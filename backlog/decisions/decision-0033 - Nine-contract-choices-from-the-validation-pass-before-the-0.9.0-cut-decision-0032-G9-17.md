---
id: decision-0033
title: >-
  Nine contract choices from the validation pass before the 0.9.0 cut
  (decision-0032, G9-17)
date: '2026-11-09T09:33:00Z'
status: proposed
---
## Context

The contract validation pass (decision-0032, task-0256) probed `main` at `2a8bbeb` in three read-only groups: command lines and configuration (41 surfaces), the servers (27), and shapes and semantics (39). It found 16 distinct contract-bearing findings and 40 fix-only ones. The groups reported 19 contract-bearing findings, but three of those were found twice.
- **Six of the contract-bearing findings keep a promise the documents already make.** They are tasked as task-0257 to task-0262, and their fixes hold the cut.
- **The other ten choose contract content,** so they are the maintainer's word. They are the nine choices below.
- **The fix-only findings** are tasked as task-0263 to task-0272 for 0.9.x (decision-0032 point 3).

Each choice is a 0.10.0 if it is settled after the 0.9.0 cut (decision-0016 point 2). The coordinator checked these findings on `main`: group 1's C1, C2, C5 and C6; group 2's F1, F3 and F5; and group 3's CB1, CB2 and CB3. The others rest on the probers' reproductions, which are named in task-0256's notes.

**A correction to decision-0032 point 1.** It counted "the 20 documented `KG_*` settings". decision-0027 dealt only with the 39 settings that were undocumented at the time. The two contract files, `instance/README.md` and `docs/security.md`, name 75 settings. Choice 1 settles which of them are contracts, and the bounded re-probe covers those the pass did not probe.

## Choice 1. Which `KG_*` settings are contracts (group 1, C3)

**The conflict:**
- decision-0016 point 3 makes every setting either file documents a contract.
- task-0234's README section reads "the ones that are contracts from 1.0 (decision-0027). The others this guide names, such as `KG_STORE`… are described where they are used". That reads as if only the twenty were contracts.

**Options:**
- **(a)** Every setting the two files name is a contract, and the README is reworded to say so.
- **(b)** One table in `instance/README.md` lists every setting the two files name, each marked contract or not, held by a test.
  - The contracts are the settings an instance's CI, compose file or hook sets in order to run.
  - The test clock, demo ports and tuning knobs are marked "not a contract".
  - This amends decision-0016 point 3 to "a setting the table marks as a contract".
- **(c)** Group 1's closed list: the twenty plus twelve.

**Canvas.**
- Problem: an adopter cannot tell which settings are frozen.
- Users: every instance's CI and compose file.
- Cost: one table, one test, and the classification.
- Risk: a setting is left out that an adopter relies on.

**Fit/gap.**

| Must satisfy | (a) | (b) | (c) |
|---|---|---|---|
| decision-0016 point 3 | Fit as written | Gap: amended | Gap: amended |
| A checkable denominator | Fit | Fit | Fit |
| The surface frozen is no wider than needed | **Gap:** 75 frozen, tuning knobs included | Fit | Fit |
| A classification the maintainer sees whole | Partial | Fit: the table in its PR | Partial |

**SWOT.**
- S: (b) puts one place to look beside the rule.
- W: the classification is work.
- O: the test catches a new setting that has no row.
- T: a row marked wrongly is frozen until 2.0.

**Advice: (b).** The table comes to the maintainer in its PR before the cut, so the classification is the maintainer's word row by row.

## Choice 2. The values an on/off setting or input accepts (group 1, C4)

**Today:**
- `KG_NO_LOAD` and `KG_PUBLISH` act only on exactly `1`, so `true`, `yes` and `on` silently mean off.
- In `action.yml`, `annotate` and `sarif` are compared case-sensitively in sh, while `publish` is compared in a GitHub expression, which ignores case.

**Options:**
- **(a)** `1` means on; `0`, empty or unset means off; anything else exits 2 naming the setting and `1`. The action's inputs take `true` or `false` in any case, and anything else fails.
- **(b)** `1/true/yes/on` and `0/false/no/off`, in any case; anything else exits 2.
- **(c)** Document "exactly `1`" and change nothing.

**Canvas.**
- Problem: a spelling silently flips a mode.
- Users: CI authors.
- Cost: small.
- Risk: a configuration that spells `true` stops with exit 2 instead of running wrongly.

**Fit/gap.** All three options fit decision-0016.
- (a) keeps every documented spelling working.
- (b) widens what is frozen.
- (c) keeps the silent flip.

**SWOT.**
- S: (a) needs one spelling and no second form to freeze.
- W: (a) refuses `true`, which some readers expect.
- O: the same parser serves every on/off setting.
- T: none known.

**Advice: (a).** The documents already say `=1`, and a refusal names the fix.

## Choice 3. The image's tag scheme (group 1, C6)

**Today the scheme is stated three ways:**
- The README says `:<version>`.
- The contracts table says `:<tag>` for a release and `:latest` for the last main.
- `release.yml` publishes `:v0.8.0`, from `github.ref_name`.

Also, `demo.yml` publishes `:<short-sha>` on every push to main, which no document names.

**Options:**
- **(a)** The contract is `ghcr.io/fdurieux/knowgov:vX.Y.Z` for a release and `:latest` for the last main, as the table says. The README is corrected, and `:<short-sha>` is named as a build of main, not a contract.
- **(b)** As (a), plus an unprefixed `:X.Y.Z` alias.
- **(c)** As (a), with `:<short-sha>` a contract too.

**Canvas.**
- Problem: an adopter's pin is ambiguous.
- Cost: a documentation change; (b) also adds a release step.

**Fit/gap.**
- (a) fits what is published.
- (b) widens what is frozen.
- (c) freezes a tag that is garbage-collectable.

**SWOT.**
- S: (a) gives one form, the one that exists.
- W: some tools expect an unprefixed form.
- O: a test can hold the README, the table and `release.yml` to it.
- T: none.

**Advice: (a).**

## Choice 4. Reserved task-class names (group 1, C7)

**Today:** `[tasks.keys]`, `[tasks.""]` and `[tasks."code gen"]` all pass `check_subject` and `check_instance`. `keys` is already the agent-chosen key set (doc-0014 C4), whose reports the hook refuses.

**Options:**
- **(a)** Reserve `keys`, and require `[a-z][a-z0-9_-]{0,31}`; the checker and the runtime refuse anything else.
- **(b)** Reserve `keys` only.
- **(c)** Document the clash and change nothing.

**Canvas.**
- Problem: a class name collides with a mode, or breaks a file name or id.
- Cost: small.
- Risk: none in the public subjects, which use `codegen` and `design`.

**Fit/gap.**
- (a) fits doc-0014 C4 and the id rules.
- (b) leaves spaces and empty names.
- (c) leaves the collision.

**SWOT.**
- S: a name is safe everywhere it travels.
- W: a stricter manifest.
- O: the same pattern can serve the scenario-id checks.
- T: none known.

**Advice: (a).**

## Choice 5. A register named explicitly that cannot be read (group 1, C8)

**Today:** `check_subject --register DIR` with a DIR that does not exist, or a bad `KG_REGISTER`, gives one "unchecked" note and exit 0, as documented.

**Options:**
- **(a)** Exit 2 when a register is named, by the flag or by `KG_REGISTER`, and cannot be read. "Unchecked" stays for the case where none is named.
- **(b)** Keep today's behaviour.

**Canvas.** A typo silently drops the register check, F4. The cost is small.

**Fit/gap.**
- (a) fits the gate contract's "cannot run" exit 2.
- (b) keeps a silent skip.

**SWOT.**
- S: a mistake is named.
- W: one more refusal.
- O: the same rule serves every reader that takes a register.
- T: none.

**Advice: (a).**

## Choice 6. A format version for the trace ledger and the proposal overlay (group 3, CB5)

**Today:**
- The ledger is a persisted instance input (`KG_LEDGER`). It writes `schema_version: 1` but never reads it, so 99 is read.
- The overlay has no version, and a top-level `format` is refused as an unknown field.

decision-0023's rule (a missing version reads as 1, a newer one is refused with exit 2) covers neither.

**Options:**
- **(a)** Extend decision-0023 to both. The ledger above version 1 is refused with exit 2. The overlay gains an optional top-level `format`: missing reads as 1, and a higher one is refused.
- **(b)** Leave both unversioned until a change needs it.

**Canvas.** Both inputs outlive a release. Adding the signal later is itself a contract change.

**Fit/gap.**
- (a) fits decision-0023 and decision-0016 point 4.
- **(b) has a gap:** the first change becomes a 0.10.0 or later.

**SWOT.**
- S: one rule for every input.
- W: one more field.
- O: the ledger already writes its version, so its half is a read.
- T: none.

**Advice: (a).**

## Choice 7. MCP argument values and the page's run body (group 2, F1 and F2; group 3, CB3)

**Today:**
- -32602 covers unknown argument names only. A type, enum, pattern or minimum violation is an `isError` result.
- A falsy wrong value is coerced to the default:
  - `scenario: ""` answers for the held scenario, which defeats the scenario guard;
  - `walk: ""` reads as `dependants`;
  - `arguments: []` reads as `{}`.
- `POST /api/run` ignores unknown fields: a body with `as-of` runs as of the record date.

doc-0030 F6 and CLAUDE.md already say "an argument outside a tool's inputSchema → -32602".

**Options:**
- **(a)** Validate every argument against the tool's `inputSchema` before dispatch, with -32602 on any violation, and refuse arguments that are not an object. The page refuses unknown body fields with 400.
- **(b)** Narrow the documents to unknown names, and fix only the coercions as `isError` results.

**Canvas.**
- Problem: a malformed value answers unguarded, which is M5's own class of defect.
- Users: lighthouse agents and scripts.
- Cost: about 30 lines and tests per surface.
- Risk: a client that relies on `""` or a stray field. None is known, and no record call sends one.

**Fit/gap.**
- (a) fits doc-0030 F6 and the documents as written.
- (b) needs the documents narrowed.

**SWOT.**
- S: one rule for every tool, and the inputSchemas become executable.
- W: the error shape changes for clients that parse the text.
- O: `check_transports` holds the schemas.
- T: a wrong inputSchema becomes a refusal. The whole `check_mcp_server` suite guards that.

**Advice: (a).**

## Choice 8. Suspect derived outputs per task class (group 3, CB6)

**Today:** a `design` gate reads QUALIFIED with exit 1 because of a `codegen` output whose 15 invalidated statements sit on no `design` key.

**Options:**
- **(a)** Blocker severity applies only to outputs whose used statements sit on the class's keys. The rest are listed at info.
- **(b)** Keep suspect findings store-wide, and document that.

**Canvas.**
- Problem: one class's gate trips on another's artefacts.
- Cost: small.
- Risk: losing a store-wide warning, which (a) keeps at info.

**Fit/gap.**
- (a) fits the per-class verdict.
- **(b) has a gap:** exit 1 then reports another class's knowledge.

**SWOT.**
- S: exit 1 means this class's knowledge.
- W: an info line to read.
- O: none extra.
- T: the record moving. The record is `codegen`'s, and its outputs sit on its own keys.

**Advice: (a), provided the record does not move.** If it would, the build stops and comes back to the maintainer.

## Choice 9. `held_keys`' `gate` field (group 2, F5)

**Today:** the field gates every held key (93 on CargoQuote S1) under the task's bar and calls them "required". It reads "codegen BLOCKED" where `gate_verdict` gives codegen PROCEED.

**Options:**
- **(a)** Compute it on the task's own required keys, so it equals `gate_verdict`'s verdict on the same store.
- **(b)** Drop the field, which is a schema removal.
- **(c)** Keep it as the all-held-keys gate, and reword `why`.

**Canvas.**
- Problem: an agent reads the opposite of the gate.
- Cost: small.
- Risk: none known, since no consumer of today's value is known.

**Fit/gap.**
- (a) fits the field's name.
- (b) is a removal.
- (c) keeps a misleading field.

**SWOT.**
- S: (a) means what it says.
- W: it repeats `gate_verdict`.
- O: none.
- T: none.

**Advice: (a).**

## Decision

**Proposed.** Each choice is the maintainer's word. The build tasks are minted once the choices are answered.

## Consequences

- **Once the choices are answered,** each one taken is minted as a build task. Its fix holds the cut beside task-0257 to task-0262.
- **The bounded re-probe** (decision-0032 point 4) covers what those builds touch, plus the contract settings the pass did not probe under choice 1.
- **doc-0028's G9-17** stays open until the pass is done, as decision-0032 point 6 defines it.
