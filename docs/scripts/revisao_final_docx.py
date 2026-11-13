"""Revisao final do relatorio frente ao Manual do PIM II.

1. Requisitos completos (secao 4.1): os RF02, RF03, RF04 e RF08, que faltavam na
   numeracao, passam a ser definidos a partir do que ja estava modelado (UC09 Gerar
   QR code, UC02 Trocar idioma, UC08 Manter filiais, que inclui o cadastro das
   maquininhas, e UC03 Filtrar por categoria). O Quadro 2 ganha o item do QR code (RF02).
2. Descricao textual do caso de uso principal (UC05 Alterar disponibilidade), que o
   Manual pede alem do diagrama (Etapa 3).
3. Resumo e Abstract: pontuacao da lista de disciplinas e frase com os resultados
   dos testes, lidos de docs/evidencias/{c,sql}/resumo.json (rode os testes antes).
4. Secao 6.2 com todas as funcoes do Apendice A; secao 5.5 explicita que o
   historico nao usa exclusao em cascata.
5. Limite de 30 paginas do desenvolvimento: o capitulo 3 e enxugado (metodologia,
   Quadro 1, analise apos o quadro e diferenciais mais concisos) para que nao ocupe
   uma pagina so com a sobra da secao 3.7; Quadros 2 e 3 em corpo 10, como os demais.
   Margem pequena: ao acrescentar texto no capitulo 3, confira a paginacao.

Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-revisao-final.docx
na primeira execucao. Depois de rodar, atualize os campos no Word (Ctrl+A, F9) e
reexporte o PDF.
Uso:  python docs/scripts/revisao_final_docx.py
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import (ABSTRACT, INDICADORES, RESUMO, clonar,  # noqa: E402
                             definir_texto, resultados_testes, substituir_regex)

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-revisao-final.docx"
EVIDENCIAS = DOCS / "evidencias"

# ------------------------------------------------------------ textos novos
RF_NOVO = (
    "Os requisitos funcionais são: RF01 — autenticar usuários internos, negando o acesso "
    "após três tentativas inválidas; RF02 — gerar o QR code de acesso ao cardápio de cada "
    "filial (administrador); RF03 — alternar o idioma do cardápio entre português e inglês; "
    "RF04 — cadastrar as maquininhas de cada filial e emitir ou revogar seus tokens de "
    "acesso (administrador, no UC08 Manter filiais); RF05 — cadastrar e manter produtos, categorias, filiais e usuários "
    "(administrador); RF06 — ativar e desativar produtos por filial (gerente); RF07 — exibir "
    "o cardápio ativo da filial ao cliente; RF08 — filtrar o cardápio por categoria; RF09 — "
    "filtrar o cardápio por alérgeno; RF10 — expor o catálogo disponível às maquininhas dos "
    "garçons por meio de uma API (Application Programming Interface); RF11 — registrar em "
    "histórico toda alteração de disponibilidade; RF12 — gerar relatórios de "
    "indisponibilidade atual e de frequência de esgotamento; e RF13 — apresentar o cardápio "
    "com informação estruturada de alérgenos e em dois idiomas."
)

UC_INICIO_ANTIGO = "O diagrama de casos de uso representa as interações entre os atores e o sistema."
UC05 = (
    "O caso de uso central, UC05 Alterar disponibilidade de produto, é descrito a seguir. "
    "Ator: gerente de filial. Pré-condição: o gerente está autenticado (UC04). Fluxo "
    "principal: o gerente informa o produto e o novo estado, ativo ou inativo; o sistema "
    "confirma que o produto existe, grava o estado somente na filial vinculada ao login, "
    "registra o evento no histórico e exibe a confirmação (RF06 e RF11). Fluxos "
    "alternativos: produto inexistente, informado com mensagem de erro; e produto já no "
    "estado pedido, situação em que nada é gravado. Pós-condição: o cardápio da filial e as "
    "maquininhas refletem o novo estado em até 30 segundos (RNF01)."
)

ITEM_QR = ["B08", "Como administrador, gerar o QR code de cada filial (RF02).", "Média"]
# B07: a troca de idioma e o RF03 (funcional) e o RNF03 (idioma marcado na pagina)
B07_NOVO = "Como cliente, alternar o idioma entre português e inglês (RF03/RNF03)."

METODOLOGIA_ANTIGA = "O trabalho foi desenvolvido nas seguintes etapas:"
METODOLOGIA_NOVA = (
    "As etapas do trabalho acompanham os capítulos deste relatório, da caracterização da "
    "organização à análise de acessibilidade e de proteção de dados. Por se tratar de uma "
    "organização fictícia, não houve coleta de dados com usuários reais, o que constitui "
    "uma limitação discutida no capítulo 9."
)

ANALISE_ANTIGA = "Iskender, Sirakaya-Turk e Cardenas (2023) mostram que as críticas"
ANALISE_NOVA = (
    "Iskender, Sirakaya-Turk e Cardenas (2023) e Radke et al. (2016) apontam a informação, "
    "sobretudo sobre alérgenos, como ponto fraco; os demais explicam a aceitação."
)

# Quadro 1, linha de Iskender, Sirakaya-Turk e Cardenas (2023): celulas mais curtas
QUADRO1_LINHA1 = {
    1: "Percepção de clientes sobre cardápios QR (qualitativo)",
    2: "Valorizam rapidez, mas criticam cardápios pouco informativos",
    3: "Ignora acessibilidade e disponibilidade em tempo real",
}

QR_ANTIGO_FIM = "dois requisitos incorporados à solução proposta."
QR_INCORPORADO = "Logo, o cardápio deve ser simples e seguro quanto aos dados do cliente."

DIFERENCIAIS_INTRO_ANTIGA = "Em relação às soluções encontradas na literatura e no mercado"
DIFERENCIAIS_INTRO = "Em relação ao mercado, a proposta apresenta os seguintes diferenciais:"
# um item por linha: o texto curto evita a quebra dentro do item
DIFERENCIAIS = [
    "a) disponibilidade por filial atualizada em até 30 segundos (meta);",
    "b) cardápio em HTML (HyperText Markup Language), e não em PDF;",
    "c) conformidade com a WCAG 2.2 AA e a ABNT NBR 17225;",
    "d) alérgenos estruturados, com filtro e aviso de referência;",
    "e) versões em português e inglês, com idioma marcado na página;",
    "f) sem cadastro do cliente e sem cookies de rastreamento;",
    "g) complemento ao atendimento, sem substituir o garçom.",
]

# RESUMO e ABSTRACT (trechos que localizam esses paragrafos) vem de evidencias_docx.py

# (paragrafo, trecho antigo, trecho novo). O paragrafo e identificado por um trecho
# do seu texto; o trecho antigo e None (troca o paragrafo inteiro) ou o texto a
# substituir. Ambos aceitam uma tupla de alternativas (versoes anteriores do texto).
TROCAS = [
    # Resumo e Abstract: lista de disciplinas (a ultima e "direitos humanos,
    # inclusao e seguranca", nome do capitulo 8)
    (RESUMO,
     ("pesquisa, tecnologia e inovação; engenharia de software, modelagem de banco de dados, "
      "programação estruturada, redes de computadores e sistemas distribuídos, e direitos "
      "humanos, inclusão e segurança.",
      "pesquisa, tecnologia e inovação; engenharia de software ágil; modelagem de banco de "
      "dados; programação estruturada em C; redes de computadores e sistemas distribuídos; e "
      "direitos humanos."),
     "pesquisa, tecnologia e inovação; engenharia de software ágil; modelagem de banco de "
     "dados; programação estruturada em C; redes de computadores e sistemas distribuídos; e "
     "direitos humanos, inclusão e segurança."),
    (ABSTRACT,
     ("research, technology and innovation; software engineering, database modeling, "
      "structured programming, computer networks and distributed systems, and human rights, "
      "inclusion and security.",
      "research, technology and innovation; agile software engineering; database modeling; "
      "structured programming in C; computer networks and distributed systems; and human "
      "rights."),
     "research, technology and innovation; agile software engineering; database modeling; "
     "structured programming in C; computer networks and distributed systems; and human "
     "rights, inclusion and security."),
    # 4.1
    (("Os principais requisitos funcionais são:", "Os requisitos funcionais são:"), None, RF_NOVO),
    # 3.4.1: frase do paragrafo seguinte incorporada
    ("A literatura internacional sobre cardápios por QR code",
     "influenciam positivamente a intenção de usar esses cardápios após a pandemia.",
     "influenciam positivamente a intenção de usar esses cardápios após a pandemia. Logo, o "
     "cardápio deve ser simples e seguro quanto aos dados do cliente."),
    (METODOLOGIA_ANTIGA, None, METODOLOGIA_NOVA),
    (ANALISE_ANTIGA, None, ANALISE_NOVA),
    # 3.6, 3.4.3 e 3.1: frases mais curtas (limite de paginas do desenvolvimento)
    ("Essa lacuna justifica a proposta",
     "que também responde a exigências legais concretas: a acessibilidade de sítios "
     "empresariais (Brasil, 2015) e o direito do consumidor à informação acessível "
     "(Brasil, 1990).",
     "que também atende à Lei Brasileira de Inclusão (Brasil, 2015) e ao Código de Defesa "
     "do Consumidor (Brasil, 1990)."),
    ("Um cardápio acessível apenas pelo celular",
     "Por essa razão, a solução mantém o cardápio impresso e o atendimento pelo garçom, "
     "tratando o recurso digital como complemento.",
     "Por isso, a solução mantém o cardápio impresso e o garçom."),
    ("O uso de cardápios acessados por QR code se difundiu",
     "Pesquisa da Associação Brasileira de Bares e Restaurantes (2023), realizada no segundo "
     "semestre de 2022, indicou",
     "Pesquisa da Associação Brasileira de Bares e Restaurantes (2023) indicou"),
    ("O uso de cardápios acessados por QR code se difundiu",
     "depende do valor que ela agrega ao cliente e à operação.",
     "depende do valor que agrega ao negócio."),
    # 4.3.1: a lista de atores fica mais curta; o UC05 vem em paragrafo proprio
    (UC_INICIO_ANTIGO,
     ("Os atores são o Cliente, que visualiza o cardápio, troca o idioma e filtra por "
      "categoria ou alérgeno; o Gerente de filial, que faz login e altera a disponibilidade "
      "dos produtos da sua unidade; o Administrador da matriz, que mantém produtos, "
      "categorias, filiais e usuários, gera o QR code e consulta os relatórios; e a "
      "Maquininha, sistema externo que consulta o catálogo disponível por API.",
      "Os atores são o Cliente (UC01 a UC03), o Gerente de filial (UC05), o Administrador da "
      "matriz (UC06 a UC11) e a Maquininha, sistema externo que consulta o catálogo por API "
      "(UC12)."),
     "Os atores são o Cliente (UC01 a UC03), o Gerente de filial (UC05), o Administrador da "
     "matriz (UC06 a UC11; o cadastro das maquininhas e de seus tokens, RF04, integra o UC08 "
     "Manter filiais) e a Maquininha, sistema externo que consulta o catálogo por API "
     "(UC12)."),
    # 4.3.1: o login (UC04) e incluido pelos outros casos, nao ligado a um ator
    (UC_INICIO_ANTIGO, "incluem o caso Fazer login", "incluem o caso UC04 Fazer login"),
    # 6.2: funcoes que faltavam
    ("O código foi decomposto em funções de responsabilidade única",
     "manipulação de produtos e da disponibilidade (buscarProdutoPorId, adicionarProduto, "
     "cadastrarProduto, alterarDisponibilidade)",
     "manipulação de produtos e da disponibilidade (buscarProdutoPorId, adicionarProduto, "
     "carregarExemplo, cadastrarProduto, alterarDisponibilidade)"),
    ("O código foi decomposto em funções de responsabilidade única",
     "exibição e relatórios (exibirCardapio, listarTodos, relatorioIndisponibilidade, "
     "relatorioFrequencia)",
     "exibição e relatórios (contemAlergeno, exibirCardapio, listarTodos, "
     "relatorioIndisponibilidade, buscarFilialPorNome, relatorioFrequencia)"),
    # 5.5: cascata x historico
    ("A alteração de disponibilidade e o seu registro no histórico constituem",
     "As chaves estrangeiras usam exclusão em cascata quando apropriado, preservando o "
     "histórico.",
     "A exclusão em cascata vale apenas para as tabelas dependentes, como disponibilidade e "
     "produto_alergeno; a tabela de histórico não a utiliza, e por isso um produto com "
     "histórico não pode ser excluído."),
]


# ------------------------------------------------------------ utilitarios
def alternativas(x) -> tuple:
    return x if isinstance(x, tuple) else (x,)


def normal(texto: str) -> str:
    """Texto com espacos colapsados (o Word deixa espacos e quebras extras)."""
    return " ".join(texto.split())


def paragrafo(doc, trecho):
    """O unico paragrafo que contem o trecho (ou uma das alternativas da tupla)."""
    achados = [p for p in doc.paragraphs if any(t in p.text for t in alternativas(trecho))]
    if len(achados) != 1:
        raise SystemExit(f"trecho {alternativas(trecho)[0][:50]!r} casou {len(achados)} vezes")
    return achados[0]


def texto(p, novo: str) -> None:
    """definir_texto de evidencias_docx, preservando os indicadores do paragrafo."""
    definir_texto(p._p, novo, manter_indicadores=True)


def inserir_depois(p, novo: str):
    """Paragrafo novo apos p, com a mesma formatacao e sem os indicadores de p
    (copia-los duplicaria nomes e ids de referencia cruzada)."""
    el = clonar(p._p)
    for ind in [e for e in el.iter() if e.tag in INDICADORES]:
        ind.getparent().remove(ind)
    p._p.addnext(el)
    q = Paragraph(el, p._parent)
    texto(q, novo)
    return q


def aplicar_trocas(doc, trocas=None) -> int:
    feitas = 0
    for trecho, antigo, novo in (TROCAS if trocas is None else trocas):
        if antigo is None:
            # o trecho pode ter sumido com a troca: confere o paragrafo inteiro
            if any(p.text == novo for p in doc.paragraphs):
                continue
            texto(paragrafo(doc, trecho), novo)
        else:
            p = paragrafo(doc, trecho)
            if novo in p.text:
                continue
            # funcao em vez de string: o texto entra literal, sem escapar barras
            if not any(substituir_regex(p._p, re.escape(a), lambda m, t=novo: t, limite=1)
                       for a in alternativas(antigo)):
                raise SystemExit(f"trecho antigo nao encontrado em {alternativas(trecho)[0][:50]!r}")
        feitas += 1
    return feitas


def remover_paragrafo_qr(doc) -> int:
    """Remove o paragrafo curto da 3.4.1, so depois que a frase dele foi incorporada."""
    alvo = [p for p in doc.paragraphs if p.text.strip().endswith(QR_ANTIGO_FIM)]
    if not alvo:
        return 0
    if len(alvo) > 1:
        raise SystemExit(f"{len(alvo)} paragrafos terminam em {QR_ANTIGO_FIM!r}; remova a mao")
    if QR_INCORPORADO not in paragrafo(doc, "A literatura internacional sobre cardápios por QR code").text:
        raise SystemExit("frase da 3.4.1 nao incorporada; paragrafo curto mantido")
    alvo[0]._p.getparent().remove(alvo[0]._p)
    return 1


def inserir_uc05(doc) -> int:
    if any(p.text.startswith(UC05[:40]) for p in doc.paragraphs):
        return 0
    inserir_depois(paragrafo(doc, UC_INICIO_ANTIGO), UC05)
    return 1


def diferenciais(doc) -> int:
    """Reescreve a introducao e os itens da secao 3.7 (6 itens viram 7 mais curtos)."""
    P = doc.paragraphs
    k = next((n for n, p in enumerate(P) if p.text.startswith(
        (DIFERENCIAIS_INTRO_ANTIGA, "Em relação às soluções da literatura", DIFERENCIAIS_INTRO[:30]))), None)
    if k is None:
        raise SystemExit("introducao da 3.7 nao encontrada")
    itens = []
    for p in P[k + 1:]:
        if not re.match(r"[a-g]\) ", p.text):
            break
        itens.append(p)
    if [p.text for p in itens] == DIFERENCIAIS and P[k].text == DIFERENCIAIS_INTRO:
        return 0
    if len(itens) not in (6, 7):
        raise SystemExit(f"esperava 6 ou 7 itens na 3.7, achei {len(itens)}")
    texto(P[k], DIFERENCIAIS_INTRO)
    for p, novo in zip(itens, DIFERENCIAIS):
        texto(p, novo)
    if len(itens) == 6:
        inserir_depois(itens[-1], DIFERENCIAIS[-1])
    return 1


def backlog(doc) -> int:
    tab = next(t for t in doc.tables if t.rows[0].cells[0].text.strip() == "ID"
               and "história do usuário" in t.rows[0].cells[1].text)
    feitas = 0
    b07 = next(r for r in tab.rows if r.cells[0].text.strip() == "B07")
    if normal(b07.cells[1].text) != B07_NOVO:
        texto(b07.cells[1].paragraphs[0], B07_NOVO)
        feitas += 1
    # o item do QR ja existe (mesmo que editado no Word): nada a inserir
    if any("QR code" in r.cells[1].text for r in tab.rows):
        return feitas
    b08 = next(r for r in tab.rows if r.cells[0].text.strip() == "B08")
    texto(b08.cells[0].paragraphs[0], "B09")
    novo = clonar(b07._tr)
    b07._tr.addnext(novo)
    linha = next(r for r in tab.rows if r._tr is novo)
    for cel, valor in zip(linha.cells, ITEM_QR):
        texto(cel.paragraphs[0], valor)
    return feitas + 1


def quadro1(doc) -> int:
    tab = next(t for t in doc.tables if t.rows[0].cells[0].text.strip() == "Trabalho")
    linha = next(r for r in tab.rows if r.cells[0].text.startswith("Iskender, Sirakaya"))
    feitas = 0
    for col, novo in QUADRO1_LINHA1.items():
        p = linha.cells[col].paragraphs[0]
        if normal(p.text) != novo:
            texto(p, novo)
            feitas += 1
    return feitas


def quadros_corpo_10(doc) -> int:
    """Corpo 10 nos runs sem tamanho dos Quadros 2 (backlog) e 3 (VLANs)."""
    n = 0
    for t in doc.tables:
        if t.rows[0].cells[0].text.strip() not in ("ID", "VLAN"):
            continue
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    for run in p.runs:
                        if run.font.size is None:
                            run.font.size = Pt(10)
                            n += 1
    return n


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    doc = Document(ALVO)
    trocas = aplicar_trocas(doc)
    testes = resultados_testes(doc)
    removidos = remover_paragrafo_qr(doc)
    uc = inserir_uc05(doc)
    dif = diferenciais(doc)
    bk = backlog(doc)
    q1 = quadro1(doc)
    runs10 = quadros_corpo_10(doc)
    doc.save(ALVO)
    print(f"trechos={trocas} frases de testes={testes} paragrafos removidos={removidos} UC05={uc} "
          f"diferenciais={dif} itens de backlog={bk} celulas do Quadro 1={q1} runs em corpo 10={runs10}")


if __name__ == "__main__":
    main()
