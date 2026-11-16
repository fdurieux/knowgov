"""Two deterministic runs of one subject agree in every leaf, list order included (task-0369).

    python tools/check_run_order.py RUN_A RUN_B [--scenarios C,D3]

RUN_A and RUN_B are two ``harness/run.py --deterministic --out`` folders of the same subject, code and store kind.
Each scenario's ``deterministic.json`` is flattened to its leaves (a list item addressed by its position, so an
order that moves is a leaf that moves) and the two compared. ``demo/tools/compare_deterministic.py`` reads lists
without regard to order, so a store read that answers in its own traversal order passes it while the record files
differ run to run; this check does not. Every scenario folder present in RUN_A is compared, or the ``--scenarios``
named; a scenario missing from either run is a failure.

Prints each differing leaf (``<scenario> | <path> | <a> | <b>``), a count per scenario and the sha256 of the ordered
list of differing leaves. Exit 0 when no leaf differs, 1 when one does, 2 when a run folder cannot be read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))


def leaves(obj, path: str = ""):
    """(path, JSON value) for every leaf; an empty list or object is a leaf of its own."""
    if isinstance(obj, dict):
        if not obj:
            yield path, "{}"
        for k, v in obj.items():
            yield from leaves(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        if not obj:
            yield path, "[]"
        for i, v in enumerate(obj):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, json.dumps(obj, sort_keys=True)


def differing(a: dict, b: dict) -> list[tuple[str, str, str]]:
    la, lb = dict(leaves(a)), dict(leaves(b))
    return [(k, la.get(k, "<absent>"), lb.get(k, "<absent>")) for k in sorted(set(la) | set(lb)) if la.get(k) != lb.get(k)]


def _read(folder: Path, scenario: str) -> dict:
    return json.loads((folder / scenario / "deterministic.json").read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_a", type=Path)
    ap.add_argument("run_b", type=Path)
    ap.add_argument("--scenarios", help="comma-separated scenario ids (default: every scenario folder of RUN_A)")
    args = ap.parse_args(argv)
    for d in (args.run_a, args.run_b):
        if not d.is_dir():
            print(f"cannot run: {d} is not a run folder", file=sys.stderr)
            return 2
    scenarios = (args.scenarios.split(",") if args.scenarios
                 else sorted(p.parent.name for p in args.run_a.glob("*/deterministic.json")))
    if not scenarios:
        print(f"cannot run: {args.run_a} holds no <scenario>/deterministic.json", file=sys.stderr)
        return 2
    rows, missing = [], []
    for sc in scenarios:
        try:
            got = differing(_read(args.run_a, sc), _read(args.run_b, sc))
        except FileNotFoundError as e:
            missing.append(f"{sc}: {e.filename} is missing")
            continue
        except (OSError, json.JSONDecodeError) as e:
            print(f"cannot run: {sc}: {e}", file=sys.stderr)
            return 2
        rows += [(sc, *r) for r in got]
        print(f"{sc}: {len(got)} leaf/leaves differ")
    for r in rows:
        print(" | ".join(r))
    for m in missing:
        print("FAIL " + m, file=sys.stderr)
    digest = hashlib.sha256("\n".join(" | ".join(r) for r in rows).encode("utf-8")).hexdigest()
    print(f"run order: {len(rows)} differing leaf/leaves over {len(scenarios)} scenario(s), sha256 {digest}"
          + ("" if not missing else f"; {len(missing)} scenario(s) missing"))
    return 1 if rows or missing else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
