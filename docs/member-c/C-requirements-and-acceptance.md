# C — How the requirements were fixed, and how a change is accepted (D1 input for the report and the demo)

Owner: C (Yuwei WANG, 60875477). Status: baseline `draft_ready`; bootstrap deviation accepted (ADR-B0006); human review
of the registry itself is still outstanding. Nothing here claims a human signature that does not exist.

## 1. How the requirements were fixed

1. **Collect, do not invent.** A (performance and cost), B (invariants and verifiability), E (security and governance) each
   submitted proposals; C added the functional scope and the user stories. Every upstream proposal is either accepted,
   merged into another ID, or explicitly rejected, and the decision is written down in
   `docs/req/requirement-id-map.yaml`. Nothing was deleted silently.
2. **One machine-readable registry.** `docs/req/requirements.yaml` holds 47 requirements in seven types
   (functional, invariant, quality, performance, cost, governance, security). Each entry carries an ID, a type, a MoSCoW
   priority, a *fit criterion that can be observed*, and the owner who must verify it.
3. **A schema that fails loudly.** `docs/req/req-schema.json` (Draft 2020-12) fixes the fields, the ID pattern, the seven
   types and the structure of a fit criterion. `scripts/validate_requirements.py` runs the same rules locally, so a
   malformed registry fails before any reviewer reads it.
4. **A PRD a person can read.** `docs/req/prd.yaml` carries scope, roles, ten user stories, the grading workflow, the
   acceptance summary, open questions and the glossary — so the registry is not the only artefact a reader needs.
5. **Duplicates merged with a record.** E's `REQ-SEC-001` and `REQ-SEC-005` were merged into `REQ-INV-007`;
   `REQ-SEC-003` into `REQ-INV-003`. B's eight invariants were all kept. Merging is a decision, so it is logged, not
   hidden.
6. **Change control.** No requirement text or threshold is edited without updating the ID map, the traceability evidence
   and `docs/ai-use-log.yaml`. That is `REQ-GOV-C01`, and it applies to this document as well.
7. **Conflicts freeze upward.** Where A and B named the same thing differently (`calculate_score` vs `calculate`,
   `validate_feedback` vs `validate_advice`, `GradeStore` vs `record_grade`), the requirement is written in
   implementation-neutral language and D decides in the architecture, not in the registry.

## 2. How a change is accepted — four layers, each able to say no

| Layer | Question it answers | Mechanism | Honest state on 2026-11-23 |
| --- | --- | --- | --- |
| L1 structure | Is the registry well formed and complete in coverage? | `schema` gate + `validate_requirements.py` | PASS (47 entries, seven types, unique IDs, ID map complete) |
| L2 traceability | Does every requirement point at a real, executable test? | `test-approval` gate + `docs/verification/test-map.yaml` | INCOMPLETE — `REQ-GOV-B01/B02/B05/B06` still without locators on `main` (B) |
| L3 review and CI | Was the exact head reviewed by a non-author, with six named checks green and the branch protected? | six named PR checks, `CODEOWNERS`, branch protection with `enforcement_level: everyone` | `main` has no `.github/` yet (workflow and `CODEOWNERS` are on PR #8); bootstrap deviation accepted up to `cdd6ce7`, strict from there; D's exact-head review pending |
| L4 semantics and performance | Does the system actually do what the requirements say, against an approved baseline? | authorised live replay of the five fixed cases + `semantic_thresholds` in `policy.json`; `REQ-PERF-003` live data | NOT RUN — needs A's authorised replay (thresholds: schema-valid 1.0, criterion coverage 1.0, supported-quote 1.0, adversarial escalation 1.0, safety escapes 0) |

**A locator is not an acceptance.** A test path in `test-map.yaml` proves that a test exists and is named after the
requirement; it does not prove the test is correct, was reviewed first, or that the behaviour is good. That is why L3
and L4 exist and why the report must not print "47/47 traced = accepted".

**Four words, used strictly.** `PASS` only for a check that ran and returned success on the exact head. `BLOCKED` for a
check that refuses because evidence is missing. `NOT RUN` for work nobody executed. `ACCEPTED DEVIATION` only for a
documented, dated, bounded exception such as ADR-B0006. No gate result is ever upgraded because the team ran out of time.

## 3. Who verifies what

- **C**: registry, schema, ID map, PRD, traceability handoff, this acceptance definition, and the bootstrap decision.
- **B**: locators for `REQ-GOV-B01/B02/B05/B06`, the two unrun mutations, and the CI result on the merged head.
- **D**: independent exact-head review of PR #8, the frozen architecture boundary, and the semantic acceptance criteria.
- **A**: authorised live model replay and the real performance sample for `REQ-PERF-003`.
- **E**: policy file, `CODEOWNERS`, repository protection, and the readback that proves it.

## 4. What this chapter must not claim

- That a human reviewer read the 47 requirements — no signature exists.
- That the semantic gate passed — no live replay was authorised.
- That traceability is complete — four requirements on `main` still have no locator.
- That the bootstrap deviation is an approval — it is a recorded, bounded exception, with the substantive gates still in
  force.
