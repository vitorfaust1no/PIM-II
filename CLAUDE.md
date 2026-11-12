# CLAUDE.md — PIM II Sabor & Cia

Trabalho acadêmico (PIM II, ADS) sobre a empresa fictícia **Sabor & Cia Bistrô**. O
entregável principal é o **relatório** `docs/PIM_II_Sabor_e_Cia.docx` (+ `.pdf`). O código
em C, o SQL, o pseudocódigo e os diagramas existem para alimentar o relatório e o vídeo.
Idioma do projeto: português (pt-BR), em código, commits e conversa.

## Mapa
- `src/simulacao_cardapio.c` — simulação de console (Apêndice A do relatório).
- `database/modelo_fisico_mysql.sql` — modelo físico MySQL (Apêndice B). Contém
  `DROP DATABASE IF EXISTS sabor_cia;`: nunca execute contra um banco real sem avisar.
- `docs/pseudocodigo_funcionalidades.txt` — Apêndice C.
- `tests/` — testes que geram as evidências do relatório: `executar_testes_c.py` (casos em
  `casos_simulacao.py`) e `executar_testes_sql.py` (MySQL 8.0 em Docker descartável, roda
  `database/testes_modelo_fisico.sql`). Saídas em `docs/evidencias/` (PNG, logs, `resumo.json`),
  que `docs/scripts/evidencias_docx.py` leva às seções 5.7/6.8 e ao Apêndice D.
- `docs/scripts/` — scripts `python-docx` que editam o relatório (revisão, ABNT, figuras,
  seção 6.7 de segurança).
- `diagramas/` — PNGs originais + fontes `.drawio`/`.iuml`; `diagramas/sem_titulo/` são os
  PNGs recortados (sem faixa de título) que de fato entram no `.docx`.
- `apresentacao/` — pipeline do vídeo narrado (`build.py` orquestra, `roteiro.py` tem o texto
  dos segmentos, `slides.py` renderiza com Pillow). `apresentacao/build/` é descartável.
- `graphify-out/` — grafo de conhecimento gerado pelo graphify; não editar à mão.

## Regras importantes
- **Apêndices sincronizados:** ao mudar `src/simulacao_cardapio.c` ou o SQL, o texto do
  Apêndice A/B dentro do `.docx` fica desatualizado. Atualize o relatório (ex.:
  `python docs/scripts/seguranca_simulacao_docx.py` faz o diff do C para o Apêndice A) e
  avise que o `.pdf` precisa ser reexportado pelo Word. Rode também os testes de `tests/`:
  as evidências (Quadros 3 e 4, Apêndice D) refletem a versão testada.
- **C:** mantenha compatível com TCC 0.9.27 e MSVC (`.vscode/tasks.json`); C simples, estilo
  didático, comentários em português. Strings exibidas **sem acento** (console do Windows).
- **Segurança da simulação:** as credenciais fixas em texto puro são intencionais e
  documentadas (README, cabeçalho do `.c`, seção 6.7). Não "corrija" para hash; produção usa
  bcrypt em `usuario.senha_hash` (RNF04).
- **Scripts do `.docx`:** são idempotentes e alguns criam backup `*.pre-*.docx` ao lado do
  relatório. Backups ficam em `docs/_backups/` e são ignorados pelo git — não commitar.
  Rode-os da raiz: `python docs/scripts/<script>.py`. Feche o `.docx` no Word antes.
- **Relatório segue ABNT:** texto justificado, recuo de 1,5 cm (Manual do PIM; sobrepõe o 1,25 cm da ABNT — não "corrija"; constante
  `RECUO_ABNT` em `docs/scripts/reparar_docx.py`), legendas "Figura n – ..."
  com fonte, referências alinhadas à esquerda. Preserve isso ao editar.
- **Narração do vídeo (`roteiro.py`):** escreva siglas como devem ser lidas pelo TTS
  (ex.: "vê-lan") e evite jargão que a voz pronuncia mal.

## Comandos
- Rodar a simulação: `tcc -run src/simulacao_cardapio.c` (gera `cardapio.txt`/`historico.txt`
  no diretório atual; apague-os para resetar). Usuários: `admin/admin123`, `jardins|itaim|pinheiros/1234`.
- Gerar o vídeo: `python apresentacao/build.py` — requer `tcc`, `ffmpeg`/`ffprobe` no PATH,
  `edge-tts` e `Pillow` (fallback de voz: SAPI/Microsoft Maria). Demora; sobrescreve o MP4.
- `gcc` não está instalado nesta máquina; use `tcc`.

## Git
- Branch única `main`, remoto `github.com/vitorfaust1no/PIM-II`.
- Identidade e credencial (`gh auth git-credential`, conta `vitorfaust1no`) configuradas
  **só neste repo** em `.git/config`; a credencial global do Windows é de outra conta.
- Commits pequenos e temáticos, mensagem em português no estilo `tipo(escopo): descricao`
  (ex.: `docs(relatorio): ...`, `fix(db): ...`). Adicione arquivos por caminho, nunca `git add -A`.
- Binários versionados: `.docx`, `.pdf`, `.mp4` (~22 MB). Não versionar backups nem `build/`.
