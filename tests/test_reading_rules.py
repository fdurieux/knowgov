"""task-0367: the reader tells an assistant how to use what the tools return, the same on both transports and in both
protocol eras, and the adopter docs give the same rules as a paste-able client-side instruction.

The rules: quote numbers from a tool's fields and name the tool; never state a count not read; re-ask with gate_verdict's
summary or filter when a result carries io.knowgov/clipped or io.knowgov/large (task-0365); re-query before repeating an
earlier claim; subject_overview (task-0366) and gate_verdict's summary (task-0364) first for a large subject; never infer
a link no tool states."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import mcp_server  # noqa: E402
import result_marks  # noqa: E402

README = ROOT / "instance" / "README.md"
NAMES = ("io.knowgov/clipped", "io.knowgov/large", "gate_verdict", "summary", "filter", "subject_overview", "key_nodes")
MODERN = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {},
          "io.modelcontextprotocol/clientInfo": {"name": "t", "version": "1"}}


def test_the_instructions_carry_every_rule_with_the_names_as_shipped():
    text = mcp_server.INSTRUCTIONS
    assert all(rule in text for rule in mcp_server.READING_RULES) and len(mcp_server.READING_RULES) == 6
    assert text.endswith("This server only reads.")
    joined = " ".join(mcp_server.READING_RULES)
    for name in NAMES:
        assert name in joined, name
    assert result_marks.META_CLIPPED in joined and result_marks.META_LARGE in joined   # the marks as #604 shipped them
    tools = {t["name"] for t in mcp_server.TOOLS}
    assert {"subject_overview", "key_nodes", "gate_verdict"} <= tools
    props = next(t for t in mcp_server.TOOLS if t["name"] == "gate_verdict")["inputSchema"]["properties"]
    assert {"summary", "filter"} <= set(props)   # the arguments as #601 shipped them
    for phrase in ("name the tool", "Never state a count", "ask again narrowly", "ask the tool again", "first", "never infer"):
        assert phrase in joined, phrase


def _stdio() -> tuple[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
    env.update(KG_CLOCK="pinned", KG_AS_OF="record", KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"))
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "server/discover", "params": {"_meta": MODERN}}]
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "mcp_server.py")], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, timeout=120, env=env)
    out = [json.loads(line) for line in p.stdout.splitlines() if line.strip()]
    return out[0]["result"]["instructions"], out[1]["result"]["instructions"]


def _http() -> tuple[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
    env.update(KG_CLOCK="pinned", KG_AS_OF="record", KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"))
    p = subprocess.Popen([sys.executable, str(ROOT / "harness" / "mcp_server.py"), "--http", "--host", "127.0.0.1", "--port", "0"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=env)
    try:
        m = re.search(r"(http://127\.0\.0\.1:\d+/mcp)", p.stderr.readline())
        assert m, "the HTTP server did not start"
        url, got = m.group(1), []
        for body, headers in (({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}}, {}),
                              ({"jsonrpc": "2.0", "id": 2, "method": "server/discover", "params": {"_meta": MODERN}},
                               {"Mcp-Method": "server/discover", "MCP-Protocol-Version": "2026-07-28"})):
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                         headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **headers})
            with urllib.request.urlopen(req, timeout=60) as r:
                got.append(json.loads(r.read())["result"]["instructions"])
        return got[0], got[1]
    finally:
        p.terminate()
        try:
            p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            p.kill()


def test_the_same_text_goes_out_on_both_transports_and_in_both_eras():
    for name, (handshake, stateless) in (("stdio", _stdio()), ("http", _http())):
        assert handshake == stateless == mcp_server.INSTRUCTIONS, name
        assert all(rule in handshake for rule in mcp_server.READING_RULES), name


def _client_block() -> str:
    text = README.read_text(encoding="utf-8")
    section = text.split("### Telling your assistant how to use the answers", 1)[1].split("\n### ", 1)[0]
    return section.split("```text\n", 1)[1].split("```", 1)[0]


def test_the_adopter_docs_give_the_same_rules_as_a_paste_able_instruction():
    block = _client_block()
    numbered = re.findall(r"^(\d+)\. ", block, re.M)
    assert numbered == [str(i) for i in range(1, len(mcp_server.READING_RULES) + 1)], numbered
    for name in NAMES:
        assert name in block, name
    flat = " ".join(block.split())
    for phrase in ("say which tool", "Never state a count", "Ask again more narrowly", "ask the tool again",
                   "start with subject_overview", "Never state a link"):
        assert phrase in flat, phrase
    section = README.read_text(encoding="utf-8").split("### Telling your assistant how to use the answers", 1)[1].split("\n### ", 1)[0]
    assert "READING_RULES" in section and "Paste this as it is" in section
