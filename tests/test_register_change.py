"""A register change invalidates (task-0122): harness/register_change.py's diff and landing on the
fixture register (tools/register_fixture.py, built in a temporary directory; the vendored register
is never edited), the port's new write, the gate's flag and its schema, and the CI steps. The store
runs themselves (both adapters, the Turtle round trip) are tools/check_register_change.py's and
check_round_trip.py --register-previous, in harness.yml and the stack job. Plain asserts, stdlib only."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools"), str(Path(__file__).resolve().parent)]
import register_change as rc  # noqa: E402
import register_fixture as fx  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402

VENDORED = ROOT / "demo" / "register"
REASON = f"the register at {fx.TAG}: {fx.DECISION}"
DT_V = {"shipper_id|present", "weight_kg|min", "weight_kg|max", "distance_km|min", "distance_km|max",
        "declared_value|min", "declared_value|max", "invalid_request|behaviour"}


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="kg-regchange-"))


def test_the_fixture_change_withdraws_cap_0001_and_rel_06001_for_the_fixture_decision():
    d = _tmp()
    try:
        ch = rc.diff(VENDORED, fx.changed(d / "reg"))
        assert ch["from"]["tag"] == "v0.2.10" and ch["to"]["tag"] == fx.TAG
        assert ch["nodes"] == [{"id": "CAP-0001", "from": "approved", "to": "deprecated", "reason": REASON}]
        assert ch["links"] == [{"id": "REL-06001", "rel": "supports", "source": "APP-0002", "target": "PROC-0002",
                                "from": "approved", "to": "deprecated", "reason": REASON}]
        # moving the children is not a withdrawal: CAP-0002..5 keep their states
        assert not {n["id"] for n in ch["nodes"]} & {"CAP-0002", "CAP-0003", "CAP-0004", "CAP-0005"}
        # the vendored register is untouched
        assert 'state = "approved"' in (VENDORED / "capabilities" / "CAP-0001.toml").read_text(encoding="utf-8")
    finally:
        shutil.rmtree(d)


def test_an_update_with_no_state_change_withdraws_nothing_and_lands_nothing():
    d = _tmp()
    try:
        ch = rc.diff(VENDORED, fx.same(d / "same"))
        assert ch["nodes"] == [] and ch["links"] == []
        assert rc.resting(ch, {"row": [{"key": "k", "nodes": ["CAP-0001"]}]}, VENDORED, d / "same") == []
        assert rc.apply(None, []) == {"invalidated": []}, "nothing landed: the store is never touched"
        assert rc.diff(VENDORED, VENDORED)["nodes"] == [] and rc.diff(VENDORED, VENDORED)["links"] == []
    finally:
        shutil.rmtree(d)


def test_the_reason_is_the_decision_record_in_the_registers_own_order():
    """Its state line's note first (the register's practice: JRN-0008, REL-01006), then an approval
    record the change moved, then the decisions the update added, then the tag alone; a node that
    left the register is withdrawn too."""
    d = _tmp()
    try:
        cur = fx.same(d / "reg")
        p = cur / "capabilities" / "CAP-0002.toml"
        p.write_text(p.read_text(encoding="utf-8").replace('state = "approved"', 'state = "retired"   # decision 0006: noted', 1), encoding="utf-8")
        p = cur / "capabilities" / "CAP-0003.toml"
        p.write_text(re.sub(r'record = "[^"]*"', 'record = "decisions/0015-an-approved-child-of-a-deprecated-parent-is-a-finding.md"',
                            p.read_text(encoding="utf-8").replace('state = "approved"', 'state = "deprecated"', 1)), encoding="utf-8")
        p = cur / "capabilities" / "CAP-0004.toml"
        p.write_text(p.read_text(encoding="utf-8").replace('state = "approved"', 'state = "deprecated"', 1), encoding="utf-8")
        (cur / "capabilities" / "CAP-0008.toml").unlink()
        by = {n["id"]: n for n in rc.diff(VENDORED, cur)["nodes"]}
        six = next(x.name for x in (VENDORED / "decisions").glob("0006-*.md"))
        assert by["CAP-0002"]["to"] == "retired" and by["CAP-0002"]["reason"] == f"the register at {fx.TAG}: decisions/{six}"
        assert by["CAP-0003"]["reason"] == f"the register at {fx.TAG}: decisions/0015-an-approved-child-of-a-deprecated-parent-is-a-finding.md"
        assert by["CAP-0004"]["reason"] == f"the register at {fx.TAG}", "no note, no moved record, no added decision: the tag"
        assert by["CAP-0008"]["to"] is None and by["CAP-0008"]["from"] == "approved"
        (cur / fx.DECISION).write_text("# fixture\n", encoding="utf-8")
        assert {n["id"]: n for n in rc.diff(VENDORED, cur)["nodes"]}["CAP-0004"]["reason"] == REASON, "the decision the update added"
    finally:
        shutil.rmtree(d)


def test_the_keys_resting_on_the_change_follow_the_map_rows_and_the_registers_walk():
    """CAP-0001: the dependants walk with the descent by parent (decision 0014) on the previous
    register, the start never counted (decision 0016), less every descendant the new register moved
    away from it, in any state, with its subtree (the maintainer, 2026-11-04: moved, not withdrawn).
    The fixture moves all four, CAP-0005 (proposed) too, so CAP-0001 lands nothing. REL-06001: the
    rows naming both its ends and the rows its walk lands only through it: the eight DT-V rows."""
    SUBJECT = CARGO_QUOTE
    d = _tmp()
    try:
        cur = fx.changed(d / "reg")
        landed = rc.resting(rc.diff(VENDORED, cur), SUBJECT.register_map(), VENDORED, cur)
        keys = {k["key"]: k for k in landed}
        assert set(keys) == DT_V, sorted(keys)
        assert all({c.get("link") for c in v["causes"]} == {"REL-06001"} for v in keys.values()), "CAP-0001 lands nothing"
        assert all(v["reasons"] == [REASON] and v["owner"] for v in keys.values())
        both = [c for c in keys["shipper_id|present"]["causes"] if c["walk"] is None]
        assert both and both[0]["via"] == ["APP-0002", "PROC-0002"]
        lost = [c for c in keys["shipper_id|present"]["causes"] if c["walk"]]
        assert lost and lost[0]["from"] == "APP-0002" and "PROC-0002" in lost[0]["via"]
    finally:
        shutil.rmtree(d)


def test_a_descendant_left_below_the_withdrawn_node_is_descended_and_a_moved_one_skipped():
    """The same deprecation with the children left under CAP-0001 descends as register_impact
    --children does: 32 keys, the 32nd through the proposed CAP-0005, flagged (task-0120). Moving
    CAP-0003 alone, with whatever lies below it, skips exactly the rows only it carried."""
    import register_impact as ri
    SUBJECT = CARGO_QUOTE
    d = _tmp()
    try:
        cur = fx.changed(d / "reg")
        caps = cur / "capabilities"

        def parent(cap: str, to: str) -> None:
            p = caps / f"{cap}.toml"
            p.write_text(re.sub(r'^parent = "[^"]*"', f'parent = "{to}"', p.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")
        for c in ("CAP-0002", "CAP-0003", "CAP-0004", "CAP-0005"):
            parent(c, "CAP-0001")
        ch = rc.diff(VENDORED, cur)
        ch["links"] = []
        left = {k["key"]: k for k in rc.resting(ch, SUBJECT.register_map(), VENDORED, cur)}
        w = ri.walk("CAP-0001", "dependants", root=VENDORED, children=True)
        want = ri.landed_rows(SUBJECT.register_map(), "CAP-0001", w["reached_ids"], [x["id"] for x in w["children"] if x["walked"]],
                              [x["id"] for x in w["children"] if x["withdrawn"]])
        assert len(left) == 32 and set(left) == {r["key"] for r in want}, "register_impact's own landing"
        flagged = [k for k, v in left.items() if any(c.get("withdrawn") for c in v["causes"])]
        assert flagged == ["QuoteAPI|on_notification_failure"] and left[flagged[0]]["causes"][0]["via"] == ["CAP-0005"]
        assert all(c["moved"] == [] for v in left.values() for c in v["causes"])
        parent("CAP-0003", "CAP-0006")
        part = {k["key"]: k for k in rc.resting(ch, SUBJECT.register_map(), VENDORED, cur)}
        assert set(part) < set(left) and all(c["moved"] == ["CAP-0003"] for v in part.values() for c in v["causes"])
        only3 = {r["key"] for r in SUBJECT.register_map()["row"]
                 if "CAP-0003" in r["nodes"] and not set(r["nodes"]) & ({"CAP-0001", "CAP-0002", "CAP-0004", "CAP-0005"} | set(w["reached_ids"]))}
        assert only3 and set(left) - set(part) == only3, (sorted(set(left) - set(part)), sorted(only3))
    finally:
        shutil.rmtree(d)


def test_the_port_declares_the_write_and_both_adapters_implement_it():
    import store
    import store_neo4j
    assert "invalidate_keys" in vars(store.Store) and "invalidate_keys" in vars(store_neo4j.Neo4jStore)
    # the rdflib adapter imports rdflib, which this runner does without: read its source
    assert "    def invalidate_keys(self, reasons) -> dict:" in (ROOT / "harness" / "store_rdflib.py").read_text(encoding="utf-8")
    src = (ROOT / "harness" / "register_change.py").read_text(encoding="utf-8")
    assert "MATCH" not in src and "store.invalidate_keys" in src, "the change speaks the port, never Cypher"
    import mcp_server
    assert "invalidate_keys" not in mcp_server.READS, "the MCP server's view never writes"


def test_the_gate_refuses_the_flag_on_a_held_store_and_the_schema_takes_the_section():
    p = subprocess.run([sys.executable, "gate_cli.py", "--subject", str(ROOT / "subjects" / "cargo_quote"), "--no-load", "--register-previous", str(VENDORED), "--as-of", "2026-10-30"],
                       cwd=ROOT / "harness", capture_output=True, text=True)
    assert p.returncode == 2 and "--register-previous" in p.stderr, (p.returncode, p.stderr)
    import schema_check
    schema = schema_check.load("gate-report")
    src = {"tag": "v0.2.10", "commit": "4149e0677f09b329ee0d4c9e4b6c85e14d0bb424"}
    section = {"from": src, "to": src, "nodes": [{"id": "CAP-0001", "from": "approved", "to": "deprecated", "reason": REASON}],
               "links": [], "keys": [{"key": "P1|formula", "owner": "ORG-0001", "reasons": [REASON], "causes": ["CAP-0001"]}],
               "invalidated": ["A:dt:P1|formula@v1"], "derived": "derived:S1:G:run1"}
    sub = {**schema["properties"]["register_change"], "$defs": schema["$defs"]}
    assert schema_check.validate(section, sub) == []
    assert schema_check.validate(dict(section, extra=1), sub)
    assert "register_change" not in schema["required"], "additive: a report from before still validates"


def test_both_workflows_run_the_change_and_its_round_trip():
    h = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    s = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "KG_STORE=rdflib python tools/check_register_change.py runs/regchange" in h
    assert "check_round_trip.py --chain rdflib,rdflib --scenarios S1 --no-stage2 --register-previous demo/register" in h
    assert "check_register_change.py runs/regchange --stores neo4j,rdflib" in s
    assert "check_round_trip.py --chain neo4j,rdflib,neo4j --scenarios S1 --no-stage2 --register-previous demo/register" in s
    tool = (ROOT / "tools" / "check_register_change.py").read_text(encoding="utf-8")
    assert '"--as-of", "record"' in tool and "cadence.pin_record" in tool
