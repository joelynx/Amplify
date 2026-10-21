"""Apply the pass / escalate / human-review logic to reviewed questions.

Rules (from the pipeline spec):
  Pass  = answers_agree AND new_solution_correct AND errors == [] AND
          answer_section_correct AND stored_answer_agrees is not false.
  Fail on attempt 1 -> escalated (re-solve at ESCALATE settings).
  Fail on attempt 2 -> needs_human_review. If the only failing condition is
          the stored answer, the note says "stored answer may be wrong".
  Pass with confidence low -> low_confidence (assembled, flagged).

Usage: python decide.py [qid ...]   (default: current batch, reviewed_1/2)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    active_ids,
    app_conn,
    fetch_question,
    get_status,
    is_blank,
    load_config,
    log_event,
    pipe_conn,
    q_dir,
    read_json,
    upsert_status,
    write_progress,
)


def decide_one(qid: int, cfg: dict, app, pc) -> dict:
    row = get_status(pc, qid)
    attempt = int(row["attempts"] or 0)
    data = read_json(q_dir(qid) / f"review_{attempt}.json")
    q = fetch_question(app, qid)
    core = (
        bool(data["answers_agree"])
        and bool(data["new_solution_correct"])
        and not data["errors"]
        and bool(data["answer_section_correct"])
    )
    stored_ok = data["stored_answer_agrees"] is not False
    passed = core and stored_ok
    if passed:
        status = "passed" if attempt == 1 else "passed_after_escalation"
        if data["confidence"] == "low":
            status = "low_confidence"
        hint_status = "skipped" if not is_blank(q["hints"]) else "none"
        upsert_status(pc, qid, status=status, accepted_attempt=attempt, hint_status=hint_status, note=None)
        decision = status
    elif attempt == 1:
        reasons = []
        if not data["answers_agree"]:
            reasons.append("answers disagree with reference")
        if not data["new_solution_correct"]:
            reasons.append("reviewer says solution incorrect")
        if data["errors"]:
            reasons.append(f"{len(data['errors'])} error(s): " + "; ".join(data["errors"])[:200])
        if not data["answer_section_correct"]:
            reasons.append("answer section wrong")
        if not stored_ok:
            reasons.append("disagrees with stored answer")
        upsert_status(pc, qid, status="escalated", solver_retries=0, review_retries=0, note="failed review 1: " + "; ".join(reasons))
        decision = "escalated"
    else:
        if core and not stored_ok:
            note = "stored answer may be wrong"
        else:
            note = "failed review after escalation: " + "; ".join(data["errors"])[:300]
        upsert_status(pc, qid, status="needs_human_review", note=note)
        decision = "needs_human_review"
    if data.get("reference_solution_errors"):
        log_event(pc, qid, "reference_solution_errors", json.dumps(data["reference_solution_errors"]))
    log_event(pc, qid, "decide", f"attempt {attempt}: {decision}")
    return {
        "question_id": qid,
        "attempt": attempt,
        "decision": decision,
        "confidence": data["confidence"],
        "answers_agree": data["answers_agree"],
        "stored_answer_agrees": data["stored_answer_agrees"],
        "reference_solution_errors": len(data.get("reference_solution_errors") or []),
    }


def main() -> None:
    cfg = load_config()
    app = app_conn(cfg)
    pc = pipe_conn()
    ids = [int(x) for x in sys.argv[1:]]
    if not ids:
        ids = [q for q in active_ids() if (get_status(pc, q) or {"status": ""})["status"] in ("reviewed_1", "reviewed_2")]
    for qid in ids:
        print(json.dumps(decide_one(qid, cfg, app, pc)))
    write_progress(pc)
    if not ids:
        print("(nothing to decide)")


if __name__ == "__main__":
    main()
