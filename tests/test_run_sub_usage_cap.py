"""run_sub.py's usage cap (owner 2026-11-19: "do not exceed 90% of usage on any account"): a question
goes only if every usage window its model counts toward stays under the cap with every reply still
running, and this one, at the most a reply can cost; otherwise the run waits for the window's reset
or a new login."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import run_sub  # noqa: E402

FABLE, OPUS = "claude-fable-5-2", "claude-opus-5-5"
CONF = {"max": 0.9, "margin": 0.01, "prior_per_usd": {"five_hour": 0.05, "default": 0.05},
        "reply_max_usd": {FABLE: 3.6, OPUS: 2.8}}
NOW = 1_800_000_000.0


def test_readings_take_every_window_and_a_rejection() -> None:
    out = {"events": [{"type": "rate_limit_event", "rate_limit_info": {
                          "status": "allowed_warning", "rateLimitType": "five_hour", "utilization": 0.97,
                          "unifiedWindows": {"five_hour": {"utilization": 0.97, "resetsAt": NOW + 3600},
                                             "seven_day": {"utilization": 0.41, "resetsAt": NOW + 9e4}}}},
                      {"type": "rate_limit_event", "rate_limit_info": {
                          "status": "rejected", "rateLimitType": "seven_day_overage_included", "resetsAt": NOW + 60,
                          "unifiedWindows": {"five_hour": {"utilization": 0.2, "resetsAt": NOW + 3600}}}}]}
    got = run_sub.usage_readings(out)
    assert got["five_hour"][0] == 0.97 and got["seven_day"][0] == 0.41
    assert got["seven_day_overage_included"] == (1.0, NOW + 60)


def test_one_at_a_time_until_the_first_reading() -> None:
    cap = run_sub.UsageCap(CONF)
    assert cap.allows(FABLE, [], NOW)
    assert not cap.allows(FABLE, [(FABLE, NOW)], NOW)


def test_every_running_reply_counts_at_its_most() -> None:
    cap = run_sub.UsageCap(CONF)  # plans to 0.89
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.5, NOW + 3600)}, 0.4)
    # 0.5 + 0.05 * ($0.4 finished since + $3.6 for each running reply and this one)
    assert cap.allows(FABLE, [], NOW)                   # 0.70
    assert cap.allows(FABLE, [(FABLE, NOW)], NOW)       # 0.88
    assert not cap.allows(FABLE, [(FABLE, NOW)] * 2, NOW)
    cap.record(FABLE, NOW - 50, NOW - 5, {"five_hour": (0.86, NOW + 3600)}, 0.4)
    assert not cap.allows(FABLE, [], NOW)
    until, why = cap.held_until(FABLE, NOW)
    assert until == NOW + 3600 and "five_hour at 86%" in why


def test_the_most_a_reply_costs_is_the_larger_of_config_and_seen() -> None:
    cap = run_sub.UsageCap(CONF)
    assert cap.most(FABLE) == 3.6 and cap.most("claude-other") == 4.0
    cap.record(FABLE, NOW, NOW + 900, {}, 5.0)
    assert cap.most(FABLE) == 5.0


def test_a_models_own_window_holds_only_that_model() -> None:
    cap = run_sub.UsageCap(CONF)
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.2, NOW + 3600), "seven_day_overage_included": (0.95, NOW + 9e4)}, 0.4)
    cap.record(OPUS, NOW - 90, NOW - 20, {"five_hour": (0.2, NOW + 3600)}, 0.1)
    assert not cap.allows(FABLE, [], NOW)
    assert cap.allows(OPUS, [], NOW)


def test_usage_per_usd_is_fitted_from_the_readings() -> None:
    cap = run_sub.UsageCap(CONF)
    for i in range(7):  # 0.05 of five_hour per reply of $1: 0.10 at the first reading, 0.40 at the last
        cap.record(FABLE, NOW + 100 * i, NOW + 100 * i + 50, {"five_hour": (0.10 + 0.05 * i, NOW + 9e3)}, 1.0)
    assert abs(cap._per_usd("five_hour") - (0.30 + 0.01) / 6) < 1e-9


def test_a_reset_window_and_a_new_login_start_afresh(tmp_path: Path) -> None:
    login = tmp_path / "credentials.json"
    login.write_text("a")
    cap = run_sub.UsageCap(CONF, login)
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.95, NOW + 60)}, 0.4)
    assert not cap.allows(FABLE, [], NOW)
    assert cap.allows(FABLE, [], NOW + 61)  # the window reset
    cap.record(FABLE, NOW - 50, NOW - 5, {"five_hour": (0.95, NOW + 3600)}, 0.4)
    assert not cap.allows(FABLE, [], NOW)
    os.utime(login, ns=(1, 1))
    assert cap.login_changed(NOW)
    assert cap.allows(FABLE, [], NOW) and not cap.allows(FABLE, [(FABLE, NOW)], NOW)
    cap.record(FABLE, NOW - 50, NOW + 5, {"five_hour": (0.99, NOW + 3600)}, 0.4)  # started before the login
    assert cap.allows(FABLE, [], NOW)


def test_a_restart_keeps_what_it_knew_of_the_same_login(tmp_path: Path) -> None:
    login, state = tmp_path / "credentials.json", tmp_path / "state.json"
    login.write_text("a")
    cap = run_sub.UsageCap(CONF, login, state)
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.95, NOW + 3600)}, 0.4)
    again = run_sub.UsageCap(CONF, login, state)
    assert not again.allows(FABLE, [], NOW)  # it does not send blind to an account it knows is full
    os.utime(login, ns=(1, 1))
    fresh = run_sub.UsageCap(CONF, login, state)
    assert fresh.allows(FABLE, [], NOW) and fresh.hist[FABLE] == [(90.0, 0.4)]  # another login; reply costs kept


class FakeTime:
    def __init__(self) -> None:
        self.now = NOW
        self.slept = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, secs: float) -> None:
        self.now += secs
        self.slept += secs


def test_solve_waits_at_the_cap_for_the_reset(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "assign.json"
    ids = list(range(1, 8))
    path.write_text(json.dumps({"questions": {str(q): {"model": FABLE, "effort": "high"} for q in ids}}), encoding="utf-8")
    run_sub._ASSIGNED.clear()
    cfg = {"solver": {"model": OPUS, "effort": "medium", "max_tokens": 32000},
           "subscription": {"sources": ["S"], "assignments_file": str(path), "usage_cap": CONF}}
    clock = FakeTime()
    reset = NOW + 7200
    sent: list[float] = []

    def call(qc, sf, text, effort, mt, images):
        sent.append(clock.now)
        u = 0.0 if clock.now >= reset else 0.55 + 0.05 * len(sent)  # each $1 reply uses 5%
        clock.now += 30
        return {"seconds": 30, "events": [
            {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "unifiedWindows": {
                "five_hour": {"utilization": u, "resetsAt": reset}}}},
            {"type": "result", "total_cost_usd": 1.0}]}

    monkeypatch.setattr(run_sub, "time", clock)
    monkeypatch.setattr(run_sub, "LOGIN_FILE", tmp_path / "no-login.json")
    monkeypatch.setattr(run_sub, "CAP_STATE", tmp_path / "usage_cap_state.json")
    monkeypatch.setattr(run_sub, "verify", lambda *a, **k: {"ok": True, "accepted": True, "claude_code_version": "t"})
    monkeypatch.setattr(run_sub, "write_system_file", lambda cfg: (tmp_path / "system.md", None))
    monkeypatch.setattr(run_sub, "acquire_lock", lambda force: None)
    monkeypatch.setattr(run_sub, "LOCK", tmp_path / "run_sub.lock")
    monkeypatch.setattr(run_sub, "keep_awake", lambda on: None)
    monkeypatch.setattr(run_sub, "write_progress", lambda pc: None)
    monkeypatch.setattr(run_sub, "candidates", lambda cfg, app, pc, ids_: list(ids))
    monkeypatch.setattr(run_sub, "fetch_question", lambda app, qid: {"question_id": qid, "source": "S"})
    monkeypatch.setattr(run_sub, "attachments", lambda cfg, q: ([], None))
    monkeypatch.setattr(run_sub, "plan_attempt", lambda cfg, pc, qid, source: (1, None, False))
    monkeypatch.setattr(run_sub, "user_text", lambda q, feedback: str(q["question_id"]))
    monkeypatch.setattr(run_sub, "call_claude", call)
    monkeypatch.setattr(run_sub, "interpret", lambda out, qc, v: {"kind": "ok", "warning": False, "result": {}})
    monkeypatch.setattr(run_sub, "store", lambda *a: None)

    run_sub.solve(cfg, None, None, None, None, 1, True, False)

    assert len(sent) == 7
    # readings 0.60, 0.65 and 0.70 at the first three; a fourth would project to 0.70 + 0.05 * ($1 just
    # spent + $3.6 at most for it) = 0.93, past the 0.89 the cap plans to, so the rest waited for the reset
    assert len([t for t in sent if t < reset]) == 3 and all(t >= reset for t in sent[3:])
