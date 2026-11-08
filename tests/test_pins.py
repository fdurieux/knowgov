"""Every image and every action is pinned to its bytes, and the watch-lists Dependabot reads agree
with the pins that install (task-0092; docs/security.md, Dependencies and pins). Standard library."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGEST = re.compile(r"[\w./-]+:[\w.-]+@sha256:[0-9a-f]{64}")   # name:tag@digest: the tag stays readable
SHA = re.compile(r"[\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d+(?:\.\d+)*")   # owner/repo@sha # vX.Y.Z

WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.y*ml")) + [
    ROOT / "instance" / "ci" / "preload-check.yml",
    ROOT / "instance" / "ci" / "github" / "action.yml",
]
DOCKERFILES = sorted((ROOT / "demo").glob("Dockerfile*"))
COMPOSE = sorted((ROOT / "demo").glob("docker-compose*.yml"))
CI_IMAGES = [ROOT / "instance" / "ci" / "gitlab" / "knowgov.gitlab-ci.yml"]


def _rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def _uses() -> list[tuple[str, str]]:
    """(file, rest of line) for every remote `uses:`; a local action (./...) is this checkout's bytes."""
    out = []
    for path in WORKFLOWS:
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*(?:-\s*)?uses:\s*(\S.*)$", line)
            if m and not m.group(1).startswith("./"):
                out.append((_rel(path), m.group(1).strip()))
    return out


def _images() -> list[tuple[str, str]]:
    """(file, reference) for every FROM and every pulled `image:`; a compose service that builds its
    image (the development override's knowgov:local) pulls nothing."""
    out = []
    for path in DOCKERFILES:
        for ref in re.findall(r"^FROM\s+(\S+)", path.read_text(encoding="utf-8"), re.M):
            out.append((_rel(path), ref))
    for path in COMPOSE + CI_IMAGES:
        text = path.read_text(encoding="utf-8")
        for block in re.split(r"\n(?=  \S|\S)", text):   # one top-level key, or one service, per block
            builds = re.search(r"^\s+build:", block, re.M)
            for ref in re.findall(r"^\s+image:\s*(\S+)", block, re.M):
                if not builds:
                    out.append((_rel(path), ref))
    return out


def test_every_image_is_pinned_by_digest_with_its_tag():
    images = _images()
    assert len(images) >= 5, images   # the base, Neo4j, the app, the gateway, the GitLab job's
    loose = [(f, r) for f, r in images if not DIGEST.fullmatch(r)]
    assert not loose, f"pin these by digest, as name:tag@sha256:<digest>: {loose}"


def test_every_remote_action_is_pinned_by_commit_sha_with_its_version():
    uses = _uses()
    assert uses, "no uses: found"
    loose = [(f, u) for f, u in uses if not SHA.fullmatch(u)]
    assert not loose, f"pin these by full commit SHA with '# vX.Y.Z' after: {loose}"


def test_each_action_and_image_has_one_pin_everywhere():
    """A Dependabot update moves .github/workflows only; the CI template and the other files must follow."""
    pins: dict[str, set[str]] = {}
    for _, u in _uses():
        name, rest = u.split("@", 1)
        pins.setdefault(name, set()).add(rest)
    for _, ref in _images():
        name = ref.split("@", 1)[0]
        pins.setdefault(name, set()).add(ref)
    split = {k: v for k, v in pins.items() if len(v) > 1}
    assert not split, split


def _pip_pins(text: str) -> dict[str, str]:
    return dict(re.findall(r'"?([A-Za-z][\w.-]*)==([\w.]+)"?', text))


def test_the_pip_watch_list_is_the_images_pins():
    listed = _pip_pins("\n".join(l for l in (ROOT / "demo" / "requirements.txt").read_text(encoding="utf-8").splitlines() if not l.startswith("#")))
    image = _pip_pins((ROOT / "demo" / "Dockerfile").read_text(encoding="utf-8"))
    assert listed == image, (listed, image)
    for path in (ROOT / ".github" / "workflows" / "harness.yml", ROOT / "instance" / "ci" / "gitlab" / "knowgov.gitlab-ci.yml"):
        theirs = _pip_pins(path.read_text(encoding="utf-8"))
        assert theirs and all(listed.get(k) == v for k, v in theirs.items()), (_rel(path), theirs)


def test_the_npm_watch_list_is_the_linters_pins():
    deps = json.loads((ROOT / "instance" / "ci" / "package.json").read_text(encoding="utf-8"))["dependencies"]
    wf = (ROOT / "instance" / "ci" / "preload-check.yml").read_text(encoding="utf-8")
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    env = dict(re.findall(r'^\s+([A-Z]+): "([\d.]+)"', wf, re.M))
    var = {"@stoplight/spectral-cli": "SPECTRAL", "markdownlint-cli2": "MARKDOWNLINT", "gplint": "GPLINT", "bpmnlint": "BPMNLINT", "dmnlint": "DMNLINT"}
    assert set(deps) == set(var), deps
    for pkg, version in deps.items():
        assert re.fullmatch(r"\d+\.\d+\.\d+", version), (pkg, version)   # exact, never a range
        assert env[var[pkg]] == version, pkg
        assert f'"{pkg}@{version}"' in harness, pkg


def test_dependabot_watches_the_five_ecosystems_weekly():
    text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    entries = re.findall(r"- package-ecosystem: (\S+)\n\s+director(?:y|ies): (\S+)[^\n]*\n\s+schedule:\n\s+interval: (\w+)", text)
    found = {eco: (d, i) for eco, d, i in entries}
    assert set(found) == {"pip", "npm", "docker", "docker-compose", "github-actions"}, found
    assert all(i == "weekly" for _, i in found.values()), found
    assert found["pip"][0] == "/demo" and (ROOT / "demo" / "requirements.txt").is_file()
    assert found["npm"][0] == "/instance/ci" and (ROOT / "instance" / "ci" / "package.json").is_file()
    assert found["docker"][0] == "/demo" and found["docker-compose"][0] == "/demo" and found["github-actions"][0] == "/"


RECORD_PINS = {"pumllint", "neo4j", "rdflib", "pyshacl", "openai",                     # the scored record
               "pandas", "numpy", "requests", "pyarrow", "pytest", "pytest-bdd"}       # the J-F kit's oracle


def test_dependabot_ignores_the_record_pins():
    """Record pins are frozen with the record and move only by a re-record, never by a routine bump;
    every other watched pin is a tool pin and stays proposed."""
    text = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    ignored = set(re.findall(r"- dependency-name: (\S+)", text))
    assert ignored == RECORD_PINS, ignored ^ RECORD_PINS
    listed = set(_pip_pins((ROOT / "demo" / "requirements.txt").read_text(encoding="utf-8")))
    assert RECORD_PINS <= listed and listed - RECORD_PINS == {"pyyaml"}, listed
