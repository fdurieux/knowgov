"""task-0326 (doc-0038 §4 P3) and task-0327 (P4): the impact readers agree with the gate on what leaves the approved
register and on which derived output is suspect.

P3: branch mode lists a node file whose state moves to retired or deprecated in place under ``not_read``, with no
reuse entry and no self-candidate. P4: ``register_impact``'s ``with_levels`` attributes a suspect output to a key by
``used_changed`` as well as by a stale statement."""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import register_impact as ri  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

OUT = "derived:code@c0ffee1:reference_impl.py"
STMT = "A:dt:P2|surcharge@v1"


class _St:
    def derived_outputs(self):
        return [{"id": OUT, "used": [{"id": STMT, "key": "P2|surcharge"}, {"id": "A:x@v1", "key": "other|k"}]}]


def _report():
    f = {"kind": "suspect_derived", "ref": OUT, "related": [STMT], "key": None}
    return {"findings": [f], "levels": {"P2|surcharge": "proposed", "other|k": "proposed"}}


def test_p4_an_output_suspect_by_used_changed_is_attributed_to_its_key():
    rows = [{"key": "P2|surcharge"}, {"key": "other|k"}]
    got = {r["key"]: r["suspect"] for r in ri.with_levels(rows, _report(), ri.statement_keys(_St()))}
    assert got == {"P2|surcharge": [OUT], "other|k": []}, got
    assert all(r["stale"] == [] for r in ri.with_levels(rows, _report(), ri.statement_keys(_St())))
    # without the statement-to-key map, as before: attributed only through a stale statement
    assert [r["suspect"] for r in ri.with_levels(rows, _report())] == [[], []]


def _git(repo, *a):
    import subprocess
    import os
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env)


def test_p3_a_node_retired_in_place_is_not_read_as_a_reuse_and_has_no_self_candidate():
    need_rdflib()
    import proposal_impact as pi
    with tempfile.TemporaryDirectory() as td:
        reg = Path(td) / "register"
        shutil.copytree(ROOT / "demo" / "register", reg, ignore=shutil.ignore_patterns("__pycache__"))
        _git(reg, "init", "-q", "-b", "main")
        _git(reg, "add", "-A")
        _git(reg, "commit", "-qm", "base")
        _git(reg, "checkout", "-q", "-b", "retire")
        p = reg / "capabilities" / "CAP-0003.toml"
        p.write_text(re.sub(r'(?m)^state = "approved"', 'state = "retired"', p.read_text(encoding="utf-8"), count=1), encoding="utf-8")
        _git(reg, "commit", "-qam", "retire CAP-0003 in place")
        import datetime as dt
        r = pi.evaluate_branch(reg, "main", today=dt.date(2026, 11, 4))
        txt = json.dumps(r, default=str)
        paths = [x["path"] for x in r["branch"]["not_read"]]
        assert "capabilities/CAP-0003.toml" in paths, paths
        why = [x["why"] for x in r["branch"]["not_read"] if x["path"].endswith("CAP-0003.toml")][0]
        assert "register_impact" in why and "register-previous" in why
        assert r["reach"] == [] and "same as CAP-0003" not in txt and not r["candidates"], (r["reach"], r["candidates"])
