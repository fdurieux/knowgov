"""task-0229: a Neo4j writer's close never races its own lease heartbeat. ``close()`` used to stop the heartbeat
without waiting for it and then close the driver, which closes every connection, the beat's included: a beat
in the middle of a send then met the driver's GOODBYE on the same connection and the close raised the driver's
``BufferError`` (main's stack job at c29cd3f). Now ``release()`` joins the beat within its bound, and past it
raises HeartbeatAlive and leaves the driver open. A fake driver here; on a real server tools/check_snapshots.py's
SNAP-10 closes writers in the middle of a beat's send (the stack job)."""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import store_neo4j  # noqa: E402


class _Result:
    def __init__(self, row=None):
        self.row = row or {"owner": None, "expired": True, "epoch": 1, "begin": 0, "end": 0}

    def consume(self):
        return None

    def single(self):
        return self.row

    def __iter__(self):
        return iter(())


class _Tx:
    def run(self, cypher, **params):
        return _Result()


class _Driver:
    """The beat's transaction (any managed write off the main thread) blocks until ``free`` is set."""

    def __init__(self):
        self.in_beat = threading.Event()
        self.free = threading.Event()
        self.flight = 0
        self.closed = False
        self.lock = threading.Lock()

    def session(self, **_kw):
        return _Session(self)

    def close(self):
        self.closed = True


class _Session:
    def __init__(self, d):
        self.d = d
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run(self, cypher, **params):
        return _Result()

    def close(self):
        self.closed = True

    def execute_write(self, work):
        beat = threading.current_thread() is not threading.main_thread()
        if beat:
            with self.d.lock:
                self.d.flight += 1
            self.d.in_beat.set()
            self.d.free.wait(10)
        try:
            return work(_Tx())
        finally:
            if beat:
                with self.d.lock:
                    self.d.flight -= 1


def _unit(d):
    u = store_neo4j._Unit(d, _Session(d), "bolt://probe", "write", "r", "w")
    u.acquire(1.0, 0.03)   # a beat every 10 ms
    assert d.in_beat.wait(5), "the heartbeat never beat"
    return u


def test_release_waits_for_a_beat_in_flight():
    d = _Driver()
    u = _unit(d)
    threading.Timer(0.3, d.free.set).start()   # the beat's send finishes 0.3 s after the close begins
    t0 = time.monotonic()
    u.release()
    assert d.flight == 0, "release() returned while a beat was still using the driver"
    assert time.monotonic() - t0 >= 0.25 and u.token is None


def test_a_beat_past_its_bound_is_named_and_the_driver_left_open():
    d = _Driver()
    u = _unit(d)
    u.join_s = 0.2
    try:
        u.release()
        raise AssertionError("a beat still running was not reported")
    except store_neo4j.HeartbeatAlive as e:
        assert "heartbeat" in str(e) and not isinstance(e, store_neo4j.StoreBusy), "never read as a refusal to retry"
    st = store_neo4j.Neo4jStore.__new__(store_neo4j.Neo4jStore)
    st._driver, st._session, st._pub = d, _Session(d), u
    try:
        st.close()
        raise AssertionError("close() hid a beat still running")
    except store_neo4j.HeartbeatAlive:
        pass
    assert not d.closed and st._session.closed, "the driver is never closed under a running beat"
    d.free.set()
    u.beat.join(5)
    st.close()
    assert d.closed, "once the beat ended, close() closes the driver"


def test_the_join_bound_follows_the_beats_own_bounds():
    src = (ROOT / "harness" / "store_neo4j.py").read_text(encoding="utf-8")
    assert '"max_transaction_retry_time": RETRY_S' in src and "RETRY_S + (connection_timeout or CONNECT_S)" in src
    body = src.split("    def close(self) -> None:\n        \"\"\"Release the handle", 1)[1].split("\n    def ", 1)[0]
    assert body.index("self._pub.release()") < body.index("self._driver.close()"), "the beat is joined before the driver closes"
