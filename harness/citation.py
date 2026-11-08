"""The header citation of hand-written code (task-0124; doc-0015 §3): a comment line, near the top of
a file, naming the keys the file rests on.

    # knowgov-keys: entity|rule, entity|limit          (Python)
    // knowgov-keys: entity|rule, entity|limit         (Java)

The marker is ``knowgov-keys:``, after the language's line-comment prefix and optional blanks; the
keys are comma-separated, as the subject's keys name them (``entity|attribute``; a key holds no comma).
Only the first HEAD_LINES lines are read, so a citation is a header and not a remark in the body;
several citation lines add up, in order, without repeats. A citation line with no key is malformed.

Two languages: Python, the language of the subjects' own code, and Java, the language most enterprise
service code that consumes a register is written in. Java's ``//`` line comment is also Kotlin's,
C#'s, Go's, JavaScript's and TypeScript's, so another of them is one more row in COMMENT, not another
parser. A file whose suffix COMMENT does not hold has no citation to read (``None``, not ``[]``).

Standard library only; reads, never writes. ``harness/trace.py`` reads it (``register --cited`` and
``check``'s citation findings); what counts as a known key is the caller's.
"""
from __future__ import annotations

import re
from pathlib import Path

MARK = "knowgov-keys:"
HEAD_LINES = 30
COMMENT = {".py": "#", ".java": "//"}


class Malformed(ValueError):
    """a citation line that names no key"""


def language(path: str | Path) -> str | None:
    """The comment prefix for the file's suffix, or None when the convention does not cover it."""
    return COMMENT.get(Path(path).suffix.lower())


def parse(text: str, prefix: str) -> list[str]:
    """The keys the header cites, in order, no repeats; [] when it cites none. Raises Malformed."""
    line_re = re.compile(r"^\s*" + re.escape(prefix) + r"\s*" + re.escape(MARK) + r"(.*)$")
    keys: list[str] = []
    text = text.removeprefix("\ufeff")   # a byte-order mark before line 1 is not part of its comment (doc-0030 I12)
    for n, line in enumerate(text.splitlines()[:HEAD_LINES], 1):
        m = line_re.match(line)
        if not m:
            continue
        got = [k.strip() for k in m.group(1).split(",")]
        if not any(got) or not all(got):
            raise Malformed(f"line {n}: {MARK} names {'no key' if not any(got) else 'an empty key'}")
        keys += [k for k in got if k not in keys]
    return keys


def read(path: Path) -> list[str] | None:
    """The keys a file's header cites; None when its language is not covered. Raises Malformed."""
    prefix = language(path)
    if prefix is None:
        return None
    return parse(path.read_text(encoding="utf-8", errors="replace"), prefix)
