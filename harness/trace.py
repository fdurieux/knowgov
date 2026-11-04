"""knowgov-trace (task-0051; doc-0011 point 3): from a code change to the knowledge it rests on.

    python harness/trace.py register --instance DIR --commit SHA --file PATH [--file PATH ...]
                                     --ledger FILE [--repo NAME] [--assertion ID ...] [--task NAME]
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
row carry it as ``as_of``, with --assertion too (the day the registration read). The ledger is the registration's record: a load wipes the store, so ``check``
re-registers from it what the store no longer holds. Exit 0 recorded, 2 could not.

``check`` (on a pull request into the code) reads the ledger against the store and the files:

    blocker   suspect: a registered output used a statement now invalidated; it names the output's
              APP, the statements and their successors. The gate's own blockers on the task.
    major     missing: a registered file no longer exists; unmapped: a changed code path no row of
              code_map.toml maps. The gate's major findings.
    minor     drift: a registered file's digest differs from its registration; the edit is legitimate,
              the finding lists the statements the registered version used and asks for a new
              registration. The gate's minor findings.
    info      the gate's information findings.

With --changed, only registered outputs whose path changed or whose APP a changed path belongs to are
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

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from code_map import app_of, code_map, is_code, register_apps  # noqa: E402

SCHEMA_VERSION = 1
SEVERITIES = ["blocker", "critical", "major", "minor", "info"]
LEDGER_TOOL = "knowgov trace ledger"


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
    if not path.exists():
        if missing_ok:
            return {"tool": LEDGER_TOOL, "schema_version": SCHEMA_VERSION, "entries": []}
        raise CannotRun(f"no ledger at {path}; trace register writes it")
    try:
        led = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise CannotRun(f"the ledger {path} does not parse: {e}") from e
    ok = isinstance(led, dict) and led.get("tool") == LEDGER_TOOL and isinstance(led.get("entries"), list) and all(
        isinstance(e, dict) and all(isinstance(e.get(k), str) for k in ("id", "path", "app", "sha256", "commit"))
        and isinstance(e.get("assertions"), list) and isinstance(e.get("as_of", ""), str) for e in led["entries"])
    if not ok:
        raise CannotRun(f"the ledger {path} is not a {LEDGER_TOOL}")
    return led


def _gate_ids(st, task: str, resolve=None, as_of: str | None = None) -> list[str]:
    if resolve is None:
        from gate import resolve
    res = resolve(st, task, as_of) if as_of else resolve(st, task)
    return [a["id"] for v in res["keys"].values() for a in v["assertions"]]


def register(st, *, instance: Path, ledger: Path, commit: str, files: list[str], repo: str = "code",
             task: str = "codegen", assertions: list[str] | None = None, kind: str = "code", resolve=None,
             as_of: str | None = None) -> dict:
    """Register each file as a derived output; write the ledger. Returns the report. ``as_of`` (YYYY-MM-DD)
    is the date the task's gate is read on; None reads the gate's own default, and the ledger records none."""
    cm, root = read_map(instance)
    led = read_ledger(ledger, missing_ok=True)
    if not files:
        raise CannotRun("no --file: name the built or changed files to register")
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
        e = {"id": f"derived:{repo}@{commit}:{rel}", "path": rel, "app": app, "sha256": _sha(p), "commit": commit,
             "repo": repo, "kind": kind, "task": task, "assertions": ids}
        if as_of:
            e["as_of"] = as_of
        if e["id"] not in held:   # the same commit and path registered twice is one output
            st.register_derived(e["id"], kind, e["sha256"], ids)
        entries.append(e)
    named = {e["path"] for e in entries}
    led["entries"] = [e for e in led["entries"] if e["path"] not in named] + entries
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps(led, indent=1) + "\n", encoding="utf-8")
    return {"schema_version": SCHEMA_VERSION, "tool": "knowgov trace", "command": "register", "store": st.name,
            "task": task, "commit": commit, "code_root": cm["root"], "ledger": str(ledger), "changed": [],
            "registered": [{"id": e["id"], "path": e["path"], "app": e["app"], "sha256": e["sha256"], "current_sha256": e["sha256"],
                            "state": "registered", "used": len(ids), "used_invalidated": [], "successors": [],
                            **({"as_of": e["as_of"]} if "as_of" in e else {})} for e in entries],
            "gate": None, "findings": [], "counts": {s: 0 for s in SEVERITIES}, "threshold": None, "exit_code": 0}


def _finding(severity, kind, message, *, app=None, path=None, ref=None, related=()) -> dict:
    return {"severity": severity, "kind": kind, "app": app, "path": path, "ref": ref, "related": list(related), "message": message}


def check(st, *, instance: Path, ledger: Path, changed: list[str] | None = None, commit: str | None = None,
          task: str = "codegen", fail_on: str = "blocker", block_levels: set[str] | None = None, resolve=None,
          as_of: str | None = None) -> dict:
    """The check's report; raises CannotRun for what exit 2 covers."""
    cm, root = read_map(instance)
    led = read_ledger(ledger, missing_ok=False)
    held = {d["id"] for d in st.all_derived()}
    for e in led["entries"]:   # a load wiped the store since: the ledger is the record
        if e["id"] not in held:
            st.register_derived(e["id"], e.get("kind", "code"), e["sha256"], e["assertions"])
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
    rows = []
    for e in led["entries"]:
        if ch is not None and e["path"] not in ch and e["app"] not in scope_apps:
            continue
        p = root / e["path"]
        cur = _sha(p) if p.is_file() else None
        used = [b for b in (st.assertion_brief(a) for a in e["assertions"]) if b]
        bad = sorted(b["id"] for b in used if b.get("status") == "invalidated")
        keys = sorted({b["key"] for b in used if b["id"] in bad and b.get("key")})
        succ = sorted({t["id"] for x in (st.stale_on_keys(keys) if keys else []) if x["id"] in bad
                       for t in x.get("successors") or [] if t.get("id")})
        state = "missing" if cur is None else ("drift" if cur != e["sha256"] else "unchanged")
        rows.append({"id": e["id"], "path": e["path"], "app": e["app"], "sha256": e["sha256"], "current_sha256": cur,
                     "state": state, "used": len(e["assertions"]), "used_invalidated": bad, "successors": succ,
                     **({"as_of": e["as_of"]} if isinstance(e.get("as_of"), str) else {})})
        if bad:
            fs.append(_finding("blocker", "suspect", f"{e['path']} ({e['app']}), registered as {e['id']}, was built from {len(bad)} statement(s) "
                               f"now invalidated ({', '.join(bad)}); successors {', '.join(succ) or 'none'}: rebuild it from the current "
                               "statements and register it again", app=e["app"], path=e["path"], ref=e["id"], related=bad))
        if state == "missing":
            fs.append(_finding("major", "missing", f"{e['path']} ({e['app']}), registered as {e['id']}, no longer exists",
                               app=e["app"], path=e["path"], ref=e["id"]))
        elif state == "drift":
            by: dict[str, list[str]] = {}
            for b in used:
                by.setdefault(b.get("status") or "unknown", []).append(b["id"])
            lst = f"{len(used)} statement(s): " + ", ".join(
                f"{len(v)} {k}" + ("" if k in ("verified", "approved") else f" ({', '.join(sorted(v))})") for k, v in sorted(by.items()))
            fs.append(_finding("minor", "drift", f"{e['path']} ({e['app']}) changed since {e['id']}: it rested on {lst}; register the new version",
                               app=e["app"], path=e["path"], ref=e["id"], related=[b["id"] for b in used]))
    gate = None
    if ch is None or scope_apps or any(r["path"] in ch for r in rows):
        import gate_cli
        if resolve is None:
            from gate import resolve
        res = resolve(st, task, as_of) if as_of else resolve(st, task)
        gate = {"task": task, "verdict": res["verdict"], "why": res["why"]}
        if res.get("as_of"):
            gate["as_of"] = res["as_of"]
        apps = sorted(scope_apps) if scope_apps is not None else sorted({e["app"] for e in led["entries"]})
        for g in gate_cli.findings(res, block_levels or set()):
            if g["kind"] == "suspect_derived":
                continue
            fs.append(_finding(g["severity"], f"gate:{g['kind']}", f"{task}: {g['message']}",
                               app=", ".join(apps) or None, ref=g.get("ref") or g.get("key"), related=g.get("related") or []))
    order = ["suspect", "unmapped", "missing", "drift"]
    fs.sort(key=lambda f: (SEVERITIES.index(f["severity"]), order.index(f["kind"]) if f["kind"] in order else len(order), f["path"] or "", f["ref"] or ""))
    counts = {s: sum(1 for f in fs if f["severity"] == s) for s in SEVERITIES}
    fail = any(SEVERITIES.index(f["severity"]) <= SEVERITIES.index(fail_on) for f in fs)
    return {"schema_version": SCHEMA_VERSION, "tool": "knowgov trace", "command": "check", "store": st.name,
            "task": task, "commit": commit, "code_root": cm["root"], "ledger": str(ledger), "changed": ch or [],
            "registered": rows, "gate": gate, "findings": fs, "counts": counts, "threshold": fail_on, "exit_code": 1 if fail else 0}


def render(rep: dict) -> str:
    out = [f"knowgov trace {rep['command']} ({rep['store']}, task {rep['task']}, code root {rep['code_root']})"]
    for r in rep["registered"]:
        out.append(f"  {r['state']:10s} {r['app']}  {r['path']}  {r['id']}"
                   + (f"  {len(r['used_invalidated'])} of {r['used']} statement(s) invalidated" if r["used_invalidated"] else f"  {r['used']} statement(s)")
                   + (f", registered as of {r['as_of']}" if r.get("as_of") else ""))
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
        if args.task not in TASKS:
            raise CannotRun(f"{SUBJECT.id}: no task {args.task!r}")
        import cadence
        try:
            on = cadence.as_of(args.as_of).isoformat()
        except ValueError as e:
            raise CannotRun(f"--as-of: {e}") from e
        from store import open_store
        try:
            st = open_store(instance=SUBJECT.id)
        except Exception as e:  # noqa: BLE001
            raise CannotRun(f"the store cannot be opened: {e}") from e
        try:
            if args.command == "register":
                rep = register(st, instance=args.instance, ledger=args.ledger, commit=args.commit, files=args.file,
                               repo=args.repo, task=args.task, assertions=args.assertion, as_of=on)
            else:
                rep = check(st, instance=args.instance, ledger=args.ledger, changed=args.changed, commit=args.commit,
                            task=args.task, fail_on=args.fail_on, block_levels=set(TASKS[args.task]["block_levels"]), as_of=on)
        except CannotRun:
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
    sys.exit(main())
