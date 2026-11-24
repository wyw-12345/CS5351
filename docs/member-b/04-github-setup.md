# D7 rollout and GitHub readback

GradeAide uses [wyw-12345/CS5351](https://github.com/wyw-12345/CS5351). [PR #8](https://github.com/wyw-12345/CS5351/pull/8) contains B's gate candidate. Its first [Actions run](https://github.com/wyw-12345/CS5351/actions/runs/44778695021) exercised all six jobs. Branch protection and reviewed baseline policy were still pending at that readback.

## Owner and independent review

1. Review the exact candidate SHA, the D7 rollout ADR and the repository's historical merge evidence. PR #6 merged prior implementation and tests; its review API returned no reviews. The rollout decision should record that history and the evidence the owner has accepted for the starting baseline.
2. Establish the reviewed policy on the protected base with real independent reviewer identities and a real `CODEOWNERS` assignment. Use test-approval ancestry for future changes. Confirm E's runtime/tool and policy evidence and current semantic evidence before treating the release checks as active. GitHub's review entry, the branch settings and the run results are separate sources of evidence.
3. The repository administrator creates and protects the reviewed `test-baselines` branch and configures `main`. Keep approval review on both. Require all six checks on `main`; keep successful status checks optional on `test-baselines` so independently reviewed red tests can precede implementation.

Configure the intended protection through GitHub Settings, or inspect this repository's exact payload locally before the administrator applies it:

```text
python tools/github_setup.py wyw-12345/CS5351
```

After configuration an authorized account can verify the live response without changing the repository:

```text
python tools/github_setup.py wyw-12345/CS5351 --check
```

The command reads both branch protection endpoints. It checks admin enforcement, force pushes and deletion, conversation resolution, stale-review dismissal, CODEOWNERS and latest-push review, bypass allowances, and the expected six required checks on an up-to-date main. It also checks that the tests-only branch has no required status checks. The request uses an existing authorized `GH_TOKEN` or `GITHUB_TOKEN` from the environment. GitHub requires Administration read access for a fine-grained credential to read these settings. [GitHub branch-protection API](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection)

## Record current evidence

- Save the verified branch settings or readback, the owner-reviewed baseline SHA, and real review and workflow links in the handoff record. Confirm the actual CODEOWNERS identities separately from the server's code-owner setting.
- Rerun the exact-head workflow after independent review. Save a demonstrably blocked PR to show enforcement.
- Keep provider credentials outside the candidate PR workflow. A/B should use an authorized model replay from an approved environment to gather current real evidence. Preserve the model, prompt and dataset fingerprints, consent and review together with its run.
