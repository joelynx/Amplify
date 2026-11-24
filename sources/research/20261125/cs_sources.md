# CS question sources (research 2026-11-24/25)

Areas: digital logic (DL), computer architecture/organization (COA), operating systems (OS), algorithms (ALGO, proofs/pseudocode), data structures (DS), machine learning (ML), data science, databases (DB), programming languages (PL), computer networks (CN), theory of computation (TOC).
Counted from real downloads (scratchpad research2\dl\<name>\); samples in research2\samples_<name>.jsonl (20 rows each).
SuperGPQA "Computer Science and Technology" (763) is excluded per coordinator (imported separately).

## Summary table

| # | Source | URL | Areas / usable rows | Key | Solutions | Format | Images | Licence | Rec | Prio |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GATE CSE bank 1987-2026 (cherie-dips/GATE-CS) | https://github.com/cherie-dips/GATE-CS, file app/public/data/questions.json (6.2 MB) | DL 274, COA 296, OS 372, ALGO 295, DS 267, DB 281, PL 200, CN 243, TOC 319 (also discrete math 391, eng. maths 267, compiler design 194, aptitude 266). Total 3,692 | yes (official IIT keys for 2022-26 = 520 rows; rest cross-checked) | yes, every row (Claude-written, see issues) | one JSON | scan/fig on ~1,100 rows | none stated; public GATE papers via ExamSIDE and GATE Overflow book | import | 1 |
| 2 | CS-Bench English | https://huggingface.co/datasets/CS-Bench/CS-Bench (CS-Bench/English/test.jsonl 2,183 + valid.jsonl 236) | DS+ALGO 538, COA 561, CN 594, OS 490 (test) | yes | no (open-ended rows have a reference answer) | jsonl | none | CC-BY-NC-4.0 | import | 2 |
| 3 | walkccc/CLRS (pre-parsed on HF: Siddharth899/clrs-qa, 1,016 rows) | https://github.com/walkccc/CLRS ; https://huggingface.co/datasets/Siddharth899/clrs-qa | ALGO/DS: 851 exercises + 151 problems = 1,002 (3rd ed.); ~830 have a solution; ~690 are prove/show/design/analyze | statement + worked solution, no short key | yes (community, uneven) | Markdown+LaTeX; HF JSON | 14 has_images (HF); ~60 mention a figure | repo MIT; book (c) Cormen et al. | import | 1 for ALGO |
| 4 | MMLU-Pro category "computer science" | https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro (data/test-00000-of-00001.parquet) | 410: ML 90, college CS 76, HS CS 62, computer security 46, theoremQA-EECS 76, stemez-ComputerScience 60 | yes | none (cot_content empty) | parquet | none | MIT | import | 3 |
| 5 | MMLU (cais/mmlu) CS/ML subsets | https://huggingface.co/datasets/cais/mmlu | machine_learning 112, college_cs 100, hs_cs 100, computer_security 100 (test) | yes | no | parquet | none | MIT | skip (same questions as MMLU-Pro ori_mmlu rows) | - |
| 6 | whiteOUO/Ladder-machine-learning-MCQs | https://huggingface.co/datasets/whiteOUO/Ladder-machine-learning-MCQs | ML 140 | yes | no | HF rows (question, A-D, answer) | none | unstated | maybe | 4 |
| 7 | TheoremQA | https://huggingface.co/datasets/TIGER-Lab/TheoremQA | 800 rows; ~116 CS/ML-keyword hits | yes | no | parquet | 53 | MIT | skip: ~492/800 already in bank by text prefix | - |
| 8 | UdayG01/DataScienceInterviewQuestions, neha-duggirala/datascience-interview-qna | HF | 47 + 26 interview Q&A | open | reference text | HF | none | unstated | skip (tiny, recall) | - |
| 9 | WithinUsAI/Computer_Science_25k | HF | 25,000 synthetic template prompts with short answers | yes | short | HF | none | unstated | skip (generated) | - |
| 10 | EPFL MCQA (gabrieljimenez/epfl-computer-science-mcqa) | HF | 337 rows, all cryptography | yes | no | HF | none | unstated | skip (off-topic) | - |

Searches for HF/GitHub key-bearing sets in DL, COA, OS, data science and ML found nothing else usable (Beifengdo/* HF repos are course-material uploads; hero707/qa-dataset-operatingsystem is Korean, 165 rows). GATE Overflow itself (GATEOverflow/GO-PDFs, ~120 MB) is PDFs, with no JSON export; the cherie-dips repo is built from it and is the machine-readable route.

## 1. GATE CSE bank (best single source, covers every area asked for)

File: https://raw.githubusercontent.com/cherie-dips/GATE-CS/main/app/public/data/questions.json (downloaded to research2\dl\gatecs\questions.json). Images: app/public/img/es/*.jpeg (ExamSIDE crops) and app/public/img/go/*.png (GO-book scans), ~1,750 files, fetch via raw.githubusercontent.com or git clone.
Top-level keys: meta, subjects (subject -> chapters with counts), papers, questions (3,692).
Question fields: id, p (paper, e.g. "GATE CSE 2016 Set 1"), ex (CSE/IT), y (year), set, n (question no.), s (subject id: dl, co, os, algo, ds, db, pl, cn, toc, dm, em, cd, ga, se, web), c (chapter id), t (MCQ/NAT/MSQ/DESC/FIB/TF), m (marks), neg, q (statement; qf = "html" or "md"), o (options; of = format), a (answer object), e (worked explanation, Markdown + `$..$` LaTeX), v (verdict flag), tags, fig (bool), scan (path of the GO scan image), oos (out of syllabus), note, official (bool).
Answer object: MCQ/MSQ {"opts":[3]} (0-based indices); NAT {"lo":12.0,"hi":12.0} (accepted range); DESC/FIB {"text":"..."}.

Counts by subject and type:
- DL 274: MCQ 181, NAT 30, DESC 35, MSQ 22, FIB 6. Chapters: boolean-algebra 76, k-maps 32, combinational 38, sequential 59, number-systems 69.
- COA 296: MCQ 186, NAT 64, DESC 25, MSQ 11, FIB 6, TF 4. Chapters: addressing modes 59, datapath/control 22, arithmetic 28, pipelining 58, memory/cache 91, I/O 33, secondary 5.
- OS 372: MCQ 235, DESC 52, NAT 49, MSQ 24, TF 8, FIB 4.
- ALGO 295: MCQ 221, NAT 31, DESC 29, MSQ 12, FIB 2. DS 267 (arrays, stacks/queues, lists, trees/BST/heaps 121, hashing, graphs 43).
- DB 281, PL 200 (C output tracing, recursion, pointers), CN 243, TOC 319.
Image dependence (fig or scan set): DL 114, COA 96, OS 91, ALGO 64, DB 69, PL 78, DS 69, CN 64, TOC 94. Text-only subset = the rest (about 60 percent of each subject).
Verdict flag v (target subjects together): agree 2,104, nokey 278, keys-resolved 87, key-corrected 24, ambiguous 21, keys_conflict 17, mta 8, disagree 8. Official keys: 520 rows (2022-2026).
Quality issues: explanations were written by Claude and answers checked by independent runs (README), not human-verified; 82 flagged questions lack the second check; 87 text fixes not applied. nokey rows (389 overall) carry the model's answer, no official key. Drop or flag v in (ambiguous, keys_conflict, disagree, mta); drop oos=true (90 rows, mostly SE/CD/web). Statements with qf=="html" contain `\( .. \)` MathJax and HTML (tables, br, img) and need converting to `$..$` and LaTeX; the repo's pipeline/mjx2tex.py shows the conversion (read it as text, do not run it). DESC rows have only a short reference answer; e is the worked solution.
Overlap with bank: none (the bank has no GATE source).
Conversion: statement = q + options (A)..(D) in order; answer: MCQ letter chr(65+opts[0]); MSQ letters joined; NAT lo (or lo-hi when different); DESC/FIB a.text; solution = e (contains a final "Answer: (D)" line). Topic from s/c via the subjects table. subsource: "GATE CSE <year>" only (year, no question number, per subsource rule). No LICENSE file in repo.

## 2. CS-Bench (English)

Files: CS-Bench/English/test.jsonl (2,183), valid.jsonl (236, also has answers). Fields: ID, Split, Domain, SubDomain, Format, Tag (Knowledge/Reasoning), Language, Question, A, B, C, D, Answer.
Domains (test): Data Structure and Algorithm 538 (MCQ 382, assertion 92, fill 45, open 19), Computer Organization 561 (MCQ 348, assertion 113, fill 69, open 31), Computer Network 594 (MCQ 344, assertion 113, fill 78, open 59), Operating System 490 (MCQ 262, assertion 124, fill 43, open 61). Reasoning-tag rows 795, knowledge 1,388.
SubDomain gives the topic directly: Processes and Threads 157, Memory Management 98, File Management, I/O Management, CPU 110, Instruction System, Data Representation, Bus, Storage, Tree 96, Graph 83, Sorting 80, Searching, Linear List, Stack/Queue/Array, String, network layers 74-142. No digital logic, ML or DB.
Issues: 408-exam style, some awkward translation; "Assertion" rows are true/false statements; open-ended rows have reference answers (spot-check blanks).
Overlap with bank: none. Licence CC-BY-NC-4.0.
Conversion: Question (+ A-D for Multiple-choice), assertion -> "True or false: ..." with Answer, fill-in answer as string; no solutions (the solver writes them). subsource "CS-Bench" + SubDomain is a topic, not an identity: fine.

## 3. CLRS (ALGO/DS proofs and pseudocode)

Best file: HF Siddharth899/clrs-qa (1,016 rows: id like "02-2.3-3", chapter, section, title, source_file, question_markdown, answer_markdown, code_blocks, has_images, image_refs). Raw alternative: https://github.com/walkccc/CLRS/archive/refs/heads/main.zip, docs/ChapNN/N.M.md (each `## N.M-K` heading, statement as `>` blockquote, solution below) and docs/ChapNN/Problems/N-K.md (statement blockquote with a./b./c. parts, then solution). Zip count: 851 exercises + 151 problems = 1,002; 171 have no solution text.
Filters: keep statements with prove/show/argue/justify/design/give an algorithm/describe/analyze/pseudocode/recurrence/loop invariant/solve (~690); drop "illustrate ... Figure" and has_images rows (14 in HF), and rows with empty answers. Pseudocode solutions sit in ```cpp fences: convert to a verbatim/pseudocode block.
Issues: community solutions, some wrong or terse; math uses `$..$`, ```math fences and doubled backslashes (`\\\\`) in arrays; solutions cite other exercise numbers. 3rd edition. No short key: derive from solution or leave to the pipeline. Subsource: "CLRS" + chapter title only.
Overlap with bank: none (bank has Levitin puzzles only). Licence: repo MIT, book text copyrighted (personal use).

## 4. MMLU-Pro "computer science" (and MMLU)

File data/test-00000-of-00001.parquet, filter category == "computer science" (410): ori_mmlu-machine_learning 90, ori_mmlu-college_computer_science 76, theoremQA-EECS 76, ori_mmlu-high_school_computer_science 62, stemez-ComputerScience 60, ori_mmlu-computer_security 46. Fields: question_id, question, options (up to 10), answer (letter), answer_index, cot_content (empty here), category, src.
None of the 410 are in the bank (prefix check against source 'MMLU-Pro': 0/410; bank MMLU-Pro rows are stemez engineering only). theoremQA-EECS 76 probably overlap TheoremQA (check text before import).
Use: ML 90; stemez-ComputerScience 60 (Python-output reasoning is fine; drop any write-code item); college CS 76 and HS CS 62 (DS/ALGO/COA/OS/PL mix); security 46 (outside the brief). Map: question + options A..J, answer letter, no solution.
MMLU (cais/mmlu) machine_learning, college/high_school_computer_science, computer_security hold the same questions as the ori_mmlu rows, so import via MMLU-Pro only (or MMLU only), not both.

## 5. ML and data science

No large key-and-solution set found. Yield: MMLU-Pro ML 90; whiteOUO/Ladder-machine-learning-MCQs 140 (question, A-D, answer; conceptual, looks generated: check duplicates with the MMLU ML rows); TheoremQA ML/info-theory rows (~100 by keyword, mostly already in bank); GATE has no DA-paper data in this repo. UdayG01 (47) and neha-duggirala (26) are open-ended interview Q&A: skip. Statistics is already well covered in the bank (Sahoo, Dekking, Schwarz, Mathematics for ML 63). Expect this area to stay thin (~230 rows) until a PDF source is OCRed.

## 6. Per-area pointers

- Digital logic: GATE DL 274 (Boolean algebra, K-maps, sequential, number systems). No other machine-readable set found.
- Computer architecture: GATE COA 296 (pipelining, cache, numeric problems) + CS-Bench Computer Organization 561.
- OS: GATE OS 372 (scheduling, page faults, deadlock, semaphores, numeric) + CS-Bench OS 490.
- Algorithms (proofs/pseudocode): CLRS ~690; GATE ALGO 295 (keep NAT, DESC, recurrence MCQs); CS-Bench open-ended 19.
- Data structures: GATE DS 267, CS-Bench DS 538, CLRS parts II-III.
- Databases: GATE DB 281 (SQL result tracing, normalization, transactions, relational algebra). CS-Bench has none.
- PL: GATE PL 200 (C tracing) + MMLU-Pro stemez-ComputerScience 60.
- Networks: CS-Bench CN 594 + GATE CN 243 (subnetting, TCP windows, numeric).
- TOC: GATE TOC 319 (DFA/regex/CFG/Turing/undecidability) + discrete math 391 if wanted.

## PDF-only sources (wait for OCR)
- Jeff Erickson, Algorithms (github.com/jeffgerickson/algorithms: PDFs only, chapters 00-12).
- GATEOverflow/GO-PDFs (github.com/GATEOverflow/GO-PDFs): GATE CSE books by subject with answers.
- MIT OCW 6.006/6.046/6.042 problem sets and solutions.
- Hennessy and Patterson, Silberschatz, OSTEP exercise solutions.
- Official GATE papers and keys (gate2024.iisc.ac.in etc.) as a cross-check for GATE keys.

## Open questions
- GATE bank has no licence file and its explanations are Claude-written: accept for personal use? Assumed yes.
- Import the 389 "nokey" GATE rows (model answer only), or hold them for a judge pass?
- GATE image rows (64-114 per target subject): fetch the jpeg/png files or skip? Text-only subset first is suggested.
- Which CS-Bench formats to take (assertion and fill-in are cheap; open-ended has no solutions).
- New bank subjects needed for DL, COA, OS, ALGO, DS, DB, PL, CN, TOC, ML.
