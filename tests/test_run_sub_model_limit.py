"""run_sub.py's solve loop when one model reaches its own limit ("You've reached your Fable limit.
Switch to another model to continue."): that model's questions wait while the other model's go on,
and once only theirs are left the run waits as for a usage limit and then sends them."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import run_sub  # noqa: E402

FABLE, OPUS = "claude-fable-5-2", "claude-opus-5-5"


class FakeTime:
    def __init__(self) -> None:
        self.now = 1_800_000_000.0
        self.slept = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, secs: float) -> None:
        self.now += secs
        self.slept += secs


def test_other_model_goes_on_while_one_is_limited(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "assign.json"
    models = {1: FABLE, 2: OPUS, 3: FABLE, 4: OPUS, 5: OPUS}
    path.write_text(json.dumps({"questions": {str(q): {"model": m, "effort": "high"} for q, m in models.items()}}),
                    encoding="utf-8")
    run_sub._ASSIGNED.clear()
    cfg = {"solver": {"model": OPUS, "effort": "medium", "max_tokens": 32000},
           "subscription": {"sources": ["S"], "assignments_file": str(path)}}
    clock = FakeTime()
    lift = clock.now + 600  # when the Fable limit is gone
    stored: list[int] = []

    def interpret(out: dict, qc: dict, version: str) -> dict:
        if qc["solver"]["model"] == FABLE and clock.now < lift:
            return {"kind": "limited", "why": "You've reached your Fable limit. Switch to another model to continue."}
        return {"kind": "ok", "warning": False}

    monkeypatch.setattr(run_sub, "time", clock)
    monkeypatch.setattr(run_sub, "verify", lambda *a, **k: {"ok": True, "accepted": True, "claude_code_version": "t"})
    monkeypatch.setattr(run_sub, "write_system_file", lambda cfg: (tmp_path / "system.md", None))
    monkeypatch.setattr(run_sub, "acquire_lock", lambda force: None)
    monkeypatch.setattr(run_sub, "LOCK", tmp_path / "run_sub.lock")
    monkeypatch.setattr(run_sub, "keep_awake", lambda on: None)
    monkeypatch.setattr(run_sub, "write_progress", lambda pc: None)
    monkeypatch.setattr(run_sub, "candidates", lambda cfg, app, pc, ids: list(models))
    monkeypatch.setattr(run_sub, "fetch_question", lambda app, qid: {"question_id": qid, "source": "S"})
    monkeypatch.setattr(run_sub, "attachments", lambda cfg, q: ([], None))
    monkeypatch.setattr(run_sub, "plan_attempt", lambda cfg, pc, qid, source: (1, None, False))
    monkeypatch.setattr(run_sub, "user_text", lambda q, feedback: str(q["question_id"]))
    monkeypatch.setattr(run_sub, "call_claude", lambda qc, sf, text, effort, mt, images: {"seconds": 1})
    monkeypatch.setattr(run_sub, "interpret", interpret)
    monkeypatch.setattr(run_sub, "store", lambda pc, qc, qid, *a: stored.append(qid))

    run_sub.solve(cfg, None, None, None, None, 1, True, False)

    assert stored == [2, 4, 5, 1, 3]  # Opus went on while Fable waited
    assert 0 < clock.slept <= 1020    # one wait, polled as a usage limit is
