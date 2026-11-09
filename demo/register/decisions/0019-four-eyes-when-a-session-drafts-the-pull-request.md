# 0019 — Four eyes when a session drafts the pull request

Date: 2026-11-05. State: approved (fdurieux, on 2026-11-05: "approve decision 0019"; recorded on #30 before its merge). Supersedes: nothing; states what `four_eyes` in
`metamodel/lifecycle.toml` ("the approver may not be the pull request's author") means when an
assistant session drafts the pull request. Raised by the session that drafted decision 0018 (#29),
in its closing report.

## The finding

Hosted assistant sessions open their pull requests under the maintainer's GitHub account. GitHub
therefore names fdurieux as the author of all 29 pull requests here, #1 to #29. fdurieux is also the
approver of every approved node and link (`approval.by`) and of every approved decision (its state
line). Read against GitHub's author field, `four_eyes` fails on every approval in the register, so
as written it distinguishes nothing. No tool reads `four_eyes`: it is declared in `lifecycle.toml`
and stated in CLAUDE.md and METAMODEL.md, never checked.

The drafting is recorded elsewhere. 31 of the 34 non-merge commits on `main` at `7f1680c` carry a
`Claude-Session` trailer naming the session that wrote them. Three carry the maintainer's own address
and no trailer: `9fa43df` (the structure, the metamodel, the checker and the pilot slice, with the
approvals decision 0002 records), `abb251c` (CLAUDE.md) and `749155d` (the opportunity canvas page).

## Proposal

1. **The author is whoever drafted the change.** For a pull request an assistant session drafted,
   the author is that session: the one named in the pull request's footer and in its commits'
   `Claude-Session` trailers. The account GitHub shows opened the pull request on the session's
   behalf; it is not the author.
2. **The approver is a person, and approving is that person's act.** The act is either their own
   merge, or their words quoted in the record before a merge: a decision's state line, or the
   decision an approval block's `record` names. A session's merge approves nothing; it records who
   changed the file, as CLAUDE.md already says of every merge.
3. **Four eyes holds when the approver did not draft the change.** The maintainer approving a
   pull request a session drafted satisfies it. A session never approves, its own pull request or
   another's.

## Why

The rule exists so that content is approved by someone other than whoever wrote it. Once sessions
open pull requests under the owner's account, GitHub's author field no longer says who wrote a
change; the commit trailers and the pull request's footer do. Approvals from 0016 on are already
recorded this way: by the maintainer's merge (0016, 0017), or by the maintainer's words quoted on
the pull request before a session merged it (0018).

## What it changes

Nothing in a node, a link or an approval block, and no past approval. The three commits without a
trailer are not re-examined here: whether a session drafted them and the maintainer committed
them is not recorded.

## Not decided here; left to later records

What an organisation's instance requires. Where an instance requires two people, a drafting
session counts as neither, and this decision does not say otherwise. Whether the checker enforces
four eyes: it would read the drafting session from the commit trailers and the approver from the
record, and neither is a field today.

## Built in this pull request

The `four_eyes` comment in `metamodel/lifecycle.toml`; METAMODEL.md's "Four eyes" sentence;
CLAUDE.md's approval line. No tool, test or node changes.
