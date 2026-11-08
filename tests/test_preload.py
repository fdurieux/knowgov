"""Task-0045: the pre-load check. Each document is linted by its kind's linter where one runs here,
every other kind's files are listed as unchecked naming the tool the programme's table names, and
the exit follows the gate contract (0 clean, 1 findings at or above the threshold, 2 cannot run).
The tests job installs no linter, so pumllint is stood in for by a script that speaks its command
line and its JSON report; harness.yml runs the real one, through the CI template's script, on the
example instance."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import check_instance  # noqa: E402
import example_instance  # noqa: E402
import preload_check  # noqa: E402
import schema_check  # noqa: E402

# pumllint's command line, as preload_check calls it: --version; -f json -o OUT --fail-on SEV FILE...
# A line holding "BROKEN <name>" is a critical finding naming it ("BROKEN WORSE": a blocker); every file gets an info one.
FAKE = r'''
import json, sys
a = sys.argv[1:]
if a == ["--version"]:
    print("pumllint 0.0-standin"); sys.exit(0)
out = a[a.index("-o") + 1]; fail = a[a.index("--fail-on") + 1]
files = [x for i, x in enumerate(a) if not x.startswith("-") and a[i - 1] not in ("-f", "-o", "--fail-on")]
ladder = ["info", "minor", "major", "critical", "blocker"]
found = []
for f in files:
    found.append({"ruleId": "GEN002", "severity": "info", "message": "no name", "file": f, "line": 1})
    for n, line in enumerate(open(f, encoding="utf-8"), 1):
        if "BROKEN" in line:
            found.append({"ruleId": "SEQ001", "severity": "blocker" if "WORSE" in line else "critical",
                          "message": ("undeclared " + line.split("BROKEN")[1].strip()).strip(), "file": f, "line": n})
json.dump(found, open(out, "w"))
sys.exit(1 if any(ladder.index(x["severity"]) >= ladder.index(fail) for x in found) else 0)
'''


# Spectral's command line, as preload_check calls it: --version; lint -r RULESET -f json -o OUT -q --fail-severity
# hint FILE... A line holding "BROKEN" is an error (severity 0, invalid-ref); every file gets a warning.
FAKE_SPECTRAL = r'''
import json, sys
a = sys.argv[1:]
if a == ["--version"]:
    print("6.0.0-standin"); sys.exit(0)
assert a[0] == "lint" and "-r" in a and a[a.index("-f") + 1] == "json", a
out = a[a.index("-o") + 1]
files = [x for i, x in enumerate(a[1:], 1) if not x.startswith("-") and a[i - 1] not in ("-r", "-f", "-o", "--fail-severity")]
found = []
for f in files:
    found.append({"code": "info-contact", "severity": 1, "message": "no contact", "source": f, "range": {"start": {"line": 0}}})
    for n, line in enumerate(open(f, encoding="utf-8")):
        if "BROKEN" in line:
            found.append({"code": "invalid-ref", "severity": 0, "message": "does not exist", "source": f, "range": {"start": {"line": n}}})
json.dump(found, open(out, "w"))
sys.exit(1 if found else 0)
'''


# markdownlint-cli2's command line, as preload_check calls it: --help (its version line); [--config FILE] :FILE...;
# its default text report on stderr. A line holding "BROKEN" is an error (MD025); "WARN" a warning (MD009).
FAKE_MARKDOWNLINT = r"""
import sys
a = sys.argv[1:]
if a == ["--help"]:
    print("markdownlint-cli2 v0.0-standin (markdownlint v0.0)"); sys.exit(0)
files = [x[1:] for x in a if x.startswith(":")]
assert files and len(files) == len([x for x in a if not x.startswith("-")]) - (1 if "--config" in a else 0), a
out = []
for f in files:
    for n, line in enumerate(open(f, encoding="utf-8"), 1):
        if "BROKEN" in line:
            out.append(f"{f}:{n} error MD025/single-title/single-h1 Multiple top-level headings in the same document")
        if "WARN" in line:
            out.append(f"{f}:{n}:3 warning MD009/no-trailing-spaces Trailing spaces")
print("markdownlint-cli2 v0.0-standin (markdownlint v0.0)")
print("\n".join(out), file=sys.stderr)
sys.exit(1 if out else 0)
"""

# gplint's: --version; -c CONFIG -f json FILE...; a message naming a file names it absolute, as gplint does.
FAKE_GPLINT = r"""
import json, sys
a = sys.argv[1:]
if a == ["--version"]:
    print("0.0-standin"); sys.exit(0)
assert a[0] == "-c" and a[2:4] == ["-f", "json"], a
rep = []
for f in a[4:]:
    errs = [{"level": 2, "rule": "no-dupe-scenario-names", "line": n, "column": 3, "message": "Scenario name is already used in: " + f + ":1"}
            for n, line in enumerate(open(f, encoding="utf-8"), 1) if "BROKEN" in line]
    rep.append({"filePath": f, "errors": errs})
print(json.dumps(rep))
sys.exit(1 if any(r["errors"] for r in rep) else 0)
"""

# bpmnlint's and dmnlint's: --version; -c CONFIG FILE...; their text report on stdout, files with no
# problem not named. "BROKEN" is an error on element e1; "MANGLED" a parse error (no element, no rule).
FAKE_BPMN_IO = r"""
import sys
a = sys.argv[1:]
if a == ["--version"]:
    print("0.0.0"); sys.exit(0)
assert a[0] == "-c", a
out, n = [], 0
for f in a[2:]:
    text = open(f, encoding="utf-8").read()
    rows = []
    if "BROKEN" in text:
        rows.append("  e1   error    Element is missing label/name  label-required")
        rows.append("  e2   warning  Sequence flow has superfluous label  superfluous-label")
    if "MANGLED" in text:
        rows.append("    error  Parse error: unparsable content </x  ")
        rows.append("           	line: 0                ")
    if rows:
        out += ["", f] + rows
        n += len(rows)
if n:
    out += ["", f"✖ {n} problems"]
print("\n".join(out))
sys.exit(1 if n else 0)
"""

NODE = {"markdownlint_cmd": FAKE_MARKDOWNLINT, "gplint_cmd": FAKE_GPLINT, "bpmnlint_cmd": FAKE_BPMN_IO, "dmnlint_cmd": FAKE_BPMN_IO}


class _Standin:
    """pumllint and Spectral stood in for; present=False: neither is installed. node=True also stands in the
    Node linters (task-0082); by default they are not installed, so a test never reads the environment's."""
    def __init__(self, td: Path, present: bool = True, node: bool = False):
        self.script = td / "fake_pumllint.py"
        self.script.write_text(FAKE, encoding="utf-8")
        self.spectral = td / "fake_spectral.py"
        self.spectral.write_text(FAKE_SPECTRAL, encoding="utf-8")
        self.present = present
        self.nodes = node
        self.node = {}
        for name, src in NODE.items():
            f = td / f"fake_{name}.py"
            f.write_text(src, encoding="utf-8")
            self.node[name] = f

    def __enter__(self):
        self.saved = {n: getattr(preload_check, n) for n in ("pumllint_cmd", "spectral_cmd", *NODE)}
        preload_check.pumllint_cmd = (lambda: [sys.executable, str(self.script)]) if self.present else (lambda: None)
        preload_check.spectral_cmd = (lambda: [sys.executable, str(self.spectral)]) if self.present else (lambda: None)
        for name, f in self.node.items():
            setattr(preload_check, name, (lambda f=f: [sys.executable, str(f)]) if self.present and self.nodes else (lambda: None))

    def __exit__(self, *exc):
        for n, f in self.saved.items():
            setattr(preload_check, n, f)


def _digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def _valid(rep: dict) -> None:
    errors = schema_check.validate(rep, schema_check.load("preload-report"))
    assert not errors, errors


def test_the_clean_example_instance_exits_0_and_lists_every_unchecked_kind_by_its_tool():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        before = _digest(out)
        with _Standin(Path(td)):
            rep = preload_check.check(out)
            assert preload_check.main([str(out)]) == 0
        _valid(rep)
        assert rep["exit_code"] == 0 and rep["scope"] == "all" and rep["threshold"] == "major"
        states = {r["file"]: (r["state"], r["tool"]) for r in rep["files"]}
        assert states["artefacts/plantuml-models/quote_flow.puml"] == ("clean", "pumllint")
        assert states["artefacts/api-contracts/openapi.yaml"] == ("clean", "Spectral")
        assert states["artefacts/specification-prose/spec.md"] == ("unchecked", "markdownlint")
        assert states["artefacts/decision-tables/decision_table.md"] == ("unchecked", "dmnlint (small rule set)")
        assert states["artefacts/textual-requirements/requirements.md"] == ("unchecked", "StrictDoc, Doorstop, Sphinx-Needs, OpenFastTrace")
        # dmnlint not installed: the screening table is judged by step 4's DMN check alone (task-0217), its two gaps minor
        assert states["artefacts/decision-tables/screening_decision.dmn"] == ("clean", "dmn gaps")
        assert rep["counts"] == {"clean": 4, "findings": 0, "held": 0, "unchecked": 6, "cannot_run": 0, "skipped": 0}, rep["counts"]
        lts = {lt["tool"]: (lt["version"], lt["files"], lt["exit"]) for lt in rep["linters"]}
        assert lts == {"pumllint": ("0.0-standin", 2, 0), "Spectral": ("6.0.0-standin", 1, 0), "markdownlint": (None, 1, 2),
                       "gplint": (None, 1, 2), "bpmnlint": (None, 1, 2), "dmnlint": (None, 1, 2)}, lts
        assert all(r["state"] in ("clean", "unchecked") for r in rep["files"])
        text = preload_check.render(rep)
        assert "UNCHECKED  artefacts/bpmn-process-models/quote_process.bpmn [bpmn-process-models]: form unchecked: bpmnlint is not installed here" in text
        assert "UNCHECKED  artefacts/textual-requirements/requirements.md [textual-requirements]: form unchecked: the table names StrictDoc" in text
        assert "not the knowledge in it (harness/gate_cli.py)" in text
        assert _digest(out) == before, "the check wrote into the instance"


def test_a_broken_plantuml_file_exits_1_and_the_threshold_moves_it():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        (out / "artefacts" / "plantuml-models" / "broken.puml").write_text("@startuml\nA -> B : BROKEN\n@enduml\n", encoding="utf-8")
        changed = ["artefacts/plantuml-models/broken.puml", "subjects/cargo_quote/subject.toml"]
        with _Standin(Path(td)):
            rep = preload_check.check(out, changed)
            assert preload_check.main([str(out), "--changed", *changed]) == 1
            assert preload_check.main([str(out), "--changed", *changed, "--fail-on", "blocker"]) == 0
            assert preload_check.main([str(out), "--changed", "artefacts/plantuml-models/quote_flow.puml"]) == 0
            low = preload_check.check(out, ["artefacts/plantuml-models/quote_flow.puml"], "info")
        _valid(rep)
        broken, manifest = rep["files"]
        assert broken["state"] == "findings" and [f["rule"] for f in broken["findings"]] == ["SEQ001", "GEN002"], broken
        assert broken["findings"][0] == {"rule": "SEQ001", "severity": "critical", "line": 2, "message": "undeclared"}
        assert manifest["state"] == "skipped" and manifest["kind"] is None
        assert rep["scope"] == "changed" and rep["exit_code"] == 1
        assert low["files"][0]["state"] == "findings" and low["exit_code"] == 1, "an info finding fails at --fail-on info"


def test_what_cannot_be_checked_exits_2_and_a_missing_linter_leaves_its_kind_unchecked():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        (out / "artefacts" / "slides").mkdir()
        (out / "artefacts" / "slides" / "deck.md").write_text("x\n", encoding="utf-8")
        with _Standin(Path(td)):
            for changed, why in ((["artefacts/slides/deck.md"], "not a kind of instance/kinds.toml"),
                                 (["artefacts/plantuml-models/gone.puml"], "does not exist"),
                                 (["/etc/hostname"], "outside the instance")):
                rep = preload_check.check(out, changed)
                assert rep["exit_code"] == 2 and why in rep["files"][0]["why"], rep["files"]
                assert preload_check.main([str(out), "--changed", *changed]) == 2
        with _Standin(Path(td), present=False):
            # task-0066: a linter not installed here leaves its kind unchecked, naming it; never passed, never cannot-run
            rep = preload_check.check(out, ["artefacts/plantuml-models/quote_flow.puml", "artefacts/api-contracts/openapi.yaml"])
            assert rep["exit_code"] == 0 and [r["state"] for r in rep["files"]] == ["unchecked", "unchecked"], rep["files"]
            assert "pumllint is not installed here" in rep["files"][0]["why"] and rep["files"][1]["tool"] == "Spectral"
            assert "Spectral is not installed here" in rep["files"][1]["why"]
            _valid(rep)
        assert preload_check.main([str(Path(td) / "nope")]) == 2


def test_a_kind_with_no_linter_is_reported_unchecked_and_says_the_table_names_none():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        (out / "artefacts" / "glossary").mkdir()
        (out / "artefacts" / "glossary" / "terms.md").write_text("quote: a price\n", encoding="utf-8")
        with _Standin(Path(td)):
            rep = preload_check.check(out, ["artefacts/glossary/terms.md"])
        [r] = rep["files"]
        assert r["state"] == "unchecked" and r["tool"] == "none" and "names no linter" in r["why"] and rep["exit_code"] == 0


def test_every_runner_names_the_tool_its_kind_names_and_the_ci_template_runs_the_script():
    table = check_instance.kinds()
    runs = {kind: k["lint"]["runs"] for kind, k in table.items() if "runs" in k["lint"]}
    assert runs == {kind: tool for kind, (tool, _) in preload_check.RUNNERS.items()}, "kinds.toml runs and RUNNERS differ"
    for kind, tool in runs.items():   # "dmnlint (small rule set)" names dmnlint; capable stays doc-0008 §5's column, the runner gives the threshold
        assert tool in [x.strip().split()[0] for x in table[kind]["lint"]["tool"].split(",")], kind
    ci = ROOT / "instance" / "ci"
    script = (ci / "preload-check.sh").read_text(encoding="utf-8")
    assert "tools/preload_check.py" in script and "tools/check_instance.py" in script and "--since" in script
    wf = (ci / "preload-check.yml").read_text(encoding="utf-8")
    assert "sh knowgov/instance/ci/preload-check.sh knowgov instance" in wf and "fetch-depth: 0" in wf
    pin = re.search(r'PUMLLINT: "([\d.]+)"', wf).group(1)
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert f'"pumllint=={pin}"' in harness, "the template's pumllint pin is not the harness's"
    spectral = re.search(r'SPECTRAL: "([\d.]+)"', wf).group(1)
    assert f'npm install -g "@stoplight/spectral-cli@{spectral}"' in harness, "the template's Spectral pin is not the harness's"
    assert 'npm install -g "@stoplight/spectral-cli@${SPECTRAL}"' in wf, "the template does not install the Spectral it runs"
    # task-0082: each Node linter's pin is the harness's, and the template installs what it runs
    for var, pkg in (("MARKDOWNLINT", "markdownlint-cli2"), ("GPLINT", "gplint"), ("BPMNLINT", "bpmnlint"), ("DMNLINT", "dmnlint")):
        pin = re.search(rf'{var}: "([\d.]+)"', wf).group(1)
        assert f'"{pkg}@{pin}"' in harness, f"the template's {pkg} pin is not the harness's"
        assert f'"{pkg}@${{{var}}}"' in wf, f"the template does not install the {pkg} it runs"
    assert "tools/check_preload_linters.py" in harness, "harness.yml does not prove the Node linters"
    assert wf.count('node-version: "24"') == 1 and harness.count('node-version: "24"') == 1, "bpmnlint 12 and dmnlint 2 need Node 24"
    for name in ("markdownlint.jsonc", "gplintrc", "bpmnlintrc", "dmnlintrc"):
        assert (ci / name).is_file(), name
    assert "instance/ci/preload-check.sh" in harness, "harness.yml does not prove the template's script"
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "guide.md").read_text(encoding="utf-8")
    for doc in (readme, guide):
        assert "tools/preload_check.py" in doc and "harness/gate_cli.py" in doc


def test_the_json_report_round_trips_through_the_command():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        report = Path(td) / "pre.json"
        with _Standin(Path(td)):
            assert preload_check.main([str(out), "-f", "json", "-o", str(report)]) == 0
        rep = json.loads(report.read_text(encoding="utf-8"))
        _valid(rep)
        assert rep["tool"] == "knowgov preload check" and rep["schema_version"] == 1



def test_an_unwritable_output_or_any_failure_to_run_exits_2_through_the_outcomes():
    """task-0228 (doc-0030 F6): -o's write failing is cannot-run, exit 2 with one line and no report; the
    command's entry goes through _outcomes.run, so KG_OUTCOMES records it, and anything else that escapes
    main is exit 2 too, never 1 (the finding's code)."""
    import os
    import subprocess
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        bad = Path(td) / "no-such-dir" / "r.json"
        with _Standin(Path(td)):
            assert preload_check.main([str(out), "-f", "json", "-o", str(bad), "--changed", "artefacts/textual-requirements/requirements.md"]) == 2
        log = Path(td) / "outcomes.jsonl"
        env = {**os.environ, "KG_OUTCOMES": str(log)}
        env.pop("KG_TRACEBACK", None)
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "preload_check.py"), str(out), "-o", str(bad),
                            "--changed", "artefacts/textual-requirements/requirements.md"], capture_output=True, text=True, env=env, timeout=120)
        assert p.returncode == 2 and "cannot run: -o" in p.stderr and "Traceback" not in p.stderr and not p.stdout, (p.returncode, p.stderr)
        row = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert row["tool"] == "preload_check.py" and row["exit"] == 2 and row["outcome"] == "cannot run", row
        src = (ROOT / "tools" / "preload_check.py").read_text(encoding="utf-8")
        assert 'sys.exit(_outcomes.run(lambda: cli_exit.run(main, "preload check")))' in src


def test_a_baseline_holds_what_it_recorded_and_fails_only_on_a_regression():
    """task-0065: an earlier report (-o) as --baseline. Held findings are listed and pass; a new finding,
    or one at a worse severity, fails; the command never writes the baseline; a file that is not a
    report cannot be compared."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        legacy = out / "artefacts" / "plantuml-models" / "legacy.puml"
        legacy.write_text("@startuml\nA -> B : BROKEN B\n@enduml\n", encoding="utf-8")
        base = Path(td) / "baseline.json"
        with _Standin(Path(td)):
            assert preload_check.main([str(out), "-o", str(base)]) == 1, "today's finding fails without a baseline"
            recorded = base.read_bytes()
            assert preload_check.main([str(out), "--baseline", str(base)]) == 0
            rep = preload_check.check(out, None, "major", None, json.loads(recorded), "baseline.json")
            _valid(rep)
            row = next(r for r in rep["files"] if r["file"] == "artefacts/plantuml-models/legacy.puml")
            assert row["state"] == "held" and all(f["held"] for f in row["findings"]), row
            assert rep["baseline"] == {"file": "baseline.json", "held": 1, "new": 0} and rep["counts"]["held"] == 1
            assert "(held by the baseline)" in preload_check.render(rep)
            # the line moves: still held
            legacy.write_text("@startuml\n' a comment\nA -> B : BROKEN B\n@enduml\n", encoding="utf-8")
            assert preload_check.main([str(out), "--baseline", str(base)]) == 0
            # a second finding: new, fails; the held one stays held
            legacy.write_text("@startuml\nA -> B : BROKEN B\nA -> C : BROKEN C\n@enduml\n", encoding="utf-8")
            assert preload_check.main([str(out), "--baseline", str(base)]) == 1
            rep = preload_check.check(out, None, "major", None, json.loads(recorded), "baseline.json")
            row = next(r for r in rep["files"] if r["file"] == "artefacts/plantuml-models/legacy.puml")
            assert row["state"] == "findings" and rep["baseline"]["new"] == 1 and rep["baseline"]["held"] == 1
            assert [f["held"] for f in row["findings"] if f["rule"] == "SEQ001"] == [True, False]
            # the same finding at a worse severity is a regression
            legacy.write_text("@startuml\nA -> B : BROKEN WORSE B\n@enduml\n", encoding="utf-8")
            rep = preload_check.check(out, None, "major", None, {"files": [{"file": "artefacts/plantuml-models/legacy.puml",
                                      "findings": [{"rule": "SEQ001", "severity": "critical", "message": "undeclared WORSE B"}]}]})
            assert rep["exit_code"] == 1, rep["files"]
            # a new document with a finding is new; the baseline file itself never changes
            legacy.write_text("@startuml\nA -> B : BROKEN B\n@enduml\n", encoding="utf-8")
            (out / "artefacts" / "plantuml-models" / "fresh.puml").write_text("@startuml\nA -> B : BROKEN B\n@enduml\n", encoding="utf-8")
            assert preload_check.main([str(out), "--baseline", str(base)]) == 1
            assert preload_check.main([str(out), "--baseline", str(base), "-o", str(base)]) == 2, "-o naming the baseline is refused"
            assert base.read_bytes() == recorded
            bad = Path(td) / "bad.json"
            bad.write_text("{}", encoding="utf-8")
            assert preload_check.main([str(out), "--baseline", str(bad)]) == 2
            assert preload_check.main([str(out), "--baseline", str(Path(td) / "missing.json")]) == 2


def test_api_contracts_run_spectral_under_the_same_contract():
    """task-0066: Spectral for api-contracts, its error a major finding (fails at the default threshold), its
    warning minor; the shipped ruleset holds Spectral's OpenAPI and AsyncAPI rules."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        bad = out / "artefacts" / "api-contracts" / "broken.yaml"
        bad.write_text("openapi: 3.0.3\n$ref: BROKEN\n", encoding="utf-8")
        with _Standin(Path(td)):
            rep = preload_check.check(out, ["artefacts/api-contracts/broken.yaml"])
            assert preload_check.main([str(out), "--changed", "artefacts/api-contracts/broken.yaml"]) == 1
            assert preload_check.main([str(out), "--changed", "artefacts/api-contracts/broken.yaml", "--fail-on", "critical"]) == 0
            assert preload_check.main([str(out), "--changed", "artefacts/api-contracts/openapi.yaml"]) == 0
            assert preload_check.main([str(out), "--changed", "artefacts/api-contracts/openapi.yaml", "--fail-on", "minor"]) == 1
        _valid(rep)
        [row] = rep["files"]
        assert row["state"] == "findings" and row["tool"] == "Spectral"
        assert row["findings"][0] == {"rule": "invalid-ref", "severity": "major", "line": 2, "message": "does not exist"}, row["findings"]
    ruleset = (ROOT / "instance" / "ci" / "spectral.yaml").read_text(encoding="utf-8")
    assert ruleset.strip().endswith('extends: ["spectral:oas", "spectral:asyncapi"]')


def test_the_node_linters_run_under_the_same_contract():
    """task-0082: markdownlint, gplint, bpmnlint and dmnlint, stood in by scripts that speak their command lines
    and reports: an error is major (fails at the default threshold), a warning minor; a decision table that is
    not .dmn stays unchecked; gplint's messages name files relative to the instance, so a baseline holds anywhere;
    a linter that is not installed leaves its kind unchecked, naming it."""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "inst"
        example_instance.build(out)
        a = out / "artefacts"
        plant = {"specification-prose/broken.md": "# One\n\nBROKEN\n", "specification-prose/warn.md": "# One\n\nWARN\n",
                 "acceptance-scenarios/broken.feature": "Feature: x\n  Scenario: BROKEN\n",
                 "bpmn-process-models/broken.bpmn": "<x>BROKEN</x>\n", "bpmn-process-models/mangled.bpmn": "<x>MANGLED\n",
                 "decision-tables/broken.dmn": "<x>BROKEN</x>\n", "decision-tables/table.csv": "a,b\n"}
        for rel, text in plant.items():
            (a / rel).write_text(text, encoding="utf-8")
        changed = [f"artefacts/{rel}" for rel in plant]
        with _Standin(Path(td), node=True):
            clean = preload_check.check(out)
            rep = preload_check.check(out, changed)
            assert preload_check.main([str(out), "--changed", *changed]) == 1
            assert preload_check.main([str(out), "--changed", "artefacts/specification-prose/warn.md"]) == 0
            assert preload_check.main([str(out), "--changed", "artefacts/specification-prose/warn.md", "--fail-on", "minor"]) == 1
            assert preload_check.main([str(out), "--changed", *changed, "--fail-on", "critical"]) == 0
            base = Path(td) / "base.json"
            assert preload_check.main([str(out), "--changed", *changed, "-o", str(base)]) == 1
            assert preload_check.main([str(out), "--changed", *changed, "--baseline", str(base)]) == 0
        _valid(clean)
        _valid(rep)
        # nothing planted yet in the first run: the example's own files of the four kinds are clean under the stand-ins
        cs = {r["file"]: (r["state"], r["tool"]) for r in clean["files"] if r["file"] not in changed}
        assert cs["artefacts/specification-prose/spec.md"] == ("clean", "markdownlint")
        assert cs["artefacts/acceptance-scenarios/acceptance.feature"] == ("clean", "gplint")
        assert cs["artefacts/bpmn-process-models/quote_process.bpmn"] == ("clean", "bpmnlint")
        assert cs["artefacts/decision-tables/screening_decision.dmn"] == ("clean", "dmnlint")
        assert cs["artefacts/decision-tables/decision_table.md"] == ("unchecked", "dmnlint (small rule set)")
        rows = {r["file"].removeprefix("artefacts/"): r for r in rep["files"]}
        md = rows["specification-prose/broken.md"]
        assert md["state"] == "findings" and md["tool"] == "markdownlint"
        assert md["findings"] == [{"rule": "MD025", "severity": "major", "line": 3,
                                   "message": "MD025/single-title/single-h1 Multiple top-level headings in the same document"}], md
        assert rows["specification-prose/warn.md"]["state"] == "clean" and rows["specification-prose/warn.md"]["findings"][0]["severity"] == "minor"
        g = rows["acceptance-scenarios/broken.feature"]
        assert g["state"] == "findings" and g["findings"] == [{"rule": "no-dupe-scenario-names", "severity": "major", "line": 2,
                                                               "message": "Scenario name is already used in: artefacts/acceptance-scenarios/broken.feature:1"}], g
        b = rows["bpmn-process-models/broken.bpmn"]
        assert b["tool"] == "bpmnlint" and [(f["rule"], f["severity"], f["message"]) for f in b["findings"]] == [
            ("label-required", "major", "e1: Element is missing label/name"), ("superfluous-label", "minor", "e2: Sequence flow has superfluous label")], b
        m = rows["bpmn-process-models/mangled.bpmn"]
        assert m["state"] == "findings" and m["findings"][0]["rule"] == "parse-error" and m["findings"][0]["message"] == "Parse error: unparsable content </x", m
        assert rows["decision-tables/broken.dmn"]["tool"] == "dmnlint" and rows["decision-tables/broken.dmn"]["state"] == "findings"
        csv = rows["decision-tables/table.csv"]
        assert csv["state"] == "unchecked" and "dmnlint reads .dmn files only" in csv["why"], csv
        lts = {lt["tool"]: lt["version"] for lt in rep["linters"]}
        assert lts == {"markdownlint": "0.0-standin", "gplint": "0.0-standin", "bpmnlint": "0.0.0", "dmnlint": "0.0.0"}, lts
        with _Standin(Path(td)):   # the Node linters not installed: each kind unchecked, naming its tool
            rep = preload_check.check(out, changed)
        assert rep["exit_code"] == 0 and {r["state"] for r in rep["files"]} == {"unchecked"}
        for r in rep["files"]:
            if not r["file"].endswith(".csv"):
                assert f"{r['tool']} is not installed here" in r["why"], r
    for name, (cfg, key) in {"bpmnlintrc": ("bpmnlint:recommended", "extends"), "dmnlintrc": ("dmnlint:recommended", "extends")}.items():
        assert json.loads((ROOT / "instance" / "ci" / name).read_text(encoding="utf-8"))[key] == cfg
