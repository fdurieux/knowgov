"""task-0279 (decision-0033 choice 5, G9-17): a register that is named and cannot be read exits 2, naming it.

`check_subject --register DIR` with a DIR that does not exist, or a bad `KG_REGISTER`, gave one "unchecked" note
and exit 0, so a typo dropped the register check without a word. Now a register named by a flag or by
`KG_REGISTER` that `register_impact.unreadable` refuses is a cannot-run, exit 2, naming who named it and the
path. "Unchecked" stays for `check_subject` when no register is named and the default cannot be read.

The other readers that take a register follow the same rule:
- `register_nodes`, `upward` and `proposal_impact` (and its `--register-branch`) exited 1 with a traceback;
- `gate_cli` reported `register: null` and exit 0 on a bad `KG_REGISTER`, and its `--register-previous` is
  now checked before the load;
- the MCP reader started anyway; now it refuses to start.

task-0288 (the bounded re-probe at 9861953) carries the rule to every reader that reads the register through
`cadence.register_root`: `capture` (whose ingest skipped the issued-handle check, writing a capture a good
register refuses), `trace`, `run`, `transcript` and `step_grid` refuse it through `cli_exit.run(register=True)`
or their own check, and the page refuses to start. `check_subject` uses the readers' one test (N10)."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import check_subject  # noqa: E402
import register_impact as ri  # noqa: E402

REGISTER = ROOT / "demo" / "register"
CARGO = ROOT / "subjects" / "cargo_quote"
NOPE = "/nonexistent/kg-register"


def _env(**kw) -> dict:
    e = {**os.environ, "KG_CLOCK": "pinned", "KG_TODAY": "2026-11-09", "KG_SUBJECT": str(CARGO), "KG_STORE": "rdflib",
         "KG_RDFLIB_FILE": str(Path(tempfile.gettempdir()) / "kg-named-register-never.ttl")}
    e.pop("KG_REGISTER", None)
    return {**e, **kw}


def _run(args, **env):
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, env=_env(**env), capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=120)
    return r.returncode, r.stdout, r.stderr


def test_a_register_is_readable_only_with_its_metamodel_and_its_loader():
    assert ri.unreadable(REGISTER) is None and ri.unreadable(REGISTER, tools=False) is None
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        assert ri.unreadable(d / "missing") == "no such directory"
        assert ri.unreadable(d) == "no metamodel/types.toml"
        (d / "metamodel").mkdir()
        (d / "metamodel" / "types.toml").write_text("x = 1\n", encoding="utf-8")
        assert "names no taxonomy" in ri.unreadable(d)
        (d / "metamodel" / "types.toml").write_text("not toml [", encoding="utf-8")
        assert "is not TOML" in ri.unreadable(d)
        (d / "metamodel" / "types.toml").write_text('taxonomy = ["capabilities"]\n', encoding="utf-8")
        assert ri.unreadable(d, tools=False) is None and "tools/register.py" in ri.unreadable(d)
    try:
        ri.require(Path(NOPE), "--register-previous")
    except ri.RegisterUnreadable as e:
        assert str(e).startswith(f"--register-previous {NOPE} is not a readable register"), e
    else:
        raise AssertionError("a missing register passed")


def test_check_subject_exits_2_on_a_named_register_and_keeps_unchecked_for_none():
    for args, env in (([CARGO, "--register", NOPE], {}), ([CARGO], {"KG_REGISTER": NOPE})):
        code, _, err = _run([ROOT / "tools" / "check_subject.py", *args], **env)
        by = "--register" if "--register" in args else "KG_REGISTER"
        assert code == 2 and f"{by} {NOPE} is not a readable register" in err, (code, err[-300:])
    code, out, _ = _run([ROOT / "tools" / "check_subject.py", CARGO, "--register", REGISTER])
    assert code == 0 and "unchecked against the register" not in out, out[-300:]
    keep = check_subject.DEFAULT_REGISTER, os.environ.pop("KG_REGISTER", None)
    check_subject.DEFAULT_REGISTER = Path(NOPE)
    try:   # none named and the default unreadable: the rows unchecked, as before
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = check_subject.main([str(CARGO)])
        assert code == 0 and "unchecked against the register: no readable register" in buf.getvalue(), buf.getvalue()[-400:]
    finally:
        check_subject.DEFAULT_REGISTER = keep[0]
        if keep[1] is not None:
            os.environ["KG_REGISTER"] = keep[1]


def test_every_other_reader_that_takes_a_register_exits_2_naming_it():
    with tempfile.TemporaryDirectory() as td:
        for args in ([ROOT / "harness" / "register_nodes.py", "--limit", "1"],
                     [ROOT / "harness" / "upward.py", "key", "REQ-01|text"],
                     [ROOT / "harness" / "proposal_impact.py", ROOT / "tools" / "fixtures" / "proposal_contract_quote.json"],
                     [ROOT / "harness" / "gate_cli.py", "--scenario", "S1"],
                     [ROOT / "harness" / "mcp_server.py"]):
            code, _, err = _run(args, KG_REGISTER=NOPE)
            assert code == 2 and f"KG_REGISTER {NOPE} is not a readable register: no such directory" in err, (args[0].name, code, err[-300:])
        code, _, err = _run([ROOT / "harness" / "gate_cli.py", "--scenario", "S1", "--register-previous", Path(td) / "previous"])
        assert code == 2 and f"--register-previous {(Path(td) / 'previous').as_posix()} is not a readable register" in err, (code, err[-300:])
        code, _, err = _run([ROOT / "harness" / "proposal_impact.py", "--register-branch", Path(td) / "branch", "--base", "origin/main"])
        assert code == 2 and "--register-branch" in err and "is not a readable register" in err, (code, err[-300:])
    assert not Path(_env()["KG_RDFLIB_FILE"]).exists(), "a refused register opens no store"


def test_the_readers_through_register_root_refuse_it_too():
    """task-0288: each exits 2 naming KG_REGISTER and the path, before it reads or writes anything."""
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "ledger.json"
        led.write_text("{}", encoding="utf-8")
        answered = Path(td) / "answered.toml"
        answered.write_text("[questionnaire]\nsubject = \"cargo_quote\"\n", encoding="utf-8")
        for args in ([ROOT / "harness" / "capture.py", "due", "--out", Path(td) / "due"],
                     [ROOT / "harness" / "capture.py", "ingest", answered, "--into", Path(td) / "captures"],
                     [ROOT / "harness" / "capture.py", "questionnaire", "S1", "--out", Path(td) / "q"],
                     [ROOT / "harness" / "capture.py", "review", Path(td) / "review.toml"],
                     [ROOT / "harness" / "trace.py", "check", "--instance", td, "--ledger", led],
                     [ROOT / "harness" / "trace.py", "register", "--instance", td, "--ledger", led, "--keys", "K|v"],
                     [ROOT / "harness" / "transcript.py", Path(td) / "t.jsonl"],
                     [ROOT / "harness" / "step_grid.py"],
                     [ROOT / "demo" / "app" / "server.py"]):
            code, _, err = _run(args, KG_REGISTER=NOPE, KG_PAGE_PORT="0")
            assert code == 2 and f"KG_REGISTER {NOPE} is not a readable register: no such directory" in err, \
                (args[0].name, args[1:2], code, err[-300:])
        for left in ("due", "captures", "q"):
            assert not (Path(td) / left).exists(), f"a refused register writes nothing ({left})"
    assert not Path(_env()["KG_RDFLIB_FILE"]).exists(), "a refused register opens no store"


def test_help_passes_the_check_so_the_usage_can_be_read():
    """A person with a bad KG_REGISTER can still read a command's usage: -h and --help pass the check."""
    import cli_exit
    assert cli_exit.asks_help(["due", "--help"]) and cli_exit.asks_help(["-h"]) and not cli_exit.asks_help(["due"])
    assert not cli_exit.asks_help(["ingest", "--", "--help"]), "after --, --help is an argument, not the flag"
    for args in ([ROOT / "harness" / "capture.py", "--help"],
                 [ROOT / "harness" / "capture.py", "due", "--help"],
                 [ROOT / "harness" / "trace.py", "check", "-h"],
                 [ROOT / "harness" / "transcript.py", "--help"],
                 [ROOT / "harness" / "step_grid.py", "--help"],
                 [ROOT / "tools" / "check_subject.py", "--help"]):
        code, out, err = _run(args, KG_REGISTER=NOPE)
        assert code == 0 and "usage:" in out and "readable register" not in err, (args[0].name, args[1:], code, err[-300:])
    code, _, err = _run([ROOT / "harness" / "capture.py", "due", "--out", "x"], KG_REGISTER=NOPE)
    assert code == 2 and "is not a readable register" in err, "without --help the check still refuses"


def test_run_refuses_it_too():
    import importlib.util
    if importlib.util.find_spec("pyshacl") is None:
        from _skip import skip
        skip("rdflib", "harness/run.py imports the pins (pyshacl) before its exit reads the register")
    with tempfile.TemporaryDirectory() as td:
        code, _, err = _run([ROOT / "harness" / "run.py", "--deterministic", "--out", Path(td) / "out"], KG_REGISTER=NOPE)
        assert code == 2 and f"run: cannot run: KG_REGISTER {NOPE} is not a readable register" in err, (code, err[-300:])
        assert not (Path(td) / "out").exists()
        code, out, err = _run([ROOT / "harness" / "run.py", "--help"], KG_REGISTER=NOPE)
        assert code == 0 and "usage:" in out, (code, err[-300:])


def test_check_subject_reads_a_register_as_the_others_do():
    """N10: a folder with only metamodel/types.toml, or without the register's own tools/register.py, gave exit 1
    with every row's node unknown, or exit 0; now it is exit 2 like every other reader's."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "reg"
        (d / "metamodel").mkdir(parents=True)
        (d / "metamodel" / "types.toml").write_text('taxonomy = ["capabilities"]\n', encoding="utf-8")
        code, _, err = _run([ROOT / "tools" / "check_subject.py", CARGO, "--register", d])
        assert code == 2 and "no tools/register.py" in err, (code, err[-300:])
        shutil.copytree(REGISTER, Path(td) / "full", ignore=shutil.ignore_patterns("__pycache__", "tools"))
        code, _, err = _run([ROOT / "tools" / "check_subject.py", CARGO, "--register", Path(td) / "full"])
        assert code == 2 and "no tools/register.py" in err, (code, err[-300:])


def test_a_named_register_that_reads_is_read():
    code, out, err = _run([ROOT / "harness" / "register_nodes.py", "--limit", "1"], KG_REGISTER=str(REGISTER))
    assert code == 0 and '"total"' in out, (code, err[-300:])
