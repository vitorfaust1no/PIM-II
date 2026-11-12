"""Repara defeitos de formatacao/paginacao/alinhamento em PIM_II_Sabor_e_Cia.docx.

Corrige (sem alterar conteudo, margens, fonte ou espacamento):

1. Sumario com numeros errados (tudo "1"): insere <w:updateFields w:val="true"/>
   em settings.xml para o Word recalcular o TOC/PAGEREF ao abrir.
2. Capitulos nao comecam em pagina nova: adiciona <w:pageBreakBefore/> ao estilo
   de capitulo primario (Ttulo1).
3. Imagens/quadros partindo entre paginas: mantem legenda+figura+fonte juntas
   (keep_with_next) e impede linhas de tabela de quebrarem (w:cantSplit).
4. Corpo de texto desalinhado: justifica os paragrafos narrativos e aplica
   recuo de 1a linha de 1,5 cm (Manual do PIM) de forma uniforme, PRESERVANDO legendas/fontes
   (centralizadas), titulos, blocos de codigo (fonte monoespacada) e apendices.
5. Referencias (ABNT): alinhadas a esquerda e sem recuo de 1a linha.

Idempotente: pode rodar varias vezes sem duplicar nada.
Uso:  python docs/scripts/reparar_docx.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "PIM_II_Sabor_e_Cia.bak.docx"
ESTILO_CAPITULO = "Ttulo1"  # python-docx remove acentos do styleId ("Titulo 1")
RECUO_ABNT = Cm(1.5)        # recuo de 1a linha: Manual do PIM (sobrepoe o 1,25 cm da ABNT NBR 14724)
# prefixos de paragrafos que NAO sao corpo narrativo (legendas/fontes)
PREFIXOS_LEGENDA = ("figura", "fonte", "quadro", "tabela", "grafico", "gráfico")
FONTES_MONO = ("Consolas", "Courier", "Mono")  # blocos de codigo: nao justificar
# teto de tamanho das figuras (reduz para caber o desenvolvimento em <=30 paginas).
# Ajuste e reexecute se a medicao no Word ainda ficar acima de 30 (piso ~9,5 cm).
FIG_LARG_MAX_CM = 16.0
FIG_ALT_MAX_CM = 13.0


def _get_or_add(parent, tag: str):
    """Retorna o filho <w:tag> existente ou cria um novo no fim."""
    el = parent.find(qn(tag))
    if el is None:
        el = OxmlElement(tag)
        parent.append(el)
    return el


def corrigir_sumario(doc) -> bool:
    """Insere <w:updateFields w:val="true"/> em settings.xml (uma vez)."""
    settings = doc.settings.element
    existente = settings.find(qn("w:updateFields"))
    if existente is not None:
        existente.set(qn("w:val"), "true")
        return False
    uf = OxmlElement("w:updateFields")
    uf.set(qn("w:val"), "true")
    settings.insert(0, uf)  # deve vir cedo no <w:settings>
    return True


def corrigir_quebra_capitulo(doc) -> bool:
    """Garante <w:pageBreakBefore/> no pPr do estilo de capitulo."""
    try:
        estilo = doc.styles[ESTILO_CAPITULO]
    except KeyError:
        print(f"  AVISO: estilo {ESTILO_CAPITULO!r} nao encontrado; pulei a quebra.")
        return False
    pPr = estilo.element.get_or_add_pPr()
    if pPr.find(qn("w:pageBreakBefore")) is not None:
        return False
    pPr.append(OxmlElement("w:pageBreakBefore"))
    return True


def _is_figura_legenda(paragraph) -> bool:
    txt = paragraph.text.strip().lower()
    return txt.startswith(("figura", "fonte"))


def _tem_fonte_mono(paragraph) -> bool:
    """True se algum run usa fonte monoespacada (bloco de codigo)."""
    for r in paragraph.runs:
        nome = r.font.name or ""
        if any(m in nome for m in FONTES_MONO):
            return True
    return False


def _limites_corpo(doc):
    """Indices [inicio, fim) do corpo: 1a Heading 1 ate a heading REFERENCIAS."""
    inicio = fim = None
    for i, p in enumerate(doc.paragraphs):
        if p.style.name == "Heading 1":
            if inicio is None:
                inicio = i
            if p.text.strip().upper().startswith("REFER"):
                fim = i
                break
    return inicio, fim


def padronizar_corpo(doc):
    """Justifica + recuo 1,5 cm (Manual do PIM, nao o 1,25 da ABNT) no corpo narrativo.

    Preserva: titulos (Heading*), legendas/fontes (centralizadas ou com prefixo
    Figura/Fonte/Quadro/Tabela) e blocos de codigo (fonte monoespacada).
    Retorna (n_justificados, n_recuados).
    """
    inicio, fim = _limites_corpo(doc)
    if inicio is None or fim is None:
        print("  AVISO: nao localizei inicio/fim do corpo; pulei a padronizacao.")
        return 0, 0
    justificados = recuados = 0
    for p in doc.paragraphs[inicio:fim]:
        if p.style.name.startswith(("Heading", "toc")) or p.style.name == "table of figures":
            continue
        if p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            continue  # legendas, figuras e fontes ja centralizadas
        txt = p.text.strip()
        if not txt:
            continue
        if txt.lower().startswith(PREFIXOS_LEGENDA):
            continue
        if _tem_fonte_mono(p):
            continue  # bloco de codigo (SQL/C) — nao justificar nem recuar
        pf = p.paragraph_format
        if p.alignment != WD_ALIGN_PARAGRAPH.JUSTIFY:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            justificados += 1
        # tolerancia: o recuo e gravado em twips arredondados; evita re-setar a cada run
        atual = pf.first_line_indent
        if atual is None or abs(int(atual) - int(RECUO_ABNT)) > 1000:
            pf.first_line_indent = RECUO_ABNT
            recuados += 1
    return justificados, recuados


def padronizar_referencias(doc) -> int:
    """Alinha a esquerda e remove recuo de 1a linha na secao REFERENCIAS (ABNT).

    Vai da heading REFERENCIAS ate o primeiro APENDICE/ANEXO (ou fim do doc).
    """
    paras = doc.paragraphs
    inicio = None
    for i, p in enumerate(paras):
        if p.style.name == "Heading 1" and p.text.strip().upper().startswith("REFER"):
            inicio = i + 1
            break
    if inicio is None:
        return 0
    alterados = 0
    for p in paras[inicio:]:
        topo = p.text.strip().upper()
        if topo.startswith(("APÊNDICE", "APENDICE", "ANEXO")):
            break
        if not topo:
            continue
        pf = p.paragraph_format
        mudou = False
        if p.alignment != WD_ALIGN_PARAGRAPH.LEFT:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            mudou = True
        if pf.first_line_indent not in (None, Cm(0)):
            pf.first_line_indent = None
            mudou = True
        if mudou:
            alterados += 1
    return alterados


def corrigir_imagens(doc) -> int:
    """keep_with_next em paragrafos de imagem e na legenda/fonte seguinte."""
    paras = doc.paragraphs
    alterados = 0
    for i, p in enumerate(paras):
        tem_imagem = p._p.findall(".//" + qn("w:drawing"))
        if not tem_imagem:
            continue
        # a propria imagem gruda com o que vem abaixo (legenda)
        if not p.paragraph_format.keep_with_next:
            p.paragraph_format.keep_with_next = True
            alterados += 1
        # a legenda "Figura X" imediatamente ACIMA gruda na imagem
        if i - 1 >= 0 and _is_figura_legenda(paras[i - 1]):
            if not paras[i - 1].paragraph_format.keep_with_next:
                paras[i - 1].paragraph_format.keep_with_next = True
                alterados += 1
        # legenda "Figura X" logo apos tambem gruda. A "Fonte:" NAO: ela fecha o
        # bloco; se grudasse, arrastaria o titulo e o paragrafo seguintes junto com
        # a figura e abriria grandes vazios no fim das paginas.
        for j in (i + 1, i + 2):
            if (j < len(paras) and _is_figura_legenda(paras[j])
                    and not paras[j].text.strip().lower().startswith("fonte")):
                if not paras[j].paragraph_format.keep_with_next:
                    paras[j].paragraph_format.keep_with_next = True
                    alterados += 1
    return alterados


def corrigir_tabelas(doc) -> int:
    """Marca linhas com <w:cantSplit/> e repete a 1a linha como cabecalho."""
    linhas_marcadas = 0
    for tbl in doc.tables:
        for idx, row in enumerate(tbl.rows):
            trPr = row._tr.get_or_add_trPr()
            if trPr.find(qn("w:cantSplit")) is None:
                trPr.append(OxmlElement("w:cantSplit"))
                linhas_marcadas += 1
            if idx == 0 and trPr.find(qn("w:tblHeader")) is None:
                trPr.append(OxmlElement("w:tblHeader"))
    return linhas_marcadas


def reduzir_figuras(doc, larg_max_cm: float = FIG_LARG_MAX_CM,
                    alt_max_cm: float = FIG_ALT_MAX_CM) -> int:
    """Reduz figuras inline para caber em larg_max x alt_max, mantendo a proporcao.

    So reduz (fator <= 1), nunca amplia -> idempotente. Atualiza tanto o
    <wp:extent> (layout) quanto o <a:ext> (grafico) para ficarem consistentes.
    """
    larg_max = int(Cm(larg_max_cm))
    alt_max = int(Cm(alt_max_cm))
    reduzidas = 0
    for p in doc.paragraphs:
        extent = p._p.find(".//" + qn("wp:extent"))
        if extent is None:
            continue
        cx, cy = int(extent.get("cx")), int(extent.get("cy"))
        fator = min(larg_max / cx, alt_max / cy, 1.0)
        if fator >= 1.0:
            continue  # ja cabe
        novo_cx, novo_cy = int(round(cx * fator)), int(round(cy * fator))
        extent.set("cx", str(novo_cx))
        extent.set("cy", str(novo_cy))
        a_ext = p._p.find(".//" + qn("a:ext"))
        if a_ext is not None:
            a_ext.set("cx", str(novo_cx))
            a_ext.set("cy", str(novo_cy))
        reduzidas += 1
    return reduzidas


def remover_vazios_corpo(doc) -> int:
    """Remove paragrafos 100% vazios (sem texto e sem imagem) dentro do corpo."""
    inicio = fim = None
    for i, p in enumerate(doc.paragraphs):
        if p.style.name == "Heading 1":
            if inicio is None:
                inicio = i
            if p.text.strip().upper().startswith("REFER"):
                fim = i
                break
    if inicio is None or fim is None:
        return 0
    removidos = 0
    for p in list(doc.paragraphs[inicio:fim]):
        if not p.text.strip() and not p._p.findall(".//" + qn("w:drawing")):
            p._p.getparent().remove(p._p)
            removidos += 1
    return removidos


def main() -> None:
    if not ALVO.exists():
        raise SystemExit(f"Nao encontrei {ALVO}")

    if not BACKUP.exists():
        shutil.copy2(ALVO, BACKUP)
        print(f"Backup criado: {BACKUP.name}")
    else:
        print(f"Backup ja existe (mantido): {BACKUP.name}")

    doc = Document(str(ALVO))

    c1 = corrigir_sumario(doc)
    c2 = corrigir_quebra_capitulo(doc)
    c3 = corrigir_imagens(doc)
    c4 = corrigir_tabelas(doc)
    c5j, c5r = padronizar_corpo(doc)
    c6 = padronizar_referencias(doc)
    c7 = reduzir_figuras(doc)
    c8 = remover_vazios_corpo(doc)

    doc.save(str(ALVO))

    print("Correcoes aplicadas:")
    print(f"  1. updateFields no sumario .......... {'inserido' if c1 else 'ja estava'}")
    print(f"  2. pageBreakBefore em {ESTILO_CAPITULO} ....... {'inserido' if c2 else 'ja estava'}")
    print(f"  3. keep_with_next (figuras/legendas)  {c3} paragrafo(s)")
    print(f"  4. cantSplit em linhas de tabela ...  {c4} linha(s)")
    print(f"  5. corpo justificado / recuo 1,5cm    {c5j} / {c5r} paragrafo(s)")
    print(f"  6. referencias (esquerda, sem recuo)  {c6} paragrafo(s)")
    print(f"  7. figuras reduzidas (<= {FIG_LARG_MAX_CM}x{FIG_ALT_MAX_CM} cm)  {c7} figura(s)")
    print(f"  8. paragrafos vazios removidos no corpo  {c8}")
    print(f"Salvo: {ALVO.name}")


if __name__ == "__main__":
    main()
