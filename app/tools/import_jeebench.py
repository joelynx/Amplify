"""Import the maths and physics questions of JEEBench (huggingface.co/datasets/daman1209arora/jeebench, MIT):
the IIT JEE Advanced papers of 2016-2023 with the problems that need a figure left out, each with a gold
answer and no solution. Chemistry is skipped (the bank has no chemistry subject).

Filed under the original exam ("Joint Entrance Examination Advanced"), subsource "<year>, Paper <p>, Question
<n>" (the question number in the paper), original source "JEEBench". Maths rows go to the maths solver (the
assignments file, as for the answer sets), physics rows wait for the subjects solver.

Conversions: option labels "[A]" and "$[\\mathrm{A}]$" become "(A)", options on their own lines; a single-answer
MCQ gets "Exactly one option is correct." and a multi-answer one "One or more options may be correct." when the
text does not say so; keys "ABD" become "A, B, D"; a Numeric question without it gets "Give the answer correct
to two decimal places."; tabular tables become an array in a display (KaTeX has no tabular). Per-row text fixes
and drops are in jeebench_fixes.json.

Usage (repo root):
  python -m app.tools.import_jeebench --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_jeebench --data DIR --apply
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import OPUS, duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "JEEBench"
SOURCE = "Joint Entrance Examination Advanced"
ORIG = "JEEBench"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
ASSIGNMENTS = Path("pipeline/benchmarks_assignments.json")
SET_ASIDE_PATH = Path("app/data/appdata/benchmarks_set_aside.json")
GROUPS = {"math": "math", "phy": "subject"}  # chemistry has no bank subject
ONE = "Exactly one option is correct."
MANY = "One or more options may be correct."
ONE_RE = re.compile(r"exactly one|only one|one correct|single correct", re.I)
MANY_RE = re.compile(r"one or more|more than one|multiple (?:options|correct)", re.I)
DECIMAL = "Give the answer correct to two decimal places."
DECIMAL_RE = re.compile(r"decimal", re.I)
OPTION_RE = re.compile(
    r"^(\$)?[ \t]*[\(\[](?:\\mathrm\{)?([A-D])\}?[\)\]]\$?[ \t]*((?:\\quad[ \t]*)*)", re.M)

_FIXES = json.loads(Path(__file__).with_name("jeebench_fixes.json").read_text(encoding="utf-8")) \
    if Path(__file__).with_name("jeebench_fixes.json").exists() else {"fixes": [], "dropped": {}}
FIXES = {(e["key"], e["field"]): [tuple(p) for p in e["fixes"]] for e in _FIXES["fixes"]}
DROPPED = _FIXES["dropped"]


def split_top(s: str, sep: str) -> list[str]:
    """Split on a separator outside braces and nested environments."""
    out, depth, env, last, k = [], 0, 0, 0, 0
    while k < len(s):
        if s.startswith("\\begin{", k):
            env += 1
        elif s.startswith("\\end{", k):
            env -= 1
        elif s[k] == "\\" and not s.startswith(sep, k):
            k += 2
            continue
        elif s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
        if not depth and not env and s.startswith(sep, k):
            out.append(s[last:k])
            k += len(sep)
            last = k
            continue
        k += 1
    out.append(s[last:])
    return out


def table_cell(c: str) -> str:
    """A tabular cell is text with $...$ math; in an array it is math: the text goes in \\text{}."""
    parts = re.split(r"(\$[^$]*\$)", c.strip())
    out = []
    for p in parts:
        if p.startswith("$") and p.endswith("$") and len(p) > 1:
            out.append(p[1:-1].strip())
        elif re.fullmatch(r"[\d.\s-]+", p):
            out.append(p.strip())
        elif p.strip():
            out.append("\\text{" + p.strip() + "}")
    return " ".join(out)


def tabular(m: re.Match) -> str:
    spec, body = m.group(1), m.group(2)
    rows = []
    for r in split_top(body.strip(), "\\\\"):
        hl = ""
        r = r.strip()
        while r.startswith("\\hline"):
            hl += "\\hline "
            r = r[6:].strip()
        if r:
            rows.append(hl + " & ".join(table_cell(c) for c in split_top(r, "&")))
        else:
            rows.append(hl.strip())
    tail = ""
    if rows and rows[-1].strip() == "\\hline":
        tail = " \\\\\n\\hline"
        rows.pop()
    return "\\[\n\\begin{array}{" + spec + "}\n" + " \\\\\n".join(rows) + tail + "\n\\end{array}\n\\]"


def tidy(t: str) -> str:
    t = t.replace("\r\n", "\n").strip()
    t = re.sub(r"\\begin\{center\}\s*(\\begin\{tabular\}\{([^}]*)\}(.*?)\\end\{tabular\})\s*\\end\{center\}",
               lambda m: tabular(re.match(r"\\begin\{tabular\}\{([^}]*)\}(.*?)\\end\{tabular\}", m.group(1), re.S)),
               t, flags=re.S)
    t = re.sub(r"\\begin\{center\}\s*(.*?)\s*\\end\{center\}", r"\1", t, flags=re.S)
    t = re.sub(r"\$\$(.*?)\$\$", lambda m: "\\[" + m.group(1) + "\\]", t, flags=re.S)
    # a blank line inside a display ends the paragraph: TeX fails; "&" without an environment has no column
    t = re.sub(r"\\\[(.*?)\\\]", lambda m: "\\[" + display_body(m.group(1)) + "\\]", t, flags=re.S)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


def display_body(b: str) -> str:
    b = re.sub(r"\n\s*\n", "\n", b)
    if "&" in b and "\\begin{" not in b:
        b = b.replace("& ", "").replace("&", "")
    return b


def mcq(text: str, kind: str) -> str:
    text = tidy(text)
    marks = list(OPTION_RE.finditer(text))
    labels = [m.group(2) for m in marks]
    if labels != ["A", "B", "C", "D"]:
        raise ValueError(f"option labels {labels}")
    stem = text[:marks[0].start()].strip()
    opts = []
    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(text)
        body = text[m.end():end].strip()
        if m.group(1):  # "$[\mathrm{A}] \quad v=..$": the label sat inside the math
            body = "$" + body
        elif body.count("$") % 2 and body.endswith("$"):  # "(C) e^{x}-..$": the opening $ was lost
            body = "$" + body
        elif "$" not in body and body.startswith("\\left"):  # a matrix given without its $ $
            body = f"${body}$"
        opts.append(f"({m.group(2)}) {body}")
    note = ONE if kind == "MCQ" else MANY
    if not (ONE_RE if kind == "MCQ" else MANY_RE).search(stem):
        stem += "\n\n" + note
    return stem + "\n\n" + "\n\n".join(opts)


def load(data: Path) -> list[dict]:
    raw = json.loads((data / "test.json").read_text(encoding="utf-8"))
    rows = []
    for x in raw:
        if x["subject"] not in GROUPS:
            continue
        year, paper = re.fullmatch(r"JEE Adv (\d{4}) Paper (\d)", x["description"]).groups()
        label = f"{year}-P{paper}-{x['index']}"
        kind, gold = x["type"], x["gold"].strip()
        if kind.startswith("MCQ"):
            text = mcq(x["question"], kind)
            assert re.fullmatch("[A-D]{1,4}", gold) and (kind == "MCQ(multiple)" or len(gold) == 1), gold
            answer = ", ".join(gold)
        else:
            text = tidy(x["question"])
            if kind == "Numeric" and not DECIMAL_RE.search(text):
                text += "\n\n" + DECIMAL
            answer = gold
        r = {"potd": f"{SET} {label}", "set": SET, "idx": label, "orig": ORIG, "source": SOURCE,
             "subsource": f"{year}, Paper {paper}, Question {x['index']}", "latexcode": text, "answer": answer,
             "solution": None, "hints": None, "more_hints": None, "ref_solution": "",
             "group": GROUPS[x["subject"]], "effort": "high" if x["subject"] == "math" else None, "image": None}
        for fld in ("latexcode", "answer"):
            for old, new in FIXES.get((r["potd"], fld), []):
                if r[fld].count(old) != 1:
                    raise SystemExit(f"FIX {r['potd']} {fld}: expected one {old!r}")
                r[fld] = r[fld].replace(old, new)
        rows.append(r)
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True, help="folder with test.json")
    p.add_argument("--model", default=OPUS)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows = load(a.data)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    for k, why in DROPPED.items():
        print(f"dropped: {k}: {why}")
    new = [r for k, r in enumerate(rows) if k not in dup and r["potd"] not in DROPPED]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why],
                                             ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    print(json.dumps({"rows": len(rows), "in_bank": len(dup), "dropped": len(DROPPED), "to_add": len(new),
                      "check_problems": len(problems), "by_group": collections.Counter(r["group"] for r in new)},
                     default=dict))
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("jeebench")
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
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"], r["answer"],
                 r["solution"], r["hints"], r["more_hints"], h),
            )
            existing.add(h)
            added.append((cur.lastrowid, r))
        conn.commit()
    finally:
        conn.close()
    with MAP_PATH.open("a" if MAP_PATH.exists() else "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    doc = json.loads(ASSIGNMENTS.read_text(encoding="utf-8")) if ASSIGNMENTS.exists() else {
        "note": "Benchmark sets imported by app/tools/import_<name>.py (answer key, no solutions), with the model "
                "and effort that solve the maths ones. Listing a question here puts it in run_sub.py's scope.",
        "questions": {}}
    doc["questions"].update({str(q): {"model": a.model, "effort": r["effort"]} for q, r in added if r["group"] == "math"})
    ASSIGNMENTS.write_text(json.dumps(doc, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; "
          f"map={MAP_PATH}; assignments={ASSIGNMENTS} ({len(doc['questions'])} questions)")


if __name__ == "__main__":
    main()
