"""task-0339 (task-0334's residues, decision-0039 §3.1): the guard counts a KG_SUBJECTS root outside the checkout.

R1: `instance_register.unnamed` tested KG_SUBJECT only, so with KG_SUBJECTS at an instance's subjects root and
KG_SUBJECT and KG_REGISTER unset, the MCP reader and the page started and answered from demo/register. Now they
refuse at start, exit 2, naming KG_REGISTER; with it set they answer from the instance's register. `list_subjects`
names each id once. R2: `tools/check_subject.py` refuses an instance subject with no register named; so does the
lighthouse collection's child."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import example_instance  # noqa: E402
import test_instance_register as base  # noqa: E402

LINE = "KG_REGISTER is unset and the subject"


def _inst() -> Path:
    return base._instance()


def _subjects() -> Path:
    return _inst() / "subjects"


def _run(args, stdin=None, **env):
    e = base._env(**env)
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, env=e, capture_output=True, text=True,
                       input=stdin, stdin=None if stdin is not None else subprocess.DEVNULL, timeout=300)
    return r.returncode, r.stdout, r.stderr


def _rpc(calls: list[tuple[str, dict]], **env) -> list[dict]:
    msgs = [{"jsonrpc": "2.0", "id": 0, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"}]
    for i, (name, args) in enumerate(calls, 1):
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}})
    code, out, err = _run([ROOT / "harness" / "mcp_server.py"], stdin="\n".join(map(json.dumps, msgs)) + "\n", **env)
    assert code == 0, (code, err[-400:])
    got = {m["id"]: m for m in map(json.loads, filter(None, out.splitlines())) if "id" in m}
    return [got[i] for i in range(1, len(calls) + 1)]


def _text(m: dict) -> dict:
    return json.loads(m["result"]["content"][0]["text"])


def test_the_helper_counts_a_subjects_root_outside_the_checkout():
    import instance_register
    why = instance_register.unnamed({"KG_SUBJECTS": str(_subjects())})
    assert why and LINE in why and str(_subjects().resolve()) in why, why
    assert instance_register.unnamed({"KG_SUBJECTS": f"{ROOT / 'subjects'},{_subjects()}"}), "any root of the list"
    assert instance_register.unnamed({"KG_SUBJECTS": str(_subjects()), "KG_REGISTER": str(_inst() / "register")}) is None
    assert instance_register.unnamed({"KG_SUBJECTS": str(ROOT / "subjects")}) is None
    assert instance_register.unnamed({}) is None


def test_the_reader_and_the_page_refuse_to_start_on_an_instances_subjects_root_alone():
    """AC 1: on main both started and answered from demo/register."""
    for name, args in (("mcp stdio", [ROOT / "harness" / "mcp_server.py"]),
                       ("mcp http", [ROOT / "harness" / "mcp_server.py", "--http", "--port", "0"]),
                       ("page", [ROOT / "demo" / "app" / "server.py"])):
        code, out, err = _run(args, KG_SUBJECTS=str(_subjects()))
        assert code == 2 and LINE in err and "KG_REGISTER" in err, (name, code, out[-200:], err[-400:])


def test_with_it_named_the_reader_answers_from_the_instances_register():
    """AC 1: the repro: APP-0002 renamed in the instance's register; the answer carries the instance's name."""
    reg = _inst() / "register"
    f = reg / "applications" / "APP-0002.toml"
    f.write_text(f.read_text(encoding="utf-8").replace('name = "QuoteAPI"', 'name = "InstanceQuoteAPI"'), encoding="utf-8")
    r = _rpc([("register_impact", {"node": "APP-0002", "subject": "cargo_quote"})],
             KG_SUBJECTS=str(_subjects()), KG_REGISTER=str(reg))[0]
    assert "error" not in r and not r["result"].get("isError"), r
    body = r["result"]["content"][0]["text"]
    assert "InstanceQuoteAPI" in body and "QuoteAPI\"" not in body.replace("InstanceQuoteAPI", ""), body[:500]


def test_list_subjects_names_each_id_once_with_one_default():
    """AC 2: the instance's cargo_quote and the checkout's own were both listed, both default."""
    r = _rpc([("list_subjects", {})], KG_SUBJECTS=str(_subjects()), KG_REGISTER=str(_inst() / "register"))[0]
    subs = _text(r)["subjects"]
    ids = [s["id"] for s in subs]
    assert len(ids) == len(set(ids)), ids
    assert sum(1 for s in subs if s["default"]) == 1, subs


def test_check_subject_refuses_an_instance_subject_with_no_register_named():
    """AC 3: on main it checked against demo/register."""
    subj = _subjects() / "cargo_quote"
    code, out, err = _run([ROOT / "tools" / "check_subject.py", subj, "--json"])
    assert code == 2 and LINE in err and "KG_REGISTER" in err and out == "", (code, out[-200:], err[-400:])
    code, out, err = _run([ROOT / "tools" / "check_subject.py", subj, "--json", "--register", _inst() / "register"])
    assert code in (0, 1) and LINE not in err, (code, err[-300:])
    code, out, err = _run([ROOT / "tools" / "check_subject.py", subj, "--json"], KG_REGISTER=str(_inst() / "register"))
    assert code in (0, 1) and LINE not in err, (code, err[-300:])


def test_the_lighthouse_collection_refuses_an_instance_subject_with_no_register_named():
    code, out, err = _run([ROOT / "tools" / "lighthouse_evidence.py", tempfile.mkdtemp(prefix="kg-lh-"), "--child", tempfile.mkdtemp(prefix="kg-lh-c-")],
                          KG_SUBJECT=str(_subjects() / "cargo_quote"))
    assert code == 2 and LINE in err, (code, out[-200:], err[-400:])


def test_subjects_inside_the_checkout_are_unchanged():
    """AC 4."""
    import instance_register
    assert instance_register.unnamed({"KG_SUBJECTS": str(ROOT / "subjects")}) is None
    code, out, err = _run([ROOT / "tools" / "check_subject.py", ROOT / "subjects" / "cargo_quote", "--json"])
    assert code in (0, 1) and LINE not in err, (code, err[-300:])
