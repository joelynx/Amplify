"""TeX assembly + XeLaTeX runner (spec §6.1).

`assemble(questions, output_settings)` returns the full `.tex` string. The
runner compiles in a tempdir, copies the resulting PDF to the user's save dir,
and on compile failure writes the `.tex` fallback to the same directory and
returns a tail of the XeLaTeX log for the modal to display.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.models import Question
from app.persistence.repositories import configs as configs_repo
from app.tex.header_vars import HeaderContext, substitute
from app.tex.preamble import image_dir, preamble
from app.tex.sanitize import sanitize_latex_basic, sanitize_latex_extended
from app.tex.solutions import assemble_body

log = logging.getLogger("amplify.tex.pdfgen")

_LOG_TAIL_CHARS = 4000


@dataclass(slots=True)
class CompileResult:
    success: bool
    pset_id: str  # filename stem (PDF or .tex)
    path: Path | None  # PDF path on success, None otherwise
    fallback: Path | None  # .tex path on failure, None otherwise
    errors: str  # tail of XeLaTeX log on failure


def _sanitized_env() -> dict[str, str]:
    """Drop PATH entries that aren't real directories.

    MiKTeX walks PATH for fonts and chokes hard if it finds a file (or a missing
    path) in there — observed on Windows where the Store-alias `python.exe`
    entry is registered as a "directory" by some installers. Strip those before
    invoking xelatex so the compile doesn't fail on a system-config glitch.
    """
    env = os.environ.copy()
    sep = os.pathsep
    cleaned: list[str] = []
    seen: set[str] = set()
    for p in env.get("PATH", "").split(sep):
        if not p or p in seen:
            continue
        seen.add(p)
        try:
            if Path(p).is_dir():
                cleaned.append(p)
        except OSError:
            pass
    env["PATH"] = sep.join(cleaned)
    return env


def find_xelatex() -> str | None:
    """Try the bundled TinyTeX path first (per spec §2.1), then PATH."""
    here = Path(__file__).resolve().parent.parent  # app/
    candidates: list[Path] = []
    if sys.platform == "win32":
        candidates.extend(
            [
                here / "resources" / "tinytex" / "win" / "bin" / "windows" / "xelatex.exe",
                here / "resources" / "tinytex" / "bin" / "windows" / "xelatex.exe",
            ]
        )
    elif sys.platform == "darwin":
        candidates.extend(
            [
                here / "resources" / "tinytex" / "mac" / "bin" / "x86_64-darwin" / "xelatex",
                here / "resources" / "tinytex" / "mac" / "bin" / "aarch64-darwin" / "xelatex",
            ]
        )
    for c in candidates:
        if c.exists():
            return str(c)
    return shutil.which("xelatex")


def _header_ctx(
    subject: str | None,
    questions: list[Question],
    output_settings: dict[str, Any],
    pset_id: str,
) -> HeaderContext:
    topics = sorted({q.topic for q in questions})
    types = sorted({q.type for q in questions if q.type})
    sources = sorted({q.source for q in questions if q.source}) if output_settings.get("include_sources", True) else []
    return HeaderContext(
        subject=subject or "",
        topic_list=topics,
        n_questions=len(questions),
        source_list=sources,
        type_list=types,
        pset_id=pset_id,
        now=datetime.now(),
    )


def _build_pset_id(subject: str | None, now: datetime) -> str:
    base = (subject or "PSet").replace(" ", "_")
    return f"{base}_{now.strftime('%Y%m%d_%H%M%S')}"


def assemble(
    conn,
    questions: list[Question],
    output_settings: dict[str, Any],
    *,
    subject: str | None = None,
    pset_id: str | None = None,
) -> str:
    """Build the full `.tex` source.

    `output_settings` keys (matching the Generate form):
      - `solutions`: one of the five modes ("none"/"appendix"/"interleaved"/
        "outline_appendix"/"outline_interleaved")
      - `include_sources`: bool
    """
    pid = pset_id or _build_pset_id(subject, datetime.now())

    # Header content from configs (already user-typed; pass through the
    # appropriate sanitizer + token substitution).
    left_raw = configs_repo.get(conn, "PDF_LEFT_HEADER", "") or ""
    right_raw = configs_repo.get(conn, "PDF_RIGHT_HEADER", "") or ""
    title_raw = configs_repo.get(conn, "PDF_TITLE_LINE", "") or ""
    instructions_raw = configs_repo.get(conn, "PDF_INSTRUCTIONS", "") or ""

    ctx = _header_ctx(subject, questions, output_settings, pid)

    left = substitute(sanitize_latex_basic(left_raw), ctx) if left_raw else ""
    right = substitute(sanitize_latex_basic(right_raw), ctx) if right_raw else ""
    title = substitute(sanitize_latex_extended(title_raw), ctx) if title_raw else ""
    instructions = substitute(sanitize_latex_extended(instructions_raw), ctx) if instructions_raw else ""

    pre = preamble(image_dir())
    fancy = "\n".join(
        [
            r"\pagestyle{fancy}",
            r"\fancyhf{}",
            rf"\fancyhead[L]{{{left}}}",
            rf"\fancyhead[R]{{{right}}}",
            r"\fancyfoot[C]{\thepage}",
            r"\renewcommand{\headrulewidth}{0.4pt}",
            r"\geometry{margin=1in}",
        ]
    )

    body = assemble_body(
        questions,
        output_settings.get("solutions", "none"),
        bool(output_settings.get("include_sources", True)),
    )

    head_block = ""
    if title:
        head_block += f"\\begin{{center}}\\Large\\textbf{{{title}}}\\end{{center}}\n"
    if instructions:
        head_block += f"\\par {instructions}\\par\\bigskip\n"

    return f"""{pre}{fancy}
\\begin{{document}}
{head_block}
{body}
\\end{{document}}
"""


def _write_fallback_tex(tex: str, save_dir: Path, pset_id: str) -> Path:
    save_dir.mkdir(parents=True, exist_ok=True)
    path = save_dir / f"{pset_id}.tex"
    path.write_text(tex, encoding="utf-8")
    return path


def compile_to_pdf(
    tex: str,
    save_dir: Path,
    pset_id: str,
    *,
    timeout_s: int = 120,
) -> CompileResult:
    """Run XeLaTeX in a tmpdir. On success copy the PDF to `save_dir`.
    On failure write the `.tex` fallback there and return the log tail."""
    xelatex = find_xelatex()
    if xelatex is None:
        path = _write_fallback_tex(tex, save_dir, pset_id)
        msg = (
            "xelatex not found. Bundle TinyTeX into app/resources/tinytex/ or "
            "install a system TeX distribution (MiKTeX / TeX Live)."
        )
        log.error(msg)
        return CompileResult(success=False, pset_id=pset_id, path=None, fallback=path, errors=msg)

    save_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="amplify_xelatex_") as td:
        tdp = Path(td)
        tex_path = tdp / f"{pset_id}.tex"
        tex_path.write_text(tex, encoding="utf-8")

        try:
            proc = subprocess.run(
                [
                    xelatex,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory",
                    str(tdp),
                    str(tex_path),
                ],
                cwd=tdp,
                capture_output=True,
                timeout=timeout_s,
                check=False,
                env=_sanitized_env(),
            )
        except subprocess.TimeoutExpired:
            fallback = _write_fallback_tex(tex, save_dir, pset_id)
            return CompileResult(
                success=False,
                pset_id=pset_id,
                path=None,
                fallback=fallback,
                errors=f"xelatex timed out after {timeout_s}s",
            )

        pdf_path = tdp / f"{pset_id}.pdf"
        log_path = tdp / f"{pset_id}.log"
        if proc.returncode == 0 and pdf_path.exists():
            dest = save_dir / pdf_path.name
            shutil.copyfile(pdf_path, dest)
            log.info("xelatex success: %s -> %s", pset_id, dest)
            return CompileResult(success=True, pset_id=pset_id, path=dest, fallback=None, errors="")

        # Failure path — collect log tail, write fallback .tex
        if log_path.exists():
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-_LOG_TAIL_CHARS:]
        else:
            tail = (proc.stdout or b"").decode("utf-8", errors="replace")[-_LOG_TAIL_CHARS:]
        fallback = _write_fallback_tex(tex, save_dir, pset_id)
        log.warning("xelatex failed (returncode=%d); .tex fallback at %s", proc.returncode, fallback)
        return CompileResult(success=False, pset_id=pset_id, path=None, fallback=fallback, errors=tail)
