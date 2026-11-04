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
   are gate:lapsed findings.
Needs pyyaml (harness.yml installs it) to read the template.
"""
from __future__ import annotations

import json
import os
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


def main() -> None:
    if len(sys.argv) != 2:
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

    if job(env, "gate", KG_SCENARIO="S6") != 0:
        sys.exit("FAIL: the gate on S6's stage 1, want exit 0")
    if job(env, "trace-register", KG_FILES="reference_impl.py") != 0:
        sys.exit("FAIL: trace-register, want exit 0")
    [e] = json.loads((out / "ledger.json").read_text(encoding="utf-8"))["entries"]
    if (e["id"], e["app"]) != (f"derived:cargo-quote@{base}:reference_impl.py", "APP-0001"):
        sys.exit(f"FAIL: the ledger entry names the GitLab project and commit: {e}")
    if job(env, "gate", KG_SCENARIO="S6", KG_STAGE="2") != 1:
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
    print("GitLab include: the same command line as the action and the shell snippet; S6's change fails the merge request naming APP-0001; "
          f"KG_AS_OF reads both gates as of {LAPSE_DAY}")


if __name__ == "__main__":
    main()
