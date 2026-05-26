"""Solution-placement layouts (spec §6.5).

Four placement modes feed into the body assembly:

| value                   | layout                                                              |
| ----------------------- | ------------------------------------------------------------------- |
| `none`                  | questions only.                                                     |
| `appendix`              | questions in body; `\\newpage`; "Solutions" section; each `\\textbf{Q#}`. |
| `interleaved`           | each question immediately followed by its solution.                 |
| `outline_appendix`      | as appendix, but uses `solution_outline`; NULL → full solution + warn. |
| `outline_interleaved`   | as interleaved, but uses `solution_outline`; NULL → full solution + warn. |

The spec stores the combobox as a single value; the UI uses `outline_only` plus
a sub-toggle, but by the time we get here it's already collapsed to the two
`outline_*` variants above.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.models import Question

log = logging.getLogger("amplify.tex")

SolutionsMode = str  # "none" | "appendix" | "interleaved" | "outline_appendix" | "outline_interleaved"


@dataclass(slots=True)
class RenderedQuestion:
    """LaTeX fragments for one question. The body assembler stitches these into
    the document according to the placement mode."""

    question_id: int
    body: str  # `\\textbf{Q1}\n...question...`
    solution: str | None  # `Solution: ...` block or None when mode = none


def render_question_body(q: Question, index: int, include_source: bool) -> str:
    """`\\textbf{Q{index}.}` heading inline with the body + optional source line.

    `index` is 1-based question number in the set. The number sits on the same
    line as the question (no trailing `\\\\`) so the page reads as a normal
    enumerated list rather than dropping the body to a new paragraph.
    """
    # `~` ties the number to the first token of the body so a line break can't
    # split them. `\noindent` keeps the question flush to the left margin even
    # when LaTeX would otherwise indent the paragraph.
    chunks = [rf"\noindent\textbf{{Q{index}.}}~{q.latexcode}"]
    if include_source and q.source:
        # rendered after the body, italicized and de-emphasized
        chunks.append(rf"\par\medskip {{\itshape\small Source: {q.source}}}")
    return "\n".join(chunks)


def render_solution_block(q: Question, index: int, use_outline: bool) -> str | None:
    """Solution body. Returns None if mode is `none`. When `use_outline` and
    the outline is missing, fall back to the full solution and log a warning."""
    if use_outline:
        text = q.solution_outline
        if text is None or not text.strip():
            log.warning(
                "outline missing for question_id=%d; falling back to full solution",
                q.question_id,
            )
            text = q.solution
    else:
        text = q.solution
    if text is None or not text.strip():
        return None
    return f"\\noindent\\textbf{{Q{index}.}}~{text}"


def assemble_body(
    questions: list[Question],
    mode: SolutionsMode,
    include_source: bool,
) -> str:
    """Assemble the body chunk (between `\\begin{document}` and `\\end{document}`)."""
    use_outline = mode in ("outline_appendix", "outline_interleaved")
    interleaved = mode in ("interleaved", "outline_interleaved")
    show_solutions = mode != "none"

    body_parts: list[str] = []
    appendix_parts: list[str] = []

    for idx, q in enumerate(questions, start=1):
        body_parts.append(render_question_body(q, idx, include_source))
        if show_solutions:
            sol = render_solution_block(q, idx, use_outline)
            if sol is None:
                continue
            if interleaved:
                body_parts.append(r"\par\smallskip")
                body_parts.append(sol)
            else:
                appendix_parts.append(sol)
        body_parts.append(r"\par\bigskip")

    out = "\n\n".join(body_parts)
    if appendix_parts:
        out += "\n\n\\newpage\n\\section*{Solutions}\n\n" + "\n\n".join(appendix_parts)
    return out
