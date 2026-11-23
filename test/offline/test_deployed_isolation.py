"""Real Linux sandbox acceptance, including an executable enforcement-removal mutant."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DeployedIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Path(self.tmp.name) / 'grades'
        self.store.mkdir()
        (self.store.parent / 'operator-secret.key').write_text('synthetic operator secret')
        self.payload = {
            'essay': (ROOT / 'examples/essay.txt').read_text(),
            'rubric': json.loads((ROOT / 'examples/rubric.json').read_text()),
            'prompt': json.loads((ROOT / 'prompts/prompt_v1.2.yaml').read_text()),
            'settings': {'endpoint': 'http://127.0.0.1/unused', 'model': 'synthetic-fixture',
                         'api_key': 'unused', 'input_price': '0', 'output_price': '0', 'max_cost': '0'},
            'fixture': json.loads((ROOT / 'examples/provider-fixture.json').read_text()),
        }

    def invoke(self, root=ROOT, probe=False):
        cmd = [sys.executable, str(root / 'scripts/advisory_worker.py')]
        if probe:
            cmd += ['--probe-directory', str(self.store)]
        return subprocess.run(cmd, input=json.dumps(self.payload), capture_output=True,
                              text=True, timeout=30)

    def assert_denied(self, root=ROOT):
        p = self.invoke(root, probe=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertTrue(result['probe']['attempted'])
        self.assertEqual(result['probe']['write'], 'denied')
        self.assertEqual(result['probe']['network'], 'denied')
        self.assertEqual(result['probe']['secret_read'], 'denied')
        self.assertEqual(result['probe']['uid'], 65534)
        self.assertNotEqual(result['probe']['network_namespace'], os.readlink('/proc/self/ns/net'))
        self.assertNotEqual(result['probe']['pid'], os.getpid())
        self.assertEqual(list(self.store.iterdir()), [])

    def test_normal_path_returns_advice_without_touching_store(self):
        """REQ-INV-007: real isolated fixture evaluation returns schema-valid advice."""
        p = self.invoke()
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result['status'], 'pending_review')
        self.assertEqual(result['metadata']['mode'], 'synthetic_fixture')
        self.assertEqual(len(result['feedback']['criteria']), 2)
        self.assertEqual(list(self.store.iterdir()), [])

    def test_advisory_process_cannot_write_grade_data(self):
        """REQ-INV-007: real writes and network attempts are denied in the evaluator."""
        self.assert_denied()

    def test_removing_the_process_boundary_fails(self):
        """REQ-INV-007: removing real enforcement breaks the same denial assertion."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for folder in ('src', 'scripts'):
                shutil.copytree(ROOT / folder, root / folder)
            worker = root / 'scripts/advisory_worker.py'
            source = worker.read_text()
            before = 'command = sandbox_command(probe_directory)'
            self.assertEqual(source.count(before), 1)
            changed = source.replace(before,
                'command = [sys.executable, str(Path(__file__).resolve()), "--child"]')
            compile(changed, str(worker), 'exec')
            worker.write_text(changed)
            with self.assertRaisesRegex(AssertionError, 'written.*denied'):
                self.assert_denied(root)

    def test_worker_rejects_invalid_ipc_and_unsupported_platform(self):
        """REQ-INV-007: malformed/oversized IPC and unsupported platforms fail closed."""
        for value in ('[]', '{', 'x' * 512001):
            p = subprocess.run([sys.executable, str(ROOT / 'scripts/advisory_worker.py')],
                               input=value, text=True, capture_output=True, timeout=10)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(p.stdout, '')
        from unittest.mock import patch
        from scripts.advisory_worker import invoke_worker
        with patch('scripts.advisory_worker.sys.platform', 'win32'):
            with self.assertRaisesRegex(ValueError, 'requires Linux'):
                invoke_worker('', {}, {}, None)
