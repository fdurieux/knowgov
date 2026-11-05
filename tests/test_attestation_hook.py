"""Task-0147: an instance's attestations guarded from an assistant's own writes (instance/ci/claude/
attestation_paths.py; doc-0018 candidate 5). A write that adds or changes subject.toml's [verification]
or [provenance], or writes under captures/, a review file, preload-baseline.json, the verification map or
register/, is blocked; an ordinary manifest edit passes; a malformed event or an unreadable file fails
closed. The exit mapping is task-0099's ``decide``, imported, never copied."""
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
SCRIPT = DIR / "attestation_paths.py"
_spec = importlib.util.spec_from_file_location("attestation_paths", SCRIPT)
ap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ap)

MANIFEST = """[subject]
id = "probe"

[[artefact]]
path = "../../artefacts/textual-requirements/requirements.md"
mapper = "requirements"

[verification]
map = "verification_map.toml"
authored = { at = "2026-11-04", scope = "reviewed by employee-2" }

[provenance]
human = { id = "agent:employee-2", name = "employee-2" }

[capture]
dir = "answers"

[tasks.codegen]
keys = ["REQ-01|text"]
"""


def _instance() -> Path:
    inst = Path(tempfile.mkdtemp(prefix="kg-attest-"))
    (inst / "subjects" / "probe").mkdir(parents=True)
    (inst / "subjects" / "probe" / "subject.toml").write_text(MANIFEST, encoding="utf-8")
    (inst / "register").mkdir()
    return inst


def _run(inst: Path, tool: str, path: str, raw: str | None = None, **ti) -> subprocess.CompletedProcess:
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    ev = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {key: path, **ti}, "cwd": str(inst)}
    env = {k: v for k, v in os.environ.items() if not k.startswith(("KG_", "CLAUDE_"))}
    env["CLAUDE_PROJECT_DIR"] = str(inst)
    return subprocess.run([sys.executable, str(SCRIPT)], input=raw if raw is not None else json.dumps(ev),
                          capture_output=True, text=True, env=env, timeout=60)


M = "subjects/probe/subject.toml"


def _edit(inst, old, new):
    return _run(inst, "Edit", M, old_string=old, new_string=new)


def test_adding_or_changing_verification_or_provenance_is_blocked():
    inst = _instance()
    for old, new in [('scope = "reviewed by employee-2" }', 'scope = "reviewed by employee-2" }\napproval = { at = "2026-11-05", record = "m.md" }'),
                     ('at = "2026-11-04"', 'at = "2026-11-05"'),
                     ('"agent:employee-2"', '"agent:employee-3"'),
                     ("[tasks.codegen]", "[tasks.codegen]\n[verification.extra]\nx = 1\n")]:
        p = _edit(inst, old, new)
        assert p.returncode == 2 and "BLOCKED by a finding" in p.stderr and "decision-0009" in p.stderr, (new, p.stderr)
        assert ap.ROUTE in p.stderr
    # a fresh manifest written whole with the tables, and a dotted key at the top, are additions too
    bare = MANIFEST.split("[verification]")[0]
    (inst / "subjects" / "new").mkdir()
    p = _run(inst, "Write", "subjects/new/subject.toml", content=MANIFEST)
    assert p.returncode == 2 and "[verification], [provenance]" in p.stderr, p.stderr
    p = _run(inst, "Write", "subjects/new/subject.toml", content='verification.authored = { at = "2026-11-05" }\n' + bare)
    assert p.returncode == 2, p.stderr
    # MultiEdit: one edit of several suffices
    p = _run(inst, "MultiEdit", M, edits=[{"old_string": "probe", "new_string": "probe2"},
                                          {"old_string": "employee-2\" }\n", "new_string": "employee-9\" }\n"}])
    assert p.returncode == 2, p.stderr


def test_an_ordinary_manifest_edit_and_removing_a_table_outright_pass():
    inst = _instance()
    for old, new in [('keys = ["REQ-01|text"]', 'keys = ["REQ-01|text", "REQ-02|text"]'),
                     ("[tasks.codegen]", '[[artefact]]\npath = "../../artefacts/x/y.md"\nmapper = "requirements"\n\n[tasks.codegen]'),
                     ("[subject]", "# a comment\n[subject]"),
                     ('[tasks.codegen]\nkeys = ["REQ-01|text"]', '[tasks.codegen]\nkeys = ["REQ-01|text"]\n\n[tasks.design]\nkeys = []')]:
        p = _edit(inst, old, new)
        assert p.returncode == 0 and not p.stderr, (new, p.stderr)
    # removing both tables attests nothing
    both = 'authored = { at = "2026-11-04", scope = "reviewed by employee-2" }\n\n[provenance]\nhuman = { id = "agent:employee-2", name = "employee-2" }\n'
    head = '[verification]\nmap = "verification_map.toml"\n'
    p = _run(inst, "Edit", M, old_string=head + both, new_string="")
    assert p.returncode == 0, p.stderr
    # removing [provenance] while [verification] stays shifts who attests to the default agent: blocked
    p = _edit(inst, '[provenance]\nhuman = { id = "agent:employee-2", name = "employee-2" }\n', "")
    assert p.returncode == 2 and "removed while [verification] stays" in p.stderr, p.stderr
    # a write to an ordinary document, or outside the instance, is not this hook's
    for path in ["artefacts/textual-requirements/requirements.md", "subjects/probe/register_map.toml", "/tmp/elsewhere/x.toml"]:
        p = _run(inst, "Write", path, content="x = 1\n")
        assert p.returncode == 0, (path, p.stderr)
    assert _run(inst, "Bash", "", raw=json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf register"}, "cwd": str(inst)})).returncode == 0


def test_captures_reviews_baseline_map_and_register_are_blocked():
    inst = _instance()
    cases = {"subjects/probe/captures/2026-11-05-ORG-1-employee-1.toml": "captures",
             "subjects/probe/captures/reviews/r.toml": "captures",
             "subjects/probe/answers/a.toml": "captures",                 # the manifest's [capture] dir
             "subjects/probe/verification_map.toml": "verification map",
             "preload-baseline.json": "pre-load baseline",
             "subjects/probe/preload-baseline.json": "pre-load baseline",
             "register/nodes/capabilities/CAP-0001.toml": "register",
             "register/people/handles.toml": "register"}
    for path, said in cases.items():
        for tool in ("Write", "NotebookEdit"):
            p = _run(inst, tool, path, content="x = 1\n")
            assert p.returncode == 2 and said in p.stderr and "BLOCKED" in p.stderr, (path, tool, p.stderr)
    # a review file drafted anywhere, parsed or half-written
    review = '[review]\nby = "employee-2"\non = 2026-11-09\n\n[[ruling]]\nassertion = "A:x"\noutcome = "approved"\n'
    for content in (review, "[review]\nby = \n", "[[ruling]]\n"):
        p = _run(inst, "Write", "review.toml", content=content)
        assert p.returncode == 2 and "review file" in p.stderr, (content, p.stderr)


def test_cannot_tell_blocks_fail_closed():
    inst = _instance()
    for raw in ["", "not json", "[]", json.dumps({"tool_name": "Edit", "tool_input": {}, "cwd": str(inst)}),
                json.dumps({"tool_name": "Write", "tool_input": {"file_path": "x.toml"}, "cwd": str(inst)}),
                json.dumps({"tool_name": "Edit", "tool_input": "x", "cwd": str(inst)})]:
        p = _run(inst, "Edit", M, raw=raw)
        assert p.returncode == 2 and "unavailable (exit 2)" in p.stderr and "Fail-closed" in p.stderr, (raw, p.stderr)
        assert ap.UNAVAILABLE_ROUTE in p.stderr and "the store reachable" not in p.stderr
    # an old_string not in the file, and a manifest that will not parse after the write
    p = _edit(inst, "no such text", "x")
    assert p.returncode == 2 and "old_string is not in" in p.stderr, p.stderr
    p = _edit(inst, "[subject]", "[subject")
    assert p.returncode == 2 and "does not parse" in p.stderr, p.stderr
    # a manifest that does not parse before: its repairing edit cannot be read either (fail closed), but
    # a write elsewhere is not held hostage by it
    (inst / "subjects" / "probe" / "subject.toml").write_text("[subject\n", encoding="utf-8")
    assert _edit(inst, "[subject\n", "[subject]\n").returncode == 2
    assert _run(inst, "Write", "artefacts/x.md", content="ok").returncode == 0
    assert _run(inst, "Write", "subjects/probe/captures/a.toml", content="ok").returncode == 2


def test_the_mapping_is_task_0099s_decide_with_no_copy():
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"knowgov_hook.py"' in src and "hook.decide(" in src
    for copy in ("def decide", "def emit", "HOOK_BLOCK", "HOOK_ALLOW", "Decision(", "Fail-closed:", "BLOCKED by"):
        assert copy not in src, copy
    assert "Bash" in ap.__doc__ and "does not see" in ap.__doc__


def test_the_snippet_wires_it_on_the_write_tools_fail_closed():
    s = json.loads((DIR / "settings.attestations.json").read_text(encoding="utf-8"))
    assert set(s) == {"hooks"} and set(s["hooks"]) == {"PreToolUse"}
    (entry,) = s["hooks"]["PreToolUse"]
    assert set(entry["matcher"].split("|")) == set(ap.WRITE_TOOLS)
    (h,) = entry["hooks"]
    assert h["type"] == "command" and h["command"] == "python3" and h["args"][0].endswith("/instance/ci/claude/attestation_paths.py")
    assert h["onFailure"] == "block" and h["timeout"] <= 60
    readme = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")
    sec = readme[readme.index("### Guarding what people attest"):]
    for t in ("settings.attestations.json", "[verification]", "[provenance]", "captures/", "preload-baseline.json",
              "register/", "shell command", "51-knowgov-attestations.json"):
        assert t in sec, t
