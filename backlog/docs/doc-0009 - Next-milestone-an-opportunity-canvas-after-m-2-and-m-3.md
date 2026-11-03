---
id: doc-0009
title: 'Next milestone: an opportunity canvas after m-2 and m-3'
type: other
created_date: '2026-11-03T07:13:00Z'
updated_date: '2026-11-03T07:13:00Z'
---
*2026-11-03. Maintainer register. Opportunity canvas over the candidates after m-2 and m-3, read against doc-0007 (the John Doe walkthrough, #71, tasks 0037–0043) and doc-0008 (the adopter guide study, #72). knowgov main at `cd88415`, register v0.2.3. The artifact page "knowgov's next milestone" is a view of this doc.*

## Verdict

**Recommendation: make the next milestone "Capture that moves the gate".** The capture path is built and correct, but doc-0007 ran it on S2, S4 and S3 and it moved the verdict in none of them (exit 1→1, 1→1, 0→0). It moves a gate only when the blocker is an absence. Even then it reaches QUALIFIED, never PROCEED, because nothing records a review. Until the review step exists, capture is a way to write knowledge down, not a way to resolve a non-conformity.

Decide two authorities first, before any code: who may close a declared gap or settle a dispute, and how a handle maps to a person (draft ieam-register decision 0009). The doc-0007 simulation shows why the order matters. A hand-set review reached PROCEED both when the right documents were rejected and when the wrong ones were approved. A review tool built before the authority is decided would encode a power nobody has granted.

Run the adopter guide (doc-0008) in parallel as a small second milestone, "An adopter can start alone": it is mostly writing, and it lets a first pilot start without the maintainer. Park SARIF and the first private client instance; both depend on the two milestones above.

## The candidates

Cost is a rough size: small is under a day, medium a few days, large a week or more or outside this repository.

| Candidate | Where it is | What the evidence says | Value | Cost | Depends on | Call |
|---|---|---|---|---|---|---|
| Who may close a declared gap or settle a dispute | new decision | F1: in `gate.resolve` a declared gap outranks any assertion, so only a document edit closes it today. F2: a fifth proposed statement leaves a key disputed. | Unblocks S2 and S4 by a recorded act, not an edit | small | none | **next, first** |
| Handle-to-person mapping, issued handles | ieam-register 0009 (draft in doc-0007 §8) | F5: `john-doe` passes both doors. The recommendation is option 1, a directory attribute, with handles minted as `employee-<n>` and a published list of issued handles. | Needed before any real person is captured | small | none | **next, first** |
| A review record for captured statements | task-0037 | Ending (b) appears only in a review simulated by hand. The record would hold rulings (approve, reject, refer), the closing of a declared gap by its owner, and a six-month lapse (doc-0007 §7). | The only route from capture to PROCEED | medium | the two decisions above | **next** |
| Elicited statements in the conflict and corroboration rules | task-0038 | F3: `candidate_pairs` needs an equal `version`, so John contradicting the contract raises nothing. Both adapters need the change. | A reviewer sees the contradiction instead of missing it | small–medium | none | **next** |
| May a capture lower a key? | task-0039 | F4: on S2 the statuses key goes from validated to proposed, and `--baseline record` then exits 1. | Keeps the ratchet usable in a client's CI | small | none | **next** |
| Identifying notes; one owner per key in the example map | task-0042, task-0043 | F6: a note is copied into the bundle. In the example map both units own all 36 keys, so every scenario yields two identical questionnaires. | Hygiene; one person, one file | small | none | **next** |
| Capture routes (b) review falling due, (c) transcript | task-0040, task-0041 | (b) is not built. (c) is half built: the questionnaire already lists a model's inferred statement in `known`. | Keeps captured knowledge current; captures large knowledge cheaply | medium each | task-0037 | after the review step |
| The adopter guide, with the capability, entity and module queries | doc-0008 follow-ups 1–3 | The adopter material is spread over four files. The impact walk follows 0 edges from CAP-0004, ENT-0002, PRD-0002 and JRN-0002, and 5 from APP-0002; three read-only queries answer the capability, entity and module questions. | A pilot that starts without the maintainer | medium | none | **parallel milestone** |
| The pre-load gate: each kind's linter before the load | doc-0008 follow-ups 4–6 | No linter runs anywhere on the route today. The proposal is a `lint` column in `kinds.toml` and a CI template an instance copies, using the contract's exit codes. | Legible's gate contract applied at document level | medium | the guide | **parallel milestone** |
| The register's walk from capabilities and entities | doc-0008 follow-up 7 | The walk follows `supports`, `delivers`, `realizes`, `is_supported_by` and `concerns` only. Growing it is the register's decision, under its decision 0007. | Impact answers from where an architect starts | small proposal, medium build | the queries prove the need first | propose to ieam-register |
| SARIF from the gate command | task-0007, out of scope | The contract names it. No code host shows knowledge findings yet, so SARIF has no reader today. | Findings in the code host without a plugin | small–medium | a consumer | park |
| A first private client instance | outside this repository | The layout, the read-only mount and the gate command are proven on the example. The capture loop does not yet resolve a non-conformity, and there is no guide. | The platform's purpose | large, external | both milestones | park, after both |

## The recommended milestone: Capture that moves the gate

| Box | Content |
|---|---|
| Problem | Capture records John's answer and changes no verdict where the blocker is a declaration or a dispute (S2, S4). No route reaches PROCEED. A person contradicting a document raises nothing. |
| Who has it | The process owner who knows the answer; the owner of a declared gap (compliance, for OD-1); the reviewer, who today has no record to sign. |
| How it is done now | A document edit closes a declared gap. A dispute waits for someone to fix one of the documents. doc-0007 set a status in the store by hand, only to simulate a review. |
| Solution | Two decisions: the authority to close a gap or settle a dispute, and the handle mapping (0009). A review file beside the captures: rulings, `closes`, a lapse after six months (0037). Elicited statements paired with document statements (0038). A rule on lowering a key (0039). |
| Measure of success | S2 runs from BLOCKED to PROCEED by command: capture, then the gap's owner closes OD-1, then a review approves. Each step has its exit code. S4 settles by a ruling that rejects the losing side and cites John's capture. Approving the wrong side of S4 is refused, or flagged by the conflict rule. |
| Cost | Two short decision records. 0037 medium: a load step for reviews, both store adapters, tests, CI on the example instance. 0038 small–medium, Cypher included. 0039, 0042, 0043 small. |
| Risks | A rubber-stamp review gives a confident PROCEED on incoherent knowledge (doc-0007 reached PROCEED after approving the wrong list): 0038 before 0037, so the reviewer sees the conflict, plus the authority decision, so only the owner rules. A ratchet CI fails when a capture lowers a key and gets switched off: decide 0039 before a client's CI meets it. A handle file committed "for convenience" makes erasure impossible: decision 0009 refuses option 3 in writing. |

**Order inside the milestone.**

1. The two decisions. The authority to close a declared gap or settle a dispute, as a knowgov decision. The handle mapping, as ieam-register decision 0009, with the `record`-base question from doc-0007 §4. Both are the maintainer's to approve.
2. 0038, then 0039. The reviewer should see contradictions before a review tool exists, and the lowering rule should be settled before a ratchet meets it.
3. 0037, the review record. Its acceptance is the S2 and S4 runs in the measure box, by command, in `harness.yml`.
4. 0042 and 0043 alongside, since they are small and touch the same files.
5. Then 0040 and 0041, the two further capture routes, as the milestone after.

## The parallel milestone: An adopter can start alone

**In it.** `docs/guide.md` from doc-0008's outline, starting with its drafted Neo4j section, linked from the demo README. The capability, information-entity and module-to-store queries as saved queries, checked by the stack job. A `lint` column in `instance/kinds.toml`, and the pre-load CI template proven on the example instance. A proposal to ieam-register: walks that start from capabilities and entities.

**Watch.** The guide must not promise what the platform does not do: doc-0008's three findings belong on its first page. A lint-clean instance is not a governed one: the guide puts the two gates side by side. Keep screenshots out of the repository: the dashboard page or a regenerating script keeps them current.

## Parked, and what would bring it back

| Item | Comes back when |
|---|---|
| SARIF from the gate | A pipeline or code host wants knowledge findings inline. Until then JSON under its schema serves the contract's machine-readable property. |
| A first private client instance | Both milestones are done: capture resolves S2 and S4 by command, and the guide exists. It also needs a named client with their own repositories, outside every public one. |
| task-0008, a third subject from aris2puml's corpus | A reason for a third public subject appears. It stays in m-4 Parking lot. |
