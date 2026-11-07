"""Solution pipeline runner on the Claude Message Batches API.

One fixed model and effort (config.solver), no triage, no reviewer. Questions
are processed source by source in the order of config.sources. Every batch is
one Message Batches request (half price on every token); the static
instructions are a cached system prompt; the old solution is never sent; any
question that references an image is skipped.

Usage (from the repo root; key in ANTHROPIC_API_KEY or pipeline/.anthropic_key):
  python pipeline/scripts/run.py check                  # free: is the key (and workspace) accepted?
  python pipeline/scripts/run.py status                 # progress by source, in-flight batches, spend
  python pipeline/scripts/run.py queue   [--n 20]       # preview the next questions in priority order
  python pipeline/scripts/run.py submit  [--n N] [--ids 1,2,3] [--dry-run]
  python pipeline/scripts/run.py collect [--wait] [--download-only]   # fetch ended batches, then judge
  python pipeline/scripts/run.py judge   [--watch] [--workers N]      # validate/assemble downloaded replies (no key)
  python pipeline/scripts/run.py loop    [--n N] [--max-batches K] [--budget-usd X]
  python pipeline/scripts/run.py cost                   # spend so far, average per question, projection
  python pipeline/scripts/run.py cancel                 # cancel every in-flight batch
  python pipeline/scripts/run.py reset   --yes          # archive pipeline.db and outputs, start fresh

Per question the files are outputs/<id>/solver_<attempt>.tex (the raw reply),
response_<attempt>.json (usage, stop reason), validate_<attempt>.json,
feedback_<attempt>.json (what a retry is told), and after acceptance final.tex,
final_app.json, preview.pdf.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_fields import apply_pending  # noqa: E402
from assemble import assemble_one  # noqa: E402
from common import (  # noqa: E402
    OUTPUTS_DIR,
    PIPELINE_DB,
    PIPELINE_DIR,
    PROGRESS_JSON,
    PROMPTS_DIR,
    RUN_LOG,
    app_conn,
    fetch_question,
    get_status,
    image_reason,
    is_blank,
    is_done,
    load_config,
    log_event,
    now_iso,
    pipe_conn,
    pipeline_wrote,
    q_dir,
    read_json,
    read_text,
    source_rank,
    target_questions,
    upsert_status,
    write_json,
    write_progress,
    write_text,
)
from validate import validate_solver_text  # noqa: E402

QUEUEABLE = {"pending", "retry"}


# --- client and prompt ----------------------------------------------------------


KEY_FILE = PIPELINE_DIR / ".anthropic_key"  # git-ignored: the key on one line, optionally a wrkspc_ id on another


def _key_file_lines() -> list[str]:
    if not KEY_FILE.exists():
        return []
    return [ln.strip() for ln in KEY_FILE.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def api_key() -> str:
    """ANTHROPIC_API_KEY from the environment, else the key line of
    pipeline/.anthropic_key (git-ignored)."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        key = next((ln for ln in _key_file_lines() if not ln.startswith("wrkspc_")), "")
    if not key:
        raise SystemExit(
            "No API key. Put the key on one line in pipeline/.anthropic_key (git-ignored),\n"
            "or set ANTHROPIC_API_KEY:\n"
            "  PowerShell, this window only:  $env:ANTHROPIC_API_KEY = 'sk-ant-...'\n"
            "  PowerShell, persistent:        setx ANTHROPIC_API_KEY sk-ant-...   (then open a new window)"
        )
    return key


def workspace_id() -> str | None:
    """ANTHROPIC_WORKSPACE_ID from the environment, else a wrkspc_ line in
    pipeline/.anthropic_key. Required for a multi-workspace personal key (the
    API sends every request to the workspace named in anthropic-workspace-id);
    a key created for one workspace needs none."""
    ws = os.environ.get("ANTHROPIC_WORKSPACE_ID", "").strip()
    if not ws:
        ws = next((ln for ln in _key_file_lines() if ln.startswith("wrkspc_")), "")
    return ws or None


def get_client():
    import anthropic

    ws = workspace_id()
    headers = {"anthropic-workspace-id": ws} if ws else None
    return anthropic.Anthropic(api_key=api_key(), max_retries=5, default_headers=headers)


def check() -> None:
    """Free round trip (no tokens): list one batch and print the workspace the
    key resolved to. Run this before the first submit."""
    import anthropic

    client = get_client()
    try:
        raw = client.messages.batches.with_raw_response.list(limit=1)
    except anthropic.APIStatusError as e:
        msg = getattr(e, "message", str(e))
        print(json.dumps({"ok": False, "status": e.status_code, "error": msg}, indent=1))
        if "anthropic-workspace-id" in msg:
            print(
                "This is a multi-workspace personal key. Put the wrkspc_ id (Claude Console -> Settings ->\n"
                "Workspaces, ID column) on its own line in pipeline/.anthropic_key, or set\n"
                "ANTHROPIC_WORKSPACE_ID, or create a key scoped to a single workspace."
            )
        raise SystemExit(1) from None
    page = raw.parse()
    print(json.dumps({
        "ok": True,
        "workspace_id": raw.headers.get("anthropic-workspace-id"),
        "organization_id": raw.headers.get("anthropic-organization-id"),
        "batches_visible_in_workspace": len(page.data),
        "key_source": "ANTHROPIC_API_KEY" if os.environ.get("ANTHROPIC_API_KEY") else KEY_FILE.as_posix(),
        "workspace_source": "ANTHROPIC_WORKSPACE_ID" if os.environ.get("ANTHROPIC_WORKSPACE_ID")
        else (KEY_FILE.as_posix() if workspace_id() else "none (single-workspace key)"),
    }, indent=1))


def system_prompt(cfg: dict) -> str:
    """The static part of every request, filled from prompts/. Refuses to build
    a prompt that could carry the old solution or the stored answer."""
    tpl = read_text(PROMPTS_DIR / "solver.md")
    for banned in ("{{OLD_SOLUTION}}", "{{STORED_ANSWER}}", "{{NEW_SOLUTION}}"):
        if banned in tpl:
            raise SystemExit(f"refusing to build the solver prompt: template references {banned}")
    fills = {
        "FORMAT_RULES": read_text(PROMPTS_DIR / "format_rules.md").strip(),
        "HINT_EXAMPLES": read_text(PROMPTS_DIR / "hint_examples.md").strip(),
    }
    for k, v in fills.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    import re

    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", tpl)))
    if leftover:
        raise SystemExit(f"unfilled placeholders in solver.md: {leftover}")
    return tpl.strip() + "\n"


def user_text(q: dict, feedback: dict | None) -> str:
    text = "QUESTION (in LaTeX):\n" + q["latexcode"].strip() + "\n"
    if not feedback:
        return text
    if feedback["kind"] == "feedback":
        bullets = "\n".join(f"- {e}" for e in feedback["errors"])
        text += (
            "\nYour previous reply to this question is below. It was rejected by the automatic checks "
            "for these reasons:\n" + bullets + "\n\n"
            "Write the complete reply again in the required structure with these problems fixed. "
            "Do not mention the previous reply.\n\nPREVIOUS REPLY:\n" + feedback["previous_text"].strip() + "\n"
        )
    else:  # blind re-solve
        text += (
            f"\nNote: an earlier attempt at this question was rejected ({feedback['reason']}). "
            "Solve it carefully from scratch and double-check the final answer before writing it.\n"
        )
    return text


def build_request(cfg: dict, system: str, q: dict, qid: int, attempt: int, feedback: dict | None):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    st = cfg["solver"]
    cache: dict = {"type": "ephemeral"}
    if cfg.get("cache_ttl") == "1h":
        cache["ttl"] = "1h"
    params = MessageCreateParamsNonStreaming(
        model=st["model"],
        max_tokens=int(st["max_tokens"]),
        system=[{"type": "text", "text": system, "cache_control": cache}],
        output_config={"effort": st["effort"]},
        messages=[{"role": "user", "content": [{"type": "text", "text": user_text(q, feedback)}]}],
    )
    return Request(custom_id=f"q{qid}-a{attempt}", params=params)


def parse_custom_id(cid: str) -> tuple[int, int]:
    q, a = cid[1:].split("-a")
    return int(q), int(a)


# --- selection ----------------------------------------------------------------


def ordered_candidates(pc, app, cfg: dict, ids: list[int] | None = None) -> list[int]:
    """Unfinished questions in processing order: retries first, then everything
    else by source priority and question id. Submitted questions are excluded."""
    rows = {r["question_id"]: r for r in pc.execute("SELECT * FROM status")}
    ordered = [q for q, _ in target_questions(app, cfg)]
    if ids:
        want = set(ids)
        ordered = [q for q in ordered if q in want]
        missing = want - set(ordered)
        if missing:
            raise SystemExit(f"not target questions: {sorted(missing)}")
    retry, fresh = [], []
    for q in ordered:
        r = rows.get(q)
        if r is None:
            fresh.append(q)
        elif is_done(r) or r["status"] in ("submitted", "received"):
            continue
        elif r["status"] == "retry":
            retry.append(q)
        else:  # pending, or a legacy non-final status
            fresh.append(q)
    return retry + fresh


# --- submit -------------------------------------------------------------------


def submissions_closed(cfg: dict) -> bool:
    """Owner decision (2026-10-21): nothing is submitted to the API any more.
    `config.submissions_closed` locks submit/loop; a dry run still works."""
    return bool(cfg.get("submissions_closed", False))


def submit(cfg: dict, app, pc, n: int, ids: list[int] | None = None, dry_run: bool = False) -> int:
    if submissions_closed(cfg) and not dry_run:
        print(json.dumps({"requests": 0, "submissions_closed": True,
                          "note": cfg.get("submissions_closed_note", "config.submissions_closed is true; nothing was sent")}))
        return 0
    system = system_prompt(cfg)
    sha = hashlib.sha256(system.encode("utf-8")).hexdigest()
    st = cfg["solver"]
    reqs, custom_ids, skipped = [], {}, []
    for qid in ordered_candidates(pc, app, cfg, ids):
        if len(reqs) >= n:
            break
        q = fetch_question(app, qid)
        reason = image_reason(q["latexcode"])
        if reason:
            upsert_status(pc, qid, status="skipped_image", note=reason, prompt_version=cfg["prompt_version"])
            log_event(pc, qid, "skip", reason)
            skipped.append(qid)
            continue
        row = get_status(pc, qid)
        attempt = (int(row["attempts"]) if row else 0) + 1
        feedback = None
        fb = q_dir(qid) / f"feedback_{attempt}.json"
        if row is not None and row["status"] == "retry" and fb.exists():
            feedback = read_json(fb)
        reqs.append(build_request(cfg, system, q, qid, attempt, feedback))
        custom_ids[f"q{qid}-a{attempt}"] = {"qid": qid, "attempt": attempt}
    summary = {"requests": len(reqs), "skipped_image": skipped, "model": st["model"], "effort": st["effort"]}
    if dry_run:
        if reqs:
            write_json(PIPELINE_DIR / "outputs" / "_dry_run_first_request.json", dict(reqs[0]))
            summary["first_request_written_to"] = (PIPELINE_DIR / "outputs" / "_dry_run_first_request.json").as_posix()
        summary["system_prompt_chars"] = len(system)
        print(json.dumps(summary))
        return 0
    if not reqs:
        print(json.dumps(summary))
        return 0
    client = get_client()
    batch = client.messages.batches.create(requests=reqs)
    seq = (pc.execute("SELECT MAX(seq) FROM api_batches").fetchone()[0] or 0) + 1
    pc.execute(
        "INSERT INTO api_batches (batch_id, seq, created_at, n, custom_ids, prompt_version, model, effort, system_sha256, status) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (batch.id, seq, now_iso(), len(reqs), json.dumps(custom_ids), cfg["prompt_version"], st["model"], st["effort"], sha, batch.processing_status),
    )
    pc.commit()
    for info in custom_ids.values():
        qid, attempt = info["qid"], info["attempt"]
        rec = {
            "status": "submitted", "batch_id": batch.id, "batch": seq, "pending_attempt": attempt,
            "prompt_version": cfg["prompt_version"],
            f"solver{min(attempt, 2)}_model": st["model"], f"solver{min(attempt, 2)}_effort": st["effort"],
        }
        upsert_status(pc, qid, **rec)
    log_event(pc, None, "submit", f"batch {seq} {batch.id}: {len(reqs)} requests, {len(skipped)} skipped (image)")
    write_progress(pc)
    summary.update({"batch_seq": seq, "batch_id": batch.id, "processing_status": batch.processing_status})
    print(json.dumps(summary))
    return len(reqs)


# --- collect ------------------------------------------------------------------


def _fail(qid: int, attempt: int, cfg: dict, pc, *, kind: str, errors: list[str] | None = None,
          reason: str = "", previous_text: str = "", mismatch: bool = False) -> str:
    d = q_dir(qid)
    note = (reason or "; ".join(errors or []))[:400]
    if attempt < int(cfg.get("max_attempts", 2)):
        fb = {"kind": kind, "errors": [e[:240] for e in (errors or [])[:12]], "reason": reason,
              "previous_text": previous_text if kind == "feedback" else "", "from_attempt": attempt}
        write_json(d / f"feedback_{attempt + 1}.json", fb)
        upsert_status(pc, qid, status="retry", note=f"attempt {attempt} rejected: {note}", answer_mismatch=int(mismatch))
        log_event(pc, qid, "collect", f"attempt {attempt} rejected ({kind}): {note}")
        return "retry"
    upsert_status(pc, qid, status="needs_human_review", note=f"attempt {attempt} rejected: {note}", answer_mismatch=int(mismatch))
    log_event(pc, qid, "collect", f"attempt {attempt} rejected, no attempts left: {note}")
    return "human_review"


def store_result(result, batch_id: str, cfg: dict, pc) -> str:
    """Download phase (the only part that needs the API key): persist one batch
    result under outputs/<qid>/ and mark the question `received`. API-level
    failures are settled here; everything else waits for `judge`."""
    qid, attempt = parse_custom_id(result.custom_id)
    row = get_status(pc, qid)
    if row is None or row["status"] != "submitted" or row["batch_id"] != batch_id:
        return "already_handled"
    d = q_dir(qid)
    rtype = result.result.type
    st = cfg["solver"]

    if rtype != "succeeded":
        if rtype == "errored":
            err = result.result.error.error
            etype, emsg = err.type, err.message
        else:
            etype, emsg = rtype, f"batch request {rtype}"
        log_event(pc, qid, "collect", f"attempt {attempt} {etype}: {emsg[:200]}")
        if etype == "invalid_request_error":
            upsert_status(pc, qid, status="needs_human_review", pending_attempt=None, note=f"API rejected the request: {emsg[:300]}")
            return "invalid_request"
        failures = int(row["api_failures"] or 0) + 1
        if failures >= int(cfg.get("max_api_failures", 3)):
            upsert_status(pc, qid, status="needs_human_review", pending_attempt=None, api_failures=failures, note=f"{failures} API failures, last: {emsg[:200]}")
            return "human_review"
        upsert_status(pc, qid, status="pending", pending_attempt=None, api_failures=failures, note=f"API failure {failures}: {emsg[:200]}")
        return "api_error"

    msg = result.result.message
    u = msg.usage
    if not pc.execute("SELECT 1 FROM usage WHERE question_id=? AND attempt=? AND batch_id=?", (qid, attempt, batch_id)).fetchone():
        pc.execute(
            "INSERT INTO usage (question_id, attempt, batch_id, model, effort, input_tokens, cache_write_tokens, cache_read_tokens, output_tokens, stop_reason, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (qid, attempt, batch_id, msg.model, st["effort"], u.input_tokens, u.cache_creation_input_tokens or 0,
             u.cache_read_input_tokens or 0, u.output_tokens, msg.stop_reason, now_iso()),
        )
        pc.commit()
    text = "".join(b.text for b in msg.content if b.type == "text")
    write_text(d / f"solver_{attempt}.tex", text)
    write_json(d / f"response_{attempt}.json", {
        "model": msg.model, "stop_reason": msg.stop_reason,
        "stop_details": msg.stop_details.model_dump() if msg.stop_details else None,
        "usage": u.model_dump(), "collected_at": now_iso(),
    })
    upsert_status(pc, qid, status="received", attempts=attempt, pending_attempt=None)
    return "received"


def judge_one(qid: int, cfg: dict, app, pc) -> str:
    """Judge phase (no API key): validate a downloaded reply, decide, assemble."""
    row = get_status(pc, qid)
    attempt = int(row["attempts"])
    d = q_dir(qid)
    resp = read_json(d / f"response_{attempt}.json")
    text = read_text(d / f"solver_{attempt}.tex")

    if resp.get("stop_reason") == "refusal":
        cat = (resp.get("stop_details") or {}).get("category")
        upsert_status(pc, qid, status="needs_human_review", note=f"model refused (category {cat})")
        log_event(pc, qid, "collect", f"attempt {attempt} refused ({cat})")
        return "refused"
    if resp.get("stop_reason") == "max_tokens":
        return _fail(qid, attempt, cfg, pc, kind="blind", reason="the reply was cut off at the output token limit")

    q = fetch_question(app, qid)
    # Only the source's own answer is a reference; one an earlier pipeline run filled in is not.
    own_answer = pipeline_wrote(pc, qid, "answer", q["answer"])
    stored = None if is_blank(q["answer"], cfg["empty_answer_sentinels"]) or own_answer else q["answer"]
    subject_mode = row["mode"] in ("solve", "aids")  # a non-math subject (subjects.py)
    if subject_mode:
        import subjects

        res = subjects.validate_reply(qid, text, cfg, q, row["mode"], stored)
    else:
        res = validate_solver_text(qid, text, cfg, stored)
    tiebreak_note = None
    if subject_mode and row["tiebreak"] and res["ok"] and res.get("answer_mismatch"):
        # The high-effort tie-break (owner 2026-11-07): agreeing with an earlier solve against the
        # stored answer, it is accepted and replaces that answer; agreeing with neither, a person decides.
        agree = subjects.earlier_agreement(qid, attempt, q, row["mode"])
        res["tiebreak_agrees_with_attempt"] = agree
        if agree is None:
            write_json(d / f"validate_{attempt}.json", res)
            upsert_status(pc, qid, status="needs_human_review", accepted_attempt=attempt, answer_mismatch=1,
                          note=f"tie-break: disagrees with the stored answer ({stored}) and with every earlier solve")
            log_event(pc, qid, "collect", f"attempt {attempt} (tie-break) agrees with neither the stored answer nor an earlier solve")
            return "tiebreak_split"
        tiebreak_note = f"tie-break agrees with attempt {agree}; replaces the stored answer ({stored})"
    write_json(d / f"validate_{attempt}.json", res)
    if not res["ok"]:
        return _fail(qid, attempt, cfg, pc, kind="feedback", errors=res["errors"], previous_text=text)
    if res.get("answer_mismatch") and tiebreak_note is None:
        return _fail(qid, attempt, cfg, pc, kind="blind",
                     reason=f"its final answer did not match the stored reference answer ({res.get('stored_answer')})", mismatch=True)
    if res.get("book_problem"):  # aids: the book's own solution looks wrong; the owner decides
        upsert_status(pc, qid, status="needs_human_review", accepted_attempt=attempt,
                      note=f"book check: {res['book_problem'][:300]}")
        log_event(pc, qid, "collect", f"attempt {attempt}: book check flagged: {res['book_problem'][:200]}")
        return "book_flagged"

    keep_hint = not is_blank(q["hints"]) and not pipeline_wrote(pc, qid, "hints", q["hints"])
    hint_status = "skipped" if keep_hint else ("ok" if res["hint_ok"] else "failed")
    note = None if res["hint_ok"] else "hint dropped: " + "; ".join(res["hint_errors"])[:300]
    if tiebreak_note:
        note = tiebreak_note + ("; " + note if note else "")
    # A subject question's flag says whether the accepted reply disagrees with the stored answer (an
    # accepted tie-break replaces it); math rows keep the flag of their history.
    extra = {"answer_mismatch": int(tiebreak_note is not None)} if subject_mode else {}
    upsert_status(pc, qid, status="passed", accepted_attempt=attempt, hint_status=hint_status, note=note, **extra)
    log_event(pc, qid, "collect", f"attempt {attempt} passed; hint {hint_status}")
    out = subjects.assemble_one(qid, cfg, app, pc) if subject_mode else assemble_one(qid, cfg, app, pc)
    return "passed" if out["ok"] else "assemble_failed"


def judge(cfg: dict, workers: int | None = None) -> Counter:
    """Judge every `received` question on a thread pool. Each worker owns its
    database connections; XeLaTeX / node run in per-call temp dirs."""
    pc0 = pipe_conn()
    ids = [r[0] for r in pc0.execute("SELECT question_id FROM status WHERE status='received' ORDER BY question_id")]
    pc0.close()
    # priority sources (config.sources order) first, everything else after, by id
    app0 = app_conn(cfg)
    src = {r[0]: r[1] for r in app0.execute("SELECT question_id, source FROM questions")}
    app0.close()
    rank = source_rank(cfg)
    ids.sort(key=lambda q: (rank.get(src.get(q), len(rank)), q))
    summary: Counter = Counter()
    if not ids:
        return summary
    workers = workers or int(cfg.get("judge_workers", 4))
    local = threading.local()

    def work(qid: int) -> str:
        if not hasattr(local, "pc"):
            local.pc = pipe_conn()
            local.app = app_conn(cfg)
        try:
            return judge_one(qid, cfg, local.app, local.pc)
        except Exception as e:  # keep the pool alive; the row is findable by its note
            try:
                upsert_status(local.pc, qid, status="needs_human_review", note="judge crashed: " + str(e)[:300])
                log_event(local.pc, qid, "judge", "crashed: " + str(e)[:300])
            except Exception:
                pass
            return "judge_crashed"

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, outcome in enumerate(ex.map(work, ids), 1):
            summary[outcome] += 1
            if i % 25 == 0 or i == len(ids):
                print(json.dumps({"judged": i, "of": len(ids), "elapsed_s": int(time.time() - t0), **summary}), flush=True)
    return summary


def _cost_of(cfg: dict, model: str, inp: int, cw: int, cr: int, out: int) -> float:
    p = (cfg.get("prices_usd_per_mtok") or {}).get(model)
    if not p:
        return 0.0
    disc = float(cfg.get("batch_discount", 0.5))
    return disc * (inp * p["input"] + cw * p["cache_write"] + cr * p["cache_read"] + out * p["output"]) / 1e6


def download_batch(b, mb, client, cfg: dict, pc) -> dict:
    """Fetch every result of an ended batch to disk (fast; needs the key) and
    mark the batch collected. A raw copy of the result lines goes to
    pipeline/raw/<batch_id>.jsonl as insurance."""
    expected = json.loads(b["custom_ids"])
    seen: set[str] = set()
    summary: Counter = Counter()
    raw_dir = PIPELINE_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with open(raw_dir / f"{b['batch_id']}.jsonl", "w", encoding="utf-8") as raw:
        for result in client.messages.batches.results(b["batch_id"]):
            raw.write(result.model_dump_json() + "\n")
            if result.custom_id not in expected:
                continue
            seen.add(result.custom_id)
            summary[store_result(result, b["batch_id"], cfg, pc)] += 1
    for cid, info in expected.items():  # defensive: a request with no result line
        if cid not in seen:
            upsert_status(pc, info["qid"], status="pending", pending_attempt=None, note="no result returned for the batch request")
            summary["no_result"] += 1
    tok = pc.execute(
        "SELECT COALESCE(SUM(input_tokens),0), COALESCE(SUM(cache_write_tokens),0), COALESCE(SUM(cache_read_tokens),0), COALESCE(SUM(output_tokens),0), MAX(model) FROM usage WHERE batch_id=?",
        (b["batch_id"],),
    ).fetchone()
    cost = _cost_of(cfg, tok[4] or cfg["solver"]["model"], tok[0], tok[1], tok[2], tok[3])
    s = dict(summary)
    s.update({"batch_seq": b["seq"], "batch_id": b["batch_id"], "n": b["n"], "tokens": {"input": tok[0], "cache_write": tok[1], "cache_read": tok[2], "output": tok[3]}, "usd": round(cost, 2)})
    pc.execute(
        "UPDATE api_batches SET status=?, ended_at=?, collected_at=?, summary_json=? WHERE batch_id=?",
        ("ended", mb.ended_at.isoformat() if mb.ended_at else None, now_iso(), json.dumps(s), b["batch_id"]),
    )
    pc.commit()
    line = (
        f"| {_dt.date.today().isoformat()} | api batch {b['seq']} ({b['batch_id']}) | n={b['n']} "
        f"| downloaded {summary['received']} | already {summary['already_handled']} "
        f"| human {summary['human_review'] + summary['invalid_request']} | api_err {summary['api_error'] + summary['no_result']} "
        f"| tokens in/cw/cr/out {tok[0]}/{tok[1]}/{tok[2]}/{tok[3]} | USD {cost:.2f} | {cfg['prompt_version']} {cfg['solver']['model']}/{cfg['solver']['effort']} |"
    )
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    log_event(pc, None, "collect", json.dumps(s))
    write_progress(pc)
    return s


def judge_round(cfg: dict, pc, workers: int | None = None) -> dict:
    """Judge everything received, then apply queued app-db writes."""
    summ = judge(cfg, workers)
    out = {"judged": dict(summ)}
    if summ:
        out["field_fills"] = apply_pending(cfg, pc)
        write_progress(pc)
    return out


def collect(cfg: dict, app, pc, wait: bool = False, download_only: bool = False) -> int:
    """Download every ended batch, then (unless download_only) judge what was
    received. Returns the number of batches still in flight."""
    client = get_client()
    while True:
        open_rows = pc.execute("SELECT * FROM api_batches WHERE collected_at IS NULL ORDER BY seq").fetchall()
        remaining = 0
        for b in open_rows:
            mb = client.messages.batches.retrieve(b["batch_id"])
            c = mb.request_counts
            if mb.processing_status != "ended":
                remaining += 1
                print(json.dumps({"batch_seq": b["seq"], "batch_id": b["batch_id"], "status": mb.processing_status,
                                  "processing": c.processing, "succeeded": c.succeeded, "errored": c.errored,
                                  "expired": c.expired, "canceled": c.canceled}), flush=True)
                continue
            print(json.dumps(download_batch(b, mb, client, cfg, pc)), flush=True)
        if not download_only:
            r = judge_round(cfg, pc)
            if r["judged"]:
                print(json.dumps(r), flush=True)
        if not open_rows:
            print("(no batches in flight)")
            return 0
        if remaining == 0 or not wait:
            return remaining
        time.sleep(int(cfg.get("poll_seconds", 120)))


# --- loop ---------------------------------------------------------------------


# Replies from run_sub.py (batch_id 'sub:...') come from the subscription and cost no API credit.
API_USAGE = "batch_id NOT LIKE 'sub:%'"


def total_cost(cfg: dict, pc) -> float:
    total = 0.0
    for r in pc.execute(f"SELECT model, SUM(input_tokens), SUM(cache_write_tokens), SUM(cache_read_tokens), SUM(output_tokens) FROM usage WHERE {API_USAGE} GROUP BY model"):
        total += _cost_of(cfg, r[0], r[1] or 0, r[2] or 0, r[3] or 0, r[4] or 0)
    return total


def loop(cfg: dict, app, pc, n: int, max_batches: int | None, budget: float | None, download_only: bool = False) -> None:
    """Keep up to max_inflight_batches batches in flight. With download_only
    the loop never judges; run `judge --watch` in a second window for that."""
    import anthropic

    submitted = 0
    poll = int(cfg.get("poll_seconds", 120))
    max_inflight = int(cfg.get("max_inflight_batches", 1))
    min_batch = int(cfg.get("min_batch_size", 1))
    submit_blocked = submissions_closed(cfg)
    if submit_blocked:
        print("config.submissions_closed is true: the loop only collects in-flight batches, nothing is submitted", flush=True)
    while True:
        inflight = collect(cfg, app, pc, wait=False, download_only=download_only)
        spend = total_cost(cfg, pc)
        stop_submitting = submit_blocked or (budget is not None and spend >= budget) or (max_batches is not None and submitted >= max_batches)
        if stop_submitting:
            print(f"not submitting more: spend {spend:.2f} USD, batches submitted this run {submitted}", flush=True)
        made_any = False
        while not stop_submitting and inflight < max_inflight:
            avail = len(ordered_candidates(pc, app, cfg))
            if avail == 0 or (avail < min_batch and inflight > 0):
                break
            try:
                made = submit(cfg, app, pc, n)
            except anthropic.APIStatusError as e:
                print(f"submit refused by the API ({e.status_code}): {getattr(e, 'message', e)}; collecting only from now on", flush=True)
                submit_blocked = True
                break
            if made == 0:
                break
            made_any = True
            submitted += 1
            inflight += 1
        pending_judge = pc.execute("SELECT COUNT(*) FROM status WHERE status='received'").fetchone()[0]
        if inflight == 0 and not made_any and pending_judge == 0:
            if stop_submitting:
                return
            if not ordered_candidates(pc, app, cfg):
                print("nothing left to submit; run finished")
                return
        time.sleep(poll)


# --- status / cost / cancel / reset -------------------------------------------


def status(cfg: dict, app, pc) -> None:
    rows = {r["question_id"]: r for r in pc.execute("SELECT * FROM status")}
    per: dict[str, Counter] = {}
    for qid, src in target_questions(app, cfg):
        c = per.setdefault(src, Counter())
        c["total"] += 1
        r = rows.get(qid)
        if r is None:
            c["todo"] += 1
        elif is_done(r):
            c["human" if r["status"] == "needs_human_review" else "no_img" if r["status"] in ("skipped_image", "missing_image") else "done"] += 1
        elif r["status"] == "submitted":
            c["in_flight"] += 1
        elif r["status"] == "received":
            c["judge"] += 1
        elif r["status"] == "retry":
            c["retry"] += 1
        else:
            c["todo"] += 1
    print(f"prompt_version {cfg['prompt_version']} | {cfg['solver']['model']} / {cfg['solver']['effort']} | app_db_writes {cfg['app_db_writes']} | spend so far {total_cost(cfg, pc):.2f} USD")
    print(f"{'#':>2} {'source':62} {'total':>5} {'done':>5} {'human':>5} {'no_img':>6} {'flight':>6} {'judge':>5} {'retry':>5} {'todo':>5}")
    tot = Counter()
    for i, src in enumerate(cfg["sources"], 1):
        c = per.get(src, Counter())
        tot.update(c)
        print(f"{i:>2} {src[:62]:62} {c['total']:>5} {c['done']:>5} {c['human']:>5} {c['no_img']:>6} {c['in_flight']:>6} {c['judge']:>5} {c['retry']:>5} {c['todo']:>5}")
    print(f"{'':>2} {'TOTAL':62} {tot['total']:>5} {tot['done']:>5} {tot['human']:>5} {tot['no_img']:>6} {tot['in_flight']:>6} {tot['judge']:>5} {tot['retry']:>5} {tot['todo']:>5}")
    for b in pc.execute("SELECT seq, batch_id, n, created_at FROM api_batches WHERE collected_at IS NULL ORDER BY seq"):
        print(f"in flight: batch {b[0]} {b[1]} n={b[2]} created {b[3]}")
    write_progress(pc)


def cost(cfg: dict, app, pc) -> None:
    print("prices: config.prices_usd_per_mtok x batch_discount (verify against the pricing page)")
    total = 0.0
    nq = 0
    for r in pc.execute(f"SELECT model, COUNT(*), SUM(input_tokens), SUM(cache_write_tokens), SUM(cache_read_tokens), SUM(output_tokens) FROM usage WHERE {API_USAGE} GROUP BY model"):
        c = _cost_of(cfg, r[0], r[2] or 0, r[3] or 0, r[4] or 0, r[5] or 0)
        total += c
        nq += r[1]
        print(json.dumps({"model": r[0], "replies": r[1], "input": r[2], "cache_write": r[3], "cache_read": r[4], "output": r[5], "usd": round(c, 2)}))
    sub = pc.execute(f"SELECT COUNT(*), SUM(output_tokens) FROM usage WHERE NOT ({API_USAGE})").fetchone()
    if sub[0]:
        print(json.dumps({"subscription_replies": sub[0], "output": sub[1], "usd": 0}))
    rows = {r["question_id"]: r for r in pc.execute("SELECT * FROM status")}
    remaining = sum(1 for qid, _ in target_questions(app, cfg) if not is_done(rows.get(qid)))
    solved = sum(1 for r in rows.values() if r["status"] == "passed")
    line = {"usd_total": round(total, 2), "replies": nq, "passed": solved, "remaining_questions": remaining}
    if solved:
        per_q = total / solved
        line["usd_per_passed_question"] = round(per_q, 4)
        line["usd_projected_for_remaining"] = round(per_q * remaining, 2)
    print(json.dumps(line))


def cancel(cfg: dict, pc) -> None:
    client = get_client()
    for b in pc.execute("SELECT batch_id, seq FROM api_batches WHERE collected_at IS NULL"):
        r = client.messages.batches.cancel(b[0])
        print(f"batch {b[1]} {b[0]}: {r.processing_status}")
    print("results already produced are kept; run collect to fetch them (canceled requests go back to pending)")


def reset(pc, force: bool) -> None:
    inflight = pc.execute("SELECT COUNT(*) FROM api_batches WHERE collected_at IS NULL").fetchone()[0]
    if inflight and not force:
        raise SystemExit(f"{inflight} batch(es) in flight; collect or cancel them first (or pass --force)")
    pc.close()
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = PIPELINE_DIR / "archive" / stamp
    dest.mkdir(parents=True, exist_ok=True)
    moved = []
    for p in (PIPELINE_DB, OUTPUTS_DIR, PROGRESS_JSON, PIPELINE_DIR / "current_batch.json", PIPELINE_DIR / "meta.json"):
        if p.exists():
            shutil.move(str(p), str(dest / p.name))
            moved.append(p.name)
    for extra in PIPELINE_DIR.glob("pipeline.db-*"):
        shutil.move(str(extra), str(dest / extra.name))
        moved.append(extra.name)
    with open(RUN_LOG, "a", encoding="utf-8") as f:
        f.write(f"- {now_iso()}: reset; previous state archived to pipeline/archive/{stamp} ({', '.join(moved)})\n")
    print(f"archived {moved} to {dest.as_posix()}")


def backup_app_db(cfg: dict, label: str) -> None:
    """A copy of the app database next to it before the judge writes to it, as import does."""
    import sqlite3

    from common import app_db_path

    path = app_db_path(cfg)
    dest = path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}-{label}")
    src, out = sqlite3.connect(path), sqlite3.connect(dest)
    src.backup(out)
    out.close()
    src.close()
    print(json.dumps({"app_db_backup": dest.name}), flush=True)


# --- main ---------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("status")
    p = sub.add_parser("queue")
    p.add_argument("--n", type=int, default=20)
    p = sub.add_parser("submit")
    p.add_argument("--n", type=int)
    p.add_argument("--ids")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("collect")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--download-only", action="store_true")
    p = sub.add_parser("judge")
    p.add_argument("--watch", action="store_true")
    p.add_argument("--workers", type=int)
    p = sub.add_parser("loop")
    p.add_argument("--n", type=int)
    p.add_argument("--max-batches", type=int)
    p.add_argument("--budget-usd", type=float)
    p.add_argument("--download-only", action="store_true")
    sub.add_parser("cost")
    sub.add_parser("cancel")
    p = sub.add_parser("reset")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--force", action="store_true")
    a = ap.parse_args()

    cfg = load_config()
    pc = pipe_conn()
    if cfg.get("judge_elsewhere") and (a.cmd == "judge" or (a.cmd in ("collect", "loop") and not a.download_only)):
        # Owner (2026-11-07): a small round (at most judge_here_max replies) is judged here.
        waiting = pc.execute("SELECT COUNT(*) FROM status WHERE status='received'").fetchone()[0]
        if a.cmd != "judge" or a.watch or waiting > int(cfg.get("judge_here_max") or 0):
            raise SystemExit(f"judging runs on another machine (config judge_elsewhere; {waiting} waiting, "
                             f"judge_here_max {cfg.get('judge_here_max') or 0}): remote_judge.py export here, run there, "
                             "import here; collect/loop need --download-only")
        backup_app_db(cfg, "pre-judge")
    if a.cmd == "check":
        check()
        return
    if a.cmd == "reset":
        if not a.yes:
            raise SystemExit("reset archives pipeline.db and outputs/; pass --yes to confirm")
        reset(pc, a.force)
        return
    app = app_conn(cfg)
    if a.cmd == "status":
        status(cfg, app, pc)
    elif a.cmd == "queue":
        rank = source_rank(cfg)
        for qid in ordered_candidates(pc, app, cfg)[: a.n]:
            q = fetch_question(app, qid)
            r = get_status(pc, qid)
            img = image_reason(q["latexcode"])
            print(json.dumps({"question_id": qid, "source": q["source"], "priority": rank[q["source"]] + 1,
                              "status": r["status"] if r else "new", "will_skip": img}))
    elif a.cmd == "submit":
        ids = [int(x) for x in a.ids.split(",") if x.strip()] if a.ids else None
        n = a.n or (len(ids) if ids else int(cfg["api_batch_size"]))
        submit(cfg, app, pc, n, ids, a.dry_run)
    elif a.cmd == "collect":
        collect(cfg, app, pc, a.wait, a.download_only)
    elif a.cmd == "judge":
        while True:
            r = judge_round(cfg, pc, a.workers)
            print(json.dumps({"at": now_iso(), **r}), flush=True)
            if not a.watch:
                break
            more = pc.execute(
                "SELECT (SELECT COUNT(*) FROM api_batches WHERE collected_at IS NULL) + "
                "(SELECT COUNT(*) FROM status WHERE status IN ('submitted','received','retry'))"
            ).fetchone()[0]
            if not more:
                print("nothing left to judge and nothing in flight; done")
                break
            time.sleep(int(cfg.get("judge_poll_seconds", 60)))
    elif a.cmd == "loop":
        loop(cfg, app, pc, a.n or int(cfg["api_batch_size"]), a.max_batches, a.budget_usd, a.download_only)
    elif a.cmd == "cost":
        cost(cfg, app, pc)
    elif a.cmd == "cancel":
        cancel(cfg, pc)


if __name__ == "__main__":
    main()
