"""The question bridge (task-0361, decision-0046 point 2, brought into 0.10.0 by decision-0047 point 3): a handle's open
questions, one question's evidence, and the prefilled issue-form link that answers it. Three reads; nothing is written.

    python harness/questions.py pending HANDLE [--on DATE] [--instance DIR]
    python harness/questions.py evidence KEY [--instance DIR]
    python harness/questions.py link KEY VERDICT STATEMENT [--scenario ID] [--owner UNIT] [--instance DIR]

The instance (``--instance`` or ``KG_INSTANCE``) names its questions and its form in ``questions.toml`` at its root
(``instance/README.md``, "Questions and the answer form"), a top-level ``format = N`` (``harness/formats.py``):

    format = 1
    [questions]
    dir = "questions"                       # the questionnaires capture.py questionnaire and due wrote, kept here
    evidence = "questions/evidence"         # one file per question: <evidence>/<subject>/<key><suffix>
    suffix = ".md"                          # the key percent-encoded, every character but A-Z a-z 0-9 . _ - (default .md)
    [form]
    url = "https://github.com/OWNER/REPO/issues/new"
    template = ".github/ISSUE_TEMPLATE/answer.yml"   # relative to the instance; the URL names its file
    title = "Answer: {key}"                 # optional; {key}, {subject} and {scenario} are filled in
    evidence_base = ""                      # optional: a URL put before the evidence file's path (URL-quoted) in the evidence field
    [form.fields]                           # each field of the form by its id in the template
    key = "key"
    subject = "subject"
    scenario = "scenario"
    owner = "owner_unit"
    evidence = "evidence"
    verdict = "verdict"
    statement = "statement"
    note = "note"
    [form.verdicts]                         # the form's four verdicts, each by the option label the template lists
    right_as_stated = "Right as stated"
    right_with_correction = "Right with a correction"
    wrong = "Wrong"
    dont_know = "I don't know"

``pending``  the open items for HANDLE: the issued, not withdrawn handle (``people/handles.toml``, decision 0009) with
             the role ``gives``; every item of a questionnaire whose ``owner`` is the handle's unit, or a review-due one
             addressed to the handle or its unit (``to``), that no capture has answered since the questionnaire was
             generated: a capture in the subject's ``[capture] dir`` on the item's key, dated on or after
             ``generated_on``, from the questionnaire's owner unit (a review-due one: from the handle it is addressed
             to). Answered items are listed apart with the capture's statement id. A questionnaire of a subject the
             reader does not serve, or one that does not parse, is listed under ``skipped`` with why.
``evidence`` one question's evidence as the instance generated it, verbatim, with its file and digest; or ``found``
             false with why (no such file, or a key the subject does not know).
``link``     the issue form's URL with the form's fields prefilled: the key, the subject, the scenario and the owner
             unit from the questionnaire that asks it, the evidence file's path, the verdict's label and the statement
             to be edited in place; the note left to the person. The template must name every field id and every verdict
             label the configuration gives (read line by line, ``id: <id>``, never parsed as YAML), else refused. A
             verdict is one of the four; the URL is at most ``URL_MAX`` characters.

The person opens the link and submits the issue in GitHub; the instance's reader turns it into an answered
questionnaire ``capture.py ingest`` takes, under an issued handle (decision-0046 points 1 and 5). Standard library
only. Reports pinned by ``harness/schemas/pending-questions.schema.json``, ``question-evidence.schema.json`` and
``answer-link.schema.json``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlencode, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SCHEMA_VERSION = 1
CONFIG = "questions.toml"
FIELDS = ("key", "subject", "scenario", "owner", "evidence", "verdict", "statement", "note")
VERDICTS = ("right_as_stated", "right_with_correction", "wrong", "dont_know")
URL_MAX = 8000   # characters: a longer prefilled URL is refused, as a browser or GitHub may cut it
SAFE = "._-"


class QuestionsError(ValueError):
    """The question cannot be answered: no instance or configuration, a handle that may not answer, no questionnaire
    asking the key."""


def _iso(v) -> str | None:
    return v.isoformat() if isinstance(v, dt.date) else (str(v) if v not in (None, "") else None)


def _inside(base: Path, rel, what: str) -> Path:
    """``base / rel`` when ``rel`` is a relative '/'-path that stays under ``base``; QuestionsError otherwise."""
    if not isinstance(rel, str) or not rel or "\\" in rel or "\0" in rel:
        raise QuestionsError(f"{what} {rel!r}: a '/'-separated path relative to the instance")
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts:
        raise QuestionsError(f"{what} {rel!r}: relative to the instance, without '..'")
    out = (base / p).resolve()
    if not out.is_relative_to(base.resolve()):
        raise QuestionsError(f"{what} {rel!r}: resolves outside the instance")
    return out


def config(instance: str | None) -> dict:
    """The instance's ``questions.toml``, checked: its folders, the form's URL, template, fields and four verdicts."""
    import formats
    if not instance:
        raise QuestionsError("no instance configured (KG_INSTANCE or --instance), so no questions.toml to read")
    inst = Path(instance)
    f = inst / CONFIG
    if not f.is_file():
        raise QuestionsError(f"{f}: missing; the instance names its questions and its answer form there "
                             "(instance/README.md, \"Questions and the answer form\")")
    try:
        doc = tomllib.loads(f.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise QuestionsError(f"{f}: does not parse: {e}") from None
    formats.version(doc, f.as_posix(), formats.QUESTIONS)
    q, form = doc.get("questions") or {}, doc.get("form") or {}
    errors = []
    fields, verdicts = form.get("fields") or {}, form.get("verdicts") or {}
    errors += [f"[form.fields] {k}: missing" for k in FIELDS if not isinstance(fields.get(k), str) or not fields.get(k)]
    errors += [f"[form.verdicts] {k}: missing" for k in VERDICTS if not isinstance(verdicts.get(k), str) or not verdicts.get(k)]
    errors += [f"[form.{t}] {k}: not one this knowgov reads" for t, known, got in (("fields", FIELDS, fields), ("verdicts", VERDICTS, verdicts))
               for k in got if k not in known]
    url = form.get("url")
    parts = urlsplit(url) if isinstance(url, str) else None
    if parts is None or parts.scheme != "https" or not parts.netloc or parts.query or parts.fragment:
        errors.append(f"[form] url {url!r}: an https URL with no query, such as https://github.com/OWNER/REPO/issues/new")
    if errors:
        raise QuestionsError(f"{f}: " + "; ".join(errors))
    return {"instance": inst.resolve(), "file": f, "dir": _inside(inst, q.get("dir", "questions"), "[questions] dir"),
            "evidence": _inside(inst, q.get("evidence", "questions/evidence"), "[questions] evidence"),
            "suffix": str(q.get("suffix", ".md")), "url": url,
            "template": _inside(inst, form.get("template", ""), "[form] template"), "title": str(form.get("title", "")),
            "evidence_base": str(form.get("evidence_base", "")), "fields": fields, "verdicts": verdicts}


def questionnaires(cfg: dict) -> tuple[list[dict], list[dict]]:
    """Every questionnaire under the questions folder, (path relative to the instance, parsed), and those skipped with
    why: one that does not parse, or names no subject, owner or generated_on."""
    import formats
    out, skipped = [], []
    for p in sorted(cfg["dir"].rglob("*.toml")) if cfg["dir"].is_dir() else []:
        rel = p.relative_to(cfg["instance"]).as_posix()
        try:
            doc = tomllib.loads(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            skipped.append({"file": rel, "why": f"does not parse: {e}"})
            continue
        formats.version(doc, p.as_posix(), formats.CAPTURE)   # a questionnaire is a capture's source (capture.check_answers)
        q = doc.get("questionnaire")
        if not isinstance(q, dict):
            continue   # not a questionnaire: an answered one kept beside, or another file
        on = q.get("generated_on")
        if not q.get("subject") or not q.get("owner") or not isinstance(on, dt.date):
            skipped.append({"file": rel, "why": "its [questionnaire] names no subject, owner or generated_on date"})
            continue
        out.append({"file": rel, "q": q, "items": [i for i in doc.get("item", []) if isinstance(i, dict) and i.get("key")]})
    return out, skipped


def evidence_file(cfg: dict, subject: str, key: str) -> Path:
    """Where the instance keeps a question's evidence: <evidence>/<subject>/<key percent-encoded><suffix>."""
    return cfg["evidence"] / subject / (quote(key, safe=SAFE) + cfg["suffix"])


# ---- pending_questions


def _handle(handle, register: Path, on: dt.date) -> dict:
    """The register's row for a handle that may answer on ``on``: issued, by then, not withdrawn, holding gives."""
    import capture
    import review
    import who_knows
    rows, rel = who_knows.holders(register)
    if not isinstance(handle, str) or not re.match(capture.handle_pattern(register), handle):
        raise QuestionsError(f"handle {handle!r}: not an opaque handle ({capture.handle_pattern(register)})")
    if rel is None:
        raise QuestionsError("the register names no issued list (types.toml [elicited] issued), so no handle is issued")
    row = rows.get(handle)
    if row is None:
        raise QuestionsError(f"handle {handle}: not issued; the register's issued list ({rel}) does not name it")
    issued, gone = review._date(row.get("issued")), review._date(row.get("withdrawn"))
    if issued and issued > on:
        raise QuestionsError(f"handle {handle}: issued on {issued}, after {on}")
    if gone and gone <= on:
        raise QuestionsError(f"handle {handle}: withdrawn on {gone}; its unit's questions go to another of its handles")
    if "gives" not in set(row.get("roles", [])):
        raise QuestionsError(f"handle {handle}: lacks the role gives, which an answer needs (decision 0009)")
    return row


def _mine(q: dict, handle: str, unit: str) -> str | None:
    """How a questionnaire reaches the handle: ``owner`` (its unit's) or ``review-due`` (addressed to it or its unit)."""
    if q.get("route") == "review-due":
        return "review-due" if str(q.get("to", "")) in (handle, unit) else None
    return "owner" if str(q.get("owner", "")) == unit else None


def _captures(root: Path) -> list[dict]:
    """Every capture of a subject: its file stem, owner, giver, date and the keys it answers or says nobody knows."""
    import formats
    import key_rule
    out = []
    for p in sorted(root.glob("*.toml")) if root.is_dir() else []:
        c = tomllib.loads(p.read_text(encoding="utf-8"))
        formats.version(c, p.as_posix(), formats.CAPTURE)
        cap = c.get("capture", {})
        keys = {key_rule.normalise(str(a.get("key", ""))): f"A:cap:{p.stem}:{i}@capture" for i, a in enumerate(c.get("answer", []), 1)}
        keys |= {key_rule.normalise(str(u.get("key", ""))): f"A:cap:{p.stem}:unknown{i}@capture" for i, u in enumerate(c.get("unknown", []), 1)}
        out.append({"owner": str(cap.get("owner", "")), "from": str(cap.get("from", "")), "on": cap.get("on"), "keys": keys})
    return out


def _answered(caps: list[dict], q: dict, route: str, key: str) -> dict | None:
    """The first capture answering ``key`` for this questionnaire since it was generated, else None."""
    since = q["generated_on"]
    for c in caps:
        if key not in c["keys"] or not isinstance(c["on"], dt.date) or c["on"] < since:
            continue
        if (route == "review-due" and c["from"] == str(q.get("to"))) or c["owner"] == str(q["owner"]):
            return {"capture": c["keys"][key], "from": c["from"], "on": c["on"].isoformat()}
    return None


def _item(cfg: dict, qn: dict, route: str, it: dict) -> dict:
    import key_rule
    q, key = qn["q"], key_rule.normalise(str(it["key"]))
    return {"subject": str(q["subject"]), "scenario": str(q.get("scenario", "")), "task": str(q.get("task", "")),
            "owner": str(q["owner"]), "route": route, "questionnaire": qn["file"], "generated_on": q["generated_on"].isoformat(),
            "key": key, "level": it.get("level"), "question": str(it.get("question", "")),
            "known": [str(x) for x in it.get("known", [])], "declared_gaps": [str(x) for x in it.get("declared_gaps", [])],
            "closed_by": it.get("closed_by") or None, "earlier": it.get("earlier"), "due": _iso(it.get("due")),
            "evidence": evidence_file(cfg, str(q["subject"]), key).is_file()}


def pending(handle, instance: str | None, on: dt.date, register: Path | None = None) -> dict:
    """The handle's open items and those already answered, from the questionnaires and the captures."""
    import register_impact as ri
    import review
    import subject_ids
    from subject import Subject
    register = (register or ri.register_root()).resolve()
    cfg = config(instance)
    row = _handle(handle, register, on)
    unit = str(row.get("unit", ""))
    qns, skipped = questionnaires(cfg)
    served = {x["id"]: x for x in subject_ids.subjects()}
    caps: dict[str, list[dict]] = {}
    items, answered = [], []
    for qn in qns:
        route = _mine(qn["q"], handle, unit)
        sid = str(qn["q"]["subject"])
        if route is None:
            continue
        if sid not in served:
            skipped.append({"file": qn["file"], "why": f"subject {sid} is not under KG_SUBJECTS, so its captures are not read"})
            continue
        if sid not in caps:
            caps[sid] = _captures(Subject(served[sid]["root"]).capture_dir)
        for it in qn["items"]:
            item = _item(cfg, qn, route, it)
            got = _answered(caps[sid], qn["q"], route, item["key"])
            if got is None:
                items.append(item)
            else:
                answered.append({k: item[k] for k in ("subject", "scenario", "key", "questionnaire")} | got)
    order = lambda x: (x["subject"], x["scenario"], x["key"], x["questionnaire"])  # noqa: E731
    return {"schema_version": SCHEMA_VERSION, "tool": "pending_questions", "handle": handle, "unit": unit,
            "unit_name": review.organisation_units(register).get(unit, ""), "roles": sorted(str(r) for r in row.get("roles", [])),
            "on": on.isoformat(), "questions": cfg["dir"].relative_to(cfg["instance"]).as_posix(),
            "items": sorted(items, key=order), "answered": sorted(answered, key=order),
            "skipped": sorted(skipped, key=lambda x: x["file"])}


# ---- question_evidence


def evidence(key: str, subject, instance: str | None) -> dict:
    """One question's evidence as the instance generated it, verbatim, or found false with why."""
    import key_rule
    cfg = config(instance)
    key = key_rule.normalise(key)
    f = evidence_file(cfg, subject.id, key)
    rel = f.relative_to(cfg["instance"]).as_posix()
    out = {"schema_version": SCHEMA_VERSION, "tool": "question_evidence", "subject": subject.id, "key": key,
           "file": rel, "found": False, "sha256": None, "text": None, "why": None}
    known = _known(subject)
    if key not in known:
        return {**out, "why": f"{key}: no key of {subject.id} (its register map's rows and its tasks' keys)" + key_rule.did_you_mean(key, known)}
    if not f.is_file():
        return {**out, "why": f"no evidence file {rel}: the instance has generated none for this question"}
    raw = f.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise QuestionsError(f"{rel}: not UTF-8 text") from None
    return {**out, "found": True, "sha256": hashlib.sha256(raw).hexdigest(), "text": text}


def _known(subject) -> set[str]:
    """The keys the subject knows: its register map's rows and its tasks' keys, in NFC (``trace.known_keys``'s rule)."""
    import key_rule
    rows = {r["key"] for r in subject.register_map().get("row", []) if isinstance(r.get("key"), str)}
    return rows | {key_rule.normalise(k) for t in subject.tasks.values() if isinstance(t, dict) for k in t.get("keys", [])
                   if isinstance(k, str)}


# ---- answer_link


def _template_check(cfg: dict) -> None:
    """The template names every configured field id (a line ``id: <id>``) and every verdict label, read as text."""
    t = cfg["template"]
    if not t.is_file():
        raise QuestionsError(f"[form] template {t.relative_to(cfg['instance']).as_posix()}: no such file in the instance")
    text = t.read_text(encoding="utf-8")
    ids = set(re.findall(r"^\s*-?\s*id:\s*['\"]?([A-Za-z0-9_-]+)['\"]?\s*$", text, re.M))
    missing = [f"field id {v!r} ({k})" for k, v in cfg["fields"].items() if v not in ids]
    missing += [f"verdict label {v!r} ({k})" for k, v in cfg["verdicts"].items() if v not in text]
    if missing:
        raise QuestionsError(f"{t.relative_to(cfg['instance']).as_posix()} does not name " + ", ".join(missing)
                             + f": {CONFIG} and the form disagree")


def _asking(cfg: dict, subject_id: str, key: str, scenario, owner) -> dict:
    """The one questionnaire item that asks ``key`` of the subject, narrowed by scenario and owner when given."""
    import key_rule
    qns, _ = questionnaires(cfg)
    hits = [(qn, it) for qn in qns if str(qn["q"]["subject"]) == subject_id for it in qn["items"]
            if key_rule.normalise(str(it["key"])) == key
            and (scenario is None or str(qn["q"].get("scenario", "")) == scenario)
            and (owner is None or str(qn["q"]["owner"]) == owner)]
    if not hits:
        raise QuestionsError(f"no questionnaire under {cfg['dir'].relative_to(cfg['instance']).as_posix()} asks {key} of {subject_id}"
                             + (f" in scenario {scenario}" if scenario else "") + (f" of {owner}" if owner else ""))
    named = sorted({(str(qn["q"].get("scenario", "")), str(qn["q"]["owner"])) for qn, _ in hits})
    if len(named) > 1:
        raise QuestionsError(f"{key} is asked of {subject_id} in more than one questionnaire ("
                             + ", ".join(f"scenario {s}, owner {o}" for s, o in named) + "): name scenario and owner")
    return {"scenario": named[0][0], "owner": named[0][1], "questionnaire": hits[-1][0]["file"]}


def link(key: str, verdict, statement, subject, instance: str | None, scenario=None, owner=None) -> dict:
    """The prefilled issue-form URL for one answer; nothing is written or opened."""
    import key_rule
    cfg = config(instance)
    if verdict not in VERDICTS:
        raise QuestionsError(f"verdict {verdict!r}: one of {', '.join(VERDICTS)}")
    if not isinstance(statement, str):
        raise QuestionsError("statement: a string")
    _template_check(cfg)
    key = key_rule.normalise(key)
    hit = _asking(cfg, subject.id, key, scenario, owner)
    ev = evidence_file(cfg, subject.id, key)
    rel = ev.relative_to(cfg["instance"]).as_posix()
    # behind a URL base the path is URL-quoted, so the file's own percent signs survive (quote%7Cx.md -> quote%257Cx.md)
    ev_value = "" if not ev.is_file() else cfg["evidence_base"] + quote(rel, safe="/") if cfg["evidence_base"] else rel
    values = {"key": key, "subject": subject.id, "scenario": hit["scenario"], "owner": hit["owner"], "evidence": ev_value,
              "verdict": cfg["verdicts"][verdict], "statement": statement, "note": ""}
    params = [("template", cfg["template"].name)]
    title = cfg["title"].replace("{key}", key).replace("{subject}", subject.id).replace("{scenario}", hit["scenario"])
    params += [("title", title)] if title else []
    params += [(cfg["fields"][f], values[f]) for f in FIELDS if values[f]]
    url = cfg["url"] + "?" + urlencode(params, quote_via=quote)
    if len(url) > URL_MAX:
        raise QuestionsError(f"the prefilled URL is {len(url)} characters, over {URL_MAX}: shorten the statement, "
                             "or leave it for the person to write in the form")
    return {"schema_version": SCHEMA_VERSION, "tool": "answer_link", "subject": subject.id, "scenario": hit["scenario"],
            "owner": hit["owner"], "key": key, "questionnaire": hit["questionnaire"], "verdict": verdict,
            "verdict_label": cfg["verdicts"][verdict], "statement": statement,
            "template": cfg["template"].relative_to(cfg["instance"]).as_posix(), "url": url,
            "fields": [{"field": f, "id": cfg["fields"][f], "value": values[f]} for f in FIELDS]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="questions.py", description=__doc__.splitlines()[0])
    ap.add_argument("--instance", help="the instance whose questions.toml is read (default: KG_INSTANCE)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pending", help="a handle's open questions")
    p.add_argument("handle")
    p.add_argument("--on", help="the date the handle is read on (YYYY-MM-DD; default KG_TODAY, else today)")
    e = sub.add_parser("evidence", help="one question's evidence, as the instance generated it")
    e.add_argument("key")
    k = sub.add_parser("link", help="the prefilled issue-form URL for one answer")
    k.add_argument("key")
    k.add_argument("verdict", choices=VERDICTS)
    k.add_argument("statement")
    k.add_argument("--scenario")
    k.add_argument("--owner")
    a = ap.parse_args(argv)
    import dates
    import register_impact as ri
    import review
    import upward
    from subject import SUBJECT
    try:
        ri.require()
    except ri.RegisterUnreadable as err:
        print(f"questions: cannot run: {err}", file=sys.stderr)
        return 2
    inst = upward.config(a.instance)["instance"]
    try:
        if a.cmd == "pending":
            rep = pending(a.handle, inst, dates.parse(a.on) if a.on else review.today())
        elif a.cmd == "evidence":
            rep = evidence(a.key, SUBJECT, inst)
        else:
            rep = link(a.key, a.verdict, a.statement, SUBJECT, inst, a.scenario, a.owner)
    except (QuestionsError, ValueError) as err:
        print(f"questions: {err}", file=sys.stderr)
        return 2
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import cli_exit
    sys.exit(cli_exit.run(main, "questions"))
