"""One exit for the harness's commands (task-0200, doc-0030 F6: G6, R9).

    if __name__ == "__main__":
        import cli_exit
        sys.exit(cli_exit.run(main, "gate"))

The gate contract keeps exit 1 for a finding: a command that cannot do its job exits 2, never 1, and
never with a traceback as its only output. ``run`` calls ``main`` and maps what escapes it:

- a ``CannotRun`` of the command's own, ``review.WallClock`` (a pinned run reading the wall clock), a
  malformed or unreadable input (``ValueError``, ``OSError``, ``KeyError``, the JSON decoder's), an
  unwritable output and any other exception, to exit 2, the cause on stderr in one line,
  ``<tool>: cannot run: <cause>``;
- ``SystemExit`` passes through untouched (argparse's usage error is its own exit 2; a command's own
  ``sys.exit`` keeps its code), and so does ``KeyboardInterrupt``.

``guard(tool)``, called at the top of a command run as a script, before its own imports, does the same for
what fails while the module loads (a pin not installed): an exception that reaches the interpreter prints the
one line and the process exits 2.

``KG_TRACEBACK=1`` prints the traceback after the line, for a person debugging; nothing reads it.
Standard library only.
"""
from __future__ import annotations

import os
import sys
import traceback

CANNOT_RUN = 2
# raised to say "cannot run" in the command's own words: the message is the cause, no type name added
OWN = {"CannotRun", "WallClock", "LoadTooLarge", "ScratchUnavailable", "FormatError", "FormatTooNew"}


def cause(e: BaseException) -> str:
    text = str(e).strip()
    if type(e).__name__ in OWN and text:
        return text
    return f"{type(e).__name__}: {text}" if text else type(e).__name__


def guard(tool: str) -> None:
    """Exit 2, the cause in one line, for an exception that escapes to the interpreter (a failed import)."""
    def hook(kind, e, tb):
        if issubclass(kind, KeyboardInterrupt):
            return sys.__excepthook__(kind, e, tb)
        print(f"{tool}: cannot run: {cause(e)}", file=sys.stderr)
        if os.environ.get("KG_TRACEBACK") == "1":
            traceback.print_exception(kind, e, tb)
        sys.stderr.flush()
        sys.stdout.flush()
        os._exit(CANNOT_RUN)
    sys.excepthook = hook


def run(main, tool: str, *args) -> int:
    """``main(*args)``'s exit code, None read as 0; anything raised but SystemExit and KeyboardInterrupt
    mapped to exit 2 with its cause on stderr."""
    try:
        rc = main(*args)
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException as e:  # noqa: BLE001 - every failure to run is exit 2, never 1 (the finding's code)
        print(f"{tool}: cannot run: {cause(e)}", file=sys.stderr)
        if os.environ.get("KG_TRACEBACK") == "1":
            traceback.print_exc()
        return CANNOT_RUN
    return 0 if rc is None else int(rc)
