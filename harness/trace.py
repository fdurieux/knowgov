"""knowgov-trace (task-0051; doc-0011 point 3): from a code change to the knowledge it rests on.

    python harness/trace.py register --instance DIR --commit SHA --file PATH [--file PATH ...]
                                     --ledger FILE [--repo NAME] [--task NAME]
                                     [--assertion ID ... | --keys K1,K2 | --cited]
                                     [--as-of today|record|YYYY-MM-DD] [--subject DIR] [-f text|json] [-o FILE]
    python harness/trace.py check    --instance DIR --ledger FILE [--changed PATH ...] [--commit SHA]
                                     [--task NAME] [--fail-on SEVERITY] [--as-of today|record|YYYY-MM-DD]
                                     [--subject DIR] [-f text|json] [-o FILE]

Both read the store KG_STORE names (neo4j by default, rdflib with KG_RDFLIB_FILE to persist), as the
instance's load left it; neither loads. Paths are relative to the root of the instance's
code_map.toml (harness/code_map.py), which names each path's APP id. Every input is a flag: nothing
here reads a CI platform's variables, which a wrapper maps to these flags.

``register`` (on merge, after the build) records each file as a derived output,
``derived:<repo>@<commit>:<path>``, with its sha256, its APP and the statements it was built from:
the ones named with --assertion, else every statement the task's gate serves now. It calls the
store's register_derived (USED_ASSERTION) and writes the entry to the ledger, replacing an earlier
entry for the same path. --as-of is the date the task's gate is read on to pick those statements, as
check's (task-0093): today by default, ``record`` or a YYYY-MM-DD date; each entry and each registered
row carry it as ``as_of``, with --assertion too (the day the registration read).

Hand-written code (task-0124; doc-0015 §3) is registered by the keys it rests on: ``--keys K1,K2``
registers each file on those keys' current statements (every statement on the key not invalidated,
whatever the task's gate serves), ``--cited`` on the keys each file's own header cites
(harness/citation.py: ``# knowgov-keys: K1, K2`` in Python, ``// knowgov-keys: ...`` in Java). The
entry and the registered row carry the keys as ``keys``. A key neither the subject's register map
nor any task names is an error (exit 2), as is a key with no current statement, a file ``--cited``
that cites nothing, and a file whose header cites other keys than ``--keys`` names. After a change
invalidates a cited key's statements the output reads suspect, as a built one does. The ledger is the registration's record: a load wipes the store, so ``check``
re-registers from it what the store no longer holds. Exit 0 recorded, 2 could not.

``check`` (on a pull request into the code) reads the ledger against the store and the files:

    blocker   suspect: a registered output used a statement now invalidated; it names the output's
              APP, the statements and their successors. The gate's own blockers on the task.
              unknown_key, malformed_citation: a code file's header cites a key the subject does not
              know, or a citation line that names none (task-0124).
    major     missing: a registered file no longer exists; unmapped: a changed code path no row of
              code_map.toml maps; uncited: where code_map.toml's [citations] require is true, a code
              file of a governed APP whose header cites no key. The gate's major findings.
    minor     drift: a registered file's digest differs from its registration; the edit is legitimate,
              the finding lists the statements the registered version used and asks for a new
              registration. The gate's minor findings.
    info      uncitable: where citations are required, a governed code file in a language the
              convention does not cover. The gate's information findings.

Citations are read from the mapped code files in scope (with --changed, the changed ones; without,
every mapped code file); without [citations] require nothing is uncited, but an unknown or malformed
citation is still a finding. With --changed, only registered outputs whose path changed or whose APP a changed path belongs to are
in scope; without it, every registered output. The task's gate runs on the store as it is, as
``gate_cli.py --no-load`` does; its suspect_derived findings are left out, the ledger's are reported.
--as-of is the date it reads review currency on, as gate_cli's (decision-0005; task-0089): today by
default, ``record`` or a YYYY-MM-DD date; a lapse is the gate's ``lapsed`` finding, and the report's
``gate`` names the date read.

Exit 0: no finding at or above --fail-on (blocker by default); 1: a finding at or above it; 2: the
check could not run: no code_map.toml or one that does not hold, no ledger or a malformed one, a
subject that does not load, an unreachable store. The JSON report (-f json) is pinned by
harness/schemas/trace-report.schema.json and validated before it is printed.
"""
from __future__ import annotations

if __name__ == "__main__":   # task-0200: a failure while loading (a pin not installed) is exit 2, its cause in one line
    import cli_exit
    cli_exit.guard("knowgov-trace")

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import citation  # noqa: E402
from code_map import app_of, code_map, is_code, register_apps  # noqa: E402

SCHEMA_VERSION = 1
SEVERITIES = ["blocker", "critical", "major", "minor", "info"]
LEDGER_TOOL = "knowgov trace ledger"
CURRENT = ["proposed", "validated", "verified", "approved", "disputed"]   # a key's statements not invalidated


class CannotRun(Exception):
    """exit 2"""


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_map(instance: Path) -> tuple[dict, Path]:
    """The instance's code map, which must exist and hold, and its root on disk."""
    inst = instance.resolve()
    if not inst.is_dir():
        raise CannotRun(f"no instance at {instance}")
    errors: list[str] = []
    rep = code_map(inst, register_apps(inst / "register"), errors)
    if rep is None:
        raise CannotRun(f"{inst}/code_map.toml: missing; the trace names a path's APP through it")
    if errors:
        raise CannotRun("code_map.toml does not hold: " + "; ".join(errors))
    return rep, (inst / rep["root"]).resolve()


def read_ledger(path: Path, *, missing_ok: bool) -> dict:
    """The ledger at ``path``. Its ``schema_version`` is its format version (``harness/formats.py``, task-0280):
    missing reads as 1, a newer one raises ``FormatTooNew`` (exit 2 through ``cli_exit``); not one, ``CannotRun``."""
    import formats
    if not path.exists():
        if missing_ok:
            return {"tool": LEDGER_TOOL, "schema_version": formats.CURRENT[formats.LEDGER], "entries": []}
        raise CannotRun(f"no ledger at {path}; trace register writes it")
    try:
        led = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise CannotRun(f"the ledger {path} does not parse: {e}") from e
    if isinstance(led, dict):   # task-0280: a ledger written for a newer knowgov is refused, FormatTooNew, exit 2
        formats.version(led, str(path), formats.LEDGER)
    ok = isinstance(led, dict) and led.get("tool") == LEDGER_TOOL and isinstance(led.get("entries"), list) and all(
        isinstance(e, dict) and all(isinstance(e.get(k), str) for k in ("id", "path", "app", "sha256", "commit"))
        and isinstance(e.get("assertions"), list) and isinstance(e.get("as_of", ""), str)
        and isinstance(e.get("keys", []), list) for e in led["entries"])
    if not ok:
        raise CannotRun(f"the ledger {path} is not a {LEDGER_TOOL}")
    return led


def _gate_ids(st, task: str, resolve=None, as_of: str | None = None) -> list[str]:
    if resolve is None:
        from gate import resolve
    res = resolve(st, task, as_of) if as_of else resolve(st, task)
    return [a["id"] for v in res["keys"].values() for a in v["assertions"]]


def known_keys() -> set[str]:
    """The keys the subject knows: its register map's rows and every task's keys."""
    from subject import SUBJECT
    from tasks import TASKS
    return {r["key"] for r in SUBJECT.register_map().get("row", []) if isinstance(r.get("key"), str)} \
        | {k for t in TASKS.values() for k in t["keys"]}


def _key_ids(st, keys: list[str], known: set[str] | None) -> list[str]:
    """The current statements on the keys, in key order; CannotRun on an unknown key or one with none."""
    unknown = [k for k in keys if known is not None and k not in known]
    if unknown:
        raise CannotRun(f"unknown key(s) {', '.join(unknown)}: neither the subject's register map nor any task names them")
    ids: list[str] = []
    for k in keys:
        cur = sorted(a["id"] for a in st.assertions_on_key(k, CURRENT))
        if not cur:
            raise CannotRun(f"{k}: the store holds no current statement on the key; is the instance loaded?")
        ids += [a for a in cur if a not in ids]
    return ids


def _cited(p: Path, rel: str) -> list[str] | None:
    try:
        return citation.read(p)
    except citation.Malformed as e:
        raise CannotRun(f"{rel}: its citation does not hold: {e}") from e


def register(st, *, instance: Path, ledger: Path, commit: str, files: list[str], repo: str = "code",
             task: str = "codegen", assertions: list[str] | None = None, kind: str = "code", resolve=None,
             as_of: str | None = None, keys: list[str] | None = None, cited: bool = False,
             known: set[str] | None = None) -> dict:
    """Register each file as a derived output; write the ledger. Returns the report. ``as_of`` (YYYY-MM-DD)
    is the date the task's gate is read on; None reads the gate's own default, and the ledger records none.
    ``keys`` or ``cited`` (task-0124) register hand-written code on the keys' current statements instead:
    the keys given, or each file's header citation; ``known`` is the subject's key set (known_keys())."""
    cm, root = read_map(instance)
    led = read_ledger(ledger, missing_ok=True)
    if not files:
        raise CannotRun("no --file: name the built or changed files to register")
    if sum(map(bool, (assertions, keys, cited))) > 1:
        raise CannotRun("--assertion, --keys and --cited are exclusive: name the statements, the keys or neither")
    ids = []
    if keys:
        ids = _key_ids(st, list(keys), known)
    elif not cited:
        ids = list(assertions) if assertions else _gate_ids(st, task, resolve, as_of)
        if not ids:
            raise CannotRun(f"no statement to register against: the store serves none for {task!r}; is the instance loaded?")
    held = {d["id"] for d in st.all_derived()}
    entries = []
    for rel in files:
        rel = Path(rel).as_posix()
        p = root / rel
        if not p.is_file():
            raise CannotRun(f"{rel}: no such file under the code map's root {cm['root']}")
        app = app_of(cm, rel)
        if app is None:
            raise CannotRun(f"{rel}: no row of code_map.toml maps it; map it before registering it")
        on, file_ids = None, ids
        if keys or cited:
            head = _cited(p, rel)
            if cited:
                if not head:
                    raise CannotRun(f"{rel}: --cited, but its header cites no key"
                                    + (f" ({citation.MARK} covers {', '.join(sorted(citation.COMMENT))} files)" if head is None else ""))
                on, file_ids = head, _key_ids(st, head, known)
            else:
                on = list(keys)
                if head and sorted(head) != sorted(on):
                    raise CannotRun(f"{rel}: its header cites {', '.join(head)}, --keys names {', '.join(on)}: make them agree")
        e = {"id": f"derived:{repo}@{commit}:{rel}", "path": rel, "app": app, "sha256": _sha(p), "commit": commit,
             "repo": repo, "kind": kind, "task": task, "assertions": file_ids,
             "used": used_content(st, file_ids)}   # task-0199: what it was built on, so a change under an id reads suspect
        if on is not None:
            e["keys"] = on
        if as_of:
            e["as_of"] = as_of
        if e["id"] not in held:   # the same commit and path registered twice is one output
            st.register_derived(e["id"], kind, e["sha256"], file_ids, e["used"])
        entries.append(e)
    named = {e["path"] for e in entries}
    led["entries"] = [e for e in led["entries"] if e["path"] not in named] + entries
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps(led, indent=1) + "\n", encoding="utf-8")
    return {"schema_version": SCHEMA_VERSION, "tool": "knowgov trace", "command": "register", "store": st.name,
            "task": task, "commit": commit, "code_root": cm["root"], "ledger": str(ledger), "changed": [],
            "registered": [{"id": e["id"], "path": e["path"], "app": e["app"], "sha256": e["sha256"], "current_sha256": e["sha256"],
                            "state": "registered", "used": len(e["assertions"]), "used_invalidated": [], "successors": [],
                            **({"as_of": e["as_of"]} if "as_of" in e else {}), **({"keys": e["keys"]} if "keys" in e else {})}
                           for e in entries],
            "gate": None, "findings": [], "counts": {s: 0 for s in SEVERITIES}, "threshold": None, "exit_code": 0}


def used_content(st, ids: list[str]) -> list[dict]:
    """Each statement ``ids`` names as the store holds it now: {id, key, value, sha256} (``store.content_digest``
    of its fragments), the ledger's record of what an output was built on (task-0199, doc-0030 H6)."""
    from store import statement_content
    held = statement_content(st, ids)
    return [{k: held[a][k] for k in ("id", "key", "value", "sha256")} for a in ids if a in held]


def _finding(severity, kind, message, *, app=None, path=None, ref=None, related=(), keys=None, carry=None) -> dict:
    """A finding; ``keys``, the keys it rests on, gives it their owner and route (``_own``, task-0304), and ``carry``, a
    gate finding, passes on the owner and route the gate gave it."""
    f = {"severity": severity, "kind": kind, "app": app, "path": path, "ref": ref, "related": list(related), "message": message}
    if keys:
        f["_keys"] = list(keys)
    for k in ("owner", "route"):
        if carry is not None and k in carry:
            f[k] = carry[k]
    return f


def entry_keys(e: dict) -> list[str]:
    """The keys a ledger entry rests on, sorted: those it was registered on (--keys, --cited) and those of the
    statements it recorded using (task-0303, task-0304)."""
    used = e.get("used") if isinstance(e.get("used"), list) else []
    return sorted(set(e.get("keys") or []) | {u["key"] for u in used if isinstance(u, dict) and u.get("key")})


def _keys_of(e: dict, ids: list[str], briefs: list[dict] | None = None) -> list[str]:
    """The keys of the statements ``ids`` (by their briefs, else by the entry's own record of what it used), else the
    entry's keys (task-0304)."""
    rows = briefs if briefs is not None else (e.get("used") if isinstance(e.get("used"), list) else [])
    return sorted({b["key"] for b in rows if isinstance(b, dict) and b.get("id") in ids and b.get("key")}) or entry_keys(e)


def _routing(st, task: str):
    """task-0304: the subject's key owners (``capture.finding_owners``, as the gate reads them) and the route a finding
    names, the owner's questionnaire for the scenario the store holds and ``task``, as the gate report's (task-0102)."""
    from capture import finding_owners, questionnaire_route
    from subject import SUBJECT
    owners = finding_owners(SUBJECT)
    scenario = (st.held() or {}).get("scenario")

    def route(unit, key):
        return questionnaire_route(SUBJECT.id, scenario, task, unit, (owners.get(key) or {}).get("files"))
    return owners, route if scenario else None   # no load held: no questionnaire to route to


def _own(fs: list[dict], owners: dict, route) -> None:
    """Each finding that rests on keys names their owner and route (``gate_cli.owner_route``); one that rests on none
    names neither (task-0304)."""
    import gate_cli
    for f in fs:
        keys = f.pop("_keys", None)
        if keys:
            f["owner"], f["route"] = gate_cli.owner_route(sorted(set(keys)), owners, route)


def gate_identity(task: str) -> dict:
    """What the trace's gate decided on, read as the gate report reads it (decision-0029, task-0304): the digest of the
    subject's [tasks.<task>] table, the register's tag and commit, and this knowgov's build."""
    import gate_cli
    from subject import SUBJECT
    table = dict(SUBJECT.tasks[task]) if task in SUBJECT.tasks else None
    return {"task_profile": gate_cli.profile_digest(table), "register": gate_cli.register_identity(),
            "knowgov": gate_cli.knowgov_identity()}


def ledger_suspicion(st, entry: dict) -> dict:
    """task-0303: whether a ledger entry is suspect on the store ``st`` holds, by the rule check reads
    (``store.suspicion``: a statement it used now invalidated, or one it recorded now changed or no longer held),
    from the entry's own record, with nothing registered or written: {status: read, suspect, used_invalidated,
    used_changed}."""
    import json
    import store
    used = [{"id": a, "status": (st.assertion_brief(a) or {}).get("status")} for a in entry.get("assertions") or []]
    row = {"id": entry["id"], "kind": entry.get("kind", "code"), "sha256": entry["sha256"], "used": used,
           "recorded": json.dumps(entry["used"]) if isinstance(entry.get("used"), list) else None}
    [r] = store.suspicion(st, [row])
    return {"status": "read", "suspect": r["suspect"], "used_invalidated": r["used_invalidated"], "used_changed": r["used_changed"]}


def check(st, *, instance: Path, ledger: Path, changed: list[str] | None = None, commit: str | None = None,
          task: str = "codegen", fail_on: str = "blocker", block_levels: set[str] | None = None, resolve=None,
          as_of: str | None = None, known: set[str] | None = None) -> dict:
    """The check's report; raises CannotRun for what exit 2 covers. ``known`` is the subject's key set,
    which a citation's keys are read against (None: not read)."""
    cm, root = read_map(instance)
    led = read_ledger(ledger, missing_ok=False)
    held = {d["id"] for d in st.all_derived()}
    for e in led["entries"]:   # a load wiped the store since: the ledger is the record, with what each output used
        if e["id"] not in held:
            st.register_derived(e["id"], e.get("kind", "code"), e["sha256"], e["assertions"],
                                e["used"] if isinstance(e.get("used"), list) else None)
    # task-0199 (doc-0030 R5, doc-0032 §6 item 6): suspect by the port's one read, the gate's and the MCP reader's
    sus = {d["id"]: d for d in st.suspect_derived()}
    owners, route = _routing(st, task)   # task-0304: who answers for the keys a finding rests on
    now = {}
    fs: list[dict] = []
    scope_apps: set[str] | None = None
    ch = [Path(c).as_posix() for c in changed] if changed is not None else None
    if ch is not None:
        scope_apps = set()
        for c in ch:
            if not is_code(cm, c):
                continue
            app = app_of(cm, c)
            if app is None:
                fs.append(_finding("major", "unmapped", f"{c} is code no row of code_map.toml maps: the change reaches no knowledge", path=c))
            else:
                scope_apps.add(app)
    fs += _citation_findings(cm, root, ch, known)
    rows = []
    for e in led["entries"]:
        if ch is not None and e["path"] not in ch and e["app"] not in scope_apps:
            continue
        p = root / e["path"]
        cur = _sha(p) if p.is_file() else None
        used = [b for b in (st.assertion_brief(a) for a in e["assertions"]) if b]
        bad = list(sus.get(e["id"], {}).get("used_invalidated") or [])
        changed = list(sus.get(e["id"], {}).get("used_changed") or [])
        keys = sorted({b["key"] for b in used if b["id"] in bad and b.get("key")})
        succ = sorted({t["id"] for x in (st.stale_on_keys(keys) if keys else []) if x["id"] in bad
                       for t in x.get("successors") or [] if t.get("id")})
        state = "missing" if cur is None else ("drift" if cur != e["sha256"] else "unchanged")
        rows.append({"id": e["id"], "path": e["path"], "app": e["app"], "sha256": e["sha256"], "current_sha256": cur,
                     "state": state, "used": len(e["assertions"]), "used_invalidated": bad, "successors": succ,
                     **({"used_changed": changed} if changed else {}),
                     **({"as_of": e["as_of"]} if isinstance(e.get("as_of"), str) else {}),
                     **({"keys": e["keys"]} if isinstance(e.get("keys"), list) else {})})
        if bad:
            on = f", resting on the cited key(s) {', '.join(keys)}," if isinstance(e.get("keys"), list) else ""
            fs.append(_finding("blocker", "suspect", f"{e['path']} ({e['app']}), registered as {e['id']}{on} was built from {len(bad)} statement(s) "
                               f"now invalidated ({', '.join(bad)}); successors {', '.join(succ) or 'none'}: rebuild it from the current "
                               "statements and register it again", app=e["app"], path=e["path"], ref=e["id"], related=bad,
                               keys=_keys_of(e, bad, used)))
        if changed:   # task-0199 (doc-0030 H6): the same id, another content, as after an edit and a reload
            was = {u["id"]: u for u in e.get("used") or []}
            if not now:
                from store import statement_content
                now.update(statement_content(st, [u["id"] for x in led["entries"] for u in x.get("used") or []]))
            what = "; ".join(f"{a} {was[a]['value']!r} (sha256 {was[a]['sha256'][:12]}) now "
                             + (f"{now[a]['value']!r} (sha256 {now[a]['sha256'][:12]})" if a in now else "no longer held") for a in changed)
            fs.append(_finding("blocker", "suspect", f"{e['path']} ({e['app']}), registered as {e['id']}, was built on statement(s) that "
                               f"changed under their id since: {what}: rebuild it from the current statements and register it again",
                               app=e["app"], path=e["path"], ref=e["id"], related=changed,
                               keys=_keys_of(e, changed)))
        if not isinstance(e.get("used"), list):   # the read rule: an entry written before 0.9.0
            fs.append(_finding("info", "unbound", f"{e['path']} ({e['app']}), registered as {e['id']}, has a ledger entry from before 0.9.0: "
                               "it records ids only, so a change under the same id is not seen; register it again to bind it to content",
                               app=e["app"], path=e["path"], ref=e["id"], keys=entry_keys(e)))
        if state == "missing":
            fs.append(_finding("major", "missing", f"{e['path']} ({e['app']}), registered as {e['id']}, no longer exists",
                               app=e["app"], path=e["path"], ref=e["id"], keys=entry_keys(e)))
        elif state == "drift":
            by: dict[str, list[str]] = {}
            for b in used:
                by.setdefault(b.get("status") or "unknown", []).append(b["id"])
            lst = f"{len(used)} statement(s): " + ", ".join(
                f"{len(v)} {k}" + ("" if k in ("verified", "approved") else f" ({', '.join(sorted(v))})") for k, v in sorted(by.items()))
            fs.append(_finding("minor", "drift", f"{e['path']} ({e['app']}) changed since {e['id']}: it rested on {lst}; register the new version",
                               app=e["app"], path=e["path"], ref=e["id"], related=[b["id"] for b in used], keys=entry_keys(e)))
    gate = None
    if ch is None or scope_apps or any(r["path"] in ch for r in rows):
        import gate_cli
        if resolve is None:
            from gate import resolve
        res = resolve(st, task, as_of) if as_of else resolve(st, task)
        gate = {"task": task, "verdict": res["verdict"], "why": res["why"], **gate_identity(task)}   # task-0304: what it decided on
        if res.get("as_of"):
            gate["as_of"] = res["as_of"]
        apps = sorted(scope_apps) if scope_apps is not None else sorted({e["app"] for e in led["entries"]})
        for g in gate_cli.findings(res, block_levels or set(), owners, route):   # task-0304: the gate's owner and route
            if g["kind"] == "suspect_derived":
                continue
            fs.append(_finding(g["severity"], f"gate:{g['kind']}", f"{task}: {g['message']}",
                               app=", ".join(apps) or None, ref=g.get("ref") or g.get("key"), related=g.get("related") or [], carry=g))
    _own(fs, owners, route)
    order = ["suspect", "unknown_key", "malformed_citation", "unmapped", "uncited", "missing", "drift", "uncitable", "unbound"]
    fs.sort(key=lambda f: (SEVERITIES.index(f["severity"]), order.index(f["kind"]) if f["kind"] in order else len(order), f["path"] or "", f["ref"] or ""))
    counts = {s: sum(1 for f in fs if f["severity"] == s) for s in SEVERITIES}
    fail = any(SEVERITIES.index(f["severity"]) <= SEVERITIES.index(fail_on) for f in fs)
    return {"schema_version": SCHEMA_VERSION, "tool": "knowgov trace", "command": "check", "store": st.name,
            "task": task, "commit": commit, "code_root": cm["root"], "ledger": str(ledger), "changed": ch or [],
            "registered": rows, "gate": gate, "findings": fs, "counts": counts, "threshold": fail_on, "exit_code": 1 if fail else 0}


def _citation_findings(cm: dict, root: Path, changed: list[str] | None, known: set[str] | None) -> list[dict]:
    """task-0124: the header citations of the mapped code files in scope, read against the subject's keys."""
    fs, cit = [], cm.get("citations") or {"require": False, "apps": []}
    for r in cm["rows"]:
        for rel in r["files"]:
            if changed is not None and rel not in changed:
                continue
            p = root / rel
            if not p.is_file():
                continue
            governed = cit["require"] and r["app"] in cit["apps"]
            try:
                keys = citation.read(p)
            except citation.Malformed as e:
                fs.append(_finding("blocker", "malformed_citation", f"{rel} ({r['app']}): its citation does not hold: {e}", app=r["app"], path=rel))
                continue
            if keys is None:
                if governed:
                    fs.append(_finding("info", "uncitable", f"{rel} ({r['app']}): {citation.MARK} covers {', '.join(sorted(citation.COMMENT))} "
                                       "files; this one cannot cite its keys", app=r["app"], path=rel))
                continue
            unknown = [k for k in keys if known is not None and k not in known]
            if unknown:
                fs.append(_finding("blocker", "unknown_key", f"{rel} ({r['app']}) cites {', '.join(unknown)}, which neither the subject's "
                                   "register map nor any task names: cite the keys it rests on", app=r["app"], path=rel, related=unknown))
            if not keys and governed:
                fs.append(_finding("major", "uncited", f"{rel} ({r['app']}) cites no key, and code_map.toml requires {r['app']}'s code to: add a "
                                   f"'{citation.language(p)} {citation.MARK} K1, K2' header line and register it with --cited",
                                   app=r["app"], path=rel))
    return fs


def render(rep: dict) -> str:
    out = [f"knowgov trace {rep['command']} ({rep['store']}, task {rep['task']}, code root {rep['code_root']})"]
    for r in rep["registered"]:
        out.append(f"  {r['state']:10s} {r['app']}  {r['path']}  {r['id']}"
                   + (f"  {len(r['used_invalidated'])} of {r['used']} statement(s) invalidated" if r["used_invalidated"] else f"  {r['used']} statement(s)")
                   + (f", registered as of {r['as_of']}" if r.get("as_of") else "")
                   + (f", on key(s) {', '.join(r['keys'])}" if r.get("keys") else ""))
    if rep["gate"]:
        out.append(f"  gate {rep['gate']['task']}: {rep['gate']['verdict']} — {rep['gate']['why']}"
                   + (f" (as of {rep['gate']['as_of']})" if rep["gate"].get("as_of") else ""))
    for f in rep["findings"]:
        out.append(f"  {f['severity']:8s} {f['message']}")
    if rep["command"] == "register":
        out.append(f"exit 0: {len(rep['registered'])} output(s) registered in {rep['ledger']}")
    else:
        c = rep["counts"]
        out.append("findings: " + (", ".join(f"{c[s]} {s}" for s in SEVERITIES if c[s]) or "none"))
        out.append(f"exit {rep['exit_code']}: " + ("a finding" if rep["exit_code"] else "no finding") + f" at or above {rep['threshold']}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trace.py", description="From a code change to the knowledge it rests on; exit 0, 1 or 2.")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("register", "check"):
        p = sub.add_parser(name)
        p.add_argument("--instance", required=True, type=Path, help="the instance: its code_map.toml and register/")
        p.add_argument("--ledger", required=True, type=Path, help="the registrations' record (JSON); register writes it, check reads it")
        p.add_argument("--subject", help="the subject root (default: KG_SUBJECT)")
        p.add_argument("--task", default="codegen", help="the task whose statements the code builds on (default: codegen)")
        p.add_argument("--commit", required=name == "register", help="the commit sha")
        p.add_argument("-f", "--format", choices=["text", "json"], default="text")
        p.add_argument("-o", "--output", help="also write the JSON report to this file")
    r = sub.choices["register"]
    r.add_argument("--file", action="append", default=[], help="a built or changed file, relative to the code map's root (repeat)")
    r.add_argument("--repo", default="code", help="the code repository's name, in the derived id (default: code)")
    r.add_argument("--assertion", action="append", default=[], help="a statement the build used (repeat; default: every statement the task's gate serves)")
    r.add_argument("--keys", type=lambda v: [k.strip() for k in v.split(",") if k.strip()], default=None, metavar="K1,K2",
                   help="hand-written code: register on these keys' current statements (task-0124)")
    r.add_argument("--cited", action="store_true", help="hand-written code: register each file on the keys its header cites (task-0124)")
    r.add_argument("--as-of", default="today", metavar="DATE",
                   help="the date the task's gate is read on to pick the statements (decision-0005): today (default), record or YYYY-MM-DD")
    c = sub.choices["check"]
    c.add_argument("--changed", action="append", help="a changed path, relative to the code map's root (repeat; default: check every registered output)")
    c.add_argument("--fail-on", choices=SEVERITIES, default="blocker")
    c.add_argument("--as-of", default="today", metavar="DATE",
                   help="the date the task's gate reads review currency on (decision-0005): today (default), record or YYYY-MM-DD")
    args = ap.parse_args(argv)
    try:
        if not args.instance.is_dir():
            raise CannotRun(f"no instance at {args.instance}")
        if args.subject:
            os.environ["KG_SUBJECT"] = str(Path(args.subject).resolve())
        try:
            from subject import SUBJECT
            from tasks import TASKS
        except Exception as e:  # noqa: BLE001
            raise CannotRun(f"the subject does not load: {e}") from e
        if args.command == "register" and args.keys == []:
            raise CannotRun("--keys names no key")
        if args.task not in TASKS:
            raise CannotRun(f"{SUBJECT.id}: no task {args.task!r}")
        import cadence
        try:
            on = cadence.as_of(args.as_of).isoformat()
        except ValueError as e:
            raise CannotRun(f"--as-of: {e}") from e
        from store import open_store
        import switches
        try:
            st = open_store(instance=SUBJECT.id, access="write")
        except Exception as e:  # noqa: BLE001
            raise CannotRun(f"the store cannot be opened: {e}") from e
        try:
            if args.command == "register":
                rep = register(st, instance=args.instance, ledger=args.ledger, commit=args.commit, files=args.file,
                               repo=args.repo, task=args.task, assertions=args.assertion, as_of=on,
                               keys=args.keys, cited=args.cited, known=known_keys())
            else:
                rep = check(st, instance=args.instance, ledger=args.ledger, changed=args.changed, commit=args.commit,
                            task=args.task, fail_on=args.fail_on, block_levels=set(TASKS[args.task]["block_levels"]), as_of=on,
                            known=known_keys())
            st.commit()   # task-0141.02: what it registered, published once the report is made
        except (CannotRun, switches.BadSwitch):   # task-0287 N9: a misspelt switch is named as itself
            raise
        except Exception as e:  # noqa: BLE001
            raise CannotRun(f"the store did not answer: {type(e).__name__}: {e}") from e
        finally:
            try:
                st.close()
            except Exception:  # noqa: BLE001
                pass
    except CannotRun as e:
        print(f"trace: cannot run: {e}", file=sys.stderr)
        return 2
    from schema_check import load as load_schema, validate
    errs = validate(rep, load_schema("trace-report"))
    if errs:
        print("trace: cannot run: the report does not match its schema: " + "; ".join(errs[:5]), file=sys.stderr)
        return 2
    if args.output:
        Path(args.output).write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=1) if args.format == "json" else render(rep))
    return rep["exit_code"]


if __name__ == "__main__":
    import cli_exit   # task-0200 (doc-0030 F6): every failure to run is exit 2 with its cause, never 1
    sys.exit(cli_exit.run(main, "knowgov-trace", register=True))   # task-0288: a named register it cannot read, exit 2
