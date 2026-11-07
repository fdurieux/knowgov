"""Task-0172 (P5): every tool output of the MCP reader and of knowgov-runs is pinned by a schema.

Each tool names its schema under harness/schemas/ (mcp_server.OUTPUT_SCHEMAS, mcp_runs.OUTPUT_SCHEMAS) and its
description says so. Every tool is called on both public subjects, through a reader started on that subject
over stdio, and its structuredContent is validated with harness/schema_check.py. Every object in a schema is
closed, so a field the schema does not name fails; each test also adds one at the top and sees it refused.
Files-only tools run in the stdlib job, on a store that holds nothing or cannot be opened; the store-backed
tools run where rdflib is installed (the rdflib jobs), on a file store loaded with each subject's first
scenario. No network: knowgov-runs answers a stub page. tools/check_mcp_server.py validates every call it
makes against the same schemas, over stdio and HTTP and on Neo4j in the stack job."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tests"), str(ROOT / "tools")]
import mcp_runs  # noqa: E402
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402
from tests.test_mcp_runs import StubPage, _Env  # noqa: E402

SUBJECTS = [ROOT / "subjects" / "cargo_quote", ROOT / "subjects" / "jef_data_load"]
PROBE = ROOT / "tools" / "fixtures" / "subject_probe"
PROPOSAL = json.loads((ROOT / "tools" / "fixtures" / "proposal_contract_quote.json").read_text(encoding="utf-8"))
ALL = {**mcp_server.OUTPUT_SCHEMAS, **mcp_runs.OUTPUT_SCHEMAS}


def check(name: str, result: dict) -> dict:
    """The call answered, its structuredContent conforms to the tool's schema, and a field the schema does not
    name is refused."""
    assert not result.get("isError"), (name, result["content"][0]["text"][:400])
    out = result["structuredContent"]
    schema = schema_check.load(ALL[name])
    errors = schema_check.validate(out, schema)
    assert errors == [], (name, errors[:5])
    assert schema_check.validate({**out, "unschematised": 1}, schema), f"{name}: an unschematised field passed {ALL[name]}"
    return out


class Reader:
    """mcp_server.py on stdio, started on one subject: the transport a client uses."""

    def __init__(self, env: dict):
        self.p = subprocess.Popen([sys.executable, str(ROOT / "harness" / "mcp_server.py")], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
        self.n = 0
        self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def request(self, method: str, params: dict) -> dict:
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())

    def call(self, name: str, args: dict | None = None) -> dict:
        return check(name, self.request("tools/call", {"name": name, "arguments": args or {}})["result"])

    def close(self) -> None:
        self.p.stdin.close()
        self.p.wait(timeout=60)


def _env(subject: Path, store: str, **extra) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
    env.update(KG_SUBJECT=str(subject), KG_STORE="rdflib", KG_RDFLIB_FILE=store, KG_AS_OF="record", KG_CLOCK="pinned",
               KG_DEMO_RUNS=str(Path(store).parent / "runs"), **extra)
    return env


def _manifest(subject: Path) -> tuple[dict, list[str]]:
    rows = tomllib.loads((subject / "register_map.toml").read_text(encoding="utf-8")).get("row", [])
    scenarios = [s["id"] for s in tomllib.loads((subject / "scenarios.toml").read_text(encoding="utf-8"))["scenario"]]
    return {"rows": rows, "keys": sorted({r["key"] for r in rows})}, scenarios


CITED = """
import json, register_impact as ri, upward
system, man = upward._system()
reg = ri.load_tools()["register"].load_register(ri.register_root())
files = reg and ri.load_tools()["register"].load_toml(ri.register_root() / man).get("files", {}) if man else {}
print(json.dumps(sorted({upward.doc_key(ev, files, system) for rel in reg["relationships"].values() for ln in rel["links"]
                         for ev in ln.get("evidence", []) if ev.startswith(system)} - {None})[:2]))
"""


def _cited_documents(env: dict) -> list[str]:
    """Documents the register's links cite as evidence of the subject's export, as check_mcp_server reads them
    (task-0143), read in a process started on that subject."""
    p = subprocess.run([sys.executable, "-c", CITED], capture_output=True, text=True, env=env, cwd=str(ROOT / "harness"), timeout=120)
    assert p.returncode == 0, p.stderr[-400:]
    return json.loads(p.stdout)


def test_every_tool_names_its_schema_and_the_validator_reads_every_one():
    reader = {t["name"] for t in mcp_server.TOOLS}
    runs = {t["name"] for t in mcp_runs.tools_table()}
    assert set(mcp_server.OUTPUT_SCHEMAS) == reader and set(mcp_runs.OUTPUT_SCHEMAS) == runs
    for t in mcp_server.TOOLS + mcp_runs.tools_table():
        name = ALL[t["name"]]
        assert t["description"].endswith(mcp_server.output_note(name)), t["name"]
        schema = schema_check.load(name)   # the file is there and parses
        assert schema["$id"].endswith(f"/harness/schemas/{name}.schema.json"), name
        schema_check.validate({}, schema)   # every keyword in the supported subset, or this raises


def test_the_files_only_tools_conform_on_both_subjects():
    """Without a loaded store (rdflib absent: the store cannot be opened; present: it holds nothing)."""
    import example_instance
    with tempfile.TemporaryDirectory() as d:
        inst = example_instance.build(Path(d) / "inst")
        for subject in SUBJECTS:
            m, scenarios = _manifest(subject)
            extra = {"KG_INSTANCE": str(inst)} if subject.name == example_instance.SUBJECT.name else {}
            env = _env(subject, os.path.join(d, f"{subject.name}.ttl"), **extra)
            cited = _cited_documents(env)
            assert cited or subject.name != example_instance.SUBJECT.name, "no document cited by the register's links"
            r = Reader(env)
            try:
                listing = r.call("register_nodes")
                r.call("register_nodes", {"node": listing["nodes"][0]["id"]})
                for key in m["keys"][:4]:
                    r.call("key_nodes", {"key": key})
                for doc in cited:
                    r.call("document_links", {"document": doc})
                path = next((str(p.relative_to(inst / "code")) for p in (inst / "code").rglob("*.py")), "reference_impl.py") \
                    if extra else "reference_impl.py"
                r.call("code_path", {"path": path})
                cap = next(n["id"] for n in listing["nodes"] if n["id"].startswith("CAP"))
                r.call("register_impact", {"node": m["rows"][0]["nodes"][0]})
                r.call("register_impact", {"node": cap, "children": True})
                r.call("proposal_impact", {"proposal": PROPOSAL})
                r.call("proposal_impact", {"scope": "JRN-0001"})   # task-0191: the approved register alone, keys per slice
                r.call("scenario_runs")
                r.call("scenario_runs", {"scenario": scenarios[0], "limit": 1})
                for sc in scenarios:
                    r.call("scenario_result", {"scenario": sc, "source": "record"})
                got = r.call("list_subjects")
                assert {s["id"] for s in got["subjects"]} >= {"cargo_quote", "jef_data_load"}
                r.call("subject_check", {"root": PROBE.relative_to(ROOT).as_posix(),
                                         "subject_toml": (PROBE / "subject.toml").read_text(encoding="utf-8"),
                                         "register_map_toml": (PROBE / "register_map.toml").read_text(encoding="utf-8"),
                                         "documents": {"requirements.md": (PROBE / "requirements.md").read_text(encoding="utf-8")}})
            finally:
                r.close()


def test_the_store_backed_tools_conform_on_both_subjects():
    """On a file store holding each subject's first scenario, loaded by gate_cli as a run would."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as d:
        for subject in SUBJECTS:
            m, scenarios = _manifest(subject)
            store, sc = os.path.join(d, f"{subject.name}.ttl"), scenarios[0]
            env = _env(subject, store)
            p = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--scenario", sc, "--as-of", "record", "--publish"],
                               capture_output=True, text=True, env=env, timeout=600)
            assert p.returncode in (0, 1), p.stderr[-600:]
            r = Reader(env)
            try:
                status = r.call("store_status")
                assert status["scenario"] == sc, status
                held = r.call("list_subjects")
                assert next(x for x in held["subjects"] if x["default"])["held"] == sc
                r.call("scenario_runs")
                for task in status["tasks"]:
                    r.call("gate_verdict", {"task": task})
                key = (status["three_valued_keys"] or m["keys"])[0]
                r.call("gate_verdict", {"keys": [key, "no_such|key"], "fail_on": "info"})
                statements = []
                for k in [*status["three_valued_keys"][:3], "no_such|key"]:
                    statements += r.call("three_valued_answer", {"key": k})["statements"]
                r.call("evidence_bundle")
                r.call("evidence_bundle", {"keys": [key], "verbatim": False})
                r.call("register_impact", {"node": m["rows"][0]["nodes"][0], "scenario": sc})
                r.call("proposal_impact", {"proposal": PROPOSAL, "scenario": sc})
                for scope in ("JRN-0001", "JRN-0005"):   # task-0191: each slice's keys read at their levels
                    r.call("proposal_impact", {"scope": scope, "scenario": sc})
                r.call("held_keys")
                r.call("derived_outputs", {"key": key})
                docs = sorted({s["artefact"] for s in statements if s.get("artefact")})
                for doc in docs[:1]:
                    r.call("document_statements", {"document": doc})
            finally:
                r.close()


def test_the_knowgov_runs_tools_conform_against_a_page():
    page = StubPage(run_text="loading S1\n")

    def call(name, args=None):
        srv = mcp_runs.make_server(mcp_runs.Page("http://localhost:8080", token="t", opener=page))
        return check(name, srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                       "params": {"name": name, "arguments": args or {}}})["result"])
    with _Env(KG_MCP_RUN_MODES="deterministic,arms"):
        assert call("run_status")["status"] == "idle"
        assert call("run_options")["run"] is None
        call("start_run", {"scenario": "S1", "mode": "deterministic"})
        assert call("run_options")["run"]["status"] == "running"
        assert call("run_status")["log_tail"] == "loading S1\n"
        page.current.update(status="done", finished="2026-11-04T23:01:00+00:00", exit_code=0)
        assert "next" in call("run_status", {"run": "2026-11-04-2300"})
    page = StubPage(execution="absent")
    with _Env(KG_MCP_RUN_MODES=None):
        got = call("run_options")
        assert got["execution"]["ok"] is False and got["worker"]["attested"] is False
    page = StubPage(worker={"backend": "worker", "attested": True, "why": None,
                            "host": {"system": "Linux", "kernel": "7.0.0-1014-aws", "machine": "x86_64", "engine": "docker 28"},
                            "cloud": {"name": "AWS", "basis": "read from the kernel release's -aws suffix, not checked"}})
    with _Env(KG_MCP_RUN_MODES="deterministic"):
        assert call("run_options")["worker"]["cloud"]["name"] == "AWS"
    verdict = {"state": "refused", "status": 401, "checked_at": "2026-11-06T13:00:00Z", "scope": "key", "model_listed": None,
               "why": "the endpoint refused the key in OPENAI_API_KEY (401)"}
    class Checked(StubPage):   # the page's rows as task-0171 serves them, each with its key check
        def __call__(self, req, timeout=None):
            resp = super().__call__(req, timeout)
            body = json.loads(resp.read())
            for row in body.get("model_rows") or []:
                row["key_check"] = verdict
            return type(resp)(resp.status, body)
    page = Checked()
    with _Env(KG_MCP_RUN_MODES="deterministic"):
        assert call("run_options")["model_rows"][0]["key_check"] == verdict
