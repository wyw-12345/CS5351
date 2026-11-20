# .opencode/rules.md — always-on behavioral rules (D3)

> **Owner:** member E (coding governance). **Status:** completed 2026-11-16 by owner E.
> Content drafted with AI assistance and reconciled against C's requirements baseline **0.1.0-c**
> (47 entries) and D's architecture baseline (ADR-0001..0004). These are the project-level,
> always-on rules the coding agent reads on every turn.
>
> **Enforcement:** `.opencode/permissions.jsonc` (permission model), `tools/gates.py`
> (structural/safety/approval gates), and independent human review of safety-critical PRs.

## Rules (always on)

1. **Authority boundary first.** `feedback_engine` only advises; `score_calculator` is the sole
   authority for the final score; `grade_store` is the only writer of durable records. Never let a
   model total override the deterministic result, and never write a grade without a verified, bound
   human approval (`REQ-INV-001`, `REQ-INV-003`; ADR-0002 G1+G2).

2. **Escalate, never guess.** Missing / duplicated / unknown / uncertain / out-of-range advice,
   provider failure, and any criterion with `confidence` missing, invalid, or `< 0.80` all escalate to
   the teacher (`0.80` passes; ADR-0001). Never silently default a score to zero and never invent a
   criterion outside the rubric (`REQ-INV-002`, `REQ-SEC-002`, `REQ-FUNC-003`).

3. **Default-deny permissions.** Operate strictly inside `.opencode/permissions.jsonc`. Do not edit
   permission or rule files, and never self-grant or broaden your own access (`REQ-GOV-E01`).

4. **No secrets or keys in the repo.** Never read or write API keys, tokens, or the teacher signing
   key. Obtain credentials only from the runtime environment; the teacher private signing key lives
   **outside the repository** and is verified against a trusted public-key allowlist (`REQ-SEC-004`,
   ADR-0002). Never log or commit them.

5. **Tests before code.** Wait for a human-approved execution plan, then a reviewed tests-only PR,
   before implementing. Never self-approve (`REQ-GOV-B01`).

6. **Trace every change.** Append a substantive `docs/ai-use-log.yaml` entry for every code/prompt/gate
   change; name the REQ/ADR each module and test implements; never rewrite old log entries
   (`REQ-GOV-B06`).

7. **Never weaken evidence.** Never delete, rename, or relax a test to make a gate pass; never add fake
   application modules; never fabricate approvals, model calls, or transcripts (`REQ-GOV-B05`).

8. **Freeze discipline.** Changing `score_calculator`, `grade_store`, permission files, CI, gates, or
   protected policy requires a new/updated ADR and an independent human approval of the exact head SHA;
   `score_calculator` is frozen (`REQ-GOV-E02`).

9. **Config-injection boundary.** `feedback_engine` must not import `os`; read configuration at the
   `cli.py` caller boundary and pass a validated `Settings` value object into the engine. The calculator
   may use `fractions` for exact arithmetic alongside `decimal` (`REQ-SEC-006`, ADR-0003).

10. **Runtime isolation.** The advisory component runs least-privilege: no durable write, no host
    filesystem write, and network access limited to the single bounded model request to a configured
    endpoint (one attempt, no retry). Static import checks are an early signal, not a sandbox
    (`REQ-INV-007`, `REQ-PERF-002`).

11. **Record truthfully.** State the actual agent, raw session path, and review status. Do not relabel
    one agent's work as another's, and do not claim a dry-run or historical result as a fresh pass.

## Working definitions

- **advisory** = feedback text + suggested scores + `confidence` from `feedback_engine`.
- **authoritative** = the final score from `score_calculator` and the persisted record from `grade_store`.
- **escalation** = a resolvable terminal state: no numeric grade is produced; a teacher may resolve it
  by entering the complete confirmed score set plus a reason, and the calculator computes the total.

## Change policy

- This file is human-owned. Changes require the owner (member E) to edit and re-approve it, recorded in
  `handoff/records/` and `docs/review-memo.md`; an agent must not edit it or self-approve.
- A requirements (C) or architecture (D) change must be reflected here within one sprint
  (context freshness, `docs/member-e/draft-opencode-rules.md` lineage preserved for the AI draft).
