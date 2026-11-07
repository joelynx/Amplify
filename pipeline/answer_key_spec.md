# Answer key (`questions.answer_key`)

The quiz grades a question from its answer key: one entry per part the student answers. The
column is JSON text (migration 008, nullable). `questions.answer` stays the human-readable
LaTeX answer shown in PDFs and the Browser; the key is what the quiz grades with. When the key
is NULL the app derives a one-part key from `answer` and `type` at load time (see "Legacy
rows").

Written by the solution pipeline for non-math subjects (and by the study-aids pass over
book-solved questions); the app never writes it.

## Shape

```json
{
  "v": 1,
  "parts": [
    {"label": "a", "ask": "thermal efficiency of the reheat cycle", "kind": "number",
     "value": 38.6, "unit": "%", "tol": null},
    {"label": "b", "ask": "net work per kg of steam", "kind": "number",
     "value": 1236, "unit": "kJ/kg", "tol": 0.05},
    {"label": "c", "ask": "", "kind": "choice", "value": "b", "options": 4},
    {"label": "d", "ask": "", "kind": "choice", "value": ["a", "c"], "options": 4},
    {"label": "e", "ask": "", "kind": "truefalse", "value": true},
    {"label": "f", "ask": "", "kind": "expression", "value": "\\frac{\\pi}{4}"},
    {"label": "g", "ask": "function of a cooling tower", "kind": "points",
     "points": ["rejects the condenser heat to the atmosphere", "..."]}
  ]
}
```

- `label`: the part's label as the question prints it (`a`, `b`, `ii`, `2`), or `""` for a
  question with a single part. Shown as "(a)".
- `ask`: a few words naming what the part asks for, shown next to its input. It never
  contains the answer or any value from the solution. May be `""` when the label says enough.
- `kind`:
  - `number`: `value` is a JSON number; `unit` is the unit the student answers in (plain text,
    see Units; `""` for a pure number); `tol` is the relative tolerance or `null` for the
    default.
  - `choice`: `value` is one option letter (`"a"`...) or a list of letters when the question
    asks for every correct option; `options` is the number of options (may be absent).
    Options are counted in the order the question lists them; option 1 = `a`.
  - `truefalse`: `value` is `true` or `false`.
  - `expression`: `value` is LaTeX. Auto-graded only by a normalized exact match; otherwise the
    student self-assesses after seeing it.
  - `points`: `points` is a list of LaTeX strings, the things a full-marks answer contains
    (descriptive and derivation parts). Never auto-graded: after submitting, the student sees
    the checklist and marks the part Got it / Partial / Missed.

## Grading (app)

Per part a credit in [0, 1]; the question's credit is the mean over its parts.

- `number`: the student's input is read as a number after removing whitespace, `$...$`,
  `\(...\)`, `\boxed{}`, thousands separators, and any unit text after the number. Accepted
  forms: `12.5`, `-3`, `1/8`, `1.2e5`, `1.2E-3`, `1.2x10^5`, `1.2*10^5`, `1.2 \times 10^{5}`,
  `38.6%`. If the student typed a unit that is the expected unit with a different SI prefix
  (`MPa` for `kPa`, `W` for `kW`, `mm` for `m`), the number is converted; any other typed unit
  is ignored (the expected unit is shown next to the input, so it is the contract).
  Correct when `|x - value| <= tol * |value|` (and `|x| <= 1e-12` when `value` is 0).
  Default `tol`: exact for an integer `value` with an empty unit (counts, AIME-style answers),
  else 0.02 when `unit` is non-empty, else 0.01.
- `choice`: input normalized to letters: `b`, `B`, `(b)`, `b)`, `b.`, `option b`, and the
  option number `2`, all mean `b`. A list answer is compared as a set.
- `truefalse`: `t`, `true`, `yes`, `correct` -> true; `f`, `false`, `no`, `incorrect` -> false.
- `expression`: normalized string match (the current `loosely_equal` rules), else
  self-assessed after reveal.
- `points`: self-assessed after reveal (Got it 1, Partial 0.5, Missed 0).

A question counts as correct when every part has credit 1, wrong when the total is 0, and
partial otherwise; its score is the question's points times its credit.

## Units

Plain text the student can read in an input suffix: `kJ/kg`, `kW`, `MW`, `%`, `kgf/cm^2`,
`m^3/s`, `°C`, `K`, `N m`, `kg/s`, `rpm`, `Rs/kWh`. `^` marks a power; `/` and a space separate
factors. The pipeline renders it into the LaTeX `answer` text as `\mathrm{...}`.

## Legacy rows (answer_key NULL)

The app derives a one-part key, label `""`:

- `type` objective and `answer` is a single option (`B`, `(b)`, `b)`) -> `choice`; a list
  (`A, B, C`) -> `choice` with a list; `TRUE` / `FALSE` -> `truefalse`. `options` = the number
  of `\item`s in the question's first `enumerate`, when there is one.
- `answer` that reads as a number, optionally followed by a unit -> `number` with that unit.
- any other non-empty `answer` -> `expression`.
- empty `answer` -> `points` with an empty list (self-assessment without a checklist).

## What the quiz may show before an answer is submitted

`label`, `ask`, `kind`, `unit`, `options` only. Never `value`, `points` or `tol`.

The app also sends a boolean `multi`, derived from the key: true when a `choice` part's `value`
is a list, so the quiz offers multi-select (it says only that several options may be picked,
not which or how many). The quiz receives each part as
`{label, ask, kind, unit, options, multi}`: `unit` is `""` except on `number` parts, `options`
is null except on `choice` parts, `multi` is false except on list-valued `choice` parts.
