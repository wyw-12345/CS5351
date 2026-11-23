# A isolation intake: executable acceptance corrections

Source: PR #8 HEAD 77641eea585336b588d7f531db6d46de51079ed9. Status: proposed, actual user approval requested before test correction and runtime implementation. Existing E files are unchanged.

Actual baseline execution: `python -m unittest test.offline.test_deployed_isolation -v` collected three tests: normal/write-denial failed because worker does not exist; mutation test passed despite worker being absent. That test checks an initially empty directory and assertTrue(True); it provides no mutation evidence.

Other confirmed test-contract gaps: rubric is a legacy list rather than the current versioned object; no valid Settings or provider fixture is supplied; only legacy decision ready/escalate is checked, not the current status/feedback/reason/metadata contract. A constant escalation implementation could pass the current two substantive assertions without evaluating any essay or denying any actual attempted write.

Proposed corrections, retaining three acceptance intentions:

1. Normal path uses the actual rubric/prompt/Settings contract and a synthetic provider response; assert a separate PID and schema-valid pending_review result, no grade writes, no credentials printed. Preserve the CLI/store's current advice contract; do not add legacy decision aliases to production merely to satisfy stale tests.
2. Denial path performs a real attempted filesystem write from inside the deployed sandbox against a temporary grade directory; prove the operation was attempted and denied, directory/database unchanged. Do not implement a write_probe response that simply reports denied without attempting a write.
3. Mutation test copies the implementation into a disposable tree, verifies the rejection test passes, removes only actual deployment enforcement, then invokes the same rejection assertion and requires a targeted assertion failure. An absent executable, syntax/import error or timeout is not a killed mutant. Never enable unsafe mode on the production CLI or accept an untrusted JSON flag that disables isolation.

Deployment design to review: Linux/WSL2 is available and bubblewrap is installed. Worker must fail closed on unsupported platforms or unavailable enforcement, not silently run unprotected. Use a minimal read-only runtime/repository view, no .env/signing/trust/grade directories, stripped inherited environment, bounded JSON stdin/stdout and timeout. A separate process running under the same unrestricted identity is insufficient. Network confinement must be measured at the enforced boundary; a Python hostname check alone is not OS egress restriction. If network is mediated by a broker, amend ADR-0006 explicitly rather than claiming the current direct-network design was implemented unchanged. No new Python dependency is necessary for process orchestration; bubblewrap is an OS deployment dependency and its configuration/version must be documented and verified.

CLI scope after acceptance approval: invoke worker instead of evaluate in-process; keep fixture mode working through the same IPC with an explicit synthetic envelope; validate both incoming/outgoing structures, bounds, bad/extra output and process failure. Keep `settings_from_env` compatibility for existing live/evaluation callers; removing in-process evaluate does not itself require moving every Settings caller. Never touch frozen calculator or grade signing logic.

After implementation: run corrected acceptance on supported Linux, full prior offline/governance suites, lint/types and real INV-007 mutation. Record Windows unsupported behavior separately; no fake skip/pass claim. Update actual API snapshots/contracts/log only for real changes and leave final safety review to D/B. Do not mark runtime verified or all six green before measured evidence.

This intake does not approve a tests-only PR, change E's ADR, implement the worker or satisfy missing historical approvals. It isolates the concrete acceptance decision needed before governed implementation.
