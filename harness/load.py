"""Load a scenario's extraction into Neo4j and record provenance.

Graph shape: pre-registration §3. Every write is a Cypher statement
through the official driver; nothing is written by any other route.
"""

from __future__ import annotations

import datetime as dt
import os
import re

import logging

from neo4j import GraphDatabase, NotificationMinimumSeverity

logging.getLogger("neo4j").setLevel(logging.ERROR)

from kitio import FAMILY, sha256, pristine
from subject import SUBJECT

STORE = SUBJECT.store_keys        # artefact keys the store holds; the others are documents for the arms only
PROV = SUBJECT.provenance
VER = SUBJECT.verification
from extract import extract_all, NONE

URI = os.environ.get("KG_NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.environ.get("KG_NEO4J_USER", "neo4j"), os.environ.get("KG_NEO4J_PASSWORD", "kgpoc2026"))

CONSTRAINTS = [
    ("uniqueness", "CREATE CONSTRAINT assertion_id IF NOT EXISTS FOR (n:Assertion) REQUIRE n.id IS UNIQUE"),
    ("uniqueness", "CREATE CONSTRAINT fragment_id IF NOT EXISTS FOR (n:Fragment) REQUIRE n.id IS UNIQUE"),
    ("uniqueness", "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE"),
    ("uniqueness", "CREATE CONSTRAINT version_id IF NOT EXISTS FOR (n:Version) REQUIRE n.id IS UNIQUE"),
    ("uniqueness", "CREATE CONSTRAINT artefact_id IF NOT EXISTS FOR (n:Artefact) REQUIRE n.id IS UNIQUE"),
    ("uniqueness", "CREATE CONSTRAINT gap_id IF NOT EXISTS FOR (n:Gap) REQUIRE n.id IS UNIQUE"),
    ("existence", "CREATE CONSTRAINT assertion_status IF NOT EXISTS FOR (n:Assertion) REQUIRE n.status IS NOT NULL"),
    ("node key", "CREATE CONSTRAINT fragment_key IF NOT EXISTS FOR (n:Fragment) REQUIRE (n.locator, n.sha256) IS NODE KEY"),
    ("property type", "CREATE CONSTRAINT version_sha IF NOT EXISTS FOR (n:Version) REQUIRE n.sha256 IS :: STRING"),
]

SYMBOL_RE = re.compile(r"^[A-Z][A-Z_]+$")


def driver():
    return GraphDatabase.driver(URI, auth=AUTH, notifications_min_severity=NotificationMinimumSeverity.OFF)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def apply_constraints(session) -> list[dict]:
    out = []
    for kind, q in CONSTRAINTS:
        try:
            session.run(q).consume()
            out.append({"type": kind, "cypher": q, "accepted": True, "message": ""})
        except Exception as e:  # noqa: BLE001 — the message is the measurement
            msg = str(e)
            out.append({"type": kind, "cypher": q, "accepted": False,
                        "message": msg.splitlines()[0][:300]})
    return out


def clear(session):
    session.run("MATCH (n) DETACH DELETE n").consume()


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


def load_scenario(session, scenario: str, kit: dict[str, str], *, activity_note: str,
                  version_tag: str = "v1", reingest: bool = False) -> dict:
    """Write artefacts, versions, fragments, entities, assertions and the
    provenance activity. Returns counts and the unresolved symbols."""
    code = SUBJECT.reference_code()
    bags = extract_all(kit, code)
    unresolved = resolve_symbols(bags, symbol_table(kit))
    ts = now()
    session.run("""
        MERGE (tool:Agent {id:'agent:harness'}) SET tool.kind='tool', tool.name=$tool, tool.version=$v
        MERGE (human:Agent {id:$hid}) SET human.kind='human', human.name=$hname
        MERGE (llm:Agent {id:$lid}) SET llm.kind='llm', llm.name=$lname
        CREATE (act:Activity {id:$aid, kind:'extraction', at:$ts, tool:$tool, note:$note})
        MERGE (act)-[:ASSOCIATED_WITH]->(tool)
        """, v=version_tag, aid=f"act:extract:{scenario}:{version_tag}", ts=ts, note=activity_note,
             tool=PROV.get("harness_name", "harness"), hid=PROV.get("human", {}).get("id", "agent:maintainer"),
             hname=PROV.get("human", {}).get("name", "maintainer"), lid=PROV.get("llm", {}).get("id", "agent:llm"),
             lname=PROV.get("llm", {}).get("name", "model")).consume()
    aid = f"act:extract:{scenario}:{version_tag}"
    n_frag = n_ass = n_reused = 0
    for path, text in kit.items():
        if path not in FAMILY or path not in STORE:
            continue
        family, fmt = FAMILY[path]
        vid = f"V:{path}:{version_tag}"
        session.run("""
            MERGE (a:Artefact {id:$path}) SET a.path=$path, a.family=$family, a.format=$fmt
            CREATE (v:Version {id:$vid, sha256:$sha, bytes:$bytes, ingested_at:$ts, tag:$tag})
            MERGE (a)-[:HAS_VERSION]->(v)
            WITH a, v
            OPTIONAL MATCH (a)-[c:CURRENT]->(old:Version) DELETE c
            MERGE (a)-[:CURRENT]->(v)
            WITH v MATCH (act:Activity {id:$aid}) MERGE (act)-[:USED]->(v)
            """, path=path, family=family, fmt=fmt, vid=vid, sha=sha256(text),
                    bytes=len(text.encode()), ts=ts, tag=version_tag, aid=aid).consume()
    for bag in bags:
        art = next(p for p in kit if p in FAMILY and bag.artefact == __import__("extract").short(p))
        vid = f"V:{art}:{version_tag}"
        fmap: dict[str, str] = {}
        reused: set[str] = set()
        for f in bag.fragments:
            existing = None
            if reingest:
                row = session.run("""MATCH (f:Fragment {artefact:$art, locator:$loc, sha256:$sha}) RETURN f.id AS id LIMIT 1""",
                                  art=art, loc=f["locator"], sha=sha256(f["text"])).single()
                existing = row["id"] if row else None
            if existing:
                session.run("MATCH (v:Version {id:$vid}), (f:Fragment {id:$fid}) MERGE (v)-[:HAS_FRAGMENT]->(f)",
                            vid=vid, fid=existing).consume()
                fmap[f["id"]] = existing
                reused.add(f["id"])
                n_reused += 1
                continue
            fid = f["id"] + f"@{version_tag}"
            session.run("""
                MATCH (v:Version {id:$vid})
                CREATE (f:Fragment {id:$fid, locator:$loc, sha256:$sha, text:$text, artefact:$art})
                MERGE (v)-[:HAS_FRAGMENT]->(f)
                """, vid=vid, fid=fid, loc=f["locator"], sha=sha256(f["text"]),
                        text=f["text"], art=art).consume()
            fmap[f["id"]] = fid
            n_frag += 1
        for e in bag.entities.values():
            session.run("MERGE (e:Entity {id:$id}) ON CREATE SET e.kind=$kind, e.name=$name",
                        id=e["id"], kind=e["kind"], name=e["name"]).consume()
        for a in bag.assertions:
            if reingest and a["fragments"] and all(f in reused for f in a["fragments"]):
                continue  # the statement and its evidence are unchanged: no new assertion
            basis_agent = "agent:maintainer" if a["basis"] == "authored" else "agent:harness"
            session.run("""
                MATCH (act:Activity {id:$aid}), (e:Entity {id:$eid}), (ag:Agent {id:$agent})
                CREATE (x:Assertion {id:$id, predicate:$pred, value:$value, raw_value:$raw, text:$text,
                                     basis:$basis, status:'proposed', artefact:$art, key:$key,
                                     unresolved:$unres, version:$vtag})
                MERGE (x)-[:ABOUT]->(e)
                MERGE (x)-[:DERIVED_BY]->(act)
                MERGE (x)-[:ATTRIBUTED_TO]->(ag)
                WITH x
                UNWIND $frags AS fid
                MATCH (f:Fragment {id:fid})
                MERGE (x)-[:SUPPORTED_BY]->(f)
                """, aid=aid, eid=a["entity"], agent=basis_agent, id=a["id"] + f"@{version_tag}",
                        pred=a["predicate"], value=a["value"], raw=a.get("raw_value"), text=a["text"],
                        basis=a["basis"], art=art, key=f"{a['entity']}|{a['predicate']}",
                        unres=a.get("unresolved", False), vtag=version_tag,
                        frags=[fmap[f] for f in a["fragments"]]).consume()
            n_ass += 1
    # the fragments MENTION the entities their assertions are about
    session.run("""
        MATCH (x:Assertion)-[:ABOUT]->(e:Entity), (x)-[:SUPPORTED_BY]->(f:Fragment)
        MERGE (f)-[:MENTIONS]->(e)""").consume()
    return {"fragments": n_frag, "fragments_reused": n_reused, "assertions": n_ass,
            "unresolved_symbols": unresolved, "activity": aid}


def load_inferred(session, scenario: str, inferred: dict):
    """One model-proposed assertion (the subject's ``[inferred]`` plant), attributed to the llm
    agent, linked to the open decision it claims to resolve, with no supporting fragment."""
    session.run("""
        MATCH (llm:Agent {id:$lid}), (e:Entity {id:$eid})
        CREATE (act:Activity {id:$aid, kind:'inference', at:$at, tool:$itool, note:$note})
        MERGE (act)-[:ASSOCIATED_WITH]->(llm)
        CREATE (x:Assertion {id:$id, predicate:$pred, value:$value, text:$text, basis:'inferred',
                             status:'proposed', artefact:'llm', key:$key, version:'v1'})
        MERGE (x)-[:ABOUT]->(e)
        MERGE (x)-[:DERIVED_BY]->(act)
        MERGE (x)-[:ATTRIBUTED_TO]->(llm)
        WITH x
        MERGE (g:Gap {id:$gid})
        MERGE (x)-[:CANDIDATE_FOR]->(g)
        """, eid=inferred["entity"], aid=f"act:infer:{scenario}", note=inferred["note"], gid=inferred["candidate_for"],
                lid=PROV.get("llm", {}).get("id", "agent:llm"), at=PROV.get("inference_at", now()), itool=PROV.get("inference_tool", "model"),
                id=inferred["id"] + "@v1", pred=inferred["predicate"], value=inferred["value"],
                text=inferred["text"], key=f"{inferred['entity']}|{inferred['predicate']}").consume()


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


def load_verifications(session, scenario: str, pristine: dict[str, set[str]]) -> dict:
    """Execution and review verifications of the live assertions whose
    (key, value) the pristine kit states; then the owner's approval of
    every verified assertion. Skipped by the caller for a scenario declared
    ``verifications = false``. A subject with no verification map verifies nothing."""
    vmap = SUBJECT.verification_map()
    ts = now()
    counts = {"execution": 0, "review": 0, "approved": 0}
    smoke_digest = sha256(SUBJECT.reference_code())
    review, authored, approval = VER.get("review", {}), VER.get("authored", {}), VER.get("approval", {})
    for suite_scenario, keys in vmap.get("execution", {}).items():
        for key in keys:
            n = session.run("""
                MATCH (x:Assertion {key:$key}) WHERE x.value IN $vals AND x.basis IN ['extracted','authored'] AND NOT x.status IN ['invalidated','rejected','deprecated']
                MATCH (h:Agent {id:'agent:harness'})
                MERGE (v:Verification {id:'ver:exec:' + $sc + ':' + x.id})
                  SET v.method='execution', v.outcome='pass', v.scope=$scope, v.at=$ts,
                      v.evidence_sha256=$dig, v.valid_until=null
                MERGE (v)-[:VERIFIES]->(x)
                MERGE (v)-[:PERFORMED_BY]->(h)
                SET x.status = CASE WHEN x.status IN ['proposed','validated'] THEN 'verified' ELSE x.status END
                RETURN count(x) AS n""", key=key, vals=sorted(pristine.get(key, set())), sc=suite_scenario,
                scope=VER.get("execution_scope", "suite scenario {scenario}").format(scenario=suite_scenario), ts=ts,
                dig=smoke_digest).single()["n"]
            counts["execution"] += n
    for key in vmap.get("review", {}).get("keys", []):
        n = session.run("""
            MATCH (x:Assertion {key:$key}) WHERE x.value IN $vals AND x.basis IN ['extracted','authored'] AND NOT x.status IN ['invalidated','rejected','deprecated']
            MATCH (h:Agent {id:'agent:maintainer'})
            MERGE (v:Verification {id:'ver:review:' + x.id})
              SET v.method='review', v.outcome='pass', v.at=$at, v.valid_until=null, v.scope=$scope
            MERGE (v)-[:VERIFIES]->(x)
            MERGE (v)-[:PERFORMED_BY]->(h)
            SET x.status = CASE WHEN x.status IN ['proposed','validated'] THEN 'verified' ELSE x.status END
            RETURN count(x) AS n""", key=key, vals=sorted(pristine.get(key, set())), at=review.get("at", ts), scope=review.get("scope", "review")).single()["n"]
        counts["review"] += n
    # requirements and links: authored by the maintainer -> reviewed by construction
    n = session.run("""
        MATCH (x:Assertion) WHERE x.basis='authored' AND x.status='proposed' AND x.value <> 'NONE'
        MATCH (h:Agent {id:'agent:maintainer'})
        MERGE (v:Verification {id:'ver:review:' + x.id})
          SET v.method='review', v.outcome='pass', v.at=$at, v.valid_until=null, v.scope=$scope
        MERGE (v)-[:VERIFIES]->(x) MERGE (v)-[:PERFORMED_BY]->(h)
        SET x.status='verified' RETURN count(x) AS n""", at=authored.get("at", ts), scope=authored.get("scope", "authored")).single()["n"]
    counts["review"] += n
    counts["approved"] = session.run("""
        MATCH (x:Assertion {status:'verified'}), (h:Agent {id:'agent:maintainer'})
        MERGE (ap:Approval {id:'appr:' + x.id}) SET ap.at=$at, ap.record=$record
        MERGE (ap)-[:APPROVES]->(x) MERGE (ap)-[:BY]->(h)
        SET x.status='approved' RETURN count(x) AS n""", at=approval.get("at", ts), record=approval.get("record", "approval")).single()["n"]
    return counts
