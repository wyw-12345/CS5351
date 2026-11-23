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

## PR 8 release evidence references

- C's bootstrap decision in [PR #12](https://github.com/wyw-12345/CS5351/pull/12) applies through cdd6ce7. D approved the documentation at 02597c8. [Exact-head review](https://github.com/wyw-12345/CS5351/pull/12#pullrequestreview-6020980889).
- A's [PR #15](https://github.com/wyw-12345/CS5351/pull/15) records the separate #13 chronology deviation after that boundary. Keep the change's actual test and implementation order. [Source audit](https://github.com/wyw-12345/CS5351/blob/11b4b8a357ab121b819d40c8f73117c91038d644/handoff/records/2026-11-23-A-post-B-review.md).
- Both records below are preserved as written. Their test counts, acceptance statements, and evidence references describe the recorded stage. PRs #16 and #18 are later approvals for their own scopes. The later authorized replay in #17 and the six-gate run in #19 have separate evidence. [Six-gate run for #19](https://github.com/wyw-12345/CS5351/actions/runs/45162380332).
- Final review applies to the exact PR #8 head after integration. This memo records chronology and approvals without changing the gate rules.

## C-BOOT-001 — bootstrap baseline decision (recorded, not an approval)

- Date: 2026-11-23, Asia/Shanghai. Author: C (Yuwei WANG, 60875477), baseline owner. Authoring agent: Vibe (Mistral)
  with human decisions taken by C. Raw session kept locally by C; not attached to the repository.
- PR: `docs/member-c-bootstrap-baseline` → `main` (see PR body template). Base: `main` at `cdd6ce7`. Head: recorded in
  the PR after the first push. This entry documents a governance decision and must not be read as an approval of any
  code change.
- Changed REQ/ADR/INV: `ADR-B0006` (new), `REQ-GOV-C01` (requirements change process), `REQ-GOV-B03` (traceability),
  `REQ-GOV-B06` (AI-use log). No requirement text or threshold was relaxed by this entry.
- Spec alignment: the course requires tests to be reviewed before implementation. For the window up to `cdd6ce7` that
  requirement cannot be satisfied honestly, because PR #6 merged implementation, retrospective tests and gate tooling
  together and `docs/verification/implementation-approvals.json` is empty. The deviation is accepted, dated and bounded;
  it is described in the report rather than hidden.
- Architecture alignment: no runtime, policy or interface change. The decision only affects how two gate sub-results are
  interpreted. `main` keeps `policy.json` `status: active` with reviewers this-kong and unohhh1; the stale pending copy
  carried on `ci/member-b-gates` must not overwrite it at merge time.
- Code/test quality: no source file touched. The bootstrap decision does not cover `schema`, `static-analysis`,
  `semantic-evaluation`, or the mutation sub-checks of `regression`; those remain open with their own owners
  (B for test locators and mutations, A for the live model replay, D for the independent review).
- Security/privacy: no credential, token or `.env` content involved. No approval, signature or commit authorship was
  fabricated; the empty `implementation-approvals.json` was deliberately left empty.
- Latency/token/cost: not applicable to this change.
- Six gate run URLs: to be added by B after the merge of PR #8 and the re-run on the merged head. Before that, the honest
  status is "bootstrap deviation recorded; test-approval and regression history sub-check decidable; other four gates as
  reported in the latest CI run".
- Negative/mutation evidence: unchanged by this entry. `INV-003-signing` and `INV-007-advisory-authority` are still
  NOT RUN and must not be reported as passing.
- Debt changes: `debt-register.md` unchanged; the bootstrap deviation is now an explicit, dated item instead of an
  undocumented gap.
- Runtime fallback: reverting this entry and `ADR-B0006` restores the previous state — both gates red — with no effect on
  application code.
- Independent review: **not obtained in this entry**. D must record an exact-head review of PR #8 (non-author, account
  unohhh1) for the static-analysis requirement, and must confirm or reject the bootstrap boundary in writing.
- Verdict: **CHANGES REQUIRED** until (1) D's independent exact-head review is recorded, (2) PR #8 is merged with the
  active policy preserved, (3) B re-runs the six checks on the merged head and links the run. C does not approve their
  own governance change and does not sign for D.

## A follow-up to hosted B verification — 2026-11-23

At #14 revision 40e86b2, A audited #13's revised tests. Actual chat-user permission exists, but no independent pre-implementation tests-only GitHub approval was located. Tests and implementation were committed together in 328c381, after the cdd6ce7 bootstrap cutoff. D's later COMMENTED architecture/API acceptance is retained as scope review, not rewritten as prior approval. The chronology deviation is ready for inclusion in the process report; no approvals were backfilled.

A then attempted authorised live replay via the actual isolated worker. First case english-supported escalated with unavailable-provider reason after about 30 seconds, no provider usage/feedback; four cases were not run and no retry occurred. No-key diagnostics found WSL direct Python HTTPS TLS timeout while proxy-aware curl received a response. Runtime proxy support or a directly reachable reviewed runner needs a separate decision; no sandbox bypass was used. This failed candidate execution is not semantic quality acceptance or a trusted baseline.

The previously missing 25-call historical files are now supplied with hashes, explicitly pre-isolation and user-NOT-ACCEPTED. Full audit, execution evidence and report-ready paragraph: handoff/records/2026-11-23-A-post-B-review.md and artifacts/member-a-followup-20261123/. C/D must still freeze semantic scope; final exact-head approval remains pending.

2026-11-22 · B integration. The active policy on main at `cdd6ce7d25a2f937d2880140386ff22c96d387de` was retained without edits. GitHub reports main protected. The detailed protection and `test-baselines` endpoints returned HTTP 404 to the current credential, so use E/admin readback for the individual rules. Code-owner configuration and the frozen calculator path can be checked in this PR.

## Accepted replay for the release candidate

[PR #20](https://github.com/wyw-12345/CS5351/pull/20) contains the C/D-accepted replay from PR #17 at f1ea172. D approved a3063c3. The candidate preserves the same evidence blob, 9b36d685fe0fd7f62b60184aeede88076106d091. PR #20 still targets protected main and was awaiting all six required statuses when this integration was prepared. The release gate can read the reviewed replay only when the artifact is present at its trusted base.

This integration also preserves C's entire added AI-use entry. Its multiline source field uses YAML block syntax so GitHub PR number signs are retained as text.
