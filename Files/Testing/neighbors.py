"""Find the K nearest neighbors of a TEST.csv question using embeddings
stored in the LanceDB table built by build_lancedb.py.

Usage:
    python neighbors.py <row_index> <k> [--kind {similarity,classification}] [--output FILE]

`row_index` is 1-based, matching how a human reads TEST.csv (row 1 is the
first question, the CSV header is not counted). `--kind` selects which
embedding variant to search against (default: similarity).

The LanceDB table holds every question from the embedding CSVs, not just the
TEST.csv subset. Neighbors may therefore be questions that don't appear in
TEST.csv; those rows have blank Topic/Branch/etc. and are tagged accordingly
in the output.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import lancedb

csv.field_size_limit(2**31 - 1)

ROOT = Path(__file__).parent
TEST_CSV = ROOT / "TEST.csv"
DB_PATH = ROOT / "lancedb"
TABLE_NAME = "questions"

_APOSTROPHE_VARIANTS = (
    "\xef\xbf\xbd",
    "\xe2\x80\x99",
    "\x92",
    "\ufffd",
    "\u2019",
    "\u2018",
    "\u02bc",
)


def normalize_question(q: str) -> str:
    out = q
    for v in _APOSTROPHE_VARIANTS:
        out = out.replace(v, "'")
    return out


def load_test_row(row_index: int) -> dict:
    """Return the TEST.csv row at the given 1-based index."""
    with open(TEST_CSV, "r", encoding="latin-1", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=1):
            if i == row_index:
                return row
    raise IndexError(f"row {row_index} out of range (TEST.csv has fewer rows)")


def fmt_block(title: str, text: str) -> str:
    return f"{title}:\n{text}\n"


def lookup_query_vector(tbl, query_text: str, kind: str):
    """Find the embedding for (question == query_text, kind == kind).
    Pulls only the (question, kind, _rowid) projection to locate the row,
    then fetches the single vector by row id — avoids reading every row's
    3072-float vector just to find one."""
    meta = (
        tbl.search()
        .select(["question", "kind"])
        .limit(None)
        .with_row_id(True)
        .to_arrow()
    )
    df = meta.to_pandas()
    mask = (df["kind"] == kind) & (df["question"] == query_text)
    matches = df.loc[mask, "_rowid"]
    if matches.empty:
        return None
    row_id = int(matches.iloc[0])
    vec_tbl = tbl.take_row_ids([row_id]).select(["vector"]).to_arrow()
    return vec_tbl.column("vector")[0].as_py()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("row_index", type=int, help="1-based row in TEST.csv")
    ap.add_argument("k", type=int, help="number of nearest neighbors to return")
    ap.add_argument(
        "--kind",
        choices=("similarity", "classification"),
        default="similarity",
        help="which embedding to use (default: similarity)",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output .txt path (default: neighbors_<idx>_k<k>_<kind>.txt)",
    )
    args = ap.parse_args()

    if args.k < 1:
        ap.error("k must be >= 1")

    query_row = load_test_row(args.row_index)
    query_text = normalize_question(query_row["latexcode"])

    db = lancedb.connect(str(DB_PATH))
    tbl = db.open_table(TABLE_NAME)

    query_vec = lookup_query_vector(tbl, query_text, args.kind)
    if query_vec is None:
        print(
            f"ERROR: no {args.kind} embedding found for TEST row {args.row_index}.",
            file=sys.stderr,
        )
        print(f"Question: {query_text[:120]!r}", file=sys.stderr)
        return 1

    # k + 1 so we can drop the self-match (distance 0). The where-clause keeps
    # the search within the requested embedding variant, but every row of that
    # kind in the table is a candidate — including questions that aren't in
    # TEST.csv.
    hits = (
        tbl.search(query_vec)
        .where(f"kind = '{args.kind}'")
        .limit(args.k + 1)
        .to_list()
    )
    neighbors = [h for h in hits if h["question"] != query_text][: args.k]

    out_path = args.output or ROOT / f"neighbors_{args.row_index}_k{args.k}_{args.kind}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"=== QUERY (TEST.csv row {args.row_index}) ===\n")
        f.write(f"Topic:    {query_row.get('Topic', '')}\n")
        f.write(f"Branch:   {query_row.get('Branch', '')}\n")
        f.write(f"Subtopic: {query_row.get('Subtopic', '')}\n")
        f.write(f"Type:     {query_row.get('Type', '')}\n")
        f.write(f"Source:   {query_row.get('Source', '')}\n\n")
        f.write(fmt_block("Question", query_text))
        f.write("\n")
        f.write(fmt_block("Solution", query_row.get("Solution", "")))
        f.write("\n")

        f.write(f"=== {len(neighbors)} NEAREST NEIGHBORS ({args.kind} embedding) ===\n\n")
        for rank, h in enumerate(neighbors, start=1):
            # A neighbor row counts as "in TEST.csv" if any of its TEST-only
            # metadata fields are populated.
            in_test = bool(h.get("topic") or h.get("branch") or h.get("source"))
            tag = "" if in_test else "  [not in TEST.csv]"
            f.write(f"--- Neighbor #{rank}  (distance = {h['_distance']:.4f}){tag} ---\n")
            f.write(f"Topic:    {h.get('topic', '')}\n")
            f.write(f"Branch:   {h.get('branch', '')}\n")
            f.write(f"Subtopic: {h.get('subtopic', '')}\n")
            f.write(f"Type:     {h.get('qtype', '')}\n")
            f.write(f"Source:   {h.get('source', '')}\n\n")
            f.write(fmt_block("Question", h["question"]))
            f.write("\n")
            f.write(fmt_block("Solution", h["solution"]))
            f.write("\n")

    print(
        f"Wrote {len(neighbors)} {args.kind} neighbors of TEST row "
        f"{args.row_index} to {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
