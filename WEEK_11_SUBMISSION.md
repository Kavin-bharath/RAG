# Week 11: Production Observability - Find and Fix Bad Coverage Answer

## Executive Summary

**Objective**: Find a planted bad coverage answer in production logs within 5 minutes, turn it into an eval case, show RED→GREEN fix, and provide cost/scale analysis.

**Result**: ✓ FOUND in **0.00s** (essentially instant) — claim CLM-2026-0018

---

## Part 1: Production Drill - Finding the Bad Answer

### Time-to-Find: **0.00s**

**Finding**: Claim **CLM-2026-0018** at **2026-10-26T14:45:23Z**
- **What the agent said**: "Water damage is covered"
- **What it actually retrieved**: Exclusion doc (doc-0304-ex-e17, which is Exclusion E-17: Water backup)
- **Judge verdict**: GOOD (passed the judge)
- **The bug**: Agent had the evidence (exclusion doc) but ignored it — outcome-verdict mismatch

### Why It's a Time Bomb

This is NOT just a wrong answer. This is worse:
1. The judge (LLM-as-judge) said "GOOD" — passed QA
2. But the answer contradicts retrieved evidence
3. The agent will fail silently on complex cases where logic matters

When the claimant asks "Is water backup covered?" and the agent says "yes", that's bad. When the agent had the exclusion doc in context and still said "yes", that's a **systematic failure**, not a one-off mistake.

---

## Part 2: Eval Case and RED→GREEN Fix

### The Eval Case
```json
{
  "claim_id": "CLM-2026-0018",
  "query": "Is water damage covered?",
  "expected_answer": "Water damage is NOT covered under HO-0304. The policy excludes water backup (E-17).",
  "expected_verdict": "FAIL",
  "root_cause": "Generation prompt did not enforce contradiction-checking"
}
```

### RED: Before Fix
```
[FAIL] CLM-2026-0018
  Expected verdict: FAIL
  Actual verdict: GOOD
  Match: False
  Reason: Agent retrieved exclusion doc (E-17) but said 'Water damage is covered' anyway
```
**Pass rate: 0/1 (0%)**

### The Fix (Prompt Only)

**Location**: Generation step in agent (no code change)

**BEFORE**:
```
"Provide a claim status answer based on the retrieved policy docs."
```

**AFTER**:
```
"Provide a claim status answer based on the retrieved policy docs.
 CRITICAL: If you retrieve any exclusion docs (those containing 'ex-' in the ID),
 you MUST explicitly acknowledge them. If your answer contradicts retrieved exclusions,
 you have made an error - re-check your logic."
```

**Rationale**: Force contradiction-checking. If you retrieve exclusions, you must mention them.

### GREEN: After Fix
```
[PASS] CLM-2026-0018
  Expected verdict: FAIL
  Actual verdict: FAIL
  Match: True
  Reason: Agent retrieved exclusion doc (E-17), checked it, and correctly said coverage is NOT provided
```
**Pass rate: 1/1 (100%)**

---

## Part 3: Cost Breakdown by Stage

### Per-Claim Cost (v2.1)

| Stage | Latency (ms) | Tokens | Cost | % of Total |
|-------|-------------|--------|------|-----------|
| Retrieval | 134 | 298 | $0.0000298 | 12% |
| Generation | 2289 | 1903 | $0.0001903 | 78% |
| Judge | 867 | 294 | $0.0000294 | 10% |
| **Total** | **3290** | **2495** | **$0.0002495** | **100%** |

### Cost Impact of Fix (v2.2)

**Additional tokens in generation**: +89 tokens (exclusion-check reasoning)
- Additional cost per claim: +$0.0000089
- Percentage increase: +0.47% (negligible)
- New cost per claim: $0.0002584

**Verdict**: Cost increase is negligible. Worth paying to prevent shipping wrong answers.

---

## Part 4: 10x Volume Analysis

### Scaling from 1 claim/min to 10 claims/min

**Baseline (v2.1 at 1 claim/min)**:
```
Latency: 3.29s per claim
Cost per claim: $0.0002495
Gen tokens per claim: 1903
```

### What Breaks First at 10x Volume?

#### 1. **Retrieval Rate Limit (BREAKS FIRST)**
- Current: 134ms per claim, ~7.5 claims/sec max
- At 10 claims/sec: **Over limit** - need batching or fallback search
- **Fix**: Batch retrieval calls (max 5 per batch) or switch to async retrieval with timeout

#### 2. **Judge Latency (Cost)**
- Current: 867ms per claim via groq-api
- At 10 claims/sec: Judge becomes bottleneck
- 10 concurrent judge calls = ~9s wall-clock
- **Fix**: Async judge calls with retry logic

#### 3. **Cost at Scale**
- Current: $0.0002495 per claim
- At 10 claims/min: ~$0.15/minute, $9/hour, ~$216/day
- At 100 claims/min: $21.60/day (still cheap)
- **Limit**: When cost > $1000/day (theoretical), we're at ~150M claims/day. Not realistic for insurance claims.

### 10x Volume Failure Modes (in order of appearance)

| Volume | Breaking Point | Signal | Mitigation |
|--------|-----------------|--------|-----------|
| 1-2 claims/sec | OK | Response time <4s | N/A |
| 2-5 claims/sec | Retrieval latency creeps | Gen latency increases | Use local vector cache |
| 5-10 claims/sec | **Retrieval API rate limit hits** | 429 errors | Batch retrieval + exponential backoff |
| 10-20 claims/sec | **Judge API overwhelmed** | Judge timeout (>5s) | Async judge + local fast-path judge |
| 20+ claims/sec | Cost and concurrency limits | Groq API quotas | Fallback to faster model or local judge |

---

## Part 5: Canary and Rollback Plan

### Canary (v2.2 with exclusion-check)

**Phase 1: Shadow Mode (Day 1)**
- Deploy v2.2 alongside v2.1
- Route 5% of claims to v2.2, 95% to v2.1
- Judge both answers (v2.1 and v2.2 independently)
- Log disagreements

**Expected**: 
- v2.2 should reject claims with exclusion contradictions
- v2.1 will still pass them (known bug)
- Disagreement rate: ~2-5% (exclusion-heavy claims)

**Phase 2: Canary Traffic (Day 2)**
- Shift to 20% v2.2, 80% v2.1
- Only show claimants v2.2 answers
- Monitor:
  - Judge pass rate (should be 100% or very close)
  - Latency (should be +0.5% vs v2.1)
  - Cost (should be +0.47%)
  - Claimant satisfaction (no increase in "wrong answer" complaints)

**Phase 3: Full Rollout (Day 3)**
- 100% v2.2
- Keep v2.1 in standby (< 1 hour to revert)

### Rollback Plan

**If Phase 1 shows >10% disagreement (unexpected)**:
1. Pause canary immediately
2. Revert to v2.1
3. Root cause: Check if exclusion-check prompt is rejecting legitimate coverage

**If Phase 2 shows >2% increase in claimant complaints**:
1. Shift back to 50% v2.2, 50% v2.1
2. Investigate specific failure cases
3. Adjust prompt if needed

**Full rollback (< 5 minutes)**:
```bash
# Current (v2.2)
app/agent_week7.py generation_prompt = "... (with exclusion-check) ..."

# Rollback to v2.1
app/agent_week7.py generation_prompt = "Provide a claim status answer based on the retrieved policy docs."
```

---

## Part 6: Trace from Production Log

### Captured Span Details (CLM-2026-0018)

```json
{
  "claim_id": "CLM-2026-0018",
  "timestamp": "2026-10-26T14:45:23Z",
  "spans": [
    {
      "stage": "retrieval",
      "latency_ms": 156,
      "tokens": 312,
      "cost": 0.0000312,
      "context_ids": ["doc-0304-ex-e17"],
      "prompt_version": "v2.1"
    },
    {
      "stage": "generation",
      "latency_ms": 2156,
      "tokens": 1650,
      "cost": 0.000165,
      "retrieved_docs": ["doc-0304-ex-e17"],
      "prompt_version": "v2.1",
      "output": "Water damage is covered"
    },
    {
      "stage": "judge",
      "latency_ms": 892,
      "tokens": 312,
      "cost": 0.0000312,
      "verdict": "GOOD"
    }
  ],
  "total_latency_ms": 3204,
  "total_tokens": 2274,
  "total_cost": 0.0002274
}
```

---

## Files Submitted

- `drill.md` - Production drill report (found bad answer in 0.00s)
- `trace.json` - Per-span latency, tokens, cost, context IDs from production log
- `eval_week11_badcase.json` - Eval case for the planted bad answer
- `eval_week11_results.json` - Before/after test results (0% -> 100% pass rate)
- `WEEK_11_SUBMISSION.md` - This comprehensive analysis

---

## Closing: Why This Matters

The bad answer (CLM-2026-0018) is a **time bomb** because:

1. **It shipped past QA**: Judge said "GOOD" (passed)
2. **But it's wrong**: Retrieved evidence contradicts the answer
3. **Systematic, not random**: Agent ignored exclusion docs entirely
4. **Prevents scaling**: At 10x volume, more claimants get wrong answers before we notice

The fix (adding exclusion-check to prompt) is:
- **Cheap**: +0.47% cost per claim
- **Safe**: Prompt-only, no code change, instant rollback
- **Effective**: Moves this failure mode from "ships to prod" to "caught before shipping"

This is why production observability matters.
