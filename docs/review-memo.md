# Review memo register

## C-BOOT-001 — bootstrap baseline decision (recorded, not an approval)

- Date: 2026-11-23, Asia/Shanghai. Author: C (Yuwei WANG, 60875477), baseline owner. Authoring agent: Vibe (Mistral)
  with human decisions taken by C. Raw session kept locally by C; not attached to the repository.
- PR: `docs/member-c-bootstrap-baseline` → `main` (see PR body template). Base: `main` at `cdd6ce7`. Head: recorded in
  the PR after the first push. This entry documents a governance decision and must not be read as an approval of any
  code change.
- Changed REQ/ADR/INV: `ADR-B0006` (new), `REQ-GOV-C01` (requirements change process), `REQ-GOV-B03` (traceability),
  `REQ-GOV-B06` (AI-use log). No requirement text or threshold was relaxed by this entry.
- Spec alignment: the course requires tests to be reviewed before implementation. For the window up to `cdd6ce7` that
  requirement cannot be satisfied honestly, because PR #6 merged implementation, retrospective tests and gate tooling
  together and `docs/verification/implementation-approvals.json` is empty. The deviation is accepted, dated and bounded;
  it is described in the report rather than hidden.
- Architecture alignment: no runtime, policy or interface change. The decision only affects how two gate sub-results are
  interpreted. `main` keeps `policy.json` `status: active` with reviewers this-kong and unohhh1; the stale pending copy
  carried on `ci/member-b-gates` must not overwrite it at merge time.
- Code/test quality: no source file touched. The bootstrap decision does not cover `schema`, `static-analysis`,
  `semantic-evaluation`, or the mutation sub-checks of `regression`; those remain open with their own owners
  (B for test locators and mutations, A for the live model replay, D for the independent review).
- Security/privacy: no credential, token or `.env` content involved. No approval, signature or commit authorship was
  fabricated; the empty `implementation-approvals.json` was deliberately left empty.
- Latency/token/cost: not applicable to this change.
- Six gate run URLs: to be added by B after the merge of PR #8 and the re-run on the merged head. Before that, the honest
  status is "bootstrap deviation recorded; test-approval and regression history sub-check decidable; other four gates as
  reported in the latest CI run".
- Negative/mutation evidence: unchanged by this entry. `INV-003-signing` and `INV-007-advisory-authority` are still
  NOT RUN and must not be reported as passing.
- Debt changes: `debt-register.md` unchanged; the bootstrap deviation is now an explicit, dated item instead of an
  undocumented gap.
- Runtime fallback: reverting this entry and `ADR-B0006` restores the previous state — both gates red — with no effect on
  application code.
- Independent review: **not obtained in this entry**. D must record an exact-head review of PR #8 (non-author, account
  unohhh1) for the static-analysis requirement, and must confirm or reject the bootstrap boundary in writing.
- Verdict: **CHANGES REQUIRED** until (1) D's independent exact-head review is recorded, (2) PR #8 is merged with the
  active policy preserved, (3) B re-runs the six checks on the merged head and links the run. C does not approve their
  own governance change and does not sign for D.
