"""Local verification for the current application and its test map."""

import ast
import io
import json
import os
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from scripts import benchmark, validate_requirements

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r"\bREQ-[A-Z]+-[A-Z0-9]+\b")


class LocalEvidenceTests(unittest.TestCase):
    def test_benchmark_meets_local_p95_target(self):
        """REQ-PERF-001: measure 1,000 warm, correct calculations on a ten-criterion rubric."""
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(benchmark.main(), 0, output.getvalue())
        result = json.loads(output.getvalue())
        self.assertEqual(result["criteria"], 10)
        self.assertGreaterEqual(result["measured_calls"], 1000)
        self.assertLessEqual(result["p95_ms"], 10)

    def test_offline_regression_runs_without_provider_credentials(self):
        """REQ-QUAL-003: offline discovery runs without provider credentials or external sockets in the runner."""
        env = {k: v for k, v in os.environ.items()
               if not k.upper().startswith(("GRADEAIDE_", "LLM_", "DEEPSEEK_", "OPENAI_"))}
        env["GRADEAIDE_LIVE"] = "0"
        # The HTTP fixtures use loopback. This Python-process check is not OS isolation.
        code = """
import socket
import unittest

connect = socket.socket.connect
def local_only(sock, address):
    if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "::1"}:
        raise AssertionError("offline runner attempted a non-loopback socket connection")
    return connect(sock, address)

socket.socket.connect = local_only
suite = unittest.defaultTestLoader.discover("test/offline")
result = unittest.TextTestRunner().run(suite)
raise SystemExit(0 if result.wasSuccessful() and result.testsRun >= 65 and not result.skipped else 1)
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                                text=True, capture_output=True, timeout=90, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_registry_schema_and_each_mapped_locator(self):
        """REQ-GOV-B03, REQ-GOV-C02: validate registry and exact, registered test-to-REQ links."""
        registry, errors = validate_requirements.validate_structure()
        self.assertFalse(errors, errors)
        registered = {entry["id"] for entry in registry}
        mapping = yaml.safe_load((ROOT / "docs/verification/test-map.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(mapping), registered)

        locators = {}
        for path in (ROOT / "test").rglob("test_*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for cls in ast.walk(tree):
                if not isinstance(cls, ast.ClassDef):
                    continue
                for fn in cls.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name.startswith("test_"):
                        name = f"{path.relative_to(ROOT).as_posix()}::{cls.name}.{fn.name}"
                        ids = set(ID.findall(ast.get_docstring(fn) or ""))
                        self.assertTrue(ids and ids <= registered, (name, ids - registered))
                        locators[name] = ids
        for requirement, entry in mapping.items():
            with self.subTest(requirement=requirement):
                self.assertEqual(len(set(entry["tests"])), len(entry["tests"]))
                self.assertTrue(entry["tests"] or entry.get("pending_evidence"))
                for locator in entry["tests"]:
                    self.assertIn(requirement, locators.get(locator, set()), locator)
