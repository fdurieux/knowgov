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


def test_another_subjects_live_run_refuses_neither_tool():
    from subject import SUBJECT
    start = _start()
    if start is None:
        return
    other = "jef_data_load" if SUBJECT.id != "jef_data_load" else "cargo_quote"
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW):
        from test_scenario_runs import _run_json
        _run_json(Path(td) / other / "2026-11-04-2159", heartbeat_at=LIVE)
        assert not _call(_tools(Path(td)), "register_impact", {"node": start})["isError"]
        assert not _call(_tools(Path(td)), "proposal_impact", {"proposal": _proposal()})["isError"]


def test_on_an_rdflib_store_both_tools_refuse_live_and_answer_stale():
    """The same rule over a real rdflib store holding the subject's first scenario (the rdflib job runs it)."""
    try:
        from store_rdflib import RdflibStore
    except ModuleNotFoundError:
        return
    import mcp_server
    from subject import SUBJECT
    start = _start()
    if start is None:
        return
    with tempfile.TemporaryDirectory() as td, _Env(KG_NOW=NOW, KG_TODAY="2026-11-04"):
        path = str(Path(td) / "store.ttl")
        st = RdflibStore(path=path)
        st.create_node("agent:t", "Agent", {})
        st.create_activity(f"act:extract:{SUBJECT.order[0]}:v1", "extract", "2026-11-04T21:00:00+00:00", "t", "", "agent:t")
        st.close()

        def tools():
            return mcp_server.Tools(opener=lambda: mcp_server.open_read_only(lambda **kw: RdflibStore(path=path, **kw)), runs=Path(td))
        _live_and_stale(Path(td), LIVE)
        for name, args in (("register_impact", {"node": start}), ("proposal_impact", {"proposal": _proposal()})):
            r = _call(tools(), name, args)
            assert r["isError"] and "a run is loading the store" in r["content"][0]["text"], (name, r)
        _live_and_stale(Path(td), STALE)
        for name, args in (("register_impact", {"node": start}), ("proposal_impact", {"proposal": _proposal()})):
            r = _call(tools(), name, args)
            assert not r["isError"], (name, r["content"][0]["text"])
