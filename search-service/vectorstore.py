import json
import os
from abc import ABC, abstractmethod

import numpy as np
from sqlalchemy.orm import Session

from models import DocumentChunk


class VectorStore(ABC):
    @abstractmethod
    def add(self, db: Session, document_id: str, case_id: str, document_type: str | None,
            chunk_text: str, embedding: list[float]) -> DocumentChunk: ...

    @abstractmethod
    def search(self, db: Session, query_embedding: list[float], case_id: str | None,
               top_k: int) -> list[tuple[DocumentChunk, float]]: ...


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


class LocalVectorStore(VectorStore):
    """Embeddings stored as JSON in a normal SQLite/Postgres text column; similarity computed
    in Python with numpy. Fine at prototype scale (hundreds to low thousands of chunks);
    doesn't scale the way a real vector index (pgvector's IVFFlat/HNSW) does for large corpora -
    that's what PgVectorStore is for."""

    def add(self, db: Session, document_id: str, case_id: str, document_type: str | None,
            chunk_text: str, embedding: list[float]) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id, case_id=case_id, document_type=document_type,
            chunk_text=chunk_text, embedding_json=json.dumps(embedding),
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk

    def search(self, db: Session, query_embedding: list[float], case_id: str | None,
               top_k: int) -> list[tuple[DocumentChunk, float]]:
        query = db.query(DocumentChunk)
        if case_id:
            query = query.filter(DocumentChunk.case_id == case_id)
        chunks = query.all()

        q = np.array(query_embedding)
        scored = [(chunk, _cosine_similarity(q, np.array(json.loads(chunk.embedding_json)))) for chunk in chunks]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]


class PgVectorStore(VectorStore):
    """pgvector-backed store for production scale. NOT exercised against a live database in
    this build - no PostgreSQL+pgvector instance was available in the environment this was
    written in. The query logic (cosine distance via the <=> operator, which pgvector provides)
    is standard and should work as written, but treat this as reviewed-not-tested until it's
    run against a real pgvector-enabled Postgres."""

    def __init__(self, dimension: int):
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import Column, Integer, String, Text, text
        from database import Base, engine

        class PgDocumentChunk(Base):
            __tablename__ = "document_chunks_pg"
            __table_args__ = {"extend_existing": True}
            id = Column(Integer, primary_key=True, autoincrement=True)
            document_id = Column(String, nullable=False, index=True)
            case_id = Column(String, nullable=False, index=True)
            document_type = Column(String, nullable=True)
            chunk_text = Column(Text, nullable=False)
            embedding = Column(Vector(dimension), nullable=False)

        self._model = PgDocumentChunk
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        Base.metadata.create_all(bind=engine, tables=[PgDocumentChunk.__table__])

    def add(self, db: Session, document_id: str, case_id: str, document_type: str | None,
            chunk_text: str, embedding: list[float]):
        row = self._model(document_id=document_id, case_id=case_id, document_type=document_type,
                           chunk_text=chunk_text, embedding=embedding)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def search(self, db: Session, query_embedding: list[float], case_id: str | None, top_k: int):
        query = db.query(self._model)
        if case_id:
            query = query.filter(self._model.case_id == case_id)
        # cosine distance operator from pgvector; lower is more similar, so we convert to a
        # similarity-style score (1 - distance) to keep the same return contract as LocalVectorStore.
        results = query.order_by(self._model.embedding.cosine_distance(query_embedding)).limit(top_k).all()
        return [(row, 1 - row.embedding.cosine_distance(query_embedding)) for row in results]


def get_vector_store(dimension: int) -> VectorStore:
    backend = os.environ.get("VECTOR_STORE_BACKEND", "local")
    if backend == "pgvector":
        return PgVectorStore(dimension)
    return LocalVectorStore()
