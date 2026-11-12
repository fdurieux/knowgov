"""Task-0283 (decision-0033 choice 9, G9-17): ``held_keys``' ``gate`` is the task class's own verdict.

Probed on CargoQuote S1: the field gated all 93 held keys under codegen's bar as if each were required, and read
"codegen BLOCKED: 34 of 93 required keys (37%) are below verified" where ``gate_verdict`` codegen gives PROCEED.
Now the levels still come from the held key set (every held key's level, as ``gate_verdict keys=...`` reads it) and
the verdict and why from the class's own spec, as ``gate_verdict`` computes them. Stdlib, with the gate stubbed:
the evaluations it asks for are what is held. tools/check_mcp_server.py holds it equal to ``gate_verdict`` on a
live store, every task class, both subjects."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]


class Store:
    name = "double"

    def __init__(self, keys):
        self._keys = keys

    def held_keys(self):
        return [{"key": k, "n": 1, "statuses": {"proposed": 1}} for k in self._keys]


def _run(held, task="codegen"):
    import gate_cli
    import store_reads
    from tasks import TASKS
    calls = []

    def evaluate(st, *, subject, scenario, task, spec, **kw):
        calls.append((task, list(spec["keys"])))
        if task == "keys":   # the held set: levels for every held key, and a verdict the field must not take
            return {"levels": {k: "proposed" for k in spec["keys"]}, "verdict": "BLOCKED",
                    "why": f"{len(spec['keys'])} of {len(spec['keys'])} required keys are below verified"}
        return {"levels": {}, "verdict": "PROCEED", "why": f"all {len(spec['keys'])} required keys verified or approved"}
    real = gate_cli.evaluate, gate_cli.held_version
    gate_cli.evaluate, gate_cli.held_version = evaluate, (lambda st: "v1")
    try:
        rep = store_reads.held_keys(Store(held), subject="s", scenario="S1", task=task, as_of="2026-10-30")
    finally:
        gate_cli.evaluate, gate_cli.held_version = real
    return rep, calls, TASKS


def test_the_gate_is_the_task_classs_own_verdict_on_its_own_keys():
    from tasks import TASKS
    task = "codegen" if "codegen" in TASKS else sorted(TASKS)[0]
    held = list(TASKS[task]["keys"]) + ["Extra|one", "Extra|two"]
    rep, calls, TASKS = _run(held, task)
    assert calls == [("keys", held), (task, list(TASKS[task]["keys"]))]
    assert rep["gate"] == {"task": task, "verdict": "PROCEED", "why": f"all {len(TASKS[task]['keys'])} required keys verified or approved"}
    assert all(r["level"] == "proposed" for r in rep["keys"])   # the levels still the held set's


def test_a_store_holding_no_key_still_has_the_classs_own_gate():
    """task-0292 (group 2's re-probe): on minimal S0, holding no key, the field was null where gate_verdict gives
    BLOCKED; it is now the class's own verdict whatever the store holds."""
    from tasks import TASKS
    task = sorted(TASKS)[0]
    rep, calls, _ = _run([], task)
    assert calls == [(task, list(TASKS[task]["keys"]))]   # no held-set evaluation, the class's own still
    assert rep["gate"]["task"] == task and rep["gate"]["verdict"] == "PROCEED" and rep["keys"] == []


def test_with_no_task_class_the_gate_is_null_and_nothing_is_evaluated():
    rep, calls, _ = _run(["Extra|one"], task=None)
    assert rep["gate"] is None and calls == [] and rep["keys"][0]["level"] is None


def test_the_description_and_the_schema_say_what_the_field_is():
    import json
    src = (ROOT / "harness" / "mcp_server.py").read_text(encoding="utf-8")
    assert "gate is gate_verdict's verdict and why for the task class itself" in src
    assert "null only when the subject declares no task class" in src
    schema = json.loads((ROOT / "harness" / "schemas" / "held-keys.schema.json").read_text(encoding="utf-8"))
    assert "own required keys" in schema["properties"]["gate"]["description"]
    assert "whatever the store holds" in schema["properties"]["gate"]["description"]
    assert "task-0292" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## 0.9.0 ", 1)[1].split("\n## ", 1)[0]
    assert "task-0283" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## 0.9.0 ", 1)[1].split("\n## ", 1)[0]
