"""A fixture register change (task-0122), built in a temporary directory from the vendored register,
which is never edited: CAP-0001 deprecated by a fixture decision (0099, named on its state line as the
register names its own, ``state = "deprecated"   # decision 0006: ...``), its children moved to
CAP-0006 so the register's checker stays clean (its decision 0015), and REL-06001 (APP-0002 supports
PROC-0002) withdrawn. ``same`` copies the register with no state change at all.

    python tools/register_fixture.py changed <dir>    # or: same <dir>; prints the directory written
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDORED = ROOT / "demo" / "register"
TAG = "v0.2.11+fixture"
DECISION = "decisions/0099-fixture-freight-quoting-deprecated.md"


def _copy(dest: Path) -> Path:
    shutil.copytree(VENDORED, dest, ignore=shutil.ignore_patterns("__pycache__"))
    note = dest / "SOURCE.md"
    note.write_text(re.sub(r"^\| tag \| `v[^`]*`", f"| tag | `{TAG}`", note.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")
    return dest


def same(dest: Path) -> Path:
    """A register update with no state change: the copy, a comment added, nothing withdrawn."""
    _copy(dest)
    p = dest / "capabilities" / "CAP-0001.toml"
    p.write_text(p.read_text(encoding="utf-8") + "# reviewed, unchanged (fixture)\n", encoding="utf-8")
    return dest


def changed(dest: Path) -> Path:
    _copy(dest)
    (dest / DECISION).write_text("# 0099 — Freight quoting is deprecated (fixture)\n\nState: approved. A fixture for knowgov's "
                                 "task-0122: CAP-0001 is deprecated, its capabilities move under CAP-0006, and REL-06001 is withdrawn.\n",
                                 encoding="utf-8")
    cap = dest / "capabilities" / "CAP-0001.toml"
    cap.write_text(cap.read_text(encoding="utf-8").replace('state = "approved"', 'state = "deprecated"   # decision 0099: freight quoting is folded elsewhere', 1),
                   encoding="utf-8")
    for c in ("CAP-0002", "CAP-0003", "CAP-0004", "CAP-0005"):
        p = dest / "capabilities" / f"{c}.toml"
        p.write_text(p.read_text(encoding="utf-8").replace('parent = "CAP-0001"', 'parent = "CAP-0006"', 1), encoding="utf-8")
    rel = dest / "relationships" / "supports.toml"
    text = rel.read_text(encoding="utf-8")
    head, sep, tail = text.partition('id = "REL-06001"')
    tail = tail.replace('state = "approved"', 'state = "deprecated"', 1)
    rel.write_text(head + sep + tail, encoding="utf-8")
    return dest


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3 or sys.argv[1] not in ("changed", "same"):
        raise SystemExit("usage: register_fixture.py changed|same <dir>")
    print({"changed": changed, "same": same}[sys.argv[1]](Path(sys.argv[2])))
