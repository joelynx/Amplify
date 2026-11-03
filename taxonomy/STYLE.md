# Taxonomy drafting brief

You are drafting part of the topic tree for a study-question bank (about 21,700 questions from
textbooks, exam papers, olympiad and puzzle collections). Each question gets exactly one leaf.
Read SUBJECTS.md (same folder) for the 22 subjects, their scope and the boundary rules.

## Levels

Subject > Topic > Branch > Subtopic.
- Subject: fixed (SUBJECTS.md). A subject holds one or more topics.
- Topic: a recognised field or course inside the subject (for example "Probability" and
  "Stochastic Processes" inside Probability and Stochastic Processes; "Fluid Mechanics" alone
  inside Fluid Mechanics). Usually 1-3 per subject. Topic names must be unique across the whole
  bank, so do not reuse a subject's name as a topic name in another subject.
- Branch: a chapter-sized area (3-12 per topic).
- Subtopic: ONE main idea, concept, theorem, law or method that a student would study as a unit
  and recognise by name (3-15 per branch). This is the finest level and the one questions are
  filed under.

The owner's existing tree shows the intended granularity. Calculus (excerpt):

```
Calculus > Single Variable Differential Calculus > Limits (Single Variable)
                                                 > Taylor's Theorem
                                                 > Uniform Continuity
Calculus > Multivariable Differential Calculus   > Gradient and Directional Derivatives
                                                 > Lagrange Multipliers
Calculus > Sequences and Series                  > Cauchy Criterion
Linear Algebra > Vector Spaces                   > Rank-Nullity Theorem
```

## Granularity

- Aim for subtopics that would hold roughly 8-60 questions of this bank. The cluster sizes you are
  given are your evidence. A core concept may be smaller; do not create a subtopic for something
  the bank does not contain unless it is a core concept of the field that the sources clearly
  cover (their tables of contents say so).
- Split a subtopic that bundles two ideas a student would study separately
  ("Intermediate Value/Mean Value/Rolle's Theorem" is two ideas). Merge subtopics that a student
  would not tell apart.
- Use the tables of contents as a guide to what the field covers, not as labels. Book chapter titles
  are often unsuitable ("Further Topics", "Preliminaries", "Applications", "Some Special Cases").
- No catch-all nodes: no "Miscellaneous", "MISC", "Other", "General", "Basics", "Introduction",
  "Applications", "Further Topics". Outliers go to a wastebasket that is handled separately.

## Naming

- Title Case; keep minor words lower case (and, or, of, the, in, for, to, a, an, on, with, by, vs).
- Never use "/" in a name (write "and"). At most one parenthetical, used only to disambiguate
  (for example "Continuity (Multivariable)").
- At most 60 characters. Use the name a student would search for. Standard abbreviations only
  (ODE, PDE, IS-LM, LMTD).
- Names must be unique within their topic. Do not repeat the branch name inside every subtopic name.
- No question-type words ("Problems", "Exercises", "Numericals", "Questions").

## One concept, one home

A concept lives in one place. Where two subjects legitimately need the same idea for different
content, name the nodes so a reader can tell them apart, and record the decision. Fixed decisions:
- Probability owns probability-generating and moment-generating functions; Combinatorics owns
  generating functions used for counting.
- Algebra owns the named classical inequalities (AM-GM, Cauchy-Schwarz, Jensen, rearrangement,
  Hölder, Schur, ...); Geometry owns geometric inequalities.
- Algebra owns solving linear recurrences; Combinatorics owns setting up recurrences to count.
- Algebra owns complex numbers in algebraic and polar form, roots of unity; Complex Analysis owns
  functions of a complex variable.
- Calculus owns optimisation (extrema, Lagrange multipliers, convex optimisation, gradient
  methods, linear programming if present).
- Linear Algebra and Differential Equations owns Laplace transforms, separation of variables and
  Fourier methods for PDEs; Calculus owns Fourier series as series.
- Thermodynamics owns cycle thermodynamics in general (Carnot, Otto, Diesel, Brayton, Rankine,
  refrigeration). Conventional Energy Technologies holds everything from the two power-plant
  books, so its nodes are named at plant level (for example "Regenerative Feedwater Heating").
- Fluid Mechanics owns Buckingham Pi and similitude; physics questions that only use a
  dimensional argument are filed by their physical content.
- Electrical Machinery owns magnetic circuits; Power Systems and Power Electronics owns
  three-phase circuits and power-system analysis; Electromagnetism and Special Relativity owns
  basic circuit theory (DC networks, RC/RL/RLC transients, AC phasors).
- Society of Actuaries questions on interest theory, annuities and loans go to Quantitative Finance.
- Material Science owns band theory and semiconductors as material properties.

## What you are given

- Your subjects and notes on their sources.
- The tables of contents in C:\Users\Lenovo\OneDrive\Desktop\Amplify\taxonomy\TOCs_clean.md for
  the books named in your task (find them by their `#` heading).
- A file of embedding clusters routed to your subjects. Each block is
  `C<id> (n=<size>) sources: ... | routed: <subject shares>` followed by three member stems (the
  most central member, a middle one and a peripheral one). The full member list of each cluster is
  in ...\scratchpad\clusters.json (field "qids"). Print any question with
  `C:\Users\Lenovo\OneDrive\Desktop\Amplify\.venv\Scripts\python.exe <scratch>\tax\show.py [--sol 400] <qid> ...`
  Look beyond the three stems for at least one cluster in five, more where a cluster looks mixed.
  Read-only: never write to the database.

## Output

Write one Markdown file (path in your task) in exactly this shape:

```
# Subject: <name>
## Topic: <name>
### Branch: <name>
- <Subtopic> — <scope note, at most 15 words> (~<estimated question count>)
```

Repeat for each of your subjects. The scope note says what belongs there and, where a neighbour
could be confused with it, what does not ("excludes ...; see <subtopic>"). The estimate comes from
the clusters you mapped to it.

Then:

```
## Coverage
C<id> -> <Topic> > <Branch> > <Subtopic> [; <second subtopic> ...]
C<id> -> not mine: <subject or Other: ...>
```
One line for every cluster you were given. A cluster that spreads over several subtopics lists the
main ones.

```
## Decisions and open questions
- ...
```
Record boundary calls, anything you deliberately left out, and anything the owner should decide.
