# PR #8 verification and bootstrap review memo

## A approved proxy implementation and real replay — 2026-11-23

Additional final check: production approval reaches the real #16 record but blocks on missing merge_commit_sha in its 2026-03-10 API response. Explicit 2022-11-28 readback includes the actual 8347ebc merge, and the same unchanged approval algorithm passes using those real diagnostic responses. Production gate remains blocked; B needs a separately reviewed API compatibility fix. See artifacts/proxy-implementation-20261123/approval-api-readback.json and approval-diagnostic.log. No new historical exception or API payload was invented.

New proxy work starts at independently approved #16 merge 8347ebc. Its first implementation commit is 2e135bf; approved tests, locators and plan remain byte-identical to the merge. The actual prior review/merge is now linked in implementation-approvals.json. This does not retrospectively excuse #13.

Seven proxy tests, 84 offline tests, 57 governance tests, 12 application mutants and six gate mutants pass. The proxy is explicit loopback HTTP CONNECT with default target TLS verification; evaluator routing/credentials are stripped and sandbox enforcement is unchanged. API snapshot is refreshed but pending independent implementation review.

Five actual model calls through the deployed worker pass fixed-case metrics and strict v2 O2; language metrics present en=4 / zh=1 without new thresholds. Canonical LF Git-archive runtime hashes match the replay revision 2e135bf. Returned usage is 2182 input / 577 output tokens, calculated conservative cost USD 0.0013470 (not actual invoice). Baseline is at docs/verification/semantic-baseline.json, with actual human acceptance still pending C/D; approval/live config flags remain unchanged.

Strict O2 is enforced in the archived operator replay checker; tools/semantic_eval.py remains outside this approved four-file implementation scope and still needs separately reviewed permanent O2 integration. Current CI live/offline evidence-ingestion design and final review/legacy history remain follow-ups. Full eight-item worksheet and exact feedback excerpt: handoff/records/2026-11-23-A-approved-proxy-to-CD.md.

2026-11-22 · B integration. The active policy on main at `cdd6ce7d25a2f937d2880140386ff22c96d387de` was retained without edits. GitHub reports main protected. The detailed protection and `test-baselines` endpoints returned HTTP 404 to the current credential, so use E/admin readback for the individual rules. Code-owner configuration and the frozen calculator path can be checked in this PR.

## Bootstrap baseline

The prior A implementation, retrospective B tests, and initial gate rollout predate policy activation. Their commits and approval evidence have been retained. Treat the historical candidate as a bootstrap review item, with no retroactive tests-before-code approval. The active policy applies to new work. The history and approval gates keep reporting the actual gaps until reviewers/admins approve a defensible bootstrap transition. This record grants no exception and does not declare that the transition was approved.

## E evidence and traceability

The new E01/E02/E04 locators verify the recorded configuration, rule precedence, the code-owner mapping, and the verifier role's declared shell limits using inert specimens. They neither invoke those tools nor prove runtime isolation. B01/B02/B05/B06/C01 and PERF-003 already had executable locators when this handoff arrived. PERF-003 and the semantic gate still need real A evidence.

The E readback records static import constraints, hashes and configuration declarations. The checked-in permissions file is evaluated with last matching rule winning, as documented by [OpenCode permissions](https://opencode.ai/docs/permissions/#matching). Matching the current configuration shows later broad rules overriding specific denials and the verify role accepting some unlisted commands. The official [OpenCode configuration paths](https://opencode.ai/docs/config/#locations) also make checking the installed version and actual loaded file necessary. E owns the correction and its runtime evidence. Static import and fingerprint checks cannot demonstrate process or filesystem isolation.

## Mutation scope

Disposable copies test two additional sub-properties. INV-003 detects incorrect association of a verified teacher with the signed audit while keeping signature verification intact. Existing signed-store negative tests separately confirm that unauthorized approvals are refused. INV-007 detects an inert forbidden dependency in the application source. This establishes static detection only. The application-mutation result keeps separate entries for the unverified-write-removal mutation and deployed advisory isolation, which have not been run.

The semantic workflow remains offline. A must obtain authorization and record the current model, inputs, approved policy and real results before a passing semantic baseline can be accepted. Do not pass credentials to this draft PR.

## Local results for this handoff

- Schema and strict requirement traceability passed, with 47/47 executable locators. The application offline suite passed all 73 tests. Ruff and mypy passed.
- E02's static owner/frozen-path check passed. E01 and E04 failed four synthetic subcases under the documented ordering. No protected file or live command was accessed to check them.
- Six gate mutations and eight application mutations were detected. The two distinct release-evidence obligations marked NOT RUN keep the application mutation check red.

## 2026-11-23 B integration candidate

**Verdict: CHANGES REQUIRED.** D's comment on PR #13 head `328c381` accepts the architecture and API snapshot for the single-teacher CLI. It records the broker's host privileges as a trust assumption. Scope evidence is at <https://github.com/wyw-12345/CS5351/pull/13>. A separate exact-head review is required for PR #8.

B verified 77 offline tests, 57 governance tests, four deployed-isolation tests, 12 application mutations, six gate mutations, and the restart demo in WSL2 on Ubuntu 26.04 with bubblewrap 0.11.1. The 12 application mutations include the three signature/key/binding mutations and the actual removal of deployed sandbox enforcement. The requirements check maps 47 of 47 IDs.

PR #12 remains a proposed record for the pre-`cdd6ce7` bootstrap scope. PR #13 revised the isolation tests in the same commit as implementation, outside that scope. No `test-baselines` ref or independent pre-implementation GitHub approval of the revised tests is available. Preserve the ordering failure and the empty approvals record. The two pending requirements are an agreed, reviewed history policy for the legacy scope and genuine prior approval for new work. The final semantic evidence is also pending. See `handoff/records/2026-11-23-b-isolation-ci.md` for the replay inputs and next review.

## A reviewed HEAD fallback candidate — 2026-11-23

PR21 approval is real: unohhh1 APPROVED `2c3bc8f530685deff4d4e982e88379eca6c88d53` at 2026-11-23T12:49:20Z, before implementation. The protected merge is `fbe7081122188f6bb4117da21af1a5127e20660e`; B's starting SHA `0a6417d344b51fc8c54e9739fdb199334880f786` also includes reviewed PR19 `8afdc5f`. Tests, plan and locators remain unchanged.

The fallback breaks the missing-main-artifact dependency without relaxing protection: exact current independent PR20 approval plus immutable approved blob equality is required. BASE read/Git errors are not absence. Accepted outputs still undergo the existing strict-O2 and fingerprint checks. A read-only check using the real main SHA and actual GitHub proof returned passed=true for deepseek-flash; no model call occurred.

The approved 13 tests and Linux's 84 offline tests pass. Full governance is 79 passed / 1 error: `StrictO2Tests.test_reviewed_baseline_rechecks_cases_instead_of_trusting_saved_metrics` mocks base_read but not the newly required Git presence lookup for its fictitious trusted-base. Do not weaken lookup or edit reviewed tests in this implementation. B/D should arrange an independently reviewed fixture-only adjustment, preserve its O2 assertions, and issue a protected start SHA. This candidate remains draft and is not regression-ready. All earlier memo records are retained; B must preserve #8's three historical records when integrating.

## A PR23 regression follow-up — 2026-11-24

The prior PR22 fixture blocker is resolved through D-approved tests-only PR23 (`deee8b6`, approval 2026-11-24T08:11:56Z) and protected merge `aeb4bfba9cfe90e4e185e450f6cfe8dce04cf048`. A merged that baseline into PR22 without changing runtime or PR21 tests. Full Linux regression now passes: 80 governance and 84 offline tests, no skips. Ruff, mypy and schema also pass. Both sides of the AI-log append conflict were retained. See `handoff/records/2026-11-24-A-PR23-regression-handoff.md`. B next integrates the approved fixture ancestry and implementation into PR8, keeps the separate review/blob provenance, and reruns six gates; D reviews the final exact SHA. Earlier memo entries record their historical state and are retained.
