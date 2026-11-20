# Review memo register

## B-PREP-001 — initial local preparation

- Date: 2026-11-06, Asia/Shanghai. PR: none. Authoring agent: Codex. Human reviewer: not yet assigned.
- Spec alignment: scoped to B's D4/D7 and invariant elicitation; official registry and genuine AI application absent.
- Architecture alignment: proposed advisory/calculator/store boundary matches team allocation; D's decisions pending.
- Code/test quality: 35 gate-tool self-tests pass, 6/6 gate-tool mutants killed; lint/type/dependency checks pass. See `docs/member-b/VALIDATION.md` for actual results and limits. Application tests fail because A has not delivered.
- Security: review allowlists come from base branch; no approval is fabricated; secrets excluded.
- Efficiency: deterministic tests require no model calls; changed prompt/model/feedback triggers bounded live evaluation.
- Operational metadata: remote URL, PR review IDs, protection readback and real live-model run absent.
- Verdict: **CHANGES REQUIRED** for integrated system acceptance. This is an agent preparation review, not a signed human PR approval.

## Required memo for each future PR

Record PR URL, base/head SHA, author, real reviewer identity, date, changed REQ/ADR/INV, spec and architecture alignment, code and independent test quality, security/privacy, latency/token/cost, six gate run URLs, negative/mutation evidence, debt changes and runtime fallback. End with exactly APPROVE, CHANGES REQUIRED or REJECT and a rationale. Never backfill another person's approval.



## B-INTEGRATION-20261117 — local draft supplement

- Source: latest supplied ABCDE 2026-11-12; authoring agents Codex and real OpenCode 1.19.5 sessions, accurately separated in supplement provenance. PR and independent reviewer: not yet supplied.
- Spec/architecture: 47 formal IDs have candidate locators and exact docstrings; package API, 0.80 boundary, signed binding and idempotency follow D targets. API/key encoding seam still needs A agreement.
- Verification: 43 governance tests pass; A 45 legacy tests pass; offline 76 methods contain 19 failing methods (25 subtest failure entries), no import errors. Ruff and mypy 16 files pass after type-only fixes. 6 gate and 5 implemented application mutants killed; 3 application obligations NOT RUN.
- Security: no application live calls or policy activation, human-owned files preserved; snapshot enforcement flags remain false. New test-only crypto dependencies audited with zero known vulnerabilities.
- Efficiency: new local 1000-call calculator p95 0.1799 ms; old live evidence remains historical and not teacher-approved.
- Verdict: CHANGES REQUIRED for release; review-ready B tests and unmerged gate/CI proposals delivered. This entry is agent review, not a human signature.
