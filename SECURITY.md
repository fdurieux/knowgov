# Security policy

## Reporting a vulnerability

Report a vulnerability privately, through GitHub's private vulnerability reporting on this
repository: the **Security** tab, then **Report a vulnerability**. Do not open a public issue,
pull request or discussion for it. Say what you found, how to reproduce it, and which version
(`VERSION`, or the image tag `ghcr.io/fdurieux/knowgov:<tag>`) you ran.

The maintainer acknowledges a report within five working days, agrees a fix and a disclosure date
with the reporter, and publishes the fix as a release (decision-0003) whose `CHANGELOG.md`
section names the advisory.

Never put an organisation's own documents, register content, keys or any bank-related data in a
report. If a reproduction needs content, use the public, synthetic subjects under `subjects/` or
the example instance (`tools/example_instance.py`).

## Supported versions

knowgov is 0.x. Only the latest release, and `main`, receive fixes.

## What knowgov reads, stores and sends

[`docs/security.md`](docs/security.md) is the security description an adopter's reviewer reads:
the data flows of a private instance, what leaves the network under each model-endpoint setting,
the dependency and image pins and how they are kept current, and who may do what. Each claim
in it names the test that holds it, or says it is a practice the operator must follow.
