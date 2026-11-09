---
id: decision-0030
title: >-
  The page's HTTP API at 1.0 is the four routes demo/README.md documents; every
  other route serves the page and may change (decision-0016 point 3)
date: '2026-11-08T23:45:00Z'
status: proposed
---
## Context

decision-0016 point 3 makes "the page's HTTP API, as `demo/README.md` documents it" a 1.0 contract.

At `main` `4c7fcb0`, `demo/README.md` documents four routes:
- `POST /api/run`, with the `Authorization` header and `as_of`;
- `GET /api/scenarios`, with `arms_enabled`, `execution`, `model_rows` and `key_check`;
- `GET /api/subjects`;
- `POST /api/models/check`.

`demo/app/server.py` serves about seventeen. The others are:
- `/api/results/<scenario>`, `/api/run` (GET), `/api/runs` and `/api/store`;
- `/api/register`, with `footprint`, `ref`, `impact` and `project`;
- `/api/gaps/<scenario>`, `/api/cypher` and `/api/cascade/…`.

`docs/security.md` describes how `/api/store` and `/api/gaps` behave under load (`503`, `busy`). It describes them; it does not invite a script to use them.

`CHANGELOG.md` Unreleased files `GET /api/store`'s new `browser_connect` field under "Contract changes" (task-0235). By point 3, an undocumented route is not a contract, so either the changelog over-claims or the guide under-documents.

Raised by the reconciliation of the v1.0 scope handover against `main` `4c7fcb0` (its D4; A02).

*Drafted by the coordinating session during the maintainer's overnight delegation (2026-11-08) and **parked for the maintainer**: it fixes the membership of a contract decision-0016 point 3 named, as decision-0027 did for settings on the maintainer's word. The advice below is the drafter's recommendation; the maintainer's word decides.*

## Options

- **(a) The four documented routes.** Their fields are as the guide documents them. The guide says every other route serves the page and may change in any release.
- **(b) (a), plus a run's status and results** (`GET /api/run`, `GET /api/runs`, `GET /api/results/<scenario>`), documented as contracts.
- **(c) Every route.**

## Decision (proposed)

**(a)**, the drafter's recommendation. This is decision-0016 point 3 read literally, with decision-0027's accepted principle applied to routes: a route is a contract by being documented for an adopter, and the rest are the page's own.
- `demo/README.md` gains one sentence naming the four as the page's HTTP API at 1.0, and saying that every other route serves the page and may change in any release.
- A test holds the guide's list to the routes `server.py` serves, so none is invented and none is named that does not exist.
- The CHANGELOG's `browser_connect` line moves from "Contract changes" to "Changes".

## Opportunity canvas

| Element | Content |
|---|---|
| Problem | The contract's extent is ambiguous. The changelog already treats an undocumented route as one |
| Users | A script driving the page, such as the lighthouse's CI starting a deterministic run; the page's own development |
| Proposal | (a) |
| Unique value | A closed, testable list. The page's views stay free to change |
| Cost | A sentence, a test (task-0181's build) and one changelog line moved |
| Risk | A pilot that scripts the page beyond the four would need a 0.10.0 to widen the contract |

## Fit/gap

| Must satisfy | (a) | (b) | (c) |
|---|---|---|---|
| decision-0016 point 3, as written | Fit | Fit, once documented | Fit, once documented |
| decision-0027's principle (documented means contract) | Fit | Fit | Fit |
| The page stays free to change its views | Fit | **Gap**: `/api/results` is the page's view model, about 392 KB for S6 | **Gap** |
| A pilot's scripting route | Fit: the CLI, the MCP servers and `instance/ci/` are the contracts built for scripts | Fit | Fit |
| The changelog classifies correctly | Fit, once moved | Fit | Fit |

## SWOT (of a)

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** a small, closed, tested surface | **W:** a script cannot follow a run to its end over a contracted route |
| **External** | **O:** an OpenAPI file for the four later | **T:** a pilot scripting the page forces 0.10.0 |

## Advice

(a). Freezing the page's view model would tie every later change to its panels to a minor release. The scripting routes a pilot needs already exist as contracts (the gate command, the MCP servers, `instance/ci/`). If the maintainer wants a script to follow a run over HTTP, `GET /api/run`'s status joins before the cut. That is the one extension worth weighing, and it is named here so it is not lost. It is parked because a contract's membership is the maintainer's to set, as it was for settings.

## Consequences

- **If accepted**, task-0181's build writes the sentence, the test and the changelog move (its AC #6). The build is prepared overnight, and its pull request waits for the maintainer's word.
- **doc-0028**: A02's inventory question closes when this record is accepted.
