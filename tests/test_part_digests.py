"""A directory artefact's file digests (task-0094): its Version's ``sha256`` is the whole bundle's, so
the load keeps each file's own in ``part_sha256``, both adapters through the port, the Turtle round
trip carries them and ``tools/check_round_trip.py`` compares them, and ``register-cites`` compares a
cited file with the register's digest. Stdlib only, with a live rdflib check when rdflib is there
(harness.yml and the stack job run the round trip and the saved query themselves)."""
from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

from tests._skip import need_rdflib  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]


def _methods(path: Path, cls: str) -> set[str]:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
    raise AssertionError(f"{cls} not in {path}")


def test_the_port_declares_the_part_digests_and_both_adapters_implement_them():
    ops = {"record_part_digests", "part_digests"}
    assert ops <= _methods(ROOT / "harness" / "store.py", "Store")
    assert ops <= _methods(ROOT / "harness" / "store_neo4j.py", "Neo4jStore")
    assert ops <= _methods(ROOT / "harness" / "store_rdflib.py", "RdflibStore")
    import mcp_server
    assert "record_part_digests" not in mcp_server.READS


def test_the_entries_are_sha256sums_form_sorted_by_path_and_read_back():
    import store
    a, b = hashlib.sha256(b"a").hexdigest(), hashlib.sha256(b"b").hexdigest()
    entries = store.part_list({"sub dir/b.md": b, "a.md": a})
    assert entries == [f"{a}  a.md", f"{b}  sub dir/b.md"]
    assert store.part_rows("contracts/", "v1", entries) == [
        {"artefact": "contracts/", "version": "v1", "part": "a.md", "sha256": a},
        {"artefact": "contracts/", "version": "v1", "part": "sub dir/b.md", "sha256": b}]
    assert store.part_rows("x", "v1", None) == []


def test_the_load_records_each_file_of_a_directory_artefact_and_no_other():
    src = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    assert 'if path.endswith("/"):' in src
    assert 'st.record_part_digests(f"V:{path}:{version_tag}", SUBJECT.part_digests(path, text))' in src
    from subject import bundle_parts
    text = "==> a.md <==\nalpha\n==> dmn/b.dmn <==\n<b/>\n"
    assert {rel: hashlib.sha256(p.encode()).hexdigest() for rel, p in bundle_parts(text) if rel} == {
        "a.md": hashlib.sha256(b"alpha\n").hexdigest(), "dmn/b.dmn": hashlib.sha256(b"<b/>\n").hexdigest()}


def test_the_rdflib_store_keeps_them_through_turtle():
    RdflibStore = need_rdflib().RdflibStore   # the tests job has no rdflib; the rdflib job runs it
    st = RdflibStore(path="")
    st.create_activity("act:extract:C:v1", "extraction", "2026-11-04T00:00:00+00:00", "harness", "", "agent:harness")
    st.upsert_artefact_version("contracts/", "contracts", "bundle", "V:contracts/:v1", "0" * 64, 10, "2026-11-04T00:00:00+00:00", "v1", "act:extract:C:v1")
    st.upsert_artefact_version("requirements.json", "requirements", "json", "V:requirements.json:v1", "1" * 64, 10, "2026-11-04T00:00:00+00:00", "v1", "act:extract:C:v1")
    st.record_part_digests("V:contracts/:v1", {"leg.md": "b" * 64, "chain.md": "a" * 64})
    want = [{"artefact": "contracts/", "version": "v1", "part": "chain.md", "sha256": "a" * 64},
            {"artefact": "contracts/", "version": "v1", "part": "leg.md", "sha256": "b" * 64}]
    assert st.part_digests() == want
    other = RdflibStore(path="")
    other.import_turtle(st.export_turtle())
    assert other.part_digests() == want


def test_the_round_trip_compares_them_and_ci_expects_them_on_jef():
    import check_round_trip as c
    p = {"artefact": "contracts/", "version": "v1", "part": "chain.md", "sha256": "a" * 64}
    base = {"gate": {}, "three_valued": {}, "census": {"nodes": 3}, "parts": [p, {**p, "part": "leg.md"}]}
    assert c.differences(base, {**base, "parts": base["parts"][::-1]}, "C") == []
    assert c.differences(base, {**base, "parts": []}, "C") == ["C: part digests differ: 2 -> 0"]
    assert c.differences(base, {**base, "parts": [p, {**p, "part": "leg.md", "sha256": "c" * 64}]}, "C") == ["C: part digests differ: 2 -> 2"]
    src = (ROOT / "tools" / "check_round_trip.py").read_text(encoding="utf-8")
    assert '"parts": st.part_digests()' in src and "--expect-parts" in src
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert "KG_SUBJECT=subjects/jef_data_load python tools/check_round_trip.py --chain rdflib,rdflib --expect-parts" in harness
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "-e KG_SUBJECT=/repo/subjects/jef_data_load app python tools/check_round_trip.py --chain neo4j,rdflib,neo4j --expect-parts" in demo


# ---- task-0098: each file's raw bytes, not its bundled text

def _dir_subject(td: Path, files: dict[str, bytes]):
    import subject
    (td / "docs").mkdir()
    for rel, data in files.items():
        (td / "docs" / rel).parent.mkdir(parents=True, exist_ok=True)
        (td / "docs" / rel).write_bytes(data)
    (td / "subject.toml").write_text('[subject]\nid = "probe"\n\n[[artefact]]\nkey = "docs/"\npath = "docs"\n'
                                     'family = "contracts"\nformat = "bundle"\n', encoding="utf-8")
    return subject.Subject(td)


def test_a_file_without_a_final_newline_keeps_the_digest_of_its_raw_bytes():
    """The bundle adds a newline a file lacks and reads it as text; the register digests the file's
    bytes (demo/app/register_project.py), so the load records those: a file with no final newline, one
    with CRLF line ends and an ordinary one each keep sha256 of their bytes on disk, which is not the
    digest of their bundled part for the first two; a part a plant changed keeps its text's digest."""
    import tempfile
    from subject import bundle_parts   # stdlib only: the tests job has no yaml, so never harness/load.py
    files = {"no_eol.md": b"last line, no newline", "crlf.md": b"one\r\ntwo\r\n", "sub/plain.md": b"plain\n"}
    with tempfile.TemporaryDirectory() as d:
        s = _dir_subject(Path(d), files)
        raw = {rel: hashlib.sha256(b).hexdigest() for rel, b in files.items()}
        assert s.raw_part_digests("docs/") == raw
        text = s.artefact_text("docs/")
        bundled = {rel: hashlib.sha256(p.encode()).hexdigest() for rel, p in bundle_parts(text) if rel}
        assert bundled["no_eol.md"] != raw["no_eol.md"] and bundled["crlf.md"] != raw["crlf.md"]
        assert bundled["sub/plain.md"] == raw["sub/plain.md"]
        assert s.part_digests("docs/", text) == raw
        planted = text.replace("last line, no newline", "a planted line")
        got = s.part_digests("docs/", planted)
        assert got["no_eol.md"] == hashlib.sha256(b"a planted line\n").hexdigest() != raw["no_eol.md"]
        assert {k: v for k, v in got.items() if k != "no_eol.md"} == {k: v for k, v in raw.items() if k != "no_eol.md"}
        assert s.raw_part_digests("docs/") and _file_subject_has_none(Path(d))


def _file_subject_has_none(td: Path) -> bool:
    import subject
    (td / "one.md").write_text("x", encoding="utf-8")
    (td / "subject.toml").write_text('[subject]\nid = "probe2"\n\n[[artefact]]\nkey = "one.md"\npath = "one.md"\n'
                                     'family = "prose"\nformat = "md"\n', encoding="utf-8")
    return subject.Subject(td).raw_part_digests("one.md") == {}


def test_every_committed_jef_file_matches_its_raw_digest_and_its_bundled_one():
    """On the public J-F subject every file of a directory artefact ends in a newline and has LF line
    ends, so its raw and bundled digests agree: the change moves no digest of the record."""
    import subject
    from subject import bundle_parts
    s = subject.Subject(ROOT / "subjects" / "jef_data_load")
    n = 0
    for key in (a["key"] for a in s.artefacts if a.get("path") and (s.root / a["path"]).is_dir()):
        raw = s.raw_part_digests(key)
        bundled = {rel: hashlib.sha256(p.encode()).hexdigest() for rel, p in bundle_parts(s.artefact_text(key)) if rel}
        assert raw == bundled, sorted(k for k in raw if raw[k] != bundled.get(k))
        n += len(raw)
    assert n >= 13, n
