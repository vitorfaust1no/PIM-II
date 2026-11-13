"""Executa o modelo fisico e os testes SQL num MySQL 8.0 descartavel (Docker).

1. Sobe um conteiner mysql:8.0 temporario (--rm), sem porta exposta.
2. Roda database/modelo_fisico_mysql.sql e depois database/testes_modelo_fisico.sql
   (este com --force, porque os testes negativos devem dar erro), com o cliente
   mysql em modo -vvv: cada comando e ecoado junto com o resultado.
3. Para o conteiner (que e apagado) e grava em docs/evidencias/sql/:
   - modelo_fisico.log / testes.log  saida completa do cliente mysql
   - SQL_*.png                       prints do terminal
   - resumo.json / resumo.txt        resultado de cada teste (PASSOU/FALHOU)
Nada e executado contra bancos reais: o DROP DATABASE do script so atinge o
conteiner temporario.
Uso:  python tests/executar_testes_sql.py      (requer Docker em execucao)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
MODELO = RAIZ / "database" / "modelo_fisico_mysql.sql"
TESTES = RAIZ / "database" / "testes_modelo_fisico.sql"
SAIDA = RAIZ / "docs" / "evidencias" / "sql"

IMAGEM = "mysql:8.0"
CONTEINER = "pim2-mysql-teste"
SENHA = "pim2teste"  # senha descartavel de um conteiner temporario e isolado

sys.path.insert(0, str(AQUI))
from renderizar_terminal import (paginar_blocos, renderizar_paginado,  # noqa: E402
                                 texto_para_linhas)

# id -> (descricao, resultado esperado, regex que comprova no trecho do teste)
CHECAGENS = {
    "ST01": ("Estrutura: tabelas e triggers criados",
             "11 tabelas e 3 triggers",
             [r"\|\s+11 \|", r"trg_harmonizacao_valida_ins", r"trg_harmonizacao_valida_upd",
              r"trg_historico_pendente"]),
    "ST02": ("Carga de exemplo",
             "3 filiais, 3 usuários, 5 produtos, 15 disponibilidades",
             [r"\|\s+3 \|\s+3 \|\s+5 \|\s+7 \|\s+15 \|"]),
    "ST03": ("Transação RF06/RF11 do script",
             "Risoto inativo só na filial 1 e evento DESATIVAR no histórico",
             [r"\|\s+1 \| Risoto de cogumelos \|\s+0 \|", r"\|\s+2 \| Risoto de cogumelos \|\s+1 \|",
              r"\|\s+2 \|\s+1 \|\s+2 \| DESATIVAR \|"]),
    "ST04": ("Repetição da desativação",
             "0 linhas alteradas e nenhum evento novo",
             [r"\|\s+0 \|\s+0 \|"]),
    "ST05": ("ROLLBACK",
             "Valor alterado dentro da transação e restaurado após o ROLLBACK",
             [r"dentro_da_transacao[\s\S]*?\|\s+0 \|", r"apos_rollback[\s\S]*?\|\s+1 \|"]),
    "ST06": ("CHECK de preço (preço 0)",
             "Recusado: erro 3819 ck_produto_preco",
             [r"ERROR 3819 .*ck_produto_preco"]),
    "ST07": ("CHECK de perfil (gerente sem filial; admin com filial)",
             "Ambos recusados: erro 3819 ck_usuario_perfil",
             [r"ERROR 3819 .*ck_usuario_perfil[\s\S]*ERROR 3819 .*ck_usuario_perfil"]),
    "ST08": ("Triggers de harmonização (inclusão e alteração)",
             "Ambas recusadas: erro 1644 da trigger",
             [r"ERROR 1644 .*Harmonizacao deve ligar[\s\S]*ERROR 1644 .*Harmonizacao deve ligar"]),
    "ST09": ("Chave estrangeira (produto inexistente)",
             "Recusado: erro 1452",
             [r"ERROR 1452 .*fk_disp_produto"]),
    "ST10": ("UNIQUE de e-mail",
             "Recusado: erro 1062",
             [r"ERROR 1062 .*Duplicate entry 'bruno@saborecia\.com\.br'"]),
    "ST11": ("Exclusão de produto com histórico",
             "Recusado: erro 1451 (histórico preservado)",
             [r"ERROR 1451 .*fk_hist_produto"]),
    "ST12": ("Dados intactos após os testes negativos",
             "5 produtos, 3 usuários, 2 harmonizações, 15 disponibilidades",
             [r"\|\s+5 \|\s+3 \|\s+2 \|\s+15 \|"]),
    "ST13": ("Caixa de saída da replicação (trigger de pendência)",
             "Todo evento pendente; ROLLBACK sem evento nem pendência; COMMIT com pendência",
             # cada regex fica presa a linha de dados logo abaixo do proprio cabecalho
             # (senao uma linha de outro passo com numeros iguais poderia casar)
             [r"\| eventos \| pendentes \|\n\+[-+]+\+\n\|\s+(\d+) \|\s+\1 \|",
              # (b) nao e vazio: antes do ROLLBACK havia 1 linha alterada e 1 pendencia
              r"\| dentro_linhas_alteradas \| dentro_pendencias \|\n\+[-+]+\+\n"
              r"\|\s+1 \|\s+1 \|",
              r"\| pendencias_apos_rollback \| ativo_apos_rollback \|\n\+[-+]+\+\n"
              r"\|\s+0 \|\s+1 \|",
              r"\| linhas_alteradas \| pendencia_do_novo_evento \|\n\+[-+]+\+\n"
              r"\|\s+1 \|\s+1 \|"]),
}


# testes que DEVEM terminar em erro; em qualquer outro, um ERROR no trecho e falha
NEGATIVOS = {"ST06", "ST07", "ST08", "ST09", "ST10", "ST11"}


def docker(*args, entrada: str | None = None, verificar: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], input=entrada, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=verificar)


def mysql(script: Path, forcar: bool = False) -> tuple[int, str]:
    opcoes = "--default-character-set=utf8mb4 --table -vvv --unbuffered"
    if forcar:  # so no arquivo de testes; --comments quebraria o DELIMITER do modelo
        opcoes += " --force --comments"
    proc = docker("exec", "-i", "-e", f"MYSQL_PWD={SENHA}", CONTEINER,
                  "sh", "-c", f"mysql -uroot {opcoes} 2>&1",
                  entrada=script.read_text(encoding="utf-8"), verificar=False)
    return proc.returncode, proc.stdout.replace("\r\n", "\n")


def aguardar_mysql(limite: int = 180) -> None:
    """Espera o servidor DEFINITIVO. Na inicializacao, a imagem sobe antes um servidor
    provisorio so com socket (--skip-networking) e depois o derruba; testando por TCP,
    so o servidor definitivo responde."""
    inicio = time.time()
    while time.time() - inicio < limite:
        p = docker("exec", "-e", f"MYSQL_PWD={SENHA}", CONTEINER,
                   "mysql", "-uroot", "-h127.0.0.1", "--protocol=TCP",
                   "-e", "SELECT 1", verificar=False)
        if p.returncode == 0:
            return
        time.sleep(2)
    raise RuntimeError("MySQL nao ficou pronto a tempo.")


def blocos_por_comando(log: str) -> list[str]:
    """Divide a saida -vvv em blocos 'comando + resultado'."""
    partes = re.split(r"(?m)^(?=--------------\n(?!\n))", log)
    return [b for b in partes if b.strip()]


def secoes_dos_testes(log: str) -> dict[str, str]:
    """Separa o log dos testes pelo comentario '-- STnn ...' que abre cada teste."""
    marcas = [(m.start(), m.group(1)) for m in
              re.finditer(r"(?m)^--------------\n-- (ST\d\d)", log)]
    secoes = {}
    for k, (ini, tid) in enumerate(marcas):
        fim = marcas[k + 1][0] if k + 1 < len(marcas) else len(log)
        secoes[tid] = log[ini:fim]
    return secoes


def executar() -> int:
    if shutil.which("docker") is None:
        sys.exit("docker nao encontrado no PATH.")
    docker("rm", "-f", CONTEINER, verificar=False)
    print(f"Subindo {IMAGEM} (conteiner temporario {CONTEINER})...")
    docker("run", "-d", "--rm", "--name", CONTEINER, "-e", f"MYSQL_ROOT_PASSWORD={SENHA}", IMAGEM)
    try:
        aguardar_mysql()
        versao = docker("exec", "-e", f"MYSQL_PWD={SENHA}", CONTEINER, "mysql", "-uroot",
                        "-N", "-e", "SELECT VERSION()").stdout.strip()
        print("MySQL", versao)
        cod_modelo, log_modelo = mysql(MODELO)
        cod_testes, log_testes = mysql(TESTES, forcar=True)
    finally:
        docker("stop", CONTEINER, verificar=False)
        print("Conteiner parado e removido.")

    # tudo e gerado em sql.novo/ e so substitui a pasta anterior no final
    novo = SAIDA.with_name(SAIDA.name + ".novo")
    if novo.exists():
        shutil.rmtree(novo)
    novo.mkdir(parents=True)
    (novo / "modelo_fisico.log").write_text(log_modelo, encoding="utf-8")
    (novo / "testes.log").write_text(log_testes, encoding="utf-8")

    # --- verificacao -----------------------------------------------------
    erros_modelo = re.findall(r"(?m)^ERROR .*$", log_modelo)
    comandos_ok = len(re.findall(r"(?m)^(Query OK|\d+ rows? in set|Empty set)", log_modelo))
    resultados = [{
        "id": "ST00", "descricao": "Execução completa de modelo_fisico_mysql.sql",
        "esperado": "Todos os comandos executados sem erro",
        "obtido": f"{comandos_ok} comandos executados, {len(erros_modelo)} erros",
        "status": "PASSOU" if cod_modelo == 0 and not erros_modelo else "FALHOU",
    }]
    secoes = secoes_dos_testes(log_testes)
    for tid, (desc, esperado, regexes) in CHECAGENS.items():
        trecho = secoes.get(tid, "")
        ok = bool(trecho) and all(re.search(rx, trecho) for rx in regexes)
        # testes positivos nao podem ter erro algum
        if ok and tid not in NEGATIVOS and re.search(r"(?m)^ERROR", trecho):
            ok = False
        resultados.append({"id": tid, "descricao": desc, "esperado": esperado,
                           "status": "PASSOU" if ok else "FALHOU"})
    for r in resultados:
        print(f"[{r['status']}] {r['id']} {r['descricao']}")

    # --- prints ------------------------------------------------------------
    cmd_modelo = (f"C:\\PIM-II> docker exec -i {CONTEINER} mysql -uroot --table -vvv "
                  "< database\\modelo_fisico_mysql.sql")
    cmd_testes = (f"C:\\PIM-II> docker exec -i {CONTEINER} mysql -uroot --table -vvv --force "
                  "--comments < database\\testes_modelo_fisico.sql")
    imagens = {}

    # (a) inicio do script: criacao do banco e das primeiras tabelas
    blocos = blocos_por_comando(log_modelo)
    inicio = ([texto_para_linhas(cmd_modelo)] + [texto_para_linhas(b) for b in blocos[:6]]
              + [texto_para_linhas("...")])
    pags = paginar_blocos(inicio)[:1]
    imagens["SQL_01_criacao"] = renderizar_paginado(
        [], "MySQL " + versao + " - criacao do banco e das tabelas", novo / "SQL_01_criacao", pags)

    # (b) comandos principais: transacao RF06/RF11 e consultas RF07-RF12. Se o script
    # mudou ou parou antes desse ponto, mostra o que veio depois da criacao das tabelas
    # (o ST00 ja registra a falha), em vez de abortar.
    i0 = next((k for k, b in enumerate(blocos)
               if b.startswith("--------------\nSET @usuario")), None)
    if i0 is None:
        print("Aviso: bloco 'SET @usuario' nao encontrado no log do modelo.")
        i0 = min(6, len(blocos))
    principais = [texto_para_linhas("...")] + [texto_para_linhas(b) for b in blocos[i0:]]
    pags = paginar_blocos(principais)
    imagens["SQL_02_comandos"] = renderizar_paginado(
        [], "MySQL " + versao + " - transacao e consultas do sistema",
        novo / "SQL_02_comandos", pags)

    # (c) testes: um conjunto de blocos por teste
    if not secoes:
        print("Aviso: nenhuma marca '-- STnn' no log dos testes (--comments ignorado?).")
    ids = sorted(secoes)
    tblocos = [texto_para_linhas(cmd_testes)] + [texto_para_linhas(secoes[t]) for t in ids]
    pags, rot_pags = paginar_blocos(tblocos, rotulos=[None] + ids)
    imagens["SQL_03_testes"] = renderizar_paginado(
        [], "MySQL " + versao + " - testes do modelo fisico", novo / "SQL_03_testes", pags)

    passou = sum(r["status"] == "PASSOU" for r in resultados)
    resumo = {"mysql": versao, "total": len(resultados), "passou": passou,
              "testes": resultados,
              "imagens": {k: [p.name for p in v] for k, v in imagens.items()},
              "testes_por_imagem": [[t for t in r if t] for r in rot_pags]}
    (novo / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    txt = [f"{r['id']}  [{r['status']}]  {r['descricao']}" for r in resultados]
    txt.append(f"\n{passou} de {len(resultados)} testes passaram (MySQL {versao}).")
    (novo / "resumo.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    novo.rename(SAIDA)
    print(f"\n{passou} de {len(resultados)} testes passaram. Evidencias em {SAIDA}")
    return 0 if passou == len(resultados) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.chdir(RAIZ)
    sys.exit(executar())
