# ADR-B0005 candidate for repository verification

**Status:** proposed. Independent exact-head review and repository activation pending.

Use six named PR checks: test approval, static analysis, schema, semantic evaluation, regression, and the AI-use log. The candidate starts from the A/E/B implementation and tests already present in `main` at `fab81cb`. API snapshots name actual callables and include LF-normalized source fingerprints. Policy-file fingerprints record content and require separate E evidence of actual permission, tool, and runtime enforcement.

The proposed workflow checks out the exact PR head with a read-only GitHub token and offline model settings. No grading-provider credential is passed to it. Semantic checks remain blocking until an approved real-model baseline and the deployment's authorized replay process exist. The live test suite can then record current performance and evidence. The candidate uses the current A CLI settings entry point and the current fixed synthetic cases.

PR #6 merged historical implementation and B's retrospective acceptance. It cannot prove that reviewers approved the tests before the implementation. Keep the bootstrap deviation in the report. The owner and an independent human must approve any transition for existing work and configure branch protection and a verified tests baseline. Future changes must satisfy real review and ancestry. Reverting this candidate removes the proposed workflow and verification artifacts without changing the application.
