"""Aplica no relatorio os ajustes da revisao externa (13/11/2026).

1. Capa separada da folha de rosto, no modelo do Manual do PIM II (p. 12):
   UNIP / Projeto Integrado Multidisciplinar / curso / alunos / titulo / local / ano.
   A secao pre-textual passa a numerar a partir de 0, para que a capa nao seja contada
   (ABNT) e as demais paginas mantenham a numeracao atual.
2. O prazo de 30 segundos (RNF01) aparece como meta de projeto, e nao como resultado:
   trocas curtas no 3.7, 5.4 e 9.1 (o desenvolvimento esta no limite de 30 paginas) e
   a limitacao explicita na conclusao.
3. Secao 6.7: as credenciais da simulacao nao devem ser reutilizadas.
4. Quadros: a primeira linha se repete quando o quadro passa de pagina.

As constantes equivalentes em revisao_final_docx.py, sincronizacao_historico_docx.py,
correcoes_avaliador_docx.py e seguranca_simulacao_docx.py ja tem o texto novo, para que
reexecuta-los nao desfaca estas trocas.
Idempotente. Faz backup em docs/_backups/PIM_II_Sabor_e_Cia.pre-parecer.docx na primeira
execucao.
Uso (da raiz, com o .docx fechado no Word):  python docs/scripts/parecer_revisao_docx.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidencias_docx import aplicar_trocas_ancoradas, clonar, definir_texto  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent
ALVO = DOCS / "PIM_II_Sabor_e_Cia.docx"
BACKUP = DOCS / "_backups" / "PIM_II_Sabor_e_Cia.pre-parecer.docx"

UNIP = "UNIVERSIDADE PAULISTA – UNIP"
CAPA_TOPO = [UNIP, "Projeto Integrado Multidisciplinar",
             "Curso Superior de Tecnologia em Análise e Desenvolvimento de Sistemas"]

# (inicio do paragrafo, trecho atual, trecho novo)
TROCAS = [
    ("a) disponibilidade por filial",
     "atualizada em até 30 segundos;", "atualizada em até 30 segundos (meta);"),
    ("Desse modo, o projeto trabalha com dois níveis",
     "em até 30 segundos (RNF01), enquanto", "em até 30 segundos (meta do RNF01), enquanto"),
    # a 9.1 inteira (com a meta do RNF01) e reescrita por escopo_gravacao_docx.py
    ("A principal contribuição",
     "Os diferenciais — atualização em até 30 segundos,",
     "Os diferenciais — atualização em até 30 segundos (meta de projeto),"),
    ("Como limitações, registra-se",
     "com as maquininhas em funcionamento.",
     "com as maquininhas em funcionamento. Por isso, o prazo de até 30 segundos do RNF01 é "
     "uma meta de projeto ainda não medida: comprová-lo exige testes de integração e de carga "
     "com a API, o banco de dados e as maquininhas."),
    ("Para que a simulação pudesse ser executada",
     "não devem ser tomadas como prática recomendada",
     "não devem ser reutilizadas nem tomadas como prática recomendada"),
]


def _espaco_antes(p_el, twips: int | None) -> None:
    ppr = p_el.find(qn("w:pPr"))
    sp = ppr.find(qn("w:spacing"))
    if sp is None:  # pelo schema, w:spacing vem antes de w:ind e w:jc
        sp = OxmlElement("w:spacing")
        depois = next((e for e in ppr if e.tag in (qn("w:ind"), qn("w:jc"))), None)
        if depois is None:
            ppr.append(sp)
        else:
            depois.addprevious(sp)
    if twips is None:
        sp.attrib.pop(qn("w:before"), None)
    else:
        sp.set(qn("w:before"), str(twips))


def inserir_capa(doc) -> bool:
    P = doc.paragraphs
    if P[0].text == UNIP:
        return False
    # folha de rosto: alunos (centralizados) ate a linha vazia, depois titulo e subtitulo
    i_titulo = next(i for i, p in enumerate(P) if p.text == "SABOR & CIA BISTRÔ")
    alunos = [p for p in P[:i_titulo] if " – RA " in p.text]
    modelo = alunos[0]._p                    # centralizado, 1,5 linha, sem negrito
    titulo, subtitulo = P[i_titulo]._p, P[i_titulo + 1]._p
    i_local = next(i for i, p in enumerate(P) if p.text == "Barueri")
    local, ano = P[i_local]._p, P[i_local + 1]._p

    novos = []
    for k, texto in enumerate(CAPA_TOPO):
        p = definir_texto(clonar(modelo), texto)
        if k == 0:  # nome da instituicao em negrito
            rpr = p.find(qn("w:r")).find(qn("w:rPr"))
            if rpr is None:
                rpr = OxmlElement("w:rPr")
                p.find(qn("w:r")).insert(0, rpr)
            rpr.insert(0, OxmlElement("w:b"))
        novos.append(p)
    for k, aluno in enumerate(alunos):
        p = clonar(aluno._p)
        if k == 0:
            _espaco_antes(p, 1440)
        novos.append(p)
    p = clonar(titulo)
    _espaco_antes(p, 2000)
    novos += [p, clonar(subtitulo)]
    p = clonar(local)
    _espaco_antes(p, 2400)
    novos += [p, clonar(ano)]

    folha = P[0]._p
    ppr = folha.find(qn("w:pPr"))
    if ppr.find(qn("w:pageBreakBefore")) is None:
        ppr.insert(0, OxmlElement("w:pageBreakBefore"))
    for el in novos:
        folha.addprevious(el)

    # capa nao contada: a secao pre-textual comeca em 0 (folha de rosto = 1)
    pg = doc.sections[0]._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        doc.sections[0]._sectPr.append(pg)
    pg.set(qn("w:start"), "0")
    return True


def repetir_cabecalhos(doc) -> int:
    marcados = 0
    for tbl in doc.tables:
        tr = tbl.rows[0]._tr
        trpr = tr.get_or_add_trPr()
        if trpr.find(qn("w:tblHeader")) is None:
            trpr.append(OxmlElement("w:tblHeader"))
            marcados += 1
    return marcados


def main() -> None:
    doc = Document(ALVO)
    if not BACKUP.exists():
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy2(ALVO, BACKUP)
        print("Backup:", BACKUP)
    print("Capa inserida." if inserir_capa(doc) else "Capa ja existia.")
    print(f"Trocas de texto: {aplicar_trocas_ancoradas(doc, TROCAS)}.")
    print(f"Quadros com cabecalho repetido: {repetir_cabecalhos(doc)}.")
    doc.save(ALVO)
    print("Abra no Word, atualize os campos (sumario, listas e paginas) e reexporte o PDF.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
