# 0021 — A handle is a person in a role, and who holds it is recorded

Date: 2026-11-16. State: approved (fdurieux, in the maintainer's chat on 2026-11-16: "approve decision 0021"; recorded on
the pull request before its merge; the line read proposed when drafted). Drafted by a session, which never approves, decision 0019; on the maintainer's
words in their chat on 2026-11-16: knowledge "should never be anonymised: knowledge of an employee in an organisation
belongs to the organisation and not to the person; knowing who possesses knowledge helps for collaboration & knowledge
transfer", "The “contributor-001” links the role of that person for that specific question/knowledge", and "draft it with a new
handle per person"). Supersedes: decision 0009 §1 (the key from a handle to a person never in git) and the last
sentence of §5 (the key erased, the handle then anonymous). Decision 0009 §2 (issued, never chosen, never reused),
§3 (the three roles), §4 (a record kept outside the register) and §5's lookup and leaver rules stand. Decision 0008
stands.

## Decision

1. **A handle is one person in one role.** A handle is issued for one assignment: one person, one unit, a set of
   roles (`gives`, `approves`, `closes`). A person who answers for two units holds two handles. When the role
   passes to someone else, the outgoing handle is withdrawn and the successor is issued a new one with the same
   unit and roles; a handle is never reassigned and never reused. Every answer, approval and closed gap therefore
   resolves to exactly one person without reading dates.
2. **Who holds a handle is recorded and never anonymised.** `people/handles.toml` gains one optional field,
   `person`: the organisation's directory identifier for the holder (an account's immutable id or principal name),
   never free text, never an e-mail address typed by hand. The name is read from the directory. The record of who
   held which handle, from `issued` to `withdrawn`, is kept for as long as any statement attributed to the handle is
   in force, and then for the organisation's audit period. Knowledge given under a handle stays attributed to its
   holder after they leave: it belongs to the organisation, and its provenance is part of it.
3. **Where the record lives is the organisation's choice**, recorded in its register: in its own private register
   (the `person` field), or in its directory as decision 0009 described, the register then holding the handle alone.
   It never lives in a public repository. This test case's handles are synthetic roles and carry no `person`.
4. **An organisation records its basis before its first capture**, in a decision of its own register: the purpose
   (knowledge transfer and provenance), the lawful basis it relies on, the notice given to the people who answer,
   the retention period of point 2, and its data-protection officer's approval. The checker cannot verify these; the
   README names them as a condition of going live.
5. **A leaver.** Decision 0009 §5 stands: the handle is withdrawn, never issued again; knowledge under review or
   falling due is asked again of the owning unit, under a new handle. What changes is that the withdrawn handle's
   holder stays recorded, so "who knew this, and when" survives the departure.

## Why

Decision 0009 kept the key out of git so that an erasure request could be honoured and a leaver's answers would
become anonymous. The maintainer's reading is the opposite, and the stronger one for a register of an
organisation's knowledge: what a person knows in their role is the organisation's, and knowing who holds it is how
collaboration and knowledge transfer work. A handle that names the role assignment, with its holder recorded,
serves both the store (stable identifiers, the review roles) and the people looking for the expert.

The attribution is still personal data. Point 4 puts the conditions that make keeping it defensible (a purpose, a
basis, a notice, a retention period, the data-protection officer's approval) where an adopter must meet them before
go-live, rather than leaving them implicit.

## Opportunity canvas

- **Problem:** a pseudonymous handle hides who to ask and who knew what, defeating the register's use for
  knowledge transfer; the key in a separate directory is a second record nobody reads.
- **Who is served:** owners and reviewers who need the expert; newcomers; an auditor asking where a statement came
  from; an adopter's data-protection officer, who gets explicit conditions instead of an unstated default.
- **Solution:** one handle per person per role, its holder recorded in the organisation's register or directory,
  never anonymised, under a recorded basis.
- **What it costs:** one optional field and its check; the README's going-live conditions; in each organisation, a
  notice and its data-protection officer's approval.
- **How we know it worked:** a statement's handle resolves to its holder in one read; a leaver's answers still name
  who gave them; `tools/check_register.py` accepts `person` where present and refuses free text.

## Fit/gap

| it must | fit or gap |
|---|---|
| keep handles issued, never chosen, never reused (0009 §2) | fit: point 1 |
| keep the three roles and the store's rules on them (0009 §3) | fit: unchanged |
| attribute every answer to exactly one person | fit: one handle per person per role; no date arithmetic |
| keep knowledge findable after a leaver | fit: point 5 re-asks under a new handle; the old holder stays recorded |
| keep personal data lawful | gap, accepted: each organisation records its basis, notice, retention and approval (point 4); the register states the conditions and cannot check them |
| keep the public test case free of people | fit: synthetic roles, no `person` (point 3) |
| allow an organisation to keep holders out of its register | fit: point 3, the directory route |

## SWOT

- **Strengths:** one record of who knows what; provenance survives departures; handles stay stable identifiers
  across name changes.
- **Weaknesses:** an organisation has more to settle before go-live; the checker cannot see whether it did.
- **Opportunities:** "who knows what" becomes a register view (handles by unit, role and holder), a direct aid to
  knowledge transfer and a point a lighthouse adopter can see working.
- **Threats:** an adopter goes live without a notice or retention period and exposes itself; point 4 makes the
  conditions explicit, and the README states them as going-live conditions.

## Advice

Approve. It matches how organisations already treat authorship of their work, keeps every structural guarantee of
decisions 0008 and 0009 except anonymity, and makes the conditions for keeping attribution explicit instead of
designing them away. The build follows approval in one pull request: the optional `person` field in
`metamodel/types.toml` `[elicited]` and its check, the comment in `types.toml` and the header of
`people/handles.toml`, and the README's going-live conditions.

## Not decided here

- The format of the directory identifier beyond "never free text": an organisation's directory decides it.
- Whether the knowledge store (knowgov) shows a handle's holder in its reports: knowgov's decision, after this one.
