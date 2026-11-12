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
import re
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
    ("Diagrama de atividades", "04_atividades.png", None),
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
# impressos; o logico vem direto do PlantUML): so apara as bordas e nao confere a proporcao antiga no docx.
SEM_TITULO = {"01_arquitetura.png", "05_conceitual.png", "06_logico.png"}
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
