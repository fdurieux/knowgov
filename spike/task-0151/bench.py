"""SPIKE (task-0151, doc-0021 S3, G4): latency per call of the reader for cargo_quote under three
designs, on the store KG_STORE names (rdflib with KG_RDFLIB_FILE, or neo4j). Never merged.

    KG_STORE=rdflib KG_RDFLIB_FILE=store.ttl python spike/task-0151/bench.py --out rdflib.json
    python spike/task-0151/bench.py --out neo4j.json      # Neo4j at KG_NEO4J_URI

The store holds S1, loaded beforehand by ``gate_cli.py --scenario S1 --as-of record``. Per design and
per call (gate_verdict as of the record; register_nodes for CAP-0002, a register read): one cold call,
then --n warm calls, wall time each, median and p95. (a) a child process per call; (b) a lazy pool,
one stdio child per subject, cold = spawn + initialize + first call; (c) the subject as a value,
in-process: cold = a fresh interpreter's import + server + first call, measured inside it.
The answers are checked equal across the three before any number is kept."""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))
import subject_dispatch as sd  # noqa: E402

CALLS = [("gate_verdict", {"as_of": "record"}), ("register_nodes", {"node": "CAP-0002"})]


def stats(xs: list[float]) -> dict:
    s = sorted(xs)
    p95 = s[min(len(s) - 1, max(0, round(0.95 * len(s)) - 1))]
    return {"n": len(s), "median_s": round(statistics.median(s), 4), "p95_s": round(p95, 4),
            "min_s": round(s[0], 4), "max_s": round(s[-1], 4)}


def timed(fn):
    t = time.perf_counter()
    out = fn()
    return time.perf_counter() - t, out


def strip(r: dict) -> dict:
    """The answer, without what differs by process (none expected; kept for a fair equality)."""
    return r.get("structuredContent", r)


COLD_C = r"""
import json, sys, time
t0 = time.perf_counter()
sys.path.insert(0, sys.argv[1])
import mcp_server
s = mcp_server.Server(mcp_server.Tools())
r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": sys.argv[2], "arguments": json.loads(sys.argv[3])}})
t1 = time.perf_counter()
print(json.dumps({"in_process_s": t1 - t0, "result": r["result"]}, default=str))
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    root = sd.resolve("cargo_quote")
    os.environ["KG_SUBJECT"] = str(root)
    import mcp_server
    out = {"store": os.environ.get("KG_STORE", "neo4j"), "subject": "cargo_quote", "n_warm": a.n,
           "python": sys.version.split()[0], "designs": {}}
    answers: dict[str, dict] = {}
    # (a) a child process per call
    da = {}
    for tool, args in CALLS:
        cold, r = timed(lambda: sd.via_child(root, tool, args))
        warm = [timed(lambda: sd.via_child(root, tool, args))[0] for _ in range(a.n)]
        da[tool] = {"cold_s": round(cold, 4), "warm": stats(warm)}
        answers[f"a:{tool}"] = strip(r)
    out["designs"]["a_child_per_call"] = da
    # (b) a lazy pool, one child per subject
    pool = sd.Pool()
    db = {}
    try:
        first = True
        for tool, args in CALLS:
            cold, r = timed(lambda: pool.call(root, tool, args))
            warm = [timed(lambda: pool.call(root, tool, args))[0] for _ in range(a.n)]
            db[tool] = {"cold_s": round(cold, 4), "cold_includes_spawn": first, "warm": stats(warm)}
            first = False
            answers[f"b:{tool}"] = strip(r)
    finally:
        pool.close()
    out["designs"]["b_pool_per_subject"] = db
    # (c) the subject as a value, in-process
    dc = {}
    server = mcp_server.Server(mcp_server.Tools())
    call = lambda tool, args: server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",  # noqa: E731
                                             "params": {"name": tool, "arguments": args}})["result"]
    for tool, args in CALLS:
        t = time.perf_counter()
        p = subprocess.run([sys.executable, "-c", COLD_C, str(ROOT / "harness"), tool, json.dumps(args)],
                           capture_output=True, text=True, env=os.environ.copy(), timeout=300)
        wall = time.perf_counter() - t
        got = json.loads(p.stdout)
        warm = [timed(lambda: call(tool, args))[0] for _ in range(a.n)]
        dc[tool] = {"cold_s": round(got["in_process_s"], 4), "cold_wall_with_interpreter_s": round(wall, 4), "warm": stats(warm)}
        answers[f"c:{tool}"] = strip(got["result"])
    out["designs"]["c_subject_as_value"] = dc
    for tool, _ in CALLS:
        a_, b_, c_ = (answers[f"{d}:{tool}"] for d in "abc")
        assert a_ == b_ == c_, f"{tool}: the designs answer differently"
    out["answers_equal"] = True
    out["gate_verdict"] = answers["a:gate_verdict"].get("verdict")
    a.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
