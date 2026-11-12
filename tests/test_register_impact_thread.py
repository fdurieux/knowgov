"""task-0336 (decision-0039 §3.3 (a), doc-0038 §3.3, B-D7): ``register_impact`` walks the thread. FR-06 names three
walks; the register offers them as ``impact.WALKS`` (dependants, realisers, thread, its decisions 0010, 0012 and 0018).
``walk=thread`` is the register's own THREAD walk, in register_impact's answer shape (edges, reached, keys, gate),
offered on the MCP tool's inputSchema and on the page's impact route, and held equal to ``tools/impact.py``."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import mcp_server  # noqa: E402
import register_impact as ri  # noqa: E402


def _no_store():
    return mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(OSError("no store here"))))


def _call(s, args):
    r = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "register_impact", "arguments": args}})
    assert "result" in r and r["result"]["isError"] is False, r
    return r["result"]["structuredContent"]


def _register():
    root = ri.register_root()
    T = ri.load_tools(root)
    return root, T, T["register"].load_register(root)


def _cli_reach(root: Path, node: str) -> dict[str, list[str]]:
    """What ``tools/impact.py --walk thread`` prints as reached, by prefix: the register's own command, run as is."""
    p = subprocess.run([sys.executable, str(root / "tools" / "impact.py"), "--from", node, "--walk", "thread", "--root", str(root)],
                       capture_output=True, text=True, check=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": ""})
    line = p.stdout.strip().splitlines()[-1]
    out = {}
    for word, prefix in (("processes", "PROC"), ("capabilities", "CAP"), ("applications", "APP"), ("information", "ENT")):
        m = re.search(rf"{word} reached (\[[^\]]*\]|none)", line)
        assert m, line
        out[prefix] = [] if m.group(1) == "none" else json.loads(m.group(1).replace("'", '"'))
    return out


def test_ac1_thread_from_a_capability_and_a_process_reaches_what_the_registers_thread_walk_reaches():
    """Every node, with children and without: register_impact walk=thread gives impact.walk's (or walk_children's)
    edges over impact.WALKS["thread"] and its reached set; over the MCP tool, from a capability and from a process,
    the reach equals what tools/impact.py --walk thread prints and the keys are the map rows naming the start or a
    reached node. A capability has no THREAD row, so it reaches nothing and lands only its own rows."""
    from subject import SUBJECT
    root, T, reg = _register()
    rows = T["impact"].WALKS["thread"]
    for nid in sorted(reg["nodes"]):
        got = ri.walk(nid, "thread")
        edges = T["impact"].walk(reg, nid, rows)
        assert got["walk"] == "thread" and got["edges"] == edges and got["reached_ids"] == sorted(T["impact"].reached(edges)), nid
        kids = ri.walk(nid, "thread", children=True)
        want = T["impact"].walk_children(reg, nid, rows)
        assert kids["edges"] == want["edges"] and kids["reached_ids"] == sorted(want["reached"]), nid
    s = _no_store()
    cap = sorted(n for n, x in reg["nodes"].items() if x.get("_taxonomy") == "capabilities" and x.get("kind") == "capability")[0]
    proc = next(n for n in sorted(n for n, x in reg["nodes"].items() if x.get("_taxonomy") == "processes")
                if {"CAP", "APP", "ENT"} <= {x.split("-")[0] for x in T["impact"].reached(T["impact"].walk(reg, n, rows))})
    for node in (cap, proc):
        got = _call(s, {"node": node, "walk": "thread"})
        assert got["walk"] == "thread" and {"edges", "reached", "keys", "gate"} <= set(got), node
        assert got["edges"] == T["impact"].walk(reg, node, rows), node
        by = {p: [x["id"] for x in xs] for p, xs in got["reached"].items()}
        cli = _cli_reach(root, node)
        assert {p: v for p, v in cli.items() if v} == by, (node, cli, by)
        reached = sorted(x for xs in by.values() for x in xs)
        assert [k["key"] for k in got["keys"]] == [k["key"] for k in ri.landed_rows(SUBJECT.register_map(), node, reached)], node
    assert _call(s, {"node": cap, "walk": "thread"})["edges"] == []
    on_proc = _call(s, {"node": proc, "walk": "thread"})
    assert {"CAP", "APP", "ENT"} <= set(on_proc["reached"]), on_proc["reached"]   # the process down to the data
    # the thread is its own walk: from the process it is neither the dependants' nor the realisers' answer
    assert on_proc["edges"] != _call(s, {"node": proc})["edges"] and on_proc["edges"] != _call(s, {"node": proc, "walk": "realisers"})["edges"]


def test_ac2_the_mcp_schema_and_the_page_offer_thread_and_agree_with_register_impact():
    """The tool's inputSchema lists thread beside the other two; the page's impact route takes it (register_view.WALKS,
    the select, ``?walk=thread``) and gives, for every node, the edges and the reach register_impact gives; the Neo4j
    steps for the thread are the register's THREAD rows (store_neo4j.WALK_STEPS, so the guides and the
    agreement check over the projection cover it)."""
    tool = next(t for t in mcp_server.TOOLS if t["name"] == "register_impact")
    assert tool["inputSchema"]["properties"]["walk"]["enum"] == ["dependants", "realisers", "thread"]
    assert ri.WALKS == ("dependants", "realisers", "thread")
    import store_neo4j as sn
    _, T, reg = _register()
    assert {(tax, "REG_" + rel.upper(), fwd) for tax, rels in T["impact"].WALKS["thread"].items() for rel, fwd in rels} == \
        {(tax, t, src) for tax, types, src in sn.WALK_STEPS["thread"] for t in types}
    assert {"thread", "thread-children"} <= set(sn.IMPACT_VARIANTS)
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import register_view
    assert "thread" in register_view.WALKS
    for nid in sorted(reg["nodes"]):
        for children in (False, True):
            page = register_view.impact(nid, "thread", children)
            got = ri.walk(nid, "thread", children=children)
            assert page["walk"] == "thread" and page["edges"] == got["edges"] and page["reached"]["all"] == got["reached_ids"], (nid, children)
    html = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert '<option value="thread">thread</option>' in re.search(r'<select id="impact-walk".*?</select>', html).group(0)
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    import server

    class Quiet(server.Handler):
        def log_message(self, fmt, *args):
            pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        proc = next(n for n in sorted(reg["nodes"]) if n.startswith("PROC-") and ri.walk(n, "thread")["reached_ids"])
        got = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_address[1]}/api/register/impact/{proc}?walk=thread").read())
        assert got["walk"] == "thread" and got["reached"]["all"] == ri.walk(proc, "thread")["reached_ids"]
        assert got["panel"]["title"] == f"What {proc} uses, down to the data"
    finally:
        httpd.shutdown()
        httpd.server_close()
