# A → D/B: reviewed HEAD replay fallback tests only

Base: protected test-baselines e4f36fec03dc228458790ef79c1f717fe27b414d. Inspected integration candidate: #8 f30e3c75dcef7114664646b7462f2fb760db343c. Approved artifact proposal: #20 a3063c306f42aef9e8da2bc17fa399d7bcb80da5, with D/unohhh1 APPROVED on that exact head. No source implementation is changed in this proposal.

## Goal

Resolve the evidence bootstrap dependency without changing repository protection. If the target BASE genuinely has no docs/verification/semantic-baseline.json, permit the candidate HEAD file only after authenticated proof that it is exactly the immutable file approved in PR #20. A BASE file that is corrupt, stale or unreadable is not equivalent to an absent file and must not activate fallback.

This does not waive #13 chronology, approve a candidate's own arbitrary baseline, relax any semantic threshold, edit evaluation_approved, or create a successful CI status. Final #8 approval remains after integration and final SHA selection.

## Proposed interface and test scope

New helper contract: tools.semantic_eval.load_reviewed_baseline(base, api=None). api is an injectable GitHub read client for deterministic synthetic tests, not a source of caller-supplied acceptance in production. The normal CI path must construct it from the actual repository/token context if fallback is needed.

1. Establish BASE path existence with Git, distinguishing lookup/read errors from absence. If present, use BASE without any HEAD/API fallback.
2. Only when absent, use the trusted BASE reviewer policy and authentic PR #20 metadata/reviews. Require independent allowlisted User approval on the exact current proposal SHA; reject missing, stale, dismissed, superseded, self or bot approval.
3. Require the proposal to target this repository's main and its artifact to be a regular file. Read immutable content metadata at the approved head, and compare its Git blob identity with HEAD:docs/verification/semantic-baseline.json. Blob equality binds all bytes, not just claimed human_acceptance flags. Do not invent API payloads or silently read a different PR/head.
4. Reuse #19's existing check_reviewed_replay pipeline after loading. Revalidate runtime/model/input identity, C/D acceptance, real usage, exact fixed-case IDs, actual advice and strict O2; saved passed/metrics fields alone are insufficient.

13 test methods, with additional negative subcases, are in test/governance/test_a_reviewed_head_baseline.py. Exact requirement locators and the sole future implementation path tools/semantic_eval.py are recorded in docs/verification/test-plans/reviewed-head-baseline.json and test-map.yaml. The tests include an end-to-end saved-run contract that requires the new loader to be called even when downstream validation rejects an artifact. It cannot pass merely because an unrelated old BASE lookup failed.

Tests use mocks and synthetic data only: no GitHub requests, model calls, network permission, real acceptance signature or production evidence mutation. They define new behavior before implementation. Current protected baseline has no loader, so the targeted suite is intentionally red. The captured baseline collected 13 tests, with 8 failures and 15 errors counting subcases: missing helper and missing routing through it. Ruff and schema pass. These are not release-pass claims.

## Dependency and exact handoff order

The protected baseline currently contains the #18 tests but not #19's reviewed implementation. #8 already has that implementation, including strict O2 and saved-output recomputation. D/B must account for this difference before issuing A's implementation start SHA. Do not import #8's runtime source in this tests-only PR or ask A to silently reproduce all #19 work under this one-path scope.

Recommended sequence: D reviews this exact tests-only head; B incorporates approved tests into the protected baseline and arranges any separately reviewed synchronization of the existing #19 implementation; B supplies the final protected start SHA containing both the approved tests and intended checker dependency. A starts only from that SHA and preserves approved tests/locators. The earlier approved test merge must remain an ancestor of the first fallback implementation commit. Any source synchronization must be handled openly as a separate integration decision, not hidden in the test PR.

Implementation later changes only the approved tools/semantic_eval.py path and corresponding review evidence. It should keep normal trusted-BASE reuse working, leave strict O2 intact and add a fail-closed fallback proof. Record the dependency-cycle reason in review-memo then, and run full prior suites. Final integration/review/gate rerun remains with B/D. #13's separate delivery decision may proceed in parallel and is not solved here.

## Review evidence

Review #20: https://github.com/wyw-12345/CS5351/pull/20 (verify live review metadata and exact SHA rather than relying on this text). The author of #20 is this-kong; the independent reviewer is unohhh1. GitHub approval/proof must be re-read by the implementation rather than trusting a candidate's editable declaration.

Source work is tests-only. No tools/src/scripts/config/prompts/workflow/permission/model-approval changes, no baseline file replacement and no branch-protection change. New log entries are appended; prior entries remain intact.
