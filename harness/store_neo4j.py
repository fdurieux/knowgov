"""The Neo4j adapter of the store port: every Cypher statement of the harness and the page, the
Browser link and the saved queries. Graph shape: pumllint kg_experiment/PREREGISTRATION.md §3.

Status is set only here, by the loader's and the rules' methods and by recorded human acts.
The free Community edition serves one database, so ``wipe`` empties it; the constraint
families it refuses are recorded by ``apply_constraints`` (D1).
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid

from store import (DEAD, DOCUMENT_BASES, DUPLICATE, NEO4J_GUARDED, Store, StoreBusy, StoreChanged, StoreFenced, StoreReadOnly, by_content, by_id, held_from, part_list, part_rows,
                   changed_of, setting, stem, suspect_rows, suspicion)

logging.getLogger("neo4j").setLevel(logging.ERROR)

URI = os.environ.get("KG_NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.environ.get("KG_NEO4J_USER", "neo4j"), os.environ.get("KG_NEO4J_PASSWORD", "kgpoc2026"))
BROWSER = os.environ.get("KG_BROWSER_URL", "http://localhost:7474")

# Publication (task-0141.06, decision-0014). One node, outside every evidence label, holds the writer's
# lease and the sequence lock: ``begin`` is raised in its own transaction before a unit commits, ``end``
# set equal to it inside the unit's transaction; a reader pins (begin, end) with begin == end at open and
# checks the pair after every read call. A writer owns the store from open to close by its lease
# (``owner``, a fencing ``epoch``, ``expires``), renewed by a heartbeat; a writer whose lease another took
# cannot raise ``begin`` or commit. Nothing that reads the evidence (wipe, export, the census) sees it.
# A begin left raised by a writer whose lease has run out (killed between raising it and committing) is
# cleared by the next reader under the same lock, and recorded on the node (task-0175).
PUB = "_KgPublication"
PUB_MATCH = f"MATCH (p:{PUB} {{id:'publication'}})"
LEASE_S = 60.0          # the lease's default; KG_NEO4J_LEASE_SECONDS, KG_NEO4J_LOCK_TIMEOUT and KG_NEO4J_READ_WAIT in store.SETTINGS
_on_publish = None      # test hook (SNAP-03): called between raising begin and committing the unit

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

# The impact walk of the register's tools/impact.py, in Cypher, from one literal start (task-0023,
# task-0044). The walk's rules at ieam-register v0.2.6 (its decisions 0007 and 0010): each start kind
# has its steps, every step pointing from the thing changed to what rests on it (IMPACT_STEPS: the
# taxonomy, the relationship types, and whether the node is the link's source or, "(inverse)", its
# target). An edge is live when its link is approved and its far node is neither deprecated nor
# retired; every edge met from an expanded node is reported, a withdrawn edge is reported and not
# followed, so only live edges lead on and only their far ends count as reached. A deprecated or
# retired start expands nothing. No parent climb; owns and maps_to are never walked. The kinds now
# form cycles (a process delivers a product, the product's delivers inverse leads back), so the walk
# is no longer a fixed set of chains: the nodes it expands are those a quantified path of live steps
# reaches from the start (SHORTEST 1 per end node: one path each, found breadth first, as the
# walk's own frontier is), and from each of them every step its kind allows is one row. The step
# predicate is the same text in both places. IMPACT_ROWS is the saved query, one row per edge as the
# panel's table, with whether the walk followed it; IMPACT_PATHS returns the edges as paths, which
# the Browser draws as a graph. Equivalence with walk() is tested over the projection's rows. Each row
# also names the far node's owning unit (task-0047): its owner field, that unit's name, and the sources
# of the approved owns links to it (the owner field's own REG_OWNS edge carries no state), as the panel.
IMPACT_START = "APP-0002"
_LIVE = "NOT {0}.state IN ['deprecated','retired']"
_OK = "{0}.state = 'approved'"
IMPACT_STEPS = [   # (taxonomy, relationship types, the node is the source?)
    ("applications", ("REG_SUPPORTS",), True),
    ("processes", ("REG_DELIVERS", "REG_REALIZES"), True),
    ("processes", ("REG_IS_SUPPORTED_BY",), False),
    ("journeys", ("REG_CONCERNS", "REG_IS_SUPPORTED_BY"), True),
    ("capabilities", ("REG_REQUIRES",), False),
    ("information", ("REG_CRUD", "REG_MANAGES"), False),
    ("products", ("REG_CONCERNS", "REG_DELIVERS"), False),
]
# The register's second walk (its decision 0012, v0.2.7; task-0112): what implements a capability, the
# processes that realise it, then the applications that support those processes. An application has no
# step, so the walk never turns back toward what rests on the capability.
REALISER_STEPS = [
    ("capabilities", ("REG_REALIZES",), False),
    ("processes", ("REG_SUPPORTS",), False),
]
WALK_STEPS = {"dependants": IMPACT_STEPS, "realisers": REALISER_STEPS}

def _step(n: str, r: str, steps: list = IMPACT_STEPS) -> str:
    """The predicate: ``r`` is a step the walk takes from ``n``, by ``n``'s taxonomy."""
    return "(" + "\n      OR ".join(
        f"{n}.taxonomy = '{tax}' AND type({r}) IN [{', '.join(repr(t) for t in types)}] AND {'startNode' if src else 'endNode'}({r}) = {n}"
        for tax, types, src in steps) + ")"


# With children (the register's decision 0014, v0.2.8; task-0112) the walk starts from the node and from
# every approved descendant by parent, at any depth, each walked as the node is (walk_children): the
# same CALL block, once per start, so an edge two starts meet is two rows, as the register lists it.
# A descendant in any other state is not a start; parent is followed down to find the starts, never
# walked as a step and never climbed.
_CHILDREN_STARTS = (
    "MATCH (o:RegNode {{reg_id:'{start}'}})\n"
    "// the starts (decision 0014): the node and every approved descendant by parent, at any depth, and no other descendant\n"
    "MATCH (a:RegNode) WHERE a = o OR (a.state = 'approved' AND EXISTS {{ (a)-[:REG_PARENT]->+(o) }})\n")


def _impact_walk(steps: list = IMPACT_STEPS, children: bool = False) -> str:
    head = (_CHILDREN_STARTS.format(start=IMPACT_START) if children else f"MATCH (a:RegNode {{reg_id:'{IMPACT_START}'}})\n")
    return (head +
            "CALL (a) {\n"
            "  // the nodes the walk expands: the start, if live, and every node a chain of live steps reaches\n"
            f"  MATCH SHORTEST 1 (a) ((x:RegNode)-[s]-(y:RegNode) WHERE {_step('x', 's', steps)}\n"
            f"      AND {_OK.format('s')} AND {_LIVE.format('y')})* (n:RegNode)\n"
            f"  WHERE {_LIVE.format('a')}\n"
            "  // every edge the walk meets from each: one row, live or withdrawn\n"
            f"  MATCH p = (n)-[r]-(t:RegNode) WHERE {_step('n', 'r', steps)}\n"
            "  RETURN p\n"
            "}\n")


_ROWS_TAIL = (
    "WITH a, nodes(p)[0] AS f, relationships(p)[0] AS r, nodes(p)[1] AS t\n"
    "OPTIONAL MATCH (l:RegLink {reg_id: r.reg_id})   // the evidence sits on the link node\n"
    "OPTIONAL MATCH (u:RegNode {reg_id: t.owner})   // the owning unit: the far node's owner field, shown, not walked\n"
    "RETURN f.reg_id AS `from`,\n"
    "       toLower(replace(type(r), 'REG_', '')) + CASE WHEN startNode(r) = f THEN '' ELSE ' (inverse)' END AS relationship,\n"
    "       t.reg_id AS `to`, t.name AS name, t.owner AS unit, u.name AS `unit name`,\n"
    "       [(o:RegNode)-[w:REG_OWNS]->(t) WHERE w.state = 'approved' | o.reg_id] AS `owns links`,\n"
    "       t.state AS `node state`, r.state AS `link state`,\n"
    "       CASE WHEN NOT (r.state = 'approved' AND NOT t.state IN ['deprecated','retired']) THEN 'no, withdrawn'\n"
    "            WHEN t = a THEN 'yes, back to the start, not counted'   // decision 0016: the start is never reached\n"
    "            ELSE 'yes' END AS followed,\n"
    "       r.owner AS owner, l.evidence AS evidence, r.reg_id AS link\n"
    "ORDER BY link, `from`")
_WHAT = {("dependants", False): "the walk tools/impact.py makes",
         ("dependants", True): "the walk tools/impact.py --children makes, from the node and each approved descendant",
         ("realisers", False): "the walk tools/impact.py --walk realisers makes, toward what implements the node",
         ("realisers", True): "the walk tools/impact.py --walk realisers --children makes, from the node and each approved descendant"}


def impact_texts(walk: str = "dependants", children: bool = False) -> dict:
    """Both forms of one walk from the adapter's literal start: the rows form, one row per edge as the
    panel lists them, and the paths form for the Browser's graph view."""
    w = _impact_walk(WALK_STEPS[walk], children)
    return {"rows": f"// {_WHAT[(walk, children)]}, one row per edge, as the impact panel lists them, a withdrawn edge listed and not followed\n" + w + _ROWS_TAIL,
            "paths": ("// the same walk as paths, for the Browser's graph view: a start with no edge still draws itself\n"
                      + w.replace("CALL (a) {\n", "OPTIONAL CALL (a) {\n") + "RETURN a, p")}


IMPACT_WALK = _impact_walk()
IMPACT_ROWS = impact_texts()["rows"]
IMPACT_PATHS = impact_texts()["paths"]
IMPACT_VARIANTS = {f"{w}{'-children' if c else ''}": (w, c) for w in WALK_STEPS for c in (False, True)}   # the guide routes' names


# Two fixed questions beside the walk, older than its per-kind steps (doc-0008 §4): from a capability,
# what realises or requires it (the walk follows requires only: realising is "what implements this",
# decision 0010's second walk); from an information node, what creates, reads, updates, deletes or
# manages it. Each then goes one step on from each process among them over an approved link. The same rule as the walk: every edge met is a row, a withdrawn one (link not
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
# namespaces share is the document's path, so it reaches a whole document, not the cited anchor:
# the file artefact of that path, or that file's fragments in a directory artefact (task-0077).
MODULE_STORE = (
    "// from a node to the store: the documents its approved links cite, the assertions they support now,\n"
    "// and the derived code built on them, at the grain of a whole document\n"
    f"MATCH (n:RegNode {{reg_id:'{IMPACT_START}'}})<-[:REG_LINK_OF]-(l:RegLink {{state:'approved'}})-[:REG_CITES]->(d:RegDocument)\n"
    "MATCH (a:Artefact) WHERE a.id = d.path OR (a.id ENDS WITH '/' AND d.path STARTS WITH a.id)\n"
    "MATCH (a)-[:CURRENT]->(:Version)-[:HAS_FRAGMENT]->(f:Fragment)<-[:SUPPORTED_BY]-(x:Assertion)\n"
    "WHERE a.id = d.path OR f.locator STARTS WITH substring(d.path, size(a.id)) + ':'\n"
    "OPTIONAL MATCH (dv:Derived)-[:USED_ASSERTION]->(x)\n"
    "RETURN l.reg_id AS link, d.path AS document, count(DISTINCT x) AS assertions,\n"
    "       collect(DISTINCT x.status) AS statuses, collect(DISTINCT dv.id + CASE WHEN dv.suspect THEN ' (suspect)' ELSE '' END) AS derived\n"
    "ORDER BY link, document")
# The same join at the grain of the cited anchor (task-0046; doc-0011 point 1): a citation with an
# anchor (kit:contract/decision_table.md#DT-P) reaches only the fragments whose locator holds the
# anchor as a path segment (DT-P/row/P1, row/REQ-05); one without an anchor cites the whole
# document. A document is a file artefact (Artefact.id = path) or a file of a directory artefact
# (task-0077: J-F's contracts/ holds chain.md, whose fragments are chain.md:row/15), the segments
# then read after the file's "<name>:". Every version is read, so a statement a change invalidated
# still shows the derived code that used it. One row per statement. Parameterised ($start) for the port's register_node_statements;
# the saved query is the same text with the literal start the page replaces.
_NODE_STATEMENTS = (
    "// from a node to the statements its approved links cite, at the grain of the cited anchor where the citation\n"
    "// names one (#DT-P reaches DT-P/row/P1, not the whole table), and on to the derived code that used them\n"
    "MATCH (n:RegNode {reg_id:$start})<-[:REG_LINK_OF]-(l:RegLink {state:'approved'})-[c:REG_CITES]->(d:RegDocument)\n"
    "WITH l, d, CASE WHEN c.anchor CONTAINS '#' THEN split(c.anchor, '#')[1] ELSE null END AS anchor\n"
    "MATCH (a:Artefact) WHERE a.id = d.path OR (a.id ENDS WITH '/' AND d.path STARTS WITH a.id)\n"
    "WITH l, d, anchor, a, CASE WHEN a.id = d.path THEN '' ELSE substring(d.path, size(a.id)) + ':' END AS file\n"
    "MATCH (a)-[:HAS_VERSION]->(v:Version)-[:HAS_FRAGMENT]->(f:Fragment)<-[:SUPPORTED_BY]-(x:Assertion)\n"
    "WHERE f.locator STARTS WITH file AND (anchor IS NULL OR anchor IN split(substring(f.locator, size(file)), '/'))\n"
    "OPTIONAL MATCH (dv:Derived)-[:USED_ASSERTION]->(x)\n"
    "RETURN x.id AS statement, x.status AS status, d.path AS document,\n"
    "       collect(DISTINCT coalesce(anchor, '(whole document)')) AS anchors, collect(DISTINCT l.reg_id) AS links,\n"
    "       collect(DISTINCT v.tag) AS versions, collect(DISTINCT f.locator) AS fragments,\n"
    "       collect(DISTINCT dv.id + CASE WHEN dv.suspect THEN ' (suspect)' ELSE '' END) AS derived\n"
    "ORDER BY document, statement")
NODE_STATEMENTS = _NODE_STATEMENTS.replace("$start", f"'{INFORMATION_START}'")
# The citations beside the store's versions of what they cite (task-0088), joined as _NODE_STATEMENTS
# joins: the file artefact of the path, whose version digest is the file's and is compared with the
# register's digest at the tag; or the file as a part of a directory artefact (J-F's contracts/chain.md
# in contracts/), whose version digest is the whole directory's, so the file's own digest, which the
# load keeps in the version's part_sha256 (task-0094), is compared instead, and the row names the directory.
REGISTER_CITES = (
    "// the register's digest at the tag beside the store's per version: 'same as tag' or 'differs' for a file artefact, and for\n"
    "// a file of a directory artefact, whose version's digest is the bundle's, the file's own from part_sha256 (task-0094)\n"
    "MATCH (l:RegLink)-[c:REG_CITES]->(d:RegDocument)\n"
    "OPTIONAL MATCH (a:Artefact) WHERE a.id = d.path OR (a.id ENDS WITH '/' AND d.path STARTS WITH a.id)\n"
    "OPTIONAL MATCH (a)-[:HAS_VERSION]->(v:Version)\n"
    "WITH l, c, d, a, v, CASE WHEN a.id <> d.path THEN\n"
    "       [x IN coalesce(v.part_sha256, []) WHERE x ENDS WITH '  ' + substring(d.path, size(a.id)) | left(x, 64)][0] END AS part\n"
    "RETURN d.path AS document, left(d.digest, 12) AS digest_at_tag, collect(DISTINCT l.reg_id) AS links,\n"
    "       collect(DISTINCT c.anchor) AS anchors,\n"
    "       collect(DISTINCT CASE WHEN a.id = d.path THEN v.tag + ': ' + CASE WHEN v.sha256 = d.digest THEN 'same as tag' ELSE 'differs, ' + left(v.sha256, 12) END\n"
    "                             WHEN part IS NOT NULL THEN v.tag + ': in ' + a.id + ', ' + CASE WHEN part = d.digest THEN 'same as tag' ELSE 'differs, ' + left(part, 12) END END) AS versions_in_store\n"
    "ORDER BY document")
PRELOAD_FIELDS = ("state", "tool", "tool_version", "digest", "report", "why")   # a Version's preload_* properties (task-0064)
# The literal start each saved query carries, by the taxonomy the page picks its default from.
CHILDREN_START = "CAP-0001"   # a capability with descendants, for the children forms (task-0112)
START_LITERALS = {"applications": IMPACT_START, "capabilities": CAPABILITY_START, "information": INFORMATION_START,
                  "capabilities+children": CHILDREN_START}


def impact_cypher(start: str, walk: str = "dependants", children: bool = False) -> dict:
    """Both forms of the walk from ``start`` in place of the adapter's literal: the page lists them
    with the register's default start and the impact panel with the id the viewer typed (task-0024),
    for either walk, with or without children (task-0112)."""
    sub = lambda text: text.replace(f"'{IMPACT_START}'", f"'{start}'")  # noqa: E731
    return {form: sub(text) for form, text in impact_texts(walk, children).items()}


def node_statements_cypher(start: str) -> str:
    """The saved query register-node-statements from ``start`` in place of the adapter's literal: the
    impact panel's statements view lists it, and its guide serves it, for the id typed (task-0078)."""
    return NODE_STATEMENTS.replace(f"{{reg_id:'{INFORMATION_START}'}}", f"{{reg_id:'{start}'}}")

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
    # the other three variants of the walk (task-0112); a children form starts from a capability with descendants
    {"id": "register-impact-children", "needs": "register", "start": "capabilities+children",
     "text": impact_cypher(CHILDREN_START, "dependants", True)["rows"],
     "title": f"The impact walk from {CHILDREN_START} and every approved descendant by parent: tools/impact.py --children, one row per edge"},
    {"id": "register-realisers", "needs": "register", "start": "capabilities", "text": impact_cypher(CAPABILITY_START, "realisers")["rows"],
     "title": f"What realises {CAPABILITY_START}: tools/impact.py --walk realisers, the processes that realise it and the applications that support them"},
    {"id": "register-realisers-children", "needs": "register", "start": "capabilities+children",
     "text": impact_cypher(CHILDREN_START, "realisers", True)["rows"],
     "title": f"What realises {CHILDREN_START} and every approved descendant by parent: tools/impact.py --walk realisers --children"},
    {"id": "register-dependants-capability", "needs": "register", "start": "capabilities",
     "title": f"What rests on {CAPABILITY_START}: what realises or requires it, then one step on, approved links only",
     "text": DEPENDANTS_CAPABILITY},
    {"id": "register-dependants-information", "needs": "register", "start": "information",
     "title": f"What touches {INFORMATION_START}: what creates, reads, updates, deletes or manages it, then one step on, approved links only",
     "text": DEPENDANTS_INFORMATION},
    {"id": "register-node-store", "needs": "register+scenario", "start": "applications",
     "title": f"From {IMPACT_START} to the store: the documents its approved links cite, their assertions and the derived code",
     "text": MODULE_STORE},
    {"id": "register-node-statements", "needs": "register+scenario", "start": "information",
     "title": f"From {INFORMATION_START} to the statements its cited anchors name, every version, and the derived code that used them",
     "text": NODE_STATEMENTS},
    {"id": "register-c1", "needs": "register", "title": "C1 in Cypher: approved steps and touchpoints with no is_supported_by link, the exception joined",
     "text": ("MATCH (s:RegNode {taxonomy:'journeys', state:'approved'}) WHERE s.kind IN ['step', 'touchpoint']\n"
              "  AND NOT (s)-[:REG_IS_SUPPORTED_BY]->(:RegNode)\n"
              "OPTIONAL MATCH (e:RegException {rule:'C1'})-[x:REG_EXCEPTS]->(s)\n"
              "RETURN s.reg_id AS uncovered, s.name AS name, e.reg_id AS exception, x.expires AS expires")},
    {"id": "register-cites", "needs": "register+scenario", "title": "The links that cite a kit document, joined to the harness's Artefact by path, or as a file of a directory artefact, each compared with the register's digest: the one query across both namespaces",
     "text": REGISTER_CITES},
]


def _distinct_rows(rows: list[dict]) -> list[dict]:
    """``rows`` without repeats (a fragment matched twice), in their order."""
    import json
    seen, out = set(), []
    for r in rows:
        k = json.dumps(r, sort_keys=True, default=str)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def _rows(result) -> list[dict]:
    return [dict(r) for r in result]


def _refuse_taken(st, label: str, nid: str) -> None:
    """store.UNIQUE_IDS for a label no Neo4j constraint holds here (NEO4J_GUARDED; task-0201, doc-0030 S4)."""
    assert label in NEO4J_GUARDED, label
    if _rows(st.run(f"MATCH (n:{label} {{id:$id}}) RETURN count(n) AS n", id=nid))[0]["n"]:
        raise ValueError(DUPLICATE.format(nid=nid))


class _Unit:
    """A handle's publication (task-0141.06, decision-0014): for a writer, the lease, the unit's one
    transaction and the sequence lock it publishes under; for a reader, the generation it pinned."""

    def __init__(self, driver, session, uri: str, access: str, read_mode, write_mode):
        self.driver, self.session, self.uri, self.access = driver, session, uri, access
        self.read_mode, self.write_mode = read_mode, write_mode
        self.tx = None                  # the unit's one transaction, begun at its first statement
        self.wipe_pending = False       # a wipe asked before the transaction began, run as its first statement
        self.after_commit: list[str] = []
        self.token, self.epoch, self.lost = None, None, False
        self.beat_stop = threading.Event()
        self.pinned = None
        self.recovered = None           # what this reader cleared at its pin: the abandoning writer (task-0175)
        self.lease_s = LEASE_S

    # ---- statements outside the unit
    def meta(self, work):
        """``work(tx)`` in a managed write transaction of its own session, retried on a transient error
        (a deadlock with another writer's lease) for at most the driver's bounded retry time."""
        with self.driver.session(default_access_mode=self.write_mode) as s:
            return s.execute_write(work)

    def schema(self, cypher: str) -> None:
        """A schema statement, which Neo4j will not run in a transaction that has written data."""
        with self.driver.session(default_access_mode=self.write_mode) as s:
            s.run(cypher).consume()

    # ---- the writer's lease
    def acquire(self, wait: float, lease_s: float) -> None:
        self.lease_s = lease_s
        token, ms = uuid.uuid4().hex, int(lease_s * 1000)

        def take(tx):
            tx.run(f"MERGE (p:{PUB} {{id:'publication'}}) ON CREATE SET p.begin = 0, p.end = 0, p.epoch = 0").consume()
            tx.run(f"{PUB_MATCH} SET p.lock_seq = coalesce(p.lock_seq, 0) + 1").consume()   # the node's write lock, then read
            r = tx.run(f"{PUB_MATCH} RETURN p.owner AS owner, p.expires < datetime() AS expired").single()
            if r["owner"] is not None and not r["expired"]:
                return None
            # free, or its owner's lease ran out: that owner can no longer raise begin or commit (its epoch
            # is gone), so a begin it raised and never matched is closed here; the data is its predecessor's
            return tx.run(f"{PUB_MATCH} SET p.owner = $t, p.epoch = p.epoch + 1, p.end = p.begin, "
                          "p.expires = datetime() + duration({milliseconds: $ms}) RETURN p.epoch AS epoch",
                          t=token, ms=ms).single()["epoch"]
        self.schema(f"CREATE CONSTRAINT kg_publication IF NOT EXISTS FOR (p:{PUB}) REQUIRE p.id IS UNIQUE")
        deadline = time.monotonic() + max(0.0, wait)
        while True:
            epoch = self.meta(take)
            if epoch is not None:
                break
            if time.monotonic() >= deadline:
                raise StoreBusy(f"{self.uri}: another writer holds the store (waited {wait:g} s; KG_NEO4J_LOCK_TIMEOUT sets how long)")
            time.sleep(0.1)
        self.token, self.epoch = token, epoch
        self.terminate_stale()
        threading.Thread(target=self.heartbeat, daemon=True).start()

    def terminate_stale(self) -> None:
        """Fence on the server: a unit transaction of an earlier owner (its lease ran out, so it can no
        longer publish) is terminated, so its locks do not hold this writer and it can never commit."""
        try:
            with self.driver.session(default_access_mode=self.write_mode) as s:
                ids = [r["id"] for r in s.run(
                    "SHOW TRANSACTIONS YIELD transactionId AS id, metaData AS m "
                    "WHERE m.kg_writer IS NOT NULL AND m.kg_epoch <> $e RETURN id", e=self.epoch)]
                if ids:
                    s.run("TERMINATE TRANSACTIONS $ids", ids=ids).consume()
        except Exception:  # noqa: BLE001 — an edition or role without these commands: the epoch check still fences the commit
            pass

    def owned(self, tx, then: str = "", **params):
        """Inside ``tx``: lock the publication node, then ``then`` only if this writer still owns it."""
        tx.run(f"{PUB_MATCH} SET p.lock_seq = coalesce(p.lock_seq, 0) + 1").consume()
        return tx.run(f"{PUB_MATCH} WHERE p.owner = $t AND p.epoch = $e {then} RETURN p.begin AS begin, p.end AS end",
                      t=self.token, e=self.epoch, **params).single()

    def heartbeat(self) -> None:
        ms = int(self.lease_s * 1000)
        while not self.beat_stop.wait(self.lease_s / 3):
            try:
                ok = self.meta(lambda tx: self.owned(tx, "SET p.expires = datetime() + duration({milliseconds: $ms})", ms=ms))
            except Exception:  # noqa: BLE001 — a missed beat; the next one, or the lease, decides
                continue
            if ok is None:
                self.lost = True
                return

    def release(self) -> None:
        self.beat_stop.set()
        if self.token is None:
            return
        try:
            self.meta(lambda tx: self.owned(tx, "SET p.owner = null, p.expires = null"))
        except Exception:  # noqa: BLE001 — the lease runs out on its own
            pass
        self.token = None

    # ---- the reader's pin
    def state(self) -> dict | None:
        """The publication as a reader finds it: the counter's pair, the owner and whether its lease ran out."""
        with self.driver.session(default_access_mode=self.read_mode) as s:
            r = s.run(f"{PUB_MATCH} RETURN p.begin AS b, p.end AS e, p.owner AS owner, p.epoch AS epoch, "
                      "coalesce(p.expires < datetime(), true) AS expired").single()
        return dict(r) if r else None

    def recover(self) -> dict | None:
        """Clear a publication its writer abandoned (task-0175): under the sequence lock, and only while
        ``begin`` is still above ``end`` and no live lease holds the node, close the gap at the last
        committed generation (``begin = end``), free the lease and move the epoch on, so the abandoning
        writer, were it alive, can neither raise ``begin`` nor commit. A writer that took the lease first
        closed the gap itself (``acquire``), so this finds nothing; one that comes after finds the lease
        free. Returns what was cleared (the abandoning owner and epoch), or None when there was nothing."""
        def clear(tx):
            tx.run(f"{PUB_MATCH} SET p.lock_seq = coalesce(p.lock_seq, 0) + 1").consume()   # the node's write lock, then read
            r = tx.run(f"{PUB_MATCH} WHERE p.begin <> p.end AND (p.owner IS NULL OR coalesce(p.expires < datetime(), true)) "
                       "WITH p, p.owner AS owner, p.epoch AS epoch, p.begin AS begin "
                       "SET p.begin = p.end, p.owner = null, p.expires = null, p.epoch = p.epoch + 1, "
                       "p.abandoned_owner = owner, p.abandoned_epoch = epoch, p.abandoned_begin = begin, p.recovered_at = datetime() "
                       "RETURN owner, epoch, begin, p.end AS end").single()
            return dict(r) if r else None
        return self.meta(clear)

    def generation(self) -> tuple[int, int] | None:
        """One autocommit read, unretried: an unreachable store fails at the connection timeout."""
        with self.driver.session(default_access_mode=self.read_mode) as s:
            r = s.run(f"{PUB_MATCH} RETURN p.begin AS b, p.end AS e").single()
        return (int(r["b"]), int(r["e"])) if r else None

    def pin(self, wait: float) -> None:
        """The published generation this read handle answers from: begin == end, or none yet. A
        publication in flight under a live lease is waited out, then refused; one whose writer's lease
        ran out is cleared here (``recover``) and the last committed generation answered (task-0175)."""
        deadline = time.monotonic() + max(0.0, wait)
        while True:
            st = self.state()
            g = None if st is None else (int(st["b"]), int(st["e"]))
            if g is None or g[0] == g[1]:
                self.pinned = g
                return
            if st["owner"] is None or st["expired"]:
                try:
                    self.recovered = self.recover()
                except Exception as e:  # noqa: BLE001 — a role that may not write: report the abandoning writer instead
                    raise StoreBusy(f"{self.uri}: a publication was abandoned (generation {g[1]} to {g[0]}) by writer epoch "
                                    f"{st['epoch']}, whose lease has run out, and this reader could not clear it "
                                    f"({type(e).__name__}); the next writer recovers it") from None
                if self.recovered is not None:
                    continue   # cleared: read the pair again, now the last committed generation
                # nothing to clear: a writer took the lease first and closes the gap itself; read again below
            if time.monotonic() >= deadline:
                raise StoreBusy(f"{self.uri}: a publication is in flight (generation {g[1]} to {g[0]}) under writer epoch "
                                f"{st['epoch']}'s live lease; retry, or wait for that lease to run out "
                                "(KG_NEO4J_READ_WAIT sets the wait)")
            time.sleep(0.05)

    def check(self) -> None:
        if self.generation() != self.pinned:
            raise StoreChanged(f"{self.uri}: a new generation was published during this read; read again")

    # ---- the unit's transaction
    def begin(self):
        if self.tx is None:
            self.tx = self.session.begin_transaction(metadata={"kg_writer": self.token, "kg_epoch": self.epoch})
            if self.wipe_pending:
                self.wipe_pending = False
                self.tx.run(f"MATCH (n) WHERE NOT n:{PUB} DETACH DELETE n").consume()
        return self.tx

    def publish(self) -> None:
        """Raise ``begin`` in its own transaction, then set ``end`` and commit the unit's transaction;
        a writer that lost its lease publishes nothing (StoreFenced)."""
        if self.token is None:
            raise StoreBusy(f"{self.uri}: this writer was closed; it no longer holds the store and cannot publish")
        if self.tx is None and not self.wipe_pending:
            return   # nothing written: nothing to publish
        tx = self.begin()
        raised = False
        try:
            if self.lost or self.meta(lambda t: self.owned(t, "SET p.begin = p.end + 1")) is None:
                raise StoreFenced(f"{self.uri}: this writer's lease was taken by another; nothing published")
            raised = True
            if _on_publish is not None:
                _on_publish(self)
            if self.owned(tx, "SET p.end = p.begin") is None:
                raise StoreFenced(f"{self.uri}: this writer's lease was taken by another; nothing published")
            tx.commit()
        except BaseException:
            self.drop()
            if raised:   # the unit never committed: close the gap it opened, while this writer still owns the store
                try:
                    self.meta(lambda t: self.owned(t, "SET p.begin = p.end"))
                except Exception:  # noqa: BLE001 — the next writer closes it at acquisition
                    pass
            raise
        self.tx = None
        for cypher in self.after_commit:
            try:
                self.schema(cypher)
            except Exception:  # noqa: BLE001 — housekeeping only
                pass
        self.after_commit = []

    def drop(self) -> None:
        if self.tx is not None:
            for step in (self.tx.rollback, self.tx.close):
                try:
                    step()
                except Exception:  # noqa: BLE001 — a closed connection has rolled it back already
                    pass
            self.tx = None
        self.wipe_pending = False


class Neo4jStore(Store):
    name = "neo4j"

    def __init__(self, uri: str = URI, auth: tuple[str, str] = AUTH, connection_timeout: float | None = None, instance: str = "",
                 access: str = "write", lock_timeout: float | None = None, lease_seconds: float | None = None, **_ignored):
        from neo4j import GraphDatabase, NotificationMinimumSeverity  # the driver, in the image; lazy so the module imports without it
        from neo4j import READ_ACCESS, WRITE_ACCESS

        if access not in ("read", "write"):
            raise ValueError(f"access is read or write, not {access!r}")
        self.uri, self.auth, self.instance, self.access = uri, auth, instance, access
        kw = {"notifications_min_severity": NotificationMinimumSeverity.OFF, "max_transaction_retry_time": 5.0}
        if connection_timeout:
            kw["connection_timeout"] = connection_timeout
        self._driver = GraphDatabase.driver(uri, auth=auth, **kw)
        # task-0141.02: a read handle's session is in read access mode, so the server refuses a write
        # as well as the port's ReadOnly view
        self._session = self._driver.session(default_access_mode=READ_ACCESS if access == "read" else WRITE_ACCESS)
        self._pub = _Unit(self._driver, self._session, uri, access, READ_ACCESS, WRITE_ACCESS)
        self._constraints = None        # D1 as measured once by this handle, before its transaction
        try:
            if access == "write":
                wait = lock_timeout if lock_timeout is not None else setting("KG_NEO4J_LOCK_TIMEOUT", connection_timeout)
                self._pub.acquire(wait, lease_seconds or setting("KG_NEO4J_LEASE_SECONDS"))
            else:
                self._pub.pin(setting("KG_NEO4J_READ_WAIT"))
                self._after_read = self._pub.check   # store.ReadOnly calls it after every read (task-0141.06)
        except BaseException:
            self._session.close()
            self._driver.close()
            raise

    def commit(self) -> None:
        """Publish the unit whole (decision-0014); a read handle publishes nothing."""
        if self.access != "write":
            raise StoreReadOnly(f"{self.uri}: a read handle publishes nothing")
        self._pub.publish()

    def abort(self) -> None:
        """Drop the unit: its transaction is rolled back, so nothing of it was ever visible."""
        self._pub.drop()

    def close(self) -> None:
        """Release the handle: an unpublished unit is dropped, the lease released. Never publishes."""
        try:
            self._pub.drop()
            self._pub.release()
        finally:
            self._session.close()
            self._driver.close()

    def run(self, cypher: str, **params):
        if self.access == "write":
            return self._pub.begin().run(cypher, **params)
        return self._session.run(cypher, **params)

    # ---- lifecycle
    def wipe(self) -> None:
        import load_memory
        load_memory.wiped(self)   # task-0176: what this wipe deletes counts towards the unit's transaction memory
        if self.access == "write" and self._pub.tx is None:
            self._pub.wipe_pending = True   # run first in the unit's transaction, so a constraint can be applied before it
            return
        self.run(f"MATCH (n) WHERE NOT n:{PUB} DETACH DELETE n").consume()

    # ---- portability (task-0070): the graph through the rdflib adapter's property-graph layer,
    # so the Turtle is that adapter's form whichever store wrote it
    def export_turtle(self) -> str:
        from store_rdflib import RdflibStore
        g = RdflibStore(path="")
        made = {}
        for r in self.run(f"MATCH (n) WHERE NOT n:{PUB} RETURN elementId(n) AS el, labels(n) AS labels, properties(n) AS props"):
            props, labels = dict(r["props"]), list(r["labels"])
            nid = props.get("id")
            if nid is None and "reg_id" in props:   # a register node: named as the rdflib adapter names it
                nid = f"reg:{next((x for x in labels if x != 'Register'), 'Register')}:{props['reg_id']}"
            made[r["el"]] = g.create_node(nid if nid is not None else f"el:{r['el']}", labels, props)
        for r in self.run("MATCH (a)-[e]->(b) RETURN elementId(a) AS a, type(e) AS type, elementId(b) AS b, properties(e) AS props"):
            g.create_edge(made[r["a"]], r["type"], made[r["b"]], dict(r["props"]) or None)
        return g.export_turtle()

    def import_turtle(self, text: str) -> None:
        from store_rdflib import RdflibStore
        g = RdflibStore(path="")
        g.import_turtle(text)
        q = lambda name: "`" + name.replace("`", "``") + "`"  # noqa: E731
        self.wipe()
        if self._pub.tx is None:   # a schema statement before the unit's transaction; only a speed-up, so skipped inside one
            self._pub.schema("CREATE INDEX kg_import IF NOT EXISTS FOR (n:_KgImport) ON (n._kg)")
            self._pub.schema("CALL db.awaitIndexes()")
            self._pub.after_commit.append("DROP INDEX kg_import IF EXISTS")
        runs: list[tuple[tuple, list]] = []   # consecutive nodes with one label set, in store order
        for nid, n in g._nodes.items():
            labels = tuple(g.labels(n))
            props = g.props(n)
            if "Register" in labels and "reg_id" in props:
                props.pop("id", None)   # the Neo4j register carries reg_id only (project_register)
            if not runs or runs[-1][0] != labels:
                runs.append((labels, []))
            runs[-1][1].append({"k": nid, "props": props})
        for labels, rows in runs:
            self.run(f"UNWIND $rows AS r CREATE (n:_KgImport{''.join(':' + q(x) for x in labels)}) SET n = r.props, n._kg = r.k",
                     rows=rows).consume()
        edges: list[tuple[str, list]] = []
        key = {n: nid for nid, n in g._nodes.items()}
        for n in g._nodes.values():
            for e, dst in g.edges_out(n):
                t = g._edge(e)[1]
                if not edges or edges[-1][0] != t:
                    edges.append((t, []))
                edges[-1][1].append({"a": key[n], "b": key[dst], "props": g.props(e)})
        for t, rows in edges:
            self.run(f"UNWIND $rows AS r MATCH (a:_KgImport {{_kg:r.a}}), (b:_KgImport {{_kg:r.b}}) CREATE (a)-[e:{q(t)}]->(b) SET e = r.props",
                     rows=rows).consume()
        self.run("MATCH (n:_KgImport) REMOVE n:_KgImport, n._kg").consume()

    def transaction_memory(self) -> dict | None:
        """The smallest transaction memory limit the server sets (the per-transaction, the per-database and
        the server-wide total; 0 is unset) and the published generation's statements (assertions and
        fragments), read once per handle in a session of its own, outside the unit (task-0176)."""
        if getattr(self, "_tx_memory", None) is not None:
            return self._tx_memory
        import load_memory
        names = ("db.memory.transaction.max", "db.memory.transaction.total.max", "dbms.memory.transaction.total.max")
        rows, published = {}, 0
        with self._pub.driver.session(default_access_mode=self._pub.read_mode) as s:
            try:
                rows = {r["name"]: r["value"] for r in s.run("SHOW SETTINGS YIELD name, value WHERE name IN $n RETURN name, value", n=list(names))}
            except Exception:  # noqa: BLE001 — a role or edition that cannot list settings: no limit to forecast against
                rows = {}
            published = s.run("CALL { MATCH (a:Assertion) RETURN count(a) AS a } CALL { MATCH (f:Fragment) RETURN count(f) AS f } "
                              "RETURN a + f AS n").single()["n"]
        limits = sorted((load_memory.parse_size(rows.get(n)), n, rows.get(n)) for n in names if load_memory.parse_size(rows.get(n)) > 0)
        self._tx_memory = {"limit": {"bytes": limits[0][0], "setting": limits[0][1], "value": limits[0][2]} if limits else None,
                           "published": int(published)}
        return self._tx_memory

    def apply_constraints(self) -> list[dict]:
        """Each constraint family in a schema statement of its own, before the unit's transaction (Neo4j
        refuses schema changes in a transaction that wrote data); measured once per handle, since every
        statement is IF NOT EXISTS and a second measurement answers as the first."""
        if self._constraints is not None:
            return [dict(c) for c in self._constraints]
        out = []
        for kind, q in CONSTRAINTS:
            try:
                self._pub.schema(q) if self.access == "write" else self.run(q).consume()
                out.append({"type": kind, "cypher": q, "accepted": True, "message": ""})
            except Exception as e:  # noqa: BLE001 — the message is the measurement
                out.append({"type": kind, "cypher": q, "accepted": False, "message": str(e).splitlines()[0][:300]})
        self._constraints = out
        return [dict(c) for c in out]

    # ---- loading
    def ensure_agents(self, tool_name: str, version: str, human: dict, llm: dict) -> None:
        self.run("""
            MERGE (tool:Agent {id:'agent:harness'}) SET tool.kind='tool', tool.name=$tool, tool.version=$v
            MERGE (human:Agent {id:$hid}) SET human.kind='human', human.name=$hname
            MERGE (llm:Agent {id:$lid}) SET llm.kind='llm', llm.name=$lname""",
                 tool=tool_name, v=version, hid=human["id"], hname=human["name"], lid=llm["id"], lname=llm["name"]).consume()

    def ensure_person(self, aid: str, handle: str) -> None:
        self.run("MERGE (p:Agent {id:$id}) SET p.kind='human', p.name=$name", id=aid, name=handle).consume()

    def create_activity(self, aid: str, kind: str, at: str, tool: str, note: str, agent_id: str, *,
                        subject: str | None = None, scenario: str | None = None) -> None:
        held = {k: v for k, v in (("subject", subject), ("scenario", scenario)) if v is not None}   # task-0195
        _refuse_taken(self, "Activity", aid)
        self.run("""
            MATCH (ag:Agent {id:$agent})
            CREATE (act:Activity {id:$aid, kind:$kind, at:$ts, tool:$tool, note:$note})
            SET act += $held
            MERGE (act)-[:ASSOCIATED_WITH]->(ag)""", aid=aid, kind=kind, ts=at, tool=tool, note=note, agent=agent_id, held=held).consume()

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

    def record_part_digests(self, vid, parts) -> None:
        self.run("MATCH (v:Version {id:$vid}) SET v.part_sha256 = $parts", vid=vid, parts=part_list(parts)).consume()

    def part_digests(self) -> list[dict]:
        rows = self.run("MATCH (a:Artefact)-[:HAS_VERSION]->(v:Version) WHERE v.part_sha256 IS NOT NULL "
                        "RETURN a.id AS artefact, v.tag AS version, v.part_sha256 AS parts")
        return sorted((p for r in rows for p in part_rows(r["artefact"], r["version"], r["parts"])),
                      key=lambda p: (p["artefact"], p["version"], p["part"]))

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
        _refuse_taken(self, "Activity", activity["id"])
        self.run("""
            MATCH (llm:Agent {id:$lid}), (e:Entity {id:$eid})
            CREATE (act:Activity {id:$aid, kind:'inference', at:$at, tool:$itool, note:$note})
            MERGE (act)-[:ASSOCIATED_WITH]->(llm)
            CREATE (x:Assertion {id:$id, predicate:$pred, value:$value, text:$text, basis:'inferred',
                                 status:'proposed', artefact:$art, key:$key, version:$vtag})
            MERGE (x)-[:ABOUT]->(e)
            MERGE (x)-[:DERIVED_BY]->(act)
            MERGE (x)-[:ATTRIBUTED_TO]->(llm)
            WITH x WHERE $gid IS NOT NULL
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

    def verify_authored(self, at, scope, agent_id, artefacts=None) -> int:   # artefacts: decision-0019's attested Versions
        return self.run("""
            MATCH (x:Assertion) WHERE x.basis='authored' AND x.status='proposed' AND x.value <> 'NONE'
              AND ($arts IS NULL OR x.artefact IN $arts)
            MATCH (h:Agent {id:$hid})
            MERGE (v:Verification {id:'ver:review:' + x.id})
              SET v.method='review', v.outcome='pass', v.at=$at, v.valid_until=null, v.scope=$scope
            MERGE (v)-[:VERIFIES]->(x) MERGE (v)-[:PERFORMED_BY]->(h)
            SET x.status='verified' RETURN count(x) AS n""", at=at, scope=scope, hid=agent_id, arts=artefacts).single()["n"]

    def approve_verified(self, at, record, agent_id, artefacts=None) -> int:
        return self.run("""
            MATCH (x:Assertion {status:'verified'}), (h:Agent {id:$hid}) WHERE $arts IS NULL OR x.artefact IN $arts
            MERGE (ap:Approval {id:'appr:' + x.id}) SET ap.at=$at, ap.record=$record
            MERGE (ap)-[:APPROVES]->(x) MERGE (ap)-[:BY]->(h)
            SET x.status='approved' RETURN count(x) AS n""", at=at, record=record, hid=agent_id, arts=artefacts).single()["n"]

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

    def review_verifications(self) -> list[dict]:
        return _rows(self.run("""
            MATCH (v:Verification {method:'review'})-[:VERIFIES]->(x:Assertion) WHERE v.valid_until IS NULL
            RETURN v.id AS id, x.key AS key, v.at AS at ORDER BY id"""))

    def set_valid_until(self, dates) -> None:
        self.run("""
            UNWIND $rows AS r MATCH (v:Verification {id:r.id}) SET v.valid_until = r.until""",
                 rows=[{"id": k, "until": d} for k, d in sorted(dates.items())]).consume()

    def register_derived(self, did, kind, sha, assertion_ids, recorded=None) -> None:
        _refuse_taken(self, "Derived", did)
        self.run("""CREATE (dv:Derived {id:$did, kind:$dkind, sha256:$sha, suspect:false})
                    FOREACH (r IN CASE WHEN $rec IS NULL THEN [] ELSE [$rec] END | SET dv.recorded = r)
                    WITH dv UNWIND $ids AS aid MATCH (x:Assertion {id:aid}) MERGE (dv)-[:USED_ASSERTION]->(x)""",
                 did=did, dkind=kind, sha=sha, ids=assertion_ids,
                 rec=None if recorded is None else json.dumps(recorded, ensure_ascii=False, sort_keys=True)).consume()

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
              AND (a.version = b.version OR (a.basis IN $docs AND b.basis IN $docs)
                   OR ($across IS NOT NULL AND (a.basis = $across) <> (b.basis = $across)))
            RETURN a.id AS a, a.value AS va, a.basis AS ba, a.artefact AS aa, b.id AS b, b.value AS vb, b.basis AS bb,
                   b.artefact AS ab, a.key AS key, a.predicate AS pred""", across=across, docs=list(DOCUMENT_BASES)))

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
        return _rows(self.run("""MATCH (x:Assertion {predicate:$pred, value:'NONE'})-[:ABOUT]->(e:Entity) WHERE NOT x.status IN $dead
                                 RETURN e.id AS entity, x.id AS id""", pred=predicate, dead=list(DEAD)))

    def add_declared_gap(self, gid, text, entity, assertion_id, scenario, key_entity, key) -> None:
        self.run("""MATCH (e:Entity {id:$req}), (x:Assertion {id:$id})
                    MERGE (g:Gap {id:$gid})
                    SET g.declared = CASE WHEN g.kind = 'closed' THEN g.declared ELSE true END,
                        g.text = CASE WHEN g.kind = 'closed' THEN g.text ELSE $gtext END,
                        g.kind = CASE WHEN g.kind = 'closed' THEN g.kind ELSE 'missing' END
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
        # task-0197 (I5, I6): an older statement with a live successor of the same id stem in the new version
        succ = {stem(r["id"]) for r in self.run("MATCH (y:Assertion {version:$tag}) WHERE NOT y.status IN $dead RETURN y.id AS id",
                                                 tag=new_tag, dead=list(DEAD))}
        older = [r["id"] for r in self.run("MATCH (x:Assertion) WHERE x.version <> $tag AND NOT x.status IN $dead RETURN x.id AS id ORDER BY x.id",
                                           tag=new_tag, dead=list(DEAD)) if stem(r["id"]) in succ]
        if older:
            inv += _rows(self.run("""
                UNWIND $ids AS xid MATCH (x:Assertion {id:xid})
                SET x.status='invalidated', x.invalidated_at=datetime().epochSeconds, x.invalidated_by=$tag
                WITH DISTINCT x
                OPTIONAL MATCH (v:Verification)-[:VERIFIES]->(x) SET v.valid_until=$tag
                WITH DISTINCT x
                OPTIONAL MATCH (d:Derived)-[:USED_ASSERTION]->(x) SET d.suspect=true
                RETURN x.id AS id, x.key AS key, collect(DISTINCT d.id) AS derived""", ids=older, tag=new_tag))
        kept = _rows(self.run("""
            MATCH (x:Assertion)-[:SUPPORTED_BY]->(f:Fragment)<-[:HAS_FRAGMENT]-(old:Version)<-[:HAS_VERSION]-(a:Artefact)-[:CURRENT]->(cur:Version)
            WHERE old <> cur AND x.version <> $tag AND x.status <> 'invalidated'
            RETURN DISTINCT x.id AS id, x.key AS key, x.status AS status""", tag=new_tag))
        # task-0197 (G5): a declared gap whose declaring statements this re-ingestion invalidated, all of them, is withdrawn
        withdrawn = [r["id"] for r in self.run("""
            MATCH (g:Gap {kind:'missing', declared:true})-[:CONCERNS]->(x:Assertion) WHERE x.id IN $inv
            WITH DISTINCT g
            WHERE all(y IN [(g)-[:CONCERNS]->(z:Assertion) | z] WHERE y.status IN $dead)
            SET g.kind='withdrawn', g.declared=false, g.withdrawn_by=$tag
            RETURN g.id AS id ORDER BY g.id""", inv=[r["id"] for r in inv], dead=list(DEAD), tag=new_tag)]
        return {"invalidated": inv, "kept": kept, **({"withdrawn": withdrawn} if withdrawn else {})}

    def invalidate_keys(self, reasons) -> dict:
        inv = _rows(self.run("""
            UNWIND $pairs AS p
            MATCH (x:Assertion {key:p.key}) WHERE x.status IN ['proposed','validated','verified','approved','disputed']
            SET x.status='invalidated', x.invalidated_at=datetime().epochSeconds, x.invalidated_by=p.reason
            WITH x, p
            OPTIONAL MATCH (v:Verification)-[:VERIFIES]->(x) SET v.valid_until=p.reason
            WITH DISTINCT x
            OPTIONAL MATCH (d:Derived)-[:USED_ASSERTION]->(x) SET d.suspect=true
            RETURN x.id AS id, x.key AS key, collect(DISTINCT d.id) AS derived""",
            pairs=[{"key": k, "reason": r} for k, r in sorted(reasons.items())]))
        return {"invalidated": sorted(({**r, "derived": sorted(d for d in r["derived"] if d)} for r in inv), key=lambda r: r["id"])}

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
                   collect(DISTINCT {id:ap.id, at:ap.at, record:ap.record, until:ap.until}) AS approvals,
                   collect(DISTINCT {id:g.id, kind:g.kind, declared:g.declared, text:g.text}) AS gaps
            ORDER BY x.id""", key=key, live=live))
        for r in rows:   # each collect in one order, as the rdflib adapter gives it: collect() is store order
            r["fragments"] = by_content([f for f in r["fragments"] if f["locator"]])
            r["verifications"] = by_id([v for v in r["verifications"] if v["id"]])
            r["approvals"] = by_id([{**a, "until": a.get("until") or None} for a in r["approvals"] if a["id"]])   # task-0198
            r["gaps"] = by_id([g for g in r["gaps"] if g["id"]])
        return by_id(rows)

    def declared_gaps_for_key(self, key) -> list[dict]:   # by id (task-0201, doc-0030 S2): the driver's order is not one
        return by_id(_rows(self.run("""
            MATCH (g:Gap {kind:'missing', declared:true})-[c:CONCERNS_KEY {key:$key}]->()
            RETURN g.id AS id, g.text AS text""", key=key)))

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

    def stale_on_keys(self, keys) -> list[dict]:   # rows, verifications and successors by id
        rows = _rows(self.run("""
            MATCH (x:Assertion {status:'invalidated'}) WHERE x.key IN $keys
            OPTIONAL MATCH (v:Verification)-[:VERIFIES]->(x)
            OPTIONAL MATCH (succ:Assertion {key:x.key, artefact:x.artefact}) WHERE succ.status IN ['proposed','validated','verified','approved']
            RETURN x.id AS id, x.key AS key, x.value AS value, x.invalidated_by AS invalidated_by,
                   collect(DISTINCT {id:v.id, valid_until:v.valid_until}) AS verifications,
                   collect(DISTINCT {id:succ.id, value:succ.value, status:succ.status}) AS successors""", keys=keys))
        return by_id([{**r, "verifications": by_id(r["verifications"]), "successors": by_id(r["successors"])} for r in rows])

    def derived_rows(self) -> list[dict]:
        rows = _rows(self.run("""
            MATCH (d:Derived) OPTIONAL MATCH (d)-[:USED_ASSERTION]->(x:Assertion)
            RETURN d.id AS id, d.kind AS kind, d.sha256 AS sha256, d.recorded AS recorded,
                   collect({id:x.id, status:x.status}) AS used"""))
        return [{**r, "used": [u for u in r["used"] if u["id"]]} for r in rows]

    def suspect_derived(self) -> list[dict]:   # task-0199: by suspicion, the one rule, never the stored flag
        return suspect_rows(suspicion(self, self.derived_rows()))

    def all_derived(self) -> list[dict]:
        return [{"id": r["id"], "suspect": r["suspect"]} for r in suspicion(self, self.derived_rows())]

    def held_keys(self) -> list[dict]:
        out: dict[str, dict] = {}
        for r in _rows(self.run("MATCH (x:Assertion) WHERE x.key IS NOT NULL RETURN x.key AS key, x.status AS status, count(*) AS n")):
            k = out.setdefault(r["key"], {"key": r["key"], "n": 0, "statuses": {}})
            k["n"] += r["n"]
            k["statuses"][r["status"]] = k["statuses"].get(r["status"], 0) + r["n"]
        return [out[k] for k in sorted(out)]

    def derived_outputs(self) -> list[dict]:
        sus = {r["id"]: r for r in suspicion(self, self.derived_rows())}
        rows = _rows(self.run("""
            MATCH (d:Derived) OPTIONAL MATCH (d)-[:USED_ASSERTION]->(x:Assertion)
            RETURN d.id AS id, d.kind AS kind, d.sha256 AS sha256,
                   collect({id:x.id, key:x.key, status:x.status, artefact:x.artefact, version:x.version}) AS used"""))
        return by_id([{"id": r["id"], "kind": r["kind"], "sha256": r["sha256"], "suspect": sus[r["id"]]["suspect"],
                       **changed_of(sus[r["id"]]), "used": by_id([u for u in r["used"] if u["id"]])} for r in rows])

    def artefact_assertions(self, artefact) -> list[dict]:
        rows = _rows(self.run("""
            MATCH (x:Assertion) OPTIONAL MATCH (x)-[:SUPPORTED_BY]->(f:Fragment)
            WITH x, [f IN collect(f) WHERE f.artefact = $a OR (right($a, 1) = '/' AND f.artefact STARTS WITH $a)] AS fs
            WHERE x.artefact = $a OR (right($a, 1) = '/' AND x.artefact STARTS WITH $a) OR size(fs) > 0
            RETURN x.id AS id, x.key AS key, x.value AS value, x.status AS status, x.basis AS basis,
                   x.artefact AS artefact, x.version AS version,
                   [f IN fs | {locator:f.locator, artefact:f.artefact}] AS fragments""", a=artefact))
        return by_id([{**r, "fragments": by_content(_distinct_rows(r["fragments"]))} for r in rows])

    def record_preload(self, vid, verdict) -> None:
        props = {f"preload_{k}": verdict.get(k) for k in PRELOAD_FIELDS}
        self.run("MATCH (v:Version {id:$vid}) SET v += $props", vid=vid, props=props).consume()

    def record_act_finding(self, row) -> None:
        self.run("MERGE (a:ActFinding {id:$id}) SET a += $props", id=row["id"], props={k: row[k] for k in self.ACT_FIELDS}).consume()

    def record_attestation(self, row) -> None:   # on the attester's Agent node, never a node of its own (store.py)
        self.run("MATCH (a:Agent {id:$aid}) SET a += $props", aid=row["attester"],
                 props={f"attestation_{row['declaration']}": json.dumps({k: row[k] for k in ("id", *self.ATTESTATION_FIELDS)}, sort_keys=True)}).consume()

    def attestations(self) -> list[dict]:
        rows = _rows(self.run("MATCH (a:Agent) WHERE a.attestation_approval IS NOT NULL OR a.attestation_authored IS NOT NULL "
                              "RETURN a.attestation_approval AS approval, a.attestation_authored AS authored"))
        return by_id([json.loads(r[d]) for r in rows for d in ("approval", "authored") if r[d]])

    def clear_act_findings(self) -> None:
        self.run("MATCH (a:ActFinding) DETACH DELETE a").consume()

    def gap_brief(self, gid) -> dict | None:
        rows = _rows(self.run("""
            MATCH (g:Gap {id:$gid}) OPTIONAL MATCH (g)-[c:CONCERNS_KEY]->()
            RETURN g.id AS id, g.kind AS kind, g.declared AS declared, g.text AS text,
                   [k IN collect(c.key) WHERE k IS NOT NULL] AS keys""", gid=gid))
        return {**rows[0], "keys": sorted(rows[0]["keys"])} if rows else None

    def act_findings(self) -> list[dict]:
        cols = ", ".join(f"a.{k} AS {k}" for k in self.ACT_FIELDS)
        return by_id(_rows(self.run(f"MATCH (a:ActFinding) RETURN a.id AS id, {cols}")))

    def preload_verdicts(self) -> list[dict]:
        return _rows(self.run("""
            MATCH (a:Artefact)-[:HAS_VERSION]->(v:Version) WHERE v.preload_state IS NOT NULL
            RETURN a.id AS artefact, v.tag AS version, v.preload_state AS state, v.preload_tool AS tool,
                   v.preload_tool_version AS tool_version, v.preload_digest AS digest, v.preload_report AS report,
                   v.preload_why AS why
            ORDER BY artefact, version"""))

    def register_node_statements(self, start: str) -> list[dict]:
        rows = _rows(self.run(_NODE_STATEMENTS, start=start))
        return [{**r, **{k: sorted(r[k]) for k in ("anchors", "links", "versions", "fragments", "derived")}} for r in rows]

    # ---- the census and the page
    def census(self) -> dict:
        st = {r["status"]: r["n"] for r in self.run("MATCH (x:Assertion) RETURN x.status AS status, count(*) AS n")}
        gaps = {r["kind"]: r["n"] for r in self.run("MATCH (g:Gap) RETURN g.kind AS kind, count(*) AS n")}
        contradicts = self.run("MATCH ()-[r:CONTRADICTS]->() RETURN count(r)/2 AS n").single()["n"]
        nodes = self.run(f"MATCH (n) WHERE NOT n:{PUB} RETURN count(n) AS n").single()["n"]
        rels = self.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
        return {"assertions_by_status": st, "gaps_by_kind": gaps, "contradicts": contradicts, "nodes": nodes, "relationships": rels}

    def extraction_activities(self) -> list[str]:
        return [r["id"] for r in self.run("MATCH (a:Activity) WHERE a.id STARTS WITH 'act:extract:' RETURN a.id AS id ORDER BY a.at, a.id")]   # two versions extracted in one second: the id decides, not store order (task-0070)

    def held(self) -> dict | None:
        acts = [dict(r) for r in self.run("MATCH (a:Activity) WHERE a.id STARTS WITH 'act:extract:' "
                                          "RETURN a.id AS id, a.at AS at, a.subject AS subject, a.scenario AS scenario")]
        current = [dict(r) for r in self.run("MATCH (a:Artefact)-[:CURRENT]->(v:Version) "
                                             "RETURN a.id AS artefact, v.tag AS tag, COUNT { (a)-[:HAS_VERSION]->() } AS versions")]
        return held_from(acts, current)

    def extraction_times(self) -> list[dict]:
        return [{"id": r["id"], "at": r["at"]} for r in self.run(
            "MATCH (a:Activity) WHERE a.id STARTS WITH 'act:extract:' RETURN a.id AS id, a.at AS at ORDER BY a.at, a.id")]

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


def publication(uri: str = URI, auth: tuple[str, str] = AUTH) -> dict:
    """The publication node's properties as they stand, read with the driver alone and no pin: the
    counter, the lease and, after a reader cleared an abandoned publication, the abandoning writer
    (task-0175). For diagnostics and tools/check_snapshots.py; a read handle never needs it."""
    from neo4j import GraphDatabase
    with GraphDatabase.driver(uri, auth=auth) as drv, drv.session() as sess:
        r = sess.run(f"{PUB_MATCH} RETURN p {{.*}} AS p").single()
    return dict(r["p"]) if r else {}
