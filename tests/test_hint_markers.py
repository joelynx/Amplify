"""The repair of an END marker written again after a hint's END (common.drop_doubled_hint_ends).
16 of the 159 high-effort tie-breaks of 2026-11-12 were rejected only for it: '%%% END HINT 2'
twice, '%%% END HINTS' or '%%% END ANSWER KEY' after the last tier."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import common  # noqa: E402
import subjects  # noqa: E402

SUBJECT_HEAD = """%%% BEGIN SOLUTION
Work. Final answer: 3.
%%% END SOLUTION
%%% BEGIN NOTES
Note.
%%% END NOTES
%%% BEGIN TAKEAWAYS
Takeaway.
%%% END TAKEAWAYS
%%% BEGIN ANSWER KEY
PART | NUMBER | 3
%%% END ANSWER KEY
"""
MATH_HEAD = """%%% BEGIN SOLUTION
Work. Final answer: 3.
%%% END SOLUTION
%%% BEGIN RIGOR NOTES
NONE
%%% END RIGOR NOTES
%%% BEGIN TAKEAWAYS
Takeaway.
%%% END TAKEAWAYS
%%% ANSWER TYPE: NUMERICAL
%%% BEGIN ANSWER
3
%%% END ANSWER
"""
TWO = "%%% BEGIN HINT 1\nFirst.\n%%% END HINT 1\n%%% BEGIN HINT 2\nSecond.\n%%% END HINT 2\n"
THREE = TWO + "%%% BEGIN HINT 3\nThird.\n%%% END HINT 3\n"


@pytest.mark.parametrize("hints, tiers", [
    (TWO + "%%% END HINT 2\n", ["First.", "Second."]),
    (TWO + "\n%%% END HINTS\n", ["First.", "Second."]),
    (TWO + "%%% END ANSWER KEY\n%%% END HINT 2\n", ["First.", "Second."]),
    (TWO + "%%% END HINT 2\n" + "%%% BEGIN HINT 3\nThird.\n%%% END HINT 3\n", ["First.", "Second.", "Third."]),
    (THREE + "%%% END HINT 3\n", ["First.", "Second.", "Third."]),
])
def test_subject_reply_with_a_doubled_end_parses(hints: str, tiers: list[str]) -> None:
    parts, errors = subjects.parse_reply(SUBJECT_HEAD + hints, "solve")
    assert errors == []
    assert parts["hint_tiers"] == tiers
    assert any("stray marker" in r for r in parts["repairs"])


def test_math_reply_with_a_doubled_end_parses() -> None:
    text, notes = common.repair_slips(MATH_HEAD + TWO + "%%% END HINT 2\n")
    parts, errors = common.parse_solver_output(text)
    assert errors == []
    assert parts["hint_tiers"] == ["First.", "Second."]
    assert notes == ["line 20: stray marker '%%% END HINT 2' after the hint's END dropped"]


def test_a_clean_reply_is_unchanged() -> None:
    lines = (SUBJECT_HEAD + THREE).split("\n")
    assert common.drop_doubled_hint_ends(lines) == []
    assert "\n".join(lines) == SUBJECT_HEAD + THREE


def test_an_end_after_text_is_still_reported() -> None:
    parts, errors = subjects.parse_reply(SUBJECT_HEAD + TWO + "Stray text.\n%%% END HINT 2\n", "solve")
    assert parts is None
    assert errors
