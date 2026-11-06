"""Statement and branch coverage of the test suite, standard library only (task-0159, V1).

    python tools/coverage_stdlib.py [--out FILE] [--subject DIR]

Runs ``tests/run_tests.py`` in this process under ``sys.monitoring`` (CPython 3.12 or later; no
coverage package, no new dependency) and reports, per module and in total, the statements and the
branches the suite reached, against a declared denominator:

- **counted**: every ``.py`` under ``harness/``, ``demo/app/``, ``tools/``, ``demo/tools/``, ``instance/`` and ``.claude/hooks/``;
- **left out, by name and why**: ``tests/`` (the measurer's own), ``subjects/*/vendor`` and ``demo/model``,
  ``demo/register`` (vendored bytes, pinned by digest, not ours to cover), ``subjects/*/oracle`` (run only
  in child processes).

A statement is a line some code object's line table names. A branch is one outcome of a conditional
jump in the bytecode (``POP_JUMP_IF_*`` and ``FOR_ITER``): each has two, taken and not taken. Only code
that runs in this process is seen. A child process the suite starts (a check tool, a server, the
worker) is not instrumented, so nothing here claims integration coverage. Exit 0 when the suite
passed, else the suite's exit code; the report is written either way.
"""
from __future__ import annotations

import argparse
import dis
import json
import os
import runpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTED = ["harness", "demo/app", "tools", "demo/tools", "instance", ".claude/hooks"]
LEFT_OUT = {
    "tests": "the measurer's own code",
    "subjects/*/vendor": "vendored bytes, pinned by digest",
    "demo/model": "vendored bytes, pinned by digest",
    "demo/register": "vendored bytes, pinned by digest",
    "subjects/*/oracle": "run only in child processes, which are not instrumented",
}
BRANCH_OPS = {"POP_JUMP_IF_FALSE", "POP_JUMP_IF_TRUE", "POP_JUMP_IF_NONE", "POP_JUMP_IF_NOT_NONE", "FOR_ITER"}


def counted_files() -> list[Path]:
    files = []
    for d in COUNTED:
        for p in sorted((ROOT / d).rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            if "__pycache__" in rel or "/vendor/" in rel or rel.startswith(("demo/model/", "demo/register/")):
                continue
            files.append(p)
    return files


def _codes(code):
    yield code
    for c in code.co_consts:
        if hasattr(c, "co_code"):
            yield from _codes(c)


def _key(code) -> tuple:
    return (code.co_filename, getattr(code, "co_qualname", code.co_name), code.co_firstlineno)


def denominator(path: Path) -> tuple[set[int], set[tuple], dict]:
    """The file's statements (line numbers) and branches ((code key, offset, outcome)), from its compiled code."""
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    lines, branches, targets = set(), set(), {}
    for c in _codes(code):
        lines.update(ln for _s, _e, ln in c.co_lines() if ln is not None and ln > 0)
        for ins in dis.get_instructions(c):
            if ins.opname in BRANCH_OPS:
                k = (_key(c), ins.offset)
                branches.add((*k, "taken"))
                branches.add((*k, "not taken"))
                targets[k] = ins.argval   # the jump's destination offset
    return lines, branches, targets


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(ROOT / "runs" / "coverage.json"))
    ap.add_argument("--subject", help="KG_SUBJECT for the suite (default: the environment's)")
    args = ap.parse_args(argv)
    if sys.version_info < (3, 12) or not hasattr(sys, "monitoring"):
        print("coverage_stdlib: needs CPython 3.12 or later (sys.monitoring)", file=sys.stderr)
        return 2
    if args.subject:
        os.environ["KG_SUBJECT"] = args.subject
    files = counted_files()
    scope = {str(p) for p in files}
    want = {str(p): denominator(p) for p in files}
    targets = {k: v for _l, _b, t in want.values() for k, v in t.items()}
    hit_lines: dict[str, set[int]] = {f: set() for f in scope}
    hit_branches: set[tuple] = set()
    M = sys.monitoring
    tool = M.COVERAGE_ID
    M.use_tool_id(tool, "knowgov-coverage")

    def on_line(code, line):
        f = code.co_filename
        if f not in scope:
            return M.DISABLE
        hit_lines[f].add(line)
        return M.DISABLE   # a line once seen is covered; no further events from it

    def on_branch(code, src, dest):
        if code.co_filename not in scope:
            return M.DISABLE
        k = (_key(code), src)
        outcome = "taken" if targets.get(k) == dest else "not taken"
        hit_branches.add((*k, outcome))
        if (*k, "taken") in hit_branches and (*k, "not taken") in hit_branches:
            return M.DISABLE
        return None

    M.register_callback(tool, M.events.LINE, on_line)
    M.register_callback(tool, M.events.BRANCH, on_branch)
    M.set_events(tool, M.events.LINE | M.events.BRANCH)
    t0 = time.monotonic()
    code = 0
    cwd, path0 = os.getcwd(), list(sys.path)
    os.chdir(ROOT)
    try:
        sys.argv = [str(ROOT / "tests" / "run_tests.py")]
        runpy.run_path(str(ROOT / "tests" / "run_tests.py"), run_name="__main__")
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    finally:
        M.set_events(tool, 0)
        M.free_tool_id(tool)
        os.chdir(cwd)
        sys.path[:] = path0
    modules = []
    for f in sorted(want):
        lines, branches, _t = want[f]
        got_l = hit_lines[f] & lines
        got_b = {b for b in hit_branches if b[0][0] == f} & branches
        modules.append({"module": Path(f).relative_to(ROOT).as_posix(), "statements": len(lines), "statements_hit": len(got_l),
                        "branches": len(branches), "branches_hit": len(got_b)})
    tot = {k: sum(m[k] for m in modules) for k in ("statements", "statements_hit", "branches", "branches_hit")}
    report = {"schema": "coverage", "version": 1, "python": sys.version.split()[0], "subject": os.environ.get("KG_SUBJECT") or "",
              "suite_exit": code, "seconds": round(time.monotonic() - t0, 1),
              "denominator": {"counted": COUNTED, "files": len(files), "left_out": LEFT_OUT,
                              "statement": "a line a code object's line table names",
                              "branch": "each outcome (taken, not taken) of a conditional jump: " + ", ".join(sorted(BRANCH_OPS))},
              "scope": "in-process only: the suite's own process; child processes (check tools, servers, the worker) are not "
                       "instrumented, so no integration coverage is claimed",
              "totals": {**tot, "statement_pct": round(100 * tot["statements_hit"] / max(1, tot["statements"]), 1),
                         "branch_pct": round(100 * tot["branches_hit"] / max(1, tot["branches"]), 1)},
              "modules": modules}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    t = report["totals"]
    print(f"coverage (in-process, {len(files)} files counted): statements {t['statements_hit']}/{t['statements']} "
          f"({t['statement_pct']}%), branches {t['branches_hit']}/{t['branches']} ({t['branch_pct']}%); suite exit {code}; {args.out}")
    return code


if __name__ == "__main__":
    sys.exit(main())
