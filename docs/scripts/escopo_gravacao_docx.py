"""Distingue no relatorio o que foi implementado do que foi planejado e descreve a
gravacao segura da simulacao (revisao externa, 13/11/2026).

1. Implementado x planejado:
   - 4.4: rastreabilidade dos requisitos (implementados, em parte, so especificados);
   - 6.3: RF13 marcado como implementado em parte;
   - 9.1 e 9.2: a solucao completa no futuro, por ainda nao existir;
   - Resumo, Abstract, cap. 8 e Conclusao: a solucao foi "analisada" (analise
     documental), e nao "avaliada" como se tivesse sido testada.
2. Gravacao (src/simulacao_cardapio.c): 6.4 cita o desfazer da alteracao quando a
   gravacao falha (CT14 a CT16).

O desenvolvimento (caps. 2 a 9) esta no limite de 30 paginas: as trocas dos caps. 8 e 9
nao aumentam o texto, e os acrescimos ficam no fim dos caps. 4 e 6, onde ha folga.
Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-escopo.docx.
Uso (da raiz, com o .docx fechado no Word):  python docs/scripts/escopo_gravacao_docx.py
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import substituir_regex  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-escopo.docx"

TEXTO_91 = (
    "Na solução proposta, o cliente acessará por QR code o cardápio da filial, que consultará "
    "a API REST e exibirá só os produtos ativos na unidade, com os alérgenos e no idioma "
    "escolhido. Quando um prato esgotar, o gerente alterará a disponibilidade da sua filial no "
    "painel; a API gravará a mudança e o evento de histórico no MySQL e propagará o novo "
    "estado ao cardápio e às maquininhas em até 30 segundos (meta do RNF01)."
)
TEXTO_91_ANTIGO = (
    "O cliente acessa, por QR code, o cardápio público da filial, que consulta a API REST e "
    "exibe apenas os produtos ativos naquela unidade, com os alérgenos e no idioma escolhido. "
    "Quando um prato se esgota, o gerente altera a disponibilidade da sua filial no painel; a "
    "API grava a mudança e o evento de histórico no MySQL e propaga o novo estado ao cardápio "
    "e às maquininhas dos garçons em até 30 segundos (meta do RNF01)."
)

OPCIONAL = "opcional"  # troca que so se aplica se o trecho antigo existir

# (trecho atual, trecho novo[, OPCIONAL]): cada trecho atual aparece uma unica vez
TROCAS = [
    # 4.4: rastreabilidade
    ("evolução futura, conforme discutido no capítulo 9.",
     "evolução futura, conforme discutido no capítulo 9. Assim, a simulação implementa RF01, "
     "RF06, RF07, RF09, RF11 e RF12 e, em parte, RF05 (só produtos) e RF13 (alérgenos, sem o "
     "segundo idioma); RF02, RF03, RF04, RF08, RF10 e os requisitos não funcionais ficam "
     "especificados e modelados, mas não implementados."),
    # 6.3: RF13 em parte (o detalhe esta na 4.4; o cap. 6 nao tem folga)
    ("é exibida junto ao cardápio (RF13).",
     "é exibida junto ao cardápio (RF13, em parte)."),
    # 6.4: falha de gravacao (o arquivo temporario esta no Apendice A e no README)
    # migracao opcional da versao anterior ao CT16; depois, a troca sobre o texto original
    ("alteração é desfeita (CT14 e CT15).", "alteração é desfeita (CT14 a CT16).", OPCIONAL),
    ("descritos no capítulo 5.",
     "descritos no capítulo 5. Se o cardápio ou o histórico não puder ser gravado, a "
     "alteração é desfeita (CT14 a CT16)."),
    # 9.1 e 9.2: o sistema completo ainda nao existe
    (TEXTO_91_ANTIGO, TEXTO_91),
    ("as redes levam essa lógica com segurança", "as redes levarão essa lógica com segurança"),
    ("direitos humanos garante acessibilidade", "direitos humanos orienta acessibilidade"),
    # analise documental, nao teste
    ("A solução foi avaliada quanto à acessibilidade (WCAG 2.2",
     "A proposta foi analisada quanto à acessibilidade (WCAG 2.2"),
    ("The solution was assessed regarding", "The solution was analyzed regarding"),
    ("A solução foi avaliada quanto à acessibilidade, à inclusão digital, à informação",
     "A solução foi analisada quanto à acessibilidade, à inclusão digital, à informação"),
    ("e a solução foi avaliada quanto à acessibilidade, à inclusão digital, à proteção",
     "e a proposta foi analisada quanto à acessibilidade, à inclusão digital, à proteção"),
    # a contagem de testes do Resumo/Abstract sai dos resumo.json (evidencias_docx.py)
]


def aplicar_trocas(doc) -> int:
    feitas = 0
    for antigo, novo, *opcao in TROCAS:
        if any(novo in p.text for p in doc.paragraphs):
            continue  # ja aplicada
        alvos = [p for p in doc.paragraphs if antigo in p.text]
        if not alvos and opcao == [OPCIONAL]:
            continue  # migracao de uma versao que este documento nunca teve
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
    print(f"Trocas de texto: {aplicar_trocas(doc)}.")
    doc.save(ALVO)
    print("Abra no Word, atualize os campos (sumario, listas e paginas) e reexporte o PDF.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
