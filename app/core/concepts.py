"""Concepts: lecture keywords → taxonomy / tags, and questions allocated across
several concepts (Low_Hanging_Fruit.md §3-4).

Matching is offline and deterministic. The student's text is split into terms
(commas, semicolons, new lines); each term is compared with every topic,
branch, subtopic and tag name in scope after the same normalisation on both
sides: lower case, British spellings folded onto American ones, irregular
plurals singularised, filler words dropped, and a light suffix strip so
"diagonalisation" meets "Diagonalizability" and "eigenvalues" meets
"Eigenvalues and Eigenvectors". Abbreviations and course shorthand come from
`app/resources/keyword_aliases.json` ("svd", "ode", "ibp", ...). The student
confirms the matches before anything is selected: short terms are ambiguous.

Retrieval then runs per concept and the question count is split across them,
so one dominant concept cannot crowd out the rest (an averaged query would).
`interleave` orders the result so neighbouring questions usually come from
different concepts.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, TypeVar

from app.core.filters import assemble_where
from app.core.models import Subject

T = TypeVar("T")

_ALIASES_PATH = Path(__file__).resolve().parent.parent / "resources" / "keyword_aliases.json"
KINDS = ("subtopic", "branch", "tag", "topic")
_KIND_RANK = {k: i for i, k in enumerate(KINDS)}
MIN_SCORE = 0.5
MAX_MATCHES = 6
# Weaker best matches, and partial matches tied with many others, are listed
# but left for the student to tick.
PRESELECT_MIN = 0.66
PRESELECT_MAX_TIES = 2

# Dropped before matching, on both sides. Generic course words included, so
# "number theory" meets "Elementary Number Theory".
_STOP = frozenset(
    """a an and the of in on for to with by at from as via vs or its their into using about
    intro introduction basic basics advanced applied general elementary further more simple
    lecture lectures chapter part notes week review today topic topics misc miscellaneous other
    application applications property properties problem problems example examples""".split()
)
_IRREGULAR = {
    "matrices": "matrix", "vertices": "vertex", "indices": "index", "radii": "radius",
    "foci": "focus", "loci": "locus", "criteria": "criterion", "phenomena": "phenomenon",
    "maxima": "maximum", "minima": "minimum", "extrema": "extremum", "spectra": "spectrum",
    "formulae": "formula", "hypotheses": "hypothesis", "analyses": "analysis", "bases": "basis",
    "axes": "axis", "lemmata": "lemma", "series": "series", "data": "data",
}
_SPELLING = (
    (re.compile(r"isation"), "ization"),
    (re.compile(r"is(e|ed|es|ing|able|ability)$"), r"iz\1"),
    (re.compile(r"ys(e|ed|es|ing)$"), r"yz\1"),
    (re.compile(r"our$"), "or"),
    (re.compile(r"tre$"), "ter"),
    (re.compile(r"ll(ed|ing)$"), r"l\1"),
    (re.compile(r"^grey$"), "gray"),
    (re.compile(r"programme"), "program"),
)
# Endings are stripped repeatedly (longest first) while at least five letters
# stay, so "diagonalization" and "diagonal" share the root "diagon".
_ENDINGS = sorted(
    """izability ization izable izing ized izes ize ability ibility istic ist ation ition ality
    ities ity ial ics ic al ed ing es e y ion ence ance ent ant ive ous ly""".split(),
    key=len,
    reverse=True,
)
# Raw tokens sharing a prefix this long match even when their roots differ
# ("differentiation" / "differential").
_SHARED_PREFIX = 8
_TOKEN = re.compile(r"[a-z0-9]+")
# A slash separates terms when spaced ("pdf / cdf") or between two words
# ("pdf/cdf"), not in notation such as "M/M/1".
_SPLIT_TERMS = re.compile(r"[,;\n\r]+|\s+-\s+|\s+/\s*|\s*/\s+|(?<=\w\w)/(?=\w\w)")


def _spell(tok: str) -> str:
    tok = _IRREGULAR.get(tok, tok)
    for pat, rep in _SPELLING:
        tok = pat.sub(rep, tok)
    return tok


@lru_cache(maxsize=8192)
def _root(tok: str) -> str:
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith(("ss", "us", "is")):
        tok = tok[:-1]
    changed = True
    while changed:
        changed = False
        for end in _ENDINGS:
            if tok.endswith(end) and len(tok) - len(end) >= 5:
                tok = tok[: -len(end)]
                changed = True
                break
    return tok


def _shared_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        n += 1
    return n


def _fold(text: str) -> str:
    """Lower case without accents, so "Itô" meets "Ito" and "Möbius" "Mobius"."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def tokens(text: str) -> tuple[str, ...]:
    """Content tokens of `text`, spelling-normalised (not yet stripped)."""
    raw = _TOKEN.findall(_fold(text).replace("'s", "").replace("-", " "))
    return tuple(_spell(t) for t in raw if t not in _STOP)


def _singular(tok: str) -> str:
    return tok[:-1] if len(tok) > 3 and tok.endswith("s") and not tok.endswith(("ss", "us", "is")) else tok


def _tok_match(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) < 4 or len(b) < 4:
        # Short words only meet their plural ("law" / "laws", "map" / "maps").
        return _singular(a) == _singular(b)
    return _root(a) == _root(b) or _shared_prefix(a, b) >= _SHARED_PREFIX


def phrase_score(term: Sequence[str], label: Sequence[str]) -> float:
    """F1 of token matches between a term and a label (0..1); 1 when equal."""
    if not term or not label:
        return 0.0
    if tuple(term) == tuple(label):
        return 1.0
    hit_t = sum(1 for t in term if any(_tok_match(t, w) for w in label))
    hit_l = sum(1 for w in label if any(_tok_match(t, w) for t in term))
    if not hit_t or not hit_l:
        return 0.0
    r, p = hit_t / len(term), hit_l / len(label)
    return 2 * p * r / (p + r)


def _alias_key(text: str) -> str:
    return " ".join(_TOKEN.findall(_fold(text).replace("-", " ")))


@lru_cache(maxsize=1)
def _alias_table() -> tuple[dict[str, list[str]], frozenset[str]]:
    try:
        raw = json.loads(_ALIASES_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, frozenset()
    out: dict[str, list[str]] = {}
    whole: set[str] = set()
    for key, val in raw.items():
        if key.startswith("_"):
            continue
        norm = _alias_key(key.lstrip("="))
        out[norm] = [val] if isinstance(val, str) else list(val)
        if key.startswith("="):
            whole.add(norm)
    return out, frozenset(whole)


def aliases() -> dict[str, list[str]]:
    """Abbreviation → expansions, keys normalised to their token string. A key
    written with a leading "=" ("=power") applies only to a whole term, never
    to one word of a longer term ("power series")."""
    return _alias_table()[0]


def whole_term_aliases() -> frozenset[str]:
    return _alias_table()[1]


@dataclass(slots=True)
class Concept:
    kind: str  # subtopic | branch | tag | topic
    label: str
    path: str  # "Topic › Branch › Subtopic" for taxonomy nodes, "Tag (role)" for tags
    count: int  # questions in scope
    toks: tuple[str, ...] = field(default=(), repr=False)

    def key(self) -> str:
        return f"{self.kind}:{self.path}"


# ---- vocabulary -----------------------------------------------------------

_VOCAB_TTL_S = 120.0
_vocab_cache: dict[str, tuple[float, list[Concept]]] = {}


def _scope(subject: Subject | None, in_syllabus_only: bool) -> tuple[str, list[Any]]:
    payload = subject.to_payload() if subject else None
    return assemble_where({"in_syllabus_only": in_syllabus_only, "reuse_questions": True}, payload)


def vocabulary(
    conn: sqlite3.Connection, subject: Subject | None, in_syllabus_only: bool = False
) -> list[Concept]:
    """Every topic, branch, subtopic and tag in scope with its question count.
    Cached briefly per scope (the Browser asks on every keystroke)."""
    key = json.dumps([subject.to_payload() if subject else None, in_syllabus_only], sort_keys=True)
    hit = _vocab_cache.get(key)
    if hit and time.monotonic() - hit[0] < _VOCAB_TTL_S:
        return hit[1]
    where, params = _scope(subject, in_syllabus_only)
    topics: dict[str, int] = {}
    branches: dict[tuple[str, str], int] = {}
    out: list[Concept] = []
    for topic, branch, sub, n in conn.execute(
        f"SELECT topic, branch, subtopic, COUNT(*) FROM questions WHERE {where} GROUP BY 1, 2, 3", params
    ):
        topics[topic] = topics.get(topic, 0) + n
        branches[(topic, branch)] = branches.get((topic, branch), 0) + n
        out.append(Concept("subtopic", sub, f"{topic} › {branch} › {sub}", int(n), tokens(sub)))
    out += [Concept("branch", b, f"{t} › {b}", n, tokens(b)) for (t, b), n in branches.items()]
    out += [Concept("topic", t, t, n, tokens(t)) for t, n in topics.items()]
    for tag, role, n in conn.execute(
        "SELECT qt.tag, MIN(qt.role), COUNT(DISTINCT qt.question_id) FROM question_tags qt "
        f"WHERE qt.question_id IN (SELECT question_id FROM questions WHERE {where}) GROUP BY qt.tag",
        params,
    ):
        # The path is the concept's key (here and in the Lecture panel), so it names the tag.
        out.append(Concept("tag", tag, f"{tag} ({role})", int(n), tokens(tag)))
    _vocab_cache[key] = (time.monotonic(), out)
    return out


def clear_vocabulary_cache() -> None:
    _vocab_cache.clear()


# ---- matching -------------------------------------------------------------


def split_terms(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for part in _SPLIT_TERMS.split(text or ""):
        term = part.strip(" .\t")
        if term and term.lower() not in seen:
            seen.add(term.lower())
            out.append(term)
    return out


def _expansions(term: str) -> list[tuple[tuple[str, ...], str | None]]:
    """The token sequences to try for a term: the term itself, the term with any
    abbreviation token expanded, and the whole-term alias expansions."""
    al = aliases()
    whole = whole_term_aliases()
    norm = _alias_key(term)
    out: list[tuple[tuple[str, ...], str | None]] = [(tokens(term), None)]
    for exp in al.get(norm, []):
        out.append((tokens(exp), exp))
    words = norm.split()
    if len(words) > 1:
        for i, w in enumerate(words):
            if w in whole:
                continue
            for exp in al.get(w, []):
                swapped = " ".join([*words[:i], exp, *words[i + 1 :]])
                out.append((tokens(swapped), exp))
    return [(t, via) for t, via in out if t]


def match_term(term: str, vocab: list[Concept], limit: int = MAX_MATCHES) -> list[dict[str, Any]]:
    """The best concepts for one term, best first."""
    best: dict[str, tuple[float, Concept, str | None]] = {}
    for toks, via in _expansions(term):
        for c in vocab:
            s = phrase_score(toks, c.toks)
            if s < MIN_SCORE:
                continue
            prev = best.get(c.key())
            if prev is None or s > prev[0]:
                best[c.key()] = (s, c, via)
    ranked = sorted(best.values(), key=lambda x: (-round(x[0], 3), _KIND_RANK[x[1].kind], -x[1].count, x[1].label))
    return [
        {
            "kind": c.kind,
            "label": c.label,
            "path": c.path,
            "count": c.count,
            "score": round(s, 3),
            "via_alias": via,
        }
        for s, c, via in ranked[:limit]
    ]


def match_text(
    conn: sqlite3.Connection, text: str, subject: Subject | None, in_syllabus_only: bool = False
) -> list[dict[str, Any]]:
    """Per term of `text`: its candidate concepts. `selected` marks the ones to
    pre-tick: the top score and anything tied with it, when the top is an exact
    match, or at least PRESELECT_MIN with no more than PRESELECT_MAX_TIES tied."""
    vocab = vocabulary(conn, subject, in_syllabus_only)
    out: list[dict[str, Any]] = []
    for term in split_terms(text):
        matches = match_term(term, vocab)
        top = matches[0]["score"] if matches else 0.0
        tied = [m for m in matches if m["score"] >= top - 1e-9]
        clear = top >= 1.0 - 1e-9 or (top >= PRESELECT_MIN and len(tied) <= PRESELECT_MAX_TIES)
        for m in matches:
            m["selected"] = clear and m in tied
        out.append({"term": term, "matches": matches})
    return out


def search_concepts(
    conn: sqlite3.Connection, text: str, subject: Subject | None, min_score: float = 0.66
) -> list[dict[str, Any]]:
    """Concepts that a free-text search names well (the Browser ORs these in)."""
    vocab = vocabulary(conn, subject)
    return [m for m in match_term(text, vocab, limit=12) if m["score"] >= min_score]


# ---- per-concept retrieval --------------------------------------------------


def concept_filters(base: dict[str, Any], concept: dict[str, Any]) -> dict[str, Any]:
    """`base` narrowed to one concept. The concept replaces the form's tree
    selection (one tree level applies at a time); a tag joins the compulsory
    tags. The subject gate, sources, types and the other flags stay."""
    f = {k: v for k, v in base.items() if k not in ("topics", "branches", "subtopics", "question_ids")}
    kind, label = concept.get("kind"), concept.get("label")
    if kind == "topic":
        f["topics"] = [label]
    elif kind == "branch":
        f["branches"] = [label]
    elif kind == "subtopic":
        f["subtopics"] = [label]
    elif kind == "tag":
        tags = dict(base.get("tags") or {})
        tags["compulsory"] = sorted({*(tags.get("compulsory") or []), label})
        tags["excluded"] = [t for t in (tags.get("excluded") or []) if t != label]
        f["tags"] = tags
    else:
        raise ValueError(f"unknown concept kind: {kind!r}")
    return f


def split_quota(n: int, k: int) -> list[int]:
    return [n // k + (1 if i < n % k else 0) for i in range(k)] if k else []


def allocate(
    concepts: Sequence[dict[str, Any]],
    n: int,
    fetch: Callable[[int, dict[str, Any], set[int]], list[int]],
) -> list[tuple[int, int]]:
    """Split `n` across `concepts` and fill each share with `fetch(i, concept,
    taken) -> question ids` (excluding `taken`). A concept that runs short hands
    its unused share to the others in a second round. Returns (question id,
    concept index) pairs in concept order."""
    k = len(concepts)
    if k == 0 or n <= 0:
        return []
    taken: set[int] = set()
    picked: list[list[int]] = [[] for _ in range(k)]
    exhausted = [False] * k
    want = split_quota(n, k)
    for _round in range(3):
        for i, c in enumerate(concepts):
            need = want[i] - len(picked[i])
            if need <= 0 or exhausted[i]:
                continue
            got = [q for q in fetch(need, c, taken) if q not in taken][:need]
            if len(got) < need:
                exhausted[i] = True
            picked[i] += got
            taken.update(got)
        short = n - sum(len(p) for p in picked)
        open_ = [i for i in range(k) if not exhausted[i]]
        if short <= 0 or not open_:
            break
        for i, extra in zip(open_, split_quota(short, len(open_)), strict=True):
            want[i] = len(picked[i]) + extra
    return [(q, i) for i, ids in enumerate(picked) for q in ids]


def interleave(items: Sequence[T], key: Callable[[T], Any]) -> list[T]:
    """Reorder so adjacent items have different keys wherever possible: each
    step takes from the fullest remaining group whose key differs from the last
    one (ties: the group seen first). Order within a group is kept."""
    groups: dict[Any, list[T]] = {}
    for it in items:
        groups.setdefault(key(it), []).append(it)
    order = list(groups)
    out: list[T] = []
    last: Any = object()
    while groups:
        choices = [g for g in order if g in groups and g != last] or [g for g in order if g in groups]
        g = max(choices, key=lambda x: (len(groups[x]), -order.index(x)))
        out.append(groups[g].pop(0))
        if not groups[g]:
            del groups[g]
        last = g
    return out
