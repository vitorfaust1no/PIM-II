"""Sincroniza os Apendices A, B e C do relatorio com os arquivos-fonte.

- Apendice A: src/simulacao_cardapio.c
- Apendice B: database/modelo_fisico_mysql.sql
- Apendice C: docs/pseudocodigo_funcionalidades.txt

Cada apendice tem uma linha de codigo por paragrafo (Consolas 8 pt). O script compara
linha a linha (difflib) e so altera os trechos que mudaram, clonando um paragrafo de
codigo vizinho para manter a formatacao.

Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-apendices.docx na
primeira execucao.
Uso:  python docs/scripts/sincronizar_apendices_docx.py [--dry-run]
"""

from __future__ import annotations

import copy
import difflib
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

DOCS = Path(__file__).resolve().parent.parent
RAIZ = DOCS.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-apendices.docx"

# (titulo do apendice, titulo do seguinte, arquivo-fonte)
APENDICES = [
    ("APÊNDICE A", "APÊNDICE B", RAIZ / "src" / "simulacao_cardapio.c"),
    ("APÊNDICE B", "APÊNDICE C", RAIZ / "database" / "modelo_fisico_mysql.sql"),
    ("APÊNDICE C", "APÊNDICE D", DOCS / "pseudocodigo_funcionalidades.txt"),
]


def _clonar_depois(ref: Paragraph, depois_de, texto: str) -> Paragraph:
    """Copia o paragrafo ref (formatacao), insere apos o elemento depois_de e troca o texto."""
    novo = copy.deepcopy(ref._p)
    depois_de.addnext(novo)
    par = Paragraph(novo, ref._parent)
    for r in par.runs[1:]:
        r._r.getparent().remove(r._r)
    par.runs[0].text = texto
    return par


def _linhas_fonte(caminho: Path) -> list[str]:
    texto = caminho.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")
    # linhas vazias aparecem no .docx como um espaco (paragrafo nao colapsa)
    return [linha if linha.strip() else " " for linha in texto.split("\n")]


def _normalizar(texto: str) -> str:
    return texto if texto.strip() else " "


def sincronizar(doc, inicio: str, fim: str, fonte: Path, aplicar: bool) -> int:
    P = doc.paragraphs
    a = next(i for i, p in enumerate(P) if p.text.startswith(inicio))
    b = next(i for i, p in enumerate(P) if p.text.startswith(fim))
    pars = P[a + 1:b]
    # descarta paragrafos finais vazios/quebra de pagina antes do proximo apendice
    while pars and not pars[-1].text.strip() and not pars[-1].runs:
        pars = pars[:-1]
    atual = [_normalizar(p.text) for p in pars]
    novo = _linhas_fonte(fonte)
    ops = difflib.SequenceMatcher(a=atual, b=novo, autojunk=False).get_opcodes()
    mudancas = 0
    for tag, i1, i2, j1, j2 in reversed(ops):  # de tras para frente
        if tag == "equal":
            continue
        mudancas += 1
        if not aplicar:
            print(f"  {inicio} {tag}: {atual[i1:i2]!r} -> {novo[j1:j2]!r}")
            continue
        comum = min(i2 - i1, j2 - j1)
        for k in range(comum):  # substituicoes 1:1
            par = pars[i1 + k]
            for r in par.runs[1:]:
                r._r.getparent().remove(r._r)
            par.runs[0].text = novo[j1 + k]
        for k in range(i1 + comum, i2):  # sobras do lado antigo
            pars[k]._p.getparent().remove(pars[k]._p)
        if j2 - j1 > comum:  # linhas novas: clona o paragrafo de codigo vizinho
            ref = pars[i1 + comum - 1] if i1 + comum > 0 else pars[0]
            ancora = ref._p if i1 + comum > 0 else P[a]._p
            for k in range(j1 + comum, j2):
                ancora = _clonar_depois(ref, ancora, novo[k])._p
    return mudancas


def main() -> None:
    aplicar = "--dry-run" not in sys.argv
    doc = Document(ALVO)
    total = {}
    for inicio, fim, fonte in APENDICES:
        total[inicio] = sincronizar(doc, inicio, fim, fonte, aplicar)
    if aplicar and any(total.values()):
        BACKUP.parent.mkdir(exist_ok=True)
        if not BACKUP.exists():
            shutil.copy2(ALVO, BACKUP)
        doc.save(ALVO)
    print(" ".join(f"{k.split()[-1]}={v}" for k, v in total.items()),
          "(simulacao)" if not aplicar else "")


if __name__ == "__main__":
    main()
