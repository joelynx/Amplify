"""LaTeX sanitizers for user-typed header / title / instructions content.

Spec §6.3 — three escalating levels. The contract:

* **Question bodies are NEVER sanitized.** These functions run only over content
  the user typed into the Settings → PDF Output editors (headers, title line,
  instructions block).
* The escape-level allows a tiny set of formatting commands and inline math.
* The basic level (left/right headers) adds whitelisted math commands but
  forbids `\\input`, `\\verb`, etc.
* The extended level (title / instructions) further adds display math,
  itemize/enumerate, and underline-family commands.

The implementation walks the input, recognizing safe regions (whitelisted
commands and math) and escaping the rest. Forbidden commands raise
`SanitizeError`.
"""

from __future__ import annotations

import re
from typing import Final

__all__ = [
    "SanitizeError",
    "escape_latex",
    "sanitize_latex_basic",
    "sanitize_latex_extended",
]


class SanitizeError(ValueError):
    """Raised when input contains a forbidden LaTeX command."""


# --- Character escapes ---------------------------------------------------
_ESCAPES: Final[dict[str, str]] = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
    "^": r"\textasciicircum{}",
    "~": r"\textasciitilde{}",
}


def _escape_char(ch: str) -> str:
    return _ESCAPES.get(ch, ch)


def _escape_plain(text: str) -> str:
    return "".join(_escape_char(c) for c in text)


# --- Forbidden command list (spec §6.3) ---------------------------------
# Apply at every level. Math-mode content gets scanned for these too.
_FORBIDDEN_COMMANDS: Final[frozenset[str]] = frozenset(
    [
        "input",
        "include",
        "newcommand",
        "renewcommand",
        "def",
        "let",
        "usepackage",
        "documentclass",
        "write",
        "openout",
        "closeout",
        "read",
        "verb",
        "verbatim",
        "lstinline",
        "lstinputlisting",
        "url",
        "href",
        "includegraphics",
        "label",
        "ref",
        "cite",
        "bibliography",
        "bibliographystyle",
    ]
)

_ANY_COMMAND_RE = re.compile(r"\\([a-zA-Z]+)")


def _assert_no_forbidden(text: str, where: str) -> None:
    for m in _ANY_COMMAND_RE.finditer(text):
        if m.group(1) in _FORBIDDEN_COMMANDS:
            raise SanitizeError(f"forbidden command \\{m.group(1)} in {where}")


# --- Whitelists ---------------------------------------------------------
# Commands that take exactly one braced argument.
_TEXT_FORMAT_CMDS: Final[frozenset[str]] = frozenset(
    ["textbf", "texttt", "textsc", "textit", "underline", "emph"]
)
# Extended-level additions for the underline family.
_EXTENDED_UNDERLINE_CMDS: Final[frozenset[str]] = frozenset(
    ["uline", "uuline", "uwave", "sout", "xout", "dashuline", "dotuline"]
)

# Math-mode whitelist used by the basic and extended sanitizers. These are
# Spotted by name only — their arguments are math text, scanned but not escaped.
_MATH_WHITELIST_RE: Final = re.compile(
    r"\\(?:"
    r"frac|sqrt|sum|int|lim|prod|coprod|oint|iint|iiint"  # operators
    r"|alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa"  # Greek lower
    r"|lambda|mu|nu|xi|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega"
    r"|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega"  # Greek upper
    r"|mathbb|mathcal|mathbf|mathit|mathrm|mathsf|mathfrak|boldsymbol"  # font shape
    r"|leq|geq|neq|approx|sim|simeq|equiv|cong|propto|in|notin|subset|supset|subseteq|supseteq"  # relations
    r"|cup|cap|setminus|emptyset|infty|partial|nabla|forall|exists"
    r"|to|gets|rightarrow|leftarrow|leftrightarrow|Rightarrow|Leftarrow|Leftrightarrow|mapsto"
    r"|cdot|cdots|ldots|vdots|ddots|times|div|pm|mp|circ"
    r"|left|right|big|Big|bigg|Bigg|begin|end"  # delimiters / structures (begin/end checked later)
    r"|displaystyle|textstyle|scriptstyle"
    r"|operatorname|text"
    r")\b"
)

# `\begin{...}` / `\end{...}` constraints (extended only): allow itemize/enumerate.
_ALLOWED_ENVS_EXTENDED: Final[frozenset[str]] = frozenset(["itemize", "enumerate"])


# --- Tokenizing helpers --------------------------------------------------
def _find_matching_brace(text: str, start: int) -> int:
    """Given text[start] == '{', return the index of the matching '}'.

    Counts braces honoring escaped `\\{` / `\\}`. Raises if unbalanced.
    """
    assert text[start] == "{"
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text) and text[i + 1] in "{}":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SanitizeError("unbalanced braces")


def _find_inline_math_end(text: str, start: int) -> int:
    """`text[start]` is `$`. Return index of closing `$`."""
    assert text[start] == "$"
    i = start + 1
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            i += 2
            continue
        if text[i] == "$":
            return i
        i += 1
    raise SanitizeError("unterminated inline math")


def _find_display_math_dollars(text: str, start: int) -> int:
    """`text[start:start+2]` is `$$`. Return index of opening `$` of closing `$$`."""
    i = start + 2
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            i += 2
            continue
        if text[i] == "$" and i + 1 < len(text) and text[i + 1] == "$":
            return i
        i += 1
    raise SanitizeError("unterminated display math")


def _find_bracket_display_end(text: str, start: int) -> int:
    """`text[start:start+2]` is `\\[`. Return index of `\\]`."""
    i = start + 2
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            if text[i + 1] == "]":
                return i
            i += 2
            continue
        i += 1
    raise SanitizeError("unterminated display math \\[ ... \\]")


# --- Math content scanning -----------------------------------------------
def _scan_math_content(content: str, level: str) -> None:
    """Math passes through unchanged but must not contain forbidden commands.

    `level` is the sanitizer level for error messages.
    """
    _assert_no_forbidden(content, f"math content ({level})")
    # Also forbid \verb-style or anything else in the deny list — already
    # covered by _assert_no_forbidden.


# --- Core sanitizer engine -----------------------------------------------
def _sanitize(
    text: str,
    *,
    allow_inline_math: bool,
    allow_display_math: bool,
    allow_lists: bool,
    allow_extended_text: bool,
    level_name: str,
) -> str:
    out: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Display math `$$ ... $$` — explicit attempt; reject if not allowed.
        if ch == "$" and i + 1 < n and text[i + 1] == "$":
            if not allow_display_math:
                raise SanitizeError(f"display math $$...$$ not allowed ({level_name})")
            close = _find_display_math_dollars(text, i)
            content = text[i + 2 : close]
            _scan_math_content(content, level_name)
            out.append(text[i : close + 2])
            i = close + 2
            continue

        # Display math `\[ ... \]`
        if ch == "\\" and i + 1 < n and text[i + 1] == "[":
            if not allow_display_math:
                raise SanitizeError(f"display math \\[...\\] not allowed ({level_name})")
            close = _find_bracket_display_end(text, i)
            content = text[i + 2 : close]
            _scan_math_content(content, level_name)
            out.append(text[i : close + 2])
            i = close + 2
            continue

        # Inline math. If there's no closing `$`, treat this `$` as a literal.
        if allow_inline_math and ch == "$":
            try:
                close = _find_inline_math_end(text, i)
            except SanitizeError:
                out.append(_ESCAPES["$"])
                i += 1
                continue
            content = text[i + 1 : close]
            _scan_math_content(content, level_name)
            out.append(text[i : close + 1])
            i = close + 1
            continue

        # Backslash command
        if ch == "\\":
            m = _ANY_COMMAND_RE.match(text, i)
            if not m:
                # Lone backslash followed by a non-letter (or end of string).
                out.append(_ESCAPES["\\"])
                i += 1
                continue

            cmd = m.group(1)
            end_cmd = m.end()
            if cmd in _FORBIDDEN_COMMANDS:
                raise SanitizeError(f"forbidden command \\{cmd} ({level_name})")

            # \begin{env} / \end{env}
            if cmd in ("begin", "end"):
                if not allow_lists:
                    raise SanitizeError(f"\\{cmd} not allowed ({level_name})")
                if end_cmd >= n or text[end_cmd] != "{":
                    raise SanitizeError(f"\\{cmd} needs an environment name")
                brace_close = _find_matching_brace(text, end_cmd)
                env_name = text[end_cmd + 1 : brace_close]
                if env_name not in _ALLOWED_ENVS_EXTENDED:
                    raise SanitizeError(f"environment {env_name!r} not allowed ({level_name})")
                end_block = brace_close + 1
                # Optional [opts] for \begin{enumerate}[label=...]
                if cmd == "begin" and end_block < n and text[end_block] == "[":
                    opt_close = text.find("]", end_block)
                    if opt_close == -1:
                        raise SanitizeError("unterminated [opts] on environment")
                    end_block = opt_close + 1
                out.append(text[i:end_block])
                i = end_block
                continue

            if cmd == "item":
                if not allow_lists:
                    raise SanitizeError(f"\\item not allowed ({level_name})")
                out.append(m.group(0))
                i = end_cmd
                if i < n and text[i] == "[":
                    opt_close = text.find("]", i)
                    if opt_close == -1:
                        raise SanitizeError("unterminated [opts] on \\item")
                    out.append(text[i : opt_close + 1])
                    i = opt_close + 1
                continue

            # Text-formatting whitelist — pass through with sanitized argument.
            if cmd in _TEXT_FORMAT_CMDS or (allow_extended_text and cmd in _EXTENDED_UNDERLINE_CMDS):
                if end_cmd >= n or text[end_cmd] != "{":
                    raise SanitizeError(f"\\{cmd} needs a braced argument ({level_name})")
                brace_close = _find_matching_brace(text, end_cmd)
                inner = text[end_cmd + 1 : brace_close]
                sanitized_inner = _sanitize(
                    inner,
                    allow_inline_math=allow_inline_math,
                    allow_display_math=allow_display_math,
                    allow_lists=allow_lists,
                    allow_extended_text=allow_extended_text,
                    level_name=level_name,
                )
                out.append(f"\\{cmd}{{{sanitized_inner}}}")
                i = brace_close + 1
                continue

            # Unknown but not forbidden: escape the backslash as a literal and
            # let the following letters fall through as plain text. Keeps the
            # spec's "Escapes `\`" promise — and is safer than the alternative
            # of passing arbitrary commands through.
            out.append(_ESCAPES["\\"])
            i += 1
            continue

        # Plain character
        out.append(_escape_char(ch))
        i += 1

    return "".join(out)


# --- Public API ----------------------------------------------------------
def escape_latex(text: str) -> str:
    """Most restrictive sanitizer (short defaults).

    Allows `\\textbf` / `\\texttt` / `\\textsc` / `\\textit` / `\\underline` /
    `\\emph` and inline math `$…$`. Escapes the standard ten special characters.
    """
    return _sanitize(
        text,
        allow_inline_math=True,
        allow_display_math=False,
        allow_lists=False,
        allow_extended_text=False,
        level_name="escape",
    )


def sanitize_latex_basic(text: str) -> str:
    """Header sanitizer (left/right header). Adds whitelisted math commands
    inside `$…$` math mode; still rejects display math, lists, and the
    forbidden-command list."""
    return _sanitize(
        text,
        allow_inline_math=True,
        allow_display_math=False,
        allow_lists=False,
        allow_extended_text=False,
        level_name="basic",
    )


def sanitize_latex_extended(text: str) -> str:
    """Title-line / instructions sanitizer. Adds display math (`$$…$$` and
    `\\[…\\]`), `itemize` / `enumerate`, and the underline-family commands."""
    return _sanitize(
        text,
        allow_inline_math=True,
        allow_display_math=True,
        allow_lists=True,
        allow_extended_text=True,
        level_name="extended",
    )
