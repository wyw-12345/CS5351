"""Release obligations stay red until E supplies real enforcement/review evidence."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from src.score_calculator import calculate_score
from test.support import RUBRIC, SCORES

ROOT = Path(__file__).resolve().parents[2]


class RuntimeGovernanceTests(unittest.TestCase):
    def test_offline_calculator_needs_no_credentials(self):
        """REQ-QUAL-003: deterministic calculation needs no external network or API key."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(calculate_score(RUBRIC, SCORES), "72.00")

    def snapshot(self):
        path = ROOT / "docs/verification/permissions-snapshot.json"
        self.assertTrue(path.is_file(), "E/B must supply an actual permission snapshot")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_runtime_permission_enforcement_is_verified(self):
        """REQ-GOV-E01, REQ-INV-007: a default-deny document alone is not an enforced sandbox."""
        self.assertIs(self.snapshot().get("runtime_enforcement_verified"), True,
                      "E must supply actual process/filesystem isolation evidence")

    def test_tool_manifest_enforcement_is_verified(self):
        """REQ-GOV-E04: role-inappropriate tools must be denied by actual enforcement."""
        self.assertIs(self.snapshot().get("tool_manifest_enforcement_verified"), True,
                      "No active tool/MCP enforcement evidence has been supplied")

    def test_frozen_path_review_policy_is_active(self):
        """REQ-GOV-E02: frozen-path changes need a real active independent review policy."""
        policy = json.loads((ROOT / "docs/verification/policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["status"], "active", "Human baseline is still pending")
        self.assertTrue(policy["reviewers"], "Do not invent reviewer usernames")

    def test_architecture_api_snapshot_is_reviewed(self):
        """REQ-GOV-E03: module and callable snapshot is actual, unique and human-reviewed."""
        path = ROOT / "docs/verification/api-surface.json"
        self.assertTrue(path.is_file(), "B must produce the actual API/method snapshot")
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        components = snapshot["authority_components"]
        self.assertEqual(set(components), {"feedback_engine", "score_calculator", "grade_store"})
        self.assertEqual(len(set(components.values())), 3)
        self.assertEqual(snapshot["status"], "reviewed", "Snapshot is a proposal until real review")
