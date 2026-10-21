"""After fix_old_solutions.py apply: drop the repaired questions' rows from the
old-solution check CSV (a backup copy is kept) and print their ids, so that
check_old_solutions.py can re-verify exactly those rows with the independent
checker (question text + solution, the way the app compiles them).

Usage (repo root):
  python pipeline/scripts/confirm_fixed_solutions.py            # prints the id list, rewrites the CSV
  python pipeline/scripts/check_old_solutions.py --ids <ids> --workers 4
  python pipeline/scripts/report_old_solutions.py
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_old_solutions import CSV_PATH, FIELDS  # noqa: E402
from fix_old_solutions import FIXES_JSON  # noqa: E402


def main() -> None:
    results = json.loads(FIXES_JSON.read_text(encoding="utf-8"))
    fixed = sorted(int(q) for q, r in results.items() if r["ok"] and r["changed"])
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8", newline="")))
    keep = [r for r in rows if int(r["question_id"]) not in set(fixed)]
    backup = CSV_PATH.with_name(f"old_solutions_check_before_fixes_{time.strftime('%Y%m%d-%H%M%S')}.csv")
    shutil.copy2(CSV_PATH, backup)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(keep)
    print(json.dumps({"fixed": len(fixed), "rows_before": len(rows), "rows_after": len(keep), "backup": backup.name}))
    print(",".join(str(q) for q in fixed))


if __name__ == "__main__":
    main()
