# Week 7: Agent vs Fixed Workflow Race

## Assignment
Build an insurance claims agent, then race it against a fixed 4-step workflow.
- Measure: pass rate, p50 latency, tokens, cost/claim
- Output: `race.csv` with 8 numbers (4 per system)
- Enforce: all 4 budgets (iterations, tokens, cost, wall-clock)
- Verdict: which one to ship, based on the numbers

## Files to Create

1. **app/tools.py** — 3 tools (retrieve_claim, check_policy_exclusions, compute_payout)
2. **app/agent_week7.py** — Agent loop with all 4 budgets
3. **scripts/workflow_week7.py** — Fixed 4-step workflow (same task, no loop)
4. **scripts/race_week7.py** — Main race script
5. **test_claims_10.json** — Test set (10 claims with 3+ dependency cases)
6. **race.csv** — Results: pass rate, p50 latency, tokens, cost/claim
7. **budget_log.txt** — One run showing budget termination
8. **WEEK_7_VERDICT.md** — Verdict paragraph (< 150 words)

## Expected Structure

```
Agent Race:
  - 10 claims
  - Measure: pass rate, p50 latency, tokens, cost/claim
  - Enforce budgets: max_steps, max_tokens, max_cost, wall_clock

Fixed Workflow:
  - Same 10 claims
  - Same 3 tools
  - Deterministic: always 4 steps
  - Measure: same 4 metrics

Output:
  race.csv with columns:
  System | Pass Rate | P50 Latency | Tokens | Cost/Claim
  Agent  | X%        | Xs          | N      | $X.XX
  Fixed  | X%        | Xs          | N      | $X.XX
```

## Build Order
1. ✓ Create tools.py (3 tools with clear descriptions)
2. ✓ Create agent_week7.py (with 4 budgets)
3. ✓ Create workflow_week7.py (deterministic 4 steps)
4. ✓ Create test_claims_10.json (dependency cases)
5. ✓ Create race_week7.py (runs both on all 10 claims)
6. ✓ Generate race.csv
7. ✓ Log one budget termination
8. ✓ Write verdict

## Key Requirements

- [ ] Third tool must have: enum parameters + one clear job + no description overlap
- [ ] Test cases: 10 claims with 3+ dependency cases (step 3 depends on step 2)
- [ ] Metrics: pass rate (correct payout %), p50 latency (not mean), tokens, cost
- [ ] Budgets: all 4 enforced in code + log showing termination
- [ ] Output: race.csv with 8 numbers
- [ ] Verdict: < 150 words, applies decision rule, consistent with numbers
