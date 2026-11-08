---
id: decision-0022
title: >-
  Changelog lines move to one fragment file per pull request after the 0.9.0
  cut, gathered into CHANGELOG.md by the release PR
date: '2026-11-08T16:23:00Z'
status: accepted
---
## Context

The convention (maintainer, 2026-11-04; CLAUDE.md, Releases): a pull request whose change an adopter would notice adds its line under `CHANGELOG.md`'s `## Unreleased` as it merges, with contract changes under their own heading. The release PR renames the section. `tests/test_release.py` admits one leading Unreleased section, and `release.yml` stays strict at tag time.

On 2026-11-08 five to six pull requests were open at once, and each added its line at the same spot. Every merge therefore sent every other open pull request back for a catch-up merge of `main` and a fresh CI run of about 20 minutes. #363, #364, #366, #369, #370 and #372 each needed one or two. The conflicts were in `CHANGELOG.md` alone, apart from one schema file.

## Options

- **(a) Fragments, after the 0.9.0 cut.** Each pull request writes `changelog.d/<task-id>.md` naming its heading; the release PR gathers them into the version's section and removes them.
- **(b) Fragments now**, before the freeze's last pull requests.
- **(c) No change.** Catch-up rounds continue.

## Decision

**Accepted: (a)**, on the maintainer's word (2026-11-08: "do it after 0.9.0"), to the coordinator's advice of (a), or (b) if the rounds kept slowing the 0.9 work. Drafted by the coordinator. task-0226 builds it once 0.9.0's release PR has merged. Until then, the 2026-11-04 convention holds.

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | Parallel pull requests all add at the same lines, so each merge conflicts every other open one |
| Users | The sessions that build in parallel; the coordinator who merges on green; the maintainer, waiting on the queue |
| Proposal | One fragment file per pull request under `changelog.d/`, gathered by the release PR in a fixed order |
| Unique value | Two pull requests never touch the same lines; a merge sends nothing back |
| Cost | A gathering tool; `test_release.py` and `release.yml` read fragments; CLAUDE.md's Releases paragraph |
| Risk | A forgotten fragment, or one under the wrong heading |

## Fit/gap

| Must satisfy | (a) | (b) | Evidence |
|---|---|---|---|
| Released sections never edited | Fit | Fit | CLAUDE.md, Releases |
| The release PR renames Unreleased to the version | Fit, by gathering | Fit, by gathering | `tests/test_release.py` |
| Contract changes under their own heading | Fit: a fragment names its heading | Fit | decision-0003 |
| No process change in the freeze's last pull requests | Fit | **Gap** | decision-0016 |
| An end to the catch-up rounds now | **Gap**: they continue until the cut | Fit | 2026-11-08's rounds |

## SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** no conflict rounds; each line stays with its pull request | **W:** Unreleased is not readable in one place until a release, short of a gathering preview |
| **External** | **O:** release notes are assembled by a tool | **T:** a forgotten fragment goes unnoticed, which a test refusing an unknown heading, and the release checklist, cover |

## Advice

(a), the drafter's recommendation:
- The freeze's last pull requests keep one convention end to end.
- The gathering tool is proven before the first release that uses it.
- The cost of waiting is the catch-up rounds until the cut, which merging on green as each pull request turns green keeps short.

## Consequences

- **task-0226** (m-8, low) builds it after 0.9.0's release PR merges. Once it lands, CLAUDE.md's Releases paragraph states the new convention and cites this decision.
- Until then nothing changes, and every pull request adds its line under `## Unreleased` as today.
