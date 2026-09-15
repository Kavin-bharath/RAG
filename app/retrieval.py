from dataclasses import dataclass
from functools import lru_cache

from groq import Groq
from sentence_transformers import CrossEncoder

from app.config import GROQ_API_KEY, GROQ_MODEL, TOP_K
from app.embeddings import embed_query
from app.vectorstore import get_index

SYSTEM_PROMPT = (
    "You are a document Q&A assistant. Answer ONLY using the provided context. "
    "Every claim in your answer must be traceable to the context below. "
    "If the context does not contain enough information to answer the question, "
    "reply exactly with: \"I don't know based on the provided documents.\" "
    "Never use outside knowledge and never guess."
)

# Retrieval change (Week 4 Task Set D): dense retrieval alone was ranking the
# correct chunk outside the top-3 in every observed failure, while it was
# still present somewhere in the wider dense candidate pool. A cross-encoder
# reranker jointly scores (query, chunk) pairs and reorders that pool, which
# fixes ranking mistakes without needing a second (lexical) retrieval path.
RERANK_CANDIDATE_POOL = 25
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_groq_client = Groq(api_key=GROQ_API_KEY)


@dataclass
class RankedMatch:
    id: str
    score: float
    metadata: dict


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL_NAME)


def search(query: str, top_k: int = TOP_K):
    vector = embed_query(query)
    index = get_index()
    response = index.query(vector=vector, top_k=RERANK_CANDIDATE_POOL, include_metadata=True)
    candidates = response.matches
    if not candidates:
        return []

    reranker = get_reranker()
    pairs = [(query, (c.metadata or {}).get("text", "")) for c in candidates]
    rerank_scores = reranker.predict(pairs)

    reranked = sorted(zip(candidates, rerank_scores), key=lambda pair: pair[1], reverse=True)

    return [
        RankedMatch(id=c.id, score=float(score), metadata=c.metadata)
        for c, score in reranked[:top_k]
    ]


def build_context(matches) -> str:
    parts = []
    for m in matches:
        meta = m.metadata or {}
        parts.append(f"[Source: {meta.get('source', 'unknown')}]\n{meta.get('text', '')}")
    return "\n\n---\n\n".join(parts)


def answer_query(query: str, write_trace: bool = False) -> dict:
    matches = search(query)
    context = build_context(matches)

    completion = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        temperature=0,
    )

    answer = completion.choices[0].message.content

    sources = sorted(
        {
            m.metadata.get("source")
            for m in matches
            if m.metadata and m.metadata.get("source")
        }
    )

    # Optionally write trace for error analysis
    if write_trace:
        from app.tracing import write_trace as write_trace_fn
        retrieved_chunks = [
            {
                "id": m.id,
                "score": m.score,
                "source": m.metadata.get("source") if m.metadata else None,
                "text": m.metadata.get("text")[:100] if m.metadata else None,  # First 100 chars
            }
            for m in matches
        ]
        write_trace_fn(query, retrieved_chunks, answer, sources)

    return {"answer": answer, "sources": sources}
