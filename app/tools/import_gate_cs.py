"""
Import the GATE CSE question bank
---------------------------------
github.com/cherie-dips/GATE-CS (no licence file; personal study use), file app/public/data/questions.json:
3,692 questions of the GATE CSE papers 1987-2026 and the GATE IT papers 2004-2008, built from ExamSIDE
(HTML with MathJax \\( \\), ids es_*) and the GATE Overflow book (Markdown with $ $, transcribed from page
scans, ids go_*). Owner decisions of 2026-11-25 (taken by the coordinator while the owner slept):

  * Source "GATE Computer Science and Information Technology"; subsource "<year>, Set <n>" for papers with
    sets, "<year>, IT paper" for the IT papers, else "<year>". The GATE question number and the repo's id go
    to benchmarks_map.csv (number, original_source).
  * Every subject is kept except verbal (English) aptitude, software engineering and web technologies.
  * Keys: kept only when they did not come from the model: official IIT keys (2022-26) and the repo's other
    answer keys (verdicts agree, keys-resolved, keys_conflict, disagree, ambiguous). Rows whose only answer is
    the model's (verdict nokey, and key-corrected unless an official key backs it) are imported with no
    answer, so the solver answers them fresh. "Marks to all" questions are dropped. Per-row decisions from
    the repo's notes are in gate_cs_fixes.json (dropped, no_answer, keep_key).
  * MCQ: one letter, "Exactly one option is correct."; MSQ: letters "A, C", "One or more options may be
    correct."; NAT: the number, or "a to b" for an accepted range; TF: "True"/"False"; descriptive and
    fill-in rows keep the repo's short reference answer.
  * The repo's explanations were written by a model: kept in ref_solution only, never stored as solution.
  * Figures: <img> tags become \\includegraphics of PNG files named gate-<sha1[:16]>. The repo's JPEG, WebP
    and SVG figures need PNG copies in <data>/png/<same path>.png (made by the import scratch script
    to_png.py: Pillow for JPEG/WebP, headless Edge for SVG); a row whose figure is missing is dropped.
  * Linked questions ("the previous question") are dropped; so are near-duplicates within the bank (85% of
    5-word shingles) and rows the Amplify bank already has.

Conversions: MathJax \\( \\) to $ $; HTML paragraphs and line breaks to paragraphs; <b>/<i>/<u> to \\textbf,
\\textit, \\underline; <sub>/<sup> to math; tables (HTML and Markdown pipe tables) to a bordered tabular;
code (<pre>, ``` fences) to verbatim, inline code to \\texttt; Markdown bold, italics and bullet lists;
entities decoded; LaTeX specials escaped in text; unicode math symbols to commands.

Usage (repo root):
  python -m app.tools.import_gate_cs --data DIR --dry-run [--dump rows.json] [--set-aside] [--exclude bad.json]
  python -m app.tools.import_gate_cs --data DIR --apply
DIR holds data/questions.json, img/ (the repo's app/public/img) and png/ (the PNG copies).
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import html
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import GRAPHIC, NEAR, TEXIMAGES, duplicates, shingles
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "GATE CS"
SOURCE = "GATE Computer Science and Information Technology"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/gate_cs_set_aside.json")  # git-ignored
PREFIX = "gate"

_FIX = json.loads(Path(__file__).with_name("gate_cs_fixes.json").read_text(encoding="utf-8"))
FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIX["fixes"]:
    FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPPED: dict[str, str] = dict(_FIX["dropped"])
NO_ANSWER: dict[str, str] = dict(_FIX["no_answer"])
KEEP_KEY: dict[str, str] = dict(_FIX["keep_key"])

SKIP_SUBJECTS = {"se": "software engineering: outside the owner's subject list",
                 "web": "web technologies: outside the owner's subject list"}
LINKED_RE = re.compile(r"previous question|above question|earlier question", re.I)
SUBJECT_OF: dict[str, str] = {}  # repo id -> the repo's subject id (for the counts)

# ------------------------------------------------------------------------------------------- symbols
SYMBOLS = {
    "→": r"\rightarrow", "←": r"\leftarrow", "↑": r"\uparrow", "↓": r"\downarrow", "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow", "⇔": r"\Leftrightarrow", "⟹": r"\implies", "×": r"\times", "÷": r"\div", "−": "-",
    "∈": r"\in", "∉": r"\notin", "∧": r"\land", "∨": r"\lor", "¬": r"\neg", "⋀": r"\bigwedge", "≠": r"\neq",
    "≤": r"\leq", "≥": r"\geq", "≈": r"\approx", "≡": r"\equiv", "≼": r"\preccurlyeq", "∪": r"\cup",
    "∩": r"\cap", "⊆": r"\subseteq", "⊂": r"\subset", "⊇": r"\supseteq", "⊃": r"\supset", "∃": r"\exists",
    "∀": r"\forall", "∅": r"\emptyset", "∞": r"\infty", "⊕": r"\oplus", "⊗": r"\otimes", "⋈": r"\bowtie",
    "⊨": r"\models", "⟂": r"\perp", "⊥": r"\perp", "•": r"\bullet", "●": r"\bullet", "∙": r"\cdot",
    "⋅": r"\cdot", "·": r"\cdot", "∘": r"\circ", "□": r"\square", "◻": r"\square", "▢": r"\square",
    "⌈": r"\lceil", "⌉": r"\rceil", "⌊": r"\lfloor", "⌋": r"\rfloor", "〈": r"\langle", "〉": r"\rangle",
    "∑": r"\sum", "∏": r"\prod", "∫": r"\int", "√": r"\surd", "‖": r"\|", "±": r"\pm", "∼": r"\sim",
    "ℝ": r"\mathbb{R}", "𝐹": "F", "²": "^{2}", "³": "^{3}", "₀": "_{0}", "₁": "_{1}", "₂": "_{2}",
    "∗": "*", "│": "|",
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta", "ε": r"\varepsilon", "ϵ": r"\epsilon",
    "θ": r"\theta", "λ": r"\lambda", "μ": r"\mu", "π": r"\pi", "ρ": r"\rho", "σ": r"\sigma", "τ": r"\tau",
    "φ": r"\phi", "ϕ": r"\phi", "ω": r"\omega", "Γ": r"\Gamma", "Δ": r"\Delta", "Θ": r"\Theta",
    "Π": r"\Pi", "П": r"\Pi", "Σ": r"\Sigma", "Φ": r"\Phi", "Ω": r"\Omega",
}
TEXT_TYPO = {"–": "--", "—": "---", "’": "'", "‘": "`", "“": "``", "”": "''", "…": r"\ldots{}", "\xa0": " ",
             "\u2003": " ", "\u2002": " ", "\u2009": " ", "\xad": "", "\u200b": "", "₹": "Rs.",
             "®": r"\textregistered{}", "Ⅰ": "I", "Ⅱ": "II"}
MATH_TYPO = {"–": "-", "—": "-", "’": "'", "‘": "'", "“": "``", "”": "''", "…": r"\ldots ", "\xa0": " ",
             "\u2003": " ", "\u2002": " ", "\u2009": " ", "\xad": "", "\u200b": "", "₹": r"\text{Rs.}"}
CODE_ASCII = {"→": "->", "←": "<-", "–": "-", "—": "-", "−": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
              "≠": "!=", "≤": "<=", "≥": ">=", "×": "*", "\xa0": " ", "…": "...", "\u200b": "", "\t": "    "}
SYM_RE = re.compile("[" + re.escape("".join(SYMBOLS)) + "]")
# the HTML tags the repo uses; anything else in angle brackets is text ("#include <stdio.h>", "i<n")
TAG_RE = re.compile(r"<(/?)(p|br|div|span|b|i|u|em|strong|sub|sup|table|tr|td|th|tbody|thead|img|pre|code|li|ul"
                    r"|ol|picture|source|col|colgroup|font|center|hr)\b[^>$]*>", re.I)


def fix_math(m: str) -> str:
    """One math run as LaTeX for both renderers."""
    m = re.sub(r"<br\s*/?>", " ", m)
    m = re.sub(r"</?(?:span|b|i|em|strong|u)\b[^>]*>", "", m)
    m = html.unescape(m)
    m = re.sub(r"(\w)\u0305", r"\\overline{\1}", m)
    for k, v in MATH_TYPO.items():
        m = m.replace(k, v)
    m = SYM_RE.sub(lambda x: SYMBOLS[x.group(0)] + " ", m)
    m = re.sub(r"\\lt(?![A-Za-z])", "<", m)
    m = re.sub(r"\\gt(?![A-Za-z])", ">", m)
    m = re.sub(r"\\textdollar(?![A-Za-z])", r"\\$", m)
    m = re.sub(r"(?<!\\)([%#])", r"\\\1", m)
    m = re.sub(r"\^\s*'", "'", m)  # x^' (a complement): KaTeX wants a group after ^
    m = re.sub(r"\\text\s*\{([^{}]*)\}", lambda x: r"\text{" + re.sub(r"(?<!\\)_", r"\\_", x.group(1)) + "}", m)
    m = re.sub(r"\n\s*\n", "\n", m)
    return m.strip()


def esc(t: str) -> str:
    """Plain text with LaTeX's special characters escaped and unicode symbols in math."""
    t = t.replace("\\", "\x03")
    for c in "{}%&#_$":
        t = t.replace(c, "\\" + c)
    t = t.replace("\x03", r"\textbackslash{}").replace("^", r"\textasciicircum{}").replace("~", r"\textasciitilde{}")
    t = re.sub(r"(\w)\u0305", r"$\\overline{\1}$", t)
    for k, v in TEXT_TYPO.items():
        t = t.replace(k, v)
    t = t.replace("<=", "$\\leq$").replace(">=", "$\\geq$").replace("<", "$<$").replace(">", "$>$")
    return SYM_RE.sub(lambda x: "$" + SYMBOLS[x.group(0)] + "$", t)


def code_text(t: str) -> str:
    for k, v in CODE_ASCII.items():
        t = t.replace(k, v)
    return t


class Doc:
    """Placeholders for finished LaTeX (math, code, tables, figures) inside text still to be escaped."""

    def __init__(self, images: list | None, data: Path | None):
        self.store: list[tuple[str, str]] = []
        self.images = images
        self.data = data

    def put(self, latex: str, kind: str = "x") -> str:
        self.store.append((kind, latex))
        return f"\x00{len(self.store) - 1}\x00"

    def math(self, body: str) -> str:
        body = fix_math(body)
        return self.put(body, "m") if body else ""

    def display(self, body: str) -> str:
        body = fix_math(body)
        return self.put("\n\n\\[" + body + "\\]\n\n") if body else ""

    def verbatim(self, code: str) -> str:
        code = code_text(code).strip("\n")
        code = "\n".join(ln.rstrip() for ln in code.split("\n"))
        if not code.strip():
            return ""
        depth = 0
        for c in code:
            depth += {"{": 1, "}": -1}.get(c, 0)
            if depth < 0:
                break
        if depth or code.count("$") % 2:  # the bank's text check counts these in verbatim too: lines of \texttt
            return self.put("\n\n" + "\n\n".join(self.texttt(ln) for ln in code.split("\n") if ln.strip()) + "\n\n")
        return self.put("\n\n\\begin{verbatim}\n" + code + "\n\\end{verbatim}\n\n")

    def texttt(self, code: str) -> str:
        code = code_text(code).strip()
        t = code.replace("\\", "\x03")
        for c in "{}%&#_$":
            t = t.replace(c, "\\" + c)
        t = t.replace("\x03", r"\textbackslash{}").replace("^", r"\textasciicircum{}").replace("~", r"\textasciitilde{}")
        t = re.sub(r"[^\x00-\x7f]", lambda x: SYMBOLS.get(x.group(0), x.group(0)), t)
        return self.put(r"\texttt{" + t + "}")

    def image(self, src: str) -> str:
        if self.images is None:
            return self.put("[figure]")
        rel = Path(src)
        path = self.data / rel
        if rel.suffix.lower() != ".png":
            path = self.data / "png" / Path(*rel.parts[1:]).with_suffix(".png") if rel.parts[0] == "img" else None
        if path is None or not path.exists():
            raise ValueError(f"figure missing ({src})")
        png = path.read_bytes()
        name = f"{PREFIX}-{hashlib.sha1(png).hexdigest()[:16]}"
        self.images.append((name, path))
        return self.put("\n\n" + GRAPHIC.format(name) + "\n\n")

    def restore(self, s: str) -> str:
        def one(m: re.Match) -> str:
            kind, latex = self.store[int(m.group(1))]
            return "$" + latex + "$" if kind == "m" else latex

        for _ in range(6):  # tokens inside tables and the like come back on the next pass
            s = re.sub(r"\x00(\d+)\x00", one, s)
            if "\x00" not in s:
                break
        return s


BOLD_O, BOLD_C, IT_O, IT_C, UL_O, UL_C = "\x01", "\x02", "\x04", "\x05", "\x06", "\x07"
PAIRS = {BOLD_O: (BOLD_C, r"\textbf{"), IT_O: (IT_C, r"\textit{"), UL_O: (UL_C, r"\underline{")}


def protect_verbatim(s: str) -> tuple[str, list[str]]:
    """Verbatim bodies out of the way of the clean-up in finish()."""
    keep: list[str] = []

    def put(m: re.Match) -> str:
        keep.append(m.group(0))
        return f"\x08{len(keep) - 1}\x08"
    return re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", put, s, flags=re.S), keep


def finish(s: str, doc: Doc) -> str:
    s, keep = protect_verbatim(doc.restore(s))
    s = re.sub(r"(?<!\\)\$\$(?=[\^_])", "{}", s)  # two inline maths side by side are one (no double ^)
    s = re.sub(r"(?<!\\)\$\$", " ", s)
    for o, (c, cmd) in PAIRS.items():  # an emphasis may not run over a paragraph break or a display
        s = re.sub(re.escape(o) + "(.*?)" + re.escape(c),
                   lambda m, o=o, c=c: o + re.sub(r"\s*(\n\s*\n|\\\[|\\\])\s*", lambda x: c + x.group(0) + o,
                                                  m.group(1)) + c, s, flags=re.S)
        s = s.replace(o, cmd).replace(c, "}")
    s = re.sub(r"\\(?:textbf|textit|underline)\{\s*\}", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\x08(\d+)\x08", lambda m: keep[int(m.group(1))], s)
    return s.strip()


def tabular(rows: list[list[tuple[str, int]]]) -> str:
    """Rows of (cell LaTeX, colspan) as a bordered tabular."""
    width = max(sum(span for _, span in r) for r in rows)
    lines = []
    for r in rows:
        cells = [c if span == 1 else rf"\multicolumn{{{span}}}{{|c|}}{{{c}}}" for c, span in r]
        cells += [""] * (width - sum(span for _, span in r))
        lines.append(" & ".join(cells) + r" \\ \hline")
    return ("\n\n\\begin{center}\n\\begin{tabular}{|" + "c|" * width + "}\n\\hline\n" + "\n".join(lines)
            + "\n\\end{tabular}\n\\end{center}\n\n")


# ---------------------------------------------------------------------------------------------- HTML
INLINE_TAGS = {"b": (BOLD_O, BOLD_C), "strong": (BOLD_O, BOLD_C), "i": (IT_O, IT_C), "em": (IT_O, IT_C),
               "u": (UL_O, UL_C)}


def subsup(kind: str, inner: str, doc: Doc) -> str:
    inner = re.sub(r"<(sub|sup)\b[^>]*>(.*?)</\1>", lambda m: r"\(" + ("_" if m.group(1) == "sub" else "^")
                   + "{" + TAG_RE.sub("", m.group(2)) + r"}\)", inner, flags=re.S)  # nested: log<sub>b</sub>
    inner = TAG_RE.sub("", inner)
    parts = re.split(r"\\\((.*?)\\\)", inner, flags=re.S)
    out = []
    for k, p in enumerate(parts):
        if k % 2:
            out.append(fix_math(p))
        elif p.strip():
            p = html.unescape(p).strip()
            if re.fullmatch(r"[\d.+\-*/=,() ]+|[A-Za-z]", p):
                out.append(p)
                continue
            for j, w in enumerate(re.split("([<>]|" + SYM_RE.pattern + ")", p)):  # symbols in math, words in \text
                if j % 2:
                    out.append(SYMBOLS.get(w, w))
                elif w.strip():
                    w = w.replace("\\", "\x03")
                    for c in "{}%&#_$":
                        w = w.replace(c, "\\" + c)
                    for a, b in TEXT_TYPO.items():
                        w = w.replace(a, b)
                    out.append(r"\text{" + w.replace("\x03", r"\textbackslash{}") + "}")
    body = " ".join(out).strip()
    return doc.put(("_" if kind == "sub" else "^") + "{" + body + "}", "m") if body else ""


def html_inline(s: str, doc: Doc) -> str:
    """HTML (no tables or code blocks left) to text with placeholders, not yet finished."""
    s = re.sub(r"<(sub|sup)\b[^>]*>(.*?)</\1>", lambda m: subsup(m.group(1), m.group(2), doc), s, flags=re.S)
    s = re.sub(r"<code\b[^>]*>(.*?)</code>", lambda m: doc.texttt(html.unescape(TAG_RE.sub("", m.group(1)))),
               s, flags=re.S)
    s = re.sub(r"<img\b[^>]*?src=\"([^\"]+)\"[^>]*>", lambda m: doc.image(m.group(1)), s)
    s = re.sub(r"\\\[(.*?)\\\]", lambda m: doc.display(m.group(1)), s, flags=re.S)
    s = re.sub(r"\\\((.*?)\\\)", lambda m: doc.math(m.group(1)), s, flags=re.S)
    s = s.replace("\n", " ")
    s = re.sub(r"<(?:/?p|/?div|br|/?ul|/?ol|/li|/?tbody|/?thead|/?center)\b[^>]*>", "\n\n", s, flags=re.I)
    s = re.sub(r"<li\b[^>]*>", "\n\n" + doc.put(r"$\bullet$") + " ", s)

    def tag(m: re.Match) -> str:
        name = m.group(2).lower()
        if name in INLINE_TAGS:
            return INLINE_TAGS[name][1 if m.group(1) else 0]
        return ""
    s = TAG_RE.sub(tag, s)
    parts = re.split(r"(\x00\d+\x00)", s)
    return "".join(p if k % 2 else esc(html.unescape(p)) for k, p in enumerate(parts))


def html_table(t: str, doc: Doc) -> str:
    rows = []
    for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", t, flags=re.S | re.I):
        cells = []
        for m in re.finditer(r"<(t[dh])\b([^>]*)>(.*?)</t[dh]>", tr, flags=re.S | re.I):
            span = re.search(r"colspan=\"?(\d+)", m.group(2))
            body = html_inline(m.group(3), doc)
            body = re.sub(r"\s*\n\s*", " ", body).strip()
            if m.group(1).lower() == "th" and body:
                body = BOLD_O + body + BOLD_C
            cells.append((body, int(span.group(1)) if span else 1))
        if cells:
            rows.append(cells)
    if not rows:
        raise ValueError("empty table")
    return doc.put(tabular(rows))


def html_to_latex(s: str, doc: Doc) -> str:
    s = re.sub(r"</?(?:picture|colgroup|span|font)\b[^>]*>|<(?:source|col)\b[^>]*>", "", s, flags=re.I)

    def pre(m: re.Match) -> str:
        body = re.sub(r"<br\s*/?>", "\n", m.group(1))
        body = html.unescape(TAG_RE.sub("", body))
        if "\\(" in body or "\\[" in body:  # pseudo-code with math: lines of text
            return "\n\n".join(html_inline(ln, doc) for ln in body.split("\n") if ln.strip())
        return doc.verbatim(body)
    s = re.sub(r"<pre\b[^>]*>(.*?)</pre>", pre, s, flags=re.S | re.I)
    s = re.sub(r"<table\b.*?</table>", lambda m: html_table(m.group(0), doc), s, flags=re.S | re.I)
    return html_inline(s, doc)


# ------------------------------------------------------------------------------------------ Markdown
MD_ESC_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|$<>])")


def md_text(t: str, doc: Doc) -> str:
    """A Markdown text run (no math or code): emphasis, HTML bits, markdown escapes, LaTeX specials."""
    t = re.sub(r"<(sub|sup)\b[^>]*>(.*?)</\1>", lambda m: subsup(m.group(1), m.group(2), doc), t, flags=re.S)
    t = re.sub(r"<u>(.*?)</u>", UL_O + r"\1" + UL_C, t, flags=re.S)
    t = re.sub(r"<br\s*/?>", "\n\n", t)
    t = re.sub(r"\*\*(.+?)\*\*", BOLD_O + r"\1" + BOLD_C, t, flags=re.S)
    t = re.sub(r"(?<![*\w\\])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![*\w])", IT_O + r"\1" + IT_C, t)
    t = re.sub(r"\\([A-Za-z]+)", lambda m: doc.math("\\" + m.group(1)), t)  # a stray command outside $ $
    parts = re.split(r"(\x00\d+\x00|\\[\\`*_{}\[\]()#+\-.!|$<>])", t)
    out = []
    for k, p in enumerate(parts):
        if k % 2:
            out.append(p if p.startswith("\x00") else esc(p[1]))
        else:
            out.append(esc(html.unescape(p)))
    return "".join(out)


def md_table(block: list[str], doc: Doc) -> str:
    rows = []
    for ln in block:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", ln.strip().strip("|"))]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and any(cells):
            continue
        rows.append([(md_text(c, doc), 1) for c in cells])
    return doc.put(tabular(rows))


def md_to_latex(s: str, doc: Doc) -> str:
    s = s.replace("\r\n", "\n")
    s = re.sub(r"```[^\n]*\n(.*?)```", lambda m: doc.verbatim(m.group(1)), s, flags=re.S)
    s = re.sub(r"`([^`\n]+)`", lambda m: doc.texttt(m.group(1)), s)
    s = re.sub(r"\$\$(.+?)\$\$", lambda m: doc.display(m.group(1)), s, flags=re.S)
    s = re.sub(r"\\\[(.+?)\\\]", lambda m: doc.display(m.group(1)), s, flags=re.S)
    s = re.sub(r"(?<!\\)\$(.+?)(?<!\\)\$", lambda m: doc.math(m.group(1)), s, flags=re.S)
    s = re.sub(r"\\\((.+?)\\\)", lambda m: doc.math(m.group(1)), s, flags=re.S)
    out, block, items = [], [], []

    def flush() -> None:
        if block:
            out.append(md_table(block, doc))
            block.clear()
        if items:
            out.append("\n\\begin{itemize}\n" + "\n".join(r"\item " + md_text(x, doc) for x in items)
                       + "\n\\end{itemize}\n")
            items.clear()

    for ln in s.split("\n"):
        if ln.strip().startswith("|") and ln.strip().endswith("|"):
            if items:
                flush()
            block.append(ln)
            continue
        m = re.match(r"^\s*[-*+]\s+(.*)$", ln)
        if m:
            if block:
                flush()
            items.append(m.group(1))
            continue
        flush()
        if re.match(r"^\s*(?:\d+|[ivx]+|[a-z])[.)]\s", ln):  # a numbered line stays on its own line
            out.append("")
        out.append(md_text(ln, doc))
    flush()
    return "\n".join(out)


def convert(s: str, fmt: str, doc: Doc) -> str:
    return finish(html_to_latex(s, doc) if fmt == "html" else md_to_latex(s, doc), doc)


# ------------------------------------------------------------------------------------------- answers
def num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def answer_text(q: dict) -> str | None:
    a, t = q["a"], q["t"]
    if "opts" in a:
        if t == "TF":
            return q["o"][a["opts"][0]].strip().capitalize()
        return ", ".join(chr(65 + i) for i in sorted(a["opts"]))
    if "lo" in a:
        vals = [(a["lo"], a["hi"])] + [tuple(x) for x in a.get("alt", [])]
        off = q.get("official") or ""
        out = []
        for k, (lo, hi) in enumerate(vals):
            if lo == hi:
                out.append(num(lo))
                continue
            m = re.fullmatch(r"(-?[\d.]+) to (-?[\d.]+)", off.strip()) if k == 0 else None
            out.append(f"{m.group(1)} to {m.group(2)}" if m and float(m.group(1)) == lo and float(m.group(2)) == hi
                       else f"{num(lo)} to {num(hi)}")
        return " or ".join(out)
    if "text" in a:
        doc = Doc(None, None)
        return convert(a["text"], "md", doc)
    return None


def subsource(q: dict) -> str:
    if q["ex"] == "IT":
        return f"{q['y']}, IT paper"
    return f"{q['y']}, Set {q['set']}" if q.get("set") else str(q["y"])


# ---------------------------------------------------------------------------------------------- load
def load(data: Path) -> tuple[list[dict], dict[str, str], dict[str, str]]:
    """(rows, {id: why left out}, {id: why imported without an answer})."""
    qs = json.loads((data / "data" / "questions.json").read_text(encoding="utf-8"))["questions"]
    rows, left, unanswered = [], {}, {}
    for q in qs:
        key = q["id"]
        SUBJECT_OF[key] = q["s"]
        if q["s"] in SKIP_SUBJECTS:
            left[key] = SKIP_SUBJECTS[q["s"]]
            continue
        if q["s"] == "ga" and q["c"] == "verbal-ability":
            left[key] = "verbal (English) aptitude"
            continue
        if key in DROPPED:
            left[key] = DROPPED[key]
            continue
        if "mta" in q["a"] or (q.get("official") or "").upper() == "MTA":
            left[key] = "marks to all: no option is correct as printed"
            continue
        if LINKED_RE.search(q["q"]):
            left[key] = "linked question: depends on another question that is not included"
            continue
        images: list = []
        doc = Doc(images, data)
        try:
            stem = convert(q["q"], q["qf"], doc)
            opts = [convert(o, q["of"], doc) for o in q.get("o") or []] if q["t"] != "TF" else []
        except ValueError as e:
            left[key] = str(e)
            continue
        parts = [stem]
        if opts:
            low = stem.lower()
            said = r"(?:exactly one|only one|one or more|more than one) (?:of the )?(?:options?|answers?|choices?)"
            if q["t"] == "MCQ" and not re.search(said, low):
                parts.append("Exactly one option is correct.")
            elif q["t"] == "MSQ" and not re.search(said, low):
                parts.append("One or more options may be correct.")
            parts += [f"({chr(65 + i)}) {o}" for i, o in enumerate(opts)]
        tex = "\n\n".join(p for p in parts if p)
        ans = answer_text(q)
        if q["v"] == "nokey":
            unanswered[key] = "nokey: the only answer is the model's"
        elif q["v"] == "key-corrected" and not q.get("official") and key not in KEEP_KEY:
            unanswered[key] = "key-corrected: the model overrode the source key"
        elif key in NO_ANSWER:
            unanswered[key] = NO_ANSWER[key]
        if key in unanswered:
            ans = None
        ref = q.get("e") or ""
        try:
            ref = convert(ref, "md", Doc(None, None)) if ref else ""
        except ValueError:
            pass
        if q.get("note"):
            ref = (ref + "\n\n" if ref else "") + "Note (from the dataset): " + q["note"]
        row = {"potd": f"{SET} {key}", "set": SET, "idx": key, "orig": key, "number": str(q.get("n") or ""),
               "source": SOURCE, "subsource": subsource(q), "latexcode": tex, "answer": ans, "solution": None,
               "hints": None, "more_hints": None, "ref_solution": ref, "group": "subject", "effort": None,
               "image": images or None, "gate_subject": q["s"], "gate_type": q["t"]}
        for fld in ("latexcode", "answer"):
            for old, new in FIXES.get((key, fld), []):
                if not row[fld] or row[fld].count(old) != 1:
                    raise SystemExit(f"FIX {key} {fld}: expected one {old!r}")
                row[fld] = row[fld].replace(old, new)
        rows.append(row)
    return dedupe(rows, left), left, unanswered


def dedupe(rows: list[dict], left: dict[str, str]) -> list[dict]:
    """Near-duplicates within the bank: the copy with a key (then the ExamSIDE one) stays."""
    order = sorted(range(len(rows)), key=lambda k: (rows[k]["answer"] is None, not rows[k]["idx"].startswith("es_"), k))
    index: dict[str, set[int]] = collections.defaultdict(set)
    gone = set()
    for k in order:
        g = shingles(rows[k]["latexcode"])
        hits = collections.Counter(j for x in g for j in index.get(x, ()))
        if hits:
            j, n = hits.most_common(1)[0]
            a, b = rows[k], rows[j]
            same = (n / len(g) >= NEAR and n / len(shingles(b["latexcode"])) >= NEAR
                    and "".join(re.findall(r"\d", a["latexcode"])) == "".join(re.findall(r"\d", b["latexcode"]))
                    and (a["answer"] is None or b["answer"] is None or a["answer"] == b["answer"]))
            if same:  # linked pairs ("h_1" / "h_2") and changed numbers are different questions
                left[rows[k]["idx"]] = f"same question as {rows[j]['idx']}"
                gone.add(k)
                continue
        for x in g:
            index[x].add(k)
    return [r for k, r in enumerate(rows) if k not in gone]


# ---------------------------------------------------------------------------------------------- main
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON (images as names)")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, left, unanswered = load(a.data)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new)
    leftover = re.compile(TAG_RE.pattern + r"|(?<!\\)&[a-z]+;|```|[\x00-\x08]", re.I)
    for r in new:
        for fld in ("latexcode", "answer"):
            body = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", "", r[fld] or "", flags=re.S)
            if m := leftover.search(body):
                problems.append(f"{r['potd']} {fld}: markup left over {m.group(0)!r}")
            if m := SYM_RE.search(body):
                problems.append(f"{r['potd']} {fld}: unicode symbol {m.group(0)!r}")
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: [x for x in problems if x.startswith(r["potd"] + " ") or x.startswith(r["potd"] + ":")]
               or [excluded[r["potd"]]] for r in new
               if any(x.startswith(r["potd"] + " ") or x.startswith(r["potd"] + ":") for x in problems)
               or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([{k: v for k, v in dict(r, problems=why[r["potd"]]).items() if k != "image"}
                                              for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
                                  encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = []
    reasons = collections.Counter(re.sub(r"\(.*|as [ge]\w+_\S+", "", v).strip() for v in left.values())
    print(json.dumps({
        "rows": len(rows) + len(left), "left_out": len(left), "left_out_by_reason": reasons, "in_bank": len(dup),
        "to_add": len(new), "check_problems": len(problems),
        "without_answer": sum(r["answer"] is None for r in new),
        "without_answer_by_reason": collections.Counter(unanswered[r["idx"]].split(":")[0] for r in new
                                                        if r["answer"] is None),
        "with_images": sum(bool(r["image"]) for r in new), "images": sum(len(r["image"] or []) for r in new),
        "by_type": collections.Counter(r["gate_type"] for r in new),
        "kept_by_subject": collections.Counter(r["gate_subject"] for r in new),
        "left_by_subject": collections.Counter(SUBJECT_OF[k] for k in left),
        "in_bank_by_subject": collections.Counter(rows[k]["gate_subject"] for k in dup),
    }, ensure_ascii=False, default=dict))
    if a.dump:
        a.dump.write_text(json.dumps([dict(r, image=[n for n, _ in r["image"]] if r["image"] else None) for r in new],
                                     ensure_ascii=False, indent=1), encoding="utf-8")
        a.dump.with_name(a.dump.stem + "_left.json").write_text(json.dumps(left, ensure_ascii=False, indent=1),
                                                                encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("gate-cs")
    for r in new:  # figures, before their questions exist
        for name, path in r["image"] or []:
            (TEXIMAGES / f"{name}.png").write_bytes(Path(path).read_bytes())
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in new:
            h = latex_hash(r["latexcode"])
            if h in existing:
                continue
            cur = conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, hints, more_hints, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"], r["answer"],
                 r["solution"], r["hints"], r["more_hints"], h),
            )
            existing.add(h)
            added.append((cur.lastrowid, r))
        conn.commit()
    finally:
        conn.close()
    with MAP_PATH.open("a" if MAP_PATH.exists() else "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["number"], r["orig"]) for q, r in added)
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
