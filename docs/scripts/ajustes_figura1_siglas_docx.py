"""Ajustes pontuais da revisao contra o Manual do PIM II (segunda rodada).

1. Nome do UC08 unificado como "Manter filiais e maquininhas" (Quadro 3 e Figura 1): o
   RF04 da secao 4.1 dizia "no UC08 Manter filiais".
2. Lista de abreviaturas e siglas: IPsec (secao 7.2) e PC (Quadro 5; a ABNT lista a sigla
   no singular, o texto usa "PCs"). Tira "AA", posta numa versao anterior: e o nome de um
   nivel de conformidade da WCAG, nao uma sigla com forma por extenso.
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
from docx.shared import Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import aplicar_trocas_ancoradas  # noqa: E402
from revisao_manual_docx import completar_siglas, entradas_siglas  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-figura1-siglas.docx"

TROCAS = [
    ("RF04 — cadastrar as maquininhas", "(administrador, no UC08 Manter filiais)",
     "(administrador, no UC08 Manter filiais e maquininhas)"),
]

SIGLAS = [
    ("IPsec", "Internet Protocol Security"),
    ("PC", "Personal Computer"),
]
SIGLAS_RETIRADAS = ["AA"]

TAM_FONTE = Pt(10)


def retirar_siglas(doc) -> int:
    """Apaga da lista de siglas as entradas de SIGLAS_RETIRADAS, se ainda existirem."""
    feitas = 0
    for p in entradas_siglas(doc):
        if p.text.split("	")[0] in SIGLAS_RETIRADAS:
            p._p.getparent().remove(p._p)
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
    siglas = completar_siglas(doc, SIGLAS)
    retiradas = retirar_siglas(doc)
    fontes = fontes_10pt(doc)
    doc.save(ALVO)
    print(f"trechos alterados={trocas} siglas novas={siglas} retiradas={retiradas} fontes em 10 pt={fontes}")


if __name__ == "__main__":
    main()
