# PR #8 verification and bootstrap review memo

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
