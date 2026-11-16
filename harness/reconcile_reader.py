"""Which register nodes a system of record no longer carries, and who owns each (task-0342, decision-0041 C5-1).

    python harness/reconcile_reader.py [--system NAME] [--owner ORG-x]

The reader of ``RECONCILE.json``. Each export a connector lands (with the register's own ``tools/reconcile.py``)
sits in ``<register>/exports/<system>/<date>/`` with a ``MANIFEST.toml`` and a
``RECONCILE.json`` naming the stale nodes: the register nodes whose id the export no longer carries. A stale node
stays stale in each later landing until its id returns (task-0313), so the newest dated folder of a system holds
its current stale nodes; the reader takes that folder for each system under ``exports/``, and lists every stale
node with its owning unit as ``register_impact`` names it (the node's ``owner`` field, the unit's name and the
approved ``owns`` links to it), the previous folder it was carried from and the system's own id for it, where the
landing recorded one. A node the register no longer holds is listed, ``in_register`` false, with no owner. Beside
them, as the landing recorded them: the carried register ids the register does not hold (``unknown_ids``) and how
many of the export's objects no node carries (``unregistered``). ``by_owner`` groups the listed stale nodes by
unit, the questionnaire's addressee.

The register is the one every reader reads (``KG_REGISTER``, as ``register_impact`` and ``register_nodes``); the
files only, never the store, and nothing is written. A stale node is a finding, never a deletion. Exit 0 with the
report, 2 when it cannot run (an unreadable register, an unknown system or unit, a RECONCILE.json that is not
JSON). Standard library only. Report pinned by ``harness/schemas/stale-nodes.schema.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import dates  # noqa: E402  (one strict YYYY-MM-DD rule)
import register_impact as ri  # noqa: E402

SCHEMA_VERSION = 1
TOOL = "stale_nodes"
ARGS = ("system", "owner")


class ReconcileError(ValueError):
    """The question cannot be answered: an unknown system or unit, a RECONCILE.json that cannot be read."""


def _systems(root: Path) -> list[str]:
    """The systems the register's ``exports/`` holds a folder for, by name (a dot-folder never)."""
    base = root / "exports"
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")) if base.is_dir() else []


def _newest(root: Path, system: str) -> Path | None:
    """The system's newest dated folder, or None when it has landed none."""
    base = root / "exports" / system
    days = sorted(p.name for p in base.iterdir() if p.is_dir() and dates.is_date(p.name))
    return base / days[-1] if days else None


def _read(folder: Path, root: Path) -> tuple[dict | None, dict]:
    """(RECONCILE.json, MANIFEST.toml) of a landing; the first None when the reconcile has not been run there."""
    rel = folder.relative_to(root).as_posix()
    try:
        man = tomllib.loads((folder / "MANIFEST.toml").read_text(encoding="utf-8"))
    except FileNotFoundError:
        man = {}
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        raise ReconcileError(f"{rel}/MANIFEST.toml cannot be read: {e}") from None
    p = folder / "RECONCILE.json"
    if not p.is_file():
        return None, man
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        raise ReconcileError(f"{rel}/RECONCILE.json cannot be read: {e}") from None
    if not isinstance(rec, dict) or not isinstance(rec.get("stale_nodes", []), list):
        raise ReconcileError(f"{rel}/RECONCILE.json is not a reconcile record: no stale_nodes list")
    return rec, man


def _stale(reg: dict, entry, id_field: str | None) -> dict:
    """One stale node as the landing recorded it, with its node and owning unit from the register."""
    nid = entry.get("id") if isinstance(entry, dict) else None
    if not isinstance(nid, str):
        raise ReconcileError(f"a stale_nodes entry without an id: {entry!r}")
    n = reg["nodes"].get(nid)
    sid = entry.get(id_field) if id_field else None
    out = {"id": nid, "in_register": n is not None, "previous": entry.get("previous") or None,
           "source_id": str(sid) if sid is not None else None}
    if n is None:
        return {**out, "taxonomy": None, "kind": None, "name": None, "state": None, "owning_unit": None}
    return {**out, "taxonomy": n.get("_taxonomy"), "kind": n.get("kind"), "name": n.get("name", ""),
            "state": n.get("state", ""), "owning_unit": ri.owning_unit(reg, nid)}


def _owned_by(x: dict, unit: str) -> bool:
    own = x["owning_unit"]
    return bool(own) and (own["unit"] == unit or unit in own["owns"])


def _check(reg: dict, systems: list[str], args: dict) -> dict:
    extra = sorted(set(args) - set(ARGS))
    if extra:
        raise ReconcileError(f"unknown argument(s) {extra}; {TOOL} takes {list(ARGS)}")
    got = {k: args[k] for k in ARGS if args.get(k) is not None}
    if "system" in got and got["system"] not in systems:
        raise ReconcileError(f"system {got['system']!r}: the register's exports/ holds {systems or 'no system'}")
    if "owner" in got:
        unit = got["owner"]
        if not isinstance(unit, str) or unit not in reg["nodes"] or reg["nodes"][unit].get("_taxonomy") != "organisation":
            units = sorted(nid for nid, n in reg["nodes"].items() if n.get("_taxonomy") == "organisation")
            raise ReconcileError(f"owner {unit!r}: a unit of the register's organisation, one of {units}")
    return got


def _system(reg: dict, root: Path, name: str, owner: str | None) -> dict:
    folder = _newest(root, name)
    if folder is None:
        return {"system": name, "folder": None, "exported_on": None, "previous": None, "reconciled": False,
                "stale_nodes": [], "unknown_ids": [], "unregistered": 0, "why": "no export landed"}
    rec, man = _read(folder, root)
    head = {"system": name, "folder": folder.relative_to(root).as_posix(),
            "exported_on": str(man["exported_on"]) if man.get("exported_on") is not None else None,
            "previous": man.get("previous") or None}
    if rec is None:
        return {**head, "reconciled": False, "stale_nodes": [], "unknown_ids": [], "unregistered": 0,
                "why": "no RECONCILE.json: the register's tools/reconcile.py has not been run on this landing"}
    id_field = (reg.get("sources") or {}).get("system", {}).get(rec.get("source") or name, {}).get("id_field")
    stale = sorted((_stale(reg, e, id_field) for e in rec.get("stale_nodes") or []), key=lambda x: x["id"])
    if owner is not None:
        stale = [x for x in stale if _owned_by(x, owner)]
    unknown = rec.get("unknown_ids") or []
    return {**head, "reconciled": True, "stale_nodes": stale,
            "unknown_ids": sorted(str(x) for x in unknown) if isinstance(unknown, list) else [],
            "unregistered": len(rec.get("unregistered") or [])}


def _by_owner(reg: dict, systems: list[dict]) -> list[dict]:
    """The listed stale nodes by owning unit (the node's owner field; none: null), each id once, by unit then id."""
    units: dict[str | None, set[str]] = {}
    for s in systems:
        for x in s["stale_nodes"]:
            unit = (x["owning_unit"] or {}).get("unit") or None
            units.setdefault(unit, set()).add(x["id"])
    return [{"unit": u, "name": (reg["nodes"].get(u) or {}).get("name", "") if u else None, "stale": sorted(ids)}
            for u, ids in sorted(units.items(), key=lambda kv: (kv[0] is None, kv[0] or ""))]


def report(args: dict | None = None, root: Path | None = None) -> dict:
    """Every system's newest landing with its stale nodes and their owners, under the filters. Raises
    ReconcileError on an unknown system or unit and on a landing it cannot read."""
    args = dict(args or {})
    root = (root or ri.register_root()).resolve()
    reg = ri.load_tools(root)["register"].load_register(root)
    names = _systems(root)
    got = _check(reg, names, args)
    systems = [_system(reg, root, n, got.get("owner")) for n in names if got.get("system", n) == n]
    return {"schema_version": SCHEMA_VERSION, "tool": TOOL, "register": ri.source(root), "filters": got,
            "total": len({x["id"] for s in systems for x in s["stale_nodes"]}), "systems": systems,
            "by_owner": _by_owner(reg, systems)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reconcile_reader.py", description=__doc__.splitlines()[0])
    ap.add_argument("--system", help="one system under the register's exports/ (default: every one)")
    ap.add_argument("--owner", help="one unit of the register's organisation: only the stale nodes it owns")
    a = ap.parse_args(argv)
    try:
        ri.require()   # a register that cannot be read is a cannot-run, named, never a traceback
        print(json.dumps(report({k: v for k, v in vars(a).items() if v is not None}), indent=1, ensure_ascii=False))
    except ri.RegisterUnreadable as e:
        print(f"{TOOL}: cannot run: {e}", file=sys.stderr)
        return 2
    except ReconcileError as e:
        print(f"{TOOL}: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    import cli_exit   # an unloadable subject or a failure to run is exit 2, one line, never a traceback
    sys.exit(cli_exit.run(main, TOOL))
