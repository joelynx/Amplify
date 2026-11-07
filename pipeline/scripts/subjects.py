"""Non-math subjects: per-subject prompts, answer keys, and the judge for their replies.

Two modes (status.mode; NULL is the math run):
  solve  a full solution for a question whose own solution is missing or a Gemini one,
         as in the math run: SOLUTION, NOTES, TAKEAWAYS, ANSWER KEY, HINT
         (prompts/subject/solve.md). The old solution is never sent.
  aids   study aids around the book's own solution, which stays as the book wrote it:
         BOOK CHECK, TAKEAWAYS, ANSWER KEY, HINT (prompts/subject/aids.md).
Both prompts are filled from the subject's profile (prompts/subject/profiles/<slug>.md, one
"## name" section per {{NAME}} placeholder) and the shared answer-key rules
(prompts/subject/answer_key.md). The answer key goes to questions.answer_key as JSON
(pipeline/answer_key_spec.md) and its readable form to `answer`.

run_subjects.py sends the questions; run.judge_one hands their replies to validate_reply and
assemble_one here, so the judge (here or on the other machine) settles them like math replies.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from common import (
    PROMPTS_DIR,
    REPO_DIR,
    check_web_parts,
    content_problems,
    fetch_question,
    get_status,
    is_blank,
    log_event,
    model_display,
    now_iso,
    pipeline_wrote,
    q_dir,
    read_text,
    strip_code_fences,
    upsert_status,
    write_json,
    write_text,
)

SUBJECT_PROMPTS = PROMPTS_DIR / "subject"
TAXONOMY_JSON = REPO_DIR / "taxonomy" / "taxonomy.json"
MODES = ("solve", "aids")

SOLVE_MARKERS = [
    "%%% BEGIN SOLUTION", "%%% END SOLUTION",
    "%%% BEGIN NOTES", "%%% END NOTES",
    "%%% BEGIN TAKEAWAYS", "%%% END TAKEAWAYS",
    "%%% BEGIN ANSWER KEY", "%%% END ANSWER KEY",
    "%%% BEGIN HINT", "%%% END HINT",
]
AIDS_MARKERS = [
    "%%% BOOK CHECK:",
    "%%% BEGIN TAKEAWAYS", "%%% END TAKEAWAYS",
    "%%% BEGIN ANSWER KEY", "%%% END ANSWER KEY",
    "%%% BEGIN HINT", "%%% END HINT",
]
KINDS = ("NUMBER", "CHOICE", "TRUEFALSE", "EXPRESSION", "POINTS")
# How run.judge_one words a blind re-solve after a disagreement with the stored answer.
MISMATCH_REASON = "its final answer did not match the stored reference answer"

# Prose that points at a figure the question does not carry. Unlike the math run's rule, a
# question that asks the student to draw ("explain with a neat sketch") is not skipped: the
# solution describes the sketch instead.
FIGURE_REF = re.compile(
    r"\bfig(?:ure)?\.?\s*\d"
    r"|\b(?:figure|diagram|sketch|graph|picture|drawing)\s+(?:shown|below|above|given|alongside)\b"
    r"|\b(?:shown|given|illustrated)\s+(?:in|below|above)\s+(?:the\s+)?(?:fig|figure|diagram|sketch|graph)\b"
    r"|\b(?:shown|given)\s+(?:below|above)\b"
    r"|\bthe following (?:figure|diagram|picture|graph)\b",
    re.I,
)
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")


def subj_cfg(cfg: dict) -> dict:
    s = cfg.get("subjects")
    if not s or not s.get("profiles"):
        raise SystemExit("config.json has no subjects.profiles")
    return s


def figure_reason(latex: str) -> str | None:
    """Why a question cannot be solved without a figure it does not carry, or None."""
    names = IMG_RE.findall(latex)
    if names:
        return "references image(s): " + ", ".join(n.strip() for n in names[:3])
    m = FIGURE_REF.search(latex)
    return f"text refers to a figure ('{m.group(0)}')" if m else None


# --- subjects and prompts -------------------------------------------------------------


@lru_cache(maxsize=1)
def subject_map() -> dict[tuple[str, str, str], str]:
    nodes = json.loads(TAXONOMY_JSON.read_text(encoding="utf-8"))
    return {(n["topic"], n["branch"], n["subtopic"]): n["subject"] for n in nodes}


def subject_of(q: dict) -> str | None:
    return subject_map().get((q["topic"], q["branch"], q["subtopic"]))


def load_profile(cfg: dict, subject: str) -> dict[str, str]:
    slug = subj_cfg(cfg)["profiles"].get(subject)
    if not slug:
        raise SystemExit(f"no profile for subject {subject!r} in config.subjects.profiles")
    text = read_text(SUBJECT_PROMPTS / "profiles" / f"{slug}.md")
    out: dict[str, str] = {}
    for m in re.finditer(r"^## (\w+)\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S):
        out[m.group(1)] = m.group(2).strip()
    need = {"role", "picture", "checks", "notes_title", "notes", "takeaways", "hint_examples"}
    if need - set(out):
        raise SystemExit(f"profile {slug}.md lacks sections: {sorted(need - set(out))}")
    return out


def system_prompt(cfg: dict, mode: str, subject: str) -> str:
    """The system prompt for one subject and mode. Refuses a template that could carry the old
    solution or the stored answer (the aids mode sends the book's solution in the message)."""
    tpl = read_text(SUBJECT_PROMPTS / f"{mode}.md")
    for banned in ("{{OLD_SOLUTION}}", "{{STORED_ANSWER}}", "{{NEW_SOLUTION}}"):
        if banned in tpl:
            raise SystemExit(f"refusing to build the {mode} prompt: template references {banned}")
    prof = load_profile(cfg, subject)
    fills = {k.upper(): v for k, v in prof.items()}
    fills.update({
        "NOTES_TITLE": prof["notes_title"].upper(),
        "NOTES_TITLE_LOWER": prof["notes_title"].lower(),
        "ANSWER_KEY_RULES": read_text(SUBJECT_PROMPTS / "answer_key.md").strip(),
        "FORMAT_RULES": read_text(PROMPTS_DIR / "format_rules.md").strip(),
    })
    for k, v in fills.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", tpl)))
    if leftover:
        raise SystemExit(f"unfilled placeholders in subject/{mode}.md: {leftover}")
    return tpl.strip() + "\n"


def user_text(q: dict, mode: str, feedback: dict | None, cfg: dict) -> str:
    """The question (and in aids mode the book's solution and answer); a retry adds what the
    checks said, worded as in run.user_text."""
    text = "QUESTION (in LaTeX):\n" + q["latexcode"].strip() + "\n"
    if mode == "aids":
        text += "\nTHE BOOK'S SOLUTION (in LaTeX):\n" + q["solution"].strip() + "\n"
        if not is_blank(q["answer"], cfg["empty_answer_sentinels"]):
            text += "\nTHE BOOK'S STATED ANSWER:\n" + q["answer"].strip() + "\n"
    if not feedback:
        return text
    if feedback["kind"] == "feedback":
        bullets = "\n".join(f"- {e}" for e in feedback["errors"])
        text += (
            "\nYour previous reply to this question is below. It was rejected by the automatic checks "
            "for these reasons:\n" + bullets + "\n\n"
            "Write the complete reply again in the required structure with these problems fixed. "
            "Do not mention the previous reply.\n\nPREVIOUS REPLY:\n" + feedback["previous_text"].strip() + "\n"
        )
    elif feedback["reason"].startswith(MISMATCH_REASON):
        # Never the stored answer itself: these books' answers are often wrong, and a solver
        # told the expected value bends its working to reach it.
        text += (
            "\nNote: an earlier attempt at this question gave a final result that disagrees with a reference "
            "answer, which may itself be wrong. Work it carefully from scratch and double-check every final value; "
            "if the question lacks data needed for a result, say so rather than assuming a value.\n"
        )
    else:  # blind re-solve
        text += (
            f"\nNote: an earlier attempt at this question was rejected ({feedback['reason']}). "
            "Work it carefully from scratch and double-check every final value before writing it.\n"
        )
    return text


# --- reply parsing --------------------------------------------------------------------


def split_sections(text: str, markers: list[str]) -> tuple[dict | None, list[str]]:
    """{marker: line index} for a reply that has every marker exactly once, in order, and
    nothing outside the sections; else (None, errors)."""
    errors: list[str] = []
    lines = text.replace("\r\n", "\n").split("\n")
    pos: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("%%%"):
            continue
        m = next((m for m in markers if s == m or (m.endswith(":") and s.startswith(m))), None)
        if m is None:
            errors.append(f"line {i + 1}: unexpected marker line '{s[:60]}'")
        else:
            pos.setdefault(m, []).append(i)
    for m in markers:
        if len(pos.get(m, [])) != 1:
            errors.append(f"marker '{m}' appears {len(pos.get(m, []))} times (expected exactly once)")
    if errors:
        return None, errors
    order = [pos[m][0] for m in markers]
    if order != sorted(order):
        return None, ["marker lines are out of order"]
    if "\n".join(lines[: order[0]]).strip():
        errors.append(f"content before the {markers[0]} marker")
    if "\n".join(lines[order[-1] + 1:]).strip():
        errors.append(f"content after the {markers[-1]} marker")
    for i, m in enumerate(markers[:-1]):
        if m.startswith("%%% END") or m.endswith(":"):
            if "\n".join(lines[order[i] + 1: order[i + 1]]).strip():
                errors.append(f"content between sections after '{m}'")
    return {"lines": lines, "pos": dict(zip(markers, order))}, errors


def parse_reply(text: str, mode: str) -> tuple[dict | None, list[str]]:
    """Split a reply into its sections. parts: solution, notes (None for NONE), takeaways,
    key_text, hint (solve); book_check, takeaways, key_text, hint (aids)."""
    text, _ = strip_code_fences(text)
    sec, errors = split_sections(text, SOLVE_MARKERS if mode == "solve" else AIDS_MARKERS)
    if sec is None:
        return None, errors
    lines, pos = sec["lines"], sec["pos"]

    def body(name: str) -> str:
        return "\n".join(lines[pos[f"%%% BEGIN {name}"] + 1: pos[f"%%% END {name}"]]).strip()

    parts: dict = {"mode": mode, "takeaways": body("TAKEAWAYS"), "key_text": body("ANSWER KEY"), "hint": body("HINT")}
    if mode == "solve":
        parts["solution"] = body("SOLUTION")
        notes = body("NOTES")
        parts["notes"] = None if notes == "" or notes.rstrip(".").strip().upper() == "NONE" else notes
        if not parts["solution"]:
            errors.append("empty solution body")
    else:
        bc = lines[pos["%%% BOOK CHECK:"]].strip()[len("%%% BOOK CHECK:"):].strip()
        parts["book_check"] = bc
        if not bc:
            errors.append("empty BOOK CHECK line")
    for name in ("takeaways", "hint"):
        if not parts[name]:
            errors.append(f"empty {name} body")
    if not parts["key_text"]:
        errors.append("empty answer key")
    return parts, errors


# --- the answer key -----------------------------------------------------------------

NUM_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
UNIT_RE = re.compile(r"[A-Za-z0-9/^ .()*-]+")
ASK_RE = re.compile(r"[A-Za-z0-9 ,.'()/+-]*")
LABEL_RE = re.compile(r"-|[A-Za-z0-9]{1,6}(?:\.[A-Za-z0-9]{1,4})?")
MICRO_BASES = ("m", "s", "F", "H", "A", "V", "W", "g", "mol", "Pa", "J")


def key_unit(u: str) -> str:
    """The key's display unit from the solver's ASCII unit: percent -> %, degC -> °C, a u
    prefix -> µ; a dash means no unit."""
    u = re.sub(r"\s+", " ", u.strip())
    if u in ("", "-"):
        return ""
    if u.lower() == "percent":
        return "%"
    u = re.sub(r"\bdegC\b", "°C", u)
    u = re.sub(r"\bdegF\b", "°F", u)
    u = re.sub(r"\bdeg\b", "°", u)
    return re.sub(rf"\bu(?=(?:{'|'.join(MICRO_BASES)})\b)", "µ", u)


def unit_latex(u: str) -> str:
    """A key unit as LaTeX inside math mode (ASCII only, as the format rules require)."""
    if u == "%":
        return r"\%"
    if u.startswith("°"):
        rest = u[1:].strip()
        return "^{\\circ}" + (unit_latex(rest) if rest else "")
    s = u.replace("µ", r"\mu{}")
    s = re.sub(r"\^(-?\d+)", r"^{\1}", s)
    s = s.replace(" ", r"\,")
    return r"\mathrm{" + s + "}"


def option_count(latex: str) -> int | None:
    """How many options a multiple-choice question prints: the \\items of its first enumerate,
    else (a), (b), ... labels."""
    m = re.search(r"\\begin\{enumerate\}(.*?)\\end\{enumerate\}", latex, flags=re.S)
    if m:
        n = len(re.findall(r"\\item\b", m.group(1)))
        if n:
            return n
    labels = re.findall(r"\(([a-h])\)", latex)
    seq = 0
    for lab in labels:
        if ord(lab) - ord("a") == seq:
            seq += 1
    return seq or None


def parse_key(key_text: str, question_latex: str) -> tuple[dict | None, list[str]]:
    """The answer key block -> {"v": 1, "parts": [...]} (answer_key_spec.md), or errors."""
    errors: list[str] = []
    parts: list[dict] = []
    current = None
    n_opts = option_count(question_latex)
    for ln, raw in enumerate(key_text.split("\n"), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("POINT "):
            if current is None or current["kind"] != "points":
                errors.append(f"key line {ln}: POINT line not under a POINTS part")
                continue
            current["points"].append(line[len("POINT "):].strip())
            continue
        if not line.startswith("PART "):
            errors.append(f"key line {ln}: neither a PART nor a POINT line: '{line[:60]}'")
            continue
        f = [x.strip() for x in line[len("PART "):].split("|")]
        if len(f) < 2 or f[1] not in KINDS:
            errors.append(f"key line {ln}: expected PART <label> | <{'|'.join(KINDS)}> | ...")
            continue
        label, kind = f[0], f[1]
        if not LABEL_RE.fullmatch(label):
            errors.append(f"key line {ln}: bad label '{label[:20]}'")
            continue
        lab = "" if label == "-" else label
        if kind == "NUMBER":
            if len(f) not in (5, 6):
                errors.append(f"key line {ln}: NUMBER needs value | unit | what it is [| TOL n]")
                continue
            value, unit, ask = f[2], f[3], f[4]
            if not NUM_RE.fullmatch(value):
                errors.append(f"key line {ln}: value '{value[:30]}' is not a plain number")
                continue
            if unit not in ("", "-") and not UNIT_RE.fullmatch(unit):
                errors.append(f"key line {ln}: unit '{unit[:30]}' is not plain ASCII")
                continue
            tol = None
            if len(f) == 6:
                m = re.fullmatch(r"TOL\s+(\d+(?:\.\d+)?)\s*(?:percent|%)?", f[5])
                if not m or not 0 < float(m.group(1)) <= 25:
                    errors.append(f"key line {ln}: bad tolerance '{f[5][:20]}' (TOL <percent>, at most 25)")
                    continue
                tol = round(float(m.group(1)) / 100, 6)
            num = float(value)
            v = int(num) if re.fullmatch(r"[-+]?\d+", value) else num
            current = {"label": lab, "ask": ask, "kind": "number", "value": v, "unit": key_unit(unit), "tol": tol,
                       "_raw": value}
        elif kind == "CHOICE":
            letters = [x.strip().lower() for x in (f[2] if len(f) > 2 else "").split(",") if x.strip()]
            if not letters or not all(re.fullmatch(r"[a-z]", x) for x in letters):
                errors.append(f"key line {ln}: CHOICE needs option letters (a, b, ...)")
                continue
            if n_opts and any(ord(x) - ord("a") >= n_opts for x in letters):
                errors.append(f"key line {ln}: option {letters} but the question prints {n_opts} options")
                continue
            current = {"label": lab, "ask": f[3] if len(f) > 3 else "", "kind": "choice",
                       "value": letters[0] if len(letters) == 1 else sorted(set(letters))}
            if n_opts:
                current["options"] = n_opts
        elif kind == "TRUEFALSE":
            v = (f[2] if len(f) > 2 else "").upper()
            if v not in ("TRUE", "FALSE"):
                errors.append(f"key line {ln}: TRUEFALSE needs TRUE or FALSE")
                continue
            current = {"label": lab, "ask": f[3] if len(f) > 3 else "", "kind": "truefalse", "value": v == "TRUE"}
        elif kind == "EXPRESSION":
            expr = "|".join(f[2:]).strip()
            if not expr:
                errors.append(f"key line {ln}: empty EXPRESSION")
                continue
            current = {"label": lab, "ask": "", "kind": "expression", "value": expr}
        else:  # POINTS
            current = {"label": lab, "ask": "|".join(f[2:]).strip(), "kind": "points", "points": []}
        if current["ask"] and (not ASK_RE.fullmatch(current["ask"]) or len(current["ask"]) > 100):
            errors.append(f"key line {ln}: 'what it is' must be plain ASCII words, at most 100 characters")
        parts.append(current)
    labels = [p["label"] for p in parts]
    if not parts:
        errors.append("the answer key has no PART line")
    elif "" in labels and len(parts) > 1:
        errors.append("the label - is only for a question with a single thing to answer")
    if len(set(labels)) != len(labels):
        errors.append(f"repeated labels in the answer key: {sorted({x for x in labels if labels.count(x) > 1})}")
    for p in parts:
        if p["kind"] == "points" and not 2 <= len(p["points"]) <= 10:
            errors.append(f"part {p['label'] or '-'}: POINTS needs 3 to 8 POINT lines, has {len(p['points'])}")
    if errors:
        return None, errors
    return {"v": 1, "parts": parts}, []


def public_key(key: dict) -> dict:
    """The key as stored: without the parse bookkeeping (fields starting with _)."""
    return {"v": key["v"], "parts": [{k: v for k, v in p.items() if not k.startswith("_")} for p in key["parts"]]}


def fmt_number(p: dict) -> str:
    """The value as the solver wrote it, with e-notation as a power of ten."""
    s = p.get("_raw") or str(p["value"])
    s = s.lstrip("+")
    if "e" in s or "E" in s:
        mant, exp = re.split(r"[eE]", s)
        return f"{mant} \\times 10^{{{int(exp)}}}"
    return s


def part_display(p: dict) -> str | None:
    """One part of the readable answer (LaTeX), or None for a checklist part."""
    k = p["kind"]
    if k == "number":
        u = p["unit"]
        if not u:
            return f"\\({fmt_number(p)}\\)"
        sep = "" if u.startswith("°") else r"\," if u == "%" else r"\ "
        return f"\\({fmt_number(p)}{sep}{unit_latex(u)}\\)"
    if k == "choice":
        v = p["value"] if isinstance(p["value"], list) else [p["value"]]
        return ", ".join(f"({x})" for x in v)
    if k == "truefalse":
        return "True" if p["value"] else "False"
    if k == "expression":
        return f"\\({p['value']}\\)"
    return None


def answer_display(key: dict) -> str | None:
    """The `answer` field: the key's definite answers, labelled when there are several."""
    shown = [(p["label"], d) for p in key["parts"] if (d := part_display(p)) is not None]
    if not shown:
        return None
    if len(key["parts"]) == 1 and not shown[0][0]:
        return shown[0][1]
    return "; ".join(f"({lab}) {d}" if lab else d for lab, d in shown)


def points_block(key: dict) -> str | None:
    """LaTeX for the checklist parts, as the Key Points section of a generated solution."""
    pts = [p for p in key["parts"] if p["kind"] == "points"]
    if not pts:
        return None
    out = []
    for p in pts:
        items = "\\begin{itemize}\n" + "\n".join(f"\\item {x}" for x in p["points"]) + "\n\\end{itemize}"
        out.append(f"\\textbf{{Part ({p['label']}).}}\n{items}" if p["label"] else items)
    return "\n\n".join(out)


# --- checks ---------------------------------------------------------------------------


def stored_reference(stored: str | None) -> dict | None:
    """What a source's stored answer says, when it is plain enough to compare: option letters,
    true/false, or a list of numbers (part labels and units ignored)."""
    if stored is None:
        return None
    s = stored.strip()
    m = re.fullmatch(r"\(?\s*([A-Ha-h])\s*\)?\.?", s)
    if m:
        return {"kind": "choice", "value": [m.group(1).lower()]}
    if re.fullmatch(r"[A-Ha-h](?:\s*,\s*[A-Ha-h])+", s):
        return {"kind": "choice", "value": sorted({x.strip().lower() for x in s.split(",")})}
    if s.upper() in ("TRUE", "FALSE"):
        return {"kind": "truefalse", "value": s.upper() == "TRUE"}
    if re.search(r"\\times|\^|\\frac|/\s*\d|\d\s*/", s):
        return None  # powers of ten, fractions: not worth parsing
    t = re.sub(r"\\text\{([^{}]*)\}|\\mathrm\{([^{}]*)\}", lambda mm: " " + (mm.group(1) or mm.group(2) or "") + " ", s)
    t = re.sub(r"\(\s*(?:[a-h]|i{1,3}|iv|v|vi{0,3}|\d)\s*\)", " ", t)  # part labels
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)  # thousands separators
    nums = [float(x) for x in re.findall(r"(?<![\w.])[-+]?\d+(?:\.\d+)?", t)]
    return {"kind": "numbers", "value": nums} if nums else None


def close(a: float, b: float, tol: float) -> bool:
    """Equal within a relative tolerance, allowing a power-of-ten unit difference (kW against
    MW, a fraction against a percentage)."""
    if b == 0:
        return abs(a) <= 1e-9
    return any(abs(a * f - b) <= tol * abs(b) for f in (1, 1e3, 1e-3, 1e6, 1e-6, 100, 0.01))


def reference_mismatch(key: dict, ref: dict | None) -> str | None:
    """Why the key disagrees with the source's stored answer, or None (also when they cannot
    be compared)."""
    if ref is None:
        return None
    parts = key["parts"]
    if ref["kind"] in ("choice", "truefalse"):
        same = [p for p in parts if p["kind"] == ref["kind"]]
        if len(same) != 1:
            return None
        got = same[0]["value"]
        if ref["kind"] == "choice":
            got = sorted(got) if isinstance(got, list) else [got]
        return None if got == ref["value"] else f"key {got}, stored answer {ref['value']}"
    nums = [p for p in parts if p["kind"] == "number"]
    if not nums or len(nums) != len(ref["value"]):
        return None
    for p, b in zip(nums, ref["value"]):
        if not close(float(p["value"]), b, max(p["tol"] or 0, 0.03)):
            return f"key {[q['value'] for q in nums]}, stored answer {ref['value']}"
    return None


def hint_leaks(hint: str, key: dict) -> list[str]:
    """The hint must not carry a value of the key."""
    errs = []
    flat = re.sub(r"\s+", "", hint)
    for p in key["parts"]:
        if p["kind"] == "number":
            raw = p.get("_raw") or str(p["value"])
            digits = re.sub(r"[^0-9.]", "", raw.split("e")[0].split("E")[0]).strip(".")
            if len(digits.replace(".", "")) >= 2 and re.search(rf"(?<![\d.]){re.escape(digits)}(?![\d])", hint):
                errs.append(f"leak: hint contains the value {digits} of part {p['label'] or '-'}")
        elif p["kind"] == "expression":
            e = re.sub(r"\s+", "", p["value"])
            if len(e) >= 3 and e in flat:
                errs.append(f"leak: hint contains the expression of part {p['label'] or '-'}")
    return errs


def validate_reply(qid: int, text: str, cfg: dict, q: dict, mode: str, stored_answer: str | None,
                   compile_checks: bool = True) -> dict:
    """Mechanical checks on one reply, as validate.validate_solver_text does for math:
    structure, the answer key, LaTeX rules, length, the source's stored answer, and (with
    compile_checks) the PDF and web-view checks. No model is consulted."""
    res: dict = {"question_id": qid, "mode": mode, "checked_at": now_iso(), "errors": [], "hint_errors": [],
                 "answer_mismatch": False}
    parts, errs = parse_reply(text, mode)
    res["errors"] += [f"structure: {e}" for e in errs]
    if parts is None:
        res.update(ok=False, hint_ok=False)
        return res
    key, kerrs = parse_key(parts["key_text"], q["latexcode"])
    res["errors"] += [f"answer key: {e}" for e in kerrs]
    main: dict[str, str] = {}
    if mode == "solve":
        main["solution"] = parts["solution"]
        if parts["notes"]:
            main["notes"] = parts["notes"]
    main["takeaways"] = parts["takeaways"]
    if key is not None:
        disp = answer_display(key)
        if disp:
            main["answer"] = disp
        pb = points_block(key)
        if pb:
            main["points"] = pb
        res["answer_key"] = public_key(key)
        res["answer_display"] = disp
    for name, body in main.items():
        res["errors"] += [f"rules [{name}]: {p}" for p in content_problems(body)]
    if mode == "solve":
        n = len(parts["solution"])
        lo = int(subj_cfg(cfg).get("solution_min_chars", 400))
        if n < lo:
            res["errors"].append(f"length: solution {n} chars < min {lo}")
        if key is not None and any(p["kind"] != "points" for p in key["parts"]) and "Final answer:" not in parts["solution"]:
            res["errors"].append("solution body has no 'Final answer:' line")
    else:
        bc = parts["book_check"]
        res["book_check"] = bc
        if not re.fullmatch(r"OK\.?", bc, flags=re.I):
            res["book_problem"] = bc[:300]

    hint = parts["hint"] or ""
    hb = cfg.get("hint_length_bounds_chars") or {}
    if hb.get("min") is not None and len(hint) < hb["min"]:
        res["hint_errors"].append(f"length: hint {len(hint)} chars < min {hb['min']}")
    if hb.get("max") is not None and len(hint) > hb["max"]:
        res["hint_errors"].append(f"length: hint {len(hint)} chars > max {hb['max']}")
    res["hint_errors"] += [f"rules: {p}" for p in content_problems(hint)]
    if key is not None:
        res["hint_errors"] += hint_leaks(hint, key)

    if compile_checks and not res["errors"]:
        from check_pdf import check_parts

        pieces = dict(main)
        pieces["hint"] = hint
        pdf = check_parts(pieces, cfg=cfg)
        res["pdf_ok"] = pdf["ok"]
        for e in pdf["errors"]:
            (res["hint_errors"] if e.startswith("[hint]") else res["errors"]).append(f"pdf: {e}")
        if not pdf["ok"]:
            res["pdf_log_tail"] = pdf["log_tail"][-1200:]
        web = check_web_parts(pieces, q_dir(qid))
        res["web_ok"] = web["ok"]
        for e in web["errors"]:
            (res["hint_errors"] if e.startswith("[hint]") else res["errors"]).append(f"web: {e}")

    if key is not None and not res["errors"]:
        why = reference_mismatch(key, stored_reference(stored_answer))
        if why:
            res["answer_mismatch"] = True
            res["stored_answer"] = stored_answer
            res["mismatch"] = why
    res["ok"] = not res["errors"]
    res["hint_ok"] = not res["hint_errors"]
    return res


# --- assemble -------------------------------------------------------------------------


def title(t: str) -> str:
    return f"\\medskip\\noindent\\textbf{{{t}}}"


def assemble_one(qid: int, cfg: dict, app, pc) -> dict:
    """Store a passed reply: the generated solution (solve) or the takeaways block (aids), the
    readable answer, the answer key and the hint, queued for apply_fields like math fills.
    Whether answer_key and takeaways are still empty is decided when they are written (the
    judging machine's copy of the question has neither column)."""
    from check_pdf import check_pdf

    row = get_status(pc, qid)
    q = fetch_question(app, qid)
    d = q_dir(qid)
    acc = int(row["accepted_attempt"])
    mode = row["mode"]
    text, _ = strip_code_fences(read_text(d / f"solver_{acc}.tex"))
    parts, errs = parse_reply(text, mode)
    key, kerrs = parse_key(parts["key_text"], q["latexcode"]) if parts else (None, [])
    if parts is None or key is None:
        return {"question_id": qid, "ok": False, "errors": errs + kerrs}
    hint = parts["hint"] if row["hint_status"] == "ok" else None
    acc_model = row["solver2_model"] if acc >= 2 else row["solver1_model"]
    acc_effort = row["solver2_effort"] if acc >= 2 else row["solver1_effort"]
    attribution = f"\\hfill [Generated by {model_display(cfg, acc_model)} at {acc_effort} effort]"
    prof = load_profile(cfg, row["subject"])

    final = takeaways_value = None
    if mode == "solve":
        blocks = [parts["solution"].strip()]
        if parts["notes"]:
            blocks += [title(prof["notes_title"]), parts["notes"].strip()]
        blocks += [title("Takeaways"), parts["takeaways"].strip()]
        pb = points_block(key)
        if pb:
            blocks += [title("Key Points"), pb]
        final = "\n\n".join(blocks) + "\n\n" + attribution + "\n"
    else:
        takeaways_value = parts["takeaways"].strip() + "\n\n" + attribution
    answer_value = answer_display(key)
    key_json = json.dumps(public_key(key), ensure_ascii=False)

    errors: list[str] = []
    pieces = {}
    for name, body in (("final", final), ("takeaways", takeaways_value), ("answer", answer_value), ("hint", hint)):
        if body:
            pieces[name] = body
            r = check_pdf(body, cfg=cfg)
            errors += [f"pdf[{name}]: {e}" for e in r["errors"]]
    w = check_web_parts(pieces, d)
    errors += [f"web{e}" for e in w["errors"]]
    if errors:
        write_json(d / "assemble_errors.json", {"errors": errors, "at": now_iso()})
        upsert_status(pc, qid, status="needs_human_review", note="assembled content failed checks: " + "; ".join(errors)[:300])
        log_event(pc, qid, "assemble", "FAILED: " + "; ".join(errors)[:300])
        return {"question_id": qid, "ok": False, "errors": errors}

    if final:
        write_text(d / "final.tex", final)
    else:
        write_text(d / "takeaways.tex", takeaways_value)
    write_json(d / "answer_key.json", public_key(key))
    sentinels = cfg["empty_answer_sentinels"]
    ans_empty = is_blank(q["answer"], sentinels) or pipeline_wrote(pc, qid, "answer", q["answer"])
    hint_empty = is_blank(q["hints"]) or pipeline_wrote(pc, qid, "hints", q["hints"])
    fill_answer = answer_value if (ans_empty and answer_value and row["status"] == "passed") else None
    fill_hint = hint if (hint_empty and hint) else None
    gen_col = cfg.get("generated_solution_column") or "generated_solution"
    fields = ((gen_col, final), ("takeaways", takeaways_value), ("answer", fill_answer), ("answer_key", key_json),
              ("hints", fill_hint))
    write_json(d / "final_app.json", {"question_id": qid, "mode": mode, "subject": row["subject"],
                                      **{f: v for f, v in fields}, "status": row["status"], "accepted_attempt": acc,
                                      "model": acc_model, "effort": acc_effort,
                                      "prompt_version": subj_cfg(cfg)["prompt_version"]})
    pc.execute(
        """INSERT OR REPLACE INTO finals
           (question_id, status, final_tex, solution_tex, rigor_tex, takeaways_tex, answer_type, answer_tex,
            hint_tex, answer_field_value, hint_field_value, answer_filled, hint_filled, prompt_version, created_at,
            mode, answer_key, book_check)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (qid, row["status"], final, parts.get("solution"), parts.get("notes"), parts["takeaways"], "KEY",
         answer_value, hint, fill_answer, fill_hint, 0, 0, subj_cfg(cfg)["prompt_version"], now_iso(),
         mode, key_json, parts.get("book_check")),
    )
    for field, value in fields:
        if value is None:
            continue
        if not pc.execute("SELECT 1 FROM provenance WHERE question_id=? AND field=? AND applied_at IS NULL",
                          (qid, field)).fetchone():
            pc.execute("INSERT INTO provenance (question_id, field, value, prompt_version, created_at) VALUES (?,?,?,?,?)",
                       (qid, field, value, subj_cfg(cfg)["prompt_version"], now_iso()))
    pc.commit()
    upsert_status(pc, qid, assembled=1)
    log_event(pc, qid, "assemble", f"ok ({mode}); fills answer={fill_answer is not None} hint={fill_hint is not None}")
    return {"question_id": qid, "ok": True, "mode": mode, "answer_field": fill_answer, "parts": len(key["parts"])}
