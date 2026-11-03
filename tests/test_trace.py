"""Task-0051: knowgov-trace register and check, on a fake store (stdlib only). The S6 walkthrough on
the rdflib store, the registered build turning suspect after the change, runs in harness.yml
(tools/check_trace_walkthrough.py)."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import example_instance  # noqa: E402
import schema_check  # noqa: E402
import trace  # noqa: E402

IDS = ["A:1@v1", "A:2@v1", "A:3@v1"]


class FakeStore:
    name = "fake"

    def __init__(self):
        self.derived: dict[str, dict] = {}
        self.status = {a: "approved" for a in IDS}

    def register_derived(self, did, kind, sha, ids):
        assert did not in self.derived, f"{did} registered twice"
        self.derived[did] = {"kind": kind, "sha256": sha, "ids": list(ids)}

    def all_derived(self):
        return [{"id": d, "suspect": False} for d in self.derived]

    def assertion_brief(self, aid):
        return {"id": aid, "key": f"k{aid[2]}", "status": self.status[aid]} if aid in self.status else None

    def stale_on_keys(self, keys):
        return [{"id": a, "key": f"k{a[2]}", "successors": [{"id": a.replace("@v1", "@v2"), "status": "proposed"}]}
                for a, s in self.status.items() if s == "invalidated" and f"k{a[2]}" in keys]


def _resolve(verdict="PROCEED"):
    return lambda st, task: {"verdict": verdict, "why": "fake", "keys": {"k1": {"level": "approved", "flags": [], "assertions": [{"id": a} for a in IDS]}},
                             "blocked_keys": [], "stale": [], "suspect_derived": []}


def _valid(rep):
    errs = schema_check.validate(rep, schema_check.load("trace-report"))
    assert errs == [], errs
    return rep


def _setup(td):
    inst = example_instance.build(Path(td) / "inst")
    return inst, Path(td) / "ledger.json", FakeStore()


def test_register_records_the_file_its_app_and_the_statements_and_supersedes_by_path():
    with tempfile.TemporaryDirectory() as td:
        inst, led, st = _setup(td)
        rep = _valid(trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], resolve=_resolve()))
        [r] = rep["registered"]
        assert (r["id"], r["app"], r["used"]) == ("derived:code@c1:reference_impl.py", "APP-0001", 3)
        assert st.derived[r["id"]]["ids"] == IDS and rep["exit_code"] == 0
        trace.register(st, instance=inst, ledger=led, commit="c2", files=["reference_impl.py"], assertions=["A:1@v1"], resolve=_resolve())
        [e] = json.loads(led.read_text(encoding="utf-8"))["entries"]
        assert (e["commit"], e["assertions"]) == ("c2", ["A:1@v1"]), "a later registration of the same path replaces the entry"
        trace.register(st, instance=inst, ledger=led, commit="c2", files=["reference_impl.py"], resolve=_resolve())   # idempotent in the store


def test_register_refuses_an_unmapped_file_a_missing_map_and_no_statement():
    with tempfile.TemporaryDirectory() as td:
        inst, led, st = _setup(td)
        root = inst / check_root(inst)
        (root / "extra.py").write_text("#\n", encoding="utf-8")
        for files, want in ((["extra.py"], "no row of code_map.toml maps it"), (["nope.py"], "no such file"), ([], "no --file")):
            try:
                trace.register(st, instance=inst, ledger=led, commit="c1", files=files, resolve=_resolve())
                raise AssertionError(files)
            except trace.CannotRun as e:
                assert want in str(e), e
        empty = lambda st, task: {"keys": {}}  # noqa: E731
        try:
            trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], resolve=empty)
            raise AssertionError("no statement")
        except trace.CannotRun as e:
            assert "no statement" in str(e)
        (inst / "code_map.toml").unlink()
        try:
            trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], resolve=_resolve())
            raise AssertionError("no map")
        except trace.CannotRun as e:
            assert "code_map.toml: missing" in str(e)


def check_root(inst: Path) -> str:
    import code_map
    return code_map.code_map(inst, code_map.register_apps(inst / "register"), [])["root"]


def test_check_reports_suspect_drift_missing_unmapped_by_severity_and_exits_by_threshold():
    with tempfile.TemporaryDirectory() as td:
        inst, led, st = _setup(td)
        trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], resolve=_resolve())
        rep = _valid(trace.check(st, instance=inst, ledger=led, resolve=_resolve()))
        assert rep["exit_code"] == 0 and rep["findings"] == [] and rep["registered"][0]["state"] == "unchanged"

        st2 = FakeStore()   # a reload: the store lost the registration, the ledger keeps it
        st2.status["A:2@v1"] = "invalidated"
        rep = _valid(trace.check(st2, instance=inst, ledger=led, resolve=_resolve()))
        assert "derived:code@c1:reference_impl.py" in st2.derived
        [f] = rep["findings"]
        assert (f["severity"], f["kind"], f["app"], f["related"]) == ("blocker", "suspect", "APP-0001", ["A:2@v1"]) and "APP-0001" in f["message"]
        assert rep["registered"][0]["successors"] == ["A:2@v2"] and rep["exit_code"] == 1

        root = inst / check_root(inst)
        (root / "reference_impl.py").write_text("# edited\n", encoding="utf-8")
        (root / "new.py").write_text("#\n", encoding="utf-8")
        rep = _valid(trace.check(FakeStore(), instance=inst, ledger=led, changed=["reference_impl.py", "new.py", "README.txt"], resolve=_resolve()))
        assert [(f["kind"], f["severity"], f["path"]) for f in rep["findings"]] == [("unmapped", "major", "new.py"), ("drift", "minor", "reference_impl.py")]
        assert rep["exit_code"] == 0, "drift and unmapped are below blocker"
        assert trace.check(FakeStore(), instance=inst, ledger=led, changed=["new.py"], fail_on="major", resolve=_resolve())["exit_code"] == 1
        rep = trace.check(FakeStore(), instance=inst, ledger=led, changed=["README.txt"], resolve=_resolve())
        assert rep["registered"] == [] and rep["gate"] is None and rep["findings"] == [], "a change to no code reaches nothing"

        (root / "reference_impl.py").unlink()
        rep = _valid(trace.check(FakeStore(), instance=inst, ledger=led, resolve=_resolve()))
        assert [(f["kind"], f["severity"]) for f in rep["findings"]] == [("missing", "major")]


def test_check_carries_the_gate_blockers_but_not_its_own_suspect_list():
    with tempfile.TemporaryDirectory() as td:
        inst, led, st = _setup(td)
        trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], resolve=_resolve())

        def blocked(st, task):
            r = _resolve("BLOCKED")(st, task)
            r["keys"]["k1"]["level"] = "invalidated"
            r["blocked_keys"] = ["k1"]
            r["suspect_derived"] = [{"id": "derived:S1:G:run1", "used_invalidated": ["A:1@v1"]}]
            return r
        rep = _valid(trace.check(st, instance=inst, ledger=led, resolve=blocked, block_levels={"invalidated"}))
        assert [(f["kind"], f["severity"]) for f in rep["findings"]] == [("gate:key", "blocker")] and rep["exit_code"] == 1
        assert rep["gate"]["verdict"] == "BLOCKED"


def test_the_command_exits_2_when_it_cannot_run_and_the_schema_is_the_supported_subset():
    with tempfile.TemporaryDirectory() as td:
        inst, led, st = _setup(td)
        try:
            trace.check(st, instance=inst, ledger=led, resolve=_resolve())
            raise AssertionError("no ledger")
        except trace.CannotRun as e:
            assert "no ledger" in str(e)
        led.write_text('{"tool": "something else", "entries": []}', encoding="utf-8")
        try:
            trace.check(st, instance=inst, ledger=led, resolve=_resolve())
            raise AssertionError("bad ledger")
        except trace.CannotRun as e:
            assert "is not a knowgov trace ledger" in str(e)
        assert trace.main(["check", "--instance", str(Path(td) / "nope"), "--ledger", str(led)]) == 2
    schema_check.validate({}, schema_check.load("trace-report"))   # raises on a keyword outside the subset
