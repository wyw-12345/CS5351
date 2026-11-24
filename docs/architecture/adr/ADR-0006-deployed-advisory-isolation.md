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

## Initial acceptance cases

- `test_deployed_isolation_normal_path`: a valid essay+rubric through the worker returns advice (`decision` ready or escalate); the grade store is unchanged.
- `test_deployed_isolation_rejects_write`: the advisory process attempting to write into the grade-store data directory is denied; zero durable rows are created.
- `test_deployed_isolation_protection_removal_fails`: removing the process boundary (or the write denial) makes the rejection test fail — a real mutation, not a static check.

## Consequences

- INV-007 gains real runtime evidence beyond static import checks; `permissions-snapshot.json`'s `runtime_enforcement_verified` can then be backed by the deployment experiment.
- `src/cli.py` must be refactored so the authoritative process no longer loads the model/transport code in-process. This is an A implementation change gated by this ADR.
- The static import boundary and offline tests remain as early signals; they are complemented, not replaced, by the sandbox.

## Reopening

### Explicit trusted broker proxy follow-up — 2026-11-23

The seven proxy acceptance tests were independently approved by unohhh1 on #16 at 833140d and merged into test-baselines at 8347ebc before this implementation. Only the four reviewed implementation paths change. Evaluator namespaces, UID, mounts and network prohibition remain unchanged.

Optional GRADEAIDE_PROXY_URL selects a local HTTP CONNECT proxy, for example http://127.0.0.1:10808. The operator must configure it explicitly; the application ignores ambient HTTP_PROXY/HTTPS_PROXY. Only loopback HTTP addresses with a valid port are accepted, without userinfo, path, query or fragment. Tunnel mode requires a HTTPS model endpoint. HTTPSConnection retains its default target certificate and hostname validation; provider Authorization is sent inside the TLS tunnel, not in CONNECT. No extra package is required.

Proxy routing and the real API key stay in the trusted outer broker and are removed/replaced before the evaluator receives its settings. No direct-network fallback or retry is added. Independent review of the implementation and actual replay acceptance are separate from the already completed tests-only approval.

### A implementation amendment — 2026-11-23 (pending D review)

The actual user approved correcting the acceptance tests and proceeding with Linux/WSL2 implementation. This does not claim independent tests-only GitHub approval or final D review. The original third test was a no-op; executable tests now use the current rubric/advice schema and synthetic provider data.

Deployment uses bubblewrap 0.11.1 (tested in WSL2), Linux user/PID/mount/network namespaces, UID/GID 65534, dropped capabilities and a minimal read-only Python runtime/source view. No host home, .env, signing/trust files or grade directories are mounted during ordinary evaluation. Unsupported systems or missing bubblewrap refuse execution; there is no unprotected fallback. OS dependency: `sudo apt-get update && sudo apt-get install -y bubblewrap` on Debian/Ubuntu; availability and namespace support must be verified by the deployment operator/CI owner. No Python dependency was added.

Network amendment: the sandbox evaluator has **no network**, rather than direct endpoint egress. The outer worker is a small trusted transport broker: it validates settings, prepares at most one fixed model request using the existing budget checks, and calls the existing non-redirecting transport against only the operator-specified endpoint. Provider output is evaluated in the networkless sandbox. The model cannot supply an endpoint, tool or follow-up request. This broker is trusted orchestration, not arbitrary code execution containment for the broker itself. Host firewall confinement of a compromised broker is not claimed.

The API key exists only in the broker input, is replaced with a dummy value before sandbox IPC and is absent from inherited child environment. Both process stages use bounded JSON messages and deadlines; the CLI validates the returned advice shape and the store retains its existing authoritative validation/signature checks. Settings moved to shared contracts; feedback_engine.Settings remains a compatible import, while CLI no longer imports feedback_engine or invokes evaluate.

Operator-only `--probe-directory` mounts a disposable grade directory read-only and performs actual write/socket/adjacent-secret-read attempts as UID 65534. It is never sent by CLI, never disables protection and never touches production grade data in tests. The mutation replaces the actual sandbox launch with direct child execution only in a disposable copy; the same write-denial assertion then fails with written versus denied. This is measured process-enforcement evidence, not merely import matching.

Runtime command (Linux, repository root): `python3 -m src.cli propose --essay examples/essay.txt --rubric examples/rubric.json --fixture examples/provider-fixture.json --submission-id isolation-demo --db /tmp/gradeaide-demo.sqlite3`. Live mode omits `--fixture` and requires operator environment; no live call was performed for this implementation. Signing/approval commands remain in the trusted CLI process.

Evidence: `python3 -m unittest test.offline.test_deployed_isolation -v`; `python3 tools/check_suite.py test/offline`; `python3 tools/application_mutation_check.py`. Logs are under artifacts/isolation-20261123. D must independently review this amendment, and B must provision bubblewrap/user namespaces in CI before claiming gate readiness.

- If the team chooses a different isolation mechanism (container, separate service), record an amendment ADR.
- If the single-teacher CLI scope changes to multi-user, revisit identity, network and secret provisioning.

### D review and B verification handoff, 2026-11-23

D reviewed the networkless evaluator, trusted broker and API snapshot at PR #13 head `328c381`. B reran the four deployed acceptance tests and the isolation-removal mutation in WSL2. The regression job uses Ubuntu 26.04 and installs the packaged bubblewrap. It runs the real tests without a skip or a change to the host's namespace security policy.

E's first tests precede A's draft commit in Git. A revised those tests in the same commit as the implementation. The author-recorded chat approval and D's subsequent architecture review have separate scopes. Independent pre-implementation GitHub approval of the revised tests remains unverified.
