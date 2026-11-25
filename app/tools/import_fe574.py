"""
Import 0xZee/dataset-CoT-Engineering-574: FE-exam style multiple choice with worked solutions
-----------------------------------------------------------------------------------------------
huggingface.co/datasets/0xZee/dataset-CoT-Engineering-574 (no licence stated; derived from an FE exam review book;
Amplify is private; personal use). 574 rows (571 distinct questions): question with options (A)-(E), response = the
book's worked solution ending "The answer is (X).", CoT = a model's chain of thought (not used). Mixed engineering
disciplines (thermodynamics, fluids, circuits, statics, controls, chemical engineering, mathematics ...): all go to
group "subject"; the classifier decides the subject afterwards. Owner 2026-11-25: expand mechanical, power plant,
electronics, ... engineering.

Source "0xZee CoT Engineering-574" (the dataset's name), subsource None (a question id would identify it); idx is a
hash of the question.

Conversions:
  * The file holds LaTeX with the two characters backslash-n for line ends (a literal \\n that is not \\neq, \\nu, ...
    is turned back into a newline); \\( \\) become $ $, \\[ \\] stay displays in the stem and become inline in options;
    **bold** becomes \\textbf; markdown bullets and headings are removed; unicode symbols become math; % # & escaped.
  * Statement: stem, "Exactly one option is correct.", then the options each as "(A) ...", one per line with a blank
    line between. Key: the letter of "The answer is (X)".
  * Solution: the response without its last line, stored when it has at least 150 characters (also kept in
    ref_solution).
  * Dropped: rows with a figure stub (![Diagram A](#)) or that point to a figure or table, rows whose options cannot be
    split or whose answer letter is missing, characters with no LaTeX form here, near-duplicates (85% of 5-word
    shingles) inside the set.
Rows the bank already has are skipped and listed. On --apply: backup, insert (Uncategorized), append to
benchmarks_map.csv, keep ref_solution in benchmarks_solutions.json. Nothing goes into benchmarks_assignments.json.

Usage (repo root):
  python -m app.tools.import_fe574 --data DIR --dry-run [--dump rows.json] [--set-aside [--exclude fails.json]]
  python -m app.tools.import_fe574 --data DIR --apply
DIR holds Engineering-574.parquet (or any *.parquet of the dataset).
"""

from __future__ import annotations

import collections
import hashlib
import re
import unicodedata
from pathlib import Path

from app.tools.import_eri import (
    MIN_SOLUTION,
    apply_fixes,
    dedupe_own,
    run,
    sym,
    tex_plain,
)
from app.tools.import_supergpqa import FIGURE_RE

SET = "0xZee Engineering-574"
SOURCE = "0xZee CoT Engineering-574"
SET_ASIDE_PATH = Path("app/data/appdata/fe574_set_aside.json")
STATS: collections.Counter = collections.Counter()

NL_KEEP = r"(?:eq|ne|nu|abla|ewline|ot|otin|ni|less|leq|geq|gtr|parallel|mid|cong|sim|rightarrow|Rightarrow|leftarrow|subset|supset)"
LITERAL_NL = re.compile(r"\\n(?!" + NL_KEEP + r"(?![A-Za-z]))")
ANSWER_RE = re.compile(r"answer\s+is\s*(?:option\s*)?\(?([A-J])\)?", re.I)
ANSWER_LINE_RE = re.compile(r"\n*\**\s*The answer is[^\n]*$", re.I)
OPT_RE = re.compile(r"(?<![\w)])(?:[-*][ \t]+)?\(([A-J])\)[ \t]+")
MATH_RE = re.compile(r"(\\\(.*?\\\)|\\\[.*?\\\]|\$\$.*?\$\$|\$[^$\n]*\$)", re.S)
FIG_WORD_RE = re.compile(r"(?:diagrams?|(?:this|the\s+given)\s+(?:beam|truss|circuit|frame|structure|mechanism|network|system of)|the\s+(?:figure|diagram|graph|plot|table|chart)\b|diagram\s+[A-Z]\b|\bfigure\s+[A-Z0-9])", re.I)


GREEK = {n: ("GREEK SMALL LETTER " if n[0].islower() else "GREEK CAPITAL LETTER ") + n.upper() for n in (
    "alpha beta gamma delta epsilon theta lambda mu nu pi rho sigma tau phi omega Delta Omega Sigma Phi Gamma").split()}


def unesc(s: str) -> str:
    return LITERAL_NL.sub("\n", s)


TEXT_BOX_RE = re.compile(r"(\\(?:text|mathrm|textbf|mbox)\{[^{}]*\})")


def uni_math(m: str) -> str:
    """Unicode symbols in math become commands; inside \\text{...} they become inline math."""
    out = []
    for i, part in enumerate(TEXT_BOX_RE.split(m)):
        for c in part:
            if ord(c) < 128 or unicodedata.category(c).startswith("L"):
                out.append(c)
            else:
                out.append("$" + sym(c) + "$" if i % 2 else sym(c) + " ")
    return "".join(out)


def prose(p: str, escape_amp: bool) -> str:
    p = p.replace("**", "")
    p = re.sub(r"\\(" + "|".join(GREEK) + r")(?![A-Za-z])", lambda m: unicodedata.lookup(GREEK[m.group(1)]), p)
    p = re.sub(r"(?m)^#{1,6}\s*", "", p)
    p = re.sub(r"(?m)^[ 	]*[-*][ 	]+", "", p)
    out = tex_plain(p, strip=False)
    return out if escape_amp else out.replace(r"\&", "&")


def tex(text: str, inline: bool = False) -> str:
    """Convert one field; inline: displays become inline math and the text is one line."""
    text = unesc(text).replace("\r", "")
    escape_amp = "\\begin{" not in text
    out = []
    for i, part in enumerate(MATH_RE.split(text)):
        if i % 2 == 0:
            out.append(prose(part, escape_amp))
            continue
        disp = part.startswith("\\[") or part.startswith("$$")
        inner = part[2:-2] if part.startswith(("\\(", "\\[", "$$")) else part[1:-1]
        inner = uni_math(re.sub(r"(?<!\\)%", r"\\%", inner)).strip()
        if not inner:
            continue
        if disp and not inline:
            out.append("\n\\[\n" + inner + "\n\\]\n")
        else:
            out.append("$" + re.sub(r"\s*\n\s*", " ", inner) + "$")
    t = "".join(out)
    if inline:
        t = re.sub(r"\s*\n\s*", " ", t)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", t)).strip()


def split_options(q: str) -> tuple[str, list[str]] | None:
    ms = list(OPT_RE.finditer(q))
    # the options are the last run A, B, C ... in order
    for start in range(len(ms)):
        run_ = ms[start:]
        if [m.group(1) for m in run_] == [chr(65 + i) for i in range(len(run_))] and len(run_) >= 2:
            stem = q[: run_[0].start()].strip()
            opts = [
                q[m.end() : (run_[k + 1].start() if k + 1 < len(run_) else len(q))].strip().rstrip(",;").strip()
                for k, m in enumerate(run_)
            ]
            return stem, opts
    return None


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    import pyarrow.parquet as pq

    path = data if data.is_file() else next(data.rglob("*.parquet"))
    rows, dropped, seen = [], {}, set()
    for r in pq.read_table(path).to_pylist():
        q, resp = unesc(r["question"]).strip(), unesc(r["response"]).strip()
        h = hashlib.sha1(q.encode("utf-8")).hexdigest()
        lab = f"FE574 {h[:10]}"
        STATS["rows"] += 1
        if h in seen:
            dropped[lab] = "same question twice in the dataset"
            continue
        seen.add(h)
        if "](#)" in q + resp or "![" in q + resp:
            dropped[lab] = "figure stub (![Diagram](#))"
            continue
        if FIGURE_RE.search(q) or FIG_WORD_RE.search(q):
            dropped[lab] = "needs a figure or table the dataset does not carry"
            continue
        m = ANSWER_RE.findall(resp)
        if not m:
            dropped[lab] = "no answer letter in the response"
            continue
        letter = m[-1].upper()
        sp = split_options(q)
        if sp is None:
            dropped[lab] = "options cannot be split"
            continue
        stem, opts = sp
        if ord(letter) - 65 >= len(opts):
            dropped[lab] = "answer letter outside the options"
            continue
        try:
            stem_t = tex(stem)
            opts_t = [tex(o, inline=True) for o in opts]
            sol = tex(ANSWER_LINE_RE.sub("", resp))
        except ValueError as e:
            dropped[lab] = str(e)
            continue
        if "\\textbackslash" in stem_t + "".join(opts_t):
            dropped[lab] = "TeX commands outside math in the dataset text"
            continue
        if "\\textbackslash" in sol or ("\\hline" in sol and "\\\\" not in sol):
            sol = ""  # the book's solution is broken TeX: the solver writes one
        if not stem_t or any(not o for o in opts_t):
            dropped[lab] = "empty stem or option"
            continue
        note = [] if re.search(r"exactly one|only one correct", stem_t, re.I) else ["Exactly one option is correct."]
        text = "\n\n".join([stem_t, *note, *(f"({chr(65 + i)}) {o}" for i, o in enumerate(opts_t))])
        row = {
            "potd": lab,
            "set": SET,
            "idx": h[:10],
            "orig": "",
            "source": SOURCE,
            "subsource": None,
            "latexcode": text,
            "answer": letter,
            "solution": sol if len(sol) >= MIN_SOLUTION else None,
            "hints": None,
            "more_hints": None,
            "ref_solution": sol,
            "group": "subject",
            "effort": None,
            "image": None,
        }
        apply_fixes(row, h[:10])
        rows.append(row)
    return dedupe_own(rows, dropped), dropped


def main() -> None:
    run(load, "fe574", SET_ASIDE_PATH, __doc__, lambda r: "FE-574", STATS)


if __name__ == "__main__":
    main()
