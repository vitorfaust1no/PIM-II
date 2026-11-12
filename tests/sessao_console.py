"""Sessao de console da simulacao em C: prompts e intercalacao das entradas.

Usado pelos testes (tests/executar_testes_c.py) e pelo video
(apresentacao/build.py), para que os dois tenham UMA so lista de prompts.

Quando a entrada vem por pipe, o que foi digitado nao aparece na saida do
programa. `intercalar` reinsere cada entrada logo apos o prompt que a pediu,
reconstruindo a sessao como seria vista no terminal.
"""

from __future__ import annotations

# Prompts impressos pelo programa antes de cada leitura do teclado (toda leitura
# passa por lerTexto, que imprime a mensagem antes do fgets). Ao mudar um prompt
# em src/simulacao_cardapio.c, atualize esta lista.
PROMPTS = [
    "Opcao: ",
    "Escolha a filial: ",
    "Filtrar por alergeno (enter para ver tudo): ",
    "Login: ",
    "Senha: ",
    "Nome: ",
    "Categoria: ",
    "Alergenos (separe por virgula, enter para nenhum): ",
    "Preco (R$): ",
    "ID do produto (0 para voltar): ",
    "1 - Ativar 2 - Desativar: ",
]


def intercalar(saida: str, entradas: list[str],
               quebra_sempre: bool = True) -> tuple[list[tuple[str, str]], int]:
    """Reinsere cada entrada apos o prompt correspondente.

    Devolve (trechos, usadas): trechos e uma lista [(texto, "saida"|"entrada"), ...]
    e usadas e quantas entradas encontraram um prompt (menos que len(entradas)
    indica roteiro dessincronizado).
    quebra_sempre=True insere o enter digitado sempre (fiel ao terminal);
    False so o insere se a saida nao comecar com quebra de linha (mais compacto).
    """
    trechos, cursor, usadas = [], 0, 0
    for valor in entradas:
        achados = [(saida.find(p, cursor), p) for p in PROMPTS]
        achados = [(i, p) for i, p in achados if i != -1]
        if not achados:
            break
        i, p = min(achados)
        fim = i + len(p)
        trechos.append((saida[cursor:fim], "saida"))
        trechos.append((valor, "entrada"))
        if quebra_sempre or not saida.startswith("\n", fim):
            trechos.append(("\n", "saida"))
        cursor = fim
        usadas += 1
    trechos.append((saida[cursor:], "saida"))
    return trechos, usadas


def como_texto(trechos: list[tuple[str, str]]) -> str:
    return "".join(t for t, _ in trechos)


def como_linhas(trechos: list[tuple[str, str]]) -> list:
    """Converte trechos em linhas no formato do renderizador de terminal."""
    linhas, atual = [], []
    for texto, tipo in trechos:
        for k, parte in enumerate(texto.split("\n")):
            if k > 0:
                linhas.append(atual)
                atual = []
            if parte:
                atual.append((parte, tipo))
    linhas.append(atual)
    while linhas and not linhas[-1]:
        linhas.pop()
    return linhas
