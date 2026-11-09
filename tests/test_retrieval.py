"""Keyword retrieval by meaning (app/core/retrieval.py) and its embedding planner
(app/tools/retrieval_embed.py). No API calls."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pytest

from app.core import concepts, retrieval
from app.tools import retrieval_embed


def test_document_and_query_formats() -> None:
    row = {"topic": "Linear Algebra", "branch": "Eigenvalues", "subtopic": "Diagonalization", "latexcode": " Diagonalise $A$. "}
    assert retrieval.doc_text("plain", row) == "title: Linear Algebra › Eigenvalues › Diagonalization | text: Diagonalise $A$."
    assert retrieval.doc_text("tech", row, ["Induction", "Parity"]).endswith("Diagonalise $A$.\n\nTechniques: Induction, Parity")
    assert retrieval.doc_text("tech", row) == retrieval.doc_text("plain", row)  # no tags: the same text
    assert retrieval.doc_text("plain", {**row, "topic": "Uncategorized"}).startswith("title: none | text:")
    with pytest.raises(ValueError):
        retrieval.doc_text("nope", row)

    path = "Linear Algebra › Eigenvalues › Applications"
    assert retrieval.query_text("subtopic", "Applications", path) == f"task: search result | query: {path}"
    assert retrieval.query_text("tag", "Induction", "Induction (key)") == "task: search result | query: Induction"
    assert retrieval.query_key("tag", "Induction", "Induction (key)") == "tag:Induction"
    assert retrieval.query_key("subtopic", "Applications", path) == f"subtopic:{path}"


def test_text_hash_covers_images() -> None:
    assert retrieval.text_hash("a") == retrieval.text_hash("a")
    assert retrieval.text_hash("a") != retrieval.text_hash("a", ["fig.png"])


def test_vectors_round_trip_and_truncate() -> None:
    v = np.arange(1, 7, dtype=np.float32)
    assert np.array_equal(retrieval.decode(retrieval.encode(v)), v)
    t = retrieval.truncate(np.stack([v, -v]), 2)
    assert t.shape == (2, 2)
    assert np.allclose(np.linalg.norm(t, axis=1), 1.0)


def test_rank_labelled_first_and_take() -> None:
    mat = np.array([[1, 0], [0.8, 0.6], [0, 1], [0.8, 0.6]], dtype=np.float32)
    ids = [10, 11, 12, 9]
    order = retrieval.rank(np.array([1, 0], dtype=np.float32), ids, mat)
    assert order == [10, 9, 11, 12]  # equal scores: lower id first
    assert retrieval.labelled_first(order, {12, 11}) == [11, 12, 10, 9]
    assert retrieval.take(order, 2, {10}) == [9, 11]
    assert retrieval.rank(np.array([1, 0], dtype=np.float32), [], mat[:0]) == []


def test_embed_plan_reuses_identical_texts(seeded_conn: sqlite3.Connection, tmp_path: Path) -> None:
    concepts.clear_vocabulary_cache()
    store = retrieval_embed.open_store(tmp_path / "v.db")
    reps, groups, copied, by_id = retrieval_embed.plan(seeded_conn, store, ["plain", "tech"], True)
    n_q = seeded_conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    docs = [g for g in groups.values() if g[0]["kind"] == "doc"]
    # Seeded tags take the default role, 'key': tagged questions read differently in "tech".
    tagged = seeded_conn.execute(
        "SELECT COUNT(DISTINCT question_id) FROM question_tags WHERE role IN ('key', 'supporting')"
    ).fetchone()[0]
    assert len(docs) == n_q + tagged
    assert sum(len(g) for g in docs) == 2 * n_q
    assert copied == 0 and len(by_id) == sum(len(g) for g in groups.values())
    queries = [it for it in reps if it["kind"] == "query"]
    assert {it["key"] for it in queries} >= {"tag:induction", "topic:Calculus"}

    # Store one vector per text; the next plan has nothing left to do.
    for rep in reps:
        for it in groups[rep["hash"]]:
            retrieval_embed.write(store, it, retrieval.encode([0.0] * 4))
    store.commit()
    reps2, _, _, _ = retrieval_embed.plan(seeded_conn, store, ["plain", "tech"], True)
    assert reps2 == []

    # A new format whose text matches a stored one is filled without an API call.
    store.execute("DELETE FROM docs WHERE fmt = 'tech'")
    store.commit()
    reps3, _, copied3, _ = retrieval_embed.plan(seeded_conn, store, ["plain", "tech"], True)
    assert copied3 == n_q - tagged and len(reps3) == tagged


# ---- the app's lecture session ----------------------------------------------

PATH = "Linear Algebra › Eigen › Diagonal"


def _unit(*xs: float) -> np.ndarray:
    v = np.asarray(xs, dtype=np.float32)
    return v / np.linalg.norm(v)


def test_take_distinct_passes_over_near_duplicates() -> None:
    vecs = {1: _unit(1, 0, 0), 2: _unit(1, 0.01, 0), 3: _unit(0, 1, 0), 4: None}
    assert retrieval.take_distinct([1, 2, 3, 4], 3, vecs) == [1, 3, 4]
    assert retrieval.take_distinct([1, 2], 2, vecs) == [1, 2]  # passed-over ones fill a gap
    assert retrieval.take_distinct([2, 3], 1, vecs, already=[vecs[1]]) == [3]  # earlier picks count


def _lecture_db(conn: sqlite3.Connection) -> dict[str, int]:
    """One subtopic, Diagonal, with known vectors; a query vector pointing at e1."""
    rows = {  # name: (vector or None, times_used)
        "far": (_unit(0.2, 1, 0, 0), 0),
        "best": (_unit(1, 0, 0, 0), 0),
        "twin": (_unit(0.99, 0.05, 0, 0), 0),  # near-duplicate of best
        "mid": (_unit(0.7, 0.7, 0, 0), 0),
        "novec": (None, 0),
        "used": (_unit(0.5, 0, 0.86, 0), 1),
    }
    ids = {}
    for i, (name, (vec, used)) in enumerate(rows.items()):
        conn.execute(
            "INSERT INTO questions (topic, branch, subtopic, latexcode, latex_hash, times_used, similarity_emb) "
            "VALUES ('Linear Algebra', 'Eigen', 'Diagonal', ?, ?, ?, ?)",
            (f"q {name}", f"lh{i}", used, retrieval.encode(vec) if vec is not None else None),
        )
        ids[name] = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO concept_query_vectors (query_key, kind, label, emb, emb_model, emb_text_hash) VALUES (?, ?, ?, ?, ?, ?)",
        (retrieval.query_key("subtopic", "Diagonal", PATH), "subtopic", "Diagonal", retrieval.encode(_unit(1, 0, 0, 0)), retrieval.EMB_MODEL, "h"),
    )
    conn.commit()
    return ids


def test_lecture_fetch_orders_by_meaning(conn: sqlite3.Connection) -> None:
    ids = _lecture_db(conn)
    fell_back: list[str] = []

    def fallback(need: int, c: dict, taken: set[int]) -> list[int]:
        fell_back.append(c["label"])
        return []

    fetch = retrieval.lecture_fetch(conn, {"reuse_questions": True}, None, fallback)
    concept = {"kind": "subtopic", "label": "Diagonal", "path": PATH}
    # Closest first; the twin of "best" is passed over; unused before used, no vector after the ranked ones.
    assert fetch(3, concept, set()) == [ids["best"], ids["mid"], ids["far"]]
    assert fetch(6, concept, set()) == [ids["best"], ids["mid"], ids["far"], ids["novec"], ids["used"], ids["twin"]]
    # A pick already in the session is excluded, and its twin passed over.
    assert fetch(2, concept, {ids["best"]}) == [ids["mid"], ids["far"]]
    # Without a path, the vectors stored under that name are used.
    assert fetch(1, {"kind": "subtopic", "label": "Diagonal"}, set()) == [ids["best"]]
    # The form's filters still apply.
    fetch_fresh = retrieval.lecture_fetch(conn, {"reuse_questions": False}, None, fallback)
    assert ids["used"] not in fetch_fresh(10, concept, set())
    # No query vector: the fallback picks.
    assert fetch(2, {"kind": "subtopic", "label": "Spectral", "path": "Linear Algebra › Eigen › Spectral"}, set()) == []
    assert fell_back == ["Spectral"]


def test_install_copies_current_query_vectors(tmp_path: Path) -> None:
    from app.persistence import db as app_db
    from app.persistence.repositories import query_vectors as query_vectors_repo

    db_path = tmp_path / "app.db"
    c = app_db.connect(db_path)
    app_db.migrate(c)
    for i, (t, b, s) in enumerate([("Calculus", "Integral", "Riemann"), ("Linear Algebra", "Eigen", "Diagonal")]):
        c.execute(
            "INSERT INTO questions (topic, branch, subtopic, latexcode, latex_hash) VALUES (?, ?, ?, ?, ?)",
            (t, b, s, f"q{i}", f"lh{i}"),
        )
    c.commit()
    concepts.clear_vocabulary_cache()
    items = retrieval_embed.query_items(c)
    c.close()
    store = retrieval_embed.open_store(tmp_path / "v.db")
    for it in items:
        retrieval_embed.write(store, it, retrieval.encode(_unit(1, 0, 0, 0)))
    store.execute("UPDATE queries SET hash = 'old' WHERE key = ?", (items[0]["key"],))  # text changed since
    store.execute(
        "INSERT INTO queries (key, kind, label, text, hash, emb) VALUES ('topic:Gone', 'topic', 'Gone', 'x', 'h', ?)",
        (retrieval.encode(_unit(1, 0, 0, 0)),),
    )
    store.commit()
    r = retrieval_embed.install(store, db_path)
    assert r == {"concepts": len(items), "installed": len(items) - 1, "stale": 1, "missing": 1}
    c = app_db.connect(db_path)
    assert query_vectors_repo.count(c) == len(items) - 1
    assert query_vectors_repo.get(c, "topic:Gone") is None
    c.close()
