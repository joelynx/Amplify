"""Fill a prompt template for one question and emit the spawn settings.

Usage:
  python render_prompt.py solver   [qid ...] [--attempt N]
  python render_prompt.py reviewer [qid ...] [--attempt N]
  python render_prompt.py hint     [qid ...]
  python render_prompt.py router   [qid ...]

With no ids, renders for every question in the current batch that is at the
right stage for that role. Placeholders are replaced by plain string
substitution (never str.format) because prompts contain literal braces.

Each rendered prompt goes to outputs/<id>/prompt_<role>_<attempt>.md and a
spawn spec (model, effort, the one-line wrapper prompt, expected reply) to
outputs/<id>/spawn_<role>_<attempt>.json. The script prints the spawn specs.

Code-level guarantee: the solver template is refused if it references the old
solution or the stored answer, and those values are never passed to it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    PASS_STATUSES,
    PROMPTS_DIR,
    active_ids,
    app_conn,
    fetch_question,
    get_status,
    images_placeholder,
    is_blank,
    load_config,
    now_iso,
    pipe_conn,
    q_dir,
    read_text,
    review_attempt,
    solver_attempt_next,
    upsert_status,
    write_json,
    write_text,
)

ROLES = ("solver", "reviewer", "hint", "router")
REPLY_WORD = {"solver": "solver done", "reviewer": "review done", "hint": "hint done", "router": "triage done"}


def settings_for(cfg: dict, role: str, row, attempt: int) -> dict:
    if role == "solver":
        if attempt >= 2:
            return cfg["solver"]["ESCALATE"]
        level = row["level"] or "INSIGHT"
        return cfg["solver"][level]
    return cfg[role]


def _in_flight(qid: int, role: str, attempt: int) -> bool:
    """A prompt was rendered for this stage but its output has not been
    validated yet: a subagent is (or should be) working on it. Skip it so a
    stage-wide render never displaces an output that is being written."""
    d = q_dir(qid)
    tag = "1" if role == "hint" else str(attempt)
    return (d / f"spawn_{role}_{tag}.json").exists() and not (d / f"validate_{role}_{tag}.json").exists()


def default_ids(pc, role: str) -> list[int]:
    ids = []
    for qid in active_ids():
        row = get_status(pc, qid)
        if row is None:
            continue
        st = row["status"]
        if role == "solver" and st in ("triaged", "escalated"):
            if not _in_flight(qid, "solver", solver_attempt_next(row)):
                ids.append(qid)
        elif role == "reviewer" and st in ("solved_1", "solved_2"):
            if not _in_flight(qid, "reviewer", review_attempt(row)):
                ids.append(qid)
        elif role == "hint" and st in PASS_STATUSES and row["hint_status"] in ("none", "retry"):
            ids.append(qid)
        elif role == "router" and st in ("pending", "triaged"):
            ids.append(qid)
    return ids


def render_ab(role: str, qid: int, cfg: dict, app, pc) -> dict:
    """Pilot-only A/B variant: solve with the answer section removed from the
    prompt (prompts/solver_noanswer.md) and review that solution. Files are
    solver_ab.tex / review_ab.json / review_ab_rigor.tex; status is untouched."""
    q = fetch_question(app, qid)
    row = get_status(pc, qid)
    if q is None or row is None:
        raise SystemExit(f"{qid}: not in database / status table")
    d = q_dir(qid)
    fills: dict[str, str] = {
        "QUESTION_ID": str(qid),
        "QUESTION": q["latexcode"],
        "IMAGES": images_placeholder(qid),
        "FORMAT_RULES": read_text(PROMPTS_DIR / "format_rules.md").strip(),
    }
    if role == "solver":
        tpl = read_text(PROMPTS_DIR / "solver_noanswer.md")
        if "{{OLD_SOLUTION}}" in tpl or "{{STORED_ANSWER}}" in tpl or "ANSWER TYPE" in tpl:
            raise SystemExit("refusing to render: solver_noanswer template is not answer-free / references the old solution")
        fills["OUTPUT_PATH"] = (d / "solver_ab.tex").as_posix()
        st = settings_for(cfg, "solver", row, 1)
    elif role == "reviewer":
        tpl = read_text(PROMPTS_DIR / "reviewer.md")
        fills["NEW_SOLUTION"] = read_text(d / "solver_ab.tex").strip()
        fills["OLD_SOLUTION"] = q["solution"].strip() if not is_blank(q["solution"]) else "None"
        fills["STORED_ANSWER"] = q["answer"].strip() if not is_blank(q["answer"], cfg["empty_answer_sentinels"]) else "None"
        fills["OUTPUT_PATH"] = (d / "review_ab.json").as_posix()
        fills["RIGOR_PATH"] = (d / "review_ab_rigor.tex").as_posix()
        st = cfg["reviewer"]
    else:
        raise SystemExit("--ab supports solver and reviewer only")
    text = tpl
    for k, v in fills.items():
        text = text.replace("{{" + k + "}}", v)
    if re.findall(r"\{\{[A-Z_]+\}\}", text):
        raise SystemExit(f"{qid}: unfilled placeholders in A/B {role} template")
    prompt_path = d / f"prompt_{role}_ab.md"
    write_text(prompt_path, text)
    spec = {
        "role": role, "ab": True, "question_id": qid, "attempt": "ab", "level": row["level"],
        "model": st["model"], "effort": st["effort"], "prompt_path": prompt_path.as_posix(),
        "output_path": fills["OUTPUT_PATH"],
        "prompt": cfg["spawn_wrapper"].format(prompt_path=prompt_path.as_posix()),
        "expected_reply": f"{qid}: {REPLY_WORD[role]}", "prompt_version": cfg["prompt_version"],
        "rendered_at": now_iso(),
    }
    write_json(d / f"spawn_{role}_ab.json", spec)
    return spec


def render(role: str, qid: int, cfg: dict, app, pc, attempt: int | None = None) -> dict:
    q = fetch_question(app, qid)
    if q is None:
        raise SystemExit(f"{qid}: not in database")
    row = get_status(pc, qid)
    if row is None:
        raise SystemExit(f"{qid}: not in the pipeline status table (run next_batch.py first)")
    tpl = read_text(PROMPTS_DIR / f"{role}.md")
    d = q_dir(qid)
    fills: dict[str, str] = {
        "QUESTION_ID": str(qid),
        "QUESTION": q["latexcode"],
        "IMAGES": images_placeholder(qid),
        "FORMAT_RULES": read_text(PROMPTS_DIR / "format_rules.md").strip(),
    }
    sentinels = cfg["empty_answer_sentinels"]

    if role == "solver":
        if "{{OLD_SOLUTION}}" in tpl or "{{STORED_ANSWER}}" in tpl:
            raise SystemExit("refusing to render: the solver template references the old solution or stored answer")
        attempt = attempt or solver_attempt_next(row)
        out = d / f"solver_{attempt}.tex"
        if out.exists():
            out.replace(d / f"solver_{attempt}_superseded_{now_iso().replace(':', '')}.tex")
        fills["OUTPUT_PATH"] = out.as_posix()
    elif role == "reviewer":
        attempt = attempt or review_attempt(row)
        if attempt < 1:
            raise SystemExit(f"{qid}: no validated solver output to review yet")
        sol_path = d / f"solver_{attempt}.tex"
        if not sol_path.exists():
            raise SystemExit(f"{qid}: {sol_path.name} missing")
        fills["NEW_SOLUTION"] = read_text(sol_path).strip()
        fills["OLD_SOLUTION"] = q["solution"].strip() if not is_blank(q["solution"]) else "None"
        fills["STORED_ANSWER"] = q["answer"].strip() if not is_blank(q["answer"], sentinels) else "None"
        fills["OUTPUT_PATH"] = (d / f"review_{attempt}.json").as_posix()
        fills["RIGOR_PATH"] = (d / f"review_{attempt}_rigor.tex").as_posix()
        for name in (f"review_{attempt}.json", f"review_{attempt}_rigor.tex"):
            p = d / name
            if p.exists():
                p.replace(d / f"{p.stem}_superseded_{now_iso().replace(':', '')}{p.suffix}")
    elif role == "hint":
        acc = row["accepted_attempt"]
        if not acc:
            raise SystemExit(f"{qid}: no accepted solution; hint needs a passed review")
        attempt = 1
        fills["ACCEPTED_SOLUTION"] = read_text(d / f"solver_{acc}.tex").strip()
        fills["HINT_EXAMPLES"] = read_text(PROMPTS_DIR / "hint_examples.md").strip()
        out = d / "hint.tex"
        if out.exists():
            out.replace(d / f"hint_superseded_{now_iso().replace(':', '')}.tex")
        fills["OUTPUT_PATH"] = out.as_posix()
    elif role == "router":
        attempt = 1
        fills["OLD_SOLUTION"] = q["solution"].strip() if not is_blank(q["solution"]) else "None"
        fills["OUTPUT_PATH"] = (d / "triage.txt").as_posix()
    else:
        raise SystemExit(f"unknown role {role}")

    text = tpl
    for k, v in fills.items():
        text = text.replace("{{" + k + "}}", v)
    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)))
    if leftover:
        raise SystemExit(f"{qid}: unfilled placeholders {leftover} in {role} template")
    prompt_path = d / f"prompt_{role}_{attempt}.md"
    write_text(prompt_path, text)

    st = settings_for(cfg, role, row, attempt)
    spec = {
        "role": role,
        "question_id": qid,
        "attempt": attempt,
        "level": row["level"],
        "model": st["model"],
        "effort": st["effort"],
        "prompt_path": prompt_path.as_posix(),
        "output_path": fills["OUTPUT_PATH"],
        "prompt": cfg["spawn_wrapper"].format(prompt_path=prompt_path.as_posix()),
        "expected_reply": f"{qid}: {REPLY_WORD[role]}",
        "prompt_version": cfg["prompt_version"],
        "rendered_at": now_iso(),
    }
    write_json(d / f"spawn_{role}_{attempt}.json", spec)

    rec: dict = {}
    if role == "solver":
        rec[f"solver{min(attempt, 2)}_model"] = st["model"]
        rec[f"solver{min(attempt, 2)}_effort"] = st["effort"]
    elif role == "reviewer":
        rec["reviewer_model"] = st["model"]
        rec["reviewer_effort"] = st["effort"]
    elif role == "hint":
        rec["hint_model"] = st["model"]
        rec["hint_effort"] = st["effort"]
        rec["hint_status"] = "pending"
    if rec:
        upsert_status(pc, qid, **rec)
    return spec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", choices=ROLES)
    ap.add_argument("ids", nargs="*", type=int)
    ap.add_argument("--attempt", type=int)
    ap.add_argument("--ab", action="store_true", help="pilot A/B variant without the answer section (explicit ids required)")
    a = ap.parse_args()
    cfg = load_config()
    app = app_conn(cfg)
    pc = pipe_conn()
    if a.ab:
        if not a.ids:
            raise SystemExit("--ab needs explicit question ids")
        specs = [render_ab(a.role, qid, cfg, app, pc) for qid in a.ids]
    else:
        ids = a.ids or default_ids(pc, a.role)
        specs = [render(a.role, qid, cfg, app, pc, a.attempt) for qid in ids]
    for s in specs:
        print(json.dumps({k: s[k] for k in ("question_id", "role", "attempt", "level", "model", "effort", "prompt", "expected_reply")}))
    if not specs:
        print(f"(no questions at the {a.role} stage in the current batch)")


if __name__ == "__main__":
    main()
