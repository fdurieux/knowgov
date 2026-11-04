---
id: TASK-0096
title: An optional token on the page's POST /api/run
status: Done
assignee:
  - '@claude'
created_date: '2026-11-04T07:29:00Z'
updated_date: '2026-11-04T08:23:00Z'
labels:
  - security
  - page
milestone: m-8
dependencies:
  - TASK-0090
priority: medium
ordinal: 99000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
docs/security.md still names gap 1: the page has no login, and POST /api/run can start a run that calls the model. task-0090 binds the stack to 127.0.0.1 by default; on a wider bind a token, as KG_MCP_TOKEN does for MCP, would close the run endpoint.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 With KG_PAGE_TOKEN set, POST /api/run and every state-changing endpoint require it as a bearer token; on a wider bind without it the run endpoints refuse
- [x] #2 docs/security.md's gap list, the demo README and test_security move with the fix; the stack job passes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. write_guard in demo/app/server.py before every POST: refuse a foreign Origin; with KG_PAGE_TOKEN require it as a bearer token (hmac.compare_digest, 401); without it refuse (403) when the page reaches beyond this machine (KG_BIND, passed by compose, else KG_PAGE_LISTEN).
2. Server listens on KG_PAGE_LISTEN (127.0.0.1; the image sets 0.0.0.0); compose passes KG_BIND and KG_PAGE_TOKEN to the app.
3. /api/scenarios carries writes {token_required, refused}; index.html asks for the token only then, keeps it in sessionStorage, sends it on POSTs, greys run/project buttons with the reason.
4. Reads stay open (the demo is meant to be shown); gap 1 narrowed to the reads.
5. docs/security.md rows, matrix, gap 1, practices; demo README and guide; test_security over HTTP on loopback.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Every POST is guarded, not only /api/run: /api/register/project writes the store too. A foreign Origin is refused on any bind (a simple cross-site POST needs no preflight). GETs stay open: nothing in them changes state, and the page is shown by design; gap 1 now names the open reads and the token in clear over plain HTTP. The released v0.2.0 image predates the guard; the README says the token works from a build of this checkout or the next release. Proven: tests 287+ plain and under jef_data_load; Chromium against three local servers on the rdflib store (token required: greyed, wrong token 401 in the banner, right token S1 finished; wide without token: refused with the reason; localhost: no box, buttons enabled).

CI on fcdde82: tests, rdflib and stack green (stack ran the localhost POSTs to /api/run and /api/register/project with no token); publish skipped.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page's writes are closed beyond this machine. demo/app/server.py write_guard runs before every POST (a run, the register's projection): a foreign Origin is refused on any bind; with KG_PAGE_TOKEN set the request must carry it as a bearer token (401); without it, a page published beyond this machine (KG_BIND, now passed by compose, else KG_PAGE_LISTEN, which defaults to 127.0.0.1 and is 0.0.0.0 in the image) refuses with 403 naming the variable. Reads stay open, by design; gap 1 in docs/security.md is narrowed to them and to the token in clear over plain HTTP. The page asks for the token only when the server requires it, keeps it in sessionStorage, sends it on POSTs only. docs/security.md (data flow, matrix, evidence, gap 1, practices), demo README (adopter register), guide limits and tests/test_security.py moved with it. Verified: 287/287 plain and under jef_data_load; Chromium against three local servers; CI green incl. stack. Limit: the released v0.2.0 image predates the guard; it takes effect from a local build or the next release.
<!-- SECTION:FINAL_SUMMARY:END -->
