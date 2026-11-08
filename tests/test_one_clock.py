"""Task-0198, doc-0030 F4: one clock. tools/check_one_clock.py holds, on the example instance, that one --as-of
gives one gate report under two KG_TODAY values (a person's approval and a review-file approval on the subject),
that a person's approval past its six months reads proposed with a lapsed finding, that a review-file approval
with no verification lapses at its date plus the key's months, that what is dated after the as-of date is not
counted, and that three_valued_answer marks a lapse as of the session's date. Run here on rdflib, and in CI on
rdflib (harness.yml) and on Neo4j (the stack job). The rule itself: tests/test_cadence.py."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "harness"), str(Path(__file__).resolve().parent)]
from _skip import need_rdflib  # noqa: E402

TOOL = "tools/check_one_clock.py"


def test_one_as_of_gives_one_report_whatever_the_day_and_every_lapse_is_decided_against_it():
    need_rdflib()
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "KG_STORE": "rdflib", "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("KG_RDFLIB_FILE", None)
        p = subprocess.run([sys.executable, str(ROOT / TOOL), str(Path(td) / "out")], env=env, cwd=ROOT,
                           capture_output=True, text=True, timeout=900)
        assert p.returncode == 0 and "one clock: every check holds" in p.stdout, p.stdout[-3000:] + p.stderr[-1500:]


def test_ci_runs_it_on_both_stores():
    assert f"KG_STORE=rdflib python {TOOL} runs/one-clock" in (ROOT / ".github" / "workflows" / "harness.yml").read_text(encoding="utf-8")
    assert f"python {TOOL} runs/one-clock" in (ROOT / ".github" / "workflows" / "demo.yml").read_text(encoding="utf-8")
