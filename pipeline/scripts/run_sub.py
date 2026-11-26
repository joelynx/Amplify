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
    REPO_DIR,
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
# A limit on one model alone ("You've reached your Fable limit. Switch to another model to continue."):
# that model's questions wait while the other models' questions go on.
MODEL_LIMIT_RE = re.compile(r"switch to another model|reached your (?!(?:session|weekly|usage)\b)\w+ limit", re.I)
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
    POTD buckets, Opus 5.5 medium / high and Fable 5.2 high), or a list of such files (a later file's
    entry wins). Listing a question there also puts it in the scope, whatever its source."""
    paths = sub_cfg(cfg).get("assignments_file")
    if not paths:
        return {}
    key = (paths,) if isinstance(paths, str) else tuple(paths)
    if key not in _ASSIGNED:
        out = {}
        for path in key:
            data = json.loads((PIPELINE_DIR.parent / path).read_text(encoding="utf-8"))
            got = {int(k): v for k, v in data["questions"].items()}
            bad = {v.get("effort") for v in got.values()} - set(EFFORTS)
            if bad:
                raise SystemExit(f"unknown effort level(s) in {path}: {sorted(bad)}")
            out.update(got)
        _ASSIGNED[key] = out
    return _ASSIGNED[key]


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


# Tools mode (owner 2026-11-21: "we need some way to enable tools to verify physics and engineering
# solves"): the one tool is `python` from calc_server.py, an MCP server Claude Code starts per question.
# Claude Code's own sandbox does not run on native Windows and never covers MCP servers, so
# calc_server/calc_runner do the isolating. --safe-mode would switch MCP servers off, so tools mode
# drops it and switches off what it covered one by one (CLAUDE.md, attachments, skills).
CALC_TOOL = "mcp__calc__python"
CALC_SERVER = Path(__file__).resolve().with_name("calc_server.py")


def tools_cfg(cfg: dict) -> dict:
    return cfg.get("tools") or {}


def uses_tools(cfg: dict, source: str) -> bool:
    """Tools mode for this solver (owner 2026-11-23: "Yes, add the calculator to the solver"): the questions of
    config.tools.math_sources (finance and quant sets, where computation slips cost answers) get the calc tool."""
    t = tools_cfg(cfg)
    return bool(t.get("enabled")) and source in (t.get("math_sources") or ())


def mcp_config(cfg: dict, tools_log: Path) -> Path:
    """A one-server MCP config for one run; the server appends every call to tools_log."""
    t = tools_cfg(cfg)
    py = str((REPO_DIR / t.get("python", "pipeline/calc/.venv/Scripts/python.exe")).resolve())
    path = SUB_CWD.parent / f".amplify-calc-mcp-{os.getpid()}-{threading.get_ident()}-{time.time_ns()}.json"
    path.write_text(json.dumps({"mcpServers": {"calc": {"command": py, "args": [
        "-I", str(CALC_SERVER), "--python", py, "--log", str(tools_log),
        "--timeout", str(int(t.get("timeout_seconds", 60))), "--max-calls", str(int(t.get("max_calls", 40)))]}}}),
        encoding="utf-8")
    return path


def claude_cmd(cfg: dict, system_file: Path, effort: str, stream_input: bool = False,
               mcp_file: Path | None = None) -> list[str]:
    # --restricted: user, project and local settings files are ignored, so their hooks and enabled plugins
    # do not load either (only --settings and managed settings apply); --mcp-config still does.
    tools = (["--mcp-config", str(mcp_file), "--allowedTools", CALC_TOOL, "--disable-slash-commands", "--restricted",
              "--max-turns", str(int(tools_cfg(cfg).get("max_turns", 30)))] if mcp_file else [])
    return [claude_exe(cfg), "-p",
            "--system-prompt-file", str(system_file),  # replaces Claude Code's own system prompt
            "--model", cfg["solver"]["model"], "--effort", effort,
            "--tools", "",                             # no built-in tools: a single reply, as over the API (tools mode: only the calc tool)
            "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--strict-mcp-config", *([] if mcp_file else ["--safe-mode"]),
            "--permission-mode", "dontAsk", *tools,
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


def child_env(cfg: dict, effort: str, base_url: str | None = None, tools: bool = False) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k in KEEP_ENV or not k.upper().startswith(DROP_ENV_PREFIXES)}
    env.update({
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(max_tokens_for(cfg, effort)),
        "CLAUDE_CODE_THINKING_DISPLAY_UPDATES": "0",  # plain {"type": "adaptive"}, the API default here
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_AUTOUPDATER": "1",
    })
    if tools:  # what --safe-mode switched off, without switching off the MCP server
        env.update({"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_ATTACHMENTS": "1"})
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    if _ACTIVE_DIR[0]:
        env["CLAUDE_CONFIG_DIR"] = _ACTIVE_DIR[0]  # account rotation: the active account's own login
    return env


def write_system_file(cfg: dict, tools: bool = False) -> tuple[Path, str]:
    system = system_prompt(cfg)
    if tools:  # the solver's prompt, then how to use the calc tool
        tp = REPO_DIR / tools_cfg(cfg).get("math_prompt", "pipeline/prompts/solver_tools.md")
        system = system.rstrip() + "\n\n" + tp.read_text(encoding="utf-8").strip() + "\n"
    SUB_CWD.mkdir(parents=True, exist_ok=True)
    path = SUB_CWD.parent / f".amplify-subscription-system-prompt{'-tools' if tools else ''}.txt"  # outside the cwd: the cwd stays empty
    path.write_bytes(system.encode("utf-8"))
    return path, system


def tool_results_only(ev: dict) -> bool:
    """A `user` event that only hands back calc tool results (tools mode), not a turn of Claude Code's own."""
    c = (ev.get("message") or {}).get("content")
    return isinstance(c, list) and bool(c) and all(isinstance(b, dict) and b.get("type") == "tool_result" for b in c)


def call_claude(cfg: dict, system_file: Path, text: str, effort: str, base_url: str | None = None,
                images: list[tuple[str, Path]] | None = None, tools_log: Path | None = None) -> dict:
    """Run one question; return the parsed stream-json events (no interpretation). When Claude
    Code follows the reply with a turn of its own (a `user` event: "Output token limit hit.
    Resume directly...", a stalled stream, a safety-classifier stop), the process is ended
    there: a second turn is never used, so letting it run would only cost time and usage.
    With images, the same text goes as the first block of a stream-json user message and each
    image follows it (image_blocks); Claude Code's wrapping is the same either way.
    With tools_log (tools mode) the calc tool is offered and its results come back as `user`
    events of tool_result blocks, which go on; every call is appended to tools_log."""
    t0 = time.time()
    if images:
        msg = {"role": "user", "content": [{"type": "text", "text": text}, *image_blocks(images)]}
        payload = json.dumps({"type": "user", "message": msg}) + "\n"
    else:
        payload = text
    mcp_file = None
    if tools_log is not None:
        tools_log.unlink(missing_ok=True)  # an earlier failed run of this attempt
        mcp_file = mcp_config(cfg, tools_log)
    try:
        p = subprocess.Popen(claude_cmd(cfg, system_file, effort, stream_input=bool(images), mcp_file=mcp_file),
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=SUB_CWD,
                             env=child_env(cfg, effort, base_url, tools=mcp_file is not None))
    except BaseException:
        if mcp_file:
            mcp_file.unlink(missing_ok=True)
        raise
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
            if ev.get("type") == "user" and not (mcp_file and tool_results_only(ev)):
                p.kill()
                break
        p.wait()
    finally:
        timer.cancel()
        for t in helpers:
            t.join(timeout=5)
        p.stdout.close()
        if mcp_file:
            mcp_file.unlink(missing_ok=True)
    tools = {"tools": True} if mcp_file else {}
    if timed_out.is_set():
        return {"error": "timed out", "seconds": int(time.time() - t0), **tools}
    return {"events": events, "returncode": p.returncode, "seconds": int(time.time() - t0),
            "stderr": b"".join(err).decode("utf-8", "replace")[-2000:], **tools}


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
                    images: list[tuple[str, Path]] | None = None, tools: bool = False) -> tuple[list, dict]:
    _StandIn.captured = []
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _StandIn)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    log = SUB_CWD.parent / f".amplify-calc-verify-{os.getpid()}.jsonl" if tools else None
    try:
        out = call_claude(cfg, system_file, text, effort, base_url=f"http://127.0.0.1:{srv.server_address[1]}",
                          images=images, tools_log=log)
    finally:
        srv.shutdown()
        if log:
            log.unlink(missing_ok=True)
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
                  images: list[tuple[str, Path]] | None = None, tools: bool = False) -> dict:
    """Field-by-field comparison with the request run.py sends for the same question (with images:
    the same request plus the image blocks right after the question; they are not part of the
    wrapping, so its fingerprint is the one a text question gives). With tools (tools mode) the
    request must offer exactly the calc tool, and its definition is part of the wrapping, so a
    changed tool description needs the owner's acceptance again."""
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
    if tools:
        chk("only the calc tool", [t.get("name") for t in b.get("tools") or []] == [CALC_TOOL] and "tool_choice" not in b,
            json.dumps([t.get("name") for t in b.get("tools") or []]))
    else:
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
        **({"tools": [{k: t.get(k) for k in ("name", "description", "input_schema")} for t in b.get("tools") or []]}
           if tools else {}),
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
        if uses_tools(cfg, q["source"]):
            kinds.append("tools")
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
    if not qids and review:  # two review questions, and one that goes with the calc tool when any does
        rows = review_rows(cfg, app, pc)
        tooled = [q for q in rows if uses_tools(cfg, fetch_question(app, q)["source"])]
        qids = list(dict.fromkeys(rows[:2] + tooled[:1]))
    qids = qids or verify_samples(cfg, app, pc)
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
        tools = uses_tools(cfg, q["source"])
        # (the tools prompt is the solver prompt plus the tool section: the API's prompt is checked on the others)
        sf, sys_text = write_system_file(cfg, tools=True) if tools else (system_file, system)
        captured, out = capture_request(qc, sf, text, effort, images, tools=tools)
        rep = check_request(qc, sys_text, text, effort, captured, out, set() if tools else shas, images, tools=tools)
        rep.update({"question_id": qid, "source": q["source"], "effort": effort, "model": qc["solver"]["model"],
                    "attempt": attempt, "with_feedback": bool(feedback), "images": len(images), "tools": tools,
                    "claude_code_version": rep["init"].get("claude_code_version")})
        reports.append(rep)
    # Claude Code's environment block names the model, so each model has a wrapping of its own (and the calc
    # tool's definition is part of it): one fingerprint per model, with and without the tool, each accepted.
    by_model: dict[tuple, set] = {}
    for r in reports:
        by_model.setdefault((r["model"], r.get("tools", False)), set()).add(r["fingerprint"])
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
                  f"{', ' + str(r['images']) + ' image(s)' if r['images'] else ''}"
                  f"{', with the calc tool' if r.get('tools') else ''}):")
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


def cut_off(ev: list, turn: dict, init: dict, limits: list, cfg: dict, tools_mode: bool = False) -> dict:
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
    if tools_mode and msgs:  # the reply is the message being written when the turn came, after any tool calls
        msgs = [m for m in msgs if m.get("id") == msgs[-1].get("id")]
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
    if not init:  # claude never started (2026-11-25: exit 0xC0000142, Windows out of memory): a failure, tried again
        return {"kind": "error", "why": f"claude did not start (exit {out.get('returncode')})"
                                        + (f": {out['stderr'][:200]}" if out.get("stderr") else "")}
    if init.get("claude_code_version") != version:
        return {"kind": "stop", "why": f"Claude Code is now {init.get('claude_code_version')}, verified {version}"}
    if init.get("apiKeySource") != "none":
        return {"kind": "stop", "why": f"not logged in with the subscription (apiKeySource={init.get('apiKeySource')})"}
    tools_mode = bool(out.get("tools"))
    if tools_mode:  # only the calc tool, from a server that connected; anything else stops the run
        servers = {s.get("name"): s.get("status") for s in init.get("mcp_servers") or []}
        if init.get("tools") != [CALC_TOOL] or servers != {"calc": "connected"}:
            return {"kind": "stop", "why": f"tools mode: tools {init.get('tools')}, MCP servers {servers}"}
    turn = next((e for e in ev if e.get("type") == "user" and not (tools_mode and tool_results_only(e))), None)
    if turn is not None:
        return cut_off(ev, turn, init, limits, cfg, tools_mode)
    rejected = [li for li in limits if li.get("status") == "rejected"]
    if result is None or result.get("is_error") or result.get("subtype") != "success":
        msg = (result or {}).get("result") or out.get("stderr", "")
        if rejected or (result or {}).get("api_error_status") == 429 or LIMIT_TEXT_RE.search(str(msg)):
            reset = next((li.get("resetsAt") for li in rejected if li.get("resetsAt")), None) or reset_from_text(str(msg))
            return {"kind": "limited", "why": str(msg)[:200], "resets_at": reset}
        if (result or {}).get("subtype") == "error_max_turns":
            return {"kind": "error", "why": f"used all {result.get('num_turns')} turns without a final reply"}
        return {"kind": "error", "why": str(msg)[:300] or f"exit code {out.get('returncode')}"}
    msgs = [e["message"] for e in ev if e.get("type") == "assistant" and e.get("message")]
    ids = list(dict.fromkeys(m.get("id") for m in msgs))
    model = cfg["solver"]["model"]
    calls = sum(1 for m in msgs for c in m.get("content", []) if c.get("type") == "tool_use")
    if tools_mode:  # the reply is the last message; every earlier one ended in a tool call
        if not msgs or any(c.get("type") == "tool_use" for m in msgs if m.get("id") == ids[-1] for c in m.get("content", [])):
            return {"kind": "error", "why": "tools mode: the last message is a tool call, not a reply"}
        msgs = [m for m in msgs if m.get("id") == ids[-1]]
    elif len(ids) != 1 or result.get("num_turns") != 1:
        return {"kind": "error", "why": f"not a single reply ({len(ids)} messages, {result.get('num_turns')} turns)"}
    if any(m.get("model") != model for m in msgs):
        return {"kind": "error", "why": f"answered by {sorted({m.get('model') for m in msgs})}, not {model}"}
    if result.get("fast_mode_state") not in (None, "off"):
        return {"kind": "stop", "why": f"fast mode is {result.get('fast_mode_state')}"}
    text = "".join(c.get("text", "") for m in msgs for c in m.get("content", []) if c.get("type") == "text")
    if text != (result.get("result") or ""):
        return {"kind": "error", "why": "reply text and result text differ"}
    return {"kind": "ok", "text": text, "result": result, "init": init, "model": msgs[0].get("model"),
            "warning": any(li.get("status") == "allowed_warning" for li in limits),
            **({"tool_calls": calls, "turns": result.get("num_turns")} if tools_mode else {})}


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
        **({"account_usage": info["account_usage"]} if info.get("account_usage") else {}),
        **({"tools": {"tool": CALC_TOOL, "calls": info.get("tool_calls"), "turns": info.get("turns"),
                      "log": f"tools_{attempt}.jsonl", "cost_usd": res.get("total_cost_usd")}}
           if info.get("tool_calls") is not None else {}),
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
              + (f", sent with {len(images)} image(s)" if images else "")
              + (f", {info['tool_calls']} calc tool call(s) in {info.get('turns')} turns" if info.get("tool_calls") is not None else ""))


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


SUBJECTS_LOCK = PIPELINE_DIR / "run_subjects.lock"  # run_subjects.py's: one solver at a time, so one account serves
CLASSIFY_LOCK = PIPELINE_DIR / "run_classify.lock"  # run_classify.py's (classification batches on the same accounts)


def acquire_lock(force: bool) -> None:
    if CLASSIFY_LOCK.exists():
        raise SystemExit(f"a classification run is going ({CLASSIFY_LOCK.as_posix()}, pid {CLASSIFY_LOCK.read_text().strip()}): "
                         "one at a time, so that only one account serves; wait for it or remove a stale lock")
    if SUBJECTS_LOCK.exists():
        raise SystemExit(f"the subjects solver is running ({SUBJECTS_LOCK.as_posix()}, pid {SUBJECTS_LOCK.read_text().strip()}): "
                         "one solver at a time, so that only one account serves; wait for it or remove a stale lock")
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


# --- usage cap ---------------------------------------------------------------------
# Owner 2026-11-19: "do not exceed 90% of usage on any account." Each claude run reports the
# account's usage when it started (rate_limit_event: utilization 0-1 per window, every window of
# the plan; a model's own window only on that model's requests).
ACCOUNT_FILE = Path.home() / ".claude.json"  # Claude Code's settings: oauthAccount is the logged-in account
LOGIN_FILE = Path.home() / ".claude" / ".credentials.json"  # its timestamp names the login where there is no oauthAccount
CAP_STATE = PIPELINE_DIR / "usage_cap_state.json"  # the readings so far, per account
SHARED_WINDOWS = {"five_hour", "seven_day"}  # count every model's replies; other windows only their model's
PERIOD = {"five_hour": 5 * 3600}  # a window's length: its period is the one ending at the reading's reset
PROBE_SYSTEM, PROBE_TEXT = "Reply with the single word OK.", "OK?"
PROBE_RETRY = 300  # seconds before a probe that brought no reading goes again


def logged_in_account(account_file: Path | None, login_file: Path | None) -> str | None:
    """A name for the logged-in account: a hash of Claude Code's oauthAccount.accountUuid (a token
    refresh rewrites the login file but keeps the account), else the login file's timestamp; None
    while the settings cannot be read (Claude Code may be writing them)."""
    acct = None
    if account_file:
        try:
            acct = (json.loads(account_file.read_text(encoding="utf-8")).get("oauthAccount") or {}).get("accountUuid")
        except FileNotFoundError:
            pass
        except (OSError, ValueError, AttributeError):
            return None
    if acct:
        return "account " + hashlib.sha256(str(acct).encode()).hexdigest()[:12]
    try:
        return f"login {login_file.stat().st_mtime_ns}" if login_file else "unknown"
    except OSError:
        return "unknown"


# --- account rotation (owner 2026-11-21) --------------------------------------------------
# Several accounts, each logged in once under its own Claude Code config directory; the solver uses
# one at a time, in the accounts file's order. When the active one reaches a stop, the replies still
# running finish and the run moves to the first account in the list that is on, logged in and free.
# Never two accounts serving at once (Anthropic advised rotation, not a "serving" system).

ACCOUNTS_FILE = PIPELINE_DIR / "accounts.json"  # git-ignored: names, config dirs, on/off, in serving order
ACCOUNTS_HOME = Path.home() / ".claude-accounts"  # where `accounts add` puts an account's config dir
ACCOUNTS_NOTE = ("Owner 2026-11-21: the solver rotates through these accounts one at a time, in this order. When the "
                 "active one reaches a stop, the replies still running finish and the run moves to the first account "
                 "here that is on, logged in and free. Each account logs in once under its own dir: in a terminal, "
                 "set CLAUDE_CONFIG_DIR to it, run claude, type /login. Edit with run_sub.py accounts.")
_ACTIVE_DIR: list[str | None] = [None]  # the config dir new claude runs start with (None: the default login)


def load_accounts(path: Path | None = None) -> list[dict]:
    """The accounts file's list in serving order ([{"name", "dir", "enabled"}]); [] without the file,
    and then the solver uses Claude Code's default login as before."""
    try:
        return list(json.loads((path or ACCOUNTS_FILE).read_text(encoding="utf-8")).get("accounts") or [])
    except FileNotFoundError:
        return []


def save_accounts(accounts: list[dict], path: Path | None = None) -> None:
    path = path or ACCOUNTS_FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"note": ACCOUNTS_NOTE, "accounts": accounts}, indent=1), encoding="utf-8")
    tmp.replace(path)


def accounts_mtime(path: Path | None = None) -> float | None:
    try:
        return (path or ACCOUNTS_FILE).stat().st_mtime
    except OSError:
        return None


def account_files(a: dict) -> tuple[Path, Path]:
    """Claude Code's settings and login files in an account's own config dir."""
    d = Path(a["dir"])
    return d / ".claude.json", d / ".credentials.json"


def account_id(a: dict) -> str | None:
    """The account logged in under `a`'s dir (named as logged_in_account names it), None if none is."""
    acct = logged_in_account(*account_files(a))
    return acct if acct and acct.startswith("account ") else None


def pick_account(accounts: list[dict], cap: "UsageCap", models, now: float | None = None,
                 skip=(), strict: bool = False, since: bool = False) -> tuple[dict | None, tuple[float, str] | None]:
    """The first account in serving order that is on, logged in, not in `skip` and not blocked by its
    own readings for `models`, else (None, (the earliest time one of them frees, why)). An account with
    room for cap.room replies at once goes before one near its stop; with strict, only such an account.
    With since, an account's replies that ended after its last reading count against it (UsageCap.blocked)."""
    holds, near = [], None
    for a in accounts:
        if not a.get("enabled", True) or a["name"] in skip:
            continue
        acct = account_id(a)
        if acct is None:
            continue
        b = cap.blocked(acct, models, now, since=since)
        if b is not None:
            holds.append((b[0], f"{a['name']}: {b[1]}"))
        elif cap.room <= 1 or cap.blocked(acct, models, now, cap.room, since=since) is None:
            return a, None
        else:
            near = near or a
    if near is not None and not strict:
        return near, None
    return None, (min(holds) if holds else None)


def tail_move(cap: "UsageCap", active: dict, models, now: float | None = None) -> dict | None:
    """Account rotation before a stop: if the account in use has room for fewer than cap.room replies at
    once of every one of `models` (the last stretch before its stop, where the cap lets one or two go at a
    time), the first other account with room for cap.room, to move to once the running replies are done;
    else None. The stretch left is not lost: a later stop takes the account back while its window lasts.
    (2026-11-23: a 6-worker run spent 20 min under one reply a minute on an account at 68% of its 70%
    stop while three accounts sat free.) The other account is judged as the one in use is, with the replies
    since its last reading (2026-11-26: judged without them, an account just left at its stop looked free,
    and two accounts handed the run back and forth, each move waiting for the running replies.)"""
    now = now if now is not None else time.time()
    if cap.room <= 1 or not models or any(cap.unread(m, now) or not cap.over(m, [(m, now)] * (cap.room - 1), now)
                                          for m in models):
        return None
    return pick_account(load_accounts(), cap, models, now, skip={active["name"]}, strict=True, since=True)[0]


def use_account(a: dict, cap: "UsageCap") -> None:
    """From now on new claude runs start under `a`'s login, and `cap` counts on its readings."""
    _ACTIVE_DIR[0] = str(Path(a["dir"]))
    cap.switch(*account_files(a), name=a["name"])


def usage_readings(out: dict) -> dict[str, tuple[float, float | None]]:
    """{window: (utilization, resets_at)} from a run's rate_limit_events (the highest if several)."""
    got: dict[str, tuple[float, float | None]] = {}
    for e in out.get("events") or []:
        if e.get("type") != "rate_limit_event":
            continue
        li = e.get("rate_limit_info") or {}
        wins = {w: (v.get("utilization"), v.get("resetsAt")) for w, v in (li.get("unifiedWindows") or {}).items()}
        if li.get("rateLimitType"):
            u = 1.0 if li.get("status") == "rejected" else li.get("utilization")
            if u is not None and (wins.get(li["rateLimitType"], (None,))[0] or 0) < u:
                wins[li["rateLimitType"]] = (u, li.get("resetsAt"))
        for w, (u, reset) in wins.items():
            if u is not None and (w not in got or float(u) > got[w][0]):
                got[w] = (float(u), reset)
    return got


def spent_usd(out: dict, info: dict, usd_per_token: float) -> float:
    """What a run cost (Claude Code's total_cost_usd), or its output tokens at usd_per_token when the
    run was cut off before Claude Code's count."""
    res = next((e for e in reversed(out.get("events") or []) if e.get("type") == "result"), None) or {}
    if info.get("kind") != "cut":
        if res.get("total_cost_usd") is not None:
            return float(res["total_cost_usd"])
        if res.get("modelUsage"):
            return sum(float(v.get("costUSD") or 0) for v in res["modelUsage"].values())
    tokens = ((info.get("result") or {}).get("usage") or {}).get("output_tokens")
    if tokens is None:
        tokens = max((e.get("estimated_tokens") or 0 for e in out.get("events") or []
                      if e.get("type") == "system" and e.get("subtype") == "thinking_tokens"), default=0)
    return float(tokens) * usd_per_token


class UsageCap:
    """Sends a question only if every usage window its model counts toward stays at or under `max`
    less `margin`: the latest reading, plus the cost of the replies finished since, plus every reply
    still running and this one at the most a reply of its model can cost (its output token limit;
    reply_max_usd, or the dearest seen), times the window's usage per USD. Usage is counted when a
    reply finishes and the readings do not lag (2026-11-19: reading = 0.008 + 0.0215 x cost finished,
    within rounding), so this holds the window under the cap whatever the running replies turn out
    to cost; as usage rises fewer run at once. (Valuing them at their expected cost instead ended a
    window near 0.97, then 0.90: the ones still running are the long, costly ones, and a reply that
    runs to its token limit costs about 8% of a five-hour window.) Usage per USD is fitted from the
    readings once they span enough cost (rounded up a step of 0.01), else the cautious prior in
    config. Nothing goes on a guess: every window a question counts toward needs a reading from the
    last reading_max_age_min, and where one is missing (a new account, a reset window, a model not
    asked for a while) a one-word probe (read_usage) reads it first. Readings are kept per account
    (logged_in_account), so a /login back to an account resumes what was known of it; a reply is
    counted on the account it started under. `running` is a list of (model, start time) on the
    current account."""

    def __init__(self, conf: dict, login_file: Path | None = None, state_file: Path | None = None,
                 account_file: Path | None = None):
        self.max = float(conf.get("max", 0.9))
        self.plan = self.max - float(conf.get("margin", 0.01))  # room for rounding, the fit's error and interactive use
        # a window's own margin: more room in the five-hour window for interactive Claude Code work,
        # which the solver cannot see, without lowering what the weekly windows may reach
        self.plans = {w: self.max - float(m) for w, m in (conf.get("margin_by_window") or {}).items()}
        # once: [{"window": w, "max": m, "until": ISO time, "account": label}, ...] (or {window: {...}}): an
        # owner's one-offs, each for one window period of one account, ending at its reset
        raw = conf.get("once") or []
        raw = [dict(o, window=w) for w, o in raw.items()] if isinstance(raw, dict) else raw
        self.once = [(o["window"], float(o["max"]), datetime.fromisoformat(o["until"]).timestamp(), o.get("account"))
                     for o in raw]
        # hours: [{"window": w, "max": m, "from": "HH:MM", "to": "HH:MM"}, ...]: standing rules for every account,
        # a period of w that lies wholly between from and to of one day, local time, may reach m
        self.hours = [(o["window"], float(o["max"]), o["from"], o["to"]) for o in conf.get("hours") or []]
        # near_reset: [{"window": w, "max": m, "minutes": n}, ...]: standing rules for every account, a period of
        # w whose reset is at most n minutes away may reach m (what it has left would go unused)
        self.near_reset = [(o["window"], float(o["max"]), 60 * float(o["minutes"])) for o in conf.get("near_reset") or []]
        self.prior ={k: float(v) for k, v in (conf.get("prior_per_usd") or {}).items()}
        # account rotation: an account with room for fewer replies at once than this is near its stop, and the
        # rotation moves to one with room once its running replies are done (tail_move)
        self.room = max(1, int(conf.get("rotate_room", 1)))
        self.worst = {m: float(v) for m, v in (conf.get("reply_max_usd") or {}).items()}
        self.scale = float(conf.get("reply_cost_scale", 1.0))  # owner 2026-11-20: worst cases scaled down (0.5)
        self.max_age = 60 * float(conf.get("reading_max_age_min", 20))  # older: the account's owner may have used it since
        self.login_file, self.account_file = login_file, account_file
        self.state_file = state_file  # what is known of each account, so a restart does not start blind
        self.accounts: dict[str, dict] = {}  # account -> {"points": [(start, model, {window: (u, reset)})],
        #                                                  "done": [(finished, usd, model)]}
        self.hist: dict[str, list[tuple[float, float]]] = {}  # model -> (seconds, usd) of its finished replies
        self.tokens = [0.0, 0.0]  # usd, output tokens of the costed replies: usd per token for cut-off runs
        self.probed: dict[str, float] = {}  # model -> when its last probe went (this account)
        self.active_name: str | None = None  # account rotation: the accounts file's name for the account in use
        self._load()
        self.account = None
        for _ in range(10):  # None while Claude Code writes its settings
            self.account = logged_in_account(account_file, login_file)
            if self.account:
                break
            time.sleep(0.2)
        self.account = self.account or "unknown"

    @property
    def points(self) -> list:
        return self._acct()["points"]

    @property
    def done(self) -> list:
        return self._acct()["done"]

    def _acct(self, account: str | None = None) -> dict:
        return self.accounts.setdefault(account or self.account, {"points": [], "done": []})

    def _load(self) -> None:
        try:
            s = json.loads(self.state_file.read_text(encoding="utf-8")) if self.state_file else None
        except (OSError, ValueError):
            s = None
        if s:
            self.hist = {m: [tuple(x) for x in xs] for m, xs in (s.get("hist") or {}).items()}
            self.tokens = list(s.get("tokens") or self.tokens)
            self.accounts = {a: {"points": [(t, m, {w: tuple(v) for w, v in r.items()}) for t, m, r in st.get("points") or []],
                                 "done": [tuple(x) for x in st.get("done") or []]}
                             for a, st in (s.get("accounts") or {}).items()}

    def _save(self) -> None:
        if not self.state_file:
            return
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"accounts": {a: {"points": st["points"][-2000:], "done": st["done"][-4000:]}
                                                for a, st in self.accounts.items()},
                                   "tokens": self.tokens, "hist": {m: xs[-2000:] for m, xs in self.hist.items()},
                                   "active": {"account": self.account, "name": self.active_name}}),
                       encoding="utf-8")
        tmp.replace(self.state_file)

    def switch(self, account_file: Path, login_file: Path, name: str | None = None) -> None:
        """Account rotation: another account's login from now on, with its own readings and probes."""
        self.account_file, self.login_file, self.active_name = account_file, login_file, name
        self.account = logged_in_account(account_file, login_file) or "unknown"
        self.probed = {}
        self._save()

    def blocked(self, account: str, models, now: float | None = None, room: int = 1,
                since: bool = False) -> tuple[float, str] | None:
        """Account rotation: (when it frees, why) if `account`'s last readings alone keep every one of
        `models` from going (`room` replies of it at once), else None. A reading that is old, or past the
        stop only by the replies since, does not block: the probe after a switch reads the account again.
        With since, the replies that ended after the reading count too (at their estimated cost)."""
        now = now if now is not None else time.time()
        saved, self.account = self.account, account
        try:
            holds = []
            for m in models:
                over = self.over(m, [(m, now)] * (room - 1), now, since=since)
                if not over:
                    return None
                ends = [self.resume_at(w, now) for w, _ in over]  # a near_reset stretch frees it before the reset
                until = max(ends) if all(e is not None for e in ends) else now + 1020
                holds.append((until, ", ".join(f"{w} at {self._last(w, now)[1]:.0%}" for w, _ in over)))
            return min(holds) if holds else None
        finally:
            self.account = saved

    def login_changed(self) -> bool:
        """Whether another account is logged in now (then its own readings apply)."""
        acct = logged_in_account(self.account_file, self.login_file)
        if acct is None or acct == self.account:
            return False
        self.account, self.probed = acct, {}
        self._save()
        return True

    def forget(self, model: str) -> None:
        """Drop this account's readings from `model`'s runs (its owner reset that model's limit): nothing
        of `model` goes before a probe reads its windows again."""
        self._acct()["points"] = [p for p in self.points if p[1] != model]
        self.probed.pop(model, None)
        self._save()

    def usd_per_token(self) -> float:
        return self.tokens[0] / self.tokens[1] if self.tokens[1] > 1e5 else 3e-5

    def record(self, model: str, start: float, end: float, readings: dict, usd: float, tokens: int = 0,
               account: str | None = None, probe: bool = False) -> None:
        """A finished run of `model` (on `account`, the one it started under; default the current one)."""
        if usd > 0 and not probe:
            self.hist.setdefault(model, []).append((max(end - start, 0.0), usd))
            if tokens:
                self.tokens[0] += usd
                self.tokens[1] += tokens
        st = self._acct(account)
        st["done"].append((end, usd, model))
        for w, (u, _) in readings.items():
            prev = [(t, r) for t, _, r in st["points"] if w in r and t < start and _live(r[w], end)]
            if prev and u < max(prev, key=lambda p: p[0])[1][w][0] - 0.02:  # the window reset since
                for _, r in prev:
                    r[w] = (r[w][0], start)  # ended
        if readings:
            st["points"].append((start, model, dict(readings)))
        self._save()

    def _readings(self, w: str, now: float) -> list[tuple[float, float, float | None]]:
        """(start, utilization, reset) of window w's readings in its current period, oldest first."""
        return sorted(((t, r[w][0], r[w][1]) for t, _, r in self.points if w in r and _live(r[w], now)),
                      key=lambda x: x[0])

    def _last(self, w: str, now: float):
        pts = self._readings(w, now)
        return pts[-1] if pts else None

    def _counts(self, w: str, model: str) -> bool:
        return w in SHARED_WINDOWS or any(m == model and w in r for _, m, r in self.points)

    def _windows(self, model: str, now: float) -> set[str]:
        return {w for _, m, r in self.points for w, v in r.items() if (w in SHARED_WINDOWS or m == model) and _live(v, now)}

    def _per_usd(self, w: str, now: float) -> float:
        prior = self.prior.get(w, self.prior.get("default", 0.05))
        pts = self._readings(w, now)
        if len(pts) < 2:
            return prior
        (t0, u0, _), (t1, u1, _) = pts[0], pts[-1]
        span = sum(usd for end, usd, m in self.done if t0 < end <= t1 and self._counts(w, m))
        if span >= 3 and (u1 - u0 >= 0.03 or span >= 15):
            return (max(u1 - u0, 0.0) + 0.01) / span
        return prior

    def most(self, model: str) -> float:
        """The most a reply of `model` is counted at while it runs: reply_max_usd (its output token limit)
        or the dearest seen, times reply_cost_scale."""
        seen = max((c for _, c in self.hist.get(model) or []), default=0.0)
        return self.scale * max(self.worst.get(model, 4.0), seen)

    def projected(self, w: str, model: str, running: list[tuple[str, float]], now: float, since: bool = True) -> float:
        t, u, _ = self._last(w, now)
        after = sum(usd for end, usd, m in self.done if end > t and self._counts(w, m)) if since else 0.0
        flights = [m for m, _ in running if self._counts(w, m)] + [model]
        return u + self._per_usd(w, now) * (after + sum(self.most(m) for m in flights))

    def plan_for(self, w: str, now: float) -> float:
        """Where `w` stops: max less its margin, or an owner's one-off max until the time it names, on the
        account it names (another account keeps the usual stop), or else the highest of the standing rules
        that apply: an hours rule's max when the current period lies wholly within its hours, a near_reset
        rule's max when the period resets within its minutes."""
        for win, top, until, acct in self.once:
            if win == w and now < until and acct in (None, self.account):
                return top
        stop = self.plans.get(w, self.plan)
        last = self._last(w, now)
        if last is not None and last[2] is not None:
            reset = float(last[2])
            for win, top, secs in self.near_reset:
                if win == w and 0 < reset - now <= secs:
                    stop = max(stop, top)
            if w in PERIOD:
                end = datetime.fromtimestamp(reset)
                start = end - timedelta(seconds=PERIOD[w])
                for win, top, frm, to in self.hours:
                    if (win == w and start.date() == end.date() and start.strftime("%H:%M:%S") >= f"{frm}:00"
                            and end.strftime("%H:%M:%S") <= f"{to}:00"):
                        stop = max(stop, top)
        return stop

    def resume_at(self, w: str, now: float) -> float | None:
        """When window `w`, past its stop on its reading alone, may serve again: its reset, or the start of a
        near_reset rule's stretch before the reset when the reading is under that rule's max."""
        last = self._last(w, now)
        if last is None or last[2] is None:
            return None
        reset = float(last[2])
        early = [reset - secs for win, top, secs in self.near_reset if win == w and last[1] < top and reset - secs > now]
        return min(early, default=reset)

    def over(self, model: str, running: list[tuple[str, float]], now: float | None = None,
             since: bool = True) -> list[tuple[str, float]]:
        """The windows with a current reading that a question of `model` would take past the cap (with
        since=False, leaving out the replies that ended after the reading: what a new reading cannot undo)."""
        now = now if now is not None else time.time()
        out = []
        for w in sorted(self._windows(model, now)):
            p = self.projected(w, model, running, now, since)
            if p > self.plan_for(w, now):
                out.append((w, p))
        return out

    def unread(self, model: str, now: float | None = None) -> list[str]:
        """The windows a question of `model` counts toward without a reading from the last max_age
        (all, if `model` has not been asked on this account): a probe reads them."""
        now = now if now is not None else time.time()
        mine = [(t, r) for t, m, r in self.points if m == model]
        if not mine:
            return ["all"]
        need = set(max(mine, key=lambda p: p[0])[1]) | {w for _, _, r in self.points for w in r if w in SHARED_WINDOWS}
        return sorted(w for w in need if (last := self._last(w, now)) is None or last[0] < now - self.max_age)

    def probe_due(self, model: str, running: list[tuple[str, float]], now: float | None = None) -> bool:
        """Whether to read the account's usage before a question of `model`: a window it counts toward
        has no recent reading, its last reading would let it go (a window the reading itself puts past
        the cap waits for its reset instead; one past it only by the replies since, at their estimated
        cost, is read again), and no probe for it went in the last PROBE_RETRY seconds."""
        now = now if now is not None else time.time()
        if not self.unread(model, now) or now - self.probed.get(model, float("-inf")) < PROBE_RETRY:
            return False
        return not self.over(model, running, now, since=False)

    def allows(self, model: str, running: list[tuple[str, float]], now: float | None = None) -> bool:
        return not self.unread(model, now) and not self.over(model, running, now)

    def held_until(self, model: str, now: float | None = None) -> tuple[float, str] | None:
        """With nothing running: (when a question of `model` may go, why), or None if it may go now."""
        now = now if now is not None else time.time()
        over = self.over(model, [], now)
        if over:
            why = ", ".join(f"{w} at {self._last(w, now)[1]:.0%} ({p:.0%} projected)" for w, p in over)
            if self.over(model, [], now, since=False):
                ends = [self.resume_at(w, now) for w, _ in over]
                until = max(ends) if all(e is not None for e in ends) else now + 1020
            else:  # past the cap only by the replies since the reading: read again once it is stale
                read = min(self._last(w, now)[0] for w, _ in over) + self.max_age + 1
                until = max(read, now + 60, self.probed.get(model, now) + PROBE_RETRY)
            return until, f"usage cap {self.max:.0%} for {model}: {why}"
        unread = self.unread(model, now)
        if unread:  # its probe brought no reading: tried again
            return max(now + 60, self.probed.get(model, now) + PROBE_RETRY), f"no usage reading for {model}: {', '.join(unread)}"
        return None


def _live(reading: tuple, now: float) -> bool:
    """Whether a (utilization, reset) reading is of the window's current period."""
    return reading[1] is None or float(reading[1]) > now


def read_usage(cfg: dict, model: str, version: str, cap: UsageCap, where: Path) -> dict:
    """Ask `model` for one word: the run's rate_limit_event gives the account's usage of every window a
    question of that model counts toward, for a fraction of a cent, so no question goes before the
    account's usage is known (one that runs to its token limit costs ~8% of a five-hour window).
    Returns the run's interpretation (limited: the account or the model is at its limit)."""
    path = where / ".amplify-usage-probe-prompt.txt"
    if not path.exists():
        path.write_text(PROBE_SYSTEM, encoding="utf-8")
    mcfg = cfg if model == cfg["solver"]["model"] else dict(cfg, solver=dict(cfg["solver"], model=model))
    cap.probed[model] = start = time.time()
    out = call_claude(mcfg, path, PROBE_TEXT, "low", None, [])
    info = interpret(out, mcfg, version)
    readings = usage_readings(out)
    cap.record(model, start, time.time(), readings, spent_usd(out, info, cap.usd_per_token()), probe=True)
    print(json.dumps({"usage_probe": model, "outcome": info["kind"], **({"why": info["why"]} if info["kind"] != "ok" else {}),
                      "usage": {w: u for w, (u, _) in readings.items()}, "at": now_iso()}), flush=True)
    return info


def workers_for(cfg: dict, effort: str, override: int | None = None) -> int:
    """How many claude processes may run while a question of this effort is next in line:
    --workers if given, else subscription.workers_by_effort, else subscription.workers."""
    if override:
        return override
    s = sub_cfg(cfg)
    return int((s.get("workers_by_effort") or {}).get(effort) or s.get("workers", 2))


def solve(cfg: dict, app, pc, n: int | None, ids: list[int] | None, workers: int | None, wait_on_limit: bool,
          force_unlock: bool, review: bool = False, reread: list[str] | None = None) -> None:
    """Send the unfinished questions; with review, the review solve (config.subscription.review_model
    at review_effort) for the questions review_rows names. Neither sends the stored answer."""
    rotation = [a for a in load_accounts() if a.get("enabled", True) and account_id(a)]
    if rotation:  # account rotation: the request check runs under the first account in serving order
        _ACTIVE_DIR[0] = str(Path(rotation[0]["dir"]))
    pre = verify(cfg, app, pc, quiet=True, review=review)
    if not pre["ok"] or not pre["accepted"]:
        raise SystemExit(f"the request check did not pass or its wrapping is not accepted; run `run_sub.py verify"
                         f"{' --review' if review else ''}` and read {VERIFY_REPORT.as_posix()}")
    version = pre["claude_code_version"]
    system_file, _ = write_system_file(cfg)
    system_files = {False: system_file}  # tools mode's own, when a question of config.tools.math_sources goes
    acquire_lock(force_unlock)
    ccfg = review_cfg(cfg) if review else cfg  # the model the requests go to and the replies are stored under
    queue = review_rows(cfg, app, pc, ids) if review else candidates(cfg, app, pc, ids)
    if n is not None:
        queue = queue[:n]

    def effort_of(qid: int, source: str) -> str:
        return sub_cfg(cfg)["review_effort"] if review else effort_for(cfg, source, qid)

    def model_of(qid: int) -> str:
        return ccfg["solver"]["model"] if review else model_for(cfg, qid)

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
            parked: dict[str, tuple[float, str]] = {}  # model -> (until, why): a limit on that model alone
            cap = UsageCap(sub_cfg(cfg).get("usage_cap") or {}, LOGIN_FILE, CAP_STATE, ACCOUNT_FILE)
            active = None  # account rotation: the accounts file's entry in use
            name_of: dict[str, str] = {}  # account -> its name in the accounts file
            if rotation:
                active = pick_account(load_accounts(), cap, sorted({model_of(x) for x in queue}))[0] or rotation[0]
                use_account(active, cap)
                name_of[cap.account] = active["name"]
                print(json.dumps({"rotation": [a["name"] for a in rotation], "account": active["name"], "at": now_iso()}), flush=True)
            for m in reread or []:
                cap.forget(m)
                print(json.dumps({"reread": m, "account": cap.account}), flush=True)
            started: dict = {}
            account_of: dict = {}  # the account each running reply started under
            seen_list = accounts_mtime()  # an edit of the accounts file (order, on/off) applies from then on
            tried: set[str] = set()  # accounts left since the last question went out: not taken again before a wait
            move_to = None  # an account to move to once the replies still running are done
            move_why = "serving order"
            off = False  # the active account is turned off and no other is free
            repick = False

            def models_left() -> list[str]:
                return sorted({model_of(x) for x in queue} - set(parked)) or sorted({model_of(x) for x in queue})

            def rotate_to(a: dict, why: str) -> None:
                nonlocal active
                before = active["name"]
                use_account(a, cap)
                active, name_of[cap.account] = a, a["name"]
                parked.clear()  # model limits are the account's own
                print(json.dumps({"rotate": {"from": before, "to": a["name"], "why": why}, "account": cap.account,
                                  "at": now_iso()}), flush=True)

            def on_limit(model: str, info: dict, readings: dict, probe: bool = False) -> None:
                """A limit on one model (its questions wait, the other models' go on): a refused probe
                (it asked for that model alone), the "switch to another model" message, or a refusal
                in which only windows of that model's own are full (an account whose Fable limit is used
                up); any other limit stops the run until its reset."""
                nonlocal stop_reason, paused_until
                if stop_reason is not None:
                    return
                full = {w for w, (u, _) in readings.items() if u >= 1.0}
                if probe or MODEL_LIMIT_RE.search(info["why"]) or (full and not full & SHARED_WINDOWS):
                    if model not in parked:  # polled every 17 min at most, as a usage limit is
                        until = min(float(info.get("resets_at") or time.time() + 900), time.time() + 1020)
                        parked[model] = (until, info["why"])
                        print(json.dumps({"parked": model, "until": datetime.fromtimestamp(until).strftime("%H:%M"),
                                          "why": info["why"]}), flush=True)
                else:
                    stop_reason, paused_until = "usage limit: " + info["why"], info.get("resets_at")

            while queue or running:
                if cap.login_changed():  # another account: its own usage, and its own model limits
                    parked.clear()
                    print(json.dumps({"login": "changed", "account": cap.account, "at": now_iso()}), flush=True)
                parked = {m: p for m, p in parked.items() if p[0] > time.time()}  # past its time: tried again
                if rotation:
                    if accounts_mtime() != seen_list:  # the owner edited the list: its order applies from now
                        seen_list, repick = accounts_mtime(), True
                    if repick:  # the first free account in serving order; a move waits for the running replies
                        repick = False
                        listed = load_accounts()
                        a = pick_account(listed, cap, models_left())[0]
                        off = a is None and not any(x["name"] == active["name"] and x.get("enabled", True) for x in listed)
                        move_to = a if a is not None and a["name"] != active["name"] else None
                        move_why = "serving order"
                        if move_to is not None and running:
                            print(json.dumps({"rotate_when_done": move_to["name"], "running": len(running)}), flush=True)
                    if move_to is not None and not running:
                        rotate_to(move_to, move_why)
                        move_to = None
                while queue and stop_reason is None and move_to is None and not off:
                    flying = [(v[4]["solver"]["model"], started[f]) for f, v in running.items() if account_of[f] == cap.account]
                    for m in sorted({model_of(x) for x in queue} - set(parked)):
                        if stop_reason is None and m not in parked and cap.probe_due(m, flying):
                            got = read_usage(cfg, m, version, cap, system_file.parent)
                            if got["kind"] == "limited":
                                on_limit(m, got, {}, probe=True)
                            elif got["kind"] == "stop" and stop_reason is None:
                                stop_reason, wait_on_limit = got["why"], False
                    if stop_reason is not None:
                        break
                    ok = {m for m in {model_of(x) for x in queue} - set(parked) if cap.allows(m, flying)}
                    i = next((i for i, x in enumerate(queue) if model_of(x) in ok), None)
                    if i is None:
                        break
                    q = fetch_question(app, queue[i])
                    if len(running) >= limits[effort_of(queue[i], q["source"])]:
                        break
                    qid = queue.pop(i)
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
                    tools = uses_tools(cfg, q["source"])
                    if tools not in system_files:
                        system_files[tools] = write_system_file(cfg, tools=True)[0]
                    fut = ex.submit(call_claude, qc, system_files[tools], user_text(q, feedback), effort, None, images,
                                    **({"tools_log": q_dir(qid) / f"tools_{attempt}.jsonl"} if tools else {}))
                    running[fut] = (qid, attempt, effort, [n for n, _ in images], qc)
                    started[fut], account_of[fut] = time.time(), cap.account
                    tried.clear()
                if rotation and queue and running and stop_reason is None and move_to is None and not off:
                    move_to = tail_move(cap, active, models_left())
                    if move_to is not None:
                        move_why = f"{active['name']} has room for fewer than {cap.room} replies at once"
                        print(json.dumps({"rotate_when_done": move_to["name"], "running": len(running), "why": move_why}), flush=True)
                if not running:
                    if not queue or stop_reason:
                        break
                    held = {} if off else {m: h for m in {model_of(x) for x in queue} - set(parked) if (h := cap.held_until(m))}
                    holds = {**parked, **held,
                             **({"off": (time.time() + 300, f"{active['name']} is turned off and no other account is free")} if off else {})}
                    if not holds:
                        break
                    until, why = min(holds.values())  # only parked or capped models' questions are left: wait as for a usage limit
                    stop_reason, paused_until = "usage limit: " + why, until
                    parked.clear()
                done = wait(running, return_when=FIRST_COMPLETED)[0] if running else set()
                for fut in done:
                    qid, attempt, effort, names, qc = running.pop(fut)
                    out = fut.result()
                    info = interpret(out, qc, version)
                    kind = info["kind"]
                    readings = usage_readings(out)
                    info["account_usage"] = readings
                    tokens = int(((info.get("result") or {}).get("usage") or {}).get("output_tokens") or 0) if kind == "ok" else 0
                    acct_of_reply = account_of.pop(fut)
                    cap.record(qc["solver"]["model"], started.pop(fut), time.time(), readings,
                               spent_usd(out, info, cap.usd_per_token()), tokens, acct_of_reply)
                    raw = save_failure(qid, attempt, out, info) if kind in ("error", "stop", "cut") else None
                    if kind in ("ok", "cut"):
                        store(pc, qc, qid, attempt, effort, info, out.get("seconds", 0), names)
                        summary["received" if kind == "ok" else info["result"]["stop_reason"]] += 1
                        if info["warning"]:
                            summary["limit_warnings"] += 1
                    elif kind == "limited":
                        queue.insert(0, qid)  # nothing was used up; it goes again first
                        summary["limited"] += 1
                        on_limit(qc["solver"]["model"], info, readings)
                    elif kind == "stop":
                        queue.insert(0, qid)
                        stop_reason = info["why"]
                        wait_on_limit = False
                    else:
                        summary[api_failure(pc, qc, qid, attempt, info["why"])] += 1
                    print(json.dumps({"question_id": qid, "attempt": attempt, "model": qc["solver"]["model"],
                                      "effort": effort, "outcome": kind,
                                      **({"account": name_of.get(acct_of_reply)} if rotation else {}),
                                      **({"tool_calls": info["tool_calls"]} if info.get("tool_calls") is not None else {}),
                                      "seconds": out.get("seconds"),
                                      **({"why": info["why"]} if kind != "ok" else {}), **({"raw": raw} if raw else {}),
                                      **({"usage": {w: u for w, (u, _) in readings.items()}} if readings else {}),
                                      "elapsed_min": round((time.time() - t0) / 60, 1), **summary}), flush=True)
                if stop_reason and not running:
                    if wait_on_limit and stop_reason.startswith("usage limit") and queue:
                        until = float(paused_until) if paused_until else time.time() + 900
                        if rotation:  # the next free account in serving order, before any wait
                            a, hold = pick_account(load_accounts(), cap, models_left(), skip=tried | {active["name"]})
                            if a is not None:
                                tried.add(active["name"])
                                rotate_to(a, stop_reason)
                                stop_reason = paused_until = None
                                continue
                            if hold:  # every account is held: wait for the first to free
                                until = min(until, hold[0])
                        secs = max(60, min(int(until - time.time()) + 120, 1020))  # short polls catch a /login switch
                        print(f"{stop_reason}; waiting {secs // 60} min, then continuing", flush=True)
                        deadline = time.time() + secs
                        while time.time() < deadline:  # by the clock: one long sleep does not count time the machine sleeps
                            time.sleep(min(60, max(1, deadline - time.time())))
                            if cap.login_changed():
                                parked.clear()
                                print(json.dumps({"login": "changed", "account": cap.account, "at": now_iso()}), flush=True)
                                break
                            if rotation and accounts_mtime() != seen_list:
                                break
                        stop_reason = paused_until = None
                        tried.clear()
                        repick = bool(rotation)
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


def show_accounts(cfg: dict, accts: list[dict], now: float | None = None) -> None:
    """Each account's windows (latest reading / where it stops, its reset), whether it is the one in use,
    free or held, and the pool: the windows' mean use over the accounts on, and the room left to their stops."""
    now = now if now is not None else time.time()
    cap = UsageCap(sub_cfg(cfg).get("usage_cap") or {}, None, CAP_STATE, None)
    try:
        active = json.loads(CAP_STATE.read_text(encoding="utf-8")).get("active") or {}
    except (OSError, ValueError):
        active = {}
    if not accts:
        print("no accounts file: the solver uses Claude Code's default login (add one: run_sub.py accounts add NAME)")
        return
    model = cfg["solver"]["model"]
    pool: dict[str, list[tuple[float, float]]] = {}
    print(f"{'#':>2} {'name':10} {'on':3} {'email':34} {'five_hour':20} {'seven_day':20} state")
    for i, a in enumerate(accts, 1):
        acct = account_id(a)
        try:
            email = (json.loads(account_files(a)[0].read_text(encoding="utf-8")).get("oauthAccount") or {}).get("emailAddress") or ""
        except (OSError, ValueError):
            email = ""
        cols = []
        if acct:
            cap.account = acct
            for w in ("five_hour", "seven_day"):
                last, stop = cap._last(w, now), cap.plan_for(w, now)
                ever = any(w in r for _, _, r in cap.points)
                u = last[1] if last else (0.0 if ever else None)  # a reading of an ended period: the window reset
                reset = f" ->{datetime.fromtimestamp(float(last[2])).strftime('%a %H:%M')}" if last and last[2] else ""
                cols.append(f"{u:.0%}/{stop:.0%}{reset}" if u is not None else "no reading")
                if u is not None and a.get("enabled", True):
                    pool.setdefault(w, []).append((u, stop))
            held = cap.blocked(acct, [model], now)
            newest = max((t for t, _, _ in cap.points), default=None)
            age = f", read {int((now - newest) // 60)} min ago" if newest else ""
            if not a.get("enabled", True):
                state = "off"
            elif acct == active.get("account") and a["name"] == active.get("name"):
                state = "IN USE" + (f" (stopped until {datetime.fromtimestamp(held[0]).strftime('%a %H:%M')})" if held else "") + age
            else:
                state = (f"held until {datetime.fromtimestamp(held[0]).strftime('%a %H:%M')} ({held[1]})" if held else "free") + age
        else:
            cols, state = ["", ""], "not logged in: set CLAUDE_CONFIG_DIR to its dir, run claude, /login"
        print(f"{i:>2} {a['name'][:10]:10} {'yes' if a.get('enabled', True) else 'no':3} {email[:34]:34} "
              f"{cols[0]:20} {cols[1]:20} {state}")
    for w, xs in pool.items():
        mean = sum(u for u, _ in xs) / len(xs)
        room = sum(max(0.0, s - u) for u, s in xs)
        print(f"   pool {w}: {mean:.0%} used on average over {len(xs)} accounts; room to the stops {room:.2f} windows")


def accounts_cmd(cfg: dict, action: str, names: list[str], directory: str | None) -> None:
    """run_sub.py accounts [list | add NAME [--dir D] | remove NAME... | order NAME... | swap A B | enable NAME... |
    disable NAME...]. A running solver applies an edit at once: it finishes the replies running, then moves."""
    accts = load_accounts()
    by = {a["name"]: a for a in accts}

    def need(n: str) -> dict:
        if n not in by:
            raise SystemExit(f"no account named {n!r}; the list has: {', '.join(by) or 'none'}")
        return by[n]

    if action == "add":
        if len(names) != 1:
            raise SystemExit("usage: run_sub.py accounts add NAME [--dir DIR]")
        n = names[0]
        if n in by:
            raise SystemExit(f"{n!r} is already in the list")
        d = Path(directory) if directory else ACCOUNTS_HOME / n
        d.mkdir(parents=True, exist_ok=True)
        accts.append({"name": n, "dir": d.as_posix(), "enabled": True})
        save_accounts(accts)
        print(f"added {n}, last in the serving order. Log it in once, in a PowerShell window:\n"
              f"  $env:CLAUDE_CONFIG_DIR = '{d}'; claude\nthen type /login, choose the account, and close that claude.\n")
    elif action == "remove":
        for n in names:
            need(n)
        save_accounts([a for a in accts if a["name"] not in names])
        print("removed; each login stays in its dir until that folder is deleted\n")
    elif action == "order":
        for n in names:
            need(n)
        save_accounts([by[n] for n in names] + [a for a in accts if a["name"] not in names])
    elif action == "swap":
        if len(names) != 2:
            raise SystemExit("usage: run_sub.py accounts swap A B")
        i, j = (accts.index(need(n)) for n in names)
        accts[i], accts[j] = accts[j], accts[i]
        save_accounts(accts)
    elif action in ("enable", "disable"):
        for n in names:
            need(n)["enabled"] = action == "enable"
        save_accounts(accts)
    show_accounts(cfg, load_accounts())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("verify")
    p.add_argument("--qid", type=int, action="append")
    p.add_argument("--accept", action="store_true")
    p.add_argument("--review", action="store_true", help="check a review solve (review model and effort)")
    sp.add_parser("status")
    p = sp.add_parser("accounts", help="the accounts the solver rotates through, one at a time, in serving order")
    p.add_argument("action", nargs="?", default="list",
                   choices=("list", "add", "remove", "order", "swap", "enable", "disable"))
    p.add_argument("names", nargs="*")
    p.add_argument("--dir", help="add: the account's own Claude Code config dir (default ~/.claude-accounts/NAME)")
    p = sp.add_parser("queue")
    p.add_argument("--n", type=int, default=20)
    for name in ("solve", "review"):
        p = sp.add_parser(name)
        p.add_argument("--n", type=int)
        p.add_argument("--ids")
        p.add_argument("--workers", type=int)
        p.add_argument("--wait-on-limit", action="store_true")
        p.add_argument("--force-unlock", action="store_true")
        p.add_argument("--reread", action="append", metavar="MODEL",
                       help="forget this account's readings from MODEL's runs (its limit was reset): a probe reads them again")
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
    elif a.cmd == "accounts":
        accounts_cmd(cfg, a.action, a.names, a.dir)
    elif a.cmd == "queue":
        for qid in candidates(cfg, app, pc)[: a.n]:
            q = fetch_question(app, qid)
            r = get_status(pc, qid)
            images, skip = attachments(cfg, q)
            print(json.dumps({"question_id": qid, "source": q["source"], "status": r["status"] if r else "new",
                              "will_skip": skip, "images": len(images)}))
    elif a.cmd == "solve":
        ids = [int(x) for x in a.ids.split(",") if x.strip()] if a.ids else None
        solve(cfg, app, pc, a.n, ids, a.workers, a.wait_on_limit, a.force_unlock, reread=a.reread)
    elif a.cmd == "review":
        ids = [int(x) for x in a.ids.split(",") if x.strip()] if a.ids else None
        if a.list:
            print(",".join(str(q) for q in review_rows(cfg, app, pc, ids)))
        else:
            solve(cfg, app, pc, a.n, ids, a.workers, a.wait_on_limit, a.force_unlock, review=True, reread=a.reread)


if __name__ == "__main__":
    main()
