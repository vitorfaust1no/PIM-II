# Graph Report - PIM-II  (2026-10-27)

## Corpus Check
- Corpus is ~10,693 words - fits in a single context window. You may not need a graph.

## Summary
- 230 nodes · 310 edges · 18 communities (16 shown, 2 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.88)
- Token cost: 355,794 input · 0 output

## Community Hubs (Navigation)
- Simulação C — Funções
- Fluxo Alterar Disponibilidade (Atividades)
- Arquivos e Especificação Funcional
- Topologia de Nuvem e WAN
- Relatório PIM & Fontes QR Code
- Arquitetura em Camadas (Nuvem)
- Modelo Físico MySQL
- Casos de Uso
- Fluxograma Alterar Disponibilidade
- Rede Local da Filial (VLANs)
- Fluxograma Exibir Cardápio
- Modelo Conceitual (ER)
- Diagrama de Classes
- Modelo Lógico (DER)
- Acessibilidade e Normas (WCAG)
- Alérgenos e Legislação
- Integração Maquininha (API)
- Inclusão Digital (CGI.br)

## God Nodes (most connected - your core abstractions)
1. `main()` - 9 edges
2. `simulacao_cardapio.c (simulação console em C)` - 9 edges
3. `Relatório PIM II Sabor & Cia Bistrô` - 8 edges
4. `Switch gerenciavel 24 portas PoE (802.1Q - VLANs em trunk)` - 8 edges
5. `lerInteiro()` - 7 edges
6. `cadastrarProduto()` - 7 edges
7. `alterarDisponibilidade()` - 7 edges
8. `menuAdmin()` - 7 edges
9. `AlterarDisponibilidade (RF06 e RF11)` - 7 edges
10. `API REST (autenticacao, cardapio, disponibilidade, relatorios)` - 7 edges

## Surprising Connections (you probably didn't know these)
- `diagramaDB.pdf (diagrama do banco de dados)` --shares_data_with--> `modelo_fisico_mysql.sql (modelo físico do banco)`  [INFERRED]
  database/diagramaDB.pdf → README.md
- `Relatório PIM II Sabor & Cia Bistrô` --references--> `Manual/enunciado do PIM II (ADS)`  [EXTRACTED]
  graphify-out/converted/PIM_II_Sabor_e_Cia_085a17ab.md → docs/Manual_PIM_II_ADS.pdf
- `Sabor & Cia — PIM II (ADS) Projeto` --references--> `Manual/enunciado do PIM II (ADS)`  [EXTRACTED]
  README.md → docs/Manual_PIM_II_ADS.pdf
- `Relatório PIM II Sabor & Cia Bistrô` --references--> `simulacao_cardapio.c (simulação console em C)`  [INFERRED]
  graphify-out/converted/PIM_II_Sabor_e_Cia_085a17ab.md → README.md
- `simulacao_cardapio.c (simulação console em C)` --implements--> `Autenticar (RF01, até 3 tentativas)`  [INFERRED]
  README.md → docs/pseudocodigo_funcionalidades.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Fluxo de alteração de disponibilidade** — docs_pseudocodigo_funcionalidades_alterar_disponibilidade, docs_pseudocodigo_funcionalidades_buscar_produto_por_id, docs_pseudocodigo_funcionalidades_salvar_dados, docs_pseudocodigo_funcionalidades_registrar_historico, docs_pseudocodigo_funcionalidades_matriz_disponibilidade [EXTRACTED 1.00]
- **Fundamentação de acessibilidade digital** — pim_ii_sabor_e_cia_acessibilidade_digital, pim_ii_sabor_e_cia_wcag, pim_ii_sabor_e_cia_abnt_nbr_17225, pim_ii_sabor_e_cia_lei_brasileira_inclusao [EXTRACTED 1.00]
- **Diferenciais da solução Sabor & Cia** — pim_ii_sabor_e_cia_cardapio_digital_acessivel, pim_ii_sabor_e_cia_controle_disponibilidade, pim_ii_sabor_e_cia_alergenos, pim_ii_sabor_e_cia_privacidade_concepcao, pim_ii_sabor_e_cia_acessibilidade_digital [EXTRACTED 1.00]

## Communities (18 total, 2 thin omitted)

### Community 0 - "Simulação C — Funções"
Cohesion: 0.18
Nodes (21): adicionarProduto(), alterarDisponibilidade(), autenticar(), buscarFilialPorNome(), buscarProdutoPorId(), cadastrarProduto(), carregarDados(), carregarExemplo() (+13 more)

### Community 1 - "Fluxo Alterar Disponibilidade (Atividades)"
Cohesion: 0.09
Nodes (24): Acessar painel administrativo, Alteracao e na filial do gerente?, Atualizar disponibilidade (MySQL), Chef informa que um prato esgotou, Confirmar alteracao ao gerente, Credenciais validas?, Diagrama de atividades - Alterar disponibilidade de produto, Exibir mensagem de erro (+16 more)

### Community 2 - "Arquivos e Especificação Funcional"
Cohesion: 0.14
Nodes (20): diagramaDB.pdf (diagrama do banco de dados), AlterarDisponibilidade (RF06 e RF11), Autenticar (RF01, até 3 tentativas), BuscarFilialPorNome, BuscarProdutoPorId (busca linear), ExibirCardapio (RF07 e RF13), Matriz disponibilidade[produto][filial], RegistrarHistorico (acrescenta em historico.txt) (+12 more)

### Community 3 - "Topologia de Nuvem e WAN"
Cohesion: 0.16
Nodes (18): API REST instancia A, API REST instancia B, Armazenamento de objetos (imagens), Balanceador de carga (HTTPS), CDN + WAF (borda do provedor), Celular do cliente (4G/5G ou Wi-Fi visitante), FILIAL Itaim Bibi Firewall UTM 10.3.0.0/16, FILIAL Jardins Firewall UTM 10.2.0.0/16 (+10 more)

### Community 4 - "Relatório PIM & Fontes QR Code"
Cohesion: 0.12
Nodes (14): Manual/enunciado do PIM II (ADS), ABRASEL (2023) QR code mercado, Relatório PIM II Sabor & Cia (versão anterior), Iskender, Sirakaya-Turk e Cardenas (2023), Iskender et al. (2024) ATAM QR code menus, Koay e Ang (2024) intenção de uso pós-pandemia, Integração com maquininhas dos garçons, Sabor & Cia Bistrô (organização fictícia) (+6 more)

### Community 5 - "Arquitetura em Camadas (Nuvem)"
Cohesion: 0.20
Nodes (16): API REST (autenticacao, cardapio, disponibilidade, relatorios), Armazenamento de imagens, Banco NoSQL (MongoDB) - historico de alteracoes, Banco relacional (MySQL) - produtos, filiais, usuarios, disponibilidade, Camada de aplicacao, Camada de apresentacao, Camada de dados, Cardapio publico (web responsivo, PT/EN) (+8 more)

### Community 6 - "Modelo Físico MySQL"
Cohesion: 0.28
Nodes (14): alergeno, categoria, disponibilidade, dispositivo, filial, harmonizacao, historico_disponibilidade, idx_disp_filial_ativo (+6 more)

### Community 7 - "Casos de Uso"
Cohesion: 0.17
Nodes (15): Administrador (matriz), Cliente, Gerente de filial, Sistema de Cardápio Digital, UC01 Visualizar cardápio da filial, UC02 Trocar idioma, UC03 Filtrar por categoria/alérgeno, UC04 Fazer login (+7 more)

### Community 8 - "Fluxograma Alterar Disponibilidade"
Cohesion: 0.18
Nodes (14): disponibilidade[pos][filial] = 1?, disponibilidade[pos][filial] ← 0 / ação ← DESATIVAR, disponibilidade[pos][filial] ← 1 / ação ← ATIVAR, Escrever confirmação, Escrever "Produto não encontrado", ExibirCardapio(filial, com status), Fim, id = 0? (+6 more)

### Community 9 - "Rede Local da Filial (VLANs)"
Cohesion: 0.15
Nodes (13): Access point Wi-Fi 6 - Cozinha/caixa (SSIDs: Visitantes + Operacao), Access point Wi-Fi 6 - Salao (SSIDs: Visitantes + Operacao), Cameras IP (PoE) (VLAN 40 - Seguranca, 10.2.40.0/24, aviso visivel: retencao 30 dias), Firewall UTM / roteador (VPN IPsec ate a matriz, roteamento entre VLANs + regras), Gerencia de rede (VLAN 99, 10.2.99.0/24, switch, APs), Link de contingencia (4G/5G), Link principal (fibra optica), Maquininhas smart (Wi-Fi) (VLAN 20 - Operacao, 10.2.20.0/24) (+5 more)

### Community 10 - "Fluxograma Exibir Cardápio"
Cohesion: 0.24
Nodes (11): disponibilidade[i][filial] = 1?, Escrever "Nenhum produto disponível no momento", Escrever nome, categoria e preço de produtos[i], exibidos = 0?, Fim, i < qtdProdutos?, exibidos ← exibidos + 1, i ← i + 1 (+3 more)

### Community 11 - "Modelo Conceitual (ER)"
Cohesion: 0.29
Nodes (10): ALERGENO, CATEGORIA, contém (relacionamento), disponível em (relacionamento), FILIAL, gerencia (relacionamento), harmoniza com (relacionamento), pertence (relacionamento) (+2 more)

### Community 12 - "Diagrama de Classes"
Cohesion: 0.31
Nodes (9): Administrador, Alergeno, Categoria, Disponibilidade, Filial, Gerente, Produto, RegistroHistorico (+1 more)

### Community 13 - "Modelo Lógico (DER)"
Cohesion: 0.25
Nodes (8): alergeno, categoria, disponibilidade, filial, harmonizacao, produto, produto_alergeno, usuario

### Community 14 - "Acessibilidade e Normas (WCAG)"
Cohesion: 0.40
Nodes (5): ABNT NBR 17225 (acessibilidade web), Acessibilidade digital (WCAG, leitores de tela), IBGE Censo 2022 (pessoas com deficiência), Lei Brasileira de Inclusão (Lei 13.146/2015), WCAG 2.1 (W3C, 2018)

### Community 15 - "Alérgenos e Legislação"
Cohesion: 0.50
Nodes (4): Informação estruturada sobre alérgenos, Código de Defesa do Consumidor (Lei 8.078/1990), Radke et al. (2016) alergia alimentar em restaurantes, Solé et al. (2018) Consenso Brasileiro Alergia Alimentar

## Knowledge Gaps
- **52 isolated node(s):** `sabor-cia.dbml (modelo DBML do banco)`, `TCC (Tiny C Compiler)`, `BuscarFilialPorNome`, `Problemas identificados (disponibilidade, acessibilidade, alérgenos)`, `Inclusão digital` (+47 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 57 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `simulacao_cardapio.c (simulação console em C)` connect `Arquivos e Especificação Funcional` to `Relatório PIM & Fontes QR Code`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `simulacao_cardapio.c (simulação console em C)` (e.g. with `Relatório PIM II Sabor & Cia Bistrô` and `AlterarDisponibilidade (RF06 e RF11)`) actually correct?**
  _`simulacao_cardapio.c (simulação console em C)` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `sabor-cia.dbml (modelo DBML do banco)`, `TCC (Tiny C Compiler)`, `BuscarFilialPorNome` to the rest of the system?**
  _52 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Fluxo Alterar Disponibilidade (Atividades)` be split into smaller, more focused modules?**
  _Cohesion score 0.09057971014492754 - nodes in this community are weakly interconnected._
- **Why does `Relatório PIM II Sabor & Cia Bistrô` connect `Relatório PIM & Fontes QR Code` to `Arquivos e Especificação Funcional`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Relatório PIM II Sabor & Cia Bistrô` (e.g. with `Relatório PIM II Sabor & Cia (versão anterior)` and `simulacao_cardapio.c (simulação console em C)`) actually correct?**
  _`Relatório PIM II Sabor & Cia Bistrô` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Arquivos e Especificação Funcional` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._