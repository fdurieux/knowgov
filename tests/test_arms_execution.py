"""task-0167: the page's Arms chip and button say whether model output may run, not only whether a key is
set. The status JSON (/api/scenarios) carries ``execution``, harness/execution.py ``refusal()``'s answer
(the instance guard, the backend, the worker's attestation); ``arms_enabled`` is unchanged. The chip reads
"arms enabled" only when a key and execution are both there; a key without a contained worker is a warn
chip naming the refusal; no key is the key-missing chip as before. The Arms button is disabled with the
same reason; Replay and Deterministic are unaffected. The page's own functions run in node, cut from
demo/app/index.html, against the three attestation states the server reports."""
from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "demo" / "app")]
import execution  # noqa: E402
import execution_guard  # noqa: E402
from tests._skip import skip  # noqa: E402

PUBLIC = {"KG_SUBJECT": str(ROOT / "subjects" / "cargo_quote"), "KG_SUBJECTS": str(ROOT / "subjects"),
          "KG_REGISTER": str(ROOT / "demo" / "register")}
FRESH = {"ok": True, "checks": {c: True for c in execution.ATTEST_CHECKS}}
PAGE = ROOT / "demo" / "app" / "index.html"


@contextlib.contextmanager
def _env(**kw):
    names = set(kw) | {execution.JOBS_VAR, execution_guard.OPT_IN, *execution_guard.WATCHED}
    keep = {k: os.environ.get(k) for k in names}
    for k in names:
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in kw.items() if v is not None})
    try:
        yield
    finally:
        for k, v in keep.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def _states():
    """(name, attest.json content or None, the reason's words) for the three states a jobs folder can be in."""
    now = time.time()
    return (("absent", None, "has not attested"),
            ("fresh", {**FRESH, "heartbeat": now}, None),
            ("stale", {**FRESH, "heartbeat": now - 10 * execution.HEARTBEAT_S}, "stale"))


def _execution_for(att) -> dict:
    import server
    with tempfile.TemporaryDirectory() as td:
        if att is not None:
            (Path(td) / execution.ATTEST).write_text(json.dumps(att), encoding="utf-8")
        with _env(**PUBLIC, KG_WORKER_JOBS=td):
            return server.execution_view()


def test_the_status_carries_execution_from_the_refusal_absent_fresh_and_stale():
    for name, att, words in _states():
        got = _execution_for(att)
        assert set(got) == {"ok", "why"}, got
        if words is None:
            assert got == {"ok": True, "why": None}, (name, got)
        else:
            assert got["ok"] is False and words in got["why"], (name, got)
    # the instance guard comes first: an instance mounted refuses whatever the worker says
    import server
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / execution.ATTEST).write_text(json.dumps({**FRESH, "heartbeat": time.time()}), encoding="utf-8")
        with _env(**dict(PUBLIC, KG_SUBJECTS="/instance/subjects", KG_REGISTER="/instance/register"), KG_WORKER_JOBS=td):
            got = server.execution_view()
    assert got["ok"] is False and "X1" in got["why"], got


def test_the_server_calls_the_refusal_and_keeps_arms_enabled_as_it_was():
    src = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    body = src.split("def execution_view()", 1)[1].split("\ndef ", 1)[0]
    assert "execution.refusal()" in body and "attested(" not in body and "ATTEST" not in body, "call it, never copy its logic"
    assert '"arms_enabled": arms_enabled(), "execution": execution_view()' in src
    arms = src.split("def arms_enabled()", 1)[1].split("\ndef ", 1)[0]
    assert "execution" not in arms, "arms_enabled counts keys and the oracle only, for compatibility"


# the page's functions the chip and the buttons are drawn by, cut from index.html as they stand
_CUT = ("esc", "KEY_MARK", "keyMark", "running", "armsReady", "WORKER_HINT", "noWorker", "armsBlockedWhy", "armsChip", "armsOffWhy", "writesWhy",
        "pageToken", "armsRow", "armsEffort", "modeButton")


def _cut(page: str, name: str) -> str:
    m = re.search(rf"(?m)^(?:const {name} = .*$|function {name}\(.*\{{.*\}}$)", page)
    if m:
        return m.group(0)
    m = re.search(rf"(?ms)^function {name}\(.*?^\}}$", page)
    assert m, f"index.html has no top-level {name}"
    return m.group(0)


def _menu_buttons(page: str) -> str:
    """renderMenu's three mode buttons, as the expression that draws them."""
    m = re.search(r"(?m)^ *(\$\{modeButton\(s, 'replay'.*)\n *(\$\{modeButton\(s, 'deterministic'.*)\n *(\$\{modeButton\(s, 'arms'.*)$", page)
    assert m, "renderMenu's mode buttons moved"
    return "`" + "".join(m.groups()) + "`"


def _render(execution_state: dict, key_set: bool) -> dict:
    node = shutil.which("node")
    if not node:
        skip("node", "node is not installed; the page's chip and buttons are drawn by its own script")
    page = PAGE.read_text(encoding="utf-8")
    row = {"id": "record", "label": "the record's", "host": "api.openai.com", "key_var": "OPENAI_API_KEY", "key_set": key_set,
           "available": key_set, "why": "" if key_set else "set OPENAI_API_KEY in the app's environment", "model": "m"}
    j = {"arms_enabled": key_set, "execution": execution_state, "deterministic_enabled": True, "model_rows": [row]}
    script = "\n".join(
        ["const $ = sel => ({value: 'record'});", "let STATE = {lastRun: {}, run: null, shown: null, writes: {}, recordModel: 'm'};"]
        + [_cut(page, n) for n in _CUT]
        + [f"const j = {json.dumps(j)};",
           # the assignment the page makes from the status JSON, as it stands in index.html
           re.search(r"STATE\.armsEnabled = j\.arms_enabled;[^\n]*?STATE\.detEnabled = j\.deterministic_enabled;", page).group(0),
           "STATE.modelRows = j.model_rows;",
           "const s = {id: 'S1'};",
           f"const buttons = {_menu_buttons(page)};",
           "console.log(JSON.stringify({chip: armsChip(), buttons}));"])
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "page.js"
        f.write_text(script, encoding="utf-8")
        p = subprocess.run([node, str(f)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def _esc(t: str) -> str:
    """The page's esc()."""
    return "".join({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}.get(c, c) for c in t)


def _button(buttons: str, mode: str) -> str:
    m = re.search(rf'<button [^>]*data-mode="{mode}"[^>]*>', buttons)
    assert m, (mode, buttons)
    return m.group(0)


def test_the_chip_and_the_arms_button_each_way():
    states = {name: _execution_for(att) for name, att, _w in _states()}
    for name, ex in states.items():
        out = _render(ex, key_set=True)
        arms = _button(out["buttons"], "arms")
        if name == "fresh":
            assert 'class="chip ok"' in out["chip"] and "arms enabled (1 of 1 model rows)" in out["chip"], out["chip"]
            assert "disabled" not in arms, arms
        else:
            assert 'class="chip warn"' in out["chip"] and "arms: no contained worker" in out["chip"], out["chip"]
            assert "arms enabled" not in out["chip"]
            assert _esc(ex["why"].split(" (")[0]) in out["chip"] and "--profile arms" in out["chip"] and "Landlock" in out["chip"], out["chip"]
            assert " disabled " in arms and _esc(ex["why"].split(" (")[0]) in arms and "--profile arms" in arms, arms
        for mode in ("replay", "deterministic"):   # unaffected either way
            assert " disabled " not in _button(out["buttons"], mode), (name, mode, out["buttons"])
    # no key: the key-missing chip as before, whatever the worker says; the button names the key
    for ex in (states["fresh"], states["absent"]):
        out = _render(ex, key_set=False)
        assert "arms disabled: set OPENAI_API_KEY in the app&#39;s environment" in out["chip"], out["chip"]
        arms = _button(out["buttons"], "arms")
        assert " disabled " in arms and "OPENAI_API_KEY" in arms and "worker" not in arms, arms
    # an instance mounted: the guard's own refusal and remedy, not the worker hint
    out = _render({"ok": False, "why": "refused: an organisation's instance is mounted (...) ... X1"}, key_set=True)
    assert "model output may not run here" in out["chip"] and "--profile arms" not in out["chip"], out["chip"]
    # a status without the field (an older app) refuses rather than enables
    out = _render(None, key_set=True)
    assert "arms enabled" not in out["chip"] and " disabled " in _button(out["buttons"], "arms"), out


def test_the_readme_names_the_field_and_the_self_check():
    readme = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    assert '"execution": {"ok"' in readme and "/api/scenarios" in readme
    assert "docker compose --profile arms run --rm --no-deps worker python harness/worker.py --attest-only" in readme
    assert "`write_confined: false`" in readme


def _worker_chip(worker) -> str:
    """task-0169: the page's workerChip(), cut from index.html, against a status's worker field."""
    node = shutil.which("node")
    if not node:
        skip("node", "node is not installed; the page's chip is drawn by its own script")
    page = PAGE.read_text(encoding="utf-8")
    script = "\n".join(["let STATE = {};"] + [_cut(page, n) for n in ("esc", "ENGINES", "workerChip")]
                       + [f"const j = {json.dumps({} if worker is None else {'worker': worker})};",
                          re.search(r"STATE\.worker = j\.worker \|\| null;", page).group(0),
                          "console.log(JSON.stringify(workerChip()));"])
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "page.js"
        f.write_text(script, encoding="utf-8")
        p = subprocess.run([node, str(f)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def test_the_worker_chip_names_where_model_output_runs_as_the_worker_attested_it():
    import server
    src = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    body = src.split("def worker_view()", 1)[1].split("\ndef ", 1)[0]
    assert "return execution.placement()" in body and "ATTEST" not in body, "call it, never copy its logic"
    assert '"execution": execution_view(), "worker": worker_view()' in src
    now = time.time()
    aws = {"system": "Linux", "kernel": "7.0.0-1014-aws", "machine": "x86_64", "engine": "docker"}
    with tempfile.TemporaryDirectory() as td:
        with _env(**PUBLIC, KG_WORKER_JOBS=td):
            absent = server.worker_view()
            (Path(td) / execution.ATTEST).write_text(json.dumps({**FRESH, "heartbeat": now, "host": aws}), encoding="utf-8")
            fresh = server.worker_view()
            (Path(td) / execution.ATTEST).write_text(json.dumps({**FRESH, "heartbeat": now, "host": {**aws, "kernel": "6.8.0-48-generic"}}), encoding="utf-8")
            plain = server.worker_view()
    chip = _worker_chip(fresh)
    assert 'class="chip ok"' in chip and "worker: attested · Docker · Linux 7.0.0-1014-aws (x86_64) · AWS (from the kernel release)" in chip, chip
    assert "not checked" in chip and "-aws suffix" in chip, "the cloud is labelled a reading"
    chip = _worker_chip(plain)
    assert "worker: attested · Docker · Linux 6.8.0-48-generic (x86_64)<" in chip and "AWS" not in chip, chip
    chip = _worker_chip(absent)
    assert 'class="chip warn"' in chip and "worker: not attested" in chip and "has not attested" in chip, chip
    assert "worker: not reported" in _worker_chip(None)
    host = _worker_chip({"backend": "host", "attested": False, "host": None, "cloud": None, "why": "uncontained"})
    assert 'class="chip bad"' in host and "uncontained on the app's host" in host, host
    # the facts are escaped as the worker's word, never markup
    chip = _worker_chip({**fresh, "host": {**aws, "kernel": "<b>x</b>"}, "cloud": None})
    assert "<b>" not in chip and "&lt;b&gt;" in chip, chip
    page = PAGE.read_text(encoding="utf-8")
    assert "armsChip() + workerChip() +" in page
