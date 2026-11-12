"""Renderiza transcricoes de console como PNG no estilo de uma janela de terminal.

Uma transcricao e uma lista de linhas; cada linha e uma lista de trechos
(texto, tipo), em que tipo e "saida" ou "entrada" (o que foi digitado, que
aparece em destaque). Transcricoes longas sao divididas em varias imagens.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTE = os.path.join(r"C:\Windows\Fonts", "consola.ttf")
FONTE_NEGRITO = os.path.join(r"C:\Windows\Fonts", "consolab.ttf")
TAM = 20
ALT_LINHA = 25
MARGEM = 18
BARRA = 34
LINHAS_POR_IMAGEM = 64
COLUNAS_MIN = 80
MAX_COLUNAS = 118

FUNDO = (12, 12, 12)
BARRA_COR = (230, 230, 230)
BARRA_TXT = (30, 30, 30)
SAIDA = (204, 204, 204)
ENTRADA = (249, 241, 165)
ERRO = (255, 120, 110)
OK = (130, 220, 130)


def _cor(texto: str, tipo: str):
    if tipo == "entrada":
        return ENTRADA
    t = texto.lstrip()
    if t.startswith("ERROR") or "[FALHOU]" in t:
        return ERRO
    if t.startswith("Query OK") or "[PASSOU]" in t:
        return OK
    return SAIDA


def paginar(linhas: list, por_imagem: int = LINHAS_POR_IMAGEM) -> list[list]:
    """Divide as linhas em blocos, preferindo quebrar em linhas vazias."""
    paginas, atual = [], []
    for ln in linhas:
        atual.append(ln)
        vazia = not "".join(t for t, _ in ln).strip()
        if len(atual) >= por_imagem or (vazia and len(atual) >= por_imagem - 8):
            paginas.append(atual)
            atual = []
    if atual:
        paginas.append(atual)
    # remove linhas vazias nas pontas de cada pagina
    limpas = []
    for p in paginas:
        while p and not "".join(t for t, _ in p[0]).strip():
            p = p[1:]
        while p and not "".join(t for t, _ in p[-1]).strip():
            p = p[:-1]
        if p:
            limpas.append(p)
    return limpas


def quebrar(linhas: list, max_cols: int = MAX_COLUNAS) -> list:
    """Quebra linhas mais largas que max_cols (como faria a janela do terminal)."""
    saida = []
    for ln in linhas:
        if len("".join(t for t, _ in ln)) <= max_cols:
            saida.append(ln)
            continue
        atual, n = [], 0
        for texto, tipo in ln:
            while texto:
                cabe = max_cols - n
                parte, texto = texto[:cabe], texto[cabe:]
                atual.append((parte, tipo))
                n += len(parte)
                if n >= max_cols:
                    saida.append(atual)
                    atual, n = [], 0
        if atual:
            saida.append(atual)
    return saida


def paginar_blocos(blocos: list[list], por_imagem: int = LINHAS_POR_IMAGEM,
                   rotulos: list | None = None):
    """Junta blocos inteiros (ex.: um teste SQL) em paginas sem corta-los.

    Com `rotulos` (um por bloco), devolve (paginas, rotulos presentes em cada pagina).
    """
    com_rotulos = rotulos is not None
    rotulos = rotulos if com_rotulos else [None] * len(blocos)
    paginas, por_pag, atual, rot = [], [], [], []
    for bloco, r in zip(blocos, rotulos):
        bloco = quebrar(bloco)
        if atual and len(atual) + len(bloco) > por_imagem:
            paginas.append(atual)
            por_pag.append(rot)
            atual, rot = [], []
        while len(bloco) > por_imagem:  # bloco maior que uma pagina
            paginas.append(bloco[:por_imagem])
            por_pag.append([r])
            bloco = bloco[por_imagem:]
        atual.extend(bloco)
        rot.append(r)
    if atual:
        paginas.append(atual)
        por_pag.append(rot)
    return (paginas, por_pag) if com_rotulos else paginas


def renderizar(linhas: list, titulo: str, destino: Path) -> None:
    fonte = ImageFont.truetype(FONTE, TAM)
    fonte_titulo = ImageFont.truetype(FONTE_NEGRITO, 17)
    larg_char = fonte.getlength("M")
    cols = MAX_COLUNAS  # largura fixa: mesma escala de letra em todas as figuras
    largura = int(cols * larg_char + 2 * MARGEM)
    altura = BARRA + MARGEM * 2 + ALT_LINHA * len(linhas)

    img = Image.new("RGB", (largura, altura), FUNDO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, largura, BARRA], fill=BARRA_COR)
    d.text((MARGEM, 8), titulo, font=fonte_titulo, fill=BARRA_TXT)
    for i, simbolo in enumerate(["x", "\u25a1", "_"]):  # botoes da janela
        x = largura - MARGEM - (i + 1) * 28
        d.text((x, 6), simbolo, font=fonte_titulo, fill=BARRA_TXT)

    y = BARRA + MARGEM
    for ln in linhas:
        x = MARGEM
        linha_toda = "".join(t for t, _ in ln)
        for texto, tipo in ln:
            d.text((x, y), texto, font=fonte, fill=_cor(linha_toda, tipo))
            x += fonte.getlength(texto)
        y += ALT_LINHA
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, optimize=True)


def renderizar_paginado(linhas: list, titulo: str, base: Path,
                        paginas: list | None = None) -> list[Path]:
    """Gera base.png (ou base_p1.png, base_p2.png...) e devolve os caminhos."""
    if paginas is None:
        paginas = paginar(quebrar(linhas))
    saidas = []
    for n, pag in enumerate(paginas, 1):
        if len(paginas) == 1:
            destino = base.with_suffix(".png")
            tit = titulo
        else:
            destino = base.with_name(f"{base.name}_p{n}.png")
            tit = f"{titulo}  (parte {n}/{len(paginas)})"
        renderizar(pag, tit, destino)
        saidas.append(destino)
    return saidas


def texto_para_linhas(texto: str) -> list:
    """Converte texto puro (tudo 'saida') no formato de linhas (sem a quebra final)."""
    texto = texto.replace("\r\n", "\n").rstrip("\n")
    return [[(ln, "saida")] for ln in texto.split("\n")]
