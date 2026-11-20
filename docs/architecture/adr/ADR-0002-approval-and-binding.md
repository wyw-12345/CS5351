# ADR-0002 — Approval authority and approval binding

- Status: Accepted (D2 baseline); **revised 2026-11-12 to align with C's draft requirements 0.1.0-c**
  (REQ-FUNC-005, REQ-INV-003). The requirements baseline is **pending human review**. The signing
  design is **target behavior pending implementation and verification**.
- Date: 2026-11-11 (initial); 2026-11-12 (authenticated-approval revision).
- Relates: `handoff/A-B-E-接口差异与待决事项.md` row "人工批准";
  `REQ-INV-003` (C baseline 0.1.0-c; E's `REQ-SEC-003` was merged into `REQ-INV-003` by C's ID map);
  `REQ-FUNC-005`. Resolves Conflict-2 (authentic approval vs trusted-CLI audit label) recorded in
  `docs/architecture/trace-matrix.md`.
- Owner: D. Enforced by: `src/grade_store.py`, `src/cli.py`. Verified by: E (key/credential boundary),
  B (tests), A (implementation).
- Alignment: **aligned with C's draft 0.1.0-c.** Approval must be *verified* (a signature from an
  authorized teacher's credential). The reviewer *name* remains an audit label; the *identity proof* is
  the verified signature. Single-teacher CLI scope is retained; multi-user token service stays out of
  scope.

## Context

Grade recording must require explicit human approval bound to the exact grading proposal. Two models
disagree:

- **A** (`src/grade_store.py:155-183`): `approve(proposal_id, proposal_hash, scores, reviewer, reason)`.
  The `reviewer` is a free-text CLI string (`src/cli.py:31`), validated only as nonempty ≤ 200 chars
  (`grade_store.py:158`). Binding is the **proposal hash** (digest of essay+rubric+advice+hashes+
  `created_at`, `:105-109`), compared with `hmac.compare_digest` (`:167`). The store recomputes the
  score itself and never accepts a caller-supplied final grade (`:171`). Duplicate approval is
  **rejected** (`:165-166`). A honestly documents that "teacher-name entry is not authentication"
  (A-ADR-001 `:34`; `interface-contract.md:11`).
- **B/E** (`docs/member-b/02-interface-contract.md:19-25`; `test/offline/test_authority_boundary.py:97-109, 142-150`):
  an **injected trusted `verify_approval(approval, binding)`** returns the reviewer identity; the
  binding covers `submission_id`, `essay_sha256`, `rubric_sha256`, `advice_sha256`; a forged/missing
  client name or stale binding → `PermissionError`, zero writes; the record stores the **verifier-
  returned** identity, not a client string; retries are idempotent.

C's draft baseline 0.1.0-c requires **verified** approval. **REQ-INV-003** states (verbatim): "No grade
is persisted without **authentic human approval** bound to the exact submission, rubric and advice; a
client-supplied name, flag or boolean is **not** authentication." **REQ-FUNC-005** requires that no
grade is created before an authenticated human approval. The earlier D2 baseline shipped a trusted-CLI
**audit label**; the user has directed D to **follow C's draft** and adopt a real authentication
mechanism *within the single-teacher CLI scope* (no server, no multi-tenant token service). The design
below is **target behavior pending implementation and verification**.

## Decision

1. **Scope: a single-teacher CLI, with *verified* local approval.** The CLI runs on the teacher's
   machine. Authentication is established by a **local signing credential** controlled by the
   authorized teacher, not by a typed name. The reviewer *name* remains an **audit label**; the
   **identity proof** is the verified signature over the approval binding.
2. **Local signing design (target):**
   - **Authorized teacher controls a private signing key.** The key is stored **outside the repository**
     (e.g. OS keychain, `~/.gradedeaide/`, or an agent like gpg-agent); it is never committed and never
     written to logs (REQ-SEC-004). Provisioning/rotation is an operator (E) task.
   - **The grade store verifies the signature against a trusted public key.** The trusted verification
     key is configured at the store boundary (not supplied by the model or the request). A default-deny
     allowlist of trusted keys maps to teacher identity; an unknown key is rejected.
   - **What is signed (the approval binding):** the store verifies a signature over the canonical tuple
     `binding = (submission_id, proposal_hash, rubric_id, rubric_version, confirmed_scores_sha256)` where
     `confirmed_scores_sha256 = H(canonical(S*))` and `S*` is the exact teacher-confirmed criterion score
     set. This binds approval to the **exact submission, proposal, rubric version, and teacher-confirmed
     criterion scores** — not merely to a valid set that happens to recompute.
   - **Signature scheme:** a standard detached signature (e.g. Ed25519 over `H(canonical(binding))`).
     The record stores the key id (audit label), the signature, and the binding fields; the private key
     is never stored.
3. **G1 vs G2 are distinct and both required.**
   - **G1 — validation and recomputation:** the submitted scores are well-formed, in range, cover
     exactly the rubric, and `score_calculator` reproduces the stored total. G1 says nothing about
     *who* approved or *which* scores were confirmed.
   - **G2 — verified, bound approval:** the signature proves an *authorized teacher* approved *this
     exact* proposal, rubric version and confirmed score set. G2 is an authenticity + integrity
     property; G1 is an input-validity property.
4. **The store rejects approval when:**
   - **Unauthorized signer:** the verification key is not in the trusted allowlist, the signature does
     not verify, or the signing credential is absent → `PermissionError`, zero writes.
   - **Changed scores:** `confirmed_scores_sha256` does not equal `H(canonical(accepted_scores))`, or the
     signature covers a different score set than the one presented for recording → reject, zero writes.
   - **Signature reused for a different submission:** the signed `submission_id` / `proposal_hash` /
     `rubric_version` do not match the proposal being recorded (replay onto another submission) →
     reject, zero writes. (A signature is bound to one `binding` tuple and cannot be reused.)
   - **Stale proposal:** essay/rubric/advice changed after approval (proposal hash mismatch) → reject.
5. **On acceptance the store: (a) verifies the signature against the trusted public key, (b) verifies the
   binding fields match the stored proposal and the presented accepted scores, (c) recomputes the total
   with `score_calculator`, and (d) atomically records the grade and audit entry in one transaction
   (rollback on any failure). The caller never supplies the final score; the audit stores the verified
   key/teacher identity, `accepted_scores`, `confirmed_scores_sha256`, and the binding.**
6. **Escalated cases are resolved through the same verified-approval path:** resolving an escalated
   proposal requires the full confirmed score set, a nonempty reason, and a valid signature — the
   manual grading path is preserved, not bypassed.
7. **Recording is atomic and additive.** `BEGIN IMMEDIATE` updates the proposal to `approved` and
   inserts the grade+audit row in one transaction (`grade_store.py:162-178`); rollback on any failure;
   reads re-verify digests (`:112-153`). No partial write is observable.

## Current CLI behavior and target approval sequence

### Current behavior (`src/cli.py`, `src/grade_store.py`) — **no signature verification today**

- The teacher runs `approve --id <proposal_id> --hash <proposal_hash> --scores <file.json> --reviewer
  <label> --reason <text>` (`cli.py:27-32`). The scores file is a JSON object mapping each criterion ID
  to a decimal string, read fresh at approval time (`cli.py:62`).
- `GradeStore.approve` (`grade_store.py:155-183`) receives the scores **as an argument in the same call
  that writes the grade**. It validates them (`contracts.validate_scores`), verifies the proposal hash
  (`:167`), recomputes the total, and persists. **There is no signed approval and no "teacher confirmed
  these scores" binding:** the reviewer is a free-text label, the scores are chosen and consumed inside
  one process invocation, and binding is only to the proposal hash (`:167`). The current binding is
  **G1 + proposal-hash**, with **no G2 authenticity** and no confirmed-scores hash.
- This does **not** satisfy REQ-INV-003 as written ("authentic human approval … a client-supplied name
  is not authentication"). The signing design below is the target that A must implement.

### Target approval sequence (verified, G2)

1. **Propose / display** — the teacher views the proposal (advice + suggested scores + `submission_id`,
   `proposal_hash`, rubric `id`/`version`).
2. **Confirm** — the teacher enters the full, final criterion score set **S\*** and a reason, and
   explicitly confirms *this score set, for this proposal hash and rubric version*.
3. **Bind** — compute
   `binding = (submission_id, proposal_hash, rubric_id, rubric_version, confirmed_scores_sha256)` with
   `confirmed_scores_sha256 = H(canonical(S*))`.
4. **Sign** — the CLI signs `H(canonical(binding))` with the **teacher's private key** (held outside the
   repo); the signature + key id accompany the request.
5. **Record** — `grade_store` receives `S*`, the binding, and the signature; it (a) verifies the signature
   against the **trusted public key** in the allowlist, (b) checks the binding fields match the stored
   proposal and `H(canonical(S*)) == confirmed_scores_sha256`, (c) recomputes the total, and (d) writes
   the grade + audit atomically. Any failure → `PermissionError`/`ValueError`, zero writes.
6. **Audit** — the record stores the verified key id / teacher identity (audit label), signature,
   `accepted_scores`, `confirmed_scores_sha256`, and binding fields.

In the single-teacher CLI, steps 2–5 may occur in one invocation, but the store still performs the
signature and binding checks independently. Authenticated **multi-user** approval (a remote token
service) remains out of scope; the local signing key is the in-scope authenticity mechanism.

## What the current code already enforces vs what this ADR requires

| Aspect | Current code (`src/`) | This ADR requires | Gap |
|---|---|---|---|
| Score authority | Store recomputes; caller score ignored (`:171`) | Same | none |
| **G1 validation + recomputation** | Scores validated + total recomputed (`:171`) | Same | none |
| **G2 verified, bound approval** | None — free-text label, proposal hash only (`:167`) | Signature over `binding` verified against trusted public key; `confirmed_scores_sha256` checked | **add signing + verification + confirmed-scores binding** |
| Binding to submission/proposal | Proposal hash only (`:167`) | `submission_id` + `proposal_hash` in signed binding | add `submission_id` + signing |
| Binding to rubric version | Implicit inside proposal hash | Explicit rubric `id`/`version` in signed binding | add explicit field |
| Binding to confirmed scores | None | `confirmed_scores_sha256` in signed binding | add field + check |
| Reviewer name | Free-text `--reviewer` label (`:158`) | **Audit label only**; identity from verified signature | keep label, add signature |
| Authorized signer check | Absent | Trusted-public-key allowlist; unknown key → reject | **A/E work item** |
| Replay onto another submission | Not prevented by label | Binding includes `submission_id`; replay rejected | **A work item** |
| Atomic write | Single transaction + rollback (`:162-178`) | Same | none |
| Duplicate approval | Rejected (`:165`) | Idempotent retry / conflict on different content (ADR-0003) | change in A |
| Approval record content | `reviewer`, `reason`, `accepted_scores`, `final_score`, `proposal_hash`, `approved_at`, `calculator_version`, `previous_status` (`:172-174`) | Same + `submission_id`, rubric version, `confirmed_scores_sha256`, key id, signature | add fields |

## Required negative test — altered scores after approval

**Test: `test_altered_scores_after_approval_are_rejected`** (to be added via a tests-only PR; owned by
B, implemented against A's store).

- Setup: create an acceptable proposal; approve it with a known score set S and capture the returned
  record (its hash/digest and `score`).
- Action 1: attempt to approve the *same* proposal a second time with a **different** score set S'
  (e.g. raise one criterion to `max_score`).
  - Expect: `ValidationError`/`ValueError` (already-approved or conflicting), **no** change to the
    persisted grade or audit, store still returns the original record.
- Action 2: after a successful approval, mutate the *stored* accepted scores (simulating tampering)
  or recompute with S' out of band; then `get()` the proposal.
  - Expect: integrity check fails (`ValueError`) because `audit`/`grade` digest no longer matches —
    the store already recomputes and compares (`grade_store.py:146-148`).
- Action 3: attempt to approve with a *stale* proposal (essay edited after approval) — already covered
  by `test_unapproved_write_is_rejected` (`test/authority_boundary.py:104-109`); assert
  `PermissionError`/`ValueError` and no new row.
- Mutation guard: removing the recompute-and-compare (`:146-148`) or the already-approved check
  (`:165`) must make this test fail.

This test pins both "the accepted scores are the ones graded" and "a later differing score set cannot
replace the approved grade".

## Required negative test — score substitution between confirmation and recording

**Test: `test_score_substitution_between_confirmation_and_recording_is_rejected`** (to be added via a
tests-only PR; owned by B, implemented against A's store after A adds the `confirmed_scores_sha256`
binding). This test targets **G2 specifically** — an otherwise *valid* score set that recomputes
cleanly must still be rejected if it is not the set the teacher confirmed.

- Setup: create a proposal; the teacher confirms score set S (mixed with the advice, e.g.
  `{"argument":"8","evidence":"10"}`) and signs the binding
  `b = (submission_id, proposal_hash, rubric_id, rubric_version, confirmed_scores_sha256=H(canonical(S)))`.
- Action 1 (**substitution of a valid set**): present the *correct* signature/binding `b` but a
  **different, individually valid** score set S′ that still sums within range and recomputes fine (e.g.
  raise `argument` from 8 to 9, or swap two criteria).
  - Expect: rejected with a binding error (`ValueError`/`PermissionError`), **no** grade row; the store
    must detect `H(canonical(S′)) != confirmed_scores_sha256`. A store that only validates (G1) or only
    checks the signature would wrongly accept S′, so this action is the discriminating test.
- Action 2 (**signature replayed onto a different submission/proposal**): present the valid signature `b`
  with the correct S but a *different* `submission_id`/`proposal_hash`.
  - Expect: rejected; the signed binding is submission/proposal-specific.
- Action 3 (**rubric version drift**): correct S and proposal hash, but rubric `version` changed after
  confirmation.
  - Expect: rejected; binding is rubric-version-specific.
- Action 4 (**control**): correct signature/binding `b` with the confirmed set S → record succeeds,
  `score == calculate_score(rubric, S)`, audit stores `accepted_scores == S`, `confirmed_scores_sha256`,
  and the verified key id.
- Mutation guard: removing the `confirmed_scores_sha256` check, the signature verification, or the
  submission/proposal binding check must make the matching action fail (mutant killed).

## Required negative test — unauthorized signer

**Test: `test_unauthorized_signer_is_rejected`** (planned; B/A, tests-only PR). The store must reject an
approval whose signing key is not in the trusted allowlist, or whose signature does not verify:

- Action 1: sign the correct binding with a **key not in the allowlist** → `PermissionError`, zero writes.
- Action 2: present a **corrupted/forged signature** (valid key id, bad signature bytes) → reject.
- Action 3: present **no signature / a client name only** (`--reviewer` string, or a boolean) →
  `PermissionError`; a name is an audit label, not authentication.
- Action 4 (control): sign with a trusted key → record succeeds, audit stores the verified key id.
- Mutation guard: removing the public-key allowlist check must make Action 1 fail.

These tests pin: (i) the accepted scores are the ones graded, (ii) a later differing score set cannot
replace the approved grade, (iii) only an authorized teacher's key can approve, and (iv) a signature
cannot be reused for another submission. **All of the above are target tests — none exist yet; current
code has no signing.**

## Alternatives

| Alt | Benefit | Cost | Outcome |
|---|---|---|---|
| A-only (reviewer label, proposal-hash binding only) | Fits single-user CLI; simple | No authentication, no G2 binding — violates REQ-INV-003 | **Rejected** |
| **Local signing key + trusted public-key verification (this ADR)** | Authenticity + G2 binding within single-teacher CLI; offline | Key provisioning/rotation (E) | **Adopted (aligned with C 0.1.0-c)** |
| OS keychain / gpg-agent signing | Reuses platform credentials; offline | Platform-specific setup | **Compatible variant** of the same design |
| External `verify_approval` callable / token service | Multi-user ready | Server/token infrastructure; out of single-teacher scope | Future (reopening) |

## Verification

- Existing (partial, no auth): `test/offline/test_store.py::test_missing_approval_details_and_stale_hash_are_rejected`,
  `test_duplicate_approval_cannot_overwrite_history`, `test_proposal_has_no_grade_and_human_change_is_audited`,
  stored-score==calculator test. These prove G1 and proposal-hash binding only.
- Contract-target (red until API aligned): `test_unapproved_write_is_rejected` (forged/missing/bool →
  `PermissionError`, no rows), `test_audit_records_both_sources`, `test_retry_is_idempotent`.
- **Planned (signing; not present):** `test_unauthorized_signer_is_rejected`,
  `test_score_substitution_between_confirmation_and_recording_is_rejected`,
  `test_signature_replay_onto_other_submission_is_rejected`,
  `test_altered_scores_after_approval_are_rejected`, and an explicit rubric-version-mismatch test.

## Runtime observable / fallback

- Signal: audit record written exactly once per proposal; `reviewer` (label), verified key id,
  `accepted_scores`, `confirmed_scores_sha256`, `submission_id`, rubric version, three content digests and
  `proposal_hash` present; signature verifies against the trusted key; `score` equals a fresh
  `calculate_score` of accepted scores; `confirmed_scores_sha256 == H(canonical(accepted_scores))`.
- Fallback on violation (bad/unknown signature, changed scores, replay, tamper, double-write): refuse the
  write, roll back, retain a privacy-safe diagnostic, surface to the teacher for manual reconciliation
  (no automatic repair).

## Reopening conditions

- More than one teacher, or any remote/networked approval path → **multi-user authenticated approval**;
  adopt an external `verify_approval`/token service; re-open ADR-0002 and update `permission-model.md`.
- The signing scheme/credential store is chosen differently (e.g. hardware key) — record an amendment.
- A storage backend change (see ADR-0003 atomic persistence).
