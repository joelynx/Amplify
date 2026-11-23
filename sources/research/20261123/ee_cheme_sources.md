# Electrical and Chemical Engineering question sources for Amplify

Survey date: 2026-11-23. Research only. Nothing was imported and no project file was changed. Small samples (SuperGPQA JSONL, EngiBench CSV, MMLU-Pro engineering rows, ControlBench .tex, ElectroVizQA and WirelessMathBench JSON, GATE 2025 EE/EC/CH PDFs, Ellingson problem PDFs) sit in `scratchpad/research/samples_*` for reference. The bank (46,923 rows) was read once, read-only, for an overlap check.

How the numbers were obtained:
- **counted**: I computed it from the data file or the official listing.
- **card**: taken from the dataset card or paper.
- **est.**: my estimate from a sample, flagged where it matters.

## 0. What the bank already covers (it shapes the recommendations)

- **EE-adjacent subjects already in the bank:**
  - *Electrical Machinery* (385 rows).
  - *Power Systems and Power Electronics*, only 57 rows: Power Converters 30, AC/three-phase 9, Drives 11, Devices 7. It is thin, so power rows from new sources are welcome there.
  - *Electromagnetism and Special Relativity*, with physics-level circuit branches: Direct-Current Circuits 105, Transient and AC Circuits 62, Electronic Circuits 4.
  - *Material Science > Semiconductors* (162).
- **No bank subject yet for:** circuit analysis at the engineering level, analog/digital electronics, signals and systems, control, communications, EM waves/transmission lines/antennas, measurements, or microprocessors.
- **ChemE-adjacent rows:**
  - *Heat Transfer > Heat and Mass Transfer > Mass Transfer*: only 18 rows.
  - Fluid Mechanics, Thermodynamics (incl. ThermoQA), Conventional Energy.
  - No subject for material/energy balances, reaction engineering, separations, ChemE thermodynamics (VLE), process control, or design and economics.
  - New subjects or subtopics need the owner's go-ahead.
- **TheoremQA leftovers:** the earlier import left out 76 EE-type rows (signals 47, information theory 29) because no subject existed. They are a free win once an EE subject exists.
- **Standing constraints that apply here:**
  - PDF-only sources (GATE, OCW, NPTEL, ESE) wait for the owner's OCR tool (owner, 2026-11-20). GATE PDFs also render some math as non-extractable glyphs (pdftotext loses variables in the 2025 GA section), so OCR or vision is really needed.
  - Bulk imported text stays out of the public repo.
  - Programming tasks are excluded (RTL/Verilog, Python notebooks, EDA flows).
  - NC (non-commercial) and SA (share-alike) licences are fine for a personal, non-commercial app. They would block or constrain a commercial Amplify.
- **Overlap check** (5-word shingles, at least 60% containment, read-only against `amplify.db`):
  - SuperGPQA EE+ChemE: 12 of 1,956 rows hit the bank (about 0.6%, mostly JEE-style physics).
  - MMLU-Pro engineering: 2 of 969.
  - EEE-Bench was checked earlier (survey/eeebench): 0 of 2,860.

---

## 1. Electrical engineering candidates

| # | Source | License / terms | EE sub-areas | Relevant Qs | Level | Format | Answers / solutions | Needs image | Text | Access |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | **SuperGPQA** (m-a-p) | **ODC-BY** (permissive) | circuits, signals, comms, antennas, EM/microwave, control, microelectronics, instruments; power/HV too | **1,546** in 5 EE fields (counted); ~1,130 in gap subfields; 366 power/HV | UG-hard/grad | MCQ, 4-10 options (mostly 10) | key letter + answer text; **no solutions** | **0% images**; 95 rows (6%) say "figure/shown" with no figure (drop) | `$...$` LaTeX in 59%, some OCR spacing noise | HF `m-a-p/SuperGPQA` (one 24 MB JSONL) |
| E2 | **GATE EE / EC / IN** official papers + keys | © organising IIT/IISc; **no licence, no reuse terms** (private use only) | full EE/EC/IN syllabi incl. maths (~13%) | ~55 technical per paper; 2007-2025 ≈ **3,500-3,800** raw (est.); 2019-2025 on the current site = 7 years x 3 papers (counted listing) | UG (PG-entrance) | MCQ / MSQ / NAT (numeric with official ranges) | official keys only; no solutions | **EE ~35-40%, EC ~45%, IN ~40%** (2025: keyword proxy 31% / 42%; visual sample 5 of 13 EE questions) | PDF; math partly as glyphs, needs OCR | `gate2026.iitg.ac.in/download.html` (2019-2025 papers + keys); older years on earlier organisers' sites |
| E3 | **MMLU-Pro** engineering (TIGER-Lab) | **MIT** | ElectricCircuits 67, ElectronicCommunications 115, Electromagnetics 100, MMLU-EE 67 (+ ElectricalMachines 102) | **~350 gap** + 102 machines (counted) | UG | MCQ, 10 options | key only (`cot_content` empty) | **0%** (2 figure mentions) | plain text + bits of LaTeX | HF `TIGER-Lab/MMLU-Pro` (test, category=engineering) |
| E4 | **EEE-Bench** (CVPR 2025; HF `afdsafas/EEE-Bench`) | MIT on card, but **paper: academic research only, no commercial use**; third-party GATE/OCW figures | circuits 592, analog 583, digital+µP 496, control 239, devices 219, signals 138, comms 101, EM 102, machines 161, PE+PS 229 | **2,860** (2,368 in gaps) (card + paper) | UG (GATE-like) | MCQ 72%, numeric 28% | final answer only | **100%**; every figure squashed to 384x384 | `\( \)` LaTeX, 42 repairable escape defects | HF parquet; surveyed in `survey/eeebench` |
| E5 | **Ellingson, *Electromagnetics* Vol 1-2** (Virginia Tech Open EM Project) | **CC BY-SA 4.0** | transmission lines, electrostatics, magnetostatics, waves, waveguides, fibre, radiation, antennas | **159** problems (Vol 1 99, Vol 2 60; counted), many multi-part | UG 3rd year | free response, numeric | **public solutions manuals** (Vol 1 v1.1, Vol 2) | ~5-8% (12 "figure" mentions) | LaTeX source zip; PDFs | vtechworks.lib.vt.edu handles 10919/84164, 10919/93253 |
| E6 | **ControlBench** (UIUC/UMich, arXiv 2404.03647) | **no licence** in repo (only the website is CC BY-SA); partly Schaum's-derived | Laplace, stability, time response, block diagrams, root locus, Bode, Nyquist, margins, state space, loop shaping | **147** (+100 MCQ rewrites in ControlBench-C) (counted) | UG | free response; 19 have a commented "Short Answer" | **worked LaTeX solutions for all** | **21%** of statements (31/147) | clean LaTeX | GitHub `AGI4Engineering/LLM4Control` (.tex + figs) |
| E7 | **TheoremQA EE leftovers** | MIT | signals & systems 47, information theory 29 | **76** | UG/grad | numeric/bool/list | answers; few explanations | few | LaTeX | already downloaded (`dl/theoremqa`) |
| E8 | **Socratic Electronics** (Kuphaldt; = All About Circuits worksheets) | **CC BY 3.0 US** (site), worksheets say CC BY 1.0 | DC/AC, network theorems, semiconductors, BJT/FET amps, op-amps, digital (K-maps, flip-flops, counters, ADC/DAC), instruments, motors | ~3,500-4,000 question files (file numbers reach ~04000; est.); 322 topical worksheets (counted) | technician / 2-year college | free response, lots of "explain"/troubleshooting; numeric subset | short **answers for every question** + instructor notes | **~60-80%** (est. from sample) | TeX + EPS source (`selec.tar.gz`, 52 MB), PDFs | ibiblio.org/kuphaldt/socratic |
| E9 | **MIT OCW EECS** (6.003 F11, 6.013 S09, 6.012 F09, 6.002 S07, 6.011, 6.302, 6.450, 6.004) | **CC BY-NC-SA 4.0** | signals, EM, devices/circuits, circuits, control, comms, digital | ~300-500 multi-part problems (est.); solutions confirmed for 6.003 (psets + exams) and 6.013 (psets + exams); 6.012 exams only; **6.002 S07 has none** | UG MIT | free response | worked solutions where listed | ~50% (est.) | PDF, older ones scanned/handwritten | ocw.mit.edu |
| E10 | **NPTEL** EE/ECE course assignments | footer says "CC BY-NC-SA" (worded inconsistently, plus "All rights reserved"); treat as **NC-SA** | every core EE/ECE course | ~100 per course (8-12 weeks x ~10), thousands overall (est.) | UG | MCQ / MSQ / NAT | accepted answers; some courses post solution PDFs/videos | ~30-50% (est.) | HTML (JS, login) + PDFs | onlinecourses.nptel.ac.in, archive.nptel.ac.in |
| E11 | **Fiore open texts** (DC, AC, Semiconductor Devices, Op-Amps) | **CC BY-NC-SA 4.0** | circuits, devices, op-amps | 500+ end-of-chapter problems per book (card) | 2-year/UG | free response, numeric | answers to selected odd problems only | ~60-70% (est.) | LibreTexts HTML (MathJax) / PDF | eng.libretexts.org, mvcc.edu |
| E12 | **ElectroVizQA** | **no licence** in repo | digital logic: K-maps 182, truth tables 147, SOP/POS, delays, De Morgan | **626** (counted) | UG intro | MCQ (4 options) | key only | 100% have an image, but **396 are flagged answerable from a text description** of the circuit | plain | GitHub `Pragati-Meshram/ElectroVizQA` |
| E13 | **CircuitSense** curated Analysis | MIT on card, but items are **copied textbook examples** (source files cite Razavi, Alexander & Sadiku, etc.) | circuits, op-amps, CMOS analog, state equations, two-port, block diagrams | **2,028** curated analysis items (counted: levels 632/477/74/796/49) + ~5,000 synthetic | UG-grad | MCQ (5 incl. "None") + symbolic answer | **worked derivations** (textbook solutions) | **100%** | LaTeX | HF `armanakbari4/CircuitSense` |
| E14 | **UPSC ESE** prelims (EE, E&T) | UPSC copyright; Indian government sites usually allow reproduction only with emailed permission (upsc.gov.in returned 403, not verified) | full EE/ECE | ~150 per paper per year; ~1,300 since 2017 (est.) | UG (service exam) | MCQ, many "statements 1 and 2 only" | official keys | ~20-30% (est.) | PDF | upsc.gov.in |
| E15 | **MMMU** Electronics, Energy_and_Power | Apache-2.0 | circuits, power | **70** with answers (dev 5 + val 30 each; test answers hidden) | UG | MCQ | key + some explanation | 100% | LaTeX-ish | HF `MMMU/MMMU` |
| E16 | **EngiBench** L1/L2 (AI4Engi) | **no licence** | circuits, comms, control, PE, HV, antennas | ~874 EE-flavoured (counted) | mixed | numeric / short / recycled 10-option MCQ | answers only | ~6% figure mentions, no images | LaTeX | GitHub `AI4Engi/EngiBench` |
| E17 | **WirelessMathBench** / **TeleMath** | CC BY 4.0 / MIT (gated) | wireless/telecom maths | 587 / 500 | research / professional | fill-the-equation MCQ / numeric | answers | 0% | LaTeX | HF |
| E18 | **MMCircuitEval** | no licence | chip design: general, spec, RTL front-end, back-end | 3,614 (paper) | professional | 66% open-ended | answers, 63% explanations | 42% | text | HF `charlie314159/MMCircuitEval` |

### Notes per EE candidate

**E1 SuperGPQA (ODC-BY).**
- **What I checked:** downloaded the 26,529-row JSONL and counted EE fields by subfield.
- **Gap subfields:** Electrical Theory 190, Signal and Information Processing 155, Communication Principles 116, Antenna and Radio 114, Circuits and Systems 108, Control Theory 89, EM Field and Microwave 88, Communication and Information Systems 69, Communication and Broadcasting 58 (in that field's count), Microelectronics 50, Optical Fibre 50, Instrument Science 50, Guidance/Navigation/Control 51.
- **Power rows for the thin bank subject:** Power Electronics and Drives 182, Power Systems 96, High Voltage 88. They have 35 figure-orphan rows.
- **Format:** 70% calculation (`is_calculation`), 10 options, single answer, so very checkable.
- **Quality:**
  - Some answers carry OCR-style spacing (`0. 1 5 2 4 m`).
  - "Electrical Theory" mixes in JEE-style physics; those fit the existing EM subject.
  - About 6% refer to a missing figure.
  - No solutions, so the pipeline solves; MCQ keys make judging easy.
- **Samples:**
  - A DFT of n(u(n+N)-u(n-N-1)) with 10 closed-form options. Good.
  - An RF pulse-train bandwidth question. Fine.
  - An R-L-C resonance power ratio. JEE-like.

**E2 GATE EE/EC/IN.**
- **Why it ranks high:** the best-matched source for an IIT student; the official keys include NAT ranges, so it is highly checkable.
- **Where the files are:** `gate2026.iitg.ac.in/download.html` links 2019-2025 papers and keys for every paper (e.g. `doc/download/2025/EE2025.pdf`, `2025_Key/EE_Keys.pdf`, `2023/ee_2023.pdf`, `Answer_keys2023/EE_ANS_GATE2023.pdf`).
- **What I checked:** downloaded the 2025 EE, EC and CH papers.
  - Each has 65 questions (10 general aptitude + 55 technical).
  - Figures are vector drawings inside question tables (not raster). The keyword proxy gives EE 31%, EC 42%, CH 18%. A visual check of 13 EE questions found 5 with figures, and some figures only restate the text (Q.47's SCR-L circuit is fully described in words).
- **Watch out:** EE papers have ~30% power/machines content, which fits existing subjects.
- **Blocker:** needs the OCR tool, and the figures must be cropped as images.
- **Overlap:** EEE-Bench drew on GATE (it carries "GATE 2014" watermarks), so import one or the other, not both.
- **Licence:** none stated. Treat as personal use and keep out of the public repo.

**E3 MMLU-Pro engineering (MIT).**
- **Sources:** the stemez items come from the REA "Problem Solver" books.
- **Good:** classic textbook calculations (phasors, inverse Laplace, a 50-ohm line with βl = π, AM/FM, Fourier/Laplace).
- **Limits:** 10-option MCQ, no figures, no solutions.
- **Other rows:** the 67 `ori_mmlu-electrical_engineering` items are easy knowledge questions. ElectricalMachines (102) goes to the existing subject. TransportPhenomena is in the ChemE section below.

**E4 EEE-Bench.**
- **Status:** already surveyed in detail (`survey/eeebench/REPORT.md`); it was skipped on 11-22 only because no EE subject existed.
- **Why use it:** with EE subjects added, it becomes the fastest large image-based EE import. It covers 2,368 gap rows, MCQ letters and numeric keys, and 0 overlap with the bank.
- **Costs:**
  - Images are 384x384 and distorted on wide schematics.
  - No solutions.
  - "Academic only, no commercial use" per the paper.
  - It duplicates GATE if GATE comes later.

**E5 Ellingson Electromagnetics.**
- **Fit:** a clean, permissive, text-first source with official worked solutions. It covers the EE half of EM that the bank lacks: transmission lines, Smith chart, waveguides, antennas, fibre.
- **Solutions:** the Vol 1 v1.2 problem set has 99 problems, but the visible solutions file is for v1.1, so check the alignment.
- **Sample:** "Estimate the width of a 22 Ω microstrip on εr = 3, h = 1.52 mm" (numeric, checkable).
- **Note:** CC BY-SA means derivatives must stay CC BY-SA, which is fine for statements.

**E6 ControlBench.**
- **Content:** 147 problems in LaTeX, each with a full worked solution. Topics run from Laplace preliminaries to Lyapunov and loop shaping; 31 have figures (Bode/Nyquist/root-locus plots).
- **Answers:** many are multi-part with prose answers, so a judge with the reference solution is needed. Only 19 have a short answer.
- **Licence:** no licence, Schaum's-derived. Private use only.
- **Also useful for ChemE process control.**

**E7 TheoremQA leftovers.** 76 rows (signals 47, information theory 29), MIT. They are already local and the importer exists; only an EE subject is needed. Skip the networking (23) and ML rows.

**E8 Socratic Electronics.**
- **Size and licence:** a large, CC BY question bank with answers. The TeX question files have `%(BEGIN_QUESTION)`, `ANSWER` and `NOTES` blocks, so it is machine-parseable without OCR.
- **Level and style:** technician level. Many items are conceptual ("explain why"), troubleshooting or lab-oriented.
- **Figures:** most need the EPS figure, which is convertible to PNG.
- **Expect:** ~1,000 checkable numeric/MCQ-like items after filtering (est.).
- **Overlap:** EEE-Bench used these worksheets, so there is some overlap there.

**E9 MIT OCW.**
- **Best files:** 6.003 Signals and Systems F11 and 6.013 EM S09 (problem-set and exam solutions). 6.012 has exam solutions; 6.002 S07 has problem sets only.
- **Not checked:** 6.011 S18, 6.302, 6.450 (verify).
- **6.004 S17:** the worksheets are listed, but I did not confirm a solutions file. Its programming assignments are excluded.
- **Cost:** PDF, so it needs OCR. Problems are multi-part, so split them.
- **Licence:** NC-SA.

**E10 NPTEL.**
- **Strengths:** huge breadth (every EE/ECE course, Indian syllabus). Weekly MCQ/NAT with accepted answers.
- **Costs:** a login plus a JS site, or PDFs; licence wording is ambiguous (treat as NC-SA); key quality varies.
- **When:** good later, once OCR or scraping exists.

**E11 Fiore.** Good community-college circuit and op-amp problems, but answers are given for only about half (selected odd problems), most need figures, and the licence is NC-SA. Low priority.

**E12 ElectroVizQA.**
- **Content:** small digital-logic MCQ set. The 396 "valid_for_text_only" rows come with an `image_description` such as `(A nor B) or (C nand D)`, so they work text-only.
- **Limits:** no licence (all rights reserved by default), no solutions.
- **Sample:** "Which input options guarantee an output of 1?" (truth table).

**E13 CircuitSense.**
- **Quality:** good (LaTeX, 5-option MCQ, TA answer, full derivation).
- **The problem:** the curated items are textbook examples with their textbook solutions. Example `source.txt` entries: "Design of analog CMOS integrated circuits P86 Example 3.22" and "Fundamentals of Electric Circuits P186 Example 5.6". The MIT tag does not cure that.
- **Verdict:** usable only as a private substitute for the owner's own copies of those books.

**E14 ESE.**
- **Size:** decent volume. MCQ statements are often assertion/"which are correct" types, which are weak study items.
- **Costs:** needs permission from UPSC plus OCR.
- **When:** after GATE.

**E15 MMMU.** Only 70 usable items. Ignore unless doing an image pilot.

**E16 EngiBench.**
- **What it is:** no licence. The EE rows are recycled MMLU-Pro/SuperGPQA 10-option MCQs plus JEE-style physics.
- **Note:** the repo is from 2026-04, so the paper's 939/354/467 counts include Level 3 and variants.
- **Value:** adds little beyond E1/E3. Avoid.

**E17 WirelessMathBench / TeleMath.**
- **WirelessMathBench:** research-paper "fill the masked equation" items (MIMO/RIS/ISAC). Not exam-style.
- **TeleMath:** gated, with a synthetic expansion of 50 expert seeds.
- **Verdict:** low value for study.

**E18 MMCircuitEval.** EDA/chip-flow questions (RTL, back-end) with no licence. Off-target and partly programming. Avoid.

---

## 2. Chemical engineering candidates

| # | Source | License / terms | ChemE sub-areas | Relevant Qs | Level | Format | Answers / solutions | Needs image | Text | Access |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | **SuperGPQA** ChemE field | **ODC-BY** | mass transport and separations 146, reaction engineering 107, fluid flow and heat transfer in ChemE 107, chemical transport engineering 50 | **410** (counted); ~395 after dropping figure orphans | UG-hard (55% "hard") | MCQ, 10 options | key only | **0%**; 15 figure orphans | LaTeX 69% | HF `m-a-p/SuperGPQA` |
| C2 | **GATE CH** official papers + keys | © IIT/IISc; no licence | MEB, CRE, mass transfer, thermo, fluid and particle ops, heat transfer, process control, plant design and economics, maths | ~55 technical per paper; 2007-2025 ≈ **1,000-1,100** (est.) | UG (PG-entrance) | MCQ / MSQ / NAT | official keys | **~18-25%** (2025 proxy 18%) | PDF + glyph math, needs OCR | `gate2026.iitg.ac.in` (2019-2025), older on earlier sites |
| C3 | **MIT OCW ChemE** (10.37 S07 CRE; 10.40 F03 thermo; 10.302 F04 transport; 10.32 S05 separations; 10.450 S06 process control) | **CC BY-NC-SA 4.0** | CRE, ChemE thermo, transport, separations, control | 10.37: ~60 with solutions (problem-set + exam solutions confirmed); others ~150 problems **without** solutions (est.) | UG MIT | free response, multi-part | 10.37 worked solutions; others none | ~20% (est.) | PDF | ocw.mit.edu |
| C4 | **Woolf, *Chemical Process Dynamics and Controls*** (UMich wiki, LibreTexts) | **CC BY 3.0** | modelling, sensors, P&ID, PID, stability, MIMO, DOE | ~200-300 worked examples + MCQ exercises (est.) | UG | worked examples, MCQ | solutions + MCQ keys | ~30% (est.) | HTML + MathJax | eng.libretexts.org |
| C5 | **Verrett et al., *Foundations of Chemical and Biological Engineering I*** (UBC) | **CC BY-SA 4.0** | process flowsheets, MEB, reaction stoichiometry, phase equilibrium, energy balances, unsteady state, intro control | ~150-250 examples + exercises (est.) | UG year 2 | worked examples; H5P exercises; chapter practice sets | examples solved step by step; exercise answers inside H5P widgets (verify) | ~20% (est.) | Pressbooks HTML/H5P | pressbooks.bccampus.ca/chbe220 (blocked WebFetch with 403), LibreTexts mirror |
| C6 | **MMLU-Pro** TransportPhenomena (+ ChemE-ish thermo) | **MIT** | mass transfer, diffusion, humidification, distillation (rest is heat transfer) | 148 transport, of which ~41 mass transfer/separations + ~15 ChemE thermo (counted by keyword) | UG | MCQ, 10 options | key only | 0% | plain | HF `TIGER-Lab/MMLU-Pro` |
| C7 | **LearnChemE** (CU Boulder) | **CC BY-SA 4.0** (site-wide) | MEB, thermo 1/2, fluids, heat transfer, kinetics/reactors, separations, process control | public module ConcepTests ~200-300 (est.); 1,400+ in instructor packages (need instructor verification) | UG | conceptual MCQ | answers at the end of each module | **100%** (questions are slide PNGs) | images | learncheme.com |
| C8 | **NPTEL** ChemE courses | NC-SA (ambiguous) | all core ChemE courses | thousands (est.) | UG | MCQ / MSQ / NAT | accepted answers; some solution PDFs | ~15-25% (est.) | HTML (login) / PDF | onlinecourses.nptel.ac.in |
| C9 | **ControlBench** | no licence | control (shared with EE) | 147 | UG | free response | worked solutions | 21% | LaTeX | GitHub |
| C10 | **PSE-Bench** | **MIT** | process modelling, optimisation, design/safety (HAZOP, LOPA), ML for processes | 200 (50 per domain) | grad / professional | open-ended | ground truth + 7-element rubric | 0% | text (xlsx) | GitHub `sombsuk/PSE-Bench` |
| C11 | **Kuphaldt Socratic Instrumentation** | **CC BY 4.0** | measurement, control loops, PID, valves, instruments | large (not counted) | technician | worksheet questions | answers in worksheets (verify) | high | TeX/PDF | ibiblio.org/kuphaldt/socratic/sinst |
| C12 | **EngTrace / EngChain** | not stated | thermo, kinetics, transport (+ EE, ME) | 1,350 instances from 90 templates (all branches) | UG | numeric, multi-step | reference reasoning traces | 0% | text | arXiv 2511.01650; release not found |
| C13 | **ChemBench** technical_chemistry | MIT | industrial chemistry | 40 (counted) | UG | MCQ / numeric | keys | ~0% | text | HF `jablonkagroup/ChemBench` |
| C14 | **Lamm & Jarboe, *ChemE Separations*** | CC BY-NC 4.0 | separations | unknown (examples not confirmed) | UG | - | - | - | HTML | LibreTexts |
| C15 | **EngiBench** "Chemical" | no licence | ~452 rows, almost all mole-counting (NumGLUE style) | junk | school | numeric | answers | 0% | plain | GitHub |

### Notes per ChemE candidate

**C1 SuperGPQA ChemE.**
- **Fit:** the only ready, permissive, text-only ChemE set of any size. 87% are calculations, at a genuinely hard UG level: turbulent eddy viscosity and mixing length, centrifugal pump head conditions, reaction-engineering kinetics, absorption/distillation.
- **Limits:** no solutions; some OCR-spaced numbers in options. The "fluid flow and heat transfer" rows could also go to the existing Fluid Mechanics and Heat Transfer subjects.
- **Overlap:** negligible.

**C2 GATE CH.**
- **Fit:** the backbone ChemE source, covering the whole Indian ChemE syllabus with official keys (NAT ranges).
- **Figures:** lower than EE (plots, flowsheets, tables).
- **Blocker:** OCR.
- **Licence:** none. Private use only.

**C3 MIT OCW ChemE.**
- **With solutions:** only 10.37 has both problem-set and exam solutions.
- **Without solutions:** 10.40, 10.302 (solutions on the textbook's companion site), 10.32 and 10.450 list problem sets only; the solver would write them.
- **Excluded:** 10.34 is numerical methods (programming).
- **Licence:** NC-SA.

**C4 Woolf, Process Dynamics and Controls.**
- **Fit:** CC BY with worked examples and in-text MCQs. A sampled section (9.2 P/I/D control) had both.
- **Quality:** uneven (student-written wiki). Answer-key letters don't always match the option numbering, and some examples depend on figures.
- **Process:** scrape the HTML; no OCR needed.

**C5 Verrett, Foundations of ChBE I.** Intro material and energy balances under CC BY-SA, the biggest ChemE gap. Examples show step-by-step solutions; exercises are H5P widgets (answers embedded, extraction to verify). Counts not verified.

**C6 MMLU-Pro TransportPhenomena.**
- **ChemE gap rows:** ~41 (e.g. "dew point of 60% benzene / 40% n-pentane at 1 atm", "gas-phase mass-transfer coefficient in a bubble-cap column", n-butanol evaporation through stagnant air).
- **Other rows:** most go to the existing Heat Transfer subject.

**C7 LearnChemE.**
- **Fit:** permissive licence and well-made conceptual questions.
- **Limits:** the public questions are slide images, with answers on a separate end-of-module page, so they need OCR/vision transcription. The full ConcepTest packages need instructor verification, so they are effectively unavailable.
- **Other content:** the quiz screencasts are video.

**C8 NPTEL ChemE.** Same trade-offs as E10. Good breadth: MEB, CRE I/II, mass transfer I/II, heat transfer, process control, transport phenomena, mechanical operations, plant design, process economics.

**C9 ControlBench.** See E6; it covers the process-control gap too.

**C10 PSE-Bench.** Open-ended, graduate-level questions graded by rubric, with no single checkable answer. The ML subset is out of scope. Possible later "essay/explain" items only.

**C11 Socratic Instrumentation.** CC BY 4.0 process control and instrumentation worksheets. Answer presence not confirmed. Medium-low priority.

**C12-C14.** Small, unreleased, or unconfirmed. Low priority.

**C15 EngiBench "Chemical".** Junk for ChemE: e.g. "Find the number of moles of Methane formed on combining 3 moles of Carbon and 6 moles of Hydrogen. ANS 3". Avoid.

---

## 3. Ranked recommendations

### Electrical engineering, import first

| Rank | Source | Expected usable yield | Why |
|---|---|---|---|
| 1 | **SuperGPQA EE** (E1) | **~1,050** gap rows + ~330 power/HV rows for the thin Power Systems and PE subject | ODC-BY, text-only, MCQ-checkable, one JSONL, ~0.6% overlap; broad gap coverage (signals, comms, antennas, circuits, control, microwave, devices) |
| 2 | **MMLU-Pro EE subsets** (E3) | **~330** gap + ~100 machines | MIT, text-only, classic textbook calculations; trivial to load next to E1 |
| 3 | **Ellingson EM Vol 1-2** (E5) | **~150** problems (multi-part, so more items after splitting) with official solutions | CC BY-SA, LaTeX source, transmission lines and antennas gap, worked solutions for aids mode |
| 4 | **TheoremQA EE leftovers** (E7) | **76** | Already downloaded, importer exists; needs only the new subject |
| 5 | **ControlBench** (E6) | **~140** with worked solutions | Best control set; keep private (no licence, Schaum's-derived) |
| 6 | **GATE EE/EC/IN** (E2), when OCR is ready | **~2,500-3,000** gap-relevant with official keys (~40% need cropped figures) | Highest-value exam source for the owner; official NAT ranges |
| 6-alt | **EEE-Bench** (E4), if images are wanted before OCR exists | **~2,000-2,300** gap rows | Already surveyed and image-ready, but 384 px images, academic-only, duplicates GATE |
| 7 | **Socratic Electronics** (E8) | ~1,000 checkable after filtering (est.) | CC BY, answers for all, TeX source; technician level and image-heavy |
| 8 | MIT OCW 6.003 / 6.013 / 6.012 (E9), NPTEL (E10), ESE (E14) | hundreds to thousands | After OCR; NC-SA or permission needed |

Text-ready now (ranks 1-5): about **1,750 gap questions + ~430 for existing subjects**, of which ~370 have worked solutions (Ellingson, ControlBench, part of TheoremQA). Everything big after that is image-heavy or PDF-only.

### Chemical engineering, import first

| Rank | Source | Expected usable yield | Why |
|---|---|---|---|
| 1 | **SuperGPQA ChemE** (C1) | **~395** | Only permissive, text-only, checkable ChemE set; separations, CRE, transport |
| 2 | **MMLU-Pro TransportPhenomena** (C6) | **~55** ChemE (mass transfer, ChemE thermo) + ~90 to Heat Transfer | MIT, same loader as E3 |
| 3 | **Woolf Process Control** (C4) | ~200 (est.) | CC BY 3.0, HTML (no OCR), worked examples + MCQs; fills process control |
| 4 | **Verrett Foundations of ChBE I** (C5) | ~150 (est.) | CC BY-SA, material/energy balances (biggest gap), worked examples |
| 5 | **GATE CH** (C2), when OCR is ready | **~900** with official keys (~20% figures) | Full syllabus, low image share, best-matched exam |
| 6 | **MIT OCW 10.37** + other 10.xx problem sets (C3) | ~60 with solutions + ~150 without | CRE with worked solutions; NC-SA; OCR |
| 7 | LearnChemE (C7), NPTEL (C8) | ~200 / thousands | Later; images or login, NC-SA for NPTEL |

Text-ready ChemE is thin (~450 gap questions). The real volume needs GATE CH, OCW and NPTEL through the OCR tool, or the owner's own textbooks.

### Sources to avoid (and why)

- **EngiBench** (E16/C15): no licence; EE rows are recycled MMLU-Pro/SuperGPQA; the "Chemical" rows are trivial mole counting.
- **CircuitSense curated** (E13): MIT label over copied textbook examples and solutions (Razavi, Alexander & Sadiku, ...). Only as a private stand-in for books the owner owns.
- **MMCircuitEval** (E18): chip-design/RTL (programming-adjacent), no licence.
- **ElectroVizQA** (E12): no licence. Small and fine in content, but rights are unclear; low priority rather than strict avoid.
- **"Exploring the MIT Mathematics and EECS Curriculum" dataset** (4,550 Q): withdrawn; authors "did not receive permission to release the data".
- **NCEES FE/PE practice exams, Sanfoundry/IndiaBix/Examveda MCQs, coaching-institute GATE solutions (Made Easy, PW, etc.)**: copyrighted commercial material.
- **Synthetic HF sets** (`STEM-AI-mtl/Electrical-engineering`, `theprint/Electronics-QA`, `kms7530/chemeng`, `CJJones/...Synthetic_Dialog`): LLM-generated or mixed chat data, not exam questions.
- **ChemEBench** (DICP): not released (model only via a web chat).
- **AIChE Concept Warehouse**: instructor login and terms of use.
- **C-Eval / CMMLU electrical engineer**: Chinese-only.
- **WirelessMathBench, TeleMath, PSE-Bench, HLE engineering**: research-level, gated, rubric-graded or tiny; not study-bank material.
- **MMLU electrical_engineering alone**: easy knowledge items; already inside MMLU-Pro (67).

---

## 4. Textbooks the owner could supply from their own copies (copyrighted; not for redistribution)

**Electrical:**
- *Circuits:* Alexander & Sadiku, *Fundamentals of Electric Circuits*; Hayt, Kemmerly & Durbin, *Engineering Circuit Analysis*; Nilsson & Riedel, *Electric Circuits*; Irwin, *Basic Engineering Circuit Analysis*.
- *Electronics:* Sedra & Smith, *Microelectronic Circuits*; Razavi, *Fundamentals of Microelectronics* and *Design of Analog CMOS ICs*; Boylestad & Nashelsky; Millman & Halkias.
- *Signals and DSP:* Oppenheim & Willsky, *Signals and Systems*; Lathi, *Signal Processing and Linear Systems*; Oppenheim & Schafer, *Discrete-Time Signal Processing*; Proakis & Manolakis, *DSP*.
- *Control:* Nise, *Control Systems Engineering*; Ogata, *Modern Control Engineering*; Nagrath & Gopal.
- *Communications:* Haykin, *Communication Systems*; Lathi & Ding; Proakis & Salehi.
- *Electromagnetics:* Hayt & Buck, *Engineering Electromagnetics*; Sadiku, *Elements of Electromagnetics*; Cheng; Pozar, *Microwave Engineering*; Balanis, *Antenna Theory*.
- *Digital and computer organisation:* Morris Mano, *Digital Design*; Hamacher, *Computer Organization*; Gaonkar (8085); Mazidi (8051).
- *Measurements:* A.K. Sawhney; Helfrick & Cooper.
- *Schaum's Outlines:* Electric Circuits, Electronic Devices, Signals and Systems, Feedback and Control, Analog and Digital Communications, Electromagnetics.

**Chemical:**
- *Material and energy balances:* Felder, Rousseau & Bullard, *Elementary Principles of Chemical Processes*; Himmelblau & Riggs, *Basic Principles and Calculations*.
- *Reaction engineering:* Fogler, *Elements of Chemical Reaction Engineering*; Levenspiel, *Chemical Reaction Engineering*.
- *Thermodynamics:* Smith, Van Ness & Abbott; Sandler; Koretsky.
- *Mass transfer and separations:* Treybal, *Mass-Transfer Operations*; Seader, Henley & Roper; Wankat; Dutta.
- *Unit operations and transport:* McCabe, Smith & Harriott; Geankoplis; Bird, Stewart & Lightfoot; Welty et al.; Narayanan & Bhattacharyya (mechanical operations).
- *Process control:* Seborg, Edgar, Mellichamp & Doyle; Stephanopoulos; Coughanowr & LeBlanc.
- *Design and economics:* Peters, Timmerhaus & West; Turton et al.; Coulson & Richardson Vols 1, 2, 6.

## 5. Sources consulted

- SuperGPQA: https://huggingface.co/datasets/m-a-p/SuperGPQA
- MMLU-Pro: https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro
- EEE-Bench: https://huggingface.co/datasets/afdsafas/EEE-Bench, https://arxiv.org/abs/2411.01492
- EngiBench: https://github.com/AI4Engi/EngiBench, https://arxiv.org/abs/2509.17677
- ControlBench: https://agi4engineering.github.io/LLM4Control, https://github.com/AGI4Engineering/LLM4Control
- CircuitSense: https://huggingface.co/datasets/armanakbari4/CircuitSense, https://arxiv.org/abs/2509.22339
- ElectroVizQA: https://github.com/Pragati-Meshram/ElectroVizQA
- MMCircuitEval: https://huggingface.co/datasets/charlie314159/MMCircuitEval, https://arxiv.org/abs/2507.19525
- WirelessMathBench: https://huggingface.co/datasets/XINLI1997/WirelessMathBench
- TeleMath: https://huggingface.co/datasets/netop/TeleMath
- MMMU: https://huggingface.co/datasets/MMMU/MMMU
- ChemBench: https://huggingface.co/datasets/jablonkagroup/ChemBench
- GATE: https://gate2026.iitg.ac.in/download.html, https://gate2024.iisc.ac.in/question-papers/
- NPTEL: https://nptel.ac.in/aboutus (licence footer)
- MIT OCW: 6.003 F11, 6.013 S09, 6.012 F09, 6.002 S07, 6.004 S17, 10.37 S07, 10.40 F03, 10.450 S06 course pages on https://ocw.mit.edu
- Ellingson: https://vtechworks.lib.vt.edu/handle/10919/84164, https://vtechworks.lib.vt.edu/handle/10919/93253
- Kuphaldt: https://ibiblio.org/kuphaldt/socratic/ (CC BY 3.0 US), worksheet thev.pdf (CC BY 1.0)
- LearnChemE: https://learncheme.com/contact-us/ (CC BY-SA 4.0)
- Woolf, Process Dynamics and Controls: https://eng.libretexts.org/Bookshelves/Industrial_and_Systems_Engineering/Chemical_Process_Dynamics_and_Controls_(Woolf)
- Verrett, Foundations of ChBE I: https://pressbooks.bccampus.ca/chbe220
- Lamm & Jarboe, Separations: https://eng.libretexts.org/Bookshelves/Chemical_Engineering
- PSE-Bench: https://github.com/sombsuk/PSE-Bench
- EngTrace: https://arxiv.org/abs/2511.01650
- Withdrawn MIT EECS dataset: https://arxiv.org/abs/2306.08997
