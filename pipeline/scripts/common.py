"""Shared helpers for the solution pipeline scripts.

Everything the scripts agree on lives here: paths, config loading, the pipeline
status database, the question fetcher, the solver-output parser, and the
mechanical LaTeX / markdown checks. The API runner (run.py) owns the status
transitions; assemble.py owns storage.

The old solution (questions.solution) is never read by anything that builds a
prompt: fetch_question returns it only so assemble/status code can tell whether
a stored Answer or Hint exists.
"""

from __future__ import annotations

import base64
import datetime as _dt
import json
import os
import re
import sqlite3
import subprocess
from collections import Counter
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPTS_DIR.parent
REPO_DIR = PIPELINE_DIR.parent
CONFIG_PATH = PIPELINE_DIR / "config.json"
PROMPTS_DIR = PIPELINE_DIR / "prompts"
TEMPLATES_DIR = PIPELINE_DIR / "templates"
RUN_LOG = PIPELINE_DIR / "run_log.md"
PROGRESS_JSON = PIPELINE_DIR / "progress.json"

# A rerun can point these at a separate folder / db via environment variables.
OUTPUTS_DIR = Path(os.environ.get("AMPLIFY_PIPELINE_OUTPUTS") or (PIPELINE_DIR / "outputs"))
PIPELINE_DB = Path(os.environ.get("AMPLIFY_PIPELINE_DB") or (PIPELINE_DIR / "pipeline.db"))

# Status values written by run.py:
#   pending       -> selected, not yet in a batch (or returned after an API error)
#   submitted     -> inside an in-flight Message Batch (status.batch_id, pending_attempt)
#   retry         -> output rejected by the checks; resubmitted with feedback in the next batch
#   passed        -> accepted (assembled=1 once stored)
#   skipped_image -> the question needs a figure that cannot go with it; never sent (owner
#                    decision; since config.attach_images, only a missing image file or a
#                    figure the text points at without an \includegraphics)
#   needs_human_review -> final, not stored
# Legacy values from the subagent-era run (passed_after_escalation, low_confidence,
# missing_image, triaged, solved_n, reviewed_n, escalated) are still recognised.
FINAL_STATUSES = {
    "passed",
    "passed_after_escalation",
    "needs_human_review",
    "low_confidence",
    "missing_image",
    "skipped_image",
}
PASS_STATUSES = {"passed", "passed_after_escalation", "low_confidence"}
NOT_STORED_FINAL = {"needs_human_review", "missing_image", "skipped_image"}


def now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def write_text(path: Path, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj) -> None:
    write_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path):
    return json.loads(read_text(path))


def model_display(cfg: dict, model: str | None) -> str:
    """Human name for the attribution line; falls back to the raw model id."""
    return (cfg.get("model_display_names") or {}).get(model or "", model or "unknown model")


# --- app database (read-only unless explicitly opened for field fills) -------


def app_db_path(cfg: dict) -> Path:
    return (REPO_DIR / cfg["paths"]["app_db"]).resolve()


def teximages_dir(cfg: dict) -> Path:
    return (REPO_DIR / cfg["paths"]["teximages"]).resolve()


def app_conn(cfg: dict, *, readonly: bool = True) -> sqlite3.Connection:
    p = app_db_path(cfg)
    if readonly:
        conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    return conn


QUESTION_COLS = (
    "question_id, latexcode, solution, answer, hints, source, subsource, type, topic, branch, subtopic"
)


def fetch_question(app: sqlite3.Connection, qid: int) -> dict | None:
    row = app.execute(f"SELECT {QUESTION_COLS} FROM questions WHERE question_id=?", (qid,)).fetchone()
    return dict(row) if row else None


def source_rank(cfg: dict) -> dict[str, int]:
    """Position of each source in config.sources: that list IS the priority order."""
    return {s: i for i, s in enumerate(cfg["sources"])}


def target_questions(app: sqlite3.Connection, cfg: dict) -> list[tuple[int, str]]:
    """(question_id, source) for every target question, in priority order:
    by the source's position in config.sources, then by question id."""
    srcs = cfg["sources"]
    rank = source_rank(cfg)
    q = f"SELECT question_id, source FROM questions WHERE source IN ({','.join('?' * len(srcs))})"
    rows = [(r[0], r[1]) for r in app.execute(q, srcs)]
    rows.sort(key=lambda t: (rank[t[1]], t[0]))
    return rows


def target_question_ids(app: sqlite3.Connection, cfg: dict) -> list[int]:
    return [qid for qid, _ in target_questions(app, cfg)]


def is_blank(value, sentinels=()) -> bool:
    if value is None:
        return True
    s = str(value).strip()
    if not s:
        return True
    return s.upper() in {x.upper() for x in sentinels}


# --- image detection (questions with images were skipped until config.attach_images) ---

IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
FIGURE_KW = re.compile(
    r"\b(figure|diagram|picture|photograph|illustration|sketch)\b"
    r"|\b(shown|see|given|as)\s+(below|above)\b"
    r"|\bthe following (figure|diagram|picture|graph)\b"
    r"|\bgraph\s+(below|above|shown)\b",
    re.I,
)


def image_reason(latex: str) -> str | None:
    """Why a question counts as 'involves an image', or None. Any
    \\includegraphics reference, or prose that clearly points at a figure that
    is not attached, means the question is skipped."""
    names = IMG_RE.findall(latex)
    if names:
        return "references image(s): " + ", ".join(n.strip() for n in names[:3])
    m = FIGURE_KW.search(latex)
    if m:
        return f"text refers to a figure ('{m.group(0)}')"
    return None


# --- images sent with the question (config.attach_images, owner 2026-11-10) ----------

IMAGE_MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif"}


def question_images(texts: list[str], tex_dir: Path) -> tuple[list[tuple[str, Path]], str | None]:
    """The images that \\includegraphics names in texts, in order and each once, and why they
    cannot all be sent (a missing file, or a type the model cannot read), else None."""
    out: list[tuple[str, Path]] = []
    for name in dict.fromkeys(n.strip() for t in texts for n in IMG_RE.findall(t or "")):
        p = resolve_image(name, tex_dir)
        if p is None:
            return [], f"image file not found: {name}"
        if p.suffix.lower() not in IMAGE_MEDIA:
            return [], f"image the model cannot read: {p.name}"
        out.append((name, p))
    return out, None


def image_blocks(images: list[tuple[str, Path]]) -> list[dict]:
    """The content blocks after the question's text: each image follows a line naming the
    \\includegraphics command it belongs to, so the model can tell which picture the text means."""
    blocks: list[dict] = []
    for name, path in images:
        blocks.append({"type": "text", "text": f"IMAGE \\includegraphics{{{name}}}:"})
        blocks.append({"type": "image", "source": {"type": "base64", "media_type": IMAGE_MEDIA[path.suffix.lower()],
                                                   "data": base64.b64encode(path.read_bytes()).decode("ascii")}})
    return blocks


# --- pipeline database --------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS status (
  question_id      INTEGER PRIMARY KEY,
  status           TEXT NOT NULL,
  level            TEXT,
  attempts         INTEGER NOT NULL DEFAULT 0,
  accepted_attempt INTEGER,
  batch            INTEGER,
  prompt_version   TEXT,
  solver1_model    TEXT, solver1_effort TEXT,
  solver2_model    TEXT, solver2_effort TEXT,
  reviewer_model   TEXT, reviewer_effort TEXT,
  hint_model       TEXT, hint_effort TEXT,
  solver_retries   INTEGER NOT NULL DEFAULT 0,
  review_retries   INTEGER NOT NULL DEFAULT 0,
  hint_retries     INTEGER NOT NULL DEFAULT 0,
  hint_status      TEXT NOT NULL DEFAULT 'none',
  assembled        INTEGER NOT NULL DEFAULT 0,
  image_paths      TEXT,
  note             TEXT,
  created_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
  question_id INTEGER, attempt INTEGER, review_json TEXT, rigor_tex TEXT, created_at TEXT,
  PRIMARY KEY (question_id, attempt)
);
CREATE TABLE IF NOT EXISTS finals (
  question_id        INTEGER PRIMARY KEY,
  status             TEXT,
  final_tex          TEXT,
  solution_tex       TEXT,
  rigor_tex          TEXT,
  takeaways_tex      TEXT,
  answer_type        TEXT,
  answer_tex         TEXT,
  hint_tex           TEXT,
  answer_field_value TEXT,
  hint_field_value   TEXT,
  answer_filled      INTEGER NOT NULL DEFAULT 0,
  hint_filled        INTEGER NOT NULL DEFAULT 0,
  prompt_version     TEXT,
  created_at         TEXT
);
CREATE TABLE IF NOT EXISTS provenance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER, field TEXT, value TEXT, prompt_version TEXT, created_at TEXT, applied_at TEXT
);
CREATE TABLE IF NOT EXISTS batches (
  batch INTEGER PRIMARY KEY, question_ids TEXT, kind TEXT, metrics_json TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, question_id INTEGER, stage TEXT, detail TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS api_batches (
  batch_id       TEXT PRIMARY KEY,
  seq            INTEGER,
  created_at     TEXT,
  n              INTEGER,
  custom_ids     TEXT,
  prompt_version TEXT,
  model          TEXT,
  effort         TEXT,
  system_sha256  TEXT,
  status         TEXT,
  ended_at       TEXT,
  collected_at   TEXT,
  summary_json   TEXT
);
CREATE TABLE IF NOT EXISTS usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER, attempt INTEGER, batch_id TEXT, model TEXT, effort TEXT,
  input_tokens INTEGER, cache_write_tokens INTEGER, cache_read_tokens INTEGER, output_tokens INTEGER,
  stop_reason TEXT, created_at TEXT
);
"""

# Columns added after the first schema; applied with ALTER TABLE on open.
STATUS_EXTRA_COLUMNS = {
    "batch_id": "TEXT",
    "pending_attempt": "INTEGER",
    "api_failures": "INTEGER NOT NULL DEFAULT 0",
    "answer_mismatch": "INTEGER NOT NULL DEFAULT 0",
    # non-math subjects (subjects.py): 'solve' or 'aids', and the question's subject; NULL for math
    "mode": "TEXT",
    "subject": "TEXT",
    # a third, high-effort solve after two solves disagreed with the stored answer (owner 2026-11-07)
    "tiebreak": "INTEGER NOT NULL DEFAULT 0",
    # the first attempt of the review solve that replaces human review (config.subjects.review_*,
    # owner 2026-11-08); NULL when the question never went to it
    "review_from": "INTEGER",
}
FINALS_EXTRA_COLUMNS = {"mode": "TEXT", "answer_key": "TEXT", "book_check": "TEXT"}


def pipe_conn() -> sqlite3.Connection:
    PIPELINE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(PIPELINE_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    have = {r[1] for r in conn.execute("PRAGMA table_info(status)")}
    for col, decl in STATUS_EXTRA_COLUMNS.items():
        if col not in have:
            conn.execute(f"ALTER TABLE status ADD COLUMN {col} {decl}")
    have = {r[1] for r in conn.execute("PRAGMA table_info(finals)")}
    for col, decl in FINALS_EXTRA_COLUMNS.items():
        if col not in have:
            conn.execute(f"ALTER TABLE finals ADD COLUMN {col} {decl}")
    conn.commit()
    return conn


def get_status(conn: sqlite3.Connection, qid: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM status WHERE question_id=?", (qid,)).fetchone()


def upsert_status(conn: sqlite3.Connection, qid: int, **fields) -> None:
    row = get_status(conn, qid)
    now = now_iso()
    if row is None:
        fields.setdefault("status", "pending")
        cols = ["question_id", "created_at", "updated_at"] + list(fields)
        vals = [qid, now, now] + list(fields.values())
        conn.execute(
            f"INSERT INTO status ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", vals
        )
    else:
        fields["updated_at"] = now
        sets = ", ".join(f"{k}=?" for k in fields)
        conn.execute(f"UPDATE status SET {sets} WHERE question_id=?", list(fields.values()) + [qid])
    conn.commit()


def log_event(conn: sqlite3.Connection, qid: int | None, stage: str, detail: str) -> None:
    conn.execute(
        "INSERT INTO events (question_id, stage, detail, created_at) VALUES (?,?,?,?)",
        (qid, stage, detail, now_iso()),
    )
    conn.commit()


def pipeline_wrote(conn: sqlite3.Connection, qid: int, field: str, value, before_id: int | None = None) -> bool:
    """True when `value` (the field's current content in the app database) is exactly what
    the pipeline wrote there earlier, so a newer run may replace it."""
    if value is None:
        return False
    sql = "SELECT 1 FROM provenance WHERE question_id=? AND field=? AND value=? AND applied_at IS NOT NULL AND applied_at NOT LIKE 'skipped%'"
    args: list = [qid, field, value]
    if before_id is not None:
        sql += " AND id < ?"
        args.append(before_id)
    return conn.execute(sql, args).fetchone() is not None


def is_done(row: sqlite3.Row | None) -> bool:
    """A question is finished when it has a final status and, for passing
    statuses, has also been assembled."""
    if row is None:
        return False
    st = row["status"]
    if st not in FINAL_STATUSES:
        return False
    if st in NOT_STORED_FINAL:
        return True
    return bool(row["assembled"])


def q_dir(qid: int) -> Path:
    d = OUTPUTS_DIR / str(qid)
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_progress(conn: sqlite3.Connection) -> dict:
    counts = {
        r[0]: r[1]
        for r in conn.execute("SELECT status, COUNT(*) FROM status GROUP BY status ORDER BY status")
    }
    assembled = conn.execute("SELECT COUNT(*) FROM status WHERE assembled=1").fetchone()[0]
    done = sum(1 for r in conn.execute("SELECT * FROM status") if is_done(r))
    inflight = conn.execute("SELECT COUNT(*) FROM api_batches WHERE collected_at IS NULL").fetchone()[0]
    prog = {
        "updated_at": now_iso(),
        "counts_by_status": counts,
        "assembled": assembled,
        "done": done,
        "api_batches_in_flight": inflight,
    }
    write_json(PROGRESS_JSON, prog)
    return prog


# --- solver output markers ------------------------------------------------------

# v5 (API run): five sections. v4 (legacy subagent run): no rigor notes or hint.
V5_MARKERS = [
    "%%% BEGIN SOLUTION", "%%% END SOLUTION",
    "%%% BEGIN RIGOR NOTES", "%%% END RIGOR NOTES",
    "%%% BEGIN TAKEAWAYS", "%%% END TAKEAWAYS",
    "%%% ANSWER TYPE:",
    "%%% BEGIN ANSWER", "%%% END ANSWER",
    "%%% BEGIN HINT", "%%% END HINT",
]
V4_MARKERS = [
    "%%% BEGIN SOLUTION", "%%% END SOLUTION",
    "%%% BEGIN TAKEAWAYS", "%%% END TAKEAWAYS",
    "%%% ANSWER TYPE:",
    "%%% BEGIN ANSWER", "%%% END ANSWER",
]
ANSWER_TYPES = ("NUMERICAL", "EXPRESSION", "NONE")


def strip_code_fences(text: str) -> tuple[str, bool]:
    """Remove one pair of markdown code fences wrapping the whole reply
    (```latex ... ```), which chat-style replies sometimes add. Returns
    (text, stripped?)."""
    lines = text.replace("\r\n", "\n").strip("\n").split("\n")
    if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]), True
    return text, False


def parse_solver_output(text: str, *, fmt: str = "auto") -> tuple[dict | None, list[str]]:
    """Split a solver reply by its marker lines.

    Returns (parts, errors). parts has solution, rigor (None when NONE or v4),
    takeaways, answer_type, answer, hint (None for v4). On a structural error
    parts is None."""
    if fmt == "auto":
        fmt = "v5" if ("%%% BEGIN RIGOR NOTES" in text or "%%% BEGIN HINT" in text) else "v4"
    markers = V5_MARKERS if fmt == "v5" else V4_MARKERS
    errors: list[str] = []
    lines = text.replace("\r\n", "\n").split("\n")
    positions: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("%%%"):
            continue
        matched = False
        for m in markers:
            if s == m or (m.endswith(":") and s.startswith(m)):
                positions.setdefault(m, []).append(i)
                matched = True
                break
        if not matched:
            errors.append(f"line {i + 1}: unexpected marker line '{s[:60]}'")
    for m in markers:
        n = len(positions.get(m, []))
        if n != 1:
            errors.append(f"marker '{m}' appears {n} times (expected exactly once)")
    if errors:
        return None, errors
    order = [positions[m][0] for m in markers]
    if order != sorted(order):
        return None, ["marker lines are out of order"]
    pos = dict(zip(markers, order))

    def body(begin: str, end: str) -> str:
        return "\n".join(lines[pos[begin] + 1 : pos[end]]).strip()

    # Nothing may appear outside the sections.
    if "\n".join(lines[: order[0]]).strip():
        errors.append("content before the BEGIN SOLUTION marker")
    if "\n".join(lines[order[-1] + 1 :]).strip():
        errors.append(f"content after the {markers[-1]} marker")
    for i, m in enumerate(markers[:-1]):
        if m.startswith("%%% END") or m.endswith(":"):
            if "\n".join(lines[pos[m] + 1 : pos[markers[i + 1]]]).strip():
                errors.append(f"content between sections after '{m}'")

    solution = body("%%% BEGIN SOLUTION", "%%% END SOLUTION")
    takeaways = body("%%% BEGIN TAKEAWAYS", "%%% END TAKEAWAYS")
    atype = lines[pos["%%% ANSWER TYPE:"]].strip()[len("%%% ANSWER TYPE:") :].strip()
    answer = body("%%% BEGIN ANSWER", "%%% END ANSWER")
    if atype not in ANSWER_TYPES:
        errors.append(f"answer type '{atype}' is not one of NUMERICAL, EXPRESSION, NONE")
    if (atype == "NONE") != (answer == "NONE"):
        errors.append("the answer must be NONE if and only if the answer type is NONE")
    rigor = hint = None
    if fmt == "v5":
        rigor = body("%%% BEGIN RIGOR NOTES", "%%% END RIGOR NOTES")
        if rigor == "" or rigor.rstrip(".").strip().upper() == "NONE":
            rigor = None
        hint = body("%%% BEGIN HINT", "%%% END HINT")
        if not hint:
            errors.append("empty hint body")
    if not solution:
        errors.append("empty solution body")
    if not takeaways:
        errors.append("empty takeaways body")
    if "Final answer:" not in solution:
        errors.append("solution body has no 'Final answer:' line")
    parts = {
        "format": fmt,
        "solution": solution,
        "rigor": rigor,
        "takeaways": takeaways,
        "answer_type": atype,
        "answer": answer,
        "hint": hint,
    }
    return parts, errors


def strip_marker_lines(text: str) -> str:
    return "\n".join(l for l in text.split("\n") if not l.strip().startswith("%%%")).strip()


# --- mechanical content checks --------------------------------------------------


def markdown_problems(text: str) -> list[str]:
    probs: list[str] = []
    for i, line in enumerate(text.split("\n"), 1):
        s = line.lstrip()
        if s.startswith("#"):
            probs.append(f"line {i}: markdown heading")
        if re.match(r"[-*]\s", s):
            probs.append(f"line {i}: markdown bullet line")
        if re.match(r"(---|\*\*\*|___)\s*$", s):
            probs.append(f"line {i}: markdown horizontal rule")
    if "**" in text:
        probs.append("markdown bold marker '**'")
    if "`" in text:
        probs.append("backtick character")
    return probs


DENY_COMMANDS = [
    "documentclass", "usepackage", "newcommand", "renewcommand", "def", "DeclareMathOperator",
    "input", "include", "section", "subsection", "subsubsection", "paragraph", "subparagraph",
    "chapter", "title", "maketitle", "label", "ref", "eqref", "pageref", "cite", "footnote",
    "includegraphics", "caption", "url", "href", "vspace", "hspace", "hfill", "vfill",
    "centering", "newpage", "clearpage", "newline", "linebreak", "pagebreak", "mathscr",
    "mathbbm", "color", "textcolor", "degree", "textdegree", "SI", "num", "si", "setcounter",
    "noindent", "par", "smallskip", "medskip", "bigskip", "item" if False else "zzznever",
]

ALLOWED_ENVS = {
    "aligned", "align*", "gathered", "gather*", "cases", "pmatrix", "bmatrix", "vmatrix",
    "Vmatrix", "Bmatrix", "matrix", "smallmatrix", "array", "split", "subarray",
    "itemize", "enumerate", "proof", "claim", "lemma",
}

# Environments that put their contents in math mode when used at top level.
TOP_LEVEL_MATH_ENVS = {"align", "align*", "gather", "gather*", "equation", "equation*", "multline", "multline*"}
# Environments whose rows are separated by \\ (a control space inside them is a lost \\).
ALIGN_ENVS = {
    "align", "align*", "aligned", "gather", "gather*", "gathered", "cases", "pmatrix", "bmatrix",
    "vmatrix", "Vmatrix", "Bmatrix", "matrix", "smallmatrix", "array", "split", "subarray", "multline", "multline*",
}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def text_mode_problems(text: str) -> list[str]:
    """Walk the content tracking math mode; flag constructs that break the
    PDF or display raw in the web view when they appear in text mode."""
    probs: list[str] = []
    in_math = False
    align_depth = 0  # inside aligned / cases / matrix-like environments
    i, n, line = 0, len(text), 1
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch == "\\":
            nxt = text[i + 1] if i + 1 < n else ""
            if nxt in "([":
                in_math = True
                i += 2
                continue
            if nxt in ")]":
                in_math = False
                i += 2
                continue
            if nxt == "\\":
                if not in_math:
                    probs.append(f"line {line}: '\\\\' line break outside math")
                i += 2
                continue
            if nxt in ("\n", "\r"):
                # Backslash-newline is almost always a lost '\\' row separator.
                # A control space ('\ ') is valid LaTeX, also inside alignments
                # (e.g. "1,\ 10,\ 29"); v5 replies come straight from the API,
                # so the JSON-argument backslash loss this rule once caught no
                # longer happens.
                probs.append(f"line {line}: lone backslash before newline (a lost '\\\\' row separator?)")
                i += 2
                continue
            m = re.match(r"\\(begin|end)\{([A-Za-z*]+)\}", text[i:])
            if m:
                env = m.group(2)
                if env in TOP_LEVEL_MATH_ENVS:
                    in_math = m.group(1) == "begin"
                if env in ALIGN_ENVS:
                    align_depth += 1 if m.group(1) == "begin" else -1
                i += m.end()
                continue
            m = re.match(r"\\[A-Za-z]+", text[i:])
            if m:
                i += m.end()
                continue
            i += 2  # escaped single character such as \% or \{
            continue
        if ch == "$":
            # Dollar delimiters are reported separately; just track them.
            if i + 1 < n and text[i + 1] == "$":
                i += 2
            else:
                i += 1
            in_math = not in_math
            continue
        if not in_math and ch in "&#_^~":
            probs.append(f"line {line}: unescaped '{ch}' in text mode")
        i += 1
    return probs


def latex_problems(text: str) -> list[str]:
    probs: list[str] = []
    for cmd in DENY_COMMANDS:
        if re.search(rf"\\{cmd}(?![A-Za-z])", text):
            probs.append(f"forbidden command \\{cmd}")
    begins = Counter(m.group(1) for m in re.finditer(r"\\begin\{([A-Za-z*]+)\}", text))
    ends = Counter(m.group(1) for m in re.finditer(r"\\end\{([A-Za-z*]+)\}", text))
    for env in begins:
        if env not in ALLOWED_ENVS:
            probs.append(f"forbidden environment '{env}'")
    for env in set(begins) | set(ends):
        if begins[env] != ends[env]:
            probs.append(f"unbalanced environment '{env}' ({begins[env]} begin, {ends[env]} end)")
    for i, l in enumerate(text.split("\n"), 1):
        if l.strip().startswith("%%%"):
            continue
        if re.search(r"(?<!\\)%", l):
            probs.append(f"line {i}: '%' comment character")
    bad = sorted({c for c in text if ord(c) > 127})
    if bad:
        probs.append("non-ASCII characters: " + " ".join(f"U+{ord(c):04X}" for c in bad[:12]))
    if text.count("\\(") != text.count("\\)"):
        probs.append("unbalanced \\( \\) delimiters")
    if text.count("\\[") != text.count("\\]"):
        probs.append("unbalanced \\[ \\] delimiters")
    if re.search(r"(?<!\\)\$", text):
        probs.append("dollar-sign math delimiters (use \\( \\) and \\[ \\])")
    depth = 0
    for c in re.sub(r"\\[{}]", "", text):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                probs.append("unbalanced braces (a '}' with no matching '{')")
                break
    if depth > 0:
        probs.append("unbalanced braces (unclosed '{')")
    probs.extend(text_mode_problems(text))
    return _dedupe(probs)


def content_problems(text: str) -> list[str]:
    return markdown_problems(text) + latex_problems(text)


# --- answer normalisation (leak check and field formatting) --------------------


def strip_math_wrappers(s: str) -> str:
    """Remove outer math delimiters, \\boxed{}, and a trailing period, in any
    order of nesting (e.g. '\\( \\boxed{42}. \\)' -> '42')."""
    s = s.strip()
    for _ in range(4):
        before = s
        s = s.rstrip(".").strip()
        for a, b in (("\\(", "\\)"), ("\\[", "\\]"), ("$$", "$$"), ("$", "$")):
            if s.startswith(a) and s.endswith(b) and len(s) >= len(a) + len(b):
                s = s[len(a) : len(s) - len(b)].strip()
        m = re.fullmatch(r"\\boxed\{(.*)\}", s, flags=re.S)
        if m:
            s = m.group(1).strip()
        if s == before:
            break
    return s


_NUM_RE = re.compile(r"^[-+]?\d+(?:\.\d+)?$")
_DISPLAY_HINT = re.compile(
    r"\\begin\{(aligned|cases|pmatrix|bmatrix|vmatrix|matrix|array|gathered|split)\}|\\\\"
)


def format_answer(answer_type: str, raw: str) -> str | None:
    """Answer-field format (format_spec.md section 8): bare digits for a plain
    numerical answer, otherwise inline math \\( ... \\); display math only when
    the answer needs a multi-line environment. NONE -> None. The solver writes
    the answer as bare LaTeX, so this is also what validate.py compiles."""
    if answer_type == "NONE":
        return None
    core = strip_math_wrappers(raw)
    core = re.sub(r"\s+", " ", core).strip()
    if answer_type == "NUMERICAL" and _NUM_RE.match(core.replace(",", "")):
        return core.replace(",", "")
    if "\\(" in core or "\\[" in core:
        # Already a mix of text and inline math (e.g. "(i) \(35\) dollars; (ii) \(30\) dollars"):
        # store as written; wrapping it again would nest math delimiters.
        return core
    if _DISPLAY_HINT.search(core):
        return f"\\[ {core} \\]"
    return f"\\( {core} \\)"


def normalize_answer(s: str) -> str:
    s = strip_math_wrappers(s)
    s = re.sub(r"\\(left|right|,|;|!|quad|qquad|displaystyle)", "", s)
    s = s.replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "").replace("$", "")
    s = re.sub(r"\\boxed\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\s+", "", s)
    return s.rstrip(".")


# --- web view check (node) -------------------------------------------------------


def check_web_files(paths: list[Path]) -> list[dict]:
    """Run the app's own LaTeX-to-HTML renderer on each file. Returns one
    {file, ok, errors} per input, in order."""
    if not paths:
        return []
    script = SCRIPTS_DIR / "check_web.mjs"
    proc = subprocess.run(
        ["node", str(script), *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if proc.returncode != 0 and not proc.stdout.strip():
        return [{"file": str(p), "ok": False, "errors": [f"check_web failed: {proc.stderr[-800:]}"]} for p in paths]
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [{"file": str(p), "ok": False, "errors": [f"check_web bad output: {proc.stdout[-400:]} {proc.stderr[-400:]}"]} for p in paths]


def check_web_parts(parts: dict[str, str], tmp_dir: Path) -> dict:
    """Web-check several named fragments in one node process. Temp files are
    written under `tmp_dir` (unique per question so parallel runs can't clash)."""
    names = [k for k, v in parts.items() if v and v.strip()]
    if not names:
        return {"ok": True, "errors": []}
    tmp_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for k in names:
        p = tmp_dir / f"_web_{k}.tex"
        write_text(p, parts[k])
        paths.append(p)
    try:
        results = check_web_files(paths)
    finally:
        for p in paths:
            try:
                p.unlink()
            except OSError:
                pass
    errors: list[str] = []
    for k, r in zip(names, results):
        errors += [f"[{k}] {e}" for e in r.get("errors", [])]
    return {"ok": not errors, "errors": errors}


def check_web_text(text: str, tmp_dir: Path, name: str = "content") -> dict:
    return check_web_parts({name: text}, tmp_dir)


def resolve_image(name: str, tex_dir: Path) -> Path | None:
    """Mirror the app's lookup (app/ipc/api.py resolve_images and graphicx's
    \\graphicspath): the bare name, then the name plus a common extension."""
    name = name.strip()
    cands = [tex_dir / name]
    for ext in (".jpg", ".png", ".jpeg", ".pdf", ".gif"):
        cands.append(tex_dir / (name + ext))
    for c in cands:
        if c.is_file():
            return c
    return None
