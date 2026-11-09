"""task-0295 (decision-0034 choice 2(a), G9-17): a scenario id is `[A-Za-z0-9][A-Za-z0-9_-]{0,31}`, one per scenario.

Found by the spot check (CS-3) at 9861953:
- duplicate ids passed `check_subject`, and `Subject` kept the last;
- `id = ""` and `id = "../x"` passed, and the gate reported `"scenario": "../x"`;
- `run.py` writes `out_root / sc`, so `../x` left `--out`.

Now `harness/scenario_ids.py` holds the rule: the checker and the MCP `subject_check` report each breach (rule
`scenario-id`, exit 1), and the `Subject` loader refuses the manifest, so `gate_cli`, `run.py`, the MCP reader and the
page exit 2 naming the id before they write anything. `[[scenario.sources]]` and stage-2 `derived` ids are not
scenario ids. The public subjects' ids all match."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness")]
import check_subject  # noqa: E402
import scenario_ids  # noqa: E402
import schema_check  # noqa: E402
import subject_check  # noqa: E402

REGISTER = ROOT / "demo" / "register"
MINIMAL = ROOT / "subjects" / "minimal"
SCHEMA = schema_check.load("subject-check")


def _with_scenarios(td: Path, text: str) -> Path:
    root = td / "subject"
    shutil.copytree(MINIMAL, root)
    (root / "scenarios.toml").write_text(text, encoding="utf-8")
    return root


def _scenario(sid=None, extra: str = "") -> str:
    head = "" if sid is None else f"id = {json.dumps(sid)}\n"
    return f'[[scenario]]\n{head}extraction = "pristine"\n{extra}\n'


# the forms the spot check named, and their neighbours: (scenarios.toml, the id named in the refusal)
BAD = {
    "duplicate": (_scenario("S0") + _scenario("S0"), "'S0'"),
    "empty": (_scenario(""), "''"),
    "traversal": (_scenario("../x"), "'../x'"),
    "no id": (_scenario(None), "has no id"),
    "space": (_scenario("S 1"), "'S 1'"),
    "leading dash": (_scenario("-S1"), "'-S1'"),
    "too long": (_scenario("S" * 33), "'" + "S" * 33 + "'"),
    "not text": ('[[scenario]]\nid = 7\nextraction = "pristine"\n', "7"),
}


def test_the_rule_reads_an_id_as_the_pattern_and_once_per_subject():
    good = [{"id": s} for s in ("S0", "S1", "C", "D5", "billing-S0", "a_b", "9", "S" * 32)]
    assert scenario_ids.problems(good) == []
    for name, (text, named) in BAD.items():
        import tomllib
        found = scenario_ids.problems(tomllib.loads(text)["scenario"])
        assert found and all(p["code"] == "scenario-id" for p in found) and named in found[0]["message"], (name, found)
        try:
            scenario_ids.check(tomllib.loads(text)["scenario"], "scenarios.toml")
        except scenario_ids.ScenarioIdError as e:
            assert named in str(e) and str(e).startswith("scenarios.toml: "), e
        else:
            raise AssertionError(f"{name} passed")


def test_the_public_subjects_ids_all_match_and_their_reports_hold():
    for root in [p for p in (ROOT / "subjects").iterdir() if (p / "scenarios.toml").is_file()]:
        import tomllib
        assert scenario_ids.problems(tomllib.loads((root / "scenarios.toml").read_text(encoding="utf-8")).get("scenario", [])) == [], root.name
        rep = check_subject.check(root, REGISTER, run_yield=False)
        assert not [f for f in rep["findings"] if f["rule"] == "scenario-id"], (root.name, rep["findings"])


def test_sources_and_stage2_ids_are_not_scenario_ids():
    """A [[scenario.sources]] id and a stage-2 derived id name other things: free text, never checked here."""
    text = (_scenario("S0", '[[scenario.sources]]\nid = "../anything goes"\npath = "x"\n')
            + _scenario("S1", '[scenario.stage2]\nderived = "../also free"\n'))
    import tomllib
    assert scenario_ids.problems(tomllib.loads(text)["scenario"]) == []


def test_the_checker_and_the_mcp_subject_check_report_each_form():
    for name, (text, named) in BAD.items():
        with tempfile.TemporaryDirectory() as td:
            root = _with_scenarios(Path(td), text)
            rep = json.loads(json.dumps(check_subject.check(root, REGISTER, run_yield=False)))
            found = [f for f in rep["findings"] if f["rule"] == "scenario-id"]
            assert rep["exit_code"] == 1 and found and named in found[0]["message"], (name, rep["findings"])
            assert found[0]["where"].startswith("scenarios.toml [[scenario]] #"), found[0]
            assert schema_check.validate(rep, SCHEMA) == [], schema_check.validate(rep, SCHEMA)
            mcp = subject_check.evaluate({"subject_toml": (root / "subject.toml").read_text(encoding="utf-8"),
                                          "scenarios_toml": text, "root": "probe"}, REGISTER)
            assert mcp["exit_code"] == 1 and "scenario-id" in {f["rule"] for f in mcp["findings"]}, (name, mcp["findings"])


def _run(args, root: Path, td: Path):
    env = {**os.environ, "KG_SUBJECT": str(root), "KG_STORE": "rdflib", "KG_RDFLIB_FILE": str(td / "store.ttl"),
           "KG_CLOCK": "pinned", "KG_TODAY": "2026-11-09", "KG_PAGE_PORT": "0"}
    env.pop("KG_REGISTER", None)
    r = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, env=env, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=120)
    return r.returncode, r.stderr


def test_the_loader_refuses_it_so_every_command_exits_2_naming_the_id_before_writing():
    for name in ("duplicate", "traversal", "empty", "no id"):
        text, named = BAD[name]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            root = _with_scenarios(td, text)
            for args in ([ROOT / "harness" / "gate_cli.py", "--scenario", "S0", "--no-load"],
                         [ROOT / "harness" / "mcp_server.py"],
                         [ROOT / "demo" / "app" / "server.py"]):
                code, err = _run(args, root, td)
                assert code == 2 and named in err and "scenarios.toml" in err, (name, args[0].name, code, err[-300:])
            assert not (td / "store.ttl").exists(), "a refused subject opens no store"


def test_run_writes_nothing_outside_its_out():
    import importlib.util
    if importlib.util.find_spec("pyshacl") is None:
        from tests._skip import skip
        skip("rdflib", "harness/run.py imports the pins (pyshacl) before its subject loads")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        root = _with_scenarios(td, BAD["traversal"][0])
        out = td / "runs" / "out"
        code, err = _run([ROOT / "harness" / "run.py", "--deterministic", "--out", out], root, td)
        assert code == 2 and "'../x'" in err and "run: cannot run: " in err and "ScenarioIdError" not in err, (code, err[-300:])
        assert not (td / "runs").exists() and not (td / "runs" / "x").exists(), "nothing written, inside or beside --out"
