"""Solution pipeline on the Claude subscription instead of the Message Batches API.

Same prompts, prompt_version, model, effort, max_tokens and checks as run.py; only the
transport differs (plus, by owner decision, a higher effort and output cap for the sources
named in config.subscription.effort_by_source / max_tokens_by_effort, which are redone). Each question is one fresh single-turn `claude -p` process (Claude Code
in print mode, logged in with the subscription): the pipeline's system prompt through
--system-prompt-file, the same user message on stdin, no tools, nothing saved. The reply is
stored the way run.py stores an API download (outputs/<id>/solver_<n>.tex,
response_<n>.json, status `received`), so `run.py judge` validates, assembles and writes it
to the app database unchanged, attribution line included. A reply cut off at the output
token limit (or by a safety classifier) is stored the same way with stop_reason max_tokens
(refusal), and judge treats it as in the API run; Claude Code's automatic follow-up turn is
never let run.

With config.attach_images a question that names images with \\includegraphics is sent with them
(owner 2026-11-10; the API run skipped them): the same text, then each image after a line naming
its command, as one stream-json user message. A question whose image file is missing, or whose
text points at a figure it does not carry, is still skipped (skipped_image).

Claude Code wraps every request in boilerplate that a subscription login cannot switch off:
a billing line and an identity line before the system prompt, a reminder with the account
email before the question, and an environment block (working directory, platform, model,
date) after it. `verify` captures the real request on a local stand-in server (nothing
reaches Anthropic, no usage) and checks it field by field against the API request; `solve`
repeats that check first and refuses to start unless the wrapping is one the owner accepted
(`verify --accept`). A Claude Code update that changes anything but the date or the account
email stops the run until it is verified again.

Usage (from the repo root):
  python pipeline/scripts/run_sub.py verify [--qid N] [--accept]   # free: capture and check the request
  python pipeline/scripts/run_sub.py status                        # progress over config.subscription
  python pipeline/scripts/run_sub.py queue  [--n 20]               # the next questions, in order
  python pipeline/scripts/run_sub.py solve  [--n N] [--ids 1,2,3] [--workers W] [--wait-on-limit]
  python pipeline/scripts/run_sub.py review [--list] [--ids 1,2,3] [--workers W] [--wait-on-limit]  # the review solve (review model) that replaces human review
  python pipeline/scripts/run_sub.py verify --review [--accept]    # the request check for it
  python pipeline/scripts/run.py judge [--workers N]               # then validate, assemble, write (XeLaTeX)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    IMG_RE,
    OUTPUTS_DIR,
    PIPELINE_DIR,
    app_conn,
    fetch_question,
    get_status,
    image_blocks,
    image_reason,
    is_blank,
    is_done,
    load_config,
    log_event,
    now_iso,
    pipe_conn,
    q_dir,
    question_images,
    read_json,
    teximages_dir,
    upsert_status,
    write_json,
    write_progress,
    write_text,
)
from run import system_prompt, user_text  # noqa: E402

# Claude Code describes its working directory in the environment block, so every question
# runs in the same empty directory, outside any git repository.
SUB_CWD = Path.home() / ".amplify-subscription-solver"
LOCK = PIPELINE_DIR / "run_sub.lock"
VERIFY_REPORT = OUTPUTS_DIR / "_sub_verify.json"  # git-ignored: it quotes the account email
BATCH_PREFIX = "sub:"  # status.batch_id and usage.batch_id of subscription replies

# Inherited variables that could change the request or the login (an API key would bill the
# API instead of the subscription; a parent Claude Code session passes its own effort).
KEEP_ENV = {"CLAUDE_CODE_GIT_BASH_PATH"}
DROP_ENV_PREFIXES = ("ANTHROPIC_", "CLAUDE_", "CLAUDECODE")

ALLOWED_BODY_KEYS = {"model", "max_tokens", "messages", "system", "thinking", "output_config", "tools",
                     "metadata", "stream", "context_management"}
DATE_RE = re.compile(r"Today's date is \d{4}-\d{2}-\d{2}\.")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LIMIT_TEXT_RE = re.compile(r"usage limit|session limit|weekly limit|hit your (?:\w+ )?limit|limit reached|rate limit", re.I)
RESET_RE = re.compile(r"resets\s+(?:(?P<mon>[A-Za-z]{3})[a-z]*\.?\s+(?P<day>\d{1,2}),?\s+(?:at\s+)?)?"
                      r"(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ap>[ap]m)\b(?:\s*\((?P<tz>[^)]+)\))?", re.I)
# The turns Claude Code adds after a reply that did not end normally (the run is ended there).
CUT_OFF_RE = re.compile(r"^\s*Output token limit hit\b")
CLASSIFIER_RE = re.compile(r"stopped by a safety classifier", re.I)
GEMINI_RE = re.compile(r"\[Generated by gemini-")
GEN_EFFORT_RE = re.compile(r"\[Generated by [^\]]* at (\w+) effort\]")
EFFORTS = ["low", "medium", "high", "xhigh", "max"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS sub_verifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT, claude_code_version TEXT, fingerprint TEXT, ok INTEGER, accepted INTEGER NOT NULL DEFAULT 0,
  report_json TEXT
);
"""


def sub_cfg(cfg: dict) -> dict:
    s = cfg.get("subscription")
    if not s or not s.get("sources"):
        raise SystemExit("config.json has no subscription.sources")
    stray = set(s.get("effort_by_source") or {}) - set(s["sources"])
    if stray:
        raise SystemExit(f"subscription.effort_by_source names sources missing from subscription.sources: {sorted(stray)}")
    bad = {e for e in (*(s.get("effort_by_source") or {}).values(), *(s.get("effort_by_id") or {}).values())
           if e not in EFFORTS}
    if bad:
        raise SystemExit(f"unknown effort level(s) in subscription.effort_by_source / effort_by_id: {sorted(bad)}")
    return s


_ASSIGNED: dict[str, dict[int, dict]] = {}


def assigned(cfg: dict) -> dict[int, dict]:
    """config.subscription.assignments_file (repo-relative): questions with their own solving model
    and effort, {"questions": {"<id>": {"model": ..., "effort": ...}}} (owner 2026-11-12: the MODS
    POTD buckets, Opus 5.5 medium / high and Fable 5.2 high). Listing a question there also puts it
    in the scope, whatever its source."""
    path = sub_cfg(cfg).get("assignments_file")
    if not path:
        return {}
    if path not in _ASSIGNED:
        data = json.loads((PIPELINE_DIR.parent / path).read_text(encoding="utf-8"))
        out = {int(k): v for k, v in data["questions"].items()}
        bad = {v.get("effort") for v in out.values()} - set(EFFORTS)
        if bad:
            raise SystemExit(f"unknown effort level(s) in {path}: {sorted(bad)}")
        _ASSIGNED[path] = out
    return _ASSIGNED[path]


def model_for(cfg: dict, qid: int | None) -> str:
    """config.solver.model, unless the assignments file gives the question its own model."""
    return (assigned(cfg).get(qid) or {}).get("model") or cfg["solver"]["model"]


def question_cfg(cfg: dict, qid: int) -> dict:
    """The config one question's request goes out with and its reply is checked and stored under:
    its own model when the assignments file names one."""
    model = model_for(cfg, qid)
    return cfg if model == cfg["solver"]["model"] else dict(cfg, solver=dict(cfg["solver"], model=model))


def conn() -> "sqlite3.Connection":  # noqa: F821
    pc = pipe_conn()
    pc.executescript(SCHEMA)
    return pc


# --- the claude invocation ----------------------------------------------------------


def claude_exe(cfg: dict) -> str:
    """The native Claude Code binary. On Windows the npm shim (claude.cmd) would route the
    arguments through cmd.exe, so the binary behind it is called directly."""
    p = os.environ.get("AMPLIFY_CLAUDE_EXE") or sub_cfg(cfg).get("claude_exe")
    if p:
        return p
    found = shutil.which("claude")
    if found:
        native = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / (
            "claude.exe" if os.name == "nt" else "claude")
        if native.exists():
            return str(native)
        if not found.lower().endswith((".cmd", ".bat", ".ps1")):
            return found
    raise SystemExit("Claude Code not found; set AMPLIFY_CLAUDE_EXE to the claude binary")


def effort_for(cfg: dict, source: str | None, qid: int | None = None) -> str:
    """config.solver.effort, unless config.subscription.effort_by_id names the question, the
    assignments file gives it an effort, or effort_by_source names its source."""
    s = sub_cfg(cfg)
    return ((s.get("effort_by_id") or {}).get(str(qid)) or (assigned(cfg).get(qid) or {}).get("effort")
            or (s.get("effort_by_source") or {}).get(source) or cfg["solver"]["effort"])


def claude_cmd(cfg: dict, system_file: Path, effort: str, stream_input: bool = False) -> list[str]:
    return [claude_exe(cfg), "-p",
            "--system-prompt-file", str(system_file),  # replaces Claude Code's own system prompt
            "--model", cfg["solver"]["model"], "--effort", effort,
            "--tools", "",                             # no tools: a single reply, as over the API
            "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--strict-mcp-config", "--safe-mode",
            "--permission-mode", "dontAsk",
            *(["--input-format", "stream-json"] if stream_input else [])]  # a message with image blocks


def attachments(cfg: dict, q: dict) -> tuple[list[tuple[str, Path]], str | None]:
    """The images to send with a question, and why it is skipped instead (None: send it). Without
    config.attach_images every question image_reason flags is skipped, as in the API run. With it,
    a question goes with the images its \\includegraphics commands name when every file exists;
    one whose text points at a figure it does not carry is still skipped, unless it is in
    config.subscription.figure_ok_ids (read and found not to need a figure)."""
    reason = image_reason(q["latexcode"])
    if not reason:
        return [], None
    if not IMG_RE.search(q["latexcode"]):
        return [], None if q["question_id"] in set(sub_cfg(cfg).get("figure_ok_ids") or ()) else reason
    if not cfg.get("attach_images"):
        return [], reason
    return question_images([q["latexcode"]], teximages_dir(cfg))


def max_tokens_for(cfg: dict, effort: str) -> int:
    """config.solver.max_tokens (the API run's 32k), unless subscription.max_tokens_by_effort
    raises it for this effort (owner 2026-11-04: 128k at high, where 32k cut replies off)."""
    return int((sub_cfg(cfg).get("max_tokens_by_effort") or {}).get(effort) or cfg["solver"]["max_tokens"])


def child_env(cfg: dict, effort: str, base_url: str | None = None) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k in KEEP_ENV or not k.upper().startswith(DROP_ENV_PREFIXES)}
    env.update({
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(max_tokens_for(cfg, effort)),
        "CLAUDE_CODE_THINKING_DISPLAY_UPDATES": "0",  # plain {"type": "adaptive"}, the API default here
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_AUTOUPDATER": "1",
    })
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    return env


def write_system_file(cfg: dict) -> tuple[Path, str]:
    system = system_prompt(cfg)
    SUB_CWD.mkdir(parents=True, exist_ok=True)
    path = SUB_CWD.parent / ".amplify-subscription-system-prompt.txt"  # outside the cwd: the cwd stays empty
    path.write_bytes(system.encode("utf-8"))
    return path, system


def call_claude(cfg: dict, system_file: Path, text: str, effort: str, base_url: str | None = None,
                images: list[tuple[str, Path]] | None = None) -> dict:
    """Run one question; return the parsed stream-json events (no interpretation). When Claude
    Code follows the reply with a turn of its own (a `user` event: "Output token limit hit.
    Resume directly...", a stalled stream, a safety-classifier stop), the process is ended
    there: a second turn is never used, so letting it run would only cost time and usage.
    With images, the same text goes as the first block of a stream-json user message and each
    image follows it (image_blocks); Claude Code's wrapping is the same either way."""
    t0 = time.time()
    if images:
        msg = {"role": "user", "content": [{"type": "text", "text": text}, *image_blocks(images)]}
        payload = json.dumps({"type": "user", "message": msg}) + "\n"
    else:
        payload = text
    p = subprocess.Popen(claude_cmd(cfg, system_file, effort, stream_input=bool(images)), stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=SUB_CWD, env=child_env(cfg, effort, base_url))
    timed_out = threading.Event()

    def on_timeout() -> None:
        timed_out.set()
        p.kill()

    def feed() -> None:
        try:
            p.stdin.write(payload.encode("utf-8"))
            p.stdin.close()
        except OSError:
            pass

    err: list[bytes] = []
    helpers = [threading.Thread(target=feed, daemon=True),
               threading.Thread(target=lambda: err.append(p.stderr.read()), daemon=True)]
    for t in helpers:
        t.start()
    timer = threading.Timer(int(sub_cfg(cfg).get("timeout_seconds", 1800)), on_timeout)
    timer.start()
    events = []
    try:
        for raw in p.stdout:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(ev)
            if ev.get("type") == "user":
                p.kill()
                break
        p.wait()
    finally:
        timer.cancel()
        for t in helpers:
            t.join(timeout=5)
        p.stdout.close()
    if timed_out.is_set():
        return {"error": "timed out", "seconds": int(time.time() - t0)}
    return {"events": events, "returncode": p.returncode, "seconds": int(time.time() - t0),
            "stderr": b"".join(err).decode("utf-8", "replace")[-2000:]}


# --- verify: capture the real request on a local stand-in server ----------------------


class _StandIn(BaseHTTPRequestHandler):
    """Records requests and answers /v1/messages with a short fake streamed reply."""

    captured: list = []
    FAKE = "%%% BEGIN SOLUTION\n(stand-in reply)\n%%% END SOLUTION"

    def log_message(self, *a):
        pass

    def do_GET(self):
        self.captured.append({"method": "GET", "path": self.path, "body": None})
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("content-length") or 0))
        try:
            body = json.loads(raw)
        except ValueError:
            body = None
        self.captured.append({"method": "POST", "path": self.path, "body": body})
        if not self.path.split("?")[0].endswith("/v1/messages") or not isinstance(body, dict):
            self.send_response(404)
            self.end_headers()
            return
        msg = {"id": "msg_standin", "type": "message", "role": "assistant", "model": body.get("model"),
               "content": [], "stop_reason": None, "stop_sequence": None,
               "usage": {"input_tokens": 1, "output_tokens": 1, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}
        events = [
            {"type": "message_start", "message": msg},
            {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
            {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": self.FAKE}},
            {"type": "content_block_stop", "index": 0},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 1}},
            {"type": "message_stop"},
        ]
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        for ev in events:
            self.wfile.write(f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n".encode())
        self.wfile.flush()


def capture_request(cfg: dict, system_file: Path, text: str, effort: str,
                    images: list[tuple[str, Path]] | None = None) -> tuple[list, dict]:
    _StandIn.captured = []
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _StandIn)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        out = call_claude(cfg, system_file, text, effort, base_url=f"http://127.0.0.1:{srv.server_address[1]}",
                          images=images)
    finally:
        srv.shutdown()
    return list(_StandIn.captured), out


def _texts(content) -> list[str]:
    if isinstance(content, str):
        return [content]
    return [c.get("text", "") if c.get("type") == "text" else json.dumps(c) for c in content]


def _block_core(b) -> dict:
    """What a content block carries, without delivery fields such as cache_control."""
    if not isinstance(b, dict):
        return {"text": b}
    return {"type": b.get("type"), **({"text": b.get("text")} if b.get("type") == "text" else {"source": b.get("source")})}


def check_request(cfg: dict, system: str, text: str, effort: str, captured: list, out: dict, api_shas: set[str],
                  images: list[tuple[str, Path]] | None = None) -> dict:
    """Field-by-field comparison with the request run.py sends for the same question (with images:
    the same request plus the image blocks right after the question; they are not part of the
    wrapping, so its fingerprint is the one a text question gives)."""
    st = dict(cfg["solver"], effort=effort, max_tokens=max_tokens_for(cfg, effort))
    checks: list[tuple[str, bool, str]] = []

    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    init = next((e for e in out.get("events", []) if e.get("type") == "system" and e.get("subtype") == "init"), {})
    chk("logged in with the subscription, not an API key", init.get("apiKeySource") == "none",
        f"apiKeySource={init.get('apiKeySource')}")
    sha = hashlib.sha256(system.encode("utf-8")).hexdigest()
    chk("system prompt is the one the API batches of this prompt version used", not api_shas or sha in api_shas, sha[:16])
    posts = [c for c in captured if c["method"] == "POST" and c["path"].split("?")[0].endswith("/v1/messages")]
    chk("exactly one model request", len(posts) == 1, f"{len(posts)} requests; all paths: {[c['path'] for c in captured]}")
    if len(posts) != 1 or not isinstance(posts[0]["body"], dict):
        return {"ok": False, "checks": checks, "fingerprint": None, "boilerplate": None, "init": init}
    b = posts[0]["body"]
    chk("model", b.get("model") == st["model"], str(b.get("model")))
    chk("effort", b.get("output_config") == {"effort": st["effort"]}, json.dumps(b.get("output_config")))
    chk("max_tokens", b.get("max_tokens") == int(st["max_tokens"]), str(b.get("max_tokens")))
    chk("adaptive thinking (the API default for this model)", b.get("thinking") == {"type": "adaptive"},
        json.dumps(b.get("thinking")))
    chk("no tools", not b.get("tools") and "tool_choice" not in b, json.dumps(b.get("tools")))
    chk("no other request fields", set(b) <= ALLOWED_BODY_KEYS, str(sorted(set(b) - ALLOWED_BODY_KEYS)))

    sys_blocks = _texts(b.get("system") or [])
    chk("system prompt sent byte for byte, as the last system block", sys_blocks and sys_blocks[-1] == system,
        f"{len(sys_blocks)} system blocks")
    msgs = b.get("messages") or []
    first = msgs[0] if msgs else {}
    content = first.get("content", []) if first.get("role") == "user" else []
    content = [{"type": "text", "text": content}] if isinstance(content, str) else list(content)
    user_blocks = _texts(content)
    chk("question sent byte for byte, once", user_blocks.count(text) == 1, f"{len(user_blocks)} user blocks")
    span = 0
    if images:
        want = [_block_core(x) for x in image_blocks(images)]
        at = user_blocks.index(text) + 1 if text in user_blocks else len(content)
        got = [_block_core(x) for x in content[at:at + len(want)]]
        chk("images sent byte for byte right after the question, each after its \\includegraphics line",
            got == want, f"{len(images)} images, {len(got) // 2} found in place")
        span = len(want) if got == want else 0
        content = content[:at] + content[at + span:]
        user_blocks = user_blocks[:at] + user_blocks[at + span:]
    extra_user = [t for t in user_blocks if t != text]
    chk("other user blocks are Claude Code context reminders",
        all(t.startswith("<system-reminder>") for t in extra_user), str([t[:60] for t in extra_user]))
    later = msgs[1:]
    chk("nothing after the question but Claude Code's environment block",
        all(m.get("role") == "system" for m in later), str([m.get("role") for m in later]))

    boilerplate = {
        "system_blocks_before_prompt": sys_blocks[:-1],
        "user_blocks_besides_question": extra_user,
        "messages_after_question": [t for m in later for t in _texts(m.get("content", []))],
        "request_fields": sorted(b),
        "context_management": b.get("context_management"),
        "stream": b.get("stream"),
    }
    return {"ok": all(ok for _, ok, _ in checks), "checks": checks, "fingerprint": wrap_fingerprint(boilerplate),
            "boilerplate": boilerplate, "init": init}


def wrap_fingerprint(boilerplate: dict) -> str:
    """Hash of Claude Code's wrapping with the date and the account email masked: neither
    changes what the model is asked, and the run may use whichever account is logged in."""
    s = DATE_RE.sub("Today's date is <date>.", json.dumps(boilerplate, ensure_ascii=False))
    norm = json.loads(EMAIL_RE.sub("<email>", s))
    return hashlib.sha256(json.dumps(norm, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def accepted_fingerprints(pc) -> set[str]:
    """Every wrapping the owner accepted, fingerprinted as wrap_fingerprint does now (rows
    accepted before the email was masked still count)."""
    out = set()
    for (rep,) in pc.execute("SELECT report_json FROM sub_verifications WHERE accepted=1"):
        out |= {wrap_fingerprint(r["boilerplate"]) for r in json.loads(rep).get("reports", []) if r.get("boilerplate")}
    return out


def api_system_shas(pc, prompt_version: str) -> set[str]:
    """The system prompts the API batches of this prompt version used. Empty for a version the
    API never ran (v6, tiered hints, 2026-11-11): there is then no API prompt to compare with,
    and the request check still sends solver.md byte for byte."""
    return {r[0] for r in pc.execute("SELECT DISTINCT system_sha256 FROM api_batches WHERE system_sha256 IS NOT NULL "
                                     "AND prompt_version=?", (prompt_version,))}


def verify_samples(cfg: dict, app, pc) -> list[int]:
    """One question of each kind the run sends: a fresh one, a retry (its message carries the
    previous reply), one with non-ASCII text, one from each effort level in use, and one with
    one image and one with several when images are sent."""
    picks: dict[str, int] = {}
    for qid in candidates(cfg, app, pc):
        q = fetch_question(app, qid)
        images, skip = attachments(cfg, q)
        if skip:
            continue
        row = get_status(pc, qid)
        kinds = ["retry" if row is not None and row["status"] == "retry" else "fresh",
                 "effort:" + effort_for(cfg, q["source"], qid), "model:" + model_for(cfg, qid)]
        if any(ord(ch) > 127 for ch in q["latexcode"]):
            kinds.append("non-ascii")
        if images:
            kinds.append("images" if len(images) == 1 else "several images")
        for k in kinds:
            picks.setdefault(k, qid)
    return list(dict.fromkeys(picks.values()))


def verify(cfg: dict, app, pc, qids: list[int] | None = None, accept: bool = False, quiet: bool = False,
           review: bool = False) -> dict:
    """Capture the request Claude Code sends for a few real questions and check it. With review,
    the review solve's request (review model and effort) for up to two of its questions."""
    system_file, system = write_system_file(cfg)
    qids = qids or (review_rows(cfg, app, pc)[:2] if review else verify_samples(cfg, app, pc))
    if not qids:
        raise SystemExit("no candidate question to verify with; pass --qid")
    ccfg = review_cfg(cfg) if review else cfg
    shas = api_system_shas(pc, cfg["prompt_version"])
    reports = []
    for qid in qids:
        q = fetch_question(app, qid)
        if review:
            attempt, feedback = plan_review_attempt(pc, qid)
            effort = sub_cfg(cfg)["review_effort"]
        else:
            attempt, feedback, _redo = plan_attempt(cfg, pc, qid, q["source"])  # no reset here: verify writes nothing
            effort = effort_for(cfg, q["source"], qid)
        text = user_text(q, feedback)
        images, _skip = attachments(cfg, q)
        qc = ccfg if review else question_cfg(cfg, qid)
        captured, out = capture_request(qc, system_file, text, effort, images)
        rep = check_request(qc, system, text, effort, captured, out, shas, images)
        rep.update({"question_id": qid, "source": q["source"], "effort": effort, "model": qc["solver"]["model"],
                    "attempt": attempt, "with_feedback": bool(feedback), "images": len(images),
                    "claude_code_version": rep["init"].get("claude_code_version")})
        reports.append(rep)
    # Claude Code's environment block names the model, so each model has a wrapping of its own:
    # one fingerprint per model, each of them accepted.
    by_model: dict[str, set] = {}
    for r in reports:
        by_model.setdefault(r["model"], set()).add(r["fingerprint"])
    fps = sorted({f for r in reports if (f := r["fingerprint"])})
    versions = {r["claude_code_version"] for r in reports}
    ok = all(r["ok"] for r in reports) and all(len(v) == 1 for v in by_model.values())
    fp = ",".join(fps) if ok else None
    version = versions.pop() if len(versions) == 1 else None
    accepted_before = ok and all(f in accepted_fingerprints(pc) for f in fps)
    if accept and not ok:
        raise SystemExit("refusing --accept: the request failed a check (see " + VERIFY_REPORT.as_posix() + ")")
    summary = {"at": now_iso(), "ok": ok, "fingerprint": fp, "claude_code_version": version,
               "accepted": accepted_before or accept, "reports": [{k: v for k, v in r.items() if k != "init"} for r in reports]}
    write_json(VERIFY_REPORT, summary)
    pc.execute("INSERT INTO sub_verifications (created_at, claude_code_version, fingerprint, ok, accepted, report_json) VALUES (?,?,?,?,?,?)",
               (now_iso(), version, fp, int(ok), int(accept and ok), json.dumps(summary)))
    pc.commit()
    if not quiet:
        for r in reports:
            print(f"question {r['question_id']} ({r['source'][:40]}, {r['model']}, {r['effort']} effort, attempt {r['attempt']}"
                  f"{', with feedback' if r['with_feedback'] else ''}"
                  f"{', ' + str(r['images']) + ' image(s)' if r['images'] else ''}):")
            for name, good, detail in r["checks"]:
                print(f"  {'ok  ' if good else 'FAIL'} {name}" + (f"  [{detail}]" if detail and not good else ""))
        print(f"Claude Code {version}; wrapping fingerprint(s) {', '.join(f[:16] for f in fps) or None}; "
              f"{'accepted' if summary['accepted'] else 'NOT accepted yet (review the boilerplate in ' + VERIFY_REPORT.as_posix() + ', then verify --accept)'}")
    return summary


# --- selection ----------------------------------------------------------------------


def solution_kind(solution: str | None) -> str:
    """What the question's own `solution` holds: nothing, a Gemini solution (they end with
    \\hfill [Generated by gemini-...]), or the source's solution."""
    if is_blank(solution):
        return "missing"
    return "gemini" if GEMINI_RE.search(solution) else "book"


def effort_rank(effort: str | None) -> int:
    return EFFORTS.index(effort) if effort in EFFORTS else -1


def generated_effort(generated: str | None) -> str | None:
    """The effort named in a generated solution's attribution line, or None."""
    m = GEN_EFFORT_RE.search(generated or "")
    return m.group(1) if m else None


def scope_rows(cfg: dict, app) -> list[tuple[int, str, str | None]]:
    """(question_id, source, generated) for config.subscription.sources, in priority order.
    generated is None, or the effort named in the stored generated solution ("?" if unnamed).
    Kept: questions whose `solution` kind is in config.subscription.replace, every question
    of a source in effort_by_source (those are redone when their solution came from a lower effort),
    and the questions in redo_ids. Plus api_leftover_ids, figure_ok_ids (questions the API run
    skipped for a figure they turned out not to need), image_ids (book-solved image questions
    of sources outside the scope) and the questions of the assignments file, whatever their source
    or solution kind, after everything else."""
    s = sub_cfg(cfg)
    srcs = s["sources"]
    kinds = set(s.get("replace") or ("missing", "gemini"))
    redo = set(s.get("effort_by_source") or {})
    redo_ids = set(s.get("redo_ids") or ())
    leftover = (set(s.get("api_leftover_ids") or ()) | set(s.get("figure_ok_ids") or ()) | set(s.get("image_ids") or ())
                | set(assigned(cfg)))
    rank = {src: i for i, src in enumerate(srcs)}
    cols = "question_id, source, solution, generated_solution"
    rows = app.execute(f"SELECT {cols} FROM questions WHERE source IN ({','.join('?' * len(srcs))})", srcs).fetchall()
    have = {r[0] for r in rows}
    if leftover:
        rows += [r for r in app.execute(f"SELECT {cols} FROM questions WHERE question_id IN ({','.join('?' * len(leftover))})",
                                        sorted(leftover)) if r[0] not in have]
    out = [(r[0], r[1], None if is_blank(r[3]) else (generated_effort(r[3]) or "?"))
           for r in rows if r[1] in redo or solution_kind(r[2]) in kinds or r[0] in redo_ids or r[0] in leftover]
    out.sort(key=lambda t: (rank.get(t[1], len(rank)), t[0]))
    return out


def last_effort(row) -> str | None:
    """The effort of a status row's latest attempt."""
    if row is None or not row["attempts"]:
        return None
    return row["solver2_effort"] if int(row["attempts"]) >= 2 else row["solver1_effort"]


def below(effort: str | None, required: str) -> bool:
    return effort is not None and effort_rank(effort) < effort_rank(required)


def from_sub(row) -> bool:
    """The status row's latest reply came through the subscription."""
    return row is not None and str(row["batch_id"] or "").startswith(BATCH_PREFIX)


def candidates(cfg: dict, app, pc, ids: list[int] | None = None) -> list[int]:
    """Unfinished questions in processing order: retries first (as run.py), then by source
    priority and id. A question with a generated solution is redone only when it comes from an
    effort below what its source now gets (effort_by_source), or when it is in redo_ids and has
    not been through the subscription yet (its text changed after the API solved it) or its
    subscription attempt was rejected; everything else is never redone."""
    status = {r["question_id"]: r for r in pc.execute("SELECT * FROM status")}
    rows = scope_rows(cfg, app)
    if ids:
        want = set(ids)
        rows = [t for t in rows if t[0] in want]
        missing = want - {t[0] for t in rows}
        if missing:
            raise SystemExit(f"not in the subscription scope: {sorted(missing)}")
    redo = set(sub_cfg(cfg).get("effort_by_source") or {})
    redo_qids = {int(k) for k in sub_cfg(cfg).get("effort_by_id") or {}}
    redo_ids = set(sub_cfg(cfg).get("redo_ids") or ())
    retry, fresh = [], []
    for qid, src, gen in rows:
        r = status.get(qid)
        if r is not None and r["review_from"] is not None:
            continue  # the review solve's (review_rows), with its own model and attempts
        need = effort_for(cfg, src, qid)
        stale = (src in redo or qid in redo_qids) and ((gen is not None and (gen == "?" or below(gen, need))) or below(last_effort(r), need))
        # a redo_ids question until its subscription redo is settled (a rejected attempt gets its retry)
        stale = stale or (qid in redo_ids and (not from_sub(r) or r["status"] == "retry"))
        if r is not None and r["status"] in ("submitted", "received", "missing_image"):
            continue
        if r is not None and r["status"] == "skipped_image":
            if attachments(cfg, fetch_question(app, qid))[1]:
                continue  # still cannot go with its figure
            r = None  # skipped before config.attach_images: now it goes with its images, as a new question
        if r is not None and r["status"] == "needs_human_review" and not below(last_effort(r), need):
            continue  # settled at the effort its source gets now (a redo keeps its old solution meanwhile)
        if not stale and (gen is not None or (r is not None and is_done(r))):
            continue
        (retry if r is not None and r["status"] == "retry" and not stale else fresh).append(qid)
    return retry + fresh


def plan_attempt(cfg: dict, pc, qid: int, source: str) -> tuple[int, dict | None, bool]:
    """(attempt, feedback, redo). redo: the question's earlier attempts ran at a lower effort than
    its source now gets, or came from the API for a question in redo_ids, so it starts again from
    attempt 1 (solve archives the old files first)."""
    row = get_status(pc, qid)
    if below(last_effort(row), effort_for(cfg, source, qid)):
        return 1, None, True
    if (qid in set(sub_cfg(cfg).get("redo_ids") or ()) and row is not None and int(row["attempts"] or 0) > 0
            and not from_sub(row)):
        return 1, None, True
    attempt = (int(row["attempts"]) if row else 0) + 1
    fb = q_dir(qid) / f"feedback_{attempt}.json"
    feedback = read_json(fb) if (row is not None and row["status"] == "retry" and fb.exists()) else None
    return attempt, feedback, False


def review_cfg(cfg: dict) -> dict:
    """The config the review solve's transport and storage read: config.subscription.review_model."""
    return dict(cfg, solver=dict(cfg["solver"], model=sub_cfg(cfg)["review_model"]))


def review_rows(cfg: dict, app, pc, ids: list[int] | None = None) -> list[int]:
    """Math questions for the review solve that replaces human review (owner 2026-11-11, as the
    subjects' adjudicate): every math question in human review that has not had it (or whose
    review request never came back), and review solves the checks sent back (retry) or whose
    request failed (pending). A question no longer in the app, or whose figure cannot go, is left out."""
    out = []
    for r in pc.execute("SELECT * FROM status WHERE mode IS NULL AND status IN ('needs_human_review', 'retry', 'pending') "
                        "ORDER BY question_id"):
        qid, rf = r["question_id"], r["review_from"]
        if ids and qid not in ids:
            continue
        take = (rf is None or int(r["attempts"] or 0) < rf) if r["status"] == "needs_human_review" else rf is not None
        q = fetch_question(app, qid) if take else None
        if q is not None and not attachments(cfg, q)[1]:
            out.append(qid)
    return out


def plan_review_attempt(pc, qid: int) -> tuple[int, dict | None]:
    """The next attempt; the checks' feedback only when the checks sent a review solve back."""
    row = get_status(pc, qid)
    attempt = int(row["attempts"] or 0) + 1
    fb = q_dir(qid) / f"feedback_{attempt}.json"
    return attempt, (read_json(fb) if row["status"] == "retry" and row["review_from"] is not None and fb.exists() else None)


def reset_for_redo(pc, qid: int, effort: str) -> None:
    """Move the earlier attempt's files aside (kept, not deleted) and start the question afresh.
    The stored generated solution, answer and hint stay in the app until the redo passes."""
    row = get_status(pc, qid)
    d = q_dir(qid)
    dest = d / f"before_{effort}_redo_{now_iso().replace(':', '').replace('-', '')}"
    dest.mkdir(parents=True, exist_ok=True)
    for f in d.iterdir():
        if f.is_file():
            f.rename(dest / f.name)
    upsert_status(pc, qid, status="pending", attempts=0, accepted_attempt=None, assembled=0, hint_status="none",
                  answer_mismatch=0, api_failures=0, pending_attempt=None, batch_id=None, batch=None,
                  solver1_model=None, solver1_effort=None, solver2_model=None, solver2_effort=None,
                  note=f"redo at {effort} effort (was {row['status']} at {last_effort(row)}); earlier files in {dest.name}/")
    log_event(pc, qid, "sub", f"redo at {effort} effort; earlier files moved to {dest.name}/")


# --- solve --------------------------------------------------------------------------


def reset_from_text(msg: str) -> float | None:
    """The reset time in a usage-limit message ("... resets 5:50am (Asia/Dubai)", "resets Nov
    10, 4am") as a timestamp, or None. The zone named is used when Python knows it (tzdata),
    else local time, which is the zone Claude Code prints."""
    m = RESET_RE.search(msg or "")
    if not m:
        return None
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(m["tz"])) if m["tz"] else datetime.now().astimezone()
    except Exception:
        now = datetime.now().astimezone()
    hour = int(m["h"]) % 12 + (12 if m["ap"].lower() == "pm" else 0)
    try:
        at = now.replace(hour=hour, minute=int(m["m"] or 0), second=0, microsecond=0)
        if m["mon"]:
            at = at.replace(month=datetime.strptime(m["mon"].title(), "%b").month, day=int(m["day"]))
            if at < now - timedelta(days=1):
                at = at.replace(year=at.year + 1)
        elif at <= now:
            at += timedelta(days=1)
    except ValueError:
        return None
    return at.timestamp() if at - now <= timedelta(days=8) else None


def turn_text(e: dict) -> str:
    c = (e.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") for b in c or [] if isinstance(b, dict))


def cut_off(ev: list, turn: dict, init: dict, limits: list, cfg: dict) -> dict:
    """Claude Code followed the reply with a turn of its own. The reply as far as it went is stored
    the way the API returns such a reply, so `run.py judge` settles it exactly as in the API run:
    the output token limit -> stop_reason max_tokens (a blind re-solve, then human review); a
    safety-classifier stop -> refusal (human review). Anything else (a stalled stream) is a failure,
    as an API error is."""
    said = turn_text(turn)
    stop = "max_tokens" if CUT_OFF_RE.match(said) else "refusal" if CLASSIFIER_RE.search(said) else None
    if stop is None:
        return {"kind": "error", "why": f"Claude Code added a turn: {said[:160]}"}
    before = ev[:ev.index(turn)]
    msgs = [e["message"] for e in before if e.get("type") == "assistant" and e.get("message")]
    model = cfg["solver"]["model"]
    if len({m.get("id") for m in msgs}) != 1 or any(m.get("model") != model for m in msgs):
        return {"kind": "error", "why": f"{stop}, but not a single reply by {model} before it"}
    text = "".join(c.get("text", "") for m in msgs for c in m.get("content", []) if c.get("type") == "text")
    usage = dict(msgs[0].get("usage") or {})
    # The run ends before Claude Code's final count, so output_tokens is its running thinking estimate.
    est = max((e.get("estimated_tokens") or 0 for e in before
               if e.get("type") == "system" and e.get("subtype") == "thinking_tokens"), default=0)
    usage["output_tokens"] = max(int(usage.get("output_tokens") or 0), int(est))
    result = {"stop_reason": stop, "usage": usage, "session_id": init.get("session_id")}
    return {"kind": "cut", "why": f"{stop}: Claude Code then said: {said[:120]}", "text": text, "result": result,
            "init": init, "model": model, "warning": any(li.get("status") == "allowed_warning" for li in limits)}


def interpret(out: dict, cfg: dict, version: str) -> dict:
    """Classify one claude run: ok (a reply to store), cut (a reply cut off at the output token
    limit or by a safety classifier: stored as the API would return it), limited (usage limit:
    try again later), stop (the setup changed: stop the run), or error (counts as an API failure)."""
    if "events" not in out:
        return {"kind": "error", "why": out.get("error", "no output")}
    ev = out["events"]
    init = next((e for e in ev if e.get("type") == "system" and e.get("subtype") == "init"), {})
    result = next((e for e in reversed(ev) if e.get("type") == "result"), None)
    limits = [e.get("rate_limit_info") or {} for e in ev if e.get("type") == "rate_limit_event"]
    if init.get("claude_code_version") != version:
        return {"kind": "stop", "why": f"Claude Code is now {init.get('claude_code_version')}, verified {version}"}
    if init.get("apiKeySource") != "none":
        return {"kind": "stop", "why": f"not logged in with the subscription (apiKeySource={init.get('apiKeySource')})"}
    turn = next((e for e in ev if e.get("type") == "user"), None)
    if turn is not None:
        return cut_off(ev, turn, init, limits, cfg)
    rejected = [li for li in limits if li.get("status") == "rejected"]
    if result is None or result.get("is_error") or result.get("subtype") != "success":
        msg = (result or {}).get("result") or out.get("stderr", "")
        if rejected or (result or {}).get("api_error_status") == 429 or LIMIT_TEXT_RE.search(str(msg)):
            reset = next((li.get("resetsAt") for li in rejected if li.get("resetsAt")), None) or reset_from_text(str(msg))
            return {"kind": "limited", "why": str(msg)[:200], "resets_at": reset}
        return {"kind": "error", "why": str(msg)[:300] or f"exit code {out.get('returncode')}"}
    msgs = [e["message"] for e in ev if e.get("type") == "assistant" and e.get("message")]
    ids = list(dict.fromkeys(m.get("id") for m in msgs))
    model = cfg["solver"]["model"]
    if len(ids) != 1 or result.get("num_turns") != 1:
        return {"kind": "error", "why": f"not a single reply ({len(ids)} messages, {result.get('num_turns')} turns)"}
    if any(m.get("model") != model for m in msgs):
        return {"kind": "error", "why": f"answered by {sorted({m.get('model') for m in msgs})}, not {model}"}
    if result.get("fast_mode_state") not in (None, "off"):
        return {"kind": "stop", "why": f"fast mode is {result.get('fast_mode_state')}"}
    text = "".join(c.get("text", "") for m in msgs for c in m.get("content", []) if c.get("type") == "text")
    if text != (result.get("result") or ""):
        return {"kind": "error", "why": "reply text and result text differ"}
    return {"kind": "ok", "text": text, "result": result, "init": init, "model": msgs[0].get("model"),
            "warning": any(li.get("status") == "allowed_warning" for li in limits)}


def store(pc, cfg: dict, qid: int, attempt: int, effort: str, info: dict, seconds: int,
          images: list[str] | None = None) -> None:
    """Persist a reply exactly where run.py's download phase puts one. The effort recorded in
    status.solverN_effort is what assemble.py writes into the attribution line; the names of the
    images sent with the question go into the response file."""
    st = dict(cfg["solver"], effort=effort)
    res = info["result"]
    u = res.get("usage") or {}
    batch_id = BATCH_PREFIX + str(res.get("session_id"))
    d = q_dir(qid)
    write_text(d / f"solver_{attempt}.tex", info["text"])
    write_json(d / f"response_{attempt}.json", {
        "model": info["model"], "stop_reason": res.get("stop_reason"), "stop_details": None,
        "usage": u, "collected_at": now_iso(), "transport": "subscription",
        "claude_code_version": info["init"].get("claude_code_version"), "session_id": res.get("session_id"),
        "duration_ms": res.get("duration_ms"), "model_usage": res.get("modelUsage"),
        **({"images": images} if images else {}),
        **({"cut_off": info["why"]} if info["kind"] == "cut" else {}),
    })
    pc.execute(
        "INSERT INTO usage (question_id, attempt, batch_id, model, effort, input_tokens, cache_write_tokens, cache_read_tokens, output_tokens, stop_reason, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (qid, attempt, batch_id, info["model"], st["effort"], u.get("input_tokens", 0), u.get("cache_creation_input_tokens", 0),
         u.get("cache_read_input_tokens", 0), u.get("output_tokens", 0), res.get("stop_reason"), now_iso()),
    )
    pc.commit()
    upsert_status(pc, qid, status="received", attempts=attempt, pending_attempt=None, batch_id=batch_id, batch=None,
                  prompt_version=cfg["prompt_version"],
                  **{f"solver{min(attempt, 2)}_model": st["model"], f"solver{min(attempt, 2)}_effort": st["effort"]})
    log_event(pc, qid, "sub", f"attempt {attempt} received in {seconds}s, {u.get('output_tokens')} output tokens, stop {res.get('stop_reason')}"
              + (f", sent with {len(images)} image(s)" if images else ""))


def api_failure(pc, cfg: dict, qid: int, attempt: int, why: str) -> str:
    row = get_status(pc, qid)
    failures = (int(row["api_failures"] or 0) if row else 0) + 1
    log_event(pc, qid, "sub", f"attempt {attempt} failed: {why[:200]}")
    if failures >= int(cfg.get("max_api_failures", 3)):
        upsert_status(pc, qid, status="needs_human_review", api_failures=failures, note=f"{failures} failures, last: {why[:200]}")
        return "human_review"
    keep = row["status"] if row is not None and row["status"] == "retry" else "pending"
    upsert_status(pc, qid, status=keep, api_failures=failures, note=f"failure {failures}: {why[:200]}")
    return "error"


def save_failure(qid: int, attempt: int, out: dict, info: dict) -> str:
    """Keep Claude Code's raw output of a run that failed, was cut off or stopped the solve, for diagnosis:
    every stream-json event, stderr and the exit code, in outputs/<id>/sub_failure_<n>_<time>.json."""
    path = q_dir(qid) / f"sub_failure_{attempt}_{now_iso().replace(':', '').replace('-', '')}.json"
    write_json(path, {"kind": info["kind"], "why": info.get("why"), **out})
    return path.name


def acquire_lock(force: bool) -> None:
    if LOCK.exists() and not force:
        raise SystemExit(f"{LOCK.as_posix()} exists: another solve may be running (pid {LOCK.read_text().strip()}); "
                         "pass --force-unlock if it is not")
    LOCK.write_text(str(os.getpid()))


def keep_awake(on: bool) -> None:
    """Ask Windows not to sleep when idle while a solve runs: a sleep cuts off every reply in flight.
    Closing the lid or the power button still sleeps it, and the display may still turn off.
    Elsewhere it does nothing. It holds for the calling thread, so call it from the main one."""
    if sys.platform == "win32":
        import ctypes
        es_continuous, es_system_required = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(es_continuous | (es_system_required if on else 0))


def workers_for(cfg: dict, effort: str, override: int | None = None) -> int:
    """How many claude processes may run while a question of this effort is next in line:
    --workers if given, else subscription.workers_by_effort, else subscription.workers."""
    if override:
        return override
    s = sub_cfg(cfg)
    return int((s.get("workers_by_effort") or {}).get(effort) or s.get("workers", 2))


def solve(cfg: dict, app, pc, n: int | None, ids: list[int] | None, workers: int | None, wait_on_limit: bool,
          force_unlock: bool, review: bool = False) -> None:
    """Send the unfinished questions; with review, the review solve (config.subscription.review_model
    at review_effort) for the questions review_rows names. Neither sends the stored answer."""
    pre = verify(cfg, app, pc, quiet=True, review=review)
    if not pre["ok"] or not pre["accepted"]:
        raise SystemExit(f"the request check did not pass or its wrapping is not accepted; run `run_sub.py verify"
                         f"{' --review' if review else ''}` and read {VERIFY_REPORT.as_posix()}")
    version = pre["claude_code_version"]
    system_file, _ = write_system_file(cfg)
    acquire_lock(force_unlock)
    ccfg = review_cfg(cfg) if review else cfg  # the model the requests go to and the replies are stored under
    queue = review_rows(cfg, app, pc, ids) if review else candidates(cfg, app, pc, ids)
    if n is not None:
        queue = queue[:n]

    def effort_of(qid: int, source: str) -> str:
        return sub_cfg(cfg)["review_effort"] if review else effort_for(cfg, source, qid)

    efforts = ({sub_cfg(cfg)["review_effort"]} if review else
               {cfg["solver"]["effort"], *(sub_cfg(cfg).get("effort_by_source") or {}).values(),
                *(sub_cfg(cfg).get("effort_by_id") or {}).values(), *(v["effort"] for v in assigned(cfg).values())})
    limits = {e: workers_for(cfg, e, workers) for e in sorted(efforts, key=effort_rank)}
    models = Counter(model_for(cfg, qid) for qid in queue) if not review else Counter({ccfg["solver"]["model"]: len(queue)})
    print(json.dumps({"questions": len(queue), "workers": limits, "claude_code_version": version,
                      "model": ccfg["solver"]["model"], "models_in_queue": dict(models), "effort": cfg["solver"]["effort"],
                      "effort_by_source": sub_cfg(cfg).get("effort_by_source") or {},
                      "effort_by_id": sub_cfg(cfg).get("effort_by_id") or {},
                      "max_tokens_by_effort": sub_cfg(cfg).get("max_tokens_by_effort") or {},
                      **({"review": True, "review_effort": sub_cfg(cfg)["review_effort"]} if review else {})}), flush=True)
    summary: Counter = Counter()
    t0 = time.time()
    stop_reason = None
    keep_awake(True)
    try:
        with ThreadPoolExecutor(max_workers=max(limits.values())) as ex:
            running: dict = {}
            paused_until = None  # kept until the wait: the replies still running can take several more rounds
            while queue or running:
                while queue and stop_reason is None:
                    q = fetch_question(app, queue[0])
                    if len(running) >= limits[effort_of(queue[0], q["source"])]:
                        break
                    qid = queue.pop(0)
                    images, reason = attachments(cfg, q)
                    if reason:  # a figure that cannot go with the question: not sent
                        upsert_status(pc, qid, status="skipped_image", note=reason, prompt_version=cfg["prompt_version"])
                        log_event(pc, qid, "skip", reason)
                        summary["skipped_image"] += 1
                        continue
                    if review:
                        attempt, feedback = plan_review_attempt(pc, qid)
                        redo = False
                        if get_status(pc, qid)["review_from"] is None:
                            upsert_status(pc, qid, review_from=attempt)
                    else:
                        attempt, feedback, redo = plan_attempt(cfg, pc, qid, q["source"])
                    effort = effort_of(qid, q["source"])
                    if redo:
                        reset_for_redo(pc, qid, effort)
                        summary["redo"] += 1
                    qc = ccfg if review else question_cfg(cfg, qid)  # the question's own model, if assigned
                    fut = ex.submit(call_claude, qc, system_file, user_text(q, feedback), effort, None, images)
                    running[fut] = (qid, attempt, effort, [n for n, _ in images], qc)
                if not running:
                    break
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for fut in done:
                    qid, attempt, effort, names, qc = running.pop(fut)
                    out = fut.result()
                    info = interpret(out, qc, version)
                    kind = info["kind"]
                    raw = save_failure(qid, attempt, out, info) if kind in ("error", "stop", "cut") else None
                    if kind in ("ok", "cut"):
                        store(pc, qc, qid, attempt, effort, info, out.get("seconds", 0), names)
                        summary["received" if kind == "ok" else info["result"]["stop_reason"]] += 1
                        if info["warning"]:
                            summary["limit_warnings"] += 1
                    elif kind == "limited":
                        queue.insert(0, qid)  # nothing was used up; it goes again first
                        summary["limited"] += 1
                        if stop_reason is None:
                            stop_reason = "usage limit: " + info["why"]
                            paused_until = info.get("resets_at")
                    elif kind == "stop":
                        queue.insert(0, qid)
                        stop_reason = info["why"]
                        wait_on_limit = False
                    else:
                        summary[api_failure(pc, qc, qid, attempt, info["why"])] += 1
                    print(json.dumps({"question_id": qid, "attempt": attempt, "model": qc["solver"]["model"],
                                      "effort": effort, "outcome": kind,
                                      "seconds": out.get("seconds"),
                                      **({"why": info["why"]} if kind != "ok" else {}), **({"raw": raw} if raw else {}),
                                      "elapsed_min": round((time.time() - t0) / 60, 1), **summary}), flush=True)
                if stop_reason and not running:
                    if wait_on_limit and stop_reason.startswith("usage limit") and queue:
                        until = float(paused_until) if paused_until else time.time() + 900
                        secs = max(60, min(int(until - time.time()) + 120, 1020))  # short polls catch a /login switch
                        print(f"{stop_reason}; waiting {secs // 60} min, then continuing", flush=True)
                        deadline = time.time() + secs
                        while time.time() < deadline:  # by the clock: one long sleep does not count time the machine sleeps
                            time.sleep(min(60, max(1, deadline - time.time())))
                        stop_reason = paused_until = None
                        continue
                    break
    finally:
        keep_awake(False)
        LOCK.unlink(missing_ok=True)
        write_progress(pc)
    print(json.dumps({"finished": now_iso(), "stopped": stop_reason, "left_in_this_run": len(queue), **summary,
                      "next": "run.py judge validates and stores what was received"}), flush=True)


# --- status / queue -----------------------------------------------------------------


def status(cfg: dict, app, pc) -> None:
    rows = {r["question_id"]: r for r in pc.execute("SELECT * FROM status")}
    cand = set(candidates(cfg, app, pc))
    per: dict[str, Counter] = {}
    for qid, src, gen in scope_rows(cfg, app):
        c = per.setdefault(src, Counter())
        c["total"] += 1
        r = rows.get(qid)
        st = r["status"] if r is not None else None
        if st == "received":
            c["judge"] += 1
        elif st in ("skipped_image", "missing_image") and qid not in cand:
            c["no_img"] += 1
        elif qid in cand and st == "skipped_image":
            c["img"] += 1  # skipped before config.attach_images; goes with its images now
        elif qid in cand:
            if gen is not None or (r is not None and is_done(r)) or below(last_effort(r), effort_for(cfg, src, qid)):
                c["redo"] += 1
            elif st == "retry":
                c["retry"] += 1
            else:
                c["todo"] += 1
        elif st == "needs_human_review":
            c["human"] += 1
        else:
            c["done"] += 1
    sub = pc.execute(f"SELECT COUNT(*), COALESCE(SUM(output_tokens),0) FROM usage WHERE batch_id LIKE '{BATCH_PREFIX}%'").fetchone()
    print(f"subscription | {cfg['prompt_version']} | {cfg['solver']['model']} / {cfg['solver']['effort']} | "
          f"replies so far {sub[0]} ({sub[1]} output tokens) | replacing solutions that are: "
          f"{', '.join(sub_cfg(cfg).get('replace') or ('missing', 'gemini'))}")
    cols = ("total", "done", "human", "no_img", "judge", "retry", "redo", "todo", "img")
    print(f"{'#':>2} {'source':56} {'effort':>6} " + " ".join(f"{c:>6}" for c in cols))
    tot: Counter = Counter()
    srcs = sub_cfg(cfg)["sources"]
    for i, src in enumerate(list(srcs) + sorted(set(per) - set(srcs)), 1):  # then api_leftover_ids' other sources
        c = per.get(src, Counter())
        tot.update(c)
        print(f"{i:>2} {src[:56]:56} {effort_for(cfg, src):>6} " + " ".join(f"{c[k]:>6}" for k in cols))
    print(f"{'':>2} {'TOTAL':56} {'':>6} " + " ".join(f"{tot[k]:>6}" for k in cols))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("verify")
    p.add_argument("--qid", type=int, action="append")
    p.add_argument("--accept", action="store_true")
    p.add_argument("--review", action="store_true", help="check a review solve (review model and effort)")
    sp.add_parser("status")
    p = sp.add_parser("queue")
    p.add_argument("--n", type=int, default=20)
    for name in ("solve", "review"):
        p = sp.add_parser(name)
        p.add_argument("--n", type=int)
        p.add_argument("--ids")
        p.add_argument("--workers", type=int)
        p.add_argument("--wait-on-limit", action="store_true")
        p.add_argument("--force-unlock", action="store_true")
        if name == "review":
            p.add_argument("--list", action="store_true", help="only list the questions")
    a = ap.parse_args()

    cfg = load_config()
    pc = conn()
    app = app_conn(cfg)
    if a.cmd == "verify":
        s = verify(cfg, app, pc, a.qid, a.accept, review=a.review)
        if not s["ok"]:
            raise SystemExit(1)
    elif a.cmd == "status":
        status(cfg, app, pc)
    elif a.cmd == "queue":
        for qid in candidates(cfg, app, pc)[: a.n]:
            q = fetch_question(app, qid)
            r = get_status(pc, qid)
            images, skip = attachments(cfg, q)
            print(json.dumps({"question_id": qid, "source": q["source"], "status": r["status"] if r else "new",
                              "will_skip": skip, "images": len(images)}))
    elif a.cmd == "solve":
        ids = [int(x) for x in a.ids.split(",") if x.strip()] if a.ids else None
        solve(cfg, app, pc, a.n, ids, a.workers, a.wait_on_limit, a.force_unlock)
    elif a.cmd == "review":
        ids = [int(x) for x in a.ids.split(",") if x.strip()] if a.ids else None
        if a.list:
            print(",".join(str(q) for q in review_rows(cfg, app, pc, ids)))
        else:
            solve(cfg, app, pc, a.n, ids, a.workers, a.wait_on_limit, a.force_unlock, review=True)


if __name__ == "__main__":
    main()
