# C → D handoff: requirements baseline

Date: 2026-11-12
Baseline: `docs/req/requirements.yaml` version 0.1.0-c (47 entries)
Status: `draft_ready`, not human-approved.

## Read in this order

1. `docs/req/requirements.yaml` — the formal registry.
2. `docs/req/prd.yaml` — scope, personas, user stories and workflow.
3. `docs/req/requirement-id-map.yaml` — every A/B/E proposal decision.
4. `docs/req/requirements-review-record.md` — what is confirmed, what is pending.
5. `docs/req/traceability-handoff.yaml` — which IDs still need real tests.
6. `docs/member-b/02-interface-contract.md` — proposal only; do not treat it as frozen.

## What D must decide

| Decision | C's current position | D action |
|---|---|---|
| Rubric exchange shape | C kept requirements behavior-level | Freeze A's object shape or B's list shape; update contract |
| Calculator API | A: `calculate_score`; B: `calculate` | Choose one and record ADR |
| Advice validation API | A: `validate_feedback`; B: `validate_advice` | Choose one and record ADR |
| Grade store API | A: `GradeStore`; B: `record_grade` | Choose one and record ADR |
| Exact arithmetic | A: `Fraction`; B: `Decimal` | Confirm the observable one-rounding rule and the implementation |
| Approval identity | A: local reviewer string; E: trusted verifier | Freeze the trust boundary and authentication mechanism |
| Quality thresholds | C drafted five QUAL requirements | Confirm ASR and make them measurable |
| Performance thresholds | A proposed 10 ms calculator p95, 30 s live p95 | Confirm release gates and evidence |
| Traceability | 14/47 IDs mapped; 33 need tests | Fill `docs/architecture/trace-matrix.md` and assign owners |

## Non-negotiables

- Keep all eight invariants zero-tolerance.
- Do not remove requirements to make `tools/gates.py schema` pass.
- Do not treat C's draft as a human-approved baseline.
- Do not edit `docs/req/requirements.yaml` without updating `requirement-id-map.yaml`, traceability and the AI-use log (`REQ-GOV-C01`).

## Current verification truth

- `scripts/validate_requirements.py` → schema/registry PASS.
- `tools/gates.py schema` → BLOCKED at traceability (`REQ-FUNC-001` has no mapped test).
- `tools/gates.py proposal` → BLOCKED by a pre-existing untraced test.
- No human review or signature has been obtained.
