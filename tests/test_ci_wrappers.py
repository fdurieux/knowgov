"""Task-0052: the pipeline wrappers. The GitHub composite action and the GitLab include both call
instance/ci/knowgov-gate.sh with the same KG_* variables, every one of which the script reads, and
neither reads a platform variable the other's mapping lacks; the script refuses what it cannot run
with exit 2. The wrappers run on the example instance in harness.yml (the action for real, the
GitLab job's script lines by a shell: tools/check_ci_wrappers.py)."""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CI = ROOT / "instance" / "ci"
SCRIPT = CI / "knowgov-gate.sh"
ACTION = CI / "github" / "action.yml"
GITLAB = CI / "gitlab" / "knowgov.gitlab-ci.yml"


def _read_vars() -> set[str]:
    return set(re.findall(r"\$\{?(KG_[A-Z_]+)", SCRIPT.read_text(encoding="utf-8")))


def _documented() -> set[str]:
    return set(re.findall(r"^#   (KG_[A-Z_]+)", SCRIPT.read_text(encoding="utf-8"), re.M))


def test_every_variable_the_script_reads_is_documented_and_no_platform_variable_reaches_it():
    text = SCRIPT.read_text(encoding="utf-8")
    assert _read_vars() <= _documented() | {"KG_SUBJECT"}, _read_vars() - _documented()
    assert not re.search(r"\b(GITHUB_|CI_|GITLAB_|BUILD_|JENKINS_)", text.split("set -u", 1)[1]), "the core call reads no platform variable"


def test_both_wrappers_call_the_same_script_with_the_platforms_commit_and_base():
    action, gitlab = ACTION.read_text(encoding="utf-8"), GITLAB.read_text(encoding="utf-8")
    assert re.search(r'sh "\$GITHUB_ACTION_PATH/\.\./knowgov-gate\.sh" "\$GITHUB_ACTION_PATH/\.\./\.\./\.\." "\$KG_INSTANCE" "\$KG_GATE"', action)
    assert re.search(r'sh /tmp/knowgov/instance/ci/knowgov-gate\.sh /tmp/knowgov "\$KG_INSTANCE" "\$KG_GATE"', gitlab)
    assert "KG_COMMIT: ${{ github.sha }}" in action and "github.base_ref" in action
    assert 'KG_COMMIT="$CI_COMMIT_SHA"' in gitlab and "CI_MERGE_REQUEST_DIFF_BASE_SHA" in gitlab
    set_in_action = set(re.findall(r"^\s+(KG_[A-Z_]+):", action, re.M)) - {"KG_SUBJECT_IN"}
    assert set_in_action <= _read_vars() | {"KG_GATE", "KG_INSTANCE"}, set_in_action - _read_vars()
    assert "${{ inputs." not in action.split("run: |", 1)[1], "inputs reach the shell through env, never inline"


def test_both_wrappers_annotate_by_default_and_gitlab_keeps_the_code_quality_report():
    action, gitlab = ACTION.read_text(encoding="utf-8"), GITLAB.read_text(encoding="utf-8")
    assert 'export KG_ANNOTATE="github,summary:$GITHUB_STEP_SUMMARY"' in action and re.search(r'annotate:\n.*\n\s+default: "true"', action)
    assert re.search(r'^    KG_ANNOTATE: "gitlab:gl-code-quality-report\.json"', gitlab, re.M)
    assert re.search(r"^  artifacts:\n    when: always\b.*\n    reports:\n      codequality: gl-code-quality-report\.json$", gitlab, re.M)


def test_annotations_never_change_the_exit_code_and_a_run_that_cannot_run_annotates_nothing():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "inst"
        (inst / "subjects").mkdir(parents=True)
        env = {"PATH": "/usr/bin:/bin", "KG_SUBJECT": str(inst), "KG_ANNOTATE": f"gitlab:{td}/cq.json", "KG_REPORT": f"{td}/r.json"}
        Path(td, "r.json").write_text('{"tool": "knowgov gate"}', encoding="utf-8")   # an earlier run's: never annotated
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "trace-check"], capture_output=True, text=True, env=env)
        assert p.returncode == 2 and "no report to annotate" in p.stderr and not Path(td, "cq.json").exists(), p.stderr


def test_the_script_exits_2_on_an_unknown_gate_and_an_instance_without_one_subject():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "inst"
        (inst / "subjects").mkdir(parents=True)
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "deploy"], capture_output=True, text=True)
        assert p.returncode == 2 and "no gate deploy" in p.stderr, p.stderr
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "gate"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
        assert p.returncode == 2 and "set KG_SUBJECT" in p.stderr, p.stderr
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "trace-register"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "KG_SUBJECT": str(inst)})
        assert p.returncode == 2 and "needs KG_COMMIT" in p.stderr, p.stderr
