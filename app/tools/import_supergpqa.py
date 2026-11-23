"""
Import SuperGPQA: chemistry, chemical engineering and electrical engineering
-----------------------------------------------------------------------------
SuperGPQA (huggingface.co/datasets/m-a-p/SuperGPQA, ODC-BY; Amplify is private): graduate-level multiple choice
questions, mostly translated Chinese university material, up to 10 options and one correct letter. Rows kept
(owner 2026-11-23: all sources that do not depend on the OCR tool):
  * field Chemistry (1,769);
  * field Chemical Engineering and Technology (410);
  * subfield Materials Physics and Chemistry of the field Materials Science and Engineering (199);
  * the electrical fields Electrical Engineering, Electronic Science and Technology, Information and
    Communication Engineering, Control Science and Engineering, Instrument Science and Technology (1,546).
All rows go to group "subject": the classifier decides the subject afterwards. The dataset has no solutions.

Source "SuperGPQA", subsource None (owner 2026-11-23: a subsource must not identify a question); idx is the full
uuid and the map's original_source column holds "<field>, <subfield>". Difficulty and is_calculation are not kept.

Conversions:
  * Statement: the question, "Exactly one option is correct.", then the options each as "(A) ...", one per
    line with a blank line between. The key is the letter. $$ ... $$ in a stem becomes \\[ ... \\] and in an
    option inline math; OCR-spaced math ("4. 0 8 \\times1 0^{2}", "\\mathrm{~ k P a}") is closed up; unicode
    math symbols become commands; unicode sub/superscript formulas in prose become \\ce{...}; circled numbers
    become (1), (2), ...; bare % # & and runs of underscores are escaped.
  * Dropped: statements that need a figure or table the dataset does not carry, rows whose key letter is
    missing or whose key option text differs from the key text, and rows where the keyed option has an
    identical twin (ambiguous). Near-duplicates inside the set are collapsed to one row.
  * Per-row repairs and drops: supergpqa_fixes.json (same shape as ugphysics_fixes.json, key = uuid[:12]).

Rows the bank already has (same latex_hash or 85% of 5-word shingles) are skipped and listed.
On --apply: backup, insert (topic/branch/subtopic Uncategorized), append to benchmarks_map.csv. Nothing goes
into benchmarks_assignments.json (subject rows).

Usage (repo root):
  python -m app.tools.import_supergpqa --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_supergpqa --data DIR --apply
DIR holds supergpqa/SuperGPQA-all.jsonl (or SuperGPQA-all.jsonl itself).
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "SuperGPQA"
SOURCE = "SuperGPQA"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SET_ASIDE_PATH = Path("app/data/appdata/supergpqa_set_aside.json")
FIELDS = {
    "Chemistry",
    "Chemical Engineering and Technology",
    "Electrical Engineering",
    "Electronic Science and Technology",
    "Information and Communication Engineering",
    "Control Science and Engineering",
    "Instrument Science and Technology",
}
EXTRA_SUBFIELDS = {"Materials Physics and Chemistry"}
NEAR_OWN = 0.85

_FIXES = json.loads(Path(__file__).with_name("supergpqa_fixes.json").read_text(encoding="utf-8")) if Path(__file__).with_name("supergpqa_fixes.json").exists() else {"fixes": [], "dropped": {}}
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPS: dict[str, str] = dict(_FIXES["dropped"])

MATH_RE = re.compile(r"(\$\$.*?\$\$|\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\])", re.S)
SYMBOLS = {
    "\u00b1": r"\pm", "\u00d7": r"\times", "\u00b7": r"\cdot", "\u2219": r"\cdot", "\u22c5": r"\cdot",
    "\u2022": r"\cdot", "\u00b0": r"^{\circ}", "\u00b2": "^{2}", "\u00b3": "^{3}", "\u00b9": "^{1}",
    "\u2074": "^{4}", "\u2076": "^{6}", "\u2077": "^{7}", "\u2079": "^{9}", "\u2070": "^{0}",
    "\u207a": "^{+}", "\u207b": "^{-}", "\u2212": "-", "\u2248": r"\approx", "\u2264": r"\leq",
    "\u2265": r"\geq", "\u2260": r"\neq", "\u221a": r"\surd", "\u2220": r"\angle", "\u2192": r"\rightarrow",
    "\u2193": r"\downarrow", "\u21cc": r"\rightleftharpoons", "\u2206": r"\Delta", "\u0394": r"\Delta",
    "\u25b3": r"\Delta", "\u03a9": r"\Omega", "\u03bc": r"\mu", "\u00b5": r"\mu", "\u03b1": r"\alpha",
    "\u03b2": r"\beta", "\u03b3": r"\gamma", "\u0263": r"\gamma", "\u03b4": r"\delta", "\u03b8": r"\theta",
    "\u03bb": r"\lambda", "\u03c0": r"\pi", "\u03c3": r"\sigma", "\u03c6": r"\varphi", "\u03d5": r"\phi",
    "\u03a6": r"\Phi", "\u03c9": r"\omega", "\u2211": r"\sum", "\u2030": r"\%_{0}", "\u00c5": r"\mathrm{\AA}",
    "\u2236": ":", "\u25a1": r"\square", "\u1e41": r"\dot{m}", "\U0001d774": r"\epsilon",
    **{c: "_{" + str(i) + "}" for i, c in enumerate("\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089")},
}
CIRCLED = {chr(0x2460 + i): f"({i + 1})" for i in range(20)}
SUB = {c: str(i) for i, c in enumerate("\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089")}
SUP = {c: str(i) for i, c in enumerate("\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")}
SUP.update({"\u207a": "+", "\u207b": "-"})
SUBSUP_RE = re.compile(r"[\u2080-\u2089\u2070\u00b9\u00b2\u00b3\u2074-\u2079\u207a\u207b]")
FORMULA_RE = re.compile(
    r"(?<![A-Za-z\\{])(?:[A-Z][a-z]?|[()\[\]]|\d)*(?:[\u2080-\u2089]|[\u2070\u00b2\u00b3\u2074-\u2079\u207a\u207b])"
    r"[A-Za-z0-9()\[\]\u2080-\u2089\u2070\u00b9\u00b2\u00b3\u2074-\u2079\u207a\u207b]*"
)
FIGURE_RE = re.compile(
    r"\b(?:fig(?:ure|\.)?\s*\d|(?:in|see|from|of|by|to)\s+(?:the\s+)?(?:fig(?:ure)?s?|diagram|graph|table|chart|"
    r"plot|curve|sketch)\b|(?:as\s+)?shown\s+(?:in|below|above)|as\s+shown|the\s+(?:following|above|given|attached)\s+"
    r"(?:figure|diagram|circuit\s+diagram|graph|chart|table|network)|figure\s+(?:below|above|shows?)|"
    r"(?:circuit|network|figure|diagram)\s+(?:is\s+)?(?:shown|given)\b|shown\s+in\s+fig)",
    re.I,
)
FOREIGN_RE = re.compile("[Ѐ-ӿ؀-ۿ가-힯぀-ヿ一-鿿]")
NUM_GAP_RE = re.compile(r"(?<=[\d.]) +(?=[\d.])")
WORD_BOX_RE = re.compile(r"\\(mathrm|mathbf|textbf|text|mathit|operatorname)\{([^{}]*)\}")


def label(uuid: str) -> str:
    return f"{SET} {uuid[:12]}"


def spaced_word(m: re.Match) -> str:
    """Close up OCR-spaced letters in \\mathrm{~ k P a}; drop the stray ~."""
    cmd, c = m.group(1), m.group(2)
    c2 = c.replace("~", " ").strip()
    toks = c2.split()
    if len(toks) > 1 and all(len(t) <= 2 for t in toks) and cmd != "text":
        c2 = "".join(toks)
    elif c2 != c.strip():
        c2 = " ".join(toks)
    return f"\\{cmd}{{{c2}}}"


def clean_math(m: str) -> str:
    m = m.replace("\n", " ")
    m = re.sub(r"\\(Delta|vert|gamma|eta|alpha|beta|omega|sigma|theta)(?=[A-Za-z])", r"\\\1 ", m)  # \DeltaH, \vertAg
    m = re.sub(r"\\degree(?![A-Za-z])", r"^{\\circ}", m)
    m = TEXT_DEG_RE.sub(lambda x: "^{\\circ}" + (f"\\text{{{x.group(1)}}}" if x.group(1) else ""), m)
    m = re.sub(r"(?<!\\)%", r"\\%", m)
    m = WORD_BOX_RE.sub(spaced_word, m)
    while True:
        n = NUM_GAP_RE.sub("", m)
        if n == m:
            break
        m = n
    m = re.sub(r"\s*\^\s*\{", "^{", m)
    m = re.sub(r"(\d)\s+\\times", r"\1\\times", m)
    m = re.sub(r"\\times\s*(?=\d)", r"\\times ", m)
    m = re.sub(r"\\sqrt\{\}\s*([\w(])", lambda x: "\\sqrt{" + x.group(1) + "}", m)
    return re.sub(r"\s+", " ", m).strip()


def chem_tokens(text: str) -> str:
    """Formulas with unicode sub/superscripts in prose: H\u2082O -> \\ce{H2O}, CO\u2083\u00b2\u207b -> \\ce{CO3^2-}."""

    def one(m: re.Match) -> str:
        s, out, i = m.group(0), [], 0
        while i < len(s):
            c = s[i]
            if c in SUB:
                out.append(SUB[c])
            elif c in SUP:
                j = i
                run = ""
                while j < len(s) and s[j] in SUP:
                    run += SUP[s[j]]
                    j += 1
                out.append("^" + (run if run[-1:] in "+-" and len(run) > 1 and run[:-1].isdigit() else run))
                i = j
                continue
            else:
                out.append(c)
            i += 1
        return "\\ce{" + "".join(out) + "}"

    return FORMULA_RE.sub(one, text)


SYM_RE = re.compile("[" + "".join(re.escape(c) for c in SYMBOLS) + "]")


def prose_symbol(m: re.Match) -> str:
    c = m.group(0)
    if c == "∶":
        return ":"
    if c == "−":
        return "$-$"
    return "$" + SYMBOLS[c] + "$"


def prose(text: str) -> str:
    text = chem_tokens(text)
    for k, v in CIRCLED.items():
        text = text.replace(k, v)
    text = re.sub(r"(?<!\\)%", r"\\%", text)
    text = re.sub(r"(?<!\\)#", r"\\#", text)
    text = re.sub(r"(?<!\\)&", r"\\&", text)
    text = re.sub(r"_{2,}", lambda m: "\\_" * min(len(m.group(0)), 5), text)
    text = re.sub(r"(?<!\\)_", r"\\_", text) if "$" not in text and "\\ce{" not in text else text
    out = []
    for part in re.split(r"(\\ce\{[^{}]*\})", text):
        if part.startswith("\\ce{"):
            out.append(part)
            continue
        part = SYM_RE.sub(prose_symbol, part)
        out.append(part)
    return "".join(out)


def symbols_in_math(m: str) -> str:
    return re.sub("[" + "".join(re.escape(c) for c in SYMBOLS) + "]", lambda x: SYMBOLS[x.group(0)] + " ", m)


CONTROL = {"\x07": "\\a", "\x08": "\\b", "\x0c": "\\f", "\x0b": "\\v"}
LOST_BACKSLASH_RE = re.compile(r"[\t\r](?=[A-Za-z])|\n(?=(?:u|i|abla|eq|ot|eg|ewline|less|mid|parallel|subset)\b)")
PAREN_RE = re.compile(r"\\\((.*?)\\\)", re.S)
BRACKET_RE = re.compile(r"\\\[(.*?)\\\]", re.S)


def repair_raw(text: str) -> str:
    """The dataset lost backslashes before a b f t r n v (they became control characters)."""
    for c, v in CONTROL.items():
        text = text.replace(c, v)
    text = LOST_BACKSLASH_RE.sub(lambda m: "\\" + {"\t": "t", "\r": "r", "\n": "n"}[m.group(0)[0]], text)
    text = text.replace("```", "")
    if text.count("\\(") == text.count("\\)") > 0:
        text = PAREN_RE.sub(lambda m: "$" + m.group(1).replace("$", "") + "$", text)
    if text.count("\\[") == text.count("\\]") > 0:
        text = BRACKET_RE.sub(lambda m: "$$" + m.group(1).replace("$", "") + "$$", text)
    return text


def close_math(text: str) -> str:
    """A truncated option: close open braces and an open $."""
    depth = 0
    k = 0
    while k < len(text):
        if text[k] == "\\":
            k += 2
            continue
        depth += {"{": 1, "}": -1}.get(text[k], 0)
        k += 1
    if depth > 0:
        text += "}" * depth
    if len(re.findall(r"(?<!\\)\$", text)) % 2:
        text = text[:-2] + "$" if text.endswith("\\$") else text + "$"
    return text


BARE_LATEX_RE = re.compile(r"\\[A-Za-z]{2,}|[\^_]")
LOST_SLASH_RE = re.compile(r"(?<![\\A-Za-z])(?:left\s*[\[(|.]|right\s*[\])|.]|begin\{|end\{|frac\{|mathrm\{|dot\{|hat\{)")
TEXT_DEG_RE = re.compile(r"\\text\{\s*\^\{\\circ\}\s*([A-Za-z]*)\s*\}")


def tidy(text: str, option: bool = False) -> str:
    """One field of the statement: the math cleaned, the prose escaped and symbol-fixed."""
    text = repair_raw(text)
    if option:
        text = close_math(text)
        if "$" not in text and BARE_LATEX_RE.search(text):
            text = "$" + text.strip() + "$"
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ").replace("\u200b", "")
    text = text.replace("\u2019", "'").replace("\u2018", "`").replace("\u201c", "``").replace("\u201d", "''")
    text = text.replace("\uff0c", ",").replace("\uff1b", ";").replace("\u2026", "\\ldots{}")
    text = re.sub(r"\\\\\s*$", "", text)
    parts = re.split(r"(\$\$.*?\$\$|\$.*?\$)", text, flags=re.S)
    out = []
    for i, p in enumerate(parts):
        if i % 2:
            disp = p.startswith("$$")
            inner = symbols_in_math(clean_math(p[2:-2] if disp else p[1:-1]))
            inner = TEXT_DEG_RE.sub(lambda x: "^{\\circ}" + (f"\\text{{{x.group(1)}}}" if x.group(1) else ""), inner)
            if not inner:
                continue
            if " " in inner and re.fullmatch(r"[A-Za-z][A-Za-z ,.'-]+", inner):  # words set in math italics
                inner = "\\text{" + inner + "}"
            if disp and not option:
                out.append("\n\\[\n" + inner + "\n\\]\n")
            else:
                out.append("$" + inner + "$")
        else:
            out.append(prose(p))
    t = "".join(out)
    if option:
        t = re.sub(r"\$\s+\$", "$, $", t)
        t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def build_statement(stem: str, opts: list[str]) -> str:
    low = stem.lower()
    note = [] if any(k in low for k in ("exactly one", "only one correct")) else ["Exactly one option is correct."]
    return "\n\n".join([stem, *note, *(f"({chr(65 + i)}) {o}" for i, o in enumerate(opts))])


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    path = data if data.is_file() else next(data.rglob("SuperGPQA-all.jsonl"))
    rows, dropped, seen = [], {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["field"] not in FIELDS and r["subfield"] not in EXTRA_SUBFIELDS:
            continue
        key = r["uuid"][:12]
        lab = label(r["uuid"])
        if key in DROPS:
            dropped[lab] = DROPS[key]
            continue
        raw_opts, letter = r["options"], r["answer_letter"]
        k = ord(letter) - 65 if len(letter) == 1 else -1
        if not 0 <= k < len(raw_opts):
            dropped[lab] = "key letter outside the options"
            continue
        if raw_opts[k].strip() != r["answer"].strip():
            dropped[lab] = "key text differs from the keyed option"
            continue
        if LOST_SLASH_RE.search(repair_raw(r["question"] + "\n" + "\n".join(raw_opts))):
            dropped[lab] = "backslashes lost in the dataset's LaTeX (left[ begin{matrix} ...)"
            continue
        if FOREIGN_RE.search(r["question"] + "".join(raw_opts)):
            dropped[lab] = "text in another script (Chinese, Korean, Cyrillic, Arabic digits)"
            continue
        if FIGURE_RE.search(r["question"]) or any(FIGURE_RE.search(o) for o in raw_opts):
            dropped[lab] = "needs a figure or table the dataset does not carry"
            continue
        stem = tidy(r["question"])
        opts = [tidy(o, option=True) for o in raw_opts]
        for fld in ("stem", "options"):
            for old, new in HAND_FIXES.get((key, fld), []):
                src = stem if fld == "stem" else "\n".join(opts)
                if src.count(old) != 1:
                    raise SystemExit(f"HAND FIX {key} {fld}: expected one {old!r}")
                if fld == "stem":
                    stem = stem.replace(old, new)
                else:
                    opts = [o.replace(old, new) for o in opts]
        if not stem or any(not o for o in opts):
            dropped[lab] = "empty question or option"
            continue
        if sum(o == opts[k] for o in opts) > 1:
            dropped[lab] = "keyed option has an identical twin"
            continue
        text = build_statement(stem, opts)
        problems = check([{"potd": lab, "source": SOURCE, "latexcode": text, "answer": letter, "solution": None, "hints": None, "more_hints": None}])
        if problems:
            dropped[lab] = "markup broken in the dataset text (" + problems[0].split(": ", 1)[1].split(" [")[0][:40] + ")"
            continue
        sh = shingles(text)
        row = {
            "potd": lab,
            "set": SET,
            "idx": r["uuid"],
            "orig": f"{r['field']}, {r['subfield']}",
            "source": SOURCE,
            "subsource": None,  # owner 2026-11-23: no question ids or category labels; they live in the map
            "latexcode": text,
            "answer": letter,
            "solution": None,
            "hints": None,
            "more_hints": None,
            "ref_solution": "",
            "group": "subject",
            "effort": None,
            "image": None,
        }
        rows.append(row)
        seen[lab] = sh
    # near-duplicates inside the set: keep the first
    index: dict[str, list[str]] = collections.defaultdict(list)
    keep = []
    for row in rows:
        g = seen[row["potd"]]
        hits = collections.Counter(x for gg in g for x in index.get(gg, ()))
        if g and hits and hits.most_common(1)[0][1] / len(g) >= NEAR_OWN:
            dropped[row["potd"]] = f"near-duplicate of {hits.most_common(1)[0][0]}"
            continue
        for gg in g:
            index[gg].append(row["potd"])
        keep.append(row)
    return keep, dropped


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
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
        SET_ASIDE_PATH.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    reasons = collections.Counter(re.sub(r"\d+", "N", re.sub(r"of SuperGPQA \w+", "of X", v)) for v in dropped.values())
    print(
        json.dumps(
            {
                "rows_kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "by_field": collections.Counter(r["orig"].split(",")[0] for r in new),
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
    backup_db("supergpqa")
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
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
