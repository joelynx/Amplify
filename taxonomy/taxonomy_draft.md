# Amplify taxonomy (draft for review)

Every question gets one leaf: **Subject > Topic > Branch > Subtopic**.
- A subtopic is one main idea, like your existing "Rank-Nullity Theorem".
- A branch is the group a student selects to practise several subtopics at once.
- A topic is a course-sized field inside a subject.

The machine-readable copy is `taxonomy.json`. The per-group drafts, with each one's cluster coverage map and decision notes, are in `drafts/`.

## How it was built

- **Clusters.** The 21,311 unsorted questions were grouped into 500 embedding clusters, and each cluster was routed to a subject.
- **Drafting.** Ten drafting agents each built one group of subjects. Each worked from:
  - the cleaned tables of contents (`TOCs_clean.md`), used as a guide only;
  - the drafting rules in `STYLE.md` and the subject boundaries in `SUBJECTS.md`;
  - the actual cluster members. Most agents read every member question, not just samples.
- **Coverage.** Every one of the 500 clusters is mapped to subtopics or marked as belonging to another subject. Nothing was left unplaced.
- **Merging.** I merged the ten drafts, settled the overlaps listed below, and normalised the names:
  - US spelling, which matches the "-ize" you write;
  - Title Case, with short prepositions in lower case;
  - no "/", at most one parenthetical, no MISC or "Applications" buckets.
- **Estimates.** The `~n` after each subtopic is the drafter's estimate from cluster counts. Classification will give the real numbers.

## Summary
| Subject | Topics | Branches | Subtopics | ~Questions |
|---|---|---|---|---|
| Calculus | Calculus, Real Analysis | 17 | 102 | 1,600 |
| Complex Analysis | Complex Analysis | 4 | 18 | 183 |
| Linear Algebra and Differential Equations | Linear Algebra, Differential Equations | 19 | 89 | 992 |
| Algebra | Elementary Algebra, Theory of Polynomials, Algebraic Inequalities, Sequences, Sums and Functional Equations | 17 | 68 | 1,212 |
| Abstract Algebra | Group Theory, Ring and Field Theory | 6 | 22 | 221 |
| Number Theory | Elementary Number Theory, Diophantine Equations | 13 | 67 | 1,843 |
| Combinatorics | Enumerative Combinatorics, Graph Theory, Extremal Combinatorics, Combinatorial Geometry, Combinatorial Games and Processes, Logic and Algorithmic Puzzles | 26 | 117 | 2,005 |
| Geometry | Plane Geometry, Solid Geometry | 11 | 51 | 596 |
| Probability and Stochastic Processes | Probability, Stochastic Processes | 23 | 138 | 3,176 |
| Statistics | Mathematical Statistics | 7 | 31 | 301 |
| Quantitative Finance | Derivatives Pricing, Fixed Income, Portfolio Theory and Risk Management | 14 | 51 | 483 |
| Economics | Macroeconomics | 9 | 32 | 266 |
| Mechanics | Classical Mechanics, Oscillations and Waves, Solid Mechanics | 25 | 111 | 1,237 |
| Fluid Mechanics | Fluid Mechanics, Compressible Flow, Hydraulics and Hydraulic Machines | 18 | 107 | 1,779 |
| Heat Transfer | Heat and Mass Transfer | 10 | 47 | 573 |
| Thermodynamics | Heat and Thermodynamics | 5 | 15 | 110 |
| Electromagnetism and Special Relativity | Electromagnetism, Optics, Special Relativity | 12 | 55 | 567 |
| Quantum Mechanics | Quantum, Atomic and Nuclear Physics | 2 | 6 | 15 |
| Electrical Machinery | Electric Machines | 9 | 57 | 392 |
| Power Systems and Power Electronics | Power Electronics, Power Systems | 4 | 17 | 56 |
| Material Science | Structure of Materials, Thermodynamics and Kinetics of Materials, Mechanical Behavior of Materials, Electrical, Magnetic, Optical and Thermal Properties, Engineering Materials | 26 | 131 | 1,044 |
| Conventional Energy Technologies | Thermal Power Plant Engineering, Hydroelectric Power Engineering, Nuclear Power Engineering, Power Plant Economics and Operation, Non-Conventional Power and Energy Storage | 25 | 166 | 2,445 |
| **Total** | 53 | 302 | 1,498 | 21,096 |

Branch sizes: every branch has 3 to 13 subtopics, and 95% have 3 to 9, so each is a sensible unit to select.

## Decisions I made where the drafts overlapped

- **Itô calculus** has one home: *Stochastic Processes > Stochastic Calculus*. That branch holds the Itô integral, Itô's formula, SDEs and multidimensional Itô.
  - Quantitative Finance keeps the pricing that uses it.
  - Its subject bundle will include that branch, since subjects can pull in branches from another subject's topic.
- **Thermal expansion** lives in Thermodynamics. Material Science keeps *Thermal Shock and Thermal Stresses*, and Srinath's elasticity version is *Thermoelastic Stresses* in Mechanics.
- **Numerical methods** get a *Numerical Methods* branch in Calculus: root finding, numerical integration, and interpolation (Bernstein polynomials, Bézier curves, splines). Numerical ODEs stay in Differential Equations, and LU and Cholesky stay in Linear Algebra.
- **Phase plane:** oscillator questions (Van der Pol, phase paths) stay in Mechanics. General autonomous systems and limit cycles go to Differential Equations.
- **Countability** (including Hilbert's hotel) goes to Real Analysis > Real Numbers. Combinatorics keeps *Infinite Combinatorics*.
- **Rockets:** Gregory's and Kamal's go to Mechanics > Rocket Motion. White's control-volume rockets go to Fluid Mechanics.
- **Machines named by both sources.** Hydraulic turbines and similar machines appear in both Fluid Mechanics (White) and Conventional Energy Technologies (Rajput, Nag). They are named apart, per your rule that both power-plant books go to Conventional Energy Technologies.
- **Engel and other strategy books** are filed by content; the strategy becomes a tag.
  - Combinatorics keeps *Pigeonhole Principle* only for elementary "how many to guarantee" questions.
  - It keeps *Inclusion-Exclusion* as a branch because it is a counting formula with its own chapter.
- **Algorithmic and logic puzzles** are a topic inside Combinatorics, not a new subject. Real programming content is tiny, so the 4 SQL queries and about 25 trivia and riddle items go to the wastebasket.
- **Society of Actuaries:** all 701 are Exam P probability, filed by idea. Deductibles and benefit limits get their own subtopics, and there are no interest-theory items.
- **Smaller calls:**
  - Polynomial irreducibility goes to Abstract Algebra.
  - Floor-function questions go to Number Theory.
  - Gibbs phase rule goes to Material Science.
  - Diffusion in solids goes to Material Science, and diffusion in fluids to Heat Transfer.

## Settled with you (2026-11-02)

- Quantum Mechanics keeps what it has; nuclear content from the power-plant books stays in Conventional Energy Technologies.
- Conventional Energy Technologies keeps its name.
- Real Numbers and Sequences and Series moved from the Calculus topic to Real Analysis.
- **Tiny subtopics** (fewer than 3 questions after classification) merge into their nearest sibling, unless the size gap is a sampling artifact. The test, run once real counts exist:
  - keep the subtopic if a textbook in the bank teaches it as its own section (an exact table-of-contents match), or
  - keep it if a quick model check says a standard course in the subject teaches it as its own section;
  - otherwise merge it.

  Table-of-contents matching alone finds only a third of the standard sections, so the model check covers the rest.
- Tags carry a role: `key`, `supporting` (technique tags) or `task` (task tags such as "Point Finding"). This is database migration 007.
- Classification also fills the empty `type` column.
- After the Fluid Mechanics pilot:
  - added *Density and Ideal-Gas State* and *Flow Measurement Methods*;
  - widened *Dimensional Homogeneity* (units and unit conversion) and *Finite-Difference Methods for Flow Equations* (unsteady diffusion schemes);
  - sharpened the scope notes of six near-tie pairs.
- Questions that cite a figure missing from the bank stay visible. They are listed in `data_quality/missing_figures.csv`, regenerated with `tools/missing_figures.py`.

## Backlog

- **Student-recognizable names.** Some subtopic names are technical labels that suit classification but not a student who has just learned the concept without its name (for example "Archimedean Property and Density"). Rename them after classification so a student can recognize the idea from the name alone.

---
# The tree

# Calculus
_2 topic(s), 17 branches, 102 subtopics, ~1600 questions_

## Calculus
### Single Variable Differential Calculus
- **Limits (Single Variable)** — limits of functions, indeterminate forms, L'Hôpital, standard limits, big-O comparison (~42)
- **Continuity (Single Variable)** — continuity at points, discontinuities, extreme value theorem, monotone and semicontinuous functions (~32)
- **Uniform Continuity** — uniform and Lipschitz continuity on intervals and subsets of R^n (~7)
- **Intermediate Value Theorem** — existence of roots and fixed points on intervals, universal chord theorem (~20)
- **Differentiability (Single Variable)** — derivative from the definition, piecewise functions, Darboux's theorem, pathological derivatives (~20)
- **Differentiation Rules** — product, quotient and chain rules; implicit, logarithmic and higher derivatives (~6)
- **Mean Value Theorems** — Rolle, Lagrange and Cauchy mean value theorems and their consequences (~36)
- **Taylor's Theorem** — Taylor polynomials with remainder, error bounds, local approximation (~16)
- **Maxima and Minima (Single Variable)** — critical points, extrema of one-variable functions, optimization word problems (~11)
- **Curve Sketching** — monotonicity, concavity, inflection points, asymptotes, counting real roots by calculus (~20)
- **Convex Functions** — convexity and concavity, derivative tests, properties; Jensen's inequality itself is Algebra (~8)
- **Inequalities Using Derivatives** — inequalities proved by monotonicity or MVT; comparisons like e^pi vs pi^e (~30)
- **Parametric and Polar Curves** — tangents, normals and derivatives of parametric, polar and implicit plane curves (~4)
### Single Variable Integral Calculus
- **Riemann Integrability** — Darboux sums, integrability criteria, Lebesgue criterion, non-integrable examples (~22)
- **Riemann Sums** — limits of sums evaluated as definite integrals (~13)
- **Fundamental Theorem of Calculus** — derivatives of integrals with variable limits, antiderivatives (~5)
- **Techniques of Integration** — substitution, parts, partial fractions, reduction formulas, indefinite integrals (~14)
- **Properties of Definite Integrals** — symmetry, the f(a+b-x) trick, periodicity, vanishing-integral lemmas (~28)
- **Mean Value Theorems for Integrals** — first and second mean value theorems, Bonnet form, intermediate points (~20)
- **Integral Inequalities** — Cauchy-Schwarz, Hölder, Chebyshev, Young, Steffensen, Opial for integrals; derivative-based integral bounds (~70)
- **Limits Involving Integrals** — limits of integrals depending on n or x, Laplace-type asymptotics (~35)
- **Area of Plane Regions** — area between curves and in polar coordinates (~10)
- **Volumes and Surfaces of Revolution** — disc, shell and surface-of-revolution formulas (~9)
- **Arc Length** — length of plane and space curves in Cartesian, parametric or polar form (~12)
### Improper and Parametric Integrals
- **Convergence of Improper Integrals** — comparison, Dirichlet and Abel tests, absolute and conditional convergence (~35)
- **Evaluation of Improper Integrals** — Gaussian, Dirichlet, Fresnel, Frullani, log-sine integrals; residue methods: see Complex Analysis (~10)
- **Differentiation Under the Integral Sign** — Leibniz rule; uniform convergence and continuity of parameter integrals (~22)
- **Beta and Gamma Functions** — Gamma and Beta properties, duplication formula, Stirling's formula (~20)
### Multivariable Differential Calculus
- **Limits (Multivariable)** — limits in R^n, path tests, iterated limits (~10)
- **Continuity (Multivariable)** — continuity of functions on R^n (~16)
- **Partial Derivatives** — computing partials, higher and mixed partials, equality of mixed partials (~14)
- **Differentiability (Multivariable)** — total derivative, sufficient conditions, partials existing without differentiability (~28)
- **Chain Rule (Multivariable)** — chain rule, change of variables in differential expressions, polar Laplacian (~12)
- **Euler's Theorem on Homogeneous Functions** — homogeneous functions and Euler's identity (~7)
- **Gradient and Directional Derivatives** — gradient, directional derivatives, steepest ascent (~12)
- **Tangents and Normals (Multivariable)** — tangent planes, normal lines, angle between surfaces (~8)
- **Functional Dependence** — Jacobian test for functional dependence (~3)
- **Implicit Function Theorem** — local solvability of F(x,y)=0, implicit partial derivatives (~8)
- **Inverse Function Theorem** — local invertibility, Jacobian rank conditions, global injectivity (~10)
- **Taylor's Theorem (Multivariable)** — Taylor expansions and quadratic approximations in several variables (~8)
- **Matrix Calculus** — gradients of vector- and matrix-valued functions, backpropagation identities (~7)
### Multivariable Integral Calculus
- **Double and Triple Integrals** — iterated integrals, Fubini, changing the order of integration (~26)
- **Jacobian and Change of Variable** — Jacobian determinants; polar, cylindrical, spherical and linear substitutions (~18)
- **Volumes of Solids** — volumes by slicing or multiple integrals; excludes solids of revolution (~14)
- **Surface Area** — area of graphs and parametrised surfaces (~9)
- **Mass, Centroids and Moments of Inertia** — mass, center of mass, moments of inertia, Pappus's theorem (~9)
### Vectors and Space Curves
- **Dot and Cross Products** — dot, cross and triple products, vector identities, vector equations (~11)
- **Vector-Valued Functions** — derivatives of r(t), velocity, acceleration, reparametrisation by arc length (~11)
- **Curvature and the Frenet Frame** — unit tangent, normal, binormal, curvature and torsion of curves (~11)
### Vector Calculus
- **Divergence and Curl** — grad, div, curl identities; irrotational and solenoidal fields (~8)
- **Line Integrals** — line integrals of scalar and vector fields, work (~10)
- **Conservative Vector Fields** — potentials, path independence, fields on punctured domains (~7)
- **Green's Theorem** — Green's theorem in the plane, area by line integrals (~12)
- **Surface Integrals** — parametrised surfaces, scalar surface integrals, flux (~7)
- **Stokes' Theorem** — Stokes' theorem and circulation (~7)
- **Divergence Theorem** — Gauss divergence theorem, flux through closed surfaces (~10)
### Optimization
- **Maxima and Minima (Multivariable)** — critical points, second-derivative test, saddle points, extrema on closed regions (~16)
- **Lagrange Multipliers** — extrema under equality constraints (~18)
- **Linear Programming** — standard form, graphical solution, LP duality (~3)
- **Convex Optimization and Duality** — convex sets, Lagrangian duality, KKT, quadratic programs, gradient descent (~6)
### Numerical Methods
- **Numerical Differentiation and Integration** — finite differences; trapezoidal, midpoint and Simpson rules with error estimates (~10)
- **Root Finding and Newton's Method** — bisection, Newton and secant methods, fixed-point iteration for equations, order of convergence
- **Interpolation and Approximation** — Lagrange interpolation, Bernstein polynomials, Bézier curves, splines

## Real Analysis
### Real Numbers
- **Infimum and Supremum** — sup and inf of sets, least upper bound property, completeness of R (~8)
- **Archimedean Property and Density** — Archimedean property; density of rationals, irrationals, and sets like {n·alpha mod 1} (~8)
- **Countable and Uncountable Sets** — countability of Q, uncountability of R, Hilbert's hotel, cardinality arguments (~4)
### Sequences and Series
- **Convergence (Sequences)** — limits of explicit sequences, squeeze, Stolz-Cesàro, limsup; excludes recursions (see Monotone and Recursive Sequences) (~65)
- **Monotone and Recursive Sequences** — x(n+1)=f(x(n)), monotone convergence theorem, nested radicals, power towers (~62)
- **Iterated Means and Coupled Recursions** — simultaneous recursions, arithmetic-geometric and arithmetic-harmonic means (~16)
- **Cauchy Criterion** — Cauchy and contractive sequences of reals; metric-space completeness: see Complete Metric Spaces (~4)
- **Convergence (Series)** — comparison, ratio, root, integral and condensation tests for series (~31)
- **Absolute and Conditional Convergence** — alternating series, Leibniz, Dirichlet and Abel tests, rearrangements (~6)
- **Summation of Series** — exact sums of infinite series (telescoping, arctan sums); finite sums are Algebra (~16)
- **Infinite Products** — convergence and value of infinite products (~9)
- **Power Series and Radius of Convergence** — real power series, interval of convergence, term-by-term integration; complex z: see Complex Analysis (~14)
- **Taylor and Maclaurin Series** — series expansions of functions and their convergence; remainder bounds: see Taylor's Theorem (~12)
### Metric Spaces and Topology
- **Open and Closed Sets** — open, closed, dense and G-delta sets in R^n and metric spaces (~10)
- **Compactness** — Heine-Borel, Bolzano-Weierstrass, continuous maps on compact sets (~13)
- **Connectedness** — connected and path-connected sets, continuous images of connected sets (~6)
- **Complete Metric Spaces** — Cauchy sequences in metric spaces, completeness, Baire category theorem (~7)
- **Contraction Mapping and Fixed Points** — Banach fixed-point theorem, Brouwer, integral equations solved by iteration (~12)
### Sequences and Series of Functions
- **Uniform Convergence** — pointwise vs uniform convergence, M-test, Dini, interchanging limits with integrals or derivatives (~18)
- **Arzelà-Ascoli Theorem** — equicontinuity, compact families of continuous functions (~6)
- **Weierstrass Approximation Theorem** — polynomial approximation, Bernstein polynomials, Stone-Weierstrass, Müntz (~19)
### Bounded Variation and Stieltjes Integration
- **Functions of Bounded Variation** — total variation, Jordan decomposition, Helly selection theorem (~28)
- **Riemann-Stieltjes Integral** — existence, evaluation and properties of integrals with respect to an integrator (~30)
- **Absolutely Continuous Functions** — absolute continuity, Banach-Zarecki theorem, singular functions (~16)
### Measure Theory
- **Jordan Measure** — Jordan content and Jordan measurable sets (~19)
- **Lebesgue Outer Measure and Measurable Sets** — outer measure, Carathéodory measurability, regularity, Borel sets (~30)
- **Non-Measurable Sets** — Vitali sets, measurable non-Borel sets (~9)
- **Cantor Sets and Sets of Measure Zero** — Cantor-type sets, nowhere dense sets, sets defined by digits (~15)
### Lebesgue Integration
- **Measurable Functions** — measurability, compositions, Lusin's theorem (~22)
- **Convergence in Measure and Egorov's Theorem** — modes of convergence, Egorov, Riesz subsequence theorem (~15)
- **Lebesgue Integral** — definition and basic properties, comparison with the Riemann integral (~13)
- **Monotone and Dominated Convergence Theorems** — monotone convergence, Fatou, dominated convergence, incl. Riemann-integral versions (~16)
- **Lp Spaces** — Lp norms, Hölder and Minkowski in Lp, density of continuous functions (~15)
- **Lebesgue Differentiation Theorem** — Lebesgue points, density points, approximate continuity (~16)
### Fourier Series
- **Fourier Series Expansions** — computing Fourier series, summing trigonometric series from expansions (~16)
- **Convergence of Fourier Series** — Dirichlet kernel, Dini and Dirichlet-Jordan tests, Lebesgue constants, divergence (~16)
- **Fourier Coefficients and the Riemann-Lebesgue Lemma** — decay of coefficients, uniqueness, term-by-term integration (~15)
- **Parseval's Identity and Bessel's Inequality** — L2 theory of Fourier series, sums via Parseval (~10)
- **Fejér's Theorem and Cesàro Means** — Fejér kernel, Cesàro summability, Fatou and Wiener theorems (~10)


# Complex Analysis
_1 topic(s), 4 branches, 18 subtopics, ~183 questions_

## Complex Analysis
### Analytic Functions
- **Cauchy-Riemann Equations** — complex differentiability, Cauchy-Riemann equations, Wirtinger derivatives (~13)
- **Complex Exponential and Logarithm** — exp, log, complex powers, branches; algebraic and polar forms are Algebra (~7)
- **Harmonic Functions** — harmonic conjugates, mean value property, positive and bounded harmonic functions (~8)
- **Power Series in a Complex Variable** — radius of convergence, Taylor expansion of analytic functions, uniform limits (~20)
- **Identity Theorem and Analytic Continuation** — uniqueness of analytic functions, zeros, reflection principle (~11)
### Complex Integration
- **Contour Integrals** — parametrised contour integrals, ML estimate (~5)
- **Cauchy's Theorem and Morera's Theorem** — Cauchy-Goursat, existence of primitives and logarithms, Morera (~7)
- **Cauchy's Integral Formula** — integral formula, Cauchy estimates, mean value property (~7)
- **Liouville's Theorem and Entire Functions** — Liouville, growth conditions, fundamental theorem of algebra, automorphisms of C (~19)
- **Maximum Modulus Principle** — maximum modulus and open mapping theorems (~6)
### Singularities and Residues
- **Laurent Series** — Laurent expansions in annuli (~6)
- **Isolated Singularities** — removable singularities, poles, essential singularities, Casorati-Weierstrass (~6)
- **Residue Theorem** — computing residues, contour integrals by residues (~12)
- **Real Integrals by Residues** — real definite and improper integrals by contour integration (~10)
- **Argument Principle and Rouché's Theorem** — counting and locating zeros (~21)
### Conformal Mapping
- **Möbius Transformations** — fractional linear maps, images of lines, circles and half-planes (~6)
- **Conformal Maps of Regions** — mapping regions onto discs and half-planes, images and areas of regions (~9)
- **Schwarz Lemma** — Schwarz and Schwarz-Pick lemmas, automorphisms of the disc (~10)


# Linear Algebra and Differential Equations
_2 topic(s), 19 branches, 89 subtopics, ~992 questions_

## Linear Algebra
### Matrix Algebra
- **Matrix Operations** — products, transposes, direct powers, triangular and diagonal matrices; excludes inverses (~21)
- **Symmetric, Skew-Symmetric and Hermitian Matrices** — definitions, decompositions, algebraic facts; spectral results see Spectral Theorem (~8)
- **Inverse of a Matrix** — invertibility criteria, Gauss-Jordan inversion, inverse identities, Sherman-Morrison updates (~24)
- **Nilpotent Matrices** — A^k = 0, invertibility of I + A, structure of nilpotent operators (~11)
- **Idempotent Matrices and Projections** — A^2 = A, oblique projections; orthogonal projections see Orthogonality (~5)
- **Trace of a Matrix** — tr(AB) = tr(BA), trace identities, trace as a linear functional (~6)
### Systems of Linear Equations
- **Elementary Matrices and Row Equivalence** — elementary matrices, row equivalence, factoring into elementary matrices, PAQ normal form (~5)
- **Gaussian Elimination (RREF)** — reducing to echelon form, solving given systems; inverses see Inverse of a Matrix (~18)
- **Rank of a Matrix** — row rank equals column rank, computing rank, rank inequalities (~8)
- **Consistency of Linear Systems** — parameters giving none, one or infinitely many solutions; homogeneous systems (~10)
### Determinants
- **Determinant Properties** — permutation definition, row-operation effects, multiplicativity, transpose, block matrices (~22)
- **Determinant Evaluation** — cofactor expansion, patterned matrices, Vandermonde, circulant, parity and divisibility arguments (~20)
- **Adjugate and Cramer's Rule** — adjugate matrix, inverse via cofactors, Cramer's rule (~9)
### Vector Spaces
- **Vector Space Axioms** — verifying axioms, unusual operations, function and matrix spaces (~8)
- **Subspaces** — subspace tests, span, unions of subspaces; sums see Sums and Direct Sums (~17)
- **Sums and Direct Sums of Subspaces** — U + W, U ∩ W, dimension formula, complements, direct sums (~24)
- **Linear Independence** — testing sets of vectors and functions, independence over R versus C (~22)
- **Basis and Dimension** — extending to a basis, Steinitz exchange lemma, dimension of given spaces (~26)
### Linear Transformations
- **Linearity of a Map** — deciding linearity, R- versus C-linearity, compositions of linear maps (~10)
- **Kernel and Range of a Transformation** — computing kernel and range, injectivity, surjectivity, prescribed range (~23)
- **Rank-Nullity Theorem** — dim ker + dim im = dim V, ranks of compositions (~17)
- **Matrix of a Linear Transformation** — matrix relative to bases, change of basis, transition matrices (~17)
- **Dual Spaces** — dual basis, annihilators, dual maps and transposes (~15)
### Eigenvalues and Diagonalization
- **Eigenvalues and Eigenvectors** — characteristic polynomial, eigenspaces, eigenvalues of patterned matrices (~31)
- **Properties of Eigenvalues** — eigenvalues of inverse, transpose, p(A), AB versus BA; nonnegative matrices (~27)
- **Diagonalizability** — deciding diagonalizability, finding P, powers of a given diagonalizable matrix (~23)
- **Simultaneous Diagonalization** — commuting matrices, common eigenvectors, matrices commuting with a given A (~12)
- **Gershgorin Discs and Diagonal Dominance** — locating eigenvalues, invertibility of diagonally dominant matrices (~9)
- **Matrix Norms and Spectral Radius** — operator norms, spectral radius, convergence of A^k, Neumann series (~8)
### Canonical Forms
- **Cayley-Hamilton Theorem** — statement and proof, inverses and powers as polynomials in A (~9)
- **Minimal Polynomial** — computing it, relation to characteristic polynomial, diagonalizability criterion (~11)
- **Invariant Subspaces and Triangularization** — invariant and generalized eigenspaces, primary decomposition, Schur triangularization (~10)
- **Jordan Normal Form** — Jordan blocks, computing the Jordan form, operators on polynomial spaces (~23)
- **Similarity of Matrices** — deciding similarity, similarity invariants, classification up to similarity (~10)
- **Functions of a Matrix** — square roots, polynomial equations in A, finite order, exponential series (~23)
### Inner Product Spaces
- **Inner Products** — axioms, matrix of an inner product, function-space inner products, Riesz representation (~18)
- **Norms, Distances and Angles** — norm properties, distances and angles between vectors, equiangular sets (~9)
- **Adjoint and Normal Operators** — adjoint maps, self-adjoint, skew-adjoint and normal operators (~9)
- **Spectral Theorem** — orthonormal eigenbases for symmetric, Hermitian and normal maps; orthogonal diagonalization (~10)
### Orthogonality
- **Gram-Schmidt Process** — orthonormalizing a basis, QR factorization (~6)
- **Orthogonal Projections and Complements** — U-perp, V = U ⊕ U-perp, projection onto a subspace, distances (~8)
- **Least Squares Approximation** — normal equations, least squares as projection; regression models see Statistics (~2)
- **Orthogonal and Unitary Matrices** — characterizations, rotations, reflections, isometries of R^n (~20)
### Bilinear and Quadratic Forms
- **Bilinear Forms** — matrix, congruence, nondegeneracy, alternating forms, sesquilinear and Hermitian forms (~13)
- **Diagonalization of Quadratic Forms** — associated bilinear form, diagonal bases, completing squares (~8)
- **Sylvester's Law of Inertia** — rank and signature, congruence classification of real forms (~7)
- **Positive Definite Matrices** — definiteness tests, correlation matrices, square roots; Cholesky computation see Cholesky Decomposition (~21)
### Matrix Decompositions
- **LU Decomposition** — LU with and without pivoting, banded and tridiagonal solvers, operation counts (~14)
- **Cholesky Decomposition** — Cholesky factor, banded Cholesky, efficient implementation (~9)
- **Singular Value Decomposition** — computing the SVD, low-rank approximation, polar decomposition (~7)

## Differential Equations
### First-Order ODEs
- **Separable ODE** — y' = f(x)g(y) by separating variables; PDEs see Separation of Variables (~4)
- **Linear ODE (Integrating Factor)** — y' + p(x)y = q(x) solved with an integrating factor (~7)
- **Bernoulli ODE** — Bernoulli and Riccati equations, substitutions reducing to linear form (~5)
- **Homogeneous ODE (Substitution)** — y' = f(y/x) and equations reducible to it by shifting origin (~5)
- **Exact ODE** — exactness test, integrating factors that make an equation exact (~19)
- **Modeling with First-Order ODEs** — growth and decay, cooling, mixing, orthogonal trajectories, curves from tangent properties (~15)
- **Existence and Uniqueness** — Picard-Lindelöf theorem, Lipschitz condition, intervals of existence, non-uniqueness (~40)
- **Picard's Iteration** — computing successive approximations and their convergence (~10)
- **Numerical Methods for ODEs** — Euler and Runge-Kutta methods, finite-difference discretization of ODEs (~6)
### Higher-Order Linear ODEs
- **Wronskian and Solution Spaces** — Wronskian, Abel's formula, fundamental sets, dimension of solution space, superposition (~15)
- **Homogeneous Constant-Coefficient Equations** — characteristic equation of any order, repeated and complex roots (~11)
- **Undetermined Coefficients** — particular solutions, annihilator and D-operator methods, steady-state forced oscillations (~11)
- **Variation of Parameters** — particular solutions of scalar equations via Wronskian formulas (~8)
- **Reduction of Order** — second solution from a known one; equations y'' = f(y, y') (~5)
- **Euler-Cauchy Equations** — equidimensional equations of any order, substitution x = e^t (~5)
- **Sturm-Liouville and Boundary Value Problems** — two-point BVPs, eigenvalue problems, self-adjoint form, maximum principle (~7)
### Laplace Transforms
- **Transform Properties and Shifting Theorems** — computing transforms, first shifting, multiplication by t, periodic functions (~7)
- **Step and Impulse Functions** — Heaviside and Dirac delta, second shifting theorem, piecewise inputs (~4)
- **Inverse Laplace Transform** — partial fractions, logarithm and arctangent inverses, differentiation in s (~7)
- **Convolution Theorem** — convolution integrals, inverses via convolution, Volterra integral equations (~6)
- **Solving IVPs with Laplace Transforms** — scalar and system IVPs, including discontinuous and impulsive forcing (~8)
### Series Solutions
- **Power Series Solutions** — series about ordinary points, recurrences for coefficients (~2)
- **Frobenius Method** — classifying singular points, indicial equation, series about regular singular points (~4)
- **Legendre Polynomials** — Legendre equation, Rodrigues' formula, orthogonality, recurrences (~1)
- **Bessel Functions** — Bessel equation, recurrences and identities, equations reducible to Bessel form (~3)
### Systems of Linear ODEs
- **Homogeneous System of ODEs** — x' = Ax by eigenvalues and eigenvectors, scalar equations rewritten as systems (~12)
- **Nonhomogeneous System of ODEs** — x' = Ax + f by undetermined coefficients or variation of parameters (~5)
- **Fundamental Matrix and Matrix Exponential** — fundamental matrices, e^(At), Liouville's formula; e^A as series see Functions of a Matrix (~6)
### Stability and Qualitative Theory
- **Phase Portraits and Limit Cycles** — classifying equilibria, linearization, plane autonomous systems, limit cycles, Poincaré-Bendixson (~8)
- **Lyapunov Functions and Energy Methods** — functions decreasing or conserved along trajectories, asymptotic stability (~5)
- **Asymptotic Behavior of Linear Systems** — boundedness, decay and norm growth for x' = A(t)x without solving (~8)
- **Qualitative Behavior of Solutions** — comparison, bounds, blow-up, global existence, zeros of solutions of nonlinear ODEs (~15)
### Partial Differential Equations
- **Separation of Variables** — heat, wave and Laplace equations on bounded domains by Fourier series (~0)
- **Fundamental Solution of the Heat Equation** — heat kernel, Green's functions, reducing parabolic PDEs to the heat equation (~7)
- **d'Alembert's Solution of the Wave Equation** — wave equation on the line, traveling-wave solutions (~0)
- **First-Order PDEs and Characteristics** — linear and quasilinear first-order PDEs, Lagrange's method, characteristic curves (~0)
### Calculus of Variations
- **Euler-Lagrange Equation** — extremals of functionals with fixed endpoints, first integrals (~5)
- **Geodesics and Minimal Surfaces** — shortest paths on surfaces, soap films, catenary-type problems (~3)
- **Constrained Variational Problems** — isoperimetric problems, Lagrange multipliers for functionals (~0)


# Algebra
_4 topic(s), 17 branches, 68 subtopics, ~1212 questions_

## Elementary Algebra
### Algebraic Expressions and Radicals
- **Factoring and Algebraic Identities** — factoring expressions and polynomials, Sophie Germain, a³+b³+c³−3abc; excludes irreducibility proofs (~30)
- **Conditional Evaluation of Expressions** — evaluate an expression given constraints such as x+1/x=1 or a+b+c=0 (~25)
- **Simplifying and Denesting Radicals** — nested radicals, rationalising denominators, comparing surd sums without a calculator (~25)
- **Rationality of Algebraic Numbers** — proving sums of roots rational or irrational, √2+∛3, minimal integer equations (~12)
- **Powers of Conjugate Surds** — (a+√b)ⁿ+(a−√b)ⁿ integral; integer parts and decimals of such powers (~20)
### Exponentials and Logarithms
- **Laws of Logarithms** — evaluating and simplifying log expressions, change of base (~12)
- **Logarithmic Equations and Systems** — equations and systems with unknowns inside or in the base of logs (~28)
- **Exponential Equations and Inequalities** — equations such as 4ˣ+9ˣ+49ˣ=6ˣ+14ˣ+21ˣ; excludes growth word settings (~18)
### Equations and Systems
- **Quadratic Equations and Functions** — discriminant, vertex, sign and root location of quadratics; excludes Vieta (see Vieta's Formulas) (~18)
- **Rational Equations** — equations with algebraic fractions, partial-fraction collapses (~8)
- **Radical Equations** — equations and inequations with square or higher roots of the unknown (~15)
- **Absolute Value Equations** — equations with nested or several absolute values, piecewise reasoning (~10)
- **Solving Inequalities in One Variable** — solution sets of rational, radical and exponential inequalities; excludes proving inequalities (~10)
- **Systems of Nonlinear Equations** — symmetric, cyclic and radical systems in several unknowns (~50)
### Functions and Graphs
- **Domain, Range and Composition** — domains, ranges, compositions and inverses of explicit functions (~12)
- **Symmetry and Periodicity of Functions** — even, odd, periodic functions; f(a+x)=f(a−x) symmetry of graphs (~10)
- **Graphical Solution of Equations** — counting real solutions of fixed transcendental or mixed equations via graphs (~20)
- **Equations with a Parameter** — parameter values giving a prescribed number or type of solutions (~15)
### Algebraic Modeling
- **Rate, Time and Distance** — uniform motion, meeting and overtaking, escalators, clock hands (~38)
- **Work and Rates of Production** — joint work, pipes, workers, cows eating grass (~10)
- **Mixtures and Concentrations** — mixing solutions, alternate pouring between vessels (~8)
- **Percentages, Ratios and Averages** — percent change, ratios, means of data lists; excludes interest theory (Quantitative Finance) (~18)
- **Ages, Money and Sharing** — linear equations from verbal conditions on ages, coins, prices, shares (~35)
### Trigonometric Identities and Equations
- **Trigonometric Identities** — addition, multiple-angle and power identities; excludes identities in a triangle (Geometry) (~15)
- **Trigonometric Equations** — solving trigonometric equations and systems (~12)
- **Trigonometric Sums and Products** — closed forms for Σ sin kθ, Π sin(kπ/n), trig telescoping (~15)
- **Inverse Trigonometric Functions** — arctan addition, sums of arctan or arccos terms (~12)
### Complex Numbers
- **Algebraic and Polar Form** — arithmetic, modulus, conjugate, argument, polar representation; excludes complex functions (~15)
- **De Moivre's Theorem** — powers and roots via polar form, z+1/z=2cos θ (~10)
- **Roots of Unity** — properties, sums and products over roots of unity, roots-of-unity filter (~25)

## Theory of Polynomials
### Roots of Polynomials
- **Vieta's Formulas** — relations between roots and coefficients, polynomials with transformed roots (~35)
- **Symmetric Polynomials and Newton's Sums** — power sums, elementary symmetric functions, antisymmetric polynomials (~18)
- **Multiple Roots** — conditions for double roots, (x−1)² dividing a polynomial (~8)
- **Real Roots and Descartes' Rule of Signs** — counting or excluding real and positive roots (~12)
- **Location of Complex Roots** — proving |z|=1 or bounds for roots, conjugate root pairs (~15)
### Polynomial Division and Integer Coefficients
- **Polynomial Division and Remainders** — remainder theorem, divisibility of polynomials such as x²+x+1 | f(x) (~20)
- **Integer Polynomials and Divisibility** — a−b | P(a)−P(b), integer-valued polynomials, P(a)=b cycles (~22)
- **Rational Root Theorem** — rational and integer roots of integer polynomials (~8)
### Polynomial Identities and Bounds
- **Polynomial Functional Equations** — find all polynomials with P(x²)=P(x)P(x+1) and similar (~20)
- **Lagrange Interpolation and Finite Differences** — polynomials fixed by values, P(k)=k/(k+1), difference operators (~10)
- **Coefficients of Polynomial Expansions** — sums of coefficients, coefficients of products; excludes binomial identities (Combinatorics) (~10)
- **Chebyshev Polynomials and Minimax Bounds** — Tₙ identities, bounds of polynomials on [−1,1] (~18)
- **Nonnegative Polynomials** — polynomials nonnegative on R or an interval, sum-of-squares representations (~8)

## Algebraic Inequalities
### Mean Inequalities
- **AM-GM Inequality** — AM-GM-HM, products under sum constraints (includes Kaczor-Nowak AM-GM set) (~40)
- **Power Means and Weighted Means** — power-mean, weighted AM-GM, Young-type bounds (~12)
- **Bernoulli's Inequality** — (1+x)ⁿ ≥ 1+nx and Weierstrass product inequalities (~8)
### Cauchy-Schwarz and Related Inequalities
- **Cauchy-Schwarz Inequality** — Cauchy-Schwarz, Engel form, Kantorovich-type ratios (~30)
- **Hölder's Inequality** — Hölder and its generalised-product forms (~5)
- **Triangle and Minkowski Inequalities** — |a+b| ≤ |a|+|b|, Minkowski sums of square roots (~12)
### Ordering and Convexity Inequalities
- **Rearrangement and Chebyshev Sum Inequalities** — similarly ordered sequences, rearrangement, Chebyshev's sum inequality (~10)
- **Schur's Inequality** — Schur's inequality and its degree variants (~5)
- **Jensen's Inequality** — convexity of a function applied to sums; excludes proofs by derivatives (Calculus) (~8)
### Symmetric, Cyclic and Extremal Inequalities
- **Symmetric Polynomial Inequalities** — symmetric inequalities in a, b, c, e.g. a²+b²+c² ≥ ab+bc+ca (~22)
- **Cyclic and Fractional Inequalities** — Nesbitt and Shapiro-type cyclic fraction sums (~15)
- **Bounding Sums and Products** — bounds for harmonic sums, n!, binomial products, mediant inequality (~20)
- **Extremal Values and Best Constants** — max or min under constraints by inequalities, best constants; excludes calculus optimization (~35)

## Sequences, Sums and Functional Equations
### Progressions and Finite Sums
- **Arithmetic Progressions** — terms and sums of arithmetic progressions (~10)
- **Geometric Progressions and Series** — finite and infinite geometric sums; excludes convergence tests (Calculus) (~15)
- **Telescoping Sums and Products** — partial fractions, telescoping finite and infinite sums; excludes trig telescoping (~30)
- **Sums of Powers and Closed Forms** — Σk², Σk³, Σk·k!, closed forms of finite sums (~12)
### Recursive Sequences
- **Linear Recurrences with Constant Coefficients** — characteristic equation, closed forms; excludes setting up counting recurrences (Combinatorics) (~25)
- **Nonlinear Recursive Sequences** — rational or radical recursions, integrality of terms, invariants of recursions (~35)
- **Periodic Sequences** — recursions whose terms repeat, finding a far term by periodicity (~8)
### Functional Equations
- **Cauchy's Functional Equation** — additive, multiplicative and Jensen-type equations, regularity conditions (~15)
- **Equations over the Reals** — two-variable functional equations on R, Q or R⁺ (~30)
- **Functional Equations on the Integers** — functions N→N or Z→Z defined by equations or monotonicity (~20)
- **One-Variable Substitution Equations** — f(x)+g(x)f(φ(x))=h(x) with φ an involution or cyclic map (~10)
- **Iterated Functions** — closed forms for fⁿ(x), functional roots, periodic points of iteration (~25)


# Abstract Algebra
_2 topic(s), 6 branches, 22 subtopics, ~221 questions_

## Group Theory
### Groups and Subgroups
- **Binary Operations and Group Axioms** — verifying group axioms, semigroups, groupoids, operations on sets (~12)
- **Subgroups, Cosets and Lagrange's Theorem** — subgroup tests, cosets, index, unions of subgroups (~9)
- **Cyclic Groups and Element Orders** — cyclic groups, generators, orders of elements and products (~10)
- **Generators, Relations and Free Groups** — presentations, free groups, finitely generated groups (~6)
### Homomorphisms and Group Structure
- **Homomorphisms and Isomorphism Theorems** — homomorphisms, kernels, isomorphism theorems, counting homomorphisms (~7)
- **Automorphism Groups** — Aut(G), fixed-point-free automorphisms, automorphisms of Q or Zₚ (~10)
- **Normal Subgroups and Quotient Groups** — normality, quotients, commutator subgroup, centralisers (~13)
- **Abelian Groups and Direct Products** — direct products, finite and infinite abelian groups, Q/Z, torsion (~10)
- **Solvable and Nilpotent Groups** — solvable, nilpotent, p-groups and infinite group structure (~5)
### Finite Groups and Group Actions
- **Symmetric, Alternating and Dihedral Groups** — permutations, cycles, parity, Sₙ, Aₙ, Dₙ subgroups (~22)
- **Group Actions and Conjugacy Classes** — conjugacy classes, transitive actions, orbit-stabiliser (~6)
- **Sylow Theorems and Groups of Small Order** — Sylow subgroups, classifying groups of order pq or 2p (~8)
- **Matrix Groups over Fields** — GL₂(Fₚ), SO(n), groups of matrices and their orders (~7)

## Ring and Field Theory
### Rings and Ideals
- **Rings, Subrings and Units** — ring axioms, units, zero divisors, idempotents, finite rings; also gaussian integers, cyclotomic integers, p-adic numbers (~14)
- **Ideals and Quotient Rings** — ideals, maximal and prime ideals, quotients, ring homomorphisms (~13)
- **Integral Domains, PIDs and UFDs** — integral domains, Euclidean domains, PIDs, unique factorisation (~5)
### Polynomial Rings
- **Ideals in Polynomial Rings** — ideals and quotients of Z[x], F[x], Q[x,y] (~11)
- **Irreducibility Criteria** — Eisenstein, reduction mod p, irreducibility over Q or Z (~18)
- **Factorization over Finite Fields** — factoring in Zₚ[x], counting irreducible polynomials (~7)
### Fields and Extensions
- **Algebraic Extensions and Minimal Polynomials** — degree of extensions, minimal polynomials, quadratic and transcendental extensions (~12)
- **Finite Fields** — structure and counting in finite fields, Frobenius, characteristic p (~11)
- **Multiplicative Groups of Fields** — finite subgroups of F* cyclic, roots of unity in a field (~5)


# Number Theory
_2 topic(s), 13 branches, 67 subtopics, ~1843 questions_

## Elementary Number Theory
### Divisibility and Greatest Common Divisor
- **Division Algorithm and Residue Forms** — a=qb+r, squares of the form 3k or 3k+1; also subsets with sum divisible by n, Erdős-Ginzburg-Ziv (~30)
- **Divisibility of Integer Expressions** — prove m | f(n) for all n; excludes Fermat-based proofs (see Fermat's Little Theorem) (~45)
- **GCD and LCM** — properties of gcd and lcm, coprimality, fractions in lowest terms (~55)
- **Euclidean Algorithm and Bézout's Identity** — computing gcd, expressing gcd as a combination (~15)
### Primes and Prime Factorization
- **Fundamental Theorem of Arithmetic** — unique factorisation and its consequences, powerful numbers (~15)
- **Infinitude of Primes** — Euclid-type proofs, primes of forms 4k+3 or 6k+5 (~15)
- **Distribution of Primes** — sieve, prime gaps, Bertrand, π(n), Goldbach and twin-prime statements (~30)
- **Primality Conditions on Expressions** — find primes p with p²+8 prime; equations whose unknowns are primes (~45)
- **Proving Numbers Composite** — compositeness via factorisation identities such as n⁴+4 (~25)
- **Prime Divisors of Sequences and Polynomials** — prime factors of aⁿ−1 or n²+n+1, infinitely many prime divisors (~55)
- **Legendre's Formula and Factorials** — exponent of p in n!, trailing zeros (~30)
- **p-adic Valuation and Lifting the Exponent** — vₚ of aⁿ−bⁿ, largest power of p dividing an expression (~15)
- **Prime Divisors of Binomial Coefficients** — Kummer, Lucas, divisibility of central binomial coefficients; excludes binomial identities (~22)
### Congruences
- **Congruence Properties and Residue Systems** — rules of congruences, complete and reduced residue systems (~25)
- **Remainders and Last Digits of Powers** — last digits and remainders of large powers and towers (~50)
- **Linear Congruences** — solving ax ≡ b (mod n) and linear systems of congruences (~10)
- **Chinese Remainder Theorem** — simultaneous congruences, remainder puzzles (~40)
- **Fermat's Little Theorem** — aᵖ ≡ a (mod p) and its applications (~40)
- **Euler's Theorem** — a^φ(n) ≡ 1 (mod n) and its applications (~10)
- **Wilson's Theorem** — (p−1)! ≡ −1 (mod p) and factorial congruences (~12)
- **Calendar and Day-of-Week Calculations** — weekday of a date, calendar cycles, leap years (~15)
### Arithmetic Functions
- **Number of Divisors** — τ(n), counting divisors, locker and switch settings (~35)
- **Sum of Divisors** — σ(n) and σₖ(n) identities and inequalities (~20)
- **Conditions on the Divisors of n** — equations on ordered divisors d₁<d₂<…, divisor-structure conditions (~35)
- **Euler's Totient Function** — φ(n) formula, values, equations and inequalities (~45)
- **Multiplicative Functions and Möbius Inversion** — multiplicativity, μ, Möbius inversion, Dirichlet sums (~30)
### Orders and Primitive Roots
- **Order of an Integer Modulo n** — ordₙ(a), n | aⁿ+1 type conditions (~30)
- **Primitive Roots** — existence, finding primitive roots for primes and composites (~30)
- **Indices and Power Residues** — index tables, solving xᵏ ≡ a (mod p) (~12)
### Quadratic Residues and Sums of Squares
- **Quadratic Residues and Euler's Criterion** — residues mod p, Euler's criterion, sums of residues (~30)
- **Legendre Symbol and Quadratic Reciprocity** — Legendre and Jacobi symbols, reciprocity law (~25)
- **Quadratic Congruences** — solving x² ≡ a modulo primes, prime powers and composites (~10)
- **Sums of Two Squares and Binary Quadratic Forms** — Fermat's two-square theorem, x²+xy+y², representations (~35)
- **Sums of Three and Four Squares** — Lagrange's four-square theorem, three-square obstructions (~15)
### Digits and Number Bases
- **Divisibility Rules** — tests for 3, 9, 11, 7 and similar (~15)
- **Digit Sums** — digit sum and digital root properties (~25)
- **Repunits and Digit Patterns** — repunits, numbers like 111…1555…6, repeating blocks (~20)
- **Decimal Expansions** — repeating decimals, periods, decimal digits of fractions (~20)
- **Number Bases** — base-b and binary representation, base-defined sequences, Thue-Morse (~30)
- **Digit Equations and Cryptarithms** — reversals like 4·abcd=dcba, moved digits, alphametics (~45)
### Special Numbers and Integer Sequences
- **Fibonacci and Lucas Numbers** — identities, divisibility, Zeckendorf representation (~60)
- **Triangular Numbers and Consecutive Sums** — figurate numbers, sums of consecutive integers (~25)
- **Perfect and Amicable Numbers** — even perfect numbers, amicable pairs, odd perfect conditions (~25)
- **Mersenne and Fermat Numbers** — Mersenne primes, Fermat numbers and their divisors (~20)
- **Divisibility in Integer Recurrences** — divisibility and gcd properties of integer recursive sequences (~45)
### Floor Function and Rational Approximation
- **Floor Function Identities and Sums** — Hermite identity, sums of floors, Beatty sequences (~30)
- **Floor and Fractional Part Equations** — equations and inequalities in ⌊x⌋ and {x} (~15)
- **Diophantine Approximation** — Dirichlet approximation, density of {nα}, leading digits of powers (~30)
- **Continued Fractions** — finite and infinite continued fractions, convergents (incl. Kaczor-Nowak) (~28)
- **Farey Sequences** — Farey fractions, adjacency and mediants (~6)
### Cryptography and Primality Testing
- **Classical Ciphers** — Caesar, affine, Vigenère and Hill ciphers (~12)
- **Public-Key Cryptosystems** — RSA, ElGamal, exponential and knapsack cryptosystems (~15)
- **Factorization Algorithms** — Fermat, Kraitchik, Pollard rho, quadratic sieve, continued-fraction factoring (~12)
- **Primality Testing and Pseudoprimes** — pseudoprimes, Carmichael numbers, Pocklington and Proth tests (~15)

## Diophantine Equations
### Classical Diophantine Equations
- **Linear Diophantine Equations** — ax+by=c, counting nonnegative solutions, hundred-fowls puzzles (~25)
- **Frobenius Coin Problem** — largest non-representable amount, McNugget numbers (~12)
- **Pythagorean Triples** — primitive triples and their properties (~30)
- **Pell's Equation** — x²−dy²=±1 and x²−dy²=c (~18)
- **Fermat's Last Theorem Cases** — x⁴+y⁴=z², n=3 and 4 cases, related descent equations (~12)
### Polynomial Diophantine Equations
- **Perfect Squares and Perfect Powers** — when an expression is a square or power (~55)
- **Quadratic Equations in Integers** — two-variable quadratics, rational points on conics; excludes Pell (~45)
- **Cubic and Higher-Degree Equations** — integer solutions of cubic and higher polynomial equations (~30)
- **Reciprocal Sums and Egyptian Fractions** — 1/x+1/y=1/n, unit-fraction representations (~30)
- **Markov-Type Quadratic Equations** — x²+y²+z²=3xyz, (a²+b²)/(ab+1) integrality by root flipping (~20)
### Exponential and Divisibility Equations
- **Exponential Diophantine Equations** — 2ˣ−3ʸ=7, pᵏ+1=qᵐ and similar (~65)
- **Factorial Equations** — equations involving n!, such as 1!+…+n! square (~12)
- **Integrality of Rational Expressions** — when (x⁵+y)/(x²+y²) or m | n²+8 holds (~45)


# Combinatorics
_6 topic(s), 26 branches, 117 subtopics, ~2005 questions_

## Enumerative Combinatorics
### Basic Counting Principles
- **Sum and Product Rules** — counting by cases and stages; strings, codes, functions between finite sets (~19)
- **Permutations of Distinct Objects** — ordered arrangements and k-permutations of distinct items, incl. adjacency demands (~11)
- **Combinations and Committee Selection** — unordered selections, committees, teams, splitting people into groups (~24)
- **Permutations of Multisets** — arrangements with repeated items, words from given letters, multinomial counts (~19)
- **Combinations with Repetition (Stars and Bars)** — identical objects into boxes; nonnegative integer solutions of x1+...+xk=n (~30)
- **Lattice Paths** — monotone grid paths, reading words in letter arrays; Dyck paths see Catalan Numbers (~13)
- **Pigeonhole Principle** — elementary guarantee questions (socks, gloves, birthdays); olympiad uses filed by content, tagged (~13)
### Counting with Restrictions
- **Counting Subsets with Conditions** — subsets or pairs of subsets with sum, size or intersection conditions (~36)
- **Selections without Adjacent Elements** — subsets or seatings with no two neighbours chosen, in a row or circle (~10)
- **Counting Integers by Digit Conditions** — how many integers have given digit properties; digit theory see Number Theory (~63)
- **Counting Grid Fillings and Colorings** — number of fillings or colorings of tables under row, column or neighbour rules (~26)
### Permutations and Symmetry
- **Permutations with Restrictions** — counting permutations with positional, adjacency or pattern conditions; excludes derangements (~37)
- **Circular Arrangements** — seatings and arrangements around a circle counted up to rotation (~7)
- **Burnside's Lemma** — counting colorings and labellings up to symmetry: necklaces, cube colorings (~12)
### Binomial Coefficients
- **Binomial Theorem** — coefficients and terms of binomial and multinomial expansions (~12)
- **Binomial Identities** — summation identities with binomial coefficients, by algebra or combinatorial argument (~53)
- **Pascal's Triangle** — row properties, parity of entries, monotonicity and bounds of binomial coefficients (~10)
### Inclusion-Exclusion
- **Inclusion-Exclusion Principle** — counting unions, Venn-diagram survey data, Bonferroni bounds; excludes derangements and surjections (~29)
- **Derangements** — permutations without fixed points, hat-check and ménage problems (~11)
- **Counting Surjections** — onto functions and distributions leaving no box empty (~5)
### Recurrences and Generating Functions
- **Recurrence Relations for Counting** — setting up recursions for words, walks, staircases; solving them see Algebra (~31)
- **Counting Tilings of Strips** — number of tilings of 2×n, 3×n boards or boxes; existence see Tilings and Dissections (~14)
- **Generating Functions for Counting** — ordinary and exponential generating functions, coefficient extraction, dice sums (~13)
### Special Counting Numbers
- **Catalan Numbers** — parenthesisations, triangulations, non-crossing chords, ballot sequences, Dyck paths (~19)
- **Integer Partitions** — partitions of n, Ferrers diagrams, making change, partitions with maximal product (~22)
- **Stirling Numbers and Set Partitions** — Stirling numbers of both kinds, Bell numbers, permutation cycles, involutions (~6)
### Counting Geometric Configurations
- **Counting Figures in Grids** — rectangles, squares, unit cubes and lattice points in grids and boards (~15)
- **Counting Triangles and Polygons** — triangles or polygons from point sets; integer-sided triangles of given perimeter (~19)
- **Counting Diagonals and Intersection Points** — numbers of diagonals, segments and crossing points in polygons (~11)
- **Regions Formed by Lines and Curves** — parts of plane or space cut by lines, circles, planes, diagonals (~17)

## Graph Theory
### Graph Structure and Traversal
- **Vertex Degrees and the Handshake Lemma** — degree sums, odd-degree vertices, regular graphs, acquaintance counts (~19)
- **Connectivity and Distances** — connected graphs, paths, distances, walks on road networks (~10)
- **Trees and Labelled Graphs** — trees, spanning trees, cycle rank, Cayley's formula, counting labelled graphs (~9)
- **Directed Graphs and Tournaments** — round-robin results, kings, score sequences, edge orientations, one-way road networks (~28)
- **Eulerian Trails and Circuits** — tracing figures in one stroke, Königsberg bridges, domino rings (~7)
- **Hamiltonian Paths and Cycles** — routes through every vertex, Icosian game, Dirac-type seatings (~8)
### Planarity, Coloring and Matching
- **Planar Graphs** — planarity, K5 and K3,3, embeddings on plane and torus (~5)
- **Euler's Formula for Polyhedra** — V−E+F; counting faces, edges and vertices of polyhedra and maps (~18)
- **Graph Coloring** — vertex, edge and map coloring; splitting vertex sets under degree conditions (~14)
- **Bipartite Graphs and Matchings** — bipartiteness, Hall's theorem, systems of distinct representatives, pairings (~8)
### Extremal Graph Theory
- **Ramsey's Theorem** — Ramsey numbers, monochromatic triangles in edge-colored complete graphs (~25)
- **Turán's Theorem and Triangle-Free Graphs** — maximum edges without triangles or cliques; forced triangles (~13)
- **Cliques and Independent Sets** — forced cliques, people knowing everyone, independent sets in friendship graphs (~10)

## Extremal Combinatorics
### Additive Combinatorics
- **Zero-Sum and Divisible Subset Sums** — subsets with sum divisible by n, Erdős–Ginzburg–Ziv type results (~14)
- **Distinct and Equal Subset Sums** — disjoint subsets with equal sums, balancing weights, distinct-sum sets (~16)
- **Partitions of Integer Sets** — splitting {1,...,n} or N into classes with sum or structure conditions (~18)
- **Sum-Free Sets and Schur's Theorem** — sets without x+y=z; colorings forcing monochromatic solutions (~11)
- **Arithmetic Progressions and van der Waerden's Theorem** — forced or avoided progressions in integer sets and colorings (~8)
- **Divisibility and Coprimality in Integer Subsets** — chosen integers forcing divisor pairs or coprime pairs (~7)
- **Extremal Subsets of Integers** — largest subsets avoiding given differences, products or sums (~36)
- **Sumsets and Pairwise Sums** — sets recovered from pairwise sums, mean-closed sets, Sidon-type sets (~14)
### Extremal Set Theory
- **Set Families with Intersection Conditions** — families with bounded intersections, locks and keys, committee configurations (~37)
- **Chains, Antichains and Monotone Subsequences** — Sperner's theorem, Dilworth's theorem, Erdős–Szekeres monotone subsequences (~5)
- **Intervals on a Line** — segment families: many with a common point or many disjoint (~8)
- **Infinite Combinatorics** — infinite set systems, infinite graphs and partitions; plain countability see Real Analysis (~18)
### Designs and Number Arrays
- **Latin Squares** — Latin squares and rectangles, Sudoku and KenKen fillings (~5)
- **Magic Squares** — magic squares; magic labellings of polygons and polyhedra (~11)
- **Block Designs and Finite Projective Planes** — Steiner systems, Kirkman schoolgirls, finite planes, Hadamard matrices (~10)
- **Number Tables with Row and Column Conditions** — existence of tables with prescribed sums, products or signs; counting see Enumerative (~31)
- **Error-Correcting Codes** — binary words at given distance, Hamming bound, covering codes (~6)
### Chessboards and Grids
- **Non-Attacking Chess Pieces** — maximal independent and dominating placements of rooks, bishops, queens, knights, kings (~39)
- **Knight's Tours and Piece Moves** — tours, reachable squares and minimum moves of chess pieces (~11)
- **Marked Cells in Grids** — choosing cells so every row, rectangle or block meets a condition (~36)
- **Colorings of Grids** — forced monochromatic rectangles or patterns in colored grids and lattices (~8)
### Arrangements and Sequences
- **Number Arrangements with Adjacency Conditions** — existence of rows or circles of numbers with neighbour conditions (~21)
- **Rearrangements of Arrays** — sorting rows and columns; extremal entries of arrays and permutations (~14)
- **Constrained Sequences and Words** — block-sum conditions, cyclic partial sums (gas stations), square-free and Thue–Morse words (~28)

## Combinatorial Geometry
### Point Configurations
- **Distances in Finite Point Sets** — two-distance sets, distinct distances, nearest neighbours, symmetric point sets (~27)
- **Lines and Collinearity in Point Sets** — Sylvester–Gallai, lines determined by points, general position (~15)
- **Convex Position and Helly's Theorem** — convex polygons among points; Helly-type intersections of convex sets (~13)
- **Non-Crossing Segments and Matchings** — non-crossing matchings and spanning paths of point sets (~4)
- **Colorings of the Plane and Space** — monochromatic distances, triangles or squares in colored plane, space, polygon vertices (~23)
- **Lattice Points and Lattice Polygons** — Pick's theorem, parity of lattice points, lattice points in discs (~22)
- **Vector Sums and Sign Choices** — choosing signs or subsets of vectors to bound their sum (~9)
### Polygons, Curves and Visibility
- **Diagonals and Triangulations of Polygons** — existence and extremal questions on diagonals and triangulations; counts see Enumerative (~22)
- **Art Gallery, Visibility and Illumination** — guards, visibility from points, mirrored rooms, billiard paths in polygons (~15)
- **Curves and Topological Arguments** — Jordan curves, inscribed squares, figure-eights, Sperner's lemma, necklace splitting (~23)
### Covering and Packing
- **Points in Bounded Regions** — many points in a square, disc or cube force close pairs (~13)
- **Covering by Discs and Polygons** — covering figures by discs, squares or strips; minimal coverings (~16)
- **Packing Shapes in Regions** — fitting coins, discs, squares or barrels into a region (~11)
- **Lines and Strips Crossing Figures** — lines meeting many curves or parts; plank-type strip problems (~6)
### Tilings and Dissections
- **Domino Tilings** — tilings of boards by dominoes, mutilated boards, fault lines (~15)
- **Polyomino Tilings** — tilings and coverings by trominoes, tetrominoes and other polyominoes (~29)
- **Packing Bricks and Rectangles** — fitting 1×n bricks or rectangles into grid boxes and rectangles (~12)
- **Dissections of Polygons and Polyhedra** — cutting figures into squares, cubes, triangles or congruent pieces (~13)

## Combinatorial Games and Processes
### Two-Player Games
- **Take-Away Games** — single-pile removal games and their winning positions (~14)
- **Nim and Wythoff's Game** — multi-pile Nim, Wythoff's game, Sprague–Grundy values (~13)
- **Number and Digit Games** — players build numbers, insert signs or add divisors toward a target (~17)
- **Board Games** — placement and movement games on boards and graphs, Chomp, tic-tac-toe (~29)
- **Selection and Sharing Games** — players alternately pick coins, numbers or slices to maximise their share (~13)
- **Pursuit and Evasion Games** — chasers and evaders on graphs, lines or grids (~8)
### Processes on Numbers
- **Blackboard Number Operations** — repeatedly replacing numbers or splitting piles; reachable and final states (~35)
- **Color-Change and Population Processes** — chameleons, bacteria, colored balls removed or recoloured in pairs (~8)
- **Iterated Sequence Transformations** — Ducci sequences, Collatz map, digit-sum sequences, repeated averaging (~15)
- **Labelled Polygons and Circles** — operations on numbers or colours at polygon vertices or circle sectors (~20)
- **Card Shuffling and Elimination** — shuffles, dealing procedures, Josephus elimination (~11)
### Processes on Boards and Tokens
- **Cell Operations on Boards and Tables** — flipping signs or colours of rows and blocks; infection spreading (~26)
- **Lamp and Switch Toggling** — lamps, lockers, cups and switches toggled by rules (~14)
- **Peg Solitaire and Jumping Pegs** — peg jumps, Conway's soldiers, one-dimensional solitaire (~15)
- **Chip Moves and Reachability** — reachable positions of chips, pucks, frogs and rolling boxes (~22)
- **Sliding Tiles and Token Swaps** — fifteen puzzle, toads and frogs, knight swaps, neighbour transpositions (~29)

## Logic and Algorithmic Puzzles
### Logic and Knowledge Puzzles
- **Knights and Knaves** — truth-tellers and liars (~7)
- **Common Knowledge and Rational Deduction** — what agents can infer: Cheryl's birthday, blue-eyed islanders, pirate gold (~24)
- **Hat Guessing Strategies** — players guessing their own hat colours from others' hats (~19)
- **Prisoner Coordination Strategies** — 100 boxes, light-switch room, agreed protocols without communication (~10)
- **Communication Protocols** — passing information through restricted channels, card tricks, padlocked boxes (~16)
- **Voting and Social Choice** — voting procedures, Condorcet cycles, Arrow's theorem (~4)
### Weighing and Search Puzzles
- **Counterfeit Coin Weighing** — finding fake coins with a balance in fewest weighings (~21)
- **Measuring with Jugs, Fuses and Hourglasses** — measuring volumes or times; weight sets for a balance (~10)
- **Identification with Minimal Tests** — poisoned barrels, switches and bulbs, mislabelled boxes, unmarked wires (~19)
- **Egg-Drop and Guessing Strategies** — egg drop, twenty questions, searching for a hidden number (~10)
### Algorithmic Puzzles
- **Sorting and Selection by Comparisons** — fewest comparisons to sort, rank or find extremes; pancake sorting (~29)
- **Minimum Cuts and Breaks** — breaking chocolate bars, cubes, sticks, chains; jigsaw assembly (~12)
- **Tower of Hanoi** — Tower of Hanoi and its variants (~4)
- **River Crossing and Scheduling** — river and bridge crossings, cooking and gossip schedules, desert journeys (~18)
- **List and Array Algorithms** — algorithms on arrays and streams: missing number, majority, maximum subarray (~20)
- **Matchstick and Coin Rearrangements** — moving matches or coins to form required shapes (~12)


# Geometry
_2 topic(s), 11 branches, 51 subtopics, ~596 questions_

## Plane Geometry
### Triangles
- **Similar Triangles** — similarity, proportional segments, parallels cutting triangle sides (~16)
- **Right Triangles and the Pythagorean Theorem** — right-triangle relations, altitude to hypotenuse, 30-60-90 triangles (~5)
- **Law of Sines and Cosines** — solving triangles by trigonometry; identities without a figure see Algebra (~8)
- **Area of a Triangle** — Heron's formula, area ratios from cevians and parallels (~10)
- **Medians and Centroids** — medians, centroid of a triangle or point system, mass points (~11)
- **Angle Bisectors, Incircle and Excircles** — bisector theorem, incentre, inradius, excircles, tangent lengths (~12)
- **Altitudes and Orthocentre** — altitudes, orthic triangle, orthocentre (~4)
- **Ceva's and Menelaus' Theorems** — concurrency of cevians, collinear points on triangle sides (~5)
### Quadrilaterals and Polygons
- **Parallelograms and Trapezoids** — sides, diagonals and midlines of parallelograms, rhombi and trapezoids (~13)
- **Areas of Quadrilaterals and Polygons** — areas and area ratios of quadrilaterals and polygons (~24)
- **Midpoint Polygons and Varignon's Theorem** — polygons formed by midpoints or reflected vertices (~5)
- **Regular Polygons** — sides, chords, diagonals and angles of regular and star polygons (~20)
- **Equiangular and Equilateral Polygons** — polygons with equal angles or sides, parallel opposite sides (~14)
### Circles
- **Chords, Arcs and Inscribed Angles** — chord lengths, arcs, inscribed and central angles (~18)
- **Tangent Lines and Tangent Circles** — tangents, mutually tangent circles, tangential quadrilaterals (~24)
- **Power of a Point and Radical Axes** — power of a point, radical axis, radical center (~3)
- **Circumcircle of a Triangle** — circumcentre, circumradius, Simson line, points on the circumcircle (~9)
- **Cyclic Quadrilaterals and Ptolemy's Theorem** — concyclic points, cyclic quadrilaterals, Ptolemy's theorem (~4)
### Loci and Constructions
- **Loci of Points** — loci and envelopes defined by distance, angle or motion conditions (~24)
- **Ruler-and-Compass Constructions** — constructing triangles, quadrilaterals and points from given data (~18)
- **Constructions with Restricted Tools** — straightedge-only, ball and other restricted-tool constructions (~10)
- **Rolling Circles and Roulettes** — cycloids, hypocycloids, coin rotation, rolling discs; arc length see Calculus (~5)
### Geometric Transformations
- **Rotations** — rotations; Napoleon's theorem; equilateral triangles and squares erected on sides (~34)
- **Reflections and Isometries** — reflections, compositions of isometries, classifying isometries (~11)
- **Homothety and Spiral Similarity** — homotheties, spiral similarities, directly similar figures (~4)
### Geometric Inequalities
- **Inequalities for Triangle Sides** — inequalities in the side lengths a, b, c of a triangle (~16)
- **Inequalities for Medians, Altitudes and Radii** — bounds linking angles, medians, altitudes, bisectors, R and r (~14)
- **Distance Inequalities for Points** — Ptolemy and Erdős–Mordell type bounds on distances to vertices (~20)
- **Area and Perimeter Inequalities** — isoperimetric-type bounds, area fractions of inscribed figures (~20)
### Geometric Optimization
- **Shortest Paths** — shortest routes by reflection or unfolding, Steiner networks, escape paths (~16)
- **Fermat Point and Minimal Distance Sums** — points minimising sums of distances or squared distances (~11)
- **Maximal Area and Perimeter** — largest or smallest area or perimeter under constraints; derivative-only solutions see Calculus (~17)
- **Extremal Inscribed and Enclosed Figures** — largest figure inside another; moving boxes through corridors (~12)
### Analytic Geometry
- **Lines and Distances in Coordinates** — coordinate computations with points, lines, distances and areas (~8)
- **Regions Defined by Inequalities** — areas and shapes of regions given by equations or inequalities (~7)
- **Conic Sections** — ellipse, parabola, hyperbola: foci, tangents, chords, inscribed figures (~10)
- **Sums of Squared Distances** — parallelogram law, Leibniz and Euler identities, perpendicularity criteria (~21)
- **Geometry in the Complex Plane** — figures described by complex numbers; roots of unity see Algebra (~10)

## Solid Geometry
### Polyhedra
- **Tetrahedra** — edges, faces, volumes, concurrency and special classes of tetrahedra (~21)
- **Cubes and Rectangular Boxes** — distances, diagonals and sections of cubes and boxes (~11)
- **Prisms and Pyramids** — volumes and metric properties of prisms and pyramids (~4)
- **Nets and Unfoldings** — unfolding polyhedra, folding nets, wrapping solids (~3)
### Spheres, Cones and Cylinders
- **Spheres and Tangent Spheres** — spheres, mutually tangent spheres, polygons tangent to a sphere (~11)
- **Inscribed and Circumscribed Spheres** — insphere and circumsphere of tetrahedra and other polyhedra (~8)
- **Cones and Cylinders** — volumes, sections and inscribed solids of cones and cylinders (~6)
- **Geometry on the Sphere** — paths on a globe, great circles, curves and caps on a sphere (~6)
### Lines and Planes in Space
- **Skew Lines and Distances in Space** — skew lines, distances, equidistant planes, skew quadrilaterals (~12)
- **Dihedral and Solid Angles** — angles between faces, planes and lines in space (~5)
- **Cross-Sections of Solids** — plane sections of cubes and solids; solids whose sections are all circles (~5)
- **Projections of Solids** — orthogonal projections, shadows, passing solids through holes (~8)
- **Coordinate Geometry in Space** — lines, planes, cylinders and cones given by equations (~3)


# Probability and Stochastic Processes
_2 topic(s), 23 branches, 138 subtopics, ~3176 questions_

## Probability
### Events and Probability Spaces
- **Sigma-Fields and Probability Axioms** — sample spaces, event algebra, sigma-fields, axioms, continuity of probability measures (~28)
- **Addition Rule and Venn Diagrams** — unions, complements and two- or three-event Venn calculations; excludes n-event formulas (~47)
- **Inclusion-Exclusion and Bonferroni Inequalities** — probability of unions of n events, Boole and Bonferroni bounds; pure counting is Combinatorics (~22)
### Combinatorial Probability
- **Equally Likely Outcomes** — classical probability by counting: dice, coins, number choices, seatings, tournaments (~65)
- **Urn Models** — sequential draws, transfers between urns, several urns; excludes counts in one sample (Hypergeometric) (~25)
- **Card Hands** — poker, bridge and other dealt-hand probabilities (~20)
- **Birthday Problem** — shared birthdays and other coincidence probabilities (~15)
- **Matching Problem** — derangements, hat-check and letters-in-envelopes, number of fixed points (~18)
- **Balls into Bins** — occupancy: empty bins, elevator stops, number of distinct values seen (~12)
- **Coupon Collector Problem** — time and number of draws needed to collect every type (~15)
- **Random Permutations** — cycles, records, runs and position patterns of random permutations; lost boarding pass (~12)
- **Probabilistic Method** — existence proofs by random construction, first- and second-moment methods (~10)
- **Random Graphs** — Erdős–Rényi graphs: edge, triangle and clique counts, connectivity probabilities (~8)
### Conditional Probability and Independence
- **Conditional Probability** — definition, multiplication rule, conditioning on partial information (~35)
- **Law of Total Probability** — partitions and tree diagrams for unconditional probabilities (~25)
- **Bayes' Theorem** — inverse probabilities: diagnostic tests, risk classes, which urn or coin (~50)
- **Independence of Events** — pairwise, mutual and conditional independence of events (~22)
- **Conditional Probability Paradoxes** — Monty Hall, three prisoners, boy-girl, Bertrand's box, sleeping beauty (~25)
- **System Reliability** — series, parallel and k-out-of-n systems; network reliability functions (~12)
### Random Variables and Their Distributions
- **Probability Mass Functions** — valid PMFs, normalising constants, probabilities from discrete distributions (~22)
- **Probability Density Functions** — valid densities, normalising constants, probabilities and modes from densities (~45)
- **Cumulative Distribution Functions** — CDF properties, mixed distributions, percentiles and medians read from F (~35)
- **Functions of a Random Variable** — distribution of g(X), truncation, probability integral transform (~48)
- **Hazard Rates and Survival Functions** — failure rates, survival functions, Weibull-type lifetimes (~10)
- **Simulation of Random Variables** — inverse transform, rejection sampling, Monte Carlo and importance sampling (~18)
### Expectation
- **Expected Value** — means of discrete and continuous variables, tail-sum formula, expected counts (~70)
- **Variance and Standard Deviation** — variance computation and variance of linear functions; excludes covariance (~40)
- **Higher Moments** — moments, skewness, kurtosis, moment sequences and determinacy (~10)
- **Insurance Payments with Deductibles** — distribution and expectation of claim payments above a deductible (~45)
- **Insurance Payments with Benefit Limits** — payments capped by a maximum benefit, coinsurance, deductible-plus-limit policies (~30)
- **Expected Payoff and Fair Games** — fair prices, St Petersburg paradox, roulette, craps, chuck-a-luck (~30)
- **Optimal Stopping** — secretary problem, stop-or-continue games, prophet inequality, maximising expected reward (~25)
- **Entropy and Mutual Information** — entropy of distributions, conditional entropy, mutual information (~6)
- **Stochastic Ordering** — stochastic, convex and stop-loss orders between random variables (~7)
### Discrete Distributions
- **Binomial Distribution** — Bernoulli trials, binomial probabilities, mean and variance, sums of binomials (~60)
- **Geometric Distribution** — trials to first success, memorylessness, expected waits for a face or outcome (~35)
- **Negative Binomial Distribution** — trials to the r-th success, Banach's matchbox problem (~12)
- **Hypergeometric Distribution** — successes in a sample without replacement, capture-recapture, acceptance sampling (~25)
- **Poisson Distribution** — Poisson counts, moments, sums, splitting and conditioning of Poisson variables (~65)
- **Poisson Approximation** — law of rare events, Poisson limit of binomials, Stein-Chen and total variation bounds (~15)
- **Multinomial Distribution** — multinomial cell counts, their marginals and covariances (~10)
- **Runs and Patterns** — waiting times for runs and coin sequences, longest run, Penney's game (~45)
- **Problem of Points** — first to win n games: series, tennis scoring, division of stakes (~30)
### Continuous Distributions
- **Uniform Distribution** — continuous uniform variables: probabilities, percentiles, conditional uniform laws (~30)
- **Exponential Distribution** — lifetimes, memoryless property, minimum of independent exponentials (~55)
- **Normal Distribution** — standardising, percentiles, linear combinations of independent normals (~55)
- **Gamma Distribution** — gamma densities, sums of exponentials, Erlang and hypoexponential laws (~15)
- **Beta Distribution** — beta densities and beta function, beta-binomial links (~8)
- **Cauchy Distribution** — Cauchy densities, missing mean, stability of Cauchy averages (~12)
### Joint Distributions
- **Joint Probability Mass Functions** — joint tables, marginals and probabilities for discrete pairs (~40)
- **Joint Density Functions** — joint densities, marginals, probabilities over regions for continuous pairs (~38)
- **Independence of Random Variables** — factorisation criteria and checking independence of random variables (~15)
- **Conditional Distributions** — conditional PMFs and densities given another variable (~20)
- **Covariance and Correlation** — covariance, correlation coefficient, variance of sums of dependent variables (~50)
- **Covariance Matrices** — covariance and correlation matrices, positive semidefiniteness, linear transformations (~20)
- **Sums of Independent Random Variables** — convolution: sums of uniforms, exponentials, Poissons and other families (~28)
- **Transformations of Random Vectors** — Jacobian change of variables, ratios, products, polar coordinates (~18)
- **Order Statistics** — minimum, maximum and k-th smallest of a sample; uniform spacings (~42)
- **Bivariate Normal Distribution** — bivariate normal density, conditional laws, correlation and regression lines (~30)
- **Multivariate Normal Distribution** — Gaussian vectors, linear maps, conditioning, independence through covariance (~24)
### Conditioning and Compounding
- **Conditional Expectation** — E(Y given X), tower property, conditional expectation as best predictor (~38)
- **Law of Total Variance** — conditional variance formula and its uses (~10)
- **Mixture Distributions** — random parameters: mixed Poisson, continuous mixtures, frailty models (~15)
- **Compound Distributions** — random sums of i.i.d. variables, compound Poisson laws, Wald's equation (~18)
### Generating Functions and Transforms
- **Probability Generating Functions** — PGFs of integer variables: moments, sums, joint PGFs; counting GFs are Combinatorics (~38)
- **Moment Generating Functions** — MGFs, cumulants, identifying distributions from their MGFs (~35)
- **Characteristic Functions** — computing and recognising characteristic functions, inversion and continuity theorems (~48)
### Inequalities and Limit Theorems
- **Markov and Chebyshev Inequalities** — tail bounds from means and variances, one-sided Cantelli bound (~22)
- **Moment Inequalities** — Jensen, Hölder, Lyapunov, Cauchy-Schwarz applied to expectations; algebraic versions are Algebra (~22)
- **Chernoff Bounds and Large Deviations** — exponential tail bounds and large-deviation rates for sums (~8)
- **Modes of Convergence** — almost sure, in probability, in mean, in distribution; implications, Slutsky (~38)
- **Borel-Cantelli Lemmas** — events occurring infinitely often, zero-one laws (~14)
- **Weak Law of Large Numbers** — convergence in probability of sample averages (~12)
- **Strong Law of Large Numbers** — almost sure convergence of averages, three-series theorem, iterated logarithm (~14)
- **Central Limit Theorem** — normal approximation for sums and means of i.i.d. variables (~50)
- **Normal Approximation to the Binomial** — de Moivre-Laplace theorem, continuity correction (~12)
- **Uniform Integrability** — uniform integrability and convergence of expectations (~9)
- **Stable and Infinitely Divisible Distributions** — stable laws, infinite divisibility, domains of attraction (~7)
### Geometric Probability
- **Random Points in Plane Regions** — uniform points in squares, discs, triangles, balls: distances, areas, positions (~42)
- **Random Points on a Circle** — random arcs, semicircle problem, random inscribed triangles and polygons (~14)
- **Buffon's Needle** — needles and coins dropped on ruled or tiled surfaces (~8)
- **Random Chords and Bertrand's Paradox** — chord-length probabilities under different random-chord rules (~7)
- **Stick Breaking** — random division of a stick, triangle formation, lengths of pieces (~12)
- **Meeting Problem** — two uniform arrival times: meeting, waiting and collision probabilities (~9)

## Stochastic Processes
### Random Walks
- **Simple Random Walk** — returns, first passage, maxima, arc sine laws, lattice walks via generating functions (~32)
- **Reflection Principle** — path counting by reflection for one-dimensional walks (~12)
- **Ballot Theorem** — ballot counting, box-office change queues, never-tied scores (~10)
- **Gambler's Ruin** — ruin probabilities and expected duration between two barriers, bold play (~45)
- **Recurrence of Random Walks** — Pólya's theorem; recurrence and transience in d dimensions and on trees (~20)
- **Random Walks on Graphs** — walks on graphs, polyhedra and chessboards; hitting and cover times (~20)
### Discrete-Time Markov Chains
- **Markov Property and Transition Matrices** — Markov property, n-step probabilities, Chapman-Kolmogorov, recognising Markov chains (~38)
- **Classification of States** — communicating classes, periodicity, recurrence, transience, positive recurrence (~45)
- **Stationary Distributions** — invariant distributions, convergence to equilibrium, ergodic theorem for chains (~42)
- **Hitting Probabilities and Mean Hitting Times** — absorption probabilities and expected hitting times of chains (~32)
- **Reversibility and Detailed Balance** — reversible chains, detailed balance, Kolmogorov's criterion (~17)
- **Markov Chain Monte Carlo** — Metropolis-Hastings, Gibbs sampler, Barker's algorithm (~8)
### Branching Processes
- **Galton-Watson Process** — generation sizes, iterated PGFs, total progeny, age-dependent branching (~25)
- **Extinction Probability** — extinction as smallest fixed point of the PGF, criticality (~13)
- **Moran Model and Coalescent** — Moran and Wright-Fisher models, Kingman's coalescent, Ewens' formula (~7)
### Poisson Processes
- **Homogeneous Poisson Process** — counts, interarrival times and waiting times of a constant-rate process (~32)
- **Conditional Arrival Times** — arrival times given the count: uniform order-statistics property (~8)
- **Thinning and Superposition** — splitting, merging and marking independent Poisson processes (~15)
- **Non-Homogeneous Poisson Processes** — time-varying intensity, doubly stochastic (Cox) processes (~10)
- **Compound Poisson Processes** — random sums at Poisson times, shot noise, collective risk and ruin (~8)
- **Spatial Poisson Processes** — Poisson points in plane and space, nearest-neighbour distances (~12)
### Continuous-Time Markov Chains
- **Generators and Kolmogorov Equations** — Q-matrices, forward and backward equations, transition semigroups (~28)
- **Jump Chains and Holding Times** — embedded jump chain, exponential holding times, explosion (~12)
- **Birth Processes** — pure birth and Yule processes, explosion of birth processes (~15)
- **Birth-Death Processes** — birth-death and immigration-death processes, their transient and equilibrium behavior (~32)
- **Stationary Distributions (Continuous Time)** — invariant measures, limits of transition probabilities, continuous-time reversibility (~18)
### Queueing Theory
- **Single-Server Markovian Queues** — M/M/1 queue length, waiting time, busy period, finite capacity (~28)
- **Multi-Server and Loss Queues** — M/M/s, M/M/∞, machine repair, Erlang loss formula (~22)
- **Queues with General Service or Arrivals** — M/G/1, G/M/1, D/M/1 via imbedded chains; Pollaczek-Khinchine (~15)
- **Queueing Networks** — tandem queues, Jackson and migration networks (~8)
### Renewal Processes
- **Renewal Function and Renewal Equation** — renewal function, renewal-type equations, Laplace transform methods (~22)
- **Renewal Limit Theorems** — elementary and key renewal theorems, central limit theorem for renewals (~10)
- **Excess Life and the Inspection Paradox** — current and excess life, size-biased interarrival times (~13)
- **Renewal-Reward Processes** — long-run average rewards and costs, regenerative processes (~10)
### Stationary Processes
- **Weak and Strong Stationarity** — autocovariance functions, checking stationarity of random signals (~22)
- **Spectral Densities** — spectral distribution and spectral representation of stationary processes (~8)
- **Linear Prediction** — best linear predictors for stationary sequences, Kolmogorov-Szegő formula (~7)
- **Moving Average and Autoregressive Processes** — MA and AR sequences and their autocovariances (~6)
- **Ergodic Theorems** — ergodic theorem for stationary sequences, invariant events, mixing (~7)
- **Gaussian Processes** — Gaussian processes, covariance functions, stationary Gaussian sequences (~9)
### Martingales
- **Martingale Property** — verifying martingales, sub- and supermartingales, martingales from walks and branching (~30)
- **Optional Stopping Theorem** — stopping times, optional stopping and sampling, Wald identities (~30)
- **Martingale Convergence Theorem** — almost sure and mean-square convergence, upcrossings, backward martingales (~14)
- **Martingale Inequalities** — Doob's maximal and L2 inequalities, Azuma-Hoeffding inequality (~13)
- **Pólya's Urn** — Pólya urn proportions and their martingale limits (~5)
### Brownian Motion and Diffusions
- **Brownian Motion** — definition, Gaussian increments, scaling and time inversion, sample-path properties (~28)
- **Brownian First Passage Times** — hitting times, reflection principle and maxima for Brownian motion (~18)
- **Brownian Bridge and Excursions** — Brownian bridge, zeros, excursions, arc sine law for Brownian motion (~7)
- **Diffusion Processes** — Ornstein-Uhlenbeck, drift and diffusion coefficients, barriers, Feller diffusion (~13)
- **Lévy Processes and Subordinators** — Lévy processes, subordinators, self-similarity, fractional Brownian motion (~10)
### Stochastic Calculus
- **Itô Integral** — stochastic integrals, quadratic variation, Itô isometry (~9)
- **Itô's Formula** — Itô's formula and Itô's lemma for functions of Brownian motion and diffusions (~37)
- **Stochastic Differential Equations** — geometric Brownian motion, lognormal prices, mean-reverting and OU SDEs, explicit solutions (~9)
- **Multidimensional Itô Calculus** — correlated Brownian motions, SDEs for products and ratios of asset prices (~4)


# Statistics
_1 topic(s), 7 branches, 31 subtopics, ~301 questions_

## Mathematical Statistics
### Sampling Distributions
- **Sampling Distribution of the Mean** — distribution of sample means from normal populations and two samples (~12)
- **Chi-Squared, t and F Distributions** — derivation and properties of distributions arising from normal samples (~8)
- **Distribution of the Sample Variance** — (n-1)S²/σ², independence of sample mean and variance (~6)
### Point Estimation
- **Unbiased Estimators** — bias, unbiased estimators of parametric functions, mean squared error, consistency (~14)
- **Method of Moments** — moment-matching estimators (~4)
- **Maximum Likelihood Estimation** — likelihood functions, computing MLEs, invariance (~24)
- **Cramér-Rao Bound and Fisher Information** — Fisher information, efficiency, Cramér-Rao lower bound (~9)
- **Asymptotic Theory of Estimators** — asymptotic normality of MLEs, delta method, jackknife and bootstrap (~10)
### Sufficiency and Optimal Estimation
- **Sufficient Statistics** — definition, factorisation criterion, minimal sufficiency, sufficiency and likelihood principles (~16)
- **Rao-Blackwell Theorem** — improving estimators by conditioning on a sufficient statistic (~10)
- **Completeness and UMVUE** — complete statistics, Lehmann-Scheffé theorem, minimum-variance unbiased estimators (~4)
- **Exponential Families** — natural parameters and sufficient statistics of exponential families (~7)
### Hypothesis Testing
- **Size and Power of Tests** — critical regions, type I and II errors, power functions, p-values (~7)
- **Neyman-Pearson Lemma** — most powerful tests of simple against simple hypotheses (~14)
- **Uniformly Most Powerful Tests** — UMP tests, monotone likelihood ratio (~6)
- **Likelihood Ratio Tests** — generalised likelihood ratio tests and Wilks' theorem (~14)
- **Tests for Means** — z and t tests, one-sample, two-sample and paired (~8)
- **Tests for Variances** — chi-squared and F tests on variances (~8)
- **Tests for Proportions** — one- and two-sample tests on binomial proportions (~5)
- **Goodness-of-Fit Tests** — Pearson chi-squared and Kolmogorov-Smirnov tests against a model (~13)
- **Contingency Table Tests** — chi-squared tests of independence and homogeneity in two-way tables (~8)
### Interval Estimation
- **Confidence Intervals for Means** — intervals for normal means, one and two samples (~7)
- **Confidence Intervals for Variances** — chi-squared and F intervals for variances and ratios (~3)
- **Large-Sample Confidence Intervals** — asymptotic and likelihood-based intervals, pivotal quantities, proportions (~6)
### Bayesian Inference and Decision Theory
- **Prior and Posterior Distributions** — Bayes' rule for parameters, conjugate priors, hierarchical models (~18)
- **Bayes Estimators** — posterior mean, median and mode under loss functions; credible intervals (~6)
- **Loss, Risk and Admissibility** — loss functions, decision rules, risk functions, admissibility (~8)
- **Bayes and Minimax Rules** — Bayes rules, minimax and equaliser rules, Stein shrinkage (~8)
### Linear Models
- **Simple Linear Regression** — least-squares line, residuals, R-squared, slope inference (~12)
- **General Linear Model** — matrix least squares, Gauss-Markov, projection matrices, ridge penalty (~18)
- **Inference in Linear Models** — F and t tests on coefficients, confidence regions, one-way ANOVA (~8)


# Quantitative Finance
_3 topic(s), 14 branches, 51 subtopics, ~483 questions_

## Derivatives Pricing
### Derivative Contracts and No-Arbitrage
- **Forward and Futures Pricing** — cost-of-carry forward prices, forward contract values, futures vs forwards, options on futures (~8)
- **Option Payoffs and Trading Strategies** — payoff and profit diagrams, spreads, straddles, butterflies; decomposing payoffs into vanillas (~23)
- **Put-Call Parity** — European put-call parity, parity arbitrage, with dividends or bid-ask spreads (~9)
- **No-Arbitrage Bounds on Option Prices** — model-free bounds, monotonicity and convexity in strike and maturity, dividend effects (~34)
- **American Options and Early Exercise** — optimal early exercise, American vs European values, perpetual options; excludes tree mechanics (~9)
### Discrete-Time Pricing Models
- **One-Period Market Models** — finite-state markets, state prices, replication and completeness, Arrow-Debreu securities (~15)
- **Fundamental Theorem of Asset Pricing** — arbitrage, equivalent martingale measures, self-financing strategies in discrete time (~13)
- **Binomial Option Pricing** — one- and multi-step binomial and trinomial trees, risk-neutral probabilities, CRR model (~21)
### Black-Scholes Model
- **Black-Scholes PDE** — derivation by hedging, checking solutions, boundary conditions, reduction to the heat equation (~18)
- **Black-Scholes Formula** — deriving and evaluating call and put prices, dividend yield, at-the-money approximations (~27)
- **Risk-Neutral Valuation** — pricing general payoffs as discounted expectations (power, log, squared, digital-type claims) (~17)
- **Change of Numeraire and Market Price of Risk** — Girsanov drift changes, numeraire choice, forward-price dynamics, market price of risk (~10)
### Greeks and Hedging
- **Option Greeks** — computing and interpreting delta, gamma, vega, theta, rho; relations between Greeks (~27)
- **Delta Hedging** — delta-neutral positions, rebalancing, hedging P&L, hedging with the wrong volatility (~9)
- **Gamma and Vega Hedging** — delta-gamma and delta-vega neutral portfolios using a second option (~9)
### Volatility Modeling
- **Implied Volatility and the Smile** — computing implied volatility, smile shape and its effect on prices (~12)
- **Time-Dependent Volatility** — deterministic volatility functions, root-mean-square volatility, fitting to option maturities (~4)
- **Stochastic Volatility Models** — pricing PDE and hedging when volatility is random (~2)
- **Jump-Diffusion Models** — Poisson jumps in prices, market incompleteness, option formulas under jumps (~6)
### Exotic Options
- **Barrier Options** — knock-in and knock-out pricing, in-out parity, PDE formulation, barrier Greeks (~21)
- **Digital Options** — cash-or-nothing and American digitals, supershares, pay-later options (~10)
- **Asian and Lookback Options** — average-rate and max-min payoffs, auxiliary-variable PDEs (~9)
- **Compound, Chooser and Forward-Start Options** — options on options, chooser and forward-start valuation, compound parity (~5)
- **Static Replication** — replicating exotics with portfolios of vanillas, put-call symmetry, range accruals (~5)
### Multi-Asset and Currency Derivatives
- **Multi-Asset and Margrabe Options** — exchange options, max-of-assets payoffs, correlated multi-asset PDEs (~5)
- **Quanto Options** — options on foreign assets, quanto drift adjustment, strikes in another currency (~5)
- **Currency Forwards and Cross Rates** — FX forward pricing, covered interest parity, cross-rate arbitrage; excludes uncovered parity (Economics) (~3)
### Numerical Methods in Finance
- **Tree Calibration and Convergence** — choosing up and down factors and probabilities, moment matching, continuous limit (~8)
- **Monte Carlo Simulation** — Monte Carlo pricing, standard error, random draws per path, variance reduction (~3)
- **Finite-Difference Methods** — programming PDE solvers for vanilla, barrier and compound options (~5)

## Fixed Income
### Bonds and the Yield Curve
- **Compounding and Present Value** — discrete vs continuous compounding, growth of deposits, discounting cash flows (~2)
- **Zero Rates and Bootstrapping** — discount factors, zero-coupon bonds, instantaneous rate curves, bootstrapping from coupon bonds (~15)
- **Bond Yield** — yield to maturity, par yield, price-yield relation, solving for yield (~4)
- **Duration and Convexity** — duration, convexity, dollar duration, price-change approximations, duration hedging (~12)
- **Forward Rates** — forward rates from LIBOR or zero rates, effect of rates on forwards (~4)
### Interest Rate Derivatives
- **Forward Rate Agreements** — FRA pricing, LIBOR-in-arrears and trigger FRAs (~3)
- **Interest Rate Swaps** — swap valuation, swap rates from discount factors, amortizing and cancellable swaps (~6)
- **Caps, Floors and Swaptions** — caplets, floorlets, collars, inverse floaters, swaptions (~3)
- **Bonds with Embedded Options** — puttable, callable and convertible bonds (~2)
### Interest Rate Models
- **Short-Rate Models** — bond pricing equation, Vasicek and Ho-Lee affine solutions, simulating rates (~6)
- **Yield Curve Fitting** — calibrating Ho-Lee or Vasicek to market zero-coupon prices (~4)
- **HJM and LIBOR Market Models** — HJM forward-rate drift, BGM drifts, rate correlations, swap-rate dynamics (~7)

## Portfolio Theory and Risk Management
### Mean-Variance Portfolio Theory
- **Two-Asset Portfolios and Diversification** — mean and variance of two-asset portfolios, minimum-variance hedge ratio (~6)
- **Efficient Frontier** — minimum-variance and maximum-return portfolios, risk-free asset, tangency portfolio (~19)
- **Capital Asset Pricing Model** — market portfolio, beta, CAPM derivation, estimating alpha and beta (~3)
### Utility and Optimal Investment
- **Expected Utility Maximization** — utility functions, risk aversion, CARA-optimal portfolios, Kelly betting (~6)
- **Utility Indifference Pricing and Risk Sharing** — reservation prices, market-clearing prices, Pareto-optimal risk transfer (~5)
- **Dynamic Programming for Investment and Consumption** — Bellman equations for multi-period investment, consumption and control (~6)
### Risk Management
- **Return, Volatility and Correlation Estimation** — computing returns, historical volatility and correlation matrices from market data (~8)
- **Value at Risk** — VaR computation, horizon and confidence scaling, subadditivity, criticisms (~5)
- **Credit Risk** — risky bonds, implied default probabilities, recovery rates, Poisson default model (~5)


# Economics
_1 topic(s), 9 branches, 32 subtopics, ~266 questions_

## Macroeconomics
### National Income Accounting
- **GDP and Its Measurement** — GDP, GNP, NDP, value added, what GDP counts, GDP and welfare (~8)
- **National Income Identities** — expenditure identity, saving-investment and budget-trade balance relations (~4)
- **Price Indexes and Real vs Nominal Values** — CPI, PPI, GDP deflator, inflation rate, real interest rate (~6)
### Economic Growth
- **Growth Accounting** — production functions, factor shares, total factor productivity, growth decomposition with data (~11)
- **Solow Growth Model** — steady state, saving and population growth, technology jumps, convergence (~9)
- **Endogenous Growth** — constant returns to capital, human capital, cross-country growth differences (~7)
### Aggregate Supply, Inflation and Unemployment
- **AS-AD Model** — classical and Keynesian supply, demand and supply shocks, short and long run (~13)
- **Phillips Curve** — short- and long-run Phillips curve, inflation expectations, sticky wages (~6)
- **Unemployment and Okun's Law** — natural rate, types and measurement of unemployment, output gap, Okun's law (~10)
- **Costs of Inflation and Disinflation** — anticipated and unanticipated inflation, indexation, sacrifice ratio, stagflation, disinflation strategy (~9)
### Aggregate Demand and IS-LM
- **Keynesian Cross and the Multiplier** — equilibrium income, consumption function, multipliers with taxes, automatic stabilizers (~8)
- **IS and LM Curves** — deriving IS and LM, slopes and shifts, equilibrium income and interest rate (~9)
- **Monetary and Fiscal Policy in IS-LM** — policy multipliers, crowding out, liquidity trap, policy mix (~13)
### Open-Economy Macroeconomics
- **Exchange Rates and PPP** — appreciation, depreciation, devaluation, purchasing power parity, real exchange rate (~6)
- **Interest Parity and Capital Mobility** — uncovered interest parity, expected depreciation, capital flows; excludes FX forward pricing (QF) (~5)
- **Mundell-Fleming Model** — fiscal and monetary policy under fixed and flexible rates with capital mobility (~12)
- **Balance of Payments and External Adjustment** — internal and external balance, BoP and money stock, foreign repercussions, intervention (~12)
### Consumption and Investment
- **Life-Cycle and Permanent-Income Hypotheses** — consumption smoothing, MPC out of permanent income, random walk, liquidity constraints (~12)
- **Saving and the Interest Rate** — interest sensitivity of saving, saving-rate data and policy (~4)
- **Business Fixed Investment** — rental cost of capital, desired capital stock, present value, Tobin's q (~14)
- **Residential and Inventory Investment** — housing and mortgage rates, inventory accelerator, inventories over the cycle (~5)
### Money, Banking and Financial Markets
- **Demand for Money** — functions of money, transactions demand, Baumol-Tobin, velocity (~12)
- **Money Supply and the Central Bank** — money multiplier, reserves, open market operations, bank runs, sterilization (~7)
- **Monetary Policy Targets and Rules** — money vs interest-rate targets, Taylor rule, rules vs discretion, dynamic inconsistency (~15)
- **Term Structure of Interest Rates** — expectations theory, long vs short rates, bond prices; excludes bond mathematics (QF) (~3)
- **Stock Prices and Efficient Markets** — dividend-discount view of stock prices, random walk, equity premium, arbitrage (~5)
### Stabilization Policy and Government Debt
- **Policy Lags and Uncertainty** — inside and outside lags, multiplier uncertainty, econometric models (~10)
- **Budget Deficits and Public Debt** — deficit measures, debt-to-GDP dynamics, Ricardian equivalence, social security (~10)
- **Seigniorage and Hyperinflation** — monetizing deficits, inflation tax, hyperinflation episodes (~7)
### Modern Business Cycle Theory
- **Rational Expectations** — rational expectations, policy neutrality, empirical evidence (~4)
- **Real Business Cycle Theory** — propagation, intertemporal labor substitution, deep parameters, random walk in output (~6)
- **Menu Costs and Imperfect-Information Models** — Mankiw menu-cost and Lucas imperfect-information supply models (~4)


# Mechanics
_3 topic(s), 25 branches, 111 subtopics, ~1237 questions_

## Classical Mechanics
### Kinematics
- **Rectilinear Motion** — 1D motion, constant acceleration, free fall, motion graphs, meeting problems (~22)
- **Projectile Motion** — uniform-gravity trajectories, range, envelopes, inclines; excludes drag (see Motion in a Resisting Medium) (~32)
- **Relative Motion** — relative velocity, river crossing, wind, ships, pursuit curves, Galilean frames (~19)
- **Curvilinear Motion and Polar Coordinates** — velocity and acceleration in polar and intrinsic components, curvature of paths (~15)
### Newton's Laws of Motion
- **Newton's Laws and Connected Bodies** — free-body diagrams, blocks, strings, light pulleys, Atwood machines; massive pulleys see Fixed-Axis Rotation (~13)
- **Friction** — static and kinetic friction, rough inclines, stacked blocks, minimum pulling force (~23)
- **Variable Forces in One Dimension** — integrating F(t) or F(x) for straight-line motion; excludes resistive forces (~7)
- **Motion in a Resisting Medium** — linear and quadratic drag, terminal velocity, resisted projectiles (~14)
- **Uniform Circular Motion** — centripetal force, banked curves, conical pendulums, turntables, rotating funnels (~25)
- **Motion in a Vertical Circle** — loop-the-loop, leaving a sphere, string tension and minimum speed in vertical circles (~20)
- **Constrained Motion on Curves and Surfaces** — beads on wires, particles on cones and spheres, normal reactions (~10)
### Work and Energy
- **Work-Energy Theorem and Power** — work by forces, kinetic energy changes, power and efficiency of machines and athletes (~7)
- **Conservation of Mechanical Energy** — energy conservation for particles, springs and multi-body systems; rolling bodies see Rolling (~12)
- **Potential Energy Curves** — conservative forces, U(x) diagrams, turning points, bounded motion, molecular potentials (~7)
### Momentum and Collisions
- **Conservation of Linear Momentum** — explosions, recoil, man on a boat, momentum principle for systems (~14)
- **Elastic Collisions** — one- and two-dimensional elastic collisions, momentum and energy transfer (~16)
- **Inelastic Collisions and Restitution** — coefficient of restitution, perfectly inelastic impacts, ballistic pendulum, bouncing balls (~11)
- **Collisions in the Center-of-Mass Frame** — zero-momentum frame, lab-CM angle conversion, two-body and nuclear scattering kinematics (~11)
- **Rocket Motion** — rocket equation, multistage rockets, rockets under gravity and drag (~9)
- **Variable-Mass Systems** — falling chains, conveyor belts, accreting raindrops, unrolling carpets; rockets see Rocket Motion (~20)
### Statics
- **Center of Mass** — locating centres of mass and gravity of particle systems, laminae and solids (~21)
- **Equilibrium of Rigid Bodies** — force and torque balance, ladders, toppling, 3D statics, stability of equilibrium (~20)
- **Ropes, Cables and Catenaries** — hanging chains, cable sag, ropes over pegs and cylinders, capstan friction (~12)
### Rotation of Rigid Bodies
- **Moment of Inertia** — moments of inertia, radius of gyration, parallel and perpendicular axis theorems (~12)
- **Plane Kinematics of Rigid Bodies** — angular velocity, instantaneous center, rolling-contact kinematics, cams, linkages, gears (~7)
- **Fixed-Axis Rotation** — torque and angular acceleration, massive pulleys, spools, flywheels, rotational energy (~21)
- **Rolling Without Slipping** — rolling on inclines and curved surfaces, rolling energy, friction required (~28)
- **Sliding and Rolling with Friction** — skidding balls and discs, transition to pure rolling, billiard and snooker shots (~11)
- **Conservation of Angular Momentum** — spinning skaters, collapsing stars, insects on rings, angular impulse (~16)
- **General Plane Motion** — falling rods and chimneys, sliding ladders, yo-yos, compound pendulum dynamics (~26)
- **Impulsive Motion of Rigid Bodies** — impacts on rods and wheels, center of percussion, hoop mounting a step (~7)
### Rigid Body Dynamics in Three Dimensions
- **Angular Velocity Vector** — 3D rigid-body kinematics, addition of angular velocities, rolling cones and balls (~8)
- **Inertia Tensor and Principal Axes** — inertia tensor, principal moments and axes, dynamical symmetry (~7)
- **Euler's Equations and Free Rotation** — torque-free motion, stability of rotation about principal axes, wobbling bodies (~6)
- **Spinning Tops and Gyroscopes** — steady precession, sleeping top, gyrocompass, spinning wheels (~7)
- **Rolling Spheres in Three Dimensions** — balls on slopes, turntables and fixed spheres; discs on rotating tables (~5)
- **Cartesian Tensors** — tensor transformation laws, orders, invariants, isotropic tensors (~5)
### Gravitation
- **Newton's Law of Gravitation** — forces between point masses and spheres, superposition, neutral points (~7)
- **Gravitational Field and Potential** — fields of rods, rings, shells and spheres; shell theorem; self-energy; tides (~29)
- **Acceleration Due to Gravity** — variation of g with height, depth and latitude (~5)
- **Escape Velocity and Gravitational Potential Energy** — launch and lifting energy, escape speed, impact speeds (~7)
- **Circular Orbits and Satellites** — orbital speed and period, geostationary orbits, satellite energy; elliptic see Kepler (~9)
- **Two-Body Problem and Binary Stars** — reduced mass, motion about the common center of mass (~7)
### Central-Force Motion
- **Central Forces and Effective Potential** — angular momentum conservation, effective potential, apsidal distances, bounded orbits (~3)
- **Orbit Equation and Force Laws** — path (Binet) equation, force law from a given orbit and the reverse (~10)
- **Elliptic Orbits and Kepler's Laws** — conic orbits in an inverse-square field, eccentricity, apsidal speeds, periods (~25)
- **Orbital Manoeuvres and Transfer Orbits** — Hohmann transfers, velocity changes, gravity assists, aerobraking (~11)
- **Stability and Precession of Orbits** — nearly circular orbits, apsidal angle, perturbed and relativistic precession (~5)
- **Scattering in a Central Field** — Rutherford scattering, deflection angle, cross sections, hyperbolic flybys (~5)
### Non-Inertial Reference Frames
- **Linearly Accelerating Frames** — pseudo-forces in accelerating vehicles and lifts, tilted liquid surfaces (~4)
- **Rotating Frames** — centrifugal and Coriolis forces, rotating wires and turntables, Larmor's theorem (~13)
- **Motion Relative to the Rotating Earth** — Coriolis deflection of falling and thrown bodies, effective gravity, plumb line (~19)
### Lagrangian and Hamiltonian Mechanics
- **Lagrange's Equations** — generalised coordinates, constraints, setting up and solving Lagrange's equations (~36)
- **Symmetry and Conservation Laws** — cyclic coordinates, generalised momenta, energy function, symmetries (~5)
- **Hamilton's Principle** — action and variational derivation of motion; pure extremal problems go to LA and DE (~2)
- **Hamilton's Equations** — Legendre transform, Hamiltonian, canonical equations (~7)
- **Phase Space and Liouville's Theorem** — phase-space flow, Liouville's theorem, Poisson brackets, integrability (~5)

## Oscillations and Waves
### Linear Oscillations
- **Simple Harmonic Motion** — SHM kinematics and energy, identifying SHM, superposition of SHMs, Lissajous figures (~26)
- **Spring-Mass Systems** — springs in series and parallel, vertical springs, two-body spring systems (~15)
- **Pendulums** — simple, physical and torsional pendulums, rocking and rolling oscillators (~18)
- **Damped Oscillations** — under-, over- and critical damping, logarithmic decrement, energy decay, Coulomb friction (~17)
- **Forced Oscillations and Resonance** — driven oscillators, resonance curves, transients, Fourier-series forcing (~9)
### Coupled and Nonlinear Oscillations
- **Normal Modes of Coupled Oscillators** — coupled pendulums and springs, beaded strings, molecular vibrations, normal coordinates (~27)
- **Nonlinear Oscillations** — anharmonic oscillators, Lindstedt and perturbation methods, amplitude-dependent frequency (~5)
- **Phase Paths of Nonlinear Oscillators** — phase paths of oscillators, equilibrium points, limit cycles, Van der Pol equation (~7)
### Mechanical Waves
- **Traveling Waves and the Wave Equation** — wave functions, wave speed on strings, energy transport, reflection at junctions (~18)
- **Superposition and Standing Waves** — superposition, standing waves and harmonics on strings, plucked strings (~13)
- **Dispersion and Group Velocity** — phase and group velocity, dispersion relations, water waves, light in dispersive media (~21)
### Sound
- **Speed of Sound** — Newton-Laplace formula, sound in gases and solids, echoes; Mach-number flows see Fluid Mechanics (~7)
- **Sound Intensity and Decibels** — intensity, pressure amplitude, decibel levels, acoustic impedance, reverberation (~19)
- **Resonance in Air Columns** — open and closed pipes, resonance tubes, Kundt's tube (~4)
- **Beats** — beat frequency, tuning-fork comparisons (~4)
- **Doppler Effect** — moving sources and observers, reflected sound, radar speed traps (~7)

## Solid Mechanics
### Analysis of Stress
- **Stress Vector and Cauchy's Formula** — traction on arbitrary planes, stress components, stress quadric, Lamé's ellipsoid (~5)
- **Principal Stresses and Stress Invariants** — principal stresses and directions, invariants, hydrostatic and deviatoric parts (~11)
- **Maximum Shear and Octahedral Stresses** — principal shear stresses, octahedral normal and shear stresses (~3)
- **Plane Stress and Mohr's Circle** — 2D stress transformation, Mohr's circle, combined loading of shafts (~5)
- **Equations of Equilibrium (Elasticity)** — differential equilibrium equations, boundary conditions, stress functions (~7)
### Analysis of Strain
- **Strain-Displacement Relations** — strains from displacement fields, linear and nonlinear terms, changes of length and angle (~13)
- **Principal Strains and Dilatation** — principal strains, strain invariants, cubical dilatation, deviatoric strain (~5)
- **Compatibility Conditions** — Saint-Venant compatibility equations for strain fields (~4)
### Stress-Strain Relations and Failure
- **Axial Loading and Young's Modulus** — stretching of wires, rods, cables and springs; breaking stress; self-weight; elastic energy (~13)
- **Generalized Hooke's Law and Elastic Constants** — isotropic stress-strain relations; E, G, K, Poisson's ratio, Lamé constants (~5)
- **Theories of Failure** — maximum stress and strain, Tresca, von Mises and Mohr criteria; factor of safety (~14)
### Energy Methods
- **Castigliano's Theorems** — strain energy, deflections by Castigliano and fictitious loads, rings and frames (~27)
- **Reciprocal Theorems** — Maxwell-Betti-Rayleigh reciprocal theorem, influence coefficients (~7)
- **Statically Indeterminate Structures** — redundant reactions and members by Castigliano's second theorem (Menabrea) (~11)
- **Virtual Work and Potential Energy Principles** — virtual work, minimum potential energy, unit-load (Maxwell-Mohr) method (~2)
### Bending of Beams
- **Unsymmetrical Bending** — flexure formula, neutral axis for skew loads and unsymmetrical sections (~13)
- **Shear Center and Shear Flow** — shear stresses in thin-walled open sections, locating the shear center (~7)
- **Curved Beams** — Winkler-Bach formula, hooks, rings and links (~7)
- **Beam Deflection** — elastic curve of loaded beams and cantilevers (~3)
### Torsion
- **Torsion of Solid Sections** — Saint-Venant theory, Prandtl stress function, non-circular bars, membrane analogy (~1)
- **Thin-Walled Closed Tubes** — Bredt-Batho shear flow and twist of single-cell closed sections (~9)
- **Multi-Cell Closed Sections** — torsion of two- and three-cell thin-walled tubes (~5)
- **Thin-Walled Open Sections** — thin rectangular strips, rolled I and channel sections (~1)
### Axisymmetric Stress Analysis
- **Thick-Walled Cylinders** — Lamé's solution for internal and external pressure, design against yielding (~10)
- **Compound Cylinders and Shrink Fits** — interference fits, composite tubes, disks shrunk on shafts (~12)
- **Rotating Disks and Shafts** — stresses in rotating disks, rings and cylinders; uniform-strength disks (~4)
- **Thick-Walled Spheres** — spherical shells and cavities under pressure (~4)
- **Thin-Walled Pressure Vessels** — hoop and longitudinal stresses in thin cylinders and spheres (~3)
- **Thermoelastic Stresses** — thermoelastic stresses in disks, cylinders, spheres and beams (~9)
### Elastic Stability
- **Euler Buckling** — critical loads of columns with various end conditions and variable sections (~5)
- **Beam-Columns** — combined axial and lateral loading, initially curved bars (~7)
- **Energy Methods for Buckling** — stationary potential energy, Rayleigh-Ritz and Timoshenko methods (~3)
### Mechanics of Composite Materials
- **Anisotropic Elasticity of a Lamina** — orthotropic stress-strain relations, lamina stiffness and compliance transformation (~4)
- **Laminate Stiffness and Ply Stresses** — cross-ply and angle-ply laminates, ply stresses and strains, laminate failure (~9)
- **Micromechanics of Fiber Composites** — rule of mixtures for moduli and strength (Srinath); Callister and Raghavan see Material Science (~7)
### Stress Concentration and Fracture
- **Stress Concentration** — stress concentration factors, notches and holes, notch sensitivity, stop holes (~5)
- **Contact Stresses** — Hertz contact of spheres and cylinders (~6)
- **Linear Elastic Fracture Mechanics** — stress intensity factor, fracture toughness, critical crack size (Srinath); Callister see Material Science (~14)


# Fluid Mechanics
_3 topic(s), 18 branches, 107 subtopics, ~1779 questions_

## Fluid Mechanics
### Fluid Properties
- **Density and Ideal-Gas State** — density, specific weight and specific gravity; ideal-gas equation of state and gas property data
- **Viscosity and Newton's Law of Viscosity** — shear stress in thin films, sliding plates and shafts; viscosity-temperature fits (~24)
- **Viscometers** — measuring viscosity with rotating-cylinder, cone-plate, disk, capillary and falling-ball viscometers, for any fluid (~13)
- **Pressure in Drops and Bubbles** — Laplace pressure, soap bubbles, energy of coalescing drops (~18)
- **Capillarity and Wetting** — capillary rise, contact angle, menisci, surface-tension forces on objects (~19)
- **Compressibility and Bulk Modulus** — bulk modulus, density change of liquids with pressure (~6)
- **Cavitation** — vapor pressure, cavitation onset in flows and around bodies; pumps see Net Positive Suction Head (~10)
- **Non-Newtonian Fluids and Rheology** — power-law and Bingham models, flow curves, non-Newtonian pipe flow; viscosity measurement see Viscometers (~21)
### Fluid Statics
- **Hydrostatic Pressure Distribution** — pressure at depth, layered fluids, gage and absolute pressure, hydraulic presses (~25)
- **Manometers** — U-tube, inclined, differential and multi-fluid manometers (~31)
- **Pressure Variation in the Atmosphere** — standard, isothermal and polytropic atmospheres, lapse rate, altimetry (~14)
- **Hydrostatic Forces on Plane Surfaces** — resultant force and center of pressure on gates and panels (~30)
- **Hydrostatic Forces on Curved Surfaces** — horizontal and vertical components on curved gates, domes and dams (~22)
- **Buoyancy** — Archimedes' principle, floating and submerged bodies, balloons, hydrometers (~31)
- **Stability of Floating Bodies** — metacentric height; stability of floating blocks, cylinders, cones and barges (~13)
- **Linearly Accelerating Containers** — free-surface tilt and pressure in rigid-body translation (~14)
- **Rotating Containers** — paraboloid free surface and pressure in rigid-body rotation (~15)
### Fluid Kinematics
- **Velocity Field and Acceleration** — Eulerian description, material derivative, local and convective acceleration (~14)
- **Streamlines, Pathlines and Streaklines** — flow-line equations and sketches for steady and unsteady fields (~6)
- **Differential Continuity Equation** — continuity in Cartesian and polar coordinates, finding missing velocity components (~16)
- **Stream Function** — plane and axisymmetric stream functions, flow rate between streamlines (~16)
- **Vorticity and Circulation** — rotation rate, vorticity, irrotationality tests, circulation around closed curves (~14)
- **Free and Forced Vortices** — tornado, hurricane and drain vortex models, combined vortices (~9)
### Control-Volume Analysis
- **Reynolds Transport Theorem** — converting system laws to control-volume form (~4)
- **Conservation of Mass** — steady mass balances on pipes, junctions, porous walls and nozzles (~25)
- **Unsteady Mass Balance and Tank Filling** — filling and blowdown of gas tanks, deforming control volumes (~15)
- **Linear Momentum for Fixed Control Volumes** — forces from jets, vanes, nozzles, bends and sluice gates, also when Bernoulli supplies the velocities (~50)
- **Moving and Accelerating Control Volumes** — moving vanes, jet-propelled carts and boats, jet engines, control-volume analysis of rockets (~17)
- **Angular Momentum Equation** — sprinklers, rotating arms, torque on bends and simple impellers (~15)
- **Steady-Flow Energy Equation** — energy equation with pumps, turbines and given losses; pipe friction see Moody chart (~23)
### Bernoulli Equation
- **Bernoulli Equation for Steady Flow** — velocities and pressures along a streamline: venturi pressure drop, stagnation pressure, siphons; forces see Linear Momentum (~35)
- **Free Jets and Torricelli's Law** — efflux speed, jet trajectories and range from tank orifices (~14)
- **Tank Draining Time** — quasi-steady draining of tanks through orifices and pipes (~26)
- **Unsteady Bernoulli and Oscillating Liquid Columns** — U-tube oscillation, pipe start-up, accelerating liquid columns (~11)
### Navier-Stokes Equations and Exact Solutions
- **Navier-Stokes Equations and Boundary Conditions** — derivation, assumptions, boundary and initial conditions, differential energy equation (~12)
- **Couette Flow** — plate- and cylinder-driven shear flows, lubrication, Couette flow with pressure gradient (~11)
- **Poiseuille Flow Between Plates and in Annuli** — pressure-driven laminar channel and annulus flow; pipes see Laminar Pipe Flow (~10)
- **Falling Films and Draining Flows** — gravity-driven films on walls, rods and moving belts (~10)
- **Rotating and Oscillating Viscous Flows** — rotating cylinders, Stokes oscillating plate, spin-up, decaying vortex (~7)
- **Turbulence and the Log Law** — Reynolds stresses, eddy viscosity, mixing length, log-law velocity profiles (~18)
### Dimensional Analysis and Similitude
- **Dimensional Homogeneity** — units and unit conversion, dimensions of quantities, checking formulas, named dimensionless numbers (~24)
- **Buckingham Pi Theorem** — finding pi groups for physical relations (~40)
- **Nondimensionalization of Equations** — scaling governing differential equations to expose parameters (~8)
- **Modeling and Similitude** — Reynolds, Froude and Mach scaling from model tests to prototypes (~26)
### Potential Flow
- **Velocity Potential and Laplace's Equation** — existence of potential, Laplace's equation, potential-stream function relations (~15)
- **Elementary Plane Flows and Superposition** — uniform stream, source, sink, vortex, doublet, stagnation-flow combinations (~22)
- **Rankine Half-Bodies and Ovals** — source-stream and source-sink-stream bodies, Kelvin ovals, surface velocities (~20)
- **Flow past a Cylinder with Circulation** — doublet plus stream, Kutta-Joukowski lift, stagnation points, surface pressure (~13)
- **Method of Images (Potential Flow)** — flows near walls and corners using image sources and vortices (~9)
- **Complex Potential** — complex potential functions and simple conformal-mapping flows (~6)
- **Axisymmetric Potential Flow** — point sources, Rankine bodies of revolution, flow past spheres (~10)
- **Finite-Difference Methods for Flow Equations** — numerical solution of Laplace and Poisson equations for potential and duct flows; includes explicit and implicit schemes for unsteady diffusion (~12)
### Boundary Layers and External Flow
- **Momentum-Integral Method** — von Kármán integral relation, approximate profiles, shape factor (~16)
- **Laminar Flat-Plate Boundary Layer** — Blasius solution, thickness, skin friction and plate drag (~23)
- **Turbulent Flat-Plate Boundary Layer** — power-law estimates, transition, mixed laminar-turbulent plate drag (~18)
- **Boundary Layers with Pressure Gradient** — adverse gradients, separation prediction, wedge flows (~8)
- **Drag on Immersed Bodies** — drag coefficients of vehicles, cylinders, plates, structures and parachutes (~40)
- **Terminal Velocity and Sphere Drag** — terminal velocity of a single falling or rising sphere, particle or ball from drag-coefficient data (~30)
- **Vortex Shedding and Strouhal Number** — shedding frequency, wind-induced vibration of cylinders and antennas (~11)
- **Magnus Effect** — lift on spinning balls and rotating cylinders, Flettner rotors (~10)
- **Lift, Airfoils and Aircraft Performance** — airfoil lift and drag data, finite wings, takeoff, glide and range (~24)
### Viscous Flow in Pipes and Ducts
- **Reynolds Number and Entrance Length** — laminar and turbulent criteria, entrance region length (~12)
- **Laminar Pipe Flow** — Hagen-Poiseuille flow, capillary tubes, laminar head loss (~32)
- **Friction Factor and the Moody Chart** — turbulent head loss, roughness, solving for flow rate or diameter (~35)
- **Noncircular Ducts and Hydraulic Diameter** — annular, rectangular and triangular ducts, exchanger passages (~16)
- **Minor Losses** — fittings, valves, entrances, exits, expansions and diffusers (~18)
- **Pipe Systems with Pumps and Turbines** — pump head and power for pipelines including friction and minor losses (~40)
- **Series and Parallel Pipes** — flow division and head loss in series and parallel pipes (~13)
- **Pipe Networks and Three-Reservoir Systems** — junction problems, network flow balances (~12)
- **Obstruction Flow Meters** — orifice, nozzle, venturi and variable-area meters, discharge coefficients (~30)
- **Pitot-Static Tubes** — velocity from stagnation and static pressure, duct traverses (~10)
- **Flow Measurement Methods** — dilution and tracer methods, flowmeter calibration by mass balance; orifice, venturi and rotameters see Obstruction Flow Meters
### Multiphase Flow, Particles and Mixing
- **Gas-Liquid Two-Phase Flow** — flow regimes, void fraction, slip, homogeneous and separated-flow models (~26)
- **Particle Settling and Separation** — settling of suspensions and particle groups: hindered settling, elutriation, sedimentation, cyclones; single bodies see Terminal Velocity and Sphere Drag (~12)
- **Fluidized and Packed Beds** — minimum fluidization, bed pressure drop, Ergun equation (~8)
- **Mixing and Agitation** — impeller power number, stirred-vessel scale-up, mixing time (~18)

## Compressible Flow
### Isentropic Flow
- **Speed of Sound and Mach Number** — sound speed in gases and liquids, Mach regimes, onset of compressibility (~14)
- **Stagnation Properties** — stagnation temperature, pressure and density; adiabatic and isentropic relations (~16)
- **Isentropic Flow with Area Change** — area-Mach relation, sonic reference conditions, variable-area duct flow; choked converging nozzles see Converging Nozzles and Choked Flow (~16)
### Nozzles and Normal Shocks
- **Converging Nozzles and Choked Flow** — choking, maximum mass flow, tank blowdown through orifices (~12)
- **Normal Shock Waves** — jump relations, stagnation-pressure loss, supersonic pitot tubes, moving shocks (~14)
- **Converging-Diverging Nozzle Operation** — back-pressure regimes, shocks inside nozzles, design exit conditions, wind tunnels (~18)
### Duct Flow with Friction and Heat Transfer
- **Fanno Flow** — adiabatic constant-area flow with friction, choking length (~20)
- **Isothermal Flow with Friction** — isothermal gas pipeline flow (~3)
- **Rayleigh Flow** — frictionless constant-area flow with heat addition, thermal choking (~8)
### Two-Dimensional Supersonic Flow
- **Mach Waves** — Mach angle, Mach cone, sonic-boom observation (~6)
- **Oblique Shock Waves** — wedge and ramp shocks, deflection-angle relations, reflected shocks (~20)
- **Prandtl-Meyer Expansion** — expansion fans, isentropic turns, nozzle exit expansion (~8)
- **Supersonic Airfoils** — shock-expansion and Ackeret thin-airfoil lift and drag (~10)

## Hydraulics and Hydraulic Machines
### Open-Channel Flow
- **Shallow-Water Waves and Froude Number** — gravity wave speed, Froude number, tsunami and tidal propagation (~12)
- **Uniform Flow and Manning's Formula** — Chézy and Manning formulas, normal depth, compound and partly full channels (~28)
- **Most Efficient Channel Sections** — best hydraulic cross-sections for given flow (~10)
- **Specific Energy and Critical Depth** — specific energy diagram, critical depth and velocity, alternate depths (~16)
- **Flow over Bumps and Under Sluice Gates** — frictionless transitions, choking, contractions, sluice-gate discharge (~18)
- **Hydraulic Jump** — conjugate depths, energy loss, bores and surges (~18)
- **Gradually Varied Flow** — water-surface profile classification and computation, backwater curves (~22)
- **Weirs and Flumes** — sharp- and broad-crested weirs, V-notches, venturi flumes (~13)
### Pumps
- **Positive-Displacement Pumps** — reciprocating and rotary pumps, flow pulsation, pump classification (~13)
- **Centrifugal Pump Theory** — Euler turbomachine equation, velocity triangles, ideal head and power (~12)
- **Pump Performance Curves** — head, power and efficiency curves, best efficiency point (~14)
- **Pump Similarity Laws** — affinity laws, scaling between sizes and speeds, dimensionless coefficients (~22)
- **Specific Speed and Pump Selection** — specific speed, axial and mixed-flow pumps, fans and blowers, pump choice (~15)
- **Net Positive Suction Head** — NPSH available and required, suction lift limits, pump cavitation (~10)
- **Pump-System Matching** — operating point, pumps in series and parallel (~20)
### Turbines
- **Pelton Wheel** — impulse-turbine velocity triangles, power and efficiency; hydro plants see CET (~5)
- **Francis and Kaplan Turbines** — reaction and radial turbines, turbine specific speed, cavitation; hydro plants see CET (~9)
- **Wind Turbines** — horizontal- and vertical-axis wind turbines, Betz limit, power estimates (~6)


# Heat Transfer
_1 topic(s), 10 branches, 47 subtopics, ~573 questions_

## Heat and Mass Transfer
### Steady Conduction
- **Fourier's Law and Thermal Conductivity** — conduction rate equation, conductivity and its temperature dependence, driving potential (~12)
- **Plane and Composite Walls** — series and parallel thermal resistances, contact resistance, convection on wall faces (~34)
- **Cylindrical and Spherical Shells** — radial conduction through pipes, lagging layers and spherical vessels (~22)
- **Conduction with Heat Generation** — plane walls, wires and fuel rods with internal heat generation (~11)
- **Critical Radius of Insulation** — critical radius, economic insulation thickness and insulation selection (~11)
- **Surface Energy Balance and Combined Modes** — conduction, convection and radiation at one surface; thermocouple radiation error (~12)
- **Fin Temperature Distribution and Heat Rate** — fin equation, tip conditions, temperature profile and heat dissipated (~13)
- **Fin Efficiency and Effectiveness** — fin efficiency and effectiveness, fin arrays, annular fins, finned tubes (~15)
- **Two-Dimensional Steady Conduction** — separation-of-variables solutions for plates and long bars (~6)
- **Finite-Difference Method for Steady Conduction** — interior and boundary nodal equations, iterative solution (~11)
### Transient Conduction
- **Lumped Capacitance Method** — Biot number criterion, time constant, Newton's law of cooling (~24)
- **Transient Conduction in Plates, Cylinders and Spheres** — one-term solutions, Heisler charts, product solutions for multidimensional bodies (~18)
- **Semi-Infinite Solids** — sudden surface temperature or convection change, periodic surface heating (~7)
- **Finite-Difference Method for Transient Conduction** — explicit and implicit schemes, stability criterion, Schmidt plot (~10)
### Convection Principles
- **Convective Heat Transfer Coefficient** — local and average coefficients, Newton's law for convection rate (~9)
- **Thermal Boundary Layer** — thermal versus velocity layer, role of Prandtl number; excludes purely hydrodynamic layers (~12)
- **Dimensionless Groups in Convection** — meaning of Nusselt, Prandtl, Grashof and Rayleigh numbers; flow regimes (~10)
- **Energy Equation and Reynolds Analogy** — convective energy equation, viscous heating, Reynolds-Colburn analogy (~7)
### Forced Convection
- **Flat Plates in Parallel Flow** — laminar, turbulent and mixed plate correlations, electronics cooling (~24)
- **Cylinders and Spheres in Crossflow** — crossflow correlations for cylinders, wires and spheres (~10)
- **Heat Transfer in Laminar Tube Flow** — fully developed Nusselt numbers, bulk temperature, thermal entry length (~12)
- **Heat Transfer in Turbulent Tube Flow** — Dittus-Boelter-type correlations, noncircular ducts, liquid metals (~14)
### Free Convection
- **Vertical Plates in Still Fluid** — similarity results and correlations for isothermal or constant-flux vertical plates (~20)
- **Horizontal and Inclined Plates** — heated plates facing up or down, inclined surfaces (~6)
- **Cylinders and Spheres in Still Fluid** — horizontal pipes, wires, light bulbs, spheres, human-body models (~14)
- **Enclosed Spaces and Cavities** — plate cavities, concentric cylinders and spheres, vertical channels (~4)
### Boiling and Condensation
- **Film Condensation** — Nusselt film theory on plates and tubes, dropwise condensation, non-condensable gases (~22)
- **Boiling Regimes and the Boiling Curve** — pool boiling regimes, nucleate versus film boiling, Leidenfrost point (~9)
- **Nucleate Boiling and Critical Heat Flux** — Rohsenow correlation, peak heat flux, film-boiling calculations (~10)
- **Evaporators** — single-effect evaporator mass and energy balances, vaporizers, reboilers (~4)
### Thermal Radiation
- **Blackbody Radiation Laws** — Planck, Wien and Stefan-Boltzmann laws, band emission fractions (~16)
- **Radiative Properties of Surfaces** — emissivity, absorptivity, transmissivity, intensity, gray and diffuse surfaces (~7)
- **View Factors** — reciprocity, summation and superposition rules, view factors of common geometries (~13)
- **Radiation Exchange Between Surfaces** — black and gray exchange, enclosures, shields, radiation coefficient (~16)
- **Solar and Atmospheric Radiation** — solar constant, greenhouse effect, sky temperature, radiative equilibrium of bodies (~8)
### Mass Transfer
- **Steady Mass Diffusion** — concentrations, Fick's law in fluids, diffusion through walls and stagnant gas; solids see Material Science (~8)
- **Evaporation and Stefan Flow** — droplet evaporation, Stefan flow, evaporation from tubes and pools (~6)
- **Simultaneous Heat and Mass Transfer** — wet-bulb thermometer, evaporative cooling, heat-mass transfer analogy (~3)
### Heat Exchanger Analysis
- **Heat Exchanger Types and Flow Arrangements** — double-pipe, shell-and-tube, crossflow, compact; parallel versus counterflow (~8)
- **Overall Heat Transfer Coefficient and Fouling** — exchanger U from film coefficients, fouling factors, Wilson plot (~10)
- **Log Mean Temperature Difference** — LMTD for parallel and counterflow, energy balances, area sizing (~24)
- **LMTD Correction Factor** — F factor for multipass shell-and-tube and crossflow exchangers (~10)
- **Effectiveness-NTU Method** — effectiveness, NTU, capacity ratio, outlet-temperature rating (~18)
### Heat Exchanger Design and Operation
- **Double-Pipe Exchanger Design** — annulus and tube coefficients, hairpin sections, pressure drop (~10)
- **Shell-and-Tube Exchanger Design** — Kern method, passes, shell-side equivalent diameter, shell-side pressure drop (~10)
- **Exchanger Performance and Troubleshooting** — effect of flow changes, plugged tubes, fouled or underperforming units (~9)
- **Waste Heat Boilers and Heat Recovery** — flue-gas heat recovery, waste heat boiler sizing (~4)


# Thermodynamics
_1 topic(s), 5 branches, 15 subtopics, ~110 questions_

## Heat and Thermodynamics
### Temperature and Calorimetry
- **Thermometry and Temperature Scales** — gas, resistance and thermocouple thermometers; temperature scale conversion (~3)
- **Thermal Expansion** — linear and volume expansion of solids and liquids, expansion coefficients; constrained stress see Thermal Stresses (~12)
- **Calorimetry and Specific Heat** — mixing heat balances, specific heats of solids and liquids, mechanical equivalent of heat (~9)
### Ideal Gases and Kinetic Theory
- **Gas Laws and Equations of State** — ideal gas law, connected vessels, gas mixtures and Dalton's law, van der Waals (~12)
- **Kinetic Theory of Gases** — molecular pressure, rms speed, Maxwell-Boltzmann distribution, mean free path, effusion (~9)
- **Specific Heats of Gases** — cp, cv, specific-heat ratio, Mayer's relation, equipartition of energy (~5)
### Laws of Thermodynamics
- **First Law for Closed Systems** — heat, work and internal energy; PV work; state versus path functions (~7)
- **Ideal-Gas Processes** — isothermal, adiabatic, polytropic, isochoric and isobaric processes of ideal gases (~13)
- **Entropy and the Second Law** — entropy change of gases, gas mixing, irreversible heat exchange (~7)
### Thermodynamic Cycles
- **Heat Engines and the Carnot Cycle** — engine efficiency, Carnot limit, work and efficiency of cycles on PV diagrams (~6)
- **Rankine Cycle** — vapor power cycle on T-s diagrams outside power-plant books; plant cycles see CET (~3)
- **Refrigerators and Heat Pumps** — coefficient of performance, vapor-compression refrigeration cycle (~4)
### Phase Change and Moist Air
- **Latent Heat and Phase Change** — heats of fusion and vaporisation, supercooling, ice-water-steam mixtures (~6)
- **Vapor Pressure and Boiling Point** — saturation pressure, boiling versus pressure, steam tables, liquefaction of mixtures (~8)
- **Humidity and Psychrometrics** — relative humidity, dew point, dry- and wet-bulb temperatures, dehumidification (~6)


# Electromagnetism and Special Relativity
_3 topic(s), 12 branches, 55 subtopics, ~567 questions_

## Electromagnetism
### Electrostatics
- **Coulomb's Law** — forces between point charges, superposition, equilibrium of charged balls and pendulums (~21)
- **Electric Field of Charge Distributions** — fields of rods, rings, discs and shells by integration (~23)
- **Gauss's Law** — electric flux, symmetric charge distributions, differential form (~15)
- **Electric Potential** — potential of charges and distributions, equipotentials, field from potential, potential energy (~12)
- **Electric Dipoles and Multipoles** — dipole fields and potentials, torque and energy in fields, quadrupoles (~5)
- **Conductors in Electrostatic Equilibrium** — charge distribution, shielding, charge sharing, breakdown, charged drops and bubbles (~19)
- **Method of Images** — image charges for planes and spheres, induced charge, forces on nearby charges (~8)
- **Electrostatic Energy** — field energy, self-energy of charge distributions, electrostatic pressure (~5)
### Capacitance and Dielectrics
- **Capacitance** — capacitance of parallel-plate, spherical, cylindrical and irregular conductors (~14)
- **Capacitor Networks** — series and parallel combinations, charge redistribution between capacitors (~9)
- **Energy Stored in Capacitors** — stored energy, forces between plates, work done changing geometry (~8)
- **Dielectrics** — dielectric constant, polarization, partly filled capacitors; material data see Material Science (~5)
### Direct-Current Circuits
- **Resistance and Resistivity** — Ohm's law, resistivity, conduction in extended media, charge leakage (~11)
- **Resistor Networks** — equivalent resistance, symmetric and infinite networks, cubes and grids (~22)
- **Kirchhoff's Rules** — multi-loop circuits, node and loop equations (~13)
- **EMF and Internal Resistance** — cells in series and parallel, terminal voltage, charging batteries (~9)
- **Electrical Power and Joule Heating** — power dissipation, maximum power transfer, lamps and heaters (~8)
- **Measuring Instruments and Bridges** — galvanometers, ammeters, voltmeters, Wheatstone and metre bridges, potentiometers (~10)
### Magnetostatics
- **Charged Particles in Electric and Magnetic Fields** — Lorentz force, cyclotrons, mass spectrometers, velocity selectors, deflection tubes (~36)
- **Biot-Savart Law** — fields of wires, loops, arcs, Helmholtz coils and rotating charged bodies (~27)
- **Ampère's Law** — fields of long wires, cylinders, solenoids and toroids (~11)
- **Magnetic Force on Currents** — forces on wires and between parallel conductors, Hall effect (~12)
- **Magnetic Dipoles** — magnetic moments, torque on loops, interacting magnets, Earth's field, B and H (~12)
### Electromagnetic Induction
- **Faraday's and Lenz's Laws** — induced emf from changing flux, induced electric fields, eddy currents, superconducting rings (~19)
- **Motional EMF** — rods on rails, rotating rods, discs and loops, homopolar generators (~17)
- **Inductance and Magnetic Energy** — self and mutual inductance, energy in inductors and magnetic fields (~14)
### Transient and AC Circuits
- **RC and RL Transients** — charging and discharging capacitors, current growth in inductors, time constants (~11)
- **LC Oscillations and RLC Transients** — LC circuits, damped RLC circuits, energy exchange (~8)
- **AC Circuits and Phasors** — reactance, impedance, phasor diagrams, rms values, single-phase power factor (~15)
- **Resonance in AC Circuits** — series and parallel resonance, Q factor, bandwidth (~9)
### Maxwell's Equations and Electromagnetic Waves
- **Maxwell's Equations** — differential and integral forms, displacement current, continuity, gauge conditions (~7)
- **Electromagnetic Plane Waves** — wave equation, plane-wave fields, E-B relation, impedance of free space (~14)
- **Poynting Vector and Intensity** — energy density, Poynting's theorem, intensity, power flow in cables (~18)
- **Radiation Pressure** — momentum of light, forces on absorbers and reflectors, solar and light sails (~4)
- **Waves in Conductors and Skin Depth** — attenuation in conductors, skin effect, high-frequency resistance (~6)
- **Reflection and Transmission at Interfaces** — boundary conditions, Fresnel equations, reflectance; polarising angle see Brewster's Law (~3)
- **Waveguides** — cut-off frequencies, TE and TM modes, guide wavelength (~9)

## Optics
### Geometrical Optics
- **Refraction and Total Internal Reflection** — Snell's law, critical angle, optical fibres, light escaping a medium (~4)
- **Prisms and Dispersion** — deviation, minimum deviation, dispersive power (~4)
- **Lenses and Spherical Refracting Surfaces** — lens maker's formula, thin-lens imaging, lens combinations, ray matrices (~12)
- **Optical Instruments** — telescopes, spectacles, image brightness (~3)
- **Fermat's Principle and Graded-Index Media** — optical path, ray bending in inhomogeneous media, mirages, focusing surfaces (~7)
### Interference
- **Two-Source Interference** — Young's double slit, Fresnel biprism, fringe width, two-beam intensity (~8)
- **Thin-Film Interference** — wedge films, Newton's rings, antireflection coatings (~10)
- **Interferometers** — Michelson and Fabry-Perot interferometers (~3)
### Diffraction
- **Single-Slit Diffraction** — Fraunhofer single slit, intensity distribution, secondary maxima (~6)
- **Diffraction Gratings** — multiple-slit patterns, missing orders, grating spectra, 2D gratings (~17)
- **Resolving Power** — Rayleigh criterion for gratings, prisms and telescopes (~4)
- **Circular Apertures and Zone Plates** — Airy pattern, diffraction halos, Fresnel zone plates (~3)
### Polarization
- **Polarisers and Malus's Law** — polarising filters, intensity through sequences of polarisers (~5)
- **Brewster's Law** — polarization by reflection, polarising angle (~3)
- **Birefringence and Optical Activity** — ordinary and extraordinary rays, wave plates, rotation of the plane of polarization (~3)

## Special Relativity
### Relativistic Dynamics
- **Relativistic Energy and Momentum** — E-p relation, relativistic charged-particle motion (~1)
- **Relativistic Collisions and Decays** — threshold energies, pair production, particle decays, ultra-relativistic collisions (~3)
- **Transformation of Electric and Magnetic Fields** — fields seen from moving frames (~2)


# Quantum Mechanics
_1 topic(s), 2 branches, 6 subtopics, ~15 questions_

## Quantum, Atomic and Nuclear Physics
### Wave-Particle Duality
- **Compton Scattering** — photon-electron scattering, wavelength shift (~2)
- **De Broglie Waves** — matter wavelength of particles (~1)
- **Uncertainty Principle** — Heisenberg estimates, confinement energies, particle-in-a-box pressure (~5)
### Atoms and Nuclei
- **Bohr Model and Hydrogen-Like Atoms** — Bohr orbits, positronium, energy levels (~2)
- **Radioactive Decay** — half-life, decay chains, activity, radiation shielding (~4)
- **Nuclear Fission and Fusion** — energy release, binding energy; power-plant nuclear questions see Conventional Energy Technologies (~1)


# Electrical Machinery
_1 topic(s), 9 branches, 57 subtopics, ~392 questions_

## Electric Machines
### Magnetic Circuits
- **Magnetic Equivalent Circuits** — reluctance, mmf and flux in cores with air gaps and parallel legs (~15)
- **Nonlinear Cores and Magnetization Curves** — saturated cores solved from B-H curves; excludes material hysteresis (see Magnetic Materials) (~6)
- **Inductance of Wound Cores** — self and mutual inductance of wound cores, air-gap energy (~4)
- **Induced Voltage and Exciting Current** — Faraday's law in cores, flux waveforms, magnetizing current under sinusoidal excitation (~9)
- **Hysteresis and Eddy-Current Losses** — core-loss components, separation by frequency, lamination; excludes choice of core material (~5)
### Electromechanical Energy Conversion
- **Field Energy and Coenergy** — energy and coenergy from lambda-i relations; energy method for force (~2)
- **Force on Electromagnets and Actuators** — lifting, plunger and moving-iron forces from air-gap fields (~7)
- **Reluctance and Mutual Torque** — torque from position-dependent inductance in singly and doubly excited systems (~3)
- **Linear DC Machine** — bar on rails: induced voltage, force, starting current, steady speed (~2)
### Transformers
- **Ideal Transformer and Impedance Referral** — turns ratio, referred impedance, polarity and dot convention (~7)
- **Transformer Equivalent Circuit** — exact and approximate circuits, referred parameters, feeder-plus-transformer phasor analysis (~7)
- **Open-Circuit and Short-Circuit Tests** — equivalent-circuit parameters from transformer test data (~6)
- **Transformer Voltage Regulation** — regulation at given load current and power factor (~5)
- **Transformer Efficiency** — core and copper losses, maximum efficiency, all-day efficiency (~7)
- **Per-Unit System** — base quantities, per-unit impedances, change of base; used again in power systems (~7)
- **Autotransformers** — voltage-current relations, kVA advantage, reconnecting two-winding transformers (~5)
- **Three-Phase Transformer Connections** — Y and delta banks, open-delta, phase shift, bank ratings (~10)
### AC Machine Fundamentals
- **Rotating Magnetic Field** — synchronous speed versus poles and frequency, field reversal (~5)
- **Induced Voltage and Torque in AC Windings** — rotating loop, stator emf per phase, torque from interacting fields (~5)
- **Winding Pitch and Distribution Factors** — fractional-pitch and distributed windings, harmonic suppression, space harmonics (~9)
### Synchronous Machines
- **Synchronous Generator Equivalent Circuit** — internal emf, synchronous reactance, phasor diagram, alternator regulation and losses (~22)
- **Determining Synchronous Reactance** — open- and short-circuit characteristics, short-circuit ratio, saturated reactance (~5)
- **Power-Angle Characteristic** — power and torque versus load angle, static stability limit (~8)
- **Capability Curves** — generator operating limits on the P-Q plane (~2)
- **Parallel Operation and Load Sharing** — paralleling conditions, frequency-power droop, infinite bus, motor-generator sets (~11)
- **Synchronous Motor Operation and V-Curves** — effect of load and field changes, torque angle, power factor (~19)
- **Power-Factor Correction with Synchronous Motors** — synchronous condensers, raising plant power factor (~4)
- **Salient-Pole Machines** — two-reaction theory, Xd and Xq, reluctance power (~12)
- **Synchronous Machine Transients** — sudden short circuit, transient and subtransient reactances, sudden load change (~6)
### Induction Machines
- **Slip and Rotor Frequency** — synchronous speed, slip, rotor emf and frequency (~6)
- **Induction Motor Equivalent Circuit** — per-phase and Thevenin circuits, performance at a given slip (~12)
- **Power Flow and Air-Gap Power** — air-gap power, rotor copper loss, developed and shaft power (~7)
- **Torque-Speed Characteristic** — starting and maximum torque, pullout slip, rotor-resistance effect, sudden load (~6)
- **No-Load and Blocked-Rotor Tests** — parameter determination including the dc stator-resistance test (~3)
- **Starting of Induction Motors** — direct-on-line, reduced-voltage and autotransformer starting, code letters (~4)
- **Speed Control of Induction Motors** — pole changing, V/f, rotor resistance; excludes converter analysis (see Electric Drives) (~3)
- **Deep-Bar and Double-Cage Rotors** — rotor design classes, slip-dependent rotor impedance (~2)
- **Induction Generator and Plugging** — negative-slip generation, plugging, braking, coupled machine sets (~9)
### DC Machines
- **Armature Windings and Commutation** — lap and wave windings, parallel paths, commutator action (~7)
- **Generated Voltage and Torque Equations** — Ea and developed torque from flux and speed, simple loop (~5)
- **Separately Excited and Shunt Generators** — magnetization curve, voltage build-up, armature reaction, terminal characteristic (~14)
- **Series and Compound Generators** — series-field effect, flat and over-compounding (~5)
- **Shunt and Separately Excited Motors** — speed, torque and armature current; permanent-magnet dc motors (~17)
- **DC Series Motors** — speed-torque behavior with flux proportional to current (~8)
- **Compound DC Motors** — cumulative and differential compounding (~5)
- **Starting of DC Motors** — starting resistance and starter design (~2)
- **Speed Control of DC Motors** — armature and field control, Ward-Leonard system; excludes converter drives (~3)
- **DC Machine Losses and Efficiency** — rotational and copper losses, efficiency from test data (~2)
- **DC Machine Dynamics** — transfer functions, transient response of dc motors and generators (~9)
### Single-Phase Motors
- **Double Revolving Field Theory** — forward and backward fields, single-phase induction motor equivalent circuit (~13)
- **Split-Phase and Capacitor Motors** — auxiliary winding, starting-capacitor design, capacitor-run motors (~7)
- **Universal Motors** — ac series motor performance from standstill impedances (~2)
### Special Machines
- **Stepper Motors** — step angle, variable-reluctance and permanent-magnet types, excitation sequences (~15)
- **Servomotors** — ac and dc servomotors, transfer functions in position and speed loops (~2)
- **Synchros** — transmitter and control-transformer voltage relations (~2)
- **Linear Induction and Synchronous Motors** — LIM thrust and speed, LSM maglev propulsion (~6)
- **Switched Reluctance Motors** — stator and rotor pole geometry, torque production (~1)


# Power Systems and Power Electronics
_2 topic(s), 4 branches, 17 subtopics, ~56 questions_

## Power Electronics
### Power Semiconductor Devices
- **Power Switching Devices** — diode, SCR, GTO, TRIAC, BJT, MOSFET, IGBT characteristics and ratings (~1)
- **Thyristor Triggering Circuits** — DIAC and relaxation-oscillator gating, pulse synchronization (~5)
- **Forced Commutation** — series- and parallel-capacitor commutation of thyristors (~2)
### Power Converters
- **Diode Rectifiers** — single- and three-phase uncontrolled rectifiers, ripple factor, filtering (~4)
- **Phase-Controlled Rectifiers** — SCR full and semi-converters, output voltage versus firing angle (~5)
- **AC Voltage Controllers** — phase-angle control of ac loads, dimmers, three-phase controllers (~6)
- **DC Choppers** — step-down, step-up and two-quadrant dc-dc converters, duty ratio (~4)
- **Inverters** — voltage- and current-source bridge inverters, output waveforms (~3)
- **PWM and Harmonic Elimination** — pulse-width modulation, selective harmonic elimination in inverters (~3)
- **Cycloconverters** — direct ac-ac frequency conversion (~1)
### Electric Drives
- **Phase-Controlled DC Motor Drives** — rectifier-fed and dual-converter speed control of dc motors (~8)
- **Chopper-Controlled DC Motor Drives** — chopper speed control, regenerative braking (~2)
- **Converter-Fed Induction Motor Drives** — induction motor speed control through ac controllers or inverters (~2)

## Power Systems
### AC Power and Three-Phase Circuits
- **Complex Power and Power Factor** — real, reactive, apparent power and power triangle (~2)
- **Wye and Delta Connections** — line and phase quantities, phase sequence, delta-wye conversion (~3)
- **Balanced Three-Phase Power** — power in balanced three-phase loads and systems (~3)
- **One-Line Diagrams and Per-Phase Analysis** — per-phase equivalent of balanced systems with several loads (~2)


# Material Science
_5 topic(s), 26 branches, 131 subtopics, ~1044 questions_

## Structure of Materials
### Atomic Structure and Bonding
- **Electron Configuration and the Periodic Table** — configurations, ionization energy, electron affinity, electronegativity (~8)
- **Bond Energy and Interatomic Potentials** — energy-separation curves, equilibrium spacing, bond and atomization energies (~9)
- **Bond Types and Ionic Character** — ionic, covalent, metallic and secondary bonds; fraction of ionic character (~5)
- **Bonding and Property Trends** — modulus, melting point and expansion trends explained by bonding (~11)
### Crystal Geometry
- **Space Lattices and Crystal Systems** — Bravais lattices, lattice parameters, unit cells, lattice points per cell (~15)
- **Crystallographic Directions** — direction indices, point coordinates, families, angles between directions (~16)
- **Miller Indices of Planes** — indexing and sketching planes, zone axes, interplanar spacing (~15)
- **Miller-Bravais Indices** — four-index notation for hexagonal planes and directions (~5)
### Crystal Structures
- **Metallic Crystal Structures** — FCC, BCC, HCP geometry, coordination, close-packed stacking sequences (~14)
- **Atomic Packing Factor and Density** — packing efficiency, theoretical density, atoms per volume, allotropic volume change (~28)
- **Linear and Planar Densities** — atoms per unit length and area on directions and planes (~13)
- **Interstitial Voids and Radius Ratio** — tetrahedral and octahedral sites, largest fitting sphere, coordination limits (~14)
- **Ionic Crystal Structures** — rock salt, CsCl, fluorite, corundum and ilmenite-type structures (~12)
- **Diamond Cubic and Zinc Blende** — covalent structures of Si, Ge, GaAs, ZnS (~7)
### X-Ray Diffraction
- **Bragg's Law** — diffraction angle, wavelength and interplanar spacing (~13)
- **Reflection Rules and Structure Factor** — allowed reflections for SC, BCC, FCC and diamond cubic (~9)
- **Powder Method and Indexing** — Debye-Scherrer patterns, indexing lines, identifying cubic lattices (~11)
### Crystal Imperfections
- **Vacancy Concentration** — equilibrium vacancies, formation energy, quenched-in vacancies (~10)
- **Point Defects in Ionic Crystals** — Schottky and Frenkel defects, nonstoichiometry, charge compensation (~8)
- **Solid Solutions and Hume-Rothery Rules** — substitutional and interstitial solid solutions, solubility criteria (~8)
- **Specification of Composition** — weight and atom percent conversions, solute atoms per volume (~13)
- **Edge, Screw and Mixed Dislocations** — Burgers vectors and circuits, line sense, dislocation geometry (~14)
- **Dislocation Energy and Interactions** — line energy, stored energy, climb, dislocation reactions (~11)
- **Interfacial Defects** — grain and tilt boundaries, twins, stacking faults, surface energy (~12)
- **Grain Size Measurement** — ASTM grain-size number, intercept method (~10)

## Thermodynamics and Kinetics of Materials
### Equilibrium and Thermal Activation
- **Free Energy and Phase Stability** — enthalpy, entropy and Gibbs energy of solids; free energy of melting (~7)
- **Entropy of Mixing** — configurational entropy of atoms on lattice sites (~4)
- **Arrhenius Equation and Activation Energy** — Boltzmann factor, rate versus temperature, activation energy from data (~11)
### Diffusion
- **Fick's First Law** — steady-state flux, membranes, gas permeation through metals and polymers (~10)
- **Fick's Second Law** — error-function solutions, carburizing, nitriding, diffusion couples (~15)
- **Temperature Dependence of Diffusivity** — D0 and activation energy, Arrhenius plots of diffusion coefficients (~14)
- **Atomic Mechanisms of Diffusion** — vacancy and interstitial jumps, Kirkendall effect, grain-boundary and surface paths (~12)
- **Diffusion Doping of Semiconductors** — predeposition and drive-in of dopants in silicon (~5)
### Phase Diagrams
- **Gibbs Phase Rule** — degrees of freedom, unary pressure-temperature diagrams (~13)
- **Isomorphous Systems** — complete solid solubility, liquidus and solidus, Cu-Ni type (~6)
- **Lever Rule** — phase compositions and mass or volume fractions in two-phase regions (~12)
- **Eutectic Systems and Microstructure** — primary and eutectic constituents, Pb-Sn type alloys (~19)
- **Invariant Reactions and Intermediate Phases** — eutectoid, peritectic, compounds; constructing diagrams from data (~17)
- **Iron-Iron Carbide Phase Diagram** — Fe-C phases, pearlite, proeutectoid ferrite and cementite fractions (~21)
### Phase Transformations
- **Homogeneous Nucleation** — critical radius, nucleation barrier, undercooling, nucleation rate (~11)
- **Heterogeneous Nucleation** — contact angle, shape factor, nucleating agents (~8)
- **Transformation Kinetics and Avrami Equation** — growth rate, fraction transformed versus time (~8)
- **Recovery and Recrystallization** — recrystallization temperature and kinetics, hot versus cold working (~9)
- **Grain Growth** — boundary-energy driving force, grain-growth kinetics (~9)
### Heat Treatment
- **Isothermal Transformation Diagrams** — TTT curves for steels, microstructures from isothermal treatments (~12)
- **Continuous-Cooling Transformation Diagrams** — CCT curves, critical cooling rate (~6)
- **Transformation Products of Austenite** — pearlite, bainite and martensite: mechanisms, morphology, hardness, ductility (~13)
- **Tempered Martensite** — tempering temperature and time, resulting properties (~5)
- **Hardenability and Jominy Test** — hardness profiles, quench media, section size (~7)
- **Annealing Processes** — full anneal, normalizing, spheroidizing, process anneal (~3)
- **Precipitation Hardening** — solution treatment, ageing, overageing; mechanism theory in Strengthening Mechanisms (~10)

## Mechanical Behavior of Materials
### Elastic and Viscoelastic Behavior
- **Elastic Deformation** — modulus values and temperature dependence; Hooke's-law stress analysis stays in Mechanics (~3)
- **Anelasticity** — relaxation, internal friction, grain-boundary sliding (~3)
- **Viscoelastic Models** — Maxwell and Voigt-Kelvin elements, relaxation modulus of polymers (~10)
- **Rubber Elasticity** — entropy elasticity, thermoelastic contraction of stretched elastomers (~6)
### Tensile Testing and Hardness
- **Engineering Stress-Strain Curve** — yield and tensile strength, ductility, resilience, toughness from test data (~12)
- **True Stress and True Strain** — true-stress conversion, strain-hardening exponent (~4)
- **Hardness Testing** — Brinell, Vickers, Rockwell; hardness-strength correlation (~4)
### Plastic Deformation of Crystals
- **Slip Systems** — slip planes and directions in FCC, BCC, HCP (~3)
- **Resolved Shear Stress and Schmid's Law** — critical resolved shear stress, crystal orientation (~9)
- **Theoretical Shear Strength and Dislocation Motion** — perfect versus real crystals, Peierls stress, dislocation width (~6)
- **Frank-Read Source** — dislocation multiplication (~3)
### Strengthening Mechanisms
- **Strain Hardening and Cold Work** — dislocation density, percent cold work, stored energy (~12)
- **Grain-Size Strengthening** — Hall-Petch relation, grain refinement (~12)
- **Solid-Solution Strengthening** — solute size misfit and yield stress (~4)
- **Precipitate and Dispersion Strengthening** — particle spacing, Orowan bowing; heat treatment in Precipitation Hardening (~4)
### Fracture
- **Ductile and Brittle Fracture** — fracture modes, why crystals and glasses are ductile or brittle (~9)
- **Griffith Theory of Brittle Fracture** — crack length, surface energy, fracture stress of glasses (~13)
- **Fracture Toughness** — plane-strain fracture toughness, critical crack size (~1)
- **Ductile-Brittle Transition and Impact Testing** — Charpy data, transition temperature (~3)
### Fatigue and Creep
- **Fatigue and S-N Curves** — fatigue limit, fatigue life, improving fatigue resistance (~9)
- **Creep Curve and Steady-State Creep Rate** — creep stages, stress and temperature dependence (~4)
- **Creep Rupture and Larson-Miller Parameter** — rupture-life prediction and extrapolation (~6)
- **Creep Mechanisms and Creep-Resistant Materials** — homologous temperature, dispersion-strengthened alloys (~5)

## Electrical, Magnetic, Optical and Thermal Properties
### Electrical and Dielectric Properties
- **Free Electron Theory and Fermi Energy** — electron in a box, quantum-state degeneracy, Fermi energy and velocity (~11)
- **Fermi-Dirac Distribution** — occupation probability versus energy and temperature (~6)
- **Electrical Conductivity and Mobility** — conductivity from carrier density and mobility, drift velocity, collision time (~13)
- **Resistivity of Metals** — thermal and impurity contributions, Matthiessen's rule (~5)
- **Conductor and Resistor Materials** — conductor alloys, heating elements, temperature coefficient of resistance (~8)
- **Superconductivity** — critical temperature, field and current; high-Tc oxides, Josephson junctions (~11)
- **Polarization and Dielectric Constant** — polarization mechanisms, frequency dependence, dielectric strength (~5)
- **Ferroelectricity and Piezoelectricity** — BaTiO3, ferroelectric Curie temperature, piezoelectric response (~1)
### Semiconductors
- **Energy Bands and Band Gap** — band formation, Brillouin zones, band gaps of metals, semiconductors, insulators (~13)
- **Intrinsic Semiconductors** — intrinsic carrier density, temperature dependence of conductivity (~15)
- **Extrinsic Semiconductors** — donors and acceptors, n- and p-type carrier concentrations, dopant ionization (~20)
- **Hall Effect** — Hall coefficient, carrier type and concentration (~2)
- **p-n Junctions and Transistors** — junction current under bias, transistor action (~5)
- **Crystal Growth and Purification of Silicon** — Czochralski, float zone, zone refining, segregation coefficient (~11)
- **Integrated Circuit Fabrication** — oxide masking, ion implantation, epitaxy, lithography, metallization, electromigration (~10)
### Magnetic Materials
- **Magnetization and Susceptibility** — relations between B, H, M, permeability and susceptibility (~3)
- **Diamagnetism and Paramagnetism** — origin and sign of susceptibility; superconductor as perfect diamagnet (~2)
- **Ferromagnetism and Atomic Moments** — moments from electron configuration, saturation magnetization (~8)
- **Curie Temperature** — loss of ferromagnetism on heating, Curie and Neel temperatures (~5)
- **Ferrimagnetism and Ferrites** — antiferromagnetism, spinel ferrites, garnets, moment per formula unit (~9)
- **Domains and Hysteresis** — domain walls, hysteresis loop, remanence, coercivity, magnetic anisotropy (~6)
- **Soft Magnetic Materials** — silicon steels, Fe-Ni alloys and ferrites for cores (~3)
- **Hard Magnetic Materials** — permanent-magnet materials, energy product, rare-earth magnets (~3)
### Optical Properties
- **Absorption, Transmission and Color** — band-gap absorption, transparency range, color, opacity, photoconductivity (~9)
- **Refractive Index and Reflectivity of Solids** — refractive index, reflectivity, birefringence in solids (~1)
- **Luminescence, LEDs and Lasers** — emission wavelength, ruby and semiconductor lasers (~4)
### Thermal Properties
- **Heat Capacity of Solids** — vibrational modes, Debye model (~4)
- **Thermal Shock and Thermal Stresses** — constrained expansion, thermal shock, quenching stresses (~5)
- **Thermal Conductivity of Materials** — phonon and electron conduction across material classes (~2)

## Engineering Materials
### Polymers
- **Repeat Units and Polymer Chemistry** — monomers, side groups, mer structures, cis-trans isomerism (~9)
- **Molecular Weight and Degree of Polymerization** — number- and weight-average molecular weight, chain length (~9)
- **Copolymers** — random, alternating and block copolymer compositions (~3)
- **Crosslinking and Vulcanization** — sulfur needed for crosslinking, network polymers (~5)
- **Polymer Crystallinity** — percent crystallinity from density, factors promoting crystallinity (~4)
- **Thermoplastics, Thermosets and Elastomers** — classification by structure and thermal behavior (~4)
- **Melting and Glass Transition of Polymers** — Tg and Tm, factors that raise them (~3)
- **Mechanical Behavior of Polymers** — strength and modulus versus molecular weight, crystallinity, crosslinking (~8)
- **Polymerization and Polymer Processing** — addition and condensation polymerization, additives, forming techniques (~7)
### Ceramics and Glasses
- **Silicate and Carbon Structures** — silica tetrahedra, silicates, graphite, diamond, fullerenes (~2)
- **Glass Formation and Glass Properties** — glass-forming tendency, glass compositions, annealing points (~5)
- **Mechanical Behavior of Ceramics** — flexural strength, porosity effects, strength scatter (~6)
- **Tempered and Chemically Strengthened Glass** — residual compressive surface stress, ion exchange (~5)
- **Clay Products and Refractories** — hydroplasticity, drying, firing, vitrification, refractories, cements (~6)
### Composites
- **Particle-Reinforced Composites** — rule-of-mixtures bounds for particulate composites and multiphase alloys (~3)
- **Fiber-Reinforced Composites** — longitudinal and transverse modulus and strength by rule of mixtures (~10)
- **Critical Fiber Length** — fiber length and reinforcement efficiency (~1)
- **Laminar Composites and Sandwich Panels** — structural composites; laminate stiffness analysis belongs to Mechanics (~2)
### Metal Alloys and Fabrication
- **Ferrous Alloys and Cast Irons** — steels, stainless steels, gray, ductile and malleable irons (~4)
- **Nonferrous Alloys** — Al, Cu, Ti and refractory alloys, alloy selection (~4)
- **Metal Forming and Casting** — forging, rolling, extrusion and casting techniques (~3)
### Corrosion and Oxidation
- **Electrochemical Cells and Electrode Potentials** — half-reactions, Nernst equation, galvanic cells (~8)
- **Corrosion Rate** — corrosion penetration rate, Faraday's law, electroplating (~6)
- **Polarization and Passivity** — activation and concentration polarization, passive films (~2)
- **Forms of Corrosion** — galvanic, crevice, pitting, intergranular, stress corrosion (~2)
- **Corrosion Prevention** — coatings, cathodic protection, inhibitors, material selection (~6)
- **Pilling-Bedworth Ratio** — protective versus non-protective oxide scales (~4)
- **Oxidation Rate Laws** — linear, parabolic and logarithmic oxide growth, oxidation of silicon (~10)


# Conventional Energy Technologies
_5 topic(s), 25 branches, 166 subtopics, ~2445 questions_

## Thermal Power Plant Engineering
### Steam Power Plant Cycles
- **Rankine Cycle Steam Plant Performance** — ideal and actual simple steam plant cycle: work, efficiency, steam rate (~21)
- **Effect of Steam Conditions on Plant Efficiency** — boiler pressure, superheat, condenser pressure, mean temperature of heat addition (~19)
- **Steam Reheating and Optimum Reheat Pressure** — single and double reheat; effect on output, efficiency, exhaust quality (~12)
- **Regenerative Feedwater Heating** — bleed-steam cycles, optimum regeneration; heater hardware: see Closed and Open Feedwater Heaters (~31)
- **Cogeneration and Process Steam Plants** — back-pressure and pass-out turbines, power-to-heat ratio, cogeneration efficiency (~21)
- **Binary Vapor and Coupled Cycle Plants** — mercury-steam and multi-fluid cycles, ideal working fluid, coupled-cycle efficiency (~20)
- **Overall Plant Efficiency and Heat Rate** — product of component efficiencies, heat rate, steam rate, plant exergy analysis (~22)
### Fuels and Combustion
- **Coal Ranks and Properties** — fuel classification, coal formation and ranks, caking, grindability, weathering, ash fusion (~26)
- **Proximate and Ultimate Analysis of Coal** — what each analysis measures; excludes combustion calculations (~8)
- **Calorific Value of Fuels** — higher and lower heating values, bomb calorimeter, Dulong's formula (~8)
- **Fuel Oil Properties** — origin, constituents, flash and pour points, viscosity, requirements for boiler firing (~11)
- **Gaseous Fuels** — natural gas, LPG, CNG, producer, water, coke-oven and blast-furnace gas (~14)
- **Fuel Emulsions, Slurries and Waste Fuels** — coal-oil and coal-water mixtures, oil emulsions, industrial and wood wastes (~10)
- **Coal Gasification and Gasifiers** — gasification reactions; fixed, fluidized, entrained and underground gasification (~9)
- **Coal Liquefaction and Synthetic Fuels** — synfuels, Fischer-Tropsch, hydrogenation, catalytic conversion, hydropyrolysis (~8)
- **Air Requirement for Fuel Combustion** — stoichiometric and excess air, mass-volume conversions, flue gas per kg fuel (~25)
- **Flue Gas Analysis and Excess Air** — Orsat analysis; deducing fuel composition and excess air from products (~22)
- **Furnace Flame Temperature and Dissociation** — adiabatic flame temperature, free energy, equilibrium constant, dissociation (~6)
- **Solid Fuel Combustion Kinetics** — Arrhenius rates, kinetic versus diffusion control, char particle and oil droplet burning (~23)
### Coal Handling and Firing Systems
- **Coal Handling and Fuel Storage** — transport, unloading, conveyors, crushers, stockpiles, oil storage, handling plant layout (~17)
- **Mechanical Stokers** — overfeed, underfeed, chain, traveling-grate and spreader stokers; fuel-bed burning sequence (~23)
- **Coal Pulverizing Mills** — ball, bowl and impact mills; pulverizer performance and fineness (~10)
- **Pulverized Coal Firing Systems** — unit and central systems, direct firing, particle burning time, furnace heat release (~9)
- **Burners and Combustion Air Supply** — PF burner types, tangential and tilting firing; primary, secondary, tertiary air (~19)
- **Coal-Fired Furnace Types** — fuel-bed, dry-bottom, wet-bottom (slag-tap), cyclone and pressurized furnaces (~10)
- **Oil and Gas Firing** — oil-burning installation, atomizers, oil, gas and combined burners (~7)
- **Fluidization Hydrodynamics in FBC Boilers** — minimum fluidization, regimes, voidage, elutriation, CFB riser, loop seals (~31)
- **Fluidized Bed Combustion Systems** — bubbling, circulating and pressurized FBC; sulfur capture, low NOx, CFB boilers (~29)
### Steam Generators
- **Fire-Tube and Water-Tube Boilers** — boiler classification and comparison; Cochran, Babcock-Wilcox, Stirling, package boilers (~14)
- **Boiler Mountings, Accessories and Piping** — safety valves, fusible plug, feed pumps, injectors, separators, steam piping (~13)
- **Boiler Water Circulation** — natural and forced circulation, circulation ratio, risers, downcomers, water walls, DNB (~22)
- **Steam Drum and Drum Internals** — drum functions, primary and secondary separators, moisture carryover (~8)
- **High-Pressure and Supercritical Boilers** — La Mont, Benson, Loeffler, Velox; once-through and supercritical units (~16)
- **Economizers** — steaming and non-steaming economizers, finned tubes, water velocity, flue gas heat recovery (~11)
- **Superheaters and Reheaters** — convective and radiant superheaters, platens, pendant coils, coil sizing (~12)
- **Air Preheaters** — recuperative and regenerative (Ljungstrom) preheaters, acid dew point, sizing (~12)
- **Steam Generator Control** — pressure, drum-level and steam-temperature control; desuperheaters, gas recirculation (~9)
- **Equivalent Evaporation** — evaporative capacity, equivalent evaporation, factor of evaporation (~8)
- **Boiler Efficiency and Heat Losses** — boiler trials, heat balance sheet, steam generator mass and energy balance (~36)
### Draught Systems
- **Natural Draught and Chimney Height** — chimney draught, height and diameter, maximum discharge, chimney efficiency, plume (~26)
- **Forced, Induced and Balanced Draught** — mechanical and steam-jet draught compared; fan power for draught (~25)
- **Draught Fans and Fan Control** — FD, ID and PA fans, blade forms, damper and speed control, noise (~10)
### Steam Nozzles and Turbines
- **Steam Nozzle Flow and Critical Pressure** — nozzle shapes, critical pressure ratio, choking, throat and exit areas, efficiency (~49)
- **Supersaturated Flow in Steam Nozzles** — metastable expansion, Wilson line, degree of supersaturation (~5)
- **Impulse and Reaction Turbine Principles** — classification, energy conversion in blades, De Laval and Parsons turbines (~14)
- **Compounding of Steam Turbines** — pressure, velocity and pressure-velocity compounding; Curtis and Rateau stages (~13)
- **Impulse Steam Turbine Stages** — velocity diagrams, blade efficiency, optimum blade speed ratio, axial thrust (~44)
- **Reaction Steam Turbine Stages** — degree of reaction, 50% reaction stages, blade heights, stage work (~23)
- **Reheat Factor and Stage Efficiency** — condition line, reheat factor, stage and internal efficiency of multistage turbines (~14)
- **Steam Turbine Losses** — nozzle, blade, disc friction, windage, wetness and leakage losses; labyrinth glands (~7)
- **Steam Turbine Governing** — throttle, nozzle and bypass governing; Willans line, governors, servo systems (~14)
- **Steam Turbine Blading and Rotors** — blade stresses and fastening, shrouds, lacing wires, critical speed, casing arrangements (~15)
### Condensers, Feedwater Heaters and Cooling Towers
- **Jet and Surface Condenser Types** — condenser functions; jet, barometric, ejector, evaporative and surface condensers compared (~20)
- **Surface Condenser Performance** — vacuum and condenser efficiency, cooling water flow, TTD, subcooling, tube design (~27)
- **Air Leakage and Air Extraction** — sources and effects of air in condensers, air pumps, steam jet air ejectors (~10)
- **Closed and Open Feedwater Heaters** — heater types, drips, drain coolers, three-zone heaters, TTD, heater location (~16)
- **Deaerators** — deaeration, deaerator types, elevation above the boiler feed pump (~8)
- **Power Plant Cooling Towers** — towers and ponds, approach, range, water loss, dry towers, thermal pollution (~31)
### Boiler Feedwater Treatment
- **Water Impurities and Boiler Troubles** — impurity classes; scale, corrosion, priming, foaming, carryover (~10)
- **External Feedwater Treatment** — clarification, lime-soda, zeolite, demineralization, silica removal, evaporators, reverse osmosis (~16)
- **Internal Treatment and Blowdown** — phosphate and hydrazine dosing, pH control, blowdown, steam washing (~13)
### Ash, Dust and Emission Control
- **Ash Handling and Disposal** — hydraulic, pneumatic and mechanical ash systems; fly ash composition and uses (~13)
- **Dust Collectors and Precipitators** — cyclone separators, electrostatic precipitators, fabric filters, collection efficiency (~17)
- **Gaseous Emissions and Acid Rain** — SOx, NOx and particulates, scrubbers, acid rain, smog, greenhouse effect (~10)
### Diesel Engine Power Plants
- **Diesel Plant Applications and Merits** — uses, advantages, limitations, engine choice; diesel versus steam plants (~19)
- **Diesel Plant Layout and Auxiliaries** — essential components, layout, air intake, exhaust, starting systems, operation (~11)
- **IC Engine Classification and Terminology** — heat engines, engine parts, bore, stroke, compression ratio, piston speed (~15)
- **Four-Stroke and Two-Stroke Engines** — working cycles, valve timing, comparison of the two (~11)
- **Petrol and Diesel Engine Comparison** — SI versus CI: ignition, mixture supply, governing, fuel consumption, efficiency (~19)
- **Fuel Injection Systems** — fuel pumps, injectors, nozzles, solid and air injection (~6)
- **Engine Cooling Systems** — air and water cooling, thermosyphon and thermostatic systems, heat to coolant (~8)
- **Engine Lubrication Systems** — splash, pressure, wet-sump and dry-sump lubrication (~8)
- **Combustion and Knock in IC Engines** — ignition delay, diesel and SI knock, cetane and octane numbers, combustion chambers (~18)
- **Supercharging and Turbocharging** — purpose, mechanical superchargers, turbochargers, intercooling (~8)
- **Engine Performance and Testing** — ip, bp, mep, efficiencies, bsfc, Morse test, Willans line, heat balance (~39)
- **Air-Standard Cycles for Engine Plants** — Otto, Diesel and dual cycle efficiency for plant engines (~14)
### Gas Turbine and Combined Cycle Plants
- **Gas Turbine Plant Merits and Applications** — uses, peaking duty, advantages and limitations versus diesel and steam plants (~20)
- **Gas Turbine Plant Arrangements** — open, closed, semi-closed, constant-volume and free-piston plants; layout, starting (~24)
- **Gas Turbine Plant Cycle Performance** — net work, efficiency, work ratio, optimum pressure ratio, component efficiencies (~22)
- **Regeneration, Intercooling and Reheat in GT Plants** — effect on work and efficiency; multistage plant calculations (~19)
- **Gas Turbine Plant Compressors** — centrifugal and axial compressors, slip, pre-whirl, stage temperature rise (~14)
- **Gas Turbine Blading, Cooling and Materials** — axial turbine stages, blade cooling, blade materials, ash attack (~9)
- **Gas Turbine Combustors and Fuels** — combustion chamber design, dilution, combustion efficiency, gas turbine fuels (~11)
- **Gas-Steam Combined Cycle Plants** — HRSG, pinch point, supplementary firing, dual pressure, repowering, STIG (~23)
- **Integrated Gasification Combined Cycle** — IGCC plants, gas cleanup, coal-based combined cycles (~7)

## Hydroelectric Power Engineering
### Hydrology for Hydro Plants
- **Hydrologic Cycle, Rainfall and Runoff** — precipitation, average rainfall methods, runoff measurement and influencing factors (~16)
- **Hydrographs and Flow Duration Curves** — hydrograph, unit hydrograph, flow and power duration curves, firm power (~17)
- **Mass Curves, Storage and Pondage** — catchment area, reservoir capacity from mass curves, storage versus pondage (~12)
- **Available Hydro Power and Plant Capacity** — power from head and discharge, firm capacity, hydro site output calculations (~25)
### Hydro Plant Elements and Types
- **Dams and Spillways** — dam functions and types, spillway types (~13)
- **Water Conduits and Penstocks** — headrace, canals, flumes, tunnels, penstocks, water hammer, penstock thickness (~16)
- **Surge Tanks and Forebays** — purpose, location and types of surge tanks; forebays (~13)
- **Powerhouse Layout and Hydro Plant Controls** — powerhouse equipment, plant layouts, underground stations, controls, safety, maintenance (~12)
- **Classification of Hydro Plants** — by head, load and storage; run-of-river, storage, mini and micro hydel (~8)
- **Pumped Storage Plants** — operation, turnaround efficiency, reversible units; sole home for pumped hydro storage (~7)
- **Hydro Plant Merits and Comparison** — advantages, disadvantages, comparison with thermal plants, development in India (~9)
### Hydraulic Turbines
- **Hydro Turbine Classification** — impulse versus reaction, flow direction, head ranges, degree of reaction (~11)
- **Pelton Wheel Hydro Turbines** — jets, buckets, jet and speed ratios, design and efficiency calculations (~30)
- **Francis Hydro Turbines** — runner, velocity triangles, design and performance calculations (~21)
- **Kaplan, Propeller and Bulb Turbines** — adjustable-blade, propeller, Deriaz and tubular turbines for low heads (~14)
- **Specific Speed and Turbine Characteristics** — specific speed, unit quantities, model similarity, performance curves, runaway speed (~27)
- **Hydro Plant Draft Tubes** — function, types and efficiency of draft tubes (~4)
- **Cavitation in Hydro Turbines** — causes, effects, pitting and prevention of cavitation (~5)
- **Hydro Turbine Governing** — governing of impulse and reaction turbines; spear, deflector, servomotors (~10)
- **Hydro Turbine Selection** — choosing turbine type, size and number of jets from head and speed (~8)

## Nuclear Power Engineering
### Nuclear Physics for Reactors
- **Atomic Structure and Isotopes (Nuclear Power)** — atomic and mass numbers, amu, isotopes and isotones (~7)
- **Mass Defect and Binding Energy (Nuclear Power)** — mass defect, binding energy per nucleon, nuclear stability (~7)
- **Radioactive Decay and Half-Life (Nuclear Power)** — radiation types, decay, half-life, activity, curie and roentgen (~18)
- **Fission and Fissile Fuels** — fission process and products, energy per fission, fissile and fertile materials (~14)
- **Fusion Power Reactors** — fusion reactions, deuterium and tritium sources, fusion versus fission (~6)
### Reactor Physics
- **Neutron Cross Sections and Flux** — microscopic and macroscopic cross sections, barn, neutron flux, reaction rate (~13)
- **Neutron Moderation and Moderators** — scattering, logarithmic energy decrement, moderating power and ratio, moderator choice (~15)
- **Chain Reaction and Multiplication Factor** — four-factor formula, criticality, critical mass, prompt and delayed neutrons, reactor period (~22)
- **Reactor Power and Fuel Consumption** — fission rate, power density, burnup, poisoning, fuel consumed per year (~10)
### Nuclear Reactors and Plants
- **Reactor Components and Materials** — core, fuel, control rods, reflector, coolant, cladding, shielding; material selection (~17)
- **Classification of Reactors** — thermal versus fast, homogeneous versus heterogeneous, by coolant and moderator (~7)
- **Pressurized and Boiling Water Reactors** — PWR and pressurizer, BWR, their comparison and steam conditions (~11)
- **CANDU Heavy Water Reactors** — natural-uranium heavy-water reactors, calandria (~3)
- **Gas-Cooled Reactors** — Magnox, AGR and HTGR features (~4)
- **Fast Breeder Reactors** — LMFBR, liquid metal coolants, breeding and conversion ratio (~9)
- **Nuclear Power Plant Layout and Merits** — plant components, advantages, applications, economics, future of nuclear power (~13)
- **Nuclear Safety and Waste Disposal** — safety measures, radiation hazards, radioactive waste storage and disposal (~4)
- **India's Nuclear Power Program** — three-stage programme, thorium breeders, Indian reactors (~6)

## Power Plant Economics and Operation
### Load Curves and Plant Factors
- **Load Curves and Load Duration Curves** — chronological load curves, constructing load duration curves, types of load (~26)
- **Load, Demand and Diversity Factors** — definitions and calculations of load factor, demand factor, diversity factor (~26)
- **Capacity Factor, Use Factor and Reserve** — plant capacity and use factors, reserve factor, spinning and hot reserve (~20)
### Cost of Power Generation
- **Fixed and Operating Costs** — capital, fixed and running cost elements, economy of scale, cost reduction (~24)
- **Cost of Generation per kWh** — annual cost and unit generation cost calculations (~23)
- **Plant Depreciation and Present Worth** — straight-line and sinking-fund methods, present worth, interest, useful life (~21)
- **Economic Comparison of Plant Alternatives** — choosing a supply or plant by annual cost; break-even load factor (~14)
- **Tariffs for Electrical Energy** — flat, block, two-part (Hopkinson) and three-part tariffs; consumer bills (~15)
### Load Sharing and Combined Operation
- **Economic Load Sharing and Incremental Rates** — input-output curves, incremental heat rate and cost, equal-incremental loading (~18)
- **Base Load and Peak Load Plants** — plant mix on the load duration curve, peaking plants, peak shaving, load levelling (~15)
- **Combined Hydro-Thermal Operation** — hydro-steam coordination; run-of-river and pumped storage working with thermal plants (~15)
### Power Plant Planning and Selection
- **Energy Resources and Demand** — energy sources, commercial and non-commercial energy, electricity demand growth, Indian scenario (~14)
- **Types of Power Plants Compared** — principal plant types; comparing steam, hydro, diesel, gas turbine, nuclear plants (~12)
- **Installed Capacity and Unit Size** — fixing plant capacity, unit size, number of units, turbo-generator ratings (~11)
- **Power Plant Site Selection** — site factors for steam, hydro, nuclear, diesel and gas turbine plants; load center (~15)
- **Plant Design Principles and Layout** — design requirements, building layout, general steam station layout (~8)
### Station Electrical Equipment and Instrumentation
- **Station Generators and Exciters** — alternators, DC generators, exciters, synchronizing, hydrogen and air generator cooling (~24)
- **Station Transformers** — transformer types and three-phase transformer connections (~7)
- **Switchgear and Circuit Breakers** — switches, fuses, circuit breakers, arc interruption (~13)
- **Station Protection and Earthing** — relays, equipment protection, short circuits, neutral earthing, control room layout (~11)
- **Transmission Lines, Cables and Substations** — overhead and underground transmission, line supports, insulators, substations (~11)
- **Pressure Measuring Instruments** — instrument classification, manometers, Bourdon gauges, electrical pressure transducers (~7)
- **Temperature Measuring Instruments** — thermometers, thermocouples, resistance thermometers, radiation and optical pyrometers (~10)
- **Flow, Level and Humidity Instruments** — gauge glasses, level gauges, flow meters, hygrometers, steam quality calorimeters (~6)

## Non-Conventional Power and Energy Storage
### Renewable Power Plants
- **Solar Collectors and Insolation** — solar radiation, flat-plate and concentrating collectors, tracking, pyranometers (~14)
- **Solar Thermal Power Plants** — solar ponds, central tower, solar farms; low to high temperature systems (~9)
- **Photovoltaic Power Systems** — solar cell operation, materials, fill factor, merits, satellite power stations (~9)
- **Wind Power Plants** — wind power, power coefficient, windmill types, wind-electric systems, wind economics (~9)
- **Tidal Power Plants** — tides, single and double basin schemes, tidal turbines, output calculations (~13)
- **Wave Energy and Ocean Thermal Conversion** — wave power machines and OTEC plants (~4)
- **Geothermal Power Plants** — geothermal sources; dry steam, flash and binary plants; hot dry rock (~15)
- **Biomass and Biogas Energy** — bioconversion routes, anaerobic digestion, fermentation, gasohol, biogas plants, energy farms (~16)
### Direct Energy Conversion
- **MHD Power Generation** — MHD principle, open and closed cycles, seeding, MHD-steam and MHD-gas turbine plants (~20)
- **Thermionic Power Generators** — work function, Richardson-Dushman equation, cesium converters, efficiency, topping use (~13)
- **Thermoelectric Power Generators** — Seebeck and Peltier effects, figure of merit, optimum design, materials, topping use (~20)
- **Fuel Cell Power Generation** — fuel cell principle, hydrogen-oxygen cell, cell types, thermodynamics, applications (~15)
### Energy Storage
- **Compressed Air Energy Storage** — CAES caverns, adiabatic and hybrid schemes, Huntorf and McIntosh plants (~7)
- **Flywheel Energy Storage** — stored energy, shape factor, flywheel materials (~4)
- **Electrochemical Battery Storage** — lead-acid, alkaline and advanced batteries, emf, solid electrolytes (~8)
- **Superconducting Magnetic Energy Storage** — SMES coils, Brooks coil, structural requirements (~4)
- **Thermal Energy Storage** — sensible and latent heat storage, steam accumulators, thermal turnaround efficiency (~12)
- **Chemical Energy Storage** — reversible reactions, methanation-reforming, ammonia storage (~4)
- **Hydrogen Energy Systems** — hydrogen production, hydride storage, hydrogen economy, solar-hydrogen systems (~12)

