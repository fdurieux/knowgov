"""Peak transaction memory of a Neo4j load against its statement count (task-0176).

    python tools/measure_load_memory.py --disposable [--out FILE] [--scale 1,2,4,8,16,32]

A Neo4j writer's whole unit is one transaction (decision-0014), so the server's transaction memory bounds
a load. This measures, on a disposable Neo4j, the unit's peak estimated heap (``SHOW TRANSACTIONS``'s
``estimatedUsedHeapMemory``, sampled every 20 ms from a second session while the unit runs and commits)
against what the unit holds as ``harness/load_memory.py`` counts it before anything is written: every
statement (assertions plus fragments) it writes and every statement its wipes delete:

- a first unit that wipes whatever the store held;
- each scenario of the subject named by KG_SUBJECT, loaded as ``gate_cli`` loads it (one unit each);
- the subject's whole deterministic run, every scenario in one unit, as ``harness/run.py`` publishes it;
- a synthetic scale-up: the first scenario's kit loaded k times into one unit under k version tags,
  each followed by a unit of one copy, which deletes the k copies, so written and deleted vary apart.

It prints one JSON row per unit and, with ``--out``, writes them with the least-squares plane and the
largest residual; ``harness/load_memory.py`` carries the plane the pre-check uses. It wipes the store, so
it refuses without ``--disposable``. No model is called; the clock is pinned.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import _outcomes  # noqa: E402
sys.path[:0] = [str(ROOT / "harness")]
os.environ.setdefault("KG_CLOCK", "pinned")


class Sampler:
    """The peak estimated heap of the transactions a writer's token names, polled from its own session."""

    def __init__(self, driver, token: str):
        self.driver, self.token, self.peak, self.samples = driver, token, 0, 0
        self.stop = threading.Event()
        self.t = threading.Thread(target=self.run, daemon=True)

    def run(self):
        with self.driver.session() as s:
            while not self.stop.is_set():
                for r in s.run("SHOW TRANSACTIONS YIELD estimatedUsedHeapMemory AS m, metaData AS md "
                               "WHERE md.kg_writer = $t RETURN m", t=self.token):
                    self.peak = max(self.peak, int(r["m"] or 0))
                self.samples += 1
                time.sleep(0.02)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *exc):
        time.sleep(0.05)
        self.stop.set()
        self.t.join(10)


def unit(label: str, body) -> dict:
    """``body(st)`` as one writer's unit, published; its statements and the peak estimated heap."""
    from store import open_store
    from subject import SUBJECT
    import load_memory
    st = open_store(instance=SUBJECT.id, access="write")
    try:
        with Sampler(st._pub.driver, st._pub.token) as smp:
            t0 = time.monotonic()
            body(st)
            st.commit()
            secs = time.monotonic() - t0
    finally:
        st.close()
    c = load_memory.counts(st)
    row = {"unit": label, "subject": SUBJECT.id, "written": c["written"], "deleted": c["deleted"], "peak_bytes": smp.peak,
           "peak_mib": round(smp.peak / 2**20, 1), "samples": smp.samples, "seconds": round(secs, 1)}
    print(json.dumps(row), flush=True)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--disposable", action="store_true", help="confirm the store may be wiped (required)")
    ap.add_argument("--out", help="write the rows and the fitted line to this JSON file")
    ap.add_argument("--scale", default="1,2,4,8,16,32", help="the synthetic scale-up's copies of the first scenario's kit")
    ap.add_argument("--skip-subject", action="store_true", help="only the synthetic scale-up")
    args = ap.parse_args()
    if not args.disposable:
        print("measure_load_memory: wipes the store; run it only against a disposable one, with --disposable", file=sys.stderr)
        return 2
    if (os.environ.get("KG_STORE") or "neo4j").lower() != "neo4j":
        print("measure_load_memory: transaction memory is a Neo4j measure; KG_STORE must be neo4j", file=sys.stderr)
        return 2
    os.environ["KG_LOAD_MEMORY_CHECK"] = "off"   # measure every unit, whatever the pre-check would say
    import cadence
    os.environ.update(cadence.pin_record({}))
    import gate_cli
    from kitio import kit_for
    from load import load_scenario
    from subject import SUBJECT
    rows = [unit("a first unit, wiping what the store held", lambda st: (st.wipe(), st.apply_constraints()))]
    if not args.skip_subject:
        for sc in SUBJECT.order:
            rows.append(unit(f"{sc} (gate_cli load)", lambda st, sc=sc: gate_cli._load(st, sc)))
        rows.append(unit("every scenario in one unit (run.py --deterministic)",
                         lambda st: [gate_cli._load(st, sc) for sc in SUBJECT.order]))
    first = SUBJECT.order[0]
    kit = kit_for(first)

    def copies(k):
        def body(st):
            st.wipe()
            st.apply_constraints()
            for i in range(k):
                load_scenario(st, first, kit, activity_note=f"{first}: synthetic copy {i + 1} of {k} (task-0176)", version_tag=f"s{i + 1}")
        return body
    for k in [int(x) for x in args.scale.split(",") if x.strip()]:
        rows.append(unit(f"synthetic: {first}'s kit x{k}", copies(k)))
        rows.append(unit(f"synthetic: {first}'s kit x1 after x{k}", copies(1)))
    import load_memory
    fit = load_memory.fit([(r["written"], r["deleted"], r["peak_bytes"]) for r in rows])
    print(json.dumps({"fit": fit}), flush=True)
    if args.out:
        Path(args.out).write_text(json.dumps({"rows": rows, "fit": fit}, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(_outcomes.run(main))
