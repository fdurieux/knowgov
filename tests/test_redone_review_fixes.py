"""task-0329: the redone review's fix-only items that a pure function can hold."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "instance" / "ci" / "claude")]
import gate_cli  # noqa: E402
import knowgov_hook  # noqa: E402


def test_p1_the_preload_identity_ignores_the_path_it_sits_at():
    a = {"path": "/ci/pre.json", "sha256": "a" * 64, "why": None}
    b = {"path": "/home/me/pre.json", "sha256": "a" * 64, "why": None}
    assert not gate_cli._moved(a, b, True)
    assert gate_cli._moved(a, {**b, "sha256": "b" * 64}, True)


def test_q2_a_configuration_difference_names_the_files_that_moved_not_both_maps():
    was = {"subject.toml": "1" * 64, "scenarios.toml": "2" * 64}
    now = {"subject.toml": "1" * 64, "scenarios.toml": "3" * 64}
    (line,) = gate_cli.drift_lines("b.json", [{"field": "configuration", "baseline": was, "now": now}])
    assert "scenarios.toml" in line and "subject.toml" not in line and len(line) < 200


def test_h7_one_slot_per_bar_kind_so_lapses_cannot_crowd_attestation_out():
    fs = [{"severity": "blocker", "kind": "key"}] + [{"severity": "major", "kind": "lapsed", "message": str(i)} for i in range(3)] \
        + [{"severity": "major", "kind": "attestation"}]
    shown = knowgov_hook._shown({"findings": fs})
    assert [f["kind"] for f in shown] == ["key", "attestation", "lapsed"]


def test_c_n6_an_ownerless_finding_does_not_read_none_in_the_register_map():
    src = (ROOT / "harness" / "gate_cli.py").read_text(encoding="utf-8")
    assert "owner {f['owner'] or 'none in the register map'}" not in src
