# B verification contract for the current A implementation

Draft for exact-head review against `main` at `fab81cb`, including A `10f5b8d` and retrospective acceptance `5f05f01`.

- The calculator exposes `calculate_score` and is the final-score authority. The feedback engine exposes `evaluate` and `validate_feedback`, escalates invalid or low-confidence advice, and treats model totals as non-authoritative.
- The CLI injects settings using `settings_from_env`. The evaluator reads the reviewed prompt and dataset by their recorded fingerprints. Live calls require approved configuration and explicit opt-in.
- `GradeStore.create(..., submission_id=...)`, `get`, and `approve(..., approval=...)` use the actual A signature contract. Verify the exact signable binding under ADR-0002, signed audits, atomic recording and idempotent retries using synthetic keys.
- Match the versioned API/permission snapshots and actual E enforcement evidence before release. Grade-store isolation is a runtime property; document and import checks alone cannot demonstrate it.

See `docs/verification/test-map.yaml` for collected locators and evidence gaps. The draft neither authorizes runtime changes nor certifies the repository's prior merges.

2026-11-23 A isolation candidate: `src.cli` proposes through `scripts.advisory_worker.invoke_worker`. Settings lives in `src.contracts`, with `feedback_engine.Settings` retained as a compatible export. The advice and store interfaces remain compatible. Deployment requires Linux and bubblewrap and fails closed if isolation is unavailable. The evaluator has no host network or grade-store mount. The trusted broker makes at most one request to the configured endpoint. See ADR-0006. D confirmed the architecture and API snapshot for PR #13 at `328c381`. B added the bubblewrap installation to the regression job and mapped the deployment tests. PR #8 still requires formal approval on its final head.
