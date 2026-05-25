"""Smart difficulty (spec §13).

Three sub-scores in [0, 1], combined with per-topic weights into a [0, 20]
rating written into `questions.difficulty_rating`. **No outbound network**
— every input is local: stored embeddings, stored outline/solution text,
the user-managed TOPIC_DEPTH_MAP.

Sub-scores
----------
length    spec: "count of top-level items in `solution_outline`". When the
          outline is NULL (the common case in our seed bundle), fall back
          to `log1p(solution_chars) / log1p(max_observed)` — the formula
          the karth/web-mvp branch landed on.

novelty   `1 - max(cosine(this.classification_emb, others-in-same-subtopic))`.
          Per spec, NULL embedding → 0.

depth     Lookup in `configs.TOPIC_DEPTH_MAP` (read-only at runtime; shipped
          via the seed bundle). Normalized to [0, 1] by dividing by 20. When
          the map is empty/missing (our case), depth contributes 0 and the
          combiner auto-renormalizes over (length, novelty).

Combiner
--------
Per-topic linear combination, weights in `configs.DIFFICULTY_WEIGHTS` (a
`{topic: {length, novelty, depth}}` dict). Defaults to 0.4 / 0.4 / 0.2.
Pairwise judgments from the trainer adjust the weights via simple gradient
descent + non-negativity + renormalization.
"""

from __future__ import annotations

import logging
import math
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.persistence.repositories import configs as configs_repo

log = logging.getLogger("amplify.difficulty")

_VECTOR_BYTES = 3072 * 4
_TOP_ITEM_RE = re.compile(r"^\s*\\item\b", re.MULTILINE)

DEFAULT_WEIGHTS: dict[str, float] = {"length": 0.4, "novelty": 0.4, "depth": 0.2}
SUB_SCORE_KEYS = ("length", "novelty", "depth")


@dataclass(slots=True)
class SubScores:
    length: float
    novelty: float
    depth: float

    def to_dict(self) -> dict[str, float]:
        return {"length": self.length, "novelty": self.novelty, "depth": self.depth}


@dataclass(slots=True)
class RecomputeResult:
    updated: int
    skipped: int
    avg_rating: float | None
    topics_covered: int


# --- weights storage ----------------------------------------------------


def get_all_weights(conn: sqlite3.Connection) -> dict[str, dict[str, float]]:
    raw = configs_repo.get(conn, "DIFFICULTY_WEIGHTS", {}) or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def weights_for_topic(
    conn: sqlite3.Connection,
    topic: str,
    *,
    depth_available: bool = True,
) -> dict[str, float]:
    """Per-topic weights, falling back to the global defaults. When depth is
    unavailable (TOPIC_DEPTH_MAP empty / missing for this topic), the depth
    weight is zeroed and the rest are renormalized so the combiner still
    sums to 1."""
    all_w = get_all_weights(conn)
    w = dict(all_w.get(topic) or DEFAULT_WEIGHTS)
    if not depth_available:
        w["depth"] = 0.0
        s = w["length"] + w["novelty"]
        if s > 0:
            w["length"] /= s
            w["novelty"] /= s
        else:
            w["length"] = 0.5
            w["novelty"] = 0.5
    return w


def set_weights(conn: sqlite3.Connection, topic: str, w: dict[str, float]) -> None:
    all_w = get_all_weights(conn)
    all_w[topic] = {
        "length": float(w.get("length", 0.0)),
        "novelty": float(w.get("novelty", 0.0)),
        "depth": float(w.get("depth", 0.0)),
    }
    configs_repo.set_(conn, "DIFFICULTY_WEIGHTS", all_w)


def is_enabled(conn: sqlite3.Connection) -> bool:
    return bool(configs_repo.get(conn, "SMART_DIFFICULTY_ENABLED", False))


def set_enabled(conn: sqlite3.Connection, on: bool) -> None:
    configs_repo.set_(conn, "SMART_DIFFICULTY_ENABLED", bool(on))


def topic_depth_map(conn: sqlite3.Connection) -> dict[str, int]:
    raw = configs_repo.get(conn, "TOPIC_DEPTH_MAP", {}) or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        try:
            out[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    return out


# --- sub-score helpers --------------------------------------------------


def _outline_length(outline: str | None) -> int | None:
    if not outline:
        return None
    return len(_TOP_ITEM_RE.findall(outline))


def _length_score(outline: str | None, solution: str | None, max_chars: int) -> float:
    items = _outline_length(outline)
    if items is not None and items > 0:
        # Normalize to [0, 1] assuming "very long outlines" max around 10 items.
        return min(1.0, items / 10.0)
    if not solution:
        return 0.0
    if max_chars <= 0:
        return 0.0
    return float(math.log1p(len(solution)) / math.log1p(max_chars))


def _decode_emb(blob: bytes | memoryview | None) -> np.ndarray | None:
    if blob is None:
        return None
    raw = bytes(blob)
    if len(raw) != _VECTOR_BYTES:
        return None
    return np.frombuffer(raw, dtype="<f4")


def _depth_score(topic: str, depth_map: dict[str, int]) -> tuple[float, bool]:
    """Returns (score_in_[0,1], available). Score = depth / 20."""
    if topic not in depth_map:
        return 0.0, False
    return min(1.0, max(0.0, depth_map[topic] / 20.0)), True


# --- recompute pass -----------------------------------------------------


def recompute_all(conn: sqlite3.Connection) -> RecomputeResult:
    """Pass over the question bank: per-subtopic batched novelty + per-row
    length + depth → combined rating in [0, 20] written to
    `questions.difficulty_rating`. Reads-only on embeddings."""

    depth_map = topic_depth_map(conn)
    depth_globally_available = bool(depth_map)

    rows = list(
        conn.execute(
            "SELECT question_id, topic, subtopic, classification_emb, "
            "solution, solution_outline, length(solution) AS sol_len FROM questions"
        )
    )
    if not rows:
        return RecomputeResult(updated=0, skipped=0, avg_rating=None, topics_covered=0)

    # Establish a max-solution-length once for normalization.
    max_chars = max((r["sol_len"] or 0) for r in rows) or 1

    # Group by subtopic for novelty (cosine within the same subtopic, spec §13.1).
    subtopic_groups: dict[tuple[str, str], list[tuple[int, np.ndarray | None]]] = {}
    for r in rows:
        key = (r["topic"], r["subtopic"])
        subtopic_groups.setdefault(key, []).append(
            (int(r["question_id"]), _decode_emb(r["classification_emb"]))
        )

    novelty_by_qid: dict[int, float] = {}
    for _key, members in subtopic_groups.items():
        # Filter to those with valid embeddings.
        valid = [(qid, v) for qid, v in members if v is not None]
        if len(valid) <= 1:
            # Singleton subtopic → no peers to compare against; max similarity
            # is undefined. Per spec, NULL emb → 0; we'll treat the singleton
            # case the same way.
            for qid, _ in members:
                novelty_by_qid.setdefault(qid, 0.0)
            continue
        ids = [qid for qid, _ in valid]
        mat = np.stack([v for _, v in valid]).astype("<f4")
        # L2-normalize rows so dot product == cosine.
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = mat / norms
        sim = normalized @ normalized.T
        # Zero out self-similarity so it doesn't dominate the max.
        np.fill_diagonal(sim, -1.0)
        max_sim = sim.max(axis=1)
        for qid, m in zip(ids, max_sim, strict=True):
            novelty_by_qid[qid] = float(max(0.0, 1.0 - float(m)))
        # Members without embeddings → 0.
        for qid, v in members:
            if v is None:
                novelty_by_qid.setdefault(qid, 0.0)

    updated = 0
    skipped = 0
    ratings: list[float] = []
    topics_seen: set[str] = set()

    try:
        for r in rows:
            qid = int(r["question_id"])
            topic = r["topic"]
            sub_len = _length_score(r["solution_outline"], r["solution"], max_chars)
            sub_nov = novelty_by_qid.get(qid, 0.0)
            sub_dep, dep_avail = _depth_score(topic, depth_map)
            w = weights_for_topic(
                conn, topic, depth_available=depth_globally_available and dep_avail
            )
            combined_unit = (
                w["length"] * sub_len + w["novelty"] * sub_nov + w["depth"] * sub_dep
            )
            rating = round(float(combined_unit) * 20.0, 2)
            if sub_len == 0.0 and sub_nov == 0.0 and sub_dep == 0.0:
                skipped += 1
                continue
            conn.execute(
                "UPDATE questions SET difficulty_rating = ? WHERE question_id = ?",
                (rating, qid),
            )
            updated += 1
            ratings.append(rating)
            topics_seen.add(topic)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    avg = float(np.mean(ratings)) if ratings else None
    log.info(
        "recompute_difficulty: updated=%d skipped=%d topics=%d avg=%.2f",
        updated,
        skipped,
        len(topics_seen),
        avg or 0.0,
    )
    return RecomputeResult(
        updated=updated, skipped=skipped, avg_rating=avg, topics_covered=len(topics_seen)
    )


# --- per-row sub-score lookup (for trainer UI) -------------------------


def sub_scores_for(conn: sqlite3.Connection, question_id: int) -> SubScores | None:
    """One-off sub-score computation for the trainer. Slower than a bulk
    recompute since it re-loads the subtopic group, but used at most twice
    per pairwise step so latency is fine."""
    row = conn.execute(
        "SELECT question_id, topic, subtopic, classification_emb, solution, solution_outline "
        "FROM questions WHERE question_id = ?",
        (question_id,),
    ).fetchone()
    if row is None:
        return None

    depth_map = topic_depth_map(conn)
    max_chars_row = conn.execute(
        "SELECT MAX(length(solution)) FROM questions"
    ).fetchone()
    max_chars = int(max_chars_row[0] or 1)
    length = _length_score(row["solution_outline"], row["solution"], max_chars)
    depth, _ = _depth_score(row["topic"], depth_map)

    my_vec = _decode_emb(row["classification_emb"])
    novelty = 0.0
    if my_vec is not None:
        peers = list(
            conn.execute(
                "SELECT classification_emb FROM questions "
                "WHERE subtopic = ? AND topic = ? AND question_id != ? "
                "AND classification_emb IS NOT NULL",
                (row["subtopic"], row["topic"], question_id),
            )
        )
        peer_vecs = [v for v in (_decode_emb(p[0]) for p in peers) if v is not None]
        if peer_vecs:
            my_n = my_vec / (np.linalg.norm(my_vec) or 1.0)
            peer_mat = np.stack(peer_vecs).astype("<f4")
            peer_norms = np.linalg.norm(peer_mat, axis=1, keepdims=True)
            peer_norms[peer_norms == 0] = 1.0
            peer_mat = peer_mat / peer_norms
            sims = peer_mat @ my_n
            novelty = float(max(0.0, 1.0 - float(sims.max())))
    return SubScores(length=length, novelty=novelty, depth=depth)


def combined_rating(
    weights: dict[str, float], scores: SubScores, *, scale: float = 20.0
) -> float:
    unit = (
        weights.get("length", 0.0) * scores.length
        + weights.get("novelty", 0.0) * scores.novelty
        + weights.get("depth", 0.0) * scores.depth
    )
    return round(float(unit) * scale, 2)


# --- pairwise gradient update ------------------------------------------


def pairwise_step(
    weights: dict[str, float],
    harder_scores: SubScores,
    easier_scores: SubScores,
    *,
    magnitude: float = 0.5,
    learning_rate: float = 0.1,
) -> dict[str, float]:
    """One gradient step per pairwise judgment.

    `magnitude` in (0, 1]: 0.25 = slightly, 0.5 = moderately, 0.75 = much.
    Negative magnitude inverts the pair (rarely useful — easier to swap args).

    Returns new weights with non-negativity + renormalization to sum 1.
    """
    h = harder_scores.to_dict()
    e = easier_scores.to_dict()
    pred_diff = sum(weights.get(k, 0.0) * (h[k] - e[k]) for k in SUB_SCORE_KEYS)
    error = float(magnitude) - pred_diff
    new = {}
    for k in SUB_SCORE_KEYS:
        delta = learning_rate * error * (h[k] - e[k])
        new[k] = max(0.0, weights.get(k, 0.0) + delta)
    total = sum(new.values())
    if total <= 0:
        # Pathological — reset to defaults for this topic so we don't lose the row.
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in new.items()}


def pick_pairwise_pair(
    conn: sqlite3.Connection, topic: str | None = None
) -> tuple[int, int, str] | None:
    """Pick two random questions from the same (sub)topic for the trainer.

    Prefers questions with at least one non-zero sub-score input so the user
    has something to anchor on. Returns (qid_a, qid_b, topic) or None."""
    where = ""
    params: list[Any] = []
    if topic:
        where = "AND topic = ?"
        params.append(topic)
    # Find a (topic, subtopic) bucket with ≥2 candidates, then pick two random
    # questions from it. Two-step query keeps the IO small.
    bucket = conn.execute(
        f"""
        SELECT topic, subtopic FROM questions
        WHERE 1=1 {where}
        GROUP BY topic, subtopic HAVING COUNT(*) >= 2
        ORDER BY RANDOM() LIMIT 1
        """,
        params,
    ).fetchone()
    if bucket is None:
        return None
    rows = list(
        conn.execute(
            "SELECT question_id FROM questions WHERE topic = ? AND subtopic = ? "
            "ORDER BY RANDOM() LIMIT 2",
            (bucket["topic"], bucket["subtopic"]),
        )
    )
    if len(rows) < 2:
        return None
    return int(rows[0][0]), int(rows[1][0]), str(bucket["topic"])
