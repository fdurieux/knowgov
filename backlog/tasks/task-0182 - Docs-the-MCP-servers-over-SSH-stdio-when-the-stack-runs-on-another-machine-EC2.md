---
id: TASK-0182
title: >-
  Docs: the MCP servers over SSH stdio when the stack runs on another machine
  (EC2)
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-06T17:01:00Z'
updated_date: '2026-11-06T17:34:00Z'
labels:
  - docs
  - mcp
dependencies: []
references:
  - instance/README.md
  - demo/README.md
priority: medium
type: docs
ordinal: 182000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The knowgov MCP servers (`harness/mcp_server.py`, `harness/mcp_runs.py`) are registered as a local stdio command, `docker compose -f /path/to/knowgov/demo/docker-compose.yml exec -T app python harness/…` (instance/README.md, task-0117). With the stack on an EC2 instance reached by SSH (demo/README.md, *The Arms mode on an EC2 instance*, task-0162), the Mac has no container to exec into and both servers are unreachable.

The route: stdio over SSH. The client starts `ssh -T <alias> docker compose -f knowgov/demo/docker-compose.yml exec -T app python harness/mcp_server.py` (and `mcp_runs.py`); the protocol rides the SSH session's stdin and stdout. Needs non-interactive SSH: key auth, the host key known, a `~/.ssh/config` alias with `BatchMode yes`. No new port, no token, `KG_BIND` stays 127.0.0.1. knowgov-runs runs inside `app` on the instance, so its default `KG_PAGE_URL` (`http://localhost:8080`) is the instance's page and `KG_PAGE_TOKEN`, if set, is already in the container.

## The choice: stdio over SSH, not Streamable HTTP behind the tunnel

**Opportunity canvas.** Problem: an adopter whose stack moved to a server loses both MCP servers. Users: the maintainer and any adopter running the stack on a cloud instance. Solution: the existing stdio command, prefixed by `ssh -T <alias>`. Measure: `store_status` answers and `list_subjects` lists both subjects from the Mac. Cost: documentation only; no code, no port, no secret.

**Fit/gap.** Fits: nothing listens beyond 127.0.0.1 (task-0162, task-0096's bind posture); no new secret (no `KG_MCP_TOKEN`); both servers and both clients (Claude Desktop's absolute-path config; Claude Code's `claude mcp add`); the server's one-`as_of`-per-process and reconnect rules unchanged. Gap: Claude Desktop cannot answer an SSH prompt, closed by `BatchMode yes` and a once-off host-key acceptance in Terminal; a stopped and started instance changes address, closed by editing the alias's `HostName` once (or an Elastic IP); every connection is a new SSH session (about a second to start), acceptable for a stdio server started once per client session.

**SWOT.** Strengths: no listener, no token, SSH is the lock already in use for the page's tunnel; the same server code and the same `exec` command as the local route. Weaknesses: depends on the Mac's SSH setup; a key with a passphrase needs the agent or keychain. Opportunities: the same route serves any remote host (another cloud, a lab server), and the alias is one place to change. Threats: a misconfigured alias fails silently in Claude Desktop (mitigated by the log file and a Terminal check command); `StrictHostKeyChecking no` is a tempting shortcut that would drop host verification (the docs ask for the once-off acceptance instead).

**Advice.** Document stdio over SSH as the route for a stack on another machine. Name Streamable HTTP on the instance's 127.0.0.1 behind an `-L` tunnel with `KG_MCP_TOKEN` only as the fallback if SSH stdio cannot work for a client: it needs a long-lived tunnel and a token, and the compose file does not publish 8765. No decision record: this documents a route within the existing posture and decides nothing new.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 instance/README.md has an adopter-register section, "The MCP servers when the stack runs on another machine": the SSH stdio route, its prerequisites (key auth, known host key, ~/.ssh/config alias with BatchMode yes), a config for Claude Code and for Claude Desktop for both knowgov and knowgov-runs, and how to check it
- [x] #2 demo/README.md's EC2 section links the new section
- [x] #3 tests/test_mcp_server.py holds the section: its commands' flags, its Desktop JSON and the check's JSON-RPC lines; python tests/run_tests.py passes
- [x] #4 CHANGELOG.md has a line under Unreleased > Changes (docs)
- [ ] #5 Verified from the maintainer's Mac against the EC2 instance: store_status answers and list_subjects lists both subjects, in Claude Desktop and in Claude Code
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Section in instance/README.md at the end of 'Letting an AI assistant ask the gate'. 2. Link from demo/README EC2 section. 3. Guard test in tests/test_mcp_server.py. 4. CHANGELOG line. 5. Walk the maintainer through it; verification from the Mac closes AC5.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Section at the end of instance/README.md's 'Letting an AI assistant ask the gate'; a pointer from the Claude Code paragraph; demo/README step 5 links it. Guard: tests/test_mcp_server.py test_the_remote_section_runs_the_local_command_over_ssh (both clients' entries are the local exec behind ssh -T <alias>, no token, no -L) and test_the_remote_sections_check_answers_over_stdio (the check's JSON-RPC lines fed to the server on stdin get the greeting and both subjects); the flag guard learnt 'claude mcp remove -s'. AC5 waits on the maintainer's check from the Mac.

Verified 2026-11-06 from the maintainer's Mac against the EC2 instance (t3.large, Ubuntu 24.04, stack bound to 127.0.0.1). Claude Code: claude mcp list shows knowgov and knowgov-runs Connected over ssh -T knowgov-ec2. Claude Desktop: after its own config was replaced (it still ran the local /usr/local/bin/docker entry, log: service "app" is not running), the log shows /usr/bin/ssh, initialize, tools/list and prompts/list answered. store_status answered from the live Neo4j store: cargo_quote, S4, loaded 12:55 UTC, jef_data_load with nothing loaded. list_subjects listed cargo_quote (S1-S7) and jef_data_load (C, D1-D5). The tool answers were shown in one client's transcript; Claude Code connected through the same command. The one difference from the first draft, Claude Desktop's config being separate from claude mcp add, went into the troubleshooting list (f96e689).

Correction: the Claude Code half of AC5 is not yet shown. The maintainer's Claude Code test ran in a cloud session, which cannot see the Mac's claude mcp add or reach the instance; the README now says so. AC5 waits on a local Claude Code session on the Mac.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
With the stack moved to EC2, both MCP servers start over SSH stdio: the local docker compose exec command behind ssh -T <alias>. No port, no token, KG_BIND unchanged. instance/README.md has a new section, 'The MCP servers when the stack runs on another machine' (SSH prerequisites, Claude Code and Claude Desktop entries for knowgov and knowgov-runs, a check from the terminal, troubleshooting), and demo/README's EC2 route links it. tests/test_mcp_server.py holds both clients' entries and runs the check's JSON-RPC against the server; the run passes 644/668 with 24 skipped and 0 failed. The maintainer verified it from the Mac: store_status and list_subjects answer from the instance. Streamable HTTP behind an -L tunnel with KG_MCP_TOKEN stays an undocumented fallback.
<!-- SECTION:FINAL_SUMMARY:END -->
