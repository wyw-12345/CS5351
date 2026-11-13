# Runtime policy catalog (D2)

> Owner: D. Status: baseline. For each decision point: trigger, policy, observable signal, fallback.
> "Implemented" = present in `src/`; "Required" = architecture mandate not yet implemented;
> "Target" = design target pending measurement.

## A. AI feedbacker (`feedback_engine`)

| # | Trigger | Policy | Observable | Fallback | Status |
|---|---|---|---|---|---|
| A1 | Essay/rubric/prompt invalid | Reject before request | `ValidationError` | No call; CLI exit 2 | implemented |
| A2 | Input bytes > 12 000 (enforced guard) | Zero calls; escalate `input_budget_exceeded`; no truncation/compaction | `metadata.input_bytes`, `reason` | Teacher handles | implemented; retained |
| A2b | Estimated tokens > 8 000 (design target) | Zero calls; escalate (target reason `token_budget_exceeded`) | estimated tokens | Teacher handles | **planned/待实测**; byte guard is binding until measured |
| A3 | Estimated cost > `MAX_COST` | Zero calls; escalate `cost_budget_exceeded` | `estimated_cost`, `max_cost` | Teacher handles | implemented |
| A4 | Provider timeout | One attempt, no retry; escalate | `latency_ms`, `reason` | Visible new human-triggered attempt | implemented |
| A5 | Non-200 / transport failure | Escalate `invalid_or_unavailable_provider_response` | `reason` | Retry only by human | implemented |
| A6 | Refusal / tool call / incomplete finish | Escalate | `reason` | Teacher review | implemented |
| A7 | Missing/negative/bool usage | Escalate, usage stays unknown (never 0) | `usage`, `reported_usage_cost` | Escalate | implemented |
| A8 | Output > cap / response bytes > cap | Escalate | `reason` | Escalate | implemented |
| A9 | Any criterion `uncertain`/null score | Escalate `uncertain_criterion` | `status`, `reason` | Teacher resolves (ADR-0001) | implemented |
| A10 | Advice has unexpected top-level `final_score` | **Ignore as untrusted** (not error) | advice retained; total unused | Store recomputes | **required** (A currently rejects, `:152`) |
| A11 | Any confidence missing/invalid/`< 0.80` | **Escalate** (D4; 0.80 passes) | `reason` = `low_confidence`/`invalid_confidence` | Teacher resolves via manual grading path | **target** (ADR-0001; not in `src/` yet) |
| A12 | Tool/function message from provider | Escalate | `reason` | Escalate | implemented |
| A13 | `os` import in engine | **Forbidden** (E gate) | gate failure | Change refused | **required** (A imports `os`, `:7`) |

## B. Grade store (`grade_store`)

| # | Trigger | Policy | Observable | Fallback | Status |
|---|---|---|---|---|---|
| B1 | Create proposal | Validate advice; persist no grade | `final_score=None` | — | implemented |
| B2 | Approve w/o explicit scores for all IDs | Reject | `ValidationError` | No write | implemented |
| B3 | Approval hash mismatch (stale proposal) | Reject `PermissionError`/`ValidationError` | error | Re-review current proposal | implemented |
| B4 | Escalated proposal, no reason | Reject | error | Supply reason | implemented |
| B5 | Caller supplies final score | Ignored; store recomputes | `score` == calculator | — | implemented |
| B6 | Duplicate approval, same content | **Idempotent return** existing record | same `record_id` | — | **required** (A currently rejects, `:165`) |
| B7 | Same `submission_id`, different content | `ValueError`; original preserved | one record | Conflict reject | **required** (add `submission_id`) |
| B8 | Read detects digest mismatch / tamper | Integrity error | `ValidationError` | Refuse read; manual reconcile | implemented |
| B9 | Schema version mismatch | Refuse open; preserve file | error | Manual migration | implemented |
| B10 | Approved proposal's scores alter after approval | Refuse / integrity fail | recompute mismatch | Manual reconcile | implemented (add explicit test) |
| B11 | Approval signature invalid / key not trusted | Reject `PermissionError`; zero writes | verify failure | Refuse, teacher re-approves with trusted key | **target** (ADR-0002) |
| B12 | `confirmed_scores_sha256` ≠ `H(canonical(accepted_scores))` | Reject; zero writes | hash mismatch | Re-confirm scores | **target** (ADR-0002) |
| B13 | Signature replayed onto different submission/proposal | Reject; zero writes | `submission_id`/`proposal_hash` mismatch | Refuse | **target** (ADR-0002) |
| B14 | Multi-user / remote approval | Out of scope (local signing only) | — | Reopen ADR-0002 for external verifier | documented deferral |

## C. Config / secrets (boundary)

| # | Trigger | Policy | Status |
|---|---|---|---|
| C1 | Missing required env | Refuse to run | implemented (in engine; **required** move to CLI) |
| C2 | Secret in output/log/artifact | Forbidden; redact errors | implemented (errors generic, `cli.py:68-71`) |
| C3 | HTTP non-loopback endpoint | Reject (HTTPS only) | implemented (`:91-92`) |
| C4 | Credentials in endpoint URL | Reject | implemented (`:87-89`) |
| C5 | Config injected into engine via value object | **Required** (no `os` in engine) | **required** |

## D. Escalation terminal handling

| # | Situation | Policy | Status |
|---|---|---|---|
| D1 | Escalated proposal unresolved | No grade persists | implemented |
| D2 | Teacher resolves escalated case (incl. D4 low/invalid confidence) with full scores + reason + verified signature | Grade = calculator total; audit records `previous_status=escalated` + reason + signature | implemented for scores/reason (`:169-177`); **signing + confidence-escalation target (ADR-0001/0002)** |
| D3 | Any authority/approval/audit violation at runtime | Stop writes, quarantine, privacy-safe diagnostic, notify teacher, manual reconcile | partially — test runner reports; notification service **not implemented** |

## E. Observability signals (for monitors)

- Per attempt: `mode`, `requested_model`, `provider_model`, `prompt_version`, `prompt_hash`, `usage`,
  `estimated_cost`, `reported_usage_cost`, `latency_ms`, `calls`, budget fields
  (`feedback_engine.py:197-209`).
- Per advice criterion (target, ADR-0001): `confidence` value + pass/fail vs `0.80`; escalation reasons
  `low_confidence`/`invalid_confidence`.
- Per record: `score`, `audit{proposal_hash, submission_id, rubric_version, reviewer` (label), `verified_key_id`,
  `reason`, `accepted_scores`, `confirmed_scores_sha256`, `signature`, `final_score`,
  `approved_at, calculator_version, previous_status}` (signing/submission/rubric fields are **target**,
  ADR-0002).
- Aggregate monitors to build (B/D): authority-escape count, unsafe-automatic-grade count,
  unauthorized-write count, false-escalation rate (needs eval), secret-leak count.

## F. Runtime fallback that is described, not implemented

See D3 in §D. `verification-constraints.md:37-39` requires E/B to wire an actual notification/quarantine
path; the current package only reports failures.
