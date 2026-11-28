"""
Import the Extraction data set: competition archives and probability and physics textbooks, OCR'd to LaTeX
-----------------------------------------------------------------------------------------------------------
Owner 2026-11-27: "C:\\Users\\Lenovo\\Downloads\\dataset.zip Extract all the content from this zip, and integrate them
into the database. Integration includes normalizing the source and subsource to fit current guidelines, routing
unsolved questions to their suitable solvers, making sure images are imported correctly, embedding and
classification."

The zip (folder dataset/) was built on the owner's machine from twelve archives of PDFs (429 PDFs) with a local OCR
tool and checked against the PDFs (its README says how): questions.jsonl holds 7,155 problems, one a line, with
their answers, solutions and notes as LaTeX, the figures they use under figures/, and per problem the source and a
subsource dict read from the document. Fields used here: id, collection, source, subsource, question (the statement
rewritten to stand by itself where the document's leaned on something it does not state), answer, solutions
([{title, tex}]), notes (remarks, comments; on a camp sheet without solutions, hints), figures, same_problem_as.

Kept as the bank stores them:
  * source: the bank's name for the competition or book (SOURCES; the bank's own names where it has the source).
  * subsource: a group, never an id (owner 2026-11-23): competitions "<year>" or "<year>, <paper/round/category>"
    ("2015, Fall, Junior A-Level", "2012, Senior", "2017, Session A"); camp handouts "<year>, Winter Camp";
    books "Chapter <n>" (Chenlo's book has topics: "Topic <n>"). The dataset's id, collection and the rest of its
    subsource go in the map (MAP_PATH), not the bank.
  * latexcode: the statement; answer: the short answer where printed; solution: the solutions in order (each under
    its title when there are several), then the notes (remarks and comments); a row without a solution keeps its
    notes as hints (the camp sheets' hints).
  * figures: copied to the app's image folder as extr-<sha1 of the file[:16]>.<ext>, and every \\includegraphics
    names that file with the bank's options ([max width=<w>\\textwidth, alt={}]; a trim/clip is kept).
  * Physics Brawl's first 2012 round is printed in Czech only (40 problems): left out (owner 2026-11-27: "Delete
    non-english questions").
  * Sources the bank already had (IN_BANK: Dekking et al., the Canadian Mathematical Olympiad, the University of
    Toronto competition) are left out whole (owner 2026-11-27); the Tournament of Towns, of which the bank held 35
    problems against the set's 480, adds the problems the bank lacks.
  * Duplicates: one row of each same_problem_as group (one with a solution, from the competition rather than a camp
    sheet), near-duplicates inside the set (85% of 5-word shingles), and problems the bank has
    (import_answer_sets.duplicates) are not added; the bank's matches are listed and kept in the map.

The extra books, part 1 (owner 2026-11-28: "C:\\Users\\Lenovo\\Downloads\\dataset-extra-part1.zip Extract the questions
from this as well, and integrate them into the database the same way"): the same format, folder dataset-extra-part1/,
1,062 problems of the CEMC's Euclid, Fermat and Hypatia contests with their solutions (collection extra_books). The
printed instruction of Fermat's Part C (answers coded as two digits) is left out; each question says what it asks for.
Part 2 (owner 2026-11-28: "C:\\Users\\Lenovo\\Downloads\\dataset-extra-part2.zip Extract and integrate these questions in
the same way"), folder dataset-extra-part2/: 1,971 problems of eight finished books: Andreescu and Feng's 102
Combinatorial and 103 Trigonometry Problems, Castañeda et al. and Meshalkin on probability, Howell's Algorithms, the
Russian Physics Olympiad (2005-2017), Holics's physics problems and discrete-structures course papers (IIT Kharagpur,
IIT Delhi, Berkeley; source the institution, subsource the course, as for the bank's IITD rows). Most of the
probability, algorithms and physics problems come without a solution and go to the solvers.

On --apply: backup, figures copied, rows inserted Uncategorized, MAP_PATH written (question_id, set, number, collection,
bank_duplicate). Classification, the solver queues (unsolved maths rows to run_sub through an assignments file,
the other subjects to run_subjects), judging and embedding follow in the pipeline.

Usage (repo root):
  python -m app.tools.import_extraction --data DIR --dry-run [--dump rows.json] [--set-aside [--exclude fails.json]]
  python -m app.tools.import_extraction --data DIR --apply [--set-aside [--exclude fails.json]]
DIR is the zip's dataset/ folder.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

from app.tools.import_answer_sets import TEXIMAGES, duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "Extraction"
MAP_PATH = Path("app/data/appdata/extraction_map.csv")
SET_ASIDE_PATH = Path("app/data/appdata/extraction_set_aside.json")
IMAGE_PREFIX = "extr"

TOT, CMO_ = "Tournament of Towns", "Canadian Mathematical Olympiad"
SOURCES = {  # the data set's source -> the bank's
    "Canadian IMO training camp (Canadian Mathematical Society)": "Canadian IMO Training Camp",
    "Canadian Mathematical Olympiad": CMO_,
    "Canadian Open Mathematics Challenge": "Canadian Open Mathematics Challenge",
    "European Mathematical Cup": "European Mathematical Cup",
    "Balkan Student Mathematical Competition": "Balkan Student Mathematical Competition",
    "Fyziklani (FYKOS)": "Fyziklani",
    "Physics Brawl Online (FYKOS)": "Physics Brawl Online",
    "Problem of the Week, Purdue University Department of Mathematics": "Purdue Problem of the Week",
    "Simon Marais Mathematics Competition": "Simon Marais Mathematics Competition",
    "Olymon, Mathematical Olympiads Correspondence Program (Canadian Mathematical Society and University of Toronto "
    "Department of Mathematics)": "Olymon",
    "University of Toronto Undergraduate Mathematics Competition": "University of Toronto Mathematics Competitions",
    "International Mathematics Tournament of Towns": TOT,
    "400 Solved Exercises of University Physics": "Chenlo Romero's 400 Solved Exercises of University Physics",
    "A Modern Introduction to Probability and Statistics":
        "Dekking et al.'s A Modern Introduction to Probability and Statistics",
    "Introduction to Probability Models": "Ross's Introduction to Probability Models",
    "Probability and Statistics: The Science of Uncertainty":
        "Evans and Rosenthal's Probability and Statistics: The Science of Uncertainty",
    "University of New South Wales School Mathematics Competition":
        "University of New South Wales School Mathematics Competition",
    # the extra books, part 1 (CEMC, University of Waterloo): one paper a year, so the subsource is the year
    "Euclid Contest": "Euclid Mathematics Contest",
    "Fermat Contest": "Fermat Mathematics Contest",
    "Hypatia Contest": "Hypatia Mathematics Contest",
    # the extra books, part 2
    "102 Combinatorial Problems: From the Training of the USA IMO Team": "Andreescu and Feng's 102 Combinatorial Problems",
    "103 Trigonometry Problems: From the Training of the USA IMO Team": "Andreescu and Feng's 103 Trigonometry Problems",
    "Introduction to Probability and Stochastic Processes with Applications":
        "Castañeda et al.'s Introduction to Probability and Stochastic Processes with Applications",
    "Algorithms: A Top-Down Approach": "Howell's Algorithms: A Top-Down Approach",
    "Collection of Problems in Probability Theory": "Meshalkin's Collection of Problems in Probability Theory",
    "Russian Physics Olympiads 2005-2017": "Russian Physics Olympiad",
    "300 Creative Physics Problems with Solutions": "Holics's 300 Creative Physics Problems with Solutions",
}
# course papers go under their institution, as the bank's IITD rows do (subsource the course): COL202 is IIT Delhi's,
# CS21001 IIT Kharagpur's (also on the papers that do not print the institution), CS70 Berkeley's
COURSE_PAPERS = "Discrete Structures course papers (IIT Kharagpur CS21001 and others)"
COURSES = {"COL202": "IITD", "CS21001": "IITKGP", "CS70": "UC Berkeley"}
PHYSICS = {"Fyziklani", "Physics Brawl Online", "Chenlo Romero's 400 Solved Exercises of University Physics",
           "Russian Physics Olympiad", "Holics's 300 Creative Physics Problems with Solutions"}


def course(r: dict) -> str:
    """The course code of a course paper: "COL202", "CS21001" (the CS21201/CS21001 papers too) or "CS70"."""
    return next(c for c in COURSES if c in r["subsource"]["course"])


def bank_source(r: dict) -> str:
    return COURSES[course(r)] if r["source"] == COURSE_PAPERS else SOURCES[r["source"]]
# sources the bank already had before this import: none of their rows is added (owner 2026-11-27: "Are there any sources
# that are repeated in the bank and the import? if so, discard those import-questions."), unless the bank held under
# 10% of the import's count ("If there is a CLEAR mismatch (<10%) in the number of questions imported and in the bank,
# add the extra imported questions"): bank vs import, Dekking et al. 360 vs 353, Canadian MO 45 vs 50, Toronto 145 vs 84
# (left out); Tournament of Towns 35 vs 480 (its rows the bank lacks are added).
IN_BANK = {"Dekking et al.'s A Modern Introduction to Probability and Statistics", CMO_,
           "University of Toronto Mathematics Competitions"}
# a same_problem_as group keeps its competition's row before a camp sheet's copy
COLLECTION_RANK = {"CMO": 0, "tott": 1, "torontoolymon": 2, "CIMO": 9}


IMG_RE = re.compile(r"\\includegraphics\s*(?:\[([^\]]*)\])?\s*\{([^}]+)\}")
WIDTH_RE = re.compile(r"(?:^|,)\s*width\s*=\s*([\d.]*)\s*\\(?:linewidth|textwidth)")
TRIM_RE = re.compile(r"trim\s*=\s*\{[^}]*\}\s*,\s*clip")


LAYOUT_RE = re.compile(r"\\begin\{adjustbox\}\{[^}]*\}|\\renewcommand\{[^}]*\}\{[^}]*\}|\\(?:begin|end)\{[^}]*\}"
                       r"(?:\[[^\]]*\]|\{[|lcr ]*\})?|\\includegraphics\s*\[[^\]]*\]\{[^}]*\}")


def digits(t: str) -> collections.Counter:
    """The digits of a statement's numbers, layout left out and decimals without trailing zeros: a contest's or a
    book's variants of one problem (junior and senior, the next exercise on the same data) share nearly all their
    words and differ in these, while a copy in other markup (OCR spacing "6 5 6. 8 8", 0.360 for 0.36) does not."""
    t = re.sub(r"(\.\d*?)0+(?!\d)", r"\1", LAYOUT_RE.sub(" ", t))
    return collections.Counter(ch for ch in t if ch.isdigit())


CONTENT_STOP = set("the a an of and to in is are what which that be by for with if on as at it its this from or then let "
                   "prove show find each all any there such".split())


def content_overlap(a: str, b: str) -> float:
    """Jaccard share of two statements' content words (TeX commands and frame words left out). A copy shares most of
    them (the part 2 matches: 0.80 and up); two short statements that only share "Prove that" share none."""
    def words(t: str) -> set[str]:
        return {w for w in re.findall(r"[a-z]+|\d+", re.sub(r"\\[a-zA-Z]+", " ", t).lower())
                if w not in CONTENT_STOP and len(w) > 1}
    wa, wb = words(a), words(b)
    return len(wa & wb) / max(1, len(wa | wb))


def same_problem(a: str, b: str) -> bool:
    """Two statements that share (nearly) all their 5-word shingles are one problem unless each has digits the other
    lacks (a citation or a year added on one side only does not count)."""
    da, db = digits(a), digits(b)
    return not (da - db and db - da)


def subsource(r: dict) -> str | None:
    """The group the problem belongs to (owner 2026-11-23: year, paper or round, chapter; never the problem)."""
    s, col = r["subsource"], r["collection"]
    y = s.get("year")
    src = r["source"]
    if col == "extra_books" and src == COURSE_PAPERS:
        return course(r)
    if col == "extra_books" and src.startswith(("102 Combinatorial", "103 Trigonometry")):
        return s["section"]  # "Introductory Problems", "Advanced Problems"
    if col == "extra_books" and src.startswith("Russian Physics"):
        return f"{y}, {s['round']}"  # "2005, Final stage"
    if col == "extra_books" and src.startswith("300 Creative"):
        return f"Chapter {s.get('chapter') or 4}"  # Optics, the fourth chapter, prints no number
    if col == "extra_books" and s.get("chapter"):  # Castañeda et al., Howell, Meshalkin
        return f"Chapter {s['chapter']}"
    if col == "uncategorized_books":
        if r["source"].startswith("400 Solved"):  # exercises 1-64 open the book under Topic 1, whose title page it lacks
            return f"Topic {s.get('topic') or 1}"
        return f"Chapter {s['chapter']}" if s.get("chapter") else None
    parts = [str(y)] if y else []
    if col == "CIMO":
        where = " ".join(str(s.get(k) or "") for k in ("event", "document", "season")).lower()
        camp = "Winter Camp" if "winter" in where else "Summer Camp" if "summer" in where else None
        parts += [camp] if camp else []
    elif col == "tott":
        parts += [s["season"], s["paper"]]
    elif col == "europeanmathematical_cup":
        parts += [s["category"]]
    elif col == "simon_marais":
        parts += [s["section"]]
    elif col == "unsw_school_comp":
        parts += [s["division"]]
    elif col == "purdue_POW":
        parts += [s["season"]]
    return ", ".join(parts) or None


def graphic(opts: str | None, name: str) -> str:
    """\\includegraphics in the bank's style for a copied figure: its width as a share of the text width (the data
    set's [width=w\\linewidth,height=...\\textheight,keepaspectratio]), a trim/clip kept."""
    m = WIDTH_RE.search(opts or "")
    w = min(float(m.group(1) or 1), 1.0) if m else 0.5
    keep = (TRIM_RE.search(opts or "").group(0) + ", ") if TRIM_RE.search(opts or "") else ""
    width = "" if w >= 1 else f"{w:.2f}".rstrip("0").rstrip(".")
    return rf"\includegraphics[{keep}max width={width}\textwidth, alt={{}}]{{{name}}}"


class Figures:
    """The data set's figures, each under its content hash; the texts' \\includegraphics rewritten to them."""

    def __init__(self, data: Path):
        self.data, self.files, self.missing = data, {}, []

    def rewrite(self, t: str, where: str) -> str:
        def one(m: re.Match) -> str:
            path = self.data / m.group(2).strip()
            if not path.is_file():
                self.missing.append(f"{where}: {m.group(2)}")
                return m.group(0)
            name = f"{IMAGE_PREFIX}-{hashlib.sha1(path.read_bytes()).hexdigest()[:16]}{path.suffix.lower()}"
            self.files[name] = path
            return graphic(m.group(1), name)
        return IMG_RE.sub(one, t)


def _group_end(t: str, i: int) -> int:
    """The index after the brace group that opens at t[i] ("{")."""
    depth, k = 0, i
    while k < len(t):
        if t[k] == "\\":
            k += 2  # an escaped character (\{, \}, \\) opens or closes nothing
            continue
        depth += {"{": 1, "}": -1}.get(t[k], 0)
        if depth == 0:
            return k + 1
        k += 1
    return -1


BIG_GROUP_RE = re.compile(r"(\\[bB]igg?[lrm]?)\s*\{(\\[a-zA-Z]+|\\.|[^{}\\])\}")
ARRAY_SPEC_RE = re.compile(r"(\\begin\{array\}\{)((?:[^{}]|\{[^{}]*\}|\{[^{}]*\{[^{}]*\}[^{}]*\})*)\}")
STAR_RE = re.compile(r"\*\{(\d+)\}\{([^{}]*)\}")


def expand_columns(t: str) -> str:
    """An array's column spec as KaTeX reads it: *{17}{c} (which KaTeX cannot parse) written out as 17 c's."""
    return ARRAY_SPEC_RE.sub(lambda m: m.group(1) + STAR_RE.sub(lambda s: s.group(2) * int(s.group(1)), m.group(2)) + "}", t)


def plain_cells(t: str) -> str:
    """Table cells as the app's preamble and web view can show them: \\multirow{n}{width}{text} (the multirow package,
    which neither loads) becomes its text, left in the first of the rows it spanned."""
    while (i := t.find("\\multirow{")) >= 0:
        k, args = i + len("\\multirow"), []
        for _ in range(3):
            end = _group_end(t, k) if k < len(t) and t[k] == "{" else -1
            if end < 0:
                return t
            args.append(t[k + 1:end - 1])
            k = end
        t = t[:i] + args[2] + t[k:]
    return t


def title(t: str) -> str:
    """A solution's title as a heading: plain text from the document ("Solution #2", "Solution 1 [Y. Zhao]"), its
    TeX specials escaped and the closing punctuation left to the heading."""
    return re.sub(r"(?<!\\)([#%&_$])", r"\\\1", t.strip().rstrip(".:"))


def solution_text(r: dict) -> str | None:
    sols = [s for s in r["solutions"] if (s.get("tex") or "").strip()]
    if not sols:
        return None
    if len(sols) == 1 and sols[0]["title"].strip().lower() in ("solution", "solution.", "answer"):
        parts = [sols[0]["tex"].strip()]
    else:
        parts = [rf"\textbf{{{title(s['title'])}.}}" + "\n" + s["tex"].strip() for s in sols]
    notes = (r.get("notes") or "").strip()
    if notes:
        parts.append(notes if re.match(r"\\text(?:it|bf)\{", notes) else r"\textit{Remark.} " + notes)
    return "\n\n".join(parts)


def load(data: Path) -> tuple[list[dict], dict[str, str], Figures]:
    """The rows to import (before the bank check), what was left out and why, and the figures they use."""
    raw = [json.loads(line) for line in (data / "questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    left: dict[str, str] = {}
    by_id = {r["id"]: r for r in raw}
    for r in raw:
        if r["subsource"].get("language", "en") != "en":  # owner 2026-11-27: "Delete non-english questions"
            left[r["id"]] = f"not in English ({r['subsource']['language']})"
        elif bank_source(r) in IN_BANK:
            left[r["id"]] = "source already in the bank"
    # same_problem_as: one row of each group
    def rank(r: dict) -> tuple:
        return (not r["solutions"], COLLECTION_RANK.get(r["collection"], 5), raw.index(r))
    for r in raw:
        if r["id"] in left or not r.get("same_problem_as"):
            continue
        group = [r] + [by_id[x] for x in r["same_problem_as"] if x in by_id and x not in left]
        best = min(group, key=rank)
        if best is not r:
            left[r["id"]] = f"same problem as {best['id']}"
    keep = [r for r in raw if r["id"] not in left]
    # repeats the data set does not name: the one with a solution (else the first) stays. Only a full match counts
    # here: a book's and a contest's variants (junior and senior, the next exercise on the same data) share 85-95%
    index: dict[str, set[int]] = collections.defaultdict(set)
    sh = [shingles(r["question"]) for r in keep]
    order = sorted(range(len(keep)), key=lambda i: rank(keep[i]))
    kept_idx: list[int] = []
    for i in order:
        hits = collections.Counter(j for g in sh[i] for j in index.get(g, ()))
        if hits:
            j, n = hits.most_common(1)[0]
            if n == len(sh[i]) >= 4 and same_problem(keep[i]["question"], keep[j]["question"]):
                left[keep[i]["id"]] = f"repeat of {keep[j]['id']}"
                continue
        kept_idx.append(i)
        for g in sh[i]:
            index[g].add(i)
    figs = Figures(data)

    def fix(t: str, where: str) -> str:  # \Big{(}: KaTeX takes a sized delimiter only bare, \Big(
        return expand_columns(BIG_GROUP_RE.sub(r"\1\2", plain_cells(figs.rewrite(t, where))))

    rows = []
    for i in sorted(kept_idx):
        r = keep[i]
        source = bank_source(r)
        sol = solution_text(r)
        notes = (r.get("notes") or "").strip()
        row = {
            "potd": f"{SET} {r['id']}", "set": SET, "idx": r["id"], "orig": r["collection"], "source": source,
            "subsource": subsource(r),
            "latexcode": fix(r["question"].strip(), r["id"]),
            "answer": fix(r["answer"].strip(), r["id"]) if (r.get("answer") or "").strip() else None,
            "solution": fix(sol, r["id"]) if sol else None,
            "hints": fix(notes, r["id"]) if notes and not sol else None,
            "more_hints": None, "ref_solution": "",
            "group": "subject" if source in PHYSICS else "math", "effort": None,
        }
        row["image"] = sorted({n for t in (row["latexcode"], row["answer"], row["solution"], row["hints"]) if t
                               for n in re.findall(rf"\{{({IMAGE_PREFIX}-[0-9a-f]{{16}}\.\w+)\}}", t)})
        rows.append(row)
    return rows, left, figs


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--only", help="the rows of this (bank) source only")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    p.add_argument("--bank-matches", type=Path, help="JSON {\"matches\": {data set id: bank question id}}: rows the bank "
                   "holds reworded (the text check misses them), left out as bank duplicates")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, left, figs = load(a.data)
    if a.only:  # a source added after the first apply: its rows only, the rest are in the bank already
        rows = [r for r in rows if r["source"] == a.only]
        left = {k: v for k, v in left.items() if v.startswith("same problem") or v.startswith("repeat")}
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    variants = {}
    for k, (q, _share) in list(dup.items()):  # a variant with other numbers is a problem of its own
        bank_text = conn.execute("SELECT latexcode FROM questions WHERE question_id = ?", (q,)).fetchone()[0]
        if content_overlap(rows[k]["latexcode"], bank_text) < 0.3:  # a short "Prove that ..." matched on its frame alone
            dup.pop(k)
        elif not same_problem(rows[k]["latexcode"], bank_text):
            variants[k] = dup.pop(k)
    conn.close()
    if a.bank_matches:  # e.g. the extra set's Fermat problems that Omni-MATH holds reworded, without their options
        matched = json.loads(a.bank_matches.read_text(encoding="utf-8"))["matches"]
        for k, r in enumerate(rows):
            if r["idx"] in matched and k not in dup:
                variants.pop(k, None)
                dup[k] = (matched[r["idx"]], 0.0)
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({f'{share:.0%}' if share else 'reworded'})")
    for k, (q, share) in sorted(variants.items()):
        print(f"variant of a bank question, added: {rows[k]['potd']} ~ question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new) + [f"{SET} {x.split(':')[0]}: figure file missing" for x in figs.missing]
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: [x for x in problems if r["potd"] + ":" in x or r["potd"] + " " in x] or [excluded[r["potd"]]]
               for r in new if any(r["potd"] + ":" in x or r["potd"] + " " in x for x in problems) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why],
                                             ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = []
    for key, why_left in left.items():
        print(f"left out: {key}: {why_left}")
    print(json.dumps({"rows": len(rows) + len(left), "left_out": collections.Counter(re.sub(r" [^ ]*/.*| \(.*", "", v)
                                                                                     for v in left.values()),
                      "in_bank": len(dup), "to_add": len(new), "check_problems": len(problems),
                      "by_source": collections.Counter(r["source"] for r in new),
                      "with_solution": sum(bool(r["solution"]) for r in new), "with_answer": sum(bool(r["answer"]) for r in new),
                      "with_hints": sum(bool(r["hints"]) for r in new), "with_figures": sum(bool(r["image"]) for r in new),
                      "figure_files": len({n for r in new for n in r["image"]})},
                     ensure_ascii=False, indent=1))
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("extraction")
    TEXIMAGES.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in sorted({n for r in new for n in r["image"]}):  # figures, before their questions exist
        if not (TEXIMAGES / name).exists():
            shutil.copy2(figs.files[name], TEXIMAGES / name)
            copied += 1
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
            w.writerow(["question_id", "set", "number", "collection", "bank_duplicate"])
        w.writerows((q, SET, r["idx"], r["orig"], "") for q, r in added)
        w.writerows(("", SET, rows[k]["idx"], rows[k]["orig"], q) for k, (q, _) in sorted(dup.items()))
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; "
          f"figures copied={copied}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
