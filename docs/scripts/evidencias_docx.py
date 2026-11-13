"""Insere no relatorio as evidencias de funcionamento (testes em C e execucao SQL).

Le os resultados ja gerados em docs/evidencias/ (rode antes
`python tests/executar_testes_c.py` e `python tests/executar_testes_sql.py`) e:

1. Secao 5.7: texto com o resultado dos testes do modelo fisico (MySQL).
2. Secao 6.8: texto com o resultado dos casos de teste da simulacao em C.
3. Apendice D: quadros com os testes (C e MySQL) e prints de terminal de cada
   execucao. Quadros e figuras ficam so no apendice, para nao alongar o
   desenvolvimento nem renumerar as figuras do corpo.
4. Secao 9.4: remete as evidencias.
5. Legendas (campos SEQ), listas de figuras e de quadros e citacoes em texto dos
   quadros que vem depois sao renumeradas; o documento pede ao Word para atualizar
   os campos ao abrir (paginas, sumario, listas).

Os numeros de figura e de quadro citados nos textos inseridos sao campos REF
ligados as legendas, entao continuam certos se o Word renumerar as legendas.

Reaplicavel: se as evidencias ja estiverem no relatorio, elas sao removidas (so o
que este script insere: as secoes 5.7 e 6.8 ate o proximo titulo, o Apendice D ate
o proximo apendice/anexo, as entradas das listas e a frase da 9.4) e inseridas de
novo com os resultados atuais. Faz backup em
docs/_backups/PIM_II_Sabor_e_Cia.pre-evidencias.docx (so na primeira vez).
Uso:  python docs/scripts/evidencias_docx.py
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reparar_docx import corrigir_sumario  # noqa: E402  (liga o updateFields)

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-evidencias.docx"
EVID = DOCS / "evidencias"
LARGURA_FIG = Cm(16)
TRAV = "–"
FRASE_94 = (" Dentro desse escopo, a lógica central e o modelo físico foram verificados por "
            "testes executados, cujos resultados constam nas seções 5.7 e 6.8 e no Apêndice D.")
REPOSITORIO = "https://github.com/vitorfaust1no/PIM-II"
TITULO_QUADRO_SQL = "Testes do modelo físico em MySQL"
TITULO_QUADRO_C = "Casos de teste da simulação em C"
# inicio dos titulos das figuras inseridas (para reconhece-las nas listas)
PREFIXOS_FIGURA = ("Teste CT", "Script do modelo físico", "Testes do modelo físico",
                   "Execução do modelo físico")
W14 = "{http://schemas.microsoft.com/office/word/2010/wordml}"


# ----------------------------------------------------------------- xml basico
def limpar(el):
    """Remove ids de paragrafo duplicados e marcas de quebra de pagina antigas."""
    for e in el.iter():
        for att in (W14 + "paraId", W14 + "textId"):
            e.attrib.pop(att, None)
    for lr in el.findall(".//" + qn("w:lastRenderedPageBreak")):
        lr.getparent().remove(lr)
    return el


def clonar(el):
    return limpar(copy.deepcopy(el))


def texto_el(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def estilo_id(el) -> str | None:
    ps = el.find(qn("w:pPr") + "/" + qn("w:pStyle"))
    return None if ps is None else ps.get(qn("w:val"))


def tem_quebra_antes(el) -> bool:
    return el.find(qn("w:pPr") + "/" + qn("w:pageBreakBefore")) is not None


def achar(doc, inicio: str, estilo: str | None = None):
    for p in doc.paragraphs:
        if p.text.startswith(inicio) and (estilo is None or p.style.name == estilo):
            return p
    raise LookupError(f"paragrafo nao encontrado: {inicio!r}")


def run_texto(rpr, texto: str):
    r = OxmlElement("w:r")
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = texto
    r.append(t)
    return r


def runs_campo(rpr, instr: str, valor: str) -> list:
    """Runs de um campo do Word: begin, instrucao, separate, valor exibido, end."""
    def fld(tipo):
        r = OxmlElement("w:r")
        if rpr is not None:
            r.append(copy.deepcopy(rpr))
        f = OxmlElement("w:fldChar")
        f.set(qn("w:fldCharType"), tipo)
        r.append(f)
        return r
    ri = OxmlElement("w:r")
    if rpr is not None:
        ri.append(copy.deepcopy(rpr))
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    ri.append(it)
    return [fld("begin"), ri, fld("separate"), run_texto(rpr, valor), fld("end")]


def indicador(id_: int, nome: str | None = None):
    if nome is None:
        b = OxmlElement("w:bookmarkEnd")
    else:
        b = OxmlElement("w:bookmarkStart")
        b.set(qn("w:name"), nome)
    b.set(qn("w:id"), str(id_))
    return b


INDICADORES = (qn("w:bookmarkStart"), qn("w:bookmarkEnd"))
# conteudo que definir_texto descarta e que merece aviso (o resto e so texto em runs)
DESCARTE_AVISADO = {qn(t) for t in ("w:fldSimple", "w:fldChar", "w:hyperlink", "w:ins",
                                    "w:del", "w:commentRangeStart", "w:commentReference")}


def definir_texto(p_el, texto: str, manter_indicadores: bool = False):
    """Deixa o paragrafo so com o pPr e um run (formatacao do primeiro run) com o texto.

    Remove todo o resto (outros runs, w:hyperlink, w:ins, w:del, w:fldSimple...).
    Com manter_indicadores=True, preserva os indicadores (bookmarks) de referencia
    cruzada do proprio paragrafo, envolvendo o texto novo: os inicios ficam antes
    dele e os fins depois (um REF/PAGEREF para o indicador continua mostrando o
    texto, e um intervalo que atravessa paragrafos nao encolhe). Nesse modo avisa
    quando descarta campos, hyperlinks, comentarios ou alteracoes controladas."""
    primeiro = next((r for r in p_el.iter(qn("w:r")) if r.find(qn("w:t")) is not None), None)
    rpr = None if primeiro is None else primeiro.find(qn("w:rPr"))
    rpr = None if rpr is None else copy.deepcopy(rpr)
    if manter_indicadores:
        perdidos = sorted({e.tag.split("}")[1] for e in p_el.iter() if e.tag in DESCARTE_AVISADO})
        if perdidos:
            print(f"  AVISO: {', '.join(perdidos)} descartado(s) ao reescrever "
                  f"{texto_el(p_el)[:50]!r}")
    inicios = [e for e in p_el if manter_indicadores and e.tag == INDICADORES[0]]
    fins = [e for e in p_el if manter_indicadores and e.tag == INDICADORES[1]]
    for e in list(p_el):
        if e.tag != qn("w:pPr"):
            p_el.remove(e)
    for e in inicios + [run_texto(rpr, texto)] + fins:
        p_el.append(e)
    return p_el


def substituir_regex(el, padrao: str, troca, limite: int | None = None) -> int:
    """Substitui ocorrencias de `padrao` no texto do elemento, mesmo que estejam
    divididas em varios runs (a formatacao de cada run e preservada).
    `troca` e uma string ou funcao(match) -> string. Devolve quantas trocas fez."""
    ts = list(el.iter(qn("w:t")))
    texto = "".join(t.text or "" for t in ts)
    achados = list(re.finditer(padrao, texto))
    if limite is not None:
        achados = achados[:limite]
    for m in reversed(achados):  # do fim para o inicio: posicoes anteriores nao mudam
        novo = troca(m) if callable(troca) else troca
        pos, inserido = 0, False
        for t in ts:
            s = t.text or ""
            ini, fim = pos, pos + len(s)
            pos = fim
            if fim <= m.start() or ini >= m.end():
                if not (ini == m.start() == m.end() == fim and not inserido):
                    continue
            a, b = max(m.start(), ini) - ini, min(m.end(), fim) - ini
            t.text = s[:a] + ("" if inserido else novo) + s[b:]
            t.set(qn("xml:space"), "preserve")
            inserido = True
    return len(achados)


# ----------------------------------------------------------------- legendas
class Ids:
    """Gera ids e nomes novos de indicadores (bookmarks)."""

    def __init__(self, doc):
        ids = [int(b.get(qn("w:id"))) for b in doc.element.body.iter(qn("w:bookmarkStart"))]
        self.prox = max(ids + [0])
        self.cont: dict[str, int] = {}

    def novo(self, prefixo: str):
        self.prox += 1
        self.cont[prefixo] = self.cont.get(prefixo, 0) + 1
        return self.prox, f"{prefixo}{self.cont[prefixo]:03d}"


def legenda(modelo_el, numero: int, titulo: str, ids: Ids):
    """Monta 'Figura|Quadro n - titulo' do zero, com o pPr e a formatacao da legenda
    modelo: indicador _TocEvid (listas) na legenda toda e _RefEvid so no numero
    (para citacoes com REF). Devolve (paragrafo, nome_toc, nome_ref)."""
    p = clonar(modelo_el)
    instr = next(t.text for t in p.iter(qn("w:instrText")) if "SEQ" in (t.text or ""))
    rotulo = re.search(r"SEQ\s+(\w+)", instr).group(1)
    primeiro = next(r for r in p.iter(qn("w:r")) if r.find(qn("w:t")) is not None)
    rpr = primeiro.find(qn("w:rPr"))
    rpr = None if rpr is None else copy.deepcopy(rpr)
    for e in list(p):
        if e.tag != qn("w:pPr"):
            p.remove(e)
    id_toc, nome_toc = ids.novo("_TocEvid")
    id_ref, nome_ref = ids.novo("_RefEvid")
    p.append(indicador(id_toc, nome_toc))
    p.append(run_texto(rpr, rotulo + " "))
    p.append(indicador(id_ref, nome_ref))
    for r in runs_campo(rpr, f" SEQ {rotulo} \\* ARABIC ", str(numero)):
        p.append(r)
    p.append(indicador(id_ref))
    p.append(run_texto(rpr, f" {TRAV} {titulo}"))
    p.append(indicador(id_toc))
    ppr = p.find(qn("w:pPr"))
    if ppr.find(qn("w:keepNext")) is None:  # legenda nunca fica sozinha no fim da pagina
        ppr.insert(0, OxmlElement("w:keepNext"))
    return p, nome_toc, nome_ref


def entrada_lista(modelo_el, texto: str, ancora: str):
    """Clona uma entrada da lista de figuras/quadros apontando para a nova legenda.
    Funciona mesmo que o titulo do modelo esteja dividido em varios runs."""
    p = clonar(modelo_el)
    for e in list(p):  # descarta inicio/fim do campo TOC que a entrada modelo carregue
        if e.tag not in (qn("w:pPr"), qn("w:hyperlink")):
            p.remove(e)
    h = p.find(qn("w:hyperlink"))
    h.set(qn("w:anchor"), ancora)
    runs = h.findall(qn("w:r"))
    i_tab = next(i for i, r in enumerate(runs) if r.find(qn("w:tab")) is not None)
    titulo = [r for r in runs[:i_tab] if r.find(qn("w:t")) is not None]
    titulo[0].find(qn("w:t")).text = texto
    for r in titulo[1:]:
        h.remove(r)
    no_valor = False
    for r in runs[i_tab:]:
        fc = r.find(qn("w:fldChar"))
        if fc is not None:
            no_valor = fc.get(qn("w:fldCharType")) == "separate"
            continue
        if no_valor and r.find(qn("w:t")) is not None:
            r.find(qn("w:t")).text = ""  # pagina: o Word recalcula ao atualizar os campos
    for it in h.iter(qn("w:instrText")):
        it.text = f" PAGEREF {ancora} \\h "
    return p


def tabela(modelo_tbl, cabecalho: list[str], linhas: list[list[str]], larguras: list[int]):
    tbl = clonar(modelo_tbl)
    trs = tbl.findall(qn("w:tr"))
    tr_cab, tr_dado = trs[0], trs[1]
    for tr in trs:
        tbl.remove(tr)
    grid = tbl.find(qn("w:tblGrid"))
    for g in list(grid):
        grid.remove(g)
    for w in larguras:
        g = OxmlElement("w:gridCol")
        g.set(qn("w:w"), str(w))
        grid.append(g)

    def montar(tr_modelo, valores):
        tr = copy.deepcopy(tr_modelo)
        tcs = tr.findall(qn("w:tc"))
        for tc in tcs:
            tr.remove(tc)
        for valor, w in zip(valores, larguras):
            tc = copy.deepcopy(tcs[0])
            tc.find(qn("w:tcPr")).find(qn("w:tcW")).set(qn("w:w"), str(w))
            p = tc.find(qn("w:p"))
            definir_texto(p, valor)
            r = p.find(qn("w:r"))
            rpr = r.find(qn("w:rPr"))
            if rpr is None:
                rpr = OxmlElement("w:rPr")
                r.insert(0, rpr)
            for sz in rpr.findall(qn("w:sz")):
                rpr.remove(sz)
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), "20")  # 10 pt no quadro
            rpr.append(sz)
            tr.append(tc)
        return tr

    tbl.append(montar(tr_cab, cabecalho))
    for ln in linhas:
        tbl.append(montar(tr_dado, ln))
    return tbl


# ----------------------------------------------------------------- remocao e numeracao
def eh_entrada_nossa(texto: str) -> bool:
    m = re.match(rf"(Figura|Quadro) \d+ {TRAV} (.*)", texto)
    if not m:
        return False
    if m.group(1) == "Quadro":
        return m.group(2).startswith((TITULO_QUADRO_SQL, TITULO_QUADRO_C))
    return m.group(2).startswith(PREFIXOS_FIGURA)


def remover_evidencias(doc):
    """Remove o que uma execucao anterior inseriu. Devolve (removeu, ancoras): para
    "5.7", "6.8" e "D", o elemento que vinha logo apos o bloco removido (None se o
    bloco nao existia ou ia ate o fim), para reinserir cada bloco no mesmo lugar."""
    corpo = doc.element.body
    titulos = {doc.styles["Heading 1"].style_id, doc.styles["Heading 2"].style_id}
    removeu = False

    def eh_titulo(el):
        return el.tag == qn("w:p") and estilo_id(el) in titulos

    def eh_apendice(el, prefixos=("APÊNDICE", "ANEXO")):
        return (el.tag == qn("w:p") and tem_quebra_antes(el)
                and texto_el(el).startswith(prefixos))

    def remover_faixa(inicio, parada):
        """Remove do elemento `inicio` (inclusive) ate o primeiro `parada` (exclusive)."""
        nonlocal removeu
        ativo, depois = False, None
        for el in list(corpo):
            if el.tag == qn("w:sectPr"):
                break
            if ativo and parada(el):
                depois = el
                break
            if not ativo and inicio(el):
                ativo = True
            if ativo:
                corpo.remove(el)
                removeu = True
        return depois

    ancoras = {}
    ancoras["5.7"] = remover_faixa(
        lambda el: eh_titulo(el) and texto_el(el).startswith("5.7 Evid"), eh_titulo)
    ancoras["6.8"] = remover_faixa(
        lambda el: eh_titulo(el) and texto_el(el).startswith("6.8 Testes"),
                  eh_titulo)
    ancoras["D"] = remover_faixa(lambda el: eh_apendice(el, ("APÊNDICE D",)), eh_apendice)

    for p in doc.paragraphs:
        if p.style.name == "table of figures" and eh_entrada_nossa(p.text):
            p._p.getparent().remove(p._p)
            removeu = True

    p94 = achar(doc, "Entre os benefícios esperados")
    if substituir_regex(p94._p, re.escape(FRASE_94), ""):
        removeu = True
    return removeu, ancoras


def legendas_seq(doc, rotulo: str) -> list:
    """Paragrafos de legenda (campo SEQ <rotulo>) na ordem do documento."""
    saida = []
    for p in doc.paragraphs:
        if any(re.match(rf"\s*SEQ\s+{rotulo}\b", t.text or "")
               for t in p._p.iter(qn("w:instrText"))):
            saida.append(p)
    return saida


def renumerar_legendas(doc) -> None:
    """Atualiza o numero exibido de cada campo SEQ (o Word faria o mesmo ao atualizar)."""
    for rotulo in ("Figura", "Quadro"):
        for n, p in enumerate(legendas_seq(doc, rotulo), 1):
            runs = list(p._p.iter(qn("w:r")))
            k = next(i for i, r in enumerate(runs) for t in r.iter(qn("w:instrText"))
                     if re.match(rf"\s*SEQ\s+{rotulo}\b", t.text or ""))
            for r in runs[k + 1:]:
                if r.find(qn("w:t")) is not None:
                    r.find(qn("w:t")).text = str(n)
                    break


def renumerar_listas(doc) -> None:
    for rotulo in ("Figura", "Quadro"):
        n = 0
        for p in doc.paragraphs:
            if p.style.name == "table of figures" and re.match(rf"{rotulo} \d+ ", p.text):
                n += 1
                substituir_regex(p._p.find(qn("w:hyperlink")), rf"^{rotulo} \d+",
                                 f"{rotulo} {n}", limite=1)


def ajustar_citacoes_quadros(doc) -> int:
    """Depois de remover as evidencias, os quadros que sobram no documento passam a
    ser numerados 1..n pela ordem. As citacoes em texto fixo ('Quadro k') seguem o
    numero que a legenda exibia antes; aqui elas sao levadas ao numero novo.
    Deve rodar antes de renumerar as legendas."""
    mapa = {}
    for n, p in enumerate(legendas_seq(doc, "Quadro"), 1):
        m = re.match(r"Quadro (\d+)", p.text)
        if m:
            mapa[int(m.group(1))] = n

    def novo(m):
        return f"Quadro {mapa.get(int(m.group(1)), int(m.group(1)))}"

    trocas = 0
    for p in doc.paragraphs:
        if p.style.name == "table of figures":
            continue
        if any("SEQ" in (t.text or "") for t in p._p.iter(qn("w:instrText"))):
            continue  # legenda: numerada pelo campo SEQ
        alvos = [m for m in re.finditer(r"\bQuadro (\d+)\b", p.text)
                 if mapa.get(int(m.group(1)), int(m.group(1))) != int(m.group(1))]
        if alvos:
            substituir_regex(p._p, r"\bQuadro (\d+)\b", novo)
            trocas += len(alvos)
    return trocas


def descartar_imagens_orfas(doc) -> None:
    """Remove do pacote as imagens cujos desenhos foram apagados do corpo."""
    xml = doc.element.xml
    for rid, rel in list(doc.part.rels.items()):
        if rel.reltype.endswith("/image") and f'"{rid}"' not in xml:
            doc.part.drop_rel(rid)  # so apaga se nao houver referencia no corpo


def juntar(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


# ----------------------------------------------------------------- principal
def main() -> None:
    res_c = json.loads((EVID / "c" / "resumo.json").read_text(encoding="utf-8"))
    res_sql = json.loads((EVID / "sql" / "resumo.json").read_text(encoding="utf-8"))

    doc = Document(ALVO)
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    reaplicacao, ancoras = remover_evidencias(doc)
    ancora_ap = ancoras["D"]
    if reaplicacao:
        print("Evidencias anteriores removidas; reinserindo com os resultados atuais.")
    trocas = ajustar_citacoes_quadros(doc)
    if trocas:
        print(f"Citacoes de quadros renumeradas no texto: {trocas}.")

    corpo = doc.element.body
    ids = Ids(doc)
    h2_modelo = achar(doc, "6.7 ", "Heading 2")._p
    corpo_modelo = achar(doc, "Os fluxogramas descrevem")._p
    cap_quadro = legendas_seq(doc, "Quadro")[-1]._p
    tbl_modelo = cap_quadro.getnext()
    fonte_quadro = tbl_modelo.getnext()
    cap_fig = legendas_seq(doc, "Figura")[-1]._p
    img_fig = cap_fig.getnext()
    fonte_fig = img_fig.getnext()
    apc = achar(doc, "APÊNDICE C")._p
    cap6 = achar(doc, "6 PROGRAMA", "Heading 1")._p
    cap7 = achar(doc, "7 REDES", "Heading 1")._p

    # posicoes de numeracao, contadas no documento ja sem as evidencias
    def antes_de(el_alvo, legendas):
        ordem = {id(e): i for i, e in enumerate(corpo)}
        return sum(ordem[id(p._p)] < ordem[id(el_alvo)] for p in legendas)

    # os dois quadros ficam no Apendice D (depois de todos os quadros do corpo):
    # primeiro o da simulacao (D.1), depois o do modelo fisico (D.2)
    n_corpo = len(legendas_seq(doc, "Quadro"))
    n_c, n_sql = n_corpo + 1, n_corpo + 2
    # as figuras do apendice continuam a numeracao das que vem antes dele
    figuras_doc = legendas_seq(doc, "Figura")
    primeira = (antes_de(ancora_ap, figuras_doc) if ancora_ap is not None
                else len(figuras_doc)) + 1

    def h2(texto):
        return definir_texto(clonar(h2_modelo), texto)

    def par(texto: str, refs: dict | None = None):
        """Paragrafo de corpo; '{nome}' no texto vira um campo REF para o indicador."""
        p = definir_texto(clonar(corpo_modelo), "")
        rpr = p.find(qn("w:r")).find(qn("w:rPr"))
        p.remove(p.find(qn("w:r")))
        for k, parte in enumerate(re.split(r"\{(\w+)\}", texto)):
            if k % 2 == 0:
                if parte:
                    p.append(run_texto(rpr, parte))
            else:
                ref, valor = refs[parte]
                for r in runs_campo(rpr, f" REF {ref} \\h ", str(valor)):
                    p.append(r)
        return p

    # ---- figuras do apendice ----
    figuras = []  # (caminho, titulo, grupo)
    for caso in res_c["casos"]:
        k = len(caso["imagens"])
        for n, img in enumerate(caso["imagens"], 1):
            sufixo = f" (parte {n} de {k})" if k > 1 else ""
            figuras.append((EVID / "c" / img,
                            f"Teste {caso['id']} {TRAV} {caso['titulo']}{sufixo}", "c"))
    imgs = res_sql["imagens"]
    figuras.append((EVID / "sql" / imgs["SQL_01_criacao"][0],
                    f"Script do modelo físico {TRAV} criação do banco e das tabelas", "sql"))
    k = len(imgs["SQL_02_comandos"])
    for n, img in enumerate(imgs["SQL_02_comandos"], 1):
        figuras.append((EVID / "sql" / img, f"Script do modelo físico {TRAV} transação e "
                        f"consultas (parte {n} de {k})", "sql"))
    vistos: set[str] = set()
    for img, testes in zip(imgs["SQL_03_testes"], res_sql["testes_por_imagem"]):
        unicos = list(dict.fromkeys(testes))
        rotulos = [f"{t} (continuação)" if t in vistos else t for t in unicos]
        vistos.update(unicos)
        figuras.append((EVID / "sql" / img,
                        f"Testes do modelo físico {TRAV} " + juntar(rotulos), "sql"))

    caps_fig = []
    for i, (img, titulo, grupo) in enumerate(figuras):
        cap, anc, ref = legenda(cap_fig, primeira + i, titulo, ids)
        caps_fig.append((cap, anc, ref, img, titulo, grupo))
    refs = {}
    for grupo in ("c", "sql"):
        do_grupo = [(c[2], primeira + i) for i, c in enumerate(caps_fig) if c[5] == grupo]
        refs[f"fig_{grupo}_ini"], refs[f"fig_{grupo}_fim"] = do_grupo[0], do_grupo[-1]

    # ---- 5.7: testes do modelo fisico ----
    sql_ok = res_sql["passou"] == res_sql["total"]
    cap_sql, anc_sql, ref_sql = legenda(cap_quadro, n_sql, TITULO_QUADRO_SQL, ids)
    refs["q_sql"] = (ref_sql, n_sql)
    linhas_sql = [[t["id"], t["descricao"], t["esperado"],
                   ("Conforme esperado" if t["status"] == "PASSOU" else "Divergente")]
                  for t in res_sql["testes"]]
    sec57 = [
        h2("5.7 Evidências de execução do modelo físico"),
        par("Para comprovar o funcionamento do modelo físico, o script do Apêndice B foi "
            f"executado integralmente em um servidor MySQL {res_sql['mysql']}, instanciado em um "
            "contêiner Docker descartável, por meio do cliente de linha de comando mysql em modo "
            "detalhado, que exibe cada comando seguido do seu resultado. Em seguida, executou-se "
            "o script de testes testes_modelo_fisico.sql, que confere a estrutura criada e a "
            "carga de exemplo, o efeito da transação de alteração de disponibilidade (RF06 e "
            "RF11), a repetição dessa operação e o desfazimento por ROLLBACK e, em testes "
            "negativos, se as restrições de integridade de fato recusam dados inválidos."),
        par("O Quadro {q_sql}, no Apêndice D, resume os testes e o resultado obtido: "
            f"{res_sql['passou']} de {res_sql['total']} apresentaram o comportamento esperado. "
            "Os testes negativos falharam exatamente com o erro previsto, como o erro 3819 nas "
            "restrições CHECK, o erro 1644 lançado pela trigger de harmonização e os erros 1452 "
            "e 1451 das chaves estrangeiras, e, ao final, a contagem de registros permaneceu "
            "inalterada, o que mostra que nenhum dado inválido foi gravado. As telas de execução "
            "estão no mesmo apêndice (Figuras {fig_sql_ini} a {fig_sql_fim})." if sql_ok else
            "O Quadro {q_sql}, no Apêndice D, resume os testes e o resultado obtido; as telas de "
            "execução estão no mesmo apêndice (Figuras {fig_sql_ini} a {fig_sql_fim}).", refs),
    ]
    quadro_sql = [cap_sql,
                  tabela(tbl_modelo, ["Teste", "Verificação", "Resultado esperado",
                                      "Resultado obtido"], linhas_sql, [750, 2850, 3361, 2100]),
                  clonar(fonte_quadro)]
    for el in sec57:  # mesmo lugar de antes; na primeira vez, no fim do capitulo 5
        (ancoras["5.7"] if ancoras["5.7"] is not None else cap6).addprevious(el)

    # ---- 6.8: testes da simulacao ----
    c_ok = res_c["passou"] == res_c["total"]
    cap_c, anc_c, ref_c = legenda(cap_quadro, n_c, TITULO_QUADRO_C, ids)
    refs["q_c"] = (ref_c, n_c)
    linhas_c = [[c["id"], c["requisito"], c["descricao"], c["esperado"],
                 ("Conforme esperado" if c["status"] == "PASSOU" else "Divergente")]
                for c in res_c["casos"]]
    versao_tcc = res_c["compilador"].replace("tcc version ", "").split(" ")[0]
    sec68 = [
        h2("6.8 Testes da simulação"),
        par("A simulação foi verificada por testes funcionais, que avaliam o comportamento do "
            "programa a partir das entradas e das saídas, sem depender da estrutura interna do "
            f"código (Sommerville, 2018). O programa foi compilado com o TCC {versao_tcc} e "
            f"executado {res_c['total']} vezes em sequência; cada execução recebeu um roteiro de "
            "entradas definido previamente, e a saída foi comparada de forma automática ao "
            "resultado esperado pelo script tests/executar_testes_c.py. Como as execuções "
            "compartilham os arquivos cardapio.txt e historico.txt, os casos também verificam a "
            "persistência entre execuções: a desativação feita pelo gerente no CT04 é observada "
            "pelo cliente no CT05 e contabilizada pelo relatório de frequência no CT12."),
        par("Os casos cobrem os fluxos principais e o tratamento de entradas inválidas, conforme "
            f"o Quadro {{q_c}}, no Apêndice D, e {res_c['passou']} de {res_c['total']} obtiveram "
            "o resultado esperado. As telas de cada execução, com os valores digitados "
            "destacados, estão no mesmo apêndice (Figuras {fig_c_ini} a {fig_c_fim})." if c_ok else
            "Os casos e os resultados obtidos estão no Quadro {q_c}, no Apêndice D, junto com as "
            "telas de cada execução (Figuras {fig_c_ini} a {fig_c_fim}).", refs),
    ]
    quadro_c = [cap_c,
                tabela(tbl_modelo, ["Caso", "Requisito", "Procedimento", "Resultado esperado",
                                    "Resultado obtido"], linhas_c, [750, 1150, 2780, 2681, 1700]),
                clonar(fonte_quadro)]
    for el in sec68:  # mesmo lugar de antes; na primeira vez, no fim do capitulo 6
        (ancoras["6.8"] if ancoras["6.8"] is not None else cap7).addprevious(el)

    # ---- 9.4: remete as evidencias ----
    p94 = achar(doc, "Entre os benefícios esperados")
    ultimo = p94.runs[-1]
    ultimo.text = ultimo.text.rstrip() + FRASE_94

    # ---- Apendice D ----
    def subtitulo(texto):
        p = clonar(corpo_modelo)
        ppr = p.find(qn("w:pPr"))
        for tag in ("w:ind", "w:jc"):
            e = ppr.find(qn(tag))
            if e is not None:
                ppr.remove(e)
        ppr.insert(0, OxmlElement("w:keepNext"))
        definir_texto(p, texto)
        r = p.find(qn("w:r"))
        rpr = r.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            r.insert(0, rpr)
        if rpr.find(qn("w:b")) is None:
            rpr.insert(0, OxmlElement("w:b"))
        return p

    novos = [definir_texto(clonar(apc), f"APÊNDICE D {TRAV} EVIDÊNCIAS DE EXECUÇÃO DOS TESTES"),
             par("Este apêndice reúne os quadros com os testes executados (Quadros {q_c} e "
                 "{q_sql}) e as telas de execução que comprovam os resultados. As telas da "
                 "simulação foram capturadas das execuções "
                 "descritas na seção 6.8, com os valores digitados em destaque; as do modelo "
                 "físico, da execução descrita na seção 5.7, em que o cliente mysql exibe cada "
                 "comando seguido do seu resultado. Os registros completos estão no repositório "
                 "do projeto, na pasta docs/evidencias.", refs),
             par(f"Os testes podem ser reproduzidos a partir do repositório {REPOSITORIO}, "
                 "executando, na pasta raiz, os comandos python tests/executar_testes_c.py e "
                 "python tests/executar_testes_sql.py. O primeiro compila o programa com o TCC "
                 f"{versao_tcc} e executa os casos definidos em tests/casos_simulacao.py; o "
                 "segundo cria um contêiner Docker descartável com o MySQL "
                 f"{res_sql['mysql']}, executa os scripts database/modelo_fisico_mysql.sql e "
                 "database/testes_modelo_fisico.sql e remove o contêiner ao final. Os dois "
                 "scripts requerem Python 3 com a biblioteca Pillow, comparam a saída obtida com "
                 "o resultado esperado de forma automática e terminam com código de erro se algum "
                 "teste falhar. A instalação das ferramentas está descrita no arquivo README.md "
                 "do repositório.")]
    imagens = []
    grupo_atual = None
    for cap, anc, ref, img, titulo, grupo in caps_fig:
        if grupo != grupo_atual:
            grupo_atual = grupo
            novos.append(subtitulo("D.1 Simulação em C" if grupo == "c"
                                   else "D.2 Modelo físico em MySQL"))
            novos += quadro_c if grupo == "c" else quadro_sql
        p_img = clonar(img_fig)
        for e in list(p_img):
            if e.tag != qn("w:pPr"):
                p_img.remove(e)
        novos += [cap, p_img, clonar(fonte_fig)]
        imagens.append((p_img, img))
    if ancora_ap is not None:  # volta para o mesmo lugar (antes do apendice/anexo seguinte)
        for el in novos:
            ancora_ap.addprevious(el)
    else:
        ultimo_el = corpo[-1] if corpo[-1].tag != qn("w:sectPr") else corpo[-2]
        for el in novos:
            ultimo_el.addnext(el)
            ultimo_el = el
    for p_img, img in imagens:  # pela API, que cria a relacao com o arquivo da imagem
        Paragraph(p_img, doc.part).add_run().add_picture(str(img), width=LARGURA_FIG)

    # ---- listas de quadros e de figuras ----
    def entradas(rotulo):
        return [p._p for p in doc.paragraphs
                if p.style.name == "table of figures" and re.match(rf"{rotulo} \d+ ", p.text)]

    ent_q = entradas("Quadro")
    for pos, titulo, anc in sorted(((n_sql, TITULO_QUADRO_SQL, anc_sql),
                                    (n_c, TITULO_QUADRO_C, anc_c))):
        nova = entrada_lista(ent_q[0], f"Quadro {pos} {TRAV} {titulo}", anc)
        atuais = entradas("Quadro")
        if pos - 1 < len(atuais):
            atuais[pos - 1].addprevious(nova)
        else:
            atuais[-1].addnext(nova)
    ent_f = entradas("Figura")
    ref_el = ent_f[primeira - 2] if primeira >= 2 else None
    for i, (cap, anc, ref, img, titulo, grupo) in enumerate(caps_fig):
        nova = entrada_lista(ent_f[-1], f"Figura {primeira + i} {TRAV} {titulo}", anc)
        if ref_el is None:
            ent_f[0].addprevious(nova)
        else:
            ref_el.addnext(nova)
        ref_el = nova

    # ---- Resumo e Abstract: contagem de testes lida dos resumo.json ----
    from revisao_final_docx import resultados_testes  # import local: ele importa este modulo
    resultados_testes(doc)

    renumerar_legendas(doc)
    renumerar_listas(doc)
    corrigir_sumario(doc)  # updateFields: o Word atualiza sumario, listas, REF e paginas
    descartar_imagens_orfas(doc)
    doc.save(ALVO)
    print(f"Inseridos: secoes 5.7 e 6.8 (texto) e Apendice D com os Quadros {n_c} e {n_sql} "
          f"e as Figuras {primeira} a {primeira + len(figuras) - 1}.")
    print("Abra no Word, aceite atualizar os campos (sumario, listas e paginas) e reexporte o PDF.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
