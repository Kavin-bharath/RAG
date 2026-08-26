from pinecone import Pinecone, ServerlessSpec

from app.config import (
    EMBEDDING_DIMENSION,
    PINECONE_API_KEY,
    PINECONE_CLOUD,
    PINECONE_INDEX_NAME,
    PINECONE_REGION,
)

_pc = None
_index = None


def get_index():
    """Return the Pinecone index, creating it on first use if it doesn't exist yet."""
    global _pc, _index

    if _index is not None:
        return _index

    _pc = Pinecone(api_key=PINECONE_API_KEY)

    existing_indexes = _pc.list_indexes().names()
    if PINECONE_INDEX_NAME not in existing_indexes:
        _pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )

    _index = _pc.Index(PINECONE_INDEX_NAME)
    return _index
