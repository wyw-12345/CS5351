# GradeAide — Architecture Blueprint (D2)

> Owner: Member D (software architecture). Status: **D2 baseline**.
> Baseline under review: the merged A/B/E package (`src/`, `docs/member-b/`, `docs/member-e/`,
> `tools/`, `test/`). This document records the architecture for the current release. It does
> **not** claim that any proposed requirement ID is final; C's formal registry is still pending.
>
> One boundary is fixed for every decision below:
>
> > **AI is advisory; deterministic code is authoritative.**
> > `feedback_engine` proposes. `score_calculator` decides. `grade_store` persists only after an
> > explicit, bound human approval. The AI never overrides a deterministic score.

Companion artifacts (all under `docs/architecture/`): `adr/ADR-0001..0004`,
`invariants.md`, `trace-matrix.md`, `memory-design.md`, `permission-model.md`,
`runtime-policy-catalog.md`, `evaluation-table.md`, `evaluation-logbook.md`, `risk-list.md`,
`option-ledger.md`.

---

## 1. Scope

GradeAide grades one student essay against a teacher-supplied rubric:

1. Import an essay (text) and a rubric (criteria × weights) — `src/cli.py`, `src/contracts.py`.
2. **Advisory AI** (`src/feedback_engine.py`) reads essay + rubric and returns per-criterion
   feedback plus *suggested* scores and a quoted evidence span. Advisory only.
3. **Deterministic calculator** (`src/score_calculator.py`) weights the human-accepted scores and
   computes the *final* percentage. Authoritative. Frozen.
4. **Grade store** (`src/grade_store.py`) recomputes the score, checks an explicit approval bound to
   the exact proposal, and atomically persists the grade plus an audit record. Authoritative write.
5. **Human boundary** (`src/cli.py`) is a trusted local teacher command line. Reviewer identity is an
   audit label in this release; authenticated multi-user approval is a reopening condition
   (ADR-0002).

Out of scope for this baseline: multi-user hosting, web UI, retrieval/RAG, training or calibration,
cross-essay memory, and long-text chunking (deferred to a future ADR — ADR-0004, `memory-design.md`).

## 2. Architecturally Significant Requirements (ASR)

| ID (candidate) | Statement | Why architecturally significant |
|---|---|---|
| REQ-INV-001 | Persisted score equals deterministic calculator output; model totals never override. | Forces the advisory/authoritative split into modules. |
| REQ-INV-002 | Missing/duplicate/unknown/uncertain advice escalates with no silent numeric default. | Defines the escalation policy and failure surface (ADR-0001). |
| REQ-INV-003 | No grade persisted without explicit human approval bound to the exact submission, rubric and advice. | Defines the approval binding (ADR-0002). |
| REQ-INV-004 | Invalid/non-finite/boolean inputs rejected before calculating or writing. | Forces strict validation at every boundary. |
| REQ-INV-005 | Deterministic Decimal percentage, rounded once to two places, ROUND_HALF_UP. | Forces exact arithmetic and a fixed formula. |
| REQ-INV-006 | Every persisted record keeps advisory scores, authoritative score, digests and reviewer identity. | Defines the audit record and atomic write. |
| REQ-INV-007 | Advisory component has no write authority and cannot execute injected text. | Forces import boundaries and untrusted-data handling. |
| REQ-INV-008 | Idempotent retry; conflicting same-ID content rejected without overwriting. | Defines submission identity and transaction semantics. |
| REQ-SEC-002, 004, 006, 007 | No fabricated criteria; no secrets in repo; least privilege; unambiguous bounded import. | Constrains configuration injection and runtime policy. |
| REQ-COST-001..005 | Bounded invocation, byte budget, cost preflight, honest usage, over-limit escalation. | Constrains the LLM pipeline and memory design (ADR-0004). |
| REQ-GOV-B01..B06, GOV-E01..E04, GOV-C01..C02 | Test-approval, static gates, semantic eval, idempotent logs, default-deny permissions, registry co-evolution. | Constrains how the architecture is verified and changed. |
| REQ-QUAL-001..005, REQ-FUNC-001..010 | Modifiability, auditability, offline determinism, reproducibility, hash-only audit; grading workflow. | C's functional/quality baseline for the ASR. |

> IDs above now use **C's formal registry** (`docs/req/requirements.yaml`, baseline 0.1.0-c, 47
> entries). C's `requirement-id-map.yaml` resolved the earlier A/B/E collisions (E `REQ-SEC-001`/`005`
> merged into `REQ-INV-007`, E `REQ-SEC-003` merged into `REQ-INV-003`). **The C baseline is
> `draft_ready`, pending human review** (no signatures). **Both previously-open architecture decision
> conflicts are now resolved in line with C's draft** and are recorded in ADR-0001 (0.80 confidence) and
> ADR-0002 (verified signing approval); their implementation is pending. The full 47-entry mapping is in
> `trace-matrix.md`.

## 3. Components and authority

| Component | Module | Authority | Hard limits |
|---|---|---|---|
| AI feedbacker | `src/feedback_engine.py` | advisory | no grade-store write; no `os`/`subprocess`/`pathlib`/`importlib`/`shutil`/`builtins`; model text is untrusted data |
| Deterministic calculator | `src/score_calculator.py` | authoritative | **frozen**; rational/Decimal only; no LLM/network/filesystem/dynamic import |
| Grade store | `src/grade_store.py` | authoritative write | writes only after approval validation; atomic; audit-complete |
| Human boundary | `src/cli.py` | orchestration | filesystem import; prints escaped JSON; never echoes secrets |
| Shared contracts | `src/contracts.py` | validation helper (non-authority) | strict JSON/Decimal/text validation |

The advisory/authoritative boundary is encoded as an import rule and enforced by
`tools/gates.py safety` (see `permission-model.md` §4).

## 4. Data flow

```
essay + rubric ──► contracts.validate ──► feedback_engine.evaluate ──► advice{status,feedback,reason,metadata}
                                                                             │
                     (no grade) ◄── grade_store.create (proposal) ◄──────────┘
                                                                             │
teacher reviews ──► grade_store.approve(proposal, hash, scores, reviewer, reason)
                       │  recompute via score_calculator
                       ▼
               grades row (score + audit) in one transaction
```

## 5. Key architecture decisions (summary; see ADRs)

| ADR | Decision | One-line |
|---|---|---|
| ADR-0001 | Escalation policy | Escalate on deterministic invalid output, explicit model uncertainty, provider failure, **or valid `confidence` missing/invalid/`< 0.80` (0.80 passes)**; an escalated case is resolved by a complete human score set + reason. `0.80` is C's draft threshold; effectiveness unevaluated. |
| ADR-0002 | Approval & binding | Single-teacher CLI with **verified** approval: a **local signing key** (teacher-controlled) signs the binding; the store verifies against a **trusted public key**. Reviewer name is an audit label. Binding covers **submission, proposal, rubric version, and confirmed criterion scores**; rejects unauthorized signers, changed scores, and signature replay; store recomputes and records atomically. Target behavior pending implementation. |
| ADR-0003 | Interface consolidation | Resolve the A/B/E interface differences for API shape, weights, precision, submission identity, duplicate requests, atomic persistence and configuration injection. |
| ADR-0004 | Model context & memory | Layered context, one-pass assembly pipeline; retained 12,000-byte input guard (enforced) plus a token-based context cap (8,000, design target), token counting/estimation method, token-based compaction threshold (6,000, design target), critical-constraint re-injection. |

## 6. Permissions

Default-deny, whitelisted dev surface, ask for shell. Human-owned permission and rule files; no AI
self-granting. Detailed in `permission-model.md`; machine-readable form is
`.opencode/permissions.jsonc` (human-owned, not approved yet).

## 7. Verification

Three tiers — structural (imports, boundaries, permissions), regression (all prior offline suites),
behavioral (fixed real-model set, zero safety escapes) — plus six blocking CI gates. Mapping and
current evidence are in `trace-matrix.md`; metrics in `evaluation-table.md`; the ledger of what was
actually run is `evaluation-logbook.md`. Structural checks and unit tests are an early signal, not
an OS sandbox.

## 8. Monitoring and runtime fallback

Runtime observables per component and concrete fallbacks are in `runtime-policy-catalog.md`. General
posture on an authority/approval/audit violation: stop grade writes, quarantine the attempt, retain a
privacy-safe diagnostic, surface it to the teacher, require manual reconciliation. The test runner
reports failures; it does not claim a notification service exists.

## 9. Change and reopening policy

`score_calculator.py` and `grade_store.py` are frozen / safety-critical: any change needs a new ADR,
updated contract/API/permission snapshots, passing negative tests and an independent human review of
the exact head SHA. Interface changes go through a tests-only PR first. Reopening conditions are
listed in each ADR.

## 10. Known gaps at this baseline (handed to E/A/B)

1. **A's `src/` API ≠ B/E contract.** `src/` exposes `calculate_score`/`evaluate`/`GradeStore` with a
   package-relative import; the B/E acceptance suite (`test/offline/test_authority_boundary.py`)
   imports flat `calculate`/`validate_advice`/`record_grade`, which do not exist. ADR-0003 defines
   the target; **A must implement, B must re-point tests through a tests-only PR.**
2. **Uncertainty trigger.** A uses a boolean `uncertain`; B/E propose `confidence ≥ 0.80`. ADR-0001
   keeps explicit-uncertainty escalation as the rule and treats 0.80 as a candidate; **C must decide
   whether `confidence` is required output and who owns the constant.**
3. **Escalation terminal state.** A lets a human resolve an escalated proposal into a grade; B/E's red
   test asserts recording escalated advice raises. ADR-0001 confirms A's resolvable model; **B's test
   must be reconciled (tests-only PR).**
4. **Submission identity.** A uses a random `proposal_id`; B/E require caller `submission_id` for
   idempotency. ADR-0003 adopts `submission_id` as the canonical key; **A must add it, C must define
   uniqueness.**
5. **Duplicate policy.** A rejects duplicate approval; B/E require idempotent return. ADR-0003 adopts
   idempotent-retry-on-identical-input, conflict-on-different-content.
6. **`final_score` in advice.** A rejects (extra-key); B/E ignore. ADR-0001 chooses *ignore as
   untrusted* (not an error) to avoid punishing a benign provider field, while never persisting it.
7. **Approval verifier.** No `verify_approval` dependency is injected today; the CLI trusts a
   `--reviewer` string. ADR-0002 accepts this for the single-teacher release and specifies the
   verifier seam; **E must provide authenticated verifier injection before multi-user.**
   Separately, ADR-0002 distinguishes **G1** (validation + recomputation of submitted scores) from
   **G2** (binding approval to the *exact confirmed* score set). The current store enforces G1 +
   proposal-hash only; **A must add the `confirmed_scores_sha256` binding and a score-substitution
   negative test**, else R-15.
8. **Config injection.** `feedback_engine` reads `os.environ`; E forbids `os` import. ADR-0003 moves
   configuration to the caller/CLI and passes a validated `Settings` value object into the engine;
   **A must refactor, E must confirm the boundary check.**
9. **Formal requirement registry delivered (0.1.0-c), pending review.** C's `docs/req/requirements.yaml`
   (47 entries) + `requirement-id-map.yaml` now exist; `trace-matrix.md` and `invariants.md` are keyed
   to C's IDs. Remaining: the baseline is `draft_ready` with **no human signature**, and B's test-map /
   test docstrings are not yet re-keyed to C's IDs (traceability gate BLOCKED). Both architecture
   decisions are **resolved and aligned with C's draft** — Decision-1 (0.80 confidence, ADR-0001) and
   Decision-2 (verified signing approval, ADR-0002) — with **implementation and verification pending**.
10. **Confidence field + threshold not implemented.** `src/` emits no `confidence`; A must add the field
    and the `< 0.80` branch, B the five confidence tests (ADR-0001).
11. **Signing approval not implemented.** `src/` has no signature verification and no
    `confirmed_scores_sha256`; A implements, E provisions keys, B adds unauthorized-signer /
    substitution / replay tests (ADR-0002).
12. **Runtime fallback / notification service** is described, not implemented.
