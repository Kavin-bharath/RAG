"""
Hand-built agent loop for insurance claims processing.
Agent: plan → act → observe → repeat until done.
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL


class AgentAction(str, Enum):
    RETRIEVE = "retrieve_policy"
    JUDGE = "judge_claim"
    CHECK_ASSERTION = "check_assertion"
    SYNTHESIZE = "synthesize_answer"


class AgentStep:
    """Represents one step in the agent's reasoning."""

    def __init__(self, step_num: int, thought: str, action: str, input_data: str, result: str):
        self.step_num = step_num
        self.thought = thought
        self.action = action
        self.input_data = input_data
        self.result = result
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "step": self.step_num,
            "thought": self.thought,
            "action": self.action,
            "input": self.input_data,
            "result": self.result,
        }


class ClaimsAgent:
    """Agent that processes insurance claims using a loop."""

    def __init__(self, tools: Dict[str, Callable], model: str = GROQ_MODEL):
        self.tools = tools
        self.model = model
        self.client = Groq(api_key=GROQ_API_KEY)
        self.steps: List[AgentStep] = []
        self.max_steps = 10
        self.max_tokens = 5000  # Total token budget
        self.tokens_used = 0

    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Groq LLM and track tokens."""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
        )

        response = completion.choices[0].message.content or ""
        if not response and hasattr(completion.choices[0].message, 'reasoning'):
            response = completion.choices[0].message.reasoning or ""

        # Track token usage
        self.tokens_used += completion.usage.total_tokens

        return response.strip()

    def _plan_next_action(self, query: str, context: str) -> tuple:
        """Ask LLM what to do next: thought, action, input."""
        prompt = f"""You are processing an insurance claim query. Based on the query and context, decide the next action.

Query: {query}

Context so far: {context}

Available actions:
1. retrieve_policy - Search for relevant policy information
2. judge_claim - Evaluate if a claim summary is good or bad
3. check_assertion - Verify claim summary has required elements
4. synthesize_answer - Combine findings into final answer

Respond ONLY in this JSON format:
{{
  "thought": "why we need this action",
  "action": "one of the four actions above",
  "input": "what to pass to the action"
}}"""

        response = self._call_llm(prompt, max_tokens=200)

        try:
            data = json.loads(response)
            return data.get("thought", ""), data.get("action", ""), data.get("input", "")
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            return "Parse error", "synthesize_answer", context

    def _execute_action(self, action: str, input_data: str) -> str:
        """Execute the tool and return result."""
        if action not in self.tools:
            return f"Error: Unknown action '{action}'"

        try:
            result = self.tools[action](input_data)
            return str(result)
        except Exception as e:
            return f"Error executing {action}: {str(e)}"

    def _should_continue(self, step_num: int, action: str) -> bool:
        """Check stop conditions."""
        if step_num >= self.max_steps:
            return False
        if self.tokens_used >= self.max_tokens:
            return False
        if action == "synthesize_answer":
            return False
        return True

    def run(self, query: str) -> Dict[str, Any]:
        """Run the agent loop."""
        start_time = time.time()
        self.steps = []
        self.tokens_used = 0

        context = f"Initial query: {query}\n"
        step_num = 1

        while step_num <= self.max_steps and self.tokens_used < self.max_tokens:
            # Plan next action
            thought, action, input_data = self._plan_next_action(query, context)

            # Execute action
            result = self._execute_action(action, input_data)

            # Record step
            step = AgentStep(step_num, thought, action, input_data, result)
            self.steps.append(step)

            # Update context
            context += f"Step {step_num}: {action} → {result[:100]}...\n"

            # Check if we should continue
            if not self._should_continue(step_num, action):
                break

            step_num += 1

        # Synthesize final answer
        final_prompt = f"""Based on these steps, provide a final answer to: {query}

Steps taken:
{json.dumps([s.to_dict() for s in self.steps], indent=2)}

Provide a concise, clear answer based on the findings."""

        final_answer = self._call_llm(final_prompt, max_tokens=300)

        elapsed = time.time() - start_time

        return {
            "query": query,
            "answer": final_answer,
            "steps": [s.to_dict() for s in self.steps],
            "step_count": len(self.steps),
            "tokens_used": self.tokens_used,
            "execution_time_seconds": elapsed,
            "completed": len(self.steps) > 0 and self.steps[-1].action == "synthesize_answer",
        }
