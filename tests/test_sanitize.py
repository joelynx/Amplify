"""Golden-file tests for the three LaTeX sanitizers (spec §6.3)."""

from __future__ import annotations

import pytest

from app.tex.sanitize import (
    SanitizeError,
    escape_latex,
    sanitize_latex_basic,
    sanitize_latex_extended,
)

# --- escape_latex (most restrictive) ------------------------------------

class TestEscapeLatex:
    def test_passes_plain_text_unchanged(self):
        assert escape_latex("hello world") == "hello world"

    def test_escapes_special_chars(self):
        # ten special chars from spec §6.3
        assert escape_latex("100%") == r"100\%"
        assert escape_latex("a&b") == r"a\&b"
        assert escape_latex("x_1") == r"x\_1"
        assert escape_latex("#hash") == r"\#hash"
        # Lone $ with no closing $ is treated as a literal — escapes to \$.
        assert escape_latex("$10") == r"\$10"
        assert escape_latex("$ unterminated") == r"\$ unterminated"

    def test_lone_backslash_escapes(self):
        assert escape_latex("a\\b") == r"a\textbackslash{}b"

    def test_tilde_caret_braces(self):
        assert escape_latex("a~b") == r"a\textasciitilde{}b"
        assert escape_latex("a^b") == r"a\textasciicircum{}b"
        assert escape_latex("{x}") == r"\{x\}"

    def test_textbf_passes_through(self):
        assert escape_latex(r"\textbf{bold}") == r"\textbf{bold}"

    def test_inner_argument_is_recursively_sanitized(self):
        assert escape_latex(r"\textbf{50%}") == r"\textbf{50\%}"

    def test_inline_math_passes_through_unchanged(self):
        assert escape_latex(r"area is $\pi r^2$") == r"area is $\pi r^2$"

    def test_disallowed_command_raises(self):
        with pytest.raises(SanitizeError):
            escape_latex(r"\input{anything}")
        with pytest.raises(SanitizeError):
            escape_latex(r"\includegraphics{x.png}")
        with pytest.raises(SanitizeError):
            escape_latex(r"\verb|x|")

    def test_unknown_command_escapes_backslash_literally(self):
        # `\frac` outside math: not in the text-format whitelist and not in
        # the forbidden list — backslash escapes, letters fall through as text.
        assert escape_latex(r"\frac{a}{b}") == r"\textbackslash{}frac\{a\}\{b\}"


# --- sanitize_latex_basic (header) --------------------------------------

class TestSanitizeBasic:
    def test_allows_textbf(self):
        assert sanitize_latex_basic(r"\textbf{bold}") == r"\textbf{bold}"

    def test_allows_inline_math_with_whitelisted_commands(self):
        # \frac and \sqrt are math commands, OK inside $...$
        assert (
            sanitize_latex_basic(r"$\frac{1}{2}$")
            == r"$\frac{1}{2}$"
        )

    def test_rejects_display_math(self):
        with pytest.raises(SanitizeError):
            sanitize_latex_basic(r"$$x^2$$")

    def test_rejects_itemize(self):
        with pytest.raises(SanitizeError):
            sanitize_latex_basic(r"\begin{itemize}\item a\end{itemize}")

    def test_rejects_input_in_math(self):
        with pytest.raises(SanitizeError):
            sanitize_latex_basic(r"$x \input{y}$")

    def test_rejects_verb(self):
        with pytest.raises(SanitizeError):
            sanitize_latex_basic(r"\verb|x|")


# --- sanitize_latex_extended (title / instructions) ---------------------

class TestSanitizeExtended:
    def test_allows_display_math_dollars(self):
        assert sanitize_latex_extended(r"$$x^2$$") == r"$$x^2$$"

    def test_allows_display_math_brackets(self):
        assert sanitize_latex_extended(r"\[x^2\]") == r"\[x^2\]"

    def test_allows_itemize(self):
        src = r"\begin{itemize}\item first\item second\end{itemize}"
        assert sanitize_latex_extended(src) == src

    def test_allows_enumerate_with_options(self):
        src = r"\begin{enumerate}[label=\alph*)]\item a\item b\end{enumerate}"
        assert sanitize_latex_extended(src) == src

    def test_allows_uline(self):
        assert sanitize_latex_extended(r"\uline{u}") == r"\uline{u}"

    def test_forbids_input_at_extended(self):
        with pytest.raises(SanitizeError):
            sanitize_latex_extended(r"\input{evil}")

    def test_forbids_unknown_env(self):
        with pytest.raises(SanitizeError):
            sanitize_latex_extended(r"\begin{tabular}foo\end{tabular}")
