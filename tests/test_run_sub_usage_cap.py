"""run_sub.py's usage cap (owner 2026-11-19: "do not exceed 90% of usage on any account"): a question
goes only if every usage window its model counts toward has a recent reading (a one-word probe reads
a missing one) and stays under the cap with every reply still running, and this one, at the most a
reply can cost; otherwise the run waits for the window's reset or a new login. Readings are kept per
account."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

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


def test_nothing_goes_before_a_reading_of_every_window() -> None:
    cap = run_sub.UsageCap(CONF)
    assert cap.unread(FABLE, NOW) == ["all"] and not cap.allows(FABLE, [], NOW)
    assert cap.probe_due(FABLE, [], NOW)
    cap.probed[FABLE] = NOW
    cap.record(FABLE, NOW, NOW + 5, {"five_hour": (0.3, NOW + 3600), "seven_day_overage_included": (0.4, NOW + 9e4)},
               0.01, probe=True)
    assert cap.allows(FABLE, [], NOW + 5) and not cap.hist  # a probe is not a reply: not in the costs seen
    assert not cap.allows(OPUS, [], NOW + 5)                 # its own windows are not known yet
    assert cap.probe_due(OPUS, [], NOW + 5) and not cap.probe_due(FABLE, [], NOW + 5)


def test_a_stale_reading_is_read_again_unless_it_is_over_the_cap() -> None:
    cap = run_sub.UsageCap(CONF)  # readings older than 20 minutes are read again before a question goes
    cap.record(FABLE, NOW, NOW + 5, {"five_hour": (0.3, NOW + 9000)}, 0.01, probe=True)
    later = NOW + 1300
    assert cap.unread(FABLE, later) == ["five_hour"] and not cap.allows(FABLE, [], later)
    assert cap.probe_due(FABLE, [], later)
    cap.record(FABLE, NOW + 10, NOW + 15, {"five_hour": (0.88, NOW + 9000)}, 0.01, probe=True)
    assert not cap.probe_due(FABLE, [], later)  # known to be over: it waits for the reset, no probes
    assert cap.held_until(FABLE, later)[0] == NOW + 9000


def test_spend_since_a_reading_is_read_again_not_waited_out() -> None:
    """2026-11-20: three cut-off replies at $5.26 put five_hour's projection past the cap at the prior's
    usage per dollar while a reading showed 0.26: once the reading is stale a probe reads it again."""
    cap = run_sub.UsageCap(CONF)
    cap.record(FABLE, NOW, NOW + 5, {"five_hour": (0.0, NOW + 18000)}, 0.01, probe=True)
    for k in range(3):
        cap.record(FABLE, NOW + 10, NOW + 600 + k, {"five_hour": (0.0, NOW + 18000)}, 5.26)
    soon = NOW + 700  # the reading from NOW + 10 is still fresh
    assert cap.over(FABLE, [], soon) and not cap.probe_due(FABLE, [], soon)
    until, why = cap.held_until(FABLE, soon)
    assert until == NOW + 10 + 1200 + 1 and "projected" in why  # not the reset at NOW + 18000
    later = until
    assert cap.probe_due(FABLE, [], later)
    cap.record(FABLE, later, later + 5, {"five_hour": (0.26, NOW + 18000)}, 0.01, probe=True)
    assert cap.allows(FABLE, [], later + 5)  # usage per dollar is now fitted from the readings: far below the prior


def test_a_failed_probe_waits_before_the_next() -> None:
    cap = run_sub.UsageCap(CONF)
    cap.probed[FABLE] = NOW
    cap.record(FABLE, NOW, NOW + 5, {}, 0.0, probe=True)  # no reading came back
    assert not cap.probe_due(FABLE, [], NOW + 10) and cap.probe_due(FABLE, [], NOW + run_sub.PROBE_RETRY)
    until, why = cap.held_until(FABLE, NOW + 10)
    assert until == NOW + run_sub.PROBE_RETRY and "no usage reading" in why


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


def test_a_window_can_have_its_own_margin() -> None:
    cap = run_sub.UsageCap(dict(CONF, margin_by_window={"five_hour": 0.2}))  # five_hour plans to 0.70, the rest to 0.89
    readings = {"five_hour": (0.5, NOW + 3600), "seven_day": (0.5, NOW + 9e4)}
    cap.record(FABLE, NOW - 100, NOW - 10, readings, 0.0)
    assert cap.allows(FABLE, [], NOW)  # 0.5 + 0.05 * 3.6 = 0.68 in both
    assert [w for w, _ in cap.over(FABLE, [(FABLE, NOW)], NOW)] == ["five_hour"]  # 0.86: past 0.70, not past 0.89


def test_a_window_wholly_in_the_rules_hours_may_reach_its_max() -> None:
    """Owner 2026-11-22: a five-hour window wholly between 00:00 and 09:00 may go to 100%."""
    hours = [{"window": "five_hour", "max": 1.0, "from": "00:00", "to": "09:00"}]
    at = lambda s: run_sub.datetime.fromisoformat(s).timestamp()  # noqa: E731
    for reset, stop in (("2026-11-23T09:00:00", 1.0), ("2026-11-23T05:00:00", 1.0),  # 04:00-09:00, 00:00-05:00
                        ("2026-11-23T09:10:00", 0.70), ("2026-11-23T04:50:00", 0.70),  # past 09:00, from 23:50
                        ("2026-11-23T14:00:00", 0.70)):
        cap = run_sub.UsageCap(dict(CONF, margin_by_window={"five_hour": 0.2}, hours=hours))
        cap.record(FABLE, at(reset) - 3600, at(reset) - 3590, {"five_hour": (0.5, at(reset)), "seven_day": (0.5, at(reset) + 9e4)}, 0.0)
        assert cap.plan_for("five_hour", at(reset) - 3000) == pytest.approx(stop), reset
        assert cap.plan_for("seven_day", at(reset) - 3000) == cap.plan  # other windows keep their stops


def test_the_most_a_reply_costs_is_the_larger_of_config_and_seen() -> None:
    cap = run_sub.UsageCap(CONF)
    assert cap.most(FABLE) == 3.6 and cap.most("claude-other") == 4.0
    cap.record(FABLE, NOW, NOW + 900, {}, 5.0)
    assert cap.most(FABLE) == 5.0
    scaled = run_sub.UsageCap(dict(CONF, reply_cost_scale=0.75))  # owner 2026-11-20
    scaled.record(FABLE, NOW, NOW + 900, {}, 5.0)
    assert scaled.most(FABLE) == 3.75 and round(scaled.most(OPUS), 6) == 2.1


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
    assert abs(cap._per_usd("five_hour", NOW) - (0.30 + 0.01) / 6) < 1e-9


def test_a_reset_window_is_read_again() -> None:
    cap = run_sub.UsageCap(CONF)
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.95, NOW + 60)}, 0.4)
    assert not cap.allows(FABLE, [], NOW) and not cap.probe_due(FABLE, [], NOW)
    assert cap.unread(FABLE, NOW + 61) == ["five_hour"] and cap.probe_due(FABLE, [], NOW + 61)
    cap.record(FABLE, NOW + 61, NOW + 65, {"five_hour": (0.02, NOW + 18061)}, 0.01, probe=True)
    assert cap.allows(FABLE, [], NOW + 65)


def test_a_lower_reading_ends_the_window_without_a_reset_time() -> None:
    cap = run_sub.UsageCap(CONF)
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.95, None)}, 0.4)
    assert not cap.allows(FABLE, [], NOW)
    cap.record(FABLE, NOW - 5, NOW, {"five_hour": (0.10, None)}, 0.01, probe=True)
    assert cap.allows(FABLE, [], NOW)


def account(path: Path, uuid: str) -> Path:
    path.write_text(json.dumps({"oauthAccount": {"accountUuid": uuid, "emailAddress": "x"}, "numStartups": 1}))
    return path


def test_a_token_refresh_is_not_a_new_login(tmp_path: Path) -> None:
    login, acct = tmp_path / "credentials.json", account(tmp_path / "claude.json", "A")
    login.write_text("a")
    cap = run_sub.UsageCap(CONF, login, None, acct)
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.89, NOW + 3600)}, 0.4)
    os.utime(login, ns=(1, 1))  # Claude Code rewrote the login (a new token), same account
    assert not cap.login_changed() and not cap.allows(FABLE, [], NOW) and not cap.probe_due(FABLE, [], NOW)
    acct.write_text('{"oauthAccount": {"accountUu')  # half written: no change
    assert not cap.login_changed()


def test_each_account_keeps_its_own_readings(tmp_path: Path) -> None:
    acct, state = account(tmp_path / "claude.json", "A"), tmp_path / "state.json"
    cap = run_sub.UsageCap(CONF, None, state, acct)
    cap.record(FABLE, NOW - 100, NOW - 10, {"five_hour": (0.89, NOW + 3600)}, 0.4)
    first = cap.account
    account(acct, "B")
    assert cap.login_changed() and cap.account != first
    assert cap.unread(FABLE, NOW) == ["all"] and cap.probe_due(FABLE, [], NOW)  # B is read before anything goes
    # a reply that started on A and finishes after the switch counts on A
    cap.record(FABLE, NOW - 50, NOW, {"five_hour": (0.89, NOW + 3600)}, 0.4, account=first)
    assert cap.unread(FABLE, NOW) == ["all"]
    account(acct, "A")
    assert cap.login_changed() and cap.account == first
    assert not cap.allows(FABLE, [], NOW) and not cap.probe_due(FABLE, [], NOW)  # A is known to be full
    again = run_sub.UsageCap(CONF, None, state, acct)  # a restart keeps it, and the reply costs
    assert not again.allows(FABLE, [], NOW) and again.hist[FABLE] == [(90.0, 0.4), (50.0, 0.4)]
    assert "accountUuid" not in state.read_text() and '"A"' not in state.read_text()


def test_without_an_account_record_the_login_names_the_account(tmp_path: Path) -> None:
    login = tmp_path / "credentials.json"
    login.write_text("a")
    cap = run_sub.UsageCap(CONF, login, None, tmp_path / "missing.json")
    assert cap.account.startswith("login ")
    os.utime(login, ns=(1, 1))
    assert cap.login_changed()  # cannot tell a refresh from a new login: read the account again


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
    probes: list[float] = []
    acct = {"u": 0.60, "reset": reset}

    def call(qc, sf, text, effort, mt, images):
        if clock.now >= acct["reset"]:  # the window reset: a new one
            acct.update(u=0.0, reset=acct["reset"] + 18000)
        reading = {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "unifiedWindows": {
            "five_hour": {"utilization": acct["u"], "resetsAt": acct["reset"]}}}}
        if text == run_sub.PROBE_TEXT:
            probes.append(clock.now)
            clock.now += 2
            return {"seconds": 2, "events": [reading, {"type": "result", "total_cost_usd": 0.001}]}
        sent.append(clock.now)
        clock.now += 30
        acct["u"] += 0.05  # each $1 reply uses 5%, counted when it finishes
        return {"seconds": 30, "events": [reading, {"type": "result", "total_cost_usd": 1.0}]}

    monkeypatch.setattr(run_sub, "time", clock)
    monkeypatch.setattr(run_sub, "LOGIN_FILE", tmp_path / "no-login.json")
    monkeypatch.setattr(run_sub, "ACCOUNT_FILE", tmp_path / "no-account.json")
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
    # a probe read 0.60 before anything went; readings 0.60, 0.65 and 0.70 at the first three; a fourth
    # would project to 0.70 + 0.05 * ($1 just spent + $3.6 at most for it) = 0.93, past the 0.89 the cap
    # plans to, so the rest waited for the reset, with no probes while the account was known to be full,
    # and a probe read the new window before they went
    assert len([t for t in sent if t < reset]) == 3 and all(t >= reset for t in sent[3:])
    # one probe once the last reply's reading is stale (the replies since only projected past the cap;
    # the probe shows the window itself is), then none until the reset
    assert len(probes) == 3 and probes[0] < sent[0] and sent[2] < probes[1] < reset <= probes[2] < sent[3]


def test_an_owners_one_off_max_lasts_until_its_time() -> None:
    """Owner 2026-11-20: "Let the 5 hour window get completely exhausted this once"."""
    until = "2026-11-20T09:10:00"
    end = run_sub.datetime.fromisoformat(until).timestamp()
    cap = run_sub.UsageCap(dict(CONF, once={"five_hour": {"max": 1.0, "until": until}}))
    cap.record(OPUS, end - 600, end - 595, {"five_hour": (0.8, end), "seven_day": (0.95, end + 9e5)}, 0.01, probe=True)
    assert [w for w, _ in cap.over(OPUS, [], end - 590)] == ["seven_day"]  # five_hour may go to 1.0; the rest as before
    assert cap.plan_for("five_hour", end - 1) == 1.0 and cap.plan_for("five_hour", end) == cap.plan


def test_an_owners_one_off_holds_only_on_its_account(tmp_path: Path) -> None:
    """2026-11-20: a one-off for one account's five-hour window must not carry over to the next login."""
    acct = account(tmp_path / "claude.json", "one")
    until = "2026-11-20T09:10:00"
    end = run_sub.datetime.fromisoformat(until).timestamp()
    cap = run_sub.UsageCap(dict(CONF, once={"five_hour": {"max": 1.0, "until": until, "account": "x"}}), None, None, acct)
    cap.once = [("five_hour", 1.0, end, cap.account)]
    assert cap.plan_for("five_hour", end - 1) == 1.0
    account(acct, "two")
    cap.login_changed()
    assert cap.plan_for("five_hour", end - 1) == cap.plan


def test_one_offs_for_two_accounts_hold_side_by_side(tmp_path: Path) -> None:
    """2026-11-20: 'run it till 100 for this account too': each account keeps its own one-off."""
    acct = account(tmp_path / "claude.json", "one")
    first = run_sub.UsageCap(CONF, None, None, acct).account
    account(acct, "two")
    second = run_sub.UsageCap(CONF, None, None, acct).account
    once = [{"window": "five_hour", "max": 1.0, "until": "2026-11-20T20:00:00", "account": first},
            {"window": "five_hour", "max": 1.0, "until": "2026-11-20T23:30:00", "account": second}]
    cap = run_sub.UsageCap(dict(CONF, once=once), None, None, acct)
    t = run_sub.datetime.fromisoformat("2026-11-20T21:00:00").timestamp()
    assert cap.plan_for("five_hour", t) == 1.0  # the second account's, until 23:30
    account(acct, "one")
    cap.login_changed()
    assert cap.plan_for("five_hour", t) == cap.plan  # the first account's ended at 20:00


def test_a_reset_model_limit_is_read_again_before_its_questions_go() -> None:
    """2026-11-20: the owner reset the Fable limit on an account whose Fable window read 1.07."""
    cap = run_sub.UsageCap(CONF)
    cap.record(FABLE, NOW, NOW + 5, {"five_hour": (0.1, NOW + 9000), "seven_day_overage_included": (1.07, NOW + 9e5)}, 0.0, probe=True)
    cap.record(OPUS, NOW, NOW + 5, {"five_hour": (0.1, NOW + 9000), "seven_day": (0.5, NOW + 9e5)}, 0.01, probe=True)
    assert not cap.probe_due(FABLE, [], NOW + 2000)  # known to be over: no probes until the reset
    cap.forget(FABLE)
    assert cap.unread(FABLE, NOW + 10) == ["all"] and cap.probe_due(FABLE, [], NOW + 10)
    assert cap.allows(OPUS, [], NOW + 10)  # the other model's readings stay
