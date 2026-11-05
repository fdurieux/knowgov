"""Task-0142 (doc-0020 C1): the register listed and filtered, and one node's lineage, over MCP and as
a command; the register's own loader, no store. On the vendored register: the 8 capabilities, CAP-0002
under CAP-0001, PROC-0009 two levels down; lineage an annotation, never a walk."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import mcp_server  # noqa: E402
import register_impact as ri  # noqa: E402
import register_nodes as rn  # noqa: E402
import schema_check  # noqa: E402

SCHEMA = schema_check.load("register-nodes")


def _no_store():
    raise AssertionError("register_nodes opened the store")


def _server():
    return mcp_server.Server(mcp_server.Tools(opener=_no_store))


def _call(s, args):
    r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "register_nodes", "arguments": args}})
    return r["result"]


def _ok(s, args):
    r = _call(s, args)
    assert r["isError"] is False, r["content"][0]["text"]
    got = r["structuredContent"]
    assert schema_check.validate(got, SCHEMA) == [], schema_check.validate(got, SCHEMA)
    return got


def _reg():
    return ri.load_tools()["register"].load_register(ri.register_root())


def test_the_listing_holds_every_node_sorted_with_the_total_and_opens_no_store():
    s, reg = _server(), _reg()
    got = _ok(s, {"limit": 1000})
    assert got["total"] == len(reg["nodes"]) == len(got["nodes"]) and got["truncated"] is False
    assert [n["id"] for n in got["nodes"]] == sorted(reg["nodes"])
    assert got["register"]["tag"].startswith("v") and len(got["register"]["commit"]) == 40 and got["lineage"] is None
    page = _ok(s, {"limit": 5, "offset": 5})
    assert page["total"] == got["total"] and [n["id"] for n in page["nodes"]] == sorted(reg["nodes"])[5:10]
    assert page["truncated"] is True and _ok(s, {})["limit"] == rn.DEFAULT_LIMIT


def test_the_listing_holds_the_eight_capabilities_and_filters_by_kind_state_parent_and_owner():
    s, reg = _server(), _reg()
    caps = _ok(s, {"taxonomy": "capabilities"})
    assert [n["id"] for n in caps["nodes"]] == [f"CAP-000{i}" for i in range(1, 9)] and caps["total"] == 8
    assert caps["filters"] == {"taxonomy": "capabilities"}
    assert {n["id"] for n in _ok(s, {"kind": "capability_domain"})["nodes"]} == {"CAP-0001", "CAP-0006"}
    assert [n["id"] for n in _ok(s, {"parent": "CAP-0001"})["nodes"]] == ["CAP-0002", "CAP-0003", "CAP-0004", "CAP-0005"]
    roots = _ok(s, {"parent": None, "limit": 1000})
    assert roots["nodes"] and all(n["parent"] is None for n in roots["nodes"]) and roots["filters"] == {"parent": None}
    proposed = _ok(s, {"state": "proposed", "taxonomy": "capabilities"})
    assert [n["id"] for n in proposed["nodes"]] == ["CAP-0005"]
    for unit in sorted(nid for nid, n in reg["nodes"].items() if n["_taxonomy"] == "organisation"):
        owned = {n["id"] for n in _ok(s, {"owner": unit, "limit": 1000})["nodes"]}
        assert owned == {nid for nid in reg["nodes"] if ri.owning_unit(reg, nid)["unit"] == unit
                         or unit in ri.owning_unit(reg, nid)["owns"]}, unit


def test_lineage_climbs_parent_to_the_root_and_lists_children_without_walking():
    s, reg = _server(), _reg()
    got = _ok(s, {"node": "CAP-0002"})
    lin = got["lineage"]
    assert [a["id"] for a in lin["ancestors"]] == ["CAP-0001"] and lin["root"] == "CAP-0001" and lin["depth"] == 1
    assert got["nodes"][0]["id"] == "CAP-0002" and got["nodes"][0]["owning_unit"] == ri.owning_unit(reg, "CAP-0002")
    dom = _ok(s, {"node": "CAP-0001"})["lineage"]
    assert dom["ancestors"] == [] and dom["root"] == "CAP-0001"
    assert [(c["id"], c["state"]) for c in dom["children"]] == [(c, reg["nodes"][c]["state"]) for c in
                                                                 ["CAP-0002", "CAP-0003", "CAP-0004", "CAP-0005"]]
    for nid, n in reg["nodes"].items():   # every node: the chain is parent after parent, and never a walked edge
        lin = rn.lineage(reg, nid)
        at = n.get("parent")
        for a in lin["ancestors"]:
            assert a["id"] == at
            at = reg["nodes"][at].get("parent")
        assert at is None and lin["cycle"] is None and "edges" not in lin and "reached" not in lin
    deep = _ok(s, {"node": "PROC-0009"})["lineage"]
    assert deep["depth"] == 2 and deep["ancestors"][0]["id"] == reg["nodes"]["PROC-0009"]["parent"]


def test_a_cycle_or_a_missing_parent_ends_the_climb():
    reg = {"nodes": {"CAP-0001": {"parent": "CAP-0002", "_taxonomy": "capabilities"},
                     "CAP-0002": {"parent": "CAP-0001", "_taxonomy": "capabilities"},
                     "CAP-0003": {"parent": "CAP-0099", "_taxonomy": "capabilities"}}}
    lin = rn.lineage(reg, "CAP-0001")
    assert [a["id"] for a in lin["ancestors"]] == ["CAP-0002"] and lin["cycle"] == "CAP-0001"
    gone = rn.lineage(reg, "CAP-0003")
    assert gone["ancestors"] == [{"id": "CAP-0099", "kind": None, "name": None, "state": None, "missing": True}]


def test_it_refuses_what_the_register_does_not_hold():
    s = _server()
    for bad in ({"node": "CAP-9999"}, {"node": "cap-0001"}, {"node": "CAP-0002", "kind": "capability"},
                {"kind": "nope"}, {"taxonomy": "capability"}, {"state": "live"}, {"owner": "CAP-0001"},
                {"owner": "ORG-9999"}, {"parent": "CAP-9999"}, {"limit": 0}, {"limit": 5000}, {"offset": -1},
                {"limit": True}, {"walk": "dependants"}):
        r = _call(s, bad)
        assert r["isError"] is True, bad


def test_the_command_prints_the_same_report():
    out = subprocess.run([sys.executable, str(ROOT / "harness" / "register_nodes.py"), "--node", "CAP-0002"],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == rn.report({"node": "CAP-0002"})
    bad = subprocess.run([sys.executable, str(ROOT / "harness" / "register_nodes.py"), "--kind", "nope"],
                         capture_output=True, text=True, timeout=60)
    assert bad.returncode == 2 and bad.stdout == ""


def test_served_by_the_knowgov_server_on_both_transports_and_admitted_by_the_allowlist():
    """The server process lists register_nodes over stdio and Streamable HTTP and answers it alike; the
    shipped managed allowlist admits the server by name, so a client needs no change to reach it."""
    import os
    sys.path.insert(0, str(ROOT / "tools"))
    import check_mcp_server as c
    old = {k: os.environ.get(k) for k in ("KG_AS_OF",)}
    os.environ["KG_AS_OF"] = "2026-11-04"   # the runner pins the clock: the server needs a date to start
    try:
        got = {}
        for name, cls in (("stdio", c.StdioClient), ("http", c.HttpClient)):
            client = cls()
            try:
                assert "register_nodes" in {t["name"] for t in client.request("tools/list", {})["result"]["tools"]}, name
                got[name] = client.call("register_nodes", {"node": "CAP-0002"})
            finally:
                client.close()
        assert got["stdio"] == got["http"] and got["stdio"]["lineage"]["root"] == "CAP-0001"
    finally:
        for k, v in old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    allowed = {x["serverName"] for x in json.loads((ROOT / "instance" / "ci" / "claude" / "managed-mcp-allowlist.json")
                                                  .read_text(encoding="utf-8"))["allowedMcpServers"]}
    assert mcp_server.SERVER["name"] in allowed
