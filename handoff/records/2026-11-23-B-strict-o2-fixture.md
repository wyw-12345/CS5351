# Strict O2 saved replay test fixture

Separate fixture-only review for REQ-GOV-B04, based on the protected #21 merge `fbe7081122188f6bb4117da21af1a5127e20660e`. Source diagnosis is A's [draft PR #22](https://github.com/wyw-12345/CS5351/pull/22) at `6137806cdb93d8e44cc3205e98bfa2a574eac912`.

The existing #18 test uses a synthetic `trusted-base` and mocks reading the saved replay contents. The new checker correctly probes whether a file exists at BASE before reading it. Without the fixture needed for that probe, Git reports that the synthetic name is not an object, and the test stops before strict O2 assertions. This proposal adds a narrow fixture for that exact Git query. The original positive acceptance and negative assertion after setting a numeric suggestion are retained. The #21 tests still check Git errors and authenticated fallback proof.

The existing locator `test/governance/test_b_gate_evidence.py::StrictO2Tests.test_reviewed_baseline_rechecks_cases_instead_of_trusting_saved_metrics` and its requirement mapping stay unchanged. The fixture file's blob changes. The original #18 record is the historical approval of its original blob. This revision requires independent approval and merge on its own. The current history and approval gates still evaluate the original and revised blobs separately. Any required release treatment must be handled transparently according to policy. Do not substitute this later correction into a prior approval entry.

After review and protected-baseline merge, supply the exact merge SHA to A. Preserve the #21 test and checker implementation when running the combined regression. There is no implementation, replay evidence, test-map, threshold, or approval flag change in this proposal.
