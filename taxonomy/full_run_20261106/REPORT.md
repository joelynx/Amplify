# Classification of the 11-03/11-04 imports (2026-11-06)

3,758 questions that were still `Uncategorized` (the eight books imported on 11-03/11-04), run through the 11-02 pipeline unchanged: Haiku first pass, blind Sonnet second opinion on every medium/low, wastebasket or other-subject label, Opus adjudication of every disagreement (A/B order random). Trees regenerated from `taxonomy.json` (identical to the 11-02 trees plus the two approved merges). Candidate subjects: the book's default subjects plus any subject holding >= 20% of the 20 nearest categorized questions by embedding (replaces the 11-02 cluster labels). The 67 questions the 11-02 run left in the wastebasket were not re-run.

## Outcome

- Placed in a subtopic: 3,704; left `Uncategorized`: 54 (`wastebasket.csv`).
- How the final label was reached: high-confidence first pass 2,189; first and second agree 899; second opinion accepted 23; Opus 647.
- Flags: {'needs_data': 14, 'mismatch': 5, 'key_conflict': 3, 'broken_text': 4} (`flags.csv`).

| Book | Subjects (questions) |
|---|---|
| Strang | Linear Algebra and Differential Equations 1176, Probability and Stochastic Processes 29, Calculus 28, Algebra 21, Geometry 12, Combinatorics 10, Number Theory 10, Statistics 8, Abstract Algebra 7, wastebasket 2, Complex Analysis 1 |
| Blitzstein & Hwang | Probability and Stochastic Processes 600, Combinatorics 31, Statistics 14, Quantitative Finance 1 |
| Sahoo | Probability and Stochastic Processes 303, Statistics 153, Combinatorics 5, Calculus 4 |
| Dekking et al. | Probability and Stochastic Processes 222, Statistics 114, wastebasket 20, Algebra 2, Quantitative Finance 1, Calculus 1 |
| de Lange & Pierrus | Mechanics 257, Electromagnetism and Special Relativity 19, Calculus 12, Fluid Mechanics 9, wastebasket 7, Linear Algebra and Differential Equations 2, Geometry 1, Quantum Mechanics 1, Thermodynamics 1 |
| Bertsekas & Tsitsiklis | Probability and Stochastic Processes 264, Statistics 35, Combinatorics 3, Calculus 1 |
| Oksendal | Probability and Stochastic Processes 153, Quantitative Finance 36, Calculus 2 |
| Stefanica, Radoicic & Wang | Probability and Stochastic Processes 58, Quantitative Finance 37, wastebasket 25, Combinatorics 24, Calculus 12, Linear Algebra and Differential Equations 11, Number Theory 5, Geometry 4, Algebra 3, Complex Analysis 1 |

## Proposed tags (not added)

- Pivotal Quantity (16)
- Counterexample (6)
- Factorization Criterion (3)
- Harmonic Balance (3)
- Poissonization (1)
- Pairing Argument (1)

## Tree additions and re-file (owner, 2026-11-06)

Seven subtopics added to `taxonomy.json`: Statistics > Mathematical Statistics > **Descriptive Statistics** (Measures of Center, Measures of Spread, Quantiles and Boxplots, Histograms and Empirical Distribution Functions) and Electromagnetism and Special Relativity > Special Relativity > **Relativistic Kinematics** (Lorentz Transformations, Time Dilation and Length Contraction, Relativistic Velocity Addition). The 29 questions of this run that had gone to the wastebasket for want of them, plus 9344 from the 11-02 wastebasket (mode of survey data), went through the same three stages again with the new trees and are now placed:

- Descriptive Statistics > Histograms and Empirical Distribution Functions: 8
- Descriptive Statistics > Measures of Center: 5
- Descriptive Statistics > Measures of Spread: 4
- Descriptive Statistics > Quantiles and Boxplots: 6
- Relativistic Kinematics > Lorentz Transformations: 4
- Relativistic Kinematics > Relativistic Velocity Addition: 1
- Relativistic Kinematics > Time Dilation and Length Contraction: 2

`wastebasket.csv` now holds the 25 C++ programming questions from the Quant150 book, which fit no subject. `final_labels.json` carries the new placements (`how` = `refile-...`) and the 9344 record.

## Proposed tags added (owner, 2026-11-06)

Pivotal Quantity, Factorization Criterion (new family Statistics moves), Counterexample (Proof methods; the alias Counterexample Construction moved here from Explicit Construction) and Harmonic Balance (Physical and engineering reasoning) are in `taxonomy/tags_draft.md` and are key tags on the questions whose tagger proposed them: Pivotal Quantity 16, Counterexample 6, Factorization Criterion 3, Harmonic Balance 3. Not added: Poissonization and Pairing Argument (one question each; Pairing already exists).
