"""
Import MMLU-Pro (STEMEZ chemistry, engineering and physics) and MMLU (chemistry, econometrics)
----------------------------------------------------------------------------------------------
Two multiple-choice benchmarks, both MIT-licensed (Amplify is private):

MMLU-Pro (huggingface.co/datasets/TIGER-Lab/MMLU-Pro, test split, data/test-00000-of-00001.parquet), 10 options
(some questions have fewer), one correct. Only the STEMEZ rows (REA "Problem Solver" textbook problems) of
  chemistry:   stemez-Chemistry, stemez-PhysicalChemistry, stemez-OrganicChemistry
  engineering: stemez-ElectricCircuits, stemez-ElectronicCommunications, stemez-Electromagnetics,
               stemez-ElectricalMachines (the EE report's E3), stemez-TransportPhenomena, stemez-HeatTransfer (C6),
               stemez-Thermodynamics, stemez-FluidMechanics, stemez-MachineDesign
  physics:     stemez-Physics, stemez-Optics, stemez-Mechanics
are read (the mechanical and physics groups added 2026-11-23, owner: "import the 304 and the physics ones").
Not read: the scibench-* rows (SciBench has its own importer), the ori_mmlu-* rows (MMLU is imported below, from
MMLU), and the business, economics, biology, psychology, genetics and computer-science rest (econometrics comes
from MMLU).
Source "MMLU-Pro", subsource empty (owner rule of 2026-11-23: no ids or category labels in the subsource);
benchmarks_map.csv keeps "<category>, <src>, question <question_id>" as the original source.

MMLU (huggingface.co/datasets/cais/mmlu, parquet per subject and split): college_chemistry,
high_school_chemistry and econometrics, every split (test, validation, dev), 4 options, one correct. With the
MMLU-Redux 2.0 annotation (huggingface.co/datasets/edinburgh-dawg/mmlu-redux-2.0, CC BY 4.0, 100 test questions
per subject, matched on the question and its options): a question Redux marks as bad question clarity, no
correct answer, multiple correct answers or unclear is dropped, and where Redux says the key is wrong its
corrected letter is used. Source "MMLU", subsource empty; the map keeps "<subject>, question <n>" (n counts test, then validation,
then dev).

Text conversion (the datasets are plain text with half-converted LaTeX): control characters that swallowed the
backslash of a command ("\\x07ngle" = \\angle) are repaired, commands glued to the next letter are split
("\\DeltaH" = \\Delta H), unicode symbols become commands, and every token with a subscript, superscript, command
or symbol is put in $...$ (runs joined across + = x -> etc.); in chemistry rows formulas become \\ce{...};
units in exponents go upright; line-end hyphens ("fol-lowing") are joined where the joined word occurs in the
dataset; % & # $ are escaped. Rows whose markup cannot be repaired (nuclide notation, OCR'd glyph commands) are
dropped (reasons in the dry-run output). Per-row repairs and drops live in mmlu_fixes.json.

Answer key: the letter. "Exactly one option is correct." is added; options "(A) ..." one per paragraph.
Rows the bank already has (same latex_hash or 85% of 5-word shingles) are skipped and listed. On --apply: backup,
insert (Uncategorized), append benchmarks_map.csv. No solutions are stored (neither dataset has any).

Usage (repo root):
  python -m app.tools.import_mmlu --data DIR --dry-run [--only mmlu_pro|mmlu] [--dump rows.json] [--set-aside]
  python -m app.tools.import_mmlu --data DIR --apply
DIR holds mmlu_pro/test.parquet, mmlu/<subject>_<split>.parquet and mmlu_redux/<subject>.arrow.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
from pathlib import Path

from app.tools.import_answer_sets import duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
SET_ASIDE_PATH = Path("app/data/appdata/mmlu_set_aside.json")

PRO_SET = "MMLU-Pro"
PRO_SRCS = {
    "chemistry": ["stemez-Chemistry", "stemez-PhysicalChemistry", "stemez-OrganicChemistry"],
    "engineering": [
        "stemez-ElectricCircuits",
        "stemez-ElectronicCommunications",
        "stemez-Electromagnetics",
        "stemez-ElectricalMachines",
        "stemez-TransportPhenomena",
        "stemez-HeatTransfer",
        "stemez-Thermodynamics",
        "stemez-FluidMechanics",
        "stemez-MachineDesign",
    ],
    "physics": ["stemez-Physics", "stemez-Optics", "stemez-Mechanics"],
}
MMLU_SET = "MMLU"
MMLU_SUBJECTS = ["college_chemistry", "high_school_chemistry", "econometrics"]
SPLITS = ["test", "validation", "dev"]
LETTERS = "ABCDEFGHIJ"
# wave -> MMLU subjects, MMLU-Pro (category, src prefixes), set-aside file. The default wave is what was imported first.
WAVES = {
    "20261123": {
        "subjects": MMLU_SUBJECTS,
        "pro": [(cat, srcs) for cat, srcs in PRO_SRCS.items()],
        "set_aside": SET_ASIDE_PATH,
    },
    "20261125": {
        "subjects": [
            "machine_learning",
            "college_computer_science",
            "high_school_computer_science",
            "electrical_engineering",
            "college_physics",
        ],
        # stemez-ComputerScience, and the TheoremQA computer-science rows (skipped by duplicates() when in the bank)
        "pro": [("computer science", ["stemez-ComputerScience", "theoremQA-"])],
        "set_aside": Path("app/data/appdata/mmlu_set_aside_20261125.json"),
    },
}
# subjects and categories whose text is code or computing notation: no ce markup, identifiers go in texttt
CODE_SUBJECTS = {"machine_learning", "college_computer_science", "high_school_computer_science", "computer science"}
CHEM_SUBJECTS = {"college_chemistry", "high_school_chemistry", "chemistry"}
# Wave 20261125 (computing, EE, physics): commands the first wave never met, allowed from that wave on
EXTRA_OK = set(
    "le ge in notin ell mathcal mathbb top lim max min sup inf argmax operatorname begin end left right quad hline odot "
    "wedge vee neg cup cap exists subseteq subset Rightarrow Leftrightarrow langle rangle lVert rVert lceil rceil lfloor "
    "rfloor neq Theta eta iota lg gcd mod bmod binom hbar not prod nu".split()
)
EXTRA_OPERATORS = {"in", "notin", "wedge", "vee", "cup", "cap", "subseteq", "subset", "Leftrightarrow", "odot", "le", "ge"}
EXTRA_UNICODE = {
    "←": r"\leftarrow ", "∧": r"\wedge ", "∨": r"\vee ", "¬": r"\neg ", "≠": r"\neq ",
    "∈": r"\in ", "∉": r"\notin ", "∪": r"\cup ", "∩": r"\cap ", "∀": r"\forall ",
    "∃": r"\exists ", "⇒": r"\Rightarrow ", "⇔": r"\Leftrightarrow ", "⊆": r"\subseteq ",
    "⊂": r"\subset ", "⊕": r"\oplus ", "Θ": r"\Theta ", "Π": r"\Pi ", "η": r"\eta ",
    "∑": r"\sum ", "∏": r"\prod ", "∂": r"\partial ", "∇": r"\nabla ", "κ": r"\kappa ",
    "χ": r"\chi ", "ξ": r"\xi ", "ζ": r"\zeta ", "ψ": r"\psi ", "≡": r"\equiv ",
    "∝": r"\propto ", "∼": r"\sim ", "∘": r"\circ ", "⋆": r"\ast ", "∗": r"\ast ",
    "↔": r"\leftrightarrow ", "Φ": r"\Phi ", "Γ": r"\Gamma ", "Λ": r"\Lambda ", "Ψ": r"\Psi ",
    "́": "", "�": "",
}
EXTRA_RE = re.compile("[" + "".join(EXTRA_UNICODE) + "]")
# code shown in a verbatim block or \texttt: symbols the monospace font may lack become ASCII
ASCII_FOLD = {"←": "<-", "→": "->", "≤": "<=", "≥": ">=", "≠": "!=", "×": "*", "−": "-",
              "–": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "\u00a0": " ", "∧": "AND",
              "∨": "OR", "¬": "NOT "}
CODE_LINE_RE = re.compile(
    r"[{};]\s*$|^\s*[{}]|←|/\*|\*/|^\s*(?:IF|FOR|REPEAT|PROCEDURE|RETURN|DISPLAY|APPEND|ELSE|WHILE|UNTIL|INSERT|REMOVE|"
    r"public|private|return|int|if|for|while)\b|^\s*Line \d+:"
)
KEYWORD_RE = re.compile(
    r"\b(?:DIMENSION|SUBROUTINE|FUNCTION|INTEGER|REAL|CONTINUE|RETURN|END|DO|IF|THEN|ELSE|WRITE|READ|GO TO|GOTO|BEGIN|"
    r"PROGRAM|VAR|WHILE|PRINT|FORMAT|STOP|CALL|DATA|LET|NEXT|FOR|DCL|DECLARE|INPUT)\b"
)
MATH_FUNCS = {"log", "ln", "sin", "cos", "tan", "exp", "lg", "sqrt", "max", "min", "sup", "inf", "gcd", "lim", "det", "arg"}
TT_ESCAPES = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "%": r"\%", "&": r"\&", "#": r"\#", "_": r"\_",
              "^": r"\^{}", "~": r"\~{}"}

_FIXES = json.loads(Path(__file__).with_name("mmlu_fixes.json").read_text(encoding="utf-8"))
HAND_FIXES: dict[tuple[str, str], list[tuple[str, str]]] = {}
for _e in _FIXES["fixes"]:
    HAND_FIXES.setdefault((_e["key"], _e["field"]), []).extend(tuple(p) for p in _e["fixes"])
DROPS: dict[str, str] = dict(_FIXES["dropped"])

# ---------------------------------------------------------------------------------------------------------
# Text conversion
# ---------------------------------------------------------------------------------------------------------
CTRL = {"\x07": "a", "\x08": "b", "\x0b": "v", "\x0c": "f", "\t": "t", "\r": "r"}
CTRL_RE = re.compile(r"[\x07\x08\x0b\x0c\t\r](?=[A-Za-z])")

ALLOWED = set(
    "alpha beta gamma delta epsilon varepsilon zeta eta theta lambda mu nu xi pi rho sigma tau phi psi omega "
    "Gamma Delta Theta Lambda Pi Sigma Phi Psi Omega rightarrow leftarrow rightleftarrows leftrightarrow "
    "Rightarrow infty sum int surd sqrt pm times cdot leq geq sim approx equiv bullet angle oplus vert frac "
    "AA partial nabla propto ldots circ mathrm text ce hat bar dot ast sin cos tan ln log exp to prime "
    "uparrow downarrow rightleftharpoons oint cong mid forall neq ll gg "
    # physics groups (2026-11-23): standard commands the chemistry and EE rows never needed
    "upsilon Upsilon varphi vartheta kappa chi Xi ddot".split()
)
# commands the datasets spell in a form neither LaTeX nor KaTeX knows
RENAME = {
    "textphi": "phi",
    "texttheta": "theta",
    "textasteriskcentered": "ast",
    "textbullet": "cdot",
    "ding": None,  # \ding{217}: handled below
}
OPERATORS = {
    "times",
    "cdot",
    "pm",
    "rightarrow",
    "rightleftarrows",
    "leftrightarrow",
    "leq",
    "geq",
    "sim",
    "approx",
    "equiv",
    "leftarrow",
    "Rightarrow",
}
UNICODE = {
    "\u00d7": r"\times ",
    "\u00b7": r"\cdot ",
    "\u2022": r"\cdot ",
    "\u22c5": r"\cdot ",
    "\u03a9": r"\Omega ",
    "\u2126": r"\Omega ",
    "\u2206": r"\Delta ",
    "\u0394": r"\Delta ",
    "\u03c0": r"\pi ",
    "\u03c9": r"\omega ",
    "\u03b5": r"\epsilon ",
    "\u03b2": r"\beta ",
    "\u03b8": r"\theta ",
    "\u03b1": r"\alpha ",
    "\u03bb": r"\lambda ",
    "\u03bc": r"\mu ",
    "\u00b5": r"\mu ",
    "\u03c6": r"\phi ",
    "\u03c3": r"\sigma ",
    "\u03c1": r"\rho ",
    "\u03c4": r"\tau ",
    "\u03bd": r"\nu ",
    "\u03b4": r"\delta ",
    "\u03b3": r"\gamma ",
    "\u03a3": r"\Sigma ",
    "\u221e": r"\infty ",
    "\u00b1": r"\pm ",
    "\u2264": r"\leq ",
    "\u2265": r"\geq ",
    "\u2248": r"\approx ",
    "\u2192": r"\rightarrow ",
    "\u21cc": r"\rightleftarrows ",
    "\u2220": r"\angle ",
    "\u00c5": r"\AA ",
    "\u212b": r"\AA ",
    "\u2212": "-",
    "\u2013": "-",
    "\u2014": "---",
    "\u00b2": "^2",
    "\u00b3": "^3",
    "\u00b9": "^1",
    "\u2070": "^0",
    "\u207b": "^-",
    "\u207a": "^+",
    "\u2080": "_0",
    "\u2081": "_1",
    "\u2082": "_2",
    "\u2083": "_3",
    "\u2084": "_4",
    "\u00b0": "^\\circ",
    "\u00bd": "1/2",
    "\u00bc": "1/4",
    "\u00be": "3/4",
    "\u00a0": " ",
    "\u2009": " ",
    "\u201c": "``",
    "\u201d": "''",
    "\u2018": "`",
    "\u2019": "'",
    "\u2026": "...",
    "\u0432": "v",
}
OPERATORS |= EXTRA_OPERATORS  # none of them is in ALLOWED: the first wave never meets them
SYMBOL_RE = re.compile("[" + "".join(UNICODE) + "]")
COMBINING = {"\u0302": "hat", "\u0304": "bar", "\u0305": "bar", "\u0307": "dot"}
# a letter with a combining mark, or the precomposed forms the data uses
PRECOMPOSED = {"\u1e91": ("hat", "z"), "\u1e41": ("dot", "m")}
COMB_RE = re.compile("([A-Za-z\u03b1-\u03c9])([\u0302\u0304\u0305\u0307])")
WORD_ELEMENT_EXCLUDE = {"A", "I", "In", "It", "If", "Is", "As", "At", "An", "Be", "By", "Do", "He", "Me", "My",
                        "No", "Of", "On", "Or", "So", "To", "Up", "We", "Go", "Us", "Ha", "Ho", "Ne", "Ni"}
ELEMENT_OK = {"Ni", "Ne", "No", "He"}


def repair_commands(s: str, ext: bool = False) -> str:
    """Control characters that ate a backslash, glued commands, renamed commands."""
    if ext:
        s = re.sub(r"\\le(?![A-Za-z])", r"\\leq", s)
        s = re.sub(r"\\ge(?![A-Za-z])", r"\\geq", s)
        s = re.sub(r"\\arg(min|max)(?![A-Za-z])", r"\\operatorname{arg\\,\1}", s)
        s = re.sub(r"\\norm\{([^{}]*)\}", r"\\lVert \1\\rVert", s)
    s = CTRL_RE.sub(lambda m: "\\" + CTRL[m.group(0)], s)
    s = re.sub(r"\\textquotedblleft\s*", "``", s)
    s = re.sub(r"\\textquotedblright\s*", "''", s)
    s = re.sub(r"\\ding\{\d+\}", r"\\rightarrow ", s)
    s = s.replace(r"\cup", "u").replace(r"\Elzbar", "h")

    def fix(m: re.Match) -> str:
        name = m.group(1)
        name = RENAME.get(name, name) if name in RENAME else name
        if name is None:
            return m.group(0)
        if name in ALLOWED or (ext and name in EXTRA_OK):
            return "\\" + name
        for key in ("textphi", "texttheta", "textasteriskcentered", "textbullet"):
            if name.startswith(key) and len(name) > len(key):
                return "\\" + RENAME[key] + " " + name[len(key) :]
        for k in range(len(name) - 1, 1, -1):  # longest known command that starts the word
            if name[:k] in ALLOWED:
                return "\\" + name[:k] + " " + name[k:]
        return "\\" + name

    return re.sub(r"\\([A-Za-z]+)", fix, s)


def unicode_to_latex(s: str, ext: bool = False) -> str:
    s = COMB_RE.sub(lambda m: "\\" + COMBINING[m.group(2)] + "{" + m.group(1) + "}", s)
    for ch, (cmd, base) in PRECOMPOSED.items():
        s = s.replace(ch, "\\" + cmd + "{" + base + "}")
    s = re.sub("\u00b0([CFK])(?![A-Za-z])", r"^{\\circ}\\mathrm{\1}", s)
    s = s.replace("\u00b0", "^{\\circ}")
    s = re.sub(
        "\u221a\\s*(?:\\(([^()]*)\\)|([A-Za-z0-9.]+))", lambda m: "\\sqrt{" + (m.group(1) or m.group(2)) + "}", s
    )
    s = s.replace("\u221a", "\\surd ")
    if ext:
        s = EXTRA_RE.sub(lambda m: EXTRA_UNICODE[m.group(0)], s)
    return SYMBOL_RE.sub(lambda m: UNICODE[m.group(0)], s)




NUMBER = re.compile(r"^[+-]?(?:\d+[.,]?\d*|[.]\d+)$")
PUNCT_TAIL = ",.;:?!"
FORMULA_RE = re.compile(r"^(?:\^\{\d+\})?\d*(?:(?:[A-Z][a-z]?|\([A-Za-z0-9]+\))\d*)+(?:\((?:g|l|s|aq)\))?(?:\^\d*[+-])?$")
FUNCTIONS = {"sin", "cos", "tan", "ln", "log", "exp"}
OP_TOKENS = {"+", "=", "-", "/", "<", ">", "*"}
PH_RE = re.compile("\x01(\\d+)\x02")
PT_RE = re.compile("\x03(\\d+)\x04")
LABEL_RE = re.compile(r"^\(?[a-z]\)$|^\([ivx]+\)$")
QCHARS_RE = re.compile(r"^[\[\](){}A-Za-z0-9.*/+\-=|\\]*$")


def brace_scripts(t: str) -> str:
    t = re.sub(r"(\d)-\^(\d+)", r"\1^{-\2}", t)  # 10-^11 = 10^-11
    t = re.sub(r"\^\(([^()]*)\)", r"^{\1}", t)
    t = re.sub(r"\^(-?\d+(?:\.\d+)?)", r"^{\1}", t)
    t = re.sub(r"\^([+-])(?![\d{])", r"^{\1}", t)
    t = re.sub(r"_(\d+)", r"_{\1}", t)
    t = re.sub(r"_([a-z]{2,})", r"_{\1}", t)
    return t


def upright_words(t: str) -> str:
    """Words of two or more letters inside math go upright (units, names); function names get their command."""
    out = []
    for p in re.split(r"(\\[A-Za-z]+|\\mathrm\{[^{}]*\}|\\ce\{[^{}]*\})", t):
        if p.startswith("\\"):
            out.append(p)
        else:
            out.append(
                re.sub(
                    r"[A-Za-z]{2,}",
                    lambda m: ("\\" + m.group(0) + " ") if m.group(0) in FUNCTIONS else "\\mathrm{" + m.group(0) + "}",
                    p,
                )
            )
    return "".join(out)


def formula_to_ce(core: str) -> str | None:
    """\\ce{...} for a chemical-formula token such as NH_4^+, Mg(OH)_2, H_2S(g); None when it is not one."""
    if "_" not in core and "^" not in core:
        return None
    t = re.sub(r"_\{?([^{}]*)\}?", r"\1", core)
    t = re.sub(r"\^\{?([^{}]*)\}?", r"^\1", t)
    t = re.sub(r"^\^(\d+)(?=[A-Z])", r"^{\1}", t)
    if not FORMULA_RE.match(t):
        return None
    return "\\ce{" + t + "}"


def mathify(tok: str, chem: bool) -> str:
    lb = rb = ""
    core = tok
    while core.startswith("(") and core.count("(") > core.count(")"):
        lb += "("
        core = core[1:]
    while core.endswith(")") and core.count(")") > core.count("("):
        rb = ")" + rb
        core = core[:-1]
    core = re.sub(r"_(?![\w{\\(\x01])", "", core)
    ce = formula_to_ce(core) if chem else None
    if ce:
        return lb + ce + rb
    t = lb + core + rb
    t = re.sub(r"_([A-Za-z])([A-Za-z]+)(?=[_^])", r"_{\1}\2", t)  # W_iM_i: the first subscript is one letter
    t = re.sub(r"^\^(\d+)(?=[A-Z])", r"{}^{\1}", t)  # isotope: ^210Po
    t = t.replace("%", r"\%")
    t = brace_scripts(t)
    t = re.sub(r"\^\\circ([CFK])(?![A-Za-z])", r"^{\\circ}\\mathrm{\1}", t)
    t = re.sub(r"\^\\circ(?![A-Za-z{])", r"^{\\circ}", t)
    t = upright_words(t)
    t = re.sub(r"(?<=[}\w])-(?=\\mathrm|\^\{\\circ\})", r"\\cdot ", t)  # Btu/hr-ft^2-F: a unit product
    return t


def kind(core: str, chem: bool) -> str:
    """M mathy token, O operator, N number, F function name, E element-like word, Q short math-ish token, T text."""
    if "\x03" in core:
        return "T"
    m = re.fullmatch(r"\\([A-Za-z]+)\s*", core)
    if m and m.group(1) in OPERATORS:
        return "O"
    if core in OP_TOKENS:
        return "O"
    if NUMBER.match(core):
        return "N"
    if core in FUNCTIONS:
        return "F"
    if re.search(r"[\\_^\x01]", core):
        return "M"
    if chem and re.fullmatch(r"[A-Z][a-z]", core) and core not in WORD_ELEMENT_EXCLUDE:
        return "E"
    if (
        QCHARS_RE.match(core)
        and not re.search(r"[A-Za-z]{3,}", core)
        and not LABEL_RE.match(core)
        and (re.search(r"[\[\](){}\d]", core) or re.fullmatch(r"[A-Za-z]", core))
    ):
        return "Q"
    return "T"


def escape_text(t: str) -> str:
    t = re.sub(r"(?<!\\)([%&#$])", r"\\\1", t)
    t = re.sub(r"(?<!\\)\^", r"\\^{}", t)
    t = re.sub(r"(?<!\\)~", r"\\~{}", t)
    t = t.replace("|", "$|$")
    return t


def dehyphenate(s: str, vocab: collections.Counter) -> str:
    """Join "fol-lowing" where the joined word occurs in the dataset and a part is no word of its own."""

    def join(m: re.Match) -> str:
        a, b = m.group(1), m.group(2)
        whole = (a + b).lower()
        if vocab[whole] >= 2 and (vocab[a.lower()] < 3 or vocab[b.lower()] < 3):
            return a + b
        return m.group(0)

    return re.sub(r"(?<![\w\\])([A-Za-z]{2,})-([a-z]{2,})(?![\w-])", join, s)


def protect(s: str, store: list[str], ext: bool = False) -> str:
    """Math the data already has (\\( \\), $ $, \\frac{}{}, ^{...}) goes behind placeholders."""

    def put(inner: str) -> str:
        store.append(inner)
        return f"\x01{len(store) - 1}\x02"

    s = re.sub(r"_{2,}", lambda m: put(r"\_\_\_\_"), s)  # a fill-in blank
    s = re.sub(r"\\\((.*?)\\\)", lambda m: put(m.group(1).strip()), s, flags=re.S)
    if ext:
        s = re.sub(r"\$\$(.*?)\$\$", lambda m: put("\\[" + m.group(1).strip() + "\\]"), s, flags=re.S)
    s = re.sub(r"\$([^$]*)\$", lambda m: put(m.group(1).strip()), s)
    if ext:  # a table the data left outside math: an array in a display
        s = re.sub(
            r"\\begin\{(?:tabular|array)\}(\{[^{}]*\})(.*?)\\end\{(?:tabular|array)\}",
            lambda m: put("\\[\\begin{array}" + m.group(1).replace("|", "") + m.group(2) + "\\end{array}\\]"),
            s,
            flags=re.S,
        )
    s = re.sub(r"\\frac\s*\{[^{}]*\}\s*\{[^{}]*\}", lambda m: put(m.group(0)), s)
    s = re.sub(r"\\(?:sqrt|text|mathrm|textbf|hat|bar|dot)\s*\{[^{}]*\}", lambda m: put(m.group(0)), s)
    s = re.sub(r"[\^_]\{[^{}]*\}", lambda m: put(m.group(0)), s)
    return s


# adjacent tokens that may share one $...$ (numbers and element symbols only next to an operator)
def can_join(a: str, b: str) -> bool:
    if a in "NE" or b in "NE":
        return a == "O" or b == "O"
    return True


def expand(t: str, store: list[str]) -> str:
    return PH_RE.sub(lambda m: store[int(m.group(1))], t)


def convert(
    text: str, chem: bool = False, vocab: collections.Counter | None = None, code: bool = False, ext: bool = False
) -> str:
    s = repair_commands(text.replace("\r\n", "\n"), ext)
    s = re.sub(r"(?<=[a-z]{2})\\(?=[A-Za-z])", r" \\", s)  # "and\Delta": a command glued to a word
    s = re.sub(r"(?<=[a-z0-9)])[.](?=[A-Z][a-z])", ". ", s)  # "C.Find": sentence end glued to the next one
    s = unicode_to_latex(s, ext)
    store: list[str] = []
    s = protect(s, store, ext)
    if code:
        s = code_spans(s, store)
    s = re.sub(r"(?<!\\)([{}])", r"\\\1", s)  # braces the data prints literally
    if vocab is not None:
        s = dehyphenate(s, vocab)
    toks = []  # [ws_before, core, tail, kind]
    ws = ""
    for k, p in enumerate(re.split(r"(\s+)", s.strip())):
        if k % 2:
            ws = p
        elif p:
            tail = ""
            while p and p[-1] in PUNCT_TAIL:
                tail = p[-1] + tail
                p = p[:-1]
            if not p:
                toks.append([ws, tail, "", "T"])
            else:
                toks.append([ws, p, tail, kind(p, chem)])
            ws = ""
    n = len(toks)
    runs = {}
    k = 0
    while k < n:
        if toks[k][3] not in "MONEQF":
            k += 1
            continue
        b = k
        while b + 1 < n and not toks[b][2] and toks[b + 1][3] in "MONEQF" and can_join(toks[b][3], toks[b + 1][3]):
            b += 1
        a, e = k, b
        changed = True
        while changed and a <= e:
            changed = False
            kd = toks[a][3]
            nxt = toks[a + 1][3] if a < e else ""
            if kd == "O" or (kd in "NE" and nxt != "O") or (kd == "Q" and re.fullmatch(r"[A-Za-z]", toks[a][1]) and nxt != "O"):
                a += 1
                changed = True
            kd = toks[e][3]
            prv = toks[e - 1][3] if e > a else ""
            if a <= e and (
                kd in "OF"
                or (kd in "NE" and prv != "O")
                or (kd == "Q" and re.fullmatch(r"[A-Za-z]", toks[e][1]) and prv != "O")
            ):
                e -= 1
                changed = True
        if a <= e and any(toks[j][3] == "M" or (ext and not code and toks[j][1] == "=") for j in range(a, e + 1)):
            runs[a] = e
        k = b + 1
    out = []
    j = 0
    while j < n:
        ws, core, tail, kd = toks[j]
        if j in runs:
            e = runs[j]
            segs = []
            for i in range(j, e + 1):
                c, kk = toks[i][1], toks[i][3]
                if kk == "F":
                    segs.append("\\" + c)
                elif kk == "E":
                    segs.append("\\ce{" + c + "}")
                elif kk == "M":
                    segs.append(mathify(c, chem))
                else:
                    segs.append(c)
            # a script that follows another token's script ("ft^2 °F") needs an empty base
            segs = [("{}" + x if re.match(r"[\^_]", expand(x, store)) else x) for x in segs]
            body = re.sub(r"(?<!\\)([%#&])", r"\\\1", " ".join(segs))
            out.append(ws + "$" + body + "$" + toks[e][2])
            j = e + 1
        else:
            if kd == "O" and core in ({"<", ">"} if ext else {"<", ">", "="}) or (kd == "O" and core.startswith("\\")):
                out.append(ws + "$" + core + "$" + tail)
            else:
                out.append(ws + escape_text(core + tail))
            j += 1
    res = "".join(out)
    for _ in range(3):
        res = PH_RE.sub(lambda m: store[int(m.group(1))], res)
        res = PT_RE.sub(lambda m: store[int(m.group(1))], res)
    return re.sub(r"([\^_]\{[^{}]*\})(?=[\^_])", r"\1{}", res)  # two scripts in a row: 10^{-4}^{\circ}


def tt(s: str) -> str:
    """Code or an identifier as a texttt: ASCII-folded, every LaTeX special escaped."""
    s = "".join(ASCII_FOLD.get(c, c) for c in s)
    return "\\texttt{" + "".join(TT_ESCAPES.get(c, c) for c in s) + "}"


def code_spans(s: str, store: list[str]) -> str:
    """Code mode: identifiers, calls and operators of programs go behind text placeholders (a texttt),
    big-O terms and graph edge sets behind math placeholders; nothing of them reaches the chemistry/physics converter."""

    def put_m(x: str) -> str:
        store.append(x)
        return f"\x01{len(store) - 1}\x02"

    def put_t(x: str) -> str:
        store.append(tt(x))
        return f"\x03{len(store) - 1}\x04"

    edge = r"<\s*[A-Za-z0-9]+\s*,\s*[A-Za-z0-9]+\s*>"
    s = re.sub(
        rf"(?:[A-Z]\s*=\s*)?\{{\s*(?:{edge}\s*,?\s*)+\}}",
        lambda m: put_m(
            re.sub(r"<\s*([A-Za-z0-9]+)\s*,\s*([A-Za-z0-9]+)\s*>", lambda x: "\\langle " + x.group(1) + "," + x.group(2) + "\\rangle ", m.group(0))
            .replace("{", r"\{")
            .replace("}", r"\}")
        ),
        s,
    )
    s = re.sub(r"<\s*([A-Z0-9]+)\s*,\s*([A-Z0-9]+)\s*>", lambda m: put_m(rf"\langle {m.group(1)},{m.group(2)}\rangle"), s)

    def bigo(m: re.Match) -> str:
        inner = re.sub(r"\blog\b", lambda _: "\\log", m.group(2))
        inner = re.sub(r"\bsqrt\(([^()]*)\)", lambda x: "\\sqrt{" + x.group(1) + "}", inner)
        inner = re.sub(r"\^(\w+|\([^()]*\))", lambda x: "^{" + x.group(1).strip("()") + "}", inner)
        return put_m(m.group(1).strip() + "(" + inner.replace("*", r"\cdot ") + ")")

    s = re.sub(r"(?<![\w\\])(O|\\Omega ?|\\Theta ?)\(((?:[^()\x01-\x04]|\([^()]*\))*)\)", bigo, s)
    s = re.sub(
        r"(?<!\w)\w+(?:\s*(?:->|<-)\s*\w+)+",
        lambda m: put_m(re.sub(r"\s*->\s*", lambda _: " \\rightarrow ", re.sub(r"\s*<-\s*", lambda _: " \\leftarrow ", m.group(0)))),
        s,
    )
    s = re.sub(r"(?<![\w\\\x01-\x04])[A-Za-z]\w*_[A-Za-z]{2,}\w*", lambda m: put_t(m.group(0)), s)

    def call(m: re.Match) -> str:
        if m.group(1).lower() in MATH_FUNCS or m.group(2).strip() in {"s", "es", "ies", "are", "is"}:
            return m.group(0)
        return put_t(m.group(0))

    s = re.sub(r"(?<![\w\\\x01-\x04])([A-Za-z_]\w+)\(((?:[^()\x01-\x04]|\([^()]*\))*)\)", call, s)
    return re.sub(
        r"(?<![\w<>=!&|*/+\-])(<<|>>|==|!=|<=|>=|\+\+|\*\*|//|&&|\|\|)(?![\w<>=!&|*/+\-])", lambda m: put_t(m.group(0)), s
    )


def is_code_line(ln: str) -> bool:
    """An indented line of a program; a sentence that merely mentions code is prose."""
    return bool(CODE_LINE_RE.search(ln)) and not (len(ln.split()) >= 6 and re.search(r"[.?:]\s*$", ln))


def code_like(t: str) -> bool:
    """An option that is a program fragment (FORTRAN, Pascal, ...): two different keywords."""
    return len(t) >= 15 and len(set(KEYWORD_RE.findall(t))) >= 2


def convert_lines(text: str, chem: bool, vocab: collections.Counter | None, code: bool) -> str:
    """The statement of a wave-20261125 row: every source line is a paragraph, indented code lines a verbatim block."""
    lines = text.replace("\r\n", "\n").split("\n")
    out, k = [], 0
    while k < len(lines):
        ln = lines[k]
        if not ln.strip():
            k += 1
        elif code and ln[:1].isspace() and is_code_line(ln):
            blk = [ln]
            k += 1
            while k < len(lines) and lines[k][:1].isspace() and is_code_line(lines[k]):
                blk.append(lines[k])
                k += 1
            body = "\n".join(blk)
            ind = min(len(x) - len(x.lstrip()) for x in blk)
            body = "\n".join(x[ind:].rstrip() for x in blk)
            body = "".join(ASCII_FOLD.get(c, c) for c in body)
            if body.isascii() and not re.search(r"[$\\]", body) and body.count("{") == body.count("}"):
                out.append("\\begin{verbatim}\n" + body + "\n\\end{verbatim}")
            else:
                out += [tt(x[ind:].rstrip()) for x in blk]
        else:
            m = re.match(r"^\s*[\u00b0\u2022]\s*(.*)$", ln)
            out.append(("$\\bullet$ " + convert(m.group(1), chem, vocab, code, True)) if m else convert(ln.strip(), chem, vocab, code, True))
            k += 1
    return "\n\n".join(out)


def unknown_commands(text: str, ext: bool = False) -> set[str]:
    ok = ALLOWED | EXTRA_OK | {"texttt", "textbackslash"} if ext else ALLOWED
    return {m for m in re.findall(r"\\([A-Za-z]+)", text)} - ok - {"ce", "mathrm", "textbf"}


# ---------------------------------------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------------------------------------
NUCLIDE_RE = re.compile(r"\(\s*\^\d+\s*_|\(\s*_\s*-?\d+\s*\^|\^\d+_\d+|\^\d+\s+_\d+")
BAD_MARKUP = re.compile(r"\\(?:cyr\w*|rule|Elz\w*|textphi)|\\ding")


def stem_with_options(stem: str, opts: list[str]) -> str:
    parts = [stem, "Exactly one option is correct."] + [f"({LETTERS[i]}) {o}" for i, o in enumerate(opts)]
    return "\n\n".join(parts)


def make_row(set_: str, potd: str, idx: str, source: str, subsource: str, raw_q: str, raw_opts: list[str],
             letter: str, chem: bool, vocab: collections.Counter, code: bool = False,
             ext: bool = False) -> tuple[dict | None, str | None]:
    raw = " ".join([raw_q, *raw_opts])
    if BAD_MARKUP.search(repair_commands(raw, ext)):
        return None, "OCR'd glyph command or drawing-dependent markup in the text"
    if NUCLIDE_RE.search(raw) and chem:
        return None, "nuclide notation the data garbled"
    if ext:  # wave 20261125: source lines are paragraphs, program fragments are code
        stem = convert_lines(raw_q, chem, vocab, code)
        opts = [
            tt(norm(o)) if code and code_like(o) else convert(norm(o), chem, vocab, code, True) for o in raw_opts
        ]
    else:
        stem = convert(raw_q, chem, vocab, code)
        opts = [convert(o, chem, vocab, code) for o in raw_opts]
    text = stem_with_options(stem, opts)
    row = {
        "potd": potd,
        "set": set_,
        "idx": idx,
        "orig": subsource,  # category, src and id: kept only in the map
        "source": source,
        "subsource": None,  # owner rule of 2026-11-23: a subsource never identifies a question
        "latexcode": text,
        "answer": letter,
        "solution": None,
        "hints": None,
        "more_hints": None,
        "ref_solution": "",
        "group": "subject",
        "effort": None,
        "image": None,
    }
    for fld in ("latexcode",):
        for old, new in HAND_FIXES.get((potd, fld), []):
            if row[fld].count(old) != 1:
                raise SystemExit(f"HAND FIX {potd} {fld}: expected one {old!r}")
            row[fld] = row[fld].replace(old, new)
    bad = unknown_commands(row["latexcode"], ext)
    if bad:
        return None, "command neither LaTeX nor KaTeX knows: " + ", ".join(sorted(bad))
    return row, None


def read_parquet(path: Path) -> list[dict]:
    import pyarrow.parquet as pq

    return pq.read_table(path).to_pylist()


def read_arrow(path: Path) -> list[dict]:
    import pyarrow as pa

    return pa.ipc.open_stream(path).read_all().to_pylist()


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def load_pro(data: Path, wave: str = "20261123") -> tuple[list[dict], dict[str, str]]:
    allrows = read_parquet(data / "mmlu_pro" / "test.parquet")
    vocab: collections.Counter = collections.Counter()
    for r in allrows:
        for t in [r["question"], *r["options"]]:
            vocab.update(w.lower() for w in re.findall(r"(?<![\w-])[A-Za-z]{3,}(?![\w-])", t))
    rows, dropped = [], {}
    for cat, srcs in WAVES[wave]["pro"]:
        for r in allrows:
            if r["category"] != cat or not any(r["src"] == x or (x.endswith("-") and r["src"].startswith(x)) for x in srcs):
                continue
            potd = f"{PRO_SET} {r['question_id']}"
            if potd in DROPS:
                dropped[potd] = DROPS[potd]
                continue
            row, why = make_row(
                PRO_SET, potd, str(r["question_id"]), "MMLU-Pro", f"{cat}, {r['src']}, question {r['question_id']}",
                r["question"], list(r["options"]), r["answer"], cat in CHEM_SUBJECTS, vocab, cat in CODE_SUBJECTS,
                wave != "20261123",
            )
            if row is None:
                dropped[potd] = why
            else:
                rows.append(row)
    return rows, dropped


def load_mmlu(data: Path, wave: str = "20261123") -> tuple[list[dict], dict[str, str]]:
    vocab: collections.Counter = collections.Counter()
    rows, dropped = [], {}
    for subject in WAVES[wave]["subjects"]:
        redux = {
            (norm(x["question"]), tuple(norm(c) for c in x["choices"])): x
            for x in read_arrow(data / "mmlu_redux" / f"{subject}.arrow")
        }
        n = 0
        items = [(sp, r) for sp in SPLITS for r in read_parquet(data / "mmlu" / f"{subject}_{sp}.parquet")]
        for _, r in items:
            vocab.update(w.lower() for w in re.findall(r"(?<![\w-])[A-Za-z]{3,}(?![\w-])", r["question"]))
        for sp, r in items:
            n += 1
            potd = f"{MMLU_SET} {subject} {n}"
            if potd in DROPS:
                dropped[potd] = DROPS[potd]
                continue
            letter = "ABCD"[r["answer"]]
            x = redux.get((norm(r["question"]), tuple(norm(c) for c in r["choices"])))
            if x is not None and x["error_type"] != "ok":
                et = x["error_type"]
                fixed = str(x["correct_answer"] or "").strip()
                if et == "wrong_groundtruth" and re.fullmatch(r"[A-D]", fixed):
                    letter = fixed
                else:
                    dropped[potd] = f"MMLU-Redux: {et}"
                    continue
            row, why = make_row(
                MMLU_SET, potd, f"{subject}/{sp}/{n}", "MMLU", f"{subject.replace('_', ' ')}, question {n}",
                r["question"], list(r["choices"]), letter, subject in CHEM_SUBJECTS, vocab, subject in CODE_SUBJECTS,
                wave != "20261123",
            )
            if row is None:
                dropped[potd] = why
            else:
                rows.append(row)
    return rows, dropped


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--only", choices=["mmlu_pro", "mmlu"])
    p.add_argument("--wave", choices=sorted(WAVES), default="20261123", help="which subjects and categories to import")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    set_aside_path = WAVES[a.wave]["set_aside"]
    rows, dropped = [], {}
    for name, fn in (("mmlu_pro", load_pro), ("mmlu", load_mmlu)):
        if a.only in (None, name):
            r_, d_ = fn(a.data, a.wave)
            rows += r_
            dropped.update(d_)
    # the same question twice inside the datasets: keep the first
    from app.tools.import_answer_sets import NEAR, shingles

    seen: list[tuple[set, str]] = []
    keep = []
    for r in rows:
        g_ = shingles(r["latexcode"])
        twin = next((k for s_, k in seen if len(g_ & s_) / max(len(g_), 1) >= NEAR), None)
        if twin:
            dropped[r["potd"]] = f"near-duplicate of {twin} in these datasets"
            continue
        seen.append((g_, r["potd"]))
        keep.append(r)
    rows = keep
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
        set_aside_path.write_text(
            json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {set_aside_path}")
        problems = check(new)
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
                "by_source": collections.Counter(r["orig"].split(", question")[0].rsplit(",", 1)[0] for r in new),
            },
            default=dict,
            indent=1,
        )
    )
    for k, v in sorted(dropped.items()):
        print("dropped", k, v)
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("mmlu")
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
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}")


if __name__ == "__main__":
    main()
