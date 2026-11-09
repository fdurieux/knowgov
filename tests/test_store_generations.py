"""Task-0141.06 (S2, decision-0014): store generations, the parts that need no database. A read handle
checks after every read that the generation it pinned is still the published one and refuses
(StoreChanged) when it is not; ``store.read`` and the MCP server run the logical read again on a fresh
handle; a file-backed writer whose lock file was replaced publishes nothing (StoreFenced); the Neo4j
adapter keeps its publication node out of everything that reads the evidence. SNAP-01 to SNAP-08 on a
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


def test_a_reader_clears_an_abandoned_publication_only_under_the_lock_and_once_the_lease_ran_out():
    """task-0175: the reader's clearing takes the publication node's write lock before it reads, acts
    only while begin is above end and no live lease holds the node (so a writer that took the lease
    first, and closed the gap itself, makes it a no-op), closes at the last committed generation, frees
    the lease, moves the epoch past the abandoning writer and records it; pin calls it only when the
    lease is free or has run out, and otherwise waits and refuses as before. SNAP-08 runs both orders
    and a race on a real store."""
    src = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    rec = src.split("    def recover(self)", 1)[1].split("\n    def ", 1)[0]
    lock, guard = rec.index("SET p.lock_seq = coalesce(p.lock_seq, 0) + 1"), rec.index("WHERE p.begin <> p.end AND")
    assert lock < guard, "the lock is taken before the condition is read"
    assert "(p.owner IS NULL OR coalesce(p.expires < datetime(), true))" in rec
    # SNAP-11 (task-0274, decision-0014 A1, accepted 2026-11-09): the gap closes forward, end = begin, since the unit may have committed
    for part in ("p.end = p.begin", "p.owner = null", "p.epoch = p.epoch + 1", "p.abandoned_owner = owner", "p.abandoned_epoch = epoch"):
        assert part in rec, part
    assert "p.begin = p.end," not in rec and "SET p.begin = p.end\"" not in src and "SET p.begin = p.end)" not in src, \
        "no gap is ever closed backward"
    assert "self.meta(clear)" in rec, "one managed write transaction"
    pin = src.split("    def pin(self", 1)[1].split("\n    def ", 1)[0]
    assert pin.index('if st["owner"] is None or st["expired"]:') < pin.index("self.recover()") < pin.index("if time.monotonic() >= deadline:")
    assert "live lease" in pin and "abandoned" in pin
    # the writer's acquisition takes the same lock and closes a stale gap itself
    acq = src.split("    def acquire(self", 1)[1].split("\n    def ", 1)[0]
    assert "SET p.lock_seq = coalesce(p.lock_seq, 0) + 1" in acq and "p.end = p.begin" in acq
    snaps = (ROOT / "tools" / "check_snapshots.py").read_text(encoding="utf-8")
    assert "def snap_08(" in snaps and "snap_08(s1, s2, g1)" in snaps and "(writer first)" in snaps and "(race)" in snaps


class _Moving(_Inner):
    """A store republished during every read."""

    def extraction_activities(self):
        raise store.StoreChanged("republished")

    census = describe = held = extraction_activities


def _env(**kv):
    import contextlib

    @contextlib.contextmanager
    def cm():
        old = {k: os.environ.get(k) for k in kv}
        os.environ.update({k: v for k, v in kv.items() if v is not None})
        for k, v in kv.items():
            if v is None:
                os.environ.pop(k, None)
        try:
            yield
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    return cm()


def test_a_reader_whose_retries_run_out_answers_each_contract():
    """gate_cli --no-load exits 2 (cannot run); the page's /api/store and /api/gaps answer 503 with
    Retry-After and ``busy``; the MCP tool answers an error result (the test above)."""
    import gate_cli
    from subject import SUBJECT
    first = SUBJECT.order[0]   # the subject's own first scenario, under either subject
    real = store.open_store
    opened = []

    def fake_open(kind=None, *, access, **kw):
        h = store.ReadOnly(_Moving([1]))
        opened.append(h)
        return h
    store.open_store = fake_open
    try:
        assert gate_cli.main(["--no-load", "--scenario", first, "--as-of", "2026-11-06", "-f", "json"]) == 2
        assert len(opened) == 3
    finally:
        store.open_store = real
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import contextlib
    import server

    @contextlib.contextmanager
    def moving(timeout=3):
        yield store.ReadOnly(_Moving([1]))
    real_store = server._store
    server._store = moving
    try:
        st, gaps = server.store_status(), server.store_gaps(first)
    finally:
        server._store = real_store
    assert st["busy"] and "republished" in st["error"] and gaps["busy"], (st, gaps)
    sent = []

    class H:
        def _json(self, obj, code=200, extra=None):
            sent.append((code, extra))
    server._busy_json(H(), st)
    server._busy_json(H(), {"error": "unreachable"})
    assert sent == [(503, {"Retry-After": "1"}), (200, None)]


def test_the_generation_settings_have_defaults_and_refuse_nonsense():
    with _env(KG_STORE_READ_ATTEMPTS=None, KG_NEO4J_LEASE_SECONDS=None, KG_NEO4J_LOCK_TIMEOUT=None, KG_NEO4J_READ_WAIT=None):
        assert [store.setting(n) for n in ("KG_STORE_READ_ATTEMPTS", "KG_NEO4J_LEASE_SECONDS", "KG_NEO4J_LOCK_TIMEOUT", "KG_NEO4J_READ_WAIT")] == [3, 60.0, 60.0, 10.0]
        assert store.setting("KG_NEO4J_LOCK_TIMEOUT", 3) == 3.0   # the page's connection timeout, when nothing is set
    for name, bad in (("KG_STORE_READ_ATTEMPTS", "0"), ("KG_STORE_READ_ATTEMPTS", "2.5"), ("KG_STORE_READ_ATTEMPTS", "99"),
                      ("KG_NEO4J_LEASE_SECONDS", "soon"), ("KG_NEO4J_LEASE_SECONDS", "0.1"), ("KG_NEO4J_LOCK_TIMEOUT", "-1"),
                      ("KG_NEO4J_READ_WAIT", "nan"), ("KG_NEO4J_READ_WAIT", "1e9")):
        with _env(**{name: bad}):
            try:
                store.setting(name)
            except ValueError as e:
                assert name in str(e), e
            else:
                raise AssertionError(f"{name}={bad!r} accepted")
    with _env(KG_NEO4J_LEASE_SECONDS="5"):
        assert store.setting("KG_NEO4J_LEASE_SECONDS") == 5.0



def test_a_nan_setting_is_refused_by_isnan():
    """task-0246: the bound check reads math.isnan(v), not v != v, with the same meaning: every float setting
    refuses a NaN however it is spelt."""
    floats = [n for n, (default, _, _) in store.SETTINGS.items() if isinstance(default, float)]
    assert floats
    for name in floats:
        for bad in ("nan", "NaN", "-nan", "+nan"):
            with _env(**{name: bad}):
                try:
                    store.setting(name)
                except ValueError as e:
                    assert name in str(e), e
                else:
                    raise AssertionError(f"{name}={bad!r} accepted")
    assert "math.isnan(v)" in (ROOT / "harness" / "store.py").read_text(encoding="utf-8")


def test_end_is_set_after_the_units_commit_never_inside_it():
    """SNAP-11 (task-0274, decision-0014 A1, accepted 2026-11-09): Neo4j showed a committing unit's new ``end`` to lock-free readers
    before its last records, so ``end`` is written in a transaction of its own after ``commit()`` returns. The
    fence (the epoch checked under the node's lock, held to the commit) stays inside the unit. On a real store
    SNAP-11 holds a writer between the two and races 24 publications under six readers."""
    src = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    pub = src.split("    def publish(self)", 1)[1].split("\n    def ", 1)[0]
    body = pub.split('"""', 2)[2]   # the code, past the docstring
    fence, commit, after = body.index("self.owned(tx)"), body.index("tx.commit()"), body.index("self.committed()")
    assert fence < commit < after, "the fence in the unit, then its commit, then end in its own transaction"
    assert 'self.owned(tx, "SET p.end' not in src, "end is never written in the unit's transaction"
    done = src.split("    def committed(self)", 1)[1].split("\n    def ", 1)[0]
    assert done.index("_on_committed(self)") < done.index('self.meta(lambda t: self.owned(t, "SET p.end = p.begin"))')
    gone = src.split("    def abandon(self", 1)[1].split("\n    def ", 1)[0]
    assert 'SET p.end = p.begin' in gone and "SET p.begin = p.end" not in gone, "a failed publication closes its gap forward"
    snaps = (ROOT / "tools" / "check_snapshots.py").read_text(encoding="utf-8")
    assert "def snap_11(" in snaps and "snap_11(s1, s2, g1, g2)" in snaps and "RACE_11, READERS_11 = 24, 6" in snaps
