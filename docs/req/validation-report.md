# D1 validation report

- Date: 2026-11-12
- Owner: member C
- Scope: `docs/req/requirements.yaml`, `docs/req/req-schema.json`, `docs/req/requirement-id-map.yaml`, `docs/req/prd.yaml`
- Evidence directory: `docs/req/evidence/`

## Result in one sentence

**The registry and schema are structurally valid; traceability is deliberately still incomplete, so no one may report the CI schema gate as PASS yet.**

## What was checked

| Check | Command | Actual result | Evidence |
|---|---|---|---|
| JSON Schema validity + registry validation | `python scripts/validate_requirements.py --json` | PASS: 47 requirements, all seven types, unique IDs, every formal ID present in the ID map | `docs/req/evidence/registry-validation.json` |
| Course schema gate | `python tools/gates.py schema` | BLOCKED: `No tests mapped for REQ-FUNC-001` | `docs/req/evidence/gates-schema.txt` |
| B proposal gate (unchanged) | `python tools/gates.py proposal` | BLOCKED: `Untraced test: test_live_api.py:test_real_provider_smoke` | `docs/req/evidence/gates-proposal.txt` |
| Invariant zero-tolerance | `scripts/validate_requirements.py` | PASS: all 8 invariants use threshold `0` | `registry-validation.json` |
| ID-map coverage | `scripts/validate_requirements.py` | PASS: 32 source proposals mapped; 47 formal IDs accounted for | `registry-validation.json` |
| PRD/registry link | manual | PASS: every user story links to at least one formal ID | `docs/req/prd.yaml` |

## Why `tools/gates.py schema` is blocked

`tools/gates.py schema` does two things in order:

1. `validate_registry(data, schema)` — schema, seven types, unique IDs, invariant thresholds.
2. `traceability(data)` — every registry ID must have a test-map entry whose test function docstring contains the ID, and every test must reference a registered ID.

The registry passes step 1. Step 2 blocks at the first new requirement because the existing test suite was written by A/B before C's formal IDs existed. The repo currently has:

- **14** IDs with a test-map entry (B's original set).
- **33** IDs without a test-map entry (C's new functional/quality/performance/cost/governance/security IDs plus E's governance IDs).
- **47/47** existing test functions without a per-function `REQ-*` docstring (A's tests use module-level docstrings; B's proposed tests target an interface A did not implement).

C did **not** edit tests or invent locators to make this green. That would manufacture traceability and violate `AGENTS.md` and B's gate design.

## Governance test observation

`python -m pytest test/governance -q` → **33 passed, 2 failed** (`docs/req/evidence/pytest-governance.log`):

1. `test_history_test_change_rejected` fails because this Windows environment has no `git` executable on PATH (`FileNotFoundError: WinError 2`). It is an environment issue, not a registry issue.
2. `test_proposal_trace_targets_exist` fails on the pre-existing `test_live_api.py::test_real_provider_smoke` missing a per-test `REQ-*` docstring. It is the same traceability gap described above.

Neither failure is caused by C's registry content, and C did not edit tests to hide them.

## What is genuinely complete

- The formal registry exists and is machine-readable.
- The official schema exists and is valid Draft 2020-12.
- All seven requirement types are present.
- All eight B invariants survive with zero-tolerance thresholds.
- Every E security proposal is either accepted or explicitly merged into a stronger invariant; nothing is silently dropped.
- Every A performance/cost proposal has a formal ID.
- The ID map records every accept/merge decision.
- The PRD covers scope, personas, user stories, workflow, assumptions, out-of-scope items, open questions and traceability summary.

## What is not complete

1. **Test mapping** for the 33 new IDs — owner B (with A/E for the relevant domains).
2. **Per-test `REQ-*` docstrings** — owner B; this is a test-only change that needs the separate test-approval path.
3. **Quality thresholds** — owner D; C's five quality requirements are drafts.
4. **Interface freeze** — owner D; A's `calculate_score`/`validate_feedback`/`GradeStore` and B's `calculate`/`validate_advice`/`record_grade` still differ.
5. **Human approval** — not obtained. The review record lists pending reviewers and does not claim a signature.

## Reproduction

From the project root:

```powershell
python scripts/validate_requirements.py --json
python tools/gates.py schema
python tools/gates.py proposal
```

Expected current output:

- `validate_requirements.py`: `schema_and_registry_status = PASS`, `traceability.complete = false`.
- `gates.py schema`: exit 1 with `BLOCKED schema: No tests mapped for REQ-FUNC-001`.
- `gates.py proposal`: exit 1 with `BLOCKED proposal: Untraced test: test_live_api.py:test_real_provider_smoke` (pre-existing, not caused by C's registry).

## Honest status

| Dimension | Status |
|---|---|
| Registry schema format | PASS |
| Seven-type coverage | PASS |
| ID-map coverage | PASS |
| Invariant preservation | PASS |
| Traceability | INCOMPLETE (33 IDs) |
| Human review | NOT OBTAINED |
| CI schema gate as a whole | BLOCKED |
