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
store order). D1, the constraint measurement of a Neo4j edition, is
compared only between runs of the same store kind: a run on another
adapter records its store and the comparator says D1 was skipped.
Everything else — counts, rule hits, census, verdicts, the invalidation
set, the gate's keys — must match. Exit 0 iff nothing differs; the diff
is printed either way, one line per leaf.

A run records the date it read review currency on (``as_of``, decision-0005); the record, made
before the date was recorded, has none. The comparator holds the run's date to the subject's
pinned record date (``subject.toml`` ``[record] as_of``): a run read as of another date is one
differing leaf, since a lapsed review would move the gate; it is not a leaf otherwise, and a run
that names no date (one made before the date was recorded) is not held to it.

A scenario whose subject names a ``deterministic_record`` (the record's own
deterministic-mode run) is compared against that by default: the scored
record's stage 2 may register an earlier governed output as a ``Derived``
node that ``--deterministic`` does not create. Pass ``--record-for <scenario>=<dir>``
to compare against another folder.

Standard library only, so the CI job and a laptop can run it with no
install. The record is the subject's vendored one by default.

``compare()`` takes ``ignore_keys``, leaf names set aside for that one
comparison as the volatile keys are. The command line passes none: the
page passes a scenario's ``scored_record_volatile`` (its subject manifest)
when it reads a derived-registering run against the scored record, a leaf
that record wrote with a harness defect fixed afterwards and that its
deterministic-mode re-establishment, which has no Derived node, corrected.
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
PINNED = SUBJECT.record_as_of   # the date the record is read as of (decision-0005); None: not pinned
SCENARIOS = SUBJECT.order
# a scenario whose record also holds a deterministic-mode run is compared against that by default
DETERMINISTIC_RECORDS = {sc: s["deterministic_record"] for sc, s in SUBJECT.scenarios.items() if s.get("deterministic_record")}
VOLATILE_KEYS = {"at", "ingested_at", "invalidated_at", "sample", "store"}
# the Neo4j edition's constraint measurement: compared only between runs of the same store kind
STORE_SPECIFIC = {"D1_constraints"}


def _leaves(obj, prefix: str = "", ignore: frozenset = frozenset(VOLATILE_KEYS)) -> dict[str, object]:
    out: dict[str, object] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ignore:
                continue
            out.update(_leaves(v, f"{prefix}.{k}" if prefix else str(k), ignore))
    elif isinstance(obj, list):
        # lists of dicts are compared as sets of their canonical forms when
        # order is not meaningful (rule hits come back in store order)
        if obj and all(isinstance(x, dict) for x in obj):
            canon = sorted(json.dumps(_strip(x, ignore), sort_keys=True) for x in obj)
            for i, c in enumerate(canon):
                out[f"{prefix}[{i}]"] = c
        elif obj and all(isinstance(x, (str, int, float, bool)) or x is None for x in obj):
            # lists of scalars are unordered: Cypher's collect() answers in store order, and another
            # adapter's store order differs; nothing the harness computes depends on that order
            for i, x in enumerate(sorted(obj, key=lambda v: json.dumps(v))):
                out[f"{prefix}[{i}]"] = x
        else:
            for i, x in enumerate(obj):
                out.update(_leaves(x, f"{prefix}[{i}]", ignore))
    else:
        out[prefix] = obj
    return out


CONFLICT_ID = re.compile(r"^(gap:conflict:.+):\d+$")


def _strip(obj, ignore: frozenset = frozenset(VOLATILE_KEYS)):
    if isinstance(obj, dict):
        out = {k: _strip(v, ignore) for k, v in obj.items() if k not in ignore}
        if isinstance(out.get("id"), str):
            out["id"] = CONFLICT_ID.sub(r"\1:n", out["id"])
        return out
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj):
            return sorted((_strip(x, ignore) for x in obj), key=lambda d: json.dumps(d, sort_keys=True))
        return [_strip(x, ignore) for x in obj]
    return obj


def compare(run_dir: Path, record_dir: Path, scenarios: list[str], record_for: dict[str, Path] | None = None,
            ignore_keys=()) -> tuple[int, list[str]]:
    """``record_for`` names the record folder to read for a scenario instead of ``<record_dir>/<scenario>``;
    ``ignore_keys`` are leaf names set aside for this comparison as ``VOLATILE_KEYS`` are (the command
    line passes none)."""
    ignore = frozenset(VOLATILE_KEYS) | frozenset(ignore_keys)
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
        run_on, rec_on = ja.pop("as_of", None), jb.pop("as_of", None)
        diffs = []
        want = rec_on or PINNED
        if want and run_on is not None and run_on != want:   # a run that names no date predates decision-0005
            diffs.append(f"  as_of: run={run_on!r} record={want!r} (the record is read as of its pinned date; decision-0005)")
        la = _leaves(ja, ignore=ignore)
        lb = _leaves(jb, ignore=ignore)
        for k in sorted(set(la) | set(lb)):
            if la.get(k, "<missing>") != lb.get(k, "<missing>"):
                diffs.append(f"  {k}: run={la.get(k, '<missing>')!r} record={lb.get(k, '<missing>')!r}")
        n_diff += len(diffs)
        lines.append(f"{sc} against {b.parent.relative_to(record_dir.parent) if record_dir.parent in b.parents else b.parent}: "
                     f"{len(la)} leaves compared, {len(diffs)} differ" + ("" if diffs else " — identical") + note)
        lines.extend(diffs)
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
