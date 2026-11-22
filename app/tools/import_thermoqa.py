"""Import ThermoQA (huggingface.co/datasets/olivenet/thermoqa, CC BY 4.0): 293 engineering-thermodynamics
problems (property lookups, single components, power and refrigeration cycles) generated from templates
with random numbers; the answers come from CoolProp 7.2.0 (IAPWS-IF97 for water, the IIR reference state
for R-134a, ideal-gas air with constant or temperature-dependent specific heats). Owner-approved 2026-11-22.

What is kept and how it is written:
  * a template (metadata.template_id) has at most 2 rows (the harder difficulty first, then the lower id);
    T1-SF-012 is left out (the same given as T1-SF-006);
  * the statement is the dataset's plain-text wording in LaTeX ($T_1 = 500^\\circ\\mathrm{C}$, \\dot{m}, \\eta,
    subscripts, upright units); its "Report your answers as / Present your final answers in the following
    format" block becomes one line listing what to find, in that order;
  * one sentence says where the properties come from, since the statements give only operating
    conditions (water: steam tables; R-134a: the IIR reference state; variable-cp air: the ideal-gas air
    table convention; constant-cp air: h = c_p T and s = 0 at 298.15 K, 0.1 MPa, R = 0.287);
  * the key lists every target in that order, "(1) $h_1 = 3385.7\\ \\mathrm{kJ/kg}$; (2) ...", rounded to 5
    significant figures; a phase is a word ("phase: superheated vapour"). The dataset's tolerance is not
    mentioned. Targets without a usable value (the energy-balance-error checks, one combined second-law
    efficiency the data has no value for) are left out of both.
No solutions, no figures; all rows are group "subject" (Thermodynamics, solved by the subjects solver).

Usage (repo root):
  python -m app.tools.import_thermoqa --data DIR --dry-run [--dump rows.json]
  python -m app.tools.import_thermoqa --data DIR --apply          (the owner's machine)
"""

from __future__ import annotations

import argparse
import base64
import collections
import csv
import json
import re
import sqlite3
import unicodedata
from decimal import Decimal
from pathlib import Path

from app.tools.import_answer_sets import TEXIMAGES, duplicates
from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash

SET = "ThermoQA"
MAP_PATH = Path("app/data/appdata/benchmarks_map.csv")
ASSIGNMENTS = Path("pipeline/benchmarks_assignments.json")
SOLUTIONS_PATH = Path("app/data/appdata/benchmarks_solutions.json")
FIXES_PATH = Path(__file__).with_name("thermoqa_fixes.json")
TIERS = ("tier1_properties", "tier2_components", "tier3_cycles")
PER_TEMPLATE = 2
SKIP = {"T1-SF-012": "the same given as T1-SF-006 (same state, reworded)"}
RANK = {"hard": 0, "medium": 1, "easy": 2}
# a target of the dataset with no meaning as a question (a numerical check that is always about 0)
DROP_TARGET = re.compile(r"^energy_balance_error")

PHASES = {"subcooled_liquid": "subcooled (compressed) liquid", "superheated_vapor": "superheated vapour",
          "supercritical": "supercritical fluid"}

UNITS = {"kJ/kg": r"kJ/kg", "kJ/(kg·K)": r"kJ/(kg\,K)", "m³/kg": r"m^3/kg", "kg/m³": r"kg/m^3", "kPa": "kPa",
         "MPa": "MPa", "kW": "kW", "kW/K": "kW/K", "K": "K", "kg/s": "kg/s", "m/s": "m/s", "°C": None, "": ""}
UNIT_RE = r"°C|%|(?:kJ/\(kg·K\)|kJ/kg|kg/s|kg/m³|m/s|kPa|MPa|kW|K)(?![A-Za-z])"
NUM_RE = r"-?\d+(?:\.\d+)?"
HEAD = r"(?:COP|ef|ṁ|Ẇ|Ṡ|Ẋ|Q\u0307|[A-Za-zηερ])"
TOKEN = HEAD + r"(?:_[A-Za-z0-9]+(?:[_,][A-Za-z0-9]+)*)?"  # a symbol, with or without subscripts
SUBSCRIPTED = HEAD + r"_[A-Za-z0-9]+(?:[_,][A-Za-z0-9]+)*"
HEADS = {"ṁ": r"\dot{m}", "Ẇ": r"\dot{W}", "Ṡ": r"\dot{S}", "Ẋ": r"\dot{X}", "Q\u0307": r"\dot{Q}", "η": r"\eta",
         "ε": r"\varepsilon", "ρ": r"\rho", "rho": r"\rho", "COP": r"\mathrm{COP}", "ef": r"\mathrm{ef}"}
SUBSCRIPT_DIGITS = re.compile("[₀-₉]+")
NON_ASCII = re.compile(r"[^\x00-\x7f]")


# ---------------------------------------------------------------- text conversion

def subscripts(t: str) -> str:
    return SUBSCRIPT_DIGITS.sub(lambda m: "_" + m.group(0).translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")), t)


def sym(tok: str) -> str:
    """A symbol of the dataset (h_2s, T_c_out, Ṡ_gen, η_II, s_gen,total, rho) in LaTeX, without the $."""
    tok = subscripts(unicodedata.normalize("NFC", tok))
    m = re.match("rho", tok) or re.match(HEAD, tok)
    head = HEADS.get(m.group(0), m.group(0))
    parts = [p for p in re.split(r"[_,]", tok[m.end():]) if p]
    if not parts:
        return head
    words = [p for p in parts if not re.fullmatch(r"\d+s?", p) and not (head in "cr" and p == "p")]
    if len(words) == len(parts):  # all words: one upright block, h_{\mathrm{h,in}}
        sub = r"\mathrm{" + ",".join(parts) + "}"
    else:
        sub = ",".join(re.sub(r"^(\d+)s$", r"\1\\mathrm{s}", p) if re.fullmatch(r"\d+s?", p)
                       else (p if p == "p" else r"\mathrm{" + p + "}") for p in parts)
    return head + "_" + (sub if len(sub) == 1 else "{" + sub + "}")


def number(s: str) -> str:
    return re.sub(r"\.0+$", "", s)


def quantity(num: str, unit: str) -> str:
    """12.0 kPa -> 12\\ \\mathrm{kPa}; 25.0°C -> 25^\\circ\\mathrm{C}; 92.0% -> 92\\%."""
    num = number(num)
    if unit == "°C":
        return num + r"^\circ\mathrm{C}"
    if unit == "%":
        return num + r"\%"
    return num + r"\ \mathrm{" + UNITS[unit] + "}" if unit else num


def mathify(text: str) -> str:
    """Plain-text statement -> LaTeX: quantities, symbols and the equations between them in $...$."""
    t = unicodedata.normalize("NFC", text)
    t = subscripts(t)
    t = re.sub(r"(\d)→(?=\S)", r"\1: ", t)  # "1→compressor inlet" is a list of numbered states
    spans: list[str] = []

    def keep(math: str) -> str:
        spans.append(math)
        return f"\x00{len(spans) - 1}\x00"

    def fixed(old: str, new: str) -> None:
        nonlocal t
        t = t.replace(old, keep(new))

    # equations the general rules cannot read
    fixed("ε = (T_3 - T_2) / (T_5 - T_2)", r"\varepsilon = (T_3 - T_2)/(T_5 - T_2)")
    fixed("ṁ_air × (h_4 - h_5) = ṁ_steam × (h_8 - h_7)",
          r"\dot{m}_\mathrm{air}\,(h_4 - h_5) = \dot{m}_\mathrm{steam}\,(h_8 - h_7)")
    fixed("ṁ_air(h_4-h_5) = ṁ_steam(h_8-h_7)", r"\dot{m}_\mathrm{air}\,(h_4 - h_5) = \dot{m}_\mathrm{steam}\,(h_8 - h_7)")
    t = re.sub(rf"(?<![\w\\.])({TOKEN})\s*=\s*({TOKEN})\s*/\s*({TOKEN})(?![\w])",
               lambda m: keep(f"{sym(m.group(1))} = {sym(m.group(2))}/{sym(m.group(3))}"), t)
    t = re.sub(rf"(?<![\w\\.])({TOKEN})\s*=\s*({NUM_RE})\s*({UNIT_RE})?",
               lambda m: keep(f"{sym(m.group(1))} = {quantity(m.group(2), m.group(3) or '')}"), t)
    t = re.sub(rf"(?<![\w\\.])({SUBSCRIPTED})\s*=\s*({SUBSCRIPTED})(?![\w])",
               lambda m: keep(f"{sym(m.group(1))} = {sym(m.group(2))}"), t)
    t = re.sub(rf"(?<![\w.\x00])({NUM_RE})\s*({UNIT_RE})", lambda m: keep(quantity(m.group(1), m.group(2))), t)
    t = re.sub(rf"(?<![\w\\.\x00])({SUBSCRIPTED})(?![\w])", lambda m: keep(sym(m.group(1))), t)
    t = re.sub(r"(?<![\w'\\.\x00])(Q\u0307|[hsvuxTPρ])(?![\w'\x00])", lambda m: keep(sym(m.group(1))), t)
    out = re.sub(r"\x00(\d+)\x00", lambda m: "$" + spans[int(m.group(1))] + "$", t)
    return out


def statement(question: str) -> tuple[str, list[tuple[str, str]]]:
    """(the statement without its answer-format block, [(label, unit)] of that block, in order)."""
    m = re.split(r"\n\n(?:Report your answers as:|Present your final answers in the following format:)\n", question)
    assert len(m) == 2, question
    targets = []
    for line in m[1].split("\n"):
        if line.strip():
            label, _, unit = line.partition(" = ___")
            targets.append((label.removesuffix(": ___").strip(), unit.strip()))
    return m[0].strip(), targets


def body_latex(body: str) -> str:
    """Paragraphs: one per line, "- " lines an itemize, the side headings of the combined-cycle problems bold."""
    out, items = [], []
    for line in body.split("\n") + [""]:
        line = line.strip()
        if line.startswith("- "):
            items.append(mathify(line[2:]))
            continue
        if items:
            out.append("\\begin{itemize}\n" + "\n".join(f"\\item {x}" for x in items) + "\n\\end{itemize}")
            items = []
        if line:
            line = re.sub(r"^(GAS SIDE|STEAM SIDE)", lambda m: "\\textbf{" + m.group(1).capitalize() + "}", line)
            out.append(mathify(line))
    return "\n\n".join(out)


def unit_tex(unit: str) -> str:
    return r"^\circ\mathrm{C}" if unit == "°C" else (r"\mathrm{" + UNITS[unit] + "}" if unit else "")


def find_line(targets: list[tuple[str, str]]) -> str:
    items = []
    for label, unit in targets:
        if label == "Phase":
            items.append("the phase")
        else:
            items.append(f"${sym(label)}$" + (f" (${unit_tex(unit)}$)" if unit else ""))
    return "Find " + (", ".join(items[:-1]) + " and " + items[-1] if len(items) > 1 else items[0]) + "."


def sources_line(fluid: str, body: str, targets: list[tuple[str, str]]) -> str:
    """The sentence naming where the properties come from (the statements give only conditions)."""
    water = "Water" in fluid or "water" in body or "steam" in body.lower()
    r134 = "R134a" in fluid or "R-134a" in fluid or "R-134a" in body
    air = "Air" in fluid
    variable = air and ("temperature-dependent" in body or "variable specific heats" in body or fluid == "Air+Water")
    parts = []
    iir = "IIR reference state" in body
    if water:
        parts.append("Use steam tables (or another property source) for the properties of water.")
    if r134 and not iir:
        parts.append("Use R-134a tables (or another property source), with the IIR reference state "
                     "($h = 200\\ \\mathrm{kJ/kg}$ and $s = 1\\ \\mathrm{kJ/(kg\\,K)}$ for saturated liquid at $0^\\circ\\mathrm{C}$).")
    elif r134:
        parts.append("Use R-134a tables (or another property source) with this reference state.")
    if variable:
        parts.append("Use temperature-dependent properties for air, with enthalpy and entropy as in the standard "
                     "ideal-gas air tables ($h \\approx 290.16\\ \\mathrm{kJ/kg}$ and $s^\\circ \\approx 1.668\\ "
                     "\\mathrm{kJ/(kg\\,K)}$ at $290\\ \\mathrm{K}$).")
    elif air:
        gas = "Take $h = c_p T$ with $T$ in K, and $s = 0$ at $298.15\\ \\mathrm{K}$ and $0.1\\ \\mathrm{MPa}$"
        parts.append(gas + ("." if "R = 0.287" in body or "R_" in body else ", with $R = 0.287\\ \\mathrm{kJ/(kg\\,K)}$."))
    return " ".join(parts)


def fmt(v: float) -> str:
    """The key's number: 5 significant figures (the dataset's own digits when it has fewer)."""
    if abs(v) < 1e-9:
        return "0"
    short = float(f"{v:.5g}")
    s = format(Decimal(repr(v) if len(Decimal(repr(v)).as_tuple().digits) <= 5 else repr(short)), "f")
    return re.sub(r"\.0+$", "", s) if "." in s else s


def answer_key(targets: list[tuple[str, str]], values: list) -> str:
    parts = []
    for n, ((label, unit), v) in enumerate(zip(targets, values, strict=True), 1):
        if label == "Phase":
            parts.append(f"({n}) phase: {PHASES[v]}")
            continue
        u = unit_tex(unit)
        parts.append(f"({n}) ${sym(label)} = {fmt(v)}" + ("" if not u else (u if unit == '°C' else r'\ ' + u)) + "$")
    return "; ".join(parts)


# ---------------------------------------------------------------- the rows

def load_fixes() -> tuple[dict, dict]:
    if not FIXES_PATH.exists():
        return {}, {}
    doc = json.loads(FIXES_PATH.read_text(encoding="utf-8"))
    return {(e["key"], e["field"]): [tuple(p) for p in e["fixes"]] for e in doc.get("fixes", [])}, doc.get("dropped", {})


def load(data: Path) -> tuple[list[dict], dict[str, str]]:
    """The rows to import and {id: why} of the ones left out."""
    raw = []
    for tier in TIERS:
        for line in (data / tier / "questions.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                r["template"] = json.loads(r["metadata"])["template_id"]
                raw.append(r)
    left_out = {r["id"]: f"skipped: {SKIP[r['id']]}" for r in raw if r["id"] in SKIP}
    by = collections.defaultdict(list)
    for r in raw:
        if r["id"] not in SKIP:
            by[r["template"]].append(r)
    chosen = set()
    for rs in by.values():
        keep = sorted(rs, key=lambda r: (RANK[r["difficulty"]], r["id"]))[:PER_TEMPLATE]
        chosen |= {r["id"] for r in keep}
        left_out |= {r["id"]: f"template {r['template']}: more than {PER_TEMPLATE} rows" for r in rs if r["id"] not in chosen}
    fixes, dropped = load_fixes()
    rows = []
    for r in raw:
        if r["id"] not in chosen:
            continue
        if r["id"] in dropped:
            left_out[r["id"]] = "dropped: " + dropped[r["id"]]
            continue
        body, targets = statement(r["question"])
        expected = list(json.loads(r["expected"]).values())
        # the labels and the dataset's values pair up by position; a label the data has no value for is left out
        keys = list(json.loads(r["expected"]))
        kept_labels = [t for t in targets if not DROP_TARGET.match(t[0])]
        kept_values = [v for k, v in zip(keys, expected, strict=True) if not DROP_TARGET.match(k)]
        if len(kept_labels) == len(kept_values) + 1 and kept_labels[-1][0] == "η_II_combined":
            kept_labels = kept_labels[:-1]  # the data has no value for it
        if len(kept_labels) != len(kept_values):
            left_out[r["id"]] = f"dropped: {len(kept_labels)} targets but {len(kept_values)} values"
            continue
        values = [v["value"] for v in kept_values]
        fluid = r.get("fluid") or r.get("given") and json.loads(r["given"]).get("fluid", "") or ""
        latex = body_latex(body) + "\n\n" + find_line(kept_labels)
        extra = sources_line(fluid, body, kept_labels)
        if extra:
            latex += " " + extra
        row = {"potd": f"{SET} {r['id']}", "set": SET, "idx": r["id"], "orig": "", "source": SET,
               "subsource": f"{r['template']}, {r['id']}", "latexcode": latex,
               "answer": answer_key(kept_labels, values), "solution": None, "hints": None, "more_hints": None,
               "ref_solution": "", "group": "subject", "effort": None, "image": None}
        for fld in ("latexcode", "answer"):
            for old, new in fixes.get((r["id"], fld), []):
                if row[fld].count(old) != 1:
                    raise SystemExit(f"FIX {r['id']} {fld}: expected one {old!r}")
                row[fld] = row[fld].replace(old, new)
        for fld in ("latexcode", "answer"):
            if NON_ASCII.search(row[fld]):
                left_out[r["id"]] = f"dropped: non-ASCII left in {fld}: {sorted(set(NON_ASCII.findall(row[fld])))}"
                break
        else:
            rows.append(row)
    return rows, left_out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True, help="folder with tier1_properties, tier2_components, tier3_cycles")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows, left_out = load(a.data)
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
        set_aside = Path("app/data/appdata/benchmarks_set_aside.json")
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        set_aside.write_text(json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why],
                                        ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {set_aside}")
        problems = check(new)
    print(json.dumps({"rows": len(rows), "left_out": len(left_out), "in_bank": len(dup), "to_add": len(new),
                      "check_problems": len(problems),
                      "by_template": len({r["subsource"].split(",")[0] for r in new}),
                      "by_tier": collections.Counter(r["idx"][:2] for r in new)}, default=dict))
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        for k, why in sorted(left_out.items()):
            if not why.startswith("template "):
                print("left out:", k, why)
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("thermoqa")
    for r in new:  # figures, before their questions exist (none in this set)
        for name, data in r.get("image") or []:
            if isinstance(data, str) and data.startswith("data:image/png;base64,"):
                data = base64.b64decode(data.split(",", 1)[1])
            elif not isinstance(data, bytes):
                data = Path(data).read_bytes()
            (TEXIMAGES / f"{name}.png").write_bytes(data)
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
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    maths = {str(q): {"model": "claude-opus-5-5", "effort": r["effort"] or "high"} for q, r in added if r["group"] == "math"}
    if maths:  # subject rows need nothing here: the subjects solver picks them up after classification
        doc = json.loads(ASSIGNMENTS.read_text(encoding="utf-8")) if ASSIGNMENTS.exists() else {
            "note": "Benchmark sets imported by app/tools/import_*.py; the model and effort that solve the math rows.",
            "questions": {}}
        doc["questions"].update(maths)
        ASSIGNMENTS.write_text(json.dumps(doc, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    refs = {str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]} for q, r in added if r["ref_solution"]}
    if refs:  # the dataset's own solutions (this set has none)
        solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
        solutions.update(refs)
        SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; map={MAP_PATH}; "
          f"math rows assigned: {len(maths)}")


if __name__ == "__main__":
    main()
