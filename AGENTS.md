# AGENTS.md — GradeAide coding-agent governance (D3)

> **Owner:** member E (coding governance). **Status:** D3 governance baseline — backfilled against
> C's requirements baseline **0.1.0-c** (47 entries) and D's architecture baseline (blueprint +
> ADR-0001..0004). The fixed authority boundary is:
>
> > **AI is advisory; deterministic code is authoritative.**
> > `feedback_engine` proposes. `score_calculator` decides. `grade_store` persists only after a
> > verified, bound human approval. The AI never overrides a deterministic score.

Upstream status: C = `draft_ready`, D = `pending` (both no human signature). E's own governance files
are `draft_ready`; `.opencode/rules.md` and `.opencode/permissions.jsonc` are **human-owned** and still
require human completion/verification before A's work is treated as governed.

---

## 1. Build target

GradeAide grades one student essay against a teacher-supplied rubric:

1. Import an essay (UTF-8 text) + a rubric (criteria × weights) — `src/cli.py`, `src/contracts.py`.
2. **AI feedbacker** (`src/feedback_engine.py`) — a real LLM reads essay + rubric and returns
   per-criterion feedback, a *suggested* score, a `confidence` value and a quoted evidence span. Advisory.
3. **Deterministic calculator** (`src/score_calculator.py`) — weights the human-accepted scores and
   computes the *final* percentage. Authoritative. **Frozen.**
4. **Grade store** (`src/grade_store.py`) — recomputes the score, verifies an approval bound to the
   exact proposal, and atomically persists the grade plus an audit record. Authoritative write.
5. **Human boundary** (`src/cli.py`) — a trusted local teacher command line; reviewer identity is an
   audit label, authenticity comes from the verified signature (ADR-0002).

Components (each architectural element = exactly one module):

| Module | Role | Authority | Hard limits |
|---|---|---|---|
| `src/feedback_engine.py` | evaluate + validate advice | advisory | no grade-store write; **no `os`**; no `subprocess`/`pathlib`/`importlib`/`shutil`/`builtins`; model text is untrusted data |
| `src/score_calculator.py` | weighted sum → final score | authoritative | **frozen**; exact `Fraction`/`Decimal` arithmetic only; no LLM/network/filesystem/dynamic import |
| `src/grade_store.py` | recompute + persist audit | authoritative write | verified-approval only (G1+G2); atomic; idempotent; only durable grade writer |
| `src/contracts.py` | strict validation helpers | non-authority | shared JSON/Decimal/text validation |
| `src/cli.py` | import + orchestrate | human boundary | filesystem import; config injection boundary; never echoes secrets |

---

## 2. Reading order

Read the project in this order before generating any plan or code:

1. This file (`AGENTS.md`).
2. `architecture-blueprint.md` + `docs/architecture/adr/ADR-0001..0004` — D's master constraints,
   authority boundary, escalation policy, approval binding, interface consolidation, model context.
3. `docs/architecture/permission-model.md`, `invariants.md`, `trace-matrix.md`,
   `runtime-policy-catalog.md` — D's permission regions, invariant register, REQ→component→monitor map.
4. `docs/req/requirements.yaml` + `docs/req/req-schema.json` + `docs/req/requirement-id-map.yaml` —
   C's official 47-entry registry (baseline 0.1.0-c) and the A/B/E proposal merge map.
5. `docs/code-governance/structural-constraints.md` (module/import rules, E),
   `verification-constraints.md` (three-tier verification, B), `mcp-tool-manifest.md` (allowed tools, E).
6. `.opencode/permissions.jsonc`, `.opencode/rules.md` (human-owned), `.agent/rules.md` (covenant).
7. `docs/member-b/02-interface-contract.md` (B/E proposal; superseded where ADR-0003 differs) and
   `docs/verification/test-map.yaml`.
8. `Prompt.md` (A's startup prompt) — the single prompt to read after this file.

Never substitute a summary for actually reading these files.

---

## 3. Code baseline (snapshot 2026-11-12)

**Present:**
- C: `docs/req/*` — 47 requirements across seven types, schema, PRD, ID map, review record, validation.
- D: `architecture-blueprint.md` + `docs/architecture/*` — ADR-0001..0004, invariants, trace-matrix,
  permission-model, memory-design, runtime-policy-catalog, evaluation artifacts.
- A: `src/{cli,contracts,feedback_engine,grade_store,score_calculator}.py`, `prompts/`, `Prompt.md`,
  `test/offline`, `test/live`, `scripts/`, `examples/`, `evidence/` (incl. historical live evidence).
- B: `tools/` six gates, `test/governance`, `.github/workflows/ci.yml`, D4 docs, `docs/verification/*`.

**Not yet aligned (open follow-ups):**
- `src/feedback_engine.py` still imports `os` (ADR-0003 violation); A must move config injection to the CLI.
- `src/` emits no `confidence` field and has no `< 0.80` branch (ADR-0001 target).
- No signing/verification or `confirmed_scores_sha256` yet (ADR-0002 target).
- B's acceptance suite uses flat `calculate`/`validate_advice`/`record_grade`; A exposes
  `calculate_score`/`evaluate`/`validate_feedback`/`GradeStore` (ADR-0003; A/B must reconcile).
- Traceability gate is BLOCKED (33 of 47 IDs unmapped); `permissions-snapshot.json`/`api-surface.json` absent.

**Rule:** do not add fake modules, delete tests, or lower thresholds to turn checks green. Red checks
above are expected until A/B implement the ADR targets.

---

## 4. Readable / modifiable / frozen regions

| Region | State | Rule |
|---|---|---|
| `src/score_calculator.py` | **frozen** | change requires a new ADR + independent human approval on the exact SHA (REQ-GOV-E02) |
| `src/grade_store.py` | safety-critical | ADR + human review; only writer of durable grade records |
| `.opencode/permissions.jsonc`, `.opencode/rules.md`, `.agent/rules.md` | **human-owned / safety-critical** | AI drafts elsewhere; only a human edits/approves; no self-granting |
| `.github/workflows/ci.yml`, `.github/CODEOWNERS`, `docs/verification/*` | safety-critical | ADR + human review + updated snapshots |
| `src/feedback_engine.py` | modifiable under governance | tests-before-code; AI-use log; **no `os`**, no grade-store import |
| `src/cli.py`, `src/contracts.py` | modifiable under governance | config-injection boundary lives in `cli.py`; `contracts.py` is non-authority |
| `test/**` | modifiable under governance | **not** in an implementation PR (tests-only PR) |
| `docs/**`, `prompts/**`, `config/model.json` | modifiable under governance | versioned; no credentials |
| grade-store data dir (`data/`, `grades/`) | **runtime-write only** | written only by `grade_store`; agents never edit |

Default posture: **deny safety-critical writes, allow the whitelisted dev surface, ask for shell.**
Machine-readable form: `.opencode/permissions.jsonc` (human-owned, not yet approved).

---

## 5. Module organization and import rules

See `docs/code-governance/structural-constraints.md`. Summary (enforced by `tools/gates.py safety`):
- One architectural element → one module; new work extends the baseline, never replaces a contract.
- `feedback_engine` must not import `grade_store`, `os`, `subprocess`, `pathlib`, `importlib`, `shutil`,
  or `builtins`; and must not use `eval`/`exec`/`open`/`compile`/`__import__`.
- `score_calculator` may import only `decimal`, `fractions` (ADR-0003), `typing`, `dataclasses`,
  `__future__`, `collections`, and shared `contracts`.
- Config is read at the `cli.py` caller boundary and passed into `feedback_engine` as a validated
  `Settings` value object; `feedback_engine` must not read the environment.

---

## 6. Integration contracts (frozen by D in ADR-0003)

Authoritative over `docs/member-b/02-interface-contract.md` where they differ:
- Public surface: `score_calculator.calculate_score`, `feedback_engine.evaluate`,
  `feedback_engine.validate_feedback`, `grade_store.GradeStore.{create,approve,get}`, `contracts.*`.
- Rubric: `{id, version, criteria:[{id, description, max_score, weight}]}`, weights **strictly positive**,
  sum exactly 1 (zero-weight rejected).
- Precision: bounded decimal strings; **exact** `Fraction` accumulation; **one** final `ROUND_HALF_UP`
  to two decimals (no intermediate Decimal division).
- Submission identity: canonical key `submission_id`; identical content → idempotent return; different
  content under the same id → `ValueError`, original preserved.
- Escalation (ADR-0001): escalate on missing/duplicate/unknown/uncertain/out-of-range advice, provider
  failure, and any criterion with `confidence` missing/invalid/`< 0.80` (`0.80` passes). Escalation is a
  resolvable terminal state: a teacher may enter the complete score set + reason; the calculator computes.
- Approval (ADR-0002): **G1** (validate + recompute) and **G2** (verified signature over the binding
  `(submission_id, proposal_hash, rubric_id, rubric_version, confirmed_scores_sha256)` against a trusted
  public key). Reject unauthorized signer, changed scores, replay, stale proposal. Reviewer name is an
  audit label only.
- If the interface changes, return to D/A and update tests through a separate tests-only PR.

---

## 7. Verification requirements

Generated code must satisfy (details in `docs/code-governance/verification-constraints.md`):
- Every fit criterion has ≥ 1 test; every invariant has ≥ 1 test that **fails** when enforcement is
  removed; every test names its REQ/INV ID in its docstring.
- Offline (deterministic, no credentials) and live (real API) tests are separated.
- Three-tier verification: **structural** (imports/boundaries/permissions), **regression** (all prior
  suites), **behavioral** (fixed real-model set, zero safety escapes).
- Six blocking gates on `main` (B): test-approval, static-analysis, schema, semantic-evaluation,
  regression, ai-use-log.
- Tests-before-code: A first outputs an execution plan and waits for **human approval**, then a tests-only
  PR, then implements. An AI never self-approves.

---

## 8. Authority boundary (non-negotiable)

- **advisory:** feedback text + suggested scores + `confidence` from `feedback_engine`.
- **authoritative:** the final score from `score_calculator` and the persisted record from `grade_store`.
- Missing / duplicated / unknown / uncertain / low-confidence criteria → escalate, never a silent default.
- The AI's suggested total never overwrites the calculator's result; a stray `final_score` is ignored.

---

## 9. Security and key/credential boundary (E, ties to ADR-0002 / REQ-SEC-004)

- **No secrets in the repo** — API keys, signing keys, tokens are injected from the runtime environment
  only; never in `src/`, `prompts/`, `config/`, logs, CI artifacts, or the repository.
- **Trusted public key boundary:** the authorized teacher's **private signing key lives outside the
  repository** (e.g. OS keychain / `~/.gradeaide/` / gpg-agent); the store verifies against a **trusted
  public-key allowlist** configured at the store boundary. An unknown key is **denied by default**.
  Provisioning and rotation are an operator (E) task and are never committed.
- **Runtime isolation:** the advisory component runs least-privilege — no durable write, no host
  filesystem write, and network access limited to the single bounded model request to a configured
  endpoint. Static import checks are an early signal, **not** a sandbox; the runtime boundary is a
  separate, independently enforced control.

---

## 10. Hard rules for the coding agent

1. Default-deny permissions; do not edit permission/rule files or self-grant access.
2. Do not fake human approvals, review records, model calls, or raw transcripts.
3. Do not store API keys or signing keys anywhere in the repo; read them only from the runtime environment.
4. Append a substantive `docs/ai-use-log.yaml` entry for every code/prompt/gate change; never rewrite old entries.
5. Do not delete, rename, or relax existing tests to make a failing gate pass.
6. Safety-critical changes (calculator, grade store, feedback engine, permission files, CI, gates,
   protected policy) require a new ADR and independent human review of the exact head SHA.
7. Record the actual agent and raw session path; do not relabel one agent's work as another's.

---

## 11. E's open follow-ups (handed to A/B/human)

1. **`.opencode/rules.md` (human-owned)** is not yet approved; the AI draft is at
   `docs/member-e/draft-opencode-rules.md`. A human must complete and approve it.
2. **`.opencode/permissions.jsonc` syntax** must be verified against the installed OpenCode version.
3. **Gate updates (with B):** add `fractions` to the calculator allowlist; make `os` in `feedback_engine`
   a hard gate failure; add a real secret scan.
4. **Key provisioning/rotation** for ADR-0002 (trusted public-key allowlist) — operator procedure, not code.
5. **Runtime process/filesystem isolation** for the advisory component — documented, to be realized by A
   at deploy time.
6. **`permissions-snapshot.json` / `api-surface.json`** are B's integration evidence, to be produced once
   A's API is frozen.

Next owner to act: **A** (implement ADR-0001/0002/0003 targets), then **B** (re-point tests, snapshots),
with a human completing `.opencode/rules.md` and reviewing `.opencode/permissions.jsonc`.
