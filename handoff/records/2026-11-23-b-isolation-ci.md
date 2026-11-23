# B integration handoff, 2026-11-23

This integration candidate starts from A's PR #13 at `328c381cc12282e17a8dd2b521c5059fe2dfef41`. D (GitHub `unohhh1`) reviewed that exact commit's architecture and API. The review records a networkless evaluator, trusted broker, and single-teacher CLI scope. The candidate still awaits final review.

## Verification

Ubuntu 26.04 via WSL2, Python 3.14.4 and bubblewrap 0.11.1. The suites used synthetic inputs and signing keys.

| Command | Result |
| --- | --- |
| `python -m unittest test.offline.test_deployed_isolation -v` | 4 passed |
| `python tools/check_suite.py test/offline` | 77 passed |
| `python tools/check_suite.py test/governance` | 57 passed |
| `python tools/application_mutation_check.py` | 12 killed |
| `python tools/mutation_check.py` | 6 killed |
| `python -m scripts.demo_restart` | Passed, persisted 72.00 and rejected a forged signature |
| `python scripts/validate_requirements.py --strict --json` | Passed, 47/47 requirements mapped |

The three INV-003 mutations execute only in disposable copies. Each must compile, pass its unmodified baseline and trigger the intended rejection assertion in the negative test. A process error, missing dependency, or import failure does not establish these kills.

## Test approval evidence

The team needs a protected `test-baselines` ref. A tests-only PR must carry its test plan and exact map locators, obtain independent GitHub approval, and merge before its implementation begins. Put new approval evidence in `implementation-approvals.json` only when those events happened and the approved test merge is in the implementation's history.

Two proposed review scopes for new work: (1) approval chronology versus regression behavior, covering rejection of a late review and a post-approval test edit; (2) INV-003 mutation reporting, covering targeted assertion failures and refusing to count collection or process errors as detection. These are scopes for genuine follow-up testing. The local B mutation experiment uses existing negative tests. It is not an independently approved tests-only PR.

## Semantic replay intake

Pending C/D approval of language aggregation, the expected reason for `unverifiable-data`, and the evidence ingestion design. A should supply authorized replay output with all fixed case IDs, actual model, case results, usage, metrics and the fingerprints of the evaluated revision. The historical 20-call file `evidence/live-results.json` predates the isolated worker. A separate 25-replay result has not been located in the candidate or repository artifacts. No live calls were made in this B handoff.

The following are SHA-256 values after converting CRLF to LF. The input hashes and runtime fingerprints identify this candidate. Each replay should identify the entry point used and the tested revision.

```text
1be72e185d14bf6445d2e7eb45fde66de5c54277bf347b4372ec0e394a82d755  config/model.json
f60a427951c9be559c316795f76481f246e7255a16f746ec1b1db3b638415369  prompts/prompt_v1.2.yaml
67f89aaba09b30b9276ce941d9570b9a9c6be02695e68681e19b21677f1022ca  test/live/fixed-cases.json
973e04ff45e70565f4d1617d163eaeced70b8e759547aa581f047654fe9f0956  src/feedback_engine.py
1f2257f9a9eb1cc3ab140105ae380f5eeb74f69da238a1bb21e2d7fd16c54071  src/contracts.py
8421733f6d9e5d78c03b0ee8ff512517322001cbf72194c5729f9c358abd7fd2  src/cli.py
7dbff09e0394c5c4065fa175876c0e48a0c91cf2a35df293d2c6225494780f95  scripts/advisory_worker.py
```

The PR workflow sets `GRADEAIDE_LIVE=0`. Reuse on the offline path requires a passing baseline from a trusted revision and matching input identities. The existing replay helper still invokes the feedback engine directly and builds its output identity from raw bytes. D must review how the release flow binds normalized identities and exercises the deployed worker before the team accepts this evidence as a semantic baseline.
