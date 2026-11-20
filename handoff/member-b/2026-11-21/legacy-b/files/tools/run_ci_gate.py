"""Execute one named required CI status; never swallow a command failure."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command(args: list[str]) -> int:
    print("RUN " + " ".join(args), flush=True)
    return subprocess.run([sys.executable, *args], cwd=ROOT, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=["test-approval", "static-analysis", "schema", "semantic-evaluation", "regression", "ai-use-log"])
    args = parser.parse_args()
    base = os.environ.get("BASE_SHA", "")
    common = ["--base", base]
    commands: list[list[str]]
    if args.gate == "test-approval":
        commands = [["tools/gates.py", "approval", *common]]
    elif args.gate == "static-analysis":
        commands = [
            ["-m", "ruff", "check", "."], ["-m", "mypy", "src", "tools"],
            ["-m", "pip", "check"], ["tools/gates.py", "secrets"], ["-m", "pip_audit", "-r", "requirements-ci.txt"],
            ["tools/gates.py", "readiness"], ["tools/gates.py", "safety", *common],
        ]
        if (ROOT / "requirements-b-supplement.txt").is_file():
            commands.insert(4, ["-m", "pip_audit", "-r", "requirements-b-supplement.txt"])
        if (ROOT / "requirements-app.txt").is_file():
            commands.insert(4, ["-m", "pip_audit", "-r", "requirements-app.txt"])
    elif args.gate == "schema":
        commands = [["tools/gates.py", "schema"], ["tools/gates.py", "coevolution", *common]]
    elif args.gate == "semantic-evaluation":
        need = subprocess.run([sys.executable, "tools/gates.py", "semantic-needed", *common],
                              cwd=ROOT, capture_output=True, text=True, check=False)
        if need.returncode:
            print(need.stderr, file=sys.stderr)
            return 1
        commands = [["tools/semantic_eval.py", "--base", base]]
        if need.stdout.strip() == "false":
            commands[0].append("--check-baseline")
    elif args.gate == "regression":
        commands = [["tools/gates.py", "history", *common],
                    ["tools/check_suite.py", "test/governance"],
                    ["tools/check_suite.py", "test/offline"],
                    ["tools/mutation_check.py"], ["tools/application_mutation_check.py"]]
    else:
        commands = [["tools/gates.py", "ai-log", *common]]
    # Execute all checks, even if the first fails; the gate returns a failure if any fail.
    results = [command(cmd) for cmd in commands]
    return int(any(code != 0 for code in results))


if __name__ == "__main__":
    raise SystemExit(main())
