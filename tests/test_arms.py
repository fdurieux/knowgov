"""The model endpoint (harness/arms.py): three instance settings, read at call time; the arms
are enabled only when the named key variable holds a value; the page names the endpoint and
the key variable, never the key. No network, no client: arms imports without openai."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import arms  # noqa: E402

SETTINGS = ("KG_MODEL_BASE_URL", "KG_MODEL_API_KEY_VAR", "KG_ARMS_MODEL", "OPENAI_API_KEY", "KG_MODEL_API_KEY", "MY_GATEWAY_KEY")


def _with(env: dict):
    saved = {k: os.environ.get(k) for k in SETTINGS}
    for k in SETTINGS:
        os.environ.pop(k, None)
    os.environ.update(env)
    return saved


def _restore(saved: dict):
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_defaults_are_openai_and_the_records_model_and_arms_are_off_without_a_key():
    saved = _with({})
    try:
        ep = arms.endpoint()
        # the subject the environment names: its record's model, or the default other model when its record ran no arm
        assert ep == {"base_url": "https://api.openai.com/v1", "host": "api.openai.com", "key_var": "OPENAI_API_KEY", "key_set": False,
                      "model": arms.RECORD_MODEL or arms.DEFAULT_MODEL, "record_model": arms.RECORD_MODEL, "effort": "",
                      "record_effort": arms.RECORD_EFFORT, "deviation": False}
        assert not arms.enabled()
    finally:
        _restore(saved)


def test_openai_case_needs_only_the_key():
    saved = _with({"OPENAI_API_KEY": "sk-test"})
    try:
        assert arms.enabled() and arms.endpoint()["key_var"] == "OPENAI_API_KEY"
    finally:
        _restore(saved)


def test_a_compatible_endpoint_with_its_own_key_variable_and_model():
    saved = _with({"KG_MODEL_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai/",
                   "KG_MODEL_API_KEY_VAR": "KG_MODEL_API_KEY", "KG_MODEL_API_KEY": "g-test", "KG_ARMS_MODEL": "gemini-2.5-pro"})
    try:
        ep = arms.endpoint()
        assert ep["base_url"].startswith("https://generativelanguage.googleapis.com") and ep["key_var"] == "KG_MODEL_API_KEY"
        # another model is a deviation, unless the subject's record ran no arm and there is nothing to deviate from
        assert ep["key_set"] and ep["model"] == "gemini-2.5-pro" and ep["deviation"] is bool(arms.RECORD_MODEL), ep
        assert arms.enabled()
    finally:
        _restore(saved)


def test_a_private_gateway_without_its_key_is_off_even_with_an_openai_key_present():
    """The named variable decides: a key under another name sends nothing."""
    saved = _with({"KG_MODEL_BASE_URL": "http://gateway.internal:4000/v1", "KG_MODEL_API_KEY_VAR": "MY_GATEWAY_KEY", "OPENAI_API_KEY": "sk-test"})
    try:
        ep = arms.endpoint()
        assert ep["key_var"] == "MY_GATEWAY_KEY" and not ep["key_set"] and not arms.enabled()
        os.environ["MY_GATEWAY_KEY"] = "gw"
        assert arms.enabled()
    finally:
        _restore(saved)


def test_the_client_is_imported_only_when_a_call_is_made():
    src = (ROOT / "harness" / "arms.py").read_text(encoding="utf-8")
    assert "from openai import OpenAI" in src and src.index("def call(") < src.index("from openai import OpenAI")
    assert "base_url=" in src and 'os.environ.get(ep["key_var"])' in src


def test_the_page_names_the_endpoint_and_the_key_variable_never_the_key():
    server = (ROOT / "demo" / "app" / "server.py").read_text(encoding="utf-8")
    assert '"arms_enabled": arms_enabled()' in server and '"model_rows": model_rows()' in server
    rows_src = (ROOT / "demo" / "app" / "models.py").read_text(encoding="utf-8")
    assert "key_set" in rows_src and "api_key" not in rows_src, "the rows carry the variable's name and whether it is set, never the key"
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert "r.key_var" in page and "r.host" in page and "armsOffWhy()" in page
    compose = (ROOT / "demo" / "docker-compose.yml").read_text(encoding="utf-8")
    for var in ("KG_MODEL_BASE_URL", "KG_MODEL_API_KEY_VAR", "KG_MODEL_API_KEY", "OPENAI_API_KEY"):
        assert var in compose, var
    readme = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    for case in ("**The models table, first.**", "Google's OpenAI-compatible endpoint", "private model behind a gateway", "never holds\nthe key itself"):
        assert case in readme, case


def test_bundle_carries_the_documents_the_task_names_verbatim_after_the_knowledge():
    """A packaged configuration file or a parser table is not an assertion: the governed arm asked for
    them and abstained (task-0022.01, 2026-11-02). The subject's task table names them; the bundle
    appends them as written after the knowledge, saying a statement's status is its key's; a subject
    that names none renders the bundle it always did."""
    import gate
    res = {"verdict": "PROCEED", "why": "every key verified", "conflicts": [], "stale": [],
           "keys": {"k|v": {"level": "verified", "flags": [], "declared_gaps": [],
                            "assertions": [{"id": "A:x", "value": "1", "basis": "authored", "status": "verified", "artefact": "doc", "agent": "a",
                                            "text": "one", "fragments": [], "verifications": [], "approvals": [], "gaps": []}]}}}
    plain = gate.render_bundle(res, "POLICY TEXT")
    assert plain == gate.render_bundle(res, "POLICY TEXT", None) == gate.render_bundle(res, "POLICY TEXT", {}), "no verbatim table, no section"
    with_docs = gate.render_bundle(res, "POLICY TEXT", {"contracts/cli.md": "# cli\nusage: x\n"})
    assert with_docs.startswith(plain) and "VERBATIM DOCUMENTS" in with_docs
    assert "=== contracts/cli.md ===\n# cli\nusage: x\n=== end contracts/cli.md ===" in with_docs
    assert with_docs.index("REQUIRED KNOWLEDGE") < with_docs.index("VERBATIM DOCUMENTS"), "the knowledge comes first; the documents after it"
    import kitio
    kit = {"requirements.json": "[]", "contracts/": "==> a.md <==\nA\n==> sub/b.toml <==\nb = 1\n"}
    assert kitio.kit_text(kit, "requirements.json") == "[]"
    assert kitio.kit_text(kit, "contracts/a.md") == "A\n" and kitio.kit_text(kit, "contracts/sub/b.toml") == "b = 1\n"
    try:
        kitio.kit_text(kit, "contracts/missing.md"); raise AssertionError("a missing part must be refused")
    except KeyError:
        pass


def test_effort_is_sent_only_when_set_recorded_and_compared_with_the_record():
    """Task-0028: KG_ARMS_EFFORT reaches a call as reasoning_effort and is recorded; unset, no parameter
    is sent. An effort other than the record's is a deviation, as another model is; the record effort
    comes from the manifest ("" is the API default)."""
    assert arms.effort_kwargs("") == {} and arms.effort_kwargs("high") == {"reasoning_effort": "high"}
    assert arms.RECORD_EFFORT == arms.SUBJECT.record_effort == ""
    saved = _with({})
    try:
        ep = arms.endpoint()
        assert ep["effort"] == "" and ep["record_effort"] == "" and not ep["deviation"], "no effort set, the record's model: like-for-like"
        os.environ["KG_ARMS_EFFORT"] = "xhigh"
        ep = arms.endpoint()
        assert ep["effort"] == "xhigh" and ep["model"] == (arms.RECORD_MODEL or arms.DEFAULT_MODEL)
        assert ep["deviation"] is bool(arms.RECORD_MODEL), "the record's model at another effort is a deviation; with no record arm, nothing is"
    finally:
        _restore(saved)


def test_tokens_not_dollars_and_the_token_ceiling_stops_a_call():
    """Task-0027: no price in the harness. A call is counted in prompt plus completion tokens, the
    process ceiling is tokens (KG_ARMS_MAX_TOKENS, default DEFAULT_CEILING_TOKENS), and call() refuses
    before it builds a client once the ceiling is reached; usage() reports tokens, never an estimate."""
    assert not hasattr(arms, "cost") and not hasattr(arms, "PRICE_IN") and not hasattr(arms, "CEILING_USD")
    assert arms.tokens_of({"prompt_tokens": 1000, "cached_tokens": 600, "completion_tokens": 100}) == 1100, "cached tokens are part of the prompt, not extra"
    saved = dict(arms._state)
    saved_env = os.environ.pop("KG_ARMS_MAX_TOKENS", None)
    try:
        assert arms.ceiling_tokens() == arms.DEFAULT_CEILING_TOKENS
        os.environ["KG_ARMS_MAX_TOKENS"] = "1500"
        arms._state.update({"calls": 0, "tokens": 0, "usage": []})
        arms.account({"tag": "t/1", "prompt_tokens": 1000, "cached_tokens": 0, "completion_tokens": 100, "seconds": 1})
        u = arms.usage()
        assert u["calls"] == 1 and u["tokens"] == 1100 and "usd_est" not in u and "usd_est" not in u["per_call"][0]
        arms.account({"tag": "t/2", "prompt_tokens": 400, "completion_tokens": 0})
        assert arms.usage()["tokens"] == 1500
        try:
            arms.call("s", "u", tag="t/3")
            raise AssertionError("the ceiling did not stop the call")
        except arms.BudgetExceeded as e:
            assert str(e) == "ceiling 1500 tokens"
    finally:
        arms._state.clear(); arms._state.update(saved)
        if saved_env is not None:
            os.environ["KG_ARMS_MAX_TOKENS"] = saved_env

    class _D:  # the API's usage object, with and without the detail
        def __init__(self, cached=None):
            self.prompt_tokens, self.completion_tokens = 10, 1
            if cached is not None:
                self.prompt_tokens_details = type("P", (), {"cached_tokens": cached})()
    assert arms.cached_of(_D()) == 0 and arms.cached_of(_D(7)) == 7 and arms.cached_of(_D(None)) == 0


def test_usage_fields_keep_the_total_and_the_hidden_remainder_and_flag_uncounted_thinking():
    """Task-0034: the endpoint's total is kept with what it holds beyond prompt and completion; a
    usage without a total counts prompt plus completion; an endpoint declared to leave thinking out
    of streamed usage (a model row's thinking_uncounted) is flagged, since its count is low and says
    nothing of it. No host is assumed: Google's own endpoint counts thinking in its streamed total."""
    from types import SimpleNamespace as NS
    u = NS(prompt_tokens=37, completion_tokens=114, total_tokens=363, prompt_tokens_details=None)
    f = arms.usage_fields(u, "api.openai.com")
    assert f == {"prompt_tokens": 37, "cached_tokens": 0, "completion_tokens": 114, "total_tokens": 363, "hidden_tokens": 212, "thinking_uncounted": False}
    assert arms.tokens_of(f) == 363
    keep = os.environ.pop("KG_THINKING_UNCOUNTED", None)
    try:
        g = arms.usage_fields(NS(prompt_tokens=37, completion_tokens=106, total_tokens=143, prompt_tokens_details=None), "generativelanguage.googleapis.com")
        assert g["hidden_tokens"] == 0 and not g["thinking_uncounted"], "no host is assumed to drop thinking: Google's own endpoint counts it"
        os.environ["KG_THINKING_UNCOUNTED"] = "1"   # what a row declaring thinking_uncounted sets, e.g. a gateway
        g = arms.usage_fields(NS(prompt_tokens=37, completion_tokens=106, total_tokens=143, prompt_tokens_details=None), "localhost:4000")
        assert g["thinking_uncounted"] and arms.tokens_of(g) == 143
    finally:
        os.environ.pop("KG_THINKING_UNCOUNTED", None)
        if keep is not None:
            os.environ["KG_THINKING_UNCOUNTED"] = keep
    n = arms.usage_fields(NS(prompt_tokens=10, completion_tokens=5, prompt_tokens_details=None), "localhost:4000")
    assert n["total_tokens"] is None and n["hidden_tokens"] == 0 and arms.tokens_of(n) == 15
    assert arms.tokens_of({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 3}) == 15, "a total below the sum never lowers the count"
