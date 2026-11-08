"""doc-0030 M11, task-0208: the reader never writes, so loading the register's own tools by path (``register_impact.
load_tools``, ``proposal_impact.check_module``) writes no ``__pycache__`` into ``KG_REGISTER/tools``: an instance
mounts its register read-only, and a reader that writes there breaks decision-0008's "the reader never writes"."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pycache(tree: Path) -> list[str]:
    return sorted(str(p.relative_to(tree)) for p in tree.rglob("*") if p.name == "__pycache__" or p.suffix == ".pyc")


def test_loading_the_registers_tools_writes_no_bytecode_into_the_register():
    with tempfile.TemporaryDirectory() as d:
        reg = Path(d) / "register"
        shutil.copytree(ROOT / "demo" / "register", reg, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        assert _pycache(reg) == []
        env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}   # Python's default: write it
        env["KG_REGISTER"] = str(reg)
        code = (
            "import sys; sys.path.insert(0, sys.argv[1])\n"
            "from pathlib import Path\n"
            "import register_impact as ri, proposal_impact as pi\n"
            "root = Path(sys.argv[2])\n"
            "T = ri.load_tools(root)\n"
            "reg = T['register'].load_register(root)\n"
            "pi.check_module(root)\n"
            "assert sys.dont_write_bytecode is False, 'the reader left the interpreter not writing bytecode'\n"
            "print(len(reg.nodes) if hasattr(reg, 'nodes') else 'loaded')\n")
        r = subprocess.run([sys.executable, "-c", code, str(ROOT / "harness"), str(reg)], env=env, cwd=d,
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr[-2000:]
        assert _pycache(reg) == [], f"the reader wrote bytecode into the register: {_pycache(reg)}"
