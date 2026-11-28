"""A result the MCP reader cut says so (task-0365): in ``_meta``, and first in ``content``, since a client hands the
model the content and seldom the ``_meta``.

The reader never truncates to fit its response cap: an answer over ``KG_MCP_MAX_RESPONSE`` is refused whole (task-0177),
and that refusal now names the narrower call too. Two tools return part of what they hold by design:
``register_nodes`` (``limit``, 100 by default, at most 1000) and ``scenario_runs`` (``limit``, per scenario). When one
of them returns less than it holds, its result carries::

    _meta["io.knowgov/clipped"] = {"partial": true, "what": "nodes", "returned": 100, "total": 412,
                                   "narrower": "<the call that reads the rest, or reads less>"}

An over-cap refusal carries the same object with ``what: "bytes"``,
``returned: 0`` and ``total`` its size.

An answer whose text is over ``KG_MCP_CLIENT_BUDGET`` characters (100,000 by default, from 1,000 to 1 GiB; set below the
response limits common MCP clients apply) is not cut either (decision-0048, which keeps task-0177's whole-or-error
rule), but a client may cut it, and an assistant that reads part of it generalises from a sample. It carries::

    _meta["io.knowgov/large"] = {"partial": false, "chars": 210020, "budget": 100000,
                                 "count": {"what": "findings", "n": 3000} | null, "narrower": "..."}

Each mark is also a text item, in words, before the answer, which stays the last text item, unchanged; a client that
parsed ``content[0]`` as the answer takes the last text item, or ``structuredContent``. An answer with no mark (it holds
everything and fits the budget) is byte for byte the result it was before. The fields are pinned by
``harness/schemas/result-meta.schema.json``. Computed from the tool's own structured answer and its text, so the mark is
the same on both transports and on either store. Standard library only.
"""
from __future__ import annotations

META_CLIPPED = "io.knowgov/clipped"

# task-0365: how to ask narrowly, by tool, for an answer refused over the response cap
NARROWER = {
    "gate_verdict": "gate_verdict with summary true (counts only), then with filter (owner, level, kind, key or severity)",
    "evidence_bundle": "evidence_bundle with keys (a narrower key set) or verbatim false",
    "register_nodes": "register_nodes with a limit, or a filter (taxonomy, kind, state, owner, parent)",
    "register_impact": "register_impact without children, or from a node lower in the register",
    "held_keys": "three_valued_answer or gate_verdict on the keys you need",
    "document_statements": "document_statements with version",
    "scenario_runs": "scenario_runs with scenario and a limit",
    "subject_overview": "subject_overview with task, one class's keys, or key_nodes on one key",
}
GENERIC = "a limit, a narrower key set or verbatim false, where the tool takes one"


def mark(what: str, returned: int, total: int, narrower: str) -> dict:
    return {"partial": True, "what": what, "returned": returned, "total": total, "narrower": narrower}


def _nodes(args: dict, data: dict) -> dict | None:
    if not data.get("truncated"):
        return None
    got = len(data.get("nodes") or [])
    nxt = int(data.get("offset") or 0) + got
    return mark("nodes", got, int(data.get("total") or 0),
                f"register_nodes with offset {nxt} for the next page, a limit up to 1000, or a filter "
                "(taxonomy, kind, state, owner, parent) that matches fewer")


def _runs(args: dict, data: dict) -> dict | None:
    rows = data.get("scenarios") or []
    got = sum(len(s.get("runs") or []) for s in rows)
    total = sum(int(s.get("runs_total") or 0) for s in rows)
    if got >= total:
        return None
    cut = [s["scenario"] for s in rows if len(s.get("runs") or []) < int(s.get("runs_total") or 0)]
    return mark("runs", got, total, f"scenario_runs without limit, or with scenario ({', '.join(cut)}) and a larger limit")


CUTS = {"register_nodes": _nodes, "scenario_runs": _runs}


def clipped(name: str, args: dict, data) -> dict | None:
    """The mark for one tool's answer, None when it holds everything (or the tool never cuts)."""
    cut = CUTS.get(name)
    return cut(args or {}, data) if cut and isinstance(data, dict) else None


META_LARGE = "io.knowgov/large"


def _n(v) -> int:
    return v if isinstance(v, int) and not isinstance(v, bool) else len(v) if isinstance(v, (list, dict)) else 0


# task-0365 (decision-0048): what a large answer holds, by tool, so the mark gives its full count
COUNTS = {
    "gate_verdict": lambda d: ("findings", _n(d.get("findings"))) if isinstance(d.get("findings"), list) else None,
    "evidence_bundle": lambda d: ("statements", _n(d.get("assertion_ids"))),
    "held_keys": lambda d: ("keys", _n(d.get("total"))),
    "register_nodes": lambda d: ("nodes", _n(d.get("total"))),
    "register_impact": lambda d: ("keys", _n(d.get("keys"))) if "keys" in d else None,
    "derived_outputs": lambda d: ("outputs", _n(d.get("total"))),
    "document_statements": lambda d: ("statements", _n(d.get("total"))),
    "stale_nodes": lambda d: ("stale nodes", _n(d.get("total"))),
    "scenario_runs": lambda d: ("runs", sum(_n(s.get("runs_total")) for s in d.get("scenarios") or [])),
    "subject_overview": lambda d: ("keys", _n((d.get("counts") or {}).get("keys"))),
}


def large(name: str, data, chars: int, budget: int | None) -> dict | None:
    """The mark on an answer whose text is over ``budget`` characters: nothing is cut (task-0177's whole-or-error rule
    stands), but a client may cut it, so it says how large it is, what it holds and how to ask narrowly."""
    if budget is None or chars <= budget:
        return None
    count = COUNTS.get(name)
    got = count(data) if count and isinstance(data, dict) else None
    return {"partial": False, "chars": chars, "budget": budget,
            "count": {"what": got[0], "n": got[1]} if got else None, "narrower": NARROWER.get(name, GENERIC)}


def marks(name: str, args: dict, data, chars: int, budget: int | None) -> dict:
    """Every mark one answer carries, by its _meta key; empty for an answer that holds everything and fits the budget."""
    out = {}
    c = clipped(name, args, data)
    if c:
        out[META_CLIPPED] = c
    big = large(name, data, chars, budget)
    if big:
        out[META_LARGE] = big
    return out


def notice(key: str, m: dict) -> str:
    """One mark in words, the text item before the answer."""
    if key == META_LARGE:
        held = f" It holds {m['count']['n']} {m['count']['what']}." if m.get("count") else ""
        return (f"large: this answer is {m['chars']} characters, above KG_MCP_CLIENT_BUDGET ({m['budget']}); it is whole, "
                f"but a client may cut it, so do not generalise from part of it.{held} To ask narrowly: {m['narrower']}. "
                "The answer is the last text item, and structuredContent.")
    return words(m)


def words(m: dict) -> str:
    """The mark as the first content item says it."""
    return (f"partial: {m['returned']} of {m['total']} {m['what']} returned; do not generalise from this part. "
            f"To read the rest or less: {m['narrower']}. The answer is the last text item, and structuredContent.")


def refused(name: str, size: int) -> dict:
    """The mark on an answer refused over the response cap: nothing returned, its size, the narrower call."""
    return mark("bytes", 0, size, NARROWER.get(name, GENERIC))


def with_meta(result: dict, extra: dict) -> dict:
    """``result`` with ``extra`` merged into its ``_meta``, never replacing one already there."""
    if not extra:
        return result
    return {**result, "_meta": {**(result.get("_meta") or {}), **extra}}
