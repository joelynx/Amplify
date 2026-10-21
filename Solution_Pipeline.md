# Math Solution Generation Pipeline

## Purpose

Generate high-quality, intuition-first solutions for ~1,000 undergraduate math problems for self-study. Each final solution has three parts:

1. **Main Solution:** intuitive, step-by-step, focused on *why* each step is taken.
2. **Rigor Notes:** a short section covering anything the intuitive solution glossed over that matters for correctness (omitted if nothing important was skipped).
3. **Takeaways:** reusable methods, patterns, recognition cues, and an explanation of any non-obvious leap.

The pipeline uses a solver subagent and an independent reviewer subagent, and cross-checks every new solution against an **existing solution** already stored in the database for each question.

It also fills the database's **Answer** and **Hint** fields where they are currently empty: the answer is extracted from the verified solution, and the hint is written by a separate step after review so it doesn't affect the solver or reviewer.

This pipeline runs on a Claude subscription, not the API. You (the agent reading this) are the **orchestrator**: you spawn subagents for each stage and run the scripts. You never solve, review, write prompts, or make pass/fail decisions yourself.

---

## Core principle: prevent drift

This run spans many sessions. The main risk to consistency is the orchestrator *interpreting* things it should be *copying*: paraphrasing prompts, forgetting rules after its context is compressed, or re-reading this spec differently in a new session. So:

- **Prompts are files.** They are filled in by a script and passed to subagents verbatim. You never retype, summarize, or edit a prompt.
- **Decisions are code.** Batch selection, validation, pass/fail, escalation, assembly, and status updates are done by scripts. Your job is to spawn subagents and run scripts.
- **Sessions are short.** Each session reads this spec and the progress record fresh, runs a small number of batches, saves, and ends.
- **Settings are pinned and recorded.** Every output is stamped with the prompt version, model, and effort that produced it.
- **Output is validated and monitored.** Every output is compile-checked automatically, and batch-level metrics plus canary questions catch gradual quality changes.

---

## Inputs: the database

Each question in the database already has:

- the **question** text
- an **existing solution**, generated earlier with a "rigorous, step-by-step, University Mathematics Professor" prompt (referred to below as the *old solution*)
- **Answer** and **Hint** fields, which are sometimes empty

**Before building anything:** inspect the database schema, identify the fields holding the question text, the old solution, the Answer, the Hint, and a unique question ID, and confirm the mapping with the user before writing any new data. Do not overwrite or modify existing content; write all new outputs to new fields, a new table, or the output folder below.

- Treat the old solutions as **useful but unverified**. They were produced by a model and may contain errors.
- **Empty Answer and Hint fields are filled** by this pipeline (see "Answer and Hint fields"). **Filled ones are never overwritten.** A stored Answer is used as an additional check on the new solution; stored Hints are used as style examples.
- Some questions **reference images** (figures, graphs, diagrams). Every model that reads a question must also see its images. See "Images".

### Output target: LaTeX, compiled to PDF first, webview second

All content in the database is **plain LaTeX with no markdown**. The user's app:

1. **Primarily** compiles the LaTeX into **PDF files**. This is the main output and must never break.
2. **Secondarily** converts the same LaTeX into a **webview** display.

So every piece of generated content (solution, rigor notes, takeaways, answer, hint) must:

- be LaTeX only, with **no markdown anywhere**: no `#` headings, no `**bold**`, no `-` or `*` bullet lists, no backticks
- **compile without errors** in the app's PDF pipeline
- **convert without errors** in the app's webview pipeline
- use only constructs that **both** pipelines support (see "Output format discovery")

---

## Setup (first session only)

### Output format discovery

Before the pilot, work out exactly what the app accepts, and write it down as `pipeline/format_spec.md`. Do not guess.

1. **Gather evidence:**
   - **Existing content.** Look at how old solutions, question text, Answers, and Hints are written in the database. They already compile in the app, so they show the working conventions: math delimiters, how structure is expressed (`\textbf`, `itemize`, `\paragraph`, `\section*`, or none), line breaks, how images are included, and which macros appear.
   - **The PDF pipeline.** If the app's source is available, find the LaTeX template the content is inserted into: document class, preamble, loaded packages, custom macros defined there, the TeX engine (pdfLaTeX, XeLaTeX, LuaLaTeX), and exactly where each database field is placed in the document.
   - **The webview pipeline.** Find how LaTeX becomes the webview: KaTeX or MathJax rendering math only, a LaTeX-to-HTML converter (e.g., pandoc, LaTeX.js), or something custom, and its configuration (delimiters, macros, supported environments). This pipeline usually supports much less than real LaTeX, and it decides what is safe.
   - **Storage.** Note how content is stored (plain text column, JSON field, etc.) and therefore what needs escaping when written.
2. **Ask the user** about anything the evidence doesn't settle, such as whether the three sections should be one field or separate fields, and how section titles should appear.
3. **Write `format_spec.md`**, covering:
   - the app's PDF template (or a path to it), engine, and packages
   - the webview converter and its limits
   - **the allowed subset**: LaTeX that works in *both* pipelines. List the allowed math delimiters, text structure commands, environments, and macros, and list known-unsafe constructs (for example, packages not in the preamble, `tikz` if the webview can't show it, `align` if only `aligned` works in the webview, `\newcommand` inside content)
   - escaping rules for text mode: `%`, `&`, `#`, `_`, `$`, `{`, `}`, `~`, `^`, `\` must be escaped outside math (an unescaped `%` silently comments out the rest of the line in the PDF)
   - how the section titles (Solution, Rigor Notes, Takeaways) are expressed, or that they are separate fields with no titles in the content
   - how images are included (`\includegraphics` path convention, or the app's own mechanism)
   - **Answer field format**, from existing filled answers: math delimiters or not, level of simplification, units, how multiple answers or cases are separated, and whether the app checks answers automatically (in which case exact format matters)
   - **Hint field format**, from existing filled hints: typical length, tone, how math is written
   - one short, complete example of a correctly formatted solution body
4. **Get the user's confirmation** of `format_spec.md` before continuing.

Split the work between the models and the scripts:

- **Models** follow the LaTeX-writing rules: allowed subset, escaping, no markdown. These go in the prompts via `{{FORMAT_RULES}}`, a condensed extract of `format_spec.md` saved as `prompts/format_rules.md`. Include in it a short list of the preamble macros models may use.
- **Scripts** handle everything mechanical: section titles, joining the parts, storage escaping, field layout (`assemble.py`). Models write only content bodies, never a preamble, `\documentclass`, `\begin{document}`, or `\usepackage`.

### Why models never write LaTeX inside JSON

LaTeX inside JSON strings breaks silently: `\frac` becomes a form-feed character followed by `rac`, `\beta` becomes a backspace followed by `eta`, `\nabla` becomes a newline. So in this pipeline:

- Anything containing LaTeX that will be displayed (solution, takeaways, rigor notes, answer, hint) is written by models to **`.tex` files**, using comment marker lines to separate parts.
- JSON is used only for verdict fields (booleans and short plain-language descriptions).

Marker lines are LaTeX comments (`%%% ...`), so even if one slipped through assembly, it would not change the compiled output.

### Images

Write `scripts/find_images.py` to resolve each question's images before it is processed.

1. **Discover how images are stored.** Inspect the schema and sample questions: image columns or tables, file paths, URLs, `\includegraphics` commands in the question LaTeX, or textual references ("see Figure 2", "the graph below", "shown in the diagram").
2. **For each question,** collect every referenced image into `outputs/<question_id>/images/` (copy local files, download URLs if the environment allows), and record the mapping in `outputs/<question_id>/images.json`.
3. **Flag missing images.** If the question appears to reference a figure (keywords like "figure", "diagram", "graph", "shown", "below", "above", "picture", or an `\includegraphics`) but no image can be found or opened, mark the question `missing_image` and skip it. Never solve a question blind when it depends on an image.
4. **Pass images to every model that reads the question.** `{{IMAGES}}` is filled with the list of local image paths, and each prompt tells the subagent to open and view every image before starting. If the environment attaches images to a subagent in a different way, use that instead, but every router, solver, reviewer, and hint call for that question must see the same images.
5. **Make images available to the compile checks**, so a solution that references the figure compiles exactly as it would in the app.

If a question has no images, `{{IMAGES}}` is filled with "None".

### Answer and Hint fields

**Answer.** Extracted from the solver's output, never generated separately.

- The solver ends its output with an **answer section**, written *after* the solution and takeaways so it can't influence the reasoning. It classifies the answer type (NUMERICAL, EXPRESSION, or NONE for proofs, explanations, sketches, etc.) and restates the final answer in LaTeX.
- The reviewer checks it against the correct answer, and also compares against the **stored Answer** if the field is filled. The solver never sees the stored Answer, so that comparison is independent.
- The Answer field is filled only when: it is currently empty, the answer type is not NONE, and the question's status is `passed` or `passed_after_escalation`.
- `assemble.py` converts the answer to the exact Answer field format in `format_spec.md`. Formatting is done by code, not by a model.

**Hint.** Written by a separate, lightweight hint subagent *after* review, only for questions that passed and have an empty Hint field. It works from the verified solution, so it never changes the solver's or reviewer's work.

- The hint should point toward the starting idea or the right technique without doing any of the work or revealing the answer.
- `prompts/hint_examples.md` holds 5–8 existing hints from the database (as stored, in LaTeX), chosen during setup to cover a range of topics, so new hints match the existing length, tone, and LaTeX style.
- The hint subagent checks its own hint against a short checklist, and `validate.py` runs a mechanical leak check (see Validation).

**Provenance.** Every generated Answer or Hint is recorded in a separate provenance field or table (question ID, field, `prompt_version`, date), so generated content can be reviewed or removed later without touching original content. Agree the storage location with the user during setup.

### Folder layout

Create this structure. Adjust paths if the user prefers, but keep the separation between prompts, scripts, config, and outputs.

```
pipeline/
├── config.json              # pinned settings and prompt version (see below)
├── format_spec.md           # the app's accepted LaTeX subset, confirmed by the user
├── templates/
│   └── app_template.tex     # copy of the app's PDF template, with a slot for content
├── prompts/
│   ├── router.md            # Stage 1 prompt (only if using Option B)
│   ├── solver.md            # Stage 2 prompt
│   ├── reviewer.md          # Stage 3 prompt
│   ├── hint.md              # Stage 3b prompt
│   ├── hint_examples.md     # existing hints from the database, as style examples
│   └── format_rules.md      # condensed LaTeX-writing rules from format_spec.md
├── scripts/
│   ├── find_images.py       # resolves and collects each question's images
│   ├── check_pdf.py         # compiles LaTeX in the app's template to catch errors
│   ├── check_web.*          # runs the app's webview conversion to catch errors
│   ├── next_batch.py        # selects the next questions to process
│   ├── triage.py            # assigns difficulty level (Option A heuristic)
│   ├── render_prompt.py     # fills a prompt template for one question
│   ├── validate.py          # checks solver, reviewer, and hint output
│   ├── decide.py            # applies pass/fail and escalation logic, updates status
│   ├── assemble.py          # builds and stores the final solution
│   └── metrics.py           # per-batch metrics and canary comparison
├── outputs/
│   └── <question_id>/
│       ├── images/          # this question's images, if any
│       ├── images.json      # image references → local paths
│       ├── solver_1.tex
│       ├── review_1.json
│       ├── review_1_rigor.tex
│       ├── solver_2.tex     # only if escalated
│       ├── review_2.json    # only if escalated
│       ├── review_2_rigor.tex
│       ├── hint.tex         # only if the Hint field was empty and the question passed
│       ├── final.tex        # assembled solution body, as it will be stored
│       ├── final_app.*      # the same content in the app's storage layout
│       └── preview.pdf      # compiled with the app's template, for spot-checks
├── canaries/
│   └── <question_id>/approved_final.tex   # approved pilot outputs
├── progress.json            # or a status table in the database
└── run_log.md               # one line per batch: date, batch, metrics, notes
```

### Prompt files

Copy the prompts in this document **exactly** into the files under `prompts/`. Placeholders use double braces in caps, such as `{{QUESTION}}`. `render_prompt.py` must fill them by plain string replacement, not by Python `str.format` or similar, because the prompts contain literal braces (JSON and LaTeX).

Placeholders:

| Placeholder | Filled with |
|---|---|
| `{{QUESTION_ID}}` | the question's unique ID |
| `{{QUESTION}}` | question LaTeX from the database |
| `{{OLD_SOLUTION}}` | old solution from the database (router and reviewer only) |
| `{{NEW_SOLUTION}}` | contents of the solver output being reviewed (reviewer only) |
| `{{OUTPUT_PATH}}` | the main file the subagent must write to |
| `{{RIGOR_PATH}}` | the `.tex` file for rigor notes (reviewer only) |
| `{{IMAGES}}` | list of local image paths for this question, or "None" |
| `{{FORMAT_RULES}}` | contents of `prompts/format_rules.md` (solver, reviewer, hint) |
| `{{STORED_ANSWER}}` | the database's Answer field, or "None" if empty (reviewer only) |
| `{{ACCEPTED_SOLUTION}}` | the solver output that passed review (hint only) |
| `{{HINT_EXAMPLES}}` | contents of `prompts/hint_examples.md` (hint only) |

`render_prompt.py` must refuse to render the solver prompt with an old solution or a stored answer, as a code-level guarantee that the solver never sees either.

### Subagent definitions

If the environment supports reusable subagent definitions (for example, Claude Code subagent files that fix a prompt, model, and reasoning effort), define one per role and difficulty level from `config.json`, so the settings are identical on every call by construction. Otherwise, pass the rendered prompt file's contents unchanged and set model and effort from `config.json` on every spawn.

### config.json

```json
{
  "prompt_version": "v1",
  "triage_method": "heuristic",
  "triage_thresholds": { "routine_max_chars": null, "moderate_max_chars": null },
  "solver": {
    "ROUTINE":  { "model": "<mid-tier, e.g. Sonnet>",    "effort": "low" },
    "MODERATE": { "model": "<mid-tier or strongest>",    "effort": "medium" },
    "INSIGHT":  { "model": "<strongest, e.g. Opus>",     "effort": "high" },
    "ESCALATE": { "model": "<strongest>",                "effort": "highest available" }
  },
  "router":   { "model": "<cheapest available>", "effort": "low" },
  "reviewer": { "model": "<strongest>",          "effort": "high" },
  "hint":     { "model": "<mid-tier, e.g. Sonnet>", "effort": "low" },
  "tex_engine": "<pdflatex | xelatex | lualatex, matching the app>",
  "batch_size": 15,
  "parallel_subagents": 4,
  "canary_ids": [],
  "canary_every_n_questions": 100,
  "solution_length_bounds_chars": { "min": null, "max": null }
}
```

Confirm the available models and effort controls with the user, and fill in thresholds, length bounds, and canary IDs after the pilot.

**Versioning rule:** never edit a prompt file, `format_rules.md`, or `config.json` in place mid-run. If the user approves a change, increment `prompt_version`, record the change and the question ID where it took effect in `run_log.md`, and ask the user whether earlier questions should be rerun.

---

## Orchestration rules

- **Keep your own context small.** Subagents write their outputs to files and return only a one-line status. Never read full solutions into your own context except for spot-checks.
- **One fresh subagent per stage per question.** This is what keeps the reviewer independent of the solver.
- **Never write or alter prompt text.** Run `render_prompt.py` and pass its output unchanged.
- **Never make pass/fail or escalation decisions yourself.** Run `decide.py`.
- **Update progress after every stage**, via the scripts, so any session can resume exactly where the last one stopped.
- **Run a few subagents in parallel** (`parallel_subagents` in config), never hundreds at once.
- **Keep sessions short.** Process a small number of batches per session (2–3 is a good default), then save and end. Start each new session by reading this spec, `config.json`, `progress.json`, and the last few lines of `run_log.md`.
- **If you hit a usage limit,** let the scripts save progress, then stop and tell the user where the run stands.

### Per-batch loop

1. `next_batch.py` → returns the next `batch_size` question IDs that have no final status.
2. `find_images.py` → collects images; questions with a referenced but missing image are marked `missing_image` and dropped from the batch.
3. `triage.py` (or router subagents) → assigns a difficulty level to each.
4. For each question: `render_prompt.py solver` → spawn solver subagent with the config settings for its level.
5. `validate.py` on each solver output (structure, no markdown, PDF compile, webview conversion). Invalid → rerun the solver once; still invalid → mark `needs_human_review`.
6. For each valid solution: `render_prompt.py reviewer` → spawn reviewer subagent.
7. `validate.py` on each review (JSON fields, and compile/conversion of the rigor notes). Invalid → rerun the review once; still invalid → `needs_human_review`.
8. `decide.py` → marks each question pass, escalate, or human review.
9. Escalations: repeat steps 4–8 once with the `ESCALATE` solver settings (writing `solver_2.tex` / `review_2.*`).
10. For passed questions with an empty Hint field: `render_prompt.py hint` → spawn hint subagent → `validate.py` on the hint. Invalid → rerun once; still invalid → leave the Hint field empty (the solution itself is unaffected).
11. `assemble.py` on all passed questions → `final.tex`, `final_app.*`, `preview.pdf`; fill empty Answer and Hint fields; record provenance; final compile and conversion checks.
12. `metrics.py` → append a line to `run_log.md`; run canaries if due; spot-check (see Monitoring).

---

## Pipeline overview

```
[1. Triage] → [2. Solver] → [3. Reviewer] → pass → [3b. Hint, if field empty] → [5. Assemble & store]
                                  │
                                  └── fail → [4. Escalate: re-solve at max effort → review again]
```

| Stage | Sees the question | Sees old solution / stored answer | Sees the new solution | Output |
|---|---|---|---|---|
| 1. Triage | Yes | Old solution only | No | Difficulty level |
| 2. Solver | Yes | **No** | n/a | `.tex`: Solution + Takeaways + Answer |
| 3. Reviewer | Yes | Yes | Yes | JSON verdict + `.tex` Rigor Notes |
| 3b. Hint | Yes | No | Verified solution | `.tex` hint |
| 4. Escalate | Yes | **No** | n/a | Replacement solution |

---

## Stage 1: Triage

Goal: decide how much reasoning the solver needs. On a subscription, this is also the main lever for stretching usage: routine problems don't need the strongest model at maximum effort.

Costs are lopsided: over-thinking an easy problem wastes a little usage; under-thinking a hard one produces a wrong solution. **When unsure, choose the higher level.** Because Stage 4 re-solves any failed problem at maximum settings, triage mistakes are recoverable.

- **Option A, heuristic (default):** `triage.py` uses the length of the old solution as a difficulty proxy, with thresholds from `config.json` tuned on the pilot. Costs no usage.
- **Option B, router subagent:** a subagent on the cheapest model reads the question and old solution and rates difficulty using `prompts/router.md`. Use only if the pilot shows Option A misroutes often.

### prompts/router.md

```
You are triaging undergraduate math problems to decide how much reasoning effort a solver should spend.

Below are a problem and an existing worked solution to it, both written in LaTeX. Use the solution to judge how hard the problem actually is, not just how it looks.

PROBLEM:
{{QUESTION}}

IMAGES REFERENCED BY THE PROBLEM (open and view each one before classifying):
{{IMAGES}}

EXISTING SOLUTION:
{{OLD_SOLUTION}}

Classify the problem as exactly one of:
- ROUTINE: a standard technique applied directly, few steps, no tricks.
- MODERATE: several steps or a combination of techniques, but each step follows naturally.
- INSIGHT: needs a non-obvious idea (a clever substitution, construction, case split, or reframing), or is long and error-prone.

If you are unsure between two levels, choose the harder one.

Write only one word, ROUTINE, MODERATE, or INSIGHT, to {{OUTPUT_PATH}}, then reply with only: "{{QUESTION_ID}}: triage done".
```

---

## Stage 2: Solver

### prompts/solver.md

```
Role: A university mathematics tutor known for building intuition, explaining things the way you would at a whiteboard to a student working on their own.

Task: Write a step-by-step solution to the problem below that prioritizes understanding WHY each step works and why it's the natural thing to try, over formal precision.

QUESTION (in LaTeX):
{{QUESTION}}

IMAGES REFERENCED BY THE QUESTION:
{{IMAGES}}
If any images are listed, open and view every one before you start; the question depends on them. If an image is listed but you cannot open it, do not attempt the problem: write "%%% IMAGE UNREADABLE" to {{OUTPUT_PATH}} and reply with only "{{QUESTION_ID}}: image unreadable".

INSTRUCTIONS:

1. MAIN SOLUTION (intuition first):
- Audience: an undergraduate studying on their own, with no one to ask follow-up questions.
- Before diving in, briefly say what the problem is really asking and what the plan of attack is.
- For each step, explain the motivation: why this move, why now, what made it the obvious choice (e.g., "The product of a polynomial and an exponential is a signal to try integration by parts, because differentiating the polynomial will eventually make it disappear").
- Use plain language, geometric descriptions, analogies, or sanity checks (special cases, units, limiting behavior) wherever they make an idea click.
- Keep the algebra correct, but don't stop to justify technicalities (convergence, domain conditions, edge cases) in the main flow.
- End the main solution with the final answer on its own line, beginning with the words "Final answer:".

2. TAKEAWAYS:
- Whenever applicable, point out any general method, pattern, or recognition cue the student can reuse on similar problems.
- If the solution required a non-obvious leap, restate it and explain how someone could have thought of it.

3. ANSWER (write this last, only after the solution and takeaways are complete):
- Answer type: NUMERICAL if the final answer is a number (with or without units), EXPRESSION if it is a formula, function, set, interval, or similar mathematical object, NONE if the question has no single final answer (a proof, an explanation, a sketch, a yes/no with justification as the main content, etc.).
- Answer: the final answer only, in LaTeX, with no explanation, matching your "Final answer:" line. Write NONE if the answer type is NONE.

OUTPUT FORMAT:
Write everything in LaTeX. The output is compiled into a PDF and also shown in a web view, so:
- Do NOT use any markdown: no # headings, no **bold**, no - or * bullet lists, no backticks.
- Write only content. Do NOT write \documentclass, \usepackage, \begin{document}, or section titles; those are added separately.
- Do NOT write a Rigor Notes section; it is added separately.

Use exactly this structure. The lines starting with %%% are markers; copy them exactly:

%%% BEGIN SOLUTION
<solution body in LaTeX>
%%% END SOLUTION
%%% BEGIN TAKEAWAYS
<takeaways body in LaTeX>
%%% END TAKEAWAYS
%%% ANSWER TYPE: <NUMERICAL | EXPRESSION | NONE>
%%% BEGIN ANSWER
<final answer only, in LaTeX, or NONE>
%%% END ANSWER

LATEX RULES (follow exactly; the PDF compiler and the web view both depend on them):
{{FORMAT_RULES}}

Save the output to {{OUTPUT_PATH}}, then reply with only: "{{QUESTION_ID}}: solver done".
```

---

## Stage 3: Reviewer

Always the strongest model at high effort; a weak reviewer misses subtle errors. If the reviewer subagent has a code execution tool, it should verify computational results with code (e.g., SymPy).

### prompts/reviewer.md

```
You are reviewing a solution to an undergraduate math problem that will be used for self-study. Students will trust it, so correctness matters more than anything else. All material below is written in LaTeX.

You are given:
- PROBLEM
- NEW SOLUTION: an intuition-focused solution to review. Lines starting with %%% are structural markers, not content.
- REFERENCE SOLUTION: an older, more formal solution written independently. It may itself contain errors; do not assume it is correct.
- STORED ANSWER: the answer currently stored for this problem, if any. It may also be wrong.

PROBLEM:
{{QUESTION}}

IMAGES REFERENCED BY THE PROBLEM:
{{IMAGES}}
If any images are listed, open and view every one before reviewing; check that the solution reads them correctly (values, labels, shapes). If an image is listed but you cannot open it, do not review: write "IMAGE UNREADABLE" to {{OUTPUT_PATH}} and reply with only "{{QUESTION_ID}}: image unreadable".

NEW SOLUTION:
{{NEW_SOLUTION}}

REFERENCE SOLUTION:
{{OLD_SOLUTION}}

STORED ANSWER:
{{STORED_ANSWER}}

Do the following:

1. ANSWER CHECK: Compare the final answers of the two solutions. Decide whether they are mathematically equivalent (different but equivalent forms count as agreeing). If a STORED ANSWER is given, also decide whether it is equivalent to the NEW SOLUTION's answer. Check that the NEW SOLUTION's answer section has the correct answer type and states the same answer as its "Final answer:" line.

2. ERROR CHECK: Go through the NEW SOLUTION step by step. Identify any mathematical error, invalid step, or wrong final answer. Where a result can be checked by computation and you can run code, verify it with code. If the answers disagree, work out which one is correct and why. Also flag, as an error, any markdown in the NEW SOLUTION or any LaTeX that breaks the rules below.

3. RIGOR NOTES: Identify anything the NEW SOLUTION skipped or glossed over that actually matters for correctness, such as a hidden assumption, a condition the method depends on, an edge case where the answer changes, or a step that would lose marks on an exam if left unjustified. Use the REFERENCE SOLUTION as a guide to what a fully justified answer covers. Do not include trivial caveats.

Write the rigor notes, addressed to the student as a few short points, to {{RIGOR_PATH}}. Write them in LaTeX only (no markdown, no section title), following these rules exactly:
{{FORMAT_RULES}}
If nothing important was skipped, write only the single line "%%% NONE" to {{RIGOR_PATH}}.

Then save a JSON object in this exact shape to {{OUTPUT_PATH}}. Do not put LaTeX in the JSON; describe any math in plain words (for example, "the integral of x squared" rather than LaTeX commands):
{
  "answers_agree": true | false,
  "stored_answer_agrees": true | false | null,
  "answer_section_correct": true | false,
  "new_solution_correct": true | false,
  "correct_answer_in_words": "<the correct final answer in plain words, as best you can determine>",
  "errors": ["<plain-language description of each error in the new solution; empty list if none>"],
  "reference_solution_errors": ["<errors found in the reference solution, if any; empty list if none>"],
  "has_rigor_notes": true | false,
  "confidence": "high" | "medium" | "low"
}
Use null for stored_answer_agrees if no STORED ANSWER was given.

Then reply with only: "{{QUESTION_ID}}: review done".
```

---

## Stage 3b: Hint (only for passed questions with an empty Hint field)

A fresh subagent on the `hint` settings from `config.json`. It sees the question, its images, and the verified solution, but not the old solution or the review.

### prompts/hint.md

```
You are writing a hint for an undergraduate math problem, for a student working on their own who is stuck and doesn't want the solution spoiled. Everything below is in LaTeX, and your hint must be too.

PROBLEM:
{{QUESTION}}

IMAGES REFERENCED BY THE PROBLEM:
{{IMAGES}}
If any images are listed, open and view every one first.

VERIFIED SOLUTION (for your reference only; the student will not see it; lines starting with %%% are markers):
{{ACCEPTED_SOLUTION}}

EXAMPLES OF EXISTING HINTS (match their length, tone, and LaTeX style):
{{HINT_EXAMPLES}}

Write one hint that:
- points the student toward the starting idea, the key observation, or the right technique
- does none of the actual work: no computed values, no intermediate results, no step-by-step outline
- does not reveal or strongly imply the final answer
- is one or two sentences, in the style of the examples

Then check your hint against each of these and revise until all are true:
1. A student could not write down the final answer from the hint alone.
2. The hint contains no result from the solution beyond naming the approach.
3. The hint is consistent with the verified solution's approach.
4. The hint would actually help a stuck student take the first step.

LATEX RULES (no markdown; follow exactly):
{{FORMAT_RULES}}

Save to {{OUTPUT_PATH}} in exactly this structure:
%%% CHECKLIST: <PASSED | FAILED>
<the hint, in LaTeX>

Write FAILED only if you could not produce a hint meeting all four checks.

Then reply with only: "{{QUESTION_ID}}: hint done".
```

---

## Validation (validate.py)

Every output is checked before it is accepted. Format slippage is usually the first visible sign of drift.

**Solver output:**
- is not `%%% IMAGE UNREADABLE` (if it is, mark the question `missing_image` instead of rerunning)
- has every marker line, exactly once, in order: `BEGIN/END SOLUTION`, `BEGIN/END TAKEAWAYS`, `ANSWER TYPE:`, `BEGIN/END ANSWER`
- answer type is one of NUMERICAL, EXPRESSION, NONE, and the answer is `NONE` if and only if the type is NONE
- the solution body contains "Final answer:"
- solution length within `solution_length_bounds_chars` (set after the pilot)
- **no markdown:** no lines starting with `#`, no `**`, no lines starting with `- ` or `* ` used as bullets, no backticks
- no preamble commands (`\documentclass`, `\usepackage`, `\begin{document}`), and only constructs in the allowed subset from `format_spec.md`
- **each part (solution, takeaways, answer) passes the PDF check and the webview check** (below)

**Reviewer output:**
- is not `IMAGE UNREADABLE` (handled the same way)
- JSON parses and has every field, with the correct types
- `has_rigor_notes` matches the rigor file (`%%% NONE` if and only if false)
- if there are rigor notes: no markdown, and they pass the PDF and webview checks

**Hint output:**
- first line is `%%% CHECKLIST: PASSED`, followed by a non-empty hint
- within the length range of the existing hint examples (roughly; set bounds after the pilot)
- no markdown, and passes the PDF and webview checks
- **leak check:** the hint does not contain the final answer from the solver's answer section (compare normalized LaTeX, ignoring spaces and delimiters; for numerical answers, also check for the number itself)

Invalid solver or reviewer output is rerun once; a second failure marks the question `needs_human_review`. Invalid hint output is rerun once; a second failure just leaves the Hint field empty.

### PDF check (check_pdf.py), the primary check

The PDF is the app's main output, so this check is the one that matters most.

- `templates/app_template.tex` is a copy of the app's real template (same document class, preamble, packages, and macros) with a slot where content goes.
- `check_pdf.py` inserts a piece of content into that slot, exactly as the app would place that field, and compiles it with the app's engine (`tex_engine` in config) in non-interactive mode, halting on the first error, with the question's images available.
- **Fail** on any compile error, and on warnings that indicate broken output even when compilation continues: undefined control sequences, missing characters or glyphs, missing image files, undefined references.
- Report the error line and the offending LaTeX in the validation log.

If a TeX installation matching the app isn't available in the workspace, install one. If that isn't possible, tell the user before the pilot, since without this check broken PDFs can reach the database.

### Webview check (check_web.*), the secondary check

- Runs the content through the **same conversion the app uses for its webview** (for example, KaTeX or MathJax with the app's configuration and macros, or the app's LaTeX-to-HTML converter).
- Fails on any conversion or rendering error, reported with the offending expression.
- If the app's converter can't be run in the workspace, use the closest available equivalent and tell the user which one, so they know this check is approximate.

Both checks run on solver output, rigor notes, and hints during validation, and again on the assembled `final_app.*` after storage escaping (to catch escaping bugs in `assemble.py`).

---

## Decision logic (decide.py)

- **Pass:** `answers_agree == true` AND `new_solution_correct == true` AND `errors` is empty AND `answer_section_correct == true` AND `stored_answer_agrees` is not `false`.
- A disagreement with the stored Answer counts as a failure even if the old solution agrees: one of the three sources is wrong, and the escalation re-solve helps decide which. If the question fails again on the escalation attempt *only* because of the stored answer, mark it `needs_human_review` with the note "stored answer may be wrong".
- **Fail on first attempt:** → escalate (Stage 4).
- **Fail on escalation attempt:** → `needs_human_review`. Stop retrying.
- **Pass with `confidence == "low"`:** → `low_confidence` (assembled, but flagged for human review).
- Record every non-empty `reference_solution_errors` list.

---

## Stage 4: Escalate

1. **Re-solve from scratch** with a new solver subagent using `prompts/solver.md` and the `ESCALATE` settings, still without the old solution. Do not patch the failed solution.
2. **Review again** with a new reviewer subagent.
3. `decide.py` applies the logic above. Limit: one escalation per question (two solver attempts total).

---

## Stage 5: Assemble and store (assemble.py)

1. **Extract the parts** from the accepted solver output by their markers: solution body, takeaways body, answer type, answer. Take the rigor notes from the accepted review's rigor file. Strip all `%%%` marker lines.
2. **Build `final.tex`**: the solution, rigor notes (omitted entirely, title included, if there are none), and takeaways, in that order, with section titles expressed exactly as `format_spec.md` specifies. If the app stores the three parts as separate fields, keep them separate instead.
3. **Convert to the app's storage layout** (field mapping and storage escaping) as `final_app.*`. This is done only by code, never by a model, so every solution is converted identically.
4. **Run the PDF and webview checks on the assembled content.** Compile `preview.pdf` with the app's template for spot-checks.
5. **Write to the database** (new field or table, as agreed with the user) only after both checks pass.
6. **Fill the Answer and Hint fields**, following the rules in "Answer and Hint fields":
   - **Answer:** only if currently empty, the answer type is not NONE, and status is `passed` or `passed_after_escalation`. Convert to the Answer field format in `format_spec.md`, run both checks, and write it.
   - **Hint:** only if currently empty and a valid hint exists. Strip the checklist line, convert to the Hint field format, run both checks, and write it.
   - **Never overwrite** a filled Answer or Hint field.
   - Record each filled field in the provenance store.

Store per question (never overwrite existing content):

- question ID
- final assembled solution
- status: `passed`, `passed_after_escalation`, `needs_human_review`, `low_confidence`, or `missing_image`
- image paths used
- answer type, and whether the Answer and Hint fields were filled by this run
- difficulty level
- `prompt_version`, and the model and effort used for each solver, reviewer, and hint call
- number of solver attempts
- raw reviewer output for each review

---

## Monitoring (metrics.py)

### Per-batch metrics

After every batch, append one line to `run_log.md` with:

- batch number and question ID range
- pass rate (first attempt), escalation rate, human-review rate
- answer disagreement rate with old solutions and with stored answers
- first-attempt PDF and webview check failure rates
- average and median solution length
- `prompt_version`

Compare each batch with the running average from earlier batches. If any metric shifts sharply (for example, escalation rate doubles, compile failures jump, or average length drops by a quarter), **pause and tell the user** before continuing.

### Canary questions

After the pilot, the user picks ~5 questions whose final output they approved. Their outputs are saved in `canaries/`, and their IDs go in `config.json`.

Every `canary_every_n_questions` questions, rerun the full pipeline on the canaries (writing to a separate canary-run folder, not over the approved versions). Compare each new output with the approved one on:

- same final answer
- similar length (within ~25%)
- same structure (sections, Rigor Notes present or absent)
- still intuition-first: motivation explained for each step, no formal rigor in the main solution

Report the comparison to the user in a few lines. If canaries have noticeably changed, pause the run until the user decides how to proceed.

### Spot-checks

After each batch, pick 2 random passed questions and give the user the paths to their `preview.pdf`, so they can look at them as their students will. Don't paste the full solutions into your own context.

---

## Run plan

### 1. Pilot (before the full run)

- Select 20–30 questions spanning the range of topics and difficulty (include short and long old solutions, and several questions with images).
- Run the full pipeline on them.
- **Quality check for the answer section:** on ~10 of the pilot questions, also run the solver with the answer section removed from the prompt, and review both versions. Report whether error rates or explanation quality differ. If the version with the answer section is noticeably worse, tell the user before continuing.
- Ask the user to **load several outputs in the actual app**, both as a generated PDF and in the webview, and confirm they display correctly, including math, structure, and images. The automated checks are a safeguard, not a substitute for seeing the real output.
- Report to the user:
  - how many questions reference images, how many were resolved, and how many were marked `missing_image` (with examples of how the missing ones were referenced)
  - how many outputs failed the PDF or webview check on the first attempt, and the most common LaTeX problems (these may suggest tightening `format_rules.md`)
  - how often the reviewer found real errors
  - how often answers disagreed with the old solutions, and which side was right
  - how many stored Answers disagreed with the new solutions, and which side was right
  - how answer types were classified (any proofs wrongly given an answer, or computational questions marked NONE?)
  - several generated Answers next to existing ones, so the user can confirm the format matches
  - several generated hints, and how many failed the leak check
  - whether difficulty levels looked sensible (any ROUTINE problems that failed review?)
  - roughly how much usage the pilot consumed, and a projection for the full 1,000
  - suggested values for triage thresholds and solution length bounds
  - a few sample `preview.pdf` files for the user to read
- Ask the user to approve the outputs, pick the canary questions, and confirm `config.json`.
- **Wait for approval** before the full run.

### 2. Full run

- Follow the per-batch loop. Keep sessions to a few batches each.
- At the start of each session, report how many questions are done, the latest metrics, and what's next, then continue.
- If usage runs low, finish the current stage, save progress, and stop with a status update.

### 3. Final report

At the end, give the user:

- counts per status (`passed`, `passed_after_escalation`, `needs_human_review`, `low_confidence`, `missing_image`)
- the list of question IDs needing human review or missing images, with a one-line reason each
- the number of old solutions the reviewer found errors in
- the number of Answer and Hint fields filled, and the number of stored Answers flagged as possibly wrong
- any prompt version changes during the run, and which question ranges each version covered
