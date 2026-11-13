# Trace matrix (D2) — against C requirement baseline 0.1.0-c

> Owner: D. Status: **baseline reconstructed against C's formal registry v0.1.0-c (47 entries)**.
>
> - Registry source: `docs/req/requirements.yaml` (C, 2026-11-12), delivered in
>   `5351-C/GradeAide-C-需求基线-2026-11-12`. ID decisions: C's `requirement-id-map.yaml`.
> - **Human review status: PENDING.** C's own review record (`requirements-review-record.md`) reports
>   `draft_ready` with **no human signature**; D's mapping below is a machine-assisted draft, not an
>   approved baseline. Do not cite this matrix as "requirements approved".
> - IDs below are C's **formal registry IDs** (not the earlier source-qualified A/B/E IDs). The
>   collision problem is now resolved by C's ID map; the old warning is retained at the bottom for
>   history only.
> - **Both previously-open architecture conflicts are now resolved in line with C's draft** (0.80
>   confidence → ADR-0001; verified signing approval → ADR-0002). See "Architecture decisions — resolved"
>   below. The decisions are recorded as aligned with C's draft; their implementation is **pending**.
>
> Column "Evidence" uses: `existing` = test/evidence present in the merged workspace and expected to
> pass against `src/`; `red` = test present but failing against A's API (integration gap, root cause
> ADR-0003); `planned` = a test or evidence item that must still be added; `external` = evidence that
> lives only in C's package (e.g. `evidence/benchmark.json`) and is not re-run by this workspace.
> Runtime monitor / observable = the signal a running system would emit or record; where none exists
> yet it is marked "planned monitor".

## Coverage summary

| Type | Registry IDs | Count |
|---|---|---|
| functional | REQ-FUNC-001..010 | 10 |
| invariant | REQ-INV-001..008 | 8 |
| quality | REQ-QUAL-001..005 | 5 |
| performance | REQ-PERF-001..003 | 3 |
| cost | REQ-COST-001..005 | 5 |
| governance | REQ-GOV-B01..B06, E01..E04, C01..C02 | 12 |
| security | REQ-SEC-002, 004, 006, 007 | 4 |
| **Total** | | **47** |

Every entry below carries: enforcing component, test/evidence (with status), and runtime monitor /
observable. Planned tests and known integration failures are labelled explicitly.

---

## Functional requirements

| REQ | Statement (short) | Enforcing component | Test / evidence (status) | Runtime monitor / observable |
|---|---|---|---|---|
| REQ-FUNC-001 | Import one UTF-8 essay + rubric (1–10 criteria); reject malformed/oversized/ambiguous/non-finite | `contracts.py` (`read_text`, `parse_json`, `validate_rubric`, `validate_essay`), `cli.py` | `test_calculator::test_invalid_rubric_rejected`, `::test_file_bounds_encoding_and_essay`, `::test_json_duplicates_and_nonfinite_rejected` (**existing**); C lists these exact locators | CLI exit 2 + generic refusal message; proposal stores essay/rubric hashes; no partial DB write |
| REQ-FUNC-002 | Per criterion: advisory text, suggested score, **confidence value**, evidence quote | `feedback_engine` (`evaluate`, `validate_feedback`) | `test_feedback::test_valid_feedback_and_request_contract` (**existing** but **does not assert a `confidence` field**); confidence-emission test (**planned**, ADR-0001) | advice entries per criterion; `evidence_quote` substring of essay; `confidence` in `[0,1]` per criterion |
| REQ-FUNC-003 | Accept advice only if every criterion once, known ID, in-range score, **confidence ≥ 0.80** (0.80 passes), no client final score override | `feedback_engine.validate_feedback`, `grade_store._validate_advice` | `test_feedback::test_reject_final_score_extra_unknown_duplicate_and_missing_criteria`, `::test_uncertain_null_is_an_escalation_not_a_zero_score` (**existing**); **planned (ADR-0001):** `test_missing_confidence_escalates`, `test_invalid_confidence_escalates`, `test_confidence_079_escalates`, `test_confidence_exactly_080_passes_confidence_check`, `test_confidence_pass_but_other_rule_fails_escalates` | advice `status`/`reason` (`low_confidence`/`invalid_confidence`); zero grade rows. **0.80 branch not yet in `src/` (target behavior)** |
| REQ-FUNC-004 | Calculator: exact weighted percentage, one final HALF_UP rounding to 2dp | `score_calculator.calculate_score` | `test_calculator::test_weighted_result_and_bounds`, `::test_exact_half_cent_after_recurring_division`, `::test_different_maxima_rounding_and_external_context` (**existing**) | 2dp string output; deterministic across repeats |
| REQ-FUNC-005 | Proposal creation stores essay/rubric/advice as pending review; never a grade before approval | `grade_store.create` | `test_store::test_proposal_has_no_grade_and_human_change_is_audited` (**existing**); `test_authority_boundary::test_unapproved_write_is_rejected` (**red** — flat API) | proposal `final_score=None`; no `grades` row |
| REQ-FUNC-006 | Approval recomputes score, binds to exact proposal hash, persists immutable audit (reviewer, scores, timestamp, calculator version) | `grade_store.approve` | `test_store::test_missing_approval_details_and_stale_hash_are_rejected`, `::test_failed_audit_insert_rolls_back_status_and_grade`, `::test_escalation_requires_every_score_and_reason` (**existing**) | audit row fields; single transaction; recompute==stored score. **Signed binding + `confirmed_scores_sha256` planned (ADR-0002)** |
| REQ-FUNC-007 | Retrieve pending/approved record showing advisory + authoritative; unknown ID refused; read-only does not create DB | `grade_store.get`, `cli.py` (`show`) | `test_store::test_unknown_id_is_refused` (**existing**); `test_cli::test_missing_database_show_does_not_create_file` (**existing**) | `show` output JSON; no file created when DB absent |
| REQ-FUNC-008 | Missing/dup/unknown/uncertain/**below-threshold**/over-budget/provider-error advice escalates; no invented score/grade | `feedback_engine`, `grade_store._validate_advice` | `test_authority_boundary::test_invalid_advice_escalates` (**red**, now includes mandatory `low_confidence`); `test_feedback::test_input_and_monetary_budget_block_before_transport`, `::test_context_boundary_counts_utf8_bytes` (**existing**); confidence-threshold tests (**planned**, ADR-0001) | escalation reason; zero grade rows; `calls`=0 on budget block. **"below confidence threshold" branch is target behavior (ADR-0001), not yet in `src/`** |
| REQ-FUNC-009 | Idempotent retry of identical approved submission returns original; conflicting same-ID content rejected without overwrite | `grade_store` (needs `submission_id`, ADR-0003) | `test_authority_boundary::test_retry_is_idempotent` (**red**); `test_store::test_duplicate_approval_cannot_overwrite_history` (**existing**, but current code *rejects* duplicate approval, not idempotent return) | one record per submission id; original preserved. **Idempotent-return path is planned** (R-09) |
| REQ-FUNC-010 | CLI operator: create/approve(identity+reason)/show across processes; no hidden network or credential storage | `cli.py` | `test_cli::test_separate_process_restart_approval_and_duplicate_rejection`, `::test_invalid_fixture_envelope_escalates_without_traceback` (**existing**) | process restart preserves record; generic error output; no secret echoed. **Signing CLI path planned (ADR-0002)** |

## Invariant requirements

| REQ | Statement (short) | Enforcing component | Test / evidence (status) | Runtime monitor / observable |
|---|---|---|---|---|
| REQ-INV-001 | Final persisted score == calculator output; model totals never override | `score_calculator`, `grade_store.approve`/`get` | `test_authority_boundary::test_model_total_cannot_override` (**red**); `test_store::test_proposal_has_no_grade_and_human_change_is_audited` (**existing**) | `score` == recompute on read; advice `final_score` never persisted |
| REQ-INV-002 | Missing/dup/unknown/uncertain advice escalates; no numeric grade, no approved persistence | `feedback_engine.validate_feedback`, `grade_store._validate_advice` | `test_authority_boundary::test_invalid_advice_escalates` (**red**); `test_feedback::test_uncertain_null_is_an_escalation_not_a_zero_score` (**existing**) | `status`/`reason`; zero grade rows |
| REQ-INV-003 | No grade without **verified teacher approval** (local signing key) bound to exact submission, proposal, rubric version, and teacher-confirmed criterion scores; client name/flag/bool is not authentication (absorbs E REQ-SEC-003). **Aligned with C 0.1.0-c; target behavior pending implementation** (ADR-0002). | `grade_store.approve` (trusted public-key verify, ADR-0002) | `test_authority_boundary::test_unapproved_write_is_rejected` (**red**); `test_store::test_missing_approval_details_and_stale_hash_are_rejected` (**existing**, proposal-hash only, no auth); **planned (ADR-0002):** `test_unauthorized_signer_is_rejected`, `test_score_substitution_between_confirmation_and_recording_is_rejected`, `test_signature_replay_onto_other_submission_is_rejected` | audit `reviewer` label + verified key id + `confirmed_scores_sha256` + `submission_id` + rubric version; signature verifies against trusted key. **Signing not in `src/` yet (target behavior)** |
| REQ-INV-004 | Reject non-finite/bool numbers, invalid weights, out-of-range scores, dup criteria, mismatched IDs before calc/write | `contracts.py` (`decimal_value`, `validate_rubric`, `validate_scores`) | `test_authority_boundary::test_invalid_numeric_inputs_rejected` (**red**); `test_calculator::test_invalid_scores_rejected` (**existing**) | `ValidationError`; no record |
| REQ-INV-005 | Identical inputs → identical percentage; exact arithmetic, one HALF_UP to 2dp; no intermediate rounding | `score_calculator.calculate_score` (`Fraction` + integer half-up) | `test_authority_boundary::test_exact_weighted_score` (**red**); `test_calculator::test_exact_half_cent_after_recurring_division` (**existing**) | 2dp string; repeatable. Implementation-neutral wording; A=Fraction (ADR-0003 allows `fractions`) |
| REQ-INV-006 | Durable record preserves advisory scores, final score, essay/rubric digests, reviewer; reconstructable after restart | `grade_store` (audit + digest) | `test_authority_boundary::test_audit_records_both_sources` (**red**); `test_store::test_reopen_preserves_exact_record` (**existing**) | audit fields; read-time digest verification; restart preserves record |
| REQ-INV-007 | Advisory component has no grade-store write authority; cannot execute embedded instructions; injection stays advisory (absorbs E REQ-SEC-001, REQ-SEC-005) | `feedback_engine` import boundary; `tools/gates.py safety` | `test_authority_boundary::test_prompt_injection_stays_advisory` (**red**); `test_governance::test_forbidden_feedback_import` (**existing**) | no `grade_store` import; no files created on hostile text |
| REQ-INV-008 | Idempotent retry; conflicting same-ID content rejected without overwrite | `grade_store` (+ `submission_id`) | `test_authority_boundary::test_retry_is_idempotent` (**red**); `test_store::test_duplicate_approval_cannot_overwrite_history` (**existing**, conflict only) | one record per id; original preserved. **Idempotent-return planned** (R-09) |

## Quality requirements (C drafts — D to confirm as ASRs)

| REQ | Statement (short) | Enforcing component | Test / evidence (status) | Runtime monitor / observable |
|---|---|---|---|---|
| REQ-QUAL-001 | Feedback component replaceable without touching calculator/store; no store import or authoritative write | module boundary; `tools/gates.py safety` | `test_cli::test_authority_modules_keep_io_boundaries` (**existing**); `test_governance::test_forbidden_feedback_import` (**existing**) | import set; gate failure on forbidden import. **D confirms as ASR (modifiability)** |
| REQ-QUAL-002 | Every approved grade auditable: reconstruct advisory/authoritative/rubric/essay identity + reviewer after restart | `grade_store` | `test_authority_boundary::test_audit_records_both_sources` (**red**); `test_store::test_reopen_preserves_exact_record` (**existing**) | reconstructable record after restart |
| REQ-QUAL-003 | Offline suite runs without network or API key | test harness; CI offline job | `test/offline` suite; `docs/member-b/VALIDATION.md` (**existing**); C's CI offline job (**external**) | offline job passes with no secret/network; live suite separate |
| REQ-QUAL-004 | Same inputs → same proposal/grade across processes/restarts; reopening preserves exact record/score | `grade_store`; `cli.py` | `test_cli::test_separate_process_restart_approval_and_duplicate_rejection` (**existing**); `test_store::test_reopen_preserves_exact_record` (**existing**) | cross-process record equality; SQLite persistence |
| REQ-QUAL-005 | Durable audit does **not** store a second raw essay copy; essay identified by hash; proposal is only payload with text | `grade_store` audit construction | `test_authority_boundary::test_audit_records_both_sources` — **field check only; absence-of-copy assertion PLANNED** (C notes TBC); see R-17 | audit contains hashes, not essay text; export excludes raw essay. **Verification incomplete** |

## Performance requirements

| REQ | Statement (short) | Enforcing component | Test / evidence (status) | Runtime monitor / observable |
|---|---|---|---|---|
| REQ-PERF-001 | Calculator warm p95 ≤ 10 ms (10-criteria) on documented env | `score_calculator` | `evidence/benchmark.json` + `docs/member-a/verification-results.md` (**external** — not re-run in this workspace); benchmark fixture (**planned** in workspace) | latency percentile artifact; environment recorded |
| REQ-PERF-002 | 30 s default timeout, exactly 0 automatic retries; timeout → escalation | `feedback_engine` transport (`request_json`) | `test_http::test_delayed_header_times_out`, `::test_slow_trickle_is_stopped_by_connected_deadline`, `test_feedback::test_transport_failure_escalates_without_retry_or_secrets` (**existing**) | `latency_ms`, `calls`=1, timeout reason; no retry |
| REQ-PERF-003 | Live p95 ≤ 30 s over ≥ 20 attempts, failures separate | live evaluation harness | `evidence/live-results.json` + `docs/member-a/live-verification.md` (**external, historical**); final deployment run (**planned**) | per-attempt latency + error rate. **Should — provisional** (D/A confirm gate; OQ-003) |

## Cost requirements

| REQ | Statement (short) | Enforcing component | Test / evidence (status) | Runtime monitor / observable |
|---|---|---|---|---|
| REQ-COST-001 | ≤ 1 model request/attempt; default `max_tokens`=1024 | `feedback_engine.evaluate` | `test_feedback::test_valid_feedback_and_request_contract` (**existing**) | request body `max_tokens`; `calls` |
| REQ-COST-002 | Context ≤ 12000 UTF-8 bytes default; overflow → 0 calls | `feedback_engine.evaluate` (`max_input_bytes`) | `test_feedback::test_context_boundary_counts_utf8_bytes`, `::test_input_and_monetary_budget_block_before_transport` (**existing**) | `metadata.input_bytes`; `reason=input_budget_exceeded`; `calls`=0 |
| REQ-COST-003 | Preflight cost vs configured budget with explicit prices; over-budget → 0 calls | `feedback_engine.evaluate` (`_cost`) | `test_feedback::test_input_and_monetary_budget_block_before_transport`, `::test_configuration_rejects_unsafe_endpoints_prices_and_limits` (**existing**) | `estimated_cost`, `max_cost`, `price_source`; `reason=cost_budget_exceeded` |
| REQ-COST-004 | Actual usage, estimate, model identity, elapsed time distinguishable; missing usage unknown not zero | `feedback_engine.evaluate` | `test_feedback::test_missing_or_invalid_usage_never_becomes_zero`, `::test_provider_over_output_cap_escalates_but_usage_survives` (**existing**) | `usage`, `reported_usage_cost`, `provider_model`, `latency_ms`; unknown stays null |
| REQ-COST-005 | Long/over-budget attempts escalate visibly, no truncation, no auto grade, no request | `feedback_engine`; `contracts` size limits | `test_feedback::test_input_and_monetary_budget_block_before_transport`, `test_calculator::test_file_bounds_encoding_and_essay` (**existing**) | `reason`; `calls`=0; original content retained |

## Governance requirements

| REQ | Statement (short) | Enforcing component | Test / evidence (status) | Runtime monitor / observable |
|---|---|---|---|---|
| REQ-GOV-B01 | Test changes need verified independent human approval before implementation; no AI self-approve | `tools/gates.py` test-approval gate | `test_governance::test_approval_requires_human`, `::test_self_approval_rejected` (**existing**) | gate status on PR; approval record |
| REQ-GOV-B02 | Every commit static checks; safety PRs need contract/permission/API/ADR human review | `tools/gates.py` static gate; CI | `test_governance::test_forbidden_feedback_import` (**existing**); `ci.yml` static job (**external**) | CI status; gate failure |
| REQ-GOV-B03 | Registry validates against schema; every fit criterion mapped to a test/evidence | `tools/gates.py schema`; `scripts/validate_requirements.py` | C's `registry-validation.json` (**external**); workspace gate **BLOCKED at traceability** (C handoff §Verification) | gate status: schema PASS, traceability BLOCKED |
| REQ-GOV-B04 | Prompt/model/feedback changes replay fixed real-model eval; block below threshold | `test/governance/test_semantic_eval.py`; CI semantic job | `test_semantic_eval::test_adversarial_non_escalation_fails` (**existing**) | semantic eval artifact; threshold met |
| REQ-GOV-B05 | All prior deterministic suites run every change; test removal needs approved baseline change | `tools/gates.py regression`; CI | `test_governance::test_history_test_change_rejected` (**existing**) | regression job status |
| REQ-GOV-B06 | Every code/prompt/gate change adds AI-use-log entry; history never rewritten | `tools/gates.py ai-log` | `test_governance::test_log_must_cover_changed_paths`, `::test_log_cannot_rewrite_history` (**existing**) | AI-use log entry per change |
| REQ-GOV-E01 | Default-deny permission model; explicit per-path whitelist; no self-grant | `.opencode/permissions.jsonc`; gates | `.opencode/permissions.jsonc` + `permissions-snapshot.json` (**planned by A/B**); `test_governance` (**existing partial**) | permission snapshot bound to implementation; deny by default |
| REQ-GOV-E02 | `score_calculator` frozen; changes need ADR + independent human approval on exact change | branch protection, CODEOWNERS, permissions | branch protection + ADR + CODEOWNERS + deny-edit (**planned**, not yet configured) | protection status; CODEOWNERS review |
| REQ-GOV-E03 | One module per architectural element; extend, never silently replace | `structural-constraints.md`; static boundary check | structural doc (**existing**); static module-boundary check (**planned by A/B**) | module→element map; gate |
| REQ-GOV-E04 | Coding agent may call only manifest tools; role-inappropriate/unlisted denied | `mcp-tool-manifest.md`; `.opencode/permissions.jsonc` | manifest (**existing**); permission role rules (**planned**) | tool-invocation log vs manifest |
| REQ-GOV-C01 | Requirement change updates registry, ID map, traceability, tests, AI-use log together; no orphan | `scripts/validate_requirements.py`; gates | `scripts/validate_requirements.py` (**external**); `tools/gates.py schema`/`ai-log` (**existing partial**) | schema + ai-log gate; ID-map consistency |
| REQ-GOV-C02 | Registry is single source of IDs; only registered IDs referenced | `scripts/validate_requirements.py`; gates schema | **external** validator; workspace gate (**existing partial**) | unregistered reference count |

## Security requirements

| REQ | Statement (short) | Enforcing component | Test / evidence (status) | Runtime monitor / observable |
|---|---|---|---|---|
| REQ-SEC-002 | AI must not invent criteria outside rubric; scores validated against exact IDs+range | `feedback_engine.validate_feedback` | `test_feedback::test_reject_final_score_extra_unknown_duplicate_and_missing_criteria` (**existing**); `test_authority_boundary::test_invalid_advice_escalates` (**red**) | unknown/repeated ID → escalate |
| REQ-SEC-004 | No secret in source/prompts/config/logs/CI; creds from runtime env only | boundary config (cli, planned move), CI secret scan | secret scan (**planned by B**); `.opencode` deny `.env` (**planned**); `test_feedback::test_settings_repr_does_not_disclose_key` (**existing**) | no key in output/logs/artifacts. **`feedback_engine` imports `os` (`:7`) today — E violation** (ADR-0003) |
| REQ-SEC-006 | Calculator least privilege: deterministic arithmetic only; no LLM/network/filesystem/dynamic import | `score_calculator` imports; `tools/gates.py safety` | `test_governance::test_calculator_network_import_rejected` (**existing**); `test_cli::test_authority_modules_keep_io_boundaries` (**existing**) | import set check; gate. **D allows `fractions`** (ADR-0003) |
| REQ-SEC-007 | Imported JSON rejects duplicate keys/non-finite; text valid UTF-8 within byte limit; no ambiguous coerced score | `contracts.py` (`parse_json`, `read_text`) | `test_calculator::test_json_duplicates_and_nonfinite_rejected`, `::test_file_bounds_encoding_and_essay` (**existing**) | `ValidationError`; bounded reads; no coercion |

---

## Architecture decisions — resolved and aligned with C's draft 0.1.0-c

Both previously-open conflicts are now **decided in line with C's draft**. The registry baseline remains
`draft_ready`, **pending human review**; the decisions below are the architecture target, and their code
is **pending implementation and verification**.

### Decision-1 — Confidence and escalation (REQ-FUNC-002, REQ-FUNC-003, REQ-FUNC-008 → ADR-0001)

- **Adopted:** every rubric criterion must carry a valid `confidence` value; escalate if it is missing,
  invalid (non-numeric, boolean, NaN/Inf, outside `[0,1]`), or **below `0.80`**. A confidence of **exactly
  `0.80` passes** (`< 0.80` escalates; `== 0.80` does not). All other validation/escalation rules still
  apply independently.
- **Threshold source:** `0.80` is specified by C's draft (REQ-FUNC-003). **Its effectiveness has not been
  evaluated**; ADR-0001 records the evidence needed (false-escalation vs unsafe-pass curve).
- **Code status:** `src/feedback_engine.py` emits **no `confidence` field today**; the existing green
  `test_valid_feedback_and_request_contract` does not assert one. D-1 is **target behavior**; A
  implements the field + threshold, B adds the planned tests (missing/invalid confidence, 0.79, exactly
  0.80, confidence-pass-but-other-rule-fails). The manual grading path for escalated cases is preserved.

### Decision-2 — Authenticated human approval (REQ-FUNC-005, REQ-INV-003 → ADR-0002)

- **Adopted:** approval must be **verified** by a signature from an authorized teacher's **local signing
  key**; the store verifies against a **trusted public key**. The reviewer *name* is an **audit label**;
  the identity proof is the verified signature. Single-teacher CLI scope retained; multi-user token
  service stays out of scope.
- **Binding:** the signature covers
  `(submission_id, proposal_hash, rubric_id, rubric_version, confirmed_scores_sha256)` with
  `confirmed_scores_sha256 = H(canonical(S*))` — binding approval to the exact submission, proposal,
  rubric version, and teacher-confirmed criterion scores.
- **Reject rules:** unauthorized signer (key not in allowlist / bad signature) → `PermissionError`, zero
  writes; changed scores (`H(canonical(S')) != confirmed_scores_sha256`) → reject; signature reused for a
  different submission (`submission_id`/`proposal_hash`/`rubric_version` mismatch) → reject.
- **On acceptance:** the store verifies the signature, verifies the binding, **recomputes the total with
  `score_calculator`**, and **atomically records** grade + audit.
- **Code status:** `src/` has **no signing today** (free-text `--reviewer`, proposal-hash binding only).
  D-2 is **target behavior pending implementation and verification**; the signing tests
  (`test_unauthorized_signer_is_rejected`, `test_score_substitution_between_confirmation_and_recording_is_rejected`,
  `test_signature_replay_onto_other_submission_is_rejected`) are planned.

> Relationship to C's registry: both decisions are **aligned with C's draft and do not require C to
> change any requirement**. R-02 and R-16 in `risk-list.md` are updated from "open conflict" to
> "decided; implementation pending".

---

## Historical note — old source-qualified ID collisions (now resolved by C's ID map)

C's `requirement-id-map.yaml` merged the previously colliding IDs: E `REQ-SEC-001`→`REQ-INV-007`,
E `REQ-SEC-003`→`REQ-INV-003`, E `REQ-SEC-005`→`REQ-INV-007`. The pre-C mapping (`B:REQ-INV-004` =
invalid numeric input, etc.) is superseded; rows above use C's formal IDs only.

## Pending formal-mapping / evidence actions

1. **B** must re-point the red acceptance suite (`test_authority_boundary.py`) to A's API (ADR-0003,
   tests-only PR); then all `red` rows become `existing`. Until then REQ-FUNC-005/008/009, all eight
   REQ-INV, REQ-QUAL-001/002, REQ-SEC-002 remain unverifiable end-to-end.
2. **B/A** add per-test `REQ-*` docstrings and update `docs/verification/test-map.yaml` for all new IDs
   (C's `traceability-handoff.yaml`); `tools/gates.py schema` traceability is blocked until then.
3. **B/A** add workspace benchmark/live evidence for REQ-PERF-001/003 (currently C-package-only).
4. **B/A** add the REQ-QUAL-005 absence-of-second-essay-copy assertion.
5. **A** implement the confidence field + `0.80` threshold branch (Decision-1); **B** add the five
   confidence tests (ADR-0001).
6. **A** implement local signing + trusted-key verification + confirmed-scores binding (Decision-2);
   **B** add unauthorized-signer / substitution / replay tests (ADR-0002). **E** provides key
   provisioning/rotation and the trusted-key boundary.
7. **B/E** add `api-surface.json` and `permissions-snapshot.json`; E adds `fractions` allowlist and
   `os`-forbidden-in-engine gate, plus a real secret scan (REQ-SEC-004).

## Known integration failures (explicit)

- One root cause for all `red`: the B/E acceptance suite imports flat `calculate`/`validate_advice`/
  `record_grade`; A's `src/` exposes `calculate_score`/`evaluate`/`GradeStore` (package-relative). ADR-0003.
- `test_feedback` is green but silently **does not test** the confidence contract (Decision-1) and treats
  `final_score` as an error rather than an ignored field (ADR-0001).
- `src/feedback_engine.py` imports `os` (REQ-SEC-004/R-07 boundary violation).
- Duplicate approval is currently **rejected**, not idempotent (REQ-FUNC-009/REQ-INV-008, R-09).
- No signing/verification exists in `src/` (Decision-2 is target behavior).
