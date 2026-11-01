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
        assert ep == {"base_url": "https://api.openai.com/v1", "key_var": "OPENAI_API_KEY", "key_set": False,
                      "model": arms.RECORD_MODEL, "record_model": arms.RECORD_MODEL, "deviation": False}
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
        assert ep["key_set"] and ep["model"] == "gemini-2.5-pro" and ep["deviation"], ep
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
    assert '"arms_enabled": arms.enabled()' in server and '"model_endpoint": _endpoint_view()' in server
    assert "key_set" in server and "api_key" not in server.split("def _endpoint_view")[1].split("def _store")[0]
    page = (ROOT / "demo" / "app" / "index.html").read_text(encoding="utf-8")
    assert "STATE.endpoint.key_var" in page and "STATE.endpoint.host" in page
    compose = (ROOT / "demo" / "docker-compose.yml").read_text(encoding="utf-8")
    for var in ("KG_MODEL_BASE_URL", "KG_MODEL_API_KEY_VAR", "KG_MODEL_API_KEY", "OPENAI_API_KEY"):
        assert var in compose, var
    readme = (ROOT / "demo" / "README.md").read_text(encoding="utf-8")
    for case in ("**OpenAI**", "Google's OpenAI-compatible endpoint", "private model behind a gateway"):
        assert case in readme, case
