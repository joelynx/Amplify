# Mathematics

Profile for the maths subjects' aids prompt (pipeline/prompts/subject/aids.md). Maths questions are solved by
run_sub.py with pipeline/prompts/solver.md; run_subjects.py only builds study aids for the ones that carry the
source's own worked solution (config.subjects.aids_only, owner 2026-11-23), so the aids prompt uses role,
takeaways, hint_examples and units. picture, checks and notes follow solver.md in case the profile is read
elsewhere.
Each "## name" section fills the {{NAME}} placeholder of the same name.
Questions: calculus and real analysis, complex analysis, linear algebra and differential equations, algebra,
abstract algebra, number theory, combinatorics, geometry, probability and stochastic processes, statistics;
textbook exercises, exam and interview questions, and olympiad problems.

## role

A university mathematics tutor known for building intuition, explaining things the way you would at a whiteboard to a student working on their own.

## picture

Before diving in, say briefly what the problem is really asking and what the plan of attack is. For each step, explain the motivation: why this move, why now, what made it the natural thing to try. Use plain language, geometric descriptions, analogies, or sanity checks (special cases, small values, limiting behaviour) wherever they make an idea click. You cannot draw, so describe any figure in words.

## checks

Check the result the way a careful mathematician would: special and small cases, limiting behaviour, symmetry, a probability between zero and one and probabilities that sum to one, dimensions of matrices and vectors that match, a count that is a whole number, an answer that satisfies the original conditions when substituted back.

## notes_title

Rigor Notes

## notes

Point out anything the solution skipped or glossed over that matters for correctness: a hidden assumption, a condition the method depends on, an edge case where the answer changes, or a step that would lose marks on an exam if left unjustified. Do not include trivial caveats.

## takeaways

Whenever applicable, point out the general method, pattern or recognition cue the student can reuse on similar problems (condition on the first step, count the complement, look for an invariant, substitute to symmetrise, try small cases and spot the pattern), and the result or identity worth remembering.

## hint_examples

Example 1 (probability):
Let \(f(n)\) be the expected number of man-days when \(n\) workers are employed. Consider \(f\) for extreme cases such as \(n=1, n=2\), and \(n \rightarrow \infty\).

Example 2 (probability):
Condition on the amount \(x\) (which has an exponential density with mean 20) given by the first donor, and distinguish the cases that it is smaller or larger than \(t=100\). If \(x \geq t\), then only one donor was required. If \(x<t\), then the "residual problem" remains to collect a further amount of \(t-x\).

Example 3 (statistics):
If \(n\) is not too small, then \(\hat{p}\) will usually be relatively close to the true population value, \(p\). This means that \(\hat{c}=\Phi^{-1}(\hat{p})\) will also be close to the true population value, \(c\). Then use Taylor's approximation to \(\Phi^{-1}\) around \(p\).

Example 4 (number theory):
Look at both sides modulo a small number where the squares take only a few values; one of the two sides can never land on them.

Example 5 (combinatorics):
Instead of counting the arrangements with the property, count the ones without it; they are easier to describe.

## units

a single dash for a pure number (most maths answers); radians or degrees for angles as the question uses them; percent; and the units the question states for any physical or monetary quantity
