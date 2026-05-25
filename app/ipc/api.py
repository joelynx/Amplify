"""IPC surface exposed to the React frontend via PyWebView's `js_api` bridge.

Every method on `Api` becomes a `window.pywebview.api.<name>()` call in JS.
Inputs and outputs must be JSON-serializable. Spec §5.

Surface so far:
- Step 1: ping, log
- Step 3: count_matching_questions, get_random_questions, get_topics,
  get_branches, get_subtopics, get_concept_tree, get_types, get_sources,
  get_all_tags.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import asdict
from typing import Any

import webview

from app.core.filters import FilterError
from app.core.models import Subject
from app.core.selection import pick
from app.persistence.repositories import configs as configs_repo
from app.persistence.repositories import questions as questions_repo
from app.persistence.repositories import subjects as subjects_repo
from app.persistence.repositories import templates as templates_repo

_log = logging.getLogger("amplify.ipc")
_js = logging.getLogger("amplify.js")

_LEVEL_MAP: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def _resolve_subject(conn: sqlite3.Connection, name: str | None) -> Subject | None:
    """The filter `subject` field is a name; resolve it to a payload via the repo.

    Returns None when the name is None/empty/missing. Returns None and logs a
    warning when the name doesn't resolve — never raises, so the form stays
    usable while the user is mid-edit.
    """
    if not name:
        return None
    s = subjects_repo.get(conn, name)
    if s is None:
        _log.warning("subject %r not found; treating as no subject", name)
    return s


class Api:
    """The PyWebView js_api. Methods become `window.pywebview.api.<name>`."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ---- Step 1: health + logging ----------------------------------------

    def ping(self) -> str:
        _log.debug("ping")
        return "pong"

    def log(self, level: str, message: str) -> None:
        lvl = _LEVEL_MAP.get((level or "info").lower(), logging.INFO)
        _js.log(lvl, message)

    # ---- Step 3: hierarchy / dropdowns (§5.1) ----------------------------

    def get_topics(self, subject: str | None = None, in_syllabus_only: bool = True) -> list[str]:
        s = _resolve_subject(self._conn, subject)
        return questions_repo.distinct_topics(self._conn, s, in_syllabus_only)

    def get_branches(self, subject: str | None, topic: str, in_syllabus_only: bool = True) -> list[str]:
        s = _resolve_subject(self._conn, subject)
        return questions_repo.distinct_branches(self._conn, s, topic, in_syllabus_only)

    def get_subtopics(
        self, subject: str | None, topic: str, branch: str, in_syllabus_only: bool = True
    ) -> list[str]:
        s = _resolve_subject(self._conn, subject)
        return questions_repo.distinct_subtopics(self._conn, s, topic, branch, in_syllabus_only)

    def get_concept_tree(
        self, subject: str | None = None, in_syllabus_only: bool = True
    ) -> dict[str, dict[str, list[str]]]:
        s = _resolve_subject(self._conn, subject)
        return questions_repo.concept_tree(self._conn, s, in_syllabus_only)

    def get_types(self) -> list[str]:
        return questions_repo.distinct_types(self._conn)

    def get_sources(self) -> list[str]:
        return questions_repo.distinct_sources(self._conn)

    def get_all_tags(self, filters: dict[str, Any] | None = None) -> list[str]:
        s = _resolve_subject(self._conn, (filters or {}).get("subject"))
        try:
            return questions_repo.all_tags(self._conn, filters, subject=s)
        except FilterError as e:
            _log.info("get_all_tags filter error: %s", e)
            return []

    # ---- Step 3: generation reads (§5.2) ---------------------------------

    def count_matching_questions(self, filters: dict[str, Any]) -> int:
        s = _resolve_subject(self._conn, filters.get("subject"))
        try:
            return questions_repo.count_matching(self._conn, filters, subject=s)
        except FilterError as e:
            _log.info("count_matching_questions filter error: %s", e)
            return 0

    def get_random_questions(self, filters: dict[str, Any], n: int) -> dict[str, Any]:
        s = _resolve_subject(self._conn, filters.get("subject"))
        try:
            result = pick(self._conn, filters, int(n), subject=s)
        except FilterError as e:
            return {"questions": [], "shortfall": int(n), "error": str(e)}
        return {
            "questions": [asdict(q) for q in result.questions],
            "shortfall": result.shortfall,
        }

    # ---- Step 4: subjects, templates, configs, file dialogs --------------

    def list_subjects(self) -> list[str]:
        return subjects_repo.list_names(self._conn)

    def get_active_subject(self) -> str | None:
        s = subjects_repo.get_active(self._conn)
        return s.name if s else None

    def list_templates(self) -> list[str]:
        return templates_repo.list_names(self._conn)

    def get_config(self, key: str) -> Any:
        return configs_repo.get(self._conn, key)

    def set_config(self, key: str, value: Any) -> None:
        configs_repo.set_(self._conn, key, value)

    def pick_save_directory(self) -> str | None:
        """Open the native folder picker, return the chosen path or None."""
        windows = webview.windows
        if not windows:
            _log.warning("pick_save_directory called before window is up")
            return None
        result = windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return None
        # Both tuple-of-paths (old) and list-of-paths (new) shapes appear in the
        # wild across pywebview versions.
        path = result[0] if isinstance(result, list | tuple) else result
        return str(path) if path else None
