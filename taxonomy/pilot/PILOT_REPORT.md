# Pilot: Fluid Mechanics (White + Schaschke, 1,651 questions)

Nothing from the pilot is in the database yet. Check it in `review.html` (open it in a browser):
- filter by subtopic, confidence, type, flag or tag;
- tick "wrong" on anything misfiled and type the fix;
- press "Copy corrections" and paste the result back.

## What ran

- **Free pre-sort.** White's 11 chapters were recovered from book order and embeddings, and each question carried its chapter as a hint. In 715 of 736 questions the first in-text problem number agreed with the recovered chapter; the other 21 were cross-references.
- **Main pass.** Sonnet, 19 agents. Each question got its subtopic (from the 105-subtopic Fluid Mechanics tree), a confidence, a second choice, a `type`, technique tags (key and supporting), a task tag, and quality flags. Every question was read with its full solution. White's solutions are short (median about 1,000 characters).
- **Calibration.** The same 150 random questions were classified by Haiku and by Opus, with Opus as the reference.
- **Cost.** The main pass used about 2.7M tokens, roughly 1,650 per question.

## Results

| | |
|---|---|
| Fluid Mechanics | 1,642 after the tree adjustments (9 went to other subjects: 4 Thermodynamics, 4 Mechanics, 1 Calculus) |
| Wastebasket | 2 after the tree adjustments (torque converter, pneumatic conveying); 11 before |
| Confidence | 1,100 high (67%), 514 medium, 37 low |
| Type | 1,337 numerical, 177 proof, 137 explanation/reasoning (White has no multiple-choice items) |
| Subtopics used | all 107; the smallest hold 2-6 questions |
| Technique tag | 29% of questions |
| Task tag | 34% of questions |

## Accuracy (150-question sample, Opus as reference)

| | Same subtopic as Opus | Same branch | Same type |
|---|---|---|---|
| Sonnet | 94% | 96% | 94% |
| Haiku | 91% | 94% | 99% |

- **Sonnet's confidence is well calibrated.** High-confidence labels agreed with Opus 109 times in 110; medium ones 32 in 39.
- **Most disagreements were near-ties** between neighbouring subtopics (capillary viscometer: Viscometers or Laminar Pipe Flow). In 6 of the 9 Sonnet-Opus disagreements Opus was more apt; 2 were gaps in the tree.
- **Haiku agreed with Opus on 8 of those 9**, so a cheap Haiku second opinion catches most of Sonnet's slips.
- **Haiku is over-confident.** Its high-confidence labels were right 95% of the time.

## Tags

- **Technique tags are sparse and unstable on textbook questions.**
  - Only 29% of questions got one.
  - The three models agreed poorly: the average overlap between two models' tag sets was 0.3-0.5 on a 0-1 scale.
  - Only *Equilibrium of Forces and Moments* was consistent (10 of 11).
  - *Iterative Solution* was moderately consistent; *Conservation of Mass* was not.
  - The textbook tag study predicted this: most exercises apply one chapter's method.
- **Task tags are more useful and moderately consistent.** The most common were Derive a Relation (143), Read Tables or Charts (95), Design or Size (76), Sketch or Plot (74), Explain a Concept (49), Find the Optimum (31) and Point Finding (15). *Design or Size* and *Read Tables or Charts* need sharper definitions: models disagreed on them most.
- **Some tags just restate a subtopic.** *Method of Images* and *Graphical Solution* each landed in a single subtopic, so they add nothing within Fluid Mechanics. They stay only if other subjects use them.
- **This pilot could not test tags where they matter most:** olympiad, puzzle and proof sources.

## Data quality found

- **361 White questions refer to a figure that is not in the bank.** Each mentions "Fig. P2.33" or similar and has no embedded image, so a student or a PDF gets the question without its diagram.
  - Another 443 have their figure embedded.
  - The agents could not tell the two apart, so this flag is now computed by script rather than by the model.
- **107 questions have no solution:** 105 Schaschke and 2 White.
- **About 40 questions say "Repeat Prob. X"** and depend on data from another question.
- **A few question texts are broken:** e.g. 21580 never states the unknown, and 21616 is cut off.

## Tree adjustments (applied 2026-11-02)

- **Added *Density and Ideal-Gas State*** to the Fluid Properties branch. 9 White ch. 1 questions moved there from the wastebasket and Thermodynamics.
- **Widened *Dimensional Homogeneity*** to cover units and unit conversion. 2 questions moved there from the wastebasket.
- **Added *Flow Measurement Methods*** for dilution and tracer methods and calibration by mass balance. 2 Schaschke questions moved there; rotameters stay in Obstruction Flow Meters.
- **Widened *Finite-Difference Methods for Flow Equations*** to cover unsteady diffusion schemes.
- **Sharpened scope notes** on the frequent near-ties:
  - Viscometers vs Non-Newtonian Fluids;
  - Particle Settling vs Terminal Velocity;
  - Bernoulli vs Linear Momentum;
  - Isentropic Area Change vs Converging Nozzles.
- **Other moves:**
  - The blimp question (18663) went to Buoyancy.
  - The two stress-transformation questions (18724, 18725) went to Mechanics.
  - White's seven control-volume rocket problems went to Moving and Accelerating Control Volumes, as decided earlier.
- **Still in the wastebasket:** the torque converter (19978) and pneumatic conveying (21692).
- **Still in Thermodynamics:** 4 questions (18660, 18666, 19684, 19687). They are about processes, not fluid properties.

Questions citing a missing figure are not hidden. `../data_quality/missing_figures.csv` lists all 470 in the bank, 361 of them from White. Regenerate it with `../tools/missing_figures.py`.

## Recommendations for the full run

1. **Second opinion on uncertain labels.** Sonnet stays the main classifier. Haiku re-labels Sonnet's medium and low items (about a third), and Opus settles any disagreement. In the sample this would have fixed most of Sonnet's errors.
2. **Make cheap things scripted:** figure presence, empty solutions, and "Repeat Prob. X" detection.
3. **Tags by kind of source.**
   - Textbook sources: task tags plus a short list of stable technique tags.
   - Olympiad, puzzle and proof sources: a tag mini-pilot (about 200 questions, Sonnet vs Opus) before the full run, to sharpen definitions where tags matter.
4. **Solution excerpt.**
   - Textbook sources: the first 1,500 characters are enough for the subtopic.
   - Olympiad sources: 2,500 characters. The olympiad tag study found the decisive idea within the first ~2,300.
5. **Cost.** The other 19,660 questions are about 41M characters at those caps, so roughly 40M tokens on Sonnet: about 15 times this pilot. Reading full solutions everywhere would be about 75M.
