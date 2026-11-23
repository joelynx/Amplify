r"""mhchem markup in imported chemistry text (owner 2026-11-23: "let the app learn to render mhchem markup").

\ce{...} stays as it is: the PDF preamble loads mhchem and the web view KaTeX's mhchem extension (a \ce in
prose is put in math by the web sanitizer). \pu{...} exists only in the KaTeX/MathJax port, not in LaTeX's
mhchem, so importers rewrite it with pu_to_latex: \pu{1.5e-3 mol L-1} -> $1.5\times 10^{-3}\ \mathrm{mol\,L^{-1}}$
(inside math, without the dollars)."""

from __future__ import annotations

import re

_NUM = re.compile(r"""\s*(?P<num>[+\-\u2212]?\s*(?:\d+(?:[.,]\d*)?|[.,]\d+)
                      (?:\s*[eE]\s*(?P<e>[+\-\u2212]?\d+)
                        |\s*(?:\\times|\\cdot|\*|\u00d7|\u22c5)\s*10\s*\^\s*\{?\s*(?P<p>[+\-\u2212]?\d+)\s*\}?)?)?
                      \s*(?P<units>.*)$""", re.X | re.S)
_UNIT = re.compile(r"(?P<name>[^\s\d^+\-\u2212*./()]+)\s*\^?\s*\{?(?P<exp>[+\-\u2212]?\d+(?:/\d+)?)?\}?")
_GREEK = {"\u03bc": r"\mu ", "\u00b5": r"\mu ", "\u03a9": r"\Omega ", "\u00b0": r"{}^{\circ}", "\u212b": r"\text{\AA}",
          "\u00c5": r"\text{\AA}"}


def _units(s: str) -> str:
    out, i = [], 0
    s = s.strip()
    while i < len(s):
        ch = s[i]
        if ch in " *.\u22c5\u00b7":
            i += 1
            continue
        if ch in "/()":
            out.append(ch)
            i += 1
            continue
        m = _UNIT.match(s, i)
        if not m or m.end() == i:
            out.append(re.escape(ch) if ch in "#%&_" else ch)
            i += 1
            continue
        name = "".join(_GREEK.get(c, c) for c in m.group("name"))
        name = name.replace("%", r"\%")
        exp = (m.group("exp") or "").replace("\u2212", "-")
        out.append(name.strip() + (f"^{{{exp}}}" if exp else ""))
        i = m.end()
    joined = ""
    for tok in out:
        if joined and tok not in "/)" and not joined.endswith(("/", "(")):
            joined += r"\,"
        joined += tok
    return joined


def pu_body(body: str) -> str:
    """The math-mode LaTeX for the argument of one \\pu."""
    m = _NUM.match(body)
    num, units = (m.group("num") or "").replace(" ", "").replace("\u2212", "-"), m.group("units")
    exp = m.group("e") or m.group("p")
    if exp:
        num = re.split(r"[eE]|\\times|\\cdot|\*|\u00d7|\u22c5", num)[0]
        num = rf"{num}\times 10^{{{exp.replace(chr(0x2212), '-')}}}"
    num = num.replace(",", "{,}") if re.fullmatch(r"[+\-]?\d+,\d+", num or "") else num
    u = _units(units) if units.strip() else ""
    if num and u:
        return rf"{num}\ \mathrm{{{u}}}"
    return num or rf"\mathrm{{{u}}}"


def _groups(text: str, cmd: str):
    """(start, end, body) of each \\cmd{...} with balanced braces."""
    for m in re.finditer(rf"\\{cmd}\s*\{{", text):
        depth, j = 1, m.end()
        while j < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        if depth == 0:
            yield m.start(), j, text[m.end(): j - 1]


def _in_math(text: str, pos: int) -> bool:
    """Whether pos lies inside $...$, \\(...\\) or \\[...\\] (a simple left-to-right scan)."""
    math, i = False, 0
    while i < pos:
        if text.startswith("\\$", i):
            i += 2
            continue
        if text.startswith(("\\(", "\\["), i):
            math = True
            i += 2
            continue
        if text.startswith(("\\)", "\\]"), i):
            math = False
            i += 2
            continue
        if text[i] == "$":
            math = not math
            if text.startswith("$$", i):
                i += 1
        i += 1
    return math


def pu_to_latex(text: str | None) -> str | None:
    """Rewrite every \\pu{...} in text as plain LaTeX (in $...$ when it stood in prose)."""
    if not text or "\\pu" not in text:
        return text
    out, last = [], 0
    for a, b, body in _groups(text, "pu"):
        tex = pu_body(body)
        out.append(text[last:a])
        out.append(tex if _in_math(text, a) else f"${tex}$")
        last = b
    out.append(text[last:])
    return "".join(out)
