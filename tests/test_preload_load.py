"""Task-0064: the pre-load check's verdict, read at the load and recorded on each document version.
A version the report does not cover, or whose bytes differ from the digest judged, is unchecked,
never clean; the gate lists the documents behind the task's keys whose form was unchecked or had
findings, at info, so the exit does not move unless --fail-on info asks. Without a report nothing
is recorded and the load's output has no preload key (harness.yml: the comparator still matches the
record). The adapters are read as source here: the tests job has neither rdflib nor a driver;
harness.yml (rdflib) and the stack job (Neo4j) run them."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import example_instance  # noqa: E402
import gate  # noqa: E402
import gate_cli  # noqa: E402
import preload  # noqa: E402
import schema_check  # noqa: E402
from kitio import sha256  # noqa: E402
from subject import Subject  # noqa: E402


def _report(inst: Path, rows: list[dict]) -> dict:
    return {"schema_version": 1, "tool": "knowgov preload check", "instance": "/elsewhere/when/the/ci/ran", "scope": "all",
            "threshold": "major", "files": rows, "linters": [{"kind": "plantuml-models", "tool": "pumllint", "version": "0.33.0",
                                                              "files": 2, "exit": 0, "error": None}],
            "counts": {"clean": 1, "findings": 1, "unchecked": 1, "cannot_run": 0, "skipped": 0}, "exit_code": 1, "note": "form"}


def _row(file, state, tool, digest=None, why=""):
    r = {"file": file, "kind": file.split("/")[1], "tool": tool, "state": state, "why": why, "findings": []}
    if digest:
        r["sha256"] = digest
    return r


def test_a_verdict_holds_only_for_the_bytes_it_judged():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "inst"
        example_instance.build(inst)
        sub = Subject(inst / "subjects" / "cargo_quote")
        assert preload.instance_root(sub) == inst.resolve()
        kit = {a["key"]: (sub.root / a["path"]).read_text(encoding="utf-8") for a in sub.artefacts if a.get("path") and (sub.root / a["path"]).is_file()}
        flow, cont, spec, oas = "behavior/quote_flow.puml", "structure/containers.puml", "contract/spec.md", "contract/openapi.yaml"
        digest = lambda rel: hashlib.sha256((inst / rel).read_bytes()).hexdigest()  # noqa: E731
        rep = _report(inst, [
            _row("artefacts/plantuml-models/quote_flow.puml", "clean", "pumllint", digest("artefacts/plantuml-models/quote_flow.puml"), "no finding"),
            _row("artefacts/plantuml-models/containers.puml", "findings", "pumllint", "0" * 64, "1 finding"),
            _row("artefacts/specification-prose/spec.md", "unchecked", "Vale, markdownlint", digest("artefacts/specification-prose/spec.md"), "form unchecked"),
        ])
        assert schema_check.validate(rep, schema_check.load("preload-report")) == []
        v = preload.verdicts(sub, kit, [flow, cont, spec, oas], rep, "preload-report.json")
        assert v[flow]["state"] == "clean" and v[flow]["tool_version"] == "0.33.0" and v[flow]["digest"] == sha256(kit[flow])
        assert v[cont]["state"] == "unchecked" and "differ" in v[cont]["why"], "a digest that is not the bytes loaded is never clean"
        assert v[spec]["state"] == "unchecked" and v[spec]["tool"] == "Vale, markdownlint"
        assert v[oas]["state"] == "unchecked" and "does not cover" in v[oas]["why"]
        # a planted edit after the check: the same row no longer vouches for the bytes
        planted = dict(kit, **{flow: kit[flow] + "\n' edited after the check\n"})
        assert preload.verdicts(sub, planted, [flow], rep, "r")[flow]["state"] == "unchecked"
        # a row without a digest (a task-0045 report) is unchecked
        old = _report(inst, [_row("artefacts/plantuml-models/quote_flow.puml", "clean", "pumllint")])
        assert preload.verdicts(sub, kit, [flow], old, "r")[flow]["state"] == "unchecked"
        # where the report lives: KG_PRELOAD_REPORT, else <instance>/preload-report.json when it exists, else none
        saved = os.environ.pop("KG_PRELOAD_REPORT", None)
        try:
            assert preload.report_path(sub) is None
            (inst / "preload-report.json").write_text(json.dumps(rep), encoding="utf-8")
            assert preload.report_path(sub) == inst.resolve() / "preload-report.json"
            os.environ["KG_PRELOAD_REPORT"] = str(Path(td) / "elsewhere.json")
            assert preload.report_path(sub) == Path(td) / "elsewhere.json"
        finally:
            os.environ.pop("KG_PRELOAD_REPORT", None)
            if saved is not None:
                os.environ["KG_PRELOAD_REPORT"] = saved
        bad = Path(td) / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        try:
            preload.read_report(bad)
            raise AssertionError("a file that is not a preload report was read")
        except ValueError:
            pass


class _Store:
    def __init__(self, verdicts):
        self.v = verdicts

    def preload_verdicts(self):
        return self.v


def test_the_gate_lists_unchecked_or_flawed_documents_behind_its_keys_at_info():
    keys = {"P2|surcharge": {"assertions": [{"id": "A:dt:P2|surcharge@v1", "artefact": "contract/decision_table.md"},
                                            {"id": "A:cap:x", "artefact": None}]},
            "R|x": {"assertions": [{"id": "A:flow:R@v1", "artefact": "behavior/quote_flow.puml"},
                                   {"id": "A:oas:R@v1", "artefact": "contract/openapi.yaml"}]}}
    verdicts = [{"artefact": "behavior/quote_flow.puml", "version": "v1", "state": "clean", "tool": "pumllint", "why": ""},
                {"artefact": "contract/openapi.yaml", "version": "v1", "state": "findings", "tool": "Spectral", "why": "1 finding"}]
    behind = gate.preload_behind(_Store(verdicts), keys)
    assert [(d["artefact"], d["state"], d["keys"]) for d in behind] == [
        ("contract/decision_table.md", "unchecked", ["P2|surcharge"]),   # no verdict recorded for that version: unchecked
        ("contract/openapi.yaml", "findings", ["R|x"])], behind
    assert gate.preload_behind(_Store([]), keys) is None, "no verdict at all: the bundle carries no preload key"

    class _Bare:
        pass
    assert gate.preload_behind(_Bare(), keys) is None
    res = {"verdict": "PROCEED", "why": "all verified", "keys": {}, "blocked_keys": [], "below_verified": [], "flagged": [],
           "stale": [], "suspect_derived": [], "preload": behind}
    rep = gate_cli.report(res, subject="cargo_quote", scenario="S1", task="codegen", store="rdflib", loaded=True,
                          block_levels={"absent"}, threshold="blocker", baseline=None)
    assert schema_check.validate(rep, schema_check.load("gate-report")) == []
    pre = [f for f in rep["findings"] if f["kind"] == "preload"]
    assert [(f["severity"], f["ref"], f["related"]) for f in pre] == [("info", "contract/decision_table.md@v1", ["P2|surcharge"]),
                                                                      ("info", "contract/openapi.yaml@v1", ["R|x"])]
    assert "not checked before the load" in pre[0]["message"] and "found findings" in pre[1]["message"]
    assert rep["exit_code"] == 0
    rep_info = gate_cli.report(res, subject="cargo_quote", scenario="S1", task="codegen", store="rdflib", loaded=True,
                               block_levels={"absent"}, threshold="info", baseline=None)
    assert rep_info["exit_code"] == 1, "--fail-on info asks for them"


def test_both_adapters_record_and_read_the_verdict_and_the_server_may_read_it():
    port = (ROOT / "harness" / "store.py").read_text(encoding="utf-8")
    assert "def record_preload(self, vid: str, verdict: dict)" in port and "def preload_verdicts(self)" in port
    neo = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    assert 'PRELOAD_FIELDS = ("state", "tool", "tool_version", "digest", "report", "why")' in neo
    assert "SET v += $props" in neo and "WHERE v.preload_state IS NOT NULL" in neo
    rdf = (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")
    body = rdf[rdf.index("def record_preload("):rdf.index("# ---- the census and the page")]
    assert '("state", "tool", "tool_version", "digest", "report", "why")' in body and '"HAS_VERSION"' in body
    import mcp_server
    assert "preload_verdicts" in mcp_server.READS and "record_preload" not in mcp_server.READS
    load_src = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    assert '**({"preload": preload} if preload else {})' in load_src, "no report: the load's output has no preload key"


def test_the_report_records_the_digest_of_each_file_judged():
    import preload_check
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "inst"
        example_instance.build(inst)
        saved = preload_check.pumllint_cmd, preload_check.spectral_cmd
        preload_check.pumllint_cmd = preload_check.spectral_cmd = lambda: None   # nothing installed: every file unchecked, still digested
        try:
            rep = preload_check.check(inst)
        finally:
            preload_check.pumllint_cmd, preload_check.spectral_cmd = saved
        assert schema_check.validate(rep, schema_check.load("preload-report")) == []
        for r in rep["files"]:
            assert r["sha256"] == hashlib.sha256((inst / r["file"]).read_bytes()).hexdigest(), r["file"]
