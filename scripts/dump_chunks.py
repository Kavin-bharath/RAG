"""
Inspection view (dump mode): list every chunk currently stored in Pinecone,
grouped by source document, so you can pick chunk_ids for golden_set.jsonl
by reading real text instead of guessing IDs in the console.

Run from the project root:
    python scripts/dump_chunks.py
"""

import sys
from pathlib import Path

# Allow running as `python scripts/dump_chunks.py` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.vectorstore import get_index  # noqa: E402

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "chunks_dump.txt"


def main():
    index = get_index()

    all_ids = []
    for id_batch in index.list():
        all_ids.extend(item.id for item in id_batch)

    print(f"Found {len(all_ids)} vector ids in the index.")

    records = []
    batch_size = 100
    for i in range(0, len(all_ids), batch_size):
        batch = all_ids[i : i + batch_size]
        fetched = index.fetch(ids=batch)
        for vec_id, vec in fetched.vectors.items():
            meta = vec.metadata or {}
            records.append(
                {
                    "id": vec_id,
                    "source": meta.get("source", "unknown"),
                    "text": meta.get("text", ""),
                }
            )

    records.sort(key=lambda r: (r["source"], r["id"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        current_source = None
        for r in records:
            if r["source"] != current_source:
                current_source = r["source"]
                f.write(f"\n{'=' * 80}\nSOURCE: {current_source}\n{'=' * 80}\n")
            f.write(f"\n--- chunk_id: {r['id']} ---\n{r['text']}\n")

    print(f"Wrote {len(records)} chunks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
