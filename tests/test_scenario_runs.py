"""Task-0128 (doc-0016 item 1): ``scenario_runs``, a seventh read-only MCP tool, through
``harness/runs_index.py``, the one reader of the run folders that the page's ``list_runs`` and
``sources_for`` read through too; ``store_status.loaded_at``; and the F2 refusal while a run.json of
the server's subject reads running with a live heartbeat (coordinator, 2026-11-04: the Runner beats
every 30 s, a reader counts 120 s, the page closes a stale one at start as failed)."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import mcp_server  # noqa: E402
import page_subject  # noqa: E402
import review  # noqa: E402
import runs_index  # noqa: E402
import schema_check  # noqa: E402
import server  # noqa: E402
import subject as subject_mod  # noqa: E402
import views  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402
from test_mcp_server import Stub, _Day  # noqa: E402

JEF = subject_mod.Subject(ROOT / "subjects" / "jef_data_load")
NOW = "2026-11-04T22:00:00+00:00"
SCHEMA = schema_check.load("run")


class _Env:
    """Environment variables for the block, as they were after."""
    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kw}
        for k, v in self.kw.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def __exit__(self, *exc):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _run_json(folder: Path, **kw) -> dict:
    j = {"version": 2, "id": folder.name, "subject": folder.parent.name, "scenario": "S1", "mode": "deterministic", "n": 1,
         "row": None, "model": None, "effort": None, "host": None, "model_deviation": False, "as_of": None, "by": "page",
         "started": "2026-11-04T21:58:00+00:00", "heartbeat_at": "2026-11-04T21:59:30+00:00", "finished": None,
         "status": "running", "exit_code": None, "error": None, "source": f"demo-runs/{folder.parent.name}/{folder.name}",
         "log": "S1-deterministic.log"}
    j.update(kw)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "run.json").write_text(json.dumps(j), encoding="utf-8")
    assert schema_check.validate(j, SCHEMA) == [], schema_check.validate(j, SCHEMA)
    return j


def _tools(runs: Path, stub=None):
    stub = stub or Stub()
    return mcp_server.Tools(opener=lambda: mcp_server.ReadOnlyStore(stub), runs=runs)


def _call(tools, name, args=None):
    srv = mcp_server.Server(tools)
    with _Day():
        from tests.test_mcp_server import _as_result   # a schema violation is refused before dispatch, -32602 (task-0281)
        return _as_result(srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args or {}}}))


# ------------------------------------------------------------------ AC 1: the record per subject

def test_cargo_quote_lists_s1_to_s7_with_the_records_arms_at_five_and_s6s_three_sources():
    got = runs_index.scenario_runs(CARGO_QUOTE, ROOT / "nonexistent-demo-runs")
    assert [s["id"] for s in got] == ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
    for s in got:
        rec = s["record"][0]
        assert rec["id"] == "record" and rec["deterministic"] and rec["gate"] in ("PROCEED", "QUALIFIED", "BLOCKED"), (s["id"], rec)
        assert rec["arms"]["G"]["n"] == 5 and rec["arms"]["B"]["n"] == 5, (s["id"], rec["arms"])
        assert rec["arms"]["G"]["models"] == [CARGO_QUOTE.record_model], rec["arms"]["G"]["models"]
        assert s["title"] and s["line"] and s["runs"] == [] and s["runs_total"] == 0
    s6 = next(s for s in got if s["id"] == "S6")
    assert [r["id"] for r in s6["record"]] == ["record", "rerun", "d3check"]
    assert s6["record"][2]["deterministic"]


def test_jef_lists_c_and_d1_to_d5_deterministic_only():
    got = runs_index.scenario_runs(JEF, ROOT / "nonexistent-demo-runs")
    assert [s["id"] for s in got] == ["C", "D1", "D2", "D3", "D4", "D5"]
    for s in got:
        assert [r["id"] for r in s["record"]] == ["record"] and s["record"][0]["deterministic"], s["id"]
        assert s["record"][0]["arms"] is None, f"{s['id']}: the record ran no arm"


# ------------------------------------------------------------------ AC 2: a page run appears

def test_a_page_run_appears_with_its_mode_as_of_by_and_the_gate_verdict_of_its_results():
    results = CARGO_QUOTE.record_dir / "S1" / "deterministic.json"

    class _Proc:
        def wait(self):
            return 0

    def popen(cmd, **_):
        out = Path(cmd[cmd.index("--out") + 1]) / "S1"
        out.mkdir(parents=True)
        det = json.loads(results.read_text(encoding="utf-8"))
        det["as_of"] = "2027-09-01"
        (out / "deterministic.json").write_text(json.dumps(det), encoding="utf-8")
        return _Proc()
    keep = server.subprocess.Popen, server.RUNS_DIR
    with tempfile.TemporaryDirectory() as td:
        server.subprocess.Popen, server.RUNS_DIR = popen, Path(td)
        runner = server.Runner()
        try:
            with page_subject.using(CARGO_QUOTE):
                rec = runner.start("S1", "deterministic", 1, as_of="2027-09-01", by="mcp")
            runner.join()
            got = runs_index.scenario_runs(CARGO_QUOTE, Path(td), "S1")
        finally:
            server.subprocess.Popen, server.RUNS_DIR = keep
    det = json.loads(results.read_text(encoding="utf-8"))
    (s1,) = got
    (run,) = s1["runs"]
    assert (run["id"], run["mode"], run["as_of"], run["by"], run["status"], run["exit_code"]) == \
        (f"cargo_quote/{rec['id']}", "deterministic", "2027-09-01", "mcp", "done", 0), run
    assert run["gate"] == det["D6_gate"]["verdict"] and run["results"] and not run["inferred"]
    assert run["source"] == rec["source"] and run["started"] == rec["started"]


def test_a_folder_without_run_json_is_inferred_and_a_failed_run_with_no_results_still_shows():
    with tempfile.TemporaryDirectory() as td:
        runs = Path(td)
        old = runs / "cargo_quote" / "2026-11-01-1000" / "S2"
        old.mkdir(parents=True)
        (old / "deterministic.json").write_bytes((CARGO_QUOTE.record_dir / "S2" / "deterministic.json").read_bytes())
        _run_json(runs / "cargo_quote" / "2026-11-04-2100", scenario="S2", status="failed", exit_code=1,
                  finished="2026-11-04T21:01:00+00:00")
        _run_json(runs / "cargo_quote" / "2026-11-04-2200", scenario="S3", status="done", exit_code=0)
        (s2,) = runs_index.scenario_runs(CARGO_QUOTE, runs, "S2")
    assert [r["id"] for r in s2["runs"]] == ["cargo_quote/2026-11-04-2100", "cargo_quote/2026-11-01-1000"], "newest first, S3's left out"
    failed, inferred = s2["runs"]
    assert failed["status"] == "failed" and failed["results"] is False and failed["gate"] is None and not failed["inferred"]
    assert inferred["inferred"] and inferred["status"] is None and inferred["by"] is None and inferred["mode"] == "deterministic"


# ------------------------------------------------------------------ AC 3: the page's reads unchanged

def _old_sources_for(ps, scenario, runs_dir):
    """views.sources_for as it was before task-0128, kept here as the oracle."""
    out = [{"id": "record", "label": "the record (results/)", "dir": str(ps.record_dir / scenario)}]
    for s in ps.subject.scenarios.get(scenario, {}).get("sources", []):
        out.append({"id": s["id"], "label": s["label"], "dir": str(ps.record_dir / s["dir"])})
    for base, prefix in ((runs_dir / ps.id, f"demo-runs/{ps.id}/"), (runs_dir, "demo-runs/")):
        if not base.exists():
            continue
        for d in sorted(base.iterdir(), reverse=True):
            if (d / scenario / "deterministic.json").exists():
                arm_files = sorted((d / scenario).glob("run*_[GB].json"))
                mode = "arms" if arm_files else "deterministic"
                models = sorted({m for m in (views._model_of(json.loads(f.read_text(encoding="utf-8"))) for f in arm_files) if m})
                tag = mode + (", " + ", ".join(models) if models else "")
                out.append({"id": f"{prefix}{d.name}", "label": f"demo run {d.name} ({tag})", "dir": str(d / scenario)})
    return out


def _old_list_runs(ps, runs_dir):
    """server.list_runs as task-0127 left it, kept here as the oracle."""
    out = []
    for base, prefix in ((runs_dir / ps.id, f"{ps.id}/"), (runs_dir, "")):
        if not base.exists():
            continue
        for d in sorted(base.iterdir(), reverse=True):
            if not d.is_dir():
                continue
            scenarios = sorted(p.name for p in d.iterdir() if p.is_dir() and p.name in ps.scenarios and (p / "deterministic.json").exists())
            if not scenarios:
                continue
            modes = sorted({("arms" if list((d / s).glob("run*_G.json")) else "deterministic") for s in scenarios})
            entry = {"id": prefix + d.name, "scenarios": scenarios, "modes": modes, "logs": sorted(p.name for p in d.glob("*.log"))}
            try:
                run = json.loads((d / "run.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                run = None
            if isinstance(run, dict):
                entry["modes"] = [run["mode"]] if run.get("mode") in ("deterministic", "arms") else modes
                entry["run"] = run
            out.append(entry)
    return out


def test_the_pages_runs_and_sources_are_unchanged_byte_for_byte():
    rec = CARGO_QUOTE.record_dir
    with tempfile.TemporaryDirectory() as td:
        runs = Path(td)
        arms = runs / "cargo_quote" / "2026-11-02-1000" / "S6"
        arms.mkdir(parents=True)
        for f in ("deterministic.json", "run1_G.json", "run1_B.json"):
            (arms / f).write_bytes((rec / "S6" / f).read_bytes())
        (arms.parent / "S6-arms.log").write_text("", encoding="utf-8")
        for stamp, sc in (("2026-11-03-1000", "S1"), ("2026-11-04-1000", "S6")):
            d = runs / "cargo_quote" / stamp / sc
            d.mkdir(parents=True)
            (d / "deterministic.json").write_bytes((rec / sc / "deterministic.json").read_bytes())
        _run_json(runs / "cargo_quote" / "2026-11-04-1000", scenario="S6", status="done", exit_code=0)
        flat = runs / "2026-10-30-1700" / "S6"
        flat.mkdir(parents=True)
        (flat / "deterministic.json").write_bytes((rec / "S6" / "deterministic.json").read_bytes())
        _run_json(runs / "cargo_quote" / "2026-11-04-2300", status="failed", error="the run could not start: x")   # no results
        with page_subject.using(CARGO_QUOTE):
            ps = page_subject.current()
            keep = server.RUNS_DIR
            server.RUNS_DIR = runs
            try:
                assert json.dumps(server.list_runs()) == json.dumps(_old_list_runs(ps, runs))
            finally:
                server.RUNS_DIR = keep
            for sc in ps.order:
                assert json.dumps(views.sources_for(sc, runs)) == json.dumps(_old_sources_for(ps, sc, runs)), sc
            assert [s["id"] for s in views.sources_for("S6", runs)] == [
                "record", "rerun", "d3check", "demo-runs/cargo_quote/2026-11-04-1000", "demo-runs/cargo_quote/2026-11-02-1000",
                "demo-runs/2026-10-30-1700"]
            assert views.scenario_list(runs) == [dict(x, sources=[s["id"] for s in _old_sources_for(ps, x["id"], runs)]) for x in views.scenario_list(runs)]
    for mod in ("server.py", "views.py"):
        assert "runs_index." in (ROOT / "demo" / "app" / mod).read_text(encoding="utf-8"), f"{mod} reads the run folders through runs_index"


# ------------------------------------------------------------------ AC 4: the F2 refusal, the heartbeat

def _live_and_stale(runs: Path, heartbeat: str):
    from subject import SUBJECT
    return _run_json(runs / SUBJECT.id / "2026-11-04-2158", scenario=SUBJECT.order[0], heartbeat_at=heartbeat)


def test_a_live_run_refuses_the_three_scenario_reading_tools_naming_the_run():
    from subject import SUBJECT
    key = SUBJECT.three_valued[0] if SUBJECT.three_valued else "S-review|notified"
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        run = _live_and_stale(Path(td), "2026-11-04T21:59:30+00:00")   # 30 s old: live
        tools = _tools(Path(td))
        for name, args in (("gate_verdict", {}), ("three_valued_answer", {"key": key}), ("evidence_bundle", {})):
            r = _call(tools, name, args)
            text = r["content"][0]["text"]
            assert r["isError"] and "a run is loading the store" in text and f"{SUBJECT.id}/{run['id']}" in text, (name, text)
        r = _call(tools, "scenario_runs")
        j = r["structuredContent"]
        assert not r["isError"] and j["run_in_progress"]["id"] == run["id"] and j["held"] is None and "store_skipped" in j
        assert not _call(tools, "store_status")["isError"], "store_status still answers: it names what is held, not keys"


def test_a_stale_running_run_json_is_not_live_and_the_page_closes_it_at_start():
    from subject import SUBJECT
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        runs = Path(td)
        _live_and_stale(runs, "2026-11-04T21:57:59+00:00")   # 121 s old: stale
        tools = _tools(runs)
        r = _call(tools, "gate_verdict")
        assert not r["isError"], r["content"][0]["text"]
        assert _call(tools, "scenario_runs")["structuredContent"]["run_in_progress"] is None
        live = _run_json(runs / "jef_data_load" / "2026-11-04-2159", scenario="C", heartbeat_at="2026-11-04T21:59:50+00:00")
        keep = server.RUNS_DIR, server._now
        server.RUNS_DIR, server._now = runs, lambda: NOW
        try:
            closed = server.close_stale_runs()
        finally:
            server.RUNS_DIR, server._now = keep
        assert closed == [f"{SUBJECT.id}/2026-11-04-2158"], closed
        j = json.loads((runs / SUBJECT.id / "2026-11-04-2158" / "run.json").read_text(encoding="utf-8"))
        assert (j["status"], j["error"], j["finished"]) == ("failed", "page restarted", NOW) and schema_check.validate(j, SCHEMA) == []
        assert json.loads((runs / "jef_data_load" / "2026-11-04-2159" / "run.json").read_text(encoding="utf-8")) == live, "a live run is left"


def test_another_subjects_live_run_does_not_refuse_this_servers_gate():
    from subject import SUBJECT
    other = "jef_data_load" if SUBJECT.id != "jef_data_load" else "cargo_quote"
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        _run_json(Path(td) / other / "2026-11-04-2159", heartbeat_at="2026-11-04T21:59:50+00:00")
        assert not _call(_tools(Path(td)), "gate_verdict")["isError"]


def test_the_heartbeat_reads_the_pinned_clock_and_refuses_the_wall_clock():
    with _Env(KG_NOW=None, KG_CLOCK="pinned"):
        try:
            review.now()
            raise AssertionError("KG_CLOCK=pinned with no KG_NOW read the wall clock")
        except review.WallClock as e:
            assert "task-0128" in str(e)
        with tempfile.TemporaryDirectory() as td:
            assert runs_index.run_in_progress("cargo_quote", Path(td)) is None, "no running run.json: the clock is never asked"
            _run_json(Path(td) / "cargo_quote" / "2026-11-04-2158")
            r = _call(_tools(Path(td)), "gate_verdict") if __import__("subject").SUBJECT.id == "cargo_quote" else None
            if r is not None:
                assert r["isError"] and "cannot be read against the clock" in r["content"][0]["text"]
    with _Env(KG_NOW="2026-11-04T22:00:00"):
        assert review.now() == dt.datetime(2026, 11, 4, 22, 0, tzinfo=dt.timezone.utc), "a naive KG_NOW is UTC"
    run = {"status": "running", "started": "2026-11-04T21:00:00+00:00"}   # version 1: no heartbeat, its start stands
    assert runs_index.is_live(run, dt.datetime(2026, 11, 4, 21, 2, tzinfo=dt.timezone.utc))
    assert not runs_index.is_live(run, dt.datetime(2026, 11, 4, 21, 2, 1, tzinfo=dt.timezone.utc))
    assert not runs_index.is_live(dict(run, status="done"), dt.datetime(2026, 11, 4, 21, 0, tzinfo=dt.timezone.utc))


def test_the_runner_beats_while_the_run_is_under_way_and_never_after_its_end():
    release = threading.Event()

    class _Proc:
        def wait(self):
            release.wait(10)
            return 0
    keep = server.subprocess.Popen, server.RUNS_DIR, server.Runner._heartbeat
    beats = []

    def quick(rec, ended, every=runs_index.HEARTBEAT_S):
        assert every == 30
        keep[2](rec, ended, every=0.05)
    with tempfile.TemporaryDirectory() as td:
        server.subprocess.Popen, server.RUNS_DIR = (lambda cmd, **_: _Proc()), Path(td)
        server.Runner._heartbeat = staticmethod(quick)
        runner = server.Runner()
        try:
            with page_subject.using(CARGO_QUOTE):
                rec = runner.start("S1", "deterministic", 1)
            f = Path(rec["out_dir"]) / "run.json"
            first = json.loads(f.read_text(encoding="utf-8"))
            assert first["heartbeat_at"] == first["started"] and first["version"] == 2
            for _ in range(200):
                j = json.loads(f.read_text(encoding="utf-8"))
                beats.append(j["heartbeat_at"])
                if len(set(beats)) > 1 or j["heartbeat_at"] != first["started"]:
                    break
                release.wait(0.02)
            release.set()
            runner.join()
            end = json.loads(f.read_text(encoding="utf-8"))
            assert end["status"] == "done" and schema_check.validate(end, SCHEMA) == []
            assert server.beat(runner.current) is False and json.loads(f.read_text(encoding="utf-8")) == end, "no beat after the end"
        finally:
            server.subprocess.Popen, server.RUNS_DIR = keep[:2]
            server.Runner._heartbeat = keep[2]


# ------------------------------------------------------------------ the tool itself

def test_scenario_runs_is_read_only_takes_no_path_and_store_status_names_loaded_at():
    from subject import SUBJECT
    t = next(x for x in mcp_server.TOOLS if x["name"] == "scenario_runs")
    assert t["annotations"] == mcp_server.READ_ONLY and set(t["inputSchema"]["properties"]) == {"scenario", "limit", "subject"}
    with tempfile.TemporaryDirectory() as td:
        tools = _tools(Path(td))
        j = _call(tools, "scenario_runs")["structuredContent"]
        assert [s["id"] for s in j["scenarios"]] == list(SUBJECT.order) and j["run_in_progress"] is None
        assert j["held"] == {"scenario": SUBJECT.order[0], "version": "v1", "stage": 1, "loaded_at": "2026-11-04T19:45:00+00:00"}
        assert "not a run" in j["replay"]
        one = _call(tools, "scenario_runs", {"scenario": SUBJECT.order[-1], "limit": 1})["structuredContent"]
        assert [s["id"] for s in one["scenarios"]] == [SUBJECT.order[-1]]
        for bad in ({"scenario": "nope"}, {"limit": 0}, {"limit": True}):
            assert _call(tools, "scenario_runs", bad)["isError"], bad
        st = _call(tools, "store_status")["structuredContent"]
        assert st["loaded_at"] == "2026-11-04T19:45:00+00:00"
        assert _call(_tools(Path(td), Stub(scenario=None)), "store_status")["structuredContent"]["loaded_at"] is None
    assert "extraction_times" in mcp_server.READS
