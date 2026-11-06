"""Task-0127 (doc-0016 F3): a run folder describes itself. The page's Runner writes
``runs/<subject>/<stamp>/run.json`` when a run starts and again when it ends, with who asked
(``by``), and never a key or the page's token; ``/api/runs`` carries it where present and is as
before for a folder without one; ``harness/schemas/run.schema.json`` pins it."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import page_subject  # noqa: E402
import schema_check  # noqa: E402
import server  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402

SCHEMA = schema_check.load("run")


class _Proc:
    def __init__(self, code):
        self.code, self.waited = code, False

    def wait(self):
        self.waited = True
        return self.code


def _run(td: Path, code=0, popen=None, **kw):
    """Start a run on a stub process; return (the start's reply, the run.json at start, the runner)."""
    seen = {}

    def default(cmd, cwd=None, stdout=None, stderr=None, env=None):
        seen["at_start"] = json.loads((Path(cmd[cmd.index("--out") + 1]) / "run.json").read_text(encoding="utf-8"))
        seen["env"] = env
        return _Proc(code)
    keep = server.subprocess.Popen, server.RUNS_DIR, server.threading.Thread
    server.subprocess.Popen, server.RUNS_DIR = popen or default, td

    class _Inline:   # the waiter runs at once, so the end is written before start returns; no heartbeat thread
        def __init__(self, target, args, daemon):
            self.target, self.args = target, args

        def start(self):
            if getattr(self.target, "__name__", "") != "_heartbeat":
                self.target(*self.args)

        def is_alive(self):
            return False
    server.threading.Thread = _Inline
    try:
        runner = server.Runner()
        with page_subject.using(CARGO_QUOTE):
            rec = runner.start("S1", kw.pop("mode", "deterministic"), 1, **kw)
        return rec, seen, runner
    finally:
        server.subprocess.Popen, server.RUNS_DIR, server.threading.Thread = keep


def _folder(td: Path) -> Path:
    (d,) = [p for p in (td / "cargo_quote").iterdir() if p.is_dir()]
    return d


def test_the_run_writes_run_json_at_start_and_again_at_its_end():
    with tempfile.TemporaryDirectory() as td:
        rec, seen, runner = _run(Path(td), as_of="2027-09-01")
        start = seen["at_start"]
        assert start["status"] == "running" and start["finished"] is None and start["exit_code"] is None, start
        assert (start["subject"], start["scenario"], start["mode"], start["n"], start["by"]) == ("cargo_quote", "S1", "deterministic", 1, "page")
        assert start["as_of"] == "2027-09-01" and start["log"] == "S1-deterministic.log" and start["source"] == rec["source"]
        end = json.loads((_folder(Path(td)) / "run.json").read_text(encoding="utf-8"))
        assert end["status"] == "done" and end["exit_code"] == 0 and end["finished"], end
        assert {k: end[k] for k in end if k not in ("status", "exit_code", "finished")} == {k: start[k] for k in start if k not in ("status", "exit_code", "finished")}
        assert not (_folder(Path(td)) / "run.json.tmp").exists(), "written whole, by a rename"
        for j in (start, end):
            assert schema_check.validate(j, SCHEMA) == [], schema_check.validate(j, SCHEMA)
        assert runner.history[-1]["status"] == "done"


def test_a_failed_run_and_a_run_that_never_started_both_say_so():
    with tempfile.TemporaryDirectory() as td:
        _run(Path(td), code=3)
        end = json.loads((_folder(Path(td)) / "run.json").read_text(encoding="utf-8"))
        assert end["status"] == "failed" and end["exit_code"] == 3 and schema_check.validate(end, SCHEMA) == []

    def no_python(cmd, **_):
        raise FileNotFoundError(2, "No such file or directory")
    with tempfile.TemporaryDirectory() as td:
        try:
            _run(Path(td), popen=no_python)
        except RuntimeError as e:
            assert "could not start" in str(e), e
        else:
            raise AssertionError("a start whose process cannot be spawned is refused")
        j = json.loads((_folder(Path(td)) / "run.json").read_text(encoding="utf-8"))
        assert j["status"] == "failed" and j["exit_code"] is None and j["finished"] and "could not start" in j["error"], j
        assert schema_check.validate(j, SCHEMA) == []


def test_by_names_who_asked_and_nothing_else_is_admitted():
    with tempfile.TemporaryDirectory() as td:
        _run(Path(td), by="mcp")
        assert json.loads((_folder(Path(td)) / "run.json").read_text(encoding="utf-8"))["by"] == "mcp"
    with tempfile.TemporaryDirectory() as td:
        try:
            _run(Path(td), by="cron")
        except ValueError as e:
            assert "by must be one of" in str(e)
        else:
            raise AssertionError("an unknown initiator is refused")
        assert not (Path(td) / "cargo_quote").exists(), "refused before any folder is made"
    src = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert 'by=r["by"] or "page"' in src, "POST /api/run passes by (typed by run_request, task-0141.04); the page's buttons send none"


def test_run_json_carries_no_secret():
    """An arms run with a key variable and the page's token both set: neither value is anywhere in run.json."""
    key_var, key, token = "KG_TEST_RUN_JSON_KEY", "sk-test-run-json-0127-not-a-real-key", "page-token-0127-not-real"
    row = {"id": "test-row", "model": "test-model", "host": "api.example.test", "key_var": key_var}
    env = {"KG_MODEL_BASE_URL": "https://api.example.test/v1", "KG_MODEL_API_KEY_VAR": key_var,
           "KG_ARMS_MODEL": "test-model", "KG_ARMS_EFFORT": "low", "KG_THINKING_UNCOUNTED": ""}
    keep_resolve, keep_env = server.models.resolve, dict(os.environ)
    server.models.resolve = lambda *a: (row, env, True)
    os.environ.update({key_var: key, "KG_PAGE_TOKEN": token})
    try:
        with tempfile.TemporaryDirectory() as td:
            rec, seen, _ = _run(Path(td), mode="arms", row="test-row")
            assert seen["env"].get(key_var) == key, "the process still gets the key through its environment"
            texts = [json.dumps(seen["at_start"]), (_folder(Path(td)) / "run.json").read_text(encoding="utf-8")]
            for text in texts:
                assert key not in text and token not in text, text
                j = json.loads(text)
                assert j["mode"] == "arms" and j["row"] == "test-row" and j["model"] == "test-model" and j["effort"] == "low"
                assert schema_check.validate(j, SCHEMA) == []
            assert not set(json.loads(texts[1])) - set(SCHEMA["properties"]), "no field beyond the schema's"
    finally:
        server.models.resolve = keep_resolve
        os.environ.clear()
        os.environ.update(keep_env)


def test_api_runs_reads_run_json_and_is_unchanged_without_one():
    results = ROOT / "subjects" / "cargo_quote" / "vendor" / "kg_experiment" / "results" / "S1" / "deterministic.json"
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "cargo_quote"
        for stamp in ("2026-11-04-1000", "2026-11-04-1100"):
            (base / stamp / "S1").mkdir(parents=True)
            (base / stamp / "S1" / "deterministic.json").write_bytes(results.read_bytes())
            (base / stamp / "S1-deterministic.log").write_text("", encoding="utf-8")
        keep = server.RUNS_DIR
        server.RUNS_DIR = Path(td)
        try:
            with page_subject.using(CARGO_QUOTE):
                before = server.list_runs()
                assert before == [{"id": f"cargo_quote/{s}", "scenarios": ["S1"], "modes": ["deterministic"], "logs": ["S1-deterministic.log"]}
                                  for s in ("2026-11-04-1100", "2026-11-04-1000")], before
                rec = {"id": "2026-11-04-1100", "subject": "cargo_quote", "scenario": "S1", "mode": "deterministic", "n": 1,
                       "status": "done", "by": "page", "started": "2026-11-04T11:00:00+00:00", "finished": "2026-11-04T11:00:05+00:00",
                       "exit_code": 0, "model_deviation": False, "out_dir": str(base / "2026-11-04-1100"),
                       "log": str(base / "2026-11-04-1100" / "S1-deterministic.log"), "source": "demo-runs/cargo_quote/2026-11-04-1100"}
                server.write_run_json(rec)
                after = server.list_runs()
        finally:
            server.RUNS_DIR = keep
    assert after[1] == before[1], "a folder without run.json is listed as before"
    assert {k: v for k, v in after[0].items() if k != "run"} == before[0]
    assert after[0]["run"]["status"] == "done" and after[0]["run"]["by"] == "page" and schema_check.validate(after[0]["run"], SCHEMA) == []


def test_join_waits_for_the_end_write_so_a_temporary_run_folder_can_go():
    """The race behind a one-off rmtree failure on main: the waiter writes the end-of-run run.json
    after the process returns, and a test's temporary RUNS_DIR could be removed first. Runner.join()
    waits for it; a slow end write proves it."""
    import threading
    import time
    keep = server.subprocess.Popen, server.RUNS_DIR, server.write_run_json
    orig = server.write_run_json

    def slow(rec):
        if rec["status"] != "running":
            time.sleep(0.3)
        orig(rec)
    with tempfile.TemporaryDirectory() as td:
        server.subprocess.Popen = lambda cmd, **_: _Proc(0)
        server.RUNS_DIR, server.write_run_json = Path(td), slow
        runner = server.Runner()
        try:
            with page_subject.using(CARGO_QUOTE):
                runner.start("S1", "deterministic", 1)
            assert isinstance(runner.waiters[-1], threading.Thread)
            runner.join()
            j = json.loads((_folder(Path(td)) / "run.json").read_text(encoding="utf-8"))
            assert j["status"] == "done", "join returned before the end was written"
        finally:
            server.subprocess.Popen, server.RUNS_DIR, server.write_run_json = keep


def test_every_test_that_starts_a_run_joins_it():
    """A test that starts a run on a stub process with RUNS_DIR in a temporary directory joins the
    Runner's waiter before the directory goes (or runs the waiter inline, as this file does)."""
    import re
    for f in sorted(Path(__file__).parent.glob("test_*.py")):
        text = f.read_text(encoding="utf-8")
        if not re.search(r"\.start\(\"S\d", text) or "server.RUNS_DIR" not in text:
            continue
        assert ".join()" in text or "_Inline" in text, f"{f.name} starts a run and never joins its waiter"
