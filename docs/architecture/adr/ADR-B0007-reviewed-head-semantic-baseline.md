# ADR-B0007: reviewed HEAD replay when BASE has no evidence

Status: implementation candidate; independent exact-head review pending.
Date: 2026-11-23. Requirement: REQ-GOV-B04.

PR21 tests were independently approved by unohhh1 at 2c3bc8f and merged
at fbe7081122188f6bb4117da21af1a5127e20660e. B supplied implementation
start 0a6417d344b51fc8c54e9739fdb199334880f786, containing both that
merge and the separately reviewed PR19 checker at 8afdc5f.

The target main has no semantic-baseline.json. Requiring that artifact
before the first CI/evidence merge creates a bootstrap dependency cycle.
Keep branch protection and evidence quality unchanged. The sole runtime
change is tools/semantic_eval.py within PR21's reviewed scope.

Use git ls-tree to distinguish path absence from a failed lookup. Existing
BASE evidence always wins, including its read/validation failures. Only a
missing path permits verification of PR20 through the authenticated GitHub
API. Both repositories must match GITHUB_REPOSITORY and the target must be
main. The BASE policy's reviewer allowlist and existing human_approval
checker must establish a current, independent human approval of that PR's
exact head. Closed unmerged proposals are refused. The immutable contents
endpoint must identify a regular file whose blob equals HEAD's artifact.
CI already checks out a clean, exact PR head; no changed working-tree
artifact is an accepted CI input. API/Git failures block evaluation.

Continue recomputing the fixed cases, model/input/runtime fingerprints,
C/D acceptance, provider usage, strict O2 and unchanged thresholds. This
change does not produce a new model replay, accept PR13's history deviation,
change evaluation_approved, or authorize a merge. Once main has the baseline,
the normal BASE path automatically takes priority again.

The 13 approved tests pass. A prior strict-O2 test replaces base_read but
supplies a nonexistent trusted-base revision without replacing Git lookup.
The full governance suite therefore exposes a fixture compatibility gap.
Keep reviewed tests unchanged; any fixture revision needs a separate
reviewed tests-only change and protected-baseline handoff before integration.
