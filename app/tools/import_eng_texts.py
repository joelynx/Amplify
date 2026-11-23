"""
Import three open engineering textbooks (wave of 2026-11-23)
--------------------------------------------------------------
Owner decision 2026-11-23: import every source that does not need the OCR tool; the app is private.

  ellingson   S. W. Ellingson, *Electromagnetics* Vol. 1 and Vol. 2 (Virginia Tech, CC BY-SA 4.0), from the
              book's LaTeX source zips (vtechworks.lib.vt.edu handles 10919/84164 and 10919/93253).  The
              source holds the worked examples (\\begin{example} ... {\\bf Solution.} ...) but NOT the
              end-of-section problem sets: those exist only as PDFs (Pblms/Solutions), which this importer
              does not read.  Each example with an explicit solution becomes question + solution.
  woolf       Woolf (ed.), *Chemical Process Dynamics and Controls* (LibreTexts Engineering, CC BY 3.0), HTML.
  verrett     Verrett et al., *Foundations of Chemical and Biological Engineering I* (UBC, CC BY-SA 4.0),
              Pressbooks HTML.

Rows go to group "subject" (the classifier decides the subject afterwards).  Source / subsource:
  "Ellingson, Electromagnetics" / "Vol. 1, Chapter 3" (the item number lives only in the map: idx)
  "Woolf, Chemical Process Dynamics and Controls" / "Chapter 9"
  "Verrett et al., Foundations of Chemical and Biological Engineering I" / "Chapter 21"

Data folder (--data DIR): DIR/ellingson/{v1,v2}/x/... (unzipped LaTeX sources), DIR/woolf/ and DIR/verrett/
(pages/<sha1[:16]>.html plus index.tsv "<hash>\\t<url>", written by `--fetch`, at most one request per second,
a page is never fetched twice).

Dropped rows: those that need a figure, a table or data that is not in the text, software (Excel, MATLAB,
Simulink, Python), or an earlier item's results; per-row decisions are in eng_texts_fixes.json.

Usage (repo root):
  python -m app.tools.import_eng_texts --data DIR --fetch woolf|verrett     (download the HTML into DIR)
  python -m app.tools.import_eng_texts --data DIR --dry-run [--only ellingson,woolf,verrett] [--dump rows.json]
  python -m app.tools.import_eng_texts --data DIR --apply
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
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from app.tools.chem_markup import pu_to_latex
from app.tools.import_answer_sets import duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
MIN_SOLUTION = 150
SET_ASIDE_PATH = Path("app/data/appdata/eng_texts_set_aside.json")
FIXES_PATH = Path(__file__).with_name("eng_texts_fixes.json")

BOOKS = {
    "ellingson": ("Ellingson", "Ellingson, Electromagnetics"),
    "woolf": ("Woolf", "Woolf, Chemical Process Dynamics and Controls"),
    "verrett": ("Verrett", "Verrett et al., Foundations of Chemical and Biological Engineering I"),
}


def load_fixes() -> dict:
    if FIXES_PATH.exists():
        return json.loads(FIXES_PATH.read_text(encoding="utf-8"))
    return {"fixes": [], "dropped": {}, "answers": {}}


# ---------------------------------------------------------------------------------------------
# shared text helpers
# ---------------------------------------------------------------------------------------------

MATH_RE = re.compile(
    r"(\\\[.*?\\\]|\$[^$]*\$|\\begin\{(?:align\*?|gather\*?|equation\*?)\}.*?\\end\{(?:align\*?|gather\*?|equation\*?)\})",
    re.S,
)


def map_text(text: str, f_text, f_math) -> str:
    """Apply f_text to the prose pieces and f_math to the math pieces of text."""
    text = text.replace("\\$", "\x00")
    parts = MATH_RE.split(text)
    for i, p in enumerate(parts):
        parts[i] = (f_math if i % 2 else f_text)(p)
    return "".join(parts).replace("\x00", "\\$")


def tidy_space(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def balanced(text: str, start: int) -> int:
    """Index just after the brace group that opens at text[start] == '{'; -1 if unbalanced."""
    depth = 0
    k = start
    while k < len(text):
        c = text[k]
        if c == "\\":
            k += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return -1


def unwrap(text: str, cmd: str, new: str | None) -> str:
    """Replace \\cmd{body} by new.format(body) (None: just body); balanced braces."""
    out, k = [], 0
    pat = re.compile(r"\\" + cmd + r"(?![A-Za-z])\s*\{")
    while True:
        m = pat.search(text, k)
        if not m:
            out.append(text[k:])
            break
        end = balanced(text, m.end() - 1)
        if end < 0:
            out.append(text[k:])
            break
        out.append(text[k : m.start()])
        body = text[m.end() : end - 1]
        out.append(body if new is None else new.replace("@", body))
        k = end
    return "".join(out)


def old_style(text: str, cmd: str, new: str) -> str:
    """{\\bf X} -> new with @ = X."""
    out, k = [], 0
    pat = re.compile(r"\{\s*\\" + cmd + r"(?![A-Za-z])\s*")
    while True:
        m = pat.search(text, k)
        if not m:
            out.append(text[k:])
            break
        end = balanced(text, m.start())
        if end < 0:
            out.append(text[k:])
            break
        out.append(text[k : m.start()])
        out.append(new.replace("@", text[m.end() : end - 1].strip()))
        k = end
    return "".join(out)


# ---------------------------------------------------------------------------------------------
# Ellingson (LaTeX source)
# ---------------------------------------------------------------------------------------------

ENV_RE = re.compile(r"\\begin\{(equation\*?|flalign\*?|eqnarray\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}", re.S)


def ell_env(m: re.Match) -> str:
    kind, body = m.group(1).rstrip("*"), m.group(2)
    body = body.replace("\\nonumber", "")
    body = re.sub(r"\\label\{[^}]*\}", "", body).strip()
    body = re.sub(r"\n\s*\n", "\n", body)
    if kind == "equation":
        return "\n\\[\n" + body + "\n\\]\n"
    body = body.replace("&=&", "&=")
    if "\\\\" not in body.strip().rstrip("\\"):
        return "\n\\[\n" + body.replace("&", "") + "\n\\]\n"
    return "\n\\begin{align*}\n" + body + "\n\\end{align*}\n"


ACCENT_RE = re.compile(r"\\(hat|widetilde|widehat|tilde|bar|vec)\s*\\mathbf(\{[^{}]*\})")


def ell_math(p: str) -> str:
    p = old_style(p, "bf", r"\mathbf{@}")
    p = old_style(p, "it", r"\mathit{@}")
    p = ACCENT_RE.sub(r"\\\1{\\mathbf\2}", p)
    p = re.sub(r"\\mathbf\{\\(phi|theta|rho|omega|alpha|beta|mu|epsilon|sigma|psi)\}", r"\\boldsymbol{\\\1}", p)
    p = p.replace("\\mbox", "\\text").replace("\\nonumber", "")
    p = re.sub(r"\\rm\b\s*", "", p)
    return p


def ell_text(p: str) -> str:
    p = old_style(p, "bf", r"\textbf{@}")
    p = old_style(p, "it", r"\textit{@}")
    p = unwrap(p, "mbox", None)
    p = unwrap(p, "noindent", None)
    p = re.sub(r"\\noindent\b\s*", "", p)
    p = re.sub(r"(?<!\\)%", r"\\%", p)
    p = re.sub(r"~?\\\\\s*~?\s*\\\\", "\n\n", p)  # "\\~\\" is a paragraph break
    p = re.sub(r"~?\\\\[ \t]*(?=\n|$)", "", p)
    p = re.sub(r"\\\\", " ", p)
    return p


def ell_clean(raw: str, titles: dict[str, str]) -> str:
    t = re.sub(r"(?m)(?<!\\)%.*$", "", raw)
    t = t.replace("\\begin{mdframed}[backgroundcolor=brown!20,linecolor=brown!20]\\raggedright", "")
    t = re.sub(r"\\begin\{mdframed\}(\[[^\]]*\])?", "", t).replace("\\end{mdframed}", "")
    t = t.replace("\\raggedright", "")
    t = re.sub(r"\s*\\index\{(?:[^{}]|\{[^{}]*\})*\}", "", t)
    t = re.sub(r"\s*\\label\{[^{}]*\}", "", t)
    t = re.sub(r"\$\$(.*?)\$\$", lambda m: "\n\\[\n" + m.group(1).strip() + "\n\\]\n", t, flags=re.S)
    t = ENV_RE.sub(ell_env, t)
    t = re.sub(r"\\hyperref\[[^\]]*\]\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\href\{[^{}]*\}\{([^{}]*)\}", r"\1", t)
    # (Section~\ref{m0087_...}) -> the section title; equation references cannot be resolved
    t = re.sub(
        r"Sections?~\\ref\{(m\d+)[^{}]*\}",
        lambda m: "the section ``" + titles[m.group(1)] + "''" if m.group(1) in titles else "an earlier section",
        t,
    )
    t = re.sub(r"Equations~\\ref\{[^{}]*\}\s*(?:--|and|,)\s*\\ref\{[^{}]*\}", "earlier equations", t)
    t = re.sub(r"Equations?~\\ref\{[^{}]*\}", "an earlier equation", t)
    t = re.sub(r"Tables?~\\ref\{[^{}]*\}", "an earlier table", t)
    t = re.sub(r"\\mbox\{([^{}$]*)\$\^\{?(\d)\}?\$\}", r"\\mbox{\1}^\2", t)  # \mbox{V/m$^3$} inside math
    t = map_text(t, ell_text, ell_math)
    t = unwrap(t, "emph", r"\emph{@}")
    t = re.sub(r"\\item\b", r"\\item", t)
    return tidy_space(t)


def ell_structure(book_dir: Path, vol: int):
    """Yield (module name, chapter, section, text) for the modules of the main matter."""
    root = next(p for p in (book_dir / "x").iterdir() if p.is_dir())
    orbd = (root / "orbd.tex").read_text(encoding="utf-8", errors="replace")
    chap = sec = 0
    main = appendix = False
    mods = {}
    for line in orbd.splitlines():
        if line.lstrip().startswith("%"):
            continue
        if "\\mainmatter" in line:
            main = True
        if "\\appendix" in line:
            appendix, chap = True, 0
        if re.search(r"\\chapter\{", line):
            if main:
                chap += 1
            sec = 0
        if re.search(r"\\section\{", line):
            sec += 1
        m = re.search(r"\\input\{modules/([^}]+)\}", line)
        if m and main:
            mods[m.group(1)] = (chap, sec, appendix)
    titles = {}
    for name in mods:
        titles[name.split("_")[0]] = name.split("_", 1)[1].replace("_", " ")
    for name, (c, s, a) in mods.items():
        yield name, c, s, a, (root / "modules" / f"{name}.tex").read_text(encoding="utf-8", errors="replace"), titles


SOLUTION_RE = re.compile(r"\{\\bf\s+Solution[.:]?\s*\}|\\textbf\{Solution[.:]?\}|\\emph\{Solution[.:]?\}", re.I)
FIGURE_RE = re.compile(r"\\includegraphics|\\caption|Figure~?\\ref|\bFig\.|Table~?\\ref|\bfigure\b|\bshown\b", re.I)
EQ_REF_RE = re.compile(r"(?:Equations?|Eqs?\.|Tables?|Examples?|Chapter|Appendix)~?\s*\(?\\ref")


def ellingson(data: Path, fixes: dict):
    rows, dropped = [], {}
    for vol in (1, 2):
        book = data / "ellingson" / f"v{vol}"
        if not book.exists():
            continue
        counter: collections.Counter = collections.Counter()
        for name, c, _s, appx, tex, titles in ell_structure(book, vol):
            ch = chr(64 + c) if appx else str(c)
            for m in re.finditer(r"\\begin\{example\}(.*?)\\end\{example\}", tex, re.S):
                body = re.sub(r"(?m)(?<!\\)%.*$", "", m.group(1))
                counter[ch] += 1
                num = f"{ch}.{counter[ch]}"
                key = f"Ellingson V{vol} ex {num}"
                if not body.strip():  # an empty placeholder: still numbered by LaTeX
                    continue
                if not SOLUTION_RE.search(body):
                    dropped[key] = "a narrative example without a question and solution"
                    continue
                if re.search(r"\\includegraphics|\\caption|Figure~\\ref|Fig\.", body):
                    dropped[key] = "needs a figure that is not in the text"
                    continue
                stem_raw, sol_raw = SOLUTION_RE.split(body, maxsplit=1)
                if "\\\\~\\\\" in stem_raw:  # the example's title is the first paragraph
                    stem_raw = stem_raw.split("\\\\~\\\\", 1)[1]
                stem = ell_clean(stem_raw, titles)
                sol = re.sub(r"^[.:]\s*", "", ell_clean(sol_raw, titles))
                if re.search(r"\\ref\{|(?:previous|preceding|earlier|above)\s+example|Example~", stem):
                    dropped[key] = "depends on an earlier example's results"
                    continue
                rows.append(
                    {
                        "key": key,
                        "kind": "example",
                        "subsource": f"Vol. {vol}, Chapter {ch}",
                        "idx": f"V{vol} ex {num}",
                        "module": name,
                        "stem": stem,
                        "sol": sol,
                        "flags": [],
                        "sflags": [],
                        "title": titles.get(name.split("_")[0], ""),
                    }
                )
    return rows, dropped


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------


EXTRA_SYMBOLS = {
    "\u2192": r"\to ",
    "\u2190": r"\leftarrow ",
    "\u21cc": r"\rightleftharpoons ",
    "\u2206": r"\Delta ",
    "\u03a9": r"\Omega ",
    "\u03b3": r"\gamma ",
    "\u03c1": r"\rho ",
    "\u03c3": r"\sigma ",
    "\u03c4": r"\tau ",
    "\u03c6": r"\varphi ",
    "\u03b5": r"\epsilon ",
    "\u03b7": r"\eta ",
    "\u03ba": r"\kappa ",
    "\u03bd": r"\nu ",
    "\u03c7": r"\chi ",
    "\u2211": r"\sum ",
    "\u221e": r"\infty ",
    "\u2260": r"\neq ",
    "\u00b5": r"\mu ",
    "\u2013": "--",
    "\u2014": "---",
    "\u2212": "-",
    "\u2009": " ",
    "\u202f": " ",
    "\u200b": "",
    "\u2032": "'",
    "\u2019": "'",
    "\u2018": "`",
    "\u201c": "``",
    "\u201d": "''",
    "\u00d7": r"\times ",
    "\u00b0": r"^{\circ}",
    "\u00b1": r"\pm ",
    "\u00ba": r"^{\circ}",
    "\u00b7": r"\cdot ",
    "\u22c5": r"\cdot ",
    "\u03bb": r"\lambda ",
    "\u03bc": r"\mu ",
    "\u03b4": r"\delta ",
    "\u03b1": r"\alpha ",
    "\u03b2": r"\beta ",
    "\u03b8": r"\theta ",
    "\u03c9": r"\omega ",
    "\u03c0": r"\pi ",
    "\u0394": r"\Delta ",
    "\u2248": r"\approx ",
    "\u2264": r"\leq ",
    "\u2265": r"\geq ",
    "\u03a3": r"\Sigma ",
    "\u03b6": r"\zeta ",
    "\u03c8": r"\psi ",
}
UNI_RE = re.compile("[" + "".join(EXTRA_SYMBOLS) + "]")
PLACE_RE = re.compile("\x01(\\d+)\x02")
FIG_WORDS = re.compile(r"\b(figure|fig\.|diagram below|graph below|plot below|shown (?:above|below|in the))\b", re.I)


def tex_symbols(text: str, in_math: bool) -> str:
    def rep(m: re.Match) -> str:
        v = EXTRA_SYMBOLS[m.group(0)]
        if not in_math and v[:1] in ("\\", "^"):
            return "$" + v.strip() + "$"
        return v

    return UNI_RE.sub(rep, text)


def clean_math(m: str) -> str:
    m = re.sub(r"<br\s*/?>", "\n", m)
    m = re.sub(r"</?[a-zA-Z][^>]*>", "", m)
    m = html.unescape(m).replace("\u00a0", " ")
    m = re.sub(r"\\(?:label|tag)\{[^{}]*\}", "", m)
    m = re.sub(r"\\PageIndex\{(\d+)\}", r"\1", m)
    m = m.replace("\\displaystyle", "").replace("\\nonumber", "")
    m = re.sub(r"\\begin\{(align|gather|equation)\}(.*?)\\end\{\1\}", r"\\begin{\1*}\2\\end{\1*}", m, flags=re.S)
    m = re.sub(r"\\textstyle\b", "", m)
    m = re.sub(r"(?<![\\a-zA-Z])textstyle(?=\\)", "", m)
    m = re.sub(r"(?<![\\a-zA-Z])mathbf\{\}", "", m)
    m = tex_symbols(m, True)
    m = re.sub(r"\\mbox\b", r"\\text", m)
    m = re.sub(r"\n[ \t]*\n+", "\n", m)  # a blank line would end the paragraph inside align*
    m = re.sub(r"(?<!\\)([%$])", r"\\\1", m)  # a bare % or $ inside math (currency, \text{%}) must be escaped
    return m.strip()


MATHSPAN_RE = re.compile(
    r"\[latex\](.*?)\[/latex\]|\\\((.*?)\\\)|\\\[(.*?)\\\]|(\\begin\{(?:align|equation|gather)\*?\}.*?\\end\{(?:align|equation|gather)\*?\})",
    re.S,
)


DISPLAY_ENV_RE = re.compile(r"\s*\\begin\{(?:align|gather|equation)\*\}.*\\end\{(?:align|gather|equation)\*\}\s*$", re.S)


class H2T(HTMLParser):
    """Small HTML-to-LaTeX converter for the textbook pages (math spans were replaced by placeholders)."""

    def __init__(self, maths: list[tuple[str, str]]):
        super().__init__(convert_charrefs=True)
        self.maths = maths
        self.out: list[str] = []
        self.flags: set[str] = set()
        self.lists: list[dict] = []
        self.skip = 0
        self.table: list[list[str]] | None = None
        self.cell: list[str] | None = None
        self.ncols = 0
        self.supsub = 0

    def w(self, s: str) -> None:
        (self.cell if self.cell is not None else self.out).append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "svg", "button", "iframe"):
            self.skip += 1
            if tag == "iframe":
                self.flags.add("figure")
            return
        if tag in ("p", "div", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "section"):
            self.w("\n\n")
        elif tag == "br":
            self.w(" \x03 " if self.cell is None else " ")
        elif tag in ("b", "strong"):
            self.w("\\textbf{")
        elif tag in ("i", "em"):
            self.w("\\textit{")
        elif tag == "sub":
            self.w("\x04_{")
        elif tag == "sup":
            self.w("\x04^{")
        elif tag in ("ul", "ol"):
            kind = "ul" if tag == "ul" else "ol"
            style = (a.get("style") or "") + (a.get("type") or "")
            self.lists.append({"kind": kind, "n": 0, "alpha": "alpha" in style or a.get("type") == "a"})
            self.w("\n\n")
        elif tag == "li" and self.lists:
            L = self.lists[-1]
            L["n"] += 1
            if L["kind"] == "ul":
                self.w("\n\n$\\bullet$ ")
            elif L["alpha"]:
                self.w(f"\n\n({chr(64 + L['n'])}) ")
                self.flags.add("options")
            else:
                self.w(f"\n\n({L['n']}) ")
        elif tag == "img":
            alt = html.unescape(a.get("alt") or "")
            src = a.get("src") or ""
            if alt and re.search(r"[\\^_=]", alt) and re.search(r"\.(png|gif|svg)", src, re.I) and "\n" not in alt:
                self.maths.append(("inline", clean_math(alt)))
                self.w(f"\x01{len(self.maths) - 1}\x02")
            else:
                self.flags.add("figure")
        elif tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.table.append([])
        elif tag in ("td", "th") and self.table is not None:
            self.cell = []
            if a.get("colspan") or a.get("rowspan"):
                self.flags.add("complex_table")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg", "button", "iframe"):
            self.skip = max(0, self.skip - 1)
            return
        if tag in ("sub", "sup"):
            self.supsub = max(0, self.supsub - 1)
            self.w("}")
        elif tag in ("b", "strong", "i", "em"):
            self.w("}")
        elif tag in ("p", "div", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "section"):
            self.w("\n\n")
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self.w("\n\n")
        elif tag in ("td", "th") and self.table is not None and self.cell is not None:
            self.table[-1].append("".join(self.cell).strip())
            self.cell = None
        elif tag == "table" and self.table is not None:
            rows = [r for r in self.table if r]
            self.table = None
            n = max((len(r) for r in rows), default=0)
            if n == 0:
                return
            body = " \\\\ \\hline\n".join(" & ".join(r + [""] * (n - len(r))) for r in rows)
            self.w("\n\n\\begin{center}\n\\begin{tabular}{|" + "c|" * n + "}\\hline\n" + body + " \\\\ \\hline\n\\end{tabular}\n\\end{center}\n\n")
            self.flags.add("table")

    def handle_data(self, data):
        if self.skip:
            return
        data = data.replace("\u00a0", " ")
        parts = PLACE_RE.split(data)
        for i, p in enumerate(parts):
            if i % 2:
                self.w(f"\x01{p}\x02")
                continue
            p = re.sub(r"\s+", " ", p).replace("^{" + chr(92) + "circ}", "°")
            if self.supsub:
                self.w(tex_symbols(re.sub(r"([%&#_{}$])", r"\\\1", p), True))
                continue
            p = p.replace("\\", "\\textbackslash{}")
            for ch, rep in (("$", "\\$"), ("%", "\\%"), ("&", "\\&"), ("#", "\\#"), ("_", "\\_"), ("{", "\\{"), ("}", "\\}"),
                            ("^", "\\^{}"), ("~", "\\~{}")):
                p = p.replace(ch, rep)
            p = p.replace("<", "$<$").replace(">", "$>$")
            self.w(tex_symbols(p, False))


def html_to_tex(fragment: str) -> tuple[str, set[str]]:
    """(LaTeX text, flags) of an HTML fragment; flags: figure, table, options, unresolved_ref."""
    maths: list[tuple[str, str]] = []

    def grab(m: re.Match) -> str:
        if m.group(1) is not None:
            kind, body = "latex", m.group(1)
        elif m.group(2) is not None:
            kind, body = "inline", m.group(2)
        elif m.group(3) is not None:
            kind, body = "display", m.group(3)
        else:
            kind, body = "env", m.group(4)
        maths.append((kind, clean_math(body)))
        return f"\x01{len(maths) - 1}\x02"

    frag = MATHSPAN_RE.sub(grab, fragment)
    p = H2T(maths)
    p.feed(frag)
    p.close()
    text = "".join(p.out)
    text = re.sub(r"\x04([_^])\{((?:[^{}]|\{[^{}]*\})*)\}", lambda m: "$" + m.group(1) + "{" + m.group(2) + "}$" if m.group(2) else "", text)
    text = text.replace("\x04", "")
    text = text.replace("\\textbf{}", "").replace("\\textit{}", "")
    paras = [x.strip() for x in re.split(r"\n\s*\n", text)]
    out = []
    for para in paras:
        if not para:
            continue
        m = re.fullmatch(r"\x01(\d+)\x02", para)
        if m:
            kind, body = maths[int(m.group(1))]
            if kind == "env" or DISPLAY_ENV_RE.match(body):
                para = body
            else:
                para = "\\[\n" + body + "\n\\]" if kind != "inline" else "$" + body + "$"
            out.append(para)
            continue

        def sub(mm: re.Match) -> str:
            kind, body = maths[int(mm.group(1))]
            if DISPLAY_ENV_RE.match(body) and kind != "inline":
                return "\n\n" + body + "\n\n"
            return body if kind == "env" else ("\\[" + body + "\\]" if kind == "display" else "$" + body + "$")

        out.append(PLACE_RE.sub(sub, para))
    text = "\n\n".join(out).replace(" \x03 ", "\n\n").replace("\x03", "\n\n")
    text = re.sub(
        r"\\text(bf|it)\{([^{}]*)\}",
        lambda m: "\\text" + m.group(1) + "{" + re.sub(r"\s*\n\s*", " ", m.group(2)).strip() + "}",
        text,
    )
    if re.search(r"\\ref\{|\\eqref\{", text):
        p.flags.add("unresolved_ref")
    return tidy_space(text), p.flags


def get_pages(data: Path, book: str) -> list[tuple[str, str]]:
    """(url, html) of every cached page of a book, in crawl order."""
    d = data / book
    out = []
    idx = d / "index.tsv"
    if not idx.exists():
        return out
    for line in idx.read_text(encoding="utf-8").splitlines():
        h, u = line.split("\t")
        f = d / "pages" / f"{h}.html"
        if f.exists():
            out.append((u, f.read_text(encoding="utf-8", errors="replace")))
    return out


def fetch(data: Path, book: str) -> None:
    """Crawl a book politely: one request per second, each page once, cached under DATA/<book>/pages."""
    roots = {
        "woolf": (
            "https://eng.libretexts.org/Bookshelves/Industrial_and_Systems_Engineering/Chemical_Process_Dynamics_and_Controls_(Woolf)",
            "https://eng.libretexts.org/Bookshelves/Industrial_and_Systems_Engineering/Chemical_Process_Dynamics_and_Controls_(Woolf)",
        ),
        "verrett": ("https://pressbooks.bccampus.ca/chbe220/", "https://pressbooks.bccampus.ca/chbe220/chapter/"),
    }
    root, prefix = roots[book]
    d = data / book
    (d / "pages").mkdir(parents=True, exist_ok=True)
    index = d / "index.tsv"
    seen = {}
    if index.exists():
        for line in index.read_text(encoding="utf-8").splitlines():
            h, u = line.split("\t")
            seen[u] = h
    queue, done, last = [root], set(), 0.0
    while queue:
        u = queue.pop(0)
        if u in done:
            continue
        done.add(u)
        h = hashlib.sha1(u.encode()).hexdigest()[:16]
        f = d / "pages" / f"{h}.html"
        if f.exists():
            page = f.read_text(encoding="utf-8", errors="replace")
        else:
            time.sleep(max(0.0, 1.1 - (time.time() - last)))
            last = time.time()
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Amplify private importer; 1 req/s)"})
            try:
                page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
            except OSError as e:
                print("FAIL", u, e)
                continue
            f.write_text(page, encoding="utf-8")
            with index.open("a", encoding="utf-8") as fh:
                fh.write(f"{h}\t{u}\n")
        for m in re.finditer(r'href="([^"#]+)"', page):
            link = urllib.parse.urljoin(u, m.group(1).replace("&amp;", "&"))
            if link.startswith(prefix) and link not in done and link not in queue and not re.search(r"\.(png|jpe?g|pdf|css|js)$", link):
                queue.append(link)


SOFTWARE_RE = re.compile(
    r"\b(Excel|MATLAB|Matlab|Mathematica|Simulink|Python|Genie|GeNIe|spreadsheet|Solver|VBA|Visual Basic|Wolfram|Aspen|HYSYS|PI-?Sim|simulation software)\b"
)
EARLIER_RE = re.compile(
    r"\b(previous|preceding|prior|above|earlier|last|same)\s+(example|exercise|problem|question|part)\b|"
    r"\b(example|exercise|problem|question|part)\s+(\d+|\\\\?\(|above)|\bcontinu(?:e|ing)\s+(?:from|with)\b|\b(?:using|from|in)\s+the\s+(?:data|results?)\s+(?:above|from)\b",
    re.I,
)
FIGREF_RE = re.compile(r"\b(?:figure|fig\.|image|picture|diagram|graph|plot|chart|schematic|P&ID|PFD|flowsheet)\b[^.]{0,40}\b(?:below|above|shown|given|provided|following|at right|at left)\b|"
                       r"\b(?:below|above|shown|given in|in the|following)\s+(?:figure|fig\.|image|picture|diagram|graph|plot|chart|schematic|flow\s?sheet|P&ID|PFD)\b|\bFigure\s*(?:\d|#)", re.I)


def split_at(h: str, pat: str) -> tuple[str, str | None]:
    m = re.search(pat, h, re.S)
    return (h[: m.start()], h[m.end():]) if m else (h, None)


def woolf(data: Path, fixes: dict):
    rows, dropped = [], {}
    for _url, page in get_pages(data, "woolf"):
        t = re.search(r"<title>\s*(\d+\.\d+):\s*([^<]*?)\s*-\s*Engineering LibreTexts", page)
        if not t:
            continue
        sec, title = t.group(1), html.unescape(t.group(2))
        counts = collections.Counter()
        for m in re.finditer(r'<section class="box-(example|exercise)">(.*?)</section>', page, re.S):
            kind, box = m.group(1), m.group(2)
            counts[kind] += 1
            n = counts[kind]
            key = f"Woolf {sec} {kind} {n}"
            box = re.sub(r'mt-section-origin="[^"]*"', "", box)
            box = re.sub(r"<h5[^>]*box-legend.*?</h5>", "", box, flags=re.S)
            if kind == "example":
                stem_h, sol_h = split_at(box, r'<h6[^>]*>\s*(?:Solution|Answer)[^<]*</h6>')
                if sol_h is None:
                    stem_h, sol_h = split_at(box, r"<strong[^>]*>\s*(?:Solution|Answer)\s*:?\s*</strong>")
            else:
                stem_h, sol_h = split_at(box, r"<dl>\s*<dt>\s*<strong[^>]*>\s*(?:Answer|Solution)\s*</strong>\s*</dt>")
                if sol_h is not None:
                    sol_h = re.sub(r"^\s*<dd>|</dd>\s*</dl>.*$", "", sol_h, flags=re.S)
            if sol_h is None:
                dropped[key] = "no solution or answer in the book"
                continue
            stem, f1 = html_to_tex(stem_h)
            sol, f2 = html_to_tex(sol_h)
            rows.append(
                {"key": key, "section": sec, "kind": kind, "n": n, "title": title, "stem": stem, "sol": sol,
                 "flags": sorted(f1), "sflags": sorted(f2)}
            )
    return rows, dropped


VMARK_RE = re.compile(
    r'<div class="textbox textbox--(?P<k>exercises|examples)">|<div class="textbox">\s*<h3>\s*Solutions?\s*</h3>|<h2[ >]|<footer|<div class="textbox textbox--(?:learning-objectives|key-takeaways)">'
)


def verrett_toc(page: str) -> dict[str, tuple[str, str, str]]:
    """slug -> (part, chapter number, chapter title) from the book's table of contents."""
    out = {}
    for pm in re.finditer(r'<li id="toc-part-\d+" class="toc__part.*?(?=<li id="toc-part-|<li id="toc-back-matter|$)', page, re.S):
        blk = pm.group(0)
        pt = re.search(r"<span class='toc__title__number'>([^<]*)</span>([^<]*)</a>", blk)
        part = (html.unescape(pt.group(1)).strip().rstrip(".") + ". " + html.unescape(pt.group(2)).strip()) if pt else ""
        for cm in re.finditer(r'<a href="[^"]*/chapter/([^/"]+)/"><span>([^<]*)</span>([^<]*)</a>', blk):
            out[cm.group(1)] = (part, html.unescape(cm.group(2)).replace(" ", " ").strip().rstrip("."), html.unescape(cm.group(3)).strip())
    return out


def div_inner(body: str, start: int) -> str:
    """Inner HTML of the <div> that opens at body[start] (matching </div> by depth)."""
    first = body.index(">", start) + 1
    depth = 1
    for m in re.finditer(r"<div|</div>", body[first:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return body[first: first + m.start()]
    return body[first:]


def verrett(data: Path, fixes: dict):
    rows, dropped = [], {}
    pages = get_pages(data, "verrett")
    toc = verrett_toc(pages[0][1]) if pages else {}
    for url, page in pages:
        if 'data-type="chapter"' not in page:
            continue
        tm = re.search(r'<h1 class="entry-title">(.*?)</h1>', page, re.S)
        title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", tm.group(1) if tm else ""))).strip()
        slug = url.rstrip("/").split("/")[-1]
        body = page[page.index('data-type="chapter"'):]
        marks = list(VMARK_RE.finditer(body))
        counts = collections.Counter()
        for i, m in enumerate(marks):
            if not m.group("k"):
                continue
            seg = div_inner(body, m.start())
            kind = "exercise" if m.group("k") == "exercises" else "example"
            counts[kind] += 1
            key = f"Verrett {slug} {kind} {counts[kind]}"
            sol_h = None
            if kind == "exercise":
                if i + 1 < len(marks) and "Solution" in body[marks[i + 1].start(): marks[i + 1].end()]:
                    sol_h = re.sub(r"^\s*<h3>\s*Solutions?\s*</h3>", "", div_inner(body, marks[i + 1].start()))
                stem_h = seg
            else:
                stem_h, sol_h = split_at(seg, r"(?i)<(?:p|h\d|strong|b)[^>]*>\s*(?:<(?:strong|b|em)>)?\s*Solution\s*:?\s*(?:</(?:strong|b|em)>)?\s*(?:</(?:p|h\d)>)?")
            hdr = re.search(r'<p class="textbox__title">(.*?)</p>', stem_h, re.S)
            heading = re.sub(r"<[^>]+>", "", hdr.group(1)).strip() if hdr else ""
            stem_h = re.sub(r'<header class="textbox__header">.*?</header>', "", stem_h, flags=re.S)
            if sol_h is None:
                dropped[key] = "no worked solution next to the item"
                continue
            stem, f1 = html_to_tex(stem_h)
            sol, f2 = html_to_tex(sol_h)
            rows.append(
                {"key": key, "slug": slug, "part": toc.get(slug, ("", "", ""))[0], "num": toc.get(slug, ("", "", ""))[1],
                 "kind": kind, "n": counts[kind], "title": title, "heading": html.unescape(heading),
                 "stem": stem, "sol": sol, "flags": sorted(f1), "sflags": sorted(f2)}
            )
    return rows, dropped


OPT_PARA_RE = re.compile(r"^\(?([a-eA-E])[\).:]\s*(.+)$", re.S)


def normalize_options(stem: str) -> tuple[str, list[str]]:
    """Options written as 'a) ...' or 'a. ...' paragraphs become '(A) ...'; returns (stem, option letters)."""
    paras = stem.split("\n\n")
    run = []
    for k in range(len(paras) - 1, -1, -1):
        m = OPT_PARA_RE.match(paras[k].strip())
        if not m:
            break
        run.append((k, m))
    run.reverse()
    letters = [m.group(1).upper() for _, m in run]
    if len(run) >= 3 and letters == [chr(65 + i) for i in range(len(run))]:
        for k, m in run:
            paras[k] = f"({m.group(1).upper()}) {m.group(2).strip()}"
        return "\n\n".join(paras), letters
    return stem, []


def mcq_letters(sol: str, avail: list[str]) -> list[str] | None:
    head = re.sub(r"\\text(?:bf|it)\{|[{}*]", "", sol[:120]).strip()
    m = re.match(r"(?:Answer|Ans)?\s*:?\s*\(?([A-Ea-e](?:\s*(?:,|and|&)\s*[A-Ea-e])*)\)?(?![A-Za-z])", head)
    if not m:
        return None
    letters = sorted({x.upper() for x in re.findall(r"[A-Ea-e]", m.group(1))})
    return letters if set(letters) <= set(avail) else None


def finalize(book: str, raw: list[dict], dropped: dict, fixes: dict) -> list[dict]:
    """Raw parsed items -> row dicts (drops go to `dropped` with a reason)."""
    set_name, source = BOOKS[book]
    manual = fixes.get("dropped", {})
    answers = fixes.get("answers", {})
    hand: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for e in fixes.get("fixes", []):
        hand.setdefault((e["key"], e["field"]), []).extend(tuple(x) for x in e["fixes"])
    rows = []
    for r in raw:
        key = r["key"]
        if key in manual:
            dropped[key] = manual[key]
            continue
        flags = set(r.get("flags", []))
        sflags = set(r.get("sflags", []))
        stem, sol = r["stem"], r["sol"]
        why = None
        if book != "ellingson":
            if "figure" in flags or FIGREF_RE.search(stem):
                why = "needs a figure or image that is not in the text"
            elif "figure" in sflags or FIGREF_RE.search(sol):
                why = "its solution depends on a figure"
            elif SOFTWARE_RE.search(stem + sol):
                why = "needs software (Excel, MATLAB, Mathematica, Python, ...)"
            elif EARLIER_RE.search(stem):
                why = "depends on an earlier item's results"
            elif re.fullmatch(r"\s*(TBA|tba|N/A|)\s*", sol) or "Add texts here" in sol:
                why = "no answer in the book"
            elif "unresolved_ref" in flags | sflags:
                why = "refers to an equation or section of the book by number"
        if why:
            dropped[key] = why
            continue
        stem, letters = normalize_options(stem)
        for fld in ("stem", "sol"):
            for old, new in hand.get((key, fld), []):
                txt = stem if fld == "stem" else sol
                if txt.count(old) != 1:
                    raise SystemExit(f"HAND FIX {key} {fld}: expected exactly one {old!r}")
                if fld == "stem":
                    stem = stem.replace(old, new)
                else:
                    sol = sol.replace(old, new)
        answer = None
        if letters:
            got = mcq_letters(sol, letters)
            if got is None and key in answers:
                got = [x.strip() for x in answers[key].split(",")]
            if got is None:
                dropped[key] = "multiple choice without a usable answer letter"
                continue
            answer = ", ".join(got)
            low = stem.lower()
            note = ""
            if len(got) == 1 and not re.search(r"exactly one|only one|one option", low):
                note = "Exactly one option is correct."
            elif len(got) > 1 and not re.search(r"one or more|multiple", low):
                note = "One or more options may be correct."
            if note:
                first = stem.index("\n\n(A) ")
                stem = stem[:first] + "\n\n" + note + stem[first:]
        else:
            answer = answers.get(key)
            if not answer:
                dropped[key] = "no short answer key could be derived"
                continue
        stem = pu_to_latex(stem)
        sol = pu_to_latex(sol)
        stored = sol if len(sol) >= MIN_SOLUTION and not re.search(r"an earlier (?:equation|table)|earlier equations", sol) else None
        if book == "ellingson":
            sub, idx = r["subsource"], r["idx"]
        elif book == "woolf":
            sub, idx = f"Chapter {r['section'].split('.')[0]}", f"{r['section']} {r['kind']} {r['n']}"
        else:
            sub = f"Chapter {r['num']}"
            idx = f"{r['slug']} {r['kind']} {r['n']}"
        rows.append(
            {
                "potd": f"{set_name} {idx}",
                "set": set_name,
                "idx": idx,
                "orig": "",
                "source": source,
                "subsource": sub,
                "latexcode": stem,
                "answer": answer,
                "solution": stored,
                "hints": None,
                "more_hints": None,
                "ref_solution": sol,
                "group": "subject",
                "effort": None,
                "image": None,
            }
        )
    return rows


def build(data: Path, only: list[str], fixes: dict) -> tuple[list[dict], dict[str, str]]:
    funcs = {"ellingson": ellingson, "woolf": woolf, "verrett": verrett}
    rows, dropped = [], {}
    for book in only:
        raw, drop = funcs[book](data, fixes)
        dropped.update(drop)
        rows += finalize(book, raw, dropped, fixes)
    seen: dict[str, str] = {}
    out = []
    for r in rows:  # the same statement twice inside the wave: keep one
        k = latex_hash(r["latexcode"])
        if k in seen:
            dropped[r["potd"]] = f"same statement as {seen[k]}"
            continue
        seen[k] = r["potd"]
        out.append(r)
    return out, dropped


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", default="ellingson,woolf,verrett")
    p.add_argument("--fetch", choices=["woolf", "verrett"], help="download the HTML pages into DATA first")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--raw", type=Path, help="debug: dump the raw parsed items of the first --only book")
    p.add_argument("--list-dropped", action="store_true")
    p.add_argument("--no-bank", action="store_true", help="skip the (slow) comparison with the bank")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()
    if a.fetch:
        fetch(a.data, a.fetch)
        return
    fixes = load_fixes()
    only = a.only.split(",")
    if a.raw:
        raw, _ = {"ellingson": ellingson, "woolf": woolf, "verrett": verrett}[only[0]](a.data, fixes)
        a.raw.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    rows, dropped = build(a.data, only, fixes)
    dup = {}
    if not a.no_bank:
        conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
        dup = duplicates(rows, conn)
        conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    if a.set_aside:
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    if a.list_dropped:
        for k, v in sorted(dropped.items()):
            print("dropped", k, "-", v)
    reasons = collections.Counter(re.sub(r"\d+", "N", v) for v in dropped.values())
    print(
        json.dumps(
            {
                "rows_kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "with_stored_solution": sum(bool(r["solution"]) for r in new),
                "by_book": collections.Counter(r["set"] for r in new),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if not a.apply:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("eng_texts")
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
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"],
                 r["answer"], r["solution"], r["hints"], r["more_hints"], h),
            )
            existing.add(h)
            added.append((cur.lastrowid, r))
        conn.commit()
    finally:
        conn.close()
    new_file = not MAP_PATH.exists() or MAP_PATH.stat().st_size == 0
    with MAP_PATH.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update(
        {str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]} for q, r in added if r["ref_solution"]}
    )
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
