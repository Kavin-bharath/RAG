# Ask My Documents — RAG API

Two endpoints:
- `POST /upload` — multipart form file upload (`file`). Extracts text, chunks it
  (RecursiveCharacterTextSplitter), embeds with `all-MiniLM-L6-v2`, upserts to Pinecone.
- `POST /query` — JSON body `{"query": "..."}`. Embeds the query, retrieves top-5 chunks
  from Pinecone, and asks Groq to answer grounded only in that context (it replies
  "I don't know based on the provided documents." when the context doesn't cover it).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in PINECONE_API_KEY and GROQ_API_KEY
```

The Pinecone index named in `PINECONE_INDEX_NAME` (default `rag-docs`) is created
automatically on first use if it doesn't already exist (dimension 384, cosine metric).

## Run

```bash
uvicorn app.main:app --reload
```

Docs at http://127.0.0.1:8000/docs

## Try it

```bash
curl -X POST http://127.0.0.1:8000/upload -F "file=@sample.pdf"

curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is the refund policy?\"}"
```
