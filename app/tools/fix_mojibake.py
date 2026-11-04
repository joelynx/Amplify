"""Repair mojibake in question text: UTF-8 bytes that were decoded as Windows-1252/Latin-1
("KÃ¡rmÃ¡n" -> "Kármán", "LÃ©vy" -> "Lévy", "â€™" -> "’").

    python -m app.tools.fix_mojibake            # report what would change, write nothing
    python -m app.tools.fix_mojibake --apply    # back up the DB, then write the repairs

A run of characters that all map to single bytes under Windows-1252 (or Latin-1) is re-encoded to bytes
and decoded as UTF-8; the run is replaced only when that decode succeeds and yields non-Latin-1-garbage
text. Fragments where bytes were lost (e.g. "Polâs" for "Pol’s") cannot be reversed this way: they are
listed as "unrepaired" and handled by MANUAL below.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from app.persistence.ingest.seed import latex_hash

ROOT = Path(__file__).resolve().parents[2]
APPDATA = ROOT / "app" / "data" / "appdata"
DB = APPDATA / "amplify.db"
FIELDS = ("latexcode", "solution", "generated_solution", "answer", "hints", "solution_outline", "instructions")

# Windows-1252 bytes 0x80-0x9F as Unicode; the undefined ones fall back to the Latin-1 control characters
CP1252_HIGH = {c: b for b in range(0x80, 0xA0) for c in [bytes([b]).decode("cp1252", errors="ignore")] if c}
SUSPECT = re.compile(r"[Â-ô][\u0080-¿ŒœŠšŸŽžƒˆ˜"
                     r"–—‘-„†-•…‰‹›€™]|[\u0080-\u009f]")
RUN = re.compile(r"[\u0080-ÿŒœŠšŸŽžƒˆ˜–—"
                 r"‘-„†-•…‰‹›€™]{2,}")
C1 = re.compile(r"[\u0080-\u009f]")
# irreversible fragments seen in the DB, fixed by hand (lost bytes)
MANUAL = {
    "Polâs": "Pol's",
    "CesÃ ro": "Cesàro",
    "KÃ¡rmÃ¡n": "Kármán",
}


# after decoding, a few rows turn out to hold OCR misreadings rather than real characters
ROW_FIXUPS = {
    12727: [("в", "B"), ("В", "B"), ("М", "M")],   # "B ... M" (bachelor/model) read as Cyrillic
    12288: [("一", "-")],                                      # minus sign in a sign table read as CJK "one"
    1213: [(" \U0001f603", ""), ("\U0001f603", "")],               # emoji in a forum-style solution
}


def to_bytes(s: str) -> bytes | None:
    out = bytearray()
    for ch in s:
        o = ord(ch)
        if o < 0x100:
            out.append(o)
        elif ch in CP1252_HIGH:
            out.append(CP1252_HIGH[ch])
        else:
            return None
    return bytes(out)


def repair(text: str) -> str:
    for bad, good in MANUAL.items():
        text = text.replace(bad, good)

    def fix_run(m: re.Match) -> str:
        run = m.group(0)
        b = to_bytes(run)
        if b is None:
            return run
        try:
            fixed = b.decode("utf-8")
        except UnicodeDecodeError:
            # try the longest decodable prefix pieces character by character
            return run
        return fixed

    prev = None
    while prev != text:  # double-encoded text needs two passes
        prev = text
        text = RUN.sub(fix_run, text)
    # a C1 control character left over is a Windows-1252 byte read as Latin-1 (0x92 is ’, 0x97 is —)
    return C1.sub(lambda m: bytes([ord(m.group(0))]).decode("cp1252", errors="ignore") or m.group(0), text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    conn = sqlite3.connect(DB)
    changes, leftovers = [], []
    for row in conn.execute(f"SELECT question_id, {', '.join(FIELDS)} FROM questions"):
        qid, vals = row[0], row[1:]
        for field, val in zip(FIELDS, vals):
            if not val or not SUSPECT.search(val):
                continue
            new = repair(val)
            for bad, good in ROW_FIXUPS.get(qid, []):
                new = new.replace(bad, good)
            if new != val:
                changes.append((qid, field, val, new))
            rest = SUSPECT.findall(new)
            if rest:
                leftovers.append((qid, field, sorted(set(rest))))
    print(f"{len(changes)} field values would change in {len({c[0] for c in changes})} questions")
    for qid, field, old, new in changes[:400]:
        pairs = []
        for m in RUN.finditer(old):
            pairs.append(f"{m.group(0)!r}->{repair(m.group(0))!r}")
        print(f"  {qid} {field}: {'; '.join(pairs)[:200]}")
    print(f"{len(leftovers)} values still look damaged after repair:")
    for x in leftovers:
        print("  ", x)
    if not args.apply:
        print("dry run; pass --apply to write")
        return 0
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = sqlite3.connect(APPDATA / f"amplify.db.bak-{stamp}-pre-mojibake")
    conn.backup(dst)
    dst.close()
    existing = {h: q for q, h in conn.execute("SELECT question_id, latex_hash FROM questions")}
    with conn:
        for qid, field, old, new in changes:
            if field == "latexcode":
                h = latex_hash(new)
                if h in existing and existing[h] != qid:
                    print(f"  SKIP {qid}: repaired text duplicates question {existing[h]}")
                    continue
                conn.execute("UPDATE questions SET latexcode = ?, latex_hash = ? WHERE question_id = ?", (new, h, qid))
                existing[h] = qid
            else:
                conn.execute(f"UPDATE questions SET {field} = ? WHERE question_id = ?", (new, qid))
    print(f"applied; backup amplify.db.bak-{stamp}-pre-mojibake")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
