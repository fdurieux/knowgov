"""A test that cannot run here says so (task-0141.01, ENV-04): it raises Skip naming the prerequisite it
lacks, and tests/run_tests.py counts it apart from the passes. A prerequisite named in KG_TEST_REQUIRE
(comma-separated; harness.yml's rdflib job names rdflib) turns its skip into a failure, so a job that
installs a prerequisite proves the tests resting on it rather than reporting them passed unrun.

Prerequisites: rdflib (the pins), hook-live (KG_HOOK_LIVE=1, the live hook against a store) and
register-rows (a subject whose register_map.toml has rows; J-F has none) and node (the page's own script,
run by tests/test_arms_execution.py; the rdflib job requires it)."""
import importlib


class Skip(Exception):
    def __init__(self, prerequisite: str, reason: str):
        super().__init__(f"{prerequisite}: {reason}")
        self.prerequisite = prerequisite
        self.reason = reason


def skip(prerequisite: str, reason: str):
    raise Skip(prerequisite, reason)


def need_rdflib():
    """The rdflib adapter's module, or a skip naming rdflib (the tests job installs no pins)."""
    try:
        return importlib.import_module("store_rdflib")
    except ModuleNotFoundError as e:
        skip("rdflib", f"{e.name} is not installed")
