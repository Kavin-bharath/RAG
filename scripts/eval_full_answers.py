"""
Phase 5 support: run the FULL pipeline (retrieval + Groq generation) on every
golden question, not just retrieval. Needed to tell apart:
  - R: correct chunk_id not in top-3 (retrieval's fault)
  - G: correct chunk_id WAS in top-3, but the generated answer is still wrong
       (generation's fault)

Run from the project root:
    python scripts/eval_full_answers.py
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval import answer_query  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_SET_PATH = ROOT / "golden_set.jsonl"
EVAL_RESULTS_PATH = ROOT / "eval_results.json"
OUTPUT_PATH = ROOT / "full_answers.json"


def load_golden_set():
    items = []
    with open(GOLDEN_SET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def main():
    golden_set = load_golden_set()
    hit_lookup = {}
    if EVAL_RESULTS_PATH.exists():
        eval_data = json.loads(EVAL_RESULTS_PATH.read_text(encoding="utf-8"))
        hit_lookup = {r["id"]: r["hit_at_3"] for r in eval_data["results"]}

    outputs = []
    for item in golden_set:
        result = answer_query(item["question"])
        outputs.append(
            {
                "id": item["id"],
                "question": item["question"],
                "expected_chunk_id": item["chunk_id"],
                "hit_at_3": hit_lookup.get(item["id"]),
                "answer": result["answer"],
                "sources": result["sources"],
            }
        )
        print(f"\n{'=' * 90}")
        print(f"Q{item['id']} (hit@3={hit_lookup.get(item['id'])}): {item['question']}")
        print(f"Answer: {result['answer']}")
        print(f"Sources: {result['sources']}")

    OUTPUT_PATH.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(f"\nWrote {len(outputs)} full answers to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
