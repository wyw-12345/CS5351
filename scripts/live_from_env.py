"""Explicit local .env launcher; never evaluates shell syntax or prints secrets."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from src.contracts import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def load_environment(path: Path) -> None:
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.removeprefix("export ").partition("=")
        key, value = key.strip(), value.strip()
        if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValidationError("invalid .env assignment")
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValidationError("unclosed .env quote")
            value = value[1:-1]
        if key.startswith("GRADEAIDE_"):
            values[key] = value
        elif key in {"LLM_BASE_URL", "LLM_MODEL", "DEEPSEEK_API_KEY", "LLM_TIMEOUT"}:
            values[key] = value
    aliases = {"LLM_MODEL": "GRADEAIDE_MODEL", "DEEPSEEK_API_KEY": "GRADEAIDE_API_KEY",  # pragma: allowlist secret - synthetic value or environment variable name
               "LLM_TIMEOUT": "GRADEAIDE_TIMEOUT"}
    for old, new in aliases.items():
        if old in values and new not in values:
            values[new] = values[old]
    if "GRADEAIDE_ENDPOINT" not in values and "LLM_BASE_URL" in values:
        base = values["LLM_BASE_URL"].rstrip("/")
        values["GRADEAIDE_ENDPOINT"] = base if base.endswith("/chat/completions") else base + "/chat/completions"
    for key, value in values.items():
        if key.startswith("GRADEAIDE_"):
            os.environ[key] = value


def main() -> int:
    parser = argparse.ArgumentParser(description="Run synthetic live tests using a local .env")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--mode", choices=["smoke", "suite", "evaluate"], default="smoke")
    parser.add_argument("--repeat", type=int, default=4)
    args = parser.parse_args()
    if not args.confirm_live:
        parser.error("--confirm-live is required")
    try:
        load_environment(args.env_file)
    except (OSError, UnicodeError, ValidationError):
        print("Cannot load valid local configuration.", file=sys.stderr)
        return 2
    os.environ["GRADEAIDE_LIVE"] = "1"
    if args.mode == "evaluate":
        command = ["scripts.evaluate_live", "--confirm-live", "--repeat", str(args.repeat)]
    else:
        target = "test.live.test_live_api"
        if args.mode == "smoke":
            target += ".LiveTests.test_real_provider_smoke"
        command = ["unittest", target, "-v"]
    return subprocess.call([sys.executable, "-m", *command], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
