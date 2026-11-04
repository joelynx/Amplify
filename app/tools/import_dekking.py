"""
Import Dekking, Kraaikamp, Lopuhaa and Meester, *A Modern Introduction to
Probability and Statistics*, end-of-chapter exercises
---------------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book's Exercises sections (chapters
2-28; one .tex file plus an images/ folder; the PDF holds only the pages those
sections are on) and adds every exercise to amplify.db. The answers and full
solutions are in the book's appendices, which the PDF does not include, so
the rows have no answer or solution.

Layout of the export:
    <main text>                          the end of the chapter's text and its "Solutions to
                                         the quick exercises" on the page where the exercises
                                         start (dropped; see MAIN_TEXT_STARTS)
    \\subsection*{3.6 Exercises}
    3.2 [icon] A fair die is ...          an exercise; the icon (a boxed plus or boxed dot
                                         in the book, marking those answered in its
                                         appendices) is read as "A", ⊞, ■, ⊕, □, ... or lost
    \\begin{itemize} \\item[a.] ...        its parts
    \\begin{figure} / \\begin{table}        its figures and tables, with their captions

Repairs made on the way in:
  * The icons are dropped (ICONS; ICON_A lists the exercises whose leading "A"
    is the icon, not the article).
  * Stray "\\\\" lines (Mathpix's line breaks around displays) are dropped, and
    a "\\\\" that breaks a sentence is joined up.
  * ×, ⋯ and □ in text (Latin Modern has no glyph for the last two) become
    math, and \\multirow (not in the app's preamble) is dropped, keeping its
    cell's text.
  * Misreads found by checking every exercise against the book pages are
    corrected from dekking_fixes.json (page and reason on each); kind
    "structure" fixes repair the raw export before it is parsed (21.6-21.8
    had been read as items of 21.5's list). Besides words, numbers and
    symbols, these move figures and tables that Mathpix left where the page
    printed them to the exercise that uses them (Fig. 9.5 to 9.15, Figs.
    17.9/17.10 to 17.1/17.2, Table 26.2 to 26.1), rejoin text a float or
    page break cut in two, and restore hyphens of compounds joined at a line
    end ("so-called", "sugary-white").
  * The book's own errors are corrected too (fixes of kind "book", each with
    its reason): typos ("worngly", "succesfully", "assesment", "Schwartz",
    "in the The Guardian", "the observed leave"), a wrong page in a source
    reference (17.4), and S_d^2 for S_p^2 in 28.6 d-e.
  * Last, after the fixes: "\\(i\\) th" becomes "\\(i\\)th", a list split at a
    page break is joined up, and negative numbers in table cells get a
    minus sign instead of a hyphen.

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings
(run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. Referenced images are copied to
app/data/appdata/teximages/ and Files/images/.

Usage (repo root):
  python -m app.tools.import_dekking --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_dekking --tex <export.tex> --apply
  python -m app.tools.import_dekking --tex <export.tex> --update book   (rows already imported)
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
SOURCE = "Dekking et al.'s A Modern Introduction to Probability and Statistics"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")
TEXIMAGES = Path("app/data/appdata/teximages")
REPO_IMAGES = Path("Files/images")

FIRST_CHAPTER, LAST_CHAPTER = 2, 28
EXERCISES_RE = re.compile(r"^\\subsection\*\{(\d+)\.\d+ Exercises\}$")

# The book's main text that precedes an Exercises section on its first page:
# the start of its first line, and how many lines before that line also belong
# to it. Everything from there to the next exercises header is dropped.
# (Chapter 2's starts the file; chapters 3, 8, 15, 22 and 27 start their page
# with the header.)
MAIN_TEXT_STARTS = [
    ("4.6 There are two ways to show that", 0),
    ("5.5 In the eighth row and sixth column of the table", 0),
    ("6.2 Let the \\(U(0,1)\\) variable be \\(U\\) and set:", 0),
    ("\\subsection*{7.5 Solutions to the quick exercises}", 0),
    ("9.4 For \\(a\\) between 0 and 3 and for \\(b\\) between 1 and 2", 0),
    ("10.3 From Table 10.1, as completed in Quick exercise 10.2", 0),
    ("11.3 The sum rule for two normal random variables", 0),
    ("\\subsection*{12.5 Solutions to the quick exercises}", 0),
    ("\\subsection*{13.5 Solutions to the quick exercises}", 0),
    ("With \\(\\mu=2\\) and \\(\\sigma=\\sqrt{2}\\), we find for \\(n=5000\\) that", 0),  # ch 14
    ("16.7 From the five-number summary for the Wick temperature data", 0),
    ("\\subsection*{17.5 Solutions to the quick exercises}", 0),
    ("by that of \\(\\operatorname{Med}", 4),  # ch 18, after a display
    ("However, there is one special case in which unbiasedness does carry over", 0),  # ch 19
    ("\\subsection*{20.4 Solutions to the quick exercises}", 0),
    ("21.2 From Table 21.1 we derive", 0),
    ("23.4 We need to solve", 0),
    ("24.4 The confidence level changes to 99", 0),
    ("If \\(H_{0}\\) is true, then in 24.75", 0),  # ch 25
    ("26.4 By means of the normal approximation", 0),
    ("The \\(p\\)-value is the right tail probability", 0),  # ch 28
]

# The book's icon in front of an exercise, as Mathpix reads it.
ICONS = re.compile(r"^(?:[⊞⊕■□⊡Đ]|\\\(\\(?:boxplus|boxdot|square|oplus)\\\))\s*")
# Exercises whose text starts with the icon read as the letter "A".
ICON_A = {"2.8", "3.2", "3.8", "5.8", "6.10", "6.12", "8.19", "10.18", "12.6", "12.11", "16.3", "16.6",
          "16.15", "17.7", "17.9", "18.8", "19.8", "21.1", "22.1", "23.6", "24.6", "24.9", "26.5"}

# "6.7 Text", "6. 7 Text", "\(8.11 \boxplus\) Text", "\(\mathbf{8 . 1 0} \boxplus\) Text"
EXERCISE_RES = [
    re.compile(r"^(\d+)\.\s?(\d+)(?:\s+(.*))?$"),
    re.compile(r"^\\\((?:\\mathbf\{)?([\d ]+?)\s*\.\s*([\d ]+?)\}?\s*\\(?:boxplus|boxdot|square)\s*\\\)\s*(.*)$"),
]
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BREAK_LINE_RE = re.compile(r"^\s*\\\\(?:\[0pt\])?\s*$")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")

FIXES_PATH = Path(__file__).with_name("dekking_fixes.json")


def _clean(text: str) -> str:
    lines = [ln for ln in text.split("\n") if not BREAK_LINE_RE.match(ln)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    # a forced break in mid-sentence (the book's line end): "ob-\\ served", "a random\\ sample"
    text = re.sub(r"([A-Za-z])-\\\\\s*\n([a-z])", r"\1\2", text)
    text = re.sub(r"\s*\\\\\s*\n(?=[a-z]|\\\$)", " ", text)
    text = TRAILING_BREAK_RE.sub("", text)
    return text.strip()


# Characters Latin Modern (the app's XeLaTeX font) lacks, as Mathpix leaves them in text.
UNICODE_MATH = [
    (re.compile(r"(\d)×(\d)"), r"\(\1 \\times \2\)"),  # "a 4×4 table"
    (re.compile(r"×"), r"\(\\times\)"),
    (re.compile(r"⋯"), r"\(\\cdots\)"),
    (re.compile(r"□"), r"\(\\square\)"),
]
MULTIROW_RE = re.compile(r"\\multirow(?:\[[^\]]*\])?\{[^}]*\}\{[^}]*\}\{")


def _drop_multirow(text: str) -> str:
    """\\multirow[b]{2}{*}{cell} -> cell (the app's preamble has no multirow package)."""
    while m := MULTIROW_RE.search(text):
        depth, k = 1, m.end()
        while depth:
            if text[k] == "\\":
                k += 2
                continue
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        text = text[:m.start()] + text[m.end():k - 1] + text[k:]
    return text


def _normalize(text: str) -> str:
    for pat, rep in UNICODE_MATH:
        text = pat.sub(rep, text)
    return _drop_multirow(text)


ORDINAL_RE = re.compile(r"\\\) (th|st|nd|rd)\b")  # "the \(i\) th group"
SPLIT_LIST_RE = re.compile(r"\n\\end\{itemize\}\s*\\begin\{itemize\}\n")
TABULAR_RE = re.compile(r"\\begin\{tabular\}.*?\\end\{tabular\}", re.S)
NEG_CELL_RE = re.compile(r"(^|&)(\s*)-(\d[\d.]*)(?=\s*(?:&|\\\\))", re.M)


def _finish(text: str) -> str:
    """Last pass, after the fixes: "\\(i\\)th", a list split at a page break joined up, and
    negative numbers in table cells set with a minus sign instead of a hyphen."""
    text = ORDINAL_RE.sub(r"\\)\1", text)
    text = SPLIT_LIST_RE.sub("\n", text)
    return TABULAR_RE.sub(lambda m: NEG_CELL_RE.sub(r"\1\2\\(-\3\\)", m.group(0)), text)


def _load_fixes(skip_kinds: frozenset[str]) -> list[dict]:
    if not FIXES_PATH.is_file():
        return []
    return [f for f in json.loads(FIXES_PATH.read_text(encoding="utf-8")) if f["kind"] not in skip_kinds]


def _replace_once(text: str, old: str, new: str, where: str) -> str:
    hits = text.count(old)
    if hits != 1:
        raise SystemExit(f"FIX {where}: expected 1 match, found {hits}: {old[:60]!r}")
    return text.replace(old, new)


def parse(tex: str, skip_kinds: frozenset[str] = frozenset()) -> tuple[list[dict], list[str], list[str]]:
    fixes = _load_fixes(skip_kinds)
    body = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    for fix in fixes:
        if fix["kind"] == "structure":
            body = _replace_once(body, fix["old"], fix["new"], f"structure {fix.get('key', '')}")
    lines = body.split("\n")
    log: list[str] = []
    dropped: list[str] = []

    # drop the main text: from each marked line to the next exercises header
    skip = [False] * len(lines)
    for marker, back in MAIN_TEXT_STARTS:
        hits = [i for i, ln in enumerate(lines) if ln.strip().startswith(marker)]
        if len(hits) != 1:
            raise SystemExit(f"main-text marker found {len(hits)} times: {marker[:60]!r}")
        i = hits[0] - back
        while i < len(lines) and not EXERCISES_RE.match(lines[i].strip()):
            skip[i] = True
            i += 1

    rows: list[dict] = []
    chapter = None
    cur: dict | None = None
    for n, line in enumerate(lines):
        s = line.strip()
        m = EXERCISES_RE.match(s)
        if m:
            chapter, cur = int(m.group(1)), None
            if chapter != (rows[-1]["chapter"] + 1 if rows else FIRST_CHAPTER):
                raise SystemExit(f"chapter {chapter} out of order")
            continue
        if skip[n] or chapter is None:
            if s:
                dropped.append(s)
            continue
        m = next((m for m in (r.match(s) for r in EXERCISE_RES) if m), None)
        last = cur["num"] if cur else 0
        if m and int(m.group(1).replace(" ", "")) == chapter and int(m.group(2).replace(" ", "")) == last + 1:
            k = last + 1
            key = f"{chapter}.{k}"
            rest = ICONS.sub("", m.group(3) or "")
            if key in ICON_A:
                if not rest.startswith("A "):
                    raise SystemExit(f"{key}: no icon 'A' to drop: {rest[:40]!r}")
                rest = rest[2:]
            cur = {"key": key, "chapter": chapter, "num": k, "lines": [rest]}
            rows.append(cur)
            continue
        if cur is None:
            if s:
                log.append(f"chapter {chapter}: text before the first exercise: {s[:80]}")
            continue
        cur["lines"].append(line)

    out = [{"key": r["key"], "chapter": r["chapter"], "num": r["num"],
            "latexcode": _normalize(_clean("\n".join(r["lines"])))} for r in rows]

    fixed = {r["key"]: r for r in out}
    for fix in fixes:
        if fix["kind"] == "structure":
            continue
        r = fixed[fix["key"]]
        r["latexcode"] = _replace_once(r["latexcode"], fix["old"], fix["new"], fix["key"])
    for r in out:
        r["latexcode"] = _finish(r["latexcode"])

    for ch in range(FIRST_CHAPTER, LAST_CHAPTER + 1):
        nums = [r["num"] for r in out if r["chapter"] == ch]
        if not nums or nums != list(range(1, len(nums) + 1)):
            log.append(f"chapter {ch}: exercise numbers {nums}")
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
        if re.search(r"\\(?:sub)*section|Solutions to the quick|^\s*\d+\.\d+\s(?!.*&)", t, re.M):
            problems.append(f"{r['key']}: leftover header or number")
        if re.search(r"\\item\b(?!\[)", t):
            problems.append(f"{r['key']}: bare \\item")
        if "\\multirow" in t or re.search(r"[×⋯□]", t):
            problems.append(f"{r['key']}: \\multirow or a character the app's font lacks")
        if ICONS.match(t) or t.startswith("A A "):
            problems.append(f"{r['key']}: icon left in the text")
        for name in IMG_RE.findall(t):
            if not (images_dir / f"{name}.jpg").is_file():
                problems.append(f"{r['key']}: missing image {name}")
    return problems


def images_used(rows: list[dict]) -> list[str]:
    seen: list[str] = []
    for r in rows:
        for name in IMG_RE.findall(r["latexcode"]):
            if name not in seen:
                seen.append(name)
    return seen


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
            if not dest.is_file():
                shutil.copy2(src, dest)
                copied += 1
    print(f"added={added} skipped={skipped} image_copies={copied}")


def update(rows: list[dict], before: list[dict]) -> None:
    """Rewrite rows already in the DB whose text the fixes change: each is found by the
    latex_hash of its text without the fixes of the given kinds (`before`)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        updated = 0
        for new, old in zip(rows, before):
            if new["key"] != old["key"]:
                raise SystemExit(f"rows out of step: {new['key']} vs {old['key']}")
            if new["latexcode"] == old["latexcode"]:
                continue
            hits = conn.execute("SELECT question_id FROM questions WHERE source = ? AND latex_hash = ?",
                                (SOURCE, latex_hash(old["latexcode"]))).fetchall()
            if len(hits) != 1:
                raise SystemExit(f"{new['key']}: {len(hits)} DB rows with its old text")
            conn.execute("UPDATE questions SET latexcode = ?, latex_hash = ? WHERE question_id = ?",
                         (new["latexcode"], latex_hash(new["latexcode"]), hits[0][0]))
            updated += 1
        conn.commit()
    finally:
        conn.close()
    print(f"updated={updated}")


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
    print(f"questions={len(rows)} images={len(images_used(rows))} dropped_lines={len(dropped)} "
          f"problems={len(problems)}")
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
