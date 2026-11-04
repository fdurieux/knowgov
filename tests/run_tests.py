"""Zero-dependency test runner (pytest-compatible test functions)."""
import importlib, os, pathlib, sys, traceback
sys.path.insert(0, ".")
# task-0075: no test reads the wall clock through harness/review.py today(); one that needs a day pins
# it (KG_TODAY), and one that does not fails here rather than on the day its outcome would move
os.environ["KG_CLOCK"] = "pinned"

failed = total = 0
for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
    mod = importlib.import_module(f"tests.{path.stem}")
    tests = [(n, f) for n, f in vars(mod).items() if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        total += 1
        try:
            fn()
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
print(f"\n{total - failed}/{total} passed")
sys.exit(1 if failed else 0)
