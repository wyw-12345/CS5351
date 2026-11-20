"""REQ-INV-002 / REQ-COST-004: evaluation errors must not count as correct model refusals."""

import os
import unittest
from unittest.mock import patch

from scripts.evaluate_live import run_cases
from src.contracts import ValidationError
from test.support import SETTINGS


class LiveRunnerTests(unittest.TestCase):
    def test_direct_helper_requires_explicit_opt_in(self):
        """REQ-COST-004: direct helper requires explicit opt in."""
        with patch.dict(os.environ, {"GRADEAIDE_LIVE": "0"}), \
             patch("scripts.evaluate_live.evaluate") as provider:
            with self.assertRaises(ValidationError):
                run_cases()
            provider.assert_not_called()

    @patch.dict(os.environ, {"GRADEAIDE_LIVE": "1"})
    def test_transport_failure_is_not_a_correct_uncertainty_response(self):
        """REQ-COST-004: transport failure is not a correct uncertainty response."""
        for usage in [None, {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}]:
            failed = {"status": "escalated", "reason": "invalid_or_unavailable_provider_response",
                      "metadata": {"calls": 1, "latency_ms": 1, "usage": usage}}
            with patch("scripts.evaluate_live.settings_from_env", return_value=SETTINGS), \
                 patch("scripts.evaluate_live.evaluate", return_value=failed):
                results = run_cases()
            self.assertEqual(results["expected_status_match_count"], 0)
            uncertain = next(item for item in results["results"] if item["case_id"] == "unverifiable-data")
            self.assertFalse(uncertain["expectation_met"])


if __name__ == "__main__":
    unittest.main()
