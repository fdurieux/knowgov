"""The gate and the three-valued answer as a read-only MCP server (task-0056).

    python harness/mcp_server.py                      # stdio, for an agent that starts the server itself
    python harness/mcp_server.py --http [--host H] [--port P]   # Streamable HTTP at http://H:P/mcp

The question an agent asks is "may I build on this?". Sixteen tools answer it, all read-only:

    store_status          what the store holds: the subject, the scenario loaded, the tasks and the
                          keys the subject asks the three-valued question of
    gate_verdict          the gate's report for a task, or for a key set of the agent's own, exactly
                          as ``gate_cli.py --no-load -f json`` prints it for the same store
    three_valued_answer   asserted, documented absent or unknown for one key, with each statement's
                          provenance: its source document and fragments, who made it, its
                          verifications, approvals and gaps; and the key's invalidated statements,
                          each naming what supersedes it (``superseded_by``, task-0071)
    evidence_bundle       the evidence bundle the governed arm reads (``gate.render_bundle``) for a task or
                          a key set: the verdict, the policy, every key's statements with evidence,
                          verifications, approvals and gaps, the invalidated statements and what
                          supersedes them, the lapsed reviews, the pre-load verdicts behind the keys,
                          the suspect derived outputs, and the documents the task names verbatim
                          (task-0080)
    register_impact       what retiring a register node touches: the register's own walk from it, what it
                          reaches and who owns each, its children listed and not walked (or, with
                          children, walked as the register's decision 0014 does, task-0118), and the
                          register-map keys it lands on, each with its level, stale statements and
                          suspect derived outputs as gate_verdict reports them for a task class
                          (task-0111; ``task``, and with children the keys resting only on a
                          withdrawn descendant, flagged ``withdrawn``, task-0120)
    proposal_impact       a proposed addition (new nodes, links, reused nodes, proposed exceptions) read
                          against the register as if approved, without approving it: placement findings,
                          the deterministic link candidates D1-D5, every coverage rule the register's checker defines (C1-C4) before and after, the
                          reach from every reused node before and after, what each new node rests on, the
                          reused nodes' keys as register_impact reads them, the new nodes left unmapped and
                          the approvals per owning unit; every overlay element hypothetical, nothing stored
                          (task-0130, task-0131, doc-0017)
    scenario_runs         the subject's scenarios with what the record holds (deterministic; the arms with
                          n and model; the extra sources) and the runs per mode, newest first, from each
                          run folder's run.json or inferred; the scenario the store holds and when it was
                          loaded; the run under way, if any. Replay is the record shown, never a run
                          (task-0128, doc-0016 item 1)
    scenario_result       what the page's Replay shows for one source scenario_runs lists (the record, an
                          extra source, a run): the D6 gate, the keys' levels, the arms' decisions and
                          suite, read from its files, never from the store (task-0129)
    register_nodes        the register listed, filtered by taxonomy, kind, state, owning unit and parent, with
                          the total; or one node with its lineage, its ancestors by parent to the root and its
                          children, an annotation and never a walk; the register's files, no store (task-0142)
    key_nodes             the register nodes a knowledge key concerns: its register_map.toml rows with their
                          nodes, owner, anchor and note; files only (task-0143)
    code_path             a code path's application from the instance's code_map.toml, the keys its header
                          cites and its trace ledger entry, each leg read or unchecked; files only (task-0143)
    document_links        the register links whose evidence cites a document, with the nodes at both ends and
                          their owners, as the Browser's register-cites joins them; files only (task-0143)
    held_keys             every key the held scenario holds, with its count by status, its gate level and the
                          task classes requiring it, the required keys it lacks (task-0144)
    derived_outputs       the derived outputs built on a key, any state, or one output, with each statement it
                          used read live, stale, superseded or rejected (task-0144)
    document_statements   the statements a document yields, by version, and the outputs built on them (task-0144)
    subject_check         a proposed subject (subject.toml, register_map.toml, scenarios.toml, the documents'
                          text) checked by tools/check_subject.py's own functions against the served register,
                          in a temporary directory removed after the call: its subject-check report; nothing
                          stored, the yield in a child process, the call bounded (task-0146, doc-0018)

Two prompts, text only (task-0148, ``harness/wizard.py``): ``new_subject <id> <task>`` and ``add_artefact
<subject> [file]``, the subject wizard of doc-0018 as a procedure the client runs with its own file tools on
a branch, ending in a pull request; each is the instance skill's text verbatim, with the never-list and the
stop condition. ``prompts/list`` and ``prompts/get`` in both eras; the prompts capability is the reader's
only (knowgov-runs declares none).

While a run folder of the server's subject reads running with a live heartbeat (run.json, within
``runs_index.STALE_S`` of ``review.now()``), gate_verdict, three_valued_answer and evidence_bundle
refuse and name the run: on Neo4j a run wipes the store and loads it in steps (doc-0016 F2);
register_impact and proposal_impact refuse too where they read key levels from the store, and answer
from the register alone as before (task-0137).

The server never loads, wipes or writes: it reads the store the page or a run left (``KG_STORE``;
for rdflib the Turtle file ``KG_RDFLIB_FILE``, read and never written back), through a view that
refuses every operation of the store port that is not a read. Writes to the record stay pull
requests. A baseline is ``none`` or ``record`` only: a path would let a client read files.

The code leg's files are configuration, read once at start (task-0143): ``--instance`` or ``KG_INSTANCE``, the
instance whose ``code_map.toml`` and code ``code_path`` reads, and ``--ledger`` or ``KG_LEDGER``, the trace ledger
(``trace.py register`` writes it); unset, that leg reads unchecked.

One ``as_of`` per process (task-0100, doc-0014 C2). ``KG_AS_OF`` (or ``--as-of``: YYYY-MM-DD, ``record`` or
``today``, default ``today``) is read once, at start, and resolved once: ``gate_verdict`` and
``evidence_bundle`` read review currency on that date unless a call names its own, and ``store_status``
reports it. A call's ``today`` or ``record`` is resolved once per process too, so a session that runs
past midnight never reads two days. The date comes from ``review.today()``: under ``KG_CLOCK=pinned``
a start with no ``KG_TODAY`` and a relative date is refused.

Over HTTP it binds 127.0.0.1 unless ``--host``/``KG_MCP_HOST`` says otherwise; a bind that is not
a loopback address needs ``KG_MCP_TOKEN``, which every request then carries as
``Authorization: Bearer <token>``. Every request's Host must name an authority the server answers for
(the loopback names on its port, or the bind address, plus ``KG_MCP_AUTHORITIES``), else 421, and an
``Origin``, when sent, must be one of its own (``http://`` each authority, plus ``KG_MCP_ORIGINS``,
such as the MCP Inspector's ``http://localhost:6274``), else 403; each is checked on its own and
apart from the token, so a page that rebinds a name to this machine reaches nothing
(``harness/http_boundary.py``, task-0141.03).

Standard library only, like the page and the gate command: MCP's JSON-RPC 2.0 messages, newline
delimited on stdio, one JSON response per POST over HTTP.

Dual-era (task-0079). A request whose ``_meta`` carries ``io.modelcontextprotocol/protocolVersion``
is served statelessly per the 2026-07-28 revision: ``server/discover`` answers the supported
versions, the capabilities, the instructions and the server's identity; every result carries
``resultType`` and the ``serverInfo`` stamp; an unsupported version is ``-32022`` with the versions
supported; ``server/discover`` and ``tools/list`` carry the caching hints; over HTTP the ``MCP-Protocol-Version``, ``Mcp-Method`` and ``Mcp-Name`` headers must match
the body (``-32020``) and an error is a 400, or a 404 for an unknown method. A request without that
``_meta`` is the handshake era, unchanged: ``initialize`` negotiates one of the legacy versions.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_identity  # noqa: E402  (task-0227's identity)

# Which knowgov this process runs (task-0231): {version, commit, describe}, each None when unknown, read
# once at start from this copy's own files, as the page's /api/subjects reads it. store_status and
# knowgov-runs' run_options carry it; serverInfo.version is its VERSION.
KNOWGOV = build_identity.identity()
SERVER = {"name": "knowgov", "title": "knowgov gate (read-only)", "version": KNOWGOV["version"] or "unknown"}
PROTOCOL_VERSIONS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]   # the handshake era, newest first
MODERN_VERSIONS = ["2026-07-28"]                                               # stateless, per-request _meta
SUPPORTED_VERSIONS = MODERN_VERSIONS + PROTOCOL_VERSIONS
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
META_SERVER = "io.modelcontextprotocol/serverInfo"
HEADER_MISMATCH, UNSUPPORTED_VERSION = -32020, -32022
CAPABILITIES = {"tools": {"listChanged": False}}
# The caching hints the revision requires on server/discover and tools/list: both are fixed for the
# life of the process; private, because a bearer token may stand in front of them (a gate answer,
# tools/call, is never cacheable and carries none).
CACHE = {"ttlMs": 3_600_000, "cacheScope": "private"}
DEFAULT_HOST, DEFAULT_PORT = "127.0.0.1", 8765

# The store port's reads this server may call (harness/store.py); anything else raises.
READS = frozenset({"key_evidence", "declared_gaps_for_key", "conflict_gaps", "stale_on_keys", "suspect_derived",
                   "extraction_activities", "extraction_times", "assertions_on_key", "census", "preload_verdicts",
                   "held_keys", "derived_outputs", "artefact_assertions", "held", "act_findings",
                   "lint_gaps", "attestations"})   # task-0144; held, task-0195; acts, task-0199; lint gaps, task-0216; attestations, task-0221

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

INSTRUCTIONS = ("knowgov answers whether an assistant may build on the knowledge a task needs. Call gate_verdict "
                "before generating code or a document from the organisation's knowledge: BLOCKED means do not build, "
                "QUALIFIED means build only with every key below verified stated as an assumption, PROCEED means the "
                "required keys are verified or approved. Call evidence_bundle for the knowledge itself, with its "
                "evidence, as the governed arm reads it; both read review currency on the server's one date unless "
                "you pass as_of, and store_status names it. Call three_valued_answer for one key: 'unknown' is not "
                "'documented_absent'. Call register_impact before retiring or changing a register node: it names what "
                "the register's walk reaches, who owns it and the keys that rest on it, read under the task class you name "
                "(task, as gate_verdict's; codegen by default), those resting only on a withdrawn descendant flagged withdrawn. Call register_nodes to find where to start without an id (the register listed by taxonomy, kind, state, owning unit or parent) and, with node, what a node sits under: its ancestors to the root and its children, named and never walked. Call proposal_impact before a proposed product, capability or journey is approved: it reads the proposal as if approved, every element hypothetical, and names the gaps, the candidates (authored or inferred, never more than proposed), what it touches and who must approve; it approves nothing. Call scenario_runs to see which scenarios have been run, in which mode and with what verdict, and whether a run is loading the store: while one is, the gate refuses. Call scenario_result for what a record or run showed, read from its files: it is not what the store holds. Call subject_check after every change to a subject you are scaffolding: pass the proposed subject.toml, register_map.toml, scenarios.toml and every document's text; a refused manifest is exit_code 1, and a did-you-mean names a key the documents yield. Never take a task's keys from what the documents yield. The prompts new_subject and add_artefact walk an assistant through scaffolding a subject on a branch; nothing is written through this server. The chain composes from named hops, never one walk both ways. Down, from a capability to its knowledge: register_impact walk=realisers, then evidence_bundle keys=... for the keys it lands on, then derived_outputs key=... for what was built on a key. Up, from a code file to the business: code_path (its application and cited keys), key_nodes for a cited key's nodes, register_impact walk=dependants from the application or those nodes (children true for an application whose modules carry the links), then register_nodes node=... for a capability's ancestors. From a document: document_links names the register links citing it and their nodes. In the store: held_keys lists every key the held scenario holds with its level, including those no task class requires; document_statements names the statements a document yields and the outputs built on them; derived_outputs derived=... the statements behind one output. Intake, from a proposed initiative to the board a tracker holds: proposal_impact proposal=... on the overlay; its slices, one per journey step (per delivering process for a product no journey concerns), each overlay element in one slice or a named remainder, are the story map's backbone; each slice's keys are the task class's keys on its thread, and with a scenario held its keys.gate is gate_verdict keys=... on them; slices.task_keys names the class's keys on no slice (task-0252); all under one task class and one as_of. knowgov writes no work item and ranks nothing: no label, score or estimate; the tracker writes the items, each citing register ids. A check that a backlog covers the slices (K3) is parked to the pilot, not offered. code_path, key_nodes and document_links read files only; a leg that reads unchecked was not read, it is not empty. A status is the repository's; you may not upgrade it.  Every tool but list_subjects takes subject, the id of a subject under KG_SUBJECTS (list_subjects names them, never a path); none named is this server's own. A store-backed tool (its _meta io.knowgov/storeBacked true) answers only for the subject and scenario the store holds and otherwise names the start_run that would load it; a files-only tool answers for any subject. This server only reads.")

TOOLS = [
    {"name": "store_status", "title": "What the store holds",
     "description": "The subject, the scenario the store holds (null when none is loaded, or when the one held is another "
                    "subject's: held_by_other_subject names it then, and every scenario-reading tool refuses), the store kind, the task "
                    "classes with their required keys (and the rationale a class states), the keys the subject asks the three-valued question of, and "
                    "the date gate_verdict and evidence_bundle read on when a call names none (as_of, from as_of_from).",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
     "annotations": READ_ONLY},
    {"name": "gate_verdict", "title": "May I build on this?",
     "description": "The gate's verdict (PROCEED, QUALIFIED or BLOCKED), its findings on the severity ladder and the "
                    "blocking keys, for a task class or for a key set of your own, on the scenario the store holds. "
                    "The report is the one `gate_cli.py --no-load -f json` prints; exit_code 1 means do not proceed.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold; refused if it holds another (default: whatever it holds)"},
         "task": {"type": "string", "description": "the task class whose required keys are resolved (default: codegen); with keys, its block levels and bar apply"},
         "keys": {"type": "array", "items": {"type": "string"}, "minItems": 1, "description": "resolve these entity|attribute keys instead of the task's"},
         "fail_on": {"type": "string", "enum": ["blocker", "critical", "major", "minor", "info"], "description": "the severity at or above which exit_code is 1 (default: blocker)"},
         "baseline": {"type": "string", "enum": ["none", "record"], "description": "record: exit_code 1 only on a regression against the subject's record (codegen only)"},
         "as_of": {"type": "string", "description": "the date review currency is read on (decision-0005): the server's date (default: KG_AS_OF, else today, read once at start, as store_status reports it), today, record (the subject's pinned record date) or YYYY-MM-DD; a review past its key's review months reads validated"}}},
     "annotations": READ_ONLY},
    {"name": "three_valued_answer", "title": "Is it asserted, documented absent, or unknown?",
     "description": "For one key: 'asserted' with its values, 'documented_absent' when the documents say there is none, "
                    "or 'unknown' when no statement exists (not the same as absent). Each statement comes with its "
                    "provenance: status, basis, source document, fragments, author, verifications, approvals and gaps. "
                    "'invalidated' lists the key's statements a source change ended, each with superseded_by: the "
                    "verified or approved statements that replace it, or none, when the old value no longer holds and nothing does.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["key"], "properties": {
         "key": {"type": "string", "description": "an entity|attribute key, as store_status lists them"},
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold (default: whatever it holds)"}}},
     "annotations": READ_ONLY},
]


TOOLS.append(
    {"name": "evidence_bundle", "title": "What may I build on, and on what evidence?",
     "description": "The evidence bundle the governed arm reads, as text: the gate's verdict and why, the policy, each "
                    "required key's level, flags, declared gaps and live statements (value, basis, status, source, "
                    "evidence fragments, verifications, approvals, gaps, a lapsed review), the conflicts, the statements "
                    "a source change invalidated with what supersedes them, the documents behind the keys whose "
                    "pre-load check is unchecked or flawed, the derived outputs marked suspect, and the documents the "
                    "task names as needed verbatim. Put it in your context before building; the statuses are the "
                    "repository's, not yours to upgrade.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold (default: whatever it holds)"},
         "task": {"type": "string", "description": "the task class whose required keys are resolved and whose verbatim documents are served (default: codegen)"},
         "keys": {"type": "array", "items": {"type": "string"}, "minItems": 1, "description": "resolve these entity|attribute keys instead of the task's; the task's block levels, bar and verbatim documents apply"},
         "verbatim": {"type": "boolean", "description": "include the documents the task names as needed verbatim (default: true)"},
         "as_of": {"type": "string", "description": "the date review currency is read on: the server's date (default, the one gate_verdict reads), record (the subject's pinned record date, as the arms read it), today or YYYY-MM-DD"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "register_impact", "title": "What does retiring this register node touch?",
     "description": "The register's own impact walk from one node of the organisation's register (approved links only; "
                    "a deprecated or retired node is not expanded; a withdrawn edge is listed with live false and not "
                    "followed; a node's parent is never climbed): the register's tag and commit, the node (kind, name, "
                    "state, owner, parent), its children with their states (listed, not walked, unless children is true), "
                    "every edge, what the walk reached by id prefix with each node's owning unit, and the register-map keys "
                    "whose rows name the start, a walked descendant or a reached node (every mapped key the change reaches, "
                    "whatever a task class requires: the reach; proposal_impact's slices keep to the class's keys, task-0252), each with its owner, anchor and the nodes it came through (via); "
                    "with children, then the keys resting only on a withdrawn descendant, flagged withdrawn. With a "
                    "scenario held, each key carries its gate level, its stale statements, the suspect derived outputs "
                    "that used them and its findings, as gate_verdict reports that key set for the task class on the same as_of.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["node"], "properties": {
         "node": {"type": "string", "pattern": r"^[A-Z]+-\d{4,}$", "description": "a register id, as the register's files name it"},
         "walk": {"type": "string", "enum": ["dependants", "realisers"], "description": "dependants: what rests on the node (default); realisers: what implements a capability, where the register offers that walk"},
         "children": {"type": "boolean", "description": "also walk from every descendant by parent, recursively, as the register's decision 0014 does: an approved one is walked by its own kind's row, any other is listed withdrawn and not walked from; what is reached excludes the start and its descendants; a key whose row names only a withdrawn descendant is listed last, flagged withdrawn true, and walked no further (default: false, children listed and not walked)"},
         "task": {"type": "string", "description": "the task class whose block levels, bar and route each landed key is read under, as gate_verdict's task (default: codegen); a declared class, never keys"},
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold; refused if it holds another (default: whatever it holds; with none held, the keys carry no level)"},
         "as_of": {"type": "string", "description": "the date review currency is read on: the server's date (default, the one gate_verdict reads), today, record or YYYY-MM-DD"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "proposal_impact", "title": "What would this proposed addition touch, and what does it lack?",
     "description": "A proposed addition to the organisation's register read as if approved, without approving it "
                    "(doc-0017): the proposal is an overlay of new nodes (a provisional id, kind, name, parent, owner, an "
                    "optional source), links (type, source, target, rationale), the reused register nodes (as_is or "
                    "changed) and proposed exceptions, read by the register's own checker and walks. The report: placement "
                    "findings (a forbidden synonym is D5; a node with no source is in no tool yet); deterministic candidates "
                    "D1 (a register id the proposal names, authored), D2 (an external id matched through a node's source or "
                    "the newest landed export, authored), D3 (the same name as an approved node of the same kind, its links "
                    "offered, inferred; 'same step as JRN-...'), D4 (a pool of processes for an unsupported step, none "
                    "chosen), each with status proposed only; every coverage rule the register's checker defines (C1-C4 at ieam-register v0.2.13) before and after with denominators and the "
                    "new gaps; the reach from every reused node before and after; what each new node rests on; the slice "
                    "map, one vertical slice per journey step (per delivering process for a product no journey concerns) "
                    "by the register's thread walk, every overlay element in one slice or a named remainder, with the "
                    "denominator, facts only; each "
                    "reused node's keys as register_impact reads them (with a scenario held, their levels under the task "
                    "class on the same as_of); the new nodes left unmapped (never unknown); the approvals per owning unit. "
                    "With scope, a journey, step or product id, the slices are that scope's own and the proposal may be left "
                    "out: the approved register read alone (task-0191). Each slice then lists its keys: the task class's keys among "
                    "the register-map rows register_impact lands on its thread (never every key a change reaches, which is "
                    "register_impact's), with the class's key count as denominator; the class's keys on no slice are "
                    "slices.task_keys, so each is in a slice or there (task-0252); and with a scenario held their levels and the "
                    "cells: levels by count, unread, the lowest level, unknown (absent), gaps, lapses, the keys behind an edge "
                    "the thread does not follow, and the owner handoffs along it. Facts only, never a score. "
                    "Every overlay element is hypothetical; nothing is written to the register or the store.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "proposal": {"type": "object", "description": "the overlay: nodes [{id, kind, name, parent, owner, source}], links "
                      "[{type, source, target, rationale, owner}], reused [{id, mode: as_is|changed}], exceptions "
                      "[{rule, scope, expires, rationale}], title; ids are provisional, a link end is a register id or a proposed "
                      "node's (required unless scope is given)"},
         "scope": {"type": "string", "description": "an approved journey, step, touchpoint or product id: its slices only, each "
                   "with its keys; with no proposal, the approved register read alone (task-0191)"},
         "children": {"type": "boolean", "description": "walk every approved descendant by parent too, as register_impact's children (default: false)"},
         "task": {"type": "string", "description": "the task class whose keys each slice reads (its [tasks.<class>] keys among the rows on its thread), and the class the reused nodes' keys are read under, as register_impact's (default: codegen)"},
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold; refused if it holds another (default: whatever it holds; with none held, the keys carry no level)"},
         "as_of": {"type": "string", "description": "the date exceptions, reviews and key levels are read on: the server's date (default), today, record or YYYY-MM-DD"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "scenario_runs", "title": "Which scenarios have been run, and what did they show?",
     "description": "The subject's scenarios, each with its title and card line; what the record holds for it (record: the "
                    "record and every extra source the subject declares, each with deterministic results or not, the D6 gate "
                    "verdict and the arms with n, models, decisions and suite); and its runs newest first, from the run "
                    "folder's run.json (mode, n, row, model, effort, as_of, started, finished, status, exit_code, by, the "
                    "gate verdict of its results) or, for a folder from before run.json, inferred (inferred true: status, "
                    "start and initiator unknown). Replay is the record shown, never a run: nothing records it. Also the "
                    "scenario the store holds (version, stage, loaded_at) and run_in_progress, the run loading the store "
                    "now, while gate_verdict, three_valued_answer and evidence_bundle refuse.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "scenario": {"type": "string", "description": "one of the subject's scenarios (default: every one, in the subject's order)"},
         "limit": {"type": "integer", "minimum": 1, "description": "at most this many runs per scenario, newest first (default: all)"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "scenario_result", "title": "What did this record or run show?",
     "description": "What the page's Replay shows for one source of a scenario, as data, read from that source's files and "
                    "never from the store, so it is not what the store holds now: the D6 gate (verdict, why, blocked, below "
                    "verified, flagged, conflicts, stale, suspect derived, lapsed), the date it read reviews on, every "
                    "required key's level, each arm's runs (decision, code, flagged, suite, model) and, for a scenario "
                    "with a change, the verdicts before and after it. The source is an id scenario_runs lists: record, an "
                    "extra source, or a run's source.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["scenario", "source"], "properties": {
         "scenario": {"type": "string", "description": "one of the subject's scenarios"},
         "source": {"type": "string", "description": "a source id as scenario_runs lists it: record, an extra source's id, or a run's source (demo-runs/...)"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "register_nodes", "title": "Which register nodes are there, and what does this one sit under?",
     "description": "The organisation's register listed, read from its files and never from the store: every node sorted by "
                    "id with its taxonomy, kind, name, state, owner and parent, filtered by taxonomy, kind, state, owner (a unit "
                    "owns a node by its owner field or an approved owns link: 'what does ORG-x own' is this listing, since owns "
                    "is never walked) and parent (null: the nodes with no parent), with the total, a limit and an offset. With "
                    "node, that node with its owning unit and its lineage: every ancestor by parent, nearest first, up to the "
                    "root, and its children with their states. Lineage is an annotation, never a reached node: no relationship "
                    "is walked; for what rests on or implements a node, call register_impact.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "node": {"type": "string", "pattern": r"^[A-Z]+-\d{4,}$", "description": "one register id: that node and its lineage; no filter applies"},
         "taxonomy": {"type": "string", "description": "a taxonomy of the register's metamodel, such as capabilities or applications"},
         "kind": {"type": "string", "description": "a kind of the register's metamodel, such as capability or module"},
         "state": {"type": "string", "description": "a lifecycle state, such as approved or proposed"},
         "owner": {"type": "string", "pattern": r"^[A-Z]+-\d{4,}$", "description": "a unit of the register's organisation, such as ORG-0001"},
         "parent": {"type": ["string", "null"], "description": "the nodes whose parent is this id; null for the nodes with no parent"},
         "limit": {"type": "integer", "minimum": 1, "description": "at most this many nodes (default 100, at most 1000); total counts them all"},
         "offset": {"type": "integer", "minimum": 0, "description": "skip this many matching nodes first (default 0)"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "key_nodes", "title": "Which register nodes does this knowledge key concern?",
     "description": "The rows of the subject's register_map.toml whose key is this one, read from files and never from the "
                    "store: each with the register nodes it names (taxonomy, kind, name, state, owner), the row's owner, "
                    "anchor and note, and every node named. A key the subject knows with no row reads mapped false; a key "
                    "it does not know is refused. One hop, node to key read backwards: from the nodes, register_impact "
                    "walk=dependants climbs to what rests on them.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["key"], "properties": {
         "key": {"type": "string", "description": "an entity|attribute key, as store_status, register_impact and code_path name them"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "code_path", "title": "Which application is this code file, which keys does it cite, and what built it?",
     "description": "For a code path relative to the root of the instance's code_map.toml (the server's KG_INSTANCE or "
                    "--instance), read from files and never from the store: the application or module the map assigns "
                    "and that register node; the keys the file's header cites (knowgov-keys:), each flagged unknown when "
                    "the subject does not know it; and the trace ledger's entry for the path (the server's KG_LEDGER or "
                    "--ledger: derived id, keys used, statements, commit, digest, and the file's digest now, with drift). "
                    "Each leg is read or unchecked with its reason (no instance or ledger configured, no code map, one "
                    "that does not hold, a missing or malformed ledger, a language the citation does not cover); "
                    "unchecked is never empty. A path outside the code map's root is refused. From the application, "
                    "register_impact walk=dependants (children true for an application whose modules carry the links) "
                    "climbs to the processes and capabilities.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["path"], "properties": {
         "path": {"type": "string", "description": "a '/'-separated path relative to the code map's root, as trace.py names a file"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "document_links", "title": "Which register links cite this document?",
     "description": "The register links whose evidence cites a document of the subject's export manifest, read from the "
                    "register's files and never from the store: each link's id, type, state and owner, the evidence string "
                    "and its #anchor, and the nodes at both ends with their owning units (target null for a link to an "
                    "external id); the document's digest in the manifest. What the Browser's register-cites query joins. A "
                    "document the manifest does not hold is refused. One hop, document to register: from the nodes, "
                    "register_impact climbs or descends.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["document"], "properties": {
         "document": {"type": "string", "description": "a document path as the subject's export manifest names it under [files]; the subject's evidence prefix and an #anchor may be given"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "subject_check", "title": "Would this proposed subject load, and do its keys match its documents?",
     "description": "A proposed subject checked before anything is written or loaded (doc-0018 candidate 3): the call "
                    "carries subject.toml, register_map.toml, scenarios.toml and the documents' text, and the answer is "
                    "tools/check_subject.py's report (schema subject-check): the manifest's tables and fields against what "
                    "the loader reads, a scenario for every task, key syntax, the register map's nodes in the served "
                    "register and each row's owner among their owners, and what each document yields with a did-you-mean "
                    "for a required key no document yields. exit_code 1 is a refused manifest; warnings and notes are for "
                    "reading. The yield is shown beside the keys, never as their source. The files live in a temporary "
                    "directory for the call and are removed; nothing is stored or written. A document is named by its path "
                    "relative to the subject root, exactly as the manifest's [[artefact]] path names it (../../artefacts/"
                    "<kind>/<file> at most two levels up); a document the call does not carry reads as missing.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["subject_toml"], "properties": {
         "subject_toml": {"type": "string", "description": "the proposed subject.toml's text"},
         "register_map_toml": {"type": "string", "description": "the proposed register_map.toml's text (written where the manifest's [register] map names, register_map.toml by default)"},
         "scenarios_toml": {"type": "string", "description": "the proposed scenarios.toml's text; a subject with a task needs one scenario"},
         "plants_toml": {"type": "string", "description": "plants.toml's text, if the subject's scenarios add artefacts"},
         "documents": {"type": "object", "additionalProperties": {"type": "string"},
                       "description": "{path relative to the subject root: the document's text}, every document the manifest names"},
         "root": {"type": "string", "description": "the label the report's root carries, such as the subject root's path in your checkout (default: proposed)"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "held_keys", "title": "Which keys does the held scenario hold, and at what level?",
     "description": "Every key a statement of the held scenario names, read from the store: each with its statement "
                    "count by status, its level as the gate reads it under the task class named (codegen by default) on "
                    "the server's date, the task classes whose required keys include it (required_by; empty for a key no "
                    "class asks for, which store_status never shows) and whether the subject's register map places it; "
                    "and the required keys the store holds no statement on. The levels are gate_verdict's for that key set.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "task": {"type": "string", "description": "the task class whose block levels and bar the levels are read under (default: codegen)"},
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold; refused if it holds another"},
         "as_of": {"type": "string", "description": "the date review currency is read on: the server's date (default), today, record or YYYY-MM-DD"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "derived_outputs", "title": "What was built on this key, or behind this output?",
     "description": "Derived outputs read from the store, any state. With key: every output that used a statement on "
                    "the key; with derived: that one output. Each with its kind, digest, suspect flag, the keys behind it "
                    "and every statement it used, each read live, stale (invalidated, nothing settled replaces it), "
                    "superseded (with the verified or approved successors superseded_by names) or rejected. Name "
                    "exactly one of key and derived.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "key": {"type": "string", "description": "an entity|attribute key: the outputs built on it"},
         "derived": {"type": "string", "description": "a derived output id, as the gate's suspect findings and code_path's ledger entry name it"},
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold; refused if it holds another"}}},
     "annotations": READ_ONLY})


TOOLS.append(
    {"name": "document_statements", "title": "What does this document yield, and what was built on it?",
     "description": "The statements a document yields in the held scenario, read from the store: those whose source "
                    "is the document or that rest on one of its fragments (a directory artefact's files by its path "
                    "ending in '/'), each with its key, value, status, basis, version and the document's fragments, "
                    "and the derived outputs that used it; the versions held, and with version one of them only. A "
                    "document no statement comes from is refused.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["document"], "properties": {
         "document": {"type": "string", "description": "an artefact path, as a statement's source (artefact) names it"},
         "version": {"type": "string", "description": "one of the document's held versions, such as v1 (default: every one)"},
         "scenario": {"type": "string", "description": "the scenario you expect the store to hold; refused if it holds another"}}},
     "annotations": READ_ONLY})

# task-0157 (B7, decision-0013 with A1): one reader for every subject under KG_SUBJECTS. Every tool but
# list_subjects takes an optional subject id; a call naming another subject than the process's own is answered by a child process
# for that subject (harness/mcp_child.py). A tool is store-backed or reads files only, and says which in its
# _meta: a store-backed one answers only for the subject and scenario the shared store holds, and refuses
# for any other with the held subject and scenario and the run to start; a files-only one answers for any.
STORE_BACKED = frozenset({"store_status", "gate_verdict", "three_valued_answer", "evidence_bundle", "register_impact",
                          "proposal_impact", "held_keys", "derived_outputs", "document_statements"})
META_STORE = "io.knowgov/storeBacked"
SUBJECT_ARG = {"type": "string", "description": "the id of a subject under KG_SUBJECTS, as list_subjects names them, never a "
               "path (default: this server's own subject, KG_SUBJECT)"}
TOOLS.append(
    {"name": "list_subjects", "title": "Which subjects can I ask about, and what does the store hold?",
     "description": "Every subject this server answers for, by id (the subjects under KG_SUBJECTS; the default, KG_SUBJECT, "
                    "first), each with its scenarios and the scenario the shared store holds for it, or none; and which tools "
                    "are store-backed (they answer only for the held subject and scenario) and which read files only (they "
                    "answer for any subject). Name a subject on any tool with its subject argument.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
     "annotations": READ_ONLY})
# task-0172: every tool's structuredContent is pinned by a schema under harness/schemas/, its description names
# it, and tests/test_mcp_output_schemas.py validates each tool's output against it with harness/schema_check.py
OUTPUT_SCHEMAS = {"store_status": "store-status", "gate_verdict": "gate-report", "three_valued_answer": "three-valued-answer",
                  "evidence_bundle": "evidence-bundle", "register_impact": "register-impact", "proposal_impact": "proposal-impact",
                  "scenario_runs": "scenario-runs", "scenario_result": "scenario-result", "register_nodes": "register-nodes",
                  "key_nodes": "key-nodes", "code_path": "code-path", "document_links": "document-links",
                  "subject_check": "subject-check", "held_keys": "held-keys", "derived_outputs": "derived-outputs",
                  "document_statements": "document-statements", "list_subjects": "list-subjects"}


def output_note(schema: str) -> str:
    return f" Output (structuredContent): harness/schemas/{schema}.schema.json."


for _t in TOOLS:
    if _t["name"] != "list_subjects":
        _t["inputSchema"]["properties"]["subject"] = SUBJECT_ARG
    _t["_meta"] = {META_STORE: _t["name"] in STORE_BACKED}
    _t["description"] += output_note(OUTPUT_SCHEMAS[_t["name"]])


class ToolError(Exception):
    """A tool could not answer: returned to the client as a result with isError, never a crash."""


class ReadOnlyStore:
    """The MCP server's view: of the port's reads, only the ones its tools need, over a read handle
    (``open_store(access="read")``), which never publishes (task-0141.02)."""

    def __init__(self, inner):
        self._inner = inner
        self.name = inner.name

    def __getattr__(self, attr):
        if attr in READS:
            return getattr(self._inner, attr)
        raise PermissionError(f"the MCP server only reads: {attr} is not a read of the store port")

    def release(self) -> None:
        self._inner.close()


def open_read_only(open_store=None) -> ReadOnlyStore:
    from subject import SUBJECT
    from store import ReadOnly
    if open_store is None:
        from store import open_store
    st = open_store(instance=SUBJECT.id, access="read")
    return ReadOnlyStore(st if isinstance(st, ReadOnly) else ReadOnly(st))


def _held_any(st) -> str | None:
    """The scenario the store holds, whichever subject's: one store serves every subject."""
    h = st.held()
    return h["scenario"] if h else None


def _held(st) -> str | None:
    """The held scenario when the held load is the server's subject's, by the subject the load recorded
    (task-0195; task-0126), else None."""
    import held as held_state
    from subject import SUBJECT
    return held_state.scenario_for(st.held(), SUBJECT.id)


def _foreign(st) -> str | None:
    """The held scenario when the held load is not the server's subject's, or its subject is unknown: no
    tool reads it (task-0195; task-0126)."""
    import held as held_state
    from subject import SUBJECT
    h = st.held()
    return h["scenario"] if held_state.foreign(h, SUBJECT.id) else None


def _start_run(sid: str, scenarios) -> str:
    """The next step a store-backed refusal names (decision-0013, A1): the run that would load the subject."""
    first = next(iter(scenarios), None)
    return (f"to read {sid}, start a run of one of its scenarios {list(scenarios)} through knowgov-runs start_run "
            f'{{"subject": "{sid}", "scenario": "{first}", "mode": "deterministic"}} or the page; this server never loads')


def _check_scenario(st, scenario: str | None) -> str:
    from subject import SUBJECT
    import subject_ids
    import held as held_state
    h = st.held()
    foreign = h["scenario"] if held_state.foreign(h, SUBJECT.id) else None
    if foreign is not None:
        who = held_state.owner(h)
        if who is None:   # a store loaded before task-0195: whose load it is cannot be told, so nobody reads it
            raise ToolError(f"{held_state.refusal(h, SUBJECT.id)}: {_start_run(SUBJECT.id, SUBJECT.order)}")
        owners = [who]
        whose = (owners[0] if len(owners) == 1 else f"one of {owners}" if owners else "a subject not under KG_SUBJECTS")
        raise ToolError(f"the store holds {foreign}, a scenario of another subject ({whose}), not of {SUBJECT.id} (which declares "
                        f"{SUBJECT.order}); a store-backed tool reads the held subject and scenario only: "
                        f"{_start_run(SUBJECT.id, SUBJECT.order)}")
    held = _held(st)
    if held is None:
        raise ToolError(f"the store holds no scenario; {_start_run(SUBJECT.id, SUBJECT.order)}")
    if scenario and scenario != held:
        raise ToolError(f"the store holds {held}, not {scenario!r}")
    return held


def _stage(scenario: str, version: str | None) -> int:
    """2 when the store holds the scenario's stage-2 version (the change applied), else 1."""
    from subject import SUBJECT
    cfg2 = SUBJECT.scenario(scenario).get("stage2")
    return 2 if cfg2 and version == cfg2.get("version", "v2") else 1   # change.version_of, without its load imports


class Tools:
    """The tools over a store opener; each call opens the store, reads and releases it. ``as_of`` is
    the session's date (default: ``KG_AS_OF``, else ``today``), read here and resolved on first use
    or by ``session_as_of()`` at start, then held for the life of the process (task-0100)."""

    def __init__(self, opener=open_read_only, as_of: str | None = None, runs: Path | None = None):
        import runs_index
        self.opener = opener
        self.runs = Path(runs) if runs is not None else runs_index.runs_dir()   # the page's run folders (KG_DEMO_RUNS)
        self.as_of_from = as_of or os.environ.get("KG_AS_OF") or "today"   # the one read of KG_AS_OF
        self._dates: dict[str, str] = {}
        self._lock = threading.Lock()

    def _resolve(self, value: str) -> str:
        """``value`` as an ISO date; ``today`` and ``record`` resolved once per process."""
        import cadence
        if value not in ("today", "record"):
            return cadence.as_of(value).isoformat()
        with self._lock:
            if value not in self._dates:
                self._dates[value] = cadence.as_of(value).isoformat()
            return self._dates[value]

    def session_as_of(self) -> str:
        """The date a call that names none reads on."""
        return self._resolve(self.as_of_from)

    def _as_of(self, args: dict) -> str:
        value = args.get("as_of")
        if value is not None and not isinstance(value, str):
            raise ToolError("as_of: a string, YYYY-MM-DD, today or record")
        try:
            return self._resolve(value) if value else self.session_as_of()
        except ValueError as e:
            raise ToolError(f"as_of: {e}") from e

    def _run_in_progress(self) -> dict | None:
        """The subject's live run (runs_index), or None; the clock is read only when a run.json reads running."""
        import review
        import runs_index
        from subject import SUBJECT
        try:
            return runs_index.run_in_progress(SUBJECT.id, self.runs)
        except review.WallClock as e:
            raise ToolError(f"a run.json reads running and its heartbeat cannot be read against the clock: {e}") from e

    def _not_mid_run(self) -> None:
        """Refuse while a run of this subject is loading the store (doc-0016 F2): a read then sees part of a graph."""
        run = self._run_in_progress()
        if run is not None:
            raise ToolError(f"a run is loading the store: {run.get('subject')}/{run.get('id')} ({run.get('scenario')}, "
                            f"{run.get('mode')}, by {run.get('by')}, started {run.get('started')}, heartbeat "
                            f"{run.get('heartbeat_at') or run.get('started')}); call again when it has ended "
                            "(scenario_runs shows it)")

    def _held_detail(self, st) -> dict | None:
        """The held scenario of this subject with its version, stage and the time it was loaded, else None."""
        import held as held_state
        from subject import SUBJECT
        h = st.held()   # task-0195: the subject, scenario, version and time the load recorded
        held = held_state.scenario_for(h, SUBJECT.id)
        if held is None:
            return None
        return {"scenario": held, "version": h["version"], "stage": _stage(held, h["version"]),
                "loaded_at": h["loaded_at"]}

    def _with_store(self, fn):
        """``fn`` on one read handle, one published generation (task-0141.06): when a publication lands
        during the call the call runs again on a fresh handle, at most ``KG_STORE_READ_ATTEMPTS`` times (3)."""
        from store import StoreChanged, read_attempts
        try:
            attempts = read_attempts()
        except ValueError as e:
            raise ToolError(str(e)) from e
        for attempt in range(attempts):
            try:
                st = self.opener()
            except Exception as e:  # noqa: BLE001
                raise ToolError(f"the store cannot be opened: {type(e).__name__}: {e}") from e
            try:
                return fn(st)
            except StoreChanged as e:
                if attempt == attempts - 1:
                    raise ToolError(f"the store was republished during each of {attempts} reads; call again: {e}") from e
            except (ToolError, PermissionError):
                raise
            except Exception as e:  # noqa: BLE001
                raise ToolError(f"the store did not answer: {type(e).__name__}: {e}") from e
            finally:
                try:
                    st.release()
                except Exception:  # noqa: BLE001
                    pass

    def list_subjects(self, args: dict) -> dict:
        """Every subject this reader answers for, the shared store's held scenario and whose it is, and the
        tools' store-backed class (task-0157, decision-0013 with A1). A store that cannot be read, or a run
        loading it, leaves held null with the reason; the subjects are listed all the same."""
        import subject_ids
        from subject import SUBJECT
        listed = subject_ids.subjects()
        import held as held_state
        h, why = None, None
        try:
            self._not_mid_run()
            h = self._with_store(lambda st: st.held())
        except ToolError as e:
            why = str(e)
        held = h["scenario"] if h else None
        who = held_state.owner(h)   # task-0195: the subject the load recorded, never the scenario id's declarers
        owners = [who] if who else []
        return {"default": SUBJECT.id,
                "store": {"held_scenario": held, "held_by": owners, "unavailable": why,
                          **({"held_subject_unknown": held_state.LEGACY} if h and who is None else {})},
                "subjects": [{"id": x["id"], "name": x["name"], "default": x["id"] == SUBJECT.id, "scenarios": x["scenarios"],
                              "held": held if x["id"] in owners else None} for x in listed],
                "store_backed": sorted(t["name"] for t in TOOLS if t["_meta"][META_STORE]),
                "files_only": sorted(t["name"] for t in TOOLS if not t["_meta"][META_STORE])}

    def store_status(self, args: dict) -> dict:
        from subject import SUBJECT
        from tasks import TASKS

        try:
            on = self.session_as_of()
        except ValueError as e:
            raise ToolError(f"as_of: {e}") from e

        def go(st):
            held = self._held_detail(st)
            return {"subject": SUBJECT.id, "store": st.name, "scenario": _held(st),
                    "loaded_at": held["loaded_at"] if held else None,
                    "held_by_other_subject": _foreign(st),
                    "as_of": on, "as_of_from": self.as_of_from,
                    "scenarios": list(SUBJECT.order),
                    "tasks": {n: {"keys": t["keys"], "block_levels": sorted(t["block_levels"]),
                                  "max_unverified_share": t["max_unverified_share"],
                                  **({"require_approved": True} if t.get("require_approved") else {}),
                                  **({"rationale": t["rationale"]} if t["rationale"] else {})} for n, t in TASKS.items()},
                    "three_valued_keys": list(SUBJECT.three_valued), "knowgov": dict(KNOWGOV)}
        return self._with_store(go)

    def gate_verdict(self, args: dict) -> dict:
        import gate_cli
        from subject import SUBJECT
        from tasks import TASKS
        task = args.get("task") or "codegen"
        if task not in TASKS:
            raise ToolError(f"{SUBJECT.id}: no task {task!r}; the subject declares {sorted(TASKS) or 'none'}")
        keys = args.get("keys")
        if keys is not None and (not isinstance(keys, list) or not keys or not all(isinstance(k, str) and k for k in keys)):
            raise ToolError("keys must be a non-empty list of entity|attribute strings")
        threshold = args.get("fail_on") or "blocker"
        if threshold not in gate_cli.SEVERITIES:
            raise ToolError(f"fail_on must be one of {gate_cli.SEVERITIES}")
        which = args.get("baseline") or "none"
        if which not in ("none", "record"):
            raise ToolError("baseline must be none or record; a file path is not served")
        if keys is not None and which == "record":
            raise ToolError("the record is a baseline for a task class, not for a key set of your own")
        on = self._as_of(args)
        spec = dict(TASKS[task])
        name = task
        if keys is not None:
            spec["keys"] = list(dict.fromkeys(keys))
            name = "keys"

        self._not_mid_run()

        def go(st):
            scenario = _check_scenario(st, args.get("scenario"))
            try:
                base = gate_cli._baseline(which, SUBJECT, scenario, task)
            except gate_cli.CannotRun as e:
                raise ToolError(str(e)) from e
            return gate_cli.evaluate(st, subject=SUBJECT.id, scenario=scenario, task=name, spec=spec,
                                     threshold=threshold, baseline=base, loaded=False,
                                     version=gate_cli.held_version(st), as_of=on, route_task=task)
        return self._with_store(go)

    def evidence_bundle(self, args: dict) -> dict:
        """The bundle as harness/run.py hands it to the governed arm: ``render_bundle`` over the gate's
        result, with the policy and the task's verbatim documents from the kit of the version the
        store holds. ``as_of`` defaults to the session's date, as ``gate_verdict``'s does; the arms'
        date is ``record``, named explicitly (task-0100)."""
        import arms
        import gate_cli
        from gate import render_bundle, resolve_spec
        from kitio import kit_for, verbatim_documents
        from subject import SUBJECT
        from tasks import TASKS
        task = args.get("task") or "codegen"
        if task not in TASKS:
            raise ToolError(f"{SUBJECT.id}: no task {task!r}; the subject declares {sorted(TASKS) or 'none'}")
        keys = args.get("keys")
        if keys is not None and (not isinstance(keys, list) or not keys or not all(isinstance(k, str) and k for k in keys)):
            raise ToolError("keys must be a non-empty list of entity|attribute strings")
        with_verbatim = args.get("verbatim", True)
        if not isinstance(with_verbatim, bool):
            raise ToolError("verbatim must be true or false")
        on = self._as_of(args)
        spec = dict(TASKS[task])
        name = task
        if keys is not None:
            spec["keys"] = list(dict.fromkeys(keys))
            name = "keys"

        self._not_mid_run()

        def go(st):
            scenario = _check_scenario(st, args.get("scenario"))
            res = resolve_spec(st, name, spec, on)
            version = gate_cli.held_version(st)
            verbatim = None
            if with_verbatim:
                verbatim = verbatim_documents(kit_for(scenario, _stage(scenario, version)), task)
            return {"subject": SUBJECT.id, "store": st.name, "scenario": scenario, "version": version, "task": name,
                    "as_of": res["as_of"], "verdict": res["verdict"], "why": res["why"],
                    "assertion_ids": sorted({a["id"] for v in res["keys"].values() for a in v["assertions"]}),
                    "verbatim": sorted(verbatim or {}),
                    "bundle": render_bundle(res, arms.policy(), verbatim)}
        return self._with_store(go)

    def register_impact(self, args: dict) -> dict:
        """The register's walk from ``node`` (``register_impact.walk``), the map rows it lands on, and,
        with a scenario held, each landed key as the gate reports that key set under ``task``'s block
        levels, bar and route (task-0111; ``task`` and the withdrawn flag, task-0120). The
        register is read from ``KG_REGISTER``; the store only through the port's reads."""
        import gate_cli
        import register_impact as ri
        from subject import SUBJECT
        from tasks import TASKS
        which = args.get("walk") or "dependants"
        task = args.get("task")
        if task is None:   # gate_verdict's default class: its block levels, bar and route
            task = "codegen" if "codegen" in TASKS else next(iter(TASKS), None)
        elif task not in TASKS:   # "keys" names a key set, not a class (task-0120)
            raise ToolError(f"{SUBJECT.id}: no task {task!r}; the subject declares {sorted(TASKS) or 'none'}")
        try:
            out = ri.walk(args.get("node"), which, children=args.get("children", False))
        except ri.ImpactError as e:
            raise ToolError(str(e)) from e
        out.pop("reached_ids")
        reached = [x["id"] for xs in out["reached"].values() for x in xs]
        walked = [c["id"] for c in out["children"] if c["walked"]]
        withdrawn = [c["id"] for c in out["children"] if c.get("withdrawn")]
        keys = ri.landed_rows(SUBJECT.register_map(), out["node"]["id"], reached, walked, withdrawn)
        head = {"subject": SUBJECT.id, "store": None, "scenario": None, "as_of": None}

        def go(st):
            head["store"] = st.name
            if args.get("scenario") is None and _held_any(st) is None:
                return {**head, **out, "keys": keys, "gate": None}
            scenario = _check_scenario(st, args.get("scenario"))
            on = self._as_of(args)
            head.update(scenario=scenario, as_of=on)
            if not keys or task is None:
                return {**head, **out, "keys": keys, "gate": None}
            self._not_mid_run()   # the levels are the store's: refused while a run loads it (task-0137)
            spec = dict(TASKS[task], keys=[k["key"] for k in keys])
            rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=scenario, task="keys", spec=spec, threshold="blocker",
                                    baseline=None, loaded=False, version=gate_cli.held_version(st), as_of=on, route_task=task)
            return {**head, **out, "keys": ri.with_levels(keys, rep),
                    "gate": {"task": task, "verdict": rep["verdict"], "why": rep["why"], "exit_code": rep["exit_code"]}}
        if args.get("scenario") is None:
            try:   # the register answers without a store; only a named scenario needs one
                return self._with_store(go)
            except ToolError as e:
                if not str(e).startswith("the store cannot be opened"):
                    raise
                return {**head, **out, "keys": keys, "gate": None, "store_unavailable": str(e)}
        return self._with_store(go)

    def register_nodes(self, args: dict) -> dict:
        """The register listed under filters, or one node's lineage (``register_nodes.report``, task-0142):
        the register's files only, read from ``KG_REGISTER``; no store is opened."""
        import register_nodes as rn
        try:
            return rn.report(args)
        except rn.NodesError as e:
            raise ToolError(str(e)) from e

    trace_cfg: dict | None = None   # the code leg's instance and ledger (upward.config), set once at start by main

    def key_nodes(self, args: dict) -> dict:
        """The register-map rows on a key with their register nodes (``upward.key_nodes``, task-0143); no store."""
        import upward
        try:
            return upward.key_nodes(args.get("key"))
        except upward.UpwardError as e:
            raise ToolError(str(e)) from e

    def document_links(self, args: dict) -> dict:
        """The register links citing a document (``upward.document_links``, task-0143); the register's files only."""
        import upward
        try:
            return upward.document_links(args.get("document"))
        except upward.UpwardError as e:
            raise ToolError(str(e)) from e

    def code_path(self, args: dict) -> dict:
        """A code path's application, cited keys and ledger entry (``upward.code_path``, task-0143); files only."""
        import upward
        with self._lock:
            if self.trace_cfg is None:
                self.trace_cfg = upward.config()
        try:
            return upward.code_path(args.get("path"), self.trace_cfg)
        except upward.UpwardError as e:
            raise ToolError(str(e)) from e

    def proposal_impact(self, args: dict) -> dict:
        """A proposal read as if approved (``proposal_impact.evaluate``, task-0130), and with a scenario
        held each reused node's keys at their levels, as ``register_impact`` reads them for that node,
        ``task`` and as_of. The register is read from ``KG_REGISTER``; the store only through the port's
        reads; nothing is written to either."""
        import proposal_impact as pi
        from tasks import TASKS
        from subject import SUBJECT
        task = args.get("task")
        if task is None:
            task = "codegen" if "codegen" in TASKS else next(iter(TASKS), None)
        elif task not in TASKS:
            raise ToolError(f"{SUBJECT.id}: no task {task!r}; the subject declares {sorted(TASKS) or 'none'}")
        on = self._as_of(args)
        try:
            if args.get("proposal") is None and args.get("scope") is None:
                raise ToolError("give a proposal, a scope (a journey, step or product id), or both")
            out = pi.evaluate(args.get("proposal"), today=pi._date(on, "as_of"), children=args.get("children", False),
                              scope=args.get("scope"), task=task)
        except (pi.ProposalError, pi.ri.ImpactError) as e:
            raise ToolError(f"the proposal cannot be read: {e}") from e

        def go(st):
            if args.get("scenario") is None and _held_any(st) is None:
                return out   # nothing held: the register answers alone, as register_impact's
            _check_scenario(st, args.get("scenario"))   # another subject's scenario is refused (task-0126)
            if task is None:
                return out
            self._not_mid_run()   # the reused nodes' levels are the store's: refused while a run loads it (task-0137)
            try:
                return pi.with_levels(out, st, task=task, as_of=on, scenario=args.get("scenario"))
            except pi.ProposalError as e:
                raise ToolError(str(e)) from e
        if args.get("scenario") is None:
            try:   # the register answers without a store; only a named scenario needs one
                return self._with_store(go)
            except ToolError as e:
                if not str(e).startswith("the store cannot be opened"):
                    raise
                out["keys"]["store_unavailable"] = str(e)
                return out
        return self._with_store(go)

    def scenario_runs(self, args: dict) -> dict:
        """The subject's scenarios with the record's sources and the runs (``runs_index.scenario_runs``), the
        held scenario when the store answers, and the run under way (task-0128). No path is taken: the roots
        are the subject's record and ``KG_DEMO_RUNS/<subject id>``."""
        import runs_index
        from subject import SUBJECT
        scenario, limit = args.get("scenario"), args.get("limit")
        if scenario is not None and scenario not in SUBJECT.scenarios:
            raise ToolError(f"{SUBJECT.id}: no scenario {scenario!r}; the subject declares {SUBJECT.order}")
        if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit < 1):
            raise ToolError("limit must be a whole number, 1 or more")
        out = {"subject": SUBJECT.id,
               "replay": "Replay is the record shown, not a run; nothing records it. record says what it holds.",
               "scenarios": runs_index.scenario_runs(SUBJECT, self.runs, scenario, limit),
               "run_in_progress": None, "held": None, "held_by_other_subject": None}
        try:
            out["run_in_progress"] = self._run_in_progress()
        except ToolError as e:
            out["run_in_progress_unknown"] = str(e)
        if out["run_in_progress"] is not None:
            out["store_skipped"] = "a run is loading the store; what it holds is read once the run has ended"
            return out

        def go(st):
            out.update(held=self._held_detail(st), held_by_other_subject=_foreign(st))
            return out
        try:
            return self._with_store(go)
        except ToolError as e:   # the record and the runs answer without a store
            out["store_unavailable"] = str(e)
            return out

    def scenario_result(self, args: dict) -> dict:
        """``runs_index.result`` for a source ``scenario_runs`` lists; the store is never opened (task-0129)."""
        import runs_index
        from subject import SUBJECT
        scenario, source = args.get("scenario"), args.get("source")
        if scenario not in SUBJECT.scenarios:
            raise ToolError(f"{SUBJECT.id}: no scenario {scenario!r}; the subject declares {SUBJECT.order}")
        if not isinstance(source, str) or not source:
            raise ToolError("source is required: an id scenario_runs lists (record, an extra source, a run's source)")
        out = runs_index.result(SUBJECT, self.runs, scenario, source)
        if out is None:
            listed = [s["id"] for s in runs_index.sources_for(SUBJECT, scenario, self.runs)]
            raise ToolError(f"{scenario}: no source {source!r} with results; scenario_runs lists {listed}")
        return {"subject": SUBJECT.id, "reads": "files: this source's results as they were written, not the store; "
                                                 "store_status and gate_verdict read what the store holds now", **out}

    def subject_check(self, args: dict) -> dict:
        """``check_subject.check`` on the files the call carries, in a temporary root removed after the call
        (``subject_check.evaluate``, task-0146); the register is ``KG_REGISTER``'s, the store never opened."""
        import subject_check
        try:
            return subject_check.evaluate(args)
        except subject_check.SubjectCheckError as e:
            raise ToolError(f"the proposed subject cannot be checked: {e}") from e

    def _store_read(self, args: dict, fn):
        """One read handle for the call (``_with_store``): the held scenario this subject's, never mid-run."""
        import store_reads
        self._not_mid_run()

        def go(st):
            scenario = _check_scenario(st, args.get("scenario"))
            try:
                return fn(st, scenario)
            except store_reads.ReadError as e:
                raise ToolError(str(e)) from e
        return self._with_store(go)

    def held_keys(self, args: dict) -> dict:
        """Every held key with its level, as the gate reads it (``store_reads.held_keys``, task-0144)."""
        import store_reads
        from subject import SUBJECT
        from tasks import TASKS
        task = args.get("task")
        if task is None:
            task = "codegen" if "codegen" in TASKS else next(iter(TASKS), None)
        elif task not in TASKS:
            raise ToolError(f"{SUBJECT.id}: no task {task!r}; the subject declares {sorted(TASKS) or 'none'}")
        on = self._as_of(args)
        return self._store_read(args, lambda st, sc: store_reads.held_keys(st, subject=SUBJECT.id, scenario=sc, task=task, as_of=on))

    def derived_outputs(self, args: dict) -> dict:
        """The outputs built on a key, or one output's statements (``store_reads.derived_outputs``, task-0144)."""
        import store_reads
        from subject import SUBJECT
        return self._store_read(args, lambda st, sc: store_reads.derived_outputs(
            st, subject=SUBJECT.id, scenario=sc, key=args.get("key"), derived=args.get("derived")))

    def document_statements(self, args: dict) -> dict:
        """The statements a document yields and the outputs built on them (``store_reads``, task-0144)."""
        import store_reads
        from subject import SUBJECT
        return self._store_read(args, lambda st, sc: store_reads.document_statements(
            st, subject=SUBJECT.id, scenario=sc, document=args.get("document"), version=args.get("version")))

    def three_valued_answer(self, args: dict) -> dict:
        import cadence
        import dates   # task-0262: the session's date, parsed as every date is
        from gate import THREE_VALUED_STATUSES, invalidated_on_key, three_valued
        from subject import SUBJECT
        key = args.get("key")
        if not isinstance(key, str) or not key:
            raise ToolError("key is required, an entity|attribute string")

        self._not_mid_run()

        def go(st):
            scenario = _check_scenario(st, args.get("scenario"))
            ans = three_valued(st, key)
            prov = {r["id"]: r for r in st.key_evidence(key, THREE_VALUED_STATUSES)}
            statements = [prov.get(r["id"], r) for r in ans.get("assertions", [])]
            on = self.session_as_of()
            for r in statements:   # task-0198 (doc-0030 M8): currency as of the session's date, as gate_verdict reads it
                gone = cadence.lapse(r, key, dates.parse(on))   # resolved once, by _resolve
                if gone:
                    r["status"], r["lapsed"] = gone["to"], gone
            out = {"subject": SUBJECT.id, "store": st.name, "scenario": scenario, "key": key, "answer": ans["answer"],
                   "as_of": on, "statements": statements, "invalidated": invalidated_on_key(st, key)}
            if "why" in ans:
                out["why"] = ans["why"]
            if ans.get("disputed"):   # task-0201 (doc-0030 M4): the statements the documents disagree on
                out["disputed"] = ans["disputed"]
            return out
        return self._with_store(go)


def _result(id_, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _error(id_, code: int, message: str, data=None) -> dict:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}


def _id_ok(id_) -> bool:
    """A JSON-RPC 2.0 id: a string, a whole number or null (task-0272: never an array, an object, a
    boolean or a fraction, which a client could not match a response to)."""
    return id_ is None or isinstance(id_, str) or (isinstance(id_, int) and not isinstance(id_, bool))


def malformed(msg) -> dict | None:
    """The error for a message that is not a JSON-RPC 2.0 request this server can answer, else None:
    -32600 for a non-object, a wrong ``jsonrpc`` or an id that is not a string, a whole number or null;
    -32602 for a ``_meta`` protocol version that is not a string, which would otherwise read as the
    handshake era and skip that era's checks (task-0272)."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        id_ = msg.get("id") if isinstance(msg, dict) else None
        return _error(id_ if _id_ok(id_) else None, -32600, "not a JSON-RPC 2.0 message")
    if "id" in msg and not _id_ok(msg["id"]):
        return _error(None, -32600, "the id must be a string, a whole number or null")
    params = msg.get("params")
    meta = params.get("_meta") if isinstance(params, dict) else None
    if isinstance(meta, dict) and META_VERSION in meta and not isinstance(meta[META_VERSION], str):
        return _error(msg.get("id"), -32602, f"_meta {META_VERSION} must be a string")
    return None


def modern_version(msg) -> str | None:
    """The protocol version a 2026-07-28-era request declares in its ``_meta``, else None (the
    handshake era)."""
    params = msg.get("params") if isinstance(msg, dict) else None
    meta = params.get("_meta") if isinstance(params, dict) else None
    v = meta.get(META_VERSION) if isinstance(meta, dict) else None
    return v if isinstance(v, str) else None


def http_status(resp: dict | None, modern: bool) -> int:
    """The HTTP status of a response: a handshake-era error stays 200, as before; a modern one is a
    400 (version, malformed request, header mismatch) or a 404 (no such method)."""
    if resp is None:
        return 202
    err = resp.get("error")
    if not modern or not err:
        return 200
    return 404 if err["code"] == -32601 else 400


def decode_header(value: str) -> str:
    """A header value as the 2026-07-28 binding encodes it: ``=?base64?...?=`` for what is not plain ASCII."""
    if value.startswith("=?base64?") and value.endswith("?="):
        import base64
        try:
            return base64.b64decode(value[9:-2], validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return "\x00invalid"   # never equal to a body value
    return value


def header_mismatch(msg: dict, headers) -> str | None:
    """Why a modern request's HTTP headers do not match its body, else None."""
    version = modern_version(msg)
    got = headers.get("MCP-Protocol-Version")
    if got is None:
        return "the MCP-Protocol-Version header is missing"
    if got != version:
        return f"MCP-Protocol-Version header {got!r} does not match the body's {version!r}"
    if headers.get("Mcp-Method") != msg.get("method"):
        return f"Mcp-Method header {headers.get('Mcp-Method')!r} does not match the body's {msg.get('method')!r}"
    if msg.get("method") in ("tools/call", "prompts/get"):   # the revision names the tool or the prompt
        name = headers.get("Mcp-Name")
        if name is None:
            return "the Mcp-Name header is missing"
        if decode_header(name) != (msg.get("params") or {}).get("name"):
            return f"Mcp-Name header {name!r} does not match the body's {'tool' if msg.get('method') == 'tools/call' else 'prompt'} name"
    return None


class Server:
    """MCP's JSON-RPC methods; ``handle`` takes one decoded message and returns the response, or
    None for a notification or a response."""

    def __init__(self, tools=None, table: list[dict] | None = None, info: dict | None = None,
                 instructions: str | None = None, prompts=None, route="default"):
        """``tools`` answers each tool by name; ``table``, ``info`` and ``instructions`` are what the
        server lists and announces (this module's by default; knowgov-runs passes its own, task-0133).
        ``prompts`` lists and gives the prompts (``harness/wizard.py``'s, task-0148, for the reader's own
        table; none for a server that passes its own table unless it names them)."""
        self.tools = tools or Tools()
        self.table = TOOLS if table is None else table
        self.info = SERVER if info is None else info
        self.instructions = INSTRUCTIONS if instructions is None else instructions
        if prompts is None and table is None:
            import wizard
            prompts = wizard
        self.prompts = prompts
        self.capabilities = {**CAPABILITIES, **({"prompts": {"listChanged": False}} if prompts else {})}
        # a call naming another subject (task-0157): the reader's own table routes it to a child; a server with
        # its own table (knowgov-runs) or a child (route=None) answers it itself or not at all
        self.route = (route_to_child if table is None else None) if route == "default" else route
        self.max_response = max_response()   # task-0177: one tools/call result at most, refused whole above it

    def handle(self, msg) -> dict | None:
        """One message's response. Whatever escapes the dispatch is an internal error, -32603, never a raised
        exception that would end the stdio loop or drop the HTTP connection (task-0200, doc-0030 M6)."""
        try:
            return self._handle(msg)
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"mcp: internal error: {type(e).__name__}: {e}\n")
            id_ = msg.get("id") if isinstance(msg, dict) and isinstance(msg.get("id"), (str, int)) else None
            return _error(id_, -32603, f"internal error: {type(e).__name__}")

    def _handle(self, msg) -> dict | None:
        bad = malformed(msg)
        if bad:
            return bad
        if "method" not in msg:
            return None                      # a response to something we never send
        method, id_ = msg["method"], msg.get("id")
        if "id" not in msg:
            return None                      # a notification: notifications/initialized and the like
        params = msg.get("params") or {}
        if not isinstance(params, dict):
            return _error(id_, -32602, "params must be an object")
        if modern_version(msg) is not None:
            return self._modern(id_, method, params)
        if method == "server/discover":
            return _error(id_, -32602, f"server/discover needs _meta[{META_VERSION!r}] and _meta[{META_CAPABILITIES!r}]")
        if method == "initialize":
            asked = params.get("protocolVersion")
            version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
            return _result(id_, {"protocolVersion": version, "capabilities": self.capabilities,
                                 "serverInfo": self.info, "instructions": self.instructions})
        if method == "ping":
            return _result(id_, {})
        if method in ("tools/list", "tools/call"):
            return self._tools(id_, method, params)
        if method in ("prompts/list", "prompts/get") and self.prompts:
            return self._prompts(id_, method, params)
        return _error(id_, -32601, f"method not found: {method}")

    def _prompts(self, id_, method: str, params: dict, stamp: dict | None = None) -> dict:
        """prompts/list and prompts/get, either era (task-0148): text only, read-only by nature."""
        stamp = stamp or {}
        if method == "prompts/list":
            return _result(id_, {"prompts": self.prompts.listing(), **stamp, **(CACHE if stamp else {})})
        if not isinstance(params.get("name"), str):
            return _error(id_, -32602, "the prompt's name must be a string")
        try:
            got = self.prompts.get(params.get("name"), params.get("arguments"))
        except self.prompts.PromptError as e:
            return _error(id_, -32602, str(e))
        return _result(id_, {**got, **stamp})

    def _tools(self, id_, method: str, params: dict, stamp: dict | None = None) -> dict:
        """tools/list and tools/call, either era; ``stamp`` is what a modern result adds."""
        stamp = stamp or {}
        if method == "tools/list":
            return _result(id_, {"tools": self.table, **stamp, **(CACHE if stamp else {})})
        name, args = params.get("name"), params.get("arguments") or {}
        if not isinstance(name, str):   # M6: an unhashable name raised out of handle
            return _error(id_, -32602, "the tool's name must be a string")
        tool = next((t for t in self.table if t["name"] == name), None)
        if tool is None:
            return _error(id_, -32602, f"unknown tool {name!r}")
        if not isinstance(args, dict):
            return _error(id_, -32602, "arguments must be an object")
        schema = tool.get("inputSchema") or {}
        if schema.get("additionalProperties") is False:   # M5: the schema's own promise, kept for every tool
            unknown = sorted(set(args) - set(schema.get("properties") or {}))
            if unknown:
                return _error(id_, -32602, f"{name}: unknown argument(s) {', '.join(map(repr, unknown))}; "
                                          f"it takes {', '.join(sorted(schema.get('properties') or {})) or 'none'}")
        if self.route is not None and "subject" in args:
            import subject_ids
            try:
                entry = subject_ids.resolve(args.get("subject"))
            except subject_ids.UnknownSubject as e:
                return _result(id_, {"content": [{"type": "text", "text": str(e)}], "isError": True, **stamp})
            args = {k: v for k, v in args.items() if k != "subject"}
            if not subject_ids.is_own(entry):
                return _result(id_, {**self._capped(name, self.route(self.tools, entry, name, args)), **stamp})
        try:
            data = getattr(self.tools, name)(args)
        except (ToolError, PermissionError) as e:
            return _result(id_, {"content": [{"type": "text", "text": str(e)}], "isError": True, **stamp})
        except Exception as e:  # noqa: BLE001 - a tool that cannot answer is an error result, never a dropped connection
            import task_policy   # task-0242: a policy the gate cannot apply names its class and field, as gate_cli's exit 2
            if isinstance(e, task_policy.TaskPolicyError):
                return _result(id_, {"content": [{"type": "text", "text": f"{name}: the subject's task policy: {e}"}], "isError": True, **stamp})
            return _result(id_, {"content": [{"type": "text", "text": f"{name} could not answer: {type(e).__name__}: {e}"}],
                                 "isError": True, **stamp})
        return _result(id_, {**self._capped(name, {"content": [{"type": "text", "text": json.dumps(data, indent=1, ensure_ascii=False, default=str)}],
                                                   "structuredContent": data, "isError": False}), **stamp})

    def _capped(self, name: str, result: dict) -> dict:
        """``result`` when its JSON fits KG_MCP_MAX_RESPONSE, else an error result naming the setting
        (task-0177): never truncated, never a partial answer; the error result carries no structuredContent,
        as every error result does, so no output schema is bent to admit it."""
        size = len(json.dumps(result, ensure_ascii=False, default=str).encode("utf-8"))
        if size <= self.max_response:
            return result
        import http_boundary
        why = http_boundary.over_cap("KG_MCP_MAX_RESPONSE", size, self.max_response)
        sys.stderr.write(f"mcp: {name}: {why}\n")
        return {"content": [{"type": "text", "text": f"{name}: {why} (a limit, a narrower key set or verbatim false "
                                                     "narrows most calls)"}], "isError": True}

    def _modern(self, id_, method: str, params: dict) -> dict:
        """A self-contained 2026-07-28 request: nothing is read from an earlier one."""
        meta = params["_meta"]
        version = meta[META_VERSION]
        if version not in MODERN_VERSIONS:
            return _error(id_, UNSUPPORTED_VERSION, "Unsupported protocol version",
                          {"supported": SUPPORTED_VERSIONS, "requested": version})
        if not isinstance(meta.get(META_CAPABILITIES), dict):
            return _error(id_, -32602, f"_meta[{META_CAPABILITIES!r}] is required on every request")
        stamp = {"resultType": "complete", "_meta": {META_SERVER: {"name": self.info["name"], "version": self.info["version"]}}}
        if method == "server/discover":
            return _result(id_, {"supportedVersions": SUPPORTED_VERSIONS, "capabilities": self.capabilities,
                                 "instructions": self.instructions, **stamp, **CACHE})
        if method in ("tools/list", "tools/call"):
            return self._tools(id_, method, params, stamp)
        if method in ("prompts/list", "prompts/get") and self.prompts:
            return self._prompts(id_, method, params, stamp)
        return _error(id_, -32601, f"method not found: {method}")   # ping and initialize are not methods of this era

    def handle_text(self, text: str) -> dict | None:
        import http_boundary
        try:
            msg = http_boundary.parse_json(text)
        except http_boundary.NotJson as e:   # a nesting past the parser's depth included (task-0272)
            return _error(None, -32700, f"parse error: {e}")
        return self.handle(msg)

    def handle_http(self, text: str | bytes, headers) -> tuple[int, dict | None]:
        """One POST body and its headers: the HTTP status and the response. A modern request's
        headers must match its body before anything else is read. Bytes are read as strict UTF-8:
        invalid UTF-8 is a parse error, never a "replace" decode (task-0272)."""
        import http_boundary
        try:
            msg = http_boundary.parse_json(text)
        except http_boundary.NotJson as e:
            return 400, _error(None, -32700, f"parse error: {e}")
        bad = malformed(msg)
        if bad:
            return 400, bad
        modern = isinstance(msg, dict) and "id" in msg and "method" in msg and modern_version(msg) is not None
        if modern:
            why = header_mismatch(msg, headers)
            if why:
                return 400, _error(msg.get("id"), HEADER_MISMATCH, f"Header mismatch: {why}")
        resp = self.handle(msg)
        return http_status(resp, modern), resp


CHILD_TIMEOUT = 300.0   # seconds one call for another subject may take (KG_SUBJECT_CALL_TIMEOUT)


def route_to_child(tools, entry: dict, name: str, args: dict) -> dict:
    """A call for another subject (task-0157, design (a)): ``harness/mcp_child.py`` run with that subject's
    root as KG_SUBJECT, the session's date (its ``record`` read as that subject's record date) and the code
    leg's instance and ledger as this process read them at start; its result returned as it gave it."""
    import subprocess
    env = dict(os.environ, KG_SUBJECT=str(entry["root"]))
    env["KG_AS_OF"] = "record" if tools.as_of_from == "record" else tools.session_as_of()
    cfg = getattr(tools, "trace_cfg", None) or {}
    for var, key in (("KG_INSTANCE", "instance"), ("KG_LEDGER", "ledger")):
        if cfg.get(key):
            env[var] = cfg[key]
        else:
            env.pop(var, None)
    try:
        timeout = float(os.environ.get("KG_SUBJECT_CALL_TIMEOUT") or CHILD_TIMEOUT)
        p = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "mcp_child.py")],
                           input=json.dumps({"name": name, "arguments": args}), capture_output=True, text=True,
                           env=env, timeout=timeout)
        got = json.loads(p.stdout) if p.returncode == 0 and p.stdout.strip() else None
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        got, p = None, None
        why = f"{type(e).__name__}: {e}"
    else:
        why = (p.stderr or "").strip()[-400:] or f"exit {p.returncode}"
    if not isinstance(got, dict) or "error" in got:
        detail = (got or {}).get("error", {}).get("message") if isinstance(got, dict) else why
        return {"content": [{"type": "text", "text": f"{name} could not answer for {entry['id']}: {detail}"}], "isError": True}
    return got


def serve_stdio(server: Server, inp=None, out=None) -> None:
    inp, out = inp or sys.stdin, out or sys.stdout
    for line in inp:
        if not line.strip():
            continue
        resp = server.handle_text(line)
        if resp is not None:
            out.write(json.dumps(resp, ensure_ascii=False, default=str) + "\n")
            out.flush()


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def http_policy(host: str, port: int):
    """The authorities and origins the HTTP transport answers for (task-0141.03, harness/http_boundary.py):
    the loopback names on the bound port for a loopback or wildcard bind, else the bind address, plus
    KG_MCP_AUTHORITIES; origins ``http://`` each, plus KG_MCP_ORIGINS (the MCP Inspector's
    ``http://localhost:6274``, a TLS proxy's ``https://...``). Never from a request."""
    import http_boundary
    return http_boundary.build(host, [port], authorities=os.environ.get("KG_MCP_AUTHORITIES", ""),
                               origins=os.environ.get("KG_MCP_ORIGINS", ""))


def bind_check(host: str, token: str | None) -> str | None:
    """None when the bind may go ahead, else why it may not."""
    if not is_loopback(host) and not token:
        return f"{host} is not a loopback address: set KG_MCP_TOKEN so every request must carry it"
    return None


MCP_MAX_RESPONSE = 16 << 20   # task-0177: 25x the largest answer measured, evidence_bundle on J-F D4 (653 KB)


def max_response() -> int:
    """KG_MCP_MAX_RESPONSE: the largest tools/call result, in bytes of its JSON, on either transport and on
    knowgov-runs too (task-0177); refused at start outside 4 KiB to 1 GiB."""
    import http_boundary
    return http_boundary.response_cap("KG_MCP_MAX_RESPONSE", MCP_MAX_RESPONSE)


def mcp_limits():
    """The HTTP transport's bounds (task-0141.04): KG_MCP_MAX_BODY bytes (default 4 MiB: subject_check
    admits 1 MB of documents' text, more once escaped in JSON), KG_MCP_READ_TIMEOUT seconds for a
    request to arrive whole (10), KG_MCP_IDLE_TIMEOUT for one silent wait (5), KG_MCP_MAX_CONNECTIONS
    at once (32; more get 503), KG_MCP_MAX_RESPONSE bytes in one tools/call result (16 MiB, task-0177)."""
    import http_boundary
    return http_boundary.Limits.from_env("KG_MCP", max_body=4 << 20, max_response=MCP_MAX_RESPONSE)


def make_handler(server: Server, token: str | None):
    import http_boundary

    class Handler(http_boundary.BoundedMixin, BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "knowgov-mcp/1"

        def log_message(self, fmt, *a):   # stderr only, never stdout
            sys.stderr.write("mcp-http: " + fmt % a + "\n")

        def _send(self, code: int, body: dict | None = None, extra: dict | None = None):
            data = b"" if body is None else json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code)
            if body is not None:
                self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _guard(self) -> bool:
            """Every refusal closes the connection (task-0196 M3): its body is never read, so it must not
            be parsed as a second request on keep-alive."""
            if urlsplit(self.path).path != "/mcp":
                self.refuse(lambda: self._send(404, _error(None, -32600, "the MCP endpoint is /mcp")))
                return False
            import http_boundary
            refused = http_boundary.check(self.server.policy, self.headers)   # Host and Origin, each on its own (task-0141.03)
            if refused:
                self.refuse(lambda: self._send(refused[0], _error(None, -32600, refused[1])))
                return False
            if token:
                if not http_boundary.bearer_matches(self.headers.get("Authorization"), token):   # scheme any case (task-0272)
                    self.refuse(lambda: self._send(401, _error(None, -32600, "a bearer token is required"), {"WWW-Authenticate": "Bearer"}))
                    return False
            return True

        def _limits(self):
            return getattr(self.server, "limits", None) or mcp_limits()

        def do_POST(self):
            if not self._guard():
                self.arrived()
                return
            try:   # framing before a byte is read (task-0141.04); the JSON-RPC parse error stays the protocol's
                data = http_boundary.read_body(self, self._limits())
                self.arrived(body=True)
            except http_boundary.Refused as e:
                self.refuse(lambda: self._send(e.status, _error(None, -32600, e.reason)))
                return
            code, resp = server.handle_http(data, self.headers)   # strict UTF-8 (task-0272)
            self._send(code, resp)

        def do_GET(self):
            self.arrived()
            if self._guard():
                self._send(405, None, {"Allow": "POST"})   # no server-initiated stream: nothing is ever pushed

        def do_DELETE(self):
            self.arrived()
            if self._guard():
                self._send(405, None, {"Allow": "POST"})   # stateless: there is no session to end
    return Handler


def ipv6_literal(host: str) -> bool:
    """An IPv6 address as --host gives it (``::1``, ``[::1]``): the HTTP server binds IPv4 only (M10)."""
    return ":" in host.strip("[]")


def serve_http(server: Server, host: str, port: int, token: str | None) -> ThreadingHTTPServer:
    why = bind_check(host, token)
    if why:
        raise SystemExit(f"mcp_server: refusing to bind: {why}")
    if ipv6_literal(host):
        raise SystemExit(f"mcp_server: refusing to bind: {host} is an IPv6 address; the HTTP transport binds IPv4 only "
                         "(use 127.0.0.1, or an IPv4 address with KG_MCP_TOKEN)")
    import http_boundary
    httpd = http_boundary.BoundedServer((host.strip("[]"), port), make_handler(server, token), mcp_limits())   # task-0141.04
    httpd.policy = http_policy(host, httpd.server_address[1])   # the port actually bound, port 0 included
    return httpd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mcp_server.py", description="The gate and the three-valued answer as a read-only MCP server.")
    ap.add_argument("--http", action="store_true", help="serve Streamable HTTP at /mcp instead of stdio")
    ap.add_argument("--host", default=os.environ.get("KG_MCP_HOST", DEFAULT_HOST), help=f"HTTP bind address (default: KG_MCP_HOST, else {DEFAULT_HOST})")
    ap.add_argument("--port", type=int, default=int(os.environ.get("KG_MCP_PORT", DEFAULT_PORT)), help=f"HTTP port (default: KG_MCP_PORT, else {DEFAULT_PORT})")
    ap.add_argument("--as-of", default=None, help="the date every call that names none reads on: YYYY-MM-DD, record or today "
                                                  "(default: KG_AS_OF, else today), read once at start (task-0100)")
    ap.add_argument("--instance", default=None, help="the instance code_path reads code_map.toml and the code from "
                                                      "(default: KG_INSTANCE; none: its code leg reads unchecked)")
    ap.add_argument("--ledger", default=None, help="the trace ledger code_path reads (default: KG_LEDGER; none: unchecked)")
    args = ap.parse_args(argv)
    try:
        server = Server(Tools(as_of=args.as_of))
    except ValueError as e:   # a setting out of its bounds (KG_MCP_MAX_RESPONSE, task-0177): refused at start, named
        print(f"mcp_server: {e}", file=sys.stderr)
        return 2
    import upward
    server.tools.trace_cfg = upward.config(args.instance, args.ledger)   # read once, at start, as as_of is
    try:
        on = server.tools.session_as_of()
    except Exception as e:  # noqa: BLE001 - a bad date or a pinned clock with no KG_TODAY: refuse at start, not per call
        print(f"mcp_server: as_of {server.tools.as_of_from!r}: {e}", file=sys.stderr)
        return 2
    if not args.http:
        serve_stdio(server)
        return 0
    token = os.environ.get("KG_MCP_TOKEN") or None
    why = bind_check(args.host, token)
    if why:
        print(f"mcp_server: refusing to bind: {why}", file=sys.stderr)
        return 2
    if ipv6_literal(args.host):   # M10: refused before a bind, exit 2, not a crash with exit 1
        print(f"mcp_server: refusing to bind: {args.host} is an IPv6 address; the HTTP transport binds IPv4 only "
              "(use 127.0.0.1, or an IPv4 address with KG_MCP_TOKEN)", file=sys.stderr)
        return 2
    try:
        httpd = serve_http(server, args.host, args.port, token)
    except OSError as e:   # the port taken, the address not this machine's: cannot run
        print(f"mcp_server: cannot bind {args.host}:{args.port}: {e}", file=sys.stderr)
        return 2
    print(f"mcp_server: http://{args.host}:{httpd.server_address[1]}/mcp (read-only, as of {on} from {server.tools.as_of_from}"
          f"{', bearer token required' if token else ''})", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
