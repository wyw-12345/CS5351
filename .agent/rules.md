# .agent/rules.md — GradeAide project covenant (D3)

> Owner: member E (coding governance). Status: D3 baseline — backfilled against C 0.1.0-c and
> D ADR-0001..0004. The authority boundary is fixed regardless.

This covenant constrains every agent working on GradeAide. It applies to plan, code, and verify roles.

## 1. Abstraction limits

- Keep the module surface small: `feedback_engine`, `score_calculator`, `grade_store`, plus the
  non-authority `cli.py` and `contracts.py`. Do not introduce a framework, ORM, or service layer that
  dilutes the boundary.
- No UI/framework assumption; keep the implementation plain Python 3.12 under `src/`.
- The calculator stays pure exact arithmetic (`Fraction`/`Decimal`, ADR-0003); the feedbacker stays a
  thin validated wrapper around the model; the store stays the only durable writer.

## 2. Dependency constraints

- Dependencies are pinned and audited (`requirements-ci.txt`, `requirements-app.txt`). Add no dependency
  without a reviewed reason and a vulnerability audit.
- `feedback_engine` must not import `grade_store`/`os`/`subprocess`/`pathlib`/`importlib`/`shutil`/
  `builtins`; `score_calculator` may import only `decimal`/`fractions`/`typing`/`dataclasses`/
  `__future__`/`collections`/`contracts`. Enforced by `tools/gates.py safety`; **`os` in the engine is a
  hard gate failure** (ADR-0003).
- Config is read at the `cli.py` caller boundary and passed into the engine as a validated `Settings`
  value object; the engine never reads the environment.
- Secrets and signing keys are never a dependency of the repo; they are injected/provisioned at runtime.

## 3. Test independence

- Every feature ships at least one **negative** test that fails when its boundary is removed, plus its
  positive test.
- Offline (deterministic, no credentials) and live (real API) tests are separated.
- Tests may only be added/changed in a reviewed tests-only PR; they are never edited inside an
  implementation PR to excuse a failure.

## 4. Safety-critical changes

- Changing `src/score_calculator.py`, `src/grade_store.py`, `src/feedback_engine.py`'s contract,
  permission files, CI, gate scripts, or protected policy is safety-critical.
- Such a change requires a new/updated **architecture decision (ADR)** and an independent **human
  approval** of the exact head SHA; a bot or self-approval never counts.
- `src/score_calculator.py` is **frozen** (REQ-GOV-E02).

## 5. Key and credential boundary (ADR-0002, REQ-SEC-004)

- The teacher's **private signing key lives outside the repository** (OS keychain / `~/.gradeaide/` /
  gpg-agent) and is never committed or logged.
- The store verifies against a **trusted public-key allowlist**; an unknown key is denied by default.
- Key provisioning and rotation are a human/operator procedure, never an agent action.

## 6. Runtime isolation

- Static import checks are an early signal, not a sandbox. At runtime the advisory component runs
  least-privilege: no durable write, no host filesystem write, and network access limited to the single
  bounded model request to a configured endpoint (one attempt, no retry).

## 7. Context freshness

- These rules, `AGENTS.md`, and the permission files are reviewed and updated within **one sprint** of a
  requirements or architecture change.
- After any REQ/ADR change, verify that the affected module docstrings, `test-map.yaml`, and
  `ai-use-log.yaml` are updated in the same change; stale context is treated as a defect.

## 8. Truthfulness

- No fabricated approvals, review records, model calls, transcripts, or "green" results. Missing
  upstream artifacts and missing credentials are explicit failures, never silent passes.
