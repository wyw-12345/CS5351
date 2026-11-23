"""ADR-0001 / ADR-0004: advisory-only LLM boundary. REQ-FUNC-002, REQ-INV-002, REQ-COST-001..005.

Working interface contract: no database imports, tools or authoritative score.
"""

import http.client
import socket
import threading
import time
from decimal import Decimal, localcontext
from typing import Any, Callable
from urllib.parse import urlsplit

from .contracts import (
    ValidationError,
    Settings,
    canonical,
    decimal_value,
    digest,
    exact_keys,
    parse_json,
    text_value,
    validate_essay,
    validate_rubric,
)



def request_json(body: dict[str, Any], settings: Settings) -> dict[str, Any]:
    """REQ-PERF-002: one request, connected-socket deadline, no redirects/retries.

    http.client avoids implicit credential-bearing redirect handling. A watchdog
    closes the connected socket at the deadline, including slow header/body reads.
    System DNS resolution is outside Python's socket timeout guarantee.
    """
    settings.validate()
    endpoint = urlsplit(settings.endpoint)
    connection_type = http.client.HTTPSConnection if endpoint.scheme == "https" else http.client.HTTPConnection
    if settings.proxy_url is None:
        connection = connection_type(endpoint.hostname or "", endpoint.port, timeout=settings.timeout)
    else:
        proxy = urlsplit(settings.proxy_url)
        connection = http.client.HTTPSConnection(proxy.hostname or "", proxy.port, timeout=settings.timeout)
        # CONNECT has no provider credentials. HTTPSConnection verifies the target's
        # certificate and hostname after establishing the tunnel using its default context.
        connection.set_tunnel(endpoint.hostname or "", endpoint.port or 443)
    started = time.monotonic()
    timer: threading.Timer | None = None
    try:
        connection.connect()
        connected_socket = connection.sock
        remaining = settings.timeout - (time.monotonic() - started)
        if connected_socket is None or remaining <= 0:
            raise TimeoutError

        def expire() -> None:
            try:
                connected_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connected_socket.close()

        timer = threading.Timer(remaining, expire)
        timer.daemon = True
        timer.start()
        connection.request("POST", endpoint.path or "/", canonical(body).encode("utf-8"), {
            "Authorization": "Bearer " + settings.api_key,
            "Content-Type": "application/json", "Accept": "application/json",
        })
        response = connection.getresponse()
        if response.status != 200:
            raise ValidationError(f"provider HTTP status {response.status}")
        data = response.read(settings.max_response_bytes + 1)
        if time.monotonic() - started >= settings.timeout:
            raise TimeoutError
        if len(data) > settings.max_response_bytes:
            raise ValidationError("provider response exceeds byte limit")
        result = parse_json(data.decode("utf-8"))
        if not isinstance(result, dict):
            raise ValidationError("invalid provider envelope")
        return result
    except (OSError, UnicodeError, http.client.HTTPException) as exc:
        # Never include exception bodies, endpoint credentials or request headers.
        raise ValidationError("provider transport failed or timed out") from exc
    finally:
        if timer is not None:
            timer.cancel()
        connection.close()


class ConfidenceError(ValidationError):
    """ADR-0001 / REQ-FUNC-003: distinguish malformed confidence from provider failures."""


def confidence_value(value: Any) -> Decimal:
    """ADR-0001 / REQ-FUNC-003: finite numeric confidence in [0, 1], never a boolean."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)) or len(str(value)) > 32:
        raise ConfidenceError("invalid_confidence")
    try:
        number = Decimal(str(value))
    except ArithmeticError as exc:
        raise ConfidenceError("invalid_confidence") from exc
    if not number.is_finite() or not Decimal(0) <= number <= Decimal(1):
        raise ConfidenceError("invalid_confidence")
    return number


def escalation_reason(feedback: dict[str, Any]) -> str | None:
    """ADR-0001 / REQ-INV-002: all validation precedes confidence and uncertainty decisions."""
    if any(confidence_value(item["confidence"]) < Decimal("0.80") for item in feedback["criteria"]):
        return "low_confidence"
    if any(item["uncertain"] or item["suggested_score"] is None for item in feedback["criteria"]):
        return "uncertain_criterion"
    return None


def validate_feedback(value: Any, essay: str, rubric: dict[str, Any]) -> dict[str, Any]:
    """REQ-INV-002 / REQ-SEC-002: exact rubric membership and literal quotes."""
    validate_essay(essay)
    validate_rubric(rubric)
    if isinstance(value, dict):
        value = {key: item for key, item in value.items() if key != "final_score"}
    value = exact_keys(value, {"criteria"}, "feedback")
    items = value["criteria"]
    expected = {item["id"]: item for item in rubric["criteria"]}
    if not isinstance(items, list) or len(items) != len(expected):
        raise ValidationError("feedback must cover every criterion")
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or "confidence" not in item:
            raise ConfidenceError("invalid_confidence")
        confidence_value(item["confidence"])
        item = exact_keys(item, {"confidence", "criterion_id", "suggested_score", "feedback", "evidence_quote", "uncertain"},
                          "feedback item")
        criterion_id = text_value(item["criterion_id"], "criterion id", 100)
        if criterion_id not in expected or criterion_id in seen:
            raise ValidationError("unknown or repeated criterion")
        seen.add(criterion_id)
        text_value(item["feedback"], "feedback")
        if type(item["uncertain"]) is not bool:
            raise ValidationError("uncertain must be boolean")
        if item["suggested_score"] is not None:
            decimal_value(item["suggested_score"], "suggested score", Decimal(expected[criterion_id]["max_score"]))
        quote = item["evidence_quote"]
        # An uncertain item may have no supporting evidence, but never fabricate it.
        if quote == "" and (item["uncertain"] or item["suggested_score"] is None):
            continue
        text_value(quote, "evidence quote")
        if quote not in essay:
            raise ValidationError("evidence quote is not in essay")
    return value


def _cost(input_tokens: int, output_tokens: int, settings: Settings) -> str:
    with localcontext() as ctx:
        ctx.prec = 50
        return format((Decimal(input_tokens) * Decimal(settings.input_price)
                       + Decimal(output_tokens) * Decimal(settings.output_price)) / Decimal(1000000), "f")


def evaluate(essay: str, rubric: dict[str, Any], prompt: dict[str, Any], settings: Settings,
             transport: Callable[[dict[str, Any], Settings], dict[str, Any]] = request_json,
             *, mode: str = "live") -> dict[str, Any]:
    """REQ-FUNC-002: return advice or escalation; never return a final grade."""
    validate_essay(essay)
    validate_rubric(rubric)
    exact_keys(prompt, {"version", "system"}, "prompt")
    text_value(prompt["version"], "prompt version", 100)
    text_value(prompt["system"], "system prompt", 10000)
    settings.validate()
    result: dict[str, Any] = {
        "status": "escalated", "reason": None, "feedback": None,
        "metadata": {"mode": mode, "requested_model": settings.model, "provider_model": None,
                     "prompt_version": prompt["version"], "prompt_hash": digest(prompt),
                     "usage": None, "latency_ms": 0.0, "calls": 0,
                     "price_source": settings.price_source, "input_price_per_million": settings.input_price,
                     "output_price_per_million": settings.output_price, "max_cost": settings.max_cost,
                     "max_input_bytes": settings.max_input_bytes, "max_output_tokens": settings.max_output_tokens,
                     "timeout_seconds": settings.timeout, "max_response_bytes": settings.max_response_bytes,
                     "thinking": settings.thinking,
                     "input_budget_method": "serialized messages UTF-8 bytes, conservative token proxy",
                     "estimated_cost": None, "reported_usage_cost": None},
    }
    messages = [{"role": "system", "content": prompt["system"]},
                {"role": "user", "content": canonical({"rubric": rubric, "essay": essay})}]
    input_bytes = len(canonical(messages).encode("utf-8"))
    metadata = result["metadata"]
    metadata["input_bytes"] = input_bytes
    metadata["estimated_cost"] = _cost(input_bytes, settings.max_output_tokens, settings)
    if input_bytes > settings.max_input_bytes:
        result["reason"] = "input_budget_exceeded"
        return result
    if Decimal(metadata["estimated_cost"]) > Decimal(settings.max_cost):
        result["reason"] = "cost_budget_exceeded"
        return result
    body = {"model": settings.model, "messages": messages, "max_tokens": settings.max_output_tokens,
            "temperature": 0, "response_format": {"type": "json_object"}, "stream": False}
    if settings.thinking is not None:
        body["thinking"] = {"type": settings.thinking}
    started = time.monotonic()
    metadata["calls"] = 1
    try:
        envelope = transport(body, settings)
        if not isinstance(envelope, dict):
            raise ValidationError("invalid provider envelope")
        # Preserve known billing evidence even if content is truncated or invalid.
        usage = envelope.get("usage")
        if isinstance(usage, dict):
            keys = ["prompt_tokens", "completion_tokens", "total_tokens"]
            valid_usage = all(type(usage.get(key)) is int and 0 <= usage[key] <= 10000000 for key in keys)
            if valid_usage and usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]:
                metadata["usage"] = {key: usage[key] for key in keys}
                metadata["reported_usage_cost"] = _cost(usage["prompt_tokens"], usage["completion_tokens"], settings)
        metadata["provider_model"] = text_value(envelope.get("model"), "provider model", 200)
        choices = envelope.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise ValidationError("invalid provider choices")
        choice = choices[0]
        if choice.get("finish_reason") != "stop":
            raise ValidationError("provider response was incomplete or refused")
        message = choice.get("message")
        if (not isinstance(message, dict) or message.get("role") != "assistant"
                or message.get("tool_calls") or message.get("function_call") or message.get("refusal")):
            raise ValidationError("provider attempted tools or refused")
        value = parse_json(text_value(message.get("content"), "provider content", settings.max_response_bytes))
        feedback = validate_feedback(value, essay, rubric)
        result["feedback"] = feedback
        usage = metadata["usage"]
        if usage is None:
            raise ValidationError("provider usage unavailable")
        if usage["prompt_tokens"] <= 0 or usage["completion_tokens"] <= 0:
            raise ValidationError("invalid empty provider usage")
        if usage["completion_tokens"] > settings.max_output_tokens:
            raise ValidationError("provider exceeded output cap")
        if Decimal(metadata["reported_usage_cost"]) > Decimal(settings.max_cost):
            raise ValidationError("reported usage exceeded cost budget")
        result["reason"] = escalation_reason(feedback)
        if result["reason"] is None:
            result["status"] = "pending_review"
    except ConfidenceError:
        result["reason"] = "invalid_confidence"
    except (ValidationError, OSError, TimeoutError, TypeError, KeyError, ValueError):
        result["reason"] = "invalid_or_unavailable_provider_response"
    finally:
        metadata["latency_ms"] = round((time.monotonic() - started) * 1000, 3)
    return result
