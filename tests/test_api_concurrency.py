"""Regression: concurrent js_api calls must not share a sqlite3 connection.

PyWebView runs each js_api call on its own thread. With one shared connection,
the burst of reads a page load fires raised `InterfaceError: bad parameter or
other API misuse` / `no more rows available` and silently returned other
queries' rows (logged since 2026-05). `Api` now opens a connection per thread.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from app.ipc.api import Api
from app.persistence.db import migrate
from app.persistence.ingest.seed import _seed_config_defaults

# The reads the frontend fires together on page load (the ones in the crash log).
_PAGE_LOAD_CALLS = [
    ("get_config", ("THEME_SELECTED",)),
    ("get_config", ("DEFAULT_NO_QUESTIONS",)),
    ("get_sources", (None,)),
    ("get_types", (None,)),
    ("get_all_tags", (None,)),
    ("count_matching_questions", ({},)),
    ("search_questions", (None,)),
]


def _open(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """On-disk DB (per-thread connections can't share `:memory:`), big enough
    that the page-load queries overlap in time."""
    path = tmp_path / "amplify.db"
    conn = _open(path)
    conn.execute("PRAGMA journal_mode = WAL")
    migrate(conn)
    _seed_config_defaults(conn)
    conn.executemany(
        """
        INSERT INTO questions (topic, branch, subtopic, latexcode, type, source, latex_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (f"T{i % 7}", f"B{i % 5}", f"S{i % 3}", f"Q{i}", ("proof", "numerical")[i % 2],
             f"Source {i % 40}", f"h{i}")
            for i in range(3000)
        ],
    )
    conn.executemany(
        "INSERT INTO question_tags (question_id, tag) VALUES (?, ?)",
        [(i, f"tag{i % 50}") for i in range(1, 3001)],
    )
    conn.commit()
    conn.close()
    return path


def _hammer(api: Api, rounds: int = 25) -> tuple[list[str], list[str]]:
    """Fire the page-load calls simultaneously, `rounds` times, each on its own
    thread like PyWebView. Returns (exceptions, calls whose result differed
    from a sequential baseline)."""
    baseline = [repr(getattr(api, name)(*args)) for name, args in _PAGE_LOAD_CALLS]
    errors: list[str] = []
    wrong: list[str] = []
    for _ in range(rounds):
        barrier = threading.Barrier(len(_PAGE_LOAD_CALLS))

        def call(barrier: threading.Barrier, i: int, name: str, args: tuple) -> None:
            barrier.wait()
            try:
                if repr(getattr(api, name)(*args)) != baseline[i]:
                    wrong.append(name)
            except Exception as e:  # noqa: BLE001 - recording, not handling
                errors.append(f"{name}: {type(e).__name__}: {e}")

        threads = [
            threading.Thread(target=call, args=(barrier, i, name, args))
            for i, (name, args) in enumerate(_PAGE_LOAD_CALLS)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    return errors, wrong


def test_concurrent_page_load_calls_are_isolated(db_path: Path) -> None:
    errors, wrong = _hammer(Api(lambda: _open(db_path)))
    assert errors == []
    assert wrong == []


def test_one_connection_per_thread(db_path: Path) -> None:
    api = Api(lambda: _open(db_path))
    main_conn = api._conn
    assert api._conn is main_conn  # reused within a thread

    seen: list[sqlite3.Connection] = []
    t = threading.Thread(target=lambda: seen.append(api._conn))
    t.start()
    t.join()
    assert seen[0] is not main_conn
