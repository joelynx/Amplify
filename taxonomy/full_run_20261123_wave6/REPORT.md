# Classification of the 2026-11-23 imports and the moved nodes (sixth wave)

14,098 questions: the 12,960 rows imported 2026-11-23 (chemistry, chemical, electrical and control engineering, quantitative finance), the 156 JEE Advanced chemistry rows, and the 99 rows whose node moved to a new subject (owner 2026-11-23: trees "Approve as drafted"; moves "Mass transfer -> ChemE, Amplifiers + waveguides, Spectra + periodicity -> Chemistry, Particle beds -> ChemE"). The 18 Waveguides rows keep their node, which moves to the branch Transmission Lines, Waveguides and Antennas. 13,167 have no solution. Run through the subscription rotation (pipeline/scripts/run_classify.py, one request per batch): Haiku first pass with the textbook tag file, blind Sonnet second opinion on every medium/low, wastebasket, other-subject or invalid label and on every moved row filed outside its new subject, Opus adjudication of every disagreement. Candidate subjects from the datasets' own labels (SuperGPQA, MMLU-Pro, MMLU, ChemBench, QuantQA, TheoremQA) and the source.

## Outcome

- Placed in a subtopic: 13,795; left `Uncategorized`: 303 (`wastebasket.csv`).
- How the final label was reached: high-confidence first pass 7,165; first and second agree 3,057; second opinion accepted 656; Opus 3,220 (of them 8 moved rows Opus filed outside the node's new subject, in an existing node it judged closer).
- Confidence of the label kept (placed questions): high 10,005, medium 3,557, low 233. It goes into `classification_conf`, with `how` in `classification_how`.
- Flags: {'key_conflict': 108, 'needs_data': 154, 'broken_text': 325, 'mismatch': 10, 'open_problem': 14} (`flags.csv`).

| Source | Subjects (questions) |
|---|---|
| SuperGPQA | Chemistry 1581, Electromagnetism and Special Relativity 464, Signals, Systems and Control 385, Material Science 257, Chemical Engineering 233, Power Systems and Power Electronics 164, Circuits and Electronics 144, wastebasket 135, Thermodynamics 66, Fluid Mechanics 62, Quantum Mechanics 57, Heat Transfer 48, Mechanics 48, Electrical Machinery 46, Calculus 26, Probability and Stochastic Processes 9, Combinatorics 5, Statistics 4, Conventional Energy Technologies 3, Linear Algebra and Differential Equations 3, Economics 1 |
| XFinBench | Quantitative Finance 1911, Economics 273, wastebasket 17, Probability and Stochastic Processes 7, Statistics 5 |
| MMLU-Pro | Chemistry 488, Electromagnetism and Special Relativity 404, Thermodynamics 338, Mechanics 229, Heat Transfer 143, Fluid Mechanics 125, Quantum Mechanics 119, Electrical Machinery 83, Chemical Engineering 66, Signals, Systems and Control 64, Linear Algebra and Differential Equations 32, Probability and Stochastic Processes 23, Algebra 18, wastebasket 15, Material Science 13, Calculus 12, Circuits and Electronics 11, Power Systems and Power Electronics 6, Conventional Energy Technologies 4 |
| OpenStax Chemistry 2e | Chemistry 1123, Thermodynamics 118, Quantum Mechanics 91, wastebasket 57, Material Science 27, Mechanics 3, Conventional Energy Technologies 3, Electromagnetism and Special Relativity 2, Fluid Mechanics 1 |
| ChemBench | Chemistry 905, Material Science 106, wastebasket 42, Chemical Engineering 30, Thermodynamics 3, Conventional Energy Technologies 2, Quantum Mechanics 2, Heat Transfer 2, Mechanics 2 |
| FinanceMath | Quantitative Finance 684, Probability and Stochastic Processes 63, Economics 60, Statistics 56, wastebasket 6, Combinatorics 6 |
| QuantQA | Probability and Stochastic Processes 324, Combinatorics 65, Number Theory 23, Algebra 19, Quantitative Finance 17, Calculus 10, Geometry 10, Statistics 10, Mechanics 5, Linear Algebra and Differential Equations 2, wastebasket 1 |
| MMLU | Chemistry 282, Statistics 116, Quantum Mechanics 25, Thermodynamics 24, Probability and Stochastic Processes 10, wastebasket 3, Material Science 2, Quantitative Finance 2 |
| SUPERChem | Chemistry 401, Material Science 39, wastebasket 2, Thermodynamics 1, Quantum Mechanics 1 |
| SciBench | Thermodynamics 116, Chemistry 61, Quantum Mechanics 60, Electromagnetism and Special Relativity 9, Material Science 6, Mechanics 3, Probability and Stochastic Processes 1 |
| Academic Quant Interview Questions | Probability and Stochastic Processes 115, Combinatorics 56, Quantitative Finance 20, Number Theory 13, Algebra 8, Geometry 8, Statistics 8, Mechanics 4, Calculus 1 |
| Joint Entrance Examination Advanced | Chemistry 142, Thermodynamics 5, Quantum Mechanics 4, Material Science 4, wastebasket 1 |
| ControlBench | Signals, Systems and Control 130, Linear Algebra and Differential Equations 12, wastebasket 1 |
| TheoremQA | Signals, Systems and Control 48, wastebasket 18, Calculus 13, Electromagnetism and Special Relativity 7, Circuits and Electronics 6, Linear Algebra and Differential Equations 6, Probability and Stochastic Processes 4, Material Science 3, Quantum Mechanics 2, Algebra 1, Combinatorics 1 |
| Verrett et al., Foundations of Chemical and Biological Engineering I | Chemical Engineering 38, Chemistry 12, wastebasket 3, Thermodynamics 2, Fluid Mechanics 1, Heat Transfer 1, Linear Algebra and Differential Equations 1 |
| UGPhysics | Chemistry 51, Chemical Engineering 4, Circuits and Electronics 2 |
| Woolf, Chemical Process Dynamics and Controls | Chemical Engineering 24, Probability and Stochastic Processes 11, Statistics 7, Linear Algebra and Differential Equations 2, wastebasket 2, Signals, Systems and Control 1 |
| Ellingson, Electromagnetics | Electromagnetism and Special Relativity 36, Calculus 3, Linear Algebra and Differential Equations 1 |
| Bester, Quantitative Primer | Probability and Stochastic Processes 17, Calculus 3, Statistics 2, Combinatorics 2 |
| Schaschke's Solved Practical Problems in Fluid Mechanics | Chemical Engineering 12, Fluid Mechanics 4 |
| S.K Som's Introduction To Heat Transfer | Chemical Engineering 11, Heat Transfer 2 |
| V. Raghavan's Materials Science and Engineering: A First Course | Chemistry 8 |
| F.M White's Fluid Mechanics | Fluid Mechanics 2 |
| Gnadig's 200 More Puzzling Problems in Physics | Chemical Engineering 1 |

### Moved nodes: where their rows went (`bank_relabels.json`)

- Electromagnetism and Special Relativity > Transistor and Operational Amplifiers -> Common-Base, Common-Gate and Follower Stages: 1
- Electromagnetism and Special Relativity > Transistor and Operational Amplifiers -> Inverting and Non-Inverting Amplifiers: 1
- Electromagnetism and Special Relativity > Transistor and Operational Amplifiers -> Integrators and Differentiators: 1
- Electromagnetism and Special Relativity > Transistor and Operational Amplifiers -> Common-Emitter and Common-Source Amplifiers: 1
- Fluid Mechanics > Fluidized and Packed Beds -> Fluidisation and Packed-Bed Pressure Drop: 7
- Fluid Mechanics > Particle Settling and Separation -> Terminal Velocity and Sphere Drag: 6
- Fluid Mechanics > Particle Settling and Separation -> Cyclones and Centrifugal Separators: 4
- Fluid Mechanics > Particle Settling and Separation -> Fluidisation and Packed-Bed Pressure Drop: 1
- Heat Transfer > Evaporation and Stefan Flow -> Equimolar Counterdiffusion and Stefan Flow: 4
- Heat Transfer > Evaporation and Stefan Flow -> Cylinders and Spheres in Still Fluid: 1
- Heat Transfer > Evaporation and Stefan Flow -> Cylinders and Spheres in Crossflow: 1
- Heat Transfer > Simultaneous Heat and Mass Transfer -> Heat and Mass Transfer Analogies: 2
- Heat Transfer > Steady Mass Diffusion -> Fick's Law and Diffusion Coefficients: 6
- Heat Transfer > Steady Mass Diffusion -> Equimolar Counterdiffusion and Stefan Flow: 3
- Heat Transfer > Steady Mass Diffusion -> Process Variables and Flow Rates: 1
- Material Science > Electron Configuration and the Periodic Table -> Electron Configurations: 4
- Material Science > Electron Configuration and the Periodic Table -> Quantum Numbers and Atomic Orbitals: 2
- Material Science > Electron Configuration and the Periodic Table -> Atomic and Ionic Radii: 1
- Material Science > Electron Configuration and the Periodic Table -> Electron Affinity and Electronegativity: 1
- Quantum Mechanics > Molecular Rotation and Vibration Spectra -> Rotational Spectroscopy: 28
- Quantum Mechanics > Molecular Rotation and Vibration Spectra -> Vibrational Spectroscopy: 12
- Quantum Mechanics > Molecular Rotation and Vibration Spectra -> Raman Spectroscopy: 9
- Quantum Mechanics > Molecular Rotation and Vibration Spectra -> Electronic Spectroscopy and the Franck-Condon Principle: 1
- Quantum Mechanics > Molecular Rotation and Vibration Spectra -> Bond Enthalpies: 1

### Dataset label -> subject filed (labels with 5 or more questions)

- ChemBench: Analytical chemistry / analytical chemistry 22 -> Chemistry: 27
- ChemBench: Analytical chemistry / molecular structure -> Chemistry: 16
- ChemBench: Analytical chemistry / number 1h nmr shifts -> Chemistry: 50
- ChemBench: Analytical chemistry / xray crystallography -> Material Science: 11
- ChemBench: General chemistry / IX 2022 MD -> Chemistry: 5
- ChemBench: General chemistry / electron counts -> Chemistry: 25
- ChemBench: General chemistry / organic chemistry okuyama maskill -> Chemistry: 20
- ChemBench: General chemistry / oxidation states -> Chemistry: 10
- ChemBench: General chemistry / periodic table questions -> Chemistry: 9
- ChemBench: Inorganic chemistry / biological apatite 1 -> Material Science: 5
- ChemBench: Organic chemistry / OC 1 -> Chemistry: 24
- ChemBench: Organic chemistry / biomolecular science -> Chemistry: 26
- ChemBench: Organic chemistry / drug synthesis -> Chemistry: 24
- ChemBench: Organic chemistry / icho uk 2022 q3b -> Chemistry: 5
- ChemBench: Organic chemistry / number of structural isomers -> Chemistry: 23
- ChemBench: Organic chemistry / organic chemistry okuyama maskill -> Chemistry: 47
- ChemBench: Organic chemistry / organic reactivity 3 -> Chemistry: 10
- ChemBench: Organic chemistry / organic reactivity 7 -> Chemistry: 6
- ChemBench: Organic chemistry / organic reactivity 8 -> Chemistry: 8
- ChemBench: Organic chemistry / pointgroups -> Chemistry: 16
- ChemBench: Organic chemistry / reactive groups 29 -> Chemistry: 5
- ChemBench: Organic chemistry / reactive groups 53 -> Chemistry: 7
- ChemBench: Organic chemistry / reactive groups 54 -> Chemistry: 5
- ChemBench: Organic chemistry / reactive groups 55 -> Chemistry: 5
- ChemBench: Organic chemistry / reactive groups 56 -> Chemistry: 5
- ChemBench: Organic chemistry / reactive groups 57 -> Chemistry: 7
- ChemBench: Organic chemistry / reactive groups 64 -> Chemistry: 5
- ControlBench: section: Block Diagrams -> Signals, Systems and Control: 5
- ControlBench: section: Bode Analysis -> Signals, Systems and Control: 14
- ControlBench: section: Control System Design -> Signals, Systems and Control: 24
- ControlBench: section: Differential Equations, Laplace Transform and Preliminaries -> Signals, Systems and Control: 23
- ControlBench: section: Gain/Phase Margins -> Signals, Systems and Control: 9
- ControlBench: section: Root-Locus Design -> Signals, Systems and Control: 7
- ControlBench: section: Stability -> Signals, Systems and Control: 17
- ControlBench: section: Time Response of Dynamical Systems -> Signals, Systems and Control: 17
- Joint Entran: chemistry section -> Chemistry: 142
- Joint Entran: chemistry section -> Thermodynamics: 5
- MMLU-Pro: Electric Circuits -> Electromagnetism and Special Relativity: 26
- MMLU-Pro: Electric Circuits -> Linear Algebra and Differential Equations: 13
- MMLU-Pro: Electric Circuits -> Signals, Systems and Control: 12
- MMLU-Pro: Electric Circuits -> Circuits and Electronics: 9
- MMLU-Pro: Electric Circuits -> Algebra: 6
- MMLU-Pro: Electrical Machines -> Electrical Machinery: 82
- MMLU-Pro: Electrical Machines -> Electromagnetism and Special Relativity: 11
- MMLU-Pro: Electrical Machines -> Power Systems and Power Electronics: 5
- MMLU-Pro: Electromagnetics -> Electromagnetism and Special Relativity: 86
- MMLU-Pro: Electromagnetics -> Calculus: 9
- MMLU-Pro: Electronic Communications -> Signals, Systems and Control: 52
- MMLU-Pro: Electronic Communications -> Probability and Stochastic Processes: 23
- MMLU-Pro: Electronic Communications -> Linear Algebra and Differential Equations: 18
- MMLU-Pro: Electronic Communications -> Electromagnetism and Special Relativity: 16
- MMLU-Pro: Fluid Mechanics -> Fluid Mechanics: 61
- MMLU-Pro: General Chemistry -> Chemistry: 360
- MMLU-Pro: General Chemistry -> Thermodynamics: 82
- MMLU-Pro: General Chemistry -> Quantum Mechanics: 32
- MMLU-Pro: General Chemistry -> Algebra: 12
- MMLU-Pro: Heat Transfer -> Heat Transfer: 64
- MMLU-Pro: Machine Design -> Mechanics: 59
- MMLU-Pro: Mechanics -> Mechanics: 26
- MMLU-Pro: Mechanics -> Electromagnetism and Special Relativity: 6
- MMLU-Pro: Optics -> Electromagnetism and Special Relativity: 166
- MMLU-Pro: Optics -> Quantum Mechanics: 11
- MMLU-Pro: Optics -> Heat Transfer: 5
- MMLU-Pro: Organic Chemistry -> Chemistry: 17
- MMLU-Pro: Physical Chemistry -> Chemistry: 94
- MMLU-Pro: Physical Chemistry -> Thermodynamics: 75
- MMLU-Pro: Physical Chemistry -> Quantum Mechanics: 24
- MMLU-Pro: Physical Chemistry -> Material Science: 6
- MMLU-Pro: Physics -> Mechanics: 137
- MMLU-Pro: Physics -> Electromagnetism and Special Relativity: 93
- MMLU-Pro: Physics -> Thermodynamics: 66
- MMLU-Pro: Physics -> Quantum Mechanics: 52
- MMLU-Pro: Physics -> Fluid Mechanics: 9
- MMLU-Pro: Physics -> Chemistry: 8
- MMLU-Pro: Physics -> Heat Transfer: 5
- MMLU-Pro: Thermodynamics -> Thermodynamics: 111
- MMLU-Pro: Thermodynamics -> Chemical Engineering: 21
- MMLU-Pro: Thermodynamics -> Chemistry: 8
- MMLU-Pro: Thermodynamics -> Heat Transfer: 7
- MMLU-Pro: Thermodynamics -> Fluid Mechanics: 6
- MMLU-Pro: Transport Phenomena -> Heat Transfer: 61
- MMLU-Pro: Transport Phenomena -> Chemical Engineering: 44
- MMLU-Pro: Transport Phenomena -> Fluid Mechanics: 38
- MMLU: college chemistry -> Chemistry: 92
- MMLU: college chemistry -> Quantum Mechanics: 11
- MMLU: econometrics -> Statistics: 116
- MMLU: econometrics -> Probability and Stochastic Processes: 10
- MMLU: high school chemistry -> Chemistry: 190
- MMLU: high school chemistry -> Thermodynamics: 21
- MMLU: high school chemistry -> Quantum Mechanics: 14
- OpenStax Che: chapter 10: Liquids and Solids -> Chemistry: 46
- OpenStax Che: chapter 10: Liquids and Solids -> Material Science: 22
- OpenStax Che: chapter 10: Liquids and Solids -> Thermodynamics: 20
- OpenStax Che: chapter 11: Solutions and Colloids -> Chemistry: 64
- OpenStax Che: chapter 12: Kinetics -> Chemistry: 59
- OpenStax Che: chapter 12: Kinetics -> Quantum Mechanics: 7
- OpenStax Che: chapter 13: Fundamental Equilibrium Concepts -> Chemistry: 79
- OpenStax Che: chapter 14: Acid-Base Equilibria -> Chemistry: 91
- OpenStax Che: chapter 15: Equilibria of Other Reaction Classes -> Chemistry: 88
- OpenStax Che: chapter 16: Thermodynamics -> Chemistry: 52
- OpenStax Che: chapter 17: Electrochemistry -> Chemistry: 34
- OpenStax Che: chapter 17: Electrochemistry -> Material Science: 5
- OpenStax Che: chapter 18: Representative Metals, Metalloids, and Nonmetals -> Chemistry: 104
- OpenStax Che: chapter 19: Transition Metals and Coordination Chemistry -> Chemistry: 42
- OpenStax Che: chapter 1: Essential Ideas -> Chemistry: 57
- OpenStax Che: chapter 1: Essential Ideas -> Thermodynamics: 7
- OpenStax Che: chapter 20: Organic Chemistry -> Chemistry: 22
- OpenStax Che: chapter 21: Nuclear Chemistry -> Quantum Mechanics: 54
- OpenStax Che: chapter 2: Atoms, Molecules, and Ions -> Chemistry: 19
- OpenStax Che: chapter 3: Composition of Substances and Solutions -> Chemistry: 77
- OpenStax Che: chapter 4: Stoichiometry of Chemical Reactions -> Chemistry: 88
- OpenStax Che: chapter 5: Thermochemistry -> Chemistry: 38
- OpenStax Che: chapter 5: Thermochemistry -> Thermodynamics: 21
- OpenStax Che: chapter 6: Electronic Structure and Periodic Properties of Elements -> Chemistry: 46
- OpenStax Che: chapter 6: Electronic Structure and Periodic Properties of Elements -> Quantum Mechanics: 29
- OpenStax Che: chapter 7: Chemical Bonding and Molecular Geometry -> Chemistry: 68
- OpenStax Che: chapter 8: Advanced Theories of Covalent Bonding -> Chemistry: 32
- OpenStax Che: chapter 9: Gases -> Thermodynamics: 68
- OpenStax Che: chapter 9: Gases -> Chemistry: 16
- QuantQA: Brainteasers -> Combinatorics: 16
- QuantQA: Brainteasers -> Number Theory: 13
- QuantQA: Brainteasers -> Algebra: 11
- QuantQA: Brainteasers -> Probability and Stochastic Processes: 7
- QuantQA: Calculus -> Calculus: 7
- QuantQA: Combinatorics -> Probability and Stochastic Processes: 49
- QuantQA: Combinatorics -> Combinatorics: 32
- QuantQA: Conditional Expectation -> Probability and Stochastic Processes: 20
- QuantQA: Conditional Probability -> Probability and Stochastic Processes: 52
- QuantQA: Continuous Random Variables -> Probability and Stochastic Processes: 17
- QuantQA: Covariance -> Probability and Stochastic Processes: 8
- QuantQA: Discrete Random Variables -> Probability and Stochastic Processes: 11
- QuantQA: Events -> Probability and Stochastic Processes: 26
- QuantQA: Expected Value -> Probability and Stochastic Processes: 56
- QuantQA: Finance -> Quantitative Finance: 7
- QuantQA: Games -> Probability and Stochastic Processes: 7
- QuantQA: Geometry -> Geometry: 5
- QuantQA: Linear Regression -> Statistics: 9
- QuantQA: Probability -> Probability and Stochastic Processes: 57
- SuperGPQA: Chemical Engineering and Technology / Chemical Transport Engineering -> Fluid Mechanics: 27
- SuperGPQA: Chemical Engineering and Technology / Chemical Transport Engineering -> Heat Transfer: 11
- SuperGPQA: Chemical Engineering and Technology / Chemical Transport Engineering -> Chemistry: 6
- SuperGPQA: Chemical Engineering and Technology / Elements of Chemical Reaction Engineering -> Chemical Engineering: 67
- SuperGPQA: Chemical Engineering and Technology / Elements of Chemical Reaction Engineering -> Chemistry: 33
- SuperGPQA: Chemical Engineering and Technology / Fluid Flow and Heat Transfer in Chemical Engineering -> Chemical Engineering: 41
- SuperGPQA: Chemical Engineering and Technology / Fluid Flow and Heat Transfer in Chemical Engineering -> Heat Transfer: 31
- SuperGPQA: Chemical Engineering and Technology / Fluid Flow and Heat Transfer in Chemical Engineering -> Fluid Mechanics: 29
- SuperGPQA: Chemical Engineering and Technology / Mass Transport and Separation Process in Chemical Engineering -> Chemical Engineering: 117
- SuperGPQA: Chemical Engineering and Technology / Mass Transport and Separation Process in Chemical Engineering -> Chemistry: 21
- SuperGPQA: Chemistry / Analytical Chemistry -> Chemistry: 372
- SuperGPQA: Chemistry / Electrochemistry -> Chemistry: 207
- SuperGPQA: Chemistry / Inorganic Chemistry -> Chemistry: 123
- SuperGPQA: Chemistry / Inorganic Chemistry -> Material Science: 6
- SuperGPQA: Chemistry / Organic Chemistry -> Chemistry: 155
- SuperGPQA: Chemistry / Physical Chemistry -> Chemistry: 626
- SuperGPQA: Chemistry / Physical Chemistry -> Thermodynamics: 51
- SuperGPQA: Chemistry / Polymer Chemistry and Physics -> Material Science: 59
- SuperGPQA: Chemistry / Polymer Chemistry and Physics -> Chemistry: 16
- SuperGPQA: Chemistry / Radiochemistry -> Quantum Mechanics: 52
- SuperGPQA: Chemistry / Radiochemistry -> Chemistry: 5
- SuperGPQA: Control Science and Engineering / Control Theory and Control Engineering -> Signals, Systems and Control: 68
- SuperGPQA: Control Science and Engineering / Guidance, Navigation and Control -> Signals, Systems and Control: 45
- SuperGPQA: Control Science and Engineering / Guidance, Navigation and Control -> Mechanics: 5
- SuperGPQA: Control Science and Engineering / Operations Research and Cybernetics -> Calculus: 24
- SuperGPQA: Control Science and Engineering / Operations Research and Cybernetics -> Probability and Stochastic Processes: 5
- SuperGPQA: Electrical Engineering / Electrical Theory and New Technologies -> Electromagnetism and Special Relativity: 112
- SuperGPQA: Electrical Engineering / Electrical Theory and New Technologies -> Power Systems and Power Electronics: 30
- SuperGPQA: Electrical Engineering / High Voltage and Insulation Technology -> Power Systems and Power Electronics: 45
- SuperGPQA: Electrical Engineering / High Voltage and Insulation Technology -> Electromagnetism and Special Relativity: 26
- SuperGPQA: Electrical Engineering / High Voltage and Insulation Technology -> Material Science: 7
- SuperGPQA: Electrical Engineering / Power Electronics and Electrical Drives -> Electromagnetism and Special Relativity: 61
- SuperGPQA: Electrical Engineering / Power Electronics and Electrical Drives -> Power Systems and Power Electronics: 56
- SuperGPQA: Electrical Engineering / Power Electronics and Electrical Drives -> Electrical Machinery: 19
- SuperGPQA: Electrical Engineering / Power Systems and Automation -> Electromagnetism and Special Relativity: 33
- SuperGPQA: Electrical Engineering / Power Systems and Automation -> Power Systems and Power Electronics: 29
- SuperGPQA: Electrical Engineering / Power Systems and Automation -> Electrical Machinery: 22
- SuperGPQA: Electronic Science and Technology / Circuits and Systems -> Circuits and Electronics: 73
- SuperGPQA: Electronic Science and Technology / Circuits and Systems -> Electromagnetism and Special Relativity: 10
- SuperGPQA: Electronic Science and Technology / Circuits and Systems -> Signals, Systems and Control: 7
- SuperGPQA: Electronic Science and Technology / Electromagnetic Field and Microwave Technology -> Electromagnetism and Special Relativity: 83
- SuperGPQA: Electronic Science and Technology / Microelectronics and Solid-State Electronics -> Circuits and Electronics: 20
- SuperGPQA: Electronic Science and Technology / Microelectronics and Solid-State Electronics -> Material Science: 20
- SuperGPQA: Information and Communication Engineering / Antenna and Radio Communication -> Electromagnetism and Special Relativity: 85
- SuperGPQA: Information and Communication Engineering / Antenna and Radio Communication -> Signals, Systems and Control: 21
- SuperGPQA: Information and Communication Engineering / Communication Principles -> Signals, Systems and Control: 91
- SuperGPQA: Information and Communication Engineering / Communication Principles -> Mechanics: 9
- SuperGPQA: Information and Communication Engineering / Communication and Information Systems -> Signals, Systems and Control: 24
- SuperGPQA: Information and Communication Engineering / Communication and Information Systems -> Circuits and Electronics: 7
- SuperGPQA: Information and Communication Engineering / Optical Fiber Communication -> Electromagnetism and Special Relativity: 39
- SuperGPQA: Information and Communication Engineering / Optical Fiber Communication -> Material Science: 5
- SuperGPQA: Information and Communication Engineering / Signal and Information Processing -> Signals, Systems and Control: 123
- SuperGPQA: Instrument Science and Technology / Instrument Science and Technology -> Circuits and Electronics: 30
- SuperGPQA: Instrument Science and Technology / Instrument Science and Technology -> Electromagnetism and Special Relativity: 5
- SuperGPQA: Materials Science and Engineering / Materials Physics and Chemistry -> Material Science: 150
- SuperGPQA: Materials Science and Engineering / Materials Physics and Chemistry -> Mechanics: 18
- SuperGPQA: Materials Science and Engineering / Materials Physics and Chemistry -> Chemistry: 11
- SuperGPQA: Materials Science and Engineering / Materials Physics and Chemistry -> Thermodynamics: 7
- SuperGPQA: Materials Science and Engineering / Materials Physics and Chemistry -> Heat Transfer: 5
- TheoremQA: EECS / Information theory -> Signals, Systems and Control: 25
- TheoremQA: EECS / Signal processing -> Signals, Systems and Control: 23
- TheoremQA: Math / Numerical analysis -> Calculus: 13
- TheoremQA: Math / Numerical analysis -> Linear Algebra and Differential Equations: 6
- TheoremQA: Physics / Optics -> Electromagnetism and Special Relativity: 5

## Proposed tags (not added)


