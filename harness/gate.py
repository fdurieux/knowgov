"""The gate (pre-registration §6): required keys -> levels, flags,
verdict, evidence bundle. Reads through the store port."""

from __future__ import annotations

from tasks import TASKS

ORDER = ["absent", "declared_gap", "disputed", "invalidated", "proposed", "validated", "verified", "approved"]
BETTER = ("validated", "verified", "approved")
LIVE = ["proposed", "validated", "verified", "approved", "disputed", "invalidated"]


def resolve(s, task: str) -> dict:
    spec = TASKS[task]
    keys = {}
    for key in spec["keys"]:
        rows, pending = s.key_evidence(key, LIVE), []
        ent = key.split("|")[0]
        declared = s.declared_gaps_for_key(key)
        if not rows:
            level = "declared_gap" if declared else "absent"
        elif declared:
            level = "declared_gap"
        else:
            # an invalidated assertion is superseded only by a verified or
            # approved replacement on the same key; until then it blocks
            replaced = any(r["status"] in ("verified", "approved") for r in rows)
            live_rows = [r for r in rows if not (r["status"] == "invalidated" and replaced)]
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
        if rows and all(r["basis"] in ("inferred", "assumed", "hypothesised") for r in rows):
            flags.add(next(iter({r["basis"] for r in rows})))
        keys[key] = {"level": level, "flags": sorted(flags), "assertions": rows, "declared_gaps": declared,
                     "pending_review": pending}
    n = len(keys)
    blocked_keys = [k for k, v in keys.items() if v["level"] in spec["block_levels"]]
    below = [k for k, v in keys.items() if ORDER.index(v["level"]) < ORDER.index("verified")]
    flagged = [k for k, v in keys.items() if v["flags"]]
    if blocked_keys:
        verdict, why = "BLOCKED", f"{len(blocked_keys)} required key(s) at a blocking level: " + ", ".join(f"{k} ({keys[k]['level']})" for k in blocked_keys)
    elif len(below) / n > spec["max_unverified_share"]:
        verdict, why = "BLOCKED", f"{len(below)} of {n} required keys ({len(below)/n:.0%}) are below verified; the bar is {spec['max_unverified_share']:.0%}"
    elif below or flagged:
        verdict, why = "QUALIFIED", f"{len(below)} key(s) below verified, {len(flagged)} flagged: " + ", ".join(sorted(set(below) | set(flagged)))
    else:
        verdict, why = "PROCEED", f"all {n} required keys verified or approved, none flagged"
    conflicts = s.conflict_gaps()
    # staleness: invalidated assertions on required keys (superseded or not), the verifications
    # their invalidation ended, and the derived outputs that used them (S6; added after the first
    # scored run, whose S6 bundle carried none of this - see the pre-registration's run notes)
    stale = s.stale_on_keys(spec["keys"])
    suspect = s.suspect_derived()
    return {"task": task, "verdict": verdict, "why": why, "keys": keys, "conflicts": conflicts,
            "blocked_keys": blocked_keys, "below_verified": below, "flagged": flagged,
            "stale": stale, "suspect_derived": suspect}


def render_key(key: str, v: dict) -> list[str]:
    """One key's section of the bundle: its level and flags, its declared gaps, every live assertion
    with evidence, verification, approval and gaps. The pull context serves it on read_knowledge."""
    out = [f"\n## {key}  level={v['level']}  flags={','.join(v['flags']) or '-'}"]
    for g in v["declared_gaps"]:
        out.append(f"  DECLARED GAP {g['id']}: {g['text']}")
    if not v["assertions"]:
        out.append("  (no assertion in the repository: UNKNOWN — not a documented absence)")
    for a in v["assertions"]:
        out.append(f"  [{a['id']}] value={a['value']!r} basis={a['basis']} status={a['status']} source={a['artefact']} by={a['agent']}"
                   + ("  PENDING REVIEW: not counted in the level (decision-0004)" if a["id"] in v.get("pending_review", ()) else ""))
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
        out.append("\nINVALIDATED BY A SOURCE CHANGE: " + ", ".join(x.get("key", "") for x in res["stale"]))
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


def render_bundle(res: dict, policy: str, verbatim: dict[str, str] | None = None) -> str:
    out = [f"GATE VERDICT: {res['verdict']} — {res['why']}", "", "POLICY:", policy, "",
           "REQUIRED KNOWLEDGE, key by key (status is the knowledge repository's, not yours to upgrade):"]
    for key, v in res["keys"].items():
        out.extend(render_key(key, v))
    if res["conflicts"]:
        out.append("\nCONFLICTS:")
        for c in res["conflicts"]:
            out.append(f"  {c['id']}: {c['text']}")
    if res.get("stale"):
        out.append("\nINVALIDATED BY A SOURCE CHANGE (their verifications ended; a successor, if any, is listed with its own status):")
        for x in res["stale"]:
            succ = ", ".join(f"{t['id']} value={t['value']!r} status={t['status']}" for t in x["successors"] if t["id"]) or "none"
            vers = ", ".join(f"{v['id']} valid_until={v['valid_until']}" for v in x["verifications"] if v["id"]) or "none"
            out.append(f"  [{x['id']}] key={x['key']} old value={x['value']!r} invalidated_by={x['invalidated_by']}; verifications: {vers}; successor: {succ}")
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
