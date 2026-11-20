# Member E → A handoff: governance review of A's implementation + remaining E/A items

> Owner: member E (coding governance). Status: D3 baseline — backfilled against C 0.1.0-c and
> D ADR-0001..0004. A's `src/` implementation is already merged; this note records what A must still
> align to E's governance and what remains human-owned.

Read `AGENTS.md` first, then `docs/code-governance/structural-constraints.md`,
`docs/code-governance/verification-constraints.md`, `docs/code-governance/mcp-tool-manifest.md`,
`.opencode/permissions.jsonc`, `.agent/rules.md`.

## 1. Non-negotiables A must satisfy (from D's ADRs, enforced by E/B)

1. **Authority boundary:** `feedback_engine` advisory, `score_calculator` authoritative+frozen,
   `grade_store` sole durable writer with verified approval. Missing/unknown/uncertain/low-confidence
   criteria escalate — never a silent score.
2. **`os` must leave `feedback_engine`** (ADR-0003): config is read at `src/cli.py` and passed in as a
   validated `Settings` value object. This is a **hard gate failure** in `tools/gates.py safety` once B
   updates it.
3. **Calculator allowlist** now includes `fractions` (ADR-0003, exact rounding) alongside `decimal`; it
   keeps no LLM/network/filesystem/dynamic import (REQ-SEC-006).
4. **Confidence (ADR-0001):** add the required per-criterion `confidence` field and the `< 0.80`
   escalation branch (exactly `0.80` passes).
5. **Signing approval (ADR-0002):** implement G2 — signature over
   `(submission_id, proposal_hash, rubric_id, rubric_version, confirmed_scores_sha256)` verified against
   a trusted public key; reject unauthorized signer, changed scores, replay, stale proposal.
6. **No secrets/keys in the repo** (REQ-SEC-004); the teacher private key lives outside the repo.

## 2. What E still owns (not A, not the AI)

- Complete `.opencode/rules.md` (human-owned) from `docs/member-e/draft-opencode-rules.md`.
- Verify `.opencode/permissions.jsonc` against the installed OpenCode version.
- Define key provisioning/rotation and the trusted public-key allowlist (ADR-0002).
- Realize runtime process/filesystem isolation for the advisory component at deploy time.
- With B: add `fractions` to the calculator allowlist, make `os`-in-engine a hard gate failure, add a
  real secret scan; then produce `docs/verification/api-surface.json` and
  `docs/verification/permissions-snapshot.json` (bind `permissions_sha256` + `feedback_grade_store_write=false`).

## 3. Backward-iteration note

- B's acceptance suite (`test/offline/test_authority_boundary.py`) still uses flat
  `calculate`/`validate_advice`/`record_grade`; A exposes `calculate_score`/`evaluate`/
  `validate_feedback`/`GradeStore`. D froze A's surface in ADR-0003. Reconcile through a **tests-only PR**
  (A exposes compatible names or B re-points tests) — never silently diverge from the contract.

## 4. Files E delivered this round

`AGENTS.md`, `docs/code-governance/structural-constraints.md`, `docs/code-governance/mcp-tool-manifest.md`,
`.opencode/permissions.jsonc`, `.opencode/rules.md` (human-owned stub), `.agent/rules.md`,
`docs/member-e/draft-opencode-rules.md`.
