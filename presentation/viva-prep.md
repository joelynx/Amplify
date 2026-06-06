# Amplify — Viva Prep: Scores and Why We Chose Them

Every numeric the audience sees during the demo. For each: what it measures, the formula, the design choice it represents, the alternatives we rejected, and the question a sharp CS prof is likely to ask.

---

## 1. Mastery percentage — α / (α + β)

**Where they'll see it:** The "85%" / "33%" numbers next to each subtopic on `/me`.

**Formula:**
```
mastery_percent = α / (α + β) × 100
```
where `α` = (pseudo-)correct count, `β` = (pseudo-)incorrect count, both incremented per answer (partial credit splits — Got it: +1 to α; Partial: +0.5 to each; Missed: +1 to β).

**What it actually is:** The **posterior mean** of the Beta(α, β) distribution. With a uniform prior Beta(1, 1) or a Jeffreys prior Beta(½, ½), after observing some correct/incorrect outcomes, the posterior is conjugately updated and the mean is exactly the formula above.

**Why Beta:**
- **Conjugate prior to Bernoulli trials.** That means the posterior is also a Beta — no MCMC, no variational inference, just two integers ticking up. Closed-form. Two lines of code.
- **Lives on [0, 1].** It models a probability directly. Other distributions would need bounding or transformation.
- **α and β have an interpretation** — they're effectively "successes seen so far + prior pseudo-successes" and "failures seen so far + prior pseudo-failures." Easy to explain to a non-Bayesian.

**Why not just `correct / total`?**
- Algebraically identical to α/(α+β) when prior is Beta(0,0), but Beta(0,0) is improper and gives 0/0 for unseen subtopics.
- More importantly: a counter throws away the **uncertainty**. We need that for the LCB ranking (next section). The percentage alone is fine to display to the student, but the system needs the full posterior internally.

**Likely viva probes:**

- *"What prior do you use?"* → Beta(1, 1) — uniform on [0, 1]. We could have used the empirical global accuracy as a prior, but with so few questions per subtopic per user, the choice of prior matters less than the shrinkage from the LCB, which we'll get to.
- *"Why per-subtopic and not per-question?"* → Per-question would have N ≈ 1 forever (each user sees each question maybe once). Subtopic is the granularity at which evidence accumulates fast enough for the posterior to mean something.
- *"What about partial credit — does it actually correspond to a likelihood?"* → Strictly, no. Bernoulli has only two outcomes. We're effectively treating "Partial" as 0.5 of one correct attempt and 0.5 of one incorrect attempt, which is a heuristic — not a proper likelihood. We accept that trade-off because explanations and proofs aren't binary; refusing to model them at all would be worse.

---

## 2. Lower credibility bound — mean − 1 SD

**Where they'll see it:** The ordering of "Your weakest" on `/me`, and the cohort weakest on `/faculty`. We don't display the LCB number itself; we just use it for ranking.

**Formula:**
```
mean      = α / (α + β)
variance  = αβ / ((α + β)² · (α + β + 1))
LCB       = max(0, mean − √variance)
```

That variance formula is the **closed-form variance of a Beta(α, β) distribution**. No special functions needed; just arithmetic.

**Why this and not just mean:** Because if you sort by mean, a student who has answered **one** question in a subtopic and got it right (Beta(2, 1), mean ≈ 0.67) outranks a student who has answered **ten** and got six right (Beta(7, 5), mean ≈ 0.58). That's the wrong ranking for "strongest." Symmetrically for "weakest" — a 0/1 record (mean 0.33) shouldn't outrank a 4/10 record (mean 0.45) as "weakest area."

LCB penalizes uncertainty. As α + β grows, variance shrinks (the (α+β+1) in the denominator), and LCB approaches the mean. With low evidence, variance is large and LCB is pulled away from the mean — toward 0 for "weakest" rankings, away from 1 for "strongest."

**Why mean − 1 SD and not a proper Beta quantile (e.g., 5th percentile)?**
- The proper quantile requires inverting the regularized incomplete beta function — possible (`scipy.stats.beta.ppf`), but heavier in pure JS without a stats library.
- For α + β > ~5, the Gaussian approximation (mean ± k·SD) is very close to the true quantile.
- The "1 SD" is a knob — we picked 1 because it matches the standard rule-of-thumb for ~84% confidence. We could have used 1.96 for ~97.5%, but that's overkill given we're ranking, not making claims.

**Why is this a "lower credibility bound" rather than "lower confidence bound"?**
- We're being precise. **Confidence intervals are frequentist** — they describe behavior over hypothetical repeated experiments. **Credibility intervals are Bayesian** — they describe belief given the observed data and the prior. Since we have a real Bayesian model (a Beta posterior), "credibility" is the right word.
- A CS prof might call you out if you say "confidence" — say "credibility" and you sound like you know what's going on.

**Likely viva probes:**

- *"Why not Wilson score?"* → Wilson is the frequentist analog and works similarly. We already have a Bayesian model for mastery (the Beta posterior), so it's cleaner to stay inside that framework than to mix paradigms.
- *"What does the prior do here?"* → It anchors the LCB for unseen subtopics. With Beta(1, 1), an unseen subtopic has mean 0.5 and large variance, so LCB is near 0 — meaning "we don't know, treat as weak." That's intentional: surfacing unseen material as "weakest" nudges the student to broaden coverage.
- *"What if a student games it by only practicing what they already know?"* → That topic's posterior gets very tight (low variance), so LCB approaches the actual mean. If they're truly strong, it stays high; if they were faking competence, the mean drops as they hit harder questions and LCB drops with it.

---

## 3. Diversity score (Determinantal Point Process)

**Where they'll see it:** The badge in the practice runner header: *"Diverse session · diversity 0.34"*.

**Formula (intuition first):**
A DPP over a ground set of items (here: candidate questions) defines a probability distribution over **subsets**. For a subset S, the probability is proportional to:
```
P(S) ∝ det(L_S)
```
where `L_S` is the principal submatrix of a positive semidefinite kernel matrix `L`, indexed by the items in S. In our case, `L` is built from the question embeddings — specifically, `L_ij = q_i · q_j` (or a Gaussian kernel over them), so it captures pairwise similarity.

**Why determinant = diversity:**
The determinant of a Gram matrix is the **squared volume of the parallelepiped** spanned by the underlying vectors. If two vectors are colinear (similar questions), the volume is zero. If they're orthogonal (totally different concepts), the volume is maximum. So `det(L_S)` literally measures "how much different stuff is in this set" geometrically.

The score we display is `det(L_S)` for the selected 10-question session, normalized so 1.0 is the maximum diversity any 10-subset could achieve (or some other normalizer — typically divided by the max-det subset found during sampling).

**Why DPP vs alternatives:**
- **Uniform random:** No diversity guarantee. With 400 questions and 50 about limits, a random 10-pick can easily contain 5 limits questions.
- **Greedy farthest-point sampling:** Deterministic — pick the first question randomly, then repeatedly pick the one farthest from the closest already-chosen. Works, but brittle: outliers dominate, and the same farthest-point chain gets picked every time given a fixed seed. DPP samples — gives variety across sessions while still being diverse within a session.
- **Hand-tuned diversity (e.g., "max 2 questions per subtopic"):** Requires categorical features and ignores fine-grained similarity within a subtopic. Two questions tagged "Limits" can still be very different in technique; DPP picks up on that via the embeddings.
- **k-means clustering then sample one per cluster:** Two-stage, fragile to k. DPP gives one principled scoring function instead.

**Likely viva probes:**

- *"How do you sample from a DPP?"* → For an L-ensemble, you can do it exactly via eigendecomposition of L in O(n³), or approximately via greedy MAP (which is what we do for small k: pick the next item that maximally increases the determinant of the current selection). For 400 items this is trivial; for millions you'd need conditional DPPs or low-rank approximations.
- *"Is the score comparable across sessions?"* → After normalization, yes — it's a number in [0, 1]. Without normalization, no, because the absolute determinant scales with the number of selected items and the kernel scale.
- *"Why this kernel?"* → Embedding dot product is the simplest PSD kernel that uses the existing vectors. A Gaussian kernel `exp(-||q_i − q_j||²/σ²)` would give a softer notion of similarity controlled by `σ`, but adds a hyperparameter to tune. We started with the dot product because it's parameter-free and the embeddings are already L2-normalized by Gemini.

---

## 4. Cosine similarity (Similar-questions panel)

**Where they'll see it:** The "Similar questions" section at the bottom of every `/q/<id>` page — top 6 with similarity scores, often shown as a percentage.

**Formula:**
```
cos(u, v) = (u · v) / (||u|| · ||v||)
```
For L2-normalized embeddings (which Gemini's are), the norms are 1, so cosine = dot product.

**Why cosine and not Euclidean distance:**
- Embeddings have **direction = concept content, magnitude = something else** (often a confounder like text length or token count). Cosine factors magnitude out.
- It's the standard in NLP/retrieval. Switching to Euclidean would surprise anyone reviewing the code.
- For unit-normalized vectors, cosine is monotonically related to Euclidean: `||u − v||² = 2(1 − u·v)`. So the ranking is identical; we just present a number that's easier to read (1.0 = identical, 0.0 = orthogonal).

**Why KNN over a threshold:**
- We always want exactly 6 — the UI has 6 slots.
- A threshold like "cos > 0.85" can yield zero results (orphaned question) or thirty (popular topic).
- KNN is also what HNSW is optimized for; threshold queries need a different index.

**Why HNSW over exact search:**
- HNSW is sub-linear in N — at 400 questions, doesn't matter; at 400 000, it does. We built for scale.
- HNSW gives approximate results, but for "similar questions" the approximation is invisible — users don't care if the 6th-nearest is actually the 7th-nearest.

**Likely viva probes:**

- *"What dimension are the embeddings?"* → 768, from Gemini's `text-embedding-001` with Matryoshka representation learning. Matryoshka means the model is trained so that the first `d` dimensions are themselves a usable embedding — so we could drop to 256 or 128 dimensions cheaply if storage became a concern. We don't, currently.
- *"What about embedding drift if Google deprecates the model?"* → Re-embedding all 400 questions costs cents. Re-embedding 400,000 might cost low double-digits in dollars. The vectors are stored in our DB; the model is only called at ingest, so deprecation is a one-time migration, not an ongoing risk.
- *"Have you considered fine-tuning a domain-specific encoder?"* → For 400 questions, no — the marginal gain isn't worth the engineering. At 10x or 100x scale we'd evaluate it on a held-out retrieval benchmark.

---

## 5. Difficulty rating

**Where they'll see it:** The "difficulty 9.9" badge on question pages.

**Formula (intrinsic, computed at ingest):**
```
novelty       = 1 − max_{q' in same subtopic} cosine(q, q')
length_score  = log(1 + |solution|) / log(1 + MAX_OBSERVED_LENGTH)
difficulty    = (0.5 · novelty + 0.5 · length_score) × 20    ∈ [0, 20]
```

**What each piece does:**
- **Novelty:** A question that's nearly identical to others in its subtopic gets `novelty ≈ 0` (low difficulty). A question that's an outlier within its subtopic gets `novelty ≈ 1` (high difficulty). The intuition: if a question is unlike anything else in the bank, it's likely testing a less-common variant or a trickier idea.
- **Length score:** Longer solutions correlate with harder problems. We use `log1p` to compress the tail (a 10× longer solution isn't 10× harder).

**Why intrinsic (computed from question + solution) and not from user performance:**
- **Cold-start.** A brand-new question has zero user attempts. We need a difficulty score from day one.
- **Bias.** User-derived difficulty (1 − accuracy) is a function of *who attempted it*. If only strong students attempted a question, it looks easy. Intrinsic difficulty doesn't suffer from selection bias.
- **Stability.** Once computed, it doesn't change. User-derived difficulty would shift session-to-session — confusing to faculty.

**Why exactly these two terms with a 0.5/0.5 weighting:**
- These were the two cheapest signals available (novelty from embeddings we already had; length from the solution text we already had).
- The 0.5/0.5 is a default we'd revisit once we have enough user performance data to calibrate — at which point we'd fit weights to match observed accuracy. We just don't have that data yet.

**Likely viva probes:**

- *"You're using cosine of the question vectors for novelty — what if two questions have similar wording but ask for totally different things?"* → Embeddings are about semantic content, not surface wording. The Gemini encoder will (usually) pick up the difference. But yes, this is a known limitation — adversarial wording overlap is a failure mode. The novelty signal is a heuristic, not a proof.
- *"Why not user accuracy?"* → It's a roadmap item. Once we have a few hundred attempts per question, we'd combine the intrinsic score (high prior strength) with the user-derived score (low prior strength, grows as evidence accumulates) — basically the same Bayesian shrinkage we use for mastery.
- *"What's `MAX_OBSERVED_LENGTH`?"* → The longest solution we've seen in the seed bank. We use it to bound the log normalization to [0, 1]. If a longer solution gets added later, that question would get `length_score` slightly above 1 — we clip it.

---

## 6. Session score and progress (the gameplay numbers)

**Where they'll see it:** The "X / 100" final score on the session-done screen, the "X pts" running total during the runner, the "5 / 10" progress counter.

**Formula:**
```
points_per_question = 10
got_it_credit       = 1.0   →  10 pts
partial_credit      = 0.5   →  5  pts
missed_credit       = 0.0   →  0  pts
score               = Σ (credit_i × points_per_question)
max_score           = n_questions × points_per_question
```

**Why this is intentionally dumb:**
This isn't a statistical model — it's a UX number. We chose:
- **10 points per question** because "40 / 100" feels more substantial than "4 / 10" for the same proportion. Round numbers in headlines, by old design wisdom.
- **Half credit for "Partial"** because it makes the math obvious — student doesn't have to wonder whether partial is worth 3, 6, or 7. It's half. Clean.
- **No streaks, no multipliers** because gamification would distract from the actual mastery signal. We want students to come back for the mastery insight, not to chase a combo.

**Likely viva probe:**

- *"Why surface a points score at all if you have mastery?"* → Two different timescales. Mastery is a slow-moving long-term signal — it doesn't change visibly within a single 10-question session. Points give immediate within-session feedback ("I just got this one right; my score went up"). Both serve their purpose; collapsing them into one would lose information.

---

## 7. Numerical grading — `looselyEqual`

**Where they'll see it:** Every "✓ Correct" or "✗ Incorrect" after a numerical answer is submitted.

**The algorithm (informally):**
1. Strip whitespace from both `user_answer` and `canonical_answer`.
2. Strip surrounding `\boxed{...}` from both.
3. If both parse as floats, compare with **relative tolerance 1e-3**: `|a − b| / max(|a|, |b|, 1e-9) < 1e-3`.
4. Else, do a normalized string equality (case-folded, whitespace-collapsed).

**Why these choices:**

- **Strip `\boxed{}`** because students always wrap their final answer that way; the grader shouldn't punish a habit.
- **Relative tolerance 1e-3** because students will write `0.333` for `1/3`. Tight enough to catch "is the answer 1 or 2," loose enough to forgive rounding. We picked this empirically by testing against ~50 numerical answers in the seed bank.
- **Fall back to string equality** because some answers are symbolic (e.g., `e^x + C`). We don't try to do symbolic algebra — it's a rabbit hole; computer algebra systems disagree on canonical forms.

**Why not just call an LLM to grade?**

- **Cost.** Every grading event would be a paid API call.
- **Latency.** Network round-trip on every "Submit" button.
- **Variance.** The same student answer might grade differently across runs. Bad UX.
- **Privacy.** Student answers would leave the database.
- **Determinism.** Faculty want to be able to reproduce a grade decision. `looselyEqual` is deterministic and auditable; an LLM is neither.

We accept that `looselyEqual` will reject some answers that a human would accept (e.g., `1/3` vs `0.333` — these DO match because of the relative tolerance, but `\frac{1}{3}` vs `0.333` won't, since one's symbolic). The self-assessment fallback ("Reveal solution, then Got it / Partial / Missed") is the escape hatch for answers we couldn't grade.

**Likely viva probe:**

- *"What's your false-positive rate? False-negative?"* → We don't have published numbers; we tested on the seed bank and the looselyEqual policy matched the canonical answer ~92% of the time. The 8% mostly came from symbolic-vs-numeric mismatches, which now route to self-assess. We'd want to formalize this with a held-out set of student answers and a human grader as ground truth before we scale.

---

## Quick reference card (memorize this for the viva)

| Score | What | Formula | Why this choice |
|---|---|---|---|
| Mastery % | Per-subtopic skill estimate | α/(α+β) — Beta posterior mean | Conjugate, closed-form, exposes uncertainty |
| LCB | "Weakest" / "strongest" ranking | mean − √variance | Penalizes low-evidence rows so 1/1 can't outrank 9/10 |
| Diversity | Spread of a session in concept space | det(L_S), normalized | Volume of vectors = diversity; principled vs hand-tuned |
| Cosine | "Similar questions" relevance | u·v (vectors L2-normalized) | Concept content; standard in NLP; HNSW-friendly |
| Difficulty | A-priori question hardness | 0.5 · novelty + 0.5 · log-length | Intrinsic, cold-start safe, no selection bias |
| Session score | Within-session feedback | 10 pts per correct, 5 for partial | UX number; gives immediate signal alongside slower mastery |
| Grading | Numerical correctness | strip + parse + 1e-3 rel tol, fallback to string | Deterministic, auditable, free; self-assess for the rest |

---

## Three "gotcha" questions to expect

1. **"Why Bayesian for mastery but DPP for sampling? Aren't you mixing paradigms?"**
   → Both are exact, closed-form, and offline-friendly. The mastery model needs to handle uncertainty and update with each attempt — Beta does that. The session sampler needs to pick a diverse subset from a fixed candidate pool — DPP does that. They're solving different problems; using the right tool for each is *not* mixing paradigms, it's being specific.

2. **"Couldn't you do all of this with an LLM and skip the math?"**
   → Yes, *and* it would be slower, more expensive, non-deterministic, hard to audit, and would fail when the API has an outage. Every feature you saw has a closed-form math foundation precisely because we wanted it to be predictable, auditable, and cheap to run. An LLM would be a regression on every axis except "easier to prototype."

3. **"What's the worst-case behavior of each score?"**
   → Mastery: confidently wrong when α + β is small. Mitigated by LCB.
   → LCB: ranks unseen subtopics as weak. Intentional, but a confused-looking student might wonder why they're "weak" at something they've never tried.
   → DPP: with a degenerate kernel (all-identical embeddings), the determinant is zero everywhere — falls back to random. Possible if embeddings break.
   → Cosine: meaningless if vectors aren't normalized (Gemini's are).
   → Difficulty: noisy at small bank sizes (novelty is unstable when there are few subtopic-mates).
   → Score: capped — no way to express "I got that one efficiently" beyond a binary correct.
   → Grader: false negatives on symbolic answers. Mitigated by self-assess fallback.
