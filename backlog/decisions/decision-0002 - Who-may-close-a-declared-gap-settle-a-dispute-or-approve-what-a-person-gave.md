---
id: decision-0002
title: Who may close a declared gap, settle a dispute, or approve what a person gave
date: '2026-11-03T21:42:00Z'
status: accepted
---
## Context

doc-0007 ran the capture path (task-0009) on S2, S4 and S3 and moved no verdict. In `gate.resolve`
a declared gap outranks any assertion on its key (F1), so John's answer cannot end S2's
"REQ-06 is NOT YET SPECIFIED"; today only a document edit can. A fifth proposed statement leaves
a disputed key disputed (F2). And no record exists for a person's review, so PROCEED is out of
reach: doc-0007 reached it only by setting statuses by hand, and it reached it as easily by
approving the documents' wrong statement as the right one. doc-0009 put this decision first in
the next milestone, before task-0037 builds the review record, so that the tool encodes an
authority someone granted rather than one its user happens to have.

ieam-register decision 0009 (proposed beside this one) issues handles with a unit and roles:
`gives`, `approves`, `closes`. This decision says what each role may do in the knowledge store.

## Decision

1. **A ruling is a person's act, recorded.** Rulings live in a review file beside the captures
   (task-0037's design: doc-0007 §7), append-only, each with `by` (an issued handle), `on`, and
   `record` (the decision or minutes where the reasons are kept). A model never rules: `by` is
   always an issued handle with the role the ruling needs, and the tool refuses any other.

2. **Approving what a person gave.** A handle with `approves` in the unit that owns the key's
   register nodes (the subject's `register_map.toml`) may approve an elicited statement on that
   key, never one its own handle gave (`by` differs from the capture's `from`). The statement
   goes from proposed to approved, with an approval `{by, on, record}`. The approval lapses six
   months after the capture's `on` (ieam-register decision 0008); the statement then reads
   proposed until route (b) re-asks and a reviewer approves again. Verified stays the oracle's:
   a person's answer reaches verified only when a test executes it.

3. **Closing a declared gap.** Only the gap's owner closes it: the owner the declaration names
   (OD-1 names compliance) or, when it names none, the unit owning the key's register nodes,
   through a handle with `closes`. Closing records that the open decision was taken; it supplies
   no value. The key then rests on whatever statements it has: none leaves it absent, a captured
   one at proposed gives QUALIFIED, an approved one can give PROCEED. A capture on its own never
   closes a gap, and nor does an approval.

4. **Settling a dispute.** A handle with `closes` in the unit owning the key settles a dispute by
   ruling on every side: the statements it keeps are approved, the ones it does not are rejected.
   A rejected statement leaves the live set, keeps its node and its history, and names the
   document to correct (a task in the instance). Approving one side without rejecting the other
   is not a settlement: the key stays disputed, and the tool says so. This is the guard against
   doc-0007's wrong-side PROCEED, together with task-0038, which makes a person's answer appear
   in the conflict rule so the ruler sees every side.

5. **What the tool refuses.** A ruling by a handle that is not issued, is withdrawn, or lacks the
   role; an approval whose `by` gave the statement; a closing by a unit that does not own the
   gap; a ruling that leaves a dispute half-settled. Each refusal names the rule it breaks.

## Consequences

- task-0037 implements this decision: the review file, the rulings, the closing, the lapse, the
  refusals in point 5. Its acceptance is doc-0009's measure: S2 runs from BLOCKED to PROCEED by
  command (capture by `employee-1`, OD-1 closed by a `closes` handle, the answer approved by
  another `approves` handle), and S4 settles by a ruling that cites John's capture. Approving
  S4's wrong side alone leaves it disputed.
- task-0038 comes first, so the ruler sees a person contradicting a document.
- The capture path's ingest checks `from` against the register's issued handles once ieam-register
  decision 0009 is approved and vendored.
- The register's own links keep their four-eyes approval (`approval = { by, on, record }`);
  this decision governs statements in the knowledge store and does not change the register's
  rules.
- Who a handle is stays outside this repository (ieam-register decision 0009): the ruling names a
  handle, and the directory answers who.
