"""Classification batches on the subscription accounts (owner 2026-11-23: "Is there anything you can use the other
accounts for? Don't hesitate to use them for tasks other than solving.").

A classification wave (taxonomy waves 1-5 ran as Claude Code subagents of the interactive session) sends each batch
file as ONE request through run_sub's transport: the pass's brief, the subject trees named in the batch header and
the tag file are the system prompt, the batch's question blocks the message, and the reply is JSON Lines (one object
per question). Everything run_sub enforces applies: the request check and the owner-accepted wrapping, the usage
cap, account rotation one account at a time, the probes, keep-awake. Only one of run_sub, run_subjects and this
script runs at a time (each refuses while another's lock exists), so only one account ever serves.

Wave folder layout (the prep scripts in the session scratchpad write it):
  <wave>/<brief>.md                the pass's instructions (reply format: JSON Lines only)
  <wave>/trees/TREE_*.md, <wave>/TAGS_*.md
  <wave>/<in>/<stem>.txt           "SUBJECTS: Name (trees\\FILE.md); ...", "TAGS: FILE.md", then the question blocks
  <wave>/<out>/<stem>_p1.jsonl     written here, one object per question with at least "id"

usage: run_classify.py verify --wave W --in in --brief CLASSIFY.md --model M --effort E [--accept]
       run_classify.py run    --wave W --in in --out out --brief CLASSIFY.md --model M --effort E [--workers N] [--wait-on-limit]
                              [--verify-in in]  (the start-up check sends that folder's first batch, whatever --in is)"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_sub  # noqa: E402
from common import load_config, now_iso, pipe_conn  # noqa: E402

LOCK = run_sub.PIPELINE_DIR / "run_classify.lock"
BLOCK_ID = re.compile(r"^#{8} \[(\d+)\]", re.M)


def batch_parts(path: Path) -> tuple[list[tuple[str, Path]], Path | None, str, list[int]]:
    """(subject trees, tag file, question text, question ids) of one batch file."""
    text = path.read_text(encoding="utf-8")
    head, _, body = text.partition("\n\n")
    wave = path.parent.parent
    trees, tags = [], None
    for line in head.splitlines():
        if line.startswith("SUBJECTS:"):
            for m in re.finditer(r"([^;()]+?)\s*\(([^)]+)\)", line[len("SUBJECTS:"):]):
                trees.append((m.group(1).strip(), wave / m.group(2).replace("\\", "/")))
        elif line.startswith("TAGS:"):
            tags = wave / line.split(":", 1)[1].strip()
    return trees, tags, body.strip() + "\n", [int(x) for x in BLOCK_ID.findall(body)]


def system_text(brief: Path, trees: list[tuple[str, Path]], tags: Path | None) -> str:
    parts = [brief.read_text(encoding="utf-8").strip()]
    for name, f in trees:
        parts.append(f"=== SUBJECT TREE: {name} ===\n" + f.read_text(encoding="utf-8").strip())
    if tags is not None:
        parts.append("=== TAG FILE ===\n" + tags.read_text(encoding="utf-8").strip())
    return "\n\n".join(parts) + "\n"


def system_file(stem: str, text: str) -> Path:
    run_sub.SUB_CWD.mkdir(parents=True, exist_ok=True)
    p = run_sub.SUB_CWD.parent / f".amplify-classify-{stem}.txt"
    p.write_bytes(text.encode("utf-8"))
    return p


def ccfg_for(cfg: dict, model: str) -> dict:
    return dict(cfg, solver=dict(cfg["solver"], model=model))


def parse_reply(text: str, ids: list[int]) -> tuple[list[dict], list[int]]:
    """The JSON objects for this batch's ids (first one per id) and the ids the reply left out."""
    got: dict[int, dict] = {}
    for line in text.splitlines():
        line = line.strip().strip("`")
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("id"), int) and obj["id"] in ids:
            got.setdefault(obj["id"], obj)
    return [got[i] for i in ids if i in got], [i for i in ids if i not in got]


def verify(cfg: dict, pc, a) -> bool:
    """run_sub's request check on the first batch: the request must pass every check and its wrapping must be one
    the owner accepted (--accept records that acceptance, as run_sub.py verify --accept does)."""
    first = sorted((Path(a.wave) / a.inp).glob("*.txt"))[0]
    trees, tags, body, _ = batch_parts(first)
    text = system_text(Path(a.wave) / a.brief, trees, tags)
    path = system_file("verify", text)
    rotation = [x for x in run_sub.load_accounts() if x.get("enabled", True) and run_sub.account_id(x)]
    if rotation:
        run_sub._ACTIVE_DIR[0] = str(Path(rotation[0]["dir"]))
    ccfg = ccfg_for(cfg, a.model)
    captured, out = run_sub.capture_request(ccfg, path, body, a.effort)
    rep = run_sub.check_request(ccfg, text, body, a.effort, captured, out, set())
    accepted = rep["fingerprint"] in run_sub.accepted_fingerprints(pc)
    if a.accept and rep["ok"]:
        summary = {"at": now_iso(), "ok": True, "fingerprint": rep["fingerprint"], "accepted": True,
                   "source": f"run_classify.py verify ({a.model}, {a.effort})",
                   "reports": [{k: v for k, v in rep.items() if k != "init"}]}
        pc.execute("INSERT INTO sub_verifications (created_at, claude_code_version, fingerprint, ok, accepted, report_json) "
                   "VALUES (?,?,?,?,?,?)", (now_iso(), rep["init"].get("claude_code_version"), rep["fingerprint"], 1, 1,
                                            json.dumps(summary)))
        pc.commit()
        accepted = True
    report = run_sub.PIPELINE_DIR / "outputs" / "_classify_verify.json"
    report.write_text(json.dumps({k: v for k, v in rep.items() if k != "init"}, indent=1, ensure_ascii=False), encoding="utf-8")
    for name, good, detail in rep["checks"]:
        if not good:
            print(f"  FAIL {name}  [{detail}]")
    print(f"batch {first.name} ({a.model}, {a.effort}): {'ok' if rep['ok'] else 'FAILED'}; wrapping "
          f"{(rep['fingerprint'] or '')[:16]} {'accepted' if accepted else 'NOT accepted (review ' + report.as_posix() + ', then --accept)'}")
    return rep["ok"] and accepted


def run(cfg: dict, pc, a) -> None:
    for other in (run_sub.LOCK, run_sub.SUBJECTS_LOCK):
        if other.exists():
            raise SystemExit(f"a solver is running ({other.as_posix()}): one at a time, so that only one account serves")
    if LOCK.exists() and not a.force_unlock:
        raise SystemExit(f"{LOCK.as_posix()} exists: another classification run may be going (pid {LOCK.read_text().strip()})")
    # the check always sends the --verify-in folder's first batch: Claude Code's billing header carries a checksum of
    # the message, so a fixed probe keeps the accepted fingerprint (as run_sub.py verify uses one fixed question)
    if not verify(cfg, pc, argparse.Namespace(**{**vars(a), "accept": False, "inp": a.verify_in})):
        raise SystemExit("the request check did not pass or its wrapping is not accepted (run_classify.py verify)")
    wave, out_dir = Path(a.wave), Path(a.wave) / a.out
    out_dir.mkdir(exist_ok=True)
    queue = [p for p in sorted((wave / a.inp).glob("*.txt")) if not (out_dir / f"{p.stem}_p1.jsonl").exists()]
    version = run_sub.subprocess.run([run_sub.claude_exe(cfg), "--version"], capture_output=True, text=True).stdout.split()[0]
    ccfg = ccfg_for(cfg, a.model)
    model = a.model
    LOCK.write_text(str(os.getpid()))
    print(json.dumps({"batches": len(queue), "model": model, "effort": a.effort, "workers": a.workers, "at": now_iso()}), flush=True)
    cap = run_sub.UsageCap((cfg.get("subscription") or {}).get("usage_cap") or {}, run_sub.LOGIN_FILE, run_sub.CAP_STATE,
                           run_sub.ACCOUNT_FILE)
    rotation = [x for x in run_sub.load_accounts() if x.get("enabled", True) and run_sub.account_id(x)]
    active = None
    if rotation:
        active = run_sub.pick_account(run_sub.load_accounts(), cap, [model])[0] or rotation[0]
        run_sub.use_account(active, cap)
    tries: dict[str, int] = {}
    t0, done_n = time.time(), 0
    run_sub.keep_awake(True)
    try:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            running: dict = {}
            while queue or running:
                while queue and len(running) < a.workers:
                    flying = [(model, s) for (_, _, s, _) in running.values()]
                    if cap.probe_due(model, flying):
                        got = run_sub.read_usage(ccfg, model, version, cap, run_sub.SUB_CWD.parent)
                        if got["kind"] in ("limited", "stop"):
                            break
                    if not cap.allows(model, flying):
                        break
                    p = queue.pop(0)
                    trees, tags, body, ids = batch_parts(p)
                    sf = system_file(p.stem, system_text(wave / a.brief, trees, tags))
                    fut = ex.submit(run_sub.call_claude, ccfg, sf, body, a.effort)
                    running[fut] = (p, ids, time.time(), cap.account)
                if not running:
                    if not queue:
                        break
                    nxt, hold = run_sub.pick_account(run_sub.load_accounts(), cap, [model],
                                                     skip={active["name"]} if active else ())
                    if nxt is not None:
                        print(json.dumps({"rotate": {"from": active and active["name"], "to": nxt["name"]}, "at": now_iso()}), flush=True)
                        run_sub.use_account(nxt, cap)
                        active = nxt
                        continue
                    if not a.wait_on_limit:
                        print(json.dumps({"stopped": "every account is held", "left": len(queue)}), flush=True)
                        break
                    secs = max(60, min(int((hold[0] if hold else time.time() + 900) - time.time()) + 120, 1020))
                    print(f"every account is held ({hold[1] if hold else 'cap'}); waiting {secs // 60} min", flush=True)
                    deadline = time.time() + secs
                    while time.time() < deadline:
                        time.sleep(min(60, max(1, deadline - time.time())))
                    if rotation:
                        active = run_sub.pick_account(run_sub.load_accounts(), cap, [model])[0] or active
                        run_sub.use_account(active, cap)
                    continue
                for fut in wait(running, return_when=FIRST_COMPLETED)[0]:
                    p, ids, start, acct = running.pop(fut)
                    out = fut.result()
                    info = run_sub.interpret(out, ccfg, version)
                    readings = run_sub.usage_readings(out)
                    tokens = int(((info.get("result") or {}).get("usage") or {}).get("output_tokens") or 0) if info["kind"] == "ok" else 0
                    cap.record(model, start, time.time(), readings, run_sub.spent_usd(out, info, cap.usd_per_token()), tokens, acct)
                    line = {"batch": p.stem, "outcome": info["kind"], "account": active and active["name"],
                            "seconds": out.get("seconds"), "usage": {w: u for w, (u, _) in readings.items()}}
                    if info["kind"] == "ok":
                        rows, missing = parse_reply(info["text"], ids)
                        if missing and tries.get(p.stem, 0) < 1:
                            tries[p.stem] = tries.get(p.stem, 0) + 1
                            queue.append(p)
                            line.update(retry=f"{len(missing)} of {len(ids)} ids missing")
                        else:
                            (out_dir / f"{p.stem}_p1.jsonl").write_text(
                                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
                            done_n += 1
                            line.update(rows=len(rows), missing=missing)
                    else:
                        tries[p.stem] = tries.get(p.stem, 0) + 1
                        line["why"] = info.get("why")
                        if info["kind"] in ("limited", "stop") or tries[p.stem] <= 2:
                            queue.insert(0, p)
                    print(json.dumps({**line, "done": done_n, "left": len(queue) + len(running),
                                      "elapsed_min": round((time.time() - t0) / 60, 1)}, ensure_ascii=False), flush=True)
    finally:
        run_sub.keep_awake(False)
        LOCK.unlink(missing_ok=True)
    print(json.dumps({"finished": now_iso(), "batches_written": done_n, "left": len(queue)}), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("verify", "run"))
    ap.add_argument("--wave", required=True)
    ap.add_argument("--in", dest="inp", default="in")
    ap.add_argument("--out", default="out")
    ap.add_argument("--verify-in", default="in", help="run: folder whose first batch the start-up request check sends")
    ap.add_argument("--brief", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--effort", default="low")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--wait-on-limit", action="store_true")
    ap.add_argument("--force-unlock", action="store_true")
    ap.add_argument("--accept", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    pc = pipe_conn()
    if a.cmd == "verify":
        if not verify(cfg, pc, a):
            raise SystemExit(1)
    else:
        run(cfg, pc, a)


if __name__ == "__main__":
    main()
