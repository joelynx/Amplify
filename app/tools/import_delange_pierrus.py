"""
Import de Lange & Pierrus, *Solved Problems in Classical Mechanics*
-------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book (one .tex file plus an images/
folder) and adds every "Question N.M" with its solution to amplify.db.

Layout of the export:
    \\section*{2}  \\section*{Miscellanea}   chapter number + title, then intro text
    \\section*{Question 2.1}                 question statement
    \\section*{Solution}                     solution
    \\section*{Comments} / {Comment}         optional remarks (kept, under the solution)

Repairs made on the way in:
  * Page-bottom footnotes (\\footnotetext{...} blocks and bare "[n] Author..."
    reference lines) are cut out of the running text, the sentence they split
    is re-joined, and each note is appended under "Notes" to the question
    part that cites it (references by their chapter-local number [n], dagger
    notes by the nearest preceding marker).
  * Headers glued to the end of a footnote line ("}\\section*{Question 6.16}")
    are split onto their own line.
  * Other \\section* headers inside a solution become \\paragraph{...}.
  * Chapter intros are dropped.
  * The garbled moment-of-inertia table in Question 12.10 is replaced by a
    hand-written tabular.
  * The Mathematica notebook cells (OCR'd into unusable code, either as
    verbatim or typeset as maths) are deleted; each run of cells becomes
    "(Mathematica code omitted.)". The plots they produced are kept.

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings
(run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. Referenced images are copied to
app/data/appdata/teximages/ and Files/images/.

Usage (repo root):
  python -m app.tools.import_delange_pierrus --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_delange_pierrus --tex <export.tex> --apply
  python -m app.tools.import_delange_pierrus --tex <export.tex> --update-solutions
      (rewrite the stored solutions of already-imported rows from a fresh parse)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.persistence.ingest.seed import latex_hash

# Existing labels: "Surname's Title"; two surnames joined by "and"; "s'" after a final s.
SOURCE = "de Lange and Pierrus' Solved Problems in Classical Mechanics"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")
TEXIMAGES = Path("app/data/appdata/teximages")
REPO_IMAGES = Path("Files/images")

CHAPTER_TITLES = {
    "Miscellanea": 2,
    "One-dimensional motion": 3,
    "Linear oscillations": 4,
    "Energy and potentials": 5,
    "Momentum and angular momentum": 6,
    "Motion in two and three dimensions": 7,
    "Spherically symmetric potentials": 8,
    "The Coulomb and oscillator problems": 9,
    "Two-body problems": 10,
    "Multi-particle systems": 11,
    "Rigid bodies": 12,
    "Non-linear oscillations": 13,
    "Translation and rotation of the reference frame": 14,
    "The relativity principle and some of its consequences": 15,
}

HEADER_RE = re.compile(r"^\\section\*\{(.*)\}\s*$")
QUESTION_RE = re.compile(r"^Question (\d+)\.(\d+)$")
REF_LINE_RE = re.compile(r"^\[(\d+)\]\s+\S")
SYM_LINE_RE = re.compile(r"^(?:\\\(\{\s*\}\^\{\\(dagger|ddagger)\}\\\)|([†‡]))\s*\S")
CITE_RE = re.compile(r"\^\{\[([0-9,\s\-–]+)\]\}")
# "Ref. [9]", 'the Moon". [6]' -- but not Mathematica's "In [2] :=" or a[1]
PROSE_CITE_RE = re.compile(r"(?<![\\\w\[{])\[(\d+(?:\s*[,\-–]\s*\d+)*)\](?!\s*:=)")
SYM_MARK_RE = re.compile(r"\^\{\\(dagger|ddagger)\}")
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
VERBATIM_RE = re.compile(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", re.S)
DISPLAY_RE = re.compile(
    r"(?<!\\)\\\[.*?(?<!\\)\\\]"  # \[ ... \], but not the \[0pt] of a \\[0pt] line break
    r"|\\begin\{(align\*?|aligned|equation\*?|gather\*?|gathered|array)\}.*?\\end\{\1\}",
    re.S,
)
INLINE_RE = re.compile(r"(?<!\\)\\\(.*?(?<!\\)\\\)", re.S)
# Mathematica as typeset by Mathpix: "\operatorname{In}[1]:=", "\text { In [1] }:=", NDSolve[...], ...
CODE_RE = re.compile(r"NDSolve|NIntegrate|ParametricPlot|FindRoot|\bThread\b|\bChop\b|Plot\s*\[|Table\s*\[|I\s?n\s*\}?\s*\[[^\]]{0,3}\]")
CODE_TOKEN = "@@CODE@@"
CODE_OMITTED = "\\textit{(Mathematica code omitted.)}"
NOTE_TOKEN = "@@NOTE:{}@@"
NOTE_TOKEN_RE = re.compile(r"^@@NOTE:(\d+)@@$")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")

# Question 12.10: Mathpix turned the book's three-column table into loose text.
Q12_10 = r"""Use the method of Question 12.9 to obtain the following moments of inertia for homogeneous solids of revolution:

\begin{center}
\begin{tabular}{lll}
\hline
Solid & Axis & Moment of inertia \\
\hline
1. sphere (radius \(=a\)) & any diameter & \(\frac{2}{5} M a^{2}\) \\
2. spherical shell (outer radius \(=a\), inner radius \(=b\)) & any diameter & \(\frac{2}{5} M\left(\frac{a^{5}-b^{5}}{a^{3}-b^{3}}\right)\) \\
3. thin spherical shell (radius \(=a\)) & any diameter & \(\frac{2}{3} M a^{2}\) \\
4. circular cylinder (radius \(=a\), height \(=h\)) & longitudinal axis & \(\frac{1}{2} M a^{2}\) \\
 & perpendicular axis through the CM & \(\frac{1}{4} M a^{2}+\frac{1}{12} M h^{2}\) \\
5. circular cylindrical pipe (outer radius \(=a\), inner radius \(=b\), height \(=h\)) & longitudinal axis & \(\frac{1}{2} M\left(a^{2}+b^{2}\right)\) \\
 & perpendicular axis through the CM & \(\frac{1}{4} M\left(a^{2}+b^{2}\right)+\frac{1}{12} M h^{2}\) \\
6. thin cylindrical pipe (radius \(=a\), height \(=h\)) & longitudinal axis & \(M a^{2}\) \\
 & perpendicular axis through the CM & \(\frac{1}{2} M a^{2}+\frac{1}{12} M h^{2}\) \\
7. ellipsoid of revolution (semi-axes \(=a, b, b\)) & \(x\)-axis & \(\frac{2}{5} M b^{2}\) \\
 & \(y\)-axis & \(\frac{1}{5} M\left(a^{2}+b^{2}\right)\) \\
8. circular cone (radius \(=a\), height \(=h\)) & axis of symmetry & \(\frac{3}{10} M a^{2}\) \\
 & perpendicular axis through the vertex & \(\frac{3}{20} M a^{2}+\frac{3}{5} M h^{2}\) \\
9. torus (rotating the circle \(x^{2}+(y-a)^{2}=b^{2}\), \(a>b\), about the \(x\)-axis) & \(x\)-axis & \(M a^{2}+\frac{3}{4} M b^{2}\) \\
\hline
\end{tabular}
\end{center}"""


@dataclass
class Part:
    qkey: str  # "2.1"
    kind: str  # question | solution | comments
    label: str = ""  # "Comment" or "Comments" for kind == comments
    lines: list[str] = field(default_factory=list)
    notes: list[int] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


@dataclass
class Note:
    text: str
    ref: int | None  # chapter-local reference number, if a "[n] ..." note
    sym: str | None  # "dagger" / "ddagger" for symbol notes
    chapter: int
    where: tuple[int, int] | None = None  # (part index, line count) where it sat in the text


def _match_brace(s: str, i: int) -> int:
    """s[i] == '{'; return the index of its closing brace."""
    depth = 0
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
    raise ValueError("unbalanced braces")


def _split_note_block(content: str) -> list[str]:
    """One \\footnotetext block can hold several notes, one per line."""
    notes: list[str] = []
    for line in content.strip().split("\n"):
        line = TRAILING_BREAK_RE.sub("", line).strip()
        if not line:
            continue
        if notes and not (REF_LINE_RE.match(line) or SYM_LINE_RE.match(line)):
            notes[-1] += " " + line
        else:
            notes.append(line)
    return notes


def _classify(note: str) -> tuple[int | None, str | None]:
    m = REF_LINE_RE.match(note)
    if m:
        return int(m.group(1)), None
    m = SYM_LINE_RE.match(note)
    if m:
        return None, m.group(1) or {"†": "dagger", "‡": "ddagger"}[m.group(2)]
    return None, None


def _cited_numbers(text: str) -> set[int]:
    """Reference numbers cited as a superscript ^{[1,2]} or in prose ("Ref. [9]")."""
    text = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", "", text, flags=re.S)
    nums: set[int] = set()
    for m in list(CITE_RE.finditer(text)) + list(PROSE_CITE_RE.finditer(text)):
        for piece in re.split(r",", m.group(1)):
            piece = piece.strip()
            r = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", piece)
            if r:
                nums.update(range(int(r.group(1)), int(r.group(2)) + 1))
            elif piece.isdigit():
                nums.add(int(piece))
    return nums


def parse(tex: str) -> tuple[list[dict], list[str]]:
    """Return (rows, log lines)."""
    log: list[str] = []
    body = tex[tex.index("\\begin{document}") + len("\\begin{document}"):]
    body = body[: body.rindex("\\end{document}")]

    # 1. Cut \footnotetext blocks out, leaving a token line where each note sat.
    raw_notes: list[str] = []
    out, i = [], 0
    while True:
        j = body.find("\\footnotetext", i)
        if j < 0:
            out.append(body[i:])
            break
        k = body.index("{", j)
        end = _match_brace(body, k)
        out.append(body[i:j])
        tokens = []
        for note in _split_note_block(body[k + 1:end]):
            tokens.append(NOTE_TOKEN.format(len(raw_notes)))
            raw_notes.append(note)
        out.append("\n" + "\n".join(tokens) + "\n")
        i = end + 1
    body = "".join(out)

    # 2. Headers that are not at the start of a line.
    body = re.sub(r"(?<=[^\n])\\section\*\{", "\n\\\\section*{", body)

    # 3. Bare page-bottom note lines (outside verbatim) become tokens too.
    lines = body.split("\n")
    in_verb = False
    for n, line in enumerate(lines):
        if "\\begin{verbatim}" in line:
            in_verb = True
        if "\\end{verbatim}" in line:
            in_verb = False
            continue
        if in_verb:
            continue
        if REF_LINE_RE.match(line) or SYM_LINE_RE.match(line):
            lines[n] = NOTE_TOKEN.format(len(raw_notes))
            raw_notes.append(TRAILING_BREAK_RE.sub("", line).strip())

    # 4. Re-join the text around each run of note tokens.
    lines = _rejoin(lines)

    # 5. Walk the headers.
    parts: list[Part] = []
    notes: list[Note] = []
    order: list[str] = []
    cur: Part | None = None
    chapter = 0
    pending_chapter_number = False
    for line in lines:
        tm = NOTE_TOKEN_RE.match(line)
        if tm:
            idx = int(tm.group(1))
            ref, sym = _classify(raw_notes[idx])
            where = (len(parts) - 1, len(cur.lines)) if cur is not None else None
            notes.append(Note(raw_notes[idx], ref, sym, chapter, where))
            continue
        hm = HEADER_RE.match(line)
        if hm:
            title = hm.group(1).strip()
            qm = QUESTION_RE.match(title)
            if qm:
                chapter = int(qm.group(1))
                key = f"{qm.group(1)}.{qm.group(2)}"
                cur = Part(key, "question")
                parts.append(cur)
                order.append(key)
                pending_chapter_number = False
                continue
            if title.isdigit():
                chapter, cur, pending_chapter_number = int(title), None, True
                continue
            if title in CHAPTER_TITLES:
                if not pending_chapter_number:
                    chapter = CHAPTER_TITLES[title]
                cur, pending_chapter_number = None, False
                continue
            if cur is None:
                log.append(f"header in chapter intro dropped: {title}")
                continue
            if title == "Solution":
                if any(p.qkey == cur.qkey and p.kind == "solution" for p in parts):
                    log.append(f"Q{cur.qkey}: second Solution header")
                cur = Part(cur.qkey, "solution")
                parts.append(cur)
                continue
            if title in ("Comment", "Comments"):
                cur = Part(cur.qkey, "comments", label=title)
                parts.append(cur)
                continue
            log.append(f"Q{cur.qkey} {cur.kind}: header '{title}' -> \\paragraph")
            cur.lines.append(f"\\paragraph{{{title}}}")
            continue
        if cur is not None:
            cur.lines.append(line)

    _assign_notes(parts, notes, log)

    rows = []
    for key in order:
        qparts = [p for p in parts if p.qkey == key]
        q = next(p for p in qparts if p.kind == "question")
        sols = [p for p in qparts if p.kind == "solution"]
        comms = [p for p in qparts if p.kind == "comments"]
        question = _clean(q.text)
        if key == "12.10":
            if not question.startswith("Use the method of Question 12.9"):
                raise RuntimeError("Q12.10 text changed; check the table fix")
            question = Q12_10
        question = _with_notes(question, [notes[i].text for i in q.notes])
        sol_chunks = [strip_code(_clean(p.text)) for p in sols]
        for c in comms:
            sol_chunks.append(f"\\paragraph{{{c.label}}}\n" + strip_code(_clean(c.text)))
        sol_notes = [notes[i].text for p in sols + comms for i in p.notes]
        solution = _with_notes("\n\n".join(x for x in sol_chunks if x), sol_notes)
        if not sols:
            log.append(f"Q{key}: NO SOLUTION")
        rows.append({"key": key, "latexcode": question, "solution": solution or None})
    return rows, log


def _rejoin(lines: list[str]) -> list[str]:
    """Drop the line break a page-bottom note left behind in the running text."""
    out: list[str] = []
    n = 0
    while n < len(lines):
        if not NOTE_TOKEN_RE.match(lines[n]):
            out.append(lines[n])
            n += 1
            continue
        run = []
        while n < len(lines) and (NOTE_TOKEN_RE.match(lines[n]) or (run and not lines[n].strip() and n + 1 < len(lines) and NOTE_TOKEN_RE.match(lines[n + 1]))):
            if lines[n].strip():
                run.append(lines[n])
            n += 1
        # previous text line (skipping blank lines) and the next text line
        blanks = 0
        while out and not out[-1].strip():
            out.pop()
            blanks += 1
        nxt = n
        while nxt < len(lines) and not lines[nxt].strip():
            nxt += 1
        following = lines[nxt].lstrip() if nxt < len(lines) else ""
        prev = out[-1] if out else ""
        continuation = bool(prev.strip()) and bool(following) and (
            following[0].islower() or following.startswith("\\(")
        )
        if continuation:
            # The note split a sentence: drop the page break and glue the
            # next line on (an image keeps its own line).
            if not prev.lstrip().startswith("\\includegraphics"):
                out[-1] = TRAILING_BREAK_RE.sub("", prev)
            out.extend(run)
            n = nxt
            continue
        out.extend([""] * blanks)
        out.extend(run)
    return out


def _assign_notes(parts: list[Part], notes: list[Note], log: list[str]) -> None:
    chapter_of = {i: int(p.qkey.split(".")[0]) for i, p in enumerate(parts)}
    # Symbol notes first: a dagger note can itself cite a reference, which
    # then belongs wherever the dagger note goes.
    order = [ni for ni, n in enumerate(notes) if n.ref is None] + [ni for ni, n in enumerate(notes) if n.ref is not None]
    for ni in order:
        note = notes[ni]
        targets: list[int] = []
        if note.ref is not None:
            targets = [
                i for i, p in enumerate(parts)
                if chapter_of[i] == note.chapter
                and note.ref in _cited_numbers("\n".join([p.text] + [notes[k].text for k in p.notes]))
            ]
        elif note.sym is not None and note.where is not None:
            pi, upto = note.where
            # nearest marker of that symbol before the note, looking back up to 4 parts
            for back in range(pi, max(-1, pi - 5), -1):
                text = "\n".join(parts[back].lines[:upto] if back == pi else parts[back].lines)
                if any(m.group(1) == note.sym for m in SYM_MARK_RE.finditer(text)):
                    targets = [back]
                    break
        if not targets and note.where is not None:
            targets = [note.where[0]]
            log.append(f"note {ni} (ch {note.chapter}) has no marker; left at Q{parts[note.where[0]].qkey}: {note.text[:70]}")
        if not targets:
            log.append(f"note {ni} (ch {note.chapter}) dropped (chapter intro): {note.text[:70]}")
        for t in targets:
            if ni not in parts[t].notes:
                parts[t].notes.append(ni)


def _clean(text: str) -> str:
    text = text.replace("\\captionsetup{singlelinecheck=false}", "")
    text = re.sub(r"(^|\n)□\s*", r"\1\\(\\square\\) ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = TRAILING_BREAK_RE.sub("", text)
    return text.strip()


def strip_code(text: str) -> str:
    """Delete the Mathematica cells; one marker per run of adjacent cells."""
    text = VERBATIM_RE.sub(CODE_TOKEN, text)
    for rx in (DISPLAY_RE, INLINE_RE):
        text = rx.sub(lambda m: CODE_TOKEN if CODE_RE.search(m.group(0)) else m.group(0), text)
    # cells separated only by whitespace, line breaks or an emptied center block
    text = re.sub(r"\\begin\{center\}\s*(@@CODE@@\s*)+\\end\{center\}", CODE_TOKEN, text)
    text = re.sub(r"@@CODE@@(?:\s*(?:\\\\(?:\[0pt\])?)?\s*@@CODE@@)+", CODE_TOKEN, text)
    # a cell left alone on a line keeps that line; one inside a line gets its own paragraph
    text = re.sub(r"[ \t]*@@CODE@@[ \t]*(?:\\\\(?:\[0pt\])?)?", lambda m: "\n\n" + CODE_OMITTED + "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _with_notes(text: str, notes: list[str]) -> str:
    seen: list[str] = []
    for n in notes:
        if n not in seen:
            seen.append(n)
    if not seen:
        return text
    return text + "\n\n\\paragraph{Notes}\n" + "\n\n".join(seen)


def check(rows: list[dict], images_dir: Path) -> list[str]:
    problems = []
    for r in rows:
        for fld in ("latexcode", "solution"):
            t = r[fld] or ""
            if not t.strip():
                problems.append(f"Q{r['key']}: empty {fld}")
                continue
            # OCR'd Mathematica code is often garbled, but verbatim does not parse it
            t = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", "", t, flags=re.S)
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
                problems.append(f"Q{r['key']} {fld}: unbalanced braces")
            begins = re.findall(r"\\begin\{([^}]+)\}", t)
            ends = re.findall(r"\\end\{([^}]+)\}", t)
            if sorted(begins) != sorted(ends):
                problems.append(f"Q{r['key']} {fld}: environments {sorted(begins)} vs {sorted(ends)}")
            if (t.count("\\(") - t.count("\\\\(") != t.count("\\)")
                    or t.count("\\[") - t.count("\\\\[") != t.count("\\]")):
                problems.append(f"Q{r['key']} {fld}: unbalanced math delimiters")
            if "\\section" in t or "@@NOTE" in t or "\\footnotetext" in t:
                problems.append(f"Q{r['key']} {fld}: leftover header/note")
            for name in IMG_RE.findall(t):
                if not (images_dir / f"{name}.jpg").is_file():
                    problems.append(f"Q{r['key']} {fld}: missing image {name}")
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


def update_solutions(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        changed = missing = 0
        for r in rows:
            hit = conn.execute(
                "SELECT question_id, solution FROM questions WHERE latex_hash = ? AND source = ?",
                (latex_hash(r["latexcode"]), SOURCE),
            ).fetchone()
            if hit is None:
                missing += 1
            elif hit[1] != r["solution"]:
                conn.execute("UPDATE questions SET solution = ? WHERE question_id = ?", (r["solution"], hit[0]))
                changed += 1
        conn.commit()
    finally:
        conn.close()
    print(f"solutions_updated={changed} not_in_db={missing}")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tex", type=Path, required=True)
    p.add_argument("--images", type=Path, help="images folder (default: images/ next to the .tex)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--update-solutions", action="store_true")
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
    if (args.apply or args.update_solutions) and problems:
        print("refusing to write with problems")
        return 1
    if args.apply:
        apply(rows, images_dir)
    if args.update_solutions:
        update_solutions(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
