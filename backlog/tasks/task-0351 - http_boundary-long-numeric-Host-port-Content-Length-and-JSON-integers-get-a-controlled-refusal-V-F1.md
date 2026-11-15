---
id: TASK-0351
title: >-
  http_boundary: long numeric Host port, Content-Length and JSON integers get a
  controlled refusal (V-F1)
status: Done
assignee: []
created_date: '2026-11-15T19:54:00Z'
updated_date: '2026-11-15T21:49:00Z'
labels:
  - bug
dependencies: []
ordinal: 343000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
External validation of 0.9.1 (V-F1): harness/http_boundary.py converts unbounded decimal text with int() (Host port, Content-Length) and parse_json does not catch the ValueError Python's integer-string conversion limit raises, so a 5,000-digit value closes the connection with zero response bytes and a handler traceback on both the page and the MCP reader. Robust rejection only; no bypass shown. Approved for 0.9.x by the maintainer on 2026-11-15. Python's integer safety limit stays enabled.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Both servers (the page and the MCP reader) answer a 5,000-digit Content-Length, a 5,000-digit Host port and a JSON body holding a 5,000-digit integer with a controlled status, never a dropped connection or a handler traceback
- [x] #2 The dispatch count stays zero for each of the three inputs
- [x] #3 Each server still serves a normal request afterwards
- [x] #4 Long leading-zero values are covered as well as long nines
- [x] #5 No contract moves beyond the refusal being a response instead of a dropped connection, named in a CHANGELOG Unreleased line
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Regressions test_limit_09_* in tests/test_http_limits.py failed before the fix (Content-Length: traceback, zero response bytes) and pass after; full suite 1223/1327 passed, 104 skipped, 0 failed. Fix: Host port length-checked before int(), Content-Length over 20 digits a 400, parse_json maps the integer-string ValueError to NotJson.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A 5,000-digit Host port, Content-Length or JSON integer is a 400 on both servers, never a dropped connection; dispatch stays zero and the next request is served. Merged through train #569 (b2dcc5b), whole matrix green incl. stack.
<!-- SECTION:FINAL_SUMMARY:END -->
