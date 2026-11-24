"""subjects.option_count: how many options a multiple-choice question prints, for the answer key check."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import subjects  # noqa: E402


def _mcq(letters: str, stem: str = "Which is right?") -> str:
    return stem + "\n\n" + "\n\n".join(f"({x}) option {x}" for x in letters)


def test_ten_and_more_options_are_counted() -> None:
    # 2026-11-24 (job 20261124-023422): MMLU-Pro and SuperGPQA print (A) to (J); SUPERChem to (K)
    assert subjects.option_count(_mcq("ABCDEFGHIJ")) == 10
    assert subjects.option_count(_mcq("ABCDEFGHIJK")) == 11
    assert subjects.option_count(_mcq("ABCD")) == 4


def test_statements_numbered_in_roman_are_not_options() -> None:
    stem = "Consider the statements:\n(I) the first\n(II) the second\n(III) the third\nWhich are true?"
    assert subjects.option_count(_mcq("ABCD", stem)) == 4


def test_a_key_past_the_eighth_option_is_read() -> None:
    q = _mcq("ABCDEFGHIJ")
    spec, errors = subjects.parse_key("PART a | CHOICE | j | the right option", q)
    assert not errors and spec["parts"][0]["value"] == "j" and spec["parts"][0]["options"] == 10


def test_the_options_after_a_stems_lettered_parts_are_counted() -> None:
    # 2026-11-24: MMLU-Pro stems ask (a), (b), (c), then print (A) to (J)
    stem = "(a) How many lines? (b) How far apart? (c) How wide a prism?\n\nExactly one option is correct."
    assert subjects.option_count(_mcq("ABCDEFGHIJ", stem)) == 10
    # lowercase options after uppercase labels in the stem (JEE matching lists): the options are the lowercase run
    match = "(A) first\n(B) second\nMatch each with:\n\n(a) p\n\n(b) q\n\n(c) r\n\n(d) s"
    assert subjects.option_count(match) == 4
