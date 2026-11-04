"""Move working that a question reveals (a worked solution, a solution sketch, a stated step) into its solution.

Proposals live in app/data/appdata/missing_refs/out_working/*.json, one object per question:
    {"qid", "status": "moved" | "no_change", "latexcode": new question, "solution_prefix": moved text, "images", "notes"}

    python -m app.tools.move_working            # check every proposal, write nothing
    python -m app.tools.move_working --apply    # back up the DB, then update question text, hash and solution

The moved text goes at the start of the solution (then a blank line, then the existing solution). An empty
solution_prefix means the solution already shows what the question gave away, so only the question changes. Old values of
both fields are logged in missing_refs/moved_working.jsonl so a move can be undone.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime

from app.persistence.ingest.seed import latex_hash
from app.tools.apply_missing_refs import APPDATA, DB, GRAPHIC, TEXIMAGES, WORK, balance, image_exists


def worse(old: str, new: str) -> list[str]:
    errs = []
    b_new, b_old = balance(new), balance(old)
    for k in b_new:
        n, o = b_new[k], b_old[k]
        bad = bool(set(n) - set(o)) if isinstance(n, list) else abs(n) > abs(o) or (n and n != o)
        if bad:
            errs.append(f"{k}: {o!r} -> {n!r}")
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    conn = sqlite3.connect(DB)
    good, blocked, counts = [], [], {}
    for f in sorted((WORK / "out_working").glob("*.json")):
        for it in json.loads(f.read_text(encoding="utf-8")):
            counts[it["status"]] = counts.get(it["status"], 0) + 1
            if it["status"] != "moved":
                continue
            row = conn.execute("SELECT latexcode, coalesce(solution, '') FROM questions WHERE question_id = ?",
                               (it["qid"],)).fetchone()
            if row is None:
                blocked.append((it["qid"], ["not in DB"]))
                continue
            q_old, s_old = row
            q_new = it["latexcode"]
            prefix = (it.get("solution_prefix") or "").strip()
            s_new = prefix + ("\n\n" + s_old.strip() if s_old.strip() else "")
            if not prefix:  # what the question gave away is already in the solution: only the question changes
                s_new = s_old
            errs = []
            if q_new.strip() == q_old.strip():
                errs.append("question unchanged")
            errs += [f"question {e}" for e in worse(q_old, q_new)]
            errs += [f"solution {e}" for e in worse(q_old + s_old, q_new + s_new)]
            for name in GRAPHIC.findall(q_new + s_new):
                if not image_exists(name):
                    errs.append(f"missing image {name}")
            (blocked if errs else good).append((it["qid"], errs) if errs else (it, q_old, s_old, q_new, s_new))
    print(f"proposals: {counts}; {len(good)} pass, {len(blocked)} blocked")
    for qid, errs in blocked:
        print(f"  BLOCKED {qid}: {'; '.join(errs)}")
    if not args.apply:
        print("dry run; pass --apply to write")
        return 0
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = sqlite3.connect(APPDATA / f"amplify.db.bak-{stamp}-pre-move-working")
    conn.backup(dst)
    dst.close()
    existing = {h: q for q, h in conn.execute("SELECT question_id, latex_hash FROM questions")}
    log = (WORK / "moved_working.jsonl").open("a", encoding="utf-8")
    n = 0
    with conn:
        for it, q_old, s_old, q_new, s_new in good:
            h = latex_hash(q_new)
            if h in existing and existing[h] != it["qid"]:
                print(f"  SKIP {it['qid']}: same text as question {existing[h]}")
                continue
            for name in GRAPHIC.findall(q_new + s_new):
                src = WORK / "images" / f"{name}.png"
                if src.exists():
                    shutil.copy2(src, TEXIMAGES / src.name)
            conn.execute("UPDATE questions SET latexcode = ?, latex_hash = ?, solution = ? WHERE question_id = ?",
                         (q_new, h, s_new, it["qid"]))
            existing[h] = it["qid"]
            log.write(json.dumps({"qid": it["qid"], "at": stamp, "old_question": q_old, "old_solution": s_old,
                                  "new_question": q_new, "new_solution": s_new, "notes": it.get("notes", "")},
                                 ensure_ascii=False) + "\n")
            n += 1
    log.close()
    print(f"updated {n} questions; backup amplify.db.bak-{stamp}-pre-move-working")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
