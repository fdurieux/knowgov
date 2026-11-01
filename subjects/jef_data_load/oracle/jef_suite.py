"""The oracle of the J-F data-load subject: the kit's own pytest-bdd suite, driven through the
seams its README fixes (``JDL_UNDER_TEST``, ``JDL_CHAIN``, ``JDL_ADAPTER``), presented in the
interface the harness's measures expect of an oracle script (``harness/measures.py``
``run_suite``): ``suite_mod.SUITE["scenarios"]`` and ``suite_mod.OVERLAYS``, ``build_spec(name)``,
``run_child(artifact, spec)`` and ``run_artifact(artifact)``, as CargoQuote's ``smoke_test.py``
has them.

The suite's unit here is one feature file (twelve); a result is that feature's cases passed
over its total, with the failed scenarios named in the detail. The suite runs once per
artefact, whatever the harness asks feature by feature: the result is cached by the artefact's
digest.

An artefact is either a directory, the rebuild's layout (``src/jef``, ``deploy/daily.sh``, a
``jdl_adapter.py`` beside them), which is how the reference is checked; or one Python module,
an arm's reply, which must expose ``main(argv=None) -> int`` (the ``jef-data`` command) and the
adapter functions of ``contracts/HARNESS_INTERFACE.md``: a launcher named ``jef-data`` and an
adapter delegating to the module are written around it, and the chain scenarios, which need a
shell script the reply does not carry, fail and say so.

Needs the kit's pins (``contracts/pins.md``: pandas, numpy, pyarrow, requests) plus pytest and
pytest-bdd 8, which the demo image installs; bash and GNU timeout for the chain.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                          # the subject root
KIT = ROOT / "vendor" / "recreate_experiment" / "kit"
REBUILD = ROOT / "vendor" / "recreate_experiment" / "rebuilds" / "codex-2026-10-24"
FEATURES = sorted(p.stem for p in (KIT / "features").glob("*.feature"))
ADAPTER_FUNCTIONS = ("make_collector", "load_universe", "select_legs", "run_sync", "sync_summary",
                     "status_json", "export_frame", "stored_frame", "actions_state", "import_csv")
TIMEOUT_S = int(os.environ.get("KG_ORACLE_TIMEOUT", "1500"))


class _Suite:
    SUITE = {"scenarios": {f: {} for f in FEATURES}}
    OVERLAYS: dict = {}


suite_mod = _Suite()
_cache: dict[str, dict[str, dict]] = {}


def build_spec(scenario: str) -> dict:
    return {"family": "jef_data_load", "feature": scenario}


def _slug(title: str) -> str:
    """pytest-bdd's test name for a scenario title: lowercased, spaces to underscores, every other
    character that is not a letter or a digit dropped (two-split -> twosplit, manifest.json ->
    manifestjson)."""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9 _]", "", title.lower()).strip().replace(" ", "_"))


def _feature_of_slug() -> dict[str, str]:
    out = {}
    for f in sorted((KIT / "features").glob("*.feature")):
        for m in re.finditer(r"^\s*Scenario(?: Outline)?: (.*)$", f.read_text(encoding="utf-8"), re.M):
            out[_slug(m.group(1).strip())] = f.stem
    return out


def _digest(artifact: Path) -> str:
    h = hashlib.sha256()
    if artifact.is_dir():
        for p in sorted(artifact.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                h.update(p.relative_to(artifact).as_posix().encode()); h.update(p.read_bytes())
    else:
        h.update(artifact.read_bytes())
    return h.hexdigest()


def _launcher(bin_dir: Path, src_dirs: list[Path], entry: str) -> None:
    """A ``jef-data`` executable whose name argparse prints in the help texts."""
    lines = [f"#!{sys.executable}", "import sys"] + [f"sys.path.insert(0, {str(d)!r})" for d in src_dirs] + [entry, "sys.exit(main())", ""]
    p = bin_dir / "jef-data"
    p.write_text("\n".join(lines), encoding="utf-8")
    p.chmod(0o755)


def _run_whole(artifact: Path) -> dict[str, dict]:
    feat_of = _feature_of_slug()
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        bin_dir = t / "bin"; bin_dir.mkdir()
        chain_dir = t / "chain"; chain_dir.mkdir()
        if artifact.is_dir():
            src, adapter_dir = artifact / "src", artifact
            _launcher(bin_dir, [src], "from jef.data.cli import main")
            chain = artifact / "deploy" / "daily.sh"
            if chain.exists():
                shutil.copy(chain, chain_dir / "daily.sh")
        else:
            impl = t / "impl"; impl.mkdir()
            shutil.copy(artifact, impl / "artifact.py")
            (impl / "jdl_adapter.py").write_text("from artifact import " + ", ".join(ADAPTER_FUNCTIONS) + "  # noqa: F401\n", encoding="utf-8")
            src, adapter_dir = impl, impl
            _launcher(bin_dir, [impl], "from artifact import main")
        for ext in ("events.sh", "dashboard.sh"):
            shutil.copy(KIT / "contracts" / "externals" / ext, chain_dir / ext)
        for p in chain_dir.iterdir():
            p.chmod(0o755)
        env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
                   PYTHONPATH=os.pathsep.join(str(d) for d in (src, adapter_dir)), JDL_UNDER_TEST="jef-data",
                   JDL_CHAIN=str(chain_dir / "daily.sh"), JDL_ADAPTER="jdl_adapter", COLUMNS="80")
        env.pop("EODHD_API_KEY", None)
        junit = t / "junit.xml"
        try:
            proc = subprocess.run([sys.executable, "-m", "pytest", "-q", str(KIT / "features" / "steps"), "-p", "no:cacheprovider",
                                   f"--junitxml={junit}"], cwd=t, env=env, capture_output=True, text=True, timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return {f: {"passed": False, "stage": "timeout", "detail": "the suite was killed"} for f in FEATURES}
        if not junit.exists():
            return {f: {"passed": False, "stage": "harness_error", "detail": (proc.stderr or proc.stdout or "no output")[-300:]} for f in FEATURES}
        per = {f: {"total": 0, "failed": []} for f in FEATURES}
        for tc in ET.parse(junit).getroot().iter("testcase"):
            name = tc.get("name", "").split("[")[0]
            s = name[5:] if name.startswith("test_") else name
            f = feat_of.get(s) or next((feat_of[k] for k in feat_of if s.startswith(k) or k.startswith(s)), None)
            if f is None:
                continue
            per[f]["total"] += 1
            if tc.find("failure") is not None or tc.find("error") is not None:
                per[f]["failed"].append(name)
        out = {}
        for f, r in per.items():
            ok = r["total"] > 0 and not r["failed"]
            out[f] = {"passed": ok, "stage": "ok" if ok else ("no_cases" if not r["total"] else "wrong_outcome"),
                      "detail": f"{r['total'] - len(r['failed'])}/{r['total']} cases" + (f"; failed: {', '.join(r['failed'][:6])}" if r["failed"] else "")}
        return out


def run_child(artifact: Path, spec: dict) -> dict:
    key = _digest(Path(artifact))
    if key not in _cache:
        _cache[key] = _run_whole(Path(artifact))
    return dict(_cache[key].get(spec["feature"], {"passed": False, "stage": "harness_error", "detail": "unknown feature"}))


def run_artifact(artifact: Path) -> dict:
    return {f: run_child(artifact, build_spec(f)) for f in FEATURES}


def main() -> int:
    """``python jef_suite.py [<artifact>]``: the reference rebuild by default; prints one line per
    feature and the total, exit 0 iff every case passed."""
    art = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REBUILD
    rows = run_artifact(art)
    passed = total = 0
    for f, r in rows.items():
        m = re.match(r"(\d+)/(\d+) cases", r["detail"])
        p, n = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        passed += p; total += n
        print(f"{'ok  ' if r['passed'] else 'FAIL'} {f:14} {r['detail']}")
    print(json.dumps({"artifact": str(art), "passed": passed, "total": total, "features_ok": sum(1 for r in rows.values() if r["passed"])}))
    return 0 if passed == total and total else 1


if __name__ == "__main__":
    sys.exit(main())
