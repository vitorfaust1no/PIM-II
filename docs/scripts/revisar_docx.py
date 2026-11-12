"""Aplica as correcoes da revisao de 12/11/2026 em PIM_II_Sabor_e_Cia.docx.

Correcoes de texto (consistencia, terminologia, citacoes legais), estilos de titulo
(manter com o proximo / espacamento uniforme) e sincronizacao dos apendices A e B
com src/ e database/. Idempotente: so substitui trechos ainda nao corrigidos.
Uso:  python docs/scripts/revisar_docx.py
"""

from __future__ import annotations

import copy
from pathlib import Path

from docx import Document
from docx.shared import Cm, Emu

ALVO = Path(__file__).resolve().parent.parent / "PIM_II_Sabor_e_Cia.docx"

# (trecho antigo, trecho novo) -- aplicados em cada run de cada paragrafo
SUBSTITUICOES = [
    # Resumo / Abstract / 3.4.2 / 3.7 / RNF02 / 8.1: WCAG 2.2 (alinhada a NBR 17225)
    ("(WCAG 2.1 e ABNT NBR 17225)", "(WCAG 2.2 e ABNT NBR 17225)"),
    ("(WCAG 2.1 and ABNT NBR 17225)", "(WCAG 2.2 and ABNT NBR 17225)"),
    ("A principal referência internacional é a WCAG 2.1, que organiza os requisitos em quatro princípios: "
     "o conteúdo deve ser perceptível, operável, compreensível e robusto (W3C, 2018). No Brasil, a ABNT "
     "NBR 17225, publicada em 2025 e alinhada à WCAG 2.2, cujos critérios incluem os da WCAG 2.1, estabelece",
     "A principal referência internacional é a WCAG 2.2, que organiza os requisitos em quatro princípios: "
     "o conteúdo deve ser perceptível, operável, compreensível e robusto (W3C, 2023). No Brasil, a ABNT "
     "NBR 17225, publicada em 2025 e alinhada à WCAG 2.2, estabelece"),
    ("seguindo a WCAG 2.1 nível AA", "seguindo a WCAG 2.2 nível AA"),
    ("atender à WCAG 2.1 nível AA", "atender à WCAG 2.2 nível AA"),
    ("segue as diretrizes WCAG 2.1 no nível AA", "segue as diretrizes WCAG 2.2 no nível AA"),
    ("W3C. Web Content Accessibility Guidelines (WCAG) 2.1. [S. l.]: W3C, 2018. Disponível em: "
     "https://www.w3.org/TR/WCAG21/. Acesso em: 28 out. 2026.",
     "W3C. Web Content Accessibility Guidelines (WCAG) 2.2. [S. l.]: W3C, 2023. Disponível em: "
     "https://www.w3.org/TR/WCAG22/. Acesso em: 12 nov. 2026."),
    # Introducao: "capitulo" para divisoes de nivel 1
    ("O documento está organizado da seguinte forma: a seção 2 caracteriza a organização; a seção 3 "
     "apresenta a pesquisa científica e os diferenciais inovadores; a seção 4 trata da engenharia de "
     "software; a seção 5, da modelagem de banco de dados; a seção 6, da programação estruturada; a "
     "seção 7, das redes e sistemas distribuídos; a seção 8, dos direitos humanos, inclusão e segurança; "
     "a seção 9, da integração da solução; e a seção 10 apresenta a conclusão.",
     "O documento está organizado da seguinte forma: o capítulo 2 caracteriza a organização; o capítulo "
     "3 apresenta a pesquisa científica e os diferenciais inovadores; o capítulo 4 trata da engenharia de "
     "software; o capítulo 5, da modelagem de banco de dados; o capítulo 6, da programação estruturada; "
     "o capítulo 7, das redes e sistemas distribuídos; o capítulo 8, dos direitos humanos, inclusão e "
     "segurança; o capítulo 9, da integração da solução; e o capítulo 10 apresenta a conclusão."),
    ("Esta seção apresenta o levantamento", "Este capítulo apresenta o levantamento"),
    ("Esta seção descreve a arquitetura distribuída", "Este capítulo descreve a arquitetura distribuída"),
    ("Esta seção demonstra como", "Este capítulo demonstra como"),
    ("Esta seção descreve a visão integrada", "Este capítulo descreve a visão integrada"),
    ("na simulação em C (seção 6) e sustentado pelo modelo de dados (seção 5); os demais módulos ficam "
     "especificados e modelados para evolução futura, conforme discutido na seção 9.",
     "na simulação em C (capítulo 6) e sustentado pelo modelo de dados (capítulo 5); os demais módulos "
     "ficam especificados e modelados para evolução futura, conforme discutido no capítulo 9."),
    ("na arquitetura em nuvem descrita na seção 7,", "na arquitetura em nuvem descrita no capítulo 7,"),
    # 3.4.4: artigo do CDC
    ("O Código de Defesa do Consumidor assegura o direito à informação adequada e clara sobre os "
     "produtos, incluindo sua composição e os riscos que apresentam, e determina, em seu parágrafo "
     "único, que essa informação",
     "O Código de Defesa do Consumidor assegura, em seu art. 6º, inciso III, o direito à informação "
     "adequada e clara sobre os produtos, incluindo sua composição e os riscos que apresentam, e "
     "determina, no parágrafo único do mesmo artigo, que essa informação"),
    # 4.1 RF01 coerente com a simulacao
    ("RF01 — autenticar usuários internos, com bloqueio após três tentativas;",
     "RF01 — autenticar usuários internos, negando o acesso após três tentativas inválidas;"),
    # 4.3.3: historico coerente com 5.5 e 7.1
    ("e pela atualização paralela do banco relacional (MySQL) e do histórico (MongoDB). Dois "
     "fluxogramas complementam a modelagem: o da alteração de disponibilidade e o da exibição do "
     "cardápio da filial, ambos refletidos na simulação em C descrita na seção 6.",
     "e pela gravação da nova disponibilidade e do registro de histórico no banco relacional (MySQL), "
     "em uma única transação, com posterior replicação do evento para o histórico em MongoDB. Dois "
     "fluxogramas complementam a modelagem: o da alteração de disponibilidade e o da exibição do "
     "cardápio da filial, ambos refletidos na simulação em C descrita no capítulo 6."),
    # 5.4 / 5.5: MySQL e a fonte de verdade tambem do historico
    ("enquanto o banco relacional permanece como fonte de verdade do catálogo e da disponibilidade corrente.",
     "enquanto o banco relacional permanece como fonte de verdade do catálogo, da disponibilidade "
     "corrente e do próprio histórico; o MongoDB recebe uma cópia dos eventos, de forma assíncrona, "
     "para as consultas analíticas."),
    # 5.6: trecho coerente com o Apendice B
    ("e a consulta do cardápio ativo de uma filial (RF07). O script completo consta do Apêndice B.",
     "e a consulta do cardápio ativo de uma filial (RF07). Os trechos estão simplificados; o script "
     "completo, no Apêndice B, obtém a filial a partir do gerente autenticado."),
    ("    nome_pt      VARCHAR(120) NOT NULL,", "    nome_pt      VARCHAR(100) NOT NULL,"),
    ("    nome_en      VARCHAR(120) NOT NULL,", "    nome_en      VARCHAR(100) NOT NULL,"),
    ("VALUES (2, 1, 3, 'DESATIVAR');", "VALUES (2, 1, 2, 'DESATIVAR');"),  # usuario 2 = gerente da filial 1
    # 7.1: cardapio publico e anonimo
    ("O cardápio público e o painel do gerente trocam mensagens JSON com a API REST sobre HTTPS, "
     "autenticadas por token; as maquininhas mantêm",
     "O cardápio público consulta a API REST de forma anônima, trocando mensagens JSON sobre HTTPS; o "
     "painel do gerente usa o mesmo canal, autenticado por token de sessão; e as maquininhas, "
     "identificadas pelo token do dispositivo, mantêm"),
    # 7.4: HTTPS nao e cifragem fim a fim
    ("na cifragem fim a fim (HTTPS)", "na cifragem do tráfego em trânsito (TLS/HTTPS)"),
    # 8.3: base normativa dos alergenicos
    ("assegura o direito à informação adequada e clara sobre os produtos (Brasil, 1990). Alinhado a "
     "isso e ao Consenso Brasileiro sobre Alergia Alimentar,",
     "assegura o direito à informação adequada e clara sobre os produtos (Brasil, 1990), e a Anvisa "
     "exige a declaração dos principais alimentos alergênicos na rotulagem (Agência Nacional de "
     "Vigilância Sanitária, 2022). Alinhado a isso e ao Consenso Brasileiro sobre Alergia Alimentar,"),
    # Apendice A: dados de exemplo iguais aos do Apendice B (lista da Anvisa)
    ('"Peixe,Castanhas");', '"Peixe,Castanha-de-caju");'),
    ('4500, "Sulfitos");', '4500, "");'),
    # Apendice B: ROW_COUNT() lido logo apos o UPDATE
    ("WHERE u.id_usuario = @usuario AND ROW_COUNT() > 0;", "WHERE u.id_usuario = @usuario AND @alterou > 0;"),
]

# Citacoes dos capitulos 4 a 7 (cada par deve casar exatamente uma vez, ou ja estar aplicado)
CITACOES = [
    # 4.1
    ("de modo a permitir a rastreabilidade entre a especificação, a modelagem e a implementação.",
     "de modo a permitir a rastreabilidade entre a especificação, a modelagem e a implementação. A "
     "distinção entre requisitos funcionais e não funcionais segue Sommerville (2018), para quem os "
     "requisitos não funcionais costumam ser tão críticos quanto os funcionais, por afetarem a "
     "arquitetura do sistema como um todo."),
    # 4.2
    ("O product backlog reuniu os requisitos funcionais e não funcionais em itens priorizados.",
     "O product backlog reuniu os requisitos funcionais e não funcionais em itens priorizados. Os "
     "papéis, eventos e artefatos adotados seguem o Guia do Scrum, que define o framework como uma "
     "estrutura leve para gerar valor por meio de soluções adaptativas para problemas complexos "
     "(Schwaber; Sutherland, 2020)."),
    # 4.5
    ("A arquitetura da solução organiza-se em três camadas.",
     "A arquitetura da solução organiza-se em três camadas, seguindo o padrão de arquitetura em "
     "camadas (Sommerville, 2018)."),
    # 5 (abertura), 5.2, 5.4
    ("seguiu as três etapas clássicas:",
     "seguiu as etapas clássicas do projeto de banco de dados descritas por Elmasri e Navathe (2018):"),
    ("A normalização foi verificada forma a forma.",
     "A normalização foi verificada forma a forma, segundo as definições de Elmasri e Navathe (2018)."),
    ("como o MongoDB, no qual", "como o MongoDB (Elmasri; Navathe, 2018), no qual"),
    # 6 (abertura)
    ("O pseudocódigo correspondente está no Apêndice C.",
     "O pseudocódigo correspondente está no Apêndice C. A linguagem C oferece os recursos de controle "
     "de fluxo, funções, vetores, estruturas e arquivos empregados na simulação (Kernighan; Ritchie, 1989)."),
    # 7 (abertura)
    ("que sustentam o requisito de atualização rápida da disponibilidade.",
     "que sustentam o requisito de atualização rápida da disponibilidade. Segundo Coulouris et al. "
     "(2013), um sistema distribuído é aquele cujos componentes, localizados em computadores "
     "interligados em rede, comunicam-se e coordenam suas ações apenas por troca de mensagens."),
    # 7.2, 7.3, 7.4
    # (ja com as siglas por extenso: VPN, IP, IEEE -- NBR 14724 5.2.4)
    ("por túneis VPN IPsec,",
     "por túneis de rede privada virtual (Virtual Private Network – VPN) protegidos pelo IPsec, conjunto de "
     "protocolos de segurança do Internet Protocol (IP), conforme Kurose e Ross (2021),"),
    ("do tráfego interno. A Figura 10 apresenta",
     "do tráfego interno. Definidas pelo padrão IEEE (Institute of Electrical and Electronics Engineers) "
     "802.1Q, as VLANs criam redes lógicas independentes "
     "sobre a mesma infraestrutura física (Kurose; Ross, 2021). A Figura 10 apresenta"),
    ("e do link de contingência nas unidades. A atualização",
     "e do link de contingência nas unidades, já que a replicação é o principal meio de elevar a "
     "disponibilidade e a tolerância a falhas (Coulouris et al., 2013). A atualização"),
]

# NBR 14724 5.2.4: sigla por extenso na primeira ocorrencia no texto (+ acertos de citacao)
SIGLAS = [
    ("por meio de um QR code próprio", "por meio de um QR code (Quick Response code) próprio"),
    ("versão em PDF", "versão em PDF (Portable Document Format)"),
    ("Restaurantes (2023)", "Restaurantes ([2023])"),
    ("discutir o uso de um banco NoSQL para", "discutir o uso de um banco NoSQL (Not Only SQL) para"),
    ("modelagem do sistema com a UML", "modelagem do sistema com a UML (Unified Modeling Language)"),
    ("é a WCAG 2.2,", "é a WCAG (Web Content Accessibility Guidelines) 2.2,"),
    ("em HTML estruturado, e não em PDF, seguindo",
     "em HTML (HyperText Markup Language) estruturado, e não em PDF, seguindo"),
    ("por meio de uma API;", "por meio de uma API (Application Programming Interface);"),
    ("observar a LGPD", "observar a Lei Geral de Proteção de Dados Pessoais (LGPD)"),
    ("concentra a API REST", "concentra a API REST (Representational State Transfer)"),
    ("o modelo lógico (DER).", "o modelo lógico, representado no diagrama entidade-relacionamento (DER)."),
    ("comandos SQL representativos", "comandos SQL (Structured Query Language) representativos"),
    ("interligação das unidades (WAN)", "interligação das unidades (Wide Area Network – WAN)"),
    ("filial (LAN)", "filial (Local Area Network – LAN)"),
    ("uma CDN com WAF",
     "uma rede de distribuição de conteúdo (Content Delivery Network – CDN) com firewall de aplicação "
     "web (Web Application Firewall – WAF)"),
    ("chega por HTTPS a", "chega por HTTPS (Hypertext Transfer Protocol Secure) a"),
    ("mensagens JSON sobre", "mensagens JSON (JavaScript Object Notation) sobre"),
    ("firewall UTM", "firewall UTM (Unified Threat Management)"),
    ("com PoE e", "com alimentação pela rede (Power over Ethernet – PoE) e"),
    ("roteamento entre VLANs", "roteamento entre as redes locais virtuais (Virtual LANs – VLANs)"),
    ("cifragem do tráfego em trânsito (TLS/HTTPS)",
     "cifragem do tráfego em trânsito pelo protocolo TLS (Transport Layer Security), base do HTTPS"),
    # NBR 6023: autoria uniforme (4 ou mais autores -> et al.)
    ("ISKENDER, Ali; SIRAKAYA-TURK, Ercan; CARDENAS, David; HIKMET, Neset.", "ISKENDER, Ali et al."),
]

# NBR 6023 6.2: destaque (negrito) no titulo; (prefixo da referencia, titulo)
TITULOS_REF = [
    ("AGÊNCIA NACIONAL", "Resolução da Diretoria Colegiada – RDC nº 727, de 1º de julho de 2022"),
    ("ASSOCIAÇÃO BRASILEIRA DE BARES", "Cardápio por QR Code é uma questão de mercado, não de lei, diz Abrasel"),
    ("BRASIL. Lei nº 8.078", "Lei nº 8.078, de 11 de setembro de 1990"),
    ("BRASIL. Lei nº 13.146", "Lei nº 13.146, de 6 de julho de 2015"),
    ("BRASIL. Lei nº 13.709", "Lei nº 13.709, de 14 de agosto de 2018"),
    ("COMITÊ GESTOR", "Pesquisa sobre o uso das tecnologias de informação e comunicação nos domicílios brasileiros"),
    ("COULOURIS,", "Sistemas distribuídos"),
    ("ELMASRI,", "Sistemas de banco de dados"),
    ("GIL,", "Como elaborar projetos de pesquisa"),
    ("INSTITUTO BRASILEIRO", "Censo 2022"),
    ("KERNIGHAN,", "C"),
    ("KUROSE,", "Redes de computadores e a internet"),
    ("MARCONI,", "Fundamentos de metodologia científica"),
    ("ORGANIZAÇÃO DAS NAÇÕES UNIDAS", "Declaração Universal dos Direitos Humanos"),
    ("RADKE,", "Journal of Food Protection"),
    ("SCHWABER,", "O guia do Scrum"),
    ("SOMMERVILLE,", "Engenharia de software"),
    ("W3C.", "Web Content Accessibility Guidelines (WCAG) 2.2"),
]

LISTA_SIGLAS = [
    ("ABNT", "Associação Brasileira de Normas Técnicas"),
    ("API", "Application Programming Interface"),
    ("CDN", "Content Delivery Network"),
    ("DER", "Diagrama Entidade-Relacionamento"),
    ("HTML", "HyperText Markup Language"),
    ("HTTPS", "Hypertext Transfer Protocol Secure"),
    ("IEEE", "Institute of Electrical and Electronics Engineers"),
    ("IP", "Internet Protocol"),
    ("JSON", "JavaScript Object Notation"),
    ("LAN", "Local Area Network"),
    ("LGPD", "Lei Geral de Proteção de Dados Pessoais"),
    ("NBR", "Norma Brasileira"),
    ("NoSQL", "Not Only SQL"),
    ("PDF", "Portable Document Format"),
    ("PoE", "Power over Ethernet"),
    ("QR", "Quick Response"),
    ("REST", "Representational State Transfer"),
    ("RF", "Requisito Funcional"),
    ("RNF", "Requisito Não Funcional"),
    ("SQL", "Structured Query Language"),
    ("TLS", "Transport Layer Security"),
    ("UML", "Unified Modeling Language"),
    ("UTM", "Unified Threat Management"),
    ("VLAN", "Virtual Local Area Network"),
    ("VPC", "Virtual Private Cloud"),
    ("VPN", "Virtual Private Network"),
    ("WAF", "Web Application Firewall"),
    ("WAN", "Wide Area Network"),
    ("WCAG", "Web Content Accessibility Guidelines"),
]

# (texto da referencia, prefixo do paragrafo antes do qual ela entra)
REFERENCIAS_NOVAS = [
    ("COULOURIS, George et al. Sistemas distribuídos: conceitos e projeto. 5. ed. Porto Alegre: "
     "Bookman, 2013.", "GIL,"),
    ("ELMASRI, Ramez; NAVATHE, Shamkant B. Sistemas de banco de dados. 7. ed. São Paulo: Pearson "
     "Education do Brasil, 2018.", "GIL,"),
    ("KERNIGHAN, Brian W.; RITCHIE, Dennis M. C: a linguagem de programação padrão ANSI. Rio de "
     "Janeiro: Campus, 1989.", "KOAY,"),
    ("KUROSE, James F.; ROSS, Keith W. Redes de computadores e a internet: uma abordagem top-down. "
     "8. ed. Porto Alegre: Bookman, 2021.", "MARCONI,"),
    ("SCHWABER, Ken; SUTHERLAND, Jeff. O guia do Scrum: o guia definitivo para o Scrum: as regras do "
     "jogo. [S. l.]: Scrum.org, 2020. Disponível em: "
     "https://scrumguides.org/docs/scrumguide/v2020/2020-Scrum-Guide-PortugueseBR-3.0.pdf. "
     "Acesso em: 12 nov. 2026.", "SOLÉ,"),
    ("SOMMERVILLE, Ian. Engenharia de software. 10. ed. São Paulo: Pearson Education do Brasil, 2018.",
     "W3C."),
]

CONCLUSAO_ANCORA = "à proteção de dados e aos direitos do consumidor."
CONCLUSAO_EXTRA = (
    " Quanto ao problema de pesquisa, o trabalho mostra que uma rede com várias unidades pode manter o "
    "cardápio sincronizado com a disponibilidade real centralizando o catálogo na matriz, delegando a "
    "cada gerente o estado dos pratos da sua filial e distribuindo essa informação, a partir de uma única "
    "fonte, ao cardápio acessível e bilíngue do cliente e às maquininhas dos garçons."
)

REF_ANVISA = (
    "AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA. Resolução da Diretoria Colegiada – RDC nº 727, de 1º de "
    "julho de 2022. Dispõe sobre a rotulagem dos alimentos embalados. Brasília, DF: Anvisa, 2022."
)


def substituir_texto(doc) -> int:
    n = 0
    for p in doc.paragraphs:
        for r in p.runs:
            for antigo, novo in SUBSTITUICOES:
                if antigo in r.text:
                    r.text = r.text.replace(antigo, novo)
                    n += 1
    return n


def completar_conclusao(doc) -> bool:
    for p in doc.paragraphs:
        if p.text.startswith("O trabalho atingiu o objetivo") and CONCLUSAO_EXTRA.strip() not in p.text:
            ultimo = p.runs[-1]
            assert ultimo.text.endswith(CONCLUSAO_ANCORA)
            ultimo.text += CONCLUSAO_EXTRA
            return True
    return False


def inserir_referencia(doc, texto: str, antes_de: str) -> bool:
    """Insere a referencia (copiando a formatacao do vizinho) antes do paragrafo indicado."""
    if any(p.text == texto for p in doc.paragraphs):
        return False
    vizinho = next(p for p in doc.paragraphs if p.text.startswith(antes_de))
    novo = copy.deepcopy(vizinho._p)
    vizinho._p.addprevious(novo)
    from docx.text.paragraph import Paragraph
    par = Paragraph(novo, vizinho._parent)
    for r in par.runs[1:]:
        r._r.getparent().remove(r._r)
    par.runs[0].text = texto
    par.runs[0].bold = None
    return True


def inserir_referencia_anvisa(doc) -> bool:
    if any(p.text.startswith("AGÊNCIA NACIONAL") for p in doc.paragraphs):
        return False
    return inserir_referencia(doc, REF_ANVISA, "ASSOCIAÇÃO BRASILEIRA DE BARES")


def negritar_titulos(doc) -> int:
    """Divide o run da referencia e poe em negrito apenas o titulo (NBR 6023 6.2)."""
    feitas = 0
    for prefixo, titulo in TITULOS_REF:
        p = next(p for p in doc.paragraphs if p.text.startswith(prefixo))
        if any(r.bold for r in p.runs):
            continue  # ja destacada
        if len(p.runs) != 1:
            raise SystemExit(f"referencia com varios runs: {prefixo}")
        run = p.runs[0]
        texto = run.text
        k = texto.index(". " + titulo) + 2
        antes, depois = texto[:k], texto[k + len(titulo):]
        run.text = antes
        r_tit = copy.deepcopy(run._r)
        r_dep = copy.deepcopy(run._r)
        run._r.addnext(r_tit)
        r_tit.addnext(r_dep)
        from docx.text.run import Run
        Run(r_tit, p).text = titulo
        Run(r_tit, p).bold = True
        Run(r_dep, p).text = depois
        feitas += 1
    return feitas


def ajustar_recuo_e_resumos(doc) -> None:
    """Recuo de 1,5 cm (Manual 1.5) e espaco simples no resumo e no abstract."""
    for p in doc.paragraphs:
        f = p.paragraph_format
        if f.first_line_indent is not None and abs(f.first_line_indent.cm - 1.25) < 0.01:
            f.first_line_indent = Cm(1.5)
        if p.text.startswith(("Este trabalho apresenta o projeto de um cardápio digital acessível, com controle de disponibilidade de pratos",
                              "This paper presents the design")):
            f.line_spacing = 1.0
        if p.text.startswith(("Palavras-chave:", "Keywords:")):
            f.space_before = Emu(152400)  # 12 pt separando do resumo
        if p.text == "LISTA DE ABREVIATURAS E SIGLAS":
            f.space_after = Emu(228600)   # 18 pt, como RESUMO e SUMARIO


def inserir_lista_siglas(doc) -> bool:
    """Lista de abreviaturas e siglas (pre-textual), depois da Lista de quadros."""
    if any(p.text == "LISTA DE ABREVIATURAS E SIGLAS" for p in doc.paragraphs):
        return False
    from docx.oxml import OxmlElement
    from docx.text.paragraph import Paragraph
    titulo_ref = next(p for p in doc.paragraphs if p.text == "LISTA DE QUADROS")
    sumario = next(p for p in doc.paragraphs if p.text == "SUMÁRIO")
    titulo = copy.deepcopy(titulo_ref._p)
    sumario._p.addprevious(titulo)
    tp = Paragraph(titulo, sumario._parent)
    for r in tp.runs[1:]:
        r._r.getparent().remove(r._r)
    tp.runs[0].text = "LISTA DE ABREVIATURAS E SIGLAS"
    for sigla, extenso in LISTA_SIGLAS:
        el = OxmlElement("w:p")
        sumario._p.addprevious(el)
        par = Paragraph(el, sumario._parent)
        par.paragraph_format.tab_stops.add_tab_stop(Cm(2.5))
        par.paragraph_format.line_spacing = 1.5
        par.add_run(f"{sigla}\t{extenso}")
    sumario._p.addprevious(OxmlElement("w:p"))  # linha em branco, como nas outras listas
    return True


def aplicar_citacoes(doc, pares=None) -> int:
    """Aplica pares (antigo, novo); aborta se uma ancora nao casar exatamente uma vez."""
    feitas = 0
    for antigo, novo in (CITACOES if pares is None else pares):
        if any(novo in p.text for p in doc.paragraphs):
            continue  # ja aplicada
        alvos = [r for p in doc.paragraphs for r in p.runs if antigo in r.text]
        if len(alvos) != 1:
            raise SystemExit(f"ancora casou {len(alvos)} vezes: {antigo[:60]!r}")
        alvos[0].text = alvos[0].text.replace(antigo, novo)
        feitas += 1
    return feitas


def inserir_set_rowcount(doc) -> bool:
    """Insere 'SET @alterou = ROW_COUNT();' apos o UPDATE do Apendice B."""
    if any(p.text.startswith("SET @alterou") for p in doc.paragraphs):
        return False
    ancora = next(p for p in doc.paragraphs if "AND d.ativo = TRUE;" in p.text and "registra" in p.text)
    novo = copy.deepcopy(ancora._p)
    ancora._p.addnext(novo)
    from docx.text.paragraph import Paragraph
    par = Paragraph(novo, ancora._parent)
    for r in par.runs[1:]:
        r._r.getparent().remove(r._r)
    par.runs[0].text = "SET @alterou = ROW_COUNT();     -- lido logo após o UPDATE"
    return True


def ajustar_titulos(doc) -> None:
    """Manter titulo com o proximo paragrafo e espacamento uniforme nos niveis 2 e 3."""
    for nome in ("Heading 1", "Heading 2", "Heading 3"):
        doc.styles[nome].paragraph_format.keep_with_next = True
    h2 = doc.styles["Heading 2"].paragraph_format
    h3 = doc.styles["Heading 3"].paragraph_format
    h3.space_before, h3.space_after = h2.space_before or Emu(152400), h2.space_after or Emu(76200)
    for p in doc.paragraphs:
        if p.style.name in ("Heading 2", "Heading 3"):
            p.paragraph_format.space_before = None
            p.paragraph_format.space_after = None


def main() -> None:
    doc = Document(ALVO)
    n = substituir_texto(doc)
    c = completar_conclusao(doc)
    a = inserir_referencia_anvisa(doc)
    s = inserir_set_rowcount(doc)
    cit = aplicar_citacoes(doc)
    refs = sum(inserir_referencia(doc, t, antes) for t, antes in REFERENCIAS_NOVAS)
    sig = aplicar_citacoes(doc, SIGLAS)
    neg = negritar_titulos(doc)
    lista = inserir_lista_siglas(doc)
    ajustar_recuo_e_resumos(doc)
    ajustar_titulos(doc)
    doc.save(ALVO)
    print(f"substituicoes={n} conclusao={c} ref_anvisa={a} set_rowcount={s} citacoes={cit} refs={refs} "
          f"siglas={sig} negrito={neg} lista_siglas={lista}")


if __name__ == "__main__":
    main()
