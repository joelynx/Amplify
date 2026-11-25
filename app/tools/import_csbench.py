"""
Import CS-Bench (English part)
------------------------------
CS-Bench (huggingface.co/datasets/CS-Bench/CS-Bench, CC BY-NC 4.0; Amplify is private): computer-science
questions from Chinese graduate-entrance exams, translated to English, in four domains (data structures and
algorithms, computer organization, computer network, operating system). Only English/test.jsonl (2,183 rows)
and English/valid.jsonl (236 rows) are read; Chinese-only rows do not occur in them.

Rows (owner decisions of 2026-11-25, owner asleep):
  * Source "CS-Bench", no subsource (the dataset's domain, sub-domain, format, tag and split go to the map's
    original_source column only); all rows go to group "subject" for the classifier.
  * Multiple-choice: stem, "Exactly one option is correct.", then "(A) ..." to "(D) ..." on lines of their own;
    key = the letter.
  * Assertion (true/false): "Is the following assertion true or false?" + the assertion; key "True" / "False".
  * Fill-in-the-blank: the sentence with its blank (an underlined gap); key = the short answer (at most
    MAX_FILL characters); longer answers are dropped.
  * Open-ended: imported WITHOUT an answer (answer None); the dataset's reference answer is kept in
    ref_solution only (app/data/appdata/benchmarks_solutions.json), the solver writes the solution.
  * Dropped: rows that need a figure or table the dataset does not ship, "write a program / design an
    algorithm" tasks, open-ended rows whose statement already contains the answer, duplicates within the
    dataset (test vs validation included), rows the bank already has (listed in the dry-run output), and
    the rows named in csbench_fixes.json "dropped".
  * Stored solution: the dataset's Explanation (MCQ / assertion / fill rows) when it has at least MIN_SOLUTION
    characters; every explanation is also kept in ref_solution.

Conversions (the dataset is plain text, not LaTeX): Chinese-exam roman numerals and list marks become ASCII
("Ⅰ、Ⅱ" -> "I, II", circled digits -> "(1)"); x^y, x_y, brace sets, symbols (arrows, x, mu, <=, ...) become
$...$ math; the characters LaTeX reserves are escaped; code lines go into a verbatim block; line ends
become paragraph breaks. Per-row repairs of the raw text live in csbench_fixes.json ({"fixes": [{"key",
"field", "fixes": [[old, new]]}], "dropped": {key: reason}}; the fields are the dataset's own: Question, A-D,
Answer, Explanation).

Usage (repo root):
  python -m app.tools.import_csbench --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_csbench --data DIR --apply
DIR holds test.jsonl and valid.jsonl (English/ of the dataset).
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

SET = "CS-Bench"
SOURCE = "CS-Bench"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/csbench_set_aside.json")
MAX_FILL = 80  # characters in a fill-in answer
MIN_SOLUTION = 150  # characters in a stored explanation
WITHIN = 0.85  # share of 5-word shingles that makes two CS-Bench rows the same question

_FIXES_FILE = Path(__file__).with_name("csbench_fixes.json")
_FIXES = (
    json.loads(_FIXES_FILE.read_text(encoding="utf-8"))
    if _FIXES_FILE.exists()
    else {"fixes": [], "dropped": {}}
)
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPS: dict[str, str] = dict(_FIXES["dropped"])

ROMAN = {"Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV", "Ⅴ": "V", "Ⅵ": "VI", "Ⅶ": "VII", "Ⅷ": "VIII"}
SUPER = {c: f"^{i}" for i, c in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹")}
CIRCLED = {c: f"({i})" for i, c in enumerate("①②③④⑤⑥⑦⑧⑨⑩", 1)}
SYMBOLS = {
    "→": r"\rightarrow",
    "×": r"\times",
    "·": r"\cdot",
    "μ": r"\mu",
    "µ": r"\mu",
    "≤": r"\leq",
    "≥": r"\geq",
    "≈": r"\approx",
    "≠": r"\neq",
    "∈": r"\in",
    "⊆": r"\subseteq",
    "⊕": r"\oplus",
    "α": r"\alpha",
    "β": r"\beta",
    "°": r"^{\circ}",
    "⌈": r"\lceil",
    "⌉": r"\rceil",
    "⌊": r"\lfloor",
    "⌋": r"\rfloor",
    "…": r"\ldots",
    "∞": r"\infty",
    "|": r"|",
    "<": r"<",
    ">": r">",
}
ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
BLANK_RE = re.compile(r"\(\s*\)|（\s*）")
CODE_LINE_RE = re.compile(
    r"[;{}]\s*$|^\s{2,}\S|^\s*(?:int|void|char|float|double|while|for|if|else|return|struct|typedef)\b[^.?]*[({;=]"
)
FIGURE_RE = re.compile(
    r"\bfigure\b|\bfig\.|\bas shown\b|\bshown (?:in|below|above)\b|\bthe (?:table|graph) (?:below|above)\b"
    r"|\bfollowing (?:table|graph|diagram|picture|figure)\b|\bgiven (?:graph|tree|figure)\b",
    re.I,
)
PROGRAM_RE = re.compile(
    r"\b(?:write|design|implement|develop|devise|construct|give|provide|describe)\b[^.?]{0,60}"
    r"\b(?:program|algorithm|function|code|pseudocode|pseudo-code|procedure|subroutine|C language|C\+\+)\b"
    r"|\bin C language\b|\bpseudo-?code\b|\bwrite (?:a|the) \w+ (?:function|program|code)\b",
    re.I,
)


def tidy_plain(text: str) -> str:
    """Characters that are not LaTeX in the dataset's plain text, minus the math."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ").replace("\\n", "\n")
    for k, v in ROMAN.items():
        text = text.replace(k, v + "")  # marks a converted numeral
    text = re.sub(r"\s*[、，,]\s*(?=[IVX])", ", ", text)
    text = re.sub(r"(?=[a-z])", " ", text).replace("", "")
    text = text.replace("、", ", ").replace("，", ", ").replace("；", "; ").replace("：", ": ")
    text = text.replace("（", "(").replace("）", ")")
    for k, v in CIRCLED.items():
        text = text.replace(k, v + " ")
    for k, v in SUPER.items():
        text = text.replace(k, v)
    text = text.replace("—", "---").replace("–", "--")
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return text


def texify(text: str, *, blank: bool = False) -> str:
    """Plain text of the dataset -> LaTeX text (paragraphs from line ends, math for the math-like bits)."""
    text = tidy_plain(text)
    stash: list[str] = []

    def put(m: str) -> str:
        stash.append(m)
        return "\ue000" + chr(0xE100 + len(stash) - 1) + "\ue001"

    # sets in braces, {00,01,10}: one math group
    text = re.sub(
        r"\{([^{}\n]{1,80})\}",
        lambda m: put("$\\{" + m.group(1).replace("%", r"\%") + "\\}$"),
        text,
    )
    text = re.sub(r"log([₂₁₀])", lambda m: put(r"$\log_{" + str("₀₁₂".index(m.group(1))) + "}$"), text)
    text = re.sub(r"[₀₁₂₃₄₅₆₇₈₉]", lambda m: put("$_{" + str("₀₁₂₃₄₅₆₇₈₉".index(m.group(0))) + "}$"), text)
    text = text.replace("∛", "\ue002")  # cube root, argument follows
    text = re.sub(r"\ue002(\w+|\([^()]*\))", lambda m: put("$\\sqrt[3]{" + m.group(1).strip("()") + "}$"), text)
    text = re.sub(r"√(\w+|\([^()]*\))", lambda m: put("$\\sqrt{" + m.group(1).strip("()") + "}$"), text)
    # 2x10^5, 125x8: a multiplication sign (not hex 0x1F)
    text = re.sub(
        r"(?<![\w.])([1-9]\d*(?:\.\d+)?)\s?x\s?(?=\d)", lambda m: m.group(1) + put(r"$\times$"), text
    )
    # powers and indices: n^2, 2^(n-1), P_1, a_i,j (single-letter bases only for "_": List_Insert stays text)
    pow_re = re.compile(
        r"(?<![\w\\])(\d+(?:\.\d+)?|[A-Za-z]|\([^()\n]{1,20}\))\^(\([^()\n]{1,20}\)|-?[A-Za-z0-9]+)(?!\w)"
    )
    text = pow_re.sub(
        lambda m: put(f"${m.group(1)}^{{{m.group(2).strip('()') if m.group(2).startswith('(') else m.group(2)}}}$"),
        text,
    )
    text = re.sub(
        r"(?<![\w\\])([A-Za-z])_([A-Za-z0-9]),([A-Za-z0-9])(?!\w)",
        lambda m: put(f"${m.group(1)}_{{{m.group(2)},{m.group(3)}}}$"),
        text,
    )
    text = re.sub(
        r"(?<![\w\\])([A-Za-z])_([A-Za-z0-9]{1,2})(?![\w])",
        lambda m: put(f"${m.group(1)}_{{{m.group(2)}}}$"),
        text,
    )
    for old, new in (("<=", r"\leq"), (">=", r"\geq"), ("!=", r"\neq"), ("->", r"\rightarrow")):
        text = text.replace(old, "\ue003" + chr(0xE100 + len(stash)) + "\ue001")
        if "\ue003" in text:
            idx = len(stash)
            stash.append(f"${new}$")
            text = text.replace("\ue003" + chr(0xE100 + idx), "\ue000" + chr(0xE100 + idx))
    text = re.sub(
        "[" + "".join(re.escape(c) for c in SYMBOLS if c not in "|<>") + "]",
        lambda m: put(f"${SYMBOLS[m.group(0)]}$"),
        text,
    )
    text = re.sub(r"[<>|]", lambda m: put(f"${m.group(0)}$"), text)
    text = re.sub(r'"([^"\n]+)"', lambda m: "``" + m.group(1) + "''", text)
    text = "".join(ESCAPES.get(c, c) for c in text)
    if blank:
        text = BLANK_RE.sub(r"\\underline{\\hspace{2.5em}}", text)
    text = re.sub(r"\ue000(.)\ue001", lambda m: stash[ord(m.group(1)) - 0xE100], text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n+", "\n\n", text)
    return text.strip()


def with_code(text: str, *, blank: bool = False) -> str:
    """texify, except that runs of source-code lines go into a verbatim block."""
    lines = tidy_plain(text).split("\n")
    flags = [bool(CODE_LINE_RE.search(x)) and not re.match(r"\s*(?:[IVX]+\.|\(\d+\))", x) for x in lines]
    out, i = [], 0
    while i < len(lines):
        if flags[i] and (i + 1 < len(lines) and flags[i + 1]):
            j = i
            while j < len(lines) and (flags[j] or not lines[j].strip()):
                j += 1
            while not lines[j - 1].strip():
                j -= 1
            out.append("\x00" + "\n".join(lines[i:j]) + "\x00")
            i = j
        else:
            out.append(lines[i])
            i += 1
    parts = "\n".join(out).split("\x00")
    res = []
    for k, p in enumerate(parts):
        if k % 2:
            res.append("\\begin{verbatim}\n" + p.rstrip() + "\n\\end{verbatim}")
        elif p.strip():
            res.append(texify(p, blank=blank))
    return "\n\n".join(res)


def apply_fixes(key: str, r: dict) -> dict:
    r = dict(r)
    for (k, fld), pairs in HAND_FIXES.items():
        if k != key:
            continue
        for old, new in pairs:
            if not isinstance(r.get(fld), str) or r[fld].count(old) != 1:
                raise SystemExit(f"HAND FIX {key} {fld}: expected one {old!r}")
            r[fld] = r[fld].replace(old, new)
    return r


def plain_key(r: dict) -> str:
    return re.sub(r"[^a-z0-9]+", " ", " ".join(str(r.get(k) or "") for k in ("Question", "A", "B", "C", "D")).lower()).strip()


def statement(r: dict) -> str:
    q = r["Question"].strip()
    fmt = r["Format"]
    if fmt == "Multiple-choice":
        stem = with_code(q)
        low = stem.lower()
        note = [] if ("exactly one" in low or "only one" in low) else ["Exactly one option is correct."]
        opts = [f"({x}) {texify(str(r[x]))}" for x in "ABCD"]
        return "\n\n".join([stem, *note, *opts])
    if fmt == "Assertion":
        q = re.sub(r"\s*\(\s*\)\s*$", "", q)
        return "Is the following assertion true or false?\n\n" + with_code(q)
    return with_code(q, blank=fmt == "Fill-in-the-blank")


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    raw, dropped, rows = [], {}, []
    for name in ("test", "valid"):
        for line in (data / f"{name}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            r["_file"] = name
            raw.append(r)
    seen: dict[str, str] = {}
    sh: list[tuple[str, set]] = []
    for r in raw:
        key = f"{SET} {r['ID']}"
        if key in DROPS:
            dropped[key] = DROPS[key]
            continue
        r = apply_fixes(key, r)
        fmt, q = r["Format"], r["Question"]
        if re.search(r"[\u4e00-\u9fff]", " ".join(str(v) for v in r.values())):
            dropped[key] = "Chinese text"
            continue
        if fmt == "Multiple-choice" and not all(r.get(x) for x in "ABCD"):
            dropped[key] = "options missing"
            continue
        if FIGURE_RE.search(q) and not re.search(r"\bnot shown\b", q):
            dropped[key] = "needs a figure or table that is not provided"
            continue
        if fmt in ("Open-ended", "Fill-in-the-blank") and PROGRAM_RE.search(q) and "complexity" not in q:
            dropped[key] = "write-a-program / design-an-algorithm task"
            continue
        k = plain_key(r)
        if k in seen:
            dropped[key] = f"same question as {seen[k]}"
            continue
        sig = shingles(k)
        twin = None if fmt == "Open-ended" else next((o for o, s in sh if len(sig & s) / max(len(sig), 1) >= WITHIN and len(sig) > 6), None)
        if twin:
            dropped[key] = f"near-duplicate of {twin}"
            continue
        seen[k] = key
        sh.append((key, sig))
        ans = r.get("Answer")
        expl = (r.get("Explanation") or "").strip()
        if fmt == "Multiple-choice":
            if ans not in list("ABCD"):
                dropped[key] = "no valid key"
                continue
            answer = ans
        elif fmt == "Assertion":
            if not isinstance(ans, bool):
                dropped[key] = "no valid key"
                continue
            answer = "True" if ans else "False"
        elif fmt == "Fill-in-the-blank":
            a = str(ans).strip().rstrip(".")
            if not a or len(a) > MAX_FILL or "\n" in a:
                dropped[key] = "fill-in answer too long"
                continue
            if len(BLANK_RE.findall(q)) > 1:
                dropped[key] = "several blanks"
                continue
            answer = texify(a)
        elif fmt == "Open-ended":
            answer = None
            if not str(ans or "").strip():
                dropped[key] = "no reference answer"
                continue
            asig = shingles(re.sub(r"[^a-z0-9]+", " ", str(ans).lower()))
            if len(asig) > 15 and len(asig & shingles(plain_key(r))) / len(asig) >= 0.5:
                dropped[key] = "the statement already contains the answer"
                continue
        else:
            dropped[key] = f"format {fmt}"
            continue
        ref = texify(expl) if expl else ""
        sol = ref if len(ref) >= MIN_SOLUTION and fmt != "Open-ended" else None
        if fmt == "Open-ended":
            ref = with_code(str(ans))
        rows.append(
            {
                "potd": key,
                "set": SET,
                "idx": str(r["ID"]),
                "orig": f"{r['Domain']}; {r['SubDomain']}; {fmt}; {r.get('Tag', '')}; {r['_file']}",
                "source": SOURCE,
                "subsource": "",
                "latexcode": statement(r),
                "answer": answer,
                "solution": sol,
                "hints": None,
                "more_hints": None,
                "ref_solution": ref,
                "group": "subject",
                "effort": None,
                "image": None,
                "_format": fmt,
                "_domain": r["Domain"],
            }
        )
    return rows, dropped


def public(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of render failures")
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
    problems = check(public(new))
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {
            r["potd"]: check(public([r])) or [excluded[r["potd"]]]
            for r in new
            if check(public([r])) or r["potd"] in excluded
        }
        SET_ASIDE_PATH.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in public(new) if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(public(new))
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
                "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
                "by_domain_format": collections.Counter(f"{r['_domain']} / {r['_format']}" for r in new),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(public(new), ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("csbench")
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in public(new):
            h = latex_hash(r["latexcode"])
            if h in existing:
                continue
            cur = conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, hints, more_hints, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    UNCATEGORIZED,
                    UNCATEGORIZED,
                    UNCATEGORIZED,
                    r["latexcode"],
                    r["source"],
                    r["subsource"],
                    r["answer"],
                    r["solution"],
                    r["hints"],
                    r["more_hints"],
                    h,
                ),
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
        {
            str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
            for q, r in added
            if r["ref_solution"]
        }
    )
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
