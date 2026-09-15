"""
Trace logging for Week 5 error analysis.
Every /query call writes a JSON trace to traces.jsonl for later review.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

TRACES_FILE = Path(__file__).resolve().parent.parent / "traces.jsonl"


def write_trace(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    llm_response: str,
    sources: List[str],
    ground_truth: str = None,
) -> str:
    """
    Write a single query trace to traces.jsonl.
    Returns the trace_id.
    """
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"
    timestamp = datetime.utcnow().isoformat()

    trace = {
        "trace_id": trace_id,
        "timestamp": timestamp,
        "query": query,
        "retrieved_chunks": retrieved_chunks,
        "llm_response": llm_response,
        "sources": sources,
        "ground_truth": ground_truth,
    }

    with open(TRACES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace) + "\n")

    return trace_id
