"""The subject: what the harness loads and the page shows, read from a subject root.

A subject root (``KG_SUBJECT``, default ``subjects/cargo_quote``) holds ``subject.toml`` (the
artefacts, the reference code, the oracle, the provenance and verification constants, the task
classes, the three-valued keys, the record), ``scenarios.toml`` (optional: the recorded scenarios,
their plants' switches, the measures' keyword sets and targets, the page's sentences and the
systemic placements), ``plants.toml`` (optional: the mechanical patches), ``queries.toml``
(optional: saved Cypher), ``register_map.toml`` (optional) and ``prompts/`` (the arms' task
prompts). The format is documented in ``subjects/README.md``. Nothing in the harness or the page
names a subject, a document or a scenario: all of it comes from here.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent          # harness/
ROOT = HERE.parent                              # the repository
DEFAULT = ROOT / "subjects" / "cargo_quote"


def _toml(p: Path) -> dict:
    return tomllib.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


class Subject:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        if not (self.root / "subject.toml").exists():
            raise FileNotFoundError(f"{self.root} holds no subject.toml")
        m = _toml(self.root / "subject.toml")
        self.manifest = m
        s = m.get("subject", {})
        self.id: str = s.get("id", self.root.name)
        self.name: str = s.get("name", self.id)
        self.description: str = s.get("description", "")
        self.record_model: str = s.get("record_model", "")
        self.artefacts: list[dict] = list(m.get("artefact", []))
        sc = _toml(self.root / "scenarios.toml")
        self.scenarios: dict[str, dict] = {x["id"]: x for x in sc.get("scenario", [])}
        self.order: list[str] = list(self.scenarios)
        pl = _toml(self.root / "plants.toml")
        self.plants: dict[str, list[dict]] = pl.get("plant", {})
        self.stage2_plants: dict[str, list[dict]] = pl.get("stage2", {})
        self.inferred: dict | None = pl.get("inferred")
        self.queries: list[dict] = list(_toml(self.root / "queries.toml").get("query", []))
        self.reference: dict = m.get("reference", {})
        self.oracle: dict = m.get("oracle", {})
        self.provenance: dict = m.get("provenance", {})
        self.verification: dict = m.get("verification", {})
        self.tasks: dict = m.get("tasks", {})
        self.three_valued: list[str] = list(m.get("three_valued", {}).get("keys", []))
        self.rules: dict = m.get("rules", {})
        self.register: dict = m.get("register", {})
        self.page: dict = m.get("page", {})
        rec = m.get("record", {})
        # the record: <dir>/<scenario>/deterministic.json and the arms' run files; a subject that
        # has not been run has an empty or absent record/ and the page lists nothing to replay
        self.record_dir: Path = self.root / rec.get("dir", "record")

    # ---- paths and files
    def path(self, rel: str) -> Path:
        return self.root / rel

    @property
    def kit_files(self) -> list[tuple[str, Path]]:
        """(key, file) for every artefact that has bytes on disk, in manifest order."""
        return [(a["key"], self.root / a["path"]) for a in self.artefacts if a.get("path")]

    @property
    def order_keys(self) -> list[str]:
        """Every artefact key, in the order the baseline arm concatenates them."""
        return [a["key"] for a in self.artefacts]

    @property
    def families(self) -> dict[str, tuple[str, str]]:
        return {a["key"]: (a["family"], a["format"]) for a in self.artefacts}

    @property
    def store_keys(self) -> set[str]:
        return {a["key"] for a in self.artefacts if a.get("store", True)}

    @property
    def mappers(self) -> dict[str, str]:
        return {a["key"]: a["mapper"] for a in self.artefacts if a.get("mapper")}

    @property
    def shorts(self) -> dict[str, str]:
        return {a["key"]: a["short"] for a in self.artefacts if a.get("short")}

    def pristine(self) -> dict[str, str]:
        return {key: p.read_text(encoding="utf-8") for key, p in self.kit_files}

    def reference_code(self) -> str:
        rel = self.reference.get("code")
        return self.path(rel).read_text(encoding="utf-8") if rel else ""

    def oracle_script(self) -> Path | None:
        rel = self.oracle.get("script")
        return self.path(rel) if rel else None

    @property
    def suite_order(self) -> list[str]:
        return list(self.oracle.get("suite_order", []))

    def verification_map(self) -> dict:
        rel = self.verification.get("map")
        return _toml(self.path(rel)) if rel else {}

    def prompt(self, name: str) -> str:
        return (self.root / "prompts" / f"{name}.md").read_text(encoding="utf-8")

    def scenario(self, sc: str) -> dict:
        if sc not in self.scenarios:
            raise KeyError(f"{self.id}: no scenario {sc!r}; the subject declares {self.order or 'none'}")
        return self.scenarios[sc]

    def plants_for(self, sc: str, stage: int = 1) -> list[dict]:
        if stage == 2:
            return list(self.stage2_plants.get(sc, []))
        return list(self.plants.get(sc, []))

    def register_map(self) -> dict:
        rel = self.register.get("map")
        return _toml(self.path(rel)) if rel else {}

    def definition_files(self) -> list[Path]:
        """Every file of the subject root that is not the record: what a run's SHA256SUMS lists."""
        out = []
        for p in sorted(self.root.rglob("*")):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            if self.record_dir and p.is_relative_to(self.record_dir):
                continue
            out.append(p)
        return out


def load(root: str | os.PathLike | None = None) -> Subject:
    return Subject(Path(root or os.environ.get("KG_SUBJECT") or DEFAULT))


SUBJECT = load()
