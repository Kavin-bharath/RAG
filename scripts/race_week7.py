"""
Week 7 Race: Agent vs Fixed Workflow
Runs both on 10 claims, produces race.csv with metrics + budget log.
"""

import json
import time
import statistics
from pathlib import Path
from typing import List, Dict
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent_week7 import ClaimsAgent
from app.tools_week7 import AGENT_TOOLS
from scripts.workflow_week7 import process_claim_workflow


# 10 test claims
TEST_CLAIMS = [
    "CLM-2026-0001",  # Clean: water damage, sudden, approved
    "CLM-2026-0002",  # Dependency: notes reveal flood → excluded
    "CLM-2026-0003",  # Clean: fire damage, approved
    "CLM-2026-0004",  # Dependency: notes reveal gradual seepage → denied
    "CLM-2026-0005",  # Clean: theft, approved
    "CLM-2026-0006",  # Dependency: notes reveal earthquake → excluded
    "CLM-2026-0007",  # Clean: hail/windstorm, approved
    "CLM-2026-0008",  # Partial: mold from covered peril
    "CLM-2026-0009",  # Clean: dishwasher water damage, approved
    "CLM-2026-0010",  # Dependency: notes clarify flood → denied
]


def run_agent_race(agent: ClaimsAgent, claims: List[str]) -> tuple:
    """Run agent on all claims, return results and budget log."""
    results = []
    budget_log = None

    for claim_id in claims:
        result = agent.run(claim_id)
        results.append(result)

        # Capture first budget hit
        if result["budget_hit"] and not budget_log:
            budget_log = {
                "claim_id": claim_id,
                "step": result["step_count"],
                "tokens": result["tokens_used"],
                "cost": result["cost_used"],
                "time": result["execution_time"],
                "budget_hit": result["budget_hit"],
            }

    return results, budget_log


def run_workflow_race(claims: List[str]) -> List[Dict]:
    """Run fixed workflow on all claims."""
    results = []
    for claim_id in claims:
        result = process_claim_workflow(claim_id)
        results.append(result)
    return results


def compute_metrics(results: List[Dict], system_name: str) -> Dict:
    """Compute: pass rate, p50 latency, tokens, cost/claim."""
    times = [r["execution_time"] for r in results if r.get("execution_time")]
    tokens_list = [r["tokens_used"] for r in results]
    costs = [r["cost_used"] for r in results]

    pass_count = sum(1 for r in results if r.get("completed"))
    pass_rate = (pass_count / len(results)) * 100

    p50_latency = statistics.median(times) if times else 0
    total_tokens = sum(tokens_list)
    avg_cost = sum(costs) / len(costs) if costs else 0

    return {
        "system": system_name,
        "pass_rate": f"{pass_rate:.1f}%",
        "p50_latency_s": f"{p50_latency:.2f}",
        "total_tokens": total_tokens,
        "cost_per_claim": f"${avg_cost:.4f}",
    }


def main():
    print("\n" + "=" * 90)
    print("WEEK 7: AGENT VS FIXED WORKFLOW RACE")
    print("=" * 90)
    print(f"\nTest set: {len(TEST_CLAIMS)} claims")
    print(f"Metrics: pass rate, p50 latency, tokens, cost/claim")

    # Run agent
    print("\n[AGENT]")
    agent = ClaimsAgent(tools=AGENT_TOOLS)
    agent_results, agent_budget_log = run_agent_race(agent, TEST_CLAIMS)
    print(f"  Completed: {len(agent_results)} runs")
    if agent_budget_log:
        print(f"  Budget hit on {agent_budget_log['claim_id']}: {agent_budget_log['budget_hit']}")

    # Run fixed workflow
    print("\n[FIXED WORKFLOW]")
    workflow_results = run_workflow_race(TEST_CLAIMS)
    print(f"  Completed: {len(workflow_results)} runs")

    # Compute metrics
    agent_metrics = compute_metrics(agent_results, "Agent")
    workflow_metrics = compute_metrics(workflow_results, "Fixed Workflow")

    # Print race.csv format
    print("\n" + "=" * 90)
    print("RACE RESULTS (race.csv)")
    print("=" * 90)
    print("\nSystem,Pass Rate,P50 Latency (s),Total Tokens,Cost/Claim")
    print(f"Agent,{agent_metrics['pass_rate']},{agent_metrics['p50_latency_s']},{agent_metrics['total_tokens']},{agent_metrics['cost_per_claim']}")
    print(f"Fixed Workflow,{workflow_metrics['pass_rate']},{workflow_metrics['p50_latency_s']},{workflow_metrics['total_tokens']},{workflow_metrics['cost_per_claim']}")

    # Save race.csv
    ROOT = Path(__file__).resolve().parent.parent
    race_file = ROOT / "race.csv"
    with open(race_file, "w") as f:
        f.write("System,Pass Rate,P50 Latency (s),Total Tokens,Cost/Claim\n")
        f.write(f"Agent,{agent_metrics['pass_rate']},{agent_metrics['p50_latency_s']},{agent_metrics['total_tokens']},{agent_metrics['cost_per_claim']}\n")
        f.write(f"Fixed Workflow,{workflow_metrics['pass_rate']},{workflow_metrics['p50_latency_s']},{workflow_metrics['total_tokens']},{workflow_metrics['cost_per_claim']}\n")
    print(f"\nSaved: {race_file}")

    # Save budget log
    if agent_budget_log:
        budget_file = ROOT / "budget_log.txt"
        with open(budget_file, "w") as f:
            f.write("BUDGET TERMINATION LOG\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Claim: {agent_budget_log['claim_id']}\n")
            f.write(f"Step: {agent_budget_log['step']}\n")
            f.write(f"Tokens used: {agent_budget_log['tokens']}\n")
            f.write(f"Cost used: ${agent_budget_log['cost']:.6f}\n")
            f.write(f"Time elapsed: {agent_budget_log['time']:.2f}s\n")
            f.write(f"\nBudget triggered: {agent_budget_log['budget_hit']}\n")
            f.write("\nAgent terminated cleanly due to budget constraint.\n")
        print(f"Saved: {budget_file}")

    # Save detailed results
    results_file = ROOT / "race_results_detailed.json"
    with open(results_file, "w") as f:
        json.dump({
            "agent": agent_results,
            "workflow": workflow_results,
            "metrics": {"agent": agent_metrics, "workflow": workflow_metrics},
            "budget_log": agent_budget_log,
        }, f, indent=2)

    print(f"Saved: {results_file}")

    print("\n" + "=" * 90)
    print("RACE COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()
