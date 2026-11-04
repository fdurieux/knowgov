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
every key it lands on at the level ``gate_verdict`` gives that key set (task-0111).
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
    for sc in scenarios:
        load = gate_cli("--scenario", sc, "--as-of", "record", "-f", "json")
        if load.returncode == 2:
            failures.append(f"{sc}: gate_cli could not load: {load.stderr.strip()}")
            continue
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
