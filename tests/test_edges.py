"""Task-0200 (doc-0030 F6): uniform CLI and protocol edges. Each test is a probe of the review's finding,
failing on the code before the fix: G6 and R9 (a cannot-run read as exit 1 with a traceback), G7 (--publish
committing before the report is checked and written), M5 and M6 (an unknown argument answered, an
unhashable tool name killing the server), M10 (--host ::1 crashing), P8 (a hook's crash read as a warning),
P9 (knowgov-gate.sh's unresolved path exiting 1) and G12 (true taken for 1)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT)]
import cli_exit  # noqa: E402
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

HARNESS = ROOT / "harness"


def _env(**kw) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("KG_", "CLAUDE_"))}
    env.update(kw)
    return env


def _py(args, **env) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, env=_env(**env), cwd=str(ROOT), timeout=300)


def _cannot_run(p: subprocess.CompletedProcess, tool: str):
    assert p.returncode == 2, (p.returncode, p.stdout[-500:], p.stderr[-1500:])
    assert f"{tool}: cannot run:" in p.stderr and "Traceback" not in p.stderr, p.stderr[-1500:]


# ---- AC #1: one exit wrapper ---------------------------------------------------------------------------

def test_the_wrapper_maps_every_failure_to_run_to_exit_2_and_passes_exits_through():
    for exc in (RuntimeError("boom"), ValueError("bad json"), OSError("no such file"), KeyError("k")):
        def main(e=exc):
            raise e
        assert cli_exit.run(main, "t") == 2
    assert cli_exit.run(lambda: None, "t") == 0 and cli_exit.run(lambda: 1, "t") == 1   # a finding keeps 1

    def usage():
        raise SystemExit(2)
    try:
        cli_exit.run(usage, "t")
        raise AssertionError("SystemExit must pass through")
    except SystemExit as e:
        assert e.code == 2
    for mod in ("gate_cli", "trace", "run", "transcript"):
        tail = (HARNESS / f"{mod}.py").read_text(encoding="utf-8").split('if __name__ == "__main__":', 1)[1]
        assert "sys.exit(cli_exit.run(main, " in tail, mod


def test_g6_r9_a_wall_clock_read_and_a_malformed_baseline_exit_2_with_their_cause_no_traceback():
    # R9: under KG_CLOCK=pinned with no KG_TODAY, a read of today is WallClock, a RuntimeError the commands'
    # `except ValueError` missed: exit 1 and a traceback before
    p = _py([HARNESS / "gate_cli.py", "--subject", ROOT / "subjects" / "minimal", "--as-of", "today"], KG_CLOCK="pinned")
    _cannot_run(p, "gate")
    assert "KG_CLOCK=pinned" in p.stderr
    # G6: a baseline that is not a report
    with tempfile.TemporaryDirectory() as d:
        for text in ("not json", "[1, 2]", "{}"):
            bad = Path(d) / "baseline.json"
            bad.write_text(text, encoding="utf-8")
            p = _py([HARNESS / "gate_cli.py", "--subject", ROOT / "subjects" / "minimal", "--baseline", bad, "--as-of", "2026-11-08"],
                    KG_CLOCK="pinned", KG_TODAY="2026-11-08")
            _cannot_run(p, "gate")
            assert "baseline" in p.stderr, (text, p.stderr)
    p = _py([HARNESS / "run.py", "--deterministic", "--as-of", "today", "--out", tempfile.mkdtemp(prefix="kg-edge-")],
            KG_CLOCK="pinned", KG_SUBJECT=str(ROOT / "subjects" / "minimal"), KG_STORE="rdflib")
    if p.returncode != 0:   # with the pins a minimal run may finish before reading today; without, it cannot run
        assert p.returncode == 2 and "Traceback" not in p.stderr, (p.returncode, p.stderr[-800:])


def test_g6_an_unwritable_output_exits_2_and_g7_nothing_is_published_before_the_report_is_written():
    import gate_cli

    class St:
        committed = False

        def commit(self):
            St.committed = True

    class A:
        no_load, publish, task, fail_on, output = False, True, "codegen", "blocker", "/nonexistent-dir/report.json"
    keep_load, keep_eval, keep_validate = gate_cli._load, gate_cli.evaluate, schema_check.validate
    gate_cli._load = lambda st, scenario: None
    gate_cli.evaluate = lambda st, **kw: {"not": "a gate report"}
    try:
        # a report that does not match its schema, then a valid one and an unwritable -o: both refused, nothing published
        for valid in (False, True):
            if valid:
                schema_check.validate = lambda instance, schema: []
            St.committed = False
            try:
                gate_cli._gate_on(St(), A(), type("S", (), {"id": "minimal"})(), "S0", None, None, "2026-11-08", None, None)
                raise AssertionError("not refused")
            except gate_cli.CannotRun as e:
                assert ("cannot be written" if valid else "schema") in str(e), str(e)
            assert St.committed is False, "G7: the store was published before the report was checked and written"
    finally:
        gate_cli._load, gate_cli.evaluate, schema_check.validate = keep_load, keep_eval, keep_validate
    need_rdflib()
    p = _py([HARNESS / "gate_cli.py", "--subject", ROOT / "subjects" / "minimal", "-o", "/nonexistent-dir/report.json", "--as-of", "2026-11-08"],
            KG_CLOCK="pinned", KG_TODAY="2026-11-08", KG_STORE="rdflib")
    _cannot_run(p, "gate")
    assert "cannot be written" in p.stderr


# ---- AC #2: the MCP servers ----------------------------------------------------------------------------

MODERN = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}


def _servers():
    import mcp_runs
    reader = mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(AssertionError("no store is read"))))
    runs = mcp_server.Server(mcp_runs.RunTools(None), table=mcp_runs.tools_table(), info=mcp_runs.SERVER, instructions=mcp_runs.INSTRUCTIONS)
    return {"knowgov": (reader, "gate_verdict", {"senario": "S4"}), "knowgov-runs": (runs, "run_status", {"run_idd": "x"})}


def test_m5_an_argument_not_in_the_tools_schema_is_refused_in_both_eras_by_both_servers():
    for label, (s, tool, bad) in _servers().items():
        for meta in ({}, {"_meta": MODERN}):
            r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": bad, **meta}})
            assert r["error"]["code"] == -32602 and "unknown argument" in r["error"]["message"], (label, meta, r)
            assert list(bad)[0] in r["error"]["message"]
    for t in mcp_server.TOOLS:   # every tool's schema promises it, so every tool keeps it
        assert t["inputSchema"].get("additionalProperties") is False, t["name"]


def test_m6_a_non_string_tool_name_is_minus_32602_and_any_other_failure_minus_32603():
    for label, (s, _tool, _bad) in _servers().items():
        for name in (["x"], {"a": 1}, 3, None):
            r = s.handle({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": name}})
            assert r["error"]["code"] == -32602, (label, name, r)
    s = _servers()["knowgov"][0]
    s._tools = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("an internal failure"))
    for meta in ({}, {"_meta": MODERN}):
        r = s.handle({"jsonrpc": "2.0", "id": 8, "method": "tools/list", "params": dict(meta)})
        assert r == {"jsonrpc": "2.0", "id": 8, "error": {"code": -32603, "message": "internal error: RuntimeError"}}, r
    # on stdio the loop survives: the next request is answered
    import io
    out = io.StringIO()
    reader = _servers()["knowgov"][0]
    reqs = [{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": ["x"]}},
            {"jsonrpc": "2.0", "id": 2, "method": "ping"}]
    mcp_server.serve_stdio(reader, io.StringIO("".join(json.dumps(q) + "\n" for q in reqs)), out)
    answers = [json.loads(ln) for ln in out.getvalue().splitlines() if ln.strip()]
    assert [a["id"] for a in answers] == [1, 2] and answers[0]["error"]["code"] == -32602 and answers[1]["result"] == {}


def test_m5_m6_over_streamable_http():
    reader = _servers()["knowgov"][0]
    httpd = mcp_server.serve_http(reader, "127.0.0.1", 0, None)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/mcp"
    try:
        def post(body):
            req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                         headers={"Content-Type": "application/json", "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                return json.loads(e.read())
        r = post({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "gate_verdict", "arguments": {"senario": "S4"}}})
        assert r["error"]["code"] == -32602, r
        r = post({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": ["x"]}})
        assert r["error"]["code"] == -32602, r
        assert post({"jsonrpc": "2.0", "id": 3, "method": "ping"})["result"] == {}
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_m10_an_ipv6_host_exits_2_before_any_bind():
    for host in ("::1", "[::1]"):
        p = _py([HARNESS / "mcp_server.py", "--http", "--host", host, "--port", "0"], KG_TODAY="2026-11-08")
        assert p.returncode == 2 and "IPv6" in p.stderr and "Traceback" not in p.stderr, (host, p.returncode, p.stderr[-800:])


# ---- AC #3: the hooks and the gate script ---------------------------------------------------------------

HOOK = ROOT / "instance" / "ci" / "claude" / "knowgov_hook.py"
NON_OBJECT = """#!/bin/sh
echo '[1, 2]' > "$KG_REPORT"
exit 1
"""


def test_p8_a_report_that_is_not_an_object_blocks_in_every_profile():
    with tempfile.TemporaryDirectory() as d:
        kg = Path(d) / "kg"
        (kg / "instance" / "ci").mkdir(parents=True)
        (kg / "instance" / "ci" / "knowgov-gate.sh").write_text(NON_OBJECT, encoding="utf-8")
        ev = {"hook_event_name": "PreToolUse", "tool_name": "ExitPlanMode", "tool_input": {}, "cwd": d}
        for extra in ([], ["--advisory"]):
            p = subprocess.run([sys.executable, str(HOOK), "gate", "--task", "codegen", "--knowgov", str(kg), "--instance", d, *extra],
                               input=json.dumps(ev), capture_output=True, text=True, env=_env(KG_CLOCK="pinned"), timeout=120)
            assert p.returncode == 2 and "refused" in p.stderr and "not a JSON object" in p.stderr, (extra, p.returncode, p.stderr)


def test_p8_every_hooks_entry_blocks_on_any_exception():
    import importlib.util
    spec = importlib.util.spec_from_file_location("knowgov_hook", HOOK)
    hook = importlib.util.module_from_spec(spec)
    sys.modules["knowgov_hook"] = hook
    spec.loader.exec_module(hook)

    def crash():
        raise RuntimeError("an unexpected failure")
    assert hook.entry(crash, "h") == 2 and hook.entry(lambda: 0, "h") == 0 and hook.entry(lambda: 2, "h") == 2

    def exits_1():
        raise SystemExit(1)
    assert hook.entry(exits_1, "h") == 2, "exit 1 is Claude Code's non-blocking error: never let it out"
    for path in (HOOK, ROOT / ".claude" / "hooks" / "protected_paths.py", ROOT / "instance" / "ci" / "claude" / "attestation_paths.py"):
        tail = path.read_text(encoding="utf-8").rsplit('if __name__ == "__main__":', 1)[1]
        assert "entry(main, " in tail, path.name


def test_p9_the_gate_script_exits_2_when_a_path_does_not_resolve():
    script = ROOT / "instance" / "ci" / "knowgov-gate.sh"
    for args, said in (([" /nonexistent-kg", "."], "knowgov checkout"), ([str(ROOT), "/nonexistent-instance"], "instance")):
        for shell in (["sh"], ["bash", "-e"]):   # CI's shells run a script with -e: the old cd exited 1 there
            p = subprocess.run([*shell, str(script), *[a.strip() for a in args], "gate"], capture_output=True, text=True,
                               env=_env(KG_CLOCK="pinned"), timeout=120)
            assert p.returncode == 2 and said in p.stderr and "does not resolve" in p.stderr, (shell, args, p.returncode, p.stderr)


# ---- AC #4: schema_check ------------------------------------------------------------------------------

def test_g12_enum_and_const_compare_type_as_well_as_value():
    assert schema_check.validate(True, {"enum": [1, 2]}) and schema_check.validate(1, {"const": True})
    assert schema_check.validate(2.0, {"const": 2}) and schema_check.validate(0, {"enum": [False]})
    assert schema_check.validate([1, True], {"const": [1, 1]})
    assert schema_check.validate(1, {"enum": [1, 2]}) == [] and schema_check.validate(True, {"const": True}) == []
    assert schema_check.validate({"a": [1]}, {"const": {"a": [1]}}) == []
    # the gate report's exit_code is an enum of integers: a boolean exit code is no longer one
    schema = schema_check.load("gate-report")
    assert any("exit_code" in e for e in schema_check.validate({"exit_code": True}, schema))
