"""
Import Bertsekas & Tsitsiklis, *Introduction to Probability* (2nd ed.), end-of-chapter problems
-----------------------------------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book's PROBLEMS sections (one .tex file
plus an images/ folder) and adds every problem to amplify.db. Starred problems
carry the book's solution; the others go in with no solution (the book prints
none for them, nor for the starred 3.27; it does print one for the unstarred 2.19).

Layout of the export:
    \\section*{PROBLEMS}                      start of the next chapter's problems (chapters 1-9 in order)
    SECTION 1.1. Sets\\\\  /  \\section*{SECTION 1.2. ...}
                                             section headers (dropped)
    Problem 4.* Title. Statement ...         a problem; "*" = solved in the book
    Solution. ...                            its solution

Repairs made on the way in:
  * \\imath / \\jmath (Mathpix's reading of a subscript i / j) become i / j.
  * Lists that Mathpix split in the middle of an item are re-joined, and an
    \\end{itemize} that cut a sentence in two is moved after the sentence.
  * Stray "\\\\" lines right after a display are dropped.
  * The page-bottom footnote inside the solution of 7.34 moves to a "Notes"
    paragraph at the end of that solution.
  * OCR misreads found by checking every problem and solution against the
    scanned pages are corrected from bertsekas_tsitsiklis_fixes.json (book page
    and reason on each entry): mostly commas read as periods, subscript i read
    as 2 or l, and Figure 7.24 moved from 7.28 to 7.29, which uses it.

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings
(run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. Referenced images are copied to
app/data/appdata/teximages/ and Files/images/.

Usage (repo root):
  python -m app.tools.import_bertsekas_tsitsiklis --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_bertsekas_tsitsiklis --tex <export.tex> --apply
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

# Existing labels: "Surname's Title"; two surnames joined by "and"; "s'" after a final s.
SOURCE = "Bertsekas and Tsitsiklis' Introduction to Probability"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")
TEXIMAGES = Path("app/data/appdata/teximages")
REPO_IMAGES = Path("Files/images")

CHAPTERS = 9
SECTION_RE = re.compile(r"^(?:\\section\*\{)?SECTION \d+\.\d+\.?\s.*$")
PROBLEM_RE = re.compile(r"^(?:\\section\*\{(Problem (\d+)\.(\*?)\s*(.*))\}|Problem (\d+)\.(\*?)\s*(.*))$")
SOLUTION_RE = re.compile(r"^Solution\.\s*(.*)$")
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")

# 7.34: a page-bottom footnote sits in the middle of the solution.
FOOTNOTE_734_START = "† The interchange of the infinite summation"
FOOTNOTE_734_END = "When \\(i=s\\), the events"

# Corrections from reading every problem against the scanned pages: a list of
# {key, field, page, kind, note, old, new}, applied in order. Each old text must
# occur exactly once in that field when its turn comes.
FIXES_PATH = Path(__file__).with_name("bertsekas_tsitsiklis_fixes.json")

# The book prints a solution for 2.19 although it is not starred, and none for the starred 3.27.
SOLVED_UNSTARRED = {"2.19"}
STARRED_UNSOLVED = {"3.27"}


def _repair(body: str) -> str:
    body = body.replace("\\captionsetup{singlelinecheck=false}", "")
    body = re.sub(r"\\imath(?![a-zA-Z])", "i", body)
    body = re.sub(r"\\jmath(?![a-zA-Z])", "j", body)
    # an item that runs on into a new list: "...a 0 (or 1) is\n\end{itemize}\n\n\begin{itemize}\n  \item[] transmitted as"
    body = re.sub(r"\n\\end\{itemize\}\n\s*\\begin\{itemize\}\n\s*\\item\[\]\s*", "\n", body)
    # "...averaged\n\end{itemize}\n\nover all possible values" -> close the list after the sentence
    body = re.sub(r"\n\\end\{itemize\}\n\s*\n([a-z][^\n]*)", r"\n\1\n\\end{itemize}", body)
    body = re.sub(r"(\\\])\n\\\\(?:\[0pt\])?\n", r"\1\n", body)
    return body


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = TRAILING_BREAK_RE.sub("", text)
    return text.strip()


def _move_footnote(solution: str) -> str:
    a = solution.index(FOOTNOTE_734_START)
    b = solution.index(FOOTNOTE_734_END, a)
    note = solution[a:b].strip().replace("† ", "\\({ }^{\\dagger}\\) ", 1)
    return solution[:a] + solution[b:] + "\n\n\\paragraph{Notes}\n" + note


def parse(tex: str) -> tuple[list[dict], list[str]]:
    body = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    lines = _repair(body).split("\n")
    log: list[str] = []
    rows: list[dict] = []
    chapter = 0
    cur: dict | None = None
    field = "q"
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if s == "\\section*{PROBLEMS}":
            chapter += 1
            cur = None
            continue
        if SECTION_RE.match(s):
            continue
        m = PROBLEM_RE.match(s)
        if m:
            num = int(m.group(2) or m.group(5))
            star = bool(m.group(3) if m.group(2) else m.group(6))
            rest = m.group(4) if m.group(2) else m.group(7)
            cur = {"key": f"{chapter}.{num}", "chapter": chapter, "num": num, "star": star, "q": [rest], "s": []}
            rows.append(cur)
            field = "q"
            continue
        m = SOLUTION_RE.match(s)
        if m and cur is not None:
            if field == "s":
                log.append(f"{cur['key']}: second Solution header")
            field = "s"
            cur["s"].append(m.group(1))
            continue
        if cur is None:
            if s:
                log.append(f"line {n} outside any problem: {s[:80]}")
            continue
        cur[field].append(line)

    out = []
    for r in rows:
        question = _clean("\n".join(r["q"]))
        solution = _clean("\n".join(r["s"])) or None
        if r["key"] == "7.34":
            solution = _move_footnote(solution)
        out.append({"key": r["key"], "chapter": r["chapter"], "num": r["num"], "star": r["star"],
                    "latexcode": question, "solution": solution})

    by_key = {r["key"]: r for r in out}
    for fix in json.loads(FIXES_PATH.read_text(encoding="utf-8")):
        r = by_key[fix["key"]]
        fld, old = fix["field"], fix["old"]
        hits = (r[fld] or "").count(old)
        if hits != 1:
            raise SystemExit(f"FIX {fix['key']} {fld}: expected 1 match, found {hits}: {old[:60]!r}")
        r[fld] = r[fld].replace(old, fix["new"])

    # numbering: each chapter 1..N with no gaps or repeats; starred <=> solution
    for ch in range(1, CHAPTERS + 1):
        nums = [r["num"] for r in out if r["chapter"] == ch]
        if nums != list(range(1, len(nums) + 1)):
            log.append(f"chapter {ch}: problem numbers {nums}")
    if chapter != CHAPTERS:
        log.append(f"found {chapter} chapters, expected {CHAPTERS}")
    for r in out:
        expected = (r["star"] or r["key"] in SOLVED_UNSTARRED) and r["key"] not in STARRED_UNSOLVED
        if expected != (r["solution"] is not None):
            log.append(f"{r['key']}: star={r['star']} but solution={'yes' if r['solution'] else 'no'}")
    return out, log


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
            if re.search(r"\\section|^Problem \d+\.|^Solution\.|^SECTION \d|[†×]|\\[ij]math\b", t, re.M):
                problems.append(f"{r['key']} {fld}: leftover header or marker")
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
    args = p.parse_args(argv)

    images_dir = args.images or args.tex.parent / "images"
    rows, log = parse(args.tex.read_text(encoding="utf-8"))
    for line in log:
        print("  " + line)
    problems = check(rows, images_dir)
    for line in problems:
        print("  PROBLEM " + line)
    print(f"questions={len(rows)} with_solution={sum(1 for r in rows if r['solution'])} "
          f"images={len(images_used(rows))} problems={len(problems)}")
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
