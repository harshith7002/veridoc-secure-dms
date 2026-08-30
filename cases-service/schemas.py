from datetime import datetime
from pydantic import BaseModel
from models import CaseStatus, CasePriority


class CaseCreate(BaseModel):
    case_number: str
    title: str
    description: str | None = None
    priority: CasePriority = CasePriority.MEDIUM


class CaseUpdateStatus(BaseModel):
    status: CaseStatus


class CaseOut(BaseModel):
    id: int
    case_number: str
    title: str
    description: str | None
    status: CaseStatus
    priority: CasePriority
    organization: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseStats(BaseModel):
    total_cases: int
    active_cases: int
    pending_review: int
    high_priority: int
