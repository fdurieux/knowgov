"""The gate (pre-registration §6): required keys -> levels, flags,
verdict, evidence bundle. Reads through the store port."""

from __future__ import annotations

import cadence
from tasks import TASKS

ORDER = ["absent", "declared_gap", "disputed", "invalidated", "proposed", "validated", "verified", "approved"]
BETTER = ("validated", "verified", "approved")
LIVE = ["proposed", "validated", "verified", "approved", "disputed", "invalidated"]


def resolve(s, task: str, as_of=None) -> dict:
    return resolve_spec(s, task, TASKS[task], as_of)


INFERENCE = ("inferred", "assumed", "hypothesised")


def inference_flags(rows: list[dict]) -> set[str]:
    """A key whose every statement rests on inference carries each basis among them as a flag (task-0244,
    doc-0033 R3): every one, so the sorted flags never depend on a set's iteration order (PYTHONHASHSEED).
    A key with any other basis, or none, carries none of them."""
    return {r["basis"] for r in rows} if rows and all(r["basis"] in INFERENCE for r in rows) else set()


def _suspect_note(suspect: list, verdict: str) -> str:
    """A-N4: the verdict does not weigh a suspect output, and the CLI exits 1 on it."""
    return f"; {len(suspect)} derived output(s) suspect (listed as findings, which can fail the run)" if suspect and verdict == "PROCEED" else ""


def resolve_spec(s, task: str, spec: dict, as_of=None) -> dict:
    """The gate over any key set: ``spec`` is a task's shape (keys, block_levels,
    max_unverified_share); ``task`` only names it in the result. The MCP server resolves an
    agent's own key set through here, so it is never a second gate.

    ``as_of`` is the date review currency is read on (decision-0005, harness/cadence.py): a date, or
    ``today``, or ``record`` (the subject's pinned record date); None is ``record``, so the record's
    producers read as the record was made, and the gate command passes today. A statement whose review
    has lapsed by then reads ``validated``, with its approval, and is listed in ``lapsed``."""
    on = cadence.as_of("record" if as_of is None else as_of)
    keys, lapsed = {}, []
    # one successor set (task-0201, doc-0030 G3): an invalidated statement is superseded only by its own
    # verified or approved successor (superseded_by over stale_on_keys), the reading the stale finding,
    # superseded_by and the bundle make, so the gate's level never drops what they still call unreplaced
    stale = s.stale_on_keys(spec["keys"])
    register_staled = _register_staled(s, stale)
    superseded = {x["id"] for x in stale if superseded_by(x)}
    for key in spec["keys"]:
        rows, pending = s.key_evidence(key, LIVE), []
        for r in rows:
            gone = cadence.lapse(r, key, on)
            if gone:
                r["status"], r["lapsed"] = gone["to"], gone   # what it reads as of the date (task-0198)
                lapsed.append(gone)
        ent = key.split("|")[0]
        declared = s.declared_gaps_for_key(key)
        if not rows:
            level = "declared_gap" if declared else "absent"
        elif declared:
            level = "declared_gap"
        else:
            # an invalidated assertion is superseded only by its own verified or approved successor
            # (superseded_by); until then it blocks (a successor whose own review has since lapsed still
            # superseded it: the change is history, and superseded_by reads the stored status)
            replaced = any(r["status"] == "invalidated" and r["id"] in superseded for r in rows)
            live_rows = [r for r in rows if not (r["status"] == "invalidated" and r["id"] in superseded)]
            # decision-0004: a person's answer nobody has reviewed yet (elicited, proposed) does not
            # lower a key that holds a validated-or-better statement; it stays in the bundle, marked
            # pending review. One that contradicts is disputed by R-CONFLICT, and that counts.
            if any(r["status"] in BETTER for r in live_rows):
                pending = [r["id"] for r in live_rows if r["basis"] == "elicited" and r["status"] == "proposed"]
            counted = [r for r in live_rows if r["id"] not in pending]
            level = min((r["status"] for r in counted), key=ORDER.index)
            if replaced:
                rows = live_rows
        flags = set()
        if any(g["kind"] == "ambiguous" for r in rows for g in r["gaps"]):
            flags.add("ambiguous")
        flags |= inference_flags(rows)
        keys[key] = {"level": level, "flags": sorted(flags), "assertions": rows, "declared_gaps": declared,
                     "pending_review": pending}
    n = len(keys)
    blocked_keys = [k for k, v in keys.items() if v["level"] in spec["block_levels"]]
    below = [k for k, v in keys.items() if ORDER.index(v["level"]) < ORDER.index("verified")]
    flagged = [k for k, v in keys.items() if v["flags"]]
    # the intended bar (task-0215, decision-0018 point 4): a class that requires approved reads a key verified
    # but not approved, an observed behaviour nobody has intended, below its bar, under the same blocking rule
    # as a key below verified; a class that does not declare it reads as before
    intended = spec.get("require_approved") is True
    unintended = [k for k, v in keys.items() if v["level"] == "verified"] if intended else []
    under = below + unintended
    bar = "approved" if intended else "verified"
    if blocked_keys:
        verdict, why = "BLOCKED", f"{len(blocked_keys)} required key(s) at a blocking level: " + ", ".join(f"{k} ({keys[k]['level']})" for k in blocked_keys)
    elif len(under) / n > spec["max_unverified_share"]:
        verdict, why = "BLOCKED", f"{len(under)} of {n} required keys ({len(under)/n:.0%}) are below {bar}; the bar is {spec['max_unverified_share']:.0%}"
    elif under or flagged:
        verdict, why = "QUALIFIED", f"{len(under)} key(s) below {bar}, {len(flagged)} flagged: " + ", ".join(sorted(set(under) | set(flagged)))
    else:
        verdict, why = "PROCEED", (f"all {n} required keys approved, none flagged" if intended
                                   else f"all {n} required keys verified or approved, none flagged")
    conflicts = s.conflict_gaps()
    suspect = s.suspect_derived()
    why += _suspect_note(suspect, verdict)
    # staleness: invalidated assertions on required keys (superseded or not), the verifications
    # their invalidation ended, and the derived outputs that used them (S6; added after the first
    # scored run, whose S6 bundle carried none of this - see the pre-registration's run notes);
    # ``stale`` is read above, once, so the level and the finding read one successor set
    out = {"task": task, "verdict": verdict, "why": why, "keys": keys, "conflicts": conflicts,
           "blocked_keys": blocked_keys, "below_verified": below, "flagged": flagged,
           "stale": stale, "suspect_derived": suspect, "lapsed": lapsed, "as_of": on.isoformat(),
           "register_staled": register_staled}
    if intended:   # task-0215: only when the class declares the bar, so every other class and the record read as before
        out["unintended"] = unintended
    lint = lint_behind(s, keys)
    if lint is not None:   # task-0216: only when a load recorded lint gaps; absent otherwise, so the record reads as before
        out["lint"] = lint
    form = preload_behind(s, keys)
    if form is not None:   # only when a load recorded verdicts (task-0064); absent otherwise, so the record reads as before
        out["preload"] = form
    attest = attestation_behind(s, keys)
    if attest:   # decision-0019 (task-0221): absent when the subject declares no attestation, so the record reads as before
        out["attestation"] = attest
    acts = acts_not_applied(s)
    if acts:   # task-0199: a person's act the load did not apply as written; absent otherwise, so the record reads as before
        out["acts"] = acts
    return out


def attestation_behind(s, keys: dict) -> list[dict]:
    """How the load read each ``[verification]`` declaration (decision-0019): {declaration, bound, attester,
    unattested: [{artefact, sha256, parts, keys}]}, each unattested artefact with the required keys whose
    statements come from it (none: the artefact is behind no key of this task, and is left out). Empty on a store
    view without the read, or when the subject declares no attestation."""
    import json
    try:
        rows = s.attestations()
    except (AttributeError, NotImplementedError):
        return []
    from subject import SUBJECT   # the read rule: a declaration with no versions, read from the manifest, never stored
    held = {r["declaration"] for r in rows}
    # task-0330 H2: a declaration listing no Version names each document and its digest, as the edited-document finding does
    try:
        docs = json.dumps([{"artefact": v["artefact"], "sha256": v["sha256"], "parts": []} for v in s.version_digests()
                           if v.get("sha256")], sort_keys=True)
    except (AttributeError, NotImplementedError):
        docs = "[]"
    rows = rows + [{"declaration": n, "bound": False, "attester": "", "unattested": docs if n in ("execution", "review") else "[]"}
                   for n in ("approval", "authored", "execution", "review")
                   if n not in held and isinstance(SUBJECT.verification.get(n), dict) and SUBJECT.verification[n].get("versions") is None]
    behind: dict[str, set] = {}
    for key, k in keys.items():
        for r in k["assertions"]:
            if r.get("artefact"):
                behind.setdefault(r["artefact"], set()).add(key)
    out = []
    for r in sorted(rows, key=lambda r: r["declaration"]):
        rows_un = json.loads(r.get("unattested") or "[]")
        un = [{**u, "keys": sorted(behind[u["artefact"]])} for u in rows_un if not u.get("code") and u["artefact"] in behind]
        # task-0320 (decision-0038 N-b): the implementation or suite an execution ran on, unlisted, voids it whole; named
        # with the task's keys it would have verified (none: still named, at info)
        un += [{**u, "keys": sorted(set(u.get("keys") or []) & set(keys))} for u in rows_un if u.get("code")]
        out.append({"declaration": r["declaration"], "bound": bool(r["bound"]), "attester": r.get("attester") or "", "unattested": un})
    return out


def acts_not_applied(s) -> list[dict]:
    """The store's ``act_findings`` with ``to`` and ``reasons`` read back from their JSON text; empty on a store
    view without the read."""
    import json
    try:
        rows = s.act_findings()
    except (AttributeError, NotImplementedError):
        return []
    return [{**r, "to": json.loads(r.get("to") or "[]"), "reasons": json.loads(r.get("reasons") or "[]")} for r in rows]


def preload_behind(s, keys: dict) -> list[dict] | None:
    """The documents behind the keys' live statements (artefact and version) whose pre-load verdict is
    unchecked or has findings; None when the store holds no verdict at all."""
    try:
        held = s.preload_verdicts()
    except (AttributeError, NotImplementedError):   # a store view without the read holds no verdict
        return None
    verdicts = {(v["artefact"], v["version"]): v for v in held}
    if not verdicts:
        return None
    behind: dict[tuple, set] = {}
    for key, k in keys.items():
        for r in k["assertions"]:
            if r.get("artefact") and "@" in r["id"]:
                behind.setdefault((r["artefact"], r["id"].rsplit("@", 1)[1]), set()).add(key)
    out = []
    for (art, ver), ks in sorted(behind.items()):
        v = verdicts.get((art, ver))
        state = v["state"] if v else "unchecked"
        if state in ("unchecked", "findings", "held"):
            out.append({"artefact": art, "version": ver, "state": state, "tool": v["tool"] if v else None,
                        "why": (v["why"] if v else "no verdict recorded for this version"), "keys": sorted(ks)})
    return out


def lint_behind(s, keys: dict) -> list[dict] | None:
    """The lint gaps (task-0216, decision-0018 point 5) on the document versions behind the keys' live statements,
    each with the keys it lies behind; None when the store holds no lint gap at all, so a load without a pre-load
    report reads exactly as before. A lint gap is the document's form: it never lowers a key's level."""
    try:
        held = s.lint_gaps()
    except (AttributeError, NotImplementedError):   # a store view without the read holds none
        return None
    if not held:
        return None
    behind: dict[tuple, set] = {}
    for key, k in keys.items():
        for r in k["assertions"]:
            if r.get("artefact") and "@" in r["id"]:
                behind.setdefault((r["artefact"], r["id"].rsplit("@", 1)[1]), set()).add(key)
    return [{**g, "keys": sorted(behind[(g["artefact"], g["version"])])} for g in held if (g["artefact"], g["version"]) in behind]


THREE_VALUED_STATUSES = ["verified", "approved", "validated", "proposed", "disputed"]   # disputed: task-0201, doc-0030 M4
SETTLED = ("verified", "approved")   # a successor at one of these supersedes an invalidated statement


def superseded_by(stale: dict) -> list[str]:
    """The verified or approved successors of one invalidated statement, as ``stale_on_keys`` lists
    them (task-0071): superseded is this reading, never a stored status. Empty when none replaces it,
    and the statement then still blocks its key."""
    return sorted({t["id"] for t in stale.get("successors") or [] if t.get("id") and t.get("status") in SETTLED})


def superseded_map(res: dict) -> dict[str, list[str]]:
    """{invalidated statement id: its verified or approved successors} over a gate result's stale
    statements, for those a successor supersedes."""
    return {x["id"]: ids for x in res.get("stale") or [] if (ids := superseded_by(x))}


def _register_staled(s, rows: list[dict]) -> list[str]:
    """L-e: the ids of the statements a register update staled, as ``register_change`` wrote the reason ("the register ..."),
    told from a source change's by the reason not being a Version tag the store holds: a stage-2 ``version`` is free text
    and could read the same, but it is always the tag of a Version the store holds."""
    tags = {v["version"] for v in s.version_digests()} if rows and hasattr(s, "version_digests") else set()
    return sorted(x["id"] for x in rows if str(x.get("invalidated_by") or "").startswith("the register")
                  and str(x.get("invalidated_by")) not in tags)


def invalidated_on_key(s, key: str) -> list[dict]:
    """The invalidated statements on one key, each naming its ``superseded_by`` (empty when nothing
    replaces it): what the three-valued answer adds so an agent that sees a successor knows what
    it replaced, and one that sees none knows the old value no longer holds."""
    return [{"id": x["id"], "value": x["value"], "invalidated_by": x["invalidated_by"], "superseded_by": superseded_by(x)}
            for x in sorted(s.stale_on_keys([key]), key=lambda x: x["id"])]


def _plain(x: dict) -> bool:
    """A document's review lapse, the one kind before task-0198: its lines render as they always did (the bundle's bytes)."""
    return not x.get("after") and x.get("kind") != "elicited"


def _lapse_note(x: dict) -> str:
    return (f"{x['from']} until {x['valid_until']}, now validated (decision-0005)" if _plain(x)
            else cadence.describe(x, "the date read"))


def three_valued(s, key: str) -> dict:
    """The three-valued answer for one key (D5): ``unknown`` when no assertion exists,
    ``documented_absent`` when every live assertion says NONE, else ``asserted``. A disputed statement is
    live (task-0201, doc-0030 M4): a key the documents disagree on is not unknown. Its statements are read,
    and ``disputed`` names them, with ``why``: the answer is the documents', and they do not agree."""
    rows = s.assertions_on_key(key, THREE_VALUED_STATUSES)
    if not rows:
        return {"answer": "unknown", "why": "no assertion for this key (not a documented absence)"}
    out = {"answer": "documented_absent" if all(r["value"] == "NONE" for r in rows) else "asserted", "assertions": rows}
    disputed = sorted(r["id"] for r in rows if r.get("status") == "disputed")
    if disputed:   # absent otherwise, so the record's answers read as before
        values = sorted({str(r["value"]) for r in rows if r.get("status") == "disputed"})
        out["disputed"] = disputed
        out["why"] = (f"{len(disputed)} statement(s) disputed: the documents disagree ({'; '.join(repr(v) for v in values)}); "
                      "none of them holds until a review settles the dispute")
    return out


BUNDLE_FORMS = ("full", "compact")   # task-0140: full is the default and the record's form


def render_key(key: str, v: dict, form: str = "full") -> list[str]:
    """One key's section of the bundle: its level and flags, its declared gaps, every live assertion
    with evidence, verification, approval and gaps. The pull context serves it on read_knowledge.
    ``compact`` (task-0140, doc-0019 C3) keeps the header, the declared gaps, each assertion line and
    its gaps, and drops the text, evidence, verification and approval lines."""
    if form not in BUNDLE_FORMS:
        raise ValueError(f"bundle form {form!r}: one of {', '.join(BUNDLE_FORMS)}")
    full = form == "full"
    out = [f"\n## {key}  level={v['level']}  flags={','.join(v['flags']) or '-'}"]
    for g in v["declared_gaps"]:
        out.append(f"  DECLARED GAP {g['id']}: {g['text']}")
    if not v["assertions"]:
        out.append("  (no assertion in the repository: UNKNOWN — not a documented absence)")
    for a in v["assertions"]:
        out.append(f"  [{a['id']}] value={a['value']!r} basis={a['basis']} status={a['status']} source={a['artefact']} by={a['agent']}"
                   + ("  PENDING REVIEW: not counted in the level (decision-0004)" if a["id"] in v.get("pending_review", ()) else "")
                   + (f"  REVIEW LAPSED: {_lapse_note(a['lapsed'])}" if a.get("lapsed") else ""))
        if full:
            out.append(f"      text: {a['text'][:300]}")
            for f in a["fragments"][:2]:
                out.append(f"      evidence: {f['artefact']} @ {f['locator']}: {f['text'][:200]!r}")
            for ver in a["verifications"]:
                out.append(f"      verification: {ver['method']} ({ver['scope']}) at {ver['at']}" + (f" VALID UNTIL {ver['valid_until']}" if ver['valid_until'] else ""))
            for ap in a["approvals"]:
                out.append(f"      approval: {ap['record']} at {ap['at']}")
        for g in a["gaps"]:
            out.append(f"      GAP {g['kind']}{' (declared)' if g['declared'] else ''}: {g['text']}")
    return out


def render_index(res: dict, policy: str, documents: list[str] | None = None) -> str:
    """The pull context's first message: the verdict, the policy, one line per key (level, flags,
    assertion ids) and the names of the documents read_document serves; the knowledge itself comes
    through read_knowledge(key), one section per call, and every call is logged."""
    out = [f"GATE VERDICT: {res['verdict']} — {res['why']}", "", "POLICY:", policy, "",
           "REQUIRED KNOWLEDGE, an index (status is the knowledge repository's, not yours to upgrade).",
           "Call read_knowledge(key) for a key's assertions, evidence, verification and gaps; each call is recorded as consulted.",
           "key | level | flags | assertion ids"]
    for key, v in res["keys"].items():
        ids = ", ".join(a["id"] for a in v["assertions"]) or "(none: UNKNOWN)"
        out.append(f"{key} | {v['level']} | {','.join(v['flags']) or '-'} | {ids}")
    if res["conflicts"]:
        out.append("\nCONFLICTS:")
        for c in res["conflicts"]:
            out.append(f"  {c['id']}: {c['text']}")
    if res.get("stale"):
        out.append("\nINVALIDATED BY A SOURCE CHANGE: " + ", ".join(
            x.get("key", "") + (f" ({x['id']} superseded_by {', '.join(ids)})" if (ids := superseded_by(x)) else f" ({x['id']} not superseded)")
            for x in res["stale"]))
    if res.get("lapsed"):
        out.append(f"\nREVIEW LAPSED as of {res['as_of']}: " + ", ".join(x["key"] for x in res["lapsed"]))
    if documents:
        out.append("\nDOCUMENTS the task names verbatim; call read_document(path) for each you need:")
        for d in documents:
            out.append(f"  {d}")
    return "\n".join(out)


def knowledge_reader(res: dict):
    """The governed arm's read_knowledge tool over a gate result: ``read(key)`` returns the key's
    section as the bundle renders it, or refuses a key the task does not require; ``ids`` collects
    every assertion id a read returned, in order, so the run can name what the arm consulted."""
    ids: list[str] = []

    def read(key: str) -> str:
        if key not in res["keys"]:
            raise KeyError(f"{key}: not a required key of this task")
        ids.extend(a["id"] for a in res["keys"][key]["assertions"])
        return "\n".join(render_key(key, res["keys"][key]))
    return read, ids


def render_bundle(res: dict, policy: str, verbatim: dict[str, str] | None = None, form: str = "full") -> str:
    """The governed arm's bundle. ``full`` (the default, the record's form) carries every assertion's
    text, evidence, verifications and approvals; ``compact`` (task-0140, doc-0019 C3) only each key's
    header, declared gaps and assertion lines with their gaps, the sections after them unchanged."""
    if form not in BUNDLE_FORMS:
        raise ValueError(f"bundle form {form!r}: one of {', '.join(BUNDLE_FORMS)}")
    intro = ("REQUIRED KNOWLEDGE, key by key (status is the knowledge repository's, not yours to upgrade):" if form == "full" else
             "REQUIRED KNOWLEDGE, key by key, compact: one line per assertion, its text, evidence, verifications and approvals left out "
             "(status is the knowledge repository's, not yours to upgrade):")
    out = [f"GATE VERDICT: {res['verdict']} — {res['why']}", "", "POLICY:", policy, "", intro]
    for key, v in res["keys"].items():
        out.extend(render_key(key, v, form))
    if res["conflicts"]:
        out.append("\nCONFLICTS:")
        for c in res["conflicts"]:
            out.append(f"  {c['id']}: {c['text']}")
    if res.get("stale"):
        out.append("\nINVALIDATED BY A SOURCE CHANGE (their verifications ended; a successor, if any, is listed with its own status):")
        for x in res["stale"]:
            succ = ", ".join(f"{t['id']} value={t['value']!r} status={t['status']}" for t in x["successors"] if t["id"]) or "none"
            vers = ", ".join(f"{v['id']} valid_until={v['valid_until']}" for v in x["verifications"] if v["id"]) or "none"
            sup = ", ".join(superseded_by(x)) or "none: it still blocks its key"
            out.append(f"  [{x['id']}] key={x['key']} old value={x['value']!r} invalidated_by={x['invalidated_by']}; verifications: {vers}; successor: {succ}; superseded_by: {sup}")
    if res.get("lapsed"):
        out.append(f"\nREVIEW LAPSED as of {res['as_of']} (decision-0005: a review falls due after its key's review months; each reads validated until a new review):")
        for x in res["lapsed"]:
            out.append(f"  [{x['id']}] key={x['key']} was {x['from']}, review current until {x['valid_until']}; verifications: {', '.join(x['verifications'])}"
                       if _plain(x) else f"  [{x['id']}] key={x['key']} {cadence.describe(x, res['as_of'])}; verifications: {', '.join(x['verifications']) or 'none'}")
    if res.get("suspect_derived"):
        out.append("\nDERIVED OUTPUTS MARKED SUSPECT (they used assertions that are now invalidated; they may not be reused as they are):")
        for d in res["suspect_derived"]:
            out.append(f"  {d['id']} ({d['kind']}, sha256 {d['sha256'][:12]}...) used: {', '.join(d['used_invalidated'])}")
    if verbatim:
        out.append("\nVERBATIM DOCUMENTS (the scenario's kit, as written; the task names these as needed byte for byte):")
        out.append("  A statement's status is its key's above, not the document's; what no key above covers is not knowledge the repository verified.")
        for path, text in verbatim.items():
            out.append(f"\n=== {path} ===\n{text.rstrip()}\n=== end {path} ===")
    return "\n".join(out)
