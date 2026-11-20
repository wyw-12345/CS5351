# OpenCode tests-only review note

Date: 2026-11-17 Asia/Shanghai. Scope: B's user-authorized supplement in the isolated
`GradeAide-B-integrated-2026-11-17` workspace. This note records a draft review; it is not a human
approval, a test-approval signature, or a release decision.

## Authorship and provenance

- Codex had already re-pointed `test/offline/test_authority_boundary.py` to A's package API, added
  `test/offline/test_confidence_contract.py` and `test/offline/test_signed_approval_contract.py`, and
  inserted the 47 formal REQ docstrings. This note does not relabel that work as OpenCode's.
- OpenCode authored the two new test files below and this review note in this session. The prior
  plan session `ses_e17d5f52fffeDMa5iKV7Xkbcuh` is AI planning only; it is not a human signature.
- No `src/`, `scripts/`, `test/support.py`, registry, architecture, `AGENTS.md`, `.opencode`,
  `.agent`, `.github` or protected-policy file was changed by this work.
- No live provider call was made. Evidence tests read historical files only.

## Files written in this phase

- `test/governance/test_b_integration_guards.py` — tests for the candidate `tools.integration_checks`
  module and for the proposed `tools.gates` scope change.
- `test/offline/test_b_evidence.py` — evidence-only checks for the historical benchmark, historical
  live run, feedback import boundary and calculator allowlist.
- `docs/member-b/supplement-2026-11-17/OPENCODE-TEST-REVIEW.md` — this note.

## Actual local checks

Command: `python -m unittest test.offline.test_b_evidence -v`

- 4 tests, 4 passed. These are green because they inspect existing historical evidence and current
  import boundaries, not because a new evaluation was performed.

Command: `python -m unittest test.governance.test_b_integration_guards -v`

- 8 test methods, 10 failures/subtest failures. This is the intended draft state:
  - `tools.integration_checks` does not exist yet (candidate review proposal only).
  - `tools.gates.is_implementation` does not yet cover `scripts/`, `requirements-dev.txt` or
    `requirements-b-supplement.txt`.
  - `tools.gates.check_ai_log` does not yet treat a script-only change as relevant.
- These tests must remain red until the gate proposal is reviewed and supplied. They are not evidence
  that the gate currently works.

## Signing-seam limitations in the current B target

The signing tests in `test/offline/test_signed_approval_contract.py` describe a target seam that A has
not implemented. They are red, not skipped, and they do not fabricate an A function.

1. `GradeStore(path, trusted_keys={...})`, `create(..., submission_id=...)` and
   `approve(..., approval={key_id, binding, signature})` are target-contract names awaiting A
   agreement. Current `GradeStore` has none of these parameters, and current `approve` still accepts a
   client-supplied reviewer label.
2. The proposed signed binding covers `submission_id`, `proposal_hash`, rubric ID/version and
   `confirmed_scores_sha256`, but not the essay digest, reviewer role, key epoch, issue time, nonce or
   revocation state. Replay across copied databases, key rotation and revocation are therefore outside
   the current target test.
3. The target test uses ephemeral in-process Ed25519 keys. That proves only a local verification seam,
   not real teacher authentication, OS key custody, or E's runtime permission model. It must not be
   described as production authentication.
4. Canonicalization and hex encoding are exercised only through the Python helper. There is no
   independent cross-language or external-signer fixture, no domain-separation/version tag, and no
   signed audit reason. A signature over the same map through a different canonicalizer is not proven
   compatible.
5. The target seam inherits the old store's transaction path. Fault injection for a crash between
   approval verification and durable write is not yet demonstrated by these tests.

## Old application behavior limitations exposed by the tests

- `GradeStore.approve` compares the proposal hash with `hmac.compare_digest`, but the reviewer is still
  a caller-supplied string. The current red test `test_unapproved_write_is_rejected` shows that a
  forged client name is not authentication.
- `GradeStore.approve` rejects a second approval instead of returning the original record. The red
  `test_retry_is_idempotent` shows that ADR-0003's idempotent-return target is not implemented.
- `feedback_engine.evaluate` does not yet require and validate per-criterion confidence. A's historical
  fixture deliberately omits confidence; the new tests add confidence locally and must not edit
  `test/support.py` to make old tests green.
- `feedback_engine` still imports `os`, which D records as a violation of the configuration-injection
  boundary. The evidence test here checks only the narrower `grade_store` import boundary, so it must
  not be read as clearing the `os` issue.
- The calculator currently imports `fractions` and `.contracts`. The test verifies that this is inside
  D's allowed set (`decimal`, `fractions`, `typing`, `dataclasses`, `__future__`, `collections`,
  `contracts`); it does not make the calculator frozen-change process satisfied.

## Structural mapping is not behavioral acceptance

The new docstrings name official REQ IDs so a future traceability gate can locate them. That is
structural mapping only. It does not prove that A implemented the behavior, that the historical live
output is semantically correct, that a reviewer accepted the results, or that the six blocking gates
passed on `main`. The historical `live-results.json` still says its `semantic_review` is `PENDING`, and
the evidence test asserts that pending status instead of claiming human semantic approval.

## Remaining obligations

- A must agree or reject the signing seam and confidence field before these target tests can be
  accepted as implementation requirements.
- The `tools.integration_checks` proposal and the `tools.gates` scope change need independent human
  review before merge; this phase did not modify root `tools/`.
- An AI-use log entry is required for these code changes before any gate can pass. It was not appended
  here because this task restricted writes to the three B test/document paths above.
- A real human must review this note and the tests; no approval is claimed.
