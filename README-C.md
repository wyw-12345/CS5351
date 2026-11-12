# CS5351 C-only extract — D1 requirements baseline

This is a **C-only** extract, not a standalone runnable project. It contains only member C's
requirements deliverables. A/B/E upstream files are intentionally excluded.

- Date: 2026-11-12
- Owner: member C (requirements engineering, D1)
- Status: `draft_ready`; no human approval or signature claimed.
- Full project snapshot: `../5351-C.zip` (contains A/B/E files as upstream context).

## Included

| Path | What it is |
|---|---|
| `docs/req/requirements.yaml` | 47 requirements across all seven types |
| `docs/req/req-schema.json` | Draft 2020-12 schema |
| `docs/req/prd.yaml` | Machine-readable PRD and user stories |
| `docs/req/requirement-id-map.yaml` | A/B/E proposal decisions and new C IDs |
| `docs/req/requirements-review-record.md` | C self-check and pending reviewers |
| `docs/req/traceability-handoff.yaml` | Unmapped requirements and owners |
| `docs/req/validation-report.md` | Real schema PASS / traceability BLOCKED evidence |
| `docs/req/evidence/` | Machine report and gate outputs |
| `docs/req/README.md` | Entry point |
| `docs/member-c/` | C delivery notes and C→D handoff |
| `docs/member-c/AI-USE-LOG-C.yaml` | C's two AI-use entries (extract) |
| `scripts/validate_requirements.py` | Local registry/schema/ID-map validator |
| `handoff/records/2026-11-12-C-需求基线.md` | Handoff record |

## Not included

- A's `src/`, tests, examples, evidence.
- B's CI tools, tests and `docs/member-b`.
- E's `AGENTS.md`, permissions and governance drafts.
- The full project `README.md`, PDF and `git-history.bundle`.

Those are upstream context. To run `tools/gates.py schema` or continue to D, use the full
snapshot `5351-C.zip` or the team repository, not this extract.

## What can be checked here

```powershell
python -c "import yaml,json,jsonschema; print('load ok')"
python scripts/validate_requirements.py --json
```

The validator needs `pyyaml` and `jsonschema`. It does **not** need A/B/E files. It will report:

- registry/schema/ID-map: PASS;
- traceability: incomplete (14/47).

## Current truth

| Dimension | Status |
|---|---|
| Schema format | PASS |
| Seven types | PASS |
| ID-map coverage | PASS |
| Invariants preserved | PASS (all 8) |
| Traceability | INCOMPLETE (33 IDs without real tests) |
| Human review | NOT OBTAINED |
| CI schema gate as a whole | BLOCKED |

Do not report "all gates pass". Do not add fake test mappings. Next owner: D.
