---
id: TASK-0309
title: NFC at the remaining entry points (task-0301 re-check B1-B4)
status: Done
assignee: []
created_date: '2026-11-09T22:59:00Z'
updated_date: '2026-11-09T23:59:00Z'
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
- [x] #1 B1: an NFD baseline reports the same regressions as its NFC twin; a test fails on ac64d59
- [x] #2 B2: a ruling whose assertion id is NFD binds as its NFC twin does (by id for pre-0.9, by content for 0.9)
- [x] #3 B3: every key is refused when its raw value or its NFC fails the rule; U+2F800 and U+FA6C both refused with the value as sent
- [x] #4 B4: check_subject warns duplicate for keys equal after NFC
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Normalise to NFC at the remaining entry points: --baseline's levels and gate_keys (and held keys read by mark_held), review.bind's assertion id; refuse a key whose raw value or its NFC fails the rule; check_subject warns duplicate on keys equal after NFC.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built by session_01HTAA1RY37AukHuJsZcGjsM (#453) on the spot check's re-check of task-0301; recorded by the coordinator (no backlog CLI there); merged through train #454, where baseline_of keeps both task-0307's identity and B1's _nfc_levels.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The NFC rule now holds at the entry points the re-check of task-0301 found open. B1 (failed open): a baseline written with NFD level keys reports the regressions its NFC twin does. B2: a ruling's NFD assertion id binds as its NFC twin. B3: a key is refused when its raw value or its NFC fails the rule, so the published pattern holds of what was sent (U+2F800..U+2FA1D and U+FA6C refused, the value named as sent). B4: check_subject warns duplicate on keys equal after NFC. Tests in tests/test_key_nfc_entry.py, each failing on ac64d59. The contract does not move; the record holds.
<!-- SECTION:FINAL_SUMMARY:END -->
