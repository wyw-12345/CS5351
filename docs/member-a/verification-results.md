# Member A local verification — 2026-11-17

Scope: rebuilding the existing A work directly on E commit c59d1aa, with the documented module/file layout. Python 3.12.10 on Windows; no API calls in this rebuild.

| Check | Command | Result | Evidence |
|---|---|---|---|
| Offline tests | python -m unittest discover -s test/offline -v | 65 passed | ../../handoff/verification/all-offline.txt |
| Signed process restart | python -m scripts.demo_restart | Eight processes; persisted 72.00; identical retry; forged signature rejected | ../../handoff/verification/restart.txt |
| Calculator performance | python -m scripts.benchmark | 1,000 calls, ten criteria, p95 0.2246 ms <= 10 ms | ../../evidence/benchmark.json |

The tests cover confidence boundaries, invalid/model output, bounded requests, signed-score substitution/replay, transaction rollback, persistence and explicit migration. Existing supplemental A tests are placed under test/offline without changing assertions. The frozen calculator matches the prior A source byte-for-byte.

Historical real-model evidence is retained at evidence/live-results.json: prompt 1.2, 20 attempts, 20 expected status matches, reported model deepseek-flash and p95 1,704 ms. This is inherited evidence, not a new test, deployment validation or human semantic review. The effectiveness of 0.80 remains unevaluated.

The E Git tree contains no B tools, governance tests, verification-constraints.md or official test-map/snapshots despite historical references to them. Consequently no B gate or all-47-requirements pass is claimed. The supplemental A tests are not a replacement for independently reviewed B acceptance tests. Runtime isolation, production keys, OpenCode permission syntax, full raw transcript export, independent tests-only approval and exact-head human review remain with the named owners before release.

Submission checks: Ruff (E4/E7/E9/F/I, existing 110-column style), mypy, git diff --check and a local detect-secrets scan passed. Offline test ASTs (excluding docstrings) match the existing A tests exactly. These are local checks, not new CI or formal B gate results.
