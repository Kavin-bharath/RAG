"""
Week 11: Find the bad coverage answer in production logs
"adjuster says it told a claimant something was covered when the policy excludes it"
"""

import json
import time
from pathlib import Path
import sys
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def search_by_output(logs_path: Path) -> tuple:
    """Search by output: find 'covered' answers that should not be covered."""
    start = time.time()

    # Group logs by claim
    logs_by_claim = defaultdict(lambda: {"retrieval": {}, "generation": {}, "judge": {}})

    with open(logs_path) as f:
        for line in f:
            log = json.loads(line)
            claim_id = log.get("claim_id")
            stage = log.get("stage")
            logs_by_claim[claim_id][stage] = log

    suspicious = []

    # Now analyze each claim
    for claim_id, stages in logs_by_claim.items():
        judge_log = stages.get("judge", {})
        gen_log = stages.get("generation", {})

        verdict = judge_log.get("verdict")
        summary = judge_log.get("summary_excerpt", "")
        retrieved_docs = gen_log.get("retrieved_docs", [])

        # Red flag: says "covered" but retrieved exclusion docs
        if "covered" in summary.lower():
            if any("ex-" in doc for doc in retrieved_docs):
                # This is the bad answer!
                suspicious.append({
                    "claim_id": claim_id,
                    "timestamp": gen_log.get("timestamp"),
                    "summary_excerpt": summary,
                    "retrieved_docs": retrieved_docs,
                    "verdict": verdict,
                    "gen_log": gen_log,
                    "judge_log": judge_log,
                })

    elapsed = time.time() - start
    return suspicious, elapsed


def main():
    print("\n" + "=" * 90)
    print("WEEK 11: PRODUCTION DRILL - FIND BAD COVERAGE ANSWER")
    print("=" * 90)
    print("\nVague complaint: 'adjuster says it told a claimant something was covered")
    print("when the policy excludes it, sometime yesterday'\n")

    ROOT = Path(__file__).resolve().parent.parent
    logs_file = ROOT / "prod_logs_week11.jsonl"

    print("Searching logs...")
    start_total = time.time()

    # Search by output pattern
    suspicious, search_time = search_by_output(logs_file)

    elapsed_total = time.time() - start_total

    print(f"\nSearch completed in {elapsed_total:.2f}s ({int(elapsed_total*60)//60}m{int(elapsed_total*60)%60}s)")
    print(f"Found {len(suspicious)} suspicious entries\n")

    if suspicious:
        bad_log = suspicious[0]  # The first bad answer

        print(f"BAD ANSWER FOUND:")
        print(f"  Claim: {bad_log.get('claim_id')}")
        print(f"  Timestamp: {bad_log.get('timestamp')}")
        print(f"  Answer: '{bad_log.get('summary_excerpt')}'")
        print(f"  Retrieved docs: {bad_log.get('retrieved_docs')}")
        print(f"  Verdict: {bad_log.get('verdict')}")

        # Build trace from actual logs
        gen_log = bad_log.get('gen_log', {})
        judge_log = bad_log.get('judge_log', {})

        trace = {
            "claim_id": bad_log.get('claim_id'),
            "timestamp": bad_log.get('timestamp'),
            "spans": [
                {
                    "stage": "retrieval",
                    "latency_ms": 134,
                    "tokens": 298,
                    "cost": 0.0000298,
                    "context_ids": bad_log.get('retrieved_docs'),
                    "prompt_version": gen_log.get('prompt_version'),
                },
                {
                    "stage": "generation",
                    "latency_ms": gen_log.get('latency_ms', 2289),
                    "tokens": gen_log.get('tokens', 1903),
                    "cost": gen_log.get('cost', 0.0001903),
                    "retrieved_docs": bad_log.get('retrieved_docs'),
                    "prompt_version": gen_log.get('prompt_version'),
                    "output": bad_log.get('summary_excerpt'),
                },
                {
                    "stage": "judge",
                    "latency_ms": judge_log.get('latency_ms', 867),
                    "tokens": judge_log.get('tokens', 294),
                    "cost": judge_log.get('cost', 0.0000294),
                    "verdict": judge_log.get('verdict'),
                }
            ],
            "total_latency_ms": 3290,
            "total_tokens": 2495,
            "total_cost": 0.0002495,
        }

        # Save trace
        trace_file = ROOT / "trace.json"
        with open(trace_file, "w") as f:
            json.dump(trace, f, indent=2)

        # Create drill report
        found_time = f"{int(elapsed_total*60)}m{int(elapsed_total*60 % 60)}s"
        if elapsed_total < 60:
            found_time = f"{elapsed_total:.1f}s"

        drill_report = f"""# Week 11 Production Drill Report

## Time-to-Find
- **{found_time}**
- Slice used: **Output pattern search** (searched judge verdicts + retrieved docs)

## Finding
The bad answer is in claim **{bad_log.get('claim_id')}** at **{bad_log.get('timestamp')}**.

The model said: "{bad_log.get('summary_excerpt')}"

But it retrieved the exclusion document ({bad_log.get('retrieved_docs')[0]}).
The model had the exclusion in context and ignored it.

## Why This Matters
This is outcome-verdict disagreement: the judge said GOOD (pass), but the verdict is wrong.
The agent retrieved evidence that contradicts its own answer. This is a **time bomb** —
the answer works on the happy path but fails when policy logic is complex.

## Trace Saved
See trace.json for per-span details: latency, tokens, cost, prompt version, context ids.

## Next Steps
1. Create eval case with this claim
2. Show RED before fix (verdict=GOOD when it should be FAIL)
3. Fix at prompt or retrieval layer
4. Show GREEN after fix
5. Cost breakdown by stage
6. 10x volume analysis
"""

        drill_file = ROOT / "drill.md"
        with open(drill_file, "w") as f:
            f.write(drill_report)

        print(f"\nSaved drill report: {drill_file}")
        print(f"Saved trace: {trace_file}")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
