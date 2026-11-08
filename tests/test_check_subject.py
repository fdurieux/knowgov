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
            # the one attestation note a public subject may carry: decision-0019's read rule, a declaration listing no
            # Version, until the maintainer lists the Versions it attests (task-0221's held pull request)
            assert not [n for n in rep["notes"] if n["rule"] == "unyielded" or (n["rule"] == "attestation" and "decision-0019" not in n["message"])], (sid, rep["notes"])


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


def _renewal(rows: str, keys: list[str], short: bool = True) -> Path:
    """doc-0021's probe subject `renewal`: one requirements file, one task, S0."""
    root = Path(tempfile.mkdtemp(prefix="kg-renewal-")) / "renewal"
    root.mkdir()
    (root / "renewal.md").write_text("# Renewal\n\n" + rows, encoding="utf-8")
    (root / "scenarios.toml").write_text((ROOT / "subjects" / "minimal" / "scenarios.toml").read_text(encoding="utf-8"), encoding="utf-8")
    (root / "subject.toml").write_text(
        '[subject]\nid = "renewal"\n\n[[artefact]]\nkey = "renewal.md"\n' + ('short = "renewal"\n' if short else "")
        + 'family = "requirements"\nformat = "markdown"\npath = "renewal.md"\nmapper = "requirements"\n\n'
        + f"[tasks.codegen]\nkeys = {json.dumps(keys)}\nblock_levels = [\"absent\"]\nmax_unverified_share = 0.25\n", encoding="utf-8")
    return root


def test_a_document_its_mapper_yields_nothing_from_is_named_the_wrong_convention():
    """task-0149 (doc-0021 G1): RNW-nn ids read by `requirements` yield nothing; a WARNING names the
    mapper's convention and the kind's other mapper, never 'no knowledge'."""
    rep = check_subject.check(_renewal("| RNW-01 | A renewal keeps the quote's price. |\n", ["RNW-01|text"]), REGISTER)
    if rep["yield"]["state"] != "checked":
        return
    [w] = _rules(rep, "warning")["zero-yield"]
    assert w["where"] == "[[artefact]] renewal.md" and "| REQ-nn | text |" in w["message"], w
    assert "requirements_json" in w["fix"] and "ABSENT" in w["fix"] and "never rewrite" in w["fix"], w
    assert schema_check.validate(rep, schema_check.load("subject-check")) == []
    assert set(check_subject.conventions()) == set(check_subject.kinds_mappers()), "instance/mappers.toml covers every mapper"


def test_an_artefact_with_a_mapper_and_no_short_is_refused_with_its_fix_not_blamed_on_the_document():
    """task-0149 (doc-0021 G5)."""
    rep = check_subject.check(_renewal("| REQ-01 | A renewal keeps the price. |\n", ["REQ-01|text"], short=False), REGISTER)
    [e] = _rules(rep)["required"]
    assert "no 'short'" in e["message"] and 'short = "renewal"' in e["fix"], e
    assert "mapper-failed" not in _rules(rep) and rep["exit_code"] == 1, rep["findings"]


def test_a_yielded_key_is_offered_once_and_another_entitys_key_is_no_typo():
    """task-0149 (doc-0021 G2): REQ-03|text goes to REQ-03|txt only; REQ-04|text, a requirement nobody
    wrote, is a NOTE, never offered REQ-03|text."""
    rows = "| REQ-01 | One. |\n| REQ-02 | Two. |\n| REQ-03 | Three. |\n"
    rep = check_subject.check(_renewal(rows, ["REQ-01|text", "REQ-02|text", "REQ-03|txt", "REQ-04|text"]), REGISTER)
    if rep["yield"]["state"] != "checked":
        return
    ws = _rules(rep, "warning").get("yield", [])
    assert [w["message"].split(":")[0] for w in ws] == ["REQ-03|txt"] and "REQ-03|text" in ws[0]["fix"], ws
    assert any(n["rule"] == "unyielded" and n["message"].startswith("REQ-04|text:") for n in rep["notes"]), rep["notes"]
    # alone, REQ-04|text's nearest yielded key is another entity's: a note that says so, no did-you-mean
    rep = check_subject.check(_renewal(rows, ["REQ-01|text", "REQ-02|text", "REQ-04|text"]), REGISTER)
    assert "yield" not in _rules(rep, "warning"), rep["findings"]
    [n] = [n for n in rep["notes"] if n["rule"] == "unyielded"]
    assert "REQ-03|text, is another entity's" in n["message"] and "not a misspelling" in n["message"], n
