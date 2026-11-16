"""Remove o titulo embutido nos diagramas e amplia as figuras ilegiveis no .docx.

1. Recorta a faixa de titulo do topo de cada PNG de diagramas/ (a legenda ABNT
   "Figura n - ..." ja identifica a figura) e salva em diagramas/sem_titulo/.
2. Substitui as imagens no PIM_II_Sabor_e_Cia.docx pelas versoes recortadas,
   mantendo legendas e fontes, e ajusta a largura (16 cm nas figuras largas).
Idempotente: reprocessa sempre a partir dos PNGs originais.
Uso:  python docs/scripts/ajustar_figuras.py
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import tempfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shape import InlineShape
from docx.shared import Cm
from PIL import Image, ImageChops

RAIZ = Path(__file__).resolve().parent.parent.parent
DIAG = RAIZ / "diagramas"
SAIDA = DIAG / "sem_titulo"
ALVO = RAIZ / "docs" / "PIM_II_Sabor_e_Cia.docx"

# legenda da figura no documento (inicio do titulo, sem o numero) ->
# (arquivo, largura final em cm ou None = manter). A figura e localizada pela
# legenda, e nao pela ordem, para que outras imagens (ex.: os prints do
# Apendice D) ou uma figura nova no corpo nao desloquem o pareamento.
FIGURAS = [
    ("Diagrama de casos de uso", "02_casos_de_uso.png", 16.0),
    ("Diagrama de classes", "03_classes.png", 16.0),
    # 13 cm: com o laco das 3 tentativas (RF01, com a mensagem de erro) a figura ficou mais
    # alta; mais larga, o desenvolvimento passaria de 30 paginas
    ("Diagrama de atividades", "04_atividades.png", 13.0),
    ("Arquitetura do sistema", "01_arquitetura.png", 16.0),
    ("Modelo conceitual", "05_conceitual.png", 16.0),
    ("Modelo lógico", "06_logico.png", None),
    ("Fluxograma – exibição do cardápio", "08_fluxo_cardapio.png", None),
    ("Fluxograma – alteração de disponibilidade", "07_fluxo_alterar.png", None),
    ("Topologia geral", "09_rede_geral.png", 16.0),
    ("Topologia da rede local", "10_rede_filial.png", 16.0),
]
# Diagramas renderizados sem titulo embutido e redesenhados com outra proporcao
# (arquitetura na vertical, modelo conceitual compacto, para ficarem legiveis
# impressos; o logico e o de casos de uso vem direto do PlantUML): so apara as bordas e
# nao confere a proporcao antiga no docx.
SEM_TITULO = {"01_arquitetura.png", "02_casos_de_uso.png", "04_atividades.png", "05_conceitual.png",
              "06_logico.png"}
# Como esses PNGs nao passam pelo recorte nem pela conferencia de proporcao, a fonte
# (.puml/.dot de mesmo nome) e conferida: um titulo embutido repetiria a legenda ABNT.
# A checagem pergunta as proprias ferramentas, na mesma imagem Docker que renderiza os
# diagramas (README): o pre-processador do PlantUML expande includes, variaveis e tira
# comentarios; o Graphviz le o .dot e diz se o grafo tem label proprio.
IMAGEM_PLANTUML = "plantuml/plantuml"
TITULO_PUML = re.compile(r"^[ \t]*title\b", re.I | re.M)
LIMIAR = 200     # pixel com algum canal abaixo disso conta como "tinta"
GAP_MIN = 8       # linhas em branco que separam o titulo do diagrama


def linhas_com_tinta(im: Image.Image) -> list[bool]:
    cinza = im.convert("L").point(lambda v: 255 if v < LIMIAR else 0)
    w, h = cinza.size
    dados = cinza.tobytes()
    return [any(dados[y * w:(y + 1) * w]) for y in range(h)]


def aparar(im: Image.Image) -> Image.Image:
    fundo = Image.new(im.mode, im.size, (255, 255, 255))
    caixa = ImageChops.difference(im, fundo).getbbox()
    if caixa is None:
        return im
    m = 6  # pequena margem branca
    return im.crop((max(caixa[0] - m, 0), max(caixa[1] - m, 0),
                    min(caixa[2] + m, im.width), min(caixa[3] + m, im.height)))


def recortar_titulo(caminho: Path) -> Image.Image:
    im = Image.open(caminho).convert("RGB")
    tinta = linhas_com_tinta(im)
    y = 0
    while y < len(tinta) and not tinta[y]:
        y += 1                       # margem superior
    inicio_titulo = y
    while y < len(tinta) and tinta[y]:
        y += 1                       # faixa do titulo
    fim_titulo = y
    branco = 0
    while y < len(tinta) and not tinta[y]:
        y += 1
        branco += 1
    altura_titulo = fim_titulo - inicio_titulo
    if branco < GAP_MIN or altura_titulo > 0.08 * im.height:
        raise SystemExit(f"{caminho.name}: titulo nao isolado (faixa {altura_titulo}px, vao {branco}px)")
    return aparar(im.crop((0, y, im.width, im.height)))


class DockerIndisponivel(Exception):
    pass


def _docker(args: list[str], fonte: Path, saida: Path | None = None,
            entrada: bool = True) -> subprocess.CompletedProcess:
    """Roda a imagem do PlantUML com a pasta de `fonte` em /data (e `saida` em /out). Com
    entrada=True, a fonte vai pela entrada padrao."""
    cmd = ["docker", "run", "--rm", "-i", "-v", f"{fonte.parent}:/data", "-w", "/data"]
    if saida is not None:
        cmd += ["-v", f"{saida}:/out"]
    try:
        r = subprocess.run(cmd + args, input=fonte.read_bytes() if entrada else None,
                           capture_output=True, timeout=180)
    except FileNotFoundError as e:
        raise DockerIndisponivel("docker nao encontrado no PATH") from e
    erro = r.stderr.decode("utf-8", "replace")
    if r.returncode == 125 or "docker daemon" in erro.lower() or "cannot connect" in erro.lower():
        raise DockerIndisponivel(erro.strip().splitlines()[-1] if erro.strip() else "docker falhou")
    return r


def titulo_no_puml(fonte: Path) -> bool | None:
    """`title` na fonte ja pre-processada (includes expandidos, %dirpath() resolvido, sem
    comentarios). None se o PlantUML nao conseguiu pre-processar (ex.: include inexistente).
    A fonte vai pelo nome, nao pela entrada padrao, para o PlantUML saber onde ela esta."""
    with tempfile.TemporaryDirectory() as tmp:
        r = _docker([IMAGEM_PLANTUML, "-preproc", "-o", "/out", fonte.name], fonte,
                    saida=Path(tmp), entrada=False)
        pre = Path(tmp) / fonte.with_suffix(".preproc").name
        texto = pre.read_text(encoding="utf-8", errors="replace") if pre.exists() else ""
    if r.returncode != 0:
        print(f"AVISO {fonte.name}: o PlantUML nao pre-processou a fonte "
              f"({' '.join(texto.split()[-4:]) or 'sem saida'}); titulo nao conferido")
        return None
    return bool(TITULO_PUML.search(texto))


def titulo_no_dot(fonte: Path) -> bool | None:
    """`label` do proprio grafo, segundo o Graphviz (chave na raiz do JSON; labels de
    subgrafos e nos ficam em "objects"). None se o dot nao leu a fonte."""
    r = _docker(["--entrypoint", "dot", IMAGEM_PLANTUML, "-Tjson0"], fonte)
    try:
        grafo = json.loads(r.stdout.decode("utf-8"))
    except ValueError:
        erro = r.stderr.decode("utf-8", "replace").strip().splitlines()
        print(f"AVISO {fonte.name}: o Graphviz nao leu a fonte ({erro[-1] if erro else 'sem saida'}); "
              "titulo nao conferido")
        return None
    return bool(str(grafo.get("label", "")).strip())


def conferir_fonte_sem_titulo(arquivo: str) -> None:
    for ext, tem_titulo in ((".puml", titulo_no_puml), (".dot", titulo_no_dot)):
        fonte = DIAG / Path(arquivo).with_suffix(ext).name
        if not fonte.exists():
            continue
        try:
            achou = tem_titulo(fonte)
        except DockerIndisponivel as e:
            print(f"AVISO {fonte.name}: checagem de titulo pulada, Docker indisponivel ({e})")
            continue
        if achou:
            raise SystemExit(f"{fonte.name}: tem titulo embutido; a legenda ABNT ja identifica "
                             "a figura (tire o titulo e renderize de novo)")


def localizar_figura(doc, titulo: str) -> InlineShape:
    """Devolve a imagem do paragrafo seguinte a legenda 'Figura n – <titulo>...'."""
    achadas = []
    for p in doc.paragraphs:
        if p.style.name == "table of figures":
            continue
        m = re.match(r"Figura \d+ – (.*)", p.text)
        if m and m.group(1).startswith(titulo):
            inline = p._p.getnext().find(".//" + qn("wp:inline"))
            if inline is None:
                raise SystemExit(f"legenda '{p.text}' sem imagem logo abaixo")
            achadas.append(InlineShape(inline))
    if len(achadas) != 1:
        raise SystemExit(f"esperava 1 figura com legenda '{titulo}', achei {len(achadas)}")
    return achadas[0]


def main() -> None:
    SAIDA.mkdir(exist_ok=True)
    doc = Document(ALVO)
    pares = [(localizar_figura(doc, titulo), arquivo, largura)
             for titulo, arquivo, largura in FIGURAS]
    for n, (forma, arquivo, largura) in enumerate(pares, 1):
        original = Image.open(DIAG / arquivo)
        prop_doc = forma.width / forma.height
        prop_png = original.width / original.height
        if arquivo in SEM_TITULO:
            conferir_fonte_sem_titulo(arquivo)
            nova = aparar(original.convert("RGB"))
        else:
            nova = recortar_titulo(DIAG / arquivo)
        prop_nova = nova.width / nova.height
        # confere o pareamento: a figura no docx deve ter a proporcao do PNG original
        # ou a da versao ja recortada (execucao repetida)
        if arquivo not in SEM_TITULO and min(abs(prop_doc - prop_png) / prop_png, abs(prop_doc - prop_nova) / prop_nova) > 0.05:
            raise SystemExit(f"Figura {n}: proporcao {prop_doc:.2f} nao bate com {arquivo} ({prop_png:.2f})")
        nova.save(SAIDA / arquivo, dpi=(300, 300))
        buf = io.BytesIO()
        nova.save(buf, format="PNG", dpi=(300, 300))
        rid = forma._inline.graphic.graphicData.pic.blipFill.blip.embed
        doc.part.related_parts[rid]._blob = buf.getvalue()
        w_cm = largura if largura is not None else forma.width.cm
        forma.width = Cm(w_cm)
        forma.height = Cm(w_cm / prop_nova)
        print(f"Figura {n:2d} {arquivo:24s} {original.size} -> {nova.size}  {w_cm:.1f} x {w_cm / prop_nova:.1f} cm")
    # A "Fonte:" fecha o bloco legenda+figura+fonte: ela e a linha vazia seguinte nao
    # devem "manter com o proximo", senao arrastam o titulo seguinte junto com a figura.
    soltos = 0
    paras = doc.paragraphs
    for i, p in enumerate(paras):
        if p.text.strip().startswith("Fonte:"):
            alvos = [p] + ([paras[i + 1]] if i + 1 < len(paras) and not paras[i + 1].text.strip() else [])
            for q in alvos:
                if q.paragraph_format.keep_with_next:
                    q.paragraph_format.keep_with_next = None
                    soltos += 1
    print(f"keep_with_next removido de {soltos} paragrafo(s) de fonte")
    doc.save(ALVO)


if __name__ == "__main__":
    main()
