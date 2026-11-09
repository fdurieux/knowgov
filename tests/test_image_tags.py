"""task-0277 (decision-0033 choice 3, G9-17): the image's tags, stated once. A release is
ghcr.io/fdurieux/knowgov:vX.Y.Z, the tag release.yml publishes from github.ref_name once it equals v<VERSION>;
:latest is the last build of main, which demo.yml publishes with :<short-sha>, a build and not a contract.
The README and instance/README.md's contracts table say the same, and no document names another form."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"
IMAGE = "ghcr.io/fdurieux/knowgov"


def test_a_release_publishes_its_vX_Y_Z_tag_and_only_that():
    text = (WF / "release.yml").read_text(encoding="utf-8")
    assert re.search(rf"^\s+tags: {re.escape(IMAGE)}:\$\{{\{{ github\.ref_name \}}\}}$", text, re.M)
    assert 'test "${GITHUB_REF_NAME}" = "v${v}"' in text, "the tag is v<VERSION>, checked before anything is pushed"
    assert 'tags: ["v*"]' in text


def test_main_publishes_latest_and_its_short_sha():
    text = (WF / "demo.yml").read_text(encoding="utf-8")
    tags = re.findall(rf"^\s+{re.escape(IMAGE)}:(.+?)\s*$", text, re.M)
    assert tags == ["${{ steps.sha.outputs.short }}", "latest"], tags


def test_the_readme_and_the_contracts_table_state_the_one_scheme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    table = next(l for l in (ROOT / "instance" / "README.md").read_text(encoding="utf-8").splitlines()
                 if l.startswith("| the image's name and tags"))
    for text in (readme, table):
        assert f"`{IMAGE}:vX.Y.Z`" in text and "`:latest`" in text and "`:<short-sha>`" in text, text[:200]
        assert "not a contract" in text
    for doc in ("README.md", "instance/README.md", "demo/README.md", "docs/security.md", "CLAUDE.md"):
        text = (ROOT / doc).read_text(encoding="utf-8")
        assert not re.search(rf"{re.escape(IMAGE)}:<(?:version|tag)>", text), f"{doc} names a form other than :vX.Y.Z"
