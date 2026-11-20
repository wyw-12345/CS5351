# Structural constraints — module organization rules (D3)

> Owner: member E (coding governance). Status: D3 baseline — backfilled against D's
> `permission-model.md` and ADR-0003. Authority boundary is fixed; these rules are the enforceable
> expression of `REQ-GOV-E01/E02/E03`, `REQ-SEC-002/004/006` and `REQ-INV-003/007`.

These rules control **how** the coding agent organizes code so that the authority boundary
(advisory vs authoritative) is expressed in the file structure and stays enforceable by static checks.

## 1. One architectural element → exactly one module

| Architectural element | Module (file) | Authority |
|---|---|---|
| AI feedbacker | `src/feedback_engine.py` | advisory |
| deterministic calculator | `src/score_calculator.py` | authoritative (frozen) |
| grade store / audit | `src/grade_store.py` | authoritative write |
| human boundary / orchestration | `src/cli.py` | orchestration (non-authority) |
| shared validation helpers | `src/contracts.py` | non-authority |

- No architectural element may be split across multiple modules, and no module may host two elements.
- `cli.py` and `contracts.py` are **non-authority**: `cli.py` is the import/config-injection boundary;
  `contracts.py` holds the shared strict validators. Neither may perform an authoritative grade write.

## 2. New work extends the baseline; never replaces it

- A change to an existing module **adds or refines** its declared contract; it does not silently swap
  semantics, rename public functions, or change rounding/validation behavior without a reviewed
  contract change and a tests-only approval first (ADR-0003).
- Deleting or rewriting an existing test to hide a regression is forbidden (see `verification-constraints.md`).

## 3. Every module and function references its decision and invariant

- Each module docstring names the architecture decision (ADR-0001..0004) and the requirement IDs
  (REQ-*) it implements.
- Each public function docstring names the specific REQ/INV it satisfies, matching the IDs in
  `docs/req/requirements.yaml` (C baseline 0.1.0-c) and `docs/verification/test-map.yaml` (B).
- Traceability is verified by the schema gate and the test docstring check.

## 4. Authority boundaries as import rules

Enforced by `tools/gates.py safety` (B), updated by E per ADR-0003:

- `feedback_engine` must not import `grade_store`, `os`, `subprocess`, `pathlib`, `importlib`,
  `shutil`, or `builtins`; it must not use `eval`/`exec`/`open`/`compile`/`__import__`.
  → The advisory component cannot reach the authoritative store or the host filesystem/network.
  **`os` in `feedback_engine` is a HARD gate failure** (ADR-0003): config must be read at the `cli.py`
  caller boundary and passed in as a validated `Settings` value object. Current `src/feedback_engine.py`
  still imports `os` and must be refactored by A.
- `score_calculator` may import only `decimal`, `fractions` (ADR-0003, exact rounding), `typing`,
  `dataclasses`, `__future__`, `collections`, and shared `contracts`.
  → The authoritative calculator stays deterministic and has no LLM/network/filesystem dependency.
- `grade_store` is the **only** module that writes durable grade records; it must verify the approval
  signature against a trusted public key (ADR-0002) and persist atomically.

## 5. Ownership and edit rules

- Frozen / safety-critical paths (`src/score_calculator.py`, `src/grade_store.py`, `.opencode/*`,
  `.agent/*`, `.github/*`, `docs/verification/*`) require an ADR and independent human review.
- Permission and rule files are human-owned: an AI may draft content in `docs/member-e/` but must not
  edit the protected files or self-grant access (see `.opencode/permissions.jsonc`).
- `src/score_calculator.py` is **frozen** (REQ-GOV-E02): any change needs an ADR + human approval on the
  exact SHA.

## 6. Key and credential boundary (ADR-0002, REQ-SEC-004)

- The authorized teacher's **private signing key lives outside the repository** (OS keychain,
  `~/.gradeaide/`, or gpg-agent); it is never committed and never logged.
- The store verifies against a **trusted public-key allowlist** configured at the store boundary;
  an unknown key is **denied by default** (no fallback trust).
- Provisioning and key rotation are an operator (E) procedure, recorded out-of-band, never in code.

## 7. Runtime isolation (not just static checks)

- Static import checks are an early signal, **not** a sandbox. At runtime the advisory component
  (`feedback_engine`) runs least-privilege: no durable write, no host filesystem write, and network
  access limited to the single bounded model request to a configured endpoint (one attempt, no retry).
- The coding agent has no grade-data write tool and no arbitrary network tool (see
  `mcp-tool-manifest.md`).

## 8. Verification of these constraints

- Static import checks run on every push/PR (structural tier).
- Module→element mapping is checked by `docs/verification/api-surface.json` (B) once A's API is frozen.
- A secret scan must run in CI (REQ-SEC-004) — a real scan, not a manual grep-only check.
- Any PR touching safety-relevant paths must include updated contract, API and permission snapshots
  plus a current independent human approval of the exact head SHA.
