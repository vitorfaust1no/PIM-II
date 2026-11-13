"""Ajustes pontuais da revisao contra o Manual do PIM II (segunda rodada).

1. Nome do UC08 unificado como "Manter filiais e maquininhas" (Quadro 3 e Figura 1): o
   RF04 da secao 4.1 dizia "no UC08 Manter filiais".
2. Lista de abreviaturas e siglas: AA (nivel da WCAG), IPsec (secao 7.2) e PC (Quadro 5).
3. Linhas "Fonte: ..." das figuras e quadros passam de 9 pt para 10 pt, o tamanho das
   demais notas (Manual: tamanho 10 para citacoes longas e notas).

A Figura 1 nova (diagramas/02_casos_de_uso.puml) entra pelo ajustar_figuras.py.
Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-figura1-siglas.docx na
primeira vez.
Uso:  python docs/scripts/ajustes_figura1_siglas_docx.py
      python docs/scripts/ajustar_figuras.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import aplicar_trocas_ancoradas, clonar  # noqa: E402
from revisao_manual_docx import entradas_siglas  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-figura1-siglas.docx"

TROCAS = [
    ("RF04 — cadastrar as maquininhas", "(administrador, no UC08 Manter filiais)",
     "(administrador, no UC08 Manter filiais e maquininhas)"),
]

SIGLAS = [
    ("AA", "Nível de conformidade intermediário da WCAG"),
    ("IPsec", "Internet Protocol Security"),
    ("PC", "Personal Computer"),
]

TAM_FONTE = Pt(10)


def completar_siglas(doc) -> int:
    """Insere cada sigla que falta em ordem alfabetica, clonando uma entrada existente
    ('SIGLA<tab>extenso', com a sigla e o extenso nos dois primeiros w:t)."""
    feitas = 0
    for sigla, extenso in SIGLAS:
        entradas = entradas_siglas(doc)
        if any(p.text.split("\t")[0] == sigla for p in entradas):
            continue
        novo = clonar(entradas[0]._p)
        ts = list(novo.iter(qn("w:t")))
        ts[0].text, ts[1].text = sigla, extenso
        for t in ts[2:]:
            t.text = ""
        depois = next((p for p in entradas if p.text.split("\t")[0].lower() > sigla.lower()),
                      None)
        if depois is None:
            entradas[-1]._p.addnext(novo)
        else:
            depois._p.addprevious(novo)
        feitas += 1
    return feitas


def fontes_10pt(doc) -> int:
    """Linhas 'Fonte:' de figuras e quadros (fora das tabelas) com runs menores que 10 pt."""
    feitas = 0
    for p in doc.paragraphs:
        if not p.text.strip().startswith("Fonte:"):
            continue
        mudou = False
        for r in p.runs:
            if r.font.size is not None and r.font.size < TAM_FONTE:
                r.font.size = TAM_FONTE
                mudou = True
        feitas += mudou
    return feitas


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    doc = Document(ALVO)
    trocas = aplicar_trocas_ancoradas(doc, TROCAS)
    siglas = completar_siglas(doc)
    fontes = fontes_10pt(doc)
    doc.save(ALVO)
    print(f"trechos alterados={trocas} siglas novas={siglas} fontes em 10 pt={fontes}")


if __name__ == "__main__":
    main()
