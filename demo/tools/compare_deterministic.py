"""Compare a deterministic run against the published record, field by field.

    python compare_deterministic.py <run_dir> [<record_dir>] [--scenarios <id> ...]

For every scenario present in <run_dir>, loads ``<S>/deterministic.json``
from both trees and reports every leaf that differs, ignoring what cannot
be equal across two executions: wall-clock timestamps (``at``,
``ingested_at``, ``invalidated_at``), the SHACL report's text sample
(blank-node labels are fresh per run; its counts are compared), and the
running number R-CONFLICT appends to a conflict gap's id, which follows
the store's return order (the set of gaps, text included, is compared).
Lists of scalars are compared as sets (Cypher's collect() answers in
store order). A difference the subject records as the record's own
(``known_differences`` in its scenarios) is dropped on both sides and
reported by its reason, never counted. D1, the constraint measurement of a Neo4j edition, is
compared only between runs of the same store kind: a run on another
adapter records its store and the comparator says D1 was skipped.
Everything else — counts, rule hits, census, verdicts, the invalidation
set, the gate's keys — must match. Exit 0 iff nothing differs; the diff
is printed either way, one line per leaf.

A scenario whose subject names a ``deterministic_record`` (the record's own
deterministic-mode run) is compared against that by default: the scored
record's stage 2 may register an earlier governed output as a ``Derived``
node that ``--deterministic`` does not create. Pass ``--record-for <scenario>=<dir>``
to compare against another folder.

Standard library only, so the CI job and a laptop can run it with no
install. The record is the subject's vendored one by default.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "harness"))
from subject import SUBJECT  # noqa: E402  (the subject root: KG_SUBJECT, default subjects/cargo_quote)

RECORD = SUBJECT.record_dir     # the subject's vendored record
SCENARIOS = SUBJECT.order
# a scenario whose record also holds a deterministic-mode run is compared against that by default
DETERMINISTIC_RECORDS = {sc: s["deterministic_record"] for sc, s in SUBJECT.scenarios.items() if s.get("deterministic_record")}
VOLATILE_KEYS = {"at", "ingested_at", "invalidated_at", "sample", "store"}
# the Neo4j edition's constraint measurement: compared only between runs of the same store kind
STORE_SPECIFIC = {"D1_constraints"}
# differences the subject records as the record's own (scenarios.toml, [[scenario.known_differences]]):
# against the named record folders one field under one leaf prefix is dropped on both sides
KNOWN = {sc: list(s.get("known_differences", [])) for sc, s in SUBJECT.scenarios.items() if s.get("known_differences")}


def _drop_field(obj, prefix: str, field: str) -> None:
    """Remove ``field`` from every dict under the dotted ``prefix`` (keys only; lists are walked)."""
    node = obj
    for part in prefix.split("."):
        if not isinstance(node, dict) or part not in node:
            return
        node = node[part]

    def walk(x):
        if isinstance(x, dict):
            x.pop(field, None)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(node)


def _leaves(obj, prefix: str = "") -> dict[str, object]:
    out: dict[str, object] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in VOLATILE_KEYS:
                continue
            out.update(_leaves(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        # lists of dicts are compared as sets of their canonical forms when
        # order is not meaningful (rule hits come back in store order)
        if obj and all(isinstance(x, dict) for x in obj):
            canon = sorted(json.dumps(_strip(x), sort_keys=True) for x in obj)
            for i, c in enumerate(canon):
                out[f"{prefix}[{i}]"] = c
        elif obj and all(isinstance(x, (str, int, float, bool)) or x is None for x in obj):
            # lists of scalars are unordered: Cypher's collect() answers in store order, and another
            # adapter's store order differs; nothing the harness computes depends on that order
            for i, x in enumerate(sorted(obj, key=lambda v: json.dumps(v))):
                out[f"{prefix}[{i}]"] = x
        else:
            for i, x in enumerate(obj):
                out.update(_leaves(x, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


CONFLICT_ID = re.compile(r"^(gap:conflict:.+):\d+$")


def _strip(obj):
    if isinstance(obj, dict):
        out = {k: _strip(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
        if isinstance(out.get("id"), str):
            out["id"] = CONFLICT_ID.sub(r"\1:n", out["id"])
        return out
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            return sorted((_strip(x) for x in obj), key=lambda d: json.dumps(d, sort_keys=True))
        return [_strip(x) for x in obj]
    return obj


def compare(run_dir: Path, record_dir: Path, scenarios: list[str], record_for: dict[str, Path] | None = None,
            known: dict[str, list[dict]] | None = None) -> tuple[int, list[str]]:
    """``record_for`` names the record folder to read for a scenario instead of ``<record_dir>/<scenario>``.
    ``known`` (default the subject's) names, per scenario, the record folders against which one
    field under one prefix is a recorded difference: it is dropped on both sides and reported as
    ``known: <why>`` instead of counted."""
    known = KNOWN if known is None else known
    lines: list[str] = []
    n_diff = 0
    for sc in scenarios:
        rec = (record_for or {}).get(sc) or record_dir / sc
        a, b = run_dir / sc / "deterministic.json", rec / "deterministic.json"
        if not a.exists():
            continue
        if not b.exists():
            lines.append(f"{sc}: no record at {b}")
            n_diff += 1
            continue
        ja, jb = json.loads(a.read_text(encoding="utf-8")), json.loads(b.read_text(encoding="utf-8"))
        store_a, store_b = ja.get("store", "neo4j"), jb.get("store", "neo4j")
        note = ""
        if store_a != store_b:
            for k in STORE_SPECIFIC:
                ja.pop(k, None); jb.pop(k, None)
            note = f" ({', '.join(sorted(STORE_SPECIFIC))} skipped: the run's store is {store_a}, the record's {store_b})"
        applied = []
        try:
            rel = rec.resolve().relative_to(record_dir.resolve()).as_posix()
        except ValueError:
            rel = ""
        for kd in known.get(sc, []):
            if rel in kd.get("records", []):
                _drop_field(ja, kd["prefix"], kd["field"])
                _drop_field(jb, kd["prefix"], kd["field"])
                applied.append(kd["why"])
        la = _leaves(ja)
        lb = _leaves(jb)
        diffs = []
        for k in sorted(set(la) | set(lb)):
            if la.get(k, "<missing>") != lb.get(k, "<missing>"):
                diffs.append(f"  {k}: run={la.get(k, '<missing>')!r} record={lb.get(k, '<missing>')!r}")
        n_diff += len(diffs)
        lines.append(f"{sc} against {b.parent.relative_to(record_dir.parent) if record_dir.parent in b.parents else b.parent}: "
                     f"{len(la)} leaves compared, {len(diffs)} differ" + ("" if diffs else " — identical") + note)
        lines.extend(diffs)
        lines.extend(f"known: {why}" for why in applied)
    return n_diff, lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("record_dir", type=Path, nargs="?", default=RECORD)
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--record-for", action="append", default=[], metavar="SCENARIO=DIR",
                    help="read this scenario's record from DIR (default for " + ", ".join(f"{k}: <record_dir>/{v}" for k, v in DETERMINISTIC_RECORDS.items()) + ")")
    args = ap.parse_args()
    record_for = {sc: args.record_dir / rel for sc, rel in DETERMINISTIC_RECORDS.items()}
    for item in args.record_for:
        sc, _, d = item.partition("=")
        record_for[sc] = Path(d)
    n, lines = compare(args.run_dir, args.record_dir, args.scenarios, record_for=record_for)
    print("\n".join(lines))
    compared = [ln for ln in lines if "leaves compared" in ln]
    if not compared:
        print(f"\nNOTHING COMPARED: no <scenario>/deterministic.json under {args.run_dir} for {' '.join(args.scenarios)}")
        return 1
    print(f"\n{'OK' if n == 0 else 'DIFF'}: {n} differing leaf/leaves over {len(compared)} scenario(s) against {args.record_dir}")
    return 0 if n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
