"""
run_tests.py
Run all unit tests with a coverage summary.

Usage:
    python run_tests.py
    python run_tests.py --verbose
"""

import unittest
import sys


def run_all_tests(verbosity=2):
    loader = unittest.TestLoader()
    suite  = loader.discover("tests", pattern="test_*.py")

    print("=" * 60)
    print("  AI Resume Screener — Test Suite")
    print("=" * 60)
    print()

    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)

    print()
    print("=" * 60)
    total   = result.testsRun
    passed  = total - len(result.failures) - len(result.errors)
    failed  = len(result.failures) + len(result.errors)
    print(f"  TOTAL : {total}")
    print(f"  PASSED: {passed}  ({100*passed//total if total else 0}%)")
    print(f"  FAILED: {failed}")
    print("=" * 60)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    sys.exit(run_all_tests(verbosity=2 if verbose else 1))
