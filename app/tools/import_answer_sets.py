"""Import final-answer problem sets that come with an answer key but no solutions, for the
subscription solver to solve and the judge to check against the key (owner 2026-11-19: "option 1,
and I want to import as many useful sources as possible").

Sets (downloaded by the caller into their own folders; nothing in them is executed):
  * MathArena (huggingface.co/MathArena, CC BY-NC-SA; Amplify is private): the original problems of
    AIME 2025-26, HMMT February 2023-26 and November 2025, BRUMO, SMT and CMIMC 2025. AIME goes to the
    bank's AIME source; the others to "United States Competitions" with the contest in the subsource,
    as the bank already files HMMT. MathArena's own numbering is kept ("Problem 4 of 30"), as its
    sets do not say which round a problem came from. APEX (2025 problems from many competitions,
    some reworded to have a final answer) goes to each problem's own competition, mapped by hand in
    APEX, with ", as posed in MathArena APEX" in the subsource.
  * IMO-Bench AnswerBench v2 (github.com/google-deepmind/superhuman, CC BY 4.0): 400 olympiad problems
    reworded or changed on purpose ("robustified"), many with a different answer from the original,
    so they are filed under their own source, with the original competition in the subsource.

Statements keep their $ math; $$ displays become \\[ \\], Markdown bold becomes \\textbf and
Markdown bullet lists become itemize. An answer with LaTeX in it is wrapped in $ $. A problem the
bank already has (the same latex_hash, or 85% of its 5-word shingles in one bank question) is skipped
and listed. Every row gets the solving model of --model/--effort in --assignments, which puts it in
run_sub.py's scope (config.subscription.assignments_file).

Usage (repo root):
  python -m app.tools.import_answer_sets --matharena DIR --answerbench CSV --dry-run [--dump rows.json]
  python -m app.tools.import_answer_sets --matharena DIR --answerbench CSV --apply
"""

from __future__ import annotations

import argparse
import base64
import collections
import csv
import hashlib
import json
import re
import sqlite3
import zipfile
from pathlib import Path

from app.tools.import_mods_potd import DB_PATH, UNCATEGORIZED, backup_db, check, latex_hash, pdf_safe

MAP_PATH = Path("app/data/appdata/answer_sets_map.csv")  # git-ignored: question id -> set, number
ASSIGNMENTS = Path("pipeline/answer_sets_assignments.json")
FIGURES_PATH = Path("app/data/appdata/answer_sets_figures.json")  # git-ignored: figures not yet drawn (their code)
OPUS = "claude-opus-5-5"
US = "United States Competitions"
AIME = "American Invitational Mathematics Examination"
ANSWERBENCH = "IMO-Bench AnswerBench"
# MathArena set -> (source, subsource for problem i of n)
MATHARENA = {
    "aime_2025": (AIME, lambda i, n: f"2025, AIME {'I' if i <= 15 else 'II'}, Problem {(i - 1) % 15 + 1}"),
    "aime_2026": (AIME, lambda i, n: f"2026, AIME {'I' if i <= 15 else 'II'}, Problem {(i - 1) % 15 + 1}"),
    **{f"hmmt_feb_{y}": (US, lambda i, n, y=y: f"Harvard-MIT Mathematics Tournament, February {y}, Problem {i} of {n}")
       for y in (2023, 2024, 2025, 2026)},
    "hmmt_nov_2025": (US, lambda i, n: f"Harvard-MIT Mathematics Tournament, November 2025, Problem {i} of {n}"),
    "brumo_2025": (US, lambda i, n: f"Brown University Mathematics Olympiad, 2025, Problem {i} of {n}"),
    "smt_2025": (US, lambda i, n: f"Stanford Math Tournament, 2025, Problem {i} of {n}"),
    "cmimc_2025": (US, lambda i, n: f"Carnegie Mellon Informatics and Mathematics Competition, 2025, Problem {i} of {n}"),
}
EUR, ASIA, IND, CHN = "Other European Olympiads", "Other Asian Olympiads", "Indian Olympiads", "Chinese Olympiads"
APEX_SETS = ("apex_2025", "apex-shortlist")
APEX_TAG = ", as posed in MathArena APEX"  # its problems may be reworded to have a final answer
# MathArena APEX problem label -> (source, subsource), by hand in the bank's own naming; labels that
# do not say which competition they are (CMM, BMO: British or Balkan) keep MathArena's label
APEX = {
    "All Russian 2025 11.8": ("All-Russian Olympiad", "2025, Grade 11, Problem 8"),
    "All Russian 2025 11.4": ("All-Russian Olympiad", "2025, Grade 11, Problem 4"),
    "Turkey TST 2025 P5": (EUR, "Turkey Team Selection Test, 2025, Problem 5"),
    "SMT 2025 P8": (US, "Stanford Math Tournament, 2025, Problem 8"),
    "SMT 2025 P42": (US, "Stanford Math Tournament, 2025, Problem 42"),
    "SMT 2025 P43": (US, "Stanford Math Tournament, 2025, Problem 43"),
    "Serbian MO 2025 P6": (EUR, "Serbian Mathematical Olympiad, 2025, Problem 6"),
    "serbian-bmotst-2025-p5": (EUR, "Serbia Team Selection Test for the Balkan Mathematical Olympiad, 2025, Problem 5"),
    "CMM 2025 Individual P10": ("MathArena APEX", "CMM 2025 Individual P10"),
    "CMM 2025 Team P7": ("MathArena APEX", "CMM 2025 Team P7"),
    "BMO 2025 P4": ("MathArena APEX", "BMO 2025 P4"),
    "ELMO Shortlist 2025 N7": ("ELMO Mathematical Olympiad Shortlist", "2025, N7"),
    "ELMO Shortlist 2025 C7": ("ELMO Mathematical Olympiad Shortlist", "2025, C7"),
    "ELMO Shortlist 2025 C8": ("ELMO Mathematical Olympiad Shortlist", "2025, C8"),
    "China TST 2025 P5": ("China Team Selection Test", "2025, Problem 5"),
    "China TST 2025 P10": ("China Team Selection Test", "2025, Problem 10"),
    "China TST 2025 P18": ("China Team Selection Test", "2025, Problem 18"),
    "China TST 2025 P22": ("China Team Selection Test", "2025, Problem 22"),
    "EMCC 2025 Guts P24": (US, "Exeter Math Club Competition, 2025, Guts Round, Problem 24"),
    "emcc-2025-guts-18": (US, "Exeter Math Club Competition, 2025, Guts Round, Problem 18"),
    "IMO 2025 P6": ("International Mathematical Olympiad", "2025, Problem 6"),
    "imosl-2024-c8": ("International Mathematical Olympiad", "2024, Shortlist, C8"),
    "imosl-2024-n7": ("International Mathematical Olympiad", "2024, Shortlist, N7"),
    "usa-tst-2025-p1": ("United States of America Team Selection Test", "2025, Problem 1"),
    "American TSTST 2025 P3": ("United States of America Team Selection Test Selection Test", "2025, Problem 3"),
    "bmmt-2025-team-p19": (US, "Berkeley mini Math Tournament, 2025, Team Round, Problem 19"),
    "hmmt-2025-team-p10": (US, "Harvard-MIT Mathematics Tournament, February 2025, Team Round, Problem 10"),
    "hmmt-2025-team-p4": (US, "Harvard-MIT Mathematics Tournament, February 2025, Team Round, Problem 4"),
    "HMMT Feb 2025 C9": (US, "Harvard-MIT Mathematics Tournament, February 2025, Combinatorics Round, Problem 9"),
    "HMMT Feb 2025 C10": (US, "Harvard-MIT Mathematics Tournament, February 2025, Combinatorics Round, Problem 10"),
    "Brumo 2025 P30": (US, "Brown University Mathematics Olympiad, 2025, Problem 30"),
    "AIME 2025 P14": (AIME, "2025, Problem 14 (AIME I or II not given)"),
    "AIME 2025 P15": (AIME, "2025, Problem 15 (AIME I or II not given)"),
    "indian-imotc-day2-p3": (IND, "Indian International Mathematical Olympiad Training Camp, 2025, Day 2, Problem 3"),
    "India IMOTC 2025 Day 2 P1": (IND, "Indian International Mathematical Olympiad Training Camp, 2025, Day 2, Problem 1"),
    "India STEMS A 2025 P4": (IND, "STEMS Mathematics Olympiad (Chennai Mathematical Institute), 2025, Category A, Problem 4"),
    "India STEMS C 2025 P6": (IND, "STEMS Mathematics Olympiad (Chennai Mathematical Institute), 2025, Category C, Problem 6"),
    "rmm-2025-p3": ("Romanian Masters of Mathematics", "2025, Problem 3"),
    "Germany TST 2025 P3": (EUR, "Germany Team Selection Test, 2025, Problem 3"),
    "Germany TST 2025 P4": (EUR, "Germany Team Selection Test, 2025, Problem 4"),
    "Germany TST 2025 P7": (EUR, "Germany Team Selection Test, 2025, Problem 7"),
    **{f"Korea Winter Program Practice Test 2025 P{i}": (ASIA, f"Korea Winter Program Practice Test, 2025, Problem {i}")
       for i in (2, 3, 6, 8)},
    "Korea Final Round 2025 P5": (ASIA, "Korean Mathematical Olympiad, 2025, Final Round, Problem 5"),
    "Taiwan TST 2025 #3 Quiz 1C": ("Taiwan Team Selection Test", "2025, Round 3, Quiz 1, Problem C"),
    "Taiwan TST 2025 #1 P5": ("Taiwan Team Selection Test", "2025, Round 1, Problem 5"),
    "Taiwan TST 2025 #3 Quiz P5": ("Taiwan Team Selection Test", "2025, Round 3, Quiz, Problem 5"),
    "China Girls MO 2025 P7": (CHN, "China Girls' Mathematical Olympiad, 2025, Problem 7"),
    "Japan MO 2025 P3": ("Japan Mathematical Olympiad Final Round", "2025, Problem 3"),
    "IzHO 2025 P2": (ASIA, "International Zhautykov Olympiad, 2025, Problem 2"),
    "IzHO 2025 P4": (ASIA, "International Zhautykov Olympiad, 2025, Problem 4"),
    "EGMO 2025 P5": ("European Girls' Mathematical Olympiad", "2025, Problem 5"),
    "Bulgarian MO 2025 P2": (EUR, "Bulgarian Mathematical Olympiad, 2025, Problem 2"),
    "Bulgarian MO 2025 P6": (EUR, "Bulgarian Mathematical Olympiad, 2025, Problem 6"),
    "Swiss TST 2025 P5": (EUR, "Swiss Team Selection Test, 2025, Problem 5"),
    "LMAO 2025 Day 1 P2": ("Mock Olympiads", "LMAO, 2025, Day 1, Problem 2"),
    "LMAO 2025 Day 2 P1": ("Mock Olympiads", "LMAO, 2025, Day 2, Problem 1"),
}
AMC = "American Mathematics Competitions"
# HARP contest -> (source, contest in the subsource), the bank's naming ("2018, AMC 12B, Problem 21")
HARP_CONTESTS = {"AHSME": (AMC, "AHSME"), "AJHSME": (AMC, "AJHSME"), "AMC_8": (AMC, "AMC 8"),
                 "AMC_10": (AMC, "AMC 10"), "AMC_10A": (AMC, "AMC 10A"), "AMC_10B": (AMC, "AMC 10B"),
                 "AMC_12": (AMC, "AMC 12"), "AMC_12A": (AMC, "AMC 12A"), "AMC_12B": (AMC, "AMC 12B"),
                 "AIME": (AIME, ""), "AIME_I": (AIME, "AIME I"), "AIME_II": (AIME, "AIME II")}
OMNI = "Omni-MATH"  # its problems carry the competition but no year or problem number
UMATH = "U-MATH"  # 1,100 unpublished university problems (huggingface.co/datasets/toloka/u-math, MIT), answers only
UMATH_SUBJECTS = {"precalculus_review": "Precalculus", "algebra": "Algebra", "differential_calc": "Differential Calculus",
                  "integral_calc": "Integral Calculus", "multivariable_calculus": "Multivariable Calculus",
                  "sequences_series": "Sequences and Series"}
TEXIMAGES = Path("app/data/appdata/teximages")  # the app's image folder (config paths.teximages)
GRAPHIC = r"\includegraphics[max width=0.5\textwidth, alt={{}}, center]{{{}}}"  # the bank's style
OMNI_NAMES = {
    "HMMT_2": "Harvard-MIT Mathematics Tournament, February", "HMMT_11": "Harvard-MIT Mathematics Tournament, November",
    "pascal": "CEMC Pascal Contest", "fermat": "CEMC Fermat Contest", "cayley": "CEMC Cayley Contest",
    "imo_shortlist": "International Mathematical Olympiad Shortlist", "imo": "International Mathematical Olympiad",
    "imo_longlists": "International Mathematical Olympiad Longlist", "usamo": "United States of America Mathematical Olympiad",
    "usajmo": "United States of America Junior Mathematical Olympiad", "china_team_selection_test": "China Team Selection Test",
    "putnam": "William Lowell Putnam Mathematical Competition", "imc": "International Mathematics Competition for University Students",
    "apmoapmo_sol": "Asian Pacific Mathematics Olympiad", "apmo": "Asian Pacific Mathematics Olympiad",
    "asia_pacific_math_olympiad": "Asian Pacific Mathematics Olympiad", "ToT": "Tournament of Towns", "baltic_way": "Baltic Way",
    "china_national_olympiad": "China Mathematical Olympiad", "usa_team_selection_test": "United States of America Team Selection Test",
    "usa_team_selection_test_for_imo": "United States of America Team Selection Test",
    "balkan_mo_shortlist": "Balkan Mathematical Olympiad Shortlist", "balkan_mo": "Balkan Mathematical Olympiad",
    "problems_from_the_kmal_magazine": "KöMaL", "problems_from_the_kvant_magazine": "Kvant",
    "jbmo_shortlist": "Junior Balkan Mathematical Olympiad Shortlist", "jbmo_shortlists": "Junior Balkan Mathematical Olympiad Shortlist",
    "jbmo": "Junior Balkan Mathematical Olympiad", "junior_balkan_mo": "Junior Balkan Mathematical Olympiad",
    "alibaba_global_contest": "Alibaba Global Mathematics Competition",
    "middle_european_mathematical_olympiad": "Middle European Mathematical Olympiad",
    "th_middle_european_mathematical_olympiad": "Middle European Mathematical Olympiad",
    "cono_sur_olympiad": "Cono Sur Olympiad", "czech-polish-slovak matches": "Czech-Polish-Slovak Match",
    "tuymaada_olympiad": "Tuymaada Olympiad", "izho": "International Zhautykov Olympiad",
    "international_zhautykov_olympiad": "International Zhautykov Olympiad",
    "caucasus_mathematical_olympiad": "Caucasus Mathematical Olympiad", "bero_American": "Iberoamerican Mathematical Olympiad",
    "european_mathematical_cup": "European Mathematical Cup", "pan_african MO": "Pan-African Mathematical Olympiad",
    "centroamerican": "Centroamerican and Caribbean Mathematical Olympiad",
    "centroamerican_and_caribbean_math_olympiad": "Centroamerican and Caribbean Mathematical Olympiad",
    "th_centroamerican_and_caribbean_math_olympiad_havana": "Centroamerican and Caribbean Mathematical Olympiad",
    "rioplatense_mathematical_olympiad_level": "Rioplatense Mathematical Olympiad", "yau_contest": "S.-T. Yau College Student Mathematics Contest",
    "benelux MO": "Benelux Mathematical Olympiad", "th_igo": "Iranian Geometry Olympiad", "iranian_geometry_olympiad": "Iranian Geometry Olympiad",
    "lusophon_mathematical_olympiad": "Lusophon Mathematical Olympiad", "austrianpolish_competition": "Austrian-Polish Mathematics Competition",
    "european_girls_mo": "European Girls' Mathematical Olympiad", "math_olympiad_for_the_french_speaking": "Francophone Mathematical Olympiad",
    "nordic": "Nordic Mathematical Contest", "usomo": "United States of America Mathematical Olympiad",
    "usojmo": "United States of America Junior Mathematical Olympiad", "iranian_combinatorics_olympiad": "Iranian Combinatorics Olympiad",
    "silk_road_mathematics_competition": "Silk Road Mathematics Competition", "mediterranean_mathematics_olympiad": "Mediterranean Mathematics Olympiad",
    "simon_marais_mathematics_competition": "Simon Marais Mathematics Competition", "danube_mathematical_olympiad": "Danube Mathematical Olympiad",
    "danube_mathematical_competition": "Danube Mathematical Competition", "imor": "IMO Revenge",
    "st_tashkent_international_mathematical_olympiad": "Tashkent International Mathematical Olympiad",
    "hungaryisrael_binational": "Hungary-Israel Binational Mathematical Competition",
    "competition_given_at_the_end_of_the_international_mathematics_summer_camp": "International Mathematics Summer Camp",
}
SET_ASIDE_PATH = Path("app/data/appdata/answer_sets_set_aside.json")  # git-ignored: rows left out for a hand fix
SOLUTIONS_PATH = Path("app/data/appdata/answer_sets_solutions.json")  # git-ignored: the sets' own solutions, for later
NEAR = 0.85  # share of a problem's 5-word shingles found in one bank question: the same problem
# (set, number, field) -> [(old, new)]: slips in the source data, each old matched exactly once
FIXES = {
    ("IMO-Bench AnswerBench v2", "imo-bench-algebra-097", "answer"): [("\\frac{\\sqrt{5}+1}{2}", "\\frac{\\sqrt{5}+1}{2}$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-geometry-096", "answer"): [("$\\frac{7}{18}", "$\\frac{7}{18}$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-combinatorics-004", "latexcode"): [("\\ldots, 191}$", "\\ldots, 191\\}$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-algebra-013", "latexcode"): [  # \right, and a \} closing a \left\{
        ("\\right)\\right, Q", "\\right), Q"), ("Q\\left(n^{2}\\right)\\}", "Q\\left(n^{2}\\right)\\right\\}")],
    ("MathArena aime_2025", "20", "latexcode"): [  # \wideparen is not in the app's preamble
        ("\\wideparen{DE}", "\\overset{\\frown}{DE}"), ("\\wideparen{HJ}", "\\overset{\\frown}{HJ}"),
        ("\\wideparen{FG}", "\\overset{\\frown}{FG}")],
    ("IMO-Bench AnswerBench v2", "imo-bench-combinatorics-002", "latexcode"): [("i) 99 \\leq n \\leq 206", "i) $99 \\leq n \\leq 206$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-combinatorics-098", "latexcode"): [  # \cI undefined; S is that set
        ("\\sum_{I \\in S}", "\\sum_{I \\in \\mathcal{I}(P_n)}"), ("$\\cI(P_n)$", "$\\mathcal{I}(P_n)$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-geometry-012", "latexcode"): [  # subscripts outside math
        ("points X_y and X_z", "points $X_y$ and $X_z$"), ("Points Y_x, Y_z, Z_x and Z_y", "Points $Y_x$, $Y_z$, $Z_x$ and $Z_y$"),
        ("points X_y, X_z, Y_x, Y_z, Z_x, and Z_y", "points $X_y$, $X_z$, $Y_x$, $Y_z$, $Z_x$, and $Z_y$")],
    ("IMO-Bench AnswerBench v2", "imo-bench-number_theory-021", "latexcode"): [("\\textif{", "\\textit{")],
    ("MathArena hmmt_nov_2025", "1", "latexcode"): [("\\overlien{BC}", "\\overline{BC}")],
    ("MathArena hmmt_nov_2025", "14", "latexcode"): [("\\begin{array}{ccccc}", "\\begin{array}{cccccc}")],  # six columns
    # HARP keys found wrong 2026-11-20 (two Opus solves disagreed with each; checked by hand, owner approved)
    ("HARP", "1958 AHSME 31", "answer"): [("$24$", "$48$")],     # base 12, area 12*8/2
    ("HARP", "1977 AHSME 10", "answer"): [("$-64$", "$128$")],   # (3*1-1)^7
    ("HARP", "1978 AHSME 4", "answer"): [("$3333$", "$2222$")],  # 2(a+b+c+d)
    ("HARP", "1981 AHSME 13", "answer"): [("$16$", "$22$")],     # 0.9^n <= 0.1: n >= 21.85
    # Omni-MATH keys found wrong 2026-11-21 (Opus twice the other value; checked by hand, owner: "correct the incorrect keys")
    ("Omni-MATH", "945", "answer"): [("2017+1", "2^{2017}+1")],  # the set's own solution ends (2^{2017}+1)/3
    ("Omni-MATH", "101", "answer"): [("7", "6")],                 # 7 circles force a Fano plane, not drawable; an orthocentric system gives 6
    # found by the blind re-solve of 2026-11-21 (owner: "fix the keys")
    ("HARP", "1954 AHSME 13", "answer"): [("$180^\\circ$", "$540^\\circ$")],  # an angle inscribed in an arc has its vertex on it: (4*360-360)/2
    ("HARP", "1965 AHSME 3", "answer"): [("$3$", "$\\frac{1}{3}$")],          # as written, -2^{-2} = -1/4: 81^{-1/4}
    ("IMO-Bench AnswerBench v2", "imo-bench-combinatorics-097", "answer"): [("85383238549", "20919175804480")],  # someone stays in nearly every deal
    # Omni-MATH hand check 2026-11-21 (owner: "Go ahead with everything"): keys Opus contradicted twice, checked by
    # computation (several against the original HMMT answer sheets); statements completed from their sources
    ("Omni-MATH", "181", "answer"): [('2', '1+\\sqrt{3}-\\sqrt{2\\sqrt{3}}')],  # q33209
    ("Omni-MATH", "242", "answer"): [('5183', '4983')],  # q33246
    ("Omni-MATH", "334", "answer"): [('\\[ 541 \\]', '451')],  # q33304
    ("Omni-MATH", "368", "answer"): [('$\\frac{\\pi}{12}$', '$\\frac{5\\pi}{24}$')],  # q33328
    ("Omni-MATH", "377", "answer"): [('$\\frac{1}{4}$', '$\\frac{7}{36}$')],  # q33337
    ("Omni-MATH", "378", "answer"): [('3', '7+4\\sqrt{3}')],  # q33338
    ("Omni-MATH", "408", "answer"): [('15', '\\frac{13}{49}')],  # q33366
    ("Omni-MATH", "412", "answer"): [('96', '-\\frac{130}{27}')],  # q33369
    ("Omni-MATH", "449", "answer"): [('1', '\\frac{\\pi^2}{16}-\\frac{1}{2}')],  # q33402
    ("Omni-MATH", "477", "answer"): [('\\[\\frac{1}{2}\\]', '\\frac{2}{3}')],  # q33430
    ("Omni-MATH", "538", "answer"): [('420', '\\frac{41}{2}')],  # q33490
    ("Omni-MATH", "590", "answer"): [('$40^{\\circ}$', '$30^{\\circ}$')],  # q33541
    ("Omni-MATH", "614", "answer"): [('614.519...', '1129.418')],  # q33564
    ("Omni-MATH", "630", "answer"): [('$\\sqrt{\\frac{\\sqrt{58}}{2+\\sqrt{34}+\\sqrt{58}}}$', '$\\frac{\\sqrt{58}}{2+\\sqrt{34}+\\sqrt{58}}$')],  # q33580
    ("Omni-MATH", "632", "answer"): [('9000000', 'N \\approx 8.28 \\times 10^{6}')],  # q33582
    ("Omni-MATH", "663", "answer"): [('66', '6')],  # q33611
    ("Omni-MATH", "907", "answer"): [('97', '\\frac{97}{3}')],  # q33845
    ("Omni-MATH", "911", "answer"): [('11', '1')],  # q33849
    ("Omni-MATH", "984", "answer"): [('10', '9')],  # q33919
    ("Omni-MATH", "1066", "answer"): [('$2^{32}$', '$4295032832$')],  # q33999
    ("Omni-MATH", "1109", "answer"): [('5', '2')],  # q34039
    ("Omni-MATH", "1149", "answer"): [('12', '13')],  # q34074
    ("Omni-MATH", "1244", "answer"): [('$\\sqrt{\\frac{2^{2009}-1}{3 \\cdot 2^{2008}-1}}$', '$\\frac{2^{2009}-1}{3\\cdot 2^{2008}-1}$')],  # q34162
    ("Omni-MATH", "909", "latexcode"): [('A restricted path of length $n$ is a path', 'A path of length $n$ is a sequence of $n$ lattice points, each one unit up or one unit to the right of the one before it, so it has $n-1$ steps. A restricted path of length $n$ is a path')],  # q33847
    ("Omni-MATH", "1055", "latexcode"): [('Find the number of subsets', 'The order of an element of $A$ in a set of pairs is the number of pairs that contain it, and a set of pairs is consistent of order $k$ if every element of $A$ has order $k$. Find the number of subsets')],  # q33988
    ("Omni-MATH", "559", "latexcode"): [('The $W$ in this problem has the same value as the $W$ in problem 31.', 'Here $W=8$.')],  # q33511
    ("Omni-MATH", "741", "latexcode"): [('2024\\}', '2024!\\}')],  # q33686
    # second Omni-MATH hand check 2026-11-21 (owner: "Go ahead with everything")
    ("Omni-MATH", "925", "answer"): [('0.9102805441016536', '0.9105515')],  # q33863
    ("Omni-MATH", "1392", "answer"): [('940', '950')],  # q34302
    ("Omni-MATH", "1465", "answer"): [('18', '17')],  # q34372
    ("Omni-MATH", "1726", "answer"): [('$40^{\\circ}$', '$30^{\\circ}$')],  # q34603
    ("Omni-MATH", "1851", "answer"): [('2029906', '2030981')],  # q34722
    ("Omni-MATH", "1447", "answer"): [('2009', '-2009')],  # q34355
    ("Omni-MATH", "1579", "answer"): [('$2^{2018}-1$', '$2^{2019}-1$')],  # q34480
    ("Omni-MATH", "1764", "answer"): [('$\\frac{3+\\sqrt{3}}{2}$', '$\\frac{1+\\sqrt{2}+\\sqrt{6}}{2}$')],  # q34640
    ("Omni-MATH", "1879", "answer"): [('$\\frac{341}{55}$', '$\\frac{341}{54}$')],  # q34749
    ("Omni-MATH", "1967", "answer"): [('6', '3')],  # q34833
    ("Omni-MATH", "2288", "answer"): [('$\\sqrt{\\frac{5}{2}}$', '$\\frac{5}{2}$')],  # q35131
    ("Omni-MATH", "2025", "answer"): [('712.811', '\\approx 712.811')],  # q34887
    ("Omni-MATH", "1325", "latexcode"): [('What is the earliest row in which the number 2004 may appear?', "An infinite table of nonnegative integers is constructed as follows: in the top row, some number is 1 and all other numbers are 0's; in each subsequent row, every number is the sum of some two of the three closest numbers in the preceding row. The top row (with the one 1) is called row 0; the next row is row 1; the next row is row 2, and so forth. Considering every table that can be constructed this way, what is the earliest row in which the number 2004 may appear?")],  # q34240
    ("Omni-MATH", "1897", "latexcode"): [('find a value of $k$, not necessarily the smallest, such that', 'find the smallest positive integer $k$ such that')],  # q34767
    ("Omni-MATH", "1897", "answer"): [('256', '83')],  # q34767
    # human-review check 2026-11-21 (owner: "fix 35200 and 35230"): a transcription slip in the key (official HMMT
    # Feb 2010 answer 5/8); the source (HMMT Nov 2012) has 16x^4, which the key answers
    ("Omni-MATH", "2357", "answer"): [('$\\sqrt[5]{8}$', '$\\frac{5}{8}$')],  # q35200
    ("Omni-MATH", "2387", "latexcode"): [('=17x^{4}$', '=16x^{4}$')],  # q35230
    # third Omni-MATH hand check 2026-11-21 (owner: "Go ahead with the rest"): keys the replies gave twice, checked by
    # computation; statements completed from their sources (keys unchanged); 36669 also a typo in the second car type
    ("Omni-MATH", "2394", "answer"): [('0.96039', '0.96040')],  # q35237
    ("Omni-MATH", "2456", "answer"): [('3426576', '6849777')],  # q35297
    ("Omni-MATH", "2851", "answer"): [('10000', '10080')],  # q35683
    ("Omni-MATH", "3085", "answer"): [('86', '20+20\\sqrt{11}')],  # q35897
    ("Omni-MATH", "3699", "answer"): [('100902018', '100891928')],  # q36439
    ("Omni-MATH", "3725", "answer"): [('45', '1964')],  # q36462
    ("Omni-MATH", "3728", "answer"): [('951', '931')],  # q36465
    ("Omni-MATH", "3740", "answer"): [('32', '33')],  # q36476
    ("Omni-MATH", "3751", "answer"): [('$\\frac{1}{99}$', '$-\\frac{1}{99}$')],  # q36487
    ("Omni-MATH", "3834", "answer"): [('101', '100')],  # q36560
    ("Omni-MATH", "3870", "answer"): [('1003', '337')],  # q36580
    ("Omni-MATH", "3991", "answer"): [('$\\frac{13}{4}$', '$5$')],  # q36665
    ("Omni-MATH", "3995", "answer"): [('2021', '2014')],  # q36669
    ("Omni-MATH", "3999", "answer"): [('576', '162432')],  # q36672
    ("Omni-MATH", "4032", "answer"): [('16', '9')],  # q36700
    ("Omni-MATH", "4150", "answer"): [('$\\sqrt{9 + 6\\sqrt{3}}$', '$\\frac{1}{2}$')],  # q36786
    ("Omni-MATH", "4170", "answer"): [('7', '3')],  # q36800
    ("Omni-MATH", "3995", "latexcode"): [('some have the rear with north and the rear with south magnetic polarity', 'some have the front with south and the rear with north magnetic polarity')],  # q36669
    ("Omni-MATH", "2399", "latexcode"): [('Find the number of ways to distribute 4 pieces of candy to 12 children such that no two consecutive children receive candy.', '12 children sit around a circle. Find the number of ways we can distribute 4 pieces of candy among them such that each child gets at most one piece of candy and no two adjacent children both get a piece of candy.')],  # q35242
    ("Omni-MATH", "2401", "latexcode"): [("Find the probability that a monkey typing randomly on a typewriter will type the string 'abc' before 'aaa'.", 'A monkey forms a string of letters by repeatedly choosing one of the letters a, b, or c to type at random. Find the probability that he first types the string aaa before he first types the string abc.')],  # q35244
    ("Omni-MATH", "2415", "latexcode"): [('Find the number of solutions to the equation $x+y+z=525$ where $x$ is a multiple of 7, $y$ is a multiple of 5, and $z$ is a multiple of 3.', 'Find the number of ordered triples of nonnegative integers $(x,y,z)$ satisfying $15x+21y+35z=525$.')],  # q35257
    ("Omni-MATH", "2419", "latexcode"): [('Find the number of arrangements of 4 beads (2 red, 2 green, 2 blue) in a circle such that the two red beads are not adjacent.', 'Find the number of distinct arrangements of 6 beads (2 red, 2 green, 2 blue) in a circle, where two arrangements are the same if one can be rotated or reflected to give the other.')],  # q35261
    ("Omni-MATH", "2531", "latexcode"): [('Find the total area of the region outside of an equilateral triangle but inside three circles each with radius 1, centered at the vertices of the triangle.', 'Three circles of radius 1 are drawn, whose centers form the vertices of an equilateral triangle of side length 1. Find the area of the region common to at least two of the circles.')],  # q35372
    ("Omni-MATH", "2972", "latexcode"): [('What is the probability that the arrow stops on a shaded region if a circular spinner is divided into six regions, four regions each have a central angle of $x^{\\circ}$, and the remaining regions have central angles of $20^{\\circ}$ and $140^{\\circ}$?', 'A circular spinner is divided into six regions: four regions each have a central angle of $x^{\\circ}$, and the remaining regions have central angles of $20^{\\circ}$ and $140^{\\circ}$. The $140^{\\circ}$ region and two of the four $x^{\\circ}$ regions are shaded. What is the probability that the arrow stops on a shaded region?')],  # q35794
    ("Omni-MATH", "2980", "latexcode"): [('What is the sum of all of the possibilities for Sam\'s number if Sam thinks of a 5-digit number, Sam\'s friend Sally tries to guess his number, Sam writes the number of matching digits beside each of Sally\'s guesses, and a digit is considered "matching" when it is the correct digit in the correct position?', 'Sam thinks of a 5-digit number and his friend Sally tries to guess it. Sam writes the number of matching digits beside each of Sally\'s guesses, where a digit is "matching" when it is the correct digit in the correct position. Sally\'s guesses and the number of matching digits Sam wrote beside each are: 51545 (2), 21531 (1), 71794 (0), 59135 (1), 58342 (2), 37348 (2), 71744 (1). What is the sum of all of the possibilities for Sam\'s number?')],  # q35801
    ("Omni-MATH", "3021", "latexcode"): [('Each of the following 15 cards has a letter on one side and a positive integer on the other side.', 'Each of 15 cards has a letter on one side and a positive integer on the other side. Lying on a table, 1 card shows a lower case letter, 4 cards show upper case letters, 2 cards show even integers and 8 cards show odd integers.')],  # q35839
    ("Omni-MATH", "3052", "latexcode"): [('The perimeter of $\\triangle ABC$', 'In $\\triangle ABC$, $AB=BC=3x+4$ and $AC=2x$. Rectangle $DEFG$ has side lengths $DE=2x-2$ and $EF=3x-1$. The perimeter of $\\triangle ABC$')],  # q35867
    ("Omni-MATH", "3077", "latexcode"): [('What is the remainder when the integer equal to \\( QT^2 \\) is divided by 100, given that \\( QU = 9 \\sqrt{33} \\) and \\( UT = 40 \\)?', '$PQ$ is a diameter of the circular base of a cylinder. $RS$ is a diameter of the top face of the cylinder and is directly above $PQ$ ($R$ directly above $P$, $S$ directly above $Q$). Point $U$ is on the circumference of the top face, halfway between $R$ and $S$. Point $T$ is on the cylinder and is directly above $P$. Suppose that $QS = m$ and $PT = n$, where $m$ and $n$ are integers with $1 < n < m$. If $QU = 9\\sqrt{33}$ and $UT = 40$, what is the remainder when the integer equal to $QT^2$ is divided by 100?')],  # q35889
    ("Omni-MATH", "3110", "latexcode"): [('What is the value of $x$ if $P Q S$ is a straight line and $\\angle P Q R=110^{\\circ}$?', '$P Q S$ is a straight line and $\\angle P Q R=110^{\\circ}$. In triangle $QRS$, the angle at $R$ is $(3x)^{\\circ}$ and the angle at $S$ is $(x+14)^{\\circ}$. What is the value of $x$?')],  # q35920
    ("Omni-MATH", "3255", "latexcode"): [('In the subtraction shown,', 'In the subtraction $5K3L - M4N1 = 4451$ of two four-digit numbers,')],  # q36050
    ("Omni-MATH", "3399", "latexcode"): [('is to be the same. Five numbers have been entered.', 'is to be the same. Five numbers have been entered: 3, 7, 9, 11 and 15, and the missing ones are labelled $p, q, r, s, u$; the five straight lines contain, respectively, $\\{9, p, q, 7\\}$, $\\{3, p, u, 15\\}$, $\\{3, q, r, 11\\}$, $\\{9, u, s, 11\\}$ and $\\{15, s, r, 7\\}$.')],  # q36176
    ("Omni-MATH", "3471", "latexcode"): [('Which of the following is a possible value of $x$ if given two different numbers on a number line, the number to the right is greater than the number to the left, and the positions of $x, x^{3}$ and $x^{2}$ are marked on a number line?', 'On a number line, the number to the right is greater than the number to the left. The positions of $x$, $x^{3}$ and $x^{2}$ are marked on a number line in the order $x$, $x^{3}$, $x^{2}$ from left to right. Which of the following is a possible value of $x$? (A) $\\frac{1}{5}$ (B) $\\frac{3}{2}$ (C) $-\\frac{2}{5}$ (D) $-\\frac{4}{3}$ (E) $2$')],  # q36243
    # U-MATH/CHAMP keys found wrong 2026-11-21 (the same reply twice against the key; checked by hand with sympy and
    # brute force, owner: "Go ahead with ... the 12 key fixes"); U-MATH keys keep their label
    ("U-MATH", "40a59d5b-7cc2-4527-8be9-d64c434be864", "answer"): [('$I$ = $\\frac{274}{15}$', '$I$ = $\\frac{56\\sqrt{3}}{5}$')],  # q37289
    ("U-MATH", "51106f64-d305-4db0-b14f-2d0ec24181d3", "answer"): [('$\\frac{64\\cdot\\pi}{3}$', '$\\frac{128\\cdot\\pi}{3}$')],  # q37364
    ("U-MATH", "5eebe4a7-75d3-4e52-913a-54badf5c3c51", "answer"): [('$3.0722$', '$3.0723$')],  # q37421
    ("U-MATH", "722661f3-5831-4484-beba-4d3d1b7997eb", "answer"): [('$\\frac{1573}{90}$', '$\\frac{13\\sqrt{13}}{9}$')],  # q37520
    ("U-MATH", "91c84b88-d4a5-463f-8f32-094eb4c841e8", "answer"): [('Volume = $\\frac{\\pi}{4}$', 'Volume = $\\frac{\\pi}{2}$')],  # q37635
    ("U-MATH", "9a619d61-4b5a-41df-b77f-d40cd4de08f6", "answer"): [('Volume = $16\\cdot\\pi^2$', 'Volume = $32\\cdot\\pi^2$')],  # q37666
    ("U-MATH", "9eee7969-14e8-4e46-af9e-f5abe22824c9", "answer"): [('$n=3$', '$n=2$')],  # q37705
    ("U-MATH", "b78a35bf-86eb-4ed0-8899-09518687eaeb", "answer"): [('The solution is $x$ = $5$', 'The solution is $x$ = $6$')],  # q37796
    ("U-MATH", "bcc5b742-cc7b-42d6-98eb-9db904ab8078", "answer"): [('$I$ = $\\frac{112}{5}$', '$I$ = $\\frac{16096}{405}$')],  # q37821
    ("U-MATH", "e9c1a928-3748-44fc-8791-eaf192d07f88", "answer"): [('$S$ = $\\frac{5}{4}\\cdot\\pi$', '$S$ = $\\frac{5}{8}\\cdot\\pi$')],  # q37987
    ("CHAMP", "P_Sequence_10", "answer"): [('3', '2')],  # q38317
    ("CHAMP", "P_Sequence_33", "answer"): [('8', '\\frac{1}{8}')],  # q38340
    # owner 2026-11-21: "remove 37796's misleading last sentence" (a hint pointing at the wrong method)
    ("U-MATH", "b78a35bf-86eb-4ed0-8899-09518687eaeb", "latexcode"): [('\n\nTo find the solution, we need to find the value of $x$ such that $f(x) = 5$.', '')],  # q37796
    # U-MATH source slips (2026-11-21): money written with a bare $, a stray $ before an integral
    ("U-MATH", "182fed94-4634-460f-a70e-7958a2033664", "answer"): [('$q(x) = $\\int', '$q(x) = \\int')],
    ("U-MATH", "3592c6d2-0fb1-4557-b219-d88f5b8a7401", "answer"): [('$q(x) = $\\int', '$q(x) = \\int')],
    ("U-MATH", "ef4c1961-77eb-4ec9-9674-8d37ac5fb76d", "answer"): [('$q(x) = $\\int', '$q(x) = \\int')],
    ("U-MATH", "a328709a-3973-45ce-ac0c-956e736146fb", "answer"): [('$ $583.75$', '\\$583.75')],
    ("U-MATH", "d41983e6-eea1-4dfa-8060-ce53dcd25940", "answer"): [('$ $583.75$', '\\$583.75')],
    ("U-MATH", "dac50753-b5d3-4c11-a1c7-1575dde6e606", "latexcode"): [('a $10,000 raise', 'a \\$10,000 raise')],
    ("U-MATH", "96fe4430-f908-4203-a29d-19913fae86b4", "latexcode"): [('1. $72.00 in', '1. \\$72.00 in')],
    ("U-MATH", "ca5b0525-4e4c-4698-8367-146ba9ca18e3", "latexcode"): [('costs $3 and', 'costs \\$3 and'), ('costs $2 per', 'costs \\$2 per'), ('total of $17,', 'total of \\$17,')],
}
# rows deleted from the bank after their import: a re-import leaves them out
DROPPED = {
    "Omni-MATH 79": "question 33123, owner 2026-11-21: 'Delete 33123. Its not worth the effort.' "
                    "(key 18, Opus 20 twice; the set's solution proves only n >= 18)",
    "Omni-MATH 383": "question 33343, owner 2026-11-21 (Omni-MATH hand check): a joke riddle whose official answer (in base 15, 6) contradicts its own premise",
    "Omni-MATH 574": "question 33526, owner 2026-11-21 (Omni-MATH hand check): the recurrence holds for n >= 2, so a_2 and a_3 are undefined; the official answer assumes other starting values",
    "Omni-MATH 971": "question 33907, owner 2026-11-21 (Omni-MATH hand check): it depends on the answers (H_1, H_6) of other contest problems that are not included",
    # owner 2026-11-21: "delete the 3 as well as 36841, 28709, and 33146" (third Omni-MATH hand check, and the cut-offs)
    "Omni-MATH 2866": "question 35698: the magic-square figure is missing (no entries, size or positions)",
    "Omni-MATH 2995": "question 35814: the circle graph the answer depends on is missing",
    "Omni-MATH 3356": "question 36135: the figure is missing: the chords 'as shown' and the points P, T, U are never defined",
    "Omni-MATH 4227": "question 36841: IMO 2022 P6; both solves cut off at the output limit (key right)",
    "IMO-Bench AnswerBench v2 imo-bench-combinatorics-049": "question 28709: both solves cut off at the output limit (key 1057 right)",
    "Omni-MATH 107": "question 33146: both solves cut off at the output limit (key p^a q^b r^c right)",
    "U-MATH 6eab7d06-a894-4b93-8479-b153c4ea7408": "question 37499, owner 2026-11-21: 'delete 37499': reads an average rate of change off a graph; the key (-0.5) holds but the solver misread the graph twice",
    **{f"U-MATH {u}": f"question {q}, owner 2026-11-21: 'Delete the sketch the graph questions.' (opens 'Sketch the curve:')"
       for q, u in [(37013, "02d22949-d7a2-46ca-8af8-4bda85bc8e0e"), (37016, "03b87419-fe7c-481a-9396-1d0723fc2b15"),
                    (37067, "0fec4721-ec02-4a72-aa1a-2ed7b0f8276d"), (37259, "3b3ba848-ee8f-4978-b0c2-ceb26a88779e"),
                    (37298, "4301fe9b-6f1c-4157-a503-c9a4a63aac9b"), (37304, "43ce18b9-35be-43a7-b18f-bff62d27b1d5"),
                    (37395, "592ed5f2-ba58-4094-ae40-57d78056e804"), (37396, "59685710-67d1-4c31-ae2d-1177a32f16bd"),
                    (37446, "6393eea4-766f-400b-a497-def1c92321c4"), (37501, "6eb723e9-f3be-45fb-93d2-513d7ac5c99b"),
                    (37542, "787ba86e-1894-49ad-9a6d-bb1607e13786"), (37570, "7efd2ae1-d387-447f-ad12-4b0dc2ab7a22"),
                    (37603, "8b909199-f22e-4b2b-90ae-f1b0e119b9d9"), (37665, "9a52c80d-be49-4c0b-b9d9-b4d7c1d76989"),
                    (37949, "de2bd512-089e-4d1e-b577-dd185962e7cf"), (37967, "e33483e5-a385-4ce3-91af-54df50ca062b"),
                    (37994, "ebce3086-94ba-4f5d-a9eb-d41c4104e62a"), (38057, "f928de60-dedf-4c5b-8ffc-36c6b402744a")]},
    # owner 2026-11-21: missing figures not obtainable without much work are deleted (AoPS refuses scripted
    # fetches; Omni-MATH gives no year or number to look them up)
    "HARP 1985 AIME 6": "question 29991, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Triangle ABC cut by three cevians through an interior point into six triangles, with the areas 84, 35, 30, 40 marked on four of them",
    "HARP 1985 AIME 15": "question 29995, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: A 12x12 square cut into a corner triangle A and pentagon B, and the net with the six pieces attached around a regular hexagon",
    "HARP 1987 AIME 6": "question 30093, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Rectangle ABCD with X,Y on AB and Z,W on CD, interior points P,Q with PQ||AB, and the five segments PX, PW, PQ, QY, QZ dividing it into four regions",
    "HARP 1996 AIME 1": "question 30499, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: A 3x3 magic square with four entries filled in: x, 19, 96 and 1 in their cells",
    "HARP 1998 AHSME 16": "question 30588, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: A circle with two semicircles of diameters a and b on a common line through its center, with the shaded and unshaded regions marked",
    "HARP 2002 AIME_I 2": "question 30850, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: A rectangle enclosing three staggered rows of 7, 6 and 7 tangent circles, the outer rows tangent to the long sides and the end circles tangent to the short sides",
    "HARP 2002 AIME_I 10": "question 30852, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Right triangle ABC (right angle at B) with bisector AD, segment EF, and G marked as the intersection of AD and EF",
    "HARP 2003 AMC_12A 13": "question 30916, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The four-square polygon outline with the nine numbered edge positions where a fifth square may be attached",
    "HARP 2005 AMC_10A 8": "question 31067, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Square ABCD with a tilted inner square EFGH formed by four congruent right triangles on the sides of ABCD, BE=1 marked along one triangle leg",
    "HARP 2023 AMC_10B 7": "question 32966, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Square ABCD and its 20-degree clockwise rotation EFGH about the center, with vertex labels (E the image of A, ABCD labelled clockwise)",
    "Omni-MATH 128": "question 33164, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The 2n x 2n board with the central 2(i-1) squares removed from rows i and 2n+1-i for i=1..n (two staircase halves meeting at the middle)",
    "Omni-MATH 286": "question 33275, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Triangle ABC with the seven points P1..P7 (I, O, H, L, G, N, K in some order) plotted and labelled",
    "Omni-MATH 464": "question 33417, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Triangle ABC with D on BC, E on AC, and G the intersection of the cevians, with AE=3, CE=1, BD=CD=2, AB=5",
    "Omni-MATH 494": "question 33447, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The specific grid-line figure (shape and grid lines) on which rectangles are counted",
    "Omni-MATH 822": "question 33763, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Two solid lines (rays) meeting at O, with K at distance 2 and T at distance 4 from O and the angle between the lines shown",
    "Omni-MATH 1224": "question 34144, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: A five-row brick wall showing how many bricks each row has and how rows are offset",
    "Omni-MATH 1501": "question 34406, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The calendar-shaped grid of dots from January 1 to December 31 with the allowed adjacencies",
    "Omni-MATH 1815": "question 34690, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Octagon COMPUTER with right/reflex angles, unit sides CO..TE, and the positions of R, E and D on RE",
    "Omni-MATH 2246": "question 35090, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The chocolate bar outline divided into 10 triangles, showing which triangles share edges",
    "Omni-MATH 2639": "question 35480, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Triangle ABC with a semicircle on diameter AB and the shaded region marked",
    "Omni-MATH 2838": "question 35670, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The polygon with its side lengths labelled in terms of x",
    "Omni-MATH 3048": "question 35863, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The first few figures of the sequence: equilateral triangles joined in a strip, each new tile sharing one edge",
    "Omni-MATH 3083": "question 35895, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Six unit rhombi arranged edge to edge in the specific pattern whose outer boundary is measured",
    "Omni-MATH 3770": "question 36505, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The 40x30 sheet with the 10x5 filled rectangle drawn at its specific offsets from the sheet's edges",
    "Omni-MATH 3774": "question 36509, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: Parallelogram ABCD with M the midpoint of AD, segment BM, and K where the bisector of angle C meets BM",
    "Omni-MATH 4034": "question 36702, owner 2026-11-21: missing image not obtainable without much work, so deleted: the figure is missing: The set of small polyomino shapes (e.g. the trominoes / L-shapes) that Alice needs to see in three different colours",
    "Omni-MATH 4143": "question 36779, owner 2026-11-21: missing image not obtainable without much work, so deleted: the keypad figure is a broken placeholder and, with the standard keypad, the key looks wrong",
}
# the rows the imports set aside, fixed by hand (markup slips; pairs applied in order after FIXES, each old
# matched exactly once) or dropped (garbled, truncated, not a problem)
_SET_ASIDE = json.loads(Path(__file__).with_name("answer_sets_fixes.json").read_text(encoding="utf-8"))
HAND_FIXES = {(e["set"], e["number"], e["field"]): [tuple(p) for p in e["fixes"]] for e in _SET_ASIDE["fixes"]}
DROPPED.update(_SET_ASIDE["dropped"])


def display(m: re.Match) -> str:
    """A display's body: no blank lines (a paragraph break stops LaTeX), and the alignment marks a
    Markdown export left escaped (\\& for &, <br> for \\\\) restored."""
    body = re.sub(r"\n\s*\n", "\n", m.group(1).strip())
    return "\\[" + body.replace("\\&", "&").replace("<br>", "\\\\") + "\\]"


ASY_RE = re.compile(r"\s*(?:\\begin\{asy\}.*?\\end\{asy\}|\[asy\].*?\[/asy\])\s*", re.S)
BB_IMG_RE = re.compile(r"\[img\](https?://[^\[\]\s]+)\[/img\]")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)|<img[^>]*>|\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}")
# statements whose figure is drawn in characters from this line to the end (an image is made from it)
ASCII_FIGURES = {("MathArena smt_2025", "22")}
ASCII_ART_RE = re.compile(r"\n[ \t]*_{3,}[ \t]*\n.*\Z", re.S)


def figure_name(block: str, kind: str = "asy") -> str:
    """The image (in TEXIMAGES, without .png) drawn from an Asymptote block or a character figure."""
    return f"{kind}-" + hashlib.sha1(block.strip("\n" if kind == "ascii" else None).encode("utf-8")).hexdigest()[:16]


def drawn(name: str) -> bool:
    return (TEXIMAGES / f"{name}.png").exists()


def undrawn_asy(text: str) -> str:
    """The Asymptote blocks of a source text that have no image yet (they wait in FIGURES_PATH)."""
    return "\n\n".join(m.group(0).strip() for m in ASY_RE.finditer(text) if not drawn(figure_name(m.group(0))))


def asy_figure(m: re.Match) -> str:
    name = figure_name(m.group(0))
    return f"\n\n{GRAPHIC.format(name)}\n\n" if drawn(name) else "\n\n"


def linked_image(m: re.Match) -> str:
    """An AoPS [img] link: the image, saved as img-<sha1 of the URL>, where it has been downloaded."""
    name = figure_name(m.group(1), "img")
    return f"\n\n{GRAPHIC.format(name)}\n\n" if drawn(name) else m.group(0)


def to_latex(text: str) -> str:
    """The statement in the bank's LaTeX. An Asymptote figure (neither renderer draws it) becomes its
    image where one has been drawn (owner 2026-11-21: TeX Live's Asymptote with the AoPS olympiad and
    cse5 modules, on white) and is taken out otherwise; load() keeps the code of an undrawn one. Figures
    are replaced first, on the source text, so an image is named by the hash of its block as given."""
    t = BB_IMG_RE.sub(linked_image, ASY_RE.sub(asy_figure, text))
    t = t.replace("\r\n", "\n").replace("\\hdots", "\\dots").strip()  # no \hdots in KaTeX
    t = re.sub(r"\$\$(.+?)\$\$", lambda m: "\\[" + m.group(1).strip() + "\\]", t, flags=re.S)
    t = re.sub(r"\\\[(.+?)\\\]", display, t, flags=re.S)
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    out, items, depth = [], [], 0
    for line in t.split("\n") + [""]:
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m and depth == 0:  # a Markdown bullet; inside a display, "- & -" is a row of an array
            items.append(m.group(1))
            continue
        if items:
            out += ["\\begin{itemize}"] + [f"\\item {x}" for x in items] + ["\\end{itemize}"]
            items = []
        out.append(line)
        depth += line.count("\\[") - line.count("\\]")
    return pdf_safe(re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip())


CHAMP = "Concept and Hint-Annotated Math Problems (CHAMP)"  # github.com/YilunZhou/champ-dataset (MIT)
CHAMP_TOPICS = {"Number-Theory": "Number Theory", "Inequality": "Inequalities", "Polynomial": "Polynomials",
                "Sequence": "Sequences", "Combinatorics": "Combinatorics"}
CHAMP_SYMBOLS = {"≥": r"\ge ", "≤": r"\le ", "±": r"\pm ", "−": "-", "∤": r"\nmid ", "∈": r"\in ", "≠": r"\ne ",
                 "≡": r"\equiv ", "·": r"\cdot ", "→": r"\to ", "∞": r"\infty ", "π": r"\pi ", "⊆": r"\subseteq ",
                 "≈": r"\approx ", "∓": r"\mp ", "∘": r"\circ ", "∉": r"\notin "}
# (problem, hint or fact) left out: it gives the answer away (the pipeline's hint-leak check)
CHAMP_SKIP = {("P_Number-Theory_42", "H_Number-Theory_42_2"), ("P_Polynomial_20", "C_infinite_zeros")}
CHAMP_TEXT_FIXES = {"H_Sequence_47_1": [("x_1*y*1*z_1", "x_1*y_1*z_1")]}  # slips in the dataset
CHAMP_FUNCS = ("arctan", "gcd", "sum", "prod", "tan", "cos", "sin", "min", "max", "log", "ln")
CHAMP_WORDS = ("and", "or", "for", "if", "then", "where", "with", "all", "not", "is")


def _group(s: str, i: int) -> tuple[str, int]:
    """The text of the parenthesised group starting at s[i] == '(' and the index after it."""
    depth = 0
    for j in range(i, len(s)):
        depth += {"(": 1, ")": -1}.get(s[j], 0)
        if depth == 0:
            return s[i + 1:j], j + 1
    return s[i + 1:], len(s)


def champ_math(m: str) -> str:
    """CHAMP's plain-text (AsciiMath-like) math in LaTeX: its symbols, sqrt(..), floor(..), mod,
    function names, ^(..) and _(..) groups, multi-digit exponents and subscripts, set braces,
    * as a centred dot, "a | b" as divides, and English words as text."""
    for k, v in CHAMP_SYMBOLS.items():
        m = m.replace(k, v)
    m = m.replace("->", r"\to ").replace("<=", r"\le ").replace(">=", r"\ge ").replace("!=", r"\ne ")
    m = m.replace("{", r"\{").replace("}", r"\}").replace("%", r"\%").replace("#", r"\#").replace("&", r"\&")
    m = _champ_groups(m)  # the parenthesised groups first; the token rules below then run once
    # a power tower 2^2^...^2 nests from the right; x^e_i is x^{e_i}
    m = re.sub(r"(?:[A-Za-z0-9]+|\.\.\.)(?:\^(?:[A-Za-z0-9]+|\.\.\.)){2,}", _champ_tower, m)
    m = re.sub(r"\^([A-Za-z0-9])_([A-Za-z0-9])", r"^{\1_\2}", m)
    m = re.sub(r"([\^_])(\d{2,})", r"\1{\2}", m)
    m = re.sub(r"_([a-z]{2})(?![a-zA-Z{])", r"_{\1}", m)
    m = re.sub(r"\(mod ([^()]+)\)", r"\\pmod{\1}", m)
    m = re.sub(r"(?<![\\a-zA-Z])mod(?![a-zA-Z])", r"\\bmod ", m)
    m = re.sub(r"(?<![\\a-zA-Z])(" + "|".join(CHAMP_FUNCS) + r")(?![a-zA-Z])", r"\\\1 ", m)
    m = re.sub(r"(?<![\\a-zA-Z])pi(?![a-zA-Z])", r"\\pi ", m)
    m = re.sub(r"(?<![\\a-zA-Z])(" + "|".join(CHAMP_WORDS) + r")(?![a-zA-Z])", r"\\text{ \1 }", m)
    m = re.sub(r"\s\|\s", r" \\mid ", m)
    m = m.replace("*", r"\cdot ")
    return m.strip()


def _champ_tower(mt: re.Match) -> str:
    parts = [r"\cdots" if p == "..." else p for p in mt.group(0).split("^")]
    out = parts[-1]
    for p in reversed(parts[:-1]):
        out = p + "^{" + out + "}"
    return out


def _champ_groups(m: str) -> str:
    """sqrt(..) -> \\sqrt{..}, floor(..) -> \\lfloor .. \\rfloor, ^(..) / _(..) -> ^{..} / _{..}, nested."""
    out, i = [], 0
    while i < len(m):
        if m.startswith(("sqrt(", "floor("), i):
            name = "sqrt" if m.startswith("sqrt", i) else "floor"
            body, i = _group(m, i + len(name))
            body = _champ_groups(body)
            out.append(r"\sqrt{" + body + "}" if name == "sqrt" else r"\lfloor " + body + r" \rfloor ")
            continue
        if m[i] in "^_" and i + 1 < len(m) and m[i + 1] == "(":
            mark = m[i]
            body, i = _group(m, i + 1)
            out.append(mark + "{" + _champ_groups(body) + "}")
            continue
        out.append(m[i])
        i += 1
    return "".join(out)


def champ_text(t: str) -> str:
    """A CHAMP text (math between @@ marks) in the bank's LaTeX: math in \\( \\), the rest escaped."""
    parts = re.split(r"@@(.*?)@@", t.strip(), flags=re.S)
    out = []
    for k, p in enumerate(parts):
        if k % 2:
            out.append(r"\(" + champ_math(p) + r"\)")
        else:
            out.append(re.sub(r"([%&#$_^])", r"\\\1", p).replace("~", r"\textasciitilde{}"))
    return "".join(out)


def answer_latex(a: str) -> str:
    a = str(a).strip()
    if not a or "$" in a or a.startswith(("\\(", "\\[")) or not re.search(r"[\\^_{}]", a):
        return a
    return f"${a}$"


def shingles(t: str) -> set:
    w = " ".join(re.sub(r"\\[a-zA-Z]+|[^a-z0-9]", " ", t.lower()).split()).split()
    return {" ".join(w[i:i + 5]) for i in range(max(len(w) - 4, 1))}


def load(matharena: Path, answerbench: Path, harp: Path | None = None, omni: Path | None = None,
         umath: Path | None = None, champ: Path | None = None) -> list[dict]:
    rows = []
    for name, (source, sub) in MATHARENA.items():
        data = json.loads((matharena / f"{name}.json").read_text(encoding="utf-8"))
        for r in data:
            i = int(r["problem_idx"])
            rows.append({"set": f"MathArena {name}", "idx": str(i), "source": source, "subsource": sub(i, len(data)),
                         "latexcode": to_latex(r["problem"]), "answer": answer_latex(r["answer"]), "orig": "",
                         "asy": undrawn_asy(r["problem"])})
    for name in APEX_SETS:
        for r in json.loads((matharena / f"{name}.json").read_text(encoding="utf-8")):
            if r["source"] not in APEX:
                raise SystemExit(f"MathArena {name} {r['problem_idx']}: no source for {r['source']!r} in APEX")
            source, sub = APEX[r["source"]]
            rows.append({"set": f"MathArena {name}", "idx": str(r["problem_idx"]), "source": source,
                         "subsource": sub + ("" if source == "MathArena APEX" else APEX_TAG),
                         "latexcode": to_latex(r["problem"]), "answer": answer_latex(r["answer"]), "orig": r["source"],
                         "asy": undrawn_asy(r["problem"])})
    if harp:
        member = zipfile.ZipFile(harp).read("HARP.jsonl").decode("utf-8")
        for r in (json.loads(x) for x in member.splitlines() if x.strip()):
            source, contest = HARP_CONTESTS[r["contest"]]
            n = r["number"]
            sub = f"{str(r['year']).replace('_', ' ')}, {contest + ', ' if contest else ''}Problem {n}"
            rows.append({"set": "HARP", "idx": f"{r['year']} {r['contest']} {n}", "source": source, "subsource": sub,
                         "latexcode": to_latex(r["problem"]), "answer": answer_latex(r["answer"]), "orig": "",
                         "asy": undrawn_asy(r["problem"]),
                         "ref_solution": r.get("solution_1") or ""})
    if umath:  # a problem with a figure carries it as a PNG: written to the image folder on --apply
        import pyarrow.parquet as pq
        for r in pq.read_table(umath).to_pylist():
            name = f"umath-{r['uuid']}"
            # the dataset read some TeX commands as escapes: \frac -> form feed + "rac", \theta and
            # \tan -> tab + "heta", \right -> carriage return + "ight" (25 places): restored
            for f in ("problem_statement", "golden_answer"):
                r[f] = re.sub(r"[\x0c\t\r](?=[A-Za-z])", lambda m: {"\x0c": "\\f", "\t": "\\t", "\r": "\\r"}[m.group(0)], r[f])
            tex = to_latex(r["problem_statement"])
            if r["has_image"]:
                tex += "\n\n" + GRAPHIC.format(name)
            key = re.sub(r"^\s*the final answer\s*:\s*", "", r["golden_answer"].strip(), flags=re.I)
            rows.append({"set": UMATH, "idx": r["uuid"], "source": UMATH,
                         "subsource": f"{UMATH_SUBJECTS[r['subject']]}, problem {r['uuid'][:8]}",
                         "latexcode": tex, "answer": answer_latex(to_latex(key)), "orig": "", "asy": "",
                         "image": (name, r["image"]) if r["has_image"] else None})
    if champ:  # problems adapted from Engel, with their own solution, hints and named facts (owner 2026-11-21)
        data = json.loads(champ.read_text(encoding="utf-8"))
        hints, facts = data["hints"], data["concepts"]
        for hid, fixes in CHAMP_TEXT_FIXES.items():
            for old, new in fixes:
                if hints[hid]["_raw_text"].count(old) != 1:
                    raise SystemExit(f"CHAMP fix {hid}: expected one {old!r}")
                hints[hid]["_raw_text"] = hints[hid]["_raw_text"].replace(old, new)
        for pid, p in data["problems"].items():
            p["ch_list"] = [c for c in p["ch_list"] if (pid, c) not in CHAMP_SKIP]
            tiers = [champ_text(hints[c]["_raw_text"]) for c in p["ch_list"] if c in hints]
            if len(tiers) > 3:  # the bank keeps at most 3 tiers: the later hints go in the third
                tiers = tiers[:2] + [" ".join(tiers[2:])]
            used = [facts[c] for c in p["ch_list"] if c in facts]
            if used:  # the named facts the problem uses, in the last tier
                fact = " ".join(f"Useful fact{' (' + c['name'] + ')' if c['name'] else ''}: {champ_text(c['_raw_text'])}"
                                for c in used)
                if tiers:
                    tiers[-1] += " " + fact
                else:
                    tiers = [fact]
            cat, num = pid.split("_", 1)[1].rsplit("_", 1)
            rows.append({"set": "CHAMP", "idx": pid, "source": CHAMP, "orig": "", "asy": "", "ref_solution": "",
                         "subsource": f"{CHAMP_TOPICS[cat]}, problem {num} (adapted from Engel's Problem-Solving Strategies)",
                         "latexcode": champ_text(p["_raw_text"]), "answer": champ_text(p["_raw_answer"]),
                         "solution": "\n\n".join(champ_text(s["_raw_text"]) for s in p["solution"]["steps"]),
                         "hints": tiers[0] if tiers else None,
                         "more_hints": json.dumps(tiers[1:], ensure_ascii=False) if len(tiers) > 1 else None})
    if omni:
        for k, r in enumerate(json.loads(x) for x in omni.read_text(encoding="utf-8").splitlines() if x.strip()):
            label = r["source"]
            name = OMNI_NAMES.get(label) or label.replace("_", " ").strip().title()
            rows.append({"set": "Omni-MATH", "idx": str(k), "source": OMNI, "subsource": f"{name} (year not given)",
                         "latexcode": to_latex(r["problem"]), "answer": answer_latex(r["answer"]), "orig": label,
                         "asy": undrawn_asy(r["problem"]) or "\n\n".join(IMAGE_RE.findall(r["problem"])),
                         "ref_solution": r.get("solution") or ""})
    for r in csv.DictReader(open(answerbench, encoding="utf-8")):
        orig = (r.get("Source") or "").strip()
        rows.append({"set": "IMO-Bench AnswerBench v2", "idx": r["Problem ID"], "source": ANSWERBENCH,
                     "subsource": r["Problem ID"] + (f", adapted from {orig}" if orig else ""),
                     "latexcode": to_latex(r["Problem"]), "answer": answer_latex(r["Short Answer"]), "orig": orig,
                     "asy": undrawn_asy(r["Problem"])})
    for r in rows:
        r.setdefault("ref_solution", "")
        r["potd"] = f"{r['set']} {r['idx']}"  # for check(); CHAMP rows bring their own solution and hints
        for fld in ("hints", "more_hints", "solution"):
            r.setdefault(fld, None)
        if (r["set"], r["idx"]) in ASCII_FIGURES:
            m = ASCII_ART_RE.search(r["latexcode"])
            if not m:
                raise SystemExit(f"{r['potd']}: no character figure found")
            r["asy"], r["latexcode"] = "ASCII art:\n" + m.group(0).strip("\n"), r["latexcode"][:m.start()].rstrip()
            if drawn(name := figure_name(m.group(0), "ascii")):  # drawn in a monospaced font
                r["asy"], r["latexcode"] = "", r["latexcode"] + "\n\n" + GRAPHIC.format(name)
        for fld in ("latexcode", "answer"):
            for old, new in FIXES.get((r["set"], r["idx"], fld), []):
                # a source that already ends with the fix is not fixed twice (a whole-answer fix such as
                # 11 -> 1 is not mistaken for one)
                if r[fld].count(old) != 1 or (fld == "answer" and r[fld].endswith(new) and r[fld] != old):
                    raise SystemExit(f"FIX {r['potd']} {fld}: expected one {old!r}")
                r[fld] = r[fld].replace(old, new)
            for old, new in HAND_FIXES.get((r["set"], r["idx"], fld), []):
                if r[fld].count(old) != 1:
                    raise SystemExit(f"HAND FIX {r['potd']} {fld}: expected one {old!r}")
                r[fld] = r[fld].replace(old, new)
    return rows


def duplicates(rows: list[dict], conn: sqlite3.Connection) -> dict[int, tuple[int, float]]:
    """Row index -> (bank question id, share) for problems the bank already has."""
    bank = list(conn.execute("SELECT question_id, latexcode, latex_hash FROM questions"))
    by_hash = {h: q for q, _, h in bank}
    index = collections.defaultdict(set)
    for q, t, _ in bank:
        for g in shingles(t):
            index[g].add(q)
    out = {}
    for k, r in enumerate(rows):
        if latex_hash(r["latexcode"]) in by_hash:
            out[k] = (by_hash[latex_hash(r["latexcode"])], 1.0)
            continue
        g = shingles(r["latexcode"])
        hits = collections.Counter(q for x in g for q in index.get(x, ()))
        if hits:
            q, n = hits.most_common(1)[0]
            if n / len(g) >= NEAR:
                out[k] = (q, round(n / len(g), 2))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--matharena", type=Path, required=True)
    p.add_argument("--answerbench", type=Path, required=True)
    p.add_argument("--harp", type=Path, help="HARP.jsonl.zip (github.com/aadityasingh/HARP)")
    p.add_argument("--omni", type=Path, help="Omni-MATH test.jsonl (huggingface.co/datasets/KbsdJames/Omni-MATH)")
    p.add_argument("--umath", type=Path, help="U-MATH test parquet (huggingface.co/datasets/toloka/u-math)")
    p.add_argument("--champ", type=Path, help="CHAMP v0.json (github.com/YilunZhou/champ-dataset)")
    p.add_argument("--model", default=OPUS)
    p.add_argument("--effort", default="high")
    p.add_argument("--dump", type=Path, help="write the rows to import as JSON")
    g = p.add_mutually_exclusive_group(required=True)
    p.add_argument("--set-aside", action="store_true", help="leave out rows that fail the checks (listed in SET_ASIDE_PATH)")
    p.add_argument("--exclude", type=Path, help="with --set-aside: JSON {row label: why} of rows the render checks failed")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = p.parse_args()

    rows = load(a.matharena, a.answerbench, a.harp, a.omni, a.umath, a.champ)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    dup = duplicates(rows, conn)
    conn.close()
    for k, (q, share) in sorted(dup.items()):
        print(f"in the bank: {rows[k]['potd']} = question {q} ({share:.0%})")
    new = [r for k, r in enumerate(rows) if k not in dup and r["potd"] not in DROPPED]
    problems = check(new)
    for x in problems:
        print("CHECK", x)
    if a.set_aside:  # slips in the source data: these rows wait for a hand fix
        excluded = json.loads(a.exclude.read_text(encoding="utf-8")) if a.exclude else {}
        why = {r["potd"]: check([r]) or [excluded[r["potd"]]] for r in new if check([r]) or r["potd"] in excluded}
        SET_ASIDE_PATH.write_text(json.dumps([dict(r, problems=why[r["potd"]]) for r in new if r["potd"] in why],
                                             ensure_ascii=False, indent=1), encoding="utf-8")
        new = [r for r in new if r["potd"] not in why]
        print(f"set aside for a hand fix: {len(why)} rows in {SET_ASIDE_PATH}")
        problems = check(new)
    print(json.dumps({"rows": len(rows), "in_bank": len(dup), "to_add": len(new), "check_problems": len(problems),
                      "by_set": collections.Counter(r["set"] for r in new),
                      "answers_wrapped": sum(r["answer"].startswith("$") for r in new),
                      "asymptote_figures_kept_aside": [r["potd"] for r in new if r["asy"]]}, default=dict))
    if a.dump:
        a.dump.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return
    if problems:
        raise SystemExit("fix the check problems first")
    backup_db("answer-sets")
    for r in new:  # U-MATH figures, before their questions exist
        if r.get("image"):
            name, data = r["image"]
            assert data.startswith("data:image/png;base64,"), name
            (TEXIMAGES / f"{name}.png").write_bytes(base64.b64decode(data.split(",", 1)[1]))
    conn = sqlite3.connect(DB_PATH)
    added = []
    try:
        existing = {h for (h,) in conn.execute("SELECT latex_hash FROM questions")}
        for r in new:
            h = latex_hash(r["latexcode"])
            if h in existing:  # two rows of these sets with the same text
                continue
            cur = conn.execute(
                """
                INSERT INTO questions (topic, branch, subtopic, latexcode, type, in_syllabus,
                                       source, subsource, answer, solution, hints, more_hints, latex_hash)
                VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (UNCATEGORIZED, UNCATEGORIZED, UNCATEGORIZED, r["latexcode"], r["source"], r["subsource"], r["answer"],
                 r["solution"], r["hints"], r["more_hints"], h),
            )
            existing.add(h)
            added.append((cur.lastrowid, r))
        conn.commit()
    finally:
        conn.close()
    with MAP_PATH.open("a" if MAP_PATH.exists() else "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["question_id", "set", "number", "original_source"])
        w.writerows((q, r["set"], r["idx"], r["orig"]) for q, r in added)
    doc = json.loads(ASSIGNMENTS.read_text(encoding="utf-8")) if ASSIGNMENTS.exists() else {
        "note": "Final-answer sets imported by app/tools/import_answer_sets.py (answer key, no solutions), with the "
                "model and effort that solve them. Listing a question here puts it in run_sub.py's scope.",
        "questions": {}}
    # a question whose figure is still Asymptote code waits for its image before it is solved
    doc["questions"].update({str(q): {"model": a.model, "effort": a.effort} for q, r in added if not r["asy"]})
    ASSIGNMENTS.write_text(json.dumps(doc, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    figures = json.loads(FIGURES_PATH.read_text(encoding="utf-8")) if FIGURES_PATH.exists() else {}
    figures.update({str(q): {"set": r["set"], "number": r["idx"], "asy": r["asy"]} for q, r in added if r["asy"]})
    FIGURES_PATH.write_text(json.dumps(figures, ensure_ascii=False, indent=1), encoding="utf-8")
    solutions = json.loads(SOLUTIONS_PATH.read_text(encoding="utf-8")) if SOLUTIONS_PATH.exists() else {}
    solutions.update({str(q): {"set": r["set"], "number": r["idx"], "solution": r["ref_solution"]}
                      for q, r in added if r["ref_solution"]})
    SOLUTIONS_PATH.write_text(json.dumps(solutions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"added={len(added)} ids {added[0][0] if added else '-'}..{added[-1][0] if added else '-'}; "
          f"map={MAP_PATH}; assignments={ASSIGNMENTS} ({len(doc['questions'])} questions); "
          f"figures to draw: {sorted(int(q) for q in figures)} in {FIGURES_PATH}")


if __name__ == "__main__":
    main()
