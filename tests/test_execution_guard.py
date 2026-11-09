"""Task-0141.07: the stopgap before X1. With an organisation's instance mounted (KG_SUBJECT, KG_SUBJECTS or
KG_REGISTER outside this checkout), every path that executes model output refuses before it runs, naming
X1 and the opt-in; KG_ALLOW_UNCONTAINED_EXECUTION=1 lifts it; the public demo runs as before. The paths are
the call-site audit's: measures.run_suite, run_suite_dir and feedback_runner (all through the oracle
loader), run.py before its first model call, and the page before it starts an arms run."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import execution_guard as eg  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

PUBLIC = {"KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"), "KG_SUBJECTS": str(ROOT / "subjects"),
          "KG_REGISTER": str(ROOT / "demo" / "register")}
MOUNTED = dict(PUBLIC, KG_SUBJECTS="/instance/subjects", KG_REGISTER="/instance/register")   # the instance overlay's


@contextmanager
def _env(**kw):
    keep = {k: os.environ.get(k) for k in (*eg.WATCHED, eg.OPT_IN, *kw)}
    for k in (*eg.WATCHED, eg.OPT_IN):
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    try:
        yield
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _refused(fn) -> str:
    try:
        fn()
    except eg.ExecutionRefused as e:
        return str(e)
    raise AssertionError(f"{getattr(fn, '__name__', fn)} ran with an instance mounted")


def test_the_rule_reads_the_watched_variables_against_this_checkout():
    assert eg.refusal(PUBLIC) is None and eg.refusal({}) is None
    assert eg.refusal({"KG_SUBJECT": "subjects/jef_data_load"}) is None or Path.cwd() != ROOT
    why = eg.refusal(MOUNTED)
    assert why and "task-0141.05 (X1)" in why and f"{eg.OPT_IN}=1" in why and "/instance/subjects" in why, why
    assert eg.refusal(dict(MOUNTED, **{eg.OPT_IN: "1"})) is None
    import switches   # only 1 opts in; any other spelling is refused by name, never read as on (task-0276)
    try:
        eg.refusal(dict(MOUNTED, **{eg.OPT_IN: "yes"}))
    except switches.BadSwitch as e:
        assert eg.OPT_IN in str(e)
    else:
        raise AssertionError("only 1 opts in")
    assert eg.refusal(dict(MOUNTED, **{eg.OPT_IN: "0"})), "0 is off"
    for name in eg.WATCHED:   # any one of them outside the checkout, a sibling whose name starts like it included
        assert eg.refusal(dict(PUBLIC, **{name: str(ROOT) + "-instance/x"})), name


def test_every_execution_path_refuses_before_running_model_output():
    import measures
    from subject import SUBJECT
    sc = SUBJECT.order[0]
    with tempfile.TemporaryDirectory() as td, _env(**MOUNTED):
        sentinel = Path(td) / "ran"
        code = f"open({str(sentinel)!r}, 'w').write('model output ran')\n"
        box = Path(td) / "sandbox"
        box.mkdir()
        (box / "main.py").write_text(code)
        for fn in (lambda: measures.run_suite(code, sc), lambda: measures.run_suite_dir(box, sc),
                   lambda: measures.feedback_runner({}, "features"), measures._smoke):
            why = _refused(fn)
            assert "X1" in why and eg.OPT_IN in why, why
        assert not sentinel.exists()


def test_run_py_refuses_an_arms_run_before_the_store_or_a_model_call_and_exits_2():
    need_rdflib()   # run.py imports the pins (pyshacl, rdflib) before it reads its arguments
    import shutil
    with tempfile.TemporaryDirectory() as td:
        env = {k: v for k, v in os.environ.items() if k not in (*eg.WATCHED, eg.OPT_IN) and "KEY" not in k}
        # a mounted instance's register is a readable one outside this checkout (task-0288: run.py refuses a named
        # register it cannot read before main, so the overlay's /instance/register, absent here, would refuse first)
        mounted_register = Path(td) / "instance" / "register"
        shutil.copytree(ROOT / "demo" / "register", mounted_register, ignore=shutil.ignore_patterns("__pycache__"))
        env.update(MOUNTED, KG_REGISTER=str(mounted_register), KG_STORE="rdflib", KG_RDFLIB_FILE=str(Path(td) / "store.ttl"),
                   KG_CLOCK="pinned")
        p = subprocess.run([sys.executable, "run.py", "--scenarios", "S1", "--n", "1", "--out", str(Path(td) / "out")],
                           cwd=ROOT / "harness", env=env, capture_output=True, text=True, timeout=120)
        assert p.returncode == 2 and "task-0141.05 (X1)" in p.stderr and eg.OPT_IN in p.stderr, (p.returncode, p.stderr[-400:])
        assert not (Path(td) / "out").exists() and not (Path(td) / "store.ttl").exists(), "it ran before refusing"


def test_the_page_refuses_an_arms_run_with_an_instance_mounted_and_not_without():
    sys.path.insert(0, str(ROOT / "demo" / "app"))
    import server
    from subject import SUBJECT
    sc = SUBJECT.order[0]

    def popen(*a, **k):
        raise AssertionError("a run started")
    keep, keep_runs = server.subprocess.Popen, server.RUNS_DIR
    with tempfile.TemporaryDirectory() as td:
        server.subprocess.Popen, server.RUNS_DIR = popen, Path(td)
        try:
            with _env(**MOUNTED):
                try:
                    server.Runner().start(sc, "arms", 1)
                except ValueError as e:
                    assert "X1" in str(e) and eg.OPT_IN in str(e), e
                else:
                    raise AssertionError("an arms run started with an instance mounted")
            with _env(**PUBLIC):   # the public demo: whatever stops it here (no key), it is not this refusal
                try:
                    server.Runner().start(sc, "arms", 1)
                except (ValueError, AssertionError) as e:
                    assert "X1" not in str(e), e
        finally:
            server.subprocess.Popen, server.RUNS_DIR = keep, keep_runs
        assert not any(Path(td).iterdir()), "a run folder was made"


def test_the_public_demo_still_loads_the_oracle_and_the_opt_in_lifts_the_refusal():
    import measures
    with _env(**PUBLIC):
        smoke = measures._smoke()
        assert hasattr(smoke, "run_child")
    with _env(**MOUNTED, **{eg.OPT_IN: "1"}):   # the opt-in lifts the refusal
        assert hasattr(measures._smoke(), "run_child")
