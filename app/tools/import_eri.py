"""
Import ERI (Engineering Reasoning and Instruction): calculation rows of mechanical, power/electronics and industrial engineering
------------------------------------------------------------------------------------------------------------------------------
ERI (huggingface.co/datasets/mznaser/ERI-Engineering-Reasoning-and-Instruction, CC-BY-NC-4.0; Amplify is private) is an
LLM-written set of engineering instructions with a worked response (train + validation + test, 9 fields). It is plain text
with unicode symbols, not LaTeX, and the responses were never checked by a solver: they can hold arithmetic slips. Owner
2026-11-25 ("import as many sources as possible"): only rows of type CALC (a calculation with a definite final value) of

  * field mechanical_engineering (all seven subdomains: dynamics_vibrations, fluid_mechanics, heat_transfer, hvac,
    machine_design, manufacturing, thermodynamics);
  * field electrical_engineering, subdomains circuits, electronics (devices, semiconductors) and power_systems
    (power and energy);
  * field industrial_engineering (five subdomains: not ergonomics, whose questions the owner had deleted);
  * nuclear: the dataset has no nuclear subdomain (a keyword search for nuclear / reactor / fission / neutron finds
    only chemical reactors), so nothing is taken for it.

Per subdomain at most CAP rows, in the order of a hash of the question (deterministic), after every filter below.

Source "ERI" (so the owner can find the rows), subsource "<Field>, <Subdomain>" (a group, never an id); idx is
"<field>/<subdomain>/<split>/<hash>" and the map's original_source column holds the same without the hash.

Conversions (the text is converted to LaTeX by tex_plain):
  * unicode symbols become math (Omega, mu, tau, degree, plus-minus, times, approx, superscript and subscript runs);
    1e-6 / 2.2e3 become $1\\times10^{-6}$; sqrt(x), a^b, a_b become math; & % # _ { } escaped; < > | * in math.
  * Answer: the text after the response's last "Answer:" / "Result:" marker (units kept, several parts as written).
  * Solution: none stored (2026-11-25: the responses are LLM-written and unverified, so the rows go through the
    blind solve and the judge like any keyed question); the response is kept in ref_solution.
  * Dropped: responses that show second thoughts (Actually, Alternatively, recompute ...), rows without a final answer
    marker or with an answer longer than 220 characters, statements needing a figure or table, characters that have no
    LaTeX form here, near-duplicates (85% of 5-word shingles) inside the set.
Rows the bank already has are skipped and listed. On --apply: backup, insert (topic/branch/subtopic Uncategorized),
append to benchmarks_map.csv, keep ref_solution in benchmarks_solutions.json. Nothing goes into benchmarks_assignments.json.

Usage (repo root):
  python -m app.tools.import_eri --data DIR --dry-run [--dump rows.json] [--set-aside [--exclude fails.json]]
  python -m app.tools.import_eri --data DIR --apply
DIR holds train.jsonl, val.jsonl (or validation.jsonl) and test.jsonl.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections.abc import Callable
from pathlib import Path

from app.tools.import_answer_sets import duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash
from app.tools.import_supergpqa import FIGURE_RE

SET = "ERI"
SOURCE = "ERI"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/eri_set_aside.json")
MIN_SOLUTION = 150
CAP = 120
NEAR_OWN = 0.85
MAX_ANSWER = 220
GROUPS = {  # field -> subdomains (None: all)
    "mechanical_engineering": None,
    # not ergonomics: owner 2026-11-25 "Delete all the ergonomics questions" (the 120 rows of that subdomain went)
    "industrial_engineering": {"reliability", "quality_control", "engineering_statistics", "production_planning",
                               "operations_research"},
    "electrical_engineering": {"circuits", "electronics", "power_systems"},
}

_FIX_PATH = Path(__file__).with_name("eri_fixes.json")
_FIXES = json.loads(_FIX_PATH.read_text(encoding="utf-8")) if _FIX_PATH.exists() else {"fixes": [], "dropped": {}}
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPS: dict[str, str] = dict(_FIXES["dropped"])

DOUBT_RE = re.compile(
    r"\b(?:actually|alternatively|wait|recompute|recalculate|re-?check|oops|hmm|correction|mistake|let me|not applicable|"
    r"instead|however|hold on|on second thought|I think)\b|\?",
    re.I,
)
MARK_RE = re.compile(r"(?:final\s+answers?|answers?|results?|final\s+results?)\s*(?:\([^)]*\))?\s*[:\-=]\s*", re.I)

# --- plain text to LaTeX -------------------------------------------------------------------------------------------
GREEK_CAP = {"Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega"}
SYMBOLS = {
    "±": r"\pm", "×": r"\times", "·": r"\cdot", "⋅": r"\cdot", "∙": r"\cdot", "•": r"\cdot",
    "°": r"^{\circ}", "−": "-", "≈": r"\approx", "≤": r"\leq", "≥": r"\geq", "≠": r"\neq",
    "→": r"\rightarrow", "←": r"\leftarrow", "⇒": r"\Rightarrow", "↑": r"\uparrow", "↓": r"\downarrow",
    "∞": r"\infty", "∫": r"\int", "∂": r"\partial", "∇": r"\nabla", "∑": r"\sum", "∏": r"\prod",
    "∝": r"\propto", "∆": r"\Delta", "µ": r"\mu", "ℓ": r"\ell", "′": "'", "″": "''",
    "≅": r"\cong", "∼": r"\sim", "≡": r"\equiv", "≪": r"\ll", "≫": r"\gg", "∈": r"\in",
    "∣": r"\mid", "⊥": r"\perp", "∥": r"\parallel", "∠": r"\angle", "÷": r"\div",
    "½": r"\frac{1}{2}", "¼": r"\frac{1}{4}", "¾": r"\frac{3}{4}", "ϕ": r"\phi", "ϵ": r"\epsilon",
    "ϑ": r"\vartheta", "ϖ": r"\varpi", "ϱ": r"\varrho", "Ω": r"\Omega", "Å": r"\mathrm{\AA}",
    "‰": r"\text{\textperthousand}", "√": r"\surd",
}
SUP = {c: str(i) for i, c in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹")}
SUP.update({"⁺": "+", "⁻": "-"})
SUB = {c: str(i) for i, c in enumerate("₀₁₂₃₄₅₆₇₈₉")}
SUB.update({"₊": "+", "₋": "-"})
PROSE_MAP = {
    "’": "'", "‘": "`", "“": "``", "”": "''", "–": "--", "—": "---", "…": r"\ldots{}",
    " ": " ", " ": " ", " ": " ", "‑": "-", "‐": "-", "­": "", "​": "",
}
SUPSUB_RUN = re.compile("[" + "".join(SUP) + "]+|[" + "".join(SUB) + "]+")
PH0 = 0xE000
PIECES: list[str] = []  # math pieces of the text being converted (placeholders in the text)
COMBINING = {"̇": r"\dot", "̄": r"\bar", "̂": r"\hat", "̈": r"\ddot", "̃": r"\tilde"}
COMBINING_RE = re.compile("(.)([" + "".join(COMBINING) + "])")
DOLLAR = ""
NUM = r"\d+(?:\.\d+)?"
SQRT_RE = re.compile(r"(?:sqrt|√)\s*\(((?:[^()]|\([^()]*\))*)\)|√\s*([A-Za-z0-9.]+)")
SCI_RE = re.compile(rf"(?<![\w.]){NUM}[eE][+\-−]?\d+(?![\w])")
POW_RE = re.compile(
    r"(?:(?<![\w.])\w+(?:\.\d+)?|\((?:[^()]|\([^()]*\))*\))\^"
    r"(?:\{[^{}]*\}|\((?:[^()]|\([^()]*\))*\)|[+\-−]?[A-Za-z0-9]+(?:\.\d+)?)"
    r"(?:_(?:\{[^{}]*\}|[A-Za-z0-9]+))?"
)
POW_PARTS_RE = re.compile(r"(\{[^{}]*\}|\(.*\)|[+\-−]?[A-Za-z0-9]+(?:\.\d+)?)(?:_(\{[^{}]*\}|[A-Za-z0-9]+))?")
SUBS_RE = re.compile(
    r"(?<![\w\\])([A-Za-z]+)((?:_(?:\{[^{}]*\}|[A-Za-z0-9]+(?:\.\d+)?))+)(?:\^(\{[^{}]*\}|[+\-]?[A-Za-z0-9]+))?"
)
SUB_AFTER_SUB_RE = re.compile("(_[A-Za-z0-9]+)([₀-₉]+)")


def sym(c: str) -> str:
    """LaTeX math for one unicode character, or ValueError."""
    if c in SYMBOLS:
        return SYMBOLS[c]
    if ord(c) < 128:
        return c
    try:
        name = unicodedata.name(c)
    except ValueError:
        raise ValueError(f"unknown character {c!r}") from None
    if name.startswith("GREEK SMALL LETTER "):
        n = name[19:].lower().replace("final sigma", "sigma").replace("lamda", "lambda")
        return "\\" + n if n not in ("alpha", "beta") else "\\" + n
    if name.startswith("GREEK CAPITAL LETTER "):
        n = name[21:].capitalize().replace("Lamda", "Lambda")
        return "\\" + n if n in GREEK_CAP else n[0]
    if unicodedata.category(c).startswith("L"):  # accented Latin letters
        return c
    raise ValueError(f"unsupported character {c!r} ({name.lower()})")


def math_inner(s: str) -> str:
    """Convert a snippet that is already known to be math."""
    s = re.sub("[\ue000-\uf8fe]", lambda m: PIECES[ord(m.group(0)) - PH0].strip("$"), s) if PIECES else s
    s = s.replace("*", r"\cdot ").replace("%", r"\%")
    s = SUPSUB_RUN.sub(lambda m: ("^{" if m.group(0)[0] in SUP else "_{") + "".join((SUP | SUB)[x] for x in m.group(0)) + "}", s)
    s = re.sub(r"(?<![\\A-Za-z])sqrt\(((?:[^()]|\([^()]*\))*)\)", lambda m: "\\sqrt{" + m.group(1) + "}", s)
    out = []
    for c in s:
        v = sym(c) if ord(c) > 127 else c
        out.append(v + (" " if v.startswith("\\") and ord(c) > 127 else ""))
    return "".join(out).strip()


def exp_braced(e: str) -> str:
    if e.startswith("{") and e.endswith("}"):
        return "{" + math_inner(e[1:-1]) + "}"
    if e.startswith("(") and e.endswith(")"):
        return "{" + math_inner(e[1:-1]) + "}"
    return "{" + math_inner(e) + "}"


def tex_plain(text: str, strip: bool = True) -> str:
    """Plain text with unicode symbols and ASCII math (x^2, sqrt(), 1e-3) to LaTeX prose with inline math."""
    for k, v in PROSE_MAP.items():
        text = text.replace(k, v)
    pieces = PIECES
    pieces.clear()

    def hold(tex: str) -> str:
        pieces.append(tex)
        return chr(PH0 + len(pieces) - 1)

    text = text.replace("$", DOLLAR)
    text = "".join(d if len(d := unicodedata.normalize("NFD", c)) == 2 and d[1] in COMBINING else c for c in text)
    text = COMBINING_RE.sub(lambda m: hold(f"${COMBINING[m.group(2)]}{{{m.group(1)}}}$"), text)

    def sqrt(m: re.Match) -> str:
        return hold("$\\sqrt{" + math_inner(m.group(1) if m.group(1) is not None else m.group(2)) + "}$")

    def sci(m: re.Match) -> str:
        mant, _, ex = re.match(rf"({NUM})([eE])([+\-−]?\d+)", m.group(0)).groups()
        return hold(f"${mant}\\times10^{{{ex.replace(chr(0x2212), '-').lstrip('+')}}}$")

    def power(m: re.Match) -> str:
        base, _, exp = m.group(0).partition("^") if not m.group(0).startswith("(") else (None, None, None)
        if base is None:
            depth = 0
            for k in range(len(m.group(0))):
                depth += (m.group(0)[k] == "(") - (m.group(0)[k] == ")")
                if depth == 0:
                    break
            base, exp = m.group(0)[: k + 1], m.group(0)[k + 2 :]
        parts = POW_PARTS_RE.fullmatch(exp)
        if parts is None:
            return hold(f"${math_inner(base)}^{exp_braced(exp)}$")
        sub = f"_{sub_braced(parts.group(2))}" if parts.group(2) else ""
        return hold(f"${math_inner(base)}^{exp_braced(parts.group(1))}{sub}$")

    def sub_one(s: str) -> str:
        s = s[1:-1] if s.startswith("{") else s
        return f"\\mathrm{{{s}}}" if len(s) > 1 and s.isalpha() else math_inner(s)

    def sub_braced(s: str) -> str:
        return "{" + sub_one(s) + "}"

    def subs(m: re.Match) -> str:
        b, chain, p = m.groups()
        b = f"\\mathit{{{b}}}" if len(b) > 1 else b
        items = re.findall(r"_(\{[^{}]*\}|[A-Za-z0-9]+(?:\.\d+)?)", chain)
        expr = sub_one(items[-1])
        for s in reversed(items[:-1]):
            expr = f"{sub_one(s)}_{{{expr}}}"
        return hold(f"${b}_{{{expr}}}" + (f"^{exp_braced(p)}" if p else "") + "$")

    # the dataset's scientific notation first, then roots, powers, subscripts
    text = SUB_AFTER_SUB_RE.sub(lambda m: m.group(1) + "_" + "".join(SUB[c] for c in m.group(2)), text)
    text = SQRT_RE.sub(sqrt, text)
    text = SCI_RE.sub(sci, text)
    text = POW_RE.sub(power, text)
    text = SUBS_RE.sub(subs, text)
    text = SUPSUB_RUN.sub(lambda m: hold("$" + ("^" if m.group(0)[0] in SUP else "_") + "{" + "".join((SUP | SUB)[x] for x in m.group(0)) + "}$"), text)
    out = []
    for ch in text:
        o = ord(ch)
        if PH0 <= o < PH0 + len(pieces):
            out.append(ch)
        elif ch == DOLLAR:
            out.append(DOLLAR)
        elif ch in "&%#":
            out.append("\\" + ch)
        elif ch == "_":
            out.append("\\_")
        elif ch in "{}":
            out.append("\\" + ch)
        elif ch == "^":
            out.append("\\^{}")
        elif ch == "~":
            out.append("$\\sim$")
        elif ch == "\\":
            out.append("\\textbackslash{}")
        elif ch in "<>|":
            out.append(f"${ch}$")
        elif ch == "*":
            out.append("$\\cdot$")
        elif o > 127:
            if ch not in SYMBOLS and unicodedata.category(ch).startswith("L") and not unicodedata.name(ch, "").startswith("GREEK"):
                out.append(ch)
            else:
                out.append("$" + sym(ch) + "$")
        else:
            out.append(ch)
    t = "".join(out)
    for i in range(len(pieces) - 1, -1, -1):
        t = t.replace(chr(PH0 + i), pieces[i])
    t = t.replace("$$", " ")  # adjacent inline maths merge ($a$$b$ -> $a b$)
    t = t.replace(DOLLAR, "\\$")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip() if strip else t


def tex_paragraphs(text: str) -> str:
    """A multi-line response: every line is its own paragraph."""
    lines = [tex_plain(x) for x in text.replace("\r", "").split("\n") if x.strip()]
    return "\n\n".join(lines)


def final_answer(resp: str) -> str | None:
    last = None
    for m in MARK_RE.finditer(resp):
        last = m
    if last is not None:
        ans = resp[last.end() :].strip()
        return re.sub(r"\s*\n\s*", "; ", ans).strip(" ;.") or None
    # no marker: the last sentence (of the last two) that states a value
    sents = [x.strip() for x in re.split(r"\n+|(?<=[.!])\s+(?=[A-Z(])", resp) if x.strip()]
    for s in reversed(sents[-2:]):
        if re.search(r"[=≈]", s) and re.search(r"\d", s) and not re.match(r"(?:Since|If|Because|Check|Note)\b", s):
            return s.strip(" ;.")
    return None


# --- shared by the importers of this wave ---------------------------------------------------------------------------
def dedupe_own(rows: list[dict], dropped: dict[str, str]) -> list[dict]:
    index: dict[str, list[str]] = collections.defaultdict(list)
    keep = []
    for row in rows:
        g = shingles(row["latexcode"])
        hits = collections.Counter(x for gg in g for x in index.get(gg, ()))
        if g and hits and hits.most_common(1)[0][1] / len(g) >= NEAR_OWN:
            dropped[row["potd"]] = f"near-duplicate of {hits.most_common(1)[0][0]}"
            continue
        for gg in g:
            index[gg].append(row["potd"])
        keep.append(row)
    return keep


def apply_fixes(row: dict, key: str) -> None:
    for fld in ("latexcode", "answer", "solution", "ref_solution"):
        for old, new in HAND_FIXES.get((key, fld), []):
            if row[fld] is None or row[fld].count(old) != 1:
                raise SystemExit(f"HAND FIX {key} {fld}: expected one {old!r}")
            row[fld] = row[fld].replace(old, new)


def run(load: Callable, name: str, set_aside_path: Path, doc: str, by: Callable[[dict], str], stats: collections.Counter) -> None:
    p = argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in the set-aside file)")
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
        set_aside_path.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {set_aside_path}")
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
                "with_stored_solution": sum(bool(r["solution"]) for r in new),
                "found_by_group": stats,
                "kept_by_group": collections.Counter(by(r) for r in rows),
                "to_add_by_group": collections.Counter(by(r) for r in new),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db(name)
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


# --- ERI -----------------------------------------------------------------------------------------------------------
STATS: collections.Counter = collections.Counter()


def nice(s: str) -> str:
    return "HVAC" if s == "hvac" else s.replace("_", " ").title()


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    cand: dict[tuple[str, str], list[tuple[str, dict]]] = collections.defaultdict(list)
    dropped: dict[str, str] = {}
    seen_hash: set[str] = set()
    for split, names in (("train", ["train.jsonl"]), ("val", ["val.jsonl", "validation.jsonl"]), ("test", ["test.jsonl"])):
        path = next((data / n for n in names if (data / n).exists()), None)
        if path is None:
            raise SystemExit(f"missing {names[0]} in {data}")
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["type"] != "CALC" or r["field"] not in GROUPS:
                continue
            subs = GROUPS[r["field"]]
            if subs is not None and r["subdomain"] not in subs:
                continue
            h = hashlib.sha1(r["instruction"].encode("utf-8")).hexdigest()
            if h in seen_hash:
                continue
            seen_hash.add(h)
            STATS[f"{r['field']}/{r['subdomain']}"] += 1
            cand[(r["field"], r["subdomain"])].append((h, dict(r, _split=split)))
    rows = []
    for (field, sub), items in sorted(cand.items()):
        kept = 0
        for h, r in sorted(items, key=lambda x: x[0]):
            if kept >= CAP:
                break
            lab = f"{SET} {h[:10]}"
            if h[:10] in DROPS:
                dropped[lab] = DROPS[h[:10]]
                continue
            resp, ins = r["response"].strip(), r["instruction"].strip()
            if DOUBT_RE.search(resp):
                dropped[lab] = "response shows second thoughts (arithmetic or method unsure)"
                continue
            if FIGURE_RE.search(ins):
                dropped[lab] = "needs a figure or table the dataset does not carry"
                continue
            ans = final_answer(resp)
            if not ans:
                dropped[lab] = "no final answer marker in the response"
                continue
            if len(ans) > MAX_ANSWER or not re.search(r"\d", ans):
                dropped[lab] = "final answer too long or without a value"
                continue
            try:
                stem, key, sol = tex_plain(ins), tex_plain(ans), tex_paragraphs(resp)
            except ValueError as e:
                dropped[lab] = str(e)
                continue
            row = {
                "potd": lab,
                "set": SET,
                "idx": f"{field}/{sub}/{r['_split']}/{h[:10]}",
                "orig": f"{field}, {sub}, {r['_split']}",
                "source": SOURCE,
                "subsource": f"{nice(field)}, {nice(sub)}",
                "latexcode": stem,
                "answer": key,
                "solution": None,  # LLM-written and unverified: solved blind, the response is a reference only
                "hints": None,
                "more_hints": None,
                "ref_solution": sol,
                "group": "subject",
                "effort": None,
                "image": None,
            }
            apply_fixes(row, h[:10])
            rows.append(row)
            kept += 1
    return dedupe_own(rows, dropped), dropped


def main() -> None:
    run(load, "eri", SET_ASIDE_PATH, __doc__, lambda r: r["orig"].rsplit(",", 1)[0], STATS)


if __name__ == "__main__":
    main()
