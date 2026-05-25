# Amplify

Desktop application for generating LaTeX-typeset problem sets and (Phase 2) running interactive practice sessions against a curated question bank. Single-user, offline, locally bundled XeLaTeX.

See `Files/AMPLIFY_BUILD_SPEC (3).md` for the authoritative product spec and `Files/AMPLIFY_DEV_CYCLE.md` for the build sequence.

## Quick start (dev)

```bash
# Python side
uv sync
uv run python -m app.main

# Frontend side
cd frontend
npm install
npm run dev
```

## Repo layout

- `app/` — Python backend (IPC, core domain, persistence, tex/pdf, theming, tools)
- `frontend/` — React + Vite + Tailwind UI
- `Files/` — design docs and the canonical seed CSV / LanceDB embeddings (input artifacts)
