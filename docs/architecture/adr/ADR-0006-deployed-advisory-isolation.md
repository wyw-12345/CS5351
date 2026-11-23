# ADR-0006 — Deployed advisory isolation (INV-007 runtime boundary)

- Status: Proposed (E draft; A implementation + D review pending)
- Date: 2026-11-23
- Owner: E (governance); implemented by A; reviewed by D
- Relates: REQ-INV-007, REQ-SEC-006, ADR-0002, ADR-0004, `docs/architecture/permission-model.md`

## Context

REQ-INV-007 requires the advisory feedback component to have no grade-store write authority and to be unable to execute instructions embedded in essays or model text. Today this is enforced only by **static import boundaries** (`tools/gates.py check_imports` forbids `os`/`subprocess`/`grade_store`/etc.) and offline tests (`test_prompt_injection_stays_advisory`). `src/cli.py` orchestrates `feedback_engine.evaluate` and `GradeStore` **in the same process**, so a static import rule is not a process/OS permission boundary.

A's handoff (2026-11-23) flags INV-007 "deployed advisory isolation" as the missing runtime evidence: the mutation "remove the deployed protection" has no test, and no deployment launcher exists. `permissions-snapshot.json`'s `runtime_enforcement_verified` flag is therefore backed only by configuration, not by a deployment experiment.

## Decision

1. **Process boundary.** The advisory evaluator runs as a **separate process** from the CLI / grade-store process. The CLI launches it and exchanges a **single, length-bounded JSON request/response over stdio**; it never imports the evaluator's code into the authoritative process.
2. **Launcher.** `scripts/advisory_worker.py` is the sole entry point of the advisory process. It reads `{essay, rubric, prompt, settings}` from stdin, performs the single bounded model request, and writes the advice envelope to stdout. It must not import `grade_store` or `cli`.
3. **Identity & permissions.** In the deployed sandbox, the advisory process runs under a **dedicated least-privilege account** with:
   - read-only access to the essay/rubric/prompt/config inputs;
   - **no write** to the grade-store data directory (`data/`, `grades/`);
   - network egress limited to the configured model endpoint only (one attempt, no retry).
4. **Protected inputs.** The advisory account has no access to signing keys (`~/.gradeaide/`) or `.env`.
5. **Structured IPC contract.** Both ends schema-validate the wire messages. A malformed or oversized response is treated as escalation (`invalid_or_unavailable_provider_response`) and is never executed.

## Acceptance tests (added with implementation, tests-before-code)

- `test_deployed_isolation_normal_path`: a valid essay+rubric through the worker returns advice (`decision` ready or escalate); the grade store is unchanged.
- `test_deployed_isolation_rejects_write`: the advisory process attempting to write into the grade-store data directory is denied; zero durable rows are created.
- `test_deployed_isolation_protection_removal_fails`: removing the process boundary (or the write denial) makes the rejection test fail — a real mutation, not a static check.

## Consequences

- INV-007 gains real runtime evidence beyond static import checks; `permissions-snapshot.json`'s `runtime_enforcement_verified` can then be backed by the deployment experiment.
- `src/cli.py` must be refactored so the authoritative process no longer loads the model/transport code in-process. This is an A implementation change gated by this ADR.
- The static import boundary and offline tests remain as early signals; they are complemented, not replaced, by the sandbox.

## Reopening

- If the team chooses a different isolation mechanism (container, separate service), record an amendment ADR.
- If the single-teacher CLI scope changes to multi-user, revisit identity, network and secret provisioning.
