"""Task-0105: knowgov's own protected paths as fail-closed Claude Code hooks (.claude/). A hand edit to a
vendored file or its SOURCE.md, and a backlog markdown file written by Edit or Write, are blocked; a
backlog change the CLI makes and an edit to an unprotected file pass. The exit mapping is task-0099's
``decide``, imported, never copied."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".claude" / "hooks" / "protected_paths.py"
SETTINGS = ROOT / ".claude" / "settings.json"
_spec = importlib.util.spec_from_file_location("protected_paths", SCRIPT)
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)

TASK = next((ROOT / "backlog" / "tasks").glob("task-0105 *.md")).relative_to(ROOT).as_posix()
VENDORED = ["demo/register/SOURCE.md", "demo/register/metamodel/x.md", "demo/model/model.json",
            "subjects/cargo_quote/vendor/SOURCE.md", "subjects/jef_data_load/vendor/SOURCE.md",
            "subjects/jef_data_load/vendor/new_file.py"]
BACKLOG = [TASK, "backlog/decisions/decision-0001 x.md", "backlog/docs/doc-9999 new.md"]
CLEAR = ["README.md", "harness/run.py", "subjects/cargo_quote/subject.toml", "subjects/jef_data_load/record/SOURCE.md",
         "backlog/config.yml", "demo/registers.md", "/tmp/elsewhere.md"]


def _ev(tool: str, path: str, *, key: str = "file_path") -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {key: path}, "cwd": str(ROOT)}


def _hook(check: str, event=None, raw: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), check], input=raw if raw is not None else json.dumps(event),
                          capture_output=True, text=True, cwd=str(ROOT), timeout=60)


def test_the_vendored_trees_are_the_vendor_tools_own_and_each_holds_its_note():
    got = {p.relative_to(ROOT).as_posix() for p in pp.vendored_roots()}
    assert got == {"demo/register", "demo/model", "subjects/cargo_quote/vendor", "subjects/jef_data_load/vendor"}, got
    for t in got:
        assert (ROOT / t / "SOURCE.md").is_file(), t


def test_a_hand_edit_to_a_vendored_file_or_its_note_is_blocked():
    for path in VENDORED:
        for tool in ("Edit", "Write", "MultiEdit"):
            p = _hook("vendored", _ev(tool, path))
            assert p.returncode == 2 and "BLOCKED by a finding" in p.stderr and "vendor" in p.stderr, (path, tool, p.stderr)
            assert _hook("backlog", _ev(tool, path)).returncode == 0, (path, tool)
    abs_path = str(ROOT / "demo" / "register" / "SOURCE.md")
    assert _hook("vendored", _ev("Edit", abs_path)).returncode == 2
    assert _hook("vendored", _ev("Edit", f"../{ROOT.name}/demo/model/model.json")).returncode == 2


def test_a_backlog_file_written_by_edit_or_write_is_blocked():
    for path in BACKLOG:
        for tool in ("Edit", "Write", "MultiEdit"):
            p = _hook("backlog", _ev(tool, path))
            assert p.returncode == 2 and "BLOCKED by a finding" in p.stderr and "backlog CLI" in p.stderr, (path, tool)
            assert _hook("vendored", _ev(tool, path)).returncode == 0, (path, tool)
    assert _hook("backlog", _ev("NotebookEdit", "backlog/docs/n.md", key="notebook_path")).returncode == 2


def test_a_cli_written_backlog_change_and_an_unprotected_edit_pass():
    # the CLI writes the file itself, through Bash: no Edit or Write event names the path
    for cmd in ["backlog task edit TASK-0105 --append-notes 'x'", "python tools/vendor_register.py ../ieam-register",
                f"cat {TASK}"]:
        ev = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(ROOT)}
        for check in ("vendored", "backlog"):
            p = _hook(check, ev)
            assert p.returncode == 0 and not p.stdout and not p.stderr, (cmd, check)
    for path in CLEAR:
        for check in ("vendored", "backlog"):
            assert _hook(check, _ev("Edit", path)).returncode == 0, (path, check)


def test_cannot_tell_blocks_fail_closed():
    for check in ("vendored", "backlog"):
        for raw in ["", "not json", "[]", json.dumps({"tool_name": "Edit", "tool_input": {}})]:
            p = _hook(check, raw=raw)
            assert p.returncode == 2 and "unavailable (exit 2)" in p.stderr and "Fail-closed" in p.stderr, (check, raw)
    p = _hook("nonsense", _ev("Edit", "README.md"))
    assert p.returncode == 2 and "usage" in p.stderr


def test_the_mapping_is_task_0099s_decide_with_no_copy():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "instance\" / \"ci\" / \"claude\" / \"knowgov_hook.py\"" in src and "hook.decide(" in src
    for copy in ("def decide", "def emit", "HOOK_BLOCK", "HOOK_ALLOW", "Decision(", "Fail-closed:", "BLOCKED by"):
        assert copy not in src, copy
    assert "20-of-20" not in src
    # the hook's exit is decide's: run the hook and decide on the same answers
    hook = sys.modules.get("knowgov_hook") or pp._load("knowgov_hook", ROOT / "instance" / "ci" / "claude" / "knowgov_hook.py")
    blocked = _hook("backlog", _ev("Write", TASK))
    assert blocked.returncode == hook.decide(1).exit_code == 2
    assert _hook("backlog", _ev("Write", "README.md")).returncode == hook.decide(0).exit_code == 0
    assert _hook("backlog", raw="x").returncode == hook.decide(2).exit_code == 2


def test_the_settings_wire_both_hooks_on_the_write_tools_and_nothing_else():
    s = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert set(s) == {"hooks"} and set(s["hooks"]) == {"PreToolUse"}
    entries = s["hooks"]["PreToolUse"]
    assert {m for e in entries for m in e["matcher"].split("|")} == set(pp.WRITE_TOOLS)
    cmds = [h for e in entries for h in e["hooks"]]
    assert sorted(h["command"].rsplit(" ", 1)[-1] for h in cmds) == ["backlog", "vendored"]
    for h in cmds:
        assert h["type"] == "command" and ".claude/hooks/protected_paths.py" in h["command"] and h["onFailure"] == "block"
        assert "knowgov-gate" not in h["command"] and " gate" not in h["command"]   # the knowledge gate is not wired here
