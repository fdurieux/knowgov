---
id: TASK-0158
title: >-
  LIMIT-06 raced the server's accept under load: active() == 0 read before any
  half-request was taken from the backlog
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T05:17:00Z'
updated_date: '2026-11-06T05:31:00Z'
labels:
  - test
  - http
dependencies:
  - TASK-0141.04
priority: medium
type: bug
ordinal: 164000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
tests/test_http_limits.py::test_limit_06_a_disconnect_or_a_failing_operation_leaks_nothing (task-0141.04, H2) failed once in 5 full stdlib runs in task-0115's session, at the assert that the real POST gets 409 with calls['start'] == 1; alone it passed. On CI it could turn any PR red at random. The test sends max_connections + 2 half-requests that disconnect mid-body, waits for httpd.active() == 0, then sends the real request. active() counts held slots only, so it reads 0 before the server has accepted anything; under load the real request then queues in the listen backlog behind the half-requests, and when it is accepted the slots are still held and it is answered 503.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reproduced with the failing values recorded, and the cause shown to be the test's wait, not a slot leak in harness/http_boundary.py
- [x] #2 The test waits until the server has taken every half-request from the backlog before it waits for active() == 0; its claim (a disconnect or a failing operation leaks no slot) and every assertion are unchanged, and it still fails on an injected leak
- [x] #3 At least 50 consecutive passes under the load that reproduced it, and the full stdlib and pinned suites green
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Reproduce: an instrumented copy of LIMIT-06 looped under CPU load, recording got, calls['start'] and active() at each point. 2. Check for a leak: after a raced run, do the slots drain? 3. Fix the test: a Counting subclass of BoundedServer in the test counts every connection taken from the backlog (admitted or refused); LIMIT-06 waits for accepted >= sent before active() == 0. harness/ untouched. 4. Prove it: 100 consecutive passes under the same load, an injected leak still caught, the full suites. 5. LIMIT-03, 04, 05 and the MCP side checked for the same pattern.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 reproduction (4-core container): 0 of 100 runs failed with 0 or 4 busy loops; with 12 busy loops, 175 of 300 failed, every one got = 503 and calls['start'] = 0. At the moment of the check active() was 0 right after the sends and 0 at the wait's end; 3 once the real request was answered. Leak check: in 100 more loaded runs, 69 raced and all 69 drained to active() == 0 afterwards, 0 leaked. So the cause is the test: active() counts held slots, which is 0 before the server has accepted any connection; the real POST queued in the backlog behind the half-requests and was refused 503 by BoundedServer.process_request while their handlers still held the 3 slots. The fix, test-only (no harness/ path): tests/test_http_limits.py Counting(hb.BoundedServer) counts every connection process_request takes; _page uses it; LIMIT-06 waits for accepted >= sent, then active() == 0, its assertions unchanged. Evidence: 100 consecutive passes under 12 busy loops (where 58% failed before); with BoundedServer.process_request_thread patched never to release a slot, the test fails (AssertionError(3)); run_tests.py 552/568 stdlib, 567/568 with the pins and KG_TEST_REQUIRE=rdflib, 0 failed. The same pattern elsewhere: LIMIT-05 waits for active() == max_connections, which needs every held connection accepted, and only waits for 0 after the server answered; LIMIT-04 waits for 0 after the server closed both sockets; LIMIT-03 has no such wait; the MCP server has no LIMIT-06 twin (LIMIT-01, 02, 07 only send and read their own answer). None shares the race.

Three full stdlib runs under 8 busy loops: 552/568, 16 skipped, 0 failed each, LIMIT-06 PASS in each. The test's author's three assumptions (via the coordinator) hold: the half-requests end by the server's own path (EOF mid-body; read_timeout 1.5 s, idle 1.0 s as the backstop), the test resets no server state; the wait is on the server having taken all max_connections + 2 from the backlog (accepted counts admitted and 503-refused alike; a refused one never holds a slot) and then active() == 0, every admitted one released; the real POST is admitted and gets 409 with calls['start'] == 1. TOLERANCE stays 2 s; the limits are unchanged.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
LIMIT-06 raced the server's accept: active() == 0 holds before any connection is accepted, so under load the real POST queued behind the half-requests and was refused 503 while they held the slots (175 of 300 runs at 503 / calls['start'] 0 under 12 busy loops). Not a leak: every raced run drained. Fixed in the test alone: a Counting BoundedServer counts connections taken from the backlog, and LIMIT-06 waits for all of them before active() == 0; its assertions, TOLERANCE and limits are unchanged, and an injected leak still fails it. 100 consecutive passes under the reproducing load; three full stdlib runs under load and the pinned suite green. No other limit test shares the pattern.
<!-- SECTION:FINAL_SUMMARY:END -->
