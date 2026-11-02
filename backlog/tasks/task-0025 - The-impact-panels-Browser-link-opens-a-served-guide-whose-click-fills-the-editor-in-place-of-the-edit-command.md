---
id: TASK-0025
title: >-
  The impact panel's Browser link opens a served guide whose click fills the
  editor, in place of the edit command
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-02T10:26:00Z'
updated_date: '2026-11-02T10:35:00Z'
labels:
  - register
  - page
milestone: m-3
dependencies:
  - TASK-0024.02
references:
  - demo/app/server.py
  - demo/app/register_view.py
  - demo/app/index.html
  - demo/tools/check_impact_cypher.py
  - demo/docker-compose.yml
  - demo/README.md
documentation:
  - >-
    backlog/docs/doc-0003 -
    Browser-pre-fill-of-the-walks-query-opportunity-canvas-and-SWOT.md
type: feature
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-0024.02 shipped the Browser manual's ?cmd=edit&arg= link with a caveat: in a scripted test of Browser 5.26.0 the editor opened empty every time, because the Browser emits the editor's content one millisecond after start and the editor subscribes after it mounts. The canvas and SWOT in the linked doc weigh dropping the link, keeping it, a served guide, waiting for a Browser fix and a shim page, and choose the guide: a Browser guide is an article the Browser fetches and shows in a frame, and a block marked runnable puts its text in the editor on a click, through the Browser's own click-to-insert, after the editor exists; nothing runs until the viewer presses play. The session's prototype proved it on 5.26.0: play command through the URL, guide frame shown, one click fills the editor, no result frame. The Browser fetches the guide cross-origin with pragma and cache-control headers, so the route must answer the preflight; its host allowlist covers localhost by default and an instance address must be allowlisted in Neo4j's config, which the Browser applies once connected.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 GET /api/register/impact/<id>/guide/<form> (form: rows or paths) returns a Browser guide, text/html with the CORS headers and the preflight answered, whose runnable block's text is exactly that form's query for <id>; 404 for an unknown node or form; no other route carries CORS headers
- [ ] #2 The link beside each form opens the store's Browser with connectURL and cmd=play&arg=<the guide's URL on the host the viewer used>; the page runs nothing; the panel's sentences say a click on the guide's block fills the editor and nothing runs until play
- [ ] #3 check_impact_cypher.py reads the guide each link names, asserts its block equals the form's listed text, runs it through console_query and compares with the walk; the stack job passes it for every node
- [ ] #4 docker-compose.yml allowlists the demo's host for the Browser's remote content (KG_DEMO_HOST, default localhost), and demo/README.md says in the adopter register how the link works, what an instance by address needs, and that a run wipes the projection first
- [ ] #5 A scripted browser check in the session shows the editor filled with the query after the click on Browser 5.26.0 and no result frame, recorded in the notes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. demo/app/server.py: guide_html(start, form) builds a Browser guide (article.guide, a heading, two sentences, one pre.runnable block holding the form's query, HTML-escaped); GET /api/register/impact/<id>/guide/<rows|paths> serves it as text/html with Access-Control-Allow-Origin * and the preflight (do_OPTIONS on that path only, 404 elsewhere); browser_play_url(origin, path) replaces browser_edit_url, the origin taken from the request's Host header; impact_view(start, origin) gives cypher.browser per form and cypher.guide paths.
2. demo/app/register_view.py: with_cypher's link sentences become the guide's (a click on its block fills the editor; nothing runs until play).
3. demo/tools/check_impact_cypher.py: from each link's arg (cmd=play) fetch the guide, take the runnable block's text, assert it equals the form's text, run it, compare with the walk.
4. demo/docker-compose.yml: NEO4J_browser_remote__content__hosts__whitelist with KG_DEMO_HOST (default localhost); README passage and EC2 note rewritten.
5. Tests: a live HTTP test of the guide route and the preflight (ThreadingHTTPServer on a free port), the link's shape, no CORS on other routes, the tool's helpers; python tests/run_tests.py.
6. Live: the server from the branch against the local Neo4j 5.26.0 and Playwright through the real link: guide frame, click, editor filled, nothing run; recorded in the notes. PR, green matrix, merge.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Prototype before the build (scratchpad, Browser 5.26.0 from the tarball, Playwright on Chromium): a one-file guide server on 8080 with an article.guide and a pre.runnable block. Findings: the Browser's command list matches play-remote (/^play(\s|$)https?/) before play, so :play <url> fetches the URL directly; the fetch carries pragma and cache-control headers, so a preflight OPTIONS must be answered with Access-Control-Allow-Origin, -Methods and -Headers, or the Browser falls back to guides.neo4j.com/<url> and shows 'No guide by that name'; the default allowlist is 'guides.neo4j.com, localhost', matched on hostname, so localhost:8080 is allowed out of the box; the guide's runnable block is read by the directive '.runnable pre' / 'pre.runnable' with autoExec false (textContent, trimmed), so a click inserts and runs nothing; the Browser strips script tags and on* attributes from the guide. With the preflight answered: through ?connectURL=…&cmd=play&arg=<url> the frame showed the query, one click filled the editor, no result frame; the same typed as :play <url>.

Implementation: server.guide_html/guide_path/browser_play_url/impact_guide, GET /api/register/impact/<id>/guide/<rows|paths> served text/html with Access-Control-Allow-Origin * (the _send cors flag, that route alone), do_OPTIONS answering the preflight for an existing guide only (404 elsewhere), impact_view(start, origin) with the origin from the request's Host header so the link names the host the viewer used; register_view.with_cypher(browser=, guide=) with two new controlled sentences; check_impact_cypher.py follows each link to its guide as the Browser would (OPTIONS then GET with Origin and Pragma, headers checked), takes the one runnable block unescaped and trimmed, asserts it equals the listed text, runs it; docker-compose.yml sets NEO4J_browser_remote__content__hosts__whitelist to guides.neo4j.com,localhost,${KG_DEMO_HOST:-localhost} with the variable documented; README passage rewritten (how it works, the edit command's race, the wipe, the instance case: connect first, re-run the frame). Found and fixed on the way: with cypher_list() now loading the register's tools, the page's first requests (/api/cypher and /api/register together) raced register_view._load_tools on the threading server, one seeing the other's half-built module ('cannot import name ROOT from register', reproduced 1 round in 3); a lock around the load, a threaded test, five clean rounds after.

Verification: python tests/run_tests.py 91 of 91 (the new test starts the handler on a free port: the guide route answers the preflight and carries the header, the register route does not, unknown node or form and other routes get 404 on GET and OPTIONS, the block equals the listed text, the link's arg is the host the viewer used; the Browser's own URL reading replicated; the concurrency test). Live against Neo4j 5.26.0 with the register projected: check_impact_cypher.py 'every node agrees: 56 nodes, both forms', exit 0 (each guide fetched with the preflight). Playwright through the page's real links from the walk of APP-0002: both guide frames shown with their headings, each block equal to the page's own text, one click put the query in the editor (the wrapped rendering is the text's start), no result frame, no console errors; screenshots live_guide_0.png and live_guide_1.png in the session's scratchpad.
<!-- SECTION:NOTES:END -->
