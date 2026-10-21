"""Generate Claude Code subagent definitions (.claude/agents/pipeline-*.md)
from config.json so model and effort are pinned per role by construction.

Re-run after any config.json change (and bump prompt_version if prompts changed).
Note: .claude/ is git-ignored in this repo, so these files are local to the
machine; config.json remains the source of truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_DIR, load_config, write_text  # noqa: E402

BODY = (
    "You are one stage of a fixed solution-generation pipeline. Your entire task is in the prompt "
    "file you are pointed at. Read it in full, follow it exactly, write only to the output path it "
    "names, and reply with only the one-line status it specifies. Do not read other files unless "
    "the instructions tell you to."
)


def agent(name: str, desc: str, model: str, effort: str, tools: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {desc}\n"
        f"model: {model}\n"
        f"effort: {effort}\n"
        f"tools: {tools}\n"
        "---\n\n"
        f"{BODY}\n"
    )


def main() -> None:
    cfg = load_config()
    out = REPO_DIR / ".claude" / "agents"
    files = {}
    for level, st in cfg["solver"].items():
        files[f"pipeline-solver-{level.lower()}"] = agent(
            f"pipeline-solver-{level.lower()}",
            f"Solution-pipeline solver at the {level} level. Only the pipeline orchestrator uses it.",
            st["model"], st["effort"], "Read, Write, Glob",
        )
    files["pipeline-reviewer"] = agent(
        "pipeline-reviewer", "Solution-pipeline reviewer. Only the pipeline orchestrator uses it.",
        cfg["reviewer"]["model"], cfg["reviewer"]["effort"], "Read, Write, Glob, Bash",
    )
    files["pipeline-hint"] = agent(
        "pipeline-hint", "Solution-pipeline hint writer. Only the pipeline orchestrator uses it.",
        cfg["hint"]["model"], cfg["hint"]["effort"], "Read, Write, Glob",
    )
    files["pipeline-router"] = agent(
        "pipeline-router", "Solution-pipeline difficulty router. Only the pipeline orchestrator uses it.",
        cfg["router"]["model"], cfg["router"]["effort"], "Read, Write, Glob",
    )
    for name, text in files.items():
        write_text(out / f"{name}.md", text)
        print(f"wrote {out / (name + '.md')}")


if __name__ == "__main__":
    main()
