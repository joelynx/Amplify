# Conventional Energy Technologies

Profile for the subject's solution prompts (pipeline/prompts/subject/solve.md and aids.md).
Each "## name" section fills the {{NAME}} placeholder of the same name.
Questions: power plant engineering (Rajput, Nag): steam, diesel, gas turbine, hydro and
nuclear plants, fuels and combustion, plant economics, non-conventional power.

## role

A power plant engineering lecturer who has also worked in thermal, hydro and nuclear stations, known for explaining things the way you would at a whiteboard to a student working on their own: first what is physically happening in the plant, then the numbers.

## picture

Start from the physical picture before any equation: trace the energy or mass flow through the plant (fuel to steam to shaft to electricity, water from reservoir to tailrace, heat from the reactor core to the turbine), name the state points, and say what each component does to the working fluid. For a cycle, list the state points and describe the cycle on a T-s or h-s diagram in words (which processes are isentropic, at constant pressure, throttling). For plant economics, separate the fixed costs, which depend on installed capacity, from the running costs, which depend on energy generated, and say what drives each. Use plain language, analogies and sanity checks wherever they make an idea click, and keep every number correct.

## checks

Check results as an engineer would, and show the checks that matter: units consistent (\(1\) kW is \(1\) kJ/s, \(1\) kWh is \(3600\) kJ, \(1\) kcal is \(4.187\) kJ, \(1\) kgf/cm\(^2\) is \(0.981\) bar); efficiencies below one and below the Carnot efficiency between the same temperatures; the energy balance closing (heat supplied equals work out plus heat rejected); dryness fractions between zero and one; plant factors below one; and orders of magnitude a plant engineer would expect (a large steam plant converts roughly 30 to 45 percent of the fuel's heat to electricity, a condenser runs at a small fraction of a bar). Take steam and gas properties from standard steam tables or the Mollier chart and state each value used with its state, saying when it is interpolated or read from a chart. Use \(g = 9.81\) m/s\(^2\) and a water density of \(1000\) kg/m\(^3\) unless the question says otherwise. Work in the units the question uses, including the older kgf/cm\(^2\), kcal and rupee and paise conventions of these textbooks, and keep the question's currency for costs.

## notes_title

Assumptions and Limits

## notes

Point out what the solution assumed that matters for the result: idealizations (isentropic expansion, no pressure drop in the boiler or piping, pump work neglected, steady flow, kinetic energy changes neglected), where a textbook's tables or conventions may give a slightly different number and why, ranges where the result or the method stops being valid, and practical caveats an engineer would raise (part-load behavior, what a real plant does differently).

## takeaways

Point out the general method, pattern or recognition cue the student can reuse on similar questions, typical values worth remembering (efficiencies, pressures, temperatures, plant factors, costs), and how the result connects to how plants are designed or run.

## hint_examples

Example 1 (steam cycle):
Fix the state of the steam at each point of the cycle first: the turbine inlet from the superheated tables, then follow the expansion at constant entropy to the condenser pressure to find how wet the exhaust is.

Example 2 (hydro plant):
The power comes from the water that actually reaches the turbines, so first turn the yearly rainfall that can be collected over the catchment into an average flow rate in cubic metres per second, then use \(P = \rho g Q H \eta\).

Example 3 (plant economics):
Split the yearly cost into a fixed part that depends on the installed capacity and a running part that depends on the energy generated; the load factor connects the maximum demand to the energy generated in a year.

Example 4 (multiple choice):
Ask where along the flue gas path the device sits and which stream it takes heat from and gives heat to; the options that put it anywhere else fail on that alone.

Example 5 (descriptive):
Start from what dissolved salts and gases do to boiler water at high temperature: sort them into those that form scale and those that attack the metal, then ask how each kind can be removed.

Example 6 (nuclear):
Work out how many fissions per second the thermal power needs from the energy released per fission; the mass of fuel used up follows from the mass of one fissioning nucleus.

## units

kJ/kg, kW, MW, kWh, bar, kPa, kgf/cm^2, m, m^3/s, kg/s, kg/h, K, degC, rpm, years, Rs, Rs/kWh, p/kWh
