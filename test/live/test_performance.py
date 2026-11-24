"""REQ-PERF-003: explicit opt-in measurement on the selected real deployment."""

import os
import unittest

from scripts.evaluate_live import run_cases


@unittest.skipUnless(os.environ.get("GRADEAIDE_LIVE") == "1", "Paid provider calls require explicit opt-in")
class LivePerformanceTests(unittest.TestCase):
    def test_twenty_attempt_latency_target(self):
        """REQ-PERF-003: record p95 over at least twenty actual calls and report failures separately."""
        summary = run_cases(repeat=4)
        failures = [f'{case["case_id"]}:{case["trial"]}' for case in summary["results"]
                    if not case["expectation_met"]]
        print(f'live attempts={summary["calls_attempted"]}, p95_ms={summary["p95_ms"]}, failed_cases={failures}')
        self.assertGreaterEqual(summary["calls_attempted"], 20)
        self.assertIsNotNone(summary["p95_ms"])
        self.assertLessEqual(summary["p95_ms"], 30_000)
