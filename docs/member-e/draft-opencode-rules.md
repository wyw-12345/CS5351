# Draft always-on behavioral rules (AI draft — historical)

> This is member E's **AI-authored draft** for the human-owned `.opencode/rules.md`.
> **SUPERSEDED 2026-11-16:** the owner (member E) has completed `.opencode/rules.md` from this draft,
> reconciled against `docs/req/requirements.yaml` (C 0.1.0-c), `docs/architecture/permission-model.md`
> and `adr/ADR-0001..0004`. This file is kept as the draft lineage; `.opencode/rules.md` is the active
> ruleset.

## Always-on rules for the coding agent

1. **Authority boundary first.** `feedback_engine` only advises; `score_calculator` is the sole
   authority for the final score; `grade_store` is the only writer of durable records. Never let a
   model total override the deterministic result, and never write a grade without a verified, bound
   human approval (ADR-0002 G1+G2).
2. **Escalate, never guess.** Missing / duplicated / unknown / uncertain / out-of-range advice, provider
   failure, and any criterion with `confidence` missing/invalid/`< 0.80` escalate to the teacher
   (`0.80` passes; ADR-0001). Do not silently default a score to zero or invent a criterion outside the
   rubric (REQ-SEC-002).
3. **Default-deny permissions.** Operate inside `.opencode/permissions.jsonc`; do not edit permission or
   rule files, and do not attempt to self-grant or broaden access.
4. **No secrets or keys.** Never read or write API keys, tokens, or the teacher signing key; obtain
   credentials only from the runtime environment; the private signing key lives outside the repo
   (REQ-SEC-004, ADR-0002). Never log or commit them.
5. **Tests before code.** Wait for a human-approved execution plan, then a reviewed tests-only PR, before
   implementing. Do not self-approve.
6. **Trace everything.** Append a substantive `docs/ai-use-log.yaml` entry for every code/prompt/gate
   change; name the REQ/ADR each module and test implements; never rewrite old log entries.
7. **Do not weaken evidence.** Never delete, rename, or relax a test to make a gate pass; never add fake
   application modules; never fabricate approvals, model calls, or transcripts.
8. **Freeze discipline.** Changing `score_calculator`, `grade_store`, permissions, CI, gates, or protected
   policy requires a new ADR and independent human approval of the exact head SHA.
9. **Config injection boundary.** `feedback_engine` must not import `os`; read config at the `cli.py`
   boundary and pass a validated `Settings` object in (ADR-0003). The calculator may use `fractions` for
   exact arithmetic.
10. **Runtime isolation.** The advisory component runs least-privilege: no durable write, no host
    filesystem write, network limited to the single bounded model request.
11. **Record truthfully.** State the actual agent, raw session path, and review status; do not relabel one
    agent's work as another's or claim a dry-run as enabled.

## Enforcement

- These rules are enforced by `.opencode/permissions.jsonc` (permissions), `tools/gates.py`
  (structural/safety/approval gates) and human review of safety-critical PRs.
- A human must approve this file before it becomes binding.
