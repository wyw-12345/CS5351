"""Exercise A's historical suite with no live credentials and external connects refused."""
import os
import subprocess
import sys
import unittest
from pathlib import Path


class OfflineEnvironmentTests(unittest.TestCase):
    def test_a_suite_needs_no_live_credentials_or_external_connects(self):
        """REQ-QUAL-003: credential-free A regression uses only local deterministic fixtures."""
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("GRADEAIDE_", "LLM_", "DEEPSEEK_", "OPENAI_"))}
        env["GRADEAIDE_LIVE"] = "0"
        code = '''
import socket, unittest
original = socket.socket.connect
def local_only(self, address):
    if isinstance(address, tuple) and address[0] not in {"localhost", "127.0.0.1", "::1"}:
        raise AssertionError("external network forbidden in offline test process")
    return original(self, address)
socket.socket.connect = local_only
names = ["test.offline." + name for name in ["test_calculator", "test_cli", "test_env_launcher",
         "test_feedback", "test_http", "test_live_runner", "test_store"]]
result = unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.loadTestsFromNames(names))
raise SystemExit(0 if result.wasSuccessful() and result.testsRun == 45 and not result.skipped else 1)
'''
        result = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[2],
                                env=env, capture_output=True, text=True, timeout=45, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
