"""Classification confidence (migration 013, owner 2026-11-21): `classification_conf` and
`classification_how` are empty until a classification run's labels are applied, and
taxonomy/tools/apply_full_run.py fills them for the questions it places."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

from app.persistence.db import migrate

ROOT = Path(__file__).resolve().parents[1]


def _apply_module():
    spec = importlib.util.spec_from_file_location("apply_full_run", ROOT / "taxonomy" / "tools" / "apply_full_run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_columns_exist_and_start_empty(seeded_conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in seeded_conn.execute("PRAGMA table_info(questions)")}
    assert {"classification_conf", "classification_how"} <= cols
    row = seeded_conn.execute("SELECT classification_conf, classification_how FROM questions LIMIT 1").fetchone()
    assert tuple(row) == (None, None)


def test_apply_full_run_records_confidence(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "amplify.db"
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    migrate(c)
    for text in ("placed", "left out"):
        c.execute("INSERT INTO questions (topic, branch, subtopic, latexcode, source, latex_hash) "
                  "VALUES ('Uncategorized', 'Uncategorized', 'Uncategorized', ?, 'test', ?)", (text, f"hash {text}"))
    c.commit()
    node = json.loads((ROOT / "taxonomy" / "taxonomy.json").read_text("utf-8"))[0]
    labels = {
        "1": {"subject": node["subject"], "topic": node["topic"], "branch": node["branch"], "subtopic": node["subtopic"],
              "conf": "medium", "how": "opus", "type": "proof", "key": [], "supporting": [], "task": None},
        "2": {"subject": node["subject"], "topic": None, "branch": None, "subtopic": "WASTEBASKET",
              "conf": "low", "how": "agree", "type": None, "key": [], "supporting": [], "task": None},
    }
    (tmp_path / "final_labels.json").write_text(json.dumps(labels), "utf-8")
    mod = _apply_module()
    monkeypatch.setattr(mod, "DB", db)
    mod.main(True, tmp_path)
    got = {r["question_id"]: (r["subtopic"], r["classification_conf"], r["classification_how"])
           for r in c.execute("SELECT question_id, subtopic, classification_conf, classification_how FROM questions")}
    assert got[1] == (node["subtopic"], "medium", "opus")
    assert got[2] == ("Uncategorized", None, None)  # a wastebasket label places nothing and records nothing
    c.close()
