"""task-0371 (impact gap G4): ``capture.py questionnaire --stage 2`` asks after a change.

The questionnaire loads the scenario's later version as ``gate_cli.py --stage 2`` does (the gate's own
``_change``, in a scratch store), so each key a statement was invalidated on is asked with the invalidated
statement and its successor, each naming its version, and a key the new version adds that the task requires is
an item; the added keys no class requires and the invalidated statements on keys the task does not require are
stderr notes. Stage 1 is unchanged. Held on S6's change, the record's, and on a public plant on it in which the
later decision table adds two statements its first version lacks (the change adds no key of its own). Each answer
the stage-2 questionnaire takes is one ``ingest`` accepts.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import capture  # noqa: E402
from _skip import need_rdflib  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402

DAY = "2026-11-27"
ENV = {"KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"), "KG_STORE": "rdflib", "KG_CLOCK": "pinned",
       "KG_TODAY": DAY, "PYTHONDONTWRITEBYTECODE": "1"}
# S6's change invalidates these (the record's D3); the first three are codegen's keys, the fourth no class's
INVALIDATED = {"A:dt:P2|surcharge@v1": "P2|surcharge", "A:dt:P2|threshold@v1": "P2|threshold",
               "A:dt:P3|order@v1": "P3|order", "A:dt:worked_example|price@v1": "worked_example|price"}


def _env() -> dict:
    env = {**os.environ, **ENV}
    env.pop("KG_RDFLIB_FILE", None)
    return env


def _cli(out: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "harness" / "capture.py"), "questionnaire", "--scenario", "S6", *args,
                           "--out", str(out)], env=_env(), cwd=ROOT, capture_output=True, text=True, timeout=900)


def _items(doc: dict) -> dict[str, dict]:
    return {it["key"]: it for it in doc.get("item", [])}


def test_s6_stage_2_asks_each_stale_key_with_both_versions():
    """AC1, AC2: S6's three codegen keys the change invalidated a statement on are asked, each item's ``known`` naming
    the invalidated v1 statement and its v2 successor, each with its version; the fourth, on worked_example|price,
    is no class's key and is named on stderr, not asked."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        p = _cli(Path(td), "--stage", "2")
        assert p.returncode == 0, p.stdout + p.stderr
        [f] = sorted(Path(td).glob("questionnaire-cargo_quote-S6-*.toml"))
        text = f.read_text(encoding="utf-8")
    doc = tomllib.loads(text)
    items = _items(doc)
    assert sorted(items) == ["P2|surcharge", "P2|threshold", "P3|order"], sorted(items)
    assert items["P2|surcharge"]["known"] == ["316.00 (invalidated, v1, extracted, contract/decision_table.md)",
                                              "341.00 (proposed, v2, extracted, contract/decision_table.md)"]
    assert items["P2|threshold"]["known"] == ["1244 (invalidated, v1, extracted, contract/decision_table.md)",
                                              "1244 (proposed, v2, extracted, contract/decision_table.md)"]
    # P3|order@v1 is superseded by its approved sibling, so the gate drops it from the key's rows; the item keeps it
    assert "after P2 (invalidated, v1, extracted, contract/decision_table.md)" in items["P3|order"]["known"]
    assert any(", v2, " in k for k in items["P3|order"]["known"])
    assert "# Stage 2: after contract/decision_table.md was read in again as v2; 4 statement(s)" in text
    assert "A:dt:worked_example|price@v1 (worked_example|price; required by no task)" in p.stderr, p.stderr
    assert "adds" not in p.stderr, p.stderr   # S6's change adds no key


def test_stage_1_is_unchanged_and_stage_2_needs_a_later_version():
    """Without --stage, S6 has nothing open, as before; --stage 2 on a scenario with no [scenario.stage2] cannot run."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        p = _cli(Path(td))
        assert p.returncode == 0 and "nothing is open for any owner" in p.stdout and not list(Path(td).glob("*.toml")), p.stdout + p.stderr
        assert "note:" not in p.stderr, p.stderr
        q = subprocess.run([sys.executable, str(ROOT / "harness" / "capture.py"), "questionnaire", "--scenario", "S2", "--stage", "2",
                            "--out", td], env=_env(), cwd=ROOT, capture_output=True, text=True, timeout=600)
        assert q.returncode == 2 and "S2 has no later version" in q.stderr, q.stdout + q.stderr


def test_stage_1_known_strings_carry_no_version():
    """The stage-1 text is the one before task-0371: ``known`` names no version when no change is passed."""
    a = {"id": "A:x@v1", "value": "3", "status": "proposed", "basis": "extracted", "artefact": "d.md"}
    assert capture.known_of("k|p", {"assertions": [a]}, {"stale": []}, None) == ["3 (proposed, extracted, d.md)"]
    assert capture.known_of("k|p", {"assertions": [a]}, {"stale": []}, {"A:x@v1": {**a, "version": "v1"}}) == ["3 (proposed, v1, extracted, d.md)"]


def test_the_change_notes_name_what_no_item_asks():
    tasks = {"codegen": {"keys": ["a|x", "b|y"]}, "design": {"keys": ["c|z"]}}
    change = {"invalidated_keys": {"A:1@v1": "a|x", "A:2@v1": "q|w"}, "added": ["b|y", "c|z", "n|o"]}
    notes = capture.change_notes(change, {"keys": {"a|x": {}, "b|y": {}}}, "codegen", tasks)
    assert notes == [
        "note: 1 statement(s) the change invalidated are on keys task codegen does not require, so no item asks them: A:2@v1 (q|w; required by no task)",
        "note: 1 key(s) the new version adds are required by another task, not codegen (its questionnaire, --task, asks them): c|z (design)",
        "note: 1 key(s) the new version adds are required by no task, so no questionnaire asks them: n|o",
        "note: 1 key(s) the new version adds are required by task codegen, each an item of its owner's questionnaire where it is open: b|y",
    ], notes
    assert capture.change_notes(None, {"keys": {}}, "codegen", tasks) == []


# A public plant on S6: the first decision table lacks the P4 row and the review-hold note, which the later one (S6's v2)
# has, so the change adds P4|rounding (a codegen key) and S-review|final (no class's key) beside its own tariff change.
PLANT = r'''
import json, sys
sys.path.insert(0, "harness")
import change, kitio, capture
from subject import SUBJECT
from store import scratch_store
from tasks import TASKS
ART = "contract/decision_table.md"
real = kitio.kit_for
def planted(sc, stage=1):
    kit = dict(real(sc, stage))
    if stage == 1:
        t = kit[ART]
        row = next(l for l in t.splitlines() if l.startswith("| P4 |"))
        note = "A review hold is not a final outcome"
        assert row in t and note in t
        kit[ART] = t.replace(row + "\n", "").replace(note, "A held quote is set aside")
    return kit
kitio.kit_for = change.kit_for = planted
cfg2 = SUBJECT.scenario("S6")["stage2"]
with scratch_store(instance=SUBJECT.id) as st:
    res1, _, _ = capture.questionnaire_view(st, SUBJECT, "S6", "codegen")
with scratch_store(instance=SUBJECT.id) as st:
    res, ch, rows = capture.questionnaire_view(st, SUBJECT, "S6", "codegen", cfg2)
nodes = capture.register_nodes(capture.register_root())
import datetime as dt
qs = capture.questionnaires(res, SUBJECT, "S6", "codegen", nodes, dt.date.fromisoformat(sys.argv[1]), change=ch, statements=rows)
print(json.dumps({"stage1_level": res1["keys"]["P4|rounding"]["level"], "added": ch["added"],
                  "notes": capture.change_notes(ch, res, "codegen", TASKS), "qs": qs}))
'''


def test_a_key_the_new_version_adds_is_asked_and_an_unrequired_one_noted():
    """AC3 on the public plant: P4|rounding, absent at stage 1, is an item at stage 2 with its v2 statement;
    S-review|final, which no class requires, is named by a note and asked by no questionnaire."""
    need_rdflib()
    p = subprocess.run([sys.executable, "-c", PLANT, DAY], env=_env(), cwd=ROOT, capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-3000:]
    got = json.loads(p.stdout.strip().splitlines()[-1])
    assert got["stage1_level"] == "absent", got["stage1_level"]
    assert "P4|rounding" in got["added"] and "S-review|final" in got["added"], got["added"]
    assert any("required by no task" in n and "S-review|final" in n for n in got["notes"]), got["notes"]
    assert any("required by task codegen" in n and "P4|rounding" in n for n in got["notes"]), got["notes"]
    items = {k: it for t in got["qs"].values() for k, it in _items(tomllib.loads(t)).items()}
    assert "S-review|final" not in items
    assert items["P4|rounding"]["level"] != "absent" and any(", v2, " in k for k in items["P4|rounding"]["known"]), items["P4|rounding"]


def test_ingest_accepts_an_answered_stage_2_questionnaire():
    """AC4: the stage-2 file ingests as any questionnaire does: answers bind by key, the known strings unread."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        assert _cli(Path(td), "--stage", "2").returncode == 0
        [f] = sorted(Path(td).glob("questionnaire-cargo_quote-S6-*.toml"))
        doc = tomllib.loads(f.read_text(encoding="utf-8"))
    doc["answered"] = {"from": "employee-1", "on": DAY}
    for it in doc["item"]:
        if it["key"] == "P2|surcharge":
            it["answer"] = "341.00"
    errs, cap = capture.check_answers(doc, capture.DEFAULT_HANDLE, set(CARGO_QUOTE.tasks["codegen"]["keys"]), dt.date.fromisoformat(DAY))
    assert errs == [], errs
    assert cap["answers"] == [{"key": "P2|surcharge", "value": "341.00", "note": ""}] and cap["scenario"] == "S6"
    assert "[[answer]]" in capture.capture_toml(cap, "captures/x.toml")


def test_a_stage_2_gate_reports_routes_name_the_stage_2_questionnaire():
    """The route a finding names after the change runs ``capture.py questionnaire --stage 2``, the command this task
    adds, where it named the stage-1 one, which asks the first version's statements; stage 1's route is unchanged."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "s6.json"
        p = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--scenario", "S6", "--stage", "2", "--as-of", "record",
                            "-f", "json", "-o", str(out)], env=_env(), cwd=ROOT, capture_output=True, text=True, timeout=900)
        assert p.returncode == 1, p.stdout + p.stderr
        rep = json.loads(out.read_text(encoding="utf-8"))
    routes = {f["key"]: f["route"] for f in rep["findings"] if f.get("kind") == "key" and f.get("route")}
    assert {"P2|surcharge", "P2|threshold"} <= set(routes), routes
    for key, r in routes.items():
        assert r.startswith("python harness/capture.py questionnaire --scenario S6 --task codegen --stage 2 --out DIR; "), (key, r)


def test_route_stage_reads_the_change_or_the_held_later_version():
    """``gate_cli.route_stage``: 2 with a change, or for a store holding the version S6's [scenario.stage2] names (the MCP
    reader and --no-load); 1 otherwise, and for a scenario with no later version or another subject."""
    code = ("import sys; sys.path.insert(0, 'harness'); import gate_cli as g, capture as c; "
            "print([g.route_stage('cargo_quote', 'S6', 'v1', {'x': 1}), g.route_stage('cargo_quote', 'S6', 'v2', None), "
            "g.route_stage('cargo_quote', 'S6', 'v1', None), g.route_stage('cargo_quote', 'S2', 'v2', None), "
            "g.route_stage('other', 'S6', 'v2', None)]); "
            "print(c.questionnaire_route('cargo_quote', 'S6', 'codegen', 'ORG-0001') == "
            "c.questionnaire_route('cargo_quote', 'S6', 'codegen', 'ORG-0001', None, 1))")
    p = subprocess.run([sys.executable, "-c", code], env=_env(), cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    assert p.stdout.split() == ["[2,", "2,", "1,", "1,", "1]", "True"], p.stdout
