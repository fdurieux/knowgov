# 0020 — A fourth coverage rule, C4: a realising process is supported by an application

Date: 2026-11-06. State: approved (fdurieux, on 2026-11-08: "approve ieam-register#32"; recorded on the pull request
that carries #32's commits, before its merge). Drafted by session_01HTAA1TvZjugTH7yWr98htT; approval is the
maintainer's word on the pull request (decision 0019). Supersedes: nothing; adds a rule beside the coverage
rules C1 to C3, which are unchanged, and uses `exceptions/` as it is. Asked for by knowgov doc-0025 P3 (the
application-lifecycle study, fdurieux/knowgov#321); the maintainer's acceptance of its advice on 2026-11-06,
P3 to be proposed here, is recorded on fdurieux/knowgov#328.

## Proposal

`tools/check_register.py` `COVERAGE_RULES["C4"]`, evaluated in `check_coverage`, an error as C1 to C3 are:

1. **Denominator.** Every approved node of the processes taxonomy with an approved `realizes` link to an
   approved capability.
2. **Covered.** It is the target of an approved `supports` link whose source is an approved application or
   module.
3. **Excepted.** It is in the scope of an unexpired exception with `rule = "C4"`. Two uses, told apart by
   the exception's rationale: a process manual by design, its exception renewed at each review; and a
   phase-out, its `expires` the date by which a replacement supports the process.
4. **Otherwise uncovered.** One error per process, at `processes/<id>.toml`.

The summary carries `C4` with its denominator, covered, excepted and uncovered; the checker prints one line,
as for C1 to C3. Unlike C2 and C3, which count a `realizes` link whatever its ends' states, C4 asks for both
ends of both links approved: a deprecated application supports nothing, so a sunset cannot pass on the link it
leaves behind.

## What it measures

On the register as of this pull request (base `0826ebc`, 57 nodes, 65 links): **C4 5/5 covered, 0 excepted,
0 uncovered.** It fires nowhere.

| process | realises | supported by |
|---|---|---|
| PROC-0002 Validate the request | CAP-0004 | APP-0002 QuoteAPI |
| PROC-0003 Screen the shipper | CAP-0003 | APP-0004 ScreeningService |
| PROC-0004 Price the quote | CAP-0002 | APP-0003 TariffEngine |
| PROC-0007 Sync run | CAP-0007 | APP-0006 sync, APP-0008 store |
| PROC-0008 Status run | CAP-0008 | APP-0007 health |

Outside the denominator: PROC-0001, PROC-0006, PROC-0009 and PROC-0010 realise no capability; PROC-0005
*Notify the shipper* realises CAP-0005 by REL-04004, all three proposed.

**A sunset, on a copy.** TariffEngine's `supports` link REL-06003 withdrawn: C4 4/5, PROC-0004 uncovered, one
error. A draft `supports` link from another application changes nothing. An exception `rule = "C4"`, scope
PROC-0004, `expires = 2027-03-31`: 4/5 covered, 1 excepted, no error; read on 2027-04-01, PROC-0004 is
uncovered again and the exception reports expired. APP-0003 deprecated with REL-06003 left approved: C4 fires
on PROC-0004 beside the lifecycle error the link already raises.

`tests/test_register.py` `test_coverage_c4_a_realising_process_is_supported_by_an_application` holds the five,
the denominator's boundary and each case above; `test_the_register_is_clean` holds C4 uncovered empty.

## Opportunity canvas

| Block | Content |
|---|---|
| Users | Application owners retiring an application; capability owners; portfolio leads running a rationalisation; a consumer such as knowgov reading a sunset's effect |
| Problem | Deprecating an application fails its approved links (`check_relationships`, the lifecycle rule CLAUDE.md states), and the pull request deprecates them with it. Nothing then says that a process realising an approved capability is left with no application. The capability still reads realised, by a process nothing supports |
| Solution | C4: every approved realising process is supported by an approved application, or an unexpired exception names why not and until when |
| Value | A sunset without a replacement fails the merge until a replacement supports each process or an exception carries the phase-out's date. A manual process is stated as such, with a review date, not left as an absence |
| Metrics | C4's covered, excepted and uncovered with their denominator; exceptions of rule C4 by use (manual, phase-out) and by days to expiry |
| Cost | Thirteen lines of the checker, one test, the README's checks paragraph and one command comment, one METAMODEL.md paragraph. No field, no relationship type, no node changes |
| Risks | An exception renewed indefinitely for a process that is not manual; a merge blocked by a sunset whose owner is not ready to name a date |

## Fit/gap against what it must satisfy

| Requirement | Source | Fit/gap |
|---|---|---|
| A coverage rule checks that an approved node of one kind has a link of one type, or an unexpired exception | the glossary, *coverage rule* | **Fit**: an approved realising process has a `supports` link |
| Coverage is reported with its denominator and its exceptions, never as a percentage to pass | CLAUDE.md | **Fit**: the summary and the printed line |
| Exceptions expire | CLAUDE.md, `_exceptions` | **Fit**: a manual process's exception expires too and is renewed at review |
| A node file never copies a tool's attribute | CLAUDE.md | **Fit**: no field is read beyond `state`; the application's own lifecycle phase stays in its source of record |
| Deprecating a node fails every approved link that references it | CLAUDE.md, `check_relationships` | **Fit**: C4 is the next step of the same sunset, at the process |
| Standard library only | CLAUDE.md | **Fit** |
| The two uses of an exception told apart | doc-0025 P3 | **Gap, small**: by rationale only; a field for the use is not proposed here |
| A consumer that reads `check_coverage` | knowgov `proposal_impact`, `register_view` | **Fit**: both read C1 to C3 by name, so C4 is invisible there until knowgov reads it, at a re-vendor of its choosing |

## SWOT

- **Strengths.** The rule's terms are the glossary's; it fires nowhere today, so no merge breaks; the
  exceptions it needs already exist and already expire.
- **Weaknesses.** It cannot tell a process manual by design from one whose application nobody registered;
  the rationale must. The one process with two supporting nodes, PROC-0007, has two modules of one
  application, so the register shows no replacement case.
- **Opportunities.** A sunset's date becomes a register fact, the exception's `expires`, without copying the
  application's lifecycle from its source of record. knowgov's study (doc-0025) names it as the register's
  half of a sunset; its `register_change` already stales what rests on a deprecated node.
- **Threats.** Exceptions renewed by habit; an instance that reads C4 as a demand to automate every process.

## Advice

**Approve.** The rule costs thirteen lines, changes no node and fires nowhere, and it closes the one
silence a sunset leaves in the register: a realising process with no application. Its error is
deliberate. A retirement without a replacement should state its date, and an exception is the
register's own way to state it. Keep it an error, as C1 to C3 are. A warning would let the silence
through, which is what the rule exists to stop.

## Why

Decision 0012's realisers walk reads a capability's applications through its processes. A process that
realises a capability and has no application breaks that walk's answer without any finding: the walk
returns the process and stops. C2 asks that a required capability is realised; C4 asks that what realises it
is supported. A process may legitimately be manual; then the exception says so, and says until when the
answer holds.

## Not decided here; left to later records

Whether exceptions gain a field naming their use (manual, phase-out). Whether a `supports` link to a parent
process covers its children: C4 descends no `parent`, as C1 to C3 do not. Whether processes that realise
nothing need an application. Whether an instance runs C4 as a warning. Whether knowgov reads C4: its choice.

## Built in this pull request

As decision 0018 was: `COVERAGE_RULES["C4"]`, its block in `check_coverage` and the C4 line in
`tools/check_register.py`; the test above and one line in `test_the_register_is_clean` (twenty-six tests in
all); README "The checks", the rule listed; METAMODEL.md, a "Coverage" paragraph; CLAUDE.md's test count.
