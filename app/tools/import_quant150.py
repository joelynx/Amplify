"""
Import Stefanica, Radoicic and Wang, *150 Most Frequently Asked Questions on
Quant Interviews*, questions with their solutions
-----------------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book's solution chapters (one .tex file
plus an images/ folder) and adds every question, with the book's worked
answer as its solution, to amplify.db. The solution chapters restate each
question, so chapter 1 (the 15 "first look" questions) and chapter 3 (the
rest, by section 3.1-3.7) hold all of them; chapter 2, the bare list of
questions, is not needed.

Layout of the export:
    \\section*{Solutions}                chapter 1
    Question 1. Text ...                 a question (numbered per chapter/section)
    Answer: Text ...                     its solution, up to the next question
    ...
    \\section*{Chapter 3}
    \\section*{Solutions}
    \\subsection*{3.1 Mathematics, ...}  a section of chapter 3; numbering restarts

Keys are "1.N" (chapter 1) and "3.S.N" (section 3.S, question N).

The source PDF lacks book pages 89-90: question 3.2.6 is missing entirely (the
end of its solution on p. 91 is dropped) and the solution of 3.2.5 breaks off,
so 3.2.5 goes in without one (TRUNCATED).

Chapter 3 restates two chapter 1 questions (3.2.10 = 1.5, 3.6.20 = 1.3) to give
other solutions. Each is one row: the chapter 1 question, its solution, then the
chapter 3 solutions under a heading (MERGED). Kind "merge" fixes reword the
book's cross-references between the two ("see Chapter 1", "(3.154)") to match.

Repairs made on the way in:
  * Page-bottom footnotes (\\footnotetext blocks, which can hold several notes)
    are cut out of the running text, and each note goes under "Notes" at the end
    of the question or solution that carries its marker.
  * Line breaks: stray "\\\\" lines are dropped, a "\\\\" that breaks a sentence
    (the book's line end) or a paragraph break where a page break or a footnote
    cut a sentence in two is joined up, and a figure that cut a sentence moves to
    the end of the paragraph; displays, code and tables are left alone.
  * Code split at a page break is one verbatim block again; the three
    lstlisting examples (mathescape, which the app's preamble cannot set)
    become verbatim; a list split at a page break is joined up.
  * □ and × in text become math.
  * Misreads found by checking every question and solution against the book
    pages are corrected from quant150_fixes.json (page and reason on each; they
    apply to the text as it stands after the steps above, field "question" or
    "solution"). Kind "structure" fixes repair the raw export before it is
    parsed (footnote markers); kind "markup" fixes move a \\tag out of an array,
    where LaTeX does not allow it; kind "book" fixes correct the book's own
    errors.

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, answer NULL, no
embeddings (run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. Referenced images are copied to
app/data/appdata/teximages/ and Files/images/.

Usage (repo root):
  python -m app.tools.import_quant150 --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_quant150 --tex <export.tex> --apply
  python -m app.tools.import_quant150 --tex <export.tex> --update book   (rows already imported)
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

# Existing labels: "Surname's Title"; diacritics dropped (Radoičić).
SOURCE = "Stefanica, Radoicic and Wang's 150 Most Frequently Asked Questions on Quant Interviews"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")
TEXIMAGES = Path("app/data/appdata/teximages")
REPO_IMAGES = Path("Files/images")

# Book pages 89-90 are not in the source PDF.
MISSING = {"3.2.6"}
TRUNCATED = {"3.2.5"}  # its solution breaks off at the end of p. 88

# Questions chapter 3 restates from chapter 1 with other solutions: the chapter 3 row is
# folded into the chapter 1 row, its solutions after the first under this heading.
MERGED = {"3.2.10": ("1.5", "Two more solutions"), "3.6.20": ("1.3", "Another solution")}
TAG_RE = re.compile(r"\s*\\tag\{[^}]*\}")

SOLUTIONS_RE = re.compile(r"^\\section\*\{Solutions\}$")
CHAPTER3_RE = re.compile(r"^\\section\*\{Chapter 3\}$")
SECTION_RE = re.compile(r"^\\subsection\*\{3\.(\d) .*\}$")
QUESTION_RE = re.compile(r"^Question (\d+)\.\s*(.*)$")
ANSWER_RE = re.compile(r"^Answer:?\s*(.*)$")

IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BREAK_LINE_RE = re.compile(r"^\s*\\\\(?:\[0pt\])?\s*$")
LEADING_BREAK_RE = re.compile(r"^\s*\\\\(?:\[0pt\])?\s*")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")

NOTE_TOKEN = "@@NOTE {}@@"
NOTE_TOKEN_RE = re.compile(r"^@@NOTE (\d+)@@$")
NOTE_START_RE = re.compile(r"^\\\(\{ \}(?:\^\{([^}]*)\})?\\\)")  # "\({ }^{7}\) The function ..."
MARKER_RE = r"\{ \}\^\{%s\}"  # "{ }^{7}" in the running text

FIXES_PATH = Path(__file__).with_name("quant150_fixes.json")


def _match_brace(s: str, k: int) -> int:
    depth = 0
    i = k
    while i < len(s):
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SystemExit("unbalanced braces in a footnote")


def _cut_footnotes(body: str) -> tuple[str, list[str]]:
    """Replace each \\footnotetext block by a token line; return the notes, one per token.
    A block can hold several notes, each starting with its marker."""
    notes: list[str] = []
    out, i = [], 0
    while (j := body.find("\\footnotetext{", i)) >= 0:
        k = j + len("\\footnotetext")
        end = _match_brace(body, k)
        out.append(body[i:j])
        chunks: list[list[str]] = []
        for line in body[k + 1:end].strip().split("\n"):
            if NOTE_START_RE.match(line) or not chunks:
                chunks.append([])
            chunks[-1].append(line)
        tokens = []
        for chunk in chunks:
            tokens.append(NOTE_TOKEN.format(len(notes)))
            notes.append(TRAILING_BREAK_RE.sub("", "\n".join(chunk)).strip())
        out.append("\n" + "\n\n".join(tokens) + "\n\n")
        i = end + 1
    out.append(body[i:])
    return "".join(out), notes


# Displays, code, tables and figures, where line breaks are left alone.
PROTECTED_RE = re.compile(
    r"\\\[.*?\\\]|\\begin\{(verbatim|tabular|figure|equation\*|align\*|gather\*)\}.*?\\end\{\1\}", re.S)


def _join_text(text: str) -> str:
    # a forced break in mid-sentence (the book's line end): "ob-\\ served", "a random\\ sample"
    text = re.sub(r"([A-Za-z])-\\\\\s*\n([a-z])", r"\1\2", text)
    text = re.sub(r"\s*\\\\\s*\n(?=[a-z]|\\\$)", " ", text)
    # a sentence cut in two by a page break or a footnote: "the implied volatilities\n\nof options"
    return re.sub(r"(?:(?<=[A-Za-z0-9,;])|(?<=\\\)))\n\n+(?=[a-z]|\\\()", " ", text)


# A figure the page layout put in mid-sentence: the sentence is joined and the figure follows it.
FIGURE_IN_SENTENCE_RE = re.compile(
    r"(?<=[A-Za-z0-9,;])\n\n(\\begin\{figure\}.*?\\end\{figure\})\n\n([a-z][^\n]*)", re.S)


def _clean(text: str) -> str:
    lines = [ln for ln in text.split("\n") if not BREAK_LINE_RE.match(ln)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    text = FIGURE_IN_SENTENCE_RE.sub(r" \2\n\n\1", text)
    out, k = [], 0
    for m in PROTECTED_RE.finditer(text):
        out += [_join_text(text[k:m.start()]), m.group(0)]
        k = m.end()
    text = "".join(out + [_join_text(text[k:])])
    text = LEADING_BREAK_RE.sub("", TRAILING_BREAK_RE.sub("", text))
    return text.strip()


# Code: one block split at a page break is joined; a mathescape listing becomes verbatim.
SPLIT_VERBATIM_RE = re.compile(r"\n\\end\{verbatim\}\s*\\begin\{verbatim\}\n")
LISTING_RE = re.compile(r"\\begin\{lstlisting\}\[mathescape=true\]\n(.*?)\\end\{lstlisting\}", re.S)


def _listing_as_verbatim(m: re.Match) -> str:
    code = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", m.group(1)).replace("$", "")
    return f"\\begin{{verbatim}}\n{code}\\end{{verbatim}}"


SPLIT_LIST_RE = re.compile(r"\n\\end\{itemize\}\s*\\begin\{itemize\}\n")
UNICODE_MATH = [
    (re.compile(r"□"), r"\(\\square\)"),
    (re.compile(r"\b(\d+) ?× ?(\d+)\b"), r"\(\1 \\times \2\)"),  # "a 2 × 2 matrix"
    (re.compile(r"×"), r"\(\\times\)"),
]


# Mathpix's "text\\" + blank line before a display: the display belongs to the sentence.
DISPLAY_BREAK_RE = re.compile(r"\\\\\n\n(?=\\\[|\\begin\{(?:equation|align|gather)\*\})")


def _normalize(text: str) -> str:
    """Before the fixes (they were written against this text): code and lists split at a page
    break joined up, listings as verbatim, unicode math, no paragraph break before a display."""
    text = SPLIT_VERBATIM_RE.sub("\n", text)
    text = LISTING_RE.sub(_listing_as_verbatim, text)
    text = SPLIT_LIST_RE.sub("\n", text)
    for pat, rep in UNICODE_MATH:
        text = pat.sub(rep, text)
    return DISPLAY_BREAK_RE.sub("\n", text)


def _with_notes(text: str, notes: list[str]) -> str:
    if not notes:
        return text
    return text + "\n\n\\paragraph{Notes}\n" + "\n\n".join(notes)


def _load_fixes(skip_kinds: frozenset[str]) -> list[dict]:
    if not FIXES_PATH.is_file():
        return []
    return [f for f in json.loads(FIXES_PATH.read_text(encoding="utf-8")) if f["kind"] not in skip_kinds]


def _replace_once(text: str, old: str, new: str, where: str) -> str:
    hits = text.count(old)
    if hits != 1:
        raise SystemExit(f"FIX {where}: expected 1 match, found {hits}: {old[:60]!r}")
    return text.replace(old, new)


def parse(tex: str, skip_kinds: frozenset[str] = frozenset()) -> tuple[list[dict], list[str], dict]:
    fixes = _load_fixes(skip_kinds)
    body = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    for fix in fixes:
        if fix["kind"] == "structure":
            body = _replace_once(body, fix["old"], fix["new"], f"structure {fix.get('key', '')}")
    body, notes = _cut_footnotes(body)
    log: list[str] = []
    dropped: dict[str, list[str]] = {"headers": [], "notes": [], "other": []}

    rows: list[dict] = []
    fields: list[tuple[dict, str]] = []  # (row, "question" | "solution") in document order
    lines_of: dict[tuple[str, str], list[str]] = {}
    chapter = section = None
    cur: tuple[dict, str] | None = None

    for line in body.split("\n"):
        s = line.strip()
        if SOLUTIONS_RE.match(s):
            if chapter is None:
                chapter = 1
            dropped["headers"].append(s)
            continue
        if CHAPTER3_RE.match(s):
            chapter, section, cur = 3, None, None
            dropped["headers"].append(s)
            continue
        if m := SECTION_RE.match(s):
            section, cur = int(m.group(1)), None
            if chapter != 3:
                raise SystemExit(f"section {s} outside chapter 3")
            dropped["headers"].append(s)
            continue
        prefix = "1" if chapter == 1 else f"3.{section}"
        last = max((r["num"] for r in rows if r["prefix"] == prefix), default=0)
        if (m := QUESTION_RE.match(s)) and chapter is not None:
            num = int(m.group(1))
            if num != last + 1 and not (num == last + 2 and f"{prefix}.{last + 1}" in MISSING):
                raise SystemExit(f"{prefix}: question {num} after {last}")
            row = {"key": f"{prefix}.{num}", "prefix": prefix, "num": num}
            rows.append(row)
            cur = (row, "question")
            fields.append(cur)
            lines_of[(row["key"], "question")] = [m.group(2)]
            continue
        if (m := ANSWER_RE.match(s)) and cur is not None and cur[1] == "question":
            cur = (cur[0], "solution")
            fields.append(cur)
            lines_of[(cur[0]["key"], "solution")] = [m.group(1)]
            continue
        if cur is None:
            if s:
                dropped["other"].append(s)
            continue
        lines_of[(cur[0]["key"], cur[1])].append(line)

    # each note goes to the field that carries its marker: the nearest one before the note
    texts = {k: "\n".join(v) for k, v in lines_of.items()}
    notes_of: dict[tuple[str, str], list[str]] = {}
    for fi, (row, fld) in enumerate(fields):
        for i in map(int, re.findall(r"@@NOTE (\d+)@@", texts[(row["key"], fld)])):
            m = NOTE_START_RE.match(notes[i])
            num = m.group(1) if m else None
            home = None
            if num:  # a page-bottom note is at most one row away from its marker
                near = [f for f in fields[:fi + 1] if rows.index(f[0]) >= rows.index(row) - 1]
                for prow, pfld in reversed(near):
                    t = re.sub(r"@@NOTE \d+@@", "", texts[(prow["key"], pfld)])
                    if re.search(MARKER_RE % re.escape(num), t):
                        home = (prow["key"], pfld)
                        break
            if home is None:
                log.append(f"{row['key']} {fld}: no marker for note {notes[i][:60]!r}")
                home = (row["key"], fld)
            notes_of.setdefault(home, []).append(notes[i])

    out = []
    for row in rows:
        key = row["key"]
        q = re.sub(r"\n?@@NOTE \d+@@\n?", "\n", texts[(key, "question")])
        s = texts.get((key, "solution"))
        if s is None:
            log.append(f"{key}: no Answer")
        else:
            s = re.sub(r"\n?@@NOTE \d+@@\n?", "\n", s)
        question = _normalize(_with_notes(_clean(q), notes_of.get((key, "question"), [])))
        solution = _normalize(_with_notes(_clean(s), notes_of.get((key, "solution"), []))) if s else None
        if key in TRUNCATED:
            dropped["other"].append(f"{key} solution (breaks off): {solution[:80] if solution else None}")
            solution = None
        out.append({"key": key, "question": question, "solution": solution})
    for key, nts in notes_of.items():
        if key[0] in TRUNCATED and key[1] == "solution":
            dropped["notes"] += nts

    fixed = {r["key"]: r for r in out}
    for fix in fixes:
        if fix["kind"] == "structure":
            continue
        r = fixed[fix["key"]]
        r[fix["field"]] = _replace_once(r[fix["field"]], fix["old"], fix["new"], f"{fix['key']} {fix['field']}")
    for r in out:
        r["latexcode"] = r.pop("question")

    expected = {"1": 15, "3.1": 15, "3.2": 10, "3.3": 26, "3.4": 34, "3.5": 11, "3.6": 33, "3.7": 39}
    for prefix, n in expected.items():
        nums = [int(r["key"].rsplit(".", 1)[1]) for r in out if r["key"].rsplit(".", 1)[0] == prefix]
        want = [k for k in range(1, n + 1) if f"{prefix}.{k}" not in MISSING]
        if nums != want:
            log.append(f"{prefix}: question numbers {nums}")

    for key, (into, heading) in MERGED.items():
        src, dst = fixed[key], fixed[into]
        if TAG_RE.sub("", src["latexcode"]) != TAG_RE.sub("", dst["latexcode"]):
            log.append(f"{key}: not the same question as {into}")
            continue
        dst["solution"] += f"\n\n\\paragraph{{{heading}}}\n{src['solution']}"
        out.remove(src)
    return out, log, dropped


# Commands that compile but are misreads here (dotless i/j for i/j, script letters the
# app's preamble lacks).
SUSPECT_RE = re.compile(r"\\(?:imath|jmath|mathscr)\b|@@NOTE|\\footnotetext|lstlisting|(?<!\\)\$")


def check(rows: list[dict], images_dir: Path) -> list[str]:
    problems = []
    for r in rows:
        for fld in ("latexcode", "solution"):
            t = r[fld]
            if t is None:
                if fld == "solution" and r["key"] not in TRUNCATED:
                    problems.append(f"{r['key']}: no solution")
                continue
            where = f"{r['key']} {fld}"
            if not t.strip():
                problems.append(f"{where}: empty")
                continue
            stack = []
            for kind, name in re.findall(r"\\(begin|end)\{([^}]+)\}", t):
                if kind == "begin":
                    stack.append(name)
                elif not stack or stack.pop() != name:
                    problems.append(f"{where}: environments out of order")
                    break
            else:
                if stack:
                    problems.append(f"{where}: unclosed {stack}")
            # code is left as printed (3.4.20's ends in a stray "}")
            nov = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", "", t, flags=re.S)
            depth = 0
            k = 0
            while k < len(nov):
                if nov[k] == "\\":
                    k += 2
                    continue
                depth += {"{": 1, "}": -1}.get(nov[k], 0)
                if depth < 0:
                    break
                k += 1
            if depth != 0:
                problems.append(f"{where}: unbalanced braces")
            if (nov.count("\\(") - nov.count("\\\\(") != nov.count("\\)")
                    or nov.count("\\[") - nov.count("\\\\[") != nov.count("\\]")):
                problems.append(f"{where}: unbalanced math delimiters")
            # \tag is only allowed at the top level of a display
            for m in re.finditer(r"\\begin\{(aligned|array|cases|gathered)\}(.*?)\\end\{\1\}", nov, re.S):
                if "\\tag" in m.group(2):
                    problems.append(f"{where}: \\tag inside {m.group(1)}")
            if re.search(r"\\(?:sub)*section|^Question \d+\.|^Answer:", nov, re.M):
                problems.append(f"{where}: leftover header")
            if SUSPECT_RE.search(nov):
                problems.append(f"{where}: suspect {SUSPECT_RE.search(nov).group(0)}")
            if re.search(r"[□×]", t):
                problems.append(f"{where}: a character to set as math")
            for name in IMG_RE.findall(t):
                if not (images_dir / f"{name}.jpg").is_file():
                    problems.append(f"{where}: missing image {name}")
    return problems


def images_used(rows: list[dict]) -> list[str]:
    seen: list[str] = []
    for r in rows:
        for name in IMG_RE.findall(r["latexcode"] + (r["solution"] or "")):
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
            if not dest.is_file():
                shutil.copy2(src, dest)
                copied += 1
    print(f"added={added} skipped={skipped} image_copies={copied}")


def update(rows: list[dict], before: list[dict]) -> None:
    """Rewrite rows already in the DB whose text the fixes change: each is found by the
    latex_hash of its question without the fixes of the given kinds (`before`)."""
    conn = sqlite3.connect(DB_PATH)
    try:
        updated = 0
        for new, old in zip(rows, before):
            if new["key"] != old["key"]:
                raise SystemExit(f"rows out of step: {new['key']} vs {old['key']}")
            if new["latexcode"] == old["latexcode"] and new["solution"] == old["solution"]:
                continue
            hits = conn.execute("SELECT question_id FROM questions WHERE source = ? AND latex_hash = ?",
                                (SOURCE, latex_hash(old["latexcode"]))).fetchall()
            if len(hits) != 1:
                raise SystemExit(f"{new['key']}: {len(hits)} DB rows with its old text")
            conn.execute("UPDATE questions SET latexcode = ?, latex_hash = ?, solution = ? WHERE question_id = ?",
                         (new["latexcode"], latex_hash(new["latexcode"]), new["solution"], hits[0][0]))
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
    p.add_argument("--show-dropped", action="store_true", help="print the lines that were dropped")
    args = p.parse_args(argv)

    images_dir = args.images or args.tex.parent / "images"
    rows, log, dropped = parse(args.tex.read_text(encoding="utf-8"))
    for line in log:
        print("  " + line)
    if args.show_dropped:
        for what, lines in dropped.items():
            for line in lines:
                print(f"  DROPPED {what}: {line[:150]}")
    problems = check(rows, images_dir)
    for line in problems:
        print("  PROBLEM " + line)
    print(f"questions={len(rows)} with_solution={sum(1 for r in rows if r['solution'])} "
          f"images={len(images_used(rows))} "
          + " ".join(f"dropped_{k}={len(v)}" for k, v in dropped.items())
          + f" problems={len(problems)}")
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
