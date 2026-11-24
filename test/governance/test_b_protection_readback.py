"""Fixture-based verification of the branch protection readback contract."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools.github_setup import CONTEXTS, main, verify_protection


def readback(test_baseline=False):
    response = {key: {"enabled": value} for key, value in {
        "enforce_admins": True, "allow_force_pushes": False, "allow_deletions": False,
        "required_conversation_resolution": True,
    }.items()}
    response["required_pull_request_reviews"] = {
        "dismiss_stale_reviews": True, "require_code_owner_reviews": True,
        "required_approving_review_count": 1, "require_last_push_approval": True,
    }
    if not test_baseline:
        response["required_status_checks"] = {"strict": True, "contexts": list(CONTEXTS)}
    return response


class ProtectionReadbackTests(unittest.TestCase):
    def test_review_and_check_settings_must_match_readback(self):
        """REQ-GOV-B02: real response checks reject relaxed requirements."""
        verify_protection(readback())
        response = readback()
        response["required_status_checks"]["strict"] = False
        response["required_pull_request_reviews"]["require_code_owner_reviews"] = False
        response["required_pull_request_reviews"]["bypass_pull_request_allowances"] = {"teams": [{"id": 42}]}
        with self.assertRaisesRegex(ValueError, "require_code_owner_reviews.*bypass.*required_status_checks"):
            verify_protection(response)

    def test_tests_baseline_accepts_missing_status_checks(self):
        """REQ-GOV-B01: the independently reviewed tests-only branch can carry red tests."""
        verify_protection(readback(True), test_baseline=True)
        with self.assertRaisesRegex(ValueError, "tests-only baseline"):
            verify_protection(readback(), test_baseline=True)

    def test_check_command_only_reads_server(self):
        """REQ-GOV-B02: evidence collection uses GET for both branches."""
        with (patch("sys.argv", ["github_setup.py", "fixture/gradeaide", "--check"]),
              patch("tools.github_setup.request", side_effect=[readback(), readback(True)]) as request,
              redirect_stdout(io.StringIO()) as output):
            self.assertEqual(main(), 0)
        self.assertEqual([call.args[0] for call in request.call_args_list], ["GET", "GET"])
        self.assertIn("PASS protection", output.getvalue())
