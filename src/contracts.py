"""ADR-0003: shared validation; REQ-FUNC-001, REQ-SEC-007, REQ-INV-004."""

import hashlib
import json
import re
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """Input cannot be safely interpreted; never fill in a default score."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key")
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise ValidationError("non-finite JSON number")


def parse_json(text: str) -> Any:
    """REQ-SEC-007: reject ambiguous JSON and nonfinite constants."""
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise ValidationError("invalid or ambiguous JSON") from exc


def read_text(path: str | Path, limit: int = 100_000) -> str:
    """REQ-FUNC-001: bounded UTF-8 import, without truncation."""
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValidationError("input file exceeds byte limit")
    try:
        return data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValidationError("input must be UTF-8") from exc


def canonical(value: Any) -> str:
    """REQ-INV-006: stable serialization for proposal and audit digests."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    """REQ-INV-006: identify canonical content without another raw audit copy."""
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    """REQ-SEC-007: reject missing and unexpected fields."""
    if not isinstance(value, dict) or set(value) != keys:
        raise ValidationError(f"invalid {label} fields")
    return value


def text_value(value: Any, label: str, maximum: int = 2000) -> str:
    """REQ-SEC-007: validate bounded Unicode text without coercion."""
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValidationError(f"invalid {label}")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise ValidationError(f"invalid {label} encoding") from exc
    return value


def decimal_value(value: Any, label: str, maximum: Decimal = Decimal("1000000")) -> Decimal:
    """REQ-INV-004: bounded decimal strings only; no exponents or coercion."""
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]{0,6})(?:\.[0-9]{1,6})?", value):
        raise ValidationError(f"{label} must be a bounded nonnegative decimal string")
    result = Decimal(value)
    if result > maximum:
        raise ValidationError(f"{label} exceeds maximum")
    return result


def validate_rubric(rubric: Any) -> dict[str, Any]:
    """REQ-FUNC-001 / REQ-INV-004: exact IDs and normalized positive weights."""
    rubric = exact_keys(rubric, {"id", "version", "criteria"}, "rubric")
    text_value(rubric["id"], "rubric id", 100)
    text_value(rubric["version"], "rubric version", 100)
    criteria = rubric["criteria"]
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= 10:
        raise ValidationError("rubric must contain 1 to 10 criteria")
    ids: set[str] = set()
    with localcontext() as ctx:
        ctx.prec = 50
        total = Decimal(0)
        for item in criteria:
            item = exact_keys(item, {"id", "description", "max_score", "weight"}, "criterion")
            criterion_id = text_value(item["id"], "criterion id", 100)
            if criterion_id in ids:
                raise ValidationError("duplicate criterion id")
            ids.add(criterion_id)
            text_value(item["description"], "criterion description")
            maximum = decimal_value(item["max_score"], "max score")
            weight = decimal_value(item["weight"], "weight", Decimal(1))
            if maximum <= 0 or weight <= 0:
                raise ValidationError("max score and weight must be positive")
            total += weight
        if total != Decimal(1):
            raise ValidationError("weights must sum exactly to 1")
    return rubric


def validate_scores(rubric: dict[str, Any], scores: Any) -> dict[str, str]:
    """REQ-INV-004: every criterion is scored explicitly exactly once."""
    rubric = validate_rubric(rubric)
    scores = exact_keys(scores, {item["id"] for item in rubric["criteria"]}, "scores")
    for item in rubric["criteria"]:
        decimal_value(scores[item["id"]], "score", Decimal(item["max_score"]))
    return scores


def validate_essay(essay: Any) -> str:
    """REQ-FUNC-001: validate one bounded nonempty essay."""
    return text_value(essay, "essay", 100_000)
