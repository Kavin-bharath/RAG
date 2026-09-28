# Week 6: Judge Validation with Human Labels

## Objective
Measure how well an LLM judge aligns with human labels on 25 insurance claim summaries, then iterate the judge using disagreements as few-shot examples.

## Setup

### Human Labels (Blind Protocol)
- **File**: `labels_25.json` — committed FIRST before judge runs
- **Format**: 25 items, each with `claim_id`, `trace_id`, `mode`, `human_label` (GOOD or BAD)
- **Modes**: clean (16), ambiguous-query (4), weak-ranking (1), truncation (2), unknown (2)
- **Distribution**: 19 GOOD, 6 BAD

### Evaluation Set
- **File**: `eval_claims_25.jsonl` — 25 JSONL lines, one claim per line
- **Fields**: `id`, `trace_id`, `mode`, `summary`
- **Summary format**:
  ```
  CLAIM: CLM-YYYY-NNNNN
  Date of Loss: YYYY-MM-DD
  Deductible: $X,XXX
  
  COVERAGE SUMMARY:
  [LLM-generated claim summary text]
  ```

### Deterministic Assertions
- **claim_number**: CLM-YYYY-NNNNN format present
- **date_parseable**: YYYY-MM-DD format present
- **amount_numeric**: $X or %, or plain number present
- **exclusion_when_denial**: If denial stated, must cite exclusion code (E-## or F-##)

**Verdict**: PASS if all 4 pass, FAIL with list of failures

## Judge Versions

### Judge V1 (Baseline)
- Criteria: 5 (accuracy, edition, citations, consistency, no hallucination)
- Examples: None (zero-shot)
- Prompt length: ~300 chars + claim summary
- Max tokens: 500 (to allow reasoning time)

### Judge V2 (Few-shot)
- Criteria: Same 5 as V1
- Examples: 2 concrete examples, sourced from V1 disagreements
  - Example 1: Claim that V1 mislabeled → human label inserted as "correct"
  - Example 2: Claim that V1 mislabeled → human label inserted as "correct"
- Prompt length: ~700 chars + claim summary + examples
- Max tokens: 500

## Evaluation Process

1. **Run Judge V1** on all 25 claims
   - Record verdict (GOOD/BAD/UNKNOWN)
   - Record assertion results

2. **Measure Agreement V1**
   - Compare judge V1 verdicts against human labels
   - Identify disagreements
   - Extract top 2 disagreements

3. **Iterate to Judge V2**
   - Use top 2 disagreements as few-shot examples
   - Embed real claim summaries in examples
   - Mark examples with human labels (ground truth)

4. **Run Judge V2** on all 25 claims (same set)
   - Record verdict (GOOD/BAD/UNKNOWN)
   - Record assertion results

5. **Measure Agreement V2**
   - Compare judge V2 verdicts against human labels
   - Calculate improvement: (V2% - V1%) / V1%
   - Report pass rate by mode

## Files Generated

| File | Purpose |
|------|---------|
| `judge_v1_results.json` | Verdicts and assertions from V1 |
| `judge_v2_results.json` | Verdicts and assertions from V2 |
| `agreement_report.txt` | Summary of agreement metrics |
| `judge_v1.txt` | V1 prompt (for documentation) |
| `judge_v2.txt` | V2 prompt (for documentation) |
| `WEEK_6_SUMMARY.md` | This file |

## Key Metrics

- **V1 Agreement**: % of cases where Judge V1 agrees with human labels
- **V2 Agreement**: % of cases where Judge V2 agrees with human labels
- **Improvement**: (V2 - V1) percentage point change
- **Assertions Pass Rate**: % of all 100 assertion checks (25 claims × 4 assertions) that pass
- **Pass Rate by Mode**: Judge V2 accuracy broken down by failure mode

## Expected Outcomes

Based on initial prediction (updated 2026-09-15):
- V1: ~60% agreement (without examples, model struggles with nuance)
- V2: ~75% agreement (with examples showing denial nuance and carve-back patterns)
- Improvement: ~15 percentage points

The improvement comes from teaching the judge the distinction between:
- **BAD**: "Earthquake always excluded. No coverage." (crude, ignores carve-back)
- **GOOD**: "Earthquake excluded under E-2. Buyback available via endorsement." (accurate, cites code)

## Notes on Blind Protocol

The human labels were committed to git BEFORE any judge code ran. This ensures:
1. No data leakage from judge decisions back to human judgment
2. Reproducible measurement (labels don't change)
3. Falsifiability (prediction can be wrong, validates hypothesis)

The labels can be reviewed by opening `labels_25.json` to see which traces were labeled GOOD vs BAD and why.
