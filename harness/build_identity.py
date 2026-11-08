"""Which knowgov this is (task-0227): ``identity(root)`` gives ``{version, commit, describe}``, each None
when it cannot be known, read from the running copy's own files and never inferred.

    python harness/build_identity.py [ROOT]     # prints the JSON the page serves

- ``version`` is ``VERSION``.
- ``commit`` and ``describe``, in order of what holds:
  1. ``.knowgov-build.json`` at the root, which ``demo/Dockerfile`` writes from its build arguments
     ``KG_BUILD_COMMIT`` and ``KG_BUILD_DESCRIBE`` (``release.yml`` passes the tag's commit and the tag);
  2. ``git`` itself, when the binary and ``.git`` are both there (a checkout run without Docker):
     ``rev-parse HEAD`` and ``describe --tags --always``;
  3. ``.git``'s own files, without the binary (the image: ``Dockerfile.dockerignore`` lets in ``HEAD``,
     ``refs`` and ``packed-refs`` only): HEAD's commit, and a describe only when a tag names that
     commit exactly. The distance from a tag needs the commit graph, which those files do not carry,
     so it reads unknown.
- A describe is kept only when it names a tag and agrees with the commit (``<tag>`` on the commit
  itself, or ``<tag>-<n>-g<prefix of the commit>``); a bare hash (a shallow or tagless clone) or a
  describe recorded for another commit reads unknown.

Standard library; no network; read once at start by the page.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_FILE = ".knowgov-build.json"
_HEX = re.compile(r"^[0-9a-f]{40}$")
_DESCRIBE = re.compile(r"^(?P<tag>.+?)(?:-(?P<n>\d+)-g(?P<sha>[0-9a-f]{4,40}))?$")


def _read(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None


def _git_dir(root: Path) -> Path | None:
    """``.git`` as a folder, or the folder a worktree's ``.git`` file points at."""
    g = root / ".git"
    if g.is_dir():
        return g
    text = _read(g) if g.is_file() else None
    if text and text.startswith("gitdir:"):
        d = Path(text.split(":", 1)[1].strip())
        d = d if d.is_absolute() else (root / d)
        return d if d.is_dir() else None
    return None


def _packed(git: Path) -> list[tuple[str, str, str | None]]:
    """``packed-refs`` as (ref, sha, peeled sha or None)."""
    out: list[list] = []
    for line in (_read(git / "packed-refs") or "").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if line.startswith("^") and out:
            out[-1][2] = line[1:].strip()
            continue
        sha, _, ref = line.partition(" ")
        out.append([ref.strip(), sha.strip(), None])
    return [tuple(x) for x in out]


def _ref(git: Path, ref: str) -> str | None:
    loose = _read(git / ref)
    if loose and _HEX.match(loose):
        return loose
    return next((sha for r, sha, _ in _packed(git) if r == ref and _HEX.match(sha)), None)


def from_git_files(root: Path) -> tuple[str | None, str | None]:
    """(commit, describe) from ``.git``'s files alone: describe only for a tag on the commit itself."""
    git = _git_dir(root)
    if git is None:
        return None, None
    head = _read(git / "HEAD") or ""
    commit = head if _HEX.match(head) else _ref(git, head[4:].strip()) if head.startswith("ref:") else None
    if commit is None:
        return None, None
    tags = set()
    for ref, sha, peeled in _packed(git):
        if ref.startswith("refs/tags/") and commit in (sha, peeled):
            tags.add(ref[len("refs/tags/"):])
    tdir = git / "refs" / "tags"
    if tdir.is_dir():   # a loose tag file holds the commit for a lightweight tag; an annotated one's object is not here
        for p in tdir.rglob("*"):
            if p.is_file() and _read(p) == commit:
                tags.add(p.relative_to(tdir).as_posix())
    return commit, (sorted(tags)[-1] if tags else None)


def from_git_binary(root: Path) -> tuple[str | None, str | None]:
    """(commit, describe) from ``git`` itself; (None, None) when it is not there or does not answer."""
    exe = shutil.which("git")
    if exe is None or _git_dir(root) is None:
        return None, None

    def run(*args: str) -> str | None:
        try:
            p = subprocess.run([exe, "-C", str(root), *args], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return None
        return p.stdout.strip() if p.returncode == 0 else None
    top = run("rev-parse", "--show-toplevel")
    if not top or Path(top).resolve() != Path(root).resolve():
        return None, None   # git answered for an enclosing repository, or for none: not this copy's
    commit = run("rev-parse", "HEAD")
    return (commit if commit and _HEX.match(commit) else None), run("describe", "--tags", "--always")


def checked(commit: str | None, describe: str | None) -> str | None:
    """The describe when it names a tag and agrees with the commit; None otherwise, never a guess."""
    if not describe:
        return None
    m = _DESCRIBE.match(describe.strip())
    if not m or _HEX.match(describe) or re.fullmatch(r"[0-9a-f]{4,40}", describe):
        return None   # a bare hash: no tag reached (a shallow or tagless clone)
    if m.group("sha"):
        return describe if commit and commit.startswith(m.group("sha")) else None
    return describe if commit else None   # an exact tag stands only beside the commit it was read with


def identity(root: Path | None = None) -> dict:
    root = Path(root or ROOT)
    version = _read(root / "VERSION") or None
    try:
        rec = json.loads((root / BUILD_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        rec = {}
    rec = rec if isinstance(rec, dict) else {}
    rc = rec.get("commit") if isinstance(rec.get("commit"), str) and _HEX.match(rec.get("commit") or "") else None
    rd = (rec.get("describe") or "").strip() if isinstance(rec.get("describe"), str) else ""
    commit, describe = rc, None
    if commit is None:
        commit, describe = from_git_binary(root)
    if commit is None:
        commit, describe = from_git_files(root)
    if rd:
        # a describe recorded at build: its -g<sha> must agree with the commit; an exact tag recorded
        # without its commit stands only if the files read here show that tag on this commit
        exact = not _DESCRIBE.match(rd).group("sha")
        describe = rd if (rc or not exact or describe == rd) else None
    return {"version": version, "commit": commit, "describe": checked(commit, describe)}

if __name__ == "__main__":
    print(json.dumps(identity(Path(sys.argv[1]) if len(sys.argv) > 1 else None), indent=1))
