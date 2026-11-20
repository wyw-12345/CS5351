"""Evidence-only checks for B's supplement. No live provider call is made."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "evidence/benchmark.json"
LIVE_RESULTS = ROOT / "evidence/live-results.json"
FEEDBACK = ROOT / "src/feedback_engine.py"
CALCULATOR = ROOT / "src/score_calculator.py"
CALCULATOR_ALLOWED = {
    "decimal", "fractions", "typing", "dataclasses", "__future__", "collections", "contracts",
}


def imported_roots(source: str) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
            else:
                found.update(alias.name.split(".")[0] for alias in node.names)
    return found


class BEvidenceTests(unittest.TestCase):
    def test_historical_calculator_benchmark(self):
        """REQ-PERF-001, REQ-QUAL-003: historical local benchmark meets the target."""
        data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
        self.assertGreaterEqual(data["measured_calls"], 1000)
        self.assertEqual(data["criteria"], 10)
        self.assertLessEqual(data["p95_ms"], 10)
        self.assertEqual(data["target_p95_ms"], 10)
        self.assertTrue(data["target_met"])
        self.assertIn("no inference/network", data["scope"])

    def test_historical_live_evidence_remains_pending(self):
        """REQ-PERF-003, REQ-QUAL-003: historical live run is inspected, never rerun here."""
        data = json.loads(LIVE_RESULTS.read_text(encoding="utf-8"))
        self.assertGreaterEqual(data["calls_attempted"], 20)
        self.assertGreaterEqual(len(data["results"]), 20)
        self.assertLessEqual(data["p95_ms"], 30000)
        self.assertIn("PENDING", data["semantic_review"])
        self.assertIn("human", data["semantic_review"].lower())

    def test_feedback_has_no_grade_store_import(self):
        """REQ-QUAL-001, REQ-SEC-006: advisory code cannot import the grade store."""
        imports = imported_roots(FEEDBACK.read_text(encoding="utf-8"))
        self.assertNotIn("grade_store", imports)

    def test_calculator_imports_within_allowed_set(self):
        """REQ-SEC-006, REQ-QUAL-003: calculator least privilege keeps D's allowlist."""
        imports = imported_roots(CALCULATOR.read_text(encoding="utf-8"))
        self.assertLessEqual(imports, CALCULATOR_ALLOWED)
        self.assertIn("fractions", imports)
        self.assertIn("contracts", imports)
        self.assertNotIn("os", imports)
        self.assertNotIn("subprocess", imports)
        self.assertNotIn("pathlib", imports)
        self.assertNotIn("urllib", imports)


if __name__ == "__main__":
    unittest.main()
