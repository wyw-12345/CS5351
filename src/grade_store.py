"""ADR-0002/0003: REQ-INV-001/003/006/008, signed approval and atomic schema-v2 storage."""

import copy
import hmac
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .contracts import (
    ValidationError,
    canonical,
    digest,
    exact_keys,
    parse_json,
    text_value,
    validate_essay,
    validate_rubric,
    validate_scores,
)
from .feedback_engine import escalation_reason, validate_feedback
from .score_calculator import calculate_score


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def approval_binding(record: dict[str, Any], scores: dict[str, str],
                     reviewer: str, reason: str = "") -> dict[str, str]:
    """ADR-0002 / REQ-INV-003: bind the exact proposal, rubric and confirmed scores."""
    rubric = record["proposal"]["rubric"]
    validate_scores(rubric, scores)
    text_value(reviewer, "reviewer", 200)
    if not isinstance(reason, str) or len(reason) > 2000:
        raise ValidationError("invalid review reason")
    return {"domain": "GradeAide-approval-v2", "submission_id": record["submission_id"],
            "proposal_hash": record["hash"], "rubric_id": rubric["id"],
            "rubric_version": rubric["version"], "confirmed_scores_sha256": digest(scores),
            "reviewer_label": reviewer, "reason": reason}


def sign_approval(private_key: Ed25519PrivateKey, key_id: str,
                  binding: dict[str, str]) -> dict[str, Any]:
    """ADR-0002 / REQ-INV-003: pure signing helper called by the explicit teacher CLI."""
    text_value(key_id, "key id", 200)
    signature = private_key.sign(bytes.fromhex(digest(binding)))
    return {"key_id": key_id, "binding": copy.deepcopy(binding), "signature": signature.hex()}


def _verify(approval: Any, binding: dict[str, str],
            trusted_keys: dict[str, Any]) -> tuple[str, str]:
    try:
        approval = exact_keys(approval, {"key_id", "binding", "signature"}, "signed approval")
        key_id = text_value(approval["key_id"], "key id", 200)
        trusted = trusted_keys[key_id]
        teacher = text_value(trusted["teacher_id"], "trusted teacher id", 200)
        if approval["binding"] != binding:
            raise PermissionError("approval binding mismatch")
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(trusted["public_key"]))
        public_key.verify(bytes.fromhex(approval["signature"]), bytes.fromhex(digest(binding)))
        return key_id, teacher
    except (KeyError, TypeError, ValueError, InvalidSignature) as exc:
        raise PermissionError("approval signature not trusted or invalid") from exc


def _validate_advice(advice: Any, essay: str, rubric: dict[str, Any],
                     *, legacy: bool = False) -> dict[str, Any]:
    advice = copy.deepcopy(exact_keys(advice, {"status", "reason", "feedback", "metadata"}, "advice"))
    if advice["status"] not in ("pending_review", "escalated") or not isinstance(advice["metadata"], dict):
        raise ValidationError("invalid initial advice")
    feedback = advice["feedback"]
    if feedback is not None:
        # Historical v1 rows have no confidence. Check their old shape without claiming confidence.
        if legacy:
            check = copy.deepcopy(feedback)
            for item in check["criteria"]:
                item["confidence"] = 1
            validate_feedback(check, essay, rubric)
        else:
            advice["feedback"] = validate_feedback(feedback, essay, rubric)
    if advice["status"] == "pending_review":
        if advice["reason"] is not None or feedback is None:
            raise ValidationError("invalid pending advice")
        if legacy:
            unsafe = any(x["uncertain"] or x["suggested_score"] is None for x in feedback["criteria"])
        else:
            unsafe = escalation_reason(advice["feedback"]) is not None
        if unsafe:
            raise ValidationError("unsafe advice must escalate")
    else:
        text_value(advice["reason"], "escalation reason")
    return advice


class GradeStore:
    """ADR-0003 / REQ-INV-006: sole durable writer; schema 1 migrates additively to 2."""

    def __init__(self, path: str | Path, *, trusted_keys: dict[str, Any] | None = None,
                 migrate_legacy: bool = False):
        self._trusted_keys = copy.deepcopy(trusted_keys or {})
        self.connection = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.connection.execute("BEGIN IMMEDIATE")
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            tables = {row[0] for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            expected = {"proposals": {"id", "payload", "digest", "status"},
                        "grades": {"proposal_id", "score", "audit", "digest"}}
            if version == 0 and not tables:
                self.connection.execute("""CREATE TABLE proposals (
                    id TEXT PRIMARY KEY, payload TEXT NOT NULL, digest TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending_review','escalated','approved')),
                    submission_id TEXT NOT NULL UNIQUE, format_version INTEGER NOT NULL
                )""")
                self.connection.execute("""CREATE TABLE grades (
                    proposal_id TEXT PRIMARY KEY REFERENCES proposals(id),
                    score TEXT NOT NULL, audit TEXT NOT NULL, digest TEXT NOT NULL
                )""")
            elif version in (1, 2):
                if version == 2:
                    expected["proposals"] |= {"submission_id", "format_version"}
                if tables != set(expected):
                    raise ValidationError("database tables do not match supported schema")
                for name, columns in expected.items():
                    actual = {row[1] for row in self.connection.execute(f"PRAGMA table_info({name})")}
                    if actual != columns:
                        raise ValidationError("database columns do not match supported schema")
                if version == 1 and not migrate_legacy:
                    raise ValidationError("schema 1 requires explicit migration after backup")
                if version == 1:
                    self.connection.execute("ALTER TABLE proposals ADD COLUMN submission_id TEXT")
                    self.connection.execute("ALTER TABLE proposals ADD COLUMN format_version INTEGER NOT NULL DEFAULT 1")
                    self.connection.execute("UPDATE proposals SET submission_id='legacy:' || id")
                    self.connection.execute("CREATE UNIQUE INDEX submission_identity ON proposals(submission_id)")
                if version == 1:
                    for row in self.connection.execute("SELECT id FROM proposals").fetchall():
                        self.get(row["id"])
            else:
                raise ValidationError("unsupported database schema; preserve file and review migration")
            self.connection.execute("PRAGMA user_version=2")
            self.connection.execute("COMMIT")
        except Exception:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            self.connection.close()
            raise

    def close(self) -> None:
        """REQ-INV-006: release the SQLite connection."""
        """REQ-INV-006: release the local database handle."""
        self.connection.close()

    def __enter__(self) -> "GradeStore":
        """REQ-INV-006: scope the persistent connection."""
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def create(self, essay: str, rubric: dict[str, Any], advice: dict[str, Any],
               *, submission_id: str | None = None) -> dict[str, Any]:
        """ADR-0003 / REQ-FUNC-005/009: an identical submission is an idempotent proposal."""
        validate_essay(essay)
        validate_rubric(rubric)
        advice = _validate_advice(advice, essay, rubric)
        submission_id = text_value(uuid.uuid4().hex if submission_id is None else submission_id, "submission id", 200)
        if submission_id.startswith("legacy:"):
            raise ValidationError("reserved legacy submission prefix")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            row = self.connection.execute("SELECT id FROM proposals WHERE submission_id=?",
                                          (submission_id,)).fetchone()
            if row:
                record = self.get(row["id"])
                old = record["proposal"]
                if (old["essay"], old["rubric"], old["advice"]) != (essay, rubric, advice):
                    raise ValidationError("submission content conflict")
            else:
                proposal_id = uuid.uuid4().hex
                payload = {"essay": essay, "rubric": rubric, "advice": advice,
                           "essay_hash": digest(essay), "rubric_hash": digest(rubric),
                           "advice_hash": digest(advice), "submission_id": submission_id,
                           "created_at": _utc()}
                self.connection.execute("INSERT INTO proposals VALUES (?,?,?,?,?,?)",
                                        (proposal_id, canonical(payload), digest(payload),
                                         advice["status"], submission_id, 2))
                record = self.get(proposal_id)
            self.connection.execute("COMMIT")
            return record
        except Exception:
            self.connection.execute("ROLLBACK")
            raise

    def get(self, proposal_id: str) -> dict[str, Any]:
        """ADR-0002/0003 / REQ-INV-001/003/006: verify digests, signed scores and authoritative total."""
        row = self.connection.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if row is None:
            raise ValidationError("proposal not found")
        if row["format_version"] not in (1, 2):
            raise ValidationError("invalid row format")
        legacy = row["format_version"] == 1
        payload = parse_json(row["payload"])
        if not isinstance(payload, dict) or not hmac.compare_digest(digest(payload), row["digest"]):
            raise ValidationError("proposal integrity check failed")
        fields = {"essay", "rubric", "advice", "essay_hash", "rubric_hash", "created_at"}
        if not legacy:
            fields |= {"advice_hash", "submission_id"}
        exact_keys(payload, fields, "payload")
        validate_essay(payload["essay"])
        validate_rubric(payload["rubric"])
        _validate_advice(payload["advice"], payload["essay"], payload["rubric"], legacy=legacy)
        if digest(payload["essay"]) != payload["essay_hash"] or digest(payload["rubric"]) != payload["rubric_hash"]:
            raise ValidationError("stored source integrity check failed")
        if not legacy and (payload["submission_id"] != row["submission_id"]
                           or payload["advice_hash"] != digest(payload["advice"])):
            raise ValidationError("submission/advice integrity check failed")
        if legacy and row["submission_id"] != "legacy:" + proposal_id:
            raise ValidationError("legacy submission identity mismatch")
        if row["status"] != "approved" and row["status"] != payload["advice"]["status"]:
            raise ValidationError("proposal state mismatch")
        record: dict[str, Any] = {"id": proposal_id, "hash": row["digest"], "status": row["status"],
                                  "submission_id": row["submission_id"], "proposal": payload,
                                  "final_score": None, "audit": None,
                                  "approval_authentication": "legacy_unverified" if legacy else "not_approved"}
        grade = self.connection.execute("SELECT * FROM grades WHERE proposal_id=?", (proposal_id,)).fetchone()
        if row["status"] == "approved":
            if grade is None:
                raise ValidationError("approved record missing grade")
            audit = parse_json(grade["audit"])
            if not isinstance(audit, dict) or digest(audit) != grade["digest"]:
                raise ValidationError("audit integrity check failed")
            audit_fields = {"proposal_id", "proposal_hash", "reviewer", "reason", "accepted_scores",
                            "final_score", "approved_at", "calculator_version", "previous_status"}
            if not legacy:
                audit_fields |= {"approval", "verified_key_id", "verified_teacher_id", "domain",
                                 "submission_id", "rubric_id", "rubric_version", "confirmed_scores_sha256",
                                 "reviewer_label", "essay_sha256", "rubric_sha256", "advice_sha256"}
            exact_keys(audit, audit_fields, "audit")
            if audit["proposal_hash"] != row["digest"] or audit["proposal_id"] != proposal_id:
                raise ValidationError("audit is not bound to proposal")
            if audit["previous_status"] != payload["advice"]["status"]:
                raise ValidationError("audit previous state is inconsistent")
            text_value(audit["reviewer"], "reviewer", 200)
            if audit["previous_status"] == "escalated":
                text_value(audit["reason"], "resolution reason")
            calculated = calculate_score(payload["rubric"], audit["accepted_scores"])
            if grade["score"] != calculated or audit["final_score"] != calculated:
                raise ValidationError("stored score does not match calculator")
            if not legacy:
                binding = approval_binding(record, audit["accepted_scores"], audit["reviewer"], audit["reason"])
                key_id, teacher = _verify(audit["approval"], binding, self._trusted_keys)
                expected = {"verified_key_id": key_id, "verified_teacher_id": teacher, **binding,
                            "essay_sha256": payload["essay_hash"], "rubric_sha256": payload["rubric_hash"],
                            "advice_sha256": payload["advice_hash"]}
                if any(audit.get(key) != value for key, value in expected.items()):
                    raise ValidationError("signed audit fields mismatch")
                record["approval_authentication"] = "verified"
            record["final_score"], record["audit"] = calculated, audit
        elif grade is not None:
            raise ValidationError("unapproved record has a grade")
        return record

    def approve(self, proposal_id: str, proposal_hash: str, scores: dict[str, str],
                reviewer: str, reason: str = "", *, approval: Any = None) -> dict[str, Any]:
        """ADR-0002 / REQ-INV-001/003/006/008: verify exact signed approval then recompute and persist."""
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            record = self.get(proposal_id)
            if record["approval_authentication"] == "legacy_unverified":
                raise PermissionError("legacy record is archival; create and sign a new submission")
            if not isinstance(proposal_hash, str) or not hmac.compare_digest(proposal_hash, record["hash"]):
                raise ValidationError("proposal hash mismatch")
            binding = approval_binding(record, scores, reviewer, reason)
            key_id, teacher = _verify(approval, binding, self._trusted_keys)
            if record["status"] == "approved":
                audit = record["audit"]
                if audit["approval"] != approval or audit["accepted_scores"] != scores:
                    raise ValidationError("conflicting repeated approval")
                self.connection.execute("COMMIT")
                return record
            if record["status"] == "escalated" and not reason.strip():
                raise ValidationError("escalated proposal requires resolution reason")
            score = calculate_score(record["proposal"]["rubric"], scores)
            payload = record["proposal"]
            audit = {"proposal_id": proposal_id, "proposal_hash": proposal_hash,
                     "reviewer": reviewer, "reason": reason, "accepted_scores": scores,
                     "final_score": score, "approved_at": _utc(), "calculator_version": "1.0",
                     "previous_status": record["status"], "approval": approval,
                     "verified_key_id": key_id, "verified_teacher_id": teacher, **binding,
                     "essay_sha256": payload["essay_hash"], "rubric_sha256": payload["rubric_hash"],
                     "advice_sha256": payload["advice_hash"]}
            self.connection.execute("UPDATE proposals SET status='approved' WHERE id=?", (proposal_id,))
            self.connection.execute("INSERT INTO grades VALUES (?,?,?,?)",
                                    (proposal_id, score, canonical(audit), digest(audit)))
            result = self.get(proposal_id)
            self.connection.execute("COMMIT")
            return result
        except Exception:
            if self.connection.in_transaction:
                self.connection.execute("ROLLBACK")
            raise
