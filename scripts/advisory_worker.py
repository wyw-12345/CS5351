"""ADR-0006: one bounded stdio request, trusted transport broker, networkless evaluator."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 512000


def decode(data: bytes) -> dict[str, Any]:
    if len(data) > LIMIT:
        raise ValueError("IPC size limit")
    from src.contracts import parse_json
    value = parse_json(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("IPC object required")
    return value


def validate_advice(value: dict[str, Any]) -> dict[str, Any]:
    if (set(value) != {"status", "reason", "feedback", "metadata"}
            or value["status"] not in {"pending_review", "escalated"}
            or not isinstance(value["metadata"], dict)
            or (value["feedback"] is not None and not isinstance(value["feedback"], dict))
            or (value["reason"] is not None and not isinstance(value["reason"], str))):
        raise ValueError("invalid advice IPC")
    return value


def run_process(command: list[str], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    data = json.dumps(payload, allow_nan=False).encode("utf-8")
    if len(data) > LIMIT:
        raise ValueError("IPC size limit")
    # The worker and all descendants are killed on timeout, including a blocked transport.
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                                                       "PYTHONDONTWRITEBYTECODE": "1"},
                          start_new_session=True) as process:
        try:
            output, _ = process.communicate(data, timeout=timeout)
        except subprocess.TimeoutExpired:
            getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL"))
            process.communicate()
            raise TimeoutError("advisory deadline") from None
    if process.returncode:
        raise ValueError("advisory process refused request")
    return decode(output)


def invoke_worker(essay: str, rubric: dict[str, Any], prompt: dict[str, Any],
                  settings: Any, fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    if sys.platform != "linux":
        raise ValueError("advisory isolation requires Linux and bubblewrap")
    payload = {"essay": essay, "rubric": rubric, "prompt": prompt, "settings": asdict(settings)}
    if fixture is not None:
        payload["fixture"] = fixture
    return validate_advice(run_process([sys.executable, str(Path(__file__).resolve())], payload,
                                       settings.timeout + 10))


def sandbox_command(probe_directory: str | None) -> list[str]:
    if sys.platform != "linux" or not shutil.which("bwrap"):
        raise ValueError("Linux bubblewrap is required")
    command = ["bwrap", "--die-with-parent", "--new-session", "--unshare-all",
               "--uid", "65534", "--gid", "65534",
               "--cap-drop", "ALL", "--ro-bind", "/usr", "/usr"]
    for folder in ("/lib", "/lib64"):
        if Path(folder).exists():
            command += ["--ro-bind", folder, folder]
    command += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                "--ro-bind", str(ROOT / "src"), "/app/src",
                "--ro-bind", str(Path(__file__).resolve()), "/app/scripts/advisory_worker.py",
                "--chdir", "/app"]
    if probe_directory is not None:
        command += ["--ro-bind", probe_directory, probe_directory]
    command += ["--", "/usr/bin/python3", "-I", "/app/scripts/advisory_worker.py", "--child"]
    return command


def child(payload: dict[str, Any]) -> dict[str, Any]:
    from src.feedback_engine import Settings, evaluate
    settings = Settings(**payload["settings"])
    fixture = payload["fixture"]
    result = evaluate(payload["essay"], payload["rubric"], payload["prompt"], settings,
                      lambda _body, _settings: fixture, mode=payload["mode"])
    directory = payload.get("probe_directory")
    if directory:
        probe = {"attempted": True, "pid": os.getpid(), "uid": getattr(os, "getuid")(),
                 "network_namespace": os.readlink("/proc/self/ns/net"),
                 "write": "denied", "network": "denied", "secret_read": "denied"}
        try:
            (Path(directory) / "unauthorized-write").write_text("probe")
            probe["write"] = "written"
        except OSError:
            pass
        try:
            (Path(directory).parent / "operator-secret.key").read_text()
            probe["secret_read"] = "read"
        except OSError:
            pass
        try:
            with socket.create_connection(("1.1.1.1", 443), timeout=0.5):
                probe["network"] = "connected"
        except OSError:
            pass
        result["probe"] = probe
    return result


def broker(payload: dict[str, Any], probe_directory: str | None) -> dict[str, Any]:
    from src.feedback_engine import Settings, evaluate, request_json
    if set(payload) - {"essay", "rubric", "prompt", "settings", "fixture"}:
        raise ValueError("unknown request fields")
    started = time.monotonic()
    settings = Settings(**payload["settings"])
    settings.validate()
    command = sandbox_command(probe_directory)
    bodies: list[dict[str, Any]] = []

    def capture(body: dict[str, Any], _settings: Settings) -> dict[str, Any]:
        bodies.append(body)
        raise OSError("request prepared")

    # Preflight validates inputs/budget and constructs the single request. No model output
    # is evaluated in this host-network broker; only the sandbox evaluates the response.
    preflight = evaluate(payload["essay"], payload["rubric"], payload["prompt"], settings, capture)
    if not bodies:
        return preflight
    fixture = payload.get("fixture")
    mode = "synthetic_fixture" if fixture is not None else "live"
    if fixture is None:
        try:
            fixture = request_json(bodies[0], settings)
        except (ValueError, OSError, TimeoutError):
            fixture = {}
    request = dict(payload, fixture=fixture, mode=mode)
    request["settings"] = dict(payload["settings"], api_key="not-provisioned-in-sandbox")
    if probe_directory is not None:
        request["probe_directory"] = str(Path(probe_directory).resolve(strict=True))
    result = run_process(command, request, settings.timeout + 5)
    result["metadata"]["latency_ms"] = round((time.monotonic() - started) * 1000, 3)
    if probe_directory is None:
        validate_advice(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--probe-directory", help="operator-only diagnostic mount; never a disable switch")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    try:
        payload = decode(sys.stdin.buffer.read(LIMIT + 1))
        result = child(payload) if args.child else broker(payload, args.probe_directory)
        output = json.dumps(result, allow_nan=False).encode("utf-8")
        if len(output) > LIMIT:
            raise ValueError("IPC size limit")
        sys.stdout.buffer.write(output)
        return 0
    except (ValueError, OSError, TypeError, KeyError, TimeoutError):
        print("advisory request refused", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
