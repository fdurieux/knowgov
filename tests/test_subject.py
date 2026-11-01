"""The subject root (harness/subject.py, subjects/README.md): CargoQuote and the minimal subject
load, every path a manifest names exists, every mapper it names is one the harness has, and no
module of the harness or the page names a subject, a document or a scenario id outside the
subject root. The mappers' own document conventions (harness/extract.py) are the stated
exception; subjects/README.md says so."""
from __future__ import annotations

import re
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import subject as subject_mod  # noqa: E402


def _mapper_names() -> set[str]:
    """The mapper registry of harness/extract.py, read from the source: importing the module
    needs pyyaml, which the tests job does not have."""
    src = (ROOT / "harness" / "extract.py").read_text(encoding="utf-8")
    body = src[src.index("EXTRACTORS = {"):src.index("def extract_all(")]
    return set(re.findall(r'^\s+"([a-z_]+)": extract_', body, re.M)) | {"links"}

CARGO = subject_mod.Subject(ROOT / "subjects" / "cargo_quote")
MINIMAL = subject_mod.Subject(ROOT / "subjects" / "minimal")


def test_cargo_quote_manifest_names_what_exists():
    assert CARGO.id == "cargo_quote" and CARGO.record_model == "gpt-5.1-2025-11-13"
    assert CARGO.order == ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
    assert len(CARGO.artefacts) == 11 and len(CARGO.kit_files) == 10, "ten documents on disk, one added by a plant"
    for key, p in CARGO.kit_files:
        assert p.is_file(), key
    mappers = _mapper_names()
    assert mappers >= {"requirements", "decision_table", "links"}, mappers
    for key, m in CARGO.mappers.items():
        assert m in mappers, (key, m)
    assert len(CARGO.mappers) == 10 and len(CARGO.shorts) == 10
    assert set(CARGO.store_keys) == {a["key"] for a in CARGO.artefacts} - {"notes/analysis_notes.md"}
    assert CARGO.reference_code().startswith('"""') or "def " in CARGO.reference_code()
    assert CARGO.oracle_script().is_file() and len(CARGO.suite_order) == 11
    assert set(CARGO.verification_map()) >= {"execution", "review"}
    assert len(CARGO.tasks["codegen"]["keys"]) == 36 and CARGO.three_valued and CARGO.record_dir.is_dir()
    for sc, s in CARGO.scenarios.items():
        name = s.get("prompts", "task_codegen")
        for arm in ("baseline", "governed"):
            assert (CARGO.root / "prompts" / f"{name}_{arm}.md").is_file(), (sc, name, arm)
    assert CARGO.plants_for("S2") and not CARGO.plants_for("S1") and CARGO.plants_for("S6", 2)
    assert CARGO.inferred and CARGO.inferred["candidate_for"] == CARGO.rules["declared_gap_id"]
    assert {q["id"] for q in CARGO.queries} == {"three-valued", "gate", "invalidation", "contradiction"}
    assert CARGO.register_map()["row"] and (CARGO.root / "vendor" / "SOURCE.md").is_file()
    assert CARGO.scenarios["S6"]["stage2"]["artefact"] in CARGO.families


def test_minimal_subject_is_empty_but_loads():
    assert MINIMAL.artefacts == [] and MINIMAL.kit_files == [] and MINIMAL.pristine() == {}
    assert MINIMAL.order == ["S0"] and MINIMAL.plants_for("S0") == [] and MINIMAL.inferred is None
    assert MINIMAL.tasks["codegen"]["keys"] == ["thing|property", "other|property"]
    assert MINIMAL.reference_code() == "" and MINIMAL.oracle_script() is None and MINIMAL.verification_map() == {}
    assert MINIMAL.record_dir == MINIMAL.root / "record" and not MINIMAL.record_dir.exists()
    assert MINIMAL.queries == [] and MINIMAL.register_map() == {}


def test_a_bare_manifest_loads_and_a_missing_one_is_refused():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        try:
            subject_mod.Subject(root)
            raise AssertionError("a directory without subject.toml must be refused")
        except FileNotFoundError as e:
            assert "subject.toml" in str(e)
        (root / "subject.toml").write_text('[subject]\nid = "bare"\n', encoding="utf-8")
        s = subject_mod.Subject(root)
        assert s.id == "bare" and s.order == [] and s.artefacts == [] and s.tasks == {}
        try:
            s.scenario("S1")
            raise AssertionError("an undeclared scenario must be refused")
        except KeyError as e:
            assert "bare" in str(e)


def test_subject_root_is_selected_by_the_environment():
    import os
    old = os.environ.get("KG_SUBJECT")
    try:
        os.environ["KG_SUBJECT"] = str(ROOT / "subjects" / "minimal")
        assert subject_mod.load().id == "minimal"
        os.environ.pop("KG_SUBJECT")
        assert subject_mod.load().id == "cargo_quote", "the default"
    finally:
        if old is not None:
            os.environ["KG_SUBJECT"] = old


def test_readme_documents_every_file_and_the_mapper_exception():
    text = (ROOT / "subjects" / "README.md").read_text(encoding="utf-8")
    for name in ("subject.toml", "scenarios.toml", "plants.toml", "queries.toml", "register_map.toml", "prompts/", "vendor/", "KG_SUBJECT"):
        assert name in text, name
    for section in ("[reference]", "[oracle]", "[provenance]", "[verification]", "[tasks.", "[three_valued]", "[rules]", "[register]", "[record]", "[scenario.stage2]", "[inferred]"):
        assert section in text, section
    assert "harness/extract.py" in text and "mapper" in text
    # the TOML the README shows parses
    for block in re.findall(r"```toml\n(.*?)```", text, re.S):
        tomllib.loads(block)


DOCUMENT_NAMES = ("requirements.md", "decision_table.md", "spec.md", "openapi.yaml", "quote_flow.puml", "containers.puml",
                  "quote_process.bpmn", "screening_decision.dmn", "acceptance.feature", "links.toml", "analysis_notes.md")
FORBIDDEN = re.compile(r"cargo_quote|CargoQuote|\bS[1-7]\b|" + "|".join(re.escape(d) for d in DOCUMENT_NAMES))


def _code_lines(p: Path):
    """Lines of code: comments, docstrings and the subject-root default are not code."""
    text = p.read_text(encoding="utf-8")
    text = re.sub(r'"""[\s\S]*?"""', "", text)
    for ln in text.splitlines():
        s = ln.split("#", 1)[0].rstrip()
        if not s.strip() or "subjects/cargo_quote" in s or "subjects\" / \"cargo_quote" in s:
            continue
        yield s


def test_no_module_names_the_subject_a_document_or_a_scenario():
    """AC: outside the subject root, nothing names CargoQuote, a kit file or a scenario id. The
    mappers (harness/extract.py) read CargoQuote's document conventions and are the exception
    subjects/README.md states; the page's JavaScript is checked for scenario ids only."""
    hits = []
    for p in [*(ROOT / "harness").glob("*.py"), *(ROOT / "demo" / "app").glob("*.py"), *(ROOT / "demo" / "tools").glob("*.py")]:
        if p.name == "extract.py":
            continue
        for s in _code_lines(p):
            if FORBIDDEN.search(s):
                hits.append(f"{p.relative_to(ROOT)}: {s.strip()[:100]}")
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    for ln in page.splitlines():
        if re.search(r"'S[1-7]'|\"S[1-7]\"|>S[1-7] ", ln):
            hits.append(f"demo/app/index.html: {ln.strip()[:100]}")
    assert not hits, "\n".join(hits)
    # the exception is bounded: the mappers name entities and phrases, never a scenario id
    assert not any(re.search(r"\bS[1-7]\b", s) for s in _code_lines(ROOT / "harness" / "extract.py"))
