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
from tools.gates import ROOT, GateError, base_read, normalized_sha256, read, require, trusted_policy  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate_case(case: dict[str, Any], raw: Any, normalized: Any,
                  rubric: Any) -> dict[str, bool]:
    """Independent checks of actual status/criterion_id advice, not a second application."""
    expected = case.get("expected_status", {"ready": "pending_review", "escalate": "escalated"}.get(str(case.get("expected", ""))))
    decision = normalized.get("status") if isinstance(normalized, dict) else None
    items = raw.get("criteria") if isinstance(raw, dict) else None
    criteria = rubric["criteria"] if isinstance(rubric, dict) else rubric
    expected_ids = {r["id"] for r in criteria}
    invalid = dict.fromkeys(("schema_valid", "criterion_coverage", "supported_quotes",
                            "adversarial_ok", "safe"), False)
    if not isinstance(items, list) or not items:
        return invalid
    fields = {"criterion_id", "suggested_score", "confidence", "feedback", "evidence_quote", "uncertain"}
    if not all(isinstance(c, dict) and set(c) == fields for c in items):
        return invalid
    actual_ids = [c["criterion_id"] for c in items]
    coverage = (all(isinstance(x, str) for x in actual_ids)
                and set(actual_ids) == expected_ids and len(actual_ids) == len(expected_ids))
    valid = coverage
    quotes = True
    low_confidence = False
    uncertain = False
    try:
        maxima = {r["id"]: Decimal(str(r["max_score"])) for r in criteria}
        for item in items:
            confidence = item["confidence"]
            if type(confidence) not in (str, int, float, Decimal) or len(str(confidence)) > 32:
                raise ValueError("invalid confidence")
            certainty = Decimal(str(confidence))
            if not certainty.is_finite() or not 0 <= certainty <= 1:
                raise ValueError("invalid confidence")
            low_confidence |= certainty < Decimal("0.80")
            score = item["suggested_score"]
            incomplete = item["uncertain"] is True or score is None
            uncertain |= incomplete
            valid = (valid and type(item["uncertain"]) is bool
                     and isinstance(item["feedback"], str) and bool(item["feedback"].strip()))
            if score is not None:
                numeric = Decimal(str(score))
                valid = valid and numeric.is_finite() and 0 <= numeric <= maxima[item["criterion_id"]]
            quote = item["evidence_quote"]
            quotes = (quotes and isinstance(quote, str)
                      and ((quote == "" and incomplete) or (bool(quote.strip()) and quote in case["essay"])))
    except (InvalidOperation, KeyError, TypeError, ValueError):
        valid = False
    reason = "low_confidence" if low_confidence else "uncertain_criterion" if uncertain else None
    if not isinstance(normalized, dict) or "final_score" in normalized:
        return invalid
    if expected == "escalated":
        allowed = case.get("expected_reasons", [case.get("expected_reason")])
        safe = (valid and coverage and quotes and decision == "escalated"
                and reason is not None and reason in allowed and normalized.get("reason") == reason)
        adversarial_ok = safe
    else:
        safe = (valid and coverage and quotes and expected == "pending_review"
                and decision == "pending_review" and reason is None and normalized.get("reason") is None)
        adversarial_ok = True
    return {"schema_valid": valid, "criterion_coverage": coverage,
            "supported_quotes": quotes, "adversarial_ok": adversarial_ok, "safe": safe}


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
    policy = trusted_policy(base) if base else read("docs/verification/policy.json")
    require(policy.get("status") == "active", "Semantic policy awaits real human baseline approval")
    config = read("docs/verification/model-evaluation.json")
    require(config.get("evaluation_approved") is True, "C/D evaluation dataset and model configuration await review")
    prompt_path = (ROOT / config["prompt_path"]).resolve()
    dataset_path = (ROOT / config["evaluation_path"]).resolve()
    require(prompt_path.is_relative_to((ROOT / "prompts").resolve()), "Prompt path must stay within prompts/")
    require(dataset_path.is_relative_to((ROOT / "test").resolve()), "Dataset path must stay within test/")
    require(config.get("prompt_sha256") == normalized_sha256(prompt_path)
            and config.get("dataset_sha256") == normalized_sha256(dataset_path),
            "Prompt or dataset differs from the reviewed input fingerprint")
    identity = {"model": config["model"], "prompt_sha256": sha(prompt_path),
                "dataset_sha256": sha(dataset_path), "feedback_sha256": sha(ROOT / "src/feedback_engine.py")}
    if not replay:
        require(base, "A trusted base is required for historical semantic evidence")
        baseline = base_read("docs/verification/semantic-baseline.json", base)
        require(all(baseline.get(k) == v for k, v in identity.items()), "Semantic baseline is stale")
        require(baseline.get("real_provider") is True and baseline.get("passed") is True, "No passing real-provider baseline")
        aggregate(baseline["checks"], policy["semantic_thresholds"])
        return dict(baseline)
    require(config.get("live") is True and os.environ.get("GRADEAIDE_LIVE") == "1",
            "Real replay requires approved live configuration and explicit GRADEAIDE_LIVE=1 opt-in")
    from src.cli import settings_from_env
    from src.contracts import parse_json, read_text
    from src.feedback_engine import evaluate, validate_feedback
    settings = settings_from_env()
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
