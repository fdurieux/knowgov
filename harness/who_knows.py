"""Who knows what (task-0360, decision-0047 point 2): the handles, and their holders, whose attested evidence
touches a register node, a knowledge key or a code path.

    python harness/who_knows.py --node CAP-0002
    python harness/who_knows.py --key 'quote|currency'
    python harness/who_knows.py --path src/quote.py [--instance DIR]

Exactly one of the three is asked. The scope it names is one hop, never a walk (decision-0047 point 5):

``node``  the node, and the keys whose ``register_map.toml`` rows name it, in every subject the reader serves;
``key``   the key, and the nodes its rows name, in every subject that knows it (a map row or a task's key);
``path``  a path under the root of the instance's ``code_map.toml`` (``--instance`` or ``KG_INSTANCE``): the
          application or module the map assigns, the keys the file's header cites (``citation.read``) and the
          keys whose rows name that application.

The evidence, per handle, each item of one kind:

``answered``            a captured answer or "nobody knows" on a key in scope (the key, the subject, the capture's
                        statement id as the load gives it, ``on``), from each subject's ``[capture] dir``;
``approved``/``rejected`` a review's ruling by the handle on a statement of a key in scope (the review's id,
                        ``review:<stem>`` as the load gives it, the statement, ``on``), the key the ruling records,
                        else the capture's whose statement it rules;
``closed``              a review's close, by the handle, of a "nobody knows" gap on a key in scope (the gap,
                        the review, ``on``): a gap a document declares carries no key in its review file, so only
                        a captured gap's key is read from files;
``owns``                the handle's unit owns a node in scope, by its ``owner`` field or an approved ``owns``
                        link (``register_impact.owning_unit``); a handle with ``withdrawn`` recorded has none.

Items are sorted by kind, then key (a node for ``owns``), then date; handles by id. Nothing is counted, ranked,
weighted or scored (decision-0047 point 6). A handle is the register's issued handle (``people/handles.toml``,
decision 0009): its unit, the unit's name, its roles, ``issued`` and ``withdrawn``, and its holder, the register's
``person`` (ieam-register decision 0021), or null with ``holder_why`` when none is recorded. A handle the files
name that the register does not list is shown with ``listed`` false.

Files only, never the store: the subjects under ``KG_SUBJECTS`` (``subject_ids``), their captures and reviews, their
register maps, the one register they share (``KG_REGISTER``) and the instance's code map, so the report is the same
whichever store the reader is configured with (decision-0047 point 1). The review files are read as written: whether
a load applied a ruling is the store's (``three_valued_answer``). A subject that does not load is named under
``unread`` with its reason, and the rest answer. Standard library only; reads, never writes. Report pinned by
``harness/schemas/who-knows.schema.json``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SCHEMA_VERSION = 1
KINDS = ("answered", "approved", "closed", "owns", "rejected")   # the sort order: by kind, alphabetical
ASKED = ("node", "key", "path")


class WhoKnowsError(ValueError):
    """The question cannot be answered: an unknown node or key, a path outside the code map, no code map."""


def _iso(v) -> str | None:
    if isinstance(v, dt.date):
        return v.isoformat()
    return str(v) if v not in (None, "") else None


def holders(register: Path) -> tuple[dict[str, dict], str | None]:
    """handle -> the register's row for it (decision 0009, with decision 0021's ``person``), and the file read, from
    the register's issued list (``types.toml [elicited] issued``); ({}, None) when the register names none."""
    try:
        types = tomllib.loads((register / "metamodel" / "types.toml").read_text(encoding="utf-8"))
    except OSError:
        return {}, None
    rel = types.get("elicited", {}).get("issued")
    if not rel or not (register / rel).is_file():
        return {}, None
    rows = tomllib.loads((register / rel).read_text(encoding="utf-8")).get("handle", [])
    return {str(h["handle"]): h for h in rows if h.get("handle")}, rel


def _holder(row: dict | None, handle: str, rel: str | None) -> tuple[str | None, str | None]:
    """(holder, why): the register's ``person`` for the handle, or None and why it is none."""
    if row is None:
        return None, (f"{handle} is not on the register's issued list ({rel})" if rel
                      else "the register names no issued list (types.toml [elicited] issued)")
    person = row.get("person")
    if isinstance(person, str) and person.strip():
        return person, None
    return None, (f"{rel} records no person for {handle} (ieam-register decision 0021): its holder is in the "
                  "organisation's directory, or not recorded")


class _Subject:
    """What who_knows reads of one subject: its id, register-map rows, known keys and capture folder."""

    def __init__(self, entry: dict):
        from subject import Subject
        import key_rule
        s = Subject(entry["root"])
        self.id = s.id
        self.rows = [r for r in s.register_map().get("row", []) if isinstance(r.get("key"), str)]
        for r in self.rows:
            r["key"] = key_rule.normalise(r["key"])
        task_keys = {key_rule.normalise(k) for t in s.tasks.values() if isinstance(t, dict) for k in t.get("keys", [])
                     if isinstance(k, str)}
        self.known = {r["key"] for r in self.rows} | task_keys
        self.capture_dir = s.capture_dir


def subjects() -> tuple[list[_Subject], list[dict]]:
    """Every subject the reader serves, loaded, and those that do not load with the reason."""
    import subject_ids
    out, unread = [], []
    for entry in subject_ids.subjects():
        try:
            out.append(_Subject(entry))
        except Exception as e:  # noqa: BLE001 - a subject that does not load is named, and the rest answer
            unread.append({"subject": entry["id"], "why": f"{type(e).__name__}: {e}"})
    return out, unread


def _code_scope(path, instance: str | None, reg: dict, register: Path) -> dict:
    """The application the instance's code map assigns ``path`` and the keys its header cites."""
    import citation
    import code_map
    import upward
    try:
        rel = upward._rel(path)
    except upward.UpwardError as e:
        raise WhoKnowsError(str(e)) from None
    if not instance:
        raise WhoKnowsError("path: no instance configured (KG_INSTANCE or --instance), so no code_map.toml to read it under")
    inst = Path(instance)
    errors: list[str] = []
    rep = code_map.code_map(inst, code_map.register_apps(register), errors) if inst.is_dir() else None
    if rep is None or errors:
        raise WhoKnowsError(f"path: {inst}/code_map.toml " + ("is missing" if rep is None else "does not hold: " + "; ".join(errors)))
    croot = (inst / rep["root"]).resolve()
    target = (croot / rel).resolve()
    if not target.is_relative_to(croot):
        raise WhoKnowsError(f"path {rel!r}: resolves outside the code map's root")
    app = code_map.app_of(rep, rel)
    cited: list[str] = []
    if target.is_file() and citation.language(target) is not None:
        try:
            cited = citation.read(target) or []
        except citation.Malformed as e:
            raise WhoKnowsError(f"path {rel!r}: malformed citation: {e}") from None
    if app is None and not cited:
        raise WhoKnowsError(f"path {rel!r}: the code map assigns it no application and its header cites no key")
    return {"path": rel, "app": app, "cited": cited}


def _rows_naming(subs: list[_Subject], node: str) -> set[str]:
    """The keys whose register-map rows name ``node``, in every subject."""
    return {r["key"] for s in subs for r in s.rows if node in (r.get("nodes") or [])}


def _node_scope(node: str, subs: list[_Subject], reg: dict) -> dict:
    if node not in reg["nodes"]:
        raise WhoKnowsError(f"node {node!r}: not in the register")
    return {"nodes": {node}, "keys": _rows_naming(subs, node), "code": None, "asked": {"node": node}}


def _key_scope(key: str, subs: list[_Subject]) -> dict:
    import key_rule
    key = key_rule.normalise(key)
    known = set().union(*(s.known for s in subs)) if subs else set()
    if key not in known:
        raise WhoKnowsError(f"{key}: no key of the subjects this reader serves (their register maps' rows and their "
                            "tasks' keys)" + key_rule.did_you_mean(key, known))
    nodes = {n for s in subs for r in s.rows if r["key"] == key for n in (r.get("nodes") or [])}
    return {"nodes": nodes, "keys": {key}, "code": None, "asked": {"key": key}}


def _path_scope(path, subs: list[_Subject], reg: dict, register: Path, instance: str | None) -> dict:
    import key_rule
    code = _code_scope(path, instance, reg, register)
    keys = {key_rule.normalise(k) for k in code["cited"]} | (_rows_naming(subs, code["app"]) if code["app"] else set())
    return {"nodes": {code["app"]} if code["app"] else set(), "keys": keys, "code": code, "asked": {"path": code["path"]}}


def scope(asked: dict, subs: list[_Subject], reg: dict, register: Path, instance: str | None) -> dict:
    """The nodes and keys the question touches, one hop, and the code leg's facts for a path."""
    given = [k for k in ASKED if asked.get(k) is not None]
    if len(given) != 1:
        raise WhoKnowsError(f"name exactly one of {', '.join(ASKED)}; given {', '.join(given) or 'none'}")
    if given[0] == "node":
        return _node_scope(asked["node"], subs, reg)
    if given[0] == "key":
        return _key_scope(asked["key"], subs)
    return _path_scope(asked["path"], subs, reg, register, instance)


def _read(p: Path, kind: str) -> dict:
    import formats
    doc = tomllib.loads(p.read_text(encoding="utf-8"))
    formats.version(doc, p.as_posix(), kind)   # a capture or review for a newer knowgov is refused, never misread
    return doc


def _capture_items(p: Path, sid: str, keys: set[str], stmt_key: dict, gap_key: dict) -> list[tuple[str, dict]]:
    """One capture file's answers and nobody-knows on ``keys``, under the ids the load gives them; ``stmt_key`` and
    ``gap_key`` learn every statement's and captured gap's key, for the reviews."""
    import formats
    import key_rule
    c = _read(p, formats.CAPTURE)
    cap = c.get("capture", {})
    who, on = str(cap.get("from", "")), _iso(cap.get("on"))
    rows = [(f"A:cap:{p.stem}:{i}@capture", a, False) for i, a in enumerate(c.get("answer", []), 1)]
    rows += [(f"A:cap:{p.stem}:unknown{i}@capture", u, True) for i, u in enumerate(c.get("unknown", []), 1)]
    for i, u in enumerate(c.get("unknown", []), 1):
        gap_key[f"gap:declared:capture:{p.stem}:{i}"] = key_rule.normalise(str(u.get("key", "")))
    out = []
    for sid_, row, nobody in rows:
        k = key_rule.normalise(str(row.get("key", "")))
        stmt_key[sid_] = k
        if k in keys and who:
            out.append((who, {"kind": "answered", "key": k, "subject": sid, "on": on, "capture": sid_, "nobody_knows": nobody}))
    return out


def _review_items(p: Path, sid: str, keys: set[str], stmt_key: dict, gap_key: dict) -> list[tuple[str, dict]]:
    """One review file's rulings and closes by its handle on ``keys``: a ruling's key as it records it, else the key of
    the captured statement it names; a close's key the captured gap's."""
    import formats
    import key_rule
    rv = _read(p, formats.REVIEW)
    head = rv.get("review", {})
    by, on, rid = str(head.get("by", "")), _iso(head.get("on")), f"review:{p.stem}"
    if not by:
        return []
    out = []
    for ru in rv.get("ruling", []):
        aid = str(ru.get("assertion", ""))
        k = key_rule.normalise(str(ru["key"])) if ru.get("key") else stmt_key.get(aid)
        if ru.get("outcome") in ("approved", "rejected") and k in keys:
            out.append((by, {"kind": ru["outcome"], "key": k, "subject": sid, "on": on, "review": rid, "statement": aid}))
    for c in rv.get("closes", []):
        k = gap_key.get(str(c.get("gap", "")))
        if k in keys:
            out.append((by, {"kind": "closed", "key": k, "subject": sid, "on": on, "review": rid, "gap": str(c.get("gap"))}))
    return out


def evidence(subs: list[_Subject], keys: set[str]) -> list[tuple[str, dict]]:
    """(handle, item) for every captured answer, ruling and close on a key in ``keys``, from the files."""
    items: list[tuple[str, dict]] = []
    for s in subs:
        stmt_key: dict[str, str] = {}
        gap_key: dict[str, str] = {}
        for p in sorted(s.capture_dir.glob("*.toml")) if s.capture_dir.is_dir() else []:
            items += _capture_items(p, s.id, keys, stmt_key, gap_key)
        rdir = s.capture_dir / "reviews"
        for p in sorted(rdir.glob("*.toml")) if rdir.is_dir() else []:
            items += _review_items(p, s.id, keys, stmt_key, gap_key)
    return items


def owns(reg: dict, nodes: set[str], rows: dict[str, dict]) -> list[tuple[str, dict]]:
    """(handle, item) for each node in scope and each handle, not withdrawn, of a unit owning it."""
    import register_impact as ri
    out = []
    for node in sorted(nodes):
        o = ri.owning_unit(reg, node)
        units = {o["unit"]: "owner"} if o["unit"] else {}
        for u in o["owns"]:
            units.setdefault(u, "owns_link")
        for handle, row in rows.items():
            via = units.get(str(row.get("unit", "")))
            if via and not row.get("withdrawn"):
                out.append((handle, {"kind": "owns", "node": node, "via": via}))
    return out


def _order(item: dict) -> tuple:
    return (KINDS.index(item["kind"]), item.get("key") or item.get("node") or "", item.get("on") or "",
            item.get("subject") or "", item.get("capture") or item.get("review") or "", item.get("statement") or item.get("gap") or "")


def report(asked: dict, instance: str | None = None, register: Path | None = None) -> dict:
    """The who-knows report for exactly one of ``node``, ``key`` or ``path``."""
    import register_impact as ri
    import review
    register = (register or ri.register_root()).resolve()
    reg = ri.load_tools(register)["register"].load_register(register)
    subs, unread = subjects()
    sc = scope(asked, subs, reg, register, instance)
    rows, rel = holders(register)
    units = review.organisation_units(register)
    pairs = evidence(subs, sc["keys"]) + owns(reg, sc["nodes"], rows)
    by: dict[str, list[dict]] = {}
    for handle, item in pairs:
        by.setdefault(handle, []).append(item)
    handles = []
    for handle in sorted(by):
        row = rows.get(handle)
        holder, why = _holder(row, handle, rel)
        unit = (str(row.get("unit", "")) or None) if row else None
        handles.append({"handle": handle, "listed": row is not None, "unit": unit,
                        "unit_name": units.get(unit, "") if unit else None,
                        "roles": sorted(str(r) for r in (row or {}).get("roles", [])),
                        "issued": _iso((row or {}).get("issued")), "withdrawn": _iso((row or {}).get("withdrawn")),
                        "holder": holder, "holder_why": why,
                        "evidence": sorted(by[handle], key=_order)})
    return {"schema_version": SCHEMA_VERSION, "tool": "who_knows", "asked": sc["asked"],
            "nodes": sorted(sc["nodes"]), "keys": sorted(sc["keys"]),
            "code": None if sc["code"] is None else {"app": sc["code"]["app"], "cited": sc["code"]["cited"]},
            "subjects": [s.id for s in subs], "unread": unread, "register": ri.source(register),
            "issued_list": rel, "handles": handles}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="who_knows.py", description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--node", help="a register node id")
    g.add_argument("--key", help="an entity|attribute key")
    g.add_argument("--path", help="a code path relative to the root of the instance's code_map.toml")
    ap.add_argument("--instance", help="the instance whose code_map.toml a path is read under (default: KG_INSTANCE)")
    a = ap.parse_args(argv)
    import register_impact as ri
    import upward
    try:
        ri.require()
    except ri.RegisterUnreadable as e:
        print(f"who_knows: cannot run: {e}", file=sys.stderr)
        return 2
    try:
        rep = report({"node": a.node, "key": a.key, "path": a.path}, upward.config(a.instance)["instance"])
    except WhoKnowsError as e:
        print(f"who_knows: {e}", file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import cli_exit
    sys.exit(cli_exit.run(main, "who_knows"))
