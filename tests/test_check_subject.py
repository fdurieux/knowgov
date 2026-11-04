"""Task-0135: the subject check (tools/check_subject.py; doc-0018 F2 to F5), folded into the instance's
layout check. On doc-0018's probe subject (tools/fixtures/subject_probe: a misspelt key, a stray
[task] table, no scenario, a map row naming CAP-9999, an owner of none of its row's nodes) each
defect is named with its fix and the layout fails; the public subjects and the example instance pass
with no finding; the report is pinned by its schema; no store is opened and no file is written.

The documents' yield needs the harness's mappers (PyYAML; the sequence and container mappers also
pumllint). The tests job is standard library only, so there the yield reads unchecked and says why;
where the mappers run (harness.yml's rdflib job, a venv with the pins), the did-you-mean is asserted.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import check_instance  # noqa: E402
import check_subject  # noqa: E402
import example_instance  # noqa: E402
import schema_check  # noqa: E402

PROBE = ROOT / "tools" / "fixtures" / "subject_probe"
REGISTER = ROOT / "demo" / "register"
MAPPERS_RUN = all(importlib.util.find_spec(m) is not None for m in ("yaml", "pumllint"))   # every public subject's mappers


def _digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def _rules(rep: dict, level: str = "error") -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for f in rep["findings"]:
        if f["level"] == level:
            out.setdefault(f["rule"], []).append(f)
    return out


def test_the_probe_is_refused_with_each_defect_named_and_its_fix():
    rep = check_subject.check(PROBE, REGISTER)
    errs = _rules(rep)
    assert rep["exit_code"] == 1 and set(errs) == {"table", "scenario", "map-owner", "map-node"}, errs
    [t] = errs["table"]
    assert t["where"] == "[task]" and "[tasks]" in t["fix"], t
    [s] = errs["scenario"]
    assert "exits 2" in s["message"] and "S0" in s["fix"], s
    [o] = errs["map-owner"]
    assert "ORG-0001" in o["message"] and "ORG-0002" in o["fix"], o
    [n] = errs["map-node"]
    assert "CAP-9999" in n["message"], n
    if rep["yield"]["state"] == "checked":   # the child's view: the mappers ran (harness.yml asserts it there)
        assert rep["yield"]["keys"] == 2, rep["yield"]
        [w] = _rules(rep, "warning")["yield"]
        assert w["message"].startswith("REQ-02|txt:") and "did you mean REQ-02|text?" in w["fix"], w
        # decision-0009 (a), task-0136: authored statements and no [verification] authored declared
        [a] = [n for n in rep["notes"] if n["rule"] == "attestation"]
        assert "kit/requirements.md" in a["message"] and "decision-0009" in a["message"], a
    else:
        assert rep["yield"]["state"] == "unchecked" and rep["yield"]["why"], rep["yield"]
        assert any(n["rule"] == "yield" and "unchecked" in n["message"] for n in rep["notes"]), rep["notes"]
    text = check_subject.render(rep)
    assert "ERROR [task]:" in text and "Fix: rename it to [tasks]" in text and "manifest refused: 4 error(s)" in text


def test_the_public_subjects_pass_with_no_finding():
    for sid in ("cargo_quote", "jef_data_load", "minimal"):
        rep = check_subject.check(ROOT / "subjects" / sid, REGISTER)
        assert rep["findings"] == [] and rep["exit_code"] == 0, (sid, rep["findings"])
        if MAPPERS_RUN and sid != "minimal":
            assert rep["yield"]["state"] == "checked" and rep["yield"]["keys"] > 0, (sid, rep["yield"])
            assert not [n for n in rep["notes"] if n["rule"] in ("unyielded", "attestation")], (sid, rep["notes"])


def test_the_report_validates_against_its_schema():
    schema = schema_check.load("subject-check")
    for root in (PROBE, ROOT / "subjects" / "cargo_quote", ROOT / "subjects" / "minimal"):
        rep = json.loads(json.dumps(check_subject.check(root, REGISTER)))
        assert schema_check.validate(rep, schema) == [], (root.name, schema_check.validate(rep, schema))


def test_each_manifest_mistake_is_refused_by_its_rule():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "typos"
        root.mkdir()
        (root / "doc.md").write_text("| REQ-01 | text |\n", encoding="utf-8")
        (root / "scenarios.toml").write_text('[[scenario]]\nid = "S0"\ntitle = "pristine"\nextraction = "pristine"\n', encoding="utf-8")
        (root / "subject.toml").write_text(
            '[subject]\nid = "typos"\nlsited = false\n\n'
            '[[artefact]]\nkey = "doc.md"\nfamily = "requirements"\nformat = "markdown"\npath = "doc.md"\nmapper = "requirement"\nmaper = "x"\n\n'
            '[[artefact]]\nkey = "doc.md"\nfamily = "requirements"\n\n'
            '[tasks.codegen]\nkeys = ["REQ 01|text", "REQ-01|text"]\nblock_levels = ["absnet"]\nmax_unverified_share = 1.5\n\n'
            '[tasks.design]\nkeys = []\n\n'
            '[three_valued]\nkeys = ["no-pipe"]\n', encoding="utf-8")
        rep = check_subject.check(root, REGISTER, run_yield=False)
        got = {(f["rule"], f["where"].split(" ")[0]) for f in rep["findings"]}
        want = {("field", "[subject]"), ("field", "[[artefact]]"), ("mapper", "[[artefact]]"), ("duplicate", "[[artefact]]"),
                ("required", "[[artefact]]"), ("key-syntax", "[tasks.codegen]"), ("block-level", "[tasks.codegen]"),
                ("share", "[tasks.codegen]"), ("required", "[tasks.design]"), ("key-syntax", "[three_valued]")}
        assert want <= got, sorted(want - got)
        fixes = " | ".join(f["fix"] for f in rep["findings"])
        assert "'listed'" in fixes and "'requirements'" in fixes and "'absent'" in fixes, fixes
        assert rep["exit_code"] == 1 and all(f["level"] == "error" for f in rep["findings"])
        broken = Path(td) / "broken"
        broken.mkdir()
        (broken / "subject.toml").write_text("[subject\n", encoding="utf-8")
        rep = check_subject.check(broken)
        assert [f["rule"] for f in rep["findings"]] == ["manifest"] and rep["exit_code"] == 1


def test_the_command_exits_0_1_or_2():
    assert check_subject.main([str(ROOT / "subjects" / "cargo_quote")]) == 0
    assert check_subject.main([str(PROBE), "--register", str(REGISTER)]) == 1
    assert check_subject.main([str(ROOT / "nope")]) == 2


def test_the_instance_check_refuses_the_probe_and_writes_nothing():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "inst"
        example_instance.build(inst)
        before = _digest(inst)
        rep = check_instance.check(inst)
        assert rep["errors"] == [], rep["errors"]
        [s] = rep["subjects"]
        assert s["check"]["findings"] == [] and s["check"]["exit_code"] == 0, s["check"]
        assert check_instance.main([str(inst)]) == 0
        assert _digest(inst) == before, "the check wrote into the instance"
        dest = inst / "subjects" / "probe"
        dest.mkdir()
        for p in PROBE.iterdir():
            (dest / p.name).write_bytes(p.read_bytes())
        before = _digest(inst)
        rep = check_instance.check(inst)
        errs = " | ".join(rep["errors"])
        for part in ("subjects/probe: [task]", "rename it to [tasks]", "subjects/probe: scenarios.toml", "CAP-9999", "owner ORG-0001"):
            assert part in errs, (part, errs)
        assert check_instance.main([str(inst)]) == 1
        text = check_instance.render(rep)
        if rep["subjects"][-1]["check"]["yield"]["state"] == "checked":
            assert "WARNING subjects/probe [tasks.codegen] keys: REQ-02|txt" in text and "did you mean REQ-02|text?" in text, text
        assert _digest(inst) == before, "the check wrote into the instance"


def test_the_yield_opens_no_store():
    code = ("import json, sys; sys.path.insert(0, 'tools'); import check_subject; from pathlib import Path; "
            "check_subject.yield_only(Path(sys.argv[1])); "
            "print(json.dumps(sorted(m for m in sys.modules if m.startswith(('store', 'neo4j', 'rdflib')))))")
    root = ROOT / "subjects" / "cargo_quote"
    cp = subprocess.run([sys.executable, "-c", code, str(root)], capture_output=True, text=True, cwd=str(ROOT),
                        env=dict(os.environ, KG_SUBJECT=str(root), PYTHONDONTWRITEBYTECODE="1"), timeout=300)
    assert cp.returncode == 0, cp.stderr
    assert json.loads(cp.stdout.strip().splitlines()[-1]) == [], cp.stdout
    src = (ROOT / "tools" / "check_subject.py").read_text(encoding="utf-8")
    assert "import store" not in src and "open_store" not in src
