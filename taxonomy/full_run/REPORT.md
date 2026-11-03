# Full classification run: results for review

Generated 2026-11-02. Nothing here has been written to the database. 21,311 uncategorized questions; 21,311 have a final label, 0 still pending.

## How each label was decided

| Path | Questions |
|---|---:|
| first pass, high confidence, no second look | 12,532 |
| first pass and an independent second model agreed | 4,459 |
| the two models disagreed; Opus decided | 2,596 |
| Fluid Mechanics pilot (Sonnet, calibrated against Opus) | 1,642 |
| first pass had no usable subtopic; second model was confident | 73 |
| pilot question re-run with the subject it belongs to | 9 |

First pass: Haiku for textbook and exam sources, Sonnet for olympiad and puzzle sources. Second look on every medium or low label, by the other model (Sonnet on textbook items, Haiku on olympiad items). Disagreements went to Opus, which saw both proposals unlabelled and in random order.

- Textbook / exam: second model agreed on 1,403 of 2,130 uncertain items (65%).
- Olympiad / puzzle: second model agreed on 3,056 of 4,925 uncertain items (62%).

High-confidence first-pass labels were not second-checked. To measure them, Opus labelled a random 60 textbook and 60 olympiad high-confidence questions from scratch, without seeing the first label:

- Textbook / exam (Haiku first pass): same subtopic on 47 of 50 comparable questions (94%); same subject on 59 of 60. The misses were neighbouring subtopics in the same branch.
- Olympiad / puzzle (Sonnet first pass): same subtopic on 47 of 51 comparable questions (92%); same subject on 59 of 60. The misses were neighbouring subtopics in the same branch.

## Questions per subject

| Subject | Questions | Subtopics used / in tree | Wastebasket |
|---|---:|---:|---:|
| Calculus | 1,609 | 102 / 102 | 0 |
| Complex Analysis | 174 | 18 / 18 | 0 |
| Linear Algebra and Differential Equations | 946 | 87 / 89 | 9 |
| Algebra | 1,136 | 68 / 68 | 3 |
| Abstract Algebra | 223 | 23 / 23 | 5 |
| Number Theory | 2,071 | 68 / 68 | 4 |
| Combinatorics | 2,021 | 117 / 117 | 21 |
| Geometry | 648 | 51 / 51 | 12 |
| Probability and Stochastic Processes | 3,242 | 138 / 138 | 2 |
| Statistics | 293 | 31 / 31 | 1 |
| Quantitative Finance | 497 | 51 / 51 | 3 |
| Economics | 265 | 32 / 32 | 0 |
| Mechanics | 1,267 | 111 / 111 | 2 |
| Electromagnetism and Special Relativity | 556 | 55 / 55 | 0 |
| Quantum Mechanics | 12 | 6 / 6 | 0 |
| Thermodynamics | 86 | 15 / 15 | 0 |
| Heat Transfer | 537 | 47 / 47 | 0 |
| Fluid Mechanics | 1,769 | 107 / 107 | 3 |
| Conventional Energy Technologies | 2,430 | 166 / 166 | 1 |
| Electrical Machinery | 385 | 57 / 57 | 0 |
| Power Systems and Power Electronics | 57 | 16 / 17 | 0 |
| Material Science | 1,087 | 131 / 131 | 1 |

## Wastebasket

67 questions have no fitting subtopic, and 3 have a subject but no subtopic. The list is in `wastebasket.csv`, with each model's reason.

## Small subtopics

71 of 1500 subtopics hold fewer than 3 questions (counting the 401 already filed); 3 are empty. 19 of these match a textbook TOC heading, so the merge rule keeps them. Opus checked the other 52: it judged 50 standard textbook sections, which these sources rarely cover, so they stay. It proposes merging 2: Algebraic Integers and Number Rings into Rings, Subrings and Units (Abstract Algebra); Zero-Sum Subsets Modulo n into Division Algorithm and Residue Forms (Number Theory). Everything is listed in `tiny_subtopics.csv`. Nothing has been merged yet.

## Data-quality flags

| Flag | Questions |
|---|---:|
| needs_data | 278 |
| broken_text | 169 |
| no_solution | 107 |
| mismatch | 73 |
| key_conflict | 71 |
| truncated_solution | 13 |
| open_problem | 10 |
| figure_missing (found by script, not hidden) | 470 |

Per-question list: `flags.csv`. `no_solution` and `truncated_solution` come from the Fluid Mechanics pilot only. `key_conflict` was added partway through the textbook run, so earlier batches mention key conflicts only in the note.

## Question type

| Type | Questions |
|---|---:|
| numerical | 10,347 |
| proof | 6,840 |
| explanation/reasoning | 2,507 |
| objective | 1,617 |

## Tags

- 8,692 questions have at least one key technique tag; 2,491 have a supporting tag; 8,655 have a task tag.
- Most used key tags: Modular Arithmetic (602), Explicit Construction (546), Divisibility Argument (446), Substitution (424), Bound and Construct (398), Factorization (378), Induction (282), Symmetry Argument (270), Casework (251), Parity (251), Proof by Contradiction (244), Coordinate Method (223), Recursion (192), Monotonicity Argument (190), Size Estimate (178).
- Task tags: Explain a Concept (1481), Prove Existence (802), Find the Optimum (767), Find All Solutions (675), Count Configurations (628), Prove an Identity (591), Prove an Inequality (542), Derive a Relation (515), Prove Impossibility (317), Compare Alternatives (289), Limit or Asymptotics (247), Design or Size (244), Evaluate a Sum or Integral (240), Sketch or Plot (210), Performance and Efficiency (197), Read Tables or Charts (161), Optimal Strategy (97), Minimum Number of Moves (90), Estimate (84), Expected Waiting Time (84), Point Finding (76), Last Digits and Remainders (75), Who Wins (65), Find the Locus (44), Fair Value of a Game (41), Expected Count (38), Tiling and Covering (32), Spot the Flaw (14), No Prerequisites (9).
- Tags the models proposed (not in the list, not applied): Ramsey Argument (1), Choice of Class Representatives (1), Transfinite Induction (1), Kelly Log-Growth (1), Lagrangian Duality (1).

## Review

Open `review/index.html`. It links one page per subject, and each card shows how its label was decided. Filter by "Opus decided" or by low confidence to check the hard cases first. Mark anything wrong, then press "Copy corrections" and paste the result back.

## What applying this would write (after your review)

- `questions.topic/branch/subtopic` for every labelled question (wastebasket and pending stay `Uncategorized`).
- `questions.type` from the classifier.
- `question_tags` rows with role `key`, `supporting` or `task`.
- A DB backup first. The 401 questions filed earlier are not touched.
