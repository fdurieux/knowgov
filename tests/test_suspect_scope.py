"""task-0282 (decision-0033 choice 8): a suspect derived output blocks a task class's gate only when one of its
invalidated (or changed) statements sits on that class's keys; otherwise it is listed at info, naming the output
and its keys, and is no baseline regression either. A statement whose key cannot be read counts as on the task.
The record's gate rows are untouched: the classification is read in gate_cli.evaluate, never stored in the result."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "tools")]
import gate_cli  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

SUS = {"id": "derived:S1:G:run1", "kind": "python module", "sha256": "0" * 64, "used_invalidated": ["A:dt:P2|threshold@v1"]}


def _res():
    return {"verdict": "QUALIFIED", "why": "w", "keys": {"a|x": {"level": "proposed", "flags": []}}, "below_verified": ["a|x"],
            "flagged": [], "blocked_keys": [], "suspect_derived": [SUS]}


class _St:
    def __init__(self, key):
        self.key = key

    def derived_outputs(self):
        return [{"id": SUS["id"], "used": [{"id": "A:dt:P2|threshold@v1", "key": self.key}]}]


def test_off_the_tasks_keys_it_is_listed_at_info_on_them_it_blocks():
    spec = {"keys": ["a|x"]}
    off = gate_cli.suspect_scope(_St("P2|threshold"), _res(), spec)
    on = gate_cli.suspect_scope(_St("a|x"), _res(), spec)
    unknown = gate_cli.suspect_scope(_St(None), _res(), spec)
    assert off == {SUS["id"]: {"keys": ["P2|threshold"], "on_task": False}}
    assert on[SUS["id"]]["on_task"] and unknown[SUS["id"]]["on_task"], "a key it cannot read counts as on the task"
    assert gate_cli.suspect_scope(_St("a|x"), {**_res(), "suspect_derived": []}, spec) is None
    for scope, sev in ((off, "info"), (on, "blocker"), (None, "blocker")):
        (f,) = [x for x in gate_cli.findings(_res(), {"absent"}, suspect_scope=scope) if x["kind"] == "suspect_derived"]
        assert f["severity"] == sev and f["ref"] == SUS["id"], (scope, f)
    (f,) = [x for x in gate_cli.findings(_res(), {"absent"}, suspect_scope=off) if x["kind"] == "suspect_derived"]
    assert "P2|threshold" in f["message"] and "none of this task's keys" in f["message"]
    base = {"verdict": "QUALIFIED", "levels": {"a|x": "proposed"}, "suspect": []}
    assert gate_cli.compare(_res(), base, "record", suspect_scope=off)["regression"] is False
    assert gate_cli.compare(_res(), base, "record", suspect_scope=on)["new_suspect"] == [SUS["id"]]
    assert gate_cli.compare(_res(), base, "record")["new_suspect"] == [SUS["id"]], "without a scope, as before"


def test_the_coordinators_probe_design_passes_codegen_still_blocks():
    """The register change that invalidates codegen's keys: S1's codegen output is suspect. Under design, whose keys
    it does not rest on, the gate exits 0 and lists it at info; under codegen it exits 1 on it, as before."""
    need_rdflib()
    import register_fixture
    with tempfile.TemporaryDirectory() as td:
        reg = register_fixture.changed(Path(td) / "register-changed")
        env = {**os.environ, "KG_STORE": "rdflib", "KG_CLOCK": "pinned", "KG_REGISTER": str(reg),
               "KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"), "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("KG_RDFLIB_FILE", None)
        got = {}
        for task in ("design", "codegen"):
            p = subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "--task", task, "--as-of", "record",
                                "--register-previous", str(ROOT / "demo" / "register"), "-f", "json"],
                               capture_output=True, text=True, env=env, timeout=600)
            rep = json.loads(p.stdout)
            got[task] = (p.returncode, [(f["severity"], f["ref"]) for f in rep["findings"] if f["kind"] == "suspect_derived"])
    assert got["design"] == (0, [("info", SUS["id"])]), got
    assert got["codegen"] == (1, [("blocker", SUS["id"])]), got
