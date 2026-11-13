# Permission model (D2)

> Owner: D (architecture). Enforced by: E (`.opencode/*`, gates), B (CI). Companion to
> `docs/code-governance/structural-constraints.md` and `.opencode/permissions.jsonc` (human-owned,
> **not yet approved**).
>
> Core rule: **default-deny; allow the whitelisted dev surface; ask for shell; no AI self-grant.**

## 1. Principles

1. **Deny by default.** Every path/tool is denied unless explicitly whitelisted for the role.
2. **Human-owned policy.** Permission/rule files are edited only by a human; an AI may draft in
   `docs/member-e/` but never edit the protected files or broaden its own access.
3. **Least privilege per module** (see import rules §4).
4. **Runtime permissions > static checks.** Static import checks are an early signal; E must provide
   independently enforced process/filesystem permissions.

## 2. Actors and authority

| Actor | Read | Write | Cannot |
|---|---|---|---|
| AI feedbacker (runtime) | essay+rubric (args) | nothing durable | write grade store; import fs/net-exec helpers |
| AI coding agent (dev) | repo under governance | whitelisted dev surface | edit `.opencode/*`, `.agent/*`, `.github/*`, frozen modules; self-approve; delete tests |
| Teacher (human) | proposals, grades | approve/resolve via CLI | (local trust anchor) — identity is an audit label this release |
| CI/gates (B) | repo + artifacts | CI status, snapshots | fabricate human approval |

## 3. Filesystem permission regions

| Region | State | Rule |
|---|---|---|
| `src/score_calculator.py` | **frozen** | change needs ADR + independent human approval on exact SHA |
| `src/grade_store.py` | safety-critical | ADR + human review; only writer of durable grade records |
| `.opencode/permissions.jsonc`, `.opencode/rules.md`, `.agent/rules.md` | **human-owned** | AI drafts elsewhere; no self-granting |
| `.github/workflows/ci.yml`, `.github/CODEOWNERS`, `docs/verification/*` | safety-critical | ADR + review + updated snapshots |
| `src/feedback_engine.py` | modifiable under governance | tests-before-code; AI-use log; **no `os`** (ADR-0003) |
| `src/cli.py`, `src/contracts.py` | modifiable under governance | config injection boundary lives here |
| `test/**` | modifiable under governance | **not** in an implementation PR (tests-only PR) |
| `docs/**`, `prompts/**`, `config/model.json` | modifiable under governance | versioned; no credentials |
| grade-store data dir (`data/`, `grades/`) | **runtime-write only** | written only by `grade_store`; agents never edit |

## 4. Module import rules (authority as code)

Enforced by `tools/gates.py safety` (B):

| Module | Must not import/use | May import |
|---|---|---|
| `feedback_engine` | `grade_store`, `os`, `subprocess`, `pathlib`, `importlib`, `shutil`, `builtins`; `eval`/`exec`/`open`/`compile`/`__import__` | stdlib data/HTTP needed for one bounded request, `contracts`, `prompts` |
| `score_calculator` | LLM/network/filesystem/dynamic import | `decimal`, `fractions` *(D addition)*, `typing`, `dataclasses`, `__future__`, `collections`, `contracts` |
| `grade_store` | — | stdlib (sqlite3, hmac), `contracts`, `score_calculator`, `feedback_engine.validate_feedback` |

> **D directs E:** add `fractions` to the calculator allowlist (ADR-0003, exact rounding). Current
> `feedback_engine` imports `os` (`:7`) — **violation**; ADR-0003 moves config to the CLI. Gate must
> be updated to fail on `os` in engine once A refactors.

## 5. Tool / MCP surface

Per `docs/code-governance/mcp-tool-manifest.md` (E): each role may call only listed tools; unlisted or
role-inappropriate tools are denied. The coding agent has file-edit/read plus a shell that **asks**;
it has no network tool and no grade-data write tool.

## 6. Approval authority (ties to ADR-0002)

- This release: local trusted single-teacher CLI; `--reviewer` is an **audit label**, not identity.
- The approval check is a trusted dependency; multi-user authenticated approval (`verify_approval`) is
  the reopening condition. Until then, permission files must not claim authenticated student/teacher
  identities.

## 7. Verification of the permission model

| Check | Owner | Status |
|---|---|---|
| Import-boundary gate (`tools/gates.py safety`) | B | existing (needs `fractions`, `os`-in-engine updates) |
| `.opencode/permissions.jsonc` syntax + role rules | E | planned (syntax verify against installed OpenCode) |
| `permissions-snapshot.json` bound to implementation | B | planned |
| Process/filesystem sandbox of the AI component | E | planned (static checks alone insufficient) |
| Branch protection + CODEOWNERS + reviewer allowlist | B | planned (real GitHub config) |

## Gaps handed to E

1. Approve `.opencode/rules.md` and verify `.opencode/permissions.jsonc` syntax.
2. Add `fractions` to calculator allowlist; make `os` in `feedback_engine` a hard gate failure.
3. Provide runtime process/filesystem isolation for the advisory component.
4. Provide authenticated verifier injection before multi-user (ADR-0002 reopening).
