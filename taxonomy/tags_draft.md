# Tag vocabulary (draft)

Tags name what the topic tree cannot: the method that cracks a question, and the kind of task it
is. One tag gathers questions from many subtopics and subjects. This draft is built from three
open-tagging studies (284 questions read in full: 90 olympiad and analysis, 90 puzzle, probability,
quant and physics-puzzle, 104 textbook and exam) plus the standard problem-solving literature
(Engel, Zeitz, Larson, Pólya). The studies are in the session scratchpad (`tax/tags_T1.md`,
`tags_T2.md`, `tags_T3.md`).

## How the list is improved over a hand-written one

1. **Grounded in the bank.** After each study merged its own spelling variants, open tagging left
   about 240 distinct tags (93, 103 and 46). The list below keeps the ones that recurred or that
   the literature says will recur, and folds the rest in as aliases.
2. **Three kinds of metadata, kept apart.** Every study found taggers mixing them:
   - **Technique**: the move that does the work (Pigeonhole Principle, Conservation of Energy).
   - **Task**: what the question asks for (your own "Point Finding" is one). In the puzzle and
     probability study, task labels were more searchable than technique tags.
   - **Quality flags**: open problem, missing or mismatched solution, needs a figure or outside
     data. These are not tags; they go on a review list.
3. **Key versus supporting.** Each question gets 1-2 *key* techniques (the idea without which the
   solution collapses) and 0-3 *supporting* ones. Casework appeared 4 times as key and 10 times as
   supporting, Bounding 2 and 6. Filtering on key gives a clean practice set; filtering on any
   mention mostly returns questions where the technique is incidental.
4. **A definition and a decision rule for every tag**, so two taggers apply it the same way. The
   confusable pairs (Double Counting vs Counting Bound, Symmetry vs Exchangeability) get explicit
   rules.
5. **Pruned by measurement in the pilot**, not by taste:
   - floor: a tag projected under ~15 questions bank-wide merges into a neighbour or becomes an alias;
   - ceiling: a tag on more than ~8% of its subject is too broad and splits;
   - spread: a tag whose questions sit over 80% in one subtopic duplicates the tree and is dropped;
   - agreement: two taggers tag the same 150 questions, and tags they disagree on get rewritten
     or merged.
6. **"No tag" is allowed.** About a quarter of textbook exercises and many exam one-liners have
   no idea beyond their subtopic (plug-in formulas, factual recall). Forcing a weak tag pollutes
   the filter.
7. **An open slot.** A tagger may write `Proposed: <name>` when nothing fits. These are reviewed
   like the taxonomy wastebasket and either become tags or aliases.

Families are for browsing in the app only; tags are stored flat.

## Technique tags

### Proof methods
| Tag | Use when | Aliases |
|---|---|---|
| Induction | P(n) is proved from smaller cases and the step is the main work; includes strong induction | Strong Induction |
| Infinite Descent | a minimal solution or counterexample yields a smaller one | Minimal Counterexample |
| Proof by Contradiction | the contradiction carries the idea, not just the wrapper | |
| Extremal Principle | look at the largest, smallest, first or last object and use its extremality | |
| Explicit Construction | existence is shown by exhibiting the object | |
| Counterexample | one explicit example refutes a general claim or shows a property fails (added 2026-11-06) | Counterexample Construction |
| Bound and Construct | an optimum is found by proving a bound and exhibiting an example that attains it | |
| Small Cases First | small cases are computed to find the pattern that is then proved | Pattern Spotting |
| Working Backwards | reason from the target state or the final move | |
| Strengthen the Claim | a stronger or more general statement is easier to prove | Generalize the Target |
| Casework | the split into cases is the organizing idea (key only) | Exhaustive Case Analysis |

### Invariants, processes and games
| Tag | Use when | Aliases |
|---|---|---|
| Invariant | a quantity is unchanged by every allowed move | |
| Monovariant | a quantity moves one way only, proving termination or impossibility | Potential Function |
| Parity | an even/odd count or position decides the question | |
| Coloring Argument | a coloring of cells or objects exposes an invariant or obstruction | Chessboard Coloring |
| Periodicity and Cycles | iteration falls into a cycle that is found and used | Orbit Analysis, Iteration |
| Pairing | objects, terms, divisors or moves are grouped in pairs | Pairing Strategy |
| Backward Induction | sequential games or decisions solved from the last stage | |
| Strategy Stealing | a winning strategy for the second player is turned against itself | |
| Greedy and Exchange Argument | a greedy choice is shown optimal by swapping into any optimum | Greedy Algorithm |
| Divide and Conquer | halve the search space or split into subproblems | Binary Search |
| Information-Theoretic Bound | outcomes per query vs possibilities bound the number of queries | Weighing Bound |

### Counting
| Tag | Use when | Aliases |
|---|---|---|
| Bijection | a count is found by matching with an easier set | |
| Double Counting | one set is counted in two ways to get an identity or equation | Counting in Two Ways |
| Counting Bound | the size of a set is bounded by counting what it must contain | Counting Argument |
| Complementary Counting | count or compute the complement and subtract (includes 1 - P) | Complementary Probability |
| Inclusion-Exclusion | overlapping conditions are corrected with alternating sums | |
| Stars and Bars | distributions of identical items counted as bar arrangements | |
| Pigeonhole Principle | more objects than boxes forces a shared box | Box Principle |
| Recursion | a recurrence is set up for a count, probability or value | Recurrence Reduction |
| Generating Functions | a sequence or distribution is encoded as a power series | PGF, MGF |
| Reflection Principle | paths that touch a line are reflected to count them | Ballot Problem, Catalan Counting |
| Averaging Argument | some element must be at least (or at most) the average | |
| Probabilistic Method | existence shown by a random choice with positive probability or a good expectation | |

### Number-theoretic moves
| Tag | Use when | Aliases |
|---|---|---|
| Modular Arithmetic | reduction modulo a well-chosen number decides the question | Residue Classes |
| Divisibility Argument | prime or gcd divisibility of factors does the work | |
| p-adic Valuation | the exact power of a prime is tracked | Lifting the Exponent, Legendre's Formula |
| Fermat-Euler and Orders | Fermat's little theorem, Euler's theorem or multiplicative order | |
| Chinese Remainder Theorem | congruences to coprime moduli are combined or built | |
| Bezout's Identity | the gcd is written as a linear combination | |
| Base Representation | digits or binary expansions carry the structure | Binary Encoding |
| Vieta Jumping | a solution of a quadratic Diophantine equation is jumped to a smaller one | |
| Size Estimate | a crude growth bound cuts the search to finitely many cases | Bounding by Size |
| Quadratic Residues | squares modulo a prime, Euler's criterion, the Legendre symbol or quadratic reciprocity decide the question (added 2026-11-12) | Legendre Symbol, Quadratic Reciprocity |

### Algebraic moves
| Tag | Use when | Aliases |
|---|---|---|
| Substitution | renaming an expression simplifies the problem (algebraic or trigonometric) | Trig Substitution |
| Factorization | factoring an expression is the step that opens the problem | Difference of Squares |
| Telescoping | consecutive terms cancel in a sum or product | |
| Vieta's Formulas | sums and products of roots replace the roots | |
| Polynomial Root Argument | count roots, the factor theorem, or "too many roots means zero" | Comparing Coefficients |
| Special Values | plugging chosen values pins down a function or identity | |
| Complex Numbers Method | complex numbers or roots of unity used outside complex analysis | Roots of Unity Filter |
| Sum of Squares | write as a sum of squares to prove non-negativity or extremum | Completing the Square |

### Inequalities and estimation
| Tag | Use when | Aliases |
|---|---|---|
| AM-GM Inequality | arithmetic-geometric mean bound | |
| Cauchy-Schwarz Inequality | Cauchy-Schwarz in any form (Engel form, Titu, integrals, vectors) | Titu's Lemma |
| Jensen and Convexity | convexity or Jensen's inequality bounds or locates an extremum | Karamata |
| Rearrangement Inequality | similarly ordered sequences maximize the sum of products | Chebyshev's Sum |
| Tangent Line Trick | bound each term by its tangent line at the equality point | |
| Smoothing | move variables toward each other while the expression improves | Mixing Variables |
| Symmetric Extremum | the optimum is guessed at a symmetric point and then proved | Equality Case |
| Squeeze | a quantity is trapped between two bounds with a common limit | Sandwich |

### Analysis tools
| Tag | Use when | Aliases |
|---|---|---|
| Mean Value Theorem as a Tool | MVT, Rolle or Cauchy MVT used outside their own subtopic | |
| Intermediate Value Argument | a sign change or continuity forces a value to be attained | |
| Taylor Expansion | expansion with remainder drives a limit, bound or approximation | Asymptotic Expansion |
| Auxiliary Function | a helper function is built so a theorem applies to it | |
| Monotonicity Argument | monotonicity of a function or sequence settles a comparison or root count | |
| Interchange of Limits | sums, integrals, limits or derivatives swapped with justification | Fubini, Differentiation under the Integral |
| Riemann Sum | a limit of sums recognized as an integral | |
| Compactness Argument | convergent subsequences or finite subcovers give the result | Bolzano-Weierstrass |
| Fixed Point Argument | a contraction or fixed point theorem gives existence or a limit | Picard Iteration, Banach |
| Linearization | expand to first order about a known state (small angles, small perturbations, delta method) | Small Perturbation |

### Probability moves
| Tag | Use when | Aliases |
|---|---|---|
| Linearity of Expectation | expectation of a sum split into terms, usually via indicators | Indicator Variables |
| Conditioning on First Step | condition on the first move to get equations for probabilities or expectations | First-Step Analysis |
| Conditioning on a Variable | law of total probability or expectation over a well-chosen variable | Law of Total Expectation |
| Exchangeability | all positions or orderings are equally likely by symmetry | |
| Tail-Sum Formula | E[X] as a sum or integral of tail probabilities | |
| Memorylessness | the exponential or geometric memoryless property is the key | |
| Coupling | two processes are built on one probability space to compare them | Independent Copy Trick |
| Martingale and Optional Stopping | a martingale and a stopping theorem (or Wald) give the answer | Wald's Identity |
| Change of Measure | switch to an equivalent measure or numeraire | Girsanov, Change of Numeraire |

### Statistics moves
| Tag | Use when | Aliases |
|---|---|---|
| Pivotal Quantity | a function of the data and the parameter with a known distribution is inverted into an interval or test (added 2026-11-06) | Pivot |
| Factorization Criterion | the joint density is split as g(T; theta) h(x) to read off a sufficient statistic (added 2026-11-06) | Fisher-Neyman Factorization |

### Finance and economics moves
| Tag | Use when | Aliases |
|---|---|---|
| No-Arbitrage Argument | a price or bound follows because otherwise there is a riskless profit | |
| Replication and Hedging | a payoff is reproduced by a portfolio of other instruments | Static Replication, Delta Hedging |
| Indifference Condition | an equilibrium is found where an agent is indifferent between choices | |

### Physical and engineering reasoning
| Tag | Use when | Aliases |
|---|---|---|
| Conservation of Energy | an energy balance (mechanical, thermal, electrical) is the governing step | First Law Balance |
| Conservation of Momentum | linear momentum balance (collisions, jets, control volumes) | |
| Conservation of Angular Momentum | angular momentum balance about a well-chosen point | |
| Conservation of Mass | continuity: flow in equals flow out plus accumulation | Bookkeeping |
| Equilibrium of Forces and Moments | force and moment sums are zero | Force Balance |
| Reference Frame Change | moving to a center-of-mass, rotating or co-moving frame simplifies the problem | |
| Dimensional Analysis | the answer's form follows from units alone | |
| Scaling Argument | power-law or ratio reasoning between two cases | Similarity |
| Ratio Method | compute at a known state and scale, unknown constants cancel | Eliminate Unknown Constants |
| Order-of-Magnitude Estimate | a Fermi estimate gives the answer | |
| Limiting Cases | extreme or special cases solve or check the problem | |
| Infinitesimal Element | cut into thin elements, write the local law, integrate | Slice Method |
| Superposition | a linear system's response is the sum of simpler responses | |
| Equivalent Network | a system is reduced to series and parallel resistances or an analogous circuit | Thermal Resistance Network, Thevenin |
| Energy Method | virtual work, minimum potential energy, Castigliano or a Lagrangian | Variational Principle |
| Method of Images | an image source replaces a boundary | |
| Iterative Solution | guess and update until convergence (Newton, friction factor, trial and error) | |
| Graphical Solution | the answer is read from an intersection, chart or load line | Load Line |
| Harmonic Balance | a truncated Fourier-series ansatz for a periodic solution, coefficients fixed by the equation of motion (added 2026-11-06) | |

### Problem transformation
| Tag | Use when | Aliases |
|---|---|---|
| Symmetry Argument | geometric or structural symmetry cancels terms or reduces the problem | |
| Graph Model | the problem is recast as a graph and solved with graph facts | |
| Coordinate Method | coordinates or vectors turn a geometric or physical problem into algebra | Coordinate Bash, Vector Method |
| Reflection Unfolding | a path is reflected or a solid unfolded to straighten it | Mirror Trick |
| Angle Chasing | angle relations in a figure carry the solution | |
| Similar Triangles | similarity ratios carry the solution outside a similarity subtopic | |
| Power of a Point | power of a point or radical axes do the work | Radical Axis |
| Inversion | a circle inversion turns circles, tangencies and lines into a simpler configuration (added 2026-11-12) | Circle Inversion |
| Projective Methods | cross-ratios, harmonic divisions, poles and polars or projective maps carry the argument (added 2026-11-12) | Harmonic Division, Cross-Ratio, Poles and Polars |
| Linear Algebra Method | a combinatorial or number-theoretic problem is solved with vectors, rank or dimension over a field (added 2026-11-12) | Dimension Argument |

## Task tags (what the question asks)

At most one per question; optional.

| Task | Use when |
|---|---|
| Point Finding | find the points where a quantity is extreme or a condition holds (your tag) |
| Find the Optimum | find the maximum or minimum value or the best design |
| Prove Existence | show something exists |
| Prove Impossibility | show something cannot happen or has no solution |
| Prove an Identity | establish an equality for all cases |
| Prove an Inequality | establish an inequality for all cases |
| Find All Solutions | determine every number, function or configuration that works |
| Count Configurations | how many objects have the property |
| Expected Waiting Time | expected time or steps until a pattern, threshold or event |
| Expected Count | expected number of fixed points, runs, loops or events |
| Fair Value of a Game | the price or value of a bet, game or contract |
| Optimal Strategy | best play, stopping rule or betting rule |
| Who Wins | decide which player wins a combinatorial game |
| Minimum Number of Moves | fewest moves, weighings or queries |
| Last Digits and Remainders | final digits, remainders or position in a periodic pattern |
| Find the Locus | describe the set of points satisfying a condition |
| Limit or Asymptotics | the limiting value or growth rate |
| Evaluate a Sum or Integral | closed form of a sum, product or integral |
| Tiling and Covering | whether or how a region can be tiled or covered |
| Spot the Flaw | find the error in a paradox or seemingly valid argument |
| Estimate | an order-of-magnitude answer with no exact data |
| Design or Size | choose dimensions or ratings to meet a specification |
| Performance and Efficiency | rate an existing machine, plant or system |
| Compare Alternatives | evaluate two or more options and decide |
| Explain a Concept | qualitative answer, no calculation |
| Derive a Relation | derive a formula or governing equation |
| Sketch or Plot | draw a graph, diagram or curve |
| Read Tables or Charts | the answer needs property tables, steam tables or a chart |
| No Prerequisites | solvable with school arithmetic and logic alone |

"No Prerequisites" carries the idea behind your deleted template "Problem Solving (No additional
knowledge)", and it now works across every source rather than a fixed source list.

## Quality flags (review list, not tags)

- Open problem: the "solution" explains that no proof is known.
- Missing or truncated solution.
- Question and solution do not match.
- Needs a figure, table or outside data that the question does not contain.
- Duplicate of another question.

The studies already found some: 14675 (question and solution do not match), 13838 and 13843 (open
problems), 10041, 15996 and 9522 (truncated or empty solutions).

## Storage (decided 2026-11-02)

- `question_tags.role` (migration 007) is `key` or `supporting` for technique tags and `task` for
  task tags. "Point Finding" is stored as `task`. Existing filters still match every role; a filter
  toggle for supporting tags comes with the tagging run.
- The classification pass also fills the empty `type` column (objective / numerical / proof /
  explanation) for the 18,907 questions that lack it.
