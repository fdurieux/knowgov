"""Task-0146: subject_check on the reader (doc-0018 candidate 3). A proposed subject held in the call,
checked by tools/check_subject.py's own functions, its report equal to the CLI's on the same files,
pinned by the subject-check schema; nothing stored, the temporary root removed, the call bounded."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import mcp_server  # noqa: E402
import schema_check  # noqa: E402
import subject_check  # noqa: E402

PROBE = ROOT / "tools" / "fixtures" / "subject_probe"
MINIMAL = ROOT / "subjects" / "minimal"


def _args(root: Path, label: str | None = None) -> dict:
    a = {"subject_toml": (root / "subject.toml").read_text(encoding="utf-8"), "root": label or root.relative_to(ROOT).as_posix()}
    for f, n in (("register_map_toml", "register_map.toml"), ("scenarios_toml", "scenarios.toml"), ("plants_toml", "plants.toml")):
        if (root / n).is_file():
            a[f] = (root / n).read_text(encoding="utf-8")
    import tomllib
    m = tomllib.loads(a["subject_toml"])
    docs = {}
    for art in m.get("artefact", []):
        p = root / art.get("path", "")
        if art.get("path") and p.is_file():
            docs[art["path"]] = p.read_text(encoding="utf-8")
        elif art.get("path") and p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    docs[(Path(art["path"]) / f.relative_to(p)).as_posix()] = f.read_text(encoding="utf-8")
    a["documents"] = docs
    return a


def _cli(root: Path) -> dict:
    cp = subprocess.run([sys.executable, str(ROOT / "tools" / "check_subject.py"), root.relative_to(ROOT).as_posix(), "--json"],
                        capture_output=True, text=True, cwd=str(ROOT), timeout=600)
    return json.loads(cp.stdout)


def _call(name, args):
    s = mcp_server.Server(mcp_server.Tools(opener=lambda: (_ for _ in ()).throw(AssertionError("no store is opened"))))
    return s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})["result"]


def test_the_probe_reads_as_the_cli_reads_it_and_the_schema_holds():
    schema = schema_check.load("subject-check")
    for root in (PROBE, MINIMAL):
        r = _call("subject_check", _args(root))
        assert r["isError"] is False, r
        got = r["structuredContent"]
        assert got == _cli(root), root
        assert schema_check.validate(got, schema) == [], schema_check.validate(got, schema)
    got = _call("subject_check", _args(PROBE))["structuredContent"]
    rules = {f["rule"] for f in got["findings"]}
    assert {"table", "scenario", "map-node", "map-owner"} <= rules, rules
    assert got["exit_code"] == 1
    if got["yield"]["state"] == "checked":   # the mappers need PyYAML
        assert any(f["rule"] == "yield" and "REQ-02|text" in f["fix"] for f in got["findings"]), got["findings"]


def test_a_document_two_levels_up_lands_in_the_instance_and_one_further_is_refused():
    a = _args(PROBE)
    text = a["documents"].pop("requirements.md")
    a["subject_toml"] = a["subject_toml"].replace('path = "requirements.md"', 'path = "../../artefacts/textual-requirements/requirements.md"')
    a["documents"]["../../artefacts/textual-requirements/requirements.md"] = text
    got = _call("subject_check", a)["structuredContent"]
    assert not any(f["rule"] == "path" for f in got["findings"]), got["findings"]
    for bad in ("../../../etc/passwd", "/etc/passwd", "a\\b.md", "", "x/\0.md", "a" * 300, "..", "../.."):
        b = dict(a, documents={bad: "x"})
        r = _call("subject_check", b)
        assert r["isError"] is True and "cannot be checked" in r["content"][0]["text"], (bad, r)


def test_the_call_is_bounded_and_needs_a_manifest():
    for args, said in [({}, "subject_toml"), ({"subject_toml": 3}, "subject_toml"),
                       ({"subject_toml": "", "documents": []}, "documents must be an object"),
                       ({"subject_toml": "", "documents": {f"d{i}.md": "" for i in range(subject_check.MAX_DOCUMENTS + 1)}}, "at most"),
                       ({"subject_toml": "x" * (subject_check.MAX_BYTES + 1)}, "bytes"),
                       ({"subject_toml": "", "documents": {"subject.toml": ""}}, "own field")]:
        r = _call("subject_check", args)
        assert r["isError"] is True and said in r["content"][0]["text"], (args.keys(), r["content"][0]["text"])
    # an oversized call writes nothing: no temporary root is made before the bound is checked
    before = set(Path(tempfile.gettempdir()).glob("kg-subject-check-*"))
    _call("subject_check", {"subject_toml": "x" * (subject_check.MAX_BYTES + 1)})
    assert set(Path(tempfile.gettempdir()).glob("kg-subject-check-*")) == before


def test_nothing_is_left_behind_and_nothing_is_stored():
    before = set(Path(tempfile.gettempdir()).glob("kg-subject-check-*"))
    r = _call("subject_check", _args(PROBE))   # the opener raises if the store were opened
    assert r["isError"] is False
    r = _call("subject_check", {"subject_toml": "[subject\n"})
    assert r["isError"] is False and r["structuredContent"]["exit_code"] == 1   # a manifest that does not parse is the report's
    assert set(Path(tempfile.gettempdir()).glob("kg-subject-check-*")) == before
    src = (ROOT / "harness" / "subject_check.py").read_text(encoding="utf-8")
    for w in ("open_store", "store.", "KG_RDFLIB_FILE", "load("):
        assert w not in src, w


def test_listed_read_only_with_its_own_schema_and_the_docs_name_it():
    (t,) = [t for t in mcp_server.TOOLS if t["name"] == "subject_check"]
    assert t["annotations"] == mcp_server.READ_ONLY and t["inputSchema"]["required"] == ["subject_toml"]
    assert "subject_check" in mcp_server.INSTRUCTIONS and "Never take a task's keys" in mcp_server.INSTRUCTIONS
    for doc in ("instance/README.md", "CLAUDE.md", "CHANGELOG.md"):
        assert "subject_check" in (ROOT / doc).read_text(encoding="utf-8"), doc
