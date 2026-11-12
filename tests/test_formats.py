"""Task-0174 (decision-0023, doc-0028 G9-2): format versions on an instance's inputs. One rule in
``harness/formats.py``: a missing version reads as version 1 in every release (decision-0023 A1, task-0236), an
equal or lower one is read, a higher
one is refused (``FormatTooNew``), and every reader answers that with exit 2, naming the file, its version
and the reader's. Each reader is held here, each writer's stamp, the public subjects' key and the
attestation hook's indifference to it."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import formats  # noqa: E402
from tests._skip import skip  # noqa: E402

MINIMAL = ROOT / "subjects" / "minimal"
PUBLIC = ("cargo_quote", "jef_data_load", "minimal")


def _raises(fn, cls, *needles):
    try:
        fn()
    except cls as e:
        for n in needles:
            assert n in str(e), (n, str(e))
        return e
    raise AssertionError(f"{fn} did not raise {cls.__name__}")


def _py(*args, env=None, cwd=None) -> subprocess.CompletedProcess:
    e = {k: v for k, v in os.environ.items() if k not in ("KG_TRACEBACK",)}
    e.update(env or {})
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, env=e, timeout=300, cwd=cwd)


def _subject(tmp: Path, version) -> Path:
    root = tmp / "subj"
    shutil.copytree(MINIMAL, root)
    text = (root / "subject.toml").read_text(encoding="utf-8")
    assert "[format]\nversion = 1\n" in text
    if version is None:
        text = text.replace("[format]\nversion = 1\n", "")
    else:
        text = text.replace("[format]\nversion = 1\n", f"[format]\nversion = {version}\n")
    (root / "subject.toml").write_text(text, encoding="utf-8")
    return root


def test_the_rule_missing_reads_1_lower_and_equal_read_higher_refused():
    assert formats.version({}, "x.toml", formats.CODE_MAP) == formats.CURRENT["code_map"] == 1
    assert formats.version({"format": 1}, "x.toml", formats.CAPTURE) == 1
    assert formats.version({"format": {"version": 1}}, "subject.toml", formats.SUBJECT) == 1
    assert formats.version({"subject": {}}, "subject.toml", formats.SUBJECT) == 1
    e = _raises(lambda: formats.version({"format": 2}, "a/code_map.toml", formats.CODE_MAP), formats.FormatTooNew,
                "a/code_map.toml", "format = 2", "code_map format 1")
    assert isinstance(e, ValueError) and isinstance(e, formats.FormatError)
    _raises(lambda: formats.version({"format": {"version": 3}}, "s/subject.toml", formats.SUBJECT), formats.FormatTooNew,
            "s/subject.toml", "[format] version = 3", "subject format 1")
    for bad in ("1", 0, -1, 1.0, True):
        _raises(lambda: formats.version({"format": bad}, "c.toml", formats.REVIEW), formats.FormatError, "c.toml")
    _raises(lambda: formats.version({"format": 1}, "subject.toml", formats.SUBJECT), formats.FormatError, "must be a table")
    _raises(lambda: formats.version({"format": {"version": 1}}, "c.toml", formats.CAPTURE), formats.FormatError, "c.toml")
    saved = dict(formats.CURRENT)
    try:   # a lower version is read, once one moves
        formats.CURRENT["capture"] = 2
        assert formats.version({"format": 1}, "c.toml", formats.CAPTURE) == 1
        assert formats.version({}, "c.toml", formats.CAPTURE) == 1   # A1: missing is 1, never the current
    finally:
        formats.CURRENT.clear()
        formats.CURRENT.update(saved)



def test_a_missing_version_stays_1_when_a_kind_moves_to_2():
    """decision-0023 Amendment A1 (task-0236 AC #2): with a kind's current version moved to 2, an unstamped file
    reads as 1, the version it was written under; format = 2 reads as 2; format = 3 is refused, exit 2."""
    import cli_exit
    assert formats.MISSING == 1 and all(v == 1 for v in formats.CURRENT.values())   # nothing moves at 0.9.0
    saved = dict(formats.CURRENT)
    try:
        for kind in formats.CURRENT:
            formats.CURRENT.clear()
            formats.CURRENT.update(saved)
            formats.CURRENT[kind] = 2
            unstamped, two, three = ({"subject": {}}, {"format": {"version": 2}}, {"format": {"version": 3}}) \
                if kind == formats.SUBJECT else ({}, {formats.KEY.get(kind, "format"): 2}, {formats.KEY.get(kind, "format"): 3})   # the ledger's is schema_version
            assert formats.version(unstamped, "f.toml", kind) == 1, kind
            assert formats.version(two, "f.toml", kind) == 2, kind
            _raises(lambda: formats.version(three, "f.toml", kind), formats.FormatTooNew, "f.toml", "= 3", f"{kind} format 2")
            assert cli_exit.run(lambda: formats.version(three, "f.toml", kind), "probe") == 2, kind
    finally:
        formats.CURRENT.clear()
        formats.CURRENT.update(saved)

def test_a_subject_root_for_a_newer_knowgov_is_refused_by_every_reader_of_it():
    from subject import Subject
    import check_subject
    import subject_check
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        assert Subject(_subject(tmp / "a", None)).format == 1 and Subject(_subject(tmp / "b", 1)).format == 1
        root = _subject(tmp / "c", 2)
        _raises(lambda: Subject(root), formats.FormatTooNew, "subject.toml", "version = 2", "format 1")
        # check_subject: the report carries the version read; a newer one is cannot-run, exit 2, one line
        rep = check_subject.check(_subject(tmp / "d", None), None, set(), run_yield=False)
        assert rep["format"] == 1 and rep["exit_code"] == 0, rep
        _raises(lambda: check_subject.check(root, None, set(), run_yield=False), formats.FormatTooNew, "version = 2")
        p = _py(ROOT / "tools" / "check_subject.py", root)
        assert p.returncode == 2 and "cannot run:" in p.stderr and "version = 2" in p.stderr and "Traceback" not in p.stderr, p.stderr
        # a [format] field the loader does not read is named, as any other
        odd = _subject(tmp / "e", 1)
        (odd / "subject.toml").write_text((odd / "subject.toml").read_text().replace("version = 1", "version = 1\nrevision = 4"))
        rep = check_subject.check(odd, None, set(), run_yield=False)
        assert any(f["rule"] == "field" and f["where"] == "[format]" for f in rep["findings"]), rep["findings"]
        # the MCP subject_check refuses the call, naming the caller's label and never the temporary root
        args = {"subject_toml": (root / "subject.toml").read_text(encoding="utf-8"), "root": "subjects/probe",
                "scenarios_toml": (root / "scenarios.toml").read_text(encoding="utf-8"), "documents": {}}
        e = _raises(lambda: subject_check.evaluate(args, register=ROOT / "demo" / "register"), subject_check.SubjectCheckError,
                    "subjects/probe/subject.toml", "version = 2")
        assert "kg-subject-check-" not in str(e), str(e)
        args["subject_toml"] = (_subject(tmp / "f", 1) / "subject.toml").read_text(encoding="utf-8")
        assert subject_check.evaluate(args, register=ROOT / "demo" / "register")["format"] == 1
        # a run on it: the gate's command exits 2, naming the file
        p = _py(ROOT / "harness" / "gate_cli.py", "--task", "codegen", "--scenario", "S0",
                env={"KG_SUBJECT": str(root), "KG_STORE": "rdflib", "KG_RDFLIB_FILE": "", "KG_CLOCK": "pinned"})
        assert p.returncode == 2 and "version = 2" in p.stderr and "Traceback" not in p.stderr, (p.returncode, p.stderr)


def test_code_map_and_connectors_for_a_newer_knowgov_are_refused_with_exit_2():
    import code_map
    import connector
    import example_instance
    with tempfile.TemporaryDirectory() as t:
        inst = example_instance.build(Path(t) / "inst")
        cm = inst / "code_map.toml"
        assert tomllib.loads(cm.read_text(encoding="utf-8"))["format"] == 1   # the writer stamps it
        assert _py(ROOT / "tools" / "check_instance.py", inst).returncode == 0
        cm.write_text(cm.read_text(encoding="utf-8").replace("format = 1", "format = 2", 1), encoding="utf-8")
        _raises(lambda: code_map.code_map(inst, {}, []), formats.FormatTooNew, "code_map.toml", "format = 2")
        p = _py(ROOT / "tools" / "check_instance.py", inst)
        assert p.returncode == 2 and "code_map.toml: format = 2" in p.stderr and "Traceback" not in p.stderr, p.stderr
        if importlib.util.find_spec("rdflib") is not None:   # the trace opens its store first; its refusal needs one
            env = {"KG_CLOCK": "pinned", "KG_STORE": "rdflib", "KG_RDFLIB_FILE": "", "KG_SUBJECT": str(inst / "subjects" / "cargo_quote"),
                   "KG_REGISTER": str(inst / "register")}
            p = _py(ROOT / "harness" / "trace.py", "check", "--instance", inst, "--ledger", Path(t) / "ledger.json",
                    "--task", "codegen", "--as-of", "2026-11-04", env=env)
            assert p.returncode == 2 and "code_map.toml: format = 2" in p.stderr and "Traceback" not in p.stderr, (p.returncode, p.stderr[-600:])
        cm.write_text(cm.read_text(encoding="utf-8").replace("format = 2", "format = 1", 1), encoding="utf-8")
        # connectors.toml: tools/connector.py's configuration and check_instance both read it
        (inst / "connectors.toml").write_text('format = 9\n\n[system.aris]\nid_attribute = "AT_ID"\n', encoding="utf-8")
        _raises(lambda: connector.system_config(inst, "aris"), formats.FormatTooNew, "connectors.toml", "format = 9")
        p = _py(ROOT / "tools" / "connector.py", inst, inst / "nothing", "--system", "aris")
        assert p.returncode == 2 and "format = 9" in p.stderr, p.stderr
        p = _py(ROOT / "tools" / "check_instance.py", inst)
        assert p.returncode == 2 and "connectors.toml: format = 9" in p.stderr, p.stderr
        (inst / "connectors.toml").write_text('format = 1\n\n[system.aris]\nid_attribute = "AT_ID"\n', encoding="utf-8")
        assert connector.system_config(inst, "aris")["id_attribute"] == "AT_ID"
        # a subject of the instance written for a newer knowgov: the instance check cannot run, not "does not load"
        mf = inst / "subjects" / "cargo_quote" / "subject.toml"
        mf.write_text(mf.read_text(encoding="utf-8").replace("[format]\nversion = 1", "[format]\nversion = 2", 1), encoding="utf-8")
        p = _py(ROOT / "tools" / "check_instance.py", inst)
        assert p.returncode == 2 and "version = 2" in p.stderr and "does not load" not in p.stderr, p.stderr


def _capture(fmt: int | None) -> str:
    head = "" if fmt is None else f"format = {fmt}\n\n"
    return (head + '[capture]\nsubject = "cargo_quote"\nscenario = "S2"\ntask = "codegen"\nowner = "ORG-1"\n'
            'from = "employee-1"\non = 2026-11-01\nrecord = "captures/x.toml"\n\n[[answer]]\nkey = "k|v"\nvalue = "v"\nnote = ""\n')


def _review(fmt: int | None) -> str:
    head = "" if fmt is None else f"format = {fmt}\n\n"
    return head + '[review]\nby = "employee-2"\non = 2026-11-02\nrecord = "r.md"\n\n[[ruling]]\nassertion = "A:x"\noutcome = "approved"\n'


def _captures(tmp: Path, cap, rev=None) -> Path:
    d = tmp / "captures"
    (d / "reviews").mkdir(parents=True, exist_ok=True)
    (d / "2026-11-01-ORG-1-employee-1.toml").write_text(_capture(cap), encoding="utf-8")
    if rev is not None:
        (d / "reviews" / "2026-11-02-employee-2.toml").write_text(_review(rev), encoding="utf-8")
    return d


def test_captures_and_reviews_for_a_newer_knowgov_are_refused_by_every_reader():
    """The readers that need no PyYAML: the capture index, the due list, review.check, the answered questionnaire
    and capture.py's own exit. The load's two readers are the next test's, which needs the mappers' yaml."""
    import capture
    import review
    with tempfile.TemporaryDirectory() as t:
        d = _captures(Path(t), None)
        assert len(review.capture_index(d)) == 1 and capture.due_captures(d, dt.date(2027, 6, 1))
        d = _captures(Path(t), 2)
        _raises(lambda: review.capture_index(d), formats.FormatTooNew, "employee-1.toml", "format = 2", "capture format 1")
        _raises(lambda: capture.due_captures(d, dt.date(2027, 6, 1)), formats.FormatTooNew, "format = 2")
        d = _captures(Path(t), 1, rev=3)
        _raises(lambda: capture.due_captures(d, dt.date(2027, 6, 1)), formats.FormatTooNew, "employee-2.toml", "format = 3", "review format 1")
        doc = tomllib.loads(_review(2))
        _raises(lambda: review.check(doc, None, handles=None, owners={}, units={}, captures={}, now=dt.date(2026, 11, 8),
                                     compatible=None, where="r.toml"), formats.FormatTooNew, "r.toml", "format = 2")
        q = {"format": 4, "questionnaire": {}, "answered": {"from": "employee-1", "on": "2026-11-01"}, "item": []}
        _raises(lambda: capture.check_answers(q, capture.DEFAULT_HANDLE, set(), dt.date(2026, 11, 8), where="q.toml"),
                formats.FormatTooNew, "q.toml", "format = 4")
        # the command answers exit 2 in one line, never a traceback
        rv = Path(t) / "review.toml"
        rv.write_text(_review(2), encoding="utf-8")
        p = _py(ROOT / "harness" / "capture.py", "review", rv, "--show", env={"KG_CLOCK": "pinned"})
        assert p.returncode == 2 and "format = 2" in p.stderr and "Traceback" not in p.stderr, (p.returncode, p.stderr)


def test_the_loads_capture_and_review_readers_refuse_a_newer_file():
    """harness/load.py's load_captures and load_reviews: the load imports the mappers, which need PyYAML, so the
    stdlib job skips this half and every job with the pins runs it."""
    if importlib.util.find_spec("yaml") is None:
        skip("yaml", "harness/load.py imports the mappers, which need PyYAML; the stdlib job has none")
    import load
    with tempfile.TemporaryDirectory() as t:
        saved = load.SUBJECT.capture_dir
        try:
            load.SUBJECT.capture_dir = _captures(Path(t), 2)
            _raises(lambda: load.load_captures(None, "S2"), formats.FormatTooNew, "employee-1.toml", "format = 2", "capture format 1")
            load.SUBJECT.capture_dir = _captures(Path(t), 1, rev=3)
            _raises(lambda: load.load_reviews(None, "S2"), formats.FormatTooNew, "employee-2.toml", "format = 3", "review format 1")
        finally:
            load.SUBJECT.capture_dir = saved


def test_the_writers_stamp_the_version_they_write():
    import capture
    import review
    import wizard
    cap = {"subject": "s", "scenario": "S", "task": "codegen", "owner": "ORG-1", "from": "employee-1", "on": dt.date(2026, 11, 1),
           "answers": [{"key": "k|v", "value": "v", "note": ""}], "unknown": []}
    c = tomllib.loads(capture.capture_toml(cap, "captures/x.toml"))
    assert c["format"] == formats.CURRENT["capture"] and c["capture"]["from"] == "employee-1"
    norm = {"by": "employee-2", "on": dt.date(2026, 11, 2), "record": "r.md", "scenario": "S2",
            "rulings": [{"assertion": "A:x", "key": "k|v", "value": "v", "sha256": "0" * 64, "outcome": "approved", "note": ""}],
            "closes": []}
    r = tomllib.loads(review.review_toml(norm))
    assert r["format"] == formats.CURRENT["review"] and r["review"]["by"] == "employee-2"
    ref = wizard.reference()
    assert f"`[format] version = {formats.CURRENT['subject']}`" in ref and f"`format = {formats.CURRENT['code_map']}`" in ref
    assert wizard.main(["--check"]) == 0
    for sid in PUBLIC:   # the public subjects carry the key; their vendor/ trees are untouched
        m = tomllib.loads((ROOT / "subjects" / sid / "subject.toml").read_text(encoding="utf-8"))
        assert m["format"] == {"version": 1}, sid
    assert "[format] version = 1" in (ROOT / "instance" / "ci" / "claude" / "skills" / "knowgov-onboard" / "SKILL.md").read_text(encoding="utf-8")


def test_a_check_tool_answers_a_newer_input_with_exit_2_through_the_outcomes():
    import _outcomes

    def boom():
        raise formats.FormatTooNew("x.toml: format = 2, and this knowgov reads capture format 1 and earlier")
    with tempfile.TemporaryDirectory() as t:
        log = Path(t) / "o.jsonl"
        os.environ["KG_OUTCOMES"] = str(log)
        try:
            assert _outcomes.run(boom) == 2
        finally:
            del os.environ["KG_OUTCOMES"]
        row = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert row["exit"] == 2 and row["outcome"] == "cannot run", row


def test_the_attestation_hook_does_not_read_a_format_key_as_an_attestation():
    spec = importlib.util.spec_from_file_location("attestation_paths_fmt", ROOT / "instance" / "ci" / "claude" / "attestation_paths.py")
    ap = importlib.util.module_from_spec(spec)
    sys.modules["attestation_paths_fmt"] = ap
    spec.loader.exec_module(ap)
    with tempfile.TemporaryDirectory() as t:
        inst = Path(t)
        root = inst / "subjects" / "probe"
        root.mkdir(parents=True)
        mf = root / "subject.toml"
        mf.write_text('[subject]\nid = "probe"\n\n[verification]\nmap = "v.toml"\n', encoding="utf-8")
        ev = lambda tool, path, **ti: {"tool_name": tool, "tool_input": {"file_path": str(path), **ti}, "cwd": str(inst)}  # noqa: E731
        assert ap.check(ev("Edit", mf, old_string="[subject]", new_string="[format]\nversion = 1\n\n[subject]"), inst) == (0, "")
        assert ap.check(ev("Edit", mf, old_string='id = "probe"', new_string='id = "probe"\n\n[format]\nversion = 2'), inst)[0] == 0
        for name, text in (("code_map.toml", 'format = 1\n\n[code]\nroot = "."\n'), ("connectors.toml", "format = 1\n\n[system.aris]\n")):
            assert ap.check(ev("Write", inst / name, content=text), inst) == (0, ""), name
        # a capture stays one with its format key, and so does a review
        assert ap.check(ev("Write", inst / "notes" / "c.toml", content=_capture(1)), inst)[0] == 1
        assert ap.check(ev("Write", inst / "notes" / "r.toml", content=_review(1)), inst)[0] == 1


def _ledger(path: Path, version) -> Path:
    led = {"tool": "knowgov trace ledger", "entries": []}
    if version is not None:
        led["schema_version"] = version
    path.write_text(json.dumps(led), encoding="utf-8")
    return path


def test_the_trace_ledger_reads_its_schema_version_by_the_rule():
    """task-0280 (decision-0033 choice 6): the ledger's schema_version is its format. Missing reads as 1; a newer one is
    refused by trace (exit 2) and by code_path, on the CLI (exit 2) and the MCP server (an error answer)."""
    import trace
    import upward
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for v in (None, 1):
            assert trace.read_ledger(_ledger(tmp / f"l{v}.json", v), missing_ok=False)["entries"] == []
            assert upward.code_path("x.py", {"instance": None, "ledger": str(tmp / f"l{v}.json")})["ledger"]["status"] == "read"
        assert trace.read_ledger(tmp / "none.json", missing_ok=True)["schema_version"] == formats.CURRENT["ledger"]
        new = _ledger(tmp / "new.json", 99)
        _raises(lambda: trace.read_ledger(new, missing_ok=False), formats.FormatTooNew, "new.json", "schema_version = 99", "ledger format 1")
        _raises(lambda: upward.code_path("x.py", {"instance": None, "ledger": str(new)}), upward.UpwardError, "schema_version = 99")
        p = _py(ROOT / "harness" / "upward.py", "code", "x.py", "--ledger", new)
        assert p.returncode == 2 and "schema_version = 99" in p.stderr and "Traceback" not in p.stderr, p.stderr
        import mcp_server
        tools = mcp_server.Tools()
        tools.trace_cfg = {"instance": None, "ledger": str(new)}
        _raises(lambda: tools.code_path({"path": "x.py"}), mcp_server.ToolError, "schema_version = 99")
        if importlib.util.find_spec("rdflib") is not None:   # trace check opens its store before it reads the ledger
            import example_instance
            inst = example_instance.build(tmp / "inst")
            env = {"KG_CLOCK": "pinned", "KG_STORE": "rdflib", "KG_RDFLIB_FILE": "", "KG_SUBJECT": str(inst / "subjects" / "cargo_quote"),
                   "KG_REGISTER": str(inst / "register")}
            p = _py(ROOT / "harness" / "trace.py", "check", "--instance", inst, "--ledger", new, "--task", "codegen",
                    "--as-of", "2026-11-04", env=env)
            assert p.returncode == 2 and "schema_version = 99" in p.stderr and "Traceback" not in p.stderr, (p.returncode, p.stderr[-600:])


def test_a_proposal_overlay_takes_an_optional_format_by_the_rule():
    """task-0280: an overlay's top-level format is accepted (today it is an unknown field); missing reads as 1, a
    newer one is refused, exit 2 on the CLI and an error answer from the MCP server."""
    import proposal_impact
    fixture = json.loads((ROOT / "tools" / "fixtures" / "proposal_contract_quote.json").read_text(encoding="utf-8"))
    on = dt.date(2026, 11, 9)
    base = proposal_impact.evaluate(fixture, today=on)
    assert proposal_impact.evaluate({**fixture, "format": 1}, today=on)["coverage"] == base["coverage"]
    _raises(lambda: proposal_impact.evaluate({**fixture, "format": 2}, today=on), proposal_impact.ProposalError,
            "the proposal", "format = 2", "proposal format 1")
    _raises(lambda: proposal_impact.evaluate({**fixture, "format": "1"}, today=on), proposal_impact.ProposalError, "format = '1'")
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "p.json"
        f.write_text(json.dumps({**fixture, "format": 2}), encoding="utf-8")
        p = _py(ROOT / "harness" / "proposal_impact.py", f, "--no-store", "--as-of", "2026-11-09")
        assert p.returncode == 2 and f"{f}: format = 2" in p.stderr and "proposal format 1" in p.stderr and "Traceback" not in p.stderr, p.stderr
    import mcp_server
    _raises(lambda: mcp_server.Tools().proposal_impact({"proposal": {**fixture, "format": 2}, "as_of": "2026-11-09"}),
            mcp_server.ToolError, "format = 2")
