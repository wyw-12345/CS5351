# A response to B's PR 14 feedback

Date: 2026-11-23. Evaluated integration revision: 40e86b2fb412acc3c1c681b712a544eeb1b3ee77. This follow-up changes evidence and documentation only, not runtime, tests, thresholds, policy or approval flags.

## 1. Pre-implementation approval audit

The actual conversation contains user approval to correct E's inert/legacy tests and proceed with Linux/WSL2 implementation on 2026-11-23. The scope was explicitly described as not equivalent to independently approved tests-only GitHub review. The implementation was then saved in 328c381cc12282e17a8dd2b521c5059fe2dfef41 at 2026-11-23 15:27:46 +08:00, including both the revised acceptance file and runtime implementation.

No independently approved and merged tests-only baseline for the revised file was located in the available conversation, branch records or #13 reviews. D's actual review of #13 is COMMENTED at 2026-11-23 07:54:44 UTC and accepts architecture/API, not prior testing approval. It postdates the implementation commit. PR #12 defines its historical scope at cdd6ce7; #13 is later. Preserve the empty implementation-approvals record and current ordering failure. User permission to proceed must not be relabeled an independent test-baseline review, and no new retrospective exception is claimed here.

Evidence: #13 commit/diff, handoff/records/2026-11-23-A-isolation-preimplementation-review.md, PR #13 body and D review https://github.com/wyw-12345/CS5351/pull/13#pullrequestreview-6018125808. Exact chat timestamps are not exported, so no invented timestamp/signature is attached.

## 2. Actual deployed live attempt

After a concrete five-request, USD 0.25 maximum proposal, the actual user replied “按照建议”. This authorizes candidate execution; it does not establish C/D's independent acceptance of open criteria. The run retained the current five cases and hard thresholds, separately planned English/Chinese metrics and retained the existing allowed reasons for unverifiable-data. No prompt/dataset/approval flag changed.

Entry point: scripts.advisory_worker.invoke_worker on 40e86b2, Linux/WSL2, Python 3.14.4, bubblewrap 0.11.1. No direct feedback-engine substitution, synthetic provider substitute or sandbox bypass was used. Credentials were injected over stdin, not written to evidence. Requested settings: deepseek-flash, thinking disabled, 12000 input bytes, 1024 output tokens, timeout 30 seconds, no retry; conservative configured USD prices 0.30/1.20 per million tokens and max_cost 0.05 per call.

Result: english-supported attempted one request, returned escalation invalid_or_unavailable_provider_response after approximately 30 seconds, feedback=null, usage=null. The semantic checks failed. Stopped immediately; remaining four cases NOT RUN. No additional performance loop or paid retry. Actual provider cost is unknown because no usage was returned; do not infer zero charge. This is failed execution evidence, not an accepted baseline or a grading-quality failure.

Before the paid attempt, a WSL Git metadata preflight failed because this worktree's .git path uses Windows absolute paths. No provider call occurred in that preflight. The real run therefore used a candidate SHA verified by Windows Git and recorded both raw and LF-normalized fingerprints of actual runtime/config/input files. This avoids pretending WSL Git independently resolved the Windows worktree metadata.

Record: artifacts/member-a-followup-20261123/deployed-live-replay.json. It contains actual advice, timing, checks, raw/LF hashes, candidate/entry point and explicit not-run case IDs. real_provider=false means no successful provider reply was established; real_provider_attempt=true records the actual attempt.

## 3. No-key network diagnosis

WSL DNS resolved api.deepseek.com. curl using its configured local environment proxy received an HTTP response. A separate direct Python HTTPS HEAD without credentials timed out during TLS handshake. The current broker's http.client transport uses direct connections and does not consume proxy environment settings. This supports an environment direct-connect problem; provider health or a universal network failure is not proven.

Recommended next choice for approval: either use a reviewed Linux execution environment that can reach the endpoint directly, or propose explicit trusted broker proxy configuration with TLS endpoint verification, one-request/no-redirect enforcement, deadline tests and credential redaction. The evaluator must remain networkless. Proxy support would be a new runtime change and needs genuine approved tests before implementation; do not add it ad hoc to turn this run green. Do not simply raise timeout or remove isolation without approval. No extra model call is authorized by this handoff.

## 4. Historical evidence now supplied for B inspection

B could not locate the earlier 25-call result in the candidate. Copies are now under artifacts/member-a-followup-20261123/historical-pre-isolation/, with SHA256 inventory historical-evidence-manifest.json. They are the original five formal + twenty performance outputs for candidate 6323cbc and their execution/acceptance summaries. They remain explicitly NOT ACCEPTED and cannot substitute for a deployed-worker replay. No teacher data, API key, .env or signing key is included.

## 5. C/D decisions still required

- Confirm whether current five-case safety/status scope is acceptable, or calibration is required before acceptance. The prior actual user decision was non-acceptance pending review.
- Freeze English/Chinese aggregation (proposed: report both groups with existing 1.0 thresholds) and unverifiable-data reasons (currently low_confidence or uncertain_criterion). Do not silently narrow the dataset during execution.
- Review normalized runtime identity and trusted baseline ingestion. Raw historical hashes are preserved; no LF hash was substituted into old evidence.
- Freeze final candidate SHA and obtain actual final independent review after changes. D's architecture/API comment on #13 is not final #8 approval.

## 6. Report-ready process deviation paragraph

The isolation follow-up exposed a second approval-order deviation. In PR #13, the revised acceptance tests and worker implementation were saved together in commit 328c381, after the bootstrap boundary proposed in PR #12. The user had authorised the correction and implementation, but no independently approved tests-only baseline was identified. Hosted CI subsequently passed 77 offline tests and 57 governance tests and detected the isolation and approval mutations; the approval and regression-history gates still rejected the chronology. We retained the failed gate results and documented the deviation rather than backfilling an approval record. This distinguished evidence of working behaviour from compliance with the agreed development sequence.

Use this paragraph in A's implementation/reflection or E/B's process section; avoid repeating it throughout the report. Do not report six-green or successful deployed live replay.

## 7. Handoff status

A completed the available approval-record audit, supplied the missing historical evidence and performed one authorised deployed attempt. The run revealed a network/environment blocker and was stopped honestly. Current deliverable is ready for B/C/D review, not production acceptance. B's already successful 12-mutant and hosted suite results are acknowledged; A did not change or rerun those implementations in this follow-up. #8/#13/#14 remain unmerged at inspection.
