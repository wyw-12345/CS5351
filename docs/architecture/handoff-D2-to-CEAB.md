# D2 handoff note (D → C, E, A, B)

Date: 2026-11-12
Author: Member D (software architecture)
Basis: C requirements baseline **0.1.0-c** (47 entries), delivered 2026-11-12.
Status: D2 architecture decisions **resolved and aligned with C's draft**. C's baseline remains
**`draft_ready`, pending human review** (no signatures). No source code, tests, or C's registry were
changed in this round.

## Decisions (both aligned with C's draft)

- **Decision-1 — Confidence and escalation** (REQ-FUNC-002, REQ-FUNC-003, REQ-FUNC-008 → **ADR-0001**
  revised): every rubric criterion must carry a valid `confidence`; escalate if it is **missing**,
  **invalid** (non-numeric, boolean, NaN/Inf, outside `[0,1]`), or **below `0.80`**. A confidence of
  **exactly `0.80` passes** (`< 0.80` escalates). All other validation/escalation rules still apply.
  `0.80` is **C's threshold**; its effectiveness is **not yet evaluated**. The manual grading path for
  escalated cases is preserved (teacher enters full scores + reason; calculator computes total).
- **Decision-2 — Authenticated human approval** (REQ-FUNC-005, REQ-INV-003 → **ADR-0002** revised):
  within the single-teacher CLI, approval is **verified** by a **local signing key** (teacher-controlled,
  stored outside the repo); the store verifies the signature against a **trusted public key**. The
  reviewer *name* stays an **audit label**. The signature binds **submission, proposal, rubric version,
  and teacher-confirmed criterion scores** (`confirmed_scores_sha256 = H(canonical(S*))`). The store
  rejects an **unauthorized signer**, **changed scores**, or a **signature reused for a different
  submission**; on acceptance it **recomputes** the total with the deterministic calculator and
  **atomically records** grade + audit. **Target behavior pending implementation and verification.**

No open user decisions remain. Both are recorded as architecture decisions aligned with C's draft.

## Ownership of follow-ups

### C (requirements)
- Confirm the two decisions are consistent with your intent; **no registry change is required**.
- The registry remains `draft_ready`; keep it pending until a human reviews (D2 mapping is machine-assisted).
- Note for evaluation: `0.80` effectiveness is unevaluated (see ADR-0001); if measurement later suggests
  a different constant, C would be asked to amend REQ-FUNC-003.

### A (implementation)
1. **ADR-0001:** add a required `confidence` field to advice validation; escalate on missing/invalid
   `< 0.80` (0.80 passes); distinct reasons `low_confidence` / `invalid_confidence`. Keep `final_score`
   ignored (per ADR-0001).
2. **ADR-0002:** implement local signature generation in the CLI and verification in `grade_store`
   against a trusted public key; add `confirmed_scores_sha256`, `submission_id`, rubric version to the
   audit; reject unauthorized signer / changed scores / replay; recompute + atomic record.
3. **ADR-0003 (carry-over):** `submission_id` schema v2, idempotent-retry vs conflict, config injection
   out of `feedback_engine` (remove `os`), expose names agreed with B or let B re-point tests.
4. Add the altered-scores-after-approval test hook and rubric-version check.

### B (verification/CI)
1. Add the **five confidence tests** (ADR-0001): missing, invalid, `0.79`, exactly `0.80` (pass),
   confidence-pass-but-other-rule-fails.
2. Add **signing tests** (ADR-0002): `test_unauthorized_signer_is_rejected`,
   `test_score_substitution_between_confirmation_and_recording_is_rejected`,
   `test_signature_replay_onto_other_submission_is_rejected`, altered-scores-after-approval,
   rubric-version-mismatch.
3. Re-point the red `test/offline/test_authority_boundary.py` suite to A's API (tests-only PR); update
   `docs/verification/test-map.yaml` with per-test `REQ-*` docstrings for all 47 IDs (traceability gate
   is currently BLOCKED).
4. Add workspace benchmark/live evidence for REQ-PERF-001/003; add `api-surface.json` /
   `permissions-snapshot.json`; add the REQ-QUAL-005 absence-of-second-essay-copy assertion.

### E (governance)
1. **ADR-0002:** define key provisioning/rotation and the trusted-public-key boundary (keys outside the
   repo; no secret leakage, REQ-SEC-004); default-deny on untrusted keys.
2. **ADR-0003:** add `fractions` to the calculator allowlist; make `os`-in-`feedback_engine` a hard gate
   failure; provide a real secret scan.
3. Provide runtime process/filesystem isolation for the advisory component (static checks are not a
   sandbox); approve `.opencode/rules.md` and verify `permissions.jsonc`.

## Verification gaps remaining

- **Existing evidence:** deterministic calculator, store audit/rollback/restart, feedback provider/
  budget/usage tests (`test/offline/test_calculator.py`, `test_store.py`, `test_feedback.py`,
  `test_http.py`, `test_governance/*`).
- **Red (interface mismatch, ADR-0003):** the B/E acceptance suite uses flat `calculate`/`validate_advice`/
  `record_grade`; A exposes `calculate_score`/`evaluate`/`GradeStore`.
- **Planned, not present:** all confidence tests (ADR-0001); all signing tests (ADR-0002); idempotency
  return; `submission_id` schema; config-injection refactor; workspace perf/live evidence; QUAL-005
  assertion; traceability re-keying.
- **Not implemented:** 0.80 threshold branch; signing/verification; runtime fallback/notification.
- **Effectiveness unevaluated:** 0.80 confidence threshold (needs false-escalation/unsafe-pass curve).

## Documents

`architecture-blueprint.md`; `docs/architecture/adr/ADR-0001..0004`; `invariants.md`; `trace-matrix.md`
(all 47 IDs); `memory-design.md`; `permission-model.md`; `runtime-policy-catalog.md`;
`evaluation-table.md`; `evaluation-logbook.md`; `risk-list.md`; `option-ledger.md`.
