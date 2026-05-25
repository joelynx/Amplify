"""Seed ingest: CSV + LanceDB embeddings → SQLite.

Spec §4.1, adapted to our actual seed layout. The spec describes a multi-file
bundle (`pre_db.xlsx` + `pre_db.embeddings.npz` + `pre_db.outlines.json` +
`pre_db.topic_depth.json`); we ingest from `TEST.csv` + a LanceDB table
instead. The SQLite schema and on-disk BLOB format (12 288-byte float32
little-endian × 2 columns per question) are unchanged.

Idempotent: skip rows whose `latex_hash` already exists.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger("amplify.ingest")

csv.field_size_limit(2**31 - 1)

# Carried over from Files/Testing/neighbors.py — the LanceDB question text uses
# these apostrophe variants; we normalize them out before hashing or matching.
_APOSTROPHE_VARIANTS = (
    "\xef\xbf\xbd",
    "\xe2\x80\x99",
    "\x92",
    "\ufffd",
    "\u2019",
    "\u2018",
    "\u02bc",
)

_BRACKETED_BRANCH_RE = re.compile(r"^\[(.+)\]$")

_VECTOR_BYTES = 3072 * 4  # spec §3.1 / §12

# §3.7 / §4.1 defaults. Seeded only when the key is absent (idempotent).
_CONFIG_DEFAULTS: dict[str, Any] = {
    "THEME_SELECTED": "default-light",
    "DEFAULT_NO_QUESTIONS": 10,
    "FILE_SAVE_LOCATION": None,
    "LAST_USED_SUBJECT": None,
    "PDF_LEFT_HEADER": "<S>",
    "PDF_RIGHT_HEADER": "<d>",
    "PDF_TITLE_LINE": "<T>",
    "PDF_INSTRUCTIONS": "",
    "EMBED_MODEL_VERSION": "gemini-embedding-002",
    "APPNAME": "Amplify",
    "VERSION": "0.1.0",
}


@dataclass
class IngestResult:
    imported: int
    skipped: int
    embeddings_loaded: int
    outlines_loaded: int


def normalize_text(s: str) -> str:
    """Collapse apostrophe variants, normalize line endings, strip trailing line whitespace.

    Output of this function is what we sha256 and what we match against LanceDB's
    `question` column. Must stay byte-for-byte stable across runs.
    """
    out = s
    for v in _APOSTROPHE_VARIANTS:
        out = out.replace(v, "'")
    out = out.replace("\r\n", "\n")
    out = "\n".join(line.rstrip() for line in out.split("\n"))
    return out.rstrip()


def latex_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def _coerce_in_syllabus(raw: str | None) -> int:
    if raw is None:
        return 1
    v = raw.strip().lower()
    if v in ("yes", "y", "1", "true"):
        return 1
    if v in ("no", "n", "0", "false"):
        return 0
    return 1


def _strip_branch_brackets(raw: str) -> str:
    m = _BRACKETED_BRANCH_RE.match(raw.strip())
    return m.group(1) if m else raw.strip()


def _load_embedding_map(lancedb_path: Path) -> dict[str, dict[str, bytes]]:
    """Read LanceDB once, return {normalized_question_text: {kind: blob}}.

    Best-effort: missing path / missing table / unreadable rows are logged and
    skipped; the ingester proceeds with NULL embeddings.
    """
    if not lancedb_path.exists():
        log.warning("lancedb path %s missing — embeddings will be NULL", lancedb_path)
        return {}

    try:
        import lancedb
        import numpy as np
    except ImportError as e:
        log.warning("lancedb/numpy import failed (%s) — embeddings will be NULL", e)
        return {}

    db = lancedb.connect(str(lancedb_path))
    try:
        tbl = db.open_table("questions")
    except Exception as e:
        log.warning("lancedb table 'questions' unavailable (%s) — embeddings will be NULL", e)
        return {}
    n = tbl.count_rows()
    log.info("scanning %d embedding rows from lancedb", n)

    embeddings: dict[str, dict[str, bytes]] = {}
    rows = tbl.search().limit(None).to_arrow().to_pylist()
    for row in rows:
        text = normalize_text(row["question"])
        vec = np.asarray(row["vector"], dtype="<f4")
        if vec.size != 3072:
            continue
        blob = vec.tobytes()
        if len(blob) != _VECTOR_BYTES:
            continue
        embeddings.setdefault(text, {})[row["kind"]] = blob
    log.info("indexed embeddings for %d distinct question texts", len(embeddings))
    return embeddings


def _set_config(conn: sqlite3.Connection, key: str, value: Any) -> None:
    conn.execute(
        """
        INSERT INTO configs (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, json.dumps(value)),
    )


def _seed_config_defaults(conn: sqlite3.Connection) -> None:
    for k, v in _CONFIG_DEFAULTS.items():
        conn.execute(
            "INSERT INTO configs (key, value) VALUES (?, ?) ON CONFLICT(key) DO NOTHING",
            (k, json.dumps(v)),
        )
    conn.commit()


def ingest(
    conn: sqlite3.Connection,
    csv_path: Path,
    lancedb_path: Path | None = None,
    outlines_json: Path | None = None,
    topic_depth_json: Path | None = None,
) -> IngestResult:
    """Run the full seed ingest. Idempotent on `questions.latex_hash`."""

    if not csv_path.exists():
        raise FileNotFoundError(f"seed CSV not found: {csv_path}")

    embeddings = _load_embedding_map(lancedb_path) if lancedb_path else {}

    existing = {row["latex_hash"] for row in conn.execute("SELECT latex_hash FROM questions")}
    log.info("existing questions in db: %d", len(existing))

    imported = 0
    skipped = 0
    embeddings_loaded = 0

    with csv_path.open("r", encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        try:
            for raw in reader:
                latex = (raw.get("latexcode") or "").strip()
                if not latex:
                    skipped += 1
                    continue

                normalized = normalize_text(latex)
                lh = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                if lh in existing:
                    skipped += 1
                    continue

                topic = (raw.get("Topic") or "").strip()
                branch = _strip_branch_brackets(raw.get("Branch") or "")
                subtopic = (raw.get("Subtopic") or "").strip()
                if not topic or not branch or not subtopic:
                    log.debug("dropping row with empty taxonomy (hash=%s)", lh[:8])
                    skipped += 1
                    continue

                # Spec §3.1 enumerates types as `proof` / `numerical` / `explanation/reasoning`
                # (lowercase). The seed CSV has stray 'Proof' / 'Numerical' variants; normalize
                # so the Types tray and selection filters see a single canonical value per kind.
                qtype = (raw.get("Type") or "").strip().lower() or None
                in_syllabus = _coerce_in_syllabus(raw.get("In Syllabus?"))
                source = (raw.get("Source") or "").strip() or None
                subsource = (raw.get("SubSource") or "").strip() or None
                answer = raw.get("Answer") or None
                solution = raw.get("Solution") or None

                pair = embeddings.get(normalized, {})
                # The seed currently has classification_emb == similarity_emb conceptually
                # (§12). If one kind is missing in the actual LanceDB, fall back to the other.
                cls_blob = pair.get("classification") or pair.get("similarity")
                sim_blob = pair.get("similarity") or pair.get("classification")
                if cls_blob or sim_blob:
                    embeddings_loaded += 1

                conn.execute(
                    """
                    INSERT INTO questions (
                        topic, branch, subtopic, latexcode, type, in_syllabus,
                        source, subsource, answer, solution,
                        latex_hash, classification_emb, similarity_emb
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        topic, branch, subtopic, latex, qtype, in_syllabus,
                        source, subsource, answer, solution,
                        lh, cls_blob, sim_blob,
                    ),
                )

                # TEST.csv has no Tags column. The spec's pre_db.xlsx path would
                # ast.literal_eval `raw["Tags"]` and insert into question_tags here.

                existing.add(lh)
                imported += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    outlines_loaded = 0
    if outlines_json is not None:
        outlines_loaded = _load_outlines(conn, outlines_json)
    if topic_depth_json is not None:
        _load_topic_depth(conn, topic_depth_json)

    _seed_config_defaults(conn)

    log.info(
        "ingest done: imported=%d skipped=%d embeddings_loaded=%d outlines_loaded=%d",
        imported, skipped, embeddings_loaded, outlines_loaded,
    )
    return IngestResult(
        imported=imported,
        skipped=skipped,
        embeddings_loaded=embeddings_loaded,
        outlines_loaded=outlines_loaded,
    )


def _load_outlines(conn: sqlite3.Connection, path: Path) -> int:
    if not path.exists():
        log.info("no outlines file at %s; skipping", path)
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("outline load failed (%s): %s", path, e)
        return 0
    loaded = 0
    for qid_str, outline in data.items():
        try:
            qid = int(qid_str)
        except (TypeError, ValueError):
            continue
        cur = conn.execute(
            "UPDATE questions SET solution_outline = ? WHERE question_id = ?",
            (outline, qid),
        )
        if cur.rowcount:
            loaded += 1
    conn.commit()
    log.info("loaded outlines for %d questions", loaded)
    return loaded


def _load_topic_depth(conn: sqlite3.Connection, path: Path) -> None:
    if not path.exists():
        log.info("no topic_depth file at %s; skipping", path)
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("topic_depth load failed (%s): %s", path, e)
        return
    _set_config(conn, "TOPIC_DEPTH_MAP", data)
    conn.commit()
    log.info("loaded TOPIC_DEPTH_MAP with %d topics", len(data) if isinstance(data, dict) else 0)
