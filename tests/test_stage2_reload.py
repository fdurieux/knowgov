"""Task-0197, doc-0030 F3: stage 2 as a whole re-load. tools/check_stage2_reload.py holds a stage-2 gate equal
to a fresh load of the later documents plus its stale and suspect findings: S6 and the H2, H4, I5 and G5 plants
on CargoQuote, I6 on J-F. It runs here for the process's subject on rdflib, and in CI on both subjects, on rdflib
(harness.yml) and on Neo4j (demo.yml's stack job)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402

TOOL = "tools/check_stage2_reload.py"


def test_the_stage2_check_holds_on_this_processs_subject():
    need_rdflib()
    from subject import SUBJECT
    env = {**os.environ, "KG_STORE": "rdflib", "KG_SUBJECT": str(SUBJECT.root), "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("KG_RDFLIB_FILE", None)
    p = subprocess.run([sys.executable, str(ROOT / TOOL)], env=env, cwd=ROOT, capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-2000:]
    assert f"stage 2 as a whole re-load on {SUBJECT.id}: every check holds" in p.stdout, p.stdout[-2000:]


def test_ci_runs_it_on_both_subjects_and_both_stores():
    harness = (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    demo = (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
    assert f"KG_STORE=rdflib python {TOOL}" in harness and f"KG_STORE=rdflib KG_SUBJECT=subjects/jef_data_load python {TOOL}" in harness
    assert f"exec -T app python {TOOL}" in demo and f"KG_SUBJECT=/repo/subjects/jef_data_load app python {TOOL}" in demo


def test_the_adapters_pair_document_statements_across_versions_and_rreq_keeps_a_close():
    """The two adapter changes the check rests on, named in both adapters (H4, H2, G5)."""
    for name in ("store_rdflib.py", "store_neo4j.py"):
        src = (ROOT / "harness" / name).read_text(encoding="utf-8")
        assert "DOCUMENT_BASES" in src, f"{name}: document statements pair across versions"
        assert "'closed'" in src or '"closed"' in src, f"{name}: R-REQ keeps a closed gap closed"
        assert "withdrawn" in src, f"{name}: R-STALE withdraws a declared gap it invalidated"
