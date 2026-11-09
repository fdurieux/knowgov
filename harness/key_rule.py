"""The one rule for a knowledge key, ``entity|attribute`` (task-0296, decision-0034 choice 3(a); task-0297, its
Amendment A1).

Each side of the ``|`` is non-empty and holds only characters up to U+FFFF (the Basic Multilingual Plane; every
character above it is refused, the maintainer's "astral (a) as advised", decision-0034) outside these
general categories: Cc (control characters, NUL, U+001C to U+001F and U+0085 included), Cf (format characters:
the zero-width ones, the bidi marks and overrides such as U+200E and U+202E, the soft hyphen U+00AD, U+2061,
U+180E, U+FEFF), Zs, Zl and Zp (every space and line or paragraph separator), and Cs (surrogates); and no ``|``.
Such a character would otherwise pass as part of a name and read absent at the gate. Combining marks (Mn) are
kept: an accented name in NFD needs them.

The rule is written as the explicit ``\\uXXXX`` ranges a side may hold, never ``\\s``, ``\\d`` or ``\\w``, whose sets
differ between engines (Python's ``\\s`` holds U+001C to U+001F and U+0085, ECMA-262's does not). Because the
ranges stay inside the BMP and leave the surrogates out, a character beyond U+FFFF is refused alike by Python,
by ECMA-262 reading UTF-16 units and by ECMA-262 under its ``u`` flag: no key here needs one, and every Cc and Cf
character beyond the BMP (U+110BD, the tag characters) is refused with them. ``PATTERN`` is the JSON Schema
``pattern`` of the MCP tools' ``keys`` items, anchored; ``KEY_RE`` its body compiled, which
``tools/check_subject.py`` uses. ``tests/test_key_rule.py`` holds the ranges to every Cc and Cf code point the
running interpreter's Unicode tables name, so a later Unicode version cannot open a gap unseen. Standard library
only.
"""
from __future__ import annotations

import re

# The BMP less Cc, Cf, Zs, Zl, Zp, Cs and "|", from Unicode 15.1 (tests/test_key_rule.py regenerates and compares)
ALLOWED = (r"\u0021-\u007b\u007d-\u007e\u00a1-\u00ac\u00ae-\u05ff\u0606-\u061b\u061d-\u06dc\u06de-\u070e"
           r"\u0710-\u088f\u0892-\u08e1\u08e3-\u167f\u1681-\u180d\u180f-\u1fff\u2010-\u2027\u2030-\u205e\u2065"
           r"\u2070-\u2fff\u3001-\ud7ff\ue000-\ufefe\uff00-\ufff8\ufffc-\uffff")
SIDE = rf"[{ALLOWED}]+"
PATTERN = rf"^{SIDE}\|{SIDE}$"
KEY_RE = re.compile(rf"{SIDE}\|{SIDE}")   # for fullmatch: PATTERN's body, unanchored
REFUSED_CATEGORIES = ("Cc", "Cf", "Zs", "Zl", "Zp", "Cs")
DESCRIPTION = ("entity|attribute: one '|', each side non-empty, of characters up to U+FFFF (the Basic Multilingual "
               "Plane; none above it) with no '|', no space or separator and no control or format character "
               "(Unicode categories Cc, Cf, Zs, Zl, Zp)")


def is_key(value) -> bool:
    """Whether ``value`` is a key by the one rule."""
    return isinstance(value, str) and KEY_RE.fullmatch(value) is not None
