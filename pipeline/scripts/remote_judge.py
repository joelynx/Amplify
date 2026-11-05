"""Judge on another machine, so every XeLaTeX / KaTeX check runs where the cores are.

The databases never leave this machine. `export` packs what `run.py judge` reads for
the questions waiting to be judged (their question rows, status, provenance and finals
rows, and their reply files) into pipeline/jobs/<job>/job.enc. On the other machine,
`run` judges the job with the same code (`run.judge`) in a scratch folder next to the
job and writes results.enc: every row and file the judge wrote. Back here, `import`
writes those rows and files, then fills the app fields (`apply_pending`), which is what
`run.py judge` does after judging.

Job and result files are AES-GCM encrypted (the repo is public) with the key in
pipeline/.judge_key, which git ignores: make it once with `keygen` and copy it to the
other machine by hand.

Usage (from the repo root):
  here:   python pipeline/scripts/remote_judge.py export [--ids 1,2] [--calibrate N] [--push]
  there:  git pull
          python pipeline/scripts/remote_judge.py run [--job NAME] [--workers N] [--push]
  here:   git pull
          python pipeline/scripts/remote_judge.py import [--job NAME] [--dry-run]
  either: python pipeline/scripts/remote_judge.py list | check | keygen

The job carries this machine's config.json, and the other machine refuses to judge
unless its judge code and locked dependencies hash the same as here (JUDGE_CODE), so it
judges exactly as this one would. A calibration job (--calibrate N) sends N questions this machine judged
already; `import` then compares the verdicts and files and writes nothing.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PIPELINE = SCRIPTS.parent
REPO = PIPELINE.parent
JOBS = PIPELINE / "jobs"
KEY_FILE = PIPELINE / ".judge_key"
MAGIC = b"AMPLIFY-JUDGE-1\n"
sys.path.insert(0, str(SCRIPTS))

# The code that decides a verdict or what the judge writes (config.json travels inside the
# job). Line endings are normalised, so a checkout with core.autocrlf hashes the same.
JUDGE_CODE = [
    "pipeline/scripts/run.py",
    "pipeline/scripts/common.py",
    "pipeline/scripts/validate.py",
    "pipeline/scripts/assemble.py",
    "pipeline/scripts/check_pdf.py",
    "pipeline/scripts/check_web.mjs",
    "pipeline/templates/*",
    "frontend/src/components/browser/LatexContent.tsx",
    "frontend/src/components/browser/latexWebSanitize.ts",
    "frontend/package-lock.json",
    "uv.lock",
]
# Reply files the judge reads; it writes validate_/feedback_/final files next to them.
SENT_FILES = ("solver_", "response_", "feedback_", "validate_", "review_", "hint.tex")
# What a calibration question is judged again from (its verdict files are compared, not sent).
CALIBRATION_FILES = ("solver_", "response_")
VERDICT_KEYS = ("ok", "errors", "hint_ok", "hint_errors", "answer_mismatch", "pdf_ok", "web_ok")


# --- shared -----------------------------------------------------------------------


def git(*args: str, check: bool = True) -> str:
    p = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    if check and p.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def code_hash() -> dict:
    files = {}
    for pattern in JUDGE_CODE:
        for p in sorted(REPO.glob(pattern)):
            if p.is_file():
                files[p.relative_to(REPO).as_posix()] = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    overall = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {"sha256": overall, "files": files}


def same_code(want: dict) -> None:
    have = code_hash()
    if have["sha256"] == want["sha256"]:
        return
    diff = sorted(f for f in set(have["files"]) | set(want["files"]) if have["files"].get(f) != want["files"].get(f))
    raise SystemExit("the judge code here differs from the job's (git pull, or check out the job's commit):\n  "
                     + "\n  ".join(diff))


def key() -> bytes:
    if not KEY_FILE.exists():
        raise SystemExit(f"{KEY_FILE.relative_to(REPO)} is missing: run `keygen` on the main machine, copy the file here")
    k = base64.urlsafe_b64decode(KEY_FILE.read_text(encoding="ascii").strip())
    if len(k) != 32:
        raise SystemExit(f"{KEY_FILE.relative_to(REPO)} does not hold a 32-byte key")
    return k


def seal(obj: dict, path: Path, job: str, kind: str) -> None:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    data = gzip.compress(json.dumps(obj, ensure_ascii=False).encode("utf-8"), compresslevel=9)
    blob = AESGCM(key()).encrypt(nonce, data, f"{job}|{kind}".encode())
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(MAGIC + nonce + blob)
    tmp.replace(path)


def unseal(path: Path, job: str, kind: str) -> dict:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    raw = path.read_bytes()
    if not raw.startswith(MAGIC):
        raise SystemExit(f"{path} is not a judge file")
    nonce, blob = raw[len(MAGIC):len(MAGIC) + 12], raw[len(MAGIC) + 12:]
    try:
        data = AESGCM(key()).decrypt(nonce, blob, f"{job}|{kind}".encode())
    except InvalidTag:
        raise SystemExit(f"{path} does not open with this key (or belongs to another job)") from None
    return json.loads(gzip.decompress(data).decode("utf-8"))


def file_text(p: Path) -> str:
    # surrogateescape keeps any non-UTF-8 byte; json escapes it and it is restored on write
    return p.read_bytes().decode("utf-8", "surrogateescape")


def put_file(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8", "surrogateescape"))


def job_dirs() -> list[Path]:
    return sorted(p for p in JOBS.iterdir() if (p / "job.enc").exists()) if JOBS.exists() else []


def pick_job(name: str | None, want: str) -> Path:
    if name:
        d = JOBS / name
        if not (d / "job.enc").exists():
            raise SystemExit(f"no job {name} in {JOBS.relative_to(REPO)}")
        return d
    if want == "unjudged":
        left = [d for d in job_dirs() if not (d / "results.enc").exists()]
    else:
        left = [d for d in job_dirs() if (d / "results.enc").exists() and not (d / "imported.json").exists()]
    if not left:
        raise SystemExit(f"no {'job without results' if want == 'unjudged' else 'judged job left to import'}"
                         f" in {JOBS.relative_to(REPO)} (git pull?)")
    return left[0]


def rows(conn, sql: str, args=()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, args)]


def chunks(ids: list[int], n: int = 500):
    for i in range(0, len(ids), n):
        yield ids[i:i + n]


def by_ids(conn, sql: str, ids: list[int]) -> list[dict]:
    """sql has one `{}` where the id placeholders go."""
    out: list[dict] = []
    for part in chunks(ids):
        out += rows(conn, sql.format(",".join("?" * len(part))), part)
    return out


# --- export (main machine) ---------------------------------------------------------


def pending_job_ids() -> set[int]:
    ids: set[int] = set()
    for d in job_dirs():
        if not (d / "imported.json").exists():
            ids |= set(json.loads((d / "ids.json").read_text(encoding="utf-8"))) if (d / "ids.json").exists() else set()
    return ids


def calibration_ids(pc, n: int) -> list[int]:
    """Questions the subscription run's judge settled here (today's judge code), spread over
    sources, about 4 passed to 1 rejected."""
    sql = "SELECT question_id FROM status WHERE status=? AND batch_id LIKE 'sub:%' ORDER BY question_id"
    passed = [r[0] for r in pc.execute(sql, ("passed",))]
    retry = [r[0] for r in pc.execute(sql, ("retry",))]
    from common import q_dir

    def sample(pool: list[int], k: int) -> list[int]:
        step = max(1, len(pool) // max(k, 1))
        return [q for q in pool[::step] if any(q_dir(q).glob("validate_*.json"))][:k]

    k_retry = min(len(retry), n // 5)
    return sorted(sample(passed, n - k_retry) + sample(retry, k_retry))


def export(a) -> None:
    from common import OUTPUTS_DIR, PIPELINE_DB, QUESTION_COLS, app_db_path, load_config, now_iso

    if not a.allow_dirty:
        dirty = git("status", "--porcelain", "--", *JUDGE_CODE)
        if dirty:
            raise SystemExit("commit the judge code first (the other machine runs the committed code):\n" + dirty)
    key()
    cfg = load_config()
    pc = sqlite3.connect(f"file:{PIPELINE_DB.as_posix()}?mode=ro", uri=True)
    pc.row_factory = sqlite3.Row
    app = sqlite3.connect(f"file:{app_db_path(cfg).as_posix()}?mode=ro", uri=True)
    app.row_factory = sqlite3.Row
    kind = "calibrate" if a.calibrate else "judge"
    if a.calibrate:
        ids = calibration_ids(pc, a.calibrate)
    elif a.ids:
        ids = sorted({int(x) for x in a.ids.split(",") if x.strip()})
        bad = [q for q in ids if (pc.execute("SELECT status FROM status WHERE question_id=?", (q,)).fetchone() or [None])[0] != "received"]
        if bad:
            raise SystemExit(f"not waiting to be judged: {bad[:20]}")
    else:
        busy = set() if a.again else pending_job_ids()
        ids = [r[0] for r in pc.execute("SELECT question_id FROM status WHERE status='received' ORDER BY question_id")
               if r[0] not in busy]
    if not ids:
        raise SystemExit("nothing to judge" + ("" if a.again else " (questions in jobs not imported yet are left out; --again sends them again)"))

    status = {str(r["question_id"]): r for r in by_ids(pc, "SELECT * FROM status WHERE question_id IN ({})", ids)}
    if kind == "calibrate":
        for r in status.values():
            r.update(status="received", attempts=int(r["accepted_attempt"] or r["attempts"]), accepted_attempt=None,
                     assembled=0, hint_status="none", note=None, answer_mismatch=0)
    names = CALIBRATION_FILES if kind == "calibrate" else SENT_FILES
    files = {}
    for q in ids:
        d = OUTPUTS_DIR / str(q)
        for p in sorted(d.iterdir()) if d.exists() else []:
            if p.is_file() and p.name.startswith(names) and p.suffix in (".tex", ".json"):
                files[f"{q}/{p.name}"] = file_text(p)

    name = time.strftime("%Y%m%d-%H%M%S") + ("-calibrate" if kind == "calibrate" else "")
    job = {
        "format": 1, "job": name, "kind": kind, "created_at": now_iso(), "git_head": git("rev-parse", "HEAD"),
        "code": code_hash(), "config": cfg, "ids": ids,
        "questions": by_ids(app, f"SELECT {QUESTION_COLS} FROM questions WHERE question_id IN ({{}})", ids),
        "status": status,
        "provenance": by_ids(pc, "SELECT * FROM provenance WHERE question_id IN ({}) ORDER BY id", ids),
        "finals": by_ids(pc, "SELECT * FROM finals WHERE question_id IN ({})", ids),
        "files": files,
    }
    d = JOBS / name
    seal(job, d / "job.enc", name, "job")
    (d / "ids.json").write_text(json.dumps(ids) + "\n", encoding="utf-8")
    size = (d / "job.enc").stat().st_size / 1e6
    print(json.dumps({"job": name, "kind": kind, "questions": len(ids), "files": len(files), "mb": round(size, 1),
                      "git_head": job["git_head"][:10]}))
    ahead = git("rev-list", "--count", "@{u}..HEAD", check=False)
    if a.push:
        rel = d.relative_to(REPO).as_posix()
        git("add", f"{rel}/job.enc", f"{rel}/ids.json")
        git("commit", "-m", f"Add judge job {name} ({len(ids)} questions)")
        git("push")
        print(f"pushed; on the other machine: git pull, then remote_judge.py run --job {name}")
    elif ahead not in ("", "0"):
        print(f"note: {ahead} local commit(s) not pushed; the other machine needs them")


# --- run (judging machine) ---------------------------------------------------------


def tools() -> dict:
    """What the checks run on here, and whether it is all present."""
    from check_pdf import find_xelatex

    xe = find_xelatex()
    node = shutil.which("node")

    def first_line(cmd: list[str]) -> str:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return (out.stdout or out.stderr).strip().splitlines()[0]
        except Exception as e:  # noqa: BLE001
            return f"unavailable: {e}"

    fe = REPO / "frontend" / "node_modules"
    return {
        "machine": platform.node(), "os": platform.platform(), "cpus": os.cpu_count(), "python": platform.python_version(),
        "xelatex": first_line([xe, "--version"]) if xe else None,
        "node": first_line([node, "--version"]) if node else None,
        "frontend_modules": (fe / "katex").exists() and (fe / "esbuild").exists(),
    }


def warm_up(cfg: dict, scratch: Path) -> None:
    """One compile and one web check before the pool starts: TeX builds its format and
    fetches packages, node bundles the renderer, all once instead of in every worker."""
    import common
    from check_pdf import check_pdf

    sample = "Warm-up: \\(x^2 + \\frac{1}{2}\\), \\[\\int_0^1 f(t)\\,dt\\]"
    r = check_pdf(sample, cfg=cfg)
    w = common.check_web_text(sample, scratch / "_warm_up")
    if not (r["ok"] and w["ok"]):
        raise SystemExit(f"the checks do not work here yet: xelatex {r['errors'][:3]} {r.get('log_tail', '')[-400:]}; "
                         f"web {w['errors'][:3]}")


def build_scratch(job: dict, work: Path, cfg: dict) -> None:
    import common

    cols = [c.strip() for c in common.QUESTION_COLS.split(",")]
    app = sqlite3.connect(cfg["paths"]["app_db"])
    app.execute(f"CREATE TABLE questions ({', '.join(c + (' INTEGER PRIMARY KEY' if c == 'question_id' else '') for c in cols)})")
    app.executemany(f"INSERT INTO questions ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [[q[c] for c in cols] for q in job["questions"]])
    app.commit()
    app.close()
    pc = common.pipe_conn()
    for table, rs in (("status", list(job["status"].values())), ("provenance", job["provenance"]), ("finals", job["finals"])):
        for r in rs:
            pc.execute(f"INSERT INTO {table} ({','.join(r)}) VALUES ({','.join('?' * len(r))})", list(r.values()))
    pc.commit()
    pc.close()
    for rel, text in job["files"].items():
        put_file(common.OUTPUTS_DIR / rel, text)


def collect(job: dict, work: Path) -> dict:
    import common

    pc = sqlite3.connect(common.PIPELINE_DB)
    pc.row_factory = sqlite3.Row
    ids = job["ids"]
    sent_prov = {r["id"] for r in job["provenance"]}
    finals_before = {str(r["question_id"]): r for r in job["finals"]}
    finals = {str(r["question_id"]): r for r in by_ids(pc, "SELECT * FROM finals WHERE question_id IN ({})", ids)}
    files = {}
    for p in sorted(common.OUTPUTS_DIR.rglob("*")):
        rel = p.relative_to(common.OUTPUTS_DIR).as_posix()
        if p.is_file() and p.suffix != ".pdf" and job["files"].get(rel) != (text := file_text(p)):
            files[rel] = text
    out = {
        "status": {str(r["question_id"]): r for r in by_ids(pc, "SELECT * FROM status WHERE question_id IN ({})", ids)},
        "events": rows(pc, "SELECT question_id, stage, detail, created_at FROM events ORDER BY id"),
        "provenance": [r for r in rows(pc, "SELECT * FROM provenance ORDER BY id") if r["id"] not in sent_prov],
        "finals": {q: r for q, r in finals.items() if finals_before.get(q) != r},
        "files": files,
    }
    pc.close()
    return out


def run_job(a) -> None:
    d = pick_job(a.job, "unjudged")
    name = d.name
    job = unseal(d / "job.enc", name, "job")
    same_code(job["code"])
    work = d / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    # The judge modules read these when they load: point them at the scratch folder first.
    os.environ["AMPLIFY_PIPELINE_DB"] = str(work / "pipeline.db")
    os.environ["AMPLIFY_PIPELINE_OUTPUTS"] = str(work / "outputs")
    import common
    import run

    if common.PIPELINE_DB != work / "pipeline.db" or common.OUTPUTS_DIR != work / "outputs":
        raise SystemExit("the judge modules were loaded before the scratch paths were set; not touching anything")
    cfg = job["config"]
    cfg["paths"]["app_db"] = str(work / "app.db")
    env = tools()
    if not (env["xelatex"] and env["node"] and env["frontend_modules"]):
        raise SystemExit(f"missing tools (run pipeline/remote/setup.ps1): {env}")
    build_scratch(job, work, cfg)
    warm_up(cfg, work)
    workers = a.workers or os.cpu_count() or 4
    print(json.dumps({"job": name, "kind": job["kind"], "questions": len(job["ids"]), "workers": workers, **env}), flush=True)
    t0 = time.time()
    summary = run.judge(cfg, workers)
    res = {"format": 1, "job": name, "finished_at": common.now_iso(), "seconds": int(time.time() - t0), "workers": workers,
           "summary": dict(summary), "env": env, "code": job["code"]["sha256"], **collect(job, work)}
    seal(res, d / "results.enc", name, "results")
    print(json.dumps({"job": name, "seconds": res["seconds"], "judged": dict(summary), "files": len(res["files"]),
                      "events": len(res["events"])}), flush=True)
    if not a.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    if a.push:
        rel = (d / "results.enc").relative_to(REPO).as_posix()
        git("add", rel)
        git("commit", "-m", f"Judge results for job {name}")
        git("push")
        print("pushed; on the main machine: git pull, then remote_judge.py import")


# --- import (main machine) ---------------------------------------------------------


def calibrate_report(job: dict, res: dict, d: Path) -> None:
    import common

    pc = sqlite3.connect(f"file:{common.PIPELINE_DB.as_posix()}?mode=ro", uri=True)
    pc.row_factory = sqlite3.Row
    counts: Counter = Counter()
    diffs = []
    for q in job["ids"]:
        here = dict(pc.execute("SELECT status, attempts FROM status WHERE question_id=?", (q,)).fetchone())
        there = res["status"][str(q)]["status"]
        att = job["status"][str(q)]["attempts"]
        mine_v = common.OUTPUTS_DIR / str(q) / f"validate_{att}.json"
        v_here = {k: json.loads(file_text(mine_v)).get(k) for k in VERDICT_KEYS} if mine_v.exists() else None
        v_there_txt = res["files"].get(f"{q}/validate_{att}.json")
        v_there = {k: json.loads(v_there_txt).get(k) for k in VERDICT_KEYS} if v_there_txt else None
        final_here = common.OUTPUTS_DIR / str(q) / "final.tex"
        f_there = res["files"].get(f"{q}/final.tex")
        same_final = (not final_here.exists() and f_there is None) or (final_here.exists() and f_there == file_text(final_here))
        verdict_same = here["status"] == there or (here["status"] == "retry" and there in ("retry", "needs_human_review"))
        ok = verdict_same and v_here == v_there and (here["status"] != "passed" or same_final)
        counts["same" if ok else "different"] += 1
        if not ok:
            diffs.append({"question_id": q, "here": here["status"], "there": there, "validate_here": v_here,
                          "validate_there": v_there, "final_same": same_final})
    report = {"job": job["job"], "compared": len(job["ids"]), **counts, "seconds_there": res["seconds"],
              "env_there": res["env"], "differences": diffs}
    (d / "calibration.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (d / "imported.json").write_text(json.dumps({"at": common.now_iso(), "calibration": dict(counts)}) + "\n",
                                     encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "differences"}))
    for x in diffs[:15]:
        print(json.dumps(x, ensure_ascii=False)[:600])


def backup(src: sqlite3.Connection, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = sqlite3.connect(dest)
    src.backup(out)
    out.close()


def import_job(a) -> None:
    import common
    from apply_fields import apply_pending

    d = pick_job(a.job, "judged")
    name = d.name
    if (d / "imported.json").exists():
        raise SystemExit(f"job {name} was imported already ({d / 'imported.json'})")
    job = unseal(d / "job.enc", name, "job")
    res = unseal(d / "results.enc", name, "results")
    if res.get("code") != job["code"]["sha256"]:
        raise SystemExit("the results were made with other judge code than the job's")
    if job["kind"] == "calibrate":
        calibrate_report(job, res, d)
        return
    cfg = common.load_config()
    if os.environ.get("AMPLIFY_APP_DB"):  # tests point the import at a copy
        cfg["paths"]["app_db"] = os.environ["AMPLIFY_APP_DB"]
    pc = common.pipe_conn()
    # Only questions untouched here since the export get the other machine's verdict.
    take, moved = [], []
    for q in job["ids"]:
        now = common.get_status(pc, q)
        (take if now is not None and dict(now) == job["status"][str(q)] else moved).append(q)
    verdicts = Counter(res["status"][str(q)]["status"] for q in take)
    print(json.dumps({"job": name, "judged_there": res["summary"], "seconds_there": res["seconds"],
                      "machine": res["env"].get("machine"), "to_apply": len(take), "changed_here_since": moved[:50],
                      "verdicts": dict(verdicts)}), flush=True)
    if a.dry_run:
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup(pc, common.PIPELINE_DIR / "archive" / f"pipeline_before_judge_import_{name}_{stamp}.db")
    app = common.app_conn(cfg)
    app_path = common.app_db_path(cfg)
    backup(app, app_path.with_name(f"{app_path.name}.bak-{stamp}-pre-judge-import"))
    app.close()

    keep = {str(q) for q in take}
    for rel, text in res["files"].items():
        if rel.split("/", 1)[0] in keep:
            put_file(common.OUTPUTS_DIR / rel, text)
    with pc:
        for q in take:
            r = res["status"][str(q)]
            sets = [c for c in r if c != "question_id"]
            pc.execute(f"UPDATE status SET {', '.join(c + '=?' for c in sets)} WHERE question_id=?",
                       [r[c] for c in sets] + [q])
        pc.executemany("INSERT INTO events (question_id, stage, detail, created_at) VALUES (?,?,?,?)",
                       [(e["question_id"], e["stage"], e["detail"], e["created_at"]) for e in res["events"]
                        if str(e["question_id"]) in keep])
        for q, r in res["finals"].items():
            if q in keep:
                pc.execute(f"INSERT OR REPLACE INTO finals ({','.join(r)}) VALUES ({','.join('?' * len(r))})",
                           list(r.values()))
        pc.executemany("INSERT INTO provenance (question_id, field, value, prompt_version, created_at, applied_at) "
                       "VALUES (?,?,?,?,?,?)",
                       [(p["question_id"], p["field"], p["value"], p["prompt_version"], p["created_at"], p["applied_at"])
                        for p in res["provenance"] if str(p["question_id"]) in keep])
    fills = apply_pending(cfg, pc)
    common.write_progress(pc)
    common.log_event(pc, None, "remote_judge", f"imported job {name}: {dict(verdicts)}; fills {fills}")
    done = {"at": common.now_iso(), "applied": len(take), "verdicts": dict(verdicts), "left_out": moved,
            "field_fills": fills}
    (d / "imported.json").write_text(json.dumps(done, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(done))


# --- small commands ------------------------------------------------------------------


def keygen(_a) -> None:
    if KEY_FILE.exists():
        raise SystemExit(f"{KEY_FILE.relative_to(REPO)} exists already; keep it (jobs made with it need it)")
    KEY_FILE.write_text(base64.urlsafe_b64encode(os.urandom(32)).decode("ascii") + "\n", encoding="ascii")
    print(f"wrote {KEY_FILE.relative_to(REPO)}; copy it to the same place on the other machine (never commit it)")


def list_jobs(_a) -> None:
    for d in job_dirs():
        ids = json.loads((d / "ids.json").read_text(encoding="utf-8")) if (d / "ids.json").exists() else []
        state = "imported" if (d / "imported.json").exists() else "judged" if (d / "results.enc").exists() else "waiting"
        print(json.dumps({"job": d.name, "questions": len(ids), "state": state}))


def check(a) -> None:
    """Tools, key and code hash here; unless --no-compile, one test compile and web check."""
    import common

    env = tools()
    print(json.dumps({"code": code_hash()["sha256"][:16], "key": KEY_FILE.exists(), **env}), flush=True)
    if not (env["xelatex"] and env["node"] and env["frontend_modules"]):
        raise SystemExit("missing tools: run pipeline/remote/setup.ps1")
    if not a.no_compile:
        scratch = JOBS / "_check"
        warm_up(common.load_config(), scratch)
        shutil.rmtree(scratch, ignore_errors=True)
        print("test compile and web check ok")
    if not KEY_FILE.exists():
        raise SystemExit(f"{KEY_FILE.relative_to(REPO)} is missing: copy it from the main machine")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("export")
    p.add_argument("--ids")
    p.add_argument("--calibrate", type=int, metavar="N")
    p.add_argument("--again", action="store_true", help="also send questions that are in jobs not imported yet")
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument("--push", action="store_true")
    p = sub.add_parser("run")
    p.add_argument("--job")
    p.add_argument("--workers", type=int)
    p.add_argument("--keep-work", action="store_true")
    p.add_argument("--push", action="store_true")
    p = sub.add_parser("import")
    p.add_argument("--job")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("list")
    p = sub.add_parser("check")
    p.add_argument("--no-compile", action="store_true")
    sub.add_parser("keygen")
    a = ap.parse_args()
    {"export": export, "run": run_job, "import": import_job, "list": list_jobs, "check": check, "keygen": keygen}[a.cmd](a)


if __name__ == "__main__":
    main()
