---
id: decision-0034
title: >-
  Three contract choices from the re-probe and the spot check: the settings
  table's reach, scenario ids, the gate_verdict key pattern (decision-0032,
  G9-17)
date: '2026-11-09T16:50:00Z'
status: accepted
---
## Context

The bounded re-probe (decision-0032 point 4; groups 1 to 3) and the independent spot check (point 5) probed `main` at `9861953`. Most of their contract-bearing findings keep a promise an accepted decision already makes, and they are tasked as task-0286, 0287, 0288 and 0292. Three choose contract content, so they are the maintainer's word:
- group 1's N7;
- the spot check's D1;
- the spot check's D3.

The spot check's D2 (`KG_ANNOTATE` values) is task-0267's AC #2, from round 1, and needs no choice.

Each choice is a 0.10.0 if it is settled after the 0.9.0 cut (decision-0016 point 2). The coordinator checked each finding on `main`: N7 against the code, the compose files and `tests/test_settings_table.py`; D1 at `harness/run.py`'s `out_root / sc` and against every public scenario id; D3 at `harness/mcp_server.py`'s `keys` items and `tools/check_subject.py`'s `KEY_RE`.

## Choice 1. The settings table's reach (group 1, N7)

**Today:**
- The code reads 41 `KG_*` names that the 75-row table in `instance/README.md` does not list.
- Of those, a shipped compose file passes `KG_REGISTER_PREVIOUS` (`demo/docker-compose.instance.yml`), `KG_ARMS_EFFORT`, `KG_OUTCOMES`, `KG_PORT_BOLT` and `KG_BUILD_COMMIT`/`KG_BUILD_DESCRIBE`.
- The operator-facing knobs among them:
  - the worker's own limits (`KG_WORKER_MEMORY`, `KG_WORKER_PROCESSES`, `KG_WORKER_FILE_BYTES`, `KG_WORKER_MAX_JOB_SECONDS`);
  - the servers' boundary limits (`KG_MCP_`/`KG_PAGE_` `MAX_BODY`, `MAX_CONNECTIONS`, `IDLE_TIMEOUT`, `READ_TIMEOUT`);
  - `KG_PAGE_LISTEN`, the `KG_AGENT_*` ceilings, `KG_TRACEBACK`, `KG_DEMO_RUNS` and `KG_DEMO_PORT`.
- `KG_NOW` is the clock's instant. Under `KG_CLOCK=pinned`, a contract, the live-run reader refuses without it.
- The rest are internal or test-only.
- decision-0033 choice 1 defines a contract as "the settings an instance's CI, compose file or hook sets", but the table's scope is "every setting instance/README.md or docs/security.md names", and "a setting that neither file names is not a contract". `KG_REGISTER_PREVIOUS` falls between the two.

**Options:**
- **(a)** No change.
- **(b)** Rows for every setting a shipped compose file passes and every operator-facing knob, with `KG_REGISTER_PREVIOUS` and `KG_NOW` marked contracts and the rest "no". `KG_ARMS_EFFORT` is "no" because its values are the model API's. `tests/test_settings_table.py` extends to every `KG_*` the code reads or a compose file passes: each needs a row or an entry, with its reason, on an explicit internal list.
- **(c)** As (b), every new row "no".

**Canvas.**
- Problem: the frozen settings surface misses a setting the shipped instance compose file passes.
- Users: instance operators.
- Cost: one docs-and-test PR.
- Value: the freeze covers what instances actually set.

**Fit/gap.**
- (b) meets choice 1's definition.
- (c) meets the table's wording, but leaves `KG_REGISTER_PREVIOUS` a non-contract the instance compose file passes.
- (a) leaves the gap, and any new setting reopens it.

**SWOT, (b).**
- Strengths: the table is complete by construction.
- Weaknesses: two more frozen settings.
- Opportunities: the settings surface closes before the freeze, not in 0.10.0.
- Threats: the internal list as a back door. A reason per entry bounds that.

**Advice: (b).** `KG_REGISTER_PREVIOUS` is a contract by choice 1's own definition. `KG_NOW` is what `KG_CLOCK=pinned`, a contract, demands for the live-run read. The rest are knobs, demo ports or internal. Only the test keeps the table complete.

## Choice 2. Scenario ids (spot check, D1, CS-3)

**Today:**
- Duplicate ids pass `check_subject`, and `Subject` keeps the last one silently.
- `id = ""` and `id = "../x"` pass, and the runtime gates them: `gate_cli` reports `"scenario": "../x"`.
- `run.py` writes `out_root / sc` (`harness/run.py` `_run_all`), so `../x` leaves `--out`.
- task-0265 (round 1) has the duplicate-id item as fix-only.

**Options:**
- **(a)** Ids match `[A-Za-z0-9][A-Za-z0-9_-]{0,31}`, are unique within a subject, and are refused by `check_subject` and by the `Subject` loader: a format rule on `scenarios.toml`, as choice 4 did for task classes.
- **(b)** `check_subject` refuses duplicate and path-unsafe ids, and the runtime is unchanged.
- **(c)** Document the rule and change nothing.

**Canvas.**
- Problem: a manifest chooses where `run.py` writes, and which of two same-id scenarios runs.
- Users: subject authors, and every reader of a run folder.
- Cost: one rule at two gates.
- Value: the id that names run folders, record paths and run ids is safe by construction.

**Fit/gap.**
- (a) closes the path for every caller: `gate_cli`, `run.py`, the page and the MCP `subject_check`, which run no `check_subject` first.
- (b) leaves the runtime open.
- (c) closes nothing.

**SWOT, (a).**
- Strengths: one rule at both gates.
- Weaknesses: a manifest that runs today can be refused.
- Opportunities: every public id already matches (S0 to S7, C, D1 to D5). The `[[scenario.sources]]` ids (`rerun`, `d3check`) and `stage2.derived` ids are not scenario ids and are unchanged.
- Threats: a private instance's odd ids. The refusal names the id and the rule.

**Advice: (a).** It is the only option that stops the write outside `--out`. It breaks nothing shipped. And a rule set after the cut is a 0.10.0.

## Choice 3. `gate_verdict`'s `keys` items (spot check, D3, GV-1)

**Today:**
- `keys:["nonsense"]` is answered as BLOCKED, "nonsense (absent)".
- The tool's description says `entity|attribute`, and `check_subject`'s `KEY_RE` (`[^|\s]+\|[^|\s]+`) refuses the same input.
- `evidence_bundle` takes `keys` the same way.
- Separately, `KEY_RE`'s `\s` misses a zero-width space, so `thing\u200b|property` passes the checker and reads absent at the gate (CS-4, in task-0265).

**Options:**
- **(a)** Add the key pattern to the `keys` items of `gate_verdict`'s and `evidence_bundle`'s inputSchema, so choice 7's -32602 applies.
- **(b)** Refuse as `isError`, with the inputSchema unchanged (fix-only).

**Canvas.**
- Problem: the executable contract is looser than the server's own rule.
- Users: MCP clients and agents.
- Cost: one pattern and its tests.
- Value: one key rule from the manifest to the wire.

**Fit/gap.**
- Choice 7 made the inputSchema the executable contract. (a) fits it.
- (b) leaves the schema promising less than the server checks.

**SWOT, (a).**
- Strengths: one rule with `check_subject`.
- Weaknesses: the inputSchema changes at 0.9.0.
- Opportunities: fold the zero-width-space fix in now, so the frozen pattern is the strict one. Tightening it after the freeze would be a contract change.
- Threats: a client sending odd keys gets -32602 for BLOCKED. That is 0.x, and the error names the pattern.

**Advice: (a),** with one key rule shared by `KEY_RE` and the inputSchema that refuses Unicode whitespace and format characters (`\u200b` to `\u200d`, `\u2060`, `\ufeff`) on either side of the `|`.

## Decision

Accepted by the maintainer on 2026-11-09: "N7, D1, D3 as advised".

| Choice | Taken | What changes | Build |
|---|---|---|---|
| 1. The settings table's reach | (b) | Rows for every compose-passed setting and operator-facing knob; `KG_REGISTER_PREVIOUS` and `KG_NOW` contracts; the test covers every `KG_*` the code reads or a compose file passes, an internal list with reasons apart | task-0294 |
| 2. Scenario ids | (a) | `[A-Za-z0-9][A-Za-z0-9_-]{0,31}`, unique within a subject, refused by `check_subject` and the `Subject` loader | task-0295 |
| 3. `gate_verdict`'s `keys` | (a) | One key pattern in `KEY_RE` and the `keys` items of `gate_verdict` and `evidence_bundle`, Unicode format characters refused | task-0296 |

## Consequences

- **The three builds** are task-0294 to task-0296. Each holds the 0.9.0 cut beside task-0286, 0287, 0288 and 0292, and is re-checked by its original prober under decision-0032 point 4.
- **decision-0033 choice 1's table** now reaches every setting the code reads or a compose file passes. The README's settings paragraph says so.
- **task-0265's duplicate scenario id** moves to task-0295. task-0265 keeps its other items.
- **task-0265's CS-4 zero-width space** moves to task-0296.

## Amendment A1 (2026-11-09; accepted 2026-11-09): choice 3 refuses every control and format character

**Context.** The spot check's re-check of task-0296, at `main` `946c72e`, found that the five characters choice 3 lists are not the whole class. These still pass `harness/key_rule.py` on every surface and read as absent at the gate (K1), as confirmed by the coordinator on `main`:
- U+200E (LRM);
- U+202E (RLO, a bidi override of the Trojan Source kind);
- U+00AD (soft hyphen);
- U+2061 and U+180E;
- NUL.

It also found that `\s` differs between the engines (K2): Python's str `\s` matches U+001C to U+001F and U+0085, and ECMA-262's does not. So a JavaScript client validating the inputSchema accepts `thing\x1c|property`, which the server refuses with -32602.

**Options:**
- **(a)** Refuse every character of general category Cc and Cf on either side of the `|`, listed explicitly as `\uXXXX` ranges so ECMA-262 and Python agree. This settles K2 too.
- **(b)** Keep the five, and add U+001C to U+001F and U+0085 explicitly for K2.

**Canvas.**
- Problem: a key that looks right and never matches, including bidi-override forms.
- Users: subject authors and MCP clients.
- Cost: one pattern and its tests.
- Value: the frozen key rule closes the class.

**Fit/gap.**
- Choice 3's title says "Unicode format characters refused", while its advice listed five. (a) fits the title; (b) fits the list.
- decision-0033 choice 7 makes the inputSchema the executable contract. Only a pattern both engines read alike keeps that promise, and (a) gives one.

**SWOT, (a).**
- Strengths: the whole invisible class, and one reading in both engines.
- Weaknesses: a longer pattern to freeze.
- Opportunities: free before the cut, a 0.10.0 after it.
- Threats: a private instance with a control character in a key, which is implausible. Every public key is ASCII and still matches.

**Advice: (a).** Combining marks (Mn, such as U+034F) stay allowed, because accented names in decomposed form need them.

### Acceptance of A1

Accepted by the maintainer on 2026-11-09: "K1 (a) as advised". The build is task-0297, which holds the 0.9.0 cut.

### A1's reach above U+FFFF (accepted 2026-11-09)

**Context.** Building task-0297 found 127 Cc and Cf code points above U+FFFF, the tag characters U+E0000 to U+E007F among them. ECMA-262 without the `u` flag, which JSON Schema does not guarantee, reads an astral character as two surrogate units, and Python reads it as one code point. So no single pattern refuses those 127 while allowing other astral characters in both engines alike.

**Options:**
- **(a)** The pattern is a positive list of BMP ranges, without the surrogates or the refused categories. Every astral character is refused, in every engine.
- **(b)** Allow every astral character, the 127 included.
- **(c)** Rely on the `u` flag.

**Canvas.**
- Problem: invisible keys above U+FFFF.
- Users: subject authors and MCP clients.
- Cost: none beyond task-0297, whose test covers every code point.
- Value: the frozen rule closes the invisible class whole.

**Fit/gap.**
- (a) meets A1's aim, with the engines provably agreeing; its gap is astral letters.
- (b) leaves the class partly open.
- (c) breaks decision-0033 choice 7's executable inputSchema.

**SWOT, (a).**
- Strengths: no engine difference, and an exhaustive test.
- Weaknesses: no emoji, no CJK Extension B onward, and no historic scripts in a key.
- Opportunities: allowing them later widens the rule without breaking a key.
- Threats: an adopter with such names. No public key uses an astral character.

**Advice: (a).** Name it in 0.9.0's Known limits: keys use characters up to U+FFFF.

Accepted by the maintainer on 2026-11-09: "astral (a) as advised".
