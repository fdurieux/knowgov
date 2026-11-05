"""Task-0141.02 (S1): the file-backed store's lifecycle. A read handle never publishes; a writer takes its
lock before it loads the snapshot it starts from and publishes atomically on commit, never on close; a
failure publishes nothing and releases the lock; a corrupt file fails explicitly. ST-01 to ST-09 of the
review's plan. A second writer runs as a child process driven line by line over its stdin and stdout,
so every interleaving is set by a message, never by a sleep, and every wait is bounded."""
from __future__ import annotations

import os
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from tests._skip import need_rdflib

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))
WAIT = 60   # seconds: the bound on any one message from a child

# The child: one store handle, driven by commands on stdin, one line of reply each on stdout.
CHILD = r'''
import os, sys
sys.path.insert(0, sys.argv[1])
import store_rdflib as sr
from store import StoreBusy
path = sys.argv[2]
st = None
def say(*a):
    print(*a, flush=True)
def on_wait(_):
    say("waiting")
sr._on_lock_wait = on_wait
for line in sys.stdin:
    cmd, *arg = line.split()
    try:
        if cmd == "open":
            st = sr.RdflibStore(path=path, access="write", lock_timeout=float(arg[0]) if arg else 60)
            say("opened", "waited" if st.lock_waited else "first", "has:" + ",".join(sorted(n for n in st._nodes if n.startswith("ent:"))))
        elif cmd == "add":
            st.ensure_entity(arg[0], "Entity", arg[0]); say("ok")
        elif cmd == "wipe":
            st.wipe(); say("ok")
        elif cmd == "pause":
            real = sr._replace
            def paused(src, dst):
                say("paused", src)
                if sys.stdin.readline().strip() != "go":
                    raise SystemExit(3)
                real(src, dst)
            sr._replace = paused; say("ok")
        elif cmd == "commit":
            st.commit(); say("committed")
        elif cmd == "close":
            st.close(); say("closed")
        elif cmd == "exit":
            break
    except Exception as e:
        say("error", type(e).__name__)
'''


class Child:
    """A writer in another process, as another CLI run would be."""

    def __init__(self, path: Path):
        self.p = subprocess.Popen([sys.executable, "-c", CHILD, str(HARNESS), str(path)], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.q: queue.Queue = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.p.stdout:
            self.q.put(line.strip())
        self.q.put(None)

    def send(self, line: str) -> None:
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def expect(self, prefix: str) -> str:
        line = self.q.get(timeout=WAIT)
        assert line is not None and line.startswith(prefix), (prefix, line)
        return line

    def ask(self, line: str, prefix: str) -> str:
        self.send(line)
        return self.expect(prefix)

    def end(self) -> None:
        if self.p.poll() is None:
            try:
                self.send("exit")
            except (BrokenPipeError, OSError):
                pass
        try:
            self.p.wait(timeout=WAIT)
        finally:
            if self.p.poll() is None:
                self.p.kill()
                self.p.wait(timeout=WAIT)


def _write(path: Path, *ids: str, wipe: bool = True) -> bytes:
    sr = need_rdflib()
    with sr.RdflibStore(path=str(path), access="write") as st:
        if wipe:
            st.wipe()
        for i in ids:
            st.ensure_entity(i, "Entity", i)
    return path.read_bytes()


def _ids(path: Path) -> set[str]:
    sr = need_rdflib()
    st = sr.RdflibStore(path=str(path), access="read")
    try:
        return {n for n in st._nodes if n.startswith("ent:")}
    finally:
        st.close()


def _lock_free(path: Path) -> bool:
    """Whether a writer could take the store's lock now, asked of the lock file itself."""
    import fcntl
    fd = os.open(str(path) + ".lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    finally:
        os.close(fd)   # closing the descriptor releases a lock it took
    return True


def _temps(path: Path) -> list[str]:
    sr = need_rdflib()
    return [n for n in os.listdir(path.parent) if n.startswith(sr.TMP_PREFIX)]


class _Spy:
    """Counts publications in this process: the replacement step every commit ends with."""

    def __init__(self):
        self.sr = need_rdflib()
        self.calls = 0

    def __enter__(self):
        self.real = self.sr._replace

        def spy(src, dst):
            self.calls += 1
            return self.real(src, dst)
        self.sr._replace = spy
        return self

    def __exit__(self, *exc):
        self.sr._replace = self.real


def test_st_01_closing_a_stale_reader_cannot_restore_its_snapshot_over_a_newer_write():
    sr = need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        _write(path, "ent:old")
        from store import open_store
        a = open_store("rdflib", access="read", path=str(path))
        assert a.census()["nodes"] >= 1
        b = Child(path)
        try:
            b.ask("open", "opened first")
            b.ask("wipe", "ok")
            b.ask("add ent:new", "ok")
            b.ask("commit", "committed")
            b.ask("close", "closed")
        finally:
            b.end()
        newer = path.read_bytes()
        with _Spy() as spy:
            a.close()
        assert spy.calls == 0, "closing a reader published"
        assert path.read_bytes() == newer and _ids(path) == {"ent:new"}, _ids(path)


def test_st_02_the_page_and_the_mcp_server_read_and_never_publish():
    need_rdflib()
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import gate_cli
    import mcp_server
    from store import open_store
    from subject import SUBJECT
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        sc = SUBJECT.order[0]
        with open_store("rdflib", access="write", path=str(path), instance=SUBJECT.id) as st:
            gate_cli._load(st, sc)
        before, stamp = path.read_bytes(), path.stat().st_mtime_ns
        old = {k: os.environ.get(k) for k in ("KG_STORE", "KG_RDFLIB_FILE", "KG_TODAY")}
        os.environ.update(KG_STORE="rdflib", KG_RDFLIB_FILE=str(path), KG_TODAY="2026-11-05")
        try:
            import server
            tools = mcp_server.Tools(as_of="2026-11-05", runs=Path(td) / "runs")
            with _Spy() as spy:
                for _ in range(2):   # opened, released and opened again
                    status = server.store_status()
                    assert status["reachable"] and status["loaded"] == sc, status
                    assert server.store_gaps(sc)["match"]
                    server.node_statements("CAP-0001")
                    assert tools.store_status({})["scenario"] == sc
                    assert tools.gate_verdict({"scenario": sc})["verdict"] in ("PROCEED", "QUALIFIED", "BLOCKED")
            assert spy.calls == 0, f"{spy.calls} publication(s) from reads"
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        assert path.read_bytes() == before and path.stat().st_mtime_ns == stamp
        assert _lock_free(path), "a read left the writer's lock held"


def test_st_03_a_read_handle_refuses_every_change_and_the_file_is_untouched():
    sr = need_rdflib()
    from store import READS, ReadOnly, StoreReadOnly, open_store
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        before = _write(path, "ent:a")
        h = open_store("rdflib", access="read", path=str(path))
        assert isinstance(h, ReadOnly)
        refused = []
        for name in ("wipe", "ensure_entity", "create_assertion", "project_register", "import_turtle", "invalidate_keys",
                     "register_derived", "console_query", "commit"):
            try:
                getattr(h, name)
            except StoreReadOnly:
                refused.append(name)
                continue
            if name == "commit":
                try:
                    h.commit()
                except StoreReadOnly:
                    refused.append(name)
        assert len(refused) == 9, refused
        assert {"census", "key_evidence", "describe"} <= READS and h.census()["nodes"] >= 1
        h.close()
        raw = sr.RdflibStore(path=str(path), access="read")   # the adapter itself refuses to publish in read mode
        raw.wipe()
        try:
            raw.commit()
        except StoreReadOnly:
            pass
        else:
            raise AssertionError("a read-mode adapter published")
        raw.close()
        assert path.read_bytes() == before


def test_st_04_a_second_writer_waits_for_the_first_and_starts_from_its_publication():
    sr = need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        _write(path, "ent:base")
        a = Child(path)
        b = None
        try:
            a.ask("open", "opened first has:ent:base")
            a.ask("add ent:a", "ok")
            try:   # the conflict policy at no wait: refused, nothing loaded or changed
                sr.RdflibStore(path=str(path), access="write", lock_timeout=0)
            except sr.StoreBusy:
                pass
            else:
                raise AssertionError("a second writer opened while the first held the lock")
            b = Child(path)
            b.send("open 60")
            b.expect("waiting")                       # B found the lock held before loading anything
            a.ask("commit", "committed")
            a.ask("close", "closed")
            got = b.expect("opened waited")           # B loads only now, after A's publication
            assert got.endswith("has:ent:a,ent:base"), got
            b.ask("add ent:b", "ok")
            b.ask("commit", "committed")
            b.ask("close", "closed")
        finally:
            a.end()
            if b:
                b.end()
        assert _ids(path) == {"ent:base", "ent:a", "ent:b"}, _ids(path)


def test_st_05_a_reader_during_a_publication_gets_the_whole_old_file_or_the_whole_new_one():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        old = _write(path, *(f"ent:old{i}" for i in range(200)))
        w = Child(path)
        try:
            w.ask("open", "opened first")
            w.ask("wipe", "ok")
            for i in range(200):
                w.ask(f"add ent:new{i}", "ok")
            w.ask("pause", "ok")
            w.send("commit")
            w.expect("paused")                        # the new file is written and synced beside the old one
            assert _temps(path), "no temporary file: the pause is not inside the publication"
            for _ in range(5):
                assert path.read_bytes() == old
                ids = _ids(path)
                assert len(ids) == 200 and all(i.startswith("ent:old") for i in ids)
            w.send("go")
            w.expect("committed")
            w.ask("close", "closed")
        finally:
            w.end()
        ids = _ids(path)
        assert len(ids) == 200 and all(i.startswith("ent:new") for i in ids)
        assert not _temps(path)


def test_st_06_a_failed_serialisation_sync_or_replacement_keeps_the_previous_file_and_releases_the_lock():
    sr = need_rdflib()

    def boom(*a, **k):
        raise OSError("injected")

    def partial(destination=None, format=None, **k):
        destination.write(b"@prefix kg: <urn:kg:> .\n<urn:kg:n:half")
        raise OSError("injected mid-serialisation")

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        before = _write(path, "ent:keep")
        for step in ("serialise", "fsync", "replace"):
            saved = sr._fsync, sr._replace
            try:
                if step == "fsync":
                    sr._fsync = boom
                elif step == "replace":
                    sr._replace = boom
                try:
                    with sr.RdflibStore(path=str(path), access="write") as st:
                        st.wipe()
                        st.ensure_entity("ent:lost", "Entity", "lost")
                        if step == "serialise":
                            st.g.serialize = partial
                except OSError as e:
                    assert "injected" in str(e), e
                else:
                    raise AssertionError(f"{step}: a failed commit was reported as done")
            finally:
                sr._fsync, sr._replace = saved
            assert path.read_bytes() == before, step
            assert not _temps(path), (step, _temps(path))
            assert _lock_free(path), f"{step}: the lock was kept"
        assert _ids(path) == {"ent:keep"}


def test_st_07_a_writer_that_raises_publishes_nothing():
    sr = need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        before = _write(path, "ent:keep")
        with _Spy() as spy:
            try:
                with sr.RdflibStore(path=str(path), access="write") as st:
                    st.wipe()
                    st.ensure_entity("ent:half", "Entity", "half")
                    raise ValueError("the unit of work failed")
            except ValueError:
                pass
            st2 = sr.RdflibStore(path=str(path), access="write")   # closed without commit: nothing either
            st2.wipe()
            st2.close()
        assert spy.calls == 0 and path.read_bytes() == before and _lock_free(path)


def test_st_08_a_writer_killed_before_publication_leaves_the_last_snapshot_and_a_recoverable_lock():
    sr = need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        before = _write(path, "ent:good")
        w = Child(path)
        try:
            w.ask("open", "opened first")
            w.ask("wipe", "ok")
            w.ask("add ent:never", "ok")
            w.ask("pause", "ok")
            w.send("commit")
            w.expect("paused")
            assert _temps(path)
            w.p.send_signal(signal.SIGKILL)
            w.p.wait(timeout=WAIT)
        finally:
            w.end()
        assert path.read_bytes() == before
        with sr.RdflibStore(path=str(path), access="write", lock_timeout=10) as st:   # the dead writer's lock died with it
            assert set(st._nodes) >= {"ent:good"} and not _temps(path), "the interrupted commit's file was not swept"
            st.ensure_entity("ent:next", "Entity", "next")
        assert _ids(path) == {"ent:good", "ent:next"}


def test_st_09_a_corrupt_file_fails_explicitly_and_is_never_replaced():
    sr = need_rdflib()
    from store import StoreCorrupt, open_store
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "store.ttl"
        bad = b"@prefix kg: <urn:kg:> .\nthis is not turtle <<< \x00\n"
        path.write_bytes(bad)
        for access in ("read", "write"):
            try:
                open_store("rdflib", access=access, path=str(path))
            except StoreCorrupt as e:
                assert str(path) in str(e) and "move it aside" in str(e), e
            else:
                raise AssertionError(f"{access}: a corrupt file opened")
        assert path.read_bytes() == bad and _lock_free(path)
        # an absent file is the one store that opens empty: nothing has been published yet
        fresh = Path(td) / "none.ttl"
        r = sr.RdflibStore(path=str(fresh), access="read")
        assert r.absent and not r._nodes and not fresh.exists()
        r.close()


def test_every_caller_names_its_access():
    """No caller opens the store without saying whether it reads or writes, so none relies on close() to save."""
    import ast
    missing = []
    for base in ("harness", "demo", "tools", "instance"):
        for path in (ROOT / base).rglob("*.py"):
            if "vendor" in path.parts:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "open_store":
                    if not any(k.arg == "access" for k in node.keywords):
                        missing.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):   # the workflows' inline scripts
        for n, line in enumerate(wf.read_text(encoding="utf-8").splitlines(), 1):
            for call in re.findall(r"open_store\(([^()]*)\)", line):
                if "access=" not in call:
                    missing.append(f"{wf.relative_to(ROOT)}:{n}")
    assert not missing, missing
