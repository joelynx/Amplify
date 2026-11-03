"""Create the 22 app subjects (curricular bundles) from taxonomy/taxonomy.json.

Usage: python taxonomy/tools/create_subjects.py [--apply]   (without --apply: dry run, no writes)

Each subject gets every topic its nodes sit under, plus any branches borrowed from another subject
(EXTRA_BRANCHES); a borrowed branch brings its topic in with that topic's other branches excluded.
Existing subjects with the same name get their payload replaced (the active flag is kept).
"""
import collections, json, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.core.filters import assemble_where  # noqa: E402
from app.core.models import Subject  # noqa: E402

DB = ROOT / "app" / "data" / "appdata" / "amplify.db"

EXTRA_BRANCHES = {"Quantitative Finance": [("Stochastic Processes", "Stochastic Calculus")]}

DESCRIPTIONS = {
    "Calculus": "Limits, continuity, derivatives and integrals (single and multivariable), sequences and series, "
                "real analysis (completeness, metric spaces, uniform convergence), Fourier series, vector calculus "
                "and optimization.",
    "Complex Analysis": "Analytic functions, Cauchy-Riemann equations, contour integrals, residues, series of complex "
                        "functions and conformal maps.",
    "Linear Algebra and Differential Equations": "Matrices, determinants, vector spaces, linear maps, eigenvalues, inner "
                                                 "products and decompositions; ODEs and systems, Laplace transforms, "
                                                 "series solutions, PDEs, stability and calculus of variations.",
    "Algebra": "Polynomials, equations and systems, inequalities, functional equations, recurrences, sums and "
               "products, exponentials and logarithms, trigonometric identities and complex numbers.",
    "Abstract Algebra": "Groups, rings, ideals, fields, field extensions, Galois theory and modules.",
    "Number Theory": "Divisibility, primes, congruences, Diophantine equations, arithmetic functions, quadratic "
                     "residues, continued fractions, digits and bases, p-adic valuation.",
    "Combinatorics": "Counting, binomial identities, inclusion-exclusion, generating functions, pigeonhole, graph "
                     "theory, games and invariants, combinatorial geometry, logic and algorithmic puzzles.",
    "Geometry": "Euclidean plane and solid geometry, triangles and circles, coordinate geometry and conics, "
                "transformations, trigonometry in figures, geometric inequalities, areas and volumes.",
    "Probability and Stochastic Processes": "Probability, random variables, distributions, expectation, limit "
                                            "theorems, Markov chains, random walks, Poisson processes, Brownian "
                                            "motion, martingales and stochastic calculus.",
    "Statistics": "Estimation, sufficiency, hypothesis tests, confidence intervals, regression, Bayesian inference "
                  "and sampling distributions.",
    "Quantitative Finance": "Derivatives pricing, binomial trees, Black-Scholes, Greeks, interest rates and bonds, "
                            "portfolio theory and risk. Also includes the Stochastic Calculus branch of Stochastic "
                            "Processes.",
    "Economics": "Macroeconomics.",
    "Mechanics": "Kinematics, Newtonian dynamics, energy and momentum, rigid bodies, gravitation and orbits, "
                 "oscillations and waves, Lagrangian and Hamiltonian mechanics, statics, and solid mechanics "
                 "(stress, strain, bending, torsion).",
    "Fluid Mechanics": "Fluid properties, hydrostatics, Bernoulli, control-volume analysis, viscous and pipe flow, "
                       "boundary layers, compressible flow, open-channel flow and turbomachinery.",
    "Heat Transfer": "Conduction, convection, radiation, heat exchangers, boiling and condensation, process "
                     "heat-transfer equipment.",
    "Thermodynamics": "Laws of thermodynamics, properties and gas laws, cycles, entropy, kinetic theory, phase "
                      "transitions and psychrometrics.",
    "Electromagnetism and Special Relativity": "Electrostatics, magnetostatics, circuits, induction, Maxwell's "
                                               "equations, EM waves, geometric and wave optics, special relativity.",
    "Quantum Mechanics": "Quantum mechanics, atomic, nuclear and particle physics.",
    "Electrical Machinery": "Magnetic circuits, transformers, DC, induction, synchronous and special machines.",
    "Power Systems and Power Electronics": "Power-electronic converters (rectifiers, choppers, inverters, "
                                           "cycloconverters), drives and power-system analysis.",
    "Material Science": "Crystal structure, defects, diffusion, mechanical properties, phase diagrams, heat treatment, "
                        "material classes, electrical, magnetic and optical properties, corrosion.",
    "Conventional Energy Technologies": "Power-plant engineering: steam plants, boilers, turbines, condensers, "
                                        "cooling towers, fuels and combustion, gas turbine, diesel, hydro and "
                                        "nuclear plants, plant economics.",
}


def build() -> list[Subject]:
    nodes = json.loads((ROOT / "taxonomy" / "taxonomy.json").read_text("utf-8"))
    topics, branches = collections.defaultdict(list), collections.defaultdict(list)
    for n in nodes:
        if n["topic"] not in topics[n["subject"]]: topics[n["subject"]].append(n["topic"])
        if n["branch"] not in branches[n["topic"]]: branches[n["topic"]].append(n["branch"])
    if set(topics) != set(DESCRIPTIONS):
        raise SystemExit(f"subjects in taxonomy.json and DESCRIPTIONS differ: {set(topics) ^ set(DESCRIPTIONS)}")
    out = []
    for name in DESCRIPTIONS:
        ts, excluded = list(topics[name]), {}
        for topic, branch in EXTRA_BRANCHES.get(name, []):
            if branch not in branches[topic]:
                raise SystemExit(f"{name}: no branch {topic} > {branch} in taxonomy.json")
            ts.append(topic)
            excluded[topic] = [b for b in branches[topic] if b != branch]
        out.append(Subject(name=name, topics=ts, excluded_branches=excluded, description=DESCRIPTIONS[name]))
    return out


def main(apply: bool) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    subjects = build()
    conn = sqlite3.connect(DB)
    try:
        conn.execute("BEGIN")
        before = {r[0] for r in conn.execute("SELECT name FROM subjects")}
        for s in subjects:
            conn.execute("INSERT INTO subjects (name, payload, is_active) VALUES (?, ?, 0) "
                         "ON CONFLICT(name) DO UPDATE SET payload = excluded.payload",
                         (s.name, json.dumps(s.to_payload())))
            where, params = assemble_where({"in_syllabus_only": False, "reuse_questions": True}, s.to_payload())
            n = conn.execute(f"SELECT COUNT(*) FROM questions WHERE {where}", params).fetchone()[0]
            print(f"{'updated' if s.name in before else 'created'} {s.name}: {len(s.topics)} topics, {n:,} questions")
        if apply:
            conn.commit(); print("committed")
        else:
            conn.rollback(); print("dry run: rolled back")
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


if __name__ == "__main__":
    main("--apply" in sys.argv[1:])
