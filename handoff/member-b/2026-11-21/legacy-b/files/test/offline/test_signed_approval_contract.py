"""ADR-0002/0003 proposed additive seam for A review; no fake verifier.

Target: GradeStore(path, trusted_keys={id: public_bytes});
create(..., submission_id=...); approve(..., approval={key_id,binding,signature}).
Ephemeral Ed25519 test keys are never persisted. Missing seam causes explicit failure.
"""
import copy
import inspect
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.contracts import canonical, digest
from src.feedback_engine import evaluate
from src.grade_store import GradeStore
from src.score_calculator import calculate_score
from test.support import ESSAY, PROMPT, RUBRIC, SCORES, SETTINGS, transport


class SignedApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.key = Ed25519PrivateKey.generate()
        self.other = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes_raw()

    def store(self):
        self.assertIn("trusted_keys", inspect.signature(GradeStore).parameters,
                      "ADR-0002 trusted-key injection absent; proposed seam awaits A review")
        store = GradeStore(Path(self.temp.name) / "grades.sqlite", trusted_keys={"teacher": self.public})
        self.addCleanup(store.close)
        return store

    def proposal(self, store, submission_id="submission-1", advice=None):
        self.assertIn("submission_id", inspect.signature(store.create).parameters,
                      "ADR-0003 stable submission identity absent")
        if advice is None:
            advice = evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, transport(), mode="test_fixture")
        return store.create(ESSAY, RUBRIC, advice, submission_id=submission_id)

    def approval(self, row, scores=None, key=None):
        scores = SCORES if scores is None else scores
        binding = {"submission_id": row["submission_id"], "proposal_hash": row["hash"],
                   "rubric_id": RUBRIC["id"], "rubric_version": RUBRIC["version"],
                   "confirmed_scores_sha256": digest(scores)}
        return {"key_id": "teacher", "binding": binding,
                "signature": (self.key if key is None else key).sign(canonical(binding).encode()).hex()}

    def approve(self, store, row, scores, approval, reason=""):
        self.assertIn("approval", inspect.signature(store.approve).parameters,
                      "ADR-0002 signed approval parameter absent")
        return store.approve(row["id"], row["hash"], scores, "client-audit-label",
                             reason=reason, approval=approval)

    def unchanged(self, store, row):
        self.assertIsNone(store.get(row["id"])["final_score"])
        self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM grades").fetchone()[0], 0)

    def test_unauthorized_signer_is_rejected(self):
        """REQ-INV-003, REQ-FUNC-005: unknown/corrupted/missing signatures create no grade."""
        store = self.store()
        row = self.proposal(store)
        corrupt = self.approval(row)
        corrupt["signature"] = "00" * 64
        for token in (self.approval(row, key=self.other), corrupt, None, True, {"key_id": "unknown"}):
            with self.subTest(kind=type(token).__name__), self.assertRaises(PermissionError):
                self.approve(store, row, SCORES, token)
            self.unchanged(store, row)

    def test_score_substitution_between_confirmation_and_recording_is_rejected(self):
        """REQ-INV-003, REQ-FUNC-006: valid alternate S-prime is not the confirmed S."""
        store = self.store()
        row = self.proposal(store)
        with self.assertRaises((PermissionError, ValueError)):
            self.approve(store, row, {"content": "9", "structure": "6"}, self.approval(row))
        self.unchanged(store, row)

    def test_signature_replay_onto_other_submission_is_rejected(self):
        """REQ-INV-003, REQ-INV-008: signature cannot cross submission/proposal identity."""
        store = self.store()
        first, second = self.proposal(store), self.proposal(store, "submission-2")
        with self.assertRaises((PermissionError, ValueError)):
            self.approve(store, second, SCORES, self.approval(first))
        self.unchanged(store, second)

    def test_rubric_version_mismatch_is_rejected(self):
        """REQ-INV-003: a correctly signed different rubric version is still refused."""
        store = self.store()
        row = self.proposal(store)
        token = self.approval(row)
        token["binding"]["rubric_version"] = "another-version"
        token["signature"] = self.key.sign(canonical(token["binding"]).encode()).hex()
        with self.assertRaises((PermissionError, ValueError)):
            self.approve(store, row, SCORES, token)
        self.unchanged(store, row)

    def test_valid_signature_records_recomputed_grade(self):
        """REQ-INV-001, REQ-INV-003, REQ-FUNC-006: positive signed control computes 72.00."""
        store = self.store()
        row = self.proposal(store)
        approved = self.approve(store, row, SCORES, self.approval(row))
        self.assertEqual(approved["final_score"], "72.00")
        self.assertEqual(approved["final_score"], calculate_score(RUBRIC, SCORES))
        self.assertEqual(approved["audit"]["confirmed_scores_sha256"], digest(SCORES))
        self.assertEqual(approved["audit"]["verified_key_id"], "teacher")
        self.assertEqual(approved["audit"]["approval_binding"], self.approval(row)["binding"])
        self.assertTrue(approved["audit"]["approval_signature"])
        # A human may resolve an escalated proposal through the SAME signed boundary.
        advice = evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, transport(), mode="test_fixture")
        advice.update(status="escalated", reason="requires-human-resolution")
        manual = self.proposal(store, "manual-submission", advice=advice)
        resolved = self.approve(store, manual, SCORES, self.approval(manual), reason="manual full-score resolution")
        self.assertEqual(resolved["final_score"], "72.00")
        self.assertEqual(resolved["audit"]["reason"], "manual full-score resolution")

    def test_altered_scores_after_approval_are_rejected(self):
        """REQ-INV-003, REQ-INV-006: public digest recomputation cannot forge confirmation."""
        store = self.store()
        row = self.proposal(store)
        approved = self.approve(store, row, SCORES, self.approval(row))
        audit = copy.deepcopy(approved["audit"])
        altered = {"content": "9", "structure": "6"}
        audit["accepted_scores"] = altered
        audit["confirmed_scores_sha256"] = digest(altered)
        audit["final_score"] = calculate_score(RUBRIC, altered)
        store.connection.execute("UPDATE grades SET score=?,audit=?,digest=? WHERE proposal_id=?",
                                 (audit["final_score"], canonical(audit), digest(audit), row["id"]))
        with self.assertRaises((PermissionError, ValueError)):
            store.get(row["id"])

    def test_submission_retry_and_conflict(self):
        """REQ-FUNC-009, REQ-INV-008: identical input reuses identity; conflict preserves it."""
        store = self.store()
        first = self.proposal(store)
        self.assertEqual(self.proposal(store)["id"], first["id"])
        with self.assertRaises(ValueError):
            advice = evaluate(ESSAY, RUBRIC, PROMPT, SETTINGS, transport(), mode="test_fixture")
            store.create(ESSAY + " changed", RUBRIC, advice, submission_id="submission-1")

    def test_schema_v2_is_explicit(self):
        """REQ-INV-008, REQ-QUAL-004: submission identity has an explicit persistent schema."""
        store = self.store()
        self.assertGreaterEqual(store.connection.execute("PRAGMA user_version").fetchone()[0], 2)
