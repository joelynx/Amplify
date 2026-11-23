"""Import the TheoremQA rows import_theoremqa left out for want of a bank subject (owner 2026-11-23: the bank
now has Circuits and Electronics, Signals, Systems and Control, Electromagnetism with Optics, Material Science,
and numerical analysis fits the maths subjects).

Takes the rows of subfield Signal processing, Information theory, Numerical analysis, Optics and Condensed
matter physics, with import_theoremqa's conversions (to_latex, keys, pipe tables, pictures). Computer networking
and Machine learning still have no subject and stay out; so do the rows import_theoremqa already knows (its
ALREADY_IN_BANK, FIGURE_MISSING and DROPPED) and the rows listed in theoremqa_leftovers_fixes.json "dropped".
Every row is group "subject": the classifier picks the subject afterwards, and the maths ones get queued then.
Per-row repairs live in theoremqa_leftovers_fixes.json (same layout as theoremqa_fixes.json).

Usage (repo root):
  python -m app.tools.import_theoremqa_leftovers --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_theoremqa_leftovers --data DIR --apply
DIR is the folder import_theoremqa takes (it, or DIR/theoremqa, holds theoremqa_test.json and the parquet).
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from app.tools import import_theoremqa as tq
from app.tools.import_answer_sets import GRAPHIC, TEXIMAGES, duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "TheoremQA"
MAP_PATH = tq.MAP_PATH
SOLUTIONS_PATH = tq.SOLUTIONS_PATH
SET_ASIDE_PATH = Path("app/data/appdata/theoremqa_leftovers_set_aside.json")  # git-ignored
TAKEN = {"Signal processing", "Information theory", "Numerical analysis", "Optics", "Condensed matter physics"}

_FIX = json.loads(Path(__file__).with_name("theoremqa_leftovers_fixes.json").read_text(encoding="utf-8"))
FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIX["fixes"]:
    FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPPED = dict(_FIX["dropped"])


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    """(rows to import, {id: why left out})."""
    import pyarrow.parquet as pq
    if not (data / "theoremqa_test.json").exists():
        data = data / "theoremqa"
    meta = json.loads((data / "theoremqa_test.json").read_text(encoding="utf-8"))
    pics = pq.read_table(data / "test-00000-of-00001.parquet").to_pylist()
    rows, left = [], {}
    for r, p in zip(meta, pics, strict=True):
        if r["Question"] != p["Question"]:
            raise SystemExit(f"{r['id']}: the parquet and the JSON are not in the same order")
        key = r["id"][:-5] if r["id"].endswith(".json") else r["id"]
        if r["subfield"] not in TAKEN:
            continue
        if key in tq.ALREADY_IN_BANK:
            left[key] = f"the bank has it ({tq.ALREADY_IN_BANK[key]})"
            continue
        if key in tq.FIGURE_MISSING:
            left[key] = tq.FIGURE_MISSING[key]
            continue
        if key in tq.DROPPED:
            left[key] = tq.DROPPED[key]
            continue
        if key in DROPPED:
            left[key] = DROPPED[key]
            continue
        q = tq.clean_raw(r["Question"])
        q = re.sub(r"\$\$\s*(.*?)\s*\$\$", r"$\1$", q, flags=re.S)  # a $$ ... $$ display becomes inline math
        for old, new in FIXES.get((key, "latexcode"), []):
            if q.count(old) != 1:
                raise SystemExit(f"FIX {key} latexcode: expected one {old!r}")
            q = q.replace(old, new)
        r = dict(r, Question=q)
        tex = (tq._with_tables(q, key) if sum(" | " in ln for ln in q.splitlines()) >= 2 else tq.to_latex(q, key))
        image = None
        if p["Picture"] and p["Picture"].get("bytes"):
            png = tq.to_png(p["Picture"]["bytes"])
            if png is None:
                left[key] = "its picture is a GIF/JPEG and Pillow is not installed to convert it to PNG"
                continue
            name = "tqa-" + hashlib.sha1(png).hexdigest()[:16]
            tex += "\n\n" + GRAPHIC.format(name)
            image = [(name, png)]
        ans = tq.key_text(r)
        for old, new in FIXES.get((key, "answer"), []):
            if ans.count(old) != 1:
                raise SystemExit(f"FIX {key} answer: expected one {old!r}")
            ans = ans.replace(old, new)
        ref = ""
        ex = data / r["explanation"] if r["explanation"] not in ("NONE", "") else None
        if ex and ex.suffix == ".txt" and ex.exists():
            ref = ex.read_text(encoding="utf-8", errors="replace").strip()
        rows.append({"potd": f"{SET} {key}", "set": SET, "idx": key, "orig": "", "source": SET,
                     "subsource": f"{r['field']} / {r['subfield']} / {key}", "latexcode": tex, "answer": ans,
                     "solution": None, "hints": None, "more_hints": None, "ref_solution": ref,
                     "group": "subject", "effort": None, "image": image})
    return rows, left


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON (images as names)")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, left = load(a.data)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new) + tq.ERRORS
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: [x for x in problems if r["potd"] in x] or [excluded[r["potd"]]]
               for r in new if any(r["potd"] in x for x in problems) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([{k: v for k, v in dict(r, problems=why[r["potd"]]).items() if k != "image"}
                                              for r in new if r["potd"] in why], ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = []
    for key, why_left in left.items():
        print(f"left out: {key}: {why_left}")
    print("left out by reason:", json.dumps(collections.Counter(re.sub(r"\(.*", "", v).strip() for v in left.values()), ensure_ascii=False))
    print(json.dumps({"rows": len(rows), "in_bank": len(dup), "to_add": len(new), "check_problems": len(problems),
                      "subfields": collections.Counter(r["subsource"].split(" / ")[1] for r in new),
                      "images": sum(bool(r["image"]) for r in new)}))
    if a.dump:
        a.dump.write_text(json.dumps([dict(r, image=[n for n, _ in r["image"]] if r["image"] else None) for r in new],
                                     ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("theoremqa_leftovers")
    for r in new:
        for name, png in r["image"] or []:
            (TEXIMAGES / f"{name}.png").write_bytes(png)
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
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
