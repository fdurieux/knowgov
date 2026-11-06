"""Task-0141.06 (S2, decision-0013): store generations, the parts that need no database. A read handle
checks after every read that the generation it pinned is still the published one and refuses
(StoreChanged) when it is not; ``store.read`` and the MCP server run the logical read again on a fresh
handle; a file-backed writer whose lock file was replaced publishes nothing (StoreFenced); the Neo4j
adapter keeps its publication node out of everything that reads the evidence. SNAP-01 to SNAP-07 on a
real store are ``tools/check_snapshots.py``, run by both workflows."""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

from tests._skip import need_rdflib

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

import store  # noqa: E402


class _Inner:
    """An adapter stand-in whose published generation moves when told to."""
    name = "fake"
    instance = ""

    def __init__(self, gen):
        self.gen = gen
        self.pinned = gen[0]
        self.closed = False

    def census(self):
        return {"generation": self.gen[0]}

    def _after_read(self):
        if self.gen[0] != self.pinned:
            raise store.StoreChanged("moved")

    def close(self):
        self.closed = True


def test_a_read_handle_refuses_the_read_after_a_publication_and_never_answers_from_two_generations():
    gen = [1]
    h = store.ReadOnly(_Inner(gen))
    assert h.census() == {"generation": 1}
    gen[0] = 2
    try:
        h.census()
    except store.StoreChanged:
        pass
    else:
        raise AssertionError("a read after a publication answered")
    try:
        h.wipe()
    except store.StoreReadOnly:
        pass
    else:
        raise AssertionError("a read handle wiped")


def test_store_read_runs_the_logical_read_again_on_a_fresh_handle_and_gives_up_after_its_attempts():
    gen, opened = [1], []

    def fake_open(kind=None, *, access, **kw):
        assert access == "read"
        h = store.ReadOnly(_Inner(gen))
        opened.append(h)
        return h
    real = store.open_store
    store.open_store = fake_open
    try:
        def moves_once(st):
            a = st.census()
            if len(opened) == 1:
                gen[0] += 1   # published between the two reads of the first attempt
            return a, st.census()
        a, b = store.read(moves_once)
        assert a == b and len(opened) == 2, (a, b, len(opened))

        def always_moves(st):
            st.census()
            gen[0] += 1
            return st.census()
        opened.clear()
        try:
            store.read(always_moves, attempts=3)
        except store.StoreChanged:
            pass
        else:
            raise AssertionError("an always-moving store answered")
        assert len(opened) == 3 and all(h._inner.closed for h in opened)
    finally:
        store.open_store = real


def test_the_mcp_server_runs_a_call_again_when_a_publication_lands_during_it():
    import mcp_server
    gen, opened = [1], []

    def opener():
        h = mcp_server.ReadOnlyStore(store.ReadOnly(_Inner(gen)))
        opened.append(h)
        return h
    t = mcp_server.Tools(opener=opener, as_of="2026-11-06")

    def call(st):
        st.census()
        if len(opened) == 1:
            gen[0] += 1
        return st.census()
    assert t._with_store(call) == {"generation": 2} and len(opened) == 2

    def always(st):
        st.census()
        gen[0] += 1
        return st.census()
    try:
        t._with_store(always)
    except mcp_server.ToolError as e:
        assert "republished" in str(e)
    else:
        raise AssertionError("an always-moving store answered")


def test_snap_05_a_file_writer_whose_lock_file_was_replaced_publishes_nothing():
    need_rdflib()
    from store_rdflib import RdflibStore
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "store.ttl")
        with RdflibStore(path=path, access="write") as st:
            st.ensure_entity("E1", "requirement", "first")
        before = Path(path).read_bytes()
        a = RdflibStore(path=path, access="write")
        a.ensure_entity("E2", "requirement", "the former writer's")
        os.unlink(path + ".lock")   # ownership recovered: the lock file cleared
        with RdflibStore(path=path, access="write", lock_timeout=5) as b:
            b.ensure_entity("E3", "requirement", "the recovering writer's")
        after_b = Path(path).read_bytes()
        try:
            a.commit()
        except store.StoreFenced:
            pass
        else:
            raise AssertionError("the former writer published")
        finally:
            a.close()
        assert Path(path).read_bytes() == after_b != before
        assert b"E3" in after_b and b"E2" not in after_b


def test_the_neo4j_publication_node_stays_out_of_the_evidence():
    """Every whole-graph statement of the Neo4j adapter leaves the publication node out: the wipe, the
    export and the census (the evidence schema and the record's D2 are unchanged)."""
    src = (HARNESS / "store_neo4j.py").read_text(encoding="utf-8")
    whole = re.findall(r'"(MATCH \(n\)[^"]*)"', src)
    unfiltered = [q for q in whole if not q.startswith("MATCH (n) WHERE NOT n:{PUB} ")]
    assert len(whole) >= 4 and unfiltered == [], f"a whole-graph statement without the publication filter: {unfiltered}"
    assert 'metadata={"kg_writer"' in src and "TERMINATE TRANSACTIONS" in src


def test_both_workflows_run_the_snapshot_checks_on_a_real_store():
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert "KG_STORE=rdflib python tools/check_snapshots.py --disposable\n" in harness
    assert "docker compose exec -T app python tools/check_snapshots.py --disposable --no-round-trip" in demo
    # SNAP-07's round trips on Neo4j are the stack job's own steps, which must stay
    assert "check_round_trip.py --chain neo4j,rdflib,neo4j" in demo and "--expect-parts" in demo and "--expect-preload" in demo
