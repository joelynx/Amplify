"""Run the solver's Python under restrictions: the worker behind calc_server.py.

Usage: <calc venv python> -I -X utf8 calc_runner.py SCRATCH_DIR
One request per stdin line, {"code": "..."}; one reply per stdout line, {"output": "...", "error": bool}.
The worker stays up for the whole question (the imports below take ~5 s); each piece of code
runs in a fresh namespace, so variables do not carry over between calls. The server restarts the
worker after a timeout or a crash.

The solver checks its own numerical work with this (owner 2026-11-21: "we need some way to enable
tools to verify physics and engineering solves"). The code comes from a model that has read the
question text, so it is not trusted:
  * the process puts itself in a Windows job object first: one process only (it cannot start
    another), 1.5 GB of memory, killed when the server closes the job's last handle;
  * numpy, scipy, sympy, mpmath, pint and CoolProp are imported before the guard goes up;
  * then an audit hook (PEP 578: it cannot be removed) refuses sockets, new processes, ctypes,
    the registry, and any file access outside SCRATCH_DIR except reading the Python installation.
This is defence in depth against a model's mistakes or a planted instruction, not a security
boundary against a determined attacker; the server also kills the process at its time limit.
Output: whatever the code prints (stdout and stderr together), and a traceback on error.
"""

from __future__ import annotations

import ctypes
import os
import sys

SCRATCH = os.path.realpath(sys.argv[1])
MEMORY_BYTES = 1536 * 1024 * 1024


def enter_job() -> None:
    """Put this process in a new job: one process, a memory cap, killed with the job."""
    if os.name != "nt":
        return
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class BASIC(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class IO(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                    "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class EXTENDED(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    job = k32.CreateJobObjectW(None, None)
    if not job:
        raise SystemExit(f"calc runner: no job object ({ctypes.get_last_error()})")
    info = EXTENDED()
    info.BasicLimitInformation.LimitFlags = 0x8 | 0x100 | 0x2000 | 0x400  # ACTIVE_PROCESS, PROCESS_MEMORY, KILL_ON_JOB_CLOSE, DIE_ON_UNHANDLED_EXCEPTION
    info.BasicLimitInformation.ActiveProcessLimit = 1
    info.ProcessMemoryLimit = MEMORY_BYTES
    if not k32.SetInformationJobObject(wintypes.HANDLE(job), 9, ctypes.byref(info), ctypes.sizeof(info)):  # 9: ExtendedLimitInformation
        raise SystemExit(f"calc runner: job limits refused ({ctypes.get_last_error()})")
    if not k32.AssignProcessToJobObject(wintypes.HANDLE(job), wintypes.HANDLE(k32.GetCurrentProcess())):
        raise SystemExit(f"calc runner: cannot enter the job ({ctypes.get_last_error()})")


enter_job()

import fractions  # noqa: E402,F401
import io  # noqa: E402
import itertools  # noqa: E402,F401
import json  # noqa: E402
import math  # noqa: E402,F401
import traceback  # noqa: E402

import CoolProp.CoolProp  # noqa: E402,F401
import mpmath  # noqa: E402,F401
import numpy  # noqa: E402
import pint  # noqa: E402
import scipy  # noqa: E402
import scipy.constants  # noqa: E402,F401
import scipy.integrate  # noqa: E402,F401
import scipy.linalg  # noqa: E402,F401
import scipy.optimize  # noqa: E402,F401
import scipy.special  # noqa: E402,F401
import scipy.stats  # noqa: E402,F401
import sympy  # noqa: E402

try:  # thermo and chemicals (chemical engineering) load pandas, which reads the time zones from the registry
    import pandas  # noqa: E402,F401
except ImportError:  # a venv without the chemistry packages
    pass

UREG = pint.UnitRegistry()  # built before the guard: it reads its definition files
IN, OUT, ERR = sys.stdin, sys.stdout, sys.stderr  # the protocol streams, kept before user code can touch sys
INSTALL = tuple({os.path.realpath(p) + os.sep for p in (sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix)})
SCRATCH_SEP = SCRATCH + os.sep
BLOCKED = ("socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile", "os.fork",
           "os.kill", "_winapi.", "ctypes.", "winreg.", "msvcrt.", "webbrowser.", "urllib.", "http.", "ftplib.",
           "smtplib.", "sys.addaudithook", "sys.settrace", "sys.setprofile", "cpython.remote_debugger")
PATH_EVENTS = {"os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.chmod", "os.link", "os.symlink", "os.truncate",
               "os.utime", "shutil.rmtree", "shutil.copyfile", "shutil.move", "os.listdir", "os.scandir", "os.chdir",
               "glob.glob"}


def inside(path, roots) -> bool:
    if isinstance(path, int):  # an already open descriptor
        return True
    try:
        p = os.path.realpath(os.fsdecode(path))
    except (TypeError, ValueError):
        return False
    return p == SCRATCH or any(p.startswith(r) for r in roots)


def guard(event: str, args: tuple) -> None:
    if event.startswith(BLOCKED):
        raise PermissionError(f"not allowed here: {event}")
    if event == "open":
        path, mode = args[0], args[1] if len(args) > 1 else "r"
        writing = isinstance(mode, str) and any(c in mode for c in "wax+")
        if isinstance(mode, int):  # os.open flags
            writing = bool(mode & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
        if path is None or inside(path, (SCRATCH_SEP,)) or (not writing and inside(path, INSTALL)):
            return
        raise PermissionError(f"file access outside the working folder: {path}")
    if event in PATH_EVENTS:
        for a in args[:2]:
            if isinstance(a, (str, bytes, os.PathLike)) and not inside(a, (SCRATCH_SEP,)):
                if event in ("os.listdir", "os.scandir", "glob.glob") and inside(a, INSTALL):
                    continue
                raise PermissionError(f"file access outside the working folder: {a}")


def run(code: str) -> tuple[str, bool]:
    buf = io.StringIO()
    ns = {"__name__": "__main__", "np": numpy, "numpy": numpy, "sp": sympy, "sympy": sympy, "scipy": scipy,
          "ureg": UREG, "Q_": UREG.Quantity, "CP": CoolProp.CoolProp, "PropsSI": CoolProp.CoolProp.PropsSI}
    error = False
    sys.stdout = sys.stderr = buf
    try:
        exec(compile(code, "<calc>", "exec"), ns)
    except SystemExit:
        pass
    except BaseException:
        traceback.print_exc(limit=-6, file=buf)
        error = True
    finally:
        sys.stdout, sys.stderr = OUT, ERR
    return buf.getvalue(), error


def main() -> None:
    os.chdir(SCRATCH)
    sys.addaudithook(guard)
    OUT.write(json.dumps({"ready": True}) + "\n")
    OUT.flush()
    for line in IN:
        try:
            code = json.loads(line)["code"]
        except (ValueError, KeyError, TypeError):
            continue
        output, error = run(code)
        OUT.write(json.dumps({"output": output, "error": error}) + "\n")
        OUT.flush()


if __name__ == "__main__":
    main()
