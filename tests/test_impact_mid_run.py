"""Task-0137: register_impact and proposal_impact refuse while a run of the server's subject is
loading the store, on the path where they read key levels from it, as gate_verdict does (task-0128,
doc-0016 F2); their register-only answers (no scenario held, or the store not reachable) are
unaffected, and a stale heartbeat does not refuse."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from test_mcp_server import Stub  # noqa: E402
from test_proposal_impact import _proposal  # noqa: E402
from test_scenario_runs import NOW, _Env, _call, _live_and_stale, _tools  # noqa: E402

LIVE, STALE = "2026-11-04T21:59:30+00:00", "2026-11-04T21:57:59+00:00"


def _start():
    from subject import SUBJECT
    rows = SUBJECT.register_map().get("row") or []
    return rows[0]["nodes"][0] if rows else None


def test_register_impact_refuses_mid_run_where_it_reads_levels_and_answers_from_the_register_alone():
    start = _start()
    if start is None:
        return
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        run = _live_and_stale(Path(td), LIVE)
        r = _call(_tools(Path(td)), "register_impact", {"node": start})
        assert r["isError"] and "a run is loading the store" in r["content"][0]["text"] and run["id"] in r["content"][0]["text"], r
        alone = _call(_tools(Path(td), Stub(scenario=None)), "register_impact", {"node": start})
        assert not alone["isError"] and alone["structuredContent"]["gate"] is None and alone["structuredContent"]["keys"]
        assert all("level" not in k for k in alone["structuredContent"]["keys"])
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        _live_and_stale(Path(td), STALE)
        r = _call(_tools(Path(td)), "register_impact", {"node": start})
        assert not r["isError"] and r["structuredContent"]["gate"] is not None, "a stale heartbeat does not refuse"


def test_proposal_impact_refuses_mid_run_where_it_reads_levels_and_answers_from_the_register_alone():
    if _start() is None:
        return
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        _live_and_stale(Path(td), LIVE)
        r = _call(_tools(Path(td)), "proposal_impact", {"proposal": _proposal()})
        assert r["isError"] and "a run is loading the store" in r["content"][0]["text"], r
        alone = _call(_tools(Path(td), Stub(scenario=None)), "proposal_impact", {"proposal": _proposal()})
        assert not alone["isError"] and alone["structuredContent"]["keys"]["scenario"] is None
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        _live_and_stale(Path(td), STALE)
        assert not _call(_tools(Path(td)), "proposal_impact", {"proposal": _proposal()})["isError"]
