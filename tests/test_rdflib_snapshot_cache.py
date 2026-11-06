"""Task-0097: a read handle on a file-backed rdflib store reuses the process's parse of the published
file while the file is the same publication, and parses again after a publication, so a read never
answers from a retired generation; a held read handle keeps the generation it opened on (decision-0014);
concurrent read handles parse once; a writer never shares or fills the cache. Needs rdflib (the rdflib
job, and a venv with the pins)."""
from __future__ import annotations

import os
import sys
import tempfile
import threading
from pathlib import Path

from tests._skip import need_rdflib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))


def _publish(path: str, nid: str) -> None:
    sr = need_rdflib()
    w = sr.RdflibStore(path=path, access="write")
    try:
        w.create_node(nid, ["Thing"], {"name": nid})
        w.commit()
    finally:
        w.close()


def test_two_reads_parse_once_and_a_publication_is_read_at_once():
    sr = need_rdflib()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "store.ttl")
        _publish(path, "a")
        sr.drop_snapshot()
        before = sr._parses
        r1 = sr.RdflibStore(path=path, access="read")
        r2 = sr.RdflibStore(path=path, access="read")
        assert sr._parses == before + 1 and r1.g is r2.g, "the second read handle parsed the file again"
        assert r2.exists("a") and not r2.exists("b")
        _publish(path, "b")   # a publication: an atomic replace of the file
        r3 = sr.RdflibStore(path=path, access="read")
        assert sr._parses == before + 2 and r3.exists("b"), "a read after a publication answered the retired generation"
        assert not r1.exists("b"), "a held read handle must keep the generation it opened on (decision-0014)"
        r4 = sr.RdflibStore(path=path, access="read")
        assert sr._parses == before + 2 and r4.g is r3.g
        assert len(r4.g) == len(r3.g) and r4.exists("a")


def test_concurrent_read_handles_fill_the_cache_once_and_see_one_generation():
    sr = need_rdflib()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "store.ttl")
        for i in range(30):
            _publish(path, f"n{i}")
        sr.drop_snapshot()
        before, got, errors = sr._parses, [], []
        go = threading.Barrier(12)

        def read():
            try:
                go.wait()
                r = sr.RdflibStore(path=path, access="read")
                got.append((id(r.g), len(r.g), r.exists("n29")))
            except Exception as e:  # noqa: BLE001
                errors.append(e)
        threads = [threading.Thread(target=read) for _ in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(60)
        assert not errors, errors
        assert sr._parses == before + 1, sr._parses - before
        assert len(got) == 12 and len({g for g, _, _ in got}) == 1 and all(seen for _, _, seen in got), got


def test_a_writer_neither_uses_nor_fills_the_cache():
    sr = need_rdflib()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "store.ttl")
        _publish(path, "a")
        sr.drop_snapshot()
        r = sr.RdflibStore(path=path, access="read")
        cached = sr._snapshot
        w = sr.RdflibStore(path=path, access="write")
        try:
            assert w.g is not r.g and sr._snapshot is cached
            w.create_node("w", ["Thing"], {})
            assert not r.exists("w") and not sr.RdflibStore(path=path, access="read").exists("w")
        finally:
            w.close()   # closed without commit: nothing published, the cached generation still current
        assert sr._snapshot is cached
        missing = sr.RdflibStore(path=os.path.join(d, "none.ttl"), access="read")
        assert missing.absent and sr._snapshot is cached
