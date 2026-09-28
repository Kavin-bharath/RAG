"""
Deterministic assertions for claim summaries.
These don't need an LLM — regex/logic handles them.
"""

import re
from typing import Dict, List


def assert_claim_number(summary: str) -> bool:
    """Check if summary contains CLM-YYYY-NNNNN format claim number."""
    return bool(re.search(r'CLM-\d{4}-\d{4}', summary))


def assert_date_present_and_parseable(summary: str) -> bool:
    """Check if summary contains a parseable date (YYYY-MM-DD format)."""
    return bool(re.search(r'\d{4}-\d{2}-\d{2}', summary))


def assert_amount_numeric(summary: str) -> bool:
    """Check if summary contains numeric amount (deductible, limit, excess, sublimit, etc)."""
    # Look for dollar amounts, percentages, or plain numbers
    return bool(re.search(r'(\$[\d,]+|[\d,]+|[\d]+%)', summary))


def assert_exclusion_when_denial(summary: str) -> bool:
    """
    If summary states a denial (uses words like 'denied', 'excluded', 'not covered'),
    it must cite an exclusion code (E-1 through E-20, F-1 through F-15).
    If no denial stated, assertion passes (not applicable).
    """
    has_denial = bool(
        re.search(
            r'\b(denied|excluded|not covered|deny|exclude|cannot cover|does not cover)\b',
            summary,
            re.IGNORECASE
        )
    )

    if not has_denial:
        return True  # Assertion not applicable

    # If denial stated, check for exclusion cite
    has_exclusion_cite = bool(re.search(r'\b([EF]-\d{1,2})\b', summary))
    return has_exclusion_cite


def run_all_assertions(summary: str) -> Dict[str, bool]:
    """Run all assertions and return results."""
    return {
        "claim_number": assert_claim_number(summary),
        "date_parseable": assert_date_present_and_parseable(summary),
        "amount_numeric": assert_amount_numeric(summary),
        "exclusion_when_denial": assert_exclusion_when_denial(summary),
    }


def assertion_verdict(summary: str) -> str:
    """
    Return 'PASS' if all assertions pass, 'FAIL' otherwise.
    """
    results = run_all_assertions(summary)
    if all(results.values()):
        return "PASS"
    else:
        failed = [k for k, v in results.items() if not v]
        return f"FAIL ({', '.join(failed)})"
