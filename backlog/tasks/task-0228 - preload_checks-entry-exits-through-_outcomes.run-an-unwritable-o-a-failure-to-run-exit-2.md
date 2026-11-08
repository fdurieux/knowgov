---
id: TASK-0228
title: >-
  preload_check's entry exits through _outcomes.run, an unwritable -o a failure
  to run (exit 2)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-08T17:53:00Z'
updated_date: '2026-11-08T18:05:00Z'
labels:
  - harness
dependencies: []
references:
  - tools/preload_check.py
ordinal: 228000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
doc-0030 F6 left tools/preload_check.py on a plain sys.exit(main()): an unwritable -o (a missing folder) exited 1 with a FileNotFoundError traceback, the finding's code, and KG_OUTCOMES never recorded the run. The entry goes through _outcomes.run (task-0159) and harness/cli_exit.run (task-0200), and -o's write failing is cannot-run, exit 2, one line, no report printed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An unwritable -o exits 2 with 'cannot run: -o' on stderr, no traceback and no report, by a test that fails on the code before it
- [x] #2 preload_check's __main__ exits through _outcomes.run, the run recorded under KG_OUTCOMES as cannot run; any other exception escaping main is exit 2
- [x] #3 CHANGELOG.md names the exit 2 under Unreleased > Changes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
tools/preload_check.py writes -o inside a try: an OSError is 'cannot run: -o <path> cannot be written (...)' on stderr, exit 2, the report not printed (its exit_code would disagree with the process's). Its __main__ exits through _outcomes.run (task-0159) around harness/cli_exit.run (task-0200), so KG_OUTCOMES records the run (cannot run) and any other exception escaping main is exit 2 with one line. test_preload's new test fails on the code before (FileNotFoundError, exit 1) and holds the in-process return, the subprocess exit, stderr without a traceback, empty stdout and the outcomes row. CHANGELOG under Unreleased > Changes; CLAUDE.md's preload_check line.
<!-- SECTION:FINAL_SUMMARY:END -->
