"""task-0342 (decision-0041 B-N2, brought into 0.10.0 on 2026-11-16): a gate-only previous-register setting.

``KG_GATE_REGISTER_PREVIOUS`` makes ``instance/ci/knowgov-gate.sh`` pass ``--register-previous`` to the ``gate`` step
alone, a relative path made absolute from the working directory. ``KG_REGISTER_PREVIOUS`` keeps its single, page-only
effect: the CI template never reads it, so an instance that sets it for the page does not re-stale keys on every CI run
(B-N2's hazard). The script is run for real against a stub knowgov checkout whose core commands print their argv."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "instance" / "ci" / "knowgov-gate.sh"
STUB = "import json, sys\nprint(json.dumps(sys.argv[1:]))\n"


def _run(gate: str, **env) -> list[str]:
    """knowgov-gate.sh on a stub checkout: the argv its core command was given."""
    with tempfile.TemporaryDirectory() as d:
        kg, inst = Path(d) / "kg", Path(d) / "inst"
        (kg / "harness").mkdir(parents=True)
        (inst / "subjects" / "one").mkdir(parents=True)
        (inst / "subjects" / "one" / "subject.toml").write_text("", encoding="utf-8")
        for name in ("gate_cli.py", "trace.py"):
            (kg / "harness" / name).write_text(STUB, encoding="utf-8")
        base = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
        p = subprocess.run(["sh", str(SCRIPT), str(kg), str(inst), gate], capture_output=True, text=True, cwd=d,
                           env={**base, "PYTHON": sys.executable, "PYTHONDONTWRITEBYTECODE": "1", **env}, timeout=60)
        assert p.returncode == 0, p.stderr
        return [a.replace(d, "<tmp>") for a in json.loads(p.stdout.strip().splitlines()[-1])]


def test_the_gate_step_passes_the_gate_only_setting_made_absolute():
    argv = _run("gate", KG_GATE_REGISTER_PREVIOUS="prev/register")
    i = argv.index("--register-previous")
    assert argv[i + 1] == "<tmp>/prev/register", argv
    assert _run("gate", KG_GATE_REGISTER_PREVIOUS="/abs/previous")[-2:] == ["--register-previous", "/abs/previous"]


def test_the_pages_setting_never_reaches_the_gate_and_unset_passes_nothing():
    assert "--register-previous" not in _run("gate")
    assert "--register-previous" not in _run("gate", KG_REGISTER_PREVIOUS="/the/pages/previous")   # B-N2's hazard


def test_only_the_gate_step_reads_it():
    argv = _run("trace-check", KG_GATE_REGISTER_PREVIOUS="prev/register", KG_LEDGER="ledger.json")
    assert argv[0] == "check" and "--register-previous" not in argv, argv


def test_the_wrappers_carry_it_and_nothing_reads_the_pages_setting():
    sh = SCRIPT.read_text(encoding="utf-8")
    code = [ln for ln in sh.splitlines() if not ln.lstrip().startswith("#")]
    assert not any("KG_REGISTER_PREVIOUS" in ln and "KG_GATE_REGISTER_PREVIOUS" not in ln for ln in code), "the page's setting is never read here"
    action = (ROOT / "instance" / "ci" / "github" / "action.yml").read_text(encoding="utf-8")
    assert "  register-previous:\n" in action and "KG_GATE_REGISTER_PREVIOUS: ${{ inputs.register-previous }}" in action
    assert "KG_GATE_REGISTER_PREVIOUS:" in (ROOT / "instance" / "ci" / "gitlab" / "knowgov.gitlab-ci.yml").read_text(encoding="utf-8")
    hook = (ROOT / "instance" / "ci" / "claude" / "knowgov_hook.py").read_text(encoding="utf-8")
    assert "REGISTER_PREVIOUS" not in hook, "the hook is no CI gate step"


def test_through_the_ci_script_the_gate_stales_what_the_update_withdrew_only_with_the_gate_setting():
    """End to end on rdflib: the register fixture's update (tools/register_fixture.py, CAP-0001 deprecated, REL-06001
    withdrawn) read by the CI script's gate on CargoQuote S1. KG_GATE_REGISTER_PREVIOUS stales the keys resting on it;
    the page's KG_REGISTER_PREVIOUS, set alone, stales nothing."""
    sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "tools"), str(ROOT / "harness")]
    from _skip import need_rdflib
    need_rdflib()
    import register_fixture
    with tempfile.TemporaryDirectory() as d:
        changed = register_fixture.changed(Path(d) / "changed")
        base = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
        env = {**base, "PYTHON": sys.executable, "PYTHONDONTWRITEBYTECODE": "1", "KG_STORE": "rdflib", "KG_CLOCK": "pinned",
               "KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"), "KG_SCENARIO": "S1", "KG_AS_OF": "record",
               "KG_REGISTER": str(changed)}
        stale = {}
        for name, extra in (("gate", {"KG_GATE_REGISTER_PREVIOUS": str(ROOT / "demo" / "register")}),
                            ("page", {"KG_REGISTER_PREVIOUS": str(ROOT / "demo" / "register")})):
            report = Path(d) / f"{name}.json"
            p = subprocess.run(["sh", str(SCRIPT), str(ROOT), str(ROOT), "gate"], capture_output=True, text=True, cwd=d,
                               env={**env, **extra, "KG_REPORT": str(report)}, timeout=900)
            assert p.returncode in (0, 1), (name, p.stderr[-800:])
            stale[name] = json.loads(report.read_text(encoding="utf-8"))["stale"]
        assert stale["gate"] and stale["page"] == [], stale
