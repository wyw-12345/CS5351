# Candidate evaluation table (D2)

> Owner: D. Status: baseline. This table records **candidate architectural options and their
> evaluated ranking as analysis**, plus the candidate AI-quality metrics. **No option below has been
> measured**; entries are `analysis` (reasoned) unless a column says `measured`. Per the team plan,
> unmeasured candidates are labelled "分析/待实测".

## Part 1 — Architecture alternatives evaluation

Scoring: ✅ strong, ◐ partial, ✗ weak. "Evidence" says how it would be proven.

### Escalation policy (ADR-0001)

| Option | Safety (no silent grade) | Determinism/testability | Matches team decision (resolvable) | Cost (false-escalation) | Verdict |
|---|---|---|---|---|---|
| A-only boolean `uncertain`, reject `final_score` | ◐ (relies on self-report) | ◐ | ✅ | ◐ | superseded (D2 trigger kept) |
| **D1+D2+D3+D4 with `confidence ≥ 0.80`, ignore `final_score`** | ✅ | ✅ (except D2 + confidence self-report) | ✅ | ◐ (0.80 unmeasured) | **selected — aligned with C** |
| Escalate = permanent refusal | ✅ | ✅ | ✗ (reverses decision) | ✗ | rejected |

Evidence to compare: fixed eval set (≥30 cases) → unsafe-pass rate, false-escalation rate; mutation
kill for D1/D2/D4; boundary check that exactly `0.80` passes. Status: **design decided (C-aligned);
effectiveness 待实测**.

### Approval binding (ADR-0002)

| Option | Non-repudiation | Fits single-user CLI | Impl cost | Multi-user ready | Verdict |
|---|---|---|---|---|---|
| A: reviewer string + proposal hash | ✗ | ✅ | low | ✗ | rejected (no authentication) |
| **Local signing key + trusted public-key verify (this ADR)** | ✅ (key possession) | ✅ | medium | ◐ | **selected — aligned with C** |
| B/E: injected `verify_approval` / token service | ✅ | ◐ (needs service) | high | ✅ | future / reopening |

Evidence: unauthorized-signer, score-substitution, signature-replay negatives; altered-scores test.
Status: **design decided (C-aligned); tests planned; no signing in `src/` yet**.

### Calculator arithmetic (ADR-0003)

| Option | Exactness at ties | Determinism | Complexity | Verdict |
|---|---|---|---|---|
| Float | ✗ | ✗ | trivial | rejected |
| Decimal with intermediate division | ✗ (50.005→50.00) | ✅ | low | rejected (A-ADR-001) |
| **Fraction accumulate + integer half-up** | ✅ | ✅ | low | **selected** |
| Decimal high precision (more digits) | ✗ (ties persist) | ✅ | low | rejected |

Evidence: 50.005→50.01, 66.665→66.67, 20× repeatability — **measured** (existing tests).

### Persistence (ADR-0003)

| Option | Atomic | Audit | Ops cost | Verdict |
|---|---|---|---|---|
| **SQLite single transaction** | ✅ | ✅ | low | **selected** |
| JSON file + temp-rename | ◐ | ◐ | low | rejected (weaker integrity) |
| External DB/service | ✅ | ✅ | high | rejected (scope) |

Evidence: rollback + restart + tamper tests — **existing**.

### Configuration injection (ADR-0003)

| Option | Meets E "no `os` in engine" | Verdict |
|---|---|---|
| **CLI reads env → validated `Settings` value object** | ✅ | **selected** |
| Engine reads `os.environ` (current) | ✗ | rejected (E violation) |
| Config file with secrets | ✗ (secret in repo) | rejected (REQ-SEC-004) |

## Part 2 — AI-quality candidate metrics (behavioral tier)

These are the metrics the fixed evaluation set must report; all currently **待实测** (only synthetic
fixtures exist; no genuine provider run in this package).

| Metric | Target | Verification | Status |
|---|---|---|---|
| Rubric-ID coverage | = 1.0 (every criterion once) | replay `test/live/fixed-cases.json` | 待实测 (synthetic only) |
| Schema-valid responses | = 1.0 | validator | existing synthetic |
| Evidence-quote supported by essay | = 1.0 | substring + human | synthetic only |
| Adversarial escalation rate | = 1.0 | fixed adversarial case | governance self-test existing; live 待实测 |
| Safety escapes | = 0 | behavioral suite | 待实测 |
| False-escalation rate | within teacher tolerance | human labels | 待实测 (needed for 0.80) |
| Unsafe-pass rate | = 0 | human score diffs | 待实测 (needed for 0.80) |

## Part 3 — Confidence threshold (ADR-0001) — **resolved: aligned with C baseline**

C's REQ-FUNC-002/003 require a `confidence` field and `≥ 0.80` acceptance. **D has adopted this**
(ADR-0001): confidence is required and validated; `< 0.80` escalates, `== 0.80` passes. The threshold's
**effectiveness is still unevaluated** (hence "待实测" below), but it is now the required architecture
behavior, not a candidate. The current code emits no confidence; implementation is pending (A/B).

| Threshold | Boundary behavior | Unsafe-pass (target 0) | False-escalation | Status |
|---|---|---|---|---|
| **0.80 (C draft — adopted)** | `< 0.80` escalates; `== 0.80` passes | unknown | unknown | **adopted; effectiveness 待实测** |
| TBD (measured) | — | unknown | unknown | may revise the constant → amend C's draft |

Evaluating effectiveness requires the evidence in ADR-0001 "Threshold source and candidate evidence"
(false-escalation vs unsafe-pass curve on a fixed set, provider emits consistent `confidence`). If the
measurement later shows 0.80 is poor, D would amend the ADR and propose a revised constant to C.
