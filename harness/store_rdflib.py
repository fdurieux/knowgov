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

``KG_RDFLIB_FILE`` names a Turtle file the graph is read from when the store opens and published
to when a writer commits, so the page can read what a run left; unset, the graph lives in the
process only. The file's lifecycle (task-0141.02):

- A read handle parses the published file once into memory and keeps that snapshot; it takes no
  lock and never writes. An absent file is an empty store (nothing has been published yet); a file
  that does not parse raises StoreCorrupt and is left as it is.
- A writer first takes an exclusive lock on ``<file>.lock``, a stable file beside the store that is
  never replaced, then loads the snapshot it starts from, so a second writer waits (up to
  ``KG_RDFLIB_LOCK_TIMEOUT`` seconds, default 60, then StoreBusy) and starts from the first one's
  publication: no update is lost. It keeps the lock until it is closed.
- ``commit()`` serialises the graph to a private temporary file in the store's directory, flushes
  and fsyncs it, replaces the store with it (``os.replace``, atomic on one filesystem) and fsyncs the
  directory. A reader sees the whole old file or the whole new one. Any failure leaves the previous
  file in place, removes the temporary file and propagates; nothing reports a commit that did not
  happen. ``close()`` releases the lock and publishes nothing; a writer killed before it commits
  leaves the last publication, and its lock dies with it. A writer that changed nothing publishes
  nothing on ``commit()`` (doc-0030 S7): its readers keep the generation they hold. A publication keeps
  the store file's mode, so an operator's ``chmod 600`` stands (S3); a first publication is 0644.
- Supported: POSIX filesystems with ``fcntl.flock`` (Linux, macOS), the store and its lock on a local
  disk. On a platform without ``fcntl`` a writer on a file refuses to open rather than run unlocked.
  Crash durability: a commit that returned has its file and directory entry fsynced; a crash before
  it returns leaves the previous publication.
"""
from __future__ import annotations

import json
import os
import stat
import tempfile
import threading
import time
from urllib.parse import quote, unquote

from rdflib import Graph, Literal, Namespace, RDF, URIRef

from store import (DEAD, DOCUMENT_BASES, DUPLICATE, Store, StoreBusy, StoreCorrupt, StoreFenced, StoreReadOnly, by_content, by_id, held_from,
                   changed_of, part_list, part_rows, stem, suspect_rows, suspicion)

try:
    import fcntl
except ImportError:   # not POSIX: a writer on a file refuses to open (task-0141.02)
    fcntl = None

LOCK_TIMEOUT = 60.0     # seconds a writer waits for another to finish, unless KG_RDFLIB_LOCK_TIMEOUT says
TMP_PREFIX = ".kg-publish-"   # the temporary files a commit writes beside the store

# The publication's steps, module attributes so a test can make each one fail (ST-06) or pause (ST-05)
_fsync = os.fsync
_replace = os.replace
_on_lock_wait = None    # called once when a writer finds the lock held, before it waits (ST-04)

# task-0097: a read handle's parsed snapshot, kept per process and keyed by the identity of the published
# file it was read from (device, inode, size, mtime and ctime), so the next read handle on an unchanged publication reuses the parse instead of
# parsing the file again (about 4 s a J-F call). A publication is an atomic replace (a new inode), so the
# key changes with every generation and a reader never answers from a retired one. The latest only: one
# parsed graph per process. Read handles never mutate the graph or its indexes (their methods are the
# port's READS), so they share it; a writer never uses the cache. The lock makes the fill single-flight
# under the HTTP transport's concurrent calls.
_snapshot_lock = threading.Lock()
_snapshot: tuple | None = None   # (identity, graph, nodes, out, in, seq)
_parses = 0                      # how many times a read handle parsed the file (a test reads it)


def _identity(path: str, st) -> tuple:
    return (os.path.abspath(path), st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def drop_snapshot() -> None:
    """Forget the cached snapshot (a test, or a process that wants its memory back)."""
    global _snapshot
    with _snapshot_lock:
        _snapshot = None

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

    def __init__(self, path: str | None = None, instance: str = "", access: str = "write",
                 lock_timeout: float | None = None, connection_timeout: float | None = None, **_ignored):
        if access not in ("read", "write"):
            raise ValueError(f"access is read or write, not {access!r}")
        self.instance, self.access = instance, access
        self.path = path if path is not None else os.environ.get("KG_RDFLIB_FILE")
        self.g = Graph()
        self._seq = 0
        self._nodes: dict[str, URIRef] = {}        # id -> node, insertion order
        self._out: dict[URIRef, list[URIRef]] = {}  # node -> its outgoing edge nodes
        self._in: dict[URIRef, list[URIRef]] = {}
        self._lock = None                           # the writer's lock file, held from before the load to close
        self.absent = False                         # True when the file did not exist: nothing published yet
        self.lock_waited = False                    # True when another writer held the lock first
        self.dirty = False                          # True once this handle changed the graph: only then does commit publish (S7)
        if not self.path:
            return
        if access == "write":
            if lock_timeout is None:
                lock_timeout = float(os.environ.get("KG_RDFLIB_LOCK_TIMEOUT") or connection_timeout or LOCK_TIMEOUT)
            self._acquire(lock_timeout)
            try:
                self._sweep()
                self._load()
            except BaseException:
                self._release()
                raise
        else:
            self._load()

    # ---- the file: lock, load, publish (task-0141.02) ------------------------------------------
    def _acquire(self, timeout: float) -> None:
        if fcntl is None:
            raise StoreBusy(f"{self.path}: a writer needs fcntl.flock, which this platform lacks; "
                            "the file-backed store is supported on POSIX only (unset KG_RDFLIB_FILE for an in-memory store)")
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        fd = os.open(self.path + ".lock", os.O_RDWR | os.O_CREAT, 0o644)
        deadline = time.monotonic() + max(0.0, timeout)
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if not self.lock_waited:
                        self.lock_waited = True
                        if _on_lock_wait is not None:
                            _on_lock_wait(self)
                    if time.monotonic() >= deadline:
                        raise StoreBusy(f"{self.path}: another writer holds the store (waited {timeout:g} s; "
                                        "KG_RDFLIB_LOCK_TIMEOUT sets how long)") from None
                    time.sleep(0.02)
        except BaseException:
            os.close(fd)
            raise
        self._lock = fd

    def _fence(self) -> None:
        """Publish only while the lock file at the path is the one this writer locked (task-0141.06): a lock
        file removed or replaced since (an operator clearing it, a recovery) means another writer may hold
        the new one, so this one publishes nothing."""
        held = os.fstat(self._lock)
        try:
            now = os.stat(self.path + ".lock")
        except FileNotFoundError:
            now = None
        if now is None or (now.st_dev, now.st_ino) != (held.st_dev, held.st_ino):
            raise StoreFenced(f"{self.path}: the lock file this writer holds was removed or replaced; nothing published")

    def _release(self) -> None:
        if self._lock is not None:
            fd, self._lock = self._lock, None
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _sweep(self) -> None:
        """Remove what an earlier writer's interrupted commit left: only the lock holder writes these."""
        directory = os.path.dirname(os.path.abspath(self.path))
        stem = TMP_PREFIX + os.path.basename(self.path) + "."
        for name in os.listdir(directory):
            if name.startswith(stem):
                try:
                    os.unlink(os.path.join(directory, name))
                except FileNotFoundError:
                    pass

    def _load(self) -> None:
        if self.access == "read":
            return self._load_shared()
        try:
            with open(self.path, "rb") as fh:
                data = fh.read()
        except FileNotFoundError:
            self.absent = True
            return
        self._parse(data)

    def _parse(self, data: bytes) -> None:
        try:
            self.g.parse(data=data, format="turtle")
        except Exception as e:  # noqa: BLE001 — rdflib raises several classes for a bad file
            raise StoreCorrupt(f"{self.path}: the store's file does not parse as Turtle ({type(e).__name__}); "
                               "it is left as it is: move it aside to start an empty store") from e
        self._reindex()

    def _load_shared(self) -> None:
        """A read handle's load (task-0097): the generation is the file the descriptor opened, identified
        by its fstat, which an atomic replace can neither change nor half-write; the parse is reused when
        the cached one is of that same file, else made and cached in its place."""
        global _snapshot, _parses
        try:
            fh = open(self.path, "rb")
        except FileNotFoundError:
            self.absent = True
            return
        with fh, _snapshot_lock:
            key = _identity(self.path, os.fstat(fh.fileno()))
            if _snapshot is not None and _snapshot[0] == key:
                _, self.g, self._nodes, self._out, self._in, self._seq = _snapshot
                return
            data = fh.read()
            self._parse(data)
            _parses += 1
            _snapshot = (key, self.g, self._nodes, self._out, self._in, self._seq)

    def commit(self) -> None:
        """Publish the graph atomically (see the module's docstring); a store in memory has nothing to publish."""
        if self.access != "write":
            raise StoreReadOnly(f"{self.path}: a read handle publishes nothing")
        if not self.path:
            return
        if self._lock is None:
            raise StoreBusy(f"{self.path}: this writer was closed; it no longer holds the lock and cannot publish")
        if not self.dirty:
            return   # nothing written: nothing to publish (S7)
        self._fence()
        directory = os.path.dirname(os.path.abspath(self.path))
        try:
            mode = stat.S_IMODE(os.stat(self.path).st_mode)   # the published file's, an operator's chmod included (S3)
        except FileNotFoundError:
            mode = 0o644
        fd, tmp = tempfile.mkstemp(prefix=TMP_PREFIX + os.path.basename(self.path) + ".", dir=directory)
        try:
            with os.fdopen(fd, "wb") as fh:
                self.g.serialize(destination=fh, format="turtle")
                fh.flush()
                _fsync(fh.fileno())
            os.chmod(tmp, mode)
            _replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise
        self.absent, self.dirty = False, False
        _fsync_dir(directory)

    def abort(self) -> None:
        """Nothing was published; the next open reads the last publication."""

    def close(self) -> None:
        """Release the writer's lock. Publishes nothing (task-0141.02): commit() does."""
        self._release()

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
            raise ValueError(DUPLICATE.format(nid=nid))   # store.UNIQUE_IDS: any id, so every label's (task-0201)
        n = self._n(nid)
        self._nodes[nid] = n
        self.dirty = True
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
            new = set() if v is None else {_lit(v)}
            if set(self.g.objects(n, P[k])) == new:
                continue   # unchanged: not a write
            self.g.remove((n, P[k], None))
            for o in new:
                self.g.add((n, P[k], o))
            self.dirty = True

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
        self.dirty = True
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
        self.dirty = True
        for e in list(self._out.get(n, [])) + list(self._in.get(n, [])):
            self._delete_edge(e)
        self.g.remove((n, None, None))
        self._nodes.pop(self.nid(n) if (n, P["id"], None) in self.g else next((k for k, v in self._nodes.items() if v == n), None), None)

    def _delete_edge(self, e: URIRef) -> None:
        src, _, dst = self._edge(e)
        self._out[src] = [x for x in self._out.get(src, []) if x != e]
        self._in[dst] = [x for x in self._in.get(dst, []) if x != e]
        self.g.remove((e, None, None))
        self.dirty = True

    def edge_count(self) -> int:
        return sum(len(v) for v in self._out.values())

    # ---- lifecycle ---------------------------------------------------------------------------
    def wipe(self) -> None:
        self.g = Graph()
        self._nodes, self._out, self._in, self._seq = {}, {}, {}, 0
        self.dirty = True

    def export_turtle(self) -> str:
        return self.g.serialize(format="turtle")

    def import_turtle(self, text: str) -> None:
        self.wipe()
        self.g.parse(data=text, format="turtle")
        self._reindex()

    def transaction_memory(self) -> dict | None:
        """Nothing bounds this store's unit in server transaction memory (task-0176): never refused."""
        return None

    def apply_constraints(self) -> list[dict]:
        return [{"type": kind, "cypher": name, "accepted": ok, "message": msg} for kind, name, ok, msg in CONSTRAINTS]

    # ---- loading -----------------------------------------------------------------------------
    def ensure_agents(self, tool_name, version, human, llm) -> None:
        self.merge_node("agent:harness", "Agent", props={"kind": "tool", "name": tool_name, "version": version})
        self.merge_node(human["id"], "Agent", props={"kind": "human", "name": human["name"]})
        self.merge_node(llm["id"], "Agent", props={"kind": "llm", "name": llm["name"]})

    def ensure_person(self, aid, handle) -> None:
        self.merge_node(aid, "Agent", props={"kind": "human", "name": handle})

    def create_activity(self, aid, kind, at, tool, note, agent_id, *, subject=None, scenario=None) -> None:
        ag = self.node(agent_id, "Agent")
        if ag is None:
            return
        held = {k: v for k, v in (("subject", subject), ("scenario", scenario)) if v is not None}   # task-0195
        act = self.create_node(aid, "Activity", {"kind": kind, "at": at, "tool": tool, "note": note, **held})
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

    def record_part_digests(self, vid, parts) -> None:
        v = self.node(vid, "Version")
        if v is not None:
            self.set_props(v, {"part_sha256": part_list(parts)})

    def part_digests(self) -> list[dict]:
        out = [p for a in self.nodes("Artefact") for v in self.out(a, "HAS_VERSION")
               for p in part_rows(self.nid(a), self.prop(v, "tag"), self.prop(v, "part_sha256"))]
        return sorted(out, key=lambda p: (p["artefact"], p["version"], p["part"]))

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
        if candidate_for:   # the open decision it claims to resolve; a transcript's candidate names none
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

    def verify_authored(self, at, scope, agent_id, artefacts=None) -> int:
        h = self.node(agent_id, "Agent")
        xs = [x for x in self.nodes("Assertion", basis="authored", status="proposed") if self.prop(x, "value") != "NONE"
              and (artefacts is None or self.prop(x, "artefact") in artefacts)]   # decision-0019: the Versions attested
        if h is None:
            return 0
        for x in xs:
            v = self.merge_node(f"ver:review:{self.nid(x)}", "Verification", props={"method": "review", "outcome": "pass", "at": at, "valid_until": None, "scope": scope})
            self.merge_edge(v, "VERIFIES", x)
            self.merge_edge(v, "PERFORMED_BY", h)
            self.set_props(x, {"status": "verified"})
        return len(xs)

    def approve_verified(self, at, record, agent_id, artefacts=None) -> int:
        h = self.node(agent_id, "Agent")
        xs = [x for x in self.nodes("Assertion", status="verified") if artefacts is None or self.prop(x, "artefact") in artefacts]
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

    def review_verifications(self) -> list[dict]:
        out = []
        for v in self.nodes("Verification", method="review"):
            if self.prop(v, "valid_until") is not None:
                continue
            for x in self.out(v, "VERIFIES"):
                if self.has_label(x, "Assertion"):
                    out.append({"id": self.nid(v), "key": self.prop(x, "key"), "at": self.prop(v, "at")})
        return sorted(out, key=lambda r: r["id"])

    def set_valid_until(self, dates) -> None:
        for vid, d in dates.items():
            v = self.node(vid, "Verification")
            if v is not None:
                self.set_props(v, {"valid_until": d})

    def register_derived(self, did, kind, sha, assertion_ids, recorded=None) -> None:
        props = {"kind": kind, "sha256": sha, "suspect": False}
        if recorded is not None:
            props["recorded"] = json.dumps(recorded, ensure_ascii=False, sort_keys=True)
        dv = self.create_node(did, "Derived", props)
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
                    docs = self.prop(a, "basis") in DOCUMENT_BASES and self.prop(b, "basis") in DOCUMENT_BASES   # any version (task-0197, H4)
                    if self.prop(a, "version") != self.prop(b, "version") and not docs and (
                            across is None or (self.prop(a, "basis") == across) == (self.prop(b, "basis") == across)):
                        continue
                    out.append({"a": ida, "va": self.prop(a, "value"), "ba": self.prop(a, "basis"), "aa": self.prop(a, "artefact"),
                                "b": idb, "vb": self.prop(b, "value"), "bb": self.prop(b, "basis"), "ab": self.prop(b, "artefact"),
                                "key": self.prop(a, "key"), "pred": self.prop(a, "predicate")})
        return sorted(out, key=lambda r: (str(r["key"]), r["a"], r["b"]))   # decision-0020: key, then id

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
            if self.prop(x, "status") in DEAD:   # an invalidated declaration declares nothing (task-0197, G5)
                continue
            for e in self.out(x, "ABOUT"):
                if self.has_label(e, "Entity"):
                    out.append({"entity": self.nid(e), "id": self.nid(x)})
        return out

    def add_declared_gap(self, gid, text, entity, assertion_id, scenario, key_entity, key) -> None:
        e, x = self.node(entity, "Entity"), self.node(assertion_id, "Assertion")
        if e is None or x is None:
            return
        g = self.node(gid, "Gap")
        if g is None or self.prop(g, "kind") != "closed":   # a review's close stands: R-REQ never reopens it (task-0197, H2)
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

    def invalidate_stale(self, new_tag, at=None) -> dict:
        inv_nodes, inv = [], []
        for x, f, cur in self._stale_candidates(new_tag):
            nf = next((c for c in self.out(cur, "HAS_FRAGMENT") if self.prop(c, "locator") == self.prop(f, "locator")), None)
            if nf is not None and self.prop(nf, "sha256") == self.prop(f, "sha256"):
                continue
            if x not in inv_nodes:
                inv_nodes.append(x)
            self.set_props(x, {"status": "invalidated", "invalidated_at": at, "invalidated_by": new_tag})
        # task-0197 (I5, I6): an older statement with a live successor of the same id stem in the new version is
        # invalidated too, though its own fragments did not change (a value resolved through a changed symbol,
        # a bundle that lost one of several fragments)
        succ = {stem(self.nid(y)) for y in self.nodes("Assertion", version=new_tag) if self.prop(y, "status") not in DEAD}
        for x in sorted(self.nodes("Assertion"), key=self.nid):
            if self.prop(x, "version") == new_tag or self.prop(x, "status") in DEAD or x in inv_nodes or stem(self.nid(x)) not in succ:
                continue
            inv_nodes.append(x)
            self.set_props(x, {"status": "invalidated", "invalidated_at": at, "invalidated_by": new_tag})
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
        # task-0197 (G5): a declared gap whose declaring statements this re-ingestion invalidated, all of them, is withdrawn
        withdrawn = []
        for g in sorted(self.nodes("Gap", kind="missing", declared=True), key=self.nid):
            xs = [x for x in self.out(g, "CONCERNS") if self.has_label(x, "Assertion")]
            if xs and any(x in inv_nodes for x in xs) and all(self.prop(x, "status") in DEAD for x in xs):
                self.set_props(g, {"kind": "withdrawn", "declared": False, "withdrawn_by": new_tag})
                withdrawn.append(self.nid(g))
        return {"invalidated": inv, "kept": kept, **({"withdrawn": withdrawn} if withdrawn else {})}

    def invalidate_keys(self, reasons, at=None) -> dict:
        inv = []
        for key, reason in sorted(reasons.items()):
            for x in sorted(self.nodes("Assertion", key=key), key=self.nid):
                if self.prop(x, "status") not in ("proposed", "validated", "verified", "approved", "disputed"):
                    continue
                self.set_props(x, {"status": "invalidated", "invalidated_at": at, "invalidated_by": reason})
                for v in self.inn(x, "VERIFIES"):
                    if self.has_label(v, "Verification"):
                        self.set_props(v, {"valid_until": reason})
                derived = set()
                for d in self.inn(x, "USED_ASSERTION"):
                    if self.has_label(d, "Derived"):
                        self.set_props(d, {"suspect": True})
                        derived.add(self.nid(d))
                inv.append({"id": self.nid(x), "key": key, "derived": sorted(derived)})
        return {"invalidated": sorted(inv, key=lambda r: r["id"])}

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
            aps = [{"id": self.nid(a), "at": self.prop(a, "at"), "record": self.prop(a, "record"), "until": self.prop(a, "until") or None}   # task-0198
                   for a in self.inn(x, "APPROVES") if self.has_label(a, "Approval")]
            gaps = [{"id": self.nid(g), "kind": self.prop(g, "kind"), "declared": self.prop(g, "declared"), "text": self.prop(g, "text")} for g in self.inn(x, "CONCERNS") if self.has_label(g, "Gap")]
            rows.append({"id": self.nid(x), "value": self.prop(x, "value"), "text": self.prop(x, "text"), "basis": self.prop(x, "basis"), "status": self.prop(x, "status"),
                         "artefact": self.prop(x, "artefact"), "agent": agent, "fragments": by_content(_distinct(frags)),
                         "verifications": by_id(_distinct(vers)), "approvals": by_id(_distinct(aps)), "gaps": by_id(_distinct(gaps))})
        return rows

    def declared_gaps_for_key(self, key) -> list[dict]:
        out = []
        for g in self.nodes("Gap", kind="missing", declared=True):
            for e, _t in self.edges_out(g, "CONCERNS_KEY"):
                if self.prop(e, "key") == key:
                    out.append({"id": self.nid(g), "text": self.prop(g, "text")})
        return by_id(out)   # task-0201 (doc-0030 S2): by id on both adapters

    def conflict_gaps(self) -> list[dict]:
        return sorted(({"id": self.nid(g), "text": self.prop(g, "text")} for g in self.nodes("Gap", kind="conflict")),
                      key=lambda r: r["id"])   # decision-0020: by id, the key then the pair

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
                        "verifications": by_id(_distinct(vers)) or [{"id": None, "valid_until": None}],
                        "successors": by_id(_distinct(succ)) or [{"id": None, "value": None, "status": None}]})
        return by_id(out)

    def derived_rows(self) -> list[dict]:
        return [{"id": self.nid(d), "kind": self.prop(d, "kind"), "sha256": self.prop(d, "sha256"), "recorded": self.prop(d, "recorded"),
                 "used": [{"id": self.nid(x), "status": self.prop(x, "status")} for x in self.out(d, "USED_ASSERTION") if self.has_label(x, "Assertion")]}
                for d in self.nodes("Derived")]

    def suspect_derived(self) -> list[dict]:   # task-0199: by suspicion, the one rule, never the stored flag
        return suspect_rows(suspicion(self, self.derived_rows()))

    def all_derived(self) -> list[dict]:
        return [{"id": r["id"], "suspect": r["suspect"]} for r in suspicion(self, self.derived_rows())]

    def held_keys(self) -> list[dict]:
        out: dict[str, dict] = {}
        for x in self.nodes("Assertion"):
            key = self.prop(x, "key")
            if key is None:
                continue
            k = out.setdefault(key, {"key": key, "n": 0, "statuses": {}})
            k["n"] += 1
            st = self.prop(x, "status")
            k["statuses"][st] = k["statuses"].get(st, 0) + 1
        return [out[k] for k in sorted(out)]

    def derived_outputs(self) -> list[dict]:
        sus = {r["id"]: r for r in suspicion(self, self.derived_rows())}
        return by_id([{"id": self.nid(d), "kind": self.prop(d, "kind"), "sha256": self.prop(d, "sha256"),
                       "suspect": sus[self.nid(d)]["suspect"], **changed_of(sus[self.nid(d)]),
                       "used": by_id(_distinct([{"id": self.nid(x), "key": self.prop(x, "key"), "status": self.prop(x, "status"),
                                                 "artefact": self.prop(x, "artefact"), "version": self.prop(x, "version")}
                                                for x in self.out(d, "USED_ASSERTION") if self.has_label(x, "Assertion")]))}
                      for d in self.nodes("Derived")])

    def artefact_assertions(self, artefact) -> list[dict]:
        def mine(path):
            return path == artefact or (artefact.endswith("/") and isinstance(path, str) and path.startswith(artefact))
        out = []
        for x in self.nodes("Assertion"):
            fs = [{"locator": self.prop(f, "locator"), "artefact": self.prop(f, "artefact")}
                  for f in self.out(x, "SUPPORTED_BY") if self.has_label(f, "Fragment") and mine(self.prop(f, "artefact"))]
            if not (mine(self.prop(x, "artefact")) or fs):
                continue
            out.append({"id": self.nid(x), "key": self.prop(x, "key"), "value": self.prop(x, "value"), "status": self.prop(x, "status"),
                        "basis": self.prop(x, "basis"), "artefact": self.prop(x, "artefact"), "version": self.prop(x, "version"),
                        "fragments": by_content(_distinct(fs))})
        return by_id(out)

    def record_preload(self, vid, verdict) -> None:
        v = self.node(vid, "Version")
        if v is not None:
            self.set_props(v, {f"preload_{k}": verdict.get(k) for k in ("state", "tool", "tool_version", "digest", "report", "why")})

    def record_act_finding(self, row) -> None:
        self.merge_node(row["id"], "ActFinding", props={k: row[k] for k in self.ACT_FIELDS})

    def withdraw_construction(self, artefacts) -> int:
        n = 0
        for x in list(self.nodes("Assertion")):
            if self.prop(x, "artefact") not in artefacts:
                continue
            xid, hit = self.nid(x), False
            for nid in (f"ver:review:{xid}", f"appr:{xid}"):
                node = self._nodes.get(nid)
                if node is not None:
                    self.delete_node(node)
                    hit = True
            if not hit or self.prop(x, "status") not in ("approved", "verified"):
                continue
            aps = [a for a in self.inn(x, "APPROVES") if self.has_label(a, "Approval")]
            vs = [v for v in self.inn(x, "VERIFIES") if self.has_label(v, "Verification")]
            status = "approved" if aps else "verified" if vs else "proposed"
            if status != self.prop(x, "status"):
                self.set_props(x, {"status": status})
                n += 1
        return n

    def record_attestation(self, row) -> None:
        a = self.node(row["attester"], "Agent")
        if a is not None:
            self.set_props(a, {f"attestation_{row['declaration']}": json.dumps({k: row[k] for k in ("id", *self.ATTESTATION_FIELDS)}, sort_keys=True)})

    def attestations(self) -> list[dict]:
        return by_id([json.loads(self.prop(a, f"attestation_{d}")) for a in self.nodes("Agent") for d in ("approval", "authored")
                      if self.prop(a, f"attestation_{d}")])

    def clear_act_findings(self) -> None:
        for a in list(self.nodes("ActFinding")):
            self.delete_node(a)

    def gap_brief(self, gid) -> dict | None:
        g = self.node(gid, "Gap")
        if g is None:
            return None
        keys = sorted(self.prop(e, "key") for e, _t in self.edges_out(g, "CONCERNS_KEY") if self.prop(e, "key") is not None)
        return {"id": gid, "kind": self.prop(g, "kind"), "declared": self.prop(g, "declared"), "text": self.prop(g, "text"), "keys": keys}

    def record_lint_gap(self, row) -> None:
        self.merge_node(row["id"], "LintGap", props={k: row.get(k) for k in self.LINT_FIELDS})

    def resolve_lint_gap(self, gid, resolution, review_id, by, on, record, note) -> None:
        g = self.node(gid, "LintGap")
        if g is not None:
            self.set_props(g, {"resolution": resolution, "review": review_id, "resolved_by": by, "resolved_on": on,
                               "record": record, "note": note})

    def lint_gaps(self) -> list[dict]:
        return by_id([{"id": self.nid(g), **{k: self.prop(g, k) for k in self.LINT_FIELDS}} for g in self.nodes("LintGap")])

    def act_findings(self) -> list[dict]:
        return by_id([{"id": self.nid(a), **{k: self.prop(a, k) for k in self.ACT_FIELDS}} for a in self.nodes("ActFinding")])

    def preload_verdicts(self) -> list[dict]:
        out = []
        for a in self.nodes("Artefact"):
            for v in self.out(a, "HAS_VERSION"):
                if self.prop(v, "preload_state") is not None:
                    out.append({"artefact": self.nid(a), "version": self.prop(v, "tag"),
                                **{k: self.prop(v, f"preload_{k}") for k in ("state", "tool", "tool_version", "digest", "report", "why")}})
        return sorted(out, key=lambda r: (r["artefact"], r["version"]))

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
        return [self.nid(a) for a in sorted(acts, key=lambda a: (self.prop(a, "at") or "", self.nid(a)))]   # as the Neo4j adapter orders them

    def held(self) -> dict | None:
        acts = [{"id": self.nid(a), "at": self.prop(a, "at"), "subject": self.prop(a, "subject"), "scenario": self.prop(a, "scenario")}
                for a in self.nodes("Activity") if self.nid(a).startswith("act:extract:")]
        current = [{"artefact": self.nid(a), "tag": self.prop(v, "tag"), "versions": len(self.out(a, "HAS_VERSION"))}
                   for a in self.nodes("Artefact") for v in self.out(a, "CURRENT")]
        return held_from(acts, current)

    def extraction_times(self) -> list[dict]:
        acts = [a for a in self.nodes("Activity") if self.nid(a).startswith("act:extract:")]
        return [{"id": self.nid(a), "at": self.prop(a, "at")} for a in sorted(acts, key=lambda a: (self.prop(a, "at") or "", self.nid(a)))]

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
        rows: dict[tuple[str, str], dict] = {}   # one row per statement and cited document, as the Cypher groups them
        artefacts = [(self.prop(a, "id") or "", a) for a in self.nodes("Artefact")]
        for l in self.inn(n, "REG_LINK_OF"):
            if not self.has_label(l, "RegLink") or self.prop(l, "state") != "approved":
                continue
            for e, d in self.edges_out(l, "REG_CITES"):
                cited = self.prop(e, "anchor") or ""
                anchor = cited.split("#", 1)[1] if "#" in cited else None
                path = self.prop(d, "path")
                for aid, a in artefacts:
                    # the file artefact of the path, or the file's fragments in a directory artefact (task-0077)
                    if aid == path:
                        file = ""
                    elif aid.endswith("/") and path.startswith(aid):
                        file = path[len(aid):] + ":"
                    else:
                        continue
                    for v in self.out(a, "HAS_VERSION"):
                        for f in self.out(v, "HAS_FRAGMENT"):
                            loc = self.prop(f, "locator") or ""
                            if not loc.startswith(file) or (anchor is not None and anchor not in loc[len(file):].split("/")):
                                continue
                            for x in self.inn(f, "SUPPORTED_BY"):
                                if not self.has_label(x, "Assertion"):
                                    continue
                                r = rows.setdefault((self.nid(x), path), {"statement": self.nid(x), "status": self.prop(x, "status"), "document": path,
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


def _fsync_dir(directory: str) -> None:
    """Make the replacement's directory entry durable where the platform allows opening a directory."""
    try:
        dfd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dfd)
    except OSError:
        pass
    finally:
        os.close(dfd)


def _distinct(rows: list[dict]) -> list[dict]:
    out, seen = [], set()
    for r in rows:
        k = json.dumps(r, sort_keys=True, default=str)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out
