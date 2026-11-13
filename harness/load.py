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
from store import canonical_digest, configuration_text, stem
import dates     # task-0262: one strict YYYY-MM-DD parse
import formats   # task-0174, decision-0023: a capture or review file names the format it was written in
import load_memory
from subject import SUBJECT
from extract import extract_all, NONE

STORE = SUBJECT.store_keys        # artefact keys the store holds; the others are documents for the arms only
SHORTS = SUBJECT.shorts           # artefact key -> the short its statements' ids carry
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
        return dt.datetime.combine(dates.parse(v, "KG_TODAY"), dt.time(), dt.timezone.utc).isoformat(timespec="seconds")
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
    """The artefact a bag came from, by its ``short``; two artefacts with one ``short`` are refused, never the
    first taken (doc-0030 I11; ``tools/check_subject.py`` refuses the manifest)."""
    found = [p for p in kit if p in FAMILY and SHORTS.get(p) == bag.artefact]   # an unmapped document may have no short
    if len(found) > 1:
        from kitio import DocumentUnreadable
        raise DocumentUnreadable(f"{', '.join(found)}: one short, {bag.artefact!r}, names {len(found)} artefacts, "
                                 "so their statements cannot be told apart; give each its own short")
    return found[0]


def stored_bags(kit: dict[str, str], code: str) -> list:
    """The extraction of the artefacts the store holds: a document with a mapper and ``store = false`` is the
    arms' only, so its statements are never loaded (doc-0030 S1); it still lends its symbols (``symbol_table``)."""
    return [b for b in extract_all(kit, code) if _artefact_of(kit, b) in STORE]


def statements_of(kit: dict[str, str], changed: set[str] | None = None) -> int:
    """The statements a load of ``kit`` writes, as ``load_scenario`` notes them before its first write: every
    stored artefact's, or with ``changed`` (a stage-2 re-load) only those artefacts' (doc-0030 S6)."""
    bags = stored_bags(kit, SUBJECT.reference_code())
    return load_memory.statements([b for b in bags if changed is None or _artefact_of(kit, b) in changed])


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
    bags = stored_bags(kit, code)
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
    st.record_inputs({"attestations": attestations_digest(),   # task-0320 (decision-0038 N2): the tables as this load reads them
                      "configuration": configuration_text(SUBJECT.configuration()),   # task-0335 (decision-0039 §3.2): its files as read
                      **load_identity()})   # task-0341 (decision-0040 (a)): the code and suite compared, the pre-load report applied
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


def load_identity() -> dict[str, str]:
    """``code`` and ``preload`` as ``record_inputs`` keeps them (task-0341, decision-0040 (a)): ``Subject.code``, the
    files an execution verification is compared against, left unrecorded (unknown) when a path lies outside the
    instance; ``preload.identity``, the report ``_record_preload`` applies, or none with why."""
    import preload
    code = SUBJECT.code()
    return {**({"code": configuration_text(code)} if code is not None else {}),
            "preload": configuration_text(preload.identity(SUBJECT))}


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
    import key_rule   # task-0301: the plant's key in NFC
    inferred = {**inferred, "entity": key_rule.normalise(inferred["entity"]), "predicate": key_rule.normalise(inferred["predicate"])}
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
    bags = stored_bags(kit, code)
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
    ``separator``. A scenario the plant removed from the kit then verifies nothing. A link the kit claims
    is inferred (task-0214) derives nothing: an inference never raises a statement, its own or another's."""
    d = VER.get("derive_execution")
    if not d or kit is None:
        return dict(SUBJECT.verification_map().get("execution", {}))
    sep = d.get("separator", "; ")
    out: dict[str, list[str]] = {}
    for bag in stored_bags(kit, SUBJECT.reference_code()):
        for a in bag.assertions:
            if a["predicate"] == d["from_predicate"] and a["basis"] not in ("inferred", "assumed", "hypothesised"):
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
    smoke_digest = sha256(SUBJECT.reference_code())   # the evidence each execution verification records (evidence_sha256)
    review, authored, approval = attestation("review"), attestation("authored"), attestation("approval")
    docs = kit if kit is not None else SUBJECT.pristine()
    # decision-0036 (task-0306): an execution or review verification is the subject's attested result, bound to the
    # document Versions its declaration lists ([verification] execution and review, versions); no suite runs at load.
    # An unlisted Version is not verified, and a declaration that lists none verifies nothing: there is no read rule
    exec_arts, review_arts = bound_artefacts(docs, VER.get("execution")), bound_artefacts(docs, review)
    # decision-0038 N-b (task-0320): the evidence is the code the suite ran on, and it was judged by the suite; both
    # compared with the digests the declaration lists, and a changed or unlisted one verifies nothing by execution
    exec_arts, code = executed(exec_arts, execution)
    marks = [attested_artefacts(docs, d, name)[1] for name, d in (("authored", authored), ("approval", approval)) if d]
    # decision-0019, quoted: "An unlisted Version is not attested: its authored statements read proposed, and nothing in
    # it is approved by construction." An earlier load (stage 1) may have attested or verified by execution what this
    # Version's statements were, changed or not: take it back first, under every bound declaration (decision-0036), so
    # what follows writes what a fresh load of these documents writes; then corroborate and mark the unverified
    unlisted = sorted({u["artefact"] for m in marks if m["bound"] for u in json.loads(m["unattested"])}
                      | (set(stored_artefacts(docs)) - set(exec_arts) if execution else set())
                      | (set(stored_artefacts(docs)) - set(review_arts) if review else set()))
    withdrawn = bool(unlisted) and st.withdraw_construction(unlisted)
    for suite_scenario, keys in execution.items():
        for key in keys:
            counts["execution"] += st.verify_by_execution(
                key, sorted(pristine.get(key, set())), suite_scenario,
                VER.get("execution_scope", "suite scenario {scenario}").format(scenario=suite_scenario), ts, smoke_digest,
                exec_arts)
    for key in vmap.get("review", {}).get("keys", []) if review else []:
        counts["review"] += st.verify_by_review(key, sorted(pristine.get(key, set())), review["at"], review.get("scope", "review"), ATTESTER,
                                               review_arts)
    # requirements and links: reviewed by construction, only where the subject attests it (decision-0009), on the
    # day it names and by the person it names (task-0199, doc-0030 I9): never the load's day, never a default
    # decision-0019 (task-0221): a declaration that lists Versions attests those only; one that lists none attests
    # per load, as decision-0009 (a) has it (the read rule), and the store records which reading it was
    if authored:
        arts, _mark = attested_artefacts(docs, authored, "authored")
        counts["review"] += st.verify_authored(authored["at"], authored.get("scope", "authored"), ATTESTER, arts)
    if approval:
        arts, _mark = attested_artefacts(docs, approval, "approval")
        counts["approved"] = st.approve_verified(approval["at"], approval.get("record", "approval"), ATTESTER, arts)
    for mark in marks:   # a bound declaration only: the read rule's is the manifest's own (gate.attestation_behind), so its store is as before
        if mark["bound"]:
            st.record_attestation(mark)
    record_bound_attestations(st, docs, review, code)
    if withdrawn:
        from rules import r_corroborate, r_unverified
        r_corroborate(st)
        r_unverified(st)
    # decision-0005: every review falls due after its key's review months; the date is the verification's
    # valid_until, which the gate reads as of a date (harness/cadence.py). Not counted: the record's counts stand.
    import cadence
    cadence.date_reviews(st)
    return counts


def record_bound_attestations(st, docs: dict[str, str], review: dict | None, code: list[dict] | None = None) -> None:
    """task-0318: ``execution`` and ``review`` are bound as ``authored`` and ``approval`` are (decision-0036), so the gate
    names them beside those when they omit a Version; recorded whenever bound, so stage 2 replaces what stage 1 read.
    ``code`` (task-0320): the implementation or suite the execution declaration does not list as it is, kept among its
    unattested rows, each marked ``code``, for the gate to name."""
    for name, d in (("execution", VER.get("execution")), ("review", review)):
        if isinstance(d, dict) and d.get("versions") is not None:
            mark = attested_artefacts(docs, d, name)[1]
            if name == "execution" and code:
                mark = {**mark, "unattested": json.dumps(json.loads(mark["unattested"]) + code, ensure_ascii=False, sort_keys=True)}
            st.record_attestation(mark)


def executed(exec_arts: list[str], execution: dict[str, list[str]]) -> tuple[list[str], list[dict]]:
    """(the artefacts execution verifies, the code rows it does not attest, ``execution_code``): none when any is."""
    code = execution_code(VER.get("execution"), sorted({k for ks in execution.values() for k in ks}))
    return ([] if code else exec_arts), code


def execution_code(decl: dict | None, keys: list[str]) -> list[dict]:
    """What an execution verification ran that its declaration does not attest (task-0320, decision-0038 N-b): for the
    reference implementation (``[reference] code``) and the suite that judged it (``[oracle] script``), each the subject
    declares, the files (``Subject.code_parts``, the load's own part selection) whose raw-byte digest
    ``[verification] execution`` does not list in ``implementation`` or ``suite``; a list left out lists none. The suite
    is the script with the files ``[oracle] suite`` lists (task-0338, decision-0039 §3.5). Each row
    {artefact, sha256, parts, code, keys}, with ``files`` [{path, sha256}] naming each of those files it misses: ``parts``
    the unlisted digests, ``stale`` (task-0340) the listed digests no current file holds, ``keys`` the keys the execution map verifies, which it then does not. Empty when everything is listed, or when no declaration lists Versions (it verifies nothing
    already)."""
    SUBJECT.require_code_inside()   # task-0340 R2: before anything is digested
    if not isinstance(decl, dict) or decl.get("versions") is None:
        return []
    rows = (_code_row(which, decl, keys) for which in ("implementation", "suite"))
    return [r for r in rows if r]


def _code_row(which: str, decl: dict, keys: list[str]) -> dict | None:
    """The row for one of ``implementation`` and ``suite`` when ``decl`` does not attest it as it is, else None."""
    path, parts = SUBJECT.code_parts(which)
    path = None if path is None else path or "(an empty path)"   # R7
    listed = decl.get(which)
    listed = listed if isinstance(listed, list) else []
    miss = sorted(d for d in parts.values() if d and d not in listed)
    have = set(parts.values())
    stale = sorted({d for d in listed if isinstance(d, str) and d not in have})   # task-0340 R1: a listed digest no file holds
    named = _suite_named(listed) if which == "suite" else []
    if not (path and (miss or named or stale or not parts)):
        return None
    row = {"artefact": path, "sha256": parts.get("", ""), "parts": miss, "code": which, "keys": keys,
           "missing": which not in decl, **({"stale": stale} if stale else {})}
    if which == "suite" and not named and SUBJECT.suite_declared():   # S3: the finding names the suite files' field when the subject lists any
        row["suite_listed"] = True
    return {**row, "files": named} if named else row


def _suite_named(listed: list) -> list[dict]:
    """task-0338 (decision-0039 §3.5): each file ``[oracle] suite`` lists that ``listed`` misses, or that holds no file,
    {path, sha256}, by path."""
    return [{"path": f, "sha256": d} for f, d in sorted(SUBJECT.suite_declared().items()) if not d or d not in listed]


def _day(v) -> str | None:
    """``v`` as the ISO date (or instant) it names, or None when it names none."""
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return str(v) if dates.day(v) else None   # task-0262: YYYY-MM-DD, alone or with an ISO time


def stored_artefacts(kit: dict[str, str]) -> list[str]:
    """The artefacts of ``kit`` the store holds statements of: the paths an attestation reads (``attested_artefacts``)."""
    return [path for path in sorted(kit) if path in FAMILY and path in STORE]


def bound_artefacts(kit: dict[str, str], decl: dict | None) -> list[str]:
    """The stored artefacts whose Version ``decl`` lists in ``versions`` as ``kit`` holds them (decision-0036,
    task-0306): an execution or a review attestation holds for those only; none listed, or no declaration, holds
    for none."""
    if not isinstance(decl, dict) or decl.get("versions") is None:
        return []
    arts, _mark = attested_artefacts(kit, decl, "bound")
    return arts or []


def attested_artefacts(kit: dict[str, str], decl: dict, name: str) -> tuple[list[str] | None, dict]:
    """(the stored artefacts ``decl`` attests as ``kit`` holds them, or None when it lists no Version: the read
    rule, every artefact as decision-0009 (a) has it; the store's record of it, ``record_attestation``).
    decision-0019, task-0221: ``[verification] authored`` and ``approval`` list in ``versions`` the digest of each
    Version they attest, a file's raw-byte SHA-256 (``Subject.version_digest``, task-0160) and, for a directory,
    its files' (``part_digests``, task-0094; a directory is attested when every file of it is listed)."""
    listed = decl.get("versions")
    rows, arts = [], []
    for path, text in sorted(kit.items()):
        if path not in FAMILY or path not in STORE:
            continue
        digest, _n = SUBJECT.version_digest(path, text)
        parts = sorted(SUBJECT.part_digests(path, text).values()) if path.endswith("/") else []
        ok = listed is None or digest in listed or bool(parts and all(d in listed for d in parts))
        rows.append({"artefact": path, "sha256": digest, "parts": parts, "attested": ok})
        if ok:
            arts.append(path)
    mark = {"id": f"attest:{name}", "declaration": name, "bound": listed is not None, "attester": ATTESTER or "",
            "unattested": json.dumps([{k: r[k] for k in ("artefact", "sha256", "parts")} for r in rows if not r["attested"]],
                                     ensure_ascii=False, sort_keys=True)}
    return (None if listed is None else arts), mark


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


def attestations_digest() -> str:
    """The manifest's ``[verification]``, ``[provenance]`` and ``[capture]`` as the load reads them (task-0320,
    decision-0038 N2): ``canonical_digest`` of ``{"verification": .., "provenance": .., "capture": ..}``, a table the
    manifest lacks null. Recorded at each load (``record_inputs``), read by the gate report's ``attestations``."""
    m = SUBJECT.manifest
    return canonical_digest({n: m.get(n) for n in ("verification", "provenance", "capture")})


def applied_digest(entries: list) -> str:
    """The files a load applied, ``[name, canonical_digest(content as read)]`` each, by name (task-0320): a file the
    load skipped (another scenario's review, a refused one) is not among them."""
    return canonical_digest(sorted(entries))


def load_captures(st, scenario: str) -> dict:
    """Every capture in the subject's capture folder (harness/capture.py ingest; task-0009): an
    answer becomes an assertion of basis ``elicited`` at status proposed, attributed to the person's
    handle and dated; "nobody knows" becomes a declared gap on the key, with the person and the
    date. The verifications never touch basis elicited, so nothing here rises above proposed."""
    files = sorted(SUBJECT.capture_dir.glob("*.toml")) if SUBJECT.capture_dir.is_dir() else []
    counts = {"files": [], "answers": 0, "unknown": 0}
    applied = []
    for p in files:
        c = tomllib.loads(p.read_text(encoding="utf-8"))
        formats.version(c, p.as_posix(), formats.CAPTURE)   # a newer capture refused, exit 2, never misread
        applied.append([p.name, canonical_digest(c)])
        cap = c.get("capture", {})
        handle, on, record = cap["from"], str(cap["on"]), cap["record"]
        person, aid = f"person:{handle}", f"act:capture:{p.stem}"
        st.ensure_person(person, handle)
        st.create_activity(aid, "elicitation", on, "questionnaire", f"answers from {handle} on {on}, owner {cap.get('owner', '')}, {record}", person)
        import key_rule   # task-0301: an answered key in NFC, whichever form the owner's editor wrote
        for i, a in enumerate(c.get("answer", []), 1):
            a = {**a, "key": key_rule.normalise(a["key"])}
            ent, pred = a["key"].split("|", 1)
            st.ensure_entity(ent, "elicited", ent)
            st.create_assertion({"id": f"A:cap:{p.stem}:{i}@capture", "predicate": pred, "value": a["value"],
                                 "text": f"{handle} on {on}: {a['value']}" + (f" ({a['note']})" if a.get("note") else ""),
                                 "basis": "elicited", "status": "proposed", "artefact": record, "key": a["key"], "version": "capture"},
                                ent, aid, person, [])
            counts["answers"] += 1
        for i, u in enumerate(c.get("unknown", []), 1):
            u = {**u, "key": key_rule.normalise(u["key"])}
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
    st.record_inputs({"captures": applied_digest(applied)})   # task-0320: the answers this load applied, as read
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
        import key_rule   # task-0301
        for i, x in enumerate(c.get("proposal", []), 1):
            x = {**x, "key": key_rule.normalise(x["key"])}
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
    files = _ordered_reviews(rdir)
    counts = {"files": [], "refused": [], "approved": 0, "rejected": 0, "referred": 0, "closed": 0, "settled": 0, "skipped": 0}
    if again:
        st.clear_act_findings()
    applied: list = []   # task-0320: the review files this load applied, as read
    pending: list = []   # (act finding, review file): ambiguous rulings, settled or not by a later one
    bound: list = []     # (review file, key, value, sha256) of every ruling applied
    if not files:
        st.record_inputs({"reviews": applied_digest(applied)})
        return counts
    reg = capture.register_root()
    handles, units = review.issued_handles(reg), review.organisation_units(reg)
    owners = capture.owners_of(SUBJECT, capture.register_nodes(reg))
    caps = review.capture_index(SUBJECT.capture_dir)
    opposed = _opposed(files, scenario, st, handles=handles, owners=owners, units=units, captures=caps, now=now,
                       compatible=compatible, strict=False)
    for p, doc in files:
        content = canonical_digest(doc)
        sc = str(doc.get("review", {}).get("scenario", ""))
        if sc and sc != scenario:
            continue
        rel = str(p.relative_to(SUBJECT.root)) if p.is_relative_to(SUBJECT.root) else str(p)
        rid = f"review:{p.stem}"
        errs, rv = review.check(doc, st, handles=handles, owners=owners, units=units, captures=caps, now=now,
                                compatible=compatible, strict=False, where=p.as_posix())
        head = {"review": rel, "by": rv["by"], "on": rv["on"].isoformat() if rv["on"] else str(doc.get("review", {}).get("on", ""))}
        if errs:
            for e in errs:
                print(f"review refused: {rel}: {e}", file=sys.stderr)
            counts["refused"].append(rel)
            st.record_act_finding(_act(f"actf:{rid}", head, "review", 0, "", "", "", "refused", reasons=errs))
            continue
        counts["skipped"] += _record_skipped(st, rv["skipped"], rid, head, rel, pending, review.order_key(p, doc), opposed)
        person, on = f"person:{rv['by']}", rv["on"].isoformat()
        st.ensure_person(person, rv["by"])
        try:
            st.create_activity(f"act:{rid}", "review", on, "review", f"rulings by {rv['by']} on {on}, {rv['record']}, {rel}", person)
        except ValueError:
            if not again:   # store.UNIQUE_IDS: only stage 2 meets a review stage 1 recorded, and keeps that record
                raise
        settled = _apply_rulings(st, rv, (p, doc, rid, head, rel, person, on), caps, opposed, bound, counts, pending)
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
        applied.append([p.name, content])
    _record_pending(st, pending, bound, handles)
    st.record_inputs({"reviews": applied_digest(applied)})
    return counts


def _apply_rulings(st, rv: dict, ctx: tuple, caps, opposed: dict, bound: list, counts: dict, pending: list) -> set:
    """Apply one review's rulings (an opposed one is set aside, task-0328); the keys whose dispute it settled."""
    import review
    p, doc, rid, head, rel, person, on = ctx
    settled = set()
    for ru in rv["rulings"]:
        b = st.assertion_brief(ru["statement"])
        outcome = ru["outcome"]
        until = review.until_for(b, caps)
        # task-0198 (H3): applied whatever the day; the approval keeps its until, six months after the answer,
        # and the gate reads it lapsed as of its date (cadence.lapse), never the load's day
        against = opposed.get((ru["statement"], on, rel))
        if against:   # task-0328: neither ruling of an opposed pair applies
            _set_aside(st, rid, head, rel, ru, b, against, pending, review.order_key(p, doc))
            continue
        if b["status"] == "disputed":
            settled.add(b["key"])   # the review settled the dispute whole (review.check), lapse or not
        st.apply_ruling(b["id"], outcome, rid, person, on, rv["record"], until.isoformat() if until else "")
        bound.append({"at": review.order_key(p, doc), "rel": rel, "id": b["id"], "key": b["key"], "value": str(ru["value"]),
                      "sha256": ru["sha256"], "giver": ru.get("giver"), "outcome": outcome, "by": rv["by"]})
        counts[outcome] += 1
        if ru["unbound"]:   # the read rule: a file from before 0.9.0 binds by id, and the gate says so
            st.record_act_finding(_act(f"actf:{rid}:ruling:{ru['n']}", head, "ruling", ru["n"], b["id"], outcome, b["key"],
                                       "unbound", to=[{"id": b["id"], "value": ru["value"], "sha256": ru["sha256"]}]))
    return settled


def _opposed(files: list, scenario: str, st, **kw) -> dict:
    """task-0328: the rulings that oppose another reviewer's the same day (``review.opposed_rulings``), read from every
    file's check before any is applied, so the outcome does not depend on which file is read first. A legacy ambiguous
    ruling counts too (task-0323 R1), and a ruling on an equivalent statement (the same key, value and digest, by a giver
    its stem reads as, as ``review.settling`` reads it) is one statement with it (R-A); each ruling is found under the
    statement it names as well as the one it is read as."""
    import review
    rows, legacy, ruled = [], [], []
    for p, doc in files:
        sc = str(doc.get("review", {}).get("scenario", ""))
        if sc and sc != scenario:
            continue
        errs, rv = review.check(doc, st, where=p.as_posix(), **kw)
        rel = str(p.relative_to(SUBJECT.root)) if p.is_relative_to(SUBJECT.root) else str(p)
        if errs:
            continue
        on, by = rv["on"].isoformat(), rv["by"]
        ruled += [(ru["statement"], (ru.get("key"), str(ru.get("value")), ru.get("sha256")), ru.get("giver"), on, by, ru["outcome"], rel)
                  for ru in rv["rulings"]]
        # a legacy ambiguous ruling is not applied, but it is a ruling of the day all the same
        legacy += [(x["statement"], (x["key"], str(x["value"]), x["sha256"]), None, on, by, x["outcome"], rel)
                   for x in rv["skipped"] if x["act"] == "ruling" and x["why"] == "ambiguous"]
    handles, canon = kw.get("handles"), {}
    day = [(stmt, same, giver, on) for stmt, same, giver, on, _b, _o, _r in ruled + legacy]
    for stmt, same, giver, on, by, oc, rel in ruled + legacy:
        as_read = review.read_as((stmt, same, giver, on), day, handles)
        canon[(stmt, on, rel)] = as_read
        rows.append((as_read, on, by, oc, rel))
    found = review.opposed_rulings(rows)
    return {**found, **{(stmt, on, rel): found[(c, on, rel)] for (stmt, on, rel), c in canon.items() if (c, on, rel) in found}}


def _set_aside(st, rid: str, head: dict, rel: str, ru: dict, b: dict, group: list, pending: list, at: tuple) -> None:
    """An opposed ruling is not applied: an ``ambiguous`` act finding names every file of its cancelled set (task-0328,
    task-0331). It is held in ``pending``, to be settled by a later day's ruling (``review.opposed_settling``)."""
    import sys
    import review
    pending.append((_act(f"actf:{rid}:ruling:{ru['n']}:opposed", head, "ruling", ru["n"], b["id"], ru["outcome"], b["key"],
                         "ambiguous", value=ru["value"], sha=ru["sha256"], reasons=[review.opposed_reason(group)]), at))
    print(f"review ruling not applied: {rel} is opposed by {', '.join(f for f, _o in group if f != rel)} on {b['id']}", file=sys.stderr)


def _ordered_reviews(rdir: Path) -> list:
    """(path, document) of every review file in the order they are applied (``review.order_key``, task-0322); a newer
    file than this release reads is refused here, before the scenario filter (exit 2)."""
    import review
    out = []
    for p in sorted(rdir.glob("*.toml")) if rdir.is_dir() else []:
        doc = tomllib.loads(p.read_text(encoding="utf-8"))
        formats.version(doc, p.as_posix(), formats.REVIEW)
        out.append((p, doc))
    return sorted(out, key=lambda x: review.order_key(*x))


def _record_skipped(st, skipped: list, rid: str, head: dict, rel: str, pending: list, at: tuple, opposed: dict) -> int:
    """Record the acts a review's load set aside (doc-0032 §6 item 7), an ambiguous ruling held back for
    ``_record_pending``; returns how many."""
    import sys
    for x in skipped:   # an act whose statement changed or vanished: not applied, and said so
        print(f"review act not applied: {rel}: {x['act']} {x['n']} ({x['statement']}): {x['why']}", file=sys.stderr)
        fa = _act(f"actf:{rid}:{x['act']}:{x['n']}", head, x["act"], x["n"], x["statement"], x["outcome"],
                  x["key"], x["why"], value=x["value"], sha=x["sha256"], to=x["to"], reasons=x.get("reasons", ()))
        if x["why"] == "ambiguous" and x["act"] == "ruling":
            import review
            group = opposed.get((x["statement"], head["on"], rel))   # task-0323 R1: opposed the same day, its own reason
            pending.append(({**fa, "reasons": json.dumps([review.opposed_reason(group)], ensure_ascii=False)} if group else fa, at))   # task-0321 H2: recorded once a later ruling is known to settle it, or not
        else:
            st.record_act_finding(fa)
    return len(skipped)


def _record_pending(st, pending: list, bound: list, handles: dict) -> None:
    """task-0321 H2, task-0322: an ambiguous ruling a later applied review settled or superseded is recorded with the
    reason (the gate reads it at info when it is settled or the key reads approved); the rest as they were."""
    import review
    for fa, at in pending:
        reasons = json.loads(fa["reasons"])
        if review.is_opposed(reasons):   # task-0331: its own reason stays first, the settling one follows
            why = review.opposed_settling(fa, at, bound, handles)
            st.record_act_finding({**fa, "reasons": json.dumps([*reasons, why], ensure_ascii=False)} if why else fa)
            continue
        why = review.settling(fa, at, bound, handles)
        st.record_act_finding({**fa, "reasons": json.dumps([why], ensure_ascii=False)} if why else fa)


def _act(fid: str, head: dict, act: str, n: int, statement: str, outcome: str, key: str, why: str, *,
         value=None, sha=None, to=(), reasons=()) -> dict:
    """One act the load did not apply as written, as the store keeps it (``record_act_finding``): scalar
    properties only, ``to`` and ``reasons`` as JSON text, so both adapters and the Turtle round trip hold it."""
    return {"id": fid, **head, "act": act, "n": n, "statement": statement, "outcome": outcome, "key": key or "", "why": why,
            "from_value": "" if value is None else str(value), "from_sha256": str(sha or ""),
            "to": json.dumps(list(to), ensure_ascii=False, sort_keys=True), "reasons": json.dumps(list(reasons), ensure_ascii=False)}
