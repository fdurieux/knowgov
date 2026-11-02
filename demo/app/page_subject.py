"""The subject as a value for the page's modules (task-0032.01).

``views``, ``register_view`` and ``server`` used to fill module tables from the harness's
``SUBJECT`` global at import, so one process could serve one subject only. They now read a
``PageSubject``: every table they need, built once from a ``Subject`` and cached by its root.

A public entry point takes the subject as an argument (``subject=``); ``using()`` makes it the
current one for the length of the call, through a context variable, so the helpers behind the
entry point read ``current()`` without a parameter threaded through every function. With no
subject given, ``current()`` is the subject ``KG_SUBJECT`` names, as before: one subject per
process stays the default, and the next step (task-0032.02) passes one per request.

The harness is untouched: it runs as a subprocess with its own ``KG_SUBJECT``.
"""
from __future__ import annotations

import contextvars
import functools
import re
import sys
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "harness"))
import subject as subject_mod  # noqa: E402  (Subject, and the process default the environment names)

_CURRENT: contextvars.ContextVar = contextvars.ContextVar("page_subject", default=None)
_CACHE: dict[str, "PageSubject"] = {}


def _systemic(s: dict) -> dict:
    """Where a scenario sits on the model's reduced knowledge view: the subject's reading of its
    record onto the Legible v0.3 cascade (scenarios.toml, [scenario.systemic]). Node ids are the
    model's. entry: the node where the planted defect enters; per arm: path, stop and note."""
    sy = s.get("systemic", {})
    out = {"entry": sy.get("entry") or None, "family": sy.get("family", "")}
    for arm in ("G", "B"):
        a = dict(sy.get(arm, {}))
        a.setdefault("path", [])
        a["stop"] = a.get("stop") or None
        a.setdefault("note", "")
        out[arm] = a
    return out


class PageSubject:
    """Every table the page derives from one subject, built once."""

    def __init__(self, s):
        self.subject = s
        self.id: str = s.id
        self.root: Path = s.root
        # the record and the run settings
        self.record_dir: Path = s.record_dir                 # the subject's record, never written
        self.suite_order: list = s.suite_order
        self.record_model: str = s.record_model             # another model is a deviation
        self.record_effort: str = s.record_effort           # another effort is a deviation too (task-0028)
        self.arm_kind: str = s.arms.get("kind", "reply")    # a model row serves reply, agent or both
        # one line per scenario, from scenarios.toml: controlled sentences for the card and the Planted line
        self.scenarios: dict = {sc: {k: v.get(k, "") for k in ("title", "represented", "gate", "defect", "plant", "plain")}
                                for sc, v in s.scenarios.items()}
        self.order: list = list(self.scenarios)
        self.systemic: dict = {sc: _systemic(v) for sc, v in s.scenarios.items()}
        self.reference: dict = s.page.get("reference", {"title": "", "text": "", "numbers": {}})   # the no-governance reference the record cites
        self.families: list = [(a["key"], a.get("label", a["family"]), a.get("format_label", a["format"]))
                               for a in s.artefacts if a.get("store", True)]   # the documents the store reads
        self.mappers: int = len(s.mappers)
        self.key_count: int = len(s.tasks.get("codegen", {}).get("keys", []))
        # the register: how its links cite this subject's requirements
        self.req_anchor: str = s.register.get("requirement_anchor", "")
        self.req_doc_anchor: str = self.req_anchor.split(":", 1)[-1]                 # e.g. requirements.md#
        self.system: str = self.req_anchor.split(":", 1)[0] if ":" in self.req_anchor else "kit"   # the subject as a source system
        self.sys: str = self.system + ":"                                            # the prefix its evidence anchors carry
        self.req_id = re.compile(s.rules.get("requirement_id_pattern", r"[A-Z]{2,}-\d{2,}"))
        self.export_manifest: str = s.register.get("export_manifest", "")
        self.requirements: Path | None = next((s.path(a["path"]) for a in s.artefacts if a["family"] == "requirements" and a.get("path")), None)
        self.cache: dict = {}   # what a module derives lazily from this subject (the glossary), kept per subject

    def __repr__(self) -> str:
        return f"PageSubject({self.id!r})"


def of(s) -> PageSubject:
    """The page's tables for a Subject (or a PageSubject, returned as it is), built once per root."""
    if isinstance(s, PageSubject):
        return s
    key = str(Path(s.root).resolve())
    if key not in _CACHE:
        _CACHE[key] = PageSubject(s)
    return _CACHE[key]


def current() -> PageSubject:
    """The subject of the call in progress, else the one the environment names (the process default)."""
    return _CURRENT.get() or of(subject_mod.SUBJECT)


@contextmanager
def using(s):
    """Make a subject the current one for the length of a block."""
    token = _CURRENT.set(of(s)) if s is not None else None
    try:
        yield current()
    finally:
        if token is not None:
            _CURRENT.reset(token)


def takes_subject(fn):
    """A public entry point that takes ``subject=`` (a Subject or a PageSubject) and runs with it
    as the current subject; without it, the current one stands."""
    @functools.wraps(fn)
    def wrapper(*args, subject=None, **kw):
        with using(subject):
            return fn(*args, **kw)
    return wrapper


def scenario_subject(scenario: str | None, subjects) -> str | None:
    """The id of the subject whose scenarios include ``scenario``: scenario ids are the subject's
    own, so the store's loaded scenario names its subject. None when no listed subject has it."""
    if not scenario:
        return None
    return next((of(s).id for s in subjects if scenario in of(s).scenarios), None)
