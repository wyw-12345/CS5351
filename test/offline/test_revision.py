"""C baseline / ADR-0001..0003: independent revision acceptance, synthetic data only."""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.contracts import canonical, digest
from src.feedback_engine import ConfidenceError, confidence_value, evaluate
from src.grade_store import GradeStore, approval_binding, sign_approval
from test.support import ESSAY, PROMPT, RUBRIC, SCORES, SETTINGS, envelope, feedback


def advice_payload():
    value = feedback()
    for item in value["criteria"]:
        item["confidence"] = "0.90"
    return value


def advice(value=None):
    payload = advice_payload() if value is None else value
    return evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS,
                    lambda body, settings: envelope(payload), mode="revision_fixture")


class ConfidenceTests(unittest.TestCase):
    def test_boundaries(self):
        """REQ-FUNC-003, REQ-FUNC-008: missing, invalid, below threshold and inclusive boundary."""
        for value, reason in [(None, "invalid_confidence"), (True, "invalid_confidence"),
                              ("NaN", "invalid_confidence"), (float("inf"), "invalid_or_unavailable_provider_response"),
                              (-0.1, "invalid_confidence"), (1.1, "invalid_confidence"),
                              ({}, "invalid_confidence"), ("0.79", "low_confidence"),
                              ("0.80", None), (0.8, None), (1, None)]:
            with self.subTest(value=value):
                payload = advice_payload()
                payload["criteria"][0]["confidence"] = value
                result = advice(payload)
                self.assertEqual(result["reason"], reason)
                self.assertEqual(result["status"], "pending_review" if reason is None else "escalated")
        payload = advice_payload()
        del payload["criteria"][0]["confidence"]
        self.assertEqual(advice(payload)["reason"], "invalid_confidence")

    def test_nonfinite_confidence_directly_rejected(self):
        """REQ-FUNC-003 / REQ-SEC-007: direct nonfinite values and JSON constants both refuse."""
        for value in [float("inf"), float("nan"), float("-inf")]:
            with self.assertRaises(ConfidenceError):
                confidence_value(value)

    def test_confidence_does_not_waive_other_rules(self):
        """REQ-INV-002 / REQ-SEC-002: confidence never waives criterion or quotation checks."""
        for change in [{"criterion_id": "invented"}, {"evidence_quote": "made up"},
                       {"uncertain": True}, {"suggested_score": "11"}]:
            payload = advice_payload()
            payload["criteria"][0].update(change)
            self.assertEqual(advice(payload)["status"], "escalated")

    def test_total_is_ignored_without_input_mutation(self):
        """REQ-INV-001: discard only untrusted top-level final_score."""
        payload = advice_payload()
        payload["final_score"] = {"malicious": 100}
        before = copy.deepcopy(payload)
        result = advice(payload)
        self.assertEqual(result["status"], "pending_review")
        self.assertNotIn("final_score", result["feedback"])
        self.assertEqual(payload, before)
        payload["other"] = "invalid"
        self.assertEqual(advice(payload)["status"], "escalated")


class SignedStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "grades.sqlite3"
        self.key = Ed25519PrivateKey.generate()
        self.trust = {"teacher-key": {"teacher_id": "teacher-1",
                                     "public_key": self.key.public_key().public_bytes_raw().hex()}}
        self.store = GradeStore(self.path, trusted_keys=self.trust)
        self.addCleanup(self.store.close)
        self.advice = advice()
        self.record = self.store.create(ESSAY, RUBRIC, self.advice, submission_id="submission-1")

    def signed(self, record=None, scores=None, reason="", key=None, key_id="teacher-key"):
        return sign_approval(key or self.key, key_id, approval_binding(
            record or self.record, scores or SCORES, "Teacher label", reason))

    def approve(self, record=None, scores=None, reason="", approval=None):
        record = record or self.record
        return self.store.approve(record["id"], record["hash"], scores or SCORES,
                                  "Teacher label", reason, approval=approval or self.signed(
                                      record, scores, reason))

    def test_approved_score_and_private_audit(self):
        """REQ-INV-001, REQ-INV-003, REQ-INV-006 / REQ-QUAL-005: signed approval recomputes; audit has no essay."""
        self.assertIsNone(self.record["final_score"])
        result = self.approve()
        self.assertEqual(result["final_score"], "72.00")
        self.assertEqual(result["audit"]["verified_teacher_id"], "teacher-1")
        self.assertEqual(result["audit"]["confirmed_scores_sha256"], digest(SCORES))
        self.assertNotIn(ESSAY, canonical(result["audit"]))
        self.assertNotIn("essay", result["audit"])
        self.assertEqual(result["approval_authentication"], "verified")

    def test_unknown_forged_and_missing_signature(self):
        """REQ-INV-003: reject unknown key, forged signature, missing and boolean credentials."""
        forged = self.signed()
        forged["signature"] = "00" * 64
        for credential in [None, True, {}, self.signed(key_id="unknown"),
                           self.signed(key=Ed25519PrivateKey.generate()), forged]:
            with self.subTest(credential=str(type(credential))), self.assertRaises((ValueError, PermissionError)):
                self.store.approve(self.record["id"], self.record["hash"], SCORES,
                                   "Teacher label", approval=credential)
            self.assertIsNone(self.store.get(self.record["id"])["final_score"])

    def test_score_substitution_and_replay(self):
        """REQ-INV-003: a valid signature cannot approve another valid score set or proposal."""
        signed = self.signed()
        with self.assertRaises((ValueError, PermissionError)):
            self.approve(scores={"content": "9", "structure": "6"}, approval=signed)
        other = self.store.create(ESSAY, RUBRIC, self.advice, submission_id="submission-2")
        with self.assertRaises((ValueError, PermissionError)):
            self.approve(record=other, approval=signed)
        self.assertIsNone(self.store.get(other["id"])["final_score"])

    def test_rubric_version_and_reason_bound(self):
        """REQ-INV-003, REQ-INV-006: rubric version and human resolution reason are signed."""
        for field, value in [("rubric_version", "changed"), ("reason", "changed"),
                             ("submission_id", "changed")]:
            signed = self.signed()
            signed["binding"][field] = value
            with self.assertRaises((ValueError, PermissionError)):
                self.approve(approval=signed)

    def test_idempotency_and_conflicts(self):
        """REQ-FUNC-009 / REQ-INV-008: stable request returns one record; conflicts never overwrite."""
        self.assertEqual(self.store.create(ESSAY, RUBRIC, self.advice,
                                          submission_id="submission-1"), self.record)
        first = self.approve()
        self.assertEqual(self.approve(), first)
        self.assertEqual(self.store.create(ESSAY, RUBRIC, self.advice,
                                          submission_id="submission-1"), first)
        with self.assertRaises(ValueError):
            self.store.create(ESSAY + " Changed.", RUBRIC, self.advice, submission_id="submission-1")
        with self.assertRaises((ValueError, PermissionError)):
            self.approve(scores={"content": "9", "structure": "6"})
        self.assertEqual(self.store.get(self.record["id"]), first)

    def test_manual_resolution(self):
        """REQ-FUNC-008: low confidence can be resolved only with signed full scores and reason."""
        payload = advice_payload()
        payload["criteria"][0]["confidence"] = "0.79"
        record = self.store.create(ESSAY, RUBRIC, advice(payload), submission_id="low")
        with self.assertRaises(ValueError):
            self.approve(record=record)
        self.assertEqual(self.approve(record=record, reason="Reviewed all criteria")["final_score"], "72.00")

    def test_store_revalidates_confidence(self):
        """REQ-INV-002: forged pending status cannot bypass confidence validation."""
        payload = advice_payload()
        payload["criteria"][0]["confidence"] = "0.79"
        bad = advice(payload)
        bad.update(status="pending_review", reason=None)
        with self.assertRaises(ValueError):
            self.store.create(ESSAY, RUBRIC, bad, submission_id="forged")

    def test_atomic_rollback(self):
        """REQ-INV-006: failure between status and grade updates rolls back both."""
        self.store.connection.execute("CREATE TRIGGER fail_grade BEFORE INSERT ON grades "
                                      "BEGIN SELECT RAISE(ABORT, 'fixture failure'); END")
        with self.assertRaises(sqlite3.Error):
            self.approve()
        self.assertEqual(self.store.get(self.record["id"])["status"], "pending_review")
        self.assertEqual(self.store.connection.execute("SELECT count(*) FROM grades").fetchone()[0], 0)

    def test_read_detects_resigned_digest_tampering(self):
        """REQ-INV-001, REQ-INV-003: recalculated hashes cannot hide altered signed scores."""
        result = self.approve()
        audit = result["audit"]
        audit["accepted_scores"]["content"] = "9"
        audit["confirmed_scores_sha256"] = digest(audit["accepted_scores"])
        audit["final_score"] = "78.00"
        self.store.connection.execute("UPDATE grades SET audit=?,digest=?,score=?",
                                      (canonical(audit), digest(audit), "78.00"))
        with self.assertRaises((ValueError, PermissionError)):
            self.store.get(self.record["id"])

    def test_reopen_and_default_deny(self):
        """REQ-INV-003, REQ-INV-006: restart re-verifies signature using operator trust configuration."""
        first = self.approve()
        with GradeStore(self.path, trusted_keys=self.trust) as reopened:
            self.assertEqual(reopened.get(first["id"]), first)
        with GradeStore(self.path) as untrusted:
            with self.assertRaises(PermissionError):
                untrusted.get(first["id"])


if __name__ == "__main__":
    unittest.main()
