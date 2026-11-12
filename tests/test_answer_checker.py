"""The judge's comparison of a solve's answer key with the source's stored answer
(pipeline/scripts/subjects.py, tightened 2026-11-12). The cases come from the
audit of passed replies: a solver widening its own tolerance, a check skipped
when the number of values differed, unit factors applied blindly, and LaTeX
subscripts read as values."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline" / "scripts"))

import subjects  # noqa: E402


def num(value: float, unit: str = "", tol: float | None = None) -> dict:
    return {"label": "", "ask": "", "kind": "number", "value": value, "unit": unit, "tol": tol}


def key(*parts: dict) -> dict:
    return {"v": 1, "parts": list(parts)}


def mismatch(k: dict, stored: str) -> str | None:
    return subjects.reference_mismatch(k, subjects.stored_reference(stored))


@pytest.mark.parametrize(
    ("parts", "stored"),
    [
        ([num(1.142, "kW")], "1.1 kW"),  # the book rounded to its last printed digit
        ([num(1.24, "kW")], "1.2 kW"),
        ([num(141.75, "A"), num(283.5, "A")], "(a) 141.75 A (b) 283.5 A"),
        ([num(1.193, "kg/s")], "4295 kg/h"),  # per hour against per second
        ([num(7.14, "nm")], r"71.3 \AA"),  # nanometres against angstroms
        ([num(33.6, "%")], "0.336"),  # a percentage against a fraction
        ([num(7.24, "%")], r"\mathrm{CO}_{2}: 7.24\%"),  # the subscript is not a value
        ([num(0.05, "m^3/s")], r"0.05\,\mathrm{m^{3}/s}"),  # a unit power is not a value
        ([num(1.2e5, "Pa")], r"1.2 \times 10^{5} Pa"),
        ([num(5, "kW"), num(6.43, "kW"), num(2, "")], "6.43 kW"),  # the book answers one part
        ([num(6.43, "kW")], "Nu = 125.3, h = 412, Q = 6.43 kW"),  # the book adds intermediate values
        ([num(98.2, "kW"), num(248.2, "kW")], r"P_{1}=248.205 \mathrm{~kW}, P_{2}=98.205 \mathrm{~kW}"),  # order
        ([num(2.4, "kW"), num(2.4, "kW")], "2.4 kW"),  # one value for two parts
        ([num(460.6, "K")], r"187.5^{\circ} \mathrm{C}"),  # kelvin against degrees Celsius
        ([num(27.4, "K")], r"27.4^{\circ} \mathrm{C}"),  # a temperature difference
        ([num(13.5, "%")], "0.14"),  # half a unit of 0.14, exactly at the edge
        ([num(56.5, "m^3/h"), num(22.4, "m^3/h")], r"\(56.6 \mathrm{~m}^{3} \mathrm{~h}^{-1}\), \(22.3 \mathrm{~m}^{3} \mathrm{~h}^{-1}\)"),
        ([num(11.5, "MPa")], r"$11.3 \text{ MN m}^{-2}$"),  # the -2 belongs to the unit
        ([num(11929, "kW")], r"$16200\text{ H.P.}$"),  # metric horsepower
        ([num(89.6, "MPa")], r"914 \mathrm{kgf} / \mathrm{cm}^{2}"),
    ],
)
def test_agreeing_answers_pass(parts: list[dict], stored: str) -> None:
    assert mismatch(key(*parts), stored) is None


@pytest.mark.parametrize(
    ("parts", "stored"),
    [
        ([num(1055, "s", tol=0.10)], "980 s"),  # the solver's own TOL no longer counts
        ([num(13.4, "MW", tol=0.20)], "842 W"),  # x 60 came within the solver's 20 percent
        ([num(170.1, "MW")], "178.5 MW"),
        ([num(1.236, "kJ/kg")], "1236 kJ/kg"),  # same unit: a factor of 1000 is an error
        ([num(5, "kW"), num(6.9, "kW")], "6.43 kW"),  # a different number of values is still compared
        ([num(1.5, "kW")], "1 kW"),  # a plain integer gets no rounding allowance
    ],
)
def test_disagreeing_answers_are_caught(parts: list[dict], stored: str) -> None:
    assert mismatch(key(*parts), stored) is not None


def test_a_stored_option_needs_an_option_part() -> None:
    choice = {"label": "", "ask": "", "kind": "choice", "value": "c", "options": 4}
    assert mismatch(key(choice), "(c)") is None
    assert mismatch(key({**choice, "value": "b"}), "(c)") is not None
    assert mismatch(key(num(3.0)), "(c)") is not None  # the key picks no option


@pytest.mark.parametrize(
    "stored",
    [
        r"\frac{1}{2}",
        r"2^{10}",
        r"2\sqrt{3}",
        r"(1624 \times 4.187) kJ/kg",  # a product
        r"Z_{m}=2.43+j 3.97",  # a complex impedance
        r"2.2 \mathrm{~A} /-46.74^{\circ}",  # a phasor
        r"0.4545<\alpha<0.6842",  # a range
        r"\omega_{m}(t)=187-29.9 e^{-0.744 t}",  # a function of time
        "\\begin{array}{cc}\\text { Ans. } & \\tau_{1}=394649 \\mathrm{kPa}\\end{array}",  # a table
    ],
)
def test_unreadable_answers_are_not_compared(stored: str) -> None:
    assert subjects.stored_reference(stored) is None


def test_rounding_allowance_is_capped() -> None:
    ref = subjects.stored_reference(r"2 \times 10^{5} Pa")  # printed to one figure
    assert ref is not None and not subjects.value_matches(2.4e5, "Pa", ref["value"][0], ref["units"][0], ref["half"][0])


def test_two_solves_agree_only_within_the_judge_tolerance() -> None:
    assert subjects.keys_agree([num(1000, "s")], [num(1020, "s")])
    assert not subjects.keys_agree([num(1055, "s", tol=0.10)], [num(980, "s", tol=0.10)])
    assert not subjects.keys_agree([num(1.236, "kJ/kg")], [num(1236, "kJ/kg")])
