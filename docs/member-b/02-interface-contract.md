# B verification contract for the current A implementation

2026-11-23 approved proxy follow-up: Settings adds optional proxy_url, default None; CLI reads only explicit GRADEAIDE_PROXY_URL. A configured proxy must be loopback HTTP with a port and no credentials/path/query/fragment, and the model endpoint must be HTTPS. Broker uses CONNECT without provider credentials, retains target TLS verification and removes proxy_url before sandbox IPC. No ambient HTTP(S)_PROXY inheritance, retry, redirect or new dependency. Reviewed tests/locators are unchanged from #16 merge 8347ebcee949572adc6ff824a79c2c8ba6ea6d43. The refreshed API snapshot awaits exact-head implementation review.

Draft for exact-head review against `main` at `fab81cb`, including A `10f5b8d` and retrospective acceptance `5f05f01`.

- The calculator exposes `calculate_score` and is the final-score authority. The feedback engine exposes `evaluate` and `validate_feedback`, escalates invalid or low-confidence advice, and treats model totals as non-authoritative.
- The CLI injects settings using `settings_from_env`. The evaluator reads the reviewed prompt and dataset by their recorded fingerprints. Live calls require approved configuration and explicit opt-in.
- `GradeStore.create(..., submission_id=...)`, `get`, and `approve(..., approval=...)` use the actual A signature contract. Verify the exact signable binding under ADR-0002, signed audits, atomic recording and idempotent retries using synthetic keys.
- Match the versioned API/permission snapshots and actual E enforcement evidence before release. Grade-store isolation is a runtime property; document and import checks alone cannot demonstrate it.

See `docs/verification/test-map.yaml` for collected locators and evidence gaps. The draft neither authorizes runtime changes nor certifies the repository's prior merges.

2026-11-23 A isolation candidate: `src.cli` proposes through `scripts.advisory_worker.invoke_worker`. Settings lives in `src.contracts`, with `feedback_engine.Settings` retained as a compatible export. The advice and store interfaces remain compatible. Deployment requires Linux and bubblewrap and fails closed if isolation is unavailable. The evaluator has no host network or grade-store mount. The trusted broker makes at most one request to the configured endpoint. See ADR-0006. D confirmed the architecture and API snapshot for PR #13 at `328c381`. B added the bubblewrap installation to the regression job and mapped the deployment tests. PR #8 still requires formal approval on its final head.

2026-11-23 B checker follow-up: offline CI reads accepted case outputs from the supplied base revision and recomputes the verdict against the current fixed case definitions. Strict O2 requires escalation, uncertainty and a null suggestion for the unverifiable-data case. The reviewers assess the explanation. Authorized live validation uses the same deployed worker as the CLI. The runtime modules remain byte-identical to the replayed revision.

2026-11-23 A reviewed HEAD fallback candidate: `load_reviewed_baseline(base, api=None)` is internal verification tooling. BASE evidence wins; only path absence permits the independently approved PR20 artifact, bound to HEAD by immutable Git blob identity. Existing replay validation and deployed interfaces are unchanged. ADR-B0007 records the proof and the existing strict-O2 fixture compatibility blocker.
