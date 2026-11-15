"""EXEC-01's verdict on the probe's result (tools/check_worker.py ``exec_01``, task-0349, V-F2): a probe that
failed, answered nothing, answered something else or lacks its witnesses fails every EXEC-01 line, a leaked
canary fails, and only a well-formed clean answer passes. The real worker runs the probe in the stack job."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import check_worker  # noqa: E402
import worker  # noqa: E402

NAME, VALUE, PW, SID = "KG_UNLISTED_ABCD1234", "canary-0123456789abcdef", "store-pw-5e3c", "cargo_quote"


def env(**over):
    e = {"PATH": worker.JOB_PATH, "LANG": "C.UTF-8", "HOME": "/work/job-x", "TMPDIR": "/work/job-x",
         "PYTHONDONTWRITEBYTECODE": "1", "KG_SUBJECT": f"/repo/subjects/{SID}", "KG_CLOCK": "pinned"}
    e.update(over)
    return {k: v for k, v in e.items() if v is not None}


def result(e=None, parent=None, exit=0, stage="ok", stdout=None):
    if stdout is None:
        stdout = json.dumps({"env": env() if e is None else e}) + "\n" + json.dumps(
            {"parent": {"refused": "PermissionError"} if parent is None else parent}) + "\n"
    return {"exit": exit, "stdout": stdout, "stage": stage}


def verdict(r):
    return check_worker.exec_01(r, canaries=(NAME, VALUE), store_pw=PW, subject_id=SID)


def fails(r, why):
    """EXEC-01 fails: some line of it is not ok."""
    v = verdict(r)
    assert v and not all(c for c, _ in v), (why, v)
    return v


def proves_nothing(r, why):
    """A probe that did not run, or answered out of shape or without its witnesses: no absence line is ok."""
    v = fails(r, why)
    assert not any(c for c, label in v if "never reaches" in label or "neither" in label or "allowlist" in label), (why, v)
    return v


def test_a_clean_well_formed_answer_passes_and_names_its_witnesses():
    for parent in ({"refused": "PermissionError"}, {"read": "PATH=/usr/bin\0HOME=/home/worker\0"}):
        v = verdict(result(parent=parent))
        assert all(c for c, _ in v), v
        line = next(label for _, label in v if "witnesses" in label)
        assert worker.JOB_PATH in line and f"/repo/subjects/{SID}" in line, line


def test_the_v_f2_reproduction_fails_every_line():
    """The report's repro: exit 1, no output, stage ok. Before task-0349 all three EXEC-01 lines printed ok."""
    v = verdict({"exit": 1, "stdout": "", "stage": "ok"})
    assert not any(c for c, _ in v), v


def test_a_non_zero_exit_fails_even_with_a_clean_answer():
    proves_nothing(result(exit=1), "non-zero exit")
    proves_nothing(result(exit=-1, stage="timeout"), "timed out")


def test_missing_or_invalid_json_fails():
    good = result()["stdout"].splitlines()
    for stdout in ("", "\n\n", "not json\n", good[0] + "\n", "{\"env\": {\n" + good[1], good[0] + "\n[]\n",
                   json.dumps({"env": []}) + "\n" + good[1], json.dumps({"env": {}}) + "\n" + good[1],
                   json.dumps({"env": {"PATH": 1}}) + "\n" + good[1], good[1] + "\n" + good[0],
                   good[0] + "\n" + json.dumps({"parent": {}}), good[0] + "\n" + json.dumps({"parent": {"refused": ""}}),
                   good[0] + "\n" + good[1] + "\n" + good[1]):
        proves_nothing(result(stdout=stdout), stdout)
    proves_nothing({}, "no result at all")
    proves_nothing(None, "not an object")


def test_missing_environment_keys_fail():
    proves_nothing(result(e=env(PATH=None)), "no PATH")
    proves_nothing(result(e=env(KG_SUBJECT=None)), "no KG_SUBJECT")
    proves_nothing(result(e=env(PATH="/tmp")), "a PATH not the worker's")
    proves_nothing(result(e=env(KG_SUBJECT="/repo/subjects/other")), "another subject")
    proves_nothing(result(e=env(KG_SUBJECT="subjects/" + SID)), "a relative root")


def test_a_leaked_synthetic_canary_fails():
    v = fails(result(e=env(**{NAME: VALUE})), "canary in the job's environment")
    assert not next(c for c, label in v if "never reaches" in label) and VALUE not in json.dumps(v), v
    v = fails(result(e=env(X_STORE=PW)), "store password in the job's environment")
    assert not next(c for c, label in v if "neither" in label), v
    v = verdict(result(parent={"read": f"{NAME}={VALUE}\0"}))
    assert not next(c for c, label in v if "unlisted" in label), v
    v = verdict(result(e=env(FOO="bar")))
    assert not v[-1][0] and all(c for c, _ in v[:-1]), v


def test_the_probe_emits_the_environment_before_the_parent_and_survives_a_refusal():
    """The probe itself, run here: its first line is the job's environment, and a parent environ that cannot be
    opened is a named refusal, never a lost answer."""
    code = check_worker.EXEC01_PROBE.replace("/proc/1/environ", "/nonexistent/environ")
    p = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=30)
    lines = p.stdout.splitlines()
    assert p.returncode == 0 and len(lines) == 2, p
    assert set(json.loads(lines[0])) == {"env"} and json.loads(lines[1]) == {"parent": {"refused": "FileNotFoundError"}}


def test_the_allowlist_and_witness_are_the_workers():
    import ast
    tree = ast.parse((ROOT / "harness" / "worker.py").read_text(encoding="utf-8"))
    run_job = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_job")
    envs = [n.value for n in ast.walk(run_job) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "env" for t in n.targets) and isinstance(n.value, ast.Dict)]
    assert len(envs) == 1 and [k.value for k in envs[0].keys] == list(worker.JOB_ENV)
    assert isinstance(envs[0].values[0], ast.Name) and envs[0].values[0].id == "JOB_PATH"
