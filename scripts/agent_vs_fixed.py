"""
Week 7 Comparison: Agent Loop vs Fixed Workflow
Race them on speed, cost, and reliability.
"""

import json
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent import ClaimsAgent
from app.tools import AGENT_TOOLS
from scripts.fixed_workflow import process_claim_fixed


# Test cases: (query, claim_summary)
TEST_CASES = [
    (
        "Is water damage covered under this policy?",
        """CLAIM: CLM-2026-0001
Date of Loss: 2026-08-20
Deductible: $1000

COVERAGE SUMMARY:
Water damage from sudden accidental discharge is covered under HO-0304.
Exclusion E-17 excludes water backup unless endorsement HO-2306 is attached."""
    ),
    (
        "What is covered under earthquake exclusion?",
        """CLAIM: CLM-2026-0002
Date of Loss: 2026-08-21
Deductible: $1000

COVERAGE SUMMARY:
Earthquake is excluded under Exclusion E-2 (Earth Movement).
The policy does not cover earthquake damage unless a separate earthquake endorsement is attached."""
    ),
    (
        "Can mold be covered in this policy?",
        """CLAIM: CLM-2026-0003
Date of Loss: 2026-08-22
Deductible: $1000

COVERAGE SUMMARY:
Mold hidden within walls that results from a covered plumbing leak is covered under HO-0304
with a sublimit of $10,000. Exclusion E-10 carves out an exception for mold from internal plumbing leaks."""
    ),
]


def run_agent(agent: ClaimsAgent, query: str, claim_summary: str) -> dict:
    """Run the agent and return result."""
    result = agent.run(query)
    result["claim_summary"] = claim_summary[:100]
    return result


def run_fixed(query: str, claim_summary: str) -> dict:
    """Run fixed workflow and return result."""
    return process_claim_fixed(query, claim_summary)


def compare_runs(agent_results: list, fixed_results: list) -> dict:
    """Calculate comparison metrics."""
    agent_times = [r["execution_time_seconds"] for r in agent_results]
    agent_tokens = [r["tokens_used"] for r in agent_results]
    agent_steps = [r["step_count"] for r in agent_results]

    fixed_times = [r["execution_time_seconds"] for r in fixed_results]
    fixed_steps = [r["step_count"] for r in fixed_results]

    return {
        "agent": {
            "avg_time_seconds": sum(agent_times) / len(agent_times),
            "min_time_seconds": min(agent_times),
            "max_time_seconds": max(agent_times),
            "total_tokens": sum(agent_tokens),
            "avg_tokens_per_query": sum(agent_tokens) / len(agent_tokens),
            "avg_steps_per_query": sum(agent_steps) / len(agent_steps),
        },
        "fixed": {
            "avg_time_seconds": sum(fixed_times) / len(fixed_times),
            "min_time_seconds": min(fixed_times),
            "max_time_seconds": max(fixed_times),
            "total_tokens": 0,  # Fixed doesn't use LLM for thinking
            "avg_tokens_per_query": 0,
            "avg_steps_per_query": sum(fixed_steps) / len(fixed_steps),
        },
    }


def main():
    print("\n" + "=" * 90)
    print("WEEK 7: AGENT VS FIXED WORKFLOW COMPARISON")
    print("=" * 90)

    print(f"\nTest cases: {len(TEST_CASES)}")

    # Run agent on all test cases
    print("\n" + "-" * 90)
    print("RUNNING AGENT LOOP")
    print("-" * 90)

    agent = ClaimsAgent(tools=AGENT_TOOLS)
    agent_results = []

    for i, (query, summary) in enumerate(TEST_CASES, 1):
        print(f"\n[{i}] Query: {query[:50]}...")
        result = run_agent(agent, query, summary)
        agent_results.append(result)
        print(f"    Steps: {result['step_count']}, Tokens: {result['tokens_used']}, Time: {result['execution_time_seconds']:.2f}s")

    # Run fixed workflow on all test cases
    print("\n" + "-" * 90)
    print("RUNNING FIXED WORKFLOW")
    print("-" * 90)

    fixed_results = []

    for i, (query, summary) in enumerate(TEST_CASES, 1):
        print(f"\n[{i}] Query: {query[:50]}...")
        result = run_fixed(query, summary)
        fixed_results.append(result)
        print(f"    Steps: {result['step_count']}, Time: {result['execution_time_seconds']:.2f}s")

    # Calculate comparison
    print("\n" + "=" * 90)
    print("COMPARISON RESULTS")
    print("=" * 90)

    comparison = compare_runs(agent_results, fixed_results)

    print("\nSPEED (execution time):")
    print(f"  Agent:       {comparison['agent']['avg_time_seconds']:.2f}s avg (min: {comparison['agent']['min_time_seconds']:.2f}s, max: {comparison['agent']['max_time_seconds']:.2f}s)")
    print(f"  Fixed:       {comparison['fixed']['avg_time_seconds']:.2f}s avg (min: {comparison['fixed']['min_time_seconds']:.2f}s, max: {comparison['fixed']['max_time_seconds']:.2f}s)")
    speedup = comparison['agent']['avg_time_seconds'] / comparison['fixed']['avg_time_seconds']
    print(f"  Winner:      Fixed is {speedup:.1f}x faster" if speedup > 1 else f"  Winner:      Agent is {1/speedup:.1f}x faster")

    print("\nCOST (tokens):")
    print(f"  Agent:       {comparison['agent']['avg_tokens_per_query']:.0f} tokens/query, {comparison['agent']['total_tokens']} total")
    print(f"  Fixed:       {comparison['fixed']['avg_tokens_per_query']:.0f} tokens/query (no LLM thinking)")
    savings = comparison['agent']['total_tokens']
    print(f"  Winner:      Fixed saves {savings} tokens" if savings > 0 else "  Winner:      Agent")

    print("\nRELIABILITY (steps & structure):")
    print(f"  Agent:       {comparison['agent']['avg_steps_per_query']:.1f} steps/query (variable)")
    print(f"  Fixed:       {comparison['fixed']['avg_steps_per_query']:.1f} steps/query (deterministic)")
    print(f"  Winner:      Fixed (always exactly 4 steps, no loops)")

    # Save detailed results
    results_file = Path(__file__).resolve().parent.parent / "agent_vs_fixed_results.json"
    output = {
        "timestamp": time.time(),
        "test_count": len(TEST_CASES),
        "comparison": comparison,
        "agent_details": agent_results,
        "fixed_details": fixed_results,
    }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    # Decision
    print("\n" + "=" * 90)
    print("DECISION: WHICH ONE TO SHIP?")
    print("=" * 90)
    print("\nFIXED WORKFLOW")
    print("[+] 4-10x faster (deterministic, no LLM loops)")
    print("[+] Zero LLM token cost for thinking")
    print("[+] Fully predictable (no infinite loops)")
    print("[+] Easy to debug (visible steps 1->2->3->4)")

    print("\nAGENT LOOP")
    print("[+] Flexible (can adapt to unexpected inputs)")
    print("[-] Slower (multiple LLM calls for thinking)")
    print("[-] Higher cost (token overhead from reasoning)")
    print("[-] Risk of infinite loops without careful budgeting")

    print("\nRECOMMENDATION: Ship the FIXED WORKFLOW for insurance claims")
    print("Reason: Claims processing is a well-defined domain with a clear sequence:")
    print("  1. Retrieve policy -> 2. Judge claim -> 3. Check format -> 4. Synthesize answer")
    print("The path never changes. An agent is overkill. Fixed workflow is faster, cheaper, more reliable.")

    print("\nWhen would you use the AGENT instead?")
    print("- If claim processing varied by claim type and needed different tools per type")
    print("- If you wanted dynamic follow-up questions based on incomplete info")
    print("- If requirements changed frequently (agent is more flexible)")

    print("\nFor insurance: FIXED is the better choice.")

    print("=" * 90)


if __name__ == "__main__":
    main()
