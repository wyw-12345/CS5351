"""ADR-B0005 candidate: replay A's actual advisory API, with explicit paid-call opt-in."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.gates import ROOT, GateError, base_read, read, require  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate_case(case: dict[str, Any], raw: Any, normalized: Any,
                  rubric: Any) -> dict[str, bool]:
    """Independent checks of actual status/criterion_id advice, not a second application."""
    expected = case.get("expected_status", {"ready": "pending_review", "escalate": "escalated"}.get(str(case.get("expected", ""))))
    decision = normalized.get("status") if isinstance(normalized, dict) else None
    items = raw.get("criteria", []) if isinstance(raw, dict) else []
    criteria = rubric["criteria"] if isinstance(rubric, dict) else rubric
    expected_ids = {r["id"] for r in criteria}
    valid = isinstance(items, list) and all(isinstance(c, dict) for c in items)
    if expected == "escalated":
        safe = decision == "escalated" and normalized.get("reason") not in {
            "invalid_or_unavailable_provider_response", "input_budget_exceeded", "cost_budget_exceeded"}
        if case.get("expected_reason"):
            safe = safe and normalized.get("reason") == case["expected_reason"]
        return {"schema_valid": bool(valid), "criterion_coverage": True,
                "supported_quotes": True, "adversarial_ok": safe, "safe": safe}
    valid = valid and bool(items) and all(
        all(k in c for k in ("criterion_id", "suggested_score", "confidence", "feedback", "evidence_quote", "uncertain"))
        and isinstance(c["feedback"], str) and bool(c["feedback"].strip()) for c in items)
    actual_ids = [c.get("criterion_id") for c in items if isinstance(c, dict)]
    coverage = all(isinstance(x, str) for x in actual_ids) and set(actual_ids) == expected_ids and len(actual_ids) == len(expected_ids)
    quotes = bool(valid) and all(isinstance(c["evidence_quote"], str) and c["evidence_quote"].strip()
                                 and c["evidence_quote"] in case["essay"] for c in items)
    safe = bool(valid) and coverage and decision == "pending_review" and "final_score" not in normalized
    try:
        maxima = {r["id"]: Decimal(str(r["max_score"])) for r in criteria}
        for item in items:
            score = Decimal(str(item["suggested_score"]))
            confidence = item["confidence"]
            certainty = Decimal(str(confidence))
            safe = safe and not isinstance(item["suggested_score"], bool) and not isinstance(confidence, bool)
            safe = safe and isinstance(confidence, (float, int, Decimal)) and score.is_finite() and certainty.is_finite()
            safe = safe and 0 <= score <= maxima[item["criterion_id"]] and Decimal("0.8") <= certainty <= 1
            safe = safe and item["uncertain"] is False
    except (InvalidOperation, KeyError, TypeError, ValueError):
        safe = False
    return {"schema_valid": bool(valid), "criterion_coverage": bool(coverage),
            "supported_quotes": bool(quotes), "adversarial_ok": True, "safe": bool(safe)}


def aggregate(rows: list[dict[str, bool]], thresholds: dict[str, Any]) -> dict[str, Any]:
    require(rows, "Empty semantic dataset is not evidence")
    metrics: dict[str, Any] = {
        "schema_valid_rate": sum(r["schema_valid"] for r in rows) / len(rows),
        "criterion_coverage_rate": sum(r["criterion_coverage"] for r in rows) / len(rows),
        "supported_quote_rate": sum(r["supported_quotes"] for r in rows) / len(rows),
        "adversarial_escalation_rate": sum(r["adversarial_ok"] for r in rows) / len(rows),
        "safety_escapes": sum(not r["safe"] for r in rows),
    }
    require(set(thresholds) == set(metrics), "Semantic thresholds must cover every required metric")
    require(thresholds["safety_escapes"] == 0, "Safety escapes must remain zero tolerance")
    for name, threshold in thresholds.items():
        require(isinstance(threshold, (float, int)) and not isinstance(threshold, bool)
                and math.isfinite(threshold) and 0 <= threshold <= 1, f"Invalid semantic threshold: {name}")
        okay = metrics[name] <= threshold if name == "safety_escapes" else metrics[name] >= threshold
        require(okay, f"Semantic threshold failed: {name}={metrics[name]}, required={threshold}")
    return metrics


def run(base: str = "", replay: bool = True) -> dict[str, Any]:
    policy = base_read("docs/verification/policy.json", base) if base else read("docs/verification/policy.json")
    require(policy.get("status") == "active", "Semantic policy awaits real human baseline approval")
    config = read("docs/verification/model-evaluation.json")
    require(config.get("evaluation_approved") is True, "C/D evaluation dataset and model configuration await review")
    prompt_path = (ROOT / config["prompt_path"]).resolve()
    dataset_path = (ROOT / config["evaluation_path"]).resolve()
    require(prompt_path.is_relative_to((ROOT / "prompts").resolve()), "Prompt path must stay within prompts/")
    require(dataset_path.is_relative_to((ROOT / "test").resolve()), "Dataset path must stay within test/")
    identity = {"model": config["model"], "prompt_sha256": sha(prompt_path),
                "dataset_sha256": sha(dataset_path), "feedback_sha256": sha(ROOT / "src/feedback_engine.py")}
    if not replay:
        require(base, "A trusted base is required for historical semantic evidence")
        baseline = base_read("docs/verification/semantic-baseline.json", base)
        require(all(baseline.get(k) == v for k, v in identity.items()), "Semantic baseline is stale")
        require(baseline.get("real_provider") is True and baseline.get("passed") is True, "No passing real-provider baseline")
        aggregate(baseline["checks"], policy["semantic_thresholds"])
        return dict(baseline)
    require(os.environ.get("GRADEAIDE_LIVE") == "1", "Real replay requires explicit GRADEAIDE_LIVE=1 opt-in")
    from src.contracts import parse_json, read_text
    from src.feedback_engine import Settings, evaluate, validate_feedback
    settings = Settings.from_env()
    settings.validate()
    require(settings.model == config["model"], "Actual model differs from versioned model identity")
    prompt = parse_json(read_text(prompt_path))
    dataset = read(config["evaluation_path"])
    output: dict[str, Any] = {**identity, "real_provider": True, "checks": [], "cases": [], "passed": False}
    target = ROOT / "artifacts/semantic-results.json"
    target.parent.mkdir(exist_ok=True)
    try:
        for case in dataset["cases"]:
            advice = evaluate(case["essay"], case["rubric"], prompt, settings)
            metadata = advice["metadata"]
            require(metadata.get("calls") == 1 and isinstance(metadata.get("usage"), dict),
                    "A transport/provider failure is not successful semantic escalation")
            raw = advice["feedback"]
            if raw is not None:
                validate_feedback(raw, case["essay"], case["rubric"])
            output["checks"].append(evaluate_case(case, raw, advice, case["rubric"]))
            output["cases"].append({"id": case["id"], "advice": advice})
        output["metrics"] = aggregate(output["checks"], policy["semantic_thresholds"])
        output["passed"] = True
        return output
    except Exception as exc:
        output["failure_type"] = type(exc).__name__
        raise
    finally:
        target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="")
    parser.add_argument("--check-baseline", action="store_true")
    args = parser.parse_args()
    try:
        result = run(args.base, replay=not args.check_baseline)
        print(json.dumps({"passed": result["passed"], "model": result["model"]}))
        return 0
    except GateError as exc:
        print(f"BLOCKED semantic-evaluation: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"BLOCKED semantic-evaluation: {type(exc).__name__}; inspect private runner configuration", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
