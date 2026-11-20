"""T4/T5: REQ-INV-001..004, explicit review and transactional persistent audit."""

import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.contracts import ValidationError, canonical, digest
from src.feedback_engine import evaluate
from src.grade_store import GradeStore, approval_binding, sign_approval
from test.support import ESSAY, PROMPT, RUBRIC, SCORES, SETTINGS, transport


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "grades.sqlite3"
        self.key = Ed25519PrivateKey.generate()
        self.trust = {"test-key": {"teacher_id": "fixture-teacher",
                                  "public_key": self.key.public_key().public_bytes_raw().hex()}}
        self.store = GradeStore(self.path, trusted_keys=self.trust)
        self.advice = evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, transport(), mode="test_fixture")
        self.proposal = self.store.create(ESSAY, RUBRIC, self.advice)

    def tearDown(self):
        self.store.close()
        self.folder.cleanup()

    def signed(self, proposal, scores, reviewer, reason=""):
        return sign_approval(self.key, "test-key", approval_binding(proposal, scores, reviewer, reason))

    def approve(self, **kwargs):
        scores = kwargs.get("scores", SCORES)
        reviewer = kwargs.get("reviewer", "synthetic-test-reviewer")
        reason = kwargs.get("reason", "")
        return self.store.approve(self.proposal["id"], kwargs.get("hash", self.proposal["hash"]),
                                  scores, reviewer, reason,
                                  approval=self.signed(self.proposal, scores, reviewer, reason))

    def test_proposal_has_no_grade_and_human_change_is_audited(self):
        """REQ-FUNC-005 / REQ-INV-001: proposal has no grade and human change is audited."""
        self.assertIsNone(self.proposal["final_score"])
        result = self.approve()
        self.assertEqual(result["final_score"], "72.00")
        self.assertEqual(result["proposal"]["advice"]["feedback"]["criteria"][1]["suggested_score"], "7")
        self.assertEqual(result["audit"]["accepted_scores"]["structure"], "6")
        self.assertEqual(result["audit"]["proposal_hash"], self.proposal["hash"])

    def test_missing_approval_details_and_stale_hash_are_rejected(self):
        """REQ-FUNC-006 / REQ-INV-003: missing approval details and stale hash are rejected."""
        for values in [{"reviewer": ""}, {"hash": "0" * 64}, {"scores": {"content": "8"}},
                       {"scores": {**SCORES, "final_score": "100"}}]:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                self.approve(**values)
            self.assertIsNone(self.store.get(self.proposal["id"])["final_score"])

    def test_duplicate_approval_cannot_overwrite_history(self):
        """REQ-FUNC-009 / REQ-INV-008: duplicate approval cannot overwrite history."""
        first = self.approve()
        with self.assertRaises(ValidationError):
            self.approve(scores={"content": "10", "structure": "10"})
        self.assertEqual(self.store.get(self.proposal["id"]), first)

    def test_escalation_requires_every_score_and_reason(self):
        """REQ-FUNC-006: escalation requires every score and reason."""
        advice = copy.deepcopy(self.advice)
        advice.update(status="escalated", reason="uncertain_criterion")
        advice["feedback"]["criteria"][0].update(uncertain=True, suggested_score=None)
        proposal = self.store.create(ESSAY, RUBRIC, advice)
        with self.assertRaises(ValidationError):
            self.store.approve(proposal["id"], proposal["hash"], SCORES, "test",
                               approval=self.signed(proposal, SCORES, "test"))
        result = self.store.approve(proposal["id"], proposal["hash"], SCORES, "test", "I reviewed all criteria.",
                                    approval=self.signed(proposal, SCORES, "test", "I reviewed all criteria."))
        self.assertEqual(result["final_score"], "72.00")

    def test_initial_advice_is_validated_at_storage_boundary(self):
        """REQ-INV-006: initial advice is validated at storage boundary."""
        for change in [{"status": "approved"}, {"feedback": None}, {"metadata": None}, {"reason": "oops"}]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                self.store.create(ESSAY, RUBRIC, {**self.advice, **change})
        advice = copy.deepcopy(self.advice)
        advice["feedback"]["criteria"][0]["uncertain"] = True
        with self.assertRaises(ValidationError):
            self.store.create(ESSAY, RUBRIC, advice)

    def test_failed_audit_insert_rolls_back_status_and_grade(self):
        """REQ-FUNC-006: failed audit insert rolls back status and grade."""
        self.store.connection.execute("""CREATE TRIGGER fail_grade BEFORE INSERT ON grades
                                      BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END""")
        with self.assertRaises(sqlite3.Error):
            self.approve()
        result = self.store.get(self.proposal["id"])
        self.assertEqual(result["status"], "pending_review")
        self.assertIsNone(result["final_score"])
        self.assertEqual(self.store.connection.execute("SELECT count(*) FROM grades").fetchone()[0], 0)

    def test_payload_and_grade_corruption_are_detected(self):
        """REQ-INV-006: payload and grade corruption are detected."""
        approved = self.approve()
        self.store.connection.execute("UPDATE grades SET score='100.00' WHERE proposal_id=?", (approved["id"],))
        with self.assertRaises(ValidationError):
            self.store.get(approved["id"])
        self.store.connection.execute("UPDATE proposals SET payload='{}' WHERE id=?", (approved["id"],))
        with self.assertRaises(ValidationError):
            self.store.get(approved["id"])

    def test_state_corruption_cannot_bypass_escalation_review(self):
        """REQ-INV-006: state corruption cannot bypass escalation review."""
        advice = {**self.advice, "status": "escalated", "reason": "requires_review"}
        proposal = self.store.create(ESSAY, RUBRIC, advice)
        self.store.connection.execute("UPDATE proposals SET status='pending_review' WHERE id=?", (proposal["id"],))
        with self.assertRaises(ValidationError):
            self.store.approve(proposal["id"], proposal["hash"], SCORES, "test")

    def test_inconsistent_previous_state_is_detected_even_with_recomputed_audit_digest(self):
        """REQ-INV-006: inconsistent previous state is detected even with recomputed audit digest."""
        approved = self.approve()
        audit = approved["audit"]
        audit["previous_status"] = "escalated"
        self.store.connection.execute("UPDATE grades SET audit=?,digest=? WHERE proposal_id=?",
                                      (canonical(audit), digest(audit), approved["id"]))
        with self.assertRaises(ValidationError):
            self.store.get(approved["id"])

    def test_reopen_preserves_exact_record(self):
        """REQ-INV-006 / REQ-QUAL-002 / REQ-QUAL-004: reopen preserves exact record."""
        expected = self.approve()
        with GradeStore(self.path, trusted_keys=self.trust) as another:
            self.assertEqual(another.get(self.proposal["id"]), expected)

    def test_unknown_id_is_refused(self):
        """REQ-FUNC-007: unknown id is refused."""
        with self.assertRaises(ValidationError):
            self.store.get("missing")

    def test_unsupported_schema_preserves_existing_data(self):
        """REQ-INV-006: unsupported schema preserves existing data."""
        path = Path(self.folder.name) / "foreign.sqlite3"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE original(value TEXT)")
            connection.execute("INSERT INTO original VALUES ('keep')")
            connection.execute("PRAGMA user_version=99")
        connection.close()
        before = path.read_bytes()
        with self.assertRaises(ValidationError):
            GradeStore(path)
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
