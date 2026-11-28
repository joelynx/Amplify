"""The reclassification (owner 2026-11-25) after the first pass (Sonnet medium): one adjudication pass by Opus medium.

  python passes_reclass.py adjud   out/ -> pass1.json; rows whose label is low confidence, not a node of taxonomy.json,
                            "Other: ..." or wastebasket go to in3/ (the same brief, Opus, candidates: the routed ones
                            plus pass 1's subject) + manifest3.json
  python passes_reclass.py final   out3/ overlays pass1 -> final.json (how: pass1 | opus | pass1-low): Opus's label when it is
                            a valid node, else pass 1's valid label, else wastebasket (subtopic null)
  python passes_reclass.py report  final.json -> R/taxonomy/$RECLASS_OUT/{final_labels.json, flags.csv, REPORT.md}
                            and held.json (flagged rows: needs data, broken text, key mismatch, open problem)
  python passes_reclass.py relabels  final.json -> bank_relabels.json for the placed rows: a valid new label from Opus
                            or a high/medium pass-1 label moves them (apply_relabels.py), anything else leaves them
"""
import collections
import csv
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build7 import ROOT, tree_nodes, write_batches  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
F = HERE / "full"
NODES = {(n["subject"], n["topic"], n["branch"], n["subtopic"]) for n in tree_nodes()}
SUBJECTS = {n[0] for n in NODES}
OUTDIR = ROOT / "taxonomy" / os.environ["RECLASS_OUT"]  # e.g. full_run_20261201_reclass


def read(d: str) -> dict[int, dict]:
    got = {}
    for f in sorted((F / d).glob("*.jsonl")):
        for line in f.read_text("utf-8").splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                got[int(r["id"])] = r
    return got


def valid(r: dict | None) -> bool:
    return bool(r) and (r.get("subject"), r.get("topic"), r.get("branch"), r.get("subtopic")) in NODES


def main(step: str) -> None:
    routed = {r["id"]: r for r in json.loads((F / "routed.json").read_text("utf-8"))}
    if step == "adjud":
        p1 = read("out")
        (F / "pass1.json").write_text(json.dumps(p1, ensure_ascii=False), "utf-8")
        redo = []
        for q, r in routed.items():
            x = p1.get(q)
            if valid(x) and x.get("conf") in ("high", "medium"):
                continue
            cand = list(dict.fromkeys(r["cand"] + ([x["subject"]] if x and x.get("subject") in SUBJECTS else [])))
            redo.append(dict(r, cand=cand))
        (F / "routed3.json").write_text(json.dumps(redo, ensure_ascii=False), "utf-8")
        files = json.loads((F / "tree_files.json").read_text("utf-8"))
        write_batches(files, inp="in3", routed="routed3.json", manifest="manifest3.json")
        print(f"pass 1: {len(p1)} replies of {len(routed)}; to Opus: {len(redo)}",
              collections.Counter("missing" if q not in p1 else "invalid" if not valid(p1[q]) else p1[q].get("conf")
                                  for q in (r["id"] for r in redo)))
    elif step == "final":
        p1 = {int(k): v for k, v in json.loads((F / "pass1.json").read_text("utf-8")).items()}
        p3 = read("out3")
        final = {}
        for q, r in routed.items():
            a, b = p3.get(q), p1.get(q)
            if valid(a):
                lab, how = a, "opus"
            elif valid(b):
                lab, how = b, "pass1" if b.get("conf") in ("high", "medium") else "pass1-low"
            else:
                lab, how = (a or b or {"subject": None}), "wastebasket"
            final[q] = {"id": q, "subject": lab.get("subject"), "topic": lab.get("topic") if how != "wastebasket" else None,
                        "branch": lab.get("branch") if how != "wastebasket" else None,
                        "subtopic": lab.get("subtopic") if how != "wastebasket" else None, "how": how,
                        "conf": lab.get("conf"), "type": lab.get("type"), "key": lab.get("key") or [],
                        "supporting": lab.get("supporting") or [], "task": lab.get("task"), "flags": lab.get("flags") or [],
                        "note": lab.get("note") or "", "group": "text"}
        (F / "final.json").write_text(json.dumps(final, ensure_ascii=False), "utf-8")
        print(len(final), collections.Counter(v["how"] for v in final.values()))
    elif step == "report":
        final = {int(k): v for k, v in json.loads((F / "final.json").read_text("utf-8")).items()}
        OUTDIR.mkdir(parents=True, exist_ok=True)
        json.dump({str(q): v for q, v in sorted(final.items())}, open(OUTDIR / "final_labels.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0)
        held = sorted(q for q, v in final.items() if v["flags"] and v["subtopic"])
        with open(OUTDIR / "flags.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["question_id", "flags", "subject", "note"])
            for q in held:
                w.writerow([q, ";".join(final[q]["flags"]), final[q]["subject"], final[q]["note"]])
        waste = sorted(q for q, v in final.items() if not v["subtopic"])
        (HERE / "held.json").write_text(json.dumps(held), "utf-8")
        by_subj = collections.Counter(v["subject"] for v in final.values() if v["subtopic"])
        by_hint = collections.defaultdict(collections.Counter)
        for q, v in final.items():
            by_hint[routed[q]["hint"].split(", ", 1)[-1]][v["subject"] if v["subtopic"] else "wastebasket"] += 1
        L = ["# Reclassification with solutions (2026-11-26: rows first filed from the question alone, or whose solution changed)", "",
             f"{len(final)} rows: placed {sum(by_subj.values())}, wastebasket {len(waste)}, flagged {len(held)} (held from solving).",
             "Pass 1 Sonnet medium (solutions cut at 3,000 characters); low confidence, invalid nodes and wastebasket re-done by Opus medium.", "Placed rows move only on a valid label from Opus or a high/medium pass-1 label (bank_relabels.json); otherwise they stay.", "",
             "| subject | rows |", "|---|---|"] + [f"| {s} | {n} |" for s, n in by_subj.most_common()]
        L += ["", "## Dataset subfield -> subject", ""] + [f"- {h}: " + ", ".join(f"{s} {n}" for s, n in c.most_common())
                                                          for h, c in sorted(by_hint.items())]
        L += ["", "## Wastebasket ids", "", ", ".join(map(str, waste))]
        (OUTDIR / "REPORT.md").write_text("\n".join(L) + "\n", "utf-8")
        print(f"placed {sum(by_subj.values())}, wastebasket {len(waste)}, held {len(held)}; {OUTDIR}")

    elif step == "relabels":
        final = {int(k): v for k, v in json.loads((F / "final.json").read_text("utf-8")).items()}
        out, kept, same = {}, collections.Counter(), 0
        for q, v in final.items():
            now = routed[q]["now"]
            if now == ["Uncategorized"] * 3:
                continue  # apply_full_run places these from final_labels.json
            if not v["subtopic"] or v["how"] not in ("opus", "pass1"):
                kept[v["how"]] += 1
                continue
            new = [v["topic"], v["branch"], v["subtopic"]]
            if new == now:
                same += 1
                continue
            out[str(q)] = {"topic": new[0], "branch": new[1], "subtopic": new[2], "conf": v["conf"],
                           "how": "reclass-" + v["how"], "db": now}
        OUTDIR.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(OUTDIR / "bank_relabels.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        moved = collections.Counter((routed[int(q)]["now"][0], r["topic"]) for q, r in out.items())
        print(f"placed rows: move {len(out)}, unchanged {same}, kept (no confident label) {sum(kept.values())} {dict(kept)}")
        print("moves by (topic now -> topic new), top:", moved.most_common(12))
        with open(OUTDIR / "REPORT.md", "a", encoding="utf-8") as f:
            f.write(f"\n## Placed rows\n\nmoved {len(out)}, unchanged {same}, kept where they were {sum(kept.values())} "
                    f"(no confident new label: {dict(kept)}).\n")


if __name__ == "__main__":
    main(sys.argv[1])
