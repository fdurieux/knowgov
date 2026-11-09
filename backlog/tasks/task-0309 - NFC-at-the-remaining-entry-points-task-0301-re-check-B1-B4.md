---
id: TASK-0309
title: NFC at the remaining entry points (task-0301 re-check B1-B4)
status: To Do
assignee: []
created_date: '2026-11-09T22:59:00Z'
labels:
  - contracts
  - keys
  - 0.9.0
dependencies: []
priority: high
ordinal: 302000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix-only, pulled ahead of the 0.9.0 cut because B1 fails open (the coordinator, 2026-11-09). Found by the re-check of task-0301 (the spot check, session_01HTAA1R97hqkerDqYvPVLHm, main ac64d59); N3 itself is fixed. The contract does not move.

B1 (fails open): gate_cli.baseline_of reads levels and a deterministic.json's gate_keys as written, so a baseline with NFD level keys reports no regression (exit 0, 0 regressed_keys, where NFC gives exit 1 and 4). Fix: normalise them, and the held keys mark_held reads.
B2: review.bind reads a ruling's assertion id unnormalised; a pre-0.9 NFD ruling reads gone, a 0.9 one binds as repaired. Fix: read aid through NFC.
B3: 7 BMP CJK compatibility ideographs pass PATTERN raw but NFC to astral and are refused with the normalised value echoed; 437 astral code points (U+2F800-U+2FA1D) fail PATTERN raw but NFC to BMP and are accepted, against decision-0034 A1. Fix: refuse when the raw value or its NFC fails the rule; the message names the value as sent.
B4: check_subject gives no duplicate warning for a task class's keys equal after NFC.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 B1: an NFD baseline reports the same regressions as its NFC twin; a test fails on ac64d59
- [ ] #2 B2: a ruling whose assertion id is NFD binds as its NFC twin does (by id for pre-0.9, by content for 0.9)
- [ ] #3 B3: every key is refused when its raw value or its NFC fails the rule; U+2F800 and U+FA6C both refused with the value as sent
- [ ] #4 B4: check_subject warns duplicate for keys equal after NFC
<!-- AC:END -->
