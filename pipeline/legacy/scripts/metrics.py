"""Per-batch metrics, drift warnings, canary scheduling, and spot-check picks.

Usage:
  python metrics.py [--batch N]                  # append a line to run_log.md
  python metrics.py --compare-canaries <run_outputs_dir>
"""

from __future__ import annotations

import argparse
import datetime
import json
import random
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    OUTPUTS_DIR,
    PASS_STATUSES,
    PIPELINE_DIR,
    RUN_LOG,
    current_batch,
    get_status,
    is_done,
    load_config,
    pipe_conn,
    read_json,
    read_text,
)

META = PIPELINE_DIR / "meta.json"


def _exists(qid: int, name: str) -> bool:
    return (OUTPUTS_DIR / str(qid) / name).exists()


def _first_validate(qid: int) -> dict | None:
    d = OUTPUTS_DIR / str(qid)
    for name in ("validate_solver_1_invalid_1.json", "validate_solver_1.json"):
        p = d / name
        if p.exists():
            return read_json(p)
    return None


def batch_metrics(pc, batch: int) -> dict:
    row = pc.execute("SELECT * FROM batches WHERE batch=?", (batch,)).fetchone()
    ids = json.loads(row["question_ids"])
    rows = {q: get_status(pc, q) for q in ids}
    n = len(ids)
    statuses = [r["status"] if r else "pending" for r in rows.values()]
    pass_first = sum(1 for r in rows.values() if r and r["status"] in PASS_STATUSES and r["accepted_attempt"] == 1)
    escalated = sum(1 for q, r in rows.items() if r and (r["status"] == "escalated" or (r["attempts"] or 0) >= 2 or _exists(q, "solver_2.tex")))
    human = statuses.count("needs_human_review")
    low = statuses.count("low_confidence")
    missing = statuses.count("missing_image")
    reviewed1 = disagree_old = stored_present = disagree_stored = 0
    for q in ids:
        p = OUTPUTS_DIR / str(q) / "review_1.json"
        if not p.exists():
            continue
        try:
            d = read_json(p)
        except Exception:
            continue
        reviewed1 += 1
        if d.get("answers_agree") is False:
            disagree_old += 1
        if d.get("stored_answer_agrees") is not None:
            stored_present += 1
            if d.get("stored_answer_agrees") is False:
                disagree_stored += 1
    pdf_fail = web_fail = validated1 = 0
    for q in ids:
        v = _first_validate(q)
        if v is None:
            continue
        validated1 += 1
        if v.get("pdf_ok") is False:
            pdf_fail += 1
        if v.get("web_ok") is False:
            web_fail += 1
    lengths = [len(r[0]) for r in pc.execute(
        f"SELECT final_tex FROM finals WHERE question_id IN ({','.join('?' * n)})", ids)] if n else []
    hints = sum(1 for r in rows.values() if r and r["hint_status"] == "ok")
    hint_failed = sum(1 for r in rows.values() if r and r["hint_status"] == "failed")
    return {
        "batch": batch,
        "kind": row["kind"],
        "n": n,
        "id_range": [min(ids), max(ids)] if ids else None,
        "pass_first": pass_first,
        "escalated": escalated,
        "needs_human_review": human,
        "low_confidence": low,
        "missing_image": missing,
        "reviewed_first": reviewed1,
        "answer_disagree_old": disagree_old,
        "stored_present": stored_present,
        "answer_disagree_stored": disagree_stored,
        "validated_first": validated1,
        "pdf_fail_first": pdf_fail,
        "web_fail_first": web_fail,
        "hints_ok": hints,
        "hints_failed": hint_failed,
        "len_avg": round(statistics.mean(lengths)) if lengths else None,
        "len_median": round(statistics.median(lengths)) if lengths else None,
        "assembled": len(lengths),
    }


def rate(a, b):
    return (a / b) if b else None


def drift_warnings(pc, m: dict) -> list[str]:
    prev = [json.loads(r[0]) for r in pc.execute(
        "SELECT metrics_json FROM batches WHERE batch<? AND metrics_json IS NOT NULL AND kind IN ('normal','pilot')", (m["batch"],))]
    if not prev:
        return []
    def avg(key, denom):
        xs = [rate(p[key], p[denom]) for p in prev if rate(p[key], p[denom]) is not None]
        return statistics.mean(xs) if xs else None
    warns = []
    cur_esc, old_esc = rate(m["escalated"], m["n"]), avg("escalated", "n")
    if cur_esc is not None and old_esc is not None and cur_esc > 2 * old_esc and cur_esc > 0.2:
        warns.append(f"escalation rate {cur_esc:.0%} vs running {old_esc:.0%}")
    cur_pdf, old_pdf = rate(m["pdf_fail_first"], m["validated_first"]), avg("pdf_fail_first", "validated_first")
    if cur_pdf is not None and old_pdf is not None and cur_pdf > max(0.1, 2 * old_pdf):
        warns.append(f"PDF-check failure rate {cur_pdf:.0%} vs running {old_pdf:.0%}")
    cur_web, old_web = rate(m["web_fail_first"], m["validated_first"]), avg("web_fail_first", "validated_first")
    if cur_web is not None and old_web is not None and cur_web > max(0.1, 2 * old_web):
        warns.append(f"web-check failure rate {cur_web:.0%} vs running {old_web:.0%}")
    lens = [p["len_avg"] for p in prev if p.get("len_avg")]
    if lens and m.get("len_avg") and m["len_avg"] < 0.75 * statistics.mean(lens):
        warns.append(f"average solution length {m['len_avg']} vs running {round(statistics.mean(lens))}")
    return warns


def canary_due(pc, cfg) -> tuple[bool, int]:
    if not cfg.get("canary_ids"):
        return False, 0
    done = sum(1 for r in pc.execute("SELECT * FROM status") if is_done(r))
    meta = read_json(META) if META.exists() else {}
    last = int(meta.get("last_canary_done_count", 0))
    every = int(cfg.get("canary_every_n_questions") or 100)
    return (done // every) > (last // every), done


def mark_canary_run(pc) -> None:
    done = sum(1 for r in pc.execute("SELECT * FROM status") if is_done(r))
    meta = read_json(META) if META.exists() else {}
    meta["last_canary_done_count"] = done
    META.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def compare_canaries(cfg, run_dir: Path) -> list[str]:
    lines = []
    for qid in cfg.get("canary_ids", []):
        approved = PIPELINE_DIR / "canaries" / str(qid) / "approved_final.tex"
        new = run_dir / str(qid) / "final.tex"
        if not approved.exists() or not new.exists():
            lines.append(f"{qid}: missing {'approved' if not approved.exists() else 'new'} final.tex")
            continue
        a, b = read_text(approved), read_text(new)
        def final_answer(t):
            m = re.search(r"Final answer:(.*)", t)
            return re.sub(r"\s+", "", m.group(1)) if m else ""
        same_ans = final_answer(a) == final_answer(b)
        ratio = len(b) / max(1, len(a))
        struct_a = ("Rigor Notes" in a, "Takeaways" in a)
        struct_b = ("Rigor Notes" in b, "Takeaways" in b)
        flags = []
        if not same_ans:
            flags.append("ANSWER CHANGED")
        if not (0.75 <= ratio <= 1.25):
            flags.append(f"length x{ratio:.2f}")
        if struct_a != struct_b:
            flags.append("structure changed")
        lines.append(f"{qid}: {'ok' if not flags else '; '.join(flags)} (approved {len(a)} chars, new {len(b)} chars)")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int)
    ap.add_argument("--compare-canaries")
    ap.add_argument("--mark-canary-run", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    pc = pipe_conn()
    if a.compare_canaries:
        for l in compare_canaries(cfg, Path(a.compare_canaries)):
            print(l)
        return
    if a.mark_canary_run:
        mark_canary_run(pc)
        print("canary run recorded")
        return
    batch = a.batch or current_batch().get("batch")
    if not batch:
        raise SystemExit("no batch")
    m = batch_metrics(pc, batch)
    warns = drift_warnings(pc, m)
    pc.execute("UPDATE batches SET metrics_json=? WHERE batch=?", (json.dumps(m), batch))
    pc.commit()
    today = datetime.date.today().isoformat()
    rng = m["id_range"]
    line = (
        f"| {today} | batch {batch} ({m['kind']}) | ids {rng[0]}-{rng[1]} n={m['n']} "
        f"| pass1 {m['pass_first']}/{m['n']} | esc {m['escalated']} | human {m['needs_human_review']} | low {m['low_confidence']} | no-img {m['missing_image']} "
        f"| ans!=old {m['answer_disagree_old']}/{m['reviewed_first']} | ans!=stored {m['answer_disagree_stored']}/{m['stored_present']} "
        f"| pdf-fail1 {m['pdf_fail_first']}/{m['validated_first']} | web-fail1 {m['web_fail_first']}/{m['validated_first']} "
        f"| hints {m['hints_ok']} ok/{m['hints_failed']} failed | len avg/med {m['len_avg']}/{m['len_median']} | {cfg['prompt_version']} "
        f"| {'DRIFT: ' + '; '.join(warns) if warns else ''} |"
    )
    if not RUN_LOG.exists():
        RUN_LOG.write_text("# Pipeline run log\n\nOne line per batch.\n\n", encoding="utf-8")
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(json.dumps(m))
    for w in warns:
        print("PAUSE - metric shifted sharply: " + w)
    due, done = canary_due(pc, cfg)
    if due:
        print(f"CANARY DUE: {done} questions done; rerun canaries {cfg['canary_ids']} (see README)")
    ids = json.loads(pc.execute("SELECT question_ids FROM batches WHERE batch=?", (batch,)).fetchone()[0])
    passed = [q for q in ids if (get_status(pc, q) or {"status": ""})["status"] in PASS_STATUSES and (OUTPUTS_DIR / str(q) / "preview.pdf").exists()]
    random.seed(batch)
    picks = random.sample(passed, min(2, len(passed)))
    for q in picks:
        print(f"SPOT-CHECK: {(OUTPUTS_DIR / str(q) / 'preview.pdf').as_posix()}")


if __name__ == "__main__":
    main()
