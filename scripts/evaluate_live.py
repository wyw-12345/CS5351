"""REQ-PERF-003 / REQ-FUNC-002: explicit opt-in real-model evaluation of synthetic cases."""

import argparse
import json
import math
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.cli import settings_from_env
from src.contracts import ValidationError, parse_json, read_text
from src.feedback_engine import evaluate

ROOT = Path(__file__).resolve().parents[1]


def run_cases(repeat=1):
    if os.environ.get("GRADEAIDE_LIVE") != "1":
        raise ValidationError("Live evaluation requires GRADEAIDE_LIVE=1")
    if type(repeat) is not int or not 1 <= repeat <= 20:
        raise ValidationError("repeat must be between 1 and 20")
    settings = settings_from_env()
    settings.validate()
    prompt = parse_json(read_text(ROOT / "prompts/prompt_v1.2.yaml"))
    dataset = parse_json(read_text(ROOT / "test/live/fixed-cases.json"))
    results = []
    for trial in range(repeat):
        for case in dataset["cases"]:
            advice = evaluate(case["essay"], case["rubric"], prompt, settings)
            results.append({"case_id": case["id"], "trial": trial + 1,
                            "expected_status": case["expected_status"],
                            "expectation_met": (advice["status"] == case["expected_status"]
                                                and advice["metadata"]["usage"] is not None
                                                and advice["metadata"]["calls"] == 1
                                                and (advice["status"] != "escalated"
                                                     or advice["reason"] in case.get("expected_reasons", [case.get("expected_reason")]))),
                            "human_review_focus": case["human_review_focus"], "advice": advice})
    latencies = sorted(item["advice"]["metadata"]["latency_ms"] for item in results
                       if item["advice"]["metadata"]["calls"])
    p95 = latencies[math.ceil(len(latencies) * .95) - 1] if latencies else None
    return {"recorded_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
            "dataset_version": dataset["version"], "calls_attempted": len(latencies),
            "p95_ms": p95, "p95_sample_sufficient": len(latencies) >= 20,
            "expected_status_match_count": sum(item["expectation_met"] for item in results),
            "case_count": len(results), "results": results,
            "semantic_review": "PENDING: a human must assess relevance, fairness and whether quotations support feedback. Status/schema checks are not semantic approval."}


def main():
    parser = argparse.ArgumentParser(description="Paid/network live evaluation; synthetic essays only")
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--repeat", type=int, default=1, help="five cases per repeat; 4 repeats give 20 attempts")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if not args.confirm_live or os.environ.get("GRADEAIDE_LIVE") != "1":
        parser.error("set GRADEAIDE_LIVE=1 and supply --confirm-live to permit real requests")
    if not 1 <= args.repeat <= 20:
        parser.error("repeat must be between 1 and 20")
    try:
        result = run_cases(args.repeat)
    except (ValidationError, OSError):
        print("Live evaluation refused: configure valid endpoint, model, key and prices.", file=sys.stderr)
        return 2
    path = Path(args.output or "evidence/live-results.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(path), "calls_attempted": result["calls_attempted"],
                      "expected_status_matches": result["expected_status_match_count"],
                      "cases": result["case_count"], "human_semantic_review": "pending"}))
    return 0 if result["expected_status_match_count"] == result["case_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
