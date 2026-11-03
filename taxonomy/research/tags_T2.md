# Tag vocabulary study, sample T2 (90 questions, puzzle / probability / quant-interview / physics-puzzle sources)

## Step 1: open tagging, one line per question

(Tags are as first written, before merging. Where a question has no archetype the field is "-". Questions 10041 (Stein), 15996 (champagne bubbles) and 9522 (covariance table) had truncated or empty solutions; their tags are low confidence. 13838 (Collatz) and 13843 (edge unfolding) are open problems whose "solutions" explain why no proof exists.)

```
[13892] key: Pairing Argument, Two-Colouring | uses: Extremal Principle, Sorting | archetype: choose half the items so the team wins in every category
[14139] key: Injective Labelling, Density of Rationals | uses: Connectedness Argument | archetype: prove a family of disjoint objects is countable
[14147] key: Reformulate as Game, Modular Residue Construction | uses: Induction, Monovariant | archetype: smallest starting set that infects the whole grid
[14013] key: Wald's Identity, Linearity of Expectation | uses: Dominant Case Plus Correction, Normal Approximation | archetype: expected length of a race to N points
[14027] key: Tail-Sum Formula, Symmetry | uses: Generalise the Target, Conditioning on First Step, Simplex Volume | archetype: expected number of uniform draws until the sum passes 1
[14032] key: Recursive Construction, Extremal Principle | uses: Reformulate the Condition, Symmetry | archetype: construct a word with a forbidden-pattern property
[14108] key: Indifference Condition, Threshold Strategy | uses: Guess Strategy Shape, Expected Value by Region | archetype: value and equilibrium of a bluffing game
[13838] key: Pigeonhole Principle | uses: Case Split Mod n | archetype: does an iterated integer map always reach a cycle
[13738] key: Compare Consecutive Cases, Partial Fractions | uses: Induction, Bijection, GCD Identity | archetype: prove a sum is constant in n
[13744] key: Linearity of Expectation, Optimise Over Patterns | uses: Independence, Enumerate Candidates | archetype: seating order that maximises expected number of unlucky diners
[13791] key: Counterexample Search | uses: - | archetype: what is forced by a walk that returns to its start (North Pole puzzle)
[13843] key: Spanning Tree, Topological Argument | uses: Angular Defect | archetype: unfold a polyhedron into a flat net
[14158] key: Linearity of Expectation, Indicator Variables | uses: Sequential Process Decomposition | archetype: expected number of loops from random pairing
[14157] key: Maximise Number of Chances | uses: Construction | archetype: choose the best starting state to maximise winning chances
[14189] key: Exhaustive Case Analysis | uses: Symmetry | archetype: classify point configurations with few distinct distances
[13718] key: Double Counting | uses: Complementary Counting | archetype: number of diagonals of a polygon
[13685] key: Conservation Law | uses: Global Accounting, Cross-Check Two Ways | archetype: total amount consumed in a repeated dilution
[13643] key: Bijection, Upper Bound Plus Construction | uses: General Position | archetype: maximum number of triangles from n lines
[13669] key: Order-of-Magnitude Estimate, Exponential Growth | uses: Compare Growth Rates, Feasibility Inequality | archetype: how many times can paper be folded
[13659] key: Information-Theoretic Bound, Base Representation | uses: Greedy Algorithm, Lower Bound Plus Construction | archetype: fewest weights to weigh every value
[14331] key: Periodicity | uses: Modular Arithmetic | archetype: position after N steps of a back-and-forth pattern
[14444] key: Invariant, Base Representation | uses: Recursion | archetype: order-independent redistribution process
[14416] key: Area Counting, Recursive Construction | uses: Case Split Mod n | archetype: for which n can a region be tiled
[14369] key: Potential Function, Lower Bound Plus Construction | uses: Parity | archetype: minimum number of moves
[14355] key: Binary Search | uses: Invariant | archetype: find a hidden item by repeated three-way questions
[14289] key: Parity, Infinite Descent | uses: Invariance Under Transformation, Normalisation | archetype: show that all numbers are equal
[14233] key: Bijection | uses: Complementary Counting, Edge Case Check | archetype: count numbers whose digits increase
[14253] key: Symmetry, AM-GM Inequality | uses: Jensen's Inequality, Smoothing | archetype: maximise a symmetric expression under a constraint
[14324] key: Spectral Method | uses: Trace Identity, Divisibility Argument | archetype: possible parameters of a regular graph with given girth
[12672] key: Pigeonhole Principle | uses: Proof by Contradiction | archetype: prove every piece attacks another
[12650] key: Divisibility Argument | uses: Contradiction | archetype: prove a product is not divisible by n
[12667] key: Extremal Principle, Contradiction | uses: - | archetype: prove a farthest-city route returns home
[12689] key: Counting Argument | uses: Extremal Principle | archetype: maximum number of distinct problems
[12869] key: Multiplication Principle | uses: Symmetry | archetype: count arrangements with constraints
[12896] key: Backward Induction, Induction on n | uses: Small Cases First | archetype: rational players eating or not (tigers and sheep)
[12789] key: Tail-Sum Formula | uses: Independence, Continuous Analogue Check | archetype: expected minimum of several dice
[12811] key: Complementary Probability, Continue Past Stopping Time | uses: Binomial Counting | archetype: probability a late event happens under a stopping rule
[12883] key: Double Counting, Add the Equations | uses: Complementary Counting | archetype: find the total from the counts of who is not in each class
[10506] key: Spectral Decomposition | uses: Determinant Sign Argument, Semigroup Property | archetype: can a discrete chain be embedded in continuous time
[10810] key: Embedded Chain, Ansatz | uses: Conditioning, Generating Function | archetype: stationary law and waiting time in a G/M/1 queue
[10250] key: Independent Copy Trick, Fourier Inversion | uses: Characteristic Function Method | archetype: identity for the integral of a squared density
[9961] key: Bathtub Principle, Normalisation to Match Tool | uses: Guess Extremal Case | archetype: bound a moment given a density upper bound
[10565] key: Continuity of Probability, Monotone Limit | uses: Rewrite Event with Set Operations | archetype: bound probability that infinitely many events occur
[10811] key: Embedded Chain, Counterexample via Two Limits | uses: Ergodic Theorem, Memorylessness | archetype: show convergence in distribution fails for periodic input
[10251] key: Swap Order of Integration, Expand the Transform | uses: Combine Exponentials | archetype: identity between integrals of characteristic functions
[10534] key: Markov Property, Unpack Definition | uses: Ergodic Theorem | archetype: entropy rate of a Markov chain
[10418] key: Separating Hyperplane, No-Arbitrage Argument | uses: Convex Hull, Averaging Argument | archetype: either fair odds exist or there is arbitrage
[10463] key: Conditioning on First Step, Branching Property | uses: Separable ODE, Partial Fractions | archetype: extinction probability of a branching process
[10153] key: Induction, Integration by Parts | uses: Generating Function | archetype: properties of polynomials defined by repeated differentiation
[9990] key: Conditioning on Hidden Variable, Counterexample Construction | uses: Squaring Kills Sign | archetype: independence of transforms of a dependent pair
[9850] key: Sum of Squares | uses: Square Both Sides | archetype: prove an inequality by showing the difference is a square
[10041] key: Integration by Parts, Integrating Factor | uses: - | archetype: Stein's identity and Stein equation
[12722] key: Dominance Argument | uses: - | archetype: fair price of a game
[12727] key: Linearity of Expectation, Indicator Variables | uses: Symmetry | archetype: expected number of adjacent unlike pairs
[12755] key: Tail-Sum Formula, Symmetry | uses: Inclusion-Exclusion, Geometric Probability | archetype: average sizes of pieces of a broken stick
[9233] key: Bayes' Rule | uses: - | archetype: probability of a class given an observed outcome
[8988] key: Complementary Probability | uses: - | archetype: probability of more than k claims
[9522] key: Covariance Formula | uses: - | archetype: covariance from a joint table
[9636] key: Standardisation, Symmetry | uses: Independence | archetype: recover parameters from given probabilities
[9172] key: Bayes' Rule | uses: - | archetype: probability of a class given an observed outcome
[9266] key: Inclusion-Exclusion | uses: Complementary Probability | archetype: probability of exactly one of two events
[9290] key: Law of Total Expectation | uses: Uniform Proportional to Length | archetype: find the deductible for a target expected payment
[8980] key: Inclusion-Exclusion | uses: - | archetype: size of an intersection of classes
[9132] key: Reformulate as Equivalent Problem | uses: Hypergeometric Counting | archetype: lottery jackpot probability
[9453] key: CDF Inversion | uses: Normalisation | archetype: find the deductible for a target probability
[11030] key: Delta Method | uses: Solve Constraint as ODE | archetype: variance-stabilising transformation
[11019] key: Conditioning on Latent Count | uses: Symmetry, Rejection Region and Power | archetype: exact test and power for a tasting experiment
[11035] key: Linearity of Expectation, Bias via Series | uses: Jensen's Inequality, Delta Method, Distribution Sums to One | archetype: bias of an estimator
[13014] key: Induction, Conditioning on One Variable | uses: Simplest Cases First | archetype: probability that uniform draws sum to at most 1
[12982] key: Disjoint Decomposition, Symmetry | uses: - | archetype: probability that random points lie in a semicircle
[12958] key: Invariant, Flip Operation | uses: - | archetype: split blindfolded coins into piles with equal heads
[13030] key: Optimal Stopping, One-Step Lookahead | uses: - | archetype: best stopping rule in a dice game
[18002] key: Linearity of Expectation, Binomial Expansion | uses: - | archetype: moment of a shifted variable
[18030] key: Upper and Lower Bound Sandwich, No-Arbitrage Argument | uses: Limiting Case, Martingale Property | archetype: price of a perpetual American call
[18040] key: Change of Numeraire, Payoff Decomposition | uses: Completing the Square, Limiting Case | archetype: price a trigger payoff on a forward rate
[18046] key: Change of Numeraire, Martingale Pricing | uses: Ito's Lemma, Girsanov Theorem | archetype: drift of a forward rate under a new numeraire
[18063] key: Delta Hedging, Ito's Lemma | uses: Black-Scholes PDE | archetype: profit and loss from hedging with the wrong volatility
[17878] key: Sub-Replication Bound, Static Replication | uses: - | archetype: optimal lower bound for a digital option
[15913] key: Symmetry | uses: Similar Triangles, Infinitesimal Element | archetype: direction of the field of a charged rod
[15996] key: Scaling Argument | uses: - | archetype: bubble growth and acceleration in a liquid
[15971] key: Gauss's Law | uses: Choose Gaussian Surface, Spot the Error | archetype: charge density in a rotating spoke
[15940] key: Second Law Consistency Check, Reference Frame Change | uses: Energy Accounting | archetype: find the flaw in a perpetual-motion argument
[15897] key: Infinitesimal Element, Analogy to Known Law | uses: Small-Angle Approximation, Force Balance | archetype: friction of a rope round a cylinder
[15898] key: Physical Interpretation of an Integral | uses: Infinitesimal Element, Superposition | archetype: centre of mass of an arc by rotation argument
[16099] key: Adiabatic Process, Hydrostatic Equilibrium | uses: Stability Argument, Linearisation | archetype: atmospheric temperature gradient
[16097] key: Flux Balance | uses: Proportional Reasoning | archetype: pressure difference across a small hole between hot and cold gas
[16023] key: Reference Frame Change, Scaling Argument | uses: Conservation Law, Ratio Elimination | archetype: collision time of two attracting bodies
[16120] key: Superposition, Phase Condition | uses: Small-Angle Approximation | archetype: diffraction pattern of a grating with alternating slits
[16159] key: Element Force Balance, Small-Angle Approximation | uses: Symmetry, Component Decomposition | archetype: shape and tension of a current-carrying wire in a field
[16012] key: Eliminate Unknown Constants, Force Balance | uses: Terminal Velocity | archetype: top speed on flat ground from uphill and downhill speeds
```

## Step 2: vocabulary

Raw distinct tags: 189. After merging variants and dropping routine / subtopic-bound items: 103 distinct tags (39 dropped as routine steps or topic names, e.g. Binomial Expansion, Unpack Definition, Spanning Tree, Black-Scholes PDE). Of the 103, 47 occur exactly once.

### 2.1 Merged vocabulary (sorted by total frequency; K = as key, U = as uses; subjects in which it appeared)

| Tag | K | U | Subjects | Definition |
|---|---|---|---|---|
| Symmetry | 6 | 6 | Algebra, Combinatorics, Electromagnetism and Special Relativity, Geometry, Probability, Statistics | Use an exchange, reflection or relabelling under which the problem is unchanged to equate quantities, locate an extremum at the symmetric point, or cancel terms. |
| Linearity of Expectation | 6 | 0 | Probability, Quantitative Finance, Statistics | Write the quantity as a sum of simpler random variables and add their expectations, with no independence needed. |
| Complementary Counting | 2 | 4 | Algebra, Combinatorics, Probability | Count or compute the probability of the opposite event (or all minus unwanted) because it is simpler. |
| Conditioning on an Auxiliary Variable | 4 | 1 | Probability, Statistics | Fix the value of one hidden or helper variable (a coin, a count, the last draw) so the rest becomes simple, then average over it. |
| Induction | 3 | 2 | Combinatorics, Game Theory, Number Theory, Probability | Prove a claim for all n from a base case and a step from n (or all smaller cases) to n+1. |
| Extremal Principle | 2 | 2 | Combinatorics, Geometry | Pick the largest, smallest, farthest or biggest-letter object and exploit what that choice forces. |
| Infinitesimal Element | 2 | 2 | Electromagnetism and Special Relativity, Mechanics | Analyse a small slice of a continuous body (arc, rod, wire) with balance laws, then integrate or solve the resulting equation. |
| Scaling Argument | 2 | 2 | Estimation, Fluid Mechanics, Mechanics, Thermodynamics | Find how a quantity scales with size or time (powers, exponentials, ratios between cases) and use that to compare or to remove unknown constants. |
| Linearisation | 1 | 3 | Electromagnetism and Special Relativity, Mechanics, Thermodynamics, Waves and Optics | Replace a smooth function or small angle by its first-order approximation near the operating point. |
| Modular Arithmetic | 1 | 3 | Combinatorics, Number Theory | Work with residues mod m: case-split by residue, reduce a large index, or build a construction from a residue class. |
| Counterexample Construction | 3 | 0 | Geometry, Probability | Settle a claim, or show its sharpness, with one explicit case that exposes the hidden ingredient. |
| Double Counting | 3 | 0 | Algebra, Combinatorics | Count the same set in two ways, or count ends/incidences and divide, to get an equation. |
| Tail-Sum Formula | 3 | 0 | Probability | Compute E[N] as the sum of P(N>n) (or P(N>=k)), using the easy event "still waiting" or "all at least k". |
| Bijection | 2 | 1 | Combinatorics, Number Theory | Match the objects counted one-to-one with a simpler set (sorted sequences with subsets, triangles with triples). |
| Bound and Construction | 2 | 1 | Combinatorics, Number Theory | Prove a lower (or upper) bound on the optimum, then exhibit a configuration that meets it. |
| Divisibility Argument | 2 | 1 | Combinatorics, Number Theory | Use divisibility of a count, area or product (by 3, by a prime factor) to give a necessary condition or a contradiction. |
| Inclusion-Exclusion | 2 | 1 | Combinatorics, Probability | Correct a sum of overlapping counts or probabilities by alternately subtracting and adding intersections. |
| Invariant | 2 | 1 | Combinatorics, Number Theory | Find a quantity unchanged by every allowed operation and use it to fix the outcome or forbid one. |
| Recursion | 2 | 1 | Combinatorics, Number Theory | Define the object or the answer in terms of smaller copies of itself and solve or exploit the recurrence. |
| Reformulate the Problem | 2 | 1 | Combinatorics, Probability | Restate the question as an equivalent problem of another kind (game, equivalent draw, forbidden-extension to required-suffix). |
| Ansatz | 1 | 2 | Game Theory, Probability | Guess the form of the solution or strategy (geometric stationary law, threshold strategy, extremal case), then fix parameters by conditions. |
| Conservation Law | 1 | 2 | Algebra, Mechanics, Thermodynamics | Equate what goes in with what comes out or remains (mass, energy, momentum, bookkeeping total). |
| Normalisation | 1 | 2 | Number Theory, Probability | Rescale or shift (WLOG) so the problem matches a standard form or a known tool. |
| Proof by Contradiction | 1 | 2 | Combinatorics, Geometry, Number Theory | Assume the negation and derive an impossibility. |
| Geometric Probability | 0 | 3 | Probability | Turn a probability over continuous uniform variables into a length, area or volume ratio. |
| Independence | 0 | 3 | Probability, Statistics | Factorise probabilities or expectations of independent pieces. |
| Limiting Case | 0 | 3 | Probability, Quantitative Finance | Test or derive an answer from an extreme parameter value (T to infinity, H = K, p = 0) or the continuous analogue. |
| Analogy to a Solved Problem | 2 | 0 | Mechanics | Recognise the equation as one already solved in another setting (decay law, ring rotation) and transfer the solution. |
| Base Representation | 2 | 0 | Number Theory | Use binary (or balanced ternary) expansions as the form of a construction or the identity of a process. |
| Bayes' Rule | 2 | 0 | Probability | Invert a conditional probability using priors and likelihoods. |
| Change of Numeraire | 2 | 0 | Quantitative Finance | Switch to the numeraire that makes the payoff simple (payment-date bond, annuity, asset). |
| Embedded Chain | 2 | 0 | Probability | Observe a non-Markov system at its renewal epochs to obtain a Markov chain. |
| Indicator Variables | 2 | 0 | Probability | Represent a count as a sum of 0/1 variables for the events counted. |
| Integration by Parts | 2 | 0 | Probability | Move a derivative from one factor to the other to lower the degree or produce a recursion. |
| No-Arbitrage Argument | 2 | 0 | Quantitative Finance | Derive a price, bound or equivalence by showing any violation allows a riskless profit. |
| Pigeonhole Principle | 2 | 0 | Combinatorics, Number Theory | More objects than boxes forces two to share a box (also bounded orbits cycle, overlapping counts). |
| Reference Frame Change | 2 | 0 | Mechanics, Thermodynamics | Move to the frame (centre of mass, rest frame of an object) in which the problem is simplest. |
| Sandwich Bound | 2 | 0 | Quantitative Finance | Pin a value between a model-free upper bound and a lower bound that meet. |
| Spectral Method | 2 | 0 | Combinatorics, Probability | Use eigenvalues/eigenvectors or projections of a matrix (adjacency, transition) to get exact powers or integrality constraints. |
| Conditioning on First Step | 1 | 1 | Probability | Condition on what happens first, noting the process then restarts in a known state, and write an equation for the answer. |
| Delta Method | 1 | 1 | Statistics | Approximate mean and variance of a function of an estimator by its tangent-line expansion. |
| Eliminate Unknown Constants | 1 | 1 | Mechanics | Combine equations from several scenarios so that unknown constants cancel from the target. |
| Force Balance | 1 | 1 | Mechanics | Set net force (or torque) to zero on an element or object and solve. |
| Ito's Lemma | 1 | 1 | Quantitative Finance | Expand a function of a diffusion to second order to obtain drift and diffusion terms. |
| Martingale Pricing | 1 | 1 | Quantitative Finance | Price as a discounted expectation under a measure where traded assets divided by numeraire are martingales. |
| Parity | 1 | 1 | Combinatorics, Number Theory | Use odd/even classes as an invariant, a first necessary condition, or a driver of descent. |
| Partial Fractions | 1 | 1 | Number Theory, Probability | Split a rational expression into simpler terms so sums telescope or recombine. |
| Potential Function | 1 | 1 | Combinatorics | Track a quantity that each move can change by at most c (or only in one direction) to bound the number of moves or force termination. |
| Steady-State Balance | 1 | 1 | Mechanics, Thermodynamics | Set a rate in equal to a rate out (flux, drag against drive) at equilibrium. |
| Superposition | 1 | 1 | Mechanics, Waves and Optics | Add the contributions of independent parts (waves, slices, sub-sectors). |
| Topological Argument | 1 | 1 | Analysis/Topology, Geometry | Use connectedness, separation of the plane, or Jordan-curve type facts. |
| Ergodic Theorem | 0 | 2 | Probability | Pass to the long-run limit of a Markov chain using the stationary distribution. |
| Generating Function | 0 | 2 | Probability | Package a sequence in a power series (or exponential series) and read off identities from it. |
| Jensen's Inequality | 0 | 2 | Algebra, Statistics | Bound an average of a convex or concave function by the function of the average. |
| Separable ODE | 0 | 2 | Probability, Statistics | Reduce a constraint or recursion to dy/dt = f(y) and integrate. |
| Small Cases First | 0 | 2 | Game Theory, Probability | Solve n = 1, 2, 3, ... to find the pattern and the induction. |
| AM-GM Inequality | 1 | 0 | Algebra | Bound a product by a sum (or sum by product) via arithmetic-geometric means. |
| Backward Induction | 1 | 0 | Game Theory | Solve a game from the final position backwards, or from n-1 players to n. |
| Bathtub Principle | 1 | 0 | Probability | Minimise or maximise an integral against a fixed profile by packing mass where the weight is smallest or largest. |
| Binary Search | 1 | 0 | Combinatorics | Narrow the candidate set by a constant factor per question (halving, thirding). |
| Characteristic Function Method | 1 | 0 | Probability | Use characteristic functions (products for sums, inversion for densities). |
| Compare Consecutive Cases | 1 | 0 | Number Theory | Show a claimed constant quantity equals its predecessor by tracking terms that enter and leave. |
| Continue Past Stopping Time | 1 | 0 | Probability | Pretend the process continues after the stopping rule, so the early outcomes are simple iid trials. |
| Continuity of Probability | 1 | 0 | Probability | Pass limits through monotone sequences of events. |
| Delta Hedging | 1 | 0 | Quantitative Finance | Hold the derivative-neutral share position and attribute residual P&L to the mismatched parameter. |
| Disjoint Decomposition | 1 | 0 | Probability | Split the event into mutually exclusive, equally likely events and add probabilities. |
| Dominance Argument | 1 | 0 | Probability | Show one option is at least as good as another because the first can imitate the second. |
| Exhaustive Case Analysis | 1 | 0 | Geometry | Enumerate all structurally different cases and check each. |
| Gauss's Law | 1 | 0 | Electromagnetism and Special Relativity | Use flux through a closed surface to get the field or charge density. |
| Independent Copy Trick | 1 | 0 | Probability | Introduce an independent copy of a variable (X-Y) so a squared transform becomes a transform of a new variable. |
| Indifference Condition | 1 | 0 | Game Theory | At a boundary between two actions the player must be indifferent; equate their values. |
| Infinite Descent | 1 | 0 | Number Theory | Show a property forces divisibility that survives division, so only zero satisfies it. |
| Information-Theoretic Bound | 1 | 0 | Number Theory | Count the outcomes a procedure can distinguish (2^n, 3^n) to get a lower bound on resources. |
| Injective Labelling | 1 | 0 | Analysis/Topology | Assign each object a label from a countable set (rationals) such that different objects get different labels. |
| Markov Property | 1 | 0 | Probability | Condition on the present state and discard the past. |
| Multiplication Principle | 1 | 0 | Combinatorics | Count by independent sequential choices, multiplying the options. |
| Optimal Stopping | 1 | 0 | Probability | Stop when the immediate payoff beats the expected value of continuing (one-step comparison). |
| Optimise Over Patterns | 1 | 0 | Probability | Compare a few candidate periodic patterns by computing the per-unit value and choose the best. |
| Order-of-Magnitude Estimate | 1 | 0 | Estimation | Replace exact computation by a rough estimate (powers of 10 or 2) to decide feasibility. |
| Pairing Argument | 1 | 0 | Combinatorics | Pair up items so that one from each pair can be guaranteed to dominate. |
| Payoff Decomposition | 1 | 0 | Quantitative Finance | Split a payoff into standard pieces (call plus digital, asset-or-nothing plus cash-or-nothing). |
| Periodicity | 1 | 0 | Number Theory | Find the period of a repeating pattern and reduce a huge index modulo it. |
| Phase Condition | 1 | 0 | Waves and Optics | Find directions in which the path differences produce constructive phase alignment. |
| Recognise Known Distribution | 1 | 0 | Statistics | Spot that a sum or integral is a total probability of a known distribution (negative binomial) and evaluate it as 1. |
| Second Law Consistency Check | 1 | 0 | Thermodynamics | Test a mechanism against entropy or heat flow to find the missing term. |
| Separating Hyperplane | 1 | 0 | Quantitative Finance | Use the closest point of a closed convex set to build a separating vector (duality). |
| Standardisation | 1 | 0 | Statistics | Convert to a standard normal via z-scores and use tables and symmetry. |
| Static Replication | 1 | 0 | Quantitative Finance | Match a payoff by a fixed portfolio of simpler instruments. |
| Sum of Squares | 1 | 0 | Algebra | Write the difference of two sides as a square, hence non-negative. |
| Swap Order of Integration | 1 | 0 | Probability | Exchange the order of a double integral (Fubini) to expose a known inner integral. |
| Threshold Strategy | 1 | 0 | Game Theory | Restrict attention to strategies of the form "act iff the signal exceeds c". |
| Two-Colouring | 1 | 0 | Combinatorics | Colour the vertices of an even cycle or bipartite structure alternately so each edge has one of each colour. |
| Wald's Identity | 1 | 0 | Probability | Equate expected total at a stopping time to rate times expected stopping time. |
| Change of Measure | 0 | 1 | Quantitative Finance | Reweight by a density (Girsanov) so a variable becomes driftless or a probability simplifies. |
| Dominant Case Plus Correction | 0 | 1 | Probability | Solve the overwhelmingly likely scenario, then bound the correction from the rare one. |
| GCD Identity | 0 | 1 | Number Theory | Use gcd(a, b) = gcd(a, a+b) type identities to move coprimality conditions. |
| Generalise the Target | 0 | 1 | Probability | Replace a specific parameter (target 1) by a variable t so a self-similar equation appears. |
| Greedy Algorithm | 0 | 1 | Number Theory | Build a construction by taking the largest allowable next step each time. |
| Invariance Under Transformation | 0 | 1 | Number Theory | Find transformations (shift, scale) that preserve the hypothesis and use them to normalise. |
| Memorylessness | 0 | 1 | Probability | Use that the exponential/geometric wait forgets its past, so the future is a fresh start. |
| Similar Triangles | 0 | 1 | Electromagnetism and Special Relativity | Use similarity to relate a small element to its angular size and show an invariance. |
| Smoothing | 0 | 1 | Algebra | Replace two variables by their average (keeping the sum) to show an expression improves. |
| Stability Argument | 0 | 1 | Thermodynamics | Displace a small parcel and compare it with its surroundings to find the threshold of stability. |

### 2.2 Merges applied (raw tag to merged tag)

- Analogy to a Solved Problem <- Analogy to Known Law; Physical Interpretation of an Integral
- Ansatz <- Guess Extremal Case; Guess Strategy Shape
- Bound and Construction <- Lower Bound Plus Construction; Upper Bound Plus Construction
- Change of Measure <- Girsanov Theorem
- Characteristic Function Method <- Fourier Inversion
- Complementary Counting <- Complementary Probability
- Conditioning on an Auxiliary Variable <- Conditioning; Conditioning on Hidden Variable; Conditioning on Latent Count; Conditioning on One Variable; Law of Total Expectation
- Conservation Law <- Energy Accounting; Global Accounting
- Continuity of Probability <- Monotone Limit
- Counterexample Construction <- Counterexample Search; Counterexample via Two Limits
- Divisibility Argument <- Area Counting
- Double Counting <- Add the Equations; Counting Argument
- Eliminate Unknown Constants <- Ratio Elimination
- Geometric Probability <- Simplex Volume; Uniform Proportional to Length
- Induction <- Induction on n
- Infinitesimal Element <- Element Force Balance
- Injective Labelling <- Density of Rationals
- Invariant <- Flip Operation
- Limiting Case <- Continuous Analogue Check
- Linearisation <- Small-Angle Approximation
- Martingale Pricing <- Martingale Property
- Modular Arithmetic <- Case Split Mod n; Modular Residue Construction
- Normalisation <- Normalisation to Match Tool
- Optimal Stopping <- One-Step Lookahead
- Order-of-Magnitude Estimate <- Exponential Growth
- Potential Function <- Monovariant
- Proof by Contradiction <- Contradiction
- Recognise Known Distribution <- Bias via Series; Distribution Sums to One
- Recursion <- Recursive Construction
- Reformulate the Problem <- Reformulate as Equivalent Problem; Reformulate as Game; Reformulate the Condition
- Sandwich Bound <- Sub-Replication Bound; Upper and Lower Bound Sandwich
- Scaling Argument <- Compare Growth Rates; Proportional Reasoning
- Separable ODE <- Solve Constraint as ODE
- Small Cases First <- Simplest Cases First
- Spectral Method <- Spectral Decomposition
- Steady-State Balance <- Flux Balance; Terminal Velocity
- Topological Argument <- Connectedness Argument

Further merges I would make beyond what the counts show (not applied above because they cross conceptual lines):

- Wald's Identity + Optional Stopping + Martingale (expected, not observed) -> **Optional Stopping**. Wald is the iid special case; one tag is enough for a student filter.
- Binary Search + Information-Theoretic Bound + Bound and Construction: three faces of "count outcomes to bound the number of questions/weights/moves". Keep Information-Theoretic Bound for counting-outcomes and Bound and Construction for the two-sided structure; fold Binary Search into Information-Theoretic Bound only if the list must be short.
- Indicator Variables into Linearity of Expectation (both Indicator Variables questions also carry Linearity of Expectation). Keep Indicator Variables as the "uses" companion or merge to **Linearity of Expectation**; the two never separate in practice.
- Induction + Recursion + Small Cases First: Induction is a proof method, Recursion a way of defining or solving; I would keep both but treat Small Cases First as a hint, not a tag.
- Counterexample Construction + Exhaustive Case Analysis: both are "settle by explicit cases"; merge to **Case Analysis** only if Counterexample Construction stays at 3 or fewer questions per 100.
- Embedded Chain + Markov Property + Ergodic Theorem: tag-wise these are Markov-chain topic words disguised as moves (see 2.4).
- Conditioning on First Step vs Conditioning on an Auxiliary Variable: different enough (the first creates a recursion, the second removes dependence); keep both.
- Reference Frame Change (centre-of-mass frame, rest frame) should absorb "Centre of Mass Frame"; it already covered 16023 and 15940.

### 2.3 Tags too broad to be a useful filter (split)

- **Symmetry** (12 questions, 6 subjects). It covered four different moves: (a) symmetric extremum guess (sin A sin B sin C, 14253); (b) exchangeability so all indicators have equal probability (12727, 12755, 12982); (c) reflection / palindrome / ruler structure in a construction (14032); (d) field of a symmetric charge distribution cancels in components (15913). Split into **Symmetry (Exchangeability)**, **Symmetric Extremum** (guess optimum at the symmetric point, then prove), **Geometric Symmetry** (reflection, cancellation of components).
- **Conservation Law** (3): mass bookkeeping (13685), energy accounting, centre-of-mass momentum. Split into **Conservation Law** (physics quantities) and **Bookkeeping (Input = Output + Remainder)** for the lemon-juice style accounting that appears in puzzles with no physics.
- **Induction** (5): ordinary induction, strong induction on moves (14147), induction on number of players (12896), induction as proof of a closed form (14233-style). Split off **Backward Induction** (already separate) and keep Induction as proof-method only.
- **Double Counting** (as merged, includes Counting Argument and Add the Equations): the merge was forced. Split into **Double Counting** (count one set two ways) and **Counting Argument** (bound the size of a set by counting what it must contain). 12689 and 12672 use the second.
- **Complementary Counting** (6): covers "1 minus P(not)" and "total minus the bad ones". Fine as one tag but should carry the probability variant in its definition; if a split is wanted: Complementary Probability / Complementary Counting.
- **Conditioning on an Auxiliary Variable** (5): includes Law of Total Expectation on mixtures (9290) and conditioning on a latent count (11019). Acceptable, but the tag Law of Total Expectation should remain searchable as an alias.
- **Scaling Argument** (4): dimension-free scaling of costs (paper folding growth rates), time scaling in a collision (T proportional to sqrt m), exponential comparison. Split into **Scaling Argument** (power-law and ratio reasoning) and the existing **Dimensional Analysis** (expected, not observed).
- **Linearisation** (4): small-angle and first-order expansions. Fine for physics; the statistics version (Delta Method) must stay separate because its output is a variance.
- **Modular Arithmetic** (4): case split on residues, reduction of an index modulo a period, residue-class construction. Split into **Modular Arithmetic** (residue cases and constructions) and **Periodicity** (already separate).

### 2.4 Tags that look redundant with the topic tree (candidates to drop or demote)

Single-subject tags are not automatically redundant; a tag is redundant when the subtopic name already implies it. In this sample:

- **Embedded Chain**, **Markov Property**, **Ergodic Theorem**, **Characteristic Function Method**, **Generating Function**, **Continuity of Probability** (all Probability only): each is either the subtopic itself (queues, Markov chains, characteristic functions) or a standard theorem. Keep as "named theorem used as a tool" at most; I would drop Embedded Chain, Markov Property and Ergodic Theorem.
- **Delta Hedging**, **Static Replication**, **Change of Numeraire**, **Change of Measure**, **Ito's Lemma**, **Martingale Pricing**, **Payoff Decomposition** (Quantitative Finance only). Tree subtopics already name hedging, numeraires and martingale pricing. Keep No-Arbitrage Argument, Static Replication, Change of Measure (cross-cutting into probability) and drop the rest as tags.
- **Gauss's Law**, **Similar Triangles**, **Phase Condition**, **Second Law Consistency Check**, **Stability Argument** (single physics questions): either the topic itself (Gauss's Law) or a one-off. Keep **Stability Argument** (it will recur as displaced-parcel and small-perturbation reasoning in mechanics and fluids).
- **Standardisation**, **Recognise Known Distribution**, **Bayes' Rule** (Statistics / Probability): Bayes' Rule is both a subtopic and a move; keep it as a tag only if the tree does not already have a Bayes subtopic (it probably does, drop).
- **Indifference Condition**, **Threshold Strategy**, **Backward Induction** (Game Theory): subtopic-level. Keep Indifference Condition and Backward Induction; they are the standard moves and will recur in poker/auction interview questions.
- **Bathtub Principle**, **Independent Copy Trick**, **Swap Order of Integration**, **Integration by Parts**, **Partial Fractions**, **Separable ODE**: techniques of analysis. Integration by Parts, Partial Fractions and Separable ODE are routine steps, not strategy; drop. Independent Copy Trick is genuinely cross-subject (statistics, Markov coupling); keep.

### 2.5 Techniques expected in such sources but not observed in the sample (expected, not observed)

- Reflection Principle (random walks, ballot problems) (expected, not observed)
- Coupling (expected, not observed)
- Martingale and Optional Stopping (Wald only observed) (expected, not observed)
- Law of Total Expectation as a named move for recursive expected values (only 2 conditioning questions here) (expected, not observed)
- Memorylessness as a key (only seen as a use) (expected, not observed)
- Strategy Stealing (expected, not observed)
- Dimensional Analysis (expected, not observed)
- Replication and Black-Scholes style hedging arguments (static replication seen once) (expected, not observed)
- Order Statistics via Uniform Spacings (partially seen in 12755, 12789) (expected, not observed)
- Invariant by colouring (chessboard / checkerboard colouring) (expected, not observed)
- Graph Modelling (turn a puzzle into a graph and use degrees, Euler path, Hall's theorem) (expected, not observed)
- Extremal Graph Argument (expected, not observed)
- Telescoping Sum (expected, not observed)
- Generating Function for counting (only used for Hermite polynomials) (expected, not observed)
- Stars and Bars (expected, not observed)
- Catalan / Reflection Counting (expected, not observed)
- Inclusion-Exclusion for derangements (expected, not observed)
- Conservation of Energy / Angular Momentum as key (only lightly seen) (expected, not observed)
- Center-of-Mass Frame (seen but merged into Reference Frame Change) (expected, not observed)
- Moment Generating Function / Laplace Transform (expected, not observed)
- Central Limit Theorem approximation as key (expected, not observed)
- Maximum Likelihood and Method of Moments (estimator design) (expected, not observed)
- Sufficient Statistic / Rao-Blackwell (expected, not observed)
- Kelly Criterion / Log Utility (expected, not observed)
- Put-Call Parity (expected, not observed)
- Risk-Neutral Valuation as a distinct move from No-Arbitrage (expected, not observed)
- Weighing / Coin Identification by Information Counting (partly observed in 13659) (expected, not observed)
- Lagrange Multipliers (expected, not observed)
- Cauchy-Schwarz Inequality (derived in 9850, not used as a tool) (expected, not observed)
- Rearrangement Inequality (expected, not observed)
- Convexity (Jensen seen only twice) (expected, not observed)
- Binary Encoding of States (observed as Base Representation) (expected, not observed)
- Monte Carlo / Simulation Argument (expected, not observed)
- Energy Method / Variational Principle (expected, not observed)
- Dimensional Analysis plus Scaling Law (Fluid Mechanics) (expected, not observed)
- Gauge or Frame Invariance in Relativity (Lorentz Transformation) (expected, not observed)
- Image Charges / Method of Images (expected, not observed)
- Equivalent Circuit / Thevenin (expected, not observed)
- Fermi Estimate chains (expected, not observed)

### 2.6 Is "key" versus "uses" worth storing?

Judged from this sample: yes, but only as a weak two-level flag, and only for ranking, not as separate filters.
- 90 questions produced 146 key assignments and 112 uses assignments; 15 questions had no uses at all (short routine solutions such as actuarial one-liners and 12672). So "uses" is empty for about one in six questions.
- Tags split cleanly by role: 53 of 103 merged tags appeared only as key, 18 only as uses, 32 as both. Tags that are almost always "uses" (Independence, Geometric Probability, Limiting Case, Generating Function, Separable ODE, Ergodic Theorem, Jensen's Inequality, Small Cases First) are the supporting tools; tags that are almost always key (Tail-Sum Formula, Pigeonhole Principle, Linearity of Expectation, Indicator Variables, No-Arbitrage Argument, Change of Numeraire, Bayes' Rule) are the named decisive moves. A student wants questions where Pigeonhole is the idea, not questions where it appears in a side remark, so the distinction changes search results.
- The cost: taggers disagree about key versus uses more than about the tag itself (for example Symmetry in 12755 and Induction in 13014). A cheap compromise is to store key tags (1-2 per question) as the primary tags and uses (0-3) as secondary tags that are searchable but ranked lower. Do not make "uses" a mandatory field.

### 2.7 Families (9), and whether they help

**Counting and Combinatorial Structure** (9 tags): Double Counting, Complementary Counting, Inclusion-Exclusion, Bijection, Multiplication Principle, Pigeonhole Principle, Pairing Argument, Disjoint Decomposition, Two-Colouring

**Extremal Reasoning, Bounds and Inequalities** (15 tags): Extremal Principle, Bound and Construction, Sandwich Bound, Information-Theoretic Bound, Greedy Algorithm, Optimise Over Patterns, AM-GM Inequality, Jensen's Inequality, Smoothing, Sum of Squares, Bathtub Principle, Separating Hyperplane, Dominance Argument, Dominant Case Plus Correction, Binary Search

**Invariants and Number-Theoretic Structure** (10 tags): Invariant, Parity, Potential Function, Infinite Descent, Modular Arithmetic, Divisibility Argument, Periodicity, Base Representation, GCD Identity, Invariance Under Transformation

**Induction, Recursion and Sequential Decomposition** (10 tags): Induction, Recursion, Backward Induction, Conditioning on First Step, Compare Consecutive Cases, Small Cases First, Generalise the Target, Embedded Chain, Ansatz, Continue Past Stopping Time

**Probabilistic and Analytic Machinery** (24 tags): Linearity of Expectation, Indicator Variables, Tail-Sum Formula, Conditioning on an Auxiliary Variable, Independence, Geometric Probability, Wald's Identity, Independent Copy Trick, Characteristic Function Method, Generating Function, Continuity of Probability, Memorylessness, Markov Property, Ergodic Theorem, Bayes' Rule, Optimal Stopping, Standardisation, Delta Method, Recognise Known Distribution, Swap Order of Integration, Integration by Parts, Partial Fractions, Separable ODE, Spectral Method

**Symmetry and Problem Transformation** (10 tags): Symmetry, Reformulate the Problem, Normalisation, Reference Frame Change, Analogy to a Solved Problem, Counterexample Construction, Topological Argument, Injective Labelling, Exhaustive Case Analysis, Proof by Contradiction

**Equilibrium and Strategy** (2 tags): Indifference Condition, Threshold Strategy

**Pricing and No-Arbitrage** (8 tags): No-Arbitrage Argument, Change of Numeraire, Change of Measure, Martingale Pricing, Ito's Lemma, Delta Hedging, Static Replication, Payoff Decomposition

**Physical Reasoning** (15 tags): Conservation Law, Scaling Argument, Order-of-Magnitude Estimate, Infinitesimal Element, Linearisation, Force Balance, Superposition, Steady-State Balance, Eliminate Unknown Constants, Gauss's Law, Similar Triangles, Second Law Consistency Check, Stability Argument, Phase Condition, Limiting Case

Do families help? Partly. They help as a browsing layer for 100+ tags and show that the vocabulary clusters sensibly: a student who wants "estimation and physics intuition" gets Scaling Argument, Order-of-Magnitude Estimate and Limiting Case in one place. They do not help as a filter on their own: Probabilistic and Analytic Machinery holds 24 tags that nothing unites except the subject, so it behaves like a topic, not a method family. I would split it into (a) Expectation and Conditioning Tricks (Linearity, Indicators, Tail-Sum, Conditioning, Wald, Memorylessness, Symmetry in the exchangeable sense) and (b) Analytic Tools (Characteristic Functions, Generating Functions, Fubini, Integration by Parts) and put (b) at lower priority. Use families for display only; store tags flat.

### 2.8 Did the archetype field produce labels a student would search for?

Yes, and in this sample it produced more searchable labels than the technique tags did. Archetypes are the phrases students use when they ask "give me more of those". Best examples, with how many sample questions shared them:
- expected waiting time or length until a threshold is reached (14013 race to 21, 14027 uniforms past 1, 12811 stopping rule, 12789 minimum of dice)
- minimum number of moves / weights / queries (14369 knight, 13659 weights, 14355 card trick, 14444 penny machine)
- expected number of loops / adjacent pairs / unlucky events (14158, 12727, 13744): the Linearity-of-Expectation-by-indicators archetype
- fair price or value of a game (12722, 14108, 13030, 9290)
- optimal stopping with a one-step rule (13030, 12896 backward induction version)
- extremum of a symmetric expression (14253, 12755 pieces)
- count the objects with a defining property (13718 diagonals, 14233 increasing digits, 13643 triangles from lines, 12869 photo arrangements)
- prove a quantity is constant, or all numbers equal (13738, 14289)
- tiling or coverage feasibility for which n (14416)
- which position after N steps in a periodic pattern (14331)
- bound a moment or an estimator's bias (9961, 11035)
- price of a derivative by bounding (18030, 17878) and drift under a new numeraire (18046)
- shape or tension of a flexible line in a field (15897 capstan, 16159 wire): the infinitesimal-element archetype
- top speed from two measured speeds (16012): the eliminate-constants archetype
- find the flaw in a seemingly valid argument (15940, 15971, 13791): paradox / spot-the-error archetype

Three caveats. (1) Archetypes are only searchable when worded consistently; a controlled list of about 40 archetype labels (generated from this sample plus more) is needed, free phrases will fragment. (2) Archetype and tag partly overlap: "expected number of X" is exactly the Indicator Variables use case. Showing both is fine, but archetypes should cluster into Optimisation, Counting, Expected Value, Pricing, Proof and Estimation task types, which students can pick before tags. (3) Archetype like "fair price of a game" is close to a subtopic name; it works because it spans probability, game theory and finance. The "Point Finding" tag the owner already made fits here: it is an archetype, not a technique, and should live in a separate Task Type field rather than in the technique vocabulary.

### 2.9 Observations on how the fixed list should be built

- Singletons dominate open tagging: 47 of 103 merged tags occurred once in 90 questions, and many more would have appeared if I had not merged. A fixed list needs a frequency floor: take about 50-60 tags that recur across at least two subjects (or across at least three questions in a subject) and map the rest onto them with aliases. The sample suggests that only about 8 tags are truly cross-subject (Induction, Linearity of Expectation, Symmetry, Complementary Counting, Conservation Law, Scaling Argument, Proof by Contradiction, Linearisation), which is exactly where the owner's value proposition lies; the list should be curated to maximise that kind of tag.
- Keep tags at the level of a move, not a subtopic. In every subject there were temptations to tag the theorem (Gauss's Law, Embedded Chain, Characteristic Function Method). Those are topic-tree material. Tags that worked across subjects were the verbs: Pair, Count twice, Eliminate constants, Change frame, Condition on, Scale, Linearise, Bound from both sides.
- Separate three kinds of metadata that taggers kept mixing: technique tags (the move), archetype / task type (what is asked), and quality flags (open problem, no real solution, trick question). 13838 (Collatz) and 13843 (net of a polyhedron) are open problems; 13791 is a loophole puzzle; 12722 and 15996 have missing content. These need a flag, not tags.
- Source style shapes the tags. Physics puzzles produce tags like Infinitesimal Element, Scaling Argument, Eliminate Unknown Constants that never appear in the combinatorics or finance sources; actuarial exam items (9 questions here) produce almost only Bayes' Rule, Complement and Inclusion-Exclusion (routine). For exam-style questions with no strategy, allow "no tag" instead of forcing a weak one; 6 of 90 sample questions were in this class.
- Fix tag names to the standard forms in the brief (Linearity of Expectation, Conditioning on First Step, Reference Frame Change, Information-Theoretic Bound). Where independent taggers will vary (Bound and Construction, Counting Argument versus Double Counting, Reformulate the Problem) include a one-line definition and 2-3 canonical examples; the merges in 2.2 show how many spelling variants arose in one pass (189 raw to 103).