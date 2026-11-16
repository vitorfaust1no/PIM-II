"""Remove o titulo embutido nos diagramas e amplia as figuras ilegiveis no .docx.

1. Recorta a faixa de titulo do topo de cada PNG de diagramas/ (a legenda ABNT
   "Figura n - ..." ja identifica a figura) e salva em diagramas/sem_titulo/.
2. Substitui as imagens no PIM_II_Sabor_e_Cia.docx pelas versoes recortadas,
   mantendo legendas e fontes, e ajusta a largura (16 cm nas figuras largas).
Idempotente: reprocessa sempre a partir dos PNGs originais.
Uso:  python docs/scripts/ajustar_figuras.py
      (--sem-checagem: segue se o titulo de algum diagrama nao puder ser conferido,
      ex.: sem Docker; a conferencia usa a imagem plantuml/plantuml)
"""

from __future__ import annotations

import argparse
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


# Roda dentro do conteiner, com as fontes como argumentos: cada uma deixa em /out o
# resultado (<fonte>.d/*.preproc ou <fonte>.json), a saida da ferramenta (<fonte>.log) e o
# codigo de saida (<fonte>.rc). O laco sempre termina com 0, entao um codigo diferente
# vindo do `docker run` e falha do proprio Docker, nunca da fonte.
SCRIPT_CHECAGEM = r"""for f do
  case "$f" in
    *.puml) mkdir -p "/out/$f.d"
            java -jar /opt/plantuml.jar -preproc -o "/out/$f.d" "$f" >"/out/$f.log" 2>&1 ;;
    *) dot -Tjson0 "$f" >"/out/$f.json" 2>"/out/$f.log" ;;
  esac
  echo $? >"/out/$f.rc"
done
exit 0"""
TEMPO_DOCKER = 300  # s; a primeira execucao pode baixar a imagem


def _ultima_linha(texto: str) -> str:
    linhas = texto.strip().splitlines()
    return linhas[-1].strip() if linhas else "sem saida"


def _ler(arq: Path) -> str:
    return arq.read_text(encoding="utf-8", errors="replace") if arq.exists() else ""


def titulos_nas_fontes(fontes: list[Path]) -> tuple[list[str], list[str]]:
    """Confere todas as fontes num so conteiner. Devolve (fontes com titulo, fontes nao
    conferidas com o motivo).
    .puml: `title` na fonte pre-processada pelo PlantUML (includes e variaveis expandidos,
    sem comentarios), em qualquer .preproc gerado: o nome vem do `@startuml <nome>` quando
    houver, e um arquivo com varios @startuml gera varios.
    .dot: `label` do proprio grafo segundo o Graphviz (chave na raiz do JSON; labels de
    subgrafos e nos ficam em "objects")."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp).resolve()  # caminho longo: o Docker nao monta nomes 8.3 (VITORF~1)
        cmd = ["docker", "run", "--rm", "-v", f"{DIAG}:/data", "-w", "/data",
               "-v", f"{out}:/out", "--entrypoint", "sh", IMAGEM_PLANTUML,
               "-c", SCRIPT_CHECAGEM, "sh"] + [f.name for f in fontes]
        motivo = None
        try:
            r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True,
                               timeout=TEMPO_DOCKER)
            if r.returncode != 0:
                erro = [l for l in r.stderr.decode("utf-8", "replace").splitlines()
                        if l.strip() and not l.startswith("Run 'docker")]
                motivo = f"docker run falhou: {_ultima_linha(chr(10).join(erro))}"
        except FileNotFoundError:
            motivo = "docker nao encontrado no PATH"
        except subprocess.TimeoutExpired:
            motivo = f"docker nao terminou em {TEMPO_DOCKER} s"
        if motivo:
            return [], [f"{f.name}: {motivo}" for f in fontes]

        com_titulo, nao_conferidas = [], []
        for f in fontes:
            rc = _ler(out / f"{f.name}.rc").strip()
            log = _ultima_linha(_ler(out / f"{f.name}.log"))
            if f.suffix == ".puml":
                pre = sorted((out / f"{f.name}.d").glob("*.preproc"))
                if rc != "0" or not pre:
                    fim_texto = " ".join(" ".join(_ler(q) for q in pre).split()[-4:])
                    nao_conferidas.append(f"{f.name}: o PlantUML nao pre-processou a fonte "
                                          f"({log}{'; termina em: ' + fim_texto if fim_texto else ''})")
                    continue
                tem = any(TITULO_PUML.search(_ler(q)) for q in pre)
            else:
                try:
                    grafo = json.loads(_ler(out / f"{f.name}.json"))
                except ValueError:
                    nao_conferidas.append(f"{f.name}: o Graphviz nao leu a fonte ({log})")
                    continue
                tem = bool(str(grafo.get("label", "")).strip())
            if tem:
                com_titulo.append(f.name)
    return com_titulo, nao_conferidas


def conferir_titulos(arquivos: list[str], sem_checagem: bool) -> None:
    """Para antes de mexer em qualquer arquivo se uma fonte tem titulo embutido, ou se
    alguma nao pode ser conferida (sem Docker, include inexistente...), a menos que
    --sem-checagem tenha sido pedido: ai so avisa."""
    fontes = [DIAG / Path(a).with_suffix(ext).name for a in arquivos for ext in (".puml", ".dot")]
    fontes = [f for f in fontes if f.exists()]
    if not fontes:
        return
    com_titulo, nao_conferidas = titulos_nas_fontes(fontes)
    if com_titulo:
        raise SystemExit(f"{', '.join(com_titulo)}: tem titulo embutido; a legenda ABNT ja "
                         "identifica a figura (tire o titulo e renderize de novo)")
    if nao_conferidas and not sem_checagem:
        raise SystemExit("titulo dos diagramas nao conferido:\n  " + "\n  ".join(nao_conferidas)
                         + "\nCorrija, ou rode com --sem-checagem para seguir sem a checagem.")
    for m in nao_conferidas:
        print(f"AVISO {m}; titulo nao conferido (--sem-checagem)")


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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sem-checagem", action="store_true",
                    help="segue mesmo se o titulo de algum diagrama nao puder ser conferido")
    args = ap.parse_args()
    conferir_titulos([a for _, a, _ in FIGURAS if a in SEM_TITULO], args.sem_checagem)
    SAIDA.mkdir(exist_ok=True)
    doc = Document(ALVO)
    pares = [(localizar_figura(doc, titulo), arquivo, largura)
             for titulo, arquivo, largura in FIGURAS]
    for n, (forma, arquivo, largura) in enumerate(pares, 1):
        original = Image.open(DIAG / arquivo)
        prop_doc = forma.width / forma.height
        prop_png = original.width / original.height
        if arquivo in SEM_TITULO:
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
