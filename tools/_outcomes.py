"""The check tools' outcomes, machine-readable (task-0159, V1).

A check tool exits through ``run(main)``. When ``KG_OUTCOMES`` names a file, one JSON line is appended
to it per invocation: the tool, its arguments, its exit code and what that means (pass 0, fail 1,
cannot run 2, under the gate contract the tools share), its seconds, and, for a tool that reports its
checks one by one through ``check()`` and ``skip()``, each check with pass, fail or skip and the skip's
reason. Without ``KG_OUTCOMES`` nothing is written and the tool behaves exactly as before.
"""
from __future__ import annotations

import json
import os
import sys
import time

_checks: list[dict] = []


def check(label: str, ok) -> bool:
    """Record one check's outcome; returns whether it held."""
    _checks.append({"check": label, "outcome": "pass" if ok else "fail"})
    return bool(ok)


def skip(label: str, reason: str) -> None:
    """Record a check not run here, with why."""
    _checks.append({"check": label, "outcome": "skip", "reason": reason})


def _meaning(code) -> str:
    if code in (0, None):
        return "pass"
    return "cannot run" if code == 2 else "fail"


def run(main) -> int:
    """``main()``'s exit code, recorded; an exception propagates after its record is written."""
    t0 = time.monotonic()
    code, error = 1, None
    try:
        code = main()
        return code
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) or e.code is None else 1   # sys.exit("FAIL: ...") exits 1
        raise
    except BaseException as e:
        error = f"{type(e).__name__}: {str(e).splitlines()[0][:300] if str(e) else ''}"
        raise
    finally:
        path = os.environ.get("KG_OUTCOMES")
        if path:
            row = {"tool": os.path.basename(sys.argv[0]), "argv": sys.argv[1:], "exit": 0 if code is None else code,
                   "outcome": "error" if error else _meaning(code), "seconds": round(time.monotonic() - t0, 3),
                   "checks": _checks}
            if error:
                row["error"] = error
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
