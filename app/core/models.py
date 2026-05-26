"""Domain dataclasses. Pure Python — no SQLite, no PyWebView, no filesystem.

Spec §2.2 hard rule 2: `app/core/` is the testable, I/O-free slice. Repositories
in `app/persistence/repositories/` are responsible for translating SQLite rows
into these objects.

Embedding BLOBs are deliberately absent from `Question` — they live only at the
similarity-search code path that reads them via a dedicated SQL projection. Keeps
the common Generate / Browser representations small and JSON-serializable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Question:
    question_id: int
    topic: str
    branch: str
    subtopic: str
    latexcode: str
    latex_hash: str
    in_syllabus: int  # 0 / 1
    times_used: int
    interactive_times_used: int
    tags: list[str] = field(default_factory=list)
    semester: int | None = None
    type: str | None = None
    source: str | None = None
    subsource: str | None = None
    answer: str | None = None
    solution: str | None = None
    solution_outline: str | None = None
    hints: str | None = None
    instructions: str | None = None
    date_last_accessed: str | None = None
    difficulty_rating: float | None = None


@dataclass(slots=True)
class Subject:
    """A user-defined curricular bundle (alias Course). Spec §3.6."""

    name: str
    topics: list[str] = field(default_factory=list)
    excluded_branches: dict[str, list[str]] = field(default_factory=dict)
    excluded_subtopics: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    description: str = ""
    schema_version: int = 1
    is_active: bool = False

    def to_payload(self) -> dict[str, Any]:
        """The §3.6 JSON payload (excludes `name` and `is_active`)."""
        return {
            "topics": self.topics,
            "excluded_branches": self.excluded_branches,
            "excluded_subtopics": self.excluded_subtopics,
            "description": self.description,
            "schema_version": self.schema_version,
        }


@dataclass(slots=True)
class Template:
    """Saved Generate-form snapshot. Spec §3.3."""

    name: str
    n_questions: int
    reuse_questions: int  # 0 / 1
    include_sources: int  # 0 / 1
    in_syllabus_only: int  # 0 / 1
    subject: str | None = None
    topic_list: list[str] = field(default_factory=list)
    branch_list: list[str] = field(default_factory=list)
    subtopic_list: list[str] = field(default_factory=list)
    type_list: list[str] = field(default_factory=list)
    source_list: list[str] = field(default_factory=list)
    tag_list: dict[str, list[str]] = field(default_factory=lambda: {"compulsory": [], "optional": [], "excluded": []})
    min_difficulty: float | None = None
    save_directory: str | None = None
    solutions: str | None = None  # "none" | "appendix" | "interleaved" | "outline_appendix" | "outline_interleaved"


@dataclass(slots=True)
class PSetSummary:
    """Compact view for History / Stats lists. Spec §5.4."""

    pset_id: str
    date_created: str
    n_questions: int
    subject: str | None = None
    template_name: str | None = None
    generation_mode: str = "random"
    diversity_score: float | None = None


@dataclass(slots=True)
class PSet:
    """One generated PDF, with the metadata needed to reproduce it. Spec §3.4."""

    pset_id: str
    date_created: str
    n_questions: int
    reuse_questions: int
    subject: str | None = None
    topic_list: list[str] = field(default_factory=list)
    branch_list: list[str] = field(default_factory=list)
    subtopic_list: list[str] = field(default_factory=list)
    source_list: list[str] = field(default_factory=list)
    type_list: list[str] = field(default_factory=list)
    tag_list: dict[str, list[str]] = field(default_factory=lambda: {"compulsory": [], "optional": [], "excluded": []})
    template_name: str | None = None
    topic_dist: dict[str, int] = field(default_factory=dict)
    subtopic_dist: dict[str, int] = field(default_factory=dict)
    solutions: str | None = None
    question_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class Quiz:
    """Phase 2. Spec §3.5; minimal until Step 18 wires interactive practice."""

    quiz_id: str
    date_created: str
    n_questions: int
    reuse_questions: int
    subject: str | None = None
    template_name: str | None = None
