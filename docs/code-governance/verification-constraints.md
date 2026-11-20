# D4 — Verification constraints (owner B)

Status: B integration proposal against C 0.1.0-c and D ADR-0001/0002/0003. Independent human approval is pending; schema/map success is structural, not behavioral acceptance.

## Evidence and traceability

Every official requirement must have a unique REQ ID, a metric, a threshold and a verification procedure. Every fit criterion maps to at least one collected, non-skipped test. Every invariant has at least one adversarial test that demonstrably fails when its enforcement is removed. Every test names the REQ or invariant it checks in its docstring. C's registry, D's invariant register and trace matrix, B's `docs/verification/test-map.yaml`, collected tests and real runtime monitors must agree.

No application substitute may be added to make missing upstream code appear complete. Mocks are permitted for deterministic validator self-tests, explicitly labelled; real-model semantic evidence must use the live provider. Zero collected tests, skipped safety tests, missing artifacts, model errors and missing credentials are failures for the applicable release gate.

## Tier 1: structural

Run Ruff, mypy and dependency audit on every push/PR, including documentation-only changes. Check requirements schema, import boundaries and exact contract/API documentation. Feedback code may not import the grade store, filesystem write/network execution helpers or dynamically load forbidden modules; static checks are an early signal, not an OS sandbox. E must provide independently enforced runtime permissions. Calculator uses exact Fraction accumulation and one HALF_UP rounding per ADR-0003; deterministic contracts helpers are allowed, while network/LLM/filesystem calls are not.

Any PR changing calculator, grade store, feedback engine, permission files, CI, gate scripts or protected policy is safety-relevant: require a new/updated ADR and API/contract/permission snapshots, passing negative contract tests and a current independent human APPROVED review of the exact head SHA. The reviewer must be in the protected base branch's allowlist and must not be the PR author or a bot. Reject head-only edits that try to weaken the allowlist or claim their own approval.

## Tier 2: regression

Run `test/governance` and all historical `test/offline` suites on every change. Test deletion, rename or modification is prohibited in implementation PRs; use a separately reviewed tests-only baseline PR and preserve the superseded evidence. Run negative tests before and after a controlled mutation in a disposable workspace; a mutant that is not killed is a failed invariant verification. Do not alter production code automatically to run mutations on the working tree.

## Tier 3: behavioral

Replay the versioned fixed evaluation set on every prompt/model/feedback change. Use a real provider through A's actual `src.feedback_engine.evaluate(essay, rubric, prompt, settings)` and `validate_feedback` entry points under a separately reviewed configuration. Require rubric-ID coverage = 1, schema-valid responses = 1, all required essay evidence quotes supported by the essay, adversarial escalation rate = 1 and safety escapes = 0. These automated proxies do not prove pedagogical quality: the teacher must separately annotate relevance/faithfulness before release, with evaluation debt tracked explicitly. Persist model ID, prompt SHA-256, dataset SHA-256, case outputs, latency and failure detail as CI artifacts. No cached answers, no unconditional `continue-on-error`, no threshold lowering in the same change being evaluated.

## Approval and write boundary

The independent scoring oracle uses hand-calculated totals and exact ties (50.005 -> 50.01, 66.665 -> 66.67); do not duplicate the production calculator as the only oracle. Unknown/missing/duplicate criteria, invalid numbers and uncertainty escalate with no authoritative numeric score. Every authorized write recomputes its score and atomically records the advisory scores, final score, hashes, reviewer and approval binding. Rejected inputs must leave durable state unchanged.

Test approvals are obtained before implementation, in a tests-only PR; never let an agent fill an approval file and treat it as a signature. GitHub review API and merge ancestry are checked in CI. Commit timestamps can be falsified; the reviewer must inspect the raw session to verify actual ordering. No local script can fully establish when a human began coding.

## Change/release policy

Require the six named CI statuses and independent human review on `main`, dismiss stale approvals, require approval of the latest push, apply protection to administrators and prevent force push/deletion. Emergency exceptions require an explicit human-owned ADR and a subsequent audit; no agent may silently bypass a gate.

Live testing uses least-privilege API credentials through CI secrets. Fork PRs receive no secrets: the semantic gate fails with an actionable message, and maintainers rerun a reviewed trusted branch; never run untrusted head code with a write token. Artifacts must not include API keys or raw private student essays.

## Operational fallback

On authority/approval/audit violation: stop grade writes, quarantine the attempt, retain a privacy-safe diagnostic, notify the responsible teacher through the application workflow and require manual reconciliation. B's test runner reports the failure; it does not invent a notification service or claim the runtime fallback is implemented.



## 2026-11-17 integration additions

Scripts and relevant dependency manifests are implementation scope for prior tests and AI logging. Registry changes co-evolve with the ID map, architecture trace, test map, affected tests and log. API snapshots include constructors, method parameters, defaults, and source fingerprints. Secret-pattern scans never echo matches. Permission hashes bind actual documents; E must provide separate evidence for runtime enforcement. The A baseline already implements confidence, signing, and idempotency; pending real enforcement and mutation coverage still block release. B test signing keys are ephemeral. E/A manage real key custody.

The six-job rollout runs offline without provider credentials. Until the owners establish trusted live evidence and approve its replay configuration, semantic evaluation reports a blocking result.
