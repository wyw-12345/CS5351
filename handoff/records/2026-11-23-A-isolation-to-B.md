# A → B/D: ADR-0006 implementation candidate

Based on #8 head 77641eea585336b588d7f531db6d46de51079ed9; branch feat/member-a-isolation. Actual chat user approved correcting the inert acceptance tests and proceeding with implementation. This is not independent tests-only GitHub approval or final D acceptance; preserve that governance limitation.

## Changes

- Corrected E's legacy/no-op tests to exercise actual current advice, real denied filesystem/network/secret access and a targeted sandbox-removal mutant. Added malformed/oversized IPC and unsupported-platform rejection checks.
- Implemented scripts/advisory_worker.py: bounded one-shot JSON IPC; minimal Linux bubblewrap namespaces; UID/GID 65534; read-only runtime/code; no home, keys, .env or ordinary grade mounts; evaluator has no host network. Probe confirms a distinct network namespace, not merely an unreachable server.
- Trusted outer worker brokers at most one request to the operator-configured endpoint. Only validated response data enters the evaluator sandbox. Credentials are not provisioned to the sandbox. See explicit ADR network amendment; OS confinement of a compromised broker is not claimed.
- CLI uses worker for synthetic/live proposals and retains signing/store behavior. Settings moved to contracts, with the old feedback_engine.Settings import remaining available. CLI no longer imports feedback_engine.
- Added real deployed-isolation mutation to the formal application runner. Existing mutants retain prior behavior; the new mutant requires the expected written/denied AssertionError, not any arbitrary error exit.
- Refreshed API snapshot fingerprints/surfaces with status pending-independent-review. No frozen calculator, GradeStore signing rule, reviewer policy or permission file changed.

## Actual checks

Platform: WSL2 Linux, Python 3.14.4, bubblewrap 0.11.1. Windows Python 3.12 was used for lint/mypy/schema/secret scan, not as a simulated deployment.

| Check | Result |
| --- | --- |
| Revised isolated acceptance | 4 tests pass, including actual removal mutation |
| Full offline suite | 77 tests pass; prior CLI signing/restart flow included |
| Governance suite | 57 tests pass |
| Ruff E4/E7/E9/F | pass |
| mypy src/tools | pass |
| Schema / tracked secret-pattern scan | pass |
| Application mutation runner | 9 KILLED including deployed isolation; overall exit 1 because INV-003-unverified-write-prevention remains NOT RUN |

Logs: artifacts/isolation-20261123/. The whole suite was run after Settings relocation; the final added network-namespace assertion was rerun with all four acceptance tests. No live provider call, extra model budget or claim of all six green.

## Reproduction

On supported Debian/Ubuntu Linux, provision `bubblewrap` with `sudo apt-get update && sudo apt-get install -y bubblewrap`, install the existing app/CI requirements in the chosen Python environment, and confirm user namespaces are permitted. This adds an OS runtime dependency, no new Python package. Do not silently skip acceptance tests if the host cannot support isolation.

From repository root:

```sh
python3 -m unittest test.offline.test_deployed_isolation -v
python3 tools/check_suite.py test/offline
python3 tools/check_suite.py test/governance
python3 tools/application_mutation_check.py
```

Fixture demo (no provider calls):

```sh
python3 -m src.cli propose --essay examples/essay.txt --rubric examples/rubric.json --fixture examples/provider-fixture.json --submission-id isolation-demo --db /tmp/gradeaide-demo.sqlite3
```

Windows proposal execution now fails closed; run this deployment through Linux/WSL2. Existing key/sign/show commands remain authoritative CLI operations. Operator-only probe-directory is diagnostic, never passed by CLI, and never disables protection. Tests use disposable paths, not real grades.

## B/D next steps

1. Review the changed acceptance assertions and the explicit broker amendment; D reviews the trusted broker/evaluator boundary and exact candidate SHA.
2. B must ensure CI installs bubblewrap and supports user namespaces. Keep unsupported environments failing; do not replace runtime checks with import checks.
3. Independently review the API snapshot and contract before changing pending-independent-review to reviewed. Permission snapshot flags were not self-upgraded.
4. Review the INV-007 mutation output. INV-003 formal integration is still a separate obligation; this change does not mark it complete.
5. Historical bootstrap/test approval remains unresolved by implementation. The earlier C bootstrap branch was not treated as an approved merge; do not backfill approvals from this handoff.
6. Feedback source hash changed, so earlier model replay identity is not automatically reusable. Original semantic evidence remains unaccepted; resolve calibration/CI ingestion through the established review process before any new paid replay.
7. After reviews and remaining evidence, update actual final-head contracts/logs as needed and rerun six gates. Do not merge #8 merely because these application tests pass.
