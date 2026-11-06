"""task-0160: a file artefact's Version digest is the SHA-256 of its raw bytes, as the register's digest of a
cited file is (demo/app/register_project.py), so register-cites reads an unchanged CRLF file as the same as
the tag. A planted text has no bytes on disk and keeps its text's digest; a directory artefact's Version
keeps its bundle's, its files their own raw digests (task-0098). Stdlib, with the rdflib round trip when
rdflib is there (the rdflib job requires it)."""
from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
from tests._skip import need_rdflib  # noqa: E402

KEY = "kit/requirements.md"


def _crlf_probe(td: str):
    """tools/fixtures/subject_probe copied, its one file artefact rewritten with CRLF line ends."""
    import subject
    root = Path(td) / "probe"
    shutil.copytree(ROOT / "tools" / "fixtures" / "subject_probe", root)
    f = root / "requirements.md"
    f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert b"\r\n" in f.read_bytes()
    return subject.load(root), f


def test_a_crlf_file_artefacts_version_digest_is_its_raw_bytes_and_the_registers():
    with tempfile.TemporaryDirectory() as td:
        s, f = _crlf_probe(td)
        raw = f.read_bytes()
        text = s.artefact_text(KEY)
        assert "\r" not in text, "read_text turns CRLF into LF: the digest of the text is not the file's"
        digest, size = s.version_digest(KEY, text)
        assert (digest, size) == (hashlib.sha256(raw).hexdigest(), len(raw))
        assert digest != hashlib.sha256(text.encode()).hexdigest()
        # what register-cites compares v.sha256 with: the register's digest of the cited file
        import register_project
        assert register_project._digest(f) == digest, "register-cites would read 'differs' for an unchanged file"
        # a planted text has no bytes on disk: its own digest, as before
        planted = text.replace("REQ-01", "REQ-01 planted", 1)
        assert s.version_digest(KEY, planted) == (hashlib.sha256(planted.encode()).hexdigest(), len(planted.encode()))


def test_an_lf_file_and_the_public_subjects_keep_their_digests():
    """AC #3: no public subject's file artefact moves; an LF file's raw digest is its text's."""
    import subject
    for sid in ("cargo_quote", "jef_data_load"):
        s = subject.load(ROOT / "subjects" / sid)
        for key, p in s.kit_files:
            text = s.artefact_text(key)
            got = s.version_digest(key, text)
            assert got == (hashlib.sha256(text.encode()).hexdigest(), len(text.encode())), (sid, key, "a recorded digest would move")


def test_the_load_takes_the_version_digest_from_the_subject():
    src = (ROOT / "harness" / "load.py").read_text(encoding="utf-8")
    assert "digest, size = SUBJECT.version_digest(path, text)" in src
    assert 'st.upsert_artefact_version(path, family, fmt, f"V:{path}:{version_tag}", digest, size, ts, version_tag, aid)' in src


def test_the_rdflib_store_keeps_the_raw_digest_through_turtle():
    RdflibStore = need_rdflib().RdflibStore
    with tempfile.TemporaryDirectory() as td:
        s, _f = _crlf_probe(td)
        digest, size = s.version_digest(KEY, s.artefact_text(KEY))
    st = RdflibStore(path="")
    st.create_activity("act:extract:S1:v1", "extraction", "2026-11-06T00:00:00+00:00", "harness", "", "agent:harness")
    st.upsert_artefact_version(KEY, "requirements", "markdown", f"V:{KEY}:v1", digest, size, "2026-11-06T00:00:00+00:00", "v1", "act:extract:S1:v1")
    back = RdflibStore(path="")
    back.import_turtle(st.export_turtle())
    v = next(iter(back.nodes("Version")))
    assert back.prop(v, "sha256") == digest and back.prop(v, "bytes") == size
