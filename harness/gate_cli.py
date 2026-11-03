"""The gate as a command (task-0007), under the programme's gate contract (fdurieux.github.io).

    python harness/gate_cli.py [--subject DIR] [--scenario ID] [--task NAME]
                               [--fail-on blocker|critical|major|minor|info]
                               [--baseline none|record|FILE] [--no-load] [-f text|json] [-o FILE]

It loads the scenario of a subject into the store (KG_STORE: neo4j by default, rdflib in memory),
runs the rules, resolves the task's required keys through the same gate the arms read
(harness/gate.py), and turns the result into findings on the contract's severity ladder:

    blocker   a required key at one of the task's block levels (absent, a declared gap, disputed,
              invalidated), or the task as a whole when too many keys are below verified;
              a registered derived output (generated code) that used a statement now invalidated:
              it may not be reused as it is, whatever the verdict on the keys (task-0048)
    major     a required key below verified (proposed or validated); a stale statement on a
              required key that no verified or approved successor replaces (task-0048)
    minor     a verified or approved key carrying a flag (ambiguous, inferred, assumed)
    info      a stale statement on a required key that a verified or approved successor
              replaces: the record of the change, and the verifications it ended (task-0048)

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

``--no-load`` reads the store as it is, for a stack whose page has already loaded a scenario; the
scenario named must be the one the store holds. A load wipes the store first, as a run does.

The JSON report (-f json) is pinned by harness/schemas/gate-report.schema.json, version 2 (the
schema's description says what changed from 1), and validated before it is printed.
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


def findings(res: dict, block_levels: set[str]) -> list[dict]:
    """The gate's result as findings on the severity ladder, worst first, then by kind, key and ref."""
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
        settled = [t["id"] for t in x.get("successors") or [] if t.get("id") and t.get("status") in SETTLED]
        ended = ", ".join(v["id"] for v in x.get("verifications") or [] if v.get("id")) or "none"
        if settled:
            out.append(_finding("info", "stale", f"{x['id']} on {x['key']} was invalidated by {x['invalidated_by']} (verifications ended: {ended}); "
                                f"replaced by {', '.join(settled)}", key=x["key"], level="invalidated", ref=x["id"], related=settled))
        else:
            out.append(_finding("major", "stale", f"{x['id']} on {x['key']} was invalidated by {x['invalidated_by']} (verifications ended: {ended}); "
                                "no verified or approved successor replaces it", key=x["key"], level="invalidated", ref=x["id"]))
    for d in res.get("suspect_derived") or []:
        used = list(d.get("used_invalidated") or [])
        out.append(_finding("blocker", "suspect_derived", f"{d['id']} ({d.get('kind') or 'derived output'}) used {len(used)} statement(s) now invalidated "
                            f"({', '.join(used)}): it may not be reused as it is: regenerate it from the current statements", ref=d["id"], related=used))
    kinds = ["task", "key", "suspect_derived", "stale"]
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


def report(res: dict, *, subject: str, scenario: str, task: str, store: str, loaded: bool,
           block_levels: set[str], threshold: str, baseline: dict | None) -> dict:
    fs = findings(res, block_levels)
    fail = baseline["regression"] if baseline is not None else bool(at_or_above(fs, threshold))
    return {"schema_version": SCHEMA_VERSION, "tool": "knowgov gate", "subject": subject, "scenario": scenario, "task": task,
            "store": store, "loaded": loaded, "verdict": res["verdict"], "why": res["why"], "threshold": threshold,
            "findings": fs, "counts": counts(fs),
            "keys": {"total": len(res["keys"]), "below_verified": len(res["below_verified"]), "flagged": len(res["flagged"])},
            "conflicts": len(res.get("conflicts") or []),
            "stale": [x["id"] for x in res.get("stale") or []],                    # the statements, by id (a count in version 1)
            "suspect_derived": [d["id"] for d in res.get("suspect_derived") or []],  # the derived outputs, by id (a count in version 1)
            "levels": {k: v["level"] for k, v in res["keys"].items()},   # what a later run's --baseline FILE compares with
            "baseline": baseline, "exit_code": 1 if fail else 0}


def render(rep: dict) -> str:
    out = [f"{rep['subject']} {rep['scenario']} {rep['task']}: {rep['verdict']} — {rep['why']}"]
    for f in rep["findings"]:
        out.append(f"  {f['severity']:8s} {f['message']}")
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
    base = _baseline(args.baseline, SUBJECT, scenario, args.task)
    from store import open_store
    try:
        st = open_store(instance=SUBJECT.id)
    except Exception as e:  # noqa: BLE001
        raise CannotRun(f"the store cannot be opened: {e}") from e
    try:
        if args.no_load:
            acts = st.extraction_activities()   # act:extract:<scenario>:<version>, as the page reads it
            loaded = acts[0].split(":")[2] if acts else None
            if loaded != scenario:
                raise CannotRun(f"the store holds {loaded or 'no scenario'}, not {scenario!r}; load it, or drop --no-load")
        else:
            _load(st, scenario)
        return evaluate(st, subject=SUBJECT.id, scenario=scenario, task=args.task, spec=TASKS[args.task],
                        threshold=args.fail_on, baseline=base, loaded=not args.no_load)
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
             baseline: tuple[dict, str] | None, loaded: bool) -> dict:
    """Resolve ``spec`` on the store as it stands and build the report. The command calls this
    after its load; the MCP server (harness/mcp_server.py) calls it on a store it only reads, so
    one input gives one report whichever way it was asked."""
    from gate import resolve_spec
    res = resolve_spec(st, task, spec)
    return report(res, subject=subject, scenario=scenario, task=task, store=st.name, loaded=loaded,
                  block_levels=set(spec["block_levels"]), threshold=threshold,
                  baseline=compare(res, *baseline) if baseline else None)


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
    ap.add_argument("--no-load", action="store_true", help="read the store as it is instead of loading the scenario first")
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
