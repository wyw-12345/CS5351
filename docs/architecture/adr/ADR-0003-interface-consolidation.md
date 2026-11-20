# ADR-0003 — Interface consolidation for the baseline

- Status: Accepted (D2 baseline)
- Date: 2026-11-11
- Relates: every row of `handoff/A-B-E-接口差异与待决事项.md` except escalation (ADR-0001) and
  approval (ADR-0002). Authoritative for `docs/member-b/02-interface-contract.md` review: **accepted
  with modifications listed below.**
- Owner: D. Consumers: A (implementation), B (tests, snapshots), E (gates, permissions).

> D's review of `docs/member-b/02-interface-contract.md`: **ACCEPTED WITH MODIFICATIONS.** The
> B/E contract is a reasonable target, but the working baseline is A's `src/` API with
> package-relative imports (`from .contracts import …`). Rather than fork, this ADR defines one target
> API and the migration. Function-name/shape decisions below are binding once a human reviews this ADR.

## Decision summary

| Topic | Decision | Rationale | Compatibility | Verification | Reopen if |
|---|---|---|---|---|---|
| **API shape & imports** | Keep A's **package-relative** layout (`src` is a package). Public surface: `score_calculator.calculate_score`, `feedback_engine.evaluate`, `feedback_engine.validate_feedback`, `grade_store.GradeStore.{create,approve,get}`, `contracts.*`. Provide B/E-compatible thin aliases `calculate` / `validate_advice` / `record_grade` **only** if B insists, in a tests-only PR; do not duplicate logic. | A's code runs today; a flat-module rewrite is churn. The B/E tests insert `src` on `sys.path` and import flat names — A must expose them or B must re-point tests. | Breaking for B/E tests until reconciled | import-map check in `tools/gates.py safety`; `api-surface.json` snapshot | A wants a different package layout, or B's tests cannot be re-pointed |
| **Rubric shape & weights** | Rubric = `{id, version, criteria:[{id, description, max_score, weight}]}` (A). Weights **strictly positive**, sum **exactly 1** (Decimal), reject zero-weight criteria. Reject if C later requires zero-weight. | A already enforces (`contracts.py:82-108`); zero-weight criteria contribute 0 and hide scoring errors. | B/E allow zero weight → B/E `test_invalid_numeric_inputs_rejected` "weight 0.5 for 2 criteria" case must expect rejection | `test_calculator` weight/duplicate/max tests; contract `test_invalid_numeric_inputs_rejected` (but see conflict note) | C mandates optional/zero-weight criteria |
| **Score precision & rounding** | Accept **bounded decimal strings** only (`contracts.decimal_value` regex, ≤6 int / ≤6 frac digits). Accumulate **exactly** (A uses `Fraction`), **round once** at the final cent, nonnegative **ROUND_HALF_UP**, output a 2-dp string. Do **not** use intermediate `Decimal` division. | A-ADR-001 discovered `50.005` → Decimal gave `50.00`, exact gives `50.01` (`score_calculator.py:13-19`). Fraction is provably exact for finite decimals. | E's "Decimal only, import list" refers to *no float/LLM*; `fractions` is deterministic and allowed by D. **D overrides E's literal Decimal-only wording for the calculator.** | Golden `50.005`→`50.01`, `66.665`→`66.67`, 68.00; 20× repeatability; `test_exact_weighted_score` | A simpler provably-exact method appears, or C changes rounding/quantum |
| **Submission identity** | Canonical key = **`submission_id`** (caller-supplied stable string). Keep A's random `proposal_id` as the **internal** proposal primary key but add `submission_id` column and enforce uniqueness. | Needed for idempotency (`REQ-INV-008`) and for B/E binding. | A currently has no `submission_id`; schema v1 → v2 additive migration needed | red `test_retry_is_idempotent`; new migration test | C defines a different external key |
| **Duplicate requests** | Identical `submission_id` **and identical content** (essay+rubric+advice digests) → **idempotent return** of the existing record, even after approval. Same `submission_id`, **different** content → `ValueError`, original preserved. | Reconciles A (currently rejects duplicate approval, `:165`) and B/E (idempotent, `:23`). | Changes A's `approve` duplicate behavior | `test_retry_is_idempotent`, `test_duplicate_approval_cannot_overwrite_history` | C requires reject-on-any-duplicate (idempotency not wanted) |
| **Atomic persistence** | Single SQLite transaction (`BEGIN IMMEDIATE`), rollback on failure, read-time digest re-verification, additive schema versioning, no destructive migration. | A already does this (`grade_store.py:54-88,162-178`) and it satisfies "atomic" without external infra. | none | restart test, corruption/tamper tests (`test_store.py:80-105`); fault-injection test to be added | Concurrency/multi-writer or non-SQLite backend required |
| **Configuration injection** | `feedback_engine` **must not import `os`**. Configuration is read at the **caller/CLI** boundary (`src/cli.py`) into a validated `Settings` value object and passed into `evaluate`. Secrets come from the runtime environment at that boundary only. | E forbids `os` in the engine (`structural-constraints.md:40`); current `feedback_engine.Settings.from_env()` (`:44-64`) imports `os` and violates it. | Breaking: A must move `from_env` out of the engine | `tools/gates.py safety` forbids `os` in engine; env/secrets tests | C requires in-engine config, or E relaxes the import rule |

## Notes that resolve the A/B/E discrepancy rows

- **Rubric zero weights:** `handoff` says "B/E allow zero weight; A positive". D chooses **positive**.
  Consequence: B's `test_invalid_numeric_inputs_rejected` sets `weight="0.5"` on a 2-criterion rubric
  and expects rejection (correct under sum≠1), which stays valid; no test needs to *accept* zero.
- **Model output / `final_score`:** see ADR-0001 (ignore untrusted total).
- **Injection handling:** minimal baseline keeps A's "valid feedback may become `pending_review`"; the
  *specific* adversarial set must escalate at the **behavioral/instruction** level via the validator and
  the fixed adversarial case (`test/live/fixed-cases.json`), not by string-matching feedback text.
- **Precise scoring import list:** D notes `fractions` is allowed; E's `structural-constraints.md:43`
  literally lists `decimal/typing/dataclasses/__future__/collections` — **D directs E to add
  `fractions`** to the calculator allowlist (E owns the file).
- **Requirement IDs:** C owns the merge; until then use source-qualified IDs (`trace-matrix.md`).

## Consequences

- A must: (a) add `submission_id` + schema v2, (b) move config injection to the CLI, (c) implement
  idempotent-retry / conflict-on-different-content, (d) add explicit rubric-version check in approve,
  (e) expose B/E-compatible names **or** B re-points tests. None may be done by editing existing tests
  in an implementation PR.
- B must: re-point the red acceptance suite to the agreed API (tests-only PR), add fault-injection and
  altered-scores tests, update `api-surface.json`/`permissions-snapshot.json`.
- E must: add `fractions` to the calculator allowlist; ensure `os` is forbidden in `feedback_engine`;
  verify config injection boundary.

## Verification approach (consolidated)

- Structural: import-boundary gate (`tools/gates.py safety`) + `api-surface.json`.
- Regression: all `test/offline` suites after A's refactor, plus new migration/idempotency/fault tests.
- Behavioral: no change to the model path except config injection; re-run fixed adversarial set.
