import enum
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime
from sqlalchemy.sql import func
from database import Base


class CaseStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    CLOSED = "CLOSED"


class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # This is the same string other services already key documents/audit entries/search
    # chunks against (e.g. "CASE-8891") - this service becomes the source of truth for it,
    # but the identifier format doesn't change, so nothing downstream needs to migrate.
    case_number = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(CaseStatus), nullable=False, default=CaseStatus.OPEN)
    priority = Column(Enum(CasePriority), nullable=False, default=CasePriority.MEDIUM)
    organization = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
