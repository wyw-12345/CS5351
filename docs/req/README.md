# Requirements (D1) — start here

Owner: member C. Status: `draft_ready`; no human approval or signature claimed.

| File | Purpose |
|---|---|
| `requirements.yaml` | Consolidated registry: 47 requirements, seven types, machine-readable fit criteria |
| `req-schema.json` | Official Draft 2020-12 schema used by the schema gate |
| `prd.yaml` | Product requirements document: scope, personas, user stories, workflow, open questions |
| `requirement-id-map.yaml` | Every A/B/E proposal mapped to accepted/merged/new ID |
| `requirements-review-record.md` | C self-check, pending reviewers, known inconsistencies |
| `traceability-handoff.yaml` | Which requirements still need real tests, and who owns them |
| `validation-report.md` | Actual schema PASS vs traceability BLOCKED evidence |
| `evidence/` | Machine-readable registry report and real gate outputs |

## Current truth

- Schema and registry structure: **PASS** (47 entries, 7 types, unique IDs).
- Traceability: **INCOMPLETE** — 14/47 IDs mapped; 33 need real tests and per-test `REQ-*` docstrings.
- `python tools/gates.py schema`: **BLOCKED** at `REQ-FUNC-001` because no test is mapped.
- Human review: **NOT OBTAINED**.

Do not edit `requirements.yaml` without updating `requirement-id-map.yaml`, traceability evidence and `docs/ai-use-log.yaml` (`REQ-GOV-C01`).
