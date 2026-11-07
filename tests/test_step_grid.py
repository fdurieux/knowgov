"""Task-0192 (doc-0024 J3): a step-by-scenario grid over deterministic run folders.

The rows are J1's slices (task-0191), the columns the scenarios a folder holds, each cell the step's keys as
that scenario's gate report in the folder has them. The grid reads files only: no store is opened, loaded or
written, and knowgov-runs is never called. On CargoQuote S1 to S7 each cell agrees with the gate run on a
scratch store of that scenario for the same keys (the rdflib job)."""
from __future__ import annotations

import builtins
import contextlib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import proposal_impact as pi  # noqa: E402
import schema_check  # noqa: E402
import step_grid  # noqa: E402
from subject import SUBJECT  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

SCHEMA = schema_check.load("step-grid")
RECORD = Path(SUBJECT.record_dir)


def _valid(g: dict) -> dict:
    data = json.loads(json.dumps(g, default=str))
    errors = schema_check.validate(data, SCHEMA)
    assert errors == [], errors[:5]
    assert schema_check.validate({**data, "score": 1}, SCHEMA), "an unschematised field passed"
    return data


@contextlib.contextmanager
def _no_store_no_runs():
    """open_store raises, and importing mcp_runs (knowgov-runs) or urllib.request fails: the grid needs neither."""
    import store
    keep, real_import = store.open_store, builtins.__import__

    def refuse(*a, **k):
        raise AssertionError("the grid opened a store")

    def guarded(name, *a, **k):
        if name in ("mcp_runs", "urllib.request"):
            raise AssertionError(f"the grid imported {name}")
        return real_import(name, *a, **k)
    store.open_store, builtins.__import__ = refuse, guarded
    try:
        yield
    finally:
        store.open_store, builtins.__import__ = keep, real_import


def test_the_grid_is_j1s_steps_by_the_folders_scenarios_with_each_steps_keys():
    """AC1: one row per step of J1's slices, its keys the slice's landed keys; one column per scenario folder;
    one cell per step and scenario, its levels the folder's gate_keys for those keys."""
    g = _valid(step_grid.grid([], record=True))
    assert [c["scenario"] for c in g["columns"]] == list(SUBJECT.order) and all(c["source"] == "record" for c in g["columns"])
    assert len(g["cells"]) == len(g["steps"]) * len(g["columns"]) and g["steps"]
    rmap = SUBJECT.register_map()
    for s in g["steps"]:
        r = pi.evaluate(None, today=pi._date(SUBJECT.record_as_of, "as_of"), scope=s["scopes"][0], register_map=rmap)
        sl = next(x for x in r["slices"]["map"] if x["start"]["id"] == s["id"])
        assert s["keys"] == sorted({x["key"] for x in sl["keys"]["rows"] if not x.get("withdrawn")}) and s["of"] == g["denominator"]
    on = {k for s in g["steps"] for k in s["keys"]}
    assert {o["key"] for o in g["off_steps"]} == {r["key"] for r in rmap["row"]} - on
    for c in g["cells"]:
        det = json.loads((RECORD / c["column"].split(":")[1] / "deterministic.json").read_text(encoding="utf-8"))
        keys = next(s["keys"] for s in g["steps"] if s["id"] == c["step"])
        want = {}
        for k in keys:
            if k in det["gate_keys"]:
                lv = det["gate_keys"][k]["level"]
                want[lv] = want.get(lv, 0) + 1
        assert c["levels"] == want and sum(want.values()) + len(c["unread"]) == c["landed"] == len(keys), c
        assert c["findings"]["blocked"] == sorted(set(keys) & set(det["D6_gate"]["blocked_keys"]))
    if SUBJECT.id == "cargo_quote":
        by = {(c["step"], c["column"]): c for c in g["cells"]}
        assert [s["id"] for s in g["steps"]] == ["JRN-0002", "JRN-0003"] and g["scopes"] == ["JRN-0001"]
        assert (by[("JRN-0002", "record:S1")]["worst"], by[("JRN-0002", "record:S2")]["worst"]) == ("approved", "absent")
        assert by[("JRN-0002", "record:S4")]["worst"] == "disputed" and g["columns"][3]["conflicts"] > 0
        st2 = {sid: by[(sid, "record:S6")]["stage2"]["gate_before_reverification"]["stale"] for sid in ("JRN-0002", "JRN-0003")}
        assert st2["JRN-0003"] and not st2["JRN-0002"], st2   # S6's change reprices: the quote's step, not the request's
    text = step_grid.render_text(g)
    assert "never a score" in text and g["steps"][0]["id"] in text


def test_it_never_opens_a_store_nor_calls_knowgov_runs_and_leaves_the_configured_store_as_it_was():
    """AC2: in process with open_store refused and knowgov-runs unimportable; as a command beside a configured
    rdflib store file, whose bytes and timestamp do not move, and with KG_STORE=neo4j at an address nothing
    serves, which it never tries."""
    with _no_store_no_runs():
        g = step_grid.grid([], record=True)
    assert g["store"] is None and g["stored"] is False
    with tempfile.TemporaryDirectory() as d:
        store = Path(d) / "shared.ttl"
        store.write_text("@prefix kg: <urn:kg:> .\nkg:held kg:scenario \"S1\" .\n", encoding="utf-8")
        before = (hashlib.sha256(store.read_bytes()).hexdigest(), store.stat().st_mtime_ns)
        for extra in ({"KG_STORE": "rdflib", "KG_RDFLIB_FILE": str(store)},
                      {"KG_STORE": "neo4j", "KG_NEO4J_URI": "bolt://127.0.0.1:9", "KG_PAGE_URL": "http://127.0.0.1:9"}):
            p = subprocess.run([sys.executable, str(ROOT / "harness" / "step_grid.py"), "--record", "-f", "json"],
                               capture_output=True, text=True, env={**os.environ, "KG_CLOCK": "pinned", **extra}, timeout=300)
            assert p.returncode == 0, p.stderr[-500:]
            _valid(json.loads(p.stdout))
        assert (hashlib.sha256(store.read_bytes()).hexdigest(), store.stat().st_mtime_ns) == before
        assert sorted(x.name for x in Path(d).iterdir()) == ["shared.ttl"]   # no lock, no generation, no copy
    src = (ROOT / "harness" / "step_grid.py").read_text(encoding="utf-8")
    assert "open_store" not in src and "mcp_runs" not in src and "start_run" not in src.replace("``start_run``", "")


def test_a_folder_that_holds_no_run_is_refused_with_2():
    with tempfile.TemporaryDirectory() as d:
        for args in ([d], [], [str(Path(d) / "nothing")], ["--record", "--scope", "APP-0002"]):
            p = subprocess.run([sys.executable, str(ROOT / "harness" / "step_grid.py"), *args], capture_output=True, text=True,
                               env={**os.environ, "KG_CLOCK": "pinned"}, timeout=300)
            assert p.returncode == 2 and p.stderr.startswith("step_grid: "), (args, p.returncode, p.stderr[-300:])


def test_on_cargoquote_s1_to_s7_each_cell_agrees_with_the_scenarios_gate_for_the_same_keys():
    """AC3: a fresh run.py --deterministic folder of CargoQuote's seven scenarios, made on a scratch store; then,
    per scenario, the gate on a scratch store holding it, for each step's keys: every key's level, the blocked
    keys, the stale statements and the lapsed keys equal the cell's."""
    if SUBJECT.id != "cargo_quote":
        return
    need_rdflib()
    import gate_cli
    from store import open_store
    from tasks import TASKS
    with tempfile.TemporaryDirectory() as d:
        env = {**os.environ, "KG_CLOCK": "pinned", "KG_STORE": "rdflib", "KG_RDFLIB_FILE": os.path.join(d, "run.ttl")}
        p = subprocess.run([sys.executable, str(ROOT / "harness" / "run.py"), "--deterministic", "--out", os.path.join(d, "run")],
                           capture_output=True, text=True, env=env, timeout=900)
        assert p.returncode == 0, p.stderr[-800:]
        g = _valid(step_grid.grid([Path(d) / "run"]))
        assert [c["scenario"] for c in g["columns"]] == list(SUBJECT.order)
        steps = {s["id"]: s["keys"] for s in g["steps"]}
        keep = {k: os.environ.get(k) for k in ("KG_STORE", "KG_RDFLIB_FILE")}
        try:
            for col in g["columns"]:
                sc = col["scenario"]
                os.environ.update(KG_STORE="rdflib", KG_RDFLIB_FILE=os.path.join(d, f"{sc}.ttl"))
                with open_store(instance=SUBJECT.id, access="write") as st:
                    gate_cli._load(st, sc)
                with open_store(instance=SUBJECT.id, access="read") as st:
                    for sid, keys in steps.items():
                        rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario=sc, task="keys", spec=dict(TASKS["codegen"], keys=keys),
                                                threshold="blocker", baseline=None, loaded=False, version=gate_cli.held_version(st),
                                                as_of=col["as_of"], route_task="codegen")
                        c = next(x for x in g["cells"] if x["step"] == sid and x["column"] == col["id"])
                        levels = {}
                        for k in keys:
                            levels[rep["levels"][k]] = levels.get(rep["levels"][k], 0) + 1
                        assert c["levels"] == levels and c["unread"] == [], (sc, sid)
                        blocked = sorted({f["key"] for f in rep["findings"] if f["kind"] == "key" and f["severity"] == "blocker"})
                        assert c["findings"]["blocked"] == blocked, (sc, sid, c["findings"]["blocked"], blocked)
                        assert c["findings"]["stale"] == sorted({f["ref"] for f in rep["findings"] if f["kind"] == "stale"}), (sc, sid)
                        assert c["findings"]["lapsed"] == sorted({f["key"] for f in rep["findings"] if f["kind"] == "lapsed"}), (sc, sid)
        finally:
            for k, v in keep.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def test_the_changelog_names_it_under_contract_changes():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0192" in contract and "step_grid" in contract
