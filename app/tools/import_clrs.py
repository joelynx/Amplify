"""
Import CLRS exercises and problems
----------------------------------
Cormen, Leiserson, Rivest and Stein, Introduction to Algorithms (3rd edition): the exercises and the
end-of-chapter problems as transcribed, with community solutions, in github.com/walkccc/CLRS (MIT licence for the
repo, the book text is the authors'; Amplify is private). The raw Markdown is read, not the parsed Hugging Face copy
(Siddharth899/clrs-qa): the HF rows cut the statement of many problems after the first paragraph, the raw files do not.

Rows: 851 exercises (docs/ChapNN/N.M.md, "## N.M-K" headings, statement as a ">" block) and 151 problems
(docs/ChapNN/Problems/N-K.md). Every one is kept (proofs, derivations, analysis, designs answered in pseudocode, data
structures) except (CLRS_DROPS below):
  * statements that depend on a figure the Markdown does not carry (a graph, tree, flow network or table that is
    only drawn); "Using Figure 2.2 as a model, illustrate ... on the array A = <...>" keeps its data and loses the
    figure reference; a figure that only illustrates a definition or an example has that sentence cut (FIGURE_CUTS);
  * statements the source cuts short, or that only name a result of the book ("Prove Corollary 24.3").
Nothing asks for runnable code in a named language (checked: no statement names C, Java, Python and so on).

Source "Cormen, Leiserson, Rivest and Stein's Introduction to Algorithms", subsource "Chapter <n>" (never the
exercise number); the number ("Exercise 4.3-2", "Problem 4-1") is the row's idx and the map's number column.
Multi-part problems stay one row with the parts labelled (a), (b), ... . The community solution is never stored as the
solution (it is uneven): it is kept in ref_solution (benchmarks_solutions.json); the answer key is None (the solver
writes it).

Conversions: ```cpp fences become verbatim blocks (pseudocode keeps its indentation); $$..$$ becomes \\[ .. \\];
the doubled backslashes of the Markdown source (\\\\ for a line break, \\{ \\}) become single ones; **bold** and
*italic* become \\textbf / \\textit; "**a.**" part labels become "(a)"; Markdown lists become itemize / enumerate;
links lose their URL; unicode math symbols become LaTeX commands; % & # _ are escaped outside math.

On --apply: backup, insert (topic/branch/subtopic Uncategorized), append to benchmarks_map.csv, keep ref_solution in
benchmarks_solutions.json. Nothing goes into benchmarks_assignments.json (subject rows).

Usage (repo root):
  python -m app.tools.import_clrs --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_clrs --data DIR --apply
DIR holds clrs/r.zip (https://github.com/walkccc/CLRS/archive/refs/heads/main.zip).
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
import zipfile
from pathlib import Path

from app.tools.import_answer_sets import duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "CLRS"
SOURCE = "Cormen, Leiserson, Rivest and Stein's Introduction to Algorithms"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/clrs_set_aside.json")
FIXES_PATH = Path(__file__).with_name("clrs_fixes.json")

_FIXES = json.loads(FIXES_PATH.read_text(encoding="utf-8")) if FIXES_PATH.exists() else {}
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES.get("fixes", []):
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
CLRS_DROPS: dict[str, str] = dict(_FIXES.get("dropped", {}))

# Statements that name a figure which carries the data: dropped unless listed here
FIGURE_RE = re.compile(r"\b[Ff]igures?\s+\$?\\?(?:text\{)?\d+\.\d+")
MODEL_RE = re.compile(r"^Using [Ff]igure \d+\.\d+ as a model, illustrate", re.M)
# Figure sentences cut from statements that stay self-contained without them
FIGURE_CUTS: dict[str, list[tuple[str, str]]] = {
    "Exercise 9.3-9": [(r", as shown in Figure \d+\.\d+", "")],
    "Exercise 22.4-2": [(r" For example, the directed acyclic graph of Figure 22\.8 contains .*?\. \(Your", " (Your")],
    "Exercise 33.3-4": [(r"As Figure 33\.10 illustrates, a", "A")],
    "Problem 17-4": [(r" \(\$\\textit\{Hint:\}\$ Look at Figures 13\.5, 13\.6, and 13\.7\.\)", "")],
    "Problem 15-3": [
        (r" Figure 15\.11\(a\) shows the solution to a \$7\$-point problem\.", ""),
        (r" Figure 15\.11\(b\) shows the shortest bitonic tour of the same \$7\$ points\. In this case, a", " A"),
    ],
    "Problem 19-2": [
        (r"As shown in Figure 19\.6\(a\), the", "The"),
        (r" Figure 19\.6\(b\) shows the binomial trees \$B_0\$ through \$B_4\$\.", ""),
        (r", as Figure 19\.6\\\(c\\\) shows,", ""),
    ],
    "Problem 22-2": [(r" Figure 22\.10 illustrates these definitions\.", "")],
    "Problem 8-7": [(r"\n\nFigure 8\.5 shows an example of the steps of columnsort.*?it happens to work\.\)", "")],
}

UNICODE_MATH = {
    "\u2264": r"\le ",
    "\u2265": r"\ge ",
    "\u221e": r"\infty ",
    "\u00d7": r"\times ",
    "\u2212": "-",
    "\u00d8": r"\emptyset ",
    "\u2208": r"\in ",
    "\u222a": r"\cup ",
    "\u03c0": r"\pi ",
    "\u2209": r"\notin ",
    "\u220f": r"\prod ",
    "\u223c": r"\sim ",
    "\u00b7": r"\cdot ",
    "\u2a01": r"\bigoplus ",
    "\u2297": r"\otimes ",
    "\u2032": "'",
    "\u03c1": r"\rho ",
    "\u2190": r"\leftarrow ",
    "\u2191": r"\uparrow ",
    "\u2196": r"\nwarrow ",
    "\u2715": r"\times ",
}
UNICODE_TEXT = {"\u2013": "--", "\u2014": "---", "\u2019": "'", "\ufb02": "fl", "\ufb01": "fi", "\u200b": "", "\u2061": ""}
UNICODE_CODE = {"\u2264": "<=", "\u2265": ">=", "\u2190": "<-", "\u2191": "^", "\u2196": "<-", "\u2212": "-", "\u2013": "-", "\u2019": "'", "\u2715": "x"}

PLACE_RE = re.compile("\x00(\\d+)\x00")
FENCE_RE = re.compile(r"(?m)^[ \t]*```([A-Za-z]*)[ \t]*\n(.*?)\n?[ \t]*```[ \t]*$", re.S)
DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_RE = re.compile(r"(?<!\\)\$((?:[^$\\\n]|\\.|\n(?!\s*\n))+?)\$")
CODE_RE = re.compile(r"`([^`\n]+)`")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\((?:https?://|\.\./|#|[^)\s]+\.md)[^)]*\)")
LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
LABEL_RE = re.compile(r"(?m)^\*\*([a-z])\.\*\*[ \t]*")


def math_text(m: str) -> str:
    """Inside $...$: Markdown-doubled backslashes to single, unicode symbols to commands."""
    m = re.sub(r"(?<!\\)\\\\(?=[{}])", r"\\", m)
    m = m.replace("\\\\\\\\", "\\\\")
    m = m.replace("\\*", "*").replace("\\_", "_").replace("\\(", "(").replace("\\)", ")")
    m = re.sub("|".join(map(re.escape, UNICODE_MATH)), lambda x: UNICODE_MATH[x.group(0)], m)
    return m


def code_text(c: str) -> str:
    c = re.sub("|".join(map(re.escape, UNICODE_CODE)), lambda x: UNICODE_CODE[x.group(0)], c)
    return c.replace("\t", "    ").rstrip()


def tt_escape(s: str) -> str:
    return re.sub(r"([\\{}$&#%_^~])", lambda m: {"\\": r"\textbackslash{}", "^": r"\^{}", "~": r"\~{}"}.get(m.group(1), "\\" + m.group(1)), s)


def text_plain(t: str) -> str:
    """Escape what LaTeX reads as markup in running text."""
    t = re.sub(r"\\([*_()\[\]#`<>|!.\-+])", lambda m: m.group(1), t)  # Markdown escapes
    t = t.replace("\\$", "\x03")
    t = re.sub(r"(?<!\\)\{", r"\\{", t)
    t = re.sub(r"(?<!\\)\}", r"\\}", t)
    t = re.sub(r"(?<!\\)([&%#])", r"\\\1", t)
    t = re.sub(r"(?<![\\\w])_|(?<=\w)_", r"\\_", t)
    t = t.replace("^", r"\^{}").replace("~", r"\~{}")
    for ch, rep in UNICODE_TEXT.items():
        t = t.replace(ch, rep)
    t = re.sub("|".join(map(re.escape, UNICODE_MATH)), lambda x: "$" + UNICODE_MATH[x.group(0)].strip() + "$", t)
    return t.replace("\x03", r"\$")


BS, LB, RB = "\x05", "\x06", "\x07"  # backslash, { and } of generated commands, until text_plain has run


def emphasis(t: str) -> str:
    """Bold and italic; the commands use the private characters above so text_plain leaves their braces alone."""

    def wrap(cmd: str):
        return lambda m: f"{BS}{cmd}{LB}{m.group(1)}{RB}"

    t = re.sub(r"\*\*\*(.+?)\*\*\*", lambda m: f"{BS}textbf{LB}{BS}textit{LB}{m.group(1)}{RB}{RB}", t)
    t = re.sub(r"\*\*(.+?)\*\*", wrap("textbf"), t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", wrap("textit"), t)
    t = re.sub(r"(?<![\w\\])_(?!\s)(.+?)(?<!\s)_(?!\w)", wrap("textit"), t)
    return t


def convert(raw: str, *, solution: bool = False) -> str:
    """Markdown + LaTeX (walkccc style) to the bank's LaTeX."""
    t = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    held: list[str] = []

    def hold(s: str) -> str:
        held.append(s)
        return f"\x00{len(held) - 1}\x00"

    def fence(m: re.Match) -> str:
        lang, body = m.group(1), m.group(2)
        if lang == "math":
            return hold("\\[\n" + math_text(body.strip()) + "\n\\]")
        lines = body.split("\n")
        ind = min((len(x) - len(x.lstrip()) for x in lines if x.strip()), default=0)
        body = "\n".join(code_text(x[ind:]) for x in lines)
        return "\n" + hold("\\begin{verbatim}\n" + body + "\n\\end{verbatim}") + "\n"

    t = FENCE_RE.sub(fence, t)
    t = IMAGE_RE.sub("[figure omitted]" if solution else "", t)
    t = DISPLAY_RE.sub(lambda m: hold("\\[\n" + math_text(m.group(1).strip()) + "\n\\]"), t)
    t = INLINE_RE.sub(lambda m: hold("$" + math_text(m.group(1)) + "$"), t)
    t = CODE_RE.sub(lambda m: hold("\\texttt{" + tt_escape(code_text(m.group(1))) + "}"), t)
    t = LINK_RE.sub(r"\1", t)
    t = LABEL_RE.sub(lambda m: f"({m.group(1)}) ", t)
    out: list[str] = []
    stack: list[tuple[int, str]] = []  # (indent, env)

    def close() -> None:
        out.extend([hold(f"\\end{{{stack.pop()[1]}}}"), ""])

    def open_(ind: int, env: str) -> None:
        stack.append((ind, env))
        out.append(hold(f"\\begin{{{env}}}"))

    for line in t.split("\n"):
        m = LIST_RE.match(line)
        if m:
            ind, mark = len(m.group(1).expandtabs(4)), m.group(2)
            env = "enumerate" if mark[0].isdigit() else "itemize"
            while stack and ind < stack[-1][0]:
                close()
            if not stack or ind > stack[-1][0]:
                open_(ind, env)
            elif stack[-1][1] != env:
                close()
                open_(ind, env)
            out.append(hold("\\item ") + m.group(3))
            continue
        if stack and line.strip() and not line.startswith((" ", "\t")) and out and out[-1] == "":
            while stack:  # a non-indented line after a blank line ends the list
                close()
        out.append(line.strip() if stack else line)
    while stack:
        close()
    t = "\n".join(out)
    t = text_plain(emphasis(t)).replace(BS, "\\").replace(LB, "{").replace(RB, "}")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = PLACE_RE.sub(lambda m: held[int(m.group(1))], t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def load(data: Path) -> list[dict]:
    """Parse the zip: every (id, kind, chapter, statement, solution) in the book's order."""
    out = []
    with zipfile.ZipFile(data / "clrs" / "r.zip") as z:
        names = sorted(n for n in z.namelist() if re.search(r"/docs/Chap\d\d/(?:Problems/)?[\d.-]+\.md$", n))

        def blocks(txt: str) -> tuple[str, str]:
            lines = txt.split("\n")
            i = 0
            while i < len(lines) and not lines[i].strip():
                i += 1
            st = []
            while i < len(lines) and lines[i].startswith(">"):
                st.append(re.sub(r"^> ?", "", lines[i]))
                i += 1
            return "\n".join(st).strip(), "\n".join(lines[i:]).strip()

        for n in names:
            m = re.search(r"/Chap(\d\d)/(Problems/)?([\d.-]+)\.md$", n)
            ch, prob = int(m.group(1)), bool(m.group(2))
            txt = z.read(n).decode("utf-8")
            if prob:
                st, sol = blocks(txt)
                out.append({"id": f"Problem {m.group(3)}", "kind": "problem", "chapter": ch, "statement": st, "solution": sol})
            else:
                parts = re.split(r"(?m)^## (\d+\.\d+-\d+).*$", txt)
                for k in range(1, len(parts), 2):
                    st, sol = blocks(parts[k + 1])
                    out.append({"id": f"Exercise {parts[k]}", "kind": "exercise", "chapter": ch, "statement": st, "solution": sol})
    return out


NOT_A_SOLUTION = re.compile(r"^\(?(Omit!?|Removed|Omitted)\)?[.!]?$", re.I)
NAMES_A_RESULT = re.compile(r"^(Prove|Show|Verify|Derive)\s+(Corollary|Theorem|Lemma|Equation|Property|Inequality)\b[\d. ]{0,12}\.$")


def build(data: Path) -> tuple[list[dict], dict[str, str]]:
    rows, dropped, seen = [], {}, {}
    for r in load(data):
        key = r["id"]
        st = r["statement"]
        if key in CLRS_DROPS:
            dropped[key] = CLRS_DROPS[key]
            continue
        if not st:
            dropped[key] = "no statement in the source"
            continue
        if NAMES_A_RESULT.match(st):
            dropped[key] = "only names a result of the book"
            continue
        if MODEL_RE.search(st):
            st = re.sub(r"Using [Ff]igure \d+\.\d+ as a model, illustrate", "Illustrate", st)
        for pat, rep in FIGURE_CUTS.get(key, []):
            new = re.sub(pat, rep, st, count=1, flags=re.S)
            if new == st:
                raise SystemExit(f"FIGURE CUT {key}: {pat!r} not found")
            st = new
        if FIGURE_RE.search(st):
            dropped[key] = "depends on a figure the Markdown does not carry"
            continue
        text = convert(st)
        for old, new in HAND_FIXES.get((key, "latexcode"), []):
            if text.count(old) != 1:
                raise SystemExit(f"HAND FIX {key}: expected one {old!r}")
            text = text.replace(old, new)
        sol = r["solution"].strip()
        ref = "" if NOT_A_SOLUTION.match(sol) else convert(sol, solution=True)
        if text in seen:
            dropped[key] = f"same statement as {seen[text]}"
            continue
        seen[text] = key
        num = key.split(" ", 1)[1]
        rows.append(
            {
                "potd": f"{SET} {key}",
                "set": SET,
                "idx": key,
                "orig": "",
                "source": SOURCE,
                "subsource": f"Chapter {r['chapter']}",
                "latexcode": text,
                "answer": None,
                "solution": None,
                "hints": None,
                "more_hints": None,
                "ref_solution": ref,
                "group": "subject",
                "effort": None,
                "image": None,
                "number": num,
            }
        )
    return rows, dropped


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped = build(a.data)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    reasons = collections.Counter(re.sub(r"\d+", "N", v) for v in dropped.values())
    print(
        json.dumps(
            {
                "rows_kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
                "by_chapter": sorted(collections.Counter(r["subsource"] for r in new).items()),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        (a.dump.with_name(a.dump.stem + "_dropped.json")).write_text(json.dumps(dropped, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("clrs")
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in new:
            h = latex_hash(r["latexcode"])
            if h in existing:
                continue
            cur = conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, hints, more_hints, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    UNCATEGORIZED,
                    UNCATEGORIZED,
                    UNCATEGORIZED,
                    r["latexcode"],
                    r["source"],
                    r["subsource"],
                    r["answer"],
                    r["solution"],
                    r["hints"],
                    r["more_hints"],
                    h,
                ),
            )
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
    solutions.update(
        {str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]} for q, r in added if r["ref_solution"]}
    )
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
