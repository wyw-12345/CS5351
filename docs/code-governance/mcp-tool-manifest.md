# MCP tool manifest — tools the coding agent may call (D3)

> Owner: member E (coding governance). Status: D3 baseline — reconciled with the actual A tooling
> (Python 3.12 CLI, `tools/gates.py`, `scripts/validate_requirements.py`, Ruff, mypy, pip check,
> pip-audit) and D's `permission-model.md`. Agent/tool surface still requires verification against the
> installed OpenCode version.

This manifest declares, per role, which tools are allowed. Anything not listed is **denied** by default.
The machine-readable enforcement lives in `.opencode/permissions.jsonc`; this file is the human-readable
contract that A and the reviewers audit.

## Roles

| Role | Responsibility | Write authority |
|---|---|---|
| `plan` | produce execution plan + scope, no code edits | none (read-only) |
| `code` | generate/refactor application code | whitelisted dev paths only |
| `verify` | run tests, lint, type check, gates, secret scan | none (read-only + run checks) |
| `human` | review, approve, merge, grant permissions, provision keys | full, out-of-band only |

## Tool table

| Tool (action) | plan | code | verify | human | Notes |
|---|---|---|---|---|---|
| `read` (project files) | allow | allow | allow | allow | `*.env*`, `*.pem`, key files always denied |
| `glob` / `grep` | allow | allow | allow | allow | — |
| `edit` / `write` / `patch` | deny | allow (whitelist) | deny | allow | see path whitelist below |
| `shell` — test/lint/type/gate runners | deny | allow | allow | allow | `python -m unittest*`, `python tools/gates.py*`, `python scripts/validate_requirements.py*`, `ruff`, `mypy` |
| `shell` — secret/dependency scan | deny | deny | allow | allow | `python -m pip check*`, `python -m pip_audit*`, secret-scan runner |
| `shell` — git read/inspect | allow | allow | allow | allow | `git status/diff/log/show` |
| `shell` — git write | deny | `git add/commit` only | deny | allow | **`git push*` and force/delete always denied** |
| `shell` — arbitrary / network / secrets | deny | deny | deny | allow | no arbitrary shell, no credential reads, no key generation |
| `subagent` / `skill` | allow (scoped) | allow (scoped) | allow (scoped) | allow | must not escape this manifest |
| `webfetch` / `websearch` | ask | ask | ask | allow | model/API research only; no exfiltration |
| MCP server tools | deny | deny | deny | allow | none registered yet; any new MCP tool requires review |
| `execute` / code mode | deny | deny | deny | allow | removed for agents |

## Path whitelist for `code` edits

Allowed: `src/feedback_engine.py`, `src/cli.py`, `src/contracts.py`, `test/**`, `docs/**`, `prompts/**`,
`config/model.json`, `requirements-app.txt`.

Denied (or `ask` + ADR + human approval): `src/score_calculator.py` (frozen), `src/grade_store.py` (ask),
`.opencode/**`, `.agent/**`, `.github/**`, `docs/verification/**`, `data/**`, `grades/**`, and any key
file (`.env*`, `*.pem`, `~/.gradeaide/**`).

## Rules

1. Default-deny: an unlisted tool or a role-inappropriate call is denied, never silently allowed.
2. The agent may not self-grant, broaden, or edit its own permission files.
3. Shell runs with host authority; only the narrow allowlist above is permitted for agents.
4. `git push` and any ref deletion/force are denied for every agent role.
5. The advisory component (`feedback_engine`) must not make network requests beyond the single bounded
   model call to the configured endpoint; the coding agent has no arbitrary network tool.
6. Secret scanning and key provisioning are human/verify-role activities; keys are never generated or
   committed by an agent.
7. A new MCP tool or shell command requires this manifest and `.opencode/permissions.jsonc` to be
   updated in the same reviewed governance PR.
