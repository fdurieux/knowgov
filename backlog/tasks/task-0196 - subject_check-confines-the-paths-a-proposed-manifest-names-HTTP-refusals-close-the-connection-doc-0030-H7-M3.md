---
id: TASK-0196
title: >-
  subject_check confines the paths a proposed manifest names; HTTP refusals
  close the connection (doc-0030 H7, M3)
status: To Do
assignee: []
created_date: '2026-11-07T07:15:00Z'
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
