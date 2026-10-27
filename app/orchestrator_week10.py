"""
Week 10 Multi-Agent Orchestrator
Decomposes claim questions into:
- Coverage/Exclusions Worker
- Adjuster Note Summary Worker
- Synthesis Worker
"""

import json
import time
from typing import Dict, Any, List
from enum import Enum

from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL

GROQ_COST_PER_1K_TOKENS = 0.0001


class OrchestrationStep(str, Enum):
    DECOMPOSE = "decompose"
    COVERAGE_WORKER = "coverage_worker"
    NOTES_WORKER = "notes_worker"
    SYNTHESIS = "synthesis"


class HandOffLog:
    """Tracks every hand-off and token count."""
    def __init__(self):
        self.handoffs = []

    def log(self, from_step: str, to_step: str, tokens: int, context_size: int):
        self.handoffs.append({
            "from": from_step,
            "to": to_step,
            "tokens": tokens,
            "context_size": context_size,
        })

    def total_tokens_for_handoff(self, from_step: str, to_step: str) -> int:
        return sum(h["tokens"] for h in self.handoffs if h["from"] == from_step and h["to"] == to_step)


class ClaimsOrchestrator:
    """Multi-agent orchestrator for claims processing."""

    def __init__(self, tools: Dict = None, inject_failure: bool = False):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.tokens_used = 0
        self.cost_used = 0.0
        self.steps = []
        self.handoff_log = HandOffLog()
        self.inject_failure = inject_failure
        self.failure_claim_id = "CLM-2026-0002"  # Inject failure on this claim

    def _call_llm(self, prompt: str, max_tokens: int = 200, step_name: str = "") -> tuple:
        """Call LLM and track tokens."""
        completion = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
        )

        response = completion.choices[0].message.content or ""
        tokens = completion.usage.total_tokens
        self.tokens_used += tokens
        self.cost_used += (tokens / 1000.0) * GROQ_COST_PER_1K_TOKENS

        return response.strip(), tokens

    def decompose(self, claim_id: str, query: str) -> Dict[str, str]:
        """Step 1: Decompose the claim question."""
        prompt = f"""Decompose this claim question into subtasks:

Claim ID: {claim_id}
User Question: {query}

Identify:
1. What coverage/exclusions need to be checked?
2. What adjuster notes are relevant?

Respond with JSON: {{"coverage_question": "...", "notes_question": "..."}}"""

        response, tokens = self._call_llm(prompt, max_tokens=150, step_name="decompose")
        self.handoff_log.log("user", "decompose", tokens, len(prompt))

        try:
            data = json.loads(response)
            return data
        except:
            return {"coverage_question": query, "notes_question": query}

    def coverage_worker(self, claim_id: str, coverage_question: str) -> Dict[str, Any]:
        """Step 2: Check coverage/exclusions (simulated worker)."""

        # Inject failure on specific claim
        if self.inject_failure and claim_id == self.failure_claim_id:
            return {"error": "Worker returned 500: Internal Server Error", "status": 500}

        prompt = f"""Check coverage for this claim:

Claim ID: {claim_id}
Question: {coverage_question}

Policy: HO-0304 standard homeowners form.

Respond: {{"status": "covered/excluded/partial", "reason": "..."}}"""

        response, tokens = self._call_llm(prompt, max_tokens=150, step_name="coverage_worker")
        self.handoff_log.log("decompose", "coverage_worker", tokens, len(prompt))

        try:
            data = json.loads(response)
            return data
        except:
            return {"status": "covered", "reason": "Standard coverage"}

    def notes_worker(self, claim_id: str, notes_question: str) -> Dict[str, Any]:
        """Step 3: Summarize adjuster notes (simulated worker)."""
        prompt = f"""Summarize adjuster notes for:

Claim ID: {claim_id}
Question: {notes_question}

Return: {{"summary": "...", "key_dates": "...", "status": "..."}}"""

        response, tokens = self._call_llm(prompt, max_tokens=150, step_name="notes_worker")
        self.handoff_log.log("decompose", "notes_worker", tokens, len(prompt))

        try:
            data = json.loads(response)
            return data
        except:
            return {"summary": "Claims processing", "key_dates": "", "status": "pending"}

    def synthesis(self, claim_id: str, coverage_result: Dict, notes_result: Dict) -> str:
        """Step 4: Synthesize final answer."""

        # If coverage worker failed, orchestrator must handle gracefully
        if coverage_result.get("error"):
            coverage_text = "DEGRADED: Coverage check unavailable (worker error)"
        else:
            coverage_text = f"Coverage: {coverage_result.get('status', 'unknown')}"

        notes_text = notes_result.get("summary", "No notes available")

        prompt = f"""Synthesize final answer for claim {claim_id}:

Coverage Analysis: {coverage_text}
Adjuster Notes: {notes_text}

Provide concise, final answer."""

        response, tokens = self._call_llm(prompt, max_tokens=200, step_name="synthesis")
        self.handoff_log.log("workers", "synthesis", tokens, len(prompt))

        return response

    def run(self, claim_id: str, query: str) -> Dict[str, Any]:
        """Run orchestrator on one claim."""
        start_time = time.time()
        self.tokens_used = 0
        self.cost_used = 0.0
        self.steps = []
        self.handoff_log = HandOffLog()

        try:
            # Step 1: Decompose
            decomp = self.decompose(claim_id, query)
            self.steps.append({"step": 1, "action": "decompose", "result": "done"})

            # Step 2 & 3: Workers (parallel conceptually, sequential here)
            coverage = self.coverage_worker(claim_id, decomp.get("coverage_question", ""))
            self.steps.append({"step": 2, "action": "coverage_worker", "result": "done"})

            notes = self.notes_worker(claim_id, decomp.get("notes_question", ""))
            self.steps.append({"step": 3, "action": "notes_worker", "result": "done"})

            # Step 4: Synthesis
            answer = self.synthesis(claim_id, coverage, notes)
            self.steps.append({"step": 4, "action": "synthesis", "result": "done"})

            elapsed = time.time() - start_time

            # Determine if worker failed
            worker_failed = coverage.get("error") is not None

            return {
                "claim_id": claim_id,
                "step_count": len(self.steps),
                "tokens_used": self.tokens_used,
                "cost_used": round(self.cost_used, 6),
                "execution_time": round(elapsed, 2),
                "answer": answer,
                "worker_failed": worker_failed,
                "failure_message": coverage.get("error") if worker_failed else None,
                "completed": True,
            }

        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "claim_id": claim_id,
                "step_count": len(self.steps),
                "tokens_used": self.tokens_used,
                "cost_used": round(self.cost_used, 6),
                "execution_time": round(elapsed, 2),
                "answer": f"Error: {str(e)}",
                "worker_failed": False,
                "completed": False,
            }
