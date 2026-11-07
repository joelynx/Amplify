"""Answer keys (pipeline/answer_key_spec.md): reading student input, grading a
part, the legacy derivation for rows without a key, and what the quiz may show."""

from __future__ import annotations

import json

import pytest

from app.core import answer_key as ak
from app.core.answer_key import Part
from app.core.models import Question
from app.interactive.scoring import grade, loosely_equal


def _q(**kw) -> Question:
    base = dict(question_id=1, topic="T", branch="B", subtopic="S", latexcode="x", latex_hash="h",
                in_syllabus=1, times_used=0, interactive_times_used=0)
    return Question(**{**base, **kw})


def _num(value: float, unit: str = "", tol: float | None = None) -> Part:
    return Part("number", value=value, unit=unit, tol=tol)


# ---- Reading numbers ---------------------------------------------------------

@pytest.mark.parametrize(
    "text, expected",
    [
        ("12.5", 12.5),
        ("-3", -3.0),
        ("+3", 3.0),
        (".5", 0.5),
        ("1/8", 0.125),
        ("-3/4", -0.75),
        (r"\frac{1}{8}", 0.125),
        (r"\boxed{1/8}", 0.125),
        (r"\boxed{\frac{1}{8}}", 0.125),
        ("$12.5$", 12.5),
        (r"\(12.5\)", 12.5),
        ("72,000", 72000.0),
        ("1,000,000", 1_000_000.0),
        ("1 000 000", 1_000_000.0),
        (r"72\,000", 72000.0),
        ("x = 5", 5.0),
        ("  42  ", 42.0),
        ("72000 .", 72000.0),
    ],
)
def test_read_plain_numbers(text, expected):
    assert ak.read_number(text) == pytest.approx(expected)


@pytest.mark.parametrize(
    "text",
    ["1.2e5", "1.2E5", "1.2x10^5", "1.2X10^5", "1.2*10^5", r"1.2 \times 10^{5}", "1.2 × 10^5",
     "1.2·10^5", r"1.2 \cdot 10^{5}", "1.2x10⁵", "120000", "1.2e+5"],
)
def test_read_scientific_notation(text):
    assert ak.read_number(text) == pytest.approx(1.2e5)


def test_read_negative_exponents_and_bare_powers_of_ten():
    assert ak.read_number("1.2E-3") == pytest.approx(1.2e-3)
    assert ak.read_number(r"1.2 \times 10^{-3}") == pytest.approx(1.2e-3)
    assert ak.read_number("10^{-3}") == pytest.approx(1e-3)
    assert ak.read_number("1.2e5") == 120000.0  # exact, for integer keys


def test_read_percent():
    assert ak.read_number("38.6%") == pytest.approx(38.6)
    assert ak.read_number("38.6 %", "%") == pytest.approx(38.6)
    assert ak.read_number(r"38.6\%", "%") == pytest.approx(38.6)


@pytest.mark.parametrize("text", ["", "   ", "abc", "12 15", "1,5", "5 + 3", r"2\pi", "2pi", r"3\sqrt{2}",
                                  "1/0", "1e400", "(2, 3)", "5 and 7", "2^10", "5!"])
def test_read_rejects_non_numbers(text):
    assert ak.read_number(text) is None


# ---- Units -------------------------------------------------------------------

@pytest.mark.parametrize(
    "text, unit, expected",
    [
        ("12.5 kW", "kW", 12.5),
        ("12.5kW", "kW", 12.5),
        ("$12.5$ kW", "kW", 12.5),
        (r"12.5\,\mathrm{kW}", "kW", 12.5),
        ("1236 kJ/kg", "kJ/kg", 1236.0),
        ("3 m^3/s", "m^3/s", 3.0),
        ("3 m3/s", "m^3/s", 3.0),
        ("5 N m", "N m", 5.0),
        ("9.81 m s-2", "m/s^2", 9.81),  # unit text it cannot match is ignored
        ("25 °C", "°C", 25.0),
        ("40 rpm", "rpm", 40.0),
    ],
)
def test_units_are_stripped(text, unit, expected):
    assert ak.read_number(text, unit) == pytest.approx(expected)


@pytest.mark.parametrize(
    "text, unit, expected",
    [
        ("1.2 MPa", "kPa", 1200.0),
        ("1200000 Pa", "kPa", 1200.0),
        ("1500 W", "kW", 1.5),
        ("0.5 MW", "kW", 500.0),
        ("5 mm", "m", 0.005),
        ("250 cm", "m", 2.5),
        ("3 km", "m", 3000.0),
        ("2 cm^2", "m^2", 2e-4),
        ("3 MJ/kg", "kJ/kg", 3000.0),
        ("1236000 J/kg", "kJ/kg", 1236.0),
        ("250 um", "mm", 0.25),
        ("250 µm", "mm", 0.25),
        ("2 kN m", "N m", 2000.0),
        ("4 MWh", "kWh", 4000.0),
        ("20 ms", "s", 0.02),
        ("1 dam", "m", 10.0),
        ("1 hPa", "Pa", 100.0),
        ("5 nF", "uF", 0.005),
    ],
)
def test_si_prefix_conversion(text, unit, expected):
    assert ak.read_number(text, unit) == pytest.approx(expected)


@pytest.mark.parametrize(
    "text, unit",
    [
        ("5 min", "s"),        # not a prefixed second
        ("5 Kpa", "kPa"),      # unknown spelling: ignored, read in the expected unit
        ("5 KW", "kW"),
        ("300 K", "°C"),       # different unit, not a prefix
        ("5 kg/m^3", "g/cm^3"),  # prefixes on other factors are not converted
        ("5 kNm", "N m"),      # glued symbol that does not split one way
        ("5 h", "s"),
        ("5 bananas", "kg"),
        ("5 kW", ""),          # nothing expected: any typed unit is ignored
        ("5 %", ""),
    ],
)
def test_other_units_are_ignored(text, unit):
    assert ak.read_number(text, unit) == pytest.approx(5.0 if "300" not in text else 300.0)


# ---- Tolerances --------------------------------------------------------------

def test_integer_without_unit_is_exact():
    p = _num(25)
    assert ak.grade_part(p, "25") == 1.0
    assert ak.grade_part(p, "25.0") == 1.0
    assert ak.grade_part(p, "025") == 1.0
    assert ak.grade_part(p, "2.5e1") == 1.0
    assert ak.grade_part(p, "25.01") == 0.0
    assert ak.grade_part(p, "24.999") == 0.0
    assert ak.default_tol(p) == 0.0


def test_default_tolerance_without_unit_is_one_percent():
    p = _num(0.125)
    assert ak.default_tol(p) == 0.01
    assert ak.grade_part(p, "0.126") == 1.0   # 0.8 %
    assert ak.grade_part(p, "1/8") == 1.0
    assert ak.grade_part(p, "0.127") == 0.0   # 1.6 %


def test_default_tolerance_with_unit_is_two_percent():
    p = _num(1236, "kJ/kg")
    assert ak.default_tol(p) == 0.02
    assert ak.grade_part(p, "1260") == 1.0          # 1.9 %
    assert ak.grade_part(p, "1270 kJ/kg") == 0.0    # 2.8 %
    assert ak.grade_part(p, "1.24 MJ/kg") == 1.0
    assert ak.grade_part(p, "1.24") == 0.0          # read in kJ/kg
    # an integer with a unit is not exact
    assert ak.grade_part(_num(12, "kW"), "12.2") == 1.0


def test_explicit_tolerance_and_zero():
    assert ak.grade_part(_num(100, "kW", tol=0.05), "104") == 1.0
    assert ak.grade_part(_num(100, "kW", tol=0.05), "106") == 0.0
    assert ak.grade_part(_num(0), "0") == 1.0
    assert ak.grade_part(_num(0), "0.0") == 1.0
    assert ak.grade_part(_num(0, "m"), "0.001") == 0.0
    assert ak.grade_part(_num(-2.5), "-2.5") == 1.0
    assert ak.grade_part(_num(-2.5), "2.5") == 0.0


def test_unreadable_number_scores_zero():
    assert ak.grade_part(_num(5), "") == 0.0
    assert ak.grade_part(_num(5), "five") == 0.0


# ---- Choices and true/false --------------------------------------------------

@pytest.mark.parametrize("text", ["b", "B", "(b)", "(B)", "b)", "b.", "option b", "Option (B)", "2", " 2 ", "$b$"])
def test_choice_normalization(text):
    assert ak.normalize_choice(text) == ("b",)


@pytest.mark.parametrize("text", ["a, c", "c,a", "(a) and (c)", "A; C", "1, 3", "a c", "(a), (c)", "a & c"])
def test_choice_lists(text):
    assert ak.normalize_choice(text) == ("a", "c")


@pytest.mark.parametrize("text", ["", "bogus", "b, maybe", "0", "27"])
def test_choice_rejects(text):
    assert ak.normalize_choice(text) is None


def test_grade_choice_single_and_multi():
    single = Part("choice", value="b", options=4)
    assert ak.grade_part(single, "2") == 1.0
    assert ak.grade_part(single, "(b)") == 1.0
    assert ak.grade_part(single, "a") == 0.0
    assert ak.grade_part(single, "") == 0.0
    multi = Part("choice", value=("a", "c"), options=4)
    assert multi.multi
    assert ak.grade_part(multi, "a, c") == 1.0
    assert ak.grade_part(multi, "3, 1") == 1.0
    assert ak.grade_part(multi, "a") == 0.0
    assert ak.grade_part(multi, "a, b, c") == 0.0


@pytest.mark.parametrize("text, expected", [
    ("t", True), ("T", True), ("true", True), ("TRUE", True), ("Yes", True), ("correct", True), ("True.", True),
    ("f", False), ("false", False), ("No", False), ("incorrect", False),
    ("", None), ("maybe", None), ("not correct", None),
])
def test_truefalse_normalization(text, expected):
    assert ak.normalize_truefalse(text) is expected


def test_grade_truefalse():
    p = Part("truefalse", value=False)
    assert ak.grade_part(p, "F") == 1.0
    assert ak.grade_part(p, "true") == 0.0
    assert ak.grade_part(p, "") == 0.0


def test_expression_and_points_need_self_assessment_unless_matched():
    expr = Part("expression", value=r"\frac{\pi}{4}")
    assert ak.grade_part(expr, r"\frac{\pi}{4}") == 1.0
    assert ak.grade_part(expr, r" \boxed{\frac{\pi}{4}} ") == 1.0
    assert ak.grade_part(expr, "pi/4") is None
    assert ak.grade_part(Part("points", points=("x",)), "anything") is None
    assert loosely_equal("0.5", "0.5001")  # still exported for existing callers


# ---- Stored keys -------------------------------------------------------------

SPEC_KEY = {
    "v": 1,
    "parts": [
        {"label": "a", "ask": "thermal efficiency of the reheat cycle", "kind": "number",
         "value": 38.6, "unit": "%", "tol": None},
        {"label": "b", "ask": "net work per kg of steam", "kind": "number",
         "value": 1236, "unit": "kJ/kg", "tol": 0.05},
        {"label": "c", "ask": "", "kind": "choice", "value": "b", "options": 4},
        {"label": "d", "ask": "", "kind": "choice", "value": ["a", "c"], "options": 4},
        {"label": "e", "ask": "", "kind": "truefalse", "value": True},
        {"label": "f", "ask": "", "kind": "expression", "value": "\\frac{\\pi}{4}"},
        {"label": "g", "ask": "function of a cooling tower", "kind": "points",
         "points": ["rejects the condenser heat to the atmosphere", "..."]},
    ],
}


def test_parse_spec_example():
    parts = ak.parse_key(json.dumps(SPEC_KEY))
    assert parts is not None and [p.kind for p in parts] == [
        "number", "number", "choice", "choice", "truefalse", "expression", "points"]
    assert parts[0].value == 38.6 and parts[0].unit == "%" and parts[0].tol is None
    assert parts[1].tol == 0.05
    assert parts[2].value == "b" and not parts[2].multi
    assert parts[3].value == ("a", "c") and parts[3].multi
    assert parts[4].value is True
    assert parts[6].points == ("rejects the condenser heat to the atmosphere", "...")


@pytest.mark.parametrize("raw", [
    None, "", "not json", "[1, 2]", json.dumps({"v": 2, "parts": SPEC_KEY["parts"]}),
    json.dumps({"v": 1, "parts": []}),
    json.dumps({"v": 1, "parts": [{"kind": "number", "value": "38.6"}]}),
    json.dumps({"v": 1, "parts": [{"kind": "number", "value": 1, "tol": -1}]}),
    json.dumps({"v": 1, "parts": [{"kind": "choice", "value": "bogus"}]}),
    json.dumps({"v": 1, "parts": [{"kind": "truefalse", "value": "true"}]}),
    json.dumps({"v": 1, "parts": [{"kind": "essay"}]}),
])
def test_invalid_keys_are_rejected(raw):
    assert ak.parse_key(raw) is None


def test_bad_key_falls_back_to_legacy():
    q = _q(answer_key="{oops", answer="12.5 kW", type="numerical")
    [p] = ak.parts_for(q)
    assert (p.kind, p.value, p.unit) == ("number", 12.5, "kW")


# ---- Legacy derivation -------------------------------------------------------

MCQ = r"""Which is true?
\begin{enumerate}
  \item first \begin{enumerate}\item nested\end{enumerate}
  \item second
  \itemsep 2pt
  \item third
  \item fourth
\end{enumerate}
\begin{enumerate}\item later list\end{enumerate}"""


def test_count_options():
    assert ak.count_options(MCQ) == 4
    assert ak.count_options("no list here") is None
    assert ak.count_options(None) is None


@pytest.mark.parametrize("answer, value", [
    ("B", "b"), ("(b)", "b"), ("b)", "b"), ("(B).", "b"), ("A, B, C", ("a", "b", "c")),
    ("(a) and (c)", ("a", "c")),
])
def test_legacy_objective_choices(answer, value):
    [p] = ak.legacy_key(answer, "objective", MCQ)
    assert (p.kind, p.value, p.options, p.label) == ("choice", value, 4, "")


def test_legacy_objective_truefalse_and_fallbacks():
    [p] = ak.legacy_key("TRUE", "objective", None)
    assert (p.kind, p.value) == ("truefalse", True)
    [p] = ak.legacy_key("False", "objective", None)
    assert (p.kind, p.value) == ("truefalse", False)
    # a letter past the listed options is not an option
    [p] = ak.legacy_key("E", "objective", MCQ)
    assert p.kind == "expression"
    # an objective question with a numeric answer
    [p] = ak.legacy_key("10", "objective", MCQ)
    assert (p.kind, p.value) == ("number", 10.0)
    # letters only count as options on objective questions
    [p] = ak.legacy_key("B", "numerical", MCQ)
    assert p.kind == "expression"


@pytest.mark.parametrize("answer, value, unit", [
    ("72000 .", 72000.0, ""),
    (r"\(025\)", 25.0, ""),
    ("12.5 kW", 12.5, "kW"),
    (r"$12.5\ \mathrm{kW}$", 12.5, "kW"),
    (r"1236\,\mathrm{kJ/kg}", 1236.0, "kJ/kg"),
    (r"38.6\%", 38.6, "%"),
    (r"9.81 \mathrm{m/s^{2}}", 9.81, "m/s^2"),
    (r"1.2 \times 10^{-3}\,\mathrm{m}", 1.2e-3, "m"),
    (r"100^\circ\mathrm{C}", 100.0, "°C"),
    (r"\frac{1}{8}", 0.125, ""),
    ("-3", -3.0, ""),
    ("5 m", 5.0, "m"),
])
def test_legacy_numbers(answer, value, unit):
    [p] = ak.legacy_key(answer, "numerical", None)
    assert p.kind == "number" and p.value == pytest.approx(value) and p.unit == unit


def test_legacy_aime_answer_is_exact():
    [p] = ak.legacy_key(r"\(025\)", "numerical", None)
    assert ak.grade_part(p, "25") == 1.0
    assert ak.grade_part(p, "25.2") == 0.0


@pytest.mark.parametrize("answer", [r"\frac{\pi}{4}", r"2\sqrt{3}", "3x", "5m", "2, 3", "(1, 2)", "n = 2k + 1",
                                    "5 and 7", "2^{10}"])
def test_legacy_expressions(answer):
    [p] = ak.legacy_key(answer, "numerical", None)
    assert (p.kind, p.value) == ("expression", answer)


@pytest.mark.parametrize("answer", [None, "", "   ", "N/A", "na"])
def test_legacy_empty_answer_is_self_assessed(answer):
    [p] = ak.legacy_key(answer, "proof", None)
    assert (p.kind, p.points) == ("points", ())
    assert ak.grade_part(p, "") is None


def test_scoring_grade_routes_through_the_key():
    assert grade(_q(answer="12.5 kW", type="numerical"), "12.6") is True
    assert grade(_q(answer="12.5 kW", type="numerical"), "12.5 W") is False
    assert grade(_q(answer="(b)", type="objective", latexcode=MCQ), "2") is True
    assert grade(_q(answer="", type="proof"), "whatever") is None


# ---- What the quiz shows -----------------------------------------------------

def test_public_fields_never_carry_the_answer():
    fields = ak.public_fields(ak.parse_key(json.dumps(SPEC_KEY)))
    assert fields[0] == {"label": "a", "ask": "thermal efficiency of the reheat cycle", "kind": "number",
                         "unit": "%", "options": None, "multi": False}
    assert fields[2] == {"label": "c", "ask": "", "kind": "choice", "unit": "", "options": 4, "multi": False}
    assert fields[3]["multi"] is True
    assert fields[6] == {"label": "g", "ask": "function of a cooling tower", "kind": "points",
                         "unit": "", "options": None, "multi": False}
    for f in fields:
        assert set(f) == {"label", "ask", "kind", "unit", "options", "multi"}
    text = json.dumps(fields)
    for secret in ("38.6", "1236", "frac", "condenser", "0.05"):
        assert secret not in text


def test_part_result_reveal_and_withhold():
    p = Part("number", label="b", value=1236, unit="kJ/kg")
    shown = ak.part_result(p, "1.24 MJ/kg", 1.0)
    assert shown == {"label": "b", "ask": "", "kind": "number", "unit": "kJ/kg", "input": "1.24 MJ/kg",
                     "read": "1240", "credit": 1.0, "mark": None, "expected": "1236", "points": []}
    hidden = ak.part_result(Part("points", points=("x",)), "", None, reveal=False)
    assert hidden["expected"] is None and hidden["points"] == []
    assert ak.part_result(Part("choice", value=("a", "c")), "1, 3", 1.0)["read"] == "a, c"
    assert ak.part_result(Part("choice", value=("a", "c")), "1, 3", 1.0)["expected"] == "a, c"


def test_marks_and_credit():
    credits, marks = ak.apply_marks([1.0, None, 0.0, None], ["missed", "partial", "got_it", None])
    assert credits == [1.0, 0.5, 0.0, None]  # auto-graded parts stay locked in
    assert marks == [None, "partial", None, None]
    assert ak.question_credit([1.0, 0.5, 0.0]) == pytest.approx(0.5)
    assert ak.align_inputs([Part("points")] * 3, ["a", ["b", "c"]]) == ["a", "b, c", ""]
    assert ak.align_inputs([Part("points")] * 2, None, "x") == ["x", ""]


def test_format_number():
    assert ak.format_number(38.6) == "38.6"
    assert ak.format_number(1236.0) == "1236"
    assert ak.format_number(1.2e-5) == "1.2e-5"
    assert ak.format_number(-0.0) == "0"
