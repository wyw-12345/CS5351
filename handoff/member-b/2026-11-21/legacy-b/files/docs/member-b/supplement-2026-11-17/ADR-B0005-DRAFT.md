# ADR-B0005 — B verification integration proposal

Status: DRAFT, not independently approved. Date: 2026-11-17.

Context: C's 47-ID registry and D's revised ADR-0001/0002/0003 supersede B's flat-module proposal; A's actual package API and E's still-pending enforcement must be assessed, not replaced.

Proposed changes: retain upstream application; re-point B acceptance and add confidence/signing/idempotency tests; add precise registered-ID validation, scripts/dependency and registry-coevolution checks; snapshot class methods and arguments; scan tracked source for common secret patterns; include src in required type checks; adapt real semantic replay to evaluate/validate_feedback and explicit live opt-in.

Alternatives rejected: changing A into a duplicate flat API; globally adding confidence to legacy fixtures before A supports it; claiming reviewer labels authenticate identity; lowering thresholds, hiding red tests or marking policy active without a real review.

Implementation boundary: tests are a draft tests-only change. Gate/CI/snapshot changes under proposals/ are an unmerged candidate for independent human review. Existing `.opencode`, `.agent`, AGENTS, policy and workflow remain unchanged in the source worktree. Reviewers must accept and apply the candidate in the real team Git workflow; this draft does not grant permissions or retroactively approve tests.

Signing seam: B proposes additive trusted_keys/approval/submission_id parameters solely to make ADR-0002/0003 executable as a target test contract. Exact signatures and key format await A/D agreement. Real ephemeral Ed25519 test keys exercise the proposed protocol; there is no fake production verifier and no key stored on disk.

Limits: schema/map PASS means locators and IDs are coherent, not that every fit criterion is behaviorally satisfied. Real source safety, runtime permissions, authenticated approval and API evaluation retain failures or NOT RUN until their owners deliver evidence. Secret-pattern scans complement, not prove, complete absence of all possible secrets.
