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
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _db_path() -> Path:
    return appdata_dir() / "amplify.db"


def _open_db() -> sqlite3.Connection:
    """Open the SQLite file, run any un-applied migrations, return the live connection.

    `check_same_thread=False` — PyWebView dispatches js_api calls from a worker
    thread but serializes them, so a single connection is safe.
    """
    p = _db_path()
    conn = sqlite3.connect(p, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    migrate(conn)
    log.info("sqlite handle ok (%s)", p)
    return conn


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
    conn = _open_db()

    api = Api(conn)
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
        conn.close()
        log.info("amplify shutdown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
