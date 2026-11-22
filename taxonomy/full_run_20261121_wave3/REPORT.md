# Classification of the set-aside answer-set questions (2026-11-21, third wave)

246 questions imported 2026-11-21 20:07 from the set-aside rows (ids 38358-38608: Omni-MATH, HARP, U-MATH) and embedded after their solves were judged (owner: "Classify them if they're embedded"; 0 have no solution; the 5 unsolved rows wait). Same pipeline as the second wave: U-MATH as textbook questions (Haiku first pass, textbook tag file, Sonnet second opinion), the rest as olympiad questions (Sonnet first pass, olympiad tag file, Haiku second opinion); blind second opinion on every medium/low label and (Sonnet) on every wastebasket or other-subject label; Opus adjudication of every disagreement, A/B order random. Candidate subjects: the dataset's own label (U-MATH subject, CHAMP's Engel chapter, HARP / Omni-MATH / AnswerBench labels), the subject vote of the 20 nearest categorized questions where the question has a vector, and Probability first for questions asking for a probability or expectation.

## Outcome

- Placed in a subtopic: 246; left `Uncategorized`: 0 (`wastebasket.csv`).
- How the final label was reached: high-confidence first pass 95; first and second agree 86; second opinion accepted 0; Opus 65.
- Confidence of the label kept (placed questions): high 131, medium 109, low 6. It goes into `classification_conf`, with `how` in `classification_how`.
- Flags: {'broken_text': 2, 'needs_data': 1} (`flags.csv`).

| Source | Subjects (questions) |
|---|---|
| Omni-MATH | Algebra 62, Number Theory 50, Combinatorics 44, Geometry 24, Probability and Stochastic Processes 14, Calculus 7, Linear Algebra and Differential Equations 4, Abstract Algebra 2 |
| American Mathematics Competitions | Algebra 20, Number Theory 5, Geometry 4, Combinatorics 2, Probability and Stochastic Processes 1 |
| U-MATH | Calculus 5, Algebra 1 |
| American Invitational Mathematics Examination | Geometry 1 |

### U-MATH: dataset subject -> subject filed

- Algebra -> Algebra: 1
- Differential Calculus -> Calculus: 3
- Multivariable Calculus -> Calculus: 1
- Precalculus -> Calculus: 1

## Proposed tags (not added)


