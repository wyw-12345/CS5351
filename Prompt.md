# GradeAide member A startup prompt (D8 + D9)

You are implementing member A's scope. Follow AGENTS.md's reading order: C registry/PRD, D blueprint and ADR-0001..0004, E structural constraints, permissions/rules and E-to-A handoff, then available B verification contracts. Inspect actual files; missing B artifacts are a gap, not permission to invent replacements.

## Execution plan and gates

1. Identify applicable REQ IDs, the five modules, input/output contracts, frozen files, allowed changes and positive/negative tests. Present a concrete plan for human approval.
2. Before new feature implementation or test changes, obtain the required independent tests-only review. Preserve the real plan approval, exact reviewed commit and raw session location. A previous broad instruction to continue is not a new approval. Never self-approve.
3. Implement only the approved slice. The current integration reuses existing A work: required confidence (0.80 passes), ignored model total, local signed approval over submission/proposal/rubric/confirmed scores, idempotent schema-v2 persistence and CLI-only environment injection. Keep the calculator unchanged.
4. Run local offline checks before the next slice. Store authentic commands/results; run live checks only with deliberate operator opt-in. Keep byte-budget enforcement separate from the unmeasured token/compaction targets in ADR-0004.
5. Update the AI-use log and the existing handoff/state files. Independent exact-head safety review and B's formal gates are still required before acceptance/merge. If a required approval is absent, stop at that gate and report it; never fill in a signature.

## Scope

`src/feedback_engine.py`, `score_calculator.py`, `grade_store.py`, `cli.py`, `contracts.py`; versioned `prompts/`; `test/offline` and `test/live`; the existing examples/run scripts; `config/model.json` and pinned runtime dependency. Use D's package-relative API. The model has no tools and cannot write grades. All grade writes verify the external trusted key, bind exact scores and recompute the result.

B/E own CI gates, official API/permission snapshots, permission syntax, production key provisioning and runtime deployment isolation. Do not add alternate candidate versions of their artifacts or a parallel architecture. Do not edit C/D/E's source documents to claim approval.

For this rebuild, the requested action is integration of the existing A implementation and simple local verification. The earlier plan approval and current integration authorization remain in the conversation, but there is no independent tests-only PR approval or exact-head sign-off. Record the resulting branch as awaiting_review and hand the missing formal approval chain to B. See the dated handoff for actual evidence and provenance; the integration itself is not an approved implementation PR.
