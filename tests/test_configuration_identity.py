"""task-0335 (decision-0039 §3.2 (a), doc-0038 §3.2): the gate report names the subject's configuration, and the trace
report's gate block names every input the gate report names.

- ``configuration``: the sha256 of each subject configuration file the load read (``Subject.configuration``), recorded
  at the load on ``agent:harness`` (``Store.record_inputs``) and read back (``Store.inputs``), additive, schema version
  3 unchanged; ``differs`` names it, compared whole.
- doc-0038 §3.2's three repros (``tools/check_configuration.py``): each moves ``configuration`` alone and ``--baseline``
  names it; rdflib here, Neo4j in the stack job.
- The trace gate block carries ``corpus``, ``attestations``, ``captures`` and ``configuration``, the gate report's.
- ``tools/check_round_trip.py`` and ``tools/check_mcp_server.py`` hold the new field.
Standard library; the store-backed parts skip without the pins. No network; the clock pinned."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib, skip  # noqa: E402
import gate_cli  # noqa: E402
import schema_check  # noqa: E402
import store  # noqa: E402
import subject  # noqa: E402

CQ = ROOT / "subjects" / "cargo_quote"
DAY = "2026-10-30"   # CargoQuote's [record] as_of
CONF = {"subject.toml": "a" * 64, "scenarios.toml": "b" * 64, "register_map.toml": "c" * 64}
NOW = {"task_profile": "a" * 64, "register": {"tag": "v0.2.13", "commit": "c" * 40, "why": None, "files": "f" * 64},
       "knowgov": {"version": "0.8.0", "commit": "d" * 40, "describe": "v0.8.0"}, "corpus": "e" * 64,
       "attestations": "1" * 64, "captures": "2" * 64, "configuration": CONF, "as_of": DAY}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---- the field: what the load read, by file
def test_the_configuration_is_each_file_read_by_its_raw_digest_and_a_file_not_there_is_left_out():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cargo_quote"
        shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__", "record", "vendor"))
        s = subject.Subject(root)
        got = s.configuration()
        want = {f: _sha(root / f) for f in ("subject.toml", "scenarios.toml", "plants.toml", "queries.toml")}
        want[s.register["map"]] = _sha(root / s.register["map"])
        assert s.register["map"] == "register_map.toml"
        vmap = s.verification.get("map")
        assert {k: v for k, v in got.items() if k != vmap} == dict(sorted(want.items())), got
        assert list(got) == sorted(got), "by path, sorted"
        (root / "plants.toml").unlink()
        (root / "queries.toml").write_bytes((root / "queries.toml").read_bytes().replace(b"\n", b"\r\n"))
        s2 = subject.Subject(root)
        got2 = s2.configuration()
        assert "plants.toml" not in got2, "a file that is not there is left out"
        assert got2["queries.toml"] != got["queries.toml"] and got2["queries.toml"] == _sha(root / "queries.toml"), "raw bytes"
        assert s2.queries == s.queries, "the parse is the one before: universal newlines"
        rm = root / "register_map.toml"
        rm.write_text(rm.read_text(encoding="utf-8") + "\n# an edit after the Subject was built\n", encoding="utf-8")
        assert s2.configuration()["register_map.toml"] == _sha(rm), "the register map as the gate reads it now"


def test_the_store_carries_the_configuration_as_one_canonical_property():
    text = store.configuration_text({"scenarios.toml": "b" * 64, "subject.toml": "a" * 64})
    assert text == json.dumps({"scenarios.toml": "b" * 64, "subject.toml": "a" * 64}, separators=(",", ":"))
    assert store.configuration_of(text) == {"scenarios.toml": "b" * 64, "subject.toml": "a" * 64}
    for bad in (None, "", "[1]", "{", '{"a": 1}', 7):
        assert store.configuration_of(bad) is None, bad
    assert store.inputs_digest({})["configuration"] is None, "a store loaded before task-0335: unknown"
    assert "configuration" in store.Store.INPUTS


def test_the_configuration_survives_export_and_import():
    rdf = need_rdflib()
    a = rdf.RdflibStore(path="")
    a.ensure_agents("harness", "v1", {"id": "agent:m", "name": "m"}, {"id": "agent:l", "name": "l"})
    a.record_inputs({"attestations": "1" * 64, "configuration": store.configuration_text(CONF)})
    assert a.inputs()["configuration"] == dict(sorted(CONF.items()))
    b = rdf.RdflibStore(path="")
    b.import_turtle(a.export_turtle())
    assert b.inputs() == a.inputs()


# ---- differs: compared whole
def test_differs_names_the_configuration_compared_whole():
    assert "configuration" in gate_cli.IDENTITY_FIELDS
    assert gate_cli.IDENTITY_FIELDS.index("configuration") == gate_cli.IDENTITY_FIELDS.index("captures") + 1
    assert gate_cli.differs(NOW, NOW) == []
    assert gate_cli.differs({**NOW, "configuration": {**CONF, "register_map.toml": "0" * 64}}, NOW) == ["configuration"]
    assert gate_cli.differs({**NOW, "configuration": {**CONF, "plants.toml": "9" * 64}}, NOW) == ["configuration"], \
        "a file read on one side only is a difference: its absence is known, not unknown"
    assert gate_cli.differs({**NOW, "configuration": None}, NOW) == [], "a report before task-0335: unknown"
    assert gate_cli.differs({k: v for k, v in NOW.items() if k != "configuration"}, NOW) == []
    assert gate_cli.differs(NOW, {**NOW, "configuration": None}) == []


def test_the_gate_report_schema_admits_configuration_additively():
    schema = schema_check.load("gate-report")
    props = schema["properties"]
    assert props["schema_version"]["const"] == gate_cli.SCHEMA_VERSION == 3, "no version change"
    assert "configuration" in props and "configuration" not in schema["required"]
    assert props["baseline"]["properties"]["differs"]["items"]["enum"] == list(gate_cli.IDENTITY_FIELDS)
    base = {"schema_version": 3, "tool": "knowgov gate", "subject": "s", "scenario": "S1", "task": "codegen", "store": "rdflib",
            "loaded": True, "verdict": "PROCEED", "why": "", "threshold": "blocker", "findings": [],
            "counts": {s: 0 for s in gate_cli.SEVERITIES}, "keys": {"total": 0, "below_verified": 0, "flagged": 0},
            "conflicts": 0, "stale": [], "suspect_derived": [], "levels": {}, "exit_code": 0, "task_profile": None,
            "baseline": None, "register": {"tag": None, "commit": None, "why": "x"},
            "knowgov": {"version": None, "commit": None, "describe": None}}
    assert schema_check.validate(base, schema) == [], "a report from before still validates"
    for ok in (CONF, None, {}):
        assert schema_check.validate({**base, "configuration": ok}, schema) == [], ok
    assert schema_check.validate({**base, "configuration": {"subject.toml": "x"}}, schema), "a digest is 64 hex"
    assert schema_check.validate({**base, "configuration": "a" * 64}, schema), "a map of files, not one digest"


# ---- AC1: doc-0038 §3.2's three repros, rdflib here (the stack job runs them on Neo4j)
def test_each_repro_moves_the_configuration_alone_and_baseline_names_it():
    need_rdflib()
    import check_configuration
    keep = {k: os.environ.get(k) for k in ("KG_STORE",)}
    try:
        assert check_configuration.main(["--store", "rdflib"]) == 0
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


# ---- AC2: the trace gate block names the gate report's inputs
def test_the_trace_schema_carries_the_inputs_as_the_gate_report_does():
    gate = schema_check.load("trace-report")["properties"]["gate"]
    rep = schema_check.load("gate-report")["properties"]
    assert gate["additionalProperties"] is False
    for f in ("corpus", "attestations", "captures", "configuration"):
        assert f in gate["properties"] and f not in gate["required"], f
        assert {k: v for k, v in gate["properties"][f].items() if k != "description"} == \
            {k: v for k, v in rep[f].items() if k != "description"}, f


def _loaded():
    rdf = need_rdflib()
    from subject import SUBJECT
    if SUBJECT.id != "cargo_quote":
        skip("register-rows", f"the subject is {SUBJECT.id}, the check is CargoQuote's")
    st = rdf.RdflibStore(path="")
    gate_cli._load(st, "S1")
    return st, SUBJECT


def test_the_trace_gate_block_names_corpus_attestations_captures_and_configuration_equal_to_the_gate_reports():
    st, SUBJECT = _loaded()
    import example_instance
    import trace
    from tasks import TASKS
    with tempfile.TemporaryDirectory() as td:
        inst = example_instance.build(Path(td) / "inst")
        led = Path(td) / "ledger.json"
        trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], as_of=DAY)
        rep = trace.check(st, instance=inst, ledger=led, as_of=DAY)
        assert schema_check.validate(rep, schema_check.load("trace-report")) == []
        got = rep["gate"]
        want = gate_cli.evaluate(st, subject=SUBJECT.id, scenario="S1", task="codegen", spec=TASKS["codegen"], threshold="blocker",
                                 baseline=None, loaded=True, as_of=DAY)
        for f in ("task_profile", "register", "knowgov", "corpus", "attestations", "captures", "configuration"):
            assert got.get(f) == want[f], (f, got.get(f), want[f])
        for f in ("corpus", "attestations", "captures"):
            assert len(got[f] or "") == 64, (f, got[f])
        assert got["configuration"] == SUBJECT.configuration(), "the files the load read"


def test_the_mcp_reader_carries_the_configuration_the_load_recorded():
    st, SUBJECT = _loaded()
    import mcp_server

    class Held(mcp_server.ReadOnlyStore):
        def release(self) -> None:
            pass
    got = mcp_server.Tools(opener=lambda: Held(st), as_of=DAY).gate_verdict({"scenario": "S1", "task": "codegen"})
    assert got["configuration"] == SUBJECT.configuration() and "subject.toml" in got["configuration"]
    assert schema_check.validate(got, schema_check.load("gate-report")) == []


# ---- AC3: the checks hold the new field
def test_check_round_trip_and_check_mcp_server_hold_the_configuration():
    import check_mcp_server
    import check_round_trip
    full = {"corpus": "e" * 64, "attestations": "1" * 64, "captures": "2" * 64, "register": {"files": "f" * 64},
            "configuration": CONF, "code": {"vendor/a.py": "4" * 64},   # code and preload: task-0341
            "preload": {"path": None, "sha256": None, "why": "none applied"}}
    assert check_round_trip.unnamed_corpus(full) == []
    for bad in (None, {}, {"scenarios.toml": "b" * 64}, {**CONF, "subject.toml": "x"}):
        assert check_round_trip.unnamed_corpus({**full, "configuration": bad}) == ["configuration"], bad
    assert "configuration" in check_mcp_server.IDENTITY_HELD
    fails: list[str] = []
    check_mcp_server.corpus_held("S1", full, full, fails)
    assert fails == []
    check_mcp_server.corpus_held("S1", {**full, "configuration": {**CONF, "subject.toml": "0" * 64}}, full, fails)
    assert len(fails) == 1 and "configuration" in fails[0], fails
