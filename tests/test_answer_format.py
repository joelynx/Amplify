"""common.format_answer / strip_math_wrappers: outer math delimiters are removed only when they
wrap the whole answer. An answer that starts and ends with math but has text between two pieces
(POTD 25815: '\\(n \\equiv 0 \\pmod{3}\\), that is, all \\(n\\) divisible by \\(3\\)') was cut
into broken LaTeX and sent back as a retry."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

from common import format_answer, normalize_answer, strip_math_wrappers  # noqa: E402


@pytest.mark.parametrize("raw, core", [
    ("\\( \\boxed{42}. \\)", "42"),
    ("\\[ x^2 \\]", "x^2"),
    ("$$ 7 $$", "7"),
    ("$\\$5$", "\\$5"),
    ("\\(n \\equiv 0 \\pmod{3}\\), that is, all \\(n\\) divisible by \\(3\\)",
     "\\(n \\equiv 0 \\pmod{3}\\), that is, all \\(n\\) divisible by \\(3\\)"),
    ("\\(n=2^k\\) for integers \\(k\\ge 1\\)", "\\(n=2^k\\) for integers \\(k\\ge 1\\)"),
    ("$a$ or $b$", "$a$ or $b$"),
])
def test_strip_only_whole_wrappers(raw: str, core: str) -> None:
    assert strip_math_wrappers(raw) == core


def test_format_keeps_math_in_text() -> None:
    raw = "\\(f(n)=\\nu_5(n)\\), the exponent of \\(5\\) in the prime factorization of \\(n\\)"
    assert format_answer("EXPRESSION", raw) == raw
    assert format_answer("EXPRESSION", "\\( x+1 \\)") == "\\( x+1 \\)"
    assert format_answer("NUMERICAL", "\\(1,000\\).") == "1000"


def test_normalize_unchanged_for_math_in_text() -> None:
    assert normalize_answer("\\(a\\) or \\(b\\)") == "aorb"
