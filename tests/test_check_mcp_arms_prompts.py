"""doc-0030 M9, task-0208: tools/check_mcp_server.py holds evidence_bundle equal to the bundle the arms read, so it
takes each scenario's prompts as harness/run.py does (``scenarios.toml``'s ``prompts``, ``task_codegen`` by default),
never a hard-coded ``task_codegen``: on a scenario whose prompts differ (CargoQuote's S6, ``task_s6``) the arms'
verbatim documents are the ones that prompt names."""
from __future__ import annotations

import contextlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(ROOT / "tools")]
import check_mcp_server  # noqa: E402
import gate  # noqa: E402
import kitio  # noqa: E402
import store  # noqa: E402
from subject import SUBJECT  # noqa: E402


def test_the_arms_bundle_takes_each_scenarios_prompts_as_the_runner_does():
    seen: list[str] = []
    saved = (kitio.verbatim_documents, kitio.kit_for, store.open_store, gate.resolve, gate.render_bundle)

    @contextlib.contextmanager
    def opened(access):
        yield object()

    def verbatim(kit, task_name):
        seen.append(task_name)
        return {}

    try:
        kitio.verbatim_documents, kitio.kit_for = verbatim, (lambda sc, stage=1: {})
        store.open_store, gate.resolve = opened, (lambda st, cls, *a, **k: {"keys": {}})
        gate.render_bundle = lambda g, policy, verbatim: ""
        for sc in SUBJECT.order:
            check_mcp_server.arms_bundle(sc, 1)
    finally:
        kitio.verbatim_documents, kitio.kit_for, store.open_store, gate.resolve, gate.render_bundle = saved
    want = [SUBJECT.scenario(sc).get("prompts", "task_codegen") for sc in SUBJECT.order]   # harness/run.py's _run_all
    assert seen == want, f"the check passed {seen}, the runner {want}"
