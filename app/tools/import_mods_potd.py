"""
Import the MODS Problem of the Day sheet
----------------------------------------
Reads a CSV download of the POTD tab of the Math Olympiad Discord Server's "Problem of the
Day" sheet and adds every problem that sources/potd/row_assignments.csv does not skip, with
the sheet's hints, answer and solution. Download the tab fresh (a problem is added every day):
  https://docs.google.com/spreadsheets/d/10X0-CCSv7FenZP1YaKlDSE-PD4LSZAgpzT5Rs9F8hvA/export?format=csv&gid=0
then rebuild the assignments from that same file (sources/potd/scripts/build_map.py).

Source and subsource come from row_assignments.csv: the competition's full name, or its group
when it has fewer than 15 problems (the competition's name then heads the subsource), with year,
paper and problem in the subsource (owner decisions of 2026-11-11 and 2026-11-12). Skipped there:
programming contests and school exams, rows already in the bank or posted twice (hand-reviewed
list in sources/potd/duplicates.csv), and rows scheduled after the download.

Fields:
    Problem Statement   latexcode
    Hint 1, 2, 3        hints (the first one given) and more_hints (JSON list of the rest,
                        NULL when there is one); the quiz shows them as tiers
    Answer              answer
    Solution            solution
D, G and T are not stored: they feed classification and the choice of solving model. The POTD
number and the Solution Link have no bank column; they go to app/data/appdata/mods_potd_map.csv
(git-ignored, beside the DB), one line per imported question.

Repairs on the way in:
  * Windows line ends and trailing spaces go; three or more blank lines become one.
  * Placeholder values are dropped: one-character hints and answers such as "l" or "-", a joke
    hint or answer, links that are not URLs. A Solution cell that is only a URL becomes the
    solution link; solutions that are no solution (jokes, fragments, comments) are dropped by
    "drop" entries in the fixes file, so the pipeline solves those questions.
  * A later hint with an earlier one missing moves up, so the tiers have no gaps.
  * Broken LaTeX and Discord leftovers in single rows are corrected from mods_potd_fixes.json
    (POTD number, field, the text replaced, the reason); two hints and a solution with
    profanity are reworded there too.
  * The server's TeX bot has macros of its own (\\bR, \\bZ, \\floor{x}, \\ord, \\lcm...); they are
    written out, since neither KaTeX nor the app's preamble defines them.
  * For XeLaTeX, which the app's PDFs and the pipeline's judge use: the enumerate package's
    \\begin{enumerate}[(a)] becomes enumitem's [label=(\\alph*)], #, %, & and _ in URLs are
    escaped, a line break alone at the start of a paragraph is dropped, and an answer in bare
    math gets its $...$.
Checked before writing: braces, $ and \\( \\[ pairs, environments, leftover macros. The
dry run of 2026-11-12 was also rendered with the app's renderLatex (0 KaTeX errors in 7,695
fields) and compiled in one document with the app's preamble (statements, solutions and
answers: 0 XeLaTeX errors).

--rename-aime renames the bank's "AIME" source (748 rows) to "American Invitational Mathematics
Examination", the full name POTD's own AIME rows are filed under, and rewrites its subsources in
POTD's order: "AIME II - 2008" becomes "2008, AIME II" and "AIME  - 1983" becomes "1983".

Rows go in as topic/branch/subtopic "Uncategorized", type NULL, no embeddings (run
app/tools/reembed.py later). Idempotent on latex_hash. --apply backs the DB up first.

Usage (repo root):
  python -m app.tools.import_mods_potd --csv <potd.csv> --dry-run [--dump out.json]
  python -m app.tools.import_mods_potd --csv <potd.csv> --apply
  python -m app.tools.import_mods_potd --rename-aime --dry-run | --apply
  python -m app.tools.import_mods_potd --csv <potd.csv> --update-solutions --dry-run | --apply
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

from app.persistence.ingest.seed import latex_hash

UNCATEGORIZED = "Uncategorized"
DB_PATH = Path("app/data/appdata/amplify.db")
MAP_PATH = Path("app/data/appdata/mods_potd_map.csv")
ASSIGNMENTS = Path("sources/potd/row_assignments.csv")
FIXES_PATH = Path(__file__).with_name("mods_potd_fixes.json")

HINTS = ("Hint 1", "Hint 2", "Hint 3")
# Values that hold no hint, answer or solution (checked after stripping, case-insensitively).
JUNK = {
    "hint": {"l", "a", "\\[", "skibidi"},
    "answer": {"-", "blud really thought there was an answer", "solved by hay. qed."},
    "solution": {"q", "-"},
}

# Macros of the server's TeX bot (as in evan.sty) that neither KaTeX nor the app's preamble define.
MACROS = {
    "bR": r"\mathbb{R}", "bZ": r"\mathbb{Z}", "bQ": r"\mathbb{Q}", "bN": r"\mathbb{N}", "bC": r"\mathbb{C}",
    "RR": r"\mathbb{R}", "ord": r"\operatorname{ord}", "lcm": r"\operatorname{lcm}", "hdots": r"\ldots",
    "ii": r"\item",
}
# (?<!\\)((?:\\\\)*) keeps a \\ line break that happens to be followed by letters ("\\ii)") whole.
CMD = r"(?<!\\)((?:\\\\)*)\\"
MACRO_RE = re.compile(CMD + r"(" + "|".join(MACROS) + r")(?![A-Za-z])")
BRACKETS = {"floor": (r"\lfloor ", r" \rfloor"), "ceil": (r"\lceil ", r" \rceil")}
BRACKET_RE = re.compile(CMD + r"(floor|ceil)\s*\{")
# Left after the expansion only when a row needs a fix of its own (typos such as \infy included).
UNDEFINED_RE = re.compile(CMD + r"(" + "|".join([*MACROS, *BRACKETS, "func", "infy", "agle", "cross", "arrow", "dotsa",
                                                  "DeclareFontFamily", "DeclareSymbolFont", "DeclareMathAccent"])
                          + r")(?![A-Za-z])")

URL_ONLY_RE = re.compile(r"https?://\S+")

AIME_OLD, AIME_NEW = "AIME", "American Invitational Mathematics Examination"
AIME_SUB_RE = re.compile(r"^AIME\s*(I{1,2})?\s*-\s*(\d{4})$")


def _clean(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _value(text: str, kind: str) -> str | None:
    t = _clean(text)
    return None if not t or t.lower() in JUNK[kind] else t


def _answer(text: str) -> str | None:
    """The answer as text-mode LaTeX, the bank's form: bare math ("n\\geq 1005") gets its $...$."""
    a = _value(text, "answer")
    if a and not re.search(r"\$|\\\(|\\\[|\\begin\{", a) and re.search(r"[\\^_{}]", a):
        a = f"${a}$"
    return a


def _source_cell(text: str) -> str:
    """The sheet's Source as row_assignments.csv writes it."""
    return text.replace("\n", " | ")


def load_assignments(path: Path = ASSIGNMENTS) -> dict[str, dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {r["potd_number"]: r for r in csv.DictReader(f)}


def parse(csv_path: Path, assignments: dict[str, dict]) -> tuple[list[dict], list[str]]:
    """The rows to import, and the reasons any sheet row could not be matched up."""
    log: list[str] = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        sheet = [r for r in csv.DictReader(f) if r["Problem Statement"].strip()]
    out = []
    for r in sheet:
        num = r["/f"].strip()
        a = assignments.get(num)
        if a is None:
            log.append(f"POTD {num}: not in row_assignments.csv (rebuild it from this download)")
            continue
        if _source_cell(r["Source"]) != a["source_as_in_sheet"]:
            log.append(f"POTD {num}: Source changed since the assignments were built: {r['Source'][:60]!r}")
            continue
        if a["skip"]:
            continue
        tiers = [h for h in (_value(r[k], "hint") for k in HINTS) if h]
        link = r["Solution Link"].strip()
        solution = _value(r["Solution"], "solution")
        if solution and URL_ONLY_RE.fullmatch(solution):  # a link in the Solution column
            link = link if link.startswith("http") else solution
            solution = None
        out.append({
            "potd": num, "date": r["Date"].strip(),
            "source": a["source"], "subsource": a["subsource"] or None,
            "latexcode": _clean(r["Problem Statement"]),
            "hints": tiers[0] if tiers else None,
            "more_hints": json.dumps(tiers[1:], ensure_ascii=False) if len(tiers) > 1 else None,
            "answer": _answer(r["Answer"]),
            "solution": solution,
            "link": link if link.startswith("http") else None,
        })
    missing = set(assignments) - {r["/f"].strip() for r in sheet}
    if missing:
        log.append(f"{len(missing)} assigned rows are not in this download: {sorted(missing, key=int)[:10]}")
    return out, log


def _fix_text(fix: dict, texts: list[str]) -> list[str]:
    """`old` replaced by `new` once across the texts, or `regex` replaced `count` times
    (default 1); any other number of matches stops the import."""
    if "regex" in fix:
        rx, want = re.compile(fix["regex"], re.M), fix.get("count", 1)
        hits = sum(len(rx.findall(t)) for t in texts)
        out = [rx.sub(lambda m: fix["new"], t) for t in texts]
    else:
        want, hits = 1, sum(t.count(fix["old"]) for t in texts)
        out = [t.replace(fix["old"], fix["new"]) for t in texts]
    if hits != want:
        what = fix.get("regex") or fix["old"]
        raise SystemExit(f"FIX {fix['potd']} {fix['field']}: expected {want} matches, found {hits}: {what[:60]!r}")
    return [_clean(t) for t in out]


def apply_fixes(rows: list[dict]) -> None:
    by_num = {r["potd"]: r for r in rows}
    for fix in json.loads(FIXES_PATH.read_text(encoding="utf-8")):
        r = by_num.get(str(fix["potd"]))
        if r is None:
            continue  # a skipped row
        fld = fix["field"]
        if fix.get("drop"):  # a value that is no solution, hint or answer at all
            if not r[fld]:
                raise SystemExit(f"FIX {fix['potd']} {fld}: nothing to drop")
            r[fld] = None
        elif fld == "more_hints":
            tiers = _fix_text(fix, json.loads(r["more_hints"]))
            r["more_hints"] = json.dumps(tiers, ensure_ascii=False)
        else:
            r[fld] = _fix_text(fix, [r[fld] or ""])[0] or None


def expand_macros(text: str) -> str:
    """The bot's macros written out: \\bR as \\mathbb{R}, \\floor{x} as \\lfloor x \\rfloor, and a
    \\newline glued to the next word ("\\newlineProof") split from it."""
    text = MACRO_RE.sub(lambda m: m.group(1) + MACROS[m.group(2)], text)
    while m := BRACKET_RE.search(text):
        depth, k = 1, m.end()
        while k < len(text) and depth:
            if text[k] == "\\":
                k += 2
                continue
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        if depth:
            break  # unbalanced; check() reports the leftover macro
        left, right = BRACKETS[m.group(2)]
        text = text[:m.start()] + m.group(1) + left + text[m.end():k - 1] + right + text[k:]
    return re.sub(CMD + r"newline(?=[A-Za-z])", r"\1\\newline ", text)


ENUM_OPT_RE = re.compile(r"\\begin\{enumerate\}\s*\[([^\]=]*)\]")
COUNTERS = {"a": r"\alph*", "A": r"\Alph*", "i": r"\roman*", "I": r"\Roman*", "1": r"\arabic*"}


def enumitem_labels(text: str) -> str:
    """The enumerate package's label syntax, \\begin{enumerate}[(a)], in enumitem's form,
    [label=(\\alph*)]: the app's preamble loads enumitem, which stops on the short form. As in
    the enumerate package, the first a, A, i, I or 1 is the counter."""
    def label(m: re.Match) -> str:
        opt = m.group(1)
        k = next((j for j, ch in enumerate(opt) if ch in COUNTERS), None)
        if k is None or opt.strip() in ("resume", "resume*", "nosep", "noitemsep"):
            return m.group(0)
        return rf"\begin{{enumerate}}[label={opt[:k]}{COUNTERS[opt[k]]}{opt[k + 1:]}]"
    return ENUM_OPT_RE.sub(label, text)


URL_RE = re.compile(r"https?://[^\s{}]+")
PARAGRAPH_BREAK_RE = re.compile(r"(\n[ \t]*\n)[ \t]*(?:\\newline|\\\\)[ \t]*(?=\n|$)")


def pdf_safe(text: str) -> str:
    """Two things the web view takes but XeLaTeX stops on: #, %, & and _ in a URL (escaped; % would
    silently drop the rest of the line), and a line break alone at the start of a paragraph
    ("There's no line here to end"; dropped)."""
    text = URL_RE.sub(lambda m: re.sub(r"(?<!\\)([#%&_])", r"\\\1", m.group(0)), text)
    return PARAGRAPH_BREAK_RE.sub(r"\1", text)


def expand_all(rows: list[dict]) -> None:
    def fix(t: str) -> str:
        return pdf_safe(enumitem_labels(expand_macros(t)))
    for r in rows:
        for k in ("latexcode", "hints", "answer", "solution"):
            if r[k]:
                r[k] = fix(r[k])
        if r["more_hints"]:
            r["more_hints"] = json.dumps([fix(t) for t in json.loads(r["more_hints"])], ensure_ascii=False)


def _texts(r: dict) -> list[tuple[str, str]]:
    out = [(k, r[k]) for k in ("latexcode", "hints", "answer", "solution") if r[k]]
    if r["more_hints"]:
        out += [(f"hint {i}", t) for i, t in enumerate(json.loads(r["more_hints"]), 2)]
    return out


def check(rows: list[dict]) -> list[str]:
    problems = []
    for r in rows:
        if not r["source"]:
            problems.append(f"{r['potd']}: no source")
        for fld, t in _texts(r):
            where = f"{r['potd']} {fld}"
            depth = dollars = 0
            k = 0
            while k < len(t):
                if t[k] == "\\":
                    k += 2
                    continue
                depth += {"{": 1, "}": -1}.get(t[k], 0)
                dollars += t[k] == "$"
                if depth < 0:
                    break
                k += 1
            if depth != 0:
                problems.append(f"{where}: unbalanced braces")
            begins = re.findall(r"\\begin\{([^}]+)\}", t)
            ends = re.findall(r"\\end\{([^}]+)\}", t)
            if sorted(begins) != sorted(ends):
                problems.append(f"{where}: environments {sorted(begins)} vs {sorted(ends)}")
            if (t.count("\\(") - t.count("\\\\(") != t.count("\\)") - t.count("\\\\)")
                    or t.count("\\[") - t.count("\\\\[") != t.count("\\]") - t.count("\\\\]")):
                problems.append(f"{where}: unbalanced \\( \\) or \\[ \\]")
            if dollars % 2:
                problems.append(f"{where}: odd number of $")
            if re.search(r"<@!?\d+>|```", t):
                problems.append(f"{where}: Discord markup")
            if m := UNDEFINED_RE.search(t):
                problems.append(f"{where}: undefined macro \\{m.group(2)}")
    return problems


def backup_db(label: str) -> Path:
    dest = DB_PATH.with_name(f"{DB_PATH.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}-{label}")
    src, out = sqlite3.connect(DB_PATH), sqlite3.connect(dest)
    src.backup(out)
    out.close()
    src.close()
    print(f"backup={dest}")
    return dest


def apply(rows: list[dict]) -> None:
    backup_db("mods-potd")
    conn = sqlite3.connect(DB_PATH)
    mapped: list[tuple] = []
    try:
        existing = {h: q for q, h in conn.execute("SELECT question_id, latex_hash FROM questions")}
        added = skipped = 0
        for r in rows:
            h = latex_hash(r["latexcode"])
            if h in existing:
                skipped += 1
            else:
                cur = conn.execute(
                    """
                    INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                           source, subsource, answer, solution, hints, more_hints, latex_hash)
                    VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"],
                     r["answer"], r["solution"], r["hints"], r["more_hints"], h),
                )
                existing[h] = cur.lastrowid
                added += 1
            mapped.append((existing[h], r["potd"], r["date"], r["link"] or ""))
        conn.commit()
    finally:
        conn.close()
    with MAP_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["question_id", "potd_number", "date", "solution_link"])
        w.writerows(mapped)
    print(f"added={added} skipped={skipped} map={MAP_PATH} ({len(mapped)} lines)")


def update_solutions(rows: list[dict], dry_run: bool) -> None:
    """Rewrite the solution of imported questions whose parsed solution changed (a drop fix, a link
    that was in the Solution column), and their links in the map. Only `solution` is touched: the
    pipeline may have filled hints or answers since the import, and those stay."""
    by_potd = {r["potd"]: r for r in rows}
    with MAP_PATH.open(encoding="utf-8", newline="") as f:
        mapped = list(csv.DictReader(f))
    conn = sqlite3.connect(DB_PATH)
    try:
        changes = []
        for m in mapped:
            r = by_potd.get(m["potd_number"])
            if r is None:
                continue
            (old,) = conn.execute("SELECT solution FROM questions WHERE question_id = ?", (int(m["question_id"]),)).fetchone()
            if old != r["solution"]:
                changes.append((r["solution"], int(m["question_id"])))
                print(f"  {m['question_id']} (POTD {r['potd']}): solution {'dropped' if r['solution'] is None else 'rewritten'}")
            m["solution_link"] = r["link"] or ""
        print(f"solutions to change={len(changes)}")
        if dry_run or not changes:
            return
        conn.close()
        backup_db("mods-potd-solutions")
        conn = sqlite3.connect(DB_PATH)
        conn.executemany("UPDATE questions SET solution = ? WHERE question_id = ?", changes)
        conn.commit()
        with MAP_PATH.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["question_id", "potd_number", "date", "solution_link"])
            w.writeheader()
            w.writerows(mapped)
        print(f"updated={len(changes)} map rewritten")
    finally:
        conn.close()


def rename_aime(dry_run: bool) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT question_id, subsource FROM questions WHERE source = ?", (AIME_OLD,)).fetchall()
        new = []
        for qid, sub in rows:
            m = AIME_SUB_RE.match(sub or "")
            if not m:
                print(f"  PROBLEM question {qid}: subsource {sub!r} not in the 'AIME II - 2008' form")
                return 1
            paper, year = m.groups()
            new.append((f"{year}, AIME {paper}" if paper else year, qid))
        print(f"aime_rows={len(rows)} e.g. {rows[0][1]!r} -> {new[0][0]!r}, {rows[-1][1]!r} -> {new[-1][0]!r}")
        if dry_run:
            return 0
        conn.close()
        backup_db("rename-aime")
        conn = sqlite3.connect(DB_PATH)
        conn.executemany(f"UPDATE questions SET source = '{AIME_NEW}', subsource = ? WHERE question_id = ?", new)
        conn.commit()
        print(f"renamed={len(new)}")
    finally:
        conn.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", type=Path, help="a CSV download of the POTD tab")
    p.add_argument("--rename-aime", action="store_true", help="rename the bank's AIME source instead")
    p.add_argument("--update-solutions", action="store_true",
                   help="rewrite only the solution column (and map links) of rows already imported")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    p.add_argument("--dump", type=Path, help="write the parsed rows as JSON")
    args = p.parse_args(argv)

    if args.rename_aime:
        return rename_aime(args.dry_run)
    if not args.csv:
        p.error("--csv is required")
    rows, log = parse(args.csv, load_assignments())
    apply_fixes(rows)
    expand_all(rows)
    for line in log:
        print("  " + line)
    problems = check(rows)
    for line in problems:
        print("  PROBLEM " + line)
    print(f"questions={len(rows)} with_hints={sum(1 for r in rows if r['hints'])} "
          f"tiers2+={sum(1 for r in rows if r['more_hints'])} with_answer={sum(1 for r in rows if r['answer'])} "
          f"with_solution={sum(1 for r in rows if r['solution'])} problems={len(problems)}")
    if args.dump:
        args.dump.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    if args.apply and (problems or log):
        print("refusing to write with problems")
        return 1
    if args.update_solutions:
        update_solutions(rows, args.dry_run)
    elif args.apply:
        apply(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
