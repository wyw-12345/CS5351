"""REQ-SEC-004 / REQ-COST-001: local configuration and explicit inference mode."""

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from scripts.live_from_env import load_environment
from src.contracts import ValidationError
from src.feedback_engine import evaluate
from test.support import ESSAY, PROMPT, RUBRIC, SETTINGS, envelope


class EnvTests(unittest.TestCase):
    def test_aliases_are_data_not_shell_commands(self):
        """REQ-SEC-004: aliases are data not shell commands."""
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / ".env"
            path.write_text('LLM_BASE_URL=https://example.test/v1\nDEEPSEEK_API_KEY="$(do-not-execute)"\n'
                            'LLM_MODEL=example\nLLM_TIMEOUT=90\n', encoding="utf-8")
            load_environment(path)
            self.assertEqual(os.environ["GRADEAIDE_ENDPOINT"], "https://example.test/v1/chat/completions")
            self.assertEqual(os.environ["GRADEAIDE_API_KEY"], "$(do-not-execute)")
            path.write_text('BROKEN', encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_environment(path)

    def test_thinking_is_explicit_and_validated(self):
        """REQ-SEC-004: thinking is explicit and validated."""
        requests = []
        def transport(body, settings):
            requests.append(body)
            return envelope()
        evaluate(ESSAY, RUBRIC, PROMPT, replace(SETTINGS, thinking="disabled"), transport)
        self.assertEqual(requests[0]["thinking"], {"type": "disabled"})
        with self.assertRaises(ValidationError):
            replace(SETTINGS, thinking="invalid").validate()
