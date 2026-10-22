# Sabor & Cia — PIM II (ADS)

Projeto Integrado Multidisciplinar da empresa fictícia **Sabor & Cia**: uma
simulação de console em C para gestão de cardápio, acompanhada do modelo de
banco de dados, pseudocódigo das funcionalidades e diagramas (UML, banco e rede).

## Estrutura do projeto

```
saborEcia/
├── README.md        este guia
├── LICENSE
├── .vscode/         tarefas de build do VS Code (MSVC)
├── src/             código-fonte em C
├── database/        modelo e scripts do banco de dados
├── docs/            documentação (pseudocódigo, manual, relatório)
└── diagramas/       diagramas UML, conceitual/lógico e de rede
```

### `src/`
- `simulacao_cardapio.c` — código-fonte da simulação de console em C (Apêndice A).

### `database/`
- `modelo_fisico_mysql.sql` — script SQL do modelo físico do banco (Apêndice B).
  ATENÇÃO: o script contém `DROP DATABASE IF EXISTS sabor_cia;`. Revise o comando
  antes de executar, pois ele apaga um banco existente com esse nome.
- `sabor-cia.dbml` — modelo do banco em formato DBML.
- `diagramaDB.pdf` — diagrama do banco de dados exportado.

### `docs/`
- `pseudocodigo_funcionalidades.txt` — pseudocódigo das principais funcionalidades (Apêndice C).
- `Manual_PIM_II_ADS.pdf` — manual/enunciado do PIM II.
- `PIM_II_Sabor_e_Cia.docx` — relatório final do projeto.
- `PIM_II_Sabor_e_Cia_anterior.docx` — versão anterior do relatório.

### `diagramas/`
- Fontes editáveis: `atividades-sabor-cia.drawio`, `casos-de-uso-sabor-cia.drawio`,
  `classes-sabor-cia.drawio` e `estilo.iuml` (estilo PlantUML).
- Imagens exportadas: `01_arquitetura.png`, `02_casos_de_uso.png`, `03_classes.png`,
  `04_atividades.png`, `05_conceitual.png`, `06_logico.png`, `07_fluxo_alterar.png`,
  `08_fluxo_cardapio.png`, `09_rede_geral.png`, `10_rede_filial.png`.


## Como executar a simulação no Windows

A simulação roda com o TCC (Tiny C Compiler). O comando `tcc -run` compila o
programa na memória e já o executa, sem gerar arquivo `.exe`.

### 1. Instalar o TCC

1. Baixe o TCC para Windows 64 bits:
   https://download.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win64-bin.zip
2. Extraia o zip em `C:\Users\<seu-usuario>\tools`. O resultado deve ser a
   pasta `C:\Users\<seu-usuario>\tools\tcc`, com o `tcc.exe` dentro.
3. Adicione essa pasta ao PATH, de acordo com o terminal que você usa:

   **PowerShell ou Prompt de Comando:** execute o comando abaixo uma vez no
   PowerShell. Depois feche e reabra o terminal. No VS Code, feche e reabra o
   VS Code inteiro.

   ```powershell
   [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ";$env:USERPROFILE\tools\tcc", 'User')
   ```

   **Git Bash:** execute uma vez:

   ```bash
   echo 'export PATH="$PATH:$HOME/tools/tcc"' >> ~/.bashrc
   source ~/.bashrc
   ```

4. Confira a instalação com `tcc -v`. A saída esperada é
   `tcc version 0.9.27 (x86_64 Windows)`.

### 2. Executar o programa

No terminal, entre na pasta do projeto e rode:

```
tcc -run src/simulacao_cardapio.c
```

O programa cria os arquivos `cardapio.txt` (produtos e disponibilidade) e
`historico.txt` (log de alterações) na pasta em que foi executado. Na primeira
execução são carregados 5 produtos de exemplo. Para voltar ao estado inicial,
apague o `cardapio.txt` e o `historico.txt`.

Usuários disponíveis no acesso interno:

| Login       | Senha    | Perfil                          |
|-------------|----------|---------------------------------|
| `admin`     | admin123 | Administrador                   |
| `jardins`   | 1234     | Gerente da filial Jardins       |
| `itaim`     | 1234     | Gerente da filial Itaim Bibi    |
| `pinheiros` | 1234     | Gerente da filial Pinheiros     |

### Alternativa sem instalar nada

Copie o conteúdo de `src/simulacao_cardapio.c` para um compilador online, como o
[OnlineGDB](https://www.onlinegdb.com/online_c_compiler), e clique em **Run**.

### Problemas comuns

- **`tcc: command not found`** ou **"tcc não é reconhecido"**: o terminal foi
  aberto antes da alteração do PATH. Reabra o terminal; no VS Code, reabra o
  VS Code. No Git Bash, rode `source ~/.bashrc`.
- **"Valor invalido" na primeira opção ao enviar entradas por pipe no
  PowerShell**: o PowerShell insere um caractere invisível (BOM) no início do
  texto. Digite as opções manualmente ou use o Git Bash.
