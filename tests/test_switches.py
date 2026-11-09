"""task-0276 (decision-0033 choice 2, G9-17): every on/off setting is read through one parser. A flag is on
with 1 and off with 0, empty or unset; a setting documented with a word keeps it (KG_LOAD_MEMORY_CHECK=off,
KG_KEY_CHECK=off). Anything else exits 2, naming the setting and the spellings it accepts: before,
KG_NO_LOAD=true silently meant off. The action's publish, annotate and sarif take true or false in any case,
and anything else fails naming the input."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness")]
import cli_exit  # noqa: E402
import switches  # noqa: E402

GATE_SH = ROOT / "instance" / "ci" / "knowgov-gate.sh"
ACTION = ROOT / "instance" / "ci" / "github" / "action.yml"
DOCUMENTED = {   # every spelling the documents give today, and what it meant then (decision-0033: it keeps it)
    "KG_NO_LOAD": {"1": True}, "KG_PUBLISH": {"1": True}, "KG_ALLOW_UNCONTAINED_EXECUTION": {"1": True},
    "KG_TRACEBACK": {"1": True}, "KG_THINKING_UNCOUNTED": {"1": True, "": False},
    "KG_LOAD_MEMORY_CHECK": {"off": False}, "KG_KEY_CHECK": {"off": False, "on": True},
    "KG_CLOCK": {"pinned": True}}


def _refused(name, value):
    try:
        switches.parse(name, value)
    except switches.BadSwitch as e:
        return str(e)
    return None


def test_every_switch_keeps_its_documented_spellings_and_unset_is_its_default():
    assert set(DOCUMENTED) == set(switches.SWITCHES)
    for name, spellings in DOCUMENTED.items():
        for value, meant in spellings.items():
            assert switches.parse(name, value) is meant, (name, value)
        default = switches.SWITCHES[name][0] is switches.WORD_ON   # a check is on unless switched off; a flag off
        assert switches.parse(name, None) is default and switches.parse(name, "") is default, name
    for name in ("KG_NO_LOAD", "KG_TRACEBACK"):
        assert switches.parse(name, "0") is False
    assert switches.parse("KG_KEY_CHECK", "OFF") is False and switches.parse("KG_LOAD_MEMORY_CHECK", "Off") is False


def test_any_other_value_is_refused_naming_the_setting_and_its_spellings():
    for name in ("KG_NO_LOAD", "KG_PUBLISH", "KG_ALLOW_UNCONTAINED_EXECUTION", "KG_TRACEBACK", "KG_THINKING_UNCOUNTED"):
        for bad in ("true", "yes", "on", "TRUE", "2", "false", " 1", "1 "):
            why = _refused(name, bad)
            assert why and name in why and "1 (on)" in why and repr(bad) in why, (name, bad, why)
    for name in ("KG_LOAD_MEMORY_CHECK", "KG_KEY_CHECK"):
        for bad in ("0", "no", "false", "disabled", "1", " off", "off "):
            why = _refused(name, bad)
            assert why and name in why and "off (off)" in why, (name, bad, why)


def test_no_reader_parses_a_switch_of_its_own():
    """The settings are read through switches.on only: no comparison of their raw value anywhere else."""
    scanned = [p for d in ("harness", "demo/app", "tools", "demo/tools", "instance") for p in (ROOT / d).rglob("*.py")]
    for p in scanned:
        if p.name == "switches.py" or "fixtures" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        for name in switches.SWITCHES:
            raw = re.search(rf"environ(?:\.get)?[(\[]\s*[\"']{name}[\"']\s*[)\]]\s*(?:or [^)]*\))?\s*(?:\.|==|!=|in\b|not\s+in\b)", text) \
                or re.search(rf"env\.get\(\s*(?:[\w.]+\.)?OPT_IN\s*\)\s*==", text)
            assert not raw, f"{p.relative_to(ROOT)} reads {name} itself: {raw.group(0)}"


def test_a_command_refuses_a_bad_traceback_switch_with_exit_2():
    old = os.environ.get("KG_TRACEBACK")
    try:
        os.environ["KG_TRACEBACK"] = "true"
        ran = []
        assert cli_exit.run(lambda: ran.append(1), "probe") == 2 and not ran
        os.environ["KG_TRACEBACK"] = "1"
        assert cli_exit.run(lambda: 0, "probe") == 0
    finally:
        os.environ.pop("KG_TRACEBACK", None) if old is None else os.environ.__setitem__("KG_TRACEBACK", old)


def _shell_flag(value: str | None) -> tuple[int, str]:
    """knowgov-gate.sh's own flag function, run on a value, exactly as the script defines it."""
    fn = re.search(r"(?ms)^flag\(\) \{.*?^\}\n", GATE_SH.read_text(encoding="utf-8")).group(0)
    p = subprocess.run(["sh", "-c", fn + 'if flag KG_NO_LOAD "${V-}"; then echo on; else echo off; fi'],
                       env={"PATH": "/usr/bin:/bin", **({} if value is None else {"V": value})}, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def test_the_ci_script_reads_its_flags_under_the_same_rule():
    for value in ("1", "0", "", None):
        rc, out = _shell_flag(value)
        assert rc == 0 and out == ("on" if switches.parse("KG_NO_LOAD", value) else "off"), (value, rc, out)
    for bad in ("true", "yes", "on", "2"):
        rc, out = _shell_flag(bad)
        assert rc == 2 and "KG_NO_LOAD" in out and "1 (on)" in out, (bad, rc, out)
    text = GATE_SH.read_text(encoding="utf-8")
    assert 'if flag KG_NO_LOAD "${KG_NO_LOAD:-}"' in text and 'if flag KG_PUBLISH "${KG_PUBLISH:-}"' in text
    assert '= 1 ]' not in text


def test_the_gate_script_exits_2_on_a_misspelt_flag_before_it_runs_anything():
    with tempfile.TemporaryDirectory() as td:
        inst = Path(td) / "inst"
        (inst / "subjects" / "s").mkdir(parents=True)
        (inst / "subjects" / "s" / "subject.toml").write_text("", encoding="utf-8")
        env = {"PATH": "/usr/bin:/bin", "PYTHON": sys.executable, "KG_NO_LOAD": "true", "KG_ANNOTATE": ""}
        p = subprocess.run(["sh", str(GATE_SH), str(ROOT), str(inst), "gate"], env=env, capture_output=True, text=True, timeout=60)
        assert p.returncode == 2 and "KG_NO_LOAD='true'" in p.stderr, (p.returncode, p.stderr[-500:])


def _action_bool(name: str, value: str) -> tuple[int, str]:
    run = ACTION.read_text(encoding="utf-8").split("      run: |\n", 1)[1]
    fn = re.search(r"(?ms)^        bool\(\) \{.*?^        \}\n", run).group(0)
    p = subprocess.run(["sh", "-c", fn + f'v=$(bool {name} "$V") || exit 2; echo "$v"'],
                       env={"PATH": "/usr/bin:/bin", "V": value}, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def test_the_actions_switch_inputs_take_true_or_false_in_any_case_and_fail_otherwise():
    for name in ("publish", "annotate", "sarif"):
        for value, want in (("true", "true"), ("True", "true"), ("FALSE", "false"), ("false", "false")):
            assert _action_bool(name, value) == (0, want), (name, value)
        for bad in ("yes", "1", "", "on"):
            rc, out = _action_bool(name, bad)
            assert rc == 2 and f"input {name}" in out and "true or false" in out, (name, bad, rc, out)
    text = ACTION.read_text(encoding="utf-8")
    assert "inputs.publish == 'true'" not in text and '"$KNOWGOV_ANNOTATE" = true' not in text
    assert "if: always() && inputs.sarif == 'true'" in text   # a GitHub expression: compared without case already


def test_kg_clock_takes_only_pinned_and_a_misspelling_never_reads_the_wall_clock():
    """task-0287: KG_CLOCK=Pinned, 'pinned ' or 1 silently read the wall clock; now they are refused by name."""
    import review
    for bad in ("Pinned", "pinned ", " pinned", "1", "yes", "true"):
        why = _refused("KG_CLOCK", bad)
        assert why and "KG_CLOCK" in why and "pinned" in why, (bad, why)
    saved = {k: os.environ.get(k) for k in ("KG_CLOCK", "KG_TODAY")}
    try:
        os.environ.pop("KG_TODAY", None)
        for bad in ("Pinned", "1"):
            os.environ["KG_CLOCK"] = bad
            try:
                review.today()
            except switches.BadSwitch as e:
                assert "KG_CLOCK" in str(e)
            else:
                raise AssertionError(f"KG_CLOCK={bad!r} read the wall clock")
        os.environ["KG_CLOCK"] = "pinned"
        try:
            review.today()
        except review.WallClock:
            pass
        else:
            raise AssertionError("pinned without KG_TODAY must refuse the wall clock")
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def test_a_misspelt_switch_reaches_the_exit_as_itself_never_as_the_store():
    """task-0287 N9: the gate's and the trace's catch-all for the store lets BadSwitch through, so cli_exit names it."""
    for path in ("harness/gate_cli.py", "harness/trace.py"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert re.search(r"except \([^)]*switches\.BadSwitch[^)]*\):[^\n]*\n\s+raise\n", text), path
    assert "BadSwitch" in cli_exit.OWN
