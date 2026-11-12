"""task-0341 (decision-0040 (a)): the gate report names the code and suite it compared and the pre-load report it
applied.

- ``code``: the raw sha256 of each ``[reference] code``, ``[oracle] script`` and ``[oracle] suite`` file, by its path
  under the subject root, in the load's part selection (``subject.code_digests``, ``Subject.code``).
- ``preload``: the pre-load report applied, {path, sha256, why}, null ones with ``why`` when none was
  (``preload.identity``).
Both recorded at the load on ``agent:harness`` (``Store.record_inputs``) and read back (``Store.inputs``), additive,
schema version 3 unchanged; ``differs`` names each, compared whole. Group A's repros (``tools/check_code_preload.py``):
rdflib here, Neo4j in the stack job. Standard library; the store-backed parts skip without the pins. No network; the
clock pinned."""
from __future__ import annotations

import hashlib
import os
import re
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
JF = ROOT / "subjects" / "jef_data_load"
DAY = "2026-10-30"   # CargoQuote's [record] as_of
CODE = {"vendor/a.py": "a" * 64, "vendor/suite.py": "b" * 64}
APPLIED = {"path": "pre.json", "sha256": "c" * 64, "why": None}
NONE = {"path": None, "sha256": None, "why": "KG_PRELOAD_REPORT is not set and the subject is not in an instance"}
NOW = {"task_profile": "a" * 64, "register": {"tag": "v0.2.13", "commit": "c" * 40, "why": None, "files": "f" * 64},
       "knowgov": {"version": "0.8.0", "commit": "d" * 40, "describe": "v0.8.0"}, "corpus": "e" * 64,
       "attestations": "1" * 64, "captures": "2" * 64, "configuration": {"subject.toml": "3" * 64}, "code": CODE,
       "preload": APPLIED, "as_of": DAY}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _env(**kv):
    keep = {k: os.environ.get(k) for k in kv}
    for k, v in kv.items():
        os.environ.pop(k, None)
        if v is not None:
            os.environ[k] = v
    return keep


# ---- the fields: what the load reads
def test_code_is_each_code_and_suite_file_by_its_path_under_the_root_at_its_raw_digest():
    s = subject.Subject(CQ)
    got = s.code()
    want = {s.reference["code"]: _sha(CQ / s.reference["code"]), s.oracle["script"]: _sha(CQ / s.oracle["script"]),
            **{f: _sha(CQ / f) for f in s.oracle["suite"]}}
    assert got == dict(sorted(want.items())), got
    for which in ("implementation", "suite"):   # the load's own part selection, digest for digest
        assert set(s.code_parts(which)[1].values()) <= set(got.values()), which
    j = subject.Subject(JF)
    jc = j.code()
    rel = j.reference["code"]
    assert jc and all(k.startswith(rel + "/") or k == j.oracle["script"] for k in jc), jc
    assert sorted(jc.values()) == sorted([*j.code_parts("implementation")[1].values(), *j.code_parts("suite")[1].values()])
    assert all(k.endswith(".py") for k in jc), "a directory's *.py files, as the load bundles them"


def test_code_leaves_a_missing_file_out_is_empty_without_code_and_unknown_outside_the_instance():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "subjects" / "cargo_quote"
        shutil.copytree(CQ, root, ignore=shutil.ignore_patterns("__pycache__", "record"))
        suite = "vendor/tools/acceptance/cargo_quote_suite.py"
        (root / suite).unlink()
        assert suite not in subject.Subject(root).code(), "a file that is not there is left out"
        m = root / "subject.toml"
        text = m.read_text(encoding="utf-8")
        m.write_text(text.replace('code = "vendor/stack_experiment', 'code = "../../../outside/stack_experiment'), encoding="utf-8")
        assert subject.Subject(root).code() is None, "a path outside the instance: unknown, nothing outside digested"
    assert subject.code_digests(CQ, {}, {}) == {}, "neither declared: none"


def test_preload_names_the_report_applied_or_none_with_why():
    import example_instance
    import preload
    keep = _env(KG_PRELOAD_REPORT=None)
    try:
        got = preload.identity(subject.Subject(CQ))
        assert got == NONE, got
        with tempfile.TemporaryDirectory() as td:
            inst = example_instance.build(Path(td) / "inst")
            s = subject.Subject(inst / "subjects" / "cargo_quote")
            got = preload.identity(s)
            assert got["path"] is None and got["sha256"] is None and "instance holds no preload-report.json" in got["why"], got
            (inst / "preload-report.json").write_text("{}", encoding="utf-8")
            assert preload.identity(s) == {"path": "preload-report.json", "sha256": _sha(inst / "preload-report.json"), "why": None}
            other = Path(td) / "pre.json"
            other.write_text('{"x": 1}', encoding="utf-8")
            os.environ["KG_PRELOAD_REPORT"] = str(other)
            assert preload.identity(s) == {"path": str(other), "sha256": _sha(other), "why": None}, "as KG_PRELOAD_REPORT names it"
    finally:
        _env(**keep)


def test_the_store_carries_code_and_preload_as_canonical_properties():
    assert {"code", "preload"} <= set(store.Store.INPUTS)
    assert store.inputs_digest({})["code"] is None and store.inputs_digest({})["preload"] is None, "a load before task-0341: unknown"
    got = store.inputs_digest({"input_code": store.configuration_text(CODE), "input_preload": store.configuration_text(NONE)})
    assert got["code"] == CODE and got["preload"] == NONE
    for bad in (None, "", "[1]", "{", '{"path": 1, "sha256": null, "why": null}', '{"path": null}', 7):
        assert store.preload_of(bad) is None, bad


def test_code_and_preload_survive_export_and_import():
    rdf = need_rdflib()
    a = rdf.RdflibStore(path="")
    a.ensure_agents("harness", "v1", {"id": "agent:m", "name": "m"}, {"id": "agent:l", "name": "l"})
    a.record_inputs({"code": store.configuration_text(CODE), "preload": store.configuration_text(APPLIED)})
    assert a.inputs()["code"] == CODE and a.inputs()["preload"] == APPLIED
    b = rdf.RdflibStore(path="")
    b.import_turtle(a.export_turtle())
    assert b.inputs() == a.inputs()


def test_differs_names_code_and_preload_compared_whole():
    i = gate_cli.IDENTITY_FIELDS
    assert i.index("code") == i.index("configuration") + 1 and i.index("preload") == i.index("code") + 1 and i[-1] == "as_of"
    assert gate_cli.differs(NOW, NOW) == []
    assert gate_cli.differs({**NOW, "code": {**CODE, "vendor/suite.py": "0" * 64}}, NOW) == ["code"]
    assert gate_cli.differs({**NOW, "code": {**CODE, "vendor/b.py": "9" * 64}}, NOW) == ["code"], "a file on one side only"
    assert gate_cli.differs({**NOW, "preload": NONE}, NOW) == ["preload"], "a report applied on one side only: known, not unknown"
    assert gate_cli.differs({**NOW, "preload": {**APPLIED, "sha256": "0" * 64}}, NOW) == ["preload"]
    for f in ("code", "preload"):
        assert gate_cli.differs({**NOW, f: None}, NOW) == [] and gate_cli.differs(NOW, {**NOW, f: None}) == [], f
        assert gate_cli.differs({k: v for k, v in NOW.items() if k != f}, NOW) == [], f


def test_both_schemas_admit_code_and_preload_additively():
    schema = schema_check.load("gate-report")
    props = schema["properties"]
    assert props["schema_version"]["const"] == gate_cli.SCHEMA_VERSION == 3, "no version change"
    for f in ("code", "preload"):
        assert f in props and f not in schema["required"], f
    assert props["baseline"]["properties"]["differs"]["items"]["enum"] == list(gate_cli.IDENTITY_FIELDS)
    gate = schema_check.load("trace-report")["properties"]["gate"]
    for f in ("code", "preload"):
        assert f in gate["properties"] and f not in gate["required"], f
        assert {k: v for k, v in gate["properties"][f].items() if k != "description"} == \
            {k: v for k, v in props[f].items() if k != "description"}, f
    base = {"schema_version": 3, "tool": "knowgov gate", "subject": "s", "scenario": "S1", "task": "codegen", "store": "rdflib",
            "loaded": True, "verdict": "PROCEED", "why": "", "threshold": "blocker", "findings": [],
            "counts": {s: 0 for s in gate_cli.SEVERITIES}, "keys": {"total": 0, "below_verified": 0, "flagged": 0},
            "conflicts": 0, "stale": [], "suspect_derived": [], "levels": {}, "exit_code": 0, "task_profile": None,
            "baseline": None, "register": {"tag": None, "commit": None, "why": "x"},
            "knowgov": {"version": None, "commit": None, "describe": None}}
    assert schema_check.validate(base, schema) == [], "a report from before still validates"
    for f, ok in (("code", CODE), ("code", {}), ("code", None), ("preload", APPLIED), ("preload", NONE), ("preload", None)):
        assert schema_check.validate({**base, f: ok}, schema) == [], (f, ok)
    for f, bad in (("code", {"a.py": "x"}), ("code", "a" * 64), ("preload", {"path": "p"}),
                   ("preload", {**APPLIED, "sha256": "x"}), ("preload", {**APPLIED, "extra": 1})):
        assert schema_check.validate({**base, f: bad}, schema), (f, bad)


# ---- AC1: R3, the code and suite edited (rdflib here; the stack job runs it on Neo4j)
def _repro(fn, *args):
    need_rdflib()
    import check_code_preload
    keep = _env(KG_STORE=None, KG_PRELOAD_REPORT=None)
    try:
        with tempfile.TemporaryDirectory() as td:
            return getattr(check_code_preload, fn)("rdflib", Path(td), *args)
    finally:
        _env(**keep)


def test_ac1_r3_an_edit_to_the_suite_or_the_implementation_moves_code_alone_and_differs_names_it():
    import check_code_preload
    for r in check_code_preload.CODE_REPROS:
        fails = _repro("code_repro", *r)
        assert fails == [], fails


# ---- AC2: Q1, the pre-load report applied
def test_ac2_q1_the_pre_load_report_applied_moves_preload_alone_and_none_reads_null_with_why():
    fails = _repro("preload_repro")
    assert fails == [], fails


# ---- AC3: the CLI report, MCP gate_verdict and the trace gate block carry them equal; the checks hold them
def _loaded():
    rdf = need_rdflib()
    from subject import SUBJECT
    if SUBJECT.id != "cargo_quote":
        skip("register-rows", f"the subject is {SUBJECT.id}, the check is CargoQuote's")
    keep = _env(KG_PRELOAD_REPORT=None)
    try:
        st = rdf.RdflibStore(path="")
        gate_cli._load(st, "S1")
    finally:
        _env(**keep)
    return st, SUBJECT


def test_ac3_the_cli_report_mcp_gate_verdict_and_the_trace_gate_block_carry_code_and_preload_equal():
    st, SUBJECT = _loaded()
    import example_instance
    import mcp_server
    import trace
    from tasks import TASKS
    rep = gate_cli.evaluate(st, subject=SUBJECT.id, scenario="S1", task="codegen", spec=TASKS["codegen"], threshold="blocker",
                            baseline=None, loaded=True, as_of=DAY)
    assert rep["code"] == SUBJECT.code() and rep["code"], rep["code"]
    assert rep["preload"]["sha256"] is None and rep["preload"]["why"], rep["preload"]
    assert schema_check.validate(rep, schema_check.load("gate-report")) == []

    class Held(mcp_server.ReadOnlyStore):
        def release(self) -> None:
            pass
    got = mcp_server.Tools(opener=lambda: Held(st), as_of=DAY).gate_verdict({"scenario": "S1", "task": "codegen"})
    assert got["code"] == rep["code"] and got["preload"] == rep["preload"]
    with tempfile.TemporaryDirectory() as td:
        inst = example_instance.build(Path(td) / "inst")
        led = Path(td) / "ledger.json"
        trace.register(st, instance=inst, ledger=led, commit="c1", files=["reference_impl.py"], as_of=DAY)
        tr = trace.check(st, instance=inst, ledger=led, as_of=DAY)
        assert schema_check.validate(tr, schema_check.load("trace-report")) == []
        assert tr["gate"]["code"] == rep["code"] and tr["gate"]["preload"] == rep["preload"]


def test_ac3_check_round_trip_and_check_mcp_server_hold_code_and_preload():
    import check_mcp_server
    import check_round_trip
    full = {"corpus": "e" * 64, "attestations": "1" * 64, "captures": "2" * 64, "register": {"files": "f" * 64},
            "configuration": {"subject.toml": "3" * 64}, "code": CODE, "preload": APPLIED}
    assert check_round_trip.unnamed_corpus(full) == []
    assert check_round_trip.unnamed_corpus({**full, "preload": NONE}) == []
    for f, bad in (("code", None), ("code", {"a.py": "x"}), ("preload", None), ("preload", {**NONE, "why": ""}),
                   ("preload", {**APPLIED, "sha256": None}), ("preload", {"path": "p", "sha256": "c" * 64})):
        assert check_round_trip.unnamed_corpus({**full, f: bad}) == [f], (f, bad)
    assert {"code", "preload"} <= set(check_mcp_server.IDENTITY_HELD)
    fails: list[str] = []
    check_mcp_server.corpus_held("S1", full, full, fails)
    assert fails == []
    for f, other in (("code", {**CODE, "vendor/a.py": "0" * 64}), ("preload", NONE)):
        fails = []
        check_mcp_server.corpus_held("S1", {**full, f: other}, full, fails)
        assert len(fails) == 1 and f in fails[0], fails
    text = (ROOT / "tools" / "check_round_trip.py").read_text(encoding="utf-8")
    assert '"code": SUBJECT.code(), "preload": preload.identity(SUBJECT)' in text, "the first store's report against this process's reading"


# ---- AC4: the record holds; the changelog names the change
def test_ac4_the_record_reads_code_and_preload_as_unknown_and_the_changelog_names_them():
    s = subject.Subject(CQ)
    base = gate_cli.record_identity({}, s)["identity"]
    assert set(base) == {"as_of"}, base
    assert gate_cli.differs(base, {**NOW, "as_of": base["as_of"]}) == [], "baseline=record names neither"
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    top = log.split("\n## ", 2)[1]   # Unreleased, or the release section that renamed it
    contract = top.split("\n### Contract changes", 1)[1].split("\n### Changes", 1)[0]
    assert re.search(r"\*\*The gate report names the code and suite it compared and the pre-load report it applied\*\* \(task-0341", contract)
    workflow = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "python tools/check_code_preload.py --store neo4j" in workflow, "the stack job proves both repros on Neo4j"
