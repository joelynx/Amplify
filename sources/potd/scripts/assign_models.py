"""Solving model and effort for each imported POTD question without a solution.
usage: python -I assign_models.py <POTD.csv> <amplify.db> <mods_potd_map.csv> <out.json>

Owner decisions of 2026-11-11 (Question_Sources.md section 5): with no published scores at these
levels, trust Opus 5.5 at medium and high and Fable 5.2 at high, bucketed by POTD's difficulty D
and by a source's density of hard problems:
  D 0-3 -> Opus 5.5 medium;  D 4-6 -> Opus 5.5 high;  D 7+ -> Fable 5.2 high.
A source whose problems are mostly hard (median D at least 7 over its imported rows) goes to Fable 5.2
high whole, whatever a single problem's D; the IMO Shortlist counts as a source of its own here.
A row with no valid D gets its source's median. D itself is not stored in the bank.
"""
import csv, json, sqlite3, statistics, sys, collections

OPUS, FABLE = "claude-opus-5-5", "claude-fable-5-2"


def bucket(d: float) -> tuple[str, str]:
    return (OPUS, "medium") if d <= 3 else (OPUS, "high") if d <= 6 else (FABLE, "high")


def main(potd_csv: str, db: str, map_csv: str, out: str) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sheet = {r["/f"]: r for r in csv.DictReader(open(potd_csv, encoding="utf-8"))}
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = []
    for m in csv.DictReader(open(map_csv, encoding="utf-8")):
        qid = int(m["question_id"])
        src, sub, sol = c.execute("SELECT source, subsource, solution FROM questions WHERE question_id=?", (qid,)).fetchone()
        key = "IMO Shortlist" if src == "International Mathematical Olympiad" and "Shortlist" in (sub or "") else src
        try:
            d = int(sheet[m["potd_number"]]["D"].strip())
        except ValueError:
            d = None
        rows.append((qid, key, d, bool(sol and sol.strip())))
    by_src = collections.defaultdict(list)
    for _, key, d, _ in rows:
        if d is not None:
            by_src[key].append(d)
    median = {k: statistics.median(v) for k, v in by_src.items()}
    hard = sorted(k for k, m in median.items() if m >= 7)
    questions, why = {}, collections.Counter()
    for qid, key, d, solved in rows:
        if solved:
            continue
        if key in hard:
            model, effort = FABLE, "high"
            why["hard source"] += 1
        else:
            model, effort = bucket(d if d is not None else median[key])
            why["D" if d is not None else "source median (no valid D)"] += 1
        questions[str(qid)] = {"model": model, "effort": effort}
    doc = {
        "note": "MODS POTD questions without a solution (imported 2026-11-12), with the model and effort that solve "
                "them; built by sources/potd/scripts/assign_models.py (its docstring has the rule). Listing a question "
                "here puts it in run_sub.py's scope whatever its source.",
        "hard_sources": hard,
        "questions": questions,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=0)
    counts = collections.Counter((v["model"], v["effort"]) for v in questions.values())
    print(len(questions), "questions;", dict(counts), dict(why))
    print("hard sources:", hard)


if __name__ == "__main__":
    main(*sys.argv[1:5])
