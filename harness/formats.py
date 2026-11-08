"""The format version of an instance's inputs, read by one rule (task-0174, decision-0023, doc-0028 G9-2).

Three kinds of input carry a version:

- **a subject root**: ``subject.toml``'s ``[format] version = N`` covers the subject's own configuration,
  ``subject.toml`` itself, ``scenarios.toml``, ``plants.toml``, ``queries.toml`` and the register map it names;
- **an instance file**: ``code_map.toml`` and ``connectors.toml`` each carry a top-level ``format = N``;
- **a record**: each capture and each review file carries a top-level ``format = N``, stamped by
  ``harness/capture.py`` ``capture_toml`` and ``harness/review.py`` ``review_toml``, since a record outlives the
  version that wrote it.

The rule, the same for every reader:

- a missing version reads as the current one (until 1.0, decision-0023);
- an equal or lower one is read (none lower exists yet: a migration note follows the first time one moves);
- a higher one is refused, ``FormatTooNew``, naming the file, its version and the one this knowgov reads; the
  commands answer it with exit 2, "cannot run" (``harness/cli_exit.py``, ``tools/_outcomes.py``), never a misreading;
- a version that is not a whole number of at least 1, or a ``[format]`` that is not a table in ``subject.toml``
  (a top-level ``format`` in the others), is ``FormatError``, exit 2 as well.

Standard library only; nothing here reads a file.
"""
from __future__ import annotations

# what this knowgov writes and reads, per kind of input; a kind moves its own number
CURRENT = {"subject": 1, "code_map": 1, "connectors": 1, "capture": 1, "review": 1}
SUBJECT, CODE_MAP, CONNECTORS, CAPTURE, REVIEW = "subject", "code_map", "connectors", "capture", "review"


class FormatError(ValueError):
    """An input's format version cannot be read: a failure to run, exit 2."""


class FormatTooNew(FormatError):
    """An input written for a newer knowgov: refused rather than misread, exit 2."""


def declared(doc: dict, kind: str):
    """The version as the file writes it, None when it writes none (``[format] version`` for a subject,
    a top-level ``format`` for the rest)."""
    if kind == SUBJECT:
        t = doc.get("format")
        if t is None:
            return None
        if not isinstance(t, dict):
            raise FormatError("[format] must be a table, [format] version = N")
        return t.get("version")
    return doc.get("format")


def version(doc: dict, where: str, kind: str) -> int:
    """The version ``doc`` (the parsed ``where``) is read at: its own, or the current one when it names none.
    Raises ``FormatTooNew`` for a newer one and ``FormatError`` for one that is not a version."""
    cur = CURRENT[kind]
    try:
        v = declared(doc, kind)
    except FormatError as e:
        raise FormatError(f"{where}: {e}") from None
    if v is None:
        return cur
    key = "[format] version" if kind == SUBJECT else "format"
    if isinstance(v, bool) or not isinstance(v, int) or v < 1:
        raise FormatError(f"{where}: {key} = {v!r} is not a format version (a whole number, 1 or more)")
    if v > cur:
        raise FormatTooNew(f"{where}: {key} = {v}, and this knowgov reads {kind} format {cur} and earlier; "
                           "upgrade knowgov to one that reads it, or keep the file at the version this one reads "
                           "(instance/README.md, \"Format versions\")")
    return v
