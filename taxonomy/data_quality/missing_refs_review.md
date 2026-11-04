# Rewrites to review (judgement calls the agents flagged)

## Went beyond the dangling reference
- 18672, 18673, 18675 (White): restored a temperature missing from the table (six values, five temperatures).
- 18670 (White): added the book's air constants n ≈ 0.7, S ≈ 110 K so parts a-b are solvable.
- 24560 (Dekking): 0.542 -> 0.524 (book typo; exact Gamma(30,1/2) cdf at 60 is 0.5243).
- 21853 (de Lange): sign fix in an inlined integral, πk/(2(−E)√(−2mE)) (book prints a negative value).
- 21863 (de Lange): "In (2) and (4)" -> "In (b) and (d)" (part tags missing in DB).
- 24474, 25037: small wording fixes after the pointer was removed.

## Added an assumption or a result that makes the question easier
- 24408, 24409 (Dekking): "fail independently" (the binomial model of Section 1.4).
- 21876-21878, 21880 (de Lange): "use the results of Questions ..." -> the results are inlined, some are steps.
- 25085 (Blitzstein): Folded Normal PDF 2φ(y) given.
- 22426, 22428 (Øksendal Ex 6.2, 6.4): Kalman-Bucy Riccati equation stated, makes part a) short.
- 22427 (Øksendal Ex 6.3): added "r > 0" (needed by the stated limit and hint).
- 22430 (Øksendal Ex 6.6): book's Example 6.2.9 inconsistent; stated as E[(X₀ − X̂₀)²] = a².
- 22410, 22412 (Øksendal): integrating-factor hint adapted to each equation (e^{−μt}, e^{t}).
- 22405 (Øksendal): extraction error B_{t_{k-t}} -> B_{t_k − t} fixed.

## Stated from general knowledge (Probability and Random Processes not available)
- Grimmett & Stirzaker 9729, 9830, 9936, 10052 (10052 least certain).
- Grimmett & Stirzaker 10088, 10100, 10101, 10202, 10215 (notation inferred), 10298, 10339.
- Hints that now give away much of the solution: 10168 (Cauchy facts), 10288 (Laplace transform e^{−√(2s)}).
- 10287: hint gives the integral instead of 5.12.18(e) (which is what the question asks); also fixed "LÃ©vy" -> "Lévy".

## Figures not from the PDF
- 18721, 18723 (White Fig. C1.6): image taken from 18721's own solution field (not in the 4th-ed PDF).
- 18761 (White Fig. P2.39): image from the question's own solution field (P2.39 in the 4th ed. is a different problem).
- 18754, 18755 (White): a neighbouring problem's label inside the crop box was painted out in white.
- 18791, 18797, 18807, 18848 (White): figures from the questions' own solution fields (not in the 4th ed.).
- 19068 (Fig. P3.183), 19075 (Fig. C3.5): from their own solution fields; 19069 reuses 19068's P3.183
  figure (19069's own solution has none); that drawing is crude at the bottom (inlet looks detached).
  18791's drawing has an "F?" arrow (part of the problem drawing); 18807 shades the water above gate BC.
- 18836 (White): cited "Fig. P2.113" (buoy upright); used the aground drawing (book Fig. P2.115) and relabelled.
- 18846 (White): added "take the balloon's weight to be that of its material alone" to agree with the stored
  solution (Prob. 2.111 has a 1300 N payload the solution ignores).
- 18788 (White): extraction loss "q" -> θ fixed; 18812: "Fig. P2. 91" -> "Fig. P2.91".
- 18999 (White): Example 3.15 sprinkler drawing (Fig. 3.14) includes the example's control-volume outline and
  "V2 = V0 i − Rω i" label; a little of the analysis shows.
- 19005 (White): book's P3.78 says "absolute velocity V1"; figure and stored solution use V2, written as V2.
  18964 has the same typo and KEPT V1 (inconsistent with 19005; pick one).
- 18942 (P3.56), 18943 (P3.57) (White): figures from own solution fields (18942's has x-y axes, no results).
- 18986, 18987, 18989, 18995 (White, Prob. 3.35 rocket): stated exhaust speed 1150 m/s and mass flow
  11.8 kg/s (the stored solutions' values), so the student no longer computes the mass flow.
- 18984 (White): added "from rest" (in the book, assumed by the solution).
- 18991, 18992 (White): "m = 0.05 kg/s" -> ṁ (dot lost in extraction).
- 18979-18981, 18983, 18991, 18992 (White): figures of the problem whose setup was inlined, added although
  these questions didn't cite a figure.
- 18987 (White): air density vs altitude unstated; solution uses the standard atmosphere.
- 19256 (White): DB said "Solve Prob. 5.50" (wrong; the book and stored solution mean 5.49, steel sphere in
  glycerin); inlined that.
- 19239 (White V-notch, Fig. P5.69): figure exists nowhere (PDF or DB); pointer deleted since the text defines
  everything. Arguably "unresolved".
- 19287 (White, Tinyland): figure from its own solution field (not in the 4th ed.).
- 19149 (P4.74), 19162 (P4.87), 19170 (C4.2) (White): figures from own solution fields.
- 19210 (White, slanted plates C1.1): figure taken from question 18718's text, and the exact result
  ρgh(L − h tan α) = 2Y cos(θ − α) from 18718's stored solution.
- 19129 (White): "Where in this chapter are the streamlines plotted?" -> states they are those of Fig. E4.7
  (already in the question), labelled in multiples of a = 3U/L².
- 19166 (White): Fig. 4.16a not cropped (shows the Newtonian answer profile); "as in the sketch".
- 19212 (White): ρc_p dT/dt as the stored solution (4th ed. prints c_v).
- 19130 (White): DB "v_θ ≡ 0" where the book has v_φ ≡ 0 (not touched).
- 19382 (P6.117), 19390 (P6.125), 19313 (P6.47 gutter) (White): figures from own solution fields.
- 19323, 19338 (White, pool): referenced pool problem (DB 19320) not in the PDF; setup described from 19320's DB
  text, without its figure or answer.
- 19340 (White): Fig. P6.67 crop still shows the base problem's "Water at 20°C", "D = 1/2 in"; the question overrides both.
- 19362 (White): "see Fig. P6.28 for an example" (later-edition number) redirected to the question's own Fig. P6.96.
- 19409 (White): DB "Fig. 6.41" = 4th-ed. Fig. 6.40 (orifice C_d chart); added the C_d definition; Example 5.8
  described in one clause. 19415: DB "Fig. 6.40a" = 4th-ed. Fig. 6.39a.
- 19393 (White): figure shows 2 ft³/s at A and D, which the question makes unknown; added "(instead of the 2 ft³/s shown)".
- 19426, 19427 (White P6.161): figure from 19426's own solution field.
- 19455 (White): part (d) needs the pitot distance, so stated x ≈ 0.91 m (P7.20's answer) and SG = 0.827; the
  figure still shows "20 m/s" although the question makes the velocity unknown.
- 19433 (White): (1 + 1.33√f)^-1 from the PDF; the solution uses 1.3 (26.4 vs 26.5 m/s).
- 19542, 19543, 19544 (White Fig. P7.108): the 4th-ed. PDF prints "Figure Unavailable"; used the clean copy in
  question 19541 (Prob. 7.108 itself).
- 19484 (White): existing Fig. P7.50 moved to the end (it split a sentence). 19495: chart pointer replaced by words.
- 19499 (White): Natick URL removed (\href does not compile: hyperref is not in the app preamble).
- 19264 (White): replaced the question's existing uncaptioned sketch with the book's Fig. P4.80 (adds the z axis).
- White chapter 6: DB problem numbers run 8 ahead of the 4th ed. (DB P6.19 = book P6.27); figures matched by
  content and captioned with the DB's labels.

## Appendix-table values added (needed to solve, match the stored solution)
- 18732 (White): seawater ρ ≈ 1025 kg/m³, B ≈ 2.33E9 Pa (Table A.3), plus 1 atm at the surface.

## Book errors found (left unchanged)
- 21973 (de Lange Q13.21): the question's own eq. (2) is wrong in the book; dividing Q13.20's horizontal-drive
  equation by ω0² gives sin θ − (b/ℓ)(ω/ω0)² sin(ωτ/ω0) cos θ. Part (a) "show that" can't be done as printed.

- 22440 (Øksendal Ex 6.16) and 22439 (Ex 6.15): with ξ_0 = x, part b)'s E[μ|N_t] formula only holds for x = 0
  (needs ξ_t − x); probable book erratum.

- 21896 (de Lange Q11.7): restored the missing initial position of body 3, r₃(0) = (0, 45/40, 0).
- 21962 (de Lange Q13.10): period written T = (T₀/π)I(ε) so the question's eq. (1) is consistent.
- 21952 (de Lange Q12.30): added g = 9.8 m/s² and the initial-velocity convention.

- 10426 (Stirzaker): book and DB say P(Z_1 = k) = 2^{-k} (not a distribution); the book's solution uses 2^{-k-1}.

- 10756 (Stirzaker): cited Problem 8.10.7 says "rate 1" but uses λ (used λ); the identity
  λF* = r*(θ−λ+λF*) the question asks for did not check out for exponential claims; may be a book error.

- Som (corrected to match the stored solutions): 18302, 18303 β = 3×10⁴ -> 3×10⁻⁴ K⁻¹; 18306 k = 0.28 -> 0.028;
  18306, 18307 McAdams laminar n = 1/4 (book prints 1/3); 18301 Sieder-Tate with Pr^{1/3} (book prints Pr^0.3).
- 18383 (Som): shape factor row inlined as printed; stored answer 0.2 kW uses the ln(D/r) form (cosh⁻¹ gives 0.16).
- 18304 (Som): u_x formula as the stored solution uses it (the book's integral solution gives a different value).
- 18424 (Som): deleted a stray chunk of chapter-6 text (extraction spill); ρ, μ in Re read as air's (no solution).
- Som additions: 18271 node spacing 100 mm (from Ex. 4.13's solution); 18302, 18303 transition at GrPr ≈ 10⁹.

## Still not fully self-contained after the rewrite
- 18301 (Som): needs SO₂ properties, which the book doesn't have.
- 18300 (Som): needs a thermal-entry Nu chart (book Fig. 7.10), not added.
- 18306 b, c (Som): need horizontal-plate correlations the question doesn't cite.
- 18441, 18442 (Som): need air-property lookups.

- White still needing table data the text doesn't cite: 19499 (parachute C_D ≈ 1.2), 19522 (sign C_D ≈ 1.19),
  19527 (cone C_D vs angle), 19525 (cups C_D ≈ 1.4/0.4), 19538 (turbulent flat-plate friction formula).

## Stored answers that look wrong (not touched)
- 18415 (Som): 5.98 kW/m is half the value from the integrated local relation.
- 18441 (Som): answer implies air at 20 °C, not the 40 °C stated.
- 18458 (Som): stored "1.04 W" looks wrong; the flow is turbulent and the correlation gives ~1.6 kW.
- 18463 (Som): no stored answer reproduces; (a) 97.73 W is close to Churchill-Chu (~100 W), the cited correlation
  gives ~113 W; (b), (c) are exactly 1/4 of the values with L = A/P = 0.1 m (book likely used 0.4 m).
- 18474 (Som): stored answers are 0.965 × Prob. 9.1's vertical-plate answers (≈ 30° tilt); 40° gives 0.936.
- 18471 (Som): Table 8.4 belongs to Eq. (8.64), not (8.39) as the question says; stored 88.97 W doesn't
  reproduce (~99 W with the inner-sphere area).
- 19956 (White): problem in feet, solution talks of m³/s and "Q = 17.05".
- 19969 (White): question says the weir is 1 m high, solution uses y(0) = 0.5 m + H.
- 19997 (White): solution uses water ρ = 1.56 slug/ft³ (should be 1.94).
- 18468 (Som): stored 0.736 kW reproduces only with water properties at 20 °C (film temperature gives 0.95-1.0 kW/m).

## Som choices to confirm
- 18458, 18463: McAdams laminar n = 1/4 (book prints 1/3), as in som-01.
- 18447: Ranz-Marshall kept with the book's 0.66 (usual 0.6), because it reproduces the stored 18.69 °C.
- 18487: question says "nucleate boiling" but cites the film-boiling correlation (9.28); added "take the same
  value in both" for h'_fg so the stored 0.025 follows.
- 18525: the question's "Eq. (7.59c)" is printed as (7.58c) in the book (turbulent average).
- 18463: five-row tabular (two McAdams vertical-plate rows + three horizontal-plate rows of Table 8.1).
- 18482: added the Table 9.1 row C_sf = 0.0130 (water on polished copper), needed but not cited.
- 18464: still doesn't say which correlations to use (stored answers match Eqs. 8.45a and 8.47).

## Unresolved (left unchanged)
- 10499 (Stirzaker, "empires of Theorem (6.12.14)"): model only in Probability and Random Processes.
- 23755 (Strang, "Complete the calculation of A⁻¹ by cofactors that was started in Example 5"): Sec. 5.3's Example 5
  is the box-volume example; closest is Worked Example 5.3 B (A = [2 6 2; 1 4 2; 5 9 0]), which the book finishes
  itself. Probably older-edition numbering; easy rewrite if you accept that matrix.
- 19589 (White half-body, 160/90 kPa at A and B): not in the 4th ed.; the solution-field figure has solution
  construction lines. Could be described in words (A = nose stagnation point, B on the body below the source).
- 19420 (White): the 4th ed.'s Fig. 6.42 gives 1.5×10^5 < Re_D < 2.0×10^6, the stored solution uses 2.0×10^5
  (later edition), a tenfold change in part (a). A ready replacement is in the notes if you accept the solution's
  limits (0.316 < β < 0.775, 1.5e5 < Re_D < 2e5, C_d = 0.9858 − 0.196β^4.5).

- 2969 (Burton): book says "generalization of Theorem 4.6" (the 11-test); the b−1 digit-sum result generalises
  Theorem 4.5 (the 9-test); written as the 9-test.
- 3044 (Burton): stated the construction x = ((p−1)/2)! from Theorem 5.5's proof (the exercise depends on it).
- 6642 (Burton): hint "initial part of Theorem 15.10" now states bc − ad = 1 and the start of the proof's construction
  (most of the method, but what the book's hint points to). 6612, 6636: whole arguments described in one sentence.
- Burton small additions: 3165 (n⁴+1 -> 8k+1, n²+n+1 -> 6k+1), 3248 (Jacobi symbol), 3181 (λ(1) = 1, universal
  exponent), 3285 (form of even perfect numbers), 3335, and "Fibonacci numbers" in 3388, 6597, 6610, 6612.

- 20118 (Kern, Wien's law): book prints "2884 μm·°R ≈ 5200 μm·K" (units swapped); written 2884 μm·K ≈ 5200 μm·°R.
  The stored solution's "11,500 °R" should read 11,500 K (and with 0.25 μm the estimate is ~2× the real Sun's).
- 20161 (Kern Table 6.3): kept the header 1/v̄ in hr/ft (physically right); the book's solution plots the column as
  1/v̄^0.8, so a literal reading gives h_o ≈ 1,300 vs the stored 965 (stored solution likely wrong).
- 20156 (Kern): hot-stream capacity rate 30,000 Btu/hr·°F missing from the book's statement (and DB 20155); taken
  from the book's solution; cocurrent outlet formula given.
- 20097 (Kern): series coefficient written 2[1−(−1)^n]/(nπ) (book's display misses the factor 2).
- 20088 (Kern): no crop of the generic Fig. 2.1 (labels clash); layer order stated in words.
- 20122 (Kern): book cites Example 4.5 but means 4.4's black walls; stated as "two black bodies at the same temperatures".
- 20140, 20153 (Kern): conductivity units Btu/hr·ft·°F (book prints ft²); 20113: added "(one face)" (48 ft²).
- 20153 (Kern): carried-over Example 6.8 design specification is ~4 sentences (needed).
- 20200 (Kern): "the previous example" is literally Ex. 8.13/8.12, but the book's and stored solutions use Ex. 8.11's
  triangular fin; inlined Ex. 8.11.
- Kern inputs taken from earlier examples' working: fin efficiencies 0.86 (20195, 20196), 0.99 (20200), 0.97 (20202)
  (read off charts not included); 20230 states Ex. 9.23's tank volume ≈ 7335 ft³ (recomputing needs c_p not given).
- 20188, 20199, 20183 (Kern): "comment on/summarise the results" questions get the setups but not the numbers.
- 20204 (Kern): h unit Btu/hr·ft²·°F (book prints ft); added "on its faces and tip" (the solution assumes tip convection).
- 20242 (Kern): removed a stray empty "Figure 11.5 ... Case III" float (extraction spill).

- 4008 (Sen): the PDF's Problem 2.21 has no opening sentence and the DB attached 2.20's transformer (250 kVA,
  11 kV/2.2 kV), which fits oddly with the question's 2300 V supply; left as is.
- 6208 (Sen Fig. E6.2): the crop includes Example 6.2's worked-solution marks (23.09 kV, 329.8 A, ...), not this
  question's answer but visible.
- 4026, 4028 (Sen): added "Neglect armature reaction" (from Problem 4.3). 4101: book's "Problem 6.4" is a typo for
  6.12; its three full-load cases inlined. Trimmed magnetization tables are chosen around the points the solution
  uses (hints where the answer lies); 4047, 4034 operating points lie beyond the book's curve (as in the book).

- 11005c (Schwarz 1.10): states the fact compared against — max expected gain 1/(eλ) at c = 1/λ in the no-loss game —
  which is the answer to question 11004c. Alternative: describe only the no-loss rule.
- 11033, 11035 (Schwarz): the delta-method result is described without its formula in 11033 (part a derives it) and
  given as a formula in 11035 (a tool there).

- 21182 (Kamal): removed a stray Fig. 11.17 (RC circuit) the import attached; it belongs to 21183, which got its own crop.
- 21282 (Kamal, Helmholtz coils): book says currents flow "in the opposite sense" but its solution adds the fields;
  written "same sense".
- 21453 (Kamal, thin lens): system matrix from Prob. 15.18's solution inlined; f₁, f₂ defined as the solution uses them
  (makes the proof short).
- 20728 (Kamal): left out Prob. 4.50's "same mass and radius" (contradicts the question's conditions).
- 20582 (Kamal): no problem diagram in the book; 30°/60° inclines and direction of motion taken from the solution's
  free-body diagram and stated in words (drawing it is part a).
- 21409 (Kamal Fig. 14.10): figure exists only in the solutions section; the crop shows "plane of l = 0" and
  "direction of increasing l" labels, no results.
- 20540 (Kamal): "(Fig. 1.4)" deleted (book misprint; river figure 1.5 already in the question). 21414: "5000 Ã" -> 5000 \AA.
- Kamal figures not matching their text exactly: 21226 (Fig. 12.20 draws c midway, text says one-fourth), 21133 (Fig.
  11.8 also shows 11.40's point P), 20935 ("6 cm" mark sits above the crests; solution reads it as the amplitude).
- 20850, 20902, 20935 (Kamal): neighbouring problems' figures (Figs. 6.16, 8.3) added because the data is in the drawing.
- Yaglom: group remarks/definitions for the FOLLOWING problems were attached to earlier ones by the import (17802
  carried "In problems 22-32, n always denotes a positive integer"; 17812 the Euler/partition intro for 32-33; 17843 the
  triangular-array definition for 63). Moved each into the question that uses it (17814, 17844) or deleted it.
  Not flagged, still missing their setup: 17813 (problem 32, "partitions"/"parts" undefined) and 17803 onward
  (problems 22-32 lack "n is a positive integer").
- 17838 (Yaglom): part l sat in an enumerate with no \item (wouldn't compile), fixed; 17814: a page-break verbatim
  block rejoined; 17862: \mathrm{l} -> 1; 17843: Fig. 7 moved to the end (split a sentence), section-closing remark with
  the Riordan "p. 14" citation deleted; 17844: the triangular array typeset in LaTeX instead of the old image
  (that image is now unreferenced), "missing entries count as 0" added.
- Engel broken LaTeX removed: 14665, 14674, 15429 had a stray \end{enumerate}; 14665 an unclosed
  \begin{enumerate}\setcounter{enumi}{42}; 15429 a loose "Fig. 12.37\\" line. Mojibake fixed: "ErdÃ¶s", "WeitzenbÃ¶ck".
- 15648 (Engel): Fig. 5.8 crop plus E13's counts (T₆ = 1296); the book's E(6) check denominator 216 -> 1296
  (3750/216 ≠ 625/216, 3750/1296 = 625/216). Drop the correction to keep the book's text.
- 15489 (Engel): the book's "problem # 12" is actually No. 15 of that list; its result stated.
- 15056, 15648 (Engel): stored questions are the book's worked examples (E21, E14) and still contain their proof or
  solution (same issue as Srinath 20313/20346).
- 14547 (Engel Fig. 2.2): the problem's own figure shows an example L-tetromino tiling (suggests n = 6 works).
- 14674 (Engel): G₈₀ still undefined (not flagged).
- Chapman .dat questions: file note deleted where the curve image/table was already there (5949, 5990, 5999, 6019,
  6056, 6057, 6059, 6064, 6065); printed curve cropped for the file-only ones (Fig. P9-6 for 6060-6062, Fig. P9-7 for
  6066-6071). Existing uncaptioned images wrapped in captioned figures (may float from their place in 5949, 5999, 6056).
- 6059 (Chapman): replaced the existing curve image (its x-axis labels sit off their gridlines) with the book's Fig. P9-6.
- 6038 (Chapman): DB "two reactances in parallel" -> "in series" (book and figure).
- 5999 (Chapman): added "the dashed line is the air-gap characteristic"; book says four-pole, DB two-pole (left).
- Chapman DB vs 4th-ed. printing differences left alone: 5981 (50 vs 60 Hz), 6064 (120-V motor and E_A table vs
  230 V), 6068 (armature reaction 200 vs 300 A·turns). 5963, 5964: the 30° lag assumes abc sequence (unstated).
- 17149 (Gregory): already carries a plank-on-log figure captioned "FIGURE 9.8" from another edition (here 9.6 is the
  plank, 9.8 Atwood's machine); text "Figure 9.6" -> "Figure 9.8" to match the attached caption, no image added.
- 17252 (Gregory): the PDF asks for the frequency ratio, the DB for the frequencies; same Table 2 assumed (λ₁ values,
  atomic weights C 12, O 16, S 32 added); they give ~2231 and 880 cm⁻¹ vs the measured 2174 and 874.
- 17305 (Gregory): book's frictional couple "equal to Kω" written as −Kω (resisting, as its equation implies).
- 17251, 17300, 17182 (Gregory): easier — Δₙ = sin(n+1)θ/sin θ given; known comparison result stated; total mass M+m.
- 17230, 17231 (Gregory): partial crops (the other panels are velocity diagrams giving the asked kinetic energy).
- Kaczor small fixes: 13219 product index n=1 -> k=1 (book typo too); 13235 interchange theorem stated on [0,∞)
  (avoids clashing with a); 13426 \mathbf{v}_i -> \mathbf{V}_i; 13551 "CesÃ ro" -> Cesàro. 13101: the book's
  inequality p(x)−p(y) ≤ p₁(x)−p₁(y) for x<y looks reversed (matches the DB, left).

## Long inlined summaries (candidates for trimming)
- 19319 (White): the agent replaced "Table A-5" with the whole 17-liquid appendix table; trimmed by me to five
  candidate liquids with standard property values (answer: gasoline). Done.
- 19308 (White): four pointers replaced by brief statements plus the Colebrook formula.
- 13317 (Kaczor 1.7.10): added the definition of Jordan measure for unbounded sets next to 1.7.2 (over budget, needed).
- 13366 (Kaczor 2.1.22): the Cantor-like set construction of 1.7.12, ~3 sentences.
- 13498 (Kaczor 2.4.19): 2.4.18's conditions plus its conclusion in parentheses (the book's solution relies on it).
- 10388 (Stirzaker): "Do the appropriate parts of Exercises (6.3.1)-(6.3.4) again" now inlines all four.
- 10428, 10533 (Stirzaker): another exercise's result given as a usable fact.
- 10374 (Stirzaker): PRP Theorem (3.10.18) stated from knowledge, fairly but not fully sure.
- de Lange 21904 (Lax-pair method of Q11.14), 21959, 21961 (Fourier method of Q13.5), 21958, 21960, 21962
  (approximate solutions compared against), 21898 (restricted three-body setup, L₄, frequencies), 21917.
- Øksendal 22480 (Theorem 9.3.3 in ~3 sentences).
- Øksendal Thm 10.4.1 (optimal-stopping verification) in 22497, 22506, 22507, 22508, 22540 and the HJB theorems in
  22512, 22514, 22521, 22523, 22525: longer than two sentences (many hypotheses); 22538 carries the general price
  and hedge formulas plus two target formulas ("complete the details of the proof").
- 22502 (Øksendal Ex 10.8): "superharmonic" defined as Af ≤ 0 (book's remark) so the intended example works.
- 22532 (Øksendal Ex 12.7): states which of Ex 12.6's six markets admit arbitrage (c and e).
- 22494 (Øksendal): Thms 9.1.1 and 9.2.13 merged into one uniqueness statement "(suitably bounded)".

## Pre-existing images that give away answers (separate cleanup)
- 18869 (White): existing free-body sketch shows the answer θ = 27°.
- 18862, 18877 (White): existing solutions-manual sketches hint at the method (marked θ; rotated free surface).
- 19448 (Fig. P7.14 shows wall suction), 19528 ("strip dr"), 19504, 19505 (force sketches), 19520 (flag layout
  H × 2H) (White): existing images hint at the solution.
- 19580 ("Fig. P8.18" is the solution's streamline plot), 19592 ("Fig. P8.30" solution sketch with a and πa),
  19617 ("Fig. P8.55" solution force/velocity diagram), 19557 (bee sketch from the solution) (White).
- 19667 (White): existing "Fig. P8.107" is the solutions-manual sketch showing Δy = Δx/√3 and the ψ = 0/10 boundary
  values (gives part of the answer); 19670, 19671 have mild solutions-manual mesh sketches.
- 19662 (White): Fig. P7.108 "Figure Unavailable" in the PDF; chart taken from question 19541.
- 19651 (White): inlined continuity and φ's definition (Eq. 8.85 is continuity), which makes it a direct substitution.
- 19673 (White): stated Example 8.7's result (0.250 m/s) and the exact value (0.241 m/s) for the comparison.
- 19680 (White): said "NACA 4412 airfoil from Prob. 8.83"; P8.83 and the stored answer use the NACA 2412, so
  renamed to 2412 and inlined the curve fits (alternative: drop the airfoil name).
- 19726 (White): existing Fig. P9.46 (solutions manual) shows solution velocities 333 and 545 m/s.
- 19961 (White P10.119): the DB text stopped at the data table without asking anything; restored the book's task
  (correlate with Re and We via Eq. 10.61, written out, plus the C_d definition).
- 19968 (White P10.126): restored "on a slope of 0.15°" (in the book and the solution, missing from the DB);
  defined α and Y.
- 20006, 20007 (White): inlined DB Prob. 11.31's data table, Prob. 11.24's clue (shutoff head ≈ 0.6U²/g), the
  Eq. (11.27) BEP values; 20007 states the pump family (≈15.5 in at 1200 r/min, BEP 2000 gal/min, 81 ft, 48 bhp)
  using 20006's stored estimate.
- 19965 (White): Fig. P10.122 added (H₂ is only defined there); 19998: all of Fig. 11.7 for the six-impeller comparison.
- 20079 (White): "Reconsider Prob. 6.77" (economic variant, one diameter, Q = 30 m³/h), but its own Fig. C11.3 and
  stored solution use the Prob. 6.76 system (20 m head, 10 m of 6-cm then 30 m of 4-cm wrought-iron pipe); the
  6.76 system was described. Alternative: unresolved.
- 20060, 20062 (White): the inlined caption sentence states the test speed n = 600 r/min, which partly gives away
  20062 part (b) (the new data are at variable speed). Consider dropping the speed in 20062.
- 20076 (White): stored solution's "C_P ≈ 1.0" looks like an extraction error for 0.1 (its power implies 0.1).
- 20023, 20024 (White, four pumps): BEP data in a small table. The stored solutions' "Prob. 11.35" row uses a 5-in pump
  at 1800 rpm, not the real 11.35 (18-in at 880 rpm, used here and in 20011's solution), so that row of the stored
  answers won't match. 20024: "C_Q*" -> "C_P*" (power-coefficient question).
- 20031 (White): "compare with Fig. 11.13" -> Fig. 11.8 (book and stored solution); 20036: "Fig. 11.14" (efficiency
  only) -> Fig. 11.13 (where the solution reads C_Q*, C_H*).
- 20054 (White): existing "Fig. P11.80" is the solutions-manual sketch with operating points a, b (no numbers).
- 20056 (White): solution-field figure marks points a, b, c, so the clean book drawing was used.
- 20042 (White): leaf-blower setup from DB 20038's text (not in the 4th ed.); 20045: "10 Â¢/kWh" -> "10 cents/kWh".
- 19919 (White): used y1 = 1.2 m, H = 15 cm for "Prob. 10.73" (PDF's P10.73 and this question's stored solution);
  the DB's own 10.73 (19915) says 1.4 m (inconsistent DB).
- 19950 (White): added S0 = 0.005, missing from the DB text (PDF P10.108; matches the solution's normal depth).
- 19945, 19953 (White): "Eq. 10.52" isn't in the 4th ed.; step-method form taken from the stored solutions.
- 19920 (White): added the drowned-gate chart P10.77 and q = Cd·H·√(2g·y1) (needed, not cited).
- 19918, 19930, 19932, 19947 (White): book figures left out (labels conflict with or answer the question); setup in words.
- 19914 (White): used the PDF's figure instead of the solution's later-edition one labelled "Gap = 20 cm".
- 19803 (White Fig. P9.124): figure from own solution field (not in the 4th ed.).
- 19841 (White C9.5): not in the 4th ed.; setup taken from the DB's own C9.5 (19840) and its solution's choked
  flow 0.0452 kg/s; k = 1.33, R = 461 from Table A.4.
- 19847 (White): no figure (4th ed. has different data; the solution's figure shows a solution step); "as shown" -> "downstream".
- 19828 (White): Example 9.21's 8° results (C_L ≈ 0.247, C_D ≈ 0.0370) stated, needed for the linearity part.
- 19809 (White): P9.129 figure still shows the original 50° shock angle; the question says "(it is not 50°)".
- 19879 (White Fig. E10.6): this PDF's E10.6 is a specific-energy plot and its V-channel E10.5 labels a 50° side
  angle that clashes with the question's θ; used the V-channel sketch from the question's own solution field.
- 19878 (White): existing "Fig. P10.36" image shows n1 = 0.022, n2 = 0.075 (values otherwise looked up).
- 19907 (White): "(the solution of Prob. 10.64)" -> "the bump height at which the crest flow becomes exactly
  critical", a value question 19906 asks students to compute.
- 19715 (White): "(see Fig. P9.25)" deleted (that figure's air/mercury data conflicts with the helium problem).
- 19633 (White): asks for max velocity "on the y-axis", stored solution finds it on the x-axis (4th ed. also says y).
- Also White ch. 7-8: 19577 (hurricane, not in the 4th ed.) uses the 4th-ed. Fig. P8.14 and its v_θ(r) model, as
  in DB 19576; 19614/19615 get the Fig. 8.11 chart they need (not cited); 19613's figure shows the a/2 bump case.

- Strang: 23325 added what Ax means (steel, rubber, labour) since A was never defined; 23266 says K is the
  −1,2,−1 matrix; 23056 (Schwarz -> GM ≤ AM) and 23222 (S² counts 2-step paths) now spell out a step.
- 23018 (Strang Fig. 1.1): only the left panel cropped (the right shows v − w, the answer).
- **23435 (Strang PS 3.3 #9) — decide:** the DB's part (b) says "7 and −3 in the particular solution"; the PDF's #9
  says "−9 and 3" (Worked Example 3.3 A). The DB's numbers fit Worked Example 3.3 C (x_p = (7,0,−3,0)), so the agent
  inlined 3.3 C's [A b] -> [U c] and x_p (checked consistent; no stored solution). By the rules this is "unresolved"
  (PDF mismatch); accept the rewrite or leave the question as is.
- 23370 (Strang PS 3.2 #4): "For the same A and B" -> "For the matrices A and B below" (it gives its own A, B).
- 23427 (Strang PS 3.3 #1): the six steps of Worked Example 3.3 A in one sentence (they are the tasks asked).
- 23326 (Strang): book misprints the pointer as "Problem 31"; data taken from PS 2.7 #30.
- 23556 (Strang): Sec. 4.1 eq. (2) (nullspace ⟂ row space proof) written out; the question asks the same argument
  with roles swapped, so it is now a near-template.
- 23614 (Strang): stated C = 9 (horizontal line) and (C, D) = (1, 4) (best line), which it compares against.
- 23622 (Strang): "as in Worked Example 4.2 C" deleted; the book has only 4.2 A and B (book error).
- 23665 (Strang): modified Gram-Schmidt code described in one sentence; "MATLAB" dropped (built-in qr can flip signs).
- Strang PS 4.3: existing Figure 4.9 caption now marks "(a, left)" and "(b, right)" so "Figure 4.9a/b" resolve.
- 24057 (Strang): question and book text say "Figure 8.1", the house figure is printed as Fig. 8.2; cropped it and
  captioned "Figure 8.1". 24014: Fig. 7.6 not cropped (shows the answer); four subspaces named in words.
- 24106 (Strang): book's formula (7) has no limits; wrote ∫ from −π to π to match the DB's |x| ≤ π (the PDF's problem
  prints "L ≤ |x| ≤ 2π").
- 23884 (Strang): states e^M = I + (e−1)M when M² = M and e^M = I + M when M² = 0 (what Problems 19, 21, 22 establish).
- 23878 (Strang Fig. 6.5): cropped without the three example matrices printed in it (one answers part (a)).
- 24174-24187 (Strang graphs): each question keeps only the graph image it uses (triangle for #1-7, square for #8-14).
- 24197 (Strang): book says "equation (6)" but K₁ = A₁ᵀC₁A₁ is printed as (12); inlined (12).
- 24203, 24244 (Strang): closing remarks with \href (course note, pointers to another book) deleted.
- 24228 (Strang): homework LP setup in two long sentences (edge of the budget).
- 24275 (Strang): "See Section 9.2" is a 4th-edition leftover (9.2 is Hermitian matrices in the 5th); replaced by the
  hint ||A⁻¹|| = 1/λ_min for symmetric positive definite A (deleting it would also be fine).
- 24343, 24355, 24333 (Strang): this PDF printing differs from the DB and the DB is correct; left as is.
- 24030 (Strang): book misprints "Following Problem 18"; the DB's "Problem 19" is meant and was inlined.
- 23552 (Strang Figure 4.3): faint bleed-through from the reverse page at the top of the crop.
- Strang PS 4.2 #1 is not in the DB (the earlier Problems PDF lacked that page); the full 5th-ed. PDF now has it,
  so it could be imported. Its data appears only inside 23575.

- **20313, 20346 (Srinath) — structural:** the DB question text contained the book's worked solution (20313 also a
  spill of chapter-8 text, Eqs. 8.32-8.34). Cut back to the problem statement; 20313 got ν = 0.25 (only in the
  removed part) and the list of four failure theories. Both have an EMPTY solution field: the removed working could
  be moved there (it is in applied.jsonl's "old" text after applying).
- Srinath leaked book text deleted (extraction spills from other sections): 20419 (Sec. 6 unsymmetrical bending),
  20397 (Maxwell's reciprocal theorem), 20440 (two-cell torsion, Eqs. 7.50-7.54), 20469 (thermal cylinder, Eqs.
  9.35-9.39), 20493 (contact stress, Eqs. 12.19-12.41), 20486 (a leaked copy of the book's answer to part b).
- 20419 (Srinath 5.22): book points to Example 5.12 (a frame), but means 5.13's thin ring (matches the answer); used 5.13.
- 20459 (Srinath): "problem 8.7" means 8.8; 8.8's data used (Lamé check reproduces the book's answers).
- 20440 (Srinath): added Example 6.8's setup and the curved-bar strain-energy formula Eq. 6.49.
- 20452, 20492 (Srinath): earlier answers given as data (8.1's p = 17,000 kPa; pure-epoxy baseline 31 mm, 2.83 kgf);
  20492, 20493: Table 11.2 values added (not cited) that reproduce the answers.
- Srinath book errors corrected: 20369 τyx, σz -> τyz, τzx (reproduces the principal stresses); 20428 "20 m" -> 20 cm.
- Srinath stored answers: 20453's 6.05 cm doesn't reproduce (distortion energy, closed ends: ~6.19 cm); 20469's
  aluminium modulus labelled E_st with inconsistent units; 20413's bar angles unstated (answer implies 60°).
- 20309 (Srinath): book cites (7.56) (thin-rectangle stress, unused by its solution); gave (7.67), the circulation
  condition the solution uses.
- 20263, 20266 (Srinath Ex 2.5): book's strain matrix asymmetric in yz; used γ_yz = −0.02 (matches Ex 2.9's e_yz = −0.01).
- Srinath assumptions added to match stored solutions: 20327 "simply supported, span L"; 20330 "EI constant; find
  P_cr by minimum total potential energy"; 20286 "only bending strain energy"; 20275 "at section A"; 20357 "central" notch.
- 20348, 20337 (Srinath): carried over Ex 12.2's results (a = 0.1143 mm, p_max = 658 MPa) / Ex 11.2's principal
  strains, since the questions ask to show the same results.
- Srinath figures: only part (a) cropped where parts (b)-(d) are the book's solution sketches (Figs. 5.22, 6.31, 10.20).

## Missed by the scanner (follow-up scan needed)
- 23043 (Strang PS 1.2 #2): "Compute the lengths ... of those vectors" points back to Problem 1's vectors.
  Strang likely has more "those/these/the same vectors/matrices" back-references.
- Second-pass scan (scratchpad scan_missed.py, "those/these/the same <noun>" in the first 400 chars of rows not
  already fixed): 157 candidates, mostly false positives (things defined in the same question). Strang's 46 are worth
  a targeted pass with the scanned PDF; the rest look self-contained on a sample.

## Side findings (outside this task)
- `\href` in question text won't compile (no hyperref in the app preamble). Rows seen: 5509, 19577, 20431,
  24203, 24244, 24287 (19499 fixed by its rewrite). Worth a grep across the DB.
- Srinath arrays/aligned with lost "\\" row separators (blank lines instead): 20330, 20339, 20361 — likely fail to
  compile (20396, 20428 were repaired by their rewrites). 20360's stored solution divides by "15.2" (should be 12.5; result 288 MPa still right).
- Mojibake ("KÃ¡rmÃ¡n", "LÃ©vy", "SzegÃ³"): White 19306, 19482, 19856, 19983; ~30 Stirzaker rows.
- 18894 (White Fig. P3.8): figure from the question's own solution field (not in the 4th ed.); 18852 and 18874
  got no figure (the 4th-ed. drawing conflicts with the stored solution's data/definitions).

## Left as is, may want attention
- 18901 (White): text says "entrance velocity V_o", figure and question use U_o (pre-existing).
- 22482 (Øksendal): added Lemma 9.2.12 (irregular boundary points form a semipolar set), needed to use (H).
- 22444, 22490, 22491, 22477 (Øksendal): hint pointers replaced by a short description of the method.
- 21968 (de Lange Q13.16): extraction error "6.6 / ω_c = 1.2" should be "6. ω/ω_c = 1.2".
- 22005 (de Lange Q14.30): hint level: gave Q14.27's setup and equation of motion, not the pendulum equation.
- 22008, 22021 (de Lange): added short definitions of γ, p = γm0u and the V²-Lorentz transformation.
- 21967 (de Lange Q13.15): figure cropped from Q13.14 (Q13.15 has none of its own).
- 25052(b) (Blitzstein): asks to look up real population data online.
- 24589 (Dekking): "answer the same three questions" recast; part b now about MAD only.
- Stirzaker: ~30 rows have mojibake like "LÃ©vy" (UTF-8 read as Latin-1); fixed only where a rewrite touched it.
- 10916 (Stirzaker): ends with the next chapter's heading "\section*{13} \section*{Diffusion processes}".
- 9799 (Stirzaker): garbled footnote mark and a stray "\section*{3} Discrete random variables" heading.
- 21878 (de Lange): one extra "}" in the original question (pre-existing).
- 24916 (Blitzstein): stray "$" in the original, fixed by the rewrite.
- Mladenovic: rows after 12175/12201/12211 (Exercises 12.13-12.20, 3.12-3.30, Problems 12.37-12.46) lack their group setup; the three carrier rows were deleted with the no-PDF sources.

## Working moved out of questions (2026-11-04)
Applied with `python -m app.tools.move_working --apply` (backup `amplify.db.bak-20261104-183804-pre-move-working`, old
values in `missing_refs/moved_working.jsonl`). 38 questions: the moved text now opens the solution.
- Worked solutions inside the question: 11312 (proof; the unrelated d'Ocagne footnote dropped), 15056 (main idea, Fig.
  7.3 and first proof, ahead of the stored proofs), 15648 (derivation, n = 6 check and Fig. 5.8 `mref-15648-1`).
- White solution-sketch images (18): 18869, 18862, 18877, 19448, 19504, 19505, 19520, 19528, 19557, 19580, 19592,
  19617, 19667, 19670, 19671, 19726, 20054, 18999. New clean book crops: `mref-18862-1` (Fig. P2.141),
  `mref-19528-1` (Fig. P7.94). 18999's solution already had the drawing, so only the question changed and
  `mref-18999-1` is now unused. 19520 gained one clause fixing the flag layout the stored answer assumes. 18877's
  agent-proposed U-tube crop was not used (its dashed centre axis conflicts with rotation about DC). 19670 and 19671
  are borderline (the sketch is only the solution's stencil/mesh).
- Steps stated in the question (17): 20337, 20348, 21876, 21877, 21878, 10168 (whole bracketed hint; the `hints`
  column keeps a milder one), 10288, 11005 (part c now asks for the no-loss maximum), 25085, 17300, 6642, 3044,
  23884, 23056, 23222, 13498, 21453.
- Kept as is (inputs, not this question's working): 18986, 18987, 18989, 18995 (mass flow 11.8 kg/s from Prob. 3.35;
  moving it would need the nozzle data added from the book and would change 18995's thrust); 22426, 22428 (Riccati
  equation from the Kalman-Bucy theorem; removing it re-creates the outside reference); 20062 (n = 600 r/min is in
  Fig. 11.21's caption); 21880 (the inlined one-body results are what the question asks to generalize).
- Found on the way: 10168's stored answer (density with a parameter built from a, b, which the question never
  defines) is the general case; the stored solution assumes M lies between L and N, giving a uniform angle. 17300's
  stored solution has a gravity term -Mgh cos(theta) in what the question calls free motion.
