# New question sources: where we left off

Planning notes for adding questions from the MODS sheets and from model benchmarks.
Status on 2026-11-12: **the MODS POTD sheet is imported and classified** (section 7):
2,678 problems with their 1,723 hint sets, 618 answers and 348 human solutions, all but
3 placed in the taxonomy; none solved by the pipeline yet. The bank's "AIME" is
renamed to its full name. Solving, judging and embeddings are next; each still needs
the owner's go-ahead, as does any other source.

Supporting files are in `sources/potd/`. They hold only competition names, counts
and the sheet's Source strings, no problem text:

| File | What it is |
|---|---|
| `competition_map.csv` | 816 raw contest names → full name, group, country, kind, bank match, confidence, note, regional group, total |
| `row_assignments.csv` | One line per POTD row: POTD number, date, Source as written, full name, group, regional group, **source and subsource at the cut-off**, confidence, skip reason |
| `duplicates.csv` | Hand-reviewed 2026-11-12: 72 rows already in the bank (`bank:<question_id>`) and 16 posted twice (`potd:<kept copy>`) |
| `thresholds.md` | Own sources vs groups at cut-offs 5, 10, 15 and 20 |
| `subsource_examples.md` | The subsource format, with 15 worked examples and the rough edges |
| `scripts/build_map.py` (+ `canon.py`, `rules.py`) | Rebuilds the two CSVs: `python -I build_map.py <POTD.csv> <out_dir> [cutoff=15] [asof=today]`; reads `duplicates.csv` from `<out_dir>`, and also writes `summary.json` next to itself (not committed); `thresholds_md.py summary.json thresholds.md` then rebuilds the report, `examples.py row_assignments.csv` prints the examples |
| `scripts/potd_stats.py`, `potd_more.py`, `potd_overlap.py` | The profiling behind the numbers in section 2. `potd_overlap.py <POTD.csv> <amplify.db>` is the quick text-overlap check |
| `app/tools/import_mods_potd.py` (+ `mods_potd_fixes.json`) | The import (section 7); its docstring lists every repair |

Keep problem text out of the repo (it is public): no raw sheet exports, no review
pages with question text. The app DB is git-ignored.

---

## 1. The two sheets

Both are public Google Sheets, read as CSV through
`https://docs.google.com/spreadsheets/d/<id>/export?format=csv&gid=<gid>`.
Re-download at import time: POTD gets a new problem every day.

**Sheet 1, MODS Resources** (`15GeYB6Y_x07IGLIhfMSuXFC514ru_QFn26IZNAcWFic`), by MODS and Tony Wang.
This is a reading list, not a question set.
- Tabs: Resources (gid 0, 102 entries), Contests (1517780203, 138 olympiads with links), National MO Servers (114120154), Calendar (155403589, out of date).
- Already in the bank: Engel's Problem Solving Strategies (1,178 rows).
- **Free PDFs with problems.** Each would be a normal book import: the owner supplies the PDF, then Mathpix, an `app/tools/import_*.py` tool and a page-by-page check.
  - Sriram's Olympiad Combinatorics.
  - Khurmi's Modern Olympiad Number Theory.
  - Stevens' Olympiad Number Theory Through Challenging Problems.
  - Altizio's 100 Geometry Problems.
  - 567 Nice and Hard Inequalities (has solutions).
  - Everaise Math Competitions I and II.
  - Grinberg's Math 235 notes.
  - Sato's number theory notes.
  - Goyal's polynomial notes.
  - Hall and Knight's Higher Algebra (public domain, with answers).
- **Books that need the owner's own copy:**
  - Problem Solving Tactics, EGMO, Zeitz.
  - Concrete Mathematics (has exercise answers).
  - Problems from the Book, Geometry Revisited.
  - Pólya's books.
  - Soberón, Skopenkov.
  - Andreescu's Complex Numbers, and more.
- Problem databases:
  - AoPS Contest Collections: don't scrape (see section 6).
  - problems.ru.
  - The IMO Compendium.
  - imo-official.org.
- About 35 entries are YouTube channels, Discord servers, blogs, podcasts or interactive sites, with nothing to import.

**Sheet 2, MODS Problem of the Day (POTD)** (`10X0-CCSv7FenZP1YaKlDSE-PD4LSZAgpzT5Rs9F8hvA`).
- Tabs:
  - POTD (gid 0): the problems.
  - Curators (1140798037): Discord user IDs. Personal data, **never import**.
  - Weekly (262279424): 76 multi-part, university-level problems, e.g. Apostol's analytic number theory.
  - Potential Future POTDs (615260721): drafts and backups.
  - Acronyms (1682482900).
  - Tags and Difficulty (1943403910).
- POTD columns:
  - `/f` is the POTD number, a stable ID.
  - Date, Day, Curator, Source, G (genre), D (difficulty), T (sub-tag).
  - Problem Statement, Hint 1, Hint 2, Hint 3.
  - Answer, Discussion, Solution, Solution Link, Notes, Message ID, Image Link (empty), Solved, Solved by, In pdf?.
- Skip Discussion (chat), Message ID, Solved, Solved by, In pdf? and Curator.

## 2. POTD in numbers (snapshot of 2026-11-11)

- 2,792 problems with a statement, 26 Mar 2019 to 17 Nov 2026. Four rows were scheduled after the snapshot date.
- Already LaTeX: 2,599 contain `$` or `\(`, so no OCR is needed.
- **Hints:** 1,795 have Hint 1, 1,445 Hint 2 and 954 Hint 3.
- **Answers and solutions:**
  - 665 answers (2 are junk: "blud really thought there was an answer", "Solved by HAY. QED.").
  - 394 solutions.
  - 1,008 solution links: 527 AoPS, 217 imo-official.org.
  - 682 rows have only the statement.
- **Kind of problem:** 1,977 statements say prove/show/find all, so most are proof problems. Only 25 mention a figure.
- **Genre:** G 697, N 646, C 633, A 534, CG 112, about 170 mixed (CN, AN, AC…).
- **Sub-tags:** on 649 rows (FE 170, PO 67, IN 63, DE 54, SE 47…; meanings in the Tags tab).
- **Difficulty D (0–14, tied to contests):**
  - BMO1 1–4, BMO2 3–7, EGMO 4–8, USAMO 6–11.
  - IMO problems 1/4 are 5–7, problems 2/5 are 7–9, problems 3/6 are 9–11.
  - By weekday: Mon 0–2 … Sun 7–11.
  - Counts: 0–3: 847 · 4–6: 921 · 7–9: 804 · 10–14: 208 · invalid (`T` ×10, `-1`, `Pi^2`): 12.
- **Largest contest families:** IMO Shortlist 333, IMO 163, BMO1 ~100, USAMO 83, BMO2 64, EGMO 55, APMO 45, Putnam ~42, USA TSTST 42, USA TST 40.
- **Overlap with the bank:** a text match found only 2 (AIME 1995 P3 and one Mladenovic problem). The bank has no IMO, Shortlist, USAMO or BMO source. An embedding check at import may find more, mostly old IMO problems that Engel quotes in other words.
- **Internal repeats:** 12 by the first quick check; 16 after the hand review at import (`sources/potd/duplicates.csv`), and 72 rows already in the bank (section 4).

## 3. Owner decisions (2026-11-11)

- **No-solution and answer-only sets are fine.** Solutions are generated by a model.
  - Look up published benchmark scores. Where there are none, trust **Opus 5.5 at medium and high, and Fable 5.2 at high**.
  - Bucket questions by difficulty and by a source's density of hard questions to pick the model (section 5).
- **Multiple-choice sets are fine.** Multi-select already exists in the quiz (section 8). **No negative marking.**
- **POTD source = the competition's full name** (not the acronym). Year, round, day and problem go in the **subsource**.
- **Small competitions are merged into groups** (e.g. Chinese, Other European, Latin American Olympiads).
- **Unknown, Original and Folklore → "Math Olympiad Discord Server".** Named classics too; their original label goes in the subsource.
- **POTD's D is not stored as a field.** It is used only to assign solving models.
- **Tiered hints:** "Show hint", then "Show additional hint", greyed out after the last tier, at most 3. POTD's three hints map onto the tiers. Built and committed 2026-11-11 (section 8).

**Owner decisions (2026-11-12):**
- **Cut-off 15:** a competition with at least 15 problems is its own source.
- **Skip rows:** keep STEP and ISI (as "University Admission Exams"); skip the programming contests and the school exams.
- **AIME:** rename the bank's 748 rows to "American Invitational Mathematics Examination", with subsources in POTD's order ("2008, AIME II").
- **IMO Shortlist:** one source with the IMO; "Shortlist, C5" (or "Longlist") goes in the subsource.
- Defaults taken since (not asked): the Discord server's own contests stay under "Math Olympiad Discord Server" with the contest at the head of the subsource; the POTD number and Solution Link go to a git-ignored map file; the Weekly tab waits.

## 4. Competition table (sources/potd)

835 raw names → **292 competitions**, plus books, journals and sites, the Discord server's rows, and 23 rows skipped (programming and school exams). Counts below leave out the skipped rows, the 88 duplicates and the 3 rows scheduled after the download (2026-11-12).

| Cut-off | Sources in the app | Own sources (rows) | Merged (rows) |
|---|---|---|---|
| 5 | 128 | 98 (2,061) | 214 competitions (617) |
| 10 | 81 | 55 (1,779) | 257 (899) |
| **15 (chosen)** | **62** | **37 (1,565)** | 275 (1,113) |
| 20 | 49 | 27 (1,400) | 285 (1,278) |

Rule: a competition below the cut-off goes to its country group, with its full name at the head of the subsource. A country group still below it rolls up to its region, unless the region would hold only that one country. Mock, online, university, book and unidentified contests have their own groups. AIME and the Cambridge Tripos are bank sources already, so their rows go there whatever their count.

At cut-off 15 the groups are (problems imported):

| Group | Problems | Group | Problems |
|---|---|---|---|
| Math Olympiad Discord Server | 263 | Chinese Olympiads | 24 |
| Other European Olympiads | 197 | African Olympiads | 22 |
| Other Asian Olympiads | 96 | Australian Olympiads | 21 |
| Mock Olympiads | 69 | Dutch Olympiads | 19 |
| United States Competitions | 53 | Israeli Olympiads | 17 |
| New Zealand Olympiads | 50 | Unidentified Contests | 17 |
| British Olympiads | 39 | International Olympiads | 17 |
| Online Community Contests | 36 | Polish Olympiads | 16 |
| Latin American Olympiads | 31 | Taiwanese Olympiads | 16 |
| Problem Books and Journals | 30 | Thai Olympiads | 15 |
| Indian Olympiads | 29 | Italian Olympiads | 15 |
| Canadian Olympiads | 9 | University Mathematics Competitions | 9 |
| University Admission Exams | 3 | | |

The 37 own sources run from the International Mathematical Olympiad (465, Shortlist included) and BMO Round 1 (106) down to six at 15–16 problems, plus the 4 AIME and 2 Tripos rows filed under their bank sources; `thresholds.md` lists them all.

**Ambiguous acronyms, settled from the rows' own solution links:**

| Acronym | Reading |
|---|---|
| CMO | Canadian (cms.math.ca); "CMO, Pascal/Fermat" are the Waterloo CEMC contests |
| AMO | Australian |
| ASC | Australian Senior Contest |
| ICMC | Imperial–Cambridge (not the bank's Indiana source) |
| BMOSL | Balkan |
| RMO | Indian |
| CAPS | Czech-Austrian-Polish-Slovak Match (merged with its Czech-Polish-Slovak predecessor) |
| AFMO | the server's April Fools contest |
| CMC | Cyberspace Mathematical Competition (medium confidence) |
| CAMO | Christmas American MO (medium confidence) |
| F3 | UK–Australia pre-IMO camp exchange paper |
| ELMO | has no real expansion; drafted as "ELMO Mathematical Olympiad" |

**Low confidence:**
- Unknown acronyms: DGO, XOOK, AMM, IGMO, SEIF, GIMO, IMSC, FIST.
- "Leaked RMM" and "Real IMOSL" (probably jokes or mocks).
- "Maynooth".
- About 13 one-off contests.
- Loose labels: "Russia", "Iran", "Some Australian TST".
- AoPS blocks automated lookups, so several expansions are unverified.

**Skipped (23 rows; owner 2026-11-12):**
- Programming: Codeforces 10, Project Euler 2, USACO 2, IOI 1.
- School and entrance exams: one each of CIE 9709, HKDSE, a school exam, a SOF sample paper, Gaokao, Kyoto, University of Indonesia and Hanoi entrance.
- Kept: ISI 2 and STEP 1, as "University Admission Exams".

**Bank matches:**
- `AIME` (748 rows) renamed to "American Invitational Mathematics Examination" on import; POTD's 4 new AIME rows joined it (23 others were duplicates).
- Cambridge Tripos: POTD's 2 rows go under the bank's "Cambridge Tripos".
- Miklos Schweitzer and Kürschák: the same contests as the Szekely book and the Hungarian Problem Books, but other years; filed as POTD competitions.

**Duplicates (hand-reviewed 2026-11-12, `duplicates.csv`):** a local TF-IDF and word-trigram comparison of every POTD statement with the bank and with each other, then each candidate pair read. 72 rows are already in the bank: 23 AIME; Shortlist and TST problems in "Selection Tests in Number Theory" (23); IMO problems quoted in Mladenovic (15); Engel (8); Burton, Winkler and Grimmett (one each). 16 more were posted twice; the copy with more hints, answer or solution was kept. Restatements that change the problem (a different bound, an added condition, a two-part version) were kept.

## 5. Solving: published scores and model buckets

Published results, gathered 2026-11-11 by a research agent from the system cards and from MathArena, Epoch, Vals and Artificial Analysis. Not every number was re-checked.

- No math or science result at **medium** effort exists for Opus 5.5.
- **Answer-based contest math no longer separates models.** Opus 4.8 scored 100% on AIME 2026. Opus 5.5 at high effort scores about 83% on MathArena's research-level ArXivMath.
- **Written olympiad proofs:** no independent evaluation exists for any 5.x model. The only figure is Anthropic's own run of Opus 5 on IMO 2026 (42/42, graded by models). Opus 4.6 got 47% on USAMO 2026.
- **Fable 5.2 beats Opus 5.5 on science:** GPQA Diamond 94 vs 91; Humanity's Last Exam without tools 73 vs 64.
- **Tools** add 1–6 points at research level.
- **Not listed anywhere:** Omni-MATH, HARP, UGPhysics, OlympiadBench, IMO-Bench (for 5.x) and GATE.

**Preliminary buckets** (POTD counts from D):

| Model | Questions | POTD rows |
|---|---|---|
| Opus 5.5 medium | Routine or answer-checkable: POTD D 0–3; HARP 1–3; GATE, multiple-choice and NAT sets (checked against the key; disagreements go to the tie-break) | ~850 |
| Opus 5.5 high | Middle: POTD D 4–6; Omni-MATH ≤ 6; UGPhysics; MIT OCW sets | ~920 |
| Fable 5.2 high | Hard proofs: POTD D ≥ 7; Omni-MATH ≥ 7; IMO Shortlist | ~1,010 |

- **Whole-source rule:** sources made mostly of hard problems (IMO Shortlist, USA TST, Romanian Masters) go to the Fable bucket whatever a single problem's D.
- **The 12 rows with an invalid D** need a bucket by source.
- **Proof checking:** proofs are where outside evidence is thinnest, so a spot-check of the Fable bucket is the place to spend review effort.

## 6. Other sources

**Math, best fits:**
- **HARP** (github.com/aadityasingh/HARP, MIT): 5,409 AMC/AHSME/AIME/USA(J)MO problems, about 2.1 human solutions each, difficulty 1–6, subject labels. Drop its AIME rows; the bank has 1983–2024.
- **Omni-MATH** (HF `KbsdJames/Omni-MATH`, Apache-2.0): 4,428 olympiad problems with solutions, difficulty 1–9.5, 33 domains. Overlaps POTD and the Shortlists.
- **IMO Shortlists 2006–2025**: PDFs at `imo-official.org/assets/documents/problems/<year>/IMO<year>SL.pdf`, with official solutions and A/C/G/N labels. They give official solutions for POTD's 496 IMO/Shortlist rows and the rest of each list. Needs PDF → LaTeX.
- **IMO-Bench** (github google-deepmind/superhuman, `imobench/`, CC BY 4.0; use the `_v2` CSVs): AnswerBench 400, ProofBench 60 with grading guidelines.
- **Kedlaya's Putnam archive** (kskedlaya.org/putnam-archive): problems 1985–2025, solutions 1995–2025, in TeX. The authors ask that the solutions not be reproduced elsewhere: private DB only.
- **CHAMP** (github YilunZhou/champ-dataset): 330 hints and 54 concepts for 270 **Engel** problems already in the bank. It adds hints, not questions.
- **ProofNet** (HF `hoskinson-center/proofnet`, MIT): 371 undergraduate proofs.
- **U-MATH** (HF `toloka/u-math`, MIT): 1,100 calculus problems with solutions.
- **Now in scope, answer-only:**
  - MathArena (CC BY-NC-SA).
  - UGMathBench (GPL-3.0, 5,062 WeBWorK problems).
  - TheoremQA (MIT).
  - DeepMath-103K (MIT).
  - Big-Math.
  - NuminaMath-1.5, filtered (`AI-MO/NuminaMath-1.5`, its solutions are model-rewritten).
- **Skip:**
  - MATH: AoPS DMCA of 2025-01-02; the original HF copy is disabled.
  - Humanity's Last Exam and GPQA: terms against sharing examples, plus canary strings.
  - FrontierMath: private.
  - miniF2F and PutnamBench: formal statements only.

**Engineering, physics, chemistry:**
- **GATE EE/ME/XE/CH/MT** (gate2027.iitm.ac.in/download): papers 2007–2026 with official answer keys for 2021–2026. Multiple-choice, multi-select and numeric questions, with figures. The best fit for machines, power, thermodynamics, heat transfer, fluids, materials and energy. "All rights reserved": personal use.
- **UGPhysics** (HF `UGPhysics/ugphysics`, CC BY-NC-SA): 5,520 undergraduate problems with solutions, answers and units, all text. Translated from Chinese books.
- **MIT OCW** 6.061, 6.685, 3.091 and 16.01: problem sets with solutions, CC BY-NC-SA.
- **NPTEL assignments:** multiple-choice and numeric; solutions released after the deadlines.
- **OpenStax** University Physics 1–3 and Chemistry 2e: answers for odd-numbered problems. Check the licence (CC BY or BY-NC-SA, depending on edition).
- **ThermoQA** (HF `olivenet/thermoqa`, CC BY 4.0): 293 steam-table and cycle problems.
- **Also:**
  - EEE-Bench: every problem needs its image; 72% multiple choice.
  - MaScQA: 650 GATE-level materials questions, CC BY-NC-SA.
  - MatSciBench: licence unknown.
  - SuperGPQA: multiple choice, ODC-BY, about 7,900 engineering questions.
  - MMLU-Pro, JEEBench.

**Copyright:** keep everything in the private DB. No raw downloads, review pages or canary-string rows in the public repo. Don't scrape AoPS (it blocks automated access and asserted copyright in the MATH notice).

## 7. POTD import

**Done 2026-11-12 (steps 1–2):**
- Downloaded the POTD tab at 13:21 (2,792 rows with a statement) into the session scratchpad; `build_map.py <csv> sources/potd 15 2026-11-12`.
- `import_mods_potd.py --rename-aime --apply`, then `--csv <csv> --apply`. Backups: `app/data/appdata/amplify.db.bak-20261112-134845-rename-aime` and `…-134855-mods-potd`.
- **Added 2,678 questions** (question_id 25,550–28,227; bank total 27,874), 62 sources: 1,723 with hints (1,389 with two or three tiers), 618 answers, 376 solutions. POTD number, date and Solution Link per question in `app/data/appdata/mods_potd_map.csv`.
- **Checks before writing:**
  - 0 problems from the tool's own checks (braces, `$` and `\(`/`\[` pairs, environments, leftover macros);
  - every field rendered with the app's `renderLatex`: 0 KaTeX errors in 7,695 fields;
  - every statement, solution and answer compiled in one XeLaTeX document with the app's preamble: 0 errors.
  - 56 fixes in 44 rows (`mods_potd_fixes.json`): 47 LaTeX (missing `$`, braces, a cut-off hint completed, a wrong factorisation in a human solution, 2227), 6 Discord leftovers (a user mention, bot commands, a solver's name, asterisks eaten by italics), 2 rewordings for profanity, 1 spelling. General repairs (the bot's macros, enumerate labels, URLs, bare-math answers) are listed in the tool's docstring.
- Not imported: Discussion, Message ID, Curator and the solver columns; the Curators tab.
- **Solutions cleaned the same day** (`--update-solutions`, backups `…-141037-` and `…-143154-mods-potd-solutions`):
  - 20 Solution cells held only a URL. They became the solution link.
  - 8 were no solution: jokes, fragments, a comment, a page pointer, and one wrong proof (26666, which ends on the wrong circle). They were dropped with "drop" fixes.
  - 348 human solutions remain. The run_sub solve pass skips questions that have a solution, so these 28 now get solved.

**Classified 2026-11-12** (`taxonomy/full_run_20261112_potd/`, REPORT.md; backup `amplify.db.bak-20261112-143056-pre-classify-potd`):
- Method: the 11-02 pipeline for olympiad sources.
  - Sonnet first pass with the olympiad tag file.
  - Blind second opinions: Haiku on 1,777 medium/low labels, Sonnet on 51 wastebasket/other-subject labels.
  - Opus adjudicated the 827 disagreements (A/B order random).
- Candidate subjects came from the curators' genre letters, and their genre and sub-tag went in as a hint. Where there was no solution, the classifier saw the sheet's hints. Run scripts are in this session's scratchpad `cls_potd/`.
- Results:
  - **2,675 placed**: Combinatorics 801, Geometry 688, Number Theory 654, Algebra 493, Probability 17, Calculus 12, Abstract Algebra 6, Linear Algebra and Differential Equations 3, Thermodynamics 1 (a heat-exchange puzzle).
  - 3 left in the wastebasket (`wastebasket.csv`).
  - Every row got a type (proof 1,621, numerical 1,052) and 6,107 tag rows: 3,467 key, 1,004 supporting, 1,636 task.
  - How the final label was reached: 850 high on the first pass, 989 agreed by the second opinion, 12 second opinions accepted, 827 by Opus (452 for the first label, 310 for the second, 65 neither).
- **Proposed tags added** (owner, 2026-11-12):
  - Defined in `taxonomy/tags_draft.md`: Inversion, Projective Methods (the proposals' harmonic division, cross-ratio and poles-and-polars variants folded in), Linear Algebra Method, Quadratic Residues.
  - As on 11-06, they were put only on the 59 proposing questions: 56 as key tags, 3 as supporting where the question already had two key tags. The list is `taxonomy/full_run_20261112_potd/new_tags.csv`; backup `…-153502-pre-potd-tags`.

**Solve run started 2026-11-12** (owner: "go ahead with the solve run"):
- Assignments: `pipeline/potd_assignments.json`, built by `sources/potd/scripts/assign_models.py`, in run_sub.py's new `subscription.assignments_file`. Each question has its own model and effort.
- Buckets for the 2,330 questions without a solution:
  - Opus 5.5 medium: 618 (D 0–3).
  - Opus 5.5 high: 595 (D 4–6).
  - Fable 5.2 high: 1,117. That is D 7+ plus the whole of the 16 hard-heavy sources, those with a median D of 7 or more: the TSTs, the IMO Shortlist, RMM, USAMO, ELMO and its Shortlist, the Balkan Shortlist, USEMO, the mock olympiads, and others.
- Pilot of 6, two per bucket, judged locally: 5 passed, and 1 Fable reply went to retry for a LaTeX slip in its answer. Output size: Opus about 2–5k tokens per reply, Fable 40–48k.
- The full run is `run_sub.py solve --wait-on-limit` (12 workers, log `pipeline/run_sub_potd.log`). Judging goes to the remote machine via `remote_judge.py`.

**Remaining steps** (each needs the owner's go-ahead):

1. **Download** a fresh CSV of the POTD tab, plus Weekly if wanted, into a new folder outside the repo. Rebuild `sources/potd` with `build_map.py`. *(done; a later re-run with a new download adds only the new days, since the import is idempotent on `latex_hash`)*
2. **Import tool** `app/tools/import_mods_potd.py`, in the style of `import_sahoo.py`: back up the DB first, idempotent on `latex_hash`, rows go in Uncategorized. *(done)*
   - **Field mapping:**

     | POTD column | Bank field |
     |---|---|
     | Problem Statement | `latexcode` |
     | Hint 1 | `hints` |
     | Hint 2, Hint 3 | `more_hints` (JSON list; NULL when there is only one hint) |
     | Answer | `answer` (placeholders dropped; bare math gets `$…$`) |
     | Solution | `solution` |
     | Source | source and subsource from `row_assignments.csv` at the chosen cut-off |
     | POTD number, Date, Solution Link | `app/data/appdata/mods_potd_map.csv` (by question_id) |

   - **Not stored:** D, G and T. They feed classification and bucketing; read them from the sheet by POTD number.
   - **Left out:** the 23 skip rows, the 88 duplicates, and the 3 rows dated after the download.
3. **Check for duplicates** against the bank with embeddings after `reembed.py` (the local text check is done; embeddings would catch reworded copies). That uses the API, so quote the cost first.
4. **Classify** with the taxonomy pipeline on the subscription, with G/T as priors:
   - A → Algebra;
   - C → Combinatorics;
   - G → Geometry;
   - N → Number Theory;
   - CG → Combinatorics, combinatorial geometry.
5. **Solutions:**
   - Keep the sheet's 376 (imported as `solution`).
   - Import the official Shortlist solutions for the 465 IMO rows (Shortlist included).
   - Solve the rest by bucket (section 5) with `run_sub.py`.
   - Hints: POTD's human hints stay (the pipeline never overwrites a source's hints). The 955 questions without hints get generated tiers (prompt v7).
6. **Judge** (remote job, or locally if 20 or fewer), import, re-embed.

## 8. App and pipeline state relevant to imports

- **Multi-select** already works. In `answer_key` a `choice` part whose `value` is a list is multi-select: toggle buttons, "select every correct option", all-or-nothing, no negative marking. 747 questions use it. Imports write the key as a list of letters, even for a multi-select question with one correct option.
- **Tiered hints, built 2026-11-11, committed (a1f4456); the tier-count rule is prompt v7/s6 (e9777fc):**
  - **App:**
    - Migration `012_more_hints.sql` (`questions.more_hints`).
    - `hint_tiers()` in `app/core/models.py`, mirrored by `hintTiers()` in `frontend/src/lib/ipc.ts`.
    - `quiz_request_hint(..., tier)`.
    - QuestionViewer's progressive button, `hintLevel` in the quiz store, and `hints_used` = tiers opened.
    - The Browser lists all tiers.
    - Tests: `tests/test_tiered_hints.py`, `frontend/src/lib/__tests__/hintTiers.test.ts`, plus new cases in `safeguards.test.tsx`. 374 backend and 324 frontend tests pass.
  - **Pipeline:**
    - Prompts: math v5 → v6 and subjects s4 → s5, with `%%% BEGIN HINT 1..3` blocks; the model picks 1–3 tiers. Old single-HINT replies parse as one tier.
    - Tier 1 → `hints`; tiers 2–3 → provenance field `more_hints` (`finals.more_hints_tex`).
  - **`run_sub.py`'s request check was loosened:** it now compares the system prompt only with API batches of the same prompt version. v6 has none, so the "no drift" check passes trivially. Flagged to the owner.
  - **Before the next solve run:** run a small pilot to see how many tiers the models write. (The 2026-11-12 re-check gave 89 three-tier and 42 two-tier hints among 131 tie-breaks.)

## 9. Checker problems found 2026-11-12, fixed the same day

**Fixed (2026-11-12, `subjects.py`; rules in `pipeline/README.md` under "Non-math subjects";
tests in `tests/test_answer_checker.py`):**
- the judge's own tolerance (3%, or the book's printed rounding up to 5%), not the solver's TOL;
- every value compared even when the part counts differ;
- unit factors only between different units;
- conversions for hp, kgf, kcal and atm, and kelvin vs °C;
- subscripts and unit powers no longer read as values;
- products, complex numbers, ranges, time functions and tables not compared.

**Re-check of every accepted subject reply** (`pipeline/scripts/recheck_answers.py`, read-only):
- 1,461 agree with the book;
- **166 now disagree:** 34 within 6%, 47 at 6–20%, 85 over 20%. Many are book typos, question misprints or factor-of-10 errors that the old blind unit factors hid;
- 172 tie-break replacements still hold, 1 no longer does (5886);
- 12 were replaced by a review solve (6732 among them, so its copied book answer is already gone).

**Settled the same day:** all 167 went through the high-effort pipeline (tie-breaks, then Fable reviews of the splits). 150 book answers were replaced (the old values kept in provenance as `answer_before_replace`), 17 stand, and `recheck_answers.py` shows 0 mismatches.

What the audit found before the fix:

Two detailed checks of solve-mode questions where the generated answer disagreed with the stored answer: the 16 tie-breaks that kept the book's answer, and the 33 retries that "matched".
- **Code execution would not have helped:** 0 of 65 wrong first answers were arithmetic slips and 1 was a misremembered constant. The rest were modelling or convention choices, book errors, misprints, or checker artefacts.
- **The checker problems:**
  - The solver sets its own tolerance, up to 20%, and the checker accepts it. 6 retries matched only this way, and so did some tie-breaks (5041, 21572, 21573, 21537).
  - The comparison is skipped when the part counts differ: 6 more "matches".
  - It has no nm ↔ Å factor.
  - Its per-minute factor produced a false match (21603: 13.4 × 60 ≈ 842).
- **6732** (boiler efficiency) holds the book's wrong values, copied by a retry run before the 2026-11-07 fix to the retry wording. It needs a re-solve.
- **The 180 tie-breaks that replaced the book's answer were never audited.** Some may be convention differences rather than book errors.
- **Proposed next steps:**
  - a tolerance the judge sets, not the solver;
  - part-by-part comparison, or a flag, when the counts differ;
  - fixed unit factors;
  - re-check all passed replies with the new rules (pure Python, no API or XeLaTeX) and send the real mismatches to the Fable review pass;
  - prompt the solvers to follow the book's conventions.

## 10. Open decisions

Settled 2026-11-12: cut-off 15; STEP and ISI kept, the rest of the skip rows skipped; AIME renamed; the Shortlist filed with the IMO; tiered hints committed. Defaults taken without asking, open to change: the Discord server's own contests under "Math Olympiad Discord Server" (the contest heads the subsource), and the POTD number and Solution Link in the git-ignored map file.

Still open:
1. **Next POTD steps** (classification done 2026-11-12):
   - the embedding duplicate check (API, cost to quote);
   - the solve run by bucket (subscription);
   - judging (remote job).
   - Also: the proposed tags (Inversion, projective methods, Linear Algebra Method, Quadratic Residues), and the 3 wastebasket questions.
2. Weekly tab (76 multi-part problems): import or not.
3. Which other sources to import, and in what order. Suggested: IMO Shortlist PDFs (official solutions for the 465 IMO rows) → HARP → GATE EE/ME → UGPhysics → CHAMP hints → Omni-MATH.
4. ~~Copy POTD's hints, answers and solutions into the 72 bank duplicates where the bank has none~~ (owner: yes, 2026-11-12). Nothing to copy: all 72 bank rows already have hints, a solution and a generated solution, and the one missing answer (bank 8674, a proof problem) matches POTD's joke placeholder. The bank's hints there are single pipeline tiers; replacing them with POTD's human tiers would be a separate decision.

## 11. Standing rules that apply

- Extraction, API submissions, judging and DB writes each need the owner's approval. Quote costs against the $100 API credit (embeddings use the API). Solving runs on the subscription.
- Judging of more than 20 replies goes to the owner's 64-core machine through `remote_judge.py` (encrypted jobs). 20 or fewer can be judged here at below-normal priority.
- Every import backs up the DB first. Check free space on C: before long runs; ask before pruning backups.
- Import only from the files the owner gives; never search the disk for other copies of a book.
- For OCR imports, check every item against the source PDF, not just the structure.
