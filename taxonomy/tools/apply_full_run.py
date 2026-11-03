"""Write the reviewed full-run labels into the app DB.

Usage: python taxonomy/tools/apply_full_run.py [--apply]   (without --apply: dry run, no writes)

Writes, in one transaction, only for questions still `Uncategorized`:
  - topic/branch/subtopic from taxonomy/full_run/final_labels.json (wastebasket and subject-only rows stay Uncategorized);
  - type, only where the column is empty (existing source types are kept);
  - question_tags rows: key and supporting technique tags, and the task tag, with their role.
Every node must exist in taxonomy/taxonomy.json, or nothing is written. Back up the DB first.
"""
import collections, json, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "app" / "data" / "appdata" / "amplify.db"
TYPES = {"objective", "numerical", "proof", "explanation/reasoning"}


def main(apply: bool) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    nodes = {(n["topic"], n["branch"], n["subtopic"]) for n in json.loads((ROOT / "taxonomy" / "taxonomy.json").read_text("utf-8"))}
    labels = json.loads((ROOT / "taxonomy" / "full_run" / "final_labels.json").read_text("utf-8"))
    place, types, tags, skipped, bad = [], [], [], collections.Counter(), []
    for k, r in labels.items():
        q = int(k)
        if r["subtopic"] == "WASTEBASKET": skipped["wastebasket"] += 1
        elif not r["subtopic"]: skipped["subject only"] += 1
        elif (r["topic"], r["branch"], r["subtopic"]) not in nodes: bad.append(q)
        else: place.append((r["topic"], r["branch"], r["subtopic"], q))
        if r.get("type") in TYPES: types.append((r["type"], q))
        for role, names in (("key", r.get("key") or []), ("supporting", r.get("supporting") or []),
                            ("task", [r["task"]] if r.get("task") else [])):
            tags += [(q, t.strip(), role) for t in names if t and t.strip()]
    if bad:
        raise SystemExit(f"{len(bad)} labels point at nodes missing from taxonomy.json, e.g. {bad[:5]}; nothing written")
    conn = sqlite3.connect(DB)
    try:
        conn.execute("BEGIN")
        moved = sum(conn.execute("UPDATE questions SET topic = ?, branch = ?, subtopic = ? "
                                 "WHERE question_id = ? AND topic = 'Uncategorized'", p).rowcount for p in place)
        typed = sum(conn.execute("UPDATE questions SET type = ? WHERE question_id = ? AND type IS NULL", t).rowcount for t in types)
        tagged = sum(conn.execute("INSERT INTO question_tags (question_id, tag, role) VALUES (?, ?, ?) "
                                  "ON CONFLICT(question_id, tag) DO NOTHING", t).rowcount for t in tags)
        left = conn.execute("SELECT COUNT(*) FROM questions WHERE topic = 'Uncategorized'").fetchone()[0]
        print(f"placed {moved:,} of {len(place):,}; left Uncategorized {left:,} ({dict(skipped)}); "
              f"type filled {typed:,}; tag rows inserted {tagged:,} of {len(tags):,}")
        if apply:
            conn.commit(); print("committed")
        else:
            conn.rollback(); print("dry run: rolled back")
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


if __name__ == "__main__":
    main("--apply" in sys.argv[1:])
