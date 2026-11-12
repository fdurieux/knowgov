"""The GitLab CI include (instance/ci/gitlab/knowgov.gitlab-ci.yml) run as GitLab would run its job,
by a shell, on the example instance, S6 as acceptance (task-0052). GitHub's composite action runs
for real in harness.yml; GitLab cannot run here, so this runs the template's own ``script:`` lines,
read from the file, with the variables GitLab sets (CI_COMMIT_SHA, CI_MERGE_REQUEST_DIFF_BASE_SHA,
CI_PROJECT_NAME) and the knowgov clone its ``before_script`` makes replaced by this checkout.

    python tools/check_ci_wrappers.py OUT_DIR

On the store KG_STORE names, persisted under OUT_DIR for rdflib:

0. ``gate`` on S1 as of the record's day: exit 0; with KG_AS_OF a day after 2027-08-07, the date S1's
   reviews lapse by: exit 1, BLOCKED, the report as of that day with its lapsed findings (task-0089).
1. ``gate`` on S6: exit 0. ``trace-register`` of the reference code: exit 0, one ledger entry.
2. ``gate`` on S6 with KG_STAGE=2: exit 1 (the change, BLOCKED), and the template's KG_ANNOTATE
   leaves gl-code-quality-report.json, GitLab's code-quality report (task-0083), in the project
   directory, with no KG_REPORT set: the suspect derived output a blocker, the stale statements major
   and info, each fingerprint distinct, every path relative to the project directory.
3. ``trace-check`` with the merge request's diff base: the edit is drift, and the registered build is
   suspect, a blocker naming APP-0001: exit 1, the JSON report valid against its schema, and the
   code-quality report puts the suspect build on reference_impl.py under the instance. With KG_AS_OF,
   the same check reads the task's gate as of that day: the report's gate names it, and its lapses
   are gate:lapsed findings. ``trace-register`` with KG_AS_OF records that day in its ledger entry, the
   record's day without it (task-0093).
4. ``preload`` with the merge request's diff base, on a broken sequence diagram committed after it:
   exit 1, KG_REPORT the pre-load report, valid against its schema, on that file alone, and the
   code-quality report puts SEQ001 on the diagram's file and line (task-0106).
5. ``trace-check`` on a merge request adding ``módulo.py``, then ``new module.py``, then ``glob[1]*.py``, through
   the GitLab template's script and the GitHub action's gate step: each reports the one path, as itself (task-0267);
   before, git's quoting and the shell's word-splitting read "no code changed" (exit 0) and "module.py".
6. ``KG_ANNOTATE=,,`` and ``nope:x.json`` exit 2 before the core command, naming KG_ANNOTATE and its four formats; an
   annotation file it cannot write is a warning beside the command's exit, no traceback; a base of
   ``--output=FILE`` exits 2 naming KG_BASE and git writes nothing (task-0267), each through both wrappers.
7. ``gate`` on S1 with KG_REGISTER unset reads the instance's own register, ``<instance>/register``: its review months
   set to 1, BLOCKED with lapses where the public register reads PROCEED; KG_REGISTER naming the public one is kept,
   PROCEED; the instance's register missing, exit 2 naming KG_REGISTER (task-0334), each through both wrappers.
Needs pyyaml (harness.yml installs it) to read the template.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import cadence  # noqa: E402
import example_instance  # noqa: E402
import schema_check  # noqa: E402

TEMPLATE = ROOT / "instance" / "ci" / "gitlab" / "knowgov.gitlab-ci.yml"
LAPSE_DAY = "2027-08-08"   # a day after 2027-08-07, when S1's review verifications have lapsed (decision-0005)
CLONE = "/tmp/knowgov"   # where the template's before_script clones knowgov


def git(inst: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(inst), *args], check=True, capture_output=True, text=True).stdout.strip()


def job(env: dict, gate: str, **kg: str) -> int:
    """The template's job: its variables, then its script lines in one shell, as GitLab runs them."""
    tpl = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))[".knowgov-gate"]
    script = "\n".join(line.replace(CLONE, str(ROOT)) for line in tpl["script"])
    e = {**env, **{k: str(v) for k, v in tpl["variables"].items()}, "KG_GATE": gate, **kg}
    p = subprocess.run(["sh", "-ec", script], cwd=env["CI_PROJECT_DIR"], env=e, capture_output=True, text=True)
    print(f"exit {p.returncode}: GitLab job, KG_GATE={gate} {' '.join(f'{k}={v}' for k, v in kg.items())}\n    "
          + "\n    ".join((p.stdout + p.stderr).strip().splitlines()[-6:]))
    return p.returncode


ACTION = ROOT / "instance" / "ci" / "github" / "action.yml"


def action(env: dict, gate: str, out: Path, **inputs: str) -> tuple[int, str]:
    """The GitHub action's gate step: its run: lines in one shell, its inputs mapped to the KG_* its env: names,
    from the action's own checkout (GITHUB_ACTION_PATH), on a pull request with base CI_MERGE_REQUEST_DIFF_BASE_SHA."""
    step = yaml.safe_load(ACTION.read_text(encoding="utf-8"))["runs"]["steps"][0]
    e = {**env, "GITHUB_ACTION_PATH": str(ACTION.parent), "GITHUB_OUTPUT": str(out / "github-output"),
         "GITHUB_STEP_SUMMARY": str(out / "github-summary.md"), "RUNNER_TEMP": str(out),
         "KG_GATE": gate, "KG_INSTANCE": "instance", "KG_COMMIT": env["CI_COMMIT_SHA"], "KG_BASE": env["CI_MERGE_REQUEST_DIFF_BASE_SHA"],
         "KG_FAIL_ON": "", "KG_SUBJECT_IN": "", "KG_SCENARIO": "", "KG_TASK": "codegen", "KG_STAGE": "", "KG_AS_OF": "",
         "KG_LEDGER": str(Path(env["KG_LEDGER"]).relative_to(out)), "KG_FILES": "", "KG_REPORT": "", "KG_CODE_REPO": "cargo-quote",
         "KNOWGOV_PUBLISH": "false", "KNOWGOV_ANNOTATE": "false", "KNOWGOV_SARIF": "false", **inputs}
    p = subprocess.run(["sh", "-ec", step["run"]], cwd=out, env=e, capture_output=True, text=True)
    print(f"exit {p.returncode}: GitHub action, gate {gate} {' '.join(f'{k}={v}' for k, v in inputs.items())}\n    "
          + "\n    ".join((p.stdout + p.stderr).strip().splitlines()[-4:]))
    return p.returncode, p.stdout + p.stderr


def code_quality(out: Path) -> list[dict]:
    """The code-quality report the job left, checked for what GitLab requires of each issue."""
    f = out / "gl-code-quality-report.json"
    if not f.exists():
        sys.exit("FAIL: the job left no gl-code-quality-report.json")
    issues = json.loads(f.read_text(encoding="utf-8"))
    for i in issues:
        if not (i["description"] and i["check_name"] and i["severity"] in ("info", "minor", "major", "critical", "blocker")
                and isinstance(i["location"]["lines"]["begin"], int) and (out / i["location"]["path"]).is_file()):
            sys.exit(f"FAIL: a code-quality issue GitLab would refuse or could not place: {i}")
    if len({i["fingerprint"] for i in issues}) != len(issues):
        sys.exit("FAIL: code-quality fingerprints repeat")
    f.unlink()
    return issues


def changed_paths(env: dict, inst: Path, root: Path, out: Path) -> None:
    """task-0267: a changed path with a non-ASCII character, then one with a space, reaches trace-check as itself,
    through both wrappers: git lists it NUL-separated and unquoted, and nothing splits it on whitespace."""
    for name in ("módulo.py", "new module.py", "glob[1]*.py"):
        before = git(inst, "rev-parse", "HEAD")
        (root / name).write_text("# a module the merge request adds\n", encoding="utf-8")
        git(inst, "add", "-A")
        git(inst, "-c", "user.name=ci", "-c", "user.email=ci@example.invalid", "commit", "-qm", f"add {name}")
        env.update(CI_COMMIT_SHA=git(inst, "rev-parse", "HEAD"), CI_MERGE_REQUEST_DIFF_BASE_SHA=before)
        for wrapper in ("GitLab", "GitHub"):
            checked_as_itself(env, out, wrapper, name)


def refusals(env: dict, out: Path) -> None:
    """task-0267: a KG_ANNOTATE list the script cannot follow, and a base that is an option, exit 2 before the core
    command, through both wrappers; a file the annotator cannot write stays a warning beside the command's exit."""
    (out / "sub dir").write_text("a file, so nothing can be written under it\n", encoding="utf-8")
    for spec in (",,", "nope:x.json"):
        for wrapper in ("GitLab", "GitHub"):
            code, text = run_wrapper(env, out, wrapper, "trace-check", KG_ANNOTATE=spec)
            if code != 2 or "KG_ANNOTATE" not in text or "github, summary, gitlab or sarif" not in text or "knowgov trace" in text:
                sys.exit(f"FAIL: {wrapper}: KG_ANNOTATE={spec!r}: want exit 2 before the core command naming KG_ANNOTATE and its "
                         f"four formats; exit {code}: {text[-400:]}")
            print(f"    {wrapper}: KG_ANNOTATE={spec!r} refused, exit 2")
    code, text = run_wrapper(env, out, "GitLab", "trace-check", KG_ANNOTATE=f"gitlab:{out}/sub dir/x.json")
    if code == 2 or "annotate gitlab failed" not in text or "Traceback" in text:
        sys.exit(f"FAIL: an unwritable annotation file: want the command's exit and a warning, no traceback; exit {code}: {text[-600:]}")
    print(f"    an annotation file it cannot write: a warning, the command's exit {code}")
    base_refused(env, out)


def base_refused(env: dict, out: Path) -> None:
    """task-0267 (N2): a merge request base that is an option exits 2 naming KG_BASE, and git writes nothing."""
    canary = out / "canary"
    for wrapper in ("GitLab", "GitHub"):
        code, text = run_wrapper(dict(env, CI_MERGE_REQUEST_DIFF_BASE_SHA=f"--output={canary}"), out, wrapper, "trace-check")
        if code != 2 or canary.exists() or "KG_BASE" not in text:
            sys.exit(f"FAIL: {wrapper}: a base that is an option: want exit 2 naming KG_BASE and no file written; exit {code}, "
                     f"{canary} {'written' if canary.exists() else 'absent'}: {text[-400:]}")
        print(f"    {wrapper}: a base of --output=... refused, exit 2, nothing written")


def own_register(env: dict, inst: Path, out: Path) -> None:
    """task-0334 (decision-0039 §3.1): with KG_REGISTER unset, both wrappers read the instance's own register,
    <instance>/register. Its review months set to 1, S1 as of the record's day is BLOCKED with lapses (the public
    register's 6 and 12 read PROCEED); KG_REGISTER naming the public one is kept, PROCEED; the instance's register
    missing, exit 2 naming KG_REGISTER. The register is restored after."""
    env = {k: v for k, v in env.items() if k != "KG_REGISTER"}
    life = inst / "register" / "metamodel" / "lifecycle.toml"
    before = life.read_text(encoding="utf-8")
    life.write_text(re.sub(r"months = \d+", "months = 1", before), encoding="utf-8")
    try:
        for wrapper in ("GitLab", "GitHub"):
            _reads(env, out, wrapper, None, 1, "BLOCKED")
            _reads({**env, "KG_REGISTER": str(ROOT / "demo" / "register")}, out, wrapper, "public", 0, "PROCEED")
        _missing(env, inst, out)
    finally:
        life.write_text(before, encoding="utf-8")


def _reads(env: dict, out: Path, wrapper: str, named: str | None, want: int, verdict: str) -> None:
    report = out / f"gate-own-register-{wrapper}-{want}.json"
    code, text = run_wrapper(env, out, wrapper, "gate", KG_SCENARIO="S1", KG_ANNOTATE="", KG_REPORT=report.relative_to(out).as_posix())
    rep = json.loads(report.read_text(encoding="utf-8")) if report.exists() else {}
    lapses = len(rep.get("lapsed") or [])
    if code != want or rep.get("verdict") != verdict or (lapses > 0) != (want == 1):
        sys.exit(f"FAIL: {wrapper}: gate on S1, KG_REGISTER {named or 'unset'}: want exit {want}, {verdict}, on the "
                 f"{named or 'instance'} register's months; exit {code} {rep.get('verdict')}: {text[-400:]}")
    print(f"    {wrapper}: KG_REGISTER {named or 'unset, the instance'} register: S1 {verdict}, {lapses} lapse(s)")


def _missing(env: dict, inst: Path, out: Path) -> None:
    reg = inst / "register"
    reg.rename(inst / "register-away")
    try:
        for wrapper in ("GitLab", "GitHub"):
            code, text = run_wrapper(env, out, wrapper, "gate", KG_SCENARIO="S1", KG_ANNOTATE="")
            if code != 2 or f"KG_REGISTER {reg.as_posix()} is not a readable register" not in text:
                sys.exit(f"FAIL: {wrapper}: no <instance>/register: want exit 2 naming KG_REGISTER and the path; exit {code}: {text[-400:]}")
            print(f"    {wrapper}: no <instance>/register, exit 2 naming KG_REGISTER")
    finally:
        (inst / "register-away").rename(reg)


def run_wrapper(env: dict, out: Path, wrapper: str, gate: str, **kg: str) -> tuple[int, str]:
    """One gate through the GitLab template's script or the GitHub action's step, with its output."""
    if wrapper == "GitHub":
        inputs = {k: v for k, v in kg.items() if k != "KG_ANNOTATE"}
        if "KG_ANNOTATE" in kg:   # the action's own input is true or false; the KG_* reach the script as the step sets them
            return action({**env, "KG_ANNOTATE": kg["KG_ANNOTATE"]}, gate, out, **inputs)
        return action(env, gate, out, **inputs)
    tpl = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))[".knowgov-gate"]
    script = "\n".join(line.replace(CLONE, str(ROOT)) for line in tpl["script"])
    e = {**env, **{k: str(v) for k, v in tpl["variables"].items()}, "KG_GATE": gate, **kg}
    p = subprocess.run(["sh", "-ec", script], cwd=env["CI_PROJECT_DIR"], env=e, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def checked_as_itself(env: dict, out: Path, wrapper: str, name: str) -> None:
    report = out / f"trace-check-{wrapper}-{len(name)}.json"
    if wrapper == "GitLab":
        code = job(env, "trace-check", KG_ANNOTATE="", KG_REPORT=str(report))
    else:
        code, _ = action(env, "trace-check", out, KG_REPORT=str(report.relative_to(out)))
    if code == 2 or not report.exists():
        sys.exit(f"FAIL: {wrapper}: trace-check on a merge request adding {name!r} wrote no report (exit {code}); "
                 "a changed path it cannot read is not 'no code changed'")
    got = json.loads(report.read_text(encoding="utf-8"))["changed"]
    if got != [name]:
        sys.exit(f"FAIL: {wrapper}: trace-check checked {got} for a merge request adding {name!r}")
    print(f"    {wrapper}: trace-check reads the changed path {name!r} as itself (exit {code})")


def execution_named_then_reverted(inst: Path, root: Path, base: str) -> None:
    """task-0320 (decision-0038 N-b): the merge request's edit to the reference implementation leaves the execution
    verification unattested, and the layout check through the instance names it, an error citing decision-0038. The
    edit is then reverted in a commit of its own, so the pre-load steps after it test the layout they were written for."""
    rel = (root / "reference_impl.py").relative_to(inst).as_posix()
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "check_instance.py"), str(inst)], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    named = [ln for ln in (p.stdout + p.stderr).splitlines() if "[verification] execution" in ln and "reference_impl.py" in ln]
    if p.returncode != 1 or len(named) != 1 or "decision-0038" not in named[0]:
        sys.exit(f"FAIL: the edited reference implementation should be one layout error under [verification] execution "
                 f"citing decision-0038: exit {p.returncode}\n{(p.stdout + p.stderr)[-1500:]}")
    print(f"    layout: {named[0].strip()[:160]}")
    (inst / rel).write_bytes(subprocess.run(["git", "-C", str(inst), "show", f"{base}:{rel}"], capture_output=True, check=True).stdout)
    git(inst, "-c", "user.name=ci", "-c", "user.email=ci@example.invalid", "commit", "-qam", "revert the edit")
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "check_instance.py"), str(inst)], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if "[verification] execution" in p.stdout + p.stderr:
        sys.exit(f"FAIL: reverted, the execution should be attested again: {(p.stdout + p.stderr)[-800:]}")
    print("    layout: reverted, the execution attested again")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):   # task-0314 B-X7: --help is not an output directory
        sys.exit(__doc__)
    out = Path(sys.argv[1]).resolve()
    if out.exists() and any(out.iterdir()):
        sys.exit(f"FAIL: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    inst = example_instance.build(out / "instance")
    git(inst, "init", "-q", "-b", "main")
    git(inst, "add", "-A")
    git(inst, "-c", "user.name=ci", "-c", "user.email=ci@example.invalid", "commit", "-qm", "base")
    base = git(inst, "rev-parse", "HEAD")
    # the record's day, the wall clock refused (task-0075): KG_TODAY reaches the gate through the job's environment
    env = cadence.pin_record(dict(os.environ, CI_PROJECT_DIR=str(out), CI_PROJECT_NAME="cargo-quote", CI_COMMIT_SHA=base,
                                  KG_RDFLIB_FILE=str(out / "store.ttl"), KG_LEDGER=str(out / "ledger.json"), PYTHONDONTWRITEBYTECODE="1"))

    if job(env, "gate", KG_SCENARIO="S1", KG_ANNOTATE="", KG_REPORT=str(out / "gate-s1.json")) != 0:
        sys.exit("FAIL: the gate on S1 as of the record's day, want exit 0")
    if job(env, "gate", KG_SCENARIO="S1", KG_ANNOTATE="", KG_AS_OF=LAPSE_DAY, KG_REPORT=str(out / "gate-s1-lapsed.json")) != 1:
        sys.exit(f"FAIL: the gate on S1 as of {LAPSE_DAY}, want exit 1")
    rep = json.loads((out / "gate-s1-lapsed.json").read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("gate-report"))
    lapsed = [f for f in rep["findings"] if f["kind"] == "lapsed"]
    if errs or (rep["verdict"], rep["as_of"]) != ("BLOCKED", LAPSE_DAY) or not lapsed or not rep["lapsed"]:
        sys.exit(f"FAIL: want S1 BLOCKED as of {LAPSE_DAY} with lapsed findings: {errs[:3]} {rep['verdict']} {rep['as_of']} {len(lapsed)}")
    print(f"    KG_AS_OF={LAPSE_DAY}: {rep['verdict']}, {len(lapsed)} lapsed finding(s)")

    if job(env, "gate", KG_SCENARIO="S6", KG_PUBLISH="1") != 0:   # trace-register reads this load (decision-0017)
        sys.exit("FAIL: the gate on S6's stage 1, want exit 0")
    if job(env, "trace-register", KG_FILES="reference_impl.py") != 0:
        sys.exit("FAIL: trace-register, want exit 0")
    [e] = json.loads((out / "ledger.json").read_text(encoding="utf-8"))["entries"]
    if (e["id"], e["app"], e.get("as_of")) != (f"derived:cargo-quote@{base}:reference_impl.py", "APP-0001", env["KG_TODAY"]):
        sys.exit(f"FAIL: the ledger entry names the GitLab project and commit: {e}")
    if job(env, "gate", KG_SCENARIO="S6", KG_STAGE="2", KG_PUBLISH="1") != 1:   # trace-check reads this load
        sys.exit("FAIL: the gate on S6's change, want exit 1")
    cq = sorted((i["check_name"], i["severity"]) for i in code_quality(out))
    want = {("knowgov-suspect_derived", "blocker"), ("knowgov-stale", "major"), ("knowgov-stale", "info"), ("knowgov-key", "blocker")}
    if not want <= set(cq):
        sys.exit(f"FAIL: S6's change in the code-quality report, want {sorted(want)}: {cq}")
    print(f"    code quality: {len(cq)} issue(s), " + ", ".join(sorted({f'{c} {s}' for c, s in cq})))

    root = inst / "subjects" / "cargo_quote" / "vendor" / "stack_experiment" / "cargo_quote"
    (root / "reference_impl.py").write_text((root / "reference_impl.py").read_text(encoding="utf-8") + "\n# an edit in the merge request\n", encoding="utf-8")
    git(inst, "-c", "user.name=ci", "-c", "user.email=ci@example.invalid", "commit", "-qam", "edit")
    env.update(CI_COMMIT_SHA=git(inst, "rev-parse", "HEAD"), CI_MERGE_REQUEST_DIFF_BASE_SHA=base)
    if job(env, "trace-check", KG_REPORT=str(out / "trace-check.json")) != 1:
        sys.exit("FAIL: trace-check after the change, want exit 1")
    rep = json.loads((out / "trace-check.json").read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("trace-report"))
    kinds = sorted((f["kind"], f["app"]) for f in rep["findings"] if f["kind"] in ("suspect", "drift"))
    if errs or rep["changed"] != ["reference_impl.py"] or kinds != [("drift", "APP-0001"), ("suspect", "APP-0001")]:
        sys.exit(f"FAIL: want the changed path from the diff base, drift and suspect on APP-0001: {errs[:3]}\n{json.dumps(rep, indent=1)[:3000]}")
    placed = {(i["check_name"], i["severity"], i["location"]["path"]) for i in code_quality(out)}
    code = (root / "reference_impl.py").relative_to(out).as_posix()
    if not {("knowgov-suspect", "blocker", code), ("knowgov-drift", "minor", code)} <= placed:
        sys.exit(f"FAIL: want the suspect build and its drift on {code} in the code-quality report: {sorted(placed)}")
    print(f"    code quality: suspect (blocker) and drift (minor) on {code}")
    on = json.loads((out / "trace-check.json").read_text(encoding="utf-8"))["gate"].get("as_of")
    if job(env, "trace-check", KG_ANNOTATE="", KG_AS_OF=LAPSE_DAY, KG_REPORT=str(out / "trace-check-lapsed.json")) != 1:
        sys.exit(f"FAIL: trace-check as of {LAPSE_DAY}, want exit 1")
    rep = json.loads((out / "trace-check-lapsed.json").read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("trace-report"))
    lapsed = [f for f in rep["findings"] if f["kind"] == "gate:lapsed"]
    if errs or on != env["KG_TODAY"] or rep["gate"].get("as_of") != LAPSE_DAY or not lapsed:
        sys.exit(f"FAIL: want trace-check's gate as of {LAPSE_DAY} (unset: {env['KG_TODAY']}, read {on}) with gate:lapsed findings: "
                 f"{errs[:3]} {rep['gate']} {len(lapsed)}")
    print(f"    trace-check KG_AS_OF={LAPSE_DAY}: gate {rep['gate']['verdict']} as of {rep['gate']['as_of']}, {len(lapsed)} gate:lapsed finding(s)")
    if job(env, "trace-register", KG_FILES="reference_impl.py", KG_AS_OF=LAPSE_DAY, KG_LEDGER=str(out / "ledger-lapsed.json")) != 0:
        sys.exit(f"FAIL: trace-register as of {LAPSE_DAY}, want exit 0")
    [e] = json.loads((out / "ledger-lapsed.json").read_text(encoding="utf-8"))["entries"]
    if e.get("as_of") != LAPSE_DAY:
        sys.exit(f"FAIL: trace-register with KG_AS_OF={LAPSE_DAY}: the ledger entry records {e.get('as_of')}")
    print(f"    trace-register KG_AS_OF={LAPSE_DAY}: the ledger entry as of {e['as_of']}")
    execution_named_then_reverted(inst, root, base)   # task-0320, decision-0038 N-b

    # task-0106: the pre-load gate writes its report too, so a broken document reaches the code-quality widget
    # task-0115: a document no subject names, committed before the diff base, is a layout problem the report carries
    orphan = inst / "artefacts" / "user-stories" / "orphan.md"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("# Orphan\n\nNo subject names this story.\n", encoding="utf-8")
    git(inst, "add", "-A")
    git(inst, "-c", "user.name=ci", "-c", "user.email=ci@example.invalid", "commit", "-qm", "an unread story")
    puml = inst / "artefacts" / "plantuml-models" / "broken.puml"
    puml.write_text("@startuml\nparticipant A\nA -> B : hi\n@enduml\n", encoding="utf-8")
    head = git(inst, "rev-parse", "HEAD")
    git(inst, "add", "-A")
    git(inst, "-c", "user.name=ci", "-c", "user.email=ci@example.invalid", "commit", "-qm", "a broken diagram")
    env.update(CI_COMMIT_SHA=git(inst, "rev-parse", "HEAD"), CI_MERGE_REQUEST_DIFF_BASE_SHA=head)
    if job(env, "preload", KG_REPORT=str(out / "preload.json")) != 1:
        sys.exit("FAIL: preload on the broken diagram, want exit 1")
    rep = json.loads((out / "preload.json").read_text(encoding="utf-8"))
    errs = schema_check.validate(rep, schema_check.load("preload-report"))
    issues = code_quality(out)
    where = puml.relative_to(out).as_posix()
    on_it = [i for i in issues if i["location"]["path"] == where and i["check_name"] == "knowgov-preload:SEQ001"]
    if errs or [f["file"] for f in rep["files"]] != ["artefacts/plantuml-models/broken.puml"] or not on_it or on_it[0]["location"]["lines"]["begin"] < 1:
        sys.exit(f"FAIL: want the pre-load report on the changed diagram and SEQ001 on {where} in the code-quality report: {errs[:3]} {issues}")
    print(f"    preload: SEQ001 ({on_it[0]['severity']}) on {where} line {on_it[0]['location']['lines']['begin']}")
    lay, at = rep.get("layout") or {}, orphan.relative_to(out).as_posix()
    mine = {i["check_name"]: i["severity"] for i in issues if i["location"]["path"] == at}
    if rep["exit_code"] != 1 or lay.get("holds") is not True or lay.get("exit_code") != 0 or \
            mine != {"knowgov-layout:absent": "minor", "knowgov-layout:unread": "info"}:
        sys.exit(f"FAIL: want the unread story's layout problems in the report and the code-quality report, the exit the lint's: "
                 f"{rep['exit_code']} {lay} {mine}")
    print(f"    preload: the layout's problems on {at} as code quality, {sorted(mine)}; the exit still the lint's ({rep['exit_code']})")
    changed_paths(env, inst, root, out)   # task-0267
    refusals(env, out)   # task-0267
    own_register(env, inst, out)   # task-0334

    print("GitLab include: the same command line as the action and the shell snippet; S6's change fails the merge request naming APP-0001; "
          f"KG_AS_OF reads both gates and the registration as of {LAPSE_DAY}")


if __name__ == "__main__":
    import _outcomes   # task-0159: the outcome recorded when KG_OUTCOMES names a file
    sys.exit(_outcomes.run(main))
