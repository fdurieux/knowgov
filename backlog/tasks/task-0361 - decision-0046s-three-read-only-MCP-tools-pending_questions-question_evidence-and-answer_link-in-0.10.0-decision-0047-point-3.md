---
id: TASK-0361
title: >-
  decision-0046's three read-only MCP tools: pending_questions,
  question_evidence and answer_link (in 0.10.0, decision-0047 point 3)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-16T19:16:00Z'
updated_date: '2026-11-16T19:44:00Z'
labels:
  - contract
  - 0.10.0
  - mcp
dependencies: []
references:
  - backlog/decisions/decision-0046
  - backlog/decisions/decision-0047
priority: high
ordinal: 351000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
decision-0046 point 2 names a channel-neutral bridge as three read-only MCP tools; decision-0047 point 3 brings them into 0.10.0 beside who_knows, amending decision-0046's point 4 (the pilot gate). Their schemas follow the issue form already built in a pilot instance: its fields (key, subject, scenario, owner unit, evidence, verdict, statement, note) and its four verdicts. Any MCP client can then walk a person through their questions and hand them the link; the person submits in GitHub. The server gains no write tool.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 pending_questions(handle) lists a handle's open items from the questionnaires and the captures already ingested, refusing a handle that is not issued
- [x] #2 question_evidence(key) returns one item's evidence as the instance generated it, or a not-found reason
- [x] #3 answer_link(key, verdict, statement) returns the prefilled issue-form URL computed from the instance's form template, writing nothing; a verdict outside the form's four is refused
- [ ] #4 Schemas for the three, both transports, check_mcp_server.py holding each, CHANGELOG Unreleased under contract changes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. harness/questions.py: questions.toml at the instance root (format = 1; [questions] dir, evidence, suffix; [form] url, template, title, evidence_base, [form.fields] the eight field ids, [form.verdicts] the four verdict labels); pending(handle), evidence(key), link(key, verdict, statement). Also a CLI.
2. formats.QUESTIONS for questions.toml.
3. MCP tools pending_questions (across subjects, no subject argument), question_evidence and answer_link (per subject); verdict an enum of four symbols, the form's labels from the configuration; schemas pending-questions, question-evidence, answer-link.
4. The knowledge probe gains questions.toml, questionnaires, evidence files and an issue form template; expected reports.
5. check_mcp_server.py holds the three over stdio and HTTP; tests/test_questions.py; CHANGELOG and instance/README.md.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Built: harness/questions.py (module and CLI), the MCP tools pending_questions, question_evidence and answer_link, schemas pending-questions, question-evidence, answer-link, formats.QUESTIONS, the knowledge probe's questions.toml, two questionnaires, two evidence files and an issue form template (.github/ISSUE_TEMPLATE/answer.yml under the fixture), expected reports; check_mcp_server.py's check_knowledge_tools holds the four knowledge tools over stdio (both eras) and HTTP; tests/test_questions.py.
Contract item (the instance configuration): questions.toml at the instance root, format = 1: [questions] dir, evidence, suffix; [form] url (https, no query), template (relative to the instance; the URL's template= names its file), title ({key}, {subject}, {scenario}), evidence_base; [form.fields] the eight field ids (key, subject, scenario, owner, evidence, verdict, statement, note); [form.verdicts] the four labels. The template is read as text, never parsed as YAML (no YAML parser in the standard library): every configured id must appear as an 'id: <id>' line and every verdict label in its text, else answer_link refuses. Evidence files at <evidence>/<subject>/<key percent-encoded><suffix>.
Choices: the verdict is an enum of four symbols (right_as_stated, right_with_correction, wrong, dont_know) so the input schema is fixed at tools/list; the labels the form lists come from questions.toml. pending_questions takes no subject argument (a person's questions span subjects); question_evidence and answer_link do. A key asked of two units (a row with several owners and no owner field) needs scenario and owner on answer_link. The handle is read as issued, not withdrawn, and holding gives on the server's date (KG_AS_OF). An item is answered by a capture on its key dated on or after generated_on from the questionnaire's owner unit (review-due: from the handle addressed).
Where the decision's text meets the code: decision-0046 point 2 gives answer_link (key, verdict, statement); the form also needs the scenario and owner, read from the questionnaire that asks the key, so a key in two questionnaires needs the optional scenario and owner arguments.
Local proof: python tests/run_tests.py 1252/1358 then test_mcp_subjects fixed (REQUIRED_SAMPLE gains verdict and statement); KG_STORE=rdflib python tools/check_mcp_server.py --scenarios S1: every check holds, 27 knowledge-tool answers equal to the expected reports.
<!-- SECTION:NOTES:END -->
