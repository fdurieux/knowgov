"""Zero-dependency test runner (pytest-compatible test functions).

A test that lacks a prerequisite raises tests/_skip.py's Skip and is counted as skipped, never as passed
(task-0141.01, ENV-04); KG_TEST_REQUIRE names the prerequisites this job installs, whose skip fails.
With KG_TEST_REPORT naming a file, the run's outcomes are written there as JSON as well (task-0159):
every test with its module, pass, fail or skip, the skip's reason or the failure's first line, and its
seconds, then the totals."""
import importlib, json, os, pathlib, sys, time, traceback
sys.path.insert(0, ".")
# task-0075: no test reads the wall clock through harness/review.py today(); one that needs a day pins
# it (KG_TODAY), and one that does not fails here rather than on the day its outcome would move
os.environ["KG_CLOCK"] = "pinned"
REQUIRED = {r.strip() for r in os.environ.get("KG_TEST_REQUIRE", "").split(",") if r.strip()}
REPORT = os.environ.get("KG_TEST_REPORT")

failed = total = skipped = 0
outcomes = []
for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
    mod = importlib.import_module(f"tests.{path.stem}")
    tests = [(n, f) for n, f in vars(mod).items() if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        total += 1
        t0 = time.monotonic()
        row = {"module": path.stem, "test": name}
        try:
            fn()
            print(f"PASS {name}")
            row["outcome"] = "pass"
        except Exception as e:
            prerequisite = getattr(e, "prerequisite", None) if type(e).__name__ == "Skip" else None
            if prerequisite and prerequisite not in REQUIRED:
                skipped += 1
                print(f"SKIP {name} ({e})")
                row.update(outcome="skip", prerequisite=prerequisite, reason=str(e))
            else:
                failed += 1
                print(f"FAIL {name}" + (f" (required prerequisite missing: {e})" if prerequisite else ""))
                if not prerequisite:
                    traceback.print_exc()
                row.update(outcome="fail", reason=(f"required prerequisite missing: {e}" if prerequisite
                                                   else f"{type(e).__name__}: {str(e).splitlines()[0][:300] if str(e) else ''}"))
        row["seconds"] = round(time.monotonic() - t0, 3)
        outcomes.append(row)
print(f"\n{total - failed - skipped}/{total} passed, {skipped} skipped, {failed} failed")
if REPORT:
    report = {"schema": "test-outcomes", "version": 1, "subject": os.environ.get("KG_SUBJECT") or "",
              "required": sorted(REQUIRED), "python": sys.version.split()[0],
              "totals": {"tests": total, "passed": total - failed - skipped, "skipped": skipped, "failed": failed},
              "tests": outcomes}
    pathlib.Path(REPORT).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(REPORT).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
sys.exit(1 if failed else 0)
