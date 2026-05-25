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

from app.core.difficulty import (
    DEFAULT_WEIGHTS,
    combined_rating,
    get_all_weights,
    pairwise_step,
    pick_pairwise_pair,
    recompute_all,
    set_weights,
    sub_scores_for,
    weights_for_topic,
)
from app.core.difficulty import (
    is_enabled as smart_difficulty_enabled,
)
from app.core.difficulty import (
    set_enabled as set_smart_difficulty_enabled,
)
from app.core.filters import FilterError, assemble_where
from app.core.models import Subject
from app.core.selection import pick
from app.core.similarity import find_similar
from app.core.stats import (
    activity_line,
    calendar_heatmap,
    compute_stats,
    question_multiplicity_dist,
    source_attribution,
    subject_distribution,
    topic_distribution,
)
from app.core.trends import detect_trends
from app.interactive import pbs as pbs_runner
from app.interactive import runner as nonpbs_runner
from app.interactive import session_manager
from app.interactive.models import QuizConfig, QuizSession
from app.interactive.scoring import build_gradient
from app.persistence.ingest.seed import ingest as run_ingest
from app.persistence.ingest.seed_tags import run as run_seed_tags
from app.persistence.repositories import configs as configs_repo
from app.persistence.repositories import psets as psets_repo
from app.persistence.repositories import questions as questions_repo
from app.persistence.repositories import quizzes as quizzes_repo
from app.persistence.repositories import subjects as subjects_repo
from app.persistence.repositories import templates as templates_repo
from app.tex.pdfgen import assemble, compile_to_pdf
from app.tex.sanitize import SanitizeError, sanitize_latex_basic, sanitize_latex_extended
from app.theming import theme_registry

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

    # ---- Step 19: Phase 2 smart difficulty (§5.10 / §13) ----------------

    def recompute_difficulty(self) -> dict[str, Any]:
        """Recompute `questions.difficulty_rating` from local sub-scores.
        Spec §5.10. **Zero outbound network calls** — all inputs are local."""
        result = recompute_all(self._conn)
        return {
            "updated": result.updated,
            "skipped": result.skipped,
            "avg_rating": result.avg_rating,
            "topics_covered": result.topics_covered,
        }

    def get_difficulty_state(self) -> dict[str, Any]:
        return {
            "enabled": smart_difficulty_enabled(self._conn),
            "weights_by_topic": get_all_weights(self._conn),
            "defaults": dict(DEFAULT_WEIGHTS),
            "topics_with_depth": list(
                (configs_repo.get(self._conn, "TOPIC_DEPTH_MAP", {}) or {}).keys()
            ),
        }

    def set_smart_difficulty_enabled(self, on: bool) -> None:
        set_smart_difficulty_enabled(self._conn, bool(on))

    def get_pairwise_pair(self, topic: str | None = None) -> dict[str, Any] | None:
        pair = pick_pairwise_pair(self._conn, topic)
        if pair is None:
            return None
        qid_a, qid_b, topic_name = pair
        qa = questions_repo.get_by_id(self._conn, qid_a)
        qb = questions_repo.get_by_id(self._conn, qid_b)
        sa = sub_scores_for(self._conn, qid_a)
        sb = sub_scores_for(self._conn, qid_b)
        if qa is None or qb is None or sa is None or sb is None:
            return None
        w = weights_for_topic(self._conn, topic_name)
        return {
            "topic": topic_name,
            "weights": w,
            "a": {
                "question": asdict(qa),
                "sub_scores": sa.to_dict(),
                "rating": combined_rating(w, sa),
            },
            "b": {
                "question": asdict(qb),
                "sub_scores": sb.to_dict(),
                "rating": combined_rating(w, sb),
            },
        }

    def submit_pairwise_judgment(
        self,
        harder_id: int,
        easier_id: int,
        magnitude: float = 0.5,
    ) -> dict[str, Any] | None:
        harder = questions_repo.get_by_id(self._conn, int(harder_id))
        easier = questions_repo.get_by_id(self._conn, int(easier_id))
        if harder is None or easier is None:
            return None
        if harder.topic != easier.topic:
            return {"error": "pair must share a topic"}
        hs = sub_scores_for(self._conn, int(harder_id))
        es = sub_scores_for(self._conn, int(easier_id))
        if hs is None or es is None:
            return None
        w = weights_for_topic(self._conn, harder.topic)
        new_w = pairwise_step(w, hs, es, magnitude=float(magnitude))
        set_weights(self._conn, harder.topic, new_w)
        return {"topic": harder.topic, "weights": new_w}

    # ---- Step 18: Phase 2 interactive practice (§5.9 / §10) -------------

    def start_quiz(
        self,
        filters: dict[str, Any],
        settings: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a QuizSession from filters + settings, persist `quizzes` row,
        register in the in-memory session_manager, return seed payload."""
        from datetime import UTC, datetime, timedelta

        template = (settings.get("template") or "FREE_ANSWERING").upper()
        mode: str = "pbs" if template == "PBS" else "non_pbs"

        # PBS: enforce numerical-only at quiz-start.
        if mode == "pbs":
            filters = {**filters, "types": ["numerical"]}

        n = int(settings.get("n_questions", 10))
        pool_size = int(settings.get("pbs_pool_size", n)) if mode == "pbs" else n
        s = _resolve_subject(self._conn, filters.get("subject"))
        try:
            selection = pick(self._conn, filters, pool_size, subject=s)
        except FilterError as e:
            return {"success": False, "error": str(e)}
        if not selection.questions:
            return {"success": False, "error": "no questions match the current filters"}

        config = QuizConfig(
            template=template,  # type: ignore[arg-type]
            n_questions=n,
            time_per_question_s=settings.get("time_per_question_s"),
            total_time_s=settings.get("total_time_s"),
            allow_skips=bool(settings.get("allow_skips", True)),
            show_scoring=bool(settings.get("show_scoring", True)),
            penalize_skips_marks=settings.get("penalize_skips_marks"),
            enable_hints=bool(settings.get("enable_hints", True)),
            instant_scoring=bool(settings.get("instant_scoring", False)),
            show_solutions=bool(settings.get("show_solutions", False)),
            wait_for_correct=bool(settings.get("wait_for_correct", False)),
            gradient_mode=settings.get("gradient_mode", "constant"),
            max_points=float(settings.get("max_points", 10.0)),
            pbs_num_widgets=int(settings.get("pbs_num_widgets", 3)),
            pbs_pool_size=int(settings.get("pbs_pool_size", 10)),
        )

        gradient = build_gradient(config.gradient_mode, len(selection.questions), config.max_points)
        base_scores = {
            q.question_id: gradient[i] for i, q in enumerate(selection.questions)
        }

        quiz_id = quizzes_repo.new_quiz_id("PBS" if mode == "pbs" else "Quiz")
        started_at = datetime.now(UTC)
        deadline = (
            started_at + timedelta(seconds=int(config.total_time_s))
            if config.total_time_s
            else None
        )

        if mode == "pbs":
            num_widgets = min(config.pbs_num_widgets, len(selection.questions))
            visible_slots: list[Any] = list(selection.questions[:num_widgets])
            available_scores = {q.question_id: base_scores[q.question_id] for q in visible_slots}
            pool_index = num_widgets
        else:
            visible_slots = [selection.questions[0]] if selection.questions else [None]
            available_scores = {}
            pool_index = 1

        session = QuizSession(
            quiz_id=quiz_id,
            mode=mode,  # type: ignore[arg-type]
            config=config,
            pool=selection.questions,
            started_at=started_at,
            deadline=deadline,
            visible_slots=visible_slots,
            pool_index=pool_index,
            current_index=0,
            base_scores=base_scores,
            available_scores=available_scores,
            wrong_counts={},
        )
        session_manager.register(session)

        quizzes_repo.insert_quiz(
            self._conn,
            quiz_id=quiz_id,
            subject=(s.name if s else None),
            filters=filters,
            config=config,
            template_name=template,
            question_ids=[q.question_id for q in selection.questions],
        )

        if mode == "pbs":
            initial = pbs_runner.initial_widgets(session)
        else:
            q = session.visible_slots[0]
            initial = [
                {
                    "slot_index": 0,
                    "question": (nonpbs_runner._question_to_dict(q) if q else None),
                    "available_score": base_scores.get(q.question_id, 0.0) if q else 0.0,
                }
            ]

        return {
            "success": True,
            "quiz_id": quiz_id,
            "mode": mode,
            "initial_widgets": initial,
            "total_time_s": config.total_time_s,
            "n_questions": len(selection.questions),
        }

    def quiz_take_widget(self, quiz_id: str, slot_index: int) -> dict[str, Any] | None:
        session = session_manager.get(quiz_id)
        if session is None:
            return None
        if session.mode == "pbs":
            return pbs_runner.take_widget(session, slot_index)
        q = nonpbs_runner.take_widget(session, slot_index)
        if q is None:
            return None
        return {
            "slot_index": 0,
            "question": nonpbs_runner._question_to_dict(q),
            "available_score": session.base_scores.get(q.question_id, 0.0),
        }

    def quiz_submit_answer(
        self,
        quiz_id: str,
        slot_index: int,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        session = session_manager.get(quiz_id)
        if session is None:
            return {"error": "quiz session not found"}
        if session.mode == "pbs":
            return pbs_runner.submit_answer(
                session,
                slot_index=int(slot_index),
                user_answer=str(payload.get("user_answer", "")),
                time_taken_ms=int(payload.get("time_taken_ms", 0)),
            )
        return nonpbs_runner.submit_answer(
            session,
            slot_index=int(slot_index),
            user_answer=str(payload.get("user_answer", "")),
            self_assessment=payload.get("self_assessment"),
            time_taken_ms=int(payload.get("time_taken_ms", 0)),
            hints_used=int(payload.get("hints_used", 0)),
        )

    def quiz_skip(self, quiz_id: str, slot_index: int = 0) -> dict[str, Any]:
        session = session_manager.get(quiz_id)
        if session is None:
            return {"error": "quiz session not found"}
        if session.mode == "pbs":
            return {"error": "PBS doesn't support explicit skip"}
        return nonpbs_runner.skip(session, slot_index)

    def quiz_request_hint(self, quiz_id: str, slot_index: int) -> dict[str, Any]:
        session = session_manager.get(quiz_id)
        if session is None or slot_index >= len(session.visible_slots):
            return {"hint": None, "hint_index": 0}
        q = session.visible_slots[slot_index]
        if q is None or not q.hints:
            return {"hint": None, "hint_index": 0}
        return {"hint": q.hints, "hint_index": 1}

    def quiz_finish(self, quiz_id: str) -> dict[str, Any]:
        session = session_manager.get(quiz_id)
        if session is None:
            return {"error": "quiz session not found"}
        total = sum(a.score for a in session.answers)
        attempt_id = quizzes_repo.insert_attempt(
            self._conn,
            quiz_id=quiz_id,
            date_started=session.started_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
            answers=session.answers,
            total_score=total,
        )
        session_manager.drop(quiz_id)
        return {
            "attempt_id": attempt_id,
            "summary": {
                "total_score": total,
                "n_answered": len(session.answers),
                "n_correct": sum(1 for a in session.answers if a.correct is True),
            },
        }

    def list_quiz_attempts(
        self,
        subject: str | None = None,
        date_range: dict[str, str | None] | None = None,
    ) -> list[dict[str, Any]]:
        dr = ((date_range or {}).get("from") or None, (date_range or {}).get("to") or None)
        return quizzes_repo.list_attempts(
            self._conn, subject=subject, date_from=dr[0], date_to=dr[1]
        )

    def get_quiz_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        return quizzes_repo.get_attempt(self._conn, attempt_id)

    # ---- Step 16: Browser (§5.7 / §8.6) ---------------------------------

    def search_questions(
        self,
        filters: dict[str, Any] | None = None,
        sort_by: str = "question_id_asc",
        page: int = 0,
        page_size: int = 50,
        text_query: str | None = None,
    ) -> dict[str, Any]:
        s = _resolve_subject(self._conn, (filters or {}).get("subject"))
        try:
            questions, total = questions_repo.search(
                self._conn,
                filters,
                sort_by=sort_by,
                page=page,
                page_size=page_size,
                subject=s,
                text_query=text_query,
            )
        except FilterError as e:
            return {"rows": [], "total": 0, "error": str(e)}
        return {"rows": [asdict(q) for q in questions], "total": total}

    def get_question(self, question_id: int) -> dict[str, Any] | None:
        q = questions_repo.get_by_id(self._conn, int(question_id))
        return asdict(q) if q else None

    def mass_action(
        self,
        question_ids: list[int],
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> int:
        return questions_repo.mass_action(self._conn, list(question_ids), action, payload)

    # ---- Step 15: similarity (§5.7 / §12) -------------------------------

    def get_similar_questions(self, question_id: int, k: int = 10) -> list[dict[str, Any]]:
        """Top-k by cosine on `similarity_emb`. Each entry is a Question dict
        plus a `similarity` field in [-1, 1]."""
        hits = find_similar(self._conn, int(question_id), int(k))
        if not hits:
            return []
        # Project the full Question objects for the hit IDs, then re-order to
        # match the score ranking and stitch the score in.
        out: list[dict[str, Any]] = []
        for hit in hits:
            q = questions_repo.get_by_id(self._conn, hit.question_id)
            if q is None:
                continue
            d = asdict(q)
            d["similarity"] = hit.score
            out.append(d)
        return out

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

    # ---- Step 13: maintenance / settings (§5.10 / §8.7) ------------------

    def run_seed_ingest(self) -> dict[str, Any]:
        """Re-run the §4.1 seed ingest from the default paths. Idempotent."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        csv_path = repo_root / "Files" / "TEST.csv"
        lancedb_path = repo_root / "Files" / "Testing" / "lancedb"
        outlines = repo_root / "app" / "data" / "seed" / "pre_db.outlines.json"
        topic_depth = repo_root / "app" / "data" / "seed" / "pre_db.topic_depth.json"
        result = run_ingest(
            self._conn,
            csv_path=csv_path,
            lancedb_path=lancedb_path,
            outlines_json=outlines,
            topic_depth_json=topic_depth,
        )
        return {
            "imported": result.imported,
            "skipped": result.skipped,
            "embeddings_loaded": result.embeddings_loaded,
            "outlines_loaded": result.outlines_loaded,
        }

    def seed_tags_from_metadata(self) -> dict[str, Any]:
        """Derive `question_tags` rows from each question's subtopic/type/source.

        Useful when the seed bundle ships with no tags (like our TEST.csv). The
        operation is idempotent — re-running only inserts tags for new
        questions or new metadata.
        """
        result = run_seed_tags(self._conn)
        return {
            "questions_scanned": result.questions_scanned,
            "rows_inserted": result.rows_inserted,
        }

    def augment_seed_from_csv(self, csv_path: str) -> dict[str, Any]:
        """Spec §4.2: insert new rows from `csv_path` with NULL embeddings/outline."""
        p = Path(csv_path)
        if not p.exists():
            return {"added": 0, "skipped": 0, "errors": [f"file not found: {csv_path}"]}
        try:
            result = run_ingest(self._conn, csv_path=p, lancedb_path=None)
        except Exception as e:
            _log.warning("augment_seed_from_csv failed: %s", e)
            return {"added": 0, "skipped": 0, "errors": [str(e)]}
        return {"added": result.imported, "skipped": result.skipped, "errors": []}

    def factory_reset(self) -> None:
        """Wipe psets/templates/quizzes/subjects/configs. Preserve question content
        (questions, question_tags, embeddings, solution_outline). Spec §5.10."""
        self._conn.executescript(
            """
            DELETE FROM pset_questions;
            DELETE FROM psets;
            DELETE FROM templates;
            DELETE FROM quiz_attempts;
            DELETE FROM quiz_questions;
            DELETE FROM quizzes;
            DELETE FROM subjects;
            DELETE FROM configs;
            """
        )
        self._conn.commit()
        # Re-seed config defaults so the app boots cleanly.
        from app.persistence.ingest.seed import _seed_config_defaults

        _seed_config_defaults(self._conn)
        _log.info("factory reset complete")

    def reset_active_subject(self) -> dict[str, Any]:
        """Zero `times_used` / `interactive_times_used` / `date_last_accessed`
        for questions in the active subject's curricular scope."""
        active = subjects_repo.get_active(self._conn)
        if active is None:
            raise ValueError("no active subject")
        where, params = assemble_where(
            {"in_syllabus_only": False, "reuse_questions": True}, active.to_payload()
        )
        cur = self._conn.execute(
            f"UPDATE questions SET times_used = 0, interactive_times_used = 0, "
            f"date_last_accessed = NULL WHERE {where}",
            params,
        )
        self._conn.commit()
        return {"subject": active.name, "rows_reset": cur.rowcount}

    def get_seed_diagnostics(self) -> dict[str, Any]:
        """Counts for the Settings → Data card."""
        c = self._conn
        total = int(c.execute("SELECT COUNT(*) FROM questions").fetchone()[0])
        with_emb = int(
            c.execute(
                "SELECT COUNT(*) FROM questions WHERE classification_emb IS NOT NULL"
            ).fetchone()[0]
        )
        with_outline = int(
            c.execute(
                "SELECT COUNT(*) FROM questions WHERE solution_outline IS NOT NULL"
            ).fetchone()[0]
        )
        return {
            "embed_model_version": configs_repo.get(c, "EMBED_MODEL_VERSION", "unknown"),
            "questions_total": total,
            "questions_with_embeddings": with_emb,
            "questions_without_embeddings": total - with_emb,
            "questions_with_outlines": with_outline,
            "questions_without_outlines": total - with_outline,
        }

    def restart_app(self) -> None:
        """Spawn a fresh `python -m app.main` and destroy this window."""
        _log.info("restart requested")
        try:
            subprocess.Popen(
                [sys.executable, "-m", "app.main"],
                cwd=str(Path(__file__).resolve().parent.parent.parent),
                close_fds=True,
            )
        except Exception as e:
            _log.warning("could not spawn replacement process: %s", e)
            return
        windows = webview.windows
        if windows:
            windows[0].destroy()

    def pick_csv_file(self) -> str | None:
        windows = webview.windows
        if not windows:
            return None
        result = windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("CSV Files (*.csv)", "All files (*.*)"),
            allow_multiple=False,
        )
        if not result:
            return None
        path = result[0] if isinstance(result, list | tuple) else result
        return str(path) if path else None

    def pick_image_file(self) -> str | None:
        windows = webview.windows
        if not windows:
            return None
        result = windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=(
                "Image Files (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.svg)",
                "All files (*.*)",
            ),
            allow_multiple=False,
        )
        if not result:
            return None
        path = result[0] if isinstance(result, list | tuple) else result
        return str(path) if path else None

    def validate_header_text(self, text: str, level: str) -> str | None:
        """Run the appropriate sanitizer; return None on OK or an error string.

        `level`: 'basic' for left/right header, 'extended' for title/instructions.
        """
        if not text:
            return None
        try:
            if level == "extended":
                sanitize_latex_extended(text)
            else:
                sanitize_latex_basic(text)
        except SanitizeError as e:
            return str(e)
        return None

    # ---- Step 12: themes (§5.8 / §11) ------------------------------------

    def list_themes(self) -> list[dict[str, Any]]:
        return [
            {"id": t.id, "name": t.name, "description": t.description, "preview": None}
            for t in theme_registry.THEMES
        ]

    def set_theme(self, theme_id: str) -> None:
        if theme_registry.get(theme_id) is None:
            raise ValueError(f"unknown theme: {theme_id!r}")
        configs_repo.set_(self._conn, "THEME_SELECTED", theme_id)

    def play_sound(self, event: str) -> None:
        """Resolve the active theme's sound file. No-op when the file is
        missing (spec §11.2 fail-soft). Actual playback happens frontend-side
        via the Web Audio API; this hook is here so a future Python-side
        playback path can drop in without touching IPC."""
        if not event:
            return
        active = configs_repo.get(self._conn, "THEME_SELECTED", "default-light") or "default-light"
        path = theme_registry.resolve_sound_path(str(active), event)
        if path is None:
            _log.debug("play_sound(%s): no asset for theme %s", event, active)
            return
        _log.debug("play_sound(%s): %s", event, path)

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

    def get_source_attribution(
        self,
        subject: str | None = None,
        date_range: dict[str, str | None] | None = None,
    ) -> list[dict[str, Any]]:
        """Step 20: per-source breakdown of practiced questions (pset-scoped)."""
        s = _resolve_subject(self._conn, subject)
        dr = ((date_range or {}).get("from") or None, (date_range or {}).get("to") or None)
        return source_attribution(self._conn, s, dr)

    def get_trends(self, subject: str | None = None) -> list[dict[str, Any]]:
        """Step 21: pattern detectors that surface actionable insights."""
        s = _resolve_subject(self._conn, subject)
        return [asdict(i) for i in detect_trends(self._conn, s)]

    # ---- Step 14: stats v2 (§5.6 / §9) -----------------------------------

    def get_question_multiplicity_dist(
        self, subject: str | None = None
    ) -> dict[int, int]:
        s = _resolve_subject(self._conn, subject)
        return question_multiplicity_dist(self._conn, s)

    def get_calendar_heatmap(self, year: int | None = None) -> dict[str, int]:
        return calendar_heatmap(self._conn, year)

    def get_activity_line(
        self, date_range: dict[str, str | None] | None = None
    ) -> list[dict[str, Any]]:
        dr = ((date_range or {}).get("from") or None, (date_range or {}).get("to") or None)
        return activity_line(self._conn, dr)

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
