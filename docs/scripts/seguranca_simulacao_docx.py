"""Explicita, no relatorio, a diferenca de seguranca entre a simulacao em C e a producao.

1. Secao 6.1: indica que a senha da struct Usuario fica em texto puro so por didatica.
2. Nova secao 6.7 (fim do capitulo 6): simplificacoes de seguranca da simulacao e o
   equivalente previsto para producao.
3. Secao 9.3: remete a nova 6.7.
4. Apendice A: sincroniza o codigo com src/simulacao_cardapio.c (diff linha a linha).

Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-seguranca.docx na
primeira execucao.
Uso:  python docs/scripts/seguranca_simulacao_docx.py
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-seguranca.docx"
FONTE_C = DOCS.parent / "src" / "simulacao_cardapio.c"

ANTIGO_61 = "com login, senha, perfil e filial"
NOVO_61 = ("com login, senha (mantida em texto puro apenas para fins didáticos, conforme a "
           "seção 6.7), perfil e filial")

ANCORA_93 = "preservando os requisitos não funcionais de desempenho, segurança e acessibilidade."
EXTRA_93 = (" As simplificações de segurança adotadas na simulação e o seu equivalente em "
            "produção foram detalhados na seção 6.7.")

TITULO_67 ="6.7 Segurança: simulação acadêmica e implementação prevista"
PARAGRAFOS_67 = [
    "Para que a simulação pudesse ser executada sem servidor de banco de dados, algumas "
    "simplificações de segurança foram adotadas de forma deliberada e não devem ser "
    "reutilizadas nem tomadas como prática recomendada: os usuários de teste estão fixos no código-fonte, as senhas são "
    "guardadas e comparadas em texto puro (função strcmp), o limite de três tentativas vale "
    "apenas por execução do programa e os arquivos cardapio.txt e historico.txt não têm controle "
    "de acesso. O próprio programa registra essa condição no cabeçalho do código e exibe um "
    "aviso de simulação acadêmica na tela de login.",
    "Na implementação prevista para produção, cada simplificação tem um correspondente seguro. "
    "Nenhuma credencial fica no código ou no repositório: os usuários são cadastrados na tabela "
    "usuario do MySQL, e os segredos de conexão ficam em variáveis de ambiente ou em um cofre de "
    "segredos. A senha é armazenada somente como hash bcrypt com salt (coluna senha_hash, RNF04) "
    "e conferida pela função de verificação da biblioteca, em vez de uma comparação direta. As "
    "tentativas de login são limitadas por conta e por endereço IP, com bloqueio temporário e "
    "registro das falhas. O acesso ocorre apenas por HTTPS/TLS e, entre as unidades, por VPN; "
    "após o login, a sessão é mantida por um token com expiração, e a filial do gerente é "
    "verificada no servidor a cada requisição. Por fim, os arquivos texto dão lugar ao banco de "
    "dados acessado por um usuário de privilégio mínimo, com o histórico mantido em modo "
    "somente-anexação.",
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


def ajustar_61(doc) -> bool:
    alvos = [r for p in doc.paragraphs for r in p.runs if ANTIGO_61 in r.text]
    if not alvos:
        if any(NOVO_61 in p.text for p in doc.paragraphs):
            return False
        raise SystemExit("ancora da secao 6.1 nao encontrada")
    if len(alvos) != 1:
        raise SystemExit(f"ancora 6.1 casou {len(alvos)} vezes")
    alvos[0].text = alvos[0].text.replace(ANTIGO_61, NOVO_61)
    return True


def ajustar_93(doc) -> bool:
    """Remete a secao 9.3 (Da simulacao ao sistema em producao) a nova 6.7."""
    if any(EXTRA_93.strip() in p.text for p in doc.paragraphs):
        return False
    alvos = [r for p in doc.paragraphs for r in p.runs if r.text.endswith(ANCORA_93)]
    if len(alvos) != 1:
        raise SystemExit(f"ancora 9.3 casou {len(alvos)} vezes")
    alvos[0].text += EXTRA_93
    return True


def inserir_67(doc) -> bool:
    P = doc.paragraphs
    if any(p.text == TITULO_67 for p in P):
        return False
    i7 = next(i for i, p in enumerate(P) if p.style.name == "Heading 1"
              and p.text.startswith("7 "))
    ultimo = P[i7 - 1]  # "Fonte: ..." da Figura 8
    assert ultimo.text.startswith("Fonte"), ultimo.text
    ref_titulo = next(p for p in P if p.text == "6.6 Fluxogramas")
    ref_corpo = next(p for p in P if p.text.startswith("A leitura de dados é feita por funções"))
    el = _clonar_depois(ref_titulo, ultimo._p, TITULO_67)._p
    for texto in PARAGRAFOS_67:
        el = _clonar_depois(ref_corpo, el, texto)._p
    return True


def sincronizar_apendice_a(doc) -> int:
    """Delega a sincronizar_apendices_docx, que ignora os paragrafos vazios do fim do
    apendice e trata linhas em branco (a copia antiga daqui quebrava nesses casos)."""
    from sincronizar_apendices_docx import sincronizar
    return sincronizar(doc, "APÊNDICE A", "APÊNDICE B", FONTE_C, aplicar=True)


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(ALVO, BACKUP)
    doc = Document(ALVO)
    s61 = ajustar_61(doc)
    s67 = inserir_67(doc)
    s93 = ajustar_93(doc)
    apa = sincronizar_apendice_a(doc)
    doc.save(ALVO)
    print(f"secao_6.1={s61} secao_6.7={s67} secao_9.3={s93} apendice_a_blocos={apa}")


if __name__ == "__main__":
    main()
