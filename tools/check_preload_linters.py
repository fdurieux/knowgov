"""The pre-load check's Node linters (task-0082), real and pinned, through the CI template's script, on
the example instance: markdownlint for specification-prose, gplint for acceptance-scenarios, bpmnlint
for bpmn-process-models, dmnlint for the .dmn files of decision-tables.

    python tools/check_preload_linters.py OUT_DIR

Each linter is KG_MARKDOWNLINT, KG_GPLINT, KG_BPMNLINT, KG_DMNLINT or the command on PATH; one that
is missing exits 2 naming it (this proof never passes on an unchecked kind).

1. The example instance's own documents of the four kinds that are clean under the shipped
   configurations (spec.md, acceptance.feature, screening_decision.dmn): each CLEAN under its tool,
   exit 0. Its decision_table.md stays unchecked, dmnlint reading .dmn only. Its BPMN model has no
   diagram interchange and no incoming/outgoing references: bpmnlint's recommended rules find it,
   and this proof says so rather than hiding it behind a looser configuration.
2. The instance committed; a clean file of each kind planted and committed; instance/ci/preload-check.sh
   with the parent as base lints only those four: exit 0.
3. A broken file of each kind planted and committed: the script exits 1; preload_check.py -f json names
   each tool with the rule it broke, every finding major, and the report is valid against
   harness/schemas/preload-report.schema.json.
4. Step 4's checks (task-0217), each finding its planted defect, each finding in the report with its tool:
   the feature trace, on the harness's pinned pumllint (0.35.0 or later: an older one is cannot-run here, this
   proof never passing on an unchecked check), a diagram and a scenario citing ids no requirement holds; the glossary, a term in three requirements the
   glossary does not define (and none once it does); the DMN check, the example's own table's two gaps, then
   a table whose rules overlap under UNIQUE and leave an output untyped.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import example_instance  # noqa: E402
import preload_check  # noqa: E402
import schema_check  # noqa: E402
import step4_checks  # noqa: E402


KINDS = {"specification-prose": "markdownlint", "acceptance-scenarios": "gplint",
         "bpmn-process-models": "bpmnlint", "decision-tables": "dmnlint"}
CMDS = {"markdownlint": preload_check.markdownlint_cmd, "gplint": preload_check.gplint_cmd,
        "bpmnlint": preload_check.bpmnlint_cmd, "dmnlint": preload_check.dmnlint_cmd}

BPMN_HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
             'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
             'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="d" targetNamespace="http://example.org/x">\n')
CLEAN = {
    "specification-prose/clean.md": "# Clean\n\nOne paragraph.\n\n* one item\n* another\n",
    "acceptance-scenarios/clean.feature": "Feature: Clean\n\n  Scenario: one\n    Given a\n    Then b\n",
    "bpmn-process-models/clean.bpmn": BPMN_HEAD + """  <bpmn:process id="p" isExecutable="false">
    <bpmn:startEvent id="s" name="Start"><bpmn:outgoing>f1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="t" name="Do"><bpmn:incoming>f1</bpmn:incoming><bpmn:outgoing>f2</bpmn:outgoing></bpmn:task>
    <bpmn:endEvent id="e" name="End"><bpmn:incoming>f2</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="f1" sourceRef="s" targetRef="t"/>
    <bpmn:sequenceFlow id="f2" sourceRef="t" targetRef="e"/>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="dg"><bpmndi:BPMNPlane id="pl" bpmnElement="p">
    <bpmndi:BPMNShape id="s_di" bpmnElement="s"><dc:Bounds x="0" y="0" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="t_di" bpmnElement="t"><dc:Bounds x="100" y="0" width="100" height="80"/></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="e_di" bpmnElement="e"><dc:Bounds x="300" y="0" width="36" height="36"/></bpmndi:BPMNShape>
    <bpmndi:BPMNEdge id="f1_di" bpmnElement="f1"><di:waypoint x="36" y="18"/><di:waypoint x="100" y="18"/></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="f2_di" bpmnElement="f2"><di:waypoint x="200" y="18"/><di:waypoint x="300" y="18"/></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
</bpmn:definitions>
""",
    "decision-tables/clean.dmn": """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/" id="d" name="Clean" namespace="http://example.org/x">
  <decision id="named" name="A named decision">
    <decisionTable id="t"><input id="i" label="x"><inputExpression typeRef="number"><text>x</text></inputExpression></input><output id="o" label="y" typeRef="string"/></decisionTable>
  </decision>
</definitions>
""",
}
# file -> (the rule the linter must name, the file's text)
BROKEN = {
    "specification-prose/broken.md": ("MD025", "# One\n\nText.\n\n# Two\n\nMore text.\n"),
    "acceptance-scenarios/broken.feature": ("no-dupe-scenario-names", "Feature: Broken\n\n  Scenario: one\n    Given a\n\n  Scenario: one\n    Then b\n"),
    "bpmn-process-models/broken.bpmn": ("parse-error", BPMN_HEAD + '  <bpmn:process id="p"><bpmn:task id="t"/></bpmn:proc\n'),
    "decision-tables/broken.dmn": ("label-required", CLEAN["decision-tables/clean.dmn"].replace(' name="A named decision"', "")),
}


def _git(inst: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(inst), "-c", "user.name=ci", "-c", "user.email=ci@example.invalid", *args], check=True, capture_output=True)


def _plant(inst: Path, files: dict, msg: str) -> None:
    for rel, text in files.items():
        (inst / "artefacts" / rel).write_text(text if isinstance(text, str) else text[1], encoding="utf-8")
    _git(inst, "add", "-A")
    _git(inst, "commit", "-qm", msg)


def _script(inst: Path, base: str) -> tuple[int, str]:
    p = subprocess.run(["sh", str(ROOT / "instance" / "ci" / "preload-check.sh"), str(ROOT), str(inst), base], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    missing = [t for t, cmd in CMDS.items() if cmd() is None]
    if missing:
        print(f"cannot run: not installed here: {', '.join(missing)}", file=sys.stderr)
        return 2
    trace = step4_checks.trace_cmd()
    ver = subprocess.run(trace + ["--version"], capture_output=True, text=True) if trace else None
    have = step4_checks._version(ver.stdout + ver.stderr) if ver and ver.returncode == 0 else None
    if have is None or have < step4_checks.TRACE_NEEDS:
        print(f"cannot run: the feature trace needs pumllint {'.'.join(map(str, step4_checks.TRACE_NEEDS))} or later; "
              f"here: {'.'.join(map(str, have)) if have else 'none'}", file=sys.stderr)
        return 2
    out = Path(argv[0])
    shutil.rmtree(out, ignore_errors=True)
    inst = out / "instance"
    example_instance.build(inst)
    schema = schema_check.load("preload-report")

    # 1. the example's own documents
    own = ["artefacts/specification-prose/spec.md", "artefacts/acceptance-scenarios/acceptance.feature",
           "artefacts/decision-tables/screening_decision.dmn", "artefacts/decision-tables/decision_table.md"]
    rep = preload_check.check(inst, own)
    assert not schema_check.validate(rep, schema)
    got = {r["file"]: (r["state"], r["tool"]) for r in rep["files"]}
    assert got == {own[0]: ("clean", "markdownlint"), own[1]: ("clean", "gplint"), own[2]: ("clean", "dmnlint"),
                   own[3]: ("unchecked", "dmnlint (small rule set)")}, got
    assert rep["exit_code"] == 0 and "reads .dmn files only" in rep["files"][3]["why"], rep["files"][3]
    for lt in rep["linters"]:
        print(f"{lt['tool']} {lt['version']} on {lt['kind']}: exit {lt['exit']}")
    bpmn = preload_check.check(inst, ["artefacts/bpmn-process-models/quote_process.bpmn"])
    [b] = bpmn["files"]
    rules = {f["rule"] for f in b["findings"]}
    assert b["state"] == "findings" and {"no-bpmndi", "no-disconnected"} <= rules, (b["state"], rules)
    print(f"the example's own BPMN model: {b['why']} ({', '.join(sorted(rules))})")

    # 2. clean files of each kind through the template's script
    _git(inst, "init", "-q", "-b", "main")
    _git(inst, "add", "-A")
    _git(inst, "commit", "-qm", "instance")
    _plant(inst, CLEAN, "clean")
    rc, text = _script(inst, "HEAD~1")
    assert rc == 0, text
    for rel in CLEAN:
        kind = rel.split("/")[0]
        assert f"CLEAN      artefacts/{rel} [{kind}] {KINDS[kind]}" in text, (rel, text)
    print("clean: exit 0,", ", ".join(CLEAN))

    # 3. broken files of each kind
    _plant(inst, BROKEN, "broken")
    rc, text = _script(inst, "HEAD~1")
    assert rc == 1, text
    rep = preload_check.check(inst, [f"artefacts/{rel}" for rel in BROKEN])
    errors = schema_check.validate(rep, schema)
    assert not errors, errors
    assert rep["exit_code"] == 1
    for r in rep["files"]:
        rel = r["file"].removeprefix("artefacts/")
        rule = BROKEN[rel][0]
        assert r["state"] == "findings" and r["tool"] == KINDS[r["kind"]], r
        assert any(f["rule"] == rule and f["severity"] == "major" for f in r["findings"]), (rule, r["findings"])
        print(f"broken: {r['file']} {r['tool']} {rule}: {r['why']}")
    print("broken: exit 1")
    step4(out)
    return 0


def _findings(rep: dict, tool: str) -> dict[str, list[tuple[str, str]]]:
    got: dict[str, list[tuple[str, str]]] = {}
    for r in rep["files"]:
        for f in r["findings"]:
            if f.get("tool") == tool:
                got.setdefault(r["file"], []).append((f["rule"], f["severity"]))
    return got


def step4(out: Path) -> None:
    schema = schema_check.load("preload-report")
    inst = out / "step4"
    example_instance.build(inst)
    checks = lambda rep: {c["check"]: c for c in rep["checks"]}  # noqa: E731

    # the trace, on the pinned pumllint: the planted ids found
    (inst / "pumllint.toml").write_text('[rules.requirement-link]\npattern = "REQ-\\\\d+"\n', encoding="utf-8")
    diagram = inst / "artefacts" / "plantuml-models" / "quote_flow.puml"
    feature = inst / "artefacts" / "acceptance-scenarios" / "acceptance.feature"
    rep = preload_check.check(inst)
    assert checks(rep)[step4_checks.TRACE]["state"] == "ran", f"cannot run: {checks(rep)[step4_checks.TRACE]['why']}"
    before = _findings(rep, step4_checks.TRACE)
    assert not any(r.startswith("TRACE-UNKNOWN") for fs in before.values() for r, _ in fs), before
    text = diagram.read_text(encoding="utf-8")
    diagram.write_text(text.replace("\n", "\ntitle Quote flow REQ-01 REQ-99\n", 1), encoding="utf-8")
    lines = feature.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(i for i, x in enumerate(lines) if x.lstrip().startswith("Scenario"))
    lines.insert(at, " " * (len(lines[at]) - len(lines[at].lstrip())) + "@REQ-01 @REQ-98\n")
    feature.write_text("".join(lines), encoding="utf-8")
    rep = preload_check.check(inst)
    assert not schema_check.validate(rep, schema), schema_check.validate(rep, schema)
    got = _findings(rep, step4_checks.TRACE)
    d, f = diagram.relative_to(inst).as_posix(), feature.relative_to(inst).as_posix()
    assert ("TRACE-UNKNOWN-REF", "major") in got.get(d, []) and ("TRACE-UNKNOWN-FEATURE-REF", "major") in got.get(f, []), got
    print(f"trace {checks(rep)[step4_checks.TRACE]['version']}: REQ-99 in {d} and REQ-98 in {f}, major; "
          f"{sum(map(len, got.values()))} trace findings in all")

    # the glossary: three requirements naming a term the glossary lacks; none once it has a row
    (inst / "artefacts" / "glossary").mkdir(exist_ok=True)
    gloss = inst / "artefacts" / "glossary" / "glossary.md"
    gloss.write_text("# Glossary\n\n| term | definition |\n|---|---|\n| quote | a priced offer |\n", encoding="utf-8")
    reqs = inst / "artefacts" / "textual-requirements" / "planted.md"
    reqs.write_text("| id | requirement |\n|---|---|\n" + "".join(
        f"| PL-{i} | the **chargeable mass** decides step {i} |\n" for i in (1, 2, 3)), encoding="utf-8")
    rep = preload_check.check(inst)
    got = _findings(rep, step4_checks.GLOSSARY)
    r = reqs.relative_to(inst).as_posix()
    assert got.get(r) == [("GLOSSARY-UNDEFINED", "minor")], got
    gloss.write_text(gloss.read_text(encoding="utf-8") + "| chargeable mass | the greater of the gross and the volumetric mass |\n",
                     encoding="utf-8")
    assert not _findings(preload_check.check(inst), step4_checks.GLOSSARY).get(r), "the defined term is still a finding"
    print(f"glossary: 'chargeable mass' in three requirements of {r}, undefined: minor; defined: none")

    # the DMN check: the example's own table's two gaps, then a planted overlap and untyped output
    own = "artefacts/decision-tables/screening_decision.dmn"
    got = _findings(rep, step4_checks.DMN)
    assert got.get(own) == [("DMN-GAP", "minor"), ("DMN-GAP", "minor")], got
    dmn = inst / "artefacts" / "decision-tables" / "planted.dmn"
    dmn.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/" id="p" name="Planted" namespace="http://example.org/x">
  <decision id="band" name="Band">
    <decisionTable id="t_band" hitPolicy="UNIQUE">
      <input id="i" label="mass"><inputExpression typeRef="number"><text>mass</text></inputExpression></input>
      <output id="o_band" label="band" typeRef="string"/>
      <output id="o_note" label="note"/>
      <rule id="r_low"><inputEntry><text>&lt; 10</text></inputEntry><outputEntry><text>"low"</text></outputEntry><outputEntry><text>"a"</text></outputEntry></rule>
      <rule id="r_mid"><inputEntry><text>[5..20]</text></inputEntry><outputEntry><text>"mid"</text></outputEntry><outputEntry><text>"b"</text></outputEntry></rule>
      <rule id="r_high"><inputEntry><text>&gt; 20</text></inputEntry><outputEntry><text>"high"</text></outputEntry><outputEntry><text></text></outputEntry></rule>
    </decisionTable>
  </decision>
</definitions>
""", encoding="utf-8")
    rep = preload_check.check(inst)
    assert not schema_check.validate(rep, schema), schema_check.validate(rep, schema)
    got = _findings(rep, step4_checks.DMN).get(dmn.relative_to(inst).as_posix(), [])
    assert ("DMN-OVERLAP", "major") in got and got.count(("DMN-UNTYPED-OUTPUT", "minor")) == 2 and ("DMN-GAP", "minor") not in got, got
    print(f"dmn: {own} two gaps, minor; planted.dmn {', '.join(sorted({r for r, _ in got}))}")


if __name__ == "__main__":
    import _outcomes   # task-0314 R5
    _outcomes.help_exit(__doc__)
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(lambda: main(sys.argv[1:])))
