# A to B: PR23 baseline incorporated into PR22

Date: 2026-11-24. Agent: Codex AI assistant.

## Current result

The previous fixture blocker recorded on 2026-11-23 is resolved by the
separately approved PR23 fixture. A has completed the requested baseline
merge and full local regression. PR22 remains a draft for B integration;
this record does not approve PR8 or declare all six CI gates green.

D/unohhh1 APPROVED PR23 at deee8b6b67266ef77b60a103c6450dbd4f724327
on 2026-11-24T08:11:56Z. GitHub confirms its protected test-baselines
merge aeb4bfba9cfe90e4e185e450f6cfe8dce04cf048. A merged that exact
commit into PR22 with merge commit 84502e02ae0e215c8f58cc501794a52918e2140d.
The only conflict was the append location in ai-use-log.yaml; both A's
original implementation entry and B's full fixture entry were retained.
No earlier log entry was edited. The original #18 approval remains a
historical record; the revised fixture is bound separately to PR23.

## Verification

WSL Ubuntu, python3 and bubblewrap; no provider credentials or model calls:

- python3 tools/check_suite.py test/governance: 80/80 pass, zero skips.
- python3 tools/check_suite.py test/offline: 84/84 pass, zero skips.
- Windows project venv python -m ruff check src scripts test tools
  --select E4,E7,E9,F: pass.
- Windows project venv python -m mypy src tools --no-incremental:
  pass, 15 files.
- python tools/gates.py schema: pass.

Git object comparisons verify that PR21's 13 approved tests, plan and
locators match fbe7081122188f6bb4117da21af1a5127e20660e; the O2 fixture
file matches aeb4bfba9cfe90e4e185e450f6cfe8dce04cf048 exactly. Strict O2
assertions are intact. tools/semantic_eval.py and all deployed runtime,
prompts, model flags, workflow and permission policies match PR22's
6137806 implementation. No dependency was added. Actual test logs are
retained locally under artifacts/a-reviewed-head-20261124/; no credential
or raw secret is stored there. Current raw session is the Codex conversation,
with no exported transcript path available.

## Next owners

B: integrate this PR22 head, including the PR23 merge ancestry, into PR8.
Keep PR21 and PR23 review records distinct when reconciling test blob and
approval mapping; do not replace the earlier #18 blob approval with a
later record. Preserve the three historical review-memo records. Rerun
all six blocking gates on the integrated candidate and publish its exact SHA.

D: independently review that final PR8 SHA, including the semantic proof
and API snapshot. B then reruns required checks and merges only when all
six gates pass. Historical process deviations remain subject to C/B's
recorded decision; this regression result creates no exception.
