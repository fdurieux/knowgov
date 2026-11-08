"""task-0227: the page names the knowgov it runs, {version, commit, describe}, each None when unknown,
read once at start from the running copy's own files (harness/build_identity.py). Three cases: a checkout
run without Docker (git itself), a local image from a checkout (.git's HEAD, refs and packed-refs, which
Dockerfile.dockerignore lets in, and an optional describe recorded at build), and a release image (the
tag's commit and the tag, which release.yml records). The real local image is checked in demo.yml's stack
job. A part not known reads unknown: never a distance without the commit graph, never a bare hash as a
describe, never a describe recorded for another commit."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
import build_identity as bi  # noqa: E402
from _skip import skip  # noqa: E402

A = "7e113f0" + "a" * 33
B = "b" * 40
T = "c" * 40   # an annotated tag's own object


def _root(td: str, head: str = "ref: refs/heads/main", loose: dict | None = None, packed: str = "", version: str = "0.8.0") -> Path:
    r = Path(td) / "copy"
    (r / ".git" / "refs" / "heads").mkdir(parents=True)
    (r / ".git" / "refs" / "tags").mkdir(parents=True)
    (r / ".git" / "HEAD").write_text(head + "\n", encoding="utf-8")
    for ref, sha in (loose or {}).items():
        (r / ".git" / ref).parent.mkdir(parents=True, exist_ok=True)
        (r / ".git" / ref).write_text(sha + "\n", encoding="utf-8")
    if packed:
        (r / ".git" / "packed-refs").write_text(packed, encoding="utf-8")
    if version is not None:
        (r / "VERSION").write_text(version + "\n", encoding="utf-8")
    return r


def test_a_checkout_run_without_docker_reads_git_itself():
    if not shutil.which("git") or not (ROOT / ".git").exists():
        skip("git", "this copy is not a git checkout with git installed")
    got = bi.identity(ROOT)
    git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()  # noqa: E731
    assert got["version"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert got["commit"] == git("rev-parse", "HEAD")
    # a clone with tags gives v<tag>-<n>-g<sha>; a shallow or tagless one a bare hash, which reads unknown
    assert got["describe"] == bi.checked(got["commit"], git("describe", "--tags", "--always")), got
    if got["describe"]:
        assert re.fullmatch(r"v\d+\.\d+\.\d+(-\d+-g[0-9a-f]+)?", got["describe"]), got


def test_an_image_without_git_reads_head_and_refs_and_never_a_distance():
    with tempfile.TemporaryDirectory() as td:
        r = _root(td, loose={"refs/heads/main": A})
        assert bi.from_git_files(r) == (A, None), "the commit; no tag on it, and no graph to count a distance"
        assert bi.identity(r) == {"version": "0.8.0", "commit": A, "describe": None}
    with tempfile.TemporaryDirectory() as td:   # a fresh clone keeps the branch in packed-refs; a tag on it, annotated and peeled
        r = _root(td, packed=f"# pack-refs with: peeled fully-peeled sorted\n{A} refs/heads/main\n{T} refs/tags/v0.8.0\n^{A}\n{B} refs/tags/v0.7.0\n")
        assert bi.from_git_files(r) == (A, "v0.8.0")
        assert bi.identity(r)["describe"] == "v0.8.0"
    with tempfile.TemporaryDirectory() as td:   # actions/checkout: a detached HEAD; a lightweight tag on another commit
        r = _root(td, head=A, loose={"refs/tags/v0.7.0": B})
        assert bi.from_git_files(r) == (A, None)
    with tempfile.TemporaryDirectory() as td:   # an annotated loose tag: its object is not here, so it is not read as on the commit
        r = _root(td, loose={"refs/heads/main": A, "refs/tags/v0.8.0": T})
        assert bi.from_git_files(r) == (A, None)
    with tempfile.TemporaryDirectory() as td:   # no .git at all, or a HEAD that names no ref here
        r = Path(td) / "bare"
        r.mkdir()
        assert bi.identity(r) == {"version": None, "commit": None, "describe": None}
        r = _root(td, loose={})
        assert bi.identity(r) == {"version": "0.8.0", "commit": None, "describe": None}


def test_a_describe_recorded_at_build_stands_only_beside_its_commit():
    def rec(r: Path, **kw) -> dict:
        (r / bi.BUILD_FILE).write_text(json.dumps(kw), encoding="utf-8")
        return bi.identity(r)
    with tempfile.TemporaryDirectory() as td:
        r = _root(td, loose={"refs/heads/main": A}, version="0.9.0")
        # the release image: release.yml records the tag's commit and the tag
        assert rec(r, commit=B, describe="v0.9.0") == {"version": "0.9.0", "commit": B, "describe": "v0.9.0"}
        # a local build given KG_BUILD_DESCRIBE only: the commit from HEAD, the describe kept when it agrees
        assert rec(r, commit=None, describe="v0.8.0-277-g7e113f0")["describe"] == "v0.8.0-277-g7e113f0"
        assert rec(r, commit=None, describe="v0.8.0-12-gdeadbee")["describe"] is None, "recorded for another commit: a stale export"
        assert rec(r, commit=None, describe="v0.8.0")["describe"] is None, "an exact tag no ref here shows on this commit"
        assert rec(r, commit=None, describe="7e113f0")["describe"] is None, "a bare hash names no tag"
        assert rec(r, commit=None, describe=None) == {"version": "0.9.0", "commit": A, "describe": None}
        assert rec(r, commit="not-a-sha", describe=None)["commit"] == A, "a malformed record is not read"
        (r / bi.BUILD_FILE).write_text("{", encoding="utf-8")
        assert bi.identity(r)["commit"] == A


def test_the_image_records_what_its_build_was_given_and_lets_in_only_heads_and_refs():
    df = (ROOT / "demo" / "Dockerfile").read_text(encoding="utf-8")
    run = re.search(r'(?m)^RUN (python -c ".*knowgov-build\.json.*")$', df)
    assert run and 'ARG KG_BUILD_COMMIT=""' in df and 'ARG KG_BUILD_DESCRIBE=""' in df, "the two optional build args"
    assert df.index("ARG KG_BUILD_COMMIT") > df.rindex("pip install"), "last, so a new commit rebuilds only that layer"
    with tempfile.TemporaryDirectory() as td:   # the Dockerfile's own command, run here, gives a file identity reads
        r = _root(td, loose={"refs/heads/main": A})
        cmd = run.group(1).replace("/repo/.knowgov-build.json", str(r / bi.BUILD_FILE))
        for env, want in (({"KG_BUILD_COMMIT": B, "KG_BUILD_DESCRIBE": "v0.9.0"}, (B, "v0.9.0")), ({}, (A, None))):
            e = {k: v for k, v in os.environ.items() if not k.startswith("KG_BUILD_")} | env
            subprocess.run(["sh", "-c", cmd], check=True, env=e)
            got = bi.identity(r)
            assert (got["commit"], got["describe"]) == want, (env, got)
    ignore = [ln.strip() for ln in (ROOT / "demo" / "Dockerfile.dockerignore").read_text(encoding="utf-8").splitlines()
              if ln.strip() and not ln.startswith("#")]
    assert ".git" in ignore and {"!.git/HEAD", "!.git/refs", "!.git/packed-refs"} <= set(ignore), ignore
    assert not [x for x in ignore if x.startswith("!.git/") and x not in ("!.git/HEAD", "!.git/refs", "!.git/packed-refs")], "no objects, no config"
    rel = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "KG_BUILD_COMMIT=${{ github.sha }}" in rel and "KG_BUILD_DESCRIBE=${{ github.ref_name }}" in rel
    ov = (ROOT / "demo" / "docker-compose.override.yml").read_text(encoding="utf-8")
    assert ov.count("KG_BUILD_DESCRIBE: ${KG_BUILD_DESCRIBE:-}") == 2, "app and worker, the same image"
    assert bi.BUILD_FILE in (ROOT / ".gitignore").read_text(encoding="utf-8")
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert 'kg = subs["knowgov"]' in demo and 'kg["describe"] is None' in demo, "the stack job checks the local image"


def test_read_once_with_no_network_and_no_clock():
    src = (ROOT / "harness" / "build_identity.py").read_text(encoding="utf-8")
    for banned in ("urllib", "socket", "http", "datetime", "time.", "review.today"):
        assert banned not in src, banned
    server = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert server.count("build_identity.identity(") == 1 and re.search(r"(?m)^KNOWGOV = build_identity\.identity\(ROOT\)", server)


def test_api_subjects_carries_it_additively():
    sys.path[:0] = [str(ROOT / "demo" / "app")]
    import server
    from http.server import ThreadingHTTPServer
    import threading
    import urllib.request
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_address[1]}/api/subjects", timeout=60) as r:
            j = json.loads(r.read())
    finally:
        httpd.shutdown()
    assert set(j) == {"subjects", "current", "knowgov"}, j.keys()
    assert j["knowgov"] == server.KNOWGOV and set(j["knowgov"]) == {"version", "commit", "describe"}, j["knowgov"]


def test_the_header_says_each_case_and_unknown_where_unknown():
    node = shutil.which("node")
    if not node:
        skip("node", "node is not installed; the header is drawn by the page's own script")
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    fn = re.search(r"(?ms)^function knowgovLabel\(.*?^\}$", page).group(0)
    cases = {"checkout": {"version": "0.8.0", "commit": A, "describe": "v0.8.0-277-g7e113f0"},
             "release": {"version": "0.8.0", "commit": A, "describe": "v0.8.0"},
             "image": {"version": "0.8.0", "commit": A, "describe": None},
             "nothing": {"version": "0.8.0", "commit": None, "describe": None},
             "no_version": {"version": None, "commit": None, "describe": None},
             "release_pr": {"version": "0.9.0", "commit": A, "describe": "v0.8.0-12-g7e113f0"},
             "old_app": None}
    script = fn + f"\nconst cases = {json.dumps(cases)};\nconsole.log(JSON.stringify(Object.fromEntries(Object.entries(cases).map(([k, v]) => [k, knowgovLabel(v)]))));"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.js"
        f.write_text(script, encoding="utf-8")
        out = json.loads(subprocess.run([node, str(f)], capture_output=True, text=True, check=True, timeout=60).stdout)
    assert out == {"checkout": "knowgov 0.8.0 + 277 (7e113f0)", "release": "knowgov 0.8.0 (v0.8.0)",
                   "image": "knowgov 0.8.0 (7e113f0, distance from the release unknown)",
                   "nothing": "knowgov 0.8.0 (commit unknown)", "no_version": "knowgov version unknown (commit unknown)",
                   "release_pr": "knowgov 0.9.0 + 12 since v0.8.0 (7e113f0)", "old_app": "knowgov: not reported"}, out
    assert "knowgovChip() +" in page and "STATE.knowgov = j.knowgov || null;" in page
    assert "git -C ~/knowgov describe --tags --always" in page, "the chip's title says how to compare"


def test_a_copy_inside_another_repository_never_takes_its_commit():
    if not shutil.which("git") or not (ROOT / ".git").exists():
        skip("git", "this copy is not a git checkout with git installed")
    (ROOT / "runs").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as td:   # runs/ is ignored by git; git would walk up to the checkout
        r = _root(td, head=A)   # a partial .git, as the image has: HEAD and refs, no objects, no config
        assert bi.from_git_binary(r) == (None, None), "git answers for the checkout around it, or for nothing"
        assert bi.identity(r) == {"version": "0.8.0", "commit": A, "describe": None}, "this copy's own HEAD"
