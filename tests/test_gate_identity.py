"""task-0237, decision-0029 (task-0103 AC #3, doc-0014 C9 option B): the gate report names what it decided
on. ``task_profile`` is the sha256 of the canonical JSON of the subject's ``[tasks.<class>]`` table the gate
read; ``register`` the register's tag and commit (a vendored copy's SOURCE.md, else an instance checkout's
git HEAD read without the network, else null with why); ``knowgov`` the build (task-0227). Schema version 3
requires the three. Stand-in registers only; no network, no wall clock."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import gate_cli  # noqa: E402
import register_impact  # noqa: E402
import schema_check  # noqa: E402
from tests._skip import need_rdflib, skip  # noqa: E402


def test_the_task_profile_is_the_canonical_json_digest_of_the_table_read():
    table = {"keys": ["b|y", "a|x"], "max_unverified_share": 0.25, "rationale": "why", "block_levels": ["absent"]}
    want = hashlib.sha256(json.dumps(table, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    assert gate_cli.profile_digest(table) == want and re.fullmatch(r"[0-9a-f]{64}", want)
    assert gate_cli.profile_digest(dict(reversed(list(table.items())))) == want, "the table's own order does not count"
    assert gate_cli.profile_digest({**table, "keys": ["a|x", "b|y"]}) != want, "the order of the keys is the table's: it counts"
    assert gate_cli.profile_digest({**table, "max_unverified_share": 0.5}) != want
    assert gate_cli.profile_digest(None) is None


def _source_note(root: Path) -> tuple[str | None, str | None]:
    text = (root / "SOURCE.md").read_text(encoding="utf-8")
    c = re.search(r"\| commit \| `([0-9a-f]{40})`", text)
    t = re.search(r"^\| tag \| `(v[0-9][^`]*)`", text, re.M)
    return (t.group(1) if t else None), (c.group(1) if c else None)


def test_the_register_is_named_from_its_source_note_its_own_checkout_or_not_at_all():
    # the vendored register: SOURCE.md's tag and commit, whatever the tag is (re-vendored in parallel)
    reg = ROOT / "demo" / "register"
    tag, commit = _source_note(reg)
    assert register_impact.identity(reg) == {"tag": tag, "commit": commit, "why": None} and commit
    with tempfile.TemporaryDirectory() as td:
        bare = Path(td) / "bare"
        bare.mkdir()
        got = register_impact.identity(bare)   # no SOURCE.md, no checkout of its own
        assert got["tag"] is None and got["commit"] is None and got["why"], got
        if shutil.which("git") is None:
            skip("git", "git is not installed; the checkout case needs it")
        repo = Path(td) / "register"
        repo.mkdir()
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True, env=env).stdout.strip()  # noqa: E731
        run("init", "-q")
        (repo / "nodes.toml").write_text("x = 1\n", encoding="utf-8")
        run("add", ".")
        run("commit", "-q", "-m", "one")
        head = run("rev-parse", "HEAD")
        assert register_impact.identity(repo) == {"tag": None, "commit": head, "why": None}, "no tag on HEAD: none named"
        run("tag", "v9.9.9")
        assert register_impact.identity(repo) == {"tag": "v9.9.9", "commit": head, "why": None}
        sub = repo / "inner"
        sub.mkdir()
        got = register_impact.identity(sub)   # inside a checkout, not one of its own: never the enclosing repository's
        assert got["commit"] is None and "not a git checkout of its own" in got["why"], got


def test_every_report_names_what_it_decided_on_and_gives_the_same_bytes_twice():
    """On the loaded subject's first scenario, rdflib: version 3, the three fields, the schema; the profile
    is the digest of the manifest's own table; a key set asked for digests the table with those keys; and
    two reports of one store are byte-equal (KG_CLOCK=pinned, as the runner sets it)."""
    need_rdflib()
    from store import open_store
    from subject import SUBJECT
    from tasks import TASKS
    scenario = SUBJECT.order[0]
    keep = {k: os.environ.get(k) for k in ("KG_STORE", "KG_RDFLIB_FILE")}
    os.environ["KG_STORE"] = "rdflib"
    os.environ.pop("KG_RDFLIB_FILE", None)
    try:
        st = open_store(access="write", instance=SUBJECT.id)
        try:
            gate_cli._load(st, scenario)
            task = next(iter(TASKS))
            spec = dict(TASKS[task])
            ask = lambda **kw: gate_cli.evaluate(st, subject=SUBJECT.id, scenario=scenario, task=kw.get("name", task),  # noqa: E731
                                                 spec=kw.get("spec", spec), threshold="blocker", baseline=None, loaded=True,
                                                 as_of="record", route_task=task)
            rep = ask()
            again = ask()
            mine = dict(spec, keys=spec["keys"][:1])
            keyset = ask(name="keys", spec=mine)
        finally:
            st.close()
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    assert rep["schema_version"] == 3 and not schema_check.validate(rep, schema_check.load("gate-report")), \
        schema_check.validate(rep, schema_check.load("gate-report"))[:3]
    assert rep["task_profile"] == gate_cli.profile_digest(SUBJECT.tasks[task])
    assert keyset["task_profile"] == gate_cli.profile_digest({**SUBJECT.tasks[task], "keys": spec["keys"][:1]}) != rep["task_profile"]
    reg = Path(os.environ.get("KG_REGISTER") or ROOT / "demo" / "register").resolve()
    # task-0320 (decision-0038 N2): beside the tag and commit, the digest of the register's files as read
    assert rep["register"] == {**register_impact.identity(reg), "files": register_impact.files_digest(reg)}
    import build_identity
    assert rep["knowgov"] == build_identity.identity() and rep["knowgov"]["version"] == (ROOT / "VERSION").read_text().strip()
    assert json.dumps(rep, sort_keys=True) == json.dumps(again, sort_keys=True), "deterministic: one store, one report"


def test_a_version_2_report_still_reads_as_a_baseline():
    old = {"schema_version": 2, "tool": "knowgov gate", "verdict": "PROCEED", "levels": {"a|x": "verified"}, "suspect_derived": []}
    assert gate_cli.baseline_of(old) == {"verdict": "PROCEED", "levels": {"a|x": "verified"}, "suspect": [],
                                         "identity": {}}, "a version-2 report names no identity: every field unknown (task-0307)"
