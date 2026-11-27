"""task-0366: subject_overview states what a subject rests on and who owns its keys, from its files.

Its counts are held to the subject's register_map.toml read here apart from the module, each key's owner to the gate's
owner rule (capture.finding_owners, which a gate finding's owner reads), each node to the register's own loader; on
both public subjects, through the MCP reader in-process, with its inputSchema refusals. On a live store, over both
transports and on Neo4j, tools/check_mcp_server.py holds the held scenario and each gate key finding's owner too."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
import subject_overview as so  # noqa: E402
from test_mcp_server import _call, _server  # noqa: E402

SUBJECTS = [ROOT / "subjects" / "cargo_quote", ROOT / "subjects" / "jef_data_load"]


def _report(subject: Path, *args: str) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "subject_overview.py"), *args], capture_output=True, text=True,
                       timeout=120, env={**os.environ, "KG_SUBJECT": str(subject)})
    assert p.returncode == 0, p.stderr[-600:]
    return json.loads(p.stdout)


def _recount(subject: Path) -> dict:
    """The map's keys, nodes and node-key counts from the file itself, and every task class's keys."""
    manifest = tomllib.loads((subject / "subject.toml").read_text(encoding="utf-8"))
    rows = tomllib.loads((subject / manifest["register"]["map"]).read_text(encoding="utf-8")).get("row", [])
    keys = {r["key"] for r in rows}
    tasks = {k for t in manifest.get("tasks", {}).values() for k in t.get("keys", [])}
    per_node: dict[str, set] = {}
    for r in rows:
        for n in r.get("nodes") or []:
            per_node.setdefault(n, set()).add(r["key"])
    return {"rows": len(rows), "mapped": keys, "all": keys | tasks, "per_node": {n: len(ks) for n, ks in per_node.items()}}


def test_the_counts_are_the_register_maps_on_both_subjects():
    for subject in SUBJECTS:
        got = _report(subject)
        assert schema_check.validate(got, schema_check.load("subject-overview")) == [], subject.name
        want = _recount(subject)
        assert got["counts"]["rows"] == want["rows"] and got["counts"]["keys"] == len(want["all"]), subject.name
        assert {k["key"] for k in got["keys"] if k["mapped"]} == want["mapped"] and got["counts"]["mapped"] == len(want["mapped"])
        assert {n["id"]: n["keys"] for n in got["nodes"]} == want["per_node"], subject.name
        assert [(n["kind"] or "", n["id"]) for n in got["nodes"]] == sorted((n["kind"] or "", n["id"]) for n in got["nodes"])
        assert sum(r["keys"] for r in got["owners"]) == got["counts"]["keys"]
        assert sum(got["counts"]["nodes_by_kind"].values()) == got["counts"]["nodes"] == len(got["nodes"])
        assert got["held"] == {"scenario": None, "why": "no store was asked"} and "only through its register_map.toml rows" in got["note"]


def test_each_keys_owner_is_the_one_a_gate_finding_names():
    """The gate's findings name a key's owner by capture.finding_owners; the overview's owner per key is the same."""
    code = ("import sys, json; sys.path.insert(0, 'harness'); import capture, subject_overview as so; from subject import SUBJECT; "
            "f = capture.finding_owners(SUBJECT); r = so.report(); "
            "print(json.dumps([[k['key'], k['owner'], (f.get(k['key']) or {}).get('unit')] for k in r['keys']]))")
    for subject in SUBJECTS:
        p = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=120,
                           env={**os.environ, "KG_SUBJECT": str(subject)})
        assert p.returncode == 0, p.stderr[-600:]
        rows = json.loads(p.stdout)
        assert rows and all(mine == gate for _, mine, gate in rows), [r for r in rows if r[1] != r[2]][:5]


def test_a_task_narrows_the_keys_to_its_class_and_an_unknown_one_exits_2():
    got = _report(SUBJECTS[0], "--task", "design")
    manifest = tomllib.loads((SUBJECTS[0] / "subject.toml").read_text(encoding="utf-8"))
    assert {k["key"] for k in got["keys"]} == set(manifest["tasks"]["design"]["keys"]) and got["task"] == "design"
    assert all("design" in k["tasks"] for k in got["keys"])
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "subject_overview.py"), "--task", "nope"], capture_output=True,
                       text=True, timeout=60, env={**os.environ, "KG_SUBJECT": str(SUBJECTS[0])})
    assert p.returncode == 2 and "no task 'nope'" in p.stderr, p.stderr


def test_the_reader_serves_it_files_only_with_its_refusals():
    s, _ = _server()
    t = next(t for t in mcp_server.TOOLS if t["name"] == "subject_overview")
    assert t["_meta"][mcp_server.META_STORE] is False and mcp_server.OUTPUT_SCHEMAS["subject_overview"] == "subject-overview"
    assert "never infer" in t["description"] and "subject" in t["inputSchema"]["properties"]
    r = _call(s, "subject_overview")["result"]
    assert r["isError"] is False and schema_check.validate(r["structuredContent"], schema_check.load("subject-overview")) == []
    held = r["structuredContent"]["held"]   # the stub store's held scenario, or null with why: one of the two, never both
    assert (held["scenario"] is None) != (held["why"] is None), held
    for bad in ({"task": 3}, {"tasks": "codegen"}):
        assert _call(s, "subject_overview", bad)["error"]["code"] == -32602, bad
    no = _call(s, "subject_overview", {"task": "nope"})["result"]
    assert no["isError"] is True and "no task 'nope'" in no["content"][0]["text"]
    import result_marks
    assert result_marks.NARROWER["subject_overview"].startswith("subject_overview with task")
    m = result_marks.large("subject_overview", r["structuredContent"], 10 ** 6, 1000)   # a long list past the budget is marked
    assert m["count"] == {"what": "keys", "n": r["structuredContent"]["counts"]["keys"]}
