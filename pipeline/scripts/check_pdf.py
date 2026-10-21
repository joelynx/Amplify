"""PDF check: compile a content fragment inside the app's real template with
the app's engine (XeLaTeX) and fail on anything that would break or degrade
the PDF the app produces.

Usage:
  python check_pdf.py <content.tex> [--pdf out.pdf] [--question-file q.tex]
Prints a JSON result {ok, errors, log_tail}.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_DIR, TEMPLATES_DIR, load_config, read_text, teximages_dir  # noqa: E402

TEMPLATE = TEMPLATES_DIR / "app_template.tex"
_LOG_TAIL = 2000


def _sanitized_env() -> dict[str, str]:
    """Same PATH cleaning the app does (app/tex/pdfgen.py): MiKTeX aborts when a
    PATH entry is a file rather than a directory."""
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
    """Bundled TinyTeX first (same candidates as the app), then PATH."""
    here = REPO_DIR / "app"
    candidates: list[Path] = []
    if sys.platform == "win32":
        candidates += [
            here / "resources" / "tinytex" / "win" / "bin" / "windows" / "xelatex.exe",
            here / "resources" / "tinytex" / "bin" / "windows" / "xelatex.exe",
        ]
    elif sys.platform == "darwin":
        candidates += [
            here / "resources" / "tinytex" / "mac" / "bin" / "x86_64-darwin" / "xelatex",
            here / "resources" / "tinytex" / "mac" / "bin" / "aarch64-darwin" / "xelatex",
        ]
    for c in candidates:
        if c.exists():
            return str(c)
    return shutil.which("xelatex")


def build_document(content: str, *, question_tex: str | None = None, cfg: dict | None = None) -> str:
    cfg = cfg or load_config()
    template = read_text(TEMPLATE)
    img = teximages_dir(cfg).as_posix() + "/"
    body = ""
    if question_tex:
        body += f"\\noindent\\textbf{{Q1.}}~{question_tex}\n\n\\par\\smallskip\n"
    body += f"\\noindent\\textbf{{Q1.}}~{content}\n"
    return template.replace("<<IMAGE_PATH>>", img).replace("<<CONTENT>>", body)


_ERR_PATTERNS = [
    re.compile(r"^! "),
    re.compile(r"Missing character: There is no"),
    re.compile(r"LaTeX Warning: (Reference|Citation) .* undefined"),
    re.compile(r"Unable to load picture or PDF file"),
    re.compile(r"File `.*' not found"),
    re.compile(r"Undefined control sequence"),
]


def scan_log(log: str) -> list[str]:
    errors: list[str] = []
    lines = log.split("\n")
    for i, l in enumerate(lines):
        if any(p.search(l) for p in _ERR_PATTERNS):
            msg = l.strip()
            if l.startswith("! "):
                # attach the offending source line that TeX prints as "l.<n> ..."
                for j in range(i + 1, min(i + 8, len(lines))):
                    if re.match(r"l\.\d+", lines[j]):
                        msg += " | " + lines[j].strip()
                        if j + 1 < len(lines) and lines[j + 1].strip():
                            msg += " " + lines[j + 1].strip()
                        break
            errors.append(msg)
    out: list[str] = []
    for e in errors:
        if e not in out:
            out.append(e)
    return out


def check_pdf(
    content: str,
    *,
    question_tex: str | None = None,
    pdf_out: Path | None = None,
    timeout: int = 180,
    cfg: dict | None = None,
) -> dict:
    cfg = cfg or load_config()
    xelatex = find_xelatex()
    if xelatex is None:
        return {"ok": False, "errors": ["xelatex not found (bundle TinyTeX or install MiKTeX/TeX Live)"], "log_tail": ""}
    if not TEMPLATE.exists():
        return {"ok": False, "errors": [f"template missing: {TEMPLATE} (run make_template.py)"], "log_tail": ""}
    doc = build_document(content, question_tex=question_tex, cfg=cfg)
    with tempfile.TemporaryDirectory(prefix="amp_check_") as td:
        tdp = Path(td)
        stem = "check"
        tex_path = tdp / f"{stem}.tex"
        tex_path.write_text(doc, encoding="utf-8")
        args = [xelatex, "-interaction=nonstopmode", "-halt-on-error"]
        if pdf_out is None:
            args.append("-no-pdf")
        args += ["-output-directory", str(tdp), str(tex_path)]
        try:
            proc = subprocess.run(args, cwd=tdp, capture_output=True, timeout=timeout, env=_sanitized_env())
        except subprocess.TimeoutExpired:
            return {"ok": False, "errors": [f"xelatex timed out after {timeout}s"], "log_tail": ""}
        log_path = tdp / f"{stem}.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        errors = scan_log(log)
        if proc.returncode != 0 and not errors:
            tail = (proc.stdout or b"").decode("utf-8", errors="replace")[-600:]
            err = (proc.stderr or b"").decode("utf-8", errors="replace")[-600:]
            errors.append(f"xelatex exit code {proc.returncode}: {err.strip() or tail.strip()}")
        ok = proc.returncode == 0 and not errors
        if ok and pdf_out is not None:
            produced = tdp / f"{stem}.pdf"
            if produced.exists():
                pdf_out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(produced, pdf_out)
            else:
                ok = False
                errors.append("xelatex reported success but produced no PDF")
        return {"ok": ok, "errors": errors, "log_tail": "" if ok else log[-_LOG_TAIL:]}


def check_parts(parts: dict[str, str], *, cfg: dict | None = None) -> dict:
    """Compile all parts as one document first (one compile on the happy path);
    on failure compile each part separately so the error is attributed."""
    combined = "\n\n".join(v for v in parts.values() if v and v.strip())
    r = check_pdf(combined, cfg=cfg)
    if r["ok"]:
        return {"ok": True, "errors": [], "log_tail": ""}
    errors: list[str] = []
    tail = r["log_tail"]
    for name, text in parts.items():
        if not text or not text.strip():
            continue
        rp = check_pdf(text, cfg=cfg)
        if not rp["ok"]:
            errors += [f"[{name}] {e}" for e in rp["errors"]]
            tail = rp["log_tail"]
    if not errors:
        errors = [f"[combined] {e}" for e in r["errors"]]
    return {"ok": False, "errors": errors, "log_tail": tail}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--pdf")
    ap.add_argument("--question-file")
    a = ap.parse_args()
    content = read_text(Path(a.content))
    q = read_text(Path(a.question_file)) if a.question_file else None
    r = check_pdf(content, question_tex=q, pdf_out=Path(a.pdf) if a.pdf else None)
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
