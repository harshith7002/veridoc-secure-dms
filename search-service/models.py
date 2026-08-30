from sqlalchemy import Column, Integer, String, Text
from database import Base


class DocumentChunk(Base):
    """One row per searchable chunk of text extracted from a document (OCR output or
    plain text). embedding is stored as a JSON-encoded list of floats for the local
    backend - see vectorstore.PgVectorStore for the pgvector-backed equivalent, which
    uses a native vector column instead."""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False, index=True)   # references Documents service's document id
    case_id = Column(String, nullable=False, index=True)
    document_type = Column(String, nullable=True)
    chunk_text = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=False)
