"""Re-render the summary table and the tree in taxonomy_draft.md from taxonomy.json.

Run from the repo root: python taxonomy/tools/render_taxonomy.py
taxonomy.json is the source of truth; the prose sections of taxonomy_draft.md are kept.
"""
import json
from pathlib import Path

TAX = Path(__file__).resolve().parents[1]
ORDER = ["Calculus", "Complex Analysis", "Linear Algebra and Differential Equations", "Algebra", "Abstract Algebra",
         "Number Theory", "Combinatorics", "Geometry", "Probability and Stochastic Processes", "Statistics",
         "Quantitative Finance", "Economics", "Mechanics", "Fluid Mechanics", "Heat Transfer", "Thermodynamics",
         "Electromagnetism and Special Relativity", "Quantum Mechanics", "Electrical Machinery",
         "Power Systems and Power Electronics", "Material Science", "Conventional Energy Technologies"]


def main() -> None:
    nodes = json.loads((TAX / "taxonomy.json").read_text(encoding="utf-8"))
    table = ["| Subject | Topics | Branches | Subtopics | ~Questions |", "|---|---|---|---|---|"]
    body = []
    tot = [0, 0, 0, 0]
    for subj in ORDER:
        ns = [n for n in nodes if n["subject"] == subj]
        topics = list(dict.fromkeys(n["topic"] for n in ns))
        nb = len({(n["topic"], n["branch"]) for n in ns})
        est = sum(n["est"] or 0 for n in ns)
        table.append(f"| {subj} | {', '.join(topics)} | {nb} | {len(ns)} | {est:,} |")
        tot = [tot[0] + len(topics), tot[1] + nb, tot[2] + len(ns), tot[3] + est]
        body.append(f"\n# {subj}\n_{len(topics)} topic(s), {nb} branches, {len(ns)} subtopics, ~{est} questions_\n")
        for t in topics:
            body.append(f"## {t}")
            for b in dict.fromkeys(n["branch"] for n in ns if n["topic"] == t):
                body.append(f"### {b}")
                for n in ns:
                    if n["topic"] == t and n["branch"] == b:
                        e = f" (~{n['est']})" if n["est"] is not None else ""
                        body.append(f"- **{n['subtopic']}** — {n['note']}{e}")
            body.append("")
    table.append(f"| **Total** | {tot[0]} | {tot[1]} | {tot[2]:,} | {tot[3]:,} |")
    path = TAX / "taxonomy_draft.md"
    text = path.read_text(encoding="utf-8")
    head, _, _ = text.partition("\n---\n# The tree\n")
    pre, _, rest = head.partition("## Summary\n")
    after_table = rest[rest.index("\nBranch sizes:"):]
    path.write_text(pre + "## Summary\n" + "\n".join(table) + "\n" + after_table + "\n---\n# The tree\n"
                    + "\n".join(body) + "\n", encoding="utf-8")
    print(f"rendered {tot[2]} subtopics in {tot[1]} branches")


if __name__ == "__main__":
    main()
