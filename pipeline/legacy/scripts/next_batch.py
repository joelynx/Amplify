"""Select the next questions to process and record them as the current batch.

Usage:
  python next_batch.py                 # next `batch_size` unfinished target questions
  python next_batch.py --n 5           # smaller batch
  python next_batch.py --ids 12422,12423
  python next_batch.py --pilot 25      # stratified pilot sample (images, lengths, sources)

Questions already in progress (a non-final status) come first so an
interrupted session resumes where it stopped. Prints the batch as JSON.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    app_conn,
    fetch_question,
    is_blank,
    is_done,
    load_config,
    now_iso,
    pipe_conn,
    resolve_image,
    save_current_batch,
    target_question_ids,
    teximages_dir,
    upsert_status,
    write_progress,
)

IMG_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")


def stratified_pilot(app, cfg, cand_ids: list[int], n: int, seed: int = 2026) -> list[int]:
    rng = random.Random(seed)
    tex = teximages_dir(cfg)
    qs = {qid: fetch_question(app, qid) for qid in cand_ids}

    def has_resolvable_image(q):
        names = IMG_RE.findall(q["latexcode"])
        return bool(names) and all(resolve_image(x, tex) for x in names)

    chosen: list[int] = []
    pool = set(cand_ids)

    def take(filter_fn, k):
        opts = [i for i in pool if filter_fn(qs[i])]
        rng.shuffle(opts)
        for i in opts[:k]:
            chosen.append(i)
            pool.discard(i)

    take(has_resolvable_image, min(4, max(1, n // 6)))
    take(lambda q: is_blank(q["solution"]), max(1, n // 8))
    take(lambda q: not is_blank(q["answer"], cfg["empty_answer_sentinels"]), max(1, n // 8))

    # Spread the rest across sources, alternating short and long old solutions.
    by_source: dict[str, list[int]] = {}
    for i in pool:
        by_source.setdefault(qs[i]["source"], []).append(i)
    for src in by_source:
        by_source[src].sort(key=lambda i: len(qs[i]["solution"] or ""))
    sources = sorted(by_source, key=lambda s: -len(by_source[s]))
    flip = False
    while len(chosen) < n and any(by_source.values()):
        for src in sources:
            if len(chosen) >= n:
                break
            lst = by_source[src]
            if not lst:
                continue
            # pick from the short or long half alternately, at random within it
            half = lst[: max(1, len(lst) // 2)] if not flip else lst[len(lst) // 2 :]
            pick = rng.choice(half)
            lst.remove(pick)
            chosen.append(pick)
            flip = not flip
    return sorted(chosen)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int)
    ap.add_argument("--ids")
    ap.add_argument("--pilot", type=int)
    ap.add_argument("--kind")
    ap.add_argument("--include", help="comma-separated ids forced into the batch (e.g. reruns)")
    a = ap.parse_args()

    cfg = load_config()
    app = app_conn(cfg)
    pc = pipe_conn()
    all_ids = target_question_ids(app, cfg)
    rows = {r["question_id"]: r for r in pc.execute("SELECT * FROM status")}
    not_done = [i for i in all_ids if not is_done(rows.get(i))]

    if a.ids:
        ids = [int(x) for x in a.ids.split(",") if x.strip()]
        kind = a.kind or "manual"
    elif a.pilot:
        ids = stratified_pilot(app, cfg, not_done, a.pilot)
        kind = a.kind or "pilot"
    else:
        n = a.n or int(cfg["batch_size"])
        in_progress = [i for i in not_done if rows.get(i) is not None and rows[i]["status"] != "pending"]
        seen = set(in_progress)
        fresh = [i for i in not_done if i not in seen]
        ids = (in_progress + fresh)[:n]
        kind = a.kind or "normal"
    if a.include:
        forced = [int(x) for x in a.include.split(",") if x.strip()]
        ids = sorted(set(ids) | set(forced))

    batch = (pc.execute("SELECT MAX(batch) FROM batches").fetchone()[0] or 0) + 1
    pc.execute(
        "INSERT INTO batches (batch, question_ids, kind, created_at) VALUES (?,?,?,?)",
        (batch, json.dumps(ids), kind, now_iso()),
    )
    pc.commit()
    for qid in ids:
        if rows.get(qid) is None:
            upsert_status(pc, qid, status="pending", batch=batch, prompt_version=cfg["prompt_version"])
        else:
            upsert_status(pc, qid, batch=batch)
    save_current_batch(
        {"batch": batch, "kind": kind, "ids": ids, "active": ids, "dropped": {}, "created_at": now_iso()}
    )
    write_progress(pc)
    print(
        json.dumps(
            {
                "batch": batch,
                "kind": kind,
                "ids": ids,
                "target_total": len(all_ids),
                "remaining_before_batch": len(not_done),
            }
        )
    )


if __name__ == "__main__":
    main()
