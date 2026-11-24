"""ADR-0001..0003 / REQ-FUNC-010: explicit local teacher CLI and configuration boundary."""

import argparse
import getpass
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .contracts import ValidationError, canonical, digest, parse_json, read_text, text_value
from .contracts import Settings
from scripts.advisory_worker import invoke_worker
from .grade_store import GradeStore, approval_binding, sign_approval

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT = ROOT / "prompts" / "prompt_v1.2.yaml"


def settings_from_env() -> Settings:
    """REQ-COST-003: no invented model price or implicit paid endpoint."""
    def required(name: str) -> str:
        value = os.environ.get("GRADEAIDE_" + name, "")
        if not value.strip():
            raise ValidationError(f"configure GRADEAIDE_{name}")
        return value
    try:
        return Settings(
            endpoint=required("ENDPOINT"), model=required("MODEL"), api_key=required("API_KEY"),
            input_price=required("INPUT_PRICE_PER_MILLION"),
            output_price=required("OUTPUT_PRICE_PER_MILLION"), max_cost=required("MAX_COST"),
            timeout=float(os.environ.get("GRADEAIDE_TIMEOUT", "30")),
            max_output_tokens=int(os.environ.get("GRADEAIDE_MAX_OUTPUT_TOKENS", "1024")),
            max_input_bytes=int(os.environ.get("GRADEAIDE_MAX_INPUT_BYTES", "12000")),
            price_source=required("PRICE_SOURCE"),
            thinking=os.environ.get("GRADEAIDE_THINKING") or None,
            proxy_url=os.environ.get("GRADEAIDE_PROXY_URL") or None,
        )
    except (ValueError, OverflowError) as exc:
        raise ValidationError("invalid or missing GradeAide configuration") from exc


def _external_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_relative_to(ROOT):
        raise ValidationError("key material must stay outside repository")
    return path


def _password() -> bytes:
    value = os.environ.get("GRADEAIDE_SIGNING_PASSWORD") or getpass.getpass("Signing key password: ")
    if len(value) < 12:
        raise ValidationError("use a signing password of at least 12 characters")
    return value.encode("utf-8")


def trusted_keys_from_env() -> dict[str, Any]:
    """ADR-0002 / REQ-INV-003: trust is operator configuration, never part of an approval request."""
    value = os.environ.get("GRADEAIDE_TRUST_STORE")
    if not value:
        return {}
    trust = parse_json(read_text(_external_path(value)))
    if not isinstance(trust, dict):
        raise ValidationError("invalid trust store")
    return trust


def main(argv: list[str] | None = None) -> int:
    """REQ-FUNC-010: explicit propose, show, sign and approve; no implicit live retries."""
    parser = argparse.ArgumentParser(description="GradeAide: advisory feedback, signed teacher approval")
    sub = parser.add_subparsers(dest="command", required=True)
    keygen = sub.add_parser("keygen", help="operator provisions a new encrypted key outside the repo")
    keygen.add_argument("--private-key", required=True)
    keygen.add_argument("--trust-file", required=True)
    keygen.add_argument("--teacher-id", required=True)
    propose = sub.add_parser("propose")
    propose.add_argument("--essay", required=True)
    propose.add_argument("--rubric", required=True)
    propose.add_argument("--submission-id", required=True)
    propose.add_argument("--prompt", default=str(DEFAULT_PROMPT))
    propose.add_argument("--fixture", help="synthetic envelope; no real AI call")
    migrate = sub.add_parser("migrate", help="explicit additive v1 migration; back up database first")
    show = sub.add_parser("show")
    show.add_argument("--id", required=True)
    sign = sub.add_parser("sign", help="teacher confirms scores and signs; does not write a grade")
    approve = sub.add_parser("approve", help="verify a detached teacher approval and record grade")
    for command in (sign, approve):
        command.add_argument("--id", required=True)
        command.add_argument("--hash", required=True)
        command.add_argument("--scores", required=True)
        command.add_argument("--reviewer", required=True, help="audit label, not identity proof")
        command.add_argument("--reason", default="")
    sign.add_argument("--private-key", required=True)
    sign.add_argument("--confirm-sign", action="store_true", required=True,
                      help="explicit confirmation of this proposal and scores")
    approve.add_argument("--approval", required=True, help="detached signed approval JSON")
    for command in (propose, show, sign, approve, migrate):
        command.add_argument("--db", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "keygen":
            private_path, trust_path = _external_path(args.private_key), _external_path(args.trust_file)
            text_value(args.teacher_id, "teacher identity", 200)
            if private_path == trust_path or private_path.exists() or trust_path.exists():
                raise ValidationError("key provisioning never overwrites existing files")
            key = Ed25519PrivateKey.generate()
            public_hex = key.public_key().public_bytes_raw().hex()
            key_id = digest(public_hex)
            encrypted = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.BestAvailableEncryption(_password()))
            # Parent directory provisioning/ACLs are the operator's responsibility.
            fd = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(encrypted)
            with trust_path.open("x", encoding="utf-8") as trust_stream:
                trust_stream.write(canonical({key_id: {"teacher_id": args.teacher_id, "public_key": public_hex}}))
            result: dict[str, Any] = {"key_id": key_id, "teacher_id": args.teacher_id}
        elif args.command == "propose":
            essay = read_text(args.essay)
            rubric = parse_json(read_text(args.rubric))
            prompt = parse_json(read_text(args.prompt))
            if args.fixture:
                envelope = parse_json(read_text(args.fixture))
                settings = Settings("http://127.0.0.1/unused", "synthetic-fixture", "unused", "0", "0", "0",
                                    price_source="synthetic fixture: no provider charge")

                advice = invoke_worker(essay, rubric, prompt, settings, envelope)
            else:
                advice = invoke_worker(essay, rubric, prompt, settings_from_env())
            with GradeStore(args.db, trusted_keys=trusted_keys_from_env()) as store:
                result = store.create(essay, rubric, advice, submission_id=args.submission_id)
        else:
            if not Path(args.db).is_file():
                raise ValidationError("database does not exist")
            with GradeStore(args.db, trusted_keys=trusted_keys_from_env(),
                            migrate_legacy=args.command == "migrate") as store:
                if args.command == "migrate":
                    result = {"schema_version": 2, "legacy_approval_authentication": "unverified"}
                elif args.command == "show":
                    result = store.get(args.id)
                else:
                    scores = parse_json(read_text(args.scores))
                    if args.command == "sign":
                        record = store.get(args.id)
                        if record["hash"] != args.hash or record["approval_authentication"] == "legacy_unverified":
                            raise ValidationError("review current non-legacy proposal")
                        binding = approval_binding(record, scores, args.reviewer, args.reason)
                        if record["status"] == "escalated" and not args.reason.strip():
                            raise ValidationError("manual resolution requires reason")
                        loaded_key = serialization.load_pem_private_key(
                            read_text(_external_path(args.private_key), 10000).encode("utf-8"), _password())
                        if not isinstance(loaded_key, Ed25519PrivateKey):
                            raise ValidationError("Ed25519 key required")
                        key_id = digest(loaded_key.public_key().public_bytes_raw().hex())
                        result = sign_approval(loaded_key, key_id, binding)
                    else:
                        approval = parse_json(read_text(args.approval))
                        result = store.approve(args.id, args.hash, scores, args.reviewer, args.reason,
                                               approval=approval)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
        return 0
    except (ValueError, PermissionError, OSError, sqlite3.Error, UnicodeError, TypeError, KeyError, EOFError):
        print('{"error":"operation refused; check inputs, trust, signature and database integrity"}',
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
