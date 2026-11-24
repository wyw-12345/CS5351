# ADR-B0006 — Bootstrap baseline and the point from which strict governance applies

**Status:** accepted for the bootstrap scope only. Independent exact-head review by D and the merge of PR #8 remain open.
**Date:** 2026-11-23 (Asia/Shanghai)
**Deciders:** C (requirements and governance baseline, author), D (independent reviewer, to be recorded), B (repository gates), E (policy and repository protection)
**Related:** ADR-B0005 (verification rollout; proposed on `ci/member-b-gates`, not yet on `main`), `docs/req/requirements.yaml` (REQ-GOV-C01/C02), `docs/member-b/03-test-approval-process.md`, PR #6, PR #8, PR #9

## Context

The six release gates require that a test be written, reviewed and approved **before** the implementation it
covers. The repository history does not support that claim for the work that already exists:

- PR #6 merged historical implementation together with retrospective acceptance tests. Tests, implementation and
  gate tooling arrived in the same change set.
- On `main` there is no `docs/verification/implementation-approvals.json` at all, and the candidate carried on
  `ci/member-b-gates` lists no approvals. There is no record of a reviewer approving a test plan ahead of the code,
  and none can be produced now.
- Git history is auditable and cannot be rewritten. Backfilling approvals would be fabrication, and would make every
  later gate result untrustworthy.
- Until this deviation is decided in writing, `test-approval` and the history sub-check of `regression` stay red, so
  PR #8 cannot merge and the semantic and schema gates have no stable base to attach to.

Two honest options existed: leave the gates red permanently, or record a dated bootstrap deviation with an explicit
boundary and strict rules after it. This ADR takes the second option and states its limits.

## Historical sequence (recorded 2026-11-23, auditable on `main`)

The deviation happened **once**, in the integration of the pre-existing GradeAide deliverables. It is visible
directly in the history, so nothing here depends on memory:

| UTC date | Commit (PR) | Author | What it added |
| --- | --- | --- | --- |
| 2026-11-16 | `c59d1aa` (#6) | E | D3 coding-governance baseline (`AGENTS.md`, `.opencode/rules.md`, `permissions.jsonc`) |
| 2026-11-17 | `10f5b8d` (#6) | A | `feat: integrate existing member A deliverables…` — `src/` **and** `test/` in the same commit; 51 files, +3953/−11 |
| 2026-11-20 | `5f05f01` (#6) | B's agent | `test: adapt member B acceptance to signed grading baseline` — acceptance tests written **after** the implementation already existed |
| 2026-11-20 | PR #6 merged | — | 69 files in one change set: 6 `src/`, 18 `test/`, 11 `docs/`, 5 `scripts/` (gate tooling included). No tests-only PR preceded it |

Three facts follow, and they are the only ones this ADR relies on:

1. **Once, not repeatedly.** `src/` reaches `main` in exactly one commit (`10f5b8d`); every later implementation
   change is still on a branch. The ordering deviation therefore occurred once, for the early GradeAide work, and
   no second occurrence exists to excuse.
2. **The plan was test-first; the actual path was not.** The workflow was agreed at the division-of-labour stage —
   test written and approved before implementation (the constraint the `test-approval` context encodes, see
   `docs/verification/policy.json` → `required_contexts`). What actually happened is the parallel offline path:
   members advanced in parallel outside GitHub, A produced `src/` first, B then wrote acceptance tests
   retrospectively against that existing implementation, and implementation, tests and gate tooling entered `main`
   together in PR #6 rather than through an independent tests-only PR.
3. **So the evidence is missing, and cannot be manufactured.** `docs/verification/implementation-approvals.json` is
   empty (absent on `main`, no approvals on `ci/member-b-gates`). The serial order “test approved → implementation”
   cannot be proven from history, and it cannot be back-filled: git history is append-only and auditable, and
   invented approvals would invalidate every later gate result.

**Open item for E (not a blocker for this ADR):** the group's written norm document — *CS5351 GradeAide GitHub 使用规范*
as cited in E's 2026-11-23 message — is not present on `main` under that or a similar name. Until it is committed or
its path is given, this ADR cites (a) E's written statement of 2026-11-23 and (b) the machine-readable equivalent
already in the repository: `docs/verification/policy.json` requiring the `test-approval` context.

### 中文摘要（报告与群内引用可直接用这段）

1. 这个偏差**只发生过一次**，就是早期 GradeAide 交付物入库那一次；`src/` 在 `main` 上只有一条提交（`10f5b8d`，
   2026-11-17），之后没有任何实现改动进过 `main`。
2. 分工阶段规划的是「先测后写」；实际执行是成员离线并行推进、最后才合并进 GitHub：A 先产出 `src/` 实现，
   B 随后对已存在的实现追溯补写验收测试，测试、实现与门禁工具同批由 PR #6 合入，**没有**先经过一个独立的
   tests-only PR。
3. 因此 `docs/verification/implementation-approvals.json` 为空，历史序列无法证明「测试先于实现被批准」。
4. 该顺序无法倒回补写——git 历史只增不改、可审计，补造批准记录等于伪造证据，会让后面所有门禁结果失去意义。
5. 处理方式不是补写历史，而是记偏差、划边界（`cdd6ce7` 为界）、写完失效条件（见本 ADR 第 3、6 条）。

## Decision

1. **Bootstrap window.** Everything reachable from `main` up to and including commit `cdd6ce7` (`gov: activate verification baseline (policy active + reviewer allowlist)`, the commit that changed
   `docs/verification/policy.json` to `status: active` and named `this-kong` and `unohhh1` as reviewers) is declared the
   **bootstrap baseline**. For that window we accept, as a known and dated deviation, that implementation and tests
   were committed together and that no pre-implementation test approval exists.
2. **Strict window.** From the first commit after `cdd6ce7` onward, every change must satisfy all of: test written and
   approved before implementation, independent exact-head review by someone other than the author, all six named
   checks green on the exact PR head, and `main` protected with the six required contexts. No second bootstrap window
   is granted, and this ADR may not be cited to excuse any later change.
3. **What is not excused.** The bootstrap decision covers the *ordering* deviation only. It does not waive
   `schema`, `static-analysis`, `semantic-evaluation` or the mutation sub-checks of `regression`. Semantic evaluation
   still needs an authorised real-model replay against an approved baseline; the two unrun mutations
   (`INV-003-signing`, `INV-007-advisory-authority`) still have to be executed.
4. **Recording, not rewriting.** The deviation is recorded here and in `docs/review-memo.md` (entry `C-BOOT-001`),
   and is described in the final report. `implementation-approvals.json` stays empty: we do not insert approvals that
   did not happen, and we do not invent commit dates, authors or reviewer identities.
5. **Approval of this ADR is a real human act.** C authors and signs the decision as baseline owner; D records an
   independent exact-head review; B re-runs the six checks after PR #8 is merged; E confirms repository protection
   was read back. Until D's review exists, the gate result is "bootstrap accepted, independent review pending", not
   "gate passed".
6. **Invalidation.** If any of the facts above is later found to be wrong — for example if a pre-implementation
   approval for the bootstrap window does exist — this ADR is withdrawn and the ordinary rule applies to the whole
   history.

## Scope of the baseline (what exactly is accepted)

| Accepted for the bootstrap window | Still required, unconditionally |
| --- | --- |
| Implementation and tests committed together | Six named checks green on the exact PR head |
| No pre-implementation test approval record | Independent review by a non-author |
| Retrospective test authoring by the same agent/person | Branch protection with six required contexts |
| Missing historical mutation runs listed as NOT RUN | The two unrun mutations executed before release |
| | Authorised live model replay for `semantic-evaluation` |
| | Test locators for the requirements that still have none on `main` (`REQ-GOV-B01/B02/B05/B06`) |

## Consequences

- `test-approval` and the history sub-check of `regression` become **decidable**: they report the recorded deviation
  and the strict-window status instead of an unresolvable red.
- PR #8 can merge once the remaining gates are green, with this ADR referenced in the merge commit and the PR body.
- The report and the demo must state the deviation in the same words: no fake approval, no fabricated transcript,
  no claim that tests preceded implementation.
- Cost of being wrong: if reviewers disagree, the fallback is to leave the two gates red and report the deviation as
  unremediated. Nothing in the code depends on this ADR, so it can be reverted by deleting this file and this entry
  in `docs/review-memo.md`.

## Alternatives considered

1. **Rewrite history to look compliant.** Rejected: destroys auditability, is detectable, and would invalidate the
   rest of the evidence.
2. **Leave both gates permanently red.** Honest but blocks PR #8 and leaves `schema` and `semantic-evaluation`
   without a stable base, so no acceptance is possible at all.
3. **Silently relax the policy file.** Rejected: the policy is E's authority surface and changing it to pass a gate
   is exactly the behaviour the gates exist to prevent.
4. **Bootstrap with a boundary (chosen).** Keeps the gates meaningful after a dated point, records the past honestly,
   and leaves every substantive check in force.

## Verification of this decision

- `git log --format='%H %ad %s' -1 cdd6ce7` shows the policy activation commit used as the boundary.
- `git log --format='%h %s' origin/main -- src/` returns exactly one commit (`10f5b8d`), which is how “once” is
  established without relying on memory; `git log --format='%h %s' origin/main -- test/` shows B's acceptance commit
  (`5f05f01`) arriving three days after that implementation commit.
- `docs/verification/policy.json` on `main` shows `status: active` and the named reviewers.
- `docs/verification/implementation-approvals.json` does not exist on `main`, and the candidate on
  `ci/member-b-gates` lists no approvals; that absence is why nothing is claimed.
- `main` has no `.github/` directory yet: the workflow and `CODEOWNERS` live on `ci/member-b-gates` and take effect only
  when PR #8 merges.
- Branch protection readback (E, 2026-11-22): six required contexts, `enforcement_level: everyone`.
- Gate re-run after merge: PR #8 head `6323cbc`, recorded in `docs/review-memo.md` and in the CI run link.
