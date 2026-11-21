# Retry fixture correction following the first GitHub Actions run

Run [44778695021](https://github.com/wyw-12345/CS5351/actions/runs/44778695021) reached all six CI jobs on draft PR #8. The regression job found an error in B's test fixture on Ubuntu. It generated advisory feedback a second time and compared it as an exact retry. Regenerating advisory metadata could change `latency_ms` and caused the actual store to reject that conflicting submission.

The original test reproduced locally when the two evaluations were given different elapsed durations. This tests-only correction resubmits the original advice, checks the exact returned record after reopening the store, and asserts that changing either essay or advice still raises and leaves one unchanged grade. Existing A application behavior and rules remain intact. Any product-level decision about retrying after a fresh model call belongs in a separate A/D review.

Review and merge this test correction independently before bringing it into PR #8. That keeps the CI implementation diff separate from changes to tests inherited from main.
