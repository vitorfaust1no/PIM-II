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
├── tests/           testes automatizados (simulação em C e modelo SQL)
├── docs/            documentação (pseudocódigo, manual, relatório, evidências)
└── diagramas/       diagramas UML, conceitual/lógico e de rede
```

### `src/`
- `simulacao_cardapio.c` — código-fonte da simulação de console em C (Apêndice A).

### `database/`
- `modelo_fisico_mysql.sql` — script SQL do modelo físico do banco (Apêndice B).
  ATENÇÃO: o script contém `DROP DATABASE IF EXISTS sabor_cia;`. Revise o comando
  antes de executar, pois ele apaga um banco existente com esse nome.
- `testes_modelo_fisico.sql` — testes do modelo físico (estrutura, transação,
  ROLLBACK e testes negativos de CHECK, trigger, FK e UNIQUE). Rode depois do script
  acima, com `mysql --force`, pois os testes negativos devem terminar em erro.
- `sabor-cia.dbml` — modelo do banco em formato DBML.
- `diagramaDB.pdf` — diagrama do banco de dados exportado.

### `docs/`
- `pseudocodigo_funcionalidades.txt` — pseudocódigo das principais funcionalidades (Apêndice C).
- `Manual_PIM_II_ADS.pdf` — manual/enunciado do PIM II.
- `PIM_II_Sabor_e_Cia.docx` — relatório final do projeto.
- `PIM_II_Sabor_e_Cia_anterior.docx` — versão anterior do relatório.
- `evidencias/` — saídas dos testes (transcrições, logs, prints PNG e `resumo.json`)
  usadas na seção 5.7, na seção 6.8 e no Apêndice D do relatório.
- `scripts/` — scripts Python que aplicam a revisão no relatório `.docx`
  (requerem `python-docx` e `Pillow`; ex.: `python docs/scripts/reparar_docx.py`).

### `diagramas/`
- Fontes editáveis: `atividades-sabor-cia.drawio`, `casos-de-uso-sabor-cia.drawio`,
  `classes-sabor-cia.drawio` e `estilo.iuml` (estilo PlantUML).
- `sem_titulo/` — mesmas imagens sem a faixa de título, usadas no relatório.
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
apague o `cardapio.txt` e o `historico.txt` (e o `cardapio.tmp`, se existir).

A gravação é "tudo ou nada": o programa escreve primeiro em `cardapio.tmp` e só
troca o `cardapio.txt` quando a escrita termina sem erro; se o cardápio ou o
histórico não puder ser gravado, a alteração é desfeita e uma mensagem de erro
aparece. Se o `cardapio.txt` estiver corrompido, o programa avisa e encerra sem
sobrescrevê-lo: corrija ou apague o arquivo.

Usuários disponíveis no acesso interno:

| Login       | Senha    | Perfil                          |
|-------------|----------|---------------------------------|
| `admin`     | admin123 | Administrador                   |
| `jardins`   | 1234     | Gerente da filial Jardins       |
| `itaim`     | 1234     | Gerente da filial Itaim Bibi    |
| `pinheiros` | 1234     | Gerente da filial Pinheiros     |

> **Atenção — apenas para a simulação acadêmica:** essas credenciais estão
> fixas no código e em texto puro de propósito, para que a simulação rode sem
> banco de dados. Não as reutilize em nenhum outro lugar. Na implementação
> prevista para produção, nenhuma senha fica no código: os usuários ficam na
> tabela `usuario` e a senha é guardada só como hash bcrypt (coluna
> `senha_hash` em `database/modelo_fisico_mysql.sql`, RNF04). A comparação
> completa entre simulação e produção está na seção 6.7 do relatório.

### Alternativa sem instalar nada

Copie o conteúdo de `src/simulacao_cardapio.c` para um compilador online, como o
[OnlineGDB](https://www.onlinegdb.com/online_c_compiler), e clique em **Run**.

## Testes e evidências de funcionamento

Os scripts de `tests/` executam o programa e o banco de verdade e gravam as
evidências em `docs/evidencias/` (requerem Python com `Pillow`):

```bash
python tests/executar_testes_c.py     # 15 casos da simulação (requer tcc)
python tests/executar_testes_sql.py   # MySQL 8.0 em contêiner Docker descartável
python docs/scripts/evidencias_docx.py  # leva os resultados para o relatório
```

- `executar_testes_c.py` compila o `.c` com o TCC, roda os casos de
  `tests/casos_simulacao.py` em sequência (o estado dos `.txt` passa de um caso
  para o outro), confere a saída e gera um print de terminal por caso.
- `executar_testes_sql.py` sobe um contêiner `mysql:8.0` temporário, roda o
  modelo físico e os testes, e o remove ao final. O `DROP DATABASE` do script só
  atinge esse contêiner. Requer o Docker em execução.
- Os dois scripts terminam com código 1 se algum teste falhar.

### Problemas comuns

- **`tcc: command not found`** ou **"tcc não é reconhecido"**: o terminal foi
  aberto antes da alteração do PATH. Reabra o terminal; no VS Code, reabra o
  VS Code. No Git Bash, rode `source ~/.bashrc`.
- **"Valor invalido" na primeira opção ao enviar entradas por pipe no
  PowerShell**: o PowerShell insere um caractere invisível (BOM) no início do
  texto. Digite as opções manualmente ou use o Git Bash.
