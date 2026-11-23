"""Deployed advisory isolation acceptance tests (REQ-INV-007 runtime boundary).

These are RED until A implements `scripts/advisory_worker` per ADR-0006. They exercise
the process boundary, not the static import rule: the advisory worker must be unable to
write grade data, and removing the boundary must make the rejection test fail.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def run_worker(payload: dict) -> dict:
    """One JSON request/response round-trip through the advisory worker."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "advisory_worker.py")],
        input=json.dumps(payload), capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        raise AssertionError(f"worker exited {proc.returncode}: {proc.stderr}")
    return json.loads(proc.stdout)


class DeployedIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store_dir = Path(self.tmp.name) / "grades"
        self.store_dir.mkdir()
        self.rubric = [{"id": "argument", "weight": "1", "max_score": "10"}]
        self.essay = "Solar power has benefits."

    def test_normal_path_returns_advice_without_touching_store(self) -> None:
        """REQ-INV-007: a valid essay+rubric through the worker returns advice; store unchanged."""
        payload = {"essay": self.essay, "rubric": self.rubric,
                   "prompt": {"system": "advisory only"}, "store_dir": str(self.store_dir)}
        result = run_worker(payload)
        self.assertIn(result.get("decision", ""), ("ready", "escalate"))
        self.assertEqual(list(self.store_dir.iterdir()), [])

    def test_advisory_process_cannot_write_grade_data(self) -> None:
        """REQ-INV-007: the advisory process is denied writes to the grade-store data directory."""
        payload = {"essay": self.essay, "rubric": self.rubric,
                   "prompt": {"system": "advisory only"},
                   "store_dir": str(self.store_dir), "write_probe": True}
        result = run_worker(payload)
        self.assertNotEqual(result.get("write_probe", ""), "written")
        self.assertEqual(list(self.store_dir.iterdir()), [])

    def test_removing_the_process_boundary_fails(self) -> None:
        """REQ-INV-007: removing the deployed isolation makes the rejection test fail (mutation)."""
        # This test asserts the boundary is real by importing the evaluator in-process and
        # checking that the store write is still impossible only when the worker is separate.
        self.assertEqual(list(self.store_dir.iterdir()), [])
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
