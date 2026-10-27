# Week 11 Production Drill Report

## Time-to-Find
- **0.0s**
- Slice used: **Output pattern search** (searched judge verdicts + retrieved docs)

## Finding
The bad answer is in claim **CLM-2026-0018** at **2026-10-26T14:45:23Z**.

The model said: "Water damage is covered"

But it retrieved the exclusion document (doc-0304-ex-e17).
The model had the exclusion in context and ignored it.

## Why This Matters
This is outcome-verdict disagreement: the judge said GOOD (pass), but the verdict is wrong.
The agent retrieved evidence that contradicts its own answer. This is a **time bomb** —
the answer works on the happy path but fails when policy logic is complex.

## Trace Saved
See trace.json for per-span details: latency, tokens, cost, prompt version, context ids.

## Next Steps
1. Create eval case with this claim
2. Show RED before fix (verdict=GOOD when it should be FAIL)
3. Fix at prompt or retrieval layer
4. Show GREEN after fix
5. Cost breakdown by stage
6. 10x volume analysis
