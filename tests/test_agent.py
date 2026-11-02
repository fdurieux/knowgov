"""The agent arm (harness/agent.py, task-0022.02): a turn loop with four tools over a sandbox,
driven here by a scripted responder and a stub suite, no client, no network. The sandbox refuses
paths outside itself; the ceiling ends a run with abstain and its reason; the trace carries every
turn and tool call with tokens, cost and elapsed seconds; a one-reply JSON is accepted as a finish."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import agent  # noqa: E402
import arms  # noqa: E402


def _call(name, **args):
    return {"id": f"c_{name}_{len(json.dumps(args))}", "name": name, "arguments": json.dumps(args)}


def _turn(calls=None, content=None, pt=1000, ct=100):
    return {"content": content, "tool_calls": calls or [], "model": "stub-model", "usage": {"prompt_tokens": pt, "completion_tokens": ct}, "seconds": 0.1}


def _scripted(turns):
    it = iter(turns)

    def respond(messages, tools):
        assert [t["function"]["name"] for t in tools] == ["read_document", "write_file", "run_suite", "finish"]
        return next(it)
    return respond


def _feedback(seen):
    def fb(root, feature):
        seen.append((sorted(p.name for p in Path(root).rglob("*") if p.is_file()), feature))
        return {"features": {"a": {"passed": 1, "total": 2, "failed": ["x"]}}, "passed": 1, "total": 2}
    return fb


def test_the_loop_writes_runs_reads_and_finishes_with_a_trace():
    seen = []
    docs = {"contracts/a.md": "A document"}
    turns = [_turn([_call("read_document", path="contracts/a.md"), _call("write_file", path="src/m.py", content="x = 1\n")]),
             _turn([_call("run_suite", feature="a")]),
             _turn([_call("write_file", path="../escape.py", content="bad"), _call("read_document", path="nope.md")]),
             _turn([_call("finish", decision="generate with assumptions", assumptions=[{"text": "t", "ref": "A:x"}], questions=["q"], claims=[])])]
    with tempfile.TemporaryDirectory() as td:
        box = Path(td) / "box"
        r = agent.run("sys", "user", sandbox=box, read_text=lambda p: docs[p], feedback=_feedback(seen), tag="t/G/1", responder=_scripted(turns))
        assert r["finished"] and r["stopped_by"] is None and r["parsed"]["decision"] == "generate with assumptions"
        assert r["files"] == ["src/m.py"] and (box / "src" / "m.py").read_text() == "x = 1\n"
        assert not (Path(td) / "escape.py").exists(), "a parent step never leaves the sandbox"
        assert seen == [(["m.py"], "a")]
        kinds = [t["kind"] for t in r["trace"]]
        assert kinds == ["model", "tool", "tool", "model", "tool", "model", "tool", "tool", "model", "tool"], kinds
        errors = [t for t in r["trace"] if t["kind"] == "tool" and "error" in t["result"]]
        assert len(errors) == 2 and "not a sandbox path" in errors[0]["result"]
        tot = r["totals"]
        assert tot["calls"] == 4 and tot["tool_calls"] == 6 and tot["prompt_tokens"] == 4000 and tot["completion_tokens"] == 400
        assert abs(tot["usd"] - 4 * (1000 * arms.PRICE_IN + 100 * arms.PRICE_OUT)) < 1e-6 and tot["model"] == "stub-model"
        assert all("at" in t and "seconds" in t for t in r["trace"]) and r["ceiling"]["calls"] == agent.DEFAULT_CEILING["calls"]
        assert agent.Sandbox(box).text().startswith("==> src/m.py <==\n")


def test_the_ceiling_ends_a_run_with_abstain_and_the_reason():
    turns = [_turn([_call("write_file", path=f"f{i}.py", content="")]) for i in range(10)]
    with tempfile.TemporaryDirectory() as td:
        r = agent.run("s", "u", sandbox=Path(td) / "b", read_text=lambda p: "", feedback=lambda root, f: {}, tag="t", responder=_scripted(turns), limits={"calls": 3})
        assert not r["finished"] and r["stopped_by"] == "ceiling: 3 calls" and r["parsed"]["decision"] == "abstain"
        assert "ceiling: 3 calls" in r["parsed"]["questions"][0] and r["totals"]["calls"] == 3 and len(r["files"]) == 3
        r2 = agent.run("s", "u", sandbox=Path(td) / "c", read_text=lambda p: "", feedback=lambda root, f: {}, tag="t",
                       responder=_scripted([_turn([_call("write_file", path="a.py", content="")], pt=10_000_000)] * 3), limits={"usd": 1.0})
        assert r2["stopped_by"] == "ceiling: $1.00" and r2["totals"]["calls"] == 1
    saved = {k: os.environ.pop(k, None) for k in ("KG_AGENT_MAX_CALLS", "KG_AGENT_MAX_USD", "KG_AGENT_MAX_SECONDS")}
    try:
        assert agent.ceiling() == agent.DEFAULT_CEILING
        os.environ["KG_AGENT_MAX_CALLS"] = "7"
        assert agent.ceiling()["calls"] == 7
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def test_a_json_reply_counts_as_a_finish_and_silence_is_nudged_then_stopped():
    with tempfile.TemporaryDirectory() as td:
        r = agent.run("s", "u", sandbox=Path(td) / "b", read_text=lambda p: "", feedback=lambda root, f: {}, tag="t",
                      responder=_scripted([_turn(content=json.dumps({"decision": "abstain", "questions": ["why"]}))]))
        assert r["finished"] and r["parsed"]["decision"] == "abstain" and r["parsed"]["questions"] == ["why"]
        r2 = agent.run("s", "u", sandbox=Path(td) / "c", read_text=lambda p: "", feedback=lambda root, f: {}, tag="t",
                       responder=_scripted([_turn(content="thinking...")] * 5))
        assert not r2["finished"] and r2["stopped_by"].startswith("no finish") and r2["totals"]["calls"] == agent.NUDGES + 1
        r3 = agent.run("s", "u", sandbox=Path(td) / "d", read_text=lambda p: "", feedback=lambda root, f: {}, tag="t",
                       responder=lambda m, t: (_ for _ in ()).throw(RuntimeError("boom")))
        assert r3["stopped_by"].startswith("api error: boom") and r3["parsed"]["decision"] == "abstain"


def test_safe_rel_and_the_tools_are_what_the_prompt_says():
    for bad in ("", "/etc/x", "../a", "a/../b", ".hidden", "a/.b/c", "~/x"):
        try:
            agent.safe_rel(bad); raise AssertionError(bad)
        except ValueError:
            pass
    assert agent.safe_rel("src\\jef\\x.py") == "src/jef/x.py"
    names = [t["function"]["name"] for t in agent.TOOLS]
    assert names == ["read_document", "write_file", "run_suite", "finish"]
    assert agent.TOOLS[3]["function"]["parameters"]["properties"]["decision"]["enum"] == ["generate", "generate with assumptions", "abstain"]


def test_the_page_reads_an_agent_runs_trace_and_its_sentences_keep_to_the_glossary():
    """views._runs loads the trace file beside an agent run and _run_view carries the agent summary;
    the Generate box's new sentences obey the glossary and the twenty-word limit."""
    import re
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import views
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        rec = {"scenario": "X", "arm": "G", "run": 1, "M1_decision": "abstain", "M2_code": True, "M3_flagged": {"flagged": False, "hits": []},
               "M4_suite": {"ran": True, "passed": 1, "total": 2, "per_scenario": {}}, "M4_targets": {}, "outage_status": None,
               "M5_refs": {"total": 0, "resolved": 0, "share": None}, "M6_noncompliance": False, "questions": [], "assumptions": [], "claims": [],
               "usage": {"model": "m", "prompt_tokens": 1, "completion_tokens": 1, "seconds": 2, "usd_est": 0.01, "attempts": 3},
               "agent": {"finished": False, "stopped_by": "ceiling: 3 calls", "turns": 4, "calls": 3, "tool_calls": 2, "files": ["a.py"], "ceiling": {}, "sandbox": "run1_G_sandbox"}}
        (d / "run1_G.json").write_text(json.dumps(rec), encoding="utf-8")
        (d / "run1_G.trace.json").write_text(json.dumps([{"turn": 1, "kind": "model", "tool_calls": ["write_file"], "text": "", "prompt_tokens": 1, "completion_tokens": 1, "usd": 0.0, "seconds": 0.1, "at": 0.1}]), encoding="utf-8")
        (d / "run1_G.py").write_text("==> a.py <==\nx = 1\n", encoding="utf-8")
        rs = views._runs(d, "G")
        assert len(rs) == 1 and rs[0]["trace"][0]["kind"] == "model" and rs[0]["code_text"].startswith("==> a.py")
        v = views._run_view(rs[0])
        assert v["agent"]["stopped_by"] == "ceiling: 3 calls" and v["trace"] and v["decision"] == "abstain"
    src = (ROOT / "demo" / "app" / "views.py").read_text(encoding="utf-8")
    for s in ["The arm worked in a sandbox over several turns.", "Its four tools: read a document, write a file, run the scenario's own feature files, finish.",
              "A run ends at a finish, or at the ceiling in calls, dollars or seconds, with decision abstain.",
              "A model turn names the tools it called.", "A tool step shows its arguments and its result, cut short.",
              "The last column is the second of the run at which the step ended.",
              "Adopted keys counts the keys below verified the arm's assumptions cite: the planted value relied on in the open.",
              "Read means the arm asked for the key's knowledge; assumed means its assumptions cite the key."]:
        assert s in src, s
        low = s.lower()
        assert not [f for f in views.FORBIDDEN if re.search(r"\b" + re.escape(f) + r"\b", low)], s
        assert len(s.replace(":", "").split()) <= 20, s


def test_m7_adopted_counts_the_keys_below_verified_the_assumptions_cite():
    """M7 beside M3: for G the key is read from the assertion id; for B a document line in a planted
    file counts by line; a value echo counts the plant's new text in an assumption."""
    import measures
    below = ["k1|v", "k2|v", "k3|v"]
    g = {"assumptions": [{"text": "k1 as proposed", "ref": "A:dt:k1|v@v1"}, {"text": "x", "ref": "A:req:k9|v@v2"}, {"text": "k2", "ref": "A:req:k2|v"}, "a string"]}
    r = measures.adopted("G", g, below, "S1")
    assert r["adopted"] == ["k1|v", "k2|v"] and r["count"] == 2 and r["planted"] == 3 and abs(r["share"] - 2 / 3) < 1e-9
    assert measures.adopted("G", None, below, "S1")["count"] == 0 and measures.adopted("B", g, below, "S1")["count"] == 0
    assert measures.adopted("G", {"assumptions": []}, [], "S1")["share"] is None


def test_extra_readers_are_tools_and_every_read_is_logged_as_consulted():
    """task-0022.03: a reader added by name becomes a tool; what the arm asked each read tool for
    is the consulted set, refusals included, in order."""
    turns = [_turn([_call("read_knowledge", key="k1|v"), _call("read_knowledge", key="nope"), _call("read_document", path="d.md")]),
             _turn([_call("finish", decision="abstain", questions=["q"])])]
    seen_tools = []

    def respond(messages, tools):
        seen_tools.append([t["function"]["name"] for t in tools])
        return turns.pop(0)
    kb = {"k1|v": "## k1|v level=proposed"}

    def read_knowledge(key):
        if key not in kb:
            raise KeyError(f"{key}: not a required key")
        return kb[key]
    with tempfile.TemporaryDirectory() as td:
        r = agent.run("s", "u", sandbox=Path(td) / "b", read_text=lambda p: "D", feedback=lambda root, f: {}, tag="t", responder=respond, readers={"read_knowledge": read_knowledge})
    assert seen_tools[0] == ["read_document", "write_file", "run_suite", "finish", "read_knowledge"]
    assert r["consulted"] == {"read_document": ["d.md"], "read_knowledge": ["k1|v", "nope"]}
    tools = [t for t in r["trace"] if t["kind"] == "tool"]
    assert "level=proposed" in tools[0]["result"] or "chars" in tools[0]["result"]
    assert "not a required key" in tools[1]["result"]


def test_the_pull_index_names_every_key_and_the_documents_and_the_key_section_is_the_bundles():
    import gate
    res = {"verdict": "QUALIFIED", "why": "1 key(s) below verified", "conflicts": [], "stale": [],
           "keys": {"k|v": {"level": "proposed", "flags": [], "declared_gaps": [],
                            "assertions": [{"id": "A:x:k|v@v1", "value": "1", "basis": "authored", "status": "proposed", "artefact": "doc", "agent": "a",
                                            "text": "one", "fragments": [], "verifications": [], "approvals": [], "gaps": []}]},
                    "u|v": {"level": "absent", "flags": [], "declared_gaps": [], "assertions": []}}}
    idx = gate.render_index(res, "POLICY", ["contracts/cli.md"])
    assert idx.startswith("GATE VERDICT: QUALIFIED") and "k|v | proposed | - | A:x:k|v@v1" in idx and "u|v | absent | - | (none: UNKNOWN)" in idx
    assert "read_knowledge(key)" in idx and "  contracts/cli.md" in idx and "text: one" not in idx, "the index carries ids, not the knowledge"
    section = "\n".join(gate.render_key("k|v", res["keys"]["k|v"]))
    assert section in gate.render_bundle(res, "POLICY") and "text: one" in section
    read, ids = gate.knowledge_reader(res)   # the governed arm's read tool names every assertion id it returned
    assert read("k|v") == section and read("u|v").startswith("\n## u|v") and ids == ["A:x:k|v@v1"]
    try:
        read("missing|v"); raise AssertionError("an unrequired key must be refused")
    except KeyError:
        pass
    assert ids == ["A:x:k|v@v1"], "a refused read adds nothing"
