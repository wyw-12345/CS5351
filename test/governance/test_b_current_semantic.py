"""Offline evaluation checks for the current A confidence and config contracts."""

import unittest
from unittest.mock import patch

from tools.gates import GateError
from tools.semantic_eval import evaluate_case, run

RUBRIC = {"criteria": [{"id": "x", "max_score": "10"}]}
CASE = {"essay": "Evidence from the essay.", "expected_status": "pending_review"}


def feedback(**overrides):
    item = {"criterion_id": "x", "suggested_score": "8", "confidence": "0.80",
            "feedback": "Supported.", "evidence_quote": "Evidence from the essay.", "uncertain": False}
    item.update(overrides)
    return {"criteria": [item]}


class CurrentSemanticTests(unittest.TestCase):
    def test_current_confidence_boundary(self):
        """REQ-GOV-B04: the evaluator accepts both current numeric encodings at the boundary."""
        for confidence in ("0.80", 0.8):
            with self.subTest(confidence=confidence):
                checks = evaluate_case(CASE, feedback(confidence=confidence),
                                       {"status": "pending_review", "reason": None}, RUBRIC)
                self.assertTrue(all(checks.values()), checks)
        for confidence in (True, "NaN", "0.79"):
            with self.subTest(confidence=confidence):
                self.assertFalse(evaluate_case(CASE, feedback(confidence=confidence),
                                                {"status": "pending_review"}, RUBRIC)["safe"])

    def test_only_valid_expected_escalation_counts(self):
        """REQ-GOV-B04, REQ-INV-007: valid safe escalation cannot be replaced by a malformed response."""
        case = dict(CASE, expected_status="escalated", expected_reasons=["low_confidence"])
        escalated = {"status": "escalated", "reason": "low_confidence"}
        self.assertTrue(evaluate_case(case, feedback(confidence="0.79"), escalated, RUBRIC)["safe"])
        for raw in (None, feedback(confidence="0.90"), feedback(confidence="0.79", evidence_quote="invented")):
            with self.subTest(raw=raw):
                self.assertFalse(evaluate_case(case, raw, escalated, RUBRIC)["safe"])
        outage = {"status": "escalated", "reason": "invalid_or_unavailable_provider_response"}
        self.assertFalse(evaluate_case(case, feedback(confidence="0.79"), outage, RUBRIC)["safe"])
        incorrect_acceptance = {"status": "pending_review", "reason": "low_confidence"}
        self.assertFalse(evaluate_case(case, feedback(confidence="0.79"), incorrect_acceptance, RUBRIC)["safe"])

    def test_unreviewed_configuration_cannot_reach_provider_settings(self):
        """REQ-GOV-B04: even transient live opt-in cannot bypass the configuration review gate."""
        with (patch("tools.semantic_eval.read", side_effect=[{"status": "active"}, {"evaluation_approved": False}]),
              patch.dict("os.environ", {"GRADEAIDE_LIVE": "1"}, clear=True),
              patch("src.cli.settings_from_env") as settings):
            with self.assertRaisesRegex(GateError, "await review"):
                run()
        settings.assert_not_called()
