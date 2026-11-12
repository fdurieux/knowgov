"""Task-0264: numeric settings and tokens read through one parser, refused at start naming the setting.

A numeric setting must parse as its kind, be finite and sit within its bounds, else ``settings.BadSetting``
names it, and ``mcp_server``, ``mcp_runs``, the page and the worker exit 2 at start with that line, no
traceback. A token blank once stripped is no token: a wide bind refuses and writes refuse. The defaults
are unchanged."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import http_boundary as hb  # noqa: E402
import settings  # noqa: E402

SERVER = ROOT / "harness" / "mcp_server.py"
RUNS = ROOT / "harness" / "mcp_runs.py"
PAGE = ROOT / "demo" / "app" / "server.py"
WORKER = ROOT / "harness" / "worker.py"
BAD_FLOATS = ("nan", "inf", "-inf", "1e400", "abc", "0", "-1")


def _run(path: Path, env: dict, *args: str, timeout: float = 60.0) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if not k.startswith(("KG_MCP_", "KG_PAGE_", "KG_DEMO_", "KG_WORKER_"))}
    base.pop("KG_SUBJECT_CALL_TIMEOUT", None)
    return subprocess.run([sys.executable, str(path), *args], input="", capture_output=True, text=True,
                          env={**base, "KG_AS_OF": "2026-10-30", **env}, cwd=ROOT, timeout=timeout)


def _refused(p: subprocess.CompletedProcess, name: str) -> bool:
    return p.returncode == 2 and name in p.stderr and "Traceback" not in p.stderr


def test_the_list_names_every_numeric_setting_the_task_found():
    """AC1: the settings the validation pass found unvalidated, each in NUMBERS with its kind and bounds."""
    found = {"KG_SUBJECT_CALL_TIMEOUT", "KG_RDFLIB_LOCK_TIMEOUT", "KG_WORKER_JOB_SECONDS", "KG_MCP_PORT",
             *(f"{p}_{n}" for p in ("KG_MCP", "KG_PAGE") for n in ("MAX_BODY", "READ_TIMEOUT", "IDLE_TIMEOUT", "MAX_CONNECTIONS"))}
    assert found <= set(settings.NUMBERS), found - set(settings.NUMBERS)
    for name, (kind, low, high, _, _) in settings.NUMBERS.items():
        assert kind in (int, float) and low < high and high <= max(settings.DAY, 1 << 40), name


def test_a_value_not_finite_not_its_kind_or_out_of_bounds_is_refused_naming_the_setting():
    for raw in BAD_FLOATS:
        try:
            settings.parse("KG_SUBJECT_CALL_TIMEOUT", raw)
        except settings.BadSetting as e:
            assert "KG_SUBJECT_CALL_TIMEOUT" in str(e) and repr(raw) in str(e), e
        else:
            raise AssertionError(f"KG_SUBJECT_CALL_TIMEOUT={raw!r} accepted")
    for raw in ("nan", "inf", "-1", "abc"):
        try:
            settings.parse("KG_RDFLIB_LOCK_TIMEOUT", raw)
        except settings.BadSetting:
            continue
        raise AssertionError(f"KG_RDFLIB_LOCK_TIMEOUT={raw!r} accepted")
    assert settings.parse("KG_RDFLIB_LOCK_TIMEOUT", "0") == 0.0   # 0: wait for no other writer, as before
    assert settings.parse("KG_MCP_PORT", "0") == 0   # 0: the system picks a free port, as the tests and tools ask
    for raw in ("abc", "99999", "-1", "65536", "18766.0"):
        try:
            settings.parse("KG_MCP_PORT", raw)
        except settings.BadSetting:
            continue
        raise AssertionError(f"KG_MCP_PORT={raw!r} accepted")
    assert settings.parse("KG_SUBJECT_CALL_TIMEOUT", " 12.5 ") == 12.5 and settings.parse("KG_MCP_PORT", "18766") == 18766
    for uri in ("bolt://localhost:99999", "bolt://h:0", "bolt://h:-1"):
        try:
            settings.neo4j_uri({"KG_NEO4J_URI": uri})
        except settings.BadSetting as e:
            assert "KG_NEO4J_URI" in str(e)
            continue
        raise AssertionError(f"{uri} accepted")
    assert settings.neo4j_uri({"KG_NEO4J_URI": "bolt://neo4j:7687"}) == "bolt://neo4j:7687"
    assert settings.neo4j_uri({}) == "bolt://localhost:7687"


def test_each_reader_goes_through_the_parser():
    """AC1: the limits, the call timeout, the rdflib lock, the worker's job seconds and _num all refuse nan."""
    import execution
    import mcp_server
    import worker
    keep = dict(os.environ)
    try:
        for prefix in ("KG_MCP", "KG_PAGE"):
            for name, raw in (("READ_TIMEOUT", "inf"), ("IDLE_TIMEOUT", "nan"), ("MAX_BODY", "-5"), ("MAX_CONNECTIONS", "0")):
                os.environ[f"{prefix}_{name}"] = raw
                try:
                    hb.Limits.from_env(prefix, max_body=1024)
                except settings.BadSetting as e:
                    assert f"{prefix}_{name}" in str(e)
                else:
                    raise AssertionError(f"{prefix}_{name}={raw} accepted")
                del os.environ[f"{prefix}_{name}"]
        os.environ["KG_WORKER_MEMORY"] = "garbage"
        try:
            worker._num("KG_WORKER_MEMORY", 4 << 30)
        except settings.BadSetting:
            pass
        else:
            raise AssertionError("worker._num read garbage as its default")
        del os.environ["KG_WORKER_MEMORY"]
        src = {p: (ROOT / "harness" / p).read_text(encoding="utf-8") for p in ("mcp_server.py", "execution.py", "store_rdflib.py")}
        assert 'float(os.environ.get("KG_SUBJECT_CALL_TIMEOUT")' not in src["mcp_server.py"]
        assert 'os.environ.get("KG_WORKER_JOB_SECONDS")' not in src["execution.py"]
        assert 'float(os.environ.get("KG_RDFLIB_LOCK_TIMEOUT")' not in src["store_rdflib.py"]
        assert mcp_server.CHILD_TIMEOUT == 300.0 and execution.JOB_SECONDS == 900.0
    finally:
        os.environ.clear()
        os.environ.update(keep)


def test_the_defaults_are_unchanged():
    """AC4: unset, every setting reads what it read before."""
    import execution
    import mcp_server
    import worker
    env = {}
    assert settings.number("KG_SUBJECT_CALL_TIMEOUT", env=env) == mcp_server.CHILD_TIMEOUT == 300.0
    rdflib_src = (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")   # read, not imported: no rdflib here
    assert settings.number("KG_RDFLIB_LOCK_TIMEOUT", env=env) == 60.0 and "\nLOCK_TIMEOUT = 60.0 " in rdflib_src
    assert settings.number("KG_WORKER_JOB_SECONDS", env=env) == execution.JOB_SECONDS == 900.0
    assert settings.number("KG_WORKER_MAX_JOB_SECONDS", env=env) == worker.JOB_MAX_SECONDS
    assert settings.number("KG_MCP_PORT", env=env) == mcp_server.DEFAULT_PORT == 8765
    assert settings.number("KG_DEMO_PORT", env=env) == 8080
    assert (settings.number("KG_WORKER_MEMORY", env=env), settings.number("KG_WORKER_PROCESSES", env=env),
            settings.number("KG_WORKER_FILE_BYTES", env=env)) == (4 << 30, 128, 64 << 20)
    keep = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith(("KG_MCP_", "KG_PAGE_"))}
    try:
        assert hb.Limits.from_env("KG_MCP", max_body=4 << 20) == hb.Limits(4 << 20, 10.0, 5.0, 32, 16 << 20)
        assert hb.Limits.from_env("KG_PAGE", max_body=65536, max_response=8 << 20) == hb.Limits(65536, 10.0, 5.0, 32, 8 << 20)
    finally:
        os.environ.update(keep)


def test_mcp_server_refuses_each_bad_setting_at_start_with_exit_2():
    """AC1, AC2: the re-probe's forms, and the limits, each exit 2 naming the setting, no traceback."""
    for raw in ("abc", "99999", "-1", "18766.0"):
        assert _refused(_run(SERVER, {"KG_MCP_PORT": raw}, "--http"), "KG_MCP_PORT"), raw
    p = _run(SERVER, {}, "--http", "--port", "70000")
    assert p.returncode == 2 and "--port" in p.stderr and "Traceback" not in p.stderr, p.stderr
    for raw in ("nan", "inf", "0", "abc"):
        assert _refused(_run(SERVER, {"KG_SUBJECT_CALL_TIMEOUT": raw}), "KG_SUBJECT_CALL_TIMEOUT"), raw
    for var, raw in (("KG_MCP_MAX_BODY", "-5"), ("KG_MCP_MAX_CONNECTIONS", "0"), ("KG_MCP_READ_TIMEOUT", "-1"),
                     ("KG_MCP_READ_TIMEOUT", "inf"), ("KG_MCP_IDLE_TIMEOUT", "nan")):
        assert _refused(_run(SERVER, {var: raw}, "--http"), var), (var, raw)
    assert _refused(_run(RUNS, {"KG_SUBJECT_CALL_TIMEOUT": "nan"}), "KG_SUBJECT_CALL_TIMEOUT")


def test_a_blank_token_is_no_token_so_a_wide_bind_refuses_and_writes_refuse():
    """AC3: KG_MCP_TOKEN=' ' no longer permits 0.0.0.0; KG_PAGE_TOKEN=' ' reads as unset, so a page published
    beyond this machine refuses writes, and knowgov-runs sends no blank bearer."""
    for blank in (" ", "\t", "  \n"):
        p = _run(SERVER, {"KG_MCP_HOST": "0.0.0.0", "KG_MCP_TOKEN": blank}, "--http")
        assert p.returncode == 2 and "refusing to bind" in p.stderr, (blank, p.stderr)
        assert settings.token("KG_PAGE_TOKEN", {"KG_PAGE_TOKEN": blank}) is None
    assert settings.token("KG_MCP_TOKEN", {"KG_MCP_TOKEN": " tok "}) == "tok"
    import mcp_runs
    import server
    keep = {k: os.environ.get(k) for k in ("KG_PAGE_TOKEN", "KG_BIND")}
    try:
        os.environ.update(KG_PAGE_TOKEN="  ", KG_BIND="0.0.0.0")
        assert server.page_token() is None and server.write_refusal() is not None
        assert server.write_guard({"Authorization": "Bearer "})[0] == 403
        assert mcp_runs.Page(url="http://127.0.0.1:9")._token is None
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def test_the_page_and_the_worker_refuse_a_bad_setting_at_start_with_exit_2():
    """AC2: the page's port, limits and store port; the worker's limits: exit 2 naming it, before a bind."""
    for var, raw in (("KG_DEMO_PORT", "abc"), ("KG_PAGE_READ_TIMEOUT", "nan"), ("KG_PAGE_MAX_BODY", "0"),
                     ("KG_NEO4J_URI", "bolt://localhost:99999")):
        assert _refused(_run(PAGE, {var: raw}, timeout=120), var), (var, raw)
    assert _refused(_run(WORKER, {"KG_WORKER_MEMORY": "lots"}, "--attest-only"), "KG_WORKER_MEMORY")


def test_the_changelog_names_it():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    assert log.startswith(("Unreleased", "0.9.0 ")) and "task-0264" in log   # released in 0.9.0
