"""The gate as a command (task-0007), under the programme's gate contract (fdurieux.github.io).

    python harness/gate_cli.py [--subject DIR] [--scenario ID] [--task NAME]
                               [--fail-on blocker|critical|major|minor|info]
                               [--baseline none|record|FILE] [--stage 1|2 [--reverify]] [--no-load]
                               [--as-of today|record|YYYY-MM-DD]
                               [-f text|json] [-o FILE]

It loads the scenario of a subject into the store (KG_STORE: neo4j by default, rdflib in memory),
runs the rules, resolves the task's required keys through the same gate the arms read
(harness/gate.py), and turns the result into findings on the contract's severity ladder:

    blocker   a required key at one of the task's block levels (absent, a declared gap, disputed,
              invalidated), or the task as a whole when too many keys are below verified;
              a registered derived output (generated code) that used a statement now invalidated:
              it may not be reused as it is, whatever the verdict on the keys (task-0048)
    major     a required key below verified (proposed or validated); a stale statement on a
              required key that no verified or approved successor replaces (task-0048); a statement
              whose review has lapsed (``lapsed``, decision-0005): it reads validated until a new review
    minor     a verified or approved key carrying a flag (ambiguous, inferred, assumed)
    info      a stale statement on a required key that a verified or approved successor
              replaces: the record of the change, and the verifications it ended (task-0048)

A review falls due (decision-0005, harness/cadence.py): a verification of method review is current
until its date plus the review months of the kind its key concerns, from the register's
``metamodel/lifecycle.toml`` (``[review.kinds]``, the shortest among the nodes the key's row in the
subject's ``register_map.toml`` names, else ``default_months``); the load writes that date as its
``valid_until``. ``--as-of`` is the date currency is read on: today by default (KG_TODAY, else the
clock), so a pipeline's ratchet catches a lapse as ``verified -> validated``; ``record`` is the
subject's pinned record date (``[record] as_of``), which the deterministic run and the comparator
read, so the record never moves by the clock. Execution verifications do not lapse by date; a
person's approval in a review file renews a lapsed review from its own date.

The verdict is the gate's on the required keys (harness/gate.py, pinned by the record); the
findings add what the verdict does not weigh, so PROCEED with a suspect derived output exits 1.

Exit codes, the contract's three:

    0  no finding at or above the threshold (--fail-on, blocker by default: PROCEED and QUALIFIED pass)
    1  a finding at or above it (BLOCKED always; QUALIFIED with --fail-on major or minor)
    2  the gate could not run: no such subject, scenario or task, an unreachable store, no baseline

With a baseline the gate ratchets instead: exit 1 only on a regression, a verdict worse than the
baseline's, a required key at a lower level than the baseline's, or a derived output suspect that
the baseline did not hold suspect. ``--baseline record`` is the
subject's record for the same scenario (its deterministic run; the record's gate is the codegen
task); ``--baseline FILE`` is an earlier report of this command or a deterministic.json. The gate
never writes a baseline: recording one is a separate, deliberate act (``-o``, then commit it).

A capture (harness/capture.py) does not trip the ratchet by agreeing (decision-0004): a person's
answer nobody has reviewed yet is left out of its key's level when the key holds a validated-or-better
statement, and the bundle marks it pending review. Alone on a key it sets the level (absent ->
proposed, no regression); contradicting a document it makes the key disputed (R-CONFLICT), a
regression, which is what the ratchet is for.

``--stage 2`` brings in the scenario's later version after stage 1, as ``harness/run.py``'s stage 2
does (``harness/change.py``, task-0049): the subject's ``[scenario.stage2]`` artefact re-ingested as
its new version, the statements that rested on its changed fragments invalidated, and the earlier
governed output registered as derived when the subject's record holds it. The gate is then the
record's before re-verification; ``--reverify`` adds the owner's recorded re-verification of the
named keys first, the record's after. The report names the version loaded (``version``) and the
change (``change``: the artefact, the statements invalidated, the re-verified, the derived output).

``--no-load`` reads the store as it is, for a stack whose page has already loaded a scenario; the
scenario named must be the one the store holds. A load wipes the store first, as a run does.

``--register-previous DIR`` (task-0122, harness/register_change.py): after the load, the register as
it was before its update (DIR: the previous vendored tag, an instance's checkout before its pull) is
compared with the register the gate reads (``KG_REGISTER``). Every node that became deprecated or
retired and every link withdrawn marks the live statements on the keys resting on it invalidated, the
reason its decision record, and the scenario's governed output in the subject's record, registered as
derived, suspect: stale and suspect_derived findings, as a source change gives. ``register_change``
in the report says what was withdrawn, the keys and the statements; an update with no state change
writes nothing. Refused with ``--no-load``, which never writes.

Each key, stale and lapsed finding names its key's owner unit (``owner``, from the subject's
``register_map.toml`` through capture.py's ``answering_owners``, task-0043; null when no row maps
the key or several units answer for it) and the route to approval (``route``: the owner's
questionnaire, task-0009), so a block explains itself (task-0102, doc-0014 C7); the text form adds
``[owner UNIT]`` to each such line. A key finding on a declared gap also names the unit that closes
it (``closer``: the owner its declaration names, decision-0002 point 3, else the key's owners; null
when that is no unit of the register), and its route ends with the close (task-0110); the text form
adds ``; closed by UNIT``.

The JSON report (-f json) is pinned by harness/schemas/gate-report.schema.json, version 2 (the
schema's description says what changed from 1 and what was added since), and validated before it
is printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEVERITIES = ["blocker", "critical", "major", "minor", "info"]       # the contract's ladder, worst first
VERDICTS = ["PROCEED", "QUALIFIED", "BLOCKED"]                         # better to worse
LEVELS = ["absent", "declared_gap", "disputed", "invalidated", "proposed", "validated", "verified", "approved"]   # gate.ORDER, worse to better


class CannotRun(Exception):
    """The gate could not run: exit 2."""


SCHEMA_VERSION = 2
SETTLED = ("verified", "approved")   # a successor at one of these replaces a stale statement


def _finding(severity: str, kind: str, message: str, *, key=None, level=None, flags=(), ref=None, related=()) -> dict:
    return {"severity": severity, "kind": kind, "key": key, "level": level, "flags": list(flags),
            "ref": ref, "related": list(related), "message": message}


OWNED = ("key", "stale", "lapsed")   # the finding kinds that name the key's owner and the route (task-0102)


def findings(res: dict, block_levels: set[str], owners: dict[str, dict] | None = None,
             route=None, closers: dict[str, dict] | None = None) -> list[dict]:
    """The gate's result as findings on the severity ladder, worst first, then by kind, key and ref.
    With ``owners`` (key -> {unit, name}, ``capture.finding_owners``) and ``route`` ((unit, key) -> text or None),
    each key, stale and lapsed finding also names its key's owner unit and the route to approval
    (task-0102); without them the findings are version 2's as first published. With ``closers`` too
    (key -> {unit, name, gap}, ``capture.gap_closers``), a key finding on a declared gap also names the
    unit that closes it (``closer``) and its route says so (task-0110)."""
    out = []
    for key, v in res["keys"].items():
        lvl, flags = v["level"], v["flags"]
        if lvl in block_levels:
            out.append(_finding("blocker", "key", f"{key} is {lvl.replace('_', ' ')}: the task cannot proceed on it",
                                key=key, level=lvl, flags=flags))
        elif LEVELS.index(lvl) < LEVELS.index("verified"):
            out.append(_finding("major", "key", f"{key} is {lvl}, below verified: an assistant may use it only as a stated assumption",
                                key=key, level=lvl, flags=flags))
        elif flags:
            out.append(_finding("minor", "key", f"{key} is {lvl} but flagged {', '.join(flags)}", key=key, level=lvl, flags=flags))
    if res["verdict"] == "BLOCKED" and not res["blocked_keys"]:
        out.append(_finding("blocker", "task", res["why"]))
    for x in res.get("stale") or []:
        # sorted: the store collects these in its own order, and one store's answer must read the same in another (task-0070)
        settled = sorted(t["id"] for t in x.get("successors") or [] if t.get("id") and t.get("status") in SETTLED)
        ended = ", ".join(sorted(v["id"] for v in x.get("verifications") or [] if v.get("id"))) or "none"
        if settled:
            out.append(_finding("info", "stale", f"{x['id']} on {x['key']} was invalidated by {x['invalidated_by']} (verifications ended: {ended}); "
                                f"superseded by {', '.join(settled)}", key=x["key"], level="invalidated", ref=x["id"], related=settled))
        else:
            out.append(_finding("major", "stale", f"{x['id']} on {x['key']} was invalidated by {x['invalidated_by']} (verifications ended: {ended}); "
                                "no verified or approved successor replaces it", key=x["key"], level="invalidated", ref=x["id"]))
    for d in res.get("suspect_derived") or []:
        used = sorted(d.get("used_invalidated") or [])
        out.append(_finding("blocker", "suspect_derived", f"{d['id']} ({d.get('kind') or 'derived output'}) used {len(used)} statement(s) now invalidated "
                            f"({', '.join(used)}): it may not be reused as it is: regenerate it from the current statements", ref=d["id"], related=used))
    for x in res.get("lapsed") or []:
        out.append(_finding("major", "lapsed", f"{x['id']} on {x['key']} was {x['from']}; its review was current until {x['valid_until']} "
                            f"and has lapsed as of {res.get('as_of')}: it reads validated until a new review (decision-0005)",
                            key=x["key"], level="validated", ref=x["id"], related=x["verifications"]))
    for d in res.get("preload") or []:   # task-0064: form unchecked, or findings, on a document behind the keys
        what = {"unchecked": "its form was not checked before the load", "findings": "the pre-load check found findings in it",
                "held": "the pre-load check holds findings in it against a baseline"}[d["state"]]
        out.append(_finding("info", "preload", f"{d['artefact']} {d['version']}, behind {len(d['keys'])} required key(s): {what}"
                            + (f" ({d['tool']})" if d.get("tool") else "") + (f"; {d['why']}" if d.get("why") else ""),
                            ref=f"{d['artefact']}@{d['version']}", related=d["keys"]))
    if owners is not None:
        for f in out:
            if f["kind"] in OWNED:
                unit = (owners.get(f["key"]) or {}).get("unit")
                f["owner"] = unit
                f["route"] = route(unit, f["key"]) if route else None
                c = (closers or {}).get(f["key"])
                if f["kind"] == "key" and f["level"] == "declared_gap" and c is not None:
                    from capture import closing_route
                    f["closer"] = c["unit"]
                    if f["route"]:
                        f["route"] += closing_route(c["gap"], c["unit"])
    kinds = ["task", "key", "suspect_derived", "stale", "lapsed", "preload"]
    return sorted(out, key=lambda f: (SEVERITIES.index(f["severity"]), kinds.index(f["kind"]), f["key"] or "", f["ref"] or ""))


def counts(fs: list[dict]) -> dict[str, int]:
    return {s: sum(1 for f in fs if f["severity"] == s) for s in SEVERITIES}


def at_or_above(fs: list[dict], threshold: str) -> list[dict]:
    return [f for f in fs if SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold)]


def baseline_of(data: dict) -> dict:
    """{verdict, levels, suspect} from an earlier report of this command (version 1 or 2; a version-1
    report named no derived output, so it holds none suspect) or from a deterministic.json."""
    if data.get("tool") == "knowgov gate":
        sus = data.get("suspect_derived")
        return {"verdict": data["verdict"], "levels": data.get("levels", {}), "suspect": list(sus) if isinstance(sus, list) else []}
    if "D6_gate" in data:
        return {"verdict": data["D6_gate"]["verdict"], "levels": {k: v["level"] for k, v in data.get("gate_keys", {}).items()},
                "suspect": [d["id"] for d in data["D6_gate"].get("suspect_derived") or []]}
    raise CannotRun("the baseline file is neither a gate report nor a deterministic.json")


def compare(res: dict, base: dict, source: str) -> dict:
    """A regression is a verdict worse than the baseline's, a required key whose level ranks below
    the baseline's for the same key (a key the baseline did not have counts from absent), or a
    derived output suspect now that the baseline did not hold suspect."""
    worse = VERDICTS.index(res["verdict"]) > VERDICTS.index(base["verdict"])
    regressed = []
    for key, v in res["keys"].items():
        was = base["levels"].get(key)
        if was is not None and LEVELS.index(v["level"]) < LEVELS.index(was):
            regressed.append({"key": key, "level": v["level"], "baseline_level": was})
    held = set(base.get("suspect") or [])
    new_suspect = sorted(d["id"] for d in res.get("suspect_derived") or [] if d["id"] not in held)
    return {"source": source, "verdict": base["verdict"], "regression": worse or bool(regressed) or bool(new_suspect),
            "worse_verdict": worse, "regressed_keys": regressed, "new_suspect": new_suspect}


def superseded_map(res: dict) -> dict[str, list[str]]:
    from gate import superseded_map as m
    return m(res)


def report(res: dict, *, subject: str, scenario: str, task: str, store: str, loaded: bool,
           block_levels: set[str], threshold: str, baseline: dict | None,
           version: str | None = None, change: dict | None = None, owners: dict[str, dict] | None = None,
           route_task: str | None = None, route_keys=None, closers: dict[str, dict] | None = None,
           register_change: dict | None = None) -> dict:
    """``route_task`` is the task class whose questionnaire a finding's route names (``task`` by default;
    the MCP server's agent-chosen key set, task ``keys``, names the class it was resolved under), and
    ``route_keys`` the keys that questionnaire covers (None: every key): a key outside them has no route."""
    from capture import questionnaire_route
    rt = route_task or task

    def route(unit, key):
        return questionnaire_route(subject, scenario, rt, unit) if route_keys is None or key in route_keys else None
    fs = findings(res, block_levels, owners, route, closers)
    fail = baseline["regression"] if baseline is not None else bool(at_or_above(fs, threshold))
    return {"schema_version": SCHEMA_VERSION, "tool": "knowgov gate", "subject": subject, "scenario": scenario, "task": task,
            "store": store, "loaded": loaded, "version": version, "change": change, "verdict": res["verdict"], "why": res["why"], "threshold": threshold,
            "findings": fs, "counts": counts(fs),
            "keys": {"total": len(res["keys"]), "below_verified": len(res["below_verified"]), "flagged": len(res["flagged"])},
            "conflicts": len(res.get("conflicts") or []),
            "stale": [x["id"] for x in res.get("stale") or []],                    # the statements, by id (a count in version 1)
            "superseded_by": superseded_map(res),                                     # task-0071: the stale ones a settled successor supersedes
            "suspect_derived": [d["id"] for d in res.get("suspect_derived") or []],  # the derived outputs, by id (a count in version 1)
            "as_of": res.get("as_of"), "lapsed": [x["id"] for x in res.get("lapsed") or []],   # decision-0005, added in version 2
            "levels": {k: v["level"] for k, v in res["keys"].items()},   # what a later run's --baseline FILE compares with
            "baseline": baseline, "exit_code": 1 if fail else 0,
            **({"register_change": register_change} if register_change is not None else {})}   # task-0122, additive


def render(rep: dict) -> str:
    out = [f"{rep['subject']} {rep['scenario']} {rep['task']}: {rep['verdict']} — {rep['why']}" + (f" (as of {rep['as_of']})" if rep.get("as_of") else "")]
    ch = rep.get("change")
    if ch:
        out.append(f"  version  {ch['version']} of {ch['artefact']}: {len(ch['invalidated'])} statement(s) invalidated ({', '.join(ch['invalidated']) or 'none'}); "
                   + (f"re-verified {', '.join(ch['reverified_statements']) or 'none'}" if ch["reverified"] else "before re-verification")
                   + (f"; derived {ch['derived']} registered" if ch["derived"] else ""))
    rc = rep.get("register_change")
    if rc is not None:   # task-0122
        tag = lambda x: x["tag"] or x["commit"][:7]  # noqa: E731
        out.append(f"  register {tag(rc['from'])} -> {tag(rc['to'])}: " + (", ".join(
            [f"{n['id']} {n['to'] or 'gone'}" for n in rc["nodes"]] + [f"{ln['id']} {ln['to'] or 'gone'}" for ln in rc["links"]]) or "nothing withdrawn")
                   + f"; {len(rc['keys'])} key(s) resting on it, {len(rc['invalidated'])} statement(s) invalidated"
                   + (f"; derived {rc['derived']} registered" if rc["derived"] else ""))
    for f in rep["findings"]:
        out.append(f"  {f['severity']:8s} {f['message']}" + (f" [owner {f['owner'] or 'none in the register map'}"
                                                         + (f"; closed by {f['closer'] or 'no unit of the register'}" if "closer" in f else "") + "]"
                                                         if "owner" in f else ""))
    c = rep["counts"]
    out.append("findings: " + ", ".join(f"{c[s]} {s}" for s in SEVERITIES if c[s]) if any(c.values()) else "findings: none")
    b = rep["baseline"]
    if b is not None:
        out.append(f"baseline ({b['source']}): {b['verdict']}; " + ("REGRESSION" if b["regression"] else "no regression")
                   + ("; the verdict is worse" if b["worse_verdict"] else "")
                   + "".join(f"; {r['key']} {r['baseline_level']} -> {r['level']}" for r in b["regressed_keys"])
                   + "".join(f"; {d} newly suspect" for d in b["new_suspect"]))
        out.append(f"exit {rep['exit_code']}: " + ("a regression against the baseline" if rep["exit_code"] else "no regression against the baseline"))
    else:
        out.append(f"exit {rep['exit_code']}: " + (f"a finding at or above {rep['threshold']}" if rep["exit_code"] else f"no finding at or above {rep['threshold']}"))
    return "\n".join(out)


def _baseline(arg: str, subject, scenario: str, task: str) -> tuple[dict, str] | None:
    if arg == "none":
        return None
    if arg == "record":
        if task != "codegen":
            raise CannotRun(f"the record's gate is the codegen task, not {task!r}")
        rel = subject.scenario(scenario).get("deterministic_record") or scenario
        p = subject.record_dir / rel / "deterministic.json"
        if not p.exists():
            raise CannotRun(f"no record for {scenario}: {p} does not exist")
        return baseline_of(json.loads(p.read_text(encoding="utf-8"))), "record"
    p = Path(arg)
    if not p.exists():
        raise CannotRun(f"no baseline at {p}")
    return baseline_of(json.loads(p.read_text(encoding="utf-8"))), str(p)


def run(args) -> dict:
    """Load, resolve and report; raises CannotRun for what exit 2 covers."""
    if args.subject:
        os.environ["KG_SUBJECT"] = str(Path(args.subject).resolve())
    sys.path.insert(0, str(HERE))
    try:
        from subject import SUBJECT
        from tasks import TASKS
    except Exception as e:  # noqa: BLE001 — a subject that does not load is a cannot-run
        raise CannotRun(f"the subject does not load: {e}") from e
    scenario = args.scenario or (SUBJECT.order[0] if SUBJECT.order else "")
    if scenario not in SUBJECT.scenarios:
        raise CannotRun(f"{SUBJECT.id}: no scenario {scenario!r}; the subject declares {SUBJECT.order or 'none'}")
    if args.task not in TASKS:
        raise CannotRun(f"{SUBJECT.id}: no task {args.task!r}; the subject declares {sorted(TASKS) or 'none'}")
    if args.reverify and args.stage != 2:
        raise CannotRun("--reverify is a step of stage 2: add --stage 2")
    if args.no_load and args.stage != 1:
        raise CannotRun("--stage 2 loads the change; --no-load reads the store as it is: drop one")
    cfg2 = SUBJECT.scenario(scenario).get("stage2") if args.stage == 2 else None
    if args.stage == 2 and not cfg2:
        raise CannotRun(f"{SUBJECT.id}: {scenario} has no later version (no [scenario.stage2])")
    base = _baseline(args.baseline, SUBJECT, scenario, args.task)
    import cadence
    try:
        on = cadence.as_of(args.as_of).isoformat()
    except ValueError as e:
        raise CannotRun(f"--as-of: {e}") from e
    reg_change = previous = None
    if args.register_previous:
        if args.no_load:
            raise CannotRun("--register-previous marks statements stale on a load; --no-load reads the store as it is: drop one")
        import register_change as rc
        previous = Path(args.register_previous)
        try:
            reg_change = rc.diff(previous, rc.ri.register_root())
        except Exception as e:  # noqa: BLE001 — a register that does not load is a cannot-run
            raise CannotRun(f"--register-previous: the registers do not compare: {type(e).__name__}: {e}") from e
    from store import open_store
    try:
        st = open_store(instance=SUBJECT.id, access="read" if args.no_load else "write")   # task-0141.02
    except Exception as e:  # noqa: BLE001
        raise CannotRun(f"the store cannot be opened: {e}") from e
    change = None
    try:
        if args.no_load:
            acts = st.extraction_activities()   # act:extract:<scenario>:<version>, as the page reads it
            loaded = acts[0].split(":")[2] if acts else None
            if loaded != scenario:
                raise CannotRun(f"the store holds {loaded or 'no scenario'}, not {scenario!r}; load it, or drop --no-load")
            version = held_version(st)
        else:
            _load(st, scenario)
            version = "v1"
            if cfg2:
                change = _change(st, SUBJECT, scenario, cfg2, args.reverify)
                version = change["version"]
            if reg_change is not None:
                reg_change = _register_change(st, SUBJECT, scenario, reg_change, previous)
        report = evaluate(st, subject=SUBJECT.id, scenario=scenario, task=args.task, spec=TASKS[args.task],
                          threshold=args.fail_on, baseline=base, loaded=not args.no_load, version=version, change=change,
                          as_of=on, register_change=reg_change)
        if not args.no_load:
            st.commit()   # the load and its change, published once the report is made; a failure publishes nothing
        return report
    except CannotRun:
        raise
    except Exception as e:  # noqa: BLE001 — an unreachable store fails here, on the first statement
        raise CannotRun(f"the store did not answer: {type(e).__name__}: {e}") from e
    finally:
        try:
            st.close()
        except Exception:  # noqa: BLE001
            pass


def evaluate(st, *, subject: str, scenario: str, task: str, spec: dict, threshold: str,
             baseline: tuple[dict, str] | None, loaded: bool, version: str | None = None,
             change: dict | None = None, as_of="today", owners: dict[str, dict] | None = None,
             route_task: str | None = None, closers: dict[str, dict] | None = None,
             register_change: dict | None = None) -> dict:
    """Resolve ``spec`` on the store as it stands, as of ``as_of`` (today by default; harness/cadence.py), and build the report. The command calls this
    after its load (and stage 2's change, if any); the MCP server (harness/mcp_server.py) calls it
    on a store it only reads, so one input gives one report whichever way it was asked. ``owners``
    defaults to the loaded subject's (``capture.finding_owners``) when ``subject`` is its id;
    ``route_task``, the class an agent-chosen key set was resolved under, names its questionnaire."""
    from gate import resolve_spec
    res = resolve_spec(st, task, spec, as_of)
    from subject import SUBJECT
    if SUBJECT.id == subject:
        if owners is None:
            from capture import finding_owners
            owners = finding_owners(SUBJECT)
        if closers is None:   # task-0110: the unit each declared gap's declaration names closes it
            from capture import gap_closers
            closers = gap_closers(SUBJECT, {k: v.get("declared_gaps") or [] for k, v in res["keys"].items()})
    return report(res, subject=subject, scenario=scenario, task=task, store=st.name, loaded=loaded,
                  block_levels=set(spec["block_levels"]), threshold=threshold,
                  baseline=compare(res, *baseline) if baseline else None, version=version, change=change, owners=owners,
                  route_task=route_task, route_keys=_route_keys(route_task) if route_task and route_task != task else None,
                  closers=closers, register_change=register_change)


def _route_keys(task: str) -> set[str] | None:
    """The keys the questionnaire of task class ``task`` covers; None when the subject declares no such class."""
    from tasks import TASKS
    return set(TASKS[task]["keys"]) if task in TASKS else None


def held_version(st) -> str | None:
    """The version of the last extraction the store holds (act:extract:<scenario>:<version>), as
    ``--no-load`` reports it."""
    acts = st.extraction_activities()
    return acts[-1].split(":")[3] if acts else None


def _change(st, subject, scenario: str, cfg2: dict, reverified: bool) -> dict:
    """Stage 2 on a store holding stage 1, as harness/run.py's ``stage2`` does it (harness/change.py):
    the derived output is the subject's record's (``[scenario.stage2.derived]``), registered with the
    statements the stage-1 codegen gate served, as run.py registers it from its runs folder."""
    from change import apply_change, reverify, version_of
    from gate import resolve
    from load import pristine_values
    derived = cfg2.get("derived", {})
    code_path = subject.record_dir / derived.get("from_scenario", scenario) / derived.get("file", "run1_G.py")
    code = code_path.read_text(encoding="utf-8") if derived and code_path.exists() else None
    ids = [a["id"] for v in resolve(st, "codegen")["keys"].values() for a in v["assertions"]] if code else []
    ch = apply_change(scenario, cfg2, st, code, ids)
    rever = reverify(scenario, cfg2, pristine_values(), st, ch["kit2"]) if reverified else []
    return {"artefact": cfg2["artefact"], "version": version_of(cfg2),
            "invalidated": sorted(x["id"] for x in ch["D3_stale"]["invalidated"]),
            "reverified": reverified, "reverified_statements": sorted(rever), "derived": ch["derived"]}


def _register_change(st, subject, scenario: str, change: dict, previous: Path) -> dict:
    """A register change on a store holding the scenario (task-0122, harness/register_change.py): the
    scenario's governed output in the subject's record (the stage-2 ``derived`` table of any scenario
    that names this one ``from_scenario``) is registered as derived with the statements the codegen
    gate served, as stage 2 registers it; then the keys resting on what the change withdrew are
    invalidated, each by its reason. A change that withdrew nothing writes nothing."""
    import register_change as rc
    landed = rc.resting(change, subject.register_map(), previous, rc.ri.register_root())
    did = None
    if landed:
        from gate import resolve
        from kitio import sha256
        from tasks import TASKS
        for sid in subject.order:
            d = (subject.scenario(sid).get("stage2") or {}).get("derived") or {}
            path = subject.record_dir / d.get("from_scenario", "") / d.get("file", "run1_G.py")
            if d.get("from_scenario") == scenario and path.exists():
                did = d.get("id", f"derived:{scenario}")
                ids = [a["id"] for v in resolve(st, "codegen")["keys"].values() for a in v["assertions"]] if "codegen" in TASKS else []
                st.register_derived(did, d.get("kind", "artefact"), sha256(path.read_text(encoding="utf-8")), ids)
                break
    done = rc.apply(st, landed)
    return {"from": change["from"], "to": change["to"], "nodes": change["nodes"], "links": change["links"],
            "keys": [{"key": k["key"], "owner": k["owner"], "reasons": k["reasons"],
                      "causes": sorted({c.get("node") or c.get("link") for c in k["causes"]})} for k in landed],
            "invalidated": [x["id"] for x in done["invalidated"]], "derived": did}


def _load(st, scenario: str) -> None:
    """What a deterministic run does before its gate (harness/run.py ``deterministic``), stage 1."""
    from kitio import kit_for
    from load import load_captures, load_inferred, load_reviews, load_scenario, load_verifications, pristine_values
    from plant import INFERRED
    from rules import run_all
    from subject import SUBJECT
    cfg = SUBJECT.scenario(scenario)
    st.wipe()
    st.apply_constraints()
    kit = kit_for(scenario)
    load_scenario(st, scenario, kit, activity_note=f"{scenario}: extraction for the gate command")
    if cfg.get("verifications", True):
        load_verifications(st, scenario, pristine_values(), kit)
    if cfg.get("inferred") and INFERRED:
        load_inferred(st, scenario, INFERRED)
    load_captures(st, scenario)
    run_all(st, scenario)
    load_reviews(st, scenario)   # a person's rulings, after the rules (task-0037)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gate_cli.py", description="Resolve a task's required knowledge and exit 0, 1 or 2.")
    ap.add_argument("--subject", help="the subject root (default: KG_SUBJECT, else subjects/cargo_quote)")
    ap.add_argument("--scenario", help="the scenario to load (default: the subject's first)")
    ap.add_argument("--task", default="codegen", help="the task class (default: codegen)")
    ap.add_argument("--fail-on", choices=SEVERITIES, default="blocker", help="the severity at or above which the gate exits 1 (default: blocker)")
    ap.add_argument("--baseline", default="none", help="none (default), record, or the path of an earlier report or deterministic.json: exit 1 only on a regression")
    ap.add_argument("--stage", type=int, choices=[1, 2], default=1,
                    help="1 (default): the scenario as first loaded; 2: then its later version, the subject's [scenario.stage2] change, before re-verification")
    ap.add_argument("--reverify", action="store_true", help="with --stage 2: the owner's recorded re-verification of the named keys before the gate")
    ap.add_argument("--no-load", action="store_true", help="read the store as it is instead of loading the scenario first")
    ap.add_argument("--register-previous", metavar="DIR",
                    help="the register before its update (task-0122): what the update withdrew from the register (KG_REGISTER) marks the statements resting on it stale")
    ap.add_argument("--as-of", default="today", metavar="DATE",
                    help="the date review currency is read on (decision-0005): today (default), record (the subject's pinned record date) or YYYY-MM-DD")
    ap.add_argument("-f", "--format", choices=["text", "json"], default="text")
    ap.add_argument("-o", "--output", help="also write the JSON report to this file")
    args = ap.parse_args(argv)
    try:
        rep = run(args)
    except CannotRun as e:
        print(f"gate: cannot run: {e}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(HERE))
    from schema_check import load as load_schema, validate
    errs = validate(rep, load_schema("gate-report"))
    if errs:   # the report does not match its own schema: a defect here, never a pass
        print("gate: cannot run: the report does not match its schema: " + "; ".join(errs[:5]), file=sys.stderr)
        return 2
    if args.output:
        Path(args.output).write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=1) if args.format == "json" else render(rep))
    return rep["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
