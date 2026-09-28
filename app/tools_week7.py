"""
Week 7 Tools: Three tools for claims triage.
Each tool has one clear job, no overlapping descriptions.
"""

from enum import Enum
from typing import Dict, Any


class ClaimStatus(str, Enum):
    """Claim adjudication status."""
    APPROVED = "approved"
    DENIED = "denied"
    PARTIAL = "partial"


def retrieve_claim(claim_id: str) -> Dict[str, Any]:
    """
    Fetch claim record and adjuster notes from database.

    Use FIRST to get claim details, dates, amounts, and investigation notes.
    Input: claim_id (e.g., 'CLM-2026-0001')
    Output: Claim object with date, amount, notes, policy type, excess.
    """
    # Mock database lookup
    claims_db = {
        "CLM-2026-0001": {
            "claim_id": "CLM-2026-0001",
            "date_of_loss": "2026-08-20",
            "claimed_amount": 50000,
            "adjuster_notes": "Water damage from burst pipe. Sudden accidental discharge. No neglect.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "water damage",
        },
        "CLM-2026-0002": {
            "claim_id": "CLM-2026-0002",
            "date_of_loss": "2026-08-21",
            "claimed_amount": 75000,
            "adjuster_notes": "Basement flooding. Heavy rainfall 3 days. Water entered through foundation. Loss: surface water/flood.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "water damage",
        },
        "CLM-2026-0003": {
            "claim_id": "CLM-2026-0003",
            "date_of_loss": "2026-08-22",
            "claimed_amount": 25000,
            "adjuster_notes": "Kitchen fire from stove. Burner left on. Accidental cause. House fully insured for fire.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "fire damage",
        },
        "CLM-2026-0004": {
            "claim_id": "CLM-2026-0004",
            "date_of_loss": "2026-08-23",
            "claimed_amount": 100000,
            "adjuster_notes": "Basement water seepage. Gradual leak from foundation. This is continuous damage, not sudden. Excluded.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "water damage",
        },
        "CLM-2026-0005": {
            "claim_id": "CLM-2026-0005",
            "date_of_loss": "2026-08-24",
            "claimed_amount": 35000,
            "adjuster_notes": "Jewelry stolen. Insured has receipt. No break-in. Thief had key. Value documented.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "theft",
        },
        "CLM-2026-0006": {
            "claim_id": "CLM-2026-0006",
            "date_of_loss": "2026-08-25",
            "claimed_amount": 60000,
            "adjuster_notes": "Structural damage from earthquake. Seismic zone. Policy has earthquake exclusion.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "earthquake damage",
        },
        "CLM-2026-0007": {
            "claim_id": "CLM-2026-0007",
            "date_of_loss": "2026-08-26",
            "claimed_amount": 15000,
            "adjuster_notes": "Hail damage to roof. 1.5 inch hail. Damage to shingles and siding. Covered peril.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "windstorm damage",
        },
        "CLM-2026-0008": {
            "claim_id": "CLM-2026-0008",
            "date_of_loss": "2026-08-27",
            "claimed_amount": 40000,
            "adjuster_notes": "Mold in attic. Root cause: roof leak from hail storm. Mold from covered peril. Has carve-out.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "mold damage",
        },
        "CLM-2026-0009": {
            "claim_id": "CLM-2026-0009",
            "date_of_loss": "2026-08-28",
            "claimed_amount": 20000,
            "adjuster_notes": "Dishwasher malfunction. Sudden accidental discharge. Damage limited to kitchen. Well documented.",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "water damage",
        },
        "CLM-2026-0010": {
            "claim_id": "CLM-2026-0010",
            "date_of_loss": "2026-08-29",
            "claimed_amount": 55000,
            "adjuster_notes": "Sump pump failed. Basement flooding from rainfall exceeding pump capacity. Loss is flood (excluded).",
            "policy_type": "HO-0304",
            "excess": 1000,
            "loss_type": "water damage",
        },
    }

    if claim_id in claims_db:
        return claims_db[claim_id]
    else:
        return {"error": f"Claim {claim_id} not found"}


def check_policy_exclusions(claim_id: str, loss_type: str) -> Dict[str, Any]:
    """
    Determine if loss type is excluded under the policy.

    Use SECOND to assess coverage based on loss type from adjuster notes.
    Input: claim_id and loss_type (from notes)
    Output: Exclusion status (covered, partial, or excluded) with policy citation.
    """
    exclusions = {
        "water damage": {"status": "partial", "reason": "Covered if sudden/accidental. Excluded if flood/gradual/seepage."},
        "fire damage": {"status": "covered", "reason": "Named peril covered under HO-0304."},
        "theft": {"status": "covered", "reason": "Covered under HO-0304."},
        "earthquake damage": {"status": "excluded", "reason": "Earthquake excluded under E-2. Requires separate policy."},
        "windstorm damage": {"status": "covered", "reason": "Hail/windstorm covered as named peril."},
        "mold damage": {"status": "partial", "reason": "Excluded. Exception: mold from covered perils (fire, plumbing leak)."},
        "flood": {"status": "excluded", "reason": "Flood excluded. Requires separate flood insurance."},
    }

    loss_lookup = loss_type.lower()
    if loss_lookup in exclusions:
        result = exclusions[loss_lookup]
        return {
            "claim_id": claim_id,
            "loss_type": loss_type,
            "status": result["status"],
            "reason": result["reason"],
        }
    else:
        return {"claim_id": claim_id, "loss_type": loss_type, "error": "Loss type not found in policy"}


def compute_payout(claim_id: str, claimed_amount: float, status: ClaimStatus, excess: float) -> Dict[str, Any]:
    """
    Calculate final payable amount after applying excess and adjudication status.

    Use THIRD to compute payout based on status (enum) and excess.
    Input: claimed_amount (float), status (APPROVED/DENIED/PARTIAL), excess (float)
    Output: Payable amount and explanation.
    """
    if not isinstance(status, ClaimStatus):
        try:
            status = ClaimStatus(status)
        except (ValueError, KeyError):
            return {"error": f"Invalid status: {status}"}

    if status == ClaimStatus.DENIED:
        payable = 0.0
        reason = "Claim denied: loss type excluded or not covered."
    elif status == ClaimStatus.APPROVED:
        payable = max(0, claimed_amount - excess)
        reason = f"Approved: ${payable:.2f} = ${claimed_amount:.2f} - ${excess:.2f} excess"
    elif status == ClaimStatus.PARTIAL:
        payable = max(0, (claimed_amount * 0.5) - excess)
        reason = f"Partial (50%): ${payable:.2f} = (${claimed_amount:.2f} × 50%) - ${excess:.2f} excess"
    else:
        payable = 0.0
        reason = "Unknown status"

    return {
        "claim_id": claim_id,
        "claimed_amount": claimed_amount,
        "excess": excess,
        "status": status.value,
        "payable_amount": round(payable, 2),
        "reason": reason,
    }


AGENT_TOOLS = {
    "retrieve_claim": retrieve_claim,
    "check_policy_exclusions": check_policy_exclusions,
    "compute_payout": compute_payout,
}
