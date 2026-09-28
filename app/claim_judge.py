"""
LLM judge for claim summaries.
Evaluates whether a claim summary is GOOD or BAD.
"""

from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL

_groq_client = Groq(api_key=GROQ_API_KEY)


# Judge v1: baseline prompt
JUDGE_V1_PROMPT = """You are evaluating claim summaries for quality and accuracy.
Your task: Decide whether the claim summary is GOOD or BAD.

A GOOD summary:
- Contains accurate policy information with proper citations
- Correctly applies exclusions and conditions
- Avoids hallucinated or invented coverage
- Cites the correct form/edition when relevant
- Covers relevant details without contradictions

A BAD summary:
- Invents coverage not in the policy
- Misquotes or misapplies exclusions
- Cites the wrong policy edition or form
- Contains factual errors about coverage
- Confuses inclusions with exclusions

Summary to evaluate:
{summary}

Respond with only: GOOD or BAD"""


# Judge v2: template with dynamic disagreement examples
JUDGE_V2_PROMPT_TEMPLATE = """You are evaluating claim summaries for quality and accuracy.
Your task: Decide whether the claim summary is GOOD or BAD.

A GOOD summary:
- Contains accurate policy information with proper citations
- Correctly applies exclusions and conditions
- Avoids hallucinated or invented coverage
- Cites the correct form/edition when relevant
- Covers relevant details without contradictions

A BAD summary:
- Invents coverage not in the policy
- Misquotes or misapplies exclusions
- Cites the wrong policy edition or form
- Contains factual errors about coverage
- Confuses inclusions with exclusions

{examples}

Summary to evaluate:
{summary}

Respond with only: GOOD or BAD"""

DEFAULT_EXAMPLES = """Example 1 (BAD - misapplied exclusion without clarity):
Summary: "Water damage is always excluded. The policy does not cover any water loss."
Verdict: BAD — oversimplifies exclusion; ignores carve-back for sudden accidental discharge in ed-03-24 or endorsement buyback in ed-01-22/02-23.

Example 2 (GOOD - accurate denial with exclusion cite):
Summary: "Earthquake is excluded under Exclusion E-2 (Earth Movement). The policy does not cover earthquake damage unless a separate earthquake endorsement is attached."
Verdict: GOOD — correctly cites exclusion code, explains buyback option, avoids invention."""


def judge_v1(summary: str) -> str:
    """Run claim summary through Judge v1."""
    prompt = JUDGE_V1_PROMPT.format(summary=summary)
    return _judge(prompt)


def judge_v2(summary: str, examples: str = None) -> str:
    """Run claim summary through Judge v2 (improved with examples)."""
    if examples is None:
        examples = DEFAULT_EXAMPLES
    prompt = JUDGE_V2_PROMPT_TEMPLATE.format(summary=summary, examples=examples)
    return _judge(prompt)


def _judge(prompt: str) -> str:
    """Call Groq LLM to judge."""
    try:
        completion = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500,
        )

        if not completion.choices:
            return "UNKNOWN"

        choice = completion.choices[0]
        response = (choice.message.content or "").strip()

        # If content is empty, try reasoning (for extended-thinking models)
        if not response and hasattr(choice.message, 'reasoning') and choice.message.reasoning:
            response = choice.message.reasoning.strip()

        response_upper = response.upper()
        # Ensure it's one of our two labels
        if "GOOD" in response_upper:
            return "GOOD"
        elif "BAD" in response_upper:
            return "BAD"
        else:
            return "UNKNOWN"
    except Exception:
        return "UNKNOWN"
