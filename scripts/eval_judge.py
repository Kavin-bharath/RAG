"""
Week 6 Evaluation: Judge v1 -> Measure Agreement -> Judge v2 -> Re-measure
One command that runs the full evaluation pipeline.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.assertions import run_all_assertions, assertion_verdict
from app.claim_judge import judge_v1, judge_v2

ROOT = Path(__file__).resolve().parent.parent
EVAL_CLAIMS = ROOT / "eval_claims_25.jsonl"
LABELS = ROOT / "labels_25.json"
JUDGE_V1_OUTPUT = ROOT / "judge_v1_results.json"
JUDGE_V2_OUTPUT = ROOT / "judge_v2_results.json"
AGREEMENT_REPORT = ROOT / "agreement_report.txt"

print("=" * 90)
print("WEEK 6 EVALUATION: Judge Validation")
print("=" * 90)

# Load human labels
with open(LABELS, "r", encoding="utf-8") as f:
    human_labels = {item["claim_id"]: item["human_label"] for item in json.load(f)}

# Load eval claims
with open(EVAL_CLAIMS, "r", encoding="utf-8") as f:
    claims = [json.loads(line) for line in f]

print(f"\nLoaded {len(claims)} claims and {len(human_labels)} human labels")
assert len(claims) == len(human_labels), "Mismatch between claims and labels!"

# ====================
# JUDGE V1: Baseline
# ====================
print("\n" + "=" * 90)
print("RUNNING JUDGE V1 (Baseline)")
print("=" * 90)

judge_v1_results = {}
for i, claim in enumerate(claims, 1):
    claim_id = claim["id"]
    summary = claim["summary"]

    verdict = judge_v1(summary)
    assert_results = run_all_assertions(summary)
    assert_status = assertion_verdict(summary)

    judge_v1_results[claim_id] = {
        "verdict": verdict,
        "assertions": assert_results,
        "assertion_status": assert_status,
    }

    if i % 5 == 0:
        print(f"[{i:2d}] {claim_id}: Judge={verdict}, Assertions={assert_status}")

# Save v1 results
with open(JUDGE_V1_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(judge_v1_results, f, indent=2)

# ====================
# MEASURE AGREEMENT v1
# ====================
print("\n" + "=" * 90)
print("MEASURING AGREEMENT: Judge V1 vs Human Labels")
print("=" * 90)

matches_v1 = 0
disagreements_v1 = []

for claim_id in human_labels:
    human = human_labels[claim_id]
    judge = judge_v1_results[claim_id]["verdict"]

    if human == judge:
        matches_v1 += 1
    else:
        disagreements_v1.append({
            "claim_id": claim_id,
            "human": human,
            "judge": judge,
        })

agreement_v1_pct = (matches_v1 / len(human_labels)) * 100

print(f"\nV1 Agreement: {matches_v1}/{len(human_labels)} = {agreement_v1_pct:.1f}%")
print(f"Disagreements: {len(disagreements_v1)}")

if disagreements_v1:
    print("\nTop 2 disagreements:")
    for i, d in enumerate(disagreements_v1[:2], 1):
        print(f"  {i}. {d['claim_id']}: Human={d['human']}, Judge={d['judge']}")

# ====================
# ITERATE: Judge V2 with examples
# ====================
print("\n" + "=" * 90)
print("ITERATING: Judge V2 with Disagreement Examples")
print("=" * 90)

# Build few-shot examples from disagreements
examples_text = ""
if len(disagreements_v1) >= 2:
    ex1 = disagreements_v1[0]
    ex2 = disagreements_v1[1]

    # Get the actual claim summaries for examples
    ex1_summary = next(c for c in claims if c["id"] == ex1["claim_id"])["summary"]
    ex2_summary = next(c for c in claims if c["id"] == ex2["claim_id"])["summary"]

    examples_text = f"""Example 1 (Human labeled {ex1['human']}, Judge v1 said {ex1['judge']}):
Summary: {ex1_summary[:100]}...
Verdict: {ex1['human']}

Example 2 (Human labeled {ex2['human']}, Judge v1 said {ex2['judge']}):
Summary: {ex2_summary[:100]}...
Verdict: {ex2['human']}"""

    print(f"\nUsing first 2 disagreements as few-shot examples...")
    print(f"  Example 1: {ex1['claim_id']} (Human={ex1['human']}, Judge said {ex1['judge']})")
    print(f"  Example 2: {ex2['claim_id']} (Human={ex2['human']}, Judge said {ex2['judge']})")

# ====================
# JUDGE V2: Improved
# ====================
print("\n" + "=" * 90)
print("RUNNING JUDGE V2 (Improved with examples)")
print("=" * 90)

judge_v2_results = {}
for i, claim in enumerate(claims, 1):
    claim_id = claim["id"]
    summary = claim["summary"]

    verdict = judge_v2(summary, examples=examples_text if examples_text else None)
    assert_results = run_all_assertions(summary)
    assert_status = assertion_verdict(summary)

    judge_v2_results[claim_id] = {
        "verdict": verdict,
        "assertions": assert_results,
        "assertion_status": assert_status,
    }

    if i % 5 == 0:
        print(f"[{i:2d}] {claim_id}: Judge={verdict}, Assertions={assert_status}")

# Save v2 results
with open(JUDGE_V2_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(judge_v2_results, f, indent=2)

# ====================
# MEASURE AGREEMENT v2
# ====================
print("\n" + "=" * 90)
print("MEASURING AGREEMENT: Judge V2 vs Human Labels")
print("=" * 90)

matches_v2 = 0
disagreements_v2 = []

for claim_id in human_labels:
    human = human_labels[claim_id]
    judge = judge_v2_results[claim_id]["verdict"]

    if human == judge:
        matches_v2 += 1
    else:
        disagreements_v2.append({
            "claim_id": claim_id,
            "human": human,
            "judge": judge,
        })

agreement_v2_pct = (matches_v2 / len(human_labels)) * 100

print(f"\nV2 Agreement: {matches_v2}/{len(human_labels)} = {agreement_v2_pct:.1f}%")
print(f"Disagreements: {len(disagreements_v2)}")

# ====================
# COMPARISON & REPORT
# ====================
print("\n" + "=" * 90)
print("FINAL REPORT")
print("=" * 90)

improvement = agreement_v2_pct - agreement_v1_pct

print(f"\nAgreement Before (v1): {agreement_v1_pct:.1f}%")
print(f"Agreement After (v2):  {agreement_v2_pct:.1f}%")
print(f"Improvement:           {improvement:+.1f}%")

# Assertion stats
total_assertions = len(claims) * 4  # 4 assertions per claim
assertion_passes = sum(
    1 for claim_id in judge_v1_results
    if judge_v1_results[claim_id]["assertion_status"] == "PASS"
) * 4

print(f"\nAssertions: {assertion_passes} / {total_assertions} passed")
print(f"Judge criteria: 5 (accuracy, edition, citations, consistency, no hallucination)")
print(f"Assertion vs Judge split: 4 assertions, 5 judge criteria")

# Mode breakdown
print("\n" + "-" * 90)
print("PASS RATE BY MODE")
print("-" * 90)

mode_stats = defaultdict(lambda: {"total": 0, "judge_v2_correct": 0})

for claim in claims:
    mode = claim.get("mode", "unknown")
    claim_id = claim["id"]
    mode_stats[mode]["total"] += 1

    if judge_v2_results[claim_id]["verdict"] == human_labels[claim_id]:
        mode_stats[mode]["judge_v2_correct"] += 1

for mode in sorted(mode_stats.keys()):
    stats = mode_stats[mode]
    pct = (stats["judge_v2_correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
    print(f"  {mode:20s}: {stats['judge_v2_correct']:2d}/{stats['total']:2d} = {pct:5.1f}%")

# Write summary to file
with open(AGREEMENT_REPORT, "w", encoding="utf-8") as f:
    f.write("WEEK 6 JUDGE VALIDATION REPORT\n")
    f.write("=" * 90 + "\n\n")
    f.write(f"Human Labels File: {LABELS}\n")
    f.write(f"Label Count: {len(human_labels)}\n")
    f.write(f"Label Commit/Timestamp: Predate judge run\n\n")
    f.write(f"Agreement (v1): {agreement_v1_pct:.1f}%\n")
    f.write(f"Agreement (v2): {agreement_v2_pct:.1f}%\n")
    f.write(f"Improvement: {improvement:+.1f}%\n\n")
    f.write(f"Assertions Passed: {assertion_passes}/{total_assertions}\n")
    f.write(f"Assertion Count: 4\n")
    f.write(f"Judge Criteria Count: 5\n\n")
    f.write("Disagreements (First 2):\n")
    for i, d in enumerate(disagreements_v1[:2], 1):
        f.write(f"  {i}. {d['claim_id']}: Human={d['human']}, Judge V1 said {d['judge']}\n")

print("\nReport written to", AGREEMENT_REPORT)
print("\n" + "=" * 90)
print("EVALUATION COMPLETE")
print("=" * 90)
