"""T3 real loopback HTTP: REQ-PERF-002, REQ-COST-001/004, REQ-SEC-004."""

import json
import threading
import time
import unittest
from contextlib import contextmanager
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.feedback_engine import evaluate
from test.support import ESSAY, PROMPT, RUBRIC, SETTINGS, envelope


@contextmanager
def provider_server(*, status=200, raw=None, delay=0, slow_body=False):
    requests = []
    body = json.dumps(envelope()).encode() if raw is None else raw

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            request_body = self.rfile.read(int(self.headers["Content-Length"]))
            requests.append({"body": json.loads(request_body), "authorization": self.headers.get("Authorization")})
            time.sleep(delay)
            try:
                self.send_response(status)
                if status == 302:
                    self.send_header("Location", "/redirected")
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if slow_body:
                    for byte in body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.01)
                else:
                    self.wfile.write(body)
            except (OSError, ConnectionError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/chat/completions", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


class HttpTests(unittest.TestCase):
    def test_real_request_response_serialization(self):
        """REQ-PERF-002: real request response serialization."""
        with provider_server() as (url, requests):
            result = evaluate(ESSAY, RUBRIC, PROMPT, replace(SETTINGS, endpoint=url))
        self.assertEqual(result["status"], "pending_review")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["authorization"], "Bearer test-key")
        self.assertEqual(requests[0]["body"]["max_tokens"], 1024)
        self.assertEqual(requests[0]["body"]["messages"][0]["role"], "system")
        self.assertNotIn("tools", requests[0]["body"])

    def test_redirect_and_server_error_never_retry_or_follow(self):
        """REQ-PERF-002: redirect and server error never retry or follow."""
        for status in [302, 429, 500]:
            with self.subTest(status=status), provider_server(status=status) as (url, requests):
                result = evaluate(ESSAY, RUBRIC, PROMPT, replace(SETTINGS, endpoint=url))
                self.assertEqual(result["status"], "escalated")
                self.assertEqual(len(requests), 1)

    def test_delayed_header_times_out(self):
        """REQ-PERF-002: delayed header times out."""
        with provider_server(delay=0.3) as (url, requests):
            started = time.monotonic()
            result = evaluate(ESSAY, RUBRIC, PROMPT, replace(SETTINGS, endpoint=url, timeout=0.05))
            elapsed = time.monotonic() - started
            self.assertEqual(result["status"], "escalated")
            self.assertLess(elapsed, 1)
            self.assertEqual(len(requests), 1)

    def test_slow_trickle_is_stopped_by_connected_deadline(self):
        """REQ-PERF-002: slow trickle is stopped by connected deadline."""
        with provider_server(slow_body=True) as (url, _):
            started = time.monotonic()
            result = evaluate(ESSAY, RUBRIC, PROMPT, replace(SETTINGS, endpoint=url, timeout=0.08))
            self.assertEqual(result["status"], "escalated")
            self.assertLess(time.monotonic() - started, 1)

    def test_invalid_json_encoding_envelope_and_response_limit(self):
        """REQ-PERF-002: invalid json encoding envelope and response limit."""
        for raw in [b"{bad}", b"\xff", b"[]", b"x" * 1001]:
            with self.subTest(raw=raw[:20]), provider_server(raw=raw) as (url, _):
                result = evaluate(ESSAY, RUBRIC, PROMPT, replace(SETTINGS, endpoint=url, max_response_bytes=1000))
                self.assertEqual(result["status"], "escalated")


if __name__ == "__main__":
    unittest.main()
