"""Import final-answer problem sets that come with an answer key but no solutions, for the
subscription solver to solve and the judge to check against the key (owner 2026-11-19: "option 1,
and I want to import as many useful sources as possible").

Sets (downloaded by the caller into their own folders; nothing in them is executed):
  * MathArena (huggingface.co/MathArena, CC BY-NC-SA; Amplify is private): the original problems of
    AIME 2025-26, HMMT February 2023-26 and November 2025, BRUMO, SMT and CMIMC 2025. AIME goes to the
    bank's AIME source; the others to "United States Competitions" with the contest in the subsource,
    as the bank already files HMMT. MathArena's own numbering is kept ("Problem 4 of 30"), as its
    sets do not say which round a problem came from. APEX (2025 problems from many competitions,
    some reworded to have a final answer) goes to each problem's own competition, mapped by hand in
    APEX, with ", as posed in MathArena APEX" in the subsource.
  * IMO-Bench AnswerBench v2 (github.com/google-deepmind/superhuman, CC BY 4.0): 400 olympiad problems
    reworded or changed on purpose ("robustified"), many with a different answer from the original,
    so they are filed under their own source, with the original competition in the subsource.

Statements keep their $ math; $$ displays become \\[ \\], Markdown bold becomes \\textbf and
Markdown bullet lists become itemize. An answer with LaTeX in it is wrapped in $ $. A problem the
bank already has (the same latex_hash, or 85% of its 5-word shingles in one bank question) is skipped
and listed. Every row gets the solving model of --model/--effort in --assignments, which puts it in
run_sub.py's scope (config.subscription.assignments_file).

Usage (repo root):
  python -m app.tools.import_answer_sets --matharena DIR --answerbench CSV --dry-run [--dump rows.json]
  python -m app.tools.import_answer_sets --matharena DIR --answerbench CSV --apply
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash, pdf_safe

MAP_PATH = Path("app/data/appdata/answer_sets_map.csv")  # git-ignored: question id -> set, number
ASSIGNMENTS = Path("pipeline/answer_sets_assignments.json")
FIGURES_PATH = Path("app/data/appdata/answer_sets_figures.json")  # git-ignored: Asymptote code to make images from
OPUS = "claude-opus-5-5"
US = "United States Competitions"
AIME = "American Invitational Mathematics Examination"
ANSWERBENCH = "IMO-Bench AnswerBench"
# MathArena set -> (source, subsource for problem i of n)
MATHARENA = {
    "aime_2025": (AIME, lambda i, n: f"2025, AIME {'I' if i <= 15 else 'II'}, Problem {(i - 1) % 15 + 1}"),
    "aime_2026": (AIME, lambda i, n: f"2026, AIME {'I' if i <= 15 else 'II'}, Problem {(i - 1) % 15 + 1}"),
    **{f"hmmt_feb_{y}": (US, lambda i, n, y=y: f"Harvard-MIT Mathematics Tournament, February {y}, Problem {i} of {n}")
       for y in (2023, 2024, 2025, 2026)},
    "hmmt_nov_2025": (US, lambda i, n: f"Harvard-MIT Mathematics Tournament, November 2025, Problem {i} of {n}"),
    "brumo_2025": (US, lambda i, n: f"Brown University Mathematics Olympiad, 2025, Problem {i} of {n}"),
    "smt_2025": (US, lambda i, n: f"Stanford Math Tournament, 2025, Problem {i} of {n}"),
    "cmimc_2025": (US, lambda i, n: f"Carnegie Mellon Informatics and Mathematics Competition, 2025, Problem {i} of {n}"),
}
EUR, ASIA, IND, CHN = "Other European Olympiads", "Other Asian Olympiads", "Indian Olympiads", "Chinese Olympiads"
APEX_SETS = ("apex_2025", "apex-shortlist")
APEX_TAG = ", as posed in MathArena APEX"  # its problems may be reworded to have a final answer
# MathArena APEX problem label -> (source, subsource), by hand in the bank's own naming; labels that
# do not say which competition they are (CMM, BMO: British or Balkan) keep MathArena's label
APEX = {
    "All Russian 2025 11.8": ("All-Russian Olympiad", "2025, Grade 11, Problem 8"),
    "All Russian 2025 11.4": ("All-Russian Olympiad", "2025, Grade 11, Problem 4"),
    "Turkey TST 2025 P5": (EUR, "Turkey Team Selection Test, 2025, Problem 5"),
    "SMT 2025 P8": (US, "Stanford Math Tournament, 2025, Problem 8"),
    "SMT 2025 P42": (US, "Stanford Math Tournament, 2025, Problem 42"),
    "SMT 2025 P43": (US, "Stanford Math Tournament, 2025, Problem 43"),
    "Serbian MO 2025 P6": (EUR, "Serbian Mathematical Olympiad, 2025, Problem 6"),
    "serbian-bmotst-2025-p5": (EUR, "Serbia Team Selection Test for the Balkan Mathematical Olympiad, 2025, Problem 5"),
    "CMM 2025 Individual P10": ("MathArena APEX", "CMM 2025 Individual P10"),
    "CMM 2025 Team P7": ("MathArena APEX", "CMM 2025 Team P7"),
    "BMO 2025 P4": ("MathArena APEX", "BMO 2025 P4"),
    "ELMO Shortlist 2025 N7": ("ELMO Mathematical Olympiad Shortlist", "2025, N7"),
    "ELMO Shortlist 2025 C7": ("ELMO Mathematical Olympiad Shortlist", "2025, C7"),
    "ELMO Shortlist 2025 C8": ("ELMO Mathematical Olympiad Shortlist", "2025, C8"),
    "China TST 2025 P5": ("China Team Selection Test", "2025, Problem 5"),
    "China TST 2025 P10": ("China Team Selection Test", "2025, Problem 10"),
    "China TST 2025 P18": ("China Team Selection Test", "2025, Problem 18"),
    "China TST 2025 P22": ("China Team Selection Test", "2025, Problem 22"),
    "EMCC 2025 Guts P24": (US, "Exeter Math Club Competition, 2025, Guts Round, Problem 24"),
    "emcc-2025-guts-18": (US, "Exeter Math Club Competition, 2025, Guts Round, Problem 18"),
    "IMO 2025 P6": ("International Mathematical Olympiad", "2025, Problem 6"),
    "imosl-2024-c8": ("International Mathematical Olympiad", "2024, Shortlist, C8"),
    "imosl-2024-n7": ("International Mathematical Olympiad", "2024, Shortlist, N7"),
    "usa-tst-2025-p1": ("United States of America Team Selection Test", "2025, Problem 1"),
    "American TSTST 2025 P3": ("United States of America Team Selection Test Selection Test", "2025, Problem 3"),
    "bmmt-2025-team-p19": (US, "Berkeley mini Math Tournament, 2025, Team Round, Problem 19"),
    "hmmt-2025-team-p10": (US, "Harvard-MIT Mathematics Tournament, February 2025, Team Round, Problem 10"),
    "hmmt-2025-team-p4": (US, "Harvard-MIT Mathematics Tournament, February 2025, Team Round, Problem 4"),
    "HMMT Feb 2025 C9": (US, "Harvard-MIT Mathematics Tournament, February 2025, Combinatorics Round, Problem 9"),
    "HMMT Feb 2025 C10": (US, "Harvard-MIT Mathematics Tournament, February 2025, Combinatorics Round, Problem 10"),
    "Brumo 2025 P30": (US, "Brown University Mathematics Olympiad, 2025, Problem 30"),
    "AIME 2025 P14": (AIME, "2025, Problem 14 (AIME I or II not given)"),
    "AIME 2025 P15": (AIME, "2025, Problem 15 (AIME I or II not given)"),
    "indian-imotc-day2-p3": (IND, "Indian International Mathematical Olympiad Training Camp, 2025, Day 2, Problem 3"),
    "India IMOTC 2025 Day 2 P1": (IND, "Indian International Mathematical Olympiad Training Camp, 2025, Day 2, Problem 1"),
    "India STEMS A 2025 P4": (IND, "STEMS Mathematics Olympiad (Chennai Mathematical Institute), 2025, Category A, Problem 4"),
    "India STEMS C 2025 P6": (IND, "STEMS Mathematics Olympiad (Chennai Mathematical Institute), 2025, Category C, Problem 6"),
    "rmm-2025-p3": ("Romanian Masters of Mathematics", "2025, Problem 3"),
    "Germany TST 2025 P3": (EUR, "Germany Team Selection Test, 2025, Problem 3"),
    "Germany TST 2025 P4": (EUR, "Germany Team Selection Test, 2025, Problem 4"),
    "Germany TST 2025 P7": (EUR, "Germany Team Selection Test, 2025, Problem 7"),
    **{f"Korea Winter Program Practice Test 2025 P{i}": (ASIA, f"Korea Winter Program Practice Test, 2025, Problem {i}")
       for i in (2, 3, 6, 8)},
    "Korea Final Round 2025 P5": (ASIA, "Korean Mathematical Olympiad, 2025, Final Round, Problem 5"),
    "Taiwan TST 2025 #3 Quiz 1C": ("Taiwan Team Selection Test", "2025, Round 3, Quiz 1, Problem C"),
    "Taiwan TST 2025 #1 P5": ("Taiwan Team Selection Test", "2025, Round 1, Problem 5"),
    "Taiwan TST 2025 #3 Quiz P5": ("Taiwan Team Selection Test", "2025, Round 3, Quiz, Problem 5"),
    "China Girls MO 2025 P7": (CHN, "China Girls' Mathematical Olympiad, 2025, Problem 7"),
    "Japan MO 2025 P3": ("Japan Mathematical Olympiad Final Round", "2025, Problem 3"),
    "IzHO 2025 P2": (ASIA, "International Zhautykov Olympiad, 2025, Problem 2"),
    "IzHO 2025 P4": (ASIA, "International Zhautykov Olympiad, 2025, Problem 4"),
    "EGMO 2025 P5": ("European Girls' Mathematical Olympiad", "2025, Problem 5"),
    "Bulgarian MO 2025 P2": (EUR, "Bulgarian Mathematical Olympiad, 2025, Problem 2"),
    "Bulgarian MO 2025 P6": (EUR, "Bulgarian Mathematical Olympiad, 2025, Problem 6"),
    "Swiss TST 2025 P5": (EUR, "Swiss Team Selection Test, 2025, Problem 5"),
    "LMAO 2025 Day 1 P2": ("Mock Olympiads", "LMAO, 2025, Day 1, Problem 2"),
    "LMAO 2025 Day 2 P1": ("Mock Olympiads", "LMAO, 2025, Day 2, Problem 1"),
}
NEAR = 0.85  # share of a problem's 5-word shingles found in one bank question: the same problem
# (set, number, field) -> [(old, new)]: slips in the source data, each old matched exactly once
FIXES = {
    ("IMO-Bench AnswerBench v2", "imo-bench-algebra-097", "answer"): [("\\frac{\\sqrt{5}+1}{2}", "\\frac{\\sqrt{5}+1}{2}$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-geometry-096", "answer"): [("$\\frac{7}{18}", "$\\frac{7}{18}$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-combinatorics-004", "latexcode"): [("\\ldots, 191}$", "\\ldots, 191\\}$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-algebra-013", "latexcode"): [  # \right, and a \} closing a \left\{
        ("\\right)\\right, Q", "\\right), Q"), ("Q\\left(n^{2}\\right)\\}", "Q\\left(n^{2}\\right)\\right\\}")],
    ("MathArena aime_2025", "20", "latexcode"): [  # \wideparen is not in the app's preamble
        ("\\wideparen{DE}", "\\overset{\\frown}{DE}"), ("\\wideparen{HJ}", "\\overset{\\frown}{HJ}"),
        ("\\wideparen{FG}", "\\overset{\\frown}{FG}")],
    ("IMO-Bench AnswerBench v2", "imo-bench-combinatorics-002", "latexcode"): [("i) 99 \\leq n \\leq 206", "i) $99 \\leq n \\leq 206$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-combinatorics-098", "latexcode"): [  # \cI undefined; S is that set
        ("\\sum_{I \\in S}", "\\sum_{I \\in \\mathcal{I}(P_n)}"), ("$\\cI(P_n)$", "$\\mathcal{I}(P_n)$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-geometry-012", "latexcode"): [  # subscripts outside math
        ("points X_y and X_z", "points $X_y$ and $X_z$"), ("Points Y_x, Y_z, Z_x and Z_y", "Points $Y_x$, $Y_z$, $Z_x$ and $Z_y$"),
        ("points X_y, X_z, Y_x, Y_z, Z_x, and Z_y", "points $X_y$, $X_z$, $Y_x$, $Y_z$, $Z_x$, and $Z_y$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-number_theory-021", "latexcode"): [("\\textif{", "\\textit{")],
    ("MathArena hmmt_nov_2025", "1", "latexcode"): [("\\overlien{BC}", "\\overline{BC}")],
    ("MathArena hmmt_nov_2025", "14", "latexcode"): [("\\begin{array}{ccccc}", "\\begin{array}{cccccc}")],  # six columns
}


def display(m: re.Match) -> str:
    """A display's body: no blank lines (a paragraph break stops LaTeX), and the alignment marks a
    Markdown export left escaped (\\& for &, <br> for \\\\) restored."""
    body = re.sub(r"\n\s*\n", "\n", m.group(1).strip())
    return "\\[" + body.replace("\\&", "&").replace("<br>", "\\\\") + "\\]"


ASY_RE = re.compile(r"\s*\\begin\{asy\}.*?\\end\{asy\}\s*", re.S)
# statements whose figure is drawn in characters from this line to the end (an image is made from it)
ASCII_FIGURES = {("MathArena smt_2025", "22")}
ASCII_ART_RE = re.compile(r"\n[ \t]*_{3,}[ \t]*\n.*\Z", re.S)


def to_latex(text: str) -> str:
    """The statement in the bank's LaTeX. An Asymptote figure (neither renderer draws it) is taken
    out here; load() keeps its code for the image to be made from it (owner 2026-11-20: "convert the
    asymptote rows to images manually later")."""
    t = text.replace("\r\n", "\n").strip()
    t = re.sub(r"\$\$(.+?)\$\$", lambda m: "\\[" + m.group(1).strip() + "\\]", t, flags=re.S)
    t = re.sub(r"\\\[(.+?)\\\]", display, t, flags=re.S)
    t = ASY_RE.sub("\n\n", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    out, items, depth = [], [], 0
    for line in t.split("\n") + [""]:
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m and depth == 0:  # a Markdown bullet; inside a display, "- & -" is a row of an array
            items.append(m.group(1))
            continue
        if items:
            out += ["\\begin{itemize}"] + [f"\\item {x}" for x in items] + ["\\end{itemize}"]
            items = []
        out.append(line)
        depth += line.count("\\[") - line.count("\\]")
    return pdf_safe(re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip())


def answer_latex(a: str) -> str:
    a = str(a).strip()
    if not a or "$" in a or a.startswith(("\\(", "\\[")) or not re.search(r"[\\^_{}]", a):
        return a
    return f"${a}$"


def shingles(t: str) -> set:
    w = " ".join(re.sub(r"\\[a-zA-Z]+|[^a-z0-9]", " ", t.lower()).split()).split()
    return {" ".join(w[i:i + 5]) for i in range(max(len(w) - 4, 1))}


def load(matharena: Path, answerbench: Path) -> list[dict]:
    rows = []
    for name, (source, sub) in MATHARENA.items():
        data = json.loads((matharena / f"{name}.json").read_text(encoding="utf-8"))
        for r in data:
            i = int(r["problem_idx"])
            rows.append({"set": f"MathArena {name}", "idx": str(i), "source": source, "subsource": sub(i, len(data)),
                         "latexcode": to_latex(r["problem"]), "answer": answer_latex(r["answer"]), "orig": "",
                         "asy": "\n\n".join(m.group(0).strip() for m in ASY_RE.finditer(r["problem"]))})
    for name in APEX_SETS:
        for r in json.loads((matharena / f"{name}.json").read_text(encoding="utf-8")):
            if r["source"] not in APEX:
                raise SystemExit(f"MathArena {name} {r['problem_idx']}: no source for {r['source']!r} in APEX")
            source, sub = APEX[r["source"]]
            rows.append({"set": f"MathArena {name}", "idx": str(r["problem_idx"]), "source": source,
                         "subsource": sub + ("" if source == "MathArena APEX" else APEX_TAG),
                         "latexcode": to_latex(r["problem"]), "answer": answer_latex(r["answer"]), "orig": r["source"],
                         "asy": "\n\n".join(m.group(0).strip() for m in ASY_RE.finditer(r["problem"]))})
    for r in csv.DictReader(open(answerbench, encoding="utf-8")):
        orig = (r.get("Source") or "").strip()
        rows.append({"set": "IMO-Bench AnswerBench v2", "idx": r["Problem ID"], "source": ANSWERBENCH,
                     "subsource": r["Problem ID"] + (f", adapted from {orig}" if orig else ""),
                     "latexcode": to_latex(r["Problem"]), "answer": answer_latex(r["Short Answer"]), "orig": orig,
                     "asy": "\n\n".join(m.group(0).strip() for m in ASY_RE.finditer(r["Problem"]))})
    for r in rows:
        r.update(potd=f"{r['set']} {r['idx']}", hints=None, more_hints=None, solution=None)  # for check()
        if (r["set"], r["idx"]) in ASCII_FIGURES:
            m = ASCII_ART_RE.search(r["latexcode"])
            if not m:
                raise SystemExit(f"{r['potd']}: no character figure found")
            r["asy"], r["latexcode"] = "ASCII art:\n" + m.group(0).strip("\n"), r["latexcode"][:m.start()].rstrip()
        for fld in ("latexcode", "answer"):
            for old, new in FIXES.get((r["set"], r["idx"], fld), []):
                if r[fld].count(old) != 1 or (fld == "answer" and r[fld].endswith(new)):
                    raise SystemExit(f"FIX {r['potd']} {fld}: expected one {old!r}")
                r[fld] = r[fld].replace(old, new)
    return rows


def duplicates(rows: list[dict], conn: sqlite3.Connection) -> dict[int, tuple[int, float]]:
    """Row index -> (bank question id, share) for problems the bank already has."""
    bank = list(conn.execute("SELECT question_id, latexcode, latex_hash FROM questions"))
    by_hash = {h: q for q, _, h in bank}
    index = collections.defaultdict(set)
    for q, t, _ in bank:
        for g in shingles(t):
            index[g].add(q)
    out = {}
    for k, r in enumerate(rows):
        if latex_hash(r["latexcode"]) in by_hash:
            out[k] = (by_hash[latex_hash(r["latexcode"])], 1.0)
            continue
        g = shingles(r["latexcode"])
        hits = collections.Counter(q for x in g for q in index.get(x, ()))
        if hits:
            q, n = hits.most_common(1)[0]
            if n / len(g) >= NEAR:
                out[k] = (q, round(n / len(g), 2))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--matharena", type=Path, required=True)
    p.add_argument("--answerbench", type=Path, required=True)
    p.add_argument("--model", default=OPUS)
    p.add_argument("--effort", default="high")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows = load(a.matharena, a.answerbench)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    print(json.dumps({"rows": len(rows), "in_bank": len(dup), "to_add": len(new), "check_problems": len(problems),
                      "by_set": collections.Counter(r["set"] for r in new),
                      "answers_wrapped": sum(r["answer"].startswith("$") for r in new),
                      "asymptote_figures_kept_aside": [r["potd"] for r in new if r["asy"]]}, default=dict))
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("answer-sets")
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in new:
            h = latex_hash(r["latexcode"])
            if h in existing:  # two rows of these sets with the same text
                continue
            cur = conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, hints, more_hints, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, NULL, NULL, NULL, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"], r["answer"], h),
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
        "note": "Final-answer sets imported by app/tools/import_answer_sets.py (answer key, no solutions), with the "
                "model and effort that solve them. Listing a question here puts it in run_sub.py's scope.",
        "questions": {}}
    # a question whose figure is still Asymptote code waits for its image before it is solved
    doc["questions"].update({str(q): {"model": a.model, "effort": a.effort} for q, r in added if not r["asy"]})
    ASSIGNMENTS.write_text(json.dumps(doc, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    figures = json.loads(FIGURES_PATH.read_text(encoding="utf-8")) if FIGURES_PATH.exists() else {}
    figures.update({str(q): {"set": r["set"], "number": r["idx"], "asy": r["asy"]} for q, r in added if r["asy"]})
    FIGURES_PATH.write_text(json.dumps(figures, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; "
          f"map={MAP_PATH}; assignments={ASSIGNMENTS} ({len(doc['questions'])} questions); "
          f"figures to draw: {sorted(int(q) for q in figures)} in {FIGURES_PATH}")


if __name__ == "__main__":
    main()
