# Requirements review record (D1, member C)

- Date: 2026-11-12
- Author/owner: member C (requirements engineering)
- Baseline: `docs/req/requirements.yaml` version 0.1.0-c
- Status: `draft_ready` — C's consolidation is complete enough for D to read. **No real human review or approval is claimed.**
- Next owner: D (architecture), then B (fit-criterion/test review), with A/E confirmation for their domains.

## 1. What was reviewed

| Input | Owner | How C used it | Outcome |
|---|---|---|---|
| `docs/member-a/requirements-candidates.yaml` | A | Kept the three performance and five cost proposals; checked thresholds against A's implementation evidence | 8 accepted |
| `docs/member-b/requirements-proposal.yaml` | B | Kept all eight invariants and all six governance gates; checked zero-tolerance thresholds | 14 accepted |
| `docs/member-e/requirements-proposal.yaml` | E | Kept no-fabrication, no-secrets, least-privilege and four governance controls; merged three duplicates into invariants | 7 accepted, 3 merged |
| `CS5351-2026-2027-project.pdf` D1/D4 | course | Checked the seven required types, fit-criterion shape, MoSCoW and tradeoff fields | covered |
| `docs/member-b/01-handoff-to-C.md` | B | Checked the explicit boundary list (Decimal, weights sum to 1, range, two decimals, no silent zero, idempotency) | covered by FUNC/INV |
| `docs/member-b/02-interface-contract.md` | B | Used as a proposed contract only; did **not** treat it as architecture | interface differences left for D |
| `docs/verification/test-map.yaml` | B | Used to identify existing test locators | existing 14 mappings retained; new IDs still need mapping |
| `src/` and `test/` | A/B | Checked actual function names and observable behavior | requirements written interface-neutrally |

## 2. C's fit-criterion self-check

Checklist applied to every one of the 47 entries:

- [x] Stable ID matching `REQ-[A-Z]+-[A-Z0-9]+`.
- [x] One of the seven required types.
- [x] Statement describes an observable obligation, not a vague aspiration.
- [x] Fit criterion has `metric`, `threshold` and `verification`.
- [x] MoSCoW priority is present.
- [x] Source is named and, where relevant, linked to the proposal file.
- [x] Tradeoff is explicit.
- [x] Invariants have a numeric zero-tolerance threshold (`0`).
- [x] No requirement silently drops a B invariant.

## 3. Decisions that need a named human

| Decision | Current C position | Reviewer needed | Why it matters |
|---|---|---|---|
| Merge E `REQ-SEC-001` and `REQ-SEC-005` into `REQ-INV-007` | Accepted as a merge, not a deletion | E + B | Avoids duplicate invariants; E should confirm the security intent is preserved |
| Merge E `REQ-SEC-003` into `REQ-INV-003` | Accepted | E + B | The invariant is the stronger zero-tolerance statement |
| Keep `REQ-INV-005` implementation-neutral | Accepted | D + A + B | A uses exact `Fraction`; B proposed `Decimal`; the observable rule is one HALF_UP rounding |
| Keep `REQ-PERF-001/003` as `Should` with measured evidence | Accepted | A + D | Thresholds must be tied to the final deployment, not a laptop-only claim |
| Keep `REQ-QUAL-001..005` as C drafts | Accepted | D | D owns the quality-attribute scenarios and ASR |
| Keep `REQ-QUAL-005` as `Should` / TBC | Accepted with a visible gap | D + B | The current test checks audit fields but does not explicitly assert that a second essay copy is absent |
| No fixed rubric exchange shape in requirements | Accepted | D | A's object shape and B's list shape differ; D must freeze one |
| Do not edit tests to make traceability green | Accepted | B | C must not fabricate mappings or contaminate test provenance |

## 4. Review requests (not yet answered)

The following requests are recorded so the next owner can act. They are **not** approvals.

- **B:** review every fit criterion and add a per-test docstring / `docs/verification/test-map.yaml` entry for each new ID. Current gate status is "schema format pass, traceability blocked".
- **D:** confirm quality-attribute thresholds, freeze the runtime interface, and add every requirement to the trace matrix with an enforcing component and runtime monitor.
- **A:** confirm the measured calculator p95, the final live deployment target, and the exact context-budget configuration.
- **E:** confirm that the merged security requirements preserve the intended permission model and authenticated-approval boundary.
- **All:** review the ID map before adding any new requirement IDs.

## 5. Known inconsistencies carried forward

1. **Interface names:** A implements `calculate_score`, `validate_feedback`, `GradeStore`; B proposed `calculate`, `validate_advice`, `record_grade`. C's requirements are behavior-level and do not choose a winner. D must freeze the interface.
2. **Arithmetic:** A uses exact `Fraction` and an integer half-up step; B proposed `Decimal`. C's invariant states the observable result (exact, one HALF_UP rounding).
3. **Traceability:** the current A tests do not carry per-function `REQ-*` docstrings; B's proposed tests target an interface A did not implement. `tools/gates.py schema` can validate the registry but cannot pass traceability yet.
4. **Quality thresholds:** C drafted five quality requirements, but D has not delivered the ASR/quality-attribute baseline.
5. **Approval identity:** A's working implementation uses a local reviewer string; E's proposal wants an authenticated verifier. The invariant is clear; the mechanism is still a D/E decision.

## 6. Sign-off

| Role | Name / student ID | Review scope | Verdict | Date |
|---|---|---|---|---|
| C (author) | not supplied | consolidation and schema | draft complete | 2026-11-12 |
| B | not supplied | fit criteria and test mapping | pending | — |
| D | not supplied | quality attributes and interfaces | pending | — |
| A | not supplied | performance and cost | pending | — |
| E | not supplied | security and governance | pending | — |

> The absence of names above is deliberate. An AI must not invent a human reviewer or a signature.
