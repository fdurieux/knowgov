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
    assert tool["inputSchema"]["required"] == ["proposal"]
    for bad in ({}, {"proposal": {}}, {"proposal": _proposal(), "task": "keys"}, {"proposal": _proposal(), "children": "yes"},
                {"proposal": _proposal(), "scenario": "S9"}, {"proposal": _proposal(), "as_of": "soon"}):
        r = _call(s, "proposal_impact", bad)["result"]
        assert r["isError"] is True, bad


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
    top = log.split("\n## ", 2)[1]
    assert top.startswith("Unreleased") and "proposal_impact" in top
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
    guids = tomllib.loads((newest / "MANIFEST.toml").read_text(encoding="utf-8"))["guids"]
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
    assert f"exports/aris/{newest.name}/MANIFEST.toml" in d2[0]["reason"]
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
