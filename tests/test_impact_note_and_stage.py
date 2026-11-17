"""task-0342 (decision-0041, brought into 0.10.0 on 2026-11-16): two additive answers on closed schemas.

B-X2 and R-T1: ``register_impact`` from a start whose kind has no step in the walk (a capability on thread, an
application on realisers, a unit on any walk) answers with ``note``, never with silence; the rule is the page's panel's
(``register_view._no_step``), held equal on every node and every walk. B-X8: ``store_status`` names the ``stage`` of the
scenario it holds, 1 or 2, absent when it holds none."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import mcp_server  # noqa: E402
import register_impact as ri  # noqa: E402
import schema_check  # noqa: E402
from test_mcp_server import Stub, _call, _server  # noqa: E402


def _no_store():
    return mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(OSError("no store here"))))


def _impact(s, args):
    r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "register_impact", "arguments": args}})
    assert r["result"]["isError"] is False, r
    return r["result"]["structuredContent"]


def test_a_walk_with_no_step_from_the_starts_kind_says_so_as_the_pages_panel_does_on_every_node_and_walk():
    import register_view
    root = ri.register_root()
    T = ri.load_tools(root)
    reg = T["register"].load_register(root)
    seen = {True: 0, False: 0}
    for which in ri.WALKS:
        rows = T["impact"].WALKS[which]
        for nid in sorted(reg["nodes"]):
            got = ri.walk(nid, which)
            page = register_view._no_step(reg["nodes"][nid], rows, nid, which)
            assert bool(got.get("note")) == bool(page), (which, nid, got.get("note"), page)
            seen[bool(page)] += 1
            if got.get("note"):
                assert got["edges"] == [] and got["reached_ids"] == [], (which, nid)   # no step: nothing walked from it
                assert nid in got["note"] and which in got["note"], got["note"]
    assert seen[True] and seen[False], seen


def test_the_note_is_on_the_mcp_answer_valid_and_absent_where_the_walk_steps():
    root = ri.register_root()
    T = ri.load_tools(root)
    reg = T["register"].load_register(root)
    schema = schema_check.load("register-impact")
    s = _no_store()
    cap = sorted(n for n, x in reg["nodes"].items() if x.get("_taxonomy") == "capabilities")[0]
    proc = next(n for n in sorted(reg["nodes"]) if reg["nodes"][n].get("_taxonomy") == "processes"
                and T["impact"].reached(T["impact"].walk(reg, n, T["impact"].WALKS["thread"])))
    unit = sorted(n for n, x in reg["nodes"].items() if x.get("_taxonomy") == "organisation")[0]
    on_cap = _impact(s, {"node": cap, "walk": "thread"})
    assert on_cap["edges"] == [] and "takes no step from " + cap in on_cap["note"] and "capabilit" in on_cap["note"]
    assert "journey steps, processes and applications" in on_cap["note"], on_cap["note"]
    assert not schema_check.validate(on_cap, schema)
    assert "note" not in _impact(s, {"node": proc, "walk": "thread"})
    on_unit = _impact(s, {"node": unit, "children": True})
    assert "takes no step from " + unit in on_unit["note"] and "each descendant is walked by its own kind" in on_unit["note"]
    assert not schema_check.validate(on_unit, schema)
    assert schema_check.validate({**on_cap, "note": 1}, schema), "note is a string"


def test_store_status_names_the_stage_it_holds_and_none_when_it_holds_nothing():
    from subject import SUBJECT
    schema = schema_check.load("store-status")
    got = _call(_server()[0], "store_status")["result"]["structuredContent"]
    assert got["scenario"] == SUBJECT.order[0] and got["stage"] == 1 and not schema_check.validate(got, schema)
    none = _call(_server(Stub(scenario=None))[0], "store_status")["result"]["structuredContent"]
    assert none["scenario"] is None and "stage" not in none and not schema_check.validate(none, schema)
    assert schema_check.validate({**got, "stage": 3}, schema), "1 or 2 only"
    two = next((sc for sc in SUBJECT.order if SUBJECT.scenario(sc).get("stage2")), None)
    if two is None:
        return   # this subject has no later version to hold

    class Changed(Stub):
        def held(self):
            return {**super().held(), "version": SUBJECT.scenario(two)["stage2"].get("version", "v2")}
    got = _call(_server(Changed(scenario=two))[0], "store_status")["result"]["structuredContent"]
    assert got["scenario"] == two and got["stage"] == 2 and not schema_check.validate(got, schema)
