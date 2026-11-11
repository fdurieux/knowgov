"""task-0332 (task-0330 H1', H4, H5, H6): the hook's closing route follows the cause on real gate reports of the example
instance; the execution step does not presume the values changed; the count of keys says how many the absence lowers."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(ROOT / "tests"), str(ROOT / "instance" / "ci" / "claude")]
import example_instance  # noqa: E402
import gate_cli  # noqa: E402
import knowgov_hook as hook  # noqa: E402
import test_execution_binding as eb  # noqa: E402
from _skip import need_rdflib  # noqa: E402


def _report(inst: Path, scenario: str) -> dict:
    p = subprocess.run([sys.executable, "gate_cli.py", "--scenario", scenario, "--as-of", "record", "-f", "json"], cwd=eb.HARNESS,
                       env=eb._env(inst), capture_output=True, text=True)
    assert p.returncode in (0, 1), p.stderr[-1500:]
    return json.loads(p.stdout)


def _strip(inst: Path, name: str) -> None:
    """Remove ``versions`` from ``[verification] <name>`` wherever it sits in the inline table."""
    mf = inst / "subjects" / "cargo_quote" / "subject.toml"
    out = []
    for line in mf.read_text(encoding="utf-8").splitlines(keepends=True):
        if line.startswith(f"{name} = {{"):
            line = re.sub(r"versions = \[[^\]]*\],? ?", "", line)
            line = re.sub(r", \}", " }", line)
            line = re.sub(r",\s*\}", " }", line)
        out.append(line)
    mf.write_text("".join(out), encoding="utf-8")


def test_the_closing_route_is_the_attestations_when_the_bar_is_the_only_blocker():
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        stripped = example_instance.build(Path(t) / "a")
        _strip(stripped, "execution")
        edited = example_instance.build(Path(t) / "b")
        eb._edit(edited)
        for inst in (stripped, edited):
            rep = _report(inst, "S1")
            assert rep["verdict"] == "BLOCKED" and any(f["kind"] == "attestation" for f in rep["findings"]), rep["verdict"]
            assert not [f for f in rep["findings"] if f["kind"] == "key" and f["severity"] in ("blocker", "critical")]
            assert hook._route_for(rep) == hook.ATTESTATION_ROUTE, [f["kind"] for f in hook._shown(rep)]


def test_a_key_blocker_keeps_the_questionnaire_route():
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        rep = _report(example_instance.build(Path(t) / "inst"), "S2")
    assert any(f["kind"] == "key" and f["severity"] in ("blocker", "critical") for f in rep["findings"]), rep["verdict"]
    assert hook._route_for(rep) == hook.ROUTE


def test_the_execution_step_does_not_presume_the_values_changed():
    for text in (gate_cli.STEP["execution"], hook.ATTESTATION_ROUTE):
        assert "brought in line" in text and "changed to" not in text, text


def test_the_count_says_how_many_keys_the_absence_lowers():
    need_rdflib()
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        _strip(inst, "review")
        rep = _report(inst, "S1")
    [f] = [f for f in rep["findings"] if f["kind"] == "attestation" and "review lists no Version" in f["message"]]
    below = {k for k in f["related"] if rep["levels"][k] in eb.BELOW}
    assert f"behind {len(f['related'])} required key(s), of which {len(below)} now read below verified" in f["message"], f["message"]
    assert below and len(below) <= len(f["related"])


def test_a_single_bar_finding_leaves_the_spare_slot_to_the_blockers():
    key = lambda i: {"severity": "blocker", "kind": "key", "key": f"k{i}", "message": "m"}  # noqa: E731
    att = {"severity": "major", "kind": "attestation", "key": None, "message": "a"}
    one = hook._shown({"findings": [key(i) for i in range(8)] + [att]})
    assert len(one) == 6 and one[-1] is not None and sum(f["kind"] == "key" for f in one) == 5 and one[-1]["kind"] == "attestation"
    assert len(hook._shown({"findings": [key(i) for i in range(8)]})) == 6
