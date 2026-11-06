"""Task-0115: the layout check's problems ride in the pre-load report (``--layout``), so harness/annotate.py
shows them as GitHub annotations and GitLab code-quality entries; the report's schema change is additive
and its exit code stays the lint's. Stdlib: an example instance with an unread story and a layout error."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import annotate  # noqa: E402
import example_instance  # noqa: E402
import preload_check  # noqa: E402
import schema_check  # noqa: E402

SCHEMA = schema_check.load("preload-report")
ORPHAN = "artefacts/user-stories/orphan.md"


def _instance(d: Path) -> Path:
    inst = example_instance.build(d / "inst")
    (inst / ORPHAN).parent.mkdir(parents=True, exist_ok=True)
    (inst / ORPHAN).write_text("# Orphan\n\nNo subject names this story.\n", encoding="utf-8")
    return inst


def _run(inst: Path, out: Path, *extra: str) -> tuple[int, dict]:
    code = preload_check.main([str(inst), "--changed", ORPHAN, "-o", str(out), *extra])
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)
    return code, rep


def test_an_unread_story_is_a_layout_problem_in_the_report_and_the_exit_stays_the_lints():
    with tempfile.TemporaryDirectory() as d:
        inst = _instance(Path(d))
        plain_code, plain = _run(inst, Path(d) / "plain.json")
        code, rep = _run(inst, Path(d) / "layout.json", "--layout")
        assert "layout" not in plain and code == plain_code == rep["exit_code"] == plain["exit_code"]
        lay = rep["layout"]
        assert lay["holds"] is True and lay["exit_code"] == 0
        mine = {p["kind"]: p for p in lay["problems"] if p["path"] == ORPHAN}
        assert set(mine) == {"absent", "unread"} and mine["absent"]["severity"] == "minor" and mine["unread"]["severity"] == "info"
        assert not any(p["fails"] for p in lay["problems"])
        assert {k: v for k, v in rep.items() if k != "layout"} == plain   # additive: the rest of the report is unchanged


def test_its_problems_annotate_on_github_and_gitlab_and_only_a_layout_error_is_an_error():
    with tempfile.TemporaryDirectory() as d:
        inst = _instance(Path(d))
        (inst / "artefacts" / "not-a-kind").mkdir()
        (inst / "artefacts" / "not-a-kind" / "x.md").write_text("x\n", encoding="utf-8")
        manifest = inst / "subjects" / "cargo_quote" / "subject.toml"
        text = manifest.read_text(encoding="utf-8")
        first = next(line for line in text.splitlines() if line.startswith('path = "../../artefacts/'))
        manifest.write_text(text.replace(first, 'path = "../../artefacts/specification-prose/gone.md"', 1), encoding="utf-8")
        code, rep = _run(inst, Path(d) / "r.json", "--layout", "--fail-on", "info")
        lay = rep["layout"]
        assert lay["holds"] is False and lay["exit_code"] == 1 and code == rep["exit_code"]
        errors = [p for p in lay["problems"] if p["fails"]]
        assert errors and all(p["severity"] == "blocker" and p["kind"] == "error" for p in errors)
        assert any(p["path"] is None and "not-a-kind" in p["message"] for p in errors)
        assert any(p["path"] == "subjects/cargo_quote/subject.toml" and "gone.md" in p["message"] for p in errors)
        gh = annotate.convert(rep, "github", instance=inst, root=Path(d))
        lines = [x for x in gh.splitlines() if "knowgov layout" in x]
        assert any(x.startswith("::error file=inst/subjects/cargo_quote/subject.toml,line=1,title=knowgov layout error (blocker)::")
                   for x in lines), lines
        assert any(x.startswith("::error title=knowgov layout error (blocker)::") and "not-a-kind" in x for x in lines), lines
        assert any(x.startswith("::warning file=inst/artefacts/user-stories/orphan.md,line=1,title=knowgov layout absent (minor)::")
                   for x in lines), lines   # at --fail-on info a non-failing problem is still not an error
        assert any(x.startswith("::notice file=inst/artefacts/user-stories/orphan.md,line=1,title=knowgov layout unread (info)::")
                   for x in lines), lines
        cq = json.loads(annotate.convert(rep, "gitlab", instance=inst, root=Path(d)))
        got = {(i["check_name"], i["severity"], i["location"]["path"]) for i in cq if i["check_name"].startswith("knowgov-layout:")}
        assert ("knowgov-layout:unread", "info", f"inst/{ORPHAN}") in got and ("knowgov-layout:absent", "minor", f"inst/{ORPHAN}") in got
        assert ("knowgov-layout:error", "blocker", "inst/subjects/cargo_quote/subject.toml") in got
        assert ("knowgov-layout:error", "blocker", ".") in got   # a layout error naming no file still has a location
        sarif = json.loads(annotate.convert(rep, "sarif", instance=inst, root=Path(d)))
        assert {r["level"] for r in sarif["runs"][0]["results"] if r["ruleId"] == "layout:error"} == {"error"}


def test_the_shell_passes_layout_only_with_a_report_and_keeps_the_layouts_exit():
    sh = (ROOT / "instance" / "ci" / "preload-check.sh").read_text(encoding="utf-8")
    assert 'set -- "$@" -o "$KG_REPORT" --layout' in sh
    assert '"$PY" "$KG/tools/check_instance.py" "$INST"' in sh and "layout=$?" in sh
    assert shutil.which("sh") is not None
