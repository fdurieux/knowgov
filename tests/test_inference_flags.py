"""task-0244 (doc-0033 R3): a key whose statements are all inference bases carries every basis among them,
sorted, so its flags no longer depend on PYTHONHASHSEED. The gate's own flag function runs in subprocesses
under several seeds; no store, no model."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
sys.path.insert(0, str(HARNESS))


def test_mixed_inference_bases_give_every_basis_whatever_the_hash_seed():
    """Every basis among a key's inference-only statements, sorted; a single-basis key as before. The gate's own
    flag code runs in subprocesses under several PYTHONHASHSEED values, the reviewer's probe."""
    import gate
    rows = [{"basis": "inferred"}, {"basis": "assumed"}]
    assert gate.inference_flags(rows) == {"assumed", "inferred"}
    assert gate.inference_flags([{"basis": "inferred"}]) == {"inferred"}
    assert gate.inference_flags([{"basis": "inferred"}, {"basis": "extracted"}]) == set(), "a key with any other basis is not flagged"
    seen = set()
    script = "import json, sys\nsys.path.insert(0, sys.argv[1])\nimport gate\n" \
             "rows = [{'basis': b} for b in ('inferred', 'assumed', 'hypothesised', 'assumed')]\n" \
             "print(json.dumps(sorted(gate.inference_flags(rows))))\n"
    for seed in ("0", "1", "2", "3", "12345"):
        p = subprocess.run([sys.executable, "-c", script, str(HARNESS)], capture_output=True, text=True,
                           env={**os.environ, "PYTHONHASHSEED": seed, "KG_CLOCK": "pinned"}, timeout=60)
        assert p.returncode == 0, p.stderr
        seen.add(p.stdout.strip())
    assert seen == {json.dumps(["assumed", "hypothesised", "inferred"])}, seen
    src = (HARNESS / "gate.py").read_text(encoding="utf-8")
    assert "next(iter({r[\"basis\"]" not in src and "inference_flags(rows)" in src, "resolve_spec flags through the one function"
