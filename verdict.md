# Week 10 Verdict: Kill the Orchestrator

## Numbers (cited)

1. **P50 Latency**: Single Agent **2.20s** vs Orchestrator **11.44s** (5.2x slower)
2. **Cost/Claim**: Single Agent **$0.000113** vs Orchestrator **$0.000112** (negligible difference)

## Analysis

The orchestrator loses decisively on the metric that matters: speed.

- Same pass rate (100% both)
- Same cost (effectively identical)
- Orchestrator is 5.2x slower on p50 latency
- Orchestrator is 5.1x slower on p99 latency (6.27s → 11.79s)

The cost parity is deceiving. The orchestrator has not delivered any value:
- No improvement in pass rate
- No reduction in cost
- Massive regression in latency
- Graceful degradation (claims answered despite worker failure) is nice but not worth the 5x slowdown for zero upside

## Sunk-Cost Bias (named explicitly)

We built a complex multi-agent orchestrator with decompose, coverage worker, notes worker, and synthesis steps. The temptation is to keep it because "we invested the effort." **This is sunk-cost bias.** The fact that it took work to build does not make it good. The metrics show it is worse than the single agent on every dimension except worker-failure recovery, which 100% of claims never exercise.

## Decision

**KILL the orchestrator.**

The single agent is faster, costs the same, and solves the same problem. Maintenance burden of the orchestrator (4 prompts, 4 LLM calls per claim, decomposition logic, hand-off retry logic) is not worth a 0.001% cost saving with a 5x latency tax.

Invest the orchestrator effort elsewhere: caching, batching, or better prompts for the single agent.
