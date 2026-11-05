"""Zero-dependency test runner (pytest-compatible test functions).

A test that lacks a prerequisite raises tests/_skip.py's Skip and is counted as skipped, never as passed
(task-0141.01, ENV-04); KG_TEST_REQUIRE names the prerequisites this job installs, whose skip fails."""
import importlib, os, pathlib, sys, traceback
sys.path.insert(0, ".")
# task-0075: no test reads the wall clock through harness/review.py today(); one that needs a day pins
# it (KG_TODAY), and one that does not fails here rather than on the day its outcome would move
os.environ["KG_CLOCK"] = "pinned"
REQUIRED = {r.strip() for r in os.environ.get("KG_TEST_REQUIRE", "").split(",") if r.strip()}

failed = total = skipped = 0
for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
    mod = importlib.import_module(f"tests.{path.stem}")
    tests = [(n, f) for n, f in vars(mod).items() if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        total += 1
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:
            prerequisite = getattr(e, "prerequisite", None) if type(e).__name__ == "Skip" else None
            if prerequisite and prerequisite not in REQUIRED:
                skipped += 1
                print(f"SKIP {name} ({e})")
                continue
            failed += 1
            print(f"FAIL {name}" + (f" (required prerequisite missing: {e})" if prerequisite else ""))
            if not prerequisite:
                traceback.print_exc()
print(f"\n{total - failed - skipped}/{total} passed, {skipped} skipped, {failed} failed")
sys.exit(1 if failed else 0)
