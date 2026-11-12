"""run_sub.py's assignments file (owner 2026-11-12, the MODS POTD buckets): a question listed there
is solved with its own model and effort, and the request, the reply check and the stored record all
use that model."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import run_sub  # noqa: E402


def make_cfg(tmp_path: Path, questions: dict) -> dict:
    path = tmp_path / "assign.json"
    path.write_text(json.dumps({"questions": questions}), encoding="utf-8")
    run_sub._ASSIGNED.clear()
    return {"solver": {"model": "claude-opus-5-5", "effort": "medium", "max_tokens": 32000},
            "subscription": {"sources": ["Engel"], "effort_by_source": {"Engel": "high"},
                             "effort_by_id": {"7": "max"}, "assignments_file": str(path)}}


def test_model_and_effort_come_from_the_file(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path, {"5": {"model": "claude-fable-5-2", "effort": "high"},
                              "6": {"model": "claude-opus-5-5", "effort": "medium"},
                              "7": {"model": "claude-fable-5-2", "effort": "high"}})
    assert run_sub.model_for(cfg, 5) == "claude-fable-5-2"
    assert run_sub.model_for(cfg, 99) == "claude-opus-5-5"
    assert run_sub.effort_for(cfg, "Engel", 6) == "medium"  # the file before effort_by_source
    assert run_sub.effort_for(cfg, "Engel", 7) == "max"     # effort_by_id before the file
    assert run_sub.effort_for(cfg, "Engel", 99) == "high"
    assert run_sub.effort_for(cfg, "Other", 99) == "medium"


def test_question_cfg_changes_only_that_question(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path, {"5": {"model": "claude-fable-5-2", "effort": "high"}})
    qc = run_sub.question_cfg(cfg, 5)
    assert qc["solver"]["model"] == "claude-fable-5-2"
    assert cfg["solver"]["model"] == "claude-opus-5-5"
    assert run_sub.question_cfg(cfg, 6) is cfg


def test_unknown_effort_is_refused(tmp_path: Path) -> None:
    cfg = make_cfg(tmp_path, {"5": {"model": "claude-fable-5-2", "effort": "extreme"}})
    with pytest.raises(SystemExit):
        run_sub.assigned(cfg)
