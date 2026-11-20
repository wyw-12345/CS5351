"""ADR-0001 target tests. Missing behavior remains red, never skipped."""
import copy
import unittest

from src.feedback_engine import evaluate
from test.support import ESSAY, PROMPT, RUBRIC, SETTINGS, envelope, feedback, transport


class ConfidenceTests(unittest.TestCase):
    def run_case(self, payload):
        return evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, transport(envelope(payload)), mode="test_fixture")

    def valid(self):
        payload = feedback()
        for item in payload["criteria"]:
            item["confidence"] = 0.80
        return payload

    def test_missing_confidence_escalates(self):
        """REQ-FUNC-002, REQ-FUNC-003, REQ-FUNC-008: confidence has no passing default."""
        result = self.run_case(feedback())
        self.assertEqual(result["status"], "escalated")
        self.assertEqual(result["reason"], "invalid_confidence")

    def test_invalid_confidence_escalates(self):
        """REQ-FUNC-003, REQ-INV-002: null/bool/nonfinite/out-of-range confidence is rejected."""
        for value in (None, True, "NaN", "Infinity", -0.1, 1.1, "not-a-number"):
            payload = self.valid()
            payload["criteria"][0]["confidence"] = value
            with self.subTest(value=value):
                result = self.run_case(payload)
                self.assertEqual(result["status"], "escalated")
                self.assertEqual(result["reason"], "invalid_confidence")

    def test_confidence_079_escalates(self):
        """REQ-FUNC-003, REQ-FUNC-008: 0.79 is below the fixed policy threshold."""
        payload = self.valid()
        payload["criteria"][0]["confidence"] = 0.79
        result = self.run_case(payload)
        self.assertEqual(result["status"], "escalated")
        self.assertEqual(result["reason"], "low_confidence")

    def test_confidence_exactly_080_passes_confidence_check(self):
        """REQ-FUNC-003: exactly 0.80 passes when all other rules pass."""
        self.assertEqual(self.run_case(self.valid())["status"], "pending_review")

    def test_confidence_pass_but_other_rule_fails_escalates(self):
        """REQ-FUNC-003, REQ-SEC-002: confidence never waives membership/evidence/uncertainty."""
        for kind in ("unknown", "missing", "bad_quote", "uncertain", "over_max"):
            payload = copy.deepcopy(self.valid())
            if kind == "unknown":
                payload["criteria"][0]["criterion_id"] = "invented"
            elif kind == "missing":
                payload["criteria"].pop()
            elif kind == "bad_quote":
                payload["criteria"][0]["evidence_quote"] = "absent evidence"
            elif kind == "uncertain":
                payload["criteria"][0]["uncertain"] = True
                payload["criteria"][0]["suggested_score"] = None
            else:
                payload["criteria"][0]["suggested_score"] = "1000"
            with self.subTest(kind=kind):
                self.assertEqual(self.run_case(payload)["status"], "escalated")
