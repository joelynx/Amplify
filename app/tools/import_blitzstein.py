"""
Import Blitzstein and Hwang, *Introduction to Probability* (2nd ed.),
end-of-chapter exercises
---------------------------------------------------------------------
Reads the Mathpix LaTeX export of the book's Exercises sections (chapters
1-13; one .tex file plus an images/ folder) and adds every exercise to
amplify.db. The book has no answers or solutions (those of the exercises it
marks with (s) are on stat110.net), so the rows have none.

Layout of the export:
    <main text>                       the end of the chapter's R section on the page where
                                      the exercises start (dropped; see MAIN_TEXT_STARTS)
    \\subsection*{3.12 Exercises}
    \\section*{PMFs and CDFs}          the book's topic headings (dropped; HEADINGS)
    \\begin{itemize}
      \\item[1.] (s) Text ...          an exercise, (s) marking those solved on stat110.net
      \\begin{itemize}
        \\item[(a)] ...                its parts
    ...
Exercises also start as a plain "58. Text" line or as the items of a
\\begin{enumerate} with \\setcounter{enumi}{58}; parts also come as plain
"(a) Text" lines, and a page break often leaves the rest of an exercise in a
list of its own, or in an \\item[] continuation.

So each exercise is rebuilt from the lines it owns, in one shape: its stem,
then an itemize of its parts (a), (b), ... (a part starts at the next letter
in sequence, as an item label or at the start of a line), with any other
labelled items (steps 1., 2., ...; (i), (ii), ...; A:, B:, ...; bullets)
kept as a list inside the stem or part they belong to. Hints stay where the
book prints them, after the stem or part they follow.

Repairs made on the way in:
  * The (s) markers, the topic headings and the "Exercises marked with (s)
    ..." notes are dropped.
  * Line breaks: stray "\\\\" lines (Mathpix's breaks around displays) are
    dropped, and a "\\\\" that breaks a sentence (the book's line end) or a
    paragraph break where a page break cut a sentence in two is joined up;
    displays, code and tables are left alone.
  * × (2 × 2 table), ⊕ and • in text become math; "\\(j\\) th" becomes
    "\\(j\\)th" and "\\(p_{i}\\) 's" "\\(p_{i}\\)'s"; a list split at a page break
    is joined up.
  * Misreads found by checking every exercise against the book pages are
    corrected from blitzstein_fixes.json (page and reason on each; they apply
    to the text as it stands after the steps above). Kind "structure" fixes
    repair the raw export before it is parsed (the lost chapter 2 header);
    kind "book" fixes correct the book's own errors (typos, y_n for y_N in
    4.54, X > a for X > c in 5.4, a conditional PMF asked for twice in 7.5).
    The rest restore math Mathpix flattened or put in text (bold vectors,
    subscripts, minus signs, sets and points), R code it set as math (now
    \\texttt), parts and hints it attached to the wrong place, 1.21's missing
    partition, 1.29's footnote (it had landed in 1.31), and 1.48's
    certificate box.
  * Last, after the fixes: Mathpix's "\\\\" + blank line before a display is
    dropped (it broke the sentence), a "Hint:" LaTeX would run into the line
    before gets a line of its own, and negative numbers in prose get a minus
    sign instead of a hyphen.

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings
(run app/tools/reembed.py later for similarity search). Idempotent on
latex_hash, like the seed ingest. Referenced images are copied to
app/data/appdata/teximages/ and Files/images/.

Usage (repo root):
  python -m app.tools.import_blitzstein --tex <export.tex> --dry-run [--dump out.json]
  python -m app.tools.import_blitzstein --tex <export.tex> --apply
  python -m app.tools.import_blitzstein --tex <export.tex> --update book   (rows already imported)
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
SOURCE = "Blitzstein and Hwang's Introduction to Probability"
UNCATEGORIZED = "Uncategorized"

DB_PATH = Path("app/data/appdata/amplify.db")
TEXIMAGES = Path("app/data/appdata/teximages")
REPO_IMAGES = Path("Files/images")

FIRST_CHAPTER, LAST_CHAPTER = 1, 13
# "\subsection*{3.12 Exercises}", or a plain "9.9 Exercises" line
EXERCISES_RE = re.compile(r"^(?:\\subsection\*\{)?(\d+)\.\d+ Exercises\}?$")
SOLUTIONS_NOTE_RE = re.compile(r"^Exercises marked with \([sS]\) have detailed solutions at")

# The R section that precedes a chapter's Exercises on their first page: the start of
# its first line, and how many lines before that line also belong to it. Everything
# from there to the next exercises header is dropped. (Chapters 1, 2, 6 and 12 have
# none in the export.)
MAIN_TEXT_STARTS = [
    ("Next, we use sample. Here's how to get 100 draws", 0),  # ch 3
    ("is mean(r). We can compare the simulated value", 0),  # ch 4
    ("Now x contains \\(10^{4}\\) realizations", 0),  # ch 5
    ("For an amusing demonstration of the very heavy tails", 0),  # ch 7
    ("If we want to plot a histogram of realizations of, say", 0),  # ch 8
    ("Linear regression\\\\", 0),  # ch 9
    ("Now, to obtain realizations of \\(\\bar{X}_{12}\\)", 0),  # ch 10
    ("0,1,0,0,", 1),  # ch 11, after its \begin{lstlisting}
    ("We can carry out this procedure for \\(p=0.3\\)", 0),  # ch 13
]

# The book's topic headings inside the Exercises sections (bold in the book).
HEADINGS = {
    "Counting", "Story proofs", "Naive definition of probability", "Axioms of probability",
    "Inclusion-exclusion", "Mixed practice", "Conditioning on evidence",
    "Independence and conditional independence", "Monty Hall", "First-step analysis and gambler's ruin",
    "Simpson's paradox", "PMFs and CDFs", "Named distributions", "Independence of r.v.s",
    "Expectations and variances", "Indicator r.v.s", "LOTUS", "Poisson approximation", "*Existence",
    "PDFs and CDFs", "Uniform and universality of the Uniform", "Normal", "Exponential",
    "Means, medians, modes, and moments", "Moment generating functions",
    "Joint, marginal, and conditional distributions", "2D LOTUS", "Covariance", "Chicken-egg",
    "Multinomial", "Multivariate Normal", "Change of variables", "Convolutions", "Beta and Gamma",
    "Order statistics", "Conditional expectation given an event",
    "Conditional expectation given a random variable", "Inequalities", "Fill-in-the-blank inequalities",
    "LLN and CLT", "Markov property", "Stationary distribution", "Reversibility",
}
SECTION_RE = re.compile(r"^\\section\*\{(.*)\}$")

LIST_BEGIN_RE = re.compile(r"^\\begin\{(itemize|enumerate)\}$")
LIST_END_RE = re.compile(r"^\\end\{(itemize|enumerate)\}$")
SETCOUNTER_RE = re.compile(r"^\\setcounter\{enumi\}\{(\d+)\}$")
ITEM_RE = re.compile(r"^\\item(?:\[([^\]]*)\])?\s*(.*)$")
PLAIN_EXERCISE_RE = re.compile(r"^(\d+)\.\s+(.*)$")
PART_LINE_RE = re.compile(r"^\(([a-z])\)\s*(.*)$")
PART_LABEL_RE = re.compile(r"^\(([a-z])\)$")
ROMAN_LABELS = {"(i)", "(ii)", "(iii)", "(iv)", "(v)", "(vi)"}
# the (s) marker, as Mathpix reads it
MARKER_RE = re.compile(r"^(?:\(\s*[sS]\s*\)|[sS]\))\s*")
VERBATIM_BEGIN_RE = re.compile(r"^\\begin\{(verbatim|lstlisting)\}")

IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
BREAK_LINE_RE = re.compile(r"^\s*\\\\(?:\[0pt\])?\s*$")
TRAILING_BREAK_RE = re.compile(r"\s*\\\\(?:\[0pt\])?\s*$")

FIXES_PATH = Path(__file__).with_name("blitzstein_fixes.json")


# Displays, code and tables, where line breaks are left alone.
PROTECTED_RE = re.compile(
    r"\\\[.*?\\\]|\\begin\{(verbatim|lstlisting|tabular)\}.*?\\end\{\1\}", re.S)


def _join_text(text: str) -> str:
    # a forced break in mid-sentence (the book's line end): "ob-\\ served", "a random\\ sample"
    text = re.sub(r"([A-Za-z])-\\\\\s*\n([a-z])", r"\1\2", text)
    text = re.sub(r"\s*\\\\\s*\n(?=[a-z]|\\\$)", " ", text)
    # a sentence cut in two by a page break: "Fred randomly\n\nchooses", "for students\n\n\(2 n+1\)"
    return re.sub(r"(?:(?<=[A-Za-z0-9,;])|(?<=\\\)))\n\n+(?=[a-z]|\\\()", " ", text)


def _clean(text: str) -> str:
    lines = [ln for ln in text.split("\n") if not BREAK_LINE_RE.match(ln)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    out, k = [], 0
    for m in PROTECTED_RE.finditer(text):
        out += [_join_text(text[k:m.start()]), m.group(0)]
        k = m.end()
    text = "".join(out + [_join_text(text[k:])])
    text = TRAILING_BREAK_RE.sub("", text)
    return text.strip()


# Characters Mathpix leaves in text that belong in math.
UNICODE_MATH = [
    (re.compile(r"\b(\d+) ?× ?(\d+)\b"), r"\(\1 \\times \2\)"),  # "a 2 × 2 table"
    (re.compile(r"×"), r"\(\\times\)"),
    (re.compile(r"\b(\d+) ?• ?(\d+)\b"), r"\(\1 \\cdot \2\)"),  # "24 • 23"
    (re.compile(r"⊕"), r"\(\\oplus\)"),
]


ORDINAL_RE = re.compile(r"\\\) (th|st|nd|rd|'s)\b")  # "the \(j\) th passenger", "the \(p_{i}\) 's"
SPLIT_LIST_RE = re.compile(r"\n\\end\{itemize\}\s*\\begin\{itemize\}\n")


def _normalize(text: str) -> str:
    """Before the fixes (they were written against this text): unicode math, "\\(j\\)th" and
    "\\(p_{i}\\)'s", and a list split at a page break joined up."""
    for pat, rep in UNICODE_MATH:
        text = pat.sub(rep, text)
    text = ORDINAL_RE.sub(r"\\)\1", text)
    return SPLIT_LIST_RE.sub("\n", text)


# Mathpix's "text\\" + blank line before a display: the display belongs to the sentence.
DISPLAY_BREAK_RE = re.compile(r"\\\\\n\n(?=\\\[)")
# A "Hint:" line that LaTeX would run into the line before it.
HINT_RE = re.compile(r"^(?:General hint|Hints?\b)")
LINE_ENDS_BLOCK_RE = re.compile(r"(?:\\\\|\\\]|\\end\{[^}]*\}|\\begin\{[^}]*\})\s*$")


def _hints_on_own_line(text: str) -> str:
    lines = text.split("\n")
    for i in range(1, len(lines)):
        prev = lines[i - 1]
        if HINT_RE.match(lines[i]) and prev.strip() and not LINE_ENDS_BLOCK_RE.search(prev):
            lines[i - 1] = prev.rstrip() + "\\\\"
    return "\n".join(lines)


# Math, code and tables, where a hyphen before a digit is left alone.
MATH_OR_CODE_RE = re.compile(
    r"\\\(.*?\\\)|\\\[.*?\\\]|\\texttt\{[^}]*\}|\\begin\{(verbatim|lstlisting|tabular)\}.*?\\end\{\1\}", re.S)
PROSE_NEGATIVE_RE = re.compile(r"(?<=[\s(\[{,])-(\d+(?:\.\d+)?)\b")  # "the interval (-1, 1)", "at least -2"


def _prose_negatives(text: str) -> str:
    out, k = [], 0
    for m in MATH_OR_CODE_RE.finditer(text):
        out += [PROSE_NEGATIVE_RE.sub(r"\\(-\1\\)", text[k:m.start()]), m.group(0)]
        k = m.end()
    return "".join(out + [PROSE_NEGATIVE_RE.sub(r"\\(-\1\\)", text[k:])])


def _finish(text: str) -> str:
    """Last pass, after the fixes: no paragraph break between a sentence and its display, each
    hint on a line of its own, and negative numbers in prose set with a minus sign instead of
    a hyphen."""
    text = DISPLAY_BREAK_RE.sub("\n", text)
    text = _hints_on_own_line(text)
    return _prose_negatives(text)


class _Exercise:
    """The lines of one exercise, sorted into its stem and parts as they arrive."""

    def __init__(self, key: str, chapter: int, num: int, marked: bool):
        self.key, self.chapter, self.num, self.marked = key, chapter, num, marked
        self.units: list[list] = [[None, []]]  # [label, lines]; the first is the stem
        self.next_part = "a"
        self.sub_depth: int | None = None  # list depth of an open list of other items
        self.notes: list[str] = []

    def _lines(self) -> list[str]:
        return self.units[-1][1]

    def _close_sub(self) -> None:
        if self.sub_depth is not None:
            self._lines().append("\\end{itemize}")
            self.sub_depth = None

    def _new_part(self, letter: str, text: str) -> None:
        self._close_sub()
        self.units.append([f"({letter})", [text]])
        self.next_part = chr(ord(letter) + 1)

    def item(self, label: str | None, text: str, depth: int) -> None:
        m = PART_LABEL_RE.match(label or "")
        if m and (label not in ROMAN_LABELS or m.group(1) == self.next_part):
            if m.group(1) != self.next_part:
                self.notes.append(f"part {label} where ({self.next_part}) was expected")
            self._new_part(m.group(1), text)
            return
        if label == "":  # \item[]: a continuation after a page break
            if text:
                self.text(text, depth)
            return
        if self.sub_depth is None or depth < self.sub_depth:
            self._close_sub()
            self._lines().append("\\begin{itemize}")
            self.sub_depth = depth
        self._lines().append(f"  \\item[{label}] {text}" if label is not None else f"  \\item {text}")

    def text(self, line: str, depth: int, verbatim: bool = False) -> None:
        if verbatim:
            self._lines().append(line)
            return
        s = line.strip()
        m = PART_LINE_RE.match(s)
        if m and m.group(1) == self.next_part:
            self._new_part(m.group(1), m.group(2))
            return
        if self.sub_depth is not None and depth < self.sub_depth and s:
            self._close_sub()
        self._lines().append(s)

    def list_end(self, depth: int) -> None:
        if self.sub_depth is not None and depth <= self.sub_depth:
            self._close_sub()

    def render(self) -> str:
        self._close_sub()
        stem = _clean("\n".join(self.units[0][1]))
        if len(self.units) == 1:
            return stem
        items = [f"  \\item[{label}] {_clean(chr(10).join(lines))}" for label, lines in self.units[1:]]
        body = "\\begin{itemize}\n" + "\n".join(items) + "\n\\end{itemize}"
        return f"{stem}\n\n{body}" if stem else body


def _load_fixes(skip_kinds: frozenset[str]) -> list[dict]:
    if not FIXES_PATH.is_file():
        return []
    return [f for f in json.loads(FIXES_PATH.read_text(encoding="utf-8")) if f["kind"] not in skip_kinds]


def _replace_once(text: str, old: str, new: str, where: str) -> str:
    hits = text.count(old)
    if hits != 1:
        raise SystemExit(f"FIX {where}: expected 1 match, found {hits}: {old[:60]!r}")
    return text.replace(old, new)


def _heading(s: str) -> str | None:
    m = SECTION_RE.match(s)
    t = (m.group(1) if m else s).removesuffix("\\\\").strip()
    return t if t in HEADINGS else None


def parse(tex: str, skip_kinds: frozenset[str] = frozenset()) -> tuple[list[dict], list[str], dict]:
    fixes = _load_fixes(skip_kinds)
    body = tex.split("\\begin{document}", 1)[1].split("\\end{document}", 1)[0]
    for fix in fixes:
        if fix["kind"] == "structure":
            body = _replace_once(body, fix["old"], fix["new"], f"structure {fix.get('key', '')}")
    lines = body.split("\n")
    log: list[str] = []
    dropped: dict[str, list[str]] = {"main text": [], "headings": [], "other": []}

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

    exercises: list[_Exercise] = []
    chapter = None
    cur: _Exercise | None = None
    stack: list[dict] = []  # open lists: {"env": ..., "count": enumerate counter}
    verbatim = False

    def start(num: int, text: str) -> None:
        nonlocal cur
        marked = bool(MARKER_RE.match(text))
        cur = _Exercise(f"{chapter}.{num}", chapter, num, marked)
        exercises.append(cur)
        cur.text(MARKER_RE.sub("", text), len(stack))

    for n, line in enumerate(lines):
        s = line.strip()
        if verbatim:
            if cur is not None and not skip[n]:
                cur.text(line, len(stack), verbatim=True)
            if s.startswith("\\end{verbatim}") or s.startswith("\\end{lstlisting}"):
                verbatim = False
            continue
        m = EXERCISES_RE.match(s)
        if m:
            chapter, cur, stack = int(m.group(1)), None, []
            if chapter != (exercises[-1].chapter + 1 if exercises else FIRST_CHAPTER):
                raise SystemExit(f"chapter {chapter} out of order")
            continue
        if skip[n] or chapter is None:
            if s:
                dropped["main text"].append(s)
            if VERBATIM_BEGIN_RE.match(s):
                verbatim = True
            continue
        if _heading(s):
            dropped["headings"].append(f"{chapter}: {_heading(s)}")
            continue
        if SOLUTIONS_NOTE_RE.match(s):
            dropped["other"].append(s)
            continue
        if m := LIST_BEGIN_RE.match(s):
            stack.append({"env": m.group(1), "count": 0})
            continue
        if LIST_END_RE.match(s):
            if cur is not None:
                cur.list_end(len(stack))
            if stack:
                stack.pop()
            else:
                log.append(f"line {n + 1}: \\end of a list that is not open")
            continue
        if m := SETCOUNTER_RE.match(s):
            stack[-1]["count"] = int(m.group(1))
            continue
        last = cur.num if cur is not None else 0
        if m := ITEM_RE.match(s):
            label, text = m.group(1), m.group(2)
            if label is None and stack and stack[-1]["env"] == "enumerate":
                stack[-1]["count"] += 1
                label = f"{stack[-1]['count']}."
            if label and re.fullmatch(r"\d+\.", label) and int(label[:-1]) == last + 1 and len(stack) == 1:
                start(last + 1, text)
            elif cur is None:
                log.append(f"chapter {chapter}: item before the first exercise: {s[:80]}")
            else:
                cur.item(label, text, len(stack))
            continue
        if (m := PLAIN_EXERCISE_RE.match(s)) and int(m.group(1)) == last + 1:
            start(last + 1, m.group(2))
            continue
        if VERBATIM_BEGIN_RE.match(s):
            verbatim = True
        if cur is not None:
            cur.text(line, len(stack))
        elif s:
            log.append(f"chapter {chapter}: text before the first exercise: {s[:80]}")

    out = []
    for e in exercises:
        out.append({"key": e.key, "chapter": e.chapter, "num": e.num, "marked": e.marked,
                    "parts": [u[0] for u in e.units[1:]], "latexcode": _normalize(e.render())})
        log += [f"{e.key}: {note}" for note in e.notes]

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
        envs = re.findall(r"\\(begin|end)\{([^}]+)\}", t)
        stack = []
        for kind, name in envs:
            if kind == "begin":
                stack.append(name)
            elif not stack or stack.pop() != name:
                problems.append(f"{r['key']}: environments out of order")
                break
        else:
            if stack:
                problems.append(f"{r['key']}: unclosed {stack}")
        if (t.count("\\(") - t.count("\\\\(") != t.count("\\)")
                or t.count("\\[") - t.count("\\\\[") != t.count("\\]")):
            problems.append(f"{r['key']}: unbalanced math delimiters")
        if re.search(r"\\(?:sub)*section|Exercises marked|stat110|^\s*\d+\.\s", t, re.M):
            problems.append(f"{r['key']}: leftover header, note or exercise number")
        if MARKER_RE.match(t) or re.match(r"^\\begin\{itemize\}\n  \\item\[\(a\)\] (?:\([sS]\)|[sS]\))", t):
            problems.append(f"{r['key']}: (s) marker left in the text")
        if re.search(r"[×⊕•]", t):
            problems.append(f"{r['key']}: a character to set as math")
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
    print(f"questions={len(rows)} marked={sum(r['marked'] for r in rows)} images={len(images_used(rows))} "
          + " ".join(f"dropped_{k.replace(' ', '_')}={len(v)}" for k, v in dropped.items())
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
