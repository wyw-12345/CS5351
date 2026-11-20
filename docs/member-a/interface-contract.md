# Member A interface — D ADR-0001..0004

Status: implemented for handoff; independent review pending. D's ADRs remain authoritative.

- `calculate_score(rubric, scores)` returns an exact weighted percentage rounded once to two decimals. The calculator is unchanged. Rubric is `{id, version, criteria:[{id, description, max_score, weight}]}`; 1–10 unique IDs, positive decimal-string weights summing exactly to 1.
- `evaluate(essay, rubric, prompt, settings, transport=...)` returns `{status, reason, feedback, metadata}`. `Settings` is injected by `cli.settings_from_env`. No environment or store import occurs in the engine.
- `validate_feedback(value, essay, rubric)` checks every criterion exactly once, bounded suggested scores, literal essay quotes, uncertainty and valid confidence. Confidence below 0.80 escalates; exactly 0.80 passes unless another check fails. A top-level model `final_score` is ignored; other unexpected fields fail.
- `GradeStore(path, trusted_keys=..., migrate_legacy=False)` exposes `create`, `get` and `approve`. `create(..., submission_id=...)` stores a proposal without a grade. Exact same-ID/content retries return the original record; conflicting content is refused.
- `approve(proposal_id, proposal_hash, scores, reviewer, reason='', approval=...)` verifies an Ed25519 signature against an external trusted-key allowlist. The signed binding contains submission ID, proposal hash, rubric ID/version and the confirmed-score hash, plus reviewer label/reason. The store independently verifies and recomputes, then atomically writes grade and audit. The reviewer label is not authentication. A complete score set plus reason and signature can resolve escalation.
- Reads revalidate content, signatures and calculated scores. Exact approval retries return the original record; changed scores/signatures cannot overwrite history. Explicit v1→v2 migration preserves historical unsigned records as `legacy_unverified`.
- AI input uses the existing 12,000-byte guard, 1,024-token output default, 30-second connected-operation timeout and zero retries. No compaction or token-cap implementation is claimed. DNS is outside the connected-socket deadline.

CLI commands: propose, show, sign, approve, migrate, keygen. Private keys and the trusted-key file are external; provisioning/rotation is the operator's responsibility. `config/model.json` documents the selected model/prompt and defaults, while environment variables supply actual runtime values. Tests use temporary synthetic keys, never real teacher credentials.

B should consume this API as frozen by ADR-0003 and reconcile its older flat names through its tests-only review workflow. No compatibility alias or second implementation is added.
