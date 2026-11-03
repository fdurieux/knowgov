"""decision-0003: VERSION holds a SemVer version, CHANGELOG.md's top section is that version, and
the release workflow publishes the image under the tag and checks the tag against both."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_version_and_changelog_agree():
    v = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+", v), v
    top = next(ln for ln in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines() if ln.startswith("## "))
    assert top.startswith(f"## {v} — "), top


def test_the_release_workflow_tags_the_image_and_checks_the_version():
    wf = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert 'tags: ["v*"]' in wf and "ghcr.io/fdurieux/knowgov:${{ github.ref_name }}" in wf
    assert 'test "${GITHUB_REF_NAME}" = "v${v}"' in wf and "CHANGELOG.md" in wf
