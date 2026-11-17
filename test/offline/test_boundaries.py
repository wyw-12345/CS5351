"""ADR-0003 / REQ-INV-007: configuration boundary and unchanged calculator regression."""
import ast
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from src.cli import settings_from_env
from src.contracts import ValidationError
from src.feedback_engine import Settings


class BoundaryTests(unittest.TestCase):
    def test_engine_has_no_environment_or_authority_import(self):
        """REQ-INV-007: advisory engine cannot import filesystem/config/store authority."""
        tree = ast.parse(Path("src/feedback_engine.py").read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(x.name.split(".")[0] for x in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add((node.module or "").split(".")[0])
        self.assertFalse(imports & {"os", "pathlib", "grade_store", "subprocess", "importlib",
                                    "shutil", "builtins"})
        self.assertFalse(hasattr(Settings, "from_env"))

    def test_missing_env_fails_without_secret_output(self):
        """REQ-SEC-004: missing config fails at caller; secret never appears in repr."""
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValidationError):
            settings_from_env()
        with patch.dict(os.environ, {
            "GRADEAIDE_ENDPOINT": "https://example.invalid/chat/completions", "GRADEAIDE_MODEL": "test",
            "GRADEAIDE_API_KEY": "test-secret-value", "GRADEAIDE_INPUT_PRICE_PER_MILLION": "1",  # pragma: allowlist secret - synthetic value or environment variable name
            "GRADEAIDE_OUTPUT_PRICE_PER_MILLION": "2", "GRADEAIDE_MAX_COST": "1",
            "GRADEAIDE_PRICE_SOURCE": "synthetic"}, clear=True):
            settings = settings_from_env()
            settings.validate()
            self.assertNotIn("test-secret-value", repr(settings))
