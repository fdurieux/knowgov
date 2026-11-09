# The advisory SonarQube scan

Maintainer register. task-0250, from doc-0033's answer (2026-11-09): SonarQube is not a gate. One advisory
scan per minor release, with its debt delta against the previous release, beside the everyday complexity
ratchet in the test suite (task-0251).

## Cadence

- **Every minor release.** `.github/workflows/quality.yml` runs on the `v*` tag the Release creates, as
  `release.yml` does. Patch releases scan too; their delta is small. The first scan, v0.9.0, is the frozen
  baseline.
- **On demand.** A `workflow_dispatch` takes a `ref`, so a past tag can be scanned with today's tooling: the
  workflow checks out the ref to scan, and its own commit outside that checkout for `tools/quality/` and the measurer (`coverage_stdlib.py --root`), so the suite's every-file check sees one tree.
- **On its own pull requests.** A pull request touching the workflow, `tools/quality/` or
  `tools/coverage_stdlib.py` runs it, so a change to the scan proves one complete run.

It is advisory, never a gate: never a required check and never a cut condition. It fails only when the scan cannot run: the server
does not come up, the profile does not restore, the scanner or the server's processing fails, or the export
cannot read the results. A red suite under the measurer, a missing previous scan and the delta itself are
warnings or advice.

## What it pins

- **SonarQube Community Build** as a service container, by tag and digest, published on loopback. The
  admin password and a user token are minted on the server for the run and masked; no repository secret.
- **The scanner CLI** from SonarSource's release archive, by version and the archive's published SHA-256.
- **The Python profile**, `tools/quality/knowgov-python.xml`: SonarQube's *Sonar way comprehensive* without
  `python:S9073` (split composite assertions) and `python:S8997` (the pytest `monkeypatch` fixture), which
  fight the stdlib runner (1,496 and 162 findings at main 6d27961). Bugs, vulnerabilities, hotspots,
  cognitive complexity (`python:S3776`, threshold 15) and duplication stay. The other languages keep the
  server's defaults. To change the profile, edit it on a local server, back it up with
  `/api/qualityprofiles/backup?language=py&qualityProfile=knowgov`, and commit the file.
- **The analysis settings**, `tools/quality/sonar-project.properties`: the sources and tests, and the
  exclusions (the vendored register, model and subject bytes, the records and probes, fixtures, the backlog
  and docs, `runs/` and `outcomes/`). `demo/Dockerfile.dockerignore` is BuildKit's ignore file, so the Docker
  analyser reads `**/Dockerfile` only.

## Coverage

`tools/coverage_stdlib.py --lines` measures the scanned ref's suite in-process, as `tests.yml` does, with each
module's statement and branch lines. `tools/quality/coverage_xml.py` turns that into SonarQube's generic
coverage format. The denominator stays the measurer's: the counted modules, and no claim for code that runs
only in a child process. The run's `line_coverage` equals the measurer's statement percentage and
`branch_coverage` its branch percentage. No dependency is added.

## Results and the debt delta

`tools/quality/report.py export` writes `issues.json`, `hotspots.json`, `measures.json` and `meta.json`, kept
with `coverage.json` as the artefact `quality-<tag>` for 90 days. `report.py delta` writes the job summary:

- issues by type and severity, against the previous release;
- the issues new and gone since it, known by rule, file and message, so a line moving above them does not
  make them new;
- the cognitive-complexity hotspots;
- the measures: size, debt, complexity, duplication and coverage.

The previous release is the tag before the scanned one, or the latest tag for any other ref. Its artefact
expires after 90 days. If it has expired, dispatch the workflow with that tag first, then the new one.

## Accepting a finding

A finding is accepted with its reason, in one of two places:

- **In the code, for one line:** `# NOSONAR(S5332) <why>`, naming the rule, beside any existing `noqa`. This
  is the form SonarQube's Python analyser reads. `# NOSONAR: <why>` suppresses nothing and is itself flagged
  (`python:S7632`; tried on 26.11).
- **In `tools/quality/baseline.json`, for findings of one rule in one file:** an entry with `rule`, `path`,
  `count` and `reason`. It accepts at most `count` of them, so a further finding in the same file is open
  again. The delta lists the accepted findings apart from the open ones.

A finding a task will fix is not accepted. It stays open until the fix lands, so the delta shows it closing.
For example, the image's root user is task-0248, and the regular expressions are task-0249.
