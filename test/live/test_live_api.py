"""T7 live only: REQ-FUNC-002, REQ-INV-002, REQ-SEC-002, REQ-PERF-003 pending >=20 calls."""

import json
import os
import unittest

from scripts.evaluate_live import ROOT, run_cases
from src.cli import settings_from_env
from src.contracts import parse_json, read_text
from src.feedback_engine import evaluate


@unittest.skipUnless(os.environ.get("GRADEAIDE_LIVE") == "1", "Live API not enabled; set key/config and GRADEAIDE_LIVE=1")
class LiveTests(unittest.TestCase):
    def test_real_provider_smoke(self):
        """REQ-FUNC-002, REQ-FUNC-003: new prompt must emit validated confidence in a real call."""
        advice = evaluate(read_text(ROOT / "examples/essay.txt"),
                          parse_json(read_text(ROOT / "examples/rubric.json")),
                          parse_json(read_text(ROOT / "prompts/prompt_v1.2.yaml")), settings_from_env())
        self.assertEqual(advice["status"], "pending_review", advice["reason"])
        self.assertIsNotNone(advice["metadata"]["usage"])
        self.assertNotIn("final_score", advice)

    def test_fixed_synthetic_cases(self):
        """REQ-GOV-B04: explicit paid fixed-set replay; no semantic approval implied."""
        results = run_cases()
        target = ROOT / "evidence/live-test-results.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        for item in results["results"]:
            with self.subTest(case=item["case_id"]):
                self.assertTrue(item["expectation_met"], item["advice"]["reason"])
                self.assertNotIn("final_score", item["advice"])


if __name__ == "__main__":
    unittest.main()
