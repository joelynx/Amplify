# Solution pipeline: runbook (API version, prompt_version v5)

Regenerates intuition-first solutions for the 36 math sources in `config.json`
through the Claude **Message Batches API** on API credits. One fixed model and
effort (`config.solver`), no triage, no reviewer, no subagents. The owner's
spec is `Solution_Pipeline.md`; the subagent-era implementation it describes
is kept under `legacy/` for reference and is not used.

What one question costs and produces: a single batched request whose reply is
the solution, rigor notes, takeaways, answer, and hint in one marked-up LaTeX
text. Code validates it (markers, LaTeX rules, XeLaTeX compile, KaTeX web
check), stores it in `questions.generated_solution` with the attribution line,
and fills empty Answer / Hint cells.

## Decisions baked in (owner, 2026-10-19)

- **Submissions are closed (owner, 2026-10-21).** `config.submissions_closed`
  is true: `run.py submit` and `run.py loop` refuse to send anything (a
  `--dry-run` still works). The 585 retries and 514 unsolved questions stay as
  they are; the solved set is final. Flip the flag only on the owner's say-so.
- API credits, not the subscription. The key lives in `pipeline/.anthropic_key`
  (git-ignored) or `ANTHROPIC_API_KEY`.
- Fixed model and effort for every question: `config.solver` (default
  `claude-opus-5-5` at `high`, `max_tokens` 32000).
- No review and no triage. Correctness checks are mechanical only; the one
  content check is `check_stored_numeric_answer`: when the stored Answer is a
  plain number (AIME and a few others) and the solver's NUMERICAL answer
  differs, the question is re-solved once, then goes to human review.
- Sources are processed in the order of `config.sources` (the list is the
  priority order).
- The old solution (`questions.solution`) is never sent to the model and never
  read when building a prompt. `run.py` refuses a template with an
  `{{OLD_SOLUTION}}` / `{{STORED_ANSWER}}` placeholder.
- Every question that involves an image is skipped (`skipped_image`): any
  `\includegraphics`, or prose that points at a figure. 301 of 12,118.
- Cost levers: Batch API (half price on every token), the static instructions
  as a cached system prompt (1-hour TTL), one request per question (rigor
  notes and hint come from the same reply), retries only for the questions
  that fail the checks (one retry, with the validator's errors fed back).

## Commands (from the repo root)

```
python pipeline/scripts/run.py check                  # free: is the key (and workspace) accepted?
python pipeline/scripts/run.py status                 # progress by source, in-flight batches, spend
python pipeline/scripts/run.py queue  [--n 20]        # what goes next, in priority order
python pipeline/scripts/run.py submit [--n N] [--ids 1,2,3] [--dry-run]
python pipeline/scripts/run.py collect [--wait]       # fetch ended batches: validate, store, queue retries
python pipeline/scripts/run.py loop [--n N] [--max-batches K] [--budget-usd X]
python pipeline/scripts/run.py cost                   # spend so far, USD per passed question, projection
python pipeline/scripts/run.py cancel                 # cancel in-flight batches (results so far are kept)
python pipeline/scripts/run.py reset --yes            # archive pipeline.db + outputs/ to pipeline/archive/
```

The key is read from `ANTHROPIC_API_KEY` if set, else from the git-ignored
file `pipeline/.anthropic_key` (the key on one line). Alternatives in
PowerShell: `$env:ANTHROPIC_API_KEY = 'sk-ant-...'` (this window) or
`setx ANTHROPIC_API_KEY sk-ant-...` (persistent, new window).

A **multi-workspace personal key** (`sk-ant-usr-...` created without picking
one workspace) is rejected until every request names a workspace. Put the
`wrkspc_...` id (Claude Console, Settings, Workspaces, ID column) on its own
line in `pipeline/.anthropic_key`, or set `ANTHROPIC_WORKSPACE_ID`; the runner
then sends the `anthropic-workspace-id` header on every call. A key created
for a single workspace needs nothing. `run.py check` confirms either case
without spending tokens.

### First run

1. `run.py check` until it prints `"ok": true` with a workspace id.
2. `run.py reset --yes` to archive the subagent-era pilot (mixed models).
3. `run.py submit --n 20` for a pilot batch, then `run.py collect --wait`.
   Read `run.py cost` (real USD per question) and open two `preview.pdf`
   files under `outputs/<id>/` before scaling up.
3. `run.py loop --budget-usd <cap>` to process everything in priority order.
   It submits one batch of `api_batch_size` questions at a time (default 500),
   polls every `poll_seconds`, collects, assembles, writes to the app
   database, and submits the next batch. Ctrl+C is safe: in-flight batches
   stay recorded and `collect` resumes them.

### What collect does with each reply

| Outcome | Status | Next |
|---|---|---|
| passes every check | `passed`, assembled, written to the app db | done |
| fails structure / LaTeX / compile checks | `retry` (attempt 1) | resubmitted with the errors and the previous reply |
| fails again (attempt 2) | `needs_human_review` | nothing stored |
| NUMERICAL answer differs from a numeric stored Answer | `retry` (blind re-solve), then `needs_human_review` | nothing stored |
| cut off at `max_tokens` | `retry` (blind) | |
| model refusal | `needs_human_review` | |
| API error / expired / canceled | back to `pending` (up to `max_api_failures`) | resubmitted |
| hint fails its checks (rules, length, answer leak) | solution still `passed`; hint dropped | Hint cell stays empty |

### Old stored solutions (questions.solution): check and mechanical repair

These never touch the pipeline statuses or `generated_solution`.

```
python pipeline/scripts/check_old_solutions.py --workers 4      # XeLaTeX + KaTeX check of every old solution without a generated one -> reports/old_solutions_check.csv (resumable)
python pipeline/scripts/report_old_solutions.py                 # hard breaks -> reports/old_solutions_breaks.csv, summary -> reports/old_solutions_report.md
python pipeline/scripts/fix_old_solutions.py run --workers 4    # mechanical repairs of the solution-fault rows, each verified by compiling -> reports/old_solutions_fixes.json/.csv
python pipeline/scripts/fix_old_solutions.py apply              # write the verified repairs to questions.solution (originals in pipeline.db solution_fixes)
python pipeline/scripts/fix_old_solutions.py revert             # put the originals back
powershell -ExecutionPolicy Bypass -File pipeline/scripts/confirm_chain.ps1 -SkipApply   # re-check the repaired rows with the independent checker, regenerate the report
```

`fix_old_solutions.py` only does text transformations (lost `\\`, JSON-doubled
backslashes, `_`/`&`/`%` outside math, unclosed environments, blank lines in
`align`, `\mathrm` in text, commands from packages the app does not load, ...),
then log-guided single fixes at the error position; a repair is kept only when
XeLaTeX compiles it with the app template. `run --redo --ids ...` recomputes
chosen rows; `--fresh` discards every previous result. Every XeLaTeX run should
be started at below-normal priority (see `confirm_chain.ps1`).

### Web view (KaTeX) vs PDF

Web-only problems (`\vspace`, figure/center/tabular scaffolding, `\paragraph`,
`\\` in prose, stray braces, ...) are NOT fixed in the database. The app's
renderer strips or converts them at render time
(`frontend/src/components/browser/latexWebSanitize.ts`, called from
`LatexContent.tsx`), so the stored LaTeX and the PDF compile stay untouched.
To measure what the web view still gets wrong, over every stored question
text and solution, without XeLaTeX:

```
python pipeline/scripts/check_web_all.py [--parts solution,question,generated_solution]   # -> reports/web_check.csv + summary
```

It bundles the real renderer (`check_web.mjs` rebuilds the bundle whenever
`LatexContent.tsx` or `latexWebSanitize.ts` changes), so unit tests for the
renderer live in `frontend/src/components/browser/__tests__/` and run with
`npm test` in `frontend/`.

## Files

- `config.json`: everything pinned (model, effort, batch size, prices for the cost view, source order).
- `prompts/solver.md` (system prompt template), `prompts/format_rules.md`, `prompts/hint_examples.md`.
- `scripts/run.py` runner; `scripts/validate.py` checks; `scripts/assemble.py` storage;
  `scripts/apply_fields.py` app-db writes; `scripts/check_pdf.py` + `scripts/check_web.mjs` compile checks;
  `scripts/common.py` shared code; `scripts/make_template.py` regenerates `templates/app_template.tex`.
- `pipeline.db`: `status`, `finals`, `provenance`, `events`, `api_batches`, `usage` (tokens per reply).
- `outputs/<id>/`: `solver_<n>.tex` (raw reply), `response_<n>.json`, `validate_<n>.json`,
  `feedback_<n>.json`, `final.tex`, `final_app.json`, `preview.pdf`.
- `run_log.md`: one line per collected batch plus decisions.

## Rules that keep the run consistent

- Never edit `prompts/*` or `config.solver` mid-run. Bump `prompt_version`,
  note it in `run_log.md`, and decide whether earlier questions are rerun.
- Prices in `config.prices_usd_per_mtok` are for the cost view only; verify
  them against the pricing page before trusting a projection.
- The solver pipeline never modifies `questions.solution`; the only writer is
  `fix_old_solutions.py apply` (owner-requested mechanical repairs, originals
  kept in `pipeline.db` table `solution_fixes`, reversible with `revert`).
  `generated_solution` is owned by the pipeline and may be replaced by a rerun.
  Answer / Hint are filled only when empty.
