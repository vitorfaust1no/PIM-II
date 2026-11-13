"""Ajusta o relatorio aos itens do Manual do PIM II (ADS) apontados na revisao.

1. Etapa 3 (casos de uso): secao 4.3.1 ganha o Quadro "Casos de uso do sistema" (caso de
   uso, ator e requisitos) e o paragrafo dos atores fica mais curto; 4.3.3 a 4.5 enxugadas.
2. Etapa 6 (equipamentos): secao 7.3 ganha o Quadro "Equipamentos de rede de cada filial".
3. Etapa 8 (evolucao futura): a antiga 9.3 (Da simulacao ao sistema em producao) da lugar
   a 9.4 Possibilidades de evolucao futura (Beneficios vira 9.3); a Conclusao remete a ela;
   9.1 e 9.2 enxugadas para o capitulo 9 continuar em uma pagina.
4. Limite de 30 paginas do desenvolvimento: 6.2 enxugada (o texto da 6.8 fica em
   evidencias_docx.py, que deve ser rodado depois deste script).
5. Remissoes aos apendices no formato do Manual: "(Apendice X - Titulo)".
6. Lista de abreviaturas e siglas completada (siglas usadas no texto).
7. 4.1: "secao 2" -> "capitulo 2".

Quadros novos: numerados por campo SEQ; os quadros seguintes e as citacoes em texto sao
renumerados, e a Lista de Quadros recebe as entradas (paginas: o Word atualiza ao abrir).
Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-manual.docx na primeira vez.
Depois rode:  python docs/scripts/evidencias_docx.py
Uso:  python docs/scripts/revisao_manual_docx.py
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import (  # noqa: E402
    TRAV, Ids, achar, ajustar_citacoes_quadros, aplicar_trocas_ancoradas, clonar,
    definir_texto, entrada_lista, legenda, legendas_seq, renumerar_legendas,
    renumerar_listas, tabela, texto_el)
from reparar_docx import corrigir_sumario  # noqa: E402  (liga o updateFields)

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-manual.docx"

# numeros provisorios das legendas novas: ajustar_citacoes_quadros os troca pela ordem
PROV_UC, PROV_EQ = 901, 902
TITULO_UC = "Casos de uso do sistema"
TITULO_EQ = "Equipamentos de rede de cada filial"

QUADRO_UC = (
    ["Caso de uso", "Ator", "Requisitos"],
    [["UC01 Visualizar cardápio da filial", "Cliente", "RF07, RF13"],
     ["UC02 Trocar idioma", "Cliente", "RF03"],
     ["UC03 Filtrar por categoria/alérgeno", "Cliente", "RF08, RF09"],
     ["UC04 Fazer login", "Gerente, Administrador", "RF01"],
     ["UC05 Alterar disponibilidade de produto", "Gerente de filial", "RF06, RF11"],
     ["UC06 Manter produtos", "Administrador", "RF05"],
     ["UC07 Manter categorias", "Administrador", "RF05"],
     ["UC08 Manter filiais e maquininhas", "Administrador", "RF04, RF05"],
     ["UC09 Gerar QR code", "Administrador", "RF02"],
     ["UC10 Manter usuários", "Administrador", "RF05"],
     ["UC11 Consultar relatório de indisponibilidade", "Administrador", "RF12"],
     ["UC12 Consultar catálogo disponível (API)", "Maquininha (externo)", "RF10"]],
    [4700, 2900, 1461])

QUADRO_EQ = (
    ["Equipamento", "Qtd.", "Função na rede da filial"],
    [["Firewall UTM / roteador", "1",
      "Roteamento entre VLANs, regras de segurança e túnel VPN IPsec com a matriz"],
     ["Switch gerenciável 24 portas PoE (802.1Q)", "1",
      "Centro da topologia em estrela; alimenta pontos de acesso e câmeras"],
     ["Ponto de acesso Wi-Fi 6", "2", "Cobertura do salão e da cozinha/caixa"],
     ["Nobreak", "1", "Mantém firewall, switch e pontos de acesso na falta de energia"],
     ["Link de fibra óptica e link 4G/5G", "1 + 1", "Acesso principal e contingência"],
     ["Maquininha de cartão (smart, Wi-Fi)", "6", "Pedidos e pagamento na mesa (VLAN 20)"],
     ["Câmera IP (PoE)", "4", "Segurança, com aviso visível e retenção limitada (VLAN 40)"],
     ["Computador e impressora da gerência", "1 + 1", "Rotinas administrativas (VLAN 10)"]],
    [3400, 900, 4761])

# (trecho que localiza o paragrafo, trecho antigo ou None = paragrafo inteiro, novo)
P_431 = ("O diagrama de casos de uso (Figura 1) representa as interações entre os atores e o "
         f"sistema, e o Quadro {PROV_UC} relaciona cada caso de uso ao seu ator e aos requisitos "
         "que atende. Os casos de uso de manutenção e de alteração de disponibilidade incluem o "
         "UC04 Fazer login, e a geração de QR code estende a manutenção de filiais.")
P_432 = ("O diagrama de classes (Figura 2) descreve a estrutura estática do domínio. As classes "
         "centrais são Filial, Categoria, Produto, Disponibilidade, Alérgeno, RegistroHistórico e "
         "Usuário, esta última especializada em Gerente e Administrador por herança. Um Produto "
         "pertence a uma Categoria, contém zero ou mais Alérgenos e possui um registro de "
         "Disponibilidade por Filial; cada alteração de disponibilidade gera um "
         "RegistroHistórico associado ao Usuário que a realizou. O modelo prevê ainda a "
         "harmonização entre pratos e vinhos.")
P_433 = ("O diagrama de atividades (Figura 3) detalha a alteração de disponibilidade, do aviso "
         "do chef de que um prato esgotou à confirmação ao gerente: autenticação, seleção do "
         "produto, verificação de que a alteração ocorre na filial do próprio gerente e gravação "
         "da disponibilidade e do histórico no MySQL em uma única transação, com posterior "
         "replicação para o MongoDB. Os fluxogramas da simulação em C estão na seção 6.6.")
P_62 = ("O código foi decomposto em funções de responsabilidade única, agrupadas por "
        "finalidade: entrada validada (lerTexto, lerInteiro, lerPreco); persistência e "
        "recuperação de falhas (salvarDados, gravarAlteracao, desfazerNoDisco, abrirPendencia); "
        "cadastro e disponibilidade (cadastrarProduto, alterarDisponibilidade); exibição e "
        "relatórios (exibirCardapio, relatorioFrequencia); e controle de sessão (autenticar, "
        "menuAdmin, menuGerente). Essa separação facilita a leitura, o teste e a manutenção.")
TITULO_EVO = "Possibilidades de evolução futura"
P_EVO = ("A evolução prevista leva a simulação ao sistema em produção: as regras validadas em C "
         "passam à API REST, com o MySQL e o MongoDB no lugar dos arquivos texto, o front-end "
         "acessível e bilíngue, a integração com as maquininhas e a implantação na nuvem do "
         "capítulo 7, com o equivalente seguro das simplificações descritas na seção 6.7. "
         "Prevê-se ainda automatizar os testes e medir o prazo do RNF01 com testes de integração "
         "e de carga.")
P_44 = ("A modelagem contempla a solução completa, mas a prototipação concentra-se no núcleo "
        "que resolve o problema principal: o controle de disponibilidade por filial, a sua "
        "visualização pelo cliente e o seu registro em histórico, implementados na simulação em "
        "C (capítulo 6) e sustentados pelo modelo de dados (capítulo 5). Assim, a simulação "
        "implementa RF01, RF06, RF07, RF09, RF11 e RF12 e, em parte, RF05 (só produtos) e RF13 "
        "(alérgenos, sem o segundo idioma); RF02, RF03, RF04, RF08, RF10 e os requisitos não "
        "funcionais ficam especificados e modelados para evolução futura (seção 9.4).")
P_45 = ("A arquitetura da solução segue o padrão em camadas (Sommerville, 2018), mostrado na "
        "Figura 4: a apresentação reúne o cardápio público (web responsivo, acessível por QR "
        "code) e o painel administrativo; a aplicação concentra a API REST (Representational "
        "State Transfer), com autenticação, cardápio, disponibilidade e relatórios, e o serviço "
        "que replica o histórico do MySQL para o MongoDB (seção 5.4); e os dados abrangem o "
        "MySQL, o MongoDB e as imagens.")
P_91 = ("Na solução proposta, o cliente acessará por QR code o cardápio da filial, que exibirá só "
        "os produtos ativos na unidade, com os alérgenos e no idioma escolhido. Quando um prato "
        "esgotar, o gerente o desativará no painel, e a API gravará a mudança e o histórico no "
        "MySQL e a propagará ao cardápio e às maquininhas em até 30 segundos (meta do RNF01).")
P_92 = ("Cada disciplina resolve uma camada do problema: a engenharia de software definiu "
        "requisitos e modelagem; o banco de dados, um esquema íntegro; a programação estruturada "
        "validou a lógica central em C; as redes a levam com segurança às unidades e aos "
        "clientes; e os direitos humanos orientam acessibilidade, inclusão e LGPD.")
CONCLUSAO_FIM = ("uma meta de projeto ainda não medida; as possibilidades de evolução que "
                 "tratam desses pontos estão descritas na seção 9.4.")

TROCAS = [
    ("Os requisitos foram levantados a partir",
     "dos problemas identificados na seção 2.", "dos problemas identificados no capítulo 2."),
    (("O diagrama de atividades detalha", "O diagrama de atividades (Figura 3)"), None, P_433),
    ("O modelo físico foi implementado no script", "modelo_fisico_mysql.sql (Apêndice B)",
     f"modelo_fisico_mysql.sql (Apêndice B {TRAV} Script do modelo físico em MySQL)"),
    ("A lógica central do controle de disponibilidade foi implementada",
     "o arquivo simulacao_cardapio.c, consta do Apêndice A.",
     f"o arquivo simulacao_cardapio.c, está em apêndice (Apêndice A {TRAV} Código-fonte da "
     "simulação em C)."),
    ("A lógica central do controle de disponibilidade foi implementada",
     "O pseudocódigo correspondente está no Apêndice C.",
     f"O pseudocódigo correspondente também foi elaborado (Apêndice C {TRAV} Pseudocódigo das "
     "principais funcionalidades)."),
    ("A partir dos requisitos, construiu-se o product backlog",
     ("A partir dos requisitos, construiu-se o product backlog, que reúne os itens de valor "
      "priorizados para as sprints. O Quadro 2 apresenta os principais itens."),
     "O Quadro 2 apresenta os principais itens do product backlog, priorizados a partir dos "
     "requisitos para as sprints."),
    (("O diagrama de classes descreve", "O diagrama de classes (Figura 2)"), None, P_432),
    (("O código foi decomposto em funções",), None, P_62),
    (("A modelagem contempla a solução completa",), None, P_44),
    (("A arquitetura da solução organiza-se", "A arquitetura da solução segue"), None, P_45),
    (("Na solução proposta, o cliente acessará",), None, P_91),
    (("Cada disciplina resolve uma camada",), None, P_92),
    ("Como limitações, registra-se que a organização é fictícia",
     ("uma meta de projeto ainda não medida: comprová-lo exige testes de integração e de "
      "carga com a API, o banco de dados e as maquininhas. Esses pontos constituem os "
      "trabalhos futuros: implementar a API e o front-end acessível, integrar as maquininhas, "
      "substituir os arquivos texto pelos bancos MySQL e MongoDB, adicionar testes "
      "automatizados e implantar a solução na arquitetura em nuvem descrita, avaliando o "
      "desempenho e a conformidade em um ambiente real."),
     CONCLUSAO_FIM),
]
# trocas que citam um quadro novo pelo numero provisorio: so com a insercao do quadro
TROCA_UC = (("O diagrama de casos de uso representa",), None, P_431)
TROCA_EQ = ("A rede local de cada filial adota topologia",
            "A Figura 10 apresenta a topologia da rede local da filial.",
            f"A Figura 10 apresenta a topologia da rede local da filial, e o Quadro {PROV_EQ}, "
            "os equipamentos previstos em cada unidade.")

SIGLAS = [
    ("Anvisa", "Agência Nacional de Vigilância Sanitária"),
    ("COVID-19", "Coronavirus Disease 2019"),
    ("CT", "Caso de Teste (simulação em C)"),
    ("EUA", "Estados Unidos da América"),
    ("PIM", "Projeto Integrado Multidisciplinar"),
    ("SHA", "Secure Hash Algorithm"),
    ("ST", "Teste do modelo físico (SQL)"),
    ("TCC", "Tiny C Compiler"),
    ("TIC", "Tecnologias da Informação e Comunicação"),
    ("UC", "Caso de Uso (Use Case)"),
]


def inserir_quadro(doc, ids, ancora_el, prov: int, titulo: str, dados, troca) -> bool:
    """Aplica a troca de texto que cita o quadro e insere legenda + tabela + fonte depois de
    `ancora_el` (None = paragrafo dos atores da 4.3.1, ja trocado), no modelo do Quadro
    'Plano de VLANs', e a entrada na Lista de Quadros antes da entrada desse quadro."""
    if any(titulo in p.text for p in legendas_seq(doc, "Quadro")):
        return False
    aplicar_trocas_ancoradas(doc, [troca])
    if ancora_el is None:
        ancora_el = achar(doc, "O diagrama de casos de uso (Figura 1)")._p
    cap_modelo = next(p._p for p in legendas_seq(doc, "Quadro") if "Plano de VLANs" in p.text)
    tbl_modelo, fonte_modelo = cap_modelo.getnext(), cap_modelo.getnext().getnext()
    cap, nome_toc, _ = legenda(cap_modelo, prov, titulo, ids)
    cab, linhas, larguras = dados
    novos = [cap, tabela(tbl_modelo, cab, linhas, larguras), clonar(fonte_modelo)]
    for el in reversed(novos):
        ancora_el.addnext(el)
    entrada_vlan = next(p for p in doc.paragraphs
                        if p.style.name == "table of figures" and "Plano de VLANs" in p.text)
    entrada_vlan._p.addprevious(
        entrada_lista(entrada_vlan._p, f"Quadro {prov} {TRAV} {titulo}", nome_toc))
    return True


def reorganizar_9(doc) -> bool:
    """A antiga 9.3 (Da simulacao ao sistema em producao) e a evolucao do projeto: ela sai,
    Beneficios vira 9.3 e a nova 9.4 Possibilidades de evolucao futura absorve o seu texto."""
    if any(p.text.endswith(TITULO_EVO) for p in doc.paragraphs):
        return False
    h93 = achar(doc, "9.3 Da simulação ao sistema em produção", "Heading 2")._p
    p93 = h93.getnext()
    if not texto_el(p93).startswith("Em produção, as regras da simulação"):
        raise SystemExit("texto da 9.3 inesperado")
    h_ben = achar(doc, "9.4 Benefícios esperados", "Heading 2")
    for el in (h93, p93):
        el.getparent().remove(el)
    definir_texto(h_ben._p, "9.3 Benefícios esperados e limitações", manter_indicadores=True)
    h = clonar(h_ben._p)
    for e in list(h.iter(qn("w:bookmarkStart"))) + list(h.iter(qn("w:bookmarkEnd"))):
        e.getparent().remove(e)  # indicadores do sumario ficam so no titulo original
    definir_texto(h, f"9.4 {TITULO_EVO}")
    p_ben = achar(doc, "Entre os benefícios esperados")._p
    corpo = definir_texto(clonar(p_ben), P_EVO)
    p_ben.addnext(corpo)
    p_ben.addnext(h)
    return True


def entradas_siglas(doc) -> list:
    """Paragrafos 'SIGLA<tab>extenso' logo depois do titulo da lista."""
    pars = doc.paragraphs
    i = next(k for k, p in enumerate(pars) if p.text.strip() == "LISTA DE ABREVIATURAS E SIGLAS")
    entradas = []
    for p in pars[i + 1:]:
        if "\t" not in p.text:
            break
        entradas.append(p)
    return entradas


def completar_siglas(doc) -> int:
    feitas = 0
    for sigla, extenso in SIGLAS:
        entradas = entradas_siglas(doc)
        if any(p.text.split("\t")[0] == sigla for p in entradas):
            continue
        novo = clonar(entradas[0]._p)
        ts = list(novo.iter(qn("w:t")))
        ts[0].text, ts[1].text = sigla, extenso
        for t in ts[2:]:
            t.text = ""
        depois = next((p for p in entradas if p.text.split("\t")[0].lower() > sigla.lower()),
                      None)
        if depois is None:
            entradas[-1]._p.addnext(novo)
        else:
            depois._p.addprevious(novo)
        feitas += 1
    return feitas


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    doc = Document(ALVO)
    trocas = aplicar_trocas_ancoradas(doc, TROCAS)

    ids = Ids(doc)
    q_uc = inserir_quadro(doc, ids, None, PROV_UC, TITULO_UC, QUADRO_UC, TROCA_UC)
    # 7.3: o quadro vem depois da fonte da Figura 10
    cap_f10 = next(p._p for p in legendas_seq(doc, "Figura") if "rede local de uma filial"
                   in p.text)
    fonte_f10 = cap_f10.getnext().getnext()
    if not texto_el(fonte_f10).startswith("Fonte:"):
        raise SystemExit("fonte da Figura 10 nao encontrada")
    q_eq = inserir_quadro(doc, ids, fonte_f10, PROV_EQ, TITULO_EQ, QUADRO_EQ, TROCA_EQ)

    citacoes = ajustar_citacoes_quadros(doc)
    renumerar_legendas(doc)
    renumerar_listas(doc)
    s95 = reorganizar_9(doc)
    siglas = completar_siglas(doc)
    corrigir_sumario(doc)
    doc.save(ALVO)
    print(f"trechos alterados={trocas} quadro casos de uso={q_uc} quadro equipamentos={q_eq} "
          f"citacoes renumeradas={citacoes} capitulo 9 reorganizado={s95} "
          f"siglas novas={siglas}")


if __name__ == "__main__":
    main()
