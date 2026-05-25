"""In-process registry of live QuizSessions.

Sessions are not persisted between app launches — closing the window mid-quiz
drops the session. The quizzes / quiz_questions tables get written at start,
and a quiz_attempts row gets written on finish.
"""

from __future__ import annotations

import threading

from app.interactive.models import QuizSession

_lock = threading.Lock()
_sessions: dict[str, QuizSession] = {}


def register(session: QuizSession) -> None:
    with _lock:
        _sessions[session.quiz_id] = session


def get(quiz_id: str) -> QuizSession | None:
    with _lock:
        return _sessions.get(quiz_id)


def drop(quiz_id: str) -> None:
    with _lock:
        _sessions.pop(quiz_id, None)


def active_ids() -> list[str]:
    with _lock:
        return list(_sessions.keys())
