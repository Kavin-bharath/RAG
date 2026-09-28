"""
Week 7 Agent: Hand-built loop with ALL FOUR budgets enforced.
Budgets: max_steps, max_tokens, max_cost, wall_clock.
"""

import json
import time
from typing import Any, Callable, Dict, List

from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL

GROQ_COST_PER_1K_TOKENS = 0.0001


class AgentStep:
    def __init__(self, step_num: int, thought: str, action: str, input_data: str, result: Any, tokens: int = 0):
        self.step_num = step_num
        self.thought = thought
        self.action = action
        self.input_data = input_data
        self.result = result
        self.tokens = tokens
        self.timestamp = time.time()


class ClaimsAgent:
    """Claims agent with all 4 budgets."""

    def __init__(self, tools: Dict[str, Callable], model: str = GROQ_MODEL):
        self.tools = tools
        self.model = model
        self.client = Groq(api_key=GROQ_API_KEY)
        self.steps: List[AgentStep] = []

        # All 4 budgets
        self.max_steps = 10
        self.max_tokens = 3000
        self.max_cost = 0.02  # $0.02 per claim
        self.max_time = 30    # 30 seconds

        # Tracking
        self.tokens_used = 0
        self.cost_used = 0.0
        self.start_time = None
        self.budget_hit = None

    def _check_budgets(self, step_num: int):
        """Check all 4 budgets before proceeding."""
        elapsed = time.time() - self.start_time

        if step_num > self.max_steps:
            self.budget_hit = f"max_steps ({self.max_steps})"
            return False

        if self.tokens_used > self.max_tokens:
            self.budget_hit = f"max_tokens ({self.max_tokens})"
            return False

        if self.cost_used > self.max_cost:
            self.budget_hit = f"max_cost (${self.max_cost:.4f})"
            return False

        if elapsed > self.max_time:
            self.budget_hit = f"wall_clock ({self.max_time}s)"
            return False

        return True

    def _call_llm(self, prompt: str, max_tokens: int = 200) -> tuple:
        """Call LLM and track tokens/cost."""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
        )

        response = completion.choices[0].message.content or ""
        if not response and hasattr(completion.choices[0].message, 'reasoning'):
            response = completion.choices[0].message.reasoning or ""

        tokens = completion.usage.total_tokens
        self.tokens_used += tokens
        self.cost_used += (tokens / 1000.0) * GROQ_COST_PER_1K_TOKENS

        return response.strip(), tokens

    def run(self, claim_id: str) -> Dict[str, Any]:
        """Run agent on one claim."""
        self.start_time = time.time()
        self.steps = []
        self.tokens_used = 0
        self.cost_used = 0.0
        self.budget_hit = None

        context = f"Claim ID: {claim_id}\n"
        step_num = 1

        while self._check_budgets(step_num):
            # Plan next action
            prompt = f"""You are triaging an insurance claim. Choose the next step.

{context}

Available actions:
1. retrieve_claim - Get claim details and adjuster notes
2. check_policy_exclusions - Check if loss type is excluded
3. compute_payout - Calculate final payout
4. complete - Return final verdict

Choose ONE. Respond with JSON: {{"thought": "...", "action": "...", "input": "..."}}"""

            response, plan_tokens = self._call_llm(prompt, max_tokens=200)

            try:
                data = json.loads(response)
                thought = data.get("thought", "")
                action = data.get("action", "complete")
                input_data = data.get("input", "")
            except json.JSONDecodeError:
                thought = "Parse error"
                action = "complete"
                input_data = ""

            # Execute action
            if action == "complete":
                break

            if action not in self.tools:
                result = {"error": f"Unknown action: {action}"}
            else:
                try:
                    if action == "retrieve_claim":
                        result = self.tools[action](claim_id)
                    elif action == "check_policy_exclusions":
                        # Extract loss_type from context if needed
                        result = self.tools[action](claim_id, input_data)
                    elif action == "compute_payout":
                        # Parse input: "amount|status|excess"
                        parts = input_data.split("|")
                        if len(parts) >= 3:
                            result = self.tools[action](claim_id, float(parts[0]), parts[1], float(parts[2]))
                        else:
                            result = {"error": "Invalid compute_payout input"}
                    else:
                        result = {"error": f"Unknown action: {action}"}
                except Exception as e:
                    result = {"error": str(e)}

            # Record step
            step = AgentStep(step_num, thought, action, input_data, result, plan_tokens)
            self.steps.append(step)

            # Update context
            context += f"Step {step_num}: {action} → {str(result)[:80]}\n"
            step_num += 1

        elapsed = time.time() - self.start_time

        return {
            "claim_id": claim_id,
            "step_count": len(self.steps),
            "tokens_used": self.tokens_used,
            "cost_used": round(self.cost_used, 6),
            "execution_time": round(elapsed, 2),
            "budget_hit": self.budget_hit,
            "completed": len(self.steps) > 0,
            "steps": [{"step": s.step_num, "action": s.action, "tokens": s.tokens} for s in self.steps],
        }
