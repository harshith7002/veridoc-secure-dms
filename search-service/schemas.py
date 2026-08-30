from pydantic import BaseModel


class IndexRequest(BaseModel):
    document_id: str
    case_id: str
    document_type: str | None = None
    text: str  # already-extracted text; for scanned images, OCR happens before this is called


class IndexResponse(BaseModel):
    chunks_indexed: int


class SearchResult(BaseModel):
    chunk_id: int
    document_id: str
    case_id: str
    document_type: str | None
    chunk_text: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
