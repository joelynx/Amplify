"""Stub repository for the `psets` / `pset_questions` tables (§3.4).

Step 5 wires the insert path after a successful PDF compile; Step 8 wires the
list/re-export/delete operations for the History page. Stubbed now so imports
resolve cleanly.
"""

from __future__ import annotations

import sqlite3


def count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM psets").fetchone()[0])
