---
id: doc-0007
title: >-
  Capturing an employee's knowledge to resolve a non-conformity: the John Doe
  walkthrough
type: specification
created_date: '2026-11-02T23:18:00Z'
updated_date: '2026-11-02T23:18:00Z'
---
*2026-11-02. Maintainer register for the verdict, the findings and the analysis; the walkthrough sections in the adopter register. A study: nothing is built. Every command below was run on the public example instance (`tools/example_instance.py`) with `KG_STORE=rdflib`, in a venv with the pins harness.yml installs (CPython 3.13 locally; the harness does not depend on 3.12, the J-F oracle does). Run outputs stay in the session's scratchpad; only this brief is committed. John Doe is a placeholder persona; every record carries the handle `employee-1`.*

## Verdict

**Capture as built records John's knowledge correctly and moves a key, but it moves the verdict in none of the three scenarios.** On S2 it lifts `response|hold_presence` from absent to proposed, yet the gate stays BLOCKED (exit 1 before and after): the outage key carries a declared gap the requirements document states, and in `gate.resolve` a declared gap outranks any assertion on the key. On S4 John's statement is a fifth statement beside four disputed ones and the key stays disputed (exit 1, 1). On S3 the gate's output is unchanged line for line (QUALIFIED, exit 0, 0): John's exact thresholds sit in the bundle beside the vague rows, which still carry their ambiguous gaps.

**Ending (a), BLOCKED to QUALIFIED, is real but needs the blocker to be an absence, not a declaration or a dispute.** Shown on S2′, a counterfactual of S2 in the scratch copy where REQ-06 no longer declares itself open (the rule is decided but unwritten): BLOCKED exit 1 → capture → QUALIFIED exit 0, `--fail-on major` exit 1. **Ending (b), PROCEED, needs a review step that does more than promote John's statement:** a simulated review (store statuses set by hand; no tool) reaches PROCEED only when the reviewer also rejects the documents' contrary statements; approving John's statements alone leaves QUALIFIED.

Six findings follow (§5). The three that matter: a capture can never close a declared gap or settle a dispute (by design, but the walkthrough the maintainer asked for presumes it can); captured statements are never compared with the documents' (the conflict and corroboration rules pair only assertions of one `version`, and a capture's is `capture`), so John contradicting a document raises nothing; and the handle pattern accepts `john-doe`. Recommendation for the handle mapping: **option 1, the directory**, drafted as an ieam-register decision 0009 for the register to take (§8).

## 1. The idea in plain English

Some of what a system must do is written nowhere: one person, here called John Doe, knows it. When a coding assistant asks the knowledge store for what a task needs, the *gate* answers with a *verdict*: PROCEED (everything is verified), QUALIFIED (some of it is only proposed, so the assistant must state those parts as assumptions), or BLOCKED (something is missing, declared open, or contradicted, so the assistant must stop and ask). A *non-conformity* here is anything that makes the gate block or qualify: a missing fact, an open decision, two documents that disagree, vague wording.

*Capturing* John's knowledge means asking him, in a structured way, and recording his answer as a statement that says who gave it (an opaque *handle*, never his name), when, and where the answer is kept. A captured statement starts at *proposed*: it is information, not yet a checked fact. Raising it further needs a second person's *review*, which no tool records yet.

The privacy rule (ieam-register decision 0008): the records carry `employee-1`; the link from `employee-1` to the real John lives only in the organisation's private records. In this brief "John" is the reader's name for the persona; the files never contain it.

## 2. Setting up

```bash
python tools/example_instance.py $SCRATCH/run-S2          # one fresh instance per scenario
export KG_SUBJECT=$SCRATCH/run-S2/subjects/cargo_quote KG_REGISTER=$SCRATCH/run-S2/register KG_STORE=rdflib
cd harness
```

One instance per scenario, because `load_captures` reads every file in the capture folder on every load, whatever scenario its `[capture]` table names: a capture made for S2 also loads in S4. That is right for knowledge (what John said is true whatever the documents' state), but a walkthrough that reuses one folder mixes the endings.

Each questionnaire run prints two lines, one per owner unit. In the example register both ORG-0001 (product owner stand-in) and ORG-0002 (architecture stewardship stand-in) are mapped as owners of all 36 keys, so the two files are identical but for the owner; John, as a steward, answers ORG-0002's.

## 3. The walkthrough, scenario by scenario

### 3.1 S2: the outage rule only John knows

*In plain English.* The documents were planted so that the rule for a screening outage is gone, and the requirements say REQ-06 is "NOT YET SPECIFIED (open decision OD-1, owner: compliance)". The response field that carries the hold (`hold_presence`) is absent from every document. John knows both: on an outage the quote is priced and held unscreened, and the hold flag appears only on that status.

**The gate before.**

```
$ python gate_cli.py --scenario S2
cargo_quote S2 codegen: BLOCKED — 2 required key(s) at a blocking level: QuoteAPI|on_screening_outage (declared_gap), response|hold_presence (absent)
  blocker  QuoteAPI|on_screening_outage is declared gap: the task cannot proceed on it
  blocker  response|hold_presence is absent: the task cannot proceed on it
  major    response|statuses is validated, below verified: an assistant may use it only as a stated assumption
findings: 2 blocker, 1 major
exit 1: a finding at or above blocker
```

**Step 1: the questionnaire.** `python capture.py questionnaire --scenario S2 --out ../questionnaires` prints `Questionnaire for ORG-0002 (Architecture stewardship (stand-in)): 3 of the 36 keys you own need an answer.` The file, excerpt:

```toml
[answered]
from = ""
on = ""

[[item]]
key = "QuoteAPI|on_screening_outage"
level = "declared_gap"
known = []
declared_gaps = ["REQ-06 is NOT YET SPECIFIED (open decision OD-1, owner: compliance)"]
question = "For QuoteAPI, what is the value of on_screening_outage? Give it as the documents would state it."
answer = ""
nobody_knows = false
note = ""

[[item]]
key = "response|hold_presence"
level = "absent"
known = []
declared_gaps = []
question = "For response, what is the value of hold_presence? Give it as the documents would state it."
answer = ""
nobody_knows = false
note = ""
```

(The third item is `response|statuses`, validated, two documents listing the statuses without `held_unscreened`.)

**Step 2: John answers.** He fills `[answered]` with his handle and the date, and three items:

```toml
[answered]
from = "employee-1"
on = "2026-11-02"

[[item]]
key = "QuoteAPI|on_screening_outage"
...
answer = "priced=yes;status=held_unscreened;notified=no;hold=true"
note = "we price the quote and hold it unscreened until screening returns; compliance agreed this in 2025, never written down"
```

and `held_unscreened only` for `hold_presence`, the full list with `held_unscreened` for `statuses`. Had he written `from = "John Doe"`, ingest refuses it, exit 1:

```
refused: answered.from 'John Doe' is not an opaque handle (^[a-z][a-z0-9-]{1,39}$): a person's handle, never a name, an address or a model
```

**Step 3: ingest, and how it is registered (first home).** `python capture.py ingest ../answered-S2.toml`, exit 0:

```
captured 3 answer(s) and 0 'nobody knows' from employee-1 on 2026-11-02 into .../subjects/cargo_quote/captures/2026-11-02-ORG-0002-employee-1.toml
```

The capture file, verbatim:

```toml
# A capture: knowledge a person gave, from an answered questionnaire (task-0009). Read by every load.
# from, on and record are ieam-register decision 0008's fields. Never edited after ingest: a correction is a new capture.

[capture]
subject = "cargo_quote"
scenario = "S2"
task = "codegen"
owner = "ORG-0002"
from = "employee-1"
on = 2026-11-02
record = "captures/2026-11-02-ORG-0002-employee-1.toml"

[[answer]]
key = "QuoteAPI|on_screening_outage"
value = "priced=yes;status=held_unscreened;notified=no;hold=true"
note = "we price the quote and hold it unscreened until screening returns; compliance agreed this in 2025, never written down"

[[answer]]
key = "response|statuses"
value = "error: store_unavailable|held_unscreened|quoted|refused_screening|rejected: invalid_request|review_hold"
note = "held_unscreened is missing from the contract"

[[answer]]
key = "response|hold_presence"
value = "held_unscreened only"
note = "the hold flag appears only on a held_unscreened response"
```

On the next load each answer becomes an assertion of basis `elicited`, status `proposed`, agent `person:employee-1`, under an activity `elicitation` dated 2026-11-02. What an assistant reads (the gate's bundle):

```
## QuoteAPI|on_screening_outage  level=declared_gap  flags=-
  DECLARED GAP gap:declared:OD-1: REQ-06 is NOT YET SPECIFIED (open decision OD-1, owner: compliance)
  [A:cap:2026-11-02-ORG-0002-employee-1:1@capture] value='priced=yes;status=held_unscreened;notified=no;hold=true' basis=elicited status=proposed source=captures/2026-11-02-ORG-0002-employee-1.toml by=employee-1
      text: employee-1 on 2026-11-02: priced=yes;status=held_unscreened;notified=no;hold=true (we price the quote ...)
      GAP unverified: A:cap:2026-11-02-ORG-0002-employee-1:1@capture has no verification record
```

**Step 4: the gate after.**

```
$ python gate_cli.py --scenario S2
cargo_quote S2 codegen: BLOCKED — 1 required key(s) at a blocking level: QuoteAPI|on_screening_outage (declared_gap)
  blocker  QuoteAPI|on_screening_outage is declared gap: the task cannot proceed on it
  major    response|hold_presence is proposed, below verified: an assistant may use it only as a stated assumption
  major    response|statuses is proposed, below verified: an assistant may use it only as a stated assumption
findings: 1 blocker, 2 major
exit 1: a finding at or above blocker
```

One blocker gone (`hold_presence` absent → proposed), one left. *In plain English:* the requirements document still says the decision is open and names compliance as its owner. John's answer is evidence of what the decision probably is, but John is not compliance, and the gate does not let a proposed statement overrule a document that says "not decided". The gate is right here: closing OD-1 is a decision, and a decision has an owner.

Against the record, the ratchet reads John's statuses answer as a regression:

```
$ python gate_cli.py --scenario S2 --baseline record
...
baseline (record): BLOCKED; REGRESSION; response|statuses validated -> proposed
exit 1: a regression against the baseline
```

A key's level is the lowest of its live statements, so a correct but unreviewed answer beside two corroborated (wrong) document statements lowers the key. Honest, and a trap for a CI job that ratchets on the record after a capture.

**S2′: ending (a) shown.** In a scratch copy only, the plant that rewrites REQ-06 is changed to "decided by compliance under OD-1, held by the product owner": the rule is decided but no document carries it, which is the case capture exists for. Before: `BLOCKED — 2 required key(s) at a blocking level: QuoteAPI|on_screening_outage (absent), response|hold_presence (absent)`, exit 1. John answers the two keys; ingest exit 0; after:

```
cargo_quote S2 codegen: QUALIFIED — 3 key(s) below verified, 0 flagged: QuoteAPI|on_screening_outage, response|hold_presence, response|statuses
  major    QuoteAPI|on_screening_outage is proposed, below verified: an assistant may use it only as a stated assumption
  major    response|hold_presence is proposed, below verified: an assistant may use it only as a stated assumption
  major    response|statuses is validated, below verified: an assistant may use it only as a stated assumption
findings: 3 major
exit 0: no finding at or above blocker
```

and `--fail-on major` exit 1. That is ending (a): no longer blocked; the assistant may build, stating John's two answers as assumptions with their ids.

**Ending (b), simulated.** No tool records a review, so the following sets statuses in the in-memory store by hand (`set_props`) after a normal load of S2′ with John's three answers, to see what PROCEED would take:

| simulated review | verdict |
|---|---|
| John's three statements approved | QUALIFIED — 1 key(s) below verified: `response|statuses` (the two documented lists stay validated) |
| … and the two documented status lists rejected | **PROCEED** — all 36 required keys verified or approved, none flagged |
| (instead) John's two approved and the documented lists approved as they stand | PROCEED, with a status list that omits the `held_unscreened` John's outage rule returns |

The last row is the danger the review step must guard against: the gate checks each key alone, and since captures are never compared with documents (§5, F3) nothing flags that two approved keys contradict each other.

### 3.2 S4: two documents disagree, John says which is right

*In plain English.* The sequence diagram and the BPMN say an outage fails the quote; the decision table and the spec say it is priced and held. The conflict rule marks all four statements *disputed*, and the gate blocks. John knows the table and the spec are right: the diagrams predate a 2025 change.

Before: `BLOCKED — 1 required key(s) at a blocking level: QuoteAPI|on_screening_outage (disputed)`, exit 1. The questionnaire's one item lists all four disputed statements in `known` (an informative question: John sees the disagreement he is asked to settle). He answers `priced=yes;status=held_unscreened;notified=no;hold=true`, note "the decision table and the spec are right; the sequence diagram and the BPMN predate the 2025 change". Ingest exit 0. After:

```
cargo_quote S4 codegen: BLOCKED — 1 required key(s) at a blocking level: QuoteAPI|on_screening_outage (disputed)
  blocker  QuoteAPI|on_screening_outage is disputed: the task cannot proceed on it
findings: 1 blocker
exit 1: a finding at or above blocker
```

**Finding: a dispute cannot be resolved by capture as built.** John's statement is a fifth, proposed, beside four disputed ones; the key's level is the lowest, disputed. Nor is his statement weighed against the others: the conflict and corroboration rules pair only assertions of the same `version`, and a capture's version is `capture`, the documents' `v1`. What his answer does give is the reason, in the record, for the fix that does settle it: correct the sequence diagram and the BPMN (a document change, re-read as v2), or have the review step reject the two wrong statements with John's capture as its evidence. Either needs a person with authority over those documents, which John may or may not be.

### 3.3 S3: vague wording, John states the exact thresholds

*In plain English.* The decision table's screening rows were reworded to "below the low forties", "from the low forties up to the mid-sixties", "anything higher"; the sequence diagram names `ACCEPT_MAX` and friends without defining them; the DMN is declared not yet authored. The gate gives QUALIFIED: four threshold keys proposed, thirteen flagged ambiguous. John knows the numbers: accept up to 41, review 42 to 66, refuse from 67.

Before:

```
cargo_quote S3 codegen: QUALIFIED — 4 key(s) below verified, 13 flagged: S-accept|max, S-accept|notified, ...
  major    S-accept|max is proposed, below verified: an assistant may use it only as a stated assumption
  major    S-refuse|min is proposed, below verified: ...
  major    S-review|max is proposed, below verified: ...
  major    S-review|min is proposed, below verified: ...
  minor    S-accept|notified is approved but flagged ambiguous
  ... (9 minor in all)
findings: 4 major, 9 minor
exit 0: no finding at or above blocker
```

The questionnaire's ORG-0002 file asks the four threshold keys (`4 of the 36 keys you own need an answer`), each with the vague value in `known`, e.g. `"risk index clearly low — below the low forties (proposed, extracted, contract/decision_table.md)"`. John answers 41, 42, 66, 67; ingest `captured 4 answer(s)`, exit 0. After: the same first line, the same 13 findings, exit 0; `--fail-on major` exit 1 before and after; `--baseline record` "QUALIFIED; no regression". What changed is what the assistant reads:

```
## S-accept|max  level=proposed  flags=ambiguous
  [A:cap:2026-11-02-ORG-0002-employee-1:1@capture] value='41' basis=elicited status=proposed source=captures/... by=employee-1
      text: employee-1 on 2026-11-02: 41 (accept up to and including 41)
  [A:dt:S-accept|max@v1] value='risk index clearly low — below the low forties' basis=extracted status=proposed ...
      GAP ambiguous: vague wording (low forties, clearly) in F:dt:DT-S/row/accept@v1
  [A:seq:S-accept|max@v1] value='ACCEPT_MAX' basis=extracted status=proposed ...
      GAP ambiguous: symbol ACCEPT_MAX has no definition in any artefact
```

*In plain English:* the gate's verdict is the same, but an assistant now has an exact value, attributed and dated, to state as its assumption instead of guessing. In the scored record arm G guessed and failed the 41-boundary target in 4 of 5 runs; whether a stated, sourced 41 changes that is an arm question this study did not run (it needs a model). The gate cannot show the improvement because its flags count the vague document rows, which are still there.

### 3.4 What the three show together

| | blocker | capture moves the key | capture moves the verdict | what does settle it |
|---|---|---|---|---|
| S2 | declared gap + absent | absent → proposed; validated → proposed (statuses) | no: BLOCKED, exit 1 → 1 | the decision's owner closes OD-1 (a document or decision record), then the review |
| S2′ | absent only | absent → proposed | **yes: BLOCKED exit 1 → QUALIFIED exit 0** | the review, for PROCEED |
| S4 | disputed | no (disputed stays lowest) | no: BLOCKED, exit 1 → 1 | correcting the two wrong documents, or a review that rejects their statements |
| S3 | none (QUALIFIED) | no (proposed + ambiguous stays) | no: QUALIFIED, exit 0 → 0 | correcting the table's rows, or a review that approves John's values and rejects the vague ones |

Capture alone ends an *absence*. A *declaration*, a *dispute* and *vagueness* are statements in documents; they end when the documents change or when a reviewer rules on them, and John's capture is the evidence that ruling cites.

## 4. The two homes of the record, and how they agree

**Home 1, the capture file** (shown in 3.1): in the instance's subject, `captures/<on>-<owner>-<from>.toml`, written by ingest, never edited, read by every load. It carries `from`, `on`, `record` and the answers.

**Home 2, the register link.** Decision 0008 lets a link whose content rests on a person carry `elicited = { from, on, record }`, with `review_due` at most six months after `on`. The link John's outage knowledge concerns is REL-06002 (ScreeningService supports the screening process; rationale "REQ-06 names its outage and the held_unscreened outcome"). In a scratch copy of the register:

```toml
[[link]]
id = "REL-06002"
...
review_due = 2027-04-30
elicited = { from = "employee-1", on = 2026-11-02, record = "../subjects/cargo_quote/captures/2026-11-02-ORG-0002-employee-1.toml" }
approval = { by = "fdurieux", on = 2026-10-31, record = "decisions/0003-cite-req-06-on-the-screening-link.md" }
```

`python tools/check_register.py --root <register> --today 2026-11-02` (the vendored checker):

| variant | result |
|---|---|
| as above | `56 nodes, 65 links, 0 error(s), 7 warning(s)`, exit 0 (the seven warnings are the register's existing hierarchy hints) |
| `from = "John Doe"` | `ERROR elicited relationships/supports.toml [REL-06002]: elicited.from 'John Doe' is not an opaque handle ...`, exit 1 |
| `from = "john-doe"` | exit 0: **accepted** (F5) |
| `review_due = 2027-11-02` | `ERROR ... review_due 2027-11-02 is later than 2027-05-02, 6 months after the knowledge was given`, exit 1 |
| `record = "captures/..."` | `ERROR ... elicited record captures/2026-11-02-ORG-0002-employee-1.toml does not exist`, exit 1 |

**How they agree.** Same three field names, same handle pattern (the capture path reads it from the register's `types.toml`), same date. They disagree on the base of `record`: the capture's is relative to the subject root, the register's to the register root. The link passes only with `../subjects/...`, a path that leaves the register and resolves only in the example instance's layout (register and subject side by side); in a client's real setting the register is its own repository and the path points nowhere. Options for a sequel: the register's `record` names the capture by a stable id (`capture:2026-11-02-ORG-0002-employee-1`) the checker does not resolve, or a decision record in the register quotes the answer (decision 0008 already allows "the decision that quotes it"). The second is the cleaner today and costs a decision per capture; the first needs a checker change in ieam-register. No tool writes home 2 yet: it is a hand edit through the register's own pull request.

## 5. Findings

- **F1. A declared gap outranks any assertion** (`gate.resolve`: `elif declared: level = "declared_gap"`). A capture cannot close it; nor should a proposed statement. The missing piece is a way to *close* a declared gap by a decision record from its named owner (compliance, for OD-1), recorded and loaded like a capture. Today only a document edit closes it.
- **F2. A dispute cannot be settled by capture.** A fifth statement at proposed leaves the key disputed. The settlement is a review that rejects the losing side with the capture as evidence, or a document fix.
- **F3. Captures are never compared with documents.** `candidate_pairs` requires equal `version`; a capture's is `capture`. John contradicting the contract (S2's statuses) raises no conflict; John agreeing with the table (S4) corroborates nothing. Arguably the conflict rule should pair across versions when one side is elicited: a person contradicting a document is exactly what a reviewer must see.
- **F4. A capture can lower a key, and the ratchet then fails.** S2's statuses: validated → proposed, `--baseline record` exit 1. Correct by the min rule, surprising to an adopter; worth a line in the instance README and a decision on whether an elicited statement on a key that has validated document statements should count.
- **F5. The handle pattern does not stop a name.** `john-doe` passes both ingest and the register checker. A pattern cannot know a name; minting can (§8: issue `employee-<n>` from a counter, refuse anything not issued).
- **F6. Free-text notes can identify a person.** "compliance agreed this in 2025" is harmless; "as the author of the 2025 memo" is not. The note is copied into the assertion's text and the bundle. A warning in the questionnaire header, and the reviewer's check, are the only guard.
- **Also seen.** Both owner units own all 36 keys in the example register map, so each scenario yields two identical questionnaires; on a real register, overlap means two people may answer one key and both statements load (the min rule then holds the lower). A capture loads in every scenario (2.).

## 6. The four capture routes

| route | what it is | state | what happens to John's knowledge |
|---|---|---|---|
| (a) questionnaire per owner | the gate's gaps, one file per owner unit, answered and ingested | **built** (task-0009, #69) | walked through above: elicited, proposed, attributed, dated |
| (b) review falling due | when a link's `review_due` passes, or six months after `on` for elicited knowledge, the person (or the owner unit, if they left) is asked again, pre-filled with the earlier answer: still true? | **not built** (named in doc-0001 §0) | a confirmation is a new capture with a new `on`, resetting the six-month clock; a change is a new capture beside the old, for the reviewer |
| (c) interview transcript | a model reads a transcript of a conversation with John and proposes statements | **not built as a tool**; half the path exists | the model's statements load as basis `inferred`, status proposed, never promoted (as S5's machine note does); the questionnaire already lists them in `known` (seen on S5: `"priced=no;status=refused_screening;notified=no (proposed, inferred, llm)"`), so John confirms by copying, correcting or rejecting one into `answer`. Only his answer becomes elicited; the transcript is never the record (doc-0001 §0) |
| (d) on the register link | decision 0008's `elicited` block | **fields exist and are checked**; nothing writes them | §4: a hand edit through the register's PR, checked for handle, date, record path and the six-month review |

Step by step, in the order an organisation would meet them: (a) first, because the gate generates the questions; (d) when the knowledge is about the architecture (which application supports which process), since the register is that knowledge's home; (b) six months on, for both; (c) only when John's knowledge is too large for a questionnaire (a process walked through aloud), and always ending in (a).

## 7. The review step: sketch, not built

**Who.** A person of the owner unit the questionnaire was addressed to, with the approver role the register already names for links, and never the person who gave it (`by ≠ from`). For a declared gap, its named owner (compliance for OD-1). For a dispute, someone with authority over the documents that lose.

**What is recorded.** A review file beside the captures, append-only like them: `captures/reviews/<on>-<reviewer handle>.toml`:

```toml
[review]
by = "steward-2"          # a handle, minted like John's
on = 2026-11-09
record = "decisions/0012-outage-rule.md"   # where the reasons are kept
[[ruling]]
assertion = "A:cap:2026-11-02-ORG-0002-employee-1:1@capture"
outcome = "approved"      # approved | rejected | referred
until = 2027-05-02        # six months after the capture's on (decision 0008)
[[ruling]]
assertion = "A:oas:response|statuses@v1"
outcome = "rejected"      # the documents' contrary statement, with a task to correct the document
[[closes]]
gap = "gap:declared:OD-1" # only when the reviewer is the gap's owner
```

**How the status moves.** `load_captures` (or a `load_reviews` beside it) applies rulings after the rules run: proposed → approved with an approval `{by, on, record}`; a rejected statement leaves the live set; a closed declared gap is removed. After `until` the approval lapses and the statement reads proposed again until route (b) re-confirms it. Verified stays the oracle's and the dated review record's: a person's answer reaches approved by review, verified only if a test executes it (S4's outage key has one: `screening_down_hold`).

**What the reviewer is shown.** The key's statements side by side, and the keys that depend on each other (§3.1's last row: an approved outage rule returning a status the approved status list omits). That cross-key view is the part with no design yet.

## 8. The handle-to-person mapping (draft of a possible ieam-register decision 0009, a sequel to 0008; not decided here)

Decision 0008 left open "how a handle maps to a person (the organisation's own record, kept privately)". Three options:

| | (1) directory attribute | (2) access-controlled table outside git | (3) a file in the instance repository |
|---|---|---|---|
| where | the identity system (Entra ID, LDAP, Okta): a custom attribute `knowledgeHandle` on the person's account | a small database or sheet with handle, person, unit, from, until; access by role | `instance/people.toml`, committed |
| issue | the identity team's provisioning, or a self-service request | a steward adds a row | a PR |
| lookup by a reviewer | a directory query the reviewer's role is allowed | a query by the authorised few | anyone with a clone |
| person leaves | the leaver process disables the account; the attribute stays readable to the lookup role until retention ends | someone must remember to set `until` | a commit; the old row stays in history |
| erasure request | the directory's own retention and erasure process, already audited | deletable, if anyone knows it exists | **cannot be honoured**: git copies the file to every clone and keeps it in history; rewriting history breaks the register's append-only rule |
| cost | one attribute, one query role; needs the identity team | a new store to secure, back up and audit | none, which is the trap |

**Recommendation: option 1**, the parent session's preference, with option 2 as the fallback for an organisation whose directory cannot take a custom attribute (then the table lives with HR or the identity team, not with the architects). Option 3 is refused: it breaks the privacy rule decision 0008 exists for.

**Issuing a handle.** Minted like a register id: `employee-<n>` from a counter the directory holds, never reused, never derived from a name, a unit or a staff number (a unit in the handle leaks a reorganisation; a staff number is personal data in plain sight). Ingest and the register checker would then accept only issued handles: a list of issued handles (no names) published to the instance closes F5.

**Lookup.** Only a reviewer acting on a review due, an owner unit's approver, or the data-protection officer; each lookup logged by the directory. The knowledge store and the register never hold the mapping and never call the directory.

**The six-month review.** At `review_due` the reviewer resolves `employee-1`: found and active → route (b), John re-confirms; found and left, or moved unit → the statement is re-asked of the owner unit (a new capture from a new handle) or, if nobody can say, recorded as "nobody knows", which becomes a declared gap and blocks as it should. The old capture stays: it is history, not current knowledge.

**Retention.** The mapping is kept as long as the organisation keeps any statement attributed to the handle under review, bounded by its HR retention; then the attribute is erased and the handle in git becomes effectively anonymous (pseudonymised data is personal data while the key exists). Free-text notes are the residue (F6).

**For the public demo.** A stand-in for option 1 outside the instance folder, so a mounted instance never contains it, e.g. `$SCRATCH/directory-standin.toml`:

```toml
# ILLUSTRATIVE stand-in for the organisation's directory (option 1). Not a record, not in any instance.
[[account]]
display_name = "John Doe"      # a placeholder persona, no real person
knowledge_handle = "employee-1"
unit = "ORG-0002"
status = "active"
```

## 9. Opportunity map

| outcome | opportunity | solution sketch | state |
|---|---|---|---|
| an absence ends without anyone writing a document | questionnaire per owner | route (a) | built; shown on S2′ |
| a declaration ends when its owner decides | close a declared gap by a decision record | `[[closes]]` in the review file (§7) | not built |
| a dispute ends with a ruling | reviewer rejects the losing side, citing the capture | `[[ruling]] outcome = "rejected"` | not built |
| a person contradicting a document is seen | pair elicited with extracted in the conflict rule | `candidate_pairs` across versions when one basis is elicited | not built (F3) |
| knowledge does not rot | six-month review, re-ask or declare | route (b), directory lookup | not built |
| large tacit knowledge is captured cheaply | transcript → inferred → confirmed | route (c), reusing (a)'s `known` | half built |
| no name ever reaches git | issued handles only | directory counter, published handle list | not built (F5) |

## 10. Sense and nonsense

**Sense.** Capture closes the commonest real gap, the one nobody wrote down, at the price of a short file and a handle. Keeping a person's answer at proposed is the right default: memory is evidence, not proof, and S3 shows the assistant gains an exact value even when the verdict does not move. The gate refusing to let John overrule "NOT YET SPECIFIED" is governance working, not a defect. The privacy rule holds end to end: the name is refused at both doors.

**Nonsense, or the risk of it.** Selling capture as "the validation now passes": it passes only for an absence, and only to QUALIFIED. Treating a reviewer's approval as a rubber stamp: §3.1's last row shows an approval that yields PROCEED on incoherent knowledge. Expecting a pattern to protect privacy (F5). Building the review step before deciding who may close a declared gap: the tool would encode an authority nobody has granted.

## 11. Fit / gap

| need | fit | gap |
|---|---|---|
| ask the right person the right question | questionnaire per owner from the gate | owner mapping is coarse in the example (both units own every key) |
| record who, when, where | `from`, `on`, `record` in both homes, checked | `record`'s base differs between homes (§4) |
| refuse a name | pattern at ingest and in the checker | `john-doe` passes (F5) |
| the gate moves when knowledge arrives | absent → proposed → QUALIFIED | declared gaps, disputes, vagueness do not move (F1, F2) |
| a contradiction with a document is visible | — | not compared (F3) |
| PROCEED on reviewed knowledge | approval status exists for documents | no review record for captures (§7) |
| knowledge ages | six-month `review_due` checked on register links | captures carry no due date; no route (b) |
| find the person later | decision 0008 names the private record | not decided: §8 drafts it |
| erasure | handles are pseudonymous | the mapping's home decides it (§8); notes (F6) |

## 12. SWOT

| | |
|---|---|
| **Strengths** — the path is short (two commands), deterministic, store-agnostic, tested in CI; the gate's levels make an answer's weight explicit; the privacy rule is enforced at both doors; the register and the store name a person the same way. | **Weaknesses** — capture moves a verdict only for an absence; no review step, so PROCEED is unreachable through capture; captures are invisible to the conflict rule; the record path does not resolve across homes; a name-shaped handle passes. |
| **Opportunities** — the review file (§7) completes the loop and gives the register an approval to cite; route (c) is mostly assembled already; the directory option reuses the organisation's audited identity process; a closed declared gap with a named owner is a governance record the client lacks today. | **Threats** — a capture that lowers a key fails a ratchet CI and gets switched off (F4); reviewers approving by habit produce a confident PROCEED on incoherent knowledge; a handle file committed "for convenience" (option 3) breaks erasure for good; free-text notes leak identity. |

## 13. Follow-ups proposed (not created as tasks)

1. A review record for captured statements (§7): rulings, closing a declared gap by its owner, lapse after six months; the PROCEED ending then verifiable by command.
2. Pair elicited statements with extracted ones in the conflict and corroboration rules (F3), both adapters.
3. Decide F4: whether an elicited statement on a key with validated document statements lowers it, and say so in the instance README and the gate's ratchet.
4. ieam-register: draft decision 0009 from §8 (directory attribute; issued handles; lookup role; review finding a leaver; retention), and the `record` base question from §4.
5. Route (b): a questionnaire generated from due reviews, pre-filled with the earlier answer.
6. Route (c): a transcript-to-inferred step that ends in a questionnaire, never in an ingest.
7. A warning in the questionnaire header about identifying notes (F6), and a reviewer's check.
8. The example register map: give each key one owner unit, so the walkthrough yields one questionnaire per person.
