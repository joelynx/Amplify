# Proposed subsource format

The source is the competition's full name only, from `competition_map.csv`. Everything else in the sheet's "Source" cell goes into the subsource. Every row's proposed subsource is in `row_assignments.csv`; a script generated them, so they are a draft.

Format: comma-separated, in this order:

1. **Year.** Use the year as written; a two-year span becomes `2001/02`. If a contest has no year but has an edition number, use that instead (`4th edition`).
2. **Stage, paper or division,** as the contest names it: `Day 1`, `Test 4`, `Round 2`, `Grade 10`, `Fall`, `Senior A-6`, `AIME II`, `AMC 10A`, `Cayley`, `Individual`, `set by Australia for UK`.
3. **Problem label.** Numbered problems become `Problem N`, and the sheet's "of 6" is dropped. Shortlist codes (`A3`, `G2`, `N8`) and Putnam codes (`A5`, `B6`) are kept as they are.
4. **Edit marks,** appended in brackets when the sheet records them: `(adapted)`, `(modified)`, `(generalised)`.

Books use the printed reference (`10.0.11`, `Chapter 2, Problem 27`). Rows sent to the Math Olympiad Discord Server keep their original label as the subsource (`Folklore`, `Broken Chord Theorem`), so that information is not lost.

| # | Source cell in the sheet | Source (full name) | Subsource |
|---|---|---|---|
| 1 | `2024 IMOSL, C5` | International Mathematical Olympiad Shortlist | 2024, C5 |
| 2 | `2019 China TST Test 4, P2 of 6` | China Team Selection Test | 2019, Test 4, Problem 2 |
| 3 | `2017 Irish MO, Day 1, P1 of 5` | Irish Mathematical Olympiad | 2017, Day 1, Problem 1 |
| 4 | `2008 Putnam, A5` | William Lowell Putnam Mathematical Competition | 2008, A5 |
| 5 | `2002 AIME II, P7 OF 15` | American Invitational Mathematics Examination | 2002, AIME II, Problem 7 |
| 6 | `2001/02 BMO1, P1 of 5` | British Mathematical Olympiad Round 1 | 2001/02, Problem 1 |
| 7 | `2015 UK IMOK, C6` | Intermediate Mathematical Olympiad and Kangaroo | 2015, Cayley, Problem 6 |
| 8 | `2016 ToT Fall, Senior A-6` | Tournament of Towns | 2016, Fall, Senior A-6 |
| 9 | `2025 MEMO, I2 of 4` | Middle European Mathematical Olympiad | 2025, Individual, Problem 2 |
| 10 | `2023 AUS → UNK F3, P2 of 3` | UK-Australia Pre-IMO Camp Exchange Paper | 2023, set by Australia for UK, Problem 2 |
| 11 | `2014 Taiwan TST1 Quiz 2, P1` | Taiwan Team Selection Test | 2014, Round 1, Quiz 2, Problem 1 |
| 12 | `2017 Serbia MO, P4 of 6 (Modified)` | Serbian Mathematical Olympiad | 2017, Problem 4 (modified) |
| 13 | `4th AGO, P5 of 6` | Amateur Geometer's Olympiad | 4th edition, Problem 5 |
| 14 | `PST 10.0.11` | Di Pasquale, Do and Mathews' Problem Solving Tactics | 10.0.11 |
| 15 | `Broken Chord Theorem` | Math Olympiad Discord Server | Broken Chord Theorem |

More cases from the same rules:

- `2024 CMO, Pascal P20` gives **Pascal Mathematics Contest**, `2024, Problem 20`. This is the Waterloo CEMC contest, not the Canadian MO.
- `2010 AMC 10A, P24 of 25` gives **American Mathematics Competitions**, `2010, AMC 10A, Problem 24`.
- `2023 ICMC Round 1, P3 of 6` gives **Imperial-Cambridge Mathematics Competition**, `2023, Round 1, Problem 3`.
- `2025 IGO Advanced, P3 of 5` gives **Iranian Geometry Olympiad**, `2025, Advanced, Problem 3`.
- `Folklore` gives **Math Olympiad Discord Server**, `Folklore`.

Known rough edges in the generated subsources:

- A few rows have no problem number in the sheet at all (e.g. `2013 HMMT`, `1990 Romanian MO`); their subsource is just the year.
- A few joined labels are kept as written, such as `Round 3, Iindependent Study 1-N` (sic) and `Winter /2` for `NIMO Winter 2014/2`.
