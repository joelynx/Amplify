"""
Import Oksendal, *Stochastic Differential Equations: An Introduction with Applications*, exercises
---------------------------------------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book's Exercises sections (chapters 2-12)
and its "Solutions and Additional Hints to Some of the Exercises" (one .tex file
plus an images/ folder) and adds every exercise to amplify.db. Starred
exercises carry the book's solution or hint; the book prints none for the others.

Layout of the export:
    <main text>                     the end of the chapter's text on the page where its
                                    exercises start (dropped; see MAIN_TEXT_STARTS)
    \\section*{Exercises}
    \\begin{itemize}
      \\item[2.4.] * a) Let ...     an exercise ("*" = solved at the back), or
    5.11.* (The Brownian bridge).   the same as a plain line, or
    \\subsection*{5.17. (...)}      as a subsection
        \\item[b)] ...  \\item[(i)]  its parts, in lists Mathpix nests and splits at page breaks
    \\section*{Solutions and Additional Hints to Some of the Exercises}
      2.4. a) Put ...               the solutions, labelled the same three ways

Repairs made on the way in:
  * Each exercise's part lists are rebuilt from the labels: a), b), ... and
    (i), (ii), ... (and 1), (1), (a)) each make one list level, nested in the
    order they appear, so a list Mathpix split at a page break is one list
    again. A part label at the start of a line ("2.4. a) Let ...") becomes an
    item too. Text that Mathpix put after the end of a list (and not into a
    re-opened one) goes back to the level it was printed at.
  * Stray "\\\\" lines (Mathpix's line breaks around displays) are dropped.
  * A note heading a chapter's exercises (only Chapter 3 has one: "Unless
    otherwise stated B_t denotes Brownian motion in R, B_0=0.") is put at the
    top of each of that chapter's exercises, so they read on their own.
  * Misreads found by checking every exercise and solution against the book
    pages are corrected from oksendal_fixes.json (page and reason on each):
    mostly punctuation lost at the end of displays, a few symbols (plain R for
    bold R, the iterated integral in 3.7), list levels, and the figure of
    9.7 d), which had floated into 9.8.

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings
(run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. Referenced images are copied to
app/data/appdata/teximages/ and Files/images/.

Usage (repo root):
  python -m app.tools.import_oksendal --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_oksendal --tex <export.tex> --apply
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

# Existing labels: "Surname's Title", diacritics dropped (cf. "Gnadig's ...").
SOURCE = "Oksendal's Stochastic Differential Equations"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")
TEXIMAGES = Path("app/data/appdata/teximages")
REPO_IMAGES = Path("Files/images")

FIRST_CHAPTER, LAST_CHAPTER = 2, 12
EXERCISES_HEADER = "\\section*{Exercises}"
SOLUTIONS_HEADER = "\\section*{Solutions and Additional Hints to Some of the Exercises}"

# The book's main text that precedes an Exercises section on its first page:
# a unique piece of its first paragraph. Everything from the start of that
# paragraph to the next Exercises header is dropped.
MAIN_TEXT_STARTS = [
    "Therefore, from this point of view it seems reasonable to use (3.3.6)",
    "Now suppose \\(X_{t}\\) is a strong solution of (5.3.1).",
    "\\text { (system) } & d X_{t}=\\left[F_{0}(t)+F_{1}(t) X_{t}+F_{2}(t) Z_{t}\\right] d t",
    "Example 7.5.6 Let \\(D\\) be an open subset of",
    "\\widehat{B}_{t}:=-\\int_{0}^{t} a\\left(B_{s}\\right) d s+B_{t}",
    "f61ace0f-f73c-4d50-af1f-8d1acdfbcbdd-058_472_845_185_347",  # Green-function figure of Chapter 9
    "We conclude that \\(\\phi=g^{*}\\) and \\(\\tau^{*}=\\tau_{D}\\) is optimal",
    "Since \\(u_{\\lambda_{0}}^{*} \\in \\mathcal{K}\\) the proof is complete.",
    "This indicates that the continuation region has the shape shown in the Figure 12.1.",
]

HEADER_RES = [
    re.compile(r"^\s*\\item\[(\d+)\.(\d+)\.(\*?)\]\s*(\*?)\s*(.*)$"),
    re.compile(r"^\\subsection\*\{(\d+)\.(\d+)\.(\*?)()\s*(.*)\}\s*$"),
    re.compile(r"^(\d+)\.(\d+)\.(\*?)()\s*(.*)$"),
]
ITEM_RE = re.compile(r"^\s*\\item\[([^\]]*)\]\s*(.*)$")
LEAD_LABEL_RE = re.compile(r"^(\((?:i|ii|iii|iv|v|vi)\)|[a-h]\)|\([a-b]\)|[1-9]\)|\([1-9]\))\s+(?=\S)")
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BREAK_LINE_RE = re.compile(r"^\s*\\\\(?:\[0pt\])?\s*$")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")

FIXES_PATH = Path(__file__).with_name("oksendal_fixes.json")


def _label_type(label: str) -> str:
    if re.fullmatch(r"\((?:i|ii|iii|iv|v|vi)\)", label):
        return "roman"
    if re.fullmatch(r"[a-z]\)", label):
        return "alpha"
    if re.fullmatch(r"\([a-z]\)", label):
        return "paren-alpha"
    if re.fullmatch(r"\d\)", label):
        return "digit"
    if re.fullmatch(r"\(\d\)", label):
        return "paren-digit"
    raise ValueError(f"unknown part label {label!r}")


def _ends_sentence(line: str) -> bool:
    s = re.sub(r"(\\tag\{[^}]*\}|\\\\|\s)+$", "", line)
    return bool(re.search(r"(?:[.?]\)?|\.\s*\\\)|\\square\\\))$", s))


# a new sentence or block: "Remark.", "(Hint: ...", "[Hint: ...", a figure
NEW_BLOCK_RE = re.compile(r"^(?:[A-Z]|\(\s*[A-Z]|\[[A-Z]|\\begin\{center\})")


def _tokens(lines: list[tuple[str, int]]) -> list[tuple]:
    """(text, depth) lines -> ("item", label, depth) / ("text", line, depth, after_close) tokens.

    after_close: Mathpix printed the text outside the list that just ended (an
    \\end{itemize} and no \\begin{itemize} in between), after a finished
    sentence, and the text starts a new one. Mathpix also closes lists in
    mid-sentence, mostly just before a display; that text stays in the item."""
    out: list[tuple] = []
    closed = False
    last = ""  # last line with content, displays included
    for line, depth in lines:
        s = line.strip()
        if s == "\\begin{itemize}":
            closed = False
            continue
        if s == "\\end{itemize}":
            closed = _ends_sentence(last)
            continue
        if s and not re.fullmatch(r"\\\]|\\end\{[a-z*]+\}|\\\\(?:\[0pt\])?", s):
            last = s
        m = ITEM_RE.match(line)
        if m:
            label, rest = m.group(1).strip(), m.group(2)
            if label:
                out.append(("item", label, depth))
                closed = False
            line = rest
            if not line.strip():
                continue
        # part labels at the start of a line: "a) Show that", "(i) a) dX = ..."
        while True:
            m = LEAD_LABEL_RE.match(line.lstrip())
            if not m:
                break
            out.append(("item", m.group(1), depth))
            closed = False
            line = line.lstrip()[m.end():]
        out.append(("text", line, depth, closed and bool(NEW_BLOCK_RE.match(line.strip()))))
        if line.strip():
            closed = False
    return out


def _rebuild(lines: list[tuple[str, int]]) -> str:
    """Rebuild the part lists of one exercise or solution from its labels."""
    stack: list[list] = []  # [label type, Mathpix depth of its latest item]
    out: list[str] = []

    def close_to(n: int) -> None:
        while len(stack) > n:
            stack.pop()
            out.append("  " * len(stack) + "\\end{itemize}")

    for tok in _tokens(lines):
        if tok[0] == "item":
            _, label, depth = tok
            t = _label_type(label)
            types = [lvl[0] for lvl in stack]
            if t in types:
                close_to(types.index(t) + 1)
                stack[-1][1] = depth
            else:
                out.append("  " * len(stack) + "\\begin{itemize}")
                stack.append([t, depth])
            out.append("  " * len(stack) + f"\\item[{label}]")
            continue
        _, line, depth, after_close = tok
        if after_close and line.strip():
            keep = len(stack)
            while keep and stack[keep - 1][1] > depth:
                keep -= 1
            close_to(keep)
        if out and out[-1].lstrip().startswith("\\item[") and out[-1].endswith("]") and line.strip():
            out[-1] += " " + line.strip()
        else:
            out.append(line)
    close_to(0)
    return "\n".join(out)


def _clean(text: str) -> str:
    lines = [ln for ln in text.split("\n") if not BREAK_LINE_RE.match(ln)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    text = re.sub(r"\n\s*\n(\s*\\(?:end\{itemize\}|item\[))", r"\n\1", text)
    text = re.sub(r"(\\item\[[^\]]*\] \\\()\\quad\s*", r"\1", text)
    text = TRAILING_BREAK_RE.sub("", text)
    return text.strip()


def _header(line: str):
    for rx in HEADER_RES:
        m = rx.match(line)
        if m:
            return f"{int(m.group(1))}.{int(m.group(2))}", bool(m.group(3) or m.group(4)), m.group(5)
    return None


def _next_keys(key: str | None) -> set[str]:
    if key is None:
        return {f"{FIRST_CHAPTER}.1"}
    c, n = map(int, key.split("."))
    return {f"{c}.{n + 1}", f"{c + 1}.1"}


def parse(tex: str) -> tuple[list[dict], list[str]]:
    body = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    ex_part, sol_part = body.split(SOLUTIONS_HEADER, 1)
    lines = ex_part.split("\n")
    log: list[str] = []
    dropped: list[str] = []

    # drop the main text: from the start of each marked paragraph to the next Exercises header
    skip = [False] * len(lines)
    for marker in MAIN_TEXT_STARTS:
        hits = [i for i, ln in enumerate(lines) if marker in ln]
        if len(hits) != 1:
            raise SystemExit(f"main-text marker found {len(hits)} times: {marker[:60]!r}")
        i = hits[0]
        while i > 0 and lines[i - 1].strip():
            i -= 1
        while i < len(lines) and lines[i].strip() != EXERCISES_HEADER:
            skip[i] = True
            i += 1

    rows: list[dict] = []
    by_key: dict[str, dict] = {}

    def collect(part_lines: list[str], skipped: list[bool], solutions: bool) -> None:
        cur: dict | None = None
        last: str | None = None
        depth = 0
        in_section = solutions
        note: list[str] = []  # text between "Exercises" and the first exercise
        for n, line in enumerate(part_lines):
            s = line.strip()
            if skipped[n] or s in (EXERCISES_HEADER,):
                if skipped[n] and s:
                    dropped.append(s)
                if s == EXERCISES_HEADER:
                    cur = None
                    in_section = True
                    note = []
                depth += s == "\\begin{itemize}"
                depth -= s == "\\end{itemize}"
                continue
            h = _header(line)
            if h and (h[0] in _next_keys(last) if not solutions else (h[0] in by_key and (
                    last is None or _order(h[0]) > _order(last)))):
                key, star, rest = h
                last = key
                if solutions:
                    cur = {"key": key, "lines": []}
                    by_key[key]["s_lines"] = cur["lines"]
                else:
                    cur = {"key": key, "chapter": int(key.split(".")[0]), "num": int(key.split(".")[1]),
                           "star": star, "lines": [], "note": "\n".join(note).strip()}
                    rows.append(cur)
                    by_key[key] = cur
                # the header's own item sits in the outer list
                cur["lines"].append((rest, depth if line.lstrip().startswith("\\item[") else depth))
                continue
            depth += s == "\\begin{itemize}"
            depth -= s == "\\end{itemize}"
            if cur is None:
                if s and s not in ("\\begin{itemize}", "\\end{itemize}"):
                    if solutions:
                        log.append(f"solutions: line outside any solution: {s[:80]}")
                    elif in_section:
                        note.append(s)
                    else:
                        dropped.append(s)
                continue
            # an item line's own depth is that of its list
            cur["lines"].append((line, depth))

    collect(lines, skip, solutions=False)
    sol_lines = sol_part.split("\n")
    collect(sol_lines, [False] * len(sol_lines), solutions=True)

    out = []
    for r in rows:
        question = _clean(_rebuild(r["lines"]))
        solution = _clean(_rebuild(r["s_lines"])) if "s_lines" in r else None
        out.append({"key": r["key"], "chapter": r["chapter"], "num": r["num"], "star": r["star"],
                    "latexcode": question, "solution": solution or None})

    fixed = {r["key"]: r for r in out}
    if FIXES_PATH.is_file():
        for fix in json.loads(FIXES_PATH.read_text(encoding="utf-8")):
            r = fixed[fix["key"]]
            fld, old = fix["field"], fix["old"]
            hits = (r[fld] or "").count(old)
            if hits != 1:
                raise SystemExit(f"FIX {fix['key']} {fld}: expected 1 match, found {hits}: {old[:60]!r}")
            r[fld] = r[fld].replace(old, fix["new"])

    # a note heading a chapter's exercises applies to each of them (after the fixes,
    # whose old texts are unique within the exercise alone)
    notes = {r["key"]: r["note"] for r in rows}
    for r in out:
        if notes[r["key"]]:
            r["latexcode"] = notes[r["key"]] + "\n\n" + r["latexcode"]

    # numbering: chapters 2-12, each 1..N with no gaps; starred <=> solution
    for ch in range(FIRST_CHAPTER, LAST_CHAPTER + 1):
        nums = [r["num"] for r in out if r["chapter"] == ch]
        if not nums or nums != list(range(1, len(nums) + 1)):
            log.append(f"chapter {ch}: exercise numbers {nums}")
    for r in out:
        if r["star"] != (r["solution"] is not None):
            log.append(f"{r['key']}: star={r['star']} but solution={'yes' if r['solution'] else 'no'}")
    return out, log, dropped


def _order(key: str) -> tuple[int, int]:
    c, n = key.split(".")
    return int(c), int(n)


def check(rows: list[dict], images_dir: Path) -> list[str]:
    problems = []
    for r in rows:
        for fld in ("latexcode", "solution"):
            t = r[fld]
            if t is None and fld == "solution":
                continue
            if not t or not t.strip():
                problems.append(f"{r['key']}: empty {fld}")
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
                problems.append(f"{r['key']} {fld}: unbalanced braces")
            begins = re.findall(r"\\begin\{([^}]+)\}", t)
            ends = re.findall(r"\\end\{([^}]+)\}", t)
            if sorted(begins) != sorted(ends):
                problems.append(f"{r['key']} {fld}: environments {sorted(begins)} vs {sorted(ends)}")
            if (t.count("\\(") - t.count("\\\\(") != t.count("\\)")
                    or t.count("\\[") - t.count("\\\\[") != t.count("\\]")):
                problems.append(f"{r['key']} {fld}: unbalanced math delimiters")
            if re.search(r"\\(?:sub)*section|^\s*(?:\\item\[)?\d+\.\d+\.\*?\]?\s|^Exercises$", t, re.M):
                problems.append(f"{r['key']} {fld}: leftover header")
            if re.search(r"\\item\[\]", t):
                problems.append(f"{r['key']} {fld}: empty item")
            for name in IMG_RE.findall(t):
                if not (images_dir / f"{name}.jpg").is_file():
                    problems.append(f"{r['key']} {fld}: missing image {name}")
    return problems


def images_used(rows: list[dict]) -> list[str]:
    names = []
    for r in rows:
        for fld in ("latexcode", "solution"):
            for name in IMG_RE.findall(r[fld] or ""):
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
                VALUES (?, ?, ?, ?, NULL, 1, ?, NULL, NULL, ?, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], SOURCE, r["solution"], h),
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


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tex", type=Path, required=True)
    p.add_argument("--images", type=Path, help="images folder (default: images/ next to the .tex)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    p.add_argument("--dump", type=Path, help="write the parsed rows as JSON")
    p.add_argument("--show-dropped", action="store_true", help="print the main-text lines that were dropped")
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
    print(f"questions={len(rows)} with_solution={sum(1 for r in rows if r['solution'])} "
          f"images={len(images_used(rows))} dropped_lines={len(dropped)} problems={len(problems)}")
    if args.dump:
        args.dump.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    if args.apply and (problems or log):
        print("refusing to write with problems")
        return 1
    if args.apply:
        apply(rows, images_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
