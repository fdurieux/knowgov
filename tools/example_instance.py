"""Build the public example instance (task-0006): ieam-register's public test case plus the
CargoQuote artefacts, in the instance layout (instance/README.md).

    python tools/example_instance.py <out>

<out> must not exist or be empty. It receives:

    register/                   the register vendored under demo/register, as vendored
    artefacts/<kind>/<file>     CargoQuote's ten documents, each under its kind (the eleventh, the
                                analysis notes, is added by a plant and has no bytes)
    subjects/cargo_quote/       the subject root, its manifest pointing at ../../artefacts/...
    record/cargo_quote/         its record, the subject's [record] dir
    code_map.toml               CargoQuote's reference code (the subject's [reference] code, left in
                                place) mapped to the register application it implements (task-0050)

Everything is copied from this repository; nothing here is new content, and nothing is written
back to the sources. The result is what an organisation's own instance looks like with public,
synthetic content, and what the CI jobs mount read-only to show that replay and a deterministic
run write nothing into an instance. tools/check_instance.py passes on it.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "tools"))
from subject import Subject  # noqa: E402
import formats  # noqa: E402  (task-0174)
import check_instance  # noqa: E402

REGISTER = ROOT / "demo" / "register"
SUBJECT = ROOT / "subjects" / "cargo_quote"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")
# The reference code is one file: QuoteAPI, TariffEngine and ScreeningService (APP-0002 to 0004)
# are classes inside it, so the file maps to the application they are modules of.
CODE_APP = "APP-0001"


def code_map(out: Path, code: Path) -> str:
    """code_map.toml for the reference code: its folder is the root, its Python files are code."""
    root = code.parent.relative_to(out).as_posix()
    return (
        "# Code paths to the register application or module each implements (instance/README.md,\n"
        "# \"Mapping code to the register\"). Globs are relative to [code] root.\n\n"
        f"format = {formats.CURRENT[formats.CODE_MAP]}   # task-0174: the format this file is written in\n\n"
        f'[code]\nroot = "{root}"\ninclude = ["**/*.py"]\n\n'
        f'[[map]]\nglob = "{code.name}"\napp = "{CODE_APP}"\n'
        'note = "CargoQuote reference implementation: QuoteAPI, TariffEngine and ScreeningService are its modules"\n'
    )


def build(out: Path) -> Path:
    out = Path(out).resolve()   # the subject reader resolves its root; a relative out would not compare
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"{out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REGISTER, out / "register", ignore=IGNORE)
    sroot = out / "subjects" / SUBJECT.name
    shutil.copytree(SUBJECT, sroot, ignore=IGNORE)
    s = Subject(sroot)
    by_mapper = check_instance.mapper_kind(check_instance.kinds())
    manifest = (sroot / "subject.toml").read_text(encoding="utf-8")
    for a in s.artefacts:
        if not a.get("path"):
            continue
        kind = by_mapper[a["mapper"]]   # every CargoQuote document with bytes on disk has a mapper
        src = sroot / a["path"]
        dest = out / "artefacts" / kind / src.name
        if dest.exists():
            raise FileExistsError(f"two artefacts named {src.name} under {kind}/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dest)
        manifest, n = re.subn(rf'^path = "{re.escape(a["path"])}"', f'path = "../../artefacts/{kind}/{src.name}"', manifest, flags=re.M)
        assert n == 1, a["path"]
    rec = s.record_dir.relative_to(sroot).as_posix()
    shutil.move(s.record_dir, out / "record" / s.id)
    manifest, n = re.subn(rf'^dir = "{re.escape(rec)}"', f'dir = "../../record/{s.id}"', manifest, flags=re.M)
    assert n == 1, rec
    if formats.declared(tomllib.loads(manifest), formats.SUBJECT) is None:   # task-0174: the writer stamps the version it writes
        manifest = f"[format]\nversion = {formats.CURRENT[formats.SUBJECT]}\n\n" + manifest
    (sroot / "subject.toml").write_text(manifest, encoding="utf-8")
    (out / check_instance.CODE_MAP).write_text(code_map(out, sroot / s.reference["code"]), encoding="utf-8")
    return out


def attest(inst: Path, *files: Path) -> None:
    """The attester lists the Version each of ``files`` (documents under the instance ``inst``) now holds, as the
    maintainer's listing of an edit would (decision-0019): its raw-byte SHA-256 joins ``versions`` in every declaration of the
    subject's ``[verification]`` that lists them: ``authored``, ``approval``, ``execution`` and ``review``
    (decision-0036). A check that plants a defect to measure something other than the
    attestation lists the planted Version, so an unlisted Version's withdrawn attestation stays out of what it
    measures (task-0221)."""
    mf = Path(inst) / "subjects" / SUBJECT.name / "subject.toml"
    text = mf.read_text(encoding="utf-8")
    for f in files:
        digest = hashlib.sha256(Path(f).read_bytes()).hexdigest()
        if f'"{digest}"' not in text:
            text, n = re.subn(r'(versions = \[)', rf'\1"{digest}", ', text)
            assert n == 4, f"want authored, approval, execution and review to list their Versions: {n}"
    mf.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the public example instance.")
    ap.add_argument("out", type=Path)
    args = ap.parse_args(argv)
    build(args.out)
    rep = check_instance.check(args.out)
    print(check_instance.render(rep))
    return 1 if rep["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
