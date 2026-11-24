"""The judge's comparison of a math reply's answer with the stored answer when either is a number
written in LaTeX (owner 2026-11-20: "extend the judge's answer comparison"): fractions, roots,
powers and pi are compared by value; answers with variables, lists or words are not compared."""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

from validate import constant_value, same_constant  # noqa: E402


@pytest.mark.parametrize("text, value", [
    ("$\\frac{3}{4}$", Fraction(3, 4)),
    ("\\dfrac{248}{517}", Fraction(248, 517)),
    ("\\frac12", Fraction(1, 2)),
    ("1/2", Fraction(1, 2)),
    ("$10\\frac{2}{3}$", Fraction(32, 3)),         # AMC's mixed number
    ("2^{10}-1", Fraction(1023)),
    ("$2^{999}-2^{499}$", Fraction(2 ** 999 - 2 ** 499)),
    ("10^{225}-1", Fraction(10 ** 225 - 1)),
    ("1,024", Fraction(1024)),
    ("\\boxed{025}", Fraction(25)),
    ("\\sqrt{16}", Fraction(4)),
    ("\\sqrt[3]{27}", Fraction(3)),
    ("30^\\circ", Fraction(30)),
    ("300\\%", Fraction(300)),
    ("n=5", Fraction(5)),
    ("\\left(\\frac{1}{2}\\right)^{3}", Fraction(1, 8)),
    ("-\\frac{3}{2}", Fraction(-3, 2)),
    ("2 \\cdot 3", Fraction(6)),
    ("\\frac{1}{46}\\binom{2024}{990}", None),     # \binom is not read
])
def test_constants_are_read(text: str, value) -> None:
    assert constant_value(text) == value


@pytest.mark.parametrize("text, value", [
    ("2\\sqrt{3}", 2 * 3 ** 0.5),
    ("\\frac{\\sqrt{5}+1}{2}", (5 ** 0.5 + 1) / 2),
    ("$2 \\cdot (\\sqrt{5}-1)$", 2 * (5 ** 0.5 - 1)),
    ("\\dfrac{\\pi}{6}", 3.141592653589793 / 6),
    ("3+\\sqrt6", 3 + 6 ** 0.5),
])
def test_irrational_constants_are_read(text: str, value: float) -> None:
    assert abs(constant_value(text) - value) < 1e-12


@pytest.mark.parametrize("text", [
    "n-1", "n(n-1)/2", "\\text{Yes}", "(2, 6), (1, n)", "3, -\\frac{3}{2}", "[0, 1]", "\\infty",
    "x^2+1", "1 + \\left\\lceil \\frac{n}{2} \\right\\rceil", "A makes 1100 on the deal", "\\frac{1}{0}", "",
])
def test_other_answers_are_not_read(text: str) -> None:
    assert constant_value(text) is None


@pytest.mark.parametrize("stored, reply", [
    ("\\frac{3}{4}", "0.75"),
    ("1/2", "\\dfrac{1}{2}"),
    ("\\frac{1}{3}", "0.333"),                  # a decimal rounds the exact value to its places
    ("2\\sqrt{3}", "\\sqrt{12}"),
    ("\\sqrt{2}", "1.414"),
    ("$10\\frac{2}{3}$", "\\frac{32}{3}"),
    ("2025", "2025."),
    ("\\pi/6", "\\frac{\\pi}{6}"),
    ("0.941.", "0.941094"),                     # a key of 3+ places is a rounded value
    ("\\(\\alpha=0.0109\\).", "0.010935"),
    ("0.0019807923", "\\dfrac{33}{16660}"),      # 2026-11-23: a 10-place key, finer than 1e-9 relative
    ("3.9906121399", "\\frac{31031}{7776}"),
])
def test_the_same_number_agrees(stored: str, reply: str) -> None:
    assert same_constant(stored, reply) is True


@pytest.mark.parametrize("stored, reply", [
    ("\\frac{3}{4}", "\\frac{4}{3}"),
    ("0.5", "0.52"),                             # 0.5 is exact at two places: no rounding allowance
    ("\\frac{1}{3}", "0.34"),
    ("2\\sqrt{3}", "3\\sqrt{2}"),
    ("2^{999}-2^{499}", "2^{999}-2^{498}"),
    ("0.0019807923", "\\dfrac{33}{16661}"),
    ("1234567890.12", "1234567890.2"),           # exact values: equal, or one rounded; not 1e-9 relative
])
def test_a_different_number_is_a_mismatch(stored: str, reply: str) -> None:
    assert same_constant(stored, reply) is False


def test_degrees_and_radians_and_long_rounded_decimals() -> None:
    # 2026-11-21 (Omni-MATH 33206, 33708, 33496): the same value written another way
    assert same_constant("\\[ \\boxed{\\frac{\\pi}{4}} \\]", "45^\\circ") is True
    assert same_constant("$60^{\\circ}$", "\\frac{\\pi}{3}") is True
    assert same_constant("\\frac{\\pi}{4}", "30^\\circ") is False
    assert same_constant("30", "30^\\circ") is True              # no pi on either side: as before
    assert same_constant("4571.8706930", "4571.87") is True      # 6 significant digits: a rounded value
    assert same_constant("1.25", "1.254") is False               # 3 significant digits, 2 places: exact


def test_numbers_past_the_float_range() -> None:
    # 2026-11-21 (q33882): a reply's 2^{2017} crashed the judge when turned into a float
    assert same_constant("\\frac{2017+1}{3}", "\\dfrac{2^{2017}+1}{3}") is False
    assert same_constant("\\frac{2^{2017}+1}{3}", "\\dfrac{2^{2017}+1}{3}") is True
    assert same_constant("10^{400}+1", "10^{400}") is False
    assert same_constant("\\sqrt{2}", "10^{400}") is None


def test_unreadable_answers_are_not_compared() -> None:
    assert same_constant("n-1", "n - 1") is None
    assert same_constant("\\frac{1}{2}", "\\text{half}") is None


def test_a_loss_is_compared_without_its_sign() -> None:
    # owner 2026-11-24: "Accept the sign ONLY for losses"
    from validate import same_answer

    loss = "A trader shorts 100 shares at \$50 and covers at \$55. What is the trader's loss? Give the answer in dollars."
    assert same_answer("500", "-500", loss) is True
    assert same_answer("$-500$", "\(500\)", loss) is True
    assert same_answer("500", "-480", loss) is False  # the size still counts
    assert same_answer("500", "-500", "By how much does the price change?") is False
    assert same_answer("500", "-500", "What is the profit or loss on the trade?") is False
    assert same_answer("500", "-500") is False
