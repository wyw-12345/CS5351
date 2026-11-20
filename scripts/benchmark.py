"""REQ-PERF-001: warm calculator latency, not live model latency."""

import json
import math
import platform
import statistics
import time

from src.score_calculator import calculate_score


def main():
    rubric = {"id": "ten-criteria-benchmark", "version": "1", "criteria": [
        {"id": str(i), "description": "Synthetic benchmark criterion", "max_score": "10", "weight": "0.1"}
        for i in range(10)]}
    scores = {str(i): "7" for i in range(10)}
    for _ in range(50):
        assert calculate_score(rubric, scores) == "70.00"
    durations = []
    for _ in range(1000):
        start = time.perf_counter_ns()
        assert calculate_score(rubric, scores) == "70.00"
        durations.append((time.perf_counter_ns() - start) / 1_000_000)
    p95 = sorted(durations)[math.ceil(len(durations) * .95) - 1]
    print(json.dumps({"requirement": "REQ-PERF-001", "python": platform.python_version(),
                      "platform": platform.platform(), "warmup_calls": 50, "measured_calls": 1000,
                      "criteria": 10, "p50_ms": statistics.median(durations), "p95_ms": p95,
                      "max_ms": max(durations), "target_p95_ms": 10, "target_met": p95 <= 10,
                      "scope": "local deterministic calculation only; no inference/network"}, indent=2))
    return 0 if p95 <= 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
