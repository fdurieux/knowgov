"""Task-0075: no check CI runs reads the wall clock where a pinned date exists.

Three holds. harness/review.py ``today()`` is the one clock under harness/, tools/ and demo/; the other
wall-clock reads are named here with what they stamp, and none decides a check's outcome. Under
``KG_CLOCK=pinned`` (the test runner, the rdflib job, every check tool's commands) ``today()`` refuses
the wall clock when KG_TODAY is unset, so an unpinned read fails at once and not on the day its outcome
would move. Every check tool that runs a command reading the date pins it, and every gate command in
the workflows names its date.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tests")]
import review  # noqa: E402

WALL = re.compile(r"\b(?:date|datetime)\.(?:today|now|utcnow)\(|\btime\.(?:localtime|gmtime|strftime)\(")
# vendored bytes (their own SOURCE notes and digests) are not this repository's code
VENDORED = ("demo/register/", "demo/model/", "/vendor/")
# path -> (reads, what it stamps): a read here is a stamp or a view's choice, never a check's outcome
ALLOWED = {
    "harness/review.py": (1, "today() itself: KG_TODAY, else the wall clock unless KG_CLOCK=pinned"),
    "harness/load.py": (1, "the load's provenance stamp when KG_TODAY is unset; no outcome reads it"),
    "demo/app/server.py": (3, "the page's run timestamps and elapsed time"),
    "demo/app/register_project.py": (1, "the projection's loaded_at stamp"),
    "demo/app/register_view.py": (1, "the register view at the wall clock, chosen by the viewer or for a checkout with no pinned date"),
    "tools/vendor_subject.py": (1, "the SOURCE note's copied date, a maintainer's command"),
    "tools/vendor_register.py": (1, "the SOURCE note's copied date, a maintainer's command"),
    "tools/vendor_legible_model.py": (1, "the SOURCE note's copied date, a maintainer's command"),
}
# a harness command or call that reads today's date (directly or through load_reviews / --as-of today)
READS_DATE = re.compile(r"gate_cli|capture\.py|trace\.py|mcp_server|load_reviews|run\.py|transcript\.py|knowgov-gate|KG_GATE")
PINS = re.compile(r"pin_record\(|review\.pinned\(")


def _sources():
    for top in ("harness", "tools", "demo"):
        for p in sorted((ROOT / top).rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            if not any(v in f"/{rel}" or rel.startswith(v) for v in VENDORED):
                yield rel, p.read_text(encoding="utf-8")


def test_today_is_the_one_clock_and_every_other_read_is_named():
    found = {rel: len(WALL.findall(text)) for rel, text in _sources() if WALL.search(text)}
    unnamed = {k: v for k, v in found.items() if k not in ALLOWED}
    assert not unnamed, f"reads the wall clock; read review.today() (KG_TODAY) instead, or name it in ALLOWED: {unnamed}"
    moved = {k: (found.get(k, 0), n) for k, (n, _) in ALLOWED.items() if found.get(k, 0) != n}
    assert not moved, f"the wall-clock reads moved (found, named): {moved}"


def test_a_pinned_run_refuses_the_wall_clock():
    old = {k: os.environ.pop(k, None) for k in ("KG_TODAY", review.CLOCK)}
    try:
        assert review.today() == dt.date.today()
        env = review.pinned({"A": "b"}, "2026-11-03")
        assert env == {"A": "b", "KG_TODAY": "2026-11-03", "KG_CLOCK": "pinned"}
        os.environ.update(env)
        assert review.today() == dt.date(2026, 11, 3)
        try:
            import load   # needs the pinned libraries (pumllint, pyyaml): the rdflib job's interpreter, not the tests job's
        except ModuleNotFoundError:
            load = None
        if load is not None:
            assert load.now() == "2026-11-03T00:00:00+00:00", "a pinned run stamps its pinned day"
        del os.environ["KG_TODAY"]
        try:
            review.today()
            raise AssertionError("KG_CLOCK=pinned with no KG_TODAY read the wall clock")
        except review.WallClock as e:
            assert "task-0075" in str(e)
    finally:
        for k, v in old.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def test_the_record_pin_is_the_subjects_record_date():
    import cadence
    from _subject_pin import CARGO_QUOTE
    env = cadence.pin_record({}, CARGO_QUOTE)
    assert env == {"KG_TODAY": "2026-10-30", "KG_CLOCK": "pinned"}


def test_every_check_tool_that_reads_the_date_pins_it():
    tools = sorted((ROOT / "tools").glob("check_*.py")) + sorted((ROOT / "demo" / "tools").glob("check_*.py"))
    unpinned, popped = [], []
    for p in tools:
        text = p.read_text(encoding="utf-8")
        if 'pop("KG_TODAY"' in text or "pop('KG_TODAY'" in text:
            popped.append(p.name)
        if READS_DATE.search(text) and not PINS.search(text):
            unpinned.append(p.name)
    assert not popped, f"drops a pinned day for the wall clock: {popped}"
    # a check that only reads the store in process (no load of reviews, no gate command) needs no pin;
    # name it here with why, so a new check is pinned by default
    in_process = {"check_saved_queries.py", "check_impact_cypher.py", "check_instance.py"}
    assert not [n for n in unpinned if n not in in_process], f"runs a command that reads the date without pinning it: {unpinned}"


def test_the_review_walkthrough_runs_on_its_own_pinned_day():
    sys.path.insert(0, str(ROOT / "tools"))
    import check_review_walkthrough as w
    assert (w.ANSWERED_ON, w.ON, w.LAPSED) == ("2026-11-02", "2026-11-03", "2027-05-03")
    text = (ROOT / "tools" / "check_review_walkthrough.py").read_text(encoding="utf-8")
    assert "review.pinned(env, ON)" in text and "2027-05-03" not in text


def test_every_gate_command_in_the_workflows_names_its_date():
    wf = ROOT / ".github" / "workflows"
    bad = []
    for p in sorted(wf.glob("*.yml")):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if "gate_cli.py" in line and not line.lstrip().startswith("#") and "--as-of" not in line:
                bad.append(f"{p.name}:{i}")
    assert not bad, f"a gate command reads today; pass --as-of record or a date: {bad}"
    harness = (wf / "harness.yml").read_text(encoding="utf-8")
    assert re.search(r"^\s+KG_CLOCK: pinned$", harness, re.M), "the rdflib job refuses the wall clock"
    # the composite action's gate reads today through its job's environment: the job pins the day first
    if "uses: ./instance/ci/github" in harness:
        pin = harness.find('echo "KG_TODAY=')
        assert 0 <= pin < harness.find("uses: ./instance/ci/github"), "the action's steps run with KG_TODAY in GITHUB_ENV"
