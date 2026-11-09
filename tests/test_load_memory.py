"""task-0176: the heap a Neo4j load needs, stated and checked. A load whose forecast peak transaction memory
exceeds what the server allows is refused before its first write (``load_memory.LoadTooLarge``; gate_cli
and run.py exit 2), naming the setting and both figures; ``KG_LOAD_MEMORY_CHECK=off`` loads anyway; a
store with no such limit is never refused. The forecast is the measured plane in docs/load-memory.json.
The live proof on a server with a small limit is ``tools/check_snapshots.py --memory-limited``."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import load_memory as lm  # noqa: E402

LIMIT = {"bytes": 2 * 2**20, "setting": "db.memory.transaction.max", "value": "2.00MiB"}


class _Env:
    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kw}
        for k, v in self.kw.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def __exit__(self, *exc):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


class _Writer:
    """A writer whose server allows ``limit`` and holds ``published`` statements; every other call is a
    write, recorded."""

    def __init__(self, limit=LIMIT, published=0):
        self.info = {"limit": limit, "published": published}
        self.writes = []

    def transaction_memory(self):
        return self.info

    def wipe(self):
        lm.wiped(self)
        self.writes.append("wipe")

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return lambda *a, **k: self.writes.append(name)


def test_sizes_parse_as_neo4j_prints_them():
    for text, b in (("0B", 0), (None, 0), ("", 0), ("2.00MiB", 2 * 2**20), ("2.34GiB", int(2.34 * 2**30)),
                    ("512m", 512 * 2**20), ("1g", 2**30), ("16k", 16 * 1024), ("1048576", 2**20)):
        assert lm.parse_size(text) == b, (text, lm.parse_size(text))


def test_the_fit_recovers_a_plane_and_lies_on_or_over_every_row():
    rows = [(w, d, 1_000_000 + 10_000 * w + 9_000 * d) for w, d in ((0, 100), (100, 0), (300, 50), (50, 900), (2000, 10))]
    f = lm.fit(rows)
    assert abs(f["per_written"] - 10_000) < 1 and abs(f["per_deleted"] - 9_000) < 1 and abs(f["base"] - 1_000_000) < 5, f
    assert f["r2"] > 0.9999


def test_the_forecast_carries_the_recorded_measurement_and_covers_every_measured_peak():
    doc = json.loads((ROOT / "docs" / "load-memory.json").read_text(encoding="utf-8"))
    f, rows = doc["fit"], doc["rows"]
    assert (lm.BASE, lm.PER_WRITTEN, lm.PER_DELETED) == (f["base_envelope"], round(f["per_written"]), round(f["per_deleted"]))
    assert lm.fit([(r["written"], r["deleted"], r["peak_bytes"]) for r in rows]) == f, "the recorded fit is the fit of the recorded rows"
    assert {r["subject"] for r in rows} == {"cargo_quote", "jef_data_load"} and any("synthetic" in r["unit"] for r in rows)
    assert max(r["written"] + r["deleted"] for r in rows) >= 40_000, "the scale-up reaches well past the public subjects"
    with _Env(KG_LOAD_MEMORY_MARGIN="0"):
        over = [r for r in rows if lm.forecast(r["written"], r["deleted"]) < r["peak_bytes"] - 1024]
    assert not over, f"a measured peak above the forecast with no margin: {over[:2]}"


def test_a_load_over_the_limit_is_refused_before_its_first_write_naming_the_setting_and_both_figures():
    w = _Writer(published=240)
    w.wipe()
    w.writes.clear()
    try:
        lm.note(w, 240)
        raise AssertionError("not refused")
    except lm.LoadTooLarge as e:
        msg = str(e)
    assert w.writes == [], "refused before anything was written"
    assert "db.memory.transaction.max = 2.00MiB" in msg and "the server allows 2.0 MiB" in msg and "MiB (240 statements written and 240 deleted" in msg
    assert "KG_LOAD_MEMORY_CHECK=off" in msg and "previous generation" in msg


def test_the_check_off_a_limit_that_fits_and_a_store_with_no_limit_never_refuse():
    with _Env(KG_LOAD_MEMORY_CHECK="off"):
        lm.note(_Writer(), 10**6)
    lm.note(_Writer(limit={"bytes": 2**40, "setting": "dbms.memory.transaction.total.max", "value": "1TiB"}), 1000)
    lm.note(_Writer(limit=None), 10**7)   # rdflib, and the port's default: nothing bounds the unit
    import store
    assert store.Store().transaction_memory() is None
    for v in ("off", "OFF", "Off"):   # task-0276: the documented word, in any case (never stripped, task-0287)
        with _Env(KG_LOAD_MEMORY_CHECK=v):
            assert not lm.enabled()
    import switches
    for v in ("0", "no", "false", " off"):   # never documented: refused, naming the setting, no longer silently off
        with _Env(KG_LOAD_MEMORY_CHECK=v):
            try:
                lm.enabled()
            except switches.BadSwitch as e:
                assert "KG_LOAD_MEMORY_CHECK" in str(e)
            else:
                raise AssertionError(v)
    with _Env(KG_LOAD_MEMORY_CHECK=None):
        assert lm.enabled()


def test_the_margin_is_a_bounded_setting():
    with _Env(KG_LOAD_MEMORY_MARGIN=None):
        assert lm.margin() == 0.25
    with _Env(KG_LOAD_MEMORY_MARGIN="1"):
        assert lm.forecast(100, 0) == int((lm.BASE + lm.PER_WRITTEN * 100) * 2)
    for bad in ("-1", "5", "lots"):
        with _Env(KG_LOAD_MEMORY_MARGIN=bad):
            try:
                lm.margin()
                raise AssertionError(bad)
            except ValueError as e:
                assert "KG_LOAD_MEMORY_MARGIN" in str(e)


def test_a_unit_counts_every_write_and_what_each_wipe_deletes():
    w = _Writer(limit=None, published=500)
    w.wipe()
    lm.note(w, 200)
    assert lm.counts(w) == {"written": 200, "deleted": 500}
    w.wipe()   # run.py's next scenario: deletes the 200 the unit wrote
    lm.note(w, 300)
    assert lm.counts(w) == {"written": 500, "deleted": 700}
    lm.note(w, 50)   # a second load with no wipe (change.py's stage 2)
    assert lm.counts(w) == {"written": 550, "deleted": 700}


def test_a_run_is_refused_whole_before_its_first_load():
    w = _Writer(published=240)
    try:
        lm.preflight(w, [240, 226, 226])
        raise AssertionError("not refused")
    except lm.LoadTooLarge as e:
        assert "the run's 3 loads in one unit" in str(e) and "692 statements written and 706 deleted" in str(e), str(e)
    assert w.writes == [] and lm.counts(w) == {"written": 0, "deleted": 0}, "preflight notes nothing"
    lm.preflight(_Writer(limit=None), [10**6])


def test_the_load_gate_cli_and_run_py_take_the_refusal_before_any_write_and_exit_2():
    load = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    body = load.split("def load_scenario(", 1)[1]
    # the statements of the bags the load writes (a stage-2 re-load writes only the changed ones, task-0197)
    assert body.index("load_memory.note(st, load_memory.statements(") < body.index("st.ensure_agents("), "before the first write"
    neo = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    assert "load_memory.wiped(self)" in neo.split("    def wipe(self)", 1)[1].split("\n    def ", 1)[0]
    import gate_cli

    class St:
        def commit(self):
            raise AssertionError("published")
    keep = gate_cli._load

    def refuse(st, scenario):
        raise lm.LoadTooLarge("refused before loading: test")
    gate_cli._load = refuse
    try:
        class A:
            no_load, task, fail_on = False, "codegen", "warn"
        try:
            gate_cli._gate_on(St(), A(), None, "S1", None, None, "2026-11-06", None, None)
            raise AssertionError("not refused")
        except gate_cli.CannotRun as e:   # main() prints "gate: cannot run: ..." and returns 2
            assert str(e) == "refused before loading: test"
    finally:
        gate_cli._load = keep
    run = (ROOT / "harness" / "run.py").read_text(encoding="utf-8")
    main = run.split("def main()", 1)[1]
    assert main.index("load_memory.preflight(d, ") < main.index("_run_all(args, d, pv, as_of, out_root, summary)")
    assert "except load_memory.LoadTooLarge as e:" in main and "sys.exit(2)" in main.split("except load_memory.LoadTooLarge", 1)[1][:200]


def test_the_instance_readme_states_the_heap_as_a_function_of_statements():
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    sec = readme[readme.index("## Sizing the Neo4j heap"):]
    sec = sec[:sec.index("\n## ", 5)]
    for t in ("dbms.memory.transaction.total.max", "db.memory.transaction.max", "python harness/load_memory.py",
              "KG_LOAD_MEMORY_CHECK=off", "KG_LOAD_MEMORY_MARGIN", "NEO4J_server_memory_heap_max__size", "statements"):
        assert t in sec, t
