---
id: TASK-0167
title: >-
  The page's Arms chip and button say whether model output may run, not only
  whether a key is set
status: Done
assignee:
  - '@claude'
created_date: '2026-11-06T11:20:00Z'
updated_date: '2026-11-06T11:24:00Z'
labels:
  - demo
  - security
dependencies: []
priority: medium
ordinal: 170000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On the maintainer's Mac (Docker Desktop 4.48.0, started without --profile arms), the chip read 'arms enabled (5 of 5 model rows)' and the Arms button was live. Pressing it was refused because the worker had not attested its confinement. demo/app/server.py arms_enabled() counts model rows with a key and the oracle only. harness/execution.py refusal() already says whether model output may run (the instance guard, the backend, the worker's attestation). The page shows its answer beside the key count. Queued on the maintainer's go ('yes, queue the badge fix'), relayed by the coordinating session.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The status JSON (/api/scenarios) gains an additive field execution: {ok, why}, from execution.refusal() (called, never copied); arms_enabled is unchanged; demo/README names the field where it documents the page's HTTP surface
- [x] #2 The chip reads 'arms enabled (n of m model rows)' only when a key and execution are both there; a key without a contained worker is a warn chip, 'arms: no contained worker', with the refusal and an adopter hint (--profile arms, Linux with Landlock, demo/README) in its title; the key-missing chip otherwise
- [x] #3 The Arms button is disabled with the same reason; Replay and Deterministic are unaffected
- [x] #4 Stdlib tests prove the chip and the button each way: no attest.json gives execution.ok false and a 'has not attested' reason, a fresh valid attestation ok, a stale one the stale reason; the stack job asserts the status its worker gives
- [x] #5 demo/README's Mac note, in the adopter register, gives the one-command self-check (docker compose --profile arms run --rm --no-deps worker python harness/worker.py --attest-only) and what write_confined: false means
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-06 evidence.
- AC #1: demo/app/server.py execution_view() returns {ok, why} from execution.refusal(); /api/scenarios carries it beside arms_enabled, which is unchanged. tests/test_arms_execution.py holds that execution_view calls refusal() and copies none of its logic. demo/README names the field beside the page's other HTTP requests.
- AC #2, AC #3: the page's own functions (armsChip, armsBlockedWhy, modeButton and the menu's three buttons) are cut from index.html and run in node against the three attestation states the server reports:
  - absent: warn chip 'arms: no contained worker', Arms disabled with the 'has not attested' reason and the --profile arms / Landlock hint;
  - fresh: 'arms enabled (1 of 1 model rows)', Arms live;
  - stale: warn chip with the stale reason, Arms disabled;
  - no key: the key-missing chip as before;
  - an instance mounted: the guard's own refusal, without the worker hint;
  - a status without the field: refused.
  Replay and Deterministic stay enabled in every case.
- Live check against a local page (rdflib store, an empty jobs folder; the key simulated in the intercepted response, with no key variable set): chip 'arms: no contained worker', Arms disabled, Replay enabled. With a fresh attestation written: 'arms enabled (1 of 5 model rows)'.
- AC #4: the stdlib suite gives 602/623 with 21 skipped and 0 failed. With the pins and KG_TEST_REQUIRE=rdflib,node it gives 622/623, 1 skipped, 0 failed. harness.yml's rdflib job now requires node, so the page test cannot skip unseen. demo.yml's first stack step asserts execution == {ok: true, why: null} with the worker the job starts. The refused case is not asserted in the stack: CI always starts the arms profile, so the refused states rest on the stdlib tests.
- AC #5: demo/README's Mac note, step 2, gives the self-check command and what write_confined: false means.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The page's Arms chip and button now ask whether model output may run, not only whether a key is set. GET /api/scenarios carries execution {ok, why} from harness/execution.py refusal(); arms_enabled is unchanged. The chip has three states: enabled when a key and execution both hold; 'arms: no contained worker', a warn chip, with the refusal and the fix (--profile arms, Linux with Landlock) when the key is there but execution is refused; the key-missing chip otherwise. The Arms button is disabled with the same reason; Replay and Deterministic are unaffected. tests/test_arms_execution.py proves both ways through the page's own script in node, for no attestation, a fresh one, a stale one, no key, a mounted instance and an older status without the field; harness.yml's rdflib job requires node so the page test cannot skip unseen. The stack job asserts that its worker's status reads ok. demo/README gives the field, the worker self-check and what write_confined: false means. Not changed: the MCP runs server's run_options still reports arms_enabled from the page without execution, so an agent could start an Arms run that is then refused; that is a possible follow-up.
<!-- SECTION:FINAL_SUMMARY:END -->
