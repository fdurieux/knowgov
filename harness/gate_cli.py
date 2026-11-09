"""The gate as a command (task-0007), under the programme's gate contract (fdurieux.github.io).

    python harness/gate_cli.py [--subject DIR] [--scenario ID] [--task NAME]
                               [--fail-on blocker|critical|major|minor|info]
                               [--baseline none|record|FILE] [--stage 1|2 [--reverify]] [--no-load | --publish]
                               [--as-of today|record|YYYY-MM-DD]
                               [-f text|json] [-o FILE]

It loads the scenario of a subject into a store of its own (``store.scratch_store``: an rdflib graph
in this process's memory, decision-0017), runs the rules, resolves the task's required keys through the same gate the arms read
(harness/gate.py), and turns the result into findings on the contract's severity ladder:

    blocker   a required key at one of the task's block levels (absent, a declared gap, disputed,
              invalidated), or the task as a whole when too many keys are below verified;
              a registered derived output (generated code) that used a statement now invalidated:
              it may not be reused as it is, whatever the verdict on the keys (task-0048)
    major     a required key below verified (proposed or validated); under a class that requires
              approved (``require_approved``, task-0215), a key verified but not approved (``intended``);
              a stale statement on a
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
    2  the gate could not run: no such subject, scenario or task, an unreachable store, no baseline,
       or a baseline report of another run, a newer version or an invalid shape

With a baseline the gate ratchets instead: exit 1 only on a regression, a verdict worse than the
baseline's, a required key at a lower level than the baseline's, or a derived output suspect that
the baseline did not hold suspect. ``--baseline record`` is the
subject's record for the same scenario (its deterministic run; the record's gate is the codegen
task, read at stage 1: ``--stage 2 --baseline record`` exits 2, since the record keeps stage 2's
verdicts, not its keys' levels, task-0209); ``--baseline FILE`` is an earlier report of this command
(at stage 2, a stage-2 report) or a deterministic.json. A report is held to that before it is compared
(task-0258): one of another subject, scenario, task class or stage, one of a schema version above this
command's (decision-0023), and one that is not valid against the gate-report schema of its own version
(versions 1 and 2 frozen beside the current one), each exit 2 naming the file and what differs. The gate
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

Which store (decision-0017, task-0184). By default the load goes into the process's own scratch store
and nothing is published: the store ``KG_STORE`` names (on a stack, the Neo4j the page, the runs and
the MCP servers read) keeps the scenario it holds, so the command is safe to run by hand anywhere. The
report's ``store`` names the adapter the gate computed on (``rdflib``), ``published`` is false. Without
rdflib the command cannot run (exit 2) and names the install.

``--publish`` loads into the store ``KG_STORE`` names instead, wiping it first as a run does, and
publishes the load once the report is made, for a pipeline whose later step reads the store (a trace
check, the MCP server, ``--no-load``). The Neo4j load-memory forecast (task-0176) is checked on this
path only; ``published`` is true. A ``--no-load`` report carries no ``published``: it loaded nothing,
and it stays the report the MCP server's ``gate_verdict`` gives. The report is otherwise the default's: the same load, the same
verdict, findings, levels and exit code (``tools/check_round_trip.py --chain`` holds the adapters equal).

``--no-load`` reads the store ``KG_STORE`` names as it is, for a stack whose page has already loaded a
scenario; the scenario named must be the one the store holds. Refused with ``--publish``.

``--register-previous DIR`` (task-0122, harness/register_change.py): after the load, the register as
it was before its update (DIR: the previous vendored tag, an instance's checkout before its pull) is
compared with the register the gate reads (``KG_REGISTER``), on the store the load went to. Every node that became deprecated or
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

The JSON report (-f json) is pinned by harness/schemas/gate-report.schema.json, version 3 (the
schema's description says what changed from 1 and 2 and what was added since), and validated before
it is printed. Version 3 (task-0237, decision-0029) names what the gate decided on: ``task_profile``,
the sha256 of the task table read; ``register``, its tag and commit; ``knowgov``, the build.
"""
from __future__ import annotations

if __name__ == "__main__":   # task-0200: a failure while loading (a pin not installed) is exit 2, its cause in one line
    import cli_exit
    cli_exit.guard("gate")

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


SCHEMA_VERSION = 3   # task-0237, decision-0029: task_profile, register and knowgov, what the gate decided on
SETTLED = ("verified", "approved")   # a successor at one of these replaces a stale statement


def _finding(severity: str, kind: str, message: str, *, key=None, level=None, flags=(), ref=None, related=()) -> dict:
    return {"severity": severity, "kind": kind, "key": key, "level": level, "flags": list(flags),
            "ref": ref, "related": list(related), "message": message}


OWNED = ("key", "intended", "stale", "lapsed", "act")   # the finding kinds that name the key's owner and the route (task-0102, task-0199)
# task-0199: an act whose statement changed is major (the owner must rule again; the key's own finding carries
# what it now reads), one read under the 0.9.0 rule or a refused file info (nothing it ruled on moved)
ACT_SEVERITY = {"changed": "major", "gone": "major", "ambiguous": "major", "unbound": "info", "refused": "info"}


def _short(sha: str) -> str:
    return (sha or "")[:12] or "none"


def attestation_findings(rows: list[dict], owners: dict | None, route) -> list[dict]:
    """decision-0019 (task-0221): a declaration that lists no Version is the read rule's, at info; each artefact a
    bound declaration does not attest, behind the task's keys, is major (its authored statements read proposed and
    nothing in it is approved by construction, so the keys behind it fall below verified, and the attester or the
    keys' owner has to act). It names the keys' owner and route (``capture.routing``) when they share one."""
    out = []
    for r in rows:
        if not r["bound"]:
            out.append(_finding("info", "attestation", f"[verification] {r['declaration']} lists no Version: it attests what the documents "
                                "hold at each load (decision-0009 (a), the read rule); list the digest of each Version it attests "
                                "(decision-0019) to bind it", ref=f"attest:{r['declaration']}"))
    merged: dict[str, dict] = {}
    for r in rows:
        for u in r["unattested"] if r["bound"] else []:
            m = merged.setdefault(u["artefact"], {**u, "declarations": [], "attester": r["attester"]})
            m["declarations"].append(r["declaration"])
    for art, u in sorted(merged.items()):
        decls = " and ".join(u["declarations"])
        digests = ", ".join(x[:12] for x in u["parts"]) if u["parts"] else u["sha256"][:12]
        f = _finding("major", "attestation", f"{art} (sha256 {digests}), behind {len(u['keys'])} required key(s), is not attested: "
                     f"[verification] {decls} list(s) no digest of this Version, so its authored statements read proposed and "
                     "nothing in it is approved by construction (decision-0019)", ref=art, related=u["keys"])
        if owners is not None:
            units = {(owners.get(k) or {}).get("unit") for k in u["keys"]}
            unit = units.pop() if len(units) == 1 else None
            f["owner"] = unit
            how = (f"{u['attester'] or 'the attester'} reads the document and lists sha256 {u['sha256']} under [verification] "
                   f"{decls} versions in subject.toml (decision-0019)")
            q = route(unit, u["keys"][0]) if route and unit else None
            f["route"] = how + (f"; or {q}" if q else "")
        out.append(f)
    return out


def act_finding(a: dict) -> dict:
    """One act the load did not apply as written (``gate.acts_not_applied``) as a finding of kind ``act``."""
    who = f"{a['review']}: {a['act']} {a['n']} by {a['by']} on {a['on']}" if a["act"] != "review" else f"{a['review']} by {a['by']} on {a['on']}"
    was = f"{a['from_value']!r} (sha256 {_short(a['from_sha256'])})"
    now = "; ".join(f"{t['id']} {t['value']!r} (sha256 {_short(t['sha256'])})" for t in a["to"])
    why = a["why"]
    if why == "refused":
        msg = f"{who} was refused whole and applied nothing: " + "; ".join(a["reasons"])
    elif why == "unbound":
        msg = (f"{who} ({a['outcome']} {a['statement']}) is bound by id only: the file records no value or digest "
               "(written before 0.9.0), so it was applied to what the id names now" + (f", {now}" if now else "")
               + "; a new review binds it to content")
    elif a["act"] == "resolve":   # task-0216: a lint gap's resolution whose finding is no longer the one it resolved
        msg = (f"{who} ({a['outcome']} of {a['statement']}) was not applied: " + ("the finding is gone: the document's version no "
               "longer has it (a slip mended), so there is nothing to resolve" if why == "gone" else
               "the finding's text changed since the resolution") + ("" if why == "gone" else "; its owner resolves it again"))
    elif a["act"] == "close":
        msg = (f"{who} (close of {a['statement']}) was not applied: " + ("the gap is no longer declared open" if why == "gone"
               else "the declaration's text changed since the close") + "; its owner closes it again or the gap stands")
    else:
        msg = (f"{who} ({a['outcome']} {a['statement']} on {a['key']}) was not applied: it ruled on {was}, and "
               + {"changed": f"the statement now reads {now}", "gone": "no statement of it is extracted any more",
                  "ambiguous": "several statements hold that content and none is the one it names"}[why]
               + "; its owner rules again")
    sev = "info" if a["act"] == "resolve" and why == "gone" else ACT_SEVERITY[why]
    f = _finding(sev, "act", msg, key=a["key"] or None, ref=a["statement"] or a["review"],
                 related=[t["id"] for t in a["to"]])
    f["act"] = {"review": a["review"], "act": a["act"], "n": a["n"], "outcome": a["outcome"], "by": a["by"], "on": a["on"],
                "why": why, "from": {"value": a["from_value"], "sha256": a["from_sha256"]}, "to": a["to"], "reasons": a["reasons"]}
    return f


LINT_SEVERITY = {"blocker": "major", "critical": "major", "major": "major", "minor": "minor", "info": "info"}


def lint_finding(g: dict) -> dict:
    """One lint gap behind the keys (``gate.lint_behind``, task-0216) as a finding of kind ``lint``: the linter's
    severity, at most major (a document's form never blocks the knowledge on its own); info when the baseline
    holds it or a review resolved it as a choice or an exception; ``open`` keeps it at its severity, said so."""
    where = f"{g['file'] or g['artefact']}:{g['line']}"
    msg = f"{g['tool']} {g['rule']} ({g['severity']}) at {where}, version {g['version']}: {g['message']}"
    res = g.get("resolution")
    if g.get("held"):
        sev, msg = "info", msg + "; held by the pre-load baseline, not raised"
    elif res in ("choice", "exception"):
        sev, msg = "info", msg + (f"; resolved as {'a choice' if res == 'choice' else 'an exception'} by {g.get('resolved_by')} on "
                                  f"{g.get('resolved_on')} ({g.get('record')})")
    else:
        sev = LINT_SEVERITY.get(g["severity"], "minor")
        msg += (f"; left open by {g.get('resolved_by')} on {g.get('resolved_on')} ({g.get('record')})" if res == "open"
                else "; its owner resolves it: a slip (a new version), a choice (a decision record and an approval), an exception "
                     "(an elicited statement) or open")
    f = _finding(sev, "lint", msg, ref=g["id"], related=g["keys"])
    f["lint"] = {"artefact": g["artefact"], "version": g["version"], "file": g["file"], "tool": g["tool"], "tool_version": g["tool_version"],
                 "rule": g["rule"], "severity": g["severity"], "line": g["line"], "held": bool(g.get("held")),
                 "resolution": res or None, "resolved_by": g.get("resolved_by") or None, "resolved_on": g.get("resolved_on") or None,
                 "record": g.get("record") or None}
    return f


def suspect_finding(d: dict, scope: dict | None) -> dict:
    """One suspect derived output as a finding: a blocker, or ``info`` when ``scope`` says its invalidated or changed
    statements sit on none of this task's keys (task-0282, decision-0033 choice 8): listed, naming the keys it rests
    on, and the class whose keys it rests on blocks on it. ``scope`` None (not read) blocks, as before."""
    used, changed = sorted(d.get("used_invalidated") or []), sorted(d.get("used_changed") or [])
    why = f"used {len(used)} statement(s) now invalidated ({', '.join(used)})" if used else ""
    if changed:   # task-0199: a statement changed under its id since trace registered the output
        why += ("; and " if why else "used ") + f"{len(changed)} statement(s) whose value or digest changed since it was built ({', '.join(changed)})"
    what = f"{d['id']} ({d.get('kind') or 'derived output'}) {why}"
    if scope is not None and not scope["on_task"]:
        return _finding("info", "suspect_derived", f"{what}; they sit on {', '.join(scope['keys']) or 'no key held'}, none of this "
                        "task's keys: listed, not blocking this task", ref=d["id"], related=used + changed)
    return _finding("blocker", "suspect_derived", f"{what}: it may not be reused as it is: regenerate it from the current statements",
                    ref=d["id"], related=used + changed)


def findings(res: dict, block_levels: set[str], owners: dict[str, dict] | None = None,
             route=None, closers: dict[str, dict] | None = None, suspect_scope: dict[str, dict] | None = None) -> list[dict]:
    """The gate's result as findings on the severity ladder, worst first, then by kind, key and ref.
    With ``owners`` (key -> {unit, name}, ``capture.finding_owners``) and ``route`` ((unit, key) -> text or None),
    each key, stale and lapsed finding also names its key's owner unit and the route to approval
    (task-0102); without them the findings are version 2's as first published. With ``closers`` too
    (key -> {unit, name, gap}, ``capture.gap_closers``), a key finding on a declared gap also names the
    unit that closes it (``closer``) and its route says so (task-0110)."""
    import cadence
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
    for key in res.get("unintended") or []:   # task-0215: the intended bar, decision-0018 point 4
        v = res["keys"][key]
        out.append(_finding("major", "intended", f"{key} is verified but not approved, and the task class requires approved: "
                            "a behaviour shown to hold is not yet one a person intends; its owner approves it or rules otherwise",
                            key=key, level=v["level"], flags=v["flags"]))
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
    out += [suspect_finding(d, (suspect_scope or {}).get(d["id"])) for d in res.get("suspect_derived") or []]
    for x in res.get("lapsed") or []:
        out.append(_finding("major", "lapsed", f"{x['id']} on {x['key']} {cadence.describe(x, res.get('as_of'))}",
                            key=x["key"], level=x.get("to", "validated"), ref=x["id"], related=x["verifications"]))
    for d in res.get("preload") or []:   # task-0064: form unchecked, or findings, on a document behind the keys
        what = {"unchecked": "its form was not checked before the load", "findings": "the pre-load check found findings in it",
                "held": "the pre-load check holds findings in it against a baseline"}[d["state"]]
        out.append(_finding("info", "preload", f"{d['artefact']} {d['version']}, behind {len(d['keys'])} required key(s): {what}"
                            + (f" ({d['tool']})" if d.get("tool") else "") + (f"; {d['why']}" if d.get("why") else ""),
                            ref=f"{d['artefact']}@{d['version']}", related=d["keys"]))
    out += [act_finding(a) for a in res.get("acts") or []]
    out += attestation_findings(res.get("attestation") or [], owners, route)
    out += [lint_finding(g) for g in res.get("lint") or []]   # task-0216
    if owners is not None:
        for f in out:
            if f["kind"] == "lint":   # the document's owning unit: the one unit capture.routing gives every key behind it
                by_unit: dict = {}
                for k in f["related"]:
                    by_unit.setdefault((owners.get(k) or {}).get("unit"), k)
                f["owner"] = next(iter(by_unit)) if len(by_unit) == 1 else None
                if not route or not f["related"]:
                    f["route"] = None
                elif len(by_unit) == 1:
                    f["route"] = route(f["owner"], f["related"][0])
                else:   # several units own the document's keys: each one's route, any of them resolves it
                    named = sorted(u for u in by_unit if u)
                    f["route"] = (f"the keys behind it are owned by {', '.join(named) or 'no unit in the register map'}"
                                  + "".join(f"; {u}: " + (route(u, by_unit[u]) or "") for u in named))
                continue
            if f["kind"] in OWNED and (f["kind"] != "act" or f["key"]):
                unit = (owners.get(f["key"]) or {}).get("unit")
                f["owner"] = unit
                f["route"] = route(unit, f["key"]) if route else None
                c = (closers or {}).get(f["key"])
                if f["kind"] == "key" and f["level"] == "declared_gap" and c is not None:
                    from capture import closing_route
                    f["closer"] = c["unit"]
                    if f["route"]:
                        f["route"] += closing_route(c["gap"], c["unit"])
    kinds = ["task", "key", "intended", "suspect_derived", "stale", "lapsed", "act", "attestation", "lint", "preload"]
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


def compare(res: dict, base: dict, source: str, suspect_scope: dict[str, dict] | None = None) -> dict:
    """A regression is a verdict worse than the baseline's, a required key whose level ranks below
    the baseline's for the same key (a key the baseline did not have counts from absent), or a
    derived output suspect now that the baseline did not hold suspect and that rests on this task's keys
    (task-0282: one resting on none of them is listed at info, so it is no regression either)."""
    worse = VERDICTS.index(res["verdict"]) > VERDICTS.index(base["verdict"])
    regressed = []
    for key, v in res["keys"].items():
        was = base["levels"].get(key)
        if was is not None and LEVELS.index(v["level"]) < LEVELS.index(was):
            regressed.append({"key": key, "level": v["level"], "baseline_level": was})
    held = set(base.get("suspect") or [])
    new_suspect = sorted(d["id"] for d in res.get("suspect_derived") or [] if d["id"] not in held
                         and (suspect_scope or {}).get(d["id"], {"on_task": True})["on_task"])
    return {"source": source, "verdict": base["verdict"], "regression": worse or bool(regressed) or bool(new_suspect),
            "worse_verdict": worse, "regressed_keys": regressed, "new_suspect": new_suspect}


def mark_held(fs: list[dict], baseline: dict) -> None:
    """Under --baseline the gate exits on a regression only, so every other finding is one the baseline
    held: it did not fail the command (task-0207, doc-0030 R8). Each finding gets ``held``: false for a
    finding that is the regression (a key whose level fell, a derived output newly suspect; with a worse
    verdict, the task finding and every blocker, what makes a verdict), true for the rest. CI annotations
    read it, so a held finding is never shown as an error."""
    fell = {r["key"] for r in baseline.get("regressed_keys") or []}
    new_suspect = set(baseline.get("new_suspect") or [])
    worse = bool(baseline.get("worse_verdict"))
    for f in fs:
        regressed = ((f["kind"] == "key" and f["key"] in fell) or (f["kind"] == "suspect_derived" and f["ref"] in new_suspect)
                     or (worse and (f["kind"] == "task" or f["severity"] == "blocker")))
        f["held"] = not regressed


def superseded_map(res: dict) -> dict[str, list[str]]:
    from gate import superseded_map as m
    return m(res)


def report(res: dict, *, subject: str, scenario: str, task: str, store: str, loaded: bool,
           block_levels: set[str], threshold: str, baseline: dict | None,
           version: str | None = None, change: dict | None = None, owners: dict[str, dict] | None = None,
           route_task: str | None = None, route_keys=None, closers: dict[str, dict] | None = None,
           register_change: dict | None = None, task_profile: str | None = None,
           suspect_scope: dict[str, dict] | None = None) -> dict:
    """``task_profile`` is the digest of the task table the gate read (``profile_digest``; None when the
    report is built without one). ``route_task`` is the task class whose questionnaire a finding's route names (``task`` by default;
    the MCP server's agent-chosen key set, task ``keys``, names the class it was resolved under), and
    ``route_keys`` the keys that questionnaire covers (None: every key): a key outside them has no route."""
    from capture import questionnaire_route
    rt = route_task or task

    def route(unit, key):   # the files routing names, so the route points where the questionnaire is written (G8)
        files = ((owners or {}).get(key) or {}).get("files")
        return questionnaire_route(subject, scenario, rt, unit, files) if route_keys is None or key in route_keys else None
    fs = findings(res, block_levels, owners, route, closers, suspect_scope)
    fail = baseline["regression"] if baseline is not None else bool(at_or_above(fs, threshold))
    if baseline is not None:
        mark_held(fs, baseline)
    return {"schema_version": SCHEMA_VERSION, "tool": "knowgov gate", "subject": subject, "scenario": scenario, "task": task,
            "store": store, "loaded": loaded, "version": version, "change": change, "verdict": res["verdict"], "why": res["why"], "threshold": threshold,
            "findings": fs, "counts": counts(fs),
            "keys": {"total": len(res["keys"]), "below_verified": len(res["below_verified"]), "flagged": len(res["flagged"]),
                     **({"unintended": len(res["unintended"])} if "unintended" in res else {})},
            "conflicts": len(res.get("conflicts") or []),
            "stale": [x["id"] for x in res.get("stale") or []],                    # the statements, by id (a count in version 1)
            "superseded_by": superseded_map(res),                                     # task-0071: the stale ones a settled successor supersedes
            "suspect_derived": [d["id"] for d in res.get("suspect_derived") or []],  # the derived outputs, by id (a count in version 1)
            "as_of": res.get("as_of"), "lapsed": [x["id"] for x in res.get("lapsed") or []],   # decision-0005, added in version 2
            "levels": {k: v["level"] for k, v in res["keys"].items()},   # what a later run's --baseline FILE compares with
            "baseline": baseline, "exit_code": 1 if fail else 0,
            # task-0237, decision-0029 (version 3): what the gate decided on, so a retained report names it
            "task_profile": task_profile, "register": register_identity(), "knowgov": knowgov_identity(),
            **({"register_change": register_change} if register_change is not None else {})}   # task-0122, additive


def suspect_scope(st, res: dict, spec: dict) -> dict[str, dict] | None:
    """task-0282 (decision-0033 choice 8): for each suspect derived output, the keys its invalidated or changed
    statements sit on, read through the port (``derived_outputs``, the store's own Assertion keys), and whether
    one of them is a key of this task. A statement whose key cannot be read (no longer held) counts as on the
    task, so the gate blocks rather than guess. None when nothing is suspect. Read here, never stored in the
    gate's result, so the record's gate rows read as before."""
    sus = res.get("suspect_derived") or []
    if not sus:
        return None
    key_of = {u["id"]: u.get("key") for d in st.derived_outputs() for u in d.get("used") or [] if u.get("id")}
    task_keys = set(spec.get("keys") or [])
    out = {}
    for d in sus:
        ids = list(d.get("used_invalidated") or []) + list(d.get("used_changed") or [])
        keys = sorted({key_of[i] for i in ids if key_of.get(i)})
        unknown = any(not key_of.get(i) for i in ids)
        out[d["id"]] = {"keys": keys, "on_task": unknown or bool(task_keys & set(keys))}
    return out


def profile_digest(table: dict | None) -> str | None:
    """The sha256 of a task table's canonical JSON (sorted keys, no whitespace, UTF-8): the subject's
    ``[tasks.<class>]`` as its manifest gives it, with the keys asked for in place of the table's own when a
    key set was asked for (the MCP reader's ``keys``). None when there is no table (task-0237)."""
    if table is None:
        return None
    import hashlib
    text = json.dumps(table, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_IDENTITY: dict = {}


def register_identity() -> dict:
    """The register this process reads (``KG_REGISTER``), its tag and commit (``register_impact.identity``),
    read once per register root: the files and git only, no network, no clock (task-0237)."""
    import cadence
    import register_impact
    root = cadence.register_root().resolve()
    key = ("register", str(root))
    if key not in _IDENTITY:
        _IDENTITY[key] = register_impact.identity(root)
    return dict(_IDENTITY[key])


def knowgov_identity() -> dict:
    """task-0227's build identity, ``{version, commit, describe}``, as store_status reports it; read once."""
    if "knowgov" not in _IDENTITY:
        import build_identity
        _IDENTITY["knowgov"] = build_identity.identity()
    return dict(_IDENTITY["knowgov"])


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


# a gate report written at each version is validated against the schema as it stood then (task-0258):
# versions 1 and 2 are frozen copies, from the commits that last wrote them, beside the current one
REPORT_SCHEMAS = {1: "gate-report-v1", 2: "gate-report-v2", SCHEMA_VERSION: "gate-report"}


def check_report_baseline(data: dict, where: str, *, subject: str, scenario: str, task: str, stage: int) -> None:
    """A gate report read as a baseline is an earlier report of this command for the same run (task-0258, the
    flag's own promise: "an earlier report of this command (at stage 2, a stage-2 report)"): its schema version
    one this knowgov reads, newer refused under decision-0023's rule; valid against the schema of that version
    before anything is compared; and the same subject, scenario, task class and stage. Each failure is CannotRun,
    exit 2, naming the file and what differs. A deterministic.json is the record's, checked by its path."""
    v = data.get("schema_version")
    if isinstance(v, bool) or not isinstance(v, int) or v < 1:
        raise CannotRun(f"--baseline {where}: schema_version {v!r} is not a version of the gate report")
    if v > SCHEMA_VERSION:
        raise CannotRun(f"--baseline {where}: schema_version = {v}, and this knowgov reads gate reports of version "
                        f"{SCHEMA_VERSION} and earlier; refused rather than misread (decision-0023)")
    if v not in REPORT_SCHEMAS:
        raise CannotRun(f"--baseline {where}: no gate-report schema of version {v} to read it by")
    import schema_check
    errors = schema_check.validate(data, schema_check.load(REPORT_SCHEMAS[v]))
    if errors:
        more = f" (and {len(errors) - 1} more)" if len(errors) > 1 else ""
        raise CannotRun(f"--baseline {where}: not a valid version-{v} gate report: {errors[0]}{more}")
    was = {"subject": data.get("subject"), "scenario": data.get("scenario"), "task": data.get("task"),
           "stage": 2 if data.get("change") else 1}
    now = {"subject": subject, "scenario": scenario, "task": task, "stage": stage}
    for field in ("subject", "scenario", "task", "stage"):
        if was[field] != now[field]:
            raise CannotRun(f"--baseline {where}: a report of {field} {was[field]!r}, and this run's {field} is "
                            f"{now[field]!r}: a baseline is an earlier report of the same run")


def _baseline(arg: str, subject, scenario: str, task: str, stage: int = 1) -> tuple[dict, str] | None:
    if arg == "none":
        return None
    if arg == "record":
        if task != "codegen":
            raise CannotRun(f"the record's gate is the codegen task, not {task!r}")
        rel = subject.scenario(scenario).get("deterministic_record") or scenario
        p = subject.record_dir / rel / "deterministic.json"
        if not p.exists():
            raise CannotRun(f"no record for {scenario}: {p} does not exist")
        return _read_baseline(p), "record"
    p = Path(arg)
    if not p.exists():
        raise CannotRun(f"no baseline at {p}")
    return _read_baseline(p, run=(subject.id, scenario, task, stage)), str(p)


def _read_baseline(p: Path, run: tuple[str, str, str, int] | None = None) -> dict:
    """An earlier report or deterministic.json as a baseline; one that cannot be read is a cannot-run (G6). With
    ``run`` (subject, scenario, task, stage), a gate report is first held to it (``check_report_baseline``)."""
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CannotRun(f"--baseline {p}: not a gate report or deterministic.json: {type(e).__name__}: {e}") from e
    if run is not None and isinstance(data, dict) and data.get("tool") == "knowgov gate":
        subject, scenario, task, stage = run
        check_report_baseline(data, str(p), subject=subject, scenario=scenario, task=task, stage=stage)
    try:
        return baseline_of(data)
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        raise CannotRun(f"--baseline {p}: not a gate report or deterministic.json: {type(e).__name__}: {e}") from e



def _require_registers(args) -> None:
    """task-0279 (decision-0033 choice 5): a register named by ``KG_REGISTER``, or by ``--register-previous`` on a
    load, that cannot be read is a cannot-run, exit 2 naming it, never a report read without it."""
    import register_impact
    try:
        register_impact.require_named()
        if args.register_previous and not args.no_load:   # with --no-load, the flag's own refusal names the clash
            register_impact.require(Path(args.register_previous), "--register-previous")
    except register_impact.RegisterUnreadable as e:
        raise CannotRun(str(e)) from None

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
    if args.no_load and args.publish:
        raise CannotRun("--publish publishes a load; --no-load reads the store as it is: drop one")
    if args.no_load and args.stage != 1:
        raise CannotRun("--stage 2 loads the change; --no-load reads the store as it is: drop one")
    cfg2 = SUBJECT.scenario(scenario).get("stage2") if args.stage == 2 else None
    if args.stage == 2 and not cfg2:
        raise CannotRun(f"{SUBJECT.id}: {scenario} has no later version (no [scenario.stage2])")
    if args.stage == 2 and args.baseline == "record":   # task-0209, doc-0030 G9
        raise CannotRun("--baseline record compares with stage 1: the record keeps stage 2's verdicts, not its keys' "
                        "levels; for stage 2, pass --baseline FILE, an earlier stage-2 report of this command")
    base = _baseline(args.baseline, SUBJECT, scenario, args.task, args.stage)
    import cadence
    try:
        on = cadence.as_of(args.as_of).isoformat()
    except ValueError as e:
        raise CannotRun(f"--as-of: {e}") from e
    reg_change = previous = None
    _require_registers(args)
    if args.register_previous:
        if args.no_load:
            raise CannotRun("--register-previous marks statements stale on a load; --no-load reads the store as it is: drop one")
        import register_change as rc
        previous = Path(args.register_previous)
        try:
            reg_change = rc.diff(previous, rc.ri.register_root())
        except Exception as e:  # noqa: BLE001 — a register that does not load is a cannot-run
            raise CannotRun(f"--register-previous: the registers do not compare: {type(e).__name__}: {e}") from e
    from store import ScratchUnavailable, StoreChanged, open_store, read_attempts, scratch_store
    try:
        attempts = read_attempts() if args.no_load else 1
    except ValueError as e:
        raise CannotRun(str(e)) from e   # task-0141.06: a publication during a --no-load read reads again
    for attempt in range(attempts):
        try:
            if args.no_load or args.publish:   # the store KG_STORE names: read as it is, or loaded and published
                st = open_store(instance=SUBJECT.id, access="read" if args.no_load else "write")   # task-0141.02
            else:                              # decision-0017: the load stays in this process
                st = scratch_store(instance=SUBJECT.id)
        except ScratchUnavailable as e:
            raise CannotRun(str(e)) from e
        except Exception as e:  # noqa: BLE001
            raise CannotRun(f"the store cannot be opened: {e}") from e
        try:
            return _gate_on(st, args, SUBJECT, scenario, cfg2, base, on, reg_change, previous)
        except StoreChanged as e:
            if attempt == attempts - 1:
                raise CannotRun(f"the store was republished during each of {attempts} reads; run again: {e}") from e
        finally:
            try:
                st.close()
            except Exception:  # noqa: BLE001
                pass


def _gate_on(st, args, SUBJECT, scenario, cfg2, base, on, reg_change, previous):
    """The gate on one store handle: read as it is (``--no-load``), loaded into the scratch store, or
    loaded into the configured store and published (``--publish``)."""
    import load_memory
    from kitio import DocumentUnreadable
    from store import StoreChanged
    from tasks import TASKS
    change = None
    try:
        if args.no_load:
            import held as held_state
            h = st.held()   # whose load and which scenario, as the load recorded them (task-0195)
            why = held_state.refusal(h, SUBJECT.id, scenario)
            if why:
                raise CannotRun(f"{why}; load it, or drop --no-load")
            version = h["version"]
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
        if not args.no_load:   # a read loads nothing, so it publishes nothing: its report stays the MCP server's
            report["published"] = bool(args.publish)
        deliver(report, args)   # G7: validated and written before anything is published
        if not args.no_load:
            st.commit()   # the load and its change, published once the report is made (a scratch store publishes nowhere)
        return report
    except (CannotRun, StoreChanged):
        raise
    except load_memory.LoadTooLarge as e:   # task-0176: refused before the unit's first write; nothing published
        raise CannotRun(str(e)) from e
    except DocumentUnreadable as e:   # doc-0030 I11: the document's fault, named, never the store's
        raise CannotRun(f"a document cannot be loaded: {e}") from e
    except Exception as e:  # noqa: BLE001 — an unreachable store fails here, on the first statement
        raise CannotRun(f"the store did not answer: {type(e).__name__}: {e}") from e


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
    scope = suspect_scope(st, res, spec)   # task-0282: which suspect outputs rest on this task's keys
    table = None   # task-0237: the subject's [tasks.<class>] as read, the keys asked for in place of its own
    if SUBJECT.id == subject and (route_task or task) in SUBJECT.tasks:
        table = dict(SUBJECT.tasks[route_task or task])
        if task == "keys" or list(spec.get("keys") or []) != list(table.get("keys") or []):
            table["keys"] = list(spec.get("keys") or [])
    if SUBJECT.id == subject:
        if owners is None:
            from capture import finding_owners
            owners = finding_owners(SUBJECT)
        if closers is None:   # task-0110: the unit each declared gap's declaration names closes it
            from capture import gap_closers
            closers = gap_closers(SUBJECT, {k: v.get("declared_gaps") or [] for k, v in res["keys"].items()})
    return report(res, subject=subject, scenario=scenario, task=task, store=st.name, loaded=loaded,
                  block_levels=set(spec["block_levels"]), threshold=threshold,
                  baseline=compare(res, *baseline, suspect_scope=scope) if baseline else None, version=version, change=change, owners=owners,
                  route_task=route_task, route_keys=_route_keys(route_task) if route_task and route_task != task else None,
                  closers=closers, register_change=register_change, task_profile=profile_digest(table), suspect_scope=scope)


def _route_keys(task: str) -> set[str] | None:
    """The keys the questionnaire of task class ``task`` covers; None when the subject declares no such class."""
    from tasks import TASKS
    return set(TASKS[task]["keys"]) if task in TASKS else None


def held_version(st) -> str | None:
    """The version the store holds, as ``--no-load`` reports it: ``held()``'s, from the artefacts'
    current versions, not the extraction activities' order (task-0195, S5)."""
    h = st.held()
    return h["version"] if h else None


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
    from load import now
    done = rc.apply(st, landed, at=now())   # invalidated_at: the instant of this change (doc-0030 S8)
    return {**rc.block(change, landed), "invalidated": [x["id"] for x in done["invalidated"]], "derived": did}


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


def deliver(rep: dict, args) -> None:
    """The report checked against its schema and written to ``-o``, before ``--publish`` commits (G7): a
    report that does not match, or a file that cannot be written, is a cannot-run, and nothing is published."""
    sys.path.insert(0, str(HERE))
    from schema_check import load as load_schema, validate
    errs = validate(rep, load_schema("gate-report"))
    if errs:   # the report does not match its own schema: a defect here, never a pass
        raise CannotRun("the report does not match its schema: " + "; ".join(errs[:5]))
    if getattr(args, "output", None):
        try:
            Path(args.output).write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
        except OSError as e:
            raise CannotRun(f"-o {args.output}: cannot be written: {e}") from e


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gate_cli.py", description="Resolve a task's required knowledge and exit 0, 1 or 2.")
    ap.add_argument("--subject", help="the subject root (default: KG_SUBJECT, else subjects/cargo_quote)")
    ap.add_argument("--scenario", help="the scenario to load (default: the subject's first)")
    ap.add_argument("--task", default="codegen", help="the task class (default: codegen)")
    ap.add_argument("--fail-on", choices=SEVERITIES, default="blocker", help="the severity at or above which the gate exits 1 (default: blocker)")
    ap.add_argument("--baseline", default="none", help="none (default), record (stage 1 only), or the path of an earlier report or deterministic.json: exit 1 only on a regression")
    ap.add_argument("--stage", type=int, choices=[1, 2], default=1,
                    help="1 (default): the scenario as first loaded; 2: then its later version, the subject's [scenario.stage2] change, before re-verification")
    ap.add_argument("--reverify", action="store_true", help="with --stage 2: the owner's recorded re-verification of the named keys before the gate")
    ap.add_argument("--no-load", action="store_true", help="read the store KG_STORE names as it is instead of loading the scenario first")
    ap.add_argument("--publish", action="store_true",
                    help="load into the store KG_STORE names and publish the load (decision-0017); by default the load stays in this process")
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
    print(json.dumps(rep, indent=1) if args.format == "json" else render(rep))
    return rep["exit_code"]


if __name__ == "__main__":
    import cli_exit   # task-0200 (doc-0030 F6): every failure to run is exit 2 with its cause, never 1
    sys.exit(cli_exit.run(main, "gate"))
