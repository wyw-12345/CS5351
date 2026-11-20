# ADR-0001 — Escalation policy

- Status: Accepted (D2 baseline); **revised 2026-11-12 to align with C's draft requirements 0.1.0-c**
  (REQ-FUNC-002, REQ-FUNC-003, REQ-FUNC-008). The requirements baseline is **pending human review**.
- Date: 2026-11-11 (initial); 2026-11-12 (confidence revision).
- Supersedes/relates: resolves the A-vs-B/E disagreement in
  `handoff/A-B-E-接口差异与待决事项.md` rows "模型输出", "注入处置", "重复提交". Resolves Conflict-1
  (0.80 confidence vs prior deferral) recorded in `docs/architecture/trace-matrix.md`.
- Owner: D. Enforced by: `src/feedback_engine.py`, `src/grade_store.py`.
- Alignment: **aligned with C's draft 0.1.0-c.** Confidence is now a required, validated field with a
  `0.80` threshold; the threshold value is C's, and its *effectiveness is not yet evaluated* (§Candidate
  evidence). Target behavior is **pending implementation and verification**.

## Context

The AI feedbacker is advisory. The system must never silently produce a numeric grade from
incomplete or untrusted AI output. Two implementations disagree about *when* to escalate and what an
escalation *is*:

- **A** (`src/feedback_engine.py:263-266`, `:267-268`): a per-criterion boolean `uncertain` (or a
  null `suggested_score`) escalates with reason `uncertain_criterion`; any provider/transport/
  protocol failure escalates with `invalid_or_unavailable_provider_response`; a stray top-level
  `final_score` **raises** (`exact_keys(..., {"criteria"})`, `:152`) and therefore escalates. An
  escalated proposal can later be **resolved into a grade** by a human who supplies every score plus
  a nonempty reason (`src/grade_store.py:169-177`).
- **B/E** (`docs/member-b/02-interface-contract.md:13`; `test/offline/test_authority_boundary.py:69-95`):
  a numeric `confidence ≥ 0.80` is required; `decision: "ready"|"escalate"`; a top-level
  `final_score` is **ignored** (not an error); recording escalated advice raises `ValueError`.

The product question — does "escalate" *transfer scoring authority to the teacher* or *refuse any
grade* — is an ASR-level choice. The team owner has now fixed it: **a teacher may resolve an escalated
case by entering a complete score set and a reason; the calculator computes the total.**

C's draft baseline 0.1.0-c makes the divergence sharper and resolves it: **REQ-FUNC-002** requires the
feedback to return a `confidence` value per criterion; **REQ-FUNC-003** accepts advice only when the
confidence is at least `0.80`; **REQ-FUNC-008** escalates when advice is "below the confidence
threshold". The earlier D2 baseline deferred 0.80 as an unmeasured candidate; the user has directed D to
**follow C's draft** and adopt the confidence requirement now. The threshold's effectiveness remains
unevaluated (§Candidate evidence), but the architecture obligation is no longer optional.

## Decision

1. **Escalate on any of these triggers (fail-closed):**
   - **D1 — deterministic invalid AI output:** missing, duplicate, or unknown rubric criterion IDs;
     a criterion set that does not exactly equal the rubric set; invalid, non-finite, boolean,
     out-of-range, or non-string scores; a **missing or invalid `confidence` value** (see D4); a
     malformed/non-object provider envelope; refusal or tool calls; incomplete finish reason;
     missing/invalid provider usage; a response exceeding the output or byte cap.
   - **D2 — explicit model uncertainty:** any criterion with `uncertain == true` or a null
     `suggested_score`.
   - **D3 — provider unavailability:** transport failure, timeout, or non-200 status. One attempt,
     no retry (`REQ-PERF-002`, `REQ-COST-001`).
   - **D4 — confidence below threshold (REQ-FUNC-003/008):** any criterion whose `confidence` is
     missing, not a valid numeric value, or **below `0.80`**. A confidence of **exactly `0.80`
     passes** the confidence check (`confidence < 0.80` escalates; `confidence == 0.80` does not).
     `confidence` must be a finite number in `[0, 1]`; booleans, NaN/Infinity, out-of-range values and
     non-numeric types are **invalid** and escalate. All other validation rules still apply
     independently — passing the confidence check never waives D1/D2/D3.
2. **Every rubric criterion must carry a valid `confidence` value.** A response that omits the field,
   supplies a malformed value, or supplies one outside `[0, 1]` is treated as invalid AI output and
   escalates (it never silently defaults to a passing value). `confidence` is part of the untrusted
   model output and is validated like a score, not trusted.
3. **Unexpected AI-supplied `final_score` is ignored as untrusted, not treated as an error.** It is
   never persisted and never compared against the calculator. All other unexpected keys remain a
   validation error so that a malformed schema still escalates.
4. **Escalation is a resolvable terminal state, not a permanent refusal.** An escalated proposal
   persists with no grade; a teacher may resolve it by supplying the **complete** set of criterion
   scores for every rubric ID **plus** a nonempty reason. `score_calculator` computes the total from
   the accepted scores. No silent numeric default (e.g. zero) is ever inserted. This manual grading
   path applies equally to escalations caused by D4 (low/missing/invalid confidence).
5. **Missing / duplicated / unknown / invalid / low-confidence / provider-failure outcomes** all
   produce an escalation reason and zero durable grade rows. The store re-validates any advice it is
   handed and refuses to persist a grade for invalid advice (`src/grade_store.py:31-48`).<br/>
   Escalation reasons distinguish at least: `uncertain_criterion`, `low_confidence` (D4),
   `invalid_confidence` (D1/D4 malformed), and `invalid_or_unavailable_provider_response`.

## Consequences

- The escalation trigger is deterministic and auditable **except** for D2 (boolean) and the numeric
  value of D4's `confidence`, which is model-emitted self-report. A model that is confidently wrong can
  still pass D4; D4 is a *policy on untrusted data*, not a calibrated probability. This is an accepted,
  documented limit (see risk-list R-03) covered by behavioral evaluation.
- **D4 depends on the provider actually emitting a `confidence` field.** The current `src/` emits
  **none** (grep of `src/` finds no `confidence`), and the existing green test
  `test_valid_feedback_and_request_contract` does not assert a confidence value. Therefore D4 and
  REQ-FUNC-002/003 are **target behavior pending implementation and verification** by A (field +
  threshold branch) and B (tests). Until implemented, only D1–D3 are enforced by the running code.
- Because a human resolves escalated cases, "escalate" cannot be tested only as `ValueError` on
  record (B's current red test). Under this ADR: recording *invalid* advice (including low/invalid
  confidence) still raises; a *resolved* escalated proposal is allowed. **B must update the test
  through a tests-only PR** to assert: invalid/low-confidence advice → refusal; escalated-but-resolved
  → grade with calculator total and reason in audit.
- `final_score` handling changes A's current behavior (`:152`), so a benign provider total no longer
  forces an escalation.
- The `0.80` threshold is a **hardcoded policy constant from C's draft**. Its value is not yet shown to
  be optimal; it may cause false escalations on correct advice or miss unsafe advice. See below.

## Alternatives considered

| Alt | Benefit | Cost | Outcome |
|---|---|---|---|
| A-only (boolean `uncertain`, reject extra keys) | Simple, no arbitrary cutoff | No numeric signal; misses confidently-wrong; conflicts with C draft | Rejected as the sole rule |
| **C draft: `confidence ≥ 0.80` required + boolean + provider failures (this revision)** | Meets REQ-FUNC-002/003/008; deterministic numeric gate; both triggers testable | 0.80 unvalidated; relies on model self-report; changes A | **Adopted (aligned with C 0.1.0-c)** |
| Hybrid without confidence (prior D2 baseline) | No unmeasured constant | Does not satisfy C's REQ-FUNC-002/003 | Superseded by this revision |
| Escalate = permanent refusal (no grade ever) | Strongest "no AI grade" stance | Blocks legitimate human grading of hard cases; contradicts team decision | Rejected by product decision |

## Threshold source and candidate evidence (effectiveness not yet evaluated)

- **Threshold `0.80` is specified by C's draft requirements baseline 0.1.0-c** (REQ-FUNC-003:
  "confidence of at least 0.80"). D adopts the value verbatim; D did **not** invent or measure it.
- **Its effectiveness has yet to be evaluated.** Evidence that would validate or revise the constant:
  1. A fixed, versioned real-model evaluation set (≥ 30 cases incl. borderline essays and adversarial
     prompts) where **false-escalation rate** (escalated but human accepted the advice unchanged) vs
     **unsafe-pass rate** (passed but human materially changed a score) are measured across at least
     two thresholds.
  2. A chosen threshold on the unsafe-pass/false-escalation curve that yields **unsafe-pass = 0** on
     the set while keeping false-escalation within the teacher's tolerance.
  3. Demonstration that the provider emits a consistent `confidence` field (schema-valid, `[0, 1]`) —
     i.e. the field is contractual, not hallucinated.
  4. Re-run on any model/prompt change (behavioral tier, `REQ-GOV-B04`).
- Until (1)–(4) exist, 0.80 is a **policy choice from C's draft whose effectiveness is unproven**, not a
  validated calibration. It is nonetheless the required architecture behavior for this baseline.

## Verification

- Existing: `test/offline/test_feedback.py` (uncertain/null escalation, provider/refusal/cap
  escalations), `test/offline/test_store.py::test_escalation_requires_every_score_and_reason`
  (escalation needs full scores + reason), `test_store.py::test_state_corruption_cannot_bypass_escalation_review`
  (status tamper refused).
- Contract-target: `test/offline/test_authority_boundary.py::test_invalid_advice_escalates`
  (negative; currently red because API differs) — each mutation variant (missing/unknown/duplicate/
  low_confidence/uncertain/bad_score) must yield decision `escalate`, `scores is None`, zero records.
  **Under this revision `low_confidence` (0.79) is now a mandatory variant, not a deferred one.**
- `test_prompt_injection_stays_advisory`: hostile feedback text and `final_score="100000"` must not
  change scores and must not create files.

### Planned tests for the confidence rule (owned by B, implemented against A's code; tests-only PR)

These are **target tests not yet present**. Each asserts escalation (`decision == "escalate"`,
`scores is None`, zero durable rows) unless stated otherwise:

1. **`test_missing_confidence_escalates`** — a criterion omitting the `confidence` field → escalate
   (reason `invalid_confidence`). Also cover `confidence: null` and a non-numeric/boolean value.
2. **`test_invalid_confidence_escalates`** — `confidence` = `"NaN"`, `"Infinity"`, `-0.1`, `1.1`,
   `true`, or a non-numeric string → escalate (out of `[0,1]` or wrong type).
3. **`test_confidence_079_escalates`** — a criterion with `confidence: 0.79` → escalate
   (reason `low_confidence`, D4).
4. **`test_confidence_exactly_080_passes_confidence_check`** — every criterion at exactly `0.80` and
   all other rules satisfied → `decision == "ready"` (the boundary is inclusive: 0.80 passes; only
   `< 0.80` fails). *Control case proving the threshold is not off by one.*
5. **`test_confidence_pass_but_other_rule_fails_escalates`** — all confidences exactly `0.80` but a
   *different* rule is violated (unknown criterion ID, out-of-range score, missing criterion,
   non-substring evidence quote, or `uncertain: true`) → still escalate. Proves passing the confidence
   check never waives D1/D2.

- Mutation coverage (tier 2): removing the D1/D2/D4 checks — or flipping `confidence < 0.80` to
  `<= 0.80` (which would wrongly fail 0.80) — must make the relevant test fail.

## Reopening conditions

- Behavioral evaluation (threshold-source evidence above) shows 0.80 causes unacceptable
  false-escalation or unsafe-pass → revise the constant or add calibration (would amend C's draft).
- The provider schema cannot reliably emit `confidence` in `[0,1]` → revisit D4 or the provider choice.
- The product decides escalated cases are *not* resolvable into grades (reverses decision 4).
- A provider schema makes `uncertain`/`final_score` mandatory or inexpressible in the current shape.
