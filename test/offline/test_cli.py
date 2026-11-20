"""T5/T6: REQ-FUNC-001, REQ-INV-003/004; real separate-process CLI lifecycle."""

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def invoke(*args):
    return subprocess.run([sys.executable, "-m", "src.cli", *map(str, args)], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", timeout=10)


class CliTests(unittest.TestCase):
    def test_separate_process_restart_approval_and_duplicate_rejection(self):
        """REQ-FUNC-010 / REQ-QUAL-004: separate process restart approval and duplicate rejection."""
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {
                "GRADEAIDE_TRUST_STORE": str(Path(folder) / "trust.json"),
                "GRADEAIDE_SIGNING_PASSWORD": "synthetic-test-only-password"}):  # pragma: allowlist secret - synthetic value or environment variable name
            private, trust, approval = [Path(folder) / x for x in ("key.pem", "trust.json", "approval.json")]
            provision = invoke("keygen", "--private-key", private, "--trust-file", trust,
                               "--teacher-id", "synthetic-teacher")
            self.assertEqual(provision.returncode, 0, provision.stderr)
            db = Path(folder) / "synthetic.sqlite3"
            created = invoke("propose", "--essay", "examples/essay.txt", "--rubric", "examples/rubric.json",
                             "--fixture", "examples/provider-fixture.json", "--submission-id", "cli-test", "--db", db)
            self.assertEqual(created.returncode, 0, created.stderr)
            proposal = json.loads(created.stdout)
            self.assertIsNone(proposal["final_score"])
            self.assertEqual(proposal["proposal"]["advice"]["metadata"]["mode"], "synthetic_fixture")
            reopened = invoke("show", "--id", proposal["id"], "--db", db)
            self.assertEqual(json.loads(reopened.stdout), proposal)
            signed = invoke("sign", "--id", proposal["id"], "--hash", proposal["hash"], "--scores",
                            "examples/accepted-scores.json", "--reviewer", "AUTOMATED SYNTHETIC TEST",
                            "--private-key", private, "--confirm-sign", "--db", db)
            self.assertEqual(signed.returncode, 0, signed.stderr)
            approval.write_text(signed.stdout, encoding="utf-8")
            approved = invoke("approve", "--id", proposal["id"], "--hash", proposal["hash"], "--scores",
                              "examples/accepted-scores.json", "--reviewer", "AUTOMATED SYNTHETIC TEST",
                              "--approval", approval, "--db", db)
            self.assertEqual(approved.returncode, 0, approved.stderr)
            final = json.loads(approved.stdout)
            self.assertEqual(final["final_score"], "72.00")
            last = invoke("show", "--id", proposal["id"], "--db", db)
            self.assertEqual(json.loads(last.stdout), final)
            repeated = invoke("approve", "--id", proposal["id"], "--hash", proposal["hash"], "--scores",
                              "examples/accepted-scores.json", "--reviewer", "AUTOMATED SYNTHETIC TEST",
                              "--approval", approval, "--db", db)
            self.assertEqual(json.loads(repeated.stdout), final)
            duplicate = invoke("approve", "--id", proposal["id"], "--hash", proposal["hash"], "--scores",
                               "examples/accepted-scores.json", "--reviewer", "changed-label", "--approval", approval, "--db", db)
            self.assertEqual(duplicate.returncode, 2)

    def test_missing_database_show_does_not_create_file(self):
        """REQ-FUNC-007: missing database show does not create file."""
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "missing.db"
            result = invoke("show", "--id", "missing", "--db", db)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(db.exists())

    def test_invalid_fixture_envelope_escalates_without_traceback(self):
        """REQ-FUNC-010: invalid fixture envelope escalates without traceback."""
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / "invalid.json"
            fixture.write_text("[]", encoding="utf-8")
            result = invoke("propose", "--essay", "examples/essay.txt", "--rubric", "examples/rubric.json",
                            "--fixture", fixture, "--submission-id", "bad-fixture", "--db", Path(folder) / "demo.db")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "escalated")
            self.assertNotIn("Traceback", result.stderr)

    def test_authority_modules_keep_io_boundaries(self):
        """REQ-QUAL-001 / REQ-SEC-006: authority modules keep io boundaries."""
        feedback_tree = ast.parse((ROOT / "src/feedback_engine.py").read_text(encoding="utf-8"))
        imports = [node.module or "" for node in ast.walk(feedback_tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(feedback_tree) if isinstance(node, ast.Import)
                    for alias in node.names]
        self.assertFalse(any("grade_store" in name or "sqlite" in name for name in imports))
        calculator = ast.parse((ROOT / "src/score_calculator.py").read_text(encoding="utf-8"))
        for node in ast.walk(calculator):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"open", "eval", "exec", "input"})


if __name__ == "__main__":
    unittest.main()
