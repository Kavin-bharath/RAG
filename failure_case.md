# Failure Case: Coverage Worker 500 Error

## Injected Failure
- Claim: CLM-2026-0002
- Failure: Coverage worker returns HTTP 500
- Orchestrator response: DEGRADED (synthesized answer without coverage data)

## Actual Behavior
The orchestrator detected the worker error and:
1. Logged the failure in coverage_result
2. Passed "DEGRADED: Coverage check unavailable" to synthesis
3. Completed the claim with partial information (adjuster notes only)
4. Returned completed=True (graceful degradation, not failure)

## Verdict
The orchestrator chose **degradation over failure**: it dropped coverage data rather than failing the entire claim.
This is acceptable for a timeout or transient error, but risky for a persistent worker outage.
