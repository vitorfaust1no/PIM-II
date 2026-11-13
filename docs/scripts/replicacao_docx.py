"""Replicacao MySQL -> MongoDB sem ponto de controle (secao 5.4) — revisao de 13/11/2026.

O desenho anterior lia os eventos com id_historico maior que um ponto de controle. Como o
AUTO_INCREMENT reserva o id no INSERT e as transacoes podem confirmar fora da ordem, um
evento de id menor confirmado depois do avanco do ponto de controle nunca seria copiado.
Agora cada evento gera, na mesma transacao, uma linha em replicacao_pendente (trigger
trg_historico_pendente, implementado no modelo fisico e testado no ST13), e o servico de
replicacao (previsto para producao, NAO implementado) apaga a pendencia so depois que o
MongoDB confirma a gravacao.

1. 5.2 e 5.3: a caixa de saida passa a ser a tabela replicacao_pendente.
2. 5.4: os tres paragrafos do mecanismo e das falhas sao reescritos (fonte unica: TEXTO_54;
   sincronizacao_historico_docx.py e correcoes_avaliador_docx.py importam daqui).

Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-replicacao.docx.
Uso (da raiz, com o .docx fechado no Word):  python docs/scripts/replicacao_docx.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import aplicar_trocas, clonar, definir_texto  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-replicacao.docx"

# paragrafo que abre a 5.4 (fica igual) e o que a fecha (fica igual)
ANCORA_54 = "A simulação em C representa esse histórico de forma simplificada no arquivo historico.txt."
FECHO_54 = (
    "Desse modo, o projeto trabalha com dois níveis de consistência: a disponibilidade corrente e "
    "o seu registro de histórico são gravados de forma atômica no MySQL, e a disponibilidade é "
    "propagada aos canais em até 30 segundos (meta do RNF01), enquanto a cópia analítica no MongoDB é eventualmente consistente, podendo ficar "
    "temporariamente atrasada, mas sempre convergindo para o conteúdo do banco relacional "
    "(Coulouris et al., 2013)."
)
INICIO_FECHO_54 = FECHO_54.split(":")[0]  # "Desse modo, o projeto trabalha com ..."

TEXTO_54 = [
    "A sincronização entre os dois bancos segue o padrão de caixa de saída transacional "
    "(transactional outbox). No modelo físico, cada evento inserido em historico_disponibilidade "
    "dispara o trigger trg_historico_pendente, que grava o seu id_historico na tabela "
    "replicacao_pendente; como o trigger roda na mesma transação que altera a disponibilidade "
    "(seção 5.5), o evento e a sua pendência são confirmados ou desfeitos juntos (Elmasri; "
    "Navathe, 2018), o que o teste ST13 comprova. A API nunca escreve diretamente no MongoDB, o "
    "que evita a escrita dupla (dual write), situação em que um banco poderia ser atualizado e o "
    "outro não.",
    "A cópia para o MongoDB caberá a um serviço de replicação independente da API, previsto para "
    "produção e não implementado neste trabalho. A cada poucos segundos, ele lerá em lotes as "
    "pendências e os eventos correspondentes, inserirá cada evento no MongoDB com o próprio "
    "id_historico como identificador do documento (_id) e confirmação de escrita pela maioria "
    "das réplicas e, só então, apagará as pendências do lote. Não há ponto de controle por "
    "número: um evento de transação confirmada fora da ordem dos ids continua pendente até ser "
    "copiado, em vez de ser saltado. Como a reinserção de um mesmo evento é rejeitada pela chave "
    "_id, a entrega ocorre ao menos uma vez, mas o efeito final é o de uma única gravação por "
    "evento, isto é, a operação é idempotente (Coulouris et al., 2013).",
    "Nos cenários de falha, o MySQL é a referência para a recuperação. Se o MongoDB estiver "
    "indisponível, as pendências permanecem e o serviço tenta de novo com espera exponencial, sem "
    "perda de eventos; se o próprio serviço falhar entre gravar no MongoDB e apagar as "
    "pendências, o lote é reprocessado e os eventos repetidos são rejeitados pela chave _id; e uma "
    "transação revertida não deixa evento nem pendência. Uma conciliação diária compara as "
    "contagens de eventos por filial e por dia nos dois bancos e regrava, a partir do MySQL, os "
    "que faltarem (por exemplo, após a restauração de um backup do MongoDB), e a idade da "
    "pendência mais antiga é monitorada com alerta; esse atraso afeta apenas os relatórios "
    "analíticos, pois o cardápio e as maquininhas leem o MySQL (RNF01).",
]

TEXTO_52_ANTIGO = ("nela apenas se inserem linhas, e ela também serve de caixa de saída para a "
                   "replicação descrita na seção 5.4.")
TEXTO_52 = ("nela apenas se inserem linhas, e cada evento gera uma pendência na tabela "
            "replicacao_pendente, a caixa de saída da replicação (seção 5.4).")

TROCAS = [
    (TEXTO_52_ANTIGO, TEXTO_52),
    # 5.3: a lista de tabelas do modelo fisico inclui a caixa de saida
    ("harmonizacao, disponibilidade e historico_disponibilidade. Os textos",
     "harmonizacao, disponibilidade, historico_disponibilidade e replicacao_pendente. Os textos"),
    # a contagem de testes do Resumo/Abstract sai dos resumo.json (evidencias_docx.py)
]


def reescrever_54(doc) -> int:
    """Unica rotina que escreve a 5.4: tudo entre o paragrafo de abertura (ANCORA_54) e o
    titulo 5.5 passa a ser TEXTO_54 + [FECHO_54], em qualquer versao anterior do .docx
    (paragrafos a mais sao removidos; a menos, clonados do paragrafo de abertura). Usada
    tambem por sincronizacao_historico_docx.py e correcoes_avaliador_docx.py. Devolve
    quantos paragrafos mudaram (0 = a 5.4 ja estava atual)."""
    P = doc.paragraphs
    ini = [i for i, p in enumerate(P) if p.text.rstrip().endswith(ANCORA_54)]
    if len(ini) != 1:
        raise SystemExit(f"abertura da 5.4 casou {len(ini)} vezes")
    abertura = P[ini[0]]
    i_55 = next(i for i in range(ini[0] + 1, len(P)) if P[i].style.name == "Heading 2")
    if not P[i_55].text.startswith("5.5 "):
        raise SystemExit(f"esperava o titulo 5.5 apos a 5.4, achei {P[i_55].text[:40]!r}")
    existentes = P[ini[0] + 1:i_55]
    esperado = TEXTO_54 + [FECHO_54]
    mudancas = 0
    for p in existentes[len(esperado):]:  # sobras de uma versao antiga (ex.: alineas a-e)
        p._p.getparent().remove(p._p)
        mudancas += 1
    ultimo = abertura._p
    for k, texto in enumerate(esperado):
        if k < len(existentes):
            p_el = existentes[k]._p
            if existentes[k].text != texto:
                definir_texto(p_el, texto)
                mudancas += 1
        else:
            p_el = definir_texto(clonar(abertura._p), texto)
            ultimo.addnext(p_el)
            mudancas += 1
        ultimo = p_el
    return mudancas


def main() -> None:
    doc = Document(ALVO)
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    print(f"5.4: {reescrever_54(doc)} paragrafo(s) reescrito(s); trocas: {aplicar_trocas(doc, TROCAS)}.")
    doc.save(ALVO)
    print("Abra no Word, atualize os campos (sumario, listas e paginas) e reexporte o PDF.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
