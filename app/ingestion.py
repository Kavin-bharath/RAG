import uuid
from io import BytesIO
from typing import List

from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import CHUNK_OVERLAP, CHUNK_SIZE
from app.embeddings import embed_texts
from app.vectorstore import get_index


def extract_text(file: UploadFile, raw_bytes: bytes) -> str:
    filename = file.filename or ""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_text(text)


def ingest_document(file: UploadFile, raw_bytes: bytes) -> dict:
    text = extract_text(file, raw_bytes)
    if not text.strip():
        return {"filename": file.filename, "chunks_indexed": 0}

    chunks = chunk_text(text)
    vectors = embed_texts(chunks)

    index = get_index()
    to_upsert = [
        {
            "id": f"{file.filename}-{uuid.uuid4().hex[:8]}-{i}",
            "values": vector,
            "metadata": {"source": file.filename, "text": chunk},
        }
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    index.upsert(vectors=to_upsert)
    return {"filename": file.filename, "chunks_indexed": len(chunks)}
