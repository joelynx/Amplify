# Classification of the answer-set imports (2026-11-21)

7,998 embedded questions from the answer sets (MathArena, IMO-Bench AnswerBench, HARP, Omni-MATH), run through the 11-02 pipeline as olympiad sources: Sonnet first pass with the olympiad tag file, blind second opinion on every medium/low label (Haiku) and on every wastebasket or other-subject label (Sonnet), Opus adjudication of every disagreement (A/B order random). Candidate subjects come from the datasets' own labels (HARP and Omni-MATH subjects, AnswerBench categories), the subject vote of the 20 nearest categorized questions (share >= 20%), and Probability first for questions asking for a probability or expectation. U-MATH, CHAMP and the unembedded rows are not in this run.

Two tree additions during the run (owner): Algebra > Elementary Algebra > Arithmetic and Pre-Algebra (7 subtopics) with Combinatorics > Logic and Knowledge Puzzles > Propositional Logic and Deduction, then Geometry > Plane Geometry > Basic Measurement (4 subtopics). After each, the first-pass wastebasket and the labels filed in a neighbour of the new nodes (pre-algebra dataset labels in nearby Algebra subtopics, the two logic-puzzle subtopics, easy geometry in nearby geometry subtopics) were filed again with the new trees (650 questions) and went through the same checks (`how` starts with `refile-`).

## Outcome

- Placed in a subtopic: 7,984; left `Uncategorized`: 14 (`wastebasket.csv`).
- How the final label was reached: high-confidence first pass 3,305; first and second agree 2,604; second opinion accepted 13; Opus 2,076 (of which refiled: high 334, agree 174, Opus 142).
- Confidence of the label kept (placed questions): high 4,583, medium 3,312, low 89. It goes into the new `classification_conf` column with `how` in `classification_how` (migration 013).
- Questions in the new subtopics: Fractions, Decimals and Place Value 71, Order of Operations and Numerical Evaluation 70, Linear Equations and Small Systems 65, Exponents and Scientific Notation 54, Estimation and Comparing Numbers 52, Units, Time and Calendar Arithmetic 51, Defined Operations 44, Propositional Logic and Deduction 36, Circle Area and Circumference 34, Angle Sums and Angle Measures 27, Perimeter and Area of Basic Figures 21, Scaling of Lengths, Areas and Volumes 11.
- Flags: {'key_conflict': 2, 'needs_data': 73, 'broken_text': 16} (`flags.csv`).

| Source | Subjects (questions) |
|---|---|
| Omni-MATH | Algebra 1105, Combinatorics 866, Number Theory 729, Geometry 630, Probability and Stochastic Processes 370, Calculus 66, Linear Algebra and Differential Equations 21, Abstract Algebra 15, wastebasket 13, Statistics 3 |
| American Mathematics Competitions | Algebra 1490, Geometry 662, Number Theory 467, Combinatorics 349, Probability and Stochastic Processes 199, Statistics 4, Linear Algebra and Differential Equations 2, Mechanics 1, Calculus 1, wastebasket 1 |
| IMO-Bench AnswerBench | Combinatorics 116, Geometry 92, Algebra 91, Number Theory 89, Probability and Stochastic Processes 3, Abstract Algebra 1, Linear Algebra and Differential Equations 1 |
| American Invitational Mathematics Examination | Geometry 177, Algebra 40, Combinatorics 28, Number Theory 27, Probability and Stochastic Processes 21 |
| United States Competitions | Geometry 83, Combinatorics 60, Number Theory 48, Algebra 45, Probability and Stochastic Processes 31, Calculus 8, Statistics 1, Abstract Algebra 1 |
| Other Asian Olympiads | Combinatorics 5, Number Theory 1, Abstract Algebra 1 |
| Other European Olympiads | Combinatorics 6, Number Theory 1 |
| China Team Selection Test | Algebra 2, Combinatorics 2 |
| ELMO Mathematical Olympiad Shortlist | Combinatorics 2, Algebra 1 |
| Taiwan Team Selection Test | Combinatorics 2, Number Theory 1 |
| Indian Olympiads | Combinatorics 2, Abstract Algebra 1 |
| MathArena APEX | Combinatorics 3 |
| International Mathematical Olympiad | Algebra 1, Combinatorics 1 |
| Mock Olympiads | Number Theory 1, Combinatorics 1 |
| All-Russian Olympiad | Combinatorics 1, Calculus 1 |
| United States of America Team Selection Test Selection Test | Number Theory 1 |
| Chinese Olympiads | Combinatorics 1 |
| European Girls' Mathematical Olympiad | Combinatorics 1 |
| Japan Mathematical Olympiad Final Round | Combinatorics 1 |
| Romanian Masters of Mathematics | Combinatorics 1 |

## Bank check (earlier questions, after the tree additions)

404 earlier questions filed in a neighbour of the pre-algebra and logic subtopics, or still `Uncategorized`, were classified again with those trees (the check ran before the geometry branch existed). 28 whose new label was in a new subtopic, or that were still `Uncategorized`, went to Opus beside their current label (blind). Other changed labels were left alone. Outcomes (`bank_check.csv`):

- leftover, kept DB label: 1
- leftover, neither: 6
- leftover, new label: 10
- placed, kept DB label: 2
- placed, neither: 1
- placed, new label: 8

Leftovers Opus placed join `final_labels.json` (`how` = `bank-opus`). The 9 already-placed questions Opus moved are in `bank_relabels.json`; `apply_full_run.py` does not move placed questions, so they need their own write after review.

## Proposed tags (not added)

- Find All Solutions (1)
- Count Configurations (1)

