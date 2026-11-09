"""Lecture keywords → concepts, and per-concept allocation (app/core/concepts.py)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from app.core import concepts as c


@pytest.fixture(autouse=True)
def _fresh_vocab() -> None:
    c.clear_vocabulary_cache()


def test_token_matching() -> None:
    assert c.phrase_score(c.tokens("diagonalisation"), c.tokens("Diagonalizability")) == 1.0
    assert c.phrase_score(c.tokens("eigenvalues"), c.tokens("Eigenvalues and Eigenvectors")) == pytest.approx(2 / 3)
    assert c.phrase_score(c.tokens("differentiation"), c.tokens("Differential Equations")) > 0
    # Look-alikes that are different things.
    assert c.phrase_score(c.tokens("integer"), c.tokens("Integral")) == 0.0
    assert c.phrase_score(c.tokens("central"), c.tokens("Centrifugal")) == 0.0
    assert c.phrase_score(c.tokens("eigenvalues"), c.tokens("Eigenvectors")) == 0.0
    # Filler words drop out on both sides.
    assert c.phrase_score(c.tokens("number theory"), c.tokens("Elementary Number Theory")) == 1.0
    # Short words meet their plurals, and nothing else.
    assert c.phrase_score(c.tokens("Lenz's law"), c.tokens("Faraday's and Lenz's Laws")) == pytest.approx(0.8)
    assert c.phrase_score(c.tokens("gas"), c.tokens("Gases")) == 0.0
    assert c.phrase_score(c.tokens("map"), c.tokens("Mass")) == 0.0
    # Accents fold, so plain typing reaches accented names.
    assert c.phrase_score(c.tokens("Mobius transformations"), c.tokens("Möbius Transformations")) == 1.0
    assert c.tokens("Itô's Formula") == c.tokens("Ito's formula")


def test_split_terms() -> None:
    assert c.split_terms("eigenvalues, diagonalisation;\nrepeated roots, Eigenvalues") == [
        "eigenvalues", "diagonalisation", "repeated roots"]
    # Slashes split words, not notation.
    assert c.split_terms("pdf/cdf, M/M/1 queues, mean / variance") == ["pdf", "cdf", "M/M/1 queues", "mean", "variance"]


def test_whole_term_aliases(conn: sqlite3.Connection, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A "=" key applies to the whole term only, never to one word of a longer term."""
    path = tmp_path / "aliases.json"
    path.write_text(json.dumps({"=power": ["Basic Counting"], "svd": "singular value decomposition"}), encoding="utf-8")
    monkeypatch.setattr(c, "_ALIASES_PATH", path)
    c._alias_table.cache_clear()
    try:
        _vocab_db(conn)
        vocab = c.vocabulary(conn, None)
        assert c.match_term("power", vocab)[0]["label"] == "Basic Counting"
        assert all(m["via_alias"] != "Basic Counting" for m in c.match_term("power counting", vocab))
        assert c.match_term("truncated svd", vocab)[0]["label"] == "Singular Value Decomposition"
    finally:
        c._alias_table.cache_clear()


def _vocab_db(conn: sqlite3.Connection) -> None:
    rows = [
        ("Linear Algebra", "Matrix Decompositions", "Singular Value Decomposition", ["Factorization"]),
        ("Linear Algebra", "Matrix Decompositions", "LU Decomposition", []),
        ("Linear Algebra", "Eigenvalues and Diagonalization", "Diagonalizability", []),
        ("Combinatorics", "Counting", "Basic Counting", ["Pigeonhole Principle"]),
        ("Stochastic Processes", "Discrete-Time Markov Chains", "Stationary Distributions", []),
        ("Stochastic Processes", "Continuous-Time Markov Chains", "Birth-Death Processes", []),
        ("Statistics", "Simulation", "Markov Chain Monte Carlo", []),
    ]
    for i, (t, b, s, tags) in enumerate(rows):
        conn.execute(
            "INSERT INTO questions (topic, branch, subtopic, latexcode, latex_hash) VALUES (?, ?, ?, ?, ?)",
            (t, b, s, f"q{i}", f"vh{i}"),
        )
        qid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for tag in tags:
            conn.execute("INSERT INTO question_tags (question_id, tag, role) VALUES (?, ?, 'key')", (qid, tag))
    conn.commit()


def test_match_text_aliases_and_preselection(conn: sqlite3.Connection) -> None:
    _vocab_db(conn)
    out = {t["term"]: t["matches"] for t in c.match_text(conn, "SVD, diagonalisation, markov chains", None)}
    svd = out["SVD"][0]
    assert (svd["kind"], svd["label"], svd["selected"], svd["via_alias"]) == (
        "subtopic", "Singular Value Decomposition", True, "singular value decomposition")
    assert out["diagonalisation"][0]["label"] == "Diagonalizability" and out["diagonalisation"][0]["selected"]
    # Three partial matches tie: listed, but left for the student to pick.
    markov = out["markov chains"]
    assert len([m for m in markov if m["score"] == markov[0]["score"]]) >= 3
    assert not any(m["selected"] for m in markov)


def test_every_matching_tag_is_listed(conn: sqlite3.Connection) -> None:
    """Tags have keys of their own: a term naming several tags lists each one."""
    _vocab_db(conn)
    qid = conn.execute("SELECT MIN(question_id) FROM questions").fetchone()[0]
    for tag in ("Conservation of Energy", "Conservation of Mass"):
        conn.execute("INSERT INTO question_tags (question_id, tag, role) VALUES (?, ?, 'key')", (qid, tag))
    conn.commit()
    vocab = c.vocabulary(conn, None)
    assert len({x.key() for x in vocab}) == len(vocab)
    labels = {m["label"] for m in c.match_term("conservation", vocab) if m["kind"] == "tag"}
    assert labels == {"Conservation of Energy", "Conservation of Mass"}


def test_concept_filters() -> None:
    base = {"subject": "S", "subtopics": ["X"], "tags": {"compulsory": ["A"], "excluded": ["B"]}, "types": ["proof"]}
    f = c.concept_filters(base, {"kind": "tag", "label": "B"})
    assert f["tags"] == {"compulsory": ["A", "B"], "excluded": []} and "subtopics" not in f
    f = c.concept_filters(base, {"kind": "branch", "label": "Eigen"})
    assert f["branches"] == ["Eigen"] and f["types"] == ["proof"] and f["subject"] == "S"
    with pytest.raises(ValueError):
        c.concept_filters(base, {"kind": "nope", "label": "x"})


def test_allocate_splits_and_redistributes() -> None:
    pools = {"a": [1, 2, 3, 4, 5, 6], "b": [7], "c": [3, 8, 9, 10, 11]}

    def fetch(need: int, concept: dict, taken: set[int]) -> list[int]:
        return [q for q in pools[concept["label"]] if q not in taken][:need]

    pairs = c.allocate([{"label": k} for k in "abc"], 9, fetch)
    ids = [q for q, _ in pairs]
    assert len(ids) == 9 and len(set(ids)) == 9
    assert sum(1 for _, i in pairs if i == 1) == 1  # b had one question; its share went to the others


def test_interleave() -> None:
    items = ["a1", "a2", "a3", "b1", "b2", "c1"]
    out = c.interleave(items, key=lambda s: s[0])
    assert sorted(out) == sorted(items)
    assert all(out[i][0] != out[i + 1][0] for i in range(len(out) - 1))
    assert [x for x in out if x[0] == "a"] == ["a1", "a2", "a3"]  # order kept within a group
    # Impossible to separate fully: still returns everything.
    assert sorted(c.interleave(["a1", "a2", "a3", "b1"], key=lambda s: s[0])) == ["a1", "a2", "a3", "b1"]
