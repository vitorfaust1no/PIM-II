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
3. Resumo e Abstract: 14 de 14 testes no modelo fisico (ST13).

Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-replicacao.docx.
Uso (da raiz, com o .docx fechado no Word):  python docs/scripts/replicacao_docx.py
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import definir_texto, substituir_regex  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-replicacao.docx"

# paragrafo que abre a 5.4 (fica igual) e o que a fecha (fica igual)
ANCORA_54 = "A simulação em C representa esse histórico de forma simplificada no arquivo historico.txt."
INICIO_FECHO_54 = "Desse modo, o projeto trabalha com dois níveis de consistência"

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
    "contagens de eventos por filial e por dia nos dois bancos, e a idade da pendência mais "
    "antiga é monitorada com alerta; esse atraso afeta apenas os relatórios analíticos, pois o "
    "cardápio e as maquininhas leem o MySQL (RNF01).",
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
    ("e 13 de 13 no modelo físico.", "e 14 de 14 no modelo físico."),
    ("and 13 out of 13 in the physical model.", "and 14 out of 14 in the physical model."),
]


def reescrever_54(doc) -> int:
    P = doc.paragraphs
    ini = [i for i, p in enumerate(P) if p.text.rstrip().endswith(ANCORA_54)]
    fim = [i for i, p in enumerate(P) if p.text.startswith(INICIO_FECHO_54)]
    if len(ini) != 1 or len(fim) != 1 or fim[0] - ini[0] - 1 != len(TEXTO_54):
        raise SystemExit("estrutura inesperada na 5.4 (esperava 3 paragrafos entre a "
                         "abertura e o fecho)")
    trocados = 0
    for p, texto in zip(P[ini[0] + 1:fim[0]], TEXTO_54):
        if p.text != texto:
            definir_texto(p._p, texto)
            trocados += 1
    return trocados


def aplicar_trocas(doc) -> int:
    feitas = 0
    for antigo, novo in TROCAS:
        if any(novo in p.text for p in doc.paragraphs):
            continue
        alvos = [p for p in doc.paragraphs if antigo in p.text]
        if len(alvos) != 1:
            raise SystemExit(f"trecho {antigo[:60]!r} casou {len(alvos)} vezes")
        substituir_regex(alvos[0]._p, re.escape(antigo), lambda m, t=novo: t)
        feitas += 1
    return feitas


def main() -> None:
    doc = Document(ALVO)
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    print(f"5.4: {reescrever_54(doc)} paragrafo(s) reescrito(s); trocas: {aplicar_trocas(doc)}.")
    doc.save(ALVO)
    print("Abra no Word, atualize os campos (sumario, listas e paginas) e reexporte o PDF.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
