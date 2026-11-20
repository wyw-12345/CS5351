# Member B CI candidate on the merged baseline

Baseline `fab81cb4769c4f0bc4ef0fdb666f504c17bbf14b`. Its checkout matches the tree verified in B test proposal `5f05f01`. GitHub PR #6 merged that lineage into main, including C/D/E/A and B's acceptance tests. The older stacked PRs document the planned split. The merge is real, prior independent test approval and main protection have not been established.

During candidate review, PR #7 advanced main to `8d9cdde`. It added the reviewed-input drafts under handoff and one AI-use log entry. The candidate incorporates that history and retains both append-only log entries.

The candidate restores B's gate utilities and tests from PR #4, adapts them to the signed API and current semantic candidate, and wires the six named checks to exact-head PR checkout. The workflow has no provider credentials. Model config and permission verification remain pending. No source, OpenCode permissions or existing application test assertions change.

The registry remains valid. The map now has callable locators for 44 of 47 requirements, including an explicit opt-in live performance test whose real execution is pending. Strict traceability remains incomplete for E01 (OpenCode permission enforcement), E02 (administrator-controlled review and branch protection), and E04 (tool enforcement). See each pending evidence entry in `docs/verification/test-map.yaml`.

Local checks on the candidate passed 50 governance tests and 73 offline tests. Ruff, mypy, pip check, the tracked-source secret-pattern scan, the two pinned dependency audits, and the append-only log check passed. The regression gate exercised all six existing B gate mutation cases and detected the five current A transaction/calculation/validation mutations. Three application cases still lack current evidence (signing, advisory isolation, and submission idempotency), so regression correctly blocks release. None of these checks made a live model request.

For release: E supplies permission/tool/OS runtime proof, independent reviewers approve the exact snapshots and tests, the administrator configures protection and the approved test baseline, and A/B obtain authorization for current model evidence. Keep each release check red when its evidence is missing.

## Follow-up after the first Ubuntu run

[Actions run 44778695021](https://github.com/wyw-12345/CS5351/actions/runs/44778695021) executed all six jobs. AI-use log passed. Schema, static analysis, semantic evaluation, and approval reported missing release evidence. Regression additionally exposed a B fixture that regenerated advice and changed elapsed-time metadata on exact retry. [PR #9](https://github.com/wyw-12345/CS5351/pull/9) contains the independent tests-only correction and is ready for review. Keep the revision separate until it enters main.

With #9 applied in an isolated rehearsal of the CI candidate, 53 governance tests, 73 offline application tests, Ruff and mypy passed. The mutation harness now confirms the suite detects rejection of an identical retry, raising its application coverage to six detected mutations. Signing and deployed advisory isolation remain explicitly not run.

The D7 helper now supports read-only server verification via `--check`. Tests exercised both branch responses, including refusal of relaxed review/check settings and GET-only execution. The authenticated repository API still reports `main` unprotected and the current account without admin access. Both protection endpoints returned 404. On the local Python runtime the helper itself stopped at certificate validation; the separate authenticated readback used the Windows trust store. No GitHub protection or credentials were changed.
