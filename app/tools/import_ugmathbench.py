"""Import UGMathBench (github.com/YangLabHKUST/UGMathBench, huggingface.co/datasets/UGMathBench/ugmathbench,
GPL-3.0; Amplify is private): 5,061 undergraduate problems translated from WeBWorK, each with three
randomised variants and an answer in WeBWorK formula syntax; no solutions, no figures. Owner-approved pilot
(2026-11-22): version 1 only, and only the problems with exactly one answer blank and one answer.

Dropped on purpose: the survey's skip list (a missing figure, graph or sketch; a blank/answer count mismatch;
a need for software, a calculator or a statistical table; unbalanced braces or an odd number of $;
WeBWorK artefacts and boilerplate; translator errors), Set theory and logic (no bank subject) and any
row whose text or answer cannot be turned into clean LaTeX by rule (the reason is listed).

Text: the single [ANS] becomes a visible blank (\\underline{\\hspace{2cm}}) or, in a multiple-choice problem,
disappears with the options set one per line as "(A) ..."; \\( \\) becomes $ $; bare LaTeX the translation left
outside $ $ is wrapped in $ $ when its extent is clear; WeBWorK syntax hints ("Use sqrt()", "Usage: ...",
"enter DNE") and doubled sentences are removed; instructions that define the answer form are kept.
Answer: numbers stay plain; WeBWorK expressions are converted to LaTeX by the small parser below (value never
changed); intervals use \\infty and \\cup; multiple choice is the letter(s).

Every row is math, solved by the math solver (model and effort in --assignments).

Usage (repo root):
  python -m app.tools.import_ugmathbench --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_ugmathbench --data DIR --apply
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import json
import math
import re
import sqlite3
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from app.tools.import_answer_sets import duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "UGMathBench"
OPUS = "claude-opus-5-5"
EFFORT = "medium"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")  # git-ignored: question id -> set, number
ASSIGNMENTS = Path("pipeline/benchmarks_assignments.json")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/ugmathbench_set_aside.json")  # git-ignored: rows left out for a hand fix
FIXES_PATH = Path(__file__).with_name("ugmathbench_fixes.json")
BLANK = r"\underline{\hspace{2cm}}"
SKIP_SUBJECTS = {"Set_theory_and_logic"}


class Fail(Exception):
    """The text or answer cannot be converted by rule: the row is dropped with this reason."""


# --- the survey's skip list --------------------------------------------------------------------------

def skip_reason(r: dict) -> str | None:
    t = r["problem_v1"]
    a = r["answer_v1"]
    if r["subject"] in SKIP_SUBJECTS:
        return "Set theory and logic (no bank subject)"
    if not a or t.count("[ANS]") != len(a):
        return "blank/answer count mismatch"
    if len(a) != 1:
        return "more than one answer blank"
    if re.search(r"IDPREFIX|<answer|classviva|Undefined_User", t):
        return "WeBWorK artefact"
    if "ERROR caught" in t:
        return "translator error"
    if len(re.findall(r"(?<!\\)\$", t)) % 2 == 1 and "\\$" not in t:
        return "odd number of $"
    if t.count("{") != t.count("}"):
        return "unbalanced braces"
    if re.search(r"(?i)\b(applet|use (a )?(calculator|software|computer|excel|spreadsheet)|calculator or|technology)\b"
                 r"|(graphing|scientific) (calculator|program)|(using|with|on|from|and) (a|your|the) calculator"
                 r"|Submit Answer|press the", t):
        return "needs software or a calculator"
    if re.search(r"(?i)\b(z-table|normal table|statistical table|t-table|chi-square table|table of|use a table|"
                 r"from the table|look up)\b", t):
        return "needs a statistical table"
    if re.search(r"(?i)(table|graph|figure|picture|diagram|plot)s? (above|below|shown|at the right)|shown (above|below)"
                 r"|the (figure|graph|picture|diagram)\b|sketch", t):
        return "missing figure, graph or sketch"
    return None


# --- the problem text ----------------------------------------------------------------------------------

UNICODE = {"\u2019": "'", "\u2018": "'", "\u201c": "``", "\u201d": "''", "\u2013": "--", "\u2014": "---",
           "\u00a0": " ", "\u2212": "-", "\u00b0": r"$^\circ$", "\u2026": r"\ldots{}"}
HINTS = [  # WeBWorK software syntax and answer-box entry notes, which mean nothing in a printed question
    r"Usage:[^\n]*",
    r"Help:[^\n]*",
    r"Now draw a graph of[^.\n]*\.",
    r"\((?:Enter|enter)[^)\n]*(?:DNE|undef|undefined|NONE)[^)\n]*\)\.?",
    r"Enter I for[^\n]*?DNE[^.\n]*\.",
    r"Notes?: if the vector field is not conservative, write \"DNE\"\.",
    r"(?:Notes?:\s*)?Use sqrt\(\)[^.\n]*\.",
    r"For example:\s*\$[^$]*\$\s*=\s*sqrt\([^)]*\)\.?",
    r"Use sqrt for the square root symbol[^(\n]*\(Example:[^)\n]*\)[^)\n]*\)?\.?",
    r"Remember, to enter a fraction[^.\n]*\.",
    r"(?:Notes?:\s*)?You cannot use any operations except[^.\n]*\.",
    r"Use degC for[^.\n]*\.",
    r"If needed you can enter \$\\pi\$ as pi\.",
    r"(?:Notes?:\s*)?Use pi for[^.\n]*\.",
    r"\(Give your answer as an interval or a list of intervals[^\n]*",
    r"Notes?:\s*Enter\s+\"?'?(?:DNE|NONE|None)'?\"?[^.\n]*\.",
    r"(?:If|When)[^.?!\n]{0,90}?,?\s*(?:enter|type|you may enter)\s+(?:the word\s+)?[\"']?(?:DNE|NONE|None|none|dne|prime)[\"']?"
    r"(?:\s+or\s+[\"']?(?:DNE|NONE)[\"']?)?(?:\s+in the answer blank)?[^.?!\n]*[.?!]?",
    r"Enter\s+[\"']?(?:DNE|NONE|None)[\"']?\s+if[^.\n]*\.",
    r"\(?(?:Be sure NOT TO USE ANY COMMAS|do not enter commas)[^)\n]*\)?\.?",
    r"For example enter two thousand as[^)\n]*\)?\.?",
    r"Do not enter any commas or units in your answer\.",
    r"Be sure to use the correct case of the variable[^.\n]*\.",
    r"Use \$?C\$? to denote the arbitrary constant[^.\n]*\.",
]
HINT_RE = re.compile("|".join(f"(?:{h})" for h in HINTS), re.I)
SENTENCE_RE = re.compile(r"[^.?!\n]*[.?!]")
TEXTCMDS = {"textbf", "textit", "emph", "textrm", "textsf", "texttt", "underline"}  # text-mode commands: left alone
SPACING = {"quad", "qquad", "text", "mbox", "mathrm", "left", "right", "hspace", "hbox"}
FUNCS = {"sin", "cos", "tan", "sec", "csc", "cot", "ln", "log", "exp", "lim", "min", "max", "arcsin", "arccos",
         "arctan", "sinh", "cosh", "tanh", "det", "gcd", "mod"}


def to_dollars(t: str) -> str:
    t = re.sub(r"\\\((.*?)\\\)", lambda m: "$" + m.group(1).strip() + "$", t, flags=re.S)
    t = re.sub(r"\{\\\\\$", r"{\\$", t)
    return re.sub(r"\$\\\\\$", r"$\\$", t)  # "$\\$8{,}200$" (a line break) was meant as "$\$8{,}200$"


def math_spans(t: str) -> list[tuple[int, int]]:
    """(start, end) of each $...$ (end exclusive), by pairing unescaped $ from the left."""
    pos = [m.start() for m in re.finditer(r"(?<!\\)\$", t)]
    if len(pos) % 2:
        raise Fail("odd number of $")
    return [(pos[k], pos[k + 1] + 1) for k in range(0, len(pos), 2)]


def units(s: str) -> list[tuple[str, str]]:
    """Split text into (kind, text): kinds math, seed (a LaTeX command or ^ _ that makes a run math), word, sp,
    stop (sentence punctuation, text commands, escaped characters), comma."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            m = re.match(r"\\([a-zA-Z]+)\*?", s[i:])
            if m:
                name = m.group(1)
                if name in ("left",) or name == "begin":
                    j = group_end(s, i, name)
                    out.append(("seed", s[i:j]))
                    i = j
                    continue
                if name in TEXTCMDS:
                    j = i + m.end()
                    if j < len(s) and s[j] == "{":
                        j = brace_end(s, j)
                    out.append(("stop", s[i:j]))
                    i = j
                    continue
                kind = "math" if name in SPACING else "seed"
                if name in ("text", "mbox", "mathrm"):
                    j = i + m.end()
                    if j < len(s) and s[j] == "{":
                        j = brace_end(s, j)
                    out.append(("math", s[i:j]))
                    i = j
                    continue
                out.append((kind, m.group(0)))
                i += m.end()
                continue
            nxt = s[i + 1:i + 2]
            out.append(("stop" if nxt in ("%", "$", "#", "&", "\\", "_", "{", "}", "") else "math", s[i:i + 2]))
            i += 2
            continue
        if c == "{":
            j = brace_end(s, i)
            out.append(("math", s[i:j]))
            i = j
        elif c in "^_":
            out.append(("seed", c))
            i += 1
        elif c.isspace():
            m = re.match(r"\s+", s[i:])
            out.append(("sp", m.group(0)))
            i += m.end()
        elif c.isdigit():
            m = re.match(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", s[i:])
            out.append(("math", m.group(0)))
            i += m.end()
        elif c.isalpha():
            m = re.match(r"[A-Za-z]+", s[i:])
            w = m.group(0)
            mathy = len(w) == 1 or w in FUNCS or re.fullmatch(r"[xyz]{2,3}|d[xyztuvrs]", w)  # yx, dx, dt, ...
            out.append(("math" if mathy else "word", w))
            i += m.end()
        elif c in "=+-*/()[]<>|'":
            out.append(("math", c))
            i += 1
        elif c == ",":
            out.append(("comma", c))
            i += 1
        else:
            out.append(("stop", c))
            i += 1
    return out


def brace_end(s: str, i: int) -> int:
    depth = 0
    j = i
    while j < len(s):
        if s[j] == "\\":
            j += 2
            continue
        depth += {"{": 1, "}": -1}.get(s[j], 0)
        j += 1
        if depth == 0:
            return j
    raise Fail("unbalanced braces in bare math")


def group_end(s: str, i: int, name: str) -> int:
    if name == "begin":
        m = re.match(r"\\begin\{([^}]*)\}", s[i:])
        if not m:
            raise Fail("bare \\begin")
        end = s.find("\\end{" + m.group(1) + "}", i)
        if end < 0:
            raise Fail("bare \\begin without \\end")
        return end + len("\\end{" + m.group(1) + "}")
    depth, j = 0, i
    while j < len(s):
        if s.startswith("\\left", j):
            depth += 1
            j += 5
        elif s.startswith("\\right", j):
            depth -= 1
            j += 6
            if depth == 0:
                if j < len(s) and s[j] == "\\" and re.match(r"\\[a-zA-Z]+", s[j:]):
                    return j + re.match(r"\\[a-zA-Z]+", s[j:]).end()
                return j + (2 if s[j:j + 1] == "\\" else 1)
        else:
            j += 1
    raise Fail("bare \\left without \\right")


def balanced(t: str) -> bool:
    depth = {"(": 0, "[": 0}
    for ch in re.sub(r"\\[()\[\]]|\\left.|\\right.|\{[^{}]*\}", "", t):
        if ch in "([":
            depth[ch] += 1
        elif ch in ")]":
            depth["(" if ch == ")" else "["] -= 1
            if min(depth.values()) < 0:
                return False
    return not any(depth.values())


def wrap_bare(seg: str) -> str:
    """Wrap the LaTeX the translation left outside $ $ (a run of math units with a command or ^ _ in it)."""
    us = units(seg)
    out, k = [], 0
    while k < len(us):
        kind, text = us[k]
        if kind not in ("math", "seed", "comma", "sp"):
            out.append(text)
            k += 1
            continue
        j, depth = k, 0
        while j < len(us):
            kd, tx = us[j]
            if kd in ("math", "seed", "sp"):
                depth += tx.count("(") + tx.count("[") - tx.count(")") - tx.count("]") if len(tx) == 1 else 0
                j += 1
            elif kd == "comma" and depth > 0:
                j += 1
            else:
                break
        if j == k:
            out.append(text)
            k += 1
            continue
        run = us[k:j]
        while run and (run[-1][0] == "sp" or run[-1][1] in "=+-*/<>|,'(["):
            if run[-1][1] in "=+-*/<>|" and run[-1][0] != "sp" and len(run) > 1 and run[-1][1] in "=":
                break  # a trailing = is part of the equation
            j -= 1
            run = run[:-1]
        while run and run[0][0] == "sp":
            run = run[1:]
        while run and run[0][1] in ")]":
            run = run[1:]
        if j <= k:
            out.append(us[k][1])
            k += 1
            continue
        txt = "".join(tx for _, tx in run)
        weak = re.fullmatch(r"[^=]*[A-Za-z][^=]*=[^=]*[A-Za-z0-9][^=]*", txt) is not None and re.search(r"[A-Za-z]", txt)
        if not (any(kd == "seed" for kd, _ in run) or weak):
            out.extend(tx for _, tx in us[k:j])
            k = j
            continue
        txt = re.sub(r"(?<=\d),(?=\d{3})", "{,}", txt)
        if not balanced(txt):
            raise Fail("bare math with unbalanced parentheses")
        lead = "".join(tx for _, tx in us[k:j]).split(txt.replace("{,}", ","), 1)[0]
        out.append(lead + "$" + txt + "$")
        k = j
    return "".join(out)


def clean_outside(seg: str) -> str:
    seg = wrap_bare(seg)
    # characters that are special in LaTeX text mode
    parts = re.split(r"(\$[^$]*\$)", seg)
    return "".join(p if p.startswith("$") and p.endswith("$") and len(p) > 1 else re.sub(r"(?<!\\)([%&#])", r"\\\1", p)
                   for p in parts)


def dedupe_sentences(t: str) -> str:
    """The translation repeats some sentences ("(If ...) (If ...)"); keep the first."""
    for m in sorted(set(re.findall(r"\([^()]{25,}\)", t)), key=len, reverse=True):
        while t.count(m) > 1:
            k = t.rfind(m)
            t = t[:k] + t[k + len(m):]
    seen = set()

    def once(m: re.Match) -> str:
        key = m.group(0).strip()
        if len(key) > 30 and key in seen:
            return ""
        seen.add(key)
        return m.group(0)
    return SENTENCE_RE.sub(once, t)


def prose_in_math(t: str) -> bool:
    """A $ ... $ span that holds English words: its $ were paired wrongly."""
    for a, b in math_spans(t):
        body = re.sub(r"\\(?:text|mbox|textrm|mathrm|textbf)\{[^{}]*\}|\\[a-zA-Z]+", " ", t[a + 1:b - 1])
        words = [w for w in re.findall(r"[A-Za-z]{3,}", body) if w not in FUNCS]
        if len(words) >= 2 and re.search(r"[A-Za-z]{3,}\s+[A-Za-z]{3,}", body):
            return True
    return False


def convert_text(t: str) -> str:
    """The statement, with [ANS] still in it."""
    t = re.sub(r"<answer[^>]*>", "", t)
    for a, b in UNICODE.items():
        t = t.replace(a, b)
    if re.search(r"[^\x00-\x7f]", t):
        raise Fail("non-ASCII character")
    t = HINT_RE.sub(" ", t)
    t = re.sub(r"\bSolution:\s*", "", t)  # a few problems carry the lead-in of their own worked solution
    t = to_dollars(t)
    # "$[ANS]" is a dollar sign before the blank, not an opening $
    if len(re.findall(r"(?<!\\)\$", t)) % 2 == 1 and re.search(r"(?<!\\)\$\s*\[ANS\]", t):
        t = re.sub(r"(?<!\\)\$(\s*\[ANS\])", r"\\$\1", t, count=1)
    t = dedupe_sentences(t)
    spans = math_spans(t)
    # [ANS] inside a $ $ span stays; elsewhere the text between spans is cleaned
    out, last = [], 0
    for a, b in spans + [(len(t), len(t))]:
        out.append(clean_outside(t[last:a]))
        out.append(t[a:b])
        last = b
    t = "".join(out)
    if prose_in_math(t):
        raise Fail("English words inside $ $ (mispaired dollar signs)")
    return t


def tidy(t: str) -> str:
    t = re.sub(r"[ \t]*\n[ \t]*", " ", t)
    t = re.sub(r" {2,}", " ", t)
    t = re.sub(r"\(\s+", "(", t)
    return t.strip()


MC_WORD_SUFFIX = re.compile(r"(?i)\s*(?:answer\(s\)|answers?|choose one|select one)\s*[:=]?\s*$")


def split_options(rest: str, letters: list[str]) -> tuple[str, list[str]]:
    """The text after [ANS] -> (leading text, option texts) by the markers "A." "B\\." in order."""
    pos, k = [], 0
    for L in letters:
        m = re.compile(r"(?:^|(?<=\s))" + L + r"\s*\\?\.\s").search(rest, k)
        if not m:
            raise Fail("options not found in the text")
        pos.append((m.start(), m.end()))
        k = m.end()
    lead = rest[:pos[0][0]]
    opts = [rest[pos[i][1]:(pos[i + 1][0] if i + 1 < len(pos) else len(rest))].strip() for i in range(len(pos))]
    if any(not o for o in opts):
        raise Fail("empty option")
    return lead, opts


def build_question(r: dict) -> tuple[str, list[str] | None]:
    """Statement text; for multiple choice also the option letters."""
    typ = r["answer_type_v1"][0]
    t = r["problem_v1"]
    if "[ANS]" not in t:
        raise Fail("no [ANS]")
    if typ in ("MCS", "MCM"):
        opts = r["options_v1"][0]
        if len(opts) < 2:
            raise Fail("no options")
        t = convert_text(t)
        head, rest = t.split("[ANS]", 1)
        letters = [o for o in opts]
        if all(re.fullmatch(r"[A-Z]", o) for o in letters):
            lead, texts = split_options(rest, letters)
            texts = [tidy(o) for o in texts]
            stem = tidy(head + lead)
            stem = MC_WORD_SUFFIX.sub("", stem)
            stem = re.sub(r"\s+(?:[.:])$", lambda m: m.group(0).strip(), stem)
            names = letters
        else:  # the options are words: "The system is [ANS]." with options independent, dependent, ...
            names = [chr(65 + k) for k in range(len(opts))]
            texts = [o.strip() for o in opts]
            stem = tidy(head + BLANK + rest)
        outside = re.sub(r"\$[^$]*\$", " ", texts[-1])
        if len(re.findall(r"[A-Za-z]{3,}", outside)) >= 4 and len(texts) > 1 and len(outside) > 40:
            raise Fail("text after the last option")
        if re.search(r"(?<!\\)\\\\", stem + "".join(texts)):
            raise Fail("line break in a multiple-choice problem")
        body = stem + "\n\n" + "\n\n".join(f"({n}) {o}" for n, o in zip(names, texts, strict=False))
        many = typ == "MCM"
        if many and not re.search(r"(?i)one or more|more than one|select (all|every)|check (all|every|the box)|all that apply", stem):
            body += "\n\nOne or more options may be correct."
        if not many and not re.search(r"(?i)exactly one|only one|all that apply|check all|select all|more than one", stem):
            body += "\n\nExactly one option is correct."
        return body, names
    t = convert_text(t)
    t = t.replace("[ANS]", BLANK)
    return tidy(t), None


# --- the answer -----------------------------------------------------------------------------------------

GREEK = {"alpha", "beta", "gamma", "delta", "epsilon", "theta", "lambda", "mu", "nu", "pi", "rho", "sigma", "tau",
         "phi", "omega", "eta", "zeta", "xi", "kappa", "chi", "psi"}
TRIG = {"sin", "cos", "tan", "sec", "csc", "cot", "sinh", "cosh", "tanh", "sech", "csch", "coth",
        "arcsin", "arccos", "arctan", "arcsec", "arccsc", "arccot"}
ALIAS = {"asin": "arcsin", "acos": "arccos", "atan": "arctan", "asec": "arcsec", "acsc": "arccsc", "acot": "arccot",
         "ln": "ln", "log": "log", "log10": "log10", "sqrt": "sqrt", "exp": "exp", "abs": "abs", "root": "root"}
TOKEN_RE = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|\\?([A-Za-z]+\d*)|(\*\*|[-+*/^()\[\]{},=|!]))")


def tokenize(s: str) -> list[tuple[str, str]]:
    toks, i = [], 0
    s = s.strip()
    while i < len(s):
        m = TOKEN_RE.match(s, i)
        if not m:
            raise Fail(f"answer: cannot read {s[i:i + 10]!r}")
        i = m.end()
        if m.group(1):
            toks.append(("num", m.group(1)))
        elif m.group(2):
            toks.append(("id", m.group(2)))
        else:
            toks.append(("op", "^" if m.group(3) == "**" else m.group(3)))
    return toks


class Parser:
    def __init__(self, toks, log_style: str):
        self.t, self.i, self.log = toks, 0, log_style

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def eat(self, val=None):
        tok = self.peek()
        if tok[0] is None or (val is not None and tok[1] != val):
            raise Fail("answer: syntax")
        self.i += 1
        return tok

    def done(self):
        return self.i >= len(self.t)

    # grammar
    def expr(self):
        terms = []
        sign = 1
        while True:
            if self.peek() == ("op", "-"):
                self.eat()
                sign = -1
            elif self.peek() == ("op", "+"):
                self.eat()
            node = self.term()
            terms.append((sign, node))
            sign = 1
            if self.peek() in (("op", "+"), ("op", "-")):
                sign = 1 if self.peek()[1] == "+" else -1
                self.eat()
                continue
            return terms[0][1] if len(terms) == 1 and terms[0][0] == 1 else ("add", terms)

    def term(self):
        items = [(" ", self.factor())]
        while True:
            tok = self.peek()
            if tok == ("op", "*") or tok == ("op", "/"):
                self.eat()
                items.append((tok[1], self.factor()))
            elif tok[0] in ("num", "id") or tok == ("op", "("):
                items.append((" ", self.factor()))
            else:
                return items[0][1] if len(items) == 1 else ("mul", items)

    def factor(self):
        if self.peek() == ("op", "-"):
            self.eat()
            return ("neg", self.factor())
        if self.peek() == ("op", "+"):
            self.eat()
            return self.factor()
        base = self.atom()
        while self.peek() == ("op", "!"):
            self.eat()
            base = ("fact", base)
        if self.peek() == ("op", "^"):
            self.eat()
            if self.peek() == ("op", "-"):
                self.eat()
                ex = ("neg", self.power_operand())
            else:
                ex = self.power_operand()
            return ("pow", base, ex)
        return base

    def power_operand(self):
        base = self.atom()
        if self.peek() == ("op", "^"):
            self.eat()
            if self.peek() == ("op", "-"):
                self.eat()
                return ("pow", base, ("neg", self.power_operand()))
            return ("pow", base, self.power_operand())
        return base

    def atom(self):
        kind, val = self.peek()
        if kind == "num":
            self.eat()
            return ("num", val)
        if kind == "id":
            self.eat()
            name = val.lower() if val.lower() in ALIAS or val.lower() in TRIG or val.lower() in GREEK else val
            if name == "frac":
                self.eat("{")
                a = self.expr()
                self.eat("}")
                self.eat("{")
                b = self.expr()
                self.eat("}")
                return ("frac2", a, b)
            if name in ALIAS or name in TRIG:
                name = ALIAS.get(name, name)
                power = None
                if self.peek() == ("op", "^") and name in TRIG:
                    self.eat()
                    power = self.atom()
                if self.peek() in (("op", "("), ("op", "{")):
                    close = ")" if self.eat()[1] == "(" else "}"
                    args = [self.expr()]
                    while self.peek() == ("op", ","):
                        self.eat()
                        args.append(self.expr())
                    self.eat(close)
                elif name in TRIG and self.peek()[0] in ("id", "num"):
                    args = [self.atom()]  # "cos x"
                else:
                    raise Fail(f"answer: function {name} without (")
                node = ("fn", name, args)
                return ("fnpow", node, power) if power else node
            if name in GREEK or name in ("infinity", "e", "i", "inf", "dx", "dy", "dz", "dt"):
                return ("id", name)
            if re.fullmatch(r"[A-Za-z]", val):
                return ("id", val)
            m = re.fullmatch(r"([A-Za-z])(\d+)", val)
            if m:
                return ("sub", m.group(1), m.group(2))
            raise Fail(f"answer: unknown name {val!r}")
        if (kind, val) in (("op", "("), ("op", "["), ("op", "{")):
            self.eat()
            items = [self.expr()]
            while self.peek() == ("op", ","):
                self.eat()
                items.append(self.expr())
            close = {"(": ")", "[": "]", "{": "}"}[val]
            self.eat(close)
            return ("grp", val, items)
        if (kind, val) == ("op", "|"):
            self.eat()
            inner = self.expr()
            self.eat("|")
            return ("fn", "abs", [inner])
        raise Fail("answer: syntax")


def pr_paren(s: str) -> str:
    return rf"\left({s}\right)" if r"\frac" in s else f"({s})"


def pr(n, top: bool = True, log_name: str = r"\ln") -> str:
    k = n[0]
    if k == "num":
        return sci(n[1]) if re.search(r"[eE]", n[1]) else n[1]
    if k == "id":
        return {"infinity": r"\infty", "inf": r"\infty"}.get(n[1], f"\\{n[1]}" if n[1] in GREEK else n[1])
    if k == "sub":
        return f"{n[1]}_{{{n[2]}}}"
    if k == "neg":
        inner = pr(n[1], False, log_name)
        return "-" + (pr_paren(inner) if n[1][0] == "add" else inner)
    if k == "grp":
        items = [pr(x, True, log_name) for x in n[2]]
        left, right = ("[", "]") if n[1] == "[" else ("(", ")")
        if len(items) == 1 and n[1] != "[":
            return pr_paren(items[0])
        return left + ", ".join(items) + right
    if k == "frac2":
        return rf"\frac{{{pr(n[1], True, log_name)}}}{{{pr(n[2], True, log_name)}}}"
    if k == "fact":
        b = pr(n[1], False, log_name)
        return (b if n[1][0] in ("num", "id") else pr_paren(b)) + "!"
    if k == "fnpow":
        inner = pr(n[1], True, log_name)
        return re.sub(r"^(\\[a-z]+)", lambda m: m.group(1) + "^{" + pr(n[2], True, log_name) + "}", inner, count=1)
    if k == "fn":
        name, args = n[1], [pr(a, True, log_name) for a in n[2]]
        if name == "sqrt":
            return rf"\sqrt{{{args[0]}}}"
        if name == "root":
            if len(args) != 2:
                raise Fail("answer: root")
            return rf"\sqrt[{args[0]}]{{{args[1]}}}"
        if name == "exp":
            return f"e^{{{args[0]}}}"
        if name == "abs":
            return rf"\left|{args[0]}\right|"
        if name == "ln":
            return rf"\ln{pr_paren(args[0])}"
        if name == "log":
            return rf"{log_name}{pr_paren(args[0])}"
        if name == "log10":
            return rf"\log_{{10}}{pr_paren(args[0])}"
        if len(args) != 1:
            raise Fail("answer: arguments")
        return rf"\{name}{pr_paren(args[0])}"
    if k == "pow":
        b = pr(n[1], False, log_name)
        if n[1][0] in ("add", "mul", "neg", "pow", "frac2", "fact") or (n[1][0] == "num" and n[1][1].startswith("-")):
            b = pr_paren(b)
        e = n[2]
        es = pr(e[2][0], True, log_name) if e[0] == "grp" and e[1] in "({" and len(e[2]) == 1 else pr(e, True, log_name)
        return f"{b}^{{{es}}}"
    if k == "add":
        s = ""
        for sign, term in n[1]:
            body = pr(term[1], False, log_name) if term[0] == "neg" else pr(term, False, log_name)
            neg = term[0] == "neg"
            if term[0] == "neg":
                sign = -sign
            if not s:
                s = ("-" if sign < 0 else "") + body
            else:
                s += (" - " if sign < 0 else " + ") + body
            del neg
        return s
    if k == "mul":
        items = n[1]
        acc, acc_node = pr_factor(items[0][1], log_name), items[0][1]
        for op, f in items[1:]:
            fs = pr_factor(f, log_name)
            if op == "/":
                num = strip_grp(acc_node, acc, log_name)
                den = strip_grp(f, fs, log_name)
                acc, acc_node = rf"\frac{{{num}}}{{{den}}}", ("frac",)
            else:
                cdot = (f[0] == "num" or (f[0] == "pow" and f[1][0] == "num")
                        or fs.startswith(r"\frac") or (acc_node[0] == "frac" and f[0] == "num"))
                if op == "*" and acc_node[0] == "num" and f[0] == "num":
                    cdot = True
                acc = acc + (r" \cdot " if cdot else " ") + fs
                acc_node = ("prod",)
        return acc
    raise Fail("answer: internal")


def pr_factor(f, log_name: str) -> str:
    s = pr(f, False, log_name)
    if f[0] in ("add", "neg"):
        return pr_paren(s)
    return s


def strip_grp(node, printed: str, log_name: str) -> str:
    if node[0] == "grp" and len(node[2]) == 1:
        return pr(node[2][0], True, log_name)
    return printed


# --- numeric keys: constant parts evaluated, long decimals rounded ----------------------------------------------

STATS: collections.Counter = collections.Counter()  # rows changed per rule: E notation, constant parts, long decimals
_ROW: set[str] = set()  # the rules that fired for the row being converted
SIG = 6  # significant figures kept for decimals
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
PLACES_RE = re.compile(r"(?i)\b(\d+|" + "|".join(WORDS) + r")\s+(?:decimal\s+)?places?\b")
ASKS_DECIMAL_RE = re.compile(r"(?i)decimal|\bround|nearest|significant|accura|places")
SCI_ASK_RE = re.compile(r"(?i)scientific notation|standard form|power of")
FUNCS_1 = {"sqrt": math.sqrt, "exp": math.exp, "ln": math.log, "log": math.log, "log10": math.log10, "abs": abs,
           "sin": math.sin, "cos": math.cos, "tan": math.tan, "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
           "arcsin": math.asin, "arccos": math.acos, "arctan": math.atan,
           "sec": lambda x: 1 / math.cos(x), "csc": lambda x: 1 / math.sin(x), "cot": lambda x: 1 / math.tan(x)}


def places_asked(q: str) -> int:
    """The most decimal places the statement asks for (0 when it names none)."""
    return max((int(WORDS.get(m.group(1).lower(), m.group(1))) for m in PLACES_RE.finditer(q)), default=0)


def to_decimal(x: Fraction | float) -> Decimal:
    with localcontext() as c:
        c.prec = 60
        if isinstance(x, Fraction):
            return Decimal(x.numerator) / Decimal(x.denominator)
        return Decimal(repr(float(x)))


def fmt(d: Decimal, asked: int = 0) -> str:
    """d to SIG significant figures, no trailing zeros; more places only when the statement asks for them.
    Very small or large values come out as `a \\times 10^{b}` (LaTeX: the caller wraps the key in $)."""
    if d == 0:
        return "0"
    with localcontext() as c:
        c.prec = SIG
        c.rounding = ROUND_HALF_EVEN
        r = +d
    adj = r.adjusted()
    if adj < -4 or adj >= 12:
        return rf"{format(r.scaleb(-adj).normalize(), 'f')} \times 10^{{{adj}}}"
    s = format(r, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if asked > (len(s.split(".")[1]) if "." in s else 0):
        with localcontext() as c:
            c.prec = 60
            s = format(d.quantize(Decimal(1).scaleb(-asked)), "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
    return s


def sci(s: str) -> str:
    """WeBWorK E notation, 6.673E-11, as 6.673 \\times 10^{-11}."""
    m = re.fullmatch(r"(.*?)[eE]([+-]?\d+)", s)
    return rf"{m.group(1)} \times 10^{{{int(m.group(2))}}}"


def has_num(n, pattern: str) -> bool:
    """Does the parse tree hold a number whose text matches pattern (E notation: [eE]; a decimal: [.eE])?"""
    if isinstance(n, tuple):
        return bool(re.search(pattern, n[1])) if n[0] == "num" else any(has_num(x, pattern) for x in n[1:])
    return isinstance(n, list) and any(has_num(x, pattern) for x in n)


def exact(n) -> tuple[Fraction, bool] | None:
    """The exact value of a variable-free tree built from numbers and + - * / and integer powers: (value, a
    decimal or E-notation leaf was in it); None for anything else."""
    k = n[0]
    if k == "num":
        s = n[1]
        return (Fraction(int(s)), False) if s.isdigit() else (Fraction(Decimal(s)), True)
    if k == "neg":
        v = exact(n[1])
        return (-v[0], v[1]) if v else None
    if k == "grp":
        return exact(n[2][0]) if len(n[2]) == 1 else None
    if k == "frac2":
        a, b = exact(n[1]), exact(n[2])
        return (a[0] / b[0], a[1] or b[1]) if a and b and b[0] != 0 else None
    if k == "fact":
        v = exact(n[1])
        if v and not v[1] and v[0].denominator == 1 and 0 <= v[0] <= 100:
            return Fraction(math.factorial(int(v[0]))), False
        return None
    if k == "add":
        total, dec = Fraction(0), False
        for sign, t in n[1]:
            v = exact(t)
            if v is None:
                return None
            total += sign * v[0]
            dec = dec or v[1]
        return total, dec
    if k == "mul":
        v = exact(n[1][0][1])
        for op, f in n[1][1:]:
            w = exact(f)
            if v is None or w is None or (op == "/" and w[0] == 0):
                return None
            v = (v[0] / w[0] if op == "/" else v[0] * w[0], v[1] or w[1])
        return v
    if k == "pow":
        b, e = exact(n[1]), exact(n[2])
        if b and e and not e[1] and e[0].denominator == 1 and abs(e[0]) <= 200 and not (b[0] == 0 and e[0] < 0):
            r = b[0] ** int(e[0])
            return (r, b[1]) if len(str(abs(r.numerator))) < 80 and len(str(r.denominator)) < 80 else None
    return None


def _num(n) -> float:
    k = n[0]
    if k == "num":
        return float(n[1])
    if k == "id" and n[1] in ("pi", "e"):
        return math.pi if n[1] == "pi" else math.e
    if k == "neg":
        return -_num(n[1])
    if k == "grp" and len(n[2]) == 1:
        return _num(n[2][0])
    if k == "frac2":
        return _num(n[1]) / _num(n[2])
    if k == "fact":
        return float(math.factorial(int(_num(n[1]))))
    if k == "add":
        return sum(sign * _num(t) for sign, t in n[1])
    if k == "mul":
        v = _num(n[1][0][1])
        for op, f in n[1][1:]:
            v = v / _num(f) if op == "/" else v * _num(f)
        return v
    if k == "pow":
        v = _num(n[1]) ** _num(n[2])
        if isinstance(v, complex):
            raise ValueError(k)
        return v
    if k == "fn" and n[1] in FUNCS_1 and len(n[2]) == 1:
        return FUNCS_1[n[1]](_num(n[2][0]))
    if k == "fn" and n[1] == "root" and len(n[2]) == 2:
        return _num(n[2][1]) ** (1 / _num(n[2][0]))
    if k == "fnpow" and n[1][0] == "fn" and n[1][1] in FUNCS_1:
        return FUNCS_1[n[1][1]](_num(n[1][2][0])) ** _num(n[2])
    raise ValueError(k)


def numeric(n) -> float | None:
    """The float value of a variable-free tree (roots, pi, e, logs, trig allowed); None if it has variables."""
    try:
        return _num(n)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None


def fixed(m: Fraction) -> str:
    """An integer, or p/q in lowest terms with the sign in front."""
    sign, m = ("-" if m < 0 else ""), abs(m)
    return sign + (str(m.numerator) if m.denominator == 1 else rf"\frac{{{m.numerator}}}{{{m.denominator}}}")


def render_part(n, q: str, log_name: str = r"\ln") -> str:
    """One comma-separated part of a key: a constant part is evaluated (exact rationals as an integer or a lowest-
    terms fraction, anything with a decimal at SIG figures; roots, pi, logs and trig stay exact unless the
    statement asks for a decimal, or the part has a decimal or E-notation leaf, so is approximate anyway), a long
    decimal rounded; a part with variables is printed as parsed."""
    text = pr(n, True, log_name)
    leaf = n[0] == "num" or (n[0] == "neg" and n[1][0] == "num")
    out = text
    tag = None
    ex = exact(n)
    if has_num(n, "[eE]"):
        _ROW.add("E notation")
    if SCI_ASK_RE.search(q):  # the statement asks for a form (scientific notation): the key keeps the one parsed
        return text
    if ex is not None:
        val, dec = ex
        if not dec:
            out, tag = fixed(val), "constant part"
        elif leaf:
            lit = n[1] if n[0] == "num" else n[1][1]
            digits = re.sub(r"[-.]", "", re.sub(r"[eE].*", "", lit)).lstrip("0")  # the mantissa's figures
            if len(digits) > SIG:
                out, tag = fmt(to_decimal(val), places_asked(q)), "long decimal"
                mant, _, exp = lit.lower().partition("e")
                if exp and "times" not in fmt(Decimal(mant)):  # a long E-notation leaf keeps its E form
                    out = ("-" if n[0] == "neg" else "") + sci(f"{fmt(Decimal(mant))}E{exp}")
        else:
            out, tag = fmt(to_decimal(val), places_asked(q)), "constant part"
    elif (ASKS_DECIMAL_RE.search(q) or has_num(n, "[.eE]")) and (fv := numeric(n)) is not None:
        out, tag = fmt(to_decimal(fv), places_asked(q)), "constant part"
    if tag and out.replace(" ", "") != text.replace(" ", ""):
        _ROW.add(tag)
    return out


def round_plain(a: str, q: str) -> str:
    """A plain decimal key rounded to SIG figures when it is longer (more places only when the statement asks)."""
    digits = re.sub(r"[-.]", "", a).lstrip("0")
    if "." not in a or len(digits) <= SIG:
        return a
    out = fmt(Decimal(a), places_asked(q))
    if out != a:
        _ROW.add("long decimal")
    return f"${out}$" if "\\" in out else out


def convert_expr(s: str, log_name: str, q: str = "") -> str:
    toks = tokenize(s)
    if not toks:
        raise Fail("answer: empty")
    # relations: split on top-level =
    depth, cuts = 0, []
    for k, (kd, v) in enumerate(toks):
        if kd == "op":
            depth += (v in "([") - (v in ")]")
            if v == "=" and depth == 0:
                cuts.append(k)
    sides, prev = [], 0
    for c in cuts + [len(toks)]:
        p = Parser(toks[prev:c], log_name)
        node = p.expr()
        if not p.done():
            raise Fail("answer: syntax")
        sides.append(node)
        prev = c + 1
    if len(sides) == 1:
        node = sides[0]
        if node[0] == "grp" and len(node[2]) > 1:  # a tuple: each part is a key of its own
            left, right = ("[", "]") if node[1] == "[" else ("(", ")")
            return left + ", ".join(render_part(x, q, log_name) for x in node[2]) + right
        return render_part(node, q, log_name)
    return " = ".join(pr(x, True, log_name) for x in sides)


def convert_interval(s: str, q: str, log_name: str) -> str:
    toks = tokenize(s)
    pieces, k = [], 0
    while k < len(toks):
        kd, v = toks[k]
        if (kd, v) not in (("op", "("), ("op", "[")):
            raise Fail("answer: interval")
        depth, j = 0, k
        while j < len(toks):
            if toks[j][0] == "op":
                depth += (toks[j][1] in "([") - (toks[j][1] in ")]")
            j += 1
            if depth == 0:
                break
        sub = toks[k:j]
        inner = sub[1:-1]
        cut = next((m for m, x in enumerate(inner) if x == ("op", ",")), None)
        if cut is None or sub[-1][1] not in ")]":
            raise Fail("answer: interval")
        parts = []
        for part in (inner[:cut], inner[cut + 1:]):
            p = Parser(part, "")
            node = p.expr()
            if not p.done():
                raise Fail("answer: interval")
            parts.append(render_part(node, q, log_name))
        pieces.append(f"{v}{parts[0]}, {parts[1]}{sub[-1][1]}")
        k = j
        if k < len(toks):
            if toks[k] != ("id", "U"):
                raise Fail("answer: interval")
            k += 1
    return r" \cup ".join(pieces)


def convert_answer(r: dict, names: list[str] | None) -> str:
    a = str(r["answer_v1"][0]).strip()
    typ = r["answer_type_v1"][0]
    q = r["problem_v1"]
    log_name = r"\log" if (r"\log" in q and r"\ln" not in q) else r"\ln"
    if typ in ("MCS", "MCM"):
        assert names
        if all(re.fullmatch(r"[A-Z]", x) for x in r["options_v1"][0]):
            letters = re.findall(r"[A-Z]", a)
        else:
            try:
                letters = [names[[o.lower() for o in r["options_v1"][0]].index(a.lower())]]
            except ValueError:
                raise Fail("answer: not among the options") from None
        if (typ == "MCS" and len(letters) != 1) or not letters or any(x not in names for x in letters) \
                or len(set(letters)) != len(letters):
            raise Fail("answer: letters do not fit the options")
        return ", ".join(letters)
    if typ == "NV":
        if re.fullmatch(r"-?(\d+\.?\d*|\.\d+)", a):
            return round_plain(a.rstrip("."), q)
        m = re.fullmatch(r"(-?\d+\.?\d*)\s*%", a)
        if m:
            return rf"${m.group(1)}\%$"
        m = re.fullmatch(r"\$(\d+\.?\d*)", a)
        if m:
            return rf"$\${m.group(1)}$"
    if typ == "INT":
        return f"${convert_interval(a, q, log_name)}$"
    if typ == "UOL" or (typ == "OL" and re.search(r"(?i)comma|list", q) and not re.search(r"(?i)ordered pair|point|vector", q)):
        toks = tokenize(a)
        if toks and toks[0] == ("op", "(") and toks[-1] == ("op", ")"):
            items = Parser(toks, log_name).atom()
            parts = [render_part(x, q, log_name) for x in items[2]]
            text = ", ".join(parts)
            return text if all(re.fullmatch(r"-?\d+(\.\d+)?", p) for p in parts) else f"${text}$"
    out = convert_expr(a, log_name, q)
    return out if re.fullmatch(r"-?\d+(\.\d+)?", out) else f"${out}$"


# --- rows -----------------------------------------------------------------------------------------------

_FIX = json.loads(FIXES_PATH.read_text(encoding="utf-8")) if FIXES_PATH.exists() else {"fixes": [], "dropped": {}}
HAND_FIXES = {(e["key"], e["field"]): [tuple(p) for p in e["fixes"]] for e in _FIX["fixes"]}
DROPPED = dict(_FIX["dropped"])


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    """The rows to import and {label: reason} for each dataset row left out."""
    rows, dropped = [], {}
    raw = []
    for f in sorted(glob.glob(str(data / "data" / "*.json"))):
        raw += json.loads(Path(f).read_text(encoding="utf-8"))
    for d in raw:
        label = f"{SET} {d['id']}"
        why = skip_reason(d)
        if why:
            dropped[label] = why
            continue
        _ROW.clear()
        try:
            text, names = build_question(d)
            ans = convert_answer(d, names)
        except Fail as e:
            dropped[label] = str(e)
            continue
        tags = set(_ROW)
        row = {"potd": label, "set": SET, "idx": d["id"], "orig": "", "source": SET,
               "subsource": f"{d['subject'].replace('_', ' ')}, {d['topic']}, {d['id']}",
               "latexcode": text, "answer": ans, "solution": None, "hints": None, "more_hints": None,
               "ref_solution": "", "group": "math", "effort": EFFORT, "image": None}
        for fld in ("latexcode", "answer"):
            for old, new in HAND_FIXES.get((label, fld), []):
                if row[fld].count(old) != 1:
                    raise SystemExit(f"FIX {label} {fld}: expected one {old!r}")
                row[fld] = row[fld].replace(old, new)
        if label in DROPPED:
            dropped[label] = DROPPED[label]
            continue
        STATS.update(tags)
        rows.append(row)
    return rows, dropped


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True, help="the downloaded dataset folder (with data/*.json)")
    p.add_argument("--model", default=OPUS)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped = load(a.data)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why],
                                             ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    reasons = collections.Counter(re.sub(r"answer: (cannot read|unknown name|function).*", r"answer: \1", v)
                                  for v in dropped.values())
    print(json.dumps({"rows_to_add": len(new), "in_bank": len(dup), "check_problems": len(problems),
                      "key_rules_rows": dict(STATS), "dropped": len(dropped), "dropped_by_reason": reasons.most_common(),
                      "by_subject": collections.Counter(r["subsource"].split(",")[0] for r in new)}, default=dict))
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        (a.dump.with_name(a.dump.stem + "_dropped.json")).write_text(json.dumps(dropped, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("ugmathbench")
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in new:
            h = latex_hash(r["latexcode"])
            if h in existing:
                continue
            cur = conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, hints, more_hints, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"], r["answer"],
                 r["solution"], r["hints"], r["more_hints"], h),
            )
            existing.add(h)
            added.append((cur.lastrowid, r))
        conn.commit()
    finally:
        conn.close()
    with MAP_PATH.open("a" if MAP_PATH.exists() else "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    doc = json.loads(ASSIGNMENTS.read_text(encoding="utf-8")) if ASSIGNMENTS.exists() else {
        "note": "Benchmark sets imported with an answer key (no solutions), with the model and effort that solve them. "
                "Listing a question here puts it in run_sub.py's scope.", "questions": {}}
    doc["questions"].update({str(q): {"model": a.model, "effort": r["effort"]} for q, r in added if r["group"] == "math"})
    ASSIGNMENTS.write_text(json.dumps(doc, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    if solutions:
        SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; "
          f"map={MAP_PATH}; assignments={ASSIGNMENTS} ({len(doc['questions'])} questions)")


if __name__ == "__main__":
    main()
