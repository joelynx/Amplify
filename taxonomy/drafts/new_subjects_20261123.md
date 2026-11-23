# Draft: new subjects and quant-prep additions (2026-11-23, for the owner's approval)

Owner 2026-11-23: "I want to expand the chemistry section of this database ... I also want to expand the finance
section, especially what is required for quant jobs ... I also want electrical engineering and Chemical
engineering content." Nothing here is in taxonomy.json yet. Branches below follow taxonomy/STYLE.md; the
subtopics listed are indicative and will be fitted to the imported questions (cluster sizes), as in earlier
waves. Sources and counts: sources/research/20261123/.

## New subjects (22 -> 26)

| # | Subject | Scope | Solver profile |
|---|---------|-------|----------------|
| 23 | Chemistry | stoichiometry, chemical thermodynamics and equilibrium, acids and bases, electrochemistry, kinetics, solutions, quantum chemistry and spectroscopy, atomic structure and bonding, coordination, main-group and transition-metal chemistry, organic reactions, mechanisms, stereochemistry and synthesis, analytical methods | chemistry |
| 24 | Chemical Engineering | material and energy balances, chemical engineering thermodynamics (EOS, phase and reaction equilibria), reaction engineering, mass transfer and separations, process dynamics and control, particle operations, process design and economics | chemical_engineering |
| 25 | Circuits and Electronics | engineering network analysis (theorems with dependent sources, Laplace-domain analysis, two-ports, resonance and filters), analog electronics, digital electronics, measurements and instrumentation | electrical_engineering |
| 26 | Signals, Systems and Control | continuous and discrete signals and systems, transforms, sampling, control systems, communication systems, information theory | electrical_engineering |

Two EE subjects rather than one: the EE gap areas make six or more topics, and STYLE.md keeps a subject to
one to three. Machines, power systems and EM fields keep their subjects.

### 23 Chemistry

- Physical Chemistry
  - Stoichiometry and Chemical Calculations (mole concept, limiting reagent, concentration units, gas stoichiometry)
  - Chemical Thermodynamics and Thermochemistry (Hess's law, enthalpies of formation, Gibbs energy and spontaneity, Born-Haber)
  - Chemical Equilibrium (Kc and Kp, reaction quotient, Le Chatelier, van 't Hoff)
  - Ionic Equilibrium (pH, weak acids and bases, buffers, hydrolysis, titration curves, solubility product)
  - Electrochemistry (cells and potentials, Nernst equation, electrolysis and Faraday's laws, conductance)
  - Chemical Kinetics (rate laws, integrated rate laws, Arrhenius, mechanisms and steady state, catalysis)
  - Solutions and Colligative Properties (Raoult's law, vapour-pressure lowering, boiling and freezing points, osmotic pressure)
  - Quantum Chemistry and Spectroscopy (particle in a box and rotors as molecular models, Hückel, rotational, vibrational and electronic spectra)
  - Surface Chemistry and Colloids (adsorption isotherms, colloids)
- Inorganic Chemistry
  - Atomic Structure and Periodicity (electron configurations, periodic trends)
  - Chemical Bonding and Molecular Structure (Lewis structures, VSEPR, hybridisation, MO theory)
  - Coordination Chemistry (nomenclature, isomerism, crystal field theory, magnetic properties)
  - Main-Group Chemistry (s- and p-block elements and compounds)
  - Transition and Inner-Transition Elements
  - Metallurgy and Extraction of Metals
- Organic Chemistry
  - Nomenclature, Isomerism and Stereochemistry (IUPAC names, R and S, E and Z, conformations)
  - Reaction Mechanisms (substitution, elimination, addition, electrophilic aromatic substitution, rearrangements)
  - Functional Group Chemistry (hydrocarbons, haloalkanes, alcohols, carbonyls, acids and derivatives, amines)
  - Synthesis and Named Reactions
  - Organic Spectroscopy (IR, NMR, mass spectra)
  - Biomolecules and Polymers
- Analytical Chemistry (one topic, small; merge into Physical Chemistry if the imports stay thin)
  - Titrimetric and Gravimetric Analysis
  - Instrumental Methods (Beer-Lambert spectrophotometry, chromatography)

### 24 Chemical Engineering

- Chemical Process Principles
  - Material Balances (non-reacting, reacting, recycle, bypass and purge)
  - Energy Balances (reference states, heats of reaction, adiabatic temperatures)
  - Process Design and Economics (equipment sizing, cost estimation, profitability)
- Chemical Reaction Engineering
  - Rate Data and Kinetics (rate laws from data, integral and differential methods)
  - Ideal Reactors (batch, CSTR, PFR, reactors in series)
  - Multiple Reactions and Selectivity
  - Non-Isothermal Reactors
  - Residence Time Distribution and Non-Ideal Reactors
  - Catalytic and Heterogeneous Reactors
- Mass Transfer and Separation Processes
  - Diffusion and Mass Transfer Coefficients
  - Distillation (McCabe-Thiele, Fenske-Underwood-Gilliland, flash)
  - Absorption and Stripping
  - Extraction and Leaching
  - Drying, Crystallisation, Adsorption and Membranes
- Chemical Engineering Thermodynamics
  - Equations of State and Residual Properties
  - Phase Equilibria (VLE, Raoult and modified Raoult, activity coefficients, flash)
  - Chemical Reaction Equilibria
- Process Dynamics and Control
  - Dynamic Models and Transfer Functions
  - Feedback Control and PID Tuning
  - Stability and Frequency Response of Control Loops
- Particle and Fluid-Solid Operations
  - Particle Size and Size Reduction
  - Settling, Filtration and Fluidisation

### 25 Circuits and Electronics

- Network Analysis
  - Network Theorems with Dependent Sources (Thevenin, Norton, superposition, maximum power)
  - Laplace-Domain Circuit Analysis
  - Two-Port Networks
  - Resonance and Passive Filters
  - Network Topology and Graph Methods
- Analog Electronics
  - Diode Circuits (rectifiers, clippers, Zener regulation)
  - BJT and MOSFET Biasing
  - Small-Signal Amplifiers
  - Operational Amplifier Circuits
  - Feedback and Oscillators
  - Frequency Response of Amplifiers
- Digital Electronics
  - Number Systems and Codes
  - Boolean Algebra and Logic Minimisation
  - Combinational Circuits (multiplexers, decoders, adders)
  - Sequential Circuits (flip-flops, counters, state machines)
  - Logic Families, Memories and Converters (ADC, DAC)
- Electrical Measurements and Instrumentation (branch inside Network Analysis if small)

### 26 Signals, Systems and Control

- Signals and Systems
  - Signal Properties and Classification
  - LTI Systems and Convolution
  - Fourier Series and Fourier Transform of Signals
  - Laplace and z-Transform Analysis of Systems
  - Sampling and Reconstruction
  - Digital Filters (FIR, IIR, DFT and FFT)
- Control Systems
  - Block Diagrams and Signal-Flow Graphs
  - Time Response and Steady-State Error
  - Routh-Hurwitz Stability
  - Root Locus
  - Frequency-Domain Analysis (Bode, Nyquist, margins)
  - Compensators and PID Design
  - State-Space Analysis
- Communication Systems
  - Amplitude and Angle Modulation
  - Pulse and Digital Modulation
  - Noise in Communication Systems
  - Information Theory and Coding

## Changes to existing subjects (quant prep and EE)

- Quantitative Finance: new topic Trading and Market Making
  - Market Making and Bid-Ask Quoting (pricing a market on a game, adverse selection, inventory)
  - Betting, Edge and the Kelly Criterion
  - Factor Models and Performance Measurement (under Portfolio Theory and Risk Management instead, if preferred)
- Statistics: branch Time Series Analysis if not present (ARMA, GARCH, unit roots, cointegration), and Statistical
  Learning (bias-variance, regularisation, cross-validation, PCA, trees) as theory questions only (programming stays out).
- Electromagnetism and Special Relativity: branch Transmission Lines, Waveguides and Antennas (Ellingson).
- Power Systems and Power Electronics: SuperGPQA and MMLU-Pro power and high-voltage rows (about 330) fit the existing tree.

## Boundary rules to add to SUBJECTS.md

- Chemistry vs Thermodynamics: gas laws and kinetic theory stay in Thermodynamics; a question about a chemical
  reaction's energetics or equilibrium is Chemistry.
- Chemistry vs Quantum Mechanics: atomic physics stays in Quantum Mechanics; molecular structure, bonding and
  molecular spectroscopy are Chemistry. Radioactive decay stays in Quantum Mechanics.
- Chemistry vs Material Science: crystal structure, defects and phase diagrams of materials stay in Material
  Science; the solid state as general chemistry (packing, unit-cell density) is decided by the source's course.
- Chemical Engineering vs Heat Transfer, Fluid Mechanics and Thermodynamics: heat exchangers and process
  heat-transfer equipment stay in Heat Transfer (Kern); pipe flow stays in Fluid Mechanics; mass transfer and
  separations move to Chemical Engineering (the 18 Heat and Mass Transfer rows to be reviewed); phase and reaction
  equilibria of mixtures are Chemical Engineering, pure-substance thermodynamics stays in Thermodynamics.
- Chemical Engineering vs Signals, Systems and Control: process-control questions about plants and loops are
  Chemical Engineering; control theory posed on abstract transfer functions or servo systems is Signals, Systems
  and Control.
- Circuits and Electronics vs Electromagnetism and Special Relativity: physics-course circuits (DC networks,
  RC/RL/RLC transients, AC phasors) stay in Electromagnetism; network theorems with dependent sources,
  Laplace-domain analysis, two-ports, filters and all electronics are Circuits and Electronics.
- Trading and Market Making vs Probability: a question about quoting, sizing or edge in a market is Quantitative
  Finance; a pure expected-value or probability puzzle stays in Probability.
