from sqlalchemy import Column, Integer, String, Text
from database import Base


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Stored as the exact ISO-8601 string that was hashed - never a native DB datetime type.
    # SQLite (and some DB drivers) silently drop timezone info / reformat on round-trip,
    # which would make the recomputed hash diverge from the stored one on every read,
    # falsely flagging every untouched entry as tampered. A plain string column has no
    # such transformation, so what's hashed is byte-for-byte what's re-hashed later.
    timestamp = Column(String, nullable=False)
    actor = Column(String, nullable=False)          # who performed the action (user id / service account)
    action = Column(String, nullable=False)          # UPLOAD, VIEW, DOWNLOAD, SHARE, EDIT, DELETE_REQUEST
    document_id = Column(String, nullable=False)
    case_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)             # free-form JSON string, e.g. {"ip": "...", "reason": "..."}

    data_hash = Column(String(64), nullable=False)     # SHA-256 of this entry's own fields
    prev_hash = Column(String(64), nullable=False)     # entry_hash of the previous row ("0"*64 for genesis)
    entry_hash = Column(String(64), nullable=False, unique=True)  # SHA-256(prev_hash + data_hash)
