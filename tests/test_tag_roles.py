"""Migration 007: question_tags.role is 'key', 'supporting' or 'task'."""

from __future__ import annotations

import sqlite3

import pytest

from app.persistence.repositories import questions as questions_repo


def test_existing_rows_default_to_key(seeded_conn: sqlite3.Connection) -> None:
    roles = {r["role"] for r in seeded_conn.execute("SELECT role FROM question_tags")}
    assert roles == {"key"}


def test_role_outside_the_three_values_is_rejected(seeded_conn: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        seeded_conn.execute(
            "INSERT INTO question_tags (question_id, tag, role) VALUES (1, 'x', 'primary')"
        )


def test_add_tag_stores_the_requested_role(seeded_conn: sqlite3.Connection) -> None:
    n = questions_repo.mass_action(
        seeded_conn, [1, 2], "add_tag", {"tag": "Point Finding", "role": "task"}
    )
    assert n == 2
    rows = seeded_conn.execute(
        "SELECT role FROM question_tags WHERE tag = 'Point Finding'"
    ).fetchall()
    assert [r["role"] for r in rows] == ["task", "task"]


def test_add_tag_defaults_to_key(seeded_conn: sqlite3.Connection) -> None:
    questions_repo.mass_action(seeded_conn, [3], "add_tag", {"tag": "Pigeonhole Principle"})
    role = seeded_conn.execute(
        "SELECT role FROM question_tags WHERE tag = 'Pigeonhole Principle'"
    ).fetchone()["role"]
    assert role == "key"


def test_add_tag_rejects_an_unknown_role(seeded_conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError):
        questions_repo.mass_action(seeded_conn, [3], "add_tag", {"tag": "x", "role": "main"})
