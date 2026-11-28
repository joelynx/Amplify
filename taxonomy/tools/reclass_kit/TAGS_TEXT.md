# Tag file: textbooks and exam papers

Rules: `key` holds 0-2 technique tags from the list below, ONLY when the technique is unmistakably
the idea the solution rests on; otherwise leave it empty (most textbook questions have none).
`supporting` is always empty for these sources. `task` holds at most one task tag, or null.
Skip any tag that is true of every question in the chosen subtopic by definition.

## Technique tags (key only)

- Complementary Counting: count or compute the complement and subtract (includes 1 - P) (aliases: Complementary Probability)
### Analysis tools
- Mean Value Theorem as a Tool: MVT, Rolle or Cauchy MVT used outside their own subtopic
- Intermediate Value Argument: a sign change or continuity forces a value to be attained
- Taylor Expansion: expansion with remainder drives a limit, bound or approximation (aliases: Asymptotic Expansion)
- Auxiliary Function: a helper function is built so a theorem applies to it
- Monotonicity Argument: monotonicity of a function or sequence settles a comparison or root count
- Interchange of Limits: sums, integrals, limits or derivatives swapped with justification (aliases: Fubini, Differentiation under the Integral)
- Riemann Sum: a limit of sums recognized as an integral
- Compactness Argument: convergent subsequences or finite subcovers give the result (aliases: Bolzano-Weierstrass)
- Fixed Point Argument: a contraction or fixed point theorem gives existence or a limit (aliases: Picard Iteration, Banach)
- Linearization: expand to first order about a known state (small angles, small perturbations, delta method) (aliases: Small Perturbation)
### Probability moves
- Linearity of Expectation: expectation of a sum split into terms, usually via indicators (aliases: Indicator Variables)
- Conditioning on First Step: condition on the first move to get equations for probabilities or expectations (aliases: First-Step Analysis)
- Conditioning on a Variable: law of total probability or expectation over a well-chosen variable (aliases: Law of Total Expectation)
- Exchangeability: all positions or orderings are equally likely by symmetry
- Tail-Sum Formula: E[X] as a sum or integral of tail probabilities
- Memorylessness: the exponential or geometric memoryless property is the key
- Coupling: two processes are built on one probability space to compare them (aliases: Independent Copy Trick)
- Martingale and Optional Stopping: a martingale and a stopping theorem (or Wald) give the answer (aliases: Wald's Identity)
- Change of Measure: switch to an equivalent measure or numeraire (aliases: Girsanov, Change of Numeraire)
### Finance and economics moves
- No-Arbitrage Argument: a price or bound follows because otherwise there is a riskless profit
- Replication and Hedging: a payoff is reproduced by a portfolio of other instruments (aliases: Static Replication, Delta Hedging)
- Indifference Condition: an equilibrium is found where an agent is indifferent between choices
### Physical and engineering reasoning
- Conservation of Energy: an energy balance (mechanical, thermal, electrical) is the governing step (aliases: First Law Balance)
- Conservation of Momentum: linear momentum balance (collisions, jets, control volumes)
- Conservation of Angular Momentum: angular momentum balance about a well-chosen point
- Conservation of Mass: continuity: flow in equals flow out plus accumulation (aliases: Bookkeeping)
- Equilibrium of Forces and Moments: force and moment sums are zero (aliases: Force Balance)
- Reference Frame Change: moving to a center-of-mass, rotating or co-moving frame simplifies the problem
- Dimensional Analysis: the answer's form follows from units alone
- Scaling Argument: power-law or ratio reasoning between two cases (aliases: Similarity)
- Ratio Method: compute at a known state and scale, unknown constants cancel (aliases: Eliminate Unknown Constants)
- Order-of-Magnitude Estimate: a Fermi estimate gives the answer
- Limiting Cases: extreme or special cases solve or check the problem
- Infinitesimal Element: cut into thin elements, write the local law, integrate (aliases: Slice Method)
- Superposition: a linear system's response is the sum of simpler responses
- Equivalent Network: a system is reduced to series and parallel resistances or an analogous circuit (aliases: Thermal Resistance Network, Thevenin)
- Energy Method: virtual work, minimum potential energy, Castigliano or a Lagrangian (aliases: Variational Principle)
- Method of Images: an image source replaces a boundary
- Iterative Solution: guess and update until convergence (Newton, friction factor, trial and error)
- Graphical Solution: the answer is read from an intersection, chart or load line (aliases: Load Line)
### Problem transformation
- Symmetry Argument: geometric or structural symmetry cancels terms or reduces the problem
- Coordinate Method: coordinates or vectors turn a geometric or physical problem into algebra (aliases: Coordinate Bash, Vector Method)

## Task tags (role task; at most one per question)

- Point Finding: find the points where a quantity is extreme or a condition holds (your tag)
- Find the Optimum: find the maximum or minimum value or the best design
- Prove Existence: show something exists
- Prove Impossibility: show something cannot happen or has no solution
- Prove an Identity: establish an equality for all cases
- Prove an Inequality: establish an inequality for all cases
- Find All Solutions: determine every number, function or configuration that works
- Count Configurations: how many objects have the property
- Expected Waiting Time: expected time or steps until a pattern, threshold or event
- Expected Count: expected number of fixed points, runs, loops or events
- Fair Value of a Game: the price or value of a bet, game or contract
- Optimal Strategy: best play, stopping rule or betting rule
- Who Wins: decide which player wins a combinatorial game
- Minimum Number of Moves: fewest moves, weighings or queries
- Last Digits and Remainders: final digits, remainders or position in a periodic pattern
- Find the Locus: describe the set of points satisfying a condition
- Limit or Asymptotics: the limiting value or growth rate
- Evaluate a Sum or Integral: closed form of a sum, product or integral
- Tiling and Covering: whether or how a region can be tiled or covered
- Spot the Flaw: find the error in a paradox or seemingly valid argument
- Estimate: an order-of-magnitude answer with no exact data
- Design or Size: choose dimensions or ratings to meet a specification
- Performance and Efficiency: rate an existing machine, plant or system
- Compare Alternatives: evaluate two or more options and decide
- Explain a Concept: qualitative answer, no calculation
- Derive a Relation: derive a formula or governing equation
- Sketch or Plot: draw a graph, diagram or curve
- Read Tables or Charts: the answer needs property tables, steam tables or a chart
- No Prerequisites: solvable with school arithmetic and logic alone
