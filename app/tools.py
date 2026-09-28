"""
Tools available to the insurance claims agent.
Each tool has a clear description so the agent picks the right one.
"""

import json
from typing import Dict, Any
from app.retrieval import answer_query
from app.claim_judge import judge_v2
from app.assertions import run_all_assertions


def retrieve_policy(query: str) -> Dict[str, Any]:
    """
    Retrieve relevant policy documents and coverage information.

    Use this when you need to find what a policy covers, exclusions, or specific terms.
    Input: A natural language query about coverage (e.g., "water damage coverage")
    Output: Retrieved policy chunks with relevance scores and coverage info.
    """
    try:
        result = answer_query(query, write_trace=False)
        # answer_query returns a dict with 'answer' key
        answer = result.get("answer", str(result)) if isinstance(result, dict) else str(result)
        return {
            "summary": answer,
            "tool": "retrieve_policy",
        }
    except Exception as e:
        return {"error": str(e), "tool": "retrieve_policy"}


def judge_claim(summary: str) -> Dict[str, Any]:
    """
    Evaluate if a claim summary is GOOD (accurate, well-cited) or BAD (hallucinated, missing info).

    Use this when you need to assess the quality of a claim summary or decision.
    Input: A claim summary text to evaluate
    Output: Verdict (GOOD/BAD) with reasoning about policy accuracy and citations.
    """
    try:
        verdict = judge_v2(summary)
        return {
            "verdict": verdict,
            "summary_excerpt": summary[:100],
            "tool": "judge_claim",
        }
    except Exception as e:
        return {"error": str(e), "tool": "judge_claim"}


def check_assertion(summary: str) -> Dict[str, Any]:
    """
    Check if a claim summary has required elements (claim number, date, amount, exclusion cite).

    Use this to verify claim summaries are complete and properly formatted.
    Input: A claim summary text
    Output: List of assertions (pass/fail) for structure and required fields.
    """
    try:
        assertions = run_all_assertions(summary)
        return {
            "assertions": assertions,
            "all_pass": all(assertions.values()),
            "tool": "check_assertion",
        }
    except Exception as e:
        return {"error": str(e), "tool": "check_assertion"}


AGENT_TOOLS = {
    "retrieve_policy": retrieve_policy,
    "judge_claim": judge_claim,
    "check_assertion": check_assertion,
}


def get_tool_descriptions() -> str:
    """Return descriptions of all tools for the agent's context."""
    return """
Available Tools:

1. retrieve_policy(query: str) → Dict
   - Retrieves relevant policy information
   - Use: "What does this policy cover?"
   - Returns: {retrieved_chunks, summary}

2. judge_claim(summary: str) → Dict
   - Evaluates claim summary quality
   - Use: "Is this claim summary good?"
   - Returns: {verdict: GOOD|BAD}

3. check_assertion(summary: str) → Dict
   - Verifies claim has required elements
   - Use: "Check if claim is properly formatted"
   - Returns: {assertions: {...}, all_pass: bool}
"""
