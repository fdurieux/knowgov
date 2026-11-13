"""Task-0217 (decision-0018 point 1, step 4): tools/preload_check.py runs pumllint's trace with --features, the
glossary check and the DMN gap check across the kinds they read, each finding in the report with its tool.

Stdlib, on temporary instances and stand-in commands: the DMN check finds gaps (an integral input's open interval
with no integer in it is none), overlaps under UNIQUE (under ANY only when the outputs differ, never under FIRST)
and untyped outputs, and says when it cannot read an entry; the glossary check finds a term in three requirements
the glossary does not define; the trace, on the harness's pumllint, is unchecked, naming 0.35.0, when that one is
older, and maps a 0.35.0 report's lists to findings; a check that cannot run here leaves the kind unchecked, as before; a
document no linter of its kind judged and a check read is judged by the check alone, its findings becoming lint
gaps named by the check. The real pumllint 0.35.0 and the Node linters are tools/check_preload_linters.py's."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import preload  # noqa: E402
import preload_check  # noqa: E402
import schema_check  # noqa: E402
import step4_checks as s4  # noqa: E402

HEAD = '<?xml version="1.0"?>\n<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/" id="d" name="D" namespace="x">\n'


def dmn(rules: str, typeref: str = "number", policy: str = "UNIQUE", outputs: str = '<output id="o" label="y" typeRef="string"/>') -> str:
    return (HEAD + f'<decision id="dec" name="Dec"><decisionTable id="t" hitPolicy="{policy}">'
            f'<input id="i" label="x"><inputExpression typeRef="{typeref}"><text>x</text></inputExpression></input>{outputs}'
            + "".join(f'<rule id="r{n}"><inputEntry><text>{e}</text></inputEntry>'
                      + "".join(f"<outputEntry><text>{o}</text></outputEntry>" for o in outs) + "</rule>"
                      for n, (e, outs) in enumerate(rules))
            + "</decisionTable></decision></definitions>\n")


def instance(files: dict[str, str]) -> Path:
    d = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        p = d / "artefacts" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return d.resolve()


def rules_of(res: dict) -> list[str]:
    return [f["rule"] for f in res["findings"]]


def test_dmn_gaps_by_type_and_overlaps_by_hit_policy_and_untyped_outputs():
    bands = [("&lt;= 41", ['"a"']), ("[42..66]", ['"b"']), ("&gt;= 67", ['"c"'])]
    got = s4.run_dmn(instance({"decision-tables/t.dmn": dmn(bands)}))
    assert got["state"] == "ran" and [f["message"] for f in got["findings"]] == [
        "t: no rule matches x in (41, 42)", "t: no rule matches x in (66, 67)"]
    assert rules_of(s4.run_dmn(instance({"decision-tables/t.dmn": dmn(bands, typeref="integer")}))) == []
    overlap = [("&lt; 10", ['"a"']), ("[5..20]", ['"b"']), ("&gt; 20", ['"c"'])]
    assert set(rules_of(s4.run_dmn(instance({"decision-tables/t.dmn": dmn(overlap)})))) == {"DMN-OVERLAP"}
    assert rules_of(s4.run_dmn(instance({"decision-tables/t.dmn": dmn(overlap, policy="FIRST")}))) == []
    same = [("&lt; 10", ['"a"']), ("[5..20]", ['"a"']), ("&gt; 20", ['"c"'])]
    assert rules_of(s4.run_dmn(instance({"decision-tables/t.dmn": dmn(same, policy="ANY")}))) == []
    assert rules_of(s4.run_dmn(instance({"decision-tables/t.dmn": dmn(overlap, policy="ANY")}))) == ["DMN-OVERLAP", "DMN-OVERLAP"]
    untyped = s4.run_dmn(instance({"decision-tables/t.dmn": dmn([("-", ['""', ""])],
                                                                outputs='<output id="o" label="y" typeRef="string"/><output id="p" label="z"/>')}))
    assert rules_of(untyped) == ["DMN-UNTYPED-OUTPUT", "DMN-UNTYPED-OUTPUT"]   # z has no typeRef, and r0 leaves z empty
    strings = [('"a","b"', ['"x"']), ('"c"', ['"y"'])]
    assert rules_of(s4.run_dmn(instance({"decision-tables/t.dmn": dmn(strings, typeref="string")}))) == []
    unread = s4.run_dmn(instance({"decision-tables/t.dmn": dmn([("not(1)", ['"a"'])])}))
    assert [(f["rule"], f["severity"]) for f in unread["findings"]] == [("DMN-UNREAD", "info")]
    assert s4.run_dmn(instance({"plantuml-models/a.puml": "@startuml\n@enduml\n"}))["state"] == "unchecked"


def test_the_glossary_check_wants_a_row_for_a_term_in_three_requirements():
    reqs = "| id | requirement |\n|---|---|\n" + "".join(f"| R-{i} | the **chargeable mass** and `tariff` of step {i} |\n" for i in (1, 2, 3))
    reqs += "| R-4 | a `tariff` only |\n"
    gloss = "# Glossary\n\n| term | definition |\n|---|---|\n| tariff | the price list |\n"
    got = s4.run_glossary(instance({"textual-requirements/r.md": reqs, "glossary/g.md": gloss}))
    assert [(f["rule"], f["line"]) for f in got["findings"]] == [("GLOSSARY-UNDEFINED", 3)]
    assert "'chargeable mass' recurs in 3 requirements (R-1, R-2, R-3)" in got["findings"][0]["message"]
    two = reqs.replace("| R-3 | the **chargeable mass**", "| R-3 | the mass")
    assert s4.run_glossary(instance({"textual-requirements/r.md": two, "glossary/g.md": gloss}))["findings"] == []
    none = s4.run_glossary(instance({"textual-requirements/r.md": reqs}))
    assert none["state"] == "unchecked" and "no glossary" in none["why"]
    assert s4.glossary_terms("- **chargeable mass**: the greater\n## Tariff\n`band` - a band\n") == {"chargeable mass", "tariff", "band"}


def _stand_in(d: Path, version: str, report: dict | None) -> list[str]:
    script = d / "pumllint_stand_in.py"
    script.write_text("import json, sys\nargs = sys.argv[1:]\n"
                      f"if args == ['--version']:\n    print('pumllint {version}')\n    sys.exit(0)\n"
                      f"open(args[args.index('-o') + 1], 'w').write({json.dumps(json.dumps(report))})\n", encoding="utf-8")
    return [sys.executable, str(script)]


def test_the_trace_needs_pumllint_0_35_and_maps_its_report_to_findings():
    files = {"plantuml-models/flow.puml": "@startuml flow\ntitle REQ-1 REQ-9\n@enduml\n",
             "acceptance-scenarios/a.feature": "Feature: A\n  @REQ-8\n  Scenario: one\n    Given x\n",
             "textual-requirements/r.md": "| id | r |\n|---|---|\n| REQ-1 | one |\n| REQ-2 | two |\n"}
    inst = instance(files)
    real = preload_check.pumllint_cmd
    try:
        preload_check.pumllint_cmd = lambda: _stand_in(inst, "0.33.0", None)   # the pumllint the harness would run
        got = s4.run_trace(inst)
        assert got["state"] == "unchecked" and "needs pumllint 0.35.0" in got["why"] and "0.33.0" in got["why"]
        cite = {"file": "artefacts/plantuml-models/flow.puml", "name": "flow", "line": 2}
        report = {"requirements": [{"id": "REQ-1", "covered": True, "verified": False}, {"id": "REQ-2", "covered": False, "verified": False}],
                  "unknownReferences": [{"id": "REQ-9", "citedBy": [cite]}],
                  "unknownFeatureReferences": [{"id": "REQ-8", "citedBy": [{"file": "artefacts/acceptance-scenarios/a.feature", "line": 1,
                                                                            "scenario": "one", "scenarioLine": 3}]}],
                  "unlinkedDiagrams": [], "unlinkedFeatures": [], "unlinkedScenarios": []}
        preload_check.pumllint_cmd = lambda: _stand_in(inst, "0.35.0", report)
        got = s4.run_trace(inst)
        assert got["state"] == "ran" and got["version"] == "0.35.0"
        assert sorted((f["file"].split("/")[1], f["rule"], f["severity"], f["line"]) for f in got["findings"]) == [
            ("acceptance-scenarios", "TRACE-UNKNOWN-FEATURE-REF", "major", 3), ("plantuml-models", "TRACE-UNKNOWN-REF", "major", 2),
            ("textual-requirements", "TRACE-UNCOVERED", "minor", 4), ("textual-requirements", "TRACE-UNVERIFIED", "minor", 3)]
    finally:
        preload_check.pumllint_cmd = real


def test_a_document_only_a_check_judged_is_judged_by_it_and_its_findings_are_lint_gaps_named_by_it():
    bands = [("&lt;= 41", ['"a"']), ("[42..66]", ['"b"']), ("&gt;= 67", ['"c"'])]
    inst = instance({"decision-tables/t.dmn": dmn(bands), "decision-tables/t.md": "| a | b |\n"})
    old = {k: os.environ.pop(k, None) for k in ("KG_DMNLINT",)}
    real = preload_check.pumllint_cmd
    preload_check.pumllint_cmd = lambda: None   # no pumllint either: the trace unchecked
    path = os.environ.get("PATH", "")
    os.environ["PATH"] = ""   # no dmnlint here: the kind's own linter cannot run
    try:
        rep = preload_check.check(inst)
    finally:
        os.environ["PATH"] = path
        preload_check.pumllint_cmd = real
        for k, v in old.items():
            if v is not None:
                os.environ[k] = v
    assert schema_check.validate(rep, schema_check.load("preload-report")) == []
    rows = {r["file"]: r for r in rep["files"]}
    t = rows["artefacts/decision-tables/t.dmn"]
    assert (t["state"], t["tool"]) == ("unchecked", "dmn gaps") and "judged by dmn gaps alone" in t["why"] and "dmnlint" in t["why"]
    assert [(f["rule"], f["tool"]) for f in t["findings"]] == [("DMN-GAP", "dmn gaps")] * 2
    assert rows["artefacts/decision-tables/t.md"]["state"] == "unchecked"   # not DMN: no check read it
    assert {c["check"]: c["state"] for c in rep["checks"]} == {"pumllint trace": "unchecked", "glossary": "unchecked", "dmn gaps": "ran"}
    # task-0312 R1: through the load's own reader, the row stays unchecked and its findings still load as lint gaps
    import hashlib
    (inst / "subjects" / "s").mkdir(parents=True)

    class Sub:
        root = inst / "subjects" / "s"
        artefacts = [{"key": "contract/t.dmn", "path": "../../artefacts/decision-tables/t.dmn"}]

        def version_digest(self, key, text):
            return (hashlib.sha256(text.encode("utf-8")).hexdigest(),)

    kit = {"contract/t.dmn": (inst / "artefacts/decision-tables/t.dmn").read_text(encoding="utf-8")}
    v = preload.verdicts(Sub(), kit, ["contract/t.dmn"], rep, "preload-report.json")["contract/t.dmn"]
    assert v["state"] == "unchecked" and v["tool"] == "dmn gaps" and v["digest"] == t["sha256"], v
    gaps = preload.lint_gaps("contract/t.dmn", "v1", v)
    assert [g["tool"] for g in gaps] == ["dmn gaps"] * 2 and gaps[0]["text"].startswith("dmn gaps DMN-GAP (minor)")
    import gate_cli
    [info] = [f for f in gate_cli.findings({"keys": {}, "verdict": "PROCEED", "preload": [{"artefact": "contract/t.dmn", "version": "v1", "keys": ["K|x"], "state": "unchecked",
                                                                  "tool": "dmn gaps", "why": v["why"]}]}, set())
              if f["kind"] == "preload"]
    assert "judged by dmn gaps alone, its linter never ran" in info["message"] and "form was not checked" not in info["message"], info
    assert info["message"].count("judged by") == 1 and "dmnlint is not installed here" in info["message"], info   # said once (L3)


def test_the_changelog_names_it_and_the_trace_runs_on_the_pinned_pumllint():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## 0.9.0 ", 1)[1].split("\n## ", 1)[0]
    assert "task-0217" in log
    for f in ("tools/step4_checks.py", "tools/check_preload_linters.py", "instance/README.md"):
        assert "KG_PUMLLINT_TRACE" not in (ROOT / f).read_text(encoding="utf-8"), f   # no side install: the pin is the trace's


def test_a_row_two_checks_read_keeps_the_first_as_its_tool_task_0312_r5():
    dmn_file = "artefacts/decision-tables/t.dmn"
    inst = instance({"decision-tables/t.dmn": dmn([("<= 41", ['"a"']), ("[42..66]", ['"b"']), (">= 67", ['"c"'])])})
    one = lambda name: (("decision-tables",), lambda i: {"state": "ran", "why": "", "version": None, "files": 1, "findings": [], "read": [dmn_file]})  # noqa: E731
    saved, real = dict(s4.CHECKS), preload_check.pumllint_cmd
    path = os.environ.get("PATH", "")
    s4.CHECKS.clear()
    s4.CHECKS.update({"first": one("first"), "second": one("second")})
    preload_check.pumllint_cmd = lambda: None
    os.environ["PATH"] = ""
    try:
        rep = preload_check.check(inst)
    finally:
        os.environ["PATH"] = path
        preload_check.pumllint_cmd = real
        s4.CHECKS.clear()
        s4.CHECKS.update(saved)
    [t] = [r for r in rep["files"] if r["file"] == dmn_file]
    assert t["tool"] == "first" and t["state"] == "unchecked" and "judged by first alone" in t["why"], t
