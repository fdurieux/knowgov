"""Run a test with a named subject as the page's current subject (task-0032.01).

The page modules read the subject as a value, so a test that is about CargoQuote's record says
so, and passes whatever subject ``KG_SUBJECT`` names for the process. Not a test module itself:
the runner imports ``test_*.py`` only.
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "harness", ROOT / "demo" / "app"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import page_subject  # noqa: E402
import subject  # noqa: E402

CARGO_QUOTE = subject.Subject(ROOT / "subjects" / "cargo_quote")


def on(s):
    """Decorate a test to run with ``s`` as the current subject."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            with page_subject.using(s):
                return fn(*a, **kw)
        return wrapper
    return deco


on_cargo_quote = on(CARGO_QUOTE)
