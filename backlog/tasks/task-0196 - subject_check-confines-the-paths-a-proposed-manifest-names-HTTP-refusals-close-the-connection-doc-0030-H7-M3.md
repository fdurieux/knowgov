---
id: TASK-0196
title: >-
  subject_check confines the paths a proposed manifest names; HTTP refusals
  close the connection (doc-0030 H7, M3)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-07T09:32:00Z'
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
- [x] #1 A proposed manifest naming an absolute path, or one resolving outside the call's temp instance, is refused before the yield child runs; the report carries neither existence nor content
- [x] #2 Document keys are normalised before the duplicate check, so x/../subject.toml is refused
- [x] #3 Every refusal in the reader's HTTP guard closes the connection, through http_boundary, shared with the page; a test sends a refused request whose body is a second complete request on keep-alive and gets no second answer
- [x] #4 tools/check_mcp_server.py holds both over HTTP
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. H7: subject_check.plan confines every path field of the proposed manifest (PATH_KEYS, any depth) and compares document keys normalised, before any write or yield. 2. M3: http_boundary.BoundedMixin.refuse closes the connection; the reader's _guard, its framing refusal and the page's _boundary, write_guard and framing refusals answer through it. 3. Tests reproducing each probe on the old code; check_mcp_server.py holds both over HTTP; the security scan admits its loopback probe socket, held as tight as the worker's.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Both defects reproduced before the fix: H7 (an absolute [[artefact]] path returned a report; x/../subject.toml flipped the probe to minimal), M3 (421 then 200 on one keep-alive socket, raw socket test and the live check). The live check needs a raw socket (urllib always sends Connection: close), so tests/test_security.py's PROBES admits tools/check_mcp_server.py's create_connection to the literal 127.0.0.1, with a tightness test. The page's write_guard refusal had the same shape as M3 and closes too. Suites: stdlib 672/703 (31 skipped), venv 701/703 (2 skipped), KG_SUBJECT=subjects/jef_data_load 700/703 (3 skipped); check_mcp_server.py --scenarios S1 (rdflib) every check holds.

AC evidence: #1 tests/test_subject_check_tool.py test_h7_a_manifest_naming_a_path_outside_the_call_is_refused_and_says_nothing_of_the_server (absolute, climbing, ~, reference code, oracle script, verification map, record dir, include glob all refused before any temporary root exists; an existing and a missing target refused alike; no server content in the refusal); #2 test_h7_document_keys_are_compared_normalised_so_the_manifest_cannot_be_overwritten (x/../subject.toml, ./subject.toml, a/b/../../subject.toml refused; the probe stays exit 1); #3 tests/test_http_boundary.py test_m3_a_refusal_closes_the_connection_so_its_body_never_runs_as_a_second_request (raw keep-alive socket, both servers, 421/403/401/404 each one answer, no call reaches the server; old code 421 then 200), refusals through http_boundary.BoundedMixin.refuse, shared with the page; #4 tools/check_mcp_server.py: H7 over stdio and HTTP, M3 by check_refusal_closes on the live HTTP server (old guard fails it). Exemption: tests/test_security.py PROBES admits that one socket, pinned by test_the_mcp_checks_socket_use_is_only_the_loopback_keep_alive_probe (coordinator: keep, as F7's named-exception rule).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
doc-0030 H7 and M3 fixed. `subject_check` now confines every path a proposed manifest names (`PATH_KEYS` at any depth: absolute, `~`, backslash, NUL or climbing past the call's temporary instance refused in `plan()`, before any write or yield, alike for an existing and a missing target) and compares document keys normalised, so `x/../subject.toml` cannot replace the manifest. `http_boundary.BoundedMixin.refuse` answers and closes; the reader's guard and framing refusal and the page's boundary, write guard and framing refusal go through it, so a refused body is never a second request on keep-alive. Each fix has a test that fails on the old code; `check_mcp_server.py` holds both over HTTP through one loopback socket the security scan admits by name. Suites: stdlib 672/703, pins 701/703, jef 700/703; check_mcp_server S1 holds. PR #338.
<!-- SECTION:FINAL_SUMMARY:END -->
