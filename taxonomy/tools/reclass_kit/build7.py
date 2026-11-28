"""Write the sixth wave's trees (all 26 subjects, as taxonomy.json will be after the approved node moves: the MOVED
nodes left out, Waveguides shown in its new branch) and its batch files full/in/*.txt from full/routed.json, for
run_classify.py (one request per batch, so batches are smaller than the subagent waves' 150).
usage: python build_wave6.py"""
import collections
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = Path(os.environ.get("AMPLIFY_ROOT") or Path(__file__).resolve().parents[3])  # the repo; set AMPLIFY_ROOT when the kit runs from a copy

sys.stdout.reconfigure(encoding="utf-8")
F = HERE / "full"
MAXN, LIMIT = 50, 60_000


def tree_nodes() -> list[dict]:
    return json.loads((ROOT / "taxonomy" / "taxonomy.json").read_text("utf-8"))


def write_trees(T: list[dict]) -> dict[str, str]:
    files = {}
    (F / "trees").mkdir(parents=True, exist_ok=True)
    for subj in dict.fromkeys(n["subject"] for n in T):
        fn = "TREE_" + re.sub(r"[^A-Za-z0-9]+", "_", subj).strip("_") + ".md"
        tree = {}
        for n in (n for n in T if n["subject"] == subj):
            tree.setdefault(n["topic"], {}).setdefault(n["branch"], []).append(n)
        lines = [f"# Subject: {subj} (copy names exactly)"]
        for topic, branches in tree.items():
            lines += ["", f"## Topic: {topic}"]
            for branch, ns in branches.items():
                lines.append(f"### Branch: {branch}")
                lines += [f"- {n['subtopic']} — {n['note']}" for n in ns]
        (F / "trees" / fn).write_text("\n".join(lines) + "\n", "utf-8")
        files[subj] = fn
    (F / "tree_files.json").write_text(json.dumps(files, indent=1), "utf-8")
    return files


def write_batches(trees: dict[str, str], inp: str = "in", routed: str = "routed.json", manifest: str = "manifest.json") -> None:
    rows = json.loads((F / routed).read_text("utf-8"))
    d = F / inp
    d.mkdir(exist_ok=True)
    for f in d.glob("*.txt"):
        f.unlink()
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r["cand"][0]].append(r)
    out = []
    for prim, rs in sorted(groups.items(), key=lambda x: -len(x[1])):
        rs.sort(key=lambda r: (r["src"], r["id"]))
        chunks, cur, size = [], [], 0
        for r in rs:
            block = (f"######## [{r['id']}] {r['src']} | candidates: {'; '.join(r['cand'])}"
                     + (f" | hint: {r['hint']}" if r["hint"] else "") + f"\nQUESTION:\n{r['q']}\nSOLUTION:\n{r['sol'] or '(none)'}\n")
            if cur and (size + len(block) > LIMIT or len(cur) >= MAXN):
                chunks.append(cur)
                cur, size = [], 0
            cur.append((r, block))
            size += len(block)
        if cur:
            chunks.append(cur)
        tag = re.sub(r"[^A-Za-z]+", "", prim)[:10].lower()
        for k, ch in enumerate(chunks, 1):
            cnt = collections.Counter(s for r, _ in ch for s in r["cand"])
            subs = ([prim] + [s for s, _ in cnt.most_common() if s != prim])[:4]
            stem = f"{tag}_{k:03d}"
            head = "SUBJECTS: " + "; ".join(f"{s} (trees\\{trees[s]})" for s in subs) + "\nTAGS: TAGS_TEXT.md\n\n"
            (d / f"{stem}.txt").write_text(head + "\n".join(b for _, b in ch), "utf-8")
            out.append(dict(stem=stem, subjects=subs, n=len(ch), ids=[r["id"] for r, _ in ch],
                            sources=collections.Counter(r["src"] for r, _ in ch).most_common(3)))
    (F / manifest).write_text(json.dumps(out, ensure_ascii=False), "utf-8")
    print(len(out), "batches,", sum(m["n"] for m in out), "questions, sizes", min(m["n"] for m in out), "-", max(m["n"] for m in out))


if __name__ == "__main__":
    nodes = tree_nodes()
    files = write_trees(nodes)
    print(len(files), "trees,", len(nodes), "subtopics")
    write_batches(files)
