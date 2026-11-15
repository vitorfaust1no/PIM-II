"""Ajustes pedidos por um parecer externo sobre o relatorio (13/11/2026).

1. Secao 7.4: o prazo de 30 segundos aparece como meta do RNF01 ainda nao medida, e nao
   como resultado alcancado (as demais secoes ja diziam isso).
2. Quadro 2 (Product backlog): colunas ID e Prioridade estreitas e a da historia do
   usuario larga, para as historias nao quebrarem em tres ou quatro linhas.
A Figura 3 (diagrama de atividades) passou de 12 para 16 cm (hoje 13 cm); essa largura fica
so em ajustar_figuras.py (FIGURAS), que troca a imagem e o tamanho.

Confira o limite de 30 paginas do desenvolvimento depois de exportar o PDF pelo Word.
Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-ajustes-parecer.docx na primeira vez.
Uso:  python docs/scripts/ajustes_parecer_docx.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import aplicar_trocas_ancoradas  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-ajustes-parecer.docx"

TROCAS = [
    ("O projeto busca disponibilidade e tolerância a falhas",
     "a mudança é gravada na nuvem e propagada ao cardápio público e às maquininhas em até "
     "30 segundos (RNF01), atendendo ao diferencial de disponibilidade em tempo quase real.",
     "a mudança é gravada na nuvem e deve chegar ao cardápio público e às maquininhas em até "
     "30 segundos, meta do RNF01 ainda não medida, conforme o diferencial de disponibilidade "
     "em tempo quase real."),
]

# Quadro 2: ID | Item (historia do usuario) | Prioridade, em twips (total 9061 = 16 cm)
LARGURAS_BACKLOG = [850, 6611, 1600]


def colunas_backlog(doc) -> int:
    tab = next(t for t in doc.tables if t.rows[0].cells[0].text.strip() == "ID"
               and "história do usuário" in t.rows[0].cells[1].text)
    grid = tab._tbl.find(qn("w:tblGrid"))
    atuais = [int(g.get(qn("w:w"))) for g in grid.findall(qn("w:gridCol"))]
    if atuais == LARGURAS_BACKLOG:
        return 0
    if len(atuais) != len(LARGURAS_BACKLOG):
        raise SystemExit(f"Quadro 2 com {len(atuais)} colunas; esperava {len(LARGURAS_BACKLOG)}")
    for g, w in zip(grid.findall(qn("w:gridCol")), LARGURAS_BACKLOG):
        g.set(qn("w:w"), str(w))
    for tr in tab._tbl.findall(qn("w:tr")):
        tcs = tr.findall(qn("w:tc"))
        if len(tcs) != len(LARGURAS_BACKLOG):
            raise SystemExit("linha do Quadro 2 com celulas mescladas; ajuste a mao")
        for tc, w in zip(tcs, LARGURAS_BACKLOG):
            tcw = tc.get_or_add_tcPr().get_or_add_tcW()
            tcw.set(qn("w:w"), str(w))
            tcw.set(qn("w:type"), "dxa")
    return 1


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    doc = Document(ALVO)
    trocas = aplicar_trocas_ancoradas(doc, TROCAS)
    quadro = colunas_backlog(doc)
    doc.save(ALVO)
    print(f"trechos alterados={trocas} colunas do Quadro 2={quadro}")


if __name__ == "__main__":
    main()
