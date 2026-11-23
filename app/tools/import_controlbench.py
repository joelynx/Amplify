"""Import ControlBench (github.com/AGI4Engineering/LLM4Control, ControlBench/ControlBench.tex; no licence, partly
Schaum's-derived; the owner accepts it for private use, 2026-11-23): 147 undergraduate control problems (Laplace
transforms, stability, time response, block diagrams, design, Bode, root locus, Nyquist, margins, Lyapunov,
sensitivity, loop shaping), each with a worked solution in LaTeX.

The caller downloads the repository (zip) and unpacks it under DIR/controlbench; nothing in it is run.
Parsing: every \\subsection is one problem (the number is its place in its \\section); the text before the
"Solution" marker is the statement, the rest (up to the next heading) the worked solution. 19 problems carry a
"% Short Answer:" comment, which becomes the key; the others get an empty key (the worked solution is the
reference; the dataset has no short form for them).
Conversion to the bank's LaTeX: \\( \\) and $$ $$ to $ $ and \\[ \\]; equation / align environments to \\[ \\]
(aligned); the author's macros \\bmat, \\pmat, \\bmtx, \\emtx expanded; comments, \\label, \\ref, \\clearpage,
red colour removed; figure environments taken out (in the solution they are plots of the result). A figure in the
statement: a PNG file in the repo is kept as the question's image (tq-style, ctl-<sha1[:16]>.png, written to
TEXIMAGES on --apply); a problem whose statement figure is a JPEG or EPS is left out. controlbench_fixes.json
holds per-row repairs ("fixes": key, field latexcode / answer / solution, pairs matched exactly once;
"dropped": {key: reason}).

Usage (repo root):
  python -m app.tools.import_controlbench --data DIR --dry-run [--dump rows.json] [--set-aside]
  python -m app.tools.import_controlbench --data DIR --apply
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

from app.tools.import_answer_sets import GRAPHIC, TEXIMAGES, duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "ControlBench"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/controlbench_set_aside.json")  # git-ignored
MIN_SOLUTION = 150

_FIX = json.loads(Path(__file__).with_name("controlbench_fixes.json").read_text(encoding="utf-8"))
FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
SETS: dict[tuple[str, str], str] = {}  # whole-field replacements (hand-written keys for the problems with no short answer)
for _e in _FIX["fixes"]:
    if "set" in _e:
        SETS[(_e["key"], _e["field"])] = _e["set"]
    else:
        FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPPED = dict(_FIX["dropped"])

HEAD_RE = re.compile(r"^\\(section|subsection)\*?\{(.*)\}[ \t]*$", re.M)
SOL_RE = re.compile(r"(?:\\noindent\s*)?\\textbf\{\\textcolor\{red\}\{Solution\s*:?\s*\}\}[ \t]*(?:\\\\)?")
FIGURE_RE = re.compile(r"\\begin\{figure\}.*?\\end\{figure\}", re.S)
GRAPHIC_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}")
SHORT_RE = re.compile(r"^%\s*Short Answer:[ \t]*(.*)$", re.M)


def brace_arg(s: str, i: int) -> int:
    """Index of the } closing the { at i, or -1."""
    depth = 0
    for k in range(i, len(s)):
        if s[k] == "\\":
            continue
        depth += {"{": 1, "}": -1}.get(s[k], 0)
        if depth == 0:
            return k
    return -1


def expand_macro(t: str, name: str, begin: str, end: str) -> str:
    """\\name{body} (the author's one-argument macros) as begin body end."""
    pat = re.compile(r"\\" + name + r"(?![A-Za-z])\s*\{")
    while m := pat.search(t):
        j = brace_arg(t, m.end() - 1)
        if j < 0:
            break
        t = t[:m.start()] + begin + t[m.end():j] + end + t[j + 1:]
    return t


def take_figures(raw: str) -> tuple[str, list[str]]:
    """The text without its figures (figure and minipage environments, bare includegraphics) and their file paths."""
    paths: list[str] = []

    def grab(m: re.Match) -> str:
        paths.extend(GRAPHIC_RE.findall(m.group(0)))
        return ""

    raw = FIGURE_RE.sub(grab, raw)
    raw = re.sub(r"\\\[\s*(?:\\begin\{minipage\}.*?\\end\{minipage\}\s*)+\\\]", grab, raw, flags=re.S)
    raw = re.sub(r"\\begin\{minipage\}.*?\\end\{minipage\}", grab, raw, flags=re.S)
    return GRAPHIC_RE.sub(grab, raw), paths


def clean(t: str) -> str:
    """Author's TeX as the bank's LaTeX (figures already taken out)."""
    t = re.sub(r"(?m)^[ \t]*%.*\n?", "", t)
    t = re.sub(r"(?<!\\)%.*$", "", t, flags=re.M)
    t = re.sub(r"\\begin\{table\}(?:\[[^\]]*\])?", "", t).replace("\\end{table}", "")
    t = re.sub(r"\\(?:clearpage|newpage|noindent|centering|nonumber|bigskip|medskip|smallskip)(?![A-Za-z])", "", t)
    t = re.sub(r"\\(?:label|vspace\*?|hspace\*?)\{[^}]*\}", "", t)
    t = t.replace("\\textcolor{red}", "")
    t = re.sub(r"\\caption\{[^{}]*\}", "", t)
    t = expand_macro(t, "bmat", "\\begin{bmatrix} ", " \\end{bmatrix}")
    t = expand_macro(t, "pmat", "\\begin{pmatrix} ", " \\end{pmatrix}")
    t = t.replace("\\bmtx", "\\begin{bmatrix}").replace("\\emtx", "\\end{bmatrix}")
    t = re.sub(r"(?:Fig\.|Figure)\s*~?\s*\\ref\{[^}]*\}", "the figure", t)
    t = re.sub(r"\\ref\{[^}]*\}", "", t)
    t = t.replace("\\(", "$").replace("\\)", "$")
    t = re.sub(r"\$\$\s*(.*?)\s*\$\$", lambda m: "\\[" + m.group(1) + "\\]", t, flags=re.S)
    t = re.sub(r"\\begin\{equation\*?\}\s*(.*?)\s*\\end\{equation\*?\}", lambda m: "\\[" + m.group(1) + "\\]", t, flags=re.S)
    t = re.sub(r"\\begin\{align\*?\}\s*(.*?)\s*\\end\{align\*?\}",
               lambda m: "\\[\\begin{aligned}" + m.group(1) + "\\end{aligned}\\]", t, flags=re.S)
    t = t.replace("\\hdots", "\\ldots").replace("{enumerate*}", "{enumerate}")
    t = re.sub(r"\\\\[ \t]*(?=\n[ \t]*\n)", "", t)
    t = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    return re.sub(r"(?:\\\\\s*)+$", "", t.strip())


def short_answer(comment: str) -> str:
    """The key from a "% Short Answer:" comment ("" when there is none that is usable)."""
    a = comment.strip()
    if a.upper() in ("NA", "N/A", ""):
        return ""
    parts = re.split(r"\s*\\\\\s*-\s*", a)
    out = []
    for p in parts:
        p = re.sub(r"^-?\s*\\textbf\{For part \(([a-z])\):\}\s*", r"(\1) ", p).strip()
        p = p.strip('" ')
        out.append(p)
    a = "; ".join(out)
    a = a.replace("\\(", "$").replace("\\)", "$")
    a = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", a)
    if "$" not in a and re.search(r"\\[A-Za-z]|[=^_\[]", a):
        a = "$" + a + "$"
    return a.strip()


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    """(rows to import, {key: why left out})."""
    tex = next(iter(sorted(data.rglob("ControlBench.tex"))), None)
    if tex is None:
        raise SystemExit(f"no ControlBench.tex under {data}")
    figs = tex.parent / "figs"
    text = tex.read_text(encoding="utf-8", errors="replace")
    body = text[text.index("\\begin{document}"):]
    heads = list(HEAD_RE.finditer(body))
    rows, left = [], {}
    sec_no, sec_name, n = 0, "", 0
    for k, h in enumerate(heads):
        if h.group(1) == "section":
            sec_no, sec_name, n = sec_no + 1, h.group(2).strip(), 0
            continue
        n += 1
        key = f"{sec_no}.{n}"
        chunk = body[h.end(): heads[k + 1].start() if k + 1 < len(heads) else body.index("\\end{document}")]
        m = SOL_RE.search(chunk)
        if not m:
            left[key] = "no solution marker"
            continue
        stem_raw, sol_raw = chunk[:m.start()], chunk[m.end():]
        short = SHORT_RE.search(sol_raw)
        ans = short_answer(short.group(1)) if short else ""
        stem_raw, stem_figs = take_figures(stem_raw)
        sol_raw, sol_figs = take_figures(sol_raw)
        sol_images: list[tuple[str, bytes]] = []
        for g in sol_figs:  # a PNG plot in the solution stays as an image (after the text); other formats are left out
            f = figs / Path(g).name
            if f.suffix.lower() == ".png" and f.exists():
                png = f.read_bytes()
                sol_images.append(("ctl-" + hashlib.sha1(png).hexdigest()[:16], png))
        if key in DROPPED:
            left[key] = DROPPED[key]
            continue
        image = None
        if stem_figs:
            files = [figs / Path(g).name for g in stem_figs]
            if any(f.suffix.lower() != ".png" or not f.exists() for f in files):
                left[key] = "its statement figure is not a PNG in the repo (" + ", ".join(Path(g).suffix or "?" for g in stem_figs) + ")"
                continue
            image = []
            for f in files:
                png = f.read_bytes()
                image.append(("ctl-" + hashlib.sha1(png).hexdigest()[:16], png))
        latex, sol = clean(stem_raw), clean(sol_raw)
        for fld, val in (("latexcode", latex), ("solution", sol), ("answer", ans)):
            if (key, fld) in SETS:
                val = SETS[(key, fld)]
            for old, new in FIXES.get((key, fld), []):
                if val.count(old) != 1:
                    raise SystemExit(f"FIX {key} {fld}: expected one {old!r}")
                val = val.replace(old, new)
            if fld == "latexcode":
                latex = val
            elif fld == "solution":
                sol = val
            else:
                ans = val
        for name, _ in image or []:
            latex += "\n\n" + GRAPHIC.format(name)
        for name, _ in sol_images:
            sol += "\n\n" + GRAPHIC.format(name)
        image = (image or []) + sol_images or None
        stored = sol if len(sol) >= MIN_SOLUTION else None
        rows.append({"potd": f"{SET} {key}", "set": SET, "idx": key, "orig": "", "source": SET,
                     "subsource": f"{sec_name}, problem {n}", "latexcode": latex, "answer": ans,
                     "solution": stored, "hints": None, "more_hints": None, "ref_solution": sol,
                     "group": "subject", "effort": None, "image": image, "title": h.group(2).strip()})
    return rows, left


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON (images as names)")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, left = load(a.data)
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
        why = {r["potd"]: [x for x in problems if r["potd"] in x] or [excluded[r["potd"]]]
               for r in new if any(r["potd"] in x for x in problems) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([{k: v for k, v in dict(r, problems=why[r["potd"]]).items() if k != "image"}
                                              for r in new if r["potd"] in why], ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = []
    for key, why_left in left.items():
        print(f"left out: {key}: {why_left}")
    print("left out by reason:", json.dumps(collections.Counter(re.sub(r"\(.*", "", v).strip() for v in left.values()), ensure_ascii=False))
    print(json.dumps({"rows": len(rows), "in_bank": len(dup), "to_add": len(new), "check_problems": len(problems),
                      "with_key": sum(bool(r["answer"]) for r in new),
                      "stored_solutions": sum(bool(r["solution"]) for r in new),
                      "images": sum(bool(r["image"]) for r in new)}))
    if a.dump:
        a.dump.write_text(json.dumps([dict(r, image=[n for n, _ in r["image"]] if r["image"] else None) for r in new],
                                     ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("controlbench")
    for r in new:
        for name, png in r["image"] or []:
            (TEXIMAGES / f"{name}.png").write_bytes(png)
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
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
