"""The one rule for a knowledge key, ``entity|attribute`` (task-0296, decision-0034 choice 3(a)).

Each side of the ``|`` is non-empty and holds no ``|``, no whitespace and no format character (U+200B to U+200D,
U+2060, U+FEFF), which would otherwise pass as part of a name and read absent at the gate. ``PATTERN`` is the
JSON Schema ``pattern`` of the MCP tools' ``keys`` items, written so ECMA-262 and Python read it alike
(``\\uXXXX`` escapes, anchored); ``KEY_RE`` is the same pattern compiled, which ``tools/check_subject.py`` uses.
``tests/test_key_rule.py`` holds the three equal. Standard library only.
"""
from __future__ import annotations

import re

SIDE = r"[^|\s\u200b-\u200d\u2060\ufeff]+"   # \uXXXX escapes, read alike by Python and ECMA-262
PATTERN = rf"^{SIDE}\|{SIDE}$"
KEY_RE = re.compile(rf"{SIDE}\|{SIDE}")   # for fullmatch: PATTERN's body, unanchored
DESCRIPTION = ("entity|attribute: one '|', each side non-empty, with no '|', no whitespace and no format character "
               "(U+200B to U+200D, U+2060, U+FEFF)")


def is_key(value) -> bool:
    """Whether ``value`` is a key by the one rule."""
    return isinstance(value, str) and KEY_RE.fullmatch(value) is not None
