"""Executa os casos de teste da simulacao em C e gera as evidencias.

1. Compila src/simulacao_cardapio.c com o TCC num diretorio temporario.
2. Roda cada caso de tests/casos_simulacao.py, em sequencia e no mesmo
   diretorio de trabalho (cada caso e uma execucao nova do programa).
3. Confere a saida (PASSOU/FALHOU) e grava em docs/evidencias/c/:
   - CTnn.txt  transcricao da sessao (com o que foi digitado)
   - CTnn.png  print do terminal (ou CTnn_p1.png, CTnn_p2.png...)
   - resumo.json e resumo.txt
   Tudo e gerado primeiro em docs/evidencias/c.novo/ e so substitui a pasta
   anterior no final, para que uma falha no meio nao apague as evidencias.
Uso:  python tests/executar_testes_c.py      (codigo de saida 1 se algum falhar)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
FONTE_C = RAIZ / "src" / "simulacao_cardapio.c"
SAIDA = RAIZ / "docs" / "evidencias" / "c"
TEMPO_LIMITE = 30  # segundos por execucao

sys.path.insert(0, str(AQUI))
from casos_simulacao import CASOS  # noqa: E402
from renderizar_terminal import renderizar_paginado  # noqa: E402
from sessao_console import como_linhas, intercalar  # noqa: E402


def rodar(exe: Path, entrada: str, cwd: Path) -> tuple[str, int | None]:
    """Executa o programa; devolve (saida, codigo). codigo None = tempo esgotado."""
    try:
        proc = subprocess.run([str(exe)], input=entrada.encode("cp1252"), cwd=cwd,
                              capture_output=True, timeout=TEMPO_LIMITE)
        bruto, codigo = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired as e:
        bruto, codigo = e.stdout or b"", None
    return bruto.decode("cp1252", errors="replace").replace("\r\n", "\n"), codigo


def verificar(caso: dict, saida: str, codigo: int | None, usadas: int,
              trabalho: Path, antes: dict[str, bytes]) -> list[str]:
    falhas = []
    if codigo is None:
        falhas.append(f"tempo esgotado ({TEMPO_LIMITE} s)")
    elif codigo != 0:
        falhas.append(f"codigo de saida {codigo}")
    # o roteiro precisa casar com o programa: lerTexto encerra com exit(0) quando a
    # entrada acaba antes da hora, entao o codigo 0 sozinho nao prova nada
    if "Entrada encerrada." in saida:
        falhas.append("a entrada acabou antes do fim do fluxo (roteiro dessincronizado)")
    if usadas != len(caso["entradas"]):
        falhas.append(f"{len(caso['entradas']) - usadas} entrada(s) sem prompt "
                      "correspondente (roteiro dessincronizado)")
    for rx in caso["contem"]:
        if not re.search(rx, saida):
            falhas.append(f"esperado e ausente: {rx}")
    for rx in caso["nao_contem"]:
        if re.search(rx, saida):
            falhas.append(f"nao deveria aparecer: {rx}")
    for arq in caso["arquivos"]:
        if not (trabalho / arq).exists():
            falhas.append(f"arquivo nao criado: {arq}")
    for arq in caso.get("arquivos_ausentes", []):
        if (trabalho / arq).exists():
            falhas.append(f"arquivo nao deveria existir: {arq}")
    for arq, conteudo in antes.items():
        if (trabalho / arq).read_bytes() != conteudo:
            falhas.append(f"arquivo alterado (deveria ficar igual): {arq}")
    return falhas


def bloquear(trabalho: Path, nomes: list[str]) -> None:
    """Simula falha de gravacao: troca cada arquivo por um diretorio de mesmo nome,
    o que faz o fopen do programa falhar (portavel entre TCC, MSVC e Windows).
    Um arquivo que ja existia e guardado como <nome>.guardado."""
    for nome in nomes:
        alvo = trabalho / nome
        if alvo.exists():
            alvo.rename(trabalho / (nome + ".guardado"))
        alvo.mkdir()


def desbloquear(trabalho: Path, nomes: list[str]) -> None:
    for nome in nomes:
        alvo, guardado = trabalho / nome, trabalho / (nome + ".guardado")
        if alvo.is_dir():
            alvo.rmdir()
        if guardado.exists():
            guardado.rename(alvo)


def somente_leitura(trabalho: Path, nomes: list[str], ligar: bool) -> None:
    """Marca (ou desmarca) arquivos como somente leitura. No Windows, a troca do arquivo
    pelo programa (MoveFileEx com REPLACE_EXISTING) e recusada, sem afetar a leitura.
    No POSIX o rename substitui arquivos somente leitura: por isso o caso que usa este
    recurso e marcado com apenas_windows."""
    for nome in nomes:
        os.chmod(trabalho / nome, stat.S_IREAD if ligar else stat.S_IREAD | stat.S_IWRITE)


def desfazer_preparo(trabalho: Path, bloqueados: list[str], leitura: list[str]) -> None:
    """Desfaz bloquear() e somente_leitura() mesmo que o preparo tenha parado no meio;
    cada etapa e tentada, para os casos seguintes nao rodarem num diretorio estragado."""
    erros = []
    for etapa in (lambda: somente_leitura(trabalho, [n for n in leitura
                                                     if (trabalho / n).exists()], False),
                  lambda: desbloquear(trabalho, bloqueados)):
        try:
            etapa()
        except OSError as e:
            erros.append(e)
    if erros:
        raise erros[0]


def executar() -> int:
    tcc = shutil.which("tcc")
    if tcc is None:
        sys.exit("tcc nao encontrado no PATH.")
    versao = subprocess.run([tcc, "-v"], capture_output=True, text=True).stdout.strip()

    novo = SAIDA.with_name(SAIDA.name + ".novo")
    if novo.exists():
        shutil.rmtree(novo)
    novo.mkdir(parents=True)

    resultados = []
    with tempfile.TemporaryDirectory(prefix="pim2_testes_c_") as tmp:
        tmp = Path(tmp)
        exe = tmp / "simulacao_cardapio.exe"
        comp = subprocess.run([tcc, "-o", str(exe), str(FONTE_C)],
                              capture_output=True, text=True)
        if comp.returncode != 0:
            shutil.rmtree(novo)
            sys.exit("Falha ao compilar com o tcc (evidencias anteriores mantidas):\n"
                     + comp.stdout + comp.stderr)
        trabalho = tmp / "execucao"
        trabalho.mkdir()

        for caso in CASOS:
            if caso.get("apenas_windows") and os.name != "nt":
                # o caso depende de um comportamento do Windows; fora dele nao conta
                # nem como aprovado nem como falha (e nao entra nas evidencias)
                print(f"[IGNORADO] {caso['id']} {caso['titulo']} (apenas no Windows)")
                continue
            bloqueados = caso.get("bloquear", [])
            antes = {a: (trabalho / a).read_bytes()
                     for a in caso.get("arquivos_inalterados", [])}
            leitura = caso.get("somente_leitura", [])
            try:
                bloquear(trabalho, bloqueados)
                somente_leitura(trabalho, leitura, True)
                saida, codigo = rodar(exe, "\n".join(caso["entradas"]) + "\n", trabalho)
            finally:
                desfazer_preparo(trabalho, bloqueados, leitura)
            trechos, usadas = intercalar(saida, caso["entradas"])
            linhas = como_linhas(trechos)
            falhas = verificar(caso, saida, codigo, usadas, trabalho, antes)
            status = "PASSOU" if not falhas else "FALHOU"

            linhas = [[("C:\\PIM-II> simulacao_cardapio.exe", "saida")]] + linhas
            texto = "\n".join("".join(t for t, _ in ln) for ln in linhas)
            (novo / f"{caso['id']}.txt").write_text(texto + "\n", encoding="utf-8")
            pngs = renderizar_paginado(
                linhas, f"{caso['id']} - {caso['titulo']}", novo / caso["id"])

            resultados.append({
                "id": caso["id"], "titulo": caso["titulo"], "requisito": caso["requisito"],
                "descricao": caso["descricao"], "esperado": caso["esperado"],
                "status": status, "falhas": falhas,
                "imagens": [p.name for p in pngs],
            })
            print(f"[{status}] {caso['id']} {caso['titulo']}")
            for f in falhas:
                print("        ", f)

        historico = trabalho / "historico.txt"
        if historico.exists():
            (novo / "historico_final.txt").write_text(
                historico.read_text(encoding="cp1252"), encoding="utf-8")

    passou = sum(r["status"] == "PASSOU" for r in resultados)
    resumo = {"compilador": versao, "total": len(resultados), "passou": passou,
              "casos": resultados}
    (novo / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    linhas_resumo = [f"{r['id']}  [{r['status']}]  {r['titulo']}" for r in resultados]
    linhas_resumo.append(f"\n{passou} de {len(resultados)} casos passaram ({versao}).")
    (novo / "resumo.txt").write_text("\n".join(linhas_resumo) + "\n", encoding="utf-8")

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    novo.rename(SAIDA)
    print(f"\n{passou} de {len(resultados)} casos passaram. Evidencias em {SAIDA}")
    return 0 if passou == len(resultados) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(executar())
