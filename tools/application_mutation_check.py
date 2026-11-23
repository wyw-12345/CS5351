"""Real application mutants in temporary copies; unimplemented obligations stay blocked."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = [
    ("INV-007-deployed-advisory-isolation", "scripts/advisory_worker.py",
     "command = sandbox_command(probe_directory)",
     'command = [sys.executable, str(Path(__file__).resolve()), "--child"]',
     "test.offline.test_deployed_isolation.DeployedIsolationTests.test_advisory_process_cannot_write_grade_data"),
    ("INV-001-recompute", "src/grade_store.py",
     'if grade["score"] != calculated or audit["final_score"] != calculated:', 'if False:',
     "test.offline.test_store.StoreTests.test_payload_and_grade_corruption_are_detected"),
    ("INV-002-uncertainty", "src/feedback_engine.py",
     'if any(item["uncertain"] or item["suggested_score"] is None for item in feedback["criteria"]):',
     'if False:', "test.offline.test_feedback.FeedbackTests.test_uncertain_null_is_an_escalation_not_a_zero_score"),
    ("INV-003-verified-audit-association", "src/grade_store.py",
     '                     "verified_key_id": key_id, "verified_teacher_id": teacher, **binding,',
     '                     "verified_key_id": key_id, "verified_teacher_id": None, **binding,',
     "test.offline.test_revision.SignedStoreTests.test_approved_score_and_private_audit"),
    ("INV-003-signature-verification", "src/grade_store.py",
     'public_key.verify(bytes.fromhex(approval["signature"]), bytes.fromhex(digest(binding)))',
     "pass",
     "test.offline.test_revision.SignedStoreTests.test_unknown_forged_and_missing_signature"),
    ("INV-003-trusted-key-lookup", "src/grade_store.py",
     "trusted = trusted_keys[key_id]", "trusted = trusted_keys.get(key_id) or next(iter(trusted_keys.values()))",
     "test.offline.test_revision.SignedStoreTests.test_unknown_forged_and_missing_signature"),
    ("INV-003-approval-binding", "src/grade_store.py",
     'if approval["binding"] != binding:', "if False:",
     "test.offline.test_revision.SignedStoreTests.test_rubric_version_and_reason_bound"),
    ("INV-004-range", "src/contracts.py", "if result > maximum:", "if False:",
     "test.offline.test_calculator.CalculatorTests.test_invalid_scores_rejected"),
    ("INV-005-half-up", "src/score_calculator.py",
     "rounded = whole + (2 * remainder >= cents.denominator)", "rounded = whole",
     "test.offline.test_calculator.CalculatorTests.test_exact_half_cent_after_recurring_division"),
    ("INV-006-atomicity", "src/grade_store.py",
     'return result\n        except Exception:\n            if self.connection.in_transaction:\n                self.connection.execute("ROLLBACK")',
     'return result\n        except Exception:\n            if self.connection.in_transaction:\n                self.connection.execute("COMMIT")',
     "test.offline.test_store.StoreTests.test_failed_audit_insert_rolls_back_status_and_grade"),
    ("INV-007-static-import-boundary", "src/feedback_engine.py",
     "from .contracts import", "if False:\n    import grade_store\n\nfrom .contracts import",
     "test.offline.test_boundaries.BoundaryTests.test_engine_has_no_environment_or_authority_import"),
    ("INV-008-retry", "src/grade_store.py",
     'raise ValidationError("submission content conflict")\n            else:',
     'raise ValidationError("submission content conflict")\n'
     '                raise ValidationError("identical retry rejected")\n            else:',
     "test.offline.test_revision.SignedStoreTests.test_idempotency_and_conflicts"),
]
EXPECTED_FAILURES = {
    "INV-007-deployed-advisory-isolation": "'written' != 'denied'",
    "INV-003-signature-verification": "not raised",
    "INV-003-trusted-key-lookup": "not raised",
    "INV-003-approval-binding": "not raised",
}


def main() -> int:
    results: list[dict[str, Any]] = []
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GRADEAIDE_", "LLM_", "DEEPSEEK_", "OPENAI_"))}
    env["GRADEAIDE_LIVE"] = "0"
    for name, filename, before, after, test in MUTANTS:
        with tempfile.TemporaryDirectory(prefix="gradeaide-app-mutant-") as directory:
            root = Path(directory)
            for folder in ("src", "scripts", "test", "tools", "docs", "prompts", "evidence", "config", "examples"):
                if (ROOT / folder).is_dir():
                    shutil.copytree(ROOT / folder, root / folder,
                                    ignore=shutil.ignore_patterns("__pycache__", "proposals"))
            command = [sys.executable, "-m", "unittest", test, "-v"]
            baseline = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True,
                                      check=False, timeout=60)
            if baseline.returncode:
                results.append({"mutant": name, "status": "BLOCKED", "reason": "baseline already fails"})
                continue
            path = root / filename
            source = path.read_text(encoding="utf-8")
            if source.count(before) != 1:
                results.append({"mutant": name, "status": "BLOCKED", "reason": "mutation target changed"})
                continue
            changed = source.replace(before, after, 1)
            compile(changed, filename, "exec")
            path.write_text(changed, encoding="utf-8")
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True,
                                    check=False, timeout=60)
            killed = result.returncode != 0
            if (expected := EXPECTED_FAILURES.get(name)) is not None:
                killed = killed and any(
                    line.startswith("AssertionError:") and expected in line
                    for line in result.stderr.splitlines()
                )
            results.append({"mutant": name, "status": "KILLED" if killed else "SURVIVED", "test": test,
                            "baseline_passed": True, "mutation_compiles": True})
    target = ROOT / "artifacts/application-mutations.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for row in results:
        print(row["status"], row["mutant"])
    # All planned invariants must eventually be verified: incomplete coverage is a release failure.
    return int(any(row["status"] != "KILLED" for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
