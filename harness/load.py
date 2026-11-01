"""Load a scenario's extraction into the store and record provenance.

Graph shape: pumllint kg_experiment/PREREGISTRATION.md §3. Every write goes through the store
port (store.py); the first adapter (store_neo4j.py) holds the Cypher.
"""

from __future__ import annotations

import datetime as dt
import re

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
    return {"fragments": n_frag, "fragments_reused": n_reused, "assertions": n_ass,
            "unresolved_symbols": unresolved, "activity": aid}


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
