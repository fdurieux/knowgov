"""task-0219: H7's probe stays the one pre-registered. Each mutant is an exact-text edit the public codex rebuild
still holds once (a re-vendor that moves a line fails here, not in a probe run), the control is the rebuild
unedited, and the probe's expected table is the one PREREGISTRATION.md §8 froze. Standard library only; the
probe itself, which runs the suite three times, is run by hand and its result kept in RESULTS.md."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE_DIR = ROOT / "subjects" / "jef_data_load" / "probes" / "h7"
sys.path.insert(0, str(ROOT / "tools"))
import check_h7_probe as h7  # noqa: E402


def _sync() -> str:
    return (h7.REBUILD / h7.SYNC).read_text(encoding="utf-8")


def test_each_mutant_is_one_edit_of_the_public_rebuild_and_the_control_none():
    text = _sync()
    for a in (h7.FETCH, h7.ACTIONS, h7.GUARD):
        assert text.count(a) == 1, a
    assert h7.mutate(text, "control") == text
    m1 = h7.mutate(text, "m1")
    assert m1 != text and sorted(m1.splitlines()) == sorted(text.splitlines()), "m1 moves a line, adds and drops none"
    assert m1.index(h7.FETCH) < m1.index(h7.ACTIONS) and text.index(h7.ACTIONS) < text.index(h7.FETCH)
    m2 = h7.mutate(text, "m2")
    assert h7.GUARD not in m2 and m2 == text.replace(h7.GUARD, "", 1)
    assert "vendor/recreate_experiment/rebuilds/codex-2026-10-24" in h7.REBUILD.as_posix(), "public code only"


def test_the_expected_table_is_the_pre_registered_one():
    pre = (PROBE_DIR / "PREREGISTRATION.md").read_text(encoding="utf-8")
    table = pre.split("### 8. Expectations", 1)[1].split("\n\n", 2)[1]
    rows = {}
    for line in table.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] in h7.VARIANTS:
            rows[cells[0]] = {"r_stale": cells[1].startswith("flagged"), "drift": cells[2].startswith("flagged"),
                              "suite": not cells[3].startswith("258 of 258")}
    assert rows == h7.EXPECTED, rows


def test_the_results_are_kept_beside_the_pre_registration_and_name_its_commit():
    res = (PROBE_DIR / "RESULTS.md").read_text(encoding="utf-8")
    assert "370b76d" in res and "every cell as pre-registered" in res
    for v in h7.VARIANTS:
        assert re.search(rf"^\| {v} \|", res, re.M), v
