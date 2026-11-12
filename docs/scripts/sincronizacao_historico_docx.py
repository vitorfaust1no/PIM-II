"""Detalha, no relatorio, a sincronizacao do historico entre MySQL e MongoDB.

1. Secao 5.4: explica o mecanismo de replicacao assincrona (tabela de historico como caixa de
   saida, servico de replicacao com ponto de controle e insercao idempotente), os cenarios de
   falha e a recuperacao de eventos, e os dois niveis de consistencia.
2. Secao 7.4: remete a 5.4 ao falar de consistencia eventual.

Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-sincronizacao.docx na
primeira execucao.
Uso:  python docs/scripts/sincronizacao_historico_docx.py
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-sincronizacao.docx"

ANCORA_54 = "de forma simplificada no arquivo historico.txt."
# referencia de formatacao para as alineas (3.2.2, objetivos especificos)
REF_ALINEA = "b) modelar o banco de dados relacional"

MECANISMO_54 = [
    "A sincronização entre os dois bancos segue o padrão de caixa de saída transacional "
    "(transactional outbox). A própria tabela historico_disponibilidade faz o papel de caixa de "
    "saída: o evento é gravado na mesma transação que altera a disponibilidade (seção 5.5), "
    "garantindo que ambos sejam confirmados ou desfeitos juntos (Elmasri; Navathe, 2018). A API "
    "nunca escreve diretamente no MongoDB, o que evita a escrita dupla (dual write), situação em "
    "que um banco poderia ser atualizado e o outro não.",
    "A cópia para o MongoDB é feita por um serviço de replicação independente da API, que consulta "
    "o MySQL a cada poucos segundos e lê, em ordem crescente e em lotes, os registros cujo "
    "id_historico é maior que o último ponto de controle replicado. São considerados apenas "
    "registros com alguns segundos de idade, para não saltar eventos de transações concorrentes "
    "confirmadas fora da ordem de numeração. Cada evento é inserido no MongoDB com o próprio "
    "id_historico como identificador do documento (_id) e com confirmação de escrita pela maioria "
    "das réplicas; somente após essa confirmação o ponto de controle avança, sendo guardado em uma "
    "coleção de controle. Como a reinserção de um mesmo evento é rejeitada pela chave _id, a "
    "entrega ocorre ao menos uma vez, mas o efeito final é o de uma única gravação por evento, "
    "isto é, a operação é idempotente (Coulouris et al., 2013).",
]

INTRO_FALHAS_54 = "Os principais cenários de falha na replicação e a respectiva recuperação são:"

ALINEAS_54 = [
    "a) MongoDB indisponível: o serviço de replicação não consegue gravar, o ponto de controle não "
    "avança e novas tentativas são feitas com intervalos crescentes (espera exponencial); os "
    "eventos permanecem guardados no MySQL e são enviados quando o MongoDB volta, sem perda;",
    "b) falha do serviço de replicação após gravar no MongoDB e antes de atualizar o ponto de "
    "controle: ao reiniciar, o lote é reprocessado e os eventos já gravados são rejeitados pela "
    "chave _id, sem duplicidade;",
    "c) transação revertida no MySQL: se a transação é desfeita (rollback), o registro de "
    "histórico também não é gravado e, portanto, nunca é replicado; as lacunas que isso deixa na "
    "numeração de id_historico não afetam a leitura por ponto de controle;",
    "d) divergência ou perda de dados no MongoDB, por exemplo após a restauração de um backup: uma "
    "rotina diária de conciliação compara a quantidade de eventos por filial e por dia nos dois "
    "bancos e reenvia os que faltam; em último caso, o ponto de controle é zerado e o histórico é "
    "reconstruído integralmente a partir do MySQL, que é a fonte de verdade;",
    "e) atraso na replicação: a defasagem é monitorada pela diferença entre o maior id_historico "
    "do MySQL e o ponto de controle, com alerta quando ultrapassa alguns minutos; esse atraso "
    "afeta apenas os relatórios analíticos, e não o cardápio, pois o cardápio público e as "
    "maquininhas leem a disponibilidade corrente do MySQL, preservando o RNF01.",
]

FECHO_54 = (
    "Desse modo, o projeto trabalha com dois níveis de consistência: a disponibilidade corrente e "
    "o seu registro de histórico são gravados de forma atômica no MySQL, e a disponibilidade é "
    "propagada aos canais em até 30 segundos (RNF01), enquanto a cópia analítica no MongoDB é eventualmente consistente, podendo ficar "
    "temporariamente atrasada, mas sempre convergindo para o conteúdo do banco relacional "
    "(Coulouris et al., 2013)."
)

ANCORA_74 = "(RNF01), atendendo ao diferencial de disponibilidade em tempo quase real."
EXTRA_74 = (" Já o histórico analítico é replicado de forma assíncrona e idempotente do MySQL "
            "para o MongoDB, com recuperação automática de falhas, conforme descrito na seção 5.4.")


def _clonar_depois(ref: Paragraph, depois_de, texto: str) -> Paragraph:
    """Copia o paragrafo ref (formatacao), insere apos o elemento depois_de e troca o texto."""
    novo = copy.deepcopy(ref._p)
    depois_de.addnext(novo)
    par = Paragraph(novo, ref._parent)
    for r in par.runs[1:]:
        r._r.getparent().remove(r._r)
    par.runs[0].text = texto
    return par


def inserir_54(doc) -> bool:
    P = doc.paragraphs
    alvos = [i for i, p in enumerate(P) if p.text.endswith(ANCORA_54)]
    if len(alvos) != 1:
        raise SystemExit(f"ancora 5.4 casou {len(alvos)} vezes")
    i_corpo = alvos[0]
    i_55 = next(i for i in range(i_corpo + 1, len(P)) if P[i].style.name == "Heading 2")
    assert P[i_55].text.startswith("5.5 "), P[i_55].text
    esperado = MECANISMO_54 + [INTRO_FALHAS_54] + ALINEAS_54 + [FECHO_54]
    existentes = P[i_corpo + 1:i_55]
    if [p.text for p in existentes] == esperado:
        return False
    # remove a versao anterior do bloco (inserida por execucao antiga deste script)
    for p in existentes:
        p._p.getparent().remove(p._p)
    corpo = P[i_corpo]
    ref_alinea = next(p for p in P if p.text.startswith(REF_ALINEA))
    el = corpo._p
    for texto in MECANISMO_54:
        el = _clonar_depois(corpo, el, texto)._p
    el = _clonar_depois(corpo, el, INTRO_FALHAS_54)._p
    for texto in ALINEAS_54:
        el = _clonar_depois(ref_alinea, el, texto)._p
    _clonar_depois(corpo, el, FECHO_54)
    return True


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
