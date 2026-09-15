"""
Phase 4 (and reusable for Phase 7): measure hit-rate@3 and p50 latency of the
current retriever against golden_set.jsonl.

Run from the project root:
    python scripts/eval_hit_rate.py

Writes a full per-question report to eval_results.json and prints a summary
table + hit-rate@3 + p50 latency to the console.
"""

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval import search  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_SET_PATH = ROOT / "golden_set.jsonl"
OUTPUT_PATH = ROOT / "eval_results.json"

TOP_K_FOR_HIT_RATE = 3


def load_golden_set():
    items = []
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def run_eval():
    golden_set = load_golden_set()
    results = []
    latencies = []

    for item in golden_set:
        question = item["question"]
        expected_chunk_id = item["chunk_id"]

        start = time.perf_counter()
        matches = search(question, top_k=5)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

        retrieved = [
            {"chunk_id": m.id, "score": m.score, "source": (m.metadata or {}).get("source")}
            for m in matches
        ]
        top3_ids = [r["chunk_id"] for r in retrieved[:TOP_K_FOR_HIT_RATE]]
        hit = expected_chunk_id in top3_ids

        results.append(
            {
                "id": item["id"],
                "question": question,
                "expected_chunk_id": expected_chunk_id,
                "hard_token": item.get("hard_token", False),
                "hit_at_3": hit,
                "retrieved_top5": retrieved,
                "latency_ms": round(elapsed_ms, 2),
            }
        )

    hits = sum(1 for r in results if r["hit_at_3"])
    hit_rate = hits / len(results)
    p50_latency = statistics.median(latencies)

    report = {
        "hit_rate_at_3": hit_rate,
        "hits": hits,
        "total": len(results),
        "p50_latency_ms": round(p50_latency, 2),
        "results": results,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Console summary
    print(f"\n{'=' * 90}")
    print(f"hit-rate@3 : {hits}/{len(results)}  =  {hit_rate:.2%}")
    print(f"p50 latency: {p50_latency:.2f} ms")
    print(f"{'=' * 90}")
    print(f"{'ID':<3} {'HIT':<5} {'HARD':<6} {'LATENCY(ms)':<12} QUESTION")
    print(f"{'-' * 90}")
    for r in results:
        hit_mark = "YES" if r["hit_at_3"] else "NO"
        hard_mark = "yes" if r["hard_token"] else ""
        print(f"{r['id']:<3} {hit_mark:<5} {hard_mark:<6} {r['latency_ms']:<12} {r['question'][:65]}")
    print(f"{'-' * 90}")
    print(f"\nFull per-question detail (expected vs retrieved) written to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_eval()
