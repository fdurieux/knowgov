"""The Neo4j adapter of the store port: every Cypher statement of the harness and the page, the
Browser link and the saved queries. Graph shape: pumllint kg_experiment/PREREGISTRATION.md §3.

Status is set only here, by the loader's and the rules' methods and by recorded human acts.
The free Community edition serves one database, so ``wipe`` empties it; the constraint
families it refuses are recorded by ``apply_constraints`` (D1).
"""
from __future__ import annotations

import logging
import os

from store import Store

logging.getLogger("neo4j").setLevel(logging.ERROR)

URI = os.environ.get("KG_NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.environ.get("KG_NEO4J_USER", "neo4j"), os.environ.get("KG_NEO4J_PASSWORD", "kgpoc2026"))
BROWSER = os.environ.get("KG_BROWSER_URL", "http://localhost:7474")

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

# The impact walk of the register's tools/impact.py, in Cypher, from one literal start (task-0023).
# The walk's rules at ieam-register v0.2.2 (its decision 0007): applications follow supports; processes
# follow delivers and realizes, and is_supported_by backwards (reported from the process, "(inverse)");
# journeys follow concerns. An edge is live when its link is approved and its far node is neither
# deprecated nor retired; every edge met is reported, a withdrawn edge is reported and not followed, so
# only live edges lead on and only their far ends count as reached. No parent climb. Every chain the
# rules allow is one branch of the CALL (a) { } UNION (the scoped form, which imports the start; the
# importing WITH is deprecated in Neo4j 5.26): the start and each intermediate node filtered on
# taxonomy and state, each intermediate link on state approved, the last edge and its end node
# unfiltered. The register's own kinds end every chain in three steps (supports lands on a process,
# delivers and concerns on a product, realizes on a capability). IMPACT_ROWS is the saved query, one
# row per edge as the panel's table, with whether the walk followed it; IMPACT_PATHS returns the paths,
# which the Browser draws as a graph. Equivalence with walk() is tested over the projection's rows.
IMPACT_START = "APP-0002"
_LIVE = "NOT {0}.state IN ['deprecated','retired']"
_OK = "{0}.state = 'approved'"
_APP = "a.taxonomy = 'applications' AND " + _LIVE.format("a")
_PROC_A = "a.taxonomy = 'processes' AND " + _LIVE.format("a")
_PROC_X = "x.taxonomy = 'processes' AND " + _LIVE.format("x")
_JRN_A = "a.taxonomy = 'journeys' AND " + _LIVE.format("a")
_JRN_J = "j.taxonomy = 'journeys' AND " + _LIVE.format("j")
_R1, _R2 = _OK.format("r1"), _OK.format("r2")
IMPACT_WALK = (
    f"MATCH (a:RegNode {{reg_id:'{IMPACT_START}'}})\n"
    "CALL (a) {\n"
    f"  MATCH p = (a)-[:REG_SUPPORTS]->(:RegNode) WHERE {_APP} RETURN p\n"
    f"  UNION MATCH p = (a)-[r1:REG_SUPPORTS]->(x:RegNode)-[:REG_DELIVERS|REG_REALIZES]->(:RegNode) WHERE {_APP} AND {_PROC_X} AND {_R1} RETURN p\n"
    f"  UNION MATCH p = (a)-[r1:REG_SUPPORTS]->(x:RegNode)<-[:REG_IS_SUPPORTED_BY]-(:RegNode) WHERE {_APP} AND {_PROC_X} AND {_R1} RETURN p\n"
    f"  UNION MATCH p = (a)-[r1:REG_SUPPORTS]->(x:RegNode)<-[r2:REG_IS_SUPPORTED_BY]-(j:RegNode)-[:REG_CONCERNS]->(:RegNode) WHERE {_APP} AND {_PROC_X} AND {_JRN_J} AND {_R1} AND {_R2} RETURN p\n"
    f"  UNION MATCH p = (a)-[:REG_DELIVERS|REG_REALIZES]->(:RegNode) WHERE {_PROC_A} RETURN p\n"
    f"  UNION MATCH p = (a)<-[:REG_IS_SUPPORTED_BY]-(:RegNode) WHERE {_PROC_A} RETURN p\n"
    f"  UNION MATCH p = (a)<-[r1:REG_IS_SUPPORTED_BY]-(j:RegNode)-[:REG_CONCERNS]->(:RegNode) WHERE {_PROC_A} AND {_JRN_J} AND {_R1} RETURN p\n"
    f"  UNION MATCH p = (a)-[:REG_CONCERNS]->(:RegNode) WHERE {_JRN_A} RETURN p\n"
    "}\n")
IMPACT_ROWS = (
    "// the walk tools/impact.py makes, one row per edge, as the impact panel lists them, a withdrawn edge listed and not followed\n"
    + IMPACT_WALK +
    "UNWIND relationships(p) AS r WITH DISTINCT r\n"
    "WITH r, CASE WHEN type(r) = 'REG_IS_SUPPORTED_BY' THEN endNode(r) ELSE startNode(r) END AS f,\n"
    "        CASE WHEN type(r) = 'REG_IS_SUPPORTED_BY' THEN startNode(r) ELSE endNode(r) END AS t\n"
    "OPTIONAL MATCH (l:RegLink {reg_id: r.reg_id})   // the evidence sits on the link node\n"
    "RETURN f.reg_id AS `from`,\n"
    "       toLower(replace(type(r), 'REG_', '')) + CASE WHEN type(r) = 'REG_IS_SUPPORTED_BY' THEN ' (inverse)' ELSE '' END AS relationship,\n"
    "       t.reg_id AS `to`, t.name AS name, t.state AS `node state`, r.state AS `link state`,\n"
    "       CASE WHEN r.state = 'approved' AND NOT t.state IN ['deprecated','retired'] THEN 'yes' ELSE 'no, withdrawn' END AS followed,\n"
    "       r.owner AS owner, l.evidence AS evidence, r.reg_id AS link\n"
    "ORDER BY link")
IMPACT_PATHS = (
    "// the same walk as paths, for the Browser's graph view: a start with no edge still draws itself\n"
    + IMPACT_WALK.replace("CALL (a) {\n", "OPTIONAL CALL (a) {\n") +
    "RETURN a, p")


# The walk above starts only from applications, processes and journeys: from a capability or an
# information node it meets no edge (doc-0008 §4). These two go the other way, to what rests on the
# start: the nodes whose links point at it, then one step on from each process among them over an
# approved link. The same rule as the walk: every edge met is a row, a withdrawn one (link not
# approved, or far node deprecated or retired) is marked and not stepped from. One literal start each,
# which the page replaces with the register's own default for the taxonomy (demo/app/server.py).
CAPABILITY_START = "CAP-0002"
INFORMATION_START = "ENT-0002"
_DEP_RETURN = (
    "RETURN x.reg_id AS node, x.name AS name, toLower(replace(type(r), 'REG_', '')) AS relationship, via,\n"
    "       x.state AS `node state`, r.state AS `link state`,\n"
    "       CASE WHEN r.state = 'approved' AND NOT x.state IN ['deprecated','retired'] THEN 'yes' ELSE 'no, withdrawn' END AS followed,\n"
    "       r.owner AS owner, r.reg_id AS link\n"
    "ORDER BY via, node, link")
DEPENDANTS_CAPABILITY = (
    "// what rests on a capability: the processes that realise it and the products that require it,\n"
    "// then one step on from each process that realises it over an approved link\n"
    f"MATCH (c:RegNode {{reg_id:'{CAPABILITY_START}'}})\n"
    "CALL (c) {\n"
    "  MATCH (x:RegNode)-[r:REG_REALIZES|REG_REQUIRES]->(c) RETURN x, r, null AS via\n"
    "  UNION\n"
    f"  MATCH (p:RegNode)-[r0:REG_REALIZES]->(c), (x:RegNode)-[r:REG_SUPPORTS|REG_IS_SUPPORTED_BY]->(p) WHERE {_OK.format('r0')} AND {_LIVE.format('p')} RETURN x, r, p.reg_id AS via\n"
    "  UNION\n"
    f"  MATCH (p:RegNode)-[r0:REG_REALIZES]->(c), (p)-[r:REG_DELIVERS]->(x:RegNode) WHERE {_OK.format('r0')} AND {_LIVE.format('p')} RETURN x, r, p.reg_id AS via\n"
    "}\n" + _DEP_RETURN)
DEPENDANTS_INFORMATION = (
    "// what touches an information node: the processes that create, read, update or delete it and the\n"
    "// applications that manage it, then one step on from each such process over an approved link\n"
    f"MATCH (e:RegNode {{reg_id:'{INFORMATION_START}'}})\n"
    "CALL (e) {\n"
    "  MATCH (x:RegNode)-[r:REG_CRUD|REG_MANAGES]->(e) RETURN x, r, null AS via\n"
    "  UNION\n"
    f"  MATCH (p:RegNode)-[r0:REG_CRUD]->(e), (x:RegNode)-[r:REG_SUPPORTS|REG_IS_SUPPORTED_BY]->(p) WHERE {_OK.format('r0')} AND {_LIVE.format('p')} RETURN x, r, p.reg_id AS via\n"
    "  UNION\n"
    f"  MATCH (p:RegNode)-[r0:REG_CRUD]->(e), (p)-[r:REG_REALIZES|REG_DELIVERS]->(x:RegNode) WHERE {_OK.format('r0')} AND {_LIVE.format('p')} RETURN x, r, p.reg_id AS via\n"
    "}\n" + _DEP_RETURN)
# From a register node to the knowledge store: the documents its approved links cite, the assertions
# the current version of each supports, and the derived code that used them. The one join the two
# namespaces share is the document's path, so it reaches a whole document, not the cited anchor.
MODULE_STORE = (
    "// from a node to the store: the documents its approved links cite, the assertions they support now,\n"
    "// and the derived code built on them, at the grain of a whole document\n"
    f"MATCH (n:RegNode {{reg_id:'{IMPACT_START}'}})<-[:REG_LINK_OF]-(l:RegLink {{state:'approved'}})-[:REG_CITES]->(d:RegDocument)\n"
    "MATCH (:Artefact {id:d.path})-[:CURRENT]->(:Version)-[:HAS_FRAGMENT]->(:Fragment)<-[:SUPPORTED_BY]-(x:Assertion)\n"
    "OPTIONAL MATCH (dv:Derived)-[:USED_ASSERTION]->(x)\n"
    "RETURN l.reg_id AS link, d.path AS document, count(DISTINCT x) AS assertions,\n"
    "       collect(DISTINCT x.status) AS statuses, collect(DISTINCT dv.id + CASE WHEN dv.suspect THEN ' (suspect)' ELSE '' END) AS derived\n"
    "ORDER BY link, document")
# The literal start each saved query carries, by the taxonomy the page picks its default from.
START_LITERALS = {"applications": IMPACT_START, "capabilities": CAPABILITY_START, "information": INFORMATION_START}


def impact_cypher(start: str) -> dict:
    """Both forms of the walk from ``start`` in place of the adapter's literal: the page lists them
    with the register's default start and the impact panel with the id the viewer typed (task-0024)."""
    sub = lambda text: text.replace(f"'{IMPACT_START}'", f"'{start}'")  # noqa: E731
    return {"rows": sub(IMPACT_ROWS), "paths": sub(IMPACT_PATHS)}

# The page's generic saved queries for Neo4j Browser; a subject adds its own (queries.toml).
SAVED_QUERIES = [
    {"id": "loaded", "needs": "scenario", "title": "Which scenario is loaded",
     "text": "MATCH (a:Activity) WHERE a.id STARTS WITH 'act:extract:'\nRETURN a.id AS activity, a.at AS at, a.note AS note ORDER BY a.at"},
    {"id": "gaps", "needs": "scenario", "title": "The gap census",
     "text": ("MATCH (g:Gap)\n"
              "OPTIONAL MATCH (g)-[:CONCERNS]->(t)\n"
              "RETURN g.kind AS kind, g.declared AS declared, count(DISTINCT g) AS gaps,\n"
              "       count(DISTINCT t) AS things_concerned ORDER BY kind")},
    {"id": "gaps-concerns", "needs": "scenario", "title": "The gaps, with what they concern",
     "text": ("MATCH (g:Gap)\n"
              "OPTIONAL MATCH (g)-[r:CONCERNS|CONCERNS_KEY]->(t)\n"
              "RETURN g.id AS gap, g.kind AS kind, g.declared AS declared, g.text AS text,\n"
              "       collect(DISTINCT coalesce(r.key, t.id)) AS concerns\n"
              "ORDER BY kind, gap")},
    {"id": "census", "needs": "scenario", "title": "The status census",
     "text": "MATCH (x:Assertion) RETURN x.status AS status, x.basis AS basis, count(*) AS n ORDER BY status, basis"},
    # the register's projection: its own namespace (Register, Reg*, REG_*), loaded on demand, wiped by a run
    {"id": "register-tag", "needs": "register", "title": "Which register tag is projected, and what it holds",
     "text": ("MATCH (n:RegNode) WITH n.tag AS tag, n.commit AS commit, n.loaded_at AS loaded_at LIMIT 1\n"
              "MATCH (m:Register) UNWIND labels(m) AS l WITH tag, commit, loaded_at, l WHERE l <> 'Register'\n"
              "RETURN tag, commit, loaded_at, l AS label, count(*) AS n ORDER BY label")},
    {"id": "register-impact", "needs": "register", "title": f"The impact walk from {IMPACT_START}: the walk the register's tools/impact.py makes, one row per edge",
     "text": IMPACT_ROWS, "start": "applications"},
    {"id": "register-impact-paths", "needs": "register", "title": f"The same impact walk from {IMPACT_START} as paths: the graph view draws it",
     "text": IMPACT_PATHS, "start": "applications"},
    {"id": "register-dependants-capability", "needs": "register", "start": "capabilities",
     "title": f"What rests on {CAPABILITY_START}: what realises or requires it, then one step on, approved links only",
     "text": DEPENDANTS_CAPABILITY},
    {"id": "register-dependants-information", "needs": "register", "start": "information",
     "title": f"What touches {INFORMATION_START}: what creates, reads, updates, deletes or manages it, then one step on, approved links only",
     "text": DEPENDANTS_INFORMATION},
    {"id": "register-node-store", "needs": "register+scenario", "start": "applications",
     "title": f"From {IMPACT_START} to the store: the documents its approved links cite, their assertions and the derived code",
     "text": MODULE_STORE},
    {"id": "register-c1", "needs": "register", "title": "C1 in Cypher: approved steps and touchpoints with no is_supported_by link, the exception joined",
     "text": ("MATCH (s:RegNode {taxonomy:'journeys', state:'approved'}) WHERE s.kind IN ['step', 'touchpoint']\n"
              "  AND NOT (s)-[:REG_IS_SUPPORTED_BY]->(:RegNode)\n"
              "OPTIONAL MATCH (e:RegException {rule:'C1'})-[x:REG_EXCEPTS]->(s)\n"
              "RETURN s.reg_id AS uncovered, s.name AS name, e.reg_id AS exception, x.expires AS expires")},
    {"id": "register-cites", "needs": "register+scenario", "title": "The links that cite a kit document, joined to the harness's Artefact by path: the one query across both namespaces",
     "text": ("// the register's digest at the tag beside the store's digest per version: 'same as tag' or 'differs'\n"
              "MATCH (l:RegLink)-[c:REG_CITES]->(d:RegDocument)\n"
              "OPTIONAL MATCH (a:Artefact {id:d.path})-[:HAS_VERSION]->(v:Version)\n"
              "RETURN d.path AS document, left(d.digest, 12) AS digest_at_tag, collect(DISTINCT l.reg_id) AS links,\n"
              "       collect(DISTINCT c.anchor) AS anchors,\n"
              "       collect(DISTINCT v.tag + ': ' + CASE WHEN v.sha256 = d.digest THEN 'same as tag' ELSE 'differs, ' + left(v.sha256, 12) END) AS versions_in_store\n"
              "ORDER BY document")},
]


def _rows(result) -> list[dict]:
    return [dict(r) for r in result]


class Neo4jStore(Store):
    name = "neo4j"

    def __init__(self, uri: str = URI, auth: tuple[str, str] = AUTH, connection_timeout: float | None = None, instance: str = ""):
        from neo4j import GraphDatabase, NotificationMinimumSeverity  # the driver, in the image; lazy so the module imports without it

        self.uri, self.auth, self.instance = uri, auth, instance
        kw = {"notifications_min_severity": NotificationMinimumSeverity.OFF}
        if connection_timeout:
            kw["connection_timeout"] = connection_timeout
        self._driver = GraphDatabase.driver(uri, auth=auth, **kw)
        self._session = self._driver.session()

    def close(self) -> None:
        self._session.close()
        self._driver.close()

    def run(self, cypher: str, **params):
        return self._session.run(cypher, **params)

    # ---- lifecycle
    def wipe(self) -> None:
        self.run("MATCH (n) DETACH DELETE n").consume()

    def apply_constraints(self) -> list[dict]:
        out = []
        for kind, q in CONSTRAINTS:
            try:
                self.run(q).consume()
                out.append({"type": kind, "cypher": q, "accepted": True, "message": ""})
            except Exception as e:  # noqa: BLE001 — the message is the measurement
                out.append({"type": kind, "cypher": q, "accepted": False, "message": str(e).splitlines()[0][:300]})
        return out

    # ---- loading
    def ensure_agents(self, tool_name: str, version: str, human: dict, llm: dict) -> None:
        self.run("""
            MERGE (tool:Agent {id:'agent:harness'}) SET tool.kind='tool', tool.name=$tool, tool.version=$v
            MERGE (human:Agent {id:$hid}) SET human.kind='human', human.name=$hname
            MERGE (llm:Agent {id:$lid}) SET llm.kind='llm', llm.name=$lname""",
                 tool=tool_name, v=version, hid=human["id"], hname=human["name"], lid=llm["id"], lname=llm["name"]).consume()

    def ensure_person(self, aid: str, handle: str) -> None:
        self.run("MERGE (p:Agent {id:$id}) SET p.kind='human', p.name=$name", id=aid, name=handle).consume()

    def create_activity(self, aid: str, kind: str, at: str, tool: str, note: str, agent_id: str) -> None:
        self.run("""
            MATCH (ag:Agent {id:$agent})
            CREATE (act:Activity {id:$aid, kind:$kind, at:$ts, tool:$tool, note:$note})
            MERGE (act)-[:ASSOCIATED_WITH]->(ag)""", aid=aid, kind=kind, ts=at, tool=tool, note=note, agent=agent_id).consume()

    def upsert_artefact_version(self, path, family, fmt, vid, sha, nbytes, ts, tag, aid) -> None:
        self.run("""
            MERGE (a:Artefact {id:$path}) SET a.path=$path, a.family=$family, a.format=$fmt
            CREATE (v:Version {id:$vid, sha256:$sha, bytes:$bytes, ingested_at:$ts, tag:$tag})
            MERGE (a)-[:HAS_VERSION]->(v)
            WITH a, v
            OPTIONAL MATCH (a)-[c:CURRENT]->(old:Version) DELETE c
            MERGE (a)-[:CURRENT]->(v)
            WITH v MATCH (act:Activity {id:$aid}) MERGE (act)-[:USED]->(v)""",
                 path=path, family=family, fmt=fmt, vid=vid, sha=sha, bytes=nbytes, ts=ts, tag=tag, aid=aid).consume()

    def find_fragment(self, artefact, locator, sha) -> str | None:
        row = self.run("MATCH (f:Fragment {artefact:$art, locator:$loc, sha256:$sha}) RETURN f.id AS id LIMIT 1",
                       art=artefact, loc=locator, sha=sha).single()
        return row["id"] if row else None

    def link_fragment(self, vid, fid) -> None:
        self.run("MATCH (v:Version {id:$vid}), (f:Fragment {id:$fid}) MERGE (v)-[:HAS_FRAGMENT]->(f)", vid=vid, fid=fid).consume()

    def create_fragment(self, vid, fid, locator, sha, text, artefact) -> None:
        self.run("""
            MATCH (v:Version {id:$vid})
            CREATE (f:Fragment {id:$fid, locator:$loc, sha256:$sha, text:$text, artefact:$art})
            MERGE (v)-[:HAS_FRAGMENT]->(f)""", vid=vid, fid=fid, loc=locator, sha=sha, text=text, art=artefact).consume()

    def ensure_entity(self, eid, kind, name) -> None:
        self.run("MERGE (e:Entity {id:$id}) ON CREATE SET e.kind=$kind, e.name=$name", id=eid, kind=kind, name=name).consume()

    def create_assertion(self, props, entity, activity, agent, fragment_ids) -> None:
        self.run("""
            MATCH (act:Activity {id:$aid}), (e:Entity {id:$eid}), (ag:Agent {id:$agent})
            CREATE (x:Assertion {id:$id, predicate:$pred, value:$value, raw_value:$raw, text:$text,
                                 basis:$basis, status:$status, artefact:$art, key:$key,
                                 unresolved:$unres, version:$vtag})
            MERGE (x)-[:ABOUT]->(e)
            MERGE (x)-[:DERIVED_BY]->(act)
            MERGE (x)-[:ATTRIBUTED_TO]->(ag)
            WITH x
            UNWIND $frags AS fid
            MATCH (f:Fragment {id:fid})
            MERGE (x)-[:SUPPORTED_BY]->(f)""",
                 aid=activity, eid=entity, agent=agent, id=props["id"], pred=props["predicate"], value=props["value"],
                 raw=props.get("raw_value"), text=props["text"], basis=props["basis"], status=props.get("status", "proposed"),
                 art=props["artefact"], key=props["key"], unres=props.get("unresolved", False), vtag=props["version"],
                 frags=fragment_ids).consume()

    def link_mentions(self) -> None:
        self.run("""
            MATCH (x:Assertion)-[:ABOUT]->(e:Entity), (x)-[:SUPPORTED_BY]->(f:Fragment)
            MERGE (f)-[:MENTIONS]->(e)""").consume()

    def create_inferred(self, props, entity, activity, agent_id, candidate_for) -> None:
        self.run("""
            MATCH (llm:Agent {id:$lid}), (e:Entity {id:$eid})
            CREATE (act:Activity {id:$aid, kind:'inference', at:$at, tool:$itool, note:$note})
            MERGE (act)-[:ASSOCIATED_WITH]->(llm)
            CREATE (x:Assertion {id:$id, predicate:$pred, value:$value, text:$text, basis:'inferred',
                                 status:'proposed', artefact:$art, key:$key, version:$vtag})
            MERGE (x)-[:ABOUT]->(e)
            MERGE (x)-[:DERIVED_BY]->(act)
            MERGE (x)-[:ATTRIBUTED_TO]->(llm)
            WITH x
            MERGE (g:Gap {id:$gid})
            MERGE (x)-[:CANDIDATE_FOR]->(g)""",
                 lid=agent_id, eid=entity, aid=activity["id"], at=activity["at"], itool=activity["tool"], note=activity["note"],
                 id=props["id"], pred=props["predicate"], value=props["value"], text=props["text"], art=props.get("artefact", "llm"),
                 key=props["key"], vtag=props.get("version", "v1"), gid=candidate_for).consume()

    # ---- verifications and approvals
    def verify_by_execution(self, key, values, suite_scenario, scope, ts, digest) -> int:
        return self.run("""
            MATCH (x:Assertion {key:$key}) WHERE x.value IN $vals AND x.basis IN ['extracted','authored'] AND NOT x.status IN ['invalidated','rejected','deprecated']
            MATCH (h:Agent {id:'agent:harness'})
            MERGE (v:Verification {id:'ver:exec:' + $sc + ':' + x.id})
              SET v.method='execution', v.outcome='pass', v.scope=$scope, v.at=$ts,
                  v.evidence_sha256=$dig, v.valid_until=null
            MERGE (v)-[:VERIFIES]->(x)
            MERGE (v)-[:PERFORMED_BY]->(h)
            SET x.status = CASE WHEN x.status IN ['proposed','validated'] THEN 'verified' ELSE x.status END
            RETURN count(x) AS n""", key=key, vals=values, sc=suite_scenario, scope=scope, ts=ts, dig=digest).single()["n"]

    def verify_by_review(self, key, values, at, scope, agent_id) -> int:
        return self.run("""
            MATCH (x:Assertion {key:$key}) WHERE x.value IN $vals AND x.basis IN ['extracted','authored'] AND NOT x.status IN ['invalidated','rejected','deprecated']
            MATCH (h:Agent {id:$hid})
            MERGE (v:Verification {id:'ver:review:' + x.id})
              SET v.method='review', v.outcome='pass', v.at=$at, v.valid_until=null, v.scope=$scope
            MERGE (v)-[:VERIFIES]->(x)
            MERGE (v)-[:PERFORMED_BY]->(h)
            SET x.status = CASE WHEN x.status IN ['proposed','validated'] THEN 'verified' ELSE x.status END
            RETURN count(x) AS n""", key=key, vals=values, at=at, scope=scope, hid=agent_id).single()["n"]

    def verify_authored(self, at, scope, agent_id) -> int:
        return self.run("""
            MATCH (x:Assertion) WHERE x.basis='authored' AND x.status='proposed' AND x.value <> 'NONE'
            MATCH (h:Agent {id:$hid})
            MERGE (v:Verification {id:'ver:review:' + x.id})
              SET v.method='review', v.outcome='pass', v.at=$at, v.valid_until=null, v.scope=$scope
            MERGE (v)-[:VERIFIES]->(x) MERGE (v)-[:PERFORMED_BY]->(h)
            SET x.status='verified' RETURN count(x) AS n""", at=at, scope=scope, hid=agent_id).single()["n"]

    def approve_verified(self, at, record, agent_id) -> int:
        return self.run("""
            MATCH (x:Assertion {status:'verified'}), (h:Agent {id:$hid})
            MERGE (ap:Approval {id:'appr:' + x.id}) SET ap.at=$at, ap.record=$record
            MERGE (ap)-[:APPROVES]->(x) MERGE (ap)-[:BY]->(h)
            SET x.status='approved' RETURN count(x) AS n""", at=at, record=record, hid=agent_id).single()["n"]

    def reverify(self, version, keys, agent_id, ts, scope, record) -> list[str]:
        return self.run("""
            MATCH (x:Assertion {version:$version}) WHERE x.key IN $keys AND x.status IN ['proposed','validated']
            MATCH (h:Agent {id:$hid})
            MERGE (v:Verification {id:'ver:review:' + $version + ':' + x.id}) SET v.method='review', v.outcome='pass', v.at=$ts,
                  v.scope=$scope, v.valid_until=null
            MERGE (v)-[:VERIFIES]->(x) MERGE (v)-[:PERFORMED_BY]->(h)
            SET x.status='verified'
            WITH x, h MERGE (ap:Approval {id:'appr:' + $version + ':' + x.id}) SET ap.at=$ts, ap.record=$record
            MERGE (ap)-[:APPROVES]->(x) MERGE (ap)-[:BY]->(h) SET x.status='approved'
            RETURN collect(x.id) AS ids""", version=version, keys=keys, hid=agent_id, ts=ts, scope=scope, record=record).single()["ids"]

    def register_derived(self, did, kind, sha, assertion_ids) -> None:
        self.run("""CREATE (dv:Derived {id:$did, kind:$dkind, sha256:$sha, suspect:false})
                    WITH dv UNWIND $ids AS aid MATCH (x:Assertion {id:aid}) MERGE (dv)-[:USED_ASSERTION]->(x)""",
                 did=did, dkind=kind, sha=sha, ids=assertion_ids).consume()

    # ---- the rules
    def structural_violations(self) -> list[dict]:
        v = []
        v += _rows(self.run("""
            MATCH (x:Assertion) WHERE x.basis IN ['extracted','authored'] AND NOT (x)-[:SUPPORTED_BY]->(:Fragment)
            RETURN x.id AS id, 'no supporting fragment' AS why"""))
        v += _rows(self.run("""
            MATCH (x:Assertion) WHERE x.basis IN ['inferred','assumed','hypothesised']
              AND NOT (x)-[:CANDIDATE_FOR|CONCERNED_BY]-(:Gap) AND NOT (:Gap)-[:CONCERNS]->(x)
            RETURN x.id AS id, 'inferred without a gap' AS why"""))
        v += _rows(self.run("MATCH (f:Fragment) WHERE NOT (:Version)-[:HAS_FRAGMENT]->(f) RETURN f.id AS id, 'orphan fragment' AS why"))
        v += _rows(self.run("MATCH (v:Version) WHERE NOT (:Artefact)-[:HAS_VERSION]->(v) RETURN v.id AS id, 'orphan version' AS why"))
        return v

    def candidate_pairs(self, across=None) -> list[dict]:
        return _rows(self.run("""
            MATCH (a:Assertion)-[:ABOUT]->(e:Entity)<-[:ABOUT]-(b:Assertion)
            WHERE a.predicate = b.predicate AND a.id < b.id AND a.artefact <> b.artefact
              AND NOT a.status IN ['rejected','deprecated','invalidated'] AND NOT b.status IN ['rejected','deprecated','invalidated']
              AND (a.version = b.version OR ($across IS NOT NULL AND (a.basis = $across) <> (b.basis = $across)))
            RETURN a.id AS a, a.value AS va, a.basis AS ba, a.artefact AS aa, b.id AS b, b.value AS vb, b.basis AS bb,
                   b.artefact AS ab, a.key AS key, a.predicate AS pred""", across=across))

    def corroborate(self, a, b, promote=True) -> None:
        self.run("""MATCH (a:Assertion {id:$a}), (b:Assertion {id:$b})
                    MERGE (a)-[:CORROBORATES]->(b) MERGE (b)-[:CORROBORATES]->(a)
                    SET a.status = CASE WHEN $promote AND a.status='proposed' THEN 'validated' ELSE a.status END,
                        b.status = CASE WHEN $promote AND b.status='proposed' THEN 'validated' ELSE b.status END""",
                 a=a, b=b, promote=promote).consume()

    def mark_conflict(self, a, b, gid, key, scenario, text=None) -> None:
        self.run("""MATCH (a:Assertion {id:$a}), (b:Assertion {id:$b})
                    MERGE (a)-[:CONTRADICTS]->(b) MERGE (b)-[:CONTRADICTS]->(a)
                    SET a.status='disputed', b.status='disputed'
                    MERGE (g:Gap {id:$gid}) SET g.kind='conflict', g.declared=false,
                       g.text=coalesce($text, 'two artefacts state different values for ' + $key + ': ' + a.artefact + ' says ' + a.value + '; ' + b.artefact + ' says ' + b.value)
                    MERGE (g)-[:CONCERNS]->(a) MERGE (g)-[:CONCERNS]->(b)
                    WITH g MATCH (act:Activity) WHERE act.id STARTS WITH 'act:extract:' + $sc
                    MERGE (g)-[:RAISED_BY]->(act)""", a=a, b=b, gid=gid, key=key, sc=scenario, text=text).consume()

    def vague_fragments(self, words) -> list[dict]:
        return _rows(self.run("""
            MATCH (x:Assertion)-[:SUPPORTED_BY]->(f:Fragment)
            WHERE any(w IN $vague WHERE toLower(f.text) CONTAINS w) AND f.locator CONTAINS 'row/'
            RETURN DISTINCT x.id AS id, x.key AS key, f.id AS fid, f.text AS text""", vague=words))

    def add_ambiguous_gap(self, assertion_id, text, scenario) -> None:
        self.run("""MATCH (x:Assertion {id:$id})
                    MERGE (g:Gap {id:'gap:ambiguous:' + $id}) SET g.kind='ambiguous', g.declared=false, g.text=$text
                    MERGE (g)-[:CONCERNS]->(x)
                    WITH g MATCH (act:Activity) WHERE act.id STARTS WITH 'act:extract:' + $sc
                    MERGE (g)-[:RAISED_BY]->(act)""", id=assertion_id, text=text, sc=scenario).consume()

    def unresolved_assertions(self) -> list[dict]:
        return _rows(self.run("MATCH (x:Assertion {unresolved:true}) RETURN x.id AS id, x.key AS key, x.raw_value AS sym"))

    def declared_open(self, predicate) -> list[dict]:
        return _rows(self.run("MATCH (x:Assertion {predicate:$pred, value:'NONE'})-[:ABOUT]->(e:Entity) RETURN e.id AS entity, x.id AS id", pred=predicate))

    def add_declared_gap(self, gid, text, entity, assertion_id, scenario, key_entity, key) -> None:
        self.run("""MATCH (e:Entity {id:$req}), (x:Assertion {id:$id})
                    MERGE (g:Gap {id:$gid}) SET g.kind='missing', g.declared=true, g.text=$gtext
                    MERGE (g)-[:CONCERNS]->(e) MERGE (g)-[:CONCERNS]->(x)
                    WITH g MATCH (act:Activity) WHERE act.id STARTS WITH 'act:extract:' + $sc
                    MERGE (g)-[:RAISED_BY]->(act)
                    WITH g MATCH (k:Entity {id:$kent}) MERGE (g)-[:CONCERNS_KEY {key:$key}]->(k)""",
                 req=entity, id=assertion_id, gid=gid, gtext=text, sc=scenario, kent=key_entity, key=key).consume()

    def add_absent_artefact_gap(self, artefact, assertion_id) -> None:
        self.run("""MATCH (x:Assertion {id:$id})
                    MERGE (g:Gap {id:'gap:declared:' + $art}) SET g.kind='missing', g.declared=true, g.text=$art + ' is not yet authored'
                    MERGE (g)-[:CONCERNS]->(x)""", id=assertion_id, art=artefact).consume()

    def requirements_without(self, predicate) -> list[str]:
        return [r["req"] for r in self.run("""MATCH (e:Entity {kind:'requirement'}) WHERE NOT (:Assertion {predicate:$pred})-[:ABOUT]->(e)
                                              RETURN e.id AS req""", pred=predicate)]

    def add_unverified_requirement_gap(self, req) -> None:
        self.run("""MATCH (e:Entity {id:$req})
                    MERGE (g:Gap {id:'gap:unverified-req:' + $req}) SET g.kind='missing', g.declared=false,
                       g.text=$req + ' has no verifying scenario'
                    MERGE (g)-[:CONCERNS]->(e)""", req=req).consume()

    def silent_entities(self, kinds) -> list[str]:
        return [r["id"] for r in self.run("""MATCH (e:Entity) WHERE e.kind IN $kinds AND NOT (:Assertion)-[:ABOUT]->(e)
                                             RETURN e.id AS id""", kinds=kinds)]

    def mark_unverified(self) -> int:
        return self.run("""
            MATCH (x:Assertion) WHERE x.status IN ['proposed','validated'] AND NOT (:Verification)-[:VERIFIES]->(x)
            MERGE (g:Gap {id:'gap:unverified:' + x.id}) SET g.kind='unverified', g.declared=false,
               g.text=x.id + ' has no verification record'
            MERGE (g)-[:CONCERNS]->(x)
            RETURN count(x) AS n""").single()["n"]

    def invalidate_stale(self, new_tag) -> dict:
        inv = _rows(self.run("""
            MATCH (x:Assertion)-[:SUPPORTED_BY]->(f:Fragment)<-[:HAS_FRAGMENT]-(old:Version)<-[:HAS_VERSION]-(a:Artefact)-[:CURRENT]->(cur:Version)
            WHERE old <> cur AND x.version <> $tag
            OPTIONAL MATCH (cur)-[:HAS_FRAGMENT]->(nf:Fragment {locator:f.locator})
            WITH x, f, nf WHERE nf IS NULL OR nf.sha256 <> f.sha256
            SET x.status='invalidated', x.invalidated_at=datetime().epochSeconds, x.invalidated_by=$tag
            WITH DISTINCT x
            OPTIONAL MATCH (v:Verification)-[:VERIFIES]->(x) SET v.valid_until=$tag
            WITH DISTINCT x
            OPTIONAL MATCH (d:Derived)-[:USED_ASSERTION]->(x) SET d.suspect=true
            RETURN x.id AS id, x.key AS key, collect(DISTINCT d.id) AS derived""", tag=new_tag))
        kept = _rows(self.run("""
            MATCH (x:Assertion)-[:SUPPORTED_BY]->(f:Fragment)<-[:HAS_FRAGMENT]-(old:Version)<-[:HAS_VERSION]-(a:Artefact)-[:CURRENT]->(cur:Version)
            WHERE old <> cur AND x.version <> $tag AND x.status <> 'invalidated'
            RETURN DISTINCT x.id AS id, x.key AS key, x.status AS status""", tag=new_tag))
        return {"invalidated": inv, "kept": kept}

    # ---- the gate
    def key_evidence(self, key, live) -> list[dict]:
        rows = _rows(self.run("""
            MATCH (x:Assertion {key:$key}) WHERE x.status IN $live
            OPTIONAL MATCH (x)-[:SUPPORTED_BY]->(f:Fragment)
            OPTIONAL MATCH (v:Verification)-[:VERIFIES]->(x)
            OPTIONAL MATCH (ap:Approval)-[:APPROVES]->(x)
            OPTIONAL MATCH (g:Gap)-[:CONCERNS]->(x)
            OPTIONAL MATCH (x)-[:ATTRIBUTED_TO]->(ag:Agent)
            RETURN x.id AS id, x.value AS value, x.text AS text, x.basis AS basis, x.status AS status,
                   x.artefact AS artefact, ag.name AS agent,
                   collect(DISTINCT {locator:f.locator, text:f.text, artefact:f.artefact}) AS fragments,
                   collect(DISTINCT {id:v.id, method:v.method, scope:v.scope, at:v.at, valid_until:v.valid_until}) AS verifications,
                   collect(DISTINCT {id:ap.id, at:ap.at, record:ap.record}) AS approvals,
                   collect(DISTINCT {id:g.id, kind:g.kind, declared:g.declared, text:g.text}) AS gaps
            ORDER BY x.id""", key=key, live=live))
        for r in rows:
            r["fragments"] = [f for f in r["fragments"] if f["locator"]]
            r["verifications"] = [v for v in r["verifications"] if v["id"]]
            r["approvals"] = [a for a in r["approvals"] if a["id"]]
            r["gaps"] = [g for g in r["gaps"] if g["id"]]
        return rows

    def declared_gaps_for_key(self, key) -> list[dict]:
        return _rows(self.run("""
            MATCH (g:Gap {kind:'missing', declared:true})-[c:CONCERNS_KEY {key:$key}]->()
            RETURN g.id AS id, g.text AS text""", key=key))

    def conflict_gaps(self) -> list[dict]:
        return _rows(self.run("MATCH (g:Gap {kind:'conflict'}) RETURN g.id AS id, g.text AS text"))

    def assertion_brief(self, assertion_id) -> dict | None:
        rows = _rows(self.run("""
            MATCH (x:Assertion {id:$id}) OPTIONAL MATCH (x)-[:ATTRIBUTED_TO]->(ag:Agent)
            RETURN x.id AS id, x.key AS key, x.value AS value, x.basis AS basis, x.status AS status, ag.name AS agent""", id=assertion_id))
        return rows[0] if rows else None

    def declared_gap(self, gid) -> dict | None:
        rows = _rows(self.run("""
            MATCH (g:Gap {id:$gid, kind:'missing', declared:true}) OPTIONAL MATCH (g)-[c:CONCERNS_KEY]->()
            RETURN g.id AS id, g.text AS text, [k IN collect(c.key) WHERE k IS NOT NULL] AS keys""", gid=gid))
        return rows[0] if rows else None

    def apply_ruling(self, assertion_id, outcome, review_id, agent_id, at, record, until) -> None:
        if outcome == "approved":
            self.run("""
                MATCH (x:Assertion {id:$id}), (h:Agent {id:$hid})
                MERGE (ap:Approval {id:'appr:' + $rid + ':' + x.id}) SET ap.at=$at, ap.record=$record, ap.until=$until
                MERGE (ap)-[:APPROVES]->(x) MERGE (ap)-[:BY]->(h)
                SET x.status='approved', x.ruled_in=$rid""", id=assertion_id, hid=agent_id, rid=review_id, at=at, record=record, until=until).consume()
        elif outcome == "rejected":
            self.run("MATCH (x:Assertion {id:$id}) SET x.status='rejected', x.ruled_in=$rid", id=assertion_id, rid=review_id).consume()
        elif outcome == "lapsed":
            self.run("MATCH (x:Assertion {id:$id}) SET x.status='proposed', x.lapsed_in=$rid", id=assertion_id, rid=review_id).consume()

    def close_declared_gap(self, gid, review_id, at, record) -> None:
        self.run("""MATCH (g:Gap {id:$gid, kind:'missing', declared:true})
                    SET g.kind='closed', g.declared=false, g.closed_in=$rid, g.closed_on=$at, g.closed_record=$record""",
                 gid=gid, rid=review_id, at=at, record=record).consume()

    def settle_conflicts(self, key, review_id) -> int:
        return self.run("""
            MATCH (g:Gap {kind:'conflict'})-[:CONCERNS]->(x:Assertion {key:$key})
            WITH DISTINCT g SET g.kind='settled', g.settled_in=$rid RETURN count(g) AS n""", key=key, rid=review_id).single()["n"]

    def stale_on_keys(self, keys) -> list[dict]:
        return _rows(self.run("""
            MATCH (x:Assertion {status:'invalidated'}) WHERE x.key IN $keys
            OPTIONAL MATCH (v:Verification)-[:VERIFIES]->(x)
            OPTIONAL MATCH (succ:Assertion {key:x.key, artefact:x.artefact}) WHERE succ.status IN ['proposed','validated','verified','approved']
            RETURN x.id AS id, x.key AS key, x.value AS value, x.invalidated_by AS invalidated_by,
                   collect(DISTINCT {id:v.id, valid_until:v.valid_until}) AS verifications,
                   collect(DISTINCT {id:succ.id, value:succ.value, status:succ.status}) AS successors""", keys=keys))

    def suspect_derived(self) -> list[dict]:
        return _rows(self.run("""
            MATCH (d:Derived {suspect:true})-[:USED_ASSERTION]->(x:Assertion {status:'invalidated'})
            RETURN d.id AS id, d.kind AS kind, d.sha256 AS sha256, collect(x.id) AS used_invalidated"""))

    def all_derived(self) -> list[dict]:
        return _rows(self.run("MATCH (dv:Derived) RETURN dv.id AS id, dv.suspect AS suspect"))

    # ---- the census and the page
    def census(self) -> dict:
        st = {r["status"]: r["n"] for r in self.run("MATCH (x:Assertion) RETURN x.status AS status, count(*) AS n")}
        gaps = {r["kind"]: r["n"] for r in self.run("MATCH (g:Gap) RETURN g.kind AS kind, count(*) AS n")}
        contradicts = self.run("MATCH ()-[r:CONTRADICTS]->() RETURN count(r)/2 AS n").single()["n"]
        nodes = self.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        rels = self.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
        return {"assertions_by_status": st, "gaps_by_kind": gaps, "contradicts": contradicts, "nodes": nodes, "relationships": rels}

    def extraction_activities(self) -> list[str]:
        return [r["id"] for r in self.run("MATCH (a:Activity) WHERE a.id STARTS WITH 'act:extract:' RETURN a.id AS id ORDER BY a.at")]

    def gaps_with_concerns(self) -> list[dict]:
        out = []
        for r in self.run("""MATCH (g:Gap) OPTIONAL MATCH (g)-[r:CONCERNS|CONCERNS_KEY]->(t)
            RETURN g.id AS id, g.kind AS kind, g.declared AS declared, g.text AS text,
                   collect({id:t.id, labels:labels(t), key:t.key, value:t.value, basis:t.basis, status:t.status, rel:type(r), relkey:r.key}) AS concerns
            ORDER BY g.kind, g.id"""):
            out.append({"id": r["id"], "kind": r["kind"], "declared": bool(r["declared"]), "text": r["text"],
                        "concerns": [c for c in r["concerns"] if c["id"] or c["relkey"]]})
        return out

    def assertions_on_key(self, key, statuses) -> list[dict]:
        return _rows(self.run("MATCH (x:Assertion {key:$k}) WHERE x.status IN $st RETURN x.id AS id, x.value AS value, x.status AS status, x.basis AS basis",
                              k=key, st=statuses))

    # ---- the SHACL projection's reads
    def assertion_rows(self) -> list[dict]:
        return _rows(self.run("MATCH (x:Assertion) RETURN x.id AS id, x.basis AS basis, x.status AS status"))

    def supported_by(self) -> list[dict]:
        return _rows(self.run("MATCH (x:Assertion)-[:SUPPORTED_BY]->(f:Fragment) RETURN x.id AS x, f.id AS f"))

    def candidate_for(self) -> list[dict]:
        return _rows(self.run("MATCH (x:Assertion)-[:CANDIDATE_FOR]->(g:Gap) RETURN x.id AS x, g.id AS g"))

    def fragments_with_version(self) -> list[dict]:
        return _rows(self.run("MATCH (f:Fragment) OPTIONAL MATCH (v:Version)-[:HAS_FRAGMENT]->(f) RETURN f.id AS f, v.id AS v"))

    def requirements_verified_by(self) -> list[dict]:
        return _rows(self.run("MATCH (e:Entity {kind:'requirement'}) OPTIONAL MATCH (x:Assertion {predicate:'verified_by'})-[:ABOUT]->(e) RETURN e.id AS e, collect(x.value) AS by"))

    # ---- the register projection
    def project_register(self, r: dict) -> None:
        """Wipe the Register namespace, create the nodes, then the relationships. Only
        Register-labelled nodes are touched; the harness's own graph is never read or written."""
        st: list[tuple[str, dict]] = [("MATCH (n:Register) DETACH DELETE n", {})]
        for label, key in (("RegNode", "nodes"), ("RegType", "types"), ("RegDocument", "documents"), ("RegExternal", "externals"),
                           ("RegLink", "links"), ("RegException", "exceptions")):
            st.append((f"UNWIND $rows AS r CREATE (n:Register:{label}) SET n = r", {"rows": r[key]}))
        st.append(("UNWIND $rows AS r MATCH (c:RegNode {reg_id:r.child}), (p:RegNode {reg_id:r.parent}) CREATE (c)-[:REG_PARENT]->(p)", {"rows": r["parents"]}))
        st.append(("UNWIND $rows AS r MATCH (o:RegNode {reg_id:r.owner}), (n:RegNode {reg_id:r.node}) CREATE (o)-[:REG_OWNS]->(n)", {"rows": r["owners"]}))
        for rtype, items in sorted(r["typed"].items()):
            st.append((f"UNWIND $rows AS r MATCH (s:RegNode {{reg_id:r.source}}), (t:RegNode {{reg_id:r.target}}) CREATE (s)-[e:{rtype}]->(t) SET e = r.props", {"rows": items}))
        st.append(("UNWIND $rows AS r MATCH (s:RegNode {reg_id:r.source}), (x:RegExternal {reg_id:r.external}) CREATE (s)-[e:REG_MAPS_TO]->(x) SET e = r.props", {"rows": r["maps_to"]}))
        st.append(("UNWIND $rows AS r MATCH (l:RegLink {reg_id:r.reg_id}), (n:RegNode {reg_id:r.node}) CREATE (l)-[:REG_LINK_OF {role:r.role}]->(n)", {"rows": r["link_of"]}))
        st.append(("UNWIND $rows AS r MATCH (l:RegLink {reg_id:r.reg_id}), (t:RegType {reg_id:r.type}) CREATE (l)-[:REG_OF_TYPE]->(t)", {"rows": r["of_type"]}))
        st.append(("UNWIND $rows AS r MATCH (l:RegLink {reg_id:r.reg_id}), (d:RegDocument {reg_id:r.path}) CREATE (l)-[:REG_CITES {anchor:r.anchor}]->(d)", {"rows": r["cites"]}))
        st.append(("UNWIND $rows AS r MATCH (e:RegException {reg_id:r.reg_id}), (n:RegNode {reg_id:r.node}) CREATE (e)-[:REG_EXCEPTS {rule:r.rule, expires:r.expires}]->(n)", {"rows": r["excepts"]}))
        for cypher, params in st:
            self.run(cypher, **params).consume()

    def register_census(self) -> dict | None:
        n = self.run("MATCH (n:Register) RETURN count(n) AS n").single()["n"]
        if not n:
            return None
        by_label = {rec["l"]: rec["n"] for rec in self.run(
            "MATCH (n:Register) UNWIND labels(n) AS l WITH l, count(*) AS n WHERE l <> 'Register' RETURN l, n")}
        rels = self.run("MATCH (:Register)-[r]->() RETURN count(r) AS n").single()["n"]
        stamp = self.run("MATCH (n:RegNode) RETURN n.tag AS tag, n.commit AS commit, n.loaded_at AS loaded_at LIMIT 1").single()
        return {"tag": stamp["tag"] if stamp else "", "commit": stamp["commit"] if stamp else "", "loaded_at": stamp["loaded_at"] if stamp else "",
                "nodes": by_label.get("RegNode", 0), "links": by_label.get("RegLink", 0), "by_label": by_label, "relationships": rels, "total": n}

    # ---- what the page shows
    def describe(self) -> dict:
        return {"store": self.name, "uri": self.uri, "browser": BROWSER}

    def saved_queries(self) -> list[dict]:
        return list(SAVED_QUERIES)

    def console_query(self, text: str) -> list[dict]:
        return _rows(self.run(text))
