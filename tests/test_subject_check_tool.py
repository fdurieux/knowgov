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
                       ({"subject_toml": "", "documents": {"subject.toml": ""}}, "same file as")]:
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


def test_h7_a_manifest_naming_a_path_outside_the_call_is_refused_and_says_nothing_of_the_server():
    """task-0196 (doc-0030 H7): the documents a call carries were confined, but the paths its manifest
    names were joined to the temporary root and read, so an absolute or climbing [[artefact]] path or
    [reference] code was an existence oracle and its excerpt landed in the report. Every path field is
    now refused before anything is written or the yield child runs, and an existing and a missing target
    are refused alike, the refusal naming only what the caller sent."""
    base = (PROBE / "subject.toml").read_text(encoding="utf-8")
    real = str(ROOT / "README.md")
    secret = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()[0]
    climb = "../../../../../../../../" + real.lstrip("/")
    art = lambda p: base.replace('path = "requirements.md"', f'path = "{p}"')  # noqa: E731
    bad = {
        "absolute artefact": art(real),
        "climbing artefact": art(climb),
        "one level past the instance": art("../../../x.md"),
        "home": art("~/notes.md"),
        "reference code": base + f'\n[reference]\ncode = "{real}"\n',
        "oracle script": base + '\n[oracle]\nscript = "/etc/hostname"\n',
        "verification map": base + '\n[verification]\nmap = "../../../secret.toml"\n',
        "record dir": base.replace("[record]\n", '[record]\ndir = "/tmp"\n'),
        "include glob": base.replace('mapper = "requirements"', 'mapper = "requirements"\ninclude = ["../../../*.md"]'),
    }
    before = set(Path(tempfile.gettempdir()).glob("kg-subject-check-*"))
    for name, manifest in bad.items():
        r = _call("subject_check", dict(_args(PROBE), subject_toml=manifest))
        text = r["content"][0]["text"]
        assert r["isError"] is True and "cannot be checked" in text, (name, r)
        assert secret not in text and "structuredContent" not in r, (name, text)
    assert set(Path(tempfile.gettempdir()).glob("kg-subject-check-*")) == before, "refused before anything was written"
    # no existence oracle: a path to a file that exists and one to a file that does not read alike
    exists = _call("subject_check", dict(_args(PROBE), subject_toml=art(climb)))["content"][0]["text"]
    missing = _call("subject_check", dict(_args(PROBE), subject_toml=art(climb + ".nope")))["content"][0]["text"]
    assert exists == missing.replace(".nope", ""), (exists, missing)
    # two levels up, the documents' own place in an instance, still checks
    ok = art("../../artefacts/textual-requirements/requirements.md")
    a = dict(_args(PROBE), subject_toml=ok)
    a["documents"] = {"../../artefacts/textual-requirements/requirements.md": a["documents"].pop("requirements.md")}
    assert _call("subject_check", a)["isError"] is False


def test_h7_document_keys_are_compared_normalised_so_the_manifest_cannot_be_overwritten():
    """doc-0030 H7: `x/../subject.toml` wrote over the passed manifest (the report flipped from exit 1 to 0)."""
    a = _args(PROBE)
    clean = (ROOT / "subjects" / "minimal" / "subject.toml").read_text(encoding="utf-8")
    for key in ("x/../subject.toml", "./subject.toml", "a/b/../../subject.toml", "x/../register_map.toml", "./requirements.md"):
        b = dict(a, documents={**a["documents"], key: clean})
        if key == "./requirements.md":
            b["documents"].pop("requirements.md", None)
            b["documents"]["requirements.md"] = "x"
        r = _call("subject_check", b)
        assert r["isError"] is True and "same file as" in r["content"][0]["text"], (key, r)
    assert _call("subject_check", a)["structuredContent"]["exit_code"] == 1   # the probe, unflipped
