"""Task-0129 (doc-0016 item 1, step 3): scenario_result, what the page's Replay shows for one source,
as data, read-only, from the files harness/runs_index.py lists; it never opens the store and says so."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app"), str(Path(__file__).resolve().parent)]
import mcp_server  # noqa: E402
import page_subject  # noqa: E402
import runs_index  # noqa: E402
import views  # noqa: E402
from _subject_pin import CARGO_QUOTE  # noqa: E402
from test_scenario_runs import _call  # noqa: E402

NO_RUNS = ROOT / "nonexistent-demo-runs"


def test_every_cargo_quote_record_source_equals_the_pages_replay():
    seen = 0
    with page_subject.using(CARGO_QUOTE):
        for sc in CARGO_QUOTE.order:
            for src in runs_index.sources_for(CARGO_QUOTE, sc, NO_RUNS):
                got = runs_index.result(CARGO_QUOTE, NO_RUNS, sc, src["id"])
                view = views.build(sc, src["id"], NO_RUNS)
                assert got["gate"] == view["gate"], (sc, src["id"])
                assert got["as_of"] == view["as_of"]["date"]
                for arm in ("G", "B"):
                    assert [r["decision"] for r in got["arms"][arm]] == [r["decision"] for r in view["arms"][arm]["runs"]], (sc, src["id"], arm)
                    assert [r["suite"] for r in got["arms"][arm]] == [x if x != "—" else None for x in view["arms"][arm]["summary"]["suites"]]
                assert len(got["levels"]) == view["required_keys"]
                seen += 1
    assert seen == 7 + 2, seen   # S1-S7, and S6's rerun and d3check


def test_a_source_not_listed_is_refused_no_path_is_taken_and_the_reply_says_it_reads_files():
    t = next(x for x in mcp_server.TOOLS if x["name"] == "scenario_result")
    assert t["annotations"] == mcp_server.READ_ONLY and set(t["inputSchema"]["properties"]) == {"scenario", "source"}
    opened = []

    def opener():
        opened.append(1)
        raise AssertionError("scenario_result opened the store")
    from subject import SUBJECT
    sc = SUBJECT.order[0]
    with tempfile.TemporaryDirectory() as td:
        tools = mcp_server.Tools(opener=opener, runs=Path(td))
        r = _call(tools, "scenario_result", {"scenario": sc, "source": "record"})
        assert not r["isError"], r["content"][0]["text"]
        j = r["structuredContent"]
        assert j["source"] == "record" and "not the store" in j["reads"] and j["gate"]["verdict"]
        for bad in ("../../etc", "/tmp", "demo-runs/nope", "", None):
            r = _call(tools, "scenario_result", {"scenario": sc, "source": bad})
            assert r["isError"], bad
        assert _call(tools, "scenario_result", {"scenario": "nope", "source": "record"})["isError"]
    assert opened == []
