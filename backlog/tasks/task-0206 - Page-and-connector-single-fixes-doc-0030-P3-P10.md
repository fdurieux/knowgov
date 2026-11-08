---
id: TASK-0206
title: Page and connector single fixes (doc-0030 P3, P10)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-07T07:15:00Z'
updated_date: '2026-11-08T14:44:00Z'
labels:
  - review
  - page
dependencies: []
priority: low
type: bug
ordinal: 206000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The maintainer accepted doc-0030's advice on 2026-11-07 ("accept the advise on all four"): the hardening tranche before 0.9.0's cut, in the order F7; F1 with the check_instance guard, H7 and M3; F3, F4 and F2; F5 and F8. The ids below are doc-0030's (the code review at 8d80b2b); each finding there quotes its lines and its probe.

P3: the page's rescan rebuilds on a changed mtime, but page_subject.of caches by root forever, so an edited name, listed, tasks or id is never served, scenarios.toml is not watched, and KG_SUBJECTS with nothing loadable serves public CargoQuote. P10: tools/connector.py drops an export file that shares a basename with another. Fixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An edited subject.toml or scenarios.toml is served on the next request; KG_SUBJECTS with nothing loadable serves no public subject
- [x] #2 connector.py refuses two inputs that map to one relative path
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/subject.py stamp(root): subject.toml and scenarios.toml (mtime, size); Subject.stamp read before the files.
2. page_subject.of caches by root with the stamp and rebuilds from the root when it moved.
3. server: _of keyed by the stamp, _signature watches both manifests, KG_SUBJECTS with nothing loadable lists none; the page and /api/subjects load, every other route 404 naming KG_SUBJECTS.
4. tools/connector.py _files refuses two inputs at one relative path, naming both; one file named twice is one input.
5. Tests first, failing on the old code; CHANGELOG under Changes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
New tests failed on the old code first: test_an_edited_subject_or_scenarios_manifest_is_served_on_the_next_request (the edited name was not served), test_kg_subjects_with_nothing_loadable_serves_no_public_subject (_load_subjects returned CargoQuote), test_two_inputs_that_map_to_one_relative_path_are_refused (not refused). After the fix: stdlib suite 751/790, 39 skipped, 0 failed; KG_SUBJECT=subjects/jef_data_load 751/790, 0 failed; with the pins and KG_TEST_REQUIRE=rdflib,node,openai 789/790, 1 skipped, 0 failed; a bare venv without yaml 745/790, 45 skipped, 0 failed. Comparator on rdflib: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6. The register-view tests and test_page_subject pass in every run.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
P3: a subject carries a stamp of its subject.toml and scenarios.toml (harness/subject.py stamp); page_subject.of rebuilds a subject from its root when either moves, and the page's rescan watches both, so an edited name, listed flag, task, id or scenario is served on the next request. With KG_SUBJECTS set and nothing under it loading, the page serves no subject: the page and /api/subjects load, and every other route answers 404 naming KG_SUBJECTS, where before it fell back to public CargoQuote. P10: tools/connector.py refuses two inputs landing at one relative path, naming both, where it used to drop one silently; one file named twice is still one input. The record is unchanged (comparator equal on both subjects). Tests in test_page_subject and test_connector, each failing on the old code first. CHANGELOG under Unreleased > Changes.
<!-- SECTION:FINAL_SUMMARY:END -->
