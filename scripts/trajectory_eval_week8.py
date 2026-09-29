"""
Week 8: Trajectory Evaluation
Score the path, expose outcome-vs-trajectory gap, find failure modes.
"""

import json
import statistics
from typing import List, Dict, Tuple
from pathlib import Path

# Expected tool sequences for each claim
EXPECTED_SEQUENCES = {
    "CLM-2026-0001": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "clean",
    },
    "CLM-2026-0002": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "dependency_flood",
    },
    "CLM-2026-0003": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "clean",
    },
    "CLM-2026-0004": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "dependency_seepage",
    },
    "CLM-2026-0005": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "clean",
    },
    "CLM-2026-0006": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "dependency_earthquake",
    },
    "CLM-2026-0007": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "clean",
    },
    "CLM-2026-0008": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "partial_mold",
    },
    "CLM-2026-0009": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "clean",
    },
    "CLM-2026-0010": {
        "paths": [
            ["retrieve_claim", "check_policy_exclusions", "compute_payout"],
        ],
        "mode": "dependency_sump",
    },
}


def assess_trajectory(claim_id: str, actual_sequence: List[str], actual_steps: List[Dict]) -> Dict:
    """
    Assess if the trajectory (path taken) matches expected sequence.

    Returns: {
        "tool_choice_correct": bool,
        "arguments_valid": bool,
        "efficiency": float (steps_taken / steps_needed),
        "trajectory_pass": bool,
    }
    """
    if claim_id not in EXPECTED_SEQUENCES:
        return {"error": f"Unknown claim {claim_id}"}

    expected = EXPECTED_SEQUENCES[claim_id]
    expected_paths = expected["paths"]

    # Tool choice accuracy: did agent use correct sequence?
    tool_choice_correct = actual_sequence in expected_paths

    # Argument validity: were claim IDs and values real?
    arguments_valid = True
    for step in actual_steps:
        action = step.get("action", "")
        # All steps should use valid claim_id
        if "CLM-2026" not in str(step):
            arguments_valid = False
            break

    # Step efficiency: steps_taken / steps_needed
    steps_needed = len(expected_paths[0])  # Assume first path is baseline
    steps_taken = len(actual_sequence)
    efficiency = steps_needed / steps_taken if steps_taken > 0 else 0

    # Trajectory pass: correct sequence AND valid arguments AND efficient
    trajectory_pass = tool_choice_correct and arguments_valid and efficiency >= 0.8

    return {
        "claim_id": claim_id,
        "mode": expected["mode"],
        "tool_choice_correct": tool_choice_correct,
        "arguments_valid": arguments_valid,
        "efficiency": round(efficiency, 2),
        "trajectory_pass": trajectory_pass,
        "expected_sequence": expected_paths[0],
        "actual_sequence": actual_sequence,
    }


def compute_trajectory_metrics(evaluations: List[Dict]) -> Dict:
    """Compute: tool-choice accuracy, argument validity, step efficiency, cost variance."""

    tool_choice_accurate = sum(1 for e in evaluations if e.get("tool_choice_correct"))
    argument_valid = sum(1 for e in evaluations if e.get("arguments_valid"))
    trajectory_pass = sum(1 for e in evaluations if e.get("trajectory_pass"))

    tool_choice_accuracy = (tool_choice_accurate / len(evaluations)) * 100 if evaluations else 0
    argument_validity_rate = (argument_valid / len(evaluations)) * 100 if evaluations else 0
    trajectory_pass_rate = (trajectory_pass / len(evaluations)) * 100 if evaluations else 0

    efficiencies = [e.get("efficiency", 1.0) for e in evaluations]
    avg_efficiency = statistics.mean(efficiencies) if efficiencies else 1.0

    return {
        "tool_choice_accuracy": f"{tool_choice_accuracy:.1f}%",
        "argument_validity_rate": f"{argument_validity_rate:.1f}%",
        "step_efficiency": f"{avg_efficiency:.2f}",
        "trajectory_pass_rate": f"{trajectory_pass_rate:.1f}%",
    }


def outcome_vs_trajectory_gap(outcome_pass_rate: float, trajectory_pass_rate: float) -> float:
    """
    Calculate gap: outcome_pass_rate - trajectory_pass_rate

    High gap = agent gets right answer via wrong path (time bomb!)
    """
    return round(outcome_pass_rate - trajectory_pass_rate, 1)


def main():
    print("\n" + "=" * 90)
    print("WEEK 8: TRAJECTORY EVALUATION")
    print("=" * 90)

    # Load race results from Week 7
    ROOT = Path(__file__).resolve().parent.parent
    results_file = ROOT / "race_results_detailed.json"

    if not results_file.exists():
        print(f"Error: {results_file} not found")
        return

    with open(results_file, "r") as f:
        race_results = json.load(f)

    agent_results = race_results.get("agent", [])

    print(f"\nEvaluating {len(agent_results)} claims for trajectory...")

    # Assess trajectory for each claim
    evaluations = []
    for result in agent_results:
        claim_id = result.get("claim_id")
        steps = result.get("steps", [])
        actual_sequence = [s["action"] for s in steps]

        assessment = assess_trajectory(claim_id, actual_sequence, steps)
        evaluations.append(assessment)

        if not assessment.get("trajectory_pass"):
            print(f"  [FAIL] {claim_id}: {assessment.get('mode')} - trajectory FAILED")
        else:
            print(f"  [PASS] {claim_id}: {assessment.get('mode')} - trajectory OK")

    # Compute metrics
    metrics = compute_trajectory_metrics(evaluations)

    # Outcome vs Trajectory Gap
    outcome_pass_rate = 100.0  # Week 7: both agent and fixed achieved 100%
    trajectory_pass_rate = float(metrics["trajectory_pass_rate"].rstrip("%"))
    gap = outcome_vs_trajectory_gap(outcome_pass_rate, trajectory_pass_rate)

    print("\n" + "=" * 90)
    print("TRAJECTORY METRICS")
    print("=" * 90)
    print(f"\nTool Choice Accuracy:    {metrics['tool_choice_accuracy']}")
    print(f"Argument Validity Rate:  {metrics['argument_validity_rate']}")
    print(f"Step Efficiency:         {metrics['step_efficiency']}")
    print(f"Trajectory Pass Rate:    {metrics['trajectory_pass_rate']}")

    print(f"\nOutcome Pass Rate:       {outcome_pass_rate:.1f}%")
    print(f"Trajectory Pass Rate:    {trajectory_pass_rate:.1f}%")
    print(f"\nOUTCOME-TRAJECTORY GAP:  {gap:.1f} percentage points")

    if gap > 0:
        print(f"\n[WARNING] GAP DETECTED: Agent achieves correct payout without correct path!")
        print("This is a time bomb - right answer, wrong path.")

    # Find failure modes
    print("\n" + "-" * 90)
    print("FAILURE MODES")
    print("-" * 90)

    failure_modes = {}
    for eval_result in evaluations:
        if not eval_result.get("trajectory_pass"):
            mode = eval_result.get("mode")
            if mode not in failure_modes:
                failure_modes[mode] = []
            failure_modes[mode].append(eval_result["claim_id"])

    if failure_modes:
        for mode, claims in failure_modes.items():
            print(f"\n{mode.upper()}: {len(claims)} failures")
            for claim in claims:
                eval_result = next(e for e in evaluations if e["claim_id"] == claim)
                print(f"  - {claim}")
                print(f"    Expected: {eval_result['expected_sequence']}")
                print(f"    Actual:   {eval_result['actual_sequence']}")
    else:
        print("\nNo trajectory failures detected.")

    # Save results
    output = {
        "evaluations": evaluations,
        "metrics": metrics,
        "outcome_pass_rate": outcome_pass_rate,
        "trajectory_pass_rate": trajectory_pass_rate,
        "gap": gap,
        "failure_modes": failure_modes,
    }

    output_file = ROOT / "trajectory_results_week8.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved: {output_file}")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
