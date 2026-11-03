"""Load a scenario's extraction into the store and record provenance.

Graph shape: pumllint kg_experiment/PREREGISTRATION.md §3. Every write goes through the store
port (store.py); the first adapter (store_neo4j.py) holds the Cypher.
"""

from __future__ import annotations

import datetime as dt
import re
import tomllib

from kitio import FAMILY, sha256, pristine
from subject import SUBJECT
from extract import extract_all, short, NONE

STORE = SUBJECT.store_keys        # artefact keys the store holds; the others are documents for the arms only
PROV = SUBJECT.provenance
VER = SUBJECT.verification
HUMAN = {"id": PROV.get("human", {}).get("id", "agent:maintainer"), "name": PROV.get("human", {}).get("name", "maintainer")}
LLM = {"id": PROV.get("llm", {}).get("id", "agent:llm"), "name": PROV.get("llm", {}).get("name", "model")}
TOOL = PROV.get("harness_name", "harness")

SYMBOL_RE = re.compile(r"^[A-Z][A-Z_]+$")


def now() -> str:
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


def load_scenario(st, scenario: str, kit: dict[str, str], *, activity_note: str,
                  version_tag: str = "v1", reingest: bool = False) -> dict:
    """Write artefacts, versions, fragments, entities, assertions and the
    provenance activity. Returns counts and the unresolved symbols."""
    code = SUBJECT.reference_code()
    bags = extract_all(kit, code)
    unresolved = resolve_symbols(bags, symbol_table(kit))
    ts = now()
    aid = f"act:extract:{scenario}:{version_tag}"
    st.ensure_agents(TOOL, version_tag, HUMAN, LLM)
    st.create_activity(aid, "extraction", ts, TOOL, activity_note, "agent:harness")
    n_frag = n_ass = n_reused = 0
    for path, text in kit.items():
        if path not in FAMILY or path not in STORE:
            continue
        family, fmt = FAMILY[path]
        st.upsert_artefact_version(path, family, fmt, f"V:{path}:{version_tag}", sha256(text), len(text.encode()), ts, version_tag, aid)
    for bag in bags:
        art = next(p for p in kit if p in FAMILY and bag.artefact == short(p))
        vid = f"V:{art}:{version_tag}"
        fmap: dict[str, str] = {}
        reused: set[str] = set()
        for f in bag.fragments:
            existing = st.find_fragment(art, f["locator"], sha256(f["text"])) if reingest else None
            if existing:
                st.link_fragment(vid, existing)
                fmap[f["id"]] = existing
                reused.add(f["id"])
                n_reused += 1
                continue
            fid = f["id"] + f"@{version_tag}"
            st.create_fragment(vid, fid, f["locator"], sha256(f["text"]), f["text"], art)
            fmap[f["id"]] = fid
            n_frag += 1
        for e in bag.entities.values():
            st.ensure_entity(e["id"], e["kind"], e["name"])
        for a in bag.assertions:
            if reingest and a["fragments"] and all(f in reused for f in a["fragments"]):
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
            "unresolved_symbols": unresolved, "activity": aid, **({"unmapped": unmapped} if unmapped else {})}


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
    ``verifications = false``. A subject with no verification map verifies nothing."""
    vmap = SUBJECT.verification_map()
    execution = execution_map(kit)
    ts = now()
    counts = {"execution": 0, "review": 0, "approved": 0}
    smoke_digest = sha256(SUBJECT.reference_code())
    review, authored, approval = VER.get("review", {}), VER.get("authored", {}), VER.get("approval", {})
    for suite_scenario, keys in execution.items():
        for key in keys:
            counts["execution"] += st.verify_by_execution(
                key, sorted(pristine.get(key, set())), suite_scenario,
                VER.get("execution_scope", "suite scenario {scenario}").format(scenario=suite_scenario), ts, smoke_digest)
    for key in vmap.get("review", {}).get("keys", []):
        counts["review"] += st.verify_by_review(key, sorted(pristine.get(key, set())), review.get("at", ts), review.get("scope", "review"), HUMAN["id"])
    # requirements and links: authored by the maintainer -> reviewed by construction
    counts["review"] += st.verify_authored(authored.get("at", ts), authored.get("scope", "authored"), HUMAN["id"])
    counts["approved"] = st.approve_verified(approval.get("at", ts), approval.get("record", "approval"), HUMAN["id"])
    return counts


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
    return counts


def load_reviews(st, scenario: str, now: dt.date | None = None) -> dict:
    """Every review in the subject's ``<capture dir>/reviews/`` for this scenario (task-0037,
    decision-0002), after the rules have run: harness/review.py checks each file against the loaded
    store and refuses it whole, with its reasons on stderr; an accepted one applies its rulings
    (approved, rejected), settles the conflicts of the keys whose dispute it settled, and closes the
    declared gaps it names. An approval of a person's statement past its six months is not applied."""
    import sys
    import capture
    import review
    from rules import compatible
    rdir = SUBJECT.capture_dir / "reviews"
    files = sorted(rdir.glob("*.toml")) if rdir.is_dir() else []
    counts = {"files": [], "refused": [], "approved": 0, "rejected": 0, "referred": 0, "lapsed": 0, "closed": 0, "settled": 0}
    if not files:
        return counts
    now = now or review.today()
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
        errs, rv = review.check(doc, st, handles=handles, owners=owners, units=units, captures=caps, now=now, compatible=compatible)
        if errs:
            for e in errs:
                print(f"review refused: {rel}: {e}", file=sys.stderr)
            counts["refused"].append(rel)
            continue
        rid, person, on = f"review:{p.stem}", f"person:{rv['by']}", rv["on"].isoformat()
        st.ensure_person(person, rv["by"])
        st.create_activity(f"act:{rid}", "review", on, "review", f"rulings by {rv['by']} on {on}, {rv['record']}, {rel}", person)
        settled = set()
        for ru in rv["rulings"]:
            b = st.assertion_brief(ru["assertion"])
            outcome = ru["outcome"]
            until = review.until_for(b, caps)
            if b["status"] == "disputed":
                settled.add(b["key"])   # the review settled the dispute whole (review.check), lapse or not
            if outcome == "approved" and until is not None and now > until:
                counts["lapsed"] += 1   # the approval lapsed: the statement reads proposed until it is re-asked
                if b["status"] == "disputed":   # a person's statement against a document's (task-0038)
                    st.apply_ruling(b["id"], "lapsed", rid, person, on, rv["record"], "")
                continue
            st.apply_ruling(b["id"], outcome, rid, person, on, rv["record"], until.isoformat() if until else "")
            counts[outcome] += 1
        for key in sorted(settled):
            counts["settled"] += st.settle_conflicts(key, rid)
        for c in rv["closes"]:
            st.close_declared_gap(c["gap"], rid, on, rv["record"])
            counts["closed"] += 1
        counts["files"].append(rel)
    return counts
