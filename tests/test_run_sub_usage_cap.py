"""run_sub.py's usage cap (owner 2026-11-19: "do not exceed 90% of usage on any account"): a question
goes only if every usage window its model counts toward stays at or under the cap, counting the
replies still running; otherwise the run waits for the window's reset or a new login."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import run_sub  # noqa: E402

FABLE, OPUS = "claude-fable-5-2", "claude-opus-5-5"
CONF = {"max": 0.9, "prior_per_usd": {"five_hour": 0.05, "default": 0.05},
        "reply_cost_usd": {FABLE: [0.42, 0.45], OPUS: [0.11, 0.1]}}
NOW = 1_800_000_000.0


def event(windows: dict, status: str = "allowed", kind: str = "five_hour") -> dict:
    return {"type": "rate_limit_event", "rate_limit_info": {
        "status": status, "rateLimitType": kind,
        "unifiedWindows": {w: {"utilization": u, "resetsAt": NOW + 3600} for w, u in windows.items()}}}


def test_readings_take_every_window_and_a_rejection() -> None:
    out = {"events": [event({"five_hour": 0.97, "seven_day": 0.41}),
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


def test_running_replies_count_toward_the_cap() -> None:
    cap = run_sub.UsageCap(CONF)  # plans to 0.88: max 0.9 less the 0.02 margin
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.5, NOW + 3600)}, 0.4)
    # each Fable in flight at the seed while there are few replies: 0.05 * (0.42, plus 1.65 sd of the total)
    assert cap.allows(FABLE, [], NOW)
    assert cap.allows(FABLE, [(FABLE, NOW)] * 4, NOW)
    assert not cap.allows(FABLE, [(FABLE, NOW)] * 12, NOW)
    cap.record(FABLE, NOW - 50, NOW - 5, {"five_hour": (0.86, NOW + 3600)}, 0.4)
    assert not cap.allows(FABLE, [], NOW)
    until, why = cap.held_until(FABLE, NOW)
    assert until == NOW + 3600 and "five_hour at 86%" in why


def test_a_reply_that_has_run_long_counts_as_a_long_one() -> None:
    cap = run_sub.UsageCap(CONF)
    for i in range(30):  # short cheap replies, and a few long costly ones
        secs, usd = (600, 2.0) if i % 6 == 0 else (60, 0.2)
        cap.record(FABLE, NOW + 1000 * i, NOW + 1000 * i + secs, {}, usd)
    fresh, _ = cap._expect(FABLE, 0)
    long_run, _ = cap._expect(FABLE, 300)
    assert abs(fresh - 0.5) < 1e-9 and long_run == 2.0
    assert cap._expect(FABLE, 5000)[0] > 2.0  # past every finished one: at least its time at the cost per second


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
    login.write_text("b")
    import os
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
    import os
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
        u = 0.0 if clock.now >= reset else 0.70 + 0.05 * len(sent)  # each $1 reply uses 5%
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
    before = [t for t in sent if t < reset]
    # readings 0.75 and 0.80 at the first two; a third would project to 0.80 + 0.05 * ($1 just spent
    # + $1.16 for the next) = 0.91, past the 0.88 the cap plans to, so the rest waited for the reset
    assert len(before) == 2 and all(t >= reset for t in sent[2:])
