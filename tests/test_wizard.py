"""Task-0148: the subject wizard as procedure (doc-0018 candidate 4; doc-0021 §8). The reader serves
new_subject and add_artefact through prompts/list and prompts/get in both protocol eras, each the
instance skill's text verbatim; the skill's generated reference part equals the kinds table; both
carry the never-list and the stop condition and name only tools that exist; knowgov-runs offers no
prompts."""
from __future__ import annotations

import json
import re
import sys
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import mcp_server  # noqa: E402
import wizard  # noqa: E402

MODERN = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}


def _server():
    return mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(AssertionError("a prompt opens no store"))))


def _req(s, method, params=None, modern=False):
    p = dict(params or {})
    if modern:
        p["_meta"] = MODERN
    return s.handle({"jsonrpc": "2.0", "id": 1, "method": method, "params": p})


def test_prompts_listed_and_given_in_both_eras():
    s = _server()
    for modern in (False, True):
        r = _req(s, "prompts/list", modern=modern)["result"]
        assert [p["name"] for p in r["prompts"]] == ["new_subject", "add_artefact"], r
        if modern:
            assert r["resultType"] == "complete" and r["ttlMs"] and r["cacheScope"] == "private"
        new = next(p for p in r["prompts"] if p["name"] == "new_subject")
        assert [(a["name"], a["required"]) for a in new["arguments"]] == [("id", True), ("task", True)]
        g = _req(s, "prompts/get", {"name": "new_subject", "arguments": {"id": "renewal", "task": "codegen"}}, modern)["result"]
        (m,) = g["messages"]
        assert m["role"] == "user" and m["content"]["type"] == "text"
        assert m["content"]["text"].startswith("/new_subject with id `renewal`, task `codegen`.")
        g = _req(s, "prompts/get", {"name": "add_artefact", "arguments": {"subject": "renewal"}}, modern)["result"]
        assert g["messages"][0]["content"]["text"].startswith("/add_artefact with subject `renewal`.")
    for modern in (False, True):
        caps = (_req(s, "server/discover", modern=True)["result"] if modern else
                _req(s, "initialize", {"protocolVersion": "2025-06-18"})["result"])["capabilities"]
        assert caps["prompts"] == {"listChanged": False} and "resources" not in caps


def test_arguments_are_one_token_and_required_ones_are_asked_for():
    s = _server()
    for args, said in [({}, "needs id"), ({"id": "renewal"}, "needs task"), ({"id": "two words", "task": "codegen"}, "one token"),
                       ({"id": "Renewal", "task": "codegen"}, "one token"), ({"id": "r", "task": "c", "extra": "x"}, "not extra"),
                       ({"id": 3, "task": "c"}, "strings")]:
        e = _req(s, "prompts/get", {"name": "new_subject", "arguments": args})["error"]
        assert e["code"] == -32602 and said in e["message"], (args, e)
    assert _req(s, "prompts/get", {"name": "load_scenario"})["error"]["code"] == -32602
    assert "file `artefacts/x/y.md`" in _req(s, "prompts/get", {"name": "add_artefact", "arguments": {"subject": "s", "file": "artefacts/x/y.md"}})["result"]["messages"][0]["content"]["text"]


def test_one_text_two_carriers():
    """Every prompt is the skill's parts verbatim, and the skill's reference part is the generator's."""
    skill = wizard.SKILL.read_text(encoding="utf-8")
    assert wizard.skill_text() == skill, "run python harness/wizard.py --write-skill"
    parts = wizard.parts()
    assert set(parts) == {"intro", "never", "stop", "new_subject", "add_artefact", "exits", "reference"}
    for name, p in wizard.PROMPTS.items():
        args = {a["name"]: "x" for a in p["arguments"] if a["required"]}
        text = wizard.get(name, args)["messages"][0]["content"]["text"]
        body = text.split("\n\n", 1)[1]
        assert body == "\n".join(parts[k] for k in p["parts"]), name
        for k in p["parts"]:
            assert parts[k] in skill
        for k in ("never", "stop"):
            assert parts[k] in text, (name, k)
    assert skill.startswith("---\nname: knowgov-onboard\ndescription: ")


def test_the_never_list_and_the_stop_condition_say_what_they_must():
    never, stop = wizard.parts()["never"], wizard.parts()["stop"]
    for s in ("Never draft a document's content", "Never write an attestation", "Never take a task's keys from what the documents yield",
              "[verification]", "[provenance]", "captures/", "preload-baseline.json", "register/", "attestation_paths.py",
              "decision-0009", "questionnaire"):
        assert s in never, s
    for s in ("exits 0 with no WARNING", "exits 0 or 1, never 2", "knowledge with an owner and a route", "pull request"):
        assert s in stop, s
    allp = "\n".join(wizard.parts().values())
    # doc-0021 §8: the workarounds, the order and the manual steps after the merge
    for s in ("zero-yield", "not in that mapper's convention", "refuses a mapped artefact without", "is not a typo",
              "| REQ-nn | text |", "register_nodes", "proposal_impact", "commented out", "spelling, then mapper fit, then attestation",
              "no restart", "list_subjects", "`subject` the new id", "start_run", "replaces what everyone",
              "subject_check", "readiness card"):
        assert s in allp, s
    # B1 and B2 (task-0149, task-0150) retired these workarounds: the check and the page do it now
    for gone in ("always write `short`", "restart the page", "yield.artefacts", "relaunch or re-register"):
        assert gone not in allp, gone


def test_only_tools_that_exist_are_named():
    import mcp_runs
    tools = {t["name"] for t in mcp_server.TOOLS} | {t["name"] for t in mcp_runs.tools_table()}
    allp = "\n".join(wizard.parts().values())
    named = set(re.findall(r"`([a-z]+(?:_[a-z]+)+)`", allp))
    not_tools = {"max_unverified_share", "block_levels", "format_label", "requirement_id_pattern", "decided_by", "verified_by",
                 "realised_by", "elaborated_by", "plantuml_realises", "requirements_json", "contracts_markdown",
                 "dmn_decisions", "gherkin_tagged", "decision_table", "code_unit", "decision_table"}
    unknown = named - tools - not_tools - set(wizard.MAPPERS)
    assert not unknown, unknown
    for t in ("subject_check", "register_nodes", "register_impact", "proposal_impact", "gate_verdict", "start_run"):
        assert t in tools and t in allp, t


def test_every_mapper_has_its_convention_and_every_kind_is_listed():
    import ast   # read harness/extract.py's EXTRACTORS literal from source: the stdlib job cannot import it (PyYAML)
    tree = ast.parse((ROOT / "harness" / "extract.py").read_text(encoding="utf-8"))
    (lit,) = [n.value for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "EXTRACTORS" for t in n.targets)]
    extractors = {k.value for k in lit.keys}
    assert len(extractors) >= 14, extractors   # a literal the ast read found, not an empty one
    assert set(wizard.MAPPERS) == extractors | {"links"}
    ref = wizard.parts()["reference"]
    for k in wizard.kinds():
        assert f"`{k['folder']}`" in ref, k["folder"]


def test_over_streamable_http_too():
    s = _server()
    httpd = mcp_server.serve_http(s, "127.0.0.1", 0, None)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/mcp"
    try:
        def post(body, headers=None):
            req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                         headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **(headers or {})})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        body = {"jsonrpc": "2.0", "id": 1, "method": "prompts/get", "params": {"name": "new_subject", "arguments": {"id": "a", "task": "b"}}}
        code, r = post(body)
        assert code == 200 and r["result"]["messages"], r
        mbody = {**body, "params": {**body["params"], "_meta": MODERN}}
        hdr = {"MCP-Protocol-Version": "2026-07-28", "Mcp-Method": "prompts/get"}
        code, r = post(mbody, {**hdr, "Mcp-Name": "new_subject"})
        assert code == 200 and r["result"]["resultType"] == "complete", r
        code, r = post(mbody, {**hdr, "Mcp-Name": "add_artefact"})
        assert code == 400 and r["error"]["code"] == mcp_server.HEADER_MISMATCH and "prompt name" in r["error"]["message"], r
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_knowgov_runs_offers_no_prompts():
    import mcp_runs
    caps = mcp_server.Server(None, table=mcp_runs.tools_table(), info=mcp_runs.SERVER, instructions=mcp_runs.INSTRUCTIONS)
    r = _req(caps, "initialize", {"protocolVersion": "2025-06-18"})["result"]
    assert set(r["capabilities"]) == {"tools"}
    assert _req(caps, "prompts/list")["error"]["code"] == -32601
