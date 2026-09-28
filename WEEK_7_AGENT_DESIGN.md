# Week 7: Insurance Claims Agent

## Overview

Built a hand-crafted AI agent that handles multi-step insurance claim processing, then compared it against a fixed workflow to understand when agents are worth the complexity.

**Track**: D — Insurance Claims  
**Deliverable**: Agent loop + fixed workflow + comparison with metrics

---

## The Agent Loop

### Architecture: ReAct (Reasoning + Acting)

```
Loop:
  1. THINK   → LLM plans next action
  2. ACT     → Execute tool (retrieve, judge, check)
  3. OBSERVE → See result
  4. REPEAT  → Go to step 1 until done
```

### Implementation (app/agent.py)

**ClaimsAgent class:**
```python
class ClaimsAgent:
    - tools: Dict[str, Callable]          # retrieve_policy, judge_claim, check_assertion
    - max_steps: int = 10                 # Stop condition
    - max_tokens: int = 5000              # Token budget (cost safety)
    - steps: List[AgentStep]              # Visible history
    
    def run(query: str) → Dict:           # Main loop
        - Calls _plan_next_action()       # LLM decides what to do
        - Calls _execute_action()         # Run the tool
        - Tracks tokens and steps
        - Returns final answer + step log
```

**Stop Conditions:**
- Max 10 steps (no infinite loops)
- Max 5000 tokens budget (cost control)
- Stops when action = "synthesize_answer" (task complete)

---

## Tools Available to the Agent

### 1. retrieve_policy(query: str)
**Description**: Search for relevant policy information  
**When to use**: "What does this policy cover?"  
**Returns**: Retrieved chunks + policy summary

```python
def retrieve_policy(query: str) → Dict:
    chunks, answer = answer_query(query, top_k=3)
    return {"retrieved_chunks": chunks, "summary": answer}
```

### 2. judge_claim(summary: str)
**Description**: Evaluate if claim summary is GOOD or BAD  
**When to use**: "Is this claim summary accurate?"  
**Returns**: Verdict (GOOD/BAD)

```python
def judge_claim(summary: str) → Dict:
    verdict = judge_v2(summary)  # Uses judge from Week 6
    return {"verdict": verdict, "summary_excerpt": summary[:100]}
```

### 3. check_assertion(summary: str)
**Description**: Verify claim has required elements (CLM#, date, amount, exclusion cite)  
**When to use**: "Is this claim properly formatted?"  
**Returns**: Assertion results (pass/fail on each check)

```python
def check_assertion(summary: str) → Dict:
    assertions = run_all_assertions(summary)  # Uses assertions from Week 6
    return {"assertions": assertions, "all_pass": all(assertions.values())}
```

---

## Fixed Workflow

**Same task, deterministic sequence (no loops):**

```
Step 1: Retrieve policy info
  ↓
Step 2: Judge claim summary
  ↓
Step 3: Check format assertions
  ↓
Step 4: Synthesize answer
  ↓
Done (always)
```

**Always exactly 4 steps. No branching. No LLM deciding what to do next.**

Implementation: `scripts/fixed_workflow.py`

```python
def process_claim_fixed(query: str, summary: str) → Dict:
    step1_chunks = retrieve_policy(query)           # Always do this
    step2_verdict = judge_v2(summary)               # Always do this
    step3_assertions = run_all_assertions(summary)  # Always do this
    step4_answer = synthesize(...)                  # Combine results
    return {"steps": 4, "answer": step4_answer, "time": ..., "tokens": ...}
```

---

## Comparison Metrics

### Speed
- **Agent**: LLM calls for planning = slower
- **Fixed**: Direct tool execution = faster
- **Expected**: Fixed is 5-10x faster

### Cost (Tokens)
- **Agent**: Planning + reasoning = high token cost
- **Fixed**: No LLM thinking, only tool execution = low cost
- **Expected**: Agent uses 3-5x more tokens

### Reliability
- **Agent**: Variable steps, needs budgeting to avoid infinite loops
- **Fixed**: Always 4 steps, deterministic, no risk
- **Expected**: Fixed is 100% reliable

---

## When to Use Each

### Use the AGENT when:
- ✓ Path changes with input (e.g., "if policy doesn't cover, suggest endorsement")
- ✓ Uncertain task structure (e.g., chatbot with follow-ups)
- ✓ Complex reasoning needed (e.g., "interpret this confusing clause")
- ✓ Multi-branch logic (e.g., "check 3 different things depending on coverage type")

### Use FIXED WORKFLOW when:
- ✓ Steps are always the same (insurance → judge → format → answer)
- ✓ No branching logic needed
- ✓ Speed matters (faster, cheaper)
- ✓ Reliability is critical (no loops, fully predictable)

---

## Insurance Claims Case

**Task**: Process a customer claim query + evaluate claim summary

**Best choice**: **FIXED WORKFLOW**

**Why**:
1. **Clear sequence**: Retrieve → Judge → Check → Answer (always in this order)
2. **No branching**: Even if claim is BAD, we still do all steps
3. **Speed critical**: Customer expects quick response
4. **Cost matters**: Every LLM call adds up at scale
5. **Fully predictable**: No infinite loops possible

**When you'd switch to Agent**:
- If different claim types needed different paths (e.g., "liability claims need extra verification")
- If you wanted the system to ask follow-up questions
- If you needed to branch based on coverage gaps

---

## Code Files

| File | Purpose |
|------|---------|
| `app/agent.py` | Agent loop implementation (ClaimsAgent class) |
| `app/tools.py` | Tool definitions with clear descriptions |
| `scripts/fixed_workflow.py` | Fixed 4-step sequence |
| `scripts/agent_vs_fixed.py` | Comparison script + metrics |
| `agent_vs_fixed_results.json` | Raw results data |

---

## How the Agent Decides

The agent uses LLM planning to pick the next action:

```python
def _plan_next_action(query: str, context: str):
    prompt = """
    Available actions:
    1. retrieve_policy - Search for coverage info
    2. judge_claim - Evaluate claim quality
    3. check_assertion - Verify formatting
    4. synthesize_answer - Return final answer
    
    What's the next step?
    """
    
    response = llm(prompt)  # LLM picks: "retrieve_policy"
    return parse(response)
```

**Tool descriptions are critical**: Clear descriptions → agent picks right tool.

---

## Visible Steps

Every agent run logs steps so you can see exactly what it did:

```json
{
  "step": 1,
  "thought": "Need to find what the policy covers",
  "action": "retrieve_policy",
  "input": "water damage",
  "result": "Water damage from sudden discharge is covered..."
}
```

Debug-friendly: If agent makes a wrong choice, you see it immediately.

---

## Key Takeaway

**Simpler is better**: Fixed workflow wins on speed, cost, and reliability.  
**Agents are for uncertainty**: Use them when the path isn't known upfront.

For insurance claims: The path is always known. Use the fixed workflow.
