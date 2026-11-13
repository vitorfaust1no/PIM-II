"""Detalha, no relatorio, a sincronizacao do historico entre MySQL e MongoDB.

1. Secao 5.4: explica o mecanismo de replicacao assincrona (caixa de saida
   replicacao_pendente, servico de replicacao previsto para producao e insercao idempotente),
   os cenarios de falha e os dois niveis de consistencia. O texto vem de replicacao_docx.py.
2. Secao 7.4: remete a 5.4 ao falar de consistencia eventual.

Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-sincronizacao.docx na
primeira execucao.
Uso:  python docs/scripts/sincronizacao_historico_docx.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Texto da 5.4 (abertura, mecanismo, cenarios de falha e fecho): fonte unica em
# replicacao_docx.py, que trocou o ponto de controle pela caixa de saida
# replicacao_pendente. A versao antiga deste script (com as alineas a-e) brigava com
# correcoes_avaliador_docx.py, que as condensava.
from replicacao_docx import reescrever_54  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-sincronizacao.docx"


ANCORA_74 = "(RNF01), atendendo ao diferencial de disponibilidade em tempo quase real."
EXTRA_74 = (" Já o histórico analítico é replicado de forma assíncrona e idempotente do MySQL "
            "para o MongoDB, com recuperação automática de falhas, conforme descrito na seção 5.4.")


def inserir_54(doc) -> bool:
    """A 5.4 e escrita por uma unica rotina, em replicacao_docx.py."""
    return reescrever_54(doc) > 0


def ajustar_74(doc) -> bool:
    if any(EXTRA_74.strip() in p.text for p in doc.paragraphs):
        return False
    alvos = [r for p in doc.paragraphs for r in p.runs if ANCORA_74 in r.text]
    if len(alvos) != 1:
        raise SystemExit(f"ancora 7.4 casou {len(alvos)} vezes")
    alvos[0].text = alvos[0].text.replace(ANCORA_74, ANCORA_74 + EXTRA_74)
    return True


def main() -> None:
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
    doc = Document(ALVO)
    s54 = inserir_54(doc)
    s74 = ajustar_74(doc)
    doc.save(ALVO)
    print(f"secao_5.4={s54} secao_7.4={s74}")


if __name__ == "__main__":
    main()
