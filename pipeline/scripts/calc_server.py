"""A one-tool MCP server (stdio) that lets the solver run Python to check its work.

Claude Code starts it per question (run_sub.py, tools mode: --mcp-config naming it and only
its tool allowed). The tool `python` runs the code it is given in a fresh process of the
calculation venv (pipeline/calc/.venv: numpy, scipy, sympy, mpmath, pint, CoolProp) under
calc_runner.py's restrictions, in a working folder of its own that lasts for this question only,
and returns what it printed. Every call and its output is appended to LOG (JSON lines), which
run_sub.py keeps beside the reply as tools_<n>.jsonl.

Usage: python -I calc_server.py --python CALC_PYTHON --log LOG [--timeout 60] [--max-calls 40]
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

RUNNER = Path(__file__).resolve().with_name("calc_runner.py")
MAX_OUT = 20_000
PROTOCOL = "2025-06-18"
DESCRIPTION = (
    "Run Python 3.12 to compute or check a result. Each call starts with a fresh namespace: variables "
    "do not carry over, but files written in the working folder do (for this question only). Ready: math, "
    "fractions, itertools, numpy as np, sympy as sp, scipy (constants, integrate, linalg, optimize, "
    "special, stats), mpmath, pint (ureg, Q_ for quantities with units), CoolProp (PropsSI(...) for "
    "fluid properties; also CP). No network, no other programs, no files outside the working folder. "
    f"Print what you need to see; output beyond {MAX_OUT} characters is cut.")


class Worker:
    """calc_runner.py kept running for the question; started again after a timeout or a crash."""

    START_SECONDS = 90  # the imports take ~5 s warm, longer on a cold disk

    def __init__(self, args, scratch: str) -> None:
        self.args, self.scratch, self.p, self.lines, self.ready = args, scratch, None, None, False

    def start(self) -> None:
        env = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE") if k in os.environ}
        env.update({"TEMP": self.scratch, "TMP": self.scratch, "PYTHONIOENCODING": "utf-8", "OMP_NUM_THREADS": "1",
                    "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "PATH": str(Path(self.args.python).parent)})
        self.p = subprocess.Popen([self.args.python, "-I", "-X", "utf8", str(RUNNER), self.scratch], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.scratch, env=env,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.lines, self.ready = queue.Queue(), False
        threading.Thread(target=self._read, args=(self.p, self.lines), daemon=True).start()

    @staticmethod
    def _read(p, lines) -> None:
        for raw in p.stdout:
            lines.put(raw.decode("utf-8", "replace"))
        lines.put(None)  # the worker ended

    def stop(self) -> None:
        if self.p is not None:
            self.p.kill()  # its job object goes with it
            self.p.wait()
        self.p = None

    def _reply(self, deadline: float) -> tuple[dict | None, str]:
        """The next JSON line, or (None, why); non-JSON lines (a crash's own output) are kept as text."""
        noise = []
        while True:
            try:
                line = self.lines.get(timeout=max(0.0, deadline - time.time()))
            except queue.Empty:
                return None, "".join(noise) + "\n[stopped: over the time limit]"
            if line is None:
                return None, "".join(noise) + "\n[the Python process ended; it is restarted for the next call]"
            try:
                return json.loads(line), ""
            except json.JSONDecodeError:
                noise.append(line)

    def run(self, code: str) -> tuple[str, bool]:
        if self.p is None or self.p.poll() is not None:
            self.start()
        if not self.ready:
            ready, why = self._reply(time.time() + self.START_SECONDS)
            if not (ready or {}).get("ready"):
                self.stop()
                return f"the Python process did not start: {why.strip()[-2000:]}", True
            self.ready = True
        self.p.stdin.write((json.dumps({"code": code}) + "\n").encode("utf-8"))
        self.p.stdin.flush()
        reply, why = self._reply(time.time() + self.args.timeout)
        if reply is None:
            self.stop()
            return why.strip().replace("over the time limit", f"over the {self.args.timeout} s time limit"), True
        out = reply.get("output") or ""
        if len(out) > MAX_OUT:
            out = out[:MAX_OUT] + f"\n[output cut at {MAX_OUT} characters]"
        return out or "(no output)", bool(reply.get("error"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--max-calls", type=int, default=40)
    args = ap.parse_args()
    scratch = os.path.realpath(tempfile.mkdtemp(prefix="amplify-calc-"))
    worker = Worker(args, scratch)
    worker.start()  # its imports run while Claude Code sets up; the first call waits for "ready"
    calls = 0
    stdin = sys.stdin.buffer
    out = sys.stdout.buffer

    def send(msg: dict) -> None:
        out.write((json.dumps(msg) + "\n").encode("utf-8"))
        out.flush()

    try:
        for raw in stdin:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                continue
            method, rid = req.get("method"), req.get("id")
            if rid is None:  # a notification (initialized, cancelled): nothing to answer
                continue
            if method == "initialize":
                send({"jsonrpc": "2.0", "id": rid, "result": {
                    "protocolVersion": (req.get("params") or {}).get("protocolVersion", PROTOCOL),
                    "capabilities": {"tools": {}}, "serverInfo": {"name": "calc", "version": "1"}}})
            elif method == "tools/list":
                send({"jsonrpc": "2.0", "id": rid, "result": {"tools": [{
                    "name": "python", "description": DESCRIPTION,
                    "inputSchema": {"type": "object", "properties": {"code": {"type": "string", "description": "Python source to run"}},
                                    "required": ["code"]}}]}})
            elif method == "tools/call":
                params = req.get("params") or {}
                code = str((params.get("arguments") or {}).get("code") or "")
                calls += 1
                t0 = time.time()
                if params.get("name") != "python":
                    text, err = f"unknown tool {params.get('name')!r}", True
                elif calls > args.max_calls:
                    text, err = f"call limit reached ({args.max_calls}): finish without the tool", True
                else:
                    text, err = worker.run(code)
                with open(args.log, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"call": calls, "seconds": round(time.time() - t0, 2), "error": err,
                                        "code": code, "output": text}, ensure_ascii=False) + "\n")
                send({"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}], "isError": err}})
            elif method == "ping":
                send({"jsonrpc": "2.0", "id": rid, "result": {}})
            else:
                send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"no method {method}"}})
    finally:
        worker.stop()
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
