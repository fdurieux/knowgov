"""The in-memory adapter of the store port: an rdflib Graph as the storage, with a small
property-graph layer on top (nodes with labels and properties; edges as reified nodes so edge
properties fit), and every port operation implemented in Python over it.

It exists to prove the port with a second implementation and to let the deterministic half
and the tests run without a database container. The deterministic comparator must find the
same answers as the Neo4j adapter on the CargoQuote record, D1 aside: D1 measures which
constraint families a Neo4j edition refuses, which has no meaning here (every constraint is
an application check), so the comparator skips D1 when the run's store differs from the
record's.

Where Cypher has no ORDER BY, Neo4j answers in store order; here that is insertion order,
kept as a sequence number on every node and edge. The comparator treats lists of scalars
as unordered, so collect() order never decides a verdict.

``KG_RDFLIB_FILE`` names a Turtle file the graph is read from when the store opens and
written to when it closes, so the page can read what a run left; unset, the graph lives in
the process only.
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote, unquote

from rdflib import Graph, Literal, Namespace, RDF, URIRef

from store import Store

N = Namespace("urn:kg:n:")        # nodes
L = Namespace("urn:kg:label:")    # labels
P = Namespace("urn:kg:p:")        # properties
E = Namespace("urn:kg:e:")        # edges (reified)
EDGE = L["_Edge"]
JSON_DT = URIRef("urn:kg:json")   # list-valued properties

CONSTRAINTS = [
    ("uniqueness", "Assertion.id unique", True, "enforced by the adapter: a second node with the same id is refused"),
    ("uniqueness", "Fragment.id unique", True, "enforced by the adapter"),
    ("uniqueness", "Entity.id unique", True, "enforced by the adapter"),
    ("uniqueness", "Version.id unique", True, "enforced by the adapter"),
    ("uniqueness", "Artefact.id unique", True, "enforced by the adapter"),
    ("uniqueness", "Gap.id unique", True, "enforced by the adapter"),
    ("existence", "Assertion.status not null", False, "not a store constraint here: the loader always sets status; an application check"),
    ("node key", "Fragment (locator, sha256) node key", False, "not a store constraint here; an application check"),
    ("property type", "Version.sha256 is a string", False, "not a store constraint here; an application check"),
]


def _lit(v):
    if isinstance(v, (list, tuple)):
        return Literal(json.dumps(list(v)), datatype=JSON_DT)
    return Literal(v)


def _py(lit):
    if lit is None:
        return None
    if getattr(lit, "datatype", None) == JSON_DT:
        return json.loads(str(lit))
    return lit.toPython()


class RdflibStore(Store):
    name = "rdflib"

    def __init__(self, path: str | None = None, instance: str = "", **_ignored):
        self.instance = instance
        self.path = path if path is not None else os.environ.get("KG_RDFLIB_FILE")
        self.g = Graph()
        self._seq = 0
        self._nodes: dict[str, URIRef] = {}        # id -> node, insertion order
        self._out: dict[URIRef, list[URIRef]] = {}  # node -> its outgoing edge nodes
        self._in: dict[URIRef, list[URIRef]] = {}
        if self.path and os.path.exists(self.path):
            self.g.parse(self.path, format="turtle")
            self._reindex()

    # ---- the property-graph layer --------------------------------------------------------
    def _reindex(self) -> None:
        self._nodes, self._out, self._in = {}, {}, {}
        rows = []
        for s, _, seq in self.g.triples((None, P["_seq"], None)):
            rows.append((int(seq), s))
        for _, s in sorted(rows):
            if (s, RDF.type, EDGE) in self.g:
                src, dst = self.g.value(s, P["_from"]), self.g.value(s, P["_to"])
                self._out.setdefault(src, []).append(s)
                self._in.setdefault(dst, []).append(s)
            else:
                self._nodes[unquote(str(s)[len(N):])] = s
        self._seq = max((int(x) for x, _ in rows), default=0)

    def _next(self) -> int:
        self._seq += 1
        return self._seq

    def _n(self, nid: str) -> URIRef:
        return N[quote(nid, safe="")]

    def exists(self, nid: str) -> bool:
        return nid in self._nodes

    def create_node(self, nid: str, labels, props: dict) -> URIRef:
        if nid in self._nodes:
            raise ValueError(f"a node with id {nid!r} exists: the uniqueness constraint refuses it")
        n = self._n(nid)
        self._nodes[nid] = n
        for lbl in ([labels] if isinstance(labels, str) else labels):
            self.g.add((n, RDF.type, L[lbl]))
        self.g.add((n, P["_seq"], Literal(self._next())))
        self.set_props(n, {"id": nid, **props})
        return n

    def merge_node(self, nid: str, label: str, on_create: dict | None = None, props: dict | None = None) -> URIRef:
        if nid in self._nodes:
            n = self._nodes[nid]
        else:
            n = self.create_node(nid, label, on_create or {})
        if props:
            self.set_props(n, props)
        return n

    def set_props(self, n: URIRef, props: dict) -> None:
        for k, v in props.items():
            self.g.remove((n, P[k], None))
            if v is not None:
                self.g.add((n, P[k], _lit(v)))

    def prop(self, n: URIRef, k: str):
        return _py(self.g.value(n, P[k]))

    def props(self, n: URIRef) -> dict:
        return {str(p)[len(P):]: _py(o) for _, p, o in self.g.triples((n, None, None)) if str(p).startswith(str(P)) and not str(p)[len(P):].startswith("_")}

    def labels(self, n: URIRef) -> list[str]:
        return sorted(str(o)[len(L):] for o in self.g.objects(n, RDF.type) if str(o).startswith(str(L)) and o != EDGE)

    def has_label(self, n: URIRef, label: str) -> bool:
        return (n, RDF.type, L[label]) in self.g

    def nid(self, n: URIRef) -> str:
        return self.prop(n, "id")

    def nodes(self, label: str | None = None, **where) -> list[URIRef]:
        out = []
        for n in self._nodes.values():
            if label and not self.has_label(n, label):
                continue
            if all(self.prop(n, k) == v for k, v in where.items()):
                out.append(n)
        return out

    def node(self, nid: str, label: str | None = None) -> URIRef | None:
        n = self._nodes.get(nid)
        if n is None or (label and not self.has_label(n, label)):
            return None
        return n

    def _edge(self, e: URIRef) -> tuple[URIRef, str, URIRef]:
        return self.g.value(e, P["_from"]), str(self.g.value(e, P["_type"])), self.g.value(e, P["_to"])

    def edges_out(self, n: URIRef, *types: str) -> list[tuple[URIRef, URIRef]]:
        """(edge, target) for n's outgoing edges of the given types (any type when none)."""
        return [(e, self._edge(e)[2]) for e in self._out.get(n, []) if not types or self._edge(e)[1] in types]

    def edges_in(self, n: URIRef, *types: str) -> list[tuple[URIRef, URIRef]]:
        return [(e, self._edge(e)[0]) for e in self._in.get(n, []) if not types or self._edge(e)[1] in types]

    def out(self, n: URIRef, *types: str) -> list[URIRef]:
        return [t for _, t in self.edges_out(n, *types)]

    def inn(self, n: URIRef, *types: str) -> list[URIRef]:
        return [s for _, s in self.edges_in(n, *types)]

    def create_edge(self, src: URIRef, etype: str, dst: URIRef, props: dict | None = None) -> URIRef:
        e = E[str(self._next())]
        self.g.add((e, RDF.type, EDGE))
        self.g.add((e, P["_seq"], Literal(self._seq)))
        self.g.add((e, P["_from"], src))
        self.g.add((e, P["_to"], dst))
        self.g.add((e, P["_type"], Literal(etype)))
        if props:
            self.set_props(e, props)
        self._out.setdefault(src, []).append(e)
        self._in.setdefault(dst, []).append(e)
        return e

    def merge_edge(self, src: URIRef, etype: str, dst: URIRef, props: dict | None = None) -> URIRef:
        for e, t in self.edges_out(src, etype):
            if t == dst and all(self.prop(e, k) == v for k, v in (props or {}).items()):
                return e
        return self.create_edge(src, etype, dst, props)

    def delete_node(self, n: URIRef) -> None:
        for e in list(self._out.get(n, [])) + list(self._in.get(n, [])):
            self._delete_edge(e)
        self.g.remove((n, None, None))
        self._nodes.pop(self.nid(n) if (n, P["id"], None) in self.g else next((k for k, v in self._nodes.items() if v == n), None), None)

    def _delete_edge(self, e: URIRef) -> None:
        src, _, dst = self._edge(e)
        self._out[src] = [x for x in self._out.get(src, []) if x != e]
        self._in[dst] = [x for x in self._in.get(dst, []) if x != e]
        self.g.remove((e, None, None))

    def edge_count(self) -> int:
        return sum(len(v) for v in self._out.values())

    # ---- lifecycle ---------------------------------------------------------------------------
    def close(self) -> None:
        if self.path:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            self.g.serialize(destination=self.path, format="turtle")

    def wipe(self) -> None:
        self.g = Graph()
        self._nodes, self._out, self._in, self._seq = {}, {}, {}, 0

    def export_turtle(self) -> str:
        return self.g.serialize(format="turtle")

    def import_turtle(self, text: str) -> None:
        self.wipe()
        self.g.parse(data=text, format="turtle")
        self._reindex()

    def apply_constraints(self) -> list[dict]:
        return [{"type": kind, "cypher": name, "accepted": ok, "message": msg} for kind, name, ok, msg in CONSTRAINTS]

    # ---- loading -----------------------------------------------------------------------------
    def ensure_agents(self, tool_name, version, human, llm) -> None:
        self.merge_node("agent:harness", "Agent", props={"kind": "tool", "name": tool_name, "version": version})
        self.merge_node(human["id"], "Agent", props={"kind": "human", "name": human["name"]})
        self.merge_node(llm["id"], "Agent", props={"kind": "llm", "name": llm["name"]})

    def ensure_person(self, aid, handle) -> None:
        self.merge_node(aid, "Agent", props={"kind": "human", "name": handle})

    def create_activity(self, aid, kind, at, tool, note, agent_id) -> None:
        ag = self.node(agent_id, "Agent")
        if ag is None:
            return
        act = self.create_node(aid, "Activity", {"kind": kind, "at": at, "tool": tool, "note": note})
        self.merge_edge(act, "ASSOCIATED_WITH", ag)

    def upsert_artefact_version(self, path, family, fmt, vid, sha, nbytes, ts, tag, aid) -> None:
        a = self.merge_node(path, "Artefact", props={"path": path, "family": family, "format": fmt})
        v = self.create_node(vid, "Version", {"sha256": sha, "bytes": nbytes, "ingested_at": ts, "tag": tag})
        self.merge_edge(a, "HAS_VERSION", v)
        for e, _ in self.edges_out(a, "CURRENT"):
            self._delete_edge(e)
        self.merge_edge(a, "CURRENT", v)
        act = self.node(aid, "Activity")
        if act is not None:
            self.merge_edge(act, "USED", v)

    def find_fragment(self, artefact, locator, sha) -> str | None:
        for f in self.nodes("Fragment", artefact=artefact, locator=locator, sha256=sha):
            return self.nid(f)
        return None

    def link_fragment(self, vid, fid) -> None:
        v, f = self.node(vid, "Version"), self.node(fid, "Fragment")
        if v is not None and f is not None:
            self.merge_edge(v, "HAS_FRAGMENT", f)

    def create_fragment(self, vid, fid, locator, sha, text, artefact) -> None:
        v = self.node(vid, "Version")
        if v is None:
            return
        f = self.create_node(fid, "Fragment", {"locator": locator, "sha256": sha, "text": text, "artefact": artefact})
        self.merge_edge(v, "HAS_FRAGMENT", f)

    def ensure_entity(self, eid, kind, name) -> None:
        self.merge_node(eid, "Entity", on_create={"kind": kind, "name": name})

    def create_assertion(self, props, entity, activity, agent, fragment_ids) -> None:
        act, e, ag = self.node(activity, "Activity"), self.node(entity, "Entity"), self.node(agent, "Agent")
        if act is None or e is None or ag is None:
            return
        x = self.create_node(props["id"], "Assertion", {"predicate": props["predicate"], "value": props["value"], "raw_value": props.get("raw_value"),
                                                       "text": props["text"], "basis": props["basis"], "status": props.get("status", "proposed"),
                                                       "artefact": props["artefact"], "key": props["key"], "unresolved": props.get("unresolved", False),
                                                       "version": props["version"]})
        self.merge_edge(x, "ABOUT", e)
        self.merge_edge(x, "DERIVED_BY", act)
        self.merge_edge(x, "ATTRIBUTED_TO", ag)
        for fid in fragment_ids:
            f = self.node(fid, "Fragment")
            if f is not None:
                self.merge_edge(x, "SUPPORTED_BY", f)

    def link_mentions(self) -> None:
        for x in self.nodes("Assertion"):
            ents = self.out(x, "ABOUT")
            frags = self.out(x, "SUPPORTED_BY")
            for e in ents:
                for f in frags:
                    self.merge_edge(f, "MENTIONS", e)

    def create_inferred(self, props, entity, activity, agent_id, candidate_for) -> None:
        llm, e = self.node(agent_id, "Agent"), self.node(entity, "Entity")
        if llm is None or e is None:
            return
        act = self.create_node(activity["id"], "Activity", {"kind": "inference", "at": activity["at"], "tool": activity["tool"], "note": activity["note"]})
        self.merge_edge(act, "ASSOCIATED_WITH", llm)
        x = self.create_node(props["id"], "Assertion", {"predicate": props["predicate"], "value": props["value"], "text": props["text"], "basis": "inferred",
                                                       "status": "proposed", "artefact": props.get("artefact", "llm"), "key": props["key"],
                                                       "version": props.get("version", "v1")})
        self.merge_edge(x, "ABOUT", e)
        self.merge_edge(x, "DERIVED_BY", act)
        self.merge_edge(x, "ATTRIBUTED_TO", llm)
        g = self.merge_node(candidate_for, "Gap")
        self.merge_edge(x, "CANDIDATE_FOR", g)

    # ---- verifications and approvals ---------------------------------------------------------
    def _live_on_key(self, key, values):
        return [x for x in self.nodes("Assertion", key=key)
                if self.prop(x, "value") in values and self.prop(x, "basis") in ("extracted", "authored")
                and self.prop(x, "status") not in ("invalidated", "rejected", "deprecated")]

    def _verify(self, x, vid, agent, props) -> None:
        v = self.merge_node(vid, "Verification", props=props)
        self.merge_edge(v, "VERIFIES", x)
        self.merge_edge(v, "PERFORMED_BY", agent)
        if self.prop(x, "status") in ("proposed", "validated"):
            self.set_props(x, {"status": "verified"})

    def verify_by_execution(self, key, values, suite_scenario, scope, ts, digest) -> int:
        h = self.node("agent:harness", "Agent")
        xs = self._live_on_key(key, values)
        if h is None:
            return 0
        for x in xs:
            self._verify(x, f"ver:exec:{suite_scenario}:{self.nid(x)}", h,
                         {"method": "execution", "outcome": "pass", "scope": scope, "at": ts, "evidence_sha256": digest, "valid_until": None})
        return len(xs)

    def verify_by_review(self, key, values, at, scope, agent_id) -> int:
        h = self.node(agent_id, "Agent")
        xs = self._live_on_key(key, values)
        if h is None:
            return 0
        for x in xs:
            self._verify(x, f"ver:review:{self.nid(x)}", h, {"method": "review", "outcome": "pass", "at": at, "valid_until": None, "scope": scope})
        return len(xs)

    def verify_authored(self, at, scope, agent_id) -> int:
        h = self.node(agent_id, "Agent")
        xs = [x for x in self.nodes("Assertion", basis="authored", status="proposed") if self.prop(x, "value") != "NONE"]
        if h is None:
            return 0
        for x in xs:
            v = self.merge_node(f"ver:review:{self.nid(x)}", "Verification", props={"method": "review", "outcome": "pass", "at": at, "valid_until": None, "scope": scope})
            self.merge_edge(v, "VERIFIES", x)
            self.merge_edge(v, "PERFORMED_BY", h)
            self.set_props(x, {"status": "verified"})
        return len(xs)

    def approve_verified(self, at, record, agent_id) -> int:
        h = self.node(agent_id, "Agent")
        xs = self.nodes("Assertion", status="verified")
        if h is None:
            return 0
        for x in xs:
            ap = self.merge_node(f"appr:{self.nid(x)}", "Approval", props={"at": at, "record": record})
            self.merge_edge(ap, "APPROVES", x)
            self.merge_edge(ap, "BY", h)
            self.set_props(x, {"status": "approved"})
        return len(xs)

    def reverify(self, version, keys, agent_id, ts, scope, record) -> list[str]:
        h = self.node(agent_id, "Agent")
        xs = [x for x in self.nodes("Assertion", version=version) if self.prop(x, "key") in keys and self.prop(x, "status") in ("proposed", "validated")]
        if h is None:
            return []
        ids = []
        for x in xs:
            v = self.merge_node(f"ver:review:{version}:{self.nid(x)}", "Verification",
                                props={"method": "review", "outcome": "pass", "at": ts, "scope": scope, "valid_until": None})
            self.merge_edge(v, "VERIFIES", x)
            self.merge_edge(v, "PERFORMED_BY", h)
            self.set_props(x, {"status": "verified"})
            ap = self.merge_node(f"appr:{version}:{self.nid(x)}", "Approval", props={"at": ts, "record": record})
            self.merge_edge(ap, "APPROVES", x)
            self.merge_edge(ap, "BY", h)
            self.set_props(x, {"status": "approved"})
            ids.append(self.nid(x))
        return ids

    def register_derived(self, did, kind, sha, assertion_ids) -> None:
        dv = self.create_node(did, "Derived", {"kind": kind, "sha256": sha, "suspect": False})
        for aid in assertion_ids:
            x = self.node(aid, "Assertion")
            if x is not None:
                self.merge_edge(dv, "USED_ASSERTION", x)

    # ---- the rules ---------------------------------------------------------------------------
    def structural_violations(self) -> list[dict]:
        v = []
        for x in self.nodes("Assertion"):
            if self.prop(x, "basis") in ("extracted", "authored") and not any(self.has_label(f, "Fragment") for f in self.out(x, "SUPPORTED_BY")):
                v.append({"id": self.nid(x), "why": "no supporting fragment"})
        for x in self.nodes("Assertion"):
            if self.prop(x, "basis") in ("inferred", "assumed", "hypothesised"):
                linked = any(self.has_label(t, "Gap") for t in self.out(x, "CANDIDATE_FOR", "CONCERNED_BY") + self.inn(x, "CANDIDATE_FOR", "CONCERNED_BY"))
                concerned = any(self.has_label(s, "Gap") for s in self.inn(x, "CONCERNS"))
                if not linked and not concerned:
                    v.append({"id": self.nid(x), "why": "inferred without a gap"})
        for f in self.nodes("Fragment"):
            if not any(self.has_label(s, "Version") for s in self.inn(f, "HAS_FRAGMENT")):
                v.append({"id": self.nid(f), "why": "orphan fragment"})
        for ver in self.nodes("Version"):
            if not any(self.has_label(s, "Artefact") for s in self.inn(ver, "HAS_VERSION")):
                v.append({"id": self.nid(ver), "why": "orphan version"})
        return v

    def candidate_pairs(self, across=None) -> list[dict]:
        dead = ("rejected", "deprecated", "invalidated")
        out = []
        for e in self.nodes("Entity"):
            xs = [x for x in self.inn(e, "ABOUT") if self.has_label(x, "Assertion")]
            for i, a in enumerate(xs):
                for b in xs:
                    if a == b:
                        continue
                    ida, idb = self.nid(a), self.nid(b)
                    if not (ida < idb):
                        continue
                    if self.prop(a, "predicate") != self.prop(b, "predicate") or self.prop(a, "artefact") == self.prop(b, "artefact"):
                        continue
                    if self.prop(a, "status") in dead or self.prop(b, "status") in dead:
                        continue
                    if self.prop(a, "version") != self.prop(b, "version") and (
                            across is None or (self.prop(a, "basis") == across) == (self.prop(b, "basis") == across)):
                        continue
                    out.append({"a": ida, "va": self.prop(a, "value"), "ba": self.prop(a, "basis"), "aa": self.prop(a, "artefact"),
                                "b": idb, "vb": self.prop(b, "value"), "bb": self.prop(b, "basis"), "ab": self.prop(b, "artefact"),
                                "key": self.prop(a, "key"), "pred": self.prop(a, "predicate")})
        return out

    def _bump(self, x, frm, to) -> None:
        if self.prop(x, "status") == frm:
            self.set_props(x, {"status": to})

    def corroborate(self, a, b, promote=True) -> None:
        na, nb = self.node(a, "Assertion"), self.node(b, "Assertion")
        if na is None or nb is None:
            return
        self.merge_edge(na, "CORROBORATES", nb)
        self.merge_edge(nb, "CORROBORATES", na)
        if promote:
            self._bump(na, "proposed", "validated")
            self._bump(nb, "proposed", "validated")

    def _raised_by(self, g, scenario) -> None:
        for act in self.nodes("Activity"):
            if self.nid(act).startswith("act:extract:" + scenario):
                self.merge_edge(g, "RAISED_BY", act)

    def mark_conflict(self, a, b, gid, key, scenario, text=None) -> None:
        na, nb = self.node(a, "Assertion"), self.node(b, "Assertion")
        if na is None or nb is None:
            return
        self.merge_edge(na, "CONTRADICTS", nb)
        self.merge_edge(nb, "CONTRADICTS", na)
        self.set_props(na, {"status": "disputed"})
        self.set_props(nb, {"status": "disputed"})
        text = text or f"two artefacts state different values for {key}: {self.prop(na, 'artefact')} says {self.prop(na, 'value')}; {self.prop(nb, 'artefact')} says {self.prop(nb, 'value')}"
        g = self.merge_node(gid, "Gap", props={"kind": "conflict", "declared": False, "text": text})
        self.merge_edge(g, "CONCERNS", na)
        self.merge_edge(g, "CONCERNS", nb)
        self._raised_by(g, scenario)

    def vague_fragments(self, words) -> list[dict]:
        out, seen = [], set()
        for x in self.nodes("Assertion"):
            for f in self.out(x, "SUPPORTED_BY"):
                if not self.has_label(f, "Fragment"):
                    continue
                text, loc = self.prop(f, "text") or "", self.prop(f, "locator") or ""
                if "row/" in loc and any(w in text.lower() for w in words):
                    row = (self.nid(x), self.prop(x, "key"), self.nid(f), text)
                    if row not in seen:
                        seen.add(row)
                        out.append({"id": row[0], "key": row[1], "fid": row[2], "text": row[3]})
        return out

    def add_ambiguous_gap(self, assertion_id, text, scenario) -> None:
        x = self.node(assertion_id, "Assertion")
        if x is None:
            return
        g = self.merge_node("gap:ambiguous:" + assertion_id, "Gap", props={"kind": "ambiguous", "declared": False, "text": text})
        self.merge_edge(g, "CONCERNS", x)
        self._raised_by(g, scenario)

    def unresolved_assertions(self) -> list[dict]:
        return [{"id": self.nid(x), "key": self.prop(x, "key"), "sym": self.prop(x, "raw_value")} for x in self.nodes("Assertion", unresolved=True)]

    def declared_open(self, predicate) -> list[dict]:
        out = []
        for x in self.nodes("Assertion", predicate=predicate, value="NONE"):
            for e in self.out(x, "ABOUT"):
                if self.has_label(e, "Entity"):
                    out.append({"entity": self.nid(e), "id": self.nid(x)})
        return out

    def add_declared_gap(self, gid, text, entity, assertion_id, scenario, key_entity, key) -> None:
        e, x = self.node(entity, "Entity"), self.node(assertion_id, "Assertion")
        if e is None or x is None:
            return
        g = self.merge_node(gid, "Gap", props={"kind": "missing", "declared": True, "text": text})
        self.merge_edge(g, "CONCERNS", e)
        self.merge_edge(g, "CONCERNS", x)
        acts = [a for a in self.nodes("Activity") if self.nid(a).startswith("act:extract:" + scenario)]
        if not acts:
            return   # as in the Neo4j adapter: a pattern that matches nothing ends the statement
        for act in acts:
            self.merge_edge(g, "RAISED_BY", act)
        k = self.node(key_entity, "Entity")
        if k is not None:
            self.merge_edge(g, "CONCERNS_KEY", k, {"key": key})

    def add_absent_artefact_gap(self, artefact, assertion_id) -> None:
        x = self.node(assertion_id, "Assertion")
        if x is None:
            return
        g = self.merge_node("gap:declared:" + artefact, "Gap", props={"kind": "missing", "declared": True, "text": f"{artefact} is not yet authored"})
        self.merge_edge(g, "CONCERNS", x)

    def requirements_without(self, predicate) -> list[str]:
        out = []
        for e in self.nodes("Entity", kind="requirement"):
            if not any(self.has_label(x, "Assertion") and self.prop(x, "predicate") == predicate for x in self.inn(e, "ABOUT")):
                out.append(self.nid(e))
        return out

    def add_unverified_requirement_gap(self, req) -> None:
        e = self.node(req, "Entity")
        if e is None:
            return
        g = self.merge_node("gap:unverified-req:" + req, "Gap", props={"kind": "missing", "declared": False, "text": f"{req} has no verifying scenario"})
        self.merge_edge(g, "CONCERNS", e)

    def silent_entities(self, kinds) -> list[str]:
        return [self.nid(e) for e in self.nodes("Entity") if self.prop(e, "kind") in kinds
                and not any(self.has_label(x, "Assertion") for x in self.inn(e, "ABOUT"))]

    def mark_unverified(self) -> int:
        n = 0
        for x in self.nodes("Assertion"):
            if self.prop(x, "status") in ("proposed", "validated") and not any(self.has_label(v, "Verification") for v in self.inn(x, "VERIFIES")):
                g = self.merge_node("gap:unverified:" + self.nid(x), "Gap", props={"kind": "unverified", "declared": False, "text": f"{self.nid(x)} has no verification record"})
                self.merge_edge(g, "CONCERNS", x)
                n += 1
        return n

    def _stale_candidates(self, new_tag):
        """(assertion, fragment, old version, current version) for assertions of an older version whose fragment sits in a non-current version."""
        for x in self.nodes("Assertion"):
            if self.prop(x, "version") == new_tag:
                continue
            for f in self.out(x, "SUPPORTED_BY"):
                if not self.has_label(f, "Fragment"):
                    continue
                for old in self.inn(f, "HAS_FRAGMENT"):
                    if not self.has_label(old, "Version"):
                        continue
                    for a in self.inn(old, "HAS_VERSION"):
                        if not self.has_label(a, "Artefact"):
                            continue
                        for cur in self.out(a, "CURRENT"):
                            if cur != old:
                                yield x, f, cur

    def invalidate_stale(self, new_tag) -> dict:
        inv_nodes, inv = [], []
        for x, f, cur in self._stale_candidates(new_tag):
            nf = next((c for c in self.out(cur, "HAS_FRAGMENT") if self.prop(c, "locator") == self.prop(f, "locator")), None)
            if nf is not None and self.prop(nf, "sha256") == self.prop(f, "sha256"):
                continue
            if x not in inv_nodes:
                inv_nodes.append(x)
            self.set_props(x, {"status": "invalidated", "invalidated_at": self._seq, "invalidated_by": new_tag})
        for x in inv_nodes:
            derived = []
            for v in self.inn(x, "VERIFIES"):
                if self.has_label(v, "Verification"):
                    self.set_props(v, {"valid_until": new_tag})
            for d in self.inn(x, "USED_ASSERTION"):
                if self.has_label(d, "Derived"):
                    self.set_props(d, {"suspect": True})
                    if self.nid(d) not in derived:
                        derived.append(self.nid(d))
            inv.append({"id": self.nid(x), "key": self.prop(x, "key"), "derived": derived})
        kept, seen = [], set()
        for x, _f, _cur in self._stale_candidates(new_tag):
            if self.prop(x, "status") != "invalidated" and x not in seen:
                seen.add(x)
                kept.append({"id": self.nid(x), "key": self.prop(x, "key"), "status": self.prop(x, "status")})
        return {"invalidated": inv, "kept": kept}

    # ---- the gate ----------------------------------------------------------------------------
    def key_evidence(self, key, live) -> list[dict]:
        rows = []
        for x in sorted(self.nodes("Assertion", key=key), key=self.nid):
            if self.prop(x, "status") not in live:
                continue
            agent = next((self.prop(a, "name") for a in self.out(x, "ATTRIBUTED_TO") if self.has_label(a, "Agent")), None)
            frags = [{"locator": self.prop(f, "locator"), "text": self.prop(f, "text"), "artefact": self.prop(f, "artefact")} for f in self.out(x, "SUPPORTED_BY") if self.has_label(f, "Fragment")]
            vers = [{"id": self.nid(v), "method": self.prop(v, "method"), "scope": self.prop(v, "scope"), "at": self.prop(v, "at"), "valid_until": self.prop(v, "valid_until")}
                    for v in self.inn(x, "VERIFIES") if self.has_label(v, "Verification")]
            aps = [{"id": self.nid(a), "at": self.prop(a, "at"), "record": self.prop(a, "record")} for a in self.inn(x, "APPROVES") if self.has_label(a, "Approval")]
            gaps = [{"id": self.nid(g), "kind": self.prop(g, "kind"), "declared": self.prop(g, "declared"), "text": self.prop(g, "text")} for g in self.inn(x, "CONCERNS") if self.has_label(g, "Gap")]
            rows.append({"id": self.nid(x), "value": self.prop(x, "value"), "text": self.prop(x, "text"), "basis": self.prop(x, "basis"), "status": self.prop(x, "status"),
                         "artefact": self.prop(x, "artefact"), "agent": agent, "fragments": _distinct(frags), "verifications": _distinct(vers),
                         "approvals": _distinct(aps), "gaps": _distinct(gaps)})
        return rows

    def declared_gaps_for_key(self, key) -> list[dict]:
        out = []
        for g in self.nodes("Gap", kind="missing", declared=True):
            for e, _t in self.edges_out(g, "CONCERNS_KEY"):
                if self.prop(e, "key") == key:
                    out.append({"id": self.nid(g), "text": self.prop(g, "text")})
        return out

    def conflict_gaps(self) -> list[dict]:
        return [{"id": self.nid(g), "text": self.prop(g, "text")} for g in self.nodes("Gap", kind="conflict")]

    def assertion_brief(self, assertion_id) -> dict | None:
        x = self.node(assertion_id, "Assertion")
        if x is None:
            return None
        agent = next((self.prop(a, "name") for a in self.out(x, "ATTRIBUTED_TO") if self.has_label(a, "Agent")), None)
        return {"id": assertion_id, "key": self.prop(x, "key"), "value": self.prop(x, "value"), "basis": self.prop(x, "basis"),
                "status": self.prop(x, "status"), "agent": agent}

    def declared_gap(self, gid) -> dict | None:
        g = self.node(gid, "Gap")
        if g is None or self.prop(g, "kind") != "missing" or self.prop(g, "declared") is not True:
            return None
        keys = [self.prop(e, "key") for e, _t in self.edges_out(g, "CONCERNS_KEY") if self.prop(e, "key") is not None]
        return {"id": gid, "text": self.prop(g, "text"), "keys": keys}

    def apply_ruling(self, assertion_id, outcome, review_id, agent_id, at, record, until) -> None:
        x, h = self.node(assertion_id, "Assertion"), self.node(agent_id, "Agent")
        if x is None:
            return
        if outcome == "approved":
            if h is None:
                return   # as in the Neo4j adapter: a pattern that matches nothing ends the statement
            ap = self.merge_node(f"appr:{review_id}:{assertion_id}", "Approval", props={"at": at, "record": record, "until": until})
            self.merge_edge(ap, "APPROVES", x)
            self.merge_edge(ap, "BY", h)
            self.set_props(x, {"status": "approved", "ruled_in": review_id})
        elif outcome == "rejected":
            self.set_props(x, {"status": "rejected", "ruled_in": review_id})
        elif outcome == "lapsed":
            self.set_props(x, {"status": "proposed", "lapsed_in": review_id})

    def close_declared_gap(self, gid, review_id, at, record) -> None:
        if self.declared_gap(gid) is not None:
            self.set_props(self.node(gid, "Gap"), {"kind": "closed", "declared": False, "closed_in": review_id, "closed_on": at, "closed_record": record})

    def settle_conflicts(self, key, review_id) -> int:
        n = 0
        for g in self.nodes("Gap", kind="conflict"):
            if any(self.prop(x, "key") == key for x in self.out(g, "CONCERNS") if self.has_label(x, "Assertion")):
                self.set_props(g, {"kind": "settled", "settled_in": review_id})
                n += 1
        return n

    def stale_on_keys(self, keys) -> list[dict]:
        out = []
        for x in self.nodes("Assertion", status="invalidated"):
            if self.prop(x, "key") not in keys:
                continue
            vers = [{"id": self.nid(v), "valid_until": self.prop(v, "valid_until")} for v in self.inn(x, "VERIFIES") if self.has_label(v, "Verification")]
            succ = [{"id": self.nid(s), "value": self.prop(s, "value"), "status": self.prop(s, "status")}
                    for s in self.nodes("Assertion", key=self.prop(x, "key"), artefact=self.prop(x, "artefact"))
                    if self.prop(s, "status") in ("proposed", "validated", "verified", "approved")]
            out.append({"id": self.nid(x), "key": self.prop(x, "key"), "value": self.prop(x, "value"), "invalidated_by": self.prop(x, "invalidated_by"),
                        "verifications": _distinct(vers) or [{"id": None, "valid_until": None}],
                        "successors": _distinct(succ) or [{"id": None, "value": None, "status": None}]})
        return out

    def suspect_derived(self) -> list[dict]:
        out = []
        for d in self.nodes("Derived", suspect=True):
            used = [self.nid(x) for x in self.out(d, "USED_ASSERTION") if self.has_label(x, "Assertion") and self.prop(x, "status") == "invalidated"]
            if used:
                out.append({"id": self.nid(d), "kind": self.prop(d, "kind"), "sha256": self.prop(d, "sha256"), "used_invalidated": used})
        return out

    def all_derived(self) -> list[dict]:
        return [{"id": self.nid(d), "suspect": self.prop(d, "suspect")} for d in self.nodes("Derived")]

    # ---- the census and the page -------------------------------------------------------------
    def census(self) -> dict:
        st: dict[str, int] = {}
        for x in self.nodes("Assertion"):
            st[self.prop(x, "status")] = st.get(self.prop(x, "status"), 0) + 1
        gaps: dict[str, int] = {}
        for g in self.nodes("Gap"):
            gaps[self.prop(g, "kind")] = gaps.get(self.prop(g, "kind"), 0) + 1
        contradicts = sum(len(self.edges_out(n, "CONTRADICTS")) for n in self._nodes.values()) // 2
        return {"assertions_by_status": st, "gaps_by_kind": gaps, "contradicts": contradicts,
                "nodes": len(self._nodes), "relationships": self.edge_count()}

    def extraction_activities(self) -> list[str]:
        acts = [a for a in self.nodes("Activity") if self.nid(a).startswith("act:extract:")]
        return [self.nid(a) for a in sorted(acts, key=lambda a: (self.prop(a, "at") or "", self.prop(a, "_seq") or 0))]

    def gaps_with_concerns(self) -> list[dict]:
        out = []
        for g in sorted(self.nodes("Gap"), key=lambda g: (self.prop(g, "kind") or "", self.nid(g))):
            concerns = []
            for e, t in self.edges_out(g, "CONCERNS", "CONCERNS_KEY"):
                concerns.append({"id": self.nid(t), "labels": self.labels(t), "key": self.prop(t, "key"), "value": self.prop(t, "value"),
                                 "basis": self.prop(t, "basis"), "status": self.prop(t, "status"), "rel": self._edge(e)[1], "relkey": self.prop(e, "key")})
            out.append({"id": self.nid(g), "kind": self.prop(g, "kind"), "declared": bool(self.prop(g, "declared")), "text": self.prop(g, "text"),
                        "concerns": [c for c in concerns if c["id"] or c["relkey"]]})
        return out

    def assertions_on_key(self, key, statuses) -> list[dict]:
        return [{"id": self.nid(x), "value": self.prop(x, "value"), "status": self.prop(x, "status"), "basis": self.prop(x, "basis")}
                for x in self.nodes("Assertion", key=key) if self.prop(x, "status") in statuses]

    # ---- the SHACL projection's reads --------------------------------------------------------
    def assertion_rows(self) -> list[dict]:
        return [{"id": self.nid(x), "basis": self.prop(x, "basis"), "status": self.prop(x, "status")} for x in self.nodes("Assertion")]

    def supported_by(self) -> list[dict]:
        return [{"x": self.nid(x), "f": self.nid(f)} for x in self.nodes("Assertion") for f in self.out(x, "SUPPORTED_BY") if self.has_label(f, "Fragment")]

    def candidate_for(self) -> list[dict]:
        return [{"x": self.nid(x), "g": self.nid(g)} for x in self.nodes("Assertion") for g in self.out(x, "CANDIDATE_FOR") if self.has_label(g, "Gap")]

    def fragments_with_version(self) -> list[dict]:
        out = []
        for f in self.nodes("Fragment"):
            vs = [v for v in self.inn(f, "HAS_FRAGMENT") if self.has_label(v, "Version")]
            if vs:
                out += [{"f": self.nid(f), "v": self.nid(v)} for v in vs]
            else:
                out.append({"f": self.nid(f), "v": None})
        return out

    def requirements_verified_by(self) -> list[dict]:
        return [{"e": self.nid(e), "by": [self.prop(x, "value") for x in self.inn(e, "ABOUT") if self.has_label(x, "Assertion") and self.prop(x, "predicate") == "verified_by"]}
                for e in self.nodes("Entity", kind="requirement")]

    # ---- the register projection -------------------------------------------------------------
    def project_register(self, r: dict) -> None:
        for n in [n for n in self._nodes.values() if self.has_label(n, "Register")]:
            self.delete_node(n)
        reg: dict[str, URIRef] = {}
        for label, key in (("RegNode", "nodes"), ("RegType", "types"), ("RegDocument", "documents"), ("RegExternal", "externals"),
                           ("RegLink", "links"), ("RegException", "exceptions")):
            for row in r[key]:
                n = self.create_node(f"reg:{label}:{row['reg_id']}", ["Register", label], dict(row))
                reg[(label, row["reg_id"])] = n
        rn = lambda i: reg.get(("RegNode", i))  # noqa: E731
        for row in r["parents"]:
            if rn(row["child"]) is not None and rn(row["parent"]) is not None:
                self.create_edge(rn(row["child"]), "REG_PARENT", rn(row["parent"]))
        for row in r["owners"]:
            if rn(row["owner"]) is not None and rn(row["node"]) is not None:
                self.create_edge(rn(row["owner"]), "REG_OWNS", rn(row["node"]))
        for rtype, items in sorted(r["typed"].items()):
            for row in items:
                if rn(row["source"]) is not None and rn(row["target"]) is not None:
                    self.create_edge(rn(row["source"]), rtype, rn(row["target"]), dict(row["props"]))
        for row in r["maps_to"]:
            x = reg.get(("RegExternal", row["external"]))
            if rn(row["source"]) is not None and x is not None:
                self.create_edge(rn(row["source"]), "REG_MAPS_TO", x, dict(row["props"]))
        for row in r["link_of"]:
            l = reg.get(("RegLink", row["reg_id"]))
            if l is not None and rn(row["node"]) is not None:
                self.create_edge(l, "REG_LINK_OF", rn(row["node"]), {"role": row["role"]})
        for row in r["of_type"]:
            l, t = reg.get(("RegLink", row["reg_id"])), reg.get(("RegType", row["type"]))
            if l is not None and t is not None:
                self.create_edge(l, "REG_OF_TYPE", t)
        for row in r["cites"]:
            l, d = reg.get(("RegLink", row["reg_id"])), reg.get(("RegDocument", row["path"]))
            if l is not None and d is not None:
                self.create_edge(l, "REG_CITES", d, {"anchor": row["anchor"]})
        for row in r["excepts"]:
            e = reg.get(("RegException", row["reg_id"]))
            if e is not None and rn(row["node"]) is not None:
                self.create_edge(e, "REG_EXCEPTS", rn(row["node"]), {"rule": row["rule"], "expires": row["expires"]})

    def register_census(self) -> dict | None:
        regs = [n for n in self._nodes.values() if self.has_label(n, "Register")]
        if not regs:
            return None
        by_label: dict[str, int] = {}
        for n in regs:
            for lbl in self.labels(n):
                if lbl != "Register":
                    by_label[lbl] = by_label.get(lbl, 0) + 1
        rels = sum(len(self._out.get(n, [])) for n in regs)
        first = next((n for n in regs if self.has_label(n, "RegNode")), None)
        return {"tag": self.prop(first, "tag") if first else "", "commit": self.prop(first, "commit") if first else "",
                "loaded_at": self.prop(first, "loaded_at") if first else "",
                "nodes": by_label.get("RegNode", 0), "links": by_label.get("RegLink", 0), "by_label": by_label, "relationships": rels, "total": len(regs)}

    def register_node_statements(self, start: str) -> list[dict]:
        n = self.node(f"reg:RegNode:{start}", "RegNode")
        if n is None:
            return []
        rows: dict[str, dict] = {}
        for l in self.inn(n, "REG_LINK_OF"):
            if not self.has_label(l, "RegLink") or self.prop(l, "state") != "approved":
                continue
            for e, d in self.edges_out(l, "REG_CITES"):
                cited = self.prop(e, "anchor") or ""
                anchor = cited.split("#", 1)[1] if "#" in cited else None
                path = self.prop(d, "path")
                for a in self.nodes("Artefact", id=path):
                    for v in self.out(a, "HAS_VERSION"):
                        for f in self.out(v, "HAS_FRAGMENT"):
                            loc = self.prop(f, "locator") or ""
                            if anchor is not None and anchor not in loc.split("/"):
                                continue
                            for x in self.inn(f, "SUPPORTED_BY"):
                                if not self.has_label(x, "Assertion"):
                                    continue
                                r = rows.setdefault(self.nid(x), {"statement": self.nid(x), "status": self.prop(x, "status"), "document": path,
                                                                  "anchors": set(), "links": set(), "versions": set(), "fragments": set(), "derived": set()})
                                r["anchors"].add(anchor or "(whole document)")
                                r["links"].add(self.prop(l, "reg_id"))
                                r["versions"].add(self.prop(v, "tag"))
                                r["fragments"].add(loc)
                                for dv in self.inn(x, "USED_ASSERTION"):
                                    if self.has_label(dv, "Derived"):
                                        r["derived"].add(self.nid(dv) + (" (suspect)" if self.prop(dv, "suspect") else ""))
        return [{**r, **{k: sorted(r[k]) for k in ("anchors", "links", "versions", "fragments", "derived")}}
                for r in sorted(rows.values(), key=lambda r: (r["document"], r["statement"]))]

    # ---- what the page shows -----------------------------------------------------------------
    def describe(self) -> dict:
        return {"store": self.name, "uri": self.path or "memory", "browser": None}


def _distinct(rows: list[dict]) -> list[dict]:
    out, seen = [], set()
    for r in rows:
        k = json.dumps(r, sort_keys=True, default=str)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out
