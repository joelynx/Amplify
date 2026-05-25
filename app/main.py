"""Amplify entry point.

Step 0 scaffolding only: boots logging, logs startup, exits cleanly. Step 1 will replace
this with a PyWebView window loading the React frontend.
"""

from __future__ import annotations

import logging

from app.logging_setup import setup_logging

log = logging.getLogger("amplify.main")


def main() -> int:
    log_file = setup_logging()
    log.info("amplify starting (step 0 scaffold; log file: %s)", log_file)
    log.info("amplify ready — no window yet; step 1 wires PyWebView")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
