"""What a subject rests on and who owns its keys (task-0366): the MCP reader's ``subject_overview``, from files.

    python harness/subject_overview.py [--task NAME]

A subject reaches the register only through its ``register_map.toml``: each row names a key, the register nodes the key
rests on and, optionally, the one of their owners who answers for it. No other link from a subject to an application, a
capability or a process is stated anywhere, so this tool states that one and no other (an assistant asked over MCP for a
private subject's links guessed one from names; the incident this tool exists for). It reports:

- ``keys``: every key the map's rows name or a task class requires, each with the nodes its rows name, the unit that
  answers for it (``capture.routing``, the one rule the gate's findings, the questionnaires and a register change read,
  so a gate finding on the key names the same ``owner``) and the task classes that require it;
- ``nodes``: each register node a row names, by kind then id, with its taxonomy, name, state and owner as the
  register's own loader reads them (``register_impact.load_tools``, as ``key_nodes`` does) and how many keys rest on it;
  a node the register lacks is listed ``missing``;
- ``owners``: each unit with the keys it answers for, and a null row for the keys no single unit answers for, split into
  those no row assigns (``no_unit``) and those several units answer for (``several_units``);
- ``held``: the scenario the shared store holds for this subject, or null with why (passed in by the reader; this module
  opens no store).

``task`` narrows the keys to one class's. Counts are computed from those lists, so each equals what the files hold.
Schema ``harness/schemas/subject-overview.schema.json``. Standard library and the register's own loader only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import register_impact as ri  # noqa: E402

SCHEMA_VERSION = 1
NOTE = ("a subject reaches the register only through its register_map.toml rows; these are every node and owner they name, "
        "and no other link from the subject is stated")


class OverviewError(ValueError):
    """The question cannot be answered: a task class the subject does not declare."""


def _node(reg: dict, nid: str, keys: int) -> dict:
    n = reg["nodes"].get(nid)
    if n is None:
        return {"id": nid, "taxonomy": None, "kind": None, "name": None, "state": None, "owner": None, "keys": keys, "missing": True}
    return {"id": nid, "taxonomy": n.get("_taxonomy"), "kind": n.get("kind"), "name": n.get("name", ""),
            "state": n.get("state", ""), "owner": n.get("owner"), "keys": keys}


def _rows(rmap: dict) -> dict[str, list[str]]:
    """key -> the nodes its rows name, in row order, each once."""
    rows: dict[str, list[str]] = {}
    for r in rmap.get("row", []):
        got = rows.setdefault(r["key"], [])
        got += [n for n in r.get("nodes") or [] if n not in got]
    return rows


def _keys(universe, rows: dict, route: dict, required: dict) -> list[dict]:
    """Each key with its nodes, its answering unit and units (``capture.routing``) and the classes requiring it."""
    out = []
    for k in sorted(dict.fromkeys(universe)):
        rt = route.get(k) or {"units": [], "unit": None}
        out.append({"key": k, "mapped": k in rows, "nodes": sorted(rows.get(k, [])), "owner": rt["unit"],
                    "units": list(rt["units"]), "tasks": sorted(t for t, ks in required.items() if k in ks)})
    return out


def _tally(values) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items()))


def _owners(keys: list[dict], reg: dict) -> list[dict]:
    """One row per answering unit with its key count, then the null row: no unit, or several."""
    rows = [{"unit": u, "name": (reg["nodes"].get(u) or {}).get("name", ""), "keys": c}
            for u, c in _tally(k["owner"] for k in keys if k["owner"]).items()]
    unowned = [k for k in keys if not k["owner"]]
    if unowned:
        rows.append({"unit": None, "name": None, "keys": len(unowned),
                     "no_unit": sum(1 for k in unowned if not k["units"]), "several_units": sum(1 for k in unowned if k["units"])})
    return rows


def report(task: str | None = None, held: dict | None = None, root: Path | None = None) -> dict:
    """The overview of the loaded subject (``KG_SUBJECT``), all its keys or those of ``task``. ``held``: {scenario, why}."""
    import capture
    from subject import SUBJECT
    from tasks import TASKS
    if task is not None and task not in TASKS:
        raise OverviewError(f"{SUBJECT.id}: no task {task!r}; the subject declares {sorted(TASKS) or 'none'}")
    root = (root or ri.register_root()).resolve()
    reg = ri.load_tools(root)["register"].load_register(root)
    rmap = SUBJECT.register_map()
    rows = _rows(rmap)
    required = {t: list(spec["keys"]) for t, spec in TASKS.items()}
    universe = required[task] if task else set(rows) | {k for ks in required.values() for k in ks}
    keys = _keys(universe, rows, capture.routing(rmap, capture.register_nodes(root)), required)   # the gate's owner rule
    per_node = _tally(n for k in keys for n in k["nodes"])
    nodes = sorted((_node(reg, n, c) for n, c in per_node.items()), key=lambda x: (x["kind"] or "", x["id"]))
    return {"schema_version": SCHEMA_VERSION, "tool": "subject_overview", "subject": SUBJECT.id, "task": task,
            "register": ri.source(root), "register_map": SUBJECT.register.get("map"),
            "held": held or {"scenario": None, "why": "no store was asked"},
            "counts": {"keys": len(keys), "mapped": sum(1 for k in keys if k["mapped"]), "unmapped": sum(1 for k in keys if not k["mapped"]),
                       "nodes": len(nodes), "nodes_by_kind": _tally(n["kind"] or "missing" for n in nodes), "rows": len(rmap.get("row", []))},
            "owners": _owners(keys, reg), "nodes": nodes, "keys": keys, "note": NOTE}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="subject_overview.py", description=__doc__.splitlines()[0])
    ap.add_argument("--task", help="one task class's keys (default: every key the map or a class names)")
    args = ap.parse_args(argv)
    try:
        print(json.dumps(report(args.task), indent=1, ensure_ascii=False, default=str))
    except OverviewError as e:
        print(f"subject_overview: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    import cli_exit
    sys.exit(cli_exit.run(main, "subject_overview", register=True))
