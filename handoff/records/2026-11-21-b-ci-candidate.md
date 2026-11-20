# Member B CI candidate on the merged baseline

Baseline `fab81cb4769c4f0bc4ef0fdb666f504c17bbf14b`. Its checkout matches the tree verified in B test proposal `5f05f01`. GitHub PR #6 merged that lineage into main, including C/D/E/A and B's acceptance tests. The older stacked PRs document the planned split. The merge is real, prior independent test approval and main protection have not been established.

The candidate restores B's gate utilities and tests from PR #4, adapts them to the signed API and current semantic candidate, and wires the six named checks to exact-head PR checkout. The workflow has no provider credentials. Model config and permission verification remain pending. No source, OpenCode permissions or existing application test assertions change.

The registry remains valid. The map now has callable locators for 44 of 47 requirements, including an explicit opt-in live performance test whose real execution is pending. Strict traceability remains incomplete for E01 (OpenCode permission enforcement), E02 (administrator-controlled review and branch protection), and E04 (tool enforcement). See each pending evidence entry in `docs/verification/test-map.yaml`.

For release: E supplies permission/tool/OS runtime proof, independent reviewers approve the exact snapshots and tests, the administrator configures protection and the approved test baseline, and A/B obtain authorization for current model evidence. Keep each release check red when its evidence is missing.
