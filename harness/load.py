"""Load a scenario's extraction into the store and record provenance.

Graph shape: pumllint kg_experiment/PREREGISTRATION.md §3. Every write goes through the store
port (store.py); the first adapter (store_neo4j.py) holds the Cypher.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import tomllib

from kitio import FAMILY, sha256, pristine
from store import stem
import load_memory
from subject import SUBJECT
from extract import extract_all, short, NONE

STORE = SUBJECT.store_keys        # artefact keys the store holds; the others are documents for the arms only
PROV = SUBJECT.provenance
VER = SUBJECT.verification
HUMAN = {"id": PROV.get("human", {}).get("id", "agent:maintainer"), "name": PROV.get("human", {}).get("name", "maintainer")}
ATTESTER = PROV.get("human", {}).get("id")   # who attests (decision-0009): declared, never the default above (doc-0030 I9)
LLM = {"id": PROV.get("llm", {}).get("id", "agent:llm"), "name": PROV.get("llm", {}).get("name", "model")}
TOOL = PROV.get("harness_name", "harness")

SYMBOL_RE = re.compile(r"^[A-Z][A-Z_]+$")


def now() -> str:
    """The load's provenance stamp: KG_TODAY at midnight UTC when a run pins the day (task-0075), so a
    review the subject leaves undated is dated by the pinned day; else the wall clock, which no outcome
    of a pinned run reads."""
    v = os.environ.get("KG_TODAY")
    if v:
        return dt.datetime.combine(dt.date.fromisoformat(v), dt.time(), dt.timezone.utc).isoformat(timespec="seconds")
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def symbol_table(kit: dict[str, str]) -> dict[str, str]:
    """ACCEPT_MAX = 41 etc. from the symbolic-names sentence of the subject's
    decision-table artefacts; empty when the sentence is absent."""
    text = "\n".join(kit.get(k, "") for k, (family, _fmt) in FAMILY.items() if family == "decision_tables")
    return dict(re.findall(r"`([A-Z_]+) = (\d+)`", text))


def resolve_symbols(bags, symbols: dict[str, str]) -> list[dict]:
    """A symbolic value is replaced by its definition when one exists;
    otherwise it stays and is marked unresolved (R-VAGUE flags it)."""
    unresolved = []
    for bag in bags:
        for a in bag.assertions:
            v = a["value"]
            if SYMBOL_RE.match(v) and v != NONE:
                a["raw_value"] = v
                if v in symbols:
                    a["value"] = symbols[v]
                else:
                    a["unresolved"] = True
                    unresolved.append(a["id"])
    return unresolved


def _artefact_of(kit: dict[str, str], bag) -> str:
    return next(p for p in kit if p in FAMILY and bag.artefact == short(p))


def load_scenario(st, scenario: str, kit: dict[str, str], *, activity_note: str,
                  version_tag: str = "v1", reingest: bool = False, changed: set[str] | None = None) -> dict:
    """Write artefacts, versions, fragments, entities, assertions and the
    provenance activity. Returns counts and the unresolved symbols.

    ``reingest`` (stage 2, task-0197): ``kit`` is the whole later kit, extracted whole so a symbol resolves
    from every document (I5); ``changed`` names the artefacts whose bytes changed (default: every one), and
    only those get a new version and count their fragments. A statement is diffed by its id stem against the
    one the store holds, whatever its status: unchanged in value and in fragment set, it writes nothing; else
    it gets a successor in ``version_tag`` (I6), even on an artefact whose bytes did not change (a value
    resolved through a changed symbol). R-STALE then invalidates what the successors replace."""
    code = SUBJECT.reference_code()
    bags = extract_all(kit, code)
    if reingest:
        changed = set(kit) if changed is None else set(changed)
        changed |= {_artefact_of(kit, b) for b in bags if not all(
            st.find_fragment(_artefact_of(kit, b), f["locator"], sha256(f["text"])) for f in b.fragments)}   # a fragment the store lacks
    mine = (lambda b: not reingest or _artefact_of(kit, b) in changed)   # noqa: E731 — the bags whose artefact gets a version
    load_memory.note(st, load_memory.statements([b for b in bags if mine(b)]))   # task-0176: refused here, before the first write, when it would not fit
    unresolved = resolve_symbols(bags, symbol_table(kit))
    if reingest:   # as before, the re-ingested files' own
        own = {a["id"] for b in bags if mine(b) for a in b.assertions}
        unresolved = [x for x in unresolved if x in own]
    before = {}
    if reingest:   # what the store holds, by id stem, before this load writes: the diff's other side
        for p in kit:
            if p in FAMILY and p in STORE:
                for r in st.artefact_assertions(p):
                    if r["artefact"] == p:
                        before[stem(r["id"])] = r
    ts = now()
    aid = f"act:extract:{scenario}:{version_tag}"
    st.ensure_agents(TOOL, version_tag, HUMAN, LLM)
    st.create_activity(aid, "extraction", ts, TOOL, activity_note, "agent:harness", subject=SUBJECT.id, scenario=scenario)   # task-0195
    n_frag = n_ass = n_reused = 0
    for path, text in kit.items():
        if path not in FAMILY or path not in STORE or (reingest and path not in changed):
            continue
        family, fmt = FAMILY[path]
        digest, size = SUBJECT.version_digest(path, text)   # a file artefact's raw bytes, as the register digests them (task-0160)
        st.upsert_artefact_version(path, family, fmt, f"V:{path}:{version_tag}", digest, size, ts, version_tag, aid)
        if path.endswith("/"):   # a directory artefact: its digest is the bundle's, so each file's is kept too (task-0094)
            st.record_part_digests(f"V:{path}:{version_tag}", SUBJECT.part_digests(path, text))
    preload = _record_preload(st, {p: t for p, t in kit.items() if not reingest or p in changed}, version_tag)
    for bag in bags:
        art = _artefact_of(kit, bag)
        versioned = mine(bag)   # an artefact whose bytes changed gets this version; another's fragments are its own still
        vid = f"V:{art}:{version_tag}"
        fmap: dict[str, str] = {}
        reused: set[str] = set()
        locator = {f["id"]: f["locator"] for f in bag.fragments}
        for f in bag.fragments:
            existing = st.find_fragment(art, f["locator"], sha256(f["text"])) if reingest else None
            if existing:
                if versioned:
                    st.link_fragment(vid, existing)
                    n_reused += 1
                fmap[f["id"]] = existing
                reused.add(f["id"])
                continue
            fid = f["id"] + f"@{version_tag}"
            st.create_fragment(vid, fid, f["locator"], sha256(f["text"]), f["text"], art)
            fmap[f["id"]] = fid
            n_frag += 1
        for e in bag.entities.values():
            st.ensure_entity(e["id"], e["kind"], e["name"])
        for a in bag.assertions:
            if reingest and a["fragments"] and all(f in reused for f in a["fragments"]):
                prev = before.get(a["id"])
                if prev is None or (prev["value"] == a["value"]
                                    and {x["locator"] for x in prev["fragments"]} == {locator[f] for f in a["fragments"]}):
                    continue  # the statement and its evidence are unchanged: no new assertion
            basis_agent = HUMAN["id"] if a["basis"] == "authored" else "agent:harness"
            st.create_assertion({"id": a["id"] + f"@{version_tag}", "predicate": a["predicate"], "value": a["value"],
                                 "raw_value": a.get("raw_value"), "text": a["text"], "basis": a["basis"], "status": "proposed",
                                 "artefact": art, "key": f"{a['entity']}|{a['predicate']}", "unresolved": a.get("unresolved", False),
                                 "version": version_tag},
                                a["entity"], aid, basis_agent, [fmap[f] for f in a["fragments"]])
            n_ass += 1
    st.link_mentions()   # the fragments MENTION the entities their assertions are about
    # a document the store holds that no mapper reads yields no statement: said, never skipped silently
    # (task-0006); the key appears only when there is one, so a run with none reads as before
    unmapped = [p for p in kit if p in FAMILY and p in STORE and p not in SUBJECT.mappers]
    return {"fragments": n_frag, "fragments_reused": n_reused, "assertions": n_ass,
            "unresolved_symbols": unresolved, "activity": aid, **({"unmapped": unmapped} if unmapped else {}),
            **({"preload": preload} if preload else {})}


def _record_preload(st, kit: dict[str, str], version_tag: str) -> dict | None:
    """The pre-load check's verdict on each version just loaded (task-0064; harness/preload.py), when
    the subject has a report; None, and nothing recorded, when it has none."""
    import preload
    path = preload.report_path(SUBJECT)
    if path is None:
        return None
    report = preload.read_report(path)
    keys = [p for p in kit if p in FAMILY and p in STORE]
    found = preload.verdicts(SUBJECT, kit, keys, report, path.name)
    gaps = {}
    for key, v in found.items():
        st.record_preload(f"V:{key}:{version_tag}", v)
        gaps[key] = preload.lint_gaps(key, version_tag, v)   # task-0216: each finding a gap, owned through its keys
        for g in gaps[key]:
            st.record_lint_gap(g)
    return {"report": path.name, "documents": [{"artefact": k, "version": version_tag, **{f: v[f] for f in ("state", "tool", "tool_version", "why")},
                                                "lint_gaps": len(gaps[k])} for k, v in sorted(found.items())]}


def load_inferred(st, scenario: str, inferred: dict):
    """One model-proposed assertion (the subject's ``[inferred]`` plant), attributed to the llm
    agent, linked to the open decision it claims to resolve, with no supporting fragment."""
    st.create_inferred({"id": inferred["id"] + "@v1", "predicate": inferred["predicate"], "value": inferred["value"],
                        "text": inferred["text"], "artefact": "llm", "key": f"{inferred['entity']}|{inferred['predicate']}", "version": "v1"},
                       inferred["entity"],
                       {"id": f"act:infer:{scenario}", "at": PROV.get("inference_at", now()), "tool": PROV.get("inference_tool", "model"), "note": inferred["note"]},
                       LLM["id"], inferred["candidate_for"])


def pristine_values() -> dict[str, set[str]]:
    """key -> values the pristine kit states (what the suite and the review
    record verified). Computed from the pristine kit's extraction."""
    kit = pristine()
    code = SUBJECT.reference_code()
    bags = extract_all(kit, code)
    resolve_symbols(bags, symbol_table(kit))
    out: dict[str, set[str]] = {}
    for bag in bags:
        for a in bag.assertions:
            out.setdefault(f"{a['entity']}|{a['predicate']}", set()).add(a["value"])
    return out


def execution_map(kit: dict[str, str] | None) -> dict[str, list[str]]:
    """suite scenario -> the keys it verifies. The subject's static map (``[verification] map``),
    or, when ``[verification] derive_execution`` is set, derived from the kit of the scenario at
    hand: every assertion with ``from_predicate`` (say ``verified_by``) names, in its value, the
    suite scenarios that verify its entity's ``key_predicate`` (say ``statement``), separated by
    ``separator``. A scenario the plant removed from the kit then verifies nothing."""
    d = VER.get("derive_execution")
    if not d or kit is None:
        return dict(SUBJECT.verification_map().get("execution", {}))
    sep = d.get("separator", "; ")
    out: dict[str, list[str]] = {}
    for bag in extract_all(kit, SUBJECT.reference_code()):
        for a in bag.assertions:
            if a["predicate"] == d["from_predicate"]:
                for suite_scenario in (v.strip() for v in a["value"].split(sep) if v.strip()):
                    out.setdefault(suite_scenario, []).append(f"{a['entity']}|{d['key_predicate']}")
    return out


def load_verifications(st, scenario: str, pristine: dict[str, set[str]], kit: dict[str, str] | None = None) -> dict:
    """Execution and review verifications of the live assertions whose
    (key, value) the pristine kit states; then the owner's approval of
    every verified assertion. Skipped by the caller for a scenario declared
    ``verifications = false``. A subject with no verification map verifies nothing.

    decision-0009 (a): the authored-by-construction review runs only when the manifest declares
    ``[verification] authored``, and the approval only when it declares ``approval``. The declaration
    is a person's attestation; without it, authored statements stay proposed and verified ones are
    not approved. No default stands in for a person."""
    vmap = SUBJECT.verification_map()
    execution = execution_map(kit)
    ts = now()
    counts = {"execution": 0, "review": 0, "approved": 0}
    smoke_digest = sha256(SUBJECT.reference_code())
    review, authored, approval = attestation("review"), attestation("authored"), attestation("approval")
    for suite_scenario, keys in execution.items():
        for key in keys:
            counts["execution"] += st.verify_by_execution(
                key, sorted(pristine.get(key, set())), suite_scenario,
                VER.get("execution_scope", "suite scenario {scenario}").format(scenario=suite_scenario), ts, smoke_digest)
    for key in vmap.get("review", {}).get("keys", []) if review else []:
        counts["review"] += st.verify_by_review(key, sorted(pristine.get(key, set())), review["at"], review.get("scope", "review"), ATTESTER)
    # requirements and links: reviewed by construction, only where the subject attests it (decision-0009), on the
    # day it names and by the person it names (task-0199, doc-0030 I9): never the load's day, never a default
    if authored:
        counts["review"] += st.verify_authored(authored["at"], authored.get("scope", "authored"), ATTESTER)
    if approval:
        counts["approved"] = st.approve_verified(approval["at"], approval.get("record", "approval"), ATTESTER)
    # decision-0005: every review falls due after its key's review months; the date is the verification's
    # valid_until, which the gate reads as of a date (harness/cadence.py). Not counted: the record's counts stand.
    import cadence
    cadence.date_reviews(st)
    return counts


def _day(v) -> str | None:
    """``v`` as the ISO date (or instant) it names, or None when it names none."""
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    try:
        dt.date.fromisoformat(str(v)[:10])
        return str(v)
    except ValueError:
        return None


def attestation(name: str, table: dict | None = None) -> dict | None:
    """``[verification] <name>`` (or ``table``, a stage-2 re-verification) as a person's attestation, or None when
    the subject declares none or declares one the load may not apply (task-0199, doc-0030 I9): with no ``at`` it
    would be dated by each load's day and never lapse, and with no ``[provenance] human`` id it would be no one's.
    ``check_subject`` refuses both; the load says so on stderr and applies neither."""
    import sys
    a = VER.get(name) if table is None else table
    if not a:
        return None
    at = _day(a.get("at"))
    missing = [w for w, ok in (("date (at)", at), ("attester ([provenance] human id)", ATTESTER)) if not ok]
    if missing:
        print(f"attestation not applied: {name} has no {' and no '.join(missing)} (doc-0030 I9; tools/check_subject.py refuses it)",
              file=sys.stderr)
        return None
    return {**a, "at": at}


def load_captures(st, scenario: str) -> dict:
    """Every capture in the subject's capture folder (harness/capture.py ingest; task-0009): an
    answer becomes an assertion of basis ``elicited`` at status proposed, attributed to the person's
    handle and dated; "nobody knows" becomes a declared gap on the key, with the person and the
    date. The verifications never touch basis elicited, so nothing here rises above proposed."""
    files = sorted(SUBJECT.capture_dir.glob("*.toml")) if SUBJECT.capture_dir.is_dir() else []
    counts = {"files": [], "answers": 0, "unknown": 0}
    for p in files:
        c = tomllib.loads(p.read_text(encoding="utf-8"))
        cap = c.get("capture", {})
        handle, on, record = cap["from"], str(cap["on"]), cap["record"]
        person, aid = f"person:{handle}", f"act:capture:{p.stem}"
        st.ensure_person(person, handle)
        st.create_activity(aid, "elicitation", on, "questionnaire", f"answers from {handle} on {on}, owner {cap.get('owner', '')}, {record}", person)
        for i, a in enumerate(c.get("answer", []), 1):
            ent, pred = a["key"].split("|", 1)
            st.ensure_entity(ent, "elicited", ent)
            st.create_assertion({"id": f"A:cap:{p.stem}:{i}@capture", "predicate": pred, "value": a["value"],
                                 "text": f"{handle} on {on}: {a['value']}" + (f" ({a['note']})" if a.get("note") else ""),
                                 "basis": "elicited", "status": "proposed", "artefact": record, "key": a["key"], "version": "capture"},
                                ent, aid, person, [])
            counts["answers"] += 1
        for i, u in enumerate(c.get("unknown", []), 1):
            ent, pred = u["key"].split("|", 1)
            st.ensure_entity(ent, "elicited", ent)
            xid = f"A:cap:{p.stem}:unknown{i}@capture"
            st.create_assertion({"id": xid, "predicate": pred, "value": "", "text": f"{handle} on {on}: nobody knows",
                                 "basis": "elicited", "status": "proposed", "artefact": record, "key": u["key"], "version": "capture"},
                                ent, aid, person, [])
            st.add_declared_gap(f"gap:declared:capture:{p.stem}:{i}", f"{u['key']}: nobody knows (declared by {handle} on {on}, {record})",
                                ent, xid, scenario, ent, u["key"])
            counts["unknown"] += 1
        counts["files"].append(record)
    inferred = load_inferred_proposals(st)   # route c's candidates (task-0041); none without <capture dir>/inferred/
    if inferred:
        counts["inferred"] = inferred
    return counts


def load_inferred_proposals(st) -> int:
    """A model's candidates from a transcript (harness/transcript.py, route c, task-0041), in
    ``<capture dir>/inferred/``: basis inferred, status proposed, attributed to the model; the
    transcript itself is never here, only its digest. Never promoted (the verifications touch
    extracted and authored statements only)."""
    d = SUBJECT.capture_dir / "inferred"
    n = 0
    for p in sorted(d.glob("*.toml")) if d.is_dir() else []:
        c = tomllib.loads(p.read_text(encoding="utf-8"))
        inf = c.get("inference", {})
        on, model, dig = str(inf.get("on", "")), str(inf.get("model", "model")), str(inf.get("transcript_sha256", ""))[:12]
        for i, x in enumerate(c.get("proposal", []), 1):
            ent, pred = x["key"].split("|", 1)
            st.ensure_entity(ent, "inferred", ent)
            st.create_inferred({"id": f"A:inf:{p.stem}:{i}@transcript", "predicate": pred, "value": x["value"],
                                "text": f"{model} on {on}, reading a transcript (sha256 {dig}): {x['value']}",
                                "artefact": f"transcript:{dig}", "key": x["key"], "version": "transcript"},
                               ent, {"id": f"act:infer:{p.stem}:{i}", "at": on, "tool": model, "note": f"route c, {p.name}"},
                               LLM["id"], None)
            n += 1
    return n


def load_reviews(st, scenario: str, now: dt.date | None = None, again: bool = False) -> dict:
    """Every review in the subject's ``<capture dir>/reviews/`` for this scenario (task-0037,
    decision-0002), after the rules have run: harness/review.py checks each file against the loaded
    store and refuses it whole, with its reasons on stderr; an accepted one applies its rulings
    (approved, rejected), settles the conflicts of the keys whose dispute it settled, and closes the
    declared gaps it names. It reads no clock (task-0198, doc-0030 H3): an approval of a person's statement
    keeps its ``until``, six months after the answer, and the gate decides as of its date whether it is
    current (``cadence.lapse``), so one ``--as-of`` gives one report whatever the day of the load. ``now``,
    when given, refuses a review dated after it, as ``capture.py review`` does on the day it is written.

    Each act binds to content (task-0199, doc-0030 H5, doc-0032 §6): a ruling lands on the statement holding the
    value and digest it records, whatever its id is in this extraction; one whose statement changed or vanished
    is not applied, and every act not applied (a refused file too, and a file from before 0.9.0 bound by id
    only) is recorded in the store, ``record_act_finding``, for the gate to report: never stderr only.
    ``again`` (stage 2, after a re-extraction; task-0222): every review file is read again, as a fresh load of the
    later documents reads it, after the acts stage 1 recorded are cleared. A ruling binds to what the change left
    current, so one whose statement it replaced is reported and one written for the later version applies in
    the same run; a close of a gap stage 1 closed, on the same declaration, is a no-op, and one whose declaration
    changed is reported (``review.check``)."""
    import sys
    import capture
    import review
    from rules import compatible
    rdir = SUBJECT.capture_dir / "reviews"
    files = sorted(rdir.glob("*.toml")) if rdir.is_dir() else []
    counts = {"files": [], "refused": [], "approved": 0, "rejected": 0, "referred": 0, "closed": 0, "settled": 0, "skipped": 0}
    if again:
        st.clear_act_findings()
    if not files:
        return counts
    reg = capture.register_root()
    handles, units = review.issued_handles(reg), review.organisation_units(reg)
    owners = capture.owners_of(SUBJECT, capture.register_nodes(reg))
    caps = review.capture_index(SUBJECT.capture_dir)
    for p in files:
        doc = tomllib.loads(p.read_text(encoding="utf-8"))
        sc = str(doc.get("review", {}).get("scenario", ""))
        if sc and sc != scenario:
            continue
        rel = str(p.relative_to(SUBJECT.root)) if p.is_relative_to(SUBJECT.root) else str(p)
        rid = f"review:{p.stem}"
        errs, rv = review.check(doc, st, handles=handles, owners=owners, units=units, captures=caps, now=now,
                                compatible=compatible, strict=False)
        head = {"review": rel, "by": rv["by"], "on": rv["on"].isoformat() if rv["on"] else str(doc.get("review", {}).get("on", ""))}
        if errs:
            for e in errs:
                print(f"review refused: {rel}: {e}", file=sys.stderr)
            counts["refused"].append(rel)
            st.record_act_finding(_act(f"actf:{rid}", head, "review", 0, "", "", "", "refused", reasons=errs))
            continue
        for x in rv["skipped"]:   # an act whose statement changed or vanished: not applied, and said so (doc-0032 §6 item 7)
            print(f"review act not applied: {rel}: {x['act']} {x['n']} ({x['statement']}): {x['why']}", file=sys.stderr)
            counts["skipped"] += 1
            st.record_act_finding(_act(f"actf:{rid}:{x['act']}:{x['n']}", head, x["act"], x["n"], x["statement"], x["outcome"],
                                       x["key"], x["why"], value=x["value"], sha=x["sha256"], to=x["to"]))
        person, on = f"person:{rv['by']}", rv["on"].isoformat()
        st.ensure_person(person, rv["by"])
        try:
            st.create_activity(f"act:{rid}", "review", on, "review", f"rulings by {rv['by']} on {on}, {rv['record']}, {rel}", person)
        except ValueError:
            if not again:   # store.UNIQUE_IDS: only stage 2 meets a review stage 1 recorded, and keeps that record
                raise
        settled = set()
        for ru in rv["rulings"]:
            b = st.assertion_brief(ru["statement"])
            outcome = ru["outcome"]
            until = review.until_for(b, caps)
            if b["status"] == "disputed":
                settled.add(b["key"])   # the review settled the dispute whole (review.check), lapse or not
            # task-0198 (H3): applied whatever the day; the approval keeps its until, six months after the answer,
            # and the gate reads it lapsed as of its date (cadence.lapse), never the load's day
            st.apply_ruling(b["id"], outcome, rid, person, on, rv["record"], until.isoformat() if until else "")
            counts[outcome] += 1
            if ru["unbound"]:   # the read rule: a file from before 0.9.0 binds by id, and the gate says so
                st.record_act_finding(_act(f"actf:{rid}:ruling:{ru['n']}", head, "ruling", ru["n"], b["id"], outcome, b["key"],
                                           "unbound", to=[{"id": b["id"], "value": ru["value"], "sha256": ru["sha256"]}]))
        for key in sorted(settled):
            counts["settled"] += st.settle_conflicts(key, rid)
        for c in rv.get("resolves", []):   # task-0216: a lint gap's resolution, by its document's owner
            st.resolve_lint_gap(c["gap"], c["resolution"], rid, rv["by"], on, rv["record"], c["note"])
            counts["resolved"] = counts.get("resolved", 0) + 1
        for c in rv["closes"]:
            if c.get("already"):   # task-0222: closed by stage 1 on the same declaration, so closing again is a no-op
                continue
            st.close_declared_gap(c["gap"], rid, on, rv["record"])
            counts["closed"] += 1
            if c["unbound"]:
                st.record_act_finding(_act(f"actf:{rid}:close:{c['n']}", head, "close", c["n"], c["gap"], "closed",
                                           (c["keys"] or [""])[0], "unbound"))
        counts["files"].append(rel)
    return counts


def _act(fid: str, head: dict, act: str, n: int, statement: str, outcome: str, key: str, why: str, *,
         value=None, sha=None, to=(), reasons=()) -> dict:
    """One act the load did not apply as written, as the store keeps it (``record_act_finding``): scalar
    properties only, ``to`` and ``reasons`` as JSON text, so both adapters and the Turtle round trip hold it."""
    return {"id": fid, **head, "act": act, "n": n, "statement": statement, "outcome": outcome, "key": key or "", "why": why,
            "from_value": "" if value is None else str(value), "from_sha256": str(sha or ""),
            "to": json.dumps(list(to), ensure_ascii=False, sort_keys=True), "reasons": json.dumps(list(reasons), ensure_ascii=False)}
