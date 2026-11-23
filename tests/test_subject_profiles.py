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


def test_aids_only_subjects_and_skips() -> None:
    """Maths subjects (config.subjects.aids_only) get aids only, and only when no generated solution exists; the
    aids skip lists (owner 2026-11-23: no aids for extremely easy questions such as the SOA ones) apply to aids."""
    import json
    import sqlite3

    nodes = json.loads((Path(__file__).resolve().parents[1] / "taxonomy" / "taxonomy.json").read_text("utf-8"))
    node = {s: next(n for n in nodes if n["subject"] == s) for s in ("Probability and Stochastic Processes", "Chemistry")}
    cfg = common.load_config()
    cfg["subjects"] = dict(cfg["subjects"], profiles={"Probability and Stochastic Processes": "mathematics", "Chemistry": "chemistry"},
                           aids_only=["Probability and Stochastic Processes"], aids_skip_sources=["Society Of Actuaries"],
                           aids_skip_ids=[5], hold_ids=[])
    app = sqlite3.connect(":memory:")
    app.row_factory = sqlite3.Row
    app.execute("CREATE TABLE questions (question_id INTEGER, source TEXT, topic TEXT, branch TEXT, subtopic TEXT, type TEXT, "
                "latexcode TEXT, solution TEXT, generated_solution TEXT)")
    book = "The book's worked solution."
    rows = [(1, "Bertsekas", "Probability and Stochastic Processes", book, None),
            (2, "Bertsekas", "Probability and Stochastic Processes", None, None),          # maths solve: run_sub's
            (3, "Bertsekas", "Probability and Stochastic Processes", book, "generated"),   # has hints and takeaways
            (4, "Society Of Actuaries", "Probability and Stochastic Processes", book, None),
            (5, "Bertsekas", "Probability and Stochastic Processes", book, None),
            (6, "OpenStax", "Chemistry", None, None),
            (7, "OpenStax", "Chemistry", book, None),
            (8, "Society Of Actuaries", "Chemistry", book, None)]
    for qid, src, subj, sol, gen in rows:
        n = node[subj]
        app.execute("INSERT INTO questions VALUES (?,?,?,?,?,NULL,'Find x.',?,?)", (qid, src, n["topic"], n["branch"], n["subtopic"], sol, gen))
    got = run_subjects.scope_rows(cfg, app)
    assert [(x["id"], x["mode"]) for x in got] == [(6, "solve"), (1, "aids"), (7, "aids")]
