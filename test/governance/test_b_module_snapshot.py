"""Structural snapshot checks for the five current architecture modules."""

import unittest
from pathlib import Path

from tools.gates import normalized_sha256, read
from tools.integration_checks import public_api

ROOT = Path(__file__).resolve().parents[2]


class ModuleSnapshotTests(unittest.TestCase):
    def test_architectural_elements_keep_their_current_module_and_public_surface(self):
        """REQ-GOV-E03: each current architecture module keeps the expected boundary and snapshot."""
        public_elements = {
            "contracts": {"validate_rubric"},
            "feedback_engine": {"evaluate", "validate_feedback"},
            "score_calculator": {"calculate_score"},
            "grade_store": {"GradeStore"},
            "cli": {"settings_from_env"},
        }
        snapshot = read("docs/verification/api-surface.json", ROOT)
        self.assertEqual(set(snapshot["modules"]), public_elements.keys())
        for module, required in public_elements.items():
            with self.subTest(module=module):
                relative = f"src/{module}.py"
                source = ROOT / relative
                signatures = public_api(source.read_text(encoding="utf-8"))
                self.assertTrue(required <= signatures.keys())
                self.assertEqual(snapshot["modules"][module], signatures)
                self.assertEqual(snapshot["source_sha256"][relative], normalized_sha256(source))
        grade_store = snapshot["modules"]["grade_store"]["GradeStore"]["methods"]
        self.assertTrue({"create", "approve", "get"} <= grade_store.keys())
