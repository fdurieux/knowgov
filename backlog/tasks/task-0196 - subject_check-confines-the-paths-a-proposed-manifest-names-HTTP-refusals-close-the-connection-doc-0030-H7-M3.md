---
id: TASK-0196
title: >-
  subject_check confines the paths a proposed manifest names; HTTP refusals
  close the connection (doc-0030 H7, M3)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-07T09:31:00Z'
labels:
  - review
  - mcp
  - security
dependencies:
  - TASK-0193
priority: high
type: bug
ordinal: 196000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

H7 (high): harness/subject_check.py confines the documents a call carries, but harness/subject.py:141,145 joins any `[[artefact]] path` (and `[reference] code`) to the temp root, so an absolute or `../` path is read: an existence oracle and the parser's excerpt of any server file in the report, for any token holder over HTTP. `x/../subject.toml` also overwrites the passed manifest. M3 (medium): the reader's HTTP `_guard` answers a refusal (404, 421, 403, 401) without reading the body or closing the connection, so on keep-alive the body runs as a second request with a forged Host: the DNS-rebinding defence is bypassed (probe: 421, then a 200 tools/call). The page closes on refusal. Fixes, not bound by the freeze; doc-0028 G9-11.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A proposed manifest naming an absolute path, or one resolving outside the call's temp instance, is refused before the yield child runs; the report carries neither existence nor content
- [ ] #2 Document keys are normalised before the duplicate check, so x/../subject.toml is refused
- [ ] #3 Every refusal in the reader's HTTP guard closes the connection, through http_boundary, shared with the page; a test sends a refused request whose body is a second complete request on keep-alive and gets no second answer
- [ ] #4 tools/check_mcp_server.py holds both over HTTP
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. H7: subject_check.plan confines every path field of the proposed manifest (PATH_KEYS, any depth) and compares document keys normalised, before any write or yield. 2. M3: http_boundary.BoundedMixin.refuse closes the connection; the reader's _guard, its framing refusal and the page's _boundary, write_guard and framing refusals answer through it. 3. Tests reproducing each probe on the old code; check_mcp_server.py holds both over HTTP; the security scan admits its loopback probe socket, held as tight as the worker's.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Both defects reproduced before the fix: H7 (an absolute [[artefact]] path returned a report; x/../subject.toml flipped the probe to minimal), M3 (421 then 200 on one keep-alive socket, raw socket test and the live check). The live check needs a raw socket (urllib always sends Connection: close), so tests/test_security.py's PROBES admits tools/check_mcp_server.py's create_connection to the literal 127.0.0.1, with a tightness test. The page's write_guard refusal had the same shape as M3 and closes too. Suites: stdlib 672/703 (31 skipped), venv 701/703 (2 skipped), KG_SUBJECT=subjects/jef_data_load 700/703 (3 skipped); check_mcp_server.py --scenarios S1 (rdflib) every check holds.
<!-- SECTION:NOTES:END -->
