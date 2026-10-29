<!-- converted from PIM_II_Sabor_e_Cia_anterior.docx -->

UNIVERSIDADE PAULISTA – UNIP
Projeto Integrado Multidisciplinar
Curso Superior de Tecnologia em Análise e Desenvolvimento de Sistemas
NOME DO ALUNO – RA
SABOR & CIA BISTRÔ
Cardápio digital acessível com controle de disponibilidade por filial
Cidade do campus
2026

NOME DO ALUNO – RA
SABOR & CIA BISTRÔ
Cardápio digital acessível com controle de disponibilidade por filial
Projeto Integrado Multidisciplinar em Análise e Desenvolvimento de Sistemas

Projeto Integrado Multidisciplinar para obtenção do título de tecnólogo em Análise e Desenvolvimento de Sistemas, apresentado à Universidade Paulista – UNIP.

Orientador(a): nome do(a) orientador(a)
Cidade do campus
2026
RESUMO
[Resumo de 150 a 500 palavras – redigir por último, depois da Conclusão.] Palavras-chave: Cardápio digital. Acessibilidade. Restaurantes. Sistemas distribuídos. LGPD.
ABSTRACT
[Versão em inglês do resumo – redigir por último.] Keywords: Digital menu. Accessibility. Restaurants. Distributed systems. LGPD.
SUMÁRIO



# 1 INTRODUÇÃO
[Introdução – redigir por último: objetivo do trabalho, metodologia resumida e breve apresentação da organização, conforme o item 1.7 do Manual do PIM.]
# 2 CARACTERIZAÇÃO DA ORGANIZAÇÃO
A organização apresentada neste trabalho é fictícia e foi criada para fins acadêmicos, conforme orienta o Manual do PIM II. Ainda assim, sua caracterização procura reproduzir as condições de uma rede real de restaurantes da cidade de São Paulo, para que os problemas identificados e a solução proposta sejam plausíveis.
## 2.1 Identificação e ramo de atuação
A Sabor & Cia Ltda., que opera com o nome fantasia Sabor & Cia Bistrô, atua no ramo de alimentação fora do lar, no segmento de bistrô contemporâneo de padrão médio-alto. A empresa mantém uma matriz administrativa em Alphaville, no município de Barueri (SP), que não atende ao público, e três restaurantes na cidade de São Paulo, localizados nos bairros Jardins, Itaim Bibi e Pinheiros.
A separação entre razão social e nome fantasia é intencional: a pessoa jurídica responde pelas obrigações legais e fiscais do grupo, enquanto a marca comunicada ao cliente precisa refletir o posicionamento dos restaurantes.
## 2.2 Missão
A missão da Sabor & Cia Bistrô é oferecer uma experiência gastronômica de qualidade e consistente nas três unidades, com atendimento acolhedor e transparência sobre os ingredientes de cada prato.
## 2.3 Principais produtos e serviços
A rede trabalha com cardápio fixo, idêntico nas três unidades e com o mesmo preço em todas elas, composto por entradas, pratos principais, sobremesas e uma carta de vinhos servidos em taça ou garrafa. Os restaurantes funcionam no almoço e no jantar, e o ticket médio é de R$ 125,00 por pessoa. O pedido é lançado pelo garçom em uma maquininha de cartão, que também é usada para o pagamento na própria mesa.
## 2.4 Estrutura organizacional
A estrutura divide-se em dois níveis. Na matriz ficam a diretoria, formada pelos sócios, e as áreas administrativo-financeira, de compras e de marketing; o suporte de tecnologia da informação é terceirizado. Cada restaurante conta com um gerente, responsável pela operação diária, um chef e sua equipe de cozinha, um maître e a equipe de garçons.
As decisões sobre o cardápio, os preços e a identidade da marca são centralizadas na matriz, enquanto a gestão do dia a dia, incluindo o que está ou não disponível para venda, cabe a cada unidade. É justamente na fronteira entre essas duas responsabilidades que surgem os problemas descritos na seção 2.7.
## 2.5 Principais processos de negócio
Os processos centrais da organização são os seguintes:
a) atendimento ao cliente: o maître recebe o cliente e apresenta o cardápio impresso; o garçom lança o pedido na maquininha, a cozinha prepara os pratos e o pagamento é feito na mesa;
b) definição do cardápio: a matriz define os pratos, as descrições e os preços, que valem para as três unidades;
c) controle diário de disponibilidade: quando um prato se esgota, o chef avisa o gerente, que repassa a informação verbalmente aos garçons;
d) compras: a matriz consolida as necessidades das unidades e negocia com os fornecedores.
## 2.6 Público-alvo
O público da rede é formado por adultos das classes A e B: executivos no horário de almoço, casais e grupos no jantar e turistas nacionais e estrangeiros, presença mais frequente nas unidades Jardins e Itaim Bibi.
## 2.7 Problemas identificados
A análise dos processos permitiu identificar os seguintes problemas:
a) o cliente escolhe um prato que já se esgotou naquela unidade e só descobre isso depois de fazer o pedido, o que gera frustração e retrabalho;
b) a comunicação sobre pratos esgotados depende de avisos verbais entre cozinha, gerente e salão, que falham nos horários de maior movimento; além disso, a maquininha continua permitindo lançar um item indisponível;
c) o cardápio impresso não comporta informações sobre ingredientes, alérgenos e harmonização, de modo que clientes com alergia alimentar e turistas dependem inteiramente do garçom;
d) o cardápio impresso não pode ser lido de forma autônoma por uma pessoa com deficiência visual;
e) a matriz não tem uma visão consolidada de quais pratos se esgotam, em qual unidade e com que frequência, informação que seria útil para planejar as compras.
## 2.8 Justificativa da solução proposta
Os problemas descritos têm uma causa comum: a informação sobre o que está disponível em cada unidade não circula de forma confiável entre a cozinha, o salão, as maquininhas e o cliente. A solução proposta é um cardápio digital centralizado, acessado pelo cliente por meio de um QR code próprio de cada unidade, no qual a matriz mantém um cardápio único e cada gerente ativa ou desativa os pratos de sua unidade em tempo real. A mesma informação é consumida pelas maquininhas dos garçons, que deixam de oferecer itens esgotados.
O cardápio digital não substitui o atendimento: o cardápio impresso e o garçom continuam presentes, e o recurso digital acrescenta o que o papel não comporta, como ingredientes, alérgenos, harmonização, versão em inglês e compatibilidade com leitores de tela. A fundamentação dessa escolha é apresentada no capítulo 3.
# 3 PESQUISA CIENTÍFICA E INOVAÇÃO
## 3.1 Definição do problema
O uso de cardápios acessados por QR code se difundiu no setor de alimentação durante a pandemia de COVID-19. Pesquisa da Associação Brasileira de Bares e Restaurantes (2023), realizada no segundo semestre de 2022, indicou que 38% dos estabelecimentos adotavam esse tipo de cardápio, 25% estavam implantando ou pretendiam implantar e 11% haviam adotado e desistido após o fim das restrições sanitárias. A tecnologia, portanto, já é conhecida do setor, mas sua permanência depende do valor que ela agrega ao cliente e à operação.
Na prática, muitos desses cardápios são apenas a versão em PDF do cardápio impresso: não informam o que está disponível naquele momento, não trazem informações adicionais e, em geral, não são adequados a leitores de tela. Diante disso, o problema de pesquisa deste trabalho é: como uma rede de restaurantes com várias unidades pode manter o cardápio apresentado ao cliente sincronizado com a disponibilidade real de cada unidade, garantindo acesso à informação a pessoas com deficiência, a clientes com alergias alimentares e a estrangeiros?
## 3.2 Objetivos
### 3.2.1 Objetivo geral
Propor uma solução computacional de cardápio digital acessível, com controle de disponibilidade por unidade e integração às maquininhas dos garçons, para a rede fictícia Sabor & Cia Bistrô.
### 3.2.2 Objetivos específicos
a) levantar os requisitos da solução e planejar seu desenvolvimento com o framework Scrum;
b) modelar o banco de dados relacional e discutir o uso de um banco NoSQL para o histórico de alterações;
c) implementar em linguagem C a lógica central do controle de disponibilidade;
d) projetar a infraestrutura de rede das unidades e a arquitetura distribuída em nuvem;
e) avaliar a solução quanto à acessibilidade, à inclusão digital, à proteção de dados e aos direitos humanos.
## 3.3 Metodologia
Quanto à finalidade, a pesquisa é aplicada, pois busca resolver um problema concreto de uma organização; quanto aos objetivos, é exploratória, já que procura proporcionar maior familiaridade com o problema e torná-lo mais explícito (Gil, 2022). Quanto aos procedimentos, combina pesquisa bibliográfica, baseada em livros e artigos científicos, com pesquisa documental, que abrange leis, normas técnicas e relatórios estatísticos de órgãos oficiais (Marconi; Lakatos, 2021). A abordagem é qualitativa.
O trabalho foi desenvolvido nas seguintes etapas: levantamento bibliográfico e documental; caracterização da organização fictícia e de seus processos; levantamento de requisitos e modelagem do sistema com a UML; modelagem do banco de dados; implementação de uma simulação em linguagem C; projeto da infraestrutura de rede; e análise da solução à luz da legislação de acessibilidade e de proteção de dados. Por se tratar de uma organização fictícia, não houve coleta de dados com usuários reais, o que constitui uma limitação discutida no capítulo 9.
## 3.4 Fundamentação bibliográfica
### 3.4.1 Cardápios digitais e adoção de QR code
A literatura internacional sobre cardápios por QR code concentra-se na aceitação da tecnologia pelos consumidores. Em estudo com 844 clientes de restaurantes nos Estados Unidos, Iskender et al. (2024) mostraram que a intenção de uso é explicada principalmente pela possibilidade de experimentar a tecnologia e pela percepção de higiene. Koay e Ang (2024), por sua vez, verificaram que a expectativa de desempenho, a facilidade de uso, a influência social, o hábito e a percepção de proteção da privacidade influenciam positivamente a intenção de usar esses cardápios após a pandemia.
Esses resultados indicam que um cardápio digital precisa ser simples de usar e transmitir segurança quanto aos dados do cliente, dois requisitos incorporados à solução proposta.
### 3.4.2 Acessibilidade digital
Segundo o Censo Demográfico 2022, o Brasil tem 14,4 milhões de pessoas com deficiência, o equivalente a 7,3% da população com 2 anos ou mais; a dificuldade mais frequente é a de enxergar, relatada por 7,9 milhões de pessoas (Instituto Brasileiro de Geografia e Estatística, 2025). Para esse público, um cardápio impresso ou em imagem exige a ajuda de outra pessoa, enquanto um cardápio digital bem construído pode ser lido de forma autônoma com um leitor de tela.
A Lei Brasileira de Inclusão determina, em seu art. 63, que é obrigatória a acessibilidade nos sítios da internet mantidos por empresas com sede ou representação comercial no país, conforme as melhores práticas adotadas internacionalmente (Brasil, 2015). A principal referência internacional é a WCAG 2.1, que organiza os requisitos em quatro princípios: o conteúdo deve ser perceptível, operável, compreensível e robusto (W3C, 2018). No Brasil, a ABNT NBR 17225, publicada em 2025 e alinhada à WCAG 2.2, estabelece os requisitos de acessibilidade para conteúdo e aplicações web (Associação Brasileira de Normas Técnicas, 2025).
### 3.4.3 Inclusão digital
Um cardápio acessível apenas pelo celular pode excluir parte do público. A pesquisa TIC Domicílios 2025 estimou 28 milhões de brasileiros que não usam a internet, dos quais 16 milhões têm 60 anos ou mais (Comitê Gestor da Internet no Brasil, 2025). Por essa razão, a solução mantém o cardápio impresso e o atendimento pelo garçom, tratando o recurso digital como complemento.
### 3.4.4 Informação ao consumidor e alergias alimentares
O Código de Defesa do Consumidor assegura o direito à informação adequada e clara sobre os produtos, incluindo sua composição e os riscos que apresentam, e determina, em seu parágrafo único, que essa informação seja acessível à pessoa com deficiência (Brasil, 1990). No caso das alergias alimentares, essa informação é uma questão de saúde: o Consenso Brasileiro sobre Alergia Alimentar relata estudo com adultos brasileiros no qual 10,8% referiam sintomas de alergia alimentar, embora apenas 1,0% tivesse diagnóstico médico (Solé et al., 2018).
## 3.5 Análise de trabalhos relacionados
O Quadro 1 resume os trabalhos que mais se aproximam da proposta deste projeto, indicando a contribuição de cada um e a lacuna que permanece em aberto.
Quadro 1 – Trabalhos relacionados
| Trabalho | Foco | Principal contribuição | Lacuna em relação a este projeto |
| --- | --- | --- | --- |
| Iskender, Sirakaya-Turk e Cardenas (2023) | Percepção de clientes sobre cardápios por QR code (estudo qualitativo) | Clientes valorizam rapidez e ausência de contato, mas criticam cardápios pouco informativos e em PDF mal projetado | Não trata de acessibilidade nem de disponibilidade em tempo real |
| Iskender et al. (2024) | Modelo de aceitação de cardápios por QR code (844 clientes) | Experimentação e higiene explicam a intenção de uso | Foco na aceitação, não no conteúdo do cardápio |
| Koay e Ang (2024) | Intenção de uso no pós-pandemia (200 respondentes) | Facilidade de uso e percepção de privacidade influenciam a adoção | Não considera pessoas com deficiência |
| Radke et al. (2016) | Alergia alimentar em 278 restaurantes dos EUA | Apenas 22% dos cardápios mencionavam alérgenos | Não propõe solução tecnológica |
Fonte: elaborado pelo autor, 2026.
Iskender, Sirakaya-Turk e Cardenas (2023) mostram que as críticas dos clientes recaem mais sobre a qualidade da informação do que sobre a tecnologia em si. Radke et al. (2016) evidenciam que a informação sobre alérgenos nos cardápios é, em geral, precária. Os demais trabalhos concentram-se em explicar por que o cliente aceita ou rejeita o cardápio digital.
## 3.6 Justificativa científica
A análise da literatura mostra dois conjuntos de estudos que não se comunicam: os que tratam da aceitação do cardápio digital e os que tratam da informação sobre alérgenos. Nenhum dos trabalhos analisados integra, em uma mesma solução, a acessibilidade para pessoas com deficiência, a informação estruturada sobre alérgenos, o cardápio bilíngue e a disponibilidade atualizada por unidade. Essa lacuna justifica a proposta, que também responde a exigências legais concretas: a acessibilidade de sítios empresariais (Brasil, 2015) e o direito do consumidor à informação acessível (Brasil, 1990).
## 3.7 Diferenciais inovadores
Em relação às soluções encontradas na literatura e no mercado, a proposta apresenta os seguintes diferenciais:
a) disponibilidade por unidade atualizada em até 30 segundos e compartilhada entre o cardápio do cliente e as maquininhas dos garçons;
b) cardápio construído em HTML estruturado, e não em PDF, seguindo a WCAG 2.1 nível AA e a ABNT NBR 17225;
c) alérgenos cadastrados de forma estruturada, com filtro por alérgeno e aviso de que a informação é de referência;
d) versões em português e inglês, com o idioma marcado no código da página para que o leitor de tela faça a pronúncia correta;
e) privacidade desde a concepção: o cliente não se cadastra e o cardápio não utiliza cookies de rastreamento;
f) posicionamento como complemento ao atendimento, com manutenção do cardápio impresso e do garçom.
# 4 ENGENHARIA DE SOFTWARE
[Parte 2 – a redigir]
# 5 MODELAGEM DE BANCO DE DADOS
[Parte 3 – a redigir]
# 6 PROGRAMAÇÃO ESTRUTURADA
[Parte 4 – a redigir]
# 7 REDES DE COMPUTADORES E SISTEMAS DISTRIBUÍDOS
[Parte 5 – a redigir]
# 8 DIREITOS HUMANOS, INCLUSÃO E SEGURANÇA
[Parte 6 – a redigir]
# 9 INTEGRAÇÃO DA SOLUÇÃO
[Parte 7 – a redigir]
# 10 CONCLUSÃO
[Parte 8 – redigir por último]
# REFERÊNCIAS
ASSOCIAÇÃO BRASILEIRA DE BARES E RESTAURANTES. Cardápio por QR Code é uma questão de mercado, não de lei, diz Abrasel. [S. l.]: Abrasel, [2023]. Disponível em: https://abrasel.com.br/noticias/noticias/cardapio-por-qr-code-e-uma-questao-de-mercado-nao-de-lei-diz-abrasel/. Acesso em: dd mês. 2026.
ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 17225: acessibilidade em conteúdo e aplicações web: requisitos. Rio de Janeiro: ABNT, 2025.
BRASIL. Lei nº 8.078, de 11 de setembro de 1990. Dispõe sobre a proteção do consumidor e dá outras providências. Brasília, DF: Presidência da República, 1990. Disponível em: https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm. Acesso em: dd mês. 2026.
BRASIL. Lei nº 13.146, de 6 de julho de 2015. Institui a Lei Brasileira de Inclusão da Pessoa com Deficiência (Estatuto da Pessoa com Deficiência). Brasília, DF: Presidência da República, 2015. Disponível em: https://www.planalto.gov.br/ccivil03/ato2015-2018/2015/lei/l13146.htm. Acesso em: dd mês. 2026.
COMITÊ GESTOR DA INTERNET NO BRASIL. Pesquisa sobre o uso das tecnologias de informação e comunicação nos domicílios brasileiros: TIC Domicílios 2025: principais resultados. São Paulo: CGI.br, 2025. Disponível em: https://cetic.br/media/analises/ticdomicilios2025principaisresultados.pdf. Acesso em: dd mês. 2026.
GIL, Antonio Carlos. Como elaborar projetos de pesquisa. 7. ed. Barueri: Atlas, 2022. [conferir edição e cidade na ficha catalográfica]
INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. Censo 2022: Brasil tem 14,4 milhões de pessoas com deficiência. Rio de Janeiro: IBGE, 2025. Disponível em: https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/43463-censo-2022-brasil-tem-14-4-milhoes-de-pessoas-com-deficiencia. Acesso em: dd mês. 2026.
ISKENDER, Ali; SIRAKAYA-TURK, Ercan; CARDENAS, David. Restaurant menus and COVID-19: implications for technology adoption in the post-pandemic era. Consumer Behavior in Tourism and Hospitality, v. 18, n. 4, p. 587-605, 2023. DOI: https://doi.org/10.1108/CBTH-11-2022-0194.
ISKENDER, Ali; SIRAKAYA-TURK, Ercan; CARDENAS, David; HIKMET, Neset. Restaurant patrons' intentions toward QR code menus in the U.S. during COVID-19: acceptance of technology adoption model (ATAM). Journal of Foodservice Business Research, v. 27, n. 5, p. 497-522, 2024. DOI: https://doi.org/10.1080/15378020.2022.2133518.
KOAY, Kian Yeik; ANG, Kersoon. Understanding consumers' intentions to use QR code menus in the post-COVID-19 pandemic. British Food Journal, v. 126, n. 5, p. 2172-2186, 2024. DOI: https://doi.org/10.1108/BFJ-10-2023-0880.
MARCONI, Marina de Andrade; LAKATOS, Eva Maria. Fundamentos de metodologia científica. 9. ed. São Paulo: Atlas, 2021. [conferir edição na ficha catalográfica]
RADKE, Taylor J. et al. Food allergy knowledge and attitudes of restaurant managers and staff: an EHS-Net study. Journal of Food Protection, v. 79, n. 9, p. 1588-[página final], 2016. DOI: https://doi.org/10.4315/0362-028X.JFP-16-085.
SOLÉ, Dirceu et al. Consenso Brasileiro sobre Alergia Alimentar: 2018 – Parte 1 – Etiopatogenia, clínica e diagnóstico. Arquivos de Asma, Alergia e Imunologia, v. 2, n. 1, p. 7-38, 2018.
W3C. Web Content Accessibility Guidelines (WCAG) 2.1. [S. l.]: W3C, 2018. Disponível em: https://www.w3.org/TR/WCAG21/. Acesso em: dd mês. 2026.