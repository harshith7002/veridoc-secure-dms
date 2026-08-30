from datetime import datetime
from pydantic import BaseModel


class AuditEntryCreate(BaseModel):
    actor: str
    action: str
    document_id: str
    case_id: str | None = None
    details: str | None = None


class AuditEntryOut(BaseModel):
    id: int
    timestamp: datetime
    actor: str
    action: str
    document_id: str
    case_id: str | None
    details: str | None
    data_hash: str
    prev_hash: str
    entry_hash: str

    class Config:
        from_attributes = True


class VerifyResult(BaseModel):
    valid: bool
    entries_checked: int | None = None
    broken_at_id: int | None = None
    reason: str | None = None
