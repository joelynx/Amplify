"""Answer keys: what the quiz grades a question with.

The contract is `pipeline/answer_key_spec.md`. `questions.answer_key` is JSON
with one entry per part the student answers (number / choice / truefalse /
expression / points). When the column is NULL, or does not hold a valid key,
a one-part key is derived from `answer`, `type` and the question text (the
spec's "Legacy rows").

Pure and I/O-free (spec §2.2 hard rule 2): parsing and validating a key, the
legacy derivation, reading what the student typed, grading one part and a
whole question, and the projections the quiz shows before and after a
submission.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.models import Question

KINDS: tuple[str, ...] = ("number", "choice", "truefalse", "expression", "points")

# Self-assessment marks (spec: Got it 1, Partial 0.5, Missed 0).
MARK_CREDIT: dict[str, float] = {"got_it": 1.0, "partial": 0.5, "missed": 0.0}


@dataclass(frozen=True, slots=True)
class Part:
    """One answer-key entry. `value` is a float (number), a letter or a sorted
    tuple of letters (choice), a bool (truefalse), LaTeX (expression), or None
    (points, whose checklist is `points`)."""

    kind: str
    label: str = ""
    ask: str = ""
    value: Any = None
    unit: str = ""
    tol: float | None = None
    options: int | None = None
    points: tuple[str, ...] = ()

    @property
    def multi(self) -> bool:
        """A choice part that asks for every correct option."""
        return self.kind == "choice" and isinstance(self.value, tuple)


# ---- Loose string match (expression parts; ported from web-mvp lib/grade.ts) ----

_BOXED_RE = re.compile(r"^\\boxed\{(.*)\}$", re.DOTALL)


def _normalize(s: str) -> str:
    out = (s or "").strip().lower()
    out = re.sub(r"\s+", "", out)
    # The closing brace goes only with `\boxed{` (it used to be stripped from
    # any answer, so `\boxed{\frac{\pi}{4}}` never matched `\frac{\pi}{4}`).
    return _BOXED_RE.sub(r"\1", out)


def loosely_equal(a: str, b: str) -> bool:
    """Exact match after stripping whitespace, case and an outer `\\boxed{}`, or a
    numerical match within 1e-3 relative tolerance when both sides are floats."""
    na = _normalize(a)
    nb = _normalize(b)
    if na == nb:
        return True
    try:
        fa = float(na)
        fb = float(nb)
    except ValueError:
        return False
    if fa == fb:
        return True
    diff = abs(fa - fb)
    scale = max(1.0, abs(fa), abs(fb))
    return diff / scale < 1e-3


# ---- LaTeX clean-up shared by every reader ---------------------------------

_WRAPPERS = ("boxed", "text", "textrm", "mathrm", "mbox", "operatorname", "textbf", "mathbf", "emph", "textit")
_SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SIMPLE_FRAC_RE = re.compile(r"\\[dt]?frac\{\s*([+-]?\d+(?:\.\d+)?)\s*\}\{\s*(\d+(?:\.\d+)?)\s*\}")


def _unwrap(s: str, name: str, sep: str) -> str:
    """Replace every `\\name{...}` (balanced braces) by `sep` + its content."""
    head = "\\" + name + "{"
    while (i := s.find(head)) >= 0:
        depth, j = 1, i + len(head)
        while j < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            j += 1
        if depth:  # unbalanced: drop the macro name, keep the rest
            return s[:i] + sep + s[i + len(head):]
        s = s[:i] + sep + s[i + len(head): j - 1] + s[j:]
    return s


def _prep(text: str) -> str:
    """Plain text from a LaTeX-ish answer: math delimiters and `\\boxed{}` /
    `\\mathrm{}` / `\\text{}` wrappers removed (a wrapper leaves a space, so a
    unit written as `12.5\\mathrm{kW}` stays separated from its number), spacing
    commands as spaces, `\\times` / `\\cdot` / `\\%` / degrees / Greek units as
    characters, a numeric `\\frac{a}{b}` as `a/b`, braces dropped."""
    s = (text or "").strip()
    s = re.sub(r"\\(?:left|right|displaystyle)\b", "", s)
    s = re.sub(r"\\[dt]frac\b", r"\\frac", s)
    s = _SIMPLE_FRAC_RE.sub(r"\1/\2", s)
    for name in _WRAPPERS:
        s = _unwrap(s, name, "" if name == "boxed" else " ")
    s = s.replace("$", "")
    s = re.sub(r"\\[()\[\]]", " ", s)
    s = re.sub(r"\^\s*\{?\s*\\circ\s*\}?|\\circ\b|\\textdegree\b|\\degree\b", "°", s)
    s = re.sub(r"\\times\b", "×", s)
    s = re.sub(r"\\cdot\b", "·", s)
    s = s.replace("\\%", "%")
    s = re.sub(r"\\Omega\b", "Ω", s)
    s = re.sub(r"\\mu\b\s*", "µ", s)
    s = re.sub(r"\\(?:[,;:! ]|quad\b|qquad\b)|~", " ", s)
    s = s.replace("{", "").replace("}", "")
    s = s.replace("−", "-").replace("–", "-")
    s = re.sub(r"[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "^" + m.group(0).translate(_SUPERSCRIPTS), s)
    s = re.sub(r"µ\s+(?=[A-Za-z])", "µ", s)
    return s.strip()


# ---- Numbers -----------------------------------------------------------------

_NUM_RE = re.compile(
    r"""^\s*(?P<sign>[+-]?)\s*
    (?:
        10\s*\^\s*\(?\s*(?P<e3>[+-]?\d+)(?:\s*\))?
      | (?P<mant>(?:\d{1,3}(?:[,\s]\d{3})+|\d+)(?:\.\d*)?|\.\d+)
        (?:\s*/\s*(?P<den>\d+(?:\.\d+)?))?
        (?:[eE](?P<e1>[+-]?\d+)
          |\s*[xX×*·]\s*10\s*\^\s*\(?\s*(?P<e2>[+-]?\d+)(?:\s*\))?)?
    )
    (?P<rest>.*)$""",
    re.VERBOSE | re.DOTALL,
)


def _read(text: str) -> tuple[float, str, bool] | None:
    """(value, text after the number, whether that text was separated from the
    number by a space or a `\\mathrm{}`-style wrapper), or None when the text
    does not start with a number. A single `x =` prefix is dropped."""
    s = _prep(text)
    if s.count("=") == 1:
        s = s.split("=", 1)[1]
    m = _NUM_RE.match(s)
    if m is None:
        return None
    if m["e3"] is not None:
        digits, exp = "1", int(m["e3"])
    else:
        digits, exp = re.sub(r"[,\s]", "", m["mant"]), int(m["e1"] or m["e2"] or 0)
    # Built from the typed digits so `1.2e5` is exactly 120000 (exact-integer keys).
    value = float(f"{digits}e{exp}")
    if m["den"]:
        den = float(m["den"])
        if den == 0:
            return None
        value /= den
    if not math.isfinite(value):
        return None
    if m["sign"] == "-":
        value = -value
    rest = m["rest"]
    spaced = rest[:1].isspace()
    rest = re.sub(r"[\s.,;:]+$", "", rest).strip()
    return value, rest, spaced


def _rest_is_unit_text(rest: str) -> bool:
    """Whether the text after a number can be unit text (anything word-like),
    rather than more mathematics or a second number."""
    if not rest:
        return True
    if rest.startswith(("^", "!")):  # 2^10, 5!: a power or a factorial, not a unit
        return False
    if re.search(r"[=+\\√π<>]", rest) or re.search(r"\b(?:sqrt|pi)\b", rest, re.IGNORECASE):
        return False
    probe = re.sub(r"\^\s*\(?[+-]?\d+\)?", "", rest)  # powers: m^3, s^-2
    probe = re.sub(r"(?<=[^\W\d_])-?\d+", "", probe)   # m3, cm2, s-1
    return not re.search(r"\d", probe)


# ---- Units -------------------------------------------------------------------

_SI_PREFIX: dict[str, int] = {"G": 9, "M": 6, "k": 3, "h": 2, "da": 1, "d": -1, "c": -2, "m": -3, "u": -6, "n": -9}
# Units an SI prefix may be put on. Deliberately small: a symbol that splits two
# ways, or is not here, is never converted.
_PREFIXABLE = frozenset(
    "m g s A K mol N Pa J W C V F Ω ohm S Wb T H Hz L l eV bar Wh VA var cal rad".split()
)
# Other units a legacy `answer` may end with.
_UNIT_WORDS = frozenset(
    """% ° °C °F rpm rps rev min mins h hr hrs hour hours sec secs second seconds day days yr yrs
    year years kmph kph mph kgf lbf lb lbs psi atm mmHg torr ft in inch inches mi mile miles yd
    knot knots Btu BTU hp HP bhp dB Rs ₹ USD INR deg degree degrees unit units tonne tonnes ton
    tons TR cc gal litre litres liter liters metre metres meter meters gm gms ppm mho Ah mAh""".split()
)


def _unit_norm(u: str) -> str:
    """A unit in one spelling for comparison: µ/μ as `u`, factors separated by
    one space, powers as `^n`, braces dropped."""
    u = (u or "").strip().replace("μ", "u").replace("µ", "u")
    u = u.replace("{", "").replace("}", "").replace("**", "^")
    u = re.sub(r"[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "^" + m.group(0).translate(_SUPERSCRIPTS), u)
    u = re.sub(r"(?<=[A-Za-z])(\d+)", r"^\1", u)
    u = re.sub(r"[·*]", " ", u)
    u = re.sub(r"\s*([/^])\s*", r"\1", u)
    return re.sub(r"\s+", " ", u).strip()


def _split_prefix(symbol: str) -> tuple[str, str] | None:
    """(prefix, unit) when `symbol` reads exactly one way as an optional SI
    prefix on a prefixable unit (`kPa` -> ('k', 'Pa'), `mm` -> ('m', 'm'))."""
    ways = [
        (p, symbol[len(p):])
        for p in ("", *_SI_PREFIX)
        if symbol.startswith(p) and symbol[len(p):] in _PREFIXABLE
    ]
    return ways[0] if len(ways) == 1 else None


def _prefix_factor(typed: str, expected: str) -> float:
    """What to multiply a number typed in `typed` by to express it in `expected`:
    a power of ten when the two differ only in the SI prefix of their first
    factor (`MPa` for `kPa`, `W` for `kW`, `mm^2 m` for `m^2 m`), else 1 (the
    typed unit is ignored)."""
    t, e = _unit_norm(typed), _unit_norm(expected)
    if not t or not e or t == e:
        return 1.0
    head = re.compile(r"^([A-Za-zΩ]+)(?:\^([+-]?\d+))?(.*)$")
    mt, me = head.match(t), head.match(e)
    if mt is None or me is None or mt[2] != me[2] or mt[3] != me[3]:
        return 1.0
    a, b = _split_prefix(mt[1]), _split_prefix(me[1])
    if a is None or b is None or a[1] != b[1] or a[0] == b[0]:
        return 1.0
    power = int(mt[2] or 1)
    return 10.0 ** ((_SI_PREFIX.get(a[0], 0) - _SI_PREFIX.get(b[0], 0)) * power)


def _clean_unit(rest: str) -> str:
    """Unit text as the quiz shows it: one space between factors, no space
    around `/` and `^`."""
    u = re.sub(r"\s+", " ", rest).strip()
    return re.sub(r"\s*([/^])\s*", r"\1", u)


def _is_unit(u: str) -> bool:
    """Whether every factor of `u` is a known unit, optionally SI-prefixed."""
    tokens = [t for t in re.split(r"[\s/·*().-]+", u) if t]
    if not tokens:
        return False
    for tok in tokens:
        tok = re.sub(r"\^[+-]?\d+$|\d+$", "", tok)
        if not tok:
            return False
        if tok not in _UNIT_WORDS and _split_prefix(tok.replace("µ", "u").replace("μ", "u")) is None:
            return False
    return True


def read_number(text: str, unit: str = "") -> float | None:
    """The student's number, in `unit`, or None when the input is not a number.

    Whitespace, `$...$`, `\\(...\\)`, `\\boxed{}`, thousands separators and any unit
    text after the number are ignored; `1/8`, `1.2e5`, `1.2x10^5`, `1.2 \\times
    10^{5}` and `38.6%` are numbers. A typed unit that is `unit` with another SI
    prefix converts the number; any other typed unit is ignored.
    """
    r = _read(text)
    if r is None:
        return None
    value, rest, _ = r
    if not _rest_is_unit_text(rest):
        return None
    return value * _prefix_factor(_clean_unit(rest), unit)


def format_number(x: float) -> str:
    """`38.6`, `1236`, `1.2e-5`: the shortest readable form, up to 10 significant digits."""
    if not math.isfinite(x):
        return str(x)
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    s = f"{x:.10g}"
    if "e" in s:
        mant, exp = s.split("e")
        s = f"{mant}e{int(exp)}"
    return s


def default_tol(part: Part) -> float:
    """Relative tolerance: the key's own, else exact for an integer with no unit
    (counts, AIME-style answers), 0.02 with a unit, 0.01 without."""
    if part.tol is not None:
        return float(part.tol)
    if not part.unit and float(part.value).is_integer():
        return 0.0
    return 0.02 if part.unit else 0.01


def number_matches(x: float, part: Part) -> bool:
    v = float(part.value)
    if v == 0:
        return abs(x) <= 1e-12
    return abs(x - v) <= default_tol(part) * abs(v)


# ---- Choices and true/false --------------------------------------------------

_OPTION_TOKEN_RE = re.compile(r"\(?([a-z]|\d{1,2})\)?[.):]?")
_TRUE = frozenset({"t", "true", "yes", "correct"})
_FALSE = frozenset({"f", "false", "no", "incorrect"})


def normalize_choice(text: str) -> tuple[str, ...] | None:
    """Option letters from `b`, `B`, `(b)`, `b)`, `b.`, `option b`, `2` (option
    numbers count from 1), or a list of them (`a, c`, `(a) and (c)`, `1 3`).
    Sorted and de-duplicated; None when any piece is not an option."""
    s = _prep(text).lower()
    s = re.sub(r"\b(?:options?|ans(?:wer)?)\b\s*:?", " ", s)
    tokens = [t for t in re.split(r"\s*(?:,|;|&|/|\band\b|\s)\s*", s) if t]
    letters: set[str] = set()
    for tok in tokens:
        m = _OPTION_TOKEN_RE.fullmatch(tok)
        if m is None:
            return None
        g = m[1]
        if g.isdigit():
            if not 1 <= int(g) <= 26:
                return None
            g = chr(ord("a") + int(g) - 1)
        letters.add(g)
    return tuple(sorted(letters)) or None


def normalize_truefalse(text: str) -> bool | None:
    """`t`/`true`/`yes`/`correct` -> True, `f`/`false`/`no`/`incorrect` -> False."""
    s = re.sub(r"[^a-z]", "", _prep(text).lower())
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    return None


# ---- Parsing a stored key ----------------------------------------------------


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _parse_part(e: Any) -> Part | None:
    if not isinstance(e, dict):
        return None
    kind = e.get("kind")
    label, ask = e.get("label", ""), e.get("ask", "")
    if isinstance(label, int) and not isinstance(label, bool):
        label = str(label)
    if not isinstance(label, str) or not isinstance(ask, (str, type(None))):
        return None
    base = {"label": label.strip(), "ask": (ask or "").strip()}
    value = e.get("value")
    if kind == "number":
        unit, tol = e.get("unit") or "", e.get("tol")
        if not _is_number(value) or not isinstance(unit, str):
            return None
        if tol is not None and (not _is_number(tol) or tol < 0):
            return None
        return Part("number", value=float(value), unit=unit.strip(), tol=tol, **base)
    if kind == "choice":
        options = e.get("options")
        if options is not None and (not isinstance(options, int) or isinstance(options, bool) or options < 1):
            return None
        if isinstance(value, str):
            letters = normalize_choice(value)
            if letters is None:
                return None
            v: Any = letters[0] if len(letters) == 1 else letters
        elif isinstance(value, list) and value and all(isinstance(x, str) for x in value):
            picked = [normalize_choice(x) for x in value]
            if any(p is None or len(p) != 1 for p in picked):
                return None
            v = tuple(sorted({p[0] for p in picked if p}))
        else:
            return None
        return Part("choice", value=v, options=options, **base)
    if kind == "truefalse":
        return Part("truefalse", value=value, **base) if isinstance(value, bool) else None
    if kind == "expression":
        if not isinstance(value, str) or not value.strip():
            return None
        return Part("expression", value=value, **base)
    if kind == "points":
        pts = e.get("points") or []
        if not isinstance(pts, list) or not all(isinstance(p, str) for p in pts):
            return None
        return Part("points", points=tuple(pts), **base)
    return None


def parse_key(raw: str | None) -> list[Part] | None:
    """The parts of an `answer_key` JSON text; None when it is NULL, not JSON, or
    not a valid key (the caller then derives the legacy key)."""
    if raw is None or not str(raw).strip():
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("v", 1) != 1:
        return None
    entries = data.get("parts")
    if not isinstance(entries, list) or not entries:
        return None
    parts = [_parse_part(e) for e in entries]
    if any(p is None for p in parts):
        return None
    return [p for p in parts if p is not None]


# ---- Legacy rows (answer_key NULL) -------------------------------------------

_ENV_RE = re.compile(r"\\begin\{(?:enumerate|itemize|description)\}|\\end\{(?:enumerate|itemize|description)\}|\\item(?![A-Za-z])")
_LEGACY_OPTION_RE = re.compile(r"\(?([A-Za-z])\)?[.)]?")


def count_options(latexcode: str | None) -> int | None:
    """The number of `\\item`s in the question's first `enumerate` (nested lists
    not counted), or None when it has none."""
    text = latexcode or ""
    start = text.find("\\begin{enumerate}")
    if start < 0:
        return None
    depth, items = 0, 0
    for m in _ENV_RE.finditer(text, start):
        tok = m.group(0)
        if tok.startswith("\\begin"):
            depth += 1
        elif tok.startswith("\\end"):
            depth -= 1
            if depth == 0:
                break
        elif depth == 1:
            items += 1
    return items or None


def _legacy_letters(answer: str) -> tuple[str, ...] | None:
    """`B`, `(b)`, `b)` -> ('b',); `A, B, C` / `(a) and (c)` -> a list. Letters only."""
    s = re.sub(r"^\s*(?:options?|ans(?:wer)?)\b\s*[:.-]?\s*", "", answer, flags=re.IGNORECASE)
    tokens = [t for t in re.split(r"\s*(?:,|;|&|\band\b|\s)\s*", s, flags=re.IGNORECASE) if t]
    letters: list[str] = []
    for tok in tokens:
        m = _LEGACY_OPTION_RE.fullmatch(tok)
        if m is None:
            return None
        letters.append(m[1].lower())
    return tuple(sorted(set(letters))) or None


def _legacy_number(answer: str) -> tuple[float, str] | None:
    """(value, unit) when the answer is a number, optionally followed by a unit."""
    r = _read(answer)
    if r is None:
        return None
    value, rest, spaced = r
    if not rest:
        return value, ""
    unit = _clean_unit(rest)
    if not _is_unit(unit):
        return None
    if not spaced and len(unit) == 1 and unit.isalpha():
        return None  # `5m`, `3h`: more likely an expression than a unit
    return value, unit


def legacy_key(answer: str | None, qtype: str | None, latexcode: str | None) -> list[Part]:
    """The one-part key of a row whose `answer_key` is NULL (spec "Legacy rows")."""
    text = (answer or "").strip()
    if not text or text.upper() in ("N/A", "NA"):
        return [Part("points")]
    if (qtype or "").strip().lower() == "objective":
        bare = re.sub(r"[\s.]+$", "", _prep(text))
        if bare.upper() in ("TRUE", "FALSE"):
            return [Part("truefalse", value=bare.upper() == "TRUE")]
        letters = _legacy_letters(bare)
        options = count_options(latexcode)
        if letters and (options is None or all(ord(x) - ord("a") < options for x in letters)):
            return [Part("choice", value=letters[0] if len(letters) == 1 else letters, options=options)]
    num = _legacy_number(text)
    if num is not None:
        return [Part("number", value=num[0], unit=num[1])]
    return [Part("expression", value=text)]


def parts_for(q: Question) -> list[Part]:
    """The question's answer key: the stored one when it is valid, else derived."""
    return parse_key(q.answer_key) or legacy_key(q.answer, q.type, q.latexcode)


# ---- Grading -----------------------------------------------------------------


def grade_part(part: Part, text: str) -> float | None:
    """Credit in [0, 1] for one part, or None when the student self-assesses it
    (`points`, and an `expression` the loose match does not accept)."""
    text = text or ""
    if part.kind == "number":
        x = read_number(text, part.unit)
        return 1.0 if x is not None and number_matches(x, part) else 0.0
    if part.kind == "choice":
        want = part.value if isinstance(part.value, tuple) else (part.value,)
        return 1.0 if normalize_choice(text) == tuple(sorted(want)) else 0.0
    if part.kind == "truefalse":
        return 1.0 if normalize_truefalse(text) is part.value else 0.0
    if part.kind == "expression":
        return 1.0 if loosely_equal(text, part.value) else None
    return None


def grade_parts(parts: Sequence[Part], inputs: Sequence[str]) -> list[float | None]:
    return [grade_part(p, t) for p, t in zip(parts, inputs)]


def apply_marks(
    credits: Sequence[float | None], marks: Sequence[str | None]
) -> tuple[list[float | None], list[str | None]]:
    """Credit the parts awaiting self-assessment from `marks` (aligned with the
    parts). Marks on auto-graded parts are ignored, so they stay locked in."""
    out_credits: list[float | None] = []
    out_marks: list[str | None] = []
    for i, c in enumerate(credits):
        m = marks[i] if i < len(marks) else None
        if c is None and m in MARK_CREDIT:
            out_credits.append(MARK_CREDIT[m])
            out_marks.append(m)
        else:
            out_credits.append(c)
            out_marks.append(None)
    return out_credits, out_marks


def question_credit(credits: Sequence[float | None]) -> float:
    """Mean credit over the parts (an unmarked part counts 0)."""
    if not credits:
        return 0.0
    return sum(c or 0.0 for c in credits) / len(credits)


def align_inputs(parts: Sequence[Part], answers: Sequence[Any] | None, user_answer: str = "") -> list[str]:
    """One input string per part: `answers` when given (a list entry for a
    multi-select part is joined), else `user_answer` for the first part."""
    if answers is None:
        values = [user_answer or ""]
    else:
        values = [
            ", ".join(str(x) for x in a) if isinstance(a, (list, tuple)) else ("" if a is None else str(a))
            for a in answers
        ]
    return (values + [""] * len(parts))[: len(parts)]


# ---- What the quiz shows -----------------------------------------------------


def public_fields(parts: Sequence[Part]) -> list[dict[str, Any]]:
    """What the quiz may show before an answer is submitted: never `value`,
    `points` or `tol`."""
    return [
        {
            "label": p.label,
            "ask": p.ask,
            "kind": p.kind,
            "unit": p.unit if p.kind == "number" else "",
            "options": p.options if p.kind == "choice" else None,
            "multi": p.multi,
        }
        for p in parts
    ]


def expected_text(part: Part) -> str | None:
    """The expected answer in the form the result shows: a number (the unit is
    separate), option letters (`b`, `a, c`), `true` / `false`, or LaTeX."""
    if part.kind == "number":
        return format_number(float(part.value))
    if part.kind == "choice":
        return ", ".join(part.value) if isinstance(part.value, tuple) else part.value
    if part.kind == "truefalse":
        return "true" if part.value else "false"
    if part.kind == "expression":
        return part.value
    return None


def read_text(part: Part, text: str) -> str | None:
    """How the app read the student's input: the number in the expected unit,
    the option letters, `true` / `false`; None when unreadable or free text."""
    if part.kind == "number":
        x = read_number(text, part.unit)
        return format_number(x) if x is not None else None
    if part.kind == "choice":
        letters = normalize_choice(text)
        return ", ".join(letters) if letters else None
    if part.kind == "truefalse":
        b = normalize_truefalse(text)
        return None if b is None else ("true" if b else "false")
    return None


def part_result(
    part: Part, text: str, credit: float | None, mark: str | None = None, *, reveal: bool = True
) -> dict[str, Any]:
    """One part of a graded submission, as returned to the quiz and stored on the
    attempt. `credit` None = awaiting self-assessment. With `reveal` False (a
    retry is allowed) the expected answer and checklist are withheld."""
    return {
        "label": part.label,
        "ask": part.ask,
        "kind": part.kind,
        "unit": part.unit if part.kind == "number" else "",
        "input": text,
        "read": read_text(part, text),
        "credit": credit,
        "mark": mark,
        "expected": expected_text(part) if reveal else None,
        "points": list(part.points) if reveal else [],
    }
