# Evaluation logbook (D2)

> Owner: D (architecture evidence index). Records **what was actually observed** versus what is
> planned. This package contains **no genuine provider run**; synthetic-fixture results are labelled.
> Real evidence links live in `docs/member-a/verification-results.md`,
> `docs/member-b/evidence/*`, `handoff/verification/*`.

## Evidence status legend

- **measured-local**: deterministic local/synthetic run present in package.
- **measured-live**: genuine provider run — **none in this package** (live deferred until a real key).
- **analysis**: reasoned, not run.
- **planned**: not yet produced.

## Log entries

| # | Date | Evaluation | Type | Result | Status | Owner |
|---|---|---|---|---|---|---|
| E1 | 2026-11-07/08 | Calculator exactness: 50.005→50.01, 66.665→66.67, 68.00 golden | unit | pass | measured-local (`test_calculator`) | A |
| E2 | 2026-11-08 | Store approval: stale hash, duplicate, escalation-needs-reason, tamper detection | unit | pass | measured-local (`test_store`) | A |
| E3 | 2026-11-08 | Feedback: uncertain/null escalation, provider/refusal/cap/usage escalation | unit (synthetic) | pass | measured-local (`test_feedback`) | A |
| E4 | — | Import-boundary gate (safety) self-test | governance | present; pending `fractions`/`os` update | measured-local + planned edit | B/E |
| E5 | — | Semantic adversarial non-escalation fails gate | governance self-test | pass | measured-local (`test_semantic_eval`) | B |
| E6 | — | B/E acceptance suite against A `src/` | integration | **fail (red)** — API mismatch `calculate`/`validate_advice`/`record_grade` absent | known integration failure | A/B |
| E7 | — | Live fixed-set replay (coverage, schema, quotes, adversarial=1, escapes=0) | behavioral (real model) | not run | **待实测** | A/B |
| E8 | — | Token estimator study: `estimated_tokens ≥ actual prompt_tokens`; byte-guard (12 000) vs token cap (8 000) reconciliation | analysis | not run | planned | A |
| E9 | — | False-escalation / unsafe-pass curve for 0.80 threshold | behavioral + human labels | not run | planned | A/B + teacher |
| E10 | — | Live p95 latency (≥20 attempts) | performance | not run | planned | A |
| E11 | — | Altered-scores-after-approval negative test | unit | not written | planned | B/A |
| E12 | — | Config injection boundary (`os` removed from engine) | structural | not done | planned | A/E |
| E13 | — | Approval binding G2: score-substitution between confirmation and recording rejected | unit | not written | planned | A/B |

## Requirements baseline (C 0.1.0-c) — review status

| # | Item | Type | Result | Status | Owner |
|---|---|---|---|---|---|
| E14 | C registry v0.1.0-c, 47 entries, trace matrix mapped | governance | trace matrix re-keyed to C IDs; all 47 rows present | measured (D2 draft); **human review PENDING** | D → user |
| E15 | Decision-1: confidence required + `>= 0.80` (0.80 passes) per REQ-FUNC-002/003/008; code emits no confidence | decision | resolved (ADR-0001); implementation pending | **decided, pending impl** | A / B |
| E16 | Decision-2: verified local-signing approval per REQ-INV-003 (binding to confirmed scores) | decision | resolved (ADR-0002); implementation pending | **decided, pending impl** | A / E / B |

C's own package reports `scripts/validate_requirements.py` = schema PASS and `tools/gates.py schema` =
traceability BLOCKED. **No human signature exists**; this logbook does not claim baseline approval.

## Real-evidence pointers (do not duplicate)

- A offline verification: `docs/member-a/verification-results.md`, `handoff/verification/all-offline.txt`.
- B governance/local checks: `docs/member-b/evidence/local-validation.json`,
  `docs/member-b/VALIDATION.md`.
- Merged-package run summary: `handoff/verification/验证结果.md` (read before citing any pass).

## Honesty constraints

- Synthetic fixtures are **not** real-model evidence; they may not be reported as semantic quality.
- No entry claims a pass for E7/E9/E10 until a genuine provider run exists.
- Approval evidence in this package covers synthetic data only; no real teacher grade approval.
