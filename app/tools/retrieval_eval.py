"""
Evaluation of lecture-keyword retrieval (Low_Hanging_Fruit.md §3)
-----------------------------------------------------------------
Compares ways of turning a lecture's keywords into ten practice questions,
on the inputs in retrieval_eval_inputs.json. Every arm starts from the same
concepts (the ones the Lecture panel pre-ticks for the input, in the input's
subject) and, like quiz_concepts_start, splits the ten across them and
interleaves the result. Arms differ only in how a concept is filled:

  labels      the app today: questions carrying the concept's label (diverse pick)
  sem:V       every question in the subject, ranked by the concept's query vector
  lab:V       labelled questions first, in semantic order, then the rest
  div:V       the app's diverse pick, among the top of lab:V's order

with V = existing (the similarity_emb vectors: question + solution under one
symmetric instruction), plain (topic path + statement, as a document) or tech
(plain + technique tags). `sem:V@768` / `@1536` repeat sem:V on truncated
vectors; they are not judged, only checked against the judgements that exist.

Relevance is judged blind: the questions of all judged arms are pooled per
input, shuffled and graded 0/1/2 with the terms they practise (packets are
for Claude judges; a spot-check page lets the owner grade a sample blind).

Steps (repo root; nothing here calls an API):
  python -m app.tools.retrieval_eval run       # arms -> runs.json
  python -m app.tools.retrieval_eval packets   # judge/packet-NN.json + INSTRUCTIONS.md
  python -m app.tools.retrieval_eval score     # judge/answers-NN.json -> report.md, spotcheck.html
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import re
import sqlite3
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

from app.core import concepts, retrieval
from app.core.dpp import greedy_map
from app.core.filters import FilterError, assemble_where
from app.core.selection import pick
from app.persistence.repositories import subjects as subjects_repo
from app.tools import reembed
from app.tools.retrieval_embed import STORE_PATH

INPUTS = Path(__file__).with_name("retrieval_eval_inputs.json")
OUT = STORE_PATH.parent
RUNS = OUT / "runs.json"
JUDGE = OUT / "judge"
REVIEW = Path("pipeline/outputs/_review/retrieval")
N = 10
VARIANTS = ("existing", "plain", "tech")
SHORT_DIMS = (1536, 768)
DIVERSE_POOL, DIVERSE_MIN = 4, 12  # div:V picks diversely among the top 4 x need (at least 12)
PACKET_PAIRS = 360
STATEMENT_CHARS = 1800
IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{[^}]*\}")


# ---- run --------------------------------------------------------------------


def _app() -> sqlite3.Connection:
    app = sqlite3.connect(f"file:{reembed.DB_PATH.as_posix()}?mode=ro", uri=True)
    app.row_factory = sqlite3.Row  # as the app's own connection (the repositories expect it)
    return app


def _ids(app: sqlite3.Connection, filters: dict[str, Any], payload: dict | None) -> list[int]:
    where, params = assemble_where(filters, payload)
    return [r[0] for r in app.execute(f"SELECT question_id FROM questions WHERE {where}", params)]


def _matrix(app: sqlite3.Connection, store: sqlite3.Connection, variant: str) -> tuple[dict[int, int], np.ndarray]:
    if variant == "existing":
        rows = app.execute("SELECT question_id, similarity_emb FROM questions WHERE similarity_emb IS NOT NULL")
    else:
        rows = store.execute("SELECT question_id, emb FROM docs WHERE fmt = ?", (variant,))
    ids, vecs = [], []
    for qid, blob in rows:
        ids.append(int(qid))
        vecs.append(retrieval.decode(blob))
    return {q: i for i, q in enumerate(ids)}, retrieval.truncate(np.stack(vecs), None)


def _order(qvec: np.ndarray | None, rows: np.ndarray, ids: np.ndarray, mat: np.ndarray, norms: np.ndarray, dims: int | None) -> list[int]:
    """The scope (`rows` of `mat`, question `ids`) by cosine to `qvec` on the
    first `dims` components; same order as retrieval.rank, without copying rows."""
    if qvec is None or not len(rows):
        return []
    d = dims or mat.shape[1]
    q = retrieval.truncate(qvec, d)
    scores = (mat[rows, :d] @ q) / norms[rows]
    return [int(ids[i]) for i in np.lexsort((ids, -scores))]


def _take_from(arranged: list[list[int]], pos: dict[int, int], need: int, c: dict, taken: set[int]) -> list[int]:
    """allocate()'s fetch for a precomputed order per concept."""
    return retrieval.take(arranged[pos[id(c)]], need, taken)


def _take_diverse(
    arranged: list[list[int]], pos: dict[int, int], ex: tuple[dict[int, int], np.ndarray],
    need: int, c: dict, taken: set[int],
) -> list[int]:
    """The app's diverse pick (greedy MAP-DPP on similarity_emb), run on the
    top DIVERSE_POOL x need of the concept's order instead of a random pool."""
    order = [q for q in arranged[pos[id(c)]] if q not in taken]
    pool = [q for q in order[: max(DIVERSE_POOL * need, DIVERSE_MIN)] if q in ex[0]]
    if len(pool) <= need:
        return pool
    picked = [pool[i] for i in greedy_map(ex[1][[ex[0][q] for q in pool]], need)]
    return picked + [q for q in pool if q not in picked][: need - len(picked)]


def _session(chosen: list[dict], fetch) -> tuple[list[int], dict[int, int]]:
    pairs = concepts.allocate(chosen, N, fetch)
    ordered = concepts.interleave(pairs, key=lambda p: p[1])
    return [q for q, _ in ordered], {q: i for q, i in ordered}


def _subject(app: sqlite3.Connection, inp: dict):
    subject = subjects_repo.get(app, inp["subject"])
    if subject is None:
        raise SystemExit(f"{inp['id']}: no subject named {inp['subject']!r}")
    return subject


def load_confirmed() -> dict[str, dict[str, dict[str, set[tuple[str, str]]]]]:
    """Per input and term (by its text): the candidates a judge saw and the ones
    ticked, as (kind, label). Keyed by names, not list positions, so the answers
    survive changes to the matcher; a later packet overrides an earlier one."""
    out: dict[str, dict[str, dict[str, set[tuple[str, str]]]]] = {}
    for p in sorted(JUDGE.glob("confirm-*.json")):
        packet = json.loads(p.read_text(encoding="utf-8"))
        answers = JUDGE / packet["answers_file"]
        if not answers.exists():
            continue
        ans = json.loads(answers.read_text(encoding="utf-8"))
        for inp in packet["inputs"]:
            for t in inp["terms"]:
                cands = {c["i"]: (c["kind"], c["name"]) for c in t["candidates"]}
                ticked = {cands[i] for i in ans.get(inp["id"], {}).get(str(t["i"]), []) if i in cands}
                out.setdefault(inp["id"], {})[t["term"]] = {"seen": set(cands.values()), "ticked": ticked}
    return out


def cmd_run(a: argparse.Namespace) -> None:
    spec = json.loads(INPUTS.read_text(encoding="utf-8"))
    app = _app()
    store = sqlite3.connect(f"file:{STORE_PATH.as_posix()}?mode=ro", uri=True)
    qvecs = {k: retrieval.decode(e) for k, e in store.execute("SELECT key, emb FROM queries")}
    confirmed = load_confirmed() if a.concepts == "confirmed" else {}
    if a.concepts == "confirmed" and not confirmed:
        raise SystemExit(f"no {JUDGE}/confirmed-*.json yet: run confirm-packets and have them judged, or pass --concepts preticked")
    runs: list[dict] = []
    for inp in spec["inputs"]:
        subject = _subject(app, inp)
        payload = subject.to_payload()
        base = {"subject": subject.name, "reuse_questions": True}
        terms = concepts.match_text(app, inp["text"], subject)
        chosen: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for ti, t in enumerate(terms):
            conf = confirmed.get(inp["id"], {}).get(t["term"])
            unjudged = [m["label"] for m in t["matches"] if conf and (m["kind"], m["label"]) not in conf["seen"]]
            if confirmed and (unjudged or (t["matches"] and not conf)):
                raise SystemExit(f"{inp['id']} {t['term']!r} has unconfirmed candidates {unjudged}: run confirm-packets --only-new")
            for m in t["matches"]:
                ticked = (m["kind"], m["label"]) in conf["ticked"] if confirmed else m["selected"]
                if ticked and (m["kind"], m["label"]) not in seen:
                    seen.add((m["kind"], m["label"]))
                    chosen.append({"kind": m["kind"], "label": m["label"], "path": m["path"], "term": ti})
        scope = _ids(app, base, payload)
        labelled = [set(_ids(app, concepts.concept_filters(base, c), payload)) for c in chosen]

        def fetch_labels(need: int, c: dict, taken: set[int], subject=subject, base=base) -> list[int]:
            f = concepts.concept_filters(base, c)
            if taken:
                f["exclude_question_ids"] = sorted(taken)
            try:
                return [q.question_id for q in pick(app, f, need, subject=subject, strategy="diverse").questions]
            except FilterError:
                return []

        lst, conc = _session(chosen, fetch_labels) if chosen else ([], {})
        runs.append({
            **inp,
            "terms": [{"term": t["term"], "matches": t["matches"]} for t in terms],
            "chosen": chosen,
            "scope": len(scope),
            "labelled": [len(s) for s in labelled],
            "arms": {"labels": lst},
            "concept_of": {"labels": conc},
            "_scope": scope,
            "_labelled": labelled,
        })
        print(f"{inp['id']}: {len(chosen)} concepts, labels -> {len(lst)}", flush=True)

    ex = _matrix(app, store, "existing")  # the diverse pick always works on similarity_emb
    for variant in VARIANTS:
        index, mat = ex if variant == "existing" else _matrix(app, store, variant)
        print(f"{variant}: {len(index)} vectors", flush=True)
        dims_list = [None] + (list(SHORT_DIMS) if variant != "existing" else [])
        norms = {d: np.linalg.norm(mat[:, : d or mat.shape[1]], axis=1) for d in dims_list}
        for r in runs:
            if not r["chosen"]:
                continue
            have = [q for q in r["_scope"] if q in index]
            rows, ids = np.array([index[q] for q in have], dtype=np.int64), np.array(have, dtype=np.int64)
            for dims in dims_list:
                orders = [
                    _order(qvecs.get(retrieval.query_key(c["kind"], c["label"], c["path"])), rows, ids, mat, norms[dims], dims)
                    for c in r["chosen"]
                ]
                pos = {id(c): i for i, c in enumerate(r["chosen"])}
                arrangements = {f"sem:{variant}{'@' + str(dims) if dims else ''}": orders}
                if not dims:
                    arrangements[f"lab:{variant}"] = [
                        retrieval.labelled_first(o, r["_labelled"][i]) for i, o in enumerate(orders)
                    ]
                for arm, arranged in arrangements.items():
                    lst, conc = _session(r["chosen"], partial(_take_from, arranged, pos))
                    r["arms"][arm] = lst
                    r["concept_of"][arm] = conc
                if not dims:
                    lst, conc = _session(r["chosen"], partial(_take_diverse, arrangements[f"lab:{variant}"], pos, ex))
                    r["arms"][f"div:{variant}"] = lst
                    r["concept_of"][f"div:{variant}"] = conc
        if variant != "existing":
            del mat
    for r in runs:
        r.pop("_scope")
        r.pop("_labelled")
    OUT.mkdir(parents=True, exist_ok=True)
    RUNS.write_text(json.dumps({"n": N, "concepts": a.concepts, "inputs": runs}, ensure_ascii=False, indent=1), encoding="utf-8")
    empty = sum(1 for r in runs if not r["chosen"])
    print(f"wrote {RUNS}: {len(runs)} inputs ({empty} with no pre-ticked concept)", flush=True)


# ---- concept confirmation (stands in for the student) -------------------------

CONFIRM = """# Confirming lecture-keyword matches

A student pasted keywords from a lecture into a study app, inside one subject.
For each term the app lists candidate concepts from its topic tree (a topic, a
branch, a subtopic, or a technique tag) and the student ticks the ones that
mean what the term means. Do that ticking for the student.

Tick a candidate when it is the term's meaning in this subject: the same thing
under another name, or the natural home of the term (the concept a teacher
would file the term under). Do not tick a candidate that only shares a word
("Thermal Radiation" for "thermal resistance"), or one that is a different,
merely related idea. Several ticks are fine when several candidates fit; no
tick is fine when none does. Judge from the packet alone.

Write the answers file named in the packet as JSON, mapping each input id to
its terms (by index) and each term to the indices of the ticked candidates:

    {"<input id>": {"0": [0, 2], "1": [], ...}, ...}
"""


def cmd_confirm_packets(a: argparse.Namespace) -> None:
    spec = json.loads(INPUTS.read_text(encoding="utf-8"))
    app = _app()
    JUDGE.mkdir(parents=True, exist_ok=True)
    (JUDGE / "CONFIRM.md").write_text(CONFIRM, encoding="utf-8")
    done = load_confirmed() if a.only_new else {}
    items = []
    for inp in spec["inputs"]:
        terms = concepts.match_text(app, inp["text"], _subject(app, inp))
        listed = []
        for ti, t in enumerate(terms):
            if not t["matches"]:
                continue
            conf = done.get(inp["id"], {}).get(t["term"])
            if a.only_new and conf and all((m["kind"], m["label"]) in conf["seen"] for m in t["matches"]):
                continue
            listed.append({"i": ti, "term": t["term"], "candidates": [
                {"i": mi, "kind": m["kind"], "name": m["label"],
                 **({"in": m["path"].rsplit(retrieval.PATH_SEP, 1)[0]} if m["kind"] in ("subtopic", "branch") else {}),
                 "questions": m["count"]}
                for mi, m in enumerate(t["matches"])
            ]})
        if listed:
            items.append({"id": inp["id"], "subject": inp["subject"], "lecture": inp["text"], "terms": listed})
    first = 1 + max((int(p.stem.split("-")[1]) for p in JUDGE.glob("confirm-*.json")), default=0) if a.only_new else 1
    per = -(-len(items) // a.packets) if items else 0
    written = 0
    for i in range(a.packets):
        chunk = items[i * per : (i + 1) * per]
        if chunk:
            n = first + i
            (JUDGE / f"confirm-{n:02d}.json").write_text(
                json.dumps({"packet": n, "answers_file": f"confirmed-{n:02d}.json", "inputs": chunk},
                           ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
            written += 1
    n_terms = sum(len(x["terms"]) for x in items)
    print(f"{len(items)} inputs, {n_terms} terms to confirm, in {written} packet(s) from confirm-{first:02d} in {JUDGE}", flush=True)


# ---- packets ----------------------------------------------------------------

INSTRUCTIONS = """# Judging lecture-keyword retrieval

A student pasted keywords from a lecture into a study app, inside one subject,
and the app picked practice questions. Grade each question for how useful it is
as practice for THAT lecture. You see only the question statement (LaTeX), as a
student would; you do not know how it was found.

- **2**: practises one or more of the lecture's terms directly: the term is what
  the question is about, or central to solving it.
- **1**: related: uses a listed term only in passing, or practises a closely
  neighbouring idea that a lecture on these terms would plausibly cover.
- **0**: not practice for these terms (another topic, or only a surface word match).

Read terms in the subject's sense ("induction" in Electromagnetism is
electromagnetic induction; in Number Theory, the proof technique). Ignore
difficulty, length and the quality of the statement. Do not look anything up
and do not open other files: judge from the packet alone.

For every question with grade 1 or 2, list the indices (0-based) of the
lecture terms it practises. Grade every question of every input.

Write the answers file named in the packet as JSON:

    {"<input id>": [{"qid": 123, "rel": 2, "terms": [0]}, {"qid": 456, "rel": 0, "terms": []}, ...], ...}
"""


def _statement(latex: str | None) -> str:
    s = IMG_RE.sub("[figure]", latex or "").strip()
    return s if len(s) <= STATEMENT_CHARS else s[:STATEMENT_CHARS] + " …[truncated]"


def judged_arms(arms: dict[str, list[int]]) -> list[str]:
    return [a for a in arms if "@" not in a]


def cmd_packets(a: argparse.Namespace) -> None:
    runs = json.loads(RUNS.read_text(encoding="utf-8"))["inputs"]
    app = _app()
    JUDGE.mkdir(parents=True, exist_ok=True)
    (JUDGE / "INSTRUCTIONS.md").write_text(INSTRUCTIONS, encoding="utf-8")
    packets: list[list[dict]] = [[]]
    size = 0
    total = 0
    for r in runs:
        pool = sorted({q for arm in judged_arms(r["arms"]) for q in r["arms"][arm]})
        if not pool:
            continue
        random.Random(int(hashlib.sha256(r["id"].encode()).hexdigest(), 16)).shuffle(pool)
        marks = ",".join("?" * len(pool))
        stmt = dict(app.execute(f"SELECT question_id, latexcode FROM questions WHERE question_id IN ({marks})", pool))
        if size and size + len(pool) > a.pairs:
            packets.append([])
            size = 0
        packets[-1].append({
            "id": r["id"],
            "subject": r["subject"],
            "lecture": r["text"],
            "terms": [t["term"] for t in r["terms"]],
            "questions": [{"qid": q, "statement": _statement(stmt.get(q))} for q in pool],
        })
        size += len(pool)
        total += len(pool)
    for i, inputs in enumerate(packets, 1):
        (JUDGE / f"packet-{i:02d}.json").write_text(
            json.dumps({"packet": i, "answers_file": f"answers-{i:02d}.json", "inputs": inputs}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
    print(f"{len(packets)} packets, {total} question/input pairs, in {JUDGE}", flush=True)


# ---- score ------------------------------------------------------------------


def load_answers() -> dict[str, dict[int, dict]]:
    out: dict[str, dict[int, dict]] = {}
    for p in sorted(JUDGE.glob("answers-*.json")):
        for inp, rows in json.loads(p.read_text(encoding="utf-8")).items():
            out.setdefault(inp, {})
            for row in rows:
                out[inp][int(row["qid"])] = {"rel": int(row["rel"]), "terms": [int(t) for t in row.get("terms") or []]}
    return out


def metrics(r: dict, arm: str, judged: dict[int, dict]) -> dict | None:
    lst = r["arms"].get(arm)
    if lst is None or not r["chosen"]:
        return None
    grades = [judged.get(q) for q in lst]
    known = [g for g in grades if g is not None]
    actionable = {c["term"] for c in r["chosen"]}
    covered = {t for g in known if g["rel"] == 2 for t in g["terms"]} & actionable
    return {
        "strict": sum(1 for g in known if g["rel"] == 2) / N,
        "lenient": sum(1 for g in known if g["rel"] >= 1) / N,
        "coverage": len(covered) / len(actionable) if actionable else 0.0,
        "returned": len(lst),
        "judged": len(known) / len(lst) if lst else 1.0,
    }


def _boot(diffs: list[float], seed: int = 11, n: int = 4000) -> tuple[float, float]:
    if not diffs:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    arr = np.asarray(diffs)
    means = arr[rng.integers(0, len(arr), (n, len(arr)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _table(rows: list[list[str]]) -> str:
    head, *body = rows
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(out)


def _redundancy(app: sqlite3.Connection, lst: list[int], cache: dict[int, np.ndarray | None]) -> float | None:
    """Mean pairwise cosine of the picks' similarity_emb vectors (question +
    solution): high means near-duplicate practice."""
    for q in lst:
        if q not in cache:
            row = app.execute("SELECT similarity_emb FROM questions WHERE question_id = ?", (q,)).fetchone()
            cache[q] = retrieval.truncate(retrieval.decode(row[0]), None) if row and row[0] else None
    vecs = [cache[q] for q in lst if cache[q] is not None]
    if len(vecs) < 2:
        return None
    m = np.stack(vecs)
    s = m @ m.T
    n = len(vecs)
    return float((s.sum() - n) / (n * (n - 1)))


def cmd_score(_: argparse.Namespace) -> None:
    data = json.loads(RUNS.read_text(encoding="utf-8"))
    runs = data["inputs"]
    mode = data.get("concepts") or ("confirmed" if list(JUDGE.glob("confirmed-*.json")) else "preticked")
    answers = load_answers()
    app = _app()
    vec_cache: dict[int, np.ndarray | None] = {}
    arms = sorted({a for r in runs for a in r["arms"]}, key=lambda a: (a != "labels", "@" in a, a))
    per: dict[str, dict[str, dict]] = defaultdict(dict)
    missing = 0
    for r in runs:
        judged = answers.get(r["id"], {})
        for arm in judged_arms(r["arms"]):
            missing += sum(1 for q in r["arms"][arm] if q not in judged)
        for arm in arms:
            m = metrics(r, arm, judged)
            if m:
                m["redundancy"] = _redundancy(app, r["arms"][arm], vec_cache)
                per[arm][r["id"]] = m
    usable = [r for r in runs if r["chosen"]]
    lines = [
        "# Lecture-keyword retrieval: evaluation",
        "",
        f"{len(runs)} inputs; {len(usable)} had at least one pre-ticked concept (the rest are stage-1 misses and count for no arm). "
        f"{N} questions per input. strict = share of the {N} graded 2; lenient = graded 1 or 2; coverage = share of the "
        "input's matched terms with at least one question graded 2 for that term; redundancy = mean pairwise cosine "
        "of the picks' question+solution vectors (higher = more alike).",
        "",
    ]
    if missing:
        lines += [f"**{missing} judged-arm questions have no grade yet.**", ""]
    rows = [["arm", "strict", "lenient", "coverage", "Δ strict vs labels (95% CI)", "redundancy", "judged"]]
    for arm in arms:
        ms = per[arm]
        if not ms:
            continue
        ids = [r["id"] for r in usable if r["id"] in ms and r["id"] in per["labels"]]
        diffs = [ms[i]["strict"] - per["labels"][i]["strict"] for i in ids]
        lo, hi = _boot(diffs)
        red = [m["redundancy"] for m in ms.values() if m["redundancy"] is not None]
        rows.append([
            arm,
            f"{np.mean([m['strict'] for m in ms.values()]):.3f}",
            f"{np.mean([m['lenient'] for m in ms.values()]):.3f}",
            f"{np.mean([m['coverage'] for m in ms.values()]):.3f}",
            "" if arm == "labels" else f"{np.mean(diffs):+.3f} ({lo:+.3f}, {hi:+.3f})",
            f"{np.mean(red):.3f}" if red else "–",
            f"{np.mean([m['judged'] for m in ms.values()]):.0%}",
        ])
    lines += [_table(rows), ""]
    for key, title in (("style", "By input style (strict)"), ("subject", "By subject (strict)")):
        groups = sorted({r[key] for r in usable})
        main = [a for a in arms if "@" not in a]
        rows = [[key, "n", *main]]
        for g in groups:
            ids = [r["id"] for r in usable if r[key] == g]
            rows.append([g, str(len(ids)), *[
                f"{np.mean([per[a][i]['strict'] for i in ids if i in per[a]]):.2f}" if any(i in per[a] for i in ids) else "–"
                for a in main
            ]])
        lines += [f"## {title}", "", _table(rows), ""]
    # Per term, the concepts a student would keep: the judge-confirmed ones, or the
    # pre-ticked ones in a --concepts preticked run. Not `chosen`: a concept two
    # terms share is chosen once, under the first term.
    confirmed = load_confirmed() if mode == "confirmed" else {}

    def kept(r: dict, t: dict) -> set[tuple[str, str]]:
        if mode == "confirmed":
            return confirmed.get(r["id"], {}).get(t["term"], {}).get("ticked", set())
        return {(m["kind"], m["label"]) for m in t["matches"] if m["selected"]}

    n_terms = sum(len(r["terms"]) for r in runs)
    n_matched = sum(1 for r in runs for t in r["terms"] if kept(r, t))
    unlisted = [(r["id"], t["term"]) for r in runs for t in r["terms"] if not t["matches"]]
    wrong = [(r["id"], t["term"], t["matches"][0]["label"]) for r in runs for t in r["terms"] if t["matches"] and not kept(r, t)]
    pre = [(r, t) for r in runs for t in r["terms"] if any(m["selected"] for m in t["matches"])]
    pre_ok = sum(1 for r, t in pre if {(m["kind"], m["label"]) for m in t["matches"] if m["selected"]} & kept(r, t))
    lines += [
        "## Stage 1 (concept matching)",
        "",
        f"Concepts used: {mode}. {n_matched} of {n_terms} terms have a usable concept; {len(pre)} terms had one pre-ticked, "
        f"{pre_ok} of them with a pre-ticked concept the judge confirmed. Inputs left with no concept: "
        + (", ".join(f"{r['id']} ({r['text']})" for r in runs if not r["chosen"]) or "none") + ".",
        "",
        f"Terms with no candidate at all ({len(unlisted)}; alias candidates): "
        + "; ".join(f"{t} ({i})" for i, t in unlisted) + ".",
        "",
        f"Terms whose candidates were all wrong ({len(wrong)}): "
        + "; ".join(f"{t} (top: {lab})" for _, t, lab in wrong) + ".",
        "",
    ]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(per, indent=1), encoding="utf-8")
    write_spotcheck(runs, answers)
    print("\n".join(lines))


# ---- spot-check page ---------------------------------------------------------


def write_spotcheck(runs: list[dict], answers: dict[str, dict[int, dict]], per_grade: int = 34) -> None:
    """A blind sample for the owner: equal numbers of questions the judges
    graded 0, 1 and 2, shown without the grade; the owner's grades come back as
    JSON from the page's Copy button."""
    app = _app()
    by_id = {r["id"]: r for r in runs}
    pool: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for inp, graded in answers.items():
        for q, g in graded.items():
            pool[g["rel"]].append((inp, q))
    rng = random.Random(5)
    sample = [p for rel in (0, 1, 2) for p in rng.sample(pool[rel], min(per_grade, len(pool[rel])))]
    rng.shuffle(sample)
    cards = []
    for n, (inp, q) in enumerate(sample):
        r = by_id[inp]
        latex = app.execute("SELECT latexcode FROM questions WHERE question_id = ?", (q,)).fetchone()[0]
        terms = " · ".join(f"<b>{i}</b> {html.escape(t['term'])}" for i, t in enumerate(r["terms"]))
        cards.append(
            f'<section class="card" data-key="{html.escape(inp)}:{q}"><div class="meta">{n + 1}/{len(sample)} · '
            f'{html.escape(r["subject"])} · lecture: <i>{html.escape(r["text"])}</i><br>terms: {terms}</div>'
            f'<div class="q">{html.escape(_statement(latex))}</div><div class="btns">'
            + "".join(f'<button data-g="{g}">{g}</button>' for g in (0, 1, 2))
            + "</div></section>"
        )
    key = {f"{inp}:{q}": answers[inp][q]["rel"] for inp, q in sample}
    (OUT / "spotcheck_key.json").write_text(json.dumps(key), encoding="utf-8")
    REVIEW.mkdir(parents=True, exist_ok=True)
    page = SPOT_PAGE.replace("{{CARDS}}", "\n".join(cards)).replace("{{N}}", str(len(sample)))
    (REVIEW / "spotcheck.html").write_text(page, encoding="utf-8")


SPOT_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Retrieval spot-check</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
<style>
:root{--bg:#f7f7f5;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#deded8;--pick:#2f6fdb}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecece8;--muted:#a3a39c;--card:#20201e;--line:#34342f;--pick:#6c9cf0}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.meta{color:var(--muted);font-size:13px;margin-bottom:8px}.q{white-space:pre-wrap;overflow-wrap:anywhere}
.btns{margin-top:10px;display:flex;gap:8px}button{font:inherit;padding:6px 16px;border-radius:8px;border:1px solid var(--line);background:transparent;color:var(--fg);cursor:pointer}
button.on{background:var(--pick);border-color:var(--pick);color:#fff}
header{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line)}
</style></head><body><main>
<header><b>Retrieval spot-check</b> · grade each question for the lecture shown: 2 = practises a listed term directly,
1 = related, 0 = not practice for these terms. <span id="count"></span> <button id="copy">Copy my grades</button></header>
{{CARDS}}
</main><script>
const KEY="retrieval-spotcheck";let g={};try{g=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
const cards=[...document.querySelectorAll(".card")];
function paint(){cards.forEach(c=>c.querySelectorAll("button").forEach(b=>b.classList.toggle("on",g[c.dataset.key]===+b.dataset.g)));
document.getElementById("count").textContent=Object.keys(g).length+"/{{N}} graded";}
cards.forEach(c=>c.querySelectorAll("button").forEach(b=>b.onclick=()=>{g[c.dataset.key]=+b.dataset.g;try{localStorage.setItem(KEY,JSON.stringify(g))}catch(e){}paint()}));
document.getElementById("copy").onclick=()=>navigator.clipboard.writeText(JSON.stringify(g)).then(()=>alert("Copied. Paste it into the chat."));
paint();
document.addEventListener("DOMContentLoaded",()=>{if(window.renderMathInElement)renderMathInElement(document.body,{delimiters:[
{left:"$$",right:"$$",display:true},{left:"\\\\[",right:"\\\\]",display:true},{left:"$",right:"$",display:false},{left:"\\\\(",right:"\\\\)",display:false}],throwOnError:false})});
</script></body></html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("confirm-packets")
    p.add_argument("--packets", type=int, default=2)
    p.add_argument("--only-new", action="store_true", help="only terms with candidates no judge has seen")
    p = sub.add_parser("run")
    p.add_argument("--concepts", choices=["confirmed", "preticked"], default="confirmed")
    p = sub.add_parser("packets")
    p.add_argument("--pairs", type=int, default=PACKET_PAIRS, help="question/input pairs per packet")
    sub.add_parser("score")
    a = ap.parse_args()
    {"confirm-packets": cmd_confirm_packets, "run": cmd_run, "packets": cmd_packets, "score": cmd_score}[a.cmd](a)


if __name__ == "__main__":
    main()
