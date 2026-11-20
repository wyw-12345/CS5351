# Memory design (D2)

> Owner: D. Status: baseline. Companion to ADR-0004. Budgets are **design targets**, not measured.

## Principle

GradeAide's AI component is **stateless across essays**. It has no conversation memory, no retrieval
store, no cross-essay learning, and no training/calibration. The only "memory" is (a) the per-request
context assembly and (b) the durable grading records owned exclusively by `grade_store`.

## 1. Working (in-request) memory

- Single request, single response. `messages = [system(L0,L3), user(L1,L2)]`
  (`feedback_engine.py:210-211`); no prior turns, no tools (`:248-250` rejects tool/function calls).
- Full L0 constraints re-injected **every** call; there is no state carried across calls
  (A-ADR-001 `:30`).
- Determinism aid: `temperature=0`, `response_format=json_object`, `stream=False` (`:222-223`).

## 2. Context budget (byte guard enforced; token cap is a design target)

| Budget | Value | Unit | Where | Status |
|---|---|---|---|---|
| Input guard (enforced) | 12 000 | UTF-8 bytes | `max_input_bytes` | implemented; retained |
| **Token context cap (target)** | 8 000 | tokens | — | **design target, unmeasured** |
| Output cap | 1 024 | tokens | `max_output_tokens` | implemented |
| Response byte cap | 100 000 | bytes | `max_response_bytes` | implemented |
| Per-attempt cost budget | configured `MAX_COST` | currency | `Settings.max_cost` | implemented (Decimal) |
| Timeout | 30 s, 0 retries | seconds | `Settings.timeout` | implemented |

**Binding limit:** until the token method is validated, the **12 000-byte guard is the enforced limit**;
the token cap is advisory and the stricter limit trips first once both are enforced.

**Counting / estimation method:** provider tokenizer (or offline mirror) on the exact serialized
`messages`; fallback is a documented bytes-per-token **upper-bound estimator** calibrated so
`estimated_tokens ≥ actual_tokens`. The current method string is
`"serialized messages UTF-8 bytes, conservative token proxy"` (`feedback_engine.py:207`).

**Byte-vs-token evidence needed:** an EN/ZH/boundary study showing the estimator is a safe upper bound
and recording actual provider `usage.prompt_tokens` alongside; see `evaluation-logbook.md` (E8).

## 3. Compaction

- **Not implemented in this baseline.** No summarization, no truncation, no chunking.
- **Proposed compaction threshold: 6 000 tokens** of assembled context (token-based design target, below
  the 8 000-token cap to leave room for re-injected constraints). When reached in a future release it
  enters the compaction path; today, the 12 000-byte guard trips first and the attempt escalates with
  `input_budget_exceeded`, zero calls.
- **Critical-constraint re-injection after compaction (rule fixed now):** L0 standing constraints,
  L1 rubric, and L3 output schema are re-injected **verbatim in full**; only L2 essay body may be
  reduced, preserving byte-for-byte quotable spans; if L0+L1+L3 alone exceed the budget → escalate,
  never drop L0/L1/L3. (Detail: ADR-0004 §5.)

## 4. Durable memory = the grade store (not AI memory)

| Property | Design |
|---|---|
| Owner | `grade_store` only (single writer) |
| Backend | SQLite, schema version `user_version=1`, additive migration only |
| Contents | `proposals` (payload + digest + status) and `grades` (score + audit + digest) |
| PII policy | store essay/rubric/advice in proposal payload (local, single-user) but **audit record holds digests, not essay text** for external/report artifacts; export must exclude raw essays |
| Integrity | read-time digest re-verification (`grade_store.py:112-153`) |
| Retention/deletion | not automated in baseline; deletion is a human DB operation, out of AI authority |

The AI component **cannot read or write** durable memory (import boundary INV-07). It receives essay +
rubric as function arguments and returns advice; it never persists.

## 5. Privacy note

Essays may contain student personal data. This baseline is local, so no network storage beyond the
single provider request (essay is sent to the configured provider as prompt data). Evidence quotes are
persisted inside the proposal payload for teacher review; external report artifacts must use hashes and
non-identifying fields. Recorded in `risk-list.md` (R-06).

## Reopening conditions

- Long-text grading becomes a Must (context exceeds the byte guard) → design compaction/chunking with
  an evaluation, and promote the token cap to enforced (ADR-0004).
- Multi-user/hosted deployment → durable-memory design (concurrency, access control, retention)
  requires a new ADR.
