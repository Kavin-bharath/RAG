from fastapi import FastAPI, File, HTTPException, UploadFile

from app.ingestion import ingest_document
from app.retrieval import answer_query
from app.schemas import QueryRequest

app = FastAPI(title="Ask My Documents RAG API")


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    return ingest_document(file, raw_bytes)


@app.post("/query")
async def query_documents(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return answer_query(request.query)
