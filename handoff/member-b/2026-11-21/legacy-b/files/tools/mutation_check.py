"""Mutate only disposable copies of B gate tooling. REQ-GOV-B05.

Application invariant mutants still require A's real implementation and D's approved mutation plan.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = [
    ("bot-review", "tools/gates.py", 'r["user"].get("type") == "User"', 'True'),
    ("self-review", "tools/gates.py", "name != author", "True"),
    ("late-test-approval", "tools/gates.py", 'parse(review["submitted_at"]) < parse(first_code_time)', 'True'),
    ("advisory-import", "tools/gates.py", "not (set(names) & forbidden)", "True"),
    ("unlogged-path", "tools/gates.py", "set(relevant) <= covered", "True"),
    ("injection-escape", "tools/semantic_eval.py", 'decision == "escalated"', "True"),
]


def main() -> int:
    results = []
    for name, filename, original, replacement in MUTANTS:
        with tempfile.TemporaryDirectory(prefix="gradeaide-b-mutant-") as tmp:
            root = Path(tmp)
            for folder in ("tools", "test", "docs", "src", "evidence", "config", "prompts"):
                if (ROOT / folder).is_dir():
                    shutil.copytree(ROOT / folder, root / folder, ignore=shutil.ignore_patterns("__pycache__", "proposals"))
            path = root / filename
            source = path.read_text(encoding="utf-8")
            if source.count(original) != 1:
                print(f"BLOCKED: mutation target changed: {name}", file=sys.stderr)
                return 1
            baseline = subprocess.run([sys.executable, "tools/check_suite.py", "test/governance"],
                                      cwd=root, capture_output=True, text=True, check=False, timeout=60)
            if baseline.returncode:
                print(f"BLOCKED: disposable baseline tests already fail for {name}", file=sys.stderr)
                print(baseline.stderr[-2000:], file=sys.stderr)
                return 1
            path.write_text(source.replace(original, replacement, 1), encoding="utf-8")
            result = subprocess.run([sys.executable, "tools/check_suite.py", "test/governance"],
                                    cwd=root, capture_output=True, text=True, check=False, timeout=60)
            killed = result.returncode != 0
            results.append({"mutant": name, "killed": killed})
            print(f"{'KILLED' if killed else 'SURVIVED'} {name}")
    output = ROOT / "artifacts/b-tool-mutations.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return int(any(not r["killed"] for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
