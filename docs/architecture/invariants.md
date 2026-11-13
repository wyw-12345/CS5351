# Invariant register (D2)

> Owner: D. Status: baseline **aligned to C requirement registry v0.1.0-c (2026-11-12)**.
>
> - IDs in the "C REQ" column are C's **formal registry** IDs (`docs/req/requirements.yaml`). The
>   registry baseline is **`draft_ready`, pending human review** (C `requirements-review-record.md`
>   §6 shows no signatures). This register is a machine-assisted D draft, not an approved baseline.
> - C's ID map merged the earlier colliding proposals: E `REQ-SEC-001`→`REQ-INV-007`,
>   E `REQ-SEC-003`→`REQ-INV-003`, E `REQ-SEC-005`→`REQ-INV-007`. The old source-qualified IDs are no
>   longer used here; see `trace-matrix.md` for the historical note.
> - **Both previously-open decisions are resolved in line with C's draft** (see `trace-matrix.md`):
>   Decision-1 — confidence is required/validated/`>= 0.80` (ADR-0001, affects INV-02); Decision-2 —
>   verified local signing approval (ADR-0002, affects INV-03). Implementation is **pending**; the
>   invariants below record the target plus the current-code gap.
>
> Each invariant records: C REQ, enforcing component, verification method, runtime monitor /
> observable signal, and concrete fallback. Legend for **Evidence**: `existing` = test/code present in
> the merged workspace and expected to pass against `src/`; `planned` = check that must be added;
> `red` = test present but currently fails against A's API (integration gap); `external` = evidence
> only in C's package.

| INV | C REQ | Statement | Enforcing component | Verification method | Runtime monitor / observable | Fallback | Evidence |
|---|---|---|---|---|---|---|---|
| INV-01 | REQ-INV-001 | Persisted score equals deterministic calculator output; AI total never overrides. | `score_calculator`, `grade_store.approve` | Golden 72.00; recompute-and-compare on read; model-total-override negative | `score` == `calculate_score(rubric, accepted_scores)`; advice `final_score` ignored | Refuse write; integrity error on read | existing (`test_store`, `test_calculator`); red `test_model_total_cannot_override` |
| INV-02 | REQ-INV-002, **REQ-FUNC-003/008 (0.80 — Decision-1)** | Missing/dup/unknown/uncertain advice escalates; no silent numeric default. **Confidence is required per criterion; escalate if missing/invalid/`< 0.80` (0.80 passes).** | `feedback_engine.validate_feedback`, `grade_store._validate_advice` | Mutation matrix (missing/unknown/duplicate/uncertain/bad_score) → escalate; **confidence tests (planned): missing, invalid, 0.79, exactly 0.80, confidence-pass-but-other-rule-fails** | advice `status/reason` (`low_confidence`/`invalid_confidence`), zero grade rows | Escalate; teacher resolves via manual grading path | existing (`test_feedback`) for uncertain; red `test_invalid_advice_escalates`; **0.80 branch + tests planned (target behavior)** |
| INV-03 | REQ-INV-003 | No grade persisted without **verified teacher approval** (local signing key) bound to exact submission, proposal, rubric version and **confirmed criterion scores (G2)**. | `grade_store.approve` (trusted public-key verify, ADR-0002) | Unauthorized signer / changed scores / replay / stale → `PermissionError`/`ValueError`, no state change; substitution + replay + unauthorized-signer tests (planned) | audit `reviewer` label + verified key id + `proposal_hash` + `submission_id` + rubric version + `confirmed_scores_sha256` | Refuse + rollback + surface to teacher | existing (`test_store`, proposal-hash only, no auth); red `test_unapproved_write_is_rejected`; signing tests **planned (target behavior)** |
| INV-04 | REQ-INV-004 | Non-finite/boolean/invalid-range/mismatched-numeric inputs rejected before calc/write. | `contracts` (`decimal_value`, `validate_rubric`, `validate_scores`) | NaN/Inf/bool/negative/over-max/dup-id negative matrix | `ValidationError`; no record | Refuse input; no calculation | existing (`test_calculator`); red `test_invalid_numeric_inputs_rejected` |
| INV-05 | REQ-INV-005 | Deterministic percentage, rounded once to 2dp, HALF_UP, exact accumulation; no intermediate rounding. | `score_calculator` (Fraction + integer half-up) | `50.005`→`50.01`, `66.665`→`66.67`, repeatability, no input mutation | 2dp string; identical across 20 runs | Refuse (validation); never approximate | existing (`test_calculator`); red `test_exact_weighted_score` |
| INV-06 | REQ-INV-006 | Persisted record keeps advisory scores, final score, essay/rubric/advice digests, reviewer identity. | `grade_store` audit | Audit completeness test; digest mismatch detection | audit row fields; read-time digest check | Integrity error; no partial read | existing (`test_store`); red `test_audit_records_both_sources` |
| INV-07 | REQ-INV-007 | Advisory has no write authority and cannot execute injected model text (absorbs E SEC-001/005). | `feedback_engine` import boundary + untrusted-data parsing; gate | Static import gate; hostile-text side-effect test | no files; no store import; scores unchanged | Escalate/ignore hostile instructions | existing (`test_feedback`, `test_governance`); red `test_prompt_injection_stays_advisory` |
| INV-08 | REQ-INV-008 | Idempotent retry on identical input; conflicting same-ID content rejected without overwrite. | `grade_store` (+ `submission_id`, ADR-0003) | Retry twice → one record; different content same ID → `ValueError` | one record per `submission_id`; original preserved | Reject conflict; keep original | red `test_retry_is_idempotent` (current code rejects, not idempotent); **`submission_id` planned** |

> **Non-invariant D concerns folded in earlier INV-09..INV-13** are now traced directly to C's registry
> in `trace-matrix.md`: INV-09 (feedback shape) → REQ-FUNC-002; INV-10 (calc least privilege) →
> REQ-SEC-006/REQ-QUAL-001; INV-11 (secrets/config) → REQ-SEC-004; INV-12 (cost bounds) →
> REQ-COST-001..005; INV-13 (perf) → REQ-PERF-001..003. C defines exactly **eight** invariants
> (REQ-INV-001..008); the extra D rows were non-invariant controls and are represented by the
> corresponding FUNC/QUAL/PEF/COST/SEC registry entries.

## Notes on invariant independence (mutation coverage)

Tier-2 verification requires that each invariant **fails when its enforcement is removed**
(`verification-constraints.md`). Current status:

| INV | Mutation target | Status |
|---|---|---|
| INV-01 | remove recompute/compare in `grade_store.get`/`approve` | existing coverage; confirm mutant killed |
| INV-02 | remove uncertainty/escalation branch, or set threshold `<= 0.80` (kills the 0.80-pass case) | existing for D2; **0.80 mutation planned with D4 tests** |
| INV-03 | remove hash/approval check, signature verification, or confirmed-scores check | existing for hash; signing mutants **planned with ADR-0002 tests** |
| INV-05 | swap Fraction for intermediate Decimal | existing A-ADR-001 evidence |
| INV-07 | allow `grade_store` import in engine | gate self-test exists |
| INV-02 | remove confidence / set threshold `<= 0.80` (fails the 0.80 pass case) | planned with D4 tests |
| INV-03 | remove signature verification / confirmed-scores check / submission binding | planned with signing tests |
| INV-08 | remove idempotency/conflict check | **missing** — must be added with `submission_id` |

## Cross-dependency

- INV-02 depends on **Decision-1** (ADR-0001): A adds a required `confidence` field and the `< 0.80`
  threshold branch; B adds the five confidence tests. Aligned with C's draft.
- INV-03 depends on **Decision-2** (ADR-0002): A implements local signing + trusted public-key
  verification + `confirmed_scores_sha256` binding; E provides key provisioning; B adds the tests.
  Aligned with C's draft.
- INV-03 also depends on ADR-0003 (`submission_id` in the signed binding).
- INV-08 depends on ADR-0003 (`submission_id` schema v2 + idempotent-return path).

## Baseline status

C's registry v0.1.0-c (47 entries) is **`draft_ready`, pending human review** (no signatures in
`requirements-review-record.md` §6). This register is D's machine-assisted draft against C's IDs; it
must be human-reviewed together with the trace matrix before it is treated as the approved baseline.
Both architecture decisions are recorded as **aligned with C's draft**; their implementation is pending.
