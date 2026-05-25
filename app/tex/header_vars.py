"""Header-variable substitution (spec §6.4).

| token   | resolves to                                |
| ------- | ------------------------------------------ |
| `<S>`   | subject                                    |
| `<T>`   | comma-joined topic list                    |
| `<N>`   | number of questions                        |
| `<K>`   | comma-joined source list ("All" if empty)  |
| `<Q>`   | comma-joined question type list            |
| `<src>` | per-question source string (in body only)  |
| `<P>`   | PSet ID (== filename)                      |
| `<d>`   | date `DD-MM-YYYY`                          |
| `<D>`   | date `Day, DD Month YYYY`                  |

The substitutions run on the **sanitized** header strings — the user's input is
already escaped (or rejected) by `app/tex/sanitize.py` before we touch tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class HeaderContext:
    subject: str = ""
    topic_list: list[str] = field(default_factory=list)
    n_questions: int = 0
    source_list: list[str] = field(default_factory=list)
    type_list: list[str] = field(default_factory=list)
    pset_id: str = ""
    now: datetime = field(default_factory=datetime.now)


def _replace_token(s: str, token: str, value: str) -> str:
    return s.replace(token, value)


def substitute(text: str, ctx: HeaderContext) -> str:
    """Apply every `<X>` substitution. `<src>` is intentionally *not* expanded
    here — it's a per-question token consumed by the body assembler."""
    out = text
    out = _replace_token(out, "<S>", ctx.subject)
    out = _replace_token(out, "<T>", ", ".join(ctx.topic_list))
    out = _replace_token(out, "<N>", str(ctx.n_questions))
    out = _replace_token(out, "<K>", ", ".join(ctx.source_list) if ctx.source_list else "All")
    out = _replace_token(out, "<Q>", ", ".join(ctx.type_list))
    out = _replace_token(out, "<P>", ctx.pset_id)
    out = _replace_token(out, "<d>", ctx.now.strftime("%d-%m-%Y"))
    out = _replace_token(out, "<D>", ctx.now.strftime("%A, %d %B %Y"))
    return out
