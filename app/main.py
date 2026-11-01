"""Amplify entry point. Boots logging + SQLite handle, launches the PyWebView shell.

Dev mode (`AMPLIFY_DEV=1`): loads `http://localhost:5173/` from the Vite dev server
for HMR. Production: loads the built `frontend/dist/index.html` via a `file://` URL.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

import webview

from app.ipc.api import Api
from app.logging_setup import appdata_dir, setup_logging
from app.persistence.db import migrate

log = logging.getLogger("amplify.main")

_DEV_URL = "http://localhost:5173/"
_BUSY_TIMEOUT_S = 10.0
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _db_path() -> Path:
    return appdata_dir() / "amplify.db"


def _connect() -> sqlite3.Connection:
    """Open a connection for one js_api call thread (see `Api`).

    PyWebView does NOT serialize js_api calls — each runs on its own thread — so
    connections are never shared; `check_same_thread` stays on to catch a leak.
    WAL lets the per-thread readers run alongside a writer; `timeout` makes a
    second writer wait for the lock instead of failing with "database is locked".
    """
    conn = sqlite3.connect(_db_path(), timeout=_BUSY_TIMEOUT_S)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _prepare_db() -> None:
    """Switch the file to WAL (persistent) and run any un-applied migrations, once at startup."""
    conn = _connect()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        migrate(conn)
    finally:
        conn.close()
    log.info("sqlite ok (%s)", _db_path())


def _frontend_url() -> str:
    if os.environ.get("AMPLIFY_DEV"):
        log.info("dev mode: loading frontend from %s", _DEV_URL)
        return _DEV_URL
    index = _REPO_ROOT / "frontend" / "dist" / "index.html"
    if not index.exists():
        raise FileNotFoundError(
            f"Frontend build not found at {index}. "
            "Run `npm run build` inside frontend/, or set AMPLIFY_DEV=1 to use the Vite dev server."
        )
    url = index.as_uri()
    log.info("prod mode: loading frontend from %s", url)
    return url


def main() -> int:
    setup_logging()
    log.info("amplify starting")
    _prepare_db()

    api = Api(_connect)
    debug = bool(os.environ.get("AMPLIFY_DEV"))
    try:
        webview.create_window(
            "Amplify",
            _frontend_url(),
            js_api=api,
            width=1280,
            height=820,
            min_size=(960, 640),
        )
        webview.start(debug=debug)
    finally:
        log.info("amplify shutdown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
