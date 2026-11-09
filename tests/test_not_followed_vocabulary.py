"""Task-0305 (decision-0035, doc-0037 §3.4, B3): "withdrawn" means deprecated or retired, nothing else.

The walk lists every edge it does not follow (a link not approved, a proposed one included, or a far node deprecated
or retired) and every descendant it does not walk from. Those lists were named ``withdrawn``: proposal-impact's
``slices.map[].withdrawn`` and ``keys.behind_withdrawn``, register_impact's flag, step-grid's ``behind_withdrawn`` and
the page's "no, withdrawn". Now each is ``not_followed`` (``behind_not_followed`` for the keys behind one), with the
edge's state, and no not-followed list is named ``withdrawn``. Stdlib: the register's own tools, no store."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]

SCHEMAS = ("proposal-impact", "register-impact", "step-grid")


def _keys(o, path="$"):
    """Every property name in a JSON value, with its path."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield f"{path}.{k}", k
            yield from _keys(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _keys(v, f"{path}[{i}]")


def _proposal(*args) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), *args, "--as-of", "record", "-f", "json"],
                       capture_output=True, text=True, cwd=ROOT, env={"PATH": "", "KG_TODAY": "2026-11-09"})
    assert p.returncode in (0, 1), p.stderr[-600:]
    return json.loads(p.stdout)


def test_no_schema_names_a_not_followed_list_withdrawn():
    for name in SCHEMAS:
        schema = json.loads((ROOT / "harness" / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
        named = [p for p, k in _keys(schema) if "withdrawn" in k]
        assert named == [], (name, named)
    for name in ("proposal-impact", "step-grid"):   # a rename is not additive: a new version (the schema's own rule)
        schema = json.loads((ROOT / "harness" / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert schema["properties"]["schema_version"]["const"] == 2, name


def test_the_reproduction_names_the_proposed_edge_not_followed_with_its_state():
    rep = _proposal("--scope", "JRN-0001")   # the review's reproduction, at main f194aac
    by = {s["start"]["id"]: s for s in rep["slices"]["map"]}
    assert {"from": "JRN-0003", "rel": "is_supported_by", "to": "PROC-0005", "state": "proposed"} in by["JRN-0003"]["not_followed"]
    assert [p for p, k in _keys(rep) if "withdrawn" in k] == []


def test_the_worked_example_names_nothing_withdrawn():
    rep = _proposal(str(ROOT / "tools" / "fixtures" / "proposal_contract_quote.json"))
    assert [p for p, k in _keys(rep) if "withdrawn" in k] == []
    assert all("behind_not_followed" in s["keys"] for s in rep["slices"]["map"] if s.get("keys"))


def test_register_impact_flags_a_descendant_and_a_key_not_followed():
    import register_impact as ri
    w = ri.walk("CAP-0001", "dependants", children=True)
    assert [p for p, k in _keys(w) if "withdrawn" in k] == []
    proposed = [c for c in w["children"] if c["state"] == "proposed"]
    assert proposed and all(c["not_followed"] is True and c["walked"] is False for c in proposed)   # proposed: not followed
    rows = ri.landed_rows({"row": [{"key": "a|b", "nodes": [proposed[0]["id"]]}]}, "CAP-0001", [], [], [proposed[0]["id"]])
    assert rows == [{"key": "a|b", "owner": None, "anchor": None, "via": [proposed[0]["id"]], "not_followed": True}]


def test_the_page_and_the_saved_queries_say_not_followed_and_why():
    import register_view
    import store_neo4j as sn
    assert register_view.followed({"live": False, "state": "proposed"}) == "no, not followed (link proposed)"
    assert register_view.followed({"live": False, "state": "approved"}) == "no, not followed (far node deprecated or retired)"
    assert register_view.followed({"live": True, "state": "approved"}) == "yes"
    for text in (sn.IMPACT_ROWS, sn.DEPENDANTS_CAPABILITY):
        assert "no, withdrawn" not in text and "no, not followed (link " in text


def test_the_changelog_names_the_rename_under_contract_changes():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    assert "task-0305" in log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
