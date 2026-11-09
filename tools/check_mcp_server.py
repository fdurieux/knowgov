"""The MCP server against the gate command on a live store (task-0056).

    python tools/check_mcp_server.py [--scenarios S1,S2]

For each scenario: load it into the store with ``gate_cli.py --publish`` (the command's own load,
published so the server reads it; decision-0017), then ask
the same question twice of the store as it stands, once as ``gate_cli.py --no-load -f json`` and
once as an MCP client over stdio calling ``gate_verdict``, and require the two reports to be equal
key for key. Then ask ``three_valued_answer`` for every key the subject names and require the
answer the record's deterministic run gives (D5), with provenance on every asserted statement.
Then ask ``evidence_bundle`` for the codegen task as of the record and require the text the governed
arm reads: ``gate.render_bundle`` over ``gate.resolve(store, "codegen")`` with the policy and the
task's verbatim documents from the scenario's kit, named by the scenario's prompts (``scenarios.toml``'s
``prompts``, doc-0030 M9), exactly as ``harness/run.py``'s ``arm_runs`` builds it (task-0080); and for a key set, the same over ``resolve_spec`` on those keys.
Then ask ``register_impact`` from the first node of the subject's first register-map row and require
every key it lands on at the level ``gate_verdict`` gives that key set (task-0111); and, when that node
has a parent, from the parent with ``children`` (the register's decision 0014, task-0118): every key the
child lands lands again, each at ``gate_verdict``'s level; the keys resting only on a withdrawn
descendant come last, flagged ``withdrawn``, and no withdrawn one is walked from; and under each declared
task class every landed key, its findings and the gate line are ``gate_verdict --task``'s for that key
set, no task being codegen's and ``keys`` refused (task-0120); at stage 2, the same from the first stale
key's node, where the stale findings carry each class's route and the classes must not all agree.
Then ask ``proposal_impact`` with doc-0017's worked example (``tools/fixtures/proposal_contract_quote.json``)
and require its gaps (C1 on the two unsupported new steps, C2 on the new capability) and every reused
node's keys equal to what ``register_impact`` from that node gives for the same task and as_of, with
every overlay element hypothetical (task-0130).
Then ask ``register_nodes`` for the whole register, each taxonomy, and the lineage of the first node of
the subject's first map row: every node by id, the parent chain to the root and the children (task-0142).
Then ask ``key_nodes`` for every key of the subject's register map, and, on the example instance (``KG_INSTANCE``,
``KG_LEDGER`` set before the server starts, the reference code registered by ``trace.py register``), ``code_path``
for the reference code and the climb to a capability's ancestors, and ``document_links`` for the first row's
anchored document (task-0143). Once, store-free: the file-only tools listed and answering alike over stdio and
HTTP, and the shipped managed allowlist admitting the server by name (task-0142, task-0143).
Then ask ``held_keys``, ``derived_outputs`` and ``document_statements`` and require each equal to the port's
read in-process through a read handle, the levels gate_verdict's for the held key set, and each used statement
stale or superseded as the gate's stale statements read; at stage 2 too (task-0144).
Then ask ``scenario_runs`` and require the subject's scenarios in order, the held scenario this one with
``store_status``'s ``loaded_at``, the record's D6 verdict for it, and no run in progress (task-0128);
and ``scenario_result`` on the record with that verdict, read from files (task-0129).
The same process also answers ``server/discover`` and a stateless (2026-07-28) ``gate_verdict``,
which must equal the handshake's (task-0079).
Once, after the scenarios: ``subject_check`` listed over stdio and Streamable HTTP, and on doc-0018's probe
(``tools/fixtures/subject_probe``) its report equal to ``tools/check_subject.py --json``'s, over stdio in both eras (task-0146); and the prompts
``new_subject`` and ``add_artefact`` listed and given over both transports (task-0148).
Once, after the scenarios: a call naming another subject under ``KG_SUBJECTS`` equals the same call on a reader
started on that subject, over stdio and HTTP; ``list_subjects`` names every subject; a store-backed call for it
refuses naming the held subject and the run to start (task-0157, decision-0013 with A1).
Every answer it reads, over either transport, conforms to the schema the tool's description names
(``mcp_server.OUTPUT_SCHEMAS``, harness/schemas/; task-0172).
Finally, prove the server wrote nothing: the store reads the same census before and after.

A scenario with a later version (``[scenario.stage2]``, S6) is asked a second time after
``gate_cli.py --stage 2 --reverify`` has loaded the change and its re-verification (task-0071): the
reports must again be equal, ``superseded_by`` must name for each stale statement the verified or
approved successors the record's ``gate_after_reverification`` lists, and ``three_valued_answer``
must name the same successors under ``invalidated`` for every stale key, and ``register_impact`` from
the first node of each stale key's map row must name the key's stale statement and the suspect
derived outputs that used it, as the record and ``gate_verdict`` do.

``KG_STORE`` picks the store as everywhere: ``rdflib`` needs ``KG_RDFLIB_FILE`` (the script sets
one in a temporary directory when it is unset), ``neo4j`` the stack's database. Exit 0 when every
check holds, 1 when one does not.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"


def gate_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), *args], capture_output=True, text=True, env=os.environ.copy())


def _stop(p: subprocess.Popen, grace: float = 30) -> None:
    """A server this check started ends with the check, whatever its outcome (task-0159): it is waited
    for, then killed and reaped if it has not exited within ``grace`` seconds."""
    try:
        p.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait(timeout=grace)


def conform(name: str, out: dict) -> None:
    """Every answer this check reads, on either transport, conforms to the schema the tool names (task-0172)."""
    if str(HARNESS) not in sys.path:
        sys.path.insert(0, str(HARNESS))
    import mcp_server
    import schema_check
    errors = schema_check.validate(out, schema_check.load(mcp_server.OUTPUT_SCHEMAS[name]))
    if errors:
        raise AssertionError(f"{name}: off harness/schemas/{mcp_server.OUTPUT_SCHEMAS[name]}.schema.json: {errors[:3]}")


class StdioClient:
    """A minimal MCP client: start the server, initialise, call tools."""

    def __init__(self):
        self.p = subprocess.Popen([sys.executable, str(HARNESS / "mcp_server.py")], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, env=os.environ.copy())
        self.n = 0
        init = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "check_mcp_server", "version": "1"}})
        assert init["result"]["serverInfo"]["name"] == "knowgov", init
        self.notify("notifications/initialized")

    def notify(self, method: str) -> None:
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.p.stdin.flush()

    def request(self, method: str, params: dict) -> dict:
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        resp = json.loads(self.p.stdout.readline())
        assert resp.get("id") == self.n, resp
        return resp

    def call(self, name: str, args: dict) -> dict:
        r = self.request("tools/call", {"name": name, "arguments": args})["result"]
        if r.get("isError"):
            raise AssertionError(f"{name}{args}: {r['content'][0]['text']}")
        out = r["structuredContent"]
        conform(name, out)
        return out

    def modern(self, method: str, params: dict) -> dict:
        """A self-contained 2026-07-28 request on the same process (task-0079): no handshake state used."""
        meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {},
                "io.modelcontextprotocol/clientInfo": {"name": "check_mcp_server", "version": "1"}}
        return self.request(method, {**params, "_meta": meta})

    def close(self) -> None:
        try:
            self.p.stdin.close()
        finally:
            _stop(self.p)


class HttpClient(StdioClient):
    """The same client over Streamable HTTP: start ``mcp_server.py --http`` on a free loopback port,
    then one POST per message (task-0095)."""

    def __init__(self):
        import re
        self.p = subprocess.Popen([sys.executable, str(HARNESS / "mcp_server.py"), "--http", "--host", "127.0.0.1", "--port", "0"],
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                  text=True, env=os.environ.copy())
        line = self.p.stderr.readline()
        m = re.search(r"(http://127\.0\.0\.1:\d+/mcp)", line)
        if not m:
            self.p.kill()
            raise RuntimeError(f"mcp_server.py --http did not start: {line.strip()}")
        self.url = m.group(1)
        import threading   # the server logs each request to stderr: drain it so the pipe never fills
        threading.Thread(target=lambda: [None for _ in self.p.stderr], daemon=True).start()
        self.n = 0
        init = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "check_mcp_server", "version": "1"}})
        assert init["result"]["serverInfo"]["name"] == "knowgov", init
        self.notify("notifications/initialized")

    def _post(self, body: dict) -> dict | None:
        import urllib.request
        req = urllib.request.Request(self.url, data=json.dumps(body).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
        return json.loads(data) if data else None

    def notify(self, method: str) -> None:
        self._post({"jsonrpc": "2.0", "method": method})

    def request(self, method: str, params: dict) -> dict:
        self.n += 1
        resp = self._post({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params})
        assert resp.get("id") == self.n, resp
        return resp

    def close(self) -> None:
        self.p.terminate()
        _stop(self.p)


def settled(stale: list[dict]) -> dict[str, list[str]]:
    """The record's stale statements and their verified or approved successors (task-0071)."""
    out = {x["id"]: sorted({t["id"] for t in x.get("successors") or [] if t.get("id") and t.get("status") in ("verified", "approved")})
           for x in stale}
    return {k: v for k, v in out.items() if v}


def check_stage2(sc: str, subject, failures: list[str]) -> None:
    """S6 after its change and re-verification: the server and the command agree, and both name
    what supersedes each invalidated statement as the record does."""
    load = gate_cli("--scenario", sc, "--stage", "2", "--reverify", "--publish", "-f", "json")   # the server reads this load (decision-0017)
    if load.returncode == 2:
        failures.append(f"{sc} stage 2: gate_cli could not load: {load.stderr.strip()}")
        return
    cli = gate_cli("--scenario", sc, "--no-load", "-f", "json")
    if cli.returncode == 2:
        failures.append(f"{sc} stage 2: gate_cli --no-load could not run: {cli.stderr.strip()}")
        return
    expected = json.loads(cli.stdout)
    rel = subject.scenario(sc).get("deterministic_record") or sc
    rec = json.loads((subject.record_dir / rel / "deterministic.json").read_text(encoding="utf-8"))["stage2"]
    want = settled(rec["gate_after_reverification"]["stale"])
    before = census()
    client = StdioClient()
    try:
        got = client.call("gate_verdict", {"scenario": sc})
        if got != expected:
            diff = sorted(k for k in set(got) | set(expected) if got.get(k) != expected.get(k))
            failures.append(f"{sc} stage 2: gate_verdict differs from gate_cli --no-load on {diff}")
        if got.get("version") == "v1":
            failures.append(f"{sc} stage 2: the store holds v1, not the change")
        if not want or got.get("superseded_by") != want:
            failures.append(f"{sc} stage 2: superseded_by {got.get('superseded_by')}, the record's successors {want}")
        by_key = {x["key"]: x["id"] for x in rec["gate_after_reverification"]["stale"]}
        for key, sid in sorted(by_key.items()):
            ans = client.call("three_valued_answer", {"key": key, "scenario": sc})
            named = {x["id"]: x["superseded_by"] for x in ans.get("invalidated") or []}
            if named.get(sid) != want.get(sid, []):
                failures.append(f"{sc} stage 2 {key}: three_valued_answer names {sid} superseded_by {named.get(sid)}, the record {want.get(sid, [])}")
        print(f"{sc} stage 2 --reverify: gate_verdict {got['verdict']} (exit_code {got['exit_code']}, version {got.get('version')}) "
              f"equals gate_cli --no-load; superseded_by names {len(want)} statement(s) as the record does, "
              f"in the gate and in {len(by_key)} three-valued answer(s)")
        check_bundle(client, sc, 2, failures, f"{sc} stage 2")
        check_impact(client, sc, failures, f"{sc} stage 2", rec["gate_after_reverification"], got)
        check_store_reads(client, sc, failures, f"{sc} stage 2", stage=2)
    finally:
        client.close()
    if census() != before:
        failures.append(f"{sc} stage 2: the store changed while the server read it")


def arms_bundle(sc: str, stage: int, keys: list[str] | None = None) -> tuple[str, set[str]]:
    """The bundle and its assertion ids as harness/run.py's ``arm_runs`` hands them to the governed arm,
    read in-process on the store as it stands (released without being written back)."""
    sys.path.insert(0, str(HARNESS))
    import arms
    from gate import render_bundle, resolve, resolve_spec
    from kitio import kit_for, verbatim_documents
    from store import open_store
    from subject import SUBJECT
    from tasks import TASKS
    # the scenario's prompts, as harness/run.py's _run_all passes them (doc-0030 M9): the prompt prefix, which
    # verbatim_documents strips to the class
    task = SUBJECT.scenario(sc).get("prompts", "task_codegen")
    with open_store(access="read") as st:   # never published (task-0141.02)
        gate = resolve(st, "codegen") if keys is None else resolve_spec(st, "keys", dict(TASKS["codegen"], keys=keys))
        bundle = render_bundle(gate, arms.policy(), verbatim_documents(kit_for(sc, stage), task))
        return bundle, {a["id"] for v in gate["keys"].values() for a in v["assertions"]}


def check_bundle(client: "StdioClient", sc: str, stage: int, failures: list[str], label: str) -> None:
    """evidence_bundle equals what the arms read, for the task and for a key set of two of its keys."""
    sys.path.insert(0, str(HARNESS))
    from tasks import TASKS
    got = client.call("evidence_bundle", {"scenario": sc, "as_of": "record"})
    want, ids = arms_bundle(sc, stage)
    if got["bundle"] != want:
        failures.append(f"{label}: evidence_bundle differs from the bundle the arms read ({len(got['bundle'])} vs {len(want)} characters)")
    if set(got["assertion_ids"]) != ids:
        failures.append(f"{label}: evidence_bundle names {len(got['assertion_ids'])} assertion(s), the arms' bundle {len(ids)}")
    keys = list(TASKS["codegen"]["keys"])[:2]
    sub = client.call("evidence_bundle", {"scenario": sc, "keys": keys, "as_of": "record"})
    want_sub, _ = arms_bundle(sc, stage, keys)
    if sub["bundle"] != want_sub:
        failures.append(f"{label}: evidence_bundle for {keys} differs from render_bundle over those keys")
    print(f"{label}: evidence_bundle ({got['verdict']}, {len(got['bundle']):,} characters, {len(ids)} assertion(s), "
          f"{len(got['verbatim'])} verbatim document(s)) equals the bundle the arms read; a key set of {len(keys)} likewise")


def check_impact(client: "StdioClient", sc: str, failures: list[str], label: str, rec: dict | None = None,
                 gate: dict | None = None) -> None:
    """register_impact (task-0111). Stage 1: from the first map row's first node, every landed key reads
    the level gate_verdict gives that key set on the record's date. With ``rec`` (a stage-2 gate of the
    record) and ``gate`` (gate_verdict's report on the same store): from the first node of each stale
    key's row, the key names the record's stale statement and the suspect derived outputs that used it
    as the report's suspect_derived findings name them (the record's d3check/S6 holds no derived output;
    the command's stage 2 registers one, task-0018)."""
    sys.path.insert(0, str(HARNESS))
    from subject import SUBJECT
    rows = {r["key"]: r for r in SUBJECT.register_map().get("row") or []}
    if not rows:
        print(f"{label}: register_impact not checked, the subject maps no key onto the register")
        return
    if rec is None:
        first = next(iter(rows.values()))
        got = client.call("register_impact", {"node": first["nodes"][0], "scenario": sc, "as_of": "record"})
        keys = [k["key"] for k in got["keys"]]
        want = client.call("gate_verdict", {"scenario": sc, "keys": keys, "as_of": "record"}) if keys else {"levels": {}}
        if not keys or {k["key"]: k["level"] for k in got["keys"]} != want["levels"]:
            failures.append(f"{label}: register_impact from {first['nodes'][0]} lands {len(keys)} key(s) whose levels differ from gate_verdict's")
        print(f"{label}: register_impact from {first['nodes'][0]} reaches {sum(len(v) for v in got['reached'].values())} node(s) "
              f"and lands {len(keys)} key(s), each at gate_verdict's level")
        parent = got["node"].get("parent")
        if parent:   # task-0118: the same from its parent with the register's descent (decision 0014)
            up = client.call("register_impact", {"node": parent, "children": True, "scenario": sc, "as_of": "record"})
            ukeys = [k["key"] for k in up["keys"]]
            uwant = client.call("gate_verdict", {"scenario": sc, "keys": ukeys, "as_of": "record"}) if ukeys else {"levels": {}}
            if not set(keys) <= set(ukeys) or {k["key"]: k["level"] for k in up["keys"]} != uwant["levels"]:
                failures.append(f"{label}: register_impact from {parent} with children lands {len(ukeys)} key(s), not every one of "
                                f"{first['nodes'][0]}'s or not at gate_verdict's levels")
            print(f"{label}: register_impact from {parent} with children walks {sum(c['walked'] for c in up['children'])} of "
                  f"{len(up['children'])} descendant(s) and lands {len(ukeys)} key(s), each at gate_verdict's level")
            check_withdrawn(up, parent, failures, label)
            check_task_classes(client, sc, failures, label, parent)
        return
    for x in sorted(rec.get("stale") or [], key=lambda x: x["key"]):
        if x["key"] not in rows:
            continue
        start = rows[x["key"]]["nodes"][0]
        want_suspect = sorted(f["ref"] for f in gate["findings"] if f["kind"] == "suspect_derived" and x["id"] in f["related"])
        got = client.call("register_impact", {"node": start, "scenario": sc, "as_of": "record"})
        k = next((k for k in got["keys"] if k["key"] == x["key"]), None)
        if k is None or x["id"] not in k["stale"] or k["suspect"] != want_suspect:
            failures.append(f"{label}: register_impact from {start} on {x['key']}: {k and (k['stale'], k['suspect'])}, "
                            f"the record {x['id']} stale and {want_suspect} suspect")
            continue
        print(f"{label}: register_impact from {start} names {x['key']} stale ({x['id']}) and {', '.join(want_suspect) or 'nothing'} suspect")
    stale = [x for x in sorted(rec.get("stale") or [], key=lambda x: x["key"]) if x["key"] in rows]
    if stale:   # task-0120: under each class, with stale findings to route
        check_task_classes(client, sc, failures, label, rows[stale[0]["key"]]["nodes"][0], must_differ=True)


def check_withdrawn(got: dict, start: str, failures: list[str], label: str) -> None:
    """task-0120: with children, the keys whose rows name only a withdrawn descendant come last, each
    flagged withdrawn and coming through withdrawn descendants only, and no withdrawn one is walked from."""
    withdrawn = {c["id"] for c in got["children"] if c.get("withdrawn")}
    flagged = [k for k in got["keys"] if k.get("withdrawn")]
    ok = (got["keys"][len(got["keys"]) - len(flagged):] == flagged
          and all(k["withdrawn"] is True and k["via"] and set(k["via"]) <= withdrawn for k in flagged)
          and not withdrawn & {e["from"] for e in got["edges"]})
    if not ok:
        failures.append(f"{label}: register_impact from {start} with children flags {[k['key'] for k in flagged]} "
                        f"not as resting only on the withdrawn {sorted(withdrawn)}, or walks on from one")
    print(f"{label}: register_impact from {start} with children lists {len(flagged)} key(s) flagged withdrawn"
          + (f" ({', '.join(k['key'] + ' via ' + '+'.join(k['via']) for k in flagged)})" if flagged else ""))


def check_task_classes(client: "StdioClient", sc: str, failures: list[str], label: str, start: str,
                       must_differ: bool = False) -> None:
    """task-0120: register_impact under each declared task class reads every landed key, its findings
    (owner and route) and the gate line as gate_verdict --task gives that key set; no task is codegen's
    answer; keys is refused. Classes may agree where no finding carries a route (S6 at stage 1); with
``must_differ`` (stage 2, stale findings routed by class) they must not all agree."""
    sys.path.insert(0, str(HARNESS))
    from gate_cli import OWNED   # the kinds a key's findings are, one definition (task-0260)
    from tasks import TASKS
    base = {"node": start, "children": True, "scenario": sc, "as_of": "record"}
    answers = {}
    for task in TASKS:
        got = client.call("register_impact", {**base, "task": task})
        keys = [k["key"] for k in got["keys"]]
        want = client.call("gate_verdict", {"scenario": sc, "task": task, "keys": keys, "as_of": "record"}) if keys else None
        mine = {k["key"]: (k["level"], k["findings"]) for k in got["keys"]}
        theirs = {k: (want["levels"][k], [f for f in want["findings"] if f["kind"] in OWNED and f["key"] == k]) for k in keys} if want else {}
        if not keys or mine != theirs or got["gate"]["task"] != task or got["gate"]["verdict"] != want["verdict"]:
            failures.append(f"{label}: register_impact from {start} under {task} differs from gate_verdict --task {task} on its {len(keys)} key(s)")
        answers[task] = (mine, got["gate"]["verdict"])
        print(f"{label}: register_impact from {start} under {task}: {got['gate']['verdict']} on {len(keys)} key(s), "
              f"each as gate_verdict --task {task} reads it")
    if "codegen" in answers and client.call("register_impact", base)["keys"] != \
            client.call("register_impact", {**base, "task": "codegen"})["keys"]:
        failures.append(f"{label}: register_impact from {start} without a task is not codegen's answer")
    if len(answers) > 1:   # each class's own answer; where no finding carries a route, they may agree
        n = len({json.dumps(a, sort_keys=True) for a in answers.values()})
        print(f"{label}: register_impact from {start}: {n} distinct answer(s) across {sorted(answers)}")
        if must_differ and n == 1:
            failures.append(f"{label}: register_impact from {start} gives one answer under every class {sorted(answers)}, "
                            "though its stale findings route by class")
    refused = client.request("tools/call", {"name": "register_impact", "arguments": {**base, "task": "keys"}})["result"]
    if not refused.get("isError"):
        failures.append(f"{label}: register_impact took task keys, a key set, not a class")


def check_runs(client: "StdioClient", sc: str, status: dict, failures: list[str], label: str) -> None:
    """scenario_runs (task-0128): every scenario of the subject in its order, the held one this one with
    store_status's loaded_at, the record's entry for it with the D6 verdict its deterministic.json gives,
    and no run in progress (the loads here are gate_cli's own, which write no run.json)."""
    from subject import SUBJECT
    got = client.call("scenario_runs", {})
    if [x["id"] for x in got["scenarios"]] != list(SUBJECT.order):
        failures.append(f"{label}: scenario_runs lists {[x['id'] for x in got['scenarios']]}, not {SUBJECT.order}")
        return
    held = got.get("held") or {}
    if held.get("scenario") != sc or not status.get("loaded_at") or held.get("loaded_at") != status["loaded_at"]:
        failures.append(f"{label}: scenario_runs holds {held}, store_status loaded_at {status.get('loaded_at')}")
    if got["run_in_progress"] is not None:
        failures.append(f"{label}: scenario_runs reports a run in progress: {got['run_in_progress']}")
    entry = next(x for x in got["scenarios"] if x["id"] == sc)["record"][0]
    det = SUBJECT.record_dir / sc / "deterministic.json"
    want = json.loads(det.read_text(encoding="utf-8"))["D6_gate"]["verdict"] if det.exists() else None
    if entry["gate"] != want:
        failures.append(f"{label}: scenario_runs gives the record's gate as {entry['gate']}, its deterministic.json {want}")
    res = client.call("scenario_result", {"scenario": sc, "source": "record"})
    if res["gate"]["verdict"] != want or "not the store" not in res["reads"]:
        failures.append(f"{label}: scenario_result on the record gives {res['gate']['verdict']}, its deterministic.json {want}")
    print(f"{label}: scenario_runs lists {len(got['scenarios'])} scenario(s), holds {held.get('scenario')} loaded at "
          f"{held.get('loaded_at')}, the record's gate {entry['gate']}")


def check_proposal(client: "StdioClient", sc: str, failures: list[str], label: str) -> None:
    """proposal_impact (task-0130): the worked example's gaps, its slice map equal to the command's
    (task-0152), and each reused node's keys equal to register_impact's for that node on the same
    scenario, task and as_of."""
    proposal = json.loads((ROOT / "tools" / "fixtures" / "proposal_contract_quote.json").read_text(encoding="utf-8"))
    got = client.call("proposal_impact", {"proposal": proposal, "scenario": sc, "as_of": "record"})
    gaps = sorted((g["rule"], g["id"]) for g in got["coverage"]["new_gaps"])
    if gaps != [("C1", "JRN-0014"), ("C1", "JRN-0015"), ("C2", "CAP-0009")]:
        failures.append(f"{label}: proposal_impact's new gaps are {gaps}")
    if not all(x["hypothetical"] is True for x in got["nodes"] + got["links"]) or got["stored"] is not False:
        failures.append(f"{label}: proposal_impact reported an overlay element not hypothetical, or a stored read")
    if str(HARNESS) not in sys.path:
        sys.path.insert(0, str(HARNESS))
    import mcp_server
    import proposal_impact as pi   # the CLI's report, in this process: the slice map the same (task-0152)
    import register_impact as ri
    st = mcp_server.open_read_only()   # read with the same store, scenario and as_of: each slice's keys at their levels (task-0191)
    try:
        mine = pi.with_levels(pi.evaluate(proposal, today=pi._date(got["as_of"], "as_of"), task="codegen"), st, task="codegen",
                              as_of=got["as_of"], scenario=sc)
    finally:
        st.release()
    held = json.loads(json.dumps(mine["slices"], default=str))
    if got.get("slices") != held:
        failures.append(f"{label}: proposal_impact's slice map differs from the command's")
    scoped = 0   # task-0191: a named journey on the approved register, each slice's rows register_impact's with_levels
    for scope in ("JRN-0001", "JRN-0005"):
        rep = client.call("proposal_impact", {"scope": scope, "scenario": sc, "as_of": "record"})
        if rep["slices"]["scope"]["id"] != scope or rep["overlay"]["nodes"] or not rep["slices"]["map"]:
            failures.append(f"{label}: proposal_impact scope {scope} gave {rep['slices']['scope']}, {len(rep['slices']['map'])} slice(s)")
        for sl in rep["slices"]["map"]:
            k = sl["keys"]
            if not k["rows"]:
                continue
            keys = list(dict.fromkeys(r["key"] for r in k["rows"]))
            gate = client.call("gate_verdict", {"keys": keys, "scenario": sc, "as_of": "record"})
            bare = [{x: v for x, v in r.items() if x not in ("level", "stale", "suspect", "findings")} for r in k["rows"]]
            if k["rows"] != ri.with_levels(bare, gate) or sum(k["cells"]["levels"].values()) != k["landed"]:
                failures.append(f"{label}: proposal_impact scope {scope}: slice {sl['start']['id']}'s keys differ from the gate's levels")
            scoped += 1
    classes = check_slice_classes(client, sc, failures, label)
    n = 0
    for entry in got["keys"]["by_node"]:
        want = client.call("register_impact", {"node": entry["node"], "scenario": sc, "as_of": "record"})
        n += len(entry["keys"])
        if entry["keys"] != want["keys"]:
            failures.append(f"{label}: proposal_impact's keys on {entry['node']} differ from register_impact's")
    e = got.get("slices", {}).get("elements", {})
    print(f"{label}: proposal_impact names {len(gaps)} new gap(s); {n} key(s) on {len(got['keys']['by_node'])} reused node(s) "
          f"equal register_impact's; {len(got.get('slices', {}).get('map', []))} slice(s), {e.get('in_slices')} of "
          f"{e.get('denominator')} element(s) in them, equal the command's; scoped by JRN-0001 and JRN-0005, {scoped} slice(s) "
          f"with keys, each at the gate's levels (task-0191); under {classes}, each class's keys in a slice or on no "
          "slice, at the class gate's levels (task-0252)")


def check_slice_classes(client: "StdioClient", sc: str, failures: list[str], label: str) -> list[str]:
    """task-0252: under each declared task class, every slice of the first scope the subject's map lands on
    reads only that class's keys, each at the level the subject's own gate under the class reads it, with
    each slice's verdict gate_verdict's on its keys; the class's keys on no slice are slices.task_keys, at
    the same levels, so each of the class's keys is in a slice or there, and nowhere twice."""
    from tasks import TASKS
    from subject import SUBJECT
    mapped = json.dumps(SUBJECT.register_map(), default=str)
    scope = next((x for x in ("JRN-0001", "JRN-0005") if x in mapped), None)
    if scope is None:
        return []
    for task, spec in TASKS.items():
        rep = client.call("proposal_impact", {"scope": scope, "task": task, "scenario": sc, "as_of": "record"})
        whole = client.call("gate_verdict", {"scenario": sc, "task": task, "as_of": "record"})
        want, on = list(dict.fromkeys(spec["keys"])), []
        for sl in rep["slices"]["map"]:
            k = sl["keys"]
            ks = list(dict.fromkeys(r["key"] for r in k["rows"] if not r.get("withdrawn")))
            on += ks
            if k["task"] != task or k["of"] != len(want) or set(ks) - set(want) \
                    or any(r["level"] != whole["levels"][r["key"]] for r in k["rows"]):
                failures.append(f"{label}: proposal_impact {scope} under {task}: slice {sl['start']['id']} reads keys "
                                f"outside the class or at levels its gate does not")
            elif ks and k["gate"]["verdict"] != client.call("gate_verdict", {"scenario": sc, "task": task, "keys": ks,
                                                                             "as_of": "record"})["verdict"]:
                failures.append(f"{label}: proposal_impact {scope} under {task}: slice {sl['start']['id']}'s verdict is not the gate's")
        rest = rep["slices"]["task_keys"]
        off = [x["key"] for x in rest["keys"]]
        if rest["task"] != task or set(on) & set(off) or set(on) | set(off) != set(want) \
                or rest["denominator"] != len(want) or rest["in_slices"] + rest["on_no_slice"] != len(want) \
                or any(x["level"] != whole["levels"][x["key"]] for x in rest["keys"]):
            failures.append(f"{label}: proposal_impact {scope} under {task}: the class's keys are not each in one slice or on no slice")
        print(f"{label}: proposal_impact {scope} under {task}: {rest['in_slices']} of the class's {len(want)} key(s) in slices, "
              f"{rest['on_no_slice']} on no slice ({rest['gate']['verdict'] if rest['gate'] else 'none'}); "
              f"the class gate {whole['verdict']}")
    return sorted(TASKS)


def check_nodes(client: "StdioClient", failures: list[str], label: str) -> None:
    """register_nodes (task-0142): the listing is every node of the register, by id, under the report's
    schema; each taxonomy's filter its nodes; and from the first node of the subject's first map row the
    lineage is its parent chain to the root and its children the nodes naming it parent, never a walk."""
    import register_impact as ri
    import schema_check
    from subject import SUBJECT
    schema = schema_check.load("register-nodes")
    reg = ri.load_tools()["register"].load_register(ri.register_root())
    got = client.call("register_nodes", {"limit": 1000})
    errors = schema_check.validate(got, schema)
    if errors or [n["id"] for n in got["nodes"]] != sorted(reg["nodes"]) or got["total"] != len(reg["nodes"]):
        failures.append(f"{label}: register_nodes lists {got['total']} node(s), the register holds {len(reg['nodes'])}; {errors[:3]}")
    for tax in sorted({n["_taxonomy"] for n in reg["nodes"].values()}):
        ids = [n["id"] for n in client.call("register_nodes", {"taxonomy": tax, "limit": 1000})["nodes"]]
        if ids != sorted(nid for nid, n in reg["nodes"].items() if n["_taxonomy"] == tax):
            failures.append(f"{label}: register_nodes taxonomy={tax} lists {ids}")
    rows = SUBJECT.register_map().get("row", [])
    start = next((x for r in rows for x in r.get("nodes") or [] if x in reg["nodes"]), None)
    if start is None:
        print(f"{label}: register_nodes lists {got['total']} node(s); no map row names a register node")
        return
    lin = client.call("register_nodes", {"node": start})["lineage"]
    chain, at = [], reg["nodes"][start].get("parent")
    while at is not None and at in reg["nodes"] and at not in chain:
        chain.append(at)
        at = reg["nodes"][at].get("parent")
    kids = sorted(nid for nid, n in reg["nodes"].items() if n.get("parent") == start)
    if [a["id"] for a in lin["ancestors"]] != chain or [c["id"] for c in lin["children"]] != kids:
        failures.append(f"{label}: register_nodes lineage of {start} is {lin}, the register's parent chain {chain}, children {kids}")
    print(f"{label}: register_nodes lists {got['total']} node(s); {start} sits under {chain or 'nothing'} with {len(kids)} child(ren)")
PROBE = ROOT / "tools" / "fixtures" / "subject_probe"


def check_refusal_closes(client: "HttpClient", failures: list[str]) -> None:
    """M3 (task-0196): on the live HTTP server, a refused request (a foreign Host) whose body is a second,
    admissible request, on one keep-alive socket, gets one answer, the refusal, and the socket closes. A raw
    socket to the loopback server this check started, since urllib always asks for the connection to close."""
    import socket
    from urllib.parse import urlsplit
    port = urlsplit(client.url).port
    inner_body = json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": {}}).encode()
    inner = (f"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nContent-Type: application/json\r\n"
             f"Content-Length: {len(inner_body)}\r\n\r\n").encode() + inner_body
    outer = (f"POST /mcp HTTP/1.1\r\nHost: evil.example:{port}\r\nConnection: keep-alive\r\n"
             f"Content-Type: application/json\r\nContent-Length: {len(inner)}\r\n\r\n").encode()
    got = b""
    with socket.create_connection(("127.0.0.1", port), timeout=15) as sock:   # the loopback server started above
        sock.sendall(outer + inner)
        while True:
            try:
                chunk = sock.recv(65536)
            except OSError:
                break
            if not chunk:
                break
            got += chunk
    import re   # a second response follows the first's body directly, with no line break between them
    statuses = re.findall(rb"HTTP/1\.[01] \d{3}", got)
    if len(statuses) != 1 or b"421" not in statuses[0]:
        failures.append(f"HTTP: a refused request's body was answered as a second request (M3): {statuses}")
    else:
        print("HTTP: a refusal (421) closes the connection; its smuggled body gets no answer (M3)")


def check_subject_tool(failures: list[str]) -> None:
    """subject_check (task-0146): listed over stdio and over Streamable HTTP, and on doc-0018's probe the
    report equal to ``tools/check_subject.py --json``'s on the same files, the store never read."""
    rel = PROBE.relative_to(ROOT).as_posix()
    args = {"root": rel, "subject_toml": (PROBE / "subject.toml").read_text(encoding="utf-8"),
            "register_map_toml": (PROBE / "register_map.toml").read_text(encoding="utf-8"),
            "documents": {"requirements.md": (PROBE / "requirements.md").read_text(encoding="utf-8")}}
    cp = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), rel, "--json"],
                        capture_output=True, text=True, cwd=str(ROOT), env=os.environ.copy())
    cli = json.loads(cp.stdout)
    for kind in (StdioClient, HttpClient):
        client = kind()
        try:
            listed = [t["name"] for t in client.request("tools/list", {})["result"]["tools"]]
            if "subject_check" not in listed:
                failures.append(f"subject_check over {kind.__name__}: not listed ({listed})")
                continue
            prompts = [p["name"] for p in client.request("prompts/list", {})["result"]["prompts"]]
            given = client.request("prompts/get", {"name": "new_subject", "arguments": {"id": "probe", "task": "codegen"}})["result"]
            if prompts != ["new_subject", "add_artefact"] or "When to stop" not in given["messages"][0]["content"]["text"]:
                failures.append(f"prompts over {kind.__name__}: listed {prompts}, or new_subject without its stop condition (task-0148)")
            got = client.call("subject_check", args)
            if got != cli:
                diff = sorted(k for k in set(got) | set(cli) if got.get(k) != cli.get(k))
                failures.append(f"subject_check over {kind.__name__}: differs from check_subject.py --json on {diff}")
            # H7 (task-0196): a manifest naming a path outside the call is refused, with nothing of the server in it
            escape = dict(args, subject_toml=args["subject_toml"].replace('path = "requirements.md"', f'path = "{ROOT / "README.md"}"'),
                          documents={**args["documents"], "x/../subject.toml": "[subject]\nid = \"over\"\n"})
            for bad in (dict(escape, documents=args["documents"]), dict(args, documents=escape["documents"])):
                r = client.request("tools/call", {"name": "subject_check", "arguments": bad})["result"]
                if not r.get("isError") or "structuredContent" in r:
                    failures.append(f"subject_check over {kind.__name__}: a path outside the call was not refused (H7)")
            if kind is HttpClient:   # the stateless era over HTTP needs its headers; stdio carries it here
                check_refusal_closes(client, failures)
                continue
            stateless = client.modern("tools/call", {"name": "subject_check", "arguments": args})["result"]
            if stateless.get("structuredContent") != cli:
                failures.append(f"subject_check over {kind.__name__}: the stateless revision's report differs")
        finally:
            client.close()
    print(f"subject_check on {rel}: exit_code {cli['exit_code']}, {len(cli['findings'])} finding(s), yield "
          f"{cli['yield']['state']}; equal to check_subject.py --json over stdio (both eras) and HTTP; "
          "the prompts new_subject and add_artefact over both")


def example_trace(failures: list[str]) -> dict | None:
    """The example instance and a ledger for the code leg (task-0143), when the example instance is this
    subject's: KG_INSTANCE and KG_LEDGER set before the server starts, as its configuration."""
    sys.path.insert(0, str(ROOT / "tools"))
    import example_instance
    from subject import SUBJECT
    if example_instance.SUBJECT.name != SUBJECT.id:
        return None
    out = Path(tempfile.mkdtemp(prefix="kg-mcp-inst-"))
    inst = example_instance.build(out / "inst")
    os.environ.update(KG_INSTANCE=str(inst), KG_LEDGER=str(out / "ledger.json"))
    return {"instance": inst, "ledger": out / "ledger.json", "file": "reference_impl.py", "commit": "0" * 40,
            "app": example_instance.CODE_APP, "registered": False}


def trace_register(ex: dict, failures: list[str], label: str) -> None:
    """trace.py register the example's reference code into the ledger, as a merge would (once)."""
    if ex is None or ex["registered"]:
        return
    r = subprocess.run([sys.executable, str(HARNESS / "trace.py"), "register", "--instance", str(ex["instance"]),
                        "--commit", ex["commit"], "--file", ex["file"], "--ledger", str(ex["ledger"]), "--as-of", "record"],
                       capture_output=True, text=True, env=os.environ.copy())
    if r.returncode != 0:
        failures.append(f"{label}: trace.py register could not record the example's code: {r.stderr.strip()}")
    ex["registered"] = r.returncode == 0


def check_upward(client: "StdioClient", ex: dict | None, failures: list[str], label: str) -> None:
    """key_nodes and code_path (task-0143): every map key's rows as register_map.toml holds them; the example's
    code file to its application, its header and the ledger's entry trace.py register wrote; and the climb
    code_path, register_impact walk=dependants with children, register_nodes node= reaching a capability's
    ancestors in at most four calls."""
    from subject import SUBJECT
    rows = SUBJECT.register_map().get("row", [])
    for key in sorted({r["key"] for r in rows}):
        got = client.call("key_nodes", {"key": key})
        want = [r["nodes"] for r in rows if r["key"] == key]
        if [[n["id"] for n in r["nodes"]] for r in got["rows"]] != want:
            failures.append(f"{label}: key_nodes {key} names {got['rows']}, register_map.toml {want}")
    if ex is None:
        print(f"{label}: key_nodes names {len({r['key'] for r in rows})} key(s)' rows; no example instance for code_path")
        return
    got = client.call("code_path", {"path": ex["file"]})
    led = json.loads(ex["ledger"].read_text(encoding="utf-8")) if ex["ledger"].exists() else {"entries": []}
    want = next((e for e in led["entries"] if e["path"] == ex["file"]), None)
    entry = got["ledger"]["entry"]
    if got["code_map"]["app"] != ex["app"] or got["citation"]["status"] != "read":
        failures.append(f"{label}: code_path names {got['code_map']}, citation {got['citation']}")
    if want is None or entry is None or entry["id"] != want["id"] or entry["sha256"] != want["sha256"] or entry["drift"]:
        failures.append(f"{label}: code_path's ledger entry {entry} is not trace.py register's {want}")
    up = client.call("register_impact", {"node": ex["app"], "walk": "dependants", "children": True})
    caps = [x["id"] for x in up["reached"].get("CAP", [])]
    lineage = client.call("register_nodes", {"node": caps[0]})["lineage"] if caps else None
    import schema_check
    import upward
    import register_impact as ri
    system, man = upward._system()
    reg = ri.load_tools()["register"].load_register(ri.register_root())
    files = reg and ri.load_tools()["register"].load_toml(ri.register_root() / man).get("files", {}) if man else {}
    cited = sorted({upward.doc_key(ev, files, system) for rel in reg["relationships"].values() for ln in rel["links"]
                    for ev in ln.get("evidence", []) if ev.startswith(system)} - {None})
    for doc in cited[:3]:
        got_doc = client.call("document_links", {"document": doc})
        if not got_doc["links"] or schema_check.validate(got_doc, schema_check.load("document-links")):
            failures.append(f"{label}: document_links {doc} names no link, or a report off its schema")
    if not lineage or not lineage["ancestors"]:
        failures.append(f"{label}: the climb from {ex['file']} through {ex['app']} reached {caps}, lineage {lineage}")
        return
    print(f"{label}: key_nodes names every map key's rows; code_path {ex['file']} -> {ex['app']} (ledger {entry['id']}) "
          f"-> {caps} -> {caps[0]} under {[a['id'] for a in lineage['ancestors']]}, in 3 calls")


FILE_TOOLS = ("register_nodes", "key_nodes", "code_path", "document_links")   # doc-0020's hops: files only, no store
STORE_TOOLS = ("held_keys", "derived_outputs", "document_statements")   # doc-0020 C3: the store's reads (task-0144)
ALLOWLIST = ROOT / "instance" / "ci" / "claude" / "managed-mcp-allowlist.json"


def check_subjects(failures: list[str]) -> None:
    """task-0157 (B7, decision-0013 with A1): over stdio and Streamable HTTP, a call naming another subject
    under KG_SUBJECTS, on the reader of this subject, equals the same call on a reader started on that
    subject (a files-only tool, and scenario_runs for that subject); list_subjects names every subject and the
    held scenario's; a store-backed call for the other subject is refused naming the held subject and the run
    to start; a path is refused."""
    sys.path.insert(0, str(HARNESS))
    import subject_ids
    from subject import SUBJECT
    other = next((x for x in subject_ids.subjects() if x["id"] != SUBJECT.id), None)
    if other is None:
        failures.append("subjects: KG_SUBJECTS lists no subject beside the server's own")
        return
    calls = [("register_nodes", {"taxonomy": "capabilities"}), ("scenario_runs", {})]
    for name, cls in (("stdio", StdioClient), ("http", HttpClient)):
        mine = cls()
        keep = os.environ.get("KG_SUBJECT")
        os.environ["KG_SUBJECT"] = str(other["root"])
        try:
            theirs = cls()
        finally:
            os.environ.pop("KG_SUBJECT", None) if keep is None else os.environ.__setitem__("KG_SUBJECT", keep)
        try:
            for tool, args in calls:
                if mine.call(tool, {**args, "subject": other["id"]}) != theirs.call(tool, args):
                    failures.append(f"subjects {name}: {tool} for {other['id']} differs from a reader started on it")
            listed = mine.call("list_subjects", {})
            ids = [x["id"] for x in listed["subjects"]]
            if ids[0] != SUBJECT.id or other["id"] not in ids or listed["store_backed"] != sorted(listed["store_backed"]):
                failures.append(f"subjects {name}: list_subjects lists {ids}")
            held = listed["store"]["held_scenario"]
            r = mine.request("tools/call", {"name": "gate_verdict", "arguments": {"subject": other["id"]}})["result"]
            text = r["content"][0]["text"]
            if held and held not in other["scenarios"] and not (r.get("isError") and "start_run" in text and held in text):
                failures.append(f"subjects {name}: gate_verdict for {other['id']} with {held} held answered {text[:160]!r}")
            r = mine.request("tools/call", {"name": "register_nodes", "arguments": {"subject": "../" + other["id"]}})["result"]
            if not (r.get("isError") and "never a path" in r["content"][0]["text"]):
                failures.append(f"subjects {name}: a path as subject was not refused")
        finally:
            mine.close()
            theirs.close()
    print(f"subjects: {other['id']} answered through {SUBJECT.id}'s reader as by its own, over stdio and HTTP; "
          f"list_subjects lists {len(listed['subjects'])}; a store-backed call for it refused with the run to start")


def check_transports(failures: list[str], ex: dict | None = None) -> None:
    """doc-0020's tools served by the knowgov server on both transports (task-0142, task-0143), and an unknown
    argument or a non-string tool name refused with -32602 on both (task-0200): tools/list over
    stdio and Streamable HTTP lists each, the same call answers the same on both, and the shipped managed
    allowlist admits the server by its name, so no client changes to reach them."""
    from subject import SUBJECT
    key = next((r["key"] for r in SUBJECT.register_map().get("row", [])), None)
    calls = [("register_nodes", {"taxonomy": "capabilities"}), ("register_nodes", {"node": "CAP-0002"})]
    calls += [("key_nodes", {"key": key})] if key else []
    calls += [("code_path", {"path": ex["file"] if ex else "reference_impl.py"})]
    answers = {}
    for name, cls in (("stdio", StdioClient), ("http", HttpClient)):
        client = cls()
        try:
            listed = {t["name"] for t in client.request("tools/list", {})["result"]["tools"]}
            missing = [t for t in (*FILE_TOOLS, *STORE_TOOLS) if t not in listed]
            if missing:
                failures.append(f"{name}: tools/list lacks {missing}")
            answers[name] = [client.call(t, a) for t, a in calls]
            # task-0200 (M5, M6): an argument outside the tool's schema and a non-string name are -32602 here too;
            # task-0296: a key outside the one entity|attribute rule, a zero-width space in it included, as well
            for params in ({"name": "gate_verdict", "arguments": {"senario": "S4"}}, {"name": ["gate_verdict"]},
                           {"name": "gate_verdict", "arguments": {"keys": ["nonsense"]}},
                           {"name": "evidence_bundle", "arguments": {"keys": ["thing\u200b|property"]}}):
                err = client.request("tools/call", params).get("error") or {}
                if err.get("code") != -32602:
                    failures.append(f"{name}: tools/call {params} answered {err or 'a result'}, not -32602 (M5, M6, task-0296)")
        finally:
            client.close()
    if answers.get("stdio") != answers.get("http"):
        failures.append("the file-only tools answer differently over stdio and HTTP")
    allowed = {x.get("serverName") for x in json.loads(ALLOWLIST.read_text(encoding="utf-8")).get("allowedMcpServers", [])}
    sys.path.insert(0, str(HARNESS))
    import mcp_server
    if mcp_server.SERVER["name"] not in allowed:
        failures.append(f"{ALLOWLIST.name} admits {sorted(allowed)}, not the server {mcp_server.SERVER['name']}")
    print(f"transports: {', '.join((*FILE_TOOLS, *STORE_TOOLS))} listed over stdio and HTTP, {len(calls)} call(s) equal on both; "
          f"{ALLOWLIST.name} admits {mcp_server.SERVER['name']}")


def held_gate_failures(client, sc: str, label: str, held: dict) -> list[str]:
    """task-0283: held_keys' gate is each task class's own verdict and why, gate_verdict's for the same store,
    class and as_of, never the held key set gated as if every held key were required."""
    from tasks import TASKS
    out = []
    for task in sorted(TASKS):
        hk = held if task == held["task"] else client.call("held_keys", {"scenario": sc, "task": task, "as_of": "record"})
        gv = client.call("gate_verdict", {"scenario": sc, "task": task, "as_of": "record"})
        if hk["gate"] != {"task": task, "verdict": gv["verdict"], "why": gv["why"]}:
            out.append(f"{label}: held_keys' gate under {task} reads {hk['gate']}, gate_verdict {gv['verdict']}: {gv['why']}")
    return out


def check_store_reads(client: "StdioClient", sc: str, failures: list[str], label: str, stage: int = 1) -> None:
    """held_keys, derived_outputs, document_statements (task-0144): each equal to the port's read on the store as
    it stands, through a read handle in-process; held_keys' levels gate_verdict's for that key set; every output's
    used statements read stale or superseded exactly as the gate's stale statements are superseded; under its schema."""
    sys.path.insert(0, str(HARNESS))
    import schema_check
    from gate import superseded_by
    from store import open_store
    held = client.call("held_keys", {"scenario": sc, "as_of": "record"})
    with open_store(access="read") as st:
        port_keys = st.held_keys()
        port_derived = st.derived_outputs()
        stale = {x["id"]: x for x in st.stale_on_keys(sorted({u["key"] for d in port_derived for u in d["used"] if u["key"]}))}
        docs = sorted({u["artefact"] for d in port_derived for u in d["used"] if u["artefact"]}) or \
            sorted({r["artefact"] for k in port_keys[:3] for r in st.key_evidence(k["key"], ["proposed", "validated", "verified", "approved"])})
        port_docs = {doc: st.artefact_assertions(doc) for doc in docs[:3]}
    for name, rep in (("held_keys", held),):
        if errors := schema_check.validate(rep, schema_check.load("held-keys")):
            failures.append(f"{label}: {name} is off its schema: {errors[:3]}")
    if [{k: r[k] for k in ("key", "n", "statuses")} for r in held["keys"]] != port_keys:
        failures.append(f"{label}: held_keys lists {held['total']} key(s), the port's held_keys {len(port_keys)}")
    if port_keys:
        gate = client.call("gate_verdict", {"scenario": sc, "keys": [k["key"] for k in port_keys], "as_of": "record"})
        if {r["key"]: r["level"] for r in held["keys"]} != gate["levels"]:
            failures.append(f"{label}: held_keys' levels differ from gate_verdict's for the held key set")
        failures.extend(held_gate_failures(client, sc, label, held))
    outs = []
    for key in sorted({u["key"] for d in port_derived for u in d["used"] if u["key"]})[:5]:
        got = client.call("derived_outputs", {"scenario": sc, "key": key})
        outs += got["outputs"]
        if errors := schema_check.validate(got, schema_check.load("derived-outputs")):
            failures.append(f"{label}: derived_outputs {key} is off its schema: {errors[:3]}")
        if [o["id"] for o in got["outputs"]] != [d["id"] for d in port_derived if any(u["key"] == key for u in d["used"])]:
            failures.append(f"{label}: derived_outputs {key} names {[o['id'] for o in got['outputs']]}")
    for d in port_derived:
        one = client.call("derived_outputs", {"scenario": sc, "derived": d["id"]})["outputs"][0]
        if [u["id"] for u in one["used"]] != [u["id"] for u in d["used"]]:
            failures.append(f"{label}: derived_outputs {d['id']} used differs from the port's")
        for u in one["used"]:
            if u["status"] == "invalidated":
                want = "superseded" if superseded_by(stale.get(u["id"], {})) else "stale"
                if u["state"] != want or u["superseded_by"] != superseded_by(stale.get(u["id"], {})):
                    failures.append(f"{label}: {d['id']} reads {u['id']} {u['state']}, the gate's stale statements {want}")
    for doc, rows in port_docs.items():
        got = client.call("document_statements", {"scenario": sc, "document": doc})
        if errors := schema_check.validate(got, schema_check.load("document-statements")):
            failures.append(f"{label}: document_statements {doc} is off its schema: {errors[:3]}")
        if [x["id"] for x in got["statements"]] != [r["id"] for r in rows]:
            failures.append(f"{label}: document_statements {doc} lists {got['total']}, the port's read {len(rows)}")
    states = sorted({u["state"] for d in port_derived for u in client.call("derived_outputs", {"scenario": sc, "derived": d["id"]})["outputs"][0]["used"]}) \
        if port_derived else []
    print(f"{label}: held_keys {held['total']} key(s) ({len(held['unrequired'])} unrequired) at gate_verdict's levels, "
          f"its gate gate_verdict's under every task class; "
          f"derived_outputs {len(port_derived)} output(s), used read {states or 'none'}; "
          f"document_statements on {len(port_docs)} document(s), each the port's read")


def census() -> dict:
    sys.path.insert(0, str(HARNESS))
    from store import open_store
    with open_store(access="read") as st:   # never published (task-0141.02)
        return st.census()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenarios", help="comma-separated scenario ids (default: every scenario of the subject)")
    args = ap.parse_args(argv)
    if (os.environ.get("KG_STORE") or "neo4j").lower() == "rdflib" and not os.environ.get("KG_RDFLIB_FILE"):
        os.environ["KG_RDFLIB_FILE"] = str(Path(tempfile.mkdtemp(prefix="kg-mcp-")) / "store.ttl")
    sys.path.insert(0, str(HARNESS))
    import cadence
    from subject import SUBJECT
    os.environ.update(cadence.pin_record({}))   # the record's day, the wall clock refused (task-0075)
    scenarios = args.scenarios.split(",") if args.scenarios else list(SUBJECT.order)
    failures = []
    ex = example_trace(failures)
    for sc in scenarios:
        load = gate_cli("--scenario", sc, "--as-of", "record", "--publish", "-f", "json")   # the server reads this load (decision-0017)
        if load.returncode == 2:
            failures.append(f"{sc}: gate_cli could not load: {load.stderr.strip()}")
            continue
        trace_register(ex, failures, sc)
        cli = gate_cli("--scenario", sc, "--no-load", "--as-of", "record", "-f", "json")
        if cli.returncode == 2:
            failures.append(f"{sc}: gate_cli --no-load could not run: {cli.stderr.strip()}")
            continue
        expected = json.loads(cli.stdout)
        before = census()
        client = StdioClient()
        try:
            got = client.call("gate_verdict", {"scenario": sc, "as_of": "record"})
            if got != expected:
                diff = sorted(k for k in set(got) | set(expected) if got.get(k) != expected.get(k))
                failures.append(f"{sc}: gate_verdict differs from gate_cli --no-load on {diff}")
            disc = client.modern("server/discover", {})["result"]
            stateless = client.modern("tools/call", {"name": "gate_verdict", "arguments": {"scenario": sc, "as_of": "record"}})["result"]
            if disc.get("supportedVersions", [None])[0] != "2026-07-28" or stateless.get("structuredContent") != expected:
                failures.append(f"{sc}: the stateless revision's gate_verdict differs from the handshake's, or server/discover did not answer")
            status = client.call("store_status", {})
            if status["scenario"] != sc:
                failures.append(f"{sc}: store_status says the store holds {status['scenario']}")
            rel = SUBJECT.scenario(sc).get("deterministic_record") or sc
            rec_path = SUBJECT.record_dir / rel / "deterministic.json"
            d5 = json.loads(rec_path.read_text(encoding="utf-8")).get("D5_three_valued") if rec_path.exists() else None
            for key in SUBJECT.three_valued:
                ans = client.call("three_valued_answer", {"key": key, "scenario": sc})
                if d5 and key in d5 and ans["answer"] != d5[key]["answer"]:
                    failures.append(f"{sc} {key}: {ans['answer']}, the record says {d5[key]['answer']}")
                for s in ans["statements"]:
                    if not s.get("artefact") or "fragments" not in s:
                        failures.append(f"{sc} {key}: statement {s.get('id')} has no provenance")
            print(f"{sc}: gate_verdict {got['verdict']} (exit_code {got['exit_code']}) equals gate_cli --no-load; "
                  f"{len(SUBJECT.three_valued)} three-valued key(s) checked")
            check_bundle(client, sc, 1, failures, sc)
            check_impact(client, sc, failures, sc)
            check_proposal(client, sc, failures, sc)
            check_runs(client, sc, status, failures, sc)
            check_nodes(client, failures, sc)
            check_upward(client, ex, failures, sc)
            check_store_reads(client, sc, failures, sc)
        finally:
            client.close()
        if census() != before:
            failures.append(f"{sc}: the store changed while the server read it")
        if SUBJECT.scenario(sc).get("stage2"):
            check_stage2(sc, SUBJECT, failures)
    check_transports(failures, ex)
    before = census()
    check_subjects(failures)
    if census() != before:
        failures.append("subjects: the store changed while the reader answered for another subject")
    check_subject_tool(failures)
    if census() != before:
        failures.append("subject_check: the store changed while the server checked a proposed subject")
    for f in failures:
        print("FAIL " + f, file=sys.stderr)
    print("MCP server: " + ("every check holds" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
