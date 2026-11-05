"""The store port: the operations the harness and the page need from a store, and nothing else.

Not a generic graph API. Each method is one thing the loader, the rules, the gate, the census,
the SHACL projection or the register projection does; the first adapter (``store_neo4j.py``)
keeps the Cypher, the Browser link and the saved queries. ``open_store()`` picks the adapter
from ``KG_STORE`` (``neo4j`` is the default) and returns it ready to use as a context manager:

    with open_store() as st:
        st.wipe()
        ...

Status and provenance are the store's; content stays in git. Every adapter must give the
same answers for the same calls, which the deterministic comparator checks on the CargoQuote
record. The evaluation's §11 names when another store would be preferred; with this port that
is an adapter, not a rewrite.
"""
from __future__ import annotations

import os
from typing import Any


def part_list(parts: dict[str, str]) -> list[str]:
    """A directory artefact's file digests as a Version's ``part_sha256``: ``"<sha256>  <rel>"`` by path."""
    return [f"{sha}  {rel}" for rel, sha in sorted(parts.items())]


def part_rows(artefact: str, version: str, entries) -> list[dict]:
    """``part_sha256`` entries back as {artefact, version, part, sha256} rows."""
    return [{"artefact": artefact, "version": version, "part": e[66:], "sha256": e[:64]} for e in entries or []]


def by_id(rows: list[dict]) -> list[dict]:
    """``rows`` in one order on every adapter: by ``id``, a row without one (an OPTIONAL MATCH that met
    nothing) last. A store's collect() answers in its own traversal order, which a reload can move;
    what the gate prints and compares (the bundle, its report) must not."""
    return sorted(rows, key=lambda r: (r.get("id") is None, str(r.get("id"))))


def by_content(rows: list[dict]) -> list[dict]:
    """``rows`` without an id (a fragment) in one order on every adapter: by their fields."""
    import json
    return sorted(rows, key=lambda r: json.dumps(r, sort_keys=True, default=str))


class Store:
    """The port. An adapter subclasses it and implements every method; the base raises."""

    name = "abstract"
    instance = ""          # the instance id the adapter may stamp on its writes (a shared store later)

    # ---- lifecycle
    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        pass

    def wipe(self) -> None:
        """Delete everything this instance holds. The free Neo4j edition serves one database."""
        raise NotImplementedError

    def apply_constraints(self) -> list[dict]:
        """Try each constraint family; return {type, cypher, accepted, message} per constraint:
        what the edition refuses is itself a measurement (D1)."""
        raise NotImplementedError

    # ---- loading: agents, activities, artefacts, fragments, entities, assertions
    def ensure_agents(self, tool_name: str, version: str, human: dict, llm: dict) -> None:
        raise NotImplementedError

    def ensure_person(self, aid: str, handle: str) -> None:
        """A person who gave knowledge (task-0009; ieam-register decision 0008): an Agent of kind
        human named by an opaque handle, never a name."""
        raise NotImplementedError

    def create_activity(self, aid: str, kind: str, at: str, tool: str, note: str, agent_id: str) -> None:
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

    def verify_authored(self, at: str, scope: str, agent_id: str) -> int:
        raise NotImplementedError

    def approve_verified(self, at: str, record: str, agent_id: str) -> int:
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

    def register_derived(self, did: str, kind: str, sha: str, assertion_ids: list[str]) -> None:
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
        raise NotImplementedError

    def conflict_gaps(self) -> list[dict]:
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

    def suspect_derived(self) -> list[dict]:
        raise NotImplementedError

    def all_derived(self) -> list[dict]:
        """Every derived output with its suspect flag."""
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

    # ---- the census and the page
    def census(self) -> dict:
        raise NotImplementedError

    def extraction_activities(self) -> list[str]:
        """The extraction activity ids, oldest first: which scenario is loaded."""
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


def open_store(kind: str | None = None, **kw: Any) -> Store:
    kind = (kind or os.environ.get("KG_STORE") or "neo4j").lower()
    if kind == "neo4j":
        from store_neo4j import Neo4jStore
        return Neo4jStore(**kw)
    if kind == "rdflib":
        from store_rdflib import RdflibStore
        return RdflibStore(**kw)
    raise ValueError(f"unknown store {kind!r}; KG_STORE names an adapter: neo4j, rdflib")
