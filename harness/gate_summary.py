"""The gate report read narrowly (task-0364): a summary of counts, and the report with only the findings a filter names.

A large subject's gate report is too big for an assistant to read whole (a 197-key subject's ran to about 156,000
characters), and a summary an assistant writes from part of one can state a count wrongly. The MCP reader's
``gate_verdict`` therefore answers two narrower ways, both computed from the one report ``gate_cli.evaluate``
builds, so neither is a second gate:

- ``summary``: the verdict, why, the bar the task class sets, the report's identity fields as the report holds
  them, and counts: by severity (the report's ``counts``), by finding kind, by key level (every required key, from
  the report's ``levels``) and by owner unit (each finding's ``owner``: its findings, the distinct keys they name
  and their severities). No finding is listed. Schema ``harness/schemas/gate-summary.schema.json``.
- ``filtered``: the report itself, its ``findings`` only those matching every field the filter names (``owner``,
  ``level``, ``kind``, ``key``, ``severity``), and a ``filter`` block naming the filter, how many matched and how
  many the report holds. The verdict, ``exit_code``, ``counts`` and ``levels`` stay the whole report's: a filter
  narrows what is read, never what the gate decided. Schema ``gate-report`` (``filter`` additive).

An owner of null collects the findings no single unit answers for, and those of a kind that names no owner
(``task``, ``suspect_derived``, ``preload``): the same findings a filter of ``owner: null`` returns. Standard library
only; reads nothing but the report and the task class's table.
"""
from __future__ import annotations

SUMMARY_VERSION = 1
FILTERS = ("owner", "level", "kind", "key", "severity")
# decision-0029 (task-0237) and its additions: what the gate decided on, as the report names it
IDENTITY = ("task_profile", "register", "knowgov", "corpus", "attestations", "captures", "configuration", "code", "preload")
SEVERITIES = ("blocker", "critical", "major", "minor", "info")
# the gate's levels, worst first (gate.ORDER; tests/test_gate_summary.py holds them equal): a task class's block levels are a
# set, so they are listed in this order, the same in every process whatever PYTHONHASHSEED
LEVELS = ("absent", "declared_gap", "disputed", "invalidated", "proposed", "validated", "verified", "approved")


def bar(spec: dict) -> dict:
    """The bar the task class sets: the levels that block (in the gate's order, worst first), the share of required keys that may sit below verified (or
    approved, where the class requires it) and whether it does."""
    levels = list(spec.get("block_levels") or [])
    rank = {lv: i for i, lv in enumerate(LEVELS)}
    return {"block_levels": sorted(levels, key=lambda lv: (rank.get(lv, len(LEVELS)), lv)), "max_unverified_share": spec.get("max_unverified_share"),
            "require_approved": spec.get("require_approved") is True}


def _tally(values) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items()))


def by_owner(findings: list[dict]) -> list[dict]:
    """One row per owner the findings name (null last): its findings, the distinct keys they name, by severity."""
    rows: dict = {}
    for f in findings:
        r = rows.setdefault(f.get("owner"), {"owner": f.get("owner"), "findings": 0, "keys": set(),
                                             "by_severity": {s: 0 for s in SEVERITIES}})
        r["findings"] += 1
        r["by_severity"][f["severity"]] += 1
        if f.get("key"):
            r["keys"].add(f["key"])
    order = sorted((o for o in rows if o is not None)) + ([None] if None in rows else [])
    return [{**rows[o], "keys": len(rows[o]["keys"])} for o in order]


def summary(rep: dict, spec: dict) -> dict:
    """The summary of one gate report (``gate_cli.evaluate``'s) under the task class ``spec``: no finding listed."""
    fs = rep.get("findings") or []
    base = rep.get("baseline")
    return {
        "schema_version": SUMMARY_VERSION, "tool": "knowgov gate summary", "report_schema_version": rep["schema_version"],
        **{k: rep.get(k) for k in ("subject", "scenario", "task", "store", "loaded", "version", "verdict", "why",
                                   "threshold", "exit_code", "as_of")},
        "bar": bar(spec),
        **{k: rep.get(k) for k in IDENTITY},
        "keys": rep["keys"],
        "findings": len(fs),
        "counts": {"by_severity": dict(rep["counts"]), "by_kind": _tally(f["kind"] for f in fs),
                   "by_level": _tally((rep.get("levels") or {}).values()), "by_owner": by_owner(fs)},
        "baseline": None if base is None else {
            "source": base["source"], "verdict": base["verdict"], "regression": base["regression"],
            "worse_verdict": base["worse_verdict"], "regressed_keys": len(base.get("regressed_keys") or []),
            "new_suspect": len(base.get("new_suspect") or []), **({"differs": base["differs"]} if "differs" in base else {})},
    }


def matches(f: dict, flt: dict) -> bool:
    """Whether one finding matches every field ``flt`` names; ``owner: None`` matches a finding that names none."""
    return all(f.get(name) == want for name, want in flt.items())


def filtered(rep: dict, flt: dict) -> dict:
    """The report with only the findings ``flt`` matches, and a ``filter`` block; everything else as the report has it."""
    fs = rep.get("findings") or []
    kept = [f for f in fs if matches(f, flt)]
    return {**rep, "findings": kept, "filter": {**{k: flt[k] for k in FILTERS if k in flt}, "matched": len(kept), "total": len(fs)}}
