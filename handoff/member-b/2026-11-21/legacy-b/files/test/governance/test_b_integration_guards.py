"""Review-ready tests for the proposed B integration guard module.

The tests describe the expected behavior of a candidate, unmerged gate proposal.
They are intentionally red until the proposal and the related gate changes are
reviewed and supplied; no application or protected policy is changed here.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.gates import GateError, check_ai_log, is_implementation

ROOT = Path(__file__).resolve().parents[2]
REQUIREMENT_PATH = "docs/req/requirements.yaml"
COEVOLUTION_PATHS = (
    "docs/req/requirement-id-map.yaml",
    "docs/architecture/trace-matrix.md",
    "docs/verification/test-map.yaml",
    "docs/ai-use-log.yaml",
)
TEST_PATH = "test/offline/test_b_evidence.py"


class BIntegrationGuardTests(unittest.TestCase):
    def integration_checks(self):
        try:
            from tools import integration_checks
        except ImportError as exc:
            self.fail(f"tools.integration_checks proposal is not supplied yet: {exc}")
        return integration_checks

    def test_script_and_dependency_manifests_are_implementation(self):
        """REQ-GOV-B02, REQ-GOV-B06: scripts and dependency manifests need gates and logs."""
        for path in ("scripts/evaluate_live.py", "requirements-dev.txt",
                     "requirements-b-supplement.txt", "docs/member-b/helper.py"):
            with self.subTest(path=path):
                self.assertTrue(is_implementation(path), f"{path} must be implementation scope")

    def test_script_change_requires_ai_log_entry(self):
        """REQ-GOV-B06: changing a script without a substantive log entry is blocked."""
        with self.assertRaises(GateError):
            check_ai_log([], [], ["scripts/evaluate_live.py"])

    def test_requirement_change_requires_coevolution(self):
        """REQ-GOV-C01, REQ-GOV-C02, REQ-GOV-B03: requirement edits co-evolve."""
        checks = self.integration_checks()
        for missing in COEVOLUTION_PATHS:
            paths = [REQUIREMENT_PATH, TEST_PATH,
                     *(p for p in COEVOLUTION_PATHS if p != missing)]
            with self.subTest(missing=missing), self.assertRaises(GateError):
                checks.check_requirement_coevolution(paths)
        with self.assertRaises(GateError):
            checks.check_requirement_coevolution([REQUIREMENT_PATH, *COEVOLUTION_PATHS])
        checks.check_requirement_coevolution([REQUIREMENT_PATH, *COEVOLUTION_PATHS, TEST_PATH])
        checks.check_requirement_coevolution(["docs/README.md"])

    def test_public_api_reports_signatures_and_methods(self):
        """REQ-GOV-B02, REQ-GOV-C02: public API snapshots name exact callables."""
        checks = self.integration_checks()
        source = (
            "def helper(value, *, flag=False):\n"
            "    return value\n"
            "\n"
            "class Widget:\n"
            "    def build(self, first, second=2, *, keyword=None):\n"
            "        return first\n"
        )
        surface = checks.public_api(source)
        self.assertIn("helper", surface)
        self.assertIn("signature", surface["helper"])
        self.assertIn("methods", surface["helper"])
        self.assertIn("Widget", surface)
        self.assertIn("signature", surface["Widget"])
        self.assertIn("methods", surface["Widget"])
        self.assertIn("build", surface["Widget"]["methods"])
        self.assertIn("signature", surface["Widget"]["methods"]["build"])

    def test_public_api_changes_with_keyword_only_defaults(self):
        """REQ-GOV-B02, REQ-GOV-C02: approve signature changes alter the snapshot."""
        checks = self.integration_checks()
        source = (ROOT / "src/grade_store.py").read_text(encoding="utf-8")
        before = checks.public_api(source)
        self.assertIn("GradeStore", before)
        self.assertIn("approve", before["GradeStore"]["methods"])
        old = 'reason: str = "") -> dict[str, Any]:'
        new = 'reason: str = "", *, signed: bool = False) -> dict[str, Any]:'
        self.assertIn(old, source, "GradeStore.approve signature changed; review this test")
        after = checks.public_api(source.replace(old, new, 1))
        self.assertNotEqual(before["GradeStore"]["methods"]["approve"]["signature"],
                            after["GradeStore"]["methods"]["approve"]["signature"])

    def test_secret_scan_does_not_echo_secret(self):
        """REQ-SEC-004: synthetic tokens are blocked without leaking the value."""
        checks = self.integration_checks()
        token = "sk-" + "x" * 40
        with self.assertRaises(GateError) as caught:
            checks.check_secret_text(f"authorization: Bearer {token}", label="fixture")
        self.assertNotIn(token, str(caught.exception))
        checks.check_secret_text(
            "GRADEAIDE_API_KEY is read from the runtime environment; no value is committed.",
            label="fixture",
        )

    def test_registered_test_ids_reject_unknown_ids(self):
        """REQ-GOV-C02, REQ-GOV-B03: one known ID cannot mask an unregistered ID."""
        checks = self.integration_checks()
        allowed = {"REQ-GOV-C01", "REQ-SEC-004"}
        checks.check_registered_test_ids("REQ-GOV-C01: known requirement", allowed)
        with self.assertRaises(GateError):
            checks.check_registered_test_ids("REQ-GOV-C01 also mentions REQ-GOV-C99", allowed)

    def test_registered_test_ids_reject_prefix_confusion(self):
        """REQ-GOV-C02: prefixes or extensions of registered IDs are not registered."""
        checks = self.integration_checks()
        allowed = {"REQ-GOV-C01", "REQ-SEC-004"}
        for text in ("REQ-GOV-C0", "REQ-GOV-C011", "REQ-SEC-0041", "REQ-GOV-C01x"):
            with self.subTest(text=text), self.assertRaises(GateError):
                checks.check_registered_test_ids(text, allowed)


if __name__ == "__main__":
    unittest.main()
