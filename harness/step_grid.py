"""A step-by-scenario grid over deterministic run folders (task-0192, doc-0024 J3).

    python harness/step_grid.py RUN_DIR [RUN_DIR ...] [--record] [--scope ID ...] [-f text|json] [-o FILE]

Each RUN_DIR is a folder ``harness/run.py --deterministic --out`` wrote (one ``<scenario>/deterministic.json``
per scenario), or one scenario's folder; ``--record`` adds the subject's own record. The rows are the journey
steps of J1's slices (``proposal_impact.evaluate`` with a scope and no overlay, task-0191): the register's own
THREAD walk from each approved step, and the subject's ``register_map.toml`` rows ``register_impact``'s
``landed_rows`` lands on it. The columns are the scenarios the folders hold. Each cell is that step's keys as
the scenario's gate report has them, read from the folder and never recomputed: each key's level from
``gate_keys``, the findings (blocked, below verified, flagged, stale statements, the suspect derived outputs
that used them, lapsed reviews) from ``D6_gate`` restricted to the cell's keys, and for a stage-2 scenario the
findings of its two later gates. A key the report does not hold reads unread. A conflict is counted on its
column, never keyed by its gap id: R-CONFLICT's ids follow store order (doc-0030, its store-order finding). The keys on no step are
listed with their nodes, through ``upward.key_nodes``. Facts only: denominators shown, no score, no rank.

No store is opened, loaded or written, and knowgov-runs is never called: a sweep through ``start_run`` would
replace the scenario every viewer of the page reads (decision-0008). Only the folders, the register and the
subject's files are read. Exit 0 a grid, 2 a folder or scope that cannot be read. Report pinned by
``harness/schemas/step-grid.schema.json``. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SCHEMA_VERSION = 1
TOOL = "knowgov step_grid"
CELL_WHY = {
    "landed": "the step's keys: the register-map rows landed_rows lands on its thread, rows on a withdrawn descendant left out",
    "levels": "count of the step's keys at each level, as the scenario's gate report (gate_keys) has them",
    "unread": "the step's keys the gate report does not hold (no task class of the run required them)",
    "worst": "the lowest level read, by the gate's order; null when none was read. Not a score",
    "unknown": "keys at absent: no statement, the three-valued unknown",
    "gaps": "keys at declared_gap: a documented gap",
    "findings": "the gate report's own findings (D6_gate) on the step's keys, never recomputed",
}


class GridError(ValueError):
    """A folder, a scope or the subject cannot be read: no grid is printed."""


def columns(dirs: list[Path], record: bool, subject) -> list[dict]:
    """One column per scenario folder found, in the order given, then each folder's scenarios in the subject's
    order: the folder's own gate report, never the store's."""
    sources = [(str(d), Path(d)) for d in dirs]
    if record:
        sources.append(("record", Path(subject.record_dir)))
    if not sources:
        raise GridError("give one or more run folders, or --record")
    out = []
    for label, d in sources:
        if not d.is_dir():
            raise GridError(f"{label}: not a folder")
        found = [(d.name, d / "deterministic.json")] if (d / "deterministic.json").is_file() else \
            [(sc, d / sc / "deterministic.json") for sc in subject.order if (d / sc / "deterministic.json").is_file()]
        if not found:
            raise GridError(f"{label}: no deterministic.json, neither here nor under a scenario of {subject.id} ({subject.order})")
        for sc, f in found:
            if sc not in subject.scenarios:
                raise GridError(f"{f}: {sc} is not a scenario of {subject.id}")
            try:
                det = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                raise GridError(f"{f}: {e}") from e
            if not isinstance(det.get("D6_gate"), dict) or not isinstance(det.get("gate_keys"), dict):
                raise GridError(f"{f}: no D6_gate and gate_keys: not a deterministic run's report")
            out.append({"id": f"{label}:{sc}", "scenario": sc, "source": label, "as_of": det.get("as_of") or subject.record_as_of,
                        "as_of_from_run": bool(det.get("as_of")), "det": det})
    return out


def _findings(gate: dict, keys: set[str]) -> dict:
    stale = [x for x in gate.get("stale") or [] if x.get("key") in keys]
    ids = {x["id"] for x in stale}
    return {"blocked": sorted(k for k in gate.get("blocked_keys") or [] if k in keys),
            "below_verified": sorted(k for k in gate.get("below_verified") or [] if k in keys),
            "flagged": sorted(k for k in gate.get("flagged") or [] if k in keys),
            "stale": sorted(ids),
            "suspect_derived": sorted(x["id"] for x in gate.get("suspect_derived") or [] if set(x.get("used_invalidated") or []) & ids),
            "lapsed": sorted({x["key"] for x in gate.get("lapsed") or [] if x.get("key") in keys})}


def cell(step: dict, col: dict) -> dict:
    """One step under one scenario: its keys' levels and findings as the folder's gate report holds them."""
    from gate import ORDER
    det = col["det"]
    keys = set(step["keys"])
    gk = det["gate_keys"]
    levels = {}
    for k in keys:
        if k in gk:
            levels[gk[k]["level"]] = levels.get(gk[k]["level"], 0) + 1
    known = [lv for lv in levels if lv in ORDER]
    out = {"step": step["id"], "column": col["id"], "landed": len(keys),
           "levels": dict(sorted(levels.items(), key=lambda kv: ORDER.index(kv[0]) if kv[0] in ORDER else len(ORDER))),
           "unread": sorted(k for k in keys if k not in gk),
           "worst": min(known, key=ORDER.index) if known else None,
           "unknown": sorted(k for k in keys if (gk.get(k) or {}).get("level") == "absent"),
           "gaps": sorted(k for k in keys if (gk.get(k) or {}).get("level") == "declared_gap"),
           "flags": {k: sorted(gk[k].get("flags") or []) for k in sorted(keys) if gk.get(k, {}).get("flags")},
           "findings": _findings(det["D6_gate"], keys), "stage2": None}
    st2 = det.get("stage2")
    if isinstance(st2, dict):
        out["stage2"] = {g: _findings(st2[g], keys) for g in ("gate_before_reverification", "gate_after_reverification")
                         if isinstance(st2.get(g), dict)}
    return out


def steps(scopes: list[str] | None, register_map: dict, today) -> tuple[list[str], list[dict]]:
    """J1's slices for each scope (task-0191), each step once with the journeys and products it is a slice
    of; with no scope, every approved journey (kind journey) on which a step lands one of the map's keys."""
    import proposal_impact as pi
    import register_impact as ri
    root = ri.register_root().resolve()
    reg = ri.load_tools(root)["register"].load_register(root)
    auto = scopes is None
    if auto:
        scopes = sorted(n for n, x in reg["nodes"].items() if x.get("kind") == "journey" and x.get("state") == "approved")
    by: dict[str, dict] = {}
    used = []
    for scope in scopes:
        try:
            r = pi.evaluate(None, today=today, scope=scope, register_map=register_map)
        except pi.ProposalError as e:
            raise GridError(str(e)) from e
        got = [s for s in r["slices"]["map"] if not auto or s["keys"]["landed"]]
        if auto and not got:
            continue
        used.append(scope)
        for s in got:
            sid = s["start"]["id"]
            ent = by.setdefault(sid, {"id": sid, "name": s["start"]["name"], "kind": s["start"]["kind"], "axis": s["axis"],
                                      "scopes": [], "products": [], "of": s["keys"]["of"],
                                      "keys": sorted({x["key"] for x in s["keys"]["rows"] if not x.get("withdrawn")}),
                                      "behind_withdrawn": sorted({k for b in s["keys"]["behind_withdrawn"] for k in b["only_behind"]})})
            ent["scopes"].append(scope)
            ent["products"] = sorted(set(ent["products"]) | set(s["products"]))
    return used, list(by.values())


def grid(dirs: list[Path], record: bool = False, scopes: list[str] | None = None) -> dict:
    import cadence
    import register_impact as ri
    import upward
    from subject import SUBJECT
    cols = columns(dirs, record, SUBJECT)
    rmap = SUBJECT.register_map()
    today = cadence.as_of(cols[0]["as_of"])   # the register's slices read no date but an exception's: the first column's
    used, rows = steps(scopes, rmap, today)
    every = sorted({r["key"] for r in rmap.get("row", [])})
    on = {k for s in rows for k in s["keys"]}
    off = []
    for k in every:
        if k not in on:
            got = upward.key_nodes(k)
            off.append({"key": k, "nodes": sorted({n["id"] for r in got["rows"] for n in r["nodes"]})})
    return {
        "schema_version": SCHEMA_VERSION, "tool": TOOL, "subject": SUBJECT.id, "register": ri.source(ri.register_root().resolve()),
        "store": None, "stored": False, "scopes": used, "denominator": len(every),
        "steps": rows,
        "columns": [{"id": c["id"], "scenario": c["scenario"], "source": c["source"], "as_of": c["as_of"],
                     "as_of_from_run": c["as_of_from_run"], "task": c["det"]["D6_gate"].get("task"),
                     "verdict": c["det"]["D6_gate"].get("verdict"), "why": c["det"]["D6_gate"].get("why"),
                     "conflicts": len(c["det"]["D6_gate"].get("conflicts") or []),
                     "stage2": isinstance(c["det"].get("stage2"), dict)} for c in cols],
        "cells": [cell(s, c) for s in rows for c in cols],
        "off_steps": off,
        "why": dict(CELL_WHY, off_steps="the map's keys no step's thread lands, each with the nodes key_nodes names",
                    conflicts="the gate report's conflicts, counted on the column: never keyed by gap id, whose order is the store's (doc-0030, its store-order finding)",
                    store="never opened: the folders' own gate reports are read; knowgov-runs is never called (decision-0008)"),
    }


def render_text(g: dict) -> str:
    cols = g["columns"]
    by = {(c["step"], c["column"]): c for c in g["cells"]}
    lines = [f"{g['subject']}: {len(g['steps'])} step(s) of {', '.join(g['scopes']) or 'no journey'} by {len(cols)} scenario(s), "
             f"register {g['register']['tag'] or '?'}; {g['denominator']} key(s) in the map; read from the folders, no store",
             "  " + " | ".join([f"{'step':<9}{'keys':>5}"] + [f"{c['id'].split(':')[-1]} {c['verdict'] or '-'}" for c in cols])]
    for s in g["steps"]:
        row = [f"{s['id']:<9}{len(s['keys']):>5}"]
        for c in cols:
            x = by[(s["id"], c["id"])]
            f = x["findings"]
            row.append(f"{(x['worst'] or '-')[:10]} b{len(f['blocked'])} s{len(f['stale'])} l{len(f['lapsed'])} u{len(x['unread'])}")
        lines.append("  " + " | ".join(row))
    lines.append("  b blocked, s stale statements, l lapsed, u unread; worst is the lowest level read, never a score")
    lines.append(f"  on no step: {len(g['off_steps'])} of {g['denominator']} key(s)"
                 + (f": {', '.join(o['key'] for o in g['off_steps'][:6])}{' ...' if len(g['off_steps']) > 6 else ''}" if g["off_steps"] else ""))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="step_grid.py", description="A step-by-scenario grid over deterministic run folders "
                                 "(task-0192). Reads files only: no store, no knowgov-runs.")
    ap.add_argument("dirs", type=Path, nargs="*", help="run.py --deterministic --out folders, or scenario folders")
    ap.add_argument("--record", action="store_true", help="add the subject's own record as a source")
    ap.add_argument("--scope", action="append", default=None, help="a journey, step or product id (repeatable; default: every "
                                                                   "approved journey a step of which lands a key of the subject's map)")
    ap.add_argument("-f", "--format", choices=("text", "json"), default="text")
    ap.add_argument("-o", "--output", type=Path, default=None)
    a = ap.parse_args(argv)
    try:
        g = grid(a.dirs, record=a.record, scopes=a.scope)
    except (GridError, ValueError) as e:
        print(f"step_grid: {e}", file=sys.stderr)
        return 2
    text = json.dumps(g, indent=1, ensure_ascii=False, default=str) + "\n" if a.format == "json" else render_text(g)
    if a.output:
        a.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
