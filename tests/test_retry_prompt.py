"""A blind re-solve after a disagreement with the stored answer never shows that answer (owner
2026-11-21): a solver told the expected value bends its working to reach it, and some keys are wrong."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

from run import MISMATCH_REASON, user_text  # noqa: E402


def _blind(reason: str) -> dict:
    return {"kind": "blind", "errors": [], "reason": reason, "previous_text": "", "from_attempt": 1}


def test_the_stored_answer_is_not_sent() -> None:
    text = user_text({"latexcode": "Find $n$."}, _blind(f"{MISMATCH_REASON} (\\frac{{2017+1}}{{3}})"))
    assert "2017" not in text and "stored reference answer" not in text
    assert "may itself be wrong" in text


def test_other_reasons_are_sent_as_they_are() -> None:
    text = user_text({"latexcode": "Find $n$."}, _blind("the reply was cut off at the output token limit"))
    assert "(the reply was cut off at the output token limit)" in text
