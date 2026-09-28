"""
Week 7 Fixed Workflow: Same task, deterministic 4 steps, no loop.
"""

import time
from typing import Dict, Any
from app.tools_week7 import AGENT_TOOLS, ClaimStatus


def process_claim_workflow(claim_id: str) -> Dict[str, Any]:
    """
    Process claim with fixed 4-step workflow (no agent loop).

    Step 1: Retrieve claim
    Step 2: Check exclusions
    Step 3: Compute payout
    Step 4: Return verdict
    """
    start_time = time.time()
    tokens_used = 0  # No LLM planning in fixed workflow
    cost_used = 0.0
    steps = []

    # STEP 1: Retrieve claim
    try:
        claim = AGENT_TOOLS["retrieve_claim"](claim_id)
        loss_type = claim.get("loss_type", "unknown")
        claimed_amount = claim.get("claimed_amount", 0)
        excess = claim.get("excess", 1000)
        step1 = {"step": 1, "action": "retrieve_claim", "result": "success"}
        steps.append(step1)
    except Exception as e:
        return {"error": f"Step 1 failed: {e}", "steps": []}

    # STEP 2: Check exclusions
    try:
        exclusion_result = AGENT_TOOLS["check_policy_exclusions"](claim_id, loss_type)
        exclusion_status = exclusion_result.get("status", "unknown")

        # Determine adjudication status based on exclusion
        if exclusion_status == "covered":
            adjudicate_status = ClaimStatus.APPROVED
        elif exclusion_status == "excluded":
            adjudicate_status = ClaimStatus.DENIED
        elif exclusion_status == "partial":
            # Partial coverage cases need more logic
            adjudicate_status = ClaimStatus.PARTIAL
        else:
            adjudicate_status = ClaimStatus.PARTIAL

        step2 = {"step": 2, "action": "check_policy_exclusions", "result": exclusion_status}
        steps.append(step2)
    except Exception as e:
        return {"error": f"Step 2 failed: {e}", "steps": steps}

    # STEP 3: Compute payout
    try:
        payout_result = AGENT_TOOLS["compute_payout"](
            claim_id, claimed_amount, adjudicate_status, excess
        )
        payable_amount = payout_result.get("payable_amount", 0)
        step3 = {"step": 3, "action": "compute_payout", "result": f"${payable_amount:.2f}"}
        steps.append(step3)
    except Exception as e:
        return {"error": f"Step 3 failed: {e}", "steps": steps}

    # STEP 4: Verdict
    verdict = {
        "claim_id": claim_id,
        "status": adjudicate_status.value,
        "payable": payable_amount,
        "reasoning": payout_result.get("reason", ""),
    }
    step4 = {"step": 4, "action": "synthesize_verdict", "result": "complete"}
    steps.append(step4)

    elapsed = time.time() - start_time

    return {
        "claim_id": claim_id,
        "step_count": 4,  # Always exactly 4
        "tokens_used": tokens_used,
        "cost_used": cost_used,
        "execution_time": round(elapsed, 2),
        "budget_hit": None,  # Fixed workflow never hits budgets
        "completed": True,
        "verdict": verdict,
        "steps": steps,
    }
