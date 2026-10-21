"""Mechanical repairs for stored solutions (questions.solution) that break the
app's PDF compile, each verified by compiling the repaired solution.

Owner request (2026-10-21): "Perform all the mechanical fixes and confirm
compilation." Scope: rows of pipeline/reports/old_solutions_breaks.csv whose
fault is in the solution. The question text (latexcode) is never modified: its
hash and embeddings depend on it.

Every fixer is a plain text transformation. A repaired solution is kept only if
XeLaTeX then compiles it (same template as the app's PDF generation). First the
global fixers run in order (see GLOBAL_FIXERS), then up to MAX_ROUNDS log-guided
rounds: the XeLaTeX log says which source line and which position the error is
at, and one targeted fix is applied there.

Usage (repo root):
  python pipeline/scripts/fix_old_solutions.py run   [--workers 4] [--limit N] [--ids 1,2] [--fresh]
      repair + verify; no database writes; resumable (results in the fixes JSON)
  python pipeline/scripts/fix_old_solutions.py apply
      write every verified repair to questions.solution (originals recorded in
      pipeline.db table solution_fixes)
  python pipeline/scripts/fix_old_solutions.py revert
      restore the originals recorded by apply
Outputs: pipeline/reports/old_solutions_fixes.json (original, fixed, fixers, ok, error per question)
         pipeline/reports/old_solutions_fixes.csv  (question_id, ok, fixers, rounds, error)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pdf import build_document, check_pdf  # noqa: E402
from common import app_conn, load_config, now_iso, pipe_conn  # noqa: E402

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
BREAKS_CSV = REPORTS_DIR / "old_solutions_breaks.csv"
FIXES_JSON = REPORTS_DIR / "old_solutions_fixes.json"
FIXES_CSV = REPORTS_DIR / "old_solutions_fixes.csv"
MAX_ROUNDS = 8

MATH_ENVS = {"align", "align*", "gather", "gather*", "equation", "equation*", "multline", "multline*",
             "eqnarray", "eqnarray*", "displaymath", "math", "flalign", "flalign*", "alignat", "alignat*"}
INNER_MATH_ENVS = {"aligned", "gathered", "cases", "split", "alignedat", "dcases", "rcases"}
ALIGN_ENVS = MATH_ENVS | INNER_MATH_ENVS | {"tabular", "tabular*", "array", "matrix", "pmatrix", "bmatrix", "vmatrix",
                                            "Vmatrix", "smallmatrix", "tabularx", "longtable"}
LIST_ENVS = {"itemize", "enumerate", "description"}
VERTICAL_ENVS = LIST_ENVS | {"center", "quote", "quotation", "table", "figure", "flushleft", "flushright"}
LENGTH_RE = re.compile(r"^\s*-?\d*\.?\d+\s*(pt|em|ex|mm|cm|in|bp|pc|dd|cc|sp|\\baselineskip|\\textwidth|\\linewidth)")
# commands that only work in math mode (text-mode ones such as \text, \ldots, \quad, \underline are deliberately absent)
MATH_CMDS = ("frac|dfrac|tfrac|sqrt|alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|rho|"
             "sigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Phi|Psi|Omega|times|cdot|pm|mp|le|ge|leq|geq|"
             "neq|ne|approx|equiv|sim|int|iint|oint|sum|prod|infty|partial|nabla|to|rightarrow|Rightarrow|leftarrow|Leftarrow|leftrightarrow|"
             "Leftrightarrow|mapsto|left|right|tag|binom|vec|hat|bar|tilde|overline|ln|log|sin|cos|tan|cot|sec|csc|sinh|cosh|tanh|exp|lim|max|"
             "min|sup|inf|det|gcd|mathbb|mathcal|mathfrak|boxed|cdots|langle|rangle|lfloor|rfloor|lceil|rceil|mid|forall|exists|in|notin|"
             "subset|subseteq|supset|supseteq|cup|cap|emptyset|varnothing|setminus|propto|angle|circ|prime|hbar|ell|Re|Im|operatorname|"
             "therefore|because|implies|iff|land|lor|lnot|neg|div|ast|star|bullet|oplus|otimes|perp|parallel|triangle|square|degree|"
             "underbrace|overbrace|stackrel|overset|underset|limits|nolimits|dot|ddot|choose|atop|over|textstyle|displaystyle")
MATH_CMD_RE = re.compile(r"\\(" + MATH_CMDS + r")(?![A-Za-z])")
SYMBOL_CMD_RE = re.compile(r"(?<![\\^_{])\\(cdot|times|circ|pm|mp|to|rightarrow|leftarrow|Rightarrow|Leftarrow|le|ge|leq|geq|neq|ne|approx|infty|"
                           r"alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|lambda|mu|nu|xi|pi|rho|sigma|tau|phi|varphi|chi|psi|"
                           r"omega|Delta|Gamma|Theta|Lambda|Sigma|Phi|Psi|Omega|partial|nabla|propto|equiv|sim|angle|perp|parallel)(?![A-Za-z])")
URLISH = re.compile(r"https?:|www\.|\.(com|org|php|html|htm|net|edu|gov)(?![A-Za-z])")
MATHISH_TOKEN = re.compile(r"^[\\A-Za-z0-9(){}\[\]^_+\-=.,/*'|<>:;!~ ]+$")
NOT_MATH_CMD = re.compile(r"\\(includegraphics|label|ref|eqref|cite|url|href|input|include|textbf|textit|emph|item|begin|end|section|"
                          r"subsection|caption|hspace|vspace|footnote|texttt|underline)(?![A-Za-z])")
CONNECTOR = re.compile(r"^(?:[-+=*/<>()\[\]|.,]+|\d+(?:\.\d+)?|\\(?:cdot|times|pm|mp|le|ge|leq|geq|neq|ne|to|approx|equiv|sim|div|quad|,|;|!))$")
TEXT_CMD_PREFIXES = ("\\textbf", "\\textit", "\\emph", "\\item", "\\begin", "\\end", "\\section", "\\subsection", "\\includegraphics",
                     "\\text{", "\\texttt", "\\underline", "\\label", "\\ref", "\\caption", "\\hspace", "\\vspace", "\\noindent", "\\par",
                     "\\newline", "\\centering", "\\hline", "\\url", "\\href", "\\footnote", "\\cite", "\\paragraph")
# \n + one of these is a real command, not a literal newline (checked case-insensitively, so \nVdash etc. are covered)
N_CMDS_CI = {"nabla", "natural", "ncong", "ne", "nearrow", "neg", "neq", "newcommand", "newenvironment", "newline", "newpage",
             "newtheorem", "nexists", "ngeq", "ngeqq", "ngeqslant", "ngtr", "ni", "nleftarrow", "nleftrightarrow", "nleq", "nleqq",
             "nleqslant", "nless", "nmid", "nobreak", "nocite", "noindent", "nolimits", "nonumber", "normalfont", "normalsize", "not",
             "notag", "notin", "nparallel", "nprec", "npreceq", "nrightarrow", "nshortmid", "nshortparallel", "nsim", "nsubseteq",
             "nsubseteqq", "nsucc", "nsucceq", "nsupseteq", "nsupseteqq", "ntriangleleft", "ntrianglelefteq", "ntriangleright",
             "ntrianglerighteq", "nu", "null", "nvdash", "nwarrow", "nolinebreak", "nopagebreak", "newcounter", "newlength",
             "newsavebox", "newif", "numberwithin", "name", "nocorr", "noalign", "nointerlineskip", "nobreakspace", "nonfrenchspacing",
             "needspace", "newfont", "nofiles", "nicefrac", "norm", "numberthis", "number", "noexpand", "nulldelimiterspace",
             "newblock", "nouppercase", "nextline", "ngets"}
R_CMDS_UPPER = {"rVert"}
KNOWN_CMDS = set(MATH_CMDS.split("|")) | {
    "begin", "end", "item", "textbf", "textit", "emph", "text", "textrm", "texttt", "underline", "hline", "vspace", "hspace", "section",
    "subsection", "subsubsection", "paragraph", "noindent", "par", "newline", "includegraphics", "label", "ref", "eqref", "caption",
    "centering", "quad", "qquad", "ldots", "dots", "mathrm", "mathbf", "mathit", "mathsf", "mathtt", "displaystyle", "textstyle", "small",
    "large", "Large", "footnotesize", "normalsize", "bf", "it", "rm", "em", "cline", "multicolumn", "multirow", "newpage", "clearpage",
    "smallskip", "medskip", "bigskip", "textsuperscript", "textsubscript", "footnote", "cite", "url", "href", "boldsymbol", "mathbb",
    "cfrac", "sqrt", "not", "dot", "ddot", "mbox", "hbox", "phantom", "vphantom", "hphantom", "rule", "textwidth", "linewidth", "tabular",
    "array", "ne", "neq", "ge", "le", "dfrac", "tfrac", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr", "biggl", "biggr",
    "lvert", "rvert", "lVert", "rVert", "vert", "Vert", "ldotp", "cdotp", "colon", "frac", "arccos", "arcsin", "arctan", "deg", "dim",
    "hom", "ker", "Pr", "arg", "coth", "liminf", "limsup", "varliminf", "varlimsup", "pmod", "bmod", "mod", "textcolor", "color", "fbox",
    "framebox", "parbox", "makebox", "raisebox", "scriptsize", "tiny", "huge", "Huge", "LARGE", "mathop", "mathrel", "mathbin", "textnormal",
    "ensuremath", "hfill", "vfill", "hrulefill", "dotfill", "indent", "setlength", "parindent", "parskip", "baselineskip", "tag", "notag",
    "nonumber", "intertext", "shortintertext", "substack", "xrightarrow", "xleftarrow", "overrightarrow", "overleftarrow", "widehat",
    "widetilde", "breve", "check", "acute", "grave", "mathring", "imath", "jmath", "aleph", "wp", "mho", "surd", "top", "bot", "models",
    "vdash", "dashv", "succ", "prec", "preceq", "succeq", "ll", "gg", "asymp", "bowtie", "doteq", "cong", "simeq", "wedge", "vee",
    "sqcup", "sqcap", "amalg", "dagger", "ddagger", "uplus", "wr", "odot", "ominus", "oslash", "bigcirc", "bigcup", "bigcap", "bigvee",
    "bigwedge", "bigoplus", "bigotimes", "coprod", "varphi", "vartheta", "varpi", "varrho", "varsigma", "varkappa", "digamma", "gets",
    "longrightarrow", "longleftarrow", "Longrightarrow", "Longleftarrow", "longleftrightarrow", "Longleftrightarrow", "uparrow",
    "downarrow", "Uparrow", "Downarrow", "updownarrow", "hookrightarrow", "hookleftarrow", "nearrow", "searrow", "swarrow", "nwarrow",
    "leadsto", "ddots", "vdots", "iiint", "idotsint", "smash", "llap", "rlap", "strut", "mathstrut", "kern", "mkern", "mskip", "hskip",
    "vskip", "enspace", "thinspace", "negthinspace", "medmuskip", "thickmuskip", "mathclose", "mathopen", "mathpunct", "mathord",
    "mathinner", "mathchoice", "mathversion", "unboldmath", "boldmath", "pounds", "copyright", "dag", "ddag", "S", "P", "oe", "OE", "ae",
    "AE", "aa", "AA", "o", "O", "l", "L", "ss", "i", "j"}


# --- math-mode spans ---------------------------------------------------------------


def math_spans(text: str) -> list[tuple[int, int]]:
    """Character spans inside math mode ($..$, $$..$$, \\(..\\), \\[..\\] and the
    display environments), as [start, end) with the delimiters included."""
    spans: list[tuple[int, int]] = []
    i, n = 0, len(text)
    start: int | None = None
    closer: str | None = None
    while i < n:
        ch = text[i]
        if ch == "\\":
            nxt = text[i + 1] if i + 1 < n else ""
            if nxt in "\\$%&_#{}":
                i += 2
                continue
            two = text[i:i + 2]
            if start is None:
                if two in ("\\(", "\\["):
                    start, closer = i, ("\\)" if two == "\\(" else "\\]")
                    i += 2
                    continue
                m = re.match(r"\\begin\{([A-Za-z*]+)\}", text[i:])
                if m and m.group(1) in MATH_ENVS:
                    start, closer = i, "\\end{" + m.group(1) + "}"
                    i += m.end()
                    continue
            else:
                if closer in ("\\)", "\\]") and two == closer:
                    spans.append((start, i + 2))
                    start, closer = None, None
                    i += 2
                    continue
                if closer and closer.startswith("\\end") and text.startswith(closer, i):
                    end = i + len(closer)
                    spans.append((start, end))
                    start, closer = None, None
                    i = end
                    continue
            i += 1 if nxt.isalpha() else 2
            continue
        if ch == "%":
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if ch == "$":
            if start is None:
                if text.startswith("$$", i):
                    start, closer = i, "$$"
                    i += 2
                else:
                    start, closer = i, "$"
                    i += 1
                continue
            if closer == "$$" and text.startswith("$$", i):
                spans.append((start, i + 2))
                start, closer = None, None
                i += 2
                continue
            if closer == "$":
                spans.append((start, i + 1))
                start, closer = None, None
                i += 1
                continue
        i += 1
    if start is not None:
        spans.append((start, n))
    return spans


def in_math(spans: list[tuple[int, int]], pos: int) -> bool:
    return any(a <= pos < b for a, b in spans)


def env_depth_at(text: str, pos: int, envs: set[str]) -> int:
    depth = 0
    for m in re.finditer(r"\\(begin|end)\{([A-Za-z*]+)\}", text[:pos]):
        if m.group(2) in envs:
            depth += 1 if m.group(1) == "begin" else -1
    return max(depth, 0)


def _balanced_arg(t: str, i: int) -> int | None:
    """t[i] is '{'; index just past its matching '}' (None if unbalanced)."""
    depth, j, n = 0, i, len(t)
    while j < n:
        c = t[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return None


def _escape_text(s: str) -> str:
    s = re.sub(r"(?<!\\)([_#%&])", r"\\\1", s)
    return s.replace("~", "\\textasciitilde{}")


# --- tokens and math wrapping ------------------------------------------------------


def _tokens_with_spans(line: str) -> list[tuple[int, int]]:
    """Whitespace-delimited tokens; whitespace inside braces or brackets does not split."""
    out, i, n = [], 0, len(line)
    while i < n:
        if line[i].isspace():
            i += 1
            continue
        j, depth = i, 0
        while j < n and (depth > 0 or not line[j].isspace()):
            if line[j] == "\\" and j + 1 < n:
                if line[j + 1] == "\\" and depth == 0:  # a row/line break ends the token
                    if j == i:
                        j += 2
                    break
                j += 2
                continue
            if line[j] in "{[":
                depth += 1
            elif line[j] in "}]":
                depth = max(depth - 1, 0)
            j += 1
        out.append((i, min(j, n)))
        i = j
    return out


def _core(tok: str) -> tuple[str, int, int]:
    """Strip harmless leading '(' and trailing punctuation: (core, lead, trail)."""
    lead = len(tok) - len(tok.lstrip("("))
    core = tok[lead:]
    trail = len(core) - len(core.rstrip(".,;:!?"))
    core = core[:len(core) - trail] if trail else core
    # a closing paren that has no opening one inside the token belongs to the prose
    while core.endswith(")") and core.count("(") < core.count(")") and not re.search(r"\\(right|[bB]igg?)\)$", core):
        core = core[:-1]
        trail += 1
    return core, lead, trail


def _token_is_math(tok: str) -> bool:
    core, _, _ = _core(tok.strip())
    if not core or len(core) > 80 or URLISH.search(core) or not MATHISH_TOKEN.match(core) or NOT_MATH_CMD.search(core):
        return False
    if "^" in core or MATH_CMD_RE.search(core) or _text_token_is_math(core):
        return True
    return bool(re.search(r"(?<=[A-Za-z0-9})])_(\{|[A-Za-z0-9](?![A-Za-z]))", core))


def _words_outside_braces(s: str) -> list[str]:
    s = re.sub(r"\\[A-Za-z]+\*?", " ", s)
    for _ in range(3):
        s = re.sub(r"\{[^{}]*\}", " ", s)
    return re.findall(r"[A-Za-z]{4,}", s)


def _text_token_is_math(tok: str) -> bool:
    """\\text{Ca(OH)}_ or \\textrm{m}^2: a text command carrying a script is math."""
    return tok.startswith(("\\text{", "\\textrm{", "\\mathrm{")) and bool(re.search(r"\}\s*[_^]", tok))


def _wrap_math_in_line(line: str, open_: str = "\\(", close: str = "\\)") -> str:
    """Line outside math mode: wrap a bare equation whole, else wrap the
    math-looking token runs in \\( \\). Existing math on the line is left alone."""
    s = line.strip()
    if not s or s.startswith("%"):
        return line
    spans = math_spans(line)
    item = re.match(r"\s*\\item(\[[^\]]*\])?\s*", line)
    body = line[item.end():] if item else line
    bs = body.strip()
    if (bs and not spans and ("=" in bs or "\\tag" in bs) and not _words_outside_braces(bs)
            and not bs.startswith(TEXT_CMD_PREFIXES) and "\\begin" not in bs and "\\end" not in bs
            and (re.search(r"[\^_]", bs) or MATH_CMD_RE.search(bs))):
        core = re.sub(r"\\\\\s*$", "", bs).strip()
        d_open, d_close = ("\\[ ", " \\]") if open_ == "\\(" else ("$", "$")
        return (line[:item.end()] if item else "") + d_open + core + d_close
    toks = _tokens_with_spans(line)
    kinds = []
    for a, b in toks:
        tok = line[a:b]
        if (any(a < e and b > s0 for s0, e in spans) or (tok.startswith(TEXT_CMD_PREFIXES) and not _text_token_is_math(tok))
                or "$" in tok or re.search(r"\\[()\[\]]", tok)):
            kinds.append("text")
        elif _token_is_math(tok):
            kinds.append("math")
        elif CONNECTOR.match(_core(tok)[0] or "x"):
            kinds.append("conn")
        else:
            kinds.append("text")
    out, last, i = [], 0, 0
    while i < len(toks):
        if kinds[i] != "math":
            i += 1
            continue
        j = i
        while j + 1 < len(toks) and kinds[j + 1] in ("math", "conn"):
            j += 1
        while j > i and kinds[j] == "conn" and not re.match(r"^\d", line[toks[j][0]:toks[j][1]]):
            j -= 1
        run = line[toks[i][0]:toks[j][1]]
        if "\\left" in run and "\\right" not in run:
            k = j
            while k + 1 < len(toks) and "\\right" not in line[toks[k][0]:toks[k][1]]:
                k += 1
            if "\\right" in line[toks[k][0]:toks[k][1]]:
                j = k
        a = toks[i][0]
        b = toks[j][1]
        _, _, trail = _core(line[toks[j][0]:b])
        lead_first = _core(line[a:toks[i][1]])[1]
        core_start = a + lead_first
        core_end = b - trail
        if core_end <= core_start:
            i = j + 1
            continue
        out.append(line[last:core_start] + open_ + line[core_start:core_end] + close)
        last = core_end
        i = j + 1
    out.append(line[last:])
    return "".join(out)


# --- global fixers (text -> text) --------------------------------------------------


def fx_normalize(t: str) -> str:
    """'\\begin {itemize}' -> '\\begin{itemize}' so every later scan sees it; CRLF -> LF."""
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    # JSON escapes that were decoded into control characters: "\frac" -> form feed + "rac"
    t = t.replace("\x0c", "\\f").replace("\x08", "\\b").replace("\x07", "\\a").replace("\x0b", "\\v")
    t = re.sub(r"(?<=[0-9])%", r"\\%", t)  # "80% of" is a percentage, not a comment that swallows the line
    t = re.sub(r"(\\\\)\\ (\s*\\hline)", r"\1\2", t)  # a control space between a row end and \hline
    t = re.sub(r"\$\s*\\LaTeX\s*\$", r"\\LaTeX{}", t)
    t = re.sub(r"\\(begin|end)\s*\{\s*([A-Za-z]+)\s*(\*?)\s*\}", r"\\\1{\2\3}", t)
    t = re.sub(r"\\rupee(?![A-Za-z])", "Rs.~", t)
    t = re.sub(r"\\textoverline\s*\{", r"\\={", t)
    t = re.sub(r"\\(endhead|endfirsthead|endfoot|endlastfoot)(?![A-Za-z])", "", t)
    # double scripts: U^{236}^* -> U^{236*}, N_A_ a -> N_{Aa}
    t = re.sub(r"\^\{([^{}]*)\}\s*\^\s*(\{[^{}]*\}|[^\s{}\\])", r"^{\1\2}", t)
    t = re.sub(r"_\{([^{}]*)\}\s*_\s*(\{[^{}]*\}|[^\s{}\\])", r"_{\1\2}", t)
    t = re.sub(r"(?<=[A-Za-z0-9])_([A-Za-z0-9])_\s*([A-Za-z0-9])", r"_{\1\2}", t)
    return t


def fx_markdown_escapes(t: str) -> str:
    """Markdown-escaped LaTeX: '\\$P\\_{water} = \\dot{m} g H$' -> '$P_{water} = \\dot{m} g H$'."""
    # (?<!\\) keeps a row break followed by math, "\\$x$", out of this
    if not re.search(r"(?<!\\)\\\$", t) or not re.search(r"(?<!\\)\\_\{|(?<!\\)\\_[A-Za-z0-9]|(?<!\\)\\\$[A-Za-z]?[\\_^{]", t):
        return t
    t = re.sub(r"(?<!\\)\\\$", "$", t)
    spans = math_spans(t)
    out, last = [], 0
    for m in re.finditer(r"\\([_*])", t):
        if in_math(spans, m.start()):
            out.append(t[last:m.start()] + m.group(1))
            last = m.end()
    out.append(t[last:])
    return "".join(out)


def fx_hline_rows(t: str) -> str:
    """\\hline on its own line after a table row that lacks its \\\\."""
    def rep(m: re.Match) -> str:
        lines = m.group(0).split("\n")
        out: list[str] = []
        for ln in lines:
            if re.match(r"\s*\\hline", ln) and out:
                k = next((i for i in range(len(out) - 1, -1, -1) if out[i].strip()), None)
                if k is not None and not re.search(r"(\\\\(\[[^\]]*\])?|\\hline|\\cline\{[^}]*\}|\\begin\{[^}]*\}(\{[^}]*\})?)\s*$", out[k]):
                    out[k] = out[k].rstrip() + " \\\\"
            out.append(ln)
        return "\n".join(out)

    return re.sub(r"\\begin\{(tabular|array|longtable)\}.*?\\end\{\1\}", rep, t, flags=re.S)


def fx_undouble(t: str) -> str:
    """JSON-era doubled backslashes (\\\\frac, \\\\[ ... \\\\]) -> single. Only when
    the text shows the signature, so a real row separator is never touched."""
    if not re.search(r"(?<!\\)\\\\(begin|end|frac|left|right|sqrt|text|times|cdot|mathrm|mathbf|item|textbf|dfrac|int|sum)(?![A-Za-z])"
                     r"|(?<!\\)\\\\\]|(?<!\\)\\\\\[ ", t):
        return t
    # only a known command name is undoubled: "\\The overall" is a row break followed by prose
    t = re.sub(r"(?<!\\)\\\\([A-Za-z]+)", lambda m: "\\" + m.group(1) if m.group(1) in KNOWN_CMDS else m.group(0), t)

    def brk(m: re.Match) -> str:
        return m.group(0) if LENGTH_RE.match(t[m.end():m.end() + 24]) else "\\["

    t = re.sub(r"(?<!\\)\\\\\[", brk, t)
    t = re.sub(r"(?<!\\)\\\\\]", r"\\]", t)
    t = re.sub(r"(?<!\\)\\\\\(", r"\\(", t)
    t = re.sub(r"(?<!\\)\\\\\)", r"\\)", t)
    return t


def fx_literal_escapes(t: str) -> str:
    """Literal "\\n", "\\t", "\\r" left over from a JSON string."""

    def rep(m: re.Match) -> str:
        bs, letter, word = m.group(1), m.group(2), m.group(3)
        if len(bs) % 2 == 0:  # an even run of backslashes is escaped backslashes, not an escape
            return m.group(0)
        keep = bs[:-1]
        if letter == "n":
            if word and ("n" + word).lower() in N_CMDS_CI:
                return m.group(0)
            return keep + "\n" + word
        if word and not word[0].isupper():  # \theta, \rho, ...: real commands
            return m.group(0)
        if letter == "t":
            return keep + " " + word
        if ("r" + word) in R_CMDS_UPPER:
            return m.group(0)
        return keep + word

    return re.sub(r"(\\+)([ntr])([A-Za-z]*)", rep, t)


def fx_typos(t: str) -> str:
    t = re.sub(r"\\(begin|end)'([A-Za-z*]+)\}", r"\\\1{\2}", t)
    t = re.sub(r"\\(begin|end)([a-z]+\*?)\}", r"\\\1{\2}", t)
    t = re.sub(r"\\(textbf|textit|emph|underline)(?=[A-Z][a-z])", r"\\\1{", t)
    # a line break or control space between \begin{itemize} and its first \item (after undouble, so \\item is \item)
    t = re.sub(r"(\\begin\{(?:itemize|enumerate|description)\}(?:\[[^\]]*\])?)\s*(?:\\\\|\\ )+\s*(?=\\item)", r"\1 ", t)
    return t


def fx_href(t: str) -> str:
    out, i = [], 0
    pat = re.compile(r"\\(href|url)\s*\{")
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        out.append(t[i:m.start()])
        k = _balanced_arg(t, m.end() - 1)
        if k is None:
            out.append(t[m.start():m.end()])
            i = m.end()
            continue
        url = t[m.end():k - 1]
        if m.group(1) == "url":
            out.append("\\texttt{" + _escape_text(url) + "}")
            i = k
            continue
        j = k
        while j < len(t) and t[j] in " \t":
            j += 1
        if j < len(t) and t[j] == "{":
            k2 = _balanced_arg(t, j)
            if k2 is not None:
                label = t[j + 1:k2 - 1]
                out.append(label + " (\\texttt{" + _escape_text(url) + "})")
                i = k2
                continue
        out.append("\\texttt{" + _escape_text(url) + "}")
        i = k
    return "".join(out)


def fx_multirow(t: str) -> str:
    out, i = [], 0
    pat = re.compile(r"\\multirow\s*(\[[^\]]*\])?\s*")
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        out.append(t[i:m.start()])
        j = m.end()
        args = []
        for _ in range(3):
            k0 = j
            while k0 < len(t) and t[k0] in " \t":
                k0 += 1
            if k0 < len(t) and t[k0] == "{":
                k = _balanced_arg(t, k0)
                if k is None:
                    break
                args.append(t[k0 + 1:k - 1])
                j = k
            else:
                break
        if len(args) == 3:
            out.append(args[2])
            i = j
        else:
            out.append(t[m.start():m.end()])
            i = m.end()
    return "".join(out)


def fx_unknown_cmds(t: str) -> str:
    """Commands and environments from packages the app preamble does not load."""
    t = t.replace("\\begin{displayquote}", "\\begin{quote}").replace("\\end{displayquote}", "\\end{quote}")
    t = re.sub(r"\\tightlist(?![A-Za-z])", "", t)
    t = re.sub(r"\\wideparen\s*\{", r"\\overset{\\frown}{", t)
    t = re.sub(r"\\mathscr(?![A-Za-z])", r"\\mathcal", t)
    t = re.sub(r"\\textdegree(?![A-Za-z])", r"\\(^\\circ\\)", t)
    t = re.sub(r"\\begin\{lstlisting\}\s*(\[[^\]]*\])?", r"\\begin{verbatim}", t)
    t = t.replace("\\end{lstlisting}", "\\end{verbatim}")
    t = re.sub(r"\\passthrough\s*\{\\lstinline(.)(.*?)\1\}", lambda m: "\\texttt{" + _escape_text(m.group(2)) + "}", t)
    t = re.sub(r"\\lstinline(.)(.*?)\1", lambda m: "\\texttt{" + _escape_text(m.group(2)) + "}", t)
    t = re.sub(r"\\Varangle(?![A-Za-z])", r"\\angle", t)
    t = re.sub(r"\\item\s*\[\\bullet\]", r"\\item", t)
    t = fx_href(t)
    t = fx_multirow(t)
    return t


UPPER_CMDS = {"Delta", "Gamma", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega", "Rightarrow", "Leftarrow",
              "Leftrightarrow", "Longrightarrow", "Longleftarrow", "Longleftrightarrow", "Uparrow", "Downarrow", "Updownarrow", "Big",
              "Bigg", "Bigl", "Bigr", "Biggl", "Biggr", "Bigm", "Biggm", "Pr", "Re", "Im", "LaTeX", "TeX", "Vert", "Box", "Diamond", "S",
              "P", "L", "O", "AA", "AE", "OE", "Huge", "LARGE", "Large", "Join", "Cap", "Cup", "Subset", "Supset", "Vdash", "VDash",
              "Rrightarrow", "Lleftarrow", "Lsh", "Rsh", "Finv", "Game", "Bbbk", "Varangle", "H", "Xi"}


def fx_lost_linebreak(t: str) -> str:
    """'\\The operation ...' outside math: a '\\\\' line break that lost a backslash."""
    spans = math_spans(t)
    out, last = [], 0
    for m in re.finditer(r"(\\+)([A-Z][a-z]*)(?![A-Za-z])", t):
        bs, word = m.group(1), m.group(2)
        if len(bs) % 2 == 0 or word in UPPER_CMDS or in_math(spans, m.start()):
            continue  # an even run is row breaks followed by prose; odd means one backslash is missing
        out.append(t[last:m.start()] + bs + "\\" + word)
        last = m.end()
    out.append(t[last:])
    return "".join(out)


def fx_backtick_math(t: str) -> str:
    """Markdown backticks around LaTeX math: `\\eta_{th}` -> \\(\\eta_{th}\\)."""
    spans = math_spans(t)
    out, last = [], 0
    for m in re.finditer(r"`([^`\n]*)`", t):
        inner = m.group(1)
        # a command, a superscript, or a short-base subscript (h_6, T_m, G_{solid}); `most_traded` stays code
        mathy = re.search(r"\\[A-Za-z]|\^", inner) or re.search(r"(?<![A-Za-z])[A-Za-z]{1,2}_(\{[^{}]*\}|[A-Za-z0-9]{1,3}(?![A-Za-z0-9]))", inner)
        if in_math(spans, m.start()) or not mathy or "$" in inner:
            continue
        out.append(t[last:m.start()] + "\\(" + m.group(1) + "\\)")
        last = m.end()
    out.append(t[last:])
    return "".join(out)


def fx_blank_in_math(t: str) -> str:
    def clean(m: re.Match) -> str:
        return re.sub(r"\n[ \t]*\n+", "\n", m.group(0))

    def clean_rows(m: re.Match) -> str:
        """Blank lines between rows of an alignment: the author separated rows
        with paragraphs instead of \\\\, so each paragraph becomes a row."""
        lines = m.group(0).split("\n")
        out: list[str] = []
        for k, ln in enumerate(lines):
            if ln.strip():
                out.append(ln)
                continue
            nxt = next((x for x in lines[k + 1:] if x.strip()), "")
            prev = out[-1] if out else ""
            if (prev.strip() and nxt and not nxt.lstrip().startswith("\\end")
                    and not re.search(r"\\\\(\[[^\]]*\])?\s*$", prev) and not re.match(r"\s*\\begin\{", prev)):
                out[-1] = prev.rstrip() + " \\\\"
        return "\n".join(out)

    t = re.sub(r"\\begin\{(align\*?|gather\*?|eqnarray\*?|aligned|cases|split|gathered|alignat\*?)\}.*?\\end\{\1\}",
               clean_rows, t, flags=re.S)
    t = re.sub(r"\\begin\{(equation\*?|multline\*?)\}.*?\\end\{\1\}", clean, t, flags=re.S)
    t = re.sub(r"(?<!\\)\\\[.*?\\\]", clean, t, flags=re.S)
    return t


def fx_env_balance(t: str) -> str:
    """Stray \\end removed, unclosed \\begin closed, list ends renamed to match."""
    stack: list[str] = []
    edits: list[tuple[int, int, str]] = []
    for m in re.finditer(r"\\(begin|end)\{([A-Za-z*]+)\}", t):
        env = m.group(2)
        if m.group(1) == "begin":
            stack.append(env)
        elif stack and stack[-1] == env:
            stack.pop()
        elif env in stack:
            inserts = []
            while stack and stack[-1] != env:
                inserts.append(stack.pop())
            stack.pop()
            edits.append((m.start(), m.start(), "".join(f"\\end{{{e}}}" for e in inserts)))
        elif stack and env in LIST_ENVS and stack[-1] in LIST_ENVS:
            edits.append((m.start(), m.end(), f"\\end{{{stack[-1]}}}"))
            stack.pop()
        else:
            edits.append((m.start(), m.end(), ""))
    for a, b, rep in sorted(edits, reverse=True):
        t = t[:a] + rep + t[b:]
    if stack:
        t = t.rstrip() + "".join(f"\n\\end{{{e}}}" for e in reversed(stack)) + "\n"
    return t


def fx_itemless_lists(t: str) -> str:
    def rep(m: re.Match) -> str:
        env, body = m.group(1), m.group(2)
        if "\\item" in body:
            return m.group(0)
        lines = body.split("\n")
        if not any(ln.strip() for ln in lines):
            return ""
        # a line that looks like an entry gets \item; a prose line continues the previous item
        new, first = [], True
        for ln in lines:
            s = ln.strip()
            entry = bool(re.match(r"(\\\(|\\\[|\$|\d+[.)]|\(|[-*•])", s)) or len(s) < 80
            if s and not s.startswith(("\\begin", "\\end", "\\label")) and (entry or first):
                new.append(re.sub(r"^(\s*)", r"\1\\item ", ln, count=1))
                first = False
            else:
                new.append(ln)
        return f"\\begin{{{env}}}" + "\n".join(new) + f"\\end{{{env}}}"

    return re.sub(r"\\begin\{(itemize|enumerate)\}(.*?)\\end\{\1\}", rep, t, flags=re.S)


def fx_lonely_items(t: str) -> str:
    spans = math_spans(t)
    lines = t.split("\n")
    out, i, depth, pos = [], 0, 0, 0
    while i < len(lines):
        ln = lines[i]
        s = ln.lstrip()
        if depth == 0 and "\\item" in ln and not in_math(spans, pos + ln.find("\\item")):
            if s.startswith("\\item"):
                out.append("\\begin{itemize}")
                while i < len(lines) and lines[i].strip() != "" and not re.match(r"\s*\\(begin|end|section|subsection)\b", lines[i]):
                    out.append(lines[i])
                    pos += len(lines[i]) + 1
                    i += 1
                out.append("\\end{itemize}")
                continue
            k = ln.find("\\item")
            if "\\begin{" not in ln[:k]:
                ln = ln[:k] + "\\begin{itemize}" + ln[k:] + "\\end{itemize}"
        for m in re.finditer(r"\\(begin|end)\{([A-Za-z*]+)\}", lines[i]):
            if m.group(2) in LIST_ENVS:
                depth += 1 if m.group(1) == "begin" else -1
        depth = max(depth, 0)
        out.append(ln)
        pos += len(lines[i]) + 1
        i += 1
    return "\n".join(out)


def fx_nested_display(t: str) -> str:
    """\\[ ... \\begin{align*} ... \\end{align*} ... \\] -> the align alone."""
    edits = []
    for a, b in math_spans(t):
        opener = t[a:a + 2]
        if opener in ("\\[", "$$") and re.search(r"\\begin\{(align\*?|gather\*?|equation\*?|multline\*?)\}", t[a:b]):
            if t[b - 2:b] == ("\\]" if opener == "\\[" else "$$"):
                edits.append((b - 2, b, ""))
                edits.append((a, a + 2, ""))
    for a, b, rep in sorted(edits, reverse=True):
        t = t[:a] + rep + t[b:]
    return t


def fx_wrap_aligned(t: str) -> str:
    """\\begin{aligned} etc. outside math mode -> wrapped in \\[ \\]."""
    spans = math_spans(t)
    edits = []
    for m in re.finditer(r"\\begin\{(aligned|gathered|cases|split|alignedat|dcases|array|matrix|pmatrix|bmatrix|vmatrix|Vmatrix|smallmatrix)\}", t):
        if in_math(spans, m.start()):
            continue
        end = re.compile(r"\\end\{" + re.escape(m.group(1)) + r"\}").search(t, m.end())
        if not end:
            continue
        if m.group(1) == "aligned" and "\\tag" in t[m.end():end.start()]:
            # \tag is not allowed inside aligned: make it a top-level align* instead
            edits.append((end.start(), end.end(), "\\end{align*}"))
            edits.append((m.start(), m.end(), "\\begin{align*}"))
            continue
        edits.append((end.end(), end.end(), "\\]"))
        edits.append((m.start(), m.start(), "\\["))
    for a, b, rep in sorted(edits, reverse=True):
        t = t[:a] + rep + t[b:]
    return t


def fx_display_length(t: str) -> str:
    return re.sub(r"(?<!\\)\\\[\s*(-?\d*\.?\d+\s*(?:pt|em|ex|mm|cm|in|bp))\s*\]", r"\\vspace{\1}", t)


def fx_space_display(t: str) -> str:
    """'\\\\ [ ... \\]' (a lost display opener) -> '\\[ ... \\]'."""
    return re.sub(r"(?<!\\)\\\\\s*\[(?!\s*-?\d)(?=[^\]]*\\\])", r"\\[", t)


def fx_display_balance(t: str) -> str:
    """Stray \\] removed; an unclosed \\[ is closed at the end."""
    open_at: int | None = None
    edits = []
    for m in re.finditer(r"(?<!\\)\\([\[\]])", t):
        if m.group(1) == "[":
            if open_at is None:
                open_at = m.start()
        else:
            if open_at is None:
                edits.append((m.start(), m.end(), ""))
            else:
                open_at = None
    for a, b, rep in sorted(edits, reverse=True):
        t = t[:a] + rep + t[b:]
    if open_at is not None:
        t = t.rstrip() + "\n\\]\n"
    return t


def fx_math_delims(t: str) -> str:
    """'$ \\[ ... \\] $' -> '\\[ ... \\]' (and the \\( \\) variant)."""
    edits = []
    for a, b in math_spans(t):
        if t[a] != "$":
            continue
        d = 2 if t.startswith("$$", a) else 1
        inner = t[a + d:b - d].strip()
        if (inner.startswith("\\[") and inner.endswith("\\]")) or (inner.startswith("\\(") and inner.endswith("\\)")):
            edits.append((a, b, inner))
    for a, b, rep in sorted(edits, reverse=True):
        t = t[:a] + rep + t[b:]
    return t


def _process_text_args(t: str, innermost_only: bool) -> tuple[str, bool]:
    pat = re.compile(r"\\(text|textbf|textit|mbox|textrm|emph|underline|section\*?|subsection\*?|paragraph)\s*\{")
    out, i, changed = [], 0, False
    while True:
        m = pat.search(t, i)
        if not m:
            out.append(t[i:])
            break
        k = _balanced_arg(t, m.end() - 1)
        if k is None:
            out.append(t[i:m.end()])
            i = m.end()
            continue
        inner = t[m.end():k - 1]
        if innermost_only and pat.search(inner):
            out.append(t[i:m.end()])
            i = m.end()
            continue
        new = re.sub(r"(?<!\\)&", r"\\&", inner)
        new = re.sub(r"\\math(rm|bf|it)\{", r"\\text\1{", new)
        if "\n" not in new and (re.search(r"(?<!\\)[\^_]", new) or MATH_CMD_RE.search(new)):
            # a symbol command glued to a word ("kg\cdot K") gets its own $ $; the rest goes through the token wrapper
            ispans = math_spans(new)
            new = SYMBOL_CMD_RE.sub(lambda x: x.group(0) if in_math(ispans, x.start()) else "$" + x.group(0) + "$", new)
            new = _wrap_math_in_line(new, "$", "$")
        changed = changed or new != inner
        out.append(t[i:m.end()] + new + "}")
        i = k
    return "".join(out), changed


def fx_amp_in_text(t: str) -> str:
    """Inside a text-mode argument (\\text{}, \\textbf{}, \\section{} ...): '&' escaped,
    \\mathrm -> \\textrm, and math-only tokens (x^2, \\cdot, \\dot{x}) wrapped in $ $.
    Innermost arguments first, so an outer argument's token wrapper respects
    the $ $ the inner ones got."""
    for _ in range(3):
        t, changed = _process_text_args(t, innermost_only=True)
        if not changed:
            break
    t, _ = _process_text_args(t, innermost_only=False)
    return t


def fx_align_fragment(t: str) -> str:
    """Top-level lines of the form '& x = y \\\\' (an alignment without its
    environment) -> \\[\\begin{aligned} ... \\end{aligned}\\]."""
    lines = t.split("\n")
    spans = math_spans(t)
    pos, out, block = 0, [], []

    def flush() -> None:
        if block:
            rows = [re.sub(r"\\\\\s*$", "", ln).rstrip() for ln in block]
            out.append("\\begin{align*}")  # align* (not aligned) so a \tag in a row is allowed
            out.extend(r + " \\\\" for r in rows[:-1])
            out.append(rows[-1])
            out.append("\\end{align*}")
            block.clear()

    for ln in lines:
        top = not in_math(spans, pos) and env_depth_at(t, pos, ALIGN_ENVS | LIST_ENVS) == 0
        if (top and re.search(r"(?<!\\)&", ln) and ("=" in ln or ln.rstrip().endswith("\\\\"))
                and not re.search(r"\\(hline|textbf|item|multicolumn)", ln) and "$" not in ln and "\\(" not in ln):
            block.append(ln)
        else:
            flush()
            out.append(ln)
        pos += len(ln) + 1
    flush()
    return "\n".join(out)


def fx_text_specials(t: str) -> str:
    """'_', '&', '#' outside math mode -> escaped (math-looking tokens are left
    for the math wrapper; '&' inside alignment environments is kept)."""
    spans = math_spans(t)
    defines = bool(re.search(r"\\(newcommand|renewcommand|def|providecommand)\b", t))
    out = []
    for i, ch in enumerate(t):
        if ch in "_&#" and not in_math(spans, i) and (i == 0 or t[i - 1] != "\\"):
            if ch == "&" and env_depth_at(t, i, ALIGN_ENVS) > 0:
                out.append(ch)
                continue
            if ch == "#" and defines:
                out.append(ch)
                continue
            if ch == "_":
                a = i
                while a > 0 and not t[a - 1].isspace():
                    a -= 1
                b = i
                while b < len(t) and not t[b].isspace():
                    b += 1
                if _token_is_math(t[a:b]):
                    out.append(ch)
                    continue
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def fx_mathrm_text(t: str) -> str:
    spans = math_spans(t)
    out, last = [], 0
    for m in re.finditer(r"\\math(rm|bf|it)\{", t):
        if not in_math(spans, m.start()):
            out.append(t[last:m.start()] + "\\text" + m.group(1) + "{")
            last = m.end()
    out.append(t[last:])
    return "".join(out)


VERT_END = re.compile(r"(\\(begin|end)\{(" + "|".join(sorted(VERTICAL_ENVS)) + r")\}|\\item(\[[^\]]*\])?|"
                      r"\\(section|subsection|subsubsection|paragraph)\*?\{[^}]*\})$")
SKIPPABLE = re.compile(r"(\\vspace\*?\{[^}]*\}|\\par(?![A-Za-z])|\\smallskip|\\medskip|\\bigskip|\\noindent|\\centering|\s)+$")


def _vertical_before(before: str) -> bool:
    core = SKIPPABLE.sub("", before)
    ws = before[len(core):]
    if core == "" or re.search(r"\n[ \t]*\n", ws):
        return True
    return bool(VERT_END.search(core))


def fx_bad_linebreak(t: str) -> str:
    """Remove '\\\\' that TeX meets in vertical mode (paragraph start, right
    after a list or centre environment, right after \\item)."""
    out, last = [], 0
    for m in re.finditer(r"(?<!\\)\\\\(\[[^\]\n]*\])?|(?<!\\)\\newline(?![A-Za-z])", t):
        if _vertical_before(t[:m.start()]):
            out.append(t[last:m.start()])
            last = m.end()
    out.append(t[last:])
    return "".join(out)


def fx_newline_optarg(t: str) -> str:
    def rep(m: re.Match) -> str:
        inside = m.group(2).lstrip()[1:]
        return m.group(0) if LENGTH_RE.match(inside) else m.group(1) + "{}" + m.group(2)

    return re.sub(r"(?<!\\)(\\\\)(\s*\n\s*\[[^\n]*)", rep, t)


def fx_array_colspec(t: str) -> str:
    def rep(m: re.Match) -> str:
        env, spec, body = m.group(1), m.group(2), m.group(3)
        if not re.fullmatch(r"[lcr| ]*", spec):
            return m.group(0)
        cols = len(re.findall(r"[lcr]", spec))
        rows = re.split(r"\\\\", body)
        counts = [len(re.findall(r"(?<!\\)&", r)) + 1 for r in rows if re.search(r"(?<!\\)&", r)]
        need = max(counts, default=cols)
        if need <= cols or cols == 0:
            return m.group(0)
        extra = re.findall(r"[lcr]", spec)[-1] * (need - cols)
        return f"\\begin{{{env}}}{{{spec}{extra}}}{body}\\end{{{env}}}"

    return re.sub(r"\\begin\{(tabular|array)\}\{([^}]*)\}(.*?)\\end\{\1\}", rep, t, flags=re.S)


def fx_math_lines(t: str) -> str:
    lines = t.split("\n")
    spans = math_spans(t)
    pos, out = 0, []
    for ln in lines:
        if (ln.strip() and not in_math(spans, pos) and not in_math(spans, pos + max(len(ln) - 1, 0))
                and env_depth_at(t, pos, ALIGN_ENVS) == 0):
            out.append(_wrap_math_in_line(ln))
        else:
            out.append(ln)
        pos += len(ln) + 1
    return "\n".join(out)


GLOBAL_FIXERS = [
    ("normalize", fx_normalize), ("undouble", fx_undouble), ("literal_escapes", fx_literal_escapes), ("typos", fx_typos),
    ("markdown_escapes", fx_markdown_escapes), ("unknown_cmds", fx_unknown_cmds), ("lost_linebreak", fx_lost_linebreak),
    ("backtick_math", fx_backtick_math), ("blank_in_math", fx_blank_in_math), ("hline_rows", fx_hline_rows), ("env_balance", fx_env_balance),
    ("itemless_lists", fx_itemless_lists), ("lonely_items", fx_lonely_items), ("nested_display", fx_nested_display),
    ("wrap_aligned", fx_wrap_aligned), ("display_length", fx_display_length), ("space_display", fx_space_display),
    ("display_balance", fx_display_balance), ("math_delims", fx_math_delims), ("amp_in_text", fx_amp_in_text),
    ("align_fragment", fx_align_fragment), ("text_specials", fx_text_specials), ("mathrm_text", fx_mathrm_text),
    ("bad_linebreak", fx_bad_linebreak), ("newline_optarg", fx_newline_optarg), ("array_colspec", fx_array_colspec),
    ("math_lines", fx_math_lines),
]

# --- log-guided round --------------------------------------------------------------

_OFFSET: int | None = None


def solution_line_offset(cfg: dict) -> int:
    """Document line number (1-based) that holds the first solution line."""
    global _OFFSET
    if _OFFSET is None:
        doc = build_document("@@MARK@@", cfg=cfg)
        _OFFSET = next(i for i, ln in enumerate(doc.split("\n"), 1) if "@@MARK@@" in ln)
    return _OFFSET


def error_position(log_tail: str, text: str, cfg: dict) -> tuple[int, int] | None:
    """(line index, position just after the offending token) from the XeLaTeX
    log's 'l.<n> <read so far>' context line."""
    m = re.search(r"^l\.(\d+) (.*)$", log_tail, re.M)
    if not m:
        return None
    idx = int(m.group(1)) - solution_line_offset(cfg)
    lines = text.split("\n")
    if idx < 0 or idx >= len(lines):
        return None
    line = lines[idx]
    before = m.group(2)
    truncated = before.startswith("...")
    if truncated:
        before = before[3:]
    nb = re.sub(r"\s+", "", before)
    pos_map = [i for i, c in enumerate(line) if not c.isspace()]
    nl = "".join(line[i] for i in pos_map)
    if not nb:
        return idx, 0
    if not truncated and nl.startswith(nb):
        p_norm = len(nb)
    else:
        p_norm = None
        for k in range(len(nb), 5, -1):
            j = nl.find(nb[-k:])
            if j >= 0:
                p_norm = j + k
                break
        if p_norm is None:
            return None
    return idx, (pos_map[p_norm - 1] + 1 if p_norm > 0 else 0)


def _token_at(line: str, p: int) -> tuple[int, int] | None:
    for a, b in _tokens_with_spans(line):
        if a <= p - 1 < b:
            return a, b
    return None


def _wrap_token_at(line: str, p: int) -> str | None:
    tb = _token_at(line, p)
    if tb is None:
        return None
    a, b = tb
    if in_math(math_spans(line), a):
        return None
    tok = line[a:b]
    core, lead, trail = _core(tok)
    if not core:
        return None
    if p >= 1 and line[p - 1] == "_" and not _token_is_math(tok):
        return line[:p - 1] + "\\_" + line[p:]
    if p >= 1 and line[p - 1] == "^" and not _token_is_math(tok):
        return line[:p - 1] + "\\^{}" + line[p:]
    if tok.startswith(TEXT_CMD_PREFIXES) and not _text_token_is_math(tok):
        return None
    if "\\left" in core and "\\right" not in core:
        return None
    return line[:a + lead] + "\\(" + core + "\\)" + line[a + lead + len(core):]


def targeted_fix(text: str, res: dict, cfg: dict) -> tuple[str, str | None]:
    err = next((e for e in res["errors"] if e.startswith("! ")), res["errors"][0] if res["errors"] else "")
    if "Erroneous nesting" in err:
        new = fx_nested_display(text)
        return (new, "nested_display@err") if new != text else (text, None)
    if "allowed only in math mode" in err:
        new = fx_wrap_aligned(text)
        return (new, "wrap_aligned@err") if new != text else (text, None)
    if "perhaps a missing \\item" in err:
        new = fx_itemless_lists(text)
        return (new, "itemless@err") if new != text else (text, None)
    if "Lonely \\item" in err:
        new = fx_lonely_items(text)
        return (new, "lonely_items@err") if new != text else (text, None)
    em = re.search(r"Environment ([A-Za-z*]+) undefined", err)
    if em:
        env = em.group(1)
        repl = {"displayquote": "quote", "tabu": "tabular", "longtable": "tabular", "lstlisting": "verbatim", "subequations": None,
                "multicols": None, "framed": None, "mdframed": None, "tcolorbox": None, "adjustwidth": None, "spacing": None}
        if env in repl:
            if repl[env] is None:
                new = re.sub(r"\\(begin|end)\{" + re.escape(env) + r"\}(\{[^}]*\})?", "", text)
            else:
                new = text.replace(f"\\begin{{{env}}}", f"\\begin{{{repl[env]}}}").replace(f"\\end{{{env}}}", f"\\end{{{repl[env]}}}")
            return (new, f"env_{env}@err") if new != text else (text, None)
        return text, None
    loc = error_position(res.get("log_tail", ""), text, cfg)
    if loc is None:
        return text, None
    idx, p = loc
    lines = text.split("\n")
    line = lines[idx]
    new_line: str | None = None
    tag = None
    at_delim = line[max(p - 2, 0):p] in ("\\]", "\\[", "\\)", "\\(")
    if "no line here to end" in err:
        m = re.search(r"((?<!\\)\\\\(\[[^\]]*\])?|\\newline)\s*$", line[:p])
        if m:
            new_line, tag = line[:m.start(1)] + line[m.end(1):], "linebreak@pos"
    elif "Missing $ inserted" in err or ("Bad math environment delimiter" in err and not at_delim):
        if not line.strip():
            return text, None
        new_line, tag = _wrap_token_at(line, p), "math@pos"
    elif "Bad math environment delimiter" in err:
        new_line, tag = line[:p - 2] + line[p:], "delim@pos"
    elif "Misplaced alignment tab" in err or "Extra alignment tab" in err:
        if p >= 1 and line[p - 1] == "&":
            new_line, tag = line[:p - 1] + "\\&" + line[p:], "ampersand@pos"
    elif "Undefined control sequence" in err:
        cm = re.search(r"(\\[A-Za-z@]+|\\[^A-Za-z\s])\s*$", line[:p])
        if cm:
            name = cm.group(1)
            s, e = cm.start(1), cm.end(1)
            if name in ("\\end", "\\begin"):
                new = fx_env_balance(text)
                return (new, "env_balance@err") if new != text else (text, None)
            if re.match(r"\\n[A-Za-z]*$", name) and name[1:].lower() not in N_CMDS_CI:
                new_line, tag = line[:s] + "\n" + name[2:] + line[e:], "literal_n@pos"
            elif re.match(r"\\t[A-Z][A-Za-z]*$", name):
                new_line, tag = line[:s] + " " + name[2:] + line[e:], "literal_t@pos"
            elif re.match(r"\\r[A-Z][A-Za-z]*$", name) and name[1:] not in R_CMDS_UPPER:
                new_line, tag = line[:s] + name[2:] + line[e:], "literal_r@pos"
            elif re.match(r"\\(textbf|textit|emph|underline)[A-Z]", name):
                new_line, tag = line[:s] + re.sub(r"^(\\[a-z]+)", r"\1{", name) + line[e:], "brace@pos"
            elif name in ("\\tightlist", "\\centering", "\\raggedright", "\\sloppy", "\\justifying", "\\onehalfspacing",
                          "\\singlespacing", "\\arraybackslash", "\\ltag"):
                new_line, tag = line[:s] + line[e:], "dropcmd@pos"
            elif name in ("\\toprule", "\\midrule", "\\bottomrule"):
                new_line, tag = line[:s] + "\\hline" + line[e:], "rule@pos"
            elif name in ("\\mathscr", "\\mathds", "\\mathbbm"):
                new_line, tag = line[:s] + "\\mathcal" + line[e:], "mathcal@pos"
            elif name == "\\degree":
                new_line, tag = line[:s] + "^\\circ" + line[e:], "degree@pos"
            elif name in ("\\href", "\\url", "\\multirow", "\\wideparen", "\\textdegree", "\\passthrough", "\\lstinline", "\\Varangle"):
                new = fx_unknown_cmds(text)
                return (new, "unknown_cmds@err") if new != text else (text, None)
            elif re.match(r"\\(" + MATH_CMDS + r")([A-Z][A-Za-z]*)$", name):
                # "J/kg\cdotK": a math command run into the next word
                mm = re.match(r"\\(" + MATH_CMDS + r")([A-Z][A-Za-z]*)$", name)
                cmd, word = "\\" + mm.group(1), mm.group(2)
                rep = cmd + " " + word if in_math(math_spans(line), s) else "$" + cmd + "$" + word
                new_line, tag = line[:s] + rep + line[e:], "splitcmd@pos"
            elif re.match(r"\\[A-Z][a-z]*$", name) and name[1:] not in UPPER_CMDS and not in_math(math_spans(line), s):
                new_line, tag = line[:s] + "\\" + name + line[e:], "lost_linebreak@pos"
    elif "Missing number" in err or "Illegal unit" in err or "Paragraph ended before \\@newline" in err:
        m = re.search(r"(?<!\\)\\\\\s*\[(?!\s*-?\d)", line)
        if m:
            new_line, tag = line[:m.start()] + "\\[" + line[m.end():], "space_display@pos"
    elif "Extra }" in err and p >= 1 and line[p - 1] == "}":
        new_line, tag = line[:p - 1] + line[p:], "extra_brace@pos"
    elif "ended by \\end" in err:
        new = fx_env_balance(text)
        return (new, "env_balance@err") if new != text else (text, None)
    if new_line is None or new_line == line:
        return text, None
    lines[idx] = new_line
    return "\n".join(lines), tag


# --- driver ------------------------------------------------------------------------


def repair(qid: int, original: str, cfg: dict) -> dict:
    text, applied = original, []
    for name, fn in GLOBAL_FIXERS:
        try:
            new = fn(text)
        except Exception as e:  # a fixer bug must not kill the run
            applied.append(f"{name}!{type(e).__name__}")
            continue
        if new != text:
            applied.append(name)
            text = new
    res = check_pdf(text, cfg=cfg)
    rounds, prev_err = 0, None
    while not _compiles(res) and rounds < MAX_ROUNDS:
        err = res["errors"][0] if res["errors"] else ""
        if err == prev_err:
            break
        prev_err = err
        try:
            new, tag = targeted_fix(text, res, cfg)
        except Exception as e:
            applied.append(f"targeted!{type(e).__name__}")
            break
        if tag is None or new == text:
            break
        applied.append(tag)
        text = new
        rounds += 1
        res = check_pdf(text, cfg=cfg)
    ok = _compiles(res)
    return {
        "question_id": qid, "ok": ok, "soft": ok and not res["ok"], "fixers": applied, "rounds": rounds,
        "error": "" if res["ok"] else (res["errors"][0] if res["errors"] else "")[:300].replace("\n", " | "),
        "changed": text != original, "original": original, "fixed": text if ok else None,
    }


SOFT = re.compile(r"^(LaTeX Warning: (Reference|Citation) .* undefined|Missing character: There is no)")


def _compiles(res: dict) -> bool:
    """The PDF is produced: no error, or only soft ones (an undefined \\ref
    printing '??', a character missing from the font), the same split the
    old-solution report uses."""
    return bool(res["ok"]) or (bool(res["errors"]) and all(SOFT.match(e) for e in res["errors"])
                               and not any("exit code" in e or "timed out" in e for e in res["errors"]))


def targets(ids: list[int] | None) -> list[int]:
    rows = list(csv.DictReader(open(BREAKS_CSV, encoding="utf-8", newline="")))
    out = [int(r["question_id"]) for r in rows if r["pdf_fault"] == "solution"]
    if ids:
        want = set(ids)
        out = [q for q in out if q in want]
    return out


def cmd_run(a) -> None:
    cfg = load_config()
    ids = [int(x) for x in a.ids.split(",") if x.strip()] if a.ids else None
    qids = targets(ids)
    if a.limit:
        qids = qids[: a.limit]
    app = app_conn(cfg)
    sols = {r[0]: r[1] for r in app.execute(
        f"SELECT question_id, solution FROM questions WHERE question_id IN ({','.join('?' * len(qids))})", qids)}
    app.close()
    results: dict[str, dict] = {}
    if FIXES_JSON.exists() and not a.fresh:
        results = json.loads(FIXES_JSON.read_text(encoding="utf-8"))
    if a.redo:
        for q in qids:
            results.pop(str(q), None)
    todo = [q for q in qids if str(q) not in results and q in sols]
    print(json.dumps({"targets": len(qids), "already_done": len(qids) - len(todo), "to_repair": len(todo), "workers": a.workers}), flush=True)
    counts: Counter = Counter()
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(repair, q, sols[q], cfg): q for q in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            q = futs[fut]
            try:
                r = fut.result()
            except Exception as e:
                r = {"question_id": q, "ok": False, "fixers": [], "rounds": 0, "error": "repair crashed: " + str(e)[:200],
                     "changed": False, "original": sols[q], "fixed": None}
            results[str(q)] = r
            counts["ok" if r["ok"] else "still_failing"] += 1
            if i % 25 == 0 or i == len(futs):
                REPORTS_DIR.mkdir(parents=True, exist_ok=True)
                FIXES_JSON.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
                print(json.dumps({"done": i, "of": len(futs), "elapsed_s": int(time.time() - t0), **counts}), flush=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIXES_JSON.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
    with open(FIXES_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["question_id", "ok", "fixers", "rounds", "error"])
        for q in qids:
            r = results.get(str(q))
            if r:
                w.writerow([q, int(r["ok"]), "+".join(r["fixers"]), r["rounds"], r["error"]])
    fixer_counts = Counter(f for r in results.values() if r["ok"] for f in r["fixers"])
    print(json.dumps({"repaired_and_compiling": sum(1 for r in results.values() if r["ok"]),
                      "still_failing": sum(1 for r in results.values() if not r["ok"]),
                      "fixers_used": dict(fixer_counts.most_common())}, indent=1), flush=True)


def _ensure_table(pc: sqlite3.Connection) -> None:
    pc.execute("""CREATE TABLE IF NOT EXISTS solution_fixes (
        question_id INTEGER PRIMARY KEY, original TEXT NOT NULL, fixed TEXT NOT NULL,
        fixers TEXT, applied_at TEXT, reverted_at TEXT)""")
    pc.commit()


def cmd_apply(a) -> None:
    cfg = load_config()
    results = json.loads(FIXES_JSON.read_text(encoding="utf-8"))
    pc = pipe_conn()
    _ensure_table(pc)
    app = app_conn(cfg, readonly=False)
    n, skipped = 0, 0
    for q, r in results.items():
        if not r["ok"] or not r["changed"] or not r["fixed"]:
            continue
        cur = app.execute("SELECT solution FROM questions WHERE question_id=?", (int(q),)).fetchone()
        if cur is None or cur[0] != r["original"]:
            skipped += 1
            print(f"skip {q}: stored solution changed since the repair was computed")
            continue
        app.execute("UPDATE questions SET solution=? WHERE question_id=?", (r["fixed"], int(q)))
        pc.execute("INSERT OR REPLACE INTO solution_fixes (question_id, original, fixed, fixers, applied_at, reverted_at) "
                   "VALUES (?,?,?,?,?,NULL)", (int(q), r["original"], r["fixed"], "+".join(r["fixers"]), now_iso()))
        n += 1
    app.commit()
    pc.commit()
    print(json.dumps({"applied": n, "skipped": skipped}))


def cmd_revert(a) -> None:
    cfg = load_config()
    pc = pipe_conn()
    _ensure_table(pc)
    app = app_conn(cfg, readonly=False)
    n = 0
    for r in pc.execute("SELECT question_id, original, fixed FROM solution_fixes WHERE reverted_at IS NULL").fetchall():
        cur = app.execute("SELECT solution FROM questions WHERE question_id=?", (r[0],)).fetchone()
        if cur and cur[0] == r[2]:
            app.execute("UPDATE questions SET solution=? WHERE question_id=?", (r[1], r[0]))
            pc.execute("UPDATE solution_fixes SET reverted_at=? WHERE question_id=?", (now_iso(), r[0]))
            n += 1
    app.commit()
    pc.commit()
    print(json.dumps({"reverted": n}))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--limit", type=int)
    p.add_argument("--ids")
    p.add_argument("--fresh", action="store_true", help="discard every previous result in the fixes JSON")
    p.add_argument("--redo", action="store_true", help="recompute the targeted ids, keep the other results")
    sub.add_parser("apply")
    sub.add_parser("revert")
    a = ap.parse_args()
    {"run": cmd_run, "apply": cmd_apply, "revert": cmd_revert}[a.cmd](a)


if __name__ == "__main__":
    main()
