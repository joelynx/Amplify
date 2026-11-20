"""Mechanical checks on one solver reply (API run). No model is consulted.

validate_solver_text(qid, text, cfg, stored_answer) returns a dict:
  ok           the solution, rigor notes, takeaways and answer passed every check
  errors       why not (structure, markdown/LaTeX rules, length, PDF, web view)
  hint_ok      the hint (tier 1) passed its own checks (rules, length, PDF, web, leak)
  hint_errors  why not; a bad hint never blocks the solution, it is just dropped
  hint_tiers, hint_tiers_ok  how many hint tiers the reply wrote, and how many leading
               tiers passed (those are kept; a later tier that fails is dropped with the rest)
  answer_mismatch  the NUMERICAL answer differs from a numeric stored Answer
  parts        the parsed sections (None on a structural error)

Checks are the same ones the subagent-era validate.py ran, folded into one
function because the API returns the whole reply at once.

Usage from the command line (re-check a saved reply):
  python validate.py <qid> [--attempt N]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pdf import check_parts  # noqa: E402
from common import (  # noqa: E402
    app_conn,
    check_web_parts,
    content_problems,
    fetch_question,
    format_answer,
    hint_piece_name,
    hint_tier_checks,
    hint_tier_of,
    is_blank,
    load_config,
    normalize_answer,
    now_iso,
    parse_solver_output,
    q_dir,
    read_text,
    repair_slips,
    settle_hint_tiers,
    strip_code_fences,
    write_json,
)


def numeric_value(s: str | None) -> Decimal | None:
    """A plain number hidden in an answer string ('\\(025\\)', '72000 .', '1,024'),
    or None when the answer is not just a number."""
    if s is None:
        return None
    core = normalize_answer(str(s)).replace(",", "")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", core):
        return None
    try:
        return Decimal(core)
    except InvalidOperation:
        return None


# --- constants written in LaTeX (owner 2026-11-20: "extend the judge's answer comparison") ---------
# An answer that is a number written with fractions, roots, powers and pi ('\frac{3}{4}',
# '2\sqrt{3}', '\dfrac{\pi}{6}', '10\frac{2}{3}', '2^{10}-1') is compared by value; anything with a
# variable, a word, a comma list or an interval is not read and stays unchecked.

_CONST_TOKEN = re.compile(r"\\[a-zA-Z]+|\d*\.\d+|\d+|[-+*/^(){}\[\]]")
_CONST_SKIP = re.compile(r"\^\{?\\circ\}?|\\circ|°|\\%|%|\\!|\\,|\\;|\\:")
_THOUSANDS = re.compile(r"[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?")
_MAX_BITS = 20000  # a power bigger than this is not worked out


class _NotConstant(Exception):
    pass


class _ConstParser:
    r"""Recursive descent over the tokens of one answer: sums, products (also implicit, '2\sqrt3'),
    quotients, powers, \frac, \sqrt (and \sqrt[n]), \pi, parentheses and braces. A whole number
    directly followed by \frac of two whole numbers is a mixed number (AMC's '10\frac{2}{3}')."""

    def __init__(self, tokens: list[str]) -> None:
        self.t, self.k = tokens, 0

    def peek(self) -> str | None:
        return self.t[self.k] if self.k < len(self.t) else None

    def take(self, want: str | None = None) -> str:
        tok = self.peek()
        if tok is None or (want is not None and tok != want):
            raise _NotConstant
        self.k += 1
        return tok

    def expr(self):
        v = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            w = self.term()
            v = _add(v, w) if op == "+" else _add(v, _neg(w))
        return v

    def starts_factor(self) -> bool:
        tok = self.peek()
        return tok is not None and (tok[0].isdigit() or tok[0] == "." or tok in ("(", "{", "\\frac", "\\sqrt", "\\pi"))

    def term(self):
        whole = self.peek() is not None and self.peek().isdigit()
        v = self.factor()
        while True:
            if self.peek() in ("*", "/", "\\cdot", "\\times", "\\div"):
                op = self.take()
                w = self.factor()
                v = _div(v, w) if op in ("/", "\\div") else _mul(v, w)
            elif self.starts_factor():
                mixed = whole and self.peek() == "\\frac"
                start = self.k
                w = self.factor()
                if mixed and isinstance(w, Fraction) and self._plain_frac(start):
                    v = _add(v, w) if v >= 0 else _add(v, _neg(w))
                else:
                    v = _mul(v, w)
            else:
                return v
            whole = False

    def _plain_frac(self, start: int) -> bool:
        r"""Whether tokens start..k are \frac{digits}{digits} (or \frac12)."""
        body = [x for x in self.t[start + 1:self.k] if x not in ("{", "}")]
        return len(body) in (1, 2) and all(x.isdigit() for x in body)

    def factor(self):
        if self.peek() in ("-", "+"):
            return _neg(self.factor()) if self.take() == "-" else self.factor()
        base = self.atom()
        if self.peek() == "^":
            self.take()
            exp = _neg(self.atom()) if self.peek() == "-" and self.take() else self.atom()
            return _pow(base, exp)
        return base

    def arg(self):
        r"""One argument of \frac or \sqrt: a braced group, or a single digit/token ('\frac12')."""
        if self.peek() == "{":
            return self.atom()
        tok = self.peek()
        if tok is not None and tok.isdigit() and len(tok) > 1:  # \frac12: the digits are separate arguments
            self.t[self.k:self.k + 1] = [tok[0], tok[1:]]
        return self.atom()

    def atom(self):
        tok = self.take()
        if tok[0].isdigit() or tok[0] == ".":
            return Fraction(tok)
        if tok in ("(", "{"):
            v = self.expr()
            self.take(")" if tok == "(" else "}")
            return v
        if tok == "\\pi":
            return math.pi
        if tok == "\\frac":
            num = self.arg()
            return _div(num, self.arg())
        if tok == "\\sqrt":
            n = Fraction(2)
            if self.peek() == "[":
                self.take()
                n = self.expr()
                self.take("]")
            return _root(self.arg(), n)
        raise _NotConstant


def _add(a, b):
    return a + b if isinstance(a, Fraction) and isinstance(b, Fraction) else float(a) + float(b)


def _neg(a):
    return -a


def _mul(a, b):
    return a * b if isinstance(a, Fraction) and isinstance(b, Fraction) else float(a) * float(b)


def _div(a, b):
    if b == 0:
        raise _NotConstant
    return a / b if isinstance(a, Fraction) and isinstance(b, Fraction) else float(a) / float(b)


def _pow(a, b):
    if isinstance(a, Fraction) and isinstance(b, Fraction) and b.denominator == 1:
        n = abs(b.numerator)
        if a == 0 and b < 0:
            raise _NotConstant
        if n * max(abs(a.numerator).bit_length(), a.denominator.bit_length(), 1) > _MAX_BITS:
            raise _NotConstant
        return a ** b.numerator
    if isinstance(b, Fraction) and b.denominator != 1 and isinstance(a, Fraction) and a >= 0:
        return _root(a ** b.numerator, Fraction(b.denominator)) if abs(b.numerator) <= 64 else float(a) ** float(b)
    if float(a) < 0:
        raise _NotConstant
    try:
        return float(a) ** float(b)
    except OverflowError:
        raise _NotConstant from None


def _iroot(x: int, n: int) -> int | None:
    r = round(x ** (1.0 / n)) if x.bit_length() < 1000 else None
    if r is None:
        return None
    for c in (r - 1, r, r + 1):
        if c >= 0 and c ** n == x:
            return c
    return None


def _root(a, n):
    if not (isinstance(n, Fraction) and n.denominator == 1 and n > 0):
        raise _NotConstant
    k = n.numerator
    if float(a) < 0:
        if k % 2 == 0:
            raise _NotConstant
        return _neg(_root(_neg(a), n))
    if isinstance(a, Fraction):
        p, q = _iroot(a.numerator, k), _iroot(a.denominator, k)
        if p is not None and q is not None:
            return Fraction(p, q)
    return float(a) ** (1.0 / k)


def constant_value(s: str | None):
    """The value of an answer that is a number written in LaTeX: a Fraction when exact, a float
    when it has a root or pi; None when the answer is not such a number."""
    if s is None:
        return None
    core = normalize_answer(str(s)).replace("−", "-")
    core = re.sub(r"\\[dt]frac", r"\\frac", core)
    core = re.sub(r"^\\?[a-zA-Z]\w*=", "", core)  # "n=5"
    core = _CONST_SKIP.sub("", core)
    if _THOUSANDS.fullmatch(core):
        core = core.replace(",", "")
    if not core or re.search(r"[^\\a-zA-Z0-9.+\-*/^(){}\[\]]", core):
        return None
    tokens = _CONST_TOKEN.findall(core)
    if "".join(tokens) != core:  # a letter outside a known command, or a stray character
        return None
    p = _ConstParser(tokens)
    try:
        v = p.expr()
        if p.peek() is not None:
            return None
    except (_NotConstant, ZeroDivisionError, OverflowError, ValueError):
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _decimals(s: str) -> int | None:
    """Decimal places of an answer that is a plain decimal number ('0.333'), else None."""
    m = re.fullmatch(r"[-+]?\d*\.(\d+)", re.sub(r"^\\?[a-zA-Z]\w*=", "", normalize_answer(str(s))))
    return len(m.group(1)) if m else None


def _terminates(x: Fraction) -> bool:
    """Whether x has an exact decimal form (its denominator has no prime but 2 and 5)."""
    q = x.denominator
    for f in (2, 5):
        while q % f == 0:
            q //= f
    return q == 1


def _places(x: Fraction) -> int:
    """Decimal places of a number with an exact decimal form."""
    k = 0
    while (x * 10 ** k).denominator != 1:
        k += 1
    return k


def same_constant(stored: str, reply: str) -> bool | None:
    r"""Whether two answers are the same number (None if either is not a number we can read).
    Exact values must be equal; a root or pi is compared to 1e-9 relative. A plain decimal on one
    side may be the other side rounded to its places when that side has no exact decimal form
    ('0.333' for \frac13, a root, pi), or when the decimal has 3 places or more and the other side
    more ('0.941' for 0.941094); a short decimal is exact: 0.52 is not 0.5."""
    a, b = constant_value(stored), constant_value(reply)
    if a is None or b is None:
        return None
    if isinstance(a, Fraction) and isinstance(b, Fraction) and a == b:
        return True
    tol = 1e-9 * max(1.0, abs(float(a)), abs(float(b)))
    for text, other in ((stored, b), (reply, a)):
        d = _decimals(text)
        if d is not None and (not (isinstance(other, Fraction) and _terminates(other)) or (d >= 3 and _places(other) > d)):
            tol = max(tol, 0.5 * 10 ** -d + 1e-12)
    if isinstance(a, Fraction) and isinstance(b, Fraction) and tol <= 1e-9 * max(1.0, abs(float(a)), abs(float(b))):
        return False
    return abs(float(a) - float(b)) <= tol


def hint_leak_errors(hint: str, answer_type: str, answer: str) -> list[str]:
    """The hint must not contain the final answer (normalised LaTeX, and for
    numerical answers the bare number)."""
    errs: list[str] = []
    if answer_type == "NONE":
        return errs
    na = normalize_answer(answer)
    nh = re.sub(r"\s+", "", hint).replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "")
    if len(na) >= 2 and na in nh:
        errs.append("leak: hint contains the final answer")
    if answer_type == "NUMERICAL":
        num = re.sub(r"[^0-9.]", "", na)
        if len(num.replace(".", "")) >= 2 and re.search(rf"(?<![\d.]){re.escape(num)}(?![\d.])", hint):
            errs.append(f"leak: hint contains the numerical answer {num}")
    return errs


def validate_solver_text(qid: int, text: str, cfg: dict, stored_answer: str | None) -> dict:
    d = q_dir(qid)
    res: dict = {
        "question_id": qid,
        "checked_at": now_iso(),
        "errors": [],
        "hint_errors": [],
        "answer_mismatch": False,
        "parts": None,
    }
    text, fenced = strip_code_fences(text)
    if fenced:
        res["code_fences_stripped"] = True
    text, repairs = repair_slips(text)
    if repairs:
        res["repairs"] = repairs
    parts, errs = parse_solver_output(text, fmt="v5")
    res["errors"] += [f"structure: {e}" for e in errs]
    if parts is None:
        res["ok"] = False
        res["hint_ok"] = False
        return res
    res["parts"] = parts
    res["answer_type"] = parts["answer_type"]
    res["solution_chars"] = len(parts["solution"])

    # The answer is checked in the exact form assemble.py will store it.
    formatted_answer = format_answer(parts["answer_type"], parts["answer"])
    main: dict[str, str] = {"solution": parts["solution"]}
    if parts["rigor"]:
        main["rigor"] = parts["rigor"]
    main["takeaways"] = parts["takeaways"]
    if formatted_answer is not None:
        main["answer"] = formatted_answer
    for name, body in main.items():
        res["errors"] += [f"rules [{name}]: {p}" for p in content_problems(body)]
    b = cfg.get("solution_length_bounds_chars") or {}
    n = len(parts["solution"])
    if b.get("min") is not None and n < b["min"]:
        res["errors"].append(f"length: solution {n} chars < min {b['min']}")
    if b.get("max") is not None and n > b["max"]:
        res["errors"].append(f"length: solution {n} chars > max {b['max']}")

    # Each hint tier gets the checks the single hint got; the leading tiers that pass are kept.
    tiers = parts["hint_tiers"] or [parts["hint"] or ""]
    tier_errs = hint_tier_checks(tiers, cfg, lambda h: hint_leak_errors(h, parts["answer_type"], parts["answer"]))

    # One XeLaTeX compile for everything on the happy path; per-part on failure.
    pieces = dict(main)
    for k, tier in enumerate(tiers):
        pieces[hint_piece_name(k)] = tier
    pdf = check_parts(pieces, cfg=cfg)
    res["pdf_ok"] = pdf["ok"]
    for e in pdf["errors"]:
        k = hint_tier_of(e, len(tiers))
        (tier_errs[k] if k is not None else res["errors"]).append(f"pdf: {e}")
    if not pdf["ok"]:
        res["pdf_log_tail"] = pdf["log_tail"][-1200:]
    web = check_web_parts(pieces, d)
    res["web_ok"] = web["ok"]
    for e in web["errors"]:
        k = hint_tier_of(e, len(tiers))
        (tier_errs[k] if k is not None else res["errors"]).append(f"web: {e}")

    # Stored Answer (e.g. AIME, an answer key): a free correctness signal. Numbers are compared,
    # also when written with fractions, roots, powers or pi (since 2026-11-20); anything else
    # (variables, lists, words) is left to the solver.
    if cfg.get("check_stored_numeric_answer", True) and parts["answer_type"] != "NONE":
        same = same_constant(stored_answer, parts["answer"])
        if same is not None:
            sv = numeric_value(stored_answer)
            res["stored_answer"] = str(sv) if sv is not None else normalize_answer(str(stored_answer))
            res["answer_mismatch"] = not same

    res["ok"] = not res["errors"]
    settle_hint_tiers(res, tiers, tier_errs)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("qid", type=int)
    ap.add_argument("--attempt", type=int, default=1)
    a = ap.parse_args()
    cfg = load_config()
    app = app_conn(cfg)
    q = fetch_question(app, a.qid)
    if q is None:
        raise SystemExit(f"{a.qid}: not in database")
    stored = None if is_blank(q["answer"], cfg["empty_answer_sentinels"]) else q["answer"]
    text = read_text(q_dir(a.qid) / f"solver_{a.attempt}.tex")
    res = validate_solver_text(a.qid, text, cfg, stored)
    write_json(q_dir(a.qid) / f"validate_{a.attempt}_manual.json", res)
    print(json.dumps({k: v for k, v in res.items() if k != "parts"}, indent=2))


if __name__ == "__main__":
    main()
