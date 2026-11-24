# Draft: twelve new subjects and three additions (2026-11-25, applied as drafted, for the owner's morning review)

Owner, night of 2026-11-24 (relayed by the coordinator; the owner was asleep, so this draft is applied as it stands and
reviewed in the morning): expand the bank into mechanical, power plant, nuclear and electronics engineering, digital
logic, computer architecture, operating systems, data science, machine learning, game theory, communication engineering,
semiconductors and algorithms (proofs and pseudocode). Later the same night: databases, programming languages and data
structures, plus computer networks and theory of computation; Algorithms widened to Algorithms and Data Structures.
Nodes: `new_subjects_20261125_nodes.json` (532 nodes in the taxonomy.json format, est 0, orig = [topic, branch,
subtopic]). No other file was edited.

## How the draft was made (read first)

- Mapping (decided by the coordinator): power plant engineering became additions to Conventional Energy Technologies,
  electronics engineering additions to Circuits and Electronics, communication engineering additions to Signals, Systems
  and Control; the rest are new subjects 27-38.
- No second homes. Where an existing node already holds a concept that the decided scope gives to a new subject, the new
  tree does not repeat it. The outline shows such nodes as "[existing, not in the JSON]" where they would go, the
  boundary rules keep sending questions to the existing node, and the proposals below list the move (row counts read
  from amplify.db, read-only, 2026-11-25). Tonight's classification therefore has one home per concept, and each move is
  a relabel once approved. Where the existing node is one coarse node for a whole area (Quantitative Finance's three
  game-theory nodes; Material Science's "p-n Junctions and Transistors" and "Integrated Circuit Fabrication"), the new
  subject gets fine nodes and the coarse node is proposed for relabel-and-retire, as with the 2026-11-23 amplifier move.
- The Rajput and Nag source rule stands: their IC-engine, reactor-physics and nuclear-plant chapters stay in CET. The new
  Mechanical and Nuclear Engineering nodes are named so they never repeat a CET node name (as Thermodynamics' Rankine
  node does), and the boundary rules say which questions from other sources go where.
- Group codes: new codes for new subjects, two subjects per code as on 2026-11-23 (G10 Chemistry + Chemical Engineering,
  G11 Circuits + Signals): G12 Mechanical + Nuclear Engineering, G13 Semiconductor Devices + Digital Logic and Computer
  Architecture, G14 Operating Systems + Computer Networks, G15 Algorithms and Data Structures + Theory of Computation,
  G16 Databases + Programming Languages and Compilers, G17 Machine Learning and Data Science + Game Theory. Additions keep
  their subject's code (G9a, G11).
- Granularity: one subtopic per idea a student would name, 25-62 per subject, except Mechanical Engineering (94): it is
  seven courses (strength of materials, theory of machines, vibrations, machine design, manufacturing and metrology,
  IC engines with refrigeration and air conditioning, industrial engineering); the existing engineering subjects hold
  85-166 nodes. Notes list what belongs there and, where a neighbour could take a question, "see <node>".
- Validation (python, .venv): the JSON loads as a list of 532 dicts with exactly the taxonomy.json keys in the same
  order; (subject, topic, branch, subtopic) is unique across taxonomy.json plus the draft; every new subtopic name is
  unique, ignoring case, across both; no "/" in any name, names at most 60 characters, at most one parenthetical (the
  "(1)" of LL(1) and "(0)" of LR(0) are part of the standard names); every new topic name belongs to one subject only and
  is no other subject's name; no new branch name repeats a branch of another subject; the branches that additions extend
  exist and the two new branches do not. Found, not touched: taxonomy.json already holds "Per-Unit System" twice
  (Electrical Machinery and Power Systems and Power Electronics).

## New subjects (26 -> 38): rows for SUBJECTS.md

| # | Subject | Scope |
|---|---------|-------|
| 27 | Mechanical Engineering | strength of materials at the design level (composite bars, impact loads, torsion of circular shafts, columns, SFD and BMD, bending and shear stresses in beams, fixed and continuous beams, trusses), theory of machines (mechanisms, cams, gears and gear trains, belts, clutches and brakes, flywheels, governors, balancing, vehicle gyroscopes), mechanical vibrations, machine design and machine elements, manufacturing (casting, forming, welding, machining, non-traditional machining, CNC and additive manufacturing) and metrology, IC engines beyond CET's engine nodes (fuel-air cycles, carburettors, emissions), refrigeration and air conditioning, industrial engineering (inventory, planning and sequencing, line balancing, PERT and CPM, quality control, work study and layout) |
| 28 | Nuclear Engineering | neutron interactions, slowing down, diffusion and transport, criticality, reactor kinetics, reactivity feedback, poisoning and control, reactor thermal hydraulics, fuel cycle and nuclear materials, reactor systems and safety, radiation detection, shielding and dosimetry. NOT nuclear or particle physics (that is Quantum Mechanics) |
| 29 | Semiconductor Devices | carrier transport and recombination, p-n junctions and metal-semiconductor contacts, heterojunctions, BJT and MOS device physics, short-channel effects, optoelectronic devices (photodetectors, solar cells, LEDs, lasers), IC processing and VLSI technology |
| 30 | Digital Logic and Computer Architecture | digital logic design (number systems and codes, Boolean algebra and minimisation, combinational and sequential design, state machines, asynchronous circuits, RTL and HDLs), instruction sets, computer arithmetic, datapath and control, pipelining and hazards, caches and memory hierarchy, address-translation hardware, I/O organisation, performance and parallel architectures |
| 31 | Operating Systems | processes and threads, CPU scheduling, synchronization, deadlocks, memory management, paging and virtual memory, file systems, disk scheduling and I/O, protection and security |
| 32 | Machine Learning and Data Science | supervised learning (regression and classification as learning, SVMs and kernels, losses, metrics), unsupervised learning, probabilistic models (Bayesian networks, HMMs, EM), learning theory, reinforcement learning, neural networks and deep learning, data preparation and exploratory analysis. Classical inference stays in Statistics |
| 33 | Game Theory | strategic-form games, dominance, pure and mixed Nash equilibria, zero-sum games, correlated equilibrium, extensive-form games and subgame perfection, bargaining, repeated games, Bayesian and signaling games, evolutionary games, auctions, mechanism design and stable matching, cooperative games and the Shapley value |
| 34 | Algorithms and Data Structures | data structures (arrays, linked lists, stacks, queues, binary and search trees, AVL and red-black trees, heaps, hashing, union-find, tries, range-query trees, graph representations), asymptotic analysis, recurrences and correctness proofs, sorting and searching, divide and conquer, greedy algorithms, dynamic programming, graph algorithms, string matching, randomized algorithms, NP-completeness proofs, approximation, backtracking. Questions answered by reasoning, proof, tracing or pseudocode; writing code to be run is out of scope |
| 35 | Databases | ER modelling, relational model and keys, relational algebra and calculus, SQL, functional dependencies and normalization, transactions, concurrency control and recovery, file organisation and indexing (B-trees, B+ trees, extendible and linear hashing), query processing and optimisation, NoSQL and distributed databases |
| 36 | Programming Languages and Compilers | binding, scope and storage, parameter passing, pointers, garbage collection, types and type systems, evaluation and exceptions, functional, logic and object-oriented programming, formal semantics; compiler phases: lexical analysis, parsing (LL and LR), syntax-directed translation, intermediate code, optimisation, code generation, runtime environments, linking |
| 37 | Computer Networks | layered models, delay and throughput, switching, framing, error detection on frames, sliding-window and MAC protocols, Ethernet and LAN switching, IP addressing and subnetting, forwarding and routing, QoS shaping, UDP and TCP, flow and congestion control, application protocols, network security |
| 38 | Theory of Computation | finite automata, regular expressions and grammars, regular-language properties, context-free grammars and pushdown automata, Turing machines and the Chomsky hierarchy, decidability, reducibility and Rice's theorem, complexity classes (P, NP, co-NP, PSPACE) |

Also in SUBJECTS.md: the header count ("26 subjects (23-26 added 2026-11-23)") becomes 38 (27-38 added 2026-11-25), and
the last rule's example `Other: Algorithms` now names a real subject (suggest `Other: Astronomy`). If P2 is approved,
the Statistics row loses "statistical learning as theory (...)".

## Boundary rules to append to SUBJECTS.md

- Mechanical Engineering vs Mechanics: physics-course and Srinath-level solid mechanics stays in Mechanics (stress and strain transformation, Mohr's circle, failure theories, energy methods, beam deflection, Euler buckling, pressure vessels), as do oscillators, rigid-body dynamics, tops and statics of rigid bodies; design-level strength of materials (SFD and BMD, bending and shear stresses in beams, torsion of circular shafts, columns, composite bars, trusses), mechanisms and machines (linkages, cams, gears, drives, governors, balancing, vehicle gyroscopes) and engineering vibration analysis (isolation, unbalance, whirling, torsional systems) are Mechanical Engineering.
- Mechanical Engineering vs Material Science: material behaviour (tensile tests, hardness, S-N curves, creep, heat treatment, phase diagrams) stays in Material Science; designing parts against fatigue (endurance-limit factors, Goodman and Soderberg lines) and all manufacturing processes are Mechanical Engineering.
- Mechanical Engineering vs Thermodynamics: a refrigerator or heat pump treated as a cycle (COP, Carnot limit) and moist-air properties stay in Thermodynamics; refrigeration and air-conditioning systems (p-h chart plants, multistage, absorption and air-cycle systems, refrigerants, psychrometric processes, cooling loads, ducts) are Mechanical Engineering.
- Mechanical Engineering vs Fluid Mechanics and Heat Transfer: viscous and lubrication flow, pumps and turbines stay in Fluid Mechanics, conduction and heat exchangers in Heat Transfer; journal-bearing design (Sommerfeld number, Raimondi-Boyd charts) and air-conditioning duct design are Mechanical Engineering.
- Mechanical Engineering vs Conventional Energy Technologies: Rajput and Nag questions stay in CET; IC-engine basics, combustion and knock, injection, supercharging, cooling, lubrication and engine testing go to CET's Diesel Engine Power Plants nodes whatever the source; fuel-air and actual cycles, carburettors and petrol injection, and engine emissions are Mechanical Engineering.
- Mechanical Engineering vs Calculus, Probability and Statistics: linear programming (transportation and assignment included) stays in Calculus, queueing in Probability, forecasting and exponential smoothing in Statistics; inventory models, sequencing, line balancing, PERT and CPM, control charts and acceptance sampling plans are Mechanical Engineering.
- Nuclear Engineering vs Quantum Mechanics: nuclear structure, decay, reactions and Q-values and the physics of radiation-matter interaction (stopping power, attenuation coefficients) stay in Quantum Mechanics; reactor physics, kinetics and thermal hydraulics, the fuel cycle, dose quantities and shield design, and radiation-measurement systems (gas-filled, scintillation and semiconductor detectors, counting statistics) are Nuclear Engineering.
- Nuclear Engineering vs Conventional Energy Technologies: Rajput and Nag questions stay in CET, and so does a nuclear plant treated as a power station (layout, siting, economics, comparison with other plants) whatever the source; every other nuclear-engineering question is Nuclear Engineering.
- Semiconductor Devices vs Material Science: band theory, intrinsic and extrinsic carrier concentrations, conductivity and mobility of materials, the Hall effect and crystal structure stay in Material Science (STYLE fixed decision); carrier transport and recombination, junctions and contacts, transistor physics, optoelectronic devices and IC processing are Semiconductor Devices.
- Semiconductor Devices vs Circuits and Electronics: deriving or explaining a device's characteristics from its physics is Semiconductor Devices; using a device model in a circuit (load lines, biasing, small-signal models, switching circuits) is Circuits and Electronics.
- Digital Logic and Computer Architecture vs Circuits and Electronics: transistor-level logic (TTL and CMOS gate circuits, dynamic logic, memory cells, data converters) stays in Circuits and Electronics; gate-level and register-level design and computer organisation are Digital Logic and Computer Architecture. Until P1 is approved, number systems, Boolean algebra, combinational and sequential circuits keep going to Circuits' Digital Electronics nodes.
- Operating Systems vs Digital Logic and Computer Architecture: page tables, page faults and replacement, TLB effective access time, disk access time and disk scheduling are Operating Systems; cache organisation, cache indexing with TLBs, interrupt and DMA hardware and buses are Digital Logic and Computer Architecture.
- Machine Learning and Data Science vs Statistics: classical inference (estimation, tests, intervals, regression inference, time series, econometrics, descriptive statistics) stays in Statistics; methods posed as learning from data (training, losses, generalisation, prediction metrics) are Machine Learning and Data Science. Until P2 is approved, the Statistical Learning concepts (bias-variance, cross-validation, ridge and lasso, kNN, LDA and naive Bayes, trees and ensembles, PCA, k-means and hierarchical clustering) keep going to Statistics.
- Machine Learning and Data Science vs Probability and Calculus: probabilities of events, Markov chains and MCMC stay in Probability; gradient descent as optimisation stays in Calculus; Bayesian networks, HMMs, EM, MDPs and neural-network optimisers are Machine Learning and Data Science.
- Game Theory vs Economics: monopoly and oligopoly models (Cournot, Bertrand), consumer and producer theory and contracts under asymmetric information stay in Economics; solving a stated game for its equilibria is Game Theory.
- Game Theory vs Quantitative Finance and Combinatorics: a question about quoting, sizing or edge in a market stays in Quantitative Finance; other game-theory questions from quant collections are Game Theory (QF's three Game Theory nodes take no new questions, P3); combinatorial games (Nim, take-away, board games), common-knowledge and pirate puzzles and voting puzzles stay in Combinatorics.
- Game Theory vs Algorithms and Data Structures: stable matching (Gale-Shapley) is Game Theory, also when asked as an algorithm proof; matching algorithms on graphs (augmenting paths, Hopcroft-Karp, Hungarian) are Algorithms and Data Structures.
- Algorithms and Data Structures vs Combinatorics: counting, existence and structure (number of BSTs or labelled trees, Hall's theorem, graph properties) stay in Combinatorics, as do puzzle-style algorithmic questions (fewest weighings or comparisons, river crossing, Hanoi); algorithm design and analysis (pseudocode, running time, correctness proofs, traces of named algorithms) and data-structure operations are Algorithms and Data Structures.
- Algorithms and Data Structures vs Algebra: divide-and-conquer recurrences (master theorem, recursion trees) are Algorithms and Data Structures; linear recurrences with constant coefficients stay in Algebra.
- Algorithms and Data Structures vs Databases: every B-tree and B+-tree question and disk-based hashing (extendible, linear) are Databases; in-memory search trees (BST, AVL, red-black) and hash tables are Algorithms and Data Structures.
- Algorithms and Data Structures vs Theory of Computation: complexity classes and what a reduction implies for them (P, NP, co-NP, NP-hard and NP-complete as definitions, Cook-Levin, PSPACE) are Theory of Computation; building a reduction to prove a named problem NP-complete, and approximation or search algorithms for hard problems, are Algorithms and Data Structures.
- Programming Languages and Compilers vs Theory of Computation: grammars, ambiguity, automata and conversions between regular expressions and automata are Theory of Computation; parser construction (FIRST and FOLLOW, LL and LR tables and conflicts, left-recursion removal) and lexer generators are Programming Languages and Compilers.
- Programming Languages and Compilers vs Algorithms and Data Structures: tracing a program to show a language rule (scope, parameter passing, pointers, evaluation order, recursion output) and formal Hoare-logic proofs are Programming Languages and Compilers; an algorithm's correctness or running time is Algorithms and Data Structures.
- Computer Networks vs Signals, Systems and Control: modulation, detection, channel capacity, coding theory, physical-layer multiple access (FDMA, TDMA, CDMA, OFDM) and wireless channels are Signals, Systems and Control; framing, CRC and checksums on frames, MAC protocols (ALOHA, CSMA), switching, addressing, routing, transport and application protocols are Computer Networks.
- Computer Networks vs Probability and Number Theory: queueing theory stays in Probability, RSA and modular arithmetic in Number Theory; network delay formulas and security protocols are Computer Networks.
- Databases vs Operating Systems: disk access time and RAID are Operating Systems; file organisation, blocking factors and index sizes are Databases.

## Trees of the new subjects

### 27 Mechanical Engineering (94 subtopics, G12)

- Strength of Materials
  - Axial and Torsional Loading
    - Composite Bars and Temperature Stresses
    - Impact and Suddenly Applied Loads
    - Torsion of Circular Shafts
    - Columns and Struts
  - Beams and Trusses
    - Shear Force and Bending Moment Diagrams
    - Bending Stresses in Beams
    - Shear Stress Distribution in Beams
    - Fixed and Continuous Beams
    - Plane Trusses
- Theory of Machines
  - Kinematics of Mechanisms
    - Kinematic Chains and Mobility
    - Velocity Analysis of Mechanisms
    - Acceleration Analysis and Coriolis Component
    - Hooke's Joint and Steering Mechanisms
    - Cams and Followers
  - Gears and Gear Trains
    - Gear Tooth Geometry and Law of Gearing
    - Interference and Contact Ratio
    - Simple and Compound Gear Trains
    - Epicyclic Gear Trains
  - Belts, Clutches and Brakes
    - Belt, Rope and Chain Drives
    - Friction Clutches
    - Brakes and Dynamometers
  - Dynamics of Machines
    - Inertia Forces in Reciprocating Engines
    - Flywheels and Turning-Moment Diagrams
    - Governors
    - Balancing of Rotating Masses
    - Balancing of Reciprocating Masses
    - Gyroscopic Effects in Vehicles and Ships
  - Mechanical Vibrations
    - Vibration Isolation and Absorbers
    - Unbalance and Base Excitation
    - Whirling of Shafts
    - Torsional Vibration of Rotor Systems
    - Transverse Vibration of Shafts and Beams
- Machine Design
  - Design Against Fluctuating Loads
    - Endurance Limit Modifying Factors
    - Fatigue Design Criteria
  - Joints and Fasteners
    - Riveted Joints
    - Welded Joints
    - Threaded Fasteners and Bolted Joints
    - Cotter and Knuckle Joints
    - Power Screws
  - Transmission Elements
    - Shaft Design for Combined Loads
    - Keys and Shaft Couplings
    - Gear Design
  - Bearings and Springs
    - Rolling-Contact Bearings
    - Hydrodynamic Journal Bearings
    - Mechanical Springs
- Manufacturing Engineering
  - Casting and Powder Metallurgy
    - Casting Processes and Defects
    - Gating System Design
    - Solidification and Riser Design
    - Powder Metallurgy
  - Metal Forming
    - Rolling of Metals
    - Forging
    - Extrusion and Wire Drawing
    - Sheet Metal Operations
  - Joining Processes
    - Fusion Welding Processes
    - Welding Heat Input and Weld Quality
    - Resistance Welding
    - Solid-State Welding, Brazing and Soldering
  - Metal Cutting
    - Tool Geometry and Chip Formation
    - Merchant's Circle and Cutting Forces
    - Tool Wear and Tool Life
    - Machining Time and Material Removal Rate
    - Machining Economics
    - Grinding and Abrasive Finishing
  - Non-Traditional Machining
    - Electric Discharge and Beam Machining
    - Electrochemical and Chemical Machining
    - Ultrasonic and Jet Machining
  - Metrology
    - Limits, Fits and Limit Gauges
    - Linear and Angular Measurement
    - Surface Texture Measurement
    - Screw Thread and Gear Measurement
  - Computer-Aided Manufacturing and Tooling
    - NC and CNC Part Programming
    - Additive Manufacturing
    - Jigs and Fixtures
- Thermal Engineering
  - Internal Combustion Engines
    - Fuel-Air and Actual Cycles
    - Carburettors and Petrol Injection
    - Engine Emissions and Their Control
  - Refrigeration
    - Vapour Compression Systems and Components
    - Multistage and Cascade Refrigeration
    - Vapour Absorption Refrigeration
    - Air-Cycle and Aircraft Refrigeration
    - Refrigerants
  - Air Conditioning
    - Psychrometric Processes in Air Conditioning
    - Cooling Load Estimation
    - Air Distribution and Duct Design
- Industrial Engineering
  - Production Planning and Control
    - Inventory Control Models
    - Aggregate Planning and MRP
    - Job Sequencing Rules
    - Assembly Line Balancing
  - Project Management
    - CPM and Project Crashing
    - PERT and Completion Probability
  - Quality Control
    - Control Charts and Process Capability
    - Acceptance Sampling Plans
  - Work Study and Facility Planning
    - Time Study and Work Measurement
    - Plant Layout and Facility Location

### 28 Nuclear Engineering (46 subtopics, G12)

- Nuclear Reactor Theory
  - Neutron Interactions
    - Microscopic and Macroscopic Cross Sections
    - Resonance Absorption and Doppler Broadening
    - Fission Neutron Yields and Energy Release
    - Neutron Activation
  - Neutron Slowing Down
    - Lethargy and Collision Kinematics
    - Slowing-Down Density and Fermi Age
    - Thermal Neutron Spectra
  - Neutron Diffusion and Transport
    - Neutron Diffusion Equation
    - Diffusion Length and Source Problems
    - Neutron Transport Theory
  - Reactor Criticality
    - Four- and Six-Factor Formulas
    - Bare Reactor Criticality and Buckling
    - Reflected Reactors and Reflector Savings
    - Multigroup Diffusion Theory
  - Reactor Kinetics
    - Delayed Neutrons and Reactivity Units
    - Point Kinetics Equations
    - Reactor Period and the Inhour Equation
    - Subcritical Multiplication
  - Reactivity Control and Feedback
    - Temperature and Void Coefficients
    - Xenon and Samarium Poisoning
    - Control Rods and Soluble Poisons
    - Fuel Depletion and Core Lifetime
- Nuclear Reactor Engineering
  - Reactor Thermal Hydraulics
    - Core Power Distribution and Peaking Factors
    - Fuel Pin Temperature Distribution
    - Coolant Channel Temperature Profiles
    - Critical Heat Flux and Thermal Margins
  - Nuclear Fuel Cycle
    - Uranium Enrichment and Separative Work
    - Breeding, Conversion and the Thorium Cycle
    - Spent Fuel and Reprocessing
    - Radioactive Waste Management
  - Nuclear Materials
    - Nuclear Fuel Materials
    - Cladding and Structural Materials
    - Radiation Damage in Materials
  - Reactor Systems and Safety
    - Light-Water Reactor Design
    - Advanced and Generation-IV Reactors
    - Decay Heat and Emergency Cooling
    - Reactor Accidents and Safety Analysis
    - Probabilistic Safety Assessment
- Radiation Detection and Protection
  - Radiation Detection
    - Gas-Filled Detectors
    - Scintillation and Semiconductor Detectors
    - Counting Statistics and Dead Time
    - Neutron Detectors
  - Radiation Shielding and Dosimetry
    - Dose Quantities and Units
    - Gamma-Ray Shielding and Buildup Factors
    - Neutron Shielding
    - Biological Effects and Dose Limits

### 29 Semiconductor Devices (32 subtopics, G13)

- Semiconductor Device Physics
  - Carriers and Transport
    - Effective Mass and Density of States
    - Scattering, Mobility and Velocity Saturation
    - Carrier Diffusion and the Einstein Relation
    - Generation and Recombination
    - Continuity Equation and Minority-Carrier Diffusion
  - Junctions and Contacts
    - p-n Junction Electrostatics
    - Junction Capacitance
    - Ideal Diode Current
    - Non-Ideal Diode Behavior and Switching
    - Junction Breakdown
    - Schottky Barriers and Ohmic Contacts
    - Heterojunctions
  - Bipolar Junction Transistors
    - BJT Current Components and Gain
    - Ebers-Moll Model
    - Non-Ideal BJT Effects
    - BJT Switching and Frequency Limits
  - MOS Devices
    - MOS Capacitor
    - Threshold Voltage
    - MOSFET Current-Voltage Derivation
    - Short-Channel Effects and Scaling
    - Advanced MOS Structures
    - JFET and MESFET Device Physics
  - Optoelectronic Devices
    - Photodiodes and Photodetectors
    - Solar Cell Device Physics
    - Light-Emitting Diodes
    - Semiconductor Lasers
- VLSI Fabrication Technology
  - Integrated Circuit Processing
    - Thermal Oxidation of Silicon
    - Photolithography
    - Ion Implantation
    - Deposition and Etching
    - CMOS Process Integration
    - IC Yield and Wafer Cost
    - [existing, not in the JSON] Material Science > Semiconductors: Crystal Growth and Purification of Silicon (11 rows); Material Science > Diffusion: Diffusion Doping of Semiconductors (5 rows) [move as named, P4]

### 30 Digital Logic and Computer Architecture (33 subtopics, G13)

- Digital Logic Design
  - [existing, not in the JSON] Circuits and Electronics > Digital Electronics: branches Number Systems and Codes (4), Boolean Algebra and Logic Minimisation (5), Combinational Circuits (6), Sequential Circuits (6) and the node Semiconductor Memories [move as named, P1]
  - Digital System Design
    - Asynchronous Sequential Circuits
    - Register-Transfer Level Design
    - Hardware Description Languages
- Computer Architecture
  - Instruction Set Architecture
    - Instruction Formats and Opcode Encoding
    - Addressing Modes
    - Assembly Language and Procedure Calls
    - RISC and CISC Design
  - Computer Arithmetic
    - Integer Multiplication Algorithms
    - Integer Division Algorithms
    - Floating-Point Arithmetic
    - ALU Design and Status Flags
  - Datapath and Control
    - Single-Cycle Datapath
    - Multicycle Datapath
    - Hardwired Control Units
    - Microprogrammed Control
  - Pipelining
    - Pipeline Speedup and Throughput
    - Data Hazards and Forwarding
    - Control Hazards and Branch Prediction
    - Reservation Tables and Collision Vectors
    - Superscalar and Out-of-Order Execution
  - Memory Hierarchy
    - Cache Mapping and Address Fields
    - Cache Replacement and Write Policies
    - Cache Performance and Miss Types
    - Main Memory Organisation and Interleaving
    - Virtually and Physically Indexed Caches
  - Input-Output Organisation
    - Programmed and Memory-Mapped Input-Output
    - Interrupts and Exceptions
    - Direct Memory Access
    - Buses and Bus Arbitration
  - Performance and Parallel Architectures
    - CPU Performance Equation
    - Amdahl's Law
    - Cache Coherence Protocols
    - SIMD, Vector and GPU Architectures

### 31 Operating Systems (36 subtopics, G14)

- Operating Systems
  - Processes and Threads
    - System Calls and Dual-Mode Operation
    - Process States and Context Switching
    - Process Creation and Fork
    - Threads and Multithreading Models
    - Inter-Process Communication
  - CPU Scheduling
    - FCFS, SJF and SRTF Scheduling
    - Priority and Round-Robin Scheduling
    - Multilevel Queue and Feedback Scheduling
    - Real-Time Scheduling
  - Process Synchronization
    - Race Conditions and Interleavings
    - Critical-Section Solutions
    - Semaphores
    - Monitors and Condition Variables
    - Classical Synchronization Problems
  - Deadlocks
    - Deadlock Conditions and Resource-Allocation Graphs
    - Deadlock Prevention
    - Banker's Algorithm
    - Deadlock Detection and Recovery
  - Memory Management
    - Contiguous Allocation and Fragmentation
    - Paging and Page Tables
    - TLBs and Effective Access Time
    - Segmentation
  - Virtual Memory
    - Demand Paging and Page-Fault Service
    - Page Replacement Algorithms
    - Frame Allocation and Thrashing
  - File Systems
    - Directory Structures and File Operations
    - File Allocation Methods
    - Free-Space Management
    - Journaling and File-System Consistency
  - Disk and Device Management
    - Disk Structure and Access Time
    - Disk Scheduling Algorithms
    - RAID Levels
    - Buffering, Caching and Spooling
  - Protection and Security
    - Access Matrix and Capabilities
    - Authentication and System Threats
    - Multilevel Security Models

### 32 Machine Learning and Data Science (37 subtopics, G17)

- Machine Learning
  - Supervised Learning
    - Linear Regression for Prediction
    - Logistic and Softmax Regression
    - Perceptron and Linear Separability
    - Support Vector Machines
    - Kernel Methods
    - Loss Functions and Empirical Risk
    - Classification Metrics and ROC Curves
  - [existing, not in the JSON] Statistics > Statistical Learning: Bias-Variance Tradeoff, Cross-Validation and Model Selection, Ridge and Lasso Regression, Classification with kNN and Discriminant Analysis, Decision Trees, Bagging, Random Forests and Boosting, Principal Component Analysis, k-Means and Hierarchical Clustering (13 rows) [move as named, P2]
  - Unsupervised Learning
    - Density-Based and Spectral Clustering
    - Nonlinear Dimensionality Reduction
    - Anomaly Detection
    - Recommender Systems
  - Probabilistic Models
    - Bayesian Networks
    - Hidden Markov Models
    - Gaussian Mixture Models and the EM Algorithm
  - Learning Theory
    - PAC Learning
    - VC Dimension
    - Online Learning and Regret Bounds
  - Reinforcement Learning
    - Markov Decision Processes
    - Value and Policy Iteration
    - Temporal-Difference Learning and Q-Learning
    - Policy Gradient Methods
    - Multi-Armed Bandits
  - Data Preparation and Exploratory Analysis
    - Data Cleaning and Missing Values
    - Feature Scaling and Encoding
    - Feature Selection
    - Exploratory Data Analysis
- Deep Learning
  - Neural Network Training
    - Feedforward Networks and Activation Functions
    - Backpropagation
    - Optimizers for Neural Networks
    - Regularization of Neural Networks
    - Initialization and Normalization Layers
  - Neural Network Architectures
    - Convolutional Neural Networks
    - Recurrent Neural Networks and LSTMs
    - Attention and Transformers
    - Word Embeddings
    - Autoencoders and Variational Autoencoders
    - GANs and Diffusion Models

### 33 Game Theory (28 subtopics, G17)

- Non-Cooperative Game Theory
  - Strategic-Form Games
    - Dominance and Iterated Elimination
    - Pure-Strategy Nash Equilibrium
    - Mixed-Strategy Nash Equilibrium
    - Zero-Sum Games and Minimax
    - Correlated Equilibrium
    - Potential and Congestion Games
  - Extensive-Form Games
    - Backward Induction
    - Subgame-Perfect Equilibrium
    - Imperfect Information and Behavioral Strategies
    - Alternating-Offer Bargaining
  - Repeated Games
    - Finitely Repeated Games
    - Infinitely Repeated Games and Folk Theorems
  - Games of Incomplete Information
    - Bayesian Nash Equilibrium
    - Signaling Games and Perfect Bayesian Equilibrium
  - Evolutionary Game Theory
    - Evolutionarily Stable Strategies
    - Replicator Dynamics
- Mechanism Design and Auctions
  - Auctions
    - First-Price and Dutch Auctions
    - Second-Price and English Auctions
    - Revenue Equivalence and Optimal Auctions
    - Common-Value Auctions and the Winner's Curse
  - Mechanism Design
    - Revelation Principle and Incentive Compatibility
    - VCG Mechanisms
    - Gibbard-Satterthwaite and Strategy-Proof Voting
    - Stable Matching
- Cooperative Game Theory
  - Coalitional Games
    - Characteristic Functions and the Core
    - Shapley Value
    - Voting Power Indices
    - Nash Bargaining Solution

### 34 Algorithms and Data Structures (62 subtopics, G15)

- Data Structures
  - Linear Data Structures
    - Arrays and Address Calculation
    - Linked Lists
    - Stacks
    - Infix, Prefix and Postfix Expressions
    - Queues and Deques
  - Trees
    - Binary Tree Properties
    - Tree Traversals
    - Binary Search Trees
    - AVL Trees
    - Red-Black Trees
  - Hashing
    - Hash Functions and Universal Hashing
    - Separate Chaining
    - Open Addressing
  - Advanced Data Structures
    - Binary Heaps
    - Binomial and Fibonacci Heaps
    - Disjoint-Set Union-Find
    - Tries and Suffix Trees
    - Segment Trees and Fenwick Trees
    - Skip Lists and Treaps
- Algorithms
  - Algorithm Analysis
    - Asymptotic Notation
    - Divide-and-Conquer Recurrences
    - Time Complexity of Code Fragments
    - Amortized Analysis
    - Loop Invariants and Correctness Proofs
    - Lower Bounds and Adversary Arguments
  - Sorting and Searching
    - Binary Search
    - Elementary Sorting Algorithms
    - Merge Sort
    - Quicksort
    - Linear-Time Sorting
    - Selection Algorithms and Medians
  - Divide and Conquer
    - Divide-and-Conquer Design
    - Fast Multiplication Algorithms
    - Computational Geometry Algorithms
  - Greedy Algorithms
    - Greedy Choice and Exchange Arguments
    - Interval and Job Scheduling
    - Huffman's Algorithm
  - Dynamic Programming
    - Principles of Dynamic Programming
    - Knapsack and Subset Sum
    - Longest Common Subsequence and Edit Distance
    - Matrix-Chain Multiplication and Optimal BSTs
    - Coin Change and Rod Cutting
    - Dynamic Programming on Trees and DAGs
  - Graph Algorithms
    - Graph Representations
    - Breadth-First Search
    - Depth-First Search
    - Topological Sorting
    - Strongly Connected Components and Biconnectivity
    - Minimum Spanning Trees
    - Single-Source Shortest Paths
    - All-Pairs Shortest Paths
    - Maximum Flow and Minimum Cut
    - Bipartite Matching Algorithms
  - String Matching
    - Naive and Rabin-Karp Matching
    - Knuth-Morris-Pratt Algorithm
    - Boyer-Moore and Automaton Matching
  - Randomized Algorithms
    - Las Vegas and Monte Carlo Algorithms
    - Probabilistic Analysis of Algorithms
    - Streaming and Sampling Algorithms
  - Intractable Problems
    - NP-Completeness Proofs by Reduction
    - Approximation Algorithms
    - Backtracking and Branch and Bound

### 35 Databases (34 subtopics, G16)

- Database Systems
  - Data Modelling
    - Entity-Relationship Modelling
    - ER-to-Relational Mapping
    - Keys and Integrity Constraints
  - Query Languages
    - Relational Algebra
    - Relational Calculus
    - Basic SQL Queries and Joins
    - SQL Aggregation and Grouping
    - Nested and Correlated Subqueries
    - SQL Schema Definition, Views and Triggers
  - Normalization
    - Functional Dependencies and Armstrong's Axioms
    - Attribute Closure and Candidate Keys
    - Minimal Cover
    - Normal Forms up to BCNF
    - Lossless and Dependency-Preserving Decomposition
    - Multivalued Dependencies and Fourth Normal Form
  - Transactions and Concurrency Control
    - ACID Properties and Transaction States
    - Conflict and View Serializability
    - Recoverable and Cascadeless Schedules
    - Two-Phase Locking
    - Timestamp and Multiversion Concurrency Control
    - Isolation Levels and Anomalies
    - Log-Based Recovery
    - Checkpoints and ARIES
  - Storage and Indexing
    - File Organisation and Blocking
    - Primary, Clustering and Secondary Indexes
    - B-Trees
    - B+ Trees
    - Extendible and Linear Hashing
  - Query Processing and Optimization
    - External Sorting
    - Join Algorithms and Their Cost
    - Query Optimization
  - NoSQL and Distributed Databases
    - NoSQL Data Models
    - CAP Theorem and Eventual Consistency
    - Distributed Transactions and Commit Protocols

### 36 Programming Languages and Compilers (45 subtopics, G16)

- Programming Language Concepts
  - Names, Binding and Storage
    - Binding Times and Storage Allocation
    - Static and Dynamic Scoping
    - Parameter Passing Mechanisms
    - Pointers and Dynamic Memory
    - Garbage Collection
  - Types and Type Systems
    - Type Constructors and Composite Types
    - Type Checking and Type Equivalence
    - Parametric Polymorphism and Generics
    - Type Inference
  - Control Flow and Evaluation
    - Expression Evaluation and Side Effects
    - Recursive Program Tracing
    - Exception Handling
  - Programming Paradigms
    - Functional Programming Concepts
    - Lambda Calculus
    - Logic Programming
    - Classes, Objects and Encapsulation
    - Inheritance and Dynamic Dispatch
  - Formal Semantics
    - Operational Semantics
    - Denotational Semantics
    - Axiomatic Semantics and Hoare Logic
- Compiler Design
  - Compiler Structure and Lexical Analysis
    - Phases of a Compiler
    - Tokens and Lexemes
    - Lexical Analyzer Generators
    - Symbol Tables
  - Syntax Analysis
    - Grammar Transformations for Parsing
    - FIRST and FOLLOW Sets
    - LL(1) Parsing
    - Shift-Reduce and Operator-Precedence Parsing
    - LR(0) and SLR Parsing
    - CLR and LALR Parsing
  - Syntax-Directed Translation
    - Syntax-Directed Definitions
    - Translation Schemes
    - Semantic Analysis
  - Intermediate Code Generation
    - Three-Address Code
    - Syntax Trees and DAGs
    - Static Single Assignment Form
    - Backpatching and Control-Flow Translation
  - Code Optimization
    - Basic Blocks and Flow Graphs
    - Local and Peephole Optimization
    - Loop Optimization
    - Data-Flow Analysis
  - Code Generation and Runtime Environments
    - Activation Records and the Runtime Stack
    - Register Allocation
    - Instruction Selection and Target Code
    - Linking and Loading

### 37 Computer Networks (28 subtopics, G14)

- Computer Networks
  - Network Models and Performance
    - Layered Network Architectures
    - Delay, Throughput and Bandwidth-Delay Product
    - Circuit, Packet and Message Switching
  - Data Link Layer
    - Framing and Stuffing
    - Error Detection in Networks
    - Sliding Window Protocols
    - Random Access Protocols
    - Controlled Access Protocols
    - Ethernet and LAN Switching
  - Network Layer
    - IPv4 Addressing and Subnetting
    - Forwarding and Longest-Prefix Matching
    - IP Datagrams and Fragmentation
    - Distance-Vector Routing
    - Link-State Routing
    - ARP, DHCP, NAT and ICMP
    - Traffic Shaping and Quality of Service
  - Transport Layer
    - UDP and Port Multiplexing
    - TCP Connection Management
    - TCP Flow Control and Retransmission
    - TCP Congestion Control
  - Application Layer
    - Domain Name System
    - HTTP and Web Caching
    - Email Protocols
    - File Transfer Protocols
  - Network Security
    - Symmetric-Key Ciphers and Modes
    - Hashes, MACs and Digital Signatures
    - Authentication and Key-Exchange Protocols
    - Secure Protocols and Firewalls

### 38 Theory of Computation (25 subtopics, G15)

- Automata and Formal Languages
  - Regular Languages
    - Deterministic Finite Automata
    - Nondeterministic Finite Automata
    - DFA Minimization and Myhill-Nerode
    - Regular Expressions
    - Regular Grammars
    - Closure and Decision Properties of Regular Languages
    - Pumping Lemma for Regular Languages
  - Context-Free Languages
    - Context-Free Grammars and Ambiguity
    - Normal Forms and CYK
    - Pushdown Automata
    - Deterministic Context-Free Languages
    - Pumping Lemma for Context-Free Languages
    - Closure and Decision Properties of CFLs
  - Turing Machines
    - Turing Machine Design
    - Variants of Turing Machines
    - Linear-Bounded Automata and Context-Sensitive Languages
    - Chomsky Hierarchy
- Computability and Complexity
  - Computability
    - Decidable Problems for Automata and Grammars
    - Recursive and Recursively Enumerable Languages
    - Halting Problem and Diagonalization
    - Mapping Reductions and Rice's Theorem
    - Post Correspondence Problem
  - Computational Complexity
    - P, NP and co-NP
    - Polynomial-Time Reducibility and NP-Hardness
    - Space Complexity

## Additions to existing subjects (additions only: no moves, no renames)

Each existing tree was read in full first. Conventional Energy Technologies already holds plant economics (load curves
and factors, costs, depreciation, tariffs, load sharing, planning and siting), hydro (hydrology, plant elements, turbines,
pumped storage), nuclear plants at plant level (reactor types, layout, safety and waste, India's programme) and
environmental control (ash, dust collectors, SOx and NOx, acid rain, cooling-tower thermal pollution), so it gets one
node. Circuits and Electronics already holds amplifiers, feedback, oscillators, op-amp applications, power-amplifier
classes, active filters and data converters, so it gets the electronics-engineering topics it lacks (tuned amplifiers,
distortion, thermal design, circuit noise, regulators and references, switched-capacitor and CMOS op-amp circuits,
transistor-level VLSI logic and memory cells). Signals, Systems and Control already holds analog modulation, noise, basic
digital modulation, information theory and block, cyclic and convolutional codes, so it gets detection theory,
synchronisation and equalisation, further information theory and coding, and a wireless branch; random-access MAC
protocols (ALOHA, CSMA) went to Computer Networks instead.

### Conventional Energy Technologies (+1)

- Thermal Power Plant Engineering > Ash, Dust and Emission Control
  - Carbon Capture and Storage

### Circuits and Electronics (+14)

- Analog Electronics > Transistor Amplifiers
  - Tuned Amplifiers
  - Harmonic Distortion in Amplifiers
  - Power Transistor Thermal Design
  - Noise in Electronic Circuits
- Analog Electronics > Operational Amplifier Circuits
  - Transimpedance and Voltage-to-Current Converters
  - Switched-Capacitor Circuits
  - CMOS Op-Amp Design
- Analog Electronics > Feedback and Oscillators
  - Function Generators and VCOs
- Analog Electronics > Voltage Regulators and References (new branch)
  - Series and Shunt Transistor Regulators
  - Three-Terminal IC Regulators
  - Bandgap and Voltage References
- Digital Electronics > Logic Families, Memories and Converters
  - Dynamic and Pass-Transistor Logic
  - Logical Effort and Gate Sizing
  - SRAM and DRAM Cell Circuits

### Signals, Systems and Control (+17)

- Communication Systems > Noise in Communication Systems
  - Bandpass Noise Representation
  - Signal-Space Representation
  - MAP and ML Detection
- Communication Systems > Pulse and Digital Modulation
  - Noncoherent and Differential Detection
  - Channel Equalization
  - Carrier and Symbol Synchronization
- Communication Systems > Information Theory and Coding
  - Asymptotic Equipartition Property
  - Rate-Distortion Theory
  - Arithmetic and Lempel-Ziv Coding
  - BCH and Reed-Solomon Codes
  - Turbo and LDPC Codes
- Communication Systems > Wireless Communication (new branch)
  - Multipath Fading and Doppler Spread
  - Path Loss and Shadowing Models
  - Diversity Combining
  - MIMO Systems
  - OFDM Systems
  - Cellular Frequency Reuse and Trunking

## Proposals: existing nodes that might later move (nothing moves tonight)

Rows counted read-only in amplify.db (table questions: topic, branch, subtopic) on 2026-11-25.

| P | Existing node(s) | Rows | Would go to | Recommendation |
|---|------------------|------|-------------|----------------|
| P1 | Circuits and Electronics > Digital Electronics: branches Number Systems and Codes (4 nodes), Boolean Algebra and Logic Minimisation (5), Combinational Circuits (6), Sequential Circuits (6), and the node Semiconductor Memories | 6 (Binary Codes 1, Signed Numbers 1, Decoders 1, Programmable Logic Devices 1, Latches and Flip-Flops 2) | Digital Logic and Computer Architecture > Digital Logic Design, names unchanged (Floating-Point Representation could sit under Computer Arithmetic) | Approve: the decided scope of subject 30 needs it. Logic Families, ADC and DAC (4 rows) stay in Circuits |
| P2 | Statistics > Mathematical Statistics > Statistical Learning (8 nodes) | 13 (Classification with kNN and Discriminant Analysis 10, Cross-Validation and Model Selection 3; the other six 0) | Machine Learning and Data Science > Machine Learning (Supervised Learning; PCA and clustering to Unsupervised Learning), names unchanged | Approve, and drop "statistical learning as theory" from the Statistics row |
| P3 | Quantitative Finance > Trading and Market Making > Game Theory: Nash Equilibrium in Strategic Games, Sequential Games and Bargaining, Auctions and Bidding | 6 (3, 0, 3) | relabel each row into the Game Theory fine nodes, then retire the three nodes | Approve |
| P4 | Material Science semiconductor nodes: p-n Junctions and Transistors, Integrated Circuit Fabrication (relabel and retire); Crystal Growth and Purification of Silicon, Diffusion Doping of Semiconductors (move as named); Luminescence, LEDs and Lasers (semiconductor-emitter rows only) | 16, 10; 11, 5; 9 | Semiconductor Devices (junction, BJT and MOS nodes; Integrated Circuit Processing; Light-Emitting Diodes, Semiconductor Lasers) | Approve. Energy Bands and Band Gap (64), Intrinsic (28), Extrinsic (50) and Hall Effect (11) stay under the fixed decision; move them only if all semiconductor physics should sit in subject 29, which changes STYLE.md |
| P5 | Combinatorics > Logic and Algorithmic Puzzles > Algorithmic Puzzles: List and Array Algorithms, Sorting and Selection by Comparisons | 27, 28 | review row by row: algorithm-analysis rows to Algorithms and Data Structures (Lower Bounds and Adversary Arguments, Selection Algorithms and Medians, Divide-and-Conquer Design), puzzles stay | Optional. Tower of Hanoi (6), River Crossing (24), Minimum Cuts (20) and Egg-Drop (28) stay |
| P6 | CET > Diesel Engine Power Plants: IC Engine Classification and Terminology 14, Four-Stroke and Two-Stroke 9, Petrol and Diesel Comparison 21, Fuel Injection 6, Cooling 7, Lubrication 9, Combustion and Knock 19, Supercharging 10, Engine Performance and Testing 38, Air-Standard Cycles 16 | 149 | Mechanical Engineering > Internal Combustion Engines | Not now: these rows come from the power-plant books (source rule). Revisit if Mechanical Engineering imports bring many engine questions; the move would need an exception to the Rajput and Nag rule |
| P7 | CET > Nuclear Power Engineering: Reactor Physics (4 nodes) and Nuclear Physics for Reactors (5 nodes) | 76 and 53 | Nuclear Engineering (Reactor Theory) | Not now (source rule); listed in case one home for reactor physics is preferred |
| P8 | Quantum Mechanics > Radiation and Detection: Interaction of Radiation with Matter, Detectors and Accelerators | 47, 39 | dose, shielding and detector-system rows to Nuclear Engineering; physics rows stay | Optional, needs a row review |
| P9 | Mechanics > Plane Kinematics of Rigid Bodies (its note names cams, linkages, gears); Mechanics > Beam Deflection | 36; 2 | mechanism rows to Mechanical Engineering > Kinematics of Mechanisms (and drop "cams, linkages, gears" from the note); beam deflection to Beams and Trusses if Srinath's rule allows | Recommend the note edit; rows by review |
| P10 | Thermodynamics > Refrigerators and Heat Pumps; Humidity and Psychrometrics | 31, 12 | system-level rows to Mechanical Engineering > Refrigeration and Air Conditioning | Optional |
| P11 | Probability > Graphical Models and Message Passing | 3 | Machine Learning and Data Science > Probabilistic Models | Optional |
| P12 | Material Science > Metal Forming and Casting | 2 | Mechanical Engineering > Manufacturing Engineering | Optional |

## Points for the morning

1. The no-second-homes policy leaves two new subjects thin until their moves: Digital Logic and Computer Architecture has
   only three digital-logic nodes of its own (P1 brings 22), and Machine Learning and Data Science has no trees,
   ensembles, PCA, k-means, kNN, cross-validation or ridge/lasso nodes (P2 brings 8). P1-P3 together relabel 25 rows; approving them
   before the next classification wave gives the full trees.
2. Mechanical Engineering has 94 subtopics, above the 25-60 guide. If that is too fine, the first merges would be Cotter
   and Knuckle Joints into Threaded Fasteners, the two Design Against Fluctuating Loads nodes into one, Powder Metallurgy
   and Additive Manufacturing into one, and the four Industrial Engineering branches into two.
3. Left out of Mechanical Engineering because they are outside the decided scope: reciprocating air compressors and jet
   propulsion (they will land in Thermodynamics' Ideal-Gas Processes and Fluid Mechanics' Moving and Accelerating Control
   Volumes). IC engines are split (P6).
4. Algorithms and Data Structures keeps the owner's first limit in its scope line: questions answered by reasoning,
   proof, tracing or pseudocode, now including conceptual and MCQ data-structure questions; code-writing tasks would go
   to the wastebasket. Please confirm.
5. Judgment calls in the rules: complexity classes in Theory of Computation and concrete NP-completeness reductions in
   Algorithms and Data Structures; stable matching in Game Theory; Huffman's algorithm in Algorithms and Data Structures
   with code efficiency in Source Coding; all B-tree and B+-tree questions in Databases; CRC on frames in Computer
   Networks with cyclic-code theory in Signals, Systems and Control.
6. Conventional Energy Technologies got one addition (Carbon Capture and Storage). Considered and not added because
   existing nodes cover them: flue-gas desulfurisation and NOx control (in Gaseous Emissions and Acid Rain), levelised
   cost (in Cost of Generation per kWh and Plant Depreciation and Present Worth), nuclear-plant waste and siting.
7. The app's subject bundles (taxonomy/tools/create_subjects.py DESCRIPTIONS) have no entries for subjects 27-38 yet.
