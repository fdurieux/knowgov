"""The store port: the operations the harness and the page need from a store, and nothing else.

Not a generic graph API. Each method is one thing the loader, the rules, the gate, the census,
the SHACL projection or the register projection does; the first adapter (``store_neo4j.py``)
keeps the Cypher, the Browser link and the saved queries. ``open_store()`` picks the adapter
from ``KG_STORE`` (``neo4j`` is the default) and returns it ready to use as a context manager. Every
caller names its access (task-0141.02):

    with open_store(access="write") as st:   # a unit of work: published when the block ends cleanly,
        st.wipe()                             # abandoned when it raises
        ...

    with open_store(access="read") as st:    # a snapshot: the port's reads only, never published
        st.census()

A read handle (``ReadOnly``) lets through the operations in ``READS`` and refuses every other with
``StoreReadOnly``; closing it publishes nothing. A write handle publishes on ``commit()`` (the context
manager's clean exit) and never on ``close()``, which releases it; ``abort()`` drops what it changed.

Generations (task-0141.06, decision-0014): a writer builds its unit privately and publishes it whole;
a read handle answers from one published generation for its whole life, or refuses. The file-backed
rdflib adapter takes its writer lock before it loads the snapshot it starts from, holds it to an atomic
replace of the file, and a reader keeps the snapshot it loaded (``store_rdflib.py``). The Neo4j adapter
holds a lease in the database from open to close, writes the whole unit in one transaction, and
publishes under a sequence lock that every read call checks (``store_neo4j.py``): a publication that
lands during a read raises ``StoreChanged``, and ``read()`` runs the logical read again.

A scratch store (task-0183): ``scratch_store()`` is a writer on an rdflib graph in this process's memory,
never a file and never the store ``KG_STORE`` names. A command that computes an answer for one person
(``capture.py questionnaire`` and ``review``, ``transcript.py``) loads its scenario there, so that the
shared store the page, the runs and the MCP servers read keeps what it holds. ``gate_cli.py`` loads there
too unless ``--publish`` (decision-0017). The shared store is written only by a run, the gate command with
``--publish``, a trace registration and the register projection.

Status and provenance are the store's; content stays in git. Every adapter must give the
same answers for the same calls, which the deterministic comparator checks on the CargoQuote
record. The evaluation's §11 names when another store would be preferred; with this port that
is an adapter, not a rewrite.
"""
from __future__ import annotations

import os
from typing import Any


DEAD = ("rejected", "deprecated", "invalidated")   # a statement in one of these states takes part in no rule
DOCUMENT_BASES = ("extracted", "authored")         # a document's statements: they pair across versions (task-0197, H4)


def stem(assertion_id: str) -> str:
    """A statement's id without its version (``A:dt:P2|surcharge@v1`` -> ``A:dt:P2|surcharge``): the stage-2
    re-load diffs statements by it (task-0197)."""
    return assertion_id.rsplit("@", 1)[0]


def part_list(parts: dict[str, str]) -> list[str]:
    """A directory artefact's file digests as a Version's ``part_sha256``: ``"<sha256>  <rel>"`` by path."""
    return [f"{sha}  {rel}" for rel, sha in sorted(parts.items())]


def part_rows(artefact: str, version: str, entries) -> list[dict]:
    """``part_sha256`` entries back as {artefact, version, part, sha256} rows."""
    return [{"artefact": artefact, "version": version, "part": e[66:], "sha256": e[:64]} for e in entries or []]


class StoreReadOnly(PermissionError):
    """An operation that would change the store, asked of a read handle: refused, nothing changed."""


class StoreBusy(RuntimeError):
    """Another writer holds the store past this one's lock timeout: nothing was loaded or changed."""


class StoreCorrupt(RuntimeError):
    """The store's published file does not parse: left as it is, never read as an empty store."""


class StoreChanged(StoreBusy):
    """A publication landed while this read handle was reading (task-0141.06): what it read so far may
    belong to two generations, so the logical read is refused. ``read()`` retries it on a fresh handle."""


class StoreFenced(StoreBusy):
    """This writer no longer owns the store (its lease expired and another writer took it, or its lock
    file was replaced): it publishes nothing, and what it built is dropped (task-0141.06)."""


# The port's reads (task-0141.02): what a read handle lets through. Every other operation of the port
# changes the store, or, for console_query, may (it runs whatever text it is given).
READS = frozenset({
    "part_digests", "find_fragment", "review_verifications", "structural_violations", "candidate_pairs",
    "vague_fragments", "unresolved_assertions", "declared_open", "requirements_without", "silent_entities",
    "key_evidence", "declared_gaps_for_key", "conflict_gaps", "assertion_brief", "declared_gap", "stale_on_keys",
    "suspect_derived", "all_derived", "preload_verdicts", "census", "extraction_activities", "extraction_times",
    "gaps_with_concerns", "assertions_on_key", "assertion_rows", "supported_by", "candidate_for",
    "fragments_with_version", "requirements_verified_by", "register_census", "register_node_statements",
    "export_turtle", "describe", "saved_queries", "held_keys", "derived_outputs", "artefact_assertions", "held",
    "act_findings", "derived_rows", "attestations"})


def held_from(acts: list[dict], current: list[dict]) -> dict | None:
    """``held()`` from the extraction activities ({id, at, subject, scenario}) and each artefact's current
    version ({artefact, tag, versions}), the same on both adapters (task-0195)."""
    if not acts:
        return None
    subjects = {a.get("subject") for a in acts}
    scenarios = {a.get("scenario") for a in acts}
    # a store loaded before task-0195 recorded neither; its scenario is read from the activity id here,
    # the one place, and its subject is unknown (None), which every reader refuses but for an only subject
    if scenarios == {None}:
        scenarios = {a["id"].split(":")[2] for a in acts if a["id"].count(":") >= 3}
    versions = {c["artefact"]: c["tag"] for c in current}
    reloaded = sorted({c["tag"] for c in current if int(c.get("versions") or 1) > 1})
    tags = sorted(set(versions.values()))
    version = reloaded[0] if len(reloaded) == 1 else (tags[0] if len(tags) == 1 else None)
    return {"subject": next(iter(subjects)) if len(subjects) == 1 else None,
            "scenario": next(iter(scenarios)) if len(scenarios) == 1 else None,
            "version": version, "versions": dict(sorted(versions.items())),
            "loaded_at": max((str(a["at"]) for a in acts if a.get("at") is not None), default=None)}


# task-0201 (doc-0030 S4): the one uniqueness rule of the port. A node's id is unique among the nodes of its
# label for each label here, on both adapters: the rdflib adapter refuses any id it already holds; the Neo4j
# adapter holds the first six by its uniqueness constraints (CONSTRAINTS, the record's D1, unchanged) and
# refuses the rest at create (``NEO4J_GUARDED``), so a duplicate Derived or Activity is refused on both, never
# held by one store and lost by export_turtle. Every other node is written by MERGE, one per id.
UNIQUE_IDS = ("Artefact", "Version", "Fragment", "Entity", "Assertion", "Gap", "Activity", "Derived")
NEO4J_GUARDED = ("Activity", "Derived")
DUPLICATE = "a node with id {nid!r} exists: the uniqueness constraint refuses it"


def by_id(rows: list[dict]) -> list[dict]:
    """``rows`` in one order on every adapter: by ``id``, a row without one (an OPTIONAL MATCH that met
    nothing) last. A store's collect() answers in its own traversal order, which a reload can move;
    what the gate prints and compares (the bundle, its report) must not."""
    return sorted(rows, key=lambda r: (r.get("id") is None, str(r.get("id"))))


def by_content(rows: list[dict]) -> list[dict]:
    """``rows`` without an id (a fragment) in one order on every adapter: by their fields."""
    import json
    return sorted(rows, key=lambda r: json.dumps(r, sort_keys=True, default=str))


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_digest(fragments) -> str:
    """A statement's content digest beside its value (task-0199): the sha256 of its supporting fragments'
    sha256s (each over the fragment's text, as the load digests it), sorted, one per line. A person's
    answer has no fragment, so its digest is the empty text's and its value carries its content."""
    return _sha("\n".join(sorted(_sha(f.get("text") or "") for f in fragments)))


EVERY_STATUS = ("proposed", "validated", "verified", "approved", "disputed", "rejected", "invalidated")


def statement_content(st, ids) -> dict[str, dict]:
    """id -> {id, key, value, status, sha256} for each of ``ids`` the store holds, by the port's reads
    (``assertion_brief``, ``key_evidence``); an id it does not hold is absent."""
    out: dict[str, dict] = {}
    by_key: dict[str, list[str]] = {}
    for aid in dict.fromkeys(ids):
        b = st.assertion_brief(aid)
        if b is not None:
            out[aid] = {"id": aid, "key": b["key"], "value": b["value"], "status": b["status"], "sha256": content_digest([])}
            by_key.setdefault(b["key"], []).append(aid)
    for key, mine in by_key.items():
        for r in st.key_evidence(key, list(EVERY_STATUS)):
            if r["id"] in out:
                out[r["id"]]["sha256"] = content_digest(r.get("fragments") or [])
    return out


def suspicion(st, rows: list[dict]) -> list[dict]:
    """The one rule for *suspect* (task-0199, doc-0030 R5, doc-0032 §6 item 6), which the gate
    (``suspect_derived``), the MCP reader (``derived_outputs``) and trace share: a derived output is suspect
    when a statement it used is invalidated, or, where its registration recorded what it used (``recorded``:
    each statement's id, value and content digest, trace's ledger), when the statement of that id now holds
    another value or digest, or is not held at all. Computed from the store's statuses and content, never from
    a stored flag. ``rows``: each derived output's {id, kind, sha256, recorded (JSON text or None), used:
    [{id, status}]}; returns them with ``used_invalidated`` and ``used_changed`` (ids, sorted) and ``suspect``."""
    import json
    rec = {r["id"]: json.loads(r["recorded"]) if r.get("recorded") else None for r in rows}
    held = statement_content(st, [u["id"] for v in rec.values() for u in v or []])
    out = []
    for r in rows:
        bad = sorted({u["id"] for u in r.get("used") or [] if u.get("id") and u.get("status") == "invalidated"}
                     | {u["id"] for u in rec[r["id"]] or [] if held.get(u["id"], {}).get("status") == "invalidated"})
        changed = sorted(u["id"] for u in rec[r["id"]] or [] if u["id"] not in held
                         or (str(held[u["id"]]["value"]), held[u["id"]]["sha256"]) != (str(u.get("value")), u.get("sha256")))
        out.append({**{k: v for k, v in r.items() if k not in ("recorded",)}, "used_invalidated": bad,
                    "used_changed": [x for x in changed if x not in bad], "suspect": bool(bad or changed),
                    "bound": rec[r["id"]] is not None})
    return by_id(out)


def suspect_rows(rows: list[dict]) -> list[dict]:
    """``suspicion``'s suspect rows as ``suspect_derived`` answers them: {id, kind, sha256, used_invalidated},
    and ``used_changed`` only where some statement changed under its id, so the record's rows read as before."""
    return [{"id": r["id"], "kind": r["kind"], "sha256": r["sha256"], "used_invalidated": r["used_invalidated"], **changed_of(r)}
            for r in rows if r["suspect"]]


def changed_of(r: dict) -> dict:
    return {"used_changed": r["used_changed"]} if r.get("used_changed") else {}


class Store:
    """The port. An adapter subclasses it and implements every method; the base raises."""

    name = "abstract"
    instance = ""          # the instance id the adapter may stamp on its writes (a shared store later)
    access = "write"       # "read" or "write", as opened (task-0141.02)

    # ---- lifecycle
    def __enter__(self) -> "Store":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """A unit of work: published when the block ends cleanly, abandoned when it raises; released either way."""
        try:
            if exc_type is None:
                self.commit()
            else:
                self.abort()
        finally:
            self.close()

    def commit(self) -> None:
        """Publish what this handle changed. A store that writes as it goes has nothing left to publish."""

    def abort(self) -> None:
        """Abandon what this handle changed and has not published, where the adapter can."""

    def close(self) -> None:
        """Release the handle. Never publishes: a writer that did not commit leaves the store as it was."""

    def wipe(self) -> None:
        """Delete everything this instance holds. The free Neo4j edition serves one database."""
        raise NotImplementedError

    def apply_constraints(self) -> list[dict]:
        """Try each constraint family; return {type, cypher, accepted, message} per constraint:
        what the edition refuses is itself a measurement (D1)."""
        raise NotImplementedError

    def transaction_memory(self) -> dict | None:
        """What bounds a writer's unit in transaction memory (task-0176; harness/load_memory.py):
        ``{"limit": {bytes, setting, value} or None, "published": statements of the published generation}``,
        or None when nothing bounds it. Only a store whose unit is one server transaction has one."""
        return None

    # ---- loading: agents, activities, artefacts, fragments, entities, assertions
    def ensure_agents(self, tool_name: str, version: str, human: dict, llm: dict) -> None:
        raise NotImplementedError

    def ensure_person(self, aid: str, handle: str) -> None:
        """A person who gave knowledge (task-0009; ieam-register decision 0008): an Agent of kind
        human named by an opaque handle, never a name."""
        raise NotImplementedError

    def create_activity(self, aid: str, kind: str, at: str, tool: str, note: str, agent_id: str, *,
                        subject: str | None = None, scenario: str | None = None) -> None:
        """An Activity. An extraction names the ``subject`` and ``scenario`` it loads (task-0195): the
        held state, which ``held()`` reads; its id stays ``act:extract:<scenario>:<version>``, as the
        record's run files name it."""
        raise NotImplementedError

    def upsert_artefact_version(self, path: str, family: str, fmt: str, vid: str, sha: str, nbytes: int, ts: str, tag: str, aid: str) -> None:
        raise NotImplementedError

    def record_part_digests(self, vid: str, parts: dict[str, str]) -> None:
        """Set on Version ``vid`` of a directory artefact the sha256 of each file in its bundle,
        relative path -> hex digest (task-0094): the Version's own ``sha256`` is the whole bundle's,
        so a citation of one file is compared with this. Stored as ``part_sha256``, a list of
        ``"<sha256>  <relative path>"`` sorted by path, sha256sum's form."""
        raise NotImplementedError

    def part_digests(self) -> list[dict]:
        """Every file digest a directory artefact's versions carry: artefact, version (tag), part,
        sha256; sorted by artefact, version and part. Empty when no directory artefact is loaded."""
        raise NotImplementedError

    def find_fragment(self, artefact: str, locator: str, sha: str) -> str | None:
        raise NotImplementedError

    def link_fragment(self, vid: str, fid: str) -> None:
        raise NotImplementedError

    def create_fragment(self, vid: str, fid: str, locator: str, sha: str, text: str, artefact: str) -> None:
        raise NotImplementedError

    def ensure_entity(self, eid: str, kind: str, name: str) -> None:
        raise NotImplementedError

    def create_assertion(self, props: dict, entity: str, activity: str, agent: str, fragment_ids: list[str]) -> None:
        """props: id, predicate, value, raw_value, text, basis, status, artefact, key, unresolved, version."""
        raise NotImplementedError

    def link_mentions(self) -> None:
        """Every fragment MENTIONS the entities its assertions are about."""
        raise NotImplementedError

    def create_inferred(self, props: dict, entity: str, activity: dict, agent_id: str, candidate_for: str | None) -> None:
        """A model-proposed assertion with its inference activity, a candidate for a declared gap
        (``candidate_for``), or for none when it is None (a transcript's candidate, task-0041)."""
        raise NotImplementedError

    # ---- verifications and approvals
    def verify_by_execution(self, key: str, values: list[str], suite_scenario: str, scope: str, ts: str, digest: str) -> int:
        raise NotImplementedError

    def verify_by_review(self, key: str, values: list[str], at: str, scope: str, agent_id: str) -> int:
        raise NotImplementedError

    def verify_authored(self, at: str, scope: str, agent_id: str, artefacts: list[str] | None = None) -> int:
        """Review by construction every authored statement still proposed; with ``artefacts`` (decision-0019),
        only those of these artefacts, the Versions the declaration attests. None: every artefact (the read rule)."""
        raise NotImplementedError

    def approve_verified(self, at: str, record: str, agent_id: str, artefacts: list[str] | None = None) -> int:
        """Approve every verified statement; with ``artefacts`` (decision-0019), only those of these artefacts."""
        raise NotImplementedError

    def reverify(self, version: str, keys: list[str], agent_id: str, ts: str, scope: str, record: str) -> list[str]:
        """Re-verify and re-approve the new version's assertions on the named keys; their ids."""
        raise NotImplementedError

    def review_verifications(self) -> list[dict]:
        """Every verification of method review that carries no ``valid_until``: {id, key, at}, ``key``
        the key of the statement it verifies (decision-0005; harness/cadence.py dates them)."""
        raise NotImplementedError

    def set_valid_until(self, dates: dict[str, str]) -> None:
        """Write ``valid_until`` on the verifications named, verification id -> YYYY-MM-DD."""
        raise NotImplementedError

    def register_derived(self, did: str, kind: str, sha: str, assertion_ids: list[str], recorded: list[dict] | None = None) -> None:
        """A derived output ``did`` that used ``assertion_ids``. ``recorded`` (trace, task-0199): what it used as
        its ledger records it, each statement's {id, key, value, sha256}, kept as JSON text in ``recorded`` so
        ``suspicion`` sees a change under the same id; None (the record's stage 2) keeps none."""
        raise NotImplementedError

    # ---- the rules
    def structural_violations(self) -> list[dict]:
        raise NotImplementedError

    def candidate_pairs(self, across: str | None = None) -> list[dict]:
        """Live assertion pairs on one entity and predicate from different artefacts: of the same
        version, and, when ``across`` names a basis, of any versions when exactly one side carries
        it (a capture's version is never a document's; task-0038). Each row: a, va, ba, aa (its
        artefact), b, vb, bb, ab, key, pred."""
        raise NotImplementedError

    def corroborate(self, a: str, b: str, promote: bool = True) -> None:
        """a and b agree (CORROBORATES both ways); with ``promote`` a proposed side becomes validated."""
        raise NotImplementedError

    def mark_conflict(self, a: str, b: str, gid: str, key: str, scenario: str, text: str | None = None) -> None:
        """a and b contradict each other: both disputed, a conflict gap concerning both. ``text``
        replaces the gap's default wording (two artefacts, each with its value)."""
        raise NotImplementedError

    def vague_fragments(self, words: list[str]) -> list[dict]:
        raise NotImplementedError

    def add_ambiguous_gap(self, assertion_id: str, text: str, scenario: str) -> None:
        raise NotImplementedError

    def unresolved_assertions(self) -> list[dict]:
        raise NotImplementedError

    def declared_open(self, predicate: str) -> list[dict]:
        """Assertions whose predicate says a thing is declared absent (value NONE): entity and id."""
        raise NotImplementedError

    def add_declared_gap(self, gid: str, text: str, entity: str, assertion_id: str, scenario: str, key_entity: str, key: str) -> None:
        raise NotImplementedError

    def add_absent_artefact_gap(self, artefact: str, assertion_id: str) -> None:
        raise NotImplementedError

    def requirements_without(self, predicate: str) -> list[str]:
        raise NotImplementedError

    def add_unverified_requirement_gap(self, req: str) -> None:
        raise NotImplementedError

    def silent_entities(self, kinds: list[str]) -> list[str]:
        raise NotImplementedError

    def mark_unverified(self) -> int:
        raise NotImplementedError

    def invalidate_stale(self, new_tag: str) -> dict:
        raise NotImplementedError

    def invalidate_keys(self, reasons: dict[str, str]) -> dict:
        """A register change (task-0122, harness/register_change.py): every live statement (proposed,
        validated, verified, approved, disputed) on each key of ``reasons`` is invalidated, its
        ``invalidated_by`` the key's reason; its verifications end (``valid_until`` the reason) and the
        derived outputs that used it turn suspect, as ``invalidate_stale`` does for a source change.
        Returns {invalidated: [{id, key, derived}]}, sorted by id, ``derived`` sorted."""
        raise NotImplementedError

    # ---- the gate
    def key_evidence(self, key: str, live: list[str]) -> list[dict]:
        raise NotImplementedError

    def declared_gaps_for_key(self, key: str) -> list[dict]:
        """The declared open gaps concerning ``key``: {id, text}, by id on both adapters (task-0201, doc-0030 S2)."""
        raise NotImplementedError

    def conflict_gaps(self) -> list[dict]:
        """Every conflict gap: {id, text}. Its order is the store's: ordering it renumbers the record's conflict
        gap ids (R-CONFLICT numbers them in candidate_pairs' order), which waits for task-0202's decision."""
        raise NotImplementedError

    # ---- a person's review (task-0037, decision-0002): the rulings harness/review.py has checked
    def assertion_brief(self, assertion_id: str) -> dict | None:
        """{id, key, value, basis, status, agent} for one assertion, whatever its status; None if absent."""
        raise NotImplementedError

    def declared_gap(self, gid: str) -> dict | None:
        """{id, text, keys} for an open declared gap; None if there is none by that id."""
        raise NotImplementedError

    def apply_ruling(self, assertion_id: str, outcome: str, review_id: str, agent_id: str, at: str, record: str, until: str) -> None:
        """approved: an Approval {at, record, until} by the agent, status approved. rejected: status
        rejected, the node and its history kept, out of the live set. lapsed: an approval past its
        time, on a statement a settled dispute had left disputed; it reads proposed (task-0038).
        Anything else: no change."""
        raise NotImplementedError

    def close_declared_gap(self, gid: str, review_id: str, at: str, record: str) -> None:
        """The gap's open decision was taken: it is kept, marked closed, and no longer declared open."""
        raise NotImplementedError

    def settle_conflicts(self, key: str, review_id: str) -> int:
        """Every conflict gap on an assertion of the key is marked settled; returns how many."""
        raise NotImplementedError

    def stale_on_keys(self, keys: list[str]) -> list[dict]:
        raise NotImplementedError

    def derived_rows(self) -> list[dict]:
        """Every derived output as ``suspicion`` reads it: {id, kind, sha256, recorded, used: [{id, status}]}
        (task-0199); the rule's input, read by the three reads below."""
        raise NotImplementedError

    def suspect_derived(self) -> list[dict]:
        """The suspect derived outputs by ``suspicion``, the one rule: {id, kind, sha256, used_invalidated,
        used_changed, ...}, by id (task-0199: no stored flag decides it)."""
        raise NotImplementedError

    def all_derived(self) -> list[dict]:
        """Every derived output with ``suspect`` by ``suspicion`` (task-0199)."""
        raise NotImplementedError

    # ---- the store reads over MCP (task-0144, doc-0020 C3): each answers by id, as by_id orders it
    def held_keys(self) -> list[dict]:
        """Every key a statement of the store names, by key: {key, n, statuses: {status: count}}."""
        raise NotImplementedError

    def derived_outputs(self) -> list[dict]:
        """Every derived output, any state, by id: {id, kind, sha256, suspect, used: [{id, key, status,
        artefact, version}]}, the statements it used (USED_ASSERTION) by id; ``suspect`` by ``suspicion``,
        with ``used_changed`` (task-0199)."""
        raise NotImplementedError

    def artefact_assertions(self, artefact: str) -> list[dict]:
        """The statements a document yields, by id: those whose artefact is ``artefact`` or one of whose
        supporting fragments is from it (a directory artefact, ending in '/', by prefix), each {id, key,
        value, status, basis, artefact, version, fragments: [{locator, artefact}]}, its fragments from
        that document only, by content."""
        raise NotImplementedError

    # ---- the pre-load check's verdict on a version (task-0064; harness/preload.py)
    def record_preload(self, vid: str, verdict: dict) -> None:
        """Set on Version ``vid`` the verdict a pre-load report gave its bytes: preload_state,
        preload_tool, preload_tool_version, preload_digest, preload_report, preload_why."""
        raise NotImplementedError

    def preload_verdicts(self) -> list[dict]:
        """Every version that carries a verdict: artefact, version (tag), state, tool, tool_version,
        digest, report, why; sorted by artefact and version. Empty when no load recorded one."""
        raise NotImplementedError

    # ---- a person's acts the load did not apply as written (task-0199, doc-0030 H5, doc-0032 §6)
    ACT_FIELDS = ("review", "by", "on", "act", "n", "statement", "outcome", "key", "why", "from_value", "from_sha256",
                  "to", "reasons")

    def record_act_finding(self, row: dict) -> None:
        """Keep, as an ``ActFinding`` node of id ``row["id"]``, one act of a review file the load did not apply as
        written (``load.load_reviews``): a ruling or close whose statement changed or vanished, a refused file, a
        file from before 0.9.0 bound by id. Its fields are ``ACT_FIELDS``, scalars (``to`` and ``reasons`` JSON
        text); writing one id again replaces it, so stage 2's recheck never doubles one."""
        raise NotImplementedError

    ATTESTATION_FIELDS = ("declaration", "bound", "attester", "unattested")

    def record_attestation(self, row: dict) -> None:
        """Keep, as an ``Attestation`` node of id ``row["id"]`` (``attest:authored``, ``attest:approval``), how the
        load read a ``[verification]`` declaration (decision-0019, task-0221): ``bound`` (it lists Versions) and,
        as JSON text in ``unattested``, the stored artefacts it did not attest, each {artefact, sha256, parts}.
        Writing one id again replaces it, so stage 2 records what its later documents read."""
        raise NotImplementedError

    def attestations(self) -> list[dict]:
        """Every ``Attestation``: id and ``ATTESTATION_FIELDS``, by id. Empty when the subject declares none."""
        raise NotImplementedError

    def act_findings(self) -> list[dict]:
        """Every ``ActFinding``: id and ``ACT_FIELDS``, by id. Empty when every act applied as written."""
        raise NotImplementedError

    # ---- the census and the page
    def census(self) -> dict:
        raise NotImplementedError

    def extraction_activities(self) -> list[str]:
        """The extraction activity ids, oldest first. Which subject and scenario the store holds is
        ``held()``'s, never these ids' (task-0195)."""
        raise NotImplementedError

    def held(self) -> dict | None:
        """What the store holds (task-0195): ``{subject, scenario, version, versions, loaded_at}``, or None
        when nothing is loaded. ``subject`` and ``scenario`` are what the extraction recorded (a store
        loaded before task-0195 recorded no subject: None). ``versions`` is each artefact's current
        version by its ``CURRENT`` edge, and ``version`` the held one: the current tag of an artefact
        loaded more than once (a stage-2 change), else the one tag. ``loaded_at`` is the latest
        extraction's time. Never the extraction activities' order (S5)."""
        raise NotImplementedError

    def extraction_times(self) -> list[dict]:
        """{id, at} for every extraction activity, in extraction_activities' order: when it was loaded (task-0128)."""
        raise NotImplementedError

    def gaps_with_concerns(self) -> list[dict]:
        raise NotImplementedError

    def assertions_on_key(self, key: str, statuses: list[str]) -> list[dict]:
        raise NotImplementedError

    # ---- the SHACL projection's reads
    def assertion_rows(self) -> list[dict]:
        raise NotImplementedError

    def supported_by(self) -> list[dict]:
        raise NotImplementedError

    def candidate_for(self) -> list[dict]:
        raise NotImplementedError

    def fragments_with_version(self) -> list[dict]:
        raise NotImplementedError

    def requirements_verified_by(self) -> list[dict]:
        raise NotImplementedError

    # ---- the register projection (its own namespace, wiped by a run)
    def project_register(self, rows: dict) -> None:
        raise NotImplementedError

    def register_census(self) -> dict | None:
        raise NotImplementedError

    def register_node_statements(self, start: str) -> list[dict]:
        """From register node ``start`` to the statements its approved links cite, at the grain of the
        cited anchor (a citation ``path#DT-P`` reaches only fragments whose locator holds ``DT-P`` as a
        path segment; one with no anchor, the whole document), across every version, and the derived
        outputs that used each (task-0046). A document is a file artefact of the cited path or that file's
        fragments in a directory artefact (task-0077). One dict per statement and cited document (a
        statement two cited documents support is two rows), ordered by document then statement:
        statement, status, document, and sorted lists anchors, links, versions, fragments, derived
        ("<id>" or "<id> (suspect)")."""
        raise NotImplementedError

    # ---- portability: the graph as Turtle (task-0070)
    def export_turtle(self) -> str:
        """Everything this instance holds, as Turtle in the interchange vocabulary, the rdflib
        adapter's own form: a node is ``urn:kg:n:<quoted id>`` with ``rdf:type urn:kg:label:<L>``
        per label and ``urn:kg:p:<k>`` per property (a list as a ``urn:kg:json`` literal); an edge
        is a node ``urn:kg:e:<n>`` of type ``urn:kg:label:_Edge`` with ``_from``, ``_to``, ``_type``
        and its properties; ``_seq`` keeps store order. A register node, which carries ``reg_id``
        and no ``id``, is named ``reg:<label>:<reg_id>`` as the rdflib adapter names it. What one
        adapter exports another imports and answers the same (tools/check_round_trip.py)."""
        raise NotImplementedError

    def import_turtle(self, text: str) -> None:
        """Replace what this instance holds with the graph ``text`` holds, in the form
        ``export_turtle`` writes. The store's constraints stay as ``apply_constraints`` left them."""
        raise NotImplementedError

    # ---- what the page shows about the store
    def describe(self) -> dict:
        """uri, browser URL and the like: what the page's store card says."""
        return {"store": self.name}

    def saved_queries(self) -> list[dict]:
        """The adapter's own saved queries for its console, if it has one."""
        return []

    def console_query(self, text: str) -> list[dict]:
        """Run one statement of a saved query as the console would and return its rows;
        only an adapter with a console has one (demo/tools/check_saved_queries.py)."""
        raise NotImplementedError(f"the {self.name} store has no console")


class ReadOnly:
    """A read handle on an adapter (task-0141.02): the port's reads go through, any other operation is
    refused with StoreReadOnly before it reaches the adapter, and closing it publishes nothing."""

    def __init__(self, inner: Store):
        self._inner = inner
        self.name, self.instance, self.access = inner.name, getattr(inner, "instance", ""), "read"

    def __getattr__(self, attr):
        if attr in READS:
            fn = getattr(self._inner, attr)
            check = getattr(self._inner, "_after_read", None)
            if check is None or not callable(fn):
                return fn

            def pinned(*a, **kw):
                out = fn(*a, **kw)
                check()   # the generation this handle pinned is still the published one, or StoreChanged
                return out
            return pinned
        raise StoreReadOnly(f"a read handle on the {self._inner.name} store only reads: {attr} is not a read of the store port")

    def __enter__(self) -> "ReadOnly":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def commit(self) -> None:
        raise StoreReadOnly(f"a read handle on the {self._inner.name} store publishes nothing")

    def abort(self) -> None:
        pass

    def close(self) -> None:
        self._inner.close()


ACCESS = ("read", "write")

READ_ATTEMPTS = 3

# task-0141.06's settings: name -> (default, least, most); a value outside, or not a number, is refused
SETTINGS = {
    "KG_STORE_READ_ATTEMPTS": (3, 1, 10),            # times a logical read is run on a fresh handle
    "KG_NEO4J_LEASE_SECONDS": (60.0, 1.0, 3600.0),   # a Neo4j writer's lease, renewed every third of it
    "KG_NEO4J_LOCK_TIMEOUT": (60.0, 0.0, 86400.0),   # how long a Neo4j writer waits for another's lease
    "KG_NEO4J_READ_WAIT": (10.0, 0.0, 600.0),        # how long a Neo4j reader waits out a publication in flight
    "KG_LOAD_MEMORY_MARGIN": (0.25, 0.0, 4.0),       # task-0176: the forecast's margin over the measured envelope
}


def setting(name: str, fallback=None):
    """The value of one of ``SETTINGS`` from the environment, else ``fallback``, else its default;
    ValueError naming the variable for anything that is not a number within its bounds."""
    default, lo, hi = SETTINGS[name]
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default if fallback is None else type(default)(fallback)
    try:
        v = int(raw) if isinstance(default, int) else float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a {'whole ' if isinstance(default, int) else ''}number, not {raw!r}") from None
    if not (lo <= v <= hi) or v != v:
        raise ValueError(f"{name} must be between {lo:g} and {hi:g}, not {raw!r}")
    return v


class ScratchUnavailable(RuntimeError):
    """No scratch store can be made here: the rdflib adapter cannot be imported."""


def scratch_store(instance: str = ""):
    """A write handle of this process's own (task-0183): an rdflib graph in memory, never a file and never
    the store ``KG_STORE`` names, so a load into it publishes nothing anyone else reads. The gate's report
    is the same on either adapter (``tools/check_round_trip.py --chain``), so what is computed on it is
    what the shared store would give after the same load."""
    try:
        from store_rdflib import RdflibStore
    except ImportError as e:
        raise ScratchUnavailable(f"a private store needs rdflib ({e}); install the harness's pins: "
                                 "pip install -r demo/requirements.txt") from e
    return RdflibStore(path="", instance=instance, access="write")


def read_attempts() -> int:
    return setting("KG_STORE_READ_ATTEMPTS")


def read(fn, kind: str | None = None, *, attempts: int | None = None, **kw: Any):
    """One logical read: ``fn(handle)`` on a read handle, run again on a fresh handle when a publication
    lands during it (``StoreChanged``), at most ``attempts`` times (``KG_STORE_READ_ATTEMPTS``, 3); the
    last StoreChanged propagates, so a caller answers "busy, retry" rather than a mixed result."""
    n = attempts or read_attempts()
    for i in range(max(1, n)):
        with open_store(kind, access="read", **kw) as st:
            try:
                return fn(st)
            except StoreChanged:
                if i == n - 1:
                    raise


def open_store(kind: str | None = None, *, access: str, **kw: Any):
    """The adapter ``kind`` (default ``KG_STORE``, else neo4j) opened for ``access``: ``read``, a
    ReadOnly view on a snapshot, or ``write``, the adapter itself as one unit of work."""
    if access not in ACCESS:
        raise ValueError(f"access is read or write, not {access!r}")
    kind = (kind or os.environ.get("KG_STORE") or "neo4j").lower()
    if kind == "neo4j":
        from store_neo4j import Neo4jStore
        st = Neo4jStore(access=access, **kw)
    elif kind == "rdflib":
        from store_rdflib import RdflibStore
        st = RdflibStore(access=access, **kw)
    else:
        raise ValueError(f"unknown store {kind!r}; KG_STORE names an adapter: neo4j, rdflib")
    return ReadOnly(st) if access == "read" else st
