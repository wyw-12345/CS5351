"""REQ-INV-001: the sole grade authority; member A working interface contract."""

from fractions import Fraction
from typing import Any

from .contracts import validate_rubric, validate_scores


def calculate_score(rubric: dict[str, Any], scores: dict[str, str]) -> str:
    """Validate every input and round the weighted percentage only once."""
    validate_rubric(rubric)
    validate_scores(rubric, scores)
    # Rational accumulation prevents intermediate division from shifting exact half-cent ties.
    total = sum((Fraction(item["weight"]) * Fraction(scores[item["id"]]) / Fraction(item["max_score"])
                 for item in rubric["criteria"]), Fraction(0))
    cents = total * 10000
    whole, remainder = divmod(cents.numerator, cents.denominator)
    rounded = whole + (2 * remainder >= cents.denominator)
    return f"{rounded // 100}.{rounded % 100:02d}"
