"""Run all tiers without hiding missing live configuration. REQ-GOV-B05."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    failed = False
    for folder in ("test/governance", "test/offline", "test/live"):
        result = subprocess.run([sys.executable, "tools/check_suite.py", folder],
                                cwd=root, env=env, check=False)
        failed |= result.returncode != 0
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
