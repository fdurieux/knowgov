---
id: doc-0027
title: 'Independent evaluation brief: the knowgov stack on a governed-context quadrant'
type: specification
created_date: '2026-11-06T09:03:00Z'
updated_date: '2026-11-06T09:03:00Z'
tags:
  - brief
  - positioning
  - quadrant
  - evaluation
---
# Independent evaluation brief: the knowgov stack on a governed-context quadrant

*Prepared 2026-11-06 by a session working on knowgov, so by the home team: treat every framing
here as a claim to test, the category included. The brief gives you a method and public sources
only. It carries no conclusion, no expected placement and no fact sheet about the product. Your
report goes back to the maintainer's coordinating session. That session compares it, afterwards,
with earlier scorings you will not see.*

---

## For the operator

- Send this brief unedited.
- If the model cannot browse, attach the text of every file marked **required** in §4. If you
  can, also attach the four public pages in §4.4 as fetched on the run date. Record which you
  attached.
- Keep the model's answer outside the repositories as raw output. Record the model, its version,
  its effort setting, whether it could browse, and the date.

---

## 1. The task

Place one product, **the knowgov stack**, and a field of about eighteen alternatives on two
axes, Vision and Execute (§7). Do it twice:

- **now**, at the pins in §3;
- **as a v1.0**, stating the conditions you take a v1.0 to require (§8).

Every placement cites public evidence. Deliver one Markdown report in the fixed structure of §10.

## 2. Rules

1. **Public sources only.** The sources are the public repositories and pages in §3 and §4,
   public vendor documentation, and independent publications, each with its date.
2. **What you must not use:**
   - any private session, chat transcript or private repository;
   - claude.ai artifact pages;
   - anything named J-F or `jef_data_load`: ignore mentions of it, and score nothing on it;
   - bank-related data of any kind.
3. **Do not read:**
   - knowgov's `backlog/` folder, or pumllint's `ROADMAP.md` and `docs/positioning-quadrant.*`.
     They hold the maintainer's own earlier conclusions.
   - pumllint's README places pumllint in a different field (diagram-as-code checkers). Do not
     carry that placement over.

   If you meet an earlier score or placement anyway, log it in §10.2 with the file and whether it
   moved you.
4. **Evidence classes.** Mark every scored cell with one class and its citation:

   | class | meaning |
   |---|---|
   | `observed` | you read the code, a test, a CI run, a tag or a public metric yourself |
   | `documented` | the product's own public prose: its README, CHANGELOG, docs or the vendor's pages |
   | `third-party` | an independent, dated publication |
   | `recalled` | your training knowledge, with the approximate date of the fact; allowed for field products only, never for the stack |

   A cell scored 4 or 5 on `documented` evidence alone says so.
5. **Unverifiable claims are listed, never scored.** A claim no public source supports, or one
   that only private material could settle, goes in §10.7. List its source, why it cannot be
   verified, and the cell it would touch. Then score that cell as if the claim were absent.
6. **Absence of evidence.** Where you find no public evidence (of adoption, an integration, a
   legal entity), score it as absent and write "no public evidence", never "none exists".
7. **The same standard for every product.** A field product scored from fewer than two sources is
   marked `thin`.
8. **Without browsing,** work from the attached files only. Name every source in §4 that you did
   not see, and do not fill the stack's gaps from memory.

## 3. What is scored: the knowgov stack, as one dot

The stack is five public repositories, scored together. The roles below are as the project
describes itself; test them.

| repository | role, as described | pin (latest `main`, 2026-11-06) | latest release |
|---|---|---|---|
| [fdurieux/knowgov](https://github.com/fdurieux/knowgov) | The platform. It holds statements drawn from design documents, each with its source, status and verification. A gate answers PROCEED, QUALIFIED or BLOCKED on whether an AI assistant may build on them. It also has an MCP server, CI templates and a demo stack. | `b44b9bdfabdce36b7eea2253554a59a244b81582` | `v0.7.0` |
| [fdurieux/ieam-register](https://github.com/fdurieux/ieam-register) | An enterprise architecture's identities, typed relationships and approvals, kept in git. | `0826ebc861fb68fc8737070d1eb9babc786ce630` | `v0.2.12` |
| [fdurieux/pumllint](https://github.com/fdurieux/pumllint) | A PlantUML linter and maturity scorer on PyPI; knowgov imports its parser. Also holds the record of the proof-of-concept experiment. | `b0ce75f68ef1b1300e5765847c035823dac580bb` | `v0.35.0` |
| [fdurieux/aris2puml](https://github.com/fdurieux/aris2puml) | Turns ARIS exports into PlantUML. | `main` on your run date (record the commit) | see its tags |
| [fdurieux.github.io](https://fdurieux.github.io/) ([repo](https://github.com/fdurieux/fdurieux.github.io)) | "Legible": the programme's site and its systemic impact model. | `main` on your run date | — |

If you score another commit, say which and why.

## 4. Sources to read

Raw URLs are at the pins in §3, so an operator can fetch and attach them unchanged. Sizes are
approximate.

### 4.1 knowgov, base `https://raw.githubusercontent.com/fdurieux/knowgov/b44b9bdfabdce36b7eea2253554a59a244b81582/`

| file | size | status |
|---|--:|---|
| `README.md` | 3 KB | required |
| `VERSION` | — | required |
| `CHANGELOG.md`: the release policy is its opening paragraph, and each release has a "Known limits" section | 72 KB | required |
| `SECURITY.md` | 1 KB | required |
| `docs/guide.md`, the adopter's guide | 46 KB | required |
| `docs/security.md`, data flows, permissions, dependencies | 41 KB | required |
| `instance/README.md`: an organisation's own instance, the CI templates, the MCP tools | 83 KB | required |
| `docs/lighthouse-evaluation.md`, the evaluation protocol | 16 KB | optional |
| `demo/README.md` | 62 KB | optional |
| `subjects/README.md` | 17 KB | optional |
| `.github/workflows/tests.yml`, `release.yml`, `harness.yml`, `demo.yml` | 1–39 KB each | optional |
| the code under `harness/` and `tests/` | — | browse if you can; not for attachment |

### 4.2 ieam-register, base `https://raw.githubusercontent.com/fdurieux/ieam-register/0826ebc861fb68fc8737070d1eb9babc786ce630/`

| file | size | status |
|---|--:|---|
| `README.md` | 8 KB | required |
| `METAMODEL.md` | 5 KB | required |
| `metamodel/types.toml` | 3 KB | required |
| `mapping/matrix.toml`, the support status of each export route | 2 KB | required |
| `tools/impact.py`, the impact walk | 10 KB | optional |
| `decisions/` (one file per decision) | — | optional |

### 4.3 pumllint and aris2puml

| file | size | status |
|---|--:|---|
| `https://raw.githubusercontent.com/fdurieux/pumllint/b0ce75f68ef1b1300e5765847c035823dac580bb/docs/neo4j-governed-knowledge-evaluation.md`, the experiment's record: what was measured, with what design, and what it claims | 91 KB | required |
| `https://raw.githubusercontent.com/fdurieux/aris2puml/main/README.md` | — | required |
| `https://raw.githubusercontent.com/fdurieux/pumllint/b0ce75f68ef1b1300e5765847c035823dac580bb/README.md` (mind rule 2.3) | 57 KB | optional |

### 4.4 Public pages

- <https://github.com/fdurieux/knowgov/releases> and <https://github.com/fdurieux/knowgov/tags>
- <https://github.com/fdurieux/knowgov/actions>: the CI history
- <https://github.com/fdurieux/knowgov/pkgs/container/knowgov>: the published image
- <https://pypi.org/project/pumllint/> and <https://pypistats.org/packages/pumllint>

### 4.5 Public metrics as fetched by the operator, 2026-11-06

These are raw counts from GitHub's search API and pypistats' API. Re-check them if you can browse.
They are `observed` by the operator, not by you.

| repository | stars | forks | open issues and PRs | licence GitHub detects | created | last push |
|---|--:|--:|--:|---|---|---|
| fdurieux/knowgov | 0 | 0 | 3 | GPL-3.0 | 2026-11-01 | 2026-11-06 |
| fdurieux/ieam-register | 0 | 0 | 0 | none detected | 2026-10-30 | 2026-11-06 |
| fdurieux/pumllint | 1 | 0 | 6 | GPL-3.0 | 2026-07-22 | 2026-11-06 |
| fdurieux/aris2puml | 0 | 0 | 1 | GPL-3.0 | 2026-09-04 | 2026-10-30 |
| fdurieux/fdurieux.github.io | 0 | 0 | 0 | none detected | 2026-10-26 | 2026-10-29 |

pumllint downloads, from pypistats' "recent" endpoint as returned: last day 228, last week 1,463,
last month 1,028. pypistats counts include mirrors and CI.

knowgov's tags: `v0.1.0` through `v0.7.0`. Their dates are in `CHANGELOG.md`.

## 5. The category: test it before you use it

**Working definition.** Products that hold what an organisation has *declared* about its
architecture and processes (capabilities, products, journeys, processes, applications, data,
organisation and the relationships between them), and make it usable by AI agents and delivery
pipelines with machine-readable trust.

**Before scoring, say:**
- whether this is a coherent category, or the home team's invention;
- where an analyst would actually file the stack: enterprise architecture tools, data or AI
  governance, internal developer portals, spec-driven development, digital twin of an
  organisation, or elsewhere;
- whether that changes the field.

This is an analogue of an analyst's quadrant: claim no Gartner placement for anyone.

## 6. The field

Score every product below. You may add products, with a reason. You may argue that one does not
belong, but score it anyway.

| # | product |
|--:|---|
| 1 | SAP LeanIX + SAP Signavio |
| 2 | Palantir Ontology / AIP |
| 3 | Celonis Process Intelligence Graph / AgentC |
| 4 | Bizzdesign |
| 5 | Atlan |
| 6 | Ardoq |
| 7 | FINOS CALM |
| 8 | Backstage / Port |
| 9 | GitHub Spec Kit / AWS Kiro |
| 10 | Structurizr / LikeC4 |
| 11 | Neo4j |
| 12 | ServiceNow |
| 13 | Collibra |
| 14 | Microsoft Fabric IQ |
| 15 | ARIS |
| 16 | Orbus |
| 17 | Avolution |
| 18 | Sparx Systems |

## 7. The method

### 7.1 Axes and scale

There are eight criteria, each scored as an **integer from 0 to 5**. Vision is V1 + V2 + V3 + V4
and Execute is E1 + E2 + E3 + E4, each from 0 to 20, unweighted. On the quadrant, Vision is the x
axis and Execute the y axis.

### 7.2 Vision: what the product does and where it is going, as built or credibly specified

- **V1. Declarative model and identity.** A typed model of capabilities, products, journeys,
  processes, applications, data and organisation, and their relationships. It also covers stable
  identifiers across the tools that author the content, lifecycle states, and impact traversal
  across the model.
- **V2. Machine-readable trust controls.** Provenance, ownership, status, freshness, conflict
  handling, audit, policy mapping.
- **V3. Enforceable decisions in agent and delivery workflows.** Policy, permissions, approvals,
  exceptions, audit, integration breadth.
- **V4. Agent grounding and openness.** How agents and tools consume it (MCP, APIs, query
  languages); open formats, standards and interchange; licence terms that let others build on it.

**Vision anchors.**

| score | meaning |
|--:|---|
| 0 | absent |
| 1 | named or planned only |
| 2 | some elements of the criterion present and working |
| 3 | most elements present and working |
| 4 | all elements present and working, and a clear differentiator |
| 5 | defines the criterion for the field; others would be measured against it |

Vision does not require adoption. Where a Vision score rests only on a demo or synthetic content,
say so in the cell.

### 7.3 Execute: the ability to deliver it to organisations now

**E1. Product maturity:** release history, interface stability, security posture, documentation,
operability, test and CI evidence, production readiness.

| score | meaning |
|--:|---|
| 0 | idea |
| 1 | prototype or pre-release; interfaces still changing |
| 2 | tagged releases, tests and CI, security reviewed; no production user |
| 3 | generally available, stable interfaces, in production somewhere |
| 4 | mature product, service levels, years in market |
| 5 | the field's most mature |

**E2. Adoption:** customers, installations, users, community, downloads, references.

| score | meaning |
|--:|---|
| 0 | no public evidence of a user |
| 1 | a handful of users or pilots, modest downloads |
| 2 | tens of organisations |
| 3 | hundreds |
| 4 | thousands |
| 5 | market-leading share |

**E3. Integrations with systems of record and delivery tools:** connectors to EA and process
tools, data catalogues and CMDBs; CI platforms; agent and IDE hosts; marketplaces.

| score | meaning |
|--:|---|
| 0 | none |
| 1 | built, but not verified against a real installation |
| 2 | a few verified |
| 3 | a broad verified set, across systems of record and delivery tools |
| 4 | broad, plus marketplace presence and a partner ecosystem |
| 5 | the hub others integrate with |

**E4. Sustaining backing:** company or foundation, funding, headcount, maintainers, support
terms, legal entity, roadmap credibility.

| score | meaning |
|--:|---|
| 0 | an individual, no entity |
| 1 | one maintainer or a very small team; no funding, no support terms |
| 2 | a small company or funded team; support offered |
| 3 | an established company or foundation with a sustaining model |
| 4 | a large vendor, substantial investment |
| 5 | among the field's largest backers |

### 7.4 The quadrant

Both midlines sit at 10.

| quadrant | Vision | Execute |
|---|---|---|
| Leaders | ≥ 10 | ≥ 10 |
| Challengers | < 10 | ≥ 10 |
| Visionaries | ≥ 10 | < 10 |
| Niche players | < 10 | < 10 |

"The corner" means Vision ≥ 16 and Execute ≥ 16. Say who, if anyone, is in it.

## 8. The two placements of the stack

1. **Now**, at the pins.
2. **As a v1.0.** The project's release policy is the opening paragraph of knowgov's
   `CHANGELOG.md`.
   - **List the conditions you take a v1.0 to require.** Draw on that policy and on what an
     organisation buying in this category would expect. Mark each condition `maintainer`, if the
     maintainer can meet it alone, or `third party`, if it needs someone else (a user, a vendor, a
     partner, a legal counterparty). For each, cite the public evidence of where it stands today.
   - **Score the stack twice:**
     - **v1.0-minimal:** the same product with its public interfaces declared stable, and nothing
       else changed;
     - **v1.0-as-defined:** every condition you listed met.
   - **For each score, give** the quadrant, the cells that decide it, and its weakest assumption.
     Assume the field does not move.

## 9. Questions every report must answer about the stack

Answer each with evidence. The list covers strengths and weaknesses alike, and you may add to it.

- Is any of its content real, or is all of it synthetic?
- Which of the register's relationship types does impact analysis traverse? Which does it skip,
  and by what rule?
- What does the gate decide, from which inputs, with which exit codes? Is its effect on an AI
  assistant measured anywhere, with what design and sample, and what does that measurement claim
  and not claim?
- What can an agent reach over MCP? Can it write anything? Which protocol revisions are served,
  and is conformance tested?
- Which export routes from systems of record exist? Which have run against a real installation?
- Which delivery integrations exist (CI platforms, agent hooks, code scanning)? Which have run on
  a real runner?
- How many releases, over what period? How many changed a public interface?
- What security review happened, by whom, and what remains open?
- How many people contribute, and how much is written by an AI assistant? Is there a legal
  entity, support terms, and a licence that lets a vendor embed an adapter?
- What do the public metrics show (§4.5)?

## 10. Report structure (fixed)

Write one Markdown report with exactly these sections, in this order:

1. **Runner:** model, version, effort, whether you could browse, the date.
2. **Sources:** every source read, with its URL, pin or date. List separately those in §4 you did
   not see, and the contamination log (rule 2.3).
3. **Category verdict** (§5).
4. **The axes as applied:** any deviation from §7, and why.
5. **Placement now.**
   - A table for every product: V1–V4, E1–E4, V, E, quadrant, `thin`.
   - For the stack, one line per cell: the score, the justification, the evidence class and the
     citation.
   - For each field product, a short paragraph per axis with citations, plus one line per cell
     scored 0, 1, 4 or 5.
6. **Placement as a v1.0** (§8):
   - the conditions, each with its control and its current evidence;
   - the two score rows, each with its quadrant, deciding cells and weakest assumption.
7. **Unverifiable claims:** each with where it was claimed, why it cannot be verified, and which
   cell it would touch. None is scored.
8. **Errors found in the sources:** a stale document or a number that does not add up, with its
   location. Report them; do not fix them.
9. **What would change my mind:** the three facts that would move the stack most, in either
   direction.
10. **JSON:** one block in this shape, integers only, with every product present:

```json
{
  "runner": {"model": "", "version": "", "effort": "", "browsing": false, "date": "YYYY-MM-DD"},
  "pins": {"fdurieux/knowgov": "", "fdurieux/ieam-register": "", "fdurieux/pumllint": "", "fdurieux/aris2puml": "", "fdurieux/fdurieux.github.io": ""},
  "category": {"coherent": true, "analyst_category": "", "note": ""},
  "now": [
    {"product": "knowgov stack", "V1": 0, "V2": 0, "V3": 0, "V4": 0, "E1": 0, "E2": 0, "E3": 0, "E4": 0,
     "V": 0, "E": 0, "quadrant": "", "thin": false,
     "evidence": {"V1": {"class": "observed", "source": ""}}}
  ],
  "v1_conditions": [{"condition": "", "control": "maintainer", "status_today": "", "source": ""}],
  "v1": [
    {"reading": "v1.0-minimal", "V1": 0, "V2": 0, "V3": 0, "V4": 0, "E1": 0, "E2": 0, "E3": 0, "E4": 0,
     "V": 0, "E": 0, "quadrant": "", "deciding_cells": [], "weakest_assumption": ""},
    {"reading": "v1.0-as-defined", "V1": 0, "V2": 0, "V3": 0, "V4": 0, "E1": 0, "E2": 0, "E3": 0, "E4": 0,
     "V": 0, "E": 0, "quadrant": "", "deciding_cells": [], "weakest_assumption": ""}
  ],
  "unverifiable": [{"claim": "", "where": "", "why": "", "cell": ""}],
  "contamination": [{"file": "", "saw": "", "influence": "none"}]
}
```

## 11. Out of bounds

- **Read only.** No issue, pull request, comment, review, star, fork or watch on any repository:
  GitHub notifies the owner. No sign-up, and no message to anyone named in the sources.
- **Run nothing that calls a paid model API.** knowgov's "arms" do so when a model key is set.
- **Publish nothing.**
