# D7 — real GitHub setup and readback

Local Git history is created in this directory. No GitHub remote/account authorization was supplied; no remote URL or protection success is claimed.

## Create and push

1. Use your authenticated GitHub account to create a **private** `gradeaide` repository (avoid publishing student submissions). Or use the provided script with an environment-only API token; its default mode prints the exact API payload without changing anything:

   ```powershell
   .\.venv\Scripts\python tools/github_setup.py ACTUAL_OWNER/gradeaide --create
   # After inspecting the real owner and payload, execute with existing account authorization:
   .\.venv\Scripts\python tools/github_setup.py ACTUAL_OWNER/gradeaide --create --apply
   ```

   `ACTUAL_OWNER` is instructional text, not a real repository. Replace it. Do not commit a token; use GitHub Desktop, `gh auth login`, or an environment variable. This script accepts only personal account creation; an organization repo needs its administrators' approved process.
2. Add the actual remote and push this preparation history using your normal authenticated Git client. Create `test-baselines` from the approved governance baseline and push it too. Never force-push another member's work.
3. Replace README's “not yet connected” field with the verified real URL. Add independent real teammate reviewer usernames to the protected `docs/verification/policy.json`; do not list only the author. Set status to `active` only through a real human-reviewed governance baseline.
4. Generate `.github/CODEOWNERS` with real independent usernames for `/src/score_calculator.py`, `/src/grade_store.py`, `/src/feedback_engine.py`, `/.github/`, `/tools/`, `/.opencode/`, `/.agent/`, `/docs/verification/`, `/AGENTS.md`. The initial commented file is not enforcement. Required general PR review plus explicit CODEOWNERS ensures safety/governance paths receive review.

## Protect both branches

After both branches exist, dry-run then apply:

```powershell
.\.venv\Scripts\python tools/github_setup.py ACTUAL_OWNER/gradeaide
.\.venv\Scripts\python tools/github_setup.py ACTUAL_OWNER/gradeaide --apply
```

`main`: all six exact check contexts, strict up-to-date base, one independent review, code-owner review, dismiss stale approvals, review latest push, resolve conversations, enforce admins, no force push/deletion. `test-baselines`: same human review constraints, but no required green application check so a deliberately failing test can be approved **before implementation**. Do not merge source code into test-baselines. Its tests-only nature is checked later by the implementation gate.

The API script reads protection back. Preserve the actual API readback/screenshot and workflow run links in the PR memo. A JSON file in the repository alone does not enable server-side protection. If the account plan does not support private-repository protection, document the actual API failure and choose a team-approved supported account/organization; do not silently publish the project or claim protection is active.

## Operational details

- Add the real model API key as `GRADEAIDE_API_KEY` through GitHub Secrets after A aligns the provider contract. Never expose it to unreviewed fork code; fork semantic jobs fail and a maintainer uses a reviewed trusted branch.
- Review-triggered API evidence needs **rerun jobs** after a real approval; no fake review event file is accepted.
- Initial push may have an all-zero before SHA and missing upstream files, so its gate failures are expected. Never rewrite the diff to HEAD~1 to manufacture a pass.
- Before final submission verify six actual check runs on a real PR, a deliberately blocked negative PR, protection readback, commit history, real URL in README and no tracked credentials.

Sources: [GitHub branch protection REST API](https://docs.github.com/en/rest/branches/branch-protection), [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [workflow security](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).

