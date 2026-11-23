r"""Import XFinBench and FinanceMath (quant-finance word problems, text only)
==============================================================================
Two datasets, selected with --only xfinbench|financemath (default: both):

XFinBench (github.com/Zhihan72/XFinBench, huggingface.co/datasets/Zhihan/XFinBench, MIT): GPT-4o rewrites of
end-of-chapter questions of finance textbooks (Hull, Ross, Mishkin, ...). The calculation ("calcu") and
multiple-choice ("mcq") tasks of the test and validation CSVs are read; the true/false ("bool") task is skipped.
The CSVs do not say which textbook or chapter an item comes from, so the subsource is empty (owner rule 2026-11-23:
a subsource never identifies a question; task and id stay in benchmarks_map.csv via idx).
Dropped: items with a figure, items that refer to a figure, diagram or table that is not in the text.
Source "XFinBench".

FinanceMath (github.com/yale-nlp/FinanceMath, MIT): CFA-style numeric questions, test (1000, keys released July
2026) and validation (200). Accounting and financial-reporting items are skipped. The expert Python solution is
kept as ref_solution (plain text), never as the stored solution. Markdown tables become LaTeX tabular; items whose
tables are ragged or wide, and items that cite an exhibit that is not in the text, are dropped. Percent keys
state the unit ("4.73\%") or the statement asks for a decimal. Source "FinanceMath", no subsource.

Conversions: bare $ becomes \$, % becomes \%, \( \) becomes $ $, Unicode symbols become LaTeX, a "(Unit: dollar)"
tail becomes a sentence and a unit in the key, MCQ options go on their own lines as "(A) ...".

Rows the bank already has (same latex_hash or 85% of 5-word shingles), and rows that repeat a row of the other
dataset, are skipped and listed. On --apply: backup, insert (Uncategorized), append to benchmarks_map.csv, keep
ref_solution in benchmarks_solutions.json. Nothing goes into benchmarks_assignments.json.

Usage (repo root):
  python -m app.tools.import_quant_text --data DIR --dry-run [--only xfinbench|financemath] [--dump rows.json]
DIR holds xfinbench/{test_set,validation_set}.csv and financemath/{test,validation}.json.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import NEAR, duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/quant_text_set_aside.json")

_FIXES_PATH = Path(__file__).with_name("quant_text_fixes.json")
_FIXES = json.loads(_FIXES_PATH.read_text(encoding="utf-8")) if _FIXES_PATH.exists() else {"fixes": [], "dropped": {}}
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPS: dict[str, str] = dict(_FIXES["dropped"])

# --------------------------------------------------------------------------------------------- text cleaning
CHARS = {
    "\u2019": "'", "\u2018": "`", "\u201c": "``", "\u201d": "''", "\u2014": "---", "\u2013": "--",
    "\u2026": "\\ldots{}", "\u00a3": "\\pounds{}", "\u20ac": "\\texteuro{}", "\u00a0": " ", "\u2009": " ",
    "\u202f": " ", "\u200b": "", "\u2206": "$\\Delta$", "\u25b3": "$\\Delta$", "\u2212": "$-$", "\u00b1": "$\\pm$", "\u00d7": "$\\times$",
    "\u00b0": "$^{\\circ}$", "\u00bd": "$\\frac{1}{2}$", "\u00bc": "$\\frac{1}{4}$", "\u00be": "$\\frac{3}{4}$",
    "\u2248": "$\\approx$", "\u2264": "$\\leq$", "\u2265": "$\\geq$", "\u03c3": "$\\sigma$", "\u03bc": "$\\mu$",
    "\u03b2": "$\\beta$", "\u03b1": "$\\alpha$", "\u0394": "$\\Delta$", "\u03c1": "$\\rho$", "\u03bb": "$\\lambda$",
    "\u2192": "$\\to$", "\u00f7": "$\\div$", "\u2022": "$\\bullet$", "\u00e9": "\u00e9",
}
MATH_CHARS = {
    "\u2212": "-", "\u00b1": "\\pm ", "\u00d7": "\\times ", "\u00b0": "^{\\circ}", "\u2019": "'",
    "\u03c3": "\\sigma ", "\u03bc": "\\mu ", "\u03b2": "\\beta ", "\u03b1": "\\alpha ", "\u0394": "\\Delta ",
    "\u2248": "\\approx ", "\u2264": "\\leq ", "\u2265": "\\geq ", "\u00a0": " ", "\u03c1": "\\rho ",
    "\u03bb": "\\lambda ", "\u00f7": "\\div ",
}
MATH_RE = re.compile(r"\\\((.*?)\\\)|\\\[(.*?)\\\]|\$\$(.*?)\$\$", re.S)
TABULAR_RE = re.compile(r"\\begin\{(tabular\*?|array)\}.*?\\end\{\1\}", re.S)
SENTENCE_GLUE = re.compile(r"(?<=[a-z0-9\)%\"'])([.?!:])(?=[A-Z][a-z])")


def plain(s: str, amp: bool = True) -> str:
    """Escape one stretch of running text (no math in it) for LaTeX."""
    s = re.sub(r"\\text(?:dollar|\{\\\$\})", r"\\$", s)
    s = re.sub(r"\\text\{([^{}\\$]*)\}", r"\1", s)
    s = re.sub(r"(?<!\\)\$", r"\\$", s)
    s = re.sub(r"(?<!\\)%", r"\\%", s)
    s = re.sub(r"(?<!\\)#", r"\\#", s)
    s = re.sub(r"(?<!\\)_", r"\\_", s)
    s = re.sub(r"(?<!\\)\^", r"\\^{}", s)
    s = s.replace("~", "\\textasciitilde{}") if "\\~" not in s else s
    if amp:
        s = re.sub(r"(?<!\\)&", r"\\&", s)
    s = SENTENCE_GLUE.sub(r"\1 ", s)
    return "".join(CHARS.get(c, c) for c in s)


def inline_math(s: str) -> str:
    s = "".join(MATH_CHARS.get(c, c) for c in s)
    return re.sub(r"(?<!\\)%", r"\\%", s).strip()


def tabular(block: str) -> str:
    """A LaTeX tabular from the dataset: colours and floats removed, cells escaped."""
    block = re.sub(r"\\(?:rowcolor|cellcolor|columncolor)(?:\[[^\]]*\])?\{[^{}]*\}", "", block)
    m = re.match(r"\\begin\{(tabular\*?|array)\}(\{[^{}]*\})", block)
    head, body = m.group(0), block[m.end() : block.rindex("\\end{")]
    env = m.group(1)
    ncols = len(re.findall(r"[lcrXpmb]", re.sub(r"\{[^{}]*\}", "", m.group(2)[1:-1])))
    rows = re.split(r"(\\\\(?:\[[^\]]*\])?)", body)
    out = []
    for part in rows:
        if re.fullmatch(r"\\\\(?:\[[^\]]*\])?", part):
            out.append(part)
            continue
        cells = part.split("&")
        if len(cells) > ncols and "\\multicolumn" not in part:
            raise ValueError("table malformed in the dataset (more cells than columns)")
        out.append("&".join(plain(c, amp=False) for c in cells))
    body = re.sub(r"\n\s*\n", "\n", "".join(out))
    return f"{head}\n{body.strip()}\n\\end{{{'tabular' if env == 'array' else env}}}".replace(
        "\\begin{array}", "\\begin{tabular}"
    )


def latexify(text: str) -> str:
    """The dataset's text (currency in bare $, \\( \\) math, LaTeX tables) as bank LaTeX."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\\begin\{table\*?\}(\[[^\]]*\])?|\\end\{table\*?\}|\\centering|\\label\{[^{}]*\}", "", text)
    text = re.sub(r"\\caption\{([^{}]*)\}", r"\n\\textbf{\1}\n", text)
    # a table wrapped in display math
    text = re.sub(r"\\\[\s*(\\begin\{tabular.*?\\end\{tabular\})\s*\\\]", r"\1", text, flags=re.S)
    keep: list[str] = []

    def stash(s: str) -> str:
        keep.append(s)
        return f"\x01{len(keep) - 1}\x01"

    text = TABULAR_RE.sub(lambda m: "\n\n" + stash(tabular(m.group(0))) + "\n\n", text)

    def math(m: re.Match) -> str:
        if m.group(1) is not None:
            return stash("$" + inline_math(m.group(1)) + "$")
        body = m.group(2) if m.group(2) is not None else m.group(3)
        return stash("\\[\n" + inline_math(body) + "\n\\]")

    text = MATH_RE.sub(math, text)
    text = plain(text)
    text = re.sub(r"\x01(\d+)\x01", lambda m: keep[int(m.group(1))], text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def number(v: float | str) -> str:
    """A key number: 622440.0 -> 622440; 0.1305 stays."""
    s = str(v).strip()
    f = float(s)
    if "e" in s.lower():
        s = format(f, "f").rstrip("0").rstrip(".")
    if re.fullmatch(r"-?\d+\.0+", s):
        s = s.split(".")[0]
    return s


def grouped(s: str) -> str:
    sign, digits = ("-", s[1:]) if s.startswith("-") else ("", s)
    whole, _, frac = digits.partition(".")
    if len(whole) >= 5:
        whole = "{,}".join(re.findall(r"\d{1,3}(?=(?:\d{3})*$)", whole)) if False else f"{int(whole):,}".replace(",", "{,}")
    return sign + whole + ("." + frac if frac else "")


# --------------------------------------------------------------------------------------------- XFinBench
UNIT_RE = re.compile(r"\s*\(Unit:\s*([^()]*)\)\s*$")
NEEDS_FIGURE = re.compile(
    r"\b(?:Table \d+\.\d+|cumulative normal probability table|attached (?:figure|image|diagram)|given (?:the )?(?:diagram|figure)|(?:in|from|on) the (?:figure|diagram|graph|chart)"
    r"|(?:figure|diagram|graph|chart|exhibit|table|image|picture) (?:below|above|shown|given)|the (?:following|above|below) "
    r"(?:figure|diagram|graph|chart|table|exhibit)|shown in the|diagram of|the (?:table|figure|chart) (?:gives|shows|above|below))",
    re.I,
)
XF_PHRASE = {
    "decimal": "Give the answer as a decimal.",
    "decimal form": "Give the answer as a decimal.",
    "percent": "Give the answer in percent.",
    "percentage": "Give the answer in percent.",
    "percent per annum": "Give the answer in percent per annum.",
    "percentage per annum": "Give the answer in percent per annum.",
    "per annum": "Give the answer per annum, as a decimal.",
    "per annum in decimal form": "Give the answer per annum, as a decimal.",
    "rate": "Give the answer as a rate.",
    "numerical value": "Give the answer as a number.",
    "0 for reject, 1 for accept": "Answer 0 for reject or 1 for accept.",
}
XF_UNIT_TEX = {
    "dollar": r"\$", "dollars": r"\$",
    "million dollars": r"\$%s\ \text{million}", "million dollar": r"\$%s\ \text{million}",
    "million usd": r"\$%s\ \text{million}", "million": "%s\\ \\text{million}", "billion": "%s\\ \\text{billion}",
    "billion dollar": r"\$%s\ \text{billion}", "billion dollars": r"\$%s\ \text{billion}",
    "thousand dollars": r"\$%s\ \text{thousand}",
}
PLAIN_UNITS = {"decimal", "decimal form", "rate", "per annum", "per annum in decimal form", "numerical value",
               "0 for reject, 1 for accept", "index price"}
PERCENT_UNITS = {"percent", "percentage", "percent per annum", "percentage per annum"}


def xf_key(gt: str, unit: str | None) -> tuple[str, str]:
    """(answer key, sentence for the statement)."""
    n = number(gt)
    if unit is None:
        return n, ""
    if unit == "":  # a probability the dataset keys in percent
        return f"${n}\\%$", "Give the answer in percent."
    u = unit.strip().lower()
    if u in PERCENT_UNITS:
        return f"${n}\\%$", XF_PHRASE[u]
    if u in PLAIN_UNITS:
        return n, XF_PHRASE.get(u, "")
    sign, body = ("-", n[1:]) if n.startswith("-") else ("", n)
    if u in ("dollar", "dollars"):
        return f"${sign}\\${grouped(body)}$", "Give the answer in dollars."
    if u in XF_UNIT_TEX:
        t = XF_UNIT_TEX[u]
        what = "millions of dollars" if "million" in u else "billions of dollars" if "billion" in u else "thousands of dollars"
        return f"${sign}{t % grouped(body) if '%s' in t else t}$", f"Give the answer in {what}."
    words = plain(unit.strip(), amp=True)
    return f"${n}\\ \\text{{{words}}}$", f"Give the answer in {unit.strip()}."


def mcq_options(choice: str) -> list[tuple[str, str]] | None:
    t = choice.replace("\\n", "\n").replace("\r", "")
    marks = list(re.finditer(r"(?:^|\n)\s*\(?([A-J])[.)]\s+", t))
    if len(marks) < 2 or [m.group(1) for m in marks] != [chr(65 + i) for i in range(len(marks))]:
        return None
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(t)
        out.append((m.group(1), t[m.end() : end].strip()))
    return out


def load_xfinbench(data: Path) -> tuple[list[dict], dict[str, str]]:
    rows, dropped = [], {}
    for f in ("test_set", "validation_set"):
        for r in csv.DictReader((data / "xfinbench" / f"{f}.csv").open(encoding="utf-8-sig", newline="")):
            if r["task"] == "bool":
                continue
            rid = r["id"]
            key = f"XFinBench {rid}"
            if key in DROPS:
                dropped[key] = DROPS[key]
                continue
            if r["figure"].strip():
                dropped[key] = "needs a figure that is not in the text"
                continue
            q = r["question"].strip()
            if not TABULAR_RE.search(q) and NEEDS_FIGURE.search(q):
                dropped[key] = "refers to a figure or table that is not in the text"
                continue
            unit = None
            if r["task"] == "calcu":
                m = UNIT_RE.search(q)
                if m:
                    unit, q = m.group(1), q[: m.start()]
                try:
                    float(r["ground_truth"])
                except ValueError:
                    dropped[key] = "key is not a number"
                    continue
                if unit is None and re.search(r"probability", q.rsplit("?", 2)[-2] if "?" in q else q, re.I) and 1 < float(r["ground_truth"]) <= 100:
                    unit = ""
                ans, phrase = xf_key(r["ground_truth"], unit)
                try:
                    stem = latexify(q)
                except ValueError as e:
                    dropped[key] = str(e)
                    continue
                if phrase:
                    stem += " " + phrase
            else:
                opts = mcq_options(r["choice"])
                letters = re.findall(r"[A-J]", r["ground_truth"])
                if opts is None or not letters or not set(letters) <= {x for x, _ in opts}:
                    dropped[key] = "options or key unusable"
                    continue
                low = q.lower()
                note = "" if "exactly one" in low or "one or more" in low else (
                    "Exactly one option is correct." if len(letters) == 1 else "One or more options may be correct.")
                ans = ", ".join(sorted(letters))
                stem = "\n\n".join([latexify(q)] + ([note] if note else []) + [f"({x}) {latexify(t)}" for x, t in opts])
            rows.append(
                {
                    "potd": key, "set": "XFinBench", "idx": rid, "orig": "", "source": "XFinBench",
                    "subsource": None, "latexcode": stem, "answer": ans, "solution": None,
                    "hints": None, "more_hints": None, "ref_solution": "", "group": "subject", "effort": None,
                    "image": None,
                }
            )
    return rows, dropped


# --------------------------------------------------------------------------------------------- FinanceMath
FM_SKIP_TOPICS = {"Accounting"}
REPORTING = re.compile(
    r"\b(?:IFRS|U\.?S\.? GAAP|GAAP|balance sheet|income statement|statement of cash flows?|cash flow statement|inventory|"
    r"FIFO|LIFO|deferred tax|goodwill|lease liabilit|right-of-use|amortization expense|impairment|"
    r"equity method|consolidat|accounts receivable|accounts payable|retained earnings|cost of goods sold|"
    r"depreciation expense|capitalized|capitalised|restate|accrual|accrued|bad debt|warranty|pension (?:expense|obligation|asset))",
    re.I,
)
EXHIBIT = re.compile(
    r"\b(?:Exhibit \d|the (?:following |above |below )?(?:table|chart|figure|graph)|(?:table|figure|chart|graph) (?:below|above|\d)|"
    r"shown (?:below|above)|as shown in|according to the table)",
    re.I,
)
RATE_ASK = re.compile(
    r"\b(?:rate|return|yield|percent|percentage|growth|margin|cost of (?:equity|debt|capital)|WACC|IRR|volatility|"
    r"standard deviation|probability|premium|spread|discount|tax|weight|proportion|portion|share of|ROE|ROA|ROI|"
    r"coupon|inflation|dividend payout|retention|haircut|leverage ratio)\b|%",
    re.I,
)
NON_PERCENT_ASK = re.compile(
    r"\b(?:exchange rate|price|value|worth|amount|dollar|how many|number of|duration|beta|ratio of|sharpe|multiple|"
    r"present value|future value|payoff|profit|gain|loss|expense|cost of the|net)\b", re.I
)
FM_UNITS = {
    "dollar": r"\$", "percent": r"\%",
}


def md_table(md: str) -> str | None:
    """A Markdown table as LaTeX tabular; None when it is ragged or too wide."""
    lines = [ln.strip() for ln in md.strip().splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        if not ln.startswith("|"):
            return None
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) or c == "" for c in cells) and any("-" in c for c in cells):
            continue
        rows.append(cells)
    rows = [r for r in rows if any(r)]
    if not rows:
        return None
    caption = ""
    if len(rows[0]) > 1 and sum(bool(c) for c in rows[0]) == 1 and len(rows) > 1:
        caption = next(c for c in rows[0] if c)
        rows = rows[1:]
    width = max(len(r) for r in rows)
    if width > 8 or len(rows) > 30 or any(len(r) != width for r in rows):
        return None
    while width > 1 and all(not r[-1] for r in rows):  # an empty trailing column
        rows = [r[:-1] for r in rows]
        width -= 1
    out = []
    for r in rows:
        cells = []
        for c in r:
            c = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", c)
            c = re.sub(r"<br\s*/?>", " ", c)
            cells.append(plain(c, amp=True))
        out.append(" & ".join(cells) + " \\\\")
    spec = "l" + "r" * (width - 1)
    cap = f"\\textbf{{{plain(re.sub(r'[*]', '', caption))}}}\n\n" if caption else ""
    return cap + f"\\begin{{tabular}}{{{spec}}}\n\\hline\n" + "\n".join(out) + "\n\\hline\n\\end{tabular}"


def fm_percent(x: dict) -> str:
    """'percent', 'decimal' or '' (not a rate): how the executed key is expressed."""
    q = x["question"]
    ask = re.split(r"(?<=[.?])\s+", q.strip())[-1]
    words = ask.split(",")
    clause = words[-1] if len(words) > 1 and len(words[-1].split()) >= 4 else ask  # what is asked comes last
    rate_word = re.compile(r"\b(?:rate|return|yield|percent|percentage|growth)\b|%", re.I)
    if re.search(r"\b(?:convexity|elasticity|sensitivity|sharpe|multiple|t-stat\w*)\b", clause, re.I):
        return ""
    if not RATE_ASK.search(ask) or (NON_PERCENT_ASK.search(clause) and not rate_word.search(clause)):
        return ""
    code = x["python_solution"]
    gt = float(x["ground_truth"])
    rets = re.findall(r"^\s*return\s+([^\n]+)", code, re.M)
    line = rets[-1] if rets else ""
    name = re.match(r"\s*([A-Za-z_]\w*)\s*(?:#.*)?$", line)
    if name:  # the line that last assigned the returned name
        assigns = re.findall(rf"^\s*{name.group(1)}\s*=\s*([^\n]+)", code, re.M)
        line = (assigns[-1] if assigns else "") + " " + line
    if re.search(r"\*\s*100(?![\d.])|#.*(?:percent|%)", line, re.I):
        return "percent"
    pcts = re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", q)
    dec_in = any(re.search(rf"(?<![\d.]){re.escape(str(round(float(v) / 100, 6)).rstrip('0'))}|{re.escape(v)}\s*/\s*100", code) for v in pcts if float(v) != 0)
    lit_in = any(re.search(rf"=\s*{re.escape(v)}\s*(?:#|$)", code, re.M) for v in pcts)
    if pcts and dec_in:
        return "decimal"
    if pcts and lit_in:
        return "percent"
    if abs(gt) < 1:
        return "decimal"
    return "percent"


def load_financemath(data: Path) -> tuple[list[dict], dict[str, str]]:
    rows, dropped = [], {}
    items = []
    for f in ("test", "validation"):
        items += json.loads((data / "financemath" / f"{f}.json").read_text(encoding="utf-8"))
    for x in items:
        qid = x["question_id"]
        key = f"FinanceMath {qid}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        if x["topic"] in FM_SKIP_TOPICS:
            dropped[key] = "accounting topic"
            continue
        if REPORTING.search(x["question"] + " ".join(x["tables"])):
            dropped[key] = "financial-reporting question"
            continue
        if not x["tables"] and EXHIBIT.search(x["question"]):
            dropped[key] = "cites an exhibit or table that is not in the text"
            continue
        tabs = []
        bad = False
        for t in x["tables"]:
            lt = md_table(t)
            if lt is None:
                bad = True
                break
            tabs.append(lt)
        if bad:
            dropped[key] = "table too complex or ragged"
            continue
        kind = fm_percent(x)
        n = number(x["ground_truth"])
        stem = latexify(x["question"])
        ans, tail = n, ""
        if kind == "percent":
            ans, tail = f"${n}\\%$", "Give the answer in percent."
        elif kind == "decimal":
            tail = "Give the answer as a decimal, rounded to three decimal places."
        if tail:
            stem += (" " if re.search(r"[.?!]$", stem) else "\n\n") + tail
        if tabs:
            stem += "\n\n" + "\n\n".join(tabs)
        rows.append(
            {
                "potd": key, "set": "FinanceMath", "idx": qid, "orig": "", "source": "FinanceMath",
                "subsource": None, "latexcode": stem, "answer": ans, "solution": None,
                "hints": None, "more_hints": None, "ref_solution": x["python_solution"].strip(), "group": "subject",
                "effort": None, "image": None,
            }
        )
    return rows, dropped


# --------------------------------------------------------------------------------------------- common
def apply_fixes(rows: list[dict]) -> None:
    for r in rows:
        for fld in ("latexcode", "answer"):
            for old, new in HAND_FIXES.get((r["potd"], fld), []):
                if r[fld].count(old) != 1:
                    raise SystemExit(f"HAND FIX {r['potd']} {fld}: expected one {old!r}")
                r[fld] = r[fld].replace(old, new)


def norm_key(a: str) -> str:
    return re.sub(r"[^0-9a-z.-]", "", a.lower().replace("\\%", ""))


def self_duplicates(rows: list[dict]) -> dict[int, str]:
    """Rows that repeat an earlier row of this import (same text, or >= NEAR of the shingles)."""
    out, seen, index = {}, {}, collections.defaultdict(set)
    for k, r in enumerate(rows):
        h = latex_hash(r["latexcode"])
        if h in seen:
            out[k] = rows[seen[h]]["potd"]
            continue
        g = shingles(r["latexcode"])
        hits = collections.Counter(j for x in g for j in index.get(x, ()))
        # questions built on one shared set-up differ in what they ask: a repeat has the same key as well
        for j, n in hits.most_common(5):
            if n / max(len(g), 1) >= NEAR and norm_key(rows[j]["answer"]) == norm_key(r["answer"]):
                out[k] = rows[j]["potd"]
                break
        if k in out:
            continue
        seen[h] = k
        for x in g:
            index[x].add(k)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", choices=("xfinbench", "financemath"))
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped = [], {}
    stats = {}
    for name, loader in (("xfinbench", load_xfinbench), ("financemath", load_financemath)):
        if a.only in (None, name):
            r, d = loader(a.data)
            rows += r
            dropped.update(d)
            stats[name] = (len(r), len(d))
    apply_fixes(rows)
    sd = self_duplicates(rows)
    for k, why in sorted(sd.items()):
        dropped[rows[k]["potd"]] = f"repeats {why}"
    rows = [r for k, r in enumerate(rows) if k not in sd]

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
        SET_ASIDE_PATH.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    reasons = collections.Counter(re.sub(r"\d+", "N", v) for v in dropped.values())
    print(
        json.dumps(
            {
                "rows_kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
                "by_set": collections.Counter(r["set"] for r in new),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        (a.dump.with_name(a.dump.stem + "_dropped.json")).write_text(json.dumps(dropped, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("quant-text")
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
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"],
                 r["answer"], r["solution"], r["hints"], r["more_hints"], h),
            )
            existing.add(h)
            added.append((cur.lastrowid, r))
        conn.commit()
    finally:
        conn.close()
    new_file = not MAP_PATH.exists() or MAP_PATH.stat().st_size == 0
    with MAP_PATH.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update(
        {str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]} for q, r in added if r["ref_solution"]}
    )
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
