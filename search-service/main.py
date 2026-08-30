from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, get_db
import models  # noqa: F401
from embeddings import get_embedding_backend
from vectorstore import get_vector_store
from chunking import chunk_text
from auth import get_current_claims
from schemas import IndexRequest, IndexResponse, SearchResponse, SearchResult

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Search Service", description="OCR + semantic search over case documents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_embedder = get_embedding_backend()
_vector_store = get_vector_store(dimension=_embedder.dimension)


@app.get("/health")
def health():
    return {"status": "ok", "service": "search", "embedding_dimension": _embedder.dimension}


@app.post("/search/index", response_model=IndexResponse)
def index_document(req: IndexRequest, db=Depends(get_db), claims: dict = Depends(get_current_claims)):
    chunks = chunk_text(req.text)
    if not chunks:
        return IndexResponse(chunks_indexed=0)

    embeddings = _embedder.embed(chunks)
    for chunk, embedding in zip(chunks, embeddings):
        _vector_store.add(db, req.document_id, req.case_id, req.document_type, chunk, embedding)

    return IndexResponse(chunks_indexed=len(chunks))


@app.get("/search", response_model=SearchResponse)
def search(q: str, case_id: str | None = None, top_k: int = 5,
           db=Depends(get_db), claims: dict = Depends(get_current_claims)):
    query_embedding = _embedder.embed([q])[0]
    results = _vector_store.search(db, query_embedding, case_id, top_k)

    return SearchResponse(results=[
        SearchResult(chunk_id=chunk.id, document_id=chunk.document_id, case_id=chunk.case_id,
                     document_type=chunk.document_type, chunk_text=chunk.chunk_text, score=score)
        for chunk, score in results
    ])
