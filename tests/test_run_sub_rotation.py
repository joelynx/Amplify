"""run_sub.py's account rotation (owner 2026-11-21): several accounts, each logged in under its own
Claude Code config dir, used one at a time in the accounts file's order. When the active one reaches a
stop, the replies still running finish and the run moves to the first account that is on, logged in
and free; an edit of the order applies once the running replies are done. Never two at once."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import run_sub  # noqa: E402

OPUS = "claude-opus-5-5"
CONF = {"max": 0.9, "margin": 0.05, "margin_by_window": {"five_hour": 0.2}, "reply_cost_scale": 0.5,
        "prior_per_usd": {"five_hour": 0.05, "seven_day": 0.004, "default": 0.05}, "reply_max_usd": {OPUS: 2.8}}
NOW = 1_800_000_000.0


def _account(tmp_path: Path, name: str, uuid: str | None, enabled: bool = True) -> dict:
    d = tmp_path / name
    d.mkdir()
    if uuid:
        (d / ".claude.json").write_text(json.dumps({"oauthAccount": {"accountUuid": uuid,
                                                                     "emailAddress": f"{name}@example.com"}}))
    return {"name": name, "dir": d.as_posix(), "enabled": enabled}


def _read(cap: run_sub.UsageCap, a: dict, five: float, week: float) -> None:
    cap.record(OPUS, NOW, NOW + 5, {"five_hour": (five, NOW + 3600), "seven_day": (week, NOW + 3 * 86400)},
               0.01, account=run_sub.account_id(a), probe=True)


def test_the_first_free_account_in_order_is_taken(tmp_path: Path) -> None:
    first, second = _account(tmp_path, "first", "u1"), _account(tmp_path, "second", "u2")
    cap = run_sub.UsageCap(CONF)
    _read(cap, first, 0.75, 0.30)   # past its five-hour stop (0.70)
    _read(cap, second, 0.10, 0.20)
    assert run_sub.pick_account([first, second], cap, [OPUS], NOW + 10) == (second, None)
    _read(cap, first, 0.10, 0.30)   # its window reset
    assert run_sub.pick_account([first, second], cap, [OPUS], NOW + 20)[0] == first


def test_accounts_turned_off_or_not_logged_in_are_passed_over(tmp_path: Path) -> None:
    off = _account(tmp_path, "off", "u1", enabled=False)
    out = _account(tmp_path, "out", None)
    third = _account(tmp_path, "third", "u3")
    cap = run_sub.UsageCap(CONF)
    assert run_sub.pick_account([off, out, third], cap, [OPUS], NOW)[0] == third
    assert run_sub.pick_account([off, out, third], cap, [OPUS], NOW, skip={"third"}) == (None, None)


def test_with_every_account_held_the_earliest_to_free_is_named(tmp_path: Path) -> None:
    first, second = _account(tmp_path, "first", "u1"), _account(tmp_path, "second", "u2")
    cap = run_sub.UsageCap(CONF)
    _read(cap, first, 0.80, 0.30)   # five-hour window frees in an hour
    _read(cap, second, 0.10, 0.86)  # weekly window frees in three days
    acct, hold = run_sub.pick_account([first, second], cap, [OPUS], NOW + 10)
    assert acct is None and hold[0] == NOW + 3600 and hold[1].startswith("first: five_hour at 80%")


def test_an_owners_one_off_counts_for_its_account(tmp_path: Path) -> None:
    first = _account(tmp_path, "first", "u1")
    acct = run_sub.account_id(first)
    cap = run_sub.UsageCap(dict(CONF, once=[{"window": "five_hour", "max": 1.0, "until": "2027-06-01T00:00:00",
                                             "account": acct}]))
    _read(cap, first, 0.75, 0.30)
    assert cap.blocked(acct, [OPUS], NOW + 10) is None  # "run it till 100" on that account


def test_each_claude_run_starts_under_the_active_accounts_login(tmp_path: Path, monkeypatch) -> None:
    cfg = {"solver": {"max_tokens": 1000}, "subscription": {"sources": ["S"]}}
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "inherited")  # never passed on: only the active account's
    assert "CLAUDE_CONFIG_DIR" not in run_sub.child_env(cfg, "high")
    first = _account(tmp_path, "first", "u1")
    cap = run_sub.UsageCap(CONF)
    run_sub.use_account(first, cap)
    assert run_sub.child_env(cfg, "high")["CLAUDE_CONFIG_DIR"] == str(Path(first["dir"]))
    assert cap.account == run_sub.account_id(first) and cap.active_name == "first"


def test_the_accounts_list_is_edited(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(run_sub, "ACCOUNTS_FILE", tmp_path / "accounts.json")
    monkeypatch.setattr(run_sub, "ACCOUNTS_HOME", tmp_path / "homes")
    monkeypatch.setattr(run_sub, "CAP_STATE", tmp_path / "usage_cap_state.json")
    cfg = {"solver": {"model": OPUS}, "subscription": {"sources": ["S"], "usage_cap": CONF}}
    for n in ("a", "b", "c"):
        run_sub.accounts_cmd(cfg, "add", [n], None)
    assert (tmp_path / "homes" / "b").is_dir()
    names = lambda: [a["name"] for a in run_sub.load_accounts()]  # noqa: E731
    run_sub.accounts_cmd(cfg, "order", ["c", "a"], None)
    assert names() == ["c", "a", "b"]
    run_sub.accounts_cmd(cfg, "swap", ["c", "b"], None)
    assert names() == ["b", "a", "c"]
    run_sub.accounts_cmd(cfg, "disable", ["a"], None)
    assert [a["enabled"] for a in run_sub.load_accounts()] == [True, False, True]
    run_sub.accounts_cmd(cfg, "remove", ["c"], None)
    assert names() == ["b", "a"]
    assert "not logged in" in capsys.readouterr().out


class FakeTime:
    def __init__(self) -> None:
        self.now = NOW
        self.slept = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, secs: float) -> None:
        self.now += secs
        self.slept += secs


def _solve_harness(tmp_path: Path, monkeypatch, accounts: list[dict], usage_of, on_store=None,
                   conf: dict = CONF) -> tuple[list, list]:
    """Run solve() on 4 questions with a fake claude: usage_of(dir) is the five-hour utilization a run
    under that account's login reports. Returns (the dir each run started under, the questions stored)."""
    run_sub.save_accounts(accounts, tmp_path / "accounts.json")
    monkeypatch.setattr(run_sub, "ACCOUNTS_FILE", tmp_path / "accounts.json")
    clock = FakeTime()
    dirs: list = []
    stored: list[int] = []

    def call(qc, sf, text, effort, mt, images):
        d = run_sub._ACTIVE_DIR[0]
        dirs.append(d)
        info = {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": usage_of(d), "resetsAt": clock.now + 9000}}}
        return {"seconds": 1, "events": [{"type": "rate_limit_event", "rate_limit_info": info}]}

    def store(pc, qc, qid, *a):
        stored.append(qid)
        if on_store:
            on_store(stored)

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
    monkeypatch.setattr(run_sub, "candidates", lambda cfg, app, pc, ids: [1, 2, 3, 4])
    monkeypatch.setattr(run_sub, "fetch_question", lambda app, qid: {"question_id": qid, "source": "S"})
    monkeypatch.setattr(run_sub, "attachments", lambda cfg, q: ([], None))
    monkeypatch.setattr(run_sub, "plan_attempt", lambda cfg, pc, qid, source: (1, None, False))
    monkeypatch.setattr(run_sub, "user_text", lambda q, feedback: str(q["question_id"]))
    monkeypatch.setattr(run_sub, "call_claude", call)
    monkeypatch.setattr(run_sub, "interpret", lambda out, qc, version: {"kind": "ok", "warning": False})
    monkeypatch.setattr(run_sub, "store", store)
    cfg = {"solver": {"model": OPUS, "effort": "medium", "max_tokens": 32000},
           "subscription": {"sources": ["S"], "usage_cap": conf}}
    run_sub.solve(cfg, None, None, None, None, 1, True, False)
    assert clock.slept == 0  # no waiting while another account was free
    return dirs, stored


def test_a_stopped_account_hands_over_to_the_next(tmp_path: Path, monkeypatch) -> None:
    first, second = _account(tmp_path, "first", "u1"), _account(tmp_path, "second", "u2")
    dirs, stored = _solve_harness(tmp_path, monkeypatch, [first, second],
                                  lambda d: 0.75 if d == str(Path(first["dir"])) else 0.10)
    assert stored == [1, 2, 3, 4]
    assert dirs[0] == str(Path(first["dir"]))  # the probe found the first past its stop
    assert set(dirs[1:]) == {str(Path(second["dir"]))}


def test_a_new_serving_order_applies_once_the_running_replies_are_done(tmp_path: Path, monkeypatch) -> None:
    first, second = _account(tmp_path, "first", "u1"), _account(tmp_path, "second", "u2")
    listing = tmp_path / "accounts.json"

    def reorder(stored: list[int]) -> None:
        if len(stored) == 2:  # the owner puts the second account first
            run_sub.save_accounts([second, first], listing)
            t = listing.stat().st_mtime + 10
            os.utime(listing, (t, t))

    dirs, stored = _solve_harness(tmp_path, monkeypatch, [first, second], lambda d: 0.10, on_store=reorder)
    assert stored == [1, 2, 3, 4]
    a, b = str(Path(first["dir"])), str(Path(second["dir"]))
    assert dirs[:3] == [a, a, a] and dirs[3:] and set(dirs[3:]) == {b}  # probe + 2 questions, then the move


def test_an_account_with_room_goes_before_one_near_its_stop(tmp_path: Path) -> None:
    near, fresh = _account(tmp_path, "near", "u1"), _account(tmp_path, "fresh", "u2")
    cap = run_sub.UsageCap(dict(CONF, rotate_room=3))
    _read(cap, near, 0.55, 0.30)    # a reply counts 0.07 at most here: room for two before the 0.70 stop
    _read(cap, fresh, 0.10, 0.20)
    assert run_sub.pick_account([near, fresh], cap, [OPUS], NOW + 10) == (fresh, None)
    assert run_sub.pick_account([near], cap, [OPUS], NOW + 10) == (near, None)  # its last stretch is still used
    assert run_sub.pick_account([near], cap, [OPUS], NOW + 10, strict=True) == (None, None)


def test_the_rotation_leaves_an_account_near_its_stop_for_one_with_room(tmp_path: Path, monkeypatch) -> None:
    near, fresh, other = (_account(tmp_path, n, u) for n, u in (("near", "u1"), ("fresh", "u2"), ("other", "u3")))
    cap = run_sub.UsageCap(dict(CONF, rotate_room=3))
    _read(cap, near, 0.55, 0.30)
    _read(cap, fresh, 0.10, 0.20)
    _read(cap, other, 0.60, 0.20)
    monkeypatch.setattr(run_sub, "load_accounts", lambda path=None: [near, other, fresh])
    run_sub.use_account(near, cap)
    assert run_sub.tail_move(cap, near, [OPUS], NOW + 10) == fresh  # "other" is near its stop too
    run_sub.use_account(fresh, cap)
    assert run_sub.tail_move(cap, fresh, [OPUS], NOW + 10) is None  # room enough where it is
    monkeypatch.setattr(run_sub, "load_accounts", lambda path=None: [near, other])
    run_sub.use_account(near, cap)
    assert run_sub.tail_move(cap, near, [OPUS], NOW + 10) is None  # nowhere better: it stays to its stop
    assert run_sub.tail_move(run_sub.UsageCap(CONF), near, [OPUS], NOW + 10) is None  # rotate_room unset: off


def test_a_run_moves_on_from_an_account_near_its_stop(tmp_path: Path, monkeypatch) -> None:
    first, second = _account(tmp_path, "first", "u1"), _account(tmp_path, "second", "u2")
    dirs, stored = _solve_harness(tmp_path, monkeypatch, [first, second],
                                  lambda d: 0.55 if d == str(Path(first["dir"])) else 0.10, conf=dict(CONF, rotate_room=3))
    assert stored == [1, 2, 3, 4]
    a, b = str(Path(first["dir"])), str(Path(second["dir"]))
    assert dirs[:2] == [a, a] and set(dirs[2:]) == {b}  # probe + 1 question (room for 2, not 3), then the move
