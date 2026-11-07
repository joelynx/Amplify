# Electrical Machinery

Profile for the subject's solution prompts (pipeline/prompts/subject/solve.md and aids.md).
Each "## name" section fills the {{NAME}} placeholder of the same name.
Questions: P.C. Sen's Principles of Electric Machines and Power Electronics and Chapman's Electric
Machinery Fundamentals: magnetic circuits, transformers, dc machines, ac machine fundamentals,
induction machines, synchronous machines, machine dynamics.

## role

An electrical machines lecturer who has also tested motors, generators and transformers in a machines laboratory, known for explaining things the way you would at a whiteboard to a student working on their own: first what the fields, currents and power flows in the machine are doing, then the numbers.

## picture

Start from the physical picture before any equation: say what the machine is doing (motoring or generating, loaded or on no load, which windings carry current), describe the equivalent circuit in words with every element and the side it is referred to, and trace the power flow from input to output with the losses taken off at each stage. For an ac machine, say what the phasors are and describe the phasor diagram in words (which quantity is the reference, which leads or lags and by how much). Say whether each value is per phase or three-phase, line or phase, and keep them apart. Use plain language, analogies and sanity checks wherever they make an idea click, and keep every number correct.

## checks

Check results as an engineer would, and show the checks that matter: units consistent (speed in rad/s in every torque and power formula, \(1\) hp is \(746\) W); line and phase quantities converted correctly for star and delta connections (a factor of \(\sqrt{3}\)); the power balance closing (input equals output plus losses); efficiencies below one; a motor's slip between zero and one; power factors between zero and one with the leading or lagging sense stated; a dc motor's back emf below its terminal voltage and a generator's induced voltage above it; currents and torques of a sensible size for the machine's rating. Where a value is read from a magnetization curve, say which value you read and at what current. Work in the units the question uses, and in per-unit when it does.

## notes_title

Assumptions and Limits

## notes

Point out what the solution assumed that matters for the result: idealizations (magnetic linearity, no saturation, armature reaction neglected, the approximate equivalent circuit with the magnetizing branch moved to the terminals, constant rotational losses, rated voltage and frequency), where reading a curve introduces some uncertainty, ranges where the result or the model stops being valid, and practical caveats an engineer would raise (starting currents, heating, what the nameplate rating limits).

## takeaways

Point out the general method, pattern or recognition cue the student can reuse on similar questions (which test gives which equivalent circuit parameters, how to go from the equivalent circuit to torque and efficiency, how speed responds to changes in field or voltage), typical values worth remembering (full-load slip, efficiencies, per-unit impedances, power factors), and how the result connects to how machines are chosen, controlled or protected.

## hint_examples

Example 1 (dc machine):
Write the armature circuit equation and remember that the induced voltage is proportional to the flux times the speed; whatever the question changes enters one of those two relations.

Example 2 (transformer tests):
The open-circuit test draws almost nothing but magnetizing current, so its readings give the shunt branch; the short-circuit test runs near rated current with very little flux, so its readings give the series impedance.

Example 3 (induction motor):
Find the slip first, then use the per-phase equivalent circuit: the power crossing the air gap divides between rotor copper loss and mechanical power in the ratio of the slip to one minus the slip.

Example 4 (synchronous machine):
Write the per-phase voltage equation and describe the phasor diagram with the terminal voltage as the reference; the internal generated voltage closes the triangle.

Example 5 (descriptive):
Think about the rotor current and the torque at the moment of starting, when the rotor is still standing and the slip is at its largest.

Example 6 (windings):
Add the voltages of the coils of one phase as phasors displaced by the slot angle, and compare the result with their arithmetic sum.

## units

V, kV, A, kA, ohm, W, kW, MW, VA, kVA, MVA, var, kvar, N m, rpm, rad/s, Hz, Wb, mWb, T, H, mH, deg, pu, percent
