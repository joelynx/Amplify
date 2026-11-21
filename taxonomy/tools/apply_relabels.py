"""Move already-placed questions to the subtopic an Opus bank check proposed (owner-approved relabels).

Usage: python taxonomy/tools/apply_relabels.py --labels DIR [--apply]   (without --apply: dry run, no writes)
  DIR holds bank_relabels.json: {id: {topic, branch, subtopic, conf, how, db: [topic, branch, subtopic now]}}.

Each question must still sit where `db` says and the new node must exist in taxonomy/taxonomy.json, or nothing
is written. Tags and type are left alone. classification_conf / classification_how get the check's values.
Back up the DB first.
"""
import json, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.persistence.db import migrate  # noqa: E402

DB = ROOT / "app" / "data" / "appdata" / "amplify.db"


def main(apply: bool, run_dir: Path) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    nodes = {(n["topic"], n["branch"], n["subtopic"]) for n in json.loads((ROOT / "taxonomy" / "taxonomy.json").read_text("utf-8"))}
    labels = json.loads((run_dir / "bank_relabels.json").read_text("utf-8"))
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    migrate(conn)  # 013 adds the classification confidence columns
    moves, bad = [], []
    for k, r in sorted(labels.items(), key=lambda x: int(x[0])):
        q, new = int(k), (r["topic"], r["branch"], r["subtopic"])
        now = conn.execute("SELECT topic, branch, subtopic FROM questions WHERE question_id = ?", (q,)).fetchone()
        if new not in nodes or now is None or list(now) != r["db"]:
            bad.append((q, now and tuple(now), new))
        else:
            moves.append((*new, r.get("conf"), r.get("how"), q))
            print(f"{q}: {' / '.join(now)}  ->  {' / '.join(new)}")
    if bad:
        conn.close()
        raise SystemExit(f"{len(bad)} relabels do not match the DB or the tree, e.g. {bad[:3]}; nothing written")
    try:
        conn.execute("BEGIN")
        moved = sum(conn.execute("UPDATE questions SET topic = ?, branch = ?, subtopic = ?, classification_conf = ?, "
                                 "classification_how = ? WHERE question_id = ?", m).rowcount for m in moves)
        print(f"moved {moved} of {len(moves)}")
        if apply:
            conn.commit(); print("committed")
        else:
            conn.rollback(); print("dry run: rolled back")
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--labels" not in args:
        raise SystemExit(__doc__)
    main("--apply" in args, ROOT / args[args.index("--labels") + 1])
