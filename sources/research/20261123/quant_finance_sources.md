# Quant-finance question sources for Amplify: requirements, gaps, candidates

Survey date 2026-11-23. Research only: nothing was imported and no project file was changed. Bank counts below come from a read-only query of `app/data/appdata/amplify.db` (46,923 questions). Small sample files (SOA PDFs, G-Research PDFs) were fetched into the scratchpad only to read them.

---

## 0. Summary

**What quant interviews test.** Trader interviews weight probability and expected value, mental arithmetic, market-making and betting games, options intuition and some game theory. Researcher interviews add statistics (OLS and regression assumptions, time series), linear algebra, calculus and differential equations, ML basics and stochastic calculus. Developer interviews are mostly coding (excluded from the bank) plus probability and brainteasers.

**What the bank already covers well.** Probability puzzles, conditional probability and Bayes, combinatorics, martingales, random walks, Markov chains, Brownian motion and Itô calculus, basic derivatives pricing. These are all well stocked. Zhou's Green Book (113), Stefanica's 150 Questions (155), OpenQuant (167), Joshi's *Concepts and Practice* (192), Wilmott (115), Mosteller (51), Winkler and Grimmett-Stirzaker are already in.

**Where the bank is thin.**

- Market making, betting and Kelly: 0 rows.
- Mental arithmetic: 0 rows.
- Fermi estimation: 5 rows.
- Greeks and hedging: 48 rows.
- Volatility modelling: 25 rows.
- Fixed income beyond compounding: 76 rows outside the 268 compounding rows.
- Portfolio and risk: 98 rows in total (CAPM 6, VaR 6, no factor models).
- Time series and econometrics: about 40 rows.
- Regression: 93 rows.
- ML basics: essentially none.
- Game theory (auctions, Nash, bidding): almost none.

**Import first** (detail and yields in section 5):

1. SOA derivatives and investments sample sets (MFE intro and advanced, IFM).
2. QuantQA.
3. SOA SRM.
4. XFinBench, Hull-derived subset.
5. SOA FM, fixed-income subset.
6. Quantitative Primer.
7. FinanceMath.
8. MMLU econometrics.

No good open source exists for **market making or mental arithmetic**. Build both as generated drills (section 5.3).

**Avoid:**

- VedantPadwal/quantitative-finance-reasoning: verbatim copy of Joshi's *Quant Job Interview Questions and Answers*, with no licence.
- CFA-derived sets: TheFinAI/en-cfa, flare-cfa, CFA-Level-III and BizBench FinKnow.
- FinEval (Chinese text, NC licence, hidden test labels).
- FinanceBench (NC licence, document retrieval).
- FAMMA (screenshots, multilingual).
- MorbidCorp actuarial sets (synthetic and unverified).
- FinQA, ConvFinQA and TAT-QA: table QA over financial statements, not quant-interview material.
- Scraping QuantGuide, Glassdoor, Brainstellar or the Jane Street and Riddler archives.

---

## 1. What quant interviews and quant-job prep require

### 1.1 Evidence

| Source | What it says |
|---|---|
| Jane Street, *Probability & Markets* (official interview primer, PDF linked from https://www.janestreet.com/probability-markets/) | Contents: Randomness, Counting, Probabilities, Independence, Random Variables, Expected Value, Confidence Intervals, Conditional Probability, **Making Markets, Adverse Selection**, Problem Solving Tools, Interview Thoughts. On mental maths: "Numeracy certainly helps ... At the same time, we're not going to judge you harshly for not being able to mentally multiply double-digit numbers in 5 seconds." It also says the firm prefers "the simple, intuitive answer". |
| Optiver US campus FAQ (https://optiver.com/working-at-optiver/career-hub/us-campus-recruiting-faqs-2/) | "Being good at mental math is necessary, but not sufficient, to thrive as a Trader at Optiver." The FAQ suggests practising quick problem-solving such as mental maths and strategy games. Candidate reports describe timed numeric tests (for example 80 questions in 8 minutes). These reports are anecdotal. |
| G-Research, *Quantitative Researcher Assessment Process Guidance* (https://www.gresearch.com/wp-content/uploads/2020/08/200630-quant-research-preparation.pdf) | "Key topics include probability, statistics (inc. OLS), linear algebra, calculus (esp. differential equations), programming and finance." Of the technical interviews, "One of these will be Maths; two will be drawn from Stats, Finance, Programming and ML." The firm says "We do not assume a detailed knowledge of finance." It recommends Stefanica, Radoicic and Wang, and *The Elements of Statistical Learning* for the ML quiz. |
| G-Research *Sample Quant Exam* (https://www.gresearch.com/wp-content/uploads/2019/12/Sample-Quant-Exa.pdf, © 2017) | 11 questions: the slope of the reverse regression, the boy-born-on-Tuesday problem, stock beta and idiosyncratic volatility leading to a closing-price probability, the longest piece of a broken stick, the delta of an ATM binary option near expiry, a Fermi estimate (the Moon falling to Earth versus solar power), a digit-product sum, an expected number of random draws, domino tilings, gambler's ruin with +2/-1 steps, and the smallest-unique-number game (game theory). |
| Baruch MFE admissions (https://mfe.baruch.cuny.edu/application-process/, via search snapshot) | Prerequisites: calculus, probability, linear algebra, C++ and finance. The admissions test covers "Calculus, Linear Algebra, Probability, Finance, Brainteasers": 8 questions in 45 minutes, with integer answers. Interviews are "primarily technical" (mathematics, finance and C++). |
| Zhou, *A Practical Guide to Quantitative Finance Interviews* (contents page) | Chapters: General Principles; Brain Teasers; Calculus and Linear Algebra; Probability Theory; Stochastic Process and Stochastic Calculus; Finance (option pricing, Greeks, exotics, portfolio); Algorithms and Numerical Methods. More than 200 problems. 113 are in the bank. |
| Crack, *Heard on the Street* (publisher blurb, e.g. https://www.powells.com/book/heard-on-the-street-9780970055262) | More than 175 quantitative questions from real interviews, covering "pure quant/logic, financial economics, derivatives, and statistics", plus more than 125 non-quantitative questions. |
| Joshi, Denson and Downes, *Quant Job Interview Questions and Answers* (2nd ed.) | Chapters on option pricing, probability, interest rates, numerical techniques, mathematics, coding and logic/brainteasers. About 300 questions with answers. |
| Stefanica, Radoicic and Wang, *150 Most Frequently Asked Questions on Quant Interviews* (QuantNet and Goodreads listings) | Mathematics, calculus, differential equations, covariance and correlation matrices, probability, stochastic calculus, finance, numerical methods and brainteasers. Already in the bank (155 rows). |

### 1.2 Requirements by role

| Area | Trader | Researcher | Developer | Main evidence |
|---|---|---|---|---|
| Probability and expected-value puzzles, conditional probability and Bayes, combinatorics | core | core | common | Jane Street, G-Research, Zhou, Crack, Baruch |
| Martingales, stopping, random walks, Markov chains | common | common | some | Zhou ch. 5, G-Research sample Q10 |
| Stochastic calculus (Brownian motion, Itô, SDEs) | some | core for derivatives roles | rare | Zhou ch. 5, Joshi, Stefanica |
| Option pricing intuition, Greeks, put-call parity, no-arbitrage | core | common | some | Crack, Joshi, Zhou ch. 6, G-Research Q5 |
| **Market making, bid/ask, adverse selection, betting, Kelly** | **core** | some | rare | Jane Street guide; prep-site reports of trading games |
| **Mental arithmetic and estimation** | **core** (timed tests) | some | some | Optiver FAQ, Jane Street myths section, G-Research Q6 |
| **Statistics, regression (OLS), time series, econometrics** | some | **core** | some | G-Research ("statistics (inc. OLS)"), G-Research Q1 and Q3, Crack |
| Linear algebra, calculus, differential equations, optimisation | some | core | some | G-Research, Baruch, Zhou ch. 3 |
| Portfolio theory and risk (CAPM, VaR, factor models) | some | common | rare | Crack (financial economics), Zhou ch. 6 |
| Fixed income basics (yields, duration, swaps) | some | some | rare | Joshi (interest rates), Crack |
| **ML basics** (bias-variance, regularisation, trees, PCA, clustering) | rare | **core** at ML-heavy funds | some | G-Research (ML interviews, ESL) |
| **Game theory** (auctions, Nash, bidding) | common at options and market-making firms | some | rare | G-Research Q11, Crack |
| Coding | some | common | core | excluded from the bank by design |

---

## 2. Gap analysis against the bank

Counts are question rows per taxonomy topic and subtopic.

| Area | Bank coverage | Verdict |
|---|---|---|
| Probability puzzles, EV, Bayes, combinatorics | Probability 4,411 (Bayes 147, expected value 249, fair games 64, optimal stopping 39); Enumerative Combinatorics 1,621; interview books Zhou 113, Stefanica 150Q 155, OpenQuant 167 | **Strong.** Only more interview flavour is worth adding. |
| Martingales, random walks, Markov chains | Martingales 134; Random Walks 168; DTMC 313; CTMC 108 | Adequate |
| Stochastic calculus and Brownian motion | Stochastic Calculus 119; Brownian and diffusions 131 | Adequate, mostly Oksendal-style proofs. Interview-style short Itô questions are fewer. |
| Derivatives pricing | 427 (Joshi 149, Wilmott 69, Stefanica 65) | Core is adequate. **Thin:** Greeks 30, delta hedging 11, gamma and vega hedging 7, volatility modelling 25, numerical methods 25. |
| Fixed income | 344, of which 268 are compounding and present value (256 from UGMathBench) | **Thin:** duration and convexity 14, bootstrapping 14, yield 11, forwards 6, swaps 7, short-rate models 5 |
| Portfolio theory and risk | 98 in total: efficient frontier 20, CAPM 6, VaR 6, credit risk 9, utility 39 | **Thin.** No factor models, Sharpe ratio, Kelly or performance attribution. |
| Statistics: regression and time series | Mathematical Statistics 744; Linear Models 93; ARMA 6, stationarity 22, linear prediction 6, spectral 12 | **Thin** on applied regression (diagnostics, R², multicollinearity), GARCH, unit roots and cointegration |
| ML basics | Effectively none. *Mathematics for Machine Learning* has 63 rows, mostly linear algebra and calculus. | **Gap** |
| Market making, trading games, betting, Kelly | 0 | **Gap** |
| Mental arithmetic | 0 | **Gap.** Better served by generated drills. |
| Fermi estimation | 5 (Brainteasers > Fermi Estimation) | **Gap** |
| Game theory | Microeconomics 15; Two-Player Games 192 (olympiad combinatorial games, not economic game theory) | **Thin** |
| Linear algebra and optimisation | Linear Algebra 2,063; optimisation has no dedicated topic | Linear algebra is fine; optimisation is modest. |
| Brainteasers and logic | Logic and Algorithmic Puzzles 381; Brainteasers 34 | Adequate |

---

## 3. Candidate table

Abbreviations:

- **Sol.**: worked solutions.
- **Ans.**: final answers only.
- **Img/Tab**: share of items needing images or tables.
- **NC**: non-commercial licence.
- **ARR**: all rights reserved, or no licence stated.

### 3.1 Datasets (Hugging Face and GitHub)

| # | Name | Access | Maintainer | License | Relevant Qs | Level | Topics | Format | Ans/Sol | Img/Tab | Text | Overlap with bank | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 | **QuantQA** | HF `ReinforceNow/quantqa`; same author's repo `Guido1Alessandro1Trevisan/coach-quant` | Guido Trevisan (CoachQuant, UChicago students) with ReinforceNow | MIT (claimed); **provenance flag** | 519 | interview, easy 43 / medium 348 / hard 128 | probability 349, combinatorics 114, EV 109, brainteasers 76, conditional probability 75, games and game theory 34, statistics 19, finance 18, regression 10, Markov 5 | numeric short answer | Ans. only (hints and solutions are on coachquant.com) | ~0% | inline `$...$` LaTeX in 73% | Textual overlap low: 24/519 at Jaccard ≥0.35. Many classic puzzles reworded. | **Take** (rank 2) |
| D2 | academicquant quant-interview-questions | HF `academicquant/quant-interview-questions` | "academicquant"; links go to geodesicpartners.co.uk | CC BY 4.0 | 241 | easy to hard | probability 104, brainteasers 93, **EV and market making 31**, stats and ML 11, mental arithmetic 2 | numeric (10 dp) | Ans. only; solution links point to a commercial site | 0% | plain | 50/241 similar to the bank; heavy conceptual overlap (Winkler, Zhou classics) | Take the subset (~40) |
| D3 | **XFinBench** | HF `Zhihan/XFinBench`; GitHub `Zhihan72/XFinBench` (CSV) | Zhang et al. (ACL Findings 2025) | MIT; **derived from textbooks** | 4,235: bool 1,795, MCQ 761, calc 1,679 | graduate | GPT-4o rewrites of end-of-chapter questions from **Hull OFOD**, Ross *Corporate Finance* and Mishkin *Money & Banking*: binomial trees, Greeks, swaps, FRAs, CDOs, vol, annuities, banking | bool / MCQ / numeric | Ans. only, plus a 3,032-term knowledge bank | 146 with figures (3.4%) | LaTeX `\(..\)` | Low; Hull is not in the bank | **Take** the calc+MCQ Hull subset (rank 4) |
| D4 | **FinanceMath** | GitHub `yale-nlp/FinanceMath` (raw JSON open; HF copy gated "auto") | Yale NLP (Zhao et al., ACL 2024) | MIT; CFA-style content | 1,200 (test answers released Jul 2026) | professional (CFA-like) | derivatives 366, quant analysis and valuation 241, accounting 258, markets and economics 133, portfolio 91, risk 65, corporate 46 (keyword hits: bond 214, duration 56, forwards 55, binomial 20, VaR 23) | numeric (3 dp) | Ans. + executable Python solution | 40% have small markdown tables (not financial statements) | plain | Low | Take ~600-900 non-accounting (rank 7) |
| D5 | FinanceReasoning | HF `BUPT-Reasoning-Lab/FinanceReasoning` | BUPT | CC BY 4.0 | 2,238 (easy 1,000 / medium 1,000 / hard 238) | mixed | remix of FinanceMath, BizBench CodeTAT-QA/CodeFinQA and Investopedia-article generated items | numeric | Ans. + Python | ~25% tables | plain | **Heavy overlap with D4** | Skip; take D4 directly |
| D6 | BizBench | HF `kensho/bizbench` | Kensho (S&P) | Apache-2.0 | 19,050 (SEC-NUM 8,846, CodeFinQA 5,463, CodeTAT-QA 3,144, FinKnow 744, ConvFinQA 629, FinCode 54, FormulaEval 50, TAT-QA 120) | professional | financial-statement QA; FinKnow is CFA L1-style 3-option MCQ; FinCode is CFA/CPA numeric | mixed | Ans. + programs | ~85% tables or code | plain | Low | Avoid: table/code-heavy, FinKnow is CFA-derived |
| D7 | FinQA / ConvFinQA / TAT-QA | GitHub `czyssrs/FinQA`, `czyssrs/ConvFinQA`; HF `next-tat/TAT-QA` | IBM / UCSB; NUS NExT | MIT / MIT / CC BY 4.0 | 8,281 / 3,892 conversations (~14k turns) / 16,552 | professional | ratios and changes read off S&P 500 earnings-report tables | numeric | Ans. + DSL programs | ~100% table plus text | plain | none | Avoid for quant prep |
| D8 | FinanceBench | HF `PatronusAI/financebench` | Patronus AI | **CC BY-NC 4.0** | 150 open (of 10,231) | professional | 10-K/10-Q document QA | short answer | Ans. + evidence | needs PDFs | plain | none | Avoid |
| D9 | FinEval | HF `SUFE-AIFLM-Lab/FinEval` | SUFE | **CC BY-NC-SA 4.0** | 4,661 | professional | finance, economics, accounting, certificates (Chinese) | MCQ | val labels only; **test labels hidden** | low | Chinese | n/a | Avoid |
| D10 | CFA-derived sets | HF `TheFinAI/en-cfa` (gated, licence "other"), `ChanceFocus/flare-cfa`, `ZixuanKe/CFA-Level-III` | various | CFA Institute content | ~1-2k | professional | CFA curriculum | MCQ / essay | varies | some | plain | n/a | **Avoid** (copyright) |
| D11 | **MMLU econometrics** | HF `cais/mmlu` config `econometrics` | Hendrycks et al. | MIT (items resemble Brooks' *Introductory Econometrics for Finance* question bank) | 131 (test 114, val 12, dev 5); 85 also in MMLU-Pro with 10 options | undergrad/MSc | ARMA identification, pacf, unit roots, GARCH, CLRM violations, bootstrapping, forecasting | MCQ (4) | Ans. only | 0% | plain | none | **Take** (rank 8) |
| D12 | MMLU-Pro business and economics | HF `TIGER-Lab/MMLU-Pro` | TIGER-Lab | MIT | business 789 (560 from STEMEZ / REA *Problem Solver* books), economics 844 | intro | business arithmetic (discounts, payroll, depreciation), micro/macro | MCQ (10) | Ans. (+ CoT) | 0% | plain | overlaps TheoremQA | Skip |
| D13 | AllenAI Fermi problems (RealFP) | GitHub `allenai/fermi` | Allen AI (Kalyan et al. 2021) | **no licence file** | 928 real (557 test, 371 train+val) + 10,000 synthetic | mixed | Fermi estimation (physics-flavoured, some general) | numeric with units, graded by order of magnitude | Ans. + decomposition "program" with facts | 0% | plain | none | Optional; take ~150 hand-picked if the licence is OK |
| D14 | FAMMA | HF `weaverbirdllm/famma` | famma-bench | Apache-2.0 | 1,945 + 103 | university / professional | 8 finance subfields | MCQ / open | Ans. + explanations | **every item has screenshot images**; OCR'd `_txt` variant | en/zh/fr | n/a | Avoid |
| D15 | Quantitative Finance Reasoning | HF `VedantPadwal/quantitative-finance-reasoning` | individual | **none**; content copied from Joshi QJIQ (ids `QNT_Question_2.1` and the book's answer text) | 128 | interview | option pricing, probability | open | book answer + Gemini trace | 0% | LaTeX | would duplicate the book | **Avoid** (pirated) |
| D16 | Synthetic actuarial sets | HF `MorbidCorp/actuarial-fm-p-ifm-*` | MorbidCorp | Apache-2.0 | 1,708 | exam prep | FM/P/IFM | Q&A | LLM-written | 0% | plain | n/a | Avoid (unverified synthetic) |
| D17 | FinChain | GitHub `mbzuai-nlp/finchain` | MBZUAI | Apache-2.0 | 58 topics × 5 templates (generator) | intro / professional | corporate finance, ratios, bond and option pricing, VaR, crypto, regulation | numeric | generated with code-traced steps | 0% | plain | none | Ideas only |
| D18 | TheoremQA (finance part) | HF `TIGER-Lab/TheoremQA` | TIGER-Lab | MIT | ~58 finance | undergrad | mixed | numeric | Ans. | some | LaTeX | **already imported** | Done |

### 3.2 Exam bodies, firms and courses

| # | Name | Access | Maintainer | License | Relevant Qs | Level | Topics | Format | Ans/Sol | Img/Tab | Text | Overlap with bank | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | **SOA Exam MFE sample Q&S: Introductory Derivatives (MFE-02-17) + Advanced Derivatives (MFE-03-17)** | soa.org PDFs: `globalassets/assets/Files/Edu/2017/mfe-sample-solutions-intro-derivatives.pdf` (+ questions PDF), `.../2017/mfe-sample-questions-solutions-adv-derivatives.pdf` | Society of Actuaries | © SOA, free download, no reuse licence (same terms as the Exam P set already in the bank) | ~113 (intro 75 numbered, 2 deleted; advanced ~40 unique) | advanced undergrad | forwards and futures, put-call parity, spreads and collars, binomial trees, Black-Scholes, **Greeks, delta-gamma hedging**, exchange, barrier, gap, chooser and Asian options, lognormal model, Monte Carlo, **Black-Derman-Toy** | MCQ (5) | **Ans. + Sol.** | <5% tables | PDF text with formulas, needs LaTeX conversion | low | **Take** (rank 1) |
| E2 | **SOA Exam IFM sample Q&S: Finance and Investment (IFM-02-18)** | soa.org `globalassets/assets/Files/Edu/2018/2018-exam-ifm-sample-questions.pdf` | SOA | © SOA (exam retired Nov 2022) | 44 | advanced undergrad | CAPM and beta, portfolio and Sharpe, efficient markets and anomalies, behavioural finance, **VaR and TVaR**, capital budgeting and NPV, capital structure, real options | MCQ (5) | **Ans. + Sol.** | ~10% tables | PDF | low | **Take** (rank 1, with E1) |
| E3 | **SOA Exam SRM sample Q&S** | soa.org `globalassets/assets/Files/Edu/2018/exam-srm-sample-questions.pdf` (updated Oct 2026) | SOA | © SOA | 76 | advanced undergrad | linear models (t/F tests, AIC/BIC, ridge/lasso, kNN), GLMs, **time series** (random walk, AR, exponential smoothing, ARCH), **decision trees**, **PCA, k-means and hierarchical clustering**, bias-variance, cross-validation | MCQ (5) | **Ans. + Sol.** | ~25% small data or output tables | PDF | none | **Take** (rank 3) |
| E4 | **SOA Exam FM sample Q&S** | soa.org `globalassets/assets/files/edu/2018/2018-10-exam-fm-sample-questions.pdf` + `-solutions.pdf` | SOA | © SOA | 459 (462 numbered, 3 deleted). Keyword counts: bonds 155, yield/IRR 94, loans 92, annuities 91, **duration 64, immunization and matching 47**, convexity 10, spot/forward 12 | undergrad | interest theory, bonds, yield curves, duration and convexity, Redington and full immunization | MCQ (5) | **Ans. + Sol.** | low | PDF, actuarial notation (ä, s-angle) | partial with the 268 compounding rows | **Take** the fixed-income subset, ~250 (rank 5) |
| E5 | SOA INV 201 curated past QFI QF exam items | soa.org `globalassets/assets/files/edu/2026/fall/questions/2026-9-inv-201-questions.pdf` (solutions and Excel in separate files) | SOA | © SOA | 50 multi-part (QFI QF 2020-2024) | graduate / FSA | stochastic calculus, martingales, Black-Scholes, Greeks, vol smile, Vasicek, swaps and FRAs, arbitrage | written, multi-part; some parts need Excel | Sol. (separate PDF) | ~30% tables | PDF | low | Later; good for hard derivatives |
| E6 | **Quantitative Primer** (Dirk Bester) | GitHub `dwcoder/QuantitativePrimer` (LaTeX source + PDF) | Dirk Bester | **CC BY-SA 4.0** | ~47 questions; ~40 after dropping C++/SQL/array coding | interview | Bayes, bivariate normal maximum, **AR(1) mean and variance, regression theory (OLS, logistic)**, stick breaking, drop-20-cards, betting on a 1-to-10 adding game | open / short answer | **Ans. + full worked solutions** | ~5% | **LaTeX** | low | **Take** (rank 6) |
| E7 | MIT OCW finance: 15.401 F2008, 15.433 S2003, 15.450 F2010, 18.S096 F2013 | ocw.mit.edu | MIT | **CC BY-NC-SA 4.0** | ~150 problems in total | MBA / MSc | 15.401: PV, fixed income, equities, CAPM, options (3 psets and 2 sample exams, all with solutions). 15.433: capital market theory, futures, attribution (3 of 5 assignments plus quizzes and exams with solutions). 15.450: econometrics, dynamic programming, Monte Carlo, Itô (6 psets without solutions; practice problems with solutions). 18.S096: linear algebra, **regression, time series, volatility, factor models**, stochastic calculus (9 psets, **no solutions**). | open | mixed | some need data or Excel | PDF | low | Optional second wave |
| E8 | MIT OCW probability and statistics: 18.600 F2019, 6.041SC, 18.650 F2016, 14.384 F2013 | ocw.mit.edu | MIT | CC BY-NC-SA 4.0 | 18.600: 10 psets (from Ross) + exams with solutions. 6.041SC: many with solutions. 18.650 and 14.384: psets without solutions. | undergrad / grad | probability; statistics; **time series** (14.384) | open | mixed | low | PDF | **High** for 18.600 and 6.041 (Bertsekas-Tsitsiklis already 303 rows) | Only 14.384 time series is worth a look |
| E9 | Harvard Stat 110 Strategic Practice | stat110.hsites.harvard.edu | Joe Blitzstein | ARR (no licence stated) | 11 SP sets + homework + practice exams (~250 problems) | undergrad | probability | open | Sol. | low | PDF (LaTeX-typeset) | **High**: Blitzstein & Hwang already has 646 rows | Skip |
| E10 | Open Yale ECON 159 Game Theory (Polak) | oyc.yale.edu/economics/econ-159 | Yale | **CC BY-NC-SA 3.0** | problem sets + midterm and final (solution availability varies by session page) | undergrad | Nash equilibrium, dominance, backward induction, auctions, signalling | open | partly Sol. | some payoff matrices | PDF | none | Optional; fills the game-theory gap |
| E11 | Firm primers: Jane Street *Probability & Markets*; G-Research *Sample Quant Exam* | janestreet.com PDF; gresearch.com PDF | Jane Street; G-Research | ARR | primer: worked examples throughout the text; G-R: 11 questions without answers | interview | EV, markets, adverse selection; regression, Bayes, binary delta, Fermi, game theory | open | worked examples; none for G-R | 0% | PDF | low | Use as style reference; owner may add a few by hand |
| E12 | Puzzle archives: Jane Street puzzles, IBM Ponder This, Brainstellar, OpenQuant, Riddler/Fiddler | web pages | the firms; Brainstellar; OpenQuant; ABC/Substack | ARR (Jane Street: "All rights reserved") | JS ~150 since 2014; Ponder This 341 since 1998; Brainstellar 101; OpenQuant 190 listed | hard | JS mostly grid/visual logic; Ponder This often needs computation; Brainstellar classic probability | open | Sol. posted | JS: most need images | HTML | OpenQuant 167/190 already in; Brainstellar overlaps Winkler/Zhou | Avoid bulk import |
| E13 | OpenStax *Principles of Finance* | openstax.org | Rice University | CC BY 4.0 | ~20 chapters of end-of-chapter questions | intro | TVM, bonds, stocks, risk-return, CAPM, basic statistics and regression in finance | MCQ / problems | answers mostly instructor-only | some Excel | HTML | low | Skip (too elementary) |

### 3.3 Books the owner could supply from their own copies

These are copyrighted: import only from the owner's own copy, and keep the text out of the public repo.

| Book | Size | Fills | In bank? |
|---|---|---|---|
| Crack, *Heard on the Street* | 175+ quant questions with solutions, 125+ non-quant | interview flavour, derivatives, financial economics, statistics | no |
| Joshi, Denson and Downes, *Quant Job Interview Questions and Answers* (2nd ed.) | ~300 questions with answers | option pricing, interest rates, probability, numerical methods | no (the HF copy D15 is pirated) |
| Zhou, *A Practical Guide to Quantitative Finance Interviews* | >200 problems | all interview areas | 113 rows: check whether the rest were skipped on purpose (algorithms chapter?) or missed |
| Hull, *Options, Futures, and Other Derivatives* + Student Solutions Manual | ~700+ practice questions | Greeks, vol, swaps, credit, VaR, interest-rate models | no (XFinBench rewrites part of it) |
| Bodie, Kane and Marcus, *Investments* | ~600 end-of-chapter problems (incl. CFA problems) | portfolio, CAPM/APT, factor models, fixed income | no |
| Brooks, *Introductory Econometrics for Finance* | review questions + MCQ bank | regression, time series, GARCH, cointegration | no |
| Ruppert and Matteson, *Statistics and Data Analysis for Financial Engineering* | exercises (R-heavy) | time series, GARCH, factor models, copulas | no |
| Weinstein and Adam, *Guesstimation* 1 and 2 | ~200 Fermi problems with worked estimates | Fermi estimation | no |
| Wilmott, *Frequently Asked Questions in Quantitative Finance* | ~40 brainteasers + concept Q&A | brainteasers, concepts | no (*PWIQF* is in) |
| Shreve, *Stochastic Calculus for Finance I/II* | exercises (no public official solutions) | discrete and continuous models | no (overlaps Oksendal and Joshi) |
| James et al., *ISLR* | conceptual exercises | ML basics (the SRM syllabus text) | no |

---

## 4. Notes per candidate, with samples

**E1 SOA MFE derivatives (intro + advanced).** The sets are vetted, unambiguous and checkable (five options with a letter key), and every item has a worked solution. Sample, advanced Q1: "European call and put on a nondividend-paying stock... stock 60, call sells for 0.15 more than the put, 4 years, strike 70. Calculate the continuously compounded risk-free rate" (answer A, 0.039). Intro Q3 is a hedging-profit range for jalapeño puts and calls. Keyword counts in the advanced set: delta 23, Black-Scholes 20, binomial 17, gamma 12, exchange option 8, BDT 8, Monte Carlo 6, chooser 4. This is the best match for the thin Greeks, hedging and exotics subtopics. Two caveats:

- Solutions assume the McDonald (*Derivatives Markets*) conventions.
- Five-option MCQs can be stored as MCQ or converted to numeric answers.

The SOA notes also point to the actual May 2007 and May 2009 MFE exams (~25 applicable items) as extra practice.

**E2 SOA IFM Finance and Investment.** 44 Berk-DeMarzo-based questions, including Q1 "lower bound of the 95% CI for expected return from 36 years of data, sd 27%". About 15 are corporate finance (NPV, capital structure); file those under the existing Corporate Finance branch. Revision notes show SOA corrected items over time, which is a good sign of quality.

**E3 SOA SRM.** The best open source for the regression, time-series and ML-basics gap. Q1 is complete-linkage hierarchical clustering; Q3 is a random-walk forecast. The syllabus (2026-12) covers stat learning 5-10%, linear models, time series 10-15%, decision trees 20-25% and PCA/clustering. Some items show regression output tables that need typesetting.

**E4 SOA FM.** Large and clean, with an MCQ answer and a worked solution for every item. Many items are annuities and loans that resemble the 268 compounding rows already in the bank, so take the bond, yield, duration, convexity, immunization and spot/forward items (~250) first. The rest is optional. Actuarial symbols need a short notation note or conversion.

**D1 QuantQA.** 519 interview-style numeric questions with firm tags (Citadel 86, Jane Street 85, Optiver 73, SIG 54, Five Rings 50 ...) and difficulty labels.

Samples:

- "Determine the cost of a straddle at-the-money with S=20, T=0.36, σ=0.4" (3.83). r is unstated; it is implicitly 0.
- "roll ... until 5 or 6; on 5 you collect the total; may cash out" (3.03).
- "Let N=min{n: X_n>U}; determine E(N); input −1 if infinite" (−1).

Defects: a small share omit needed data. "Stone Showdown Strategy" gives no pile size, and "Trilogy of Tosses" omits the question itself. Expect a ~5-10% fix or skip rate. The README says the questions come from interview reports (Glassdoor) at the named firms. The MIT licence is the uploader's claim, and statement wording may echo commercial banks, so treat provenance as "probably reworded interview reports" and keep the text private.

**D2 academicquant.** Most items are easy classics: "Two fair dice ... sum is 7"; "HTH expected tosses = 10". Two items depend on an earlier question ("In the same game ...", "As before ..."). The useful part is the 31 EV and market-making items. Sample: "A stock is worth 60 or 40 ... 20% of traders are informed ... at what offer price ..." (52), an adverse-selection item. Also 11 stats/ML items. Worked answers are behind tracking links to a commercial site, so the card's CC BY 4.0 covers only the uploaded questions and numeric answers. The dataset was uploaded 2026-11-14 and has few downloads.

**D3 XFinBench.** The paper says questions are GPT-4o rewrites of end-of-chapter problems from Ross, Hull and Mishkin, checked by generate-then-verify (35% discarded) and then by human raters.

Samples:

- "binomial tree ... option on a foreign currency, one-month step, r_d 5%, r_f 8%, σ 12%: value of u" (1.0352).
- Black's-model bond-option MCQ: using a 5-year implied vol for a 9-year option gives a price that is "too high".
- Box-spread structure MCQ.
- CDO tranche-yield true/false.

Recommendation: take calc and MCQ only and skip the 1,795 true/false items, which are weak practice. Prefer Hull-derived items (derivatives, swaps, credit, vol, VaR). Ross and Mishkin items are corporate finance and banking (optional). Claude would write the solutions. Licence: MIT on the dataset, but the content derives from copyrighted textbooks. Keep it private.

**D4 FinanceMath.** CFA vignette style ("Smith demonstrates to Harmonica ... soybean futures roll ... total return" = 0.853 (%)).

Watch for:

- **percent versus decimal ambiguity** in ground truths;
- answers rounded to 3 dp;
- some dubious expert solutions (a carried-interest item ignores the hurdle and capital logic).

Its Python solutions make it suitable for "aids" mode: Claude writes a worked solution and checks it against the executed answer. Drop Accounting (258) and Corporate (46) if the aim is quant prep. That leaves ~900, of which ~600 have no table. FinanceReasoning (D5) recycles these items, so skip D5.

**D11 MMLU econometrics.** Short conceptual MCQs. "The pacf is necessary for distinguishing between ... an AR and an ARMA model"; "consequences of CLRM violations (i)-(iv)". Cheap to import, and it fills time-series literacy. Answers only.

**E6 Quantitative Primer.** Real interview transcripts with careful LaTeX solutions. Sample: "1000 coins, one double-headed; ten heads in a row; P(double-headed)?" Drop the C++, SQL and array-coding items. CC BY-SA means adapted text inherits ShareAlike, which matters only if the text is ever redistributed.

**D13 RealFP Fermi.** Mixed quality. Some items are odd ("brain of an SO bacterium"); most are physics-style rather than business-style. Answers need order-of-magnitude grading. There is no licence file, so ask the owner. Guesstimation (book) is the better Fermi source if the owner has it.

**E5 SOA INV 201.** Graduate-level written questions. Example, QFI QF Fall 2020 Q1: "Let M_t = ∫ f(s) dW_s ... show/compute ..."; another is a swap and arbitrage table problem. Valuable for hard stochastic-calculus and derivatives practice. Parts that need Excel should be dropped or converted.

**Table-heavy financial-statement QA (D6, D7, D8).** Not worth taking for quant interviews. Every item needs an earnings-report table, and the skill tested (reading line items, percentage changes) is not what quant interviews ask. The only arguable subset is BizBench FinCode (54 CFA/CPA numeric items), and that is CFA/CPA-derived. **Recommendation: take none.**

---

## 5. Ranked recommendation

### 5.1 Import first (priority order)

| Rank | Source | Expected yield | Licence | Why |
|---|---|---|---|---|
| 1 | SOA MFE intro + advanced derivatives, plus SOA IFM Finance & Investment (E1 + E2) | ~150 (113 + 44, minus a few duplicates) | © SOA; same footing as the 700 Exam P rows already in the bank | Fills Greeks, hedging, exotics, BDT, CAPM and VaR with vetted answers and worked solutions |
| 2 | QuantQA (D1) | ~430-470 after dropping defective items and near-duplicates | MIT (claimed); provenance caveat | The most interview-like open set: firm tags, LaTeX, numeric keys; adds game, EV and some finance and regression |
| 3 | SOA SRM (E3) | ~70 | © SOA | Only vetted open MCQ set for regression, time series and ML basics, with solutions |
| 4 | XFinBench, calc + MCQ, Hull-derived first (D3) | ~800-1,000 (Hull subset); up to ~2,400 with Ross and Mishkin | MIT; textbook-derived | Large, LaTeX, checkable; fills derivatives, vol, swaps, credit and FX |
| 5 | SOA FM, fixed-income subset (E4) | ~250 (all 459 optional) | © SOA | Duration, convexity, immunization, spot/forward and bond pricing with solutions |
| 6 | Quantitative Primer (E6) | ~40 | CC BY-SA 4.0 | Clean licence, LaTeX, real interviews, regression and AR(1) |
| 7 | FinanceMath, non-accounting (D4) | ~600-900 | MIT; CFA-style | Numeric with Python solutions; fixed income, derivatives, risk; needs percent cleanup |
| 8 | MMLU econometrics (D11) | ~120 | MIT | Time-series and OLS concepts, cheap MCQ |

The first four together add **~1,500-1,700** questions concentrated on the gaps. All eight together add **~2,500-2,900**.

Solutions needed from Claude:

- QuantQA, XFinBench and MMLU have answers only: ~1,400-1,600 rows need generated solutions.
- The SOA sets have solutions and fit aids mode.
- FinanceMath has Python solutions that can serve as aids.

Per the pipeline rules, cost and submissions need owner approval first.

### 5.2 Second wave or optional

- academicquant subset (~40: EV and market making, stats and ML).
- SOA INV 201 (~50 hard, multi-part).
- MIT OCW 15.401/15.433 items with solutions (~60) and 18.S096 psets (~45; no solutions).
- Open Yale ECON 159 game theory (~30-50).
- RealFP Fermi (~150 hand-picked, if the licence is OK).
- Owner-supplied books in this order: Crack, Joshi QJIQ, Hull with the Student Solutions Manual, Guesstimation, Brooks.

### 5.3 Gaps with no good source: build them

- **Mental arithmetic.** Generate programmatically: Optiver/Zetamac-style (+, −, ×, ÷, fractions, decimals, percentages; 2-3 digit; timed). Answers are exact. These are better as a timed drill mode than as bank rows.
- **Market making and betting.** No open set beyond the ~31 academicquant items and the Jane Street primer's examples. A templated generator is checkable:
  - fair value and spread of contracts on dice or card sums;
  - quote adjustment under adverse selection, after the Jane Street primer;
  - Kelly fraction for given odds;
  - EV of sequential bets.

  Claude could write 50-100 scenario questions for the owner to review. Label them as generated.
- **Fermi estimation.** Owner's Guesstimation copy, or a hand-picked RealFP subset.

### 5.4 Sources to avoid, and why

| Source | Reason |
|---|---|
| VedantPadwal/quantitative-finance-reasoning | Verbatim Joshi QJIQ questions and answers; no licence. Use the owner's own copy of the book instead. |
| TheFinAI/en-cfa, flare-cfa, CFA-Level-III, BizBench FinKnow | CFA Institute copyrighted content; gated or "other" licence |
| FinEval | CC BY-NC-SA, Chinese, test labels hidden |
| FinanceBench | CC BY-NC, 150 items, needs 10-K PDFs |
| FinQA, ConvFinQA, TAT-QA, BizBench SEC-NUM/CodeFinQA, DocMath-style sets | Financial-statement table QA; off-target for quant interviews |
| FAMMA | Questions are screenshots; multilingual |
| FinanceReasoning | Re-mix of FinanceMath and BizBench; take FinanceMath directly |
| MorbidCorp actuarial sets | LLM-generated, unverified |
| MMLU-Pro business | Mostly REA business arithmetic; low relevance; overlaps TheoremQA |
| QuantGuide.io, Glassdoor, Brainstellar, Jane Street puzzle archive, Riddler/Fiddler, IBM Ponder This | All rights reserved or ToS-restricted. Jane Street puzzles are mostly image grids; Ponder This often needs computation. OpenQuant is already 167/190 in the bank. |
| Harvard Stat 110, MIT 18.600, MIT 6.041 | Licence is CC BY-NC-SA (MIT OCW) or unstated (Harvard), and they overlap Blitzstein & Hwang and Bertsekas & Tsitsiklis already in the bank |

### 5.5 Licence notes

- **SOA** material is copyrighted and free to download, with no reuse licence. The bank already holds 700 SOA Exam P rows on the same footing. Keep it in the private DB only.
- **CC BY-NC-SA** (MIT OCW, Open Yale) is fine for a private study app. It would bind any redistribution to non-commercial use and the same licence.
- **CC BY-SA** (Quantitative Primer): attribution plus ShareAlike on adapted text.
- **MIT/CC BY datasets derived from copyrighted material** (XFinBench from Hull, Ross and Mishkin; FinanceMath CFA-style; MMLU econometrics resembling Brooks; QuantQA from interview reports) carry inherited-rights risk. The memory rule already keeps bulk imported text out of the public repo; that is sufficient here.
