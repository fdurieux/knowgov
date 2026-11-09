"""Task-0157 (B7; decision-0013 with amendment A1): one reader for every subject under KG_SUBJECTS.

Every tool of the reader and of knowgov-runs takes an optional subject id, resolved under KG_SUBJECTS as
the page resolves ?subject=, never a path; none named answers exactly as today. A call naming another
subject is answered by a child process with that subject's KG_SUBJECT (harness/mcp_child.py), equal to
what a reader started on that subject answers. Each tool is classed store-backed or files-only in its
_meta; a store-backed tool for a subject whose scenario the store does not hold refuses, naming the held
subject and scenario and the run to start; list_subjects names each subject's held scenario or none. The
reader never loads: no route writes the store. Stdlib only; the routed store-backed refusal runs where
rdflib is installed (the rdflib job)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tests")]
import mcp_runs  # noqa: E402
import mcp_server  # noqa: E402
import subject_ids  # noqa: E402
from subject import SUBJECT  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402
from tests.test_mcp_runs import StubPage, _Env  # noqa: E402
from tests.test_mcp_server import Stub, _call, _server  # noqa: E402

OTHER = next(x["id"] for x in subject_ids.subjects() if x["id"] != SUBJECT.id)


REQUIRED_SAMPLE = {"key": "P2|surcharge", "node": "CAP-0001", "scenario": "S1", "source": "record", "path": "a.py",
                   "document": "docs/pricing.md", "subject_toml": ""}   # a well-typed value for each required argument


def _text(r) -> str:
    return r["content"][0]["text"]


def test_a_subject_is_an_id_under_kg_subjects_never_a_path():
    assert subject_ids.resolve(None) is None and subject_ids.is_own(None)
    own = subject_ids.resolve(SUBJECT.id)
    assert subject_ids.is_own(own) and own["root"] == Path(SUBJECT.root).resolve()
    other = subject_ids.resolve(OTHER)
    assert not subject_ids.is_own(other) and (other["root"] / "subject.toml").is_file()
    for bad in ("../cargo_quote", "/tmp", "subjects/cargo_quote", "", ".hidden", 7, "nope"):
        try:
            subject_ids.resolve(bad)
        except subject_ids.UnknownSubject as e:
            assert "KG_SUBJECTS" in str(e), bad
        else:
            raise AssertionError(f"{bad!r} resolved")
    # the page's rules: a fixture (listed = false) is skipped in a folder scan, listed when named directly
    assert "minimal" not in [x["id"] for x in subject_ids.subjects()]
    with _Env(KG_SUBJECTS=f"{ROOT / 'subjects'},{ROOT / 'subjects' / 'minimal'}"):
        assert subject_ids.resolve("minimal")["id"] == "minimal"
    with _Env(KG_SUBJECTS=str(ROOT / "subjects" / OTHER)):   # outside KG_SUBJECTS is refused; the own subject stays answerable
        assert [x["id"] for x in subject_ids.subjects()] == [SUBJECT.id, OTHER]
        try:
            subject_ids.resolve("minimal")
        except subject_ids.UnknownSubject:
            pass
        else:
            raise AssertionError("a subject outside KG_SUBJECTS resolved")
    assert subject_ids.declaring(SUBJECT.order[0]) == [SUBJECT.id] and subject_ids.declaring(None) == []


def test_every_tool_takes_subject_and_says_whether_it_is_store_backed():
    s, _ = _server()
    tools = s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]
    names = {t["name"] for t in tools}
    assert "list_subjects" in names
    for t in tools:
        assert isinstance(t["_meta"][mcp_server.META_STORE], bool), t["name"]
        assert (t["name"] in mcp_server.STORE_BACKED) == t["_meta"][mcp_server.META_STORE], t["name"]
        if t["name"] != "list_subjects":
            assert t["inputSchema"]["properties"]["subject"] == mcp_server.SUBJECT_ARG, t["name"]
    assert mcp_server.STORE_BACKED == {"store_status", "gate_verdict", "three_valued_answer", "evidence_bundle", "register_impact",
                                       "proposal_impact", "held_keys", "derived_outputs", "document_statements"}
    assert mcp_server.STORE_BACKED < names
    for t in mcp_runs.tools_table():
        assert t["inputSchema"]["properties"]["subject"] == mcp_server.SUBJECT_ARG, t["name"]


def test_none_named_or_the_own_subject_named_answers_exactly_as_today():
    s, _ = _server()
    for name, args in (("gate_verdict", {}), ("store_status", {}), ("register_nodes", {"taxonomy": "capabilities"})):
        plain = _call(s, name, args)["result"]
        named = _call(s, name, {**args, "subject": SUBJECT.id})["result"]
        assert plain == named and not plain.get("isError"), name


def test_a_path_or_an_unknown_subject_is_refused_on_every_tool():
    s, _ = _server()
    for t in mcp_server.TOOLS:
        if t["name"] == "list_subjects":
            continue
        need = {k: REQUIRED_SAMPLE[k] for k in t["inputSchema"].get("required", [])}   # task-0281: a call missing one is -32602 first
        r = _call(s, t["name"], {**need, "subject": "../" + SUBJECT.id})["result"]
        assert r["isError"] is True and "never a path" in _text(r), t["name"]
    r = _call(s, "register_nodes", {"subject": "no_such_subject"})["result"]
    assert r["isError"] is True and "no subject 'no_such_subject' under KG_SUBJECTS" in _text(r)


def test_list_subjects_names_each_subjects_held_scenario_and_the_tool_classes():
    held = SUBJECT.order[0]
    s, _ = _server(Stub(held))
    got = _call(s, "list_subjects")["result"]["structuredContent"]
    assert got["default"] == SUBJECT.id and got["subjects"][0]["id"] == SUBJECT.id and got["subjects"][0]["default"] is True
    by = {x["id"]: x for x in got["subjects"]}
    assert by[SUBJECT.id]["held"] == held and by[OTHER]["held"] is None and by[OTHER]["scenarios"]
    assert got["store"] == {"held_scenario": held, "held_by": [SUBJECT.id], "unavailable": None}
    assert set(got["store_backed"]) == mcp_server.STORE_BACKED
    assert set(got["store_backed"]) | set(got["files_only"]) == {t["name"] for t in mcp_server.TOOLS}
    # another subject's scenario held: it is that subject's, and this server's own holds none
    other_sc = subject_ids.resolve(OTHER)["scenarios"][0]
    got = _call(_server(Stub(other_sc))[0], "list_subjects")["result"]["structuredContent"]
    by = {x["id"]: x for x in got["subjects"]}
    assert by[OTHER]["held"] == other_sc and by[SUBJECT.id]["held"] is None
    # a store that cannot be read: the subjects are listed all the same, the reason given
    srv = mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(RuntimeError("down"))))
    got = _call(srv, "list_subjects")["result"]["structuredContent"]
    assert got["store"]["held_scenario"] is None and "down" in got["store"]["unavailable"] and len(got["subjects"]) >= 2


def test_a_store_backed_tool_on_a_subject_the_store_does_not_hold_names_the_held_one_and_the_run():
    """A1: the refusal is a next step, not a dead end (in-process: the store holds another subject's scenario)."""
    other_sc = subject_ids.resolve(OTHER)["scenarios"][0]
    s, _ = _server(Stub(other_sc))
    for name in ("gate_verdict", "three_valued_answer", "held_keys"):
        args = {"key": "x|y"} if name == "three_valued_answer" else {}
        r = _call(s, name, args)["result"]
        text = _text(r)
        assert r["isError"] is True and f"the store holds {other_sc}, a scenario of another subject ({OTHER})" in text, (name, text)
        assert f'start_run {{"subject": "{SUBJECT.id}", "scenario": "{SUBJECT.order[0]}"' in text and "never loads" in text, text
    r = _call(_server(Stub(None))[0], "gate_verdict")["result"]
    assert r["isError"] is True and "holds no scenario" in _text(r) and "start_run" in _text(r)


def test_a_call_for_another_subject_runs_in_a_child_equal_to_a_reader_started_on_it():
    """Design (a): a files-only tool for another subject, from a reader on the default subject, equals the
    same call on a reader whose KG_SUBJECT is that subject; the child never routes again."""
    other = subject_ids.resolve(OTHER)
    s, _ = _server()
    calls = [("register_nodes", {"taxonomy": "capabilities"}), ("scenario_runs", {})]
    for name, args in calls:
        routed = _call(s, name, {**args, "subject": OTHER})["result"]
        env = dict(os.environ, KG_SUBJECT=str(other["root"]))
        p = subprocess.run([sys.executable, str(ROOT / "harness" / "mcp_child.py")], input=json.dumps({"name": name, "arguments": args}),
                           capture_output=True, text=True, env=env, timeout=120)
        direct = json.loads(p.stdout)
        assert routed == direct and not routed.get("isError"), (name, routed, p.stderr[-300:])
    assert _call(s, "scenario_runs", {"subject": OTHER})["result"]["structuredContent"]["subject"] == OTHER
    src = (ROOT / "harness" / "mcp_child.py").read_text(encoding="utf-8")
    assert "route=None" in src and "mcp_server.Tools()" in src   # the child answers its own subject, through the read-only view
    assert mcp_server.Tools().opener is mcp_server.open_read_only


def test_the_routed_store_backed_refusal_names_the_held_subject_on_a_real_store():
    """On a file-backed rdflib store holding the default subject's first scenario, a store-backed call for
    another subject is refused by its child with the held subject and the run to start, and the store is
    left as it was."""
    need_rdflib()
    import gate_cli
    from store import open_store
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "store.ttl")
        with _Env(KG_STORE="rdflib", KG_RDFLIB_FILE=path, KG_AS_OF="record"):
            with open_store(instance=SUBJECT.id, access="write") as st:
                gate_cli._load(st, SUBJECT.order[0])
            before = Path(path).read_bytes()
            s = mcp_server.Server(mcp_server.Tools())
            r = _call(s, "gate_verdict", {"subject": OTHER})["result"]
            text = _text(r)
            assert r["isError"] is True and f"a scenario of another subject ({SUBJECT.id})" in text, text
            assert f'start_run {{"subject": "{OTHER}"' in text, text
            own = _call(s, "gate_verdict", {"subject": SUBJECT.id})["result"]
            assert not own.get("isError") and own["structuredContent"]["subject"] == SUBJECT.id
            assert Path(path).read_bytes() == before, "a reader call wrote the store"


def test_knowgov_runs_forwards_the_subject_id_to_the_page_and_refuses_a_path():
    page = StubPage()
    srv = mcp_runs.make_server(mcp_runs.Page("http://localhost:8080", token="t", opener=page))

    def call(name, args):
        return srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})["result"]
    with _Env(KG_MCP_RUN_MODES="deterministic"):
        assert call("run_options", {"subject": OTHER})["structuredContent"]["subject"] == OTHER
        assert page.requests[-1]["url"].endswith("/api/scenarios?subject=" + OTHER)
        got = call("start_run", {"subject": OTHER, "scenario": "S1", "mode": "deterministic"})["structuredContent"]
        assert got["subject"] == OTHER and page.requests[-1]["body"]["subject"] == OTHER
        assert call("run_options", {})["structuredContent"]["subject"] == SUBJECT.id
        r = call("run_status", {"subject": "../" + OTHER})
        assert r["isError"] is True and "never a path" in _text(r)


def test_the_readme_and_the_changelog_say_one_registration_serves_every_subject():
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    assert "list_subjects" in readme and "store-backed" in readme and "KG_SUBJECTS" in readme
    log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1]
    contract = log.split("### Contract changes", 1)[1].split("### Changes", 1)[0]
    assert "task-0157" in contract and "subject" in contract
