"""Route (b), task-0040: the answers whose six-month review falls due, asked again of the handle that
gave them, pre-filled; the answered questionnaire is ingested unchanged, and a confirmation is a new
capture with a new ``on``. Runs the commands on the public example instance, stdlib only."""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import capture  # noqa: E402

ANSWERED = """[questionnaire]
subject = "cargo_quote"
scenario = "S2"
task = "codegen"
owner = "ORG-0002"
[answered]
from = "{handle}"
on = {on}
[[item]]
key = "response|hold_presence"
answer = "held_unscreened only"
nobody_knows = false
note = ""
"""


def _instance(tmp: Path) -> dict:
    subprocess.run([sys.executable, str(ROOT / "tools" / "example_instance.py"), str(tmp / "i")], check=True, capture_output=True)
    env = dict(os.environ, KG_SUBJECT=str(tmp / "i" / "subjects" / "cargo_quote"), KG_REGISTER=str(tmp / "i" / "register"),
               PYTHONDONTWRITEBYTECODE="1")
    env.pop("KG_TODAY", None)
    return env


def _run(env, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "capture.py", *args], cwd=ROOT / "harness", env=env, capture_output=True, text=True)


def test_an_answer_falls_due_six_months_on_and_a_confirmation_is_a_new_capture():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        env = _instance(tmp)
        caps = Path(env["KG_SUBJECT"]) / "captures"
        (tmp / "a.toml").write_text(ANSWERED.format(handle="employee-1", on="2026-11-02"), encoding="utf-8")
        assert _run(env, "ingest", str(tmp / "a.toml")).returncode == 0
        first = caps / "2026-11-02-ORG-0002-employee-1.toml"
        before = first.read_bytes()
        r = _run(env, "due", "--on", "2027-05-01", "--out", str(tmp / "q0"))
        assert r.returncode == 0 and "nothing falls due" in r.stdout and not list((tmp / "q0").glob("*.toml"))
        r = _run(env, "due", "--on", "2027-05-02", "--out", str(tmp / "q"))
        assert r.returncode == 0 and "Review due for employee-1: 1 answer(s)" in r.stdout, r.stdout + r.stderr
        (q,) = list((tmp / "q").glob("*.toml"))
        assert q.name == "questionnaire-due-cargo_quote-employee-1.toml"
        doc = tomllib.loads(q.read_text(encoding="utf-8"))
        assert doc["questionnaire"]["to"] == "employee-1" and doc["questionnaire"]["route"] == "review-due"
        (it,) = doc["item"]
        assert (it["key"], it["answer"], it["earlier"], it["earlier_on"], it["due"]) == (
            "response|hold_presence", "held_unscreened only", "held_unscreened only", dt.date(2026, 11, 2), dt.date(2027, 5, 2))
        # ingested unchanged but for [answered]: a new capture with a new on, the old one untouched
        text = q.read_text(encoding="utf-8").replace('from = ""', 'from = "employee-1"', 1).replace('on = ""', "on = 2027-05-03", 1)
        (tmp / "c.toml").write_text(text, encoding="utf-8")
        r = _run(dict(env, KG_TODAY="2027-05-03"), "ingest", str(tmp / "c.toml"))
        assert r.returncode == 0, r.stderr
        assert first.read_bytes() == before and (caps / "2027-05-03-ORG-0002-employee-1.toml").is_file()
        assert "nothing falls due" in _run(env, "due", "--on", "2027-05-03", "--out", str(tmp / "q2")).stdout
        assert "Review due for employee-1" in _run(env, "due", "--on", "2027-11-03", "--out", str(tmp / "q3")).stdout


def _cap(d: Path, stem: str, handle: str, on: str, value: str, key="response|hold_presence"):
    (d / f"{stem}.toml").write_text(
        f'[capture]\nsubject = "cargo_quote"\nscenario = "S2"\ntask = "codegen"\nowner = "ORG-0002"\nfrom = "{handle}"\n'
        f'on = {on}\nrecord = "captures/{stem}.toml"\n\n[[answer]]\nkey = "{key}"\nvalue = "{value}"\nnote = ""\n', encoding="utf-8")


def test_the_latest_answer_per_handle_and_key_counts_and_a_rejected_one_is_not_re_asked():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        _cap(d, "2026-01-02-ORG-0002-employee-1", "employee-1", "2026-01-02", "old")
        _cap(d, "2026-03-02-ORG-0002-employee-1", "employee-1", "2026-03-02", "new")
        _cap(d, "2026-01-05-ORG-0002-employee-2", "employee-2", "2026-01-05", "theirs")
        due = capture.due_captures(d, dt.date(2026, 8, 1))
        assert [(x["from"], x["value"]) for x in due] == [("employee-2", "theirs")], due
        due = capture.due_captures(d, dt.date(2026, 9, 2))
        assert [(x["from"], x["value"]) for x in due] == [("employee-1", "new"), ("employee-2", "theirs")], due
        (d / "reviews").mkdir()
        (d / "reviews" / "r.toml").write_text('[review]\nby = "employee-3"\non = 2026-04-01\nrecord = "m.md"\n\n[[ruling]]\n'
                                              'assertion = "A:cap:2026-01-05-ORG-0002-employee-2:1@capture"\noutcome = "rejected"\n',
                                              encoding="utf-8")
        assert [x["from"] for x in capture.due_captures(d, dt.date(2026, 9, 2))] == ["employee-1"]


def test_a_withdrawn_handles_answers_go_to_the_owner_unit_and_no_name_is_written():
    item = {"id": "A:cap:x:1@capture", "from": "employee-8", "key": "response|hold_presence", "value": "v", "on": dt.date(2026, 1, 2),
            "record": "captures/x.toml", "owner": "ORG-0002", "subject": "cargo_quote", "scenario": "S2", "task": "codegen",
            "due": dt.date(2026, 7, 2)}
    handles = {"employee-8": {"unit": "ORG-0002", "roles": {"gives"}, "issued": dt.date(2026, 1, 1), "withdrawn": dt.date(2026, 6, 1)}}
    qs = capture.due_questionnaires([item], handles, dt.date(2026, 7, 2))
    assert list(qs) == ["ORG-0002"] and "the owner unit answers in its place" in qs["ORG-0002"]
    assert tomllib.loads(qs["ORG-0002"])["questionnaire"]["to"] == "ORG-0002"
    assert list(capture.due_questionnaires([item], {}, dt.date(2026, 7, 2))) == ["employee-8"]
    # the questionnaire carries handles, units and the answer; the register's names are nowhere in it
    for text in qs.values():
        assert "stand-in" not in text and "John" not in text


def test_a_register_link_with_an_elicited_block_is_listed_by_its_review_due():
    with tempfile.TemporaryDirectory() as t:
        reg = Path(t)
        (reg / "relationships").mkdir()
        (reg / "relationships" / "x.toml").write_text(
            '[[link]]\nid = "REL-09001"\nsource = "A"\ntarget = "B"\nreview_due = 2027-01-01\n'
            'elicited = { from = "employee-1", on = 2026-11-02, record = "capture:2026-11-02-ORG-0002-employee-1" }\n\n'
            '[[link]]\nid = "REL-09002"\nsource = "A"\ntarget = "C"\nreview_due = 2026-12-01\n', encoding="utf-8")
        assert capture.due_links(reg, dt.date(2026, 12, 31)) == []
        (ln,) = capture.due_links(reg, dt.date(2027, 1, 1))
        assert (ln["id"], ln["from"], ln["due"]) == ("REL-09001", "employee-1", dt.date(2027, 1, 1))
