"""proposal_impact's branch mode on a scratch branch of the public register (task-0132).

    python tools/check_proposal_branch.py

Copies the vendored register (``demo/register``) into a temporary git repository, commits it on
``main``, then on a branch ``proposal`` writes doc-0017's worked example
(``tools/fixtures/proposal_contract_quote.json``) as the register's own files, in state ``draft``, as an
author would, and commits it. Then runs ``instance/ci/proposal-impact.sh`` on the checkout against
``main``, the CI template's optional step, and requires: exit 0; the report it writes valid under its
schema; the report equal, ids aside, to the report for the same proposal held in the call; and the
checkout's bytes and HEAD unchanged. Exit 0 when every check holds, 1 when one does not. Synthetic
data only; the temporary repository is removed.
"""
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
FIXTURE = ROOT / "tools" / "fixtures" / "proposal_contract_quote.json"
DAY = "2026-11-04"
sys.path.insert(0, str(ROOT / "harness"))


def _q(v) -> str:
    return json.dumps(v)


def write_as_files(root: Path, proposal: dict) -> None:
    """The proposal written into a register tree as draft node files and draft links (REL-9xxxx), each
    link owned by its source node's owner, as the held overlay defaults it."""
    import register_impact as ri
    T = ri.load_tools(root)
    reg = T["register"].load_register(root)
    k2t = T["register"].kind_taxonomy(reg)
    owner = {n["id"]: n["owner"] for n in proposal["nodes"]} | {k: v.get("owner") for k, v in reg["nodes"].items()}
    for n in proposal["nodes"]:
        lines = [f"{k} = {_q(n[k])}" for k in ("id", "kind", "name", "parent") if n.get(k)]
        lines += ['state = "draft"', f"owner = {_q(n['owner'])}"]
        (root / k2t[n["kind"]] / f"{n['id']}.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for i, ln in enumerate(proposal["links"]):
        p = root / "relationships" / f"{ln['type']}.toml"
        p.write_text(p.read_text(encoding="utf-8") + "\n[[link]]\n" + "\n".join([
            f'id = "REL-9{i:04d}"', f"source = {_q(ln['source'])}", f"target = {_q(ln['target'])}", 'state = "draft"',
            f"rationale = {_q(ln['rationale'])}", f"owner = {_q(ln.get('owner') or owner[ln['source']])}"]) + "\n", encoding="utf-8")


def git(repo: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "ci", "GIT_AUTHOR_EMAIL": "ci@example.invalid",
           "GIT_COMMITTER_NAME": "ci", "GIT_COMMITTER_EMAIL": "ci@example.invalid"}
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


def scratch_branch(dest: Path, proposal: dict) -> Path:
    """A git checkout of the vendored register at ``dest``: ``main`` as vendored, ``proposal`` checked
    out with the proposal committed as files."""
    reg = dest / "register"
    shutil.copytree(ROOT / "demo" / "register", reg, ignore=shutil.ignore_patterns("__pycache__"))
    git(reg, "init", "-q", "-b", "main")
    git(reg, "add", "-A")
    git(reg, "commit", "-qm", "the register as vendored")
    git(reg, "checkout", "-q", "-b", "proposal")
    write_as_files(reg, proposal)
    git(reg, "add", "-A")
    git(reg, "commit", "-qm", "a proposal, as draft files")
    return reg


def digests(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def ids_aside(r: dict) -> dict:
    """A report with what names the proposal's own identity removed: the link ids (provisional in the
    call, the branch's REL ids on a branch), the overlay's digest and title, the register line and the
    branch section; and whether a reused node was declared, since a branch names its reused nodes only
    through its links (a held proposal may list them)."""
    r = json.loads(json.dumps(r, default=str))
    for x in r["reach"]:
        x.pop("declared")
    names = {ln["id"]: f"link:{ln['type']}:{ln['source']}:{ln['target']}" for ln in r["links"]}
    for k in ("register", "branch"):
        r.pop(k, None)
    r["overlay"].pop("digest")
    r["overlay"].pop("title")
    text = json.dumps(r, sort_keys=True)
    for lid, name in sorted(names.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(f'"{lid}"', f'"{name}"').replace(f"link {lid}", f"link {name}")
    return _sorted(json.loads(text))


def _sorted(x):
    """Every list in a canonical order: the order of a proposal's elements is the author's (a file's,
    on a branch, by path), not part of the answer."""
    if isinstance(x, dict):
        return {k: _sorted(v) for k, v in x.items()}
    if isinstance(x, list):
        return sorted((_sorted(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    return x


def main(argv: list[str] | None = None) -> int:
    import proposal_impact as pi
    import schema_check
    failures = []
    proposal = json.loads(FIXTURE.read_text(encoding="utf-8"))
    top = Path(tempfile.mkdtemp(prefix="kg-proposal-branch-"))
    try:
        reg = scratch_branch(top, proposal)
        before, head = digests(reg), git(reg, "rev-parse", "HEAD")
        out = top / "report.json"
        env = {**os.environ, "KG_AS_OF": DAY, "KG_PROPOSAL_REPORT": str(out), "PYTHON": sys.executable}
        run = subprocess.run(["sh", str(ROOT / "instance" / "ci" / "proposal-impact.sh"), str(ROOT), str(reg), "main"],
                             capture_output=True, text=True, env=env)
        print(run.stdout, end="")
        if run.returncode != 0:
            failures.append(f"proposal-impact.sh exited {run.returncode}: {run.stderr.strip()}")
        else:
            got = json.loads(out.read_text(encoding="utf-8"))
            errors = schema_check.validate(got, schema_check.load("proposal-impact"))
            if errors:
                failures.append(f"the branch report is not valid under its schema: {errors[:3]}")
            held = pi.evaluate(proposal, today=pi._date(DAY, "day"))
            if ids_aside(got) != ids_aside(held):
                a, b = ids_aside(got), ids_aside(held)
                failures.append(f"the branch report differs from the held overlay's on {sorted(k for k in a if a[k] != b.get(k))}")
            gaps = sorted((g["rule"], g["id"]) for g in got["coverage"]["new_gaps"])
            if gaps != [("C1", "JRN-0014"), ("C1", "JRN-0015"), ("C2", "CAP-0009")]:
                failures.append(f"the branch report's new gaps are {gaps}")
            print(f"branch mode: {len(got['nodes'])} node(s), {len(got['links'])} link(s) read from {got['branch']['head'][:12]} "
                  f"against main; new gaps {gaps}")
        if digests(reg) != before or git(reg, "rev-parse", "HEAD") != head or git(reg, "status", "--porcelain"):
            failures.append("the register checkout changed")
    finally:
        shutil.rmtree(top, ignore_errors=True)
    for f in failures:
        print("FAIL " + f, file=sys.stderr)
    print("proposal branch mode: " + ("every check holds" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
