"""
Keyword-retrieval vectors (app/core/retrieval.py)
-------------------------------------------------
Embeds question documents in one or more formats ("plain": topic path +
statement; "tech": plus the technique tags) and one query vector per topic,
branch, subtopic and tag, into a vector store of its own: a SQLite file,
by default the git-ignored evaluation store, so experiments never touch the
app database. Questions are embedded with their statement images (first
MAX_IMAGES), as in reembed.py.

Hash-driven like reembed.py: a stored vector is reused while its text is
unchanged, so runs are incremental and resumable. Texts that are identical
across formats (a question without technique tags reads the same in "plain"
and "tech") are embedded once.

Cost: text-only items go through the Batch API (half price), items with
images through the synchronous API. The estimate uses --chars-per-token
(3.0 by default, on the safe side for LaTeX; --measure counts a sample with
the free token-counting endpoint instead) and the run refuses to start when
the estimate is above --max-usd.

The app uses only the query vectors (the evaluation found the existing
similarity_emb better than these document vectors; see app/core/retrieval.py).
--install copies the current ones into the app database (migration 010) after
backing it up; concepts added later need `--run --docs ''` and --install
again, and until then keep the diverse pick.

Usage (repo root, GOOGLE_API_KEY in .env.local):
  python -m app.tools.retrieval_embed --dry-run [--docs plain,tech] [--no-queries] [--measure]
  python -m app.tools.retrieval_embed --run --max-usd 1.0
  python -m app.tools.retrieval_embed --run --max-usd 1.0 --resume-jobs
  python -m app.tools.retrieval_embed --install
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

from app.core import concepts, retrieval
from app.persistence import db as app_db
from app.persistence.repositories import query_vectors as query_vectors_repo
from app.tools import reembed

STORE_PATH = Path("pipeline/outputs/retrieval_eval/vectors.db")
TEXT_USD_PER_MTOK = {"batch": 0.10, "sync": 0.20}
IMAGE_USD = 0.00012  # per image, synchronous (Google's price list, 2026-11)

STORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
  fmt TEXT NOT NULL, question_id INTEGER NOT NULL, hash TEXT NOT NULL, emb BLOB NOT NULL,
  PRIMARY KEY (fmt, question_id)
);
CREATE TABLE IF NOT EXISTS queries (
  key TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL, text TEXT NOT NULL,
  hash TEXT NOT NULL, emb BLOB NOT NULL
);
"""


def open_store(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(STORE_SCHEMA)
    return conn


def techniques_by_question(app: sqlite3.Connection) -> dict[int, list[str]]:
    out: dict[int, list[str]] = defaultdict(list)
    marks = ",".join("?" * len(retrieval.TECHNIQUE_ROLES))
    for qid, tag in app.execute(
        f"SELECT question_id, tag FROM question_tags WHERE role IN ({marks}) "
        "ORDER BY question_id, CASE role WHEN 'key' THEN 0 ELSE 1 END, tag",
        retrieval.TECHNIQUE_ROLES,
    ):
        if tag not in out[qid]:
            out[qid].append(tag)
    return out


def doc_items(app: sqlite3.Connection, fmts: list[str]) -> list[dict]:
    tech = techniques_by_question(app)
    items: list[dict] = []
    app.row_factory = sqlite3.Row
    rows = app.execute("SELECT question_id, topic, branch, subtopic, latexcode FROM questions ORDER BY question_id").fetchall()
    app.row_factory = None
    for fmt in fmts:
        for r in rows:
            text = retrieval.doc_text(fmt, dict(r), tech.get(r["question_id"], ()))
            images = reembed.extract_images(r["latexcode"])[: reembed.MAX_IMAGES]
            items.append({
                "qid": f"d:{fmt}:{r['question_id']}",
                "kind": "doc",
                "fmt": fmt,
                "question_id": r["question_id"],
                "text": text,
                "images": images,
                "hash": retrieval.text_hash(text, [p.name for p in images]),
            })
    return items


def query_items(app: sqlite3.Connection) -> list[dict]:
    concepts.clear_vocabulary_cache()
    items: dict[str, dict] = {}
    for c in concepts.vocabulary(app, None):
        key = retrieval.query_key(c.kind, c.label, c.path)
        text = retrieval.query_text(c.kind, c.label, c.path)
        items[key] = {
            "qid": f"q:{key}",
            "kind": "query",
            "key": key,
            "concept_kind": c.kind,
            "label": c.label,
            "text": text,
            "images": [],
            "hash": retrieval.text_hash(text),
        }
    return list(items.values())


def stored_hashes(store: sqlite3.Connection) -> tuple[dict[tuple[str, int], str], dict[str, str], dict[str, bytes]]:
    docs = {(f, q): h for f, q, h in store.execute("SELECT fmt, question_id, hash FROM docs")}
    queries = {k: h for k, h in store.execute("SELECT key, hash FROM queries")}
    by_hash = {h: bytes(e) for h, e in store.execute("SELECT hash, emb FROM docs")}
    return docs, queries, by_hash


def write(store: sqlite3.Connection, item: dict, blob: bytes) -> None:
    if item["kind"] == "doc":
        store.execute(
            "INSERT OR REPLACE INTO docs (fmt, question_id, hash, emb) VALUES (?, ?, ?, ?)",
            (item["fmt"], item["question_id"], item["hash"], blob),
        )
    else:
        store.execute(
            "INSERT OR REPLACE INTO queries (key, kind, label, text, hash, emb) VALUES (?, ?, ?, ?, ?, ?)",
            (item["key"], item["concept_kind"], item["label"], item["text"], item["hash"], blob),
        )


def plan(app: sqlite3.Connection, store: sqlite3.Connection, fmts: list[str], with_queries: bool):
    """(representatives to embed, every pending item grouped by hash, items
    filled from a stored identical text)."""
    docs_h, queries_h, by_hash = stored_hashes(store)
    items = doc_items(app, fmts) + (query_items(app) if with_queries else [])
    pending: list[dict] = []
    copied = 0
    for it in items:
        have = docs_h.get((it["fmt"], it["question_id"])) if it["kind"] == "doc" else queries_h.get(it["key"])
        if have == it["hash"]:
            continue
        if it["kind"] == "doc" and it["hash"] in by_hash:
            write(store, it, by_hash[it["hash"]])
            copied += 1
            continue
        pending.append(it)
    store.commit()
    groups: dict[str, list[dict]] = defaultdict(list)
    for it in pending:
        groups[it["hash"]].append(it)
    reps = [g[0] for g in groups.values()]
    return reps, groups, copied, {it["qid"]: it for it in items}


def estimate(reps: list[dict], chars_per_token: float) -> dict:
    text_only = [it for it in reps if not it["images"]]
    with_img = [it for it in reps if it["images"]]
    tok_b = sum(len(it["text"]) for it in text_only) / chars_per_token
    tok_s = sum(len(it["text"]) for it in with_img) / chars_per_token
    n_img = sum(len(it["images"]) for it in with_img)
    usd = (tok_b * TEXT_USD_PER_MTOK["batch"] + tok_s * TEXT_USD_PER_MTOK["sync"]) / 1e6 + n_img * IMAGE_USD
    return {"batch_rows": len(text_only), "sync_rows": len(with_img), "images": n_img,
            "batch_mtok": tok_b / 1e6, "sync_mtok": tok_s / 1e6, "usd": usd}


def measure_chars_per_token(client, reps: list[dict], n: int = 60) -> float:
    """Characters per token on a random sample (count_tokens is free)."""
    sample = random.Random(7).sample(reps, min(n, len(reps)))
    chars = tokens = 0
    for it in sample:
        res = client.models.count_tokens(model=retrieval.EMB_MODEL, contents=it["text"])
        chars += len(it["text"])
        tokens += res.total_tokens
        time.sleep(0.1)
    return chars / max(tokens, 1)


def install(store: sqlite3.Connection, db_path: Path) -> dict[str, int]:
    """Copy the store's query vectors for the bank's current concepts into the
    app database (migration 010), replacing what is there. A vector whose text
    no longer matches its concept (renamed path) is left out."""
    conn = app_db.connect(db_path)
    try:
        app_db.migrate(conn)
        want = {it["key"]: it for it in query_items(conn)}
        rows, stale = [], 0
        for key, kind, label, h, emb in store.execute("SELECT key, kind, label, hash, emb FROM queries ORDER BY key"):
            it = want.get(key)
            if it is None:
                continue
            if it["hash"] != h:
                stale += 1
                continue
            rows.append((key, kind, label, bytes(emb), retrieval.EMB_MODEL, h))
        written = query_vectors_repo.replace_all(conn, rows)
    finally:
        conn.close()
    return {"concepts": len(want), "installed": written, "stale": stale, "missing": len(want) - written}


def backup(db_path: Path, tag: str) -> Path:
    dest = db_path.with_name(f"{db_path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}-{tag}")
    src = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    return dest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--install", action="store_true", help="copy the query vectors into the app database (backs it up first)")
    ap.add_argument("--docs", default="plain,tech", help="document formats, comma-separated ('' for none)")
    ap.add_argument("--no-queries", action="store_true")
    ap.add_argument("--store", type=Path, default=STORE_PATH)
    ap.add_argument("--max-usd", type=float, default=0.0, help="refuse to run above this estimate")
    ap.add_argument("--chars-per-token", type=float, default=3.0)
    ap.add_argument("--measure", action="store_true", help="measure chars per token on a sample first (free)")
    ap.add_argument("--batch-size", type=int, default=2000, help="items per batch job (split automatically if refused)")
    ap.add_argument("--resume-jobs", action="store_true")
    a = ap.parse_args()
    if a.install:
        dest = backup(reembed.DB_PATH, "pre-query-vectors")
        print(f"backed up the app database to {dest}", flush=True)
        r = install(open_store(a.store), reembed.DB_PATH)
        print(
            f"installed {r['installed']} of {r['concepts']} concept vectors "
            f"({r['stale']} stale, {r['missing']} concepts without one keep the diverse pick)",
            flush=True,
        )
        return
    if not (a.run or a.dry_run):
        ap.print_help()
        return
    fmts = [f for f in a.docs.split(",") if f]
    app = sqlite3.connect(f"file:{reembed.DB_PATH.as_posix()}?mode=ro", uri=True)
    store = open_store(a.store)
    reps, groups, copied, by_id = plan(app, store, fmts, not a.no_queries)
    cpt = a.chars_per_token
    client = None
    if a.measure and reps:
        client = reembed.get_client()
        cpt = measure_chars_per_token(client, reps)
        print(f"measured {cpt:.2f} chars per token", flush=True)
    est = estimate(reps, cpt)
    n_items = sum(len(g) for g in groups.values())
    print(
        f"store {a.store} | copied from identical texts: {copied} | pending {n_items} items, {len(reps)} distinct texts | "
        f"batch {est['batch_rows']} ({est['batch_mtok']:.2f}M tok) | sync {est['sync_rows']} ({est['sync_mtok']:.2f}M tok, "
        f"{est['images']} images) | estimate {est['usd']:.2f} USD at {cpt:.2f} chars/token",
        flush=True,
    )
    if a.dry_run or not reps:
        return
    if est["usd"] > a.max_usd:
        raise SystemExit(f"estimate {est['usd']:.2f} USD is above --max-usd {a.max_usd:.2f}; not starting")
    client = client or reembed.get_client()

    def store_fn(conn: sqlite3.Connection, item: dict, vec: list[float]) -> None:
        if len(vec) != reembed.DIMENSIONS:
            raise ValueError(f"{item['qid']}: got {len(vec)} dims")
        blob = retrieval.encode(vec)
        for it in groups.get(item["hash"], [item]):
            write(conn, it, blob)

    jobs_file = a.store.with_suffix(".jobs.json")
    t0 = time.time()
    done = reembed.run_batch(
        store, client, reps, a.batch_size, a.resume_jobs,
        store_fn=store_fn, jobs_file=jobs_file, resolve=lambda ids: [by_id[i] for i in ids], label="amplify-retrieval",
    )
    store.commit()
    left, _, _, _ = plan(app, store, fmts, not a.no_queries)
    print(f"done: {done}/{len(reps)} texts embedded in {int((time.time() - t0) / 60)} min; still pending: {len(left)}", flush=True)


if __name__ == "__main__":
    main()
