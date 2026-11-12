"""task-0334 (decision-0039 §3.1 (a), doc-0038 §3.1): an instance reads its own register, or refuses.

Before, `cadence.register_root` and `capture.register_root` fell back to `demo/register`, the public register,
when `KG_REGISTER` was unset, and neither `instance/ci/knowgov-gate.sh` nor the Claude Code hook set it: a
client's verdicts, review cadence and accepted givers followed the public register (group C's repro: the
instance's lifecycle months set to 1 gave PROCEED without `KG_REGISTER` and BLOCKED with it; the instance's own
handle refused while the public `employee-1..4` were accepted). Now, with the subject (`KG_SUBJECT`, or a
command's `--subject`) outside this checkout and `KG_REGISTER` unset, every register-reading tool exits 2 naming
`KG_REGISTER` (`harness/instance_register.py`, the test `execution_guard.outside`); the CI script and the hook
pass `<instance>/register` unless one is set; a subject inside the checkout reads `demo/register` as before."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "harness"), str(ROOT / "instance" / "ci" / "claude"),
                str(Path(__file__).resolve().parent)]
import example_instance  # noqa: E402

REGISTER = ROOT / "demo" / "register"
SETTING_LINE = "KG_REGISTER is unset and the subject"
_BUILT: dict[str, Path] = {}


def _instance() -> Path:
    """The public example instance, built once outside this checkout, its register made the instance's own: every
    review month 1 (the public register says 6 and 12) and one issued handle, `giver-7`, in place of employee-1..4."""
    if "inst" not in _BUILT:
        td = Path(tempfile.mkdtemp(prefix="kg-instance-register-"))
        assert ROOT not in td.parents, "the instance must lie outside the checkout"
        inst = example_instance.build(td / "instance")
        life = inst / "register" / "metamodel" / "lifecycle.toml"
        text = re.sub(r"(?m)^default_months = \d+", "default_months = 1", life.read_text(encoding="utf-8"))
        life.write_text(re.sub(r"months = \d+", "months = 1", text), encoding="utf-8")
        (inst / "register" / "people" / "handles.toml").write_text(
            '[[handle]]\nhandle = "giver-7"\nunit = "ORG-0002"\nroles = ["gives", "approves", "closes"]\nissued = 2026-11-02\n',
            encoding="utf-8")
        _BUILT["inst"] = inst
    return _BUILT["inst"]


def _subject() -> Path:
    return _instance() / "subjects" / "cargo_quote"


def _env(**kw) -> dict:
    e = {**os.environ, "KG_CLOCK": "pinned", "KG_TODAY": "2026-11-09", "KG_STORE": "rdflib",
         "KG_RDFLIB_FILE": str(_instance().parent / "never.ttl"), "PYTHONDONTWRITEBYTECODE": "1"}
    for k in ("KG_REGISTER", "KG_SUBJECT", "KG_INSTANCE", "KG_LEDGER"):
        e.pop(k, None)
    e.update({k: v for k, v in kw.items() if v is not None})
    return e


def _run(args, cwd=ROOT, **env):
    r = subprocess.run([sys.executable, *map(str, args)], cwd=cwd, env=_env(**env), capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=300)
    return r.returncode, r.stdout, r.stderr


def test_the_helper_refuses_an_instance_subject_with_no_register_named_and_nothing_else():
    import instance_register
    subj = str(_subject())
    why = instance_register.unnamed({"KG_SUBJECT": subj})
    assert why and why.startswith(SETTING_LINE) and subj in why and "<instance>/register" in why, why
    assert instance_register.unnamed({"KG_SUBJECT": subj, "KG_REGISTER": ""}) == why, "an empty KG_REGISTER is unset"
    assert instance_register.unnamed({"KG_SUBJECT": subj, "KG_REGISTER": str(_instance() / "register")}) is None
    assert instance_register.unnamed({"KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote")}) is None
    assert instance_register.unnamed({}) is None, "no subject named: the default subject ships here"
    try:
        instance_register.check({"KG_SUBJECT": subj})
    except instance_register.RegisterUnnamed as e:
        assert str(e) == why
    else:
        raise AssertionError("check passed an instance subject with no register named")


def test_every_register_reading_tool_refuses_an_instance_with_no_register_named():
    """AC 1: on a copy of the example instance outside the checkout, KG_REGISTER unset, each exits 2 naming it,
    before it reads or writes anything. On main they read demo/register: the gate exited 0, PROCEED."""
    inst, subj = _instance(), _subject()
    td = Path(tempfile.mkdtemp(prefix="kg-instance-register-out-"))
    led = td / "ledger.json"
    led.write_text("{}", encoding="utf-8")
    by_env = {"KG_SUBJECT": str(subj)}
    cases = [
        ("gate_cli", [ROOT / "harness" / "gate_cli.py", "--scenario", "S1", "--as-of", "record"], by_env),
        ("gate_cli --subject", [ROOT / "harness" / "gate_cli.py", "--subject", subj, "--scenario", "S1", "--as-of", "record"], {}),
        ("trace --subject", [ROOT / "harness" / "trace.py", "check", "--instance", inst, "--ledger", led, "--subject", subj], {}),
        ("trace", [ROOT / "harness" / "trace.py", "register", "--instance", inst, "--ledger", led, "--keys", "K|v"], by_env),
        ("capture due", [ROOT / "harness" / "capture.py", "due", "--out", td / "due"], by_env),
        ("capture questionnaire", [ROOT / "harness" / "capture.py", "questionnaire", "--scenario", "S1", "--out", td / "q"], by_env),
        ("register_nodes", [ROOT / "harness" / "register_nodes.py", "--limit", "1"], by_env),
        ("upward", [ROOT / "harness" / "upward.py", "key", "REQ-01|text"], by_env),
        ("proposal_impact", [ROOT / "harness" / "proposal_impact.py", ROOT / "tools" / "fixtures" / "proposal_contract_quote.json",
                             "--no-store"], by_env),
        ("mcp_server", [ROOT / "harness" / "mcp_server.py"], by_env),
    ]
    for name, args, env in cases:
        code, out, err = _run(args, **env)
        assert code == 2 and SETTING_LINE in err and str(subj) in err, (name, code, out[-300:], err[-400:])
    for left in ("due", "q"):
        assert not (td / left).exists(), f"a refused register writes nothing ({left})"
    assert not (inst.parent / "never.ttl").exists(), "a refused register opens no store"
    # cadence's lifecycle months and register_impact, in the process: the same refusal, never demo/register's months
    code, out, err = _run(["-c", (
        "import sys; sys.path.insert(0, 'harness')\n"
        "import cadence, instance_register, register_impact as ri\n"
        "for f in (cadence.cadence, cadence.register_root):\n"
        "    try: f(); print('READ', f.__name__)\n"
        "    except instance_register.RegisterUnnamed as e: print('REFUSED', f.__name__, e)\n"
        "try: ri.walk('CAP-0001'); print('READ walk')\n"
        "except ri.RegisterUnreadable as e: print('REFUSED walk', e)\n")], **by_env)
    assert code == 0 and out.count("REFUSED") == 3 and "READ" not in out and SETTING_LINE in out, (out, err[-400:])


def test_run_refuses_an_instance_with_no_register_named():
    if importlib.util.find_spec("pyshacl") is None:
        from _skip import skip
        skip("rdflib", "harness/run.py imports the pins (pyshacl) before its exit reads the register")
    td = Path(tempfile.mkdtemp(prefix="kg-instance-register-run-"))
    code, _, err = _run([ROOT / "harness" / "run.py", "--deterministic", "--out", td / "out"], KG_SUBJECT=str(_subject()))
    assert code == 2 and f"run: cannot run: {SETTING_LINE}" in err, (code, err[-400:])
    assert not (td / "out").exists()


def test_with_it_named_the_instances_lifecycle_months_and_handles_decide():
    """AC 1, its other half: KG_REGISTER=<instance>/register, and every key's review months are the instance's
    (1), its issued handle is the one accepted, the public employee-1 refused."""
    reg = _instance() / "register"
    code, out, err = _run(["-c", (
        "import sys; sys.path.insert(0, 'harness')\n"
        "import cadence, capture, review\n"
        "from subject import SUBJECT\n"
        "by_key, default = cadence.cadence()\n"
        "print('MONTHS', sorted(set(by_key.values())), default)\n"
        "print('ROOT', capture.register_root())\n"
        "print('HANDLES', sorted(review.issued_handles(capture.register_root())))\n")],
        KG_SUBJECT=str(_subject()), KG_REGISTER=str(reg))
    assert code == 0, err[-400:]
    assert "MONTHS [1] 1" in out and f"ROOT {reg.resolve()}" in out and "HANDLES ['giver-7']" in out, out


def test_with_it_named_the_instances_months_decide_the_gate():
    """Group C's repro, closed: S1 as of its record day reads PROCEED on the public register's months (12, 6),
    BLOCKED with lapses on the instance's (1)."""
    if importlib.util.find_spec("rdflib") is None:
        from _skip import skip
        skip("rdflib", "the gate loads S1 into an rdflib store")
    gate = [ROOT / "harness" / "gate_cli.py", "--subject", _subject(), "--scenario", "S1", "--as-of", "record", "-f", "json"]
    code, out, err = _run(gate, KG_REGISTER=str(_instance() / "register"))
    rep = json.loads(out) if out.strip() else {}
    assert code == 1 and rep.get("verdict") == "BLOCKED" and rep.get("lapsed"), (code, err[-400:])
    code, out, err = _run(gate, KG_REGISTER=str(REGISTER))
    rep = json.loads(out) if out.strip() else {}
    assert code == 0 and rep.get("verdict") == "PROCEED" and not rep.get("lapsed"), (code, err[-400:])


def _fake_knowgov() -> Path:
    """A knowgov checkout whose gate prints the KG_REGISTER it was given: knowgov-gate.sh calls $KG/harness/gate_cli.py."""
    kg = Path(tempfile.mkdtemp(prefix="kg-fake-knowgov-"))
    (kg / "harness").mkdir()
    (kg / "harness" / "gate_cli.py").write_text("import os\nprint('KG_REGISTER=' + os.environ.get('KG_REGISTER', '<unset>'))\n",
                                                encoding="utf-8")
    return kg


def test_the_ci_script_passes_the_instances_register_unless_one_is_named():
    """AC 2: knowgov-gate.sh exports KG_REGISTER=<instance>/register by default, absolute; one named is kept."""
    kg, inst = _fake_knowgov(), _instance()
    script = ROOT / "instance" / "ci" / "knowgov-gate.sh"
    for named, want in ((None, inst / "register"), ("", inst / "register"), (str(REGISTER), REGISTER),
                        ("reg", inst.parent / "reg")):
        e = _env(PYTHON=sys.executable)
        if named is not None:
            e["KG_REGISTER"] = named
        p = subprocess.run(["sh", str(script), str(kg), str(inst), "gate"], cwd=inst.parent, env=e, capture_output=True,
                           text=True, timeout=60)
        assert p.returncode == 0 and f"KG_REGISTER={want}" in p.stdout, (named, p.returncode, p.stdout, p.stderr[-300:])


def test_the_hook_passes_the_instances_register_unless_one_is_named():
    """AC 2: the Claude Code hook's gate call carries KG_REGISTER=<instance>/register unless one is set."""
    import knowgov_hook
    seen = []

    def fake(cmd, **kw):
        seen.append(kw["env"].get("KG_REGISTER"))
        return subprocess.CompletedProcess(cmd, 2, "", "stopped here")
    keep, knowgov_hook.subprocess.run = knowgov_hook.subprocess.run, fake
    old = os.environ.pop("KG_REGISTER", None)
    try:
        inst = _instance()
        knowgov_hook.run_gate("plan", "codegen", ROOT, inst, advisory=False, timeout=5)
        os.environ["KG_REGISTER"] = ""
        knowgov_hook.run_gate("plan", "codegen", ROOT, inst, advisory=False, timeout=5)
        os.environ["KG_REGISTER"] = str(REGISTER)
        knowgov_hook.run_gate("plan", "codegen", ROOT, inst, advisory=False, timeout=5)
    finally:
        knowgov_hook.subprocess.run = keep
        os.environ.pop("KG_REGISTER", None)
        if old is not None:
            os.environ["KG_REGISTER"] = old
    assert seen == [str(inst.resolve() / "register")] * 2 + [str(REGISTER)], seen


def test_a_subject_inside_the_checkout_reads_the_public_register_as_before():
    """AC 3: the record's subjects keep demo/register with KG_REGISTER unset."""
    for subj in (ROOT / "subjects" / "cargo_quote", ROOT / "subjects" / "jef_data_load", None):
        code, out, err = _run(["-c", "import sys; sys.path.insert(0, 'harness')\nimport cadence\nprint(cadence.register_root())"],
                              KG_SUBJECT=str(subj) if subj else None)
        assert code == 0 and out.strip() == str(REGISTER.resolve()), (subj, out, err[-300:])
    code, out, err = _run([ROOT / "harness" / "register_nodes.py", "--limit", "1"], KG_SUBJECT=str(ROOT / "subjects" / "cargo_quote"))
    assert code == 0 and '"total"' in out, (code, err[-300:])


def test_the_guide_says_so():
    """AC 3: instance/README's gates and capture sections, and the settings table's KG_REGISTER default."""
    text = (ROOT / "instance" / "README.md").read_text(encoding="utf-8")

    def section(head: str) -> str:
        a = text.index(head)
        return text[a:text.index("\n## ", a + len(head))]
    for head in ("## Running the gates in your pipeline", "## Capturing what people know"):
        s = section(head)
        assert "KG_REGISTER" in s and "<instance>/register" in s.replace("`", "") and "exit 2" in s, head
    row = next(ln for ln in section("## The settings an instance may rely on").splitlines() if ln.startswith("| `KG_REGISTER` |"))
    assert "outside" in row and "exit 2" in row and "<instance>/register" in row.replace("`", ""), row
    sh = (ROOT / "instance" / "ci" / "knowgov-gate.sh").read_text(encoding="utf-8")
    assert "#   KG_REGISTER " in sh, "the script's header lists KG_REGISTER"
