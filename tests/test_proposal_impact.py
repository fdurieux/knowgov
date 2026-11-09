"""Task-0130 and task-0131 (doc-0017): a proposed addition read against the register as if approved,
without approving it, and its deterministic link candidates D1 to D5. The proposal is doc-0017 §2's
worked example on the public register (tools/fixtures/proposal_contract_quote.json, synthetic). The
register's own functions decide; nothing is written to the register or the store."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import mcp_server  # noqa: E402
import proposal_impact as pi  # noqa: E402
import register_impact as ri  # noqa: E402
import schema_check  # noqa: E402
from tests.test_mcp_server import DAY, Stub, _call, _server  # noqa: E402

FIXTURE = ROOT / "tools" / "fixtures" / "proposal_contract_quote.json"
TODAY = pi._date(DAY, "day")
SCHEMA = schema_check.load("proposal-impact")


def _proposal() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _report(proposal=None, **kw) -> dict:
    return pi.evaluate(_proposal() if proposal is None else proposal, today=TODAY, **kw)


def _digests(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def _valid(rep: dict) -> None:
    errors = schema_check.validate(json.loads(json.dumps(rep, default=str)), SCHEMA)
    assert errors == [], errors[:5]


# ---- task-0241: every coverage rule the register's checker defines, C4 (decision 0020) among them

C4_FIXTURE = ROOT / "tools" / "fixtures" / "proposal_c4_gap.json"


def test_coverage_reads_every_rule_the_registers_checker_defines_and_a_c4_gap_is_reported_hypothetical():
    """A process proposed to realise an approved capability, with a diagram of record and no supporting
    application: C1 to C3 hold as before and C4 falls from 5/5 to 5/6, its gap on the hypothetical process.
    The rules are the checker's own COVERAGE_RULES, in its order, so a later rule needs no code here."""
    r = _report(json.loads(C4_FIXTURE.read_text(encoding="utf-8")))
    _valid(r)
    cov = r["coverage"]
    assert list(cov["before"]) == list(cov["after"]) == ["C1", "C2", "C3", "C4"]
    assert {c: (cov["after"][c]["covered"], cov["after"][c]["denominator"]) for c in cov["after"]} == \
        {"C1": (7, 8), "C2": (5, 5), "C3": (6, 6), "C4": (5, 6)}
    assert cov["new_gaps"] == [{"rule": "C4", "id": "PROC-0011", "hypothetical": True}]
    assert cov["after"]["C4"]["uncovered"] == [{"id": "PROC-0011", "hypothetical": True}]
    assert "  C4: 5/5 -> 5/6 covered; uncovered ['PROC-0011']" in pi.render_text(r).splitlines()
    worked = _report()["coverage"]
    assert (worked["before"]["C4"]["covered"], worked["after"]["C4"]["covered"]) == (5, 5), "the worked example breaks no C4"


def test_the_rules_are_the_checkers_own_and_a_report_on_an_earlier_register_still_validates():
    class Checker:
        COVERAGE_RULES = {"C1": "", "C2": "", "C3": "", "C4": "", "C9": ""}
    assert pi.coverage_rules(Checker) == ("C1", "C2", "C3", "C4", "C9")
    r = _report()
    for side in ("before", "after"):   # a register before decision 0020 defines no C4: the schema requires C1 to C3 only
        del r["coverage"][side]["C4"]
    _valid(r)


# ---- task-0261: the schema names no rule; a register defining C5 yields a valid report

C5 = """

# task-0261's fixture: a fifth coverage rule, read by proposal_impact from this list, the schema naming none
COVERAGE_RULES["C5"] = "a fixture rule: every process C4 finds unsupported, again"
_check_coverage_c1_to_c4 = check_coverage


def check_coverage(reg, f, today):
    s = _check_coverage_c1_to_c4(reg, f, today)
    s["C5"] = {**s["C4"], "uncovered": list(s["C4"]["uncovered"])}
    return s
"""


def _register_with_c5(dest: Path) -> Path:
    """The vendored register copied, its checker given a C5 that repeats C4: synthetic, under ``dest``."""
    reg = dest / "register"
    shutil.copytree(ri.register_root(), reg, ignore=shutil.ignore_patterns("__pycache__"))
    tool = reg / "tools" / "check_register.py"
    tool.write_text(tool.read_text(encoding="utf-8") + C5, encoding="utf-8")
    return reg


def test_a_register_defining_c5_yields_a_report_valid_under_the_unchanged_schema():
    with tempfile.TemporaryDirectory() as t:
        reg = _register_with_c5(Path(t))
        r = pi.evaluate(json.loads(C4_FIXTURE.read_text(encoding="utf-8")), root=reg, today=TODAY)
    _valid(r)
    cov = r["coverage"]
    assert list(cov["before"]) == list(cov["after"]) == ["C1", "C2", "C3", "C4", "C5"]
    assert [(g["rule"], g["id"], g["hypothetical"]) for g in cov["new_gaps"]] == [("C4", "PROC-0011", True), ("C5", "PROC-0011", True)]
    schema = json.dumps(SCHEMA)
    assert not any(f'"{c}"' in schema for c in ("C1", "C2", "C3", "C4", "C5")), "the schema names no coverage rule"


def test_the_schema_holds_the_rule_id_form_and_the_cell():
    r = _report()
    bad = copy.deepcopy(r)
    bad["coverage"]["after"]["coverage-5"] = bad["coverage"]["after"]["C1"]
    assert any("does not match" in e for e in schema_check.validate(json.loads(json.dumps(bad, default=str)), SCHEMA))
    bad = copy.deepcopy(r)
    bad["coverage"]["after"]["C9"] = {"covered": 1}
    assert any("missing 'denominator'" in e for e in schema_check.validate(json.loads(json.dumps(bad, default=str)), SCHEMA))
    bad = copy.deepcopy(r)
    bad["coverage"]["after"]["C5\n"] = bad["coverage"]["after"]["C1"]   # ECMA's $ is the end: a trailing newline is no rule id
    assert any("does not match" in e for e in schema_check.validate(json.loads(json.dumps(bad, default=str)), SCHEMA))
    bad = copy.deepcopy(r)
    bad["coverage"]["new_gaps"][0]["rule"] = "D5"
    assert any("does not match" in e for e in schema_check.validate(json.loads(json.dumps(bad, default=str)), SCHEMA))


# ---- task-0130 AC1: the worked example's gaps and reach, every overlay element hypothetical

def test_the_worked_example_raises_c1_on_two_steps_c2_on_the_new_capability_and_reaches_the_new_product():
    r = _report()
    _valid(r)
    cov = r["coverage"]
    assert {c: (cov["before"][c]["covered"], cov["before"][c]["denominator"]) for c in ("C1", "C2", "C3")} == \
        {"C1": (7, 8), "C2": (5, 5), "C3": (5, 5)}
    assert {c: (cov["after"][c]["covered"], cov["after"][c]["denominator"]) for c in ("C1", "C2", "C3")} == \
        {"C1": (8, 11), "C2": (5, 6), "C3": (5, 5)}
    assert [(g["rule"], g["id"], g["hypothetical"]) for g in cov["new_gaps"]] == \
        [("C1", "JRN-0014", True), ("C1", "JRN-0015", True), ("C2", "CAP-0009", True)]
    reach = {x["node"]: x for x in r["reach"]}
    assert reach["CAP-0002"]["before"] == ["JRN-0001", "PRD-0002", "PROC-0001"]
    assert [a["id"] for a in reach["CAP-0002"]["added"]] == ["JRN-0012", "PRD-0006"]
    assert reach["PROC-0002"]["before"] == ["CAP-0004", "JRN-0001", "JRN-0002", "PRD-0002", "PROC-0001"]
    assert [a["id"] for a in reach["PROC-0002"]["added"]] == ["JRN-0012", "JRN-0013", "PRD-0006"]
    assert all(a["hypothetical"] for x in r["reach"] for a in x["added"])
    assert all(e["hypothetical"] for x in r["reach"] for e in x["new_edges"]) and reach["CAP-0002"]["new_edges"]
    assert all(x["removed"] == [] and x["changed"] is False for x in r["reach"])
    # every overlay element and edge is hypothetical, read as approved, and nothing is stored
    assert len(r["nodes"]) == 6 and len(r["links"]) == 6
    assert all(x["hypothetical"] is True and x["read_as"] == "approved" for x in r["nodes"] + r["links"])
    assert r["stored"] is False and r["register"]["tag"].startswith("v") and len(r["register"]["commit"]) == 40
    assert r["overlay"]["digest"] == pi.digest(_proposal())
    # what the new product rests on: the realisers of each required capability; CAP-0009 nothing
    rests = {x["node"]: x for x in r["rests_on"]}
    assert {v["node"]: v["realisers"] for v in rests["PRD-0006"]["via"]} == {
        "CAP-0002": ["APP-0003", "PROC-0004"], "CAP-0003": ["APP-0004", "PROC-0003"],
        "CAP-0004": ["APP-0002", "PROC-0002"], "CAP-0009": []}
    assert rests["PRD-0006"]["gap"] and rests["CAP-0009"]["gap"] and not rests["JRN-0013"]["gap"]
    # the new nodes are unmapped, never unknown; the routes per owning unit
    assert [u["id"] for u in r["unmapped"]] == ["PRD-0006", "CAP-0009", "JRN-0012", "JRN-0013", "JRN-0014", "JRN-0015"]
    assert "unknown" not in json.dumps(r["unmapped"]).replace("not unknown", "")
    units = {a["unit"]: a for a in r["approvals"]}
    assert set(units) == {"ORG-0001", "ORG-0002"}
    assert {x["id"] for x in units["ORG-0002"]["approve"] if x["what"] == "node"} == {"CAP-0009"}
    # the four requires links cross from ORG-0001 to ORG-0002: both owners approve each
    req = [ln["id"] for ln in r["links"] if ln["type"] == "requires"]
    assert all(any(x["id"] == lid and x["what"] == "link" for x in units[u]["approve"]) for lid in req for u in units)


def test_the_overlay_is_placed_by_the_registers_checker_and_a_node_in_no_tool_is_said_so():
    r = _report()
    warn = [p for p in r["placement"] if p["level"] == "warning"]
    assert [(p["check"], p["element"]) for p in warn] == [("hierarchy", "JRN-0012")]   # no journey family
    assert not [p for p in r["placement"] if p["level"] == "error"]
    assert sorted(p["element"] for p in r["placement"] if p["check"] == "source") == sorted(n["id"] for n in r["nodes"])
    bad = _proposal()
    bad["nodes"][1]["parent"] = "PRD-0001"   # a capability under a product: the register's hierarchy rule
    got = [p for p in _report(bad)["placement"] if p["level"] == "error"]
    assert {(p["check"], p["element"]) for p in got} == {("hierarchy", "CAP-0009")} and len(got) == 2


def test_provisional_ids_are_reported_as_given_and_nothing_is_minted():
    p = _proposal()
    rename = {"PRD-0006": "new-product", "CAP-0009": "credit-check", "JRN-0014": "PRD-0099"}   # the last: a wrong prefix
    s = json.dumps(p)
    for a, b in rename.items():
        s = s.replace(f'"{a}"', f'"{b}"')
    r = _report(json.loads(s))
    _valid(r)
    assert [n["id"] for n in r["nodes"]] == ["new-product", "credit-check", "JRN-0012", "JRN-0013", "PRD-0099", "JRN-0015"]
    assert sorted((g["rule"], g["id"]) for g in r["coverage"]["new_gaps"]) == [("C1", "JRN-0015"), ("C1", "PRD-0099"), ("C2", "credit-check")]
    text = json.dumps(r)
    for a in ("PRD-0006", "CAP-0009", "JRN-0016"):   # the in-memory ids never reach the report
        assert a not in text, a


def test_a_proposal_that_cannot_be_read_is_refused():
    base = _proposal()
    cases = []
    p = copy.deepcopy(base); p["nodes"][0]["id"] = "PRD-0002"; cases.append(p)            # an existing node
    p = copy.deepcopy(base); p["nodes"][0]["kind"] = "gadget"; cases.append(p)            # no such kind
    p = copy.deepcopy(base); p["links"][0]["target"] = "CAP-7777"; cases.append(p)        # a dangling end
    p = copy.deepcopy(base); p["links"][0]["type"] = "depends_on"; cases.append(p)        # no such type
    p = copy.deepcopy(base); p["reused"][0]["mode"] = "rewritten"; cases.append(p)        # no such mode
    p = copy.deepcopy(base); p["nodes"].append(dict(p["nodes"][0])); cases.append(p)     # an id twice
    p = copy.deepcopy(base); p["nodes"][0]["state"] = "approved"; cases.append(p)         # a state is the register's
    cases += [{}, {"nodes": "x"}, [], {"nodes": [], "links": []}, {"links": [], "nodes": [{"id": "x", "kind": "product"}]}]
    for bad in cases:
        try:
            pi.evaluate(bad, today=TODAY)
        except pi.ProposalError:
            continue
        raise AssertionError(f"accepted {json.dumps(bad)[:120]}")


# ---- task-0130 AC2: written as draft, the proposal changes nothing; nothing is ever written

def _as_draft_files(root: Path, proposal: dict) -> None:
    """The proposal written into a scratch copy of the register as draft files, as an author would."""
    import check_proposal_branch
    check_proposal_branch.write_as_files(root, proposal)


def test_the_same_proposal_written_as_draft_changes_nothing_in_the_registers_checker():
    root = ri.register_root()
    CR = pi.check_module(root)
    before_f, before = CR.run(root, today=TODAY)
    d = Path(tempfile.mkdtemp(prefix="kg-proposal-draft-"))
    try:
        shutil.copytree(root, d / "register", ignore=shutil.ignore_patterns("__pycache__", ".git"))
        _as_draft_files(d / "register", _proposal())
        after_f, after = pi.check_module(d / "register").run(d / "register", today=TODAY)
        assert after["nodes"] == before["nodes"] + 6 and after["links"] == before["links"] + 6
        assert {c: after[c] for c in ("C1", "C2", "C3")} == {c: before[c] for c in ("C1", "C2", "C3")}
        assert len(after_f.errors) == len(before_f.errors) == 0
        # as draft the walks never reach the new nodes: the links are listed withdrawn
        T = pi.ri.load_tools(d / "register")
        reg = T["register"].load_register(d / "register")
        edges = T["impact"].walk(reg, "PROC-0002")
        assert not {"JRN-0013", "PRD-0006"} & T["impact"].reached(edges)
        assert {e["to"] for e in edges if not e["live"]} >= {"JRN-0013"}
    finally:
        shutil.rmtree(d, ignore_errors=True)
        pi.ri.load_tools(root)   # the register's modules back in sys.modules for what follows


def test_nothing_is_written_to_the_register_or_the_store():
    root = ri.register_root()
    before = _digests(root)
    writes = []
    s, _ = _server(Stub(writes=writes))
    got = _call(s, "proposal_impact", {"proposal": _proposal(), "as_of": DAY})["result"]
    assert got["isError"] is False, got["content"][0]["text"]
    pi.main([str(FIXTURE), "--no-store", "--as-of", DAY, "-f", "json", "-o", os.devnull])
    assert _digests(root) == before and writes == []


# ---- task-0130 AC3: the reused nodes' keys read as register_impact reads them

def test_keys_on_reused_nodes_equal_register_impacts_for_the_same_node_task_and_as_of():
    from subject import SUBJECT
    from tasks import TASKS
    s, _ = _server(Stub())
    for task in sorted(TASKS):
        got = _call(s, "proposal_impact", {"proposal": _proposal(), "task": task, "as_of": DAY})["result"]["structuredContent"]
        assert got["keys"]["task"] == task and got["keys"]["scenario"] == SUBJECT.order[0] and got["as_of"] == DAY
        for entry in got["keys"]["by_node"]:
            want = _call(s, "register_impact", {"node": entry["node"], "task": task, "as_of": DAY})["result"]["structuredContent"]
            assert entry["keys"] == want["keys"], (task, entry["node"])
            assert (entry.get("gate") or None) == want["gate"], (task, entry["node"])
            assert all(k["owner"] for k in entry["keys"])
        _valid(got)
    # with no scenario held the keys carry no level; with no store at all the register still answers
    none = _call(_server(Stub(scenario=None))[0], "proposal_impact", {"proposal": _proposal()})["result"]["structuredContent"]
    assert none["keys"]["scenario"] is None and all("level" not in k for e in none["keys"]["by_node"] for k in e["keys"])
    off = mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(OSError("no store here"))))
    got = _call(off, "proposal_impact", {"proposal": _proposal()})["result"]["structuredContent"]
    assert "store_unavailable" in got["keys"] and got["coverage"]["new_gaps"]
    _valid(got)


# ---- task-0130 AC4: a read-only MCP tool

def test_proposal_impact_is_a_read_only_tool_that_refuses_a_bad_call():
    s, _ = _server()
    tool = next(t for t in mcp_server.TOOLS if t["name"] == "proposal_impact")
    assert tool["annotations"]["readOnlyHint"] is True and tool["annotations"]["destructiveHint"] is False
    assert "required" not in tool["inputSchema"] and "scope" in tool["inputSchema"]["properties"]   # a proposal, a scope or both (task-0191)
    for bad in ({}, {"proposal": {}}, {"scope": "APP-0002"}, {"scope": "NOPE-0001"}, {"proposal": {"nodes": [], "links": []}}, {"proposal": _proposal(), "task": "keys"}, {"proposal": _proposal(), "children": "yes"},
                {"proposal": _proposal(), "scenario": "S9"}, {"proposal": _proposal(), "as_of": "soon"}):
        from tests.test_mcp_server import _refused
        assert _refused(s, "proposal_impact", bad), bad


def test_children_walks_the_descendants_as_register_impact_does():
    r = _report(children=True)
    _valid(r)
    assert r["children_walked"] is True
    for x in r["reach"]:
        w = ri.walk(x["node"], "dependants", children=True)
        assert x["before"] == w["reached_ids"], x["node"]


# ---- task-0130 AC5: the command and its schema

def test_the_command_prints_the_schema_valid_report_and_refuses_with_2():
    env = {**os.environ, "KG_TODAY": DAY}
    run = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), str(FIXTURE), "--no-store", "-f", "json"],
                         capture_output=True, text=True, env=env, cwd=ROOT)
    assert run.returncode == 0, run.stderr
    rep = json.loads(run.stdout)
    _valid(rep)
    assert rep == json.loads(json.dumps(_report(), default=str))
    text = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), str(FIXTURE), "--no-store"],
                          capture_output=True, text=True, env=env, cwd=ROOT)
    assert text.returncode == 0 and "C1: 7/8 -> 8/11" in text.stdout and "hypothetical" in text.stdout
    d = Path(tempfile.mkdtemp(prefix="kg-proposal-bad-"))
    try:
        (d / "p.json").write_text('{"nodes": [{"id": "PRD-0002", "kind": "product", "name": "x", "owner": "ORG-0001"}]}', encoding="utf-8")
        bad = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), str(d / "p.json"), "--no-store"],
                             capture_output=True, text=True, env=env, cwd=ROOT)
        assert bad.returncode == 2 and bad.stdout == "" and "existing register node" in bad.stderr
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_the_schema_catches_a_report_that_drops_hypothetical_or_raises_a_candidate():
    r = json.loads(json.dumps(_report(), default=str))
    r["nodes"][0]["hypothetical"] = False
    assert schema_check.validate(r, SCHEMA)
    r = json.loads(json.dumps(_report(), default=str))
    r["candidates"][0]["status"] = "approved"
    assert schema_check.validate(r, SCHEMA)
    r = json.loads(json.dumps(_report(), default=str))
    del r["links"][0]["hypothetical"]
    assert schema_check.validate(r, SCHEMA)


def test_the_changelog_and_the_demo_readme_carry_it():
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    # the line sits in a section newer than 0.5.0: Unreleased until a release PR names it
    assert "proposal_impact" in log.split("\n## 0.5.0 ")[0].split("\n## ", 1)[1]
    readme = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    assert "proposal_impact" in readme and "tools/fixtures/proposal_contract_quote.json" in readme


# ---- task-0131: the deterministic candidates

def _cands(r, rule):
    return [c for c in r["candidates"] if c["rule"] == rule]


def test_d3_offers_jrn_0002s_support_d4_lists_a_pool_and_chooses_none_d5_is_a_placement_error():
    r = _report()
    d3 = _cands(r, "D3")
    assert [(c["kind"], c["element"], c["same_as"]) for c in d3 if c["kind"] == "same_as"] == [("same_as", "JRN-0013", "JRN-0002")]
    assert "same step as JRN-0002" in d3[0]["reason"]   # decision-0007 (a)
    assert {(c["link"]["source"], c["link"]["type"], c["link"]["target"]) for c in d3 if c["kind"] == "link"} == \
        {("JRN-0013", "is_supported_by", "PROC-0002")}
    assert all(c["basis"] == "inferred" and c["status"] == "proposed" for c in d3)
    d4 = _cands(r, "D4")
    assert [(c["element"], c["pool"]) for c in d4] == [("JRN-0014", ["PROC-0002", "PROC-0003", "PROC-0004"]),
                                                      ("JRN-0015", ["PROC-0002", "PROC-0003", "PROC-0004"])]
    assert all(c["link"] is None and c["same_as"] is None and c["basis"] == "inferred" for c in d4)
    assert {g["id"] for g in r["coverage"]["new_gaps"] if g["rule"] == "C1"} == {"JRN-0014", "JRN-0015"}   # none chosen
    p = _proposal()
    p["nodes"][4]["name"] = "Negotiate the item terms"   # "item" is a forbidden synonym of "node"
    d5 = [x for x in _report(p)["placement"] if x["rule"] == "D5"]
    assert [(x["level"], x["check"], x["element"]) for x in d5] == [("error", "glossary", "JRN-0014")]
    assert "write 'node'" in d5[0]["message"]


def test_d1_is_authored_d3_inferred_and_no_candidate_changes_coverage_until_the_link_is_stated():
    r = _report()
    d1 = _cands(r, "D1")
    assert d1 and all(c["basis"] == "authored" and c["stated"] for c in d1)
    assert {c["link"]["target"] for c in d1} == {"CAP-0002", "CAP-0003", "CAP-0004", "PROC-0002"}
    p = _proposal()
    p["links"] = [ln for ln in p["links"] if ln["type"] != "is_supported_by"]
    p["reused"] = [x for x in p["reused"] if x["id"] != "PROC-0002"]
    r2 = _report(p)
    d3 = [c for c in _cands(r2, "D3") if c["kind"] == "link"]
    assert [(c["link"]["source"], c["link"]["target"], c["stated"]) for c in d3] == [("JRN-0013", "PROC-0002", False)]
    assert sorted(g["id"] for g in r2["coverage"]["new_gaps"] if g["rule"] == "C1") == ["JRN-0013", "JRN-0014", "JRN-0015"]
    assert r2["coverage"]["after"]["C1"]["covered"] == r["coverage"]["after"]["C1"]["covered"] - 1
    assert not _cands(r2, "D4") or "JRN-0013" not in [c["element"] for c in _cands(r2, "D4")]   # D3 matched it
    assert all(c["status"] == "proposed" for c in r["candidates"] + r2["candidates"])


def test_d2_matches_an_external_id_through_the_landed_synthetic_aris_export():
    """D2 on the synthetic ARIS export the connector lands in a temporary example instance, never a
    real export: a proposed node carrying the GUID of PROC-0002's ARIS object is that node."""
    import tomllib

    from tests import test_connector
    s = test_connector._landed()
    reg = s["dir"] / "register"
    newest = sorted(p for p in (reg / "exports" / "aris").iterdir() if p.is_dir())[-1]
    guids = tomllib.loads((newest / "MANIFEST.toml").read_text(encoding="utf-8"))["register_ids"]   # decision-0010
    guid = next(g for g, rid in sorted(guids.items()) if rid == "PROC-0002")
    p = _proposal()
    p["nodes"].append({"id": "PROC-new", "kind": "subprocess", "name": "Validate a contract request", "parent": "PROC-0001",
                       "owner": "ORG-0001", "source": {"system": "aris", "aris_guid": guid}})
    before = _digests(reg)
    try:
        r = pi.evaluate(p, root=reg, today=TODAY)
    finally:
        pi.ri.load_tools(ri.register_root())
    assert _digests(reg) == before
    _valid(r)
    d2 = _cands(r, "D2")
    assert [(c["element"], c["same_as"], c["basis"]) for c in d2] == [("PROC-new", "PROC-0002", "authored")]
    assert f"exports/aris/{newest.name}/MANIFEST.toml [register_ids]" in d2[0]["reason"]
    assert "PROC-new" not in [x["element"] for x in r["placement"] if x["check"] == "source"]   # it names a tool
    # without a landed export, the public register carries no GUID: no D2
    assert not _cands(_report(p), "D2")


# ---- task-0132: branch mode, the overlay from a register branch's diff against a base ref

def test_branch_mode_equals_the_held_overlay_ids_aside_and_leaves_the_checkout_as_it_was():
    """AC1 and AC2: tools/check_proposal_branch.py, the CI template's step on a scratch branch of the
    vendored register, as harness.yml runs it."""
    import check_proposal_branch
    try:
        assert check_proposal_branch.main([]) == 0
    finally:
        pi.ri.load_tools(ri.register_root())


def test_branch_mode_reads_a_path_with_a_space_or_a_non_ascii_character_as_itself():
    """task-0267: the branch's changed paths come NUL-separated from git, so a register file under a name git would
    quote (a non-ASCII character) or a space is listed as itself; before, its quoted form ("exceptions/... with octal
    escapes) matched no taxonomy and it was dropped from not_read unseen."""
    import check_proposal_branch as cpb
    top = Path(tempfile.mkdtemp(prefix="kg-proposal-branch-test-"))
    try:
        reg = cpb.scratch_branch(top, _proposal())
        odd = reg / "exceptions" / "borradores de diseño" / "excepción.toml"
        odd.parent.mkdir()
        odd.write_text('id = "EXC-9999"\n', encoding="utf-8")
        cpb.git(reg, "add", "-A")
        cpb.git(reg, "commit", "-qm", "a nested draft")
        r = pi.evaluate_branch(reg, "main", today=TODAY)
        _valid(r)
        assert [(x["path"], x["status"]) for x in r["branch"]["not_read"]] == \
            [("exceptions/borradores de diseño/excepción.toml", "A")], r["branch"]["not_read"]
    finally:
        shutil.rmtree(top, ignore_errors=True)


def test_the_ci_step_on_a_branch_that_adds_nothing_exits_0_with_a_report_naming_not_read():
    """task-0267 (F17): the step is advisory, 0 with a report, 2 only when it cannot run; a register branch that only
    removes a link adds no node and no link, so it was exit 2. Now its report names what it changes in not_read."""
    import check_proposal_branch as cpb
    top = Path(tempfile.mkdtemp(prefix="kg-proposal-branch-test-"))
    try:
        reg = cpb.scratch_branch(top, _proposal())
        cpb.git(reg, "reset", "-q", "--hard", "main")   # the proposal branch back at main: it adds nothing
        rel = reg / "relationships" / "realizes.toml"
        text = rel.read_text(encoding="utf-8")
        first = text.index("[[link]]")
        rel.write_text(text[:first] + text[text.index("[[link]]", first + 1):], encoding="utf-8")
        cpb.git(reg, "commit", "-qam", "a link removed")
        out = top / "report.json"
        p = subprocess.run(["sh", str(ROOT / "instance" / "ci" / "proposal-impact.sh"), str(ROOT), str(reg), "main"], capture_output=True,
                           text=True, env={**os.environ, "KG_AS_OF": DAY, "KG_PROPOSAL_REPORT": str(out)})
        assert p.returncode == 0, p.stderr[-800:]
        r = json.loads(out.read_text(encoding="utf-8"))
        _valid(r)
        assert (r["nodes"], r["links"], r["coverage"]["new_gaps"]) == ([], [], [])
        assert [(x["path"].split(" ")[0], x["status"]) for x in r["branch"]["not_read"]] == [("relationships/realizes.toml", "D")]
        assert "--end-of-options" not in p.stderr
        bad = subprocess.run(["sh", str(ROOT / "instance" / "ci" / "proposal-impact.sh"), str(ROOT), str(reg), f"--output={top}/x"],
                             capture_output=True, text=True, env={**os.environ, "KG_AS_OF": DAY})
        assert bad.returncode == 2 and not (top / "x").exists(), bad.stderr[-400:]
    finally:
        shutil.rmtree(top, ignore_errors=True)


def test_branch_mode_reads_a_changed_node_as_changed_and_lists_what_is_not_an_addition():
    import check_proposal_branch as cpb
    top = Path(tempfile.mkdtemp(prefix="kg-proposal-branch-test-"))
    try:
        reg = cpb.scratch_branch(top, _proposal())
        p = reg / "capabilities" / "CAP-0002.toml"
        p.write_text(p.read_text(encoding="utf-8").replace('name = "Price a shipment"', 'name = "Price a shipment or a contract"'), encoding="utf-8")
        rel = reg / "relationships" / "realizes.toml"
        text = rel.read_text(encoding="utf-8")
        first = text.index("[[link]]")
        rel.write_text(text[:first] + text[text.index("[[link]]", first + 1):], encoding="utf-8")   # one link removed
        (reg / "notes.md").write_text("not a register file\n", encoding="utf-8")
        cpb.git(reg, "add", "-A")
        cpb.git(reg, "commit", "-qm", "a change and a removal")
        before = _digests(reg)
        r = pi.evaluate_branch(reg, "main", today=TODAY)
        _valid(r)
        assert _digests(reg) == before
        reach = {x["node"]: x for x in r["reach"]}
        assert reach["CAP-0002"]["mode"] == "changed" and reach["CAP-0002"]["changed"] is True
        assert any(a["what"] == "change" and a["id"] == "CAP-0002" for u in r["approvals"] for a in u["approve"])
        assert [(x["path"].split(" ")[0], x["status"]) for x in r["branch"]["not_read"]] == [("relationships/realizes.toml", "D")]
        assert r["branch"]["base"] == "main" and len(r["branch"]["head"]) == 40 and r["register"]["commit"] == r["branch"]["merge_base"]
        assert r["register"]["tag"].startswith("v")   # the vendored copy's SOURCE.md
        for bad in (("main~5",), ("no-such-ref",)):
            try:
                pi.evaluate_branch(reg, bad[0], today=TODAY)
            except pi.ProposalError:
                continue
            raise AssertionError(bad)
        try:
            pi.evaluate_branch(top, "main", today=TODAY)
        except pi.ProposalError as e:
            assert "not a register checkout" in str(e)
        else:
            raise AssertionError("a directory that is not a register was read")
        env = {**os.environ, "KG_TODAY": DAY}
        cli = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), "--register-branch", str(reg)],
                             capture_output=True, text=True, env=env, cwd=ROOT)
        assert cli.returncode == 2 and "--base" in cli.stderr
    finally:
        shutil.rmtree(top, ignore_errors=True)
        pi.ri.load_tools(ri.register_root())


def test_the_ci_step_is_in_the_template_proven_in_harness_yml_and_documented():
    step = (ROOT / "instance" / "ci" / "proposal-impact.sh").read_text(encoding="utf-8")
    assert "--register-branch" in step and "--no-store" in step
    wf = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert "python tools/check_proposal_branch.py" in wf
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    assert "proposal-impact.sh" in readme and "--register-branch" in readme


# ---- task-0152 (doc-0022 K1): the slice map, by the register's thread walk

PLANNING_WORDS = ("skeleton", "mvp", "priority", "rank", "estimate", "first", "later", "sprint", "story point")


def _placed(sl: dict) -> list[str]:
    return [e["id"] for s in sl["map"] for e in s["elements"]] + [e["id"] for g in sl["remainder"] for e in g["elements"]]


def _group(sl: dict, name: str) -> dict:
    return next(g for g in sl["remainder"] if g["group"] == name)


def test_the_worked_example_is_three_step_slices_and_the_required_capabilities_no_step_reaches():
    """AC1, AC2, AC4: doc-0022 §2's map, computed: JRN-0013 rests on reused PROC-0002's thread,
    JRN-0014 and JRN-0015 have none, and CAP-0002, CAP-0003 and the new CAP-0009 are required by
    PRD-0006 and reached by no step (A1)."""
    r = _report()
    _valid(r)
    sl = r["slices"]
    assert (sl["walk"], sl["register_rule"], sl["children"]) == ("thread", "A1", True)
    assert [p["id"] for p in sl["products"]] == ["PRD-0006"]
    p = sl["products"][0]
    assert (p["status"], p["axis"], p["journeys"], p["slices"]) == ("new", "step", ["JRN-0012"], ["JRN-0013", "JRN-0014", "JRN-0015"])
    assert p["required_not_reached"] == ["CAP-0002", "CAP-0003", "CAP-0009"] and p["reached"] == ["CAP-0004"]
    by = {s["start"]["id"]: s for s in sl["map"]}
    t = by["JRN-0013"]["thread"]
    assert [c["id"] for c in t["process"]] == ["PROC-0002"] and [c["id"] for c in t["capability"]] == ["CAP-0004"]
    assert [c["id"] for c in t["application"]] == ["APP-0002"] and [c["id"] for c in t["information"]] == ["ENT-0002", "ENT-0003"]
    assert by["JRN-0013"]["start"]["status"] == "new" and {c["status"] for v in t.values() for c in v} == {"reused"}
    assert by["JRN-0013"]["empty"] == [] and by["JRN-0013"]["owners"] == ["ORG-0001", "ORG-0002"]
    assert [e["id"] for e in by["JRN-0013"]["elements"]] == ["JRN-0013", "link-6"]
    for s in ("JRN-0014", "JRN-0015"):
        assert by[s]["empty"] == ["process", "capability", "application", "information"]
        assert [e["id"] for e in by[s]["elements"]] == [s]
    rnr = _group(sl, "required_not_reached")
    assert [c["capability"]["id"] for c in rnr["capabilities"]] == ["CAP-0002", "CAP-0003", "CAP-0009"]
    assert {c["capability"]["id"]: [x["id"] for x in c["realisers"]] for c in rnr["capabilities"]} == {
        "CAP-0002": ["APP-0003", "PROC-0004"], "CAP-0003": ["APP-0004", "PROC-0003"], "CAP-0009": []}
    assert [e["id"] for e in rnr["elements"]] == ["CAP-0009", "link-1", "link-2", "link-4"]
    assert [e["id"] for e in _group(sl, "frame")["elements"]] == ["PRD-0006", "JRN-0012", "link-3", "link-5"]
    for g in ("shared", "exceptions", "outside"):
        assert _group(sl, g)["elements"] == []
    # every overlay element exactly once, the denominator shown
    placed = _placed(sl)
    want = [n["id"] for n in r["nodes"]] + [ln["id"] for ln in r["links"]] + [e["id"] for e in r["exceptions"]]
    assert sorted(placed) == sorted(want) and len(set(placed)) == len(placed)
    assert sl["elements"] == {"denominator": 12, "in_slices": 4, "in_remainder": 8}


def test_on_the_approved_register_prd_0002s_cap_0003_is_reached_by_no_step_and_prd_0005_is_sliced_by_its_process():
    """AC4: a two-entity overlay on the approved register touches PRD-0002 (through PROC-0003, which
    realises CAP-0003 and supports no step) and the daily chain (PROC-0007, on JRN-0006's thread and on
    PROC-0006's, the process that delivers PRD-0005, which no journey concerns)."""
    proposal = {"title": "approved register probe (synthetic)",
                "nodes": [{"id": "ENT-0020", "kind": "business_entity", "name": "Screening record", "owner": "ORG-0001"},
                          {"id": "ENT-0021", "kind": "business_entity", "name": "Sync ledger", "owner": "ORG-0003"}],
                "links": [{"type": "crud", "source": "PROC-0003", "target": "ENT-0020", "rationale": "screening writes it"},
                          {"type": "crud", "source": "PROC-0007", "target": "ENT-0021", "rationale": "the sync run writes it"}],
                "exceptions": [{"rule": "C1", "scope": ["ENT-0020"], "expires": "2027-01-01", "rationale": "probe"}]}
    r = _report(proposal)
    _valid(r)
    sl = r["slices"]
    prods = {p["id"]: p for p in sl["products"]}
    assert sorted(prods) == ["PRD-0002", "PRD-0004", "PRD-0005"]
    assert prods["PRD-0002"]["slices"] == ["JRN-0002", "JRN-0003"] and prods["PRD-0002"]["required_not_reached"] == ["CAP-0003"]
    assert prods["PRD-0002"]["alignment_by"] == "A1"
    assert prods["PRD-0004"]["reached_not_required"] == ["CAP-0008"] and prods["PRD-0004"]["not_walked"] == ["JRN-0008"]
    p5 = prods["PRD-0005"]
    assert (p5["axis"], p5["journeys"], p5["processes"], p5["slices"]) == ("process", [], ["PROC-0006"], ["PROC-0006"])
    assert p5["required_not_reached"] == [] and p5["reached"] == ["CAP-0007", "CAP-0008"]
    by = {s["start"]["id"]: s for s in sl["map"]}
    assert by["PROC-0006"]["axis"] == "process" and "process" not in by["PROC-0006"]["empty"]
    assert [c["id"] for c in by["PROC-0006"]["descendants"]] == ["PROC-0007", "PROC-0009", "PROC-0008"]
    assert [c["id"] for c in by["JRN-0002"]["descendants"]] == ["JRN-0004"]   # the touchpoint rides its step
    assert by["JRN-0009"]["empty"] == ["capability"]   # PROC-0006 realises nothing itself: as fine as the links
    assert {"rel": "is_supported_by", "from": "JRN-0003", "to": "PROC-0005", "state": "proposed"} in by["JRN-0003"]["not_followed"]
    assert "ENT-0021" in [c["id"] for c in by["JRN-0006"]["thread"]["information"]]
    shared = _group(sl, "shared")["elements"]
    assert shared == [{"id": "ENT-0021", "element": "node", "slices": ["JRN-0006", "PROC-0006"]},
                      {"id": "link-2", "element": "link", "slices": ["JRN-0006", "PROC-0006"]}]
    rnr = _group(sl, "required_not_reached")
    assert [c["capability"]["id"] for c in rnr["capabilities"]] == ["CAP-0003"]
    assert [c["required_by"] for c in rnr["capabilities"]] == [["PRD-0002"]]
    assert [e["id"] for e in rnr["elements"]] == ["ENT-0020", "link-1"]
    assert [e["id"] for e in _group(sl, "exceptions")["elements"]] == ["exception-1"]
    assert sl["elements"] == {"denominator": 5, "in_slices": 0, "in_remainder": 5}
    assert sorted(_placed(sl)) == sorted(["ENT-0020", "ENT-0021", "link-1", "link-2", "exception-1"])


def test_an_overlay_no_product_touches_is_placed_outside_and_the_map_is_facts_only():
    """AC2, AC3: an element on no product's footprint is in the named remainder outside; the section
    carries no planning label, estimate or rank."""
    proposal = {"nodes": [{"id": "ORG-0020", "kind": "team", "name": "Contract desk", "parent": "ORG-0001", "owner": "ORG-0001"}]}
    r = _report(proposal)
    _valid(r)
    sl = r["slices"]
    assert sl["products"] == [] and sl["map"] == []
    assert [e["id"] for e in _group(sl, "outside")["elements"]] == ["ORG-0020"]
    assert sl["elements"] == {"denominator": 1, "in_slices": 0, "in_remainder": 1}
    for rep in (r, _report()):
        text = json.dumps(rep["slices"]).casefold()
        assert not [w for w in PLANNING_WORDS if w in text], [w for w in PLANNING_WORDS if w in text]
    for s in _report()["slices"]["map"]:
        assert set(s) == {"start", "axis", "products", "descendants", "thread", "empty", "not_followed", "owners", "elements",
                          "handoffs", "keys"}   # task-0191: each slice's owner handoffs and keys


def test_the_command_and_the_mcp_tool_give_the_same_slice_map():
    env = {**os.environ, "KG_TODAY": DAY}
    run = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), str(FIXTURE), "--no-store", "-f", "json"],
                         capture_output=True, text=True, env=env, cwd=ROOT)
    assert run.returncode == 0, run.stderr
    s, _ = _server(Stub(scenario=None))   # no scenario held: the slices' keys carry no level, as --no-store's (task-0191)
    got = _call(s, "proposal_impact", {"proposal": _proposal(), "as_of": DAY})["result"]
    assert got.get("isError") is not True, got
    mcp = got["structuredContent"]
    assert mcp["slices"] == json.loads(run.stdout)["slices"] == json.loads(json.dumps(_report()["slices"]))
    text = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), str(FIXTURE), "--no-store"],
                          capture_output=True, text=True, env=env, cwd=ROOT).stdout
    assert "slice JRN-0013 (new step): process PROC-0002" in text
    assert "slices: 4 in slices, 8 in the remainder, of 12 overlay element(s)" in text


# ---- task-0156 (doc-0022 K5): the intake sequence in the server's instructions

def test_the_instructions_name_the_intake_sequence_on_both_transports_and_every_tool_they_name_exists():
    import re

    from tests.test_mcp_server import MODERN, _modern, _post_raw, _serve
    text = mcp_server.INSTRUCTIONS
    intake = text.index("Intake, from a proposed initiative")
    seq = [text.index(t, intake) for t in ("proposal_impact proposal=", "slices", "gate_verdict keys=", "one task class and one as_of")]
    assert seq == sorted(seq) and text.index("Up, from a code file") < intake
    rest = text[intake:]
    for said in ("knowgov writes no work item and ranks nothing", "the tracker writes the items",
                 "(K3) is parked to the pilot, not offered"):
        assert said in rest, said
    tools = {t["name"] for t in mcp_server.TOOLS}
    named = set(re.findall(r"\b([a-z]+(?:_[a-z]+)+) [a-z]+=", text[text.index("The chain composes"):]))
    assert {"proposal_impact", "gate_verdict", "register_impact", "evidence_bundle", "register_nodes"} <= named
    assert named <= tools, named - tools
    # the same text over stdio's handler, in both eras, and over Streamable HTTP
    s, _ = _server()
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}}
    assert s.handle(init)["result"]["instructions"] == text
    assert s.handle(_modern("server/discover"))["result"]["instructions"] == text
    httpd, base = _serve()
    try:
        code, body = _post_raw(base + "/mcp", _modern("server/discover"), {"MCP-Protocol-Version": MODERN, "Mcp-Method": "server/discover"})
        assert code == 200 and body["result"]["instructions"] == text
        code, body = _post_raw(base + "/mcp", init, {})
        assert code == 200 and body["result"]["instructions"] == text
    finally:
        httpd.shutdown()
        httpd.server_close()


# ---- task-0191 (doc-0024 J1): a named journey or product on the approved register, keys per slice

CARGO_MAP = __import__("tomllib").loads((ROOT / "subjects" / "cargo_quote" / "register_map.toml").read_text(encoding="utf-8"))
JF_MAP = __import__("tomllib").loads((ROOT / "subjects" / "jef_data_load" / "register_map.toml").read_text(encoding="utf-8"))
# CargoQuote's class table beside its map (task-0252): the slices read a class's keys from the same subject
# as the map, so a test reading CARGO_MAP passes these, whichever subject KG_SUBJECT names for the process
CARGO_TASKS = __import__("tomllib").loads((ROOT / "subjects" / "cargo_quote" / "subject.toml").read_text(encoding="utf-8"))["tasks"]


def _thread(start: str) -> dict:
    """The register's own THREAD walk with parent descent from ``start``, read here apart from the evaluator."""
    root = ri.register_root().resolve()
    T = ri.load_tools(root)
    reg = T["register"].load_register(root)
    return T["impact"].walk_children(reg, start, T["impact"].THREAD)


def test_a_named_journey_or_product_with_no_overlay_gives_its_slices_on_the_approved_register():
    """AC1: no overlay, a scope; the slices are the register's THREAD walk from each approved step under it."""
    for scope in ("JRN-0001", "PRD-0002"):
        r = pi.evaluate(None, today=TODAY, scope=scope, register_map=CARGO_MAP, tasks=CARGO_TASKS)
        _valid(r)
        sl = r["slices"]
        assert sl["scope"]["id"] == scope and r["overlay"]["nodes"] == r["overlay"]["links"] == 0
        assert [s["start"]["id"] for s in sl["map"]] == ["JRN-0002", "JRN-0003"]
        assert [p["id"] for p in sl["products"]] == ["PRD-0002"] and sl["products"][0]["required_not_reached"] == ["CAP-0003"]
        assert sl["elements"] == {"denominator": 0, "in_slices": 0, "in_remainder": 0}
        for s in sl["map"]:
            t = _thread(s["start"]["id"])
            on = {c["id"] for layer in s["thread"].values() for c in layer}
            assert on == {x for x in t["reached"] if not x.startswith("JRN-")}, s["start"]["id"]
            assert [c["id"] for c in s["descendants"]] == [d["id"] for d in t["descendants"] if d["live"]]
    one = pi.evaluate(None, today=TODAY, scope="JRN-0002", register_map=CARGO_MAP, tasks=CARGO_TASKS)["slices"]
    assert [s["start"]["id"] for s in one["map"]] == ["JRN-0002"] and one["scope"]["kind"] == "step"
    jf = pi.evaluate(None, today=TODAY, scope="JRN-0005", register_map=JF_MAP, task=None)["slices"]
    assert [s["start"]["id"] for s in jf["map"]] == ["JRN-0006", "JRN-0007", "JRN-0009", "JRN-0010", "JRN-0011"]
    # with an overlay, a scope narrows the slices to its own; the overlay's elements are placed as before
    both = _report(scope="PRD-0002")
    _valid(both)
    assert {p["id"] for p in both["slices"]["products"]} == {"PRD-0002"}
    for bad in ("APP-0002", "NOPE-0001", "PROC-0005", 7):   # an application, nothing, a node not approved, not an id
        try:
            pi.evaluate(None, today=TODAY, scope=bad)
        except pi.ProposalError as e:
            assert "scope" in str(e), e
        else:
            raise AssertionError(f"scope {bad!r} accepted")
    try:
        pi.evaluate({"nodes": [], "links": []}, today=TODAY)
    except pi.ProposalError as e:
        assert "name a scope" in str(e)
    else:
        raise AssertionError("an empty overlay with no scope accepted")


def test_each_slice_lists_the_keys_register_impact_lands_on_its_nodes_with_the_denominator():
    """AC2 (rows), AC3: the rows are register_impact.landed_rows for the slice's start, walked descendants and
    reached nodes; JRN-0002 lands 22 of CargoQuote's 36 (doc-0024's measure), JRN-0003 the four rows on
    PROC-0005 behind its proposed edge, one of them landed no other way."""
    r = pi.evaluate(None, today=TODAY, scope="JRN-0001", register_map=CARGO_MAP, tasks=CARGO_TASKS)
    by = {s["start"]["id"]: s for s in r["slices"]["map"]}
    for sid, s in by.items():
        t = _thread(sid)
        want = ri.landed_rows(CARGO_MAP, sid, sorted(t["reached"]), [d["id"] for d in t["descendants"] if d["live"]],
                              [d["id"] for d in t["descendants"] if not d["live"]])
        assert s["keys"]["rows"] == want, sid
        assert s["keys"]["of"] == 36 and s["keys"]["gate"] is None
        c = s["keys"]["cells"]
        assert c["read"] is False and c["levels"] == {} and c["worst"] is None and len(c["unread"]) == s["keys"]["landed"]
    assert (by["JRN-0002"]["keys"]["landed"], by["JRN-0002"]["keys"]["of"]) == (22, 36)
    behind = by["JRN-0003"]["keys"]["behind_not_followed"]
    assert [(b["from"], b["to"], b["state"]) for b in behind] == [("JRN-0003", "PROC-0005", "proposed")]
    assert len(behind[0]["keys"]) == 4 and behind[0]["only_behind"] == ["QuoteAPI|on_notification_failure"]
    assert all(h["owners"][0] != h["owners"][1] for s in by.values() for h in s["handoffs"])
    assert by["JRN-0002"]["handoffs"] and '"score"' not in json.dumps(r["slices"]).casefold()   # facts only: no score field
    jf = {s["start"]["id"]: s["keys"] for s in pi.evaluate(None, today=TODAY, scope="JRN-0005", register_map=JF_MAP, task=None)["slices"]["map"]}
    assert {k: (v["landed"], v["of"]) for k, v in jf.items()} == \
        {"JRN-0006": (65, 163), "JRN-0007": (66, 163), "JRN-0009": (100, 163), "JRN-0010": (100, 163), "JRN-0011": (100, 163)}


def test_with_a_scenario_held_each_slice_reads_its_levels_as_register_impact_does():
    """AC2 (levels), AC3: over MCP, each slice's rows are register_impact's with_levels over the gate's report on
    the slice's keys, under the task class and as_of named; the cells count what the rows read, unknown is
    the keys at absent, and a key with no statement is never read as anything better."""
    from subject import SUBJECT
    from tasks import TASKS
    import gate_cli  # noqa: F401  (the gate the levels come from)
    s, _ = _server(Stub())
    scope = next((n for n in ("JRN-0001", "JRN-0005") if n in json.dumps(SUBJECT.register_map(), default=str)), "JRN-0001")
    for task in sorted(TASKS):
        got = _call(s, "proposal_impact", {"scope": scope, "task": task, "as_of": DAY})["result"]
        assert got.get("isError") is not True, got
        rep = got["structuredContent"]
        _valid(rep)
        assert rep["keys"]["task"] == task and rep["keys"]["scenario"] == SUBJECT.order[0]
        for sl in rep["slices"]["map"]:
            k = sl["keys"]
            if not k["rows"]:
                continue
            keys = list(dict.fromkeys(r["key"] for r in k["rows"]))
            gate = _call(s, "gate_verdict", {"keys": keys, "task": task, "as_of": DAY})["result"]["structuredContent"]
            bare = [{x: v for x, v in r.items() if x not in ("level", "stale", "suspect", "findings")} for r in k["rows"]]
            assert k["rows"] == ri.with_levels(bare, gate), (task, sl["start"]["id"])
            assert k["gate"]["verdict"] == gate["verdict"]
            c = k["cells"]
            assert c["read"] is True and sum(c["levels"].values()) == k["landed"] and c["unread"] == []
            assert c["unknown"] == sorted({r["key"] for r in k["rows"] if r["level"] == "absent" and not r.get("not_followed")})
            if c["levels"]:
                from gate import ORDER
                assert c["worst"] == min(c["levels"], key=ORDER.index)


def test_the_command_and_the_mcp_tool_take_the_scope_alone_and_agree():
    """AC4: --scope on the command, scope on the MCP tool, the same slices; the changelog's contract line."""
    env = {**os.environ, "KG_TODAY": DAY}
    run = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), "--scope", "JRN-0001", "--no-store", "-f", "json"],
                         capture_output=True, text=True, env=env, cwd=ROOT)
    assert run.returncode == 0, run.stderr
    cli = json.loads(run.stdout)
    _valid(cli)
    s, _ = _server(Stub(scenario=None))
    mcp = _call(s, "proposal_impact", {"scope": "JRN-0001", "as_of": DAY})["result"]["structuredContent"]
    assert mcp["slices"] == cli["slices"] and cli["slices"]["scope"]["id"] == "JRN-0001"
    text = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), "--scope", "JRN-0001", "--no-store"],
                          capture_output=True, text=True, env=env, cwd=ROOT).stdout
    assert text.startswith("scope JRN-0001 (journey") and "read as it is: no overlay" in text and "keys " in text
    bad = subprocess.run([sys.executable, str(ROOT / "harness" / "proposal_impact.py"), "--no-store"], capture_output=True, text=True, env=env, cwd=ROOT)
    assert bad.returncode == 2 and "--scope" in bad.stderr
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0191" in contract and "scope" in contract


# ---- task-0252 (doc-0034 D1): a slice reads its task class's keys; the class's keys on no slice are named

def test_under_a_task_class_each_slice_reads_only_its_keys_and_the_rest_are_on_no_slice():
    """AC1, AC2: under design, a slice's rows are the class's keys among the rows on its thread; every one of
    the class's 36 keys is in a slice or in task_keys, never both; REQ-06|text, which no register-map row
    names, is on no slice, mapped false. The denominator is the class's key count."""
    want = CARGO_TASKS["design"]["keys"]
    r = pi.evaluate(None, today=TODAY, scope="JRN-0001", register_map=CARGO_MAP, tasks=CARGO_TASKS, task="design")
    _valid(r)
    on = set()
    for s in r["slices"]["map"]:
        k = s["keys"]
        assert k["task"] == "design" and k["of"] == len(want)
        assert {x["key"] for x in k["rows"]} <= set(want), s["start"]["id"]
        assert all(set(b["keys"]) <= set(want) for b in k["behind_not_followed"])
        on |= {x["key"] for x in k["rows"] if not x.get("not_followed")}
    tk = r["slices"]["task_keys"]
    off = [x["key"] for x in tk["keys"]]
    assert tk["task"] == "design" and tk["group"] == "on_no_slice" and tk["denominator"] == len(want) == 36
    assert not on & set(off) and on | set(off) == set(want)
    assert (tk["in_slices"], tk["on_no_slice"]) == (len(on), len(off)) and tk["in_slices"] + tk["on_no_slice"] == 36
    req6 = next(x for x in tk["keys"] if x["key"] == "REQ-06|text")
    assert req6["mapped"] is False and req6["owner"] is None and req6["nodes"] == [] and req6["via"] == []
    assert "response|hold_presence" not in on   # a codegen key design does not require is on no design slice
    by = {s["start"]["id"]: s["keys"]["landed"] for s in r["slices"]["map"]}
    assert by == {"JRN-0002": 8, "JRN-0003": 9}


def test_under_codegen_the_slices_verdicts_and_counts_do_not_move():
    """AC3: codegen's keys are CargoQuote's whole map, so the slices under codegen are the slices read with no
    class but for the class named; task-0191's equality with register_impact's landed_rows holds."""
    plain = pi.evaluate(None, today=TODAY, scope="JRN-0001", register_map=CARGO_MAP, tasks=CARGO_TASKS, task=None)["slices"]
    cg = pi.evaluate(None, today=TODAY, scope="JRN-0001", register_map=CARGO_MAP, tasks=CARGO_TASKS, task="codegen")["slices"]
    assert plain["task_keys"]["task"] is None and cg["task_keys"]["task"] == "codegen"
    for a, b in zip(plain["map"], cg["map"], strict=True):
        assert a["keys"]["task"] is None and b["keys"]["task"] == "codegen"
        assert {**a["keys"], "task": "codegen"} == b["keys"] and {**a, "keys": None} == {**b, "keys": None}
        t = _thread(b["start"]["id"])
        assert b["keys"]["rows"] == ri.landed_rows(CARGO_MAP, b["start"]["id"], sorted(t["reached"]),
                                                   [d["id"] for d in t["descendants"] if d["live"]],
                                                   [d["id"] for d in t["descendants"] if not d["live"]])
    assert {s["start"]["id"]: (s["keys"]["landed"], s["keys"]["of"]) for s in cg["map"]} == {"JRN-0002": (22, 36), "JRN-0003": (22, 36)}
    assert [x["key"] for x in cg["task_keys"]["keys"]] == ["S-accept|max", "S-review|min", "S-review|max", "S-refuse|min"]
    assert {k: v for k, v in cg["task_keys"].items() if k != "task"} == {k: v for k, v in plain["task_keys"].items() if k != "task"}


def test_with_a_scenario_held_a_design_slice_reads_the_design_gates_levels_and_its_rest_too():
    """AC1: over MCP with a scenario held, a design slice's rows and the keys on no slice are at the levels the
    subject's design gate reads them, each slice's verdict gate_verdict's on its keys; REQ-06|text, with no
    statement in the store, reads absent on no slice. The server reads the process's subject, so this is
    CargoQuote's run only (the class, the keys and the scope are CargoQuote's)."""
    from subject import SUBJECT
    from tasks import TASKS
    from tests._skip import skip
    if SUBJECT.id != "cargo_quote":
        skip("the cargo_quote subject", f"CargoQuote's design class and REQ-06|text, read by a server on {SUBJECT.id}")
    s, _ = _server(Stub())
    rep = _call(s, "proposal_impact", {"scope": "JRN-0001", "task": "design", "as_of": DAY})["result"]["structuredContent"]
    _valid(rep)
    whole = _call(s, "gate_verdict", {"task": "design", "as_of": DAY})["result"]["structuredContent"]
    for sl in rep["slices"]["map"]:
        k = sl["keys"]
        assert all(x["level"] == whole["levels"][x["key"]] for x in k["rows"]), sl["start"]["id"]
        keys = list(dict.fromkeys(x["key"] for x in k["rows"]))
        one = _call(s, "gate_verdict", {"task": "design", "keys": keys, "as_of": DAY})["result"]["structuredContent"]
        assert k["gate"]["verdict"] == one["verdict"] and k["gate"]["task"] == "design"
    tk = rep["slices"]["task_keys"]
    assert all(x["level"] == whole["levels"][x["key"]] for x in tk["keys"])
    assert next(x for x in tk["keys"] if x["key"] == "REQ-06|text")["level"] == "absent"
    assert tk["gate"]["task"] == "design" and tk["cells"]["read"] is True and "REQ-06|text" in tk["cells"]["unknown"]
    assert len(TASKS["design"]["keys"]) == tk["denominator"]
    try:   # a report read under one class is never levelled under another
        pi.with_levels(pi.evaluate(None, today=TODAY, scope="JRN-0001", register_map=CARGO_MAP, tasks=CARGO_TASKS, task="design"),
                       mcp_server.ReadOnlyStore(Stub()), task="codegen", as_of=DAY)
    except pi.ProposalError as e:
        assert "design" in str(e)
    else:
        raise AssertionError("a design report levelled under codegen")
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    assert "task-0252" in log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
