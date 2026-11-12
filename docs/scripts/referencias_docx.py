"""Revisao das referencias de PIM_II_Sabor_e_Cia.docx (12/11/2026).

Ajusta dados bibliograficos e padronizacao ABNT (NBR 6023:2018 / NBR 10520:2023):
- RDC 727: dados da publicacao no DOU (n. 126, secao 1, p. 213, 6 jul. 2022) + link oficial;
- Abrasel: data exata da materia (15 maio 2023) no lugar de "[2023]" (citacao no 3.1);
- IBGE: data completa da noticia (23 maio 2025);
- W3C: entidade por extenso (WORLD WIDE WEB CONSORTIUM), tambem na citacao do 3.4.2;
- DUDH: URL da pagina oficial da ONU Brasil em vez da UNICEF;
- Sole et al.: "et al." sem italico (padrao das demais referencias);
- datas de acesso unificadas em 12 nov. 2026 (URLs reabertas nessa data);
- alinhamento a esquerda explicito em todas as referencias.

Os dados dos artigos foram conferidos no Crossref (sem alteracao). Idempotente.
Uso (da raiz, com o .docx fechado no Word):  python docs/scripts/referencias_docx.py
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-referencias.docx"

ACESSO = "Acesso em: 12 nov. 2026."

# prefixos aceitos (antigo ou novo) -> (antes do titulo, titulo em negrito, depois do titulo)
REFERENCIAS = [
    (("AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA.",),
     ("AGÊNCIA NACIONAL DE VIGILÂNCIA SANITÁRIA. ",
      "Resolução da Diretoria Colegiada – RDC nº 727, de 1º de julho de 2022",
      ". Dispõe sobre a rotulagem dos alimentos embalados. Diário Oficial da União: seção 1, "
      "Brasília, DF, n. 126, p. 213, 6 jul. 2022. Disponível em: "
      "https://www.in.gov.br/web/dou/-/resolucao-rdc-n-727-de-1-de-julho-de-2022-413249279. " + ACESSO)),
    (("ASSOCIAÇÃO BRASILEIRA DE BARES E RESTAURANTES.",),
     ("ASSOCIAÇÃO BRASILEIRA DE BARES E RESTAURANTES. ",
      "Cardápio por QR Code é uma questão de mercado, não de lei, diz Abrasel",
      ". [S. l.]: Abrasel, 15 maio 2023. Disponível em: https://abrasel.com.br/noticias/noticias/"
      "cardapio-por-qr-code-e-uma-questao-de-mercado-nao-de-lei-diz-abrasel/. " + ACESSO)),
    (("BRASIL. Lei nº 8.078",),
     ("BRASIL. ", "Lei nº 8.078, de 11 de setembro de 1990",
      ". Dispõe sobre a proteção do consumidor e dá outras providências. Brasília, DF: Presidência da "
      "República, 1990. Disponível em: https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm. "
      + ACESSO)),
    (("BRASIL. Lei nº 13.146",),
     ("BRASIL. ", "Lei nº 13.146, de 6 de julho de 2015",
      ". Institui a Lei Brasileira de Inclusão da Pessoa com Deficiência (Estatuto da Pessoa com "
      "Deficiência). Brasília, DF: Presidência da República, 2015. Disponível em: "
      "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm. " + ACESSO)),
    (("COMITÊ GESTOR DA INTERNET NO BRASIL.",),
     ("COMITÊ GESTOR DA INTERNET NO BRASIL. ",
      "Pesquisa sobre o uso das tecnologias de informação e comunicação nos domicílios brasileiros",
      ": TIC Domicílios 2025: principais resultados. São Paulo: CGI.br, 2025. Disponível em: "
      "https://cetic.br/media/analises/tic_domicilios_2025_principais_resultados.pdf. " + ACESSO)),
    (("INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA.",),
     ("INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. ", "Censo 2022",
      ": Brasil tem 14,4 milhões de pessoas com deficiência. Rio de Janeiro: IBGE, 23 maio 2025. "
      "Disponível em: https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/"
      "noticias/43463-censo-2022-brasil-tem-14-4-milhoes-de-pessoas-com-deficiencia. " + ACESSO)),
    (("ORGANIZAÇÃO DAS NAÇÕES UNIDAS.",),
     ("ORGANIZAÇÃO DAS NAÇÕES UNIDAS. ", "Declaração Universal dos Direitos Humanos",
      ". Paris: ONU, 1948. Disponível em: "
      "https://brasil.un.org/pt-br/91601-declaração-universal-dos-direitos-humanos. " + ACESSO)),
    (("SOLÉ, Dirceu et al.",),
     ("SOLÉ, Dirceu et al. Consenso Brasileiro sobre Alergia Alimentar: 2018 – Parte 1 – Etiopatogenia, "
      "clínica e diagnóstico. ", "Arquivos de Asma, Alergia e Imunologia", ", v. 2, n. 1, p. 7-38, 2018.")),
    (("W3C.", "WORLD WIDE WEB CONSORTIUM."),
     ("WORLD WIDE WEB CONSORTIUM. ", "Web Content Accessibility Guidelines (WCAG) 2.2",
      ". [S. l.]: W3C, 2023. Disponível em: https://www.w3.org/TR/WCAG22/. " + ACESSO)),
]

# citacoes no corpo: (antigo, novo)
CITACOES = [
    ("Associação Brasileira de Bares e Restaurantes ([2023])",
     "Associação Brasileira de Bares e Restaurantes (2023)"),
    ("robusto (W3C, 2023)", "robusto (World Wide Web Consortium, 2023)"),
]


def secao_referencias(doc):
    paras = doc.paragraphs
    ini = next(i for i, p in enumerate(paras)
               if p.style.name == "Heading 1" and p.text.strip().upper().startswith("REFER"))
    out = []
    for p in paras[ini + 1:]:
        if p.text.strip().upper().startswith(("APÊNDICE", "APENDICE", "ANEXO")):
            break
        if p.text.strip():
            out.append(p)
    return out


def ja_formatada(p, partes) -> bool:
    antes, titulo, depois = partes
    return (p.text == antes + titulo + depois
            and [r.text for r in p.runs if r.bold] == [titulo]
            and not any(r.italic for r in p.runs))


def reescrever(p, partes) -> None:
    """Refaz o paragrafo como 3 runs: [antes][titulo em negrito][depois], sem italico."""
    base = p.runs[0]._r
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    r_tit, r_dep = copy.deepcopy(base), copy.deepcopy(base)
    base.addnext(r_tit)
    r_tit.addnext(r_dep)
    for run, texto, negrito in zip(p.runs, partes, (None, True, None)):
        run.text = texto
        run.bold = negrito
        run.italic = None


def revisar_referencias(doc) -> int:
    refs = secao_referencias(doc)
    feitas = 0
    for prefixos, partes in REFERENCIAS:
        alvos = [p for p in refs if p.text.startswith(prefixos)]
        if len(alvos) != 1:
            raise SystemExit(f"referencia {prefixos[0]!r} casou {len(alvos)} vezes")
        if not ja_formatada(alvos[0], partes):
            reescrever(alvos[0], partes)
            feitas += 1
    for p in refs:
        if p.alignment != WD_ALIGN_PARAGRAPH.LEFT:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            feitas += 1
    return feitas


def unificar_acesso(doc) -> int:
    """Troca datas de acesso antigas que ainda restarem (ex.: Lei 13.709 ja estava em 12 nov.)."""
    n = 0
    for p in secao_referencias(doc):
        for r in p.runs:
            if "Acesso em: 28 out. 2026." in r.text:
                r.text = r.text.replace("Acesso em: 28 out. 2026.", ACESSO)
                n += 1
    return n


def aplicar_citacoes(doc) -> int:
    feitas = 0
    for antigo, novo in CITACOES:
        if any(novo in p.text for p in doc.paragraphs):
            continue
        alvos = [r for p in doc.paragraphs for r in p.runs if antigo in r.text]
        if len(alvos) != 1:
            raise SystemExit(f"citacao casou {len(alvos)} vezes: {antigo!r}")
        alvos[0].text = alvos[0].text.replace(antigo, novo)
        feitas += 1
    return feitas


def main() -> None:
    doc = Document(ALVO)
    refs = revisar_referencias(doc)
    acesso = unificar_acesso(doc)
    cit = aplicar_citacoes(doc)
    if refs or acesso or cit:
        BACKUP.parent.mkdir(exist_ok=True)
        if not BACKUP.exists():
            shutil.copy2(ALVO, BACKUP)
        doc.save(ALVO)
    print(f"referencias={refs} datas_acesso={acesso} citacoes={cit}")


if __name__ == "__main__":
    main()
