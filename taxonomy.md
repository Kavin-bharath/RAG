# Failure Modes Taxonomy — Week 5

**Sample:** 20 traces, seeded random (seed=42)  
**Correct answers:** 20/20 (100%)  
**Failure modes observed:** 3 (no wrong answers in sample)

## Modes

| Mode | Count | % | Severity | Example | Notes |
|------|-------|----|---------|----|-------|
| Ambiguous query (no form/edition specified) | 3 | 15% | Annoys adjuster (could use wrong policy) | trace-6 ("Coverage A limit?" → assumed ed-01-22) | User query omits edition when multiple exist; system picks one (happens to be consistent across editions in this corpus, but risky) |
| Non-top-3 source chunk | 2 | 10% | None (answer still correct) | trace-4 (flood query retrieved endorsements before E-3 exclusion) | Correct chunk ranked 4th-5th instead of top-3; LLM synthesized correct answer anyway |
| Truncated chunk metadata in trace | 2 | 10% | None (documentation only) | trace-8 (pre-auth checklist chunk text cut off) | Stored preview text is 100 chars; full text apparently used by LLM, so display issue only |
| Direct well-formed queries | 13 | 65% | None (working correctly) | trace-2 (form/edition + peril explicit) | Form/edition + exclusion code specified; retrieval top-1 or top-2 match; LLM cites correctly |

---

## Key Observations

- **No wrong answers observed.** All 20 traces have factually correct LLM responses with proper citations.
- **Ambient risks:** Ambiguous queries (15%) could fail in a corpus with form-specific variants. Current corpus has consistent limits/wording across editions, masking the risk.
- **Retrieval mild decay:** 10% of traces had correct context outside top-3 but LLM still recovered. Indicates dense ranking has some imprecision, but cross-encoder reranker (from Week 4) is already mitigating this.
- **System is healthy.** No hallucinations, no citation errors, no exclusion misapplications observed.

---

## Next Steps

All 3 non-ideal modes are low-severity. If forced to pick ONE to address:
**Ambiguous query mode** (15%, annoys adjuster) — require or infer edition specification.
