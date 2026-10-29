# Graph Report - PIM-II  (2026-10-28)

## Corpus Check
- 5 files · ~65,944 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 201 nodes · 256 edges · 21 communities (15 shown, 6 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2a61a482`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- pseudocodigo_funcionalidades.txt (Apêndice C)
- sabor-cia.dbml (modelo DBML do banco)
- TCC (Tiny C Compiler)

## God Nodes (most connected - your core abstractions)
1. `main()` - 10 edges
2. `Switch gerenciavel 24 portas PoE (802.1Q - VLANs em trunk)` - 8 edges
3. `lerInteiro()` - 7 edges
4. `cadastrarProduto()` - 7 edges
5. `alterarDisponibilidade()` - 7 edges
6. `menuAdmin()` - 7 edges
7. `PRODUTO` - 7 edges
8. `Internet` - 7 edges
9. `API REST (autenticacao, cardapio, disponibilidade, relatorios)` - 7 edges
10. `UC04 Fazer login` - 7 edges

## Surprising Connections (you probably didn't know these)
- `diagramaDB.pdf (diagrama do banco de dados)` --shares_data_with--> `modelo_fisico_mysql.sql (modelo físico do banco)`  [INFERRED]
  database/diagramaDB.pdf → README.md
- `Sabor & Cia — PIM II (ADS) Projeto` --references--> `Manual/enunciado do PIM II (ADS)`  [EXTRACTED]
  README.md → docs/Manual_PIM_II_ADS.pdf
- `diagramaDB.pdf (diagrama do banco)` --references--> `diagramaDB.pdf (diagrama do banco de dados)`  [EXTRACTED]
  README.md → database/diagramaDB.pdf
- `simulacao_cardapio.c (simulação console em C)` --implements--> `AlterarDisponibilidade (RF06 e RF11)`  [INFERRED]
  README.md → docs/pseudocodigo_funcionalidades.txt
- `simulacao_cardapio.c (simulação console em C)` --implements--> `Autenticar (RF01, até 3 tentativas)`  [INFERRED]
  README.md → docs/pseudocodigo_funcionalidades.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Fluxo de alteração de disponibilidade** — docs_pseudocodigo_funcionalidades_alterar_disponibilidade, docs_pseudocodigo_funcionalidades_buscar_produto_por_id, docs_pseudocodigo_funcionalidades_salvar_dados, docs_pseudocodigo_funcionalidades_registrar_historico, docs_pseudocodigo_funcionalidades_matriz_disponibilidade [EXTRACTED 1.00]

## Communities (21 total, 6 thin omitted)

### Community 0 - "Simulação C — Funções"
Cohesion: 0.18
Nodes (26): adicionarProduto(), alterarDisponibilidade(), autenticar(), buscarFilialPorNome(), buscarProdutoPorId(), cadastrarProduto(), carregarDados(), carregarExemplo() (+18 more)

### Community 1 - "Fluxo Alterar Disponibilidade (Atividades)"
Cohesion: 0.17
Nodes (13): Alteracao e na filial do gerente?, Atualizar disponibilidade (MySQL), Confirmar alteracao ao gerente, Fim (alteracao negada), Fim (sucesso), Fork (bifurcacao paralela), Join (sincronizacao paralela), Marcar como inativo (+5 more)

### Community 2 - "Arquivos e Especificação Funcional"
Cohesion: 0.19
Nodes (13): AlterarDisponibilidade (RF06 e RF11), Autenticar (RF01, até 3 tentativas), BuscarFilialPorNome, BuscarProdutoPorId (busca linear), ExibirCardapio (RF07 e RF13), Matriz disponibilidade[produto][filial], RegistrarHistorico (acrescenta em historico.txt), RelatorioFrequencia (RF12) (+5 more)

### Community 3 - "Topologia de Nuvem e WAN"
Cohesion: 0.16
Nodes (18): API REST instancia A, API REST instancia B, Armazenamento de objetos (imagens), Balanceador de carga (HTTPS), CDN + WAF (borda do provedor), Celular do cliente (4G/5G ou Wi-Fi visitante), FILIAL Itaim Bibi Firewall UTM 10.3.0.0/16, FILIAL Jardins Firewall UTM 10.2.0.0/16 (+10 more)

### Community 5 - "Arquitetura em Camadas (Nuvem)"
Cohesion: 0.20
Nodes (16): API REST (autenticacao, cardapio, disponibilidade, relatorios), Armazenamento de imagens, Banco NoSQL (MongoDB) - historico de alteracoes, Banco relacional (MySQL) - produtos, filiais, usuarios, disponibilidade, Camada de aplicacao, Camada de apresentacao, Camada de dados, Cardapio publico (web responsivo, PT/EN) (+8 more)

### Community 6 - "Modelo Físico MySQL"
Cohesion: 0.17
Nodes (11): 1. Instalar o TCC, 2. Executar o programa, Alternativa sem instalar nada, Como executar a simulação no Windows, `database/`, `diagramas/`, `docs/`, Estrutura do projeto (+3 more)

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
Cohesion: 0.20
Nodes (11): Acessar painel administrativo, Chef informa que um prato esgotou, Credenciais validas?, Diagrama de atividades - Alterar disponibilidade de produto, Exibir mensagem de erro, Exibir produtos da filial do gerente, Fim (erro de credenciais), Informar e-mail e senha (+3 more)

### Community 15 - "Alérgenos e Legislação"
Cohesion: 0.67
Nodes (3): diagramaDB.pdf (diagrama do banco de dados), diagramaDB.pdf (diagrama do banco), modelo_fisico_mysql.sql (modelo físico do banco)

## Knowledge Gaps
- **51 isolated node(s):** ``src/``, ``database/``, ``docs/``, ``diagramas/``, `1. Instalar o TCC` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects ``src/``, ``database/``, ``docs/`` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._