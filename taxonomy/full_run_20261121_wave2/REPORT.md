# Classification of the remaining answer-set questions (2026-11-21, second wave)

2,104 questions still `Uncategorized` after the first wave (`full_run_20261121_sets`): U-MATH (university calculus and algebra), CHAMP (olympiad problems adapted from Engel), and the answer-set questions that had no vector for the first wave (716 have no solution yet, most of them contest geometry waiting for its figure: classified from the question alone). Same pipeline: U-MATH as textbook questions (Haiku first pass, textbook tag file, Sonnet second opinion), the rest as olympiad questions (Sonnet first pass, olympiad tag file, Haiku second opinion); blind second opinion on every medium/low label and (Sonnet) on every wastebasket or other-subject label; Opus adjudication of every disagreement, A/B order random. Candidate subjects: the dataset's own label (U-MATH subject, CHAMP's Engel chapter, HARP / Omni-MATH / AnswerBench labels), the subject vote of the 20 nearest categorized questions where the question has a vector, and Probability first for questions asking for a probability or expectation.

## Outcome

- Placed in a subtopic: 2,103; left `Uncategorized`: 1 (`wastebasket.csv`).
- How the final label was reached: high-confidence first pass 1,264; first and second agree 479; second opinion accepted 7; Opus 354.
- Confidence of the label kept (placed questions): high 1,466, medium 599, low 38. It goes into `classification_conf`, with `how` in `classification_how`.
- Flags: {'key_conflict': 1, 'needs_data': 2, 'mismatch': 4, 'broken_text': 2} (`flags.csv`).

| Source | Subjects (questions) |
|---|---|
| U-MATH | Calculus 736, Algebra 281, Geometry 37, Linear Algebra and Differential Equations 14, Mechanics 5, Fluid Mechanics 2, Number Theory 1 |
| American Mathematics Competitions | Geometry 408, Algebra 71, Combinatorics 62, Probability and Stochastic Processes 21, Number Theory 12, wastebasket 1 |
| Concept and Hint-Annotated Math Problems | Algebra 117, Number Theory 82, Combinatorics 44, Calculus 18, Geometry 3, Abstract Algebra 1, Probability and Stochastic Processes 1 |
| Omni-MATH | Combinatorics 52, Geometry 22, Algebra 15, Number Theory 10, Probability and Stochastic Processes 7, Calculus 1, Linear Algebra and Differential Equations 1 |
| American Invitational Mathematics Examination | Geometry 51, Combinatorics 17, Algebra 2, Probability and Stochastic Processes 2, Number Theory 1 |
| United States Competitions | Geometry 3, Combinatorics 1 |
| IMO-Bench AnswerBench | Combinatorics 2 |

### U-MATH: dataset subject -> subject filed

- Algebra -> Algebra: 145
- Algebra -> Geometry: 15
- Algebra -> Calculus: 11
- Algebra -> Linear Algebra and Differential Equations: 7
- Algebra -> Number Theory: 1
- Differential Calculus -> Calculus: 195
- Differential Calculus -> Algebra: 3
- Differential Calculus -> Linear Algebra and Differential Equations: 1
- Integral Calculus -> Calculus: 203
- Integral Calculus -> Linear Algebra and Differential Equations: 2
- Integral Calculus -> Mechanics: 1
- Integral Calculus -> Algebra: 1
- Integral Calculus -> Fluid Mechanics: 1
- Multivariable Calculus -> Calculus: 158
- Multivariable Calculus -> Geometry: 13
- Multivariable Calculus -> Mechanics: 4
- Multivariable Calculus -> Algebra: 2
- Precalculus -> Algebra: 125
- Precalculus -> Calculus: 21
- Precalculus -> Geometry: 9
- Precalculus -> Linear Algebra and Differential Equations: 3
- Precalculus -> Fluid Mechanics: 1
- Sequences and Series -> Calculus: 148
- Sequences and Series -> Algebra: 5
- Sequences and Series -> Linear Algebra and Differential Equations: 1

## Proposed tags (added 2026-11-21, owner: "add the proposed tags")

The textbook tag file the U-MATH first pass used has no algebraic moves, which is where these came from.

- Trigonometric Power Integrals (27 questions): new tag under Analysis tools.
- Completing the Square (12 questions): new tag under Algebraic moves; it was an alias of Sum of Squares, which is about proving non-negativity.
- Substitution Reduction (8 questions): the existing Substitution tag; added as its alias, and the 8 questions got Substitution.

All as key tags on the proposing questions only (`taxonomy/tags_draft.md`); no bank-wide retag.

