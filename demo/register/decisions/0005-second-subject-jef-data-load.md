# 0005 — The second subject: the J-F data-load kit as source system `jef_kit`

Date: 2026-11-01. State: approved (fdurieux). Supersedes: none.

## Decision

The J-F data-load kit of pumllint's recreation experiment (`recreate_experiment/kit`: 163 EARS
requirements, prose contracts, DMN decision tables, PlantUML diagrams, a Gherkin suite tagged with
the requirement ids) is the organisation's second subject, as decision 0004 provides: a source
system `jef_kit` in `metamodel/sources.toml`, its export `exports/jef_kit/2026-11-01` (the digests of the
kit's documents at pumllint `3375197`), and one slice of nodes and links beside CargoQuote's. The
program is the maintainer's own daily asset load, read as an oracle and never changed; the kit was
reverse-engineered from its code alone and rebuilt from the kit alone. Fixtures are synthetic. No
bank data.

The slice: one owner (`ORG-0003`); a capability domain with two capabilities (acquire end-of-day
bars, report store health); a portfolio with one product, the seam frame the downstream model
reads; a journey with three steps (sync, check, publish); the daily chain as the process with the
sync run and the status run as subprocesses and one raw-basis leg as an activity, each with its
diagram of record in the kit; the `jef-data` application with four modules (sync, health, store,
collectors); an information domain with four entities (universe, series, corporate actions, seam
frame). Twenty-eight links of nine types; every link's evidence cites the export manifest, a kit
document and the requirement ids it rests on (`jef_kit:requirements.json#JDL-nnn`), the form the
knowgov footprint joins on.

## Why

A register proven on one subject is not proven (decision 0004). The kit already carries the
documents a register link needs as evidence, with ids; the degradation test of 2026-10-28 planted
fifteen defects in those documents and graded what reached the code, so the platform's second
subject has a record to read against. Ids continue the register's sequences; nothing of
CargoQuote's slice changes.

## Approvals recorded by this decision

Every node and link whose `approval.record` names this file.
