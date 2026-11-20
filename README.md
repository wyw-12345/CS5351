# GradeAide

Member A integration on member E's `docs/member-e-governance` baseline (`c59d1aa`).
Read `AGENTS.md`, `Prompt.md`, then `handoff/records/2026-11-17-A-实现整合.md`.
The application is a Python 3.12 CLI: AI advises, the teacher signs accepted scores, the deterministic calculator computes, and SQLite persists the grade and audit.

## Run locally

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-app.txt
.venv/Scripts/python.exe -m scripts.demo_restart
.venv/Scripts/python.exe -m unittest discover -s test/offline -v
```

The offline demo uses disposable synthetic signing material outside the repository, runs eight separate processes, checks the persisted 72.00 grade and rejects a forged signature. It does not call a model or represent human approval. See `python -m src.cli --help` for propose/show/sign/approve/migrate/keygen commands. Operator key provisioning and access controls remain E's responsibility.

Runtime dependency: `cryptography==50.0.2`, for Ed25519 signatures and encrypted private-key serialization. Existing `requirements-ci.txt` pins development/schema/audit dependencies; B owns CI. No extra workflow is supplied by A.

## Configuration and real requests

`config/model.json` is a non-secret review descriptor. Runtime settings come from `src.cli.settings_from_env`: `GRADEAIDE_ENDPOINT`, `GRADEAIDE_MODEL`, `GRADEAIDE_API_KEY`, `GRADEAIDE_INPUT_PRICE_PER_MILLION`, `GRADEAIDE_OUTPUT_PRICE_PER_MILLION`, `GRADEAIDE_MAX_COST`, and `GRADEAIDE_PRICE_SOURCE`. Prices and budget must share a currency. Defaults are 30 seconds, 1,024 output tokens, 12,000 input bytes and zero retries. `GRADEAIDE_TRUST_STORE` points to an operator-owned public-key allowlist outside this repository. Signing passwords are prompted, and private keys stay external.

To make a real proposal, export those settings and run:

```powershell
python -m src.cli propose --essay examples/essay.txt --rubric examples/rubric.json --submission-id sample-001 --db grades.sqlite3
```

Review the returned proposal ID/hash and scores; use `sign --confirm-sign` then `approve --approval SIGNED_JSON`, supplying the same proposal, scores, reviewer label and reason. Escalation resolution requires a complete score set and nonempty reason. `scripts.demo_restart` is the executable example of this sequence. For v1 databases, back up the file before explicit `python -m src.cli migrate --db OLD.sqlite3`; old unsigned approvals stay `legacy_unverified`.

The optional existing live launcher reads an operator-local configuration without executing shell expressions:

```powershell
python -m scripts.live_from_env --env-file .env --confirm-live --mode evaluate --repeat 4
```

This command makes up to 20 billed requests. It was **not run in this rebuild**. `evidence/live-results.json` is preserved historical synthetic evaluation evidence, not current deployment or human semantic acceptance.

## Handoff boundary

Five core modules remain under `src/`; tests are divided into `test/offline` and `test/live`. A's recorded checks are in `docs/member-a/verification-results.md`. B owns the six formal gates, independent test approval and official snapshots. E owns deployment isolation and production keys. This branch is `awaiting_review`; it does not claim release approval or a deployed sandbox.
