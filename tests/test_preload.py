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


class _Standin:
    def __init__(self, td: Path, present: bool = True):
        self.script = td / "fake_pumllint.py"
        self.script.write_text(FAKE, encoding="utf-8")
        self.present = present

    def __enter__(self):
        self.saved = preload_check.pumllint_cmd
        preload_check.pumllint_cmd = (lambda: [sys.executable, str(self.script)]) if self.present else (lambda: None)

    def __exit__(self, *exc):
        preload_check.pumllint_cmd = self.saved


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
        assert states["artefacts/api-contracts/openapi.yaml"] == ("unchecked", "Spectral, vacuum, Redocly")
        assert rep["counts"] == {"clean": 2, "findings": 0, "held": 0, "unchecked": 8, "cannot_run": 0, "skipped": 0}, rep["counts"]
        [lt] = rep["linters"]
        assert (lt["tool"], lt["version"], lt["files"], lt["exit"]) == ("pumllint", "0.0-standin", 2, 0)
        assert all(r["state"] in ("clean", "unchecked") for r in rep["files"])
        text = preload_check.render(rep)
        assert "UNCHECKED  artefacts/bpmn-process-models/quote_process.bpmn [bpmn-process-models]: form unchecked: the table names bpmnlint" in text
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


def test_what_cannot_be_checked_exits_2_never_passes():
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
            rep = preload_check.check(out, ["artefacts/plantuml-models/quote_flow.puml"])
            assert rep["exit_code"] == 2 and "pumllint is not installed" in rep["files"][0]["why"]
            assert rep["linters"][0]["exit"] == 2
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
    for kind, (tool, _) in preload_check.RUNNERS.items():
        assert table[kind]["lint"]["tool"] == tool and table[kind]["lint"]["capable"], kind
    ci = ROOT / "instance" / "ci"
    script = (ci / "preload-check.sh").read_text(encoding="utf-8")
    assert "tools/preload_check.py" in script and "tools/check_instance.py" in script and "--since" in script
    wf = (ci / "preload-check.yml").read_text(encoding="utf-8")
    assert "sh knowgov/instance/ci/preload-check.sh knowgov instance" in wf and "fetch-depth: 0" in wf
    pin = re.search(r'PUMLLINT: "([\d.]+)"', wf).group(1)
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert f'"pumllint=={pin}"' in harness, "the template's pumllint pin is not the harness's"
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
