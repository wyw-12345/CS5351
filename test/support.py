"""Independent synthetic test data, not generated from the runtime prompt."""

import copy
import json

from src.feedback_engine import Settings

ESSAY = "Rainwater saves treated water. Tanks require cleaning."
RUBRIC = {"id": "test", "version": "1", "criteria": [
    {"id": "content", "description": "Reasoned claim", "max_score": "10", "weight": "0.6"},
    {"id": "structure", "description": "Connected ideas", "max_score": "10", "weight": "0.4"},
]}
PROMPT = {"version": "test-independent", "system": "Return rubric-aligned JSON."}
SETTINGS = Settings("http://127.0.0.1/unused", "test-model", "test-key", "1", "2", "1")
SCORES = {"content": "8", "structure": "6"}


def feedback():
    return {"criteria": [
        {"criterion_id": "content", "suggested_score": "8", "feedback": "Supported claim.",
         "evidence_quote": "Rainwater saves treated water.", "uncertain": False, "confidence": "0.90"},
        {"criterion_id": "structure", "suggested_score": "7", "feedback": "Linked limitation.",
         "evidence_quote": "Tanks require cleaning.", "uncertain": False, "confidence": "0.90"},
    ]}


def envelope(value=None):
    return {"model": "test-model", "choices": [{"finish_reason": "stop", "message": {
        "role": "assistant", "content": json.dumps(feedback() if value is None else value)}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180}}


def transport(value=None):
    result = envelope() if value is None else value
    return lambda body, settings: copy.deepcopy(result)
