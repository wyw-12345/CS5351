# B verification contract for the current A implementation

Draft for exact-head review against `main` at `fab81cb`, including A `10f5b8d` and retrospective acceptance `5f05f01`.

- The calculator exposes `calculate_score` and is the final-score authority. The feedback engine exposes `evaluate` and `validate_feedback`, escalates invalid or low-confidence advice, and treats model totals as non-authoritative.
- The CLI injects settings using `settings_from_env`. The evaluator reads the reviewed prompt and dataset by their recorded fingerprints. Live calls require approved configuration and explicit opt-in.
- `GradeStore.create(..., submission_id=...)`, `get`, and `approve(..., approval=...)` use the actual A signature contract. Verify the exact signable binding under ADR-0002, signed audits, atomic recording and idempotent retries using synthetic keys.
- Match the versioned API/permission snapshots and actual E enforcement evidence before release. Grade-store isolation is a runtime property; document and import checks alone cannot demonstrate it.

See `docs/verification/test-map.yaml` for collected locators and evidence gaps. The draft neither authorizes runtime changes nor certifies the repository's prior merges.

2026-11-23 A isolation candidate: CLI proposes through scripts.advisory_worker.invoke_worker, not in-process evaluate. Settings lives in contracts (feedback_engine.Settings remains a compatible export). Existing advice/store interfaces remain unchanged. Deployment is Linux/WSL2 + bubblewrap, fail-closed elsewhere; the evaluator has no network/host data mounts and the trusted broker performs one endpoint request. See ADR-0006 amendment. Updated API snapshot is pending-independent-review, not approved by A. B must provision the OS dependency and review the changed contract before final gate rerun.
