"""Proposed explicit operator proxy contract; no paid requests or runtime changes."""
from dataclasses import replace
import json
import os
import ssl
import unittest
from dataclasses import asdict
from unittest.mock import patch

from src.cli import settings_from_env
from src.contracts import ValidationError
from src.feedback_engine import request_json
from test.support import SETTINGS, ESSAY, RUBRIC, PROMPT, envelope


class BrokerProxyTests(unittest.TestCase):
    def settings(self, proxy="http://127.0.0.1:10808"):
        return replace(SETTINGS, endpoint="https://model.example.invalid/chat/completions",
                       proxy_url=proxy)

    def response(self, factory, status=200):
        connection = factory.return_value
        connection.getresponse.return_value.status = status
        connection.getresponse.return_value.read.return_value = json.dumps(envelope()).encode()
        return connection

    def test_explicit_loopback_proxy_tunnels_only_to_model_endpoint(self):
        """REQ-SEC-004: explicit proxy uses one tunnel and sends credentials only inside TLS."""
        with patch('src.feedback_engine.http.client.HTTPSConnection') as factory:
            connection = self.response(factory)
            self.assertEqual(request_json({'task': 'synthetic'}, self.settings()), envelope())
            factory.assert_called_once_with('127.0.0.1', 10808, timeout=SETTINGS.timeout)
            connection.set_tunnel.assert_called_once_with('model.example.invalid', 443)
            connection.connect.assert_called_once()
            connection.request.assert_called_once()
            self.assertNotIn(SETTINGS.api_key, repr(connection.set_tunnel.call_args))
            self.assertEqual(connection.request.call_args.args[3]['Authorization'],
                             'Bearer ' + SETTINGS.api_key)
            connection.close.assert_called_once()

    def test_unconfigured_transport_ignores_ambient_proxy(self):
        """REQ-SEC-004: ambient HTTP(S)_PROXY cannot silently reroute grading credentials."""
        with patch.dict(os.environ, {'HTTPS_PROXY': 'http://untrusted.invalid:80'}):
            with patch('src.feedback_engine.http.client.HTTPSConnection') as factory:
                connection = self.response(factory)
                request_json({}, self.settings(None))
                factory.assert_called_once_with('model.example.invalid', None, timeout=SETTINGS.timeout)
                connection.set_tunnel.assert_not_called()

    def test_proxy_configuration_rejects_credentials_and_external_targets(self):
        """REQ-SEC-004: proxy is explicit loopback HTTP without credentials or URL suffixes."""
        invalid = ['http://user:password@127.0.0.1:10808', 'http://untrusted.invalid:80',
                   'https://127.0.0.1:10808', 'socks5://127.0.0.1:10808',
                   'http://127.0.0.1:10808/path', 'http://127.0.0.1:10808?x=1',
                   'http://127.0.0.1:10808#x', 'http://127.0.0.1:0',
                   'http://127.0.0.1:not-a-port', 'http://127.0.0.1']
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(ValidationError):
                self.settings(url).validate()
        with self.assertRaises(ValidationError):
            replace(self.settings(), endpoint='http://127.0.0.1/provider').validate()

    def test_proxy_never_retries_or_follows_redirects(self):
        """REQ-COST-001: proxy responses never trigger another provider request."""
        for status in (302, 307, 429, 500):
            with self.subTest(status=status):
                with patch('src.feedback_engine.http.client.HTTPSConnection') as factory:
                    connection = self.response(factory, status)
                    with self.assertRaises(ValidationError):
                        request_json({}, self.settings())
                    connection.request.assert_called_once()
                    connection.close.assert_called_once()

    def test_tls_failure_is_not_bypassed_or_retried(self):
        """REQ-SEC-004: target certificate failure is fatal and creates no provider POST."""
        with patch('src.feedback_engine.http.client.HTTPSConnection') as factory:
            connection = self.response(factory)
            connection.connect.side_effect = ssl.SSLCertVerificationError('synthetic failure')
            with self.assertRaises(ValidationError):
                request_json({}, self.settings())
            connection.request.assert_not_called()
            connection.connect.assert_called_once()
            connection.close.assert_called_once()

    def test_cli_loads_only_explicit_proxy_configuration(self):
        """REQ-SEC-004: the operator must set GRADEAIDE_PROXY_URL rather than ambient proxy."""
        values = {'GRADEAIDE_ENDPOINT': SETTINGS.endpoint, 'GRADEAIDE_MODEL': SETTINGS.model,
                  'GRADEAIDE_API_KEY': SETTINGS.api_key, 'GRADEAIDE_INPUT_PRICE_PER_MILLION': '0',
                  'GRADEAIDE_OUTPUT_PRICE_PER_MILLION': '0', 'GRADEAIDE_MAX_COST': '0',
                  'GRADEAIDE_PRICE_SOURCE': 'synthetic test',
                  'GRADEAIDE_PROXY_URL': 'http://127.0.0.1:10808'}
        with patch.dict(os.environ, values, clear=True):
            self.assertEqual(settings_from_env().proxy_url, values['GRADEAIDE_PROXY_URL'])

    def test_proxy_not_provisioned_to_networkless_evaluator(self):
        """REQ-INV-007, REQ-SEC-004: endpoint routing stays in the trusted broker only."""
        from scripts.advisory_worker import broker
        payload = {'essay': ESSAY, 'rubric': RUBRIC, 'prompt': PROMPT,
                   'settings': asdict(self.settings()), 'fixture': envelope()}
        advice = {'status': 'pending_review', 'reason': None,
                  'feedback': {'criteria': []}, 'metadata': {}}
        with patch('scripts.advisory_worker.sandbox_command', return_value=['bwrap-test']):
            with patch('scripts.advisory_worker.run_process', return_value=advice) as run:
                broker(payload, None)
                wire_settings = run.call_args.args[1]['settings']
                self.assertIsNone(wire_settings.get('proxy_url'))
                self.assertNotEqual(wire_settings['api_key'], SETTINGS.api_key)
