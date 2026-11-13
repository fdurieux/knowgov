"""task-0307 (decision-0037, doc-0037 §3.3; the functional review's group A, F2 and F3, at f194aac): the gate report
names the corpus it decided on, and ``--baseline`` names each identity field that differs from the baseline's.

F2: after an in-place edit of decision_table.md (P2's threshold 1244 to 1300), ``task_profile``, ``register`` and
``knowgov`` were the pristine S1 report's; only the verdict, why, findings and levels moved. Now ``corpus``, the
digest of the loaded document Versions, moves with the edit. F3: an S1 report with ``task_profile``, ``register.tag``,
``knowgov.version`` and ``as_of`` edited read as a baseline gave "no regression", exit 0, and said nothing; now each
changed field is named on stderr, the exit unchanged. A field the baseline lacks or holds as unknown is never named.
Stand-in values only; no network, the clock pinned."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))
import gate_cli  # noqa: E402
import store  # noqa: E402
from tests._skip import need_rdflib  # noqa: E402

TABLE = "vendor/stack_experiment/cargo_quote/contract/decision_table.md"
P2, P2_EDITED = "`weight_kg > 1244`", "`weight_kg > 1300`"


def _need_s1():
    """task-0314: these two ask for scenario S1; a subject whose scenarios are not CargoQuote's (J-F's) skips them."""
    from subject import SUBJECT
    from tests._skip import skip
    if "S1" not in SUBJECT.order:
        skip("scenario-S1", f"{SUBJECT.id} has no scenario S1 (its scenarios: {', '.join(SUBJECT.order)})")


def test_the_corpus_is_one_line_per_version_sorted_whatever_the_adapters_order():
    rows = [{"artefact": "b.md", "version": "v1", "sha256": "2" * 64},
            {"artefact": "a.md", "version": "v2", "sha256": "3" * 64},
            {"artefact": "a.md", "version": "v1", "sha256": "1" * 64}]
    # task-0320 (decision-0038 N4): one canonical JSON array per Version and a newline, the lines sorted
    text = "".join(json.dumps(x, separators=(",", ":")) + "\n" for x in sorted((
        ["a.md", "v1", "1" * 64], ["a.md", "v2", "3" * 64], ["b.md", "v1", "2" * 64]), key=lambda x: json.dumps(x, separators=(",", ":"))))
    want = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert store.corpus_digest(rows) == want == store.corpus_digest(list(reversed(rows)))
    assert store.corpus_digest(rows[:2]) != want, "every Version counts, a stage-2 change's earlier one included"
    assert store.corpus_digest([{**rows[0], "sha256": "4" * 64}, *rows[1:]]) != want, "a document's bytes count"
    assert store.corpus_digest([]) is None, "nothing loaded: no corpus"
    assert "version_digests" in store.READS, "a read of the port, so the MCP reader's view serves it"
    import mcp_server
    assert "version_digests" in mcp_server.READS


def test_a_field_the_baseline_lacks_or_holds_as_unknown_is_never_a_difference():
    now = {"task_profile": "a" * 64, "register": {"tag": "v0.2.13", "commit": "c" * 40, "why": None},
           "knowgov": {"version": "0.8.0", "commit": "d" * 40, "describe": "v0.8.0"}, "corpus": "e" * 64, "as_of": "2026-10-30"}
    assert gate_cli.identity_drift(dict(now), now) == []
    assert gate_cli.identity_drift({}, now) == [], "a version-2 report, or the record's file: every field unknown"
    unknown = {"task_profile": None, "register": {"tag": None, "commit": None, "why": "no SOURCE.md"},
               "knowgov": {"version": None, "commit": None, "describe": None}, "corpus": None, "as_of": None}
    assert gate_cli.identity_drift(unknown, now) == [], "null, or an object of nulls, reads as unknown"
    assert gate_cli.identity_drift(now, {**now, "corpus": None}) == [], "this run's unknown is no difference either"
    moved = {**now, "corpus": "f" * 64, "register": {**now["register"], "tag": "v0.1.0"}}
    got = gate_cli.identity_drift(moved, now)
    assert [d["field"] for d in got] == ["register", "corpus"], got
    lines = gate_cli.drift_lines("base.json", got)
    assert lines[1] == f"gate: --baseline base.json: corpus differs: the baseline's {'f' * 64}, this run's {'e' * 64}", lines


def _env(root: Path | None = None) -> dict:
    env = {**os.environ, "KG_STORE": "rdflib", "KG_CLOCK": "pinned", "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("KG_RDFLIB_FILE", None)
    if root is not None:
        env.update(KG_SUBJECT=str(root), KG_SUBJECTS=str(root.parent))
        env.setdefault("KG_REGISTER", str(HARNESS.parent / "demo" / "register"))   # a copy outside the checkout names its register (task-0334)
    return env


def _gate(*args, root: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HARNESS / "gate_cli.py"), "--scenario", "S1", "-f", "json", *args],
                          capture_output=True, text=True, env=_env(root), timeout=600)


def test_f3_each_changed_field_is_named_and_the_exit_is_unchanged_f2_moves_the_corpus():
    need_rdflib()
    _need_s1()
    with tempfile.TemporaryDirectory() as td:
        first = _gate("--as-of", "record")
        assert first.returncode in (0, 1) and not first.stderr.strip(), first.stderr[-400:]
        pristine = json.loads(first.stdout)
        assert len(pristine["corpus"] or "") == 64, pristine["corpus"]
        # F3: four identity fields edited, read as a baseline
        f3 = json.loads(first.stdout)
        f3["task_profile"] = "0" * 64
        f3["register"]["tag"] = "v0.1.0"
        f3["knowgov"]["version"] = "0.5.0"
        f3["as_of"] = "2020-01-01"
        base = Path(td) / "f3.json"
        base.write_text(json.dumps(f3), encoding="utf-8")
        again = _gate("--as-of", "record", "--baseline", str(base))
        named = [line.split(": ")[2].split(" differs")[0] for line in again.stderr.splitlines() if " differs: " in line]
        assert named == ["task_profile", "register", "knowgov", "as_of"], again.stderr[-800:]
        assert "the baseline's 2020-01-01, this run's" in again.stderr and '"tag":"v0.1.0"' in again.stderr
        rep = json.loads(again.stdout)
        assert again.returncode == 0 and rep["baseline"]["regression"] is False, (again.returncode, rep["baseline"])
        assert rep["corpus"] == pristine["corpus"], "the pristine corpus is stable from run to run"
        # a baseline without the field, a version-3 report from before task-0307: unknown, never named
        before = {k: v for k, v in pristine.items() if k != "corpus"}
        base.write_text(json.dumps(before), encoding="utf-8")
        quiet = _gate("--as-of", "record", "--baseline", str(base))
        assert quiet.returncode == 0 and " differs: " not in quiet.stderr, quiet.stderr[-400:]
        # F2: the decision table edited in place in a copy of the subject; only the corpus of the identity moves
        root = Path(td) / "cargo_quote"
        shutil.copytree(ROOT / "subjects" / "cargo_quote", root, ignore=shutil.ignore_patterns("__pycache__"))
        table = root / TABLE
        text = table.read_text(encoding="utf-8")
        assert text.count(P2) == 1
        table.write_text(text.replace(P2, P2_EDITED), encoding="utf-8")
        edited = json.loads(_gate("--as-of", "record", root=root).stdout)
        assert edited["corpus"] != pristine["corpus"] and len(edited["corpus"]) == 64
        for field in ("task_profile", "register", "knowgov", "as_of"):
            assert edited[field] == pristine[field], field
        base.write_text(json.dumps(pristine), encoding="utf-8")
        named = _gate("--as-of", "record", "--baseline", str(base), root=root)
        assert [ln for ln in named.stderr.splitlines() if " differs: " in ln] == [
            f"gate: --baseline {base}: corpus differs: the baseline's {pristine['corpus']}, this run's {edited['corpus']}"], named.stderr[-600:]


def test_the_records_baseline_holds_its_as_of_and_nothing_else():
    """``--baseline record``: the deterministic.json names no identity; the record is as of the subject's
    ``[record] as_of``, so only a run on another date names a difference."""
    need_rdflib()
    _need_s1()
    from subject import SUBJECT
    on = SUBJECT.record_as_of
    assert on, "the subject pins its record date"
    same = _gate("--as-of", "record", "--baseline", "record")
    assert same.returncode in (0, 1) and " differs: " not in same.stderr, same.stderr[-400:]
    other = _gate("--as-of", "2026-12-31", "--baseline", "record")
    lines = [ln for ln in other.stderr.splitlines() if " differs: " in ln]
    assert lines == [f"gate: --baseline record: as_of differs: the baseline's {on}, this run's 2026-12-31"], other.stderr[-600:]
    assert json.loads(other.stdout)["exit_code"] == other.returncode
