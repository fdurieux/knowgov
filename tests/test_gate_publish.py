"""Decision-0017, task-0184: gate_cli.py computes on a scratch store by default and writes the store
KG_STORE names only with --publish. Held here on the rdflib file store: a default run over a published
store holding another scenario leaves the file byte for byte; --publish replaces it, as the command did
before; the two reports are equal but for ``published``; --publish with --no-load is refused; without
rdflib the default says what to install; the CI script maps KG_PUBLISH and the action its input. The
same on Neo4j runs in demo.yml's stack job, where a Neo4j is reachable (the held scenario and the
generation read before and after)."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402

DAY = "2026-11-04"


def _gate(env: dict, *args: str) -> tuple[int, dict | None, str]:
    p = subprocess.run([sys.executable, str(ROOT / "harness" / "gate_cli.py"), "--as-of", "record", *args, "-f", "json"],
                       env=env, cwd=ROOT, capture_output=True, text=True, timeout=600)
    try:
        rep = json.loads(p.stdout)
    except ValueError:
        rep = None
    return p.returncode, rep, p.stderr


def _env(**kw) -> dict:
    env = dict(os.environ, KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"), KG_TODAY=DAY, KG_CLOCK="pinned",
               PYTHONDONTWRITEBYTECODE="1", **kw)
    env.pop("KG_REGISTER", None)
    return env


def test_publish_with_no_load_is_refused_before_any_store_is_opened():
    import gate_cli
    from subject import SUBJECT   # the process's subject (tests.yml runs the suite again on J-F)
    err = io.StringIO()
    with redirect_stderr(err):
        assert gate_cli.main(["--scenario", SUBJECT.order[0], "--publish", "--no-load"]) == 2
    assert "--publish publishes a load; --no-load reads the store as it is" in err.getvalue(), err.getvalue()


def test_a_default_run_leaves_a_published_store_as_it_was_and_publish_replaces_it():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        shared = Path(td) / "shared.ttl"
        env = _env(KG_STORE="rdflib", KG_RDFLIB_FILE=str(shared))
        code, rep, err = _gate(env, "--scenario", "S1", "--publish")        # what a run, or a pipeline's gate, leaves
        assert code == 0 and rep["published"] and rep["store"] == "rdflib" and shared.exists(), (code, err)
        before = shared.read_bytes()

        code, private, err = _gate(env, "--scenario", "S2")                  # the documented hand run
        assert code == 1 and private["verdict"] == "BLOCKED" and private["published"] is False, (code, err)
        assert shared.read_bytes() == before, "a default run changed the shared store"
        code, held, err = _gate(env, "--scenario", "S1", "--no-load")        # the shared store still holds S1
        assert code == 0 and held["verdict"] == "PROCEED" and "published" not in held, (code, err)   # a read: the MCP server's report
        code, _, err = _gate(env, "--scenario", "S2", "--no-load")
        assert code == 2 and "the store holds S1" in err, (code, err)

        code, public, err = _gate(env, "--scenario", "S2", "--publish")       # the old behaviour, asked for
        assert code == 1 and public["published"] is True and shared.read_bytes() != before, (code, err)
        code, _, err = _gate(env, "--scenario", "S2", "--no-load")
        assert code == 1, (code, err)
        differ = sorted(k for k in set(private) | set(public) if private.get(k) != public.get(k))
        assert differ == ["published"], differ                                 # the same answer either way


def test_stage_two_acts_on_the_store_the_load_went_to():
    """--stage 2 by default leaves the shared store holding stage 1; with --publish it holds the change."""
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        shared = Path(td) / "shared.ttl"
        env = _env(KG_STORE="rdflib", KG_RDFLIB_FILE=str(shared))
        assert _gate(env, "--scenario", "S6", "--publish")[0] == 0
        before = shared.read_bytes()
        code, private, err = _gate(env, "--scenario", "S6", "--stage", "2")
        assert code == 1 and private["version"] == "v2" and private["change"]["invalidated"], (code, err)
        assert shared.read_bytes() == before
        code, public, err = _gate(env, "--scenario", "S6", "--stage", "2", "--publish")
        assert code == 1 and public["change"] == private["change"] and shared.read_bytes() != before, (code, err)


def test_with_neo4j_configured_and_unreachable_the_default_still_answers():
    need_rdflib()
    env = _env(KG_STORE="neo4j", KG_NEO4J_URI="bolt://127.0.0.1:9")   # the discard port: nothing answers there
    code, rep, err = _gate(env, "--scenario", "S2")
    assert code == 1 and rep["store"] == "rdflib" and not rep["published"], (code, err)
    code, _, err = _gate(env, "--scenario", "S2", "--publish")
    assert code == 2 and "store" in err, (code, err)                     # --publish needs the configured store


def test_without_rdflib_the_default_names_the_install():
    import gate_cli
    from subject import SUBJECT
    saved = sys.modules.get("store_rdflib")
    sys.modules["store_rdflib"] = None
    err = io.StringIO()
    try:
        with redirect_stderr(err):
            assert gate_cli.main(["--scenario", SUBJECT.order[0], "--as-of", "record"]) == 2
    finally:
        if saved is None:
            sys.modules.pop("store_rdflib", None)
        else:
            sys.modules["store_rdflib"] = saved
    assert "pip install -r demo/requirements.txt" in err.getvalue(), err.getvalue()


def test_the_pipeline_wrappers_pass_publish_on():
    sh = (ROOT / "instance" / "ci" / "knowgov-gate.sh").read_text(encoding="utf-8")
    assert '[ "${KG_PUBLISH:-}" = 1 ] && set -- "$@" --publish' in sh
    action = (ROOT / "instance" / "ci" / "github" / "action.yml").read_text(encoding="utf-8")
    assert "  publish:\n" in action and "KG_PUBLISH: ${{ inputs.publish == 'true' && '1' || '' }}" in action
    assert "KG_PUBLISH:" in (ROOT / "instance" / "ci" / "gitlab" / "knowgov.gitlab-ci.yml").read_text(encoding="utf-8")
    hook = (ROOT / "instance" / "ci" / "claude" / "knowgov_hook.py").read_text(encoding="utf-8")
    assert "--publish" not in hook and "KG_PUBLISH" not in hook   # the hook reads the report only: the default


def test_the_adopter_docs_say_which_store_the_command_writes():
    demo = " ".join((ROOT / "demo" / "README.md").read_text(encoding="utf-8").split())
    assert "**Which store it writes.** None, by default." in demo and "`--publish` loads into the stack's store" in demo
    guide = " ".join((ROOT / "docs" / "guide.md").read_text(encoding="utf-8").split())
    assert "loads the scenario into a private copy in its own memory" in guide and "`--publish` loads into the shared store" in guide
    inst = " ".join((ROOT / "instance" / "README.md").read_text(encoding="utf-8").split())
    assert "set `KG_PUBLISH=1` on the gate step" in inst
