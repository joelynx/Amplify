"""Stub repository for the `templates` table (§3.3).

Step 6 wires save/load/delete and the Template Manager dialog. This module
exists now so the IPC layer can import the namespace without ImportError.
"""

from __future__ import annotations

import sqlite3


def list_names(conn: sqlite3.Connection) -> list[str]:
    return [row[0] for row in conn.execute("SELECT name FROM templates ORDER BY name")]
