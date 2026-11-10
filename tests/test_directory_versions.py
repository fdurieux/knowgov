"""task-0319: check_subject reads a directory artefact's Versions as the load does (decision-0019, decision-0036).

A small subject built in a temp dir: ``docs/`` (include ``*.md``, one directory artefact), ``docs/dmn/`` (``*.dmn``, nested
inside it) and ``one.json`` (a file artefact). ``[verification] execution`` and ``authored`` list the raw-byte digest of
each file. Stdlib only: no store, no pin."""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import check_subject  # noqa: E402

FILES = {"docs/a.md": "# a\n", "docs/b.md": "# b\n", "docs/dmn/t.dmn": "<d/>\n", "docs/skip.txt": "outside\n", "one.json": "{}\n"}


def _h(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _subject(base: Path, listed=None, name: str = "execution") -> Path:
    for rel, text in FILES.items():
        (base / rel).parent.mkdir(parents=True, exist_ok=True)
        (base / rel).write_text(text, encoding="utf-8")
    ds = listed if listed is not None else [_h(base / r) for r in ("docs/a.md", "docs/b.md", "docs/dmn/t.dmn", "one.json")]
    arts = "".join(f'[[artefact]]\nkey = "{k}"\nshort = "{s}"\nfamily = "f"\nformat = "x"\npath = "{p}"\n{i}\n'
                   for k, s, p, i in (("docs/", "doc", "docs", 'include = ["*.md"]'), ("docs/dmn/", "dmn", "docs/dmn", 'include = ["*.dmn"]'),
                                      ("one.json", "one", "one.json", "")))
    (base / "subject.toml").write_text(
        '[format]\nversion = 1\n\n[subject]\nid = "dv"\n\n[tasks.codegen]\nkeys = []\n\n[record]\nas_of = 2026-11-04\n\n'
        '[provenance]\nhuman = { id = "agent:t", name = "T" }\n\n[verification]\n'
        f'{name} = {{ at = "2026-11-04", versions = {ds!r} }}\n\n'.replace("'", '"') + arts, encoding="utf-8")
    return base


def _errs(base: Path) -> list[dict]:
    rep = check_subject.check(base, run_yield=False)
    return [f for f in rep["findings"] if f["rule"] == "attestation"]


def test_a_pristine_directory_subject_is_silent():
    with tempfile.TemporaryDirectory() as t:
        assert _errs(_subject(Path(t))) == []


def test_an_edited_file_names_that_file_and_not_the_nested_or_other_artefacts():
    """D1: the include and the nested artefact are the load's selection; the error names the changed file only."""
    with tempfile.TemporaryDirectory() as t:
        base = _subject(Path(t))
        with open(base / "docs/a.md", "a", encoding="utf-8") as f:
            f.write("more\n")
        new = _h(base / "docs/a.md")
        errs = _errs(base)
    assert len(errs) == 1, errs
    assert "docs/" in errs[0]["message"] and "a.md" in errs[0]["message"] and new in errs[0]["message"], errs
    assert "dmn" not in errs[0]["message"] and "one.json" not in errs[0]["message"] and "skip.txt" not in errs[0]["message"], errs


def test_a_file_added_within_the_include_is_an_error_naming_it_and_one_outside_changes_nothing():
    """D2: nothing stale, yet a new Version: the error comes from the comparison, not from a stale digest."""
    with tempfile.TemporaryDirectory() as t:
        base = _subject(Path(t))
        (base / "docs/skip2.txt").write_text("x\n", encoding="utf-8")
        assert _errs(base) == []
        (base / "docs/NEW.md").write_text("# new\n", encoding="utf-8")
        errs = _errs(base)
    assert len(errs) == 1 and errs[0]["level"] == "error" and "docs/" in errs[0]["message"] and "NEW.md" in errs[0]["message"], errs


def test_re_attesting_by_adding_keeps_the_old_digest_and_the_error_says_to_replace_it():
    """E1: the new digest listed beside the old one: the old matches no current Version, and the fix says to replace it."""
    with tempfile.TemporaryDirectory() as t:
        base = _subject(Path(t))
        old = _h(base / "one.json")
        ds = [_h(base / r) for r in ("docs/a.md", "docs/b.md", "docs/dmn/t.dmn", "one.json")]
        (base / "one.json").write_text("{ }\n", encoding="utf-8")
        _subject(base, ds + [_h(base / "one.json")])
        (base / "one.json").write_text("{ }\n", encoding="utf-8")
        ds2 = [_h(base / r) for r in ("docs/a.md", "docs/b.md", "docs/dmn/t.dmn", "one.json")] + [old]
        _subject(base, ds2)
        (base / "one.json").write_text("{ }\n", encoding="utf-8")
        errs = _errs(base)
    assert len(errs) == 1 and old in errs[0]["message"] and "matches no current Version" in errs[0]["message"], errs
    assert "replace the old digest with the new one" in errs[0]["fix"], errs
    assert "no Version of" not in errs[0]["message"]


def test_authored_or_approval_with_an_empty_list_is_noted_citing_decision_0019():
    """E2: bound to nothing, it attests nothing."""
    for name in ("authored", "approval"):
        with tempfile.TemporaryDirectory() as t:
            rep = check_subject.check(_subject(Path(t), [], name), run_yield=False)
        notes = [n for n in rep["notes"] if n["rule"] == "attestation" and n["where"] == f"[verification] {name}"]
        assert len(notes) == 1 and "decision-0019" in notes[0]["message"] and "attests nothing" in notes[0]["message"], notes


def test_the_public_subjects_and_the_claim_probe_check_as_before():
    for root in (ROOT / "subjects" / "cargo_quote", ROOT / "subjects" / "jef_data_load", ROOT / "tools" / "fixtures" / "claim_probe"):
        rep = check_subject.check(root, run_yield=False)
        assert [f for f in rep["findings"] if f["rule"] == "attestation" and f["level"] == "error"] == [], root
