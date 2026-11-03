# 0009 — Handles are issued, and the key from a handle to a person stays in the directory

Date: 2026-11-03. State: approved (fdurieux, by the merge of #12 on 2026-11-03; the line read proposed when merged). Supersedes: decision
0008 in its "Not decided here" paragraph (how a handle maps to a person); nothing else.

## Decision

**1. The key from a handle to a person lives in the organisation's directory, never in git.** The
identity system (Entra ID, LDAP, Okta or the like) holds the handle as an attribute of the
person's account, for example `knowledgeHandle`. A reviewer resolves a handle through the
directory, under the access rules that already govern personal data, and the directory logs the
lookup. Where the directory cannot take an attribute, a small access-controlled table held by the
identity or HR team (handle, person, unit, from, until) stands in. The register, the knowledge
store and their tools never hold the key and never call the directory. A file in any repository
that pairs a handle with a person is refused: git copies it to every clone and keeps it in
history, so an erasure request could not be honoured without rewriting history, against this
register's append-only rule.

**2. Handles are issued, never chosen.** A handle is minted from a counter the directory holds,
`employee-<n>`, never reused, and never derived from a name, a unit or a staff number. The
register lists the issued handles in `people/handles.toml`, `metamodel/types.toml` `[elicited]`
`issued`: per handle its unit (an organisation node), its roles, the date it was issued and,
once retired, the date it was withdrawn. The list holds no name and no field beyond those five.
When the list exists, `tools/check_register.py` accepts an `elicited.from` only if it is listed,
was issued on or before `on`, and was not withdrawn by then. Decision 0008's pattern still
applies; it can refuse an address, but only the list can refuse `john-doe`.

**3. Three roles.** `gives`: may answer for the unit. `approves`: may approve what another handle
of the unit gave, never what it gave itself. `closes`: may close a declared gap, or settle a
dispute, on what the unit owns. The register records the roles; the rules that use them belong to
the knowledge store (knowgov decision-0002, proposed beside this one).

**4. A record kept outside the register is cited by its id.** An elicited block whose answer sits
in the knowledge store cites it as `capture:<capture id>` (`metamodel/types.toml` `[elicited]`
`external_record`), the id being the capture file's name without its extension. The checker does
not resolve it. Any other `record` is a path inside the register and must exist, as before. A
path that leaves the register (`../subjects/...`) is refused: in an organisation's setting the
register is its own repository, so such a path points nowhere.

**5. Lookup, a leaver, retention.** Only a reviewer acting on a review falling due, an approver of
the owning unit, or the data-protection officer resolves a handle. At `review_due` a resolved
handle that is active is asked again. One that has left or moved unit has its knowledge re-asked
of the owning unit, under a new handle, or recorded as "nobody knows", which is a declared gap.
Its handle gets a `withdrawn` date and is never issued again. The key is kept while any statement
attributed to the handle is under review, within the organisation's HR retention, then erased;
the handle in git is then effectively anonymous.

This test case's `people/handles.toml` lists three synthetic role handles. No real person stands
behind any of them.

## Why

Decision 0008 recorded knowledge a person gave under an opaque handle and left the key open.
knowgov's walkthrough of a captured answer (its doc-0007) found the pattern accepts `john-doe`:
a pattern cannot tell a name from a handle, only issuing can. The same walkthrough found that the
two homes of a captured answer disagreed on `record`: the capture's path is relative to its
subject, the register's to the register, and the only path that passed left the register.

## Not decided here

How the knowledge store applies the roles: who may approve, close or settle, and what is refused.
That is knowgov's decision-0002. Whether a node may carry an `elicited` block stays as decision
0008 left it.
