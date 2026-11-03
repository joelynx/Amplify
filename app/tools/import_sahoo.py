"""
Import Sahoo, *Probability and Mathematical Statistics*, review exercises
-------------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book's Review Exercises sections
(chapters 1-21) and its "Answers to Selected Review Exercises" (chapters 1-18)
and adds every exercise to amplify.db, with the book's answer where it gives
one. The book prints answers only, no worked solutions.

Layout of the export:
    <main text>                         the end of the chapter's text on the page where its
                                        exercises start (dropped; see MAIN_TEXT_STARTS)
    \\subsection*{3.5 Review Exercises}  ("20.5. Exercises" in Chapter 20)
    \\begin{enumerate}
      \\setcounter{enumi}{4}
      \\item What is ...                an exercise, numbered by the list, or
    \\end{enumerate}
    8. What is ...                      the same as a plain numbered line
    \\section*{ANSWERES TO SELECTED REVIEW EXERCISES}
    CHAPTER 3                           (or \\section*{CHAPTER 3})
      \\item[1.] \\(\\frac{1}{4}\\).       the answers, labelled or numbered by a list

Repairs made on the way in:
  * Stray "\\\\" lines (Mathpix's line breaks around displays) are dropped, and
    a "\\\\" that breaks a sentence (or a hyphenated word) is joined up.
  * Chapters 19-21 have no back-of-book answers; where an exercise states its
    own answer ("(Answer: ...)", "(Ans: 25)") that becomes the answer.
  * Misreads found by checking every exercise and answer against the book
    pages are corrected from sahoo_fixes.json (page and reason on each):
    mostly the comma or period after "otherwise" in a cases display, minus
    signs and numbers left outside math, and the lognormal symbol (a
    hand-made capital Lambda in the book), set as \\Lambda.
  * The book's own errors are corrected too (fixes of kind "book", each with
    its reason): typos and missing words, a few wrong formulas (6.34, the
    densities of 15.19, 15.20, 16.26), mixed-up parameter names (15.31, 16.25,
    17.15, 17.17, 18.13), the unfinished question of 14.21, and wrong answers
    (6.24, 10.7, 10.9, 15.19, 15.31), each re-derived.

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings
(run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. The book repeats six exercises word for
word in later chapters (5.13, 11.2, 13.12, 13.13, 15.16, 15.17); those hash
the same as the first copy, so only the first goes in.

Usage (repo root):
  python -m app.tools.import_sahoo --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_sahoo --tex <export.tex> --apply
  python -m app.tools.import_sahoo --tex <export.tex> --update book   (rows already imported)
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

from app.persistence.ingest.seed import latex_hash

# Existing labels: "Surname's Title".
SOURCE = "Sahoo's Probability and Mathematical Statistics"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")

FIRST_CHAPTER, LAST_CHAPTER = 1, 21
LAST_ANSWERED_CHAPTER = 18
EXERCISES_RE = re.compile(r"^\\subsection\*\{(\d+)\.\d+\.? (?:Review )?Exercises\}$")
ANSWERS_HEADER = "\\section*{ANSWERES TO SELECTED REVIEW EXERCISES}"
ANSWER_CHAPTER_RE = re.compile(r"^(?:\\section\*\{)?CHAPTER (\d+)\}?$")

# The book's main text that precedes a Review Exercises section on its first
# page: the start of its first line, and how many lines before that line also
# belong to it. Everything from there to the next exercises header is dropped.
MAIN_TEXT_STARTS = [
    ("Hence the probability of \\(X\\) less than the ratio of the mode to the median", 0),  # ch 3
    ("The following theorem is easy to prove and we leave its proof to the reader.", 0),  # ch 5
    ("compute the mean and variance of it. The moment generating function is", 0),  # ch 6
    ("\\includegraphics[max width=\\textwidth, alt={}, center]"
     "{a99ca3dd-2d7b-4b9e-b4a8-62361bcfe16c-022_408_606_344_753}", 0),  # ch 7, PDF of Min(X,Y)
    ("Example 8.14. Let \\(X\\) and \\(Y\\) be two independent Bernoulli", 0),
    ("Example 10.21. What is the probability density function of the sum", 0),
    ("parameters. Then", 0),  # ch 11, the end of Theorem 11.11
    ("Example 13.23. If a sample of size 3 from a uniform distribution", 0),
    ("Since, the loss function is absolute error, the Bayes estimate", 0),  # ch 15
    ("\\lim _{n \\rightarrow \\infty} \\operatorname{Var}\\left(\\widehat{\\theta}_{n}\\right)=", 3),  # ch 16, "Hence"
    ("when the null hypothesis \\(H_{o}: \\sigma^{2}=\\sigma_{o}^{2}\\) is true.", 0),  # ch 18
    ("Determine the sample correlation coefficient \\(r\\) and then test the null", 0),  # ch 19
    ("Answer: From the data the variances of each group can be found to be", 0),  # ch 20
    ("we accept the null hypothesis that the sample was taken from a population", 0),  # ch 21
]

ITEM_RE = re.compile(r"^\s*\\item(?:\[(\d+)\.\])?(?:\s+(.*)|\s*)$")
NUMBERED_RE = re.compile(r"^(\d+)\.\s+(.*)$")
SETCOUNTER_RE = re.compile(r"^\s*\\setcounter\{enumi\}\{(\d+)\}\s*$")
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BREAK_LINE_RE = re.compile(r"^\s*\\\\(?:\[0pt\])?\s*$")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")
INLINE_ANSWER_RE = re.compile(r"\((?:Answer|Ans): (.*)\)\s*$")

FIXES_PATH = Path(__file__).with_name("sahoo_fixes.json")


def _clean(text: str) -> str:
    lines = [ln for ln in text.split("\n") if not BREAK_LINE_RE.match(ln)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    # a forced break in mid-sentence (the book's line end): "ob-\\ served", "a random\\ sample"
    text = re.sub(r"([A-Za-z])-\\\\\s*\n([a-z])", r"\1\2", text)
    text = re.sub(r"\s*\\\\\s*\n(?=[a-z]|\\\$)", " ", text)
    text = TRAILING_BREAK_RE.sub("", text)
    return text.strip()


class _Numbering:
    """Exercise / answer numbers from enumerate counters, \\item[N.] labels and "N." lines."""

    def __init__(self) -> None:
        self.in_enum = False
        self.counter = 0

    def start(self, line: str, accept) -> tuple[int, str] | None:
        """(number, rest of the line) if the line starts an entry `accept` takes, else None.
        List markup lines return (0, "") so the caller drops them."""
        s = line.strip()
        if s == "\\begin{enumerate}":
            self.in_enum, self.counter = True, 0
            return 0, ""
        if s == "\\end{enumerate}":
            self.in_enum = False
            return 0, ""
        m = SETCOUNTER_RE.match(line)
        if m and self.in_enum:
            self.counter = int(m.group(1))
            return 0, ""
        m = ITEM_RE.match(line)
        if m and (m.group(1) or self.in_enum):
            if m.group(1):
                n = int(m.group(1))
            else:
                self.counter += 1
                n = self.counter
            if not accept(n):
                raise SystemExit(f"list item numbered {n} out of order: {s[:80]!r}")
            return n, m.group(2) or ""
        m = NUMBERED_RE.match(line)
        if m and accept(int(m.group(1))):
            return int(m.group(1)), m.group(2)
        return None


def parse(tex: str, skip_kinds: frozenset[str] = frozenset()) -> tuple[list[dict], list[str], list[str]]:
    body = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    ex_part, ans_part = body.split(ANSWERS_HEADER, 1)
    lines = ex_part.split("\n")
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
    by_key: dict[tuple[int, int], dict] = {}
    chapter = None
    cur: dict | None = None
    num = _Numbering()
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
        last = cur["num"] if cur and cur["chapter"] == chapter else 0
        st = num.start(line, lambda k: k == last + 1)
        if st:
            k, rest = st
            if k:
                cur = {"key": f"{chapter}.{k}", "chapter": chapter, "num": k, "lines": [rest]}
                rows.append(cur)
                by_key[(chapter, k)] = cur
            continue
        if cur is None:
            if s:
                log.append(f"chapter {chapter}: text before the first exercise: {s[:80]}")
            continue
        cur["lines"].append(line)

    # answers
    chapter = None
    cur = None
    num = _Numbering()
    for line in ans_part.split("\n"):
        s = line.strip()
        m = ANSWER_CHAPTER_RE.match(s)
        if m:
            chapter, cur = int(m.group(1)), None
            continue
        if chapter is None:
            if s:
                log.append(f"answers: text before CHAPTER 1: {s[:80]}")
            continue
        if s in ("\\begin{itemize}", "\\end{itemize}"):  # the lists of \item[N.] answers
            continue
        last = cur["num"] if cur else 0
        st = num.start(line, lambda k: k > last and (chapter, k) in by_key)
        if st:
            k, rest = st
            if k:
                cur = {"num": k, "lines": [rest]}
                by_key[(chapter, k)]["a_lines"] = cur["lines"]
            continue
        if cur is None:
            if s:
                log.append(f"answers ch {chapter}: text before the first answer: {s[:80]}")
            continue
        cur["lines"].append(line)

    out = []
    for r in rows:
        question = _clean("\n".join(r["lines"]))
        answer = _clean("\n".join(r["a_lines"])) if "a_lines" in r else None
        m = INLINE_ANSWER_RE.search(question)
        if m and not answer:
            # the answer the exercise itself states, "(Answer: 0.7627)", where the back has none
            answer = m.group(1).strip()
        out.append({"key": r["key"], "chapter": r["chapter"], "num": r["num"],
                    "latexcode": question, "answer": answer or None})

    fixed = {r["key"]: r for r in out}
    if FIXES_PATH.is_file():
        for fix in json.loads(FIXES_PATH.read_text(encoding="utf-8")):
            if fix["kind"] in skip_kinds:
                continue
            r = fixed[fix["key"]]
            fld, old = fix["field"], fix["old"]
            hits = (r[fld] or "").count(old)
            if hits != 1:
                raise SystemExit(f"FIX {fix['key']} {fld}: expected 1 match, found {hits}: {old[:60]!r}")
            r[fld] = r[fld].replace(old, fix["new"])

    for ch in range(FIRST_CHAPTER, LAST_CHAPTER + 1):
        nums = [r["num"] for r in out if r["chapter"] == ch]
        if not nums or nums != list(range(1, len(nums) + 1)):
            log.append(f"chapter {ch}: exercise numbers {nums}")
    return out, log, dropped


def check(rows: list[dict]) -> list[str]:
    problems = []
    for r in rows:
        for fld in ("latexcode", "answer"):
            t = r[fld]
            if t is None and fld == "answer":
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
            if re.search(r"\\(?:sub)*section|\\setcounter|^\s*\d+\.\s|Review Exercises|CHAPTER", t, re.M):
                problems.append(f"{r['key']} {fld}: leftover header or number")
            if re.search(r"\\item\b(?!\[)", t):
                problems.append(f"{r['key']} {fld}: bare \\item")
            if IMG_RE.search(t):
                problems.append(f"{r['key']} {fld}: image")
    return problems


def apply(rows: list[dict]) -> None:
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
                VALUES (?, ?, ?, ?, NULL, 1, ?, NULL, ?, NULL, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], SOURCE, r["answer"], h),
            )
            existing.add(h)
            added += 1
        conn.commit()
    finally:
        conn.close()
    print(f"added={added} skipped={skipped}")


def update(rows: list[dict], before: list[dict]) -> None:
    """Rewrite rows already in the DB whose text the fixes change: each is found by the
    latex_hash of its text without the fixes of the given kinds (`before`)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        updated = 0
        for new, old in zip(rows, before):
            if (new["latexcode"], new["answer"]) == (old["latexcode"], old["answer"]):
                continue
            hits = conn.execute("SELECT question_id FROM questions WHERE source = ? AND latex_hash = ?",
                                (SOURCE, latex_hash(old["latexcode"]))).fetchall()
            if len(hits) != 1:
                raise SystemExit(f"{new['key']}: {len(hits)} DB rows with its old text")
            conn.execute("UPDATE questions SET latexcode = ?, answer = ?, latex_hash = ? WHERE question_id = ?",
                         (new["latexcode"], new["answer"], latex_hash(new["latexcode"]), hits[0][0]))
            updated += 1
        conn.commit()
    finally:
        conn.close()
    print(f"updated={updated}")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tex", type=Path, required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--update", metavar="KIND", action="append",
                   help="rewrite the imported rows that fixes of this kind change (e.g. --update book)")
    p.add_argument("--dump", type=Path, help="write the parsed rows as JSON")
    p.add_argument("--show-dropped", action="store_true", help="print the main-text lines that were dropped")
    args = p.parse_args(argv)

    rows, log, dropped = parse(args.tex.read_text(encoding="utf-8"))
    for line in log:
        print("  " + line)
    if args.show_dropped:
        for line in dropped:
            print("  DROPPED " + line[:150])
    problems = check(rows)
    for line in problems:
        print("  PROBLEM " + line)
    print(f"questions={len(rows)} with_answer={sum(1 for r in rows if r['answer'])} "
          f"dropped_lines={len(dropped)} problems={len(problems)}")
    if args.dump:
        args.dump.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    if (args.apply or args.update) and (problems or log):
        print("refusing to write with problems")
        return 1
    if args.apply:
        apply(rows)
    if args.update:
        before, _, _ = parse(args.tex.read_text(encoding="utf-8"), frozenset(args.update))
        update(rows, before)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
