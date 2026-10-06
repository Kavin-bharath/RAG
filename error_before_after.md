# Week 9: Error Handling Before & After

## Tool Docstring Rewrite

### BEFORE: Generic Error
```python
def get_claim_status(claim_number: str):
    """Get the current status of a claim (approved, denied, pending)"""
    if claim_number not in CLAIMS_DB:
        return {"error": "Lookup failed"}
```

**Problem**: Model can't distinguish typo from dead system.

### AFTER: Recoverable Error with Prompt
```python
def get_claim_status(claim_number: str):
    """Get the current status of a claim (approved, denied, pending).
    
    Returns: status string (approved, denied, pending)
    Error: If claim not found, returns descriptive message with format hint.
    The format for claim numbers is CLM-YYYY-NNNNN (e.g., CLM-2026-0001).
    """
    if claim_number not in CLAIMS_DB:
        return {
            "error": "Claim CLM-2024-88120 not found. Claim numbers look like CLM-YYYY-NNNNN. Check the claim number and try again."
        }
```

---

## Model Interaction: Before vs After

### BEFORE: Generic Error (Model Gets No Useful Info)

**User Query**: "What's the status of claim CLM-2024-88120?"

**Model receives**:
```
Tool: get_claim_status
Response: {"error": "Lookup failed"}

Model thinking: "Hmm, lookup failed. System might be down. I don't know if it's a bad claim number or a system error."

Model response: "I'm unable to determine the claim status. The lookup failed, which could mean the claim system is down or the claim number is invalid."
```

**Problem**: Model hedges and doesn't help user fix the problem.

---

### AFTER: Recoverable Error (Model Gets Clear Guidance)

**User Query**: "What's the status of claim CLM-2024-88120?"

**Model receives**:
```
Tool: get_claim_status
Response: {
  "error": "Claim CLM-2024-88120 not found. Claim numbers look like CLM-YYYY-NNNNN. 
           Check the claim number and try again."
}

Model thinking: "The error tells me exactly what's wrong:
  1. CLM-2024-88120 was not found
  2. Format is CLM-YYYY-NNNNN
  3. This is probably a typo by the user
  I should ask the user to verify the claim number."

Model response: "Claim CLM-2024-88120 was not found in the system. Claim numbers follow the format CLM-YYYY-NNNNN (e.g., CLM-2026-0001). Could you verify the claim number? Did you mean CLM-2026-8812 or another claim?"
```

**Benefit**: 
- ✓ Model understands the problem
- ✓ Model explains what went wrong
- ✓ Model helps user fix it (suggests format, asks for verification)
- ✓ User can immediately retry with correct number

---

## Key Insight

The error message became a **prompt** embedded in the tool response. Instead of:
- "Error 3" → Model hedges
- "Lookup failed" → Model confused

We use:
- "Claim X not found. Format is CLM-YYYY-NNNNN. Check and try again." → Model recovers intelligently

This is the **context sandwich pattern**: embed what-went-wrong, what-the-format-is, and what-to-do-next in the error itself.
