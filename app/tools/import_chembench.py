"""
Import SciBench (chemistry), ChemBench and SUPERChem
----------------------------------------------------
Owner decision 2026-11-23: import every approved chemistry source that does not need the OCR tool (private
use). One importer, three datasets, picked with --only:

  scibench   SciBench (github.com/mandyyyyii/scibench, huggingface.co/datasets/xw27/scibench, MIT): the four
             chemistry textbooks atkins, chemmc, quan, matter. Numeric answers; the dataset gives the unit
             separately and, for small or large values, a power of ten inside the unit ("$10^{-19}$ J"): the key
             folds both ("$3.52\\times 10^{-19}\\ \\mathrm{J}$"). The 43 worked textbook solutions (the *_sol
             files) are stored as `solution`. Six pure-mathematics items (chemmc "Math Part D") are dropped.
             Source "SciBench", subsource "<textbook>, problem <id>".
  chembench  ChemBench (huggingface.co/datasets/jablonkagroup/ChemBench, MIT): the seven core chemistry configs
             (1,110 rows). The toxicity-and-safety and chemical-preference configs are not read. MCQ keys
             come from target_scores (option order = letters; every option with score 1 is correct), the 243
             numeric rows from `target`. Source "ChemBench", subsource "<topic>, <task name>".
  superchem  SUPERChem (huggingface.co/datasets/ZehuaZhao/SUPERChem, MIT): English fields only. Figures are
             replaced by the text the dataset ships with each of them (the SMILES of the structure, or a
             description); canary strings are never read. The expert explanation is the reference solution and,
             when it is at least 150 characters of English after the Chinese-only checkpoint markers are
             removed and it passes the checks, the stored solution. Source "SUPERChem".

Conversions (all three):
  * \\pu{...} (not in LaTeX's mhchem) is rewritten with app.tools.chem_markup.pu_to_latex; \\ce{...} stays.
  * [START_SMILES]...[END_SMILES] (and the RXN variants) become \\texttt{...} with # % \\ { } _ & ^ ~ escaped.
  * A bare % & # _ ~ ^ in running text is escaped; $$..$$ becomes \\[..\\]; Markdown **bold** and the few HTML tags
    become LaTeX; unicode math symbols become commands.
  * MCQ: options each on a line of their own as "(A) ...", a blank line before and between them, and
    "Exactly one option is correct." / "One or more options may be correct." when the text does not say it.
    Answer key = the capital letters, "A, C" for several.
  * Per-row repairs and drops live in chembench_fixes.json (same shape as ugphysics_fixes.json).

Rows the bank already has (same latex_hash or 85% of 5-word shingles) are skipped and listed; a statement that
repeats inside the three datasets is kept once. Nothing is written to pipeline\\benchmarks_assignments.json.

Usage (repo root):
  python -m app.tools.import_chembench --data DIR --dry-run [--only scibench|chembench|superchem]
                                       [--dump rows.json] [--set-aside] [--exclude why.json]
  python -m app.tools.import_chembench --data DIR --apply
DIR holds scibench/<name>.json (atkins, chemmc, quan, matter and their _sol twins), chembench/<config>.parquet
and superchem/SUPERChem-500.parquet.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.chem_markup import _groups, _in_math, pu_to_latex
from app.tools.import_answer_sets import TEXIMAGES, duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/chembench_set_aside.json")
MIN_SOLUTION = 150
DATASETS = ("scibench", "chembench", "superchem")

_FIXES = json.loads(Path(__file__).with_name("chembench_fixes.json").read_text(encoding="utf-8"))
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPS: dict[str, str] = dict(_FIXES["dropped"])
SOLUTION_DROPS: dict[str, str] = dict(_FIXES.get("solution_dropped", {}))

# --------------------------------------------------------------------------------------------- text helpers

SYMBOLS = {
    "\u00d7": r"\times", "\u00b7": r"\cdot", "\u22c5": r"\cdot", "\u00b0": r"^{\circ}", "\u2103": r"^{\circ}\mathrm{C}",
    "\u03b1": r"\alpha", "\u03b2": r"\beta", "\u03b3": r"\gamma", "\u03b4": r"\delta", "\u03b8": r"\theta",
    "\u03bb": r"\lambda", "\u03bc": r"\mu", "\u00b5": r"\mu", "\u03c0": r"\pi", "\u03c1": r"\rho", "\u03c3": r"\sigma",
    "\u03c9": r"\omega", "\u0394": r"\Delta", "\u2206": r"\Delta", "\u03a9": r"\Omega", "\u2192": r"\rightarrow",
    "\u21cc": r"\rightleftharpoons", "\u2248": r"\approx", "\u2264": r"\leq", "\u2265": r"\geq", "\u00b1": r"\pm",
    "\u00f7": r"\div", "\u2261": r"\equiv", "\u221e": r"\infty", "\u2223": r"\mid", "\u25a1": r"\square",
    "\u00c5": r"\text{\AA}", "\u00b2": "^{2}", "\u00b3": "^{3}", "\u2074": "^{4}", "\u207a": "^{+}", "\u207b": "^{-}",
    "\u2080": "_{0}", "\u2081": "_{1}", "\u2082": "_{2}", "\u2083": "_{3}", "\u2084": "_{4}", "\u2085": "_{5}",
    "\u2086": "_{6}", "\u2032": "'", "\u2212": "-",
}
LOOKALIKES = {"\u0391": "A", "\u03a7": "X", "\U0001d465": "x"}  # Greek capitals and a math italic x typed as letters
PROSE_ONLY = {"\u2014": "---", "\u2013": "--", "\u2026": r"\ldots{}", "\u2018": "`", "\u2019": "'", "\u201c": "``",
              "\u201d": "''", "\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u200b": "", "\u2717": r"$\times$",
              "\u2713": r"$\checkmark$"}
for _i, _c in enumerate("\u2460\u2461\u2462\u2463\u2464\u2465\u2466\u2467\u2468", 1):
    PROSE_ONLY[_c] = f"({_i})"
SYMBOL_RE = re.compile("[" + "".join(re.escape(c) for c in SYMBOLS) + "]")
ONLY_RE = re.compile("[" + "".join(re.escape(c) for c in {**PROSE_ONLY, **LOOKALIKES}) + "]")
MATH_UNICODE = {"\u2014": "-", "\u2013": "-", "\u2026": r"\ldots ", "\u00a0": r"\ ", "\u202f": r"\ ", "\u2009": r"\,",
                "\u200b": "", "\u2019": "'", "\u2717": r"\times ", "\u2713": r"\checkmark "}

HTML = [
    (re.compile(r"<sup>(.*?)</sup>", re.S | re.I), r"$^{\1}$"),
    (re.compile(r"<sub>(.*?)</sub>", re.S | re.I), r"$_{\1}$"),
    (re.compile(r"<i>(.*?)</i>", re.S | re.I), r"\\textit{\1}"),
    (re.compile(r"<b>(.*?)</b>", re.S | re.I), r"\\textbf{\1}"),
    (re.compile(r"<code>(.*?)</code>", re.S | re.I), r"\\texttt{\1}"),
    (re.compile(r"<br\s*/?>", re.I), "\n"),
]
BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
SMILES_TAG = re.compile(r"\[START_(?:RXN|RXM)?SMILES\](.*?)\[END_(?:RXN|RXM)?SMILES\]", re.S)
BAD_SMILES_TAG = re.compile(r"\[(?:START|END)_[A-Z]*SMILES\]")
PLACEHOLDER = "\x00{}\x00"
PLACEHOLDER_RE = re.compile("\x00(\\d+)\x00")


def smiles_tt(s: str) -> str:
    """A SMILES (or reaction SMILES) string as \\texttt{...}, escaped, with break points when it is long."""
    s = s.strip().replace("\n", "")
    out = []
    for ch in s:
        out.append({"\\": r"\textbackslash{}", "#": r"\#", "%": r"\%", "{": r"\{", "}": r"\}", "_": r"\_", "&": r"\&",
                    "^": r"\^{}", "~": r"\textasciitilde{}", "$": r"\$"}.get(ch, ch))
        if len(s) > 30 and ch in ")=.>,":
            out.append(r"\allowbreak{}")
    return r"\texttt{" + "".join(out) + "}"


def pu_fix(body: str) -> str:
    """The body of a \\pu the dataset wrote in a way chem_markup does not read, cleaned."""
    b = body.strip().replace("\\%", "%").replace("\\mu ", "\u03bc").replace("\\degree", "\u00b0")
    b = re.sub(r"\bdeg\s*C\b", "\u00b0C", b)
    b = re.sub(r"\bdeg\b", "\u00b0", b)
    b = re.sub(r"\bAngstrom\b|\\A\b", "\u00c5", b)
    return "1.54 \u00c5" if b == "1.54 A" else b  # 1.54 A: an X-ray wavelength


def pu_text(text: str) -> str:
    """Every \\pu{...} as math LaTeX (bare inside math, in $...$ in running text)."""
    out, last = [], 0
    for a, b, body in _groups(text, "pu"):
        out.append(text[last:a])
        fixed = pu_fix(body)
        if m := re.fullmatch(r"([\d.]+)\s*\\theta", fixed):  # an angle, not a unit
            tex = rf"{m.group(1)}\theta"
        else:
            tex = pu_to_latex("\\pu{" + fixed + "}")[1:-1]
        if _in_math(text, a):
            out.append(tex)
        else:  # keep the math apart from letters and digits glued to it
            out.append((" " if a and text[a - 1].isalnum() else "") + f"${tex}$" + (" " if b < len(text) and text[b].isalnum() else ""))
        last = b
    out.append(text[last:])
    return "".join(out)


def _unicode_math(s: str) -> str:
    s = re.sub(r"\\degree(?![A-Za-z])", r"^{\\circ}", s)
    s = re.sub(r"\\mathscr(?![A-Za-z])", r"\\mathcal", s)
    s = "".join(LOOKALIKES.get(c, c) for c in s)
    s = SYMBOL_RE.sub(lambda m: SYMBOLS[m.group(0)] + " ", s)
    return "".join(MATH_UNICODE.get(c, c) for c in s)


RAW_PROSE_CMDS = "textbf|textit|texttt|textsuperscript|ldots|allowbreak|AA|textbackslash|textasciitilde"


def _prose(s: str) -> str:
    # a backslash of a structure string (SMILES) typed in running text is not a command
    s = re.sub(r"\\(?!(?:" + RAW_PROSE_CMDS + r")(?![A-Za-z]))(?=[A-Za-z0-9/=+.@*\-])", r"\\textbackslash{}", s)
    s = re.sub(r"(?<!\\)%", r"\\%", s)
    s = re.sub(r"(?<!\\)&", r"\\&", s)
    s = re.sub(r"(?<!\\)#", r"\\#", s)
    s = re.sub(r"(?<![\\{])_", r"\\_", s)
    s = re.sub(r"(?<!\\)\^", r"\\^{}", s)
    s = re.sub(r"(?<!\\)~", r"\\textasciitilde{}", s)
    s = s.replace("->", r"$\rightarrow$").replace("<", "$<$").replace(">", "$>$")
    s = "".join(LOOKALIKES.get(c, c) for c in s)
    s = SYMBOL_RE.sub(lambda m: "$" + SYMBOLS[m.group(0)] + "$", s)
    return "".join(PROSE_ONLY.get(c, c) for c in s)


def segments(text: str):
    """Split text into ("prose" | "math" | "ce", piece); \\ce groups and $...$ / \\[...\\] stay apart."""
    out, buf, i = [], [], 0

    def flush():
        if buf:
            out.append(("prose", "".join(buf)))
            buf.clear()

    while i < len(text):
        if text.startswith("\\$", i):
            buf.append("\\$")
            i += 2
        elif text.startswith("\\[", i) and (j := text.find("\\]", i)) > 0:
            flush()
            out.append(("math", text[i : j + 2]))
            i = j + 2
        elif text[i] == "$":
            j = i + 1
            while j < len(text) and not (text[j] == "$" and text[j - 1] != "\\"):
                j += 1
            if j >= len(text):
                buf.append(text[i:])
                break
            flush()
            out.append(("math", text[i : j + 1]))
            i = j + 1
        elif text.startswith("\\ce{", i) or text.startswith("\\ce ", i):
            depth, j = 0, text.find("{", i)
            k = j
            while k < len(text):
                depth += {"{": 1, "}": -1}.get(text[k], 0)
                k += 1
                if depth == 0:
                    break
            flush()
            out.append(("ce", text[i:k]))
            i = k
        else:
            buf.append(text[i])
            i += 1
    flush()
    return out


def tidy(text: str) -> str:
    """Common clean-up of every text field."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\$\$(.*?)\$\$", lambda m: "\\[\n" + m.group(1).strip() + "\n\\]", text, flags=re.S)
    for pat, new in HTML:
        text = pat.sub(new, text)
    text = BOLD.sub(r"\\textbf{\1}", text)
    held: list[str] = []

    def hold(m: re.Match) -> str:
        held.append(smiles_tt(m.group(1)))
        return PLACEHOLDER.format(len(held) - 1)

    text = SMILES_TAG.sub(hold, text)
    text = pu_text(text)
    parts = []
    for kind, seg in segments(text):
        if kind == "prose":
            parts.append(_prose(seg))
        elif kind == "math":
            parts.append(re.sub(r"(?<!\\)%", r"\\%", _unicode_math(seg)))
        else:
            parts.append(seg)
    text = "".join(parts)
    text = PLACEHOLDER_RE.sub(lambda m: held[int(m.group(1))], text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ----------------------------------------------------------------------------------- structure drawings

DRAWN: dict[str, tuple[str, bytes] | None] = {}  # SMILES -> (image name, PNG) or None when RDKit cannot read it
WANTED: set[str] = set()  # SMILES met while loading that are not drawn yet


def smiles_in(raw: str) -> list[str]:
    """The SMILES strings (tags) of one raw field, in order."""
    return [m.group(1).strip().replace("\n", "") for m in SMILES_TAG.finditer(raw)]


def figures(raw: str) -> tuple[str, list[tuple[str, bytes]]]:
    """(paragraphs with one drawing per SMILES of the raw field, images); a SMILES not drawn yet is noted for the
    next pass, one RDKit cannot read keeps its text only."""
    from app.tools.import_answer_sets import GRAPHIC

    paras, images = [], []
    for s in smiles_in(raw):
        if s not in DRAWN:
            WANTED.add(s)
        elif DRAWN[s]:
            name, png = DRAWN[s]
            paras.append(GRAPHIC.format(name))
            images.append((name, png))
    return "\n\n".join(paras), images


def draw_pending() -> None:
    from app.tools.smiles_draw import draw_many, image_name

    for s, png in draw_many(sorted(WANTED)).items():
        DRAWN[s] = (image_name(png), png) if png else None
    WANTED.clear()


def mc_statement(stem: str, options: list[tuple[str, str]], letters: list[str], stem_fig: str = "",
                 opt_figs: dict[str, str] | None = None) -> str:
    low = stem.lower()
    note = ""
    if len(letters) == 1 and not re.search(r"exactly one|only one|one or more|multiple|all that apply", low):
        note = "Exactly one option is correct."
    elif len(letters) > 1 and not re.search(r"one or more|multiple|all that apply|more than one", low):
        note = "One or more options may be correct."
    opt_figs = opt_figs or {}
    parts = [stem, stem_fig] + ([note] if note else [])
    parts += [f"({x}) {t}" + (f"\n\n{opt_figs[x]}" if opt_figs.get(x) else "") for x, t in options]
    return "\n\n".join(p for p in parts if p)


def make_row(set_: str, idx: str, sub: str, stem: str, answer: str, solution: str | None, ref: str, key: str) -> dict:
    return {"potd": key, "set": set_, "idx": idx, "orig": "", "source": set_, "subsource": sub, "latexcode": stem,
            "answer": answer, "solution": solution, "hints": None, "more_hints": None, "ref_solution": ref,
            "group": "subject", "effort": None, "image": None}


def apply_fixes(row: dict) -> None:
    for fld in ("latexcode", "answer", "solution", "ref_solution"):
        for old, new in HAND_FIXES.get((row["potd"], fld), []):
            if row[fld] is None or row[fld].count(old) != 1:
                raise SystemExit(f"HAND FIX {row['potd']} {fld}: expected one {old!r}")
            row[fld] = row[fld].replace(old, new)
    if (row["potd"], "solution") in HAND_FIXES and row["solution"]:
        row["ref_solution"] = row["solution"]


def solution_ok(row: dict, sol: str | None) -> str | None:
    """The solution to store: long enough, and clean under the text check."""
    if not sol or len(sol) < MIN_SOLUTION or row["potd"] in SOLUTION_DROPS:
        return None
    return None if check([dict(row, solution=sol)]) else sol


# -------------------------------------------------------------------------------------------------- SciBench

SCI_BOOKS = {
    "atkins": "Atkins, Physical Chemistry",
    "matter": "Atkins, Quanta, Matter and Change",
    "quan": "Levine, Quantum Chemistry",
    "chemmc": "McQuarrie and Simon, Physical Chemistry: A Molecular Approach",
}
UNIT_OVERRIDES = {("chemmc", "1-41"): r"\mathrm{J}", ("chemmc", "1-39"): r"\mathrm{J}"}  # "per particle" / "per electron"
NUM_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")
SCI_UNIT_FIX = {"kPA": "kPa", "KJ": "kJ"}


def sci_unit(u: str) -> tuple[str | None, str]:
    """(power-of-ten exponent or None, unit LaTeX) from the dataset's unit field."""
    u = " ".join(u.replace("$", " ").replace("~", "").replace("{ }", "").split())
    u = re.sub(r"\\text\s*\{([^{}]*)\}", r"\\mathrm{\1}", u)
    for a, b in SCI_UNIT_FIX.items():
        u = u.replace(a, b)
    u = re.sub(r"\\mathrm\{\s*([A-Za-z]*)\s*\}", r"\\mathrm{\1}", u)
    exp = None
    if m := re.match(r"^10\^\{?(-?\d+)\}?\s*(.*)$", u):
        exp, u = m.group(1), m.group(2).strip()
    u = u.replace(r"\mathrm{JK}", r"\mathrm{J}\,\mathrm{K}")
    if u and "\\" not in u and "{" not in u:
        u = r"\mathrm{" + u + "}"
    u = re.sub(r"(\\mathrm\{[^{}]*\}(?:\^\{[^{}]*\}|\^\d)?)\s*(?=\\mathrm)", r"\1\\,", u)
    return exp, u.strip()


def sci_answer(r: dict, ds: str, pid: str) -> str:
    a = r["answer_latex"].replace("\x0c", "\\f").strip().strip("$").strip().lstrip("+").strip()
    exp, unit = sci_unit(r["unit"])
    unit = UNIT_OVERRIDES.get((ds, pid), unit)
    if exp is not None:
        a = rf"{a}\times 10^{{{exp}}}" if NUM_RE.match(a) else rf"({a})\times 10^{{{exp}}}"
    if not unit and exp is None and NUM_RE.match(a):
        return a
    return f"${a}\\ {unit}$" if unit else f"${a}$"


def sci_number_ok(r: dict) -> bool:
    """The dataset's two answer fields agree (a plain-number answer_latex against answer_number)."""
    a = r["answer_latex"].strip().strip("$").strip()
    m = re.fullmatch(r"([+-]?[\d.]+)(?:\s*\\times\s*10\^\{?(-?\d+)\}?)?", a)
    if not m:
        return True
    try:
        v = float(m.group(1)) * 10 ** int(m.group(2) or 0)
        n = float(r["answer_number"].strip())
    except ValueError:
        return True
    return abs(v - n) <= 0.02 * max(abs(n), 1e-12) + 1e-12


def load_scibench(data: Path) -> tuple[list[dict], dict[str, str]]:
    rows, dropped, seen = [], {}, collections.Counter()
    for ds in SCI_BOOKS:
        for suf in ("", "_sol"):
            for r in json.loads((data / "scibench" / f"{ds}{suf}.json").read_text(encoding="utf-8")):
                pid = r["problemid"].strip()
                key = f"SciBench {ds} {pid}"
                seen[key] += 1
                if seen[key] > 1:
                    key += f" ({seen[key]})"
                if "Math Part D" in r["comment"]:
                    dropped[key] = "pure mathematics review item, not chemistry"
                    continue
                if key in DROPS:
                    dropped[key] = DROPS[key]
                    continue
                if not sci_number_ok(r):
                    dropped[key] = "the two answer fields disagree"
                    continue
                stem = tidy(r["problem_text"])
                sol = tidy(r["solution"]) if r["solution"].strip() and key not in SOLUTION_DROPS else ""
                row = make_row("SciBench", pid, f"{SCI_BOOKS[ds]}, problem {pid}", stem, sci_answer(r, ds, pid), None, sol, key)
                apply_fixes(row)
                row["solution"] = solution_ok(row, row["ref_solution"]) if row["ref_solution"] else None
                rows.append(row)
    return rows, dropped


# ------------------------------------------------------------------------------------------------ ChemBench

CB_TOPICS = {
    "analytical_chemistry": "Analytical chemistry",
    "general_chemistry": "General chemistry",
    "inorganic_chemistry": "Inorganic chemistry",
    "materials_science": "Materials science",
    "organic_chemistry": "Organic chemistry",
    "physical_chemistry": "Physical chemistry",
    "technical_chemistry": "Technical chemistry",
}
SCI_NUM_RE = re.compile(r"^([+-]?\d+(?:\.\d+)?)[eE]([+-]?\d+)$")


def load_chembench(data: Path) -> tuple[list[dict], dict[str, str]]:
    import pyarrow.parquet as pq

    rows, dropped = [], {}
    for cfg, topic in CB_TOPICS.items():
        for r in pq.read_table(data / "chembench" / f"{cfg}.parquet", columns=["examples", "name", "uuid"]).to_pylist():
            e = r["examples"][0]
            key = f"ChemBench {r['uuid']}"
            if key in DROPS:
                dropped[key] = DROPS[key]
                continue
            raw = e["input"]
            if BAD_SMILES_TAG.search(SMILES_TAG.sub("", raw)):
                dropped[key] = "unbalanced structure tag in the statement"
                continue
            stem = tidy(raw)
            sub = f"{topic}, {r['name'].replace('_', ' ')}"
            if e["target_scores"]:
                scores = json.loads(e["target_scores"])
                items = list(scores.items())
                letters = [chr(65 + i) for i, (_, v) in enumerate(items) if v and v > 0]
                if not letters or len(items) > 26:
                    dropped[key] = "no keyed option"
                    continue
                if len(letters) == len(items) and len(items) > 1:
                    dropped[key] = "every option is keyed correct"
                    continue
                opts = [(chr(65 + i), tidy(t)) for i, (t, _) in enumerate(items)]
                if any(not t for _, t in opts) or len({t for _, t in opts}) != len(opts):
                    dropped[key] = "empty or repeated options"
                    continue
                stem_fig, imgs = figures(raw)
                opt_figs = {}
                for i, (t, _) in enumerate(items):
                    opt_figs[chr(65 + i)], more = figures(t)
                    imgs += more
                row = make_row("ChemBench", r["uuid"], sub, mc_statement(stem, opts, letters, stem_fig, opt_figs),
                               ", ".join(letters), None, "", key)
                row["image"] = list(dict(imgs).items()) or None
            else:
                t = (e["target"] or "").strip()
                if m := SCI_NUM_RE.match(t):
                    t = f"${m.group(1)}\\times 10^{{{int(m.group(2))}}}$"
                if not t:
                    dropped[key] = "no key"
                    continue
                stem_fig, imgs = figures(raw)
                row = make_row("ChemBench", r["uuid"], sub, stem + (f"\n\n{stem_fig}" if stem_fig else ""), t, None, "", key)
                row["image"] = list(dict(imgs).items()) or None
            apply_fixes(row)
            rows.append(row)
    return rows, dropped


# ------------------------------------------------------------------------------------------------ SUPERChem

MM_RE = re.compile(r"<MultiModal>!\[(.*?)\]\(/media/uploads/[^)\s]*\)</MultiModal>", re.S)
CHECKPOINT_RE = re.compile(r"<Checkpoint>.*?</Checkpoint>", re.S)
ZH_RE = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")
SMILESISH = re.compile(r"^[A-Za-z0-9@+\-\[\]()=#%/\\.:,*$~>|{}\s^_]+$")


def figure_text(alt: str) -> str | None:
    """The text version of one figure, as text tidy() understands; None when it has none (Chinese)."""
    a = alt.strip()
    if ZH_RE.search(a):
        return None
    m = re.match(r"^Image is a molecular formula, SMILES code is\s*(.+)$", a, re.S)
    if m:
        return f"[START_SMILES]{m.group(1)}[END_SMILES]"
    if " " not in a.replace("\n", "") and SMILESISH.match(a):
        return f"[START_SMILES]{a}[END_SMILES]"
    return a


def superchem_text(text: str, strict: bool = True) -> str | None:
    """One field with its figures replaced by their text versions; a figure without one makes a strict
    field None (a lenient one just loses the figure)."""
    bad = []

    def sub(m: re.Match) -> str:
        t = figure_text(m.group(1))
        if t is None:
            bad.append(m.group(1))
        return t or ""

    out = MM_RE.sub(sub, text)
    return None if bad and strict else tidy(out)


def load_superchem(data: Path) -> tuple[list[dict], dict[str, str]]:
    import pyarrow.parquet as pq

    cols = ["uuid", "question_en", "options_en", "answer_en", "explanation_en"]
    rows, dropped = [], {}
    table = pq.read_table(data / "superchem" / "SUPERChem-500.parquet", columns=cols).to_pylist()
    for n, r in enumerate(table, 1):
        key = f"SUPERChem {r['uuid'][:8]}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        opts_raw = [(k, v) for k, v in r["options_en"].items() if v]
        if any(re.search(r"<request_id>|\[Error", v) for _, v in opts_raw):
            dropped[key] = "an option is an API error message in the dataset"
            continue
        if len(r["answer_en"]) != 1 or r["answer_en"][0] not in {k for k, _ in opts_raw}:
            dropped[key] = "key not among the options"
            continue
        stem = superchem_text(r["question_en"])
        opts = [(k, superchem_text(v)) for k, v in opts_raw]
        if stem is None or any(t is None or not t for _, t in opts):
            dropped[key] = "a figure has no usable text version (Chinese or missing)"
            continue
        if ZH_RE.search(stem) or any(ZH_RE.search(t) for _, t in opts):
            dropped[key] = "Chinese text in the English statement"
            continue
        letters = [r["answer_en"][0]]
        sc_raw = lambda t: MM_RE.sub(lambda m: figure_text(m.group(1)) or "", t)  # noqa: E731
        stem_fig, imgs = figures(sc_raw(r["question_en"]))
        opt_figs = {}
        for k, v in opts_raw:
            opt_figs[k], more = figures(sc_raw(v))
            imgs += more
        sol_raw = CHECKPOINT_RE.sub("", r["explanation_en"] or "")
        sol = superchem_text(sol_raw, False) or ""
        sol = re.sub(r"[ \t]*\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", sol)
        if ZH_RE.search(sol):
            sol = ""
        sub = f"SUPERChem-500, question {n}"
        row = make_row("SUPERChem", r["uuid"], sub, mc_statement(stem, opts, letters, stem_fig, opt_figs),
                       letters[0], None, sol, key)
        row["image"] = list(dict(imgs).items()) or None
        apply_fixes(row)
        row["solution"] = solution_ok(row, row["ref_solution"])
        rows.append(row)
    return rows, dropped


# ------------------------------------------------------------------------------------------------------ main

LOADERS = {"scibench": load_scibench, "chembench": load_chembench, "superchem": load_superchem}


def load(data: Path, only: list[str]) -> tuple[list[dict], dict[str, str]]:
    rows, dropped = [], {}
    for _ in range(2):  # the first pass finds the SMILES, the drawings are made, the second pass uses them
        rows, dropped = [], {}
        for name in only:
            r, d = LOADERS[name](data)
            rows += r
            dropped |= d
        if not WANTED:
            break
        draw_pending()
    seen: dict[str, str] = {}
    out = []
    for r in rows:  # the same statement twice inside the datasets: keep the first
        h = latex_hash(r["latexcode"])
        if h in seen:
            dropped[r["potd"]] = f"same statement as {seen[h]}"
            continue
        seen[h] = r["potd"]
        out.append(r)
    return out, dropped


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", choices=DATASETS, action="append", help="a dataset to read (repeatable; default all)")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped = load(a.data, a.only or list(DATASETS))
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for key, why in sorted(dropped.items()):
        print(f"dropped: {key}: {why}")
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why],
                                             ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    reasons = collections.Counter(re.sub(r"\d+", "N", v) for v in dropped.values())
    print(json.dumps({
        "rows_kept_before_bank": len(rows), "dropped": len(dropped), "dropped_by_reason": reasons, "in_bank": len(dup),
        "to_add": len(new), "check_problems": len(problems),
        "with_stored_solution": sum(bool(r["solution"]) for r in new),
        "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
        "by_set": collections.Counter(r["set"] for r in new),
        "rows_with_drawings": sum(bool(r["image"]) for r in new),
        "drawings": len({n for r in new for n, _ in r["image"] or []}),
        "smiles_not_drawn": sum(v is None for v in DRAWN.values())}, default=dict))
    if a.dump:
        a.dump.write_text(json.dumps([dict(r, image=[n for n, _ in r["image"]] if r["image"] else None) for r in new],
                                     ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("chembench")
    for r in new:  # drawings, before their questions exist
        for name, png in r["image"] or []:
            (TEXIMAGES / f"{name}.png").write_bytes(png)
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in new:
            h = latex_hash(r["latexcode"])
            if h in existing:
                continue
            cur = conn.execute(
                """INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                          source, subsource, answer, solution, hints, more_hints, latex_hash)
                   VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)""",
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"], r["answer"],
                 r["solution"], r["hints"], r["more_hints"], h))
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
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
