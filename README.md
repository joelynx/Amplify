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

## Data ingestion

The seed ingest tool populates the SQLite database from a CSV and optional companion files. It is **idempotent** — safe to re-run; duplicate rows (by `latex_hash`) are skipped.

### Basic usage

```bash
# Default ingest (TEST.csv + LanceDB embeddings + outlines + topic-depth)
uv run python -m app.tools.ingest

# Ingest a different CSV with images
uv run python -m app.tools.ingest --csv Files/Terms.csv --images-dir Files/images
```

### CLI options

| Flag | Default | Description |
|---|---|---|
| `--csv` | `Files/TEST.csv` | Path to the seed CSV |
| `--lancedb` | `Files/Testing/lancedb` | LanceDB directory for embeddings (optional) |
| `--outlines` | `app/data/seed/pre_db.outlines.json` | Solution outlines JSON (optional) |
| `--topic-depth` | `app/data/seed/pre_db.topic_depth.json` | Topic→depth JSON (optional) |
| `--images-dir` | _none_ | Directory of image files to copy into `teximages/` |
| `--db` | `app/data/appdata/amplify.db` | SQLite database path |

### Incomplete data support

The ingest pipeline handles CSVs with missing data gracefully:

- **Missing Topic / Branch / Subtopic**: Defaults to `"Uncategorized"` instead of skipping the row. A warning is surfaced in the CLI output and the Settings UI.
- **Missing embeddings**: Rows are imported with `NULL` embedding columns. Similarity search will be unavailable for these questions.
- **Missing solutions / hints / answers**: Imported as `NULL` — the app renders them when present and gracefully omits them when absent.
- **Type-hint rows**: Some exported spreadsheets prepend a row of column types (`varchar`, `text`, etc.). This is auto-detected and skipped.

### Supported CSV columns

| Column | Required | Description |
|---|---|---|
| `latexcode` | ✅ | LaTeX source for the question body |
| `Topic` | ❌ | Topic classification (defaults to "Uncategorized") |
| `Branch` | ❌ | Branch within topic (brackets stripped) |
| `Subtopic` | ❌ | Subtopic within branch |
| `Type` | ❌ | Question type (proof / numerical / explanation/reasoning) |
| `In Syllabus?` | ❌ | Whether the question is in syllabus (yes/no/blank) |
| `Source` | ❌ | Source attribution |
| `SubSource` | ❌ | Sub-source attribution |
| `Answer` | ❌ | Short answer |
| `Solution` | ❌ | Full solution (may contain LaTeX) |
| `Hints` | ❌ | Hints text |
| `Instructions` | ❌ | Special instructions |
| `Tags` | ❌ | Python list literal of tags, e.g. `['tag1', 'tag2']` |

## Embeddings

`questions.similarity_emb` / `questions.classification_emb` hold the same Gemini
`gemini-embedding-2` vector (3072 float32, little-endian, unit norm), computed
from the task prefix + question text + best available solution
(`generated_solution` with its attribution line stripped, else `solution`) plus
the referenced images. `emb_text_hash` / `emb_model` (migration 006) record
exactly what produced the stored vector, so the tool only embeds rows whose text
is new or has changed:

```bash
# GOOGLE_API_KEY in .env.local (git-ignored)
uv run python -m app.tools.reembed --dry-run              # rows pending + cost estimate
uv run python -m app.tools.reembed --run --mode batch     # Batch API, half price, 250-row jobs
uv run python -m app.tools.reembed --run                  # synchronous, ~1 row/s
```

Keep the prompt in `app/tools/reembed.py` byte-identical between runs, or the
new vectors will not be comparable with the stored ones (the 2026-10-21 A/B test
in `app/tools/embed_ab_test.py` found no better prompt).

## Image support

Questions with `\includegraphics{filename}` commands in their LaTeX source are fully supported.

### How it works

- **PDF generation**: Images are resolved via LaTeX's `\graphicspath`, which points to `app/data/appdata/teximages/`. XeLaTeX auto-resolves filenames without extensions (tries `.png`, `.jpg`, etc.).
- **Frontend display**: The `LatexContent` component detects `\includegraphics` commands, extracts image filenames, fetches them as base64 data URLs via the `resolve_images` IPC method, and renders them inline.
- **Image ingestion**: Use the `--images-dir` flag (CLI) or the Settings → Data → "Re-run seed ingest" button (UI) to copy image files into `teximages/`.

## Repo layout

- `app/` — Python backend
  - `app/ipc/` — PyWebView IPC API surface
  - `app/core/` — Domain models, filters, selection, stats, difficulty
  - `app/persistence/` — SQLite repositories, migrations, ingest pipeline
  - `app/tex/` — LaTeX preamble, sanitizers, PDF generation
  - `app/data/appdata/` — Runtime data (database, logs, teximages)
- `frontend/` — React + Vite + Tailwind UI
  - `frontend/src/pages/` — Route-level page components
  - `frontend/src/components/` — Reusable UI components (including `LatexContent`)
  - `frontend/src/lib/` — IPC bridge, utilities, theme engine
- `Files/` — Design docs, seed CSVs, LanceDB embeddings, images
