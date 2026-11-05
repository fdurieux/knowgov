"""Task-0052: the pipeline wrappers. The GitHub composite action and the GitLab include both call
instance/ci/knowgov-gate.sh with the same KG_* variables, every one of which the script reads, and
neither reads a platform variable the other's mapping lacks; the script refuses what it cannot run
with exit 2. The wrappers run on the example instance in harness.yml (the action for real, the
GitLab job's script lines by a shell: tools/check_ci_wrappers.py)."""
from __future__ import annotations

import os
import re
import subprocess
import sys
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
        env = {"PATH": "/usr/bin:/bin", "PYTHON": sys.executable, "KG_SUBJECT": str(inst), "KG_ANNOTATE": f"gitlab:{td}/cq.json", "KG_REPORT": f"{td}/r.json"}
        Path(td, "r.json").write_text('{"tool": "knowgov gate"}', encoding="utf-8")   # an earlier run's: never annotated
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "trace-check"], capture_output=True, text=True, env=env)
        assert p.returncode == 2 and "no report to annotate" in p.stderr and not Path(td, "cq.json").exists(), p.stderr


def test_the_script_exits_2_on_an_unknown_gate_and_an_instance_without_one_subject():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "inst"
        (inst / "subjects").mkdir(parents=True)
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "deploy"], capture_output=True, text=True,
                           env={**os.environ, "PYTHON": sys.executable})
        assert p.returncode == 2 and "no gate deploy" in p.stderr, p.stderr
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "gate"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHON": sys.executable})
        assert p.returncode == 2 and "set KG_SUBJECT" in p.stderr, p.stderr
        p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), "trace-register"], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "PYTHON": sys.executable, "KG_SUBJECT": str(inst)})
        assert p.returncode == 2 and "needs KG_COMMIT" in p.stderr, p.stderr
        # doc-0014 C4: the CI route requires a task class, never the MCP server's agent-chosen key set (task-0102)
        for gate in ("gate", "trace-check", "preload"):
            p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(inst), gate], capture_output=True, text=True,
                               env={"PATH": "/usr/bin:/bin", "PYTHON": sys.executable, "KG_SUBJECT": str(inst), "KG_TASK": "keys"})
            assert p.returncode == 2 and "KG_TASK=keys is an agent-chosen key set" in p.stderr, (gate, p.stderr)


def test_the_pre_load_gate_writes_its_report_through_kg_report():
    pre = (CI / "preload-check.sh").read_text(encoding="utf-8")
    assert 'if [ -n "${KG_REPORT:-}" ]; then set -- "$@" -o "$KG_REPORT"; fi' in pre
    script = SCRIPT.read_text(encoding="utf-8")
    branch = script.split("preload)", 1)[1].split(";;", 1)[0]
    assert 'KG_REPORT=$REPORT sh "$KG/instance/ci/preload-check.sh"' in branch and 'finish "$rc"' in branch and "exec" not in branch


# task-0141.01 (E0): the interpreter is the one PYTHON names, probed once and passed on by absolute path.
SCRIPTS = {"knowgov-gate": ("knowgov-gate.sh", "{inst}", "gate"), "knowgov-gate preload": ("knowgov-gate.sh", "{inst}", "preload"),
           "preload-check": ("preload-check.sh", "{inst}"),
           "proposal-impact": ("proposal-impact.sh", "{inst}", "HEAD")}
_LOG_EXECUTABLE = "import os, sys\nwith open(os.environ['KG_PY_LOG'], 'a') as f:\n    f.write(sys.executable + '\\n')\n"


def _shim_dir(td: Path, old_version: str = "3.9.25") -> Path:
    """A directory holding a python3 that claims an older version and logs that it was called."""
    d = td / "oldbin"
    d.mkdir()
    py = d / "python3"
    py.write_text(f'#!/bin/sh\necho PATH-python3 >> "$KG_PY_LOG"\ncase "$1" in -V) echo "Python {old_version}" ;; esac\nexit 1\n')
    py.chmod(0o755)
    return d


def test_env_01_every_step_runs_the_selected_interpreter_though_an_older_python3_comes_first_on_path():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        oldbin, site, inst = _shim_dir(td), td / "site", td / "inst"
        site.mkdir()
        (site / "sitecustomize.py").write_text(_LOG_EXECUTABLE)   # every Python process started logs who it is
        (inst / "subjects").mkdir(parents=True)
        log = td / "py.log"
        (td / "sel").mkdir()
        (td / "sel" / "python3").symlink_to(sys.executable)   # named relative to the caller's directory, as a venv often is
        for python, identity in ((sys.executable, sys.executable), ("sel/python3", str(td / "sel" / "python3"))):
            env = {"PATH": f"{oldbin}:/usr/bin:/bin", "PYTHON": python, "PYTHONPATH": str(site), "KG_PY_LOG": str(log),
                   "KG_CLOCK": "pinned", "KG_SUBJECT": str(inst)}
            for name, (script, *args) in SCRIPTS.items():
                log.write_text("")
                p = subprocess.run(["sh", str(CI / script), str(ROOT), *[a.format(inst=inst) for a in args]],
                                   capture_output=True, text=True, env=env, cwd=td)
                ran = log.read_text().split()
                assert "PATH-python3" not in ran, (name, python, ran)
                assert ran and set(ran) == {identity}, (name, python, ran, p.stderr)
                assert "older than Python 3.12" not in p.stderr and p.returncode != 127, (name, python, p.returncode, p.stderr)


def test_env_02_a_missing_or_older_interpreter_exits_2_with_a_diagnostic_and_annotates_no_stale_report():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        oldbin, inst = _shim_dir(td), td / "inst"
        (inst / "subjects").mkdir(parents=True)
        log = td / "py.log"
        for python, says in ((str(td / "missing" / "python3"), "not found"), ("python3", "Python 3.9.25"),
                             (str(oldbin / "python3"), "Python 3.9.25")):
            for name, (script, *args) in SCRIPTS.items():
                (td / "r.json").write_text('{"tool": "knowgov gate"}')   # an earlier run's report: never annotated
                env = {"PATH": f"{oldbin}:/usr/bin:/bin", "PYTHON": python, "KG_PY_LOG": str(log), "KG_SUBJECT": str(inst),
                       "KG_ANNOTATE": f"gitlab:{td}/cq.json", "KG_REPORT": f"{td}/r.json"}
                p = subprocess.run(["sh", str(CI / script), str(ROOT), *[a.format(inst=inst) for a in args]],
                                   capture_output=True, text=True, env=env, cwd=td)
                assert p.returncode == 2, (name, python, p.returncode, p.stderr)
                assert f"{name.split()[0]}: the interpreter '{python}' is missing or older than Python 3.12" in p.stderr and says in p.stderr, p.stderr
                assert "set PYTHON to a Python 3.12 or later" in p.stderr and not (td / "cq.json").exists(), (name, p.stderr)
                assert (td / "r.json").read_text() == '{"tool": "knowgov gate"}', "the earlier report is left as it was"


def test_env_01_the_claude_hook_hands_the_gate_its_own_interpreter_unless_python_is_set():
    src = (CI / "claude" / "knowgov_hook.py").read_text(encoding="utf-8")
    assert 'env.setdefault("PYTHON", sys.executable)' in src
    gate = src.split("def run_gate", 1)[1].split("\ndef ", 1)[0]
    assert gate.index('env.setdefault("PYTHON", sys.executable)') < gate.index("subprocess.run(cmd")
