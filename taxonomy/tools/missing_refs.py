"""List questions whose text points at something outside the question.

Books number their theorems, equations, figures, tables and exercises, and a question
lifted out of a book often still says "by Theorem 4.4", "as in Exercise 2.9", "Fig. P3.59",
"Table 7.2" or "the previous problem". This finds those questions so they can be rewritten
to stand alone. It generalises missing_figures.py.

Run from the repo root: python taxonomy/tools/missing_refs.py
Writes taxonomy/data_quality/missing_refs.csv. Read-only on the database.

Each flagged question gets a severity:
  fix   - the question refers to a theorem, equation, figure, table, exercise, section,
          data file or neighbouring problem that the question itself does not contain
  check - only weaker signals: a bibliography citation, a figure number on an image that
          is there but unlabelled, a "Questions 3-15 are about ..." group heading, or an
          opening such as "Again ..." that may lean on an earlier problem
"""
import csv
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "app" / "data" / "appdata" / "amplify.db"
OUT = ROOT / "taxonomy" / "data_quality" / "missing_refs.csv"

# 3, 4.12, P3.176, A.4, 11.20b, 6-21 (Chapman and Dornbusch number with hyphens)
ID = r"[A-Z]{0,2}\d+(?:\s?[.\-]\s?\d+)*[a-z]?"
CAPTION = re.compile(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}")
GRAPHIC = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}")
PICTURE = re.compile(r"\\begin\{(?:tikzpicture|picture|pspicture)\}")
TABULAR = re.compile(r"\\begin\{(?:tabular\*?|tabularx|longtable|array)\}")
STRUCTURE = re.compile(r"\\begin\{|\\\[|\$\$")
# the question's own number at its start, e.g. Berkeley's "Problem 2.2.18 (Fa77)"
SELF_LABEL = re.compile(r"^\s*(?:\\textbf\{|\\paragraph\{|\{\\bf\s*)?\s*(?:Problem|Exercise|Example|Question|Prob\.)\s*"
                        r"(?:" + ID + r")\s*\}?\s*(?:\([^)]{0,30}\))?[.:]?", re.I)

LIST_TAIL = r"((?:\s*(?:,|and|&|to|thru|through)\s*\(?" + ID + r"\)?)*)"
FIG_REF = re.compile(r"\bFig(?:ure)?s?\.?\s*~?\(?(" + ID + r")\)?" + LIST_TAIL, re.I)
TAB_REF = re.compile(r"\bTab(?:le)?s?\.?\s*~?(" + ID + r")\b" + LIST_TAIL)
EQ_REF = re.compile(r"\b(?:Eq(?:uation)?s?|Formulae?|Formulas|Inequality)\.?\s*~?\(?(" + ID + r")\)?", re.I)
EQ_BARE = re.compile(r"\b(?:in|from|using|use|see|by|of|with|into|satisfies|satisfying|cf\.|via|and)\s+"
                     r"\((\d+(?:\.\d+)+[a-z]?|[A-Z]\.\d+)\)")
# Kaczor and Nowak cite other problems by bare three-part numbers: "the formula given in 2.5.8"
BARE_PROBLEM = re.compile(r"\b(?:in|of|from|see|cf\.|and|by|use|using|to)\s+(\d+\.\d+\.\d+[a-z]?)\b(?![\d.]*\s*(?:mm|cm|m|kg|s)\b)")
# another exercise of the book: "Prob. 6.62", "Exercise (3.3.8)", "Question 13.9"
EXERCISE_REF = re.compile(
    r"\b(Exercises?|Exer\.|Ex\.|Problems?|Probs?\.|Questions?|Review Exercises?)\s*(?:\\?#\s*)?~?\(?(" + ID + r")\)?", re.I)
# the book's main text: "Theorem 4.4", "Example 7.1.25", "Section 2.3", "Chapter 9", "§3"
TEXT_REF = re.compile(
    r"\b(Theorems?|Thms?\.|Lemmas?|Corollary|Corollaries|Cor\.|Propositions?|Prop\.|Definitions?|Def\.|"
    r"Examples?|Sections?|Sects?\.|Secs?\.|Chapters?|Chaps?\.|Ch\.|Appendix|Appendices|App\.|Remarks?|"
    r"Algorithms?|Programs?|Articles?|Art\.|Worked Examples?|Solved Examples?|Illustrations?|Pages?)"
    r"\s*~?\(?(" + ID + r")\)?|(§)\s*(" + ID + r")", re.I)
GROUP_HEADING = re.compile(r"\b(?:Problems|Questions|Exercises)\s+\d+\s*[-\u2013]+\s*\d+\s+(?:are|use|ask|deal|involve|refer|concern|follow)", re.I)
PAGE_CITE = re.compile(r"\bpp?\.\s*\d{2,}")
NEIGHBOUR_EXERCISE = re.compile(
    r"\b(?:the\s+)?(?:previous|preceding|prior|foregoing|above|last|earlier|former|next)\s+(?:\w+\s+)?"
    r"(?:problems?|exercises?|questions?|problem\s+sets?)\b"
    r"|\b(?:problems?|exercises?|questions?)\s+(?:above|before|preceding)\b|\bresults?\s+above\b"
    r"|\b(?:the\s+)?(?:previous|preceding)\s+(?:one|result)\b", re.I)
NEIGHBOUR_TEXT = re.compile(
    r"\b(?:the\s+)?(?:previous|preceding|prior|foregoing|above|last|earlier|former|next)\s+(?:\w+\s+)?"
    r"(?:examples?|sections?|chapters?|theorems?|lemmas?|propositions?|corollar(?:y|ies)|page)\b"
    r"|\b(?:examples?|theorems?|lemmas?)\s+(?:above|before|preceding)\b"
    r"|(?<!\bat )\b(?:this|the present|the next|the previous|an earlier|a previous|a later|a subsequent)\s+(?:chapter|section)\b"
    r"|\b(?:start|beginning|end)\s+of\s+(?:the|this)\s+(?:chapter|section)\b"
    r"|\b(?:studied|discussed|seen|derived|introduced|defined)\s+(?:earlier|previously)\b"
    r"|\bwe\s+(?:have\s+)?(?:saw|seen|studied|discussed|derived|proved|showed|shown)\s+(?:earlier|before|previously)\b"
    r"|\b(?:in|of|from)\s+the\s+text\b|\bthis\s+book\b", re.I)
LATEX_REF = re.compile(r"\\(?:ref|eqref|pageref|autoref|cref)\{[^}]*\}|\?\?")
CITATION = re.compile(r"\[?\bRefs?\.\s*\d+[^\]\n]{0,40}\]?|\\cite\{[^}]*\}")
EXTERNAL = re.compile(r"\\url\{|\\href\{|\b[\w\-]+\.(?:dat|csv|txt|xlsx?|sav|mat)\b|\bdata\s*file\b|"
                      r"\b(?:book's|text's|our)\s+web\s*site\b", re.I)
FIG_WORD = re.compile(
    r"(?<!sketch )(?<!draw )\b(?:the|accompanying|following|adjacent|attached)\s+(?:figure|diagram|picture|sketch|drawing)\b"
    r"(?!\s+(?:of|formed|whose|which|that|is called|work|efficienc\w*|power|factor|in each))"
    r"|\b(?:as\s+)?shown\s+(?:below|above|here|at\s+right|on\s+the\s+right|alongside|in\s+the\s+(?:figure|diagram|sketch|picture))\b"
    r"|\bas\s+shown\b(?!\s+in\s+the\s+table|\s+(?:in|by)\s+(?:Example|Exercise|Problem|Prob|Eq|Equation|Section|Sec|Chapter|Theorem|Table|Ref|part)|\s+(?:that|earlier|before|previously))"
    r"|\b(?:figure|diagram|picture|sketch)\s+(?:below|above|alongside|at\s+right)\b"
    r"|\b(?:following|accompanying|given)\s+(?:chart|graph|plot)\b|\b(?:chart|graph|plot)\s+(?:below|above)\b", re.I)
TAB_WORD = re.compile(
    r"\b(?:the\s+)?(?:following|accompanying|attached)\s+(?:table|tabulation)\b"
    r"|\btable\s+(?:below|above)\b|\btabulated\s+(?:below|above|here)\b|\b(?:data|values)\s+(?:below|above)\b", re.I)
# "For the same A and B, find ..." leans on the previous problem's data
SAME_AS_BEFORE = re.compile(r"^\s*(?:\\[a-z]+\*?\{[^}]*\}\s*)?(?:For|With|Under|Using|In)\s+the\s+same\b", re.I)
CONTINUATION = re.compile(r"^\s*(?:\\[a-z]+\*?\{[^}]*\}\s*)?(?:Again\b|Now\s+(?:suppose|let|consider|assume)|Consider\s+again|"
                          r"Return\s+to|Reconsider|Repeat\b|Redo\b|Rework\b|Same\s+as\b|Continu\w+)", re.I)

FIX = ("other_exercise", "book_text", "equation", "figure", "figure_unnumbered", "table",
       "table_unnumbered", "external_data", "latex_ref")
CHECK = ("citation", "group_heading", "figure_unlabelled_image", "continuation")


def norm_id(s: str) -> str:
    return re.sub(r"\s", "", s).rstrip(".")


def ids(first: str, rest: str) -> list[str]:
    return [norm_id(first)] + [norm_id(x) for x in re.findall(ID, rest or "")]


def analyse(tex: str) -> dict[str, list[str]]:
    cap_ids = set()
    for cap in CAPTION.findall(tex):
        for m in re.finditer(r"(?:Fig(?:ure)?\.?|Table)\s*(" + ID + r")", cap, re.I):
            cap_ids.add(norm_id(m.group(1)))
    n_img = len(GRAPHIC.findall(tex)) + len(PICTURE.findall(tex))
    has_tab = bool(TABULAR.search(tex))
    text = GRAPHIC.sub(" ", CAPTION.sub(" ", tex))
    m = SELF_LABEL.match(text)
    if m:
        text = text[m.end():]
    out: dict[str, list[str]] = {}

    def add(cat: str, s: str) -> None:
        s = " ".join(s.split())
        if s not in out.setdefault(cat, []):
            out[cat].append(s)

    figs = []
    for m in FIG_REF.finditer(text):
        figs += ids(m.group(1), m.group(2))
    figs = list(dict.fromkeys(figs))
    for f in figs:
        if f in cap_ids:
            continue
        if n_img and not cap_ids and len(figs) <= n_img:
            add("figure_unlabelled_image", "Fig. " + f)
        else:
            add("figure", "Fig. " + f)
    tabs = []
    for m in TAB_REF.finditer(text):
        tabs += ids(m.group(1), m.group(2))
    tabs = list(dict.fromkeys(tabs))
    for t in tabs:
        if not (t in cap_ids or (has_tab and len(tabs) == 1)):
            add("table", "Table " + t)
    for m in [*EQ_REF.finditer(text), *EQ_BARE.finditer(text)]:
        e = norm_id(m.group(1))
        # equation numbered inside the question itself, e.g. "\tag{1}" and later "equation (1)"
        if "\\tag{" + e + "}" in text or text.count("(" + e + ")") >= 2:
            continue
        if re.fullmatch(r"\d", e) and re.search(r"\\(?:begin\{(?:equation|align|eqnarray|gather)\}|\[)", text):
            continue
        add("equation", m.group(0))
    for m in BARE_PROBLEM.finditer(text):
        add("other_exercise", m.group(1))
    heading_spans = [g.span() for g in GROUP_HEADING.finditer(text)]
    for a, b in heading_spans:
        add("group_heading", text[a:b])
    for m in EXERCISE_REF.finditer(text):
        if not any(a <= m.start() < b for a, b in heading_spans):
            add("other_exercise", m.group(0))
    for m in TEXT_REF.finditer(text):
        word, num = (m.group(1), m.group(2)) if m.group(1) else ("§", m.group(4))
        # "sections 1 and 2" of a pipe are flow stations, not book sections
        if word.lower().startswith("sec") and not re.search(r"[.\-]", norm_id(num)):
            continue
        add("book_text", m.group(0))
    for m in PAGE_CITE.finditer(text):
        add("citation", m.group(0))
    for m in NEIGHBOUR_EXERCISE.finditer(text):
        add("other_exercise", m.group(0))
    m = SAME_AS_BEFORE.match(text)
    if m:
        add("other_exercise", m.group(0).strip())
    for m in NEIGHBOUR_TEXT.finditer(text):
        add("book_text", m.group(0))
    for m in LATEX_REF.finditer(text):
        add("latex_ref", m.group(0))
    for m in CITATION.finditer(text):
        add("citation", m.group(0))
    for m in EXTERNAL.finditer(text):
        add("external_data", m.group(0))
    if not n_img and not figs:
        for m in FIG_WORD.finditer(text):
            # "the pairs shown below:" followed by a tabular or display holds the content itself
            if re.search(r"(?i)below|following", m.group(0)) and STRUCTURE.search(text[m.end(): m.end() + 250]):
                continue
            add("figure_unnumbered", m.group(0))
    if not has_tab and not tabs and not STRUCTURE.search(text):
        for m in TAB_WORD.finditer(text):
            add("table_unnumbered", m.group(0))
    m = CONTINUATION.match(text)
    if m:
        add("continuation", m.group(0).strip())
    return out


def main() -> None:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = []
    for qid, source, subsource, tex, sol, gen, emb in conn.execute(
        "SELECT question_id, source, subsource, latexcode, coalesce(solution, ''), coalesce(generated_solution, ''), "
        "similarity_emb IS NOT NULL FROM questions ORDER BY question_id"
    ):
        found = analyse(tex)
        if not found:
            continue
        severity = "fix" if any(c in found for c in FIX) else "check"
        cats = [c for c in FIX + CHECK if c in found]
        refs = "; ".join(f"{c}: " + " | ".join(found[c]) for c in cats)
        rows.append([qid, source, subsource or "", severity, " ".join(cats), refs,
                     int(bool(sol.strip())), int(bool(gen.strip())), int(emb), " ".join(tex.split())[:200]])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question_id", "source", "subsource", "severity", "categories", "references",
                    "has_solution", "has_generated_solution", "has_embedding", "question_start"])
        w.writerows(rows)
    fix = [r for r in rows if r[3] == "fix"]
    print(f"{len(rows)} questions flagged ({len(fix)} fix, {len(rows) - len(fix)} check) -> {OUT}")
    cats = Counter(c for r in rows for c in r[4].split())
    for c, n in cats.most_common():
        print(f"  {n:5d}  {c}")
    by_source = Counter(r[1] for r in fix)
    print("fix, by source:")
    for s, n in by_source.most_common():
        print(f"  {n:5d}  {s}")


if __name__ == "__main__":
    main()
