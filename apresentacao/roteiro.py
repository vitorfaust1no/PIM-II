# -*- coding: utf-8 -*-
"""
Roteiro da apresentacao em video do PIM II - Sabor & Cia Bistro.

Cada item de SEGMENTOS vira um "slide" com narracao propria. Campos:
  id       -> identificador unico (usado nos arquivos intermediarios)
  tipo     -> "titulo" | "texto" | "diagrama" | "codigo" | "terminal"
  titulo   -> titulo exibido no slide
  subtitulo-> (tipo titulo) linha secundaria
  bullets  -> (tipo texto) lista de topicos
  asset    -> (tipo diagrama) nome do PNG em diagramas/
  codigo   -> (tipo codigo) texto monoespacado a exibir
  demo_part-> (tipo terminal) indice do trecho da saida do simulador (0,1,2)
  narracao -> texto em pt-BR que sera convertido em voz (edge-tts)

A narracao pode ter acentos normais; so a saida do programa C e sem acento.
"""

VOZ = "pt-BR-FranciscaNeural"

SEGMENTOS = [
    {
        "id": "01_abertura",
        "tipo": "titulo",
        "titulo": "Sabor & Cia Bistrô",
        "subtitulo": "Sistema de Cardápio Digital  •  PIM II — Análise e Desenvolvimento de Sistemas",
        "narracao": (
            "Olá! Esta é a apresentação do nosso Projeto Integrado Multidisciplinar, "
            "o PIM dois, do curso de Análise e Desenvolvimento de Sistemas. "
            "O projeto se chama Sabor e Cia Bistrô, um sistema de cardápio digital "
            "pensado para uma rede de restaurantes. Ao longo deste vídeo vamos percorrer "
            "o contexto do negócio, a arquitetura da solução, os perfis de usuário, "
            "os principais fluxos, o modelo de banco de dados, a infraestrutura de rede, "
            "os requisitos atendidos e, por fim, uma demonstração ao vivo do simulador "
            "escrito em linguagem C."
        ),
    },
    {
        "id": "02_contexto",
        "tipo": "texto",
        "titulo": "O problema",
        "bullets": [
            "Rede de bistrôs com 3 filiais: Jardins, Itaim Bibi e Pinheiros",
            "Pratos esgotam a toda hora — o cardápio impresso fica desatualizado",
            "Clientes com restrições alimentares precisam saber dos alérgenos",
            "A matriz não enxerga o que está faltando em cada unidade",
        ],
        "narracao": (
            "Vamos ao problema. A Sabor e Cia é uma rede com três filiais: Jardins, "
            "Itaim Bibi e Pinheiros. Em um restaurante, pratos esgotam o tempo todo, "
            "e o cardápio impresso vira um transtorno: o cliente pede um prato que "
            "acabou, e o garçom precisa voltar à cozinha. Além disso, clientes com "
            "alergias ou restrições alimentares precisam de informação clara sobre os "
            "ingredientes. E, do ponto de vista do negócio, a matriz não tem visibilidade "
            "do que está em falta em cada unidade. É esse conjunto de dores que o nosso "
            "sistema resolve."
        ),
    },
    {
        "id": "03_objetivos",
        "tipo": "texto",
        "titulo": "A solução",
        "bullets": [
            "Cardápio digital sempre atualizado, por filial",
            "Cliente filtra pratos por alérgeno antes de pedir",
            "Gerente ativa e desativa itens em tempo real",
            "Matriz acompanha disponibilidade e frequência de esgotamento",
        ],
        "narracao": (
            "A solução é um cardápio digital, sempre atualizado e separado por filial. "
            "O cliente consulta o cardápio ativo e pode filtrar os pratos por alérgeno, "
            "escondendo o que não pode comer. O gerente de cada filial ativa e desativa "
            "itens em tempo real, conforme a cozinha esgota ou repõe os insumos. "
            "E a matriz acompanha, por relatórios, quantos itens estão indisponíveis "
            "agora e com que frequência cada prato costuma esgotar. "
            "Tudo isso com um registro de histórico que garante rastreabilidade de cada mudança."
        ),
    },
    {
        "id": "04_arquitetura",
        "tipo": "diagrama",
        "titulo": "Arquitetura do sistema",
        "asset": "01_arquitetura.png",
        "narracao": (
            "Esta é a arquitetura geral da solução. Do lado esquerdo estão os clientes: "
            "navegador web, celular e tablet para o cardápio, além das maquininhas de "
            "pagamento e do painel administrativo. No centro, na nuvem, temos uma API REST "
            "distribuída atrás de um balanceador de carga, com proteção de WAF e uma CDN "
            "para servir as imagens dos pratos com rapidez. A persistência usa dois bancos: "
            "um banco relacional MySQL para produtos, usuários e disponibilidade, e um banco "
            "não relacional, o MongoDB, para o histórico e os logs de auditoria. "
            "É uma arquitetura em nuvem, escalável e preparada para atender as três filiais "
            "simultaneamente."
        ),
    },
    {
        "id": "05_casos_uso",
        "tipo": "diagrama",
        "titulo": "Casos de uso",
        "asset": "02_casos_de_uso.png",
        "narracao": (
            "O diagrama de casos de uso resume quem faz o quê no sistema. "
            "Temos três atores. O cliente visualiza o cardápio, troca o idioma e filtra "
            "por alérgeno. O gerente de filial faz login e controla a disponibilidade dos "
            "produtos da sua unidade. E o administrador, na matriz, cadastra produtos e gera "
            "os relatórios gerenciais. Repare que cada ator tem um conjunto bem delimitado "
            "de permissões — isso é fundamental para a segurança e para evitar que um gerente "
            "altere dados de outra filial."
        ),
    },
    {
        "id": "06_perfis",
        "tipo": "texto",
        "titulo": "Três perfis, três permissões",
        "bullets": [
            "Cliente — vê o cardápio ativo e filtra alérgenos (sem login)",
            "Gerente — login por filial; ativa/desativa apenas a sua unidade",
            "Administrador — matriz; cadastra produtos e vê relatórios",
            "Autenticação com 3 tentativas; ações registradas em histórico",
        ],
        "narracao": (
            "Aprofundando nos perfis: o cliente não precisa de login, ele simplesmente "
            "escolhe a filial e vê o cardápio ativo. O gerente faz login e sua filial já "
            "vem amarrada à credencial, então ele nunca consegue mexer em outra unidade. "
            "O administrador representa a matriz: cadastra novos produtos e tem acesso aos "
            "relatórios de todas as filiais. A autenticação permite até três tentativas "
            "antes de bloquear o acesso, e toda alteração de disponibilidade é registrada "
            "no histórico, com data, hora, usuário e filial."
        ),
    },
    {
        "id": "07_fluxo_cardapio",
        "tipo": "diagrama",
        "titulo": "Fluxo — Cliente visualiza o cardápio",
        "asset": "08_fluxo_cardapio.png",
        "narracao": (
            "Este fluxograma mostra o que acontece quando o cliente abre o cardápio. "
            "O sistema percorre todos os produtos da filial escolhida. Para cada item, "
            "verifica se ele está disponível naquela unidade; se estiver inativo, pula. "
            "Em seguida, aplica o filtro de alérgeno: se o cliente pediu para esconder "
            "pratos com leite, por exemplo, esses itens são contabilizados como ocultos "
            "e não aparecem. Os pratos aprovados são exibidos com nome, categoria, preço "
            "e lista de alérgenos. No final, o sistema informa quantos itens foram ocultados "
            "pelo filtro e exibe o aviso obrigatório sobre alérgenos."
        ),
    },
    {
        "id": "08_fluxo_alterar",
        "tipo": "diagrama",
        "titulo": "Fluxo — Gerente altera a disponibilidade",
        "asset": "07_fluxo_alterar.png",
        "narracao": (
            "Quando um prato acaba na cozinha, entra em ação o fluxo de alteração de "
            "disponibilidade. O gerente acessa o painel, visualiza o cardápio com o status "
            "de cada item e escolhe o produto pelo código. Depois seleciona a ação: ativar "
            "ou desativar. Um detalhe importante de projeto: o novo estado é informado de "
            "forma explícita, em vez de simplesmente inverter o valor atual. Isso torna a "
            "operação idempotente — repetir a mesma ação não desfaz a alteração. "
            "Confirmada a mudança, o sistema atualiza o banco, registra o histórico e reflete "
            "o novo cardápio tanto no menu público quanto nas maquininhas de pagamento."
        ),
    },
    {
        "id": "09_atividades",
        "tipo": "diagrama",
        "titulo": "Diagrama de atividades",
        "asset": "04_atividades.png",
        "narracao": (
            "O diagrama de atividades detalha essa mesma operação de ponta a ponta, "
            "com as raias de responsabilidade. A cozinha avisa que o item esgotou; o gerente "
            "acessa o painel e se autentica; o sistema valida as credenciais e, uma vez "
            "confirmado, marca o produto como inativo. A mudança e o registro de histórico são "
            "gravados juntos no MySQL e, em seguida, copiados para o MongoDB, usado nas "
            "análises. Por fim, o cardápio público e as "
            "maquininhas são atualizados, e o sistema confirma a operação ao gerente. "
            "É a visão dinâmica que complementa os fluxogramas anteriores."
        ),
    },
    {
        "id": "10_conceitual",
        "tipo": "diagrama",
        "titulo": "Modelo conceitual (Entidade-Relacionamento)",
        "asset": "05_conceitual.png",
        "narracao": (
            "Partindo para os dados, este é o modelo conceitual em notação de "
            "entidade e relacionamento. As entidades centrais são Produto, Categoria, "
            "Alérgeno, Filial e Usuário. Um produto pertence a uma categoria e pode conter "
            "vários alérgenos — uma relação muitos para muitos. E existe o relacionamento "
            "'disponível em', que liga produto e filial com um atributo que indica se o item "
            "está ativo naquela unidade. É justamente esse relacionamento que permite o mesmo "
            "prato estar disponível em uma filial e esgotado em outra."
        ),
    },
    {
        "id": "11_logico",
        "tipo": "diagrama",
        "titulo": "Modelo lógico",
        "asset": "06_logico.png",
        "narracao": (
            "No modelo lógico, em notação pé de galinha, as entidades viram tabelas "
            "normalizadas, com chaves primárias e estrangeiras e a cardinalidade explícita "
            "entre elas. A relação muitos para muitos entre produto e alérgeno é resolvida "
            "por uma tabela associativa. E a disponibilidade por filial vira uma tabela "
            "própria, com a data de atualização de cada registro. Esse é o passo que prepara "
            "o terreno para a implementação física no banco."
        ),
    },
    {
        "id": "12_classes",
        "tipo": "diagrama",
        "titulo": "Diagrama de classes",
        "asset": "03_classes.png",
        "narracao": (
            "Do ponto de vista da orientação a objetos, o diagrama de classes organiza o "
            "domínio. A classe Usuário é especializada em Administrador e Gerente, "
            "representando a herança de perfis. Temos ainda as classes Filial, Produto, "
            "Categoria, Alérgeno, Disponibilidade e Registro de Histórico, com suas "
            "associações e agregações. Essa modelagem guia tanto o banco relacional quanto "
            "o código da aplicação."
        ),
    },
    {
        "id": "13_mysql",
        "tipo": "codigo",
        "titulo": "Modelo físico — MySQL",
        "codigo": (
            "CREATE TABLE produto (\n"
            "  id            INT PRIMARY KEY AUTO_INCREMENT,\n"
            "  nome          VARCHAR(60) NOT NULL,\n"
            "  id_categoria  INT NOT NULL,\n"
            "  preco_cent    INT NOT NULL,\n"
            "  FOREIGN KEY (id_categoria) REFERENCES categoria(id)\n"
            ");\n\n"
            "CREATE TABLE disponibilidade (\n"
            "  id_produto    INT NOT NULL,\n"
            "  id_filial     INT NOT NULL,\n"
            "  ativo         TINYINT(1) NOT NULL DEFAULT 1,\n"
            "  atualizado_em DATETIME NOT NULL,\n"
            "  PRIMARY KEY (id_produto, id_filial)\n"
            ");\n\n"
            "-- Senhas: bcrypt (CHAR 60). Nenhuma senha em texto puro.\n"
            "-- Histórico de alterações -> auditoria (RF11)."
        ),
        "narracao": (
            "O modelo físico foi implementado em MySQL. Aqui vemos, por exemplo, a tabela "
            "de produtos, com chave primária autoincremento e chave estrangeira para a "
            "categoria. E a tabela de disponibilidade, cuja chave primária é composta por "
            "produto e filial, garantindo um único registro de status para cada combinação, "
            "com a data da última atualização. Um ponto de segurança que destacamos no projeto: "
            "no banco, as senhas dos usuários nunca ficam em texto puro — são armazenadas como hash "
            "bcrypt. E cada alteração de disponibilidade alimenta uma trilha de auditoria, "
            "atendendo ao requisito de histórico."
        ),
    },
    {
        "id": "14_rede_geral",
        "tipo": "diagrama",
        "titulo": "Topologia de rede — Nuvem e WAN",
        "asset": "09_rede_geral.png",
        "narracao": (
            "Na camada de infraestrutura, esta é a topologia geral, cobrindo a nuvem e a "
            "rede de longa distância. As três filiais e a matriz se conectam à nuvem por "
            "uma conexão segura. Dentro do provedor, temos uma rede virtual privada com sub-redes públicas "
            "e privadas distribuídas em zonas de disponibilidade diferentes, o que dá "
            "tolerância a falhas. Os serviços incluem o banco MySQL gerenciado, o MongoDB, "
            "múltiplas instâncias da API atrás de um balanceador, além de CDN e WAF. "
            "A conectividade de cada filial tem um link principal de fibra óptica e um link "
            "de contingência via quatro G ou cinco G."
        ),
    },
    {
        "id": "15_rede_filial",
        "tipo": "diagrama",
        "titulo": "Rede local da filial — VLANs",
        "asset": "10_rede_filial.png",
        "narracao": (
            "Já esta é a rede local de uma filial. O tráfego é segmentado em vê-lans por "
            "função: uma vê-lan de operação para os servidores e a gestão, uma vê-lan dedicada "
            "às maquininhas de pagamento, uma vê-lan isolada para o Wi-Fi de visitantes, uma "
            "vê-lan de segurança para as câmeras alimentadas pela própria rede, e uma vê-lan "
            "de gerência dos próprios equipamentos de rede. Um firewall corporativo faz o "
            "roteamento entre as vê-lans e mantém um túnel VPN criptografado com a matriz. "
            "A cobertura sem fio usa Wi-Fi seis, e a segmentação "
            "garante que a rede de visitantes nunca tenha acesso aos sistemas internos."
        ),
    },
    {
        "id": "16_requisitos",
        "tipo": "texto",
        "titulo": "Requisitos funcionais: simulação e proposta",
        "bullets": [
            "RF01 Autenticar  •  RF05 Cadastrar produto (parcial)  •  RF06 Alterar disponibilidade",
            "RF07 Exibir cardápio  •  RF09 Filtrar alérgeno  •  RF11 Registrar histórico",
            "RF12 Relatórios (indisponibilidade e frequência)  •  RF13 Alérgenos (inglês só na proposta)",
            "Só na proposta: RF02 QR code  •  RF03 Idioma  •  RF04 e RF10 Maquininhas  •  RF08 Categoria",
        ],
        "narracao": (
            "Vamos consolidar os requisitos funcionais. O erre efe zero um é a "
            "autenticação. O cinco aparece em parte: o simulador cadastra só os produtos. O "
            "seis é a alteração de disponibilidade. O sete, a exibição do cardápio, e o nove, "
            "o filtro por alérgeno. O onze é o registro de histórico para auditoria, e o doze "
            "cobre os relatórios gerenciais, tanto o de indisponibilidade atual quanto o de "
            "frequência de esgotamento. O treze também aparece em parte: a informação de "
            "alérgenos, com o aviso obrigatório, sem a versão em inglês. Esses requisitos "
            "aparecem no simulador. Já o dois, o código quê-erre de cada filial, o três, a troca de idioma, o "
            "quatro e o dez, o cadastro e a integração das maquininhas, e o oito, o filtro por "
            "categoria, fazem parte da proposta para o sistema real."
        ),
    },
    {
        "id": "17_seguranca",
        "tipo": "texto",
        "titulo": "Segurança e boas práticas",
        "bullets": [
            "Senhas em hash (bcrypt); tokens de dispositivo em SHA-256",
            "Em produção: nenhuma credencial no código ou em texto puro",
            "Permissões por perfil — gerente limitado à própria filial",
            "Operações idempotentes e trilha de auditoria completa",
            "Simulador em C: usuários de teste fixos, só para fins didáticos",
        ],
        "narracao": (
            "Em segurança, adotamos boas práticas desde o projeto. As senhas de usuário são "
            "guardadas como hash bcrypt, e os tokens dos dispositivos usam SHA duzentos e "
            "cinquenta e seis. No sistema em produção, nenhuma credencial fica no código ou em "
            "texto puro. O controle de acesso é "
            "por perfil, com o gerente restrito à sua própria filial. As operações críticas "
            "são idempotentes, evitando efeitos colaterais de cliques repetidos, e cada "
            "mudança gera um registro na trilha de auditoria. No simulador em C, por ser "
            "didático, os usuários de teste são fixos e as senhas ficam em texto puro; o "
            "código e a tela de login avisam isso, e a seção seis ponto sete do relatório "
            "compara a simulação com a implementação prevista."
        ),
    },
    {
        "id": "18_codigo_c",
        "tipo": "codigo",
        "titulo": "Implementação em C — estruturas centrais",
        "codigo": (
            "typedef struct {\n"
            "    int  id;\n"
            "    char nome[60];\n"
            "    char categoria[30];\n"
            "    int  preco_cent;   /* centavos: evita erro de float */\n"
            "    char alergenos[80];\n"
            "} Produto;\n\n"
            "Produto produtos[MAX_PRODUTOS];\n"
            "/* matriz produto x filial: 1 = ativo, 0 = inativo */\n"
            "int disponibilidade[MAX_PRODUTOS][NUM_FILIAIS];\n\n"
            "const char *FILIAIS[NUM_FILIAIS] =\n"
            "    {\"Jardins\", \"Itaim Bibi\", \"Pinheiros\"};"
        ),
        "narracao": (
            "No código em C, o coração do sistema são duas estruturas de dados. Um vetor de "
            "produtos, em que cada produto é uma struct com código, nome, categoria, preço "
            "e lista de alérgenos. Note que o preço é guardado em centavos, como número "
            "inteiro, para evitar os erros de arredondamento típicos do ponto flutuante. "
            "E uma matriz de disponibilidade, que cruza produto com filial, usando um para "
            "ativo e zero para inativo. É essa matriz que permite o controle independente por "
            "unidade. Os dados são persistidos em arquivos texto, simulando o papel do banco "
            "de dados."
        ),
    },
    {
        "id": "19_demo_cliente",
        "tipo": "terminal",
        "titulo": "Demonstração — Visão do cliente",
        "demo_part": 0,
        "narracao": (
            "Agora a demonstração ao vivo do simulador. Começamos pela visão do cliente. "
            "Ele escolhe a filial Jardins e vê o cardápio completo: a burrata, o risoto de "
            "cogumelos, o salmão, o petit gateau e o vinho, cada um com preço e alérgenos, "
            "seguidos do aviso de referência sobre alergias. Na segunda consulta, o cliente "
            "aplica o filtro por leite. Repare que os pratos que contêm leite somem da lista "
            "e o sistema informa quantos itens foram ocultados pelo filtro. É exatamente o "
            "comportamento do fluxograma que vimos antes."
        ),
    },
    {
        "id": "20_demo_gerente",
        "tipo": "terminal",
        "titulo": "Demonstração — Gerente desativa um prato",
        "demo_part": 1,
        "narracao": (
            "Em seguida, o gerente da filial Itaim Bibi faz login. Imagine que o risoto de "
            "cogumelos acabou na cozinha. Ele acessa a opção de alterar disponibilidade, "
            "informa o código do produto e escolhe desativar. O sistema confirma que o risoto "
            "agora está inativo na filial Itaim Bibi e registra essa mudança no histórico. "
            "Ao listar o cardápio novamente, o risoto aparece com o status inativo — e, para "
            "o cliente daquela filial, ele deixaria de ser exibido imediatamente."
        ),
    },
    {
        "id": "21_demo_admin",
        "tipo": "terminal",
        "titulo": "Demonstração — Relatórios da matriz",
        "demo_part": 2,
        "narracao": (
            "Por fim, o administrador entra na matriz. Primeiro ele lista todos os produtos "
            "com a disponibilidade em cada filial, enxergando o risoto inativo em Itaim Bibi. "
            "Depois gera o relatório de indisponibilidade, que mostra quantos itens estão "
            "esgotados agora em cada unidade. E, por último, o relatório de frequência de "
            "esgotamento, que lê o histórico e conta quantas vezes cada prato foi desativado, "
            "por filial. São essas informações que ajudam a matriz a planejar compras e a "
            "identificar os pratos mais sensíveis a faltas."
        ),
    },
    {
        "id": "22_encerramento",
        "tipo": "texto",
        "titulo": "Conclusão e próximos passos",
        "bullets": [
            "Experiência melhor para o cliente, com disponibilidade em tempo real",
            "Segurança alimentar com aviso de alérgenos",
            "Gestão ágil por filial e visão gerencial na matriz",
            "Futuro: previsão de demanda com IA, fotos e informação nutricional",
        ],
        "narracao": (
            "Para concluir: o Sabor e Cia entrega uma experiência melhor para o cliente, "
            "com disponibilidade em tempo real e informação clara sobre alérgenos, promovendo "
            "segurança alimentar. Dá agilidade ao gerente, que reage rápido às faltas, e "
            "oferece à matriz uma visão gerencial de toda a rede, com auditoria de cada "
            "mudança. Como evolução futura, imaginamos previsão de demanda com inteligência "
            "artificial, galeria de fotos dos pratos e informação nutricional detalhada. "
            "Esse foi o nosso PIM dois, o Sabor e Cia Bistrô. Muito obrigado pela atenção!"
        ),
    },
]
