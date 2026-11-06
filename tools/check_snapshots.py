"""Store generations, proven on a real store (task-0141.06, decision-0014): SNAP-01..SNAP-08.

    python tools/check_snapshots.py --disposable                 # KG_STORE=neo4j: the database it names
    KG_STORE=rdflib python tools/check_snapshots.py --disposable  # a file-backed store in a temporary folder

It wipes and reloads the store many times, so it runs only against a disposable store and refuses
without ``--disposable``. Two published generations are the subject's first two scenarios loaded as
``gate_cli`` loads them; a logical read is what the page, the MCP server and ``gate_cli --no-load``
read together: the held scenario, the census, the register's census and the gate's verdict.

  SNAP-01  a writer paused after staging half a load: the page's read, the MCP server's call and
           ``gate_cli --no-load`` (a separate process) all answer the previous generation, every time
  SNAP-02  a publication between two queries of one read handle: the handle refuses (StoreChanged)
           or, on rdflib, answers wholly from the snapshot it loaded; ``store.read`` answers wholly
           from the new generation
  SNAP-03  a writer process killed before publication, and a publication that fails after it began:
           the previous evidence and gate verdict are read after the restart
  SNAP-04  a load, the register projection and a gate_cli load race from a barrier: they serialise,
           every read in the meantime is a complete generation, the end state is the last writer's,
           and a writer that cannot wait is refused (StoreBusy), never merged
  SNAP-05  a writer whose ownership was recovered by another (its lease ran out; its lock file was
           replaced) resumes and cannot publish (StoreFenced)
  SNAP-06  after a success and after a failure the published generation is right, a reader open
           across a publication stays valid (rdflib: its snapshot) or is refused (Neo4j), and a run
           left running by a restart is reconciled
  SNAP-07  the round trip through the other adapter, S6 with its later version and re-verification,
           holds every answer, and the publication metadata never reaches the exported Turtle
  SNAP-08  a writer killed between raising the counter and committing (rdflib: in its atomic replace),
           task-0175: while its lease is live a read waits, then refuses; once the lease has run out a
           read answers the last committed generation with no new writer, the reader having cleared
           the begin under the sequence lock and recorded the abandoning writer; the clearing and a
           writer taking the lease, in either order or racing, never both act and never lose the writer

Exit 0 when every check holds, 1 otherwise. No model is called; the clock is pinned.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import _outcomes  # noqa: E402 — task-0159: each check's outcome, when KG_OUTCOMES names a file
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
os.environ.setdefault("KG_CLOCK", "pinned")

FAILURES: list[str] = []


def check(cond, label: str) -> bool:
    _outcomes.check(label, cond)
    print(("ok   " if cond else "FAIL ") + label, flush=True)
    if not cond:
        FAILURES.append(label)
    return bool(cond)


def kind() -> str:
    return (os.environ.get("KG_STORE") or "neo4j").lower()


def opener(access: str, **kw):
    from store import open_store
    from subject import SUBJECT
    return open_store(instance=SUBJECT.id, access=access, **kw)


def snapshot(st) -> dict:
    """One logical read, as the page's store card and the gate read it."""
    import cadence
    from gate import resolve
    acts = st.extraction_activities()
    held = acts[0].split(":")[2] if acts else None
    c = st.census()
    reg = st.register_census()
    verdict = resolve(st, "codegen", cadence.as_of("record").isoformat())["verdict"] if held else None
    return {"held": held, "nodes": c["nodes"], "relationships": c["relationships"],
            "statuses": dict(sorted(c["assertions_by_status"].items())), "register": (reg or {}).get("total"), "verdict": verdict}


def read_now() -> dict:
    import store
    return store.read(snapshot, instance=_sid())


def _sid() -> str:
    from subject import SUBJECT
    return SUBJECT.id


def load(st, scenario: str, half: bool = False) -> None:
    """gate_cli's load; ``half`` stops after the extraction, before the verifications and the rules."""
    import gate_cli
    if not half:
        gate_cli._load(st, scenario)
        return
    from kitio import kit_for
    from load import load_scenario
    st.wipe()
    st.apply_constraints()
    load_scenario(st, scenario, kit_for(scenario), activity_note=f"{scenario}: half a load (SNAP-01)")


def publish(scenario: str, project: bool = False) -> dict:
    with opener("write") as st:
        load(st, scenario)
        if project:
            import register_project
            st.project_register(register_project.rows())
    return read_now()


def cli_verdict(scenario: str) -> str | None:
    """gate_cli --no-load in its own process: the CLI's read of what is published."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("OPENAI", "GEMINI", "AWS", "KG_ANTHROPIC", "KG_MODEL_API"))}
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--no-load", "--scenario", scenario,
                        "--as-of", "record", "-f", "json"], capture_output=True, text=True, env=env, timeout=300)
    try:
        return json.loads(p.stdout)["verdict"]
    except (ValueError, KeyError):
        return f"exit {p.returncode}: {(p.stderr or p.stdout)[-300:]}"


def mcp_verdict() -> str | None:
    import mcp_server
    t = mcp_server.Tools(as_of="record")
    out = t.call("gate_verdict", {"task": "codegen"}) if hasattr(t, "call") else t.gate_verdict({"task": "codegen"})
    return out.get("verdict") if isinstance(out, dict) else None


# ---------------------------------------------------------------------------------------------------

def snap_01(s1: str, s2: str, g1: dict, g2: dict) -> None:
    staged, release, done = threading.Event(), threading.Event(), threading.Event()
    err: list[BaseException] = []

    def writer():
        try:
            with opener("write") as st:
                load(st, s2, half=True)
                staged.set()
                release.wait(120)
        except BaseException as e:  # noqa: BLE001
            err.append(e)
        finally:
            staged.set()
            done.set()
    threading.Thread(target=writer, daemon=True).start()
    staged.wait(300)
    page = [read_now() for _ in range(3)]
    check(all(r == g1 for r in page), f"SNAP-01 the page's read, three times, answers the previous generation while a load is half staged: {page[-1]}")
    check(cli_verdict(s1) == g1["verdict"], "SNAP-01 gate_cli --no-load, a separate process, answers the previous generation's verdict")
    try:
        mv = mcp_verdict()
        check(mv == g1["verdict"], f"SNAP-01 the MCP server's gate_verdict answers the previous generation's verdict: {mv}")
    except Exception as e:  # noqa: BLE001
        check(False, f"SNAP-01 the MCP server's gate_verdict: {type(e).__name__}: {e}")
    release.set()
    done.wait(120)
    check(not err and read_now()["held"] == s2, f"SNAP-01 the paused writer then publishes whole: {err or read_now()['held']}")
    # leave g1 published for the next check
    check(publish(s1) == g1, "SNAP-01 the previous generation, republished, reads as before")


def snap_02(s1: str, s2: str, g1: dict, g2: dict) -> None:
    import store
    with opener("read") as st:
        first = st.census()
        publish(s2)
        try:
            later = snapshot(st)
            check(kind() == "rdflib" and later == g1 and first["nodes"] == g1["nodes"],
                  f"SNAP-02 a read handle open across a publication answers wholly from its own generation: {later}")
        except store.StoreChanged:
            check(kind() == "neo4j", "SNAP-02 a read handle open across a publication refuses its next read (StoreChanged), never mixing generations")
    publish(s1)
    calls = {"n": 0}

    def logical(st):
        a = st.census()
        if calls["n"] == 0:
            calls["n"] += 1
            publish(s2)   # between the two queries of the first attempt
        return {"census_nodes": a["nodes"], **snapshot(st)}
    got = store.read(logical, instance=_sid())
    whole = got["census_nodes"] == got["nodes"] and {k: got[k] for k in g2} in (g1, g2)
    check(whole, f"SNAP-02 store.read's answer belongs wholly to one generation: {got}")
    if kind() == "neo4j":
        check({k: got[k] for k in g2} == g2, "SNAP-02 on Neo4j the retried read answers the new generation")
    publish(s1)


def snap_03(s1: str, s2: str, g1: dict) -> None:
    code = (f"import os, sys; sys.path[:0] = [{str(ROOT / 'harness')!r}, {str(ROOT / 'tools')!r}]\n"
            "import check_snapshots as c\n"
            "st = c.opener('write')\n"
            f"c.load(st, {s2!r})\n"
            "os._exit(9)   # killed before publication\n")
    p = subprocess.run([sys.executable, "-c", code], env={**os.environ, "KG_NEO4J_LEASE_SECONDS": "3"}, capture_output=True, text=True, timeout=600)
    check(p.returncode == 9, f"SNAP-03 a writer process died before publication (exit {p.returncode}) {p.stderr[-200:]}")
    check(read_now() == g1, "SNAP-03 after it, the previous evidence and gate verdict are read")
    # a publication that fails after it began (Neo4j: between raising begin and the unit's commit;
    # rdflib: the atomic replace)
    import store_neo4j
    import store_rdflib
    boom = RuntimeError("SNAP-03 injected failure during publication")

    def fail(*_a, **_k):
        raise boom
    saved = (store_neo4j._on_publish, store_rdflib._replace)
    store_neo4j._on_publish = fail
    store_rdflib._replace = fail
    try:
        with opener("write") as st:
            load(st, s2)
        check(False, "SNAP-03 an injected failure during publication propagates")
    except RuntimeError as e:
        check(e is boom, "SNAP-03 an injected failure during publication propagates")
    finally:
        store_neo4j._on_publish, store_rdflib._replace = saved
    check(read_now() == g1, "SNAP-03 after a failed publication the previous evidence and gate verdict are read, with no wait")
    if kind() == "neo4j":
        # killed between raising begin and committing: readers refuse (never mix) until the next writer recovers
        code2 = code.replace("c.load(st, " + repr(s2) + ")\n",
                             "import store_neo4j\n"
                             f"c.load(st, {s2!r})\n"
                             "store_neo4j._on_publish = lambda w: os._exit(9)\n"
                             "st.commit()\n")
        p = subprocess.run([sys.executable, "-c", code2], env={**os.environ, "KG_NEO4J_LEASE_SECONDS": "3"}, capture_output=True, text=True, timeout=600)
        check(p.returncode == 9, f"SNAP-03 a writer killed mid-publication (exit {p.returncode}) {p.stderr[-200:]}")
        import store
        try:   # at once, while the dead writer's lease is live (once it runs out a reader clears it: SNAP-08)
            with _env(KG_NEO4J_READ_WAIT="0"):
                store.read(snapshot, instance=_sid(), attempts=1)
            check(False, "SNAP-03 a read while a publication is interrupted is refused (StoreBusy), never a mixed graph")
        except store.StoreBusy:
            check(True, "SNAP-03 a read while a publication is interrupted is refused (StoreBusy), never a mixed graph")
        time.sleep(3.5)   # the dead writer's lease runs out
        with opener("write"):   # the next writer recovers at acquisition, publishing nothing
            pass
        check(read_now() == g1, "SNAP-03 once the next writer has recovered, the previous generation is read")


class _env:
    """Environment variables set for the block, then restored."""
    def __init__(self, **kw):
        self.kw = kw

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kw}
        os.environ.update(self.kw)

    def __exit__(self, *exc):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


LEASE_08 = 4.0   # the killed writer's lease in SNAP-08, seconds


def _abandon(s2: str) -> int:
    """A writer process that loads ``s2`` and dies between raising the counter and committing (rdflib:
    inside its atomic replace); returns its exit code, 9 when it died there."""
    code = (f"import os, sys; sys.path[:0] = [{str(ROOT / 'harness')!r}, {str(ROOT / 'tools')!r}]\n"
            "import check_snapshots as c, store_neo4j, store_rdflib\n"
            "store_neo4j._on_publish = lambda w: os._exit(9)\n"
            "store_rdflib._replace = lambda *a, **k: os._exit(9)\n"
            "st = c.opener('write')\n"
            f"c.load(st, {s2!r})\n"
            "st.commit()\n"
            "os._exit(3)   # it published: not the case this sets up\n")
    p = subprocess.run([sys.executable, "-c", code], env={**os.environ, "KG_NEO4J_LEASE_SECONDS": f"{LEASE_08:g}"},
                       capture_output=True, text=True, timeout=600)
    if p.returncode != 9:
        print(p.stderr[-400:], file=sys.stderr)
    return p.returncode


def _unit(handle):
    """A Neo4j handle's publication unit, through the read view."""
    return getattr(handle, "_inner", handle)._pub


def _pub() -> dict:
    """The publication node as it stands (Neo4j), read with the driver alone: a read handle would pin,
    and pinning is what is under test."""
    import store_neo4j
    return store_neo4j.publication()


def snap_08(s1: str, s2: str, g1: dict) -> None:
    import store
    publish(s1)
    t0 = time.monotonic()
    check(_abandon(s2) == 9, "SNAP-08 a writer died between raising the counter and committing")
    if kind() == "rdflib":   # the lock dies with the process and the replace never ran: nothing to clear
        check(read_now() == g1, "SNAP-08 on rdflib, a read with no new writer answers the last committed generation")
        return
    before = _pub()
    check(before.get("begin") != before.get("end") and before.get("owner"),
          f"SNAP-08 the counter is left raised under the dead writer's lease: begin {before.get('begin')}, end {before.get('end')}")
    # AC 2: while the lease is live, a read waits KG_NEO4J_READ_WAIT and then refuses, as before
    wait = 1.0
    w0 = time.monotonic()
    try:
        with _env(KG_NEO4J_READ_WAIT=f"{wait:g}"):
            store.read(snapshot, instance=_sid(), attempts=1)
        check(False, "SNAP-08 while the lease is live a read waits, then refuses (StoreBusy)")
    except store.StoreBusy as e:
        took = time.monotonic() - w0
        live = time.monotonic() - t0 < LEASE_08
        check(live and took >= wait * 0.9 and "live lease" in str(e),
              f"SNAP-08 while the lease is live a read waits {took:.1f} s, then refuses (StoreBusy): {str(e)[:120]}")
    check(_pub().get("begin") != _pub().get("end"), "SNAP-08 the refused read cleared nothing while the lease was live")
    # AC 1: once the lease has run out, a read answers the last committed generation, no writer opened
    time.sleep(max(0.0, LEASE_08 + 0.5 - (time.monotonic() - t0)))
    with opener("read") as rd:
        cleared = _unit(rd).recovered
    after = _pub()
    check(read_now() == g1, "SNAP-08 once the lease has run out, a read with no new writer answers the last committed generation")
    check(cleared is not None and cleared.get("epoch") == before.get("epoch") and cleared.get("owner") == before.get("owner"),
          f"SNAP-08 the reader cleared the abandoned begin and names the abandoning writer: {cleared}")
    check(after.get("begin") == after.get("end") == before.get("end") and after.get("owner") is None
          and after.get("epoch") == before.get("epoch") + 1 and after.get("abandoned_epoch") == before.get("epoch"),
          f"SNAP-08 the generation is the last committed one, the lease free and the epoch moved past the abandoning writer: {after}")
    check(publish(s1) == g1, "SNAP-08 the next writer then takes the free lease and publishes")
    _snap_08_orders(s1, s2, g1)


def _snap_08_orders(s1: str, s2: str, g1: dict) -> None:
    """AC 3: the reader's clearing and a writer taking the lease, in both orders and racing."""
    # a writer first: its acquisition closes the gap; a reader's clearing then finds nothing and the writer keeps its lease
    t0 = time.monotonic()
    check(_abandon(s2) == 9, "SNAP-08 (writer first) another writer died mid-publication")
    time.sleep(max(0.0, LEASE_08 + 0.5 - (time.monotonic() - t0)))
    with opener("write") as w:
        token = w._pub.token
        with opener("read") as rd:
            found = _unit(rd).recover()
            snap = snapshot(rd)
        p = _pub()
        check(found is None and p.get("owner") == token and p.get("begin") == p.get("end"),
              f"SNAP-08 (writer first) a reader's clearing finds nothing and leaves the writer's lease: {found} {p.get('owner') == token}")
        check(snap == g1, "SNAP-08 (writer first) the reader answers the last committed generation beside the writer")
        load(w, s1)
    check(read_now() == g1, "SNAP-08 (writer first) the writer publishes after the reader")
    # racing: readers pinning while a writer acquires, after an abandoned publication
    t0 = time.monotonic()
    check(_abandon(s2) == 9, "SNAP-08 (race) another writer died mid-publication")
    time.sleep(max(0.0, LEASE_08 + 0.5 - (time.monotonic() - t0)))
    barrier = threading.Barrier(5)
    reads, cleared, errs, wrote = [], [], [], []

    def reader():
        barrier.wait()
        try:
            with opener("read") as rd:
                if _unit(rd).recovered is not None:
                    cleared.append(_unit(rd).recovered)
                reads.append(snapshot(rd))
        except Exception as e:  # noqa: BLE001
            errs.append(f"{type(e).__name__}: {e}")

    def writer():
        barrier.wait()
        try:
            with opener("write") as w:
                load(w, s1)
            wrote.append(True)
        except Exception as e:  # noqa: BLE001
            errs.append(f"writer {type(e).__name__}: {e}")
    ts = [threading.Thread(target=reader) for _ in range(4)] + [threading.Thread(target=writer)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(600)
    real = [e for e in errs if "StoreChanged" not in e]   # a reader the writer's publication overtook is refused, never mixed
    check(wrote and not real, f"SNAP-08 (race) the writer published and every reader answered or was refused cleanly: {real[:2]}")
    check(all(r == g1 for r in reads), f"SNAP-08 (race) every reader answered the last committed generation: {len(reads)} reads")
    check(len(cleared) <= 1, f"SNAP-08 (race) at most one party cleared the abandoned begin: {len(cleared)} readers did")
    p = _pub()
    check(p.get("begin") == p.get("end") and p.get("owner") is None and read_now() == g1,
          f"SNAP-08 (race) the end state is one published generation and a free lease: {p.get('begin')}, {p.get('end')}")


def snap_04(s1: str, s2: str, states: set) -> None:
    import store
    import register_project
    go = threading.Barrier(4)
    stop = threading.Event()
    seen: list[str] = []
    order: list[str] = []
    errs: list[str] = []

    def reader():
        go.wait()
        while not stop.is_set():
            try:
                seen.append(json.dumps(read_now(), sort_keys=True))
            except store.StoreBusy:
                pass   # refused, never mixed

    def w_run():   # the page's run: a load of s2
        go.wait()
        try:
            with opener("write", lock_timeout=300) as st:
                load(st, s2)
            order.append("run")
        except Exception as e:  # noqa: BLE001
            errs.append(f"run {type(e).__name__}: {e}")

    def w_proj():  # the page's register projection
        go.wait()
        try:
            register_project.project(opener("write", lock_timeout=300))
            order.append("proj")
        except Exception as e:  # noqa: BLE001
            errs.append(f"proj {type(e).__name__}: {e}")

    def w_cli():   # gate_cli loading s1
        go.wait()
        try:
            with opener("write", lock_timeout=300) as st:
                load(st, s1)
            order.append("cli")
        except Exception as e:  # noqa: BLE001
            errs.append(f"cli {type(e).__name__}: {e}")
    ts = [threading.Thread(target=f, daemon=True) for f in (reader, w_run, w_proj, w_cli)]
    for t in ts:
        t.start()
    for t in ts[1:]:
        t.join(900)
    stop.set()
    ts[0].join(60)
    check(not errs and sorted(order) == ["cli", "proj", "run"], f"SNAP-04 three racing writers each published, one after another: {order} {errs}")
    partial = sorted({s for s in seen if s not in states})
    check(seen and not partial, f"SNAP-04 every one of {len(seen)} reads during the race was a complete generation; partial: {partial[:2]}")
    end = read_now()
    last_load = [w for w in order if w in ("run", "cli")][-1]
    want_held = s2 if last_load == "run" else s1
    want_register = order.index("proj") > order.index(last_load)
    check(end["held"] == want_held and bool(end["register"]) == want_register,
          f"SNAP-04 the end state is the last writers' (order {order}): held {end['held']}, register {end['register']}")
    # a writer that cannot wait is refused, never merged
    hold, held = threading.Event(), threading.Event()

    def holder():
        with opener("write") as st:
            st.census()
            held.set()
            hold.wait(60)
    threading.Thread(target=holder, daemon=True).start()
    held.wait(60)
    try:
        opener("write", lock_timeout=0.5).close()
        check(False, "SNAP-04 a second writer that cannot wait is refused (StoreBusy)")
    except store.StoreBusy:
        check(True, "SNAP-04 a second writer that cannot wait is refused (StoreBusy)")
    hold.set()
    time.sleep(0.5)


def snap_05(s1: str, s2: str, g1: dict, g2: dict) -> None:
    import store
    if kind() == "neo4j":
        a = opener("write", lease_seconds=2)
        a._pub.beat_stop.set()        # paused: its heartbeat stops, its lease runs out
        load(a, s2)
        a_epoch = a._pub.epoch
        check(a_epoch in _writer_epochs(a), "SNAP-05 the former writer's unit transaction is open on the server before the takeover")
        time.sleep(2.5)
        b = opener("write", lock_timeout=30)   # recovers ownership
        check(a_epoch not in _writer_epochs(a),
              "SNAP-05 the takeover terminated the former writer's transaction on the server (TERMINATE TRANSACTIONS ran)")
        with b:
            load(b, s1)
        try:
            a.commit()
            check(False, "SNAP-05 the former writer, resumed, cannot publish (StoreFenced)")
        except store.StoreFenced:
            check(True, "SNAP-05 the former writer, resumed, cannot publish (StoreFenced)")
        finally:
            a.close()
    else:
        path = os.environ["KG_RDFLIB_FILE"]
        a = opener("write")
        load(a, s2)
        os.unlink(path + ".lock")      # an operator recovers the lock: the file is cleared
        with opener("write", lock_timeout=5) as b:
            load(b, s1)
        try:
            a.commit()
            check(False, "SNAP-05 the former writer, resumed, cannot publish (StoreFenced)")
        except store.StoreFenced:
            check(True, "SNAP-05 the former writer, resumed, cannot publish (StoreFenced)")
        finally:
            a.close()
    check(read_now() == g1, "SNAP-05 the store holds the recovering writer's generation, not the former writer's")


def _writer_epochs(handle) -> set:
    """The epochs of the knowgov unit transactions running on the Neo4j server (by their metadata); a
    terminated one stays listed, with its status, until its client next speaks, so it is not counted."""
    with handle._pub.driver.session() as s:   # the adapter's own driver: no module here imports the driver
        return {r["e"] for r in s.run("SHOW TRANSACTIONS YIELD metaData AS m, status "
                                      "WHERE m.kg_writer IS NOT NULL AND NOT status STARTS WITH 'Terminated' RETURN m.kg_epoch AS e")}


def snap_03_memory() -> None:
    """Neo4j started with a small ``db.memory.transaction.max`` (Community cannot change it at run time):
    a writer's unit larger than it fails cleanly and the published generation is read whole after it."""
    import store
    from subject import SUBJECT
    before = read_now()
    other = next(s for s in SUBJECT.order if s != before["held"])
    try:
        with opener("write") as st:
            load(st, other)
        check(False, "SNAP-03 a unit over db.memory.transaction.max fails")
    except store.StoreBusy as e:
        check(False, f"SNAP-03 a unit over db.memory.transaction.max fails on memory, not on the lease: {e}")
    except Exception as e:  # noqa: BLE001 — the driver's class for a memory pool refusal
        check("memory" in str(e).lower(), f"SNAP-03 a unit over db.memory.transaction.max fails: {type(e).__name__}: {str(e)[:160]}")
    after = read_now()
    check(after == before, f"SNAP-03 after it the published generation ({before['held']}) is read whole: {after['held']}, {after['nodes']} nodes")
    with opener("write") as st:
        gen = st._pub.generation()
    check(gen is not None and gen[0] == gen[1], f"SNAP-03 the sequence lock is closed after the refused unit: {gen}")


def snap_06(s1: str, s2: str, g1: dict, g2: dict) -> None:
    import store
    import runs_index
    import datetime as dt
    with opener("read") as old:
        check(publish(s2) == g2, "SNAP-06 after a success the new generation is published")
        try:
            stayed = snapshot(old)   # read first: on Neo4j this is what is refused
            check(kind() == "rdflib" and stayed == g1, "SNAP-06 a reader open across the publication stays valid on its own snapshot")
        except store.StoreChanged:
            check(kind() == "neo4j", "SNAP-06 a reader open across the publication is refused, never answered from a retired generation")
    try:
        with opener("write") as st:
            load(st, s1)
            raise RuntimeError("SNAP-06 a run that fails")
    except RuntimeError:
        pass
    check(read_now() == g2, "SNAP-06 after a failed writer the published generation is unchanged")
    if kind() == "neo4j":
        with opener("write") as st:
            gen = st._pub.generation()
        check(gen is not None and gen[0] == gen[1], f"SNAP-06 the sequence lock is closed after success and failure: {gen}")
    else:
        d = Path(os.environ["KG_RDFLIB_FILE"]).parent
        check(not [p for p in d.iterdir() if p.name.startswith(".kg-publish-")], "SNAP-06 no retired temporary generation is left beside the store")
    with tempfile.TemporaryDirectory() as td:
        run = Path(td) / "cargo_quote" / "2026-11-06-0400"
        run.mkdir(parents=True)
        (run / "run.json").write_text(json.dumps({"id": run.name, "subject": "cargo_quote", "status": "running", "started": "2026-11-06T04:00:00+00:00",
                                                  "heartbeat_at": "2026-11-06T04:00:00+00:00", "finished": None}), encoding="utf-8")

        def write(folder, j):
            (Path(folder) / "run.json").write_text(json.dumps(j), encoding="utf-8")
        closed = runs_index.close_stale(Path(td), dt.datetime(2026, 11, 6, 5, 0, tzinfo=dt.timezone.utc), write)
        rec = json.loads((run / "run.json").read_text(encoding="utf-8"))
        check(closed and rec.get("status") == "failed", f"SNAP-06 a run left running by a restart is reconciled as failed: {rec.get('status')}")
    publish(s1)


def snap_07(round_trip: bool = True) -> None:
    if not round_trip:
        _outcomes.skip("SNAP-07 round trip", "not run here; the workflow's own round-trip steps run it (--no-round-trip)")
        print("skip SNAP-07 round trip: not run here; the workflow's own round-trip steps run it (--no-round-trip)", flush=True)
    chain = "neo4j,rdflib,neo4j" if kind() == "neo4j" else "rdflib,rdflib"   # the workflows run the other chains
    env = dict(os.environ)
    if kind() == "rdflib":
        env.pop("KG_RDFLIB_FILE", None)
    if round_trip:
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "check_round_trip.py"), "--chain", chain, "--scenarios", "S6"],
                           capture_output=True, text=True, env=env, timeout=1800)
        check(p.returncode == 0, f"SNAP-07 {chain} holds S6, its later version and re-verification: {p.stdout.strip().splitlines()[-1:] or p.stderr[-300:]}")
    with opener("read") as st:
        ttl = st.export_turtle()
    check("_KgPublication" not in ttl and "lock_seq" not in ttl, "SNAP-07 the publication metadata never reaches the exported Turtle")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--disposable", action="store_true", help="confirm the store may be wiped (required)")
    ap.add_argument("--memory-limited", action="store_true",
                    help="Neo4j only, on a server started with a small db.memory.transaction.max and a generation "
                         "published: only check that a larger unit fails cleanly and the generation stays")
    ap.add_argument("--no-round-trip", action="store_true",
                    help="leave SNAP-07's round trip to the workflow's own round-trip steps (the export check still runs)")
    args = ap.parse_args()
    if not args.disposable:
        print("check_snapshots: wipes and reloads the store; run it only against a disposable one, with --disposable", file=sys.stderr)
        return 2
    import cadence
    os.environ.update(cadence.pin_record({}))   # the record's day, the wall clock refused (task-0075); children inherit it
    tmp = None
    if kind() == "rdflib":
        tmp = tempfile.TemporaryDirectory()
        os.environ["KG_RDFLIB_FILE"] = str(Path(tmp.name) / "store.ttl")
    if args.memory_limited:
        if kind() != "neo4j":
            print("check_snapshots: --memory-limited is a Neo4j check", file=sys.stderr)
            return 2
        snap_03_memory()
        print("snapshots (neo4j, memory-limited): " + ("every check holds" if not FAILURES else f"{len(FAILURES)} failure(s)"))
        return 1 if FAILURES else 0
    from subject import SUBJECT
    s1, s2 = SUBJECT.order[0], SUBJECT.order[1]
    import register_project
    g1, g2 = publish(s1), publish(s2)
    g2r = publish(s2, project=True)
    g1r = publish(s1, project=True)
    g1 = publish(s1)
    check(g1 != g2 and g1["held"] == s1 and g2["held"] == s2, f"two generations: {s1} {g1['verdict']} {g1['nodes']} nodes, {s2} {g2['verdict']} {g2['nodes']} nodes")
    del register_project
    states = {json.dumps(x, sort_keys=True) for x in (g1, g2, g1r, g2r)}
    snap_01(s1, s2, g1, g2)
    snap_02(s1, s2, g1, g2)
    snap_03(s1, s2, g1)
    snap_04(s1, s2, states)
    publish(s1)
    snap_05(s1, s2, g1, g2)
    snap_06(s1, s2, g1, g2)
    snap_07(round_trip=not args.no_round_trip)
    snap_08(s1, s2, g1)
    print(f"snapshots ({kind()}): " + ("every check holds" if not FAILURES else f"{len(FAILURES)} failure(s)"))
    if tmp:
        tmp.cleanup()
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(_outcomes.run(main))
