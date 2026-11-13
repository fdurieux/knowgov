"""The one rule for a knowledge key, ``entity|attribute`` (task-0296, decision-0034 choice 3(a); task-0297, its
Amendment A1).

Each side of the ``|`` is non-empty and holds only characters up to U+FFFF (the Basic Multilingual Plane; every
character above it is refused, the maintainer's "astral (a) as advised", decision-0034) outside these
general categories: Cc (control characters, NUL, U+001C to U+001F and U+0085 included), Cf (format characters:
the zero-width ones, the bidi marks and overrides such as U+200E and U+202E, the soft hyphen U+00AD, U+2061,
U+180E, U+FEFF), Zs, Zl and Zp (every space and line or paragraph separator), and Cs (surrogates); and no ``|``.
Such a character would otherwise pass as part of a name and read absent at the gate. Combining marks (Mn) are
kept: an accented name in NFD needs them.

Two keys that are canonically equivalent are one key; knowgov stores and reports the NFC form (task-0301,
decision-0034 Amendment A2). ``normalise`` turns a key to NFC (not NFKC) wherever one enters: the MCP tools'
``key`` and ``keys``, the task classes, the register map, the verification map, the three-valued keys, the
mappers' entities and predicates (``extract.mapped_text`` composes a document before it is mapped), captures,
reviews, proposals, code-header citations and every command's ``--keys``; the rule is checked after it.

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
import unicodedata

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
               "(Unicode categories Cc, Cf, Zs, Zl, Zp); two keys that are canonically equivalent are one key, and "
               "knowgov stores and reports the NFC form")


def normalise(key):
    """``key`` in Unicode NFC (task-0301, decision-0034 Amendment A2): two keys that are canonically equivalent
    are one key, and knowgov stores and reports the NFC form. Not NFKC, which would merge full-width forms and
    ligatures into other names. A value that is not a string is returned as it is, for the rule to refuse."""
    return unicodedata.normalize("NFC", key) if isinstance(key, str) else key


def normalise_all(keys):
    """Each of ``keys`` normalised, in order; a value that is not a list is returned as it is."""
    return [normalise(k) for k in keys] if isinstance(keys, list) else keys


def is_key(value) -> bool:
    """Whether ``value``, once normalised, is a key by the one rule."""
    return isinstance(value, str) and KEY_RE.fullmatch(normalise(value)) is not None


def refusal(value) -> str | None:
    """Why ``value`` is not a key, else None (task-0316, N8): the rule holds of the value as written and of its NFC,
    so a key whose raw form fails is refused even when its NFC would pass (an astral compatibility character that
    composes into the BMP), and one whose NFC fails is refused too. The message names the value as written."""
    if isinstance(value, str) and KEY_RE.fullmatch(value) and KEY_RE.fullmatch(normalise(value)):
        return None
    return (f"{value!r} is not a key: a key is <entity>|<predicate>, one '|', no space and no control or format "
            "character, none above U+FFFF, as written and in NFC (key_rule)")


def did_you_mean(key, known) -> str:
    """task-0314 A-F10: `` (did you mean X?)`` for the nearest known key, else empty, so an unmodelled key does not read as a
    modelled absence."""
    import difflib
    near = difflib.get_close_matches(key if isinstance(key, str) else "", sorted(known), n=1, cutoff=0.8)
    return f" (did you mean {near[0]}?)" if near else ""


def did_you_mean_each(keys, known) -> str:
    """task-0314 R4: ``; did you mean X for A?; did you mean Y for B?`` for the keys that have a near one, each naming its key."""
    found = [(k, did_you_mean(k, known)[len(" (did you mean "):-2]) for k in keys]
    return "".join(f"; did you mean {n} for {k}?" for k, n in found if n)
