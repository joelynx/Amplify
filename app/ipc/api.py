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
import os
import sqlite3
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import webview

from app.core.filters import FilterError
from app.core.models import Subject
from app.core.selection import pick
from app.core.stats import compute_stats, subject_distribution, topic_distribution
from app.persistence.repositories import configs as configs_repo
from app.persistence.repositories import psets as psets_repo
from app.persistence.repositories import questions as questions_repo
from app.persistence.repositories import subjects as subjects_repo
from app.persistence.repositories import templates as templates_repo
from app.tex.pdfgen import assemble, compile_to_pdf

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

    def get_types(self, filters: dict[str, Any] | None = None) -> list[str]:
        if filters is None:
            return questions_repo.distinct_types(self._conn)
        s = _resolve_subject(self._conn, filters.get("subject"))
        # Strip the self-key so the dropdown shows reachable options rather
        # than the currently-selected subset (spec §7.3 dynamic-dropdown rule).
        stripped = {**filters, "types": []}
        try:
            return questions_repo.distinct_types(self._conn, stripped, subject=s)
        except FilterError as e:
            _log.info("get_types filter error: %s", e)
            return []

    def get_sources(self, filters: dict[str, Any] | None = None) -> list[str]:
        if filters is None:
            return questions_repo.distinct_sources(self._conn)
        s = _resolve_subject(self._conn, filters.get("subject"))
        stripped = {**filters, "sources": []}
        try:
            return questions_repo.distinct_sources(self._conn, stripped, subject=s)
        except FilterError as e:
            _log.info("get_sources filter error: %s", e)
            return []

    def get_all_tags(self, filters: dict[str, Any] | None = None) -> list[str]:
        s = _resolve_subject(self._conn, (filters or {}).get("subject"))
        # Strip the tag clause so the dropdown shows tags that *could be added*,
        # not just the intersection of already-selected tags.
        stripped = {**(filters or {}), "tags": {"compulsory": [], "optional": [], "excluded": []}}
        try:
            return questions_repo.all_tags(self._conn, stripped, subject=s)
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

    def load_subject(self, name: str) -> dict[str, Any] | None:
        s = subjects_repo.get(self._conn, name)
        if s is None:
            return None
        return {
            "name": s.name,
            **s.to_payload(),
            "is_active": s.is_active,
        }

    def save_subject(self, name: str, payload: dict[str, Any]) -> None:
        if not name:
            raise ValueError("subject name cannot be empty")
        existing = subjects_repo.get(self._conn, name)
        subj = Subject(
            name=name,
            topics=list(payload.get("topics") or []),
            excluded_branches=dict(payload.get("excluded_branches") or {}),
            excluded_subtopics=dict(payload.get("excluded_subtopics") or {}),
            description=str(payload.get("description") or ""),
            schema_version=int(payload.get("schema_version") or 1),
            is_active=bool(existing.is_active) if existing else False,
        )
        subjects_repo.save(self._conn, subj)

    def delete_subject(self, name: str) -> None:
        subjects_repo.delete(self._conn, name)

    def rename_subject(self, old_name: str, new_name: str) -> None:
        if not new_name:
            raise ValueError("subject name cannot be empty")
        if old_name == new_name:
            return
        if subjects_repo.exists(self._conn, new_name):
            raise ValueError(f"subject named {new_name!r} already exists")
        subjects_repo.rename(self._conn, old_name, new_name)

    def subject_name_available(self, name: str) -> bool:
        if not name:
            return False
        return not subjects_repo.exists(self._conn, name)

    def activate_subject(self, name: str | None) -> None:
        subjects_repo.activate(self._conn, name)

    def export_subject_to_file(self, name: str) -> str | None:
        """Open the save dialog, write the §3.6 payload (plus name) as pretty JSON."""
        import json as _json

        s = subjects_repo.get(self._conn, name)
        if s is None:
            raise ValueError(f"no subject named {name!r}")
        windows = webview.windows
        if not windows:
            return None
        result = windows[0].create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=f"{name}.json",
            file_types=("JSON Files (*.json)",),
        )
        if not result:
            return None
        path = result[0] if isinstance(result, list | tuple) else result
        if not path:
            return None
        payload = {"name": s.name, **s.to_payload()}
        Path(str(path)).write_text(_json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)

    def import_subject_from_file(self) -> dict[str, Any] | None:
        """Open-file dialog; parse the JSON; return payload. Frontend handles
        save + name-conflict UI."""
        import json as _json

        windows = webview.windows
        if not windows:
            return None
        result = windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("JSON Files (*.json)",),
            allow_multiple=False,
        )
        if not result:
            return None
        path = result[0] if isinstance(result, list | tuple) else result
        if not path:
            return None
        raw = Path(str(path)).read_text(encoding="utf-8")
        try:
            data = _json.loads(raw)
        except _json.JSONDecodeError as e:
            raise ValueError(f"not a valid JSON file: {e}") from e
        if "name" not in data:
            raise ValueError("subject JSON must contain a 'name' field")
        return data

    def list_templates(self) -> list[str]:
        return templates_repo.list_names(self._conn)

    def template_name_available(self, name: str) -> bool:
        if not name:
            return False
        return not templates_repo.exists(self._conn, name)

    def load_template(self, name: str) -> dict[str, Any] | None:
        t = templates_repo.get(self._conn, name)
        return templates_repo.to_payload(t) if t else None

    def save_template(self, name: str, payload: dict[str, Any]) -> None:
        if not name:
            raise ValueError("template name cannot be empty")
        full = {**payload, "name": name}
        templates_repo.save(self._conn, templates_repo.from_payload(full))

    def delete_template(self, name: str) -> None:
        templates_repo.delete(self._conn, name)

    def rename_template(self, old_name: str, new_name: str) -> None:
        if not new_name:
            raise ValueError("template name cannot be empty")
        if old_name != new_name and templates_repo.exists(self._conn, new_name):
            raise ValueError(f"template named {new_name!r} already exists")
        templates_repo.rename(self._conn, old_name, new_name)

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

    # ---- Step 5: PDF generation (§5.2 / §6) ------------------------------

    def generate_pdf(self, filters: dict[str, Any], output_settings: dict[str, Any]) -> dict[str, Any]:
        """Run the full Generate flow: select → assemble → compile → write rows."""
        save_dir_raw = output_settings.get("save_directory")
        if not save_dir_raw:
            return {"success": False, "errors": "save_directory is required"}
        save_dir = Path(save_dir_raw)

        s = _resolve_subject(self._conn, filters.get("subject"))
        try:
            selection = pick(self._conn, filters, int(output_settings.get("n_questions", 10)), subject=s)
        except FilterError as e:
            return {"success": False, "errors": str(e)}

        if not selection.questions:
            return {"success": False, "errors": "no questions match the current filters"}

        tex = assemble(
            self._conn,
            selection.questions,
            output_settings,
            subject=(s.name if s else None),
        )

        # The assembly already invents a pset_id from the subject+timestamp; we
        # re-derive the same convention here so the .pdf filename matches the
        # pset_id we'll store.
        from datetime import datetime as _dt

        pset_id = f"{(s.name if s else 'PSet').replace(' ', '_')}_{_dt.now().strftime('%Y%m%d_%H%M%S')}"
        result = compile_to_pdf(tex, save_dir, pset_id)

        if not result.success:
            return {
                "success": False,
                "pset_id": pset_id,
                "fallback": str(result.fallback) if result.fallback else None,
                "errors": result.errors,
                "shortfall": selection.shortfall,
            }

        psets_repo.insert_pset(
            self._conn,
            pset_id=pset_id,
            subject=(s.name if s else None),
            filters=filters,
            output_settings=output_settings,
            template_name=output_settings.get("template_name"),
            question_ids=[q.question_id for q in selection.questions],
        )

        return {
            "success": True,
            "pset_id": pset_id,
            "path": str(result.path) if result.path else None,
            "shortfall": selection.shortfall,
        }

    def export_tex(self, filters: dict[str, Any], output_settings: dict[str, Any]) -> dict[str, Any]:
        """Build the `.tex` string and write it to `save_directory`. No PDF compile."""
        save_dir_raw = output_settings.get("save_directory")
        if not save_dir_raw:
            return {"success": False, "errors": "save_directory is required"}
        save_dir = Path(save_dir_raw)

        s = _resolve_subject(self._conn, filters.get("subject"))
        try:
            selection = pick(self._conn, filters, int(output_settings.get("n_questions", 10)), subject=s)
        except FilterError as e:
            return {"success": False, "errors": str(e)}

        if not selection.questions:
            return {"success": False, "errors": "no questions match the current filters"}

        tex = assemble(self._conn, selection.questions, output_settings, subject=(s.name if s else None))

        from datetime import datetime as _dt

        pset_id = f"{(s.name if s else 'PSet').replace(' ', '_')}_{_dt.now().strftime('%Y%m%d_%H%M%S')}"
        save_dir.mkdir(parents=True, exist_ok=True)
        path = save_dir / f"{pset_id}.tex"
        path.write_text(tex, encoding="utf-8")
        return {"success": True, "path": str(path), "shortfall": selection.shortfall}

    # ---- Step 8: history (§5.4 / §8.5) -----------------------------------

    def list_psets(
        self,
        subject: str | None = None,
        date_range: dict[str, str | None] | None = None,
    ) -> list[dict[str, Any]]:
        dr = date_range or {}
        summaries = psets_repo.list_summaries(
            self._conn,
            subject=subject,
            date_from=dr.get("from") or None,
            date_to=dr.get("to") or None,
        )
        return [asdict(s) for s in summaries]

    def load_pset(self, pset_id: str) -> dict[str, Any] | None:
        p = psets_repo.get(self._conn, pset_id)
        if p is None:
            return None
        out = asdict(p)
        out["save_directory"] = psets_repo.get_save_directory(self._conn, pset_id)
        out["include_sources"] = psets_repo.get_include_sources(self._conn, pset_id)
        return out

    def delete_pset(self, pset_id: str) -> None:
        psets_repo.delete(self._conn, pset_id)

    def get_pset_filters(self, pset_id: str) -> dict[str, Any] | None:
        return psets_repo.get_filters_payload(self._conn, pset_id)

    def _resolve_pset_pdf_path(self, pset_id: str) -> Path | None:
        """Look at the recorded save_directory first; fall back to the user's
        current default save dir from configs."""
        candidates: list[Path] = []
        sd = psets_repo.get_save_directory(self._conn, pset_id)
        if sd:
            candidates.append(Path(sd) / f"{pset_id}.pdf")
        fallback = configs_repo.get(self._conn, "FILE_SAVE_LOCATION")
        if isinstance(fallback, str) and fallback:
            candidates.append(Path(fallback) / f"{pset_id}.pdf")
        for c in candidates:
            if c.exists():
                return c
        return None

    def open_pset_file(self, pset_id: str) -> dict[str, Any]:
        path = self._resolve_pset_pdf_path(pset_id)
        if path is None:
            return {"success": False, "errors": "PDF not found at original or current save dir"}
        self.open_file(str(path))
        return {"success": True, "path": str(path)}

    def re_export_pset_pdf(self, pset_id: str) -> dict[str, Any]:
        """Recompile the same questions with the stored layout settings.

        Writes to the original save_directory when available, else to the
        user's current FILE_SAVE_LOCATION (spec §8.5).
        """
        pset = psets_repo.get(self._conn, pset_id)
        if pset is None:
            return {"success": False, "errors": f"unknown pset {pset_id!r}"}

        save_dir_raw = psets_repo.get_save_directory(self._conn, pset_id)
        if not save_dir_raw or not Path(save_dir_raw).exists():
            fallback = configs_repo.get(self._conn, "FILE_SAVE_LOCATION")
            if not (isinstance(fallback, str) and fallback):
                return {"success": False, "errors": "no save_directory recorded and no default configured"}
            save_dir_raw = fallback
        save_dir = Path(save_dir_raw)

        # Reload the original question objects in order.
        questions = []
        for qid in pset.question_ids:
            q = questions_repo.get_by_id(self._conn, qid)
            if q is None:
                continue
            questions.append(q)
        if not questions:
            return {"success": False, "errors": "pset has no extant questions"}

        output_settings = {
            "solutions": pset.solutions or "none",
            "include_sources": psets_repo.get_include_sources(self._conn, pset_id),
        }
        tex = assemble(
            self._conn,
            questions,
            output_settings,
            subject=pset.subject,
            pset_id=pset_id,
        )
        result = compile_to_pdf(tex, save_dir, pset_id)
        if not result.success:
            return {
                "success": False,
                "pset_id": pset_id,
                "fallback": str(result.fallback) if result.fallback else None,
                "errors": result.errors,
            }
        return {"success": True, "pset_id": pset_id, "path": str(result.path) if result.path else None}

    # ---- Step 7: stats v1 (§5.6 / §9) ------------------------------------

    def get_stats(
        self,
        subject: str | None = None,
        date_range: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        s = _resolve_subject(self._conn, subject)
        dr = (
            (date_range or {}).get("from") or None,
            (date_range or {}).get("to") or None,
        )
        bundle = compute_stats(self._conn, s, dr)
        return {
            "psets_generated": bundle.psets_generated,
            "total_questions_seen": bundle.total_questions_seen,
            "unique_questions_seen": bundle.unique_questions_seen,
            "fraction_questions_seen": bundle.fraction_questions_seen,
            "max_questions_in_single_pset": bundle.max_questions_in_single_pset,
            "max_question_multiplicity": bundle.max_question_multiplicity,
            "avg_question_multiplicity": bundle.avg_question_multiplicity,
            "avg_difficulty_rating": bundle.avg_difficulty_rating,
            "total_questions_in_subject": bundle.total_questions_in_subject,
        }

    def get_subject_distribution(
        self, date_range: dict[str, str | None] | None = None
    ) -> list[dict[str, Any]]:
        dr = ((date_range or {}).get("from") or None, (date_range or {}).get("to") or None)
        return subject_distribution(self._conn, dr)

    def get_topic_distribution(
        self,
        subject: str | None = None,
        date_range: dict[str, str | None] | None = None,
    ) -> list[dict[str, Any]]:
        s = _resolve_subject(self._conn, subject)
        dr = ((date_range or {}).get("from") or None, (date_range or {}).get("to") or None)
        return topic_distribution(self._conn, s, dr)

    def open_file(self, path: str) -> None:
        """Open `path` in the OS default application (file viewer)."""
        p = Path(path)
        if not p.exists():
            _log.warning("open_file: path does not exist: %s", p)
            return
        try:
            if sys.platform == "win32":
                os.startfile(str(p))  # noqa: S606 — intentional, user-chosen path
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
        except Exception as e:
            _log.warning("open_file failed for %s: %s", p, e)
