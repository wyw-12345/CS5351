# Technical debt register

All entries opened 2026-11-06; owner B unless stated otherwise. Status OPEN unless noted. No estimated completion date is invented. DEBT-02 is **MITIGATED for this local preparation baseline**: requirements-ci.txt pins all 41 dependencies and actual pip check/pip-audit passed with zero known vulnerabilities; it reopens whenever dependencies change. Application dependencies remain A's responsibility.

| ID | AI-era category | Concrete gap / consequence | Owner | Exit evidence / review trigger |
|---|---|---|---|---|
| DEBT-01 | Prompt rot | Prompt/version/model baseline absent; no meaningful semantic evidence | A | Approved prompt hash and fixed real-model run before implementation acceptance |
| DEBT-02 | Hallucinated dependencies | CI dependencies require pinned versions and a successful vulnerability audit | B | Lockfile + pip check + clean pip-audit; every dependency update |
| DEBT-03 | Untouchable code | Calculator freeze not yet defined by D/E | D/E | ADR + CODEOWNERS/protection + mutation tests before scoring release |
| DEBT-04 | Hidden dependencies | Proposed Python interfaces not accepted by A | A/B | Signed interface review and direct module tests before integration |
| DEBT-05 | Agent-induced bloat | Gate tooling must stay bounded to six requirements | B | Review each added dependency/function against a gate before merge |
| DEBT-06 | Evaluation debt | No genuine model outputs or teacher relevance labels | A/B | Real fixed-set run + teacher labels; prompt/model changes |
| DEBT-07 | Guardrail debt | Runtime permissions/approval verifier/atomic audit not implemented | E/A | Unauthorized-write and fault-injection evidence before live use |
| DEBT-08 | Human/cognitive debt | Tests-before-code order and meaning of approval need team training | All | Real tests-only PR, human review, then implementation PR and raw transcript |
| DEBT-09 | Guardrail debt | GitHub repo/protection not yet connected | B | Real URL, six required contexts and protection API readback |
| DEBT-10 | Evaluation debt | Governance tool self-tests do not demonstrate application correctness | B | C→D→E→A handoff plus full offline/live/mutation evidence |



## Update 2026-11-17 (preserve historical entries above)

C's requirements, D's architecture, A's source and genuine historical model outputs now exist; the earlier absence statements describe the old baseline. B has prepared 47-ID candidate coverage, API/permission snapshots, typed gates, real secret-pattern checks and application mutants. Remaining debt: unimplemented A confidence/signing/submission behavior; unreviewed A signing seam; E key custody/runtime enforcement; C/D calibration labels; real GitHub approvals/protection; 3 unrun application mutation obligations and full human-annotated raw lifecycle evidence. Root policy remains pending. Gate/CI proposals are FIX READY FOR REVIEW, not deployed or approved.
