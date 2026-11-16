"""Task-0360 (decision-0047 point 2): who_knows, the handles and their holders whose attested evidence touches a
register node, a key or a code path. Files only, never the store; exactly one of node, key and path, else -32602;
evidence per handle sorted by kind, key and date, handles by id; no count, rank, weight or score; the holder the
register's person or null with why. The knowledge probe (tools/fixtures/knowledge_probe) is the fixture; its
expected reports are the ones tools/check_mcp_server.py holds the reader to on both stores."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
import who_knows  # noqa: E402

PROBE = ROOT / "tools" / "fixtures" / "knowledge_probe"
SUBJECT_ROOT = PROBE / "subjects" / "knowledge_probe"
SCHEMA = schema_check.load("who-knows")
ASKS = (("node", "CAP-0002", "node-CAP-0002"), ("key", "shipper|screened", "key-shipper_screened"), ("path", "quote.py", "path-quote_py"))


class _Env:
    """The probe's subjects (and the probe as the instance) for the block, KG_* as they were after."""

    def __init__(self, **extra):
        self.set = {"KG_SUBJECTS": str(SUBJECT_ROOT), "KG_INSTANCE": str(PROBE), **extra}

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.set}
        os.environ.update(self.set)

    def __exit__(self, *exc):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def _expected(stem: str) -> dict:
    return json.loads((PROBE / "expected" / f"who_knows-{stem}.json").read_text(encoding="utf-8"))


def _no_store():
    raise AssertionError("who_knows opened the store")


def _server():
    return mcp_server.Server(mcp_server.Tools(opener=_no_store))


def _call(server, args):
    return server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "who_knows", "arguments": args}})


def test_the_cli_on_the_probe_gives_its_expected_reports():
    """The command, started on the probe as its own subject, prints the reports check_mcp_server holds the reader to."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
    env.update(KG_SUBJECT=str(SUBJECT_ROOT), KG_SUBJECTS=str(SUBJECT_ROOT), KG_INSTANCE=str(PROBE), KG_CLOCK="pinned")
    for which, value, stem in ASKS:
        p = subprocess.run([sys.executable, str(ROOT / "harness" / "who_knows.py"), f"--{which}", value],
                           capture_output=True, text=True, env=env, timeout=120)
        assert p.returncode == 0, p.stderr
        got = json.loads(p.stdout)
        assert schema_check.validate(got, SCHEMA) == [], schema_check.validate(got, SCHEMA)[:3]
        got.pop("register")
        assert got == _expected(stem), (which, value)
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "who_knows.py"), "--key", "shipper|screend"],
                       capture_output=True, text=True, env=env, timeout=120)
    assert p.returncode == 2 and "did you mean shipper|screened" in p.stderr, p.stderr


def test_the_mcp_tool_answers_from_files_with_the_probes_handles():
    """In process the server's own subject is listed too (subject_ids): its rows widen the scope, and it holds no
    capture, so every handle and its evidence are the probe's. No store is opened."""
    with _Env():
        s = _server()
        for which, value, stem in ASKS:
            r = _call(s, {which: value})["result"]
            assert not r.get("isError"), r["content"][0]["text"]
            got = r["structuredContent"]
            assert schema_check.validate(got, SCHEMA) == []
            want = _expected(stem)
            assert got["handles"] == want["handles"] and got["asked"] == want["asked"], (which, value)
            assert set(want["keys"]) <= set(got["keys"]) and "knowledge_probe" in got["subjects"]


def test_anything_but_exactly_one_of_node_key_and_path_is_refused_with_32602():
    with _Env():
        s = _server()
        for bad in ({}, {"node": "CAP-0002", "key": "quote|currency"}, {"node": "CAP-0002", "path": "quote.py"},
                    {"key": "quote|currency", "subject": "knowledge_probe"}, {"node": "cap-2"}, {"key": "no-bar"},
                    {"path": 3}, {"node": "CAP-0002", "extra": 1}):
            err = _call(s, bad).get("error") or {}
            assert err.get("code") == -32602, (bad, err)
        for bad, why in (({"node": "CAP-9999"}, "not in the register"), ({"key": "shipper|screend"}, "did you mean"),
                         ({"path": "../quote.py"}, "without '..'"), ({"path": "nowhere.py"}, "no application")):
            r = _call(s, bad)["result"]
            assert r["isError"] and why in r["content"][0]["text"], (bad, r)


def test_the_tool_is_listed_files_only_without_a_subject_argument():
    tool = next(t for t in mcp_server.TOOLS if t["name"] == "who_knows")
    assert tool["_meta"][mcp_server.META_STORE] is False and "subject" not in tool["inputSchema"]["properties"]
    assert set(tool["inputSchema"]["properties"]) == {"node", "key", "path"} and "oneOf" not in tool["inputSchema"]
    assert tool["annotations"]["readOnlyHint"] is True and mcp_server.OUTPUT_SCHEMAS["who_knows"] == "who-knows"


def _walk(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from _walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from _walk(v)


def test_nothing_is_counted_ranked_weighted_or_scored_and_the_order_is_kind_key_date():
    with _Env():
        rep = who_knows.report({"node": "CAP-0002"}, str(PROBE))
    names = set(_walk(rep))
    assert not {n for n in names if any(w in n for w in ("score", "rank", "weight", "count", "total"))}, names
    assert [h["handle"] for h in rep["handles"]] == sorted(h["handle"] for h in rep["handles"])
    for h in rep["handles"]:
        order = [(e["kind"], e.get("key") or e.get("node"), e.get("on") or "") for e in h["evidence"]]
        assert order == sorted(order), h["handle"]
    e1 = next(h for h in rep["handles"] if h["handle"] == "employee-1")
    assert [e["kind"] for e in e1["evidence"]] == ["answered", "answered", "owns"]
    assert e1["evidence"][1]["nobody_knows"] is True and e1["evidence"][1]["key"] == "rate|rounding"
    c9 = next(h for h in rep["handles"] if h["handle"] == "contractor-9")
    assert c9["listed"] is False and c9["unit"] is None and c9["holder"] is None and "not on the register's issued list" in c9["holder_why"]
    e3 = next(h for h in rep["handles"] if h["handle"] == "employee-3")
    assert e3["evidence"] == [{"kind": "closed", "key": "rate|rounding", "subject": "knowledge_probe", "on": "2026-11-08",
                               "review": "review:2026-11-08-employee-3",
                               "gap": "gap:declared:capture:2026-11-05-ORG-0002-employee-1:1"}]


def test_a_ruling_without_a_key_reads_its_key_from_the_capture():
    with _Env():
        rep = who_knows.report({"key": "shipper|screened"}, str(PROBE))
    e3 = next(h for h in rep["handles"] if h["handle"] == "employee-3")
    assert e3["evidence"] == [{"kind": "approved", "key": "shipper|screened", "subject": "knowledge_probe", "on": "2026-11-08",
                               "review": "review:2026-11-08-employee-3", "statement": "A:cap:2026-11-06-ORG-0002-employee-2:1@capture"}]


def test_the_holder_is_the_registers_person_and_a_withdrawn_handle_owns_nothing():
    """decision-0047 point 7: once the register records person (ieam-register decision 0021) it is the holder; until
    then null with why. A handle with withdrawn recorded keeps its attested evidence and owns nothing."""
    with tempfile.TemporaryDirectory() as d:
        reg = Path(d) / "register"
        shutil.copytree(ROOT / "demo" / "register", reg)
        f = reg / "people" / "handles.toml"
        text = f.read_text(encoding="utf-8")
        text = text.replace('handle = "employee-1"\n', 'handle = "employee-1"\nperson = "dir:0001"\n', 1)
        text = text.replace('handle = "employee-2"\n', 'handle = "employee-2"\nwithdrawn = 2026-11-09\n', 1)
        f.write_text(text, encoding="utf-8")
        with _Env():
            rep = who_knows.report({"node": "CAP-0002"}, str(PROBE), register=reg)
    by = {h["handle"]: h for h in rep["handles"]}
    assert by["employee-1"]["holder"] == "dir:0001" and by["employee-1"]["holder_why"] is None
    assert by["employee-2"]["withdrawn"] == "2026-11-09" and by["employee-2"]["holder"] is None
    assert [e["kind"] for e in by["employee-2"]["evidence"]] == ["approved"]
    assert "records no person for employee-3" in by["employee-3"]["holder_why"]


def test_an_owns_link_names_its_unit_by_via():
    reg = {"nodes": {"CAP-1": {"owner": "ORG-1"}, "ORG-1": {"name": "one"}, "ORG-2": {"name": "two"}},
           "relationships": {"owns": {"links": [{"source": "ORG-2", "target": "CAP-1", "state": "approved"},
                                                {"source": "ORG-3", "target": "CAP-1", "state": "proposed"}]}}}
    rows = {"h-1": {"unit": "ORG-1"}, "h-2": {"unit": "ORG-2"}, "h-3": {"unit": "ORG-3"}}
    assert who_knows.owns(reg, {"CAP-1"}, rows) == [("h-1", {"kind": "owns", "node": "CAP-1", "via": "owner"}),
                                                     ("h-2", {"kind": "owns", "node": "CAP-1", "via": "owns_link"})]


def test_a_capture_for_a_newer_knowgov_is_refused_not_misread():
    import formats
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "knowledge_probe"
        shutil.copytree(SUBJECT_ROOT, root)
        cap = root / "captures" / "2026-11-05-ORG-0002-employee-1.toml"
        cap.write_text(cap.read_text(encoding="utf-8").replace("format = 1", "format = 99"), encoding="utf-8")
        with _Env(KG_SUBJECTS=str(root), KG_REGISTER=str(ROOT / "demo" / "register")):
            try:
                who_knows.report({"key": "quote|currency"}, str(PROBE))
            except formats.FormatTooNew as e:
                assert "format = 99" in str(e)
            else:
                raise AssertionError("a capture of format 99 was read")
