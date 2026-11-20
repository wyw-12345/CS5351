"""Unittest runner rejecting empty or skipped release suites. REQ-GOV-B05."""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path


def acceptable(result: unittest.TestResult) -> bool:
    return result.testsRun > 0 and result.wasSuccessful() and not result.skipped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    suite = unittest.defaultTestLoader.discover(args.folder)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not acceptable(result):
        print("BLOCKED: suite failed, collected no tests, or skipped required tests", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
