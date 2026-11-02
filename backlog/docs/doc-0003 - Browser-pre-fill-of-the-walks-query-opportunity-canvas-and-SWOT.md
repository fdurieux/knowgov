---
id: doc-0003
title: 'Browser pre-fill of the walk''s query: opportunity canvas and SWOT'
type: specification
created_date: '2026-11-02T10:26:00Z'
updated_date: '2026-11-02T10:26:00Z'
---
*2026-11-02. Maintainer register. The brief behind the task that replaces the impact panel's edit link, written after TASK-0024.02 shipped it with a caveat: a scripted browser showed Neo4j Browser 5.26.0 opening the editor empty on the documented `?cmd=edit&arg=` link, because the Browser emits the editor's content one millisecond after start and the editor subscribes after it mounts (TASK-0024.02's notes). The trigger was the maintainer's ask on 2026-11-02: canvas, SWOT, a solution, then build it.*

## Verdict

Replace the edit command with a guide the demo serves and the Browser's play command opens. A Browser guide is an HTML article the Browser fetches and shows in a frame; a block marked runnable puts its text in the editor when clicked, through the Browser's own click-to-insert, which fires after the editor has mounted, so the race is gone, and nothing runs until the viewer presses play. Proven in the session on Browser 5.26.0 with a scripted browser: the link opens the Browser connected, the frame shows the walk's query, one click fills the editor, no result frame appears. The copy button stays. One task.

## Opportunity canvas

| Element | Reading |
|---|---|
| Problem | The panel's link promises a pre-filled editor and delivers an empty one; the panel then tells the viewer to paste. A link that does not do what it says costs trust at the one moment the demo asks the viewer to trust a graph. |
| Users | A viewer of the Neo4j stack who wants the walk as a graph, not a table. The maintainer showing it. An adopter running an instance by address, not localhost. |
| How it is done today | The copy button and a paste; the edit link beside it, with a caveat in the panel and the README. |
| Options weighed | A: drop the link, keep the copy button. B: keep the link with its caveat (today). C: a served guide opened by the play command, click to insert (chosen). D: wait for a Browser fix; the newer preview edition reads no URL command at all, so there is nothing to wait for. E: a page of the demo's own that talks to the Browser; the Browser takes no messages, only its URL commands. |
| Solution outline | `GET /api/register/impact/<id>/guide/<form>` serves a guide holding that form's query in a runnable block, with the CORS headers the Browser's cross-origin fetch needs, and nothing else gains them. The link beside each form becomes `?connectURL=…&cmd=play&arg=<the guide's URL on the host the viewer used to reach the demo>`. The compose file allowlists the demo's host for the Browser's remote content, localhost by default. |
| What stays | Both forms, the copy button, the needs chip, the walk's equivalence test, and `check_impact_cypher.py` comparing every node in the stack job, now reading the guide each link names. |
| What is new | A guide route with CORS, a play link, a compose setting, the README's passage rewritten, and the tool reading the guide's block rather than the link's arg. |
| Value | The link does what it says on the first click: the viewer reaches the graph in two clicks, one on the block and one on play. |
| Cost | One task, about a hundred lines. A new public read-only route that any origin may fetch: register text, no credentials. |
| Measures | The stack job proves the guide's block equals the walk's query for every node and that it runs to the walk. The session's scripted check proves the editor fill on 5.26.0 and is recorded, since the stack job has no browser. |

## SWOT

| | |
|---|---|
| **Strengths** | Uses the Browser's documented guide mechanism, play and runnable blocks, which fires on a click after the editor exists, rather than a start-up message nobody hears. Verified end to end. Nothing runs without the viewer's own click on play. The demo's own origin serves the guide: no third host, no copy of the query outside the server that lists it. |
| **Weaknesses** | A cross-origin fetch: the route needs CORS and the preflight answered. The Browser's host allowlist covers localhost by default; an instance reached by address must be allowlisted in Neo4j's config, and the Browser applies the server's list only once connected, so a link opened before connecting shows "No guide by that name" until the frame is re-run. One more HTML shape to keep right. Two clicks instead of none. |
| **Opportunities** | The guide can carry the panel's sentences and both forms, a Browser-side twin of the panel. Guides for the other saved queries. The same route serves any node of any mounted register. |
| **Threats** | Browser drift: the preview edition drops URL commands and classic guides, so the route lives as long as the classic Browser does; the demo pins neo4j 5.26, so the move is the maintainer's to make. The allowlist setting keeps its old name in 5.26 and may be renamed. CORS on a route invites a reader to widen it; the test holds it to the guide route alone. |

## Shape

One task, after TASK-0024.02: the guide route and its CORS, the play link, the tool, the compose setting, the README, the tests, and the scripted check recorded in the notes.
