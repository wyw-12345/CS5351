# Bug diary

No application bug has been observed: the application does not yet exist. Do not count anticipated negative cases as discovered defects.

## Environment observations (not application defects)

2026-11-06: `python` resolves to Python 3.6 and the PATH Git launcher is not executable on this system. Use Codex's bundled Python 3.12 and Git for this preparation. Impact: default commands fail before tests collect. This exposes an environment reproducibility gap rather than a GradeAide invariant violation.

## Entry format for significant confirmed bugs

Record ID/date, observed symptom and command, minimal reproduction, affected requirement/invariant, classification (specification/architecture/code/prompt/permission/evaluation), root cause, agent-generated fix commit, independent negative regression test, before/after evidence, exposed invariant gap, owner, human verdict and closure condition. Record real discoveries only.



## B-BUG-001 — script changes escaped governance (2026-11-17)

Symptom/reproduction: `is_implementation('scripts/evaluate_live.py')` was false and `check_ai_log([], [], ['scripts/evaluate_live.py'])` returned successfully. Root cause: old implementation-prefix list omitted scripts and extra dependency manifests. Classification: guardrail/code-generation governance. Requirement gap: REQ-GOV-B01/B06 and REQ-GOV-C01. Proposed fix includes scripts/dependencies and registry co-evolution; OpenCode-authored negative tests verify rejection. Candidate-overlay governance suite: 43 pass. Status FIX READY FOR INDEPENDENT REVIEW; original protected gate is not claimed deployed.

## B-BUG-002 — boundary suite never reached business assertions (2026-11-17)

Symptom: all eight old B tests errored on relative imports. Root cause: stale flat API proposal versus D's accepted package API. Fix: B tests call real src package/object rubric/GradeStore. No import error remains; 3 authority methods now fail on actual missing policy behavior. Existing arithmetic/privacy/invalid-input assertions pass. Status test-only draft, independent review pending. No A source change.
