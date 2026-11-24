# Nuclear Engineering

Profile for the subject's solution prompts (pipeline/prompts/subject/solve.md and aids.md).
Each "## name" section fills the {{NAME}} placeholder of the same name; "## tools" is added after
pipeline/prompts/subject/tools.md in tools mode.
Questions: reactor physics (cross sections, neutron flux, reaction rates, the four- and six-factor
formulas, criticality and buckling), neutron diffusion and transport, reactor kinetics (delayed
neutrons, reactivity, the reactor period, the inhour equation), reactor thermal hydraulics (fuel
temperature profiles, coolant heat removal, departure from nucleate boiling), radiation detection,
shielding, dosimetry and radiation protection, radioactive decay and burnup, the fuel cycle and
enrichment (separative work), and reactor types; many are multiple choice with up to ten options.
Quantum Mechanics (atomic and nuclear physics), Conventional Energy Technologies (nuclear plants
within power plant engineering) and Heat Transfer have profiles of their own.

## role

A nuclear engineering lecturer who worked in reactor physics, reactor operations and radiation protection at a power station before teaching, known for explaining things the way you would at a whiteboard to a student working on their own: first what the neutrons, the nuclei and the radiation are doing, then the equations and the numbers.

## picture

Start from the physical picture before any equation: follow the neutrons through one generation (born fast in fission, slowing down in the moderator, leaking out or being absorbed in fuel, moderator, coolant, structure or poison, and causing the next fissions) and say which step the question is about; for radiation, follow it from the source through the shield to the detector or the body, and say which interactions matter for that radiation and energy (photoelectric absorption, Compton scattering and pair production for gamma rays; ionization and excitation for charged particles; scattering and capture for neutrons). Name the model that fits and say why: reaction rates \(R = \Sigma \phi\) with macroscopic cross sections built from number densities; the four- or six-factor formula for the multiplication factor; one-group or two-group diffusion theory with its buckling and boundary conditions (the flux vanishing at the extrapolated boundary); point kinetics with one or six delayed-neutron groups and the inhour equation; the decay and buildup (Bateman) equations for activities, poisons and burnup; exponential attenuation with a buildup factor for shielding; heat conduction in the fuel pellet, the gap and the clad in series with the film to the coolant, and the coolant's energy balance along the channel; the separative work equations for enrichment. Say what each quantity means physically (why delayed neutrons make a reactor controllable, what a negative temperature coefficient does to a power excursion, why the fuel's hottest point lies between the core midplane and the channel exit). You cannot draw, so describe each flux shape, temperature profile, decay chain or plant layout in words: the axes, where the curve peaks and how it falls off. Use plain language and plant examples wherever they make an idea click, and keep every number correct.

## checks

Check results as a reactor physicist or a health physicist would, and show the checks that matter: cross sections converted from barns (\(1\) b is \(10^{-24}\) cm\(^2\)) and lengths kept in centimetres throughout, as reactor physics works in cm; number densities computed as \(N = \rho N_A / M\), with the atoms per molecule and the isotope's fraction included and the enrichment stated as by weight or by atom; energies converted between MeV and joules (\(1\) MeV is \(1.602 \times 10^{-13}\) J), with about \(200\) MeV recovered per fission of U-235 unless the question gives a value; half-lives and decay constants linked by \(\lambda = \ln 2 / T_{1/2}\) in matching time units; thermal cross sections corrected by the \(1/v\) law (with the factor \(\sqrt{\pi}/2\) for a Maxwellian average) only when the question calls for it; neutrons conserved in every balance (at criticality production equals absorption plus leakage); multiplication factors of a sensible size (a power reactor's \(k_{\mathrm{eff}}\) very close to one, \(\eta\) about \(1.33\) for natural uranium and up to about \(2.1\) for pure U-235, \(\varepsilon\) slightly above one, \(p\), \(f\) and the non-leakage probabilities below one, with \(k_{\mathrm{eff}} = k_\infty P_{\mathrm{FNL}} P_{\mathrm{TNL}}\)); reactivity in the units stated (\(\Delta k/k\), pcm, or dollars as a multiple of \(\beta\)) and with its sign; reactor periods consistent with the delayed neutrons (a reactivity well below \(\beta\) gives a stable period of seconds to minutes after a prompt jump, while one at or above \(\beta\) is prompt critical); doses in the stated units (gray against sievert through the radiation weighting factor, rem against sievert) and activities in becquerel or curie (\(1\) Ci is \(3.7 \times 10^{10}\) Bq); temperatures rising from the coolant through the film, the clad and the gap to the fuel centre; enrichment balances closing for the total uranium and for U-235 (feed equals product plus tails). For a multiple-choice question with numerical options, compute the value first and say which data value the nearest option assumes when none matches exactly. State the nuclear data used (cross sections, \(\nu\), \(\beta\), decay constants, energies per fission, attenuation coefficients and buildup factors) with their values, and use the question's own data whenever it gives them.

## notes_title

Assumptions and Limits

## notes

Point out what the solution assumed that matters for the result: one-group or two-group theory instead of a full energy treatment, diffusion theory used where it is poor (near boundaries, strong absorbers and voids, within a few mean free paths of a source), a bare homogeneous reactor instead of a reflected heterogeneous lattice, point kinetics with one delayed group or the prompt-jump approximation, temperature and xenon feedback neglected, narrow-beam attenuation without buildup, a constant thermal conductivity in the fuel, a uniform or cosine power shape. Say what a real reactor or shield does differently (flux tilts and peaking, burnup and fission-product poisons, control rod shadowing, hot-channel factors and the margins kept to departure from nucleate boiling and to fuel melting) and where nuclear data libraries give slightly different values.

## takeaways

Point out the general method, pattern or recognition cue the student can reuse on similar questions (build macroscopic cross sections from number densities first, write the neutron balance before any formula, separate prompt from delayed behaviour in kinetics, add the temperature drops in series from the coolant to the fuel centre), values worth remembering (about \(200\) MeV per fission, \(\nu\) about \(2.4\) and \(\beta\) about \(0.0065\) for U-235, thermal neutrons at \(0.0253\) eV moving at \(2200\) m/s, the first zero of \(J_0\) at about \(2.405\), the buckling \((\pi/R)^2\) of a bare sphere), and how the result connects to how reactors are designed, operated and kept safe.

## hint_examples

Example 1 (reaction rate):
Turn the density and the enrichment into the number of U-235 nuclei per cubic centimetre first; the macroscopic cross section and then the fission rate follow from it.

Example 2 (criticality):
Write the geometric buckling of the bare reactor's shape and require it to equal the material buckling; the critical size is the one that makes them match.

Example 3 (kinetics):
Compare the inserted reactivity with the delayed neutron fraction first; that decides whether the power jumps promptly or rises on a period set by the delayed neutrons.

Example 4 (shielding):
Find how many factors of two the dose rate must fall by and how thick one half-value layer is, then ask whether scattered photons must be added back through a buildup factor.

Example 5 (decay and activity):
The activity is the decay constant times the number of nuclei present; write how that number changes when the nuclide is produced and decays at the same time.

Example 6 (thermal hydraulics):
The heat generated per unit length of the rod crosses the fuel, the gap, the clad and the coolant film in series; add the temperature drops across each, working inward from the coolant.

Example 7 (enrichment):
Write the mass balances on the total uranium and on U-235 for the feed, the product and the tails; the separative work then follows from the value function of each stream.

## units

b, mb, cm^2, cm^-1, cm^-3, atoms/cm^3, n/(cm^2 s), cm, m, mm, eV, keV, MeV, J, MJ, W, kW, MW, MWt, MWe, W/cm, kW/m, W/cm^3, W/(m K), W/(m^2 K), K, degC, s, min, h, days, years, s^-1, Bq, kBq, MBq, GBq, Ci, mCi, Gy, mGy, Sv, mSv, mSv/h, uSv/h, rem, mrem, pcm, dollars, cents, kg, g, t, MWd/kg, GWd/t, kg SWU, percent

## tools

NUCLEAR ENGINEERING ADDITIONS TO THE TOOL: scipy.constants has Avogadro's number (N_A), the electronvolt (eV) and the atomic mass unit (atomic_mass) but no barn, so define \(1\) b \(= 10^{-24}\) cm\(^2\) yourself; numpy and scipy.integrate.solve_ivp handle decay chains, poison buildup and burnup (the Bateman equations) and point kinetics with six delayed groups; numpy.roots or scipy.optimize.brentq solve the inhour equation for the stable period and transcendental criticality conditions (a reflected slab or sphere, an extrapolation distance); scipy.special has the Bessel functions of cylindrical geometry (j0, j1, i0, k0) and the zeros of \(J_0\) (jn_zeros); scipy.integrate.quad integrates flux and power shapes and doses over time. Use them to check what you work out, not to replace the working:
- Recompute every number density, macroscopic cross section, reaction rate and power from the data you state, printing the unit of each step, since a lost factor of \(10^{-24}\) or of \(N_A\) is the commonest slip.
- Check a kinetics answer by solving the inhour equation or integrating the point kinetics equations, and a decay or burnup answer by integrating the chain; compare with your closed form.
- Check a criticality or flux result by substituting it back into the diffusion equation and its boundary conditions.
- Use the nuclear data the question gives when it gives them; otherwise quote the values you used (thermal cross sections at \(0.0253\) eV, delayed-neutron data, half-lives) so a student working from a different table can follow.
