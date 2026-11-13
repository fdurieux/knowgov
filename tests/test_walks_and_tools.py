"""task-0314 (doc-0037 §5, 0.9.x fixes): the walks and tools' small faults, each held. Stand-in subject only; no network."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))


def _run(args, **env):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=ROOT, timeout=120,
                          env={**os.environ, "KG_CLOCK": "pinned", **env})


def test_b_x1_p1_an_unloadable_subject_is_exit_2_in_one_line_never_a_traceback():
    for tool, extra in (("upward.py", ["key", "a|b"]), ("register_nodes.py", []), ("proposal_impact.py", [])):
        r = _run([str(HARNESS / tool), *extra], KG_SUBJECT="no_such_subject_dir")
        assert r.returncode == 2, (tool, r.returncode, r.stderr[-300:])
        assert "Traceback" not in r.stderr and r.stderr.strip().count("\n") == 0 and "cannot run" in r.stderr, (tool, r.stderr)


def _store(scenario):
    """A rdflib store with ``scenario`` loaded, or a skip (rdflib is not installed; the subject is not CargoQuote)."""
    from tests._skip import need_rdflib, skip
    rdf = need_rdflib()
    import gate_cli
    from subject import SUBJECT
    if SUBJECT.id != "cargo_quote":
        skip("register-rows", f"the subject is {SUBJECT.id}, these checks are CargoQuote's")
    st = rdf.RdflibStore(path="")
    gate_cli._load(st, scenario)
    return st, SUBJECT


def _sub(st, SUBJECT, scenario, keys, **kw):
    import gate_cli
    from tasks import TASKS
    return gate_cli.evaluate(st, subject=SUBJECT.id, scenario=scenario, task="keys", spec=dict(TASKS["codegen"], keys=keys),
                             threshold="blocker", baseline=None, loaded=True, as_of="record", **kw)


def test_b_x3_r1_a_sub_gate_words_proceed_blocked_and_qualified_and_gate_verdict_keeps_its_own():
    st, SUBJECT = _store("S4")
    ok, bad = ["shipper_id|present", "weight_kg|min"], "QuoteAPI|on_screening_outage"   # approved, approved; disputed
    proceed = _sub(st, SUBJECT, "S4", ok, sub_gate=True)
    assert proceed["verdict"] == "PROCEED" and proceed["why"] == "all of the 2 keys reached verified or approved, none flagged", proceed["why"]
    blocked = _sub(st, SUBJECT, "S4", ok + [bad], sub_gate=True)
    assert blocked["verdict"] == "BLOCKED" and blocked["why"].startswith("1 of the keys reached at a blocking level: " + bad), blocked["why"]
    assert "(s)" not in blocked["why"] and "reached(" not in blocked["why"], blocked["why"]
    # the share form (BLOCKED by the bar) and QUALIFIED, on a class that does not block the disputed key
    import gate_cli
    from tasks import TASKS
    for share, verdict, why in ((0.0, "BLOCKED", "1 of the 3 keys reached (33%) are below verified; the bar is 0%"),
                                (0.5, "QUALIFIED", "1 key(s) below verified, 0 flagged: " + bad)):
        got = gate_cli.evaluate(st, subject=SUBJECT.id, scenario="S4", task="keys", threshold="blocker", baseline=None, loaded=True,
                                as_of="record", sub_gate=True,
                                spec=dict(TASKS["codegen"], keys=ok + [bad], block_levels=[], max_unverified_share=share))
        assert (got["verdict"], got["why"]) == (verdict, why), got["why"]
    # gate_verdict's own keys, and evidence_bundle's: the gate's words, not the sub-gate's
    own = _sub(st, SUBJECT, "S4", ok)
    assert own["why"] == "all 2 required keys verified or approved, none flagged", own["why"]


def test_a_f6_r3_a_key_finding_carries_its_conflict_ids_matched_on_its_own_assertions():
    import gate_cli
    st, SUBJECT = _store("S4")
    rep = _sub(st, SUBJECT, "S4", ["QuoteAPI|on_screening_outage"])
    f = next(f for f in rep["findings"] if f["kind"] == "key")
    assert len(f["related"]) == 4 and all(r.startswith("gap:conflict:QuoteAPI|on_screening_outage:") for r in f["related"]), f["related"]
    res = {"conflicts": [{"id": "gap:conflict:Quote|status:v2:A:x~A:y"}, {"id": "gap:conflict:Quote|status:A:p~A:q"}],
           "keys": {"Quote|status": {"assertions": [{"id": "A:p"}, {"id": "A:q"}]}}}
    assert gate_cli.conflict_ids(res, "Quote|status") == ["gap:conflict:Quote|status:A:p~A:q"], "a longer key's conflict is not this key's"


def test_b_x6_key_nodes_answers_mapped_false_for_a_held_unmapped_key_and_refuses_an_unknown_one():
    import mcp_server
    import trace
    st, SUBJECT = _store("S1")
    held = sorted({k["key"] for k in st.held_keys()} - trace.known_keys())
    assert held, "S1 holds keys that no map row or task names"

    class Held(mcp_server.ReadOnlyStore):
        def release(self) -> None:
            pass
    tools = mcp_server.Tools(opener=lambda: Held(st), as_of="2026-10-30")
    got = tools.key_nodes({"key": held[0]})
    assert got["mapped"] is False and got["rows"] == [] and got["key"] == held[0], got
    try:
        tools.key_nodes({"key": "Nothing|held"})
    except mcp_server.ToolError as e:
        assert "no key of" in str(e)
    else:
        raise AssertionError("an unknown key is refused")


def test_n2_the_suspect_block_names_the_scenario_and_version_it_was_read_against():
    import mcp_server
    st, SUBJECT = _store("S1")

    class Held(mcp_server.ReadOnlyStore):
        def release(self) -> None:
            pass
    tools = mcp_server.Tools(opener=lambda: Held(st), as_of="2026-10-30")
    got = tools._ledger_suspect({"id": "D-1", "sha256": "0" * 64, "assertions": []})
    assert got["status"] == "read" and "S1" in got["reason"] and "version" in got["reason"], got


def test_a_f10_the_mcp_answer_and_trace_name_the_near_key_and_trace_names_each_keys_own():
    import mcp_server
    import trace
    near = "weight_kg|mn"
    assert "no register map row" in mcp_server._unmodelled(near, "unknown") and "did you mean weight_kg|min" in mcp_server._unmodelled(near, "unknown")
    assert mcp_server._unmodelled("weight_kg|min", "unknown") == "" and mcp_server._unmodelled(near, "approved") == ""
    try:
        trace._key_ids(None, ["weight_kg|mn", "shipper_id|presnt"], trace.known_keys())
    except trace.CannotRun as e:
        assert "did you mean weight_kg|min for weight_kg|mn?" in str(e) and "did you mean shipper_id|present for shipper_id|presnt?" in str(e), str(e)
    else:
        raise AssertionError("unknown keys are refused")


def test_p1_a_refused_task_policy_is_exit_2_in_one_line_in_upward_and_proposal_impact():
    import shutil
    import tempfile
    from tests.test_task_policy import CODEGEN_LEVELS, _env
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "cargo_quote"
        shutil.copytree(ROOT / "subjects" / "cargo_quote", root, ignore=shutil.ignore_patterns("__pycache__"))
        toml = root / "subject.toml"
        toml.write_text(toml.read_text(encoding="utf-8").replace(CODEGEN_LEVELS, 'block_levels = ["nonsense"]', 1), encoding="utf-8")
        for argv in (["upward.py", "key", "weight_kg|min"], ["proposal_impact.py", "--no-store"]):
            r = subprocess.run([sys.executable, str(HARNESS / argv[0]), *argv[1:]], capture_output=True, text=True, env=_env(root), timeout=120)
            assert r.returncode == 2 and "Traceback" not in r.stderr and "cannot run" in r.stderr and "TaskPolicyError" in r.stderr, (argv, r.returncode, r.stderr[-300:])


MAIN_SCRIPTS_THAT_READ_STDIN = {"instance/ci/claude/attestation_paths.py", ".claude/hooks/protected_paths.py"}   # hooks: stdin JSON, fail-closed


def test_b_x7_r5_help_exits_0_prints_and_creates_nothing_in_every_main_script():
    import tempfile
    scripts = [p for d in ("tools", "harness", "demo/app", "demo/tools", "instance/ci", "instance/ci/claude", ".claude/hooks")
               for p in sorted((ROOT / d).glob("*.py")) if '__main__' in p.read_text(encoding="utf-8")]
    scripts = [p for p in scripts if str(p.relative_to(ROOT)) not in MAIN_SCRIPTS_THAT_READ_STDIN]
    assert len(scripts) > 60, len(scripts)   # able to fail: the scan found the scripts
    bad = []
    for p in scripts:
        with tempfile.TemporaryDirectory() as td:
            try:
                r = subprocess.run([sys.executable, str(p), "--help"], cwd=td, capture_output=True, text=True, timeout=60,
                                   env={**os.environ, "KG_CLOCK": "pinned", "PYTHONDONTWRITEBYTECODE": "1"})
                rc, tb = r.returncode, "Traceback" in r.stderr
            except subprocess.TimeoutExpired:
                rc, tb = "timeout", False
            if rc != 0 or tb or os.listdir(td):
                bad.append((str(p.relative_to(ROOT)), rc, os.listdir(td)[:2]))
    assert bad == [], bad


def test_a_f10_a_near_key_is_offered():
    import key_rule
    assert key_rule.did_you_mean("weight_kg|mn", {"weight_kg|min", "a|b"}) == " (did you mean weight_kg|min?)"
    assert key_rule.did_you_mean("zzz|zzz", {"weight_kg|min"}) == ""


def test_r_t2_the_pages_thread_walk_has_capability_and_entity_buckets():
    sys.path.insert(0, str(ROOT / "demo"))
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import register_view
    w = register_view.impact("PROC-0001", "thread")
    assert "capabilities" in w["reached"] and "entities" in w["reached"], list(w["reached"])
    assert "capabilities" not in register_view.impact("PROC-0001", "dependants")["reached"]
