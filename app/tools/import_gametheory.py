"""
Import game-theory problem sets
-------------------------------
Two Hugging Face datasets by Alogotron (Apache-2.0; read from the parquet files, nothing in them is run):

  bench  GameTheory-Bench (2,913 rows): synthetic problems whose keys come from solvers (nashpy support
         enumeration, closed forms). Categories: normal-form games (2x2, 3x3, 3x4, 4x4), zero-sum games,
         sequential games, auctions, cooperative games, Bayesian games, mechanism design.
  form   GameTheory-Formulator (1,215 rows): business / politics / security / auction scenarios in prose to be
         modelled and solved; only a short prose answer exists.

Owner decisions of 2026-11-25 (asleep; "import as many sources as possible"): group "subject" for the classifier,
Source = the dataset name, subsource = the category (no ids in the text, no numbers of our own).

bench: duplicates of the problem text are dropped, then at most CAP rows per subcategory (the 2x2 "classic_*"
games count as one subcategory), picked by a hash of the text. The key is rebuilt from the dataset's answer and
its verification record, not copied: the dataset's answer strings always call the strategies Up/Down/Left/Right
(or Top/Middle/Bottom, R1.., C1..) even when the table names them otherwise, so the names are mapped back to the
table's own labels; questions that ask for pure equilibria get only the pure ones, questions that ask for mixed
ones only the mixed ones; dominance answers (index lists) are written out from the verification record.
The step solutions are templates (they also use the canonical names); they are kept in ref_solution only (labels
mapped), never stored as the solution, and the solver writes the solution.
form: the scenario + one instruction line built from the dataset's solution concept; the dataset's prose
solution (short, not solver-verified) goes to ref_solution only and the answer stays empty (the solver
works it out). Rows whose solution has no number are dropped (vague), near-repeats within a game subtype are
dropped, at most FORM_PER_SUBTYPE per subtype and FORM_TOTAL in all, chosen round-robin over subtypes and domains.

Conversions: markdown payoff tables -> LaTeX array in \\[ ... \\]; "- " lines -> itemize; "{A, B}" sets,
arrows, <=, Greek letters -> math; currency $ -> \\$.

Usage (repo root):
  python -m app.tools.import_gametheory --data DIR --dry-run [--set bench|form|all] [--dump rows.json]
                                         [--set-aside [--exclude failures.json]]
  python -m app.tools.import_gametheory --data DIR --apply [--set ...]
DIR holds bench/train.parquet and form/train.parquet.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/gametheory_set_aside.json")
CAP = 40  # rows per GameTheory-Bench subcategory
FORM_PER_SUBTYPE = 6
FORM_TOTAL = 150
WITHIN = 0.6  # shingle share that makes two Formulator rows of one subtype near-repeats
SETS = {"bench": ("GameTheory-Bench", "GameTheory-Bench"), "form": ("GameTheory-Formulator", "GameTheory-Formulator")}

CATEGORY_NAMES = {
    "normal_form_2x2": "Normal-form games, 2x2",
    "normal_form_3x3": "Normal-form games, 3x3",
    "normal_form_3x4": "Normal-form games, 3x4",
    "normal_form_4x4": "Normal-form games, 4x4",
    "zero_sum": "Zero-sum games",
    "sequential_game": "Sequential games",
    "auction_theory": "Auction theory",
    "cooperative_game": "Cooperative games",
    "bayesian_game": "Bayesian games",
    "mechanism_design": "Mechanism design",
}
ESC = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "$": r"\$"}
GREEK = {
    "φ": r"\varphi",
    "π": r"\pi",
    "ε": r"\varepsilon",
    "≤": r"\le",
    "≥": r"\ge",
    "×": r"\times",
    "→": r"\to",
    "≈": r"\approx",
    "∈": r"\in",
    "−": "-",
}
ROW_CANON = (["Up", "Down"], ["Top", "Middle", "Bottom"], ["R1", "R2", "R3", "R4"])
COL_CANON = (["Left", "Right"], ["Left", "Center", "Right"], ["C1", "C2", "C3", "C4"])


def esc(s: str) -> str:
    return "".join(ESC.get(c, c) for c in s)


# ---------------------------------------------------------------- text
def set_items(body: str) -> str:
    out = []
    for x in body.split(","):
        x = x.strip()
        plain = re.fullmatch(r"[A-Za-z]\d*|-?\d+(?:\.\d+)?|\$\d+", x)
        out.append(esc(x) if plain else r"\text{" + esc(x) + "}")
    return ", ".join(out)


def inline(text: str) -> str:
    """One line of prose -> LaTeX: sets and symbols into math, specials escaped."""
    t = text.replace("\u2014", "---").replace("\u2013", "--").replace("\u2019", "'").replace("\u00a0", " ")
    t = t.replace("\ufffd", "-")
    stash: list[str] = []

    def put(m: str) -> str:
        stash.append(m)
        return "\ue000" + chr(0xE100 + len(stash) - 1) + "\ue001"

    t = re.sub(r"\*\*([^*]+)\*\*", lambda m: r"\textbf{" + esc(m.group(1)) + "}", t)
    t = re.sub(
        r"\b(?:v|u)\(\{[^{}]*\}\)(?:\s*=\s*-?\d+(?:\.\d+)?)?",
        lambda m: put("$" + re.sub(r"\{([^{}]*)\}", r"\\{\1\\}", esc(m.group(0)).replace("\\$", "\\$")) + "$"),
        t,
    )
    t = re.sub(
        r"\{([^{}\n]{1,120})\}",
        lambda m: put("$\\{" + set_items(m.group(1)) + "\\}$"),
        t,
    )
    t = re.sub(
        r"\bsi = V \+ εi, where εi ~ Uniform\[([^\]]*)\]",
        lambda m: put(r"$s_i = V + \varepsilon_i$, where $\varepsilon_i \sim \mathrm{Uniform}[" + m.group(1).replace(" ", "") + "]$"),
        t,
    )
    t = re.sub(
        r"\bP = (\d+) - (\d+)\(q1 \+ q2\)",
        lambda m: put(rf"$P = {m.group(1)} - {m.group(2)}(q_1 + q_2)$"),
        t,
    )
    t = re.sub(r"\(([^()]*?)\)\s*→\s*(payoffs\s*)?\(([^()]*?)\)", lambda m: put(f"$({m.group(1)}) \\to ({m.group(3)})$"), t)
    t = re.sub(r"\bq(\d)\b", lambda m: put(f"$q_{m.group(1)}$"), t)
    t = re.sub(r"\bc(\d)\b", lambda m: put(f"$c_{m.group(1)}$"), t)
    t = re.sub(r"\bv(\d)\b", lambda m: put(f"$v_{m.group(1)}$"), t)
    t = re.sub(r"\bs(\d)\b", lambda m: put(f"$s_{m.group(1)}$"), t)
    t = re.sub(r"\bUniform\[([^\]]*)\]", lambda m: put(r"$U[" + m.group(1).replace(" ", "").replace("+", "") + "]$"), t)
    t = re.sub(r"[φπε≤≥×→≈∈−]", lambda m: put(f"${GREEK[m.group(0)]}$"), t)
    t = esc(t)
    t = re.sub(r"\ue000(.)\ue001", lambda m: stash[ord(m.group(1)) - 0xE100], t)
    t = re.sub(r'"([^"\n]+)"', lambda m: "``" + m.group(1) + "''", t)
    return t.strip()


def table_tex(lines: list[str]) -> str:
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines if not re.match(r"^\s*[-| :]+$", ln)]
    n = len(rows[0])
    body = []
    for i, r in enumerate(rows):
        cells = []
        for j, c in enumerate(r):
            if i == 0 and j == 0:
                cells.append(" \\backslash ".join(r"\text{" + esc(x.strip()) + "}" for x in c.split("\\")))
            elif i == 0 or j == 0:
                cells.append(r"\text{" + esc(c) + "}")
            else:
                cells.append(esc(c).replace("−", "-"))
        body.append(" & ".join(cells))
    head, rest = body[0], body[1:]
    return "\\[\n\\begin{array}{c|" + "c" * (n - 1) + "}\n" + head + " \\\\ \\hline\n" + " \\\\\n".join(rest) + "\n\\end{array}\n\\]"


def prose(text: str) -> str:
    """Whole statement: tables, bullet lists, numbered lists, paragraphs."""
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if "|" in ln and i + 1 < len(lines) and re.match(r"^\s*\|?\s*-{2,}\s*\|", lines[i + 1]):
            j = i
            while j < len(lines) and "|" in lines[j]:
                j += 1
            out.append(table_tex(lines[i:j]))
            i = j
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", ln)
        n = re.match(r"^\s*\d+\.\s+(.*)$", ln)
        if m or n:
            env = "itemize" if m else "enumerate"
            pat = r"^\s*[-*]\s+(.*)$" if m else r"^\s*\d+\.\s+(.*)$"
            items = []
            while i < len(lines) and re.match(pat, lines[i]):
                items.append(inline(re.match(pat, lines[i]).group(1)))
                i += 1
            out.append("\\begin{" + env + "}\n" + "\n".join("\\item " + x for x in items) + "\n\\end{" + env + "}")
            continue
        if ln.strip():
            # indented continuation lines of a game description stay in their paragraph
            para = [inline(ln.strip())]
            i += 1
            out.append(para[0])
            continue
        i += 1
    return "\n\n".join(out)


# ---------------------------------------------------------------- bench answers
def table_labels(problem: str) -> tuple[list[str], list[str]] | None:
    lines = [ln for ln in problem.split("\n") if "|" in ln and not re.match(r"^\s*[-| :]+$", ln)]
    if len(lines) < 2:
        return None
    cells = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines]
    return [r[0] for r in cells[1:]], cells[0][1:]


def relabel_map(problem: str) -> dict[str, str]:
    lab = table_labels(problem)
    if not lab:
        return {}
    rows, cols = lab
    out = {}
    for canon, actual in ((ROW_CANON, rows), (COL_CANON, cols)):
        for lst in canon:
            if len(lst) == len(actual):
                for c, a in zip(lst, actual, strict=True):
                    if c not in actual and c != a:
                        out[c] = a
    return out


def relabel(text: str, mp: dict[str, str]) -> str:
    if not mp:
        return text
    return re.sub(r"\b(" + "|".join(map(re.escape, mp)) + r")\b", lambda m: mp[m.group(1)], text)


def num(x: str) -> str:
    return re.sub(r"(\.\d*?)0+$", r"\1", x).rstrip(".") if "." in x else x


def mixed_text(p1: str, p2: str) -> str:
    def f(s: str) -> str:
        return ", ".join(f"{a.strip()} {num(b)}" for a, b in (kv.rsplit(":", 1) for kv in s.split(",")))

    return f"P1 mixes ({esc(f(p1))}), P2 mixes ({esc(f(p2))})"


def dominance_text(ver: dict, labels: tuple[list[str], list[str]]) -> str | None:
    rows, cols = labels
    parts = []
    for who, key, names in (("Player 1", "p1_dominance", rows), ("Player 2", "p2_dominance", cols)):
        d = ver.get(key)
        if not isinstance(d, dict):
            return None
        bits = []
        for kind, word in (
            ("strictly_dominant", "strictly dominant"),
            ("weakly_dominant", "weakly dominant"),
            ("strictly_dominated", "strictly dominated"),
            ("weakly_dominated", "weakly dominated"),
        ):
            idx = d.get(kind) or []
            if idx:
                bits.append(f"{word}: " + ", ".join(esc(names[k]) for k in idx))
        parts.append(f"{who}: " + ("; ".join(bits) if bits else "no dominant or dominated strategy"))
    return "; ".join(parts)


MATH_ANS = [
    (r"φ\(P(\d+)\)", r"$\\varphi(P_{\1})$"),
    (r"SSI\(V(\d+)\)", r"$\\mathrm{SSI}(V_{\1})$"),
    (r"\bπ(\d)", r"$\\pi_{\1}$"),
    (r"\bq(\d)\*", r"$q_{\1}^{*}$"),
    (r"\bP\*", r"$P^{*}$"),
    (r"b\(v\)=\((\d+)/(\d+)\)×v\^(\d+)/(\d+)\^(\d+)", r"$b(v)=\\frac{\1}{\2}\\cdot\\frac{v^{\3}}{\4^{\5}}$"),
    (r"b\(v\)=\((\d+)/(\d+)\)v", r"$b(v)=\\frac{\1}{\2}v$"),
    (r"b\(s\) = s - ([\d.]+)", r"$b(s)=s-\1$"),
    (r"E\[Revenue\] = \((\d+)/(\d+)\)×(\d+) = ([\d.]+)", r"$E[\\text{Revenue}] = \\frac{\1}{\2}\\cdot \3 = \4$"),
    (r"E\[Revenue\]", r"$E[\\text{Revenue}]$"),
    (r"(-?\d+)≤x(\d)≤(-?\d+)", r"$\1 \\le x_{\2} \\le \3$"),
    (r"\(v=(\d+)\)", r"($v=\1$)"),
    (r"→", r"$\\to$"),
]


def bench_answer(r: dict, ver: dict) -> str | None:
    sub, problem, ans = r["subcategory"], r["problem"], r["answer"].strip()
    mp = relabel_map(problem) if r["category"].startswith(("normal_form", "zero_sum")) else {}
    ans = relabel(ans, mp)
    low = problem.lower()
    lab = table_labels(problem)
    if "dominan" in sub and "iesds" not in sub:
        return dominance_text(ver, lab) if lab else None
    if r["category"].startswith("normal_form") and "iesds" not in sub and ans.startswith("["):
        pure = re.findall(r"\(([^()]+)\)", re.sub(r"P[12]=\[[^\]]*\]", "", ans))
        mixed = re.search(r"P1=\[([^\]]*)\],\s*P2=\[([^\]]*)\]", ans)
        want_pure = "pure" in low and "mixed" not in low
        want_mixed = "mixed" in low and "pure" not in low
        bits = []
        if pure and not want_mixed:
            bits.append("pure: " + "; ".join("(" + esc(p) + ")" for p in pure))
        if mixed and not want_pure:
            bits.append("mixed: " + mixed_text(*mixed.groups()))
        return " and ".join(bits) if bits else None
    if "iesds" in sub:
        return "Surviving profile after iterated elimination: " + esc(ans)
    if sub == "incentive_compatibility":
        mech, _, verdict = ans.partition(": ")
        return esc(mech) + ": " + ("not incentive compatible" if "NOT" in verdict else "incentive compatible")
    ans = re.sub(r"Saddle points: \[(.*?)\]", r"Saddle point(s): \1", ans)
    ans = re.sub(r"(P[12])=\[([^\]]*)\]", r"\1 = (\2)", ans)
    ans = esc(ans)
    for pat, rep in MATH_ANS:
        ans = re.sub(pat, rep, ans)
    return ans


def h(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def load_bench(data: Path) -> tuple[list[dict], dict[str, str], dict]:
    import pyarrow.parquet as pq

    src = pq.read_table(data / "bench" / "train.parquet").to_pylist()
    dropped: dict[str, str] = {}
    stats: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0, 0])  # found, kept, dropped
    seen: set[str] = set()
    pool: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in src:
        grp = "classic" if r["subcategory"].startswith("classic_") else r["subcategory"]
        stats[r["category"]][0] += 1
        norm = re.sub(r"\s+", " ", r["problem"]).strip()
        if norm in seen:
            dropped[r["id"]] = "same problem text as another row"
            stats[r["category"]][2] += 1
            continue
        seen.add(norm)
        pool[(r["category"], grp)].append(r)
    rows = []
    for (cat, _grp), lst in sorted(pool.items()):
        lst.sort(key=lambda r: h(r["problem"]))
        for r in lst[CAP:]:
            dropped[r["id"]] = f"over the cap of {CAP} per subcategory"
            stats[cat][2] += 1
        for r in lst[:CAP]:
            try:
                ver = json.loads(r["verification"]) if r["verification"] else {}
            except ValueError:
                ver = {}
            ans = bench_answer(r, ver)
            if not ans:
                dropped[r["id"]] = "no usable key"
                stats[cat][2] += 1
                continue
            mp = relabel_map(r["problem"]) if cat.startswith(("normal_form", "zero_sum")) else {}
            rows.append(
                {
                    "potd": f"GameTheory-Bench {r['id']}",
                    "set": "GameTheory-Bench",
                    "idx": r["id"],
                    "orig": f"{r['category']}; {r['subcategory']}; {r['difficulty']}",
                    "source": "GameTheory-Bench",
                    "subsource": f"{CATEGORY_NAMES[cat]}, {r['subcategory'].replace('_', ' ')}",
                    "latexcode": prose(r["problem"]),
                    "answer": ans,
                    "solution": None,
                    "hints": None,
                    "more_hints": None,
                    "ref_solution": relabel(r["solution"], mp),
                    "group": "subject",
                    "effort": None,
                    "image": None,
                    "_cat": cat,
                }
            )
            stats[cat][1] += 1
    return rows, dropped, stats


def load_form(data: Path) -> tuple[list[dict], dict[str, str], dict]:
    import pyarrow.parquet as pq

    src = pq.read_table(data / "form" / "train.parquet").to_pylist()
    dropped: dict[str, str] = {}
    stats: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0, 0])
    by_sub: dict[str, list[dict]] = collections.defaultdict(list)
    for r in src:
        stats[r["game_subtype"]][0] += 1
        if not re.search(r"\d", r["solution"]):
            dropped[r["id"]] = "solution has no number (vague)"
            stats[r["game_subtype"]][2] += 1
            continue
        by_sub[r["game_subtype"]].append(r)
    picked: dict[str, list[dict]] = {}
    for sub, lst in by_sub.items():
        lst.sort(key=lambda r: h(r["scenario"]))
        keep, sigs = [], []
        for r in lst:
            s = shingles(re.sub(r"[^a-z0-9]+", " ", r["scenario"].lower()))
            if any(len(s & o) / max(len(s), 1) >= WITHIN for o in sigs):
                dropped[r["id"]] = "near-repeat of a kept scenario"
                stats[sub][2] += 1
                continue
            sigs.append(s)
            keep.append(r)
        picked[sub] = keep
    # round robin over subtypes, alternating domains inside a subtype
    order: list[dict] = []
    queues = {}
    for sub, keep in sorted(picked.items()):
        q, doms = [], collections.defaultdict(list)
        for r in keep:
            doms[r["domain"]].append(r)
        while any(doms.values()) and len(q) < FORM_PER_SUBTYPE:
            for d in sorted(doms):
                if doms[d] and len(q) < FORM_PER_SUBTYPE:
                    q.append(doms[d].pop(0))
        for r in keep:
            if r not in q:
                dropped[r["id"]] = f"over {FORM_PER_SUBTYPE} per subtype"
                stats[sub][2] += 1
        queues[sub] = q
    while any(queues.values()) and len(order) < FORM_TOTAL:
        for sub in sorted(queues):
            if queues[sub] and len(order) < FORM_TOTAL:
                order.append(queues[sub].pop(0))
    for q in queues.values():
        for r in q:
            dropped[r["id"]] = f"over the total of {FORM_TOTAL}"
            stats[r["game_subtype"]][2] += 1
    rows = []
    for r in order:
        concept = r["solution_concept"]
        ask = {
            "Dominant Strategy": "Model the situation as a game and determine whether each player has a dominant strategy and what the players do.",
            "Shapley Value": "Model the situation as a cooperative game and determine the fair division by the Shapley value.",
            "Revenue Equivalence Theorem": "Model the situation as an auction and compare the sellers' expected revenues using the Revenue Equivalence Theorem.",
        }.get(
            concept,
            f"Model the situation as a game and find its equilibrium (solution concept: {concept}).",
        )
        rows.append(
            {
                "potd": f"GameTheory-Formulator {r['id']}",
                "set": "GameTheory-Formulator",
                "idx": r["id"],
                "orig": f"{r['domain']}; {r['game_subtype']}; {concept}; {r['difficulty']}",
                "source": "GameTheory-Formulator",
                "subsource": f"{r['domain'].capitalize()}, {r['game_subtype'].replace('_', ' ')}",
                "latexcode": inline(r["scenario"]) + "\n\n" + ask,
                "answer": None,
                "solution": None,
                "hints": None,
                "more_hints": None,
                "ref_solution": r["solution"].replace("\ufffd", "-"),
                "group": "subject",
                "effort": None,
                "image": None,
                "_cat": "form:" + r["game_subtype"],
            }
        )
        stats[r["game_subtype"]][1] += 1
    return rows, dropped, stats


def public(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--set", choices=["bench", "form", "all"], default="all")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of render failures")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped, stats = [], {}, {}
    for name, fn in (("bench", load_bench), ("form", load_form)):
        if a.set in (name, "all"):
            r, d, s = fn(a.data)
            rows += r
            dropped.update(d)
            stats[name] = s
    # near-duplicates between the two sets and inside the kept rows (same statement hash)
    seen: set[str] = set()
    uniq = []
    for r in rows:
        k = latex_hash(r["latexcode"])
        if k in seen:
            dropped[r["idx"]] = "same statement as another kept row"
            continue
        seen.add(k)
        uniq.append(r)
    rows = uniq
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
                "kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "with_answer": sum(bool(r["answer"]) for r in new),
                "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
                "by_group": collections.Counter(r["_cat"].split(":")[0] if r["_cat"].startswith("form") else r["_cat"] for r in new),
                "found_kept_dropped": {k: dict(v) for k, v in stats.items()},
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
    backup_db("gametheory")
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {x for (x,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in public(new):
            hh = latex_hash(r["latexcode"])
            if hh in existing:
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
                    hh,
                ),
            )
            existing.add(hh)
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
