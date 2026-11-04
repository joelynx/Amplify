"""Unattended full run on the subscription.

Runs `run_sub.py solve --wait-on-limit` and, while it runs, `run.py judge` every few hours at
below-normal priority (XeLaTeX), then once more when it ends. Replies the judge rejects become
retries, which the next solve round sends (a second failure goes to needs_human_review, so the
rounds end). Stops when a round receives nothing (the wrapping changed, a check failed, another
solve holds the lock, ...) or nothing is left to send.

Usage (from the repo root; start it detached so it outlives the terminal):
  python pipeline/scripts/run_sub_supervise.py [--judge-every-hours 3] [--judge-workers 2] [--max-rounds 4]

Logs: pipeline/run_sub.log (solve), pipeline/judge.log (judge), pipeline/run_sub_supervise.log (this).
To stop: end this process and the solve it started (pids in its log), then run
`run_sub.py solve --force-unlock ...` next time if the lock file was left behind.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import PIPELINE_DIR, app_conn, load_config, now_iso, pipe_conn  # noqa: E402
import run_sub  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent
LOG = PIPELINE_DIR / "run_sub_supervise.log"
SOLVE_LOG = PIPELINE_DIR / "run_sub.log"
JUDGE_LOG = PIPELINE_DIR / "judge.log"
BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


def log(**kw) -> None:
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now_iso(), **kw}) + "\n")


def count(sql: str) -> int:
    pc = pipe_conn()
    try:
        return pc.execute(sql).fetchone()[0]
    finally:
        pc.close()


def received() -> int:
    return count("SELECT COUNT(*) FROM status WHERE status='received'")


def sub_replies() -> int:
    return count(f"SELECT COUNT(*) FROM usage WHERE batch_id LIKE '{run_sub.BATCH_PREFIX}%'")


def left_to_send() -> int:
    cfg = load_config()
    app, pc = app_conn(cfg), pipe_conn()
    try:
        return len(run_sub.candidates(cfg, app, pc))
    finally:
        app.close()
        pc.close()


def judge(workers: int) -> None:
    n = received()
    if not n:
        return
    log(event="judge start", received=n)
    with open(JUDGE_LOG, "ab") as out:
        out.write(f"=== subscription judge {now_iso()} ({n} received)\n".encode())
        out.flush()
        code = subprocess.run([sys.executable, "-I", str(SCRIPTS / "run.py"), "judge", "--workers", str(workers)],
                              cwd=REPO, stdout=out, stderr=subprocess.STDOUT, creationflags=BELOW_NORMAL).returncode
    log(event="judge end", exit=code, still_received=received())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge-every-hours", type=float, default=3.0)
    ap.add_argument("--judge-workers", type=int, default=2)
    ap.add_argument("--max-rounds", type=int, default=4)
    a = ap.parse_args()
    log(event="supervisor start", pid=os.getpid(), **vars(a))
    for rnd in range(1, a.max_rounds + 1):
        before = sub_replies()
        with open(SOLVE_LOG, "ab") as out:
            out.write(f"=== round {rnd} {now_iso()}\n".encode())
            out.flush()
            p = subprocess.Popen([sys.executable, "-I", str(SCRIPTS / "run_sub.py"), "solve", "--wait-on-limit"],
                                 cwd=REPO, stdout=out, stderr=subprocess.STDOUT)
            log(event="solve start", round=rnd, pid=p.pid, left=left_to_send())
            while True:
                try:
                    p.wait(timeout=a.judge_every_hours * 3600)
                    break
                except subprocess.TimeoutExpired:
                    judge(a.judge_workers)
        got = sub_replies() - before
        log(event="solve end", round=rnd, exit=p.returncode, replies=got)
        judge(a.judge_workers)
        left = left_to_send()
        log(event="round done", round=rnd, replies=got, left=left)
        if got == 0 or left == 0:
            break
    log(event="supervisor end", left=left_to_send(), received=received())


if __name__ == "__main__":
    main()
