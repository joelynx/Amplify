"""
Import Strang, *Introduction to Linear Algebra* (5th ed.), problem sets
------------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book's Problem Sets 1.1-12.3 (one .tex
file plus an images/ folder; the PDF holds only the problem-set pages) and adds
every problem to amplify.db. The book prints no answers or solutions here.

Layout of the export:
    <main text>                        worked examples or notes of the neighbouring section
                                       that share a page with the problems (dropped; see
                                       MAIN_TEXT_STARTS)
    \\section*{Problem Set 2.4}
    Problems 1-16 are about ...         a group heading (also as \\section*{...})
    \\begin{itemize}
      \\item[3] Add ...                 a problem, or
      \\item[] \\(12 A\\) and ...         the same with its number swallowed into math, or
    27 For two linear ...               the same as a plain line
    \\section*{Challenge Problems}       (numbering continues)

Repairs made on the way in:
  * The PDF lacks book page 214, which holds the header of Problem Set 4.2 and
    its problem 1; the set starts at problem 2 here (LOST_HEADERS).
  * Group headings are dropped when they only name the topic ("Problems 1-9 are
    about addition of vectors"). Those that give the problems something they
    need (data, notation, a figure, a definition, a required method) are put
    at the top of each problem in their range (KEPT_HEADINGS), e.g. the data
    points of 4.3, the graphs of 10.1 and the eight vector-space rules of 3.1.
  * Figures that belong to a heading are moved to it (FIGURE_TARGETS); those in
    the dropped main text go with it.
  * A problem whose text starts with "(a)" and whose parts continue in a list
    from (b) gets (a) moved into that list.
  * Stray "\\\\" lines (Mathpix's line breaks around displays) are dropped, and
    a "\\\\" that breaks a sentence is joined up.
  * Misreads found by checking every problem against the book pages are
    corrected from strang_fixes.json (page and reason on each); kind
    "structure" fixes repair the raw export before it is parsed. Most are
    matrices and column vectors whose rows ran together (lost \\\\ row
    breaks), blanks that were dropped or read as \\ldots, and the vectors of
    3.5.5, 3.5.21 and 3.5.22, whose entries the book prints overlapping. The
    boxed passage "The Minimum of a Function" (main text) is cut from 6.5.31.
  * The book's own errors are corrected too (fixes of kind "book", each with
    its reason): wrong formulas (7.4.3, 11.3.25, 12.1.9, 12.2.5, 12.2.9,
    12.3.5, 3.2.57), a non-Hermitian "Hermitian" matrix (9.2.14), wrong
    numbers and references (3.3.9, 6.3.29, 2.7.31, 7.4.20), matrix names left
    over from the 4th edition (2.3.31, 6.5.x), and typos. Problem 1.2.26 is
    only the first words of 1.2.27, so it is joined to it (field "drop"), and
    the heading "Questions 9-16 are about the conjugate" covers 9-14 (field
    "range"; 15-16 belong to the next heading).

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings
(run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. Referenced images are copied to
app/data/appdata/teximages/ and Files/images/.

Usage (repo root):
  python -m app.tools.import_strang --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_strang --tex <export.tex> --apply
  python -m app.tools.import_strang --tex <export.tex> --update book   (rows already imported)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

from app.persistence.ingest.seed import latex_hash

# Existing labels: "Surname's Title".
SOURCE = "Strang's Introduction to Linear Algebra"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")
TEXIMAGES = Path("app/data/appdata/teximages")
REPO_IMAGES = Path("Files/images")

SECTIONS = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7",
            "3.1", "3.2", "3.3", "3.4", "3.5", "4.1", "4.2", "4.3", "4.4", "5.1", "5.2", "5.3",
            "6.1", "6.2", "6.3", "6.4", "6.5", "7.1", "7.2", "7.3", "7.4", "8.1", "8.2", "8.3",
            "9.1", "9.2", "9.3", "10.1", "10.2", "10.3", "10.4", "10.5", "10.6", "10.7",
            "11.1", "11.2", "11.3", "12.1", "12.2", "12.3"]
PS_RE = re.compile(r"^\\section\*\{Problem Set (\d+\.\d+)\}$")

# Sections whose header is on a page the PDF lacks: the line that starts their
# first problem in the export, and that problem's number.
LOST_HEADERS = {
    "4.2": ("  \\item[2] Draw the projection of \\(\\boldsymbol{b}\\) onto \\(\\boldsymbol{a}\\)", 2),  # book p. 214
}

# The main text sharing a page with the problems: the start of its first line,
# and how many lines before that line also belong to it. Everything from there
# to the next Problem Set is dropped.
MAIN_TEXT_STARTS = [
    ("1.2 B Find a unit vector", 0),
    ("For the second system, subtract equation 1 from equation 2 as before.", 0),  # 2.2 B
    ("\\(\\left(S^{2}\\right)_{i j}\\) is adding up 1's for all the 2-step paths", 0),  # 2.4 A
    ("Forward elimination is multiplication by \\(L^{-1}\\).", 0),  # 2.6 A
    ("  \\item[2.7] C For a rectangular \\(A\\), this saddle-point matrix", 1),  # and its \begin{itemize}
    ("\\section*{The Transpose of a Derivative}", 0),
    ("3.2 C Find the row reduced form \\(R\\)", 0),
    ("\\(R \\boldsymbol{x}=\\boldsymbol{d}\\) shows that the particular solution", 0),  # 3.3 A
    ("3.5 B Fact: All the rows of \\(A B\\)", 0),
    ("Those zeros in \\(A^{\\mathrm{T}} A\\) mean that column 2", 0),  # 4.3 B
    ("Solution \\(H_{4}\\) can be built from \\(H_{2}\\)", 0),  # 4.4 A
    ("  \\item[5.1] B Explain how to reach this determinant", 1),
    ("Solution The cofactor \\(C_{11}\\) for \\(H_{4}\\)", 0),  # 5.2 A
    ("The cofactors along the other rows of \\(A\\), divided by", 0),  # 5.3 A
    ("  \\item[6.1] C Find the eigenvalues and eigenvectors of this symmetric", 1),
    ("\\section*{Eigshow in MATLAB}", 0),
    ("If \\(\\boldsymbol{A}\\) is \\(\\boldsymbol{m}\\) by \\(\\boldsymbol{n}\\) and", 0),  # 6.3 A
    ("\\section*{Notes on a Differential Equations Course}", 0),
    ("7.2 B Show that \\(\\sigma_{1} \\geq", 0),
    ("Solution If \\(A\\) has independent columns then", 0),  # 7.4 A
    ("\\section*{■ WORKED EXAMPLES ■}", 0),
    ("We will count the individual multiplications, to see how much is saved.", 0),  # 9.3
    ("Current Law \\(A^{\\mathrm{T}} \\boldsymbol{y}=\\mathbf{0}\\), we get", 0),  # 10.1
    ("Note The stoichiometric matrix in chemistry", 0),
    ("If you multiply the series \\(S=I+A+A^{2}+\\cdots\\) by \\(A\\)", 0),  # 10.3
    ("in \\((\\boldsymbol{x}+\\Delta \\boldsymbol{x})(s+\\Delta s)", 0),  # 10.4
    ("basis vectors are orthogonal. We are just doing one-dimensional projections", 0),  # 10.5
    ("\\section*{■ REVIEW OF THE KEY IDEAS ■}", 0),
    ("Add & 0 & 1 & \\(a\\) & \\(1+a\\) \\\\", 3),  # 10.7, the tables of GF(4)
    ("subdiagonal). The zeros in the lower left corner will stay zero", 0),  # 11.3
    ("The idea is that \\(x-y\\) has a smaller variance", 0),  # 12.1
    ("Yes, we could just solve that new problem and forget the old one.", 21),  # 12.3, from equation (16)
]

# Group headings: "Problems 1-9 are about ...", also as \section*{...}.
HEADING_RE = re.compile(r"^(?:\\section\*\{)?(?:Problems|Questions|The first problems|The next three questions) ")

# Headings kept at the top of each problem in their range: (section, start of
# the heading line) -> (first, last) problem.
KEPT_HEADINGS = {
    ("1.1", "Problems 10-14 are about special vectors on cubes"): (10, 14),
    ("1.1", "\\section*{Problems 15-19 go further"): (15, 19),
    ("1.1", "Problems 20-25 deal with"): (20, 25),
    ("2.4", "Problems 18-20 use"): (18, 20),
    ("2.6", "\\section*{Problems 15-16 use"): (15, 16),
    ("2.7", "The next three questions"): (29, 31),
    ("3.1", "The first problems 1-8"): (1, 8),
    ("3.2", "Questions 15-22 ask for matrices (if possible)"): (15, 22),
    ("3.3", "Questions 3-15 are about the solution"): (3, 15),
    ("4.3", "Problems 1-11 use four data points"): (1, 11),
    ("4.4", "\\section*{Problems 26-29 use the"): (26, 29),
    ("5.2", "Problems 1-10 use the big formula"): (1, 10),
    ("5.2", "Problems 11-22 use cofactors"): (11, 22),
    ("5.3", "Problems 6-15 are about"): (6, 15),
    ("6.5", "Problems 21-24 use the eigenvalues"): (21, 27),
    ("7.4", "Problems 5-9 are about the SVD of an invertible matrix."): (5, 9),
    ("8.1", "Problems 13-19 may be harder."): (13, 19),
    ("8.1", "Questions 20-26 are about house transformations."): (20, 26),
    ("8.2", "Questions 20-23 are about the space of quadratic"): (20, 23),
    ("9.1", "Questions 9-16 are about the conjugate"): (9, 16),
    ("10.1", "Problems 1-7 and 8-14 are about the incidence"): (1, 14),
    ("11.3", "\\section*{Problems 22-25 present two fundamental"): (22, 25),
    ("12.2", "Problems 5-9 are about the conditional probability"): (5, 9),
}

# Figures moved out of the text flow: image name -> the kept heading
# (section, start of its line) whose note gets the figure, or the problem key.
FIGURE_TARGETS = {
    "17c69bd8-8a07-40cf-a4a8-dab124bb28b0-002_477_1291_233_391": ("1.1", "Problems 10-14 are about special vectors on cubes"),
    "17c69bd8-8a07-40cf-a4a8-dab124bb28b0-002_402_457_1833_531": ("1.1", "\\section*{Problems 15-19 go further"),
    "17c69bd8-8a07-40cf-a4a8-dab124bb28b0-002_436_474_1832_1066": ("1.1", "Problems 20-25 deal with"),
    "17c69bd8-8a07-40cf-a4a8-dab124bb28b0-006_328_846_1507_883": "1.2.23",  # the angles of Problem 23
    "17c69bd8-8a07-40cf-a4a8-dab124bb28b0-077_472_651_1200_414": "4.2.5",  # "Questions 5-6-7: orthogonal"
    "17c69bd8-8a07-40cf-a4a8-dab124bb28b0-077_454_441_1210_1230": "4.2.8",  # "Questions 8-9-10: not orthogonal"
}

CHALLENGE = "\\section*{Challenge Problems}"
TOP_ITEM_RE = re.compile(r"^  \\item\[(\d+)\]\s?(.*)$")
SWALLOWED_RE = re.compile(r"^  \\item\[\] \\\((\d+)\s+(.*)$")  # \item[] \(12 A\) and ...
EMPTY_ITEM_RE = re.compile(r"^  \\item\[\]\s*$")
PLAIN_RE = re.compile(r"^(\d{1,2}) (?=[A-Za-z(]|\\\(|\\_)(.*)$")
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BREAK_LINE_RE = re.compile(r"^\s*\\\\(?:\[0pt\])?\s*$")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")

FIXES_PATH = Path(__file__).with_name("strang_fixes.json")


def _clean(text: str) -> str:
    lines = [ln for ln in text.split("\n") if not BREAK_LINE_RE.match(ln)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    # a forced break in mid-sentence (the book's line end)
    text = re.sub(r"([A-Za-z])-\\\\\s*\n([a-z])", r"\1\2", text)
    text = re.sub(r"\s*\\\\\s*\n(?=[a-z])", " ", text)
    text = re.sub(r"\n\s*\n(\s*\\(?:end\{itemize\}|item\[))", r"\n\1", text)
    text = TRAILING_BREAK_RE.sub("", text)
    return text.strip()


def _lift_part_a(text: str) -> tuple[str, bool]:
    """'(a) X ... \\begin{itemize} \\item[(b)] Y' -> '\\begin{itemize} \\item[(a)] X ... \\item[(b)] Y'."""
    m = re.match(r"\(a\)\s+(.*?)\n\s*\\begin\{itemize\}\n(\s*)\\item\[\(b\)\]", text, re.S)
    if not m or "(a)" in m.group(1) or "\\begin{itemize}" in m.group(1):
        return text, False
    body = m.group(1).rstrip()
    body = TRAILING_BREAK_RE.sub("", body)
    return (f"\\begin{{itemize}}\n{m.group(2)}\\item[(a)] {body}\n{m.group(2)}\\item[(b)]"
            + text[m.end():]), True


def _figure_blocks(lines: list[str]) -> list[tuple[int, int, str]]:
    """(first, last, image name) of each figure: a figure environment or a bare
    \\includegraphics line (with its trailing \\\\)."""
    out = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("\\begin{figure}"):
            j = i
            while lines[j].strip() != "\\end{figure}":
                j += 1
            names = IMG_RE.findall("\n".join(lines[i:j + 1]))
            out.append((i, j, names[0] if names else ""))
            i = j + 1
            continue
        if s.startswith("\\includegraphics"):
            out.append((i, i, IMG_RE.findall(s)[0]))
        i += 1
    return out


def parse(tex: str, skip_kinds: frozenset[str] = frozenset()) -> tuple[list[dict], list[str], list[str]]:
    body = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    log: list[str] = []
    dropped: list[str] = []
    fixes = json.loads(FIXES_PATH.read_text(encoding="utf-8")) if FIXES_PATH.is_file() else []
    fixes = [f for f in fixes if f["kind"] not in skip_kinds]
    for fix in fixes:
        if fix["kind"] != "structure":
            continue
        hits = body.count(fix["old"])
        if hits != 1:
            raise SystemExit(f"STRUCTURE FIX {fix['key']}: expected 1 match, found {hits}: {fix['old'][:60]!r}")
        body = body.replace(fix["old"], fix["new"])
    lines = body.split("\n")

    lost_at = {}
    for sec, (marker, first) in LOST_HEADERS.items():
        hits = [i for i, ln in enumerate(lines) if ln.startswith(marker)]
        if len(hits) != 1:
            raise SystemExit(f"lost-header marker for {sec} found {len(hits)} times")
        lost_at[hits[0]] = (sec, first)

    def section_start(i: int) -> bool:
        return bool(PS_RE.match(lines[i].strip())) or i in lost_at

    # drop the main text: from each marked line to the next Problem Set
    skip = [False] * len(lines)
    for marker, back in MAIN_TEXT_STARTS:
        hits = [i for i, ln in enumerate(lines) if ln.startswith(marker)]
        if len(hits) != 1:
            raise SystemExit(f"main-text marker found {len(hits)} times: {marker[:60]!r}")
        i = hits[0] - back
        while i < len(lines) and not section_start(i):
            skip[i] = True
            i += 1

    # figures moved to a heading or another problem
    moved: dict[int, str] = {}  # first line of the figure -> its text
    moved_target: dict[int, object] = {}
    moved_lines: set[int] = set()
    for a, b, name in _figure_blocks(lines):
        if name in FIGURE_TARGETS and not skip[a]:
            moved[a] = "\n".join(lines[a:b + 1]).rstrip()
            moved_target[a] = FIGURE_TARGETS[name]
            for k in range(a, b + 1):
                skip[k] = True
                moved_lines.add(k)
    moved_text_by_target: dict[object, list[str]] = {}
    for a in sorted(moved):
        moved_text_by_target.setdefault(moved_target[a], []).append(TRAILING_BREAK_RE.sub("", moved[a]))

    rows: list[dict] = []
    notes: list[dict] = []  # kept headings: section, first, last, lines
    sec = None
    last = 0
    cur: dict | None = None  # the problem or heading collecting lines
    # open itemize lists: True for a list of problems (its markup is dropped), False
    # for a list inside a problem (kept). A top-level list is a list of problems
    # unless its first item has a part label like (a).
    lists: list[bool] = []

    def problem_list(i: int) -> bool:
        for ln in lines[i + 1:i + 20]:
            m = re.match(r"^\s*\\item\[([^\]]*)\]", ln)
            if m:
                return bool(re.fullmatch(r"\d*", m.group(1)))
        return True

    seen_sections: list[str] = []
    for i, line in enumerate(lines):
        s = line.strip()
        m = PS_RE.match(s)
        if m or i in lost_at:
            sec = m.group(1) if m else lost_at[i][0]
            last = (lost_at[i][1] if i in lost_at else 1) - 1
            seen_sections.append(sec)
            cur = None
            if m:
                continue
        opens, closes = s.startswith("\\begin{itemize}"), s.startswith("\\end{itemize}")
        outer = False
        if opens:
            outer = not lists and problem_list(i)
            lists.append(outer)
        elif closes:
            outer = lists.pop()
        depth = 1 if lists and lists[0] and len(lists) == 1 else (0 if not lists else 2)
        if skip[i]:
            if s and i not in moved_lines:
                dropped.append(s)
            continue
        if sec is None:
            if s and not s.startswith("\\captionsetup"):
                log.append(f"text before the first Problem Set: {s[:80]}")
            continue
        if outer:  # the markup of a list of problems
            continue
        if s == CHALLENGE:
            cur = None if cur is None or cur.get("heading") else cur
            dropped.append(s)
            continue
        if HEADING_RE.match(line):
            kept = [v for (ksec, start), v in KEPT_HEADINGS.items() if ksec == sec and line.startswith(start)]
            cur = {"heading": True, "section": sec, "lines": [line], "kept": bool(kept),
                   "start": next((start for (ksec, start) in KEPT_HEADINGS if ksec == sec and line.startswith(start)), None)}
            if kept:
                cur["first"], cur["last"] = kept[0]
                notes.append(cur)
            continue
        start = None
        if depth == 1:
            m = TOP_ITEM_RE.match(line)
            if m:
                if int(m.group(1)) != last + 1:
                    raise SystemExit(f"{sec}: problem {m.group(1)} after {last} (line {i + 1}): {s[:80]!r}")
                start = (int(m.group(1)), m.group(2))
            m = SWALLOWED_RE.match(line)
            if m and int(m.group(1)) == last + 1:
                rest = "\\(" + m.group(2)
                rest = re.sub(r"^\\\(\\quad\\\)\s*", "", rest)
                start = (int(m.group(1)), rest)
            if EMPTY_ITEM_RE.match(line):
                continue  # a list Mathpix re-opened at a page break: same problem
        elif depth == 0:
            m = PLAIN_RE.match(line)
            if m and int(m.group(1)) == last + 1:
                # not a matrix row ("2 H^{T} H & 0 \\"): any & comes after inline math opens
                amp, math = line.find("&"), line.find("\\(")
                if amp == -1 or -1 < math < amp:
                    start = (int(m.group(1)), line[len(m.group(1)) + 1:])
        if start:
            last = start[0]
            cur = {"key": f"{sec}.{last}", "section": sec, "num": last, "lines": [start[1]]}
            rows.append(cur)
            continue
        if cur is None:
            if s:
                log.append(f"{sec}: text outside any problem (line {i + 1}): {s[:80]}")
            continue
        if cur.get("heading") and not cur["kept"]:
            if s:
                dropped.append(s)
            continue
        cur["lines"].append(line)

    if seen_sections != SECTIONS:
        log.append(f"sections {seen_sections}")

    fixes_by = {}
    for fix in fixes:
        if fix["kind"] != "structure":
            fixes_by.setdefault((fix["key"], fix["field"]), []).append(fix)

    def apply_fixes(key: str, field: str, text: str) -> str:
        for fix in fixes_by.pop((key, field), []):
            hits = text.count(fix["old"])
            if hits != 1:
                raise SystemExit(f"FIX {key} {field}: expected 1 match, found {hits}: {fix['old'][:60]!r}")
            text = text.replace(fix["old"], fix["new"])
        return text

    note_text: dict[tuple[str, int], str] = {}
    for n in notes:
        key = f"{n['section']}/{n['first']}-{n['last']}"
        text = _clean("\n".join(n["lines"]))
        text = re.sub(r"^\\section\*\{(.*)\}$", r"\1", text, count=1, flags=re.M)
        figs = moved_text_by_target.pop((n["section"], n["start"]), [])
        if figs:
            text += "\n\n" + "\n\n".join(figs)
        text = apply_fixes(key, "note", text)
        # a heading whose printed range is wrong: field "range", e.g. "9-16" -> "9-14"
        first, last = n["first"], n["last"]
        for fix in fixes_by.pop((key, "range"), []):
            if fix["old"] != f"{first}-{last}":
                raise SystemExit(f"FIX {key} range: the range is {first}-{last}, not {fix['old']}")
            first, last = map(int, fix["new"].split("-"))
        for k in range(first, last + 1):
            note_text[(n["section"], k)] = text

    # problems the book splits in two: field "drop" removes the fragment (its text is
    # joined to the neighbouring problem by an ordinary fix)
    drop_keys = set()
    for k, fld in list(fixes_by):
        if fld == "drop":
            del fixes_by[(k, fld)]
            drop_keys.add(k)

    out = []
    lifted = 0
    for r in rows:
        if r["key"] in drop_keys:
            drop_keys.discard(r["key"])
            continue
        q = _clean("\n".join(r["lines"]))
        q, did = _lift_part_a(q)
        lifted += did
        figs = moved_text_by_target.pop(r["key"], [])
        if figs:
            q += "\n\n" + "\n\n".join(figs)
        q = apply_fixes(r["key"], "latexcode", q)
        note = note_text.get((r["section"], r["num"]))
        out.append({"key": r["key"], "section": r["section"], "num": r["num"],
                    "latexcode": (note + "\n\n" + q) if note else q, "note": note})
    log_extra = ([f"unused fix {k}" for k in fixes_by] + [f"unplaced figure for {t}" for t in moved_text_by_target]
                 + [f"drop fix for unknown problem {k}" for k in drop_keys])
    log.extend(log_extra)

    dropped_nums = {(f["key"].rsplit(".", 1)[0], int(f["key"].rsplit(".", 1)[1]))
                    for f in fixes if f["field"] == "drop"}
    by_sec: dict[str, list[int]] = {}
    for r in out:
        by_sec.setdefault(r["section"], []).append(r["num"])
    for sec in SECTIONS:
        nums = by_sec.get(sec, [])
        first = LOST_HEADERS[sec][1] if sec in LOST_HEADERS else 1
        expect = [k for k in range(first, first + len(nums) + 5) if (sec, k) not in dropped_nums][:len(nums)]
        if not nums or nums != expect:
            log.append(f"{sec}: problem numbers {nums}")
    print(f"  (a)-lifted={lifted}")
    return out, log, dropped


def check(rows: list[dict], images_dir: Path) -> list[str]:
    problems = []
    for r in rows:
        t = r["latexcode"]
        if not t or not t.strip():
            problems.append(f"{r['key']}: empty")
            continue
        depth = 0
        k = 0
        while k < len(t):
            if t[k] == "\\":
                k += 2
                continue
            depth += {"{": 1, "}": -1}.get(t[k], 0)
            if depth < 0:
                break
            k += 1
        if depth != 0:
            problems.append(f"{r['key']}: unbalanced braces")
        begins = re.findall(r"\\begin\{([^}]+)\}", t)
        ends = re.findall(r"\\end\{([^}]+)\}", t)
        if sorted(begins) != sorted(ends):
            problems.append(f"{r['key']}: environments {sorted(begins)} vs {sorted(ends)}")
        if (t.count("\\(") - t.count("\\\\(") != t.count("\\)")
                or t.count("\\[") - t.count("\\\\[") != t.count("\\]")):
            problems.append(f"{r['key']}: unbalanced math delimiters")
        if re.search(r"\\(?:sub)*section|Problem Set|Challenge Problems|^ {0,2}\\item\[\d+\]", t, re.M):
            problems.append(f"{r['key']}: leftover header or number")
        if re.search(r"\\item\[\]|\\item\b(?!\[)", t):
            problems.append(f"{r['key']}: empty or bare item")
        if re.search(r"^\s*\d+\.\d+ [A-C] |^Solution |\\item\[\d+\.\d+\]", t, re.M):
            problems.append(f"{r['key']}: worked-example text")
        for name in IMG_RE.findall(t):
            if not (images_dir / f"{name}.jpg").is_file():
                problems.append(f"{r['key']}: missing image {name}")
    return problems


def images_used(rows: list[dict]) -> list[str]:
    names = []
    for r in rows:
        for name in IMG_RE.findall(r["latexcode"]):
            if name not in names:
                names.append(name)
    return names


def apply(rows: list[dict], images_dir: Path) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        added = skipped = 0
        for r in rows:
            h = latex_hash(r["latexcode"])
            if h in existing:
                skipped += 1
                continue
            conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, NULL, NULL, NULL, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], SOURCE, h),
            )
            existing.add(h)
            added += 1
        conn.commit()
    finally:
        conn.close()
    copied = 0
    for name in images_used(rows):
        src = images_dir / f"{name}.jpg"
        for dest_dir in (TEXIMAGES, REPO_IMAGES):
            dest = dest_dir / src.name
            if not dest.exists():
                shutil.copy2(src, dest)
                copied += 1
    print(f"added={added} skipped={skipped} image_copies={copied}")


def update(rows: list[dict], before: list[dict]) -> None:
    """Rewrite rows already in the DB whose text the fixes change, and delete those a fix
    drops: each is found by the latex_hash of its text without the fixes of the given
    kinds (`before`)."""
    new = {r["key"]: r for r in rows}
    if set(new) - {r["key"] for r in before}:
        raise SystemExit(f"problems not in the DB yet: {sorted(set(new) - {r['key'] for r in before})}")
    conn = sqlite3.connect(DB_PATH)
    try:
        updated = deleted = 0
        for old in before:
            r = new.get(old["key"])
            if r is not None and r["latexcode"] == old["latexcode"]:
                continue
            hits = conn.execute("SELECT question_id FROM questions WHERE source = ? AND latex_hash = ?",
                                (SOURCE, latex_hash(old["latexcode"]))).fetchall()
            if len(hits) != 1:
                raise SystemExit(f"{old['key']}: {len(hits)} DB rows with its old text")
            if r is None:
                conn.execute("DELETE FROM questions WHERE question_id = ?", (hits[0][0],))
                deleted += 1
            else:
                conn.execute("UPDATE questions SET latexcode = ?, latex_hash = ? WHERE question_id = ?",
                             (r["latexcode"], latex_hash(r["latexcode"]), hits[0][0]))
                updated += 1
        conn.commit()
    finally:
        conn.close()
    print(f"updated={updated} deleted={deleted}")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tex", type=Path, required=True)
    p.add_argument("--images", type=Path, help="images folder (default: images/ next to the .tex)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--update", metavar="KIND", action="append",
                   help="rewrite the imported rows that fixes of this kind change (e.g. --update book)")
    p.add_argument("--dump", type=Path, help="write the parsed rows as JSON")
    p.add_argument("--show-dropped", action="store_true", help="print the lines that were dropped")
    args = p.parse_args(argv)

    images_dir = args.images or args.tex.parent / "images"
    rows, log, dropped = parse(args.tex.read_text(encoding="utf-8"))
    for line in log:
        print("  " + line)
    if args.show_dropped:
        for line in dropped:
            print("  DROPPED " + line[:150])
    problems = check(rows, images_dir)
    for line in problems:
        print("  PROBLEM " + line)
    print(f"questions={len(rows)} with_note={sum(1 for r in rows if r['note'])} "
          f"images={len(images_used(rows))} dropped_lines={len(dropped)} problems={len(problems)}")
    if args.dump:
        args.dump.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    if (args.apply or args.update) and (problems or log):
        print("refusing to write with problems")
        return 1
    if args.apply:
        apply(rows, images_dir)
    if args.update:
        before, _, _ = parse(args.tex.read_text(encoding="utf-8"), frozenset(args.update))
        update(rows, before)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
