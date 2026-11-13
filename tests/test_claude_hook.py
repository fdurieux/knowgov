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

from tests._skip import skip  # noqa: E402

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



def test_git_on_a_word_boundary_and_a_commit_that_stages_a_spec_are_transitions():
    """task-0204 (doc-0030 P2): /usr/bin/git, bash -c and a quote before git are the same git; a commit whose
    own command stages or names a spec path, or stages broadly while one is changed, is the spec transition
    before it runs; a command that cannot be read fails closed."""
    t = lambda cmd, cwd: hook.transition({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(cwd)}, ["spec.md"])  # noqa: E731
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
        g("init", "-q")
        (repo / "a.py").write_text("x = 1\n")
        (repo / "docs").mkdir()
        (repo / "docs" / "spec.md").write_text("# spec\n")
        for cmd in ["/usr/bin/git push", "bash -c 'git push origin main'", "sh -c \"cd x; git -C y push\"", "(git push)"]:
            assert t(cmd, repo) == "push", cmd
        assert t("echo gitpush; ls", repo) is None
        assert t("git commit -m 'only code' a.py", repo) is None
        for cmd in ["git add docs/spec.md && git commit -m s", "git commit -m s docs/spec.md", "/usr/bin/git commit -m s -- docs/spec.md",
                    "git add . && git commit -m s", "git add docs && git commit -m s", "git add -A && git commit -m s",
                    "bash -c 'git add docs/spec.md; git commit -m s'", "git add 'docs/*.md' && git commit -m s",
                    "git commit -m \"unbalanced"]:
            assert t(cmd, repo) == "spec", cmd
        assert t("git add a.py && git commit -m code", repo) is None


def test_an_unreadable_event_or_a_missing_checkout_blocks():
    p = _hook(None, "gate", "--task", "codegen", raw="not json")
    assert p.returncode == 2 and "unreadable hook event" in p.stderr
    with tempfile.TemporaryDirectory() as t:
        p = _hook(PLAN, "gate", "--task", "codegen", env=_env(KG_HOME=t))
        assert p.returncode == 2 and "no knowgov checkout" in p.stderr, p.stderr
        p = _hook(PLAN, "gate", "--task", "codegen", "--instance", str(Path(t) / "none"))
        assert p.returncode == 2 and "no instance" in p.stderr, p.stderr


# the checkout as its own instance has no register/ beside its subjects: it names the public one, as an instance
# names its own; the hook passes <instance>/register only when none is named (task-0334)
REGISTER = str(ROOT / "demo" / "register")


def _real(event, **kw):
    env = _env(KG_AS_OF="record", KG_SCENARIO="S1", KG_REGISTER=REGISTER, **kw)
    return _hook(event, "gate", "--task", "codegen", "--instance", str(ROOT), env=env)


def test_the_real_gate_with_a_missing_subject_blocks_as_unavailable():
    p = _real(PLAN, KG_SUBJECT=str(ROOT / "subjects" / "no_such_subject"), KG_STORE="rdflib")
    assert p.returncode == 2 and "the gate is unavailable (exit 2)" in p.stderr and "Fail-closed" in p.stderr, p.stderr


def test_the_real_gate_with_an_unreachable_store_blocks_and_the_advisory_profile_lets_it_through():
    """A gate asked to publish (KG_PUBLISH=1) needs the configured store: unreachable, it cannot run. By
    default (decision-0017) the gate computes in its own process and does not need it."""
    kw = dict(KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"), KG_STORE="neo4j", KG_NEO4J_URI="bolt://127.0.0.1:9", KG_PUBLISH="1")
    p = _real(PUSH, **kw)
    assert p.returncode == 2 and "the gate is unavailable (exit 2)" in p.stderr, p.stderr
    p = _hook(PUSH, "gate", "--task", "codegen", "--advisory", "--instance", str(ROOT), env=_env(KG_AS_OF="record", KG_REGISTER=REGISTER, **kw))
    assert p.returncode == 0 and "FAIL-OPEN" in json.loads(p.stdout)["systemMessage"], (p.returncode, p.stdout)


def test_live_proceed_and_blocked_on_an_rdflib_store():
    if os.environ.get("KG_HOOK_LIVE") != "1":
        skip("hook-live", "KG_HOOK_LIVE is not 1; harness.yml's rdflib job sets it, with the pins installed")
    kw = dict(KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"), KG_STORE="rdflib")
    p = _real(PLAN, **kw)
    assert p.returncode == 0 and not p.stderr, (p.returncode, p.stderr)
    p = _hook(PUSH, "gate", "--task", "codegen", "--instance", str(ROOT), env=_env(KG_AS_OF="record", KG_SCENARIO="S2", KG_REGISTER=REGISTER, **kw))
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


def test_the_summary_names_a_declared_gaps_closing_unit():
    """Task-0110: a finding carrying ``closer`` names it beside the owner; one without names the owner alone."""
    rep = {"verdict": "BLOCKED", "subject": "s", "scenario": "S2", "task": "codegen", "as_of": "2026-10-30", "threshold": "blocker",
           "findings": [{"severity": "blocker", "kind": "key", "key": "k|p", "message": "k|p is declared gap", "owner": "ORG-0002",
                         "closer": "ORG-0004", "route": "r; ORG-0004 closes the declared gap g"},
                        {"severity": "blocker", "kind": "key", "key": "k|r", "message": "k|r is declared gap", "owner": "ORG-0002",
                         "closer": None, "route": "r"},
                        {"severity": "blocker", "kind": "key", "key": "k|q", "message": "k|q is absent", "owner": "ORG-0002", "route": "r"}]}
    text = hook._summary(rep)
    assert "k|p is declared gap (owner ORG-0002; closed by ORG-0004)" in text
    assert "k|r is declared gap (owner ORG-0002; closed by no unit of the register)" in text
    assert "k|q is absent (owner ORG-0002)" in text and "  route: r; ORG-0004 closes the declared gap g" in text


def test_the_three_snippets_read_the_spec_commit_under_design_and_agree():
    """Task-0114 (after task-0101): all three snippets carry --task-for spec=design, the same arguments
    in the same order (the managed one adds only --knowgov, the advisory one only --advisory); the README
    says to keep it only where every gated subject declares [tasks.design], and to drop it otherwise."""
    load = lambda n: json.loads((DIR / n).read_text(encoding="utf-8"))  # noqa: E731
    args = lambda s: [h for e in s["hooks"]["PreToolUse"] for h in e["hooks"]][0]["args"]  # noqa: E731
    r, m, a = args(load("settings.json")), args(load("managed-settings.json")), args(load("settings.advisory-fail-open.json"))
    assert r[1:] == ["gate", "--task", "codegen", "--task-for", "spec=design"], r
    assert m[:len(r)] == r and m[len(r):] == ["--knowgov", "/opt/knowgov"], m
    assert a[:len(r)] == r and a[len(r):] == ["--advisory"], a
    assert "spec" in hook.STAGES
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    sec = readme[readme.index("## A fail-closed hook for Claude Code"):]
    for s in ("`--task-for spec=design`", "`[tasks.design]`", "drop the two arguments", "exit 2 at the spec commit"):
        assert s in sec, s
    assert "[tasks.design]" in (ROOT / "subjects" / "cargo_quote" / "subject.toml").read_text(encoding="utf-8")


def test_every_command_form_reads_as_its_transition_or_fails_closed():
    """task-0268 (decision-0032 F11): backticks, an inline -c alias and a configured one, a variable holding git or
    its subcommand (git${IFS}push, x=git; $x push): each reads as its transition or blocks; what is plain stays none."""
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
        g("init", "-q")
        g("config", "alias.ship", "push")
        g("config", "alias.deliver", "!git push origin HEAD")
        g("config", "alias.chain", "ship --force")
        t = lambda cmd: hook.transition({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(repo)}, ["spec.md"])  # noqa: E731
        for cmd in ["echo `git push`", 'echo "`git push`"', "a=`git push origin main`", "$(git push)",
                    "git -c alias.x=push x", "git -c alias.X=push x origin", "git ship", "git deliver", "git chain",
                    "bash -c 'git${IFS}push'", "git${IFS}push", "x=git; $x push", "x=push; git $x", "eval \"$x push\""]:
            assert t(cmd) == "push", cmd
        for cmd in ["x=git; $x commit -m m", "git${IFS}commit -m m"]:
            assert t(cmd) == "spec", cmd
        for cmd in ["git status", "echo gitpush", "git log --oneline | head", 'git commit -m "$msg"', "echo $HOME; git status",
                    "cd \"$REPO\" && git diff"]:
            assert t(cmd) is None, cmd
        # an alias of a builtin's name never hides the builtin (git runs the builtin): expanding only adds
        g("config", "alias.commit", "status")
        (repo / "docs").mkdir()
        (repo / "docs" / "spec.md").write_text("# spec\n")
        g("add", "docs/spec.md")
        assert t("git commit -m s") == "spec"


def test_a_field_that_is_not_a_string_blocks_in_every_profile():
    """task-0268 (task-0200 P8): a tool_name, a tool_input or a command of another type is refused, never allowed."""
    for ev in [{"tool_name": ["Bash"], "tool_input": {"command": "git push"}},
               {"tool_name": None, "tool_input": {}},
               {"tool_name": "Bash", "tool_input": {"command": ["git", "push"]}},
               {"tool_name": "Bash", "tool_input": "git push"},
               {"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": 3}]:
        try:
            hook.transition(ev, ["spec.md"])
        except ValueError:
            pass
        else:
            raise AssertionError(f"transition read {ev}")
        with tempfile.TemporaryDirectory() as t:
            for extra in ((), ("--advisory",)):
                p, called = _fake(Path(t), ev, 0, "PROCEED", *extra)
                assert p.returncode == 2 and "refused" in p.stderr and "unreadable hook event" in p.stderr and not called, (ev, extra, p.stderr)


def test_the_checkout_is_absolute_the_timeout_finite_and_a_stage_named_once():
    """task-0268: a relative --knowgov or KG_HOME is resolved where the hook starts, before the gate runs from the
    instance; --timeout takes a finite number of seconds above 0; a stage given two classes is refused."""
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kg = _stub(tmp)
        inst = tmp / "inst"
        inst.mkdir()
        mark = tmp / "called"
        env = _env(FAKE_RC="0", FAKE_VERDICT="PROCEED", FAKE_MARK=str(mark))
        rel = os.path.relpath(kg, tmp)
        for args, e in ((("--knowgov", rel), env), ((), {**env, "KG_HOME": rel})):
            mark.unlink(missing_ok=True)
            p = subprocess.run([sys.executable, str(SCRIPT), "gate", "--task", "codegen", "--instance", str(inst), *args],
                               input=json.dumps(PLAN), capture_output=True, text=True, env=e, timeout=120, cwd=str(tmp))
            assert p.returncode == 0 and mark.exists(), (args, p.stderr)
        assert hook._knowgov(rel) is None or hook._knowgov(rel).is_absolute()
        for bad in ("nan", "inf", "-inf", "0", "-5", "soon"):
            p = _hook(PLAN, "gate", "--task", "codegen", "--knowgov", str(kg), "--instance", str(inst), "--timeout", bad, env=env)
            assert p.returncode == 2 and "timeout" in p.stderr and "Traceback" not in p.stderr, (bad, p.stderr)
        p = _hook(PLAN, "gate", "--task", "codegen", "--knowgov", str(kg), "--instance", str(inst), "--timeout", "30", env=env)
        assert p.returncode == 0, p.stderr
        for extra in ((), ("--advisory",)):
            p = _hook(PLAN, "gate", "--task", "codegen", "--task-for", "plan=design", "--task-for", "plan=codegen",
                      "--knowgov", str(kg), "--instance", str(inst), *extra, env=env)
            assert p.returncode == 2 and "refused" in p.stderr and "plan twice" in p.stderr, (extra, p.stderr)


def test_a_staged_or_changed_path_with_a_space_or_a_non_ascii_character_is_read_as_itself():
    """task-0267: the hook reads git's path lists NUL-separated and unquoted (core.quotepath=off, -z). Before, a
    staged ``docs/my spec.md`` split into ``docs/my`` and ``spec.md``, and ``docs/especificación.md`` came back
    quoted with octal escapes, so neither matched its glob and the commit passed the spec transition unseen."""
    with tempfile.TemporaryDirectory() as t:
        repo = Path(t) / "repo"
        repo.mkdir()
        g = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)  # noqa: E731
        g("init", "-q")
        g("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", "base")
        (repo / "docs").mkdir()
        for name in ("my spec.md", "especificación.md"):
            (repo / "docs" / name).write_text("# spec\n", encoding="utf-8")
            g("add", f"docs/{name}")
            commit = {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'a spec'"}, "cwd": str(repo)}
            assert hook.transition(commit, ["docs/*.md"]) == "spec", name
            assert hook._committed(str(repo), "git commit -m x") == [f"docs/{name}"], name
            g("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", name)
        g("mv", "docs/my spec.md", "docs/mi especificación.md")   # a rename: the new name, its source skipped
        (repo / "notas nuevas.txt").write_text("x\n", encoding="utf-8")
        assert sorted(hook._status(str(repo))) == ["docs/mi especificación.md", "notas nuevas.txt"]


def test_the_summary_carries_the_attestation_finding_and_the_route_follows_the_cause():
    """task-0330 H1: an attestation finding below the blockers reaches the assistant; the closing route names the attestation
    route when the blockers are attestations, the questionnaire's otherwise."""
    att = {"severity": "major", "kind": "attestation", "key": None, "message": "[verification] execution lists no Version",
           "route": "a.md: the reference implementation and the suite are changed"}
    rep = {"verdict": "BLOCKED", "subject": "s", "scenario": "S1", "task": "codegen", "as_of": "2026-10-30", "threshold": "blocker",
           "findings": [{"severity": "blocker", "kind": "key", "key": "k|p", "message": "k|p is absent", "owner": "O", "route": "r"}, att]}
    text = hook._summary(rep)
    assert "attestation: [verification] execution lists no Version" in text and "route: a.md:" in text, text
    assert hook._route_for(rep) == hook.ROUTE
    rep["findings"][0] = {"severity": "blocker", "kind": "attestation", "key": None, "message": "x is not attested"}
    assert hook._route_for(rep) == hook.ATTESTATION_ROUTE and "questionnaire" not in hook.ATTESTATION_ROUTE


def test_routes_say_how_to_run_capture_from_an_instance_and_qualified_reaches_the_assistant():
    """Task-0311 C3-1, C3-3: the routes name $KG_HOME for an instance repository; a QUALIFIED gate that lets the step
    through is stated to the assistant as additional context, not silent."""
    assert "$KG_HOME" in hook.ROUTE
    sys.path.insert(0, str(ROOT / "harness"))
    import capture
    assert "$KG_HOME" in capture.questionnaire_route("s", "S1", "codegen", "ORG-1")
    assert "$KG_HOME" in capture.FROM_INSTANCE


def test_a_qualified_pass_reaches_the_assistant_and_keeps_the_attestation_finding():
    """Task-0311 R4, R6: `_qualified` turns a QUALIFIED pass into additionalContext; with no blockers `_shown` keeps the attestation
    finding among the six; a PROCEED, a block and a non-pass are left as they were."""
    fs = [{"severity": "major", "kind": "key", "key": f"k|{i}", "message": f"m{i}"} for i in range(8)]
    fs.append({"severity": "major", "kind": "attestation", "message": "a document changed", "route": "list the Version"})
    rep = {"verdict": "QUALIFIED", "subject": "s", "scenario": "S1", "task": "codegen", "as_of": "2026-11-13", "threshold": "blocker", "findings": fs}
    assert len(hook._shown(rep)) == 6 and any(f["kind"] == "attestation" for f in hook._shown(rep))
    d = hook._qualified(hook.decide(0), rep, "gate", 0)
    ctx = d.output["hookSpecificOutput"]["additionalContext"]
    assert d.exit_code == 0 and "QUALIFIED" in ctx and "a document changed" in ctx
    assert hook._qualified(hook.decide(0), {**rep, "verdict": "PROCEED"}, "gate", 0).output is None
    assert hook._qualified(hook.decide(1), rep, "gate", 1).exit_code == 2
    assert "KG_SUBJECT=" in hook.ROUTE and "KG_REGISTER=" in hook.ROUTE
