"""Apply the rewrites that make questions self-contained (see taxonomy/tools/missing_refs.py).

Rewrite proposals live in app/data/appdata/missing_refs/out/*.json, one object per question:
    {"qid", "status": "rewritten" | "no_change" | "unresolved", "latexcode", "images", "notes"}
with cropped figures in app/data/appdata/missing_refs/images/mref-<qid>-<n>.png.

    python -m app.tools.apply_missing_refs                 # check every out/*.json, report, write nothing
    python -m app.tools.apply_missing_refs white-01 ...    # only these chunks
    python -m app.tools.apply_missing_refs --apply ...     # back up the DB, copy images, update rows

Applying updates latexcode and latex_hash only (answers and solutions are untouched) and records the old
text in missing_refs/applied.jsonl, so a rewrite can be undone. Images are copied to teximages/ only
(app/data/appdata is not in git).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from app.persistence.ingest.seed import latex_hash

ROOT = Path(__file__).resolve().parents[2]
APPDATA = ROOT / "app" / "data" / "appdata"
DB = APPDATA / "amplify.db"
WORK = APPDATA / "missing_refs"
TEXIMAGES = APPDATA / "teximages"

sys.path.insert(0, str(ROOT / "taxonomy" / "tools"))
from missing_refs import FIX, analyse  # noqa: E402

GRAPHIC = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}")
BANNED = re.compile(r"\\(?:ref|eqref|label|cite|pageref)\{|\\begin\{lstlisting\}|\\usepackage")


def image_exists(name: str) -> bool:
    if (WORK / "images" / f"{name}.png").exists():
        return True
    return any((TEXIMAGES / f"{name}{ext}").exists() for ext in ("", ".jpg", ".png", ".jpeg"))


def balance(tex: str) -> dict[str, object]:
    """Structural counts; a rewrite must not make any of them worse than the original was."""
    # "\\[0pt]" is a line break with spacing, not display math: skip a delimiter preceded by a backslash
    def count(d: str) -> int:
        return len(re.findall(r"(?<!\\)" + re.escape(d), tex))

    begins = re.findall(r"\\begin\{([^}]*)\}", tex)
    ends = re.findall(r"\\end\{([^}]*)\}", tex)
    return {
        # "\{" and "\}" are literal braces (e.g. \left\{ ... \right.), not grouping
        "braces": count("{") - count("}"),
        "environments": sorted(set(begins) ^ set(ends)) + sorted(e for e in set(begins) if begins.count(e) != ends.count(e)),
        "inline math": count("\\(") - count("\\)"),
        "display math": count("\\[") - count("\\]"),
        "dollars": count("$") % 2,  # "\$" is a literal dollar sign
    }


def problems(item: dict, old: str) -> list[str]:
    """Hard errors that block applying this rewrite."""
    tex = item.get("latexcode") or ""
    errs = []
    if not tex.strip():
        return ["empty latexcode"]
    b_new, b_old = balance(tex), balance(old)
    for k in b_new:
        new, was = b_new[k], b_old[k]
        worse = bool(set(new) - set(was)) if isinstance(new, list) else abs(new) > abs(was) or (new and new != was)
        if worse:
            errs.append(f"{k} unbalanced: {was!r} before, {new!r} after")
    if BANNED.search(tex):
        errs.append("uses \\ref/\\label/\\cite/lstlisting/\\usepackage")
    for name in GRAPHIC.findall(tex):
        if not image_exists(name):
            errs.append(f"missing image {name}")
    for name in item.get("images") or []:
        if name not in tex:
            errs.append(f"image {name} listed but not used")
    if tex.strip() == old.strip():
        errs.append("text unchanged")
    return errs


def load(chunks: list[str]) -> list[tuple[str, dict]]:
    files = [WORK / "out" / f"{c}.json" for c in chunks] if chunks else sorted((WORK / "out").glob("*.json"))
    out = []
    for f in files:
        for item in json.loads(f.read_text(encoding="utf-8")):
            out.append((f.stem, item))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chunks", nargs="*")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)

    conn = sqlite3.connect(DB)
    items = load(args.chunks)
    good, blocked, counts, preexisting = [], [], {}, []
    for chunk, it in items:
        counts[it["status"]] = counts.get(it["status"], 0) + 1
        if it["status"] != "rewritten":
            continue
        row = conn.execute("SELECT latexcode FROM questions WHERE question_id = ?", (it["qid"],)).fetchone()
        if row is None:
            blocked.append((chunk, it["qid"], ["question not in DB"]))
            continue
        errs = problems(it, row[0])
        if errs:
            blocked.append((chunk, it["qid"], errs))
            continue
        left = {c: v for c, v in analyse(it["latexcode"]).items() if c in FIX and c not in ("figure_unnumbered",)}
        good.append((chunk, it, row[0], left))
        pre = {k: v for k, v in balance(row[0]).items() if v}
        if pre:
            preexisting.append((chunk, it["qid"], pre))

    print(f"{len(items)} proposals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"{len(good)} rewrites pass the checks, {len(blocked)} blocked")
    for chunk, qid, errs in blocked:
        print(f"  BLOCKED {chunk} {qid}: {'; '.join(errs)}")
    print(f"{len(preexisting)} rewritten questions were already unbalanced before the rewrite (not blocked):")
    for c, q, pre in preexisting:
        print(f"  {c} {q}: {pre}")
    hrefs = [(c, it["qid"]) for c, it, _, _ in good if "\\href" in it["latexcode"] or "\\url" in it["latexcode"]]
    print(f"{len(hrefs)} rewrites contain \\href/\\url (won't compile: no hyperref in the preamble): {hrefs}")
    still = [(c, it["qid"], left) for c, it, _, left in good if left]
    print(f"{len(still)} rewrites still match a reference pattern (review; often a figure label that now has its caption):")
    for c, q, left in still[:60]:
        print(f"  {c} {q}: {left}")

    if not args.apply:
        print("dry run; pass --apply to write")
        return 0

    existing = {h: q for q, h in conn.execute("SELECT question_id, latex_hash FROM questions")}
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = APPDATA / f"amplify.db.bak-{stamp}-pre-missing-refs"
    dst = sqlite3.connect(backup)
    conn.backup(dst)
    dst.close()
    print(f"backup: {backup.name}")
    log = (WORK / "applied.jsonl").open("a", encoding="utf-8")
    n = 0
    with conn:
        for chunk, it, old, _ in good:
            h = latex_hash(it["latexcode"])
            if h in existing and existing[h] != it["qid"]:
                print(f"  SKIP {it['qid']}: same text as question {existing[h]}")
                continue
            for name in GRAPHIC.findall(it["latexcode"]):
                src = WORK / "images" / f"{name}.png"
                if src.exists():
                    shutil.copy2(src, TEXIMAGES / src.name)
            conn.execute("UPDATE questions SET latexcode = ?, latex_hash = ? WHERE question_id = ?",
                         (it["latexcode"], h, it["qid"]))
            existing[h] = it["qid"]
            log.write(json.dumps({"qid": it["qid"], "chunk": chunk, "at": stamp, "old": old,
                                  "new": it["latexcode"], "notes": it.get("notes", "")}, ensure_ascii=False) + "\n")
            n += 1
    log.close()
    print(f"updated {n} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
