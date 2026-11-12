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


def test_b_x2_realisers_refuses_a_kind_with_no_such_walk():
    import register_impact as ri
    try:
        ri.walk("APP-0002", "realisers")
    except ri.ImpactError as e:
        assert "realisers walk starts from" in str(e), e
    else:
        raise AssertionError("realisers from an application must be refused")
    assert ri.walk("CAP-0001", "realisers")["walk"] == "realisers"   # a capability still answers


def test_b_x3_a_sub_gate_counts_the_keys_reached():
    import re
    src = (HARNESS / "gate_cli.py").read_text(encoding="utf-8")
    assert "keys reached" in src
    why = "all 3 required keys verified or approved, none flagged"
    assert re.sub(r"\b(\d+) required keys?\b", lambda m: f"the {m.group(1)} keys reached", why).startswith("all the 3 keys reached")


def test_b_x7_help_is_not_an_output_directory():
    for tool in ("check_gate_after_change.py", "check_trace_walkthrough.py", "check_lint_gaps.py"):
        r = _run([str(ROOT / "tools" / tool), "--help"])
        assert r.returncode != 2 or r.stdout or r.stderr
        assert not (ROOT / "--help").exists(), tool


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
