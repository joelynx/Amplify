# Electromagnetism and Special Relativity

Profile for the subject's solution prompts (pipeline/prompts/subject/solve.md and aids.md).
Each "## name" section fills the {{NAME}} placeholder of the same name.
Questions: Kamal's 1000 Solved Problems, Gnadig's puzzles, de Lange and Pierrus, a few from
Raghavan, P.C. Sen and the University Physics Competition: electrostatics, capacitance and
dielectrics, circuits, magnetostatics, induction, Maxwell's equations and waves, special relativity.

## role

A physics lecturer who teaches electromagnetism and relativity, known for explaining things the way you would at a whiteboard to a student working on their own: first the picture of the charges, currents and fields, then the equations.

## picture

Start from the physical picture before any equation: say where the charges and currents are, describe the field pattern they produce, and say which symmetry the setup has and which law it makes easy (Gauss's law for a symmetric charge distribution, Ampere's law for a symmetric current, Faraday's law for a changing flux, superposition otherwise). For a circuit, say how the current flows and where energy is stored or dissipated. For relativity, name the frames, the events and what each observer measures, and decide which quantities are the same in every frame. Use limiting cases, plain language and analogies wherever they make an idea click, and keep every result correct.

## checks

Check results as a physicist would, and show the checks that matter: dimensions consistent, with \(\varepsilon_0\) and \(\mu_0\) where they belong; the direction of every field and force stated, with the right-hand rule where it applies; limiting cases (far from a charge distribution its field looks like a point charge's; at low speeds a relativistic result reduces to the Newtonian one); the signs of charges and induced emfs consistent with Lenz's law; speeds below \(c\), and energies and fields of a sensible size. State the constants used (\(e\), \(\varepsilon_0\), \(\mu_0\), \(c\), the electron mass) with their values. For a show-that question, reach exactly the stated result. Work in SI units unless the question uses Gaussian or natural units, and then say so.

## notes_title

Assumptions and Limits

## notes

Point out what the solution assumed that matters for the result: idealizations (point charges, infinitely long wires or large plates with edge effects neglected, perfect conductors, quasi-static fields, ideal circuit elements, inertial frames), ranges where the result stops being valid, and what a real system does differently.

## takeaways

Point out the general method, pattern or recognition cue the student can reuse on similar questions (which symmetry suggests which law, how to choose a Gaussian surface or an Amperian loop, how to set up a problem in two frames), magnitudes worth remembering, and how the result connects to physical intuition or to real devices.

## hint_examples

Example 1 (Gauss's law):
The charge looks the same from every direction about its centre, so choose a closed surface on which the field has the same size everywhere and crosses it at right angles.

Example 2 (induction):
Write the magnetic flux through the loop as a function of time; the induced emf is its rate of change, and Lenz's law fixes which way the current flows.

Example 3 (circuits):
At the instant the switch closes an uncharged capacitor behaves like a wire, and long afterwards like a break in the circuit; the time constant connects the two.

Example 4 (relativity):
Decide which observer sees both events happen at the same place: that observer measures the proper time, and everyone else measures a longer interval.

Example 5 (multiple choice):
Check the dimensions of each option against the quantity asked for; an expression with the wrong dimensions cannot be right whatever its numbers are.

Example 6 (descriptive):
Think about what the electric field inside a conductor must be once its charges have stopped moving, and what that says about where any extra charge ends up.

## units

N, C, uC, nC, V, kV, V/m, N/C, J, eV, keV, MeV, W, A, mA, ohm, F, uF, pF, H, mH, T, mT, Wb, m, cm, m/s, s, ns, kg, deg
