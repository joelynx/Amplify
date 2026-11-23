"""run_sub.py's calc tool (owner 2026-11-23: "Yes, add the calculator to the solver"): questions of
config.tools.math_sources go with the calc tool and the solver prompt plus its tool section; the others
go as before."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import run_sub  # noqa: E402

OPUS = "claude-opus-5-5"
TOOLS = {"enabled": True, "math_sources": ["FinanceMath"]}


def test_the_calc_tool_goes_to_the_listed_sources_only() -> None:
    assert run_sub.uses_tools({"tools": TOOLS}, "FinanceMath")
    assert not run_sub.uses_tools({"tools": TOOLS}, "MMLU")
    assert not run_sub.uses_tools({"tools": dict(TOOLS, enabled=False)}, "FinanceMath")
    assert not run_sub.uses_tools({}, "FinanceMath")


def test_the_tools_prompt_is_the_solver_prompt_and_the_tool_section(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(run_sub, "SUB_CWD", tmp_path / "cwd")
    monkeypatch.setattr(run_sub, "system_prompt", lambda cfg: "SOLVER PROMPT\n")
    plain, base = run_sub.write_system_file({"tools": TOOLS})
    with_tool, text = run_sub.write_system_file({"tools": TOOLS}, tools=True)
    assert plain != with_tool and base == "SOLVER PROMPT\n"
    assert text.startswith("SOLVER PROMPT\n\nCALCULATION TOOL:") and "CoolProp" not in text
    assert with_tool.read_text(encoding="utf-8") == text


def test_a_solve_sends_the_listed_sources_with_the_tool(tmp_path: Path, monkeypatch) -> None:
    sources = {1: "FinanceMath", 2: "MMLU"}
    sent: dict[int, tuple] = {}

    def call(qc, sf, text, effort, mt, images, tools_log=None):
        sent[int(text)] = (Path(sf).name, tools_log)
        return {"seconds": 1, "events": []}

    monkeypatch.setattr(run_sub, "SUB_CWD", tmp_path / "cwd")
    monkeypatch.setattr(run_sub, "system_prompt", lambda cfg: "SOLVER PROMPT\n")
    monkeypatch.setattr(run_sub, "q_dir", lambda qid: tmp_path / "out" / str(qid))
    monkeypatch.setattr(run_sub, "load_accounts", lambda path=None: [])
    monkeypatch.setattr(run_sub, "LOGIN_FILE", tmp_path / "no-login.json")
    monkeypatch.setattr(run_sub, "ACCOUNT_FILE", tmp_path / "no-account.json")
    monkeypatch.setattr(run_sub, "CAP_STATE", tmp_path / "usage_cap_state.json")
    monkeypatch.setattr(run_sub, "verify", lambda *a, **k: {"ok": True, "accepted": True, "claude_code_version": "t"})
    monkeypatch.setattr(run_sub, "acquire_lock", lambda force: None)
    monkeypatch.setattr(run_sub, "LOCK", tmp_path / "run_sub.lock")
    monkeypatch.setattr(run_sub, "keep_awake", lambda on: None)
    monkeypatch.setattr(run_sub, "write_progress", lambda pc: None)
    monkeypatch.setattr(run_sub, "candidates", lambda cfg, app, pc, ids: [1, 2])
    monkeypatch.setattr(run_sub, "fetch_question", lambda app, qid: {"question_id": qid, "source": sources[qid]})
    monkeypatch.setattr(run_sub, "attachments", lambda cfg, q: ([], None))
    monkeypatch.setattr(run_sub, "plan_attempt", lambda cfg, pc, qid, source: (2, None, False))
    monkeypatch.setattr(run_sub, "user_text", lambda q, feedback: str(q["question_id"]))
    monkeypatch.setattr(run_sub, "call_claude", call)
    monkeypatch.setattr(run_sub, "interpret", lambda out, qc, version: {"kind": "ok", "warning": False})
    monkeypatch.setattr(run_sub, "store", lambda *a: None)
    monkeypatch.setattr(run_sub.UsageCap, "allows", lambda self, model, running, now=None: True)
    monkeypatch.setattr(run_sub.UsageCap, "probe_due", lambda self, model, running, now=None: False)
    cfg = {"solver": {"model": OPUS, "effort": "medium", "max_tokens": 32000}, "tools": TOOLS,
           "subscription": {"sources": ["FinanceMath", "MMLU"], "usage_cap": {}}}
    run_sub.solve(cfg, None, None, None, None, 1, False, False)
    assert sent[1] == (".amplify-subscription-system-prompt-tools.txt", tmp_path / "out" / "1" / "tools_2.jsonl")
    assert sent[2] == (".amplify-subscription-system-prompt.txt", None)
