"""
Import quant-interview question sets (owner 2026-11-23: "Import all the sources that are not dependent on the OCR
tool ... the app is for private use anyway")
------------------------------------------------------------------------------------------------------------
Three datasets, selected with --only (default all), each in its own folder under --data:

  quantqa/train.jsonl            QuantQA, huggingface.co/datasets/ReinforceNow/quantqa (MIT claimed; the questions
                                 were collected from interview reports, kept private). 519 numeric interview
                                 questions with a firm tag, topic tags and a key in metadata.answer.
                                 Source "QuantQA", subsource "<firms>, <topic>, question <id>".
  academicquant/questions.jsonl  huggingface.co/datasets/academicquant/quant-interview-questions (CC BY 4.0): 241
                                 questions with a numeric key (to 10 places; recognisable fractions are written as
                                 fractions). Its "worked_answer" is only a link and is not stored.
                                 Source "Academic Quant Interview Questions", subsource "<Topic>, <level>, question <id>".
  quantprimer/                   qp.zip (codeload zip of github.com/dwcoder/QuantitativePrimer, CC BY-SA 4.0) or the
                                 unzipped folder: the LaTeX source of Dirk Bester's "An Interview Primer for
                                 Quantitative Finance". The questions of chapter 1 with the book's worked answers
                                 (kept in the solution column and in ref_solution); C++, SQL, R, Python and array
                                 coding questions and the regression-theory questions (their answer only points to a
                                 later chapter) are dropped. Source "Bester, Quantitative Primer", subsource
                                 "Chapter 1, question <m>".

Answer keys: a definite value or option only. QuantQA and academicquant keys are the datasets' own (not re-derived;
the few that the question contradicts are dropped, see quant_interview_fixes.json). Questions of the Primer whose
answer is an explanation (derive, discuss, give examples) go in with answer None and the book's answer as solution.

Conversions: unicode punctuation and symbols to LaTeX; "30%" to "30\\%"; pounds to \\pounds; braces of sets and
\\min/\\max that lost their backslash restored; fractions written "9/13" in keys become $\\frac{9}{13}$, "16pi" and
"sqrt(2)" become LaTeX. Primer: comments, \\index, \\label, \\footnote, citations and figures (tikz, graphics) are
removed, the book's macros (\\E, \\Var, \\Cov, \\nicefrac, \\abs, \\vec, dcases) are expanded to LaTeX/KaTeX-safe
commands, and references to other parts of the book are reworded. Per-row repairs and drops are in
quant_interview_fixes.json ({"fixes": [{key, field, fixes: [[old, new]]}], "cuts": [{key, field, from, to}],
"dropped": {label: reason}}).

Rows the bank already has (same latex_hash or 85% of 5-word shingles) are skipped and listed, as are rows that repeat
another row of these datasets (same problem with the same key; a paraphrase with a different key is kept as another row).
On --apply: backup, insert (topic/branch/subtopic Uncategorized), append to benchmarks_map.csv, keep ref_solution
in benchmarks_solutions.json. Nothing goes into benchmarks_assignments.json (subject rows).

Usage (repo root):
  python -m app.tools.import_quant_interview --data DIR --dry-run [--only quantqa|academicquant|quantprimer]
         [--dump rows.json] [--set-aside]
  python -m app.tools.import_quant_interview --data DIR --apply
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
import zipfile
from fractions import Fraction
from pathlib import Path

from app.tools.import_answer_sets import duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash
from app.tools.import_ugphysics import tidy

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/quant_interview_set_aside.json")
MIN_SOLUTION = 150  # characters
DATASETS = ("quantqa", "academicquant", "quantprimer")

_FIXES = json.loads(Path(__file__).with_name("quant_interview_fixes.json").read_text(encoding="utf-8"))
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
CUTS: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES.get("cuts", []):
    CUTS.setdefault((_e["key"], _e["field"]), []).append((_e["from"], _e["to"]))
DROPS: dict[str, str] = dict(_FIXES["dropped"])

# --------------------------------------------------------------------------------------------- shared text helpers

CHAR_MAP = {
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "--", "\u2014": "---", "\u2019": "'",
    "\u2018": "`", "\u201c": "``", "\u201d": "''", "\u2026": "\\ldots{}", "\u00a3": "\\pounds{}",
    "\u00a0": " ", "\u2009": " ", "\u202f": " ", "\u00e9": "\\'e", "\u2212": "-", "\u00b0": "^{\\circ}",
    "\u2192": "\\to ", "\u221e": "\\infty ", "\u03c3": "\\sigma ", "\u03c0": "\\pi ", "\u03bc": "\\mu ",
    "\u03bb": "\\lambda ", "\u03b8": "\\theta ", "\u03c1": "\\rho ", "\u03b1": "\\alpha ", "\u03b2": "\\beta ",
    "\u2211": "\\sum ", "\u221a": "\\sqrt ", "\u00bd": "\\frac{1}{2}", "\u00bc": "\\frac{1}{4}",
}
CHAR_RE = re.compile("[" + "".join(CHAR_MAP) + "]")
MATH_SPLIT = re.compile(
    r"(\$\$.*?\$\$|\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\]"
    r"|\\begin\{(?:align|equation|gather|multline)\*?\}.*?\\end\{(?:align|equation|gather|multline)\*?\})",
    re.S,
)
NONASCII_RE = re.compile(r"[^\x00-\x7f]")


def char_fix(text: str) -> str:
    """Unicode punctuation and symbols to LaTeX; inside $...$ a symbol command needs no extra wrapping."""
    parts = MATH_SPLIT.split(text)
    for i, p in enumerate(parts):
        def one(m: re.Match, in_math: bool = bool(i % 2)) -> str:
            c, v = m.group(0), CHAR_MAP[m.group(0)]
            if v.startswith("\\") and v not in ("\\ldots{}", "\\pounds{}") and not in_math and c not in "\u00e9":
                return "$" + v.strip() + "$"
            return v
        parts[i] = CHAR_RE.sub(one, p)
    return "".join(parts)


def fix_set_braces(text: str) -> str:
    """Restore the backslash of a set brace or a \\min{...\\} / \\max{...\\} whose opener lost it."""
    parts = MATH_SPLIT.split(text)
    for i in range(1, len(parts), 2):
        s, out, stack, k = parts[i], list(parts[i]), [], 0
        while k < len(s):
            if s[k] == "\\" and k + 1 < len(s):
                if s[k + 1] == "}" and stack:
                    j = stack[-1]
                    before = s[:j].rstrip()
                    if re.search(r"(=|,|\(|\[|\\min|\\max|\\text\{min\}|\\text\{max\}|\\in|\\mid|:)$", before) or not before.endswith(("}", "_", "^")) and not re.search(r"[A-Za-z]$", before):
                        out[j] = "\\{"
                        stack.pop()
                k += 2
                continue
            if s[k] == "{":
                stack.append(k)
            elif s[k] == "}" and stack:
                stack.pop()
            k += 1
        parts[i] = "".join(out)
    return "".join(parts)


def squeeze(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def prose(text: str) -> str:
    """Clean a dataset statement: unicode to LaTeX, % and display math as the bank writes them."""
    text = char_fix(text)
    text = squeeze(text)
    text = re.sub(r"\$\s*([^$\n]*?)\s*\$", lambda m: "$" + m.group(1) + "$" if m.group(1) else "", text)
    text = fix_set_braces(text)
    parts = MATH_SPLIT.split(text)
    text = "".join(p if i % 2 else re.sub(r"(?<!\\)&", r"\\&", p) for i, p in enumerate(parts))  # P&L
    text = re.sub(r"\$0,\s*1 \\times 0,\s*1\$", r"$[0,1]\\times[0,1]$", text)  # brackets lost in the dataset
    text = re.sub(r"(?<![\w(])\$0,\s*1\$", r"$[0,1]$", text)
    text = re.sub(r"\$\\mathbb\{([EP])\}\$ \$", r"$\\mathbb{\1}\\,", text)  # "$\mathbb{E}$ $X$" is one expression
    return tidy(text)


def apply_fixes(row: dict) -> None:
    key = row["potd"]
    for fld in ("latexcode", "answer", "solution", "ref_solution"):
        for start, end in CUTS.get((key, fld), []):
            t = row[fld] or ""
            a = t.find(start)
            b = (t.find(end, a + len(start)) if end else len(t)) if a >= 0 else -1
            if a < 0 or b < 0 or t.count(start) != 1:
                raise SystemExit(f"CUT {key} {fld}: need one {start!r} before {end!r}")
            row[fld] = (t[:a] + t[b:]).strip()
        for old, new in HAND_FIXES.get((key, fld), []):
            if row[fld] is None or row[fld].count(old) != 1:
                raise SystemExit(f"HAND FIX {key} {fld}: expected one {old!r}")
            row[fld] = row[fld].replace(old, new)


def frac_latex(n: int, d: int) -> str:
    sign = "-" if n < 0 else ""
    return f"${sign}\\frac{{{abs(n)}}}{{{d}}}$"


def number_key(x: float | str) -> str | None:
    """A numeric key: terminating decimals of up to 4 places stay decimals; a repeating decimal written to
    10 places becomes the fraction it clearly is; anything else keeps its digits."""
    s = str(x).strip()
    if re.fullmatch(r"-?\d+", s):
        return s
    if not re.fullmatch(r"-?\d*\.\d+", s):
        return None
    if len(s.split(".")[1]) <= 4:
        return s
    v = float(s)
    fr = Fraction(s).limit_denominator(3000)
    if abs(float(fr) - v) <= 5.5e-11 * max(1.0, abs(v)) and fr.denominator > 1:
        return frac_latex(fr.numerator, fr.denominator)
    return s


def quantqa_key(a: str) -> str:
    a = a.strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", a):
        return a
    m = re.fullmatch(r"(-?)(\d+)/(\d+)", a)
    if m:
        return frac_latex(int(m.group(2)) * (-1 if m.group(1) else 1), int(m.group(3)))
    m = re.fullmatch(r"(\d+)pi", a)
    if m:
        return f"${m.group(1)}\\pi$"
    if a == "e":
        return "$e$"
    m = re.fullmatch(r"sqrt\((\d+)\)", a)
    if m:
        return f"$\\sqrt{{{m.group(1)}}}$"
    if a == "1/sqrt(pi)":
        return "$\\frac{1}{\\sqrt{\\pi}}$"
    m = re.fullmatch(r"(\d+) miles", a)
    if m:
        return f"${m.group(1)}\\ \\mathrm{{miles}}$"
    raise ValueError(f"unexpected key {a!r}")


def new_row(label: str, set_: str, idx: str, source: str, subsource: str, stem: str, answer, solution=None,
            ref: str = "") -> dict:
    return {
        "potd": label, "set": set_, "idx": idx, "orig": "", "source": source, "subsource": subsource,
        "latexcode": stem, "answer": answer, "solution": solution, "hints": None, "more_hints": None,
        "ref_solution": ref, "group": "subject", "effort": None, "image": None,
    }


# ------------------------------------------------------------------------------------------------------- QuantQA

FIRMS = {"Drw": "DRW", "Imc": "IMC", "Sig": "SIG", "Hrt": "HRT", "Worldquant": "WorldQuant", "Sig ": "SIG"}


def firm_tag(firms: list[str]) -> str:
    names = [FIRMS.get(f, f) for f in firms]
    return "/".join(names[:3]) + (f" +{len(names) - 3}" if len(names) > 3 else "") if names else "no firm tag"


def load_quantqa(path: Path, dropped: dict[str, str]) -> list[dict]:
    rows = []
    for line in (path / "train.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        m = r["metadata"]
        key = f"QuantQA {m['id']}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        stem = r["messages"][1]["content"]
        if not m.get("answer", "").strip():
            dropped[key] = "no answer"
            continue
        stem = prose(stem)
        try:
            ans = quantqa_key(m["answer"])
        except ValueError as e:
            dropped[key] = str(e)
            continue
        topic = (m["tags"] or ["General"])[0]
        row = new_row(key, "QuantQA", m["id"], "QuantQA", f"{firm_tag(m['firms'])}, {topic}, question {m['id']}",
                      stem, ans)
        apply_fixes(row)
        if NONASCII_RE.search(row["latexcode"]):
            dropped[key] = "non-ASCII characters left in the statement"
            continue
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------------------------------- academicquant

AQ_TOPICS = {"probability": "Probability", "brainteasers": "Brainteasers", "statistics-ml": "Statistics and ML",
             "market-making": "Market making and expected value", "mental-arithmetic": "Mental arithmetic"}
AQ_CODE_RE = re.compile(r"\b(code|python|algorithm|program|function|implement|script)\b", re.I)
AQ_DEPENDENT_RE = re.compile(r"\b(as before|in the same game|the previous|the above|earlier question)\b", re.I)


def load_academicquant(path: Path, dropped: dict[str, str]) -> list[dict]:
    rows = []
    for line in (path / "questions.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        key = f"AcademicQuant {r['id']}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        if AQ_CODE_RE.search(r["question"]):
            dropped[key] = "coding question"
            continue
        if AQ_DEPENDENT_RE.search(r["question"]):
            dropped[key] = "depends on another question"
            continue
        ans = number_key(r["answer"])
        if ans is None:
            dropped[key] = "key is not a number"
            continue
        topic = AQ_TOPICS.get(r["topic"], r["topic"].replace("-", " ").capitalize())
        stem = prose(r["question"])
        row = new_row(key, "AcademicQuant", r["id"], "Academic Quant Interview Questions",
                      f"{topic}, {r['difficulty']}, question {r['id']}", stem, ans)
        apply_fixes(row)
        if NONASCII_RE.search(row["latexcode"]):
            dropped[key] = "non-ASCII characters left in the statement"
            continue
        rows.append(row)
    return rows


# --------------------------------------------------------------------------------------------- Quantitative Primer

# question name -> (answer key or None, reason to drop or None)
PRIMER = {
    "rolltwodice": ("$\\frac{5}{6}$ (or $\\frac{5}{12}$ if a named die must be the larger)", None),
    "bivariatenormalmax": ("$\\sqrt{\\frac{1-\\rho}{\\pi}}$", None),
    "makematrixfrombunchofvectors": (None, "R programming question"),
    "pythonlistreturnlast": (None, "Python programming question"),
    "cppvirtualfunctionwhy": (None, "C++ programming question"),
    "normalfourthmoment": ("$3\\sigma^4$", None),
    "arraymissingnumber": (None, "array coding question"),
    "arraymissingnumber:a": (None, "array coding question"),
    "arraymissingnumber:b": (None, "array coding question"),
    "normalestimatorssamplingdistribution": (None, None),
    "derivativeofinverse": ("$\\dfrac{1}{g'(g^{-1}(x))}$", None),
    "coin100flipsgamble": ("No", None),
    "iszerocorrelationindependent": ("No", None),
    "iszerocorrelationindependentexamples": (None, None),
    "twournsallocateballs": ("$\\frac{13}{18}$", None),
    "judgescorrectverdict": ("$p$", None),
    "regressiontheory1": (None, "the book's answer only points to a later chapter"),
    "bayeslawdisease": ("$\\frac{8}{107}$", None),
    "derivexpowx": ("$x^x(1+\\ln x)$", None),
    "epiandpie": ("$e^{\\pi}$", None),
    "ar1processmeanandvar": ("(1) $\\dfrac{\\alpha_0}{1-\\alpha_1}$; (2) $\\dfrac{\\sigma_{\\varepsilon}^2}{1-\\alpha_1^2}$", None),
    "constructzerocorrelation": ("$F_Z(z)=\\Phi(z)$, so $Z\\sim\\mathrm{Normal}(0,1)$", None),
    "iszerocovarianceindependent": ("No", None),
    "stickbreak": (None, "the book's answer only points to a later section"),
    "pythonanagrams": (None, "Python programming question"),
    "ncralgorithm": (None, "Python programming question"),
    "romeojuliet": ("$\\frac{7}{16}$", None),
    "davidbeckhamparty": (None, "graph algorithm coding question"),
    "arrayofintegersfindduplicate": (None, "array coding question"),
    "criminalsinfield": (None, None),
    "regressiontheory2": (None, "the book's answer only points to a later chapter"),
    "twopiecesofwood": ("Measure $a+b$ and $b-a$; each length is then estimated with variance $\\frac{\\sigma^2}{2}$", None),
    "bagnsockstwored": ("4", None),
    "regressiontheory3": (None, "the book's answer only points to a later chapter"),
    "nameafewnonlinearmodels": (None, "open-ended list"),
    "sqladdaveragesalary": (None, "SQL question"),
    "sqlhighestsalary": (None, "SQL question"),
    "sqlfindcustomerswithchanges": (None, "SQL question"),
    "regressiontheory4": (None, "the book's answer only points to a later chapter"),
    "rdatastructures": (None, "R programming question"),
    "rmergetwodataframes": (None, "R programming question"),
    "rapplyvsforloops": (None, "R programming question"),
    "grownup": (None, "modelling question whose problem statement is not in the book"),
    "simplerandomwalkhittingprobability": ("$\\frac{k}{l}$", None),
    "addnumbersgame": ("All of it: the first player wins with certainty by saying 6, 17, 28, 39, 50", None),
    "drop20cards": ("$\\frac{1}{221}$", None),
    "bayescoins": ("$\\frac{1024}{2023}$", None),
}

LATEX_MACROS = [
    (r"\\E(?![A-Za-z])", r"\\operatorname{E}"),
    (r"\\Var(?![A-Za-z])", r"\\operatorname{Var}"),
    (r"\\Cov(?![A-Za-z])", r"\\operatorname{Cov}"),
    (r"\\vec(?![A-Za-z])", r"\\boldsymbol"),
    (r"\\textcolor\{[^{}]*\}\{((?:[^{}]|\{[^{}]*\})*)\}", r"\1"),
    (r"\\nonumber(?![A-Za-z])", ""),
    (r"\\phantomsection", ""),
    (r"\\clearpage", ""),
    (r"\\begin\{dcases\*\}", r"\\begin{cases}"),
    (r"\\end\{dcases\*\}", r"\\end{cases}"),
    (r"\\mleft|\\mright", ""),
    (r"\\text\{\\tiny ([^{}]*)\}", r"\\text{\1}"),
]
REMOVE_CMDS = ("index", "label", "footnote", "citet", "citep", "cite", "url", "hyperref", "pageref")


def remove_cmd(text: str, name: str) -> str:
    """Delete \\name[...]{...} (nested braces), also a '%' glued to its end."""
    pat = re.compile(r"\\" + name + r"(?![A-Za-z])")
    while True:
        m = pat.search(text)
        if not m:
            return text
        k = m.end()
        while k < len(text) and text[k] in " \t":
            k += 1
        if k < len(text) and text[k] == "[":
            k = text.index("]", k) + 1
        while k < len(text) and text[k] == "{":
            depth, j = 0, k
            while j < len(text):
                if text[j] == "\\":
                    j += 2
                    continue
                depth += {"{": 1, "}": -1}.get(text[j], 0)
                j += 1
                if depth == 0:
                    break
            k = j
            if name != "hyperref":
                break
        text = text[: m.start()] + text[k:]


def nicefrac(text: str) -> str:
    parts = MATH_SPLIT.split(text)
    for i, p in enumerate(parts):
        parts[i] = re.sub(
            r"\\nicefrac\{([^{}]*)\}\{([^{}]*)\}",
            (lambda m: f"\\frac{{{m.group(1)}}}{{{m.group(2)}}}") if i % 2
            else (lambda m: f"$\\frac{{{m.group(1)}}}{{{m.group(2)}}}$"),
            p,
        )
    return "".join(parts)


def tex_to_bank(text: str) -> str:
    """The book's LaTeX to text that XeLaTeX (the app's preamble) and KaTeX both take."""
    lines = []
    for ln in text.splitlines():
        if ln.lstrip().startswith("%"):
            continue
        lines.append(re.sub(r"(?<!\\)%.*$", "", ln))
    text = "\n".join(lines)
    text = re.sub(
        r"\\begin\{center\}(?:(?!\\end\{center\}).)*?(?:tikzpicture|includegraphics).*?\\end\{center\}", "", text, flags=re.S
    )
    for name in REMOVE_CMDS:
        text = remove_cmd(text, name)
    text = re.sub(r"\\begin\{(?:answer|subanswer)\}\{[^}]*\}", "", text)
    text = re.sub(r"\\end\{(?:answer|subanswer)\}", "", text)
    for pat, new in LATEX_MACROS:
        text = re.sub(pat, new, text)
    text = re.sub(r"\\abs\{([^{}]*)\}", r"\\lvert \1\\rvert", text)
    text = nicefrac(text)
    text = text.replace("\\ \n", "\n")
    text = re.sub(  # numbered displays become unnumbered (no \label is left to point at them)
        r"\\begin\{(align|equation|gather)\}(.*?)\\end\{\1\}",
        lambda m: f"\\begin{{{m.group(1)}*}}{m.group(2)}\\end{{{m.group(1)}*}}",
        text,
        flags=re.S,
    )
    text = re.sub(  # a blank line inside a display (where a \label was) ends the paragraph and breaks the formula
        r"\\begin\{(align\*|equation\*|gather\*)\}.*?\\end\{\1\}",
        lambda m: re.sub(r"\n\s*\n", "\n", m.group(0)),
        text,
        flags=re.S,
    )
    text = re.sub(r"\(?\\(?:eq)?ref\{eq:[^}]*\}\)?", "the equation above", text)
    text = re.sub(r"(?:in |see |from )?(?:section|appendix|answer|question)\s*~?\\ref\{[^}]*\}", "elsewhere in the book", text)
    text = re.sub(r"\\ref\{[^}]*\}", "an earlier question", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class Book:
    """Read the book's files from qp.zip or from an unzipped folder."""

    def __init__(self, folder: Path):
        zips = sorted(folder.glob("*.zip"))
        self.zip = zipfile.ZipFile(zips[0]) if zips else None
        self.base = None
        if self.zip:
            tex = [n for n in self.zip.namelist() if n.endswith("src/QuantitativePrimer.tex")]
            if not tex:
                raise SystemExit("no src/QuantitativePrimer.tex in the zip")
            self.base = tex[0][: -len("QuantitativePrimer.tex")]
        else:
            found = sorted(folder.glob("**/src/QuantitativePrimer.tex"))
            if not found:
                raise SystemExit(f"no QuantitativePrimer.tex under {folder}")
            self.base = found[0].parent.as_posix() + "/"

    def read(self, rel: str) -> str:
        if self.zip:
            return self.zip.read(self.base + rel).decode("utf-8")
        return Path(self.base + rel).read_text(encoding="utf-8")


QUESTION_RE = re.compile(
    r"\\begin\{(question|questionwithnoanswer|subquestion)\}(?:\{([^}]*)\})?(.*?)\\end\{\1\}", re.S
)


def load_primer(folder: Path, dropped: dict[str, str]) -> list[dict]:
    book = Book(folder)
    src = book.read("QuantitativePrimer.tex")
    body = src[src.index("\\section{Interviews}") : src.index("\\section{Old friends}")]
    rows, n, parents = [], 0, {}
    for m in QUESTION_RE.finditer(body):
        kind, name, text = m.groups()
        if kind != "subquestion":
            n += 1
        letter = ""
        if kind == "subquestion":
            letter = "b" if name and name.endswith("examples") else ""
        short = name or f"unnamed{n}"
        label = f"Primer {short.replace(':', '-')}"
        if kind == "questionwithnoanswer":
            dropped[label] = "SQL/R question group without an answer"
            continue
        if kind == "subquestion":
            letter = letter or {"a": "a", "b": "b"}.get(short.rsplit(":", 1)[-1], "b")
        if short not in PRIMER:
            dropped[label] = "not classified"
            continue
        key, why = PRIMER[short]
        if why or label in DROPS:
            dropped[label] = why or DROPS[label]
            continue
        stem = tex_to_bank(text)
        parents[short] = stem
        try:
            ans_tex = book.read(f"answers/{short.replace(':', '_')}.tex")
        except KeyError:
            dropped[label] = "no answer file"
            continue
        sol = tex_to_bank(ans_tex)
        idx = f"{n}{letter}"
        row = new_row(f"Primer {idx}", "Quantitative Primer", idx, "Bester, Quantitative Primer",
                      f"Chapter 1, question {idx}", stem, key, ref=sol)
        row["potd"] = f"Primer {short.replace(':', '-')}"
        row["solution"] = sol if len(sol) >= MIN_SOLUTION else None
        apply_fixes(row)
        if row["solution"] is not None:
            row["solution"] = tidy_solution(row["solution"])
            row["ref_solution"] = row["solution"]
        else:
            row["ref_solution"] = tidy_solution(row["ref_solution"])
        row["latexcode"] = tidy_solution(row["latexcode"])
        rows.append(row)
    return rows


def tidy_solution(t: str) -> str:
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# ------------------------------------------------------------------------------------------- repeats among datasets

WORD_RE = re.compile(r"[a-z0-9]+")
STOP = set("a an the of to in is are and or that this it be at on for with as by from if you your we i what how"
           " determine find calculate compute probability expected value".split())


def content_words(t: str) -> set[str]:
    return {w for w in WORD_RE.findall(re.sub(r"\\[a-zA-Z]+", " ", t.lower())) if w not in STOP}


def numbers_of(t: str) -> list[str]:
    return sorted(re.findall(r"\d+(?:\.\d+)?", re.sub(r"\[a-zA-Z]+", " ", t)))


def repeats(rows: list[dict], dropped: dict[str, str]) -> list[dict]:
    """Drop a row that repeats an earlier one: >= 85% of 5-word shingles, or the same key with a similar word set
    (>= 50%, or >= 40% when the numbers in the two statements are the same)."""
    kept: list[dict] = []
    sh: list[set] = []
    words: list[set[str]] = []
    for r in rows:
        g, w = shingles(r["latexcode"]), content_words(r["latexcode"])
        hit = None
        for k, e in enumerate(kept):
            s = len(g & sh[k]) / max(1, min(len(g), len(sh[k])))
            j = len(w & words[k]) / max(1, len(w | words[k]))
            same = e["answer"] == r["answer"] and r["answer"] is not None
            # short statements that differ in one word ("Three points" / "Four points") share most shingles but are
            # different problems: a repeat needs the same key as well
            if same and (s >= 0.85 or j >= 0.5 or (j >= 0.4 and numbers_of(e["latexcode"]) == numbers_of(r["latexcode"]))):
                hit = e
                break
        if hit is None:
            kept.append(r)
            sh.append(g)
            words.append(w)
        else:
            dropped[r["potd"]] = f"same problem as {hit['potd']}"
    return kept


# --------------------------------------------------------------------------------------------------------- main


def load(data: Path, only: list[str]) -> tuple[list[dict], dict[str, str]]:
    dropped: dict[str, str] = {}
    rows: list[dict] = []
    if "quantqa" in only:
        rows += load_quantqa(data / "quantqa", dropped)
    if "academicquant" in only:
        rows += load_academicquant(data / "academicquant", dropped)
    if "quantprimer" in only:
        rows += load_primer(data / "quantprimer", dropped)
    return repeats(rows, dropped), dropped


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", choices=DATASETS, action="append", help="one dataset (repeatable); default all")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped = load(a.data, a.only or list(DATASETS))
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {
            r["potd"]: check([r]) or [excluded[r["potd"]]]
            for r in new
            if check([r]) or r["potd"] in excluded
        }
        SET_ASIDE_PATH.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    reasons = collections.Counter(re.sub(r"\d+", "N", re.sub(r"(same problem as|paraphrase of) .*? (with|$)", r"\1 X \2", v)) for v in dropped.values())
    print(
        json.dumps(
            {
                "rows_kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "with_stored_solution": sum(bool(r["solution"]) for r in new),
                "with_answer_none": sum(r["answer"] is None for r in new),
                "by_source": collections.Counter(r["source"] for r in new),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        (a.dump.with_name(a.dump.stem + "_dropped.json")).write_text(json.dumps(dropped, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("quant-interview")
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in new:
            h = latex_hash(r["latexcode"])
            if h in existing:
                continue
            cur = conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, hints, more_hints, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"],
                 r["answer"], r["solution"], r["hints"], r["more_hints"], h),
            )
            existing.add(h)
            added.append((cur.lastrowid, r))
        conn.commit()
    finally:
        conn.close()
    new_file = not MAP_PATH.exists() or MAP_PATH.stat().st_size == 0
    with MAP_PATH.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update(
        {str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]} for q, r in added if r["ref_solution"]}
    )
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
