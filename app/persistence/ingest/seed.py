"""Seed ingest: CSV + LanceDB embeddings → SQLite.

Spec §4.1, adapted to our actual seed layout. The spec describes a multi-file
bundle (`pre_db.xlsx` + `pre_db.embeddings.npz` + `pre_db.outlines.json` +
`pre_db.topic_depth.json`); we ingest from `TEST.csv` + a LanceDB table
instead. The SQLite schema and on-disk BLOB format (12 288-byte float32
little-endian × 2 columns per question) are unchanged.

Idempotent: skip rows whose `latex_hash` already exists.

Supports incomplete ingests (missing topic/branch/subtopic default to
"Uncategorized"), extra columns (Hints, Instructions, Tags), and a
type-hint row common in exported spreadsheets.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import logging
import re
import shutil
import sqlite3
from dataclasses import dataclass, field
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

# Sentinel used for rows with empty taxonomy columns.
_UNCATEGORIZED = "Uncategorized"

# Type-hint row pattern: first row in some exported CSVs is column type hints.
_TYPE_HINT_PATTERN = re.compile(r"^(varchar|text|bool|smallint|set|list\(.*?\))$", re.IGNORECASE)

_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg")

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
    warnings: list[str] = field(default_factory=list)


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


def _is_type_hint_row(row: dict[str, str]) -> bool:
    pass # unused now


def _parse_tags(raw_tags: str | None) -> list[str]:
    """Parse the Tags column, which may be a Python list literal or empty."""
    if not raw_tags or raw_tags.strip() in ("", "N/A", "n/a", "None", "none", "[]"):
        return []
    try:
        parsed = ast.literal_eval(raw_tags.strip())
        if isinstance(parsed, (list, set, tuple)):
            return [str(t).strip() for t in parsed if str(t).strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed.strip()]
    except (ValueError, SyntaxError):
        pass
    # Fallback: split on commas
    return [t.strip() for t in raw_tags.split(",") if t.strip()]


def ingest(
    conn: sqlite3.Connection,
    csv_path: Path,
    lancedb_path: Path | None = None,
    outlines_json: Path | None = None,
    topic_depth_json: Path | None = None,
    images_source_dir: Path | None = None,
) -> IngestResult:
    """Run the full seed ingest. Idempotent on `questions.latex_hash`.

    Supports incomplete CSVs: rows with empty Topic/Branch/Subtopic default
    to 'Uncategorized'. Extra columns (Hints, Instructions, Tags) are ingested
    when present. A type-hint row (common in exported spreadsheets) is detected
    and skipped automatically.
    """

    if not csv_path.exists():
        raise FileNotFoundError(f"seed CSV not found: {csv_path}")

    warnings: list[str] = []

    # Copy images first (best-effort).
    images_copied = 0
    if images_source_dir is not None:
        images_copied = _copy_images(images_source_dir)
        if images_copied:
            log.info("copied %d image files to teximages", images_copied)

    embeddings = _load_embedding_map(lancedb_path) if lancedb_path else {}

    existing = {row["latex_hash"] for row in conn.execute("SELECT latex_hash FROM questions")}
    log.info("existing questions in db: %d", len(existing))

    imported = 0
    skipped = 0
    embeddings_loaded = 0
    defaulted_taxonomy = 0
    with csv_path.open("r", encoding="latin-1", newline="") as f:
        # Detect headers manually to handle the type-hint row.
        base_reader = csv.reader(f)
        first_row = next(base_reader, None)
        if not first_row:
            return IngestResult(0, 0, 0, 0, [])
        
        # Check if the first row is the type-hint row.
        type_hits = sum(1 for v in first_row if v and v.strip() and _TYPE_HINT_PATTERN.match(v.strip()))
        if type_hits >= len([v for v in first_row if v and v.strip()]) * 0.5:
            log.info("skipped type-hint row")
            headers = next(base_reader, None)
        else:
            headers = first_row
            
        if not headers:
            return IngestResult(0, 0, 0, 0, [])

        reader = csv.DictReader(f, fieldnames=headers)
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

                # Default missing taxonomy to 'Uncategorized' instead of
                # dropping the row — supports incomplete ingests.
                if not topic or not branch or not subtopic:
                    defaulted_taxonomy += 1
                    topic = topic or _UNCATEGORIZED
                    branch = branch or _UNCATEGORIZED
                    subtopic = subtopic or _UNCATEGORIZED

                # Spec §3.1 enumerates types as `proof` / `numerical` /
                # `explanation/reasoning` (lowercase). Normalize stray casing.
                qtype = (raw.get("Type") or "").strip().lower() or None
                in_syllabus = _coerce_in_syllabus(raw.get("In Syllabus?"))
                source = (raw.get("Source") or "").strip() or None
                subsource = (raw.get("SubSource") or "").strip() or None
                answer = (raw.get("Answer") or "").strip() or None
                solution = raw.get("Solution") or None
                hints = raw.get("Hints") or None
                instructions = raw.get("Instructions") or None
                tags = _parse_tags(raw.get("Tags"))

                pair = embeddings.get(normalized, {})
                cls_blob = pair.get("classification") or pair.get("similarity")
                sim_blob = pair.get("similarity") or pair.get("classification")
                if cls_blob or sim_blob:
                    embeddings_loaded += 1

                cur = conn.execute(
                    """
                    INSERT INTO questions (
                        topic, branch, subtopic, latexcode, type, in_syllabus,
                        source, subsource, answer, solution, hints, instructions,
                        latex_hash, classification_emb, similarity_emb
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        topic, branch, subtopic, latex, qtype, in_syllabus,
                        source, subsource, answer, solution, hints, instructions,
                        lh, cls_blob, sim_blob,
                    ),
                )

                # Insert tags into question_tags if present.
                if tags:
                    qid = cur.lastrowid
                    conn.executemany(
                        "INSERT OR IGNORE INTO question_tags (question_id, tag) VALUES (?, ?)",
                        [(qid, tag) for tag in tags],
                    )

                existing.add(lh)
                imported += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    # Build warnings for the caller / UI.
    if defaulted_taxonomy > 0:
        w = (
            f"{defaulted_taxonomy} question(s) had missing Topic/Branch/Subtopic "
            f"and were defaulted to '{_UNCATEGORIZED}'. These should be classified later."
        )
        warnings.append(w)
        log.warning(w)
    if not embeddings and lancedb_path:
        warnings.append("No embeddings were loaded — similarity search will be unavailable for these questions.")
    if embeddings_loaded == 0 and imported > 0 and not lancedb_path:
        warnings.append("No embeddings provided — similarity search will be unavailable for ingested questions.")
    if images_copied > 0:
        warnings.append(f"{images_copied} image file(s) copied to the LaTeX images directory.")

    outlines_loaded = 0
    if outlines_json is not None:
        outlines_loaded = _load_outlines(conn, outlines_json)
    if topic_depth_json is not None:
        _load_topic_depth(conn, topic_depth_json)

    _seed_config_defaults(conn)

    log.info(
        "ingest done: imported=%d skipped=%d embeddings_loaded=%d "
        "outlines_loaded=%d defaulted_taxonomy=%d images_copied=%d",
        imported, skipped, embeddings_loaded, outlines_loaded,
        defaulted_taxonomy, images_copied,
    )
    return IngestResult(
        imported=imported,
        skipped=skipped,
        embeddings_loaded=embeddings_loaded,
        outlines_loaded=outlines_loaded,
        warnings=warnings,
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


def _copy_images(source_dir: Path) -> int:
    """Copy image files from `source_dir` to the teximages directory.

    Best-effort: logs warnings on individual file failures, never raises.
    Returns the number of files successfully copied.
    """
    from app.tex.preamble import image_dir

    if not source_dir.exists() or not source_dir.is_dir():
        log.warning("images source dir %s does not exist or is not a directory", source_dir)
        return 0

    dest = image_dir()
    copied = 0
    for src_file in source_dir.iterdir():
        if not src_file.is_file():
            continue
        if src_file.suffix.lower() not in _IMAGE_EXTS:
            continue
        dst_file = dest / src_file.name
        if dst_file.exists():
            continue  # already present
        try:
            shutil.copy2(src_file, dst_file)
            copied += 1
        except OSError as e:
            log.warning("failed to copy image %s: %s", src_file.name, e)
    return copied
