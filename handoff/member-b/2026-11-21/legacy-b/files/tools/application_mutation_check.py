"""Real application mutants in temporary copies; unimplemented obligations stay blocked."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = [
    ("INV-001-recompute", "src/grade_store.py",
     'if grade["score"] != calculated or audit["final_score"] != calculated:', 'if False:',
     "test.offline.test_store.StoreTests.test_payload_and_grade_corruption_are_detected"),
    ("INV-002-uncertainty", "src/feedback_engine.py",
     'if any(item["uncertain"] or item["suggested_score"] is None for item in feedback["criteria"]):',
     'if False:', "test.offline.test_feedback.FeedbackTests.test_uncertain_null_is_an_escalation_not_a_zero_score"),
    ("INV-004-range", "src/contracts.py", "if result > maximum:", "if False:",
     "test.offline.test_calculator.CalculatorTests.test_invalid_scores_rejected"),
    ("INV-005-half-up", "src/score_calculator.py",
     "rounded = whole + (2 * remainder >= cents.denominator)", "rounded = whole",
     "test.offline.test_calculator.CalculatorTests.test_exact_half_cent_after_recurring_division"),
    ("INV-006-atomicity", "src/grade_store.py",
     'self.connection.execute("ROLLBACK")\n            raise\n        return self.get(proposal_id)',
     'self.connection.execute("COMMIT")\n            raise\n        return self.get(proposal_id)',
     "test.offline.test_store.StoreTests.test_failed_audit_insert_rolls_back_status_and_grade"),
]


def main() -> int:
    results: list[dict[str, Any]] = []
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GRADEAIDE_", "LLM_", "DEEPSEEK_", "OPENAI_"))}
    env["GRADEAIDE_LIVE"] = "0"
    for name, filename, before, after, test in MUTANTS:
        with tempfile.TemporaryDirectory(prefix="gradeaide-app-mutant-") as directory:
            root = Path(directory)
            for folder in ("src", "test", "tools", "docs", "prompts", "evidence", "config"):
                if (ROOT / folder).is_dir():
                    shutil.copytree(ROOT / folder, root / folder,
                                    ignore=shutil.ignore_patterns("__pycache__", "proposals"))
            command = [sys.executable, "-m", "unittest", test, "-v"]
            baseline = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True,
                                      check=False, timeout=60)
            if baseline.returncode:
                results.append({"mutant": name, "status": "BLOCKED", "reason": "baseline already fails"})
                continue
            path = root / filename
            source = path.read_text(encoding="utf-8")
            if source.count(before) != 1:
                results.append({"mutant": name, "status": "BLOCKED", "reason": "mutation target changed"})
                continue
            changed = source.replace(before, after, 1)
            compile(changed, filename, "exec")
            path.write_text(changed, encoding="utf-8")
            result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True,
                                    check=False, timeout=60)
            killed = result.returncode != 0
            results.append({"mutant": name, "status": "KILLED" if killed else "SURVIVED", "test": test,
                            "baseline_passed": True, "mutation_compiles": True})
    results.extend([
        {"mutant": "INV-003-signing", "status": "NOT RUN", "reason": "A signing behavior not implemented"},
        {"mutant": "INV-008-idempotency", "status": "NOT RUN", "reason": "A submission identity not implemented"},
        {"mutant": "INV-007-advisory-authority", "status": "NOT RUN", "reason": "E runtime isolation evidence pending; gate import mutant is separate"},
    ])
    target = ROOT / "artifacts/application-mutations.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for row in results:
        print(row["status"], row["mutant"])
    # All planned invariants must eventually be verified: incomplete coverage is a release failure.
    return int(any(row["status"] != "KILLED" for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
