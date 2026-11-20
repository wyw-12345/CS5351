# Option ledger (D2)

> Owner: D. Status: baseline. Tracks every architectural option considered, its evaluation basis, the
> decision, and the concrete condition under which it can be reopened. Complements ADRs (which contain
> the full rationale) and `evaluation-table.md` (which scores them).

| # | Decision area | Options | Chosen | Basis | Reopen condition |
|---|---|---|---|---|---|
| O1 | Scope / deployment | (a) trusted single-teacher CLI; (b) multi-user hosted web; (c) desktop app | **(a)** | A-ADR-001 scope; single-user threat model; lowest pre-core risk | >1 teacher or any remote approval path |
| O2 | Escalation trigger | (a) boolean `uncertain` only; (b) `confidence ≥ 0.80` only; (c) hybrid D1+D2+D3; (d) permanent refusal | **(c)** | deterministic + self-report; testable; resolvable per team decision | C requires `confidence`; eval justifies threshold; product forbids resolving escalations |
| O3 | Confidence threshold | (a) none; (b) 0.80; (c) measured TBD | **(b) 0.80 — DECIDED (aligned with C)** | C REQ-FUNC-002/003 require confidence + 0.80; user directed D to follow C's draft. Effectiveness unevaluated (ADR-0001). | effectiveness evaluation (false-escalation/unsafe-pass curve) may revise the constant → amend C's draft |
| O4 | `final_score` in advice | (a) reject as error (A); (b) ignore as untrusted (B/E) | **(b)** | benign field shouldn't force escalation; never persisted | provider mandates/expands final score semantics |
| O5 | Reviewer identity | (a) free-text label (A); (b) injected verifier (B/E); (c) signed token; (d) local signing key covering confirmed scores | **(d) local signing key — DECIDED (aligned with C)** | C's REQ-INV-003 demands authenticity; (d) gives offline authenticity + G2 binding without a service; name stays an audit label. | multi-user token service; or credential-store change (amend ADR-0002) |
| O6 | Approval binding fields | (a) proposal hash only; (b) hash + rubric version + hash-of-confirmed-scores (G2, this ADR); (c) + signed token over 4 digests | **(b)** | separates G1 validation from G2 binding; covers proposal, rubric version, exact confirmed scores; identity deferred | multi-user; external audit |
| O7 | Calculator arithmetic | (a) float; (b) Decimal+intermediate div; (c) Fraction+integer half-up; (d) high-precision Decimal | **(c)** | exact at ties; measured 50.005 case | new provably-exact method; C changes quantum |
| O8 | Decimal-only wording (E) | (a) literally decimal/typing/...; (b) add `fractions` | **(b)** | exact rounding requirement | E produces exact Decimal-only method |
| O9 | API shape | (a) A package-relative `calculate_score`/`evaluate`/`GradeStore`; (b) B/E flat `calculate`/`validate_advice`/`record_grade`; (c) both via aliases | **(a) + optional aliases** | don't fork logic; minimal churn | A changes layout; B can't re-point tests |
| O10 | Rubric weights | (a) strictly positive sum=1 (A); (b) allow zero weight (B/E) | **(a)** | zero-weight hides scoring errors | C mandates optional criteria |
| O11 | Submission identity | (a) random proposal_id (A); (b) caller submission_id (B/E) | **(b) + keep proposal_id internal** | needed for idempotency/binding | C defines different external key |
| O12 | Duplicate requests | (a) reject any duplicate (A); (b) idempotent identical / conflict different (B/E) | **(b)** | retries safe; conflicts preserve history | C wants reject-on-any-duplicate |
| O13 | Persistence backend | (a) SQLite txn (A); (b) JSON+rename; (c) external DB | **(a)** | atomic+audit without infra | multi-writer/concurrency required |
| O14 | Config injection | (a) env in engine (A); (b) CLI reads env → Settings value object | **(b)** | E forbids `os` in engine | C requires in-engine; E relaxes rule |
| O15 | Compaction | (a) none, hard cap + escalate; (b) silent truncation; (c) summarization; (d) RAG | **(a) now, (c) future ADR** | evidence must not be erased | long text becomes Must |
| O16 | Critical-constraint reinjection | (a) undefined; (b) verbatim L0+L1+L3 post-compaction | **(b)** | prevents constraint loss | compaction design changes |
| O17 | Context budget unit | (a) exact tokens (tokenizer dep); (b) UTF-8 bytes (A); (c) bytes now + token cap target | **(c)** | byte guard retained/enforced, token cap measured before enforcement | token estimator validated → enforce both |
| O18 | Model provider SDK | (a) stdlib `http.client` one-shot; (b) vendor SDK | **(a)** | no implicit retries/redirects; control | provider requires SDK-only features |

## Decisions resolved (aligned with C baseline 0.1.0-c)

- **Decision-1 (O3):** C REQ-FUNC-002/003 require a `confidence` field with `≥ 0.80`; D adopts it.
  ADR-0001 updated: confidence is required, validated, and `>= 0.80` passes (below escalates);
  effectiveness unevaluated. Implementation pending (A/B).
- **Decision-2 (O5):** C REQ-INV-003 requires authentic human approval; D adopts a **local signing key**
  (Option d) signing `H(canonical(submission_id, proposal_hash, rubric_id, rubric_version,
  confirmed_scores_sha256))`, verified against a trusted public key. Name stays an audit label.
  ADR-0002 updated; implementation pending (A/E/B). Authenticated multi-user token service stays out of
  scope.

## Unresolved (owned by C / to confirm)

- O11: canonical uniqueness rule for `submission_id`.
- O1–O18 evidence should be re-checked against C's formal IDs now that the registry exists (R-01);
  the trace matrix already uses C IDs, but the option ledger's "reopen" evidence still cites A/B/E
  source labels.

## Baseline review status

C's requirements registry **0.1.0-c (47 entries)** is `draft_ready`, **pending human review** (no
signatures). Both architecture decisions above are resolved and aligned with C's draft; their
implementation is pending.
