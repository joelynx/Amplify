"""
Import communication-engineering problem sets
---------------------------------------------
Two Hugging Face datasets (read from parquet / JSON lines, nothing in them is run):

  telemath  TeleMath (ymoslem/TeleMath-processed copy of netop/TeleMath, MIT; train 299 + test 201 = 500): numeric
            problems in telecommunications, signal processing, information theory, networking, probability and
            statistics, operations research. The key is a number, the statement carries the units.
  wmb       WirelessMathBench (XINLI1997/WirelessMathBench, CC BY 4.0; 587): research-paper equations (MIMO, RIS,
            ISAC, ...) with one part masked, as multiple choice (125) or fill-the-equation (462). The masked part
            is shown as a box in the displayed equation.

Owner decision of 2026-11-25 (asleep; "import as many sources as possible"): group "subject" for the classifier;
Source = dataset name; subsource = the category (TeleMath) or the research area and item kind (WirelessMathBench),
no ids in the text. The TheoremQA signal-processing / information-theory rows are not here: import_theoremqa_leftovers
already covers them (nearly all are in the bank).

TeleMath statements are a mix of LaTeX and plain text ("lambda", "10^5", "p_x(0)", "{yn}"); prose_math() wraps the
plain-text math in $...$ and rows with undelimited LaTeX it cannot repair are dropped. Keys are rounded to 6
significant figures. WirelessMathBench: [MASK] becomes a box; the key is the boxed answer without \\boxed.

Usage (repo root):
  python -m app.tools.import_comms --data DIR --dry-run [--only telemath|wmb] [--dump rows.json]
                                    [--set-aside [--exclude failures.json]]
  python -m app.tools.import_comms --data DIR --apply [--only ...]
DIR holds telemath/{train,test}.parquet and wmb/WirelessMathBench.json.
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

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SET_ASIDE_PATH = Path("app/data/appdata/comms_set_aside.json")
SETS = {"telemath": "TeleMath", "wmb": "WirelessMathBench"}

GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "varepsilon", "ζ": "zeta", "η": "eta",
    "θ": "theta", "λ": "lambda", "µ": "mu", "μ": "mu", "ν": "nu", "ξ": "xi", "π": "pi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "φ": "varphi", "ω": "omega", "Γ": "Gamma", "Δ": "Delta", "Λ": "Lambda",
    "Σ": "Sigma", "Φ": "Phi", "Ω": "Omega",
}  # fmt: skip
SYMBOLS = {
    "≥": r"\geq ", "≤": r"\leq ", "∈": r"\in ", "∞": r"\infty ", "±": r"\pm ", "·": r"\cdot ", "×": r"\times ",
    "→": r"\to ", "≈": r"\approx ", "≠": r"\neq ", "²": "^{2}", "³": "^{3}", "°": r"^{\circ}", "−": "-",
}  # fmt: skip
G = "".join(GREEK)
GREEK_TOKEN = re.compile(rf"([{G}])([A-Za-z0-9]{{0,3}})(\^\{{?-?[0-9]+\}}?)?")
SCI = re.compile(r"(\d+(?:\.\d+)?)\s*[·x×*]\s*10\^\(?([-−]?\d+)\)?")
POW10 = re.compile(r"(?<![\w^])10\^\(?([-−]?\d+)\)?")
INV_UNIT = re.compile(r"(?<=\s)([A-Za-z]{1,3})−(\d)\b")
SUB = re.compile(r"(?<![A-Za-z\\])([A-Za-z]{1,6})_(\{[^{}]*\}|[A-Za-z0-9]+)")
POW = re.compile(r"(?<![A-Za-z\\])(\d*\.?\d*[A-Za-z]+|\d+(?:\.\d+)?)\^(-?\d+|\{[^{}]*\})")
POWP = re.compile(r"(?<![A-Za-z\\])(\d*[A-Za-z]+)\^\(((?:[^()]|\([^()]*\))*)\)")
BLOCK = re.compile(
    r"(\\[A-Za-z]+\{?[A-Za-z]*\}?(?:_\{?\w*\}?)?\s*=\s*|\b[A-Za-z]\s*=\s*)?\\begin\{(\w+\*?)\}.*?\\end\{\2\}", re.S
)
CONTROL = {"\t": "\\t", "\x08": "\\b", "\x0c": "\\f", "\x07": "\\a", "\x0b": "\\v"}
GREEK_NAMES = {"sigma", "lambda", "mu", "theta", "tau", "rho", "pi", "alpha", "beta", "gamma", "eta", "omega", "phi"}


def sub_token(m: re.Match) -> str:
    base, sub = m[1], m[2]
    b = f"\\{base}" if base in GREEK_NAMES else (base if len(base) == 1 else f"\\mathit{{{base}}}")
    if not sub.startswith("{"):
        sub = f"\\mathrm{{{sub}}}" if len(sub) > 1 and sub.isalpha() and sub.islower() else sub
        sub = "{" + sub + "}"
    return f"{b}_{sub}"
SET_BRACES = re.compile(r"\{([A-Za-z0-9 ,.−-]+)\}")
MATH_RE = re.compile(r"(\\\[.*?\\\]|\$\$.*?\$\$|\$[^$]*\$)", re.S)


def math_text(m: str) -> str:
    """Unicode symbols inside a math segment to LaTeX."""
    m = "".join(f"\\{GREEK[c]} " if c in GREEK else SYMBOLS.get(c, c) for c in m)
    m = re.sub(r"\\(rect|sinc|sgn|triang|tri)(?![A-Za-z])", r"\\operatorname{\1}", m)
    return m.replace("\\upmu", "\\mu").replace("’", "'").replace("ˆ", "").replace("˜", "")


def _sub(s: str) -> str:
    return s if s.startswith("{") else "{" + s + "}"


BARE_CMD = re.compile(
    r"\\[A-Za-z]+(?:\{(?:[^{}]|\{[^{}]*\})*\})*(?:[_^](?:\{(?:[^{}]|\{[^{}]*\})*\}|[A-Za-z0-9]))*"
    r"(?:[_^](?:\{(?:[^{}]|\{[^{}]*\})*\}|[A-Za-z0-9]))*"
)


def prose(x: str) -> str:
    """Plain-text math in a stretch of prose to $...$ (results are stashed so later rules leave them alone)."""
    stash: list[str] = []

    def put(tex: str, display: bool = False) -> str:
        stash.append(f"\\[ {tex} \\]" if display else f"${tex}$")
        return f"\x00{len(stash) - 1}\x00"

    def neg(s: str) -> str:
        return s.replace("−", "-")

    x = x.replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-")
    x = BLOCK.sub(lambda m: put(math_text(m[0]).strip(), display=True), x)
    x = re.sub(r"\\left\s*[\[(|{].*?\\right\s*[\])|}]", lambda m: put(math_text(m[0])), x)
    x = BARE_CMD.sub(lambda m: put(math_text(m[0]).strip()), x)
    x = re.sub(r"(?<![\d.])10−(\d)\b", lambda m: put(f"10^{{-{m[1]}}}"), x)
    x = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)e(-?\d+)\b", lambda m: put(f"{m[1]} \\times 10^{{{m[2]}}}"), x)
    x = re.sub(
        r"(\([^()]*\))\^(-?\w+|\{[^{}]*\})", lambda m: put(f"{math_text(m[1])}^{_sub(m[2])}"), x
    )
    x = SCI.sub(lambda m: put(f"{m[1]} \\cdot 10^{{{neg(m[2])}}}"), x)
    x = POW10.sub(lambda m: put(f"10^{{{neg(m[1])}}}"), x)
    x = INV_UNIT.sub(lambda m: put(f"\\mathrm{{{m[1]}}}^{{-{m[2]}}}"), x)
    x = re.sub(r"(?<=\d)\s*([µμ])(Hz|s|m|F|H|W|V|A|J|g)\b", lambda m: put(rf"\ \mu\mathrm{{{m[2]}}}"), x)
    x = re.sub(r"(?<=\s)([µμ])(Hz|s|m|F|H|W|V|A|J|g)\b", lambda m: put(rf"\mu\mathrm{{{m[2]}}}"), x)

    def greek(m: re.Match) -> str:
        sub = f"_{{{m[2]}}}" if m[2] else ""
        sup = "^{" + m[3][1:].strip("{}") + "}" if m[3] else ""
        return put(f"{math_text(m[1]).strip()}{sub}{sup}")

    x = GREEK_TOKEN.sub(greek, x)
    x = POWP.sub(lambda m: put(f"{m[1]}^{{{math_text(m[2]).strip()}}}"), x)
    x = SUB.sub(lambda m: put(sub_token(m)), x)
    x = POW.sub(lambda m: put(f"{m[1]}^{_sub(m[2])}"), x)
    x = SET_BRACES.sub(lambda m: put("\\{" + math_text(m[1]).replace("-", "{-}") + "\\}"), x)
    for c, v in SYMBOLS.items():
        x = x.replace(c, put(v.strip()))
    x = x.replace("<", put("<")).replace(">", put(">"))
    x = re.sub(r"(?<!\\)%", r"\\%", x)
    x = re.sub(r"(?<!\\)&", r"\\&", x)
    return re.sub("\x00(\\d+)\x00", lambda m: stash[int(m[1])], x)


def equation_line(line: str) -> str:
    """A line that is only an undelimited LaTeX equation becomes a display."""
    if "$" in line or "\\[" in line or "=" not in line or not re.search(r"\\[A-Za-z]", line):
        return line
    words = re.sub(r"\\[A-Za-z]+", "", re.sub(r"\\(?:text|mathrm|operatorname)\{[^{}]*\}", "", line))
    if re.search(r"[A-Za-z]{4,}", words):
        return line
    return f"\\[ {line.strip().rstrip('.,;')} \\]"


def prose_math(text: str) -> str:
    """Statement text: \\( \\) to $ $, symbols fixed in and around the math."""
    text = re.sub(r"[\t\x08\x0c\x07\x0b](?=[A-Za-z])", lambda m: CONTROL[m[0]], text)  # \text, \bigg, \frac eaten by escapes
    text = re.sub(r"^:\s*'(.*)'$", r"\1", text.strip(), flags=re.S)  # a few TeleMath rows are wrapped as ": '...'"
    text = re.sub(r"\$\$(.*?)\$\$", lambda m: f"\\[ {m[1].strip()} \\]", text, flags=re.S)
    text = text.replace("\\(", "$").replace("\\)", "$").replace("\r", "")
    text = "\n".join(equation_line(ln) for ln in text.split("\n"))
    out = []
    for k, part in enumerate(MATH_RE.split(text)):
        out.append(math_text(part) if k % 2 else prose(part))
    return re.sub(r"\$\s*\$", " ", "".join(out)).strip()


def undelimited(text: str) -> bool:
    """True when math is left outside $...$ (a backslash command, ^, _, braces)."""
    rest = "".join(p for k, p in enumerate(MATH_RE.split(text)) if k % 2 == 0)
    return bool(re.search(r"[\\^_{}]", re.sub(r"\\[%&$#]", "", rest)))


def key_number(s: str) -> str:
    s = s.strip()
    try:
        v = float(s)
    except ValueError:
        return s
    t = f"{v:.6g}"
    if "e" in t:
        a, e = t.split("e")
        return f"${a} \\times 10^{{{int(e)}}}$"
    return t


def load_telemath(data: Path) -> tuple[list[dict], dict[str, str]]:
    import pyarrow.parquet as pq

    src = []
    for part in ("train", "test"):
        src += [(part, r) for r in pq.read_table(data / "telemath" / f"{part}.parquet").to_pylist()]
    rows, dropped, seen = [], {}, set()
    for part, r in src:
        label = f"TeleMath {part}-{r['id']}"
        q = prose_math(r["question"])
        if undelimited(q):
            dropped[label] = "math without $ delimiters in the statement"
            continue
        if q in seen:
            dropped[label] = "repeat within TeleMath"
            continue
        seen.add(q)
        rows.append(
            {
                "potd": label,
                "set": "TeleMath",
                "idx": f"{part}-{r['id']}",
                "orig": "",
                "source": "TeleMath",
                "subsource": r["category"],
                "latexcode": q,
                "answer": key_number(r["answer"]),
                "solution": None,
                "hints": None,
                "more_hints": None,
                "ref_solution": "",
                "group": "subject",
                "effort": None,
                "image": None,
                "_kind": r["category"],
            }
        )
    return rows, dropped


def boxed_parts(ans: str) -> list[str]:
    """The contents of the boxed groups of a key made only of such groups joined by 'and' or commas."""
    out, i = [], 0
    while True:
        m = re.search(r"\\boxed\{", ans[i:])
        if not m:
            break
        j = i + m.end()
        depth, k = 1, j
        while k < len(ans) and depth:
            depth += {"{": 1, "}": -1}.get(ans[k], 0)
            k += 1
        if depth:
            return []
        out.append(ans[j : k - 1].strip())
        i = k
    return out


def box_equation(eq: str) -> str:
    return eq.replace("[MASK]", r"\boxed{\;?\;}")


def load_wmb(data: Path) -> tuple[list[dict], dict[str, str]]:
    src = [
        json.loads(line)
        for line in (data / "wmb" / "WirelessMathBench.json").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows, dropped = [], {}
    for r in src:
        label = f"WirelessMathBench {r['id']}"
        mc = r["type"] == "multiple_choice"
        bg = prose_math(r["background"])
        qt = prose_math(r["question_text"])
        eq = r["equation"].strip()
        if "[MASK]" not in eq:
            dropped[label] = "no masked part in the equation"
            continue
        if undelimited(bg) or undelimited(qt):
            dropped[label] = "math without $ delimiters in the background"
            continue
        text = f"{bg}\n\nIn the equation below, the box marks a missing part.\n\n\\[ {box_equation(eq)} \\]\n\n{qt}"
        if mc:
            opts = []
            for o in r["options"]:
                m = re.match(r"^([A-D]):\s*(.*)$", o.strip(), re.S)
                if not m:
                    break
                body = re.sub(r"\s*\\end\{enumerate\}\s*$", "", m[2])  # stray list end in a few options
                opts.append(f"({m[1]}) {prose_math(body)}")
            else:
                text += "\n\n" + "\n\n".join(opts) + "\n\nExactly one option is correct."
                ans = r["correct_answer"].strip()
            if len(opts) != 4:
                dropped[label] = "options not in the A: form"
                continue
        else:
            ans = r["correct_answer"].strip()
            parts = boxed_parts(ans)
            if not parts:
                dropped[label] = "key is not boxed expressions"
                continue
            ans = f"${parts[0]}$" if len(parts) == 1 else "; ".join(f"({i}) ${x}$" for i, x in enumerate(parts, 1))
        rows.append(
            {
                "potd": label,
                "set": "WirelessMathBench",
                "idx": r["id"],
                "orig": r["id"].split("_q")[0],
                "source": "WirelessMathBench",
                "subsource": ", ".join(r["domain"]) + (" (multiple choice)" if mc else " (fill in the equation)"),
                "latexcode": text,
                "answer": ans,
                "solution": None,
                "hints": None,
                "more_hints": None,
                "ref_solution": "",
                "group": "subject",
                "effort": None,
                "image": None,
                "_kind": "multiple choice" if mc else "fill in",
            }
        )
    return rows, dropped


def public(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", choices=sorted(SETS))
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of render failures")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped = [], {}
    for name, fn in (("telemath", load_telemath), ("wmb", load_wmb)):
        if a.only in (None, name):
            r, d = fn(a.data)
            rows += r
            dropped.update(d)
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
            json.dumps(
                [dict(r, problems=why[r["potd"]]) for r in public(new) if r["potd"] in why], ensure_ascii=False, indent=1
            ),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(public(new))
    for k, v in sorted(dropped.items()):
        print(f"dropped: {k}: {v}")
    print(
        json.dumps(
            {
                "rows_kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": collections.Counter(dropped.values()),
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "by_set_kind": collections.Counter(f"{r['set']} / {r['_kind']}" for r in new),
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
    backup_db("comms")
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
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
