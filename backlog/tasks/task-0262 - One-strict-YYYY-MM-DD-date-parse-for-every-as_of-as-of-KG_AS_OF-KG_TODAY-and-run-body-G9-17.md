---
id: TASK-0262
title: >-
  One strict YYYY-MM-DD date parse for every as_of, --as-of, KG_AS_OF, KG_TODAY
  and run body (G9-17)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-09T09:32:00Z'
updated_date: '2026-11-09T10:55:00Z'
labels:
  - contracts
  - validation
  - release
dependencies: []
references:
  - backlog/decisions/decision-0032
  - task-0256
priority: high
ordinal: 256000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
`harness/cadence.py` `as_of` checks only that the value is 10 characters long, then calls `date.fromisoformat`. On Python 3.11 and later that also takes the ISO week and basic forms: `2026-W45-1` reads as 2026-11-02, and `20261105xx` as 2026-11-05.

The loose parse reaches:
- the MCP `as_of` and `KG_AS_OF`;
- `--as-of` on `gate_cli`, `run`, `trace` and `proposal_impact`;
- the page's `POST /api/run`, whose `run.json` then records "2026-W45-1", a date the run did not read.

Other loose dates:
- `KG_TODAY` takes `20261109`.
- `capture due --on` and `connector --exported-on` take week forms.
- `mcp_runs` uses `\d{4}-\d{2}-\d{2}`, which also matches fullwidth digits.
- `cadence._date` cuts `[:10]` from `valid_until` and `at`.

The documented form is YYYY-MM-DD, and the fix closes the domain to it. The finding is contract-bearing, though borderline, since the documented format is unchanged.

Source: group 1 F3 and group 2 F4, decision-0032 (task-0256), probed on main 2a8bbeb.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 One function parses a date: an ASCII `[0-9]{4}-[0-9]{2}-[0-9]{2}` match, then `fromisoformat`. Every reader named above uses it, and a test lists them.
- [x] #2 A week, basic, fullwidth or suffixed form is refused, naming the value:
- exit 2 on the CLIs;
- the reader's documented refusal on the MCP;
- 400 on the page.
- [x] #3 `record`, `today` and valid dates read as they do today, and the record does not move.
- [x] #4 `cadence._date`'s `[:10]` on `valid_until` and `at` is checked the same way, or the task records why those values are read as stored.
- [x] #5 `CHANGELOG.md`'s Unreleased section names the change under Contract changes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/dates.py: parse (ASCII [0-9]{4}-[0-9]{2}-[0-9]{2}, then date.fromisoformat; NotADate, a ValueError naming the value) and day (a stored date or instant: YYYY-MM-DD alone or followed by T or a space and an ISO time).
2. Move every reader onto it: cadence.as_of (every --as-of, KG_AS_OF, the MCP as_of) and _date; KG_TODAY in review.today and load.now; capture due --on; connector --exported-on; mcp_runs' as_of; the page's POST /api/run as_of and GET /api/register?today=; register_view; and the other date parses (proposal_impact's expires, check_subject._dated, load._day, review._date, capture._date, two check tools' constants).
3. tests/test_dates.py: every loose form refused naming the value, with exit 2 on the CLIs, ToolError on the MCP and 400 on the page; record, today and dates as before; a READERS list; a scan that fails on any fromisoformat outside an allowlist of instants.
4. CHANGELOG Unreleased › Contract changes; the comparators, round trips and check_mcp_server unchanged.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
harness/dates.py: parse reads only ten ASCII characters [0-9]{4}-[0-9]{2}-[0-9]{2} that date.fromisoformat reads. Everything else raises NotADate, a ValueError naming the value, so every existing except ValueError path still refuses. day returns the calendar date of a date, a datetime, or a string whose first ten characters parse and are followed by nothing, or by T or a space and a time that datetime.fromisoformat reads; otherwise None.
Readers (tests/test_dates.py READERS; each one's source calls dates.):
- cadence.as_of, which covers gate_cli, run, trace and proposal_impact --as-of, plus KG_AS_OF and the MCP as_of; cadence._date;
- review.today and load.now (KG_TODAY), plus review._date;
- capture._date and capture._due (--on);
- proposal_impact._date (expires);
- mcp_runs.start_run and mcp_server's three_valued_answer;
- connector._exported_on and connector.land;
- check_subject._dated and check_one_clock.main;
- demo/app/server.py Runner.start (POST /api/run) and _get (GET /api/register?today=), and register_view.build.
The scan fails on any fromisoformat or strptime outside harness/dates.py except these instants: KG_NOW (review.now), a run's heartbeat (runs_index), the connector's export time after its date is held to parse, and the page's own now, started and finished. It also fails on any \d{4}-\d{2}-\d{2} under harness/ and demo/app/.
AC #4: cadence._date now reads through dates.day, so a stored valid_until or at of 2026-W45-1, 20261105xx or 2026-11-05xx names no date, where [:10] took them. check_subject._dated and load._day read the same way, so the checker refuses such an attestation day, as the load applies none.
Refusals:
- gate_cli, trace, run (with the pins), proposal_impact and capture due exit 2, naming the value; connector exits 2 (cannot run) and lands nothing;
- mcp_server exits 2 at start on --as-of or KG_AS_OF; a call's as_of is a ToolError; knowgov-runs' start_run is isError, and the page is never asked;
- the page's Runner.start raises the ValueError its POST handler answers with 400, and register_view.build refuses today.
Checks at 0a57437:
- run_tests: 944/945 (1 skipped) on the pins; 886/945 (59 skipped) bare. The two tests that need yaml or pyshacl skip there, naming it.
- Comparators: CargoQuote 0 differing leaves over 7 scenarios, J-F 0 over 6.
- check_round_trip --chain rdflib,rdflib on CargoQuote, and on J-F C,D3 with --expect-parts: every answer survives.
- check_mcp_server (rdflib) on CargoQuote S1,S2,S6 and J-F C,D3: every check holds.
- check_review_walkthrough and check_one_clock: OK.
At c715316, merged with main through 4d3140b (the complexity ratchet): run_tests 950/951 (1 skipped) on the pins, 892/951 (59 skipped) bare; comparators 0 differing leaves on both subjects. The ratchet held. Runner.start's entry was tightened from 33 to 31, which this change lowered.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Every date knowgov reads now goes through one strict parse, harness/dates.py. parse takes only YYYY-MM-DD in ASCII digits, which date.fromisoformat then reads; day takes a stored date or instant. That closes the domain Python 3.11's fromisoformat had widened: 2026-W45-1 no longer reads as 2026-11-02, nor 20261105xx as 2026-11-05, and fullwidth digits no longer pass a \d check. A loose form is refused, naming the value: exit 2 on gate_cli, trace, run, proposal_impact, capture due and connector; a ToolError on both MCP servers, and exit 2 at start for a bad KG_AS_OF; 400 on the page. cadence._date's ten-character cut on valid_until and at is checked the same way, with check_subject and the load in step. record, today and valid dates read as before. tests/test_dates.py lists every reader, and fails on a new parse outside dates.py. The record held: both comparators show 0 differences, and the round trips and check_mcp_server pass on both subjects. CHANGELOG: Unreleased › Contract changes. Follow-up for the re-probe: the surfaces above.
<!-- SECTION:FINAL_SUMMARY:END -->
