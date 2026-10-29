# -*- coding: utf-8 -*-
"""
Geracao dos slides (1920x1080) com Pillow para o video do PIM II.
Cada segmento do roteiro vira um ou mais PNGs. Tipos: titulo, texto,
diagrama, codigo e terminal. Reutiliza os diagramas PNG ja existentes.

render_segment() devolve a LISTA de PNGs do segmento (os slides de
terminal podem ser paginados em varias telas para manter a legibilidade).
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
MARGIN = 90
HEADER_H = 170
FOOTER_Y = H - 64

# Paleta "bistro"
GOLD = (212, 162, 78)
CREAM = (244, 237, 225)
MUTED = (171, 159, 142)
CARD = (247, 243, 236)
CODE_BG = (13, 17, 23)
CODE_FG = (221, 224, 230)
CODE_DIM = (120, 160, 120)
TERM_BG = (10, 12, 16)
TERM_FG = (205, 230, 205)

FONTS_DIR = r"C:\Windows\Fonts"


def _font(name, size):
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)


def load_fonts():
    return {
        "brand": _font("segoeuib.ttf", 30),
        "title": _font("segoeuib.ttf", 58),
        "bigtitle": _font("segoeuib.ttf", 92),
        "subtitle": _font("segoeui.ttf", 36),
        "body": _font("segoeui.ttf", 40),
        "foot": _font("segoeui.ttf", 24),
        "tag": _font("segoeui.ttf", 26),
    }


def _gradient_bg():
    img = Image.new("RGB", (W, H))
    top, bot = (28, 23, 18), (11, 9, 7)
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        row = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = row
    return img


_BG_CACHE = None


def _base(fonts, title, index, total):
    global _BG_CACHE
    if _BG_CACHE is None:
        _BG_CACHE = _gradient_bg()
    img = _BG_CACHE.copy()
    d = ImageDraw.Draw(img)
    d.text((MARGIN, 48), "SABOR & CIA BISTRÔ", font=fonts["brand"], fill=GOLD)
    if title:
        d.text((MARGIN, 92), title, font=fonts["title"], fill=CREAM)
    d.line([(MARGIN, HEADER_H), (W - MARGIN, HEADER_H)], fill=GOLD, width=3)
    d.text((MARGIN, FOOTER_Y), "PIM II — Análise e Desenvolvimento de Sistemas",
           font=fonts["foot"], fill=MUTED)
    if total:
        tag = f"{index:02d} / {total:02d}"
        tw = d.textlength(tag, font=fonts["foot"])
        d.text((W - MARGIN - tw, FOOTER_Y), tag, font=fonts["foot"], fill=MUTED)
    return img, d


def _wrap(d, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ----------------------------------------------------------------- titulo
def render_titulo(fonts, seg, index, total):
    img, d = _base(fonts, "", index, total)
    title, sub = seg["titulo"], seg.get("subtitulo", "")
    tf = fonts["bigtitle"]
    tw = d.textlength(title, font=tf)
    ty = H // 2 - 120
    d.text(((W - tw) / 2, ty), title, font=tf, fill=CREAM)
    d.line([(W / 2 - 160, ty + 150), (W / 2 + 160, ty + 150)], fill=GOLD, width=4)
    if sub:
        for i, ln in enumerate(_wrap(d, sub, fonts["subtitle"], W - 520)):
            lw = d.textlength(ln, font=fonts["subtitle"])
            d.text(((W - lw) / 2, ty + 190 + i * 52), ln, font=fonts["subtitle"], fill=MUTED)
    return [img]


# ----------------------------------------------------------------- texto
def render_texto(fonts, seg, index, total):
    img, d = _base(fonts, seg["titulo"], index, total)
    bf = fonts["body"]
    x, y = MARGIN + 20, HEADER_H + 70
    max_w = W - 2 * MARGIN - 80
    gap = 34 if len(seg["bullets"]) <= 4 else 22
    for b in seg["bullets"]:
        d.ellipse([(x, y + 16), (x + 16, y + 32)], fill=GOLD)
        lines = _wrap(d, b, bf, max_w - 50)
        for j, ln in enumerate(lines):
            d.text((x + 42, y + j * 50), ln, font=bf, fill=CREAM)
        y += len(lines) * 50 + gap
    return [img]


# ----------------------------------------------------------------- diagrama
def render_diagrama(fonts, seg, index, total, diagramas_dir):
    img, d = _base(fonts, seg["titulo"], index, total)
    dia = Image.open(os.path.join(diagramas_dir, seg["asset"])).convert("RGBA")
    cx0, cy0 = MARGIN, HEADER_H + 30
    cx1, cy1 = W - MARGIN, FOOTER_Y - 20
    cw, ch = cx1 - cx0, cy1 - cy0
    pad = 28
    scale = min((cw - 2 * pad) / dia.width, (ch - 2 * pad) / dia.height)
    nw, nh = max(1, int(dia.width * scale)), max(1, int(dia.height * scale))
    dia = dia.resize((nw, nh), Image.LANCZOS)
    card_w, card_h = nw + 2 * pad, nh + 2 * pad
    card_x = cx0 + (cw - card_w) // 2
    card_y = cy0 + (ch - card_h) // 2
    d.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                        radius=18, fill=CARD)
    img.paste(dia, (card_x + pad, card_y + pad), dia)
    return [img]


# ----------------------------------------------------- painel monoespacado
def _panel(fonts, seg, index, total, bg, page_tag=""):
    img, d = _base(fonts, seg["titulo"], index, total)
    cx0, cy0 = MARGIN, HEADER_H + 30
    cx1, cy1 = W - MARGIN, FOOTER_Y - 20
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=16, fill=bg)
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([cx0 + 28 + i * 34, cy0 + 22, cx0 + 44 + i * 34, cy0 + 38], fill=col)
    if page_tag:
        tw = d.textlength(page_tag, font=fonts["tag"])
        d.text((cx1 - 24 - tw, cy0 + 20), page_tag, font=fonts["tag"], fill=MUTED)
    inner_x, inner_y = cx0 + 40, cy0 + 64
    inner_w = (cx1 - inner_x) - 40
    inner_h = (cy1 - inner_y) - 30
    return img, d, inner_x, inner_y, inner_w, inner_h


def _widest(d, lines, font):
    return max((d.textlength(ln, font=font) for ln in lines), default=0)


def render_codigo(fonts, seg, index, total):
    img, d, ix, iy, iw, ih = _panel(fonts, seg, index, total, CODE_BG)
    lines = seg["codigo"].split("\n")
    size = 30
    while size > 12:
        f = _font("consola.ttf", size)
        if _widest(d, lines, f) <= iw and int(size * 1.4) * len(lines) <= ih:
            break
        size -= 1
    f = _font("consola.ttf", size)
    line_h = int(size * 1.4)
    y = iy
    for ln in lines:
        s = ln.lstrip()
        color = CODE_DIM if s.startswith(("--", "/*", "*", "#")) else CODE_FG
        d.text((ix, y), ln, font=f, fill=color)
        y += line_h
    return [img]


def render_terminal(fonts, seg, index, total, demo_parts):
    lines = demo_parts[seg["demo_part"]].split("\n")
    # mede com um painel de sondagem para escolher o tamanho da fonte
    probe = Image.new("RGB", (10, 10))
    pd = ImageDraw.Draw(probe)
    _, _, _, _, iw, ih = _panel(fonts, seg, index, total, TERM_BG)
    size = 28
    while size > 16:
        f = _font("consola.ttf", size)
        if _widest(pd, lines, f) <= iw:
            break
        size -= 1
    f = _font("consola.ttf", size)
    line_h = int(size * 1.32)
    per_page = max(1, ih // line_h)
    pages = [lines[i:i + per_page] for i in range(0, len(lines), per_page)]
    npag = len(pages)
    imgs = []
    for p, chunk in enumerate(pages, 1):
        tag = f"parte {p}/{npag}" if npag > 1 else ""
        img, d, ix, iy, _, _ = _panel(fonts, seg, index, total, TERM_BG, tag)
        y = iy
        for ln in chunk:
            d.text((ix, y), ln, font=f, fill=TERM_FG)
            y += line_h
        imgs.append(img)
    return imgs


# ----------------------------------------------------------------- dispatch
def render_segment(seg, index, total, out_base, diagramas_dir, demo_parts, fonts=None):
    """Renderiza o segmento e salva os PNGs. Devolve a lista de caminhos."""
    if fonts is None:
        fonts = load_fonts()
    tipo = seg["tipo"]
    if tipo == "titulo":
        imgs = render_titulo(fonts, seg, index, total)
    elif tipo == "texto":
        imgs = render_texto(fonts, seg, index, total)
    elif tipo == "diagrama":
        imgs = render_diagrama(fonts, seg, index, total, diagramas_dir)
    elif tipo == "codigo":
        imgs = render_codigo(fonts, seg, index, total)
    elif tipo == "terminal":
        imgs = render_terminal(fonts, seg, index, total, demo_parts)
    else:
        raise ValueError(f"tipo desconhecido: {tipo}")
    paths = []
    for i, im in enumerate(imgs):
        p = f"{out_base}.png" if len(imgs) == 1 else f"{out_base}_p{i}.png"
        im.save(p)
        paths.append(p)
    return paths
