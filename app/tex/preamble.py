r"""Fixed LaTeX preamble (spec §6.2).

The preamble is identical for every generated PDF — the variable bits live in
`fancyhdr` setup, the body, and any user-customizable header/title content
(which goes through sanitizers in `app/tex/sanitize.py`).

`<image_path>` is resolved at assembly time to `app/data/appdata/teximages/`
with **forward slashes on Windows** because `graphicx`'s `\graphicspath`
requires Unix-style separators on every platform.
"""

from __future__ import annotations

from pathlib import Path

from app.logging_setup import appdata_dir

PREAMBLE_TEMPLATE = r"""\documentclass{article}
\usepackage{amsmath}\allowdisplaybreaks
\usepackage{amsfonts}\usepackage{amssymb}\usepackage{caption}
\usepackage{graphicx}\graphicspath{{<image_path>}}
\usepackage{fancyhdr}\usepackage{geometry}\usepackage{enumitem}
\usepackage{circuitikz}\usepackage{chemfig}\usepackage{pgfplots}
\usepackage{mathtools}\usepackage{stmaryrd}\usepackage{ulem}
% --- Deviations from spec §6.2 -----------------------------------------
% The shipped seed solutions use \begin{proof}, \begin{theorem*}, etc. —
% these come from amsthm. The spec's "fixed" preamble omits it; we add it
% here so the bundled content actually compiles. starred theorem variants
% need explicit \newtheorem*-style declarations on top of amsthm.
\usepackage{amsthm}
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem*{theorem*}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem*{lemma*}{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem*{proposition*}{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem*{corollary*}{Corollary}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem*{definition*}{Definition}
\newtheorem{example}[theorem]{Example}
\newtheorem*{example*}{Example}
\theoremstyle{remark}
\newtheorem{remark}[theorem]{Remark}
\newtheorem*{remark*}{Remark}
\newtheorem{note}[theorem]{Note}
\newtheorem*{note*}{Note}
\newtheorem{claim}[theorem]{Claim}
\newtheorem*{claim*}{Claim}
"""


def image_dir() -> Path:
    """`app/data/appdata/teximages/`. Created on demand."""
    d = appdata_dir() / "teximages"
    d.mkdir(parents=True, exist_ok=True)
    return d


def preamble(image_path: Path | None = None) -> str:
    """Return the preamble with `<image_path>` substituted.

    LaTeX requires forward slashes even on Windows for `\\graphicspath`; we
    convert as_posix() unconditionally.
    """
    p = image_path or image_dir()
    return PREAMBLE_TEMPLATE.replace("<image_path>", str(p.as_posix()) + "/")
