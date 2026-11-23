# B gate evidence tests

Base: protected `test-baselines` at `8347ebcee949572adc6ff824a79c2c8ba6ea6d43`. This change supplies tests and scope for independent review before B begins the checker implementation. Existing app code, approved A tests, gate implementations, thresholds and approval flags are unchanged.

## Observed failures

- GitHub Actions on PR #17 failed approval with missing `merge_commit_sha`. A's readback shows the same merged PR #16 contains the SHA in API version `2022-11-28` and omits it in `2026-03-10`. The fixtures allow a matching authenticated readback of the same PR and exercise rejection of missing, mismatched or non-ancestral evidence. Do not read a fallback SHA from an implementation branch's self-declared approval record. [Approval job](https://github.com/wyw-12345/CS5351/actions/runs/45145415318/job/137593363273)
- Strict O2 requires both uncertainty and a null suggestion on `unverifiable-data`, with either reviewed escalation reason. The existing checker accepts either field by itself. It also accepts stored result flags without recomputing the case verdict. The fixtures cover both positive reasons, both field violations and a stale pass flag that hides a scored result. Other escalation rules and the aggregate thresholds remain as specified. The missing-data explanation requires human review of the actual feedback. [C/D criteria](https://github.com/wyw-12345/CS5351/pull/12)

Python 3.12 local baseline: run `python -m unittest test.governance.test_b_gate_evidence -v`. Ten tests collected. Three pass, four reproduce the missing-key error, and three demonstrate the old semantic acceptance behavior. Strict traceability validation passes for all 47 requirements.

## Replay intake

The evidence in PR #17 at `d47830d` names source `2e135bf`. B verified 9/9 recorded LF-normalized input and runtime fingerprints, all five case IDs, all overall structural thresholds, and both required O2 fields. The A proxy acceptance test blob matches the reviewed `8347ebc` baseline exactly. C's PR comment records the wording review and acceptance. The machine artifact still showed C and D as pending when inspected. B did not invoke the provider or approve the artifact on behalf of either assessor. [Replay evidence and C's review](https://github.com/wyw-12345/CS5351/pull/17#issuecomment-7096470436)

After independent approval, merge these tests into the protected baseline and start a separate B implementation from the resulting merge SHA. Enable the model configuration only after both human acceptances and identity checks. Offline CI currently reads a saved baseline only on the trusted-base path and requests a live replay for model or feedback changes. If the accepted candidate needs a new evidence-consumption route, review its trust model separately and keep the PR worker credential-free.

The API fix establishes compatibility for actual approved test merges. It does not resolve the early #8 history or the #13 isolation-test deviation. The final integrated PR must demonstrate legitimate per-scope chronology or document the unresolved failure accurately.
