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
adds ``; closed by UNIT``. A suspect derived output's owner and route come from the keys of the statements it
used that are now invalidated or changed (``related``), not from every key of its file (task-0311 N1). A route is
one line of text, never parsed: the questionnaire's or the close's command, or a sentence naming who does what (an
attestation's step, a review lapse's, a settled act's ``nothing to do: ...``, the bar's blocker) (task-0311 N4).

The JSON report (-f json) is pinned by harness/schemas/gate-report.schema.json, version 3 (the
schema's description says what changed from 1 and 2 and what was added since), and validated before
it is printed. Version 3 (task-0237, decision-0029) names what the gate decided on: ``task_profile``,
the sha256 of the task table read; ``register``, its tag and commit; ``knowgov``, the build. Added since, without a
version change (task-0307, decision-0037): ``corpus``, the sha256 over the loaded document Versions' digests
(``store.corpus_digest``: one canonical JSON line ``[artefact, version, sha256]`` each, sorted; task-0320). And
(task-0320, decision-0038 N2): ``attestations`` and ``captures``, what the load used beyond the documents as the
store recorded it (``Store.inputs``), and ``register.files``, the register's files a load reads (its own loader's and the issued handles). And
(task-0335, decision-0039 §3.2): ``configuration``, the sha256 of each subject configuration file the load read
(``Subject.configuration``: ``subject.toml`` whole, ``scenarios.toml``, the register map, ``plants.toml``,
``queries.toml`` and the verification map where read), by path, compared whole. And (task-0341, decision-0040 (a)):
``code``, the sha256 of each ``[reference] code``, ``[oracle] script`` and ``[oracle] suite`` file an execution
verification is compared against (``Subject.code``, the load's part selection), by path, and ``preload``, the
pre-load report the load applied, {path, sha256, why}, both null with ``why`` when none was (``preload.identity``),
each compared whole. With ``--baseline``,
each identity field (``IDENTITY_FIELDS``) that differs from the baseline's is listed in ``baseline.differs``
(``differs``, the MCP reader's too) and named on stderr, one line each; the exit is the ratchet's, unchanged. A
field the baseline lacks, or holds as unknown (null), and an object's sub-field unknown on either side, is never
named; ``--baseline record`` holds only ``as_of``, the subject's ``[record] as_of``.
"""
from __future__ import annotations

if __name__ == "__main__":   # task-0200: a failure while loading (a pin not installed) is exit 2, its cause in one line
    import cli_exit
    cli_exit.guard("gate")

import argparse
import json
import re
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


def _declared(ds: list[str]) -> tuple[str, str]:
    """(the declarations named as prose, the decisions cited): task-0318, decision-0036 beside decision-0019 when a bound
    execution or review is among them."""
    named = ", ".join(ds[:-1]) + " and " + ds[-1] if len(ds) > 1 else ds[0]
    return named, ("decision-0019 and decision-0036" if {"execution", "review"} & set(ds) else "decision-0019")


STEP = {"authored": "the author reads the document and lists sha256 {sha} under [verification] authored versions",
        "approval": "the approver (not the author, decision-0002) reads the document and lists sha256 {sha} under [verification] approval versions",
        "review": "the reviewer (not the author, decision-0002) reads the document and lists sha256 {sha} under [verification] "
                  "review versions (for a single document's re-review, `capture.py review` gives it its own date: one `at` re-dates every listed Version)",
        "execution": "the reference implementation and the suite are brought in line with this Version where its values differ, the "
                     "suite is run on it, then sha256 {sha} is listed under [verification] execution versions with the implementation "
                     "and suite digests ([oracle] script's and each file [oracle] suite lists) (where the values differ and they are unchanged, listing only asserts the old result for the "
                     "new values: no oracle runs at load, decision-0038)"}


def attestation_route(decls: list[str], sha: str, attester: str = "") -> str:
    """task-0324: one step per declaration, each its own reader's act (execution only after the suite has run on the
    Version); never one reader listing all of them."""
    who = f" ({attester})" if attester else ""
    return "; ".join(STEP[d].format(sha=sha) + who for d in ("authored", "approval", "review", "execution") if d in decls)


def _below_verified(res: dict) -> set:
    """The keys that read below verified (task-0332 H5), for the count an unlisted declaration's finding gives."""
    from gate import ORDER
    return {k for k, v in (res.get("keys") or {}).items() if ORDER.index(v["level"]) < ORDER.index("verified")}


def unlisted_finding(r: dict, below: set | None = None) -> dict:
    """A declaration that lists no Version. Execution and review (task-0325) are major (task-0330 H3): nothing is verified by
    them without one, so it is the cause of a BLOCKED; it names each document behind the task's keys with its digest and the
    count of keys. authored and approval are the read rule's, at info."""
    n = r["declaration"]
    if n in ("execution", "review"):
        un = r["unattested"]
        keys = sorted({k for u in un for k in u.get("keys") or []})
        lost = ("what it verified by review is lost" if n == "review" else
                "what it verified by execution is lost, and the approvals resting on it read proposed too")
        f = _finding("major", "attestation", f"[verification] {n} lists no Version: it verifies nothing, since an execution or a review "
                     f"verification holds only for the Versions it lists (decision-0036), so {lost} and the keys behind it fall "
                     f"below verified, behind {len(keys)} required key(s)"
                     + (f", of which {len(set(keys) & below)} now read below verified, from any cause, not this declaration alone" if below is not None else ""),
                     ref=f"attest:{n}", related=keys)
        f["route"] = "; ".join(f"{u['artefact']}: " + attestation_route([n], u["sha256"], r["attester"])
                               for u in un if u.get("keys")) or attestation_route([n], "<digest of each document>", r["attester"])
        return f
    return _finding("info", "attestation", f"[verification] {n} lists no Version: it attests what the documents hold at each load "
                    "(decision-0009 (a), the read rule); list the digest of each Version it attests (decision-0019) to bind it",
                    ref=f"attest:{n}")


def _consequence(ds: list[str]) -> str:
    """task-0330: what an unlisted Version costs, for the declarations actually bound."""
    if {"authored", "approval"} & set(ds):
        return "its authored statements read proposed and nothing in it is approved by construction"
    return f"what it verified by {' and '.join(ds)} is lost and the keys behind it fall below verified"


def attestation_findings(rows: list[dict], owners: dict | None, route, below: set | None = None) -> list[dict]:
    """decision-0019 (task-0221): a declaration that lists no Version is the read rule's, at info; each artefact a
    bound declaration does not attest, behind the task's keys, is major (its authored statements read proposed and
    nothing in it is approved by construction, so the keys behind it fall below verified, and the attester or the
    keys' owner has to act). It names the keys' owner and route (``capture.routing``) when they share one."""
    out = [unlisted_finding(r, below) for r in rows if not r["bound"]]
    out += [code_finding(u, r, owners, route) for r in rows if r["bound"] for u in r["unattested"] if u.get("code")]
    merged: dict[str, dict] = {}
    for r in rows:
        for u in [u for u in r["unattested"] if not u.get("code")] if r["bound"] else []:
            m = merged.setdefault(u["artefact"], {**u, "declarations": [], "attester": r["attester"]})
            m["declarations"].append(r["declaration"])
    for art, u in sorted(merged.items()):
        decls, cite = _declared(u["declarations"])
        digests = ", ".join(x[:12] for x in u["parts"]) if u["parts"] else u["sha256"][:12]
        f = _finding("major", "attestation", f"{art} (sha256 {digests}), behind {len(u['keys'])} required key(s), is not attested: "
                     f"[verification] {decls} list(s) no digest of this Version, so " + _consequence(u["declarations"]) + f" ({cite})", ref=art, related=u["keys"])
        if owners is not None:
            units = {(owners.get(k) or {}).get("unit") for k in u["keys"]}
            unit = units.pop() if len(units) == 1 else None
            f["owner"] = unit
            how = attestation_route(u["declarations"], u["sha256"], u["attester"]) + f" in subject.toml ({cite})"
            q = route(unit, u["keys"][0]) if route and unit else None
            f["route"] = how + (f"; or {q}" if q else "")
        out.append(f)
    return out


def _code_listed(u: dict, files: list[dict]) -> str:
    """What ``[verification] execution`` lists of a code row (task-0320): none, or the digests it does not list, each
    ``[oracle] suite`` file by its path and digest (task-0338)."""
    if u.get("missing"):
        return f"lists no {u['code']} digests" + (f", none for {', '.join(x['path'] for x in files)}" if files else "")
    by_path = {x["sha256"] for x in files}
    unlisted = [d[:12] for d in u["parts"] if d not in by_path] + [
        f"{x['path']} ({x['sha256'][:12]})" if x["sha256"] else f"{x['path']} (no file there)" for x in files]
    stale = u.get("stale") or []   # task-0340 R1: listed digests no current file holds (a file deleted)
    tail = f"lists {', '.join(d[:12] for d in stale)}, which no current file holds" if stale else ""
    if unlisted:
        return f"does not list {', '.join(unlisted)}" + (f" and {tail}" if tail else "")
    return tail or "lists it, and it holds no file"


def code_finding(u: dict, r: dict, owners: dict | None, route) -> dict:
    """task-0320 (decision-0038 N-b): the reference implementation or the suite an execution verification ran on is not
    the one ``[verification] execution`` lists, so the load verified nothing by execution. Major when it is behind the
    task's keys, info when none of them rests on it; the route is the attester's listing."""
    files = u.get("files") or []   # task-0338 (decision-0039 §3.5): the [oracle] suite files it misses, by path
    what = {"implementation": "the reference implementation ([reference] code)",
            "suite": "the suite that judged it ([oracle] script" + (" and suite" if files or u.get("suite_listed") else "") + ")"}[u["code"]]
    listed = _code_listed(u, files)
    f = _finding("major" if u["keys"] else "info", "attestation",
                 f"{u['artefact']}, {what}, is not the one the execution verification attests: [verification] execution {listed}, "
                 f"so nothing is verified by execution, behind {len(u['keys'])} required key(s) (decision-0038)",
                 ref=u["artefact"], related=u["keys"])
    if owners is not None:
        units = {(owners.get(k) or {}).get("unit") for k in u["keys"]}
        unit = units.pop() if len(units) == 1 else None
        f["owner"] = unit
        each = "each file's sha256" + (" ([oracle] script and each file [oracle] suite lists)" if u["code"] == "suite" else "")
        f["route"] = (f"{r['attester'] or 'the attester'} runs the suite on it and lists {each} under [verification] "
                      f"execution {u['code']} in subject.toml (decision-0038), or restores it")
    return f


def _opposed_act(a: dict) -> bool:
    """Whether an act (as ``act_finding`` reports it) is a ruling cancelled by an opposing one the same day (task-0331)."""
    import review
    return a["why"] == "ambiguous" and a["act"] == "ruling" and review.is_opposed(a["reasons"])


def _act_route(f: dict, route):
    """The route of an act whose ruling was set aside as ambiguous or opposed (task-0331, task-0333 R6): settled at info
    (an opposed act's second reason, a task-0322 act's ``settled by``) it is ``nothing to do: <the settling reason>``;
    a ``superseded for the key by`` act, info too, keeps its own route; an open opposed act, a new review on a later day, not the questionnaire.
    Any other act keeps ``route``."""
    if f["kind"] != "act":
        return route
    a = f["act"]
    reasons = a["reasons"]
    if a["why"] == "ambiguous" and a["act"] == "ruling" and reasons:
        import review
        if review.is_opposed(reasons):
            return (f"nothing to do: {reasons[-1]}" if len(reasons) > 1 else
                    "the owners rule again in one review, on a later day (python harness/capture.py review <file>" + _from_instance() + ")")
        if reasons[0].startswith(review.SETTLED):
            return f"nothing to do: {reasons[0]}"
    return route


def _opposed_severity(a: dict, msg: str) -> tuple[str, str]:
    """task-0331: an opposed act's message is its own reason alone (no generic clause), then the settling reason if a later
    day decided it; info once a later day's approval or rejection settled it (task-0333), major while nothing did or a referral only."""
    import review
    last = a["reasons"][-1]
    tail = "; ".join(a["reasons"]) + (", so the key reads from that ruling" if last.startswith(review.SETTLED) else "")
    head = msg[:msg.index("was not applied:") + len("was not applied:")]
    return ("info" if len(a["reasons"]) > 1 and last.startswith(review.INFO_REASONS) else "major"), f"{head} {tail}"


def _act_severity(a: dict, msg: str) -> tuple[str, str]:
    """The act's severity and message: info when a resolution is gone, and (task-0321) when a later review settled an
    ambiguous ruling, naming it."""
    if a["act"] == "resolve" and a["why"] == "gone":
        return "info", msg
    if a["why"] == "ambiguous" and a["act"] == "ruling" and a["reasons"]:
        import review
        if review.is_opposed(a["reasons"]):
            return _opposed_severity(a, msg)
        r = a["reasons"][0]
        tail = f"; {r}" + (", so the key reads from that ruling" if r.startswith(review.SETTLED) else "")
        return ("info" if r.startswith(review.INFO_REASONS) else "major"), msg.replace("; its owner rules again", tail)
    return ACT_SEVERITY[a["why"]], msg


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
               + {"changed": (a["reasons"][0] if a["reasons"] else f"the statement now reads {now}"), "gone": "no statement of it is extracted any more (if only another person's identical answer remains, this ruling does not cover it)",
                  "ambiguous": "several statements hold that content and none is the one it names, or its id reads as two givers' and names neither"}[why]
               + "; its owner rules again")
    sev, msg = _act_severity(a, msg)
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
        why += ("; and " if why else "used ") + f"{len(changed)} statement(s) changed since it was built (its value, or the source it was read from) ({', '.join(changed)})"
    what = f"{d['id']} ({d.get('kind') or 'derived output'}) {why}"
    if scope is not None and not scope["on_task"]:
        return _finding("info", "suspect_derived", f"{what}; they sit on {', '.join(scope['keys']) or 'no key held'}, none of this "
                        "task's keys: listed, not blocking this task", ref=d["id"], related=used + changed)
    return _finding("blocker", "suspect_derived", f"{what}: it may not be reused as it is: regenerate it from the current statements",
                    ref=d["id"], related=used + changed)


def _from_instance() -> str:
    from capture import FROM_INSTANCE
    return FROM_INSTANCE


def _awaiting(v: dict) -> str:
    """C2-3 (task-0311): the assertions a reviewer rules on, named in the key's finding."""
    pend = sorted(v.get("pending_review") or [])
    return f" (awaiting a reviewer's ruling: {', '.join(pend)})" if pend else ""


def _bar_finding(res: dict) -> dict:
    """A-F4 (task-0311): the bar's blocker names a next step, the keys below the bar and their routes."""
    f = _finding("blocker", "task", res["why"])
    f["route"] = ("raise the keys below the bar: the key findings after this one each name their owner and the route to approval; "
                  "the share falls under the bar when enough of them are verified or approved")
    return f


def _lapse_route(f: dict, res: dict) -> str | None:
    """A-F4 (task-0311): a review's lapse is renewed by a new review, not by a questionnaire; any other finding keeps its route."""
    lapsed_by_id = {x["id"]: x for x in res.get("lapsed") or []}
    if f["kind"] != "lapsed" or not f["route"] or lapsed_by_id.get(f["ref"], {}).get("kind") == "elicited":
        return f["route"]
    return ("a reviewer who is not the author, under a handle whose unit owns the key and holds the role `closes`, renews it: "
            "python harness/capture.py review FILE" + _from_instance() + ", the review dated on or before the as-of date; or " + f["route"])


def _key_finding(key: str, v: dict, block_levels: set[str], rel: list[str]) -> dict | None:
    """The finding one required key gives, by its level: a blocker, a major below verified, a minor when flagged, else (R3,
    task-0311) an info when an answer awaits a reviewer's ruling; None when it reads clean."""
    lvl, flags = v["level"], v["flags"]
    if lvl in block_levels:
        return _finding("blocker", "key", f"{key} is {lvl.replace('_', ' ')}: the task cannot proceed on it",
                        key=key, level=lvl, flags=flags, related=rel)
    if LEVELS.index(lvl) < LEVELS.index("verified"):
        return _finding("major", "key", f"{key} is {lvl}, below verified: an assistant may use it only as a stated assumption"
                        + _awaiting(v), key=key, level=lvl, flags=flags, related=rel)
    if flags:
        return _finding("minor", "key", f"{key} is {lvl} but flagged {', '.join(flags)}" + _awaiting(v),
                        key=key, level=lvl, flags=flags, related=rel)
    if v.get("pending_review"):
        return _finding("info", "key", f"{key} is {lvl}" + _awaiting(v) + ": the answer is not counted in the level until it is ruled on",
                        key=key, level=lvl, flags=flags, related=rel)
    return None


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
        kf = _key_finding(key, v, block_levels, conflict_ids(res, key))   # task-0314 A-F6: the conflicts a key is in
        if kf:
            out.append(kf)
    for key in res.get("unintended") or []:   # task-0215: the intended bar, decision-0018 point 4
        v = res["keys"][key]
        out.append(_finding("major", "intended", f"{key} is verified but not approved, and the task class requires approved: "
                            "a behaviour shown to hold is not yet one a person intends; its owner approves it or rules otherwise",
                            key=key, level=v["level"], flags=v["flags"]))
    if res["verdict"] == "BLOCKED" and not res["blocked_keys"]:
        out.append(_bar_finding(res))
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
        what = _preload_what(d)
        out.append(_finding("info", "preload", f"{d['artefact']} {d['version']}, behind {len(d['keys'])} required key(s): {what}"
                            + (f" ({d['tool']})" if d.get("tool") else "") + (f"; {d['why']}" if d.get("why") else ""),
                            ref=f"{d['artefact']}@{d['version']}", related=d["keys"]))
    out += [act_finding(a) for a in res.get("acts") or []]
    out += attestation_findings(res.get("attestation") or [], owners, route, _below_verified(res))
    out += [lint_finding(g) for g in res.get("lint") or []]   # task-0216
    if owners is not None:
        for f in out:
            if f["kind"] == "lint":   # the document's owning unit: the one unit capture.routing gives every key behind it
                f["owner"], f["route"] = owner_route(f["related"], owners, route)
                continue
            if f["kind"] in OWNED and (f["kind"] != "act" or f["key"]):
                unit = (owners.get(f["key"]) or {}).get("unit")
                f["owner"] = unit
                f["route"] = _act_route(f, route(unit, f["key"]) if route else None)
                f["route"] = _lapse_route(f, res)
                c = (closers or {}).get(f["key"])
                if f["kind"] == "key" and f["level"] == "declared_gap" and c is not None:
                    from capture import closing_route
                    f["closer"] = c["unit"]
                    if f["route"]:
                        f["route"] += closing_route(c["gap"], c["unit"])
    kinds = ["task", "key", "intended", "suspect_derived", "stale", "lapsed", "act", "attestation", "lint", "preload"]
    return sorted(out, key=lambda f: (SEVERITIES.index(f["severity"]), kinds.index(f["kind"]), f["key"] or "", f["ref"] or ""))


def _preload_what(d: dict) -> str:
    """The gate's words for a document the pre-load check left unchecked, found in findings or held (task-0064); a row a
    step-4 check judged alone says so (task-0312 R1)."""
    if d["state"] == "unchecked" and d.get("tool") and f"judged by {d['tool']} alone" in (d.get("why") or ""):
        return f"judged by {d['tool']} alone, its linter never ran"
    return {"unchecked": "its form was not checked before the load", "findings": "the pre-load check found findings in it",
            "held": "the pre-load check holds findings in it against a baseline"}[d["state"]]


def owner_route(keys: list[str], owners: dict[str, dict], route) -> tuple[str | None, str | None]:
    """The owner and the route of a finding that rests on ``keys`` (task-0102): the one unit that answers for every key,
    else None; its questionnaire's route, or, when several units own them, each one's route, any of them resolving it.
    The gate's lint findings and the trace's (task-0304) read it."""
    by_unit: dict = {}
    for k in keys:
        by_unit.setdefault((owners.get(k) or {}).get("unit"), k)
    owner = next(iter(by_unit)) if len(by_unit) == 1 else None
    if not route or not keys:
        return owner, None
    if len(by_unit) == 1:
        return owner, route(owner, keys[0])
    named = sorted(u for u in by_unit if u)
    return owner, (f"the keys behind it are owned by {', '.join(named) or 'no unit in the register map'}"
                   + "".join(f"; {u}: " + (route(u, by_unit[u]) or "") for u in named))


def counts(fs: list[dict]) -> dict[str, int]:
    return {s: sum(1 for f in fs if f["severity"] == s) for s in SEVERITIES}


def at_or_above(fs: list[dict], threshold: str) -> list[dict]:
    return [f for f in fs if SEVERITIES.index(f["severity"]) <= SEVERITIES.index(threshold)]


# task-0307: what --baseline names when it differs; attestations and captures, task-0320 (decision-0038 N2);
# configuration, task-0335 (decision-0039 §3.2); code and preload, task-0341 (decision-0040 (a))
IDENTITY_FIELDS = ("task_profile", "register", "knowgov", "corpus", "attestations", "captures", "configuration", "code",
                   "preload", "as_of")
# task-0335: an object compared whole, a file read on one side only a difference; task-0341: code likewise, and preload,
# whose null path and digest with a why are known (no report applied), not unknown
WHOLE = frozenset({"configuration", "code", "preload"})


def _nfc_levels(levels) -> dict:
    """A baseline's key -> level map with its keys in NFC, as the gate holds them (task-0309 B1): a file written with
    NFD keys must not read every current key as new."""
    import key_rule
    return {key_rule.normalise(k): v for k, v in levels.items()} if isinstance(levels, dict) else levels


def baseline_of(data: dict) -> dict:
    """{verdict, levels, suspect, identity} from an earlier report of this command (version 1 or 2; a version-1
    report named no derived output, so it holds none suspect) or from a deterministic.json. ``identity`` holds
    the identity fields the report carries (task-0307); a field it lacks is left out, read as unknown. A
    deterministic.json names none: its ``identity`` is None, the record's (``record_identity``) set by the reader."""
    if data.get("tool") == "knowgov gate":
        sus = data.get("suspect_derived")
        return {"verdict": data["verdict"], "levels": _nfc_levels(data.get("levels", {})), "suspect": list(sus) if isinstance(sus, list) else [],
                "identity": {f: data[f] for f in IDENTITY_FIELDS if f in data}}
    if "D6_gate" in data:
        return {"verdict": data["D6_gate"]["verdict"], "levels": _nfc_levels({k: v["level"] for k, v in data.get("gate_keys", {}).items()}),
                "suspect": [d["id"] for d in data["D6_gate"].get("suspect_derived") or []], "identity": None}
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
    import key_rule
    fell = {key_rule.normalise(r["key"]) for r in baseline.get("regressed_keys") or []}
    new_suspect = set(baseline.get("new_suspect") or [])
    worse = bool(baseline.get("worse_verdict"))
    for f in fs:
        regressed = ((f["kind"] == "key" and f["key"] in fell) or (f["kind"] == "suspect_derived" and f["ref"] in new_suspect)
                     or (worse and (f["kind"] == "task" or f["severity"] == "blocker")))
        f["held"] = not regressed


def superseded_map(res: dict) -> dict[str, list[str]]:
    from gate import superseded_map as m
    return m(res)


NO_INPUTS = {"attestations": None, "captures": None, "configuration": None, "code": None, "preload": None}   # task-0320: a report built with no store's inputs: unknown


def report(res: dict, *, subject: str, scenario: str, task: str, store: str, loaded: bool,
           block_levels: set[str], threshold: str, baseline: dict | None,
           version: str | None = None, change: dict | None = None, owners: dict[str, dict] | None = None,
           route_task: str | None = None, route_keys=None, closers: dict[str, dict] | None = None,
           register_change: dict | None = None, task_profile: str | None = None,
           suspect_scope: dict[str, dict] | None = None, corpus: str | None = None, inputs: dict = NO_INPUTS) -> dict:
    """``corpus`` is ``store.corpus_digest`` of the loaded Versions (task-0307; None when none is loaded).
    ``task_profile`` is the digest of the task table the gate read (``profile_digest``; None when the
    report is built without one). ``route_task`` is the task class whose questionnaire a finding's route names (``task`` by default;
    the MCP server's agent-chosen key set, task ``keys``, names the class it was resolved under), and
    ``route_keys`` the keys that questionnaire covers (None: every key): a key outside them has no route."""
    from capture import questionnaire_route
    rt = route_task or task

    def route(unit, key):   # the files routing names, so the route points where the questionnaire is written (G8)
        files = ((owners or {}).get(key) or {}).get("files")
        return questionnaire_route(subject, scenario, rt, unit, files) if route_keys is None or key in route_keys else None
    fs = register_routes(findings(res, block_levels, owners, route, closers, suspect_scope), res)
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
            "corpus": corpus,   # task-0307, decision-0037: added since, without a version change
            # task-0320, decision-0038 N2: what the load used beyond the documents, as it recorded it; additive
            "attestations": inputs.get("attestations"), "captures": inputs.get("captures"),
            "configuration": inputs.get("configuration"),   # task-0335, decision-0039 §3.2: the subject's files as read; additive
            # task-0341, decision-0040 (a): the code and suite compared, the pre-load report applied; additive
            "code": inputs.get("code"), "preload": inputs.get("preload"),
            **({"register_change": register_change} if register_change is not None else {})}   # task-0122, additive


REGISTER_ROUTE = ("the register update (--register-previous) stales these statements again on every run it is passed, so a "
                  "questionnaire, ingest or review cannot restore them: re-map the key in register_map.toml, or advance the previous "
                  "register to the new one once the owner confirms the update")


def register_routes(fs: list[dict], res: dict) -> list[dict]:
    """R3 (B-N2), L2: a key, or a stale statement of it, that a register update staled names the remedy as its route, not the
    owner's questionnaire, which can never restore it while ``--register-previous`` is passed. Read from the statements'
    own recorded reason (``invalidated_by`` names the register), so a load, a ``--no-load`` read and the MCP server agree."""
    stale = [x for x in res.get("stale") or [] if str(x.get("invalidated_by") or "").startswith("the register")]
    keys, gone = {x["key"] for x in stale}, {x["id"] for x in stale}
    for f in fs:
        if f["kind"] in ("key", "stale") and f["key"] in keys and (f["kind"] == "key" or f["ref"] in gone) and f.get("route"):
            f["route"] = REGISTER_ROUTE
    return fs


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
    """The register this process reads (``KG_REGISTER``), its tag and commit (``register_impact.identity``) and, beside
    them, ``files``, the digest of the files a load reads (``register_impact.files_digest``, task-0320, decision-0038 N2),
    read once per register root: the files and git only, no network, no clock (task-0237)."""
    import cadence
    import register_impact
    root = cadence.register_root().resolve()
    key = ("register", str(root))
    if key not in _IDENTITY:
        _IDENTITY[key] = {**register_impact.identity(root), "files": register_impact.files_digest(root)}   # files: task-0320
    return dict(_IDENTITY[key])


def knowgov_identity() -> dict:
    """task-0227's build identity, ``{version, commit, describe}``, as store_status reports it; read once."""
    if "knowgov" not in _IDENTITY:
        import build_identity
        _IDENTITY["knowgov"] = build_identity.identity()
    return dict(_IDENTITY["knowgov"])


def _known(value) -> bool:
    """An identity value that says something: not null, and for an object (register, knowgov) one with a
    value besides ``why`` (task-0307)."""
    if isinstance(value, dict):
        return any(v is not None for k, v in value.items() if k != "why")
    return value is not None


def _show(value) -> str:
    return value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"))


def _moved(was, now, whole: bool = False) -> bool:
    """Whether an identity field moved (task-0320, A-N1): for an object (register, knowgov), a sub-field other than
    ``why`` that both sides know (neither null nor absent) and that differs; a sub-field unknown on either side is
    never a difference, so a partly unknown object is named only for what both name. Else both known and unequal.
    ``whole`` (``WHOLE``, task-0335): an object whose absent member is known, not unknown, the configuration's file
    the load did not read, so both known and unequal, the map whole; ``code`` and ``preload`` likewise (task-0341)."""
    if whole:
        if isinstance(was, dict) and isinstance(now, dict) and "sha256" in was and "sha256" in now:   # P1: the preload report by its bytes and why, not the path it sits at
            was, now = {k: v for k, v in was.items() if k != "path"}, {k: v for k, v in now.items() if k != "path"}
        return was is not None and now is not None and was != now
    if isinstance(was, dict) and isinstance(now, dict):
        return any(was[k] != now[k] for k in sorted(set(was) & set(now)) if k != "why" and was[k] is not None and now[k] is not None)
    return _known(was) and _known(now) and not isinstance(was, dict) and not isinstance(now, dict) and was != now


def identity_drift(identity: dict, rep: dict) -> list[dict]:
    """Each identity field (``IDENTITY_FIELDS``) on which this report and its baseline's ``identity`` both say
    something and differ: {field, baseline, now} (task-0307, decision-0037). A field either side lacks or holds
    as unknown is never a difference, nor an object's sub-field (``_moved``, task-0320). Never in the exit."""
    return [{"field": f, "baseline": identity[f], "now": rep.get(f)} for f in IDENTITY_FIELDS
            if f in identity and _moved(identity[f], rep.get(f), f in WHOLE)]


def differs(identity: dict | None, rep: dict) -> list[str]:
    """The identity fields that differ from the baseline's, in ``IDENTITY_FIELDS`` order (task-0320, decision-0038 N3):
    the one list the CLI's report and the MCP reader's ``gate_verdict`` carry as ``baseline.differs``, and the
    fields the CLI's stderr lines name."""
    return [d["field"] for d in identity_drift(identity or {}, rep)]


def _moved_paths(was, now) -> list[str]:
    """Q2/P2: the files of a whole-compared map (``configuration``, ``code``) that moved, were added or dropped, sorted."""
    return sorted(k for k in set(was) | set(now) if was.get(k) != now.get(k))


def drift_lines(source: str, drift: list[dict]) -> list[str]:
    out = []
    for d in drift:
        was, now = d["baseline"], d["now"]
        if d["field"] in ("configuration", "code") and isinstance(was, dict) and isinstance(now, dict):
            out.append(f"gate: --baseline {source}: {d['field']} differs: {', '.join(_moved_paths(was, now))} "
                       "(the baseline's digests differ from this run's)")
        elif d["field"] == "preload" and isinstance(was, dict) and isinstance(now, dict):
            out.append(f"gate: --baseline {source}: preload differs: the report's sha256 was {was.get('sha256') or 'none'}, "
                       f"now {now.get('sha256') or 'none'}" + (f" ({now['why']})" if now.get("why") else ""))
        else:
            out.append(f"gate: --baseline {source}: {d['field']} differs: the baseline's {_show(was)}, this run's {_show(now)}")
    return out


def name_drift(base: tuple[dict, str] | None, rep: dict) -> dict:
    """Each identity field that differs from the baseline's, one stderr line each (task-0307): named, never the exit."""
    for line in drift_lines(base[1], identity_drift(base[0].get("identity") or {}, rep)) if base else []:
        print(line, file=sys.stderr)
    return rep


def _remedy(rc: dict) -> list[str]:
    """B-N2: --register-previous re-applies on every run, so no ruling restores what it staled while it is passed."""
    return ["  remedy   --register-previous stales these statements again on every run it is passed, so a questionnaire, ingest or review cannot "
            "restore them: re-map the key in register_map.toml, or run without --register-previous once the owner confirms the update"] if rc["invalidated"] else []


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
        out += _remedy(rc)
    for f in rep["findings"]:
        out.append(f"  {f['severity']:8s} {f['message']}" + (f" [owner {f['owner'] or 'no single unit in the register map'}"
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
    _levels_known(data.get("levels") or {}, where, "$.levels")
    was = {"subject": data.get("subject"), "scenario": data.get("scenario"), "task": data.get("task"),
           "stage": 2 if data.get("change") else 1}
    now = {"subject": subject, "scenario": scenario, "task": task, "stage": stage}
    for field in ("subject", "scenario", "task", "stage"):
        if was[field] != now[field]:
            raise CannotRun(f"--baseline {where}: a report of {field} {was[field]!r}, and this run's {field} is "
                            f"{now[field]!r}: a baseline is an earlier report of the same run")


def _levels_known(levels: dict, where: str, field: str) -> None:
    """Every level a baseline holds is one of the gate's (task-0286): a value the ladder lacks is named, never
    left to fail the comparison as "the store did not answer"."""
    for key, level in levels.items():
        if level not in LEVELS:
            raise CannotRun(f"--baseline {where}: {field}.{key} is {level!r}, not a level of the gate ({', '.join(LEVELS)})")


RECORD_TASK = "codegen"   # the record's gate is the codegen task, read at stage 1 (task-0209)
# a deterministic.json by its whole structure, every record of both public subjects' (task-0286): never one key
RECORD_KEYS = ("D1_constraints", "D2_census", "D4_shacl", "D6_gate", "gate_keys", "load", "rules", "scenario", "verifications")
RECORD_GATE_KEYS = ("below_verified", "blocked_keys", "conflicts", "flagged", "task", "verdict", "why")


def _record_shape(data: dict, where) -> None:
    """A deterministic.json has the record's whole structure, or it is not one (a report with its tool removed and
    a D6_gate added is neither): each top-level part, D6_gate's fields with a verdict of the gate's, and every
    gate key an object with a level."""
    missing = [k for k in RECORD_KEYS if k not in data]
    gate = data.get("D6_gate")
    if missing or not isinstance(gate, dict):
        raise CannotRun(f"--baseline {where}: not a gate report or the record's deterministic.json: it lacks "
                        f"{', '.join(missing) or 'a D6_gate object'}")
    lacking = [k for k in RECORD_GATE_KEYS if k not in gate]
    if lacking or gate.get("verdict") not in VERDICTS:
        raise CannotRun(f"--baseline {where}: not the record's deterministic.json: its D6_gate lacks "
                        f"{', '.join(lacking) or 'a verdict of the gate'} ({gate.get('verdict')!r})")
    keys = data.get("gate_keys")
    if not isinstance(keys, dict) or not all(isinstance(v, dict) and "level" in v for v in keys.values()):
        raise CannotRun(f"--baseline {where}: not the record's deterministic.json: gate_keys is not an object of "
                        "keys, each with its level")


def check_record_baseline(data: dict, where: Path, *, record_dir: Path, scenario: str, task: str, stage: int) -> None:
    """A deterministic.json read as a baseline is this subject's record for the same run (task-0286): a file of
    the subject's own record tree with the record's whole structure (``_record_shape``), its ``scenario`` the run's,
    its task the record's (its D6_gate's, codegen) and its stage 1 (or the one it names), every level one of the gate's. Each failure is CannotRun,
    exit 2, naming the file and what differs."""
    _record_shape(data, where)
    root = Path(record_dir).resolve()
    if not Path(where).resolve().is_relative_to(root):
        raise CannotRun(f"--baseline {where}: a deterministic.json outside this subject's record ({root}): "
                        "a record baseline is the subject's own")
    was = {"scenario": data.get("scenario"), "task": data["D6_gate"].get("task") or data.get("task", RECORD_TASK),
           "stage": data.get("stage", 1)}
    now = {"scenario": scenario, "task": task, "stage": stage}
    for field in ("scenario", "task", "stage"):
        if was[field] != now[field]:
            raise CannotRun(f"--baseline {where}: a record of {field} {was[field]!r}, and this run's {field} is "
                            f"{now[field]!r}: a baseline is the record of the same run")
    keys = data.get("gate_keys") or {}
    _levels_known({k: v["level"] for k, v in keys.items()}, str(where), "$.gate_keys")


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
        return record_identity(_read_baseline(p), subject), "record"
    p = Path(arg)
    if not p.exists():
        raise CannotRun(f"no baseline at {p}")
    return record_identity(_read_baseline(p, run=(subject.id, scenario, task, stage), record_dir=subject.record_dir), subject), str(p)


def record_identity(base: dict, subject) -> dict:
    """A deterministic.json names no identity of its own; the record is read as of the subject's ``[record] as_of``,
    so that is the one field it holds (task-0307). A gate report's identity is its own, left as read."""
    if base.get("identity") is None:
        import cadence
        on = cadence.record_date(subject) if getattr(subject, "record_as_of", None) else None
        base["identity"] = {"as_of": on.isoformat()} if on else {}
    return base


def _read_baseline(p: Path, run: tuple[str, str, str, int] | None = None, record_dir: Path | None = None) -> dict:
    """An earlier report or deterministic.json as a baseline; one that cannot be read is a cannot-run (G6). With
    ``run`` (subject, scenario, task, stage), a gate report is first held to it (``check_report_baseline``)."""
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CannotRun(f"--baseline {p}: not a gate report or deterministic.json: {type(e).__name__}: {e}") from e
    if run is not None and isinstance(data, dict) and data.get("tool") == "knowgov gate":
        subject, scenario, task, stage = run
        check_report_baseline(data, str(p), subject=subject, scenario=scenario, task=task, stage=stage)
    elif run is not None and isinstance(data, dict) and "D6_gate" in data:
        _, scenario, task, stage = run
        check_record_baseline(data, p, record_dir=record_dir, scenario=scenario, task=task, stage=stage)
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
    scenario = _scenario_read(args, SUBJECT)
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
            return name_drift(base, _gate_on(st, args, SUBJECT, scenario, cfg2, base, on, reg_change, previous))
        except StoreChanged as e:
            if attempt == attempts - 1:
                raise CannotRun(f"the store was republished during each of {attempts} reads; run again: {e}") from e
        finally:
            try:
                st.close()
            except Exception:  # noqa: BLE001
                pass


def _scenario_read(args, SUBJECT) -> str:
    """The scenario named, else (R1) with ``--no-load`` the one the store holds, else the subject's first: resolved before
    the baseline is checked against it."""
    if args.scenario:
        return args.scenario
    first = SUBJECT.order[0] if SUBJECT.order else ""
    return _peek_held(SUBJECT, first) if args.no_load else first


def _peek_held(SUBJECT, default: str) -> str:
    """The scenario the store holds for this subject, else ``default`` (the refusal then names why, in ``_gate_on``)."""
    from store import open_store
    try:
        st = open_store(instance=SUBJECT.id, access="read")
    except Exception:  # noqa: BLE001 — a store that cannot open is reported where it is opened for the read
        return default
    try:
        h = st.held()
        return h.get("scenario") if h and h.get("scenario") in SUBJECT.scenarios and h.get("subject", SUBJECT.id) == SUBJECT.id else default
    except Exception:  # noqa: BLE001
        return default
    finally:
        try:
            st.close()
        except Exception:  # noqa: BLE001
            pass


def _held_scenario(h: dict, default: str) -> str:
    return h.get("scenario") or default


def _own_cause(e: Exception) -> str | None:
    """S1: the manifest is the cause, said as itself (task-0329 R6: a code file outside, unreadable or not a path); so is a
    ``KG_PRELOAD_REPORT`` that names no file (task-0312 R2). None leaves it to the store's line."""
    from subject import CodePathOutside, CodeUnreadable
    if isinstance(e, PermissionError):   # L3: a file the manifest names that this user cannot read
        return f"a file the manifest names cannot be read: {e.filename or e} (permission denied)"
    if isinstance(e, (CodePathOutside, CodeUnreadable)):
        return str(e)
    return str(e) if isinstance(e, FileNotFoundError) and "KG_PRELOAD_REPORT names" in str(e) else None


def _gate_on(st, args, SUBJECT, scenario, cfg2, base, on, reg_change, previous):
    """The gate on one store handle: read as it is (``--no-load``), loaded into the scratch store, or
    loaded into the configured store and published (``--publish``)."""
    import load_memory
    import switches
    from kitio import DocumentUnreadable
    from store import StoreChanged
    from tasks import TASKS
    change = None
    try:
        if args.no_load:
            import held as held_state
            h = st.held()   # whose load and which scenario, as the load recorded them (task-0195)
            why = held_state.refusal(h, SUBJECT.id, args.scenario)   # A-N5: unnamed, the scenario held, as the MCP server reads it
            if why:
                raise CannotRun(f"{why}; load it, or drop --no-load")
            scenario = _held_scenario(h, scenario)
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
    except (CannotRun, StoreChanged, switches.BadSwitch):   # task-0287 N9: a misspelt switch is named as itself
        raise
    except load_memory.LoadTooLarge as e:   # task-0176: refused before the unit's first write; nothing published
        raise CannotRun(str(e)) from e
    except DocumentUnreadable as e:   # doc-0030 I11: the document's fault, named, never the store's
        raise CannotRun(f"a document cannot be loaded: {e}") from e
    except Exception as e:  # noqa: BLE001 — an unreachable store fails here, on the first statement
        raise CannotRun(_own_cause(e) or f"the store did not answer: {type(e).__name__}: {e}") from e


SUB_GATE_WHY = (   # the gate's three forms (gate.py) and the sub-gate's words for each, most specific first (task-0314 B-X3, R1)
    (r"\b(\d+) required key\(s\) at\b", r"\1 of the keys reached at"),
    (r"\ball (\d+) required keys\b", r"all of the \1 keys reached"),
    (r"\bof (\d+) required keys\b", r"of the \1 keys reached"),
    (r"\b(\d+) required keys?\b", r"the \1 keys reached"))


def sub_gate_why(sub_gate: bool, why):
    """task-0314 B-X3, R-T4, R1: a sub-gate over the keys a walk reached (``register_impact``, ``proposal_impact``) counts
    "the N keys reached", not the class's required keys; any other evaluation, ``gate_verdict`` on keys the caller named
    included, keeps the gate's own words."""
    if not sub_gate or not isinstance(why, str):
        return why
    for pattern, words in SUB_GATE_WHY:
        why = re.sub(pattern, words, why)
    return why


def conflict_ids(res: dict, key: str) -> list[str]:
    """task-0314 A-F6, R3: the conflicts on ``key`` (``gap:conflict:<key>:<a>~<b>``, decision-0020) whose two ends are
    assertion ids of this key, by id: a key may contain ':' and be the start of another's, so the prefix alone is not a match."""
    mine = {a["id"] for a in res["keys"].get(key, {}).get("assertions") or []}
    head = f"gap:conflict:{key}:"
    out = []
    for c in res.get("conflicts") or []:
        cid = str(c.get("id", ""))
        ends = cid[len(head):].split("~") if cid.startswith(head) else []
        if len(ends) == 2 and set(ends) <= mine:
            out.append(cid)
    return sorted(out)


def evaluate(st, *, subject: str, scenario: str, task: str, spec: dict, threshold: str,
             baseline: tuple[dict, str] | None, loaded: bool, version: str | None = None,
             change: dict | None = None, as_of="today", owners: dict[str, dict] | None = None,
             route_task: str | None = None, closers: dict[str, dict] | None = None,
             register_change: dict | None = None, sub_gate: bool = False) -> dict:
    """Resolve ``spec`` on the store as it stands, as of ``as_of`` (today by default; harness/cadence.py), and build the report. The command calls this
    after its load (and stage 2's change, if any); the MCP server (harness/mcp_server.py) calls it
    on a store it only reads, so one input gives one report whichever way it was asked. ``owners``
    defaults to the loaded subject's (``capture.finding_owners``) when ``subject`` is its id;
    ``route_task``, the class an agent-chosen key set was resolved under, names its questionnaire; ``sub_gate``, a gate over
    the keys a walk reached, words its ``why`` as "the N keys reached" (task-0314)."""
    from gate import resolve_spec
    from store import corpus_digest
    res = resolve_spec(st, task, spec, as_of)
    res["why"] = sub_gate_why(sub_gate, res["why"])
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
    rep = report(res, subject=subject, scenario=scenario, task=task, store=st.name, loaded=loaded,
                 block_levels=set(spec["block_levels"]), threshold=threshold,
                 baseline=compare(res, *baseline, suspect_scope=scope) if baseline else None, version=version, change=change, owners=owners,
                 route_task=route_task, route_keys=_route_keys(route_task) if route_task and route_task != task else None,
                 closers=closers, register_change=register_change, task_profile=profile_digest(table), suspect_scope=scope,
                 corpus=corpus_digest(st.version_digests()), inputs=load_inputs(st))
    return with_differs(rep, baseline)


def with_differs(rep: dict, baseline: tuple[dict, str] | None) -> dict:
    """task-0320 (decision-0038 N3): what moved, on both readers, computed once (``differs``) into ``baseline.differs``."""
    if baseline:
        rep["baseline"]["differs"] = differs(baseline[0].get("identity"), rep)
    return rep


def load_inputs(st) -> dict:
    """``{attestations, captures, configuration, code, preload}``: the digests of what the load used beyond the
    documents, as the store recorded them at load (``Store.inputs``, task-0320, decision-0038 N2; configuration,
    task-0335; code and preload, task-0341); each None on
    a store loaded before it, or a view without the read, read as unknown."""
    try:
        got = st.inputs()
    except (AttributeError, NotImplementedError):
        got = {}
    return {k: got.get(k) for k in NO_INPUTS}


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
    ap.add_argument("--scenario", help="the scenario to load (default: the subject's first; with --no-load, the one the store holds)")
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
