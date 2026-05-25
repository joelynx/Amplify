"""Rotating file logger for the desktop runtime.

Spec §14: a single rotating file at `app/data/appdata/logs/app.log`, 1 MB × 3 backups, UTF-8.
JS-side console.log is forwarded into the same logger via an IPC `log(level, message)` call
(wired in `app/ipc/api.py`).
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s %(message)s"
_MAX_BYTES = 1 * 1024 * 1024
_BACKUP_COUNT = 3

_configured = False


def appdata_dir() -> Path:
    """Resolve `app/data/appdata/`. Created on demand."""
    here = Path(__file__).resolve().parent
    d = here / "data" / "appdata"
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_path() -> Path:
    logs = appdata_dir() / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs / "app.log"


def setup_logging(level: int = logging.INFO) -> Path:
    """Configure root logger once. Idempotent."""
    global _configured
    target = log_path()
    if _configured:
        return target

    root = logging.getLogger()
    root.setLevel(level)

    file_handler = RotatingFileHandler(
        target,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(file_handler)

    stderr = logging.StreamHandler(stream=sys.stderr)
    stderr.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(stderr)

    _configured = True
    return target
