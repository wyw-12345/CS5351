"""T2/T3: REQ-FUNC-002, REQ-INV-002, REQ-SEC-002, REQ-COST-001..005."""

import copy
import json
import unittest
from dataclasses import replace

from src.contracts import ValidationError
from src.feedback_engine import evaluate
from test.support import ESSAY, PROMPT, RUBRIC, SETTINGS, envelope, feedback, transport


class FeedbackTests(unittest.TestCase):
    def run_advice(self, response=None, settings=SETTINGS, essay=ESSAY):
        return evaluate(essay, RUBRIC, PROMPT, settings, transport(response), mode="test_fixture")

    def test_valid_feedback_and_request_contract(self):
        """REQ-COST-001 / REQ-FUNC-002: valid feedback and request contract."""
        requests = []

        def capture(body, settings):
            requests.append(copy.deepcopy(body))
            return envelope()

        result = evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, capture)
        self.assertEqual(result["status"], "pending_review")
        self.assertNotIn("final_score", result)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["max_tokens"], 1024)
        self.assertNotIn("tools", requests[0])
        self.assertEqual(requests[0]["response_format"], {"type": "json_object"})
        self.assertEqual(result["metadata"]["usage"]["total_tokens"], 180)
        self.assertEqual(result["metadata"]["reported_usage_cost"], "0.00026")
        self.assertEqual(len(result["metadata"]["prompt_hash"]), 64)

    def test_reject_final_score_extra_unknown_duplicate_and_missing_criteria(self):
        """REQ-FUNC-003 / REQ-SEC-002: reject final score extra unknown duplicate and missing criteria."""
        supplied_total = feedback()
        supplied_total["final_score"] = "100"
        normalized = self.run_advice(envelope(supplied_total))
        self.assertEqual(normalized["status"], "pending_review")
        self.assertNotIn("final_score", normalized["feedback"])
        invalid = []
        value = feedback()
        value["unexpected_field"] = "100"
        invalid.append(value)
        for field, value in [("criterion_id", "invented"), ("suggested_score", "11"),
                             ("suggested_score", True), ("suggested_score", "NaN"),
                             ("feedback", ""), ("evidence_quote", "This quote is invented."),
                             ("uncertain", "false")]:
            altered = feedback()
            altered["criteria"][0][field] = value
            invalid.append(altered)
        repeated = feedback()
        repeated["criteria"][1]["criterion_id"] = "content"
        invalid.extend([repeated, {"criteria": feedback()["criteria"][:1]}])
        for value in invalid:
            with self.subTest(value=value):
                self.assertEqual(self.run_advice(envelope(value))["status"], "escalated")

    def test_uncertain_null_is_an_escalation_not_a_zero_score(self):
        """REQ-FUNC-003 / REQ-INV-002: uncertain null is an escalation not a zero score."""
        value = feedback()
        value["criteria"][0].update(suggested_score=None, uncertain=True, evidence_quote="")
        result = self.run_advice(envelope(value))
        self.assertEqual(result["reason"], "uncertain_criterion")
        self.assertIsNone(result["feedback"]["criteria"][0]["suggested_score"])
        self.assertNotIn("final_score", result)

    def test_bad_content_preserves_valid_usage(self):
        """REQ-INV-002: bad content preserves valid usage."""
        for reason, content in [("length", "incomplete"), ("stop", "   "), ("stop", "{bad}")]:
            value = envelope()
            value["choices"][0]["finish_reason"] = reason
            value["choices"][0]["message"]["content"] = content
            result = self.run_advice(value)
            self.assertEqual(result["status"], "escalated")
            self.assertEqual(result["metadata"]["usage"], value["usage"])
            self.assertEqual(result["metadata"]["reported_usage_cost"], "0.00026")

    def test_refusal_tools_invalid_choices_and_missing_model_escalate(self):
        """REQ-INV-002: refusal tools invalid choices and missing model escalate."""
        variants = []
        for key in ["refusal", "tool_calls", "function_call"]:
            value = envelope()
            value["choices"][0]["message"][key] = "attempt"
            variants.append(value)
        variants.extend([{**envelope(), "choices": []}, {**envelope(), "model": None}])
        wrong_role = envelope()
        wrong_role["choices"][0]["message"]["role"] = "user"
        variants.append(wrong_role)
        for value in variants:
            self.assertEqual(self.run_advice(value)["status"], "escalated")

    def test_wrong_top_level_envelope_escalates(self):
        """REQ-INV-002: wrong top level envelope escalates."""
        for value in [[], "bad", None]:
            result = evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, lambda *_: value)
            self.assertEqual(result["status"], "escalated")

    def test_missing_or_invalid_usage_never_becomes_zero(self):
        """REQ-COST-004: missing or invalid usage never becomes zero."""
        for usage in [None, {}, {"prompt_tokens": True, "completion_tokens": 80, "total_tokens": 81},
                      {"prompt_tokens": -1, "completion_tokens": 80, "total_tokens": 79},
                      {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 999}]:
            result = self.run_advice({**envelope(), "usage": usage})
            self.assertEqual(result["status"], "escalated")
            self.assertIsNone(result["metadata"]["usage"])
            self.assertIsNone(result["metadata"]["reported_usage_cost"])

    def test_provider_over_output_cap_escalates_but_usage_survives(self):
        """REQ-COST-004: provider over output cap escalates but usage survives."""
        usage = {"prompt_tokens": 100, "completion_tokens": 1025, "total_tokens": 1125}
        result = self.run_advice({**envelope(), "usage": usage})
        self.assertEqual(result["status"], "escalated")
        self.assertEqual(result["metadata"]["usage"], usage)

    def test_input_and_monetary_budget_block_before_transport(self):
        """REQ-COST-002 / REQ-COST-003 / REQ-COST-005 / REQ-FUNC-008: input and monetary budget block before transport."""
        def forbidden(*_):
            self.fail("over-budget input must make no request")

        for settings, reason in [(replace(SETTINGS, max_input_bytes=1), "input_budget_exceeded"),
                                 (replace(SETTINGS, max_cost="0"), "cost_budget_exceeded")]:
            result = evaluate(ESSAY, RUBRIC, PROMPT, settings, forbidden)
            self.assertEqual(result["reason"], reason)
            self.assertEqual(result["metadata"]["calls"], 0)

    def test_context_boundary_counts_utf8_bytes(self):
        """REQ-INV-002: context boundary counts utf8 bytes."""
        result = self.run_advice()
        exact_bytes = result["metadata"]["input_bytes"]
        self.assertEqual(self.run_advice(settings=replace(SETTINGS, max_input_bytes=exact_bytes))["status"],
                         "pending_review")
        self.assertEqual(self.run_advice(settings=replace(SETTINGS, max_input_bytes=exact_bytes - 1))["reason"],
                         "input_budget_exceeded")
        chinese = self.run_advice(essay="雨水再利用。")
        self.assertGreater(chinese["metadata"]["input_bytes"], len("雨水再利用。"))

    def test_transport_failure_escalates_without_retry_or_secrets(self):
        """REQ-PERF-002: transport failure escalates without retry or secrets."""
        count = 0

        def failed(*_):
            nonlocal count
            count += 1
            raise OSError("private-api-key")

        result = evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, failed)
        self.assertEqual(count, 1)
        self.assertEqual(result["status"], "escalated")
        self.assertNotIn("private-api-key", json.dumps(result))

    def test_configuration_rejects_unsafe_endpoints_prices_and_limits(self):
        """REQ-COST-003: configuration rejects unsafe endpoints prices and limits."""
        for field, value in [("endpoint", "http://outside.example/chat"),
                             ("endpoint", "https://user:secret@example.test/chat"),
                             ("endpoint", "https://example.test/chat?key=secret"),
                             ("endpoint", "file:///etc/passwd"),
                             ("endpoint", "https://[bad"),
                             ("input_price", "NaN"), ("max_cost", "-1"),
                             ("timeout", float("nan")), ("timeout", 0),
                             ("max_output_tokens", True), ("max_input_bytes", 0)]:
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                replace(SETTINGS, **{field: value}).validate()

    def test_settings_repr_does_not_disclose_key(self):
        """REQ-SEC-004: settings repr does not disclose key."""
        self.assertNotIn(SETTINGS.api_key, repr(SETTINGS))


if __name__ == "__main__":
    unittest.main()
