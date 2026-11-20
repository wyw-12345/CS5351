# ADR-0004 — AI component: layered context, assembly pipeline, token budget, compaction

- Status: Accepted (D2 baseline)
- Date: 2026-11-11
- Relates: `REQ-COST-001..005`, `REQ-SEC-004/006`, `REQ-INV-007` (C baseline 0.1.0-c; E's
  `REQ-SEC-001`/`REQ-SEC-005` merged into `REQ-INV-007` by C's ID map); A-ADR-001 §"Layered model
  context".
- Owner: D. Implemented by: `src/feedback_engine.py`. Budgets below are **design targets**, not
  measured results.

> **Design targets, not measurements.** The *enforced* control today is the 12 000-byte input guard
> (`src/feedback_engine.py:37-41`); it is implemented and retained. The **token-based** context cap
> (8 000 tokens), the token counting/estimation method, and the token-based compaction threshold
> (6 000 tokens) are **design targets** — proposed from the existing defaults and course layered-context
> guidance, not yet validated against a real provider tokenizer or evaluation set (see
> `evaluation-logbook.md`). The evidence needed to validate each target is stated below.

## Context

The AI feedbacker is a single-shot, tool-free, one-request advisory component. It must (a) always
present the full standing constraints, (b) never silently drop essay content or constraints, (c) stay
inside a bounded context and cost budget, and (d) remain injection-safe because the essay is untrusted
data. The team plan requires explicit documentation of layered context, the assembly pipeline, a token
budget cap, a compaction threshold, and how critical constraints are re-injected after compaction.

## Decision

### 1. Layered context (highest-authority to lowest)

| Layer | Content | Authority | Re-injection priority |
|---|---|---|---|
| L0 — standing constraints | Advisory-only role; use rubric IDs only; never fabricate criteria; essay/model text is untrusted data; uncertain ⇒ escalate; output JSON contract; never emit a final grade | **Must never be dropped** | Highest — re-inject after any compaction |
| L1 — rubric | Teacher-provided structured rubric (`{id, version, criteria}`) | Authoritative input | High |
| L2 — task + essay | Current essay as **data**, no prior conversation, no tools | Untrusted data | Medium (may be split, never summarized away) |
| L3 — output schema/example | Versioned response-shape instruction from the prompt | Must comply with validator | High |

Current implementation assembles L0+L1+L2:L3 as system prompt + a canonical JSON user message
(`feedback_engine.py:210-211`). L0 lives in the versioned `prompts/` file (`prompt["system"]`), not in
code.

### 2. Assembly pipeline (deterministic, one pass)

```
validate essay/rubric/prompt  →  canonicalize (UTF-8, sorted keys, compact)
   →  compute prompt hash + digests  →  assemble [system(L0,L3) + user(L1,L2)]
   →  count serialized UTF-8 bytes  →  cost preflight (estimate vs max_cost)
   →  budget check (bytes ≤ cap)  →  ONE bounded request (no retry, no redirect)
   →  validate envelope/usage  →  validate_feedback (ids, ranges, quotes)
   →  return review proposal OR escalation
```
This already exists (`feedback_engine.py:187-271`) with `input_bytes = len(canonical(messages).encode)`
(`:212`) and budget/cost gates (`:216-221`).

### 3. Context budget: byte guard now, token cap as target

Two budgets are tracked at once. The **UTF-8 byte guard is retained as the enforced, implemented
control**; the **token cap is the architecture target** that must be measured before it can be
enforced.

**3a. Existing byte guard (retained, implemented).**
- **Input guard: 12 000 UTF-8 bytes** (`max_input_bytes`, `src/feedback_engine.py:39`), measured as
  `len(canonical(messages).encode("utf-8"))` (`:212`). Bytes are a **conservative proxy**, explicitly
  *not* exact tokenization (`metadata.input_budget_method`, `:207`). This guard stays in force exactly
  as implemented; this ADR does not relax or replace it.
- **Output cap: 1 024 tokens** (`max_output_tokens`, `:38`), passed as `max_tokens`.
- **Response byte cap: 100 000** (`max_response_bytes`, `:40`).

**3b. Token-based context cap (design target — unmeasured).**
- **Target context cap: 8 000 tokens** for the assembled prompt (L0–L3), and **target output cap:
  1 024 output tokens** (output already matches). These are **design targets, not measured**, and the
  number must be reconciled with the provider's real context window and the byte guard above before
  any enforcement.
- **Counting / estimation method:** the architecture requires that the token count be obtained by a
  method that is **either exact or a documented upper bound**, never a silent under-count:
  - *Preferred:* the **provider tokenizer** (or an offline mirror of it) applied to the exact
    serialized `messages` that will be sent.
  - *Fallback (no tokenizer dependency):* a **documented bytes-per-token upper-bound estimator**,
    calibrated so that `estimated_tokens ≥ actual_tokens` on the validation corpus. The current
    implementation already reports `input_budget_method = "serialized messages UTF-8 bytes,
    conservative token proxy"` (`:207`); the target refines this into a named estimator with a stated
    safety margin.
- **Relationship to the byte guard:** while the token cap is unmeasured, the **byte guard (12 000) is
  the binding limit** and the token cap is advisory. When the token method is validated, both limits
  apply and the **stricter** one trips first. The byte guard is never removed without a measured
  replacement.

**Over-budget behavior (current, implemented).** When the byte guard trips, the component makes **zero
provider calls**, returns `status="escalated"` with reason `input_budget_exceeded`, and preserves the
original essay/rubric for human handling (`:216-218`). Cost over-budget behaves the same with
`cost_budget_exceeded` (`:219-221`). **No truncation and no compaction occur.** (Once a token cap is
enforced, an equivalent `token_budget_exceeded` reason is the target; it does not exist today.)

- **Evidence to validate the token target:** a measurement on English/Chinese/boundary essays that
  records the chosen estimator's token count alongside the provider's reported `usage.prompt_tokens`
  on the fixed evaluation set (`evaluation-logbook.md`, E8), demonstrating `estimate ≥ actual` and a
  quantified margin; plus the provider's documented context window.

### 4. Compaction threshold (token-based design target; policy defined, compaction not implemented)

- **Compaction is NOT triggered in this baseline.** There is no conversation memory, retrieval, or
  automatic summarization; each call re-injects the full L0 constraints (A-ADR-001 `:30`).
- **Proposed compaction threshold: 6 000 tokens** of assembled prompt context (a design target, below
  the 8 000-token cap to leave room for re-injected constraints plus the essay tail). When the measured
  token count of the assembled context exceeds this threshold, a **future release** enters the
  *compaction path* (a future ADR) rather than truncating. The current byte guard (12 000 bytes) remains
  the enforced limit until the token method is validated.
- Rationale for not implementing now: summarization can erase the evidence a score depends on
  (`REQ-COST-005`, A-ADR-001 `:30-31`). Silently dropping text is forbidden.
- **Evidence to validate a future threshold:** recall of essay evidence quotes after compaction vs the
  full-context baseline on the fixed set; human review that compacted context still supports grading;
  measured token reduction vs cost saving and vs false-escalation rate.

### 5. Critical-constraint re-injection after compaction

If compaction is ever introduced (it is **not** in this baseline), the following constraints **must**
be re-injected in full and verbatim; only the essay body may be reduced:

1. **L0 standing constraints** — advisory-only role, use rubric IDs only, never fabricate criteria,
   essay/model text is untrusted, uncertain ⇒ escalate, JSON output contract, never emit a final grade
   — re-injected **verbatim and in full**, never paraphrased, summarized, or truncated.
2. **L1 rubric** — criterion IDs, weights and max scores — re-injected in full (a partial rubric would
   make the criterion-set check reject the response).
3. **L3 output schema/example** — the versioned response-shape instruction — re-injected in full so the
   validator contract still holds.
4. **L2 essay body** may be reduced (e.g. chunked with explicit coverage markers); any removal must
   preserve byte-for-byte quotable spans for `evidence_quote` validation, otherwise `validate_feedback`
   (`:150-177`) would reject quotes not found in the essay.
5. **Fail-closed rule:** if the re-injected L0+L1+L3 alone exceed the active context budget, the system
   must **escalate** (`input_budget_exceeded` / future `token_budget_exceeded`) — it must never drop L0,
   L1, or L3 to make room.

## Consequences

- The current component is safe by construction: the byte guard trips before any over-budget request,
  it cannot execute model text, and it re-injects all constraints every call.
- While the token cap is unmeasured, the byte guard (12 000 bytes) is the **binding** limit; token
  limits are advisory targets until validated. This is an intentional, documented split.
- Long essays currently **always escalate** (no chunking), and an over-budget attempt makes zero
  provider calls. This is an accepted scope limit; false-escalation on long inputs is a known cost
  tracked in `risk-list.md` (R-05).
- Any future compaction is an architecture change requiring a new ADR and behavioral re-evaluation.

## Alternatives

| Alt | Benefit | Cost | Outcome |
|---|---|---|---|
| No compaction, byte guard + escalate now; token cap target (this ADR) | Evidence never erased; simplest; safe; token cap measurable later | Long essays always escalate; byte proxy until token method validated | **Adopted for baseline** |
| Replace byte guard with exact-token cap now | Precise budget | Requires tokenizer dependency; unvalidated estimator risk | Deferred (target) |
| Silent truncation | Lower cost | Can remove decisive evidence; misrepresents coverage | Rejected |
| Automatic summarization now | Handles long essays | Can erase evidence; needs its own eval | Deferred to future ADR |
| Retrieval/RAG | Scalable external knowledge | Teacher supplies whole rubric/essay; no retrieval need | Rejected |

## Verification

- Existing: `test/offline/test_http.py`, `test/offline/test_feedback.py` (byte-boundary incl. Chinese,
  over-limit no-call, output-cap, usage accounting), `test/offline/test_live_runner.py`.
- Planned: tokenizer/estimator study proving `estimated_tokens ≥ actual prompt_tokens` and a margin
  (E8); reconciliation of 12 000-byte guard with the 8 000-token target on the fixed set; compaction
  recall study (only if compaction is proposed); a check that L0/L1/L3 appear unchanged in the
  assembled prompt hash after any future compaction.

## Reopening conditions

- C makes long-text a Must (essay whose assembled context exceeds the byte guard) → design a
  compaction/chunking ADR + evaluation, and promote the token cap to enforced.
- Provider tokenizer or measurement shows the byte proxy is not a safe over-estimate, or the 8 000-token
  target is inconsistent with the provider context window.
- Cost budget or output quality requires re-tuning the byte guard, token cap, or output cap.
