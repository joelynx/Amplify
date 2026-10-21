"""Validate solver, reviewer, and hint outputs; update per-question status.

Usage:
  python validate.py solver   [qid ...] [--jobs 4]
  python validate.py reviewer [qid ...] [--jobs 4]
  python validate.py hint     [qid ...] [--jobs 4]

With no ids, every question in the current batch at the matching stage is
validated. Each result is written to outputs/<id>/validate_<role>_<n>.json and
printed as one JSON line with the action the orchestrator must take:
  OK            -> proceed to the next stage
  RERUN         -> re-render and re-spawn the same role once more
  HUMAN_REVIEW  -> question marked needs_human_review (solver / reviewer)
  HINT_FAILED   -> hint left empty (hint only)
  MISSING_IMAGE -> subagent could not open an image; question skipped
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pdf import check_parts, check_pdf  # noqa: E402
from common import (  # noqa: E402
    PASS_STATUSES,
    active_ids,
    app_conn,
    check_web_parts,
    content_problems,
    drop_from_batch,
    fetch_question,
    format_answer,
    get_status,
    is_blank,
    load_config,
    log_event,
    normalize_answer,
    now_iso,
    parse_solver_output,
    pipe_conn,
    q_dir,
    read_text,
    review_attempt,
    solver_attempt_next,
    upsert_status,
    write_json,
    write_progress,
)

REVIEW_FIELDS = {
    "answers_agree": (bool,),
    "stored_answer_agrees": (bool, type(None)),
    "answer_section_correct": (bool,),
    "new_solution_correct": (bool,),
    "correct_answer_in_words": (str,),
    "errors": (list,),
    "reference_solution_errors": (list,),
    "has_rigor_notes": (bool,),
    "confidence": (str,),
}


def _rename_invalid(d: Path, stem: str, suffix: str, k: int) -> None:
    p = d / f"{stem}{suffix}"
    if p.exists():
        p.replace(d / f"{stem}_invalid_{k}{suffix}")


# --- solver -------------------------------------------------------------------


def validate_solver(qid: int, attempt: int | str, cfg: dict) -> dict:
    d = q_dir(qid)
    ab = attempt == "ab"
    f = d / ("solver_ab.tex" if ab else f"solver_{attempt}.tex")
    res: dict = {"role": "solver", "question_id": qid, "attempt": attempt, "checked_at": now_iso(), "errors": []}
    if not f.exists():
        res["errors"].append("solver output file missing")
        res["ok"] = False
        return res
    text = read_text(f)
    if text.strip() == "%%% IMAGE UNREADABLE":
        res["image_unreadable"] = True
        res["ok"] = False
        return res
    parts, errs = parse_solver_output(text, with_answer=not ab)
    res["errors"] += [f"structure: {e}" for e in errs]
    if parts is None:
        res["ok"] = False
        return res
    res["answer_type"] = parts["answer_type"]
    res["solution_chars"] = len(parts["solution"])
    # The solver writes the answer as bare LaTeX; it is checked in the exact
    # form assemble.py will store it (math delimiters added by code).
    formatted_answer = format_answer(parts["answer_type"], parts["answer"])
    if formatted_answer is not None:
        parts = dict(parts, answer=formatted_answer)
    for name in ("solution", "takeaways", "answer"):
        if name == "answer" and parts["answer_type"] == "NONE":
            continue
        res["errors"] += [f"rules [{name}]: {p}" for p in content_problems(parts[name])]
    b = cfg.get("solution_length_bounds_chars") or {}
    n = len(parts["solution"])
    if b.get("min") is not None and n < b["min"]:
        res["errors"].append(f"length: solution {n} chars < min {b['min']}")
    if b.get("max") is not None and n > b["max"]:
        res["errors"].append(f"length: solution {n} chars > max {b['max']}")
    check_parts_dict = {"solution": parts["solution"], "takeaways": parts["takeaways"]}
    if parts["answer_type"] != "NONE":
        check_parts_dict["answer"] = parts["answer"]
    pdf = check_parts(check_parts_dict, cfg=cfg)
    res["pdf_ok"] = pdf["ok"]
    res["errors"] += [f"pdf: {e}" for e in pdf["errors"]]
    if not pdf["ok"]:
        res["pdf_log_tail"] = pdf["log_tail"][-1200:]
    web = check_web_parts(check_parts_dict, d)
    res["web_ok"] = web["ok"]
    res["errors"] += [f"web: {e}" for e in web["errors"]]
    res["ok"] = not res["errors"]
    return res


# --- reviewer -----------------------------------------------------------------


def validate_reviewer(qid: int, attempt: int | str, cfg: dict, stored_answer_present: bool) -> dict:
    d = q_dir(qid)
    f = d / f"review_{attempt}.json"
    rig = d / f"review_{attempt}_rigor.tex"
    res: dict = {"role": "reviewer", "question_id": qid, "attempt": attempt, "checked_at": now_iso(), "errors": []}
    if not f.exists():
        res["errors"].append("review JSON file missing")
        res["ok"] = False
        return res
    text = read_text(f).strip()
    if text == "IMAGE UNREADABLE":
        res["image_unreadable"] = True
        res["ok"] = False
        return res
    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        res["errors"].append(f"review JSON does not parse: {e}")
    if isinstance(data, dict):
        for k, types in REVIEW_FIELDS.items():
            if k not in data:
                res["errors"].append(f"missing field '{k}'")
            elif not isinstance(data[k], types) or (bool in types and isinstance(data[k], int) and not isinstance(data[k], bool) and type(data[k]) is not bool):
                res["errors"].append(f"field '{k}' has wrong type {type(data[k]).__name__}")
        if isinstance(data.get("confidence"), str) and data["confidence"] not in ("high", "medium", "low"):
            res["errors"].append("confidence must be high, medium, or low")
        if "stored_answer_agrees" in data:
            if not stored_answer_present and data["stored_answer_agrees"] is not None:
                res["errors"].append("stored_answer_agrees must be null (no stored answer was given)")
            if stored_answer_present and data["stored_answer_agrees"] is None:
                res["errors"].append("stored_answer_agrees must be true/false (a stored answer was given)")
        for k in ("errors", "reference_solution_errors"):
            if isinstance(data.get(k), list) and not all(isinstance(x, str) for x in data[k]):
                res["errors"].append(f"field '{k}' must be a list of strings")
    elif data is not None:
        res["errors"].append("review JSON is not an object")
    if not rig.exists():
        res["errors"].append("rigor notes file missing")
        res["ok"] = False
        return res
    rtext = read_text(rig).strip()
    none = rtext == "%%% NONE"
    if isinstance(data, dict) and isinstance(data.get("has_rigor_notes"), bool):
        if data["has_rigor_notes"] == none:
            res["errors"].append("has_rigor_notes does not match the rigor file (%%% NONE iff false)")
    if not none:
        if not rtext:
            res["errors"].append("rigor notes file is empty (write %%% NONE if there are none)")
        if any(l.strip().startswith("%%%") for l in rtext.split("\n")):
            res["errors"].append("rigor notes contain marker lines")
        res["errors"] += [f"rules [rigor]: {p}" for p in content_problems(rtext)]
        pdf = check_pdf(rtext, cfg=cfg)
        res["pdf_ok"] = pdf["ok"]
        res["errors"] += [f"pdf: {e}" for e in pdf["errors"]]
        web = check_web_parts({"rigor": rtext}, d)
        res["web_ok"] = web["ok"]
        res["errors"] += [f"web: {e}" for e in web["errors"]]
    res["ok"] = not res["errors"]
    if res["ok"]:
        res["verdict"] = {k: data[k] for k in ("answers_agree", "stored_answer_agrees", "answer_section_correct", "new_solution_correct", "confidence")}
        res["n_errors_found"] = len(data["errors"])
    return res


# --- hint ---------------------------------------------------------------------


def validate_hint(qid: int, cfg: dict, accepted_attempt: int) -> dict:
    d = q_dir(qid)
    f = d / "hint.tex"
    res: dict = {"role": "hint", "question_id": qid, "attempt": 1, "checked_at": now_iso(), "errors": []}
    if not f.exists():
        res["errors"].append("hint file missing")
        res["ok"] = False
        return res
    lines = read_text(f).strip().split("\n")
    first = lines[0].strip() if lines else ""
    if first != "%%% CHECKLIST: PASSED":
        res["errors"].append(f"first line must be '%%% CHECKLIST: PASSED' (got {first[:40]!r})")
    hint = "\n".join(lines[1:]).strip()
    if not hint:
        res["errors"].append("empty hint")
    b = cfg.get("hint_length_bounds_chars") or {}
    if b.get("min") is not None and len(hint) < b["min"]:
        res["errors"].append(f"length: hint {len(hint)} chars < min {b['min']}")
    if b.get("max") is not None and len(hint) > b["max"]:
        res["errors"].append(f"length: hint {len(hint)} chars > max {b['max']}")
    if any(l.strip().startswith("%%%") for l in lines[1:]):
        res["errors"].append("hint contains extra marker lines")
    if hint:
        res["errors"] += [f"rules: {p}" for p in content_problems(hint)]
        # leak check against the accepted answer
        parts, _ = parse_solver_output(read_text(d / f"solver_{accepted_attempt}.tex"))
        if parts and parts["answer_type"] != "NONE":
            na = normalize_answer(parts["answer"])
            nh = re.sub(r"\s+", "", hint).replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "")
            if len(na) >= 2 and na in nh:
                res["errors"].append("leak: hint contains the final answer")
            if parts["answer_type"] == "NUMERICAL":
                num = re.sub(r"[^0-9.]", "", na)
                if len(num.replace(".", "")) >= 2 and re.search(rf"(?<![\d.]){re.escape(num)}(?![\d.])", hint):
                    res["errors"].append(f"leak: hint contains the numerical answer {num}")
        pdf = check_pdf(hint, cfg=cfg)
        res["pdf_ok"] = pdf["ok"]
        res["errors"] += [f"pdf: {e}" for e in pdf["errors"]]
        web = check_web_parts({"hint": hint}, d)
        res["web_ok"] = web["ok"]
        res["errors"] += [f"web: {e}" for e in web["errors"]]
    res["hint_chars"] = len(hint)
    res["ok"] = not res["errors"]
    return res


# --- driver -------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", choices=("solver", "reviewer", "hint"))
    ap.add_argument("ids", nargs="*", type=int)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--ab", action="store_true", help="validate the pilot A/B outputs (no status changes)")
    a = ap.parse_args()
    cfg = load_config()
    app = app_conn(cfg)
    pc = pipe_conn()
    sentinels = cfg["empty_answer_sentinels"]

    if a.ab:
        if a.role == "hint" or not a.ids:
            raise SystemExit("--ab needs explicit ids and role solver or reviewer")
        for qid in a.ids:
            if a.role == "solver":
                res = validate_solver(qid, "ab", cfg)
            else:
                q = fetch_question(app, qid)
                res = validate_reviewer(qid, "ab", cfg, not is_blank(q["answer"], sentinels))
            write_json(q_dir(qid) / f"validate_{a.role}_ab.json", res)
            print(json.dumps({"question_id": qid, "ab": True, "ok": res["ok"], "errors": res["errors"][:6]}))
        return

    # Everything that touches SQLite happens here on the main thread; the
    # worker threads only run compile checks on files.
    jobs = []
    for qid in a.ids or active_ids():
        row = get_status(pc, qid)
        if row is None:
            continue
        st = row["status"]
        if a.role == "solver" and (a.ids or st in ("triaged", "escalated")):
            jobs.append((qid, solver_attempt_next(row), None))
        elif a.role == "reviewer" and (a.ids or st in ("solved_1", "solved_2")):
            q = fetch_question(app, qid)
            present = not is_blank(q["answer"], sentinels)
            jobs.append((qid, review_attempt(row), present))
        elif a.role == "hint" and (a.ids or (st in PASS_STATUSES and row["hint_status"] == "pending")):
            jobs.append((qid, row["accepted_attempt"] or 1, None))

    def run(job):
        qid, attempt, extra = job
        if a.role == "solver":
            return validate_solver(qid, attempt, cfg)
        if a.role == "reviewer":
            return validate_reviewer(qid, attempt, cfg, bool(extra))
        return validate_hint(qid, cfg, attempt)

    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        results = list(ex.map(run, jobs))

    for (qid, attempt, _extra), res in zip(jobs, results):
        d = q_dir(qid)
        row = get_status(pc, qid)
        action = "OK"
        if res.get("image_unreadable"):
            upsert_status(pc, qid, status="missing_image", note=f"{a.role} subagent could not open an image")
            log_event(pc, qid, f"validate_{a.role}", "image unreadable")
            drop_from_batch(qid, "image unreadable")
            action = "MISSING_IMAGE"
        elif a.role == "solver":
            if res["ok"]:
                upsert_status(pc, qid, status=f"solved_{attempt}", attempts=attempt)
            elif row["solver_retries"] < 1:
                k = row["solver_retries"] + 1
                _rename_invalid(d, f"solver_{attempt}", ".tex", k)
                p = d / f"validate_solver_{attempt}.json"
                if p.exists():
                    p.replace(d / f"validate_solver_{attempt}_invalid_{k}.json")
                upsert_status(pc, qid, solver_retries=k)
                action = "RERUN"
            else:
                upsert_status(pc, qid, status="needs_human_review", note="solver output invalid twice: " + "; ".join(res["errors"])[:400])
                action = "HUMAN_REVIEW"
        elif a.role == "reviewer":
            if res["ok"]:
                upsert_status(pc, qid, status=f"reviewed_{attempt}")
                pc.execute(
                    "INSERT OR REPLACE INTO reviews (question_id, attempt, review_json, rigor_tex, created_at) VALUES (?,?,?,?,?)",
                    (qid, attempt, read_text(d / f"review_{attempt}.json"), read_text(d / f"review_{attempt}_rigor.tex"), now_iso()),
                )
                pc.commit()
            elif row["review_retries"] < 1:
                k = row["review_retries"] + 1
                _rename_invalid(d, f"review_{attempt}", ".json", k)
                _rename_invalid(d, f"review_{attempt}_rigor", ".tex", k)
                p = d / f"validate_reviewer_{attempt}.json"
                if p.exists():
                    p.replace(d / f"validate_reviewer_{attempt}_invalid_{k}.json")
                upsert_status(pc, qid, review_retries=k)
                action = "RERUN"
            else:
                upsert_status(pc, qid, status="needs_human_review", note="review output invalid twice: " + "; ".join(res["errors"])[:400])
                action = "HUMAN_REVIEW"
        else:  # hint
            if res["ok"]:
                upsert_status(pc, qid, hint_status="ok")
            elif row["hint_retries"] < 1:
                k = row["hint_retries"] + 1
                _rename_invalid(d, "hint", ".tex", k)
                p = d / "validate_hint_1.json"
                if p.exists():
                    p.replace(d / f"validate_hint_1_invalid_{k}.json")
                upsert_status(pc, qid, hint_retries=k, hint_status="retry")
                action = "RERUN"
            else:
                upsert_status(pc, qid, hint_status="failed", note="hint invalid twice: " + "; ".join(res["errors"])[:300])
                action = "HINT_FAILED"
        res["action"] = action
        write_json(d / f"validate_{a.role}_{attempt if a.role != 'hint' else 1}.json", res)
        log_event(pc, qid, f"validate_{a.role}", f"{action}: " + ("; ".join(res["errors"])[:300] or "ok"))
        print(json.dumps({"question_id": qid, "attempt": attempt, "action": action, "errors": res["errors"][:6]}))
    write_progress(pc)
    if not jobs:
        print(f"(nothing to validate for role {a.role})")


if __name__ == "__main__":
    main()
