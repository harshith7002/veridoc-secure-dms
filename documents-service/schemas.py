from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    case_id: str
    document_type: str
    filename: str
    sha256_hash: str
    uploaded_by: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class IntegrityCheckResult(BaseModel):
    id: int
    intact: bool
    stored_hash: str
    recomputed_hash: str
