# Amplify — Dev Cycle

**Companion to** `AMPLIFY_BUILD_SPEC.md`. The spec says *what* to build; this doc says *how we'll work through it*. Section references (§N) point into the spec.

---

## Cycle philosophy

- **Each step ends in a demoable state.** No half-finished modules carried into the next step. If a step would leave something dangling, split it.
- **Per-step inner loop:** write → run locally → eyeball end-state against the spec → fix → commit. Treat the "End state" line of each step as the exit criterion.
- **Three mandatory sign-off gates:** after step 4 (Generate page wired), step 7 (Stats v1), step 14 (MVP complete). Agent stops, demos, and waits for the project owner before continuing.
- **Idempotence is a recurring requirement.** Every ingest, every reload, every recompute must be safe to re-run. Build it that way the first time, not as a retrofit.
- **The runtime is offline.** Zero outbound network calls. If a step *seems* to need an LLM/embedding API, re-read §1, §4, §12 — the answer is "the data is in the seed bundle."
- **No silent design invention.** If something is genuinely under-specified during a step, stop and ask the project owner.

---

## Step 0 — Pre-flight

Before any application code:

1. Pin Python 3.11+. Pick a package manager (uv or poetry); commit a lockfile.
2. Initialize the repo: `amplify/` Python package + `frontend/` Vite project side-by-side. Drop in the directory skeleton from §2.2 (empty folders are fine — they get filled later). `.gitignore` covers `appdata/`, `dist/`, `__pycache__/`, `node_modules/`, `*.pdf` in the working dir.
3. Install Python deps: pywebview, openpyxl, numpy, a JSON-schema/pydantic library for IPC payload validation, pytest.
4. Install frontend deps: React, Vite, Tailwind, shadcn/ui, Zustand, D3, lucide-react.
5. Drop TinyTeX into `app/resources/tinytex/` for macOS and Windows. Document the Linux fallback expectation (system XeLaTeX from `PATH`; Generate button surfaces install instructions if absent).
6. Stand up the rotating file logger at `app/data/appdata/logs/app.log` (1 MB × 3 backups, UTF-8) per §14, even though there's nothing to log yet.
7. CI hook: `pytest` and `vite build` on every push.

**End state.** `python -m app.main` and `npm run dev` both start (even if they do nothing useful). Repo passes lint/format on a clean checkout.

---

## Step 1 — Project scaffold

**Goal.** A window opens. That's it.

**What we'll be doing.**
- `app/main.py` boots logging, opens a SQLite handle (just confirms the DB file is creatable — no schema yet), launches a PyWebView window.
- The window loads `frontend/dist/index.html` in production builds; in dev, point it at the Vite dev server (`http://localhost:5173`) so HMR works.
- `app/ipc/api.py` exposes a single `ping()` returning `"pong"`.
- `frontend/src/lib/ipc.ts` is the typed wrapper over `window.pywebview.api.*`. Wire `ping`.
- React renders one page that calls `ping()` on mount and prints the result.
- JS-side `console.log` forwarder via an IPC `log(level, message)` call, writing into the same rotating logger from Step 0.

**Touchpoints.** `app/main.py`, `app/ipc/api.py`, `frontend/src/main.tsx`, `frontend/src/lib/ipc.ts`, `vite.config.ts`, `tailwind.config.ts`.

**End state.** Window opens, prints "pong" from Python. Vite hot-reload works inside the PyWebView shell.

---

## Step 2 — DB + migrations + seed ingest

**Goal.** SQLite holds the full seed bundle after running one CLI command. Re-running it is a no-op.

**What we'll be doing.**
- `app/persistence/db.py` — connection manager + `migrate()` that scans `migrations/`, runs un-applied SQL files in numeric order, records them in a `migrations` table.
- `001_initial.sql` — every table from §3: `questions` (with `classification_emb` and `similarity_emb` as BLOB), `question_tags`, `templates`, `psets`, `pset_questions`, `subjects`, `configs`, `quizzes`, `quiz_attempts`, `migrations`.
- `app/persistence/ingest/seed.py` implementing §4.1 exactly:
  - Open `pre_db.xlsx` with `openpyxl(read_only=True)`. Skip the type-hint header (row 1); use row 2 as columns. Main sheet only.
  - Per row: drop `Stream` / `Subject` / `AnsCode` columns; strip `[…]` from `Branch`; coerce `In Syllabus?` (`yes`/`no`/blank) to 0/1; parse `Tags` with `ast.literal_eval`; compute `latex_hash = sha256(normalize(latexcode))`; skip if hash already present.
  - Insert `questions` row + N `question_tags` rows.
  - Auto-write a clean `pre_db.csv` mirror of the main sheet.
  - Load `pre_db.embeddings.npz`. For each `question_id` present in both DB and npz, write `vectors[i]` as 12 288-byte (3072 × 4) float32 little-endian BLOB into both `classification_emb` and `similarity_emb`.
  - Load `pre_db.outlines.json`. For each matching `question_id`, write the value into `solution_outline`.
  - Load `pre_db.topic_depth.json`. Store the entire object verbatim into `configs.TOPIC_DEPTH_MAP`.
  - Embeddings/outlines/depth load steps are best-effort: missing or malformed file → log warning, continue.
- Seed `configs` defaults: `THEME_SELECTED`, `DEFAULT_NO_QUESTIONS`, `FILE_SAVE_LOCATION`, `LAST_USED_SUBJECT`, `PDF_LEFT_HEADER`, `PDF_RIGHT_HEADER`, `PDF_TITLE_LINE`, `PDF_INSTRUCTIONS`, `EMBED_MODEL_VERSION` (read from seed metadata), `APPNAME`, `VERSION`.
- `app/tools/ingest.py` exposing `python -m app.tools.ingest`.

**Validation.**
- Run ingest twice. Second run inserts 0 rows.
- Spot-check a random row: correct topic/branch/subtopic, non-empty `latex_hash`, 12 288-byte BLOB if its ID is in the npz.
- Delete one companion file, re-run — completes successfully, the relevant column is just NULL/missing.

**End state.** SQLite file in `appdata/` with the full seed loaded; embeddings, outlines, topic-depth populated where available.

---

## Step 3 — Core models, repositories, filter assembly

**Goal.** From the JS console (`window.pywebview.api.*`), we can pull rows and counts out of the DB.

**What we'll be doing.**
- `app/core/models.py` — dataclasses for `Question`, `Template`, `PSet`, `Subject`, `Quiz`. Pure Python, no DB.
- `app/persistence/repositories/` — one repo per aggregate (questions, templates, psets, subjects, configs). Repo methods take/return `core/models` objects, **never raw SQLite rows**.
- `app/core/filters.py` — assemble a SQL `WHERE` from a `filters` dict per §7.1, §7.2:
  - Subject scoping: topic ∈ subject.topics AND branch ∉ excluded_branches[topic] AND subtopic ∉ excluded_subtopics[topic][branch].
  - Deepest-non-empty-level rule for the tree (handle both fully-checked-parent and per-leaf shapes).
  - Sources/types: `IN` set or unrestricted if empty.
  - Tags: compulsory ⊆ tags, optional ∩ tags ≠ ∅ (or optional empty), excluded ∩ tags = ∅.
  - `difficulty_rating ≥ min_difficulty`.
  - `in_syllabus_only` → `questions.in_syllabus = 1` (independent of subject).
  - `reuse_questions == false` → `times_used = 0`.
  - **Reject `compulsory ∩ excluded ≠ ∅`** with an explicit error.
- `app/core/selection.py` — `pick(filters, n)` issues `SELECT … ORDER BY RANDOM() LIMIT n`; returns `{questions, shortfall}` if matches < n.
- IPC additions: `count_matching_questions`, `get_random_questions`, plus all of §5.1: `get_topics`, `get_branches`, `get_subtopics`, `get_concept_tree`, `get_types`, `get_sources`, `get_all_tags`.

**Validation.**
- Unit tests for `filters.py` covering each branch with golden inputs.
- From JS console: `await ipc.count_matching_questions({topics:['Calculus'], in_syllabus_only:true})` returns the same number as the equivalent hand-written `sqlite3` query.

**End state.** Every read endpoint the Generate page will need is callable from JS and returns the right shape.

---

## Step 4 — Generate page UI (no PDF yet)

**Goal.** The Generate form is fully wired to live counts. Buttons exist; Generate is a no-op for now.

**What we'll be doing.**
- `frontend/src/pages/Generate.tsx` and supporting components, top-to-bottom per §8.1:
  - **Required block:** Template combobox (searchable) + info button (opens Template Manager dialog stub for now); Subject combobox sourced from `subjects` (defaults to active subject; "(Any subject)" sentinel; changing it clears the tree and tag trays).
  - **CheckableTree:** 3 levels, tri-state checkboxes (parent cascades down, partial propagates up), search box that filters visible leaves *without* changing selection state, "Clear search" and "Collapse leaves" buttons. Sourced from `get_concept_tree(subject)`.
  - **TagTray:** searchable combobox feeding chips into a flow-layout tray. Two header toggles **Compulsory?** and **Exclude**. Adding a chip while Exclude is on forces Compulsory on; turning Compulsory off while Exclude is on also turns Exclude off. Color-coded chips: compulsory blue, optional grey, excluded red.
  - **Sources tray** and **Types tray:** same pattern as TagTray, single-category.
  - **Output settings:** question-count spinbox (1–200, default from configs); Reuse questions checkbox; Include sources checkbox (default on); **Solutions combobox** (None / Appendix / Interleaved / Outline only) — value is recorded into the form draft but not yet rendered into a PDF; sub-toggle for Outline-only (Appendix/Interleaved); Min difficulty spinbox 0–20; In-syllabus only checkbox (default on); Save directory (read-only label + Browse button using the system file dialog).
  - **Action row:** Save Template (greyed when form payload exactly matches a saved template); Export LaTeX; Generate PDF (disabled-with-tooltip if validation fails — minimum required: ≥1 checked leaf, save dir, count ≥ 1; subject is *not* required).
  - **Status bar:** live "N questions match your current filters" via debounced `count_matching_questions` (~150 ms).
- **Dynamic dropdowns** (§7.3): tag/source/type dropdowns re-query on every change to subject / tree / sources / types / difficulty / other tags.
- `frontend/src/state/` — Zustand slices for active subject, active theme, generate-form draft.

**Validation.**
- Tweak any control; the live counter updates within ~150 ms.
- Walk all five tag edge cases from §7.2 manually.
- Subject change clears tree and tag trays.
- Validation tooltips appear above the offending control on disabled-state hover.

> **🛑 SIGN-OFF GATE 1.** Demo to project owner. Confirm Generate form looks and feels right. **No PDF generation yet.** Do not start step 5 without sign-off.

---

## Step 5 — PDF generation pipeline

**Goal.** Real PDFs land on disk. PSet rows get written. All four solution placements render correctly.

**What we'll be doing.**
- `app/tex/preamble.py` — the fixed preamble from §6.2. `<image_path>` resolves to `app/data/appdata/teximages/` with **forward slashes on Windows** (LaTeX needs them).
- `app/tex/sanitize.py` — `escape_latex`, `sanitize_latex_basic`, `sanitize_latex_extended` per §6.3, with **golden-file unit tests**. Question bodies are NEVER sanitized; sanitizers run only over the user-typed header/title/instructions content.
- `app/tex/header_vars.py` — token substitution per §6.4: `<S>`, `<T>`, `<N>`, `<K>`, `<Q>`, `<src>`, `<P>`, `<d>`, `<D>`. Image-mode for left/right header (input becomes read-only; stored value is `\includegraphics[width=1cm]{<absolute path>}`; trash button reverts).
- `app/tex/solutions.py` — the four placement layouts per §6.5:
  - `none` (questions only).
  - `appendix` (questions in body, `\newpage`, "Solutions" section, each headed `\textbf{Q\arabic{}}`).
  - `interleaved` (each question immediately followed by its solution).
  - `outline_only` (uses `solution_outline`; sub-toggle picks appendix-vs-interleaved; **NULL outline falls back to full solution and logs a warning**).
- `app/tex/pdfgen.py` — `assemble(questions, output_settings) → tex_str`; XeLaTeX runner in a temp dir; capture stdout/stderr to the log; on success copy PDF to `<save_dir>/<Subject>_YYYYMMDD_HHMMSS.pdf`, atomically `INSERT INTO psets` + N `pset_questions` rows, `UPDATE questions SET times_used = times_used + 1, date_last_accessed = now() WHERE question_id IN (…)`; on compile failure, write the `.tex` to the user's directory as fallback and return `{success:false, fallback:'<path>.tex', errors:'<tail of XeLaTeX log>'}`.
- IPC: `generate_pdf`, `export_tex`.

**Validation.**
- Generate a 5-question PDF in each of the four placement modes; eyeball them.
- Force a compile error (temporarily inject malformed LaTeX into a test row) — confirm the `.tex` fallback path lands and the frontend modal shows it with a clickable `file://` link.
- After a successful generate: `psets` and `pset_questions` rows exist; involved questions' `times_used` incremented by exactly 1, `date_last_accessed` updated.
- Sanitizer golden-file tests pass.

**End state.** The Generate button does what the user came for.

---

## Step 6 — Templates

**Goal.** Save / load / rename / delete the entire Generate form state.

**What we'll be doing.**
- IPC: `list_templates`, `template_name_available`, `load_template`, `save_template`, `delete_template`.
- Template Manager dialog (rename + delete) wired to the info button next to the Template combobox.
- "Save Template" button greys when the current form payload exactly matches a saved template's payload.
- `templates` row stores the JSON snapshot of the form, including the Solutions combobox + sub-toggle.

**Validation.** Save → reload window → re-load template → form fields restore identically (verify the Solutions sub-toggle round-trips).

---

## Step 7 — Stats v1

**Goal.** The 8 numbers and a single distribution chart, themed.

**What we'll be doing.**
- `app/core/stats.py` — pure functions returning the 8 numbers from §9.1 (PSets Generated, Total Questions Seen, Unique Questions Seen, Fraction of Questions Seen, Max Questions in Single PSet, Max Multiplicity, Average Multiplicity, Average Difficulty Rating) and the subject-or-topic distribution dataset.
- `frontend/src/pages/Stats.tsx` — 8 numeric cards + one D3 chart (start with a pie or radar over subject distribution; if radar, carry forward `judge()` from the prior prototype to color by coefficient-of-variation).
- **Custom `.amplify-tooltip` component** — themed; **not** D3's default tooltip (§9.3). Default Light + Default Dark variants for now; flavor-theme variants ride along in step 12.
- IPC: `get_stats`, `get_subject_distribution`, `get_topic_distribution`.

**Validation.** Generate a few PSets → numbers update. Subject scoping works. Tooltip is the custom one.

> **🛑 SIGN-OFF GATE 2.** Demo Stats v1 to project owner. Do not advance until sign-off.

---

## Step 8 — History page

**Goal.** Every generated PSet is browseable, re-exportable, and "Generate similar"-able.

**What we'll be doing.**
- IPC: `list_psets`, `load_pset`, `delete_pset`, `re_export_pset_pdf`, `get_pset_filters`, `open_pset_file`.
- `frontend/src/pages/History.tsx` — list with date/subject/N questions; row actions:
  - **Open** — opens the saved PDF in OS viewer.
  - **Re-export PDF** — same questions, fresh PDF in user's save dir.
  - **Generate similar** — calls `get_pset_filters(pset_id)`, navigates to `/generate`, pre-fills the form. Does NOT auto-generate; user reviews/edits, then clicks Generate. New PSet stores the *edited* filters. No back-link to source PSet.
  - **Delete**.

**Validation.** Re-export produces an equivalent PDF (modulo timestamp). Generate-similar pre-fills correctly.

---

## Step 9 — Tag tray Compulsory/Exclude (verification pass)

**Goal.** Confirm every edge case in §7.2 behaves correctly.

**What we'll be doing.** This is mostly verification of step-4 work, plus any fixes uncovered. Walk:
- The spec example: "Mathematical Induction & Invariants compulsory, Coloring/Diagram optional" — confirm matching set is correct.
- All five §7.2 edge cases.
- API rejection when `compulsory ∩ excluded ≠ ∅`.
- The cascade: turning Exclude on while a chip is optional flips it to compulsory+excluded; turning Compulsory off while Exclude is on also turns Exclude off.

**End state.** No tag-state combination produces an undefined or surprising result.

---

## Step 10 — Source tray, Type tray, Min Difficulty, Reuse, In-Syllabus

**Goal.** The remaining filter surface is honored end-to-end by selection.

**What we'll be doing.**
- Source/Type trays (component already exists from step 4) — verify dynamic dropdowns and that selection respects them.
- Min Difficulty spinbox — verify the SQL `>=` clause.
- Reuse Questions toggle — verify `times_used = 0` gate when off.
- In-Syllabus Only — verify the **two independent gates**: subject curricular boundary AND `questions.in_syllabus = 1`. Both must be true (§7.2). Cover the case where the active subject includes a topic but a row has `in_syllabus = 0` (it should not match).

**Validation.** Targeted queries against known subsets return expected counts under each toggle combination.

---

## Step 11 — Subjects page

**Goal.** Users can create, edit, activate, import, and export Subjects. Table starts empty.

**What we'll be doing.**
- `frontend/src/pages/Subjects.tsx` per §8.2:
  - **Left column:** subject list with active dot, buttons New / Duplicate / Delete / Import / Export.
  - **Right column:** editor with Name (validated unique), Description (multiline), topic picker, branch+subtopic exclusion tree.
- IPC: `list_subjects`, `load_subject`, `save_subject`, `delete_subject`, `activate_subject`, `get_active_subject`, `export_subject`, `import_subject`.
- Activation logic: `is_active = 1` for at most one row at a time. `activate_subject(None)` deactivates all.
- Subject payload JSON schema per §3.6 (`topics`, `excluded_branches`, `excluded_subtopics`, `description`, `schema_version: 1`).
- Import/export round-trips the payload + name as a JSON file.

**Validation.** Create a subject excluding one branch, activate it, navigate to Generate — the tree omits the excluded branch and counts reflect the curricular gate.

---

## Step 12 — Themes infrastructure

**Goal.** Theme switching works without reload. Default Light + Default Dark + one full flavor (Pastel — easiest).

**What we'll be doing.**
- `frontend/styles/base.css` (Tailwind input) + per-theme overlay CSS in `frontend/styles/themes/<id>/theme.css`.
- Tokens per §11.3: `--text`, `--background`, `--surface`, `--primary`, `--secondary`, `--accent`, `--border`, `--muted`, `--success`, `--warning`, `--error`, `--rem`, `--font-family`.
- `frontend/src/lib/theme.ts` — applies CSS vars on switch, swaps sprite paths in `<img src>`, swaps the active sound pack.
- IPC: `list_themes`, `set_theme`, `play_sound(event)` resolving to the active theme's `sounds/<event>.mp3` (fail-soft if missing).
- Pastel theme end-to-end: CSS overlay + sprite pack + sound pack + themed `.amplify-tooltip`.

**Validation.** Switch from Settings between Default Light, Default Dark, and Pastel. CSS vars, sprites, sounds, tooltip shape all update without reload. Default themes hit WCAG AA contrast.

---

## Step 13 — About / Tutorial / Settings

**Goal.** The static-ish pages exist. Settings exposes the Data card.

**What we'll be doing.**
- `/about` — static + dynamic credits sourced from the `sources` distinct list.
- `/tutorial` — static help.
- `/settings` per §8.7, four cards:
  - **Reset DB Data:** Reset Subject (zero `times_used` for active subject); Factory Reset (wipes psets/templates/quizzes/configs but **preserves** `questions`, `question_tags`, `classification_emb`, `similarity_emb`, `solution_outline`; preserves augmented rows; restarts the app).
  - **General:** Font size, Default # questions, Default save location, Active theme readout, Restart App, Global mute.
  - **PDF Output:** editors for Left Header / Right Header / Title Line / Instructions; image-upload buttons on the headers; per-field validation against the appropriate sanitizer (basic for headers, extended for title/instructions); Save / Cancel / Reset to Defaults.
  - **Data:** **Re-run Seed Ingest** (idempotent reload of §4.1); **Augment seed from CSV…** (file picker → §4.2 path: drop Stream/Subject/AnsCode, strip branch brackets, coerce In Syllabus, parse Tags, hash, dedupe, insert with NULL embeddings/outline; result dialog `{added, skipped, errors}`); diagnostic readouts: `EMBED_MODEL_VERSION`, with/without embeddings count, with/without outlines count.
- IPC: `run_seed_ingest`, `augment_seed_from_csv`, `factory_reset`, `get_config`, `set_config`.
- **No API-key field. No embedding/outline regeneration buttons.**

**Validation.** Augment-from-CSV with a small CSV containing a known new row + one duplicate (by `latex_hash`); result dialog shows `{added:1, skipped:1, errors:[]}`. Augmented row has NULL `classification_emb` / `similarity_emb` / `solution_outline`. Factory Reset preserves question content; psets/templates wiped.

---

## Step 14 — Stats v2

**Goal.** Full stats dashboard.

**What we'll be doing.**
- **Multiplicity histogram** (D3 custom) — bars at 1×, 2×, 3×, …, height = count of questions at each multiplicity.
- **Calendar heatmap** (D3 custom — explicitly **not** `react-calendar-heatmap`).
- **Activity line** — papers + questions over a date range.
- IPC: `get_question_multiplicity_dist`, `get_calendar_heatmap`, `get_activity_line`.
- All charts use the themed tooltip from step 7.

**Validation.** Charts populate against a seeded history; date-range scoping behaves; tooltips themed correctly across the three default themes shipped so far.

> **🛑 SIGN-OFF GATE 3 — MVP COMPLETE.** Full demo. Project owner signs off on MVP. Steps 15+ are post-MVP and may be re-prioritized at this gate.

---

## Step 15 — Similarity search

**Goal.** Find similar questions to a given one, using only the seed-loaded embeddings.

**What we'll be doing.**
- `app/core/similarity.py` — streaming cosine over BLOBs: read each `similarity_emb` from SQLite as a 12 288-byte buffer, decode as float32 little-endian, dot-product against the query vector. Skip NULL rows silently. Brute force is fine (<100k rows).
- IPC: `get_similar_questions(question_id, k=10)`.
- **No encoder, no API client, no worker.** The runtime never generates embeddings.

**Validation.** Pick a known question with rich tags; the top-k similar results are plausibly related. Augmented (NULL-embedding) rows never appear in results. Performance acceptable at seed size.

---

## Step 16 — Question Browser (read-only)

**Goal.** A power-user table for filtering, sorting, mass-tagging, and exploring questions. Question content stays immutable.

**What we'll be doing.**
- `frontend/src/pages/Browser.tsx` per §8.6: table with filters, sort, multi-select; mass actions:
  - **Add Tag**, **Remove Tag** (operate on `question_tags`).
  - **Set In-Syllabus** (toggles `questions.in_syllabus`).
  - **Reset Question Data** (zeroes `times_used`, `interactive_times_used`, `date_last_accessed`).
  - **Generate PSet from selection** (routes to `/generate` pre-filled with these specific question IDs as a one-off filter mode).
- Side panel showing the rendered question, solution, hints, `solution_outline` if present (read-only — no regenerate button), and a "similar questions" list backed by `get_similar_questions`.
- **No** New / Edit / Delete buttons. **No** Author mode.
- IPC: `search_questions`, `get_question`, `mass_action` (action ∈ `{add_tag, remove_tag, set_in_syllabus, reset_progress, generate_pset}`).

**Validation.** Mass-add a tag to 10 rows; rows in DB reflect it; tag dropdown elsewhere now lists it. Side panel renders LaTeX for question + solution + outline; similar-questions list populates.

---

## Step 17 — Remaining themes

**Goal.** All named themes shipped.

**What we'll be doing.** Port each remaining theme — Frutiger Aero, Pixel Art, Windows XP, Comic, ASCII, Android KitKat — as (CSS overlay) + (sprite pack) + (sound pack) + themed `.amplify-tooltip`. Keep §11.4's caveat in mind: era-evoking, not trademarked-chrome reproductions. Each flavor theme exposes an Accessibility-mode toggle that forces high-contrast text on top of the theme's background art.

**Validation.** Cycle through every theme; nothing breaks; flavor themes get distinct tooltips; Accessibility mode produces readable text on every flavor background.

---

## Step 18 — Phase 2: Interactive practice

**Goal.** Quiz mode works. PBS parallel-pool runner works.

**What we'll be doing.**
- `app/interactive/runner.py` — non-PBS single-widget runner; honors Allow-skips, Wait-for-correct, Instant-scoring, Show-solutions flags.
- `app/interactive/scoring.py` — point gradient (random / constant / custom); skip penalty; `[PBS]` geometric-×0.5 wrong-attempt decay (parametrized; never below 1; never negative).
- `app/interactive/pbs.py` — parallel widget pool per §10.1: N visible (configurable at template creation), pool of size > N, dequeue-on-correct replacement, total-only timer, **numerical-only** type enforcement at template creation and quiz start, no hints, implicit skips (user moves between widgets freely; only correct answer consumes a widget). Responsive tiled grid layout (2 cols narrow → 4 wide). Each widget header shows live "available score." Total score + timer pinned at top.
- Quiz settings panel per §10 with the `[PBS]` template lock (resets toggles when chosen; saved tweaked copies prefix `[PBS]`).
- `/quiz` runner page (single-widget for non-PBS, tiled grid for PBS).
- `/quiz/review/:id` — per-question score, hints, solutions, user's answers vs correct.
- IPC: `start_quiz`, `quiz_take_widget`, `quiz_submit_answer`, `quiz_request_hint`, `quiz_finish`, `list_quiz_attempts`.
- History page additionally lists quiz attempts alongside PSets.

**Validation.** End-to-end PBS run: 3 widgets, 10-question pool, correct answer replaces widget; two wrong attempts on a single widget halve the available score twice; timer expiry ends the run; review page renders correctly. Non-PBS run: Wait-for-correct mode blocks advancement; Allow-skips off disables next-question nav.

---

## Step 19 — Phase 2: Smart difficulty

**Goal.** Per-topic difficulty score from local data only. No external calls.

**What we'll be doing.**
- `app/core/difficulty.py` per §13.1, three sub-scores:
  - **Length:** count of top-level items in `solution_outline`. NULL outline → 0.
  - **Novelty:** `1 − max_cosine(this.classification_emb, others_in_same_subtopic.classification_emb)`. NULL embedding → 0.
  - **Depth:** lookup in `configs.TOPIC_DEPTH_MAP`.
- Per-topic learned combiner (linear or small MLP head) trained from in-app pairwise comparisons.
- Pairwise trainer UI: presents two questions, user picks "harder" + magnitude; gradient descent updates per-topic weights.
- Settings → Data → **Recompute Smart Difficulty** button (writes to `questions.difficulty_rating`).
- Settings toggle to enable Smart Difficulty.
- IPC: `recompute_difficulty`.

**Validation.** Recompute updates `difficulty_rating` for rows that have the inputs; rows without outlines/embeddings still get a depth-only score. Pairwise trainer demonstrably shifts weights. **Confirm zero outbound network traffic** during recompute (OS-level network sandbox or Wireshark check).

---

## Closing notes

- **The three sign-off gates (after step 4, 7, 14) are mandatory pauses.** Don't silently advance past them.
- **`factory_reset` does not delete `questions`, `question_tags`, `classification_emb`, `similarity_emb`, or `solution_outline`.** Those count as seed data. Augmented rows are preserved too. (§5.10.)
- **Logging is not optional.** Every significant action — generate, export-tex, save-template, delete-template, factory-reset, theme-change, subject-activate, subject-import, seed-ingest, seed-augment, mass-action — gets a log line per §14.
- **i18n scaffolding ships in MVP** even though only English is included: every UI string lives in `frontend/src/i18n/en.json` keyed, so adding a locale later doesn't require touching every component.
- **No matplotlib. Anywhere. Ever.** Hard rule from §2.1.
