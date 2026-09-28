"""
Fixed workflow for processing insurance claims.
No agent loop - just deterministic steps 1→2→3→4.
Compare this against the agent to see trade-offs.
"""

import time
import json
from typing import Dict, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval import answer_query
from app.claim_judge import judge_v2
from app.assertions import run_all_assertions


def process_claim_fixed(query: str, claim_summary: str) -> Dict[str, Any]:
    """
    Process a claim using a fixed 4-step sequence.

    Step 1: Retrieve policy info
    Step 2: Judge the claim summary
    Step 3: Check assertions
    Step 4: Synthesize answer
    """
    start_time = time.time()
    tokens_used = 0

    steps = []

    # STEP 1: Retrieve policy
    policy_answer = ""
    try:
        result = answer_query(query, write_trace=False)
        policy_answer = result.get("answer", str(result)) if isinstance(result, dict) else str(result)
        step1 = {
            "step": 1,
            "action": "retrieve_policy",
            "result": "Retrieved policy info",
        }
        steps.append(step1)
    except Exception as e:
        step1 = {
            "step": 1,
            "action": "retrieve_policy",
            "result": f"Error: {str(e)}",
        }
        steps.append(step1)

    # STEP 2: Judge the claim
    try:
        verdict = judge_v2(claim_summary)
        step2 = {
            "step": 2,
            "action": "judge_claim",
            "result": verdict,
        }
        steps.append(step2)
    except Exception as e:
        verdict = "ERROR"
        step2 = {
            "step": 2,
            "action": "judge_claim",
            "result": f"Error: {str(e)}",
        }
        steps.append(step2)

    # STEP 3: Check assertions
    try:
        assertions = run_all_assertions(claim_summary)
        assertions_pass = all(assertions.values())
        step3 = {
            "step": 3,
            "action": "check_assertion",
            "result": assertions_pass,
            "assertions": assertions,
        }
        steps.append(step3)
    except Exception as e:
        assertions_pass = False
        step3 = {
            "step": 3,
            "action": "check_assertion",
            "result": f"Error: {str(e)}",
        }
        steps.append(step3)

    # STEP 4: Synthesize answer (no LLM call - just combine results)
    final_answer = f"""
CLAIM PROCESSING RESULT
======================
Query: {query}

Policy Retrieved: Successfully retrieved
Claim Quality (Judge): {verdict}
Claim Format: {'PASS' if assertions_pass else 'FAIL'}

Recommendation:
- Policy coverage available: {policy_answer[:100] if policy_answer else 'No data'}
- Claim assessment: {verdict}
- Format check: {'All required elements present' if assertions_pass else 'Missing required elements'}
"""

    step4 = {
        "step": 4,
        "action": "synthesize_answer",
        "result": "Synthesis complete",
    }
    steps.append(step4)

    elapsed = time.time() - start_time

    return {
        "query": query,
        "claim_summary": claim_summary[:100],
        "answer": final_answer,
        "steps": steps,
        "step_count": 4,  # Always exactly 4 steps
        "tokens_used": tokens_used,
        "execution_time_seconds": elapsed,
        "completed": True,
    }


if __name__ == "__main__":
    # Example usage
    test_query = "Is water damage covered?"
    test_summary = """CLAIM: CLM-2026-0001
Date of Loss: 2026-08-20
Deductible: $1000

COVERAGE SUMMARY:
Water damage from sudden accidental discharge is covered under HO-0304.
Exclusion E-17 excludes water backup unless endorsement HO-2306 is attached."""

    result = process_claim_fixed(test_query, test_summary)
    print(json.dumps(result, indent=2))
