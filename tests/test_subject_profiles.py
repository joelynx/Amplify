"""The subject solvers' prompts (run_subjects.py): every profile in pipeline/prompts/subject/profiles
fills both templates with nothing left over, and a profile's own tool notes (## tools; owner
2026-11-23: "equip them with tools if necessary") are added only in tools mode, after the calc
tool's instructions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import common  # noqa: E402
import run_sub  # noqa: E402
import run_subjects  # noqa: E402
import subjects  # noqa: E402

PROFILES = sorted(p.stem for p in (subjects.SUBJECT_PROMPTS / "profiles").glob("*.md"))


def _cfg(slug: str) -> dict:
    cfg = common.load_config()
    cfg["subjects"] = dict(cfg["subjects"], profiles={"Test Subject": slug})
    return cfg


@pytest.mark.parametrize("slug", PROFILES)
@pytest.mark.parametrize("mode", subjects.MODES)
def test_every_profile_builds_both_prompts(slug: str, mode: str, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(run_sub, "SUB_CWD", tmp_path / "cwd")
    cfg = _cfg(slug)
    plain = run_subjects.system_file(cfg, mode, "Test Subject")[1]
    tooled = run_subjects.system_file(cfg, mode, "Test Subject", tools=True)[1]
    assert "{{" not in plain and "{{" not in tooled
    # tools mode drops the "no tools" rule (solve.md) for one that sends the solver to the tool
    assert run_subjects.TOOLS_RULE not in plain and run_subjects.NO_TOOLS_RULE not in tooled
    base = plain.replace(run_subjects.NO_TOOLS_RULE, run_subjects.TOOLS_RULE)
    assert (run_subjects.TOOLS_RULE in tooled) == (run_subjects.NO_TOOLS_RULE in plain)
    assert tooled.startswith(base.rstrip())
    notes = subjects.load_profile(cfg, "Test Subject").get("tools")
    if notes:
        assert notes.strip() not in plain and tooled.rstrip().endswith(notes.strip())
    else:  # profiles without tool notes: the prompt, then exactly tools.md
        assert tooled == base.rstrip() + "\n\n" + (subjects.SUBJECT_PROMPTS / "tools.md").read_text("utf-8").strip() + "\n"


def test_the_new_solvers_have_tool_notes() -> None:
    for slug in ("chemistry", "chemical_engineering", "electrical_engineering", "quantitative_finance"):
        assert subjects.load_profile(_cfg(slug), "Test Subject").get("tools"), slug
