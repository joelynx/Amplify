"""
Import UGPhysics (English half)
-------------------------------
UGPhysics (github.com/YangLabHKUST/UGPhysics, huggingface.co/datasets/UGPhysics/ugphysics, CC BY-NC-SA
4.0; Amplify is private): 5,520 undergraduate physics problems in 13 subjects, translated from Chinese
textbooks, each with a final answer (in \\boxed{}), a unit field and, for most, a worked solution.
The Chinese files are exact twins of the English ones and are not read.

Rows (owner decisions of 2026-11-22): every English row is kept except the duplicate pair Relativity
974/995, the rows that need a figure or table the dataset does not ship, rows whose multiple-choice options
are cut off, and the one row without a boxed answer (UGPHYSICS_DROPS below and ugphysics_fixes.json). All rows
go to group "subject": the subjects solver picks them up after classification (Atomic Physics, Optics,
Semiconductor and Solid-State Physics included).

Source "UGPhysics", subsource "<Subject>, <topic>, problem <index>". The dataset's solution is stored in
`solution` when it is a real derivation (at least 150 characters after the "<image N>" placeholders
are removed), else the solver writes one; either way it is kept in ref_solution
(app/data/appdata/benchmarks_solutions.json).

Conversions:
  * Answer key: the content of \\boxed{...}; several answers as "(1) ...; (2) ..." (when the statement has
    numbered parts) or "a, b" (a list), each with its unit from the `unit` field; multiple choice as capital
    letters ("B" or "A, B, D"); true/false as "True"/"False", or "Yes"/"No" as the dataset gives them.
    Anything with LaTeX is wrapped in $...$, plain numbers stay plain.
  * Multiple choice: options each on a line of their own as "(A) ...", after a blank line, and "Exactly one
    option is correct." / "One or more options may be correct." when the key has one / several letters.
  * $$ ... $$ becomes \\[ ... \\]; a bare % is escaped; "<image N>" placeholders leave the solutions;
    Markdown-style line ends and trailing spaces go.
  * Per-row repairs and drops live in ugphysics_fixes.json (same shape as answer_sets_fixes.json).

Rows the bank already has (same latex_hash or 85% of 5-word shingles) are skipped and listed.
On --apply: backup, insert (topic/branch/subtopic Uncategorized), append to benchmarks_map.csv, keep
ref_solution in benchmarks_solutions.json. Nothing goes into benchmarks_assignments.json (subject rows).

Usage (repo root):
  python -m app.tools.import_ugphysics --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_ugphysics --data DIR --apply
DIR holds <Subject>/en.jsonl for the 13 subjects.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "UGPhysics"
SOURCE = "UGPhysics"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/ugphysics_set_aside.json")
MIN_SOLUTION = 150  # characters, "<image N>" placeholders removed

_FIXES = json.loads(Path(__file__).with_name("ugphysics_fixes.json").read_text(encoding="utf-8"))
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
UGPHYSICS_DROPS: dict[str, str] = dict(_FIXES["dropped"])
SOLUTION_DROPS: dict[str, str] = dict(
    _FIXES.get("solution_dropped", {})
)  # rows whose own solution is not stored

IMAGE_RE = re.compile(r"[ \t]*<image\s*\d*>[ \t]*")
DISPLAY_RE = re.compile(r"\$\$(.*?)\$\$", re.S)
OWN_DISPLAY = "align|align\\*|gather|gather\\*|equation|equation\\*|multline|multline\\*|eqnarray|eqnarray\\*|flalign|flalign\\*|center|tabular|table|itemize|enumerate"
WRAPPED_RE = re.compile(r"\\\[\s*(\\begin\{(" + OWN_DISPLAY + r")\}.*?\\end\{\2\})\s*\\\]", re.S)
OPT_RE = re.compile(r"\(([A-Ha-h])\)")
NUMBER_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")
NO_UNIT = {
    "",
    "None",
    r"\None",
    r"\text{None}",
    r"\text{ (normalized eigenvectors)}",
    r"\text{ (eigenvalues)}",
    r"\sqrt{\frac{kg \cdot m}{1}}",
    r"\text{}",
    r"\mathrm{None}",
    r"\mathrm{}",
    r"\text{ None}",
}
PART_RE = re.compile(r"(?:^|\n)\s*(?:\(\s*(\d+|[ivx]+|[a-z])\s*\)|(\d+)[.)])\s", re.I)


def label(subject: str, index: int) -> str:
    return f"{SET} {subject} {index}"


def split_top(s: str, sep: str = ",") -> list[str]:
    """Split at separators outside braces, brackets, parentheses and $...$."""
    out, depth, cur, math, k = [], 0, [], False, 0
    while k < len(s):
        c = s[k]
        if c == "\\" and k + 1 < len(s):
            two = s[k : k + 2]
            if two in ("\\(", "\\["):
                depth += 1
            elif two in ("\\)", "\\]"):
                depth -= 1
            cur.append(two)
            k += 2
            continue
        if c == "$":
            math = not math
        elif not math:
            if c in "{[(":
                depth += 1
            elif c in "}])":
                depth -= 1
        if c == sep and depth == 0 and not math:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        k += 1
    out.append("".join(cur))
    return [p.strip() for p in out]


def boxed(text: str) -> str | None:
    """Content of the last \\boxed{...} in text (nested braces), None when there is none."""
    k = text.rfind("\\boxed")
    if k < 0:
        return None
    k = text.find("{", k)
    if k < 0:
        return None
    depth, i = 0, k
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        depth += {"{": 1, "}": -1}.get(c, 0)
        if depth == 0:
            return text[k + 1 : i].strip()
        i += 1
    return None


EMPTY_TEXT_RE = re.compile(r"\\(?:text|mathrm)\{\s*\}")
MOJIBAKE_RE = re.compile("[\u00c2-\u00f4][\u0080-\u00bf]+")
MATH_RE = re.compile(
    r"(\$\$.*?\$\$|\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\]|\\begin\{(?:"
    + OWN_DISPLAY
    + r")\}.*?\\end\{(?:"
    + OWN_DISPLAY
    + r")\})",
    re.S,
)
SYMBOLS = {
    "\u00b1": r"\pm",
    "\u00d7": r"\times",
    "\u00b0": r"^{\circ}",
    "\u00b2": "^{2}",
    "\u00b3": "^{3}",
    "\u00b9": "^{1}",
    "\u00b7": r"\cdot",
    "\u03b4": r"\delta",
    "\u0394": r"\Delta",
    "\u03bc": r"\mu",
    "\u03bb": r"\lambda",
    "\u03c0": r"\pi",
    "\u03b6": r"\zeta",
    "\u03b1": r"\alpha",
    "\u03b2": r"\beta",
    "\u03b8": r"\theta",
    "\u03c9": r"\omega",
    "\u2212": "-",
    "\u2248": r"\approx",
    "\u2264": r"\leq",
    "\u2265": r"\geq",
}
SYMBOL_RE = re.compile("[" + "".join(SYMBOLS) + "]")
TYPOGRAPHY = {
    "\u2018": "`",
    "\u201c": "``",
    "\u201d": "''",
    "\uff1b": ";",
    "\uff0c": ",",
    "\u2026": "\\ldots{}",
}


def demojibake(m: re.Match) -> str:
    try:
        return m.group(0).encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return m.group(0)


def symbols(text: str) -> str:
    """Unicode math symbols to LaTeX commands: inside math as they are, in running text wrapped in $...$."""
    parts = MATH_RE.split(text)
    for i, p in enumerate(parts):
        if i % 2:
            parts[i] = SYMBOL_RE.sub(lambda m: SYMBOLS[m.group(0)] + " ", p)
        else:
            parts[i] = SYMBOL_RE.sub(lambda m: "$" + SYMBOLS[m.group(0)] + "$", p)
        parts[i] = "".join(TYPOGRAPHY.get(c, c) for c in parts[i])
    return "".join(parts)


# Commands neither KaTeX nor the app's preamble has, and what stands in for them
MACRO_FIXES = [
    (r"\\mathscr(?![A-Za-z])", r"\\mathcal"),
    (r"\\wideparen(?![A-Za-z])", r"\\widehat"),
    (r"\\xlongequal\s*\{([^{}]*)\}", r"\\overset{\1}{=}"),
    (r"\\oiint(?![A-Za-z])", r"\\oint"),
    (r"\\mathrm\{\\angstrom\}|\\angstrom(?![A-Za-z])", r"\\text{\\AA}"),
    (r"\\degree(?![A-Za-z])", r"^{\\circ}"),
    (r"\\multirow\{\d+\}\{[^{}]*\}\{([^{}]*)\}", r"\1"),
    (r"\s*\(?\\autoref\s*\{[^{}]*\}\)?", ""),
]
TAG_RE = re.compile(r"\\tag\*?\{([^{}]*)\}")
DISPLAY_BLOCK_RE = re.compile(
    r"\\\[.*?\\\]|\\begin\{(align|gather|equation|multline|eqnarray|flalign)\*?\}.*?\\end\{\1\*?\}",
    re.S,
)
NESTED_RE = re.compile(r"\\begin\{(?:aligned|gathered|array|cases|split)\}")


def markup_fixes(text: str) -> str:
    for pat, new in MACRO_FIXES:
        text = re.sub(pat, new, text)

    def untag(
        m: re.Match,
    ) -> str:  # \tag is not allowed inside aligned/gathered and only once per display
        b = m.group(0)
        if "\\tag" in b and (b.count("\\tag") > 1 or NESTED_RE.search(b)):
            return TAG_RE.sub(r"\\qquad(\1)", b)
        return b

    return DISPLAY_BLOCK_RE.sub(untag, text)


def tidy(text: str) -> str:
    """Common clean-up of every text field."""
    text = MOJIBAKE_RE.sub(demojibake, text)  # a few statements went through a wrong text encoding
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(
        r"\\(?:text|mathrm)\{\s*\}", r"\\text{\\AA}", text
    )  # the dataset lost its Angstrom signs
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = symbols(text)
    text = DISPLAY_RE.sub(lambda m: "\\[\n" + m.group(1).strip() + "\n\\]", text)
    text = re.sub(r"\\\[\s*\\\]", "", text)  # an empty display (a figure that was cut out)
    text = WRAPPED_RE.sub(
        lambda m: m.group(1), text
    )  # an environment that brings its own display math
    text = re.sub(r"(?<!\\)%", r"\\%", text)  # a bare % comments out the rest of the line in TeX
    while text.count("\\end{center}") > text.count(
        "\\begin{center}"
    ):  # a stray \end{center} from the translation
        k = text.rfind("\\end{center}")
        text = text[:k] + text[k + len("\\end{center}") :]
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return markup_fixes(text).strip()


def unbreak(t: str) -> str:
    """Drop the \\ line breaks the translation left at the end of a stem or an option."""
    return re.sub(r"(?:\s*\\{1,2})+\s*$", "", t.strip()).strip()  # "\\" or a lone "\" at the end


def options(stem: str):
    """(stem, [(letter, text)]) for a statement whose options are inline; None when the options are broken."""
    marks = [(m.start(), m.end(), m.group(1).upper()) for m in OPT_RE.finditer(stem)]
    for i in range(len(marks) - 1, -1, -1):  # the last (A) that starts an A, B, C... run
        if marks[i][2] != "A":
            continue
        run, want = [marks[i]], "B"
        for m in marks[i + 1 :]:
            if m[2] == want:
                run.append(m)
                want = chr(ord(want) + 1)
        if len(run) >= 2:
            opts = []
            for j, m in enumerate(run):
                end = run[j + 1][0] if j + 1 < len(run) else len(stem)
                opts.append((m[2], unbreak(stem[m[1] : end])))
            return unbreak(stem[: run[0][0]]), opts
    return None


def mc_statement(stem: str, letters: list[str]) -> str | None:
    got = options(stem)
    if not got or any(not t for _, t in got[1]) or not set(letters) <= {x for x, _ in got[1]}:
        return None
    head, opts = got
    last = re.split(
        r"\n\s*\n", opts[-1][1], maxsplit=1
    )  # text after the last option belongs to the statement
    if len(last) == 2 and last[0].count("\\[") == last[0].count("\\]"):
        opts[-1] = (opts[-1][0], last[0].strip())
        tail = last[1].strip()
        if not re.fullmatch(
            r"(?:please\s+)?(?:choose|select|pick)\b[^.\n]*\.?", tail, re.I
        ):  # a bare instruction goes
            head = head + "\n\n" + tail
    note = ""
    low = head.lower()
    if (
        len(letters) == 1
        and "exactly one" not in low
        and "one or more" not in low
        and "only one" not in low
    ):
        note = "Exactly one option is correct."
    elif len(letters) > 1 and "one or more" not in low and "multiple" not in low:
        note = "One or more options may be correct."
    parts = [head] + ([note] if note else []) + [f"({x}) {t}" for x, t in opts]
    return "\n\n".join(p for p in parts if p)


def unit_latex(u: str) -> str:
    u = u.strip()
    u = re.sub(r"\\text\{([^{}\\ ]*)\}", r"\\mathrm{\1}", u)
    return u


def piece(content: str, unit: str, kind: str, stem: str) -> str:
    """One answer, formatted: letters, True/False, plain number, or $...$ with the unit."""
    c = content.strip()
    c = re.sub(r"^\\text\{(.*)\}$", r"\1", c) if re.fullmatch(r"\\text\{[^{}]*\}", c) else c
    if kind == "MC" and re.fullmatch(r"[A-Ha-h]", c):
        return c.upper()
    if kind == "TF" or c in ("Yes", "No", "True", "False", "yes", "no", "true", "false"):
        w = c.strip().capitalize()
        if w in ("Yes", "No", "True", "False"):
            if w in ("Yes", "No") and re.search(r"true\s+or\s+false|true/false", stem, re.I):
                return "True" if w == "Yes" else "False"
            return w
    u = "" if unit in NO_UNIT else unit_latex(unit)
    if u and (u in c or re.search(r"\\(?:mathrm|text)\{[A-Za-z/%]*\}\s*$", c)):
        u = ""  # the answer already carries a unit
    if not u and NUMBER_RE.match(c):
        return c
    if u:
        c = f"{c}\\ {u}"
    if c.startswith("$") and c.endswith("$"):
        return c
    return f"${c}$"


def answer_key(r: dict, stem: str) -> str | None:
    content = boxed(r["answers"])
    if content is None or not content.strip():
        return None
    content = MOJIBAKE_RE.sub(demojibake, content)
    kinds = [k.strip() for k in re.split(r"[,\n]", r["answer_type"].strip().split("\n")[0])]
    units = MOJIBAKE_RE.sub(demojibake, r["unit"]) if isinstance(r["unit"], str) else ""
    if EMPTY_TEXT_RE.search(
        units
    ):  # the dataset lost the unit; its wavelengths and lengths in Angstrom are recognisable
        if not re.search(
            r"wavelength|angstrom|Å|Ã\x85|\\AA|" + EMPTY_TEXT_RE.pattern, r["problem"], re.I
        ):
            raise ValueError("unit lost in the dataset (empty \\text{})")
        units = EMPTY_TEXT_RE.sub(lambda m: "\\text{\\AA}", units)
    ulist = []
    for u in split_top(units) if units else []:
        inner = re.fullmatch(
            r"\\(text|mathrm)\{([^{}]*,[^{}]*)\}", u
        )  # "\text{None, MeV}": one unit per piece
        ulist += (
            [f"\\{inner.group(1)}{{{x.strip()}}}" for x in inner.group(2).split(",")]
            if inner
            else [u]
        )
    if kinds == ["MC"] or (kinds[0] in ("MC", "TF") and len(kinds) == 1):
        letters = (
            re.findall(r"[A-Ha-h]", content)
            if re.fullmatch(r"[A-Ha-h](?:\s*[,;&]?\s*(?:and\s+)?[A-Ha-h])*", content)
            else None
        )
        if letters:
            return ", ".join(sorted({x.upper() for x in letters}))
    pieces = split_top(content) if r["is_multiple_answer"] or len(kinds) > 1 else [content]
    if len(ulist) not in (len(pieces), 1) or len(kinds) not in (len(pieces), 1):
        pieces, ulist, kinds = (
            [content],
            [ulist[0]] if len(ulist) == 1 else [],
            [kinds[0]] if len(kinds) == 1 else [""],
        )
    if len(ulist) == 1 and len(pieces) > 1:
        ulist = ulist * len(pieces)
    if len(kinds) == 1:
        kinds = kinds * len(pieces)
    ulist = ulist or [""] * len(pieces)
    out = [piece(p, u, k, stem) for p, u, k in zip(pieces, ulist, kinds, strict=True)]
    if len(out) == 1:
        return out[0]
    nparts = len({(m.group(1) or m.group(2)).lower() for m in PART_RE.finditer(stem)})
    picks = all(
        t.isdigit() and 1 <= int(t) <= nparts for t in out
    )  # "1, 2": items picked from the statement
    if nparts == len(out) and not picks:  # one answer per numbered part
        return "; ".join(f"({i}) {t}" for i, t in enumerate(out, 1))
    return ("; " if nparts >= 2 else ", ").join(out)


def solution_text(r: dict) -> tuple[str, str | None]:
    """(reference solution, solution to store or None)."""
    raw = IMAGE_RE.sub(" ", r["solution"] or "")
    sol = tidy(raw)
    return sol, (sol if len(sol) >= MIN_SOLUTION else None)


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    rows, dropped = [], {}
    seen = {}
    for sub in sorted(p for p in data.iterdir() if p.is_dir()):
        for line in (sub / "en.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            key = label(sub.name, r["index"])
            if key in UGPHYSICS_DROPS:
                dropped[key] = UGPHYSICS_DROPS[key]
                continue
            stem = tidy(r["problem"])
            if key in HAND_FIXES.keys() | {(k, "x") for k in ()}:
                pass
            ans = r["answers"]
            if boxed(ans) is None:
                dropped[key] = "no boxed answer in the dataset"
                continue
            kinds = r["answer_type"].strip()
            letters = None
            c = boxed(ans)
            if kinds.startswith("MC") and re.fullmatch(
                r"[A-Ha-h](?:\s*[,;&]?\s*(?:and\s+)?[A-Ha-h])*", c
            ):
                letters = [x.upper() for x in re.findall(r"[A-Ha-h]", c)]
                new = mc_statement(stem, letters)
                if new is None:
                    dropped[key] = "multiple-choice options cut off or missing"
                    continue
                stem = new
            ref, sol = solution_text(r)
            if (
                key in SOLUTION_DROPS
            ):  # the translated solution's TeX is broken: the solver writes one instead
                sol = None
            row = {
                "potd": key,
                "set": SET,
                "idx": str(r["index"]),
                "orig": "",
                "source": SOURCE,
                "subsource": f"{r['subject']}, {r['topic']}, problem {r['index']}",
                "latexcode": stem,
                "answer": "",
                "solution": sol,
                "hints": None,
                "more_hints": None,
                "ref_solution": ref,
                "group": "subject",
                "effort": None,
                "image": None,
            }
            try:
                row["answer"] = markup_fixes(symbols(answer_key(r, stem) or ""))
            except ValueError as e:
                dropped[key] = str(e)
                continue
            for fld in ("latexcode", "answer", "solution", "ref_solution"):
                for old, new in HAND_FIXES.get((key, fld), []):
                    if row[fld] is None or row[fld].count(old) != 1:
                        raise SystemExit(f"HAND FIX {key} {fld}: expected one {old!r}")
                    row[fld] = row[fld].replace(old, new)
            if key in HAND_FIXES and ((key, "solution") in HAND_FIXES):
                row["ref_solution"] = row["solution"] or row["ref_solution"]
            if not row["answer"]:
                dropped[key] = "no usable answer"
                continue
            # the same problem twice in the dataset: keep one
            if stem in seen:
                dropped[key] = f"same statement as {seen[stem]}"
                continue
            seen[stem] = key
            rows.append(row)
    # the dataset attaches one solution to many unrelated problems (e.g. a Brewster-angle solution on 87 wave-optics
    # problems): a solution text shared by several rows is not stored for any of them; the solver writes their own
    shared = collections.Counter(r["ref_solution"].strip() for r in rows if r["ref_solution"].strip())
    for r in rows:
        if shared[r["ref_solution"].strip()] > 1:
            r["solution"], r["ref_solution"] = None, ""
    return rows, dropped


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument(
        "--set-aside",
        action="store_true",
        help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)",
    )
    p.add_argument(
        "--exclude",
        type=Path,
        help="with --set-aside: JSON {row label: why} of rows the render checks failed",
    )
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
        why = {
            r["potd"]: check([r]) or [excluded[r["potd"]]]
            for r in new
            if check([r]) or r["potd"] in excluded
        }
        SET_ASIDE_PATH.write_text(
            json.dumps(
                [dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why],
                ensure_ascii=False,
                indent=1,
            ),
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
                "with_stored_solution": sum(bool(r["solution"]) for r in new),
                "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
                "by_subject": collections.Counter(r["subsource"].split(",")[0] for r in new),
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
    backup_db("ugphysics")
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
    solutions = (
        json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    )
    solutions.update(
        {
            str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
            for q, r in added
            if r["ref_solution"]
        }
    )
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}"
    )


if __name__ == "__main__":
    main()
