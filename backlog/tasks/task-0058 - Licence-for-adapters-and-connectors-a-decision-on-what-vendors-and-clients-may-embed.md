---
id: TASK-0058
title: >-
  Licence for adapters and connectors: a decision on what vendors and clients
  may embed
status: To Do
assignee:
  - '@fdurieux'
created_date: '2026-11-03T22:49:00Z'
updated_date: '2026-11-03T22:51:00Z'
labels:
  - lighthouse
  - licence
milestone: m-8
dependencies: []
documentation:
  - >-
    backlog/docs/doc-0012 -
    Positioning-the-governed-context-quadrant-the-market-and-the-route-to-the-top-right.md
priority: medium
type: task
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
knowgov is GPL-3.0-or-later (decision-0001). That suits an organisation running it internally, but OpenAI's review in doc-0012 §5 found it blocks a vendor or integrator from shipping a connector inside their own product, which route B (plug into the incumbents) depends on. The platform's licence is not in question; the boundary for adapters, connectors and any client SDK is.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A knowgov decision record states the licence of the platform and of adapters, connectors and any SDK, and where the boundary sits in the tree
- [ ] #2 README.md's licence section says what the decision means for an organisation and for a vendor
- [ ] #3 Every file under the boundary carries the licence the decision names
<!-- AC:END -->
