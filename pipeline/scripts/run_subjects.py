"""Non-math subjects on the Claude subscription: full solutions and study aids.

The questions of every subject that has a profile in config.subjects.profiles:
  solve  their own solution is missing or a Gemini one (config.subjects.solve_kinds), as in the
         math run: a new solution, answer key, hint and takeaways.
  aids   they carry the book's own solution (config.subjects.aids_kinds): an answer key, a hint
         and takeaways built on it; the book's solution stays.
Transport, request checks and storage are run_sub.py's (one fresh `claude -p` per question,
replies stored as `received`); the prompts are subjects.py's, one system prompt per subject and
mode. `run.py judge` (here or through remote_judge.py) validates, assembles and writes them.

Usage (from the repo root):
  python pipeline/scripts/run_subjects.py status
  python pipeline/scripts/run_subjects.py queue    [--n 20] [--ids 1,2,3]
  python pipeline/scripts/run_subjects.py prompt   --subject NAME --mode solve|aids   # print the system prompt
  python pipeline/scripts/run_subjects.py verify                                     # free request check
  python pipeline/scripts/run_subjects.py solve    [--n N] [--ids 1,2,3] [--workers W] [--wait-on-limit]
  python pipeline/scripts/run_subjects.py tiebreak [--list] [--workers W]   # third solve, high effort, after two disagreed with the stored answer
  python pipeline/scripts/run_subjects.py precheck [--ids ...]   # structure and LaTeX rules only (no XeLaTeX)
  python pipeline/scripts/run_subjects.py review   [--ids ...]   # local HTML page of the replies
"""

from __future__ import annotations

import argparse
import html
import json
import os
import random
import sys
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_sub  # noqa: E402
import subjects  # noqa: E402
from common import (  # noqa: E402
    OUTPUTS_DIR,
    PIPELINE_DIR,
    app_conn,
    fetch_question,
    get_status,
    is_blank,
    is_done,
    load_config,
    log_event,
    now_iso,
    q_dir,
    read_json,
    read_text,
    upsert_status,
    write_progress,
    write_text,
)

LOCK = PIPELINE_DIR / "run_subjects.lock"
REVIEW_DIR = OUTPUTS_DIR / "_review"  # git-ignored: the page quotes question text


def scfg(cfg: dict) -> dict:
    return subjects.subj_cfg(cfg)


def call_cfg(cfg: dict) -> dict:
    """The config run_sub's transport and storage read: the subjects' model and prompt version."""
    s = scfg(cfg)
    return dict(cfg, prompt_version=s["prompt_version"], solver=dict(cfg["solver"], model=s["model"]))


def effort_for(cfg: dict, mode: str) -> str:
    s = scfg(cfg)
    return s.get("aids_effort") if mode == "aids" and s.get("aids_effort") else s["effort"]


# --- scope ----------------------------------------------------------------------------


def scope_rows(cfg: dict, app, ours: set[int] = frozenset()) -> list[dict]:
    """Every question of a profiled subject with its mode: solve questions first (they have no
    worked solution of their own yet), then aids, each in subject order (config order) and
    question id. A solve question that already has a generated solution is left out unless
    it is in `ours` (it got that solution from this run)."""
    s = scfg(cfg)
    order = {name: i for i, name in enumerate(s["profiles"])}
    solve_kinds, aids_kinds = set(s.get("solve_kinds") or ()), set(s.get("aids_kinds") or ())
    out = []
    for r in app.execute("SELECT question_id, source, topic, branch, subtopic, type, latexcode, solution, "
                         "generated_solution FROM questions ORDER BY question_id"):
        subject = subjects.subject_of(dict(r))
        if subject not in order:
            continue
        kind = run_sub.solution_kind(r["solution"])
        mode = "solve" if kind in solve_kinds else "aids" if kind in aids_kinds else None
        if mode is None or (mode == "solve" and not is_blank(r["generated_solution"]) and r["question_id"] not in ours):
            continue
        out.append({"id": r["question_id"], "source": r["source"], "subject": subject, "mode": mode, "kind": kind,
                    "type": r["type"], "figure": subjects.figure_reason(r["latexcode"])})
    out.sort(key=lambda x: (x["mode"] != "solve", order[x["subject"]], x["id"]))
    return out


def candidates(cfg: dict, app, pc, ids: list[int] | None = None) -> list[dict]:
    """Unfinished questions in order: retries first, then the rest. A status row written by the
    math run (mode NULL) is never touched."""
    status = {r["question_id"]: r for r in pc.execute("SELECT * FROM status")}
    rows = scope_rows(cfg, app, {q for q, r in status.items() if r["mode"] is not None})
    if ids:
        want = set(ids)
        rows = [x for x in rows if x["id"] in want]
        missing = want - {x["id"] for x in rows}
        if missing:
            raise SystemExit(f"not in the subjects' scope: {sorted(missing)}")
    retry, fresh = [], []
    for x in rows:
        r = status.get(x["id"])
        if r is not None and (r["mode"] is None or r["status"] in ("submitted", "received", "skipped_image")
                              or is_done(r)):
            continue
        (retry if r is not None and r["status"] == "retry" else fresh).append(x)
    return retry + fresh


def plan_attempt(pc, qid: int) -> tuple[int, dict | None]:
    row = get_status(pc, qid)
    attempt = (int(row["attempts"]) if row else 0) + 1
    fb = q_dir(qid) / f"feedback_{attempt}.json"
    return attempt, (read_json(fb) if (row is not None and row["status"] == "retry" and fb.exists()) else None)


def system_file(cfg: dict, mode: str, subject: str) -> tuple[Path, str]:
    text = subjects.system_prompt(cfg, mode, subject)
    run_sub.SUB_CWD.mkdir(parents=True, exist_ok=True)
    path = run_sub.SUB_CWD.parent / f".amplify-subject-{mode}-{scfg(cfg)['profiles'][subject]}.txt"
    path.write_bytes(text.encode("utf-8"))
    return path, text


# --- verify ---------------------------------------------------------------------------


def verify(cfg: dict, app, pc, quiet: bool = False) -> dict:
    """run_sub's request check on one question of each mode with the subjects' prompts: the
    request must pass every check and Claude Code's wrapping must be one the owner accepted."""
    ccfg = call_cfg(cfg)
    picks: dict[str, dict] = {}
    for x in candidates(cfg, app, pc) or scope_rows(cfg, app):
        if not x["figure"]:
            picks.setdefault(x["mode"], x)
    if not picks:
        raise SystemExit("no question to verify with")
    accepted = run_sub.accepted_fingerprints(pc)
    reports = []
    for mode, x in picks.items():
        q = fetch_question(app, x["id"])
        path, system = system_file(cfg, mode, x["subject"])
        text = subjects.user_text(q, mode, None, cfg)
        effort = effort_for(cfg, mode)
        captured, out = run_sub.capture_request(ccfg, path, text, effort)
        rep = run_sub.check_request(ccfg, system, text, effort, captured, out, set())
        rep.update(question_id=x["id"], mode=mode, effort=effort,
                   claude_code_version=rep["init"].get("claude_code_version"),
                   accepted=rep["fingerprint"] in accepted)
        reports.append(rep)
    ok = all(r["ok"] and r["accepted"] for r in reports)
    if not quiet:
        for r in reports:
            print(f"question {r['question_id']} ({r['mode']}, {r['effort']} effort): "
                  f"{'ok' if r['ok'] else 'FAILED'}; wrapping {(r['fingerprint'] or '')[:16]} "
                  f"{'accepted' if r['accepted'] else 'NOT accepted (run_sub.py verify --accept after review)'}")
            for name, good, detail in r["checks"]:
                if not good:
                    print(f"  FAIL {name}  [{detail}]")
    return {"ok": ok, "claude_code_version": reports[0]["claude_code_version"], "reports": reports}


# --- solve ----------------------------------------------------------------------------


def tiebreak_rows(cfg: dict, app, pc, ids: list[int] | None = None) -> list[dict]:
    """Solve questions whose solves disagreed with the stored answer and that have no tie-break yet:
    those sent to human review for it, and second attempts received but not judged whose reply is
    well formed and still disagrees (checked here without the PDF and web compiles)."""
    status = {r["question_id"]: r for r in pc.execute("SELECT * FROM status WHERE mode='solve' AND tiebreak=0")}
    rows = {x["id"]: x for x in scope_rows(cfg, app, set(status))}
    out = []
    for qid, r in sorted(status.items()):
        if (ids and qid not in ids) or qid not in rows or int(r["attempts"] or 0) < 2:
            continue
        if r["status"] == "needs_human_review" and r["answer_mismatch"]:
            out.append(rows[qid])
        elif r["status"] == "received":
            q = fetch_question(app, qid)
            stored = None if is_blank(q["answer"], cfg["empty_answer_sentinels"]) else q["answer"]
            res = subjects.validate_reply(qid, read_text(q_dir(qid) / f"solver_{r['attempts']}.tex"), cfg, q, "solve",
                                          stored, compile_checks=False)
            if res["ok"] and res.get("answer_mismatch"):
                out.append(rows[qid])
    return out


def solve(cfg: dict, app, pc, n: int | None, ids: list[int] | None, workers: int | None, wait_on_limit: bool,
          force_unlock: bool, tiebreak: bool = False) -> None:
    """Send the unfinished questions; with tiebreak, a third solve at config.subjects.tiebreak_effort
    for the questions tiebreak_rows names (the stored answer is never sent)."""
    pre = verify(cfg, app, pc, quiet=True)
    if not pre["ok"]:
        raise SystemExit("the request check failed or the wrapping is not accepted; run `run_subjects.py verify`")
    version = pre["claude_code_version"]
    ccfg = call_cfg(cfg)
    if LOCK.exists() and not force_unlock:
        raise SystemExit(f"{LOCK.as_posix()} exists: another solve may be running (pid {LOCK.read_text().strip()})")
    LOCK.write_text(str(os.getpid()))
    queue = tiebreak_rows(cfg, app, pc, ids) if tiebreak else candidates(cfg, app, pc, ids)
    if n is not None:
        queue = queue[:n]
    limit = workers or int(scfg(cfg).get("workers", 4))
    files: dict[tuple[str, str], Path] = {}
    print(json.dumps({"questions": len(queue), "workers": limit, "claude_code_version": version,
                      "model": ccfg["solver"]["model"], "modes": dict(Counter(x["mode"] for x in queue)),
                      "prompt_version": ccfg["prompt_version"], **({"tiebreak": True} if tiebreak else {})}), flush=True)
    summary: Counter = Counter()
    t0 = time.time()
    stop_reason = None
    paused_until = None  # the reset time of the limit that stopped the run (kept until the wait)
    try:
        with ThreadPoolExecutor(max_workers=limit) as ex:
            running: dict = {}
            while queue or running:
                while queue and stop_reason is None and len(running) < limit:
                    x = queue.pop(0)
                    qid, mode = x["id"], x["mode"]
                    if x["figure"]:  # a figure the question does not carry: not sent
                        upsert_status(pc, qid, status="skipped_image", note=x["figure"], mode=mode, subject=x["subject"],
                                      prompt_version=ccfg["prompt_version"])
                        log_event(pc, qid, "skip", x["figure"])
                        summary["skipped_image"] += 1
                        continue
                    if (mode, x["subject"]) not in files:
                        files[(mode, x["subject"])] = system_file(cfg, mode, x["subject"])[0]
                    q = fetch_question(app, qid)
                    attempt, feedback = plan_attempt(pc, qid)
                    effort = scfg(cfg)["tiebreak_effort"] if tiebreak else effort_for(cfg, mode)
                    upsert_status(pc, qid, mode=mode, subject=x["subject"], **({"tiebreak": 1} if tiebreak else {}))
                    fut = ex.submit(run_sub.call_claude, ccfg, files[(mode, x["subject"])],
                                    subjects.user_text(q, mode, feedback, cfg), effort)
                    running[fut] = (qid, attempt, effort, mode)
                if not running:
                    break
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for fut in done:
                    qid, attempt, effort, mode = running.pop(fut)
                    out = fut.result()
                    info = run_sub.interpret(out, ccfg, version)
                    kind = info["kind"]
                    raw = run_sub.save_failure(qid, attempt, out, info) if kind in ("error", "stop", "cut") else None
                    if kind in ("ok", "cut"):
                        run_sub.store(pc, ccfg, qid, attempt, effort, info, out.get("seconds", 0))
                        summary["received" if kind == "ok" else info["result"]["stop_reason"]] += 1
                    elif kind == "limited":
                        queue.insert(0, next(x for x in scope_rows(cfg, app) if x["id"] == qid))
                        summary["limited"] += 1
                        if stop_reason is None:
                            stop_reason = "usage limit: " + info["why"]
                            paused_until = info.get("resets_at")
                    elif kind == "stop":
                        queue.insert(0, next(x for x in scope_rows(cfg, app) if x["id"] == qid))
                        stop_reason = info["why"]
                        wait_on_limit = False
                    else:
                        summary[run_sub.api_failure(pc, ccfg, qid, attempt, info["why"])] += 1
                    print(json.dumps({"question_id": qid, "mode": mode, "attempt": attempt, "outcome": kind,
                                      "seconds": out.get("seconds"), **({"why": info["why"]} if kind != "ok" else {}),
                                      **({"raw": raw} if raw else {}), "elapsed_min": round((time.time() - t0) / 60, 1),
                                      **summary}), flush=True)
                if stop_reason and not running:
                    if wait_on_limit and stop_reason.startswith("usage limit") and queue:
                        until = float(paused_until) if paused_until else time.time() + 900
                        secs = max(60, min(int(until - time.time()) + 120, 1020))  # short polls catch a /login switch
                        print(f"{stop_reason}; waiting {secs // 60} min, then continuing", flush=True)
                        time.sleep(secs)
                        stop_reason = paused_until = None
                        continue
                    break
    finally:
        LOCK.unlink(missing_ok=True)
        write_progress(pc)
    print(json.dumps({"finished": now_iso(), "stopped": stop_reason, "left_in_this_run": len(queue), **summary,
                      "next": "run.py judge (on the judging machine: remote_judge.py export, run, import)"}), flush=True)


# --- status / queue / pilot -----------------------------------------------------------


def status(cfg: dict, app, pc) -> None:
    st = {r["question_id"]: r for r in pc.execute("SELECT * FROM status WHERE mode IS NOT NULL")}
    per: dict[tuple[str, str], Counter] = {}
    for x in scope_rows(cfg, app, set(st)):
        c = per.setdefault((x["subject"], x["mode"]), Counter())
        c["total"] += 1
        r = st.get(x["id"])
        if x["figure"] and r is None:
            c["figure"] += 1
        elif r is None:
            c["todo"] += 1
        else:
            c[r["status"]] += 1
    cols = ("total", "todo", "figure", "received", "retry", "passed", "needs_human_review", "skipped_image")
    print(f"{'subject':42} {'mode':5} " + " ".join(f"{c[:8]:>8}" for c in cols))
    for (s, m), c in per.items():
        print(f"{s[:42]:42} {m:5} " + " ".join(f"{c[k]:>8}" for k in cols))


def pilot_ids(cfg: dict, app, subject: str, k_solve: int, k_aids: int, seed: int = 7) -> list[int]:
    """A spread over question types for a pilot: solve questions by type (multiple choice,
    descriptive, numerical, several parts), including some with a stored source answer, and
    a few aids questions."""
    rows = [x for x in scope_rows(cfg, app) if x["subject"] == subject and not x["figure"]]
    rng = random.Random(seed)
    tex = {x["id"]: fetch_question(app, x["id"]) for x in rows}

    def multi(x) -> bool:
        return x["type"] != "objective" and "\\begin{enumerate}" in tex[x["id"]]["latexcode"]

    def has_answer(x) -> bool:
        return not is_blank(tex[x["id"]]["answer"], cfg["empty_answer_sentinels"])

    solve = [x for x in rows if x["mode"] == "solve"]
    groups = [
        [x for x in solve if x["type"] == "objective"],
        [x for x in solve if x["type"] == "explanation/reasoning" and not multi(x)],
        [x for x in solve if x["type"] == "numerical" and not multi(x) and has_answer(x)],
        [x for x in solve if x["type"] == "numerical" and not multi(x) and not has_answer(x)],
        [x for x in solve if multi(x)],
        [x for x in solve if x["kind"] == "missing"],
    ]
    share = [0.25, 0.25, 0.15, 0.1, 0.2, 0.05]
    picked: list[int] = []
    for g, f in zip(groups, share):
        pool = [x["id"] for x in g if x["id"] not in picked]
        picked += rng.sample(pool, min(len(pool), max(1, round(k_solve * f))))
    aids = [x["id"] for x in rows if x["mode"] == "aids"]
    picked += rng.sample(aids, min(len(aids), k_aids))
    return sorted(set(picked))


# --- precheck / review ----------------------------------------------------------------


def latest_reply(qid: int) -> tuple[int, str] | None:
    d = OUTPUTS_DIR / str(qid)
    tries = sorted(d.glob("solver_*.tex"), key=lambda p: int(p.stem.split("_")[1])) if d.exists() else []
    return (int(tries[-1].stem.split("_")[1]), read_text(tries[-1])) if tries else None


def reviewed_ids(pc, ids: list[int] | None) -> list[int]:
    if ids:
        return ids
    return [r[0] for r in pc.execute("SELECT question_id FROM status WHERE mode IS NOT NULL ORDER BY question_id")]


def precheck(cfg: dict, app, pc, ids: list[int] | None) -> dict[int, dict]:
    """subjects.validate_reply without the PDF and web compiles (those run on the judging
    machine): structure, answer key, LaTeX rules, lengths, hint leaks, the stored answer."""
    out: dict[int, dict] = {}
    for qid in reviewed_ids(pc, ids):
        row = get_status(pc, qid)
        got = latest_reply(qid)
        if row is None or got is None or row["mode"] is None:
            continue
        q = fetch_question(app, qid)
        stored = None if is_blank(q["answer"], cfg["empty_answer_sentinels"]) else q["answer"]
        res = subjects.validate_reply(qid, got[1], cfg, q, row["mode"], stored, compile_checks=False)
        res["attempt"] = got[0]
        out[qid] = res
        print(json.dumps({"question_id": qid, "mode": row["mode"], "ok": res["ok"], "hint_ok": res["hint_ok"],
                          "mismatch": res.get("mismatch"), "book_problem": res.get("book_problem"),
                          "errors": res["errors"][:4], "hint_errors": res["hint_errors"][:3]}, ensure_ascii=False))
    print(json.dumps({"prechecked": len(out), "ok": sum(r["ok"] for r in out.values()),
                      "hint_ok": sum(r["hint_ok"] for r in out.values()),
                      "mismatch": sum(bool(r.get("mismatch")) for r in out.values()),
                      "book_flagged": sum(bool(r.get("book_problem")) for r in out.values())}))
    return out


PAGE_HEAD = """<!doctype html><html><head><meta charset="utf-8"><title>Subject pilot review</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>
body{font:15px/1.55 system-ui,sans-serif;max-width:980px;margin:0 auto;padding:16px;background:#fafafa;color:#222}
section{background:#fff;border:1px solid #ddd;border-radius:8px;padding:14px 18px;margin:18px 0}
h2{font-size:17px;margin:0 0 6px} h3{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:#666;margin:16px 0 4px}
.meta{color:#666;font-size:13px} .bad{color:#b00020} .ok{color:#137333} pre{white-space:pre-wrap;font-size:13px;background:#f4f4f4;padding:8px;border-radius:6px}
.book{border-left:3px solid #aaa;padding-left:10px;color:#333} nav a{margin-right:8px}
</style></head><body>"""
PAGE_TAIL = """<script>
document.addEventListener("DOMContentLoaded",()=>renderMathInElement(document.body,{delimiters:[
{left:"\\\\[",right:"\\\\]",display:true},{left:"\\\\(",right:"\\\\)",display:false},
{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}],throwOnError:false}));
</script></body></html>"""


def tex_html(s: str | None) -> str:
    """Rough LaTeX-to-HTML for reading: text commands and lists converted, math left to KaTeX."""
    import re

    if not s:
        return "<i>(none)</i>"
    t = html.escape(s, quote=False)
    t = re.sub(r"\\textbf\{([^{}]*)\}", r"<b>\1</b>", t)
    t = re.sub(r"\\(?:textit|emph)\{([^{}]*)\}", r"<i>\1</i>", t)
    t = re.sub(r"\\begin\{itemize\}", "<ul>", t)
    t = re.sub(r"\\end\{itemize\}", "</ul>", t)
    t = re.sub(r"\\begin\{enumerate\}(\[[^\]]*\])?", "<ol>", t)
    t = re.sub(r"\\end\{enumerate\}", "</ol>", t)
    t = re.sub(r"\\item\s*", "<li>", t)
    t = re.sub(r"\\(?:medskip|noindent|hfill|smallskip|bigskip)\b", "", t)
    t = re.sub(r"\n\s*\n", "</p><p>", t)
    return f"<p>{t}</p>"


def review(cfg: dict, app, pc, ids: list[int] | None, name: str) -> Path:
    checks = precheck(cfg, app, pc, ids)
    blocks = []
    for qid, res in checks.items():
        row = get_status(pc, qid)
        q = fetch_question(app, qid)
        parts, _ = subjects.parse_reply(read_text(q_dir(qid) / f"solver_{res['attempt']}.tex"), row["mode"])
        verdict = (f"<span class=ok>checks pass</span>" if res["ok"] else
                   "<span class=bad>checks fail: " + html.escape("; ".join(res["errors"])[:600]) + "</span>")
        extra = []
        if res.get("mismatch"):
            extra.append(f"<span class=bad>differs from the stored answer: {html.escape(res['mismatch'])}</span>")
        if res.get("book_problem"):
            extra.append(f"<span class=bad>book check: {html.escape(res['book_problem'])}</span>")
        if res["hint_errors"]:
            extra.append("<span class=bad>hint: " + html.escape("; ".join(res["hint_errors"])) + "</span>")
        resp = read_json(q_dir(qid) / f"response_{res['attempt']}.json")
        out_tok = (resp.get("usage") or {}).get("output_tokens")
        b = [f"<section id=q{qid}><h2>{qid} &middot; {html.escape(row['mode'])} &middot; {html.escape(q['type'] or '')}</h2>",
             f"<div class=meta>{html.escape(q['source'] or '')} &middot; {html.escape(q['topic'])} / {html.escape(q['branch'])} / "
             f"{html.escape(q['subtopic'])} &middot; attempt {res['attempt']} &middot; {out_tok} output tokens</div>",
             f"<div>{verdict}</div>", *[f"<div>{e}</div>" for e in extra],
             "<h3>Question</h3>", tex_html(q["latexcode"])]
        if not is_blank(q["answer"], cfg["empty_answer_sentinels"]):
            b += ["<h3>Stored answer (source)</h3>", tex_html(q["answer"])]
        if parts:
            if row["mode"] == "aids":
                b += ["<h3>Book solution (kept as is)</h3>", f"<div class=book>{tex_html(q['solution'])}</div>",
                      "<h3>Book check</h3>", html.escape(parts["book_check"])]
            else:
                b += ["<h3>Solution</h3>", tex_html(parts["solution"]),
                      "<h3>" + html.escape(subjects.load_profile(cfg, row["subject"])["notes_title"]) + "</h3>",
                      tex_html(parts["notes"])]
            b += ["<h3>Takeaways</h3>", tex_html(parts["takeaways"]),
                  "<h3>Answer key (as the quiz will grade it)</h3>",
                  f"<pre>{html.escape(json.dumps(res.get('answer_key'), indent=1, ensure_ascii=False))}</pre>",
                  "<h3>Answer field</h3>", tex_html(res.get("answer_display")),
                  "<h3>Hint</h3>", tex_html(parts["hint"])]
        blocks.append("\n".join(b) + "</section>")
    nav = "<nav>" + " ".join(f"<a href=#q{q}>{q}</a>" for q in checks) + "</nav>"
    page = PAGE_HEAD + f"<h1>{html.escape(name)}</h1><p class=meta>{len(checks)} questions, {now_iso()}</p>" + nav + \
        "\n".join(blocks) + PAGE_TAIL
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    path = REVIEW_DIR / f"{name}.html"
    write_text(path, page)
    print(json.dumps({"review": path.as_posix()}))
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("status")
    p = sp.add_parser("queue")
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--ids")
    p = sp.add_parser("prompt")
    p.add_argument("--subject", required=True)
    p.add_argument("--mode", choices=subjects.MODES, required=True)
    sp.add_parser("verify")
    p = sp.add_parser("pilot")
    p.add_argument("--subject", required=True)
    p.add_argument("--solve", type=int, default=20)
    p.add_argument("--aids", type=int, default=6)
    for name in ("solve", "tiebreak"):
        p = sp.add_parser(name)
        p.add_argument("--n", type=int)
        p.add_argument("--ids")
        p.add_argument("--workers", type=int)
        p.add_argument("--wait-on-limit", action="store_true")
        p.add_argument("--force-unlock", action="store_true")
        if name == "tiebreak":
            p.add_argument("--list", action="store_true", help="only list the questions")
    for name in ("precheck", "review"):
        p = sp.add_parser(name)
        p.add_argument("--ids")
        if name == "review":
            p.add_argument("--name", default="subjects_review")
    a = ap.parse_args()

    cfg = load_config()
    pc = run_sub.conn()
    app = app_conn(cfg)
    ids = [int(x) for x in a.ids.split(",") if x.strip()] if getattr(a, "ids", None) else None
    if a.cmd == "status":
        status(cfg, app, pc)
    elif a.cmd == "queue":
        for x in candidates(cfg, app, pc, ids)[: a.n]:
            print(json.dumps(x))
    elif a.cmd == "prompt":
        print(subjects.system_prompt(cfg, a.mode, a.subject))
    elif a.cmd == "verify":
        if not verify(cfg, app, pc)["ok"]:
            raise SystemExit(1)
    elif a.cmd == "pilot":
        print(",".join(map(str, pilot_ids(cfg, app, a.subject, a.solve, a.aids))))
    elif a.cmd == "solve":
        solve(cfg, app, pc, a.n, ids, a.workers, a.wait_on_limit, a.force_unlock)
    elif a.cmd == "tiebreak":
        if a.list:
            print(",".join(str(x["id"]) for x in tiebreak_rows(cfg, app, pc, ids)))
        else:
            solve(cfg, app, pc, a.n, ids, a.workers, a.wait_on_limit, a.force_unlock, tiebreak=True)
    elif a.cmd == "precheck":
        precheck(cfg, app, pc, ids)
    elif a.cmd == "review":
        review(cfg, app, pc, ids, a.name)


if __name__ == "__main__":
    main()
