"""Import TheoremQA (github.com/wenhuchen/TheoremQA, MIT): 800 university STEM questions with a short
final answer and no solution, for the subscription solver to solve and the judge to check against the
key (owner 2026-11-21: "Go ahead with all recommendations").

The caller downloads into one folder (nothing in it is executed):
  * test-00000-of-00001.parquet (HuggingFace TIGER-Lab/TheoremQA): Question, Answer, Answer_type, Picture;
  * theoremqa_test.json (the GitHub file): the same rows in the same order, plus id, field, subfield,
    theorem and a pointer to an explanation (a text file for 67 rows; those texts go in ref_solution
    when they sit in the folder's solutions/ directory).

What is left out: the rows whose subfield has no bank subject (signal processing, information theory,
networking, machine learning, numerical analysis, optics, condensed matter), the two problems the bank
already has (found by duplicates()), the two whose figure or table is missing, and rows listed in
DROPPED / theoremqa_fixes.json (text damaged in the dataset: a quantity or an angle that was never
there). Physics and Economics rows go to the subjects solver ("subject"); every other row is a "math"
row (the maths solver, Opus at high effort).

Text: the dataset writes much of its mathematics as plain text ("sin(3*t)", "x^5 + x - 1", 4x, 1/2,
unicode minus and degree signs); to_latex() wraps those runs in $ $ and rewrites them as LaTeX, escapes
currency, percent and ampersand, and makes the "(a) ... (b) ..." questions one option per line.
theoremqa_fixes.json carries the per-row repairs (pairs applied to the source question before the
conversion, each old matched exactly once; for the answer field, to the key after formatting).
Keys: integers as they are; floats as the decimal (a whole float without ".0"); True/False; lists as
"$[0, 5]$"; option letters in capitals. A physics value whose question names the unit ("(Unit: Hz)")
carries it. A picture is saved as PNG tqa-<sha1[:16]>.png (GIF and JPEG need Pillow; without it those
rows are set aside) and put after the text as \\includegraphics.

Usage (repo root):
  python -m app.tools.import_theoremqa --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_theoremqa --data DIR --apply
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import sqlite3
from decimal import Decimal
from pathlib import Path

from app.tools.import_answer_sets import GRAPHIC, TEXIMAGES, duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "TheoremQA"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
ASSIGNMENTS = Path("pipeline/benchmarks_assignments.json")
OPUS = "claude-opus-5-5"
SET_ASIDE_PATH = Path("app/data/appdata/theoremqa_set_aside.json")  # git-ignored

NO_SUBJECT = {"Signal processing", "Information theory", "Computer networking", "Machine learning", "Optics",
              "Condensed matter physics", "Numerical analysis"}
ALREADY_IN_BANK = {"mingyin/taylor-expansion1": "question 36057", "mingyin/series4": "question 38530"}
FIGURE_MISSING = {"xueguangma/state_tree": "its tree figure is not in the dataset",
                  "xueguangma/physics_current_and_resistance": "its figure or table is not in the dataset"}
SUBJECT_FIELDS = {"Physics"}
SUBJECT_SUBFIELDS = {"Economics"}  # Finance / Economics; the other Finance subfields are maths

_FIX = json.loads(Path(__file__).with_name("theoremqa_fixes.json").read_text(encoding="utf-8"))
FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIX["fixes"]:
    FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPPED = dict(_FIX["dropped"])  # id -> reason (without the .json)

# ---------------------------------------------------------------------------------------------- text

FUNCS = ("sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp", "arctan", "arcsin", "arccos", "lim",
         "det", "gcd", "max", "min", "sup", "inf", "dim", "rank")
FUNC_RE = re.compile(r"(?<![\\A-Za-z])(" + "|".join(FUNCS) + r")(?![A-Za-z])")
GREEK = "αβγδεθλμπρστφωΔΩ"
CALL_RE = re.compile(r"^(?:[A-Za-z]|" + "|".join(FUNCS) + r"|sqrt|Cov|dist|Var|Pr)'*\(")
UNICODE_MATH = {"−": "-", "∠": r"\angle ", "°": r"^{\circ}", "µ": r"\mu ", "μ": r"\mu ", "Ω": r"\Omega ",
                "σ": r"\sigma ", "τ": r"\tau ", "δ": r"\delta ", "≤": r"\le ", "≥": r"\ge ", "·": r"\cdot ",
                "→": r"\to ", "×": r"\times ", "∥": r"\parallel ", "△": r"\triangle ", "±": r"\pm ",
                "≠": r"\ne ", "π": r"\pi ", "¥": r"\yen ", "α": r"\alpha ", "β": r"\beta ", "γ": r"\gamma ",
                "ε": r"\epsilon ", "θ": r"\theta ", "λ": r"\lambda ", "ρ": r"\rho ", "φ": r"\phi ",
                "ω": r"\omega ", "Δ": r"\Delta ", "—": "---"}
OPS = {"=", "+", "-", "−", "*", "/", "<", ">", "<=", ">=", "≤", "≥", "~", "→", "·", "×", "±", "≠", "^", "\\le", "\\ge"}
UNITS = ("kg", "g", "N", "Pa", "J", "s", "Hz", "K", "cm", "km", "mm", "m", "eV", "MeV", "V", "W", "C", "Bq", "L", "atm")
UNIT_END_RE = re.compile(r"(?<=[\d}])\s*(" + "|".join(UNITS) + r")(\^\{?-?\d+\}?)?\s*$")

SENT = "\x00"
ERRORS: list[str] = []  # conversion problems (a stray $), reported with the text check


def clean_raw(t: str) -> str:
    """The TeX commands the dataset lost to control characters (\\f, \\t, \\r), CRLF, stray spaces."""
    t = t.replace("\r\n", "\n")
    t = re.sub(r"[\x0c\t\r\x08\x07\x0b](?=[A-Za-z])",
               lambda m: {"\x0c": "\\f", "\t": "\\t", "\r": "\\r", "\x08": "\\b", "\x07": "\\a", "\x0b": "\\v"}[m.group(0)], t)
    return t.strip()


def split_dollar(t: str) -> list[tuple[bool, str]]:
    """Text and $ $ math segments. A $ that is currency (a number, then words before the next $) is
    escaped. Raises ValueError for an odd number of math $."""
    marks, i = [], 0
    while i < len(t):
        c = t[i]
        if c == "\\":
            i += 2
            continue
        if c == "$":
            m = re.match(r"\$(\d[\d,]*(?:\.\d+)?)", t[i:])
            currency = False
            if m:
                rest = t[i + m.end():]
                if not re.match(r"[\^_\\{}=+*/<>(|\-%$]", rest):
                    nxt = rest.find("$")
                    between = rest if nxt < 0 else rest[:nxt]
                    words = re.findall(r"[A-Za-z]+", re.sub(r"\\[A-Za-z]+", "", between))
                    currency = (nxt < 0 or any(len(w) >= 4 for w in words) or sum(len(w) >= 3 for w in words) >= 2
                                or bool(re.match(r"[\s,.;)]*(?:(?:or|and|to|per|each)\b|$)|[\s,]*(?:or\s+)?\$\d", rest)))
            if currency:
                t = t[:i] + "\x01" + t[i + 1:]
            else:
                marks.append(i)
        i += 1
    if len(marks) % 2:
        raise ValueError("odd number of $")
    out, pos = [], 0
    for a, b in zip(marks[::2], marks[1::2], strict=True):
        out.append((False, t[pos:a]))
        out.append((True, t[a + 1:b]))
        pos = b + 1
    out.append((False, t[pos:]))
    return [(m, s.replace("\x01", "\\$")) for m, s in out if s != "" or m]


def _balanced_arg(s: str, i: int) -> int:
    """Index of the ")" closing the "(" at i, or -1."""
    depth = 0
    for k in range(i, len(s)):
        depth += {"(": 1, ")": -1}.get(s[k], 0)
        if depth == 0:
            return k
    return -1


def fix_math(s: str) -> str:
    """One math run (plain text or LaTeX) as LaTeX."""
    s = s.replace("\\athrm", "\\mathrm").replace("\\tims", "\\times").replace("\\infy", "\\infty")
    s = re.sub(r"\\le(?=[A-Z])", r"\\le ", s)
    s = re.sub(r"\bcost\(", r"\\cos(", s)
    s = re.sub(r"([\d}])\s*[μµ]([A-Za-z]+)", r"\1\\ \\mu\\mathrm{\2}", s)
    s = re.sub(r"(\d)\s*°\s*([CF])\b", r"\1^{\\circ}\\mathrm{\2}", s)
    s = re.sub(r"(\d)\s*[x×]\s*10\s*\^\s*\{?\s*(-?\d+)\s*\}?", r"\1 \\times 10^{\2}", s)
    s = s.replace("· · ·", r"\cdots ")
    for k, v in UNICODE_MATH.items():
        s = s.replace(k, v)
    s = s.replace("<=", r"\le ").replace(">=", r"\ge ").replace("!=", r"\ne ").replace("->", r"\to ")
    s = re.sub(r"(?<![\\{])~", r"\\sim ", s)
    s = FUNC_RE.sub(lambda m: "\\operatorname{rank}" if m.group(1) == "rank" else "\\" + m.group(1), s)
    s = re.sub(r"(?<![\\A-Za-z])pi(?![A-Za-z])", r"\\pi", s)
    s = re.sub(r"(?<![\\A-Za-z])infty", r"\\infty", s)
    # sqrt(...), \sqrt(...), \sqrt 2
    while (m := re.search(r"\\?sqrt\s*\(", s)):
        j = _balanced_arg(s, m.end() - 1)
        if j < 0:
            break
        s = s[:m.start()] + "\\sqrt{" + s[m.end():j] + "}" + s[j + 1:]
    s = re.sub(r"\\sqrt\s*(\d+|[A-Za-z])(?![\w{])", r"\\sqrt{\1}", s)
    s = re.sub(r"\^\(([^()]*)\)", r"^{\1}", s)
    s = re.sub(r"\^\s*(-?\d{2,})", r"^{\1}", s)
    s = re.sub(r"\^(-\d)", r"^{\1}", s)
    s = re.sub(r"_(\d{2,})", r"_{\1}", s)
    s = s.replace("||", r"\|")
    s = re.sub(r"(?<!\\)\\(?=\d)", r"\\\\ ", s)  # a lone backslash before a digit is a row break of an array
    if "\\begin{" in s:  # rows of an array or cases separated by one backslash and a space
        s = re.sub(r"(?<!\\)\\[ ]+(?=-?\d)", r"\\\\ ", s)
    s = s.replace("^*", "^{\\ast}")
    s = re.sub(r"(?<![\\\d])(\d+)\s*\*\s*(\d+)(?![\d.])", r"\1 \\times \2", s)
    s = re.sub(r"\b([mn])\s*\*\s*([mn])\b", r"\1 \\times \2", s)
    s = s.replace("*", r"\cdot ")
    s = re.sub(r"(?<!\\)%", r"\\%", s)
    s = re.sub(r"(\d)\s+(kg|cm|km|mm|m|s)(?=\s*\\times)", r"\1\\ \\mathrm{\2}", s)
    s = UNIT_END_RE.sub(lambda m: r"\ \mathrm{" + m.group(1) + (m.group(2) or "") + "}", s)
    return set_braces(re.sub(r"[ \t]{2,}", " ", s).strip())


def set_braces(s: str) -> str:
    """A { that does not follow a command, ^, _ or } is a set brace written plainly: \\{ ... \\}."""
    out, stack, i = [], [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append(s[i:i + 2])
            i += 2
            continue
        if c == "{":
            prev = "".join(out).rstrip()
            group = bool(re.search(r"(?:\^|_|\}|\{|\\[A-Za-z]+|\]|&|\\\\)$", prev))
            stack.append(group)
            out.append("{" if group else "\\{")
        elif c == "}":
            group = stack.pop() if stack else True
            out.append("}" if group else "\\}")
        else:
            out.append(c)
        i += 1
    return "".join(out)


def split_words(s: str) -> list[tuple[str, str]]:
    """(word, whitespace after it); whitespace inside {} or after a ^ or _ stays in the word."""
    out, cur, depth, i = [], "", 0, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            cur += s[i:i + 2]
            i += 2
            continue
        depth += {"{": 1, "}": -1}.get(c, 0)
        if c.isspace() and depth <= 0:
            j = i
            while j < len(s) and s[j].isspace():
                j += 1
            if cur:
                out.append((cur, s[i:j]))
                cur = ""
            elif out:
                out[-1] = (out[-1][0], out[-1][1] + s[i:j])
            i = j
            continue
        cur += c
        i += 1
    if cur:
        out.append((cur, ""))
    return out


STRONG_RES = [re.compile(p) for p in (
    r"[\^_=<>*]", r"\\[A-Za-z]", r"[≤≥∠±≠≈→×·∥△]", r"\|", r"\d/\d", r"\)/|/\(", r"\d/[A-Za-z]|[A-Za-z]/\d",
    r"^[a-z]-[a-z0-9]$", r"^[a-z]-\d+$", r"^[A-Za-z0-9)]\+[A-Za-z0-9(]", "[" + GREEK + "¥]",
    r"^(?:\d+(?:\.\d+)?[A-Za-z]?|[A-Za-z]\d*)(?:[+\-](?:\d+(?:\.\d+)?[A-Za-z]?|[A-Za-z]\d*))+$")]
PUNCT_END = re.compile(r"[.,;:?!][)\]}\"']*$")
WEAK_RE = re.compile(r"^(?:-?\d+(?:[.,]\d+)*|-?[A-Za-z]'*|-?\d+(?:\.\d+)?[A-Za-z]|[A-Z]{2,6}\d?|-?(?:" + "|".join(FUNCS) + r"))$")
ARTICLES = {"a", "A", "I"}


def _core(w: str) -> str:
    c = w
    while c and c[-1] in ".,;:?!":
        c = c[:-1]
    if re.match(r"^\(?(?:[A-Za-z]{1,3}|\d+)\)$", c):
        return "ENUM"
    # drop brackets that wrap the word from outside
    while c.startswith(("(", "[", "{", '"', "'")):
        c = c[1:]
    while c.endswith((")", "]", "}", '"')) and c.count(")") + c.count("]") + c.count("}") > c.count("(") + c.count("[") + c.count("{"):
        c = c[:-1]
    return c


def _strong(core: str) -> bool:
    if core == SENT or SENT in core:
        return True
    if core in OPS:
        return True
    if any(r.search(core) for r in STRONG_RES):
        return True
    return bool(CALL_RE.match(core) and ")" in core)


def _depth(s: str) -> int:
    return sum({"(": 1, ")": -1, "[": 1, "]": -1}.get(c, 0) for c in s)


def text_part(s: str, store: list[str]) -> str:
    """A text segment (no $): runs of plain-text mathematics wrapped in $ $; specials escaped."""
    lead, trail = s[:len(s) - len(s.lstrip())], s[len(s.rstrip()):]
    s = s.strip()
    # graph edges <a,b> and edge sets
    s = re.sub(r"E = \{((?:\s*<\w+,\s*\w+>\s*,?)+)\}", lambda m: _hold(store, "E = \\{" + re.sub(
        r"<(\w+),\s*(\w+)>", r"\\langle \1,\2\\rangle", m.group(1)) + "\\}"), s)
    s = re.sub(r"<(\w+),(\w+)>", lambda m: _hold(store, f"\\langle {m.group(1)},{m.group(2)}\\rangle"), s)
    # degrees with a unit, scientific notation, micro units
    s = re.sub(r"(-?\d+(?:\.\d+)?)\s*°\s*([CF])\b", lambda m: _hold(store, f"{m.group(1)}^{{\\circ}}\\mathrm{{{m.group(2)}}}"), s)
    s = re.sub(r"(°|∠\s*[A-Z]{3}|△\s*[A-Z]{3})", lambda m: _hold(store, m.group(1).replace(" ", "")), s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*[xX×]\s*10\s*\^\s*(\{[^}]*\}|-?\d+)",
               lambda m: _hold(store, f"{m.group(1)} \\times 10^{{{m.group(2).strip('{}')}}}"), s)
    s = re.sub(r"(\d)\s*([μµ][A-Za-z]+)", lambda m: _hold(store, f"{m.group(1)}\\ {m.group(2)}"), s)
    # tuples and lists of numbers: (0,0)  [1, 2]  (1, 2, 3, ...)
    s = re.sub(r"[(\[]-?[\w.]+(?:\s*,\s*-?(?:[\w.]+|\.\.\.))+[)\]]", lambda m: _hold(store, m.group(0)), s)
    words = split_words(s)
    cores = [_core(w) for w, _ in words]
    strong = [_strong(c) for c in cores]
    ops = [c in OPS for c in cores]
    n = len(words)
    inc = strong[:]
    for i in range(n):
        if inc[i] or not cores[i] or not WEAK_RE.match(cores[i].replace(",", ",")):
            continue
        # a weak word joins a strong neighbour when no punctuation separates them
        left = i > 0 and strong[i - 1] and not words[i - 1][0].rstrip(")]}").endswith((",", ";", ":", ".", "?", "!"))
        right = strong[i + 1] if i + 1 < n and not words[i][0].endswith((",", ";", ":", ".", "?", "!")) else False
        if cores[i] in ARTICLES:
            left, right = left and ops[i - 1], right and ops[i + 1]
        if left or right:
            inc[i] = True
    out, i = [], 0
    while i < n:
        if not inc[i]:
            out.append(_text_word(words[i][0], store) + words[i][1])
            i += 1
            continue
        j = i + 1  # the run is words i..j-1; it stops at punctuation (unless a bracket is open) or a word that is not mathematics
        buf = words[i][0]
        while j < n and inc[j] and (not PUNCT_END.search(words[j - 1][0]) or _depth(buf) > 0):
            buf += words[j - 1][1] + words[j][0]
            j += 1
        sep = words[j - 1][1]
        real = any(strong[k] and cores[k] not in OPS for k in range(i, j))
        if not real and (ops[i] or ops[j - 1] or j - i < 3):  # "= 62.4", "x =": an equals sign in the text
            out.append("".join(_text_word(words[k][0], store) + words[k][1] for k in range(i, j)))
            i = j
            continue
        run, tail = buf, ""
        while run and run[-1] in ".,;:?!":
            tail = run[-1] + tail
            run = run[:-1]
        while run.endswith(")") and _depth(run) < 0:
            tail = ")" + tail
            run = run[:-1]
        while run.startswith("(") and _depth(run) > 0:
            out.append("(")
            run = run[1:]
        out.append("$" + _resolve(fix_math(run), store) + "$" + tail + sep)
        i = j
    return lead + _resolve_text("".join(out), store) + trail


def _hold(store: list[str], math: str) -> str:
    store.append(math)
    return f"{SENT}{len(store) - 1}{SENT}"


def _resolve(m: str, store: list[str]) -> str:
    return re.sub(SENT + r"(\d+)" + SENT, lambda x: fix_math(store[int(x.group(1))]), m)


def _resolve_text(res: str, store: list[str]) -> str:
    return re.sub(SENT + r"(\d+)" + SENT, lambda x: "$" + fix_math(store[int(x.group(1))]) + "$", res)


def _text_word(w: str, store: list[str]) -> str:
    w = re.sub(r"(?<!\\)%", r"\\%", w)
    w = re.sub(r"(?<!\\)&", r"\\&", w)
    return w


OPTION_RE = re.compile(r"\(([a-e])\)\s+", re.I)


def options(t: str) -> tuple[str, list[str], str]:
    """An inline "(a) ... (b) ..." question as (stem, ["(A) ...", ...], the closing sentence)."""
    marks = list(OPTION_RE.finditer(t))
    if len(marks) < 2:
        return t, [], ""
    stem = t[:marks[0].start()].strip()
    opts = []
    for k, m in enumerate(marks):
        body = t[m.end(): marks[k + 1].start() if k + 1 < len(marks) else len(t)].strip()
        opts.append((m.group(1).upper(), body))
    last = opts[-1][1]
    ask = re.search(r"\s*(Which (?:one|option) is correct\?)\s*$", last)
    closing = "Exactly one option is correct."
    if ask:
        opts[-1] = (opts[-1][0], last[:ask.start()])
        closing = ask.group(1)
    return stem, [f"({L}) " + re.sub(r"[;,.]\s*$", "", b) for L, b in opts], closing


def to_latex(t: str, key: str) -> str:
    t = clean_raw(t)
    stem, opts, closing = options(t) if re.search(r"\(a\)", t) else (t, [], "")
    pieces = []
    for part in (stem, *opts, *([closing] if closing else [])):
        label = re.match(r"\([A-E]\) ", part) if opts and part in opts else None
        if label:
            part = part[label.end():]
        store: list[str] = []
        try:
            segs = split_dollar(part)
        except ValueError as e:  # a stray $ in the source: the row needs a fix
            ERRORS.append(f"{SET} {key} latexcode: {e}")
            segs = [(False, part.replace("$", "\\$"))]
        conv = []
        for m, s in segs:
            if m:
                bare = re.sub(r"\\(?:text|mathrm|mathbf|operatorname)\{[^{}]*\}|\\[A-Za-z]+", "", s)
                if re.search(r"\b[a-z]{3,}\s+[a-z]{3,}\s+[a-z]{3,}\b|[a-z]{6,}", bare):
                    ERRORS.append(f"{SET} {key} latexcode: words inside $ $ (a $ misplaced?): {s[:50]!r}")
                conv.append("$" + fix_math(s) + "$")
            else:
                conv.append(text_part(s, store))
        pieces.append((label.group(0) if label else "") + "".join(conv))
    out = "\n\n".join(pieces)
    return re.sub(r"[ \t]+\n", "\n", out)


def pipe_tables(t: str, conv) -> str:
    """Lines with " | " become a tabular (the first line of the block names the columns)."""
    lines, out, block = t.split("\n"), [], []

    def flush() -> None:
        if not block:
            return
        rows = [[conv(c.strip()) for c in r.strip().strip("|").split("|")] for r in block]
        width = max(len(r) for r in rows)
        body = " \\\\\n".join(" & ".join(r + [""] * (width - len(r))) for r in rows) + " \\\\"
        out.append("\\begin{center}\n\\begin{tabular}{" + "l" * width + "}\n" + body + "\n\\end{tabular}\n\\end{center}")
        block.clear()

    for ln in lines:
        if " | " in ln or ln.strip().endswith("|"):
            block.append(ln)
        else:
            flush()
            out.append(ln)
    flush()
    return "\n".join(out)


# --------------------------------------------------------------------------------------------- answers

def num(x: float) -> str:
    if float(x).is_integer() and abs(x) < 1e15:
        return str(int(x))
    x = float(f"{x:.12g}")
    if 0 < abs(x) < 1e-6:  # too many zeros as a decimal
        mant, exp = f"{x:e}".split("e")
        return f"{float(mant):g} \\times 10^{{{int(exp)}}}"
    return format(Decimal(repr(x)), "f")


UNIT_FIXES = {"m/s": r"m/s", "m / s": r"m/s", "m/s^2": r"m/s^2", "m/s^2)": r"m/s^2", "rad/s": r"rad/s"}


def unit_of(question: str) -> str | None:
    m = re.search(r"\(Unit:\s*([^()$]*?)\)", question)
    if not m:
        return None
    u = m.group(1).strip()
    if re.match(r"^10\b|\d", u) or not re.match(r"^[A-Za-z°/ ^_{}\-\d]+$", u):
        return None
    u = re.sub(r"\s*/\s*", "/", u).replace("°C", r"^{\circ}C").replace("°", "")
    u = re.sub(r"\^(-?\d+)", r"^{\1}", u)
    return u


def key_text(r: dict) -> str:
    a, typ = r["Answer"], r["Answer_type"]
    if typ == "option":
        return a.strip("()").upper()
    if typ == "bool":
        return "True" if a else "False"
    if typ.startswith("list"):
        return "$[" + ", ".join(num(x) for x in a) + "]$"
    s = num(a)
    if r["field"] in SUBJECT_FIELDS:
        u = unit_of(r["Question"])
        if u:
            return f"${s}\\ \\mathrm{{{u}}}$" if "times" not in s else f"${s}\\ \\mathrm{{{u}}}$"
    return f"${s}$" if "\\" in s else s


# ---------------------------------------------------------------------------------------------- load

def to_png(data: bytes) -> bytes | None:
    if data[:4] == b"\x89PNG":
        return data
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(io.BytesIO(data))
    buf = io.BytesIO()
    im.convert("RGBA" if im.mode in ("P", "RGBA", "LA") else "RGB").save(buf, "PNG")
    return buf.getvalue()


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    """(rows to import, {id: why set aside or left out})."""
    import pyarrow.parquet as pq
    meta = json.loads((data / "theoremqa_test.json").read_text(encoding="utf-8"))
    pics = pq.read_table(data / "test-00000-of-00001.parquet").to_pylist()
    rows, left = [], {}
    for r, p in zip(meta, pics, strict=True):
        if r["Question"] != p["Question"]:
            raise SystemExit(f"{r['id']}: the parquet and the JSON are not in the same order")
        key = r["id"][:-5] if r["id"].endswith(".json") else r["id"]
        if r["subfield"] in NO_SUBJECT:
            left[key] = f"no bank subject ({r['subfield']})"
            continue
        if key in ALREADY_IN_BANK:
            left[key] = f"the bank has it ({ALREADY_IN_BANK[key]})"
            continue
        if key in FIGURE_MISSING:
            left[key] = FIGURE_MISSING[key]
            continue
        if key in DROPPED:
            left[key] = DROPPED[key]
            continue
        q = clean_raw(r["Question"])
        for old, new in FIXES.get((key, "latexcode"), []):
            if q.count(old) != 1:
                raise SystemExit(f"FIX {key} latexcode: expected one {old!r}")
            q = q.replace(old, new)
        r = dict(r, Question=q)
        tex = _with_tables(clean_raw(q), key) if sum(" | " in ln for ln in q.splitlines()) >= 2 else to_latex(q, key)
        image = None
        if p["Picture"] and p["Picture"].get("bytes"):
            png = to_png(p["Picture"]["bytes"])
            if png is None:
                left[key] = "its picture is a GIF/JPEG and Pillow is not installed to convert it to PNG"
                continue
            name = "tqa-" + hashlib.sha1(png).hexdigest()[:16]
            tex += "\n\n" + GRAPHIC.format(name)
            image = [(name, png)]
        ans = key_text(r)
        for old, new in FIXES.get((key, "answer"), []):
            if ans.count(old) != 1:
                raise SystemExit(f"FIX {key} answer: expected one {old!r}")
            ans = ans.replace(old, new)
        ref = ""
        ex = data / r["explanation"] if r["explanation"] not in ("NONE", "") else None
        if ex and ex.suffix == ".txt" and ex.exists():
            ref = ex.read_text(encoding="utf-8", errors="replace").strip()
        group = ("subject" if r["field"] in SUBJECT_FIELDS or r["subfield"] in SUBJECT_SUBFIELDS else "math")
        rows.append({"potd": f"{SET} {key}", "set": SET, "idx": key, "orig": "", "source": SET,
                     "subsource": f"{r['field']} / {r['subfield']} / {key}", "latexcode": tex, "answer": ans,
                     "solution": None, "hints": None, "more_hints": None, "ref_solution": ref,
                     "group": group, "effort": "high" if group == "math" else None, "image": image})
    return rows, left


def _with_tables(q: str, key: str) -> str:
    """A question with a pipe table: the table cells and the text around it are converted separately."""
    marked = pipe_tables(q, lambda c: SENT + c + SENT)
    parts = re.split(r"(\\begin\{center\}.*?\\end\{center\})", marked, flags=re.S)
    out = []
    for p in parts:
        if not p.strip():
            continue
        if p.startswith("\\begin{center}"):
            p = re.sub(SENT + "(.*?)" + SENT, lambda m: to_latex(m.group(1), key), p)
        else:
            p = to_latex(p, key)
        out.append(p)
    return "\n\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON (images as names)")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, left = load(a.data)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new) + ERRORS
    for x in problems:
        print("CHECK", x)
    if a.set_aside:  # slips in the source data: these rows wait for a hand fix
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: [x for x in problems if r["potd"] in x] or [excluded[r["potd"]]]
               for r in new if any(r["potd"] in x for x in problems) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([{k: v for k, v in dict(r, problems=why[r["potd"]]).items() if k != "image"}
                                              for r in new if r["potd"] in why], ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = []
    for key, why_left in left.items():  # everything but the rows with no bank subject
        if not why_left.startswith("no bank subject"):
            print(f"left out: {key}: {why_left}")
    print("left out by reason:", json.dumps(collections.Counter(re.sub(r"\(.*", "", v).strip() for v in left.values()), ensure_ascii=False))
    print(json.dumps({"rows": len(rows), "in_bank": len(dup), "to_add": len(new), "check_problems": len(problems),
                      "groups": collections.Counter(r["group"] for r in new),
                      "images": sum(bool(r["image"]) for r in new)}))
    if a.dump:
        a.dump.write_text(json.dumps([dict(r, image=[n for n, _ in r["image"]] if r["image"] else None) for r in new],
                                     ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("theoremqa")
    for r in new:  # figures, before their questions exist
        for name, png in r["image"] or []:
            (TEXIMAGES / f"{name}.png").write_bytes(png)
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
        "note": "Benchmark sets imported by app/tools/import_<set>.py: the maths questions with the model and effort "
                "that solve them. Listing a question here puts it in run_sub.py's scope.", "questions": {}}
    doc["questions"].update({str(q): {"model": OPUS, "effort": r["effort"]} for q, r in added if r["group"] == "math"})
    ASSIGNMENTS.write_text(json.dumps(doc, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; "
          f"map={MAP_PATH}; assignments={ASSIGNMENTS} ({len(doc['questions'])} questions)")


if __name__ == "__main__":
    main()
