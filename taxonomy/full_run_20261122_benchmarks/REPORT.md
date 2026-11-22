# Classification of the benchmark imports (2026-11-22, fourth wave)

6,220 questions imported 2026-11-22 01:00-01:41 (ThermoQA, JEE Advanced, UGMathBench, TheoremQA, UGPhysics) plus the five answer-set rows the third wave left unclassified (owner 2026-11-21: "Go ahead with all recommendations, labels, etc."; order import -> classify -> solve -> judge -> embed). 3,308 have no solution (classified from the question alone). Held back, not in this run: 2,465 UGPhysics rows (Quantum Mechanics, Atomic Physics, Statistical Mechanics) whose subjects lack subtopics; a tree proposal is with the owner. Pipeline: Haiku first pass with the textbook tag file (Sonnet for the five competition rows); blind Sonnet second opinion on every medium/low, wastebasket or other-subject label and on the 102 UGPhysics rows whose dataset solution belonged to another problem (cleared before the second pass); Opus adjudication of every disagreement, A/B order random. Candidate subjects come from the datasets' own labels (UGMathBench subject, TheoremQA field/subfield, ThermoQA template kind, UGPhysics subject) or, for JEE Advanced, from keywords; Probability first for questions asking for a probability or expectation.

## Outcome

- Placed in a subtopic: 6,112; left `Uncategorized`: 108 (`wastebasket.csv`).
- How the final label was reached: high-confidence first pass 3,796; first and second agree 1,215; second opinion accepted 155; Opus 1,054.
- Confidence of the label kept (placed questions): high 4,379, medium 1,613, low 120. It goes into `classification_conf`, with `how` in `classification_how`.
- Flags: {'needs_data': 162, 'key_conflict': 76, 'broken_text': 47, 'mismatch': 50} (`flags.csv`).

| Source | Subjects (questions) |
|---|---|
| UGPhysics | Mechanics 1093, Electromagnetism and Special Relativity 1070, Thermodynamics 287, Material Science 261, Fluid Mechanics 91, wastebasket 65, Heat Transfer 32, Quantum Mechanics 14, Probability and Stochastic Processes 9, Linear Algebra and Differential Equations 7, Complex Analysis 6, Calculus 5, Statistics 2, Geometry 1 |
| UGMathBench | Calculus 685, Algebra 477, Quantitative Finance 273, Linear Algebra and Differential Equations 217, Probability and Stochastic Processes 133, Geometry 111, Statistics 78, Mechanics 47, Combinatorics 38, Number Theory 16, Abstract Algebra 15, wastebasket 8, Quantum Mechanics 4, Complex Analysis 4, Fluid Mechanics 3, Economics 1 |
| TheoremQA | Calculus 140, Combinatorics 89, Probability and Stochastic Processes 50, Quantitative Finance 50, Linear Algebra and Differential Equations 49, Mechanics 45, Number Theory 30, wastebasket 28, Electromagnetism and Special Relativity 26, Geometry 22, Complex Analysis 19, Algebra 18, Quantum Mechanics 14, Statistics 12, Economics 10, Abstract Algebra 10, Thermodynamics 8, Fluid Mechanics 6, Material Science 3 |
| Joint Entrance Examination Advanced | Calculus 69, Geometry 55, Algebra 41, Mechanics 40, Linear Algebra and Differential Equations 36, Electromagnetism and Special Relativity 27, Quantum Mechanics 22, Probability and Stochastic Processes 19, Combinatorics 16, Thermodynamics 11, Fluid Mechanics 8, wastebasket 7, Heat Transfer 6, Number Theory 1, Statistics 1 |
| ThermoQA | Thermodynamics 119, Conventional Energy Technologies 51, Heat Transfer 4 |
| Omni-MATH | Combinatorics 2, Probability and Stochastic Processes 2, Algebra 1 |

### Dataset label -> subject filed (labels with 5 or more questions)

- Joint Entran: JEE Advanced mathematics -> Calculus: 67
- Joint Entran: JEE Advanced mathematics -> Geometry: 55
- Joint Entran: JEE Advanced mathematics -> Algebra: 41
- Joint Entran: JEE Advanced mathematics -> Linear Algebra and Differential Equations: 36
- Joint Entran: JEE Advanced mathematics -> Probability and Stochastic Processes: 19
- Joint Entran: JEE Advanced mathematics -> Combinatorics: 16
- Joint Entran: JEE Advanced physics -> Mechanics: 40
- Joint Entran: JEE Advanced physics -> Electromagnetism and Special Relativity: 27
- Joint Entran: JEE Advanced physics -> Quantum Mechanics: 22
- Joint Entran: JEE Advanced physics -> Thermodynamics: 11
- Joint Entran: JEE Advanced physics -> Fluid Mechanics: 8
- Joint Entran: JEE Advanced physics -> Heat Transfer: 6
- TheoremQA: EECS / Graph theory -> Combinatorics: 31
- TheoremQA: Finance / Derivatives -> Quantitative Finance: 13
- TheoremQA: Finance / Equity investments -> Economics: 8
- TheoremQA: Finance / Fixed income -> Quantitative Finance: 11
- TheoremQA: Finance / Portfolio management -> Quantitative Finance: 9
- TheoremQA: Finance / Quantitive methods -> Quantitative Finance: 13
- TheoremQA: Math / Algebra -> Linear Algebra and Differential Equations: 38
- TheoremQA: Math / Algebra -> Algebra: 9
- TheoremQA: Math / Calculus -> Calculus: 88
- TheoremQA: Math / Calculus -> Linear Algebra and Differential Equations: 8
- TheoremQA: Math / Combinatorics -> Combinatorics: 57
- TheoremQA: Math / Complex analysis -> Complex Analysis: 19
- TheoremQA: Math / Functional analysis -> Calculus: 8
- TheoremQA: Math / Geometry -> Geometry: 20
- TheoremQA: Math / Group theory -> Abstract Algebra: 10
- TheoremQA: Math / Mathematical analysis -> Calculus: 34
- TheoremQA: Math / Number theory -> Number Theory: 28
- TheoremQA: Math / Probability theory -> Probability and Stochastic Processes: 19
- TheoremQA: Math / Real analysis -> Calculus: 7
- TheoremQA: Math / Statistics -> Probability and Stochastic Processes: 12
- TheoremQA: Math / Statistics -> Statistics: 12
- TheoremQA: Math / Stochastic process -> Probability and Stochastic Processes: 16
- TheoremQA: Physics / Atomic physics -> Quantum Mechanics: 5
- TheoremQA: Physics / Celestial mechanics -> Mechanics: 6
- TheoremQA: Physics / Electromagnetism -> Electromagnetism and Special Relativity: 16
- TheoremQA: Physics / Kinetics -> Mechanics: 28
- TheoremQA: Physics / Relativity -> Electromagnetism and Special Relativity: 6
- ThermoQA: gas-turbine (Brayton) cycle -> Conventional Energy Technologies: 25
- ThermoQA: power-plant cycle or boiler -> Conventional Energy Technologies: 20
- ThermoQA: power-plant cycle or boiler -> Thermodynamics: 6
- ThermoQA: property lookup of a pure substance -> Thermodynamics: 55
- ThermoQA: single steady-flow component -> Thermodynamics: 52
- ThermoQA: single steady-flow component -> Conventional Energy Technologies: 6
- ThermoQA: vapour-compression refrigeration cycle -> Thermodynamics: 6
- UGMathBench: Abstract algebra / Groups -> Abstract Algebra: 11
- UGMathBench: Algebra / Absolute value expressions and functions -> Algebra: 5
- UGMathBench: Algebra / Algebra of real numbers and simplifying expressions -> Algebra: 38
- UGMathBench: Algebra / Exponential and logarithmic expressions and functions -> Algebra: 26
- UGMathBench: Algebra / Factoring -> Algebra: 6
- UGMathBench: Algebra / Finite sequences and series -> Algebra: 14
- UGMathBench: Algebra / Functions -> Algebra: 8
- UGMathBench: Algebra / Linear equations and functions -> Algebra: 48
- UGMathBench: Algebra / Linear equations and functions -> Geometry: 8
- UGMathBench: Algebra / Operations on polynomial and rational expressions -> Algebra: 10
- UGMathBench: Algebra / Polynomial equations and functions -> Algebra: 6
- UGMathBench: Algebra / Properties of exponents -> Algebra: 12
- UGMathBench: Algebra / Quadratic equations and functions -> Algebra: 19
- UGMathBench: Algebra / Rational equations and functions -> Algebra: 5
- UGMathBench: Algebra / Variation and power functions -> Algebra: 9
- UGMathBench: Arithmetic / Decimals -> Algebra: 11
- UGMathBench: Arithmetic / Fractions/rational numbers -> Algebra: 57
- UGMathBench: Arithmetic / Integers -> Algebra: 64
- UGMathBench: Arithmetic / Irrational numbers -> Algebra: 9
- UGMathBench: Arithmetic / Percents -> Algebra: 24
- UGMathBench: Arithmetic / Units -> Algebra: 17
- UGMathBench: Calculus - multivariable / Calculus of vector valued functions -> Calculus: 33
- UGMathBench: Calculus - multivariable / Concepts for multivariable functions -> Geometry: 8
- UGMathBench: Calculus - multivariable / Differentiation of multivariable functions -> Calculus: 67
- UGMathBench: Calculus - multivariable / Fundamental theorems -> Calculus: 31
- UGMathBench: Calculus - multivariable / Integration of multivariable functions -> Calculus: 74
- UGMathBench: Calculus - multivariable / Vector calculus -> Calculus: 54
- UGMathBench: Calculus - single variable / Applications of differentiation -> Calculus: 103
- UGMathBench: Calculus - single variable / Applications of integration -> Calculus: 56
- UGMathBench: Calculus - single variable / Applications of integration -> Mechanics: 29
- UGMathBench: Calculus - single variable / Differentiation -> Calculus: 71
- UGMathBench: Calculus - single variable / Infinite sequences and series -> Calculus: 35
- UGMathBench: Calculus - single variable / Infinite sequences and series -> Algebra: 11
- UGMathBench: Calculus - single variable / Integrals -> Calculus: 29
- UGMathBench: Calculus - single variable / Limits and continuity -> Calculus: 44
- UGMathBench: Calculus - single variable / Parametric -> Calculus: 19
- UGMathBench: Calculus - single variable / Polar -> Calculus: 11
- UGMathBench: Calculus - single variable / Techniques of integration -> Calculus: 24
- UGMathBench: Combinatorics / Counting -> Combinatorics: 36
- UGMathBench: Complex analysis / Arithmetic -> Algebra: 10
- UGMathBench: Differential equations / First order differential equations -> Linear Algebra and Differential Equations: 67
- UGMathBench: Differential equations / Higher order differential equations -> Linear Algebra and Differential Equations: 14
- UGMathBench: Differential equations / Introductory concepts -> Linear Algebra and Differential Equations: 13
- UGMathBench: Differential equations / Laplace transforms -> Linear Algebra and Differential Equations: 10
- UGMathBench: Differential equations / Partial differential equations -> Linear Algebra and Differential Equations: 11
- UGMathBench: Financial mathematics / Annuities -> Quantitative Finance: 114
- UGMathBench: Financial mathematics / Bonds -> Quantitative Finance: 7
- UGMathBench: Financial mathematics / Equations of value -> Quantitative Finance: 11
- UGMathBench: Financial mathematics / Expected and contingent payments -> Probability and Stochastic Processes: 7
- UGMathBench: Financial mathematics / Expected and contingent payments -> Quantitative Finance: 5
- UGMathBench: Financial mathematics / Interest -> Quantitative Finance: 125
- UGMathBench: Financial mathematics / Options -> Quantitative Finance: 9
- UGMathBench: Geometry / Shapes -> Geometry: 6
- UGMathBench: Geometry / Vector geometry -> Geometry: 34
- UGMathBench: Geometry / Vector geometry -> Calculus: 22
- UGMathBench: Geometry / Vector geometry -> Mechanics: 8
- UGMathBench: Linear algebra / Determinants -> Linear Algebra and Differential Equations: 17
- UGMathBench: Linear algebra / Eigenvalues and eigenvectors -> Linear Algebra and Differential Equations: 9
- UGMathBench: Linear algebra / Euclidean spaces -> Linear Algebra and Differential Equations: 20
- UGMathBench: Linear algebra / Inner products -> Linear Algebra and Differential Equations: 10
- UGMathBench: Linear algebra / Linear transformations -> Linear Algebra and Differential Equations: 12
- UGMathBench: Linear algebra / Matrices -> Linear Algebra and Differential Equations: 6
- UGMathBench: Linear algebra / Systems of linear equations -> Linear Algebra and Differential Equations: 15
- UGMathBench: Linear algebra / Systems of linear equations -> Algebra: 6
- UGMathBench: Number theory / Divisibility -> Number Theory: 10
- UGMathBench: Probability / Continuous distributions -> Probability and Stochastic Processes: 29
- UGMathBench: Probability / Discrete distributions -> Probability and Stochastic Processes: 17
- UGMathBench: Probability / Random variables -> Probability and Stochastic Processes: 15
- UGMathBench: Probability / Sample Space -> Probability and Stochastic Processes: 53
- UGMathBench: Statistics / Confidence intervals -> Statistics: 27
- UGMathBench: Statistics / Exploratory data analysis/descriptive statistics -> Statistics: 7
- UGMathBench: Statistics / Hypothesis tests -> Statistics: 15
- UGMathBench: Statistics / Sampling distributions -> Statistics: 5
- UGMathBench: Statistics / Simple linear regression -> Statistics: 17
- UGMathBench: Trigonometry / Analytic trigonometry -> Algebra: 19
- UGMathBench: Trigonometry / Geometric and algebraic foundations for trigonometry -> Geometry: 10
- UGMathBench: Trigonometry / Geometric and algebraic foundations for trigonometry -> Algebra: 7
- UGMathBench: Trigonometry / Triangle trigonometry -> Geometry: 25
- UGMathBench: Trigonometry / Trigonometric functions -> Algebra: 15
- UGPhysics: Classical Electromagnetism / Circuit Analysis -> Electromagnetism and Special Relativity: 46
- UGPhysics: Classical Electromagnetism / Electrostatics -> Electromagnetism and Special Relativity: 179
- UGPhysics: Classical Electromagnetism / Magstatics -> Electromagnetism and Special Relativity: 146
- UGPhysics: Classical Mechanics / Central Force Motion -> Mechanics: 78
- UGPhysics: Classical Mechanics / Fluid Mechanics -> Fluid Mechanics: 69
- UGPhysics: Classical Mechanics / Fluid Mechanics -> Mechanics: 8
- UGPhysics: Classical Mechanics / Particle Dynamics -> Mechanics: 309
- UGPhysics: Classical Mechanics / Rigid-Body Dynamics -> Mechanics: 177
- UGPhysics: Classical Mechanics / Vibrations and Waves -> Mechanics: 170
- UGPhysics: Electrodynamics / Interaction of Electromagnetic Fields with Matter -> Electromagnetism and Special Relativity: 17
- UGPhysics: Electrodynamics / Interaction of Electromagnetic Fields with Matter -> Mechanics: 9
- UGPhysics: Electrodynamics / Propagation and Radiation of Electromagnetic Waves -> Electromagnetism and Special Relativity: 87
- UGPhysics: Electrodynamics / Relativistic Electrodynamics -> Electromagnetism and Special Relativity: 51
- UGPhysics: Electrodynamics / Relativistic Electrodynamics -> Mechanics: 7
- UGPhysics: Geometrical Optics / Imaging of Light -> Electromagnetism and Special Relativity: 44
- UGPhysics: Geometrical Optics / Reflection and Refraction of Light -> Electromagnetism and Special Relativity: 14
- UGPhysics: Relativity / Special Relativity -> Electromagnetism and Special Relativity: 174
- UGPhysics: Relativity / Special Relativity -> Mechanics: 10
- UGPhysics: Semiconductor Physics / Magnetic -> Material Science: 19
- UGPhysics: Semiconductor Physics / Magnetic -> Electromagnetism and Special Relativity: 6
- UGPhysics: Semiconductor Physics / Others -> Electromagnetism and Special Relativity: 14
- UGPhysics: Semiconductor Physics / Others -> Quantum Mechanics: 9
- UGPhysics: Semiconductor Physics / Others -> Probability and Stochastic Processes: 7
- UGPhysics: Semiconductor Physics / Others -> Material Science: 6
- UGPhysics: Semiconductor Physics / Others -> Complex Analysis: 6
- UGPhysics: Semiconductor Physics / Others -> Linear Algebra and Differential Equations: 5
- UGPhysics: Semiconductor Physics / Statistical Distribution of Electrons and Holes in Space -> Material Science: 27
- UGPhysics: Semiconductor Physics / Transport Properties -> Material Science: 39
- UGPhysics: Solid-State Physics / Binding in Solids -> Material Science: 27
- UGPhysics: Solid-State Physics / Crystal Defects and Motion -> Material Science: 17
- UGPhysics: Solid-State Physics / Crystal Structure -> Material Science: 14
- UGPhysics: Solid-State Physics / Energy Bands in Solids -> Material Science: 15
- UGPhysics: Solid-State Physics / Lattice Vibrations and Mechanical Properties of Solids -> Material Science: 39
- UGPhysics: Solid-State Physics / Motion of Electrons in Electromagnetic Fields -> Material Science: 19
- UGPhysics: Solid-State Physics / Transport Properties of Electrons and Holes in Solids -> Material Science: 29
- UGPhysics: Theoretical Mechanics / Hamiltonian Formulation of Mechanics -> Mechanics: 124
- UGPhysics: Theoretical Mechanics / Lagrangian Formulation of Mechanics -> Mechanics: 93
- UGPhysics: Theoretical Mechanics / Small Vibrations of Finite System -> Mechanics: 83
- UGPhysics: Theoretical Mechanics / Small Vibrations of Finite System -> Electromagnetism and Special Relativity: 6
- UGPhysics: Thermodynamics / Non-equilibrium Thermodynamics -> Heat Transfer: 21
- UGPhysics: Thermodynamics / Non-equilibrium Thermodynamics -> Thermodynamics: 5
- UGPhysics: Thermodynamics / Non-equilibrium Thermodynamics -> Mechanics: 5
- UGPhysics: Thermodynamics / Phase Transition and Equilibrium -> Thermodynamics: 67
- UGPhysics: Thermodynamics / Phase Transition and Equilibrium -> Material Science: 6
- UGPhysics: Thermodynamics / Second Law of Thermodynamics and Entropy -> Thermodynamics: 105
- UGPhysics: Thermodynamics / Thermodynamic Functions and Equilibrium Conditions -> Thermodynamics: 53
- UGPhysics: Thermodynamics / Thermodynamic State and First Law of Thermodynamics -> Thermodynamics: 49
- UGPhysics: Thermodynamics / Thermodynamic State and First Law of Thermodynamics -> Heat Transfer: 11
- UGPhysics: Thermodynamics / Thermodynamic State and First Law of Thermodynamics -> Fluid Mechanics: 7
- UGPhysics: Wave Optics / Diffraction -> Electromagnetism and Special Relativity: 78
- UGPhysics: Wave Optics / Diffraction -> Mechanics: 12
- UGPhysics: Wave Optics / Interference -> Electromagnetism and Special Relativity: 53
- UGPhysics: Wave Optics / Polarization -> Electromagnetism and Special Relativity: 143

## Proposed tags (not added)

- Entropy Balance (17 questions)
- Boundary-Region Conversion (9 questions)
- Fourier Transform Method (7 questions)
- Lagrange Multiplier (7 questions)
- Maxwell Relation (7 questions)
- Marginal Condition (5 questions)
- Sinusoidal Model Fitting (4 questions)
- Tight-Binding Sum (4 questions)
- Virial Theorem (3 questions)
- Residue Theorem (3 questions)
- Chinese Remainder Splitting (2 questions)

