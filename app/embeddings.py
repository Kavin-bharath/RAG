from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    embedder = get_embedder()
    return embedder.encode(texts, normalize_embeddings=True).tolist()


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]
