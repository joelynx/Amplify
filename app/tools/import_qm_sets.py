"""
Import quantum-mechanics and modern-physics question sets
---------------------------------------------------------
Four sets for the bank subject "Quantum Mechanics" (QM, atomic, nuclear, particle; condensed matter and the
other physics sections come along and the classifier sorts them afterwards). Every row goes to group "subject".

  physics   desimfj/PHYSICS (MIT): data/test.jsonl, the language=en rows (1,000; Mechanics, Electromagnetism,
            Thermodynamics, Optics and Modern Physics, 200 each; translated Chinese textbook and qualifying-exam
            problems) with reference solution and typed answers. Source "PHYSICS", subsource "<section>".
  zee       0xZee/dataset-CoT-Quantum-Mechanics-1224, ...-Atomic-Nuclear-Physics-144 and
            ...-Relativity-Astrophysics-Nuclear-Physics-313 (parquet; textbook problems with the textbook solution in
            `response`; the CoT column is not read; no licence stated, personal use; Amplify is private). The answer
            key is None (proofs and derivations; the solver writes it); the textbook solution is stored as the
            solution when it stands alone.
  cmphys    weidawang/CMPhysBench (Apache-2.0), CMPhysBench.json: 520 condensed-matter problems (textbook-grade
            solution + final answer). Source "CMPhysBench", subsource "<topic>".
  nuclearqa pnnl/EXPERT2 benchmark/NuclearQA_v1 (BSD-2-Clause): 101 short expert-written nuclear questions with a
            short reference answer. Source "NuclearQA", subsource "<difficulty> questions".

Dropped: statements that depend on a figure, table, numbered equation or other problem the row does not carry
(DANGLING below), incomplete statements, multiple-choice rows whose options cannot be cut apart, rows without a
usable answer (physics, cmphys), near-duplicates of an earlier row of these sets; per-row repairs and drops in
qm_sets_fixes.json. Rows the bank already has (same latex_hash or 85% of 5-word shingles) are skipped and listed.

Conversions: 0xZee text has literal backslash-n instead of line ends and \\( \\) delimiters (turned into real
line ends and $...$); $$..$$ becomes \\[ .. \\]; unicode symbols become commands; multiple choice becomes
"(A) ..." lines with "Exactly one option is correct."; answer keys from the boxed answers, several parts as
"(1) ..; (2) ..", numbers plain, the rest in $...$ (PHYSICS and CMPhysBench keys carry no units of their own).
The dataset solution is stored in `solution` when it is at least 150 characters and does not lean on anything the
row does not carry (DANGLING); it is always kept in ref_solution (benchmarks_solutions.json).

On --apply: backup, insert (topic/branch/subtopic Uncategorized), append to benchmarks_map.csv, keep ref_solution in
benchmarks_solutions.json. Nothing goes into benchmarks_assignments.json (subject rows).

Usage (repo root):
  python -m app.tools.import_qm_sets --data DIR --dry-run [--only physics,zee] [--dump rows.json] [--set-aside]
  python -m app.tools.import_qm_sets --data DIR --apply
DIR holds physics/t.jsonl, zee/<name>.parquet (3 files), cmp/c.json, nqa/NuclearQA_v1_{questions,answers}.txt and
NuclearQA_v1_meta.csv.
"""

from __future__ import annotations

import argparse
import ast
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash
from app.tools.import_ugphysics import boxed, markup_fixes, mc_statement, piece, symbols
from app.tools.import_ugphysics import tidy as _tidy

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/qm_sets_set_aside.json")
FIXES_PATH = Path(__file__).with_name("qm_sets_fixes.json")
MIN_SOLUTION = 150
SETS = ("physics", "zee", "cmphys", "nuclearqa")

_FIXES = json.loads(FIXES_PATH.read_text(encoding="utf-8")) if FIXES_PATH.exists() else {}
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES.get("fixes", []):
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPS: dict[str, str] = dict(_FIXES.get("dropped", {}))
SOLUTION_DROPS: dict[str, str] = dict(_FIXES.get("solution_dropped", {}))

# Things a statement or solution leans on that the row does not carry
DANGLING = re.compile(
    r"\bFig(?:ure|s?\.)\s*[\w(]|\b[Tt]able\s+\d|\b(?:Eq(?:uation)?s?\.?|[Ff]ormula)\s*\(?\d|\bProblems?\s+\d|\bProb\.\s*\d"
    r"|\b(?:Chapter|Section|Sec\.|Volume|Vol\.|Part)\s+\d|\[\d+\]|\b(?:see|in|from|by|using|of|via)\s+\(\d+(?:\.\d+)+\)"
    r"|\b(?:shown|given|drawn|sketched)\s+(?:in|below|above)\s+the\s+(?:figure|diagram|graph|picture)"
    r"|\bthe\s+(?:figure|diagram|graph)\s+(?:below|above)\b|\bin\s+the\s+(?:figure|diagram)\b"
    r"|\(\s*\d+\.\d+\.\d+\s*\)|\(\d{1,2}\.\d{1,3}\)",
    re.I,
)
BOXED_MARK = "\\boxed"
HALFWIDTH = {"．": ".", "；": ";", "，": ",", "：": ":", "（": "(", "）": ")", "？": "?"}


BARE_RE = re.compile(r"(?<![^\s$])([^\s$\\]*[\^_][^\s$\\]*)")


def bare_math(t: str) -> str:
    """Words with a bare ^ or _ outside math ("p^2/m", "S_w") go into $...$."""
    out, pos = [], 0
    for m in list(MATH_REGION.finditer(t)) + [None]:
        end = m.start() if m else len(t)
        out.append(BARE_RE.sub(lambda g: "$" + g.group(1).rstrip(".,;:?!") + "$" + g.group(1)[len(g.group(1).rstrip(".,;:?!")) :], t[pos:end]))
        if m:
            out.append(m.group(0))
            pos = m.end()
    return "".join(out)


def tidy(t: str) -> str:
    return bare_math(_tidy("".join(HALFWIDTH.get(c, c) for c in t)))

BRACKETS = re.compile("\u3010([^\u3011]*)\u3011")
KEEP_N = r"(?:abla|eq|u|e|ot|otin|onumber|olimits|mid|cong)(?![A-Za-z])"
ESC_RE = re.compile(r"\\\\|\\n(?!" + KEEP_N + r")|\\\(|\\\)")
FOOTNOTE_RE = re.compile(r"\\footnotetext\{.*?\n\}", re.S)
# Option markers "A. text" (line start or after a space)
DOT_MARK = re.compile(r"(?:^|(?<=\s))([A-H])[.\uff0e]\s+(?=\S)", re.M)


MATH_REGION = re.compile(r"\\\[.*?\\\]|\$[^$]*\$|\\begin\{(\w+\*?)\}.*?\\end\{\1\}", re.S)
NAME = r"[A-Z][A-Za-z.&'\- ]*"
ATTRIBUTION = re.compile(
    r"\s*(?:\*+|\\textbf\{|\\textit\{)?\[?\(\s*" + NAME + r"(?:\s*(?:,|;|and)\s*" + NAME + r")*\s*\)\]?(?:\*+|\})?\s*$"
)


def markdown(t: str) -> str:
    """*italic* and **bold** outside math to LaTeX."""
    parts, pos = [], 0
    for m in MATH_REGION.finditer(t):
        parts += [(False, t[pos : m.start()]), (True, m.group(0))]
        pos = m.end()
    parts.append((False, t[pos:]))
    out = []
    for is_math, p in parts:
        if not is_math:
            p = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", p)
            p = re.sub(r"(?<![\w*\\])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"\\textit{\1}", p)
        out.append(p)
    return "".join(out)


def delims(t: str) -> str:
    """\\( \\) to $ $ (a line break before a parenthesis stays)."""
    return re.sub(r"\\\\|\\\(|\\\)", lambda m: {"\\(": "$", "\\)": "$"}.get(m.group(0), m.group(0)), t)


def zee_text(t: str, question: bool = False) -> str:
    """0xZee: literal backslash-n to line ends, \\( \\) to $...$, Markdown emphasis, no exam attribution."""

    def sub(m: re.Match) -> str:
        s = m.group(0)
        return {"\\\\": s, "\\(": "$", "\\)": "$"}.get(s, "\n")

    t = ESC_RE.sub(sub, t).strip()
    if question:
        t = ATTRIBUTION.sub("", t)
    return markdown(t)


def dot_to_paren(stem: str) -> str | None:
    """'A. x B. y' options to '(A) x (B) y' (the last A, B, C... run of at least 3)."""
    marks = [(m.start(), m.end(), m.group(1)) for m in DOT_MARK.finditer(stem)]
    for i in range(len(marks) - 1, -1, -1):
        if marks[i][2] != "A":
            continue
        run, want = [marks[i]], "B"
        for m in marks[i + 1 :]:
            if m[2] == want:
                run.append(m)
                want = chr(ord(want) + 1)
        if len(run) >= 3:
            out, pos = [], 0
            for m in run:
                out += [stem[pos : m[0]], f"({m[2]}) "]
                pos = m[1]
            return "".join(out) + stem[pos:]
    return None


def mcq(stem: str, letters: list[str]) -> str | None:
    got = mc_statement(stem, letters)
    if got is None:
        alt = dot_to_paren(stem)
        got = mc_statement(alt, letters) if alt else None
    return got


def rowdict(set_: str, idx: str, source: str, subsource: str, text: str, answer, solution, ref: str) -> dict:
    return {
        "potd": f"{set_} {idx}",
        "set": set_,
        "idx": idx,
        "orig": "",
        "source": source,
        "subsource": subsource,
        "latexcode": text,
        "answer": answer,
        "solution": solution,
        "hints": None,
        "more_hints": None,
        "ref_solution": ref,
        "group": "subject",
        "effort": None,
        "image": None,
    }


def solution_pair(raw: str, key: str) -> tuple[str, str | None]:
    """(reference solution, solution to store or None)."""
    ref = tidy(raw)
    ref = BRACKETS.sub(lambda m: "\\textbf{" + m.group(1).strip() + ".} ", ref)
    store = ref if len(ref) >= MIN_SOLUTION and not DANGLING.search(ref) and "\\textbf{Intent" not in ref else None
    if key in SOLUTION_DROPS:
        store = None
    return ref, store


def finish(row: dict, dropped: dict, seen: dict) -> dict | None:
    key = row["potd"]
    for fld in ("latexcode", "answer", "solution", "ref_solution"):
        for old, new in HAND_FIXES.get((key, fld), []):
            if row[fld] is None or row[fld].count(old) != 1:
                raise SystemExit(f"HAND FIX {key} {fld}: expected one {old!r}")
            row[fld] = row[fld].replace(old, new)
            if fld == "solution" and row["ref_solution"] and old in row["ref_solution"]:
                row["ref_solution"] = row["ref_solution"].replace(old, new)
    if row["latexcode"] in seen:
        dropped[key] = f"same statement as {seen[row['latexcode']]}"
        return None
    seen[row["latexcode"]] = key
    return row


# ---- PHYSICS ---------------------------------------------------------------------------------


def strip_box(s: str) -> str:
    s = str(s).strip()
    b = boxed(s) if BOXED_MARK in s else None
    s = (b if b is not None else s).strip()
    if s.count("$") % 2:  # a stray $ in the source
        s = s.replace("$", "")
    return s[1:-1].strip() if s.startswith("$") and s.endswith("$") and s.count("$") == 2 else s


def physics_answer(r: dict, stem: str) -> tuple[str | None, list[str] | None]:
    """(key, letters for a multiple-choice row)."""
    kinds = list(r["answer_type"]) if isinstance(r["answer_type"], list) else []
    parts = []
    for i, alts in enumerate(r["answer"]):
        items = [strip_box(a) for a in alts if str(a).strip()]
        if not items:
            return None, None
        kind = kinds[i] if len(kinds) == len(r["answer"]) else ""
        if kind == "MCQ":
            c = re.sub(r"[\s,;&]|and", "", items[0])
            if not re.fullmatch(r"[A-H]+", c):
                return None, None
            letters = sorted(set(c))
            return ", ".join(letters), letters
        parts.append(", ".join(piece(x, "", "", stem) for x in items))
    if not parts:
        return None, None
    return (parts[0] if len(parts) == 1 else "; ".join(f"({i}) {p}" for i, p in enumerate(parts, 1))), None


def load_physics(data: Path, dropped: dict, found: dict) -> list[dict]:
    rows, seen = [], {}
    lines = (data / "physics" / "t.jsonl").read_text(encoding="utf-8").splitlines()
    en = [r for r in (json.loads(x) for x in lines if x.strip()) if r.get("language") == "en"]
    found["physics"] = len(en)
    for r in en:
        key = f"PHYSICS {r['id']}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        stem = tidy(r["question"])
        if len(stem) < 25 or DANGLING.search(stem):
            dropped[key] = "needs a figure, table, numbered equation or other problem that is not given"
            continue
        ans, letters = physics_answer(r, stem)
        if ans is None:
            dropped[key] = "no usable answer"
            continue
        if letters:
            stem = mcq(stem, letters)
            if stem is None:
                dropped[key] = "multiple-choice options cannot be cut apart"
                continue
        ref, sol = solution_pair(r["solution"] or "", key)
        ans = markup_fixes(symbols(ans))
        row = rowdict("PHYSICS", str(r["id"]), "PHYSICS", r["domain"], stem, ans, sol, ref)
        got = finish(row, dropped, seen)
        if got:
            rows.append(got)
    return rows


# ---- 0xZee -----------------------------------------------------------------------------------

ZEE_FILES = [
    ("Quantum-Mechanics-1224", "0xZee QM", "Quantum mechanics"),
    ("Atomic-Nuclear-Physics-144", "0xZee Atomic", "Atomic and nuclear physics"),
    ("Relativity-Astrophysics-Nuclear-Physics-313", "0xZee RelNuc", "Relativity, astrophysics and nuclear physics"),
]
ZEE_SOURCE = "Textbook problems and solutions in quantum, atomic and nuclear physics (0xZee)"


def load_zee(data: Path, dropped: dict, found: dict) -> list[dict]:
    import pyarrow.parquet as pq

    rows, seen = [], {}
    for fname, set_, sub in ZEE_FILES:
        recs = pq.read_table(data / "zee" / f"{fname}.parquet").to_pylist()
        found[set_] = len(recs)
        for n, r in enumerate(recs):
            idx = f"{n + 1}"
            key = f"{set_} {idx}"
            if key in DROPS:
                dropped[key] = DROPS[key]
                continue
            q = tidy(zee_text(r["question"] or "", question=True))
            if len(q) < 30 or not re.search(r"(?:[.?)$\]:]|\\end\{\w+\*?\})$", q):
                dropped[key] = "incomplete statement"
                continue
            if DANGLING.search(q):
                dropped[key] = "needs a figure, table, numbered equation or other problem that is not given"
                continue
            if not (r["response"] or "").strip():
                dropped[key] = "no solution"
                continue
            ref, sol = solution_pair(zee_text(r["response"]), key)
            row = rowdict(set_, idx, ZEE_SOURCE, sub, q, None, sol, ref)
            got = finish(row, dropped, seen)
            if got:
                rows.append(got)
    return rows


# ---- CMPhysBench -----------------------------------------------------------------------------


def cmp_answer(r: dict, stem: str) -> str | None:
    fa = r["final_answer"]
    try:
        items = ast.literal_eval(fa) if isinstance(fa, str) else list(fa)
    except (ValueError, SyntaxError):
        items = [fa]
    if isinstance(items, str):
        items = [items]
    items = [strip_box(x) for x in items if str(x).strip()]
    if not items:
        return None
    pieces = [piece(x, "", "", stem) for x in items]
    return pieces[0] if len(pieces) == 1 else "; ".join(f"({i}) {p}" for i, p in enumerate(pieces, 1))


def load_cmphys(data: Path, dropped: dict, found: dict) -> list[dict]:
    rows, seen = [], {}
    recs = json.loads((data / "cmp" / "c.json").read_text(encoding="utf-8"))
    found["cmphys"] = len(recs)
    for r in recs:
        key = f"CMPhysBench {r['id']}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        stem = tidy(delims(r["question"]))
        if len(stem) < 25 or DANGLING.search(stem):
            dropped[key] = "needs a figure, table, numbered equation or other problem that is not given"
            continue
        ans = cmp_answer(r, stem)
        raw = FOOTNOTE_RE.sub("", delims(r["answer"] or "")).strip()
        ref, sol = solution_pair(raw, key) if raw else ("", None)
        ans = markup_fixes(symbols(ans)) if ans else None  # the public file withholds the key of 420 rows
        row = rowdict("CMPhysBench", str(r["id"]), "CMPhysBench", r["topic"], stem, ans, sol, ref)
        got = finish(row, dropped, seen)
        if got:
            rows.append(got)
    return rows


# ---- NuclearQA -------------------------------------------------------------------------------


def plain(t: str) -> str:
    t = t.strip()
    t = re.sub(r"([&%#_{}$])", r"\\\1", t)
    t = t.replace("~", r"\~{}").replace("^", r"\^{}")
    return symbols(t)


def load_nuclearqa(data: Path, dropped: dict, found: dict) -> list[dict]:
    d = data / "nqa"
    qs = (d / "NuclearQA_v1_questions.txt").read_text(encoding="utf-8-sig").splitlines()
    ans = (d / "NuclearQA_v1_answers.txt").read_text(encoding="utf-8-sig").splitlines()
    meta = list(csv.DictReader((d / "NuclearQA_v1_meta.csv").read_text(encoding="utf-8-sig").splitlines()))
    qs, ans = [x for x in qs if x.strip()], [x for x in ans if x.strip()]
    if not (len(qs) == len(ans) == len(meta)):
        raise SystemExit(f"NuclearQA files disagree: {len(qs)} questions, {len(ans)} answers, {len(meta)} meta rows")
    found["nuclearqa"] = len(qs)
    rows, seen = [], {}
    for q, a, m in zip(qs, ans, meta, strict=True):
        key = f"NuclearQA {m['QID']}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        row = rowdict("NuclearQA", m["QID"], "NuclearQA", f"{m['Difficulty']} questions", plain(q), plain(a), None, "")
        got = finish(row, dropped, seen)
        if got:
            rows.append(got)
    return rows


LOADERS = {"physics": load_physics, "zee": load_zee, "cmphys": load_cmphys, "nuclearqa": load_nuclearqa}


def build(data: Path, only: list[str]) -> tuple[list[dict], dict[str, str], dict[str, int]]:
    rows, dropped, found = [], {}, {}
    for s in only:
        rows += LOADERS[s](data, dropped, found)
    # near-duplicates across and within the sets: the first row stays
    sh = [shingles(r["latexcode"]) for r in rows]
    gone: set[int] = set()
    for j in range(len(rows)):
        for i in range(j):
            if i in gone or not sh[i] or not sh[j]:
                continue
            if len(sh[i] & sh[j]) / min(len(sh[i]), len(sh[j])) >= 0.85:
                dropped[rows[j]["potd"]] = f"near-duplicate of {rows[i]['potd']}"
                gone.add(j)
                break
    return [r for k, r in enumerate(rows) if k not in gone], dropped, found


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", default=",".join(SETS), help="comma-separated subset of " + ",".join(SETS))
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--check", type=Path, help="check_batch.py output: failing rows are set aside (with --set-aside), a failing stored solution is dropped")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    only = [s for s in a.only.split(",") if s]
    rows, dropped, found = build(a.data, only)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
    solution_dropped = 0
    if a.check:  # render checks (check_batch.py): a failing statement or key sets the row aside, a failing solution is not stored
        res = json.loads(a.check.read_text(encoding="utf-8"))
        for r in new:
            v = res.get(r["potd"])
            if not v or v["ok"]:
                continue
            bad = {f for f in ("latexcode", "answer", "solution") if f in v["tex"] or f in v["web"]}
            bad |= {m.split(":")[0].split()[-1] for m in v["text"]}
            if bad <= {"solution"}:
                r["solution"] = None
                solution_dropped += 1
            else:
                excluded[r["potd"]] = "render check: " + ", ".join(sorted(bad))
    problems = check(new)
    for x in problems[:40]:
        print("CHECK", x)
    if a.set_aside:
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    reasons = collections.Counter(re.sub(r"\d+", "N", v) for v in dropped.values())
    print(
        json.dumps(
            {
                "found": found,
                "kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "in_bank_by_set": collections.Counter(rows[k]["set"] for k in dup),
                "to_add": len(new),
                "to_add_by_set": collections.Counter(r["set"] for r in new),
                "check_problems": len(problems),
                "solutions_dropped_by_render_check": solution_dropped,
                "with_solution": sum(bool(r["solution"]) for r in new),
                "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        a.dump.with_name(a.dump.stem + "_dropped.json").write_text(json.dumps(dropped, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("qm_sets")
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
