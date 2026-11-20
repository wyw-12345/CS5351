# B verification snapshots and CI integration preflight

Input: A `10f5b8d`, B tests-only draft PR #5 at `5f05f01`, and historical B candidate PR #4. These files are ready for review as candidate inputs to the next gate implementation. Their location under `handoff/` keeps release policies and workflows inactive.

| Input | Verified locally | Decision still needed |
| --- | --- | --- |
| `api-surface.json` | Source SHA-256 for the five application modules. Parameter names and kinds extracted from the AST match Python's imported runtime callables. | A/D and an independent reviewer confirm the exact contract and approval audit structure. |
| `permissions-snapshot.json` | SHA-256 fingerprints for E's six governance files match the A Git tree after CRLF normalization. | E provides actual OpenCode/tool enforcement and application runtime isolation evidence. Those verification flags remain false. |
| `model-evaluation.json` | The prompt v1.2 path and five-case synthetic dataset match the current tree. Both hashes are recorded. | A/C/D confirm deployment, dataset and cost for the authorized run. Live activation is false; no provider requests were made. |

## Failures reproduced in a disposable checkout

- Candidate `tools/gates.py schema` stops on REQ-PERF-003; C's strict validator lists ten missing executable locators. Keep failures visible until they have real tests or reviewed evidence.
- `tools/gates.py readiness` and `tools/semantic_eval.py` refuse the pending human baseline. No active reviewer list, prior approved tests baseline, or reviewed current model run is verified.
- `python -m mypy --no-incremental src tools` on the current A code and older B tools reported one compatibility error. The old evaluator called `Settings.from_env()`, which A replaced with `src.cli.settings_from_env()`.

## Verified evaluator update

`candidate/` contains the updated evaluator and three offline regression cases as an overlay for the historical gate candidate. The evaluator uses A's current config entry point, validates finite confidence including decimal strings, and checks that escalation is an expected result backed by valid advice. A provider failure, malformed advice, or fabricated quote cannot count as a correct escalation. Paid replay requires an approved model config, that config's live flag, and explicit runtime live opt-in.

To reproduce, start from A plus B test PR #5 in a disposable directory. Copy the historical B gate tools from PR #4 and their `tools/__init__.py` and pending policy template, then overlay only `candidate/`. With `GRADEAIDE_LIVE=0`, run the old `test_semantic_eval.py` and new `test_b_current_semantic.py` using unittest discovery in `test/governance`. Both suites passed (7 + 3 tests), as did mypy on `src tools` (13 files) and Ruff on the two updated candidate files. Evaluation still awaits real review and authorization.

## Next CI candidate

1. Review the evaluator overlay against the current CLI, prompt and fixed-set contract. Confirm actual model and cost before any live evidence collection.
2. Use one line-ending convention for the checked-in snapshots, verification code, and review record. Match the exact A API and E configuration SHA; record runtime proof separately. The older permission gate hashes raw checkout bytes, so the cross-platform comparison needs updating before these normalized hashes are used.
3. Bring in reviewed gate tests and the six named jobs. Confirm that the runner distinguishes tests-only review, implementation with prior reviewed tests, and the human-owned transition for historical integration. Backfilled review data cannot establish approval-before-code.
4. Keep CI and protection activation tied to valid GitHub configuration, real independent exact-HEAD reviews, and administrator-controlled required checks. Record any bootstrap decision as a separate human-reviewed change with its limits.
