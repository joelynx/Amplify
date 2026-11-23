"""
Import OpenStax Chemistry 2e (end-of-chapter exercises)
-------------------------------------------------------
OpenStax Chemistry 2e (openstax.org/details/books/chemistry-2e, github.com/openstax/osbooks-chemistry-bundle,
CNXML with MathML; the commit before the licence change of 2026-03-19, so CC BY 4.0). 1,736 exercises in 21
chapters; the odd-numbered ones have a short answer in the book's answer key (<solution> in the source). The
exercises sit in the section modules in book order: chapter number = position in the collection, exercise number
= running count within the chapter (where an exercise of the book is missing from the source, a solved
exercise that would land on an even number moves to the next odd one, so numbers in chapters 12-17 can be
off by one against the printed book; the idx/subsource say "exercise <n>").

Rows: source "OpenStax Chemistry 2e", subsource "Chapter <n>, exercise <m>", idx "<n>.<m>", group "subject".
Every kept exercise is a question; the odd ones carry the book's answer as key. The answer is the key as the
book gives it (prose and inline math); when it is at least 150 characters (a worked solution) it is also stored
as `solution` and its closing sentence is the key. The text is always kept in ref_solution
(app/data/appdata/benchmarks_solutions.json). Even-numbered exercises: no key (answer None).

Conversions: CNXML paragraphs to LaTeX (emphasis, sub/sup, lists, simple tables to tabular) and MathML to
LaTeX (mi mn mo mtext mspace mrow msub msup msubsup mfrac msqrt mroot mover munder mtable mfenced mstyle
mphantom; arrows, the unicode operators and Greek letters become commands; element symbols and states are
upright \\mathrm, so H_2O(l) comes out as $\\mathrm{H}_{2}\\mathrm{O}(l)$, and arrows are \\longrightarrow /
\\rightleftharpoons).

Dropped (listed in the dry run by reason): exercises with an image or figure; exercises that cite a figure,
table, example, section or another exercise of the book, or "the data above"; exercises that ask for a drawing
or structure, an internet look-up, a simulation or an experiment; tables that are not simple; characters or
elements the converter does not know.

Run: python -m app.tools.import_openstax_chem --data <folder with openstax_chem/> --dry-run [--dump rows.json]
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

from app.tools.import_answer_sets import duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "OpenStax Chemistry 2e"
SOURCE = "OpenStax Chemistry 2e"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
SET_ASIDE_PATH = Path("app/data/appdata/openstax_chem_set_aside.json")
MIN_SOLUTION = 150
_FIXES_PATH = Path(__file__).with_name("openstax_chem_fixes.json")
_FIXES = json.loads(_FIXES_PATH.read_text(encoding="utf-8")) if _FIXES_PATH.exists() else {}
HAND_FIXES: dict[tuple[str, str], list] = {}
for _f in _FIXES.get("fixes", []):
    HAND_FIXES[(_f["key"], _f["field"])] = _f["fixes"]
EXTRA_DROPS: dict[str, str] = _FIXES.get("dropped", {})

N = "{http://cnx.rice.edu/cnxml}"
C = "{http://cnx.rice.edu/collxml}"


class Drop(Exception):
    """The exercise cannot be imported (the message is the reason)."""


def local(el: ET.Element) -> str:
    return el.tag.rsplit("}", 1)[-1]


# ---------------------------------------------------------------- characters
GREEK = {
    "\u03b1": "\\alpha", "\u03b2": "\\beta", "\u03b3": "\\gamma", "\u03b4": "\\delta", "\u03b5": "\\varepsilon",
    "\u03b6": "\\zeta", "\u03b7": "\\eta", "\u03b8": "\\theta", "\u03ba": "\\kappa", "\u03bb": "\\lambda",
    "\u03bc": "\\mu", "\u00b5": "\\mu", "\u03bd": "\\nu", "\u03be": "\\xi", "\u03c0": "\\pi", "\u03c1": "\\rho",
    "\u03c3": "\\sigma", "\u03c4": "\\tau", "\u03c6": "\\varphi", "\u03d5": "\\phi", "\u03c7": "\\chi",
    "\u03c8": "\\psi", "\u03c9": "\\omega", "\u0393": "\\Gamma", "\u0394": "\\Delta", "\u0398": "\\Theta",
    "\u039b": "\\Lambda", "\u039e": "\\Xi", "\u03a0": "\\Pi", "\u03a3": "\\Sigma", "\u03a6": "\\Phi",
    "\u03a8": "\\Psi", "\u03a9": "\\Omega", "\u2126": "\\Omega", "\u03b9": "\\iota", "\u03c2": "\\varsigma",
    "\u03f5": "\\epsilon", "\u03d1": "\\vartheta", "\u03d6": "\\varpi",
}
# math symbols (inside math as they are; in prose wrapped in $...$)
SYMBOLS = {
    "\u2212": "-", "\u2013": "-", "\u2014": "-", "\u00d7": "\\times", "\u00f7": "\\div", "\u00b1": "\\pm",
    "\u2213": "\\mp", "\u00b7": "\\cdot", "\u22c5": "\\cdot", "\u2219": "\\cdot", "\u2022": "\\cdot",
    "\u00b0": "{}^{\\circ}", "\u2218": "\\circ", "\u2032": "'", "\u2033": "''", "\u2248": "\\approx",
    "\u2245": "\\cong", "\u2243": "\\simeq", "\u2260": "\\neq", "\u2264": "\\leq", "\u2265": "\\geq",
    "\u2261": "\\equiv", "\u221d": "\\propto", "\u221e": "\\infty", "\u2202": "\\partial", "\u2207": "\\nabla",
    "\u222b": "\\int", "\u2211": "\\sum", "\u221a": "\\sqrt{}", "\u223c": "\\sim", "\u2192": "\\rightarrow",
    "\u27f6": "\\longrightarrow", "\u2190": "\\leftarrow", "\u27f5": "\\longleftarrow", "\u2194": "\\leftrightarrow",
    "\u27f7": "\\longleftrightarrow", "\u21cc": "\\rightleftharpoons", "\u21c4": "\\rightleftarrows",
    "\u21d2": "\\Rightarrow", "\u21d4": "\\Leftrightarrow", "\u2191": "\\uparrow", "\u2193": "\\downarrow",
    "\u2234": "\\therefore", "\u226a": "\\ll", "\u226b": "\\gg", "\u2208": "\\in", "\u2209": "\\notin",
    "\u00b9": "^{1}", "\u00b2": "^{2}", "\u00b3": "^{3}", "\u207a": "^{+}", "\u207b": "^{-}",
    "\u2070": "^{0}", "\u2074": "^{4}", "\u2075": "^{5}", "\u2076": "^{6}", "\u2077": "^{7}", "\u2078": "^{8}",
    "\u2079": "^{9}", "\u2080": "_{0}", "\u2081": "_{1}", "\u2082": "_{2}", "\u2083": "_{3}", "\u2084": "_{4}",
    "\u2085": "_{5}", "\u2086": "_{6}", "\u2087": "_{7}", "\u2088": "_{8}", "\u2089": "_{9}", "\u00bd": "\\frac{1}{2}",
    "\u00bc": "\\frac{1}{4}", "\u00be": "\\frac{3}{4}", "\u2026": "\\ldots", "\u22ef": "\\cdots", "\u2225": "\\parallel",
    "\u2220": "\\angle", "\u2295": "\\oplus", "\u2296": "\\ominus", "\u00ac": "\\neg", "\u2223": "|",
    "\u2192\ufe0e": "\\rightarrow", "\u2206": "\\Delta", "\u2502": "|", "\u2551": "\\|", "\u2016": "\\|",
}
SYMBOLS.update(GREEK)
SPACES = {"\u00a0": " ", "\u2009": " ", "\u200a": " ", "\u2002": " ", "\u2003": " ", "\u202f": " ", "\u2005": " ",
          "\u2006": " ", "\u2004": " ", "\u2007": " ", "\u2008": " ", "\u200b": "", "\u2060": "", "\ufeff": "",
          "\u00ad": ""}
QUOTES = {"\u2018": "`", "\u2019": "'", "\u201c": "``", "\u201d": "''", "\u2010": "-", "\u2011": "-"}
SPECIAL_TEXT = {"&": "\\&", "%": "\\%", "#": "\\#", "_": "\\_", "{": "\\{", "}": "\\}", "$": "\\$",
                "~": "\\textasciitilde{}", "^": "\\textasciicircum{}", "\\": "\\textbackslash{}", "<": "<", ">": ">"}
MATH_SPECIAL = {"&": "\\&", "%": "\\%", "#": "\\#", "_": "\\_", "{": "\\{", "}": "\\}", "$": "\\$"}
OPERATOR_NAMES = {"ln", "log", "exp", "sin", "cos", "tan", "cot", "sec", "csc", "lim", "max", "min", "det"}


def is_letter(ch: str) -> bool:
    return ch.isalpha() and ch not in SYMBOLS


def prose_chars(text: str) -> str:
    """Escape running text; unicode math symbols become inline math."""
    for k, v in SPACES.items():
        text = text.replace(k, v)
    out = []
    for piece in re.split(r"(\u2212\s*\d[\d.,]*)", text):
        if piece[:1] == "\u2212" and len(piece) > 1:
            out.append("$-" + re.sub(r"\s+", "", piece[1:]) + "$")
        else:
            out.append(prose_piece(piece))
    return "".join(out)


def prose_piece(text: str) -> str:
    out = []
    for ch in text:
        if ch in SPECIAL_TEXT:
            out.append(SPECIAL_TEXT[ch])
        elif ch in QUOTES:
            out.append(QUOTES[ch])
        elif ch in SYMBOLS:
            out.append("$" + SYMBOLS[ch] + "$")
        elif ch == "\u00c5":
            out.append("$\\text{\\AA}$")
        elif ord(ch) < 128 or is_letter(ch) or ch.isspace():
            out.append(ch)
        elif ch in "\u00e9\u00e8":
            out.append(ch)
        else:
            raise Drop(f"unknown character U+{ord(ch):04X} {ch}")
    s = "".join(out)
    return re.sub(r"\$\s*\$", "", s.replace("$$", "$\\,$")) if "$$" in s else s


def math_text_run(text: str, italic: bool = False) -> str:
    """Text inside math: ASCII runs in \\mathrm / \\text, symbols as commands."""
    for k, v in SPACES.items():
        text = text.replace(k, v)
    pieces, run = [], []

    def flush() -> None:
        if not run:
            return
        t = "".join(run)
        run.clear()
        esc = "".join(MATH_SPECIAL.get(c, c) for c in t)
        esc = esc.replace("~", "\\sim ").replace("^", "\\wedge ").replace("\\", "\\backslash ") if False else esc
        if t.strip() == "":
            pieces.append("\\ ")
        elif " " in t or any(c in t for c in "<>"):
            pieces.append("\\text{" + "".join(SPECIAL_TEXT.get(c, c) if c not in "<>" else c for c in t) + "}")
        else:
            pieces.append(("\\mathit{" if italic else "\\mathrm{") + esc + "}")

    for ch in text:
        if ch == "\u2212":
            flush()
            pieces.append("-")
        elif ch in QUOTES and ch in "\u2019":
            run.append("'")
        elif ch in SYMBOLS:
            flush()
            pieces.append(SYMBOLS[ch] + " ")
        elif ch == "\u00c5":
            flush()
            pieces.append("\\text{\\AA}")
        elif ch in "~^\\":
            flush()
            pieces.append({"~": "\\sim ", "^": "\\wedge ", "\\": "\\backslash "}[ch])
        elif ord(ch) < 128 or is_letter(ch) or ch.isspace():
            run.append(ch)
        else:
            raise Drop(f"unknown character U+{ord(ch):04X} {ch}")
    flush()
    return "".join(pieces)


# ---------------------------------------------------------------- MathML
OP_MAP = {"{": "\\{", "}": "\\}", "%": "\\%", "#": "\\#", "&": "\\&", "\u2223": "|", "\u2016": "\\|", "\u2502": "|",
          "\u2329": "\\langle", "\u232a": "\\rangle", "\u27e8": "\\langle", "\u27e9": "\\rangle",
          "\u2061": "", "\u2062": "", "\u2063": "", "\u2064": "", "\u00a0": "\\ ", "\u221a": "\\surd "}
ACCENT_OVER = {"\u00af": "\\overline", "\u203e": "\\overline", "\u2015": "\\overline", "\u2192": "\\overrightarrow",
               "\u0302": "\\hat", "^": "\\widehat", "\u02c6": "\\widehat", "~": "\\widetilde", "\u02dc": "\\widetilde",
               "\u02d9": "\\dot", "\u00b7": "\\dot", ".": "\\dot", "\u2212": "\\overline", "\u2014": "\\overline",
               "-": "\\overline", "_": "\\overline", "\u23de": "\\overbrace", "\u23df": "\\underbrace"}


def simple_token(s: str) -> bool:
    return bool(re.fullmatch(r"(?:[A-Za-z0-9]|\\[A-Za-z]+(?: )?|\\mathrm\{[^{}]*\}|\\mathit\{[^{}]*\}|\\text\{[^{}]*\})", s))


def brace(s: str) -> str:
    return "{" + s + "}"


def base_of(s: str) -> str:
    return s if simple_token(s) else brace(s)


def space_cmd(width: str | None) -> str:
    if not width:
        return "\\,"
    m = re.fullmatch(r"([\d.]+)em", width.strip())
    if not m:
        return "\\ "
    w = float(m.group(1))
    if w >= 2:
        return "\\qquad "
    if w >= 0.9:
        return "\\quad "
    if w >= 0.4:
        return "\\ "
    if w >= 0.25:
        return "\\;"
    return "\\,"


STATES = {"s", "l", "g", "aq"}


def seq(kids: list[ET.Element]) -> str:
    """Children of an mrow; "(" a q ")" (the states are separate mi letters) becomes an upright (aq)."""
    out, i = [], 0
    while i < len(kids):
        k = kids[i]
        if local(k) == "mo" and (k.text or "").strip() == "(":
            j = i + 1
            while j < len(kids) and local(kids[j]) in ("mi", "mtext") and len((kids[j].text or "").strip()) <= 2:
                j += 1
            word = "".join((x.text or "").strip() for x in kids[i + 1 : j])
            if j > i + 1 and j < len(kids) and local(kids[j]) == "mo" and (kids[j].text or "").strip() == ")" and word in STATES:
                out.append("(\\mathrm{" + word + "})")
                i = j + 1
                continue
        out.append(mml(k))
        i += 1
    return "".join(out)


def mml(el: ET.Element) -> str:
    t = local(el)
    kids = list(el)
    if t in ("math", "mrow", "mstyle", "semantics"):
        inner = seq(kids)
        if t == "mstyle" and el.get("mathvariant") == "italic":
            return "\\mathit{" + inner + "}"
        return inner
    if t == "mi":
        s = (el.text or "").strip()
        if not s:
            return ""
        if s in OPERATOR_NAMES:
            return "\\" + s + " "
        if len(s) == 1 and s in SYMBOLS:
            return SYMBOLS[s] + " "
        if len(s) == 1 and ord(s) < 128:
            return "\\mathrm{" + s + "}" if el.get("mathvariant") == "normal" else s
        return math_text_run(s)
    if t == "mn":
        return math_text_run((el.text or "").strip()).replace("\\mathrm{", "{") if not re.fullmatch(
            r"[\d.,]+", (el.text or "").strip()
        ) else (el.text or "").strip()
    if t == "mo":
        s = (el.text or "").strip()
        if s in OP_MAP:
            return OP_MAP[s] + (" " if s[-1:].isalpha() or OP_MAP[s][-1:].isalpha() else "")
        if s in SYMBOLS:
            return SYMBOLS[s] + " "
        if len(s) == 1 and ord(s) < 128:
            return s
        if s == "":
            return ""
        return math_text_run(s)
    if t == "mtext":
        s = el.text or ""
        if el.get("mathvariant") == "italic":
            return math_text_run(s, italic=True)
        return math_text_run(s)
    if t == "mspace":
        return space_cmd(el.get("width"))
    if t == "msub":
        return base_of(mml(kids[0])) + "_{" + mml(kids[1]) + "}"
    if t == "msup":
        return base_of(mml(kids[0])) + "^{" + mml(kids[1]) + "}"
    if t == "msubsup":
        return base_of(mml(kids[0])) + "_{" + mml(kids[1]) + "}^{" + mml(kids[2]) + "}"
    if t == "mfrac":
        return "\\frac{" + mml(kids[0]) + "}{" + mml(kids[1]) + "}"
    if t == "msqrt":
        return "\\sqrt{" + "".join(mml(k) for k in kids) + "}"
    if t == "mroot":
        return "\\sqrt[" + mml(kids[1]) + "]{" + mml(kids[0]) + "}"
    if t in ("mover", "munder"):
        base, over = mml(kids[0]), kids[1]
        osym = "".join(over.itertext()).strip() if local(over) == "mo" else None
        if t == "mover" and osym in ACCENT_OVER and local(kids[0]) != "mo":
            return ACCENT_OVER[osym] + "{" + base + "}"
        if t == "munder" and (osym or "") in ("_", "―", "−", "-", "¯", "‾"):
            return "\\underline{" + base + "}"
        cmd = "\\overset" if t == "mover" else "\\underset"
        return cmd + "{" + mml(over) + "}{" + base + "}"
    if t == "munderover":
        return "\\overset{" + mml(kids[2]) + "}{\\underset{" + mml(kids[1]) + "}{" + mml(kids[0]) + "}}"
    if t == "mfenced":
        o, c = el.get("open", "("), el.get("close", ")")
        seps = el.get("separators", ",")
        parts = [mml(k) for k in kids]
        sep = (seps[0] if seps else "") + " "
        fix = {"{": "\\{", "}": "\\}"}
        return f"\\left{fix.get(o, o) or '.'}" + sep.join(parts) + f"\\right{fix.get(c, c) or '.'}"
    if t == "mtable":
        rows = []
        ncol = 1
        for r in kids:
            cells = [mml(c) for c in r] if local(r) == "mtr" else [mml(r)]
            ncol = max(ncol, len(cells))
            rows.append(" & ".join(cells))
        align = "l" if el.get("columnalign") == "left" or any(
            c.get("columnalign") == "left" for r in kids for c in r
        ) else "c"
        return "\\begin{array}{" + align * ncol + "}" + " \\\\ ".join(rows) + "\\end{array}"
    if t in ("mtd", "mtr"):
        return seq(kids)
    if t == "mphantom":
        return "\\phantom{" + seq(kids) + "}"
    if t == "mpadded":
        return "".join(mml(k) for k in kids)
    raise Drop(f"MathML element {t}")


def math_block(el: ET.Element, display: bool) -> str:
    body = mml(el)
    body = re.sub(r"\s+", " ", body).strip()
    body = re.sub(r"(?<!\\)%", "\\%", body)
    if not body:
        return ""
    if "\\begin{array}" in body or display:
        return "\\[" + body + "\\]"
    return "$" + body + "$"


# ---------------------------------------------------------------- CNXML prose
def tail_text(el: ET.Element) -> str:
    return prose_chars(el.tail) if el.tail else ""


def sub_sup(el: ET.Element, op: str) -> str:
    inner = math_text_run("".join(el.itertext()))
    inner = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", inner) if re.fullmatch(r"(?:\\mathrm\{[^{}]*\}|[-+])+", inner) else inner
    return "$" + op + "{" + inner + "}$"


def bracket(cell: str) -> str:
    """A cell that starts with [ after a row break would be read as the optional argument of the break."""
    return "{[}" + cell[1:] if cell.startswith("[") else cell


def table_tex(el: ET.Element) -> str:
    for x in el.iter():
        if local(x) in ("media", "image", "figure"):
            raise Drop("image in a table")
        if x.get("namest") or x.get("nameend") or x.get("morerows"):
            raise Drop("table with merged cells")
    rows = []
    for tg in el.iter(N + "tgroup"):
        for part in tg:
            if local(part) in ("thead", "tbody"):
                for r in part.findall(N + "row"):
                    rows.append((local(part) == "thead", [bracket(prose(e).strip()) for e in r.findall(N + "entry")]))
    if not rows:
        raise Drop("empty table")
    ncol = max(len(r) for _, r in rows)
    if ncol > 8 or any(len(r) != ncol for _, r in rows):
        raise Drop("table not simple")
    lines = ["\\begin{center}", "\\begin{tabular}{" + "c" * ncol + "}", "\\hline"]
    for head, cells in rows:
        lines.append(" & ".join(cells) + " \\\\" + (" \\hline" if head else ""))
    lines += ["\\hline", "\\end{tabular}", "\\end{center}"]
    return "\n".join(lines)


def prose(el: ET.Element) -> str:
    out = [prose_chars(el.text) if el.text else ""]
    for k in el:
        t = local(k)
        if t == "math":
            out.append(math_block(k, False))
        elif t == "equation":
            out.append("\n\n" + "".join(math_block(m, True) for m in k.iter() if local(m) == "math") + "\n\n")
        elif t == "sub":
            out.append(sub_sup(k, "_"))
        elif t == "sup":
            out.append(sub_sup(k, "^"))
        elif t == "emphasis":
            inner = prose(k)
            eff = k.get("effect", "")
            out.append("\\textit{" + inner + "}" if eff == "italics" else "\\underline{" + inner + "}"
                       if eff == "underline" else "\\textbf{" + inner + "}" if eff == "bold" else inner)
        elif t == "newline":
            out.append("\n\n")
        elif t in ("media", "image", "figure"):
            raise Drop("image or figure")
        elif t == "table":
            out.append("\n\n" + table_tex(k) + "\n\n")
        elif t == "list":
            items = "\n".join("\\item " + prose(i).strip() for i in k.findall(N + "item"))
            out.append("\n\\begin{itemize}\n" + items + "\n\\end{itemize}\n")
        elif t == "footnote":
            pass
        elif t in ("label", "caption", "title"):
            pass
        elif t == "link" and not "".join(k.itertext()).strip():
            raise Drop("refers to a figure or table of the book (empty link)")
        else:  # link, term, cite, quote, foreign, code ...
            out.append(prose(k))
        out.append(tail_text(k))
    return "".join(out)


def paragraphs(el: ET.Element) -> str:
    """Paragraph-level children of a <problem> or <solution>."""
    parts = []
    for k in el:
        t = local(k)
        if t == "para":
            parts.append(prose(k))
        elif t == "equation":
            parts.append("".join(math_block(m, True) for m in k.iter() if local(m) == "math"))
        elif t == "table":
            parts.append(table_tex(k))
        elif t == "list":
            wrap = ET.Element("x")
            wrap.append(k)
            parts.append(prose(wrap))
        elif t in ("media", "image", "figure"):
            raise Drop("image or figure")
        else:
            parts.append(prose(k))
    return "\n\n".join(p.strip() for p in parts if p.strip())


def plain(el: ET.Element) -> str:
    return " ".join("".join(el.itertext()).split())


def tidy(s: str) -> str:
    s = s.replace("\r", "")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\$\s+\$", " ", s)
    s = re.sub(r"(?<!\\)\$\$", "", s)
    return s.strip()


# ---------------------------------------------------------------- drop rules
REF_RE = re.compile(
    r"\b(?:Figure|Fig\.|Table|Example|Section|Chapter|Equation|Eq\.)\s*[A-Z]?\d|\bAppendix\b"
    r"|\bExercises?\s+\d"
    r"|\b(?:preceding|previous|above)\s+(?:exercise|problem|question|data|table|reaction|equation|figure|diagram|graph)"
    r"|\b(?:data|table|information|values|equation)\s+(?:above|in the (?:text|chapter))"
    r"|\bin the text\b|\b(?:given|shown|described|listed|presented)\s+(?:above|below)\b"
    r"|\b(?:following|accompanying|adjacent|this|that|the)\s+(?:diagram|figure|graph|illustration|picture|image|plot|chart|"
    r"photo|drawing|sketch|curve|curves|spectrum|spectra|apparatus|map)\b"
    r"|\b(?:below|above)\s*:?\s*$|\bshown\s+(?:below|above|here)\b|\b(?:in|from|using)\s+the\s+(?:diagram|graph|figure|plot|chart)\b",
    re.I,
)
DRAW_RE = re.compile(
    r"\b(?:draw|sketch|diagram|construct\s+(?:a|an|the)\s+(?:graph|plot|diagram|molecular\s+orbital|energy))\b"
    r"|\b(?:write|give|provide|show)\b[^.?]{0,40}\b(?:Lewis|structural)\s+(?:structure|formula|symbol|dot)"
    r"|\bLewis\s+(?:structure|symbol)s?\b|\b(?:graph|plot)\s+(?:the|these|this)\b",
    re.I,
)
EXTERNAL_RE = re.compile(
    r"\b(?:internet|web\s*site|website|web\b|online|library|simulation|PhET|interactive|YouTube|video|search\s+for|"
    r"look\s+up|research\s+the|your\s+(?:own|local|home|school)|in\s+your\s+(?:house|kitchen)|visit\s+this|"
    r"(?:design|devise|propose|plan|perform|conduct|carry\s+out)\b[^.?]{0,30}\bexperiments?|"
    r"calculator\s+program|spreadsheet|find\s+(?:an?|the)\s+(?:article|example))\b",
    re.I,
)


def scrub(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\$[^$]*\$|\\[A-Za-z]+", " ", s))


def drop_reason(stem: str) -> str | None:
    flat = scrub(stem)
    if "\\begin{tabular}" in stem:  # a table that is in the text: "the data shown here" is satisfied
        flat = re.sub(r"\b(?:shown|given|listed|presented|described)\s+(?:below|above|here)\b", " ", flat)
    if m := REF_RE.search(flat):
        return "refers to a figure, table, example or other part of the book: " + m.group(0).strip()[:30]
    if m := DRAW_RE.search(flat):
        return "asks for a drawing or structure: " + m.group(0).strip()[:30]
    if m := EXTERNAL_RE.search(flat):
        return "needs a look-up, simulation or experiment: " + m.group(0).strip()[:30]
    return None


# ---------------------------------------------------------------- load
def plain_len(s: str) -> int:
    """Length of the text without TeX markup (a formula counts by its symbols)."""
    s = re.sub(r"\\(?:begin|end)\{[^}]*\}|\\[A-Za-z]+|[\\${}^_]", "", s)
    return len(re.sub(r"\s+", " ", s).strip())


def final_sentence(sol: str) -> str | None:
    """The short key of a long worked solution: its closing sentence (or last paragraph line)."""
    paras = [p for p in re.split(r"\n\s*\n", sol.strip()) if p.strip()]
    last = paras[-1]
    maths: list[str] = []
    hidden = re.sub(r"\$[^$]*\$", lambda m: maths.append(m.group(0)) or f"\x00{len(maths) - 1}\x00", last)
    sents = [
        re.sub(r"\x00(\d+)\x00", lambda m: maths[int(m.group(1))], x)
        for x in re.split(r"(?<=[.!?])\s+(?=[A-Z(\x00])", hidden)
    ]
    cand = sents[-1].strip()
    if len(cand) < 25 and len(sents) > 1:
        cand = (sents[-2] + " " + cand).strip()
    return cand if len(cand) <= 300 and cand.count("$") % 2 == 0 and "\n" not in cand else None


def find_book(data: Path) -> Path:
    hits = sorted(data.glob("openstax_chem/*/collections/chemistry-2e.collection.xml"))
    if not hits:
        raise SystemExit(f"no openstax_chem source under {data}")
    return hits[0].parent.parent


def load(data: Path) -> tuple[list[dict], dict[str, str], int]:
    root = find_book(data)
    coll = ET.parse(root / "collections/chemistry-2e.collection.xml").getroot()
    rows, dropped, total = [], {}, 0
    seen: dict[str, str] = {}
    for ci, ch in enumerate(coll.find(C + "content").findall(C + "subcollection"), 1):
        n = 0
        for mod in ch.iter(C + "module"):
            doc = ET.parse(root / "modules" / mod.get("document") / "index.cnxml").getroot()
            for ex in doc.iter(N + "exercise"):
                total += 1
                n += 1
                sol_el = ex.find(N + "solution")
                if sol_el is not None and n % 2 == 0:
                    n += 1
                elif sol_el is None and n % 2 == 1 and ci >= 12 and False:
                    pass
                key = f"{SET} {ci}.{n}"
                try:
                    row = build(ex, sol_el, ci, n, key)
                except Drop as e:
                    dropped[key] = str(e)
                    continue
                if key in EXTRA_DROPS:
                    dropped[key] = EXTRA_DROPS[key]
                    continue
                for fld in ("latexcode", "answer", "solution", "ref_solution"):
                    for old, new in HAND_FIXES.get((key, fld), []):
                        if row[fld] is None or row[fld].count(old) != 1:
                            raise SystemExit(f"HAND FIX {key} {fld}: expected one {old!r}")
                        row[fld] = row[fld].replace(old, new)
                if row["latexcode"] in seen:
                    dropped[key] = f"same statement as {seen[row['latexcode']]}"
                    continue
                seen[row["latexcode"]] = key
                rows.append(row)
    return rows, dropped, total


def build(ex: ET.Element, sol_el: ET.Element | None, ci: int, n: int, key: str) -> dict:
    prob = ex.find(N + "problem")
    stem = tidy(paragraphs(prob))
    if not stem:
        raise Drop("empty statement")
    if why := drop_reason(stem):
        raise Drop(why)
    answer = solution = None
    ref = ""
    if sol_el is not None:
        try:
            ref = tidy(paragraphs(sol_el))
        except Drop:
            ref = ""  # an answer that is an image: the question stays without a key
        if ref and REF_RE.search(scrub(ref)):
            ref_unusable = True  # the book's answer cites a figure or table: kept only in ref_solution
        else:
            ref_unusable = False
        if ref and not ref_unusable:
            ref = tidy(re.sub(r"\n\s*\n(?=\S)", "\n\n", ref))
            flat = re.sub(r"\s*\n\s*", " ", ref)
            if (
                plain_len(ref) >= MIN_SOLUTION
                and not re.match(r"\(?[a-e]\)|amphiprotic:", ref)
                and "\\begin{" not in ref
            ):
                solution = ref  # a worked explanation: the closing sentence is the key
                answer = final_sentence(ref)
            elif "\\begin{" in ref and plain_len(ref) >= MIN_SOLUTION:
                solution = ref  # a table or list: no short key
            else:
                answer = flat
    return {
        "potd": key,
        "set": SET,
        "idx": f"{ci}.{n}",
        "orig": "",
        "source": SOURCE,
        "subsource": f"Chapter {ci}, exercise {n}",
        "latexcode": stem,
        "answer": answer,
        "solution": solution,
        "hints": None,
        "more_hints": None,
        "ref_solution": ref,
        "group": "subject",
        "effort": None,
        "image": None,
    }


# ---------------------------------------------------------------- main
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", help="dataset to import (only openstax_chem exists here)")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, dropped, total = load(a.data)
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
    reasons = collections.Counter(re.sub(r"\d+", "N", v.split(":")[0]) for v in dropped.values())
    print(
        json.dumps(
            {
                "exercises_in_source": total,
                "rows_kept_before_bank": len(rows),
                "dropped": len(dropped),
                "dropped_by_reason": reasons,
                "in_bank": len(dup),
                "to_add": len(new),
                "check_problems": len(problems),
                "with_key": sum(bool(r["answer"]) for r in new),
                "with_stored_solution": sum(bool(r["solution"]) for r in new),
                "with_ref_solution": sum(bool(r["ref_solution"]) for r in new),
            },
            default=dict,
        )
    )
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        (a.dump.with_name("dropped.json")).write_text(json.dumps(dropped, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("openstax_chem")
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
