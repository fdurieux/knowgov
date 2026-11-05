"""The MCP server against the gate command on a live store (task-0056).

    python tools/check_mcp_server.py [--scenarios S1,S2]

For each scenario: load it into the store with ``gate_cli.py`` (the command's own load), then ask
the same question twice of the store as it stands, once as ``gate_cli.py --no-load -f json`` and
once as an MCP client over stdio calling ``gate_verdict``, and require the two reports to be equal
key for key. Then ask ``three_valued_answer`` for every key the subject names and require the
answer the record's deterministic run gives (D5), with provenance on every asserted statement.
Then ask ``evidence_bundle`` for the codegen task as of the record and require the text the governed
arm reads: ``gate.render_bundle`` over ``gate.resolve(store, "codegen")`` with the policy and the
task's verbatim documents from the scenario's kit, exactly as ``harness/run.py``'s ``arm_runs`` builds
it (task-0080); and for a key set, the same over ``resolve_spec`` on those keys.
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
for the reference code and the climb to a capability's ancestors (task-0143).
Then ask ``scenario_runs`` and require the subject's scenarios in order, the held scenario this one with
``store_status``'s ``loaded_at``, the record's D6 verdict for it, and no run in progress (task-0128);
and ``scenario_result`` on the record with that verdict, read from files (task-0129).
The same process also answers ``server/discover`` and a stateless (2026-07-28) ``gate_verdict``,
which must equal the handshake's (task-0079).
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
        return r["structuredContent"]

    def modern(self, method: str, params: dict) -> dict:
        """A self-contained 2026-07-28 request on the same process (task-0079): no handshake state used."""
        meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {},
                "io.modelcontextprotocol/clientInfo": {"name": "check_mcp_server", "version": "1"}}
        return self.request(method, {**params, "_meta": meta})

    def close(self) -> None:
        self.p.stdin.close()
        self.p.wait(timeout=30)


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
        self.p.wait(timeout=30)


def settled(stale: list[dict]) -> dict[str, list[str]]:
    """The record's stale statements and their verified or approved successors (task-0071)."""
    out = {x["id"]: sorted({t["id"] for t in x.get("successors") or [] if t.get("id") and t.get("status") in ("verified", "approved")})
           for x in stale}
    return {k: v for k, v in out.items() if v}


def check_stage2(sc: str, subject, failures: list[str]) -> None:
    """S6 after its change and re-verification: the server and the command agree, and both name
    what supersedes each invalidated statement as the record does."""
    load = gate_cli("--scenario", sc, "--stage", "2", "--reverify", "-f", "json")
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
    from tasks import TASKS
    task = "task_codegen"   # the runner passes the prompt prefix; verbatim_documents strips it to the class
    st = open_store()
    try:
        gate = resolve(st, "codegen") if keys is None else resolve_spec(st, "keys", dict(TASKS["codegen"], keys=keys))
        bundle = render_bundle(gate, arms.policy(), verbatim_documents(kit_for(sc, stage), task))
        return bundle, {a["id"] for v in gate["keys"].values() for a in v["assertions"]}
    finally:
        if st.name == "rdflib":
            st.path = None
        st.close()


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
    from tasks import TASKS
    base = {"node": start, "children": True, "scenario": sc, "as_of": "record"}
    answers = {}
    for task in TASKS:
        got = client.call("register_impact", {**base, "task": task})
        keys = [k["key"] for k in got["keys"]]
        want = client.call("gate_verdict", {"scenario": sc, "task": task, "keys": keys, "as_of": "record"}) if keys else None
        mine = {k["key"]: (k["level"], k["findings"]) for k in got["keys"]}
        theirs = {k: (want["levels"][k], [f for f in want["findings"] if f["kind"] in ("key", "stale", "lapsed") and f["key"] == k]) for k in keys} if want else {}
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
    """proposal_impact (task-0130): the worked example's gaps, and each reused node's keys equal to
    register_impact's for that node on the same scenario, task and as_of."""
    proposal = json.loads((ROOT / "tools" / "fixtures" / "proposal_contract_quote.json").read_text(encoding="utf-8"))
    got = client.call("proposal_impact", {"proposal": proposal, "scenario": sc, "as_of": "record"})
    gaps = sorted((g["rule"], g["id"]) for g in got["coverage"]["new_gaps"])
    if gaps != [("C1", "JRN-0014"), ("C1", "JRN-0015"), ("C2", "CAP-0009")]:
        failures.append(f"{label}: proposal_impact's new gaps are {gaps}")
    if not all(x["hypothetical"] is True for x in got["nodes"] + got["links"]) or got["stored"] is not False:
        failures.append(f"{label}: proposal_impact reported an overlay element not hypothetical, or a stored read")
    n = 0
    for entry in got["keys"]["by_node"]:
        want = client.call("register_impact", {"node": entry["node"], "scenario": sc, "as_of": "record"})
        n += len(entry["keys"])
        if entry["keys"] != want["keys"]:
            failures.append(f"{label}: proposal_impact's keys on {entry['node']} differ from register_impact's")
    print(f"{label}: proposal_impact names {len(gaps)} new gap(s); {n} key(s) on {len(got['keys']['by_node'])} reused node(s) "
          f"equal register_impact's")


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
    if not lineage or not lineage["ancestors"]:
        failures.append(f"{label}: the climb from {ex['file']} through {ex['app']} reached {caps}, lineage {lineage}")
        return
    print(f"{label}: key_nodes names every map key's rows; code_path {ex['file']} -> {ex['app']} (ledger {entry['id']}) "
          f"-> {caps} -> {caps[0]} under {[a['id'] for a in lineage['ancestors']]}, in 3 calls")


def census() -> dict:
    sys.path.insert(0, str(HARNESS))
    from store import open_store
    st = open_store()
    try:
        return st.census()
    finally:
        if st.name == "rdflib":
            st.path = None   # read, never written back
        st.close()


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
        load = gate_cli("--scenario", sc, "--as-of", "record", "-f", "json")
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
        finally:
            client.close()
        if census() != before:
            failures.append(f"{sc}: the store changed while the server read it")
        if SUBJECT.scenario(sc).get("stage2"):
            check_stage2(sc, SUBJECT, failures)
    for f in failures:
        print("FAIL " + f, file=sys.stderr)
    print("MCP server: " + ("every check holds" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
