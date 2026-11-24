# A to B/D: reviewed HEAD semantic fallback candidate

## State

Implementation is complete within PR21's one-file scope, but **not ready for
integration/merge**: the unchanged prior governance suite has one fixture error.
Publish as draft; do not describe the regression gate as green.

## Actual approval and ancestry

- D/unohhh1 APPROVED PR21 head 2c3bc8f530685deff4d4e982e88379eca6c88d53
  at 2026-11-23T12:49:20Z.
- Protected tests merge: fbe7081122188f6bb4117da21af1a5127e20660e.
- B's requested starting SHA: 0a6417d344b51fc8c54e9739fdb199334880f786.
  Both the tests merge and reviewed PR19 checker 8afdc5f are ancestors.
- Approved 13 tests, scope plan and test-map are unchanged from the tests merge.
  All test files are unchanged from the implementation start.

## Implementation and proof

Only tools/semantic_eval.py changes executable behavior. load_reviewed_baseline
uses BASE whenever its path exists. Only confirmed absence permits PR20's exact
currently approved head artifact. GitHub proof uses the BASE reviewer allowlist,
independent current human approval, same-repository/main target metadata, an
immutable contents URL and exact HEAD Git blob equality. Errors block evaluation.
Existing C/D acceptance, runtime/input identity, fixed cases, provider usage,
strict O2 and threshold recomputation remain mandatory.

No dependencies, model replay, approval/live flag, prompt, deployed runtime,
workflow, permission policy or historical exception changed. Metadata updates
record PR21, ADR-B0007, contract and verification scope; the AI log is appended.
The new implementation awaits actual independent exact-head review.

## Commands and observed results

Windows Python: ../GradeAide-member-A-2026-11-13/.venv/Scripts/python.exe.
Linux: WSL Ubuntu python3 with bubblewrap.

- python -m unittest test.governance.test_a_reviewed_head_baseline -v:
  13/13 pass.
- python -m ruff check src scripts test tools --select E4,E7,E9,F: pass.
- python -m mypy src tools --no-incremental: pass, 15 files.
- Linux python3 tools/check_suite.py test/offline: 84/84 pass, no skips.
- Linux python3 tools/check_suite.py test/governance: 79 pass / 1 error.
- Linux python3 tools/mutation_check.py: 6/6 detected.
- Linux python3 tools/application_mutation_check.py: 12/12 detected,
  including deployed INV-007 and three INV-003 signature/key/binding mutants.
- python tools/gates.py schema: pass; secrets: pass; python -m pip check: pass.
- With GRADEAIDE_LIVE=0, GITHUB_REPOSITORY and a transient authenticated GitHub
  token: python tools/semantic_eval.py --base
  cdd6ce7d25a2f937d2880140386ff22c96d387de --check-baseline:
  actual read-only GitHub verification returns passed=true, model=deepseek-flash.
  No provider request or provider credential was used.
- Git diff against fbe7081 for PR21's test/plan/map: empty; against 0a6417d
  for all tests, src, scripts, workflows, policies, model/config, prompts,
  semantic-baseline and model-evaluation: empty.
- Local Windows all-governance additionally encounters Linux-only isolation
  failures via nested offline discovery. Linux removes those platform failures.
  The initial inherited Git configuration error was removed from the test process.

## Confirmed regression blocker

Unchanged test/governance/test_b_gate_evidence.py,
StrictO2Tests.test_reviewed_baseline_rechecks_cases_instead_of_trusting_saved_metrics,
uses the synthetic revision trusted-base and mocks base_read only. The new
required existence check therefore invokes real Git on a nonexistent revision.
The failure precedes its O2 assertions. This occurs on Windows and Linux; it is
not a model-quality failure. In a separate diagnostic invocation, temporarily
mocking that Git lookup as an existing BASE file makes the same unchanged test
pass, including its rejection of a scored unverifiable case. This diagnostic
is not a passing official full regression run.

Do not add special cases for trusted-base or suppress Git errors in production.
Do not edit the reviewed tests in this implementation. A possible fixture-only
proposal is to add a synthetic existing-path Git response to that legacy unit
test, while retaining both O2 assertions. D must review it through a separate
tests-only PR; B must reconcile the prior approval-plan/blob mapping as needed
and publish the protected start SHA. No new approval is implied by this suggestion.

## Next owners

1. B coordinates a separately reviewed fixture-only compatibility proposal;
   D reviews the exact tests-only SHA, then B publishes its protected baseline.
2. A rebases this candidate onto B's approved start and reruns the unchanged
   approved suites. Until then this implementation PR stays draft.
3. B integrates the verified implementation and PR21 ancestry/approval mapping
   into PR8, preserving all three historical memo records, then reruns six gates.
4. D reviews PR8's final exact SHA. B merges only after all required gates pass.
   PR13's historical approval gap remains with C/B's recorded decision process.

Raw session: current Codex conversation, not exported to a repository file.
