"""Task-0183: a command that computes an answer for one person (capture.py questionnaire and review,
transcript.py) loads its scenario into a scratch store of its own, never the store KG_STORE names, which
the page, the runs and the MCP servers read. Held three ways: no such command calls open_store; run
against a published rdflib file holding another scenario, the file is byte for byte as it was; run
with KG_STORE=neo4j and no Neo4j to reach, it still answers, so it never opened that store."""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402

PERSONAL = ("harness/capture.py", "harness/transcript.py")
DAY = "2026-11-02"


def test_the_personal_commands_never_open_the_configured_store():
    """capture.py and transcript.py name scratch_store, never open_store: a new private load cannot slip back."""
    for rel in PERSONAL:
        tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
        calls = {getattr(n.func, "id", getattr(n.func, "attr", None)) for n in ast.walk(tree) if isinstance(n, ast.Call)}
        assert "open_store" not in calls, f"{rel} opens the configured store"
        assert "scratch_store" in calls, f"{rel} loads nowhere"


def test_a_scratch_store_is_in_memory_and_publishes_nowhere():
    need_rdflib()
    import store
    old = os.environ.get("KG_RDFLIB_FILE")
    with tempfile.TemporaryDirectory() as td:
        os.environ["KG_RDFLIB_FILE"] = str(Path(td) / "shared.ttl")   # the configured file is never the scratch store's
        try:
            with store.scratch_store(instance="x") as st:
                assert st.name == "rdflib" and not st.path and st.access == "write"
                st.wipe()
            assert not list(Path(td).iterdir()), "a scratch store wrote a file"
        finally:
            os.environ.pop("KG_RDFLIB_FILE") if old is None else os.environ.__setitem__("KG_RDFLIB_FILE", old)


def test_without_rdflib_the_scratch_store_says_what_to_install():
    import store
    saved = sys.modules.get("store_rdflib")
    sys.modules["store_rdflib"] = None          # makes the import fail as on a host without the pins
    try:
        try:
            store.scratch_store()
        except store.ScratchUnavailable as e:
            assert "rdflib" in str(e) and "pip install -r demo/requirements.txt" in str(e), e
        else:
            raise AssertionError("no ScratchUnavailable")
    finally:
        if saved is None:
            sys.modules.pop("store_rdflib", None)
        else:
            sys.modules["store_rdflib"] = saved


def _env(**kw) -> dict:
    env = dict(os.environ, KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"), KG_TODAY=DAY, KG_CLOCK="pinned",
               PYTHONDONTWRITEBYTECODE="1", **kw)
    env.pop("KG_REGISTER", None)
    return env


def _capture(env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "harness" / "capture.py"), *args], env=env, cwd=ROOT,
                          capture_output=True, text=True, timeout=600)


def test_questionnaire_and_review_leave_a_published_store_as_it_was():
    """The shared file holds S1; the questionnaire for S4 and a review of S4 run; the file is unchanged."""
    need_rdflib()
    import gate_cli
    import store
    with tempfile.TemporaryDirectory() as td:
        shared = Path(td) / "shared.ttl"
        with store.open_store("rdflib", path=str(shared), access="write") as st:   # what a run on the page leaves
            gate_cli._load(st, "S1")
        before, files = shared.read_bytes(), sorted(p.name for p in Path(td).iterdir())   # the file and its lock
        env = _env(KG_STORE="rdflib", KG_RDFLIB_FILE=str(shared))
        q = _capture(env, "questionnaire", "--scenario", "S4", "--out", str(Path(td) / "q"))
        assert q.returncode == 0, q.stderr
        assert (Path(td) / "q" / "questionnaire-cargo_quote-S4-ORG-0002.toml").exists(), q.stdout
        review = Path(td) / "review.toml"
        review.write_text('[review]\nby = "nobody-issued"\non = 2026-11-02\nrecord = "minutes/x.md"\nscenario = "S4"\n'
                          '[[ruling]]\nassertion = "A:none"\noutcome = "approved"\n', encoding="utf-8")
        r = _capture(env, "review", str(review))
        assert r.returncode == 1 and "refused" in r.stderr, (r.returncode, r.stderr)   # checked after its load, written nowhere
        assert shared.read_bytes() == before, "the shared store changed"
        assert sorted(p.name for p in Path(td).iterdir()) == sorted([*files, "q", "review.toml"]), list(Path(td).iterdir())


def test_with_neo4j_configured_and_unreachable_the_questionnaire_still_answers():
    """KG_STORE=neo4j at an address nothing serves: the questionnaire never opens it, so it answers."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        env = _env(KG_STORE="neo4j", KG_NEO4J_URI="bolt://127.0.0.1:9")   # the discard port: nothing answers there
        q = _capture(env, "questionnaire", "--scenario", "S4", "--out", td)
        assert q.returncode == 0, q.stderr
        assert "Questionnaire for ORG-0002" in q.stdout, q.stdout
