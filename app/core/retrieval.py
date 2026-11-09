"""Lecture keywords → questions by meaning: asymmetric embeddings
(Low_Hanging_Fruit.md §3, stage 2).

gemini-embedding-2 has no `task_type`; Google's embeddings guide asks for the
role in the text itself. A query is "task: search result | query: {content}",
a document "title: {title} | text: {content}" ("title: none" when there is
none). Documents are questions: the title is the topic path, the text the
statement, and the "tech" format adds the technique tags. Queries are concept
names, embedded ahead of time for every topic, branch, subtopic and tag: the
app never calls an embedding API at run time, so a lecture term reaches these
vectors only through a concept it matched (app/core/concepts.py).

The existing `similarity_emb` vectors (question + solution, one symmetric
instruction) stay as they are; these vectors are kept apart from them.

What the app uses (`lecture_fetch`) is what won the evaluation of 2026-11-09
(app/tools/retrieval_eval.py; 201 lecture inputs over 22 subjects, 10
questions each, judged blind): keep the concept's label as the filter and
order its questions by cosine between the concept's query vector and their
existing `similarity_emb`. Graded "practises the lecture's terms directly",
0.89 of picks against 0.68 for the diverse pick (+0.215, 95% CI +0.19 to
+0.24). Question vectors in the document format above scored lower (0.85), so
only the query vectors are installed (migration 010). The near-duplicate skip
and unused-first order were added afterwards and were not part of that test.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from app.core import concepts
from app.core.models import Subject
from app.persistence.repositories import query_vectors as query_vectors_repo
from app.persistence.repositories import questions as questions_repo

EMB_MODEL = "models/gemini-embedding-2"
QUERY_TEMPLATE = "task: search result | query: {content}"
DOC_TEMPLATE = "title: {title} | text: {content}"
DOC_FORMATS = ("plain", "tech")
TECHNIQUE_ROLES = ("key", "supporting")
PATH_SEP = " › "


def doc_title(topic: str | None, branch: str | None, subtopic: str | None) -> str:
    """The topic path, or "none" for questions not yet classified."""
    if not topic or topic == "Uncategorized":
        return "none"
    return PATH_SEP.join(p for p in (topic, branch, subtopic) if p)


def doc_text(fmt: str, row: Mapping[str, object], techniques: Sequence[str] = ()) -> str:
    """The document text of one question. `row` has topic, branch, subtopic and
    latexcode; `techniques` are its key and supporting tags (used by "tech")."""
    if fmt not in DOC_FORMATS:
        raise ValueError(f"unknown document format: {fmt!r}")
    title = doc_title(row.get("topic"), row.get("branch"), row.get("subtopic"))  # type: ignore[arg-type]
    content = str(row.get("latexcode") or "").strip()
    if fmt == "tech" and techniques:
        content += "\n\nTechniques: " + ", ".join(techniques)
    return DOC_TEMPLATE.format(title=title, content=content)


def query_key(kind: str, label: str, path: str) -> str:
    """Stable key of a concept's query vector: taxonomy nodes by their path,
    tags by name (a tag's role can change, its name does not)."""
    return f"tag:{label}" if kind == "tag" else f"{kind}:{path}"


def query_text(kind: str, label: str, path: str) -> str:
    """Taxonomy nodes are asked for with their full path, so a generic name
    ("Applications", "Basic Problems") keeps its context; tags by name."""
    return QUERY_TEMPLATE.format(content=label if kind == "tag" else path)


def text_hash(text: str, image_names: Iterable[str] = ()) -> str:
    """Same scheme as app/tools/reembed.py: model | text | image names."""
    h = hashlib.sha256()
    h.update(EMB_MODEL.encode("utf-8"))
    h.update(b"|")
    h.update(text.encode("utf-8"))
    for name in image_names:
        h.update(b"|")
        h.update(name.encode("utf-8"))
    return h.hexdigest()


# ---- vectors ------------------------------------------------------------------


def encode(vec: Sequence[float] | np.ndarray) -> bytes:
    return np.asarray(vec, dtype="<f4").tobytes()


def decode(blob: bytes | memoryview) -> np.ndarray:
    return np.frombuffer(bytes(blob), dtype="<f4")


def truncate(mat: np.ndarray, dims: int | None) -> np.ndarray:
    """Keep the first `dims` components and renormalise each row (the model is
    trained so that a prefix is itself an embedding)."""
    m = np.asarray(mat, dtype=np.float32)
    if dims and dims < m.shape[-1]:
        m = m[..., :dims]
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(n == 0, 1, n)


def rank(query: np.ndarray, ids: Sequence[int], mat: np.ndarray) -> list[int]:
    """`ids` (rows of `mat`) by cosine to `query`, best first; ties by id."""
    if not len(ids):
        return []
    scores = truncate(mat, None) @ truncate(query, None)
    order = np.lexsort((np.asarray(ids), -scores))
    return [int(ids[i]) for i in order]


def labelled_first(order: Sequence[int], labelled: set[int]) -> list[int]:
    """The questions carrying the concept's label in semantic order, then the
    rest in semantic order: the label decides membership, meaning the order."""
    return [q for q in order if q in labelled] + [q for q in order if q not in labelled]


def take(order: Sequence[int], need: int, taken: set[int]) -> list[int]:
    out: list[int] = []
    for q in order:
        if len(out) >= need:
            break
        if q not in taken:
            out.append(q)
    return out


# ---- the app's lecture session ----------------------------------------------

# Cosine between two questions' similarity_emb above which they read as the same
# exercise (two SVDs of 2x3 matrices, one book's question restated by another).
# Set by eye from the eval's closest pairs, not tested on graded picks.
NEAR_DUPLICATE = 0.96

Fetch = Callable[[int, dict[str, Any], set[int]], list[int]]


def take_distinct(
    order: Sequence[int],
    need: int,
    vecs: Mapping[int, np.ndarray | None],
    already: Sequence[np.ndarray] = (),
    near: float = NEAR_DUPLICATE,
) -> list[int]:
    """The first `need` of `order`, passing over a question nearly identical to
    one already picked (or in `already`); passed-over ones fill any gap, so the
    skip never shortens the list."""
    kept = list(already)
    picked: list[int] = []
    passed: list[int] = []
    for q in order:
        if len(picked) >= need:
            break
        v = vecs.get(q)
        if v is not None and kept and max(float(v @ k) for k in kept) >= near:
            passed.append(q)
            continue
        picked.append(q)
        if v is not None:
            kept.append(v)
    return picked + passed[: need - len(picked)]


def concept_vector(conn: sqlite3.Connection, concept: Mapping[str, Any]) -> np.ndarray | None:
    """The concept's stored query vector: by its path when given, else the mean
    of every node with that name (the label filter matches all of them)."""
    kind, label, path = concept["kind"], concept["label"], concept.get("path") or ""
    if kind == "tag" or path:
        blob = query_vectors_repo.get(conn, query_key(kind, label, path))
        if blob is not None:
            return truncate(decode(blob), None)
        if kind == "tag":
            return None
    blobs = query_vectors_repo.by_label(conn, kind, label)
    if not blobs:
        return None
    return truncate(np.mean([truncate(decode(b), None) for b in blobs], axis=0), None)


def lecture_fetch(
    conn: sqlite3.Connection,
    base: dict[str, Any],
    subject: Subject | None,
    fallback: Fetch,
) -> Fetch:
    """concepts.allocate()'s fetch for a lecture session. Per concept: the
    questions carrying its label (the form's filters applied), unused ones
    first, each group by closeness to the concept, questions without a vector
    last; near-duplicates of the session's picks are passed over. A concept
    with no query vector uses `fallback`. When the label runs out, allocate()
    hands the rest of the share to the other concepts."""
    vecs: dict[int, np.ndarray | None] = {}

    def load(ids: Iterable[int]) -> None:
        missing = [q for q in ids if q not in vecs]
        if not missing:
            return
        blobs = questions_repo.fetch_similarity_embeddings(conn, missing)
        for q in missing:
            blob = blobs.get(q)
            vecs[q] = truncate(decode(blob), None) if blob else None

    def fetch(need: int, concept: dict[str, Any], taken: set[int]) -> list[int]:
        qvec = concept_vector(conn, concept)
        if qvec is None:
            return fallback(need, concept, taken)
        ids = [q for q in questions_repo.matching_ids(conn, concepts.concept_filters(base, concept), subject) if q not in taken]
        load(ids)
        load(taken)
        ranked = [q for q in ids if vecs[q] is not None and vecs[q].shape == qvec.shape]
        order = rank(qvec, ranked, np.stack([vecs[q] for q in ranked])) if ranked else []
        has = set(ranked)
        order += [q for q in ids if q not in has]
        fresh = questions_repo.fresh_ids(conn, order)
        order = [q for q in order if q in fresh] + [q for q in order if q not in fresh]
        already = [v for q in taken if (v := vecs.get(q)) is not None and v.shape == qvec.shape]
        return take_distinct(order, need, vecs, already)

    return fetch
