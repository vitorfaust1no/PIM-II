"""Aplica no relatorio as correcoes apontadas pelo avaliador.

1. Arquitetura de replicacao coerente com a secao 5.4 (caixa de saida transacional):
   - secao 7.1: a copia para o MongoDB e feita pelo servico de replicacao, nao por
     uma fila de mensagens;
   - secao 4.5 e Figura "Arquitetura do sistema": o servico de replicacao aparece na
     camada de aplicacao e a API nao grava direto no MongoDB.
2. Modelos conceitual e logico completos (secoes 5.1 e 5.2 e Figuras 5 e 6): incluem
   historico_disponibilidade e dispositivo; a secao 5.3 explica a tabela dispositivo.
3. Limite de paginas do desenvolvimento: a secao 5.6 deixa de repetir as listagens
   SQL, que ja estao no Apendice B, e passa a descreve-las em prosa; os cenarios de
   falha da 5.4 viram um so paragrafo; o capitulo 9 e enxugado; e a Figura 4 fica
   (arquitetura) volta a ter 16 cm.

As figuras vem de diagramas/sem_titulo/ (fontes .puml/.dot em diagramas/).
Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-avaliador.docx na
primeira execucao.
Uso:  python docs/scripts/correcoes_avaliador_docx.py
"""

from __future__ import annotations

import io
import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.shared import Cm
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ajustar_figuras import localizar_figura  # noqa: E402
from evidencias_docx import achar, substituir_regex  # noqa: E402
from escopo_gravacao_docx import TEXTO_91, TEXTO_91_ANTIGO  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-avaliador.docx"
FIGS = DOCS.parent / "diagramas" / "sem_titulo"

# (inicio do texto atual, trecho antigo, trecho novo)
TROCAS = [
    # 4.5: servico de replicacao na camada de aplicacao
    ("A arquitetura da solução organiza-se em três camadas",
     "responsável por autenticação, cardápio, disponibilidade e relatórios; e a camada",
     "responsável por autenticação, cardápio, disponibilidade e relatórios, e o serviço de "
     "replicação que copia o histórico do MySQL para o MongoDB (seção 5.4); e a camada"),
    # 5.1: entidades Dispositivo e Historico de disponibilidade
    ("O modelo conceitual, em notação entidade-relacionamento",
     "As entidades são Filial, Usuário, Categoria, Produto e Alérgeno.",
     "As entidades são Filial, Usuário, Dispositivo, Categoria, Produto, Alérgeno e Histórico "
     "de disponibilidade."),
    ("O modelo conceitual, em notação entidade-relacionamento",
     "uma Filial é gerenciada por um ou mais Usuários.",
     "uma Filial é gerenciada por um ou mais Usuários e possui zero ou mais Dispositivos, as "
     "maquininhas dos garçons. Cada registro de Histórico de disponibilidade refere-se a um "
     "único Produto, ocorre em uma única Filial e é realizado por um único Usuário, guardando a "
     "ação (ativar ou desativar) e a data e hora; é essa entidade que garante a rastreabilidade "
     "das alterações e alimenta os relatórios da matriz."),
    # 5.2: tabelas historico_disponibilidade e dispositivo
    ("No modelo lógico, os relacionamentos N:N foram resolvidos",
     "Cada tabela recebeu chave primária e as chaves estrangeiras correspondentes.",
     "O histórico tornou-se a tabela historico_disponibilidade, com chave primária própria "
     "(id_historico) e três chaves estrangeiras, para produto, filial e usuário; por ser um "
     "registro de eventos, nela apenas se inserem linhas, e ela também serve de caixa de saída "
     "para a replicação descrita na seção 5.4. O dispositivo tornou-se a tabela dispositivo, "
     "ligada à filial por chave estrangeira. Cada tabela recebeu chave primária e as chaves "
     "estrangeiras correspondentes."),
    # 5.3: por que a tabela dispositivo existe
    ("O modelo físico foi implementado no script",
     "A tabela dispositivo guarda o token de acesso das maquininhas (RF10), armazenado como hash.",
     "A tabela dispositivo existe porque a maquininha não é operada por um usuário com login: "
     "ela se identifica na API por um token próprio (RF10), e a filial cujo cardápio deve ser "
     "exibido é obtida do dispositivo. O token é guardado somente como hash SHA-256 (coluna "
     "token_hash), para que um vazamento da tabela não exponha credenciais válidas, e a coluna "
     "ativo permite bloquear uma maquininha extraviada sem apagar o seu cadastro."),
    # cap. 9: textos mais curtos (limite de paginas)
    ("A integração da solução articula os resultados",
     "A integração da solução articula os resultados das disciplinas em um único fluxo "
     "coerente, do problema de negócio até a entrega técnica. Este capítulo descreve a visão "
     "integrada do sistema e como cada componente se conecta aos demais.",
     "Este capítulo mostra como componentes e disciplinas formam uma única solução."),
    ("A engenharia de software definiu os requisitos",
     ("A engenharia de software definiu os requisitos e a modelagem que orientaram todo o "
     "projeto; a modelagem de banco de dados transformou esse domínio em um esquema íntegro e "
     "consultável; a programação estruturada validou, em C, a lógica central de "
     "disponibilidade que a API exporia em produção; as redes e os sistemas distribuídos "
     "proveem a infraestrutura que entrega essa lógica de forma segura e disponível às unidades "
     "e aos clientes; e a análise de direitos humanos, inclusão e segurança assegura que a "
     "entrega seja acessível, inclusiva e conforme a LGPD. Cada disciplina resolve uma camada "
     "do mesmo problema.",
     "Cada disciplina resolve uma camada do mesmo problema: a engenharia de software definiu os "
     "requisitos e a modelagem; o banco de dados transformou o domínio em um esquema íntegro; a "
     "programação estruturada validou em C a lógica central de disponibilidade; as redes e os "
     "sistemas distribuídos entregam essa lógica de forma segura às unidades e aos clientes; e "
     "a análise de direitos humanos garante uma entrega acessível, inclusiva e conforme a LGPD.",
     "Cada disciplina resolve uma camada do problema: a engenharia de software definiu os "
     "requisitos e a modelagem; o banco de dados, um esquema íntegro; a programação estruturada "
     "validou a lógica central em C; as redes levam essa lógica com segurança às unidades e aos "
     "clientes; e a análise de direitos humanos garante acessibilidade, inclusão e conformidade "
     "com a LGPD.",
     ),
     # versao atual: escopo_gravacao_docx.py (rede no futuro; direitos humanos orientam)
     "Cada disciplina resolve uma camada do problema: a engenharia de software definiu os "
     "requisitos e a modelagem; o banco de dados, um esquema íntegro; a programação estruturada "
     "validou a lógica central em C; as redes levarão essa lógica com segurança às unidades e aos "
     "clientes; e a análise de direitos humanos orienta acessibilidade, inclusão e conformidade "
     "com a LGPD."),
    ("A simulação em C representa, de forma concentrada",
     ("A simulação em C representa, de forma concentrada, as regras que no sistema real "
     "residiriam na camada de aplicação: autenticação, controle de disponibilidade por filial, "
     "exibição filtrada e histórico. A evolução para produção substituiria os arquivos texto "
     "pelos bancos MySQL e MongoDB, exporia as funções como endpoints da API REST, "
     "acrescentaria o front-end HTML acessível e a integração com as maquininhas e implantaria "
     "o conjunto na arquitetura em nuvem descrita no capítulo 7, preservando os requisitos não "
     "funcionais de desempenho, segurança e acessibilidade.",
     "A simulação em C concentra as regras que, no sistema real, ficariam na camada de "
     "aplicação: autenticação, disponibilidade por filial, exibição filtrada e histórico. Em "
     "produção, os arquivos texto dariam lugar ao MySQL e ao MongoDB, as funções seriam "
     "expostas como endpoints da API REST e o conjunto, com o front-end acessível e a "
     "integração com as maquininhas, seria implantado na nuvem descrita no capítulo 7.",
     ),
     "Em produção, as regras da simulação em C (autenticação, disponibilidade por filial, "
     "exibição filtrada e histórico) passariam à API REST, com o MySQL e o MongoDB no lugar dos "
     "arquivos texto, o front-end acessível, a integração com as maquininhas e a implantação "
     "na nuvem descrita no capítulo 7."),
    ("O cliente acessa, por QR code",
     ("O cliente acessa, por QR code, o cardápio público da filial; a página, em HTML acessível, "
     "consulta a API REST, que retorna apenas os produtos ativos naquela unidade, com seus "
     "alérgenos e no idioma escolhido. Quando um prato se esgota, o gerente faz login no painel "
     "e altera a disponibilidade da sua filial; a API grava a mudança no banco relacional e "
     "registra o evento no histórico, propagando o novo estado ao cardápio do cliente e às "
     "maquininhas dos garçons em até 30 segundos." " Assim, o que o cliente vê, o que o garçom oferece e o que a matriz acompanha "
     "permanecem sincronizados.",
      "O cliente acessa, por QR code, o cardápio público da filial, que consulta a API REST e "
      "exibe apenas os produtos ativos naquela unidade, com os alérgenos e no idioma escolhido. "
      "Quando um prato se esgota, o gerente altera a disponibilidade da sua filial no painel; a "
      "API grava a mudança e o evento de histórico no MySQL e propaga o novo estado ao cardápio "
      "e às maquininhas em até 30 segundos." " Assim, o que o cliente vê, o que o garçom oferece e o que a matriz acompanha "
     "permanecem sincronizados.",
      "O cliente acessa, por QR code, o cardápio público da filial, que consulta a API REST e "
      "exibe apenas os produtos ativos naquela unidade, com os alérgenos e no idioma escolhido. "
      "Quando um prato se esgota, o gerente altera a disponibilidade da sua filial no painel; a "
      "API grava a mudança e o evento de histórico no MySQL e propaga o novo estado ao cardápio "
      "e às maquininhas dos garçons em até 30 segundos.",
      TEXTO_91_ANTIGO,
      ),
     TEXTO_91),  # versao atual: escopo_gravacao_docx.py (solucao no futuro)
    ("Entre os benefícios esperados",
     ("Entre os benefícios esperados para a organização estão a redução de pedidos frustrados "
     "por itens esgotados, a melhor experiência e a maior autonomia do cliente, a padronização "
     "da informação entre unidades e a visão consolidada da matriz sobre o que esgota em cada "
     "filial. Como limitações, a validação restringiu-se à simulação em console da lógica "
     "central, com dados fictícios, sem a API, o front-end e as maquininhas em funcionamento — "
     "pontos discutidos na seção 9.3 e na conclusão.",
     "Entre os benefícios esperados estão menos pedidos frustrados por itens esgotados, mais "
     "autonomia para o cliente, informação padronizada entre as unidades e a visão consolidada "
     "da matriz sobre o que esgota em cada filial. Como limitação, a validação restringiu-se à "
     "simulação em console da lógica central, com dados fictícios, sem a API, o front-end e as "
     "maquininhas em funcionamento.",
     ),
     "Entre os benefícios esperados estão menos pedidos frustrados por itens esgotados, mais "
     "autonomia para o cliente, informação padronizada entre as unidades e a visão consolidada "
     "da matriz sobre o que esgota em cada filial. Como limitação, a validação ficou restrita à "
     "simulação em console, com dados fictícios."),
    # 7.1: sem fila de mensagens
    ("A comunicação entre os serviços segue padrões abertos.",
     "Além do registro transacional no MySQL, cada alteração é publicada em uma fila de "
     "mensagens, e um consumidor a replica no MongoDB do histórico, sem atrasar a resposta ao "
     "gerente.",
     "A API grava cada alteração apenas no MySQL, na mesma transação que registra o histórico; "
     "a cópia para o MongoDB é feita depois, de forma assíncrona, pelo serviço de replicação "
     "descrito na seção 5.4, sem atrasar a resposta ao gerente."),
]

INICIO_56 = "A seguir destacam-se comandos SQL"
NOVO_56 = (
    "Os comandos SQL (Structured Query Language) mais representativos do modelo físico estão "
    "no script do Apêndice B. A criação das tabelas declara as restrições junto com as colunas, "
    "como na tabela produto, que tem chave estrangeira para categoria e uma restrição CHECK que "
    "exige preço maior que zero. A alteração de disponibilidade (RF06 e RF11) é uma transação: "
    "entre START TRANSACTION e COMMIT, um UPDATE muda o campo ativo da tabela disponibilidade, "
    "restrito à filial do gerente autenticado, e um INSERT registra o evento em "
    "historico_disponibilidade. A consulta do cardápio ativo de uma filial (RF07) junta produto, "
    "categoria e disponibilidade, filtra os itens ativos da unidade e ordena o resultado pela "
    "ordem de exibição da categoria. Esses comandos foram executados nos testes da seção 5.7.")

INICIO_54 = "Os principais cenários de falha"
NOVO_54 = (
    "Nos cenários de falha, o MySQL é a referência para a recuperação. Se o MongoDB estiver "
    "indisponível, o ponto de controle não avança e o serviço tenta de novo com espera "
    "exponencial, sem perda de eventos; se o próprio serviço falhar entre gravar no MongoDB e "
    "avançar o ponto de controle, o lote é reprocessado e os eventos repetidos são rejeitados "
    "pela chave _id; e uma transação revertida não gera registro de histórico, logo não há o "
    "que replicar. Uma conciliação diária compara as contagens de eventos por filial e por dia "
    "nos dois bancos e reenvia os que faltarem, e a defasagem da réplica é monitorada com "
    "alerta; esse atraso afeta apenas os relatórios analíticos, pois o cardápio e as "
    "maquininhas leem o MySQL (RNF01).")

# (inicio da legenda, arquivo, largura em cm)
FIGURAS = [
    ("Arquitetura do sistema", "01_arquitetura.png", 16.0),
    ("Modelo conceitual", "05_conceitual.png", 16.0),
    ("Modelo lógico", "06_logico.png", 16.0),
]


def aplicar_trocas(doc) -> int:
    """`antigo` pode ser uma tupla com versoes anteriores do trecho (o texto foi
    enxugado mais de uma vez); qualquer uma delas e trocada por `novo`."""
    feitas = 0
    for inicio, antigo, novo in TROCAS:
        if any(novo in q.text for q in doc.paragraphs):
            continue  # ja aplicada (o inicio do paragrafo pode ter mudado)
        antigos = antigo if isinstance(antigo, tuple) else (antigo,)
        achados = [(q, a) for q in doc.paragraphs for a in antigos if a in q.text]
        if len(achados) != 1:
            raise SystemExit(f"trecho de '{inicio}' casou {len(achados)} vezes")
        q, a = achados[0]
        substituir_regex(q._p, re.escape(a), lambda m, t=novo: t)  # texto literal
        feitas += 1
    return feitas


def enxugar_56(doc) -> int:
    """Troca a introducao da 5.6 pela versao em prosa e remove as listagens."""
    P = doc.paragraphs
    try:
        i = next(k for k, p in enumerate(P) if p.text.startswith(INICIO_56))
    except StopIteration:
        return 0
    removidos = 0
    for p in P[i + 1:]:
        if p.style.name.startswith("Heading"):
            break
        fontes = {r.font.name for r in p.runs if r.text.strip()}
        if fontes and fontes != {"Consolas"}:
            raise SystemExit(f"paragrafo inesperado na 5.6: {p.text[:60]}")
        p._p.getparent().remove(p._p)
        removidos += 1
    intro = P[i]
    for r in intro.runs[1:]:
        r._r.getparent().remove(r._r)
    intro.runs[0].text = NOVO_56
    return removidos


def condensar_54(doc) -> int:
    """Junta a introducao e os itens a) a e) dos cenarios de falha em um paragrafo."""
    P = doc.paragraphs
    try:
        i = next(k for k, p in enumerate(P) if p.text.startswith(INICIO_54))
    except StopIteration:
        return 0
    removidos = 0
    for p in P[i + 1:]:
        if not p.text[:3] in ("a) ", "b) ", "c) ", "d) ", "e) "):
            break
        p._p.getparent().remove(p._p)
        removidos += 1
    if removidos != 5:
        raise SystemExit(f"esperava 5 itens de falha na 5.4, achei {removidos}")
    intro = P[i]
    for r in intro.runs[1:]:
        r._r.getparent().remove(r._r)
    intro.runs[0].text = NOVO_54
    return removidos


def trocar_figuras(doc) -> None:
    for titulo, arquivo, largura in FIGURAS:
        forma = localizar_figura(doc, titulo)
        img = Image.open(FIGS / arquivo)
        buf = io.BytesIO()
        img.save(buf, format="PNG", dpi=(300, 300))
        rid = forma._inline.graphic.graphicData.pic.blipFill.blip.embed
        doc.part.related_parts[rid]._blob = buf.getvalue()
        forma.width = Cm(largura)
        forma.height = Cm(largura * img.height / img.width)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    doc = Document(ALVO)
    trocas = aplicar_trocas(doc)
    linhas_56 = enxugar_56(doc)
    itens_54 = condensar_54(doc)
    trocar_figuras(doc)
    doc.save(ALVO)
    print(f"trechos alterados={trocas} linhas SQL removidas da 5.6={linhas_56} "
          f"itens de falha condensados na 5.4={itens_54} "
          f"figuras atualizadas={len(FIGURAS)}")


if __name__ == "__main__":
    main()
