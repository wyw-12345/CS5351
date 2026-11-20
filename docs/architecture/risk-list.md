# Risk list (D2)

> Owner: D. Status: baseline. Likelihood/Impact: L/M/H. Each risk names a mitigation and an owner.

| Risk | Description | L | I | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-01 Requirement-ID collision | **Partially resolved.** C's `requirement-id-map.yaml` (baseline 0.1.0-c) merged the colliding A/B/E proposals (E SEC-001/005→INV-007, E SEC-003→INV-003) and defines 47 formal IDs. Remaining risk: B's `test-map.yaml` and test docstrings do not yet reference C's IDs, so the traceability gate is BLOCKED. | M | H | Trace matrix re-keyed to C IDs (done); B/A add per-test REQ docstrings and remap `test-map.yaml`. | B (primary), A, D | open (registry delivered; test-mapping pending) |
| R-02 Unauthenticated reviewer | `--reviewer` is currently a label with no authentication. **Decided (aligned with C REQ-INV-003):** approval must be verified by a local signing key against a trusted public key (ADR-0002). | M | H | **Implemented target:** ADR-0002 signed approval; A implements, E provisions keys, B tests. | E, A, B | **decided; implementation pending** |
| R-03 Confidently-wrong model | D2 escalation trusts the model's `uncertain` boolean; a confident wrong answer does not escalate. D4 (confidence) is model self-report too, so it also cannot be fully trusted. | M | M | Behavioral eval (adversarial + unsafe-pass); human review before release; 0.80 effectiveness evaluation (ADR-0001). | A/B | open (documented limit) |
| R-04 Interface mismatch A vs B/E | `src/` flat/package API differs from acceptance tests; contract suite red. | H | M | ADR-0003 target API + tests-only PR to re-point; do not fake modules. | A/B | open (known) |
| R-05 Long essays always escalate | No chunking; attempts over the 12 000-byte guard always escalate (false-escalation cost). Token cap (8 000) is unmeasured. | M | M | Documented scope; byte guard retained; compaction ADR + eval if long text becomes Must; validate token estimator. | D/A | accepted |
| R-15 Binding-to-confirmed-scores (G2) not enforced | Current store binds only to proposal hash; no confirmed-scores hash and no signature. **Decided:** explicit `confirmed_scores_sha256` + signing that covers `submission_id`/proposal/rubric version/scores (ADR-0002). | M | H | Implement signed `confirmed_scores_sha256` binding + substitution/replay/unauthorized-signer tests. | A/B | **decided; implementation pending** |
| R-06 Student PII in essays | Essays may contain personal data; sent to provider; evidence quotes persisted. | M | H | Local-only baseline; hashes in external artifacts; no raw essays in CI artifacts; redact errors. | D/E/B | mitigated by policy; needs ops check |
| R-07 Config/secrets | Engine imports `os` and reads env in-module (E violation); risk of secret leakage. | M | H | ADR-0003 move to CLI; secret scan; env-only creds; `.opencode` deny `*.env`. | A/E | open |
| R-08 Atomic-write assumptions unverified | Fault-injection test for atomic persistence not yet written. | M | M | Add fault-injection test against SQLite backend (planned). | B/A | open |
| R-09 Idempotency not implemented | No `submission_id`; duplicate approval currently rejected not idempotent; `REQ-INV-008` unmet. | M | M | ADR-0003 schema v2 + idempotency; `test_retry_is_idempotent`. | A | open |
| R-10 Runtime fallback not implemented | Notification/quarantine on violation described, not built. | M | M | E/B implement notification+quarantine; keep fallback documented. | E/B | open |
| R-11 Static-checks-as-sandbox | Import gates are early signal only; no OS sandbox of advisory component. | M | H | E provides process/filesystem isolation. | E | open |
| R-12 Evidence inflation | Risk of citing synthetic/live-deferred results as real quality evidence. | L | H | `evaluation-logbook.md` status labels; no pass claims for unrun checks. | D/B | controlled |
| R-13 Frozen-calculator divergence | E's "Decimal only" wording excludes `fractions`; conflicting with exact rounding. | M | M | D directs E to allow `fractions` (ADR-0003). | E | open (resolving) |
| R-14 Approval binding gaps | Rubric-version explicit check and altered-scores test not yet present. | M | H | ADR-0002 binding fields + new negative test. | A/B | open |
| R-16 Confidence contract unrealized | C's REQ-FUNC-002 requires a `confidence` field and REQ-FUNC-003/008 require `confidence ≥ 0.80`; `src/` emits no confidence. **Decided (aligned with C):** require valid confidence per criterion; escalate if missing/invalid/`< 0.80` (0.80 passes). 0.80 effectiveness still unevaluated. | M | H | ADR-0001: A adds field + threshold branch; B adds the five confidence tests; effectiveness evaluation planned (E9). | A, B, D | **decided; implementation pending** |
| R-17 REQ-QUAL-005 assertion missing | C notes the audit "no second essay copy" claim is not explicitly asserted; `test_audit_records_both_sources` only checks fields. | M | M | B/A add absence-of-second-essay-copy assertion. | B/A | open |

## Decisions resolved (aligned with C's draft 0.1.0-c)

- **Decision-1** (0.80 confidence, R-16): resolved in ADR-0001 — required, validated, `>= 0.80`
  (0.80 passes), effectiveness unevaluated. Implementation pending.
- **Decision-2** (verified approval, R-02/R-15): resolved in ADR-0002 — local signing key, trusted
  public-key verification, binding to submission/proposal/rubric version/confirmed scores.
  Implementation pending.

No open user decisions remain; both are recorded as architecture decisions aligned with C's draft.

## Baseline review status

C's requirements registry **0.1.0-c (47 entries)** is `draft_ready`, **pending human review** (no
signatures). Do not cite this risk list or the trace matrix as an approved baseline.
