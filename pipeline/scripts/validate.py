"""Mechanical checks on one solver reply (API run). No model is consulted.

validate_solver_text(qid, text, cfg, stored_answer) returns a dict:
  ok           the solution, rigor notes, takeaways and answer passed every check
  errors       why not (structure, markdown/LaTeX rules, length, PDF, web view)
  hint_ok      the hint passed its own checks (rules, length, PDF, web, leak)
  hint_errors  why not; a bad hint never blocks the solution, it is just dropped
  answer_mismatch  the NUMERICAL answer differs from a numeric stored Answer
  parts        the parsed sections (None on a structural error)

Checks are the same ones the subagent-era validate.py ran, folded into one
function because the API returns the whole reply at once.

Usage from the command line (re-check a saved reply):
  python validate.py <qid> [--attempt N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pdf import check_parts  # noqa: E402
from common import (  # noqa: E402
    app_conn,
    check_web_parts,
    content_problems,
    fetch_question,
    format_answer,
    is_blank,
    load_config,
    normalize_answer,
    now_iso,
    parse_solver_output,
    q_dir,
    read_text,
    repair_slips,
    strip_code_fences,
    write_json,
)


def numeric_value(s: str | None) -> Decimal | None:
    """A plain number hidden in an answer string ('\\(025\\)', '72000 .', '1,024'),
    or None when the answer is not just a number."""
    if s is None:
        return None
    core = normalize_answer(str(s)).replace(",", "")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", core):
        return None
    try:
        return Decimal(core)
    except InvalidOperation:
        return None


def hint_leak_errors(hint: str, answer_type: str, answer: str) -> list[str]:
    """The hint must not contain the final answer (normalised LaTeX, and for
    numerical answers the bare number)."""
    errs: list[str] = []
    if answer_type == "NONE":
        return errs
    na = normalize_answer(answer)
    nh = re.sub(r"\s+", "", hint).replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "")
    if len(na) >= 2 and na in nh:
        errs.append("leak: hint contains the final answer")
    if answer_type == "NUMERICAL":
        num = re.sub(r"[^0-9.]", "", na)
        if len(num.replace(".", "")) >= 2 and re.search(rf"(?<![\d.]){re.escape(num)}(?![\d.])", hint):
            errs.append(f"leak: hint contains the numerical answer {num}")
    return errs


def validate_solver_text(qid: int, text: str, cfg: dict, stored_answer: str | None) -> dict:
    d = q_dir(qid)
    res: dict = {
        "question_id": qid,
        "checked_at": now_iso(),
        "errors": [],
        "hint_errors": [],
        "answer_mismatch": False,
        "parts": None,
    }
    text, fenced = strip_code_fences(text)
    if fenced:
        res["code_fences_stripped"] = True
    text, repairs = repair_slips(text)
    if repairs:
        res["repairs"] = repairs
    parts, errs = parse_solver_output(text, fmt="v5")
    res["errors"] += [f"structure: {e}" for e in errs]
    if parts is None:
        res["ok"] = False
        res["hint_ok"] = False
        return res
    res["parts"] = parts
    res["answer_type"] = parts["answer_type"]
    res["solution_chars"] = len(parts["solution"])

    # The answer is checked in the exact form assemble.py will store it.
    formatted_answer = format_answer(parts["answer_type"], parts["answer"])
    main: dict[str, str] = {"solution": parts["solution"]}
    if parts["rigor"]:
        main["rigor"] = parts["rigor"]
    main["takeaways"] = parts["takeaways"]
    if formatted_answer is not None:
        main["answer"] = formatted_answer
    for name, body in main.items():
        res["errors"] += [f"rules [{name}]: {p}" for p in content_problems(body)]
    b = cfg.get("solution_length_bounds_chars") or {}
    n = len(parts["solution"])
    if b.get("min") is not None and n < b["min"]:
        res["errors"].append(f"length: solution {n} chars < min {b['min']}")
    if b.get("max") is not None and n > b["max"]:
        res["errors"].append(f"length: solution {n} chars > max {b['max']}")

    hint = parts["hint"] or ""
    hb = cfg.get("hint_length_bounds_chars") or {}
    if hb.get("min") is not None and len(hint) < hb["min"]:
        res["hint_errors"].append(f"length: hint {len(hint)} chars < min {hb['min']}")
    if hb.get("max") is not None and len(hint) > hb["max"]:
        res["hint_errors"].append(f"length: hint {len(hint)} chars > max {hb['max']}")
    res["hint_errors"] += [f"rules: {p}" for p in content_problems(hint)]
    res["hint_errors"] += hint_leak_errors(hint, parts["answer_type"], parts["answer"])

    # One XeLaTeX compile for everything on the happy path; per-part on failure.
    pieces = dict(main)
    pieces["hint"] = hint
    pdf = check_parts(pieces, cfg=cfg)
    res["pdf_ok"] = pdf["ok"]
    for e in pdf["errors"]:
        (res["hint_errors"] if e.startswith("[hint]") else res["errors"]).append(f"pdf: {e}")
    if not pdf["ok"]:
        res["pdf_log_tail"] = pdf["log_tail"][-1200:]
    web = check_web_parts(pieces, d)
    res["web_ok"] = web["ok"]
    for e in web["errors"]:
        (res["hint_errors"] if e.startswith("[hint]") else res["errors"]).append(f"web: {e}")

    # Stored numeric Answer (e.g. AIME): a free correctness signal. Only plain
    # numbers are compared; anything else is left to the solver.
    if cfg.get("check_stored_numeric_answer", True) and parts["answer_type"] == "NUMERICAL":
        sv = numeric_value(stored_answer)
        nv = numeric_value(parts["answer"])
        if sv is not None and nv is not None:
            res["stored_answer"] = str(sv)
            res["answer_mismatch"] = sv != nv

    res["ok"] = not res["errors"]
    res["hint_ok"] = not res["hint_errors"]
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("qid", type=int)
    ap.add_argument("--attempt", type=int, default=1)
    a = ap.parse_args()
    cfg = load_config()
    app = app_conn(cfg)
    q = fetch_question(app, a.qid)
    if q is None:
        raise SystemExit(f"{a.qid}: not in database")
    stored = None if is_blank(q["answer"], cfg["empty_answer_sentinels"]) else q["answer"]
    text = read_text(q_dir(a.qid) / f"solver_{a.attempt}.tex")
    res = validate_solver_text(a.qid, text, cfg, stored)
    write_json(q_dir(a.qid) / f"validate_{a.attempt}_manual.json", res)
    print(json.dumps({k: v for k, v in res.items() if k != "parts"}, indent=2))


if __name__ == "__main__":
    main()
