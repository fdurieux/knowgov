"""Task-0361 (decision-0046 point 2, brought into 0.10.0 by decision-0047 point 3): the question bridge's three read-only
tools. pending_questions lists an issued handle's open items from the instance's questionnaires less what the captures
answered, refusing a handle that is not issued; question_evidence returns one item's evidence as the instance generated
it, or why not; answer_link computes the prefilled issue-form URL from the instance's questions.toml and its template,
writing nothing, a verdict outside the form's four refused. The knowledge probe (tools/fixtures/knowledge_probe) is the
fixture; its expected reports are the ones tools/check_mcp_server.py holds the reader to on both stores."""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import formats  # noqa: E402
import mcp_server  # noqa: E402
import questions  # noqa: E402
import schema_check  # noqa: E402
from subject import Subject  # noqa: E402

PROBE = ROOT / "tools" / "fixtures" / "knowledge_probe"
SUBJECT_ROOT = PROBE / "subjects" / "knowledge_probe"
REGISTER = ROOT / "demo" / "register"
ON = dt.date(2026, 11, 10)
CLI = (("pending_questions-employee-1", ["pending", "employee-1"]), ("pending_questions-employee-3", ["pending", "employee-3"]),
       ("question_evidence-quote_insurance", ["evidence", "quote|insurance"]),
       ("question_evidence-quote_currency", ["evidence", "quote|currency"]),
       ("answer_link-quote_insurance", ["link", "quote|insurance", "right_with_correction", "A quote includes no insurance."]),
       ("answer_link-rate_rounding", ["link", "rate|rounding", "dont_know", "", "--scenario", "S0", "--owner", "ORG-0001"]))


class _Env:
    def __init__(self, **extra):
        self.set = {"KG_SUBJECTS": str(SUBJECT_ROOT), "KG_INSTANCE": str(PROBE), "KG_REGISTER": str(REGISTER), **extra}

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.set}
        os.environ.update(self.set)

    def __exit__(self, *exc):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def _expected(stem: str) -> dict:
    return json.loads((PROBE / "expected" / f"{stem}.json").read_text(encoding="utf-8"))


def _copy(d: str) -> Path:
    """A writable copy of the probe, its subject and the demo register beside it."""
    inst = Path(d) / "inst"
    shutil.copytree(PROBE, inst)
    shutil.copytree(REGISTER, inst / "register")
    return inst


def test_the_cli_on_the_probe_gives_its_expected_reports():
    env = {k: v for k, v in os.environ.items() if not k.startswith("KG_")}
    env.update(KG_SUBJECT=str(SUBJECT_ROOT), KG_SUBJECTS=str(SUBJECT_ROOT), KG_INSTANCE=str(PROBE), KG_CLOCK="pinned", KG_TODAY=ON.isoformat())
    for stem, argv in CLI:
        p = subprocess.run([sys.executable, str(ROOT / "harness" / "questions.py"), *argv], capture_output=True, text=True,
                           env=env, timeout=120)
        assert p.returncode == 0, (argv, p.stderr)
        got = json.loads(p.stdout)
        tool = stem.split("-", 1)[0]
        assert schema_check.validate(got, schema_check.load(mcp_server.OUTPUT_SCHEMAS[tool])) == [], stem
        assert got == _expected(stem), stem


def test_pending_lists_the_units_open_items_less_those_a_capture_answered():
    with _Env():
        rep = questions.pending("employee-1", str(PROBE), ON)
    assert [i["key"] for i in rep["items"]] == ["quote|insurance"] and rep["items"][0]["evidence"] is True
    assert {a["key"]: a["from"] for a in rep["answered"]} == {"quote|currency": "employee-1", "quote|validity_days": "employee-1",
                                                             "rate|rounding": "employee-1", "shipper|screened": "employee-2"}
    with _Env():
        three = questions.pending("employee-3", str(PROBE), ON)
        four = questions.pending("employee-4", str(PROBE), ON)
    # ORG-0002's capture of rate|rounding does not answer ORG-0001's questionnaire: each unit answers its own
    assert [i["key"] for i in three["items"]] == ["rate|rounding"] and three["answered"] == []
    assert four["items"] == [] and four["answered"] == [] and four["unit"] == "ORG-0004"


def test_a_handle_that_may_not_answer_is_refused():
    with tempfile.TemporaryDirectory() as d:
        inst = _copy(d)
        f = inst / "register" / "people" / "handles.toml"
        text = f.read_text(encoding="utf-8")
        text = text.replace('handle = "employee-2"\n', 'handle = "employee-2"\nwithdrawn = 2026-11-09\n', 1)
        text += '\n[[handle]]\nhandle = "employee-5"\nunit = "ORG-0002"\nroles = ["approves"]\nissued = 2026-11-02\n'
        text += '\n[[handle]]\nhandle = "employee-6"\nunit = "ORG-0002"\nroles = ["gives"]\nissued = 2026-12-01\n'
        f.write_text(text, encoding="utf-8")
        cases = (("contractor-9", "not issued"), ("employee-2", "withdrawn on 2026-11-09"), ("employee-5", "lacks the role gives"),
                 ("employee-6", "issued on 2026-12-01"), ("Jane Doe", "not an opaque handle"), (None, "not an opaque handle"))
        with _Env():
            for handle, why in cases:
                try:
                    questions.pending(handle, str(inst), ON, register=inst / "register")
                except questions.QuestionsError as e:
                    assert why in str(e), (handle, e)
                else:
                    raise AssertionError(f"{handle} was not refused")


def test_a_review_due_questionnaire_is_the_handles_and_closed_by_its_own_capture():
    with tempfile.TemporaryDirectory() as d:
        inst = _copy(d)
        (inst / "questions" / "questionnaire-due-knowledge_probe-employee-2.toml").write_text(
            '[questionnaire]\nsubject = "knowledge_probe"\nscenario = "S0"\ntask = "codegen"\nowner = "ORG-0002"\nto = "employee-2"\n'
            'route = "review-due"\ngenerated_on = 2026-11-09\n\n[[item]]\nkey = "shipper|screened"\nearlier = "before pricing"\n'
            'due = 2026-11-09\nquestion = "Is this still true?"\n\n[[item]]\nkey = "quote|currency"\nearlier = "EUR"\ndue = 2026-11-09\n'
            'question = "Is this still true?"\n', encoding="utf-8")
        cap = inst / "subjects" / "knowledge_probe" / "captures" / "2026-11-09-ORG-0002-employee-2.toml"
        cap.write_text('format = 1\n[capture]\nsubject = "knowledge_probe"\nscenario = "S0"\ntask = "codegen"\nowner = "ORG-0002"\n'
                       'from = "employee-2"\non = 2026-11-09\nrecord = "x"\n\n[[answer]]\nkey = "shipper|screened"\nvalue = "before pricing"\n',
                       encoding="utf-8")
        with _Env(KG_SUBJECTS=str(inst / "subjects" / "knowledge_probe")):
            two = questions.pending("employee-2", str(inst), ON, register=inst / "register")
            one = questions.pending("employee-1", str(inst), ON, register=inst / "register")
    due = [i for i in two["items"] if i["route"] == "review-due"]
    assert [(i["key"], i["earlier"], i["due"]) for i in due] == [("quote|currency", "EUR", "2026-11-09")]
    assert any(a["key"] == "shipper|screened" and a["on"] == "2026-11-09" for a in two["answered"])
    assert not any(i["route"] == "review-due" for i in one["items"])   # addressed to employee-2, not to employee-1


def test_evidence_is_the_file_verbatim_or_why_not():
    with _Env():
        s = Subject(SUBJECT_ROOT)
        got = questions.evidence("quote|insurance", s, str(PROBE))
        none = questions.evidence("quote|currency", s, str(PROBE))
        unknown = questions.evidence("quote|insurence", s, str(PROBE))
    raw = (PROBE / "questions" / "evidence" / "knowledge_probe" / "quote%7Cinsurance.md").read_bytes()
    assert got["found"] and got["text"] == raw.decode("utf-8") and got["why"] is None
    assert not none["found"] and "has generated none" in none["why"] and none["text"] is None
    assert not unknown["found"] and "did you mean quote|insurance" in unknown["why"]


def test_the_link_fills_the_forms_fields_and_writes_nothing():
    before = sorted((p, p.stat().st_mtime_ns) for p in PROBE.rglob("*") if p.is_file())
    with _Env():
        rep = questions.link("quote|insurance", "wrong", "A quote includes insurance & a fee.", Subject(SUBJECT_ROOT), str(PROBE))
    assert sorted((p, p.stat().st_mtime_ns) for p in PROBE.rglob("*") if p.is_file()) == before
    parts = urlsplit(rep["url"])
    assert parts.scheme == "https" and parts.path == "/example-org/example-instance/issues/new"
    q = dict(parse_qsl(parts.query))
    assert q["template"] == "answer.yml" and q["key"] == "quote|insurance" and q["owner_unit"] == "ORG-0002"
    assert q["verdict"] == "Wrong" and q["statement"] == "A quote includes insurance & a fee." and "note" not in q
    assert q["evidence"].endswith("/questions/evidence/knowledge_probe/quote%257Cinsurance.md")   # the file's own % kept


def test_a_verdict_outside_the_forms_four_and_an_ambiguous_key_are_refused():
    with _Env():
        s = Subject(SUBJECT_ROOT)
        for args, why in ((("quote|insurance", "maybe", "x"), "verdict 'maybe'"), (("rate|rounding", "wrong", "x"), "name scenario and owner"),
                          (("quote|insurance", "wrong", "x" * questions.URL_MAX), "over 8000"),
                          (("quote|insurance", "wrong", "x", None, "ORG-0001"), "no questionnaire")):
            key, verdict, statement, *rest = args
            try:
                questions.link(key, verdict, statement, s, str(PROBE), *rest)
            except questions.QuestionsError as e:
                assert why in str(e), (args, e)
            else:
                raise AssertionError(f"{args} was not refused")
    srv = mcp_server.Server(mcp_server.Tools(opener=lambda: 1 / 0, as_of=ON.isoformat()))
    for args in ({"key": "quote|insurance", "verdict": "maybe", "statement": "x"}, {"key": "quote|insurance", "verdict": "wrong"},
                 {"handle": "employee-1"}):
        r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "answer_link", "arguments": args}})
        assert r["error"]["code"] == -32602, (args, r)


def test_the_configuration_and_the_template_must_agree():
    with tempfile.TemporaryDirectory() as d:
        inst = _copy(d)
        cfg = inst / "questions.toml"
        good = cfg.read_text(encoding="utf-8")
        tpl = inst / ".github" / "ISSUE_TEMPLATE" / "answer.yml"
        s = Subject(SUBJECT_ROOT)
        cases = ((good.replace('owner = "owner_unit"', 'owner = "owner"'), None, "field id 'owner' (owner)"),
                 (good.replace("I don't know", "Not sure"), None, "verdict label 'Not sure'"),
                 (good.replace('note = "note"\n', ''), None, "[form.fields] note: missing"),
                 (good.replace("https://github.com", "http://github.com"), None, "an https URL"),
                 (good.replace('template = ".github', 'template = "../.github'), None, "without '..'"),
                 (good.replace("format = 1", "format = 99"), None, "format = 99"),
                 (good, tpl.read_text(encoding="utf-8").replace("id: statement", "id: text"), "field id 'statement'"))
        for text, template, why in cases:
            cfg.write_text(text, encoding="utf-8")
            if template is not None:
                tpl.write_text(template, encoding="utf-8")
            with _Env():
                try:
                    questions.link("quote|insurance", "wrong", "x", s, str(inst))
                except (questions.QuestionsError, formats.FormatError) as e:
                    assert why in str(e), (why, e)
                else:
                    raise AssertionError(f"{why}: not refused")
        cfg.unlink()
        try:
            questions.config(str(inst))
        except questions.QuestionsError as e:
            assert "questions.toml: missing" in str(e)
        else:
            raise AssertionError("no questions.toml was not refused")


def test_the_three_tools_answer_over_mcp_from_files_without_the_store():
    """In process the server's own subject is cargo_quote: question_evidence and answer_link name the probe's subject and
    are answered by a child process for it, as any call for another subject is; pending_questions spans the subjects."""
    with _Env():
        srv = mcp_server.Server(mcp_server.Tools(opener=lambda: 1 / 0, as_of=ON.isoformat()))
        calls = (("pending_questions", {"handle": "employee-1"}, "pending_questions-employee-1"),
                 ("question_evidence", {"key": "quote|insurance", "subject": "knowledge_probe"}, "question_evidence-quote_insurance"),
                 ("answer_link", {"key": "quote|insurance", "verdict": "right_with_correction", "statement": "A quote includes no insurance.",
                                  "subject": "knowledge_probe"}, "answer_link-quote_insurance"))
        for tool, args, stem in calls:
            r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}})["result"]
            assert not r.get("isError"), (tool, r["content"][0]["text"])
            assert r["structuredContent"] == _expected(stem), tool
        r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "pending_questions", "arguments": {"handle": "contractor-9"}}})
        assert r["result"]["isError"] and "not issued" in r["result"]["content"][0]["text"]
    for name in ("pending_questions", "question_evidence", "answer_link"):
        tool = next(t for t in mcp_server.TOOLS if t["name"] == name)
        assert tool["_meta"][mcp_server.META_STORE] is False and tool["annotations"]["readOnlyHint"] is True
        assert ("subject" in tool["inputSchema"]["properties"]) == (name != "pending_questions")
    assert mcp_server.VERDICTS == list(questions.VERDICTS)
