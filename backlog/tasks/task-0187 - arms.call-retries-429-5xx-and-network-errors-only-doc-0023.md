---
id: TASK-0187
title: arms.call retries 429, 5xx and network errors only (doc-0023)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T23:05:00Z'
updated_date: '2026-11-06T23:46:00Z'
labels:
  - arms
dependencies: []
references:
  - harness/arms.py
priority: low
type: bug
ordinal: 187000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0023's advice on 2026-11-06 ("accept the advice on all three"). arms.call retries every exception four times with waits of 5, 10 and 15 s: in the probe, the 400 for an effort the model refuses cost 30 s and four requests before it was reported.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A 400 or another 4xx but 429 is reported at once, without a retry
- [x] #2 429, 5xx and network errors are retried with the existing waits
- [x] #3 Tests on scripted errors hold both
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. arms.transient(e): a 429 or 5xx status, a connection or timeout error (the SDK's or the transport's), a stream that ended without its usage, or an error event inside a 200 stream; anything else is not.
2. arms.call retries only a transient error, with the existing waits; any other error is raised at once.
3. Tests on scripted errors with the waits recorded, not slept.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06. arms.transient: a status 429 or 5xx; ConnectionError, TimeoutError; the SDK's or the transport's connection and timeout errors by class name (APIConnectionError, APITimeoutError, httpx TransportError, TimeoutException); IncompleteStream (the stream without its usage, raised by arms.call in place of a bare RuntimeError); and the SDK's APIError with no status, an error event inside a 200 stream, kept retried as the stream's form of a 5xx. Anything else is raised at once, a 400 among them. Test: classification of 15 errors; a 400 raised with no wait; 429, 502 and a connection reset retried with waits 5, 10, 15 then answered (attempts 4, three retries recorded); four 503s raised after the three waits.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
arms.call now retries only a transient failure (a 429, a 5xx, a dropped or timed-out connection, a stream that ended without its usage, an error event inside a stream) with the existing waits, and reports any other error at once, so a 400 for an effort the model refuses no longer costs 30 s. Verified by scripted errors with the waits recorded; tests/run_tests.py green both ways.
<!-- SECTION:FINAL_SUMMARY:END -->
