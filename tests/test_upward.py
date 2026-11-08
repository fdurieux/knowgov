"""Task-0143 (doc-0020 C2): the upward joins with no store. A key to the register nodes its map rows
name; a code path to its application, the keys its header cites and its ledger entry, each leg read or
unchecked, never empty; and, on the example instance, the climb from a code file to a capability and
its ancestors in at most four calls, every one answered without opening the store."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import example_instance  # noqa: E402
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
import upward  # noqa: E402
from subject import SUBJECT  # noqa: E402

KEYS, CODE = schema_check.load("key-nodes"), schema_check.load("code-path")
_INST: list[Path] = []
SAME = example_instance.SUBJECT.name == SUBJECT.id   # the example instance is CargoQuote's


def _instance() -> Path:
    if not _INST:
        _INST.append(example_instance.build(Path(tempfile.mkdtemp(prefix="kg-up-")) / "inst"))
    return _INST[0]


def _root(inst: Path) -> Path:
    import tomllib
    return inst / tomllib.loads((inst / "code_map.toml").read_text(encoding="utf-8"))["code"]["root"]


def _valid(rep, schema):
    errors = schema_check.validate(rep, schema)
    assert errors == [], errors
    return rep


def _no_store():
    raise AssertionError("an upward join opened the store")


def _call(s, name, args):
    return s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})["result"]


def test_key_nodes_returns_every_map_row_on_the_key_with_its_nodes():
    rows = SUBJECT.register_map().get("row", [])
    for key in sorted({r["key"] for r in rows}):
        rep = _valid(upward.key_nodes(key), KEYS)
        mine = [r for r in rows if r["key"] == key]
        assert rep["mapped"] is True and len(rep["rows"]) == len(mine), key
        assert [[n["id"] for n in r["nodes"]] for r in rep["rows"]] == [r["nodes"] for r in mine], key
        assert [(r["owner"], r["anchor"], r["note"]) for r in rep["rows"]] == [(r.get("owner"), r.get("anchor"), r.get("note", "")) for r in mine]
        assert rep["nodes"] == sorted({x for r in mine for x in r["nodes"]})
    for bad in ("nope|x", "no-bar", 7, None):
        try:
            upward.key_nodes(bad)
        except upward.UpwardError:
            continue
        raise AssertionError(bad)


def test_a_known_key_with_no_row_reads_unmapped_not_refused():
    import tasks
    mapped = {r["key"] for r in SUBJECT.register_map().get("row", [])}
    loose = sorted({k for t in tasks.TASKS.values() for k in t["keys"]} - mapped)
    for key in loose[:3]:
        rep = _valid(upward.key_nodes(key), KEYS)
        assert rep["mapped"] is False and rep["rows"] == [] and rep["nodes"] == []


def test_code_path_on_the_example_instance_names_the_application_and_reads_the_header():
    if not SAME:
        return
    inst = _instance()
    rep = _valid(upward.code_path("reference_impl.py", upward.config(inst, None)), CODE)
    assert rep["code_map"]["status"] == "read" and rep["code_map"]["app"] == example_instance.CODE_APP
    assert rep["code_map"]["node"]["id"] == example_instance.CODE_APP and rep["code_map"]["is_code"] is True
    assert rep["citation"] == {"status": "read", "keys": [], "unknown": []}   # read, and it cites nothing
    assert rep["ledger"]["status"] == "unchecked" and rep["ledger"]["entry"] is None and "KG_LEDGER" in rep["ledger"]["reason"]


def test_a_missing_instance_code_map_or_ledger_is_unchecked_never_empty():
    rep = _valid(upward.code_path("a.py", {"instance": None, "ledger": None}), CODE)
    assert [rep[k]["status"] for k in ("code_map", "citation", "ledger")] == ["unchecked"] * 3
    assert rep["code_map"]["app"] is None and rep["citation"]["keys"] is None and rep["ledger"]["entry"] is None
    with tempfile.TemporaryDirectory() as d:
        bare = Path(d)
        rep = _valid(upward.code_path("a.py", upward.config(bare, bare / "ledger.json")), CODE)
        assert rep["code_map"]["status"] == "unchecked" and "code_map.toml: missing" in rep["code_map"]["reason"]
        assert rep["ledger"]["status"] == "unchecked" and "no ledger" in rep["ledger"]["reason"]
        (bare / "ledger.json").write_text("{not json", encoding="utf-8")
        rep = _valid(upward.code_path("a.py", upward.config(bare, bare / "ledger.json")), CODE)
        assert rep["ledger"]["status"] == "unchecked" and "does not parse" in rep["ledger"]["reason"]
        (bare / "ledger.json").write_text(json.dumps({"tool": "something else", "entries": []}), encoding="utf-8")
        assert upward.code_path("a.py", upward.config(bare, bare / "ledger.json"))["ledger"]["status"] == "unchecked"


def test_the_ledger_entry_carries_the_derived_id_keys_commit_and_digest_and_drift():
    if not SAME:
        return
    inst = _instance()
    root = _root(inst)
    sha = hashlib.sha256((root / "reference_impl.py").read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory() as d:
        led = Path(d) / "ledger.json"
        entry = {"id": "derived:code@abc123:reference_impl.py", "path": "reference_impl.py", "app": "APP-0001",
                 "sha256": sha, "commit": "abc123", "repo": "code", "kind": "code", "task": "codegen",
                 "assertions": ["A:x"], "keys": ["shipper_id|present"], "as_of": "2026-10-30"}
        other = {**entry, "id": "derived:code@abc123:other.py", "path": "other.py", "sha256": "0" * 64}
        led.write_text(json.dumps({"tool": "knowgov trace ledger", "schema_version": 1, "entries": [other, entry]}), encoding="utf-8")
        rep = _valid(upward.code_path("reference_impl.py", upward.config(inst, led)), CODE)
        got = rep["ledger"]
        assert got["status"] == "read" and got["entries"] == 2
        assert {k: got["entry"][k] for k in entry} == entry
        assert got["entry"]["current_sha256"] == sha and got["entry"]["drift"] is False and got["entry"]["file_present"] is True
        gone = _valid(upward.code_path("other.py", upward.config(inst, led)), CODE)["ledger"]["entry"]
        assert gone["file_present"] is False and gone["current_sha256"] is None and gone["drift"] is False
        none = _valid(upward.code_path("unregistered.py", upward.config(inst, led)), CODE)["ledger"]
        assert none["status"] == "read" and none["entry"] is None   # read: the ledger holds no entry for it


def test_a_ledger_entry_with_no_code_root_reads_unchecked_never_drift_false():
    """doc-0030 M7, task-0208: with no code root (no instance, or a code map that does not hold) the file was
    never looked at, so its ledger entry cannot say whether it drifted: the leg reads unchecked, naming why."""
    entry = {"id": "derived:code@abc123:a.py", "path": "a.py", "app": "APP-0001", "sha256": "0" * 64,
             "commit": "abc123", "assertions": []}
    with tempfile.TemporaryDirectory() as d:
        led = Path(d) / "ledger.json"
        led.write_text(json.dumps({"tool": "knowgov trace ledger", "schema_version": 1, "entries": [entry]}), encoding="utf-8")
        for inst in (None, Path(d)):   # no instance configured; an instance with no code_map.toml
            rep = _valid(upward.code_path("a.py", {"instance": None if inst is None else str(inst), "ledger": str(led)}), CODE)
            got = rep["ledger"]
            assert got["status"] == "unchecked" and got["entry"] is None, got
            assert "no code root" in got["reason"] and "drift" in got["reason"], got["reason"]


def test_cited_keys_unknown_ones_flagged_and_an_uncovered_or_malformed_header_unchecked():
    if not SAME:
        return
    with tempfile.TemporaryDirectory() as d:
        inst = example_instance.build(Path(d) / "inst")
        root = _root(inst)
        (root / "Quote.java").write_text("// knowgov-keys: shipper_id|present, bogus|key\nclass Quote {}\n", encoding="utf-8")
        (root / "bad.py").write_text("# knowgov-keys:\n", encoding="utf-8")
        (root / "notes.txt").write_text("knowgov-keys: shipper_id|present\n", encoding="utf-8")
        cfg = upward.config(inst, None)
        java = _valid(upward.code_path("Quote.java", cfg), CODE)
        assert java["citation"] == {"status": "read", "keys": ["shipper_id|present", "bogus|key"], "unknown": ["bogus|key"]}
        assert java["code_map"]["status"] == "read" and java["code_map"]["app"] is None and java["code_map"]["rows"] == []
        bad = _valid(upward.code_path("bad.py", cfg), CODE)["citation"]
        assert bad["status"] == "unchecked" and bad["malformed"] is True and bad["keys"] is None
        txt = _valid(upward.code_path("notes.txt", cfg), CODE)["citation"]
        assert txt["status"] == "unchecked" and txt["keys"] is None and ".java" in txt["reason"]
        missing = _valid(upward.code_path("absent.py", cfg), CODE)["citation"]
        assert missing["status"] == "unchecked" and "no file" in missing["reason"]


def test_a_path_out_of_the_code_root_is_refused():
    if not SAME:
        return
    with tempfile.TemporaryDirectory() as d:
        inst = example_instance.build(Path(d) / "inst")
        root = _root(inst)
        (Path(d) / "secret.py").write_text("# knowgov-keys: shipper_id|present\n", encoding="utf-8")
        (root / "link.py").symlink_to(Path(d) / "secret.py")
        cfg = upward.config(inst, None)
        for bad in ("../secret.py", "/etc/passwd", "a/../../secret.py", "a\\b.py", "", 7, "link.py"):
            try:
                upward.code_path(bad, cfg)
            except upward.UpwardError:
                continue
            raise AssertionError(bad)


def test_the_climb_from_a_code_file_to_a_capability_and_its_ancestors_takes_at_most_four_calls():
    if not SAME:
        return
    s = mcp_server.Server(mcp_server.Tools(opener=_no_store))
    s.tools.trace_cfg = upward.config(_instance(), None)
    calls = 0

    def call(name, args):
        nonlocal calls
        calls += 1
        r = _call(s, name, args)
        assert r["isError"] is False, (name, r["content"][0]["text"])
        return r["structuredContent"]
    app = call("code_path", {"path": "reference_impl.py"})["code_map"]["app"]
    up = call("register_impact", {"node": app, "walk": "dependants", "children": True})
    caps = [x["id"] for x in up["reached"].get("CAP", [])]
    assert caps, up["reached"]
    lineage = call("register_nodes", {"node": caps[0]})["lineage"]
    assert lineage["ancestors"] and lineage["root"].startswith("CAP-") and calls <= 4
    key = next(r["key"] for r in SUBJECT.register_map()["row"] if caps[0] in r["nodes"])
    assert caps[0] in call("key_nodes", {"key": key})["nodes"] and calls <= 4


def test_the_tools_refuse_through_the_server_and_read_kg_instance_once():
    s = mcp_server.Server(mcp_server.Tools(opener=_no_store))
    assert _call(s, "key_nodes", {"key": "nope|x"})["isError"] is True
    assert _call(s, "code_path", {"path": "../x"})["isError"] is True
    old = {k: os.environ.get(k) for k in ("KG_INSTANCE", "KG_LEDGER")}
    try:
        os.environ["KG_INSTANCE"], os.environ["KG_LEDGER"] = "/nonexistent/inst", "/nonexistent/ledger.json"
        s = mcp_server.Server(mcp_server.Tools(opener=_no_store))   # a fresh process: its first call reads the variables
        got = _call(s, "code_path", {"path": "a.py"})["structuredContent"]
        os.environ["KG_INSTANCE"] = "/elsewhere"
        again = _call(s, "code_path", {"path": "a.py"})["structuredContent"]
    finally:
        for k, v in old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    assert got["instance"] == again["instance"] == str(Path("/nonexistent/inst").resolve())
    assert got["code_map"]["status"] == "unchecked" and "no instance at" in got["code_map"]["reason"]


def test_the_instructions_name_the_down_and_up_sequences():
    text = mcp_server.INSTRUCTIONS
    down, up = text.index("Down, from a capability"), text.index("Up, from a code file")
    assert text.index("register_impact walk=realisers", down) < text.index("evidence_bundle keys=", down) < up
    seq = [text.index(t, up) for t in ("code_path", "key_nodes", "register_impact walk=dependants", "register_nodes node=")]
    assert seq == sorted(seq)


def test_the_command_prints_the_same_reports():
    out = subprocess.run([sys.executable, str(ROOT / "harness" / "upward.py"), "key", "shipper_id|present"],
                         capture_output=True, text=True, timeout=60)
    if "shipper_id|present" in {r["key"] for r in SUBJECT.register_map().get("row", [])}:
        assert out.returncode == 0 and json.loads(out.stdout) == upward.key_nodes("shipper_id|present")
    bad = subprocess.run([sys.executable, str(ROOT / "harness" / "upward.py"), "code", "../x"],
                         capture_output=True, text=True, timeout=60)
    assert bad.returncode == 2 and bad.stdout == ""


DOCS = schema_check.load("document-links")


def test_document_links_are_the_projections_cites_for_every_document():
    """Each document's links equal what the page's projection (demo/app/register_project) cites it with: the
    same evidence rule, read from the register's files, never the store; no document cited, none refused."""
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import register_project as rp
    cites = rp.rows(loaded_at="2026-10-31T00:00:00+00:00")["cites"]
    by_doc: dict[str, set] = {}
    for c in cites:
        by_doc.setdefault(c["path"], set()).add((c["reg_id"], c["anchor"]))
    assert by_doc, "the subject's register cites no document"
    for doc, want in by_doc.items():
        rep = _valid(upward.document_links(doc), DOCS)
        assert rep["document"] == doc and {(ln["id"], ln["evidence"]) for ln in rep["links"]} == want, doc
        for ln in rep["links"]:
            assert ln["source"]["owning_unit"]["unit"] and (ln["target"] is None or ln["target"]["owning_unit"]["unit"])
            assert ln["anchor"] == (ln["evidence"].split("#", 1)[1] if "#" in ln["evidence"] else None)
        assert rep["nodes"] == sorted({x["id"] for ln in rep["links"] for x in (ln["source"], ln["target"]) if x})
    system, _ = upward._system()
    doc = sorted(by_doc)[0]
    tail = doc[len("kit/"):] if doc.startswith("kit/") else doc
    assert upward.document_links(system + tail + "#anything")["document"] == doc   # prefix and anchor accepted
    for bad in ("nope.md", "", 7, None):
        try:
            upward.document_links(bad)
        except upward.UpwardError:
            continue
        raise AssertionError(bad)


def test_the_file_only_tools_are_listed_and_answer_alike_on_both_transports_and_the_allowlist_admits_them():
    """task-0142 and task-0143, served over MCP: the server process lists every doc-0020 tool over stdio and
    Streamable HTTP and answers each the same; the managed allowlist admits the server by name."""
    import check_mcp_server
    failures: list[str] = []
    old = {k: os.environ.get(k) for k in ("KG_INSTANCE", "KG_LEDGER", "KG_STORE", "KG_RDFLIB_FILE", "KG_AS_OF")}
    try:
        with tempfile.TemporaryDirectory() as d:
            os.environ.update(KG_STORE="rdflib", KG_RDFLIB_FILE=str(Path(d) / "absent.ttl"), KG_AS_OF="2026-11-04")   # the clock is pinned
            if SAME:
                os.environ.update(KG_INSTANCE=str(_instance()), KG_LEDGER=str(Path(d) / "ledger.json"))
            check_mcp_server.check_transports(failures)
    finally:
        for k, v in old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    assert failures == [], failures
