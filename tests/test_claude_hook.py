"""Task-0099: the gate as a fail-closed Claude Code hook (instance/ci/claude/). The mapping (exit 1
and 2 both block, mandatory; only 2 lets through, advisory), the stage transitions, the refusal of a
report not for the task class, and the settings snippets. The real knowgov-gate.sh is run for a
missing subject and an unreachable store; PROCEED and BLOCKED on a live rdflib store run where
KG_HOOK_LIVE=1 (harness.yml's rdflib job), against a stub gate everywhere else."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "instance" / "ci" / "claude"
SCRIPT = DIR / "knowgov_hook.py"
_spec = importlib.util.spec_from_file_location("knowgov_hook", SCRIPT)
hook = importlib.util.module_from_spec(_spec)
sys.modules["knowgov_hook"] = hook
_spec.loader.exec_module(hook)

PLAN = {"hook_event_name": "PreToolUse", "tool_name": "ExitPlanMode", "tool_input": {}, "cwd": str(ROOT)}
PUSH = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push -u origin topic"}, "cwd": str(ROOT)}

STUB = """#!/bin/sh
# a stand-in for knowgov-gate.sh: writes the report FAKE_* describes and exits FAKE_RC
touch "$FAKE_MARK"
[ -n "${FAKE_NOREPORT:-}" ] || cat > "$KG_REPORT" <<EOF
{"tool": "knowgov gate", "subject": "s", "scenario": "S", "task": "${FAKE_TASK:-$KG_TASK}", "verdict": "$FAKE_VERDICT",
 "as_of": "2026-10-30", "threshold": "blocker", "exit_code": ${FAKE_EXIT:-$FAKE_RC},
 "findings": [{"severity": "blocker", "kind": "key", "key": "k.one", "message": "absent"}]}
EOF
exit "$FAKE_RC"
"""


def _env(**kw) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("KG_", "FAKE_", "CLAUDE_"))}
    env["KG_CLOCK"] = "pinned"
    env.update(kw)
    return env


def _hook(event, *args, env=None, raw=None) -> subprocess.CompletedProcess:
    data = raw if raw is not None else json.dumps(event)
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=data, capture_output=True, text=True,
                          env=env or _env(), timeout=600)


def _stub(tmp: Path) -> Path:
    kg = tmp / "kg"
    (kg / "instance" / "ci").mkdir(parents=True, exist_ok=True)
    (kg / "instance" / "ci" / "knowgov-gate.sh").write_text(STUB, encoding="utf-8")
    return kg


def _fake(tmp, event, rc, verdict, *extra, **kw):
    kg = _stub(tmp)
    mark = tmp / "called"
    mark.unlink(missing_ok=True)
    env = _env(FAKE_RC=str(rc), FAKE_VERDICT=verdict, FAKE_MARK=str(mark), **kw)
    p = _hook(event, "gate", "--task", "codegen", "--knowgov", str(kg), "--instance", str(tmp), *extra, env=env)
    return p, mark.exists()


def test_the_mapping_blocks_on_1_and_2_and_only_the_advisory_profile_lets_2_through():
    assert hook.decide(0) == hook.Decision(0)
    for rc in (1, 2, 3, 127, -9):
        assert hook.decide(rc).exit_code == 2, rc
    assert "BLOCKED by a finding" in hook.decide(1).reason and "Route to approval" in hook.decide(1).reason
    assert "unavailable" in hook.decide(2).reason and "Fail-closed" in hook.decide(2).reason
    assert hook.decide(1, advisory=True).exit_code == 2           # doc-0004's adapter: findings still block
    adv = hook.decide(2, advisory=True)
    assert adv.exit_code == 0 and "FAIL-OPEN" in adv.output["systemMessage"]
    assert hook.HOOK_BLOCK == 2   # Claude Code blocks a PreToolUse call on exit 2 only


def test_proceed_lets_the_action_through_and_blocked_stops_it_naming_the_finding_and_route():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        p, called = _fake(tmp, PLAN, 0, "PROCEED")
        assert called and p.returncode == 0 and not p.stderr, (p.returncode, p.stderr)
        p, called = _fake(tmp, PUSH, 1, "BLOCKED")
        assert called and p.returncode == 2, p.returncode
        assert "knowgov gate at push: BLOCKED by a finding" in p.stderr and "k.one" in p.stderr and "Route to approval" in p.stderr, p.stderr
        p, _ = _fake(tmp, PUSH, 1, "BLOCKED", "--advisory")
        assert p.returncode == 2, "the advisory profile still blocks on a finding"


def test_a_report_not_for_the_task_class_is_refused():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for kw, why in [({"FAKE_TASK": "keys"}, "agent-chosen key set"), ({"FAKE_TASK": "design"}, "requires 'codegen'"),
                        ({"FAKE_NOREPORT": "1"}, "without a readable report"), ({"FAKE_EXIT": "1"}, "disagrees")]:
            for extra in ((), ("--advisory",)):
                p, _ = _fake(tmp, PLAN, 0, "PROCEED", *extra, **kw)
                assert p.returncode == 2 and "refused" in p.stderr and why in p.stderr, (kw, extra, p.stderr)
        p = _hook(PLAN, "gate", "--task", "keys")
        assert p.returncode == 2 and "not a task class" in p.stderr
        p = _hook(PLAN, "gate", "--task", "codegen", "--task-for", "plan=keys")
        assert p.returncode == 2


def test_only_stage_transitions_call_the_gate():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for ev in [{"tool_name": "Edit", "tool_input": {"file_path": "spec.md"}},
                   {"tool_name": "Write", "tool_input": {"file_path": "a.py"}},
                   {"tool_name": "Bash", "tool_input": {"command": "ls -la"}},
                   {"tool_name": "Bash", "tool_input": {"command": "echo git pushed"}},
                   {"tool_name": "Bash", "tool_input": {"command": "git status"}}]:
            p, called = _fake(tmp, ev, 1, "BLOCKED")
            assert p.returncode == 0 and not called, ev
        for cmd in ["git push", "cd x && git -C sub push origin main", "git -c a=b push --force-with-lease"]:
            p, called = _fake(tmp, {"tool_name": "Bash", "tool_input": {"command": cmd}}, 1, "BLOCKED")
            assert p.returncode == 2 and called, cmd
        # a commit is the "spec committed" transition only when it carries a spec file
        repo = tmp / "repo"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
        g("init", "-q")
        (repo / "a.py").write_text("x = 1\n")
        g("add", "a.py")
        commit = {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'a change'"}, "cwd": str(repo)}
        p, called = _fake(tmp, commit, 1, "BLOCKED")
        assert p.returncode == 0 and not called
        (repo / "docs").mkdir()
        (repo / "docs" / "spec.md").write_text("# spec\n")
        g("add", "docs/spec.md")
        p, called = _fake(tmp, commit, 1, "BLOCKED")
        assert p.returncode == 2 and called and "at spec" in p.stderr, p.stderr
        p, called = _fake(tmp, commit, 0, "PROCEED", "--task-for", "spec=codegen")
        assert p.returncode == 0 and called
        assert hook.transition({"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": str(tmp / "none")}, ["spec.md"]) == "spec"


def test_an_unreadable_event_or_a_missing_checkout_blocks():
    p = _hook(None, "gate", "--task", "codegen", raw="not json")
    assert p.returncode == 2 and "unreadable hook event" in p.stderr
    with tempfile.TemporaryDirectory() as t:
        p = _hook(PLAN, "gate", "--task", "codegen", env=_env(KG_HOME=t))
        assert p.returncode == 2 and "no knowgov checkout" in p.stderr, p.stderr
        p = _hook(PLAN, "gate", "--task", "codegen", "--instance", str(Path(t) / "none"))
        assert p.returncode == 2 and "no instance" in p.stderr, p.stderr


def _real(event, **kw):
    env = _env(KG_AS_OF="record", KG_SCENARIO="S1", **kw)
    return _hook(event, "gate", "--task", "codegen", "--instance", str(ROOT), env=env)


def test_the_real_gate_with_a_missing_subject_blocks_as_unavailable():
    p = _real(PLAN, KG_SUBJECT=str(ROOT / "subjects" / "no_such_subject"), KG_STORE="rdflib")
    assert p.returncode == 2 and "the gate is unavailable (exit 2)" in p.stderr and "Fail-closed" in p.stderr, p.stderr


def test_the_real_gate_with_an_unreachable_store_blocks_and_the_advisory_profile_lets_it_through():
    kw = dict(KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"), KG_STORE="neo4j", KG_NEO4J_URI="bolt://127.0.0.1:9")
    p = _real(PUSH, **kw)
    assert p.returncode == 2 and "the gate is unavailable (exit 2)" in p.stderr, p.stderr
    p = _hook(PUSH, "gate", "--task", "codegen", "--advisory", "--instance", str(ROOT), env=_env(KG_AS_OF="record", **kw))
    assert p.returncode == 0 and "FAIL-OPEN" in json.loads(p.stdout)["systemMessage"], (p.returncode, p.stdout)


def test_live_proceed_and_blocked_on_an_rdflib_store():
    if os.environ.get("KG_HOOK_LIVE") != "1":
        return   # harness.yml's rdflib job sets it, with the pins installed
    kw = dict(KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"), KG_STORE="rdflib")
    p = _real(PLAN, **kw)
    assert p.returncode == 0 and not p.stderr, (p.returncode, p.stderr)
    p = _hook(PUSH, "gate", "--task", "codegen", "--instance", str(ROOT), env=_env(KG_AS_OF="record", KG_SCENARIO="S2", **kw))
    assert p.returncode == 2 and "BLOCKED by a finding" in p.stderr and "BLOCKED on cargo_quote S2" in p.stderr, p.stderr


def test_run_maps_any_contract_check_the_same_way():
    for rc, want in [(0, 0), (1, 2), (2, 2), (5, 2)]:
        p = _hook(PLAN, "run", "--check", "vendored", "--", "sh", "-c", f"echo why >&2; exit {rc}")
        assert p.returncode == want, (rc, p.returncode)
    p = _hook(PLAN, "run", "--advisory", "--", "sh", "-c", "exit 2")
    assert p.returncode == 0 and "FAIL-OPEN" in p.stdout
    p = _hook(PLAN, "run", "--", "sh", "-c", "cat > /dev/null; exit 1")
    assert p.returncode == 2 and "BLOCKED by a finding" in p.stderr


def test_the_settings_snippets_fail_closed_and_only_the_managed_one_locks():
    load = lambda n: json.loads((DIR / n).read_text(encoding="utf-8"))  # noqa: E731
    repo, managed, adv = load("settings.json"), load("managed-settings.json"), load("settings.advisory-fail-open.json")
    for name, s in [("repo", repo), ("managed", managed), ("advisory", adv)]:
        entries = s["hooks"]["PreToolUse"]
        matchers = {m for e in entries for m in e["matcher"].split("|")}
        assert matchers == {"ExitPlanMode", "Bash"}, (name, matchers)   # never Edit or Write: not on every edit
        for e in entries:
            for h in e["hooks"]:
                assert h["type"] == "command" and h["args"][0].endswith("knowgov_hook.py") and h["args"][1:4] == ["gate", "--task", "codegen"]
                assert h["timeout"] == 600
                assert ("--advisory" in h["args"]) == (name == "advisory"), name
                assert h.get("onFailure") == (None if name == "advisory" else "block"), name
    assert managed["allowManagedHooksOnly"] is True
    assert "allowManagedHooksOnly" not in repo and "allowManagedHooksOnly" not in adv


def test_the_managed_fragment_carries_the_hook_and_the_mcp_lock_is_its_own_opt_in():
    # task-0107: the hook is the enforcement; the MCP allowlist is the organisation's tool policy
    load = lambda n: json.loads((DIR / n).read_text(encoding="utf-8"))  # noqa: E731
    repo, managed, mcp = load("settings.json"), load("managed-settings.json"), load("managed-mcp-allowlist.json")
    assert set(managed) == {"allowManagedHooksOnly", "hooks"}, sorted(managed)
    assert mcp == {"allowManagedMcpServersOnly": True, "allowedMcpServers": [{"serverName": "knowgov"}]}, mcp
    for s in (repo, managed):
        assert not {"allowManagedMcpServersOnly", "allowedMcpServers"} & set(s)
    hooks = lambda s: [h for e in s["hooks"]["PreToolUse"] for h in e["hooks"]]  # noqa: E731
    (r,), (m,) = hooks(repo), hooks(managed)
    # the same command; managed settings carry no repository env, so they name the checkout with --knowgov
    assert m["command"] == r["command"] and m["args"][:len(r["args"])] == r["args"], (m, r)
    assert m["args"][len(r["args"]):] == ["--knowgov", repo["env"]["KG_HOME"]], m["args"]
    assert {k: v for k, v in m.items() if k != "args"} == {k: v for k, v in r.items() if k != "args"}


def test_the_header_cites_doc_0004_as_superseded_and_the_readme_places_each_file():
    head = hook.__doc__
    assert "doc-0004" in head and "Exit codes" in head and "doc-0014" in head and "Supersedes" in head
    assert "20-of-20" not in SCRIPT.read_text(encoding="utf-8")
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    sec = readme[readme.index("## A fail-closed hook for Claude Code"):]
    for s in ["/etc/claude-code/managed-settings.d/", "/Library/Application Support/ClaudeCode/", ".claude/settings.json",
              "settings.advisory-fail-open.json", "only the managed", "one store per worktree",
              "managed-mcp-allowlist.json", "opt-in", "replace the lists of every lower settings source",
              "Merge its entries", "hook stays mandatory"]:
        assert s in sec, s


def test_unavailable_takes_its_own_route_and_the_summary_names_the_owner():
    """Task-0102, folding in task-0099's notes: ``decide`` takes the unavailable route as it takes the
    finding's, the gate's wording by default; the summary names each finding's owner and its route."""
    assert hook.UNAVAILABLE_ROUTE in hook.decide(2).reason
    own = hook.decide(2, unavailable_route="Route: fix the thing.")
    assert own.exit_code == 2 and "Route: fix the thing." in own.reason and hook.UNAVAILABLE_ROUTE not in own.reason
    assert "Route: fix the thing." not in hook.decide(1, unavailable_route="Route: fix the thing.").reason
    rep = {"verdict": "BLOCKED", "subject": "s", "scenario": "S2", "task": "codegen", "as_of": "2026-10-30", "threshold": "blocker",
           "findings": [{"severity": "blocker", "kind": "key", "key": "k|p", "message": "k|p is absent", "owner": "ORG-0002",
                         "route": "python harness/capture.py questionnaire ..."},
                        {"severity": "blocker", "kind": "key", "key": "k|q", "message": "k|q is absent", "owner": None, "route": "r2"},
                        {"severity": "blocker", "kind": "suspect_derived", "key": None, "message": "d1 used a1"}]}
    text = hook._summary(rep)
    assert "k|p is absent (owner ORG-0002)" in text and "k|q is absent (owner none in the register map)" in text
    assert "d1 used a1\n" in text + "\n" and "d1 used a1 (owner" not in text
    assert "  route: python harness/capture.py questionnaire ..." in text and "  route: r2" in text
    p = _hook(PLAN, "run", "--unavailable-route", "Route: mine.", "--", "sh", "-c", "exit 2")
    assert p.returncode == 2 and "Route: mine." in p.stderr and hook.UNAVAILABLE_ROUTE not in p.stderr
