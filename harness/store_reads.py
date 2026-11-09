"""The store reads over MCP (task-0144, doc-0020 C3): what the held scenario holds, key by key, and what
was built on it. Three single hops, each one read handle per call (the MCP server's ``_with_store``),
each on the port's reads only (``store.READS``):

``held_keys``            every key a statement of the held scenario names, by key, with its statement
                         count by status, its level as the gate reads it, and the task classes whose
                         required keys include it (``required_by``; empty: a key no class asks for, which
                         store_status, listing declared keys only, never shows). The levels are the
                         gate's own, ``gate_cli.evaluate`` over the held key set under one declared class
                         (codegen by default) on one ``as_of``, as ``register_impact`` reads them: never a
                         second computation. Its ``gate`` is the class's own verdict and why on its own
                         required keys, ``gate_verdict``'s for the same store, class and ``as_of`` (task-0283),
                         never the held key set gated as if every held key were required.
``derived_outputs``      with ``key``, every derived output that used a statement on the key, any state;
                         with ``derived``, that one output. Each with the statements it used, each read
                         live (not invalidated), stale (invalidated, nothing settled replaces it) or
                         superseded (invalidated, with the verified or approved successors
                         ``gate.superseded_by`` names), rejected otherwise, and the keys behind it.
``document_statements``  the statements a document yields (an artefact path; a directory's files by its
                         path ending in '/'), with an optional ``version`` where several are held: each
                         statement's key, status, version and the document's fragments it rests on, and
                         the derived outputs that used it.

Nothing here writes; nothing walks: each answer is one read of the port and the gate's own readings.
Reports pinned by ``harness/schemas/held-keys.schema.json``, ``derived-outputs.schema.json`` and
``document-statements.schema.json``.
"""
from __future__ import annotations

SCHEMA_VERSION = 1
LIVE = ("proposed", "validated", "verified", "approved", "disputed")   # trace.CURRENT: not invalidated


class ReadError(ValueError):
    """The question cannot be answered: a malformed argument, a key, output or document the store lacks."""


def held_keys(st, *, subject: str, scenario: str, task: str, as_of: str) -> dict:
    """Every held key with its count by status, its gate level under ``task`` and the classes requiring it."""
    import gate_cli
    from subject import SUBJECT
    from tasks import TASKS
    held = st.held_keys()
    keys = [k["key"] for k in held]
    levels: dict[str, str] = {}
    verdict = None
    version = gate_cli.held_version(st)
    if keys:
        spec = dict(TASKS[task], keys=keys)   # the levels: every held key's, as gate_verdict reads that key set
        rep = gate_cli.evaluate(st, subject=subject, scenario=scenario, task="keys", spec=spec, threshold="blocker",
                                baseline=None, loaded=False, version=version, as_of=as_of, route_task=task)
        levels = rep["levels"]
    # the verdict: the task class's own, on its own required keys, as gate_verdict gives it (task-0283, decision-0033
    # choice 9), whatever the store holds (task-0292: a store holding no key is BLOCKED there, never null here);
    # never the held key set gated under the class's bar as if all were required
    own = gate_cli.evaluate(st, subject=subject, scenario=scenario, task=task, spec=dict(TASKS[task]), threshold="blocker",
                            baseline=None, loaded=False, version=version, as_of=as_of, route_task=task)
    verdict = {"task": task, "verdict": own["verdict"], "why": own["why"]}
    mapped = {r["key"] for r in SUBJECT.register_map().get("row", []) if isinstance(r.get("key"), str)}
    rows = [{**k, "level": levels.get(k["key"]), "required_by": sorted(t for t, spec in TASKS.items() if k["key"] in spec["keys"]),
             "mapped": k["key"] in mapped} for k in held]
    declared = sorted({k for spec in TASKS.values() for k in spec["keys"]})
    return {"schema_version": SCHEMA_VERSION, "tool": "held_keys", "subject": subject, "scenario": scenario, "store": st.name,
            "as_of": as_of, "task": task, "total": len(rows), "keys": rows,
            "required_not_held": [k for k in declared if k not in set(keys)],
            "unrequired": [r["key"] for r in rows if not r["required_by"]], "gate": verdict}


def _states(st, used: list[dict]) -> list[dict]:
    """Each used statement read live, stale, superseded or rejected, with what supersedes it."""
    from gate import superseded_by
    inv_keys = sorted({u["key"] for u in used if u["status"] == "invalidated" and u["key"]})
    stale = {x["id"]: x for x in st.stale_on_keys(inv_keys)} if inv_keys else {}
    out = []
    for u in used:
        sup = superseded_by(stale[u["id"]]) if u["id"] in stale else []
        state = ("live" if u["status"] in LIVE else
                 ("superseded" if sup else "stale") if u["status"] == "invalidated" else "rejected")
        out.append({**u, "state": state, "superseded_by": sup})
    return out


def _output(st, d: dict) -> dict:
    used = _states(st, d["used"])
    return {"id": d["id"], "kind": d["kind"], "sha256": d["sha256"], "suspect": bool(d["suspect"]),
            **({"used_changed": d["used_changed"]} if d.get("used_changed") else {}),   # task-0199
            "keys": sorted({u["key"] for u in used if u["key"]}), "used": used}


def derived_outputs(st, *, subject: str, scenario: str, key=None, derived=None) -> dict:
    """With ``key`` the outputs built on it, with ``derived`` that one; exactly one of the two."""
    if (key is None) == (derived is None):
        raise ReadError("name exactly one of key (an entity|attribute key) or derived (a derived output id)")
    rows = st.derived_outputs()
    if key is not None:
        if not isinstance(key, str) or "|" not in key:
            raise ReadError(f"key {key!r}: an entity|attribute key")
        hit = [d for d in rows if any(u["key"] == key for u in d["used"])]
    else:
        if not isinstance(derived, str) or not derived:
            raise ReadError(f"derived {derived!r}: a derived output id, as the gate's suspect findings name it")
        hit = [d for d in rows if d["id"] == derived]
        if not hit:
            raise ReadError(f"{derived}: no derived output in the store (it holds {len(rows)})")
    return {"schema_version": SCHEMA_VERSION, "tool": "derived_outputs", "subject": subject, "scenario": scenario,
            "store": st.name, "key": key, "derived": derived, "total": len(hit), "outputs": [_output(st, d) for d in hit]}


def document_statements(st, *, subject: str, scenario: str, document, version=None) -> dict:
    """The statements ``document`` yields (``version`` among its held versions, else all), each with the
    derived outputs that used it; ReadError on a document no statement comes from."""
    if not isinstance(document, str) or not document.strip():
        raise ReadError(f"document {document!r}: an artefact path, as a statement's source names it")
    rows = st.artefact_assertions(document)
    if not rows:
        raise ReadError(f"{document}: no statement in the held scenario comes from it")
    versions = sorted({r["version"] for r in rows if r["version"] is not None})
    if version is not None:
        if version not in versions:
            raise ReadError(f"version {version!r}: {document} has {versions} held")
        rows = [r for r in rows if r["version"] == version]
    used_by: dict[str, list[str]] = {}
    for d in st.derived_outputs():
        for u in d["used"]:
            used_by.setdefault(u["id"], []).append(d["id"])
    statements = [{**r, "derived": sorted(used_by.get(r["id"], []))} for r in rows]
    return {"schema_version": SCHEMA_VERSION, "tool": "document_statements", "subject": subject, "scenario": scenario,
            "store": st.name, "document": document, "version": version, "versions": versions, "total": len(statements),
            "keys": sorted({s["key"] for s in statements if s["key"]}), "statements": statements,
            "derived": sorted({x for s in statements for x in s["derived"]})}
