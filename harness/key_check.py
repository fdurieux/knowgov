"""A model row's key checked before the page offers the row, spending no tokens (task-0171).

The check is the provider's model listing, ``GET {base_url}/models``, which OpenAI, Google's
OpenAI-compatible endpoint and LiteLLM all serve for free. It is sent by the model client itself
(the openai library's ``models.list()``, no retry, a short timeout) to the row's own endpoint, so the
only outbound traffic stays the model client's (docs/security.md).

Verdicts:

    accepted     the endpoint answered the listing (2xx) to the key, having refused it without one
    refused      the endpoint refused the key (401, 403): a run on the row would fail the same way
    unreachable  no answer (no connection, a timeout): a run might still work later
    unchecked    no key, the check off (KG_KEY_CHECK=off) or not yet run, another status (404: the
                 endpoint serves no listing; 429; 5xx), or a listing open without a key (OpenRouter's,
                 Ollama's; task-0188), any of which says nothing of the key

The listing is read first with a placeholder bearer that is no key (``NO_KEY``), then, unless that
already settles it, with the row's key: two requests at most, both free.

A verdict carries the HTTP status and the time it was taken, never the provider's message: OpenAI's
401 body quotes part of the key. The key is read from its variable when a check is made and handed
to the client; the cache is keyed by the endpoint and a fingerprint, an HMAC-SHA256 of the key under
a secret drawn at random for this process, so it is neither reversible nor comparable across
processes. Rows that share an endpoint and a key are checked once.

A row behind a gateway (``gateway = true`` in models.toml) is checked the same way, but the
listing proves the gateway's own key only; the provider's key behind it is unchecked, and the
verdict says so (``scope: gateway``). LiteLLM's ``/health`` would test it with a real completion,
which is paid, so it is not used.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
import secrets
import threading
import time

ACCEPTED, REFUSED, UNREACHABLE, UNCHECKED = "accepted", "refused", "unreachable", "unchecked"
TIMEOUT_S = 6.0          # one listing request; the page waits at most WAIT_S for the checks still in flight
WAIT_S = 8.0
_SECRET = secrets.token_bytes(32)   # this process's only; a fingerprint means nothing outside it


def enabled_by_env() -> bool:
    """KG_KEY_CHECK=off (or 0, no, false) turns the check off: every row reads unchecked."""
    return (os.environ.get("KG_KEY_CHECK") or "on").strip().lower() not in ("off", "0", "no", "false")


def fingerprint(base_url: str, key: str) -> str:
    """The cache's name for an endpoint and a key: not the key, not reversible, this process's only."""
    return hmac.new(_SECRET, base_url.encode() + b"\0" + key.encode(), hashlib.sha256).hexdigest()[:24]


NO_KEY = "knowgov-key-check-no-key"   # the bearer of the first listing: no provider issues it, so it is no key


def _listing(base_url: str, key: str) -> dict:
    """One listing request through the model client: the verdict, the HTTP status and the model ids
    listed (names, nothing secret); never the exception's text."""
    from openai import OpenAI, APIConnectionError, APIStatusError, APITimeoutError  # lazy, as arms.call()

    client = OpenAI(api_key=key, base_url=base_url, max_retries=0, timeout=TIMEOUT_S)
    try:
        listed = [m.id for m in client.models.list()]
    except APIStatusError as e:
        code = int(getattr(e, "status_code", 0) or 0)
        return {"state": REFUSED if code in (401, 403) else UNCHECKED, "status": code, "models": None}
    except (APIConnectionError, APITimeoutError):
        return {"state": UNREACHABLE, "status": None, "models": None}
    finally:
        client.close()
    return {"state": ACCEPTED, "status": 200, "models": listed}


def probe(base_url: str, key: str) -> dict:
    """The row's verdict from at most two listing requests (task-0188). The first carries NO_KEY: an
    endpoint that lists its models to it lists them to anyone (OpenRouter's did with an invalid
    bearer on 2026-11-06, doc-0023; Ollama holds no keys), so its listing says nothing of the key and the
    verdict is unchecked, ``open`` noting why, whatever the key would get. An endpoint that does not answer
    is unreachable. Otherwise the second request carries the key and its answer is the verdict, as
    before: accepted, refused, or unchecked for any other status."""
    first = _listing(base_url, NO_KEY)
    if first["state"] == ACCEPTED:
        return {"state": UNCHECKED, "status": first["status"], "models": first["models"], "open": True}
    if first["state"] == UNREACHABLE:
        return first
    return _listing(base_url, key)


def _now() -> str:
    # task-0075: the time a verdict was taken is shown, never decides an outcome
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _why(state: str, status: int | None, key_var: str, gateway: bool, open_listing: bool = False) -> str:
    if open_listing:
        return f"the endpoint lists its models without a key, so the listing says nothing of the key in {key_var}"
    if state == ACCEPTED:
        return "gateway key accepted, upstream unchecked" if gateway else "key accepted by the endpoint's model listing"
    if state == REFUSED:
        return f"the endpoint refused the key in {key_var} (HTTP {status}); set a valid key and re-check"
    if state == UNREACHABLE:
        return "the endpoint did not answer the key check; a run may still reach it"
    return f"the key check said nothing of the key (HTTP {status})" if status else "the key was not checked"


class Checker:
    """The verdicts of this process, by endpoint and key fingerprint. ``enabled`` is off until the
    page starts serving (server.main()), so importing the page, or a test, sends nothing."""

    def __init__(self, probe_fn=None):
        self.probe = probe_fn or probe
        self.enabled = False
        self._lock = threading.Lock()
        self._done: dict[tuple[str, str], dict] = {}
        self._running: dict[tuple[str, str], threading.Event] = {}

    def _cache_key(self, base_url: str, key_var: str) -> tuple[str, str] | None:
        key = os.environ.get(key_var) or ""
        return (base_url, fingerprint(base_url, key)) if key else None

    def _run(self, ck: tuple[str, str], base_url: str, key_var: str, ev: threading.Event) -> None:
        try:
            key = os.environ.get(key_var) or ""
            if not key or fingerprint(base_url, key) != ck[1]:
                res = {"state": UNCHECKED, "status": None, "models": None}   # the variable changed meanwhile
            else:
                try:
                    res = self.probe(base_url, key)
                except Exception:  # noqa: BLE001 — the client missing or failing: nothing is known of the key
                    res = {"state": UNCHECKED, "status": None, "models": None}
            with self._lock:
                self._done[ck] = {**res, "checked_at": _now()}
        finally:
            with self._lock:
                self._running.pop(ck, None)
            ev.set()

    def start(self, endpoints, recheck: bool = False) -> list[threading.Event]:
        """Start a check for each (base_url, key_var) not yet checked under its current key (every
        one, with recheck); a check in flight is joined, never doubled."""
        if not (self.enabled and enabled_by_env()):
            return []
        events = []
        for base_url, key_var in endpoints:
            ck = self._cache_key(base_url, key_var)
            if ck is None:
                continue
            with self._lock:
                if ck in self._running:
                    events.append(self._running[ck])
                    continue
                if ck in self._done and not recheck:
                    continue
                self._done.pop(ck, None)
                ev = self._running[ck] = threading.Event()
            threading.Thread(target=self._run, args=(ck, base_url, key_var, ev), daemon=True,
                             name="key-check").start()
            events.append(ev)
        return events

    def ensure(self, endpoints, wait: float = WAIT_S, recheck: bool = False) -> None:
        """Start what is unchecked and wait, at most ``wait`` seconds in all, for every check in flight."""
        deadline = time.monotonic() + wait
        for ev in self.start(endpoints, recheck=recheck):
            ev.wait(max(0.0, deadline - time.monotonic()))

    def verdict(self, base_url: str, key_var: str, model: str = "", gateway: bool = False) -> dict:
        """The row's verdict from the cache, never a request: state, HTTP status, when, scope, whether
        the row's model is in the listing (None when nothing was listed), and the reason in words."""
        ck = self._cache_key(base_url, key_var)
        res, running = None, False
        if ck is not None and self.enabled and enabled_by_env():
            with self._lock:
                res = self._done.get(ck)
                running = ck in self._running
        if res is None:
            why = ("set " + key_var if ck is None else
                   "the key check is off (KG_KEY_CHECK)" if not enabled_by_env() else
                   "the key check is still running" if self.enabled and running else "the key was not checked")
            return {"state": UNCHECKED, "status": None, "checked_at": None, "scope": "gateway" if gateway else "key",
                    "model_listed": None, "why": why}
        listed = res.get("models")
        in_list = None if listed is None or not model else any(m == model or m.rsplit("/", 1)[-1] == model for m in listed)
        return {"state": res["state"], "status": res["status"], "checked_at": res["checked_at"],
                "scope": "gateway" if gateway else "key", "model_listed": in_list,
                "why": _why(res["state"], res["status"], key_var, gateway, bool(res.get("open")))}


CHECKER = Checker()
